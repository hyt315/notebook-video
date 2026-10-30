#!/usr/bin/env python3
"""export-srt.py — 把 `manifests/caption-cues.json` 导成标准 .srt。

用法：
    python scripts/export-srt.py CAPTION_CUES_JSON OUTPUT_SRT [--offset-ms N]

为什么要有它：片子交付出去，别人拿到的应该是一支 mp4 **和一份字幕**，而不是只能看画面。
视频平台自动识别字幕对中文讲解片几乎不可用（术语、数字、断句全错），而我们的 cues 是
按语义断点切好的，直接导出比事后重做准。

口径：
- 时间取 `start_ms` → `speech_end_ms`。两个字幕生成器（`build-semantic-captions` 与
  `compose-story`）都把 `reveal_end_ms` 写成与 `speech_end_ms` 相同，所以两者等价；
  取 `speech_end_ms` 是因为它语义更明确（这句话什么时候说完）。
- `--offset-ms` 用于整体平移（例如成片前加了片头）。负数会把早于 0 的时间夹到 0。
- SRT 要求每条 `end > start`；长度为 0 的 cue 补 1 ms，否则播放器会吞掉。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def ms_to_srt(ms: int) -> str:
    if ms < 0:
        ms = 0
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, milli = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"


def load_cues(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cues = data.get("cues") if isinstance(data, dict) else data
    if not isinstance(cues, list) or not cues:
        raise SystemExit(f"no cues in {path}")
    return cues


def main() -> int:
    parser = argparse.ArgumentParser(description="Export caption cues to SRT.")
    parser.add_argument("cues", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--offset-ms", type=int, default=0,
                        help="shift every cue by this many milliseconds (negative allowed)")
    args = parser.parse_args()

    cues = load_cues(args.cues)
    lines: list[str] = []
    prev_end = -1
    written = 0

    for cue in cues:
        text = str(cue.get("text") or "").strip()
        if not text:
            continue
        start = int(cue.get("start_ms", 0)) + args.offset_ms
        end = int(cue.get("speech_end_ms", cue.get("reveal_end_ms", start))) + args.offset_ms
        start = max(0, start)
        end = max(start + 1, end)
        # 严格递增：上一条的结束不许晚于下一条开始，否则播放器会叠字。
        if start <= prev_end:
            start = prev_end + 1
            end = max(start + 1, end)
        prev_end = end
        written += 1
        lines.extend([str(written), f"{ms_to_srt(start)} --> {ms_to_srt(end)}", text, ""])

    if not written:
        raise SystemExit(f"no non-empty cue in {args.cues}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # 写 LF：SRT 两种换行都能读，LF 在 git 里不会每行都变成改动。
    args.output.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    total = prev_end
    print(f"SRT: {args.output} — {written} cues, {ms_to_srt(total)} total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
