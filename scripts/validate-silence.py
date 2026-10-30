#!/usr/bin/env python3
"""validate-silence.py · 「句间必须是真安静」的成片门禁（3.5.0）

病因：`treatment.sound.music.use=false` 也关不掉音乐床（src/index.tsx 无条件循环 bed.ogg），
成片 145 秒里没有一处低于 −45 dB 持续 0.4 秒的静音——配乐一直在，用户没法关。

判据（只在 music.use 不是 true 时执行）：
  用字幕的句间空隙（相邻 cue 的 speech_end_ms → 下一句 start_ms，≥0.4 s 才算）当"应该安静"的位置，
  对成片跑 `ffmpeg silencedetect=n=-45dB:d=0.4`；检测到的静音段数必须 ≥ 期望段数 − 1
  （允许一处被音效尾巴盖住）。低于这个数 = 有持续底噪 / 配乐。

用法：python scripts/validate-silence.py PROJECT VIDEO_MP4
退出码：0 通过 / 1 有 P0 / 2 用法或测量失败（门禁自身故障）。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

MIN_GAP_MS = 400


def music_on(project: Path) -> bool:
    p = project / "manifests" / "treatment.json"
    if not p.is_file():
        return False
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("sound", {}).get("music", {}).get("use") is True
    except ValueError:
        return False


def expected_gaps(project: Path) -> list[tuple[float, float]]:
    p = project / "manifests" / "caption-cues.json"
    if not p.is_file():
        return []
    cues = json.loads(p.read_text(encoding="utf-8")).get("cues") or []
    gaps = []
    for a, b in zip(cues, cues[1:]):
        end = float(a.get("speech_end_ms") or a.get("end_ms") or 0)
        start = float(b.get("start_ms") or 0)
        if start - end >= MIN_GAP_MS:
            gaps.append((end / 1000.0, start / 1000.0))
    return gaps


def main() -> int:
    if len(sys.argv) < 3:
        print("用法：python scripts/validate-silence.py PROJECT VIDEO_MP4", file=sys.stderr)
        return 2
    project, video = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    if not video.is_file():
        print(f"成片不存在：{video}", file=sys.stderr)
        return 2
    if music_on(project):
        print("validate-silence：treatment.sound.music.use=true（明确要配乐）→ 跳过句间静音判据")
        return 0
    gaps = expected_gaps(project)
    if not gaps:
        print("validate-silence：没有 ≥400ms 的句间空隙（字幕连续）→ 无静音可判")
        return 0
    try:
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-i", str(video), "-af", "silencedetect=n=-45dB:d=0.4",
             "-f", "null", "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800,
        )
    except (OSError, subprocess.SubprocessError) as e:
        print(f"测量失败：ffmpeg 无法运行（{e}）—— 门禁没跑成，不能按通过处理", file=sys.stderr)
        return 2
    log = (r.stdout or "") + (r.stderr or "")
    starts = [float(x) for x in re.findall(r"silence_start:\s*(-?[\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*(-?[\d.]+)", log)]
    detected = len(ends) if len(ends) <= len(starts) else len(starts)
    # 只统计"和某个期望空隙有重叠"的静音段，避免片头/片尾的静音凑数
    hits = 0
    for i in range(min(len(starts), len(ends))):
        a, b = starts[i], ends[i]
        if any(a < gb and b > ga for ga, gb in gaps):
            hits += 1
    need = max(1, len(gaps) - 1)
    print(f"validate-silence：句间空隙 {len(gaps)} 段 / 检测到与空隙重叠的静音 {hits} 段"
          f"（阈值 ≥{need}）· 全片静音段 {detected}")
    if hits < need:
        print("  P0 句间不是真安静：music.use=false 时不该有持续底噪 / 配乐。"
              "检查 src/index.tsx 的 MUSIC_ON 是否为 false（sync 从 treatment 生成），"
              "以及音效尾巴是否盖住了整段空隙。")
        return 1
    print("结论：PASS（句间安静）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
