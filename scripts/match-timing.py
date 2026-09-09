#!/usr/bin/env python3
"""Align active re-voiced segments to a locked chapter timeline.

Usage: python scripts/match-timing.py PROJECT_DIR [--lock]
Uses manifests/tts-segments.json, or an unambiguous legacy segment cache.
Each chapter is tempo-matched within 0.5-2.0, then padded/trimmed to its exact
48kHz sample length. Leading silence, each gap, and any locked trailing
silence are reconstructed from the lock, never from a fixed gap.wav.
Word items are mapped by chapter interval, not by character count.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

_spec = importlib.util.spec_from_file_location(
    "tts_audio", Path(__file__).resolve().parents[1] / "assets/lecture-template/scripts/tts-openai-compatible.py")
audio = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audio)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        raise SystemExit(0 if len(sys.argv) > 1 else 2)
    root = Path(sys.argv[1]).resolve()
    if len(sys.argv) > 2 and sys.argv[2] != "--lock":
        raise ValueError("unknown option")
    chapter_path = root / "manifests/chapters.json"
    lock_path = root / "manifests/chapters-timing-lock.json"
    mp3 = root / "audio/narration.mp3"
    word_path = root / "audio/narration.mp3.json"
    chapters = audio.validate_chapters(json.loads(chapter_path.read_text(encoding="utf-8")))
    words = json.loads(word_path.read_text(encoding="utf-8"))
    paragraphs = [p.strip() for p in (root / "narration.txt").read_text(encoding="utf-8").splitlines() if p.strip()]
    groups = audio.map_words(words, chapters, paragraphs)
    if len(sys.argv) > 2:
        with tempfile.TemporaryDirectory(prefix=".timing-lock-", dir=mp3.parent) as tmp:
            tmp = Path(tmp)
            frames = audio.normalize_audio(mp3, tmp / "source.wav")
            for ch in chapters:
                ch["start_sample"], ch["end_sample"] = audio.chapter_samples(ch)
            if chapters[-1]["end_sample"] > frames + 24:
                raise ValueError("chapter timeline exceeds narration audio")
            chapters[-1]["timeline_total_samples"] = max(frames, chapters[-1]["end_sample"])
            audio.write_json(tmp / "lock.json", chapters)
            os.replace(tmp / "lock.json", lock_path)
        print(f"locked {len(chapters)} chapters")
        return
    lock = audio.validate_chapters(json.loads(lock_path.read_text(encoding="utf-8")))
    if len(lock) != len(chapters):
        raise ValueError("locked and current chapter counts differ")
    segments = audio.active_segments(root, len(lock), paragraphs)
    total = lock[-1].get("timeline_total_samples", audio.chapter_samples(lock[-1])[1])
    if not isinstance(total, int) or isinstance(total, bool) or total < audio.chapter_samples(lock[-1])[1]:
        raise ValueError("invalid locked total sample length")
    scaled = []
    for old, target, group in zip(chapters, lock, groups):
        factor = (target["end_ms"] - target["start_ms"]) / (old["end_ms"] - old["start_ms"])
        for word in group:
            item = dict(word)
            for edge in ("start", "end"):
                item[edge] = round(target["start_ms"] + (word[edge] - old["start_ms"]) * factor)
            scaled.append(item)
    audio.map_words(scaled, lock, paragraphs)
    with tempfile.TemporaryDirectory(prefix=".match-", dir=mp3.parent) as tmp:
        tmp = Path(tmp)
        # Normalize and check every ratio before rendering or publishing outputs.
        prepared = []
        for i, (segment, target) in enumerate(zip(segments, lock)):
            source = tmp / f"source{i}.wav"
            real = audio.normalize_audio(segment, source)
            start, end = audio.chapter_samples(target)
            rate = real / (end - start)
            if not 0.5 <= rate <= 2.0:
                raise ValueError(f"chapter {i + 1} ratio {rate:.6f} outside 0.5-2.0")
            prepared.append((source, start, end, rate))
        parts, position = [], 0
        for i, (source, start, end, rate) in enumerate(prepared):
            matched = tmp / f"seg-matched{i + 1:02d}.wav"
            audio.normalize_audio(source, matched, f"atempo={rate:.12g}", end - start)
            parts.extend([start - position, matched])
            position = end
        parts.append(total - position)
        audio.join_pcm(parts, tmp / "joined.wav")
        audio.normalize_audio(tmp / "joined.wav", tmp / "narration.wav",
                              "loudnorm=I=-16:TP=-1.5:LRA=11", total)
        audio.encode_mp3(tmp / "narration.wav", tmp / "narration.mp3")
        audio.write_json(tmp / "words.json", scaled)
        output_chapters = []
        for target, current in zip(lock, chapters):
            ch = dict(target)
            ch["start_sample"], ch["end_sample"] = audio.chapter_samples(ch)
            ch["timing_quality"] = current.get("timing_quality", "unspecified")
            ch["chapter_timing_quality"] = "locked"
            output_chapters.append(ch)
        audio.write_json(tmp / "chapters.json", output_chapters)
        # Retain the historical matched WAV filename as well as the current PCM.
        shutil.copyfile(tmp / "narration.wav", tmp / "narration-matched.wav")
        for source, target in [("narration.wav", mp3.with_suffix(".wav")), ("narration-matched.wav", mp3.parent / "narration-matched.wav"),
                               ("narration.mp3", mp3), ("words.json", word_path), ("chapters.json", chapter_path)]:
            os.replace(tmp / source, target)
    print(f"matched total {total / 48:.3f} ms ({total} samples @48000Hz)")


if __name__ == "__main__":
    main()
