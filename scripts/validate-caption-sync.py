#!/usr/bin/env python3
"""Verify subtitle text, word order and timings exactly match TTS boundaries."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", text)


def core(word: dict) -> tuple[str, int, int]:
    return str(word["part"]), int(word["start"]), int(word["end"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tts_words_json", type=Path)
    parser.add_argument("caption_cues_json", type=Path)
    parser.add_argument("--max-lead-ms", type=int, default=80)
    args = parser.parse_args()

    source = json.loads(args.tts_words_json.read_text(encoding="utf-8"))
    data = json.loads(args.caption_cues_json.read_text(encoding="utf-8"))
    cues = data.get("cues", data) if isinstance(data, dict) else data
    if not isinstance(source, list) or not isinstance(cues, list):
        raise SystemExit("Expected a TTS word list and a subtitle cue list")

    flattened = []
    failures = []
    if not isinstance(data, dict) or data.get("segmentation") != "semantic":
        failures.append(
            "caption file is not marked segmentation=semantic; mechanical draft cues cannot be rendered"
        )
    for index, cue in enumerate(cues, 1):
        words = cue.get("words")
        if not isinstance(words, list) or not words:
            failures.append(f"cue {index}: missing word boundaries")
            continue
        joined = "".join(str(word["part"]) for word in words)
        if normalized(joined) != normalized(str(cue.get("text", ""))):
            failures.append(f"cue {index}: text differs from its TTS words")
        lead = int(words[0]["start"]) - int(cue["start_ms"])
        if lead < 0 or lead > args.max_lead_ms:
            failures.append(f"cue {index}: visual lead {lead}ms exceeds 0–{args.max_lead_ms}ms")
        flattened.extend(words)

    if [core(word) for word in flattened] != [core(word) for word in source]:
        failures.append("flattened cue words do not exactly match the complete TTS word stream")
    if failures:
        for failure in failures:
            print(f"SYNC ERROR: {failure}")
        raise SystemExit(f"{len(failures)} caption sync failure(s)")
    print(f"Validated {len(source)} TTS word boundaries across {len(cues)} synchronized cues")


if __name__ == "__main__":
    main()
