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

用法：python scripts/validate-audio-levels.py PROJECT_DIR [--json]
退出码：0 通过 / 1 存在 P0 / 2 用法或文件错误
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


def peak_db(path: Path) -> float | None:
    try:
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"max_volume:\s*(-?[\d.]+) dB", (r.stdout or "") + (r.stderr or ""))
    return float(m.group(1)) if m else None


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

    files = sorted([p for p in sfx_dir.glob("*") if p.is_file()]) if sfx_dir.is_dir() else []
    if not files:
        p1.append("public/sfx/ 里没有任何音效文件（成片会完全没有音效）")

    for f in files:
        if f.name.lower().startswith("bgm"):
            continue
        if f.name.upper().endswith(".TXT") or f.suffix.lower() == ".txt":
            continue
        pk = peak_db(f)
        if pk is None:
            p1.append(f"{f.name}：读不到峰值（文件损坏或非音频）")
            continue
        checked.append({"file": f.name, "peak_db": pk})
        if pk < PEAK_FLOOR:
            msg = (f"{f.name} 峰值 {pk:.1f} dBFS 低于 {PEAK_FLOOR:.0f} dBFS —— 素材本身太轻，"
                   f"乘上混音音量后必然被 BGM/人声压住（实测过 paper-tap 有效峰值 −49 dB）。"
                   f"修法：`ffmpeg -i {f.name} -af volume={-3.0 - pk:.1f}dB <out>` 归一到 −3 dBFS")
            (p0 if QUIET_P0 else p1).append(msg)

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
