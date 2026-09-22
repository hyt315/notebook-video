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


def dual_copy_failures(cues_path: Path) -> list[str]:
    """防"校验一份、渲染另一份"：真实工程同时存在两份 caption-cues.json —
    `manifests/caption-cues.json`（各校验器按约定读这份）与 `src/caption-cues.json`
    （`src/index.tsx` 直接 import、真正进渲染的那份）。CLI `sync` 只在渲染前**静默复制**
    manifests→src，不是门禁：单独跑校验、或直接开 Studio 时，两份漂移零检出。
    判据与技能侧一致性锁同口径（validate-skill-consistency 对模板、
    validate-official-example 对示例工程都是字节相等）：两份都在、字节不等 → 报问题。
    只有 manifests/ 一份（或传的就是 src/ 那份）时不适用，跳过。"""
    if cues_path.name != "caption-cues.json" or cues_path.parent.name != "manifests":
        return []
    twin = cues_path.parent.parent / "src" / "caption-cues.json"
    if not twin.is_file():
        return []
    if cues_path.read_bytes() != twin.read_bytes():
        return [
            "caption-cues dual-copy divergence: validated manifests/caption-cues.json != rendered "
            f"src/caption-cues.json (you are about to validate one copy while index.tsx ships the other; "
            "run `notebook-video sync PROJECT` or copy manifests/ over src/)"
        ]
    return []


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
    failures = dual_copy_failures(args.caption_cues_json)
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
