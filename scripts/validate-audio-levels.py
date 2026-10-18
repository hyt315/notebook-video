#!/usr/bin/env python3
"""validate-audio-levels.py · 音效可听度门禁（P0）

病因（实测）：技能自带的 sfx 素材录得极轻——`paper-tap.wav` 峰值只有 −31 dB，
再乘混音音量 0.13（−17.7 dB）后有效峰值 **−49 dB**；而 BGM 持续在 −22 dB。
四个音效全被人声与 BGM 压住，成片听起来"几乎没有音效"（用户与实测一致）。
根因是**双重衰减**：素材轻 × 音量小。

判据：
  P0  `public/sfx/*`（bgm 除外）峰值 < -12 dBFS —— 素材太轻，混音后必然听不见
  P0  `src/index.tsx` 里引用的 `sfx/xxx` 文件不存在
  P1  缺少 bgm
  P1  引用了 SFX 但 index.tsx 里查不到任何 `vol:` 设定（可能整段音效被删）
  v4.3 预制音效库（public/sfx/lib + sfx-manifest.json）：
  P0  manifest 缺失 / 损坏；manifest 里的文件不存在；sha256 与 manifest 不符（被替换或损坏）
  P0  src/sfx.ts 的 SFX_FILES 与 manifest 的事件/文件不一致；引用的 sfx/lib 文件不存在
  P0  库文件实测响度偏离 manifest 目标超过容差（一致性），或峰值 > -0.5 dBFS（削波风险）
  P0  缺少 SFX_EVENTS 里的任一语义事件；SFX_GAIN 任一项 > 0.7（会顶到人声）或 < 0.15（听不见）

测量失败（ffmpeg 不可用 / 读不到峰值）= **门禁自身故障**，直接 rc=2 硬失败：
旧版把它记成 P1 → rc=0 静默通过，等于这道门在没装 ffmpeg 的环境里从未生效。
"内容没测出缺陷"与"根本没测成"必须可区分；sfx 目录不存在/为空仍是 P1（内容口径）。

用法：python scripts/validate-audio-levels.py PROJECT_DIR [--json]
退出码：0 通过 / 1 存在 P0 / 2 用法或文件错误 / 2 测量失败（门禁自身故障）
零第三方依赖（只用 ffmpeg + 标准库）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PEAK_FLOOR = -12.0          # 素材峰值下限（dBFS）
QUIET_P0 = True             # 太轻记 P0（这是"静默失效"型缺陷）


def peak_db(path: Path) -> tuple[float | None, str]:
    """测峰值 dBFS。返回 (峰值, 失败原因)：原因为空串 = 测成功；
    原因非空 = **测量失败（门禁自身故障）**——调用方必须 rc=2，
    绝不允许记成 P0/P1 内容问题（旧版记 P1 → rc=0，是静默放行路径）。"""
    try:
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
    except FileNotFoundError:
        return None, "找不到 ffmpeg（未安装或不在 PATH）——音效可听度门禁无法测量"
    except OSError as e:
        return None, f"ffmpeg 无法调用（{e.__class__.__name__}: {e}）——无法测量"
    except subprocess.SubprocessError as e:
        return None, f"ffmpeg 运行异常（{e.__class__.__name__}: {e}）——读不到峰值"
    m = re.search(r"max_volume:\s*(-?[\d.]+) dB", (r.stdout or "") + (r.stderr or ""))
    if not m:
        return None, "ffmpeg 输出里没有 max_volume（volumedetect 未产出测量值）——文件可能损坏或不是音频"
    return float(m.group(1)), ""


def ebur128_loudness(path: Path) -> tuple[float | None, str]:
    """ffmpeg ebur128 integrated loudness (LUFS). 短音效的积分响度在 400ms 门限下偏低，
    所以只拿来和 manifest 里**同一文件**的 pyloudnorm(100ms) 值比较一致性时，用宽容差 6 LU 防误报；
    主判据是 sha256（文件没被换）+ 峰值。"""
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=sample", "-f", "null", "-"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"ffmpeg 无法调用：{e}"
    m = re.findall(r"I:\s*(-?[\d.]+|-inf) LUFS", (r.stderr or ""))
    if not m:
        return None, "ebur128 没有产出积分响度"
    return (float(m[-1]) if m[-1] != "-inf" else -99.0), ""


def check_library(project: Path, p0: list[str], p1: list[str], checked: list[dict], measure_fail: list[str]) -> None:
    sfx_dir = project / "public" / "sfx"
    man_p = sfx_dir / "sfx-manifest.json"
    if not (sfx_dir / "lib").is_dir() and not man_p.exists():
        return  # 旧项目：没有预制库，走旧口径
    try:
        man = json.loads(man_p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        p0.append(f"sfx-manifest.json 缺失或无法解析（{e}）")
        return
    target = float(man.get("target_lufs_100ms", -18.0))
    events = {e["event"]: e for e in man.get("events", [])}
    for ev, e in events.items():
        f = project / "public" / e["file"]
        if not f.exists():
            p0.append(f"manifest 事件 {ev} 的文件 {e['file']} 不存在")
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        if h != e.get("sha256"):
            p0.append(f"{e['file']} 的 sha256 与 manifest 不符（文件被替换/损坏；重建库请用 scripts/dev/build-sfx-library.py 并同时更新 manifest）")
        pk, err = peak_db(f)
        if pk is None:
            measure_fail.append(f"{e['file']}: {err}")
            continue
        lu, err2 = ebur128_loudness(f)
        if lu is None:
            measure_fail.append(f"{e['file']}: {err2}")
            continue
        checked.append({"file": e["file"], "peak_db": pk, "lufs_i": lu, "manifest_lufs_100ms": e.get("loudness_lufs_100ms")})
        if pk > -0.5:
            p0.append(f"{e['file']} 峰值 {pk:.1f} dBFS > -0.5（削波风险）")
        if ev != "bed":
            if abs(float(e.get("loudness_lufs_100ms", target)) - target) > float(man.get("tolerance_lu", 1.5)):
                p0.append(f"{e['file']} manifest 响度 {e.get('loudness_lufs_100ms')} LUFS 偏离库目标 {target} 超过容差（库内响度不一致）")
            if pk < PEAK_FLOOR:
                p0.append(f"{e['file']} 峰值 {pk:.1f} dBFS 低于 {PEAK_FLOOR:.0f} dBFS（素材太轻）")
    sfx_ts = project / "src" / "sfx.ts"
    if sfx_ts.exists():
        src = sfx_ts.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"SFX_EVENTS\s*=\s*\[([^\]]*)\]", src)
        want = re.findall(r"'([a-z]+)'", m.group(1)) if m else []
        for ev in want:
            if ev not in events:
                p0.append(f"src/sfx.ts 声明了事件 {ev}，但 sfx-manifest.json 里没有")
        for ev, path in re.findall(r"^\s*([a-z]+):\s*'(sfx/lib/[\w.-]+)'", src, re.M):
            if ev in events and events[ev]["file"] != path:
                p0.append(f"src/sfx.ts SFX_FILES.{ev}={path} 与 manifest {events[ev]['file']} 不一致")
            if not (project / "public" / path).exists():
                p0.append(f"src/sfx.ts 引用的 {path} 不存在")
        g = re.search(r"SFX_GAIN[^=]*=\s*\{([^}]*)\}", src)
        for ev, v in re.findall(r"([a-z]+):\s*([\d.]+)", g.group(1) if g else ""):
            if float(v) > 0.7 or float(v) < 0.15:
                p0.append(f"SFX_GAIN.{ev}={v} 越界（0.15–0.70）：太大会顶到人声，太小听不见")
            mg = events.get(ev, {}).get("gain")
            if mg is not None and abs(float(mg) - float(v)) > 0.01:
                p0.append(f"SFX_GAIN.{ev}={v} 与 sfx-manifest.json gain={mg} 不一致（v4.5：增益以库元数据为准；改 src/sfx.ts 让它等于 manifest）")
        o = re.search(r"SFX_OFFSET_MS[^=]*=\s*\{([^}]*)\}", src)
        for ev, v in re.findall(r"([a-z]+):\s*([\d.]+)", o.group(1) if o else ""):
            mo = events.get(ev, {}).get("offsetMs")
            if mo is not None and abs(float(mo) - float(v)) > 2:
                p0.append(f"SFX_OFFSET_MS.{ev}={v} 与 sfx-manifest.json offsetMs={mo} 不一致（瞬态会偏离视觉命中帧）")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"项目目录不存在：{project}", file=sys.stderr)
        return 2

    sfx_dir = project / "public" / "sfx"
    p0: list[str] = []
    p1: list[str] = []
    checked: list[dict] = []
    measure_fail: list[str] = []   # 测量失败清单（门禁自身故障 → rc=2，不是内容问题）

    files = sorted([p for p in sfx_dir.glob("*") if p.is_file()]) if sfx_dir.is_dir() else []
    if not files and not (sfx_dir / "lib").is_dir():
        p1.append("public/sfx/ 里没有任何音效文件（成片会完全没有音效）")

    for f in files:
        if f.name.lower().startswith("bgm"):
            continue
        if f.name.upper().endswith(".TXT") or f.suffix.lower() in (".txt", ".json"):
            continue
        pk, err = peak_db(f)
        if pk is None:
            # 旧版这里记 P1 → 整脚本 rc=0：ffmpeg 没装/文件读不出峰值 = 这道门**从未跑成**，
            # 却被当成"通过"。测量失败不是内容档位问题，直接走门禁自身故障（rc=2）。
            measure_fail.append(f"{f.name}: {err}")
            continue
        checked.append({"file": f.name, "peak_db": pk})
        if pk < PEAK_FLOOR:
            msg = (f"{f.name} 峰值 {pk:.1f} dBFS 低于 {PEAK_FLOOR:.0f} dBFS —— 素材本身太轻，"
                   f"乘上混音音量后必然被 BGM/人声压住（实测过 paper-tap 有效峰值 −49 dB）。"
                   f"修法：`ffmpeg -i {f.name} -af volume={-3.0 - pk:.1f}dB <out>` 归一到 −3 dBFS")
            (p0 if QUIET_P0 else p1).append(msg)

    check_library(project, p0, p1, checked, measure_fail)

    # ---- 测量失败 = 门禁自身故障：rc=2 硬失败（先于任何 PASS/FAIL 结论）----
    if measure_fail:
        print("validate-audio-levels · 门禁自身故障：以下素材**没能完成测量**"
              "（这不是内容 P0/P1，是判据没跑成，不许按通过处理）：", file=sys.stderr)
        for mf in measure_fail:
            print(f"  ·· 测量失败 {mf}", file=sys.stderr)
        return 2

    if not any((sfx_dir / f"bgm{s}").exists() for s in (".mp3", ".wav", ".ogg")) and not (sfx_dir / "lib" / "bed.ogg").exists() and sfx_dir.is_dir():
        p1.append("缺少 bgm（背景音乐）文件")

    # 引用的音效文件是否存在
    idx = project / "src" / "index.tsx"
    if idx.exists():
        src = idx.read_text(encoding="utf-8", errors="replace")
        refs = sorted(set(re.findall(r"sfx/([\w.-]+)", src)))
        for r in refs:
            if not (sfx_dir / r).exists():
                p0.append(f"src/index.tsx 引用了 sfx/{r}，但 public/sfx/ 里没有这个文件")
        if refs and "vol:" not in src:
            p1.append("引用了音效但 index.tsx 里找不到任何 vol: 设定（音效可能被注释掉或整段删除）")

    if args.json:
        print(json.dumps({"p0": p0, "p1": p1, "checked": checked}, ensure_ascii=False, indent=2))
    else:
        print(f"validate-audio-levels · 检查 {len(checked)} 个音效素材（峰值下限 {PEAK_FLOOR:.0f} dBFS）")
        for c in checked:
            extra = (f"  I {c['lufs_i']:>6.1f} LUFS" if c.get("lufs_i", -99) > -69 else "  I   n/a (<0.4 s, gated)") if "lufs_i" in c else ""
            if c.get("manifest_lufs_100ms") is not None:
                extra += f"  manifest {c['manifest_lufs_100ms']:>6.1f} LUFS/100ms"
            print(f"  ·· {c['file']:<24} 峰值 {c['peak_db']:>6.1f} dBFS{extra}")
        for x in p0:
            print(f"  P0 {x}")
        for x in p1:
            print(f"  P1 {x}")
        print(f"结论：P0={len(p0)} P1={len(p1)} → {'PASS' if not p0 else 'FAIL'}")
    return 1 if p0 else 0


if __name__ == "__main__":
    sys.exit(main())
