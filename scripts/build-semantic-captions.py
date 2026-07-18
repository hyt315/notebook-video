#!/usr/bin/env python3
"""Bind editor-approved semantic subtitle lines to exact TTS word boundaries."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("words_json", type=Path)
    parser.add_argument("lines_txt", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("--lead-ms", type=int, default=60)
    args = parser.parse_args()

    words = json.loads(args.words_json.read_text(encoding="utf-8"))
    lines = [line.strip() for line in args.lines_txt.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not isinstance(words, list) or not words or not lines:
        raise SystemExit("Expected a non-empty TTS word list and semantic line list")

    cursor = 0
    cues = []
    for index, line in enumerate(lines, 1):
        chosen = []
        built = ""
        target = normalized(line)
        while cursor < len(words) and len(normalized(built)) < len(target):
            word = words[cursor]
            if not all(key in word for key in ("part", "start", "end")):
                raise SystemExit(f"Malformed timing item: {word!r}")
            chosen.append({
                "part": str(word["part"]),
                "start": int(word["start"]),
                "end": int(word["end"]),
            })
            built += str(word["part"])
            cursor += 1
        if normalized(built) != target:
            raise SystemExit(
                f"Cue {index} does not end on a TTS word boundary: {line!r} != {built!r}"
            )
        start_ms = max(0, chosen[0]["start"] - args.lead_ms)
        end_ms = chosen[-1]["end"]
        cues.append({
            "text": line,
            "words": chosen,
            "start_ms": start_ms,
            "speech_end_ms": end_ms,
            "reveal_end_ms": end_ms,
            "start": round(start_ms / 1000, 3),
            "speech_end": round(end_ms / 1000, 3),
            "reveal_end": round(end_ms / 1000, 3),
        })

    if cursor != len(words):
        raise SystemExit(f"Unmatched TTS words: {len(words) - cursor}")
    result = {
        "source": str(args.words_json),
        "lead_ms": args.lead_ms,
        "segmentation": "semantic",
        "cues": cues,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created {len(cues)} semantic subtitle cues: {args.output_json}")


if __name__ == "__main__":
    main()
