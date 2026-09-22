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

测量失败（ffmpeg 不可用 / 读不到峰值）= **门禁自身故障**，直接 rc=2 硬失败：
旧版把它记成 P1 → rc=0 静默通过，等于这道门在没装 ffmpeg 的环境里从未生效。
"内容没测出缺陷"与"根本没测成"必须可区分；sfx 目录不存在/为空仍是 P1（内容口径）。

用法：python scripts/validate-audio-levels.py PROJECT_DIR [--json]
退出码：0 通过 / 1 存在 P0 / 2 用法或文件错误 / 2 测量失败（门禁自身故障）
零第三方依赖（只用 ffmpeg + 标准库）。
"""
from __future__ import annotations

import argparse
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
    if not files:
        p1.append("public/sfx/ 里没有任何音效文件（成片会完全没有音效）")

    for f in files:
        if f.name.lower().startswith("bgm"):
            continue
        if f.name.upper().endswith(".TXT") or f.suffix.lower() == ".txt":
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

    # ---- 测量失败 = 门禁自身故障：rc=2 硬失败（先于任何 PASS/FAIL 结论）----
    if measure_fail:
        print("validate-audio-levels · 门禁自身故障：以下素材**没能完成测量**"
              "（这不是内容 P0/P1，是判据没跑成，不许按通过处理）：", file=sys.stderr)
        for mf in measure_fail:
            print(f"  ·· 测量失败 {mf}", file=sys.stderr)
        return 2

    if not any((sfx_dir / f"bgm{s}").exists() for s in (".mp3", ".wav", ".ogg")) and sfx_dir.is_dir():
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
            print(f"  ·· {c['file']:<20} 峰值 {c['peak_db']:>6.1f} dBFS")
        for x in p0:
            print(f"  P0 {x}")
        for x in p1:
            print(f"  P1 {x}")
        print(f"结论：P0={len(p0)} P1={len(p1)} → {'PASS' if not p0 else 'FAIL'}")
    return 1 if p0 else 0


if __name__ == "__main__":
    sys.exit(main())
