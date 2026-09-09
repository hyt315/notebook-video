"""Shared validation for canonical integer-millisecond speech boundaries."""
from __future__ import annotations


def timing_errors(words: object) -> list[str]:
    if not isinstance(words, list) or not words:
        return ["Expected a non-empty TTS word list"]
    errors = []
    previous_end = 0
    for i, word in enumerate(words, 1):
        if not isinstance(word, dict):
            errors.append(f"word {i}: expected an object")
            continue
        if not isinstance(word.get("part"), str) or not word["part"].strip():
            errors.append(f"word {i}: part must be non-empty text")
        start, end = word.get("start"), word.get("end")
        if type(start) is not int or type(end) is not int or start < 0 or end <= start:
            errors.append(f"word {i}: require integer 0 <= start < end")
            continue
        if start < previous_end:
            errors.append(f"word {i}: overlaps or precedes the previous word")
        previous_end = end
    return errors
