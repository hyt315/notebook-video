#!/usr/bin/env python3
"""Apply a tempo once to fresh TTS audio and scale its chapter/word timeline.

Usage: python speed-post.py PROJECT_DIR [tempo=1.10]
Stages all outputs before replacement. manifests/speed-post.json records audio
hashes so rerunning on an already processed narration is refused.
"""
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile

_spec = importlib.util.spec_from_file_location("tts_audio", Path(__file__).with_name("tts-openai-compatible.py"))
audio = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audio)


def main():
    root = Path(sys.argv[1]).resolve()
    tempo = float(sys.argv[2]) if len(sys.argv) > 2 else 1.10
    if not math.isfinite(tempo) or not 0.5 <= tempo <= 2.0:
        raise ValueError("tempo must be finite and within 0.5-2.0")
    mp3 = root / "audio/narration.mp3"
    word_path = root / "audio/narration.mp3.json"
    chapter_path = root / "manifests/chapters.json"
    meta_path = root / "manifests/speed-post.json"
    chapters = audio.validate_chapters(json.loads(chapter_path.read_text(encoding="utf-8")))
    words = json.loads(word_path.read_text(encoding="utf-8"))
    paragraphs = [p.strip() for p in (root / "narration.txt").read_text(encoding="utf-8").splitlines() if p.strip()]
    groups = audio.map_words(words, chapters, paragraphs)
    history = []
    if meta_path.exists():
        old = json.loads(meta_path.read_text(encoding="utf-8"))
        history = old.get("processed_audio_sha256") if isinstance(old, dict) else None
        if not isinstance(history, list) or any(not isinstance(h, str) or len(h) != 64 for h in history):
            raise ValueError("invalid speed-post metadata")
    source_hash = audio.file_hash(mp3)
    if source_hash in history:
        raise ValueError("narration has already been speed-processed; synthesize fresh audio first")
    manifest_path = root / "manifests/tts-segments.json"
    if manifest_path.exists():
        audio.active_segments(root, len(chapters))
    scaled_chapters, scaled_words = [], []
    for ch, group in zip(chapters, groups):
        start, end = audio.chapter_samples(ch)
        updated = dict(ch)
        updated.update(start_sample=round(start / tempo), end_sample=round(end / tempo))
        updated.update(start_ms=round(updated["start_sample"] / 48), end_ms=round(updated["end_sample"] / 48))
        scaled_chapters.append(updated)
        ratio = (updated["end_ms"] - updated["start_ms"]) / (ch["end_ms"] - ch["start_ms"])
        for word in group:
            item = dict(word)
            for edge in ("start", "end"):
                item[edge] = round(updated["start_ms"] + (word[edge] - ch["start_ms"]) * ratio)
            scaled_words.append(item)
    audio.map_words(scaled_words, scaled_chapters, paragraphs)
    with tempfile.TemporaryDirectory(prefix=".speed-", dir=mp3.parent) as tmp:
        tmp = Path(tmp)
        source_frames = audio.normalize_audio(mp3, tmp / "source.wav")
        if audio.chapter_samples(chapters[-1])[1] > source_frames + 24:
            raise ValueError("chapter timeline exceeds narration audio")
        target_frames = max(round(source_frames / tempo), audio.chapter_samples(scaled_chapters[-1])[1])
        if "timeline_total_samples" in scaled_chapters[-1]:
            scaled_chapters[-1]["timeline_total_samples"] = target_frames
        audio.normalize_audio(tmp / "source.wav", tmp / "narration.wav",
                              f"atempo={tempo:.12g},loudnorm=I=-16:TP=-1.5:LRA=11", target_frames)
        audio.encode_mp3(tmp / "narration.wav", tmp / "narration.mp3")
        output_hash = audio.file_hash(tmp / "narration.mp3")
        metadata = {"version": 1, "tempo": tempo, "input_sha256": source_hash,
                    "output_sha256": output_hash, "processed_audio_sha256": list(dict.fromkeys(history + [output_hash])),
                    "sample_rate": audio.SAMPLE_RATE, "samples": target_frames,
                    "timing_quality": chapters[0].get("timing_quality", "unspecified")}
        audio.write_json(tmp / "words.json", scaled_words)
        audio.write_json(tmp / "chapters.json", scaled_chapters)
        audio.write_json(tmp / "metadata.json", metadata)
        for source, target in [("narration.wav", mp3.with_suffix(".wav")), ("narration.mp3", mp3),
                               ("words.json", word_path), ("chapters.json", chapter_path), ("metadata.json", meta_path)]:
            os.replace(tmp / source, target)
    print(f"[pace] tempo={tempo} new duration: {target_frames / audio.SAMPLE_RATE:.3f}s")


if __name__ == "__main__":
    main()
