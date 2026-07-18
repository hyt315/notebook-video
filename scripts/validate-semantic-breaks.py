#!/usr/bin/env python3
"""Reject protected phrases or ASCII names split across semantic caption cues."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("caption_cues_json", type=Path)
    parser.add_argument("protected_phrases_txt", type=Path)
    args = parser.parse_args()

    data = json.loads(args.caption_cues_json.read_text(encoding="utf-8"))
    cues = data.get("cues") if isinstance(data, dict) else None
    if not isinstance(cues, list) or not cues:
        raise SystemExit("Expected a non-empty caption file with cues")
    if data.get("segmentation") != "semantic":
        raise SystemExit("Caption segmentation must be semantic")

    phrases = [
        normalized(line)
        for line in args.protected_phrases_txt.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not phrases:
        raise SystemExit("Protected phrase manifest must not be empty")

    texts = [normalized(str(cue.get("text", ""))) for cue in cues]
    stream = "".join(texts)
    boundaries = set()
    cursor = 0
    for text in texts[:-1]:
        cursor += len(text)
        boundaries.add(cursor)

    failures: list[str] = []
    for phrase in phrases:
        starts = [match.start() for match in re.finditer(re.escape(phrase), stream)]
        if not starts:
            failures.append(f"protected phrase not found in captions: {phrase}")
            continue
        for start in starts:
            end = start + len(phrase)
            crossed = sorted(point for point in boundaries if start < point < end)
            if crossed:
                failures.append(f"protected phrase crosses a cue boundary: {phrase}")

    for index, (left, right) in enumerate(zip(texts, texts[1:]), 1):
        if left and right and re.search(r"[A-Za-z0-9]$", left) and re.match(r"[A-Za-z0-9]", right):
            failures.append(
                f"cue {index}/{index + 1}: ASCII product, model, benchmark or number token is split"
            )

    if failures:
        for failure in failures:
            print(f"SEMANTIC BREAK ERROR: {failure}")
        raise SystemExit(f"{len(failures)} semantic caption break failure(s)")
    print(f"Validated {len(cues)} semantic cues and {len(phrases)} protected phrases")


if __name__ == "__main__":
    main()
