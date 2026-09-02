#!/usr/bin/env python3
"""Post-process TTS output to the standard pace: atempo speed-up plus
timestamp scaling, so every downstream consumer stays self-consistent.

Usage: python speed_post.py PROJECT_DIR [tempo]
Rewrites audio/narration.mp3, audio/narration.mp3.json, manifests/chapters.json.
"""
import json
import os
import subprocess
import sys

TEMPO = float(sys.argv[2]) if len(sys.argv) > 2 else 1.10


def main() -> None:
    root = sys.argv[1]
    mp3 = os.path.join(root, "audio", "narration.mp3")
    tmp = mp3 + ".tmp.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", mp3,
        "-filter:a", f"atempo={TEMPO},loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", "48000", "-b:a", "192k", tmp,
    ], check=True)
    os.replace(tmp, mp3)

    for rel in (os.path.join("audio", "narration.mp3.json"),
                os.path.join("manifests", "chapters.json")):
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else data.get("chapters", data)
        for it in items:
            for k in ("start", "end", "start_ms", "end_ms"):
                if k in it:
                    it[k] = round(it[k] / TEMPO)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    out = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", mp3], capture_output=True, text=True)
    print(f"[pace] tempo={TEMPO} new duration: {float(out.stdout.strip()):.2f}s")


if __name__ == "__main__":
    main()
