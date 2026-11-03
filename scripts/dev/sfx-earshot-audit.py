#!/usr/bin/env python3
"""sfx-earshot-audit.py · DEV-ONLY：用 earshot 复核 SFX 库与成片声轨（P1-35）。

定位：**维护者离线质检**，不是运行时依赖。普通用户渲染一支视频永远不需要装 earshot、
PyTorch 或那 1.1GB 模型——上传包继续只带成品音频、配方与许可。

这一步做什么（按 `技能持续优化接手清单.md` §7.8 的接入顺序）：

  1. `earshot measure`（无模型、不联网）复核每个 OGG 的响度 / 真峰值 / 包络，
     与 `scripts/dev/audit-sfx.py`（numpy + pyloudnorm）的数字并排，差异要能解释；
  2. `--mix <成片>` 时用 `earshot timeline` 看真实事件密度与命中点（先分析，不改声音）。

明确不做的：
  · 不用 `realness` / CLAP 分数单独决定入库（只作参考）；
  · 不因工具升级重生成整库；
  · `critique` 要先有「中文教学旁白 + 克制拟音」的自有 profile，本脚本不擅自打分。

用法：
    python scripts/dev/sfx-earshot-audit.py                 # 复核库里的 9 个 OGG
    python scripts/dev/sfx-earshot-audit.py --mix 成片.mp4   # 另看成片事件时间线
    python scripts/dev/sfx-earshot-audit.py --json out.json  # 报告可复现

缺 earshot 时**不报错**：打印安装提示并 exit 0（它是可选开发依赖，不该挡住出片）。
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SFX = ROOT / "assets" / "lecture-template" / "public" / "sfx"
LIB = SFX / "lib"
MANIFEST = SFX / "sfx-manifest.json"
INSTALL = "pip install git+https://github.com/Leonxlnx/earshot  （维护者可选；渲染不需要）"


def have_earshot() -> str | None:
    """返回 earshot 可执行文件路径，没有就 None。"""
    return shutil.which("earshot")


def earshot_measure(exe: str, path: Path) -> dict | None:
    """`earshot measure FILE --json`；失败返回 None（不让单个文件搞挂整轮）。"""
    r = subprocess.run([exe, "measure", str(path), "--json"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    if r.returncode != 0:
        print(f"  ! {path.name}: earshot measure 失败：{(r.stderr or r.stdout or '').strip()[:200]}", file=sys.stderr)
        return None
    out = r.stdout
    try:
        return json.loads(out[out.index("{"):])
    except ValueError:
        print(f"  ! {path.name}: earshot measure 没给出 JSON", file=sys.stderr)
        return None


def numpy_numbers(path: Path) -> dict | None:
    """用 audit-sfx 那套（numpy + soundfile + pyloudnorm）量同一个文件，供交叉对照。"""
    try:
        import numpy as np
        import soundfile as sf
        import pyloudnorm as pyln
    except ImportError:
        return None
    data, sr = sf.read(str(path), always_2d=False)
    if getattr(data, "ndim", 1) > 1:
        data = data.mean(axis=1)
    meter = pyln.Meter(sr)
    loud = float(meter.integrated_loudness(data)) if float(np.max(np.abs(data))) > 1e-6 else float("-inf")
    peak_db = 20 * float(np.log10(max(1e-9, float(np.max(np.abs(data))))))
    return {"lufs": round(loud, 2), "true_peak_dbfs": round(peak_db, 2), "duration_ms": int(len(data) / sr * 1000)}


def pull(d: dict, *keys) -> float | None:
    """从 earshot 的 JSON 里按几个候选键名取一个数（字段名以实际版本为准，逐层找）。"""
    for k in keys:
        if k in d and isinstance(d[k], (int, float)):
            return float(d[k])
        for v in d.values():
            if isinstance(v, dict):
                got = pull(v, k)
                if got is not None:
                    return got
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", dest="json_out", help="把报告写成 JSON（可复现）")
    ap.add_argument("--mix", help="成片（mp4/wav）：另跑 earshot timeline 看事件密度与命中点")
    a = ap.parse_args()

    exe = have_earshot()
    if not exe:
        print(f"没找到 earshot 命令。这是维护者可选开发依赖，**渲染一支视频不需要它**。\n  {INSTALL}")
        print("（skipped — 不是失败；无 earshot 的干净环境照样能出片。）")
        return 0

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.is_file() else {}
    entries = manifest.get("cues") or manifest.get("entries") or manifest
    report: dict = {"tool": "earshot (measure)", "files": {}, "mix": None, "notes": []}

    oggs = sorted(LIB.glob("*.ogg"))
    if not oggs:
        print(f"库里没有 OGG：{LIB}", file=sys.stderr)
        return 1
    print(f"earshot measure × {len(oggs)} 个 OGG（无模型）：")
    for ogg in oggs:
        name = ogg.stem
        es = earshot_measure(exe, ogg)
        npz = numpy_numbers(ogg)
        row: dict = {"numpy": npz, "earshot": es}
        # 与 sfx-manifest 里已记的值对照（dur / lufs / peak 是入库时就写下的）
        rec = entries.get(name) if isinstance(entries, dict) else None
        if isinstance(rec, dict):
            row["manifest"] = {k: rec.get(k) for k in ("duration_ms", "dur", "lufs", "peak", "peak_dbfs", "gain", "offsetMs")
                               if rec.get(k) is not None}
        # 差异说明：两个工具的 LUFS 实现不同（pyloudnorm vs earshot 的），差 ±0.5 LU 属正常；
        # 真峰值差 ±0.3 dBFS 属正常。超出就写进 notes，让人去查。
        if es and npz:
            el = pull(es, "lufs", "loudness", "integrated_loudness")
            ep = pull(es, "true_peak", "true_peak_dbfs", "peak_dbfs", "peak")
            if el is not None and abs(el - npz["lufs"]) > 0.5:
                report["notes"].append(f"{name}: LUFS 差 {el - npz['lufs']:+.2f} LU（earshot {el} vs numpy {npz['lufs']}）——超出 ±0.5 要解释")
            if ep is not None and abs(ep - npz["true_peak_dbfs"]) > 0.3:
                report["notes"].append(f"{name}: 真峰值差 {ep - npz['true_peak_dbfs']:+.2f} dBFS——超出 ±0.3 要解释")
            row["delta"] = {"lufs": None if el is None else round(el - npz["lufs"], 2),
                            "true_peak": None if ep is None else round(ep - npz["true_peak_dbfs"], 2)}
        report["files"][name] = row
        d = row.get("delta") or {}
        print(f"  {name:<12} numpy {npz['lufs'] if npz else '—':>7} LUFS / "
              f"earshot {('%.2f' % d['lufs']) if d.get('lufs') is not None else '—':>7} Δ · "
              f"peak {npz['true_peak_dbfs'] if npz else '—':>6} dBFS")

    if a.mix:
        mix = Path(a.mix)
        if not mix.is_file():
            print(f"成片不存在：{mix}", file=sys.stderr)
            return 2
        print(f"\nearshot timeline（事件密度与命中点，先分析不改声音）：{mix.name}")
        r = subprocess.run([exe, "timeline", str(mix), "--json"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600)
        if r.returncode == 0:
            try:
                tl = json.loads(r.stdout[r.stdout.index("{"):])
            except ValueError:
                tl = {"raw": r.stdout[-2000:]}
            report["mix"] = tl
            events = tl.get("events") if isinstance(tl, dict) else None
            if isinstance(events, list):
                print(f"  事件 {len(events)} 个；前 5：")
                for e in events[:5]:
                    print(f"    {e.get('time', '?'):>8}  {e.get('tag', ''):<12} {e.get('level', '')}")
                report["notes"].append("timeline 只作观察：事件密度/命中点先记录，改不改声音要靠人工盲听决定")
        else:
            print(f"  ! timeline 失败：{(r.stderr or '')[:300]}", file=sys.stderr)
            report["notes"].append("timeline 失败（模型/输入问题），不影响出片")

    if report["notes"]:
        print("\n需要解释/跟进：")
        for n in report["notes"]:
            print(f"  · {n}")
    else:
        print("\n两个工具的测量都在容差内（LUFS ±0.5 / 真峰值 ±0.3 dBFS）。")

    if a.json_out:
        Path(a.json_out).write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"报告已写：{a.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
