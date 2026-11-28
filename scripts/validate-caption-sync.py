#!/usr/bin/env python3
"""Verify subtitle text, word order and timings exactly match TTS boundaries."""

from __future__ import annotations

import argparse
import json
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate_report import emit  # noqa: E402  统一结果：设了 NV_GATE_JSON 就逐条追加一行 JSON
from story_caption import MAX_CHARS  # noqa: E402  上限与生成端同源（contract.json）
from story_text import cap_chars  # noqa: E402  字幕行长唯一口径（CaptionFitGate 的 captionChars 与之同义）


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", text)


def core(word: dict) -> tuple[str, int, int]:
    return str(word["part"]), int(word["start"]), int(word["end"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tts_words_json", type=Path)
    parser.add_argument("caption_cues_json", type=Path)
    parser.add_argument("--max-lead-ms", type=int, default=80)
    parser.add_argument("--max-chars", type=int, default=MAX_CHARS,
                        help="characters per subtitle line after stripping trailing punctuation (0 = off)")
    # 单条字幕在屏时长（到下一条出现为止；最后一条不查）：Netflix 通用字幕要求最短 5/6 s、最长 7 s
    # （https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617）。短于下限读不完 = 失败；长于上限只警告。
    parser.add_argument("--min-cue-sec", type=float, default=0.83, help="minimum on-screen seconds per cue (0 = off)")
    parser.add_argument("--max-cue-sec", type=float, default=7.0, help="warn above this many on-screen seconds per cue (0 = off)")
    parser.add_argument("--audio", type=Path, default=None, help="optional narration audio file to verify duration against last TTS word")
    args = parser.parse_args()

    source = json.loads(args.tts_words_json.read_text(encoding="utf-8"))
    data = json.loads(args.caption_cues_json.read_text(encoding="utf-8"))
    cues = data.get("cues", data) if isinstance(data, dict) else data
    if not isinstance(source, list) or not isinstance(cues, list):
        raise SystemExit("Expected a TTS word list and a subtitle cue list")

    flattened = []
    failures: list[str] = []
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
        n = cap_chars(str(cue.get("text", "")))
        if args.max_chars > 0 and n > args.max_chars:
            failures.append(f"cue {index}: {n} characters > {args.max_chars} per line ({cue.get('text')!r}); "
                            f"re-run build-semantic-captions.py (it splits at legal breaks) or shorten the line")
        lead = int(words[0]["start"]) - int(cue["start_ms"])
        if lead < 0 or lead > args.max_lead_ms:
            failures.append(f"cue {index}: visual lead {lead}ms exceeds 0–{args.max_lead_ms}ms")
        flattened.extend(words)

    warnings = []
    for index, cue in enumerate(cues, 1):
        if not isinstance(cue.get("start_ms"), (int, float)):
            continue
        if index >= len(cues) or not isinstance(cues[index].get("start_ms"), (int, float)):
            continue  # 最后一条留在屏上直到片尾，时长由片尾决定
        shown = (cues[index]["start_ms"] - cue["start_ms"]) / 1000
        if args.min_cue_sec > 0 and shown < args.min_cue_sec:
            failures.append(f"cue {index}: on screen {shown:.2f}s < {args.min_cue_sec}s ({cue.get('text')!r}); merge it with a neighbour "
                            f"or slow the reading speed (silent-timing.py --cps)")
        if args.max_cue_sec > 0 and shown > args.max_cue_sec:
            warnings.append(f"cue {index}: on screen {shown:.2f}s > {args.max_cue_sec}s ({cue.get('text')!r}); split it or let the gap breathe without a caption")

    if [core(word) for word in flattened] != [core(word) for word in source]:
        failures.append("flattened cue words do not exactly match the complete TTS word stream")
    if isinstance(data, dict) and data.get("estimated") is True:
        warnings.append("caption timings are marked estimated=true (fallback split); run TTS or faster-whisper for word-exact sync")
    if args.audio is not None and args.audio.is_file() and source:
        import subprocess
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(args.audio)],
                capture_output=True, text=True, timeout=15,
            )
            dur_ms = round(float(r.stdout.strip()) * 1000)
            last_end = max(int(w["end"]) for w in source)
            if last_end - dur_ms > 500:
                failures.append(f"last TTS word ends at {last_end}ms but audio duration is only {dur_ms}ms (>500ms overrun)")
            elif dur_ms - last_end > 2500:
                warnings.append(f"audio duration {dur_ms}ms exceeds last TTS word {last_end}ms by {dur_ms - last_end}ms")
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    emit("validate-caption-sync", failures, warnings, str(args.caption_cues_json))
    if failures:
        for failure in failures:
            print(f"SYNC ERROR: {failure}")
        raise SystemExit(f"{len(failures)} caption sync failure(s)")
    for warning in warnings:
        print(f"SYNC WARN: {warning}")
    print(f"Validated {len(source)} TTS word boundaries across {len(cues)} synchronized cues")


if __name__ == "__main__":
    main()
