#!/usr/bin/env python3
"""Verify caption data consistency; this does not measure acoustic alignment."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from timing_validation import timing_errors


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", text)


def validate(source: object, data: object, max_lead_ms: int = 80) -> list[str]:
    failures = timing_errors(source)
    if not 0 <= max_lead_ms <= 80:
        failures.append("max-lead-ms must be between 0 and 80")
    if not isinstance(data, dict) or data.get("segmentation") != "semantic":
        return failures + ["caption file must be marked segmentation=semantic"]
    cues = data.get("cues")
    if not isinstance(cues, list) or not cues:
        return failures + ["Expected a non-empty subtitle cue list"]
    flattened = []
    previous_start = -1
    for index, cue in enumerate(cues, 1):
        if not isinstance(cue, dict):
            failures.append(f"cue {index}: expected an object")
            continue
        words = cue.get("words")
        errors = timing_errors(words)
        if errors:
            failures.extend(f"cue {index}: {e}" for e in errors)
            continue
        joined = "".join(word["part"] for word in words)
        text = cue.get("text")
        if not isinstance(text, str) or normalized(joined) != normalized(text):
            failures.append(f"cue {index}: text differs from its TTS words")
        start = cue.get("start_ms")
        if type(start) is not int or start < 0 or start < previous_start:
            failures.append(f"cue {index}: invalid or reordered start_ms")
        else:
            lead = words[0]["start"] - start
            if not 0 <= lead <= max_lead_ms:
                failures.append(f"cue {index}: visual lead {lead}ms exceeds 0–{max_lead_ms}ms")
            previous_start = start
        for key in ("speech_end_ms", "reveal_end_ms"):
            if type(cue.get(key)) is not int or cue[key] != words[-1]["end"]:
                failures.append(f"cue {index}: {key} must equal its last word end")
        flattened.extend(words)
    if flattened != source:
        # Compare the canonical fields only; providers may attach confidence metadata.
        core = lambda w: (w.get("part"), w.get("start"), w.get("end")) if isinstance(w, dict) else None
        if not isinstance(source, list) or list(map(core, flattened)) != list(map(core, source)):
            failures.append("flattened cue words do not exactly match the complete TTS word stream")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tts_words_json", type=Path)
    parser.add_argument("caption_cues_json", type=Path)
    parser.add_argument("--max-lead-ms", type=int, default=80)
    args = parser.parse_args()
    source = json.loads(args.tts_words_json.read_text(encoding="utf-8"))
    data = json.loads(args.caption_cues_json.read_text(encoding="utf-8"))
    failures = validate(source, data, args.max_lead_ms)
    if failures:
        raise SystemExit("SYNC ERROR: " + "\nSYNC ERROR: ".join(failures))
    print(f"Validated {len(source)} TTS word boundaries across {len(data['cues'])} synchronized cues")


if __name__ == "__main__":
    main()
