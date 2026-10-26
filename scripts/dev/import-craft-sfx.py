#!/usr/bin/env python3
"""import-craft-sfx.py · DEV-ONLY: add the craft (paper / ink / scissors / stamp) foley to the SFX library.

Ordinary users never run this. The finished .ogg files and their manifest entries are committed.

Source: Kenney "RPG Audio" (https://kenney.nl/assets/rpg-audio) — CC0 1.0, real recordings, so they can ship
inside this Apache-2.0 repository (unlike Sonniss / Mixkit packs, which forbid redistribution as sound effects).
Download the zip once and pass the folder that contains Audio/*.ogg:

    python scripts/dev/import-craft-sfx.py /path/to/kenney_rpg-audio

Per event (same contract as build-sfx-library.py / tune-sfx.py, so validate-audio-levels checks it unchanged):
trim leading near-silence, cut to keep_ms with a fade-out, mono 48 kHz, normalise to -18 LUFS (100 ms blocks,
pyloudnorm) with a -1 dBFS sample-peak ceiling, encode Ogg Vorbis, measure the transient (5 ms RMS maximum) →
offsetMs, and gain = the linear gain that puts the cue on its loudness-ladder rung.
Needs numpy + pyloudnorm + ffmpeg (maintainer machine only).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
import pyloudnorm as pyln

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "assets" / "lecture-template" / "public"
MAN = PUB / "sfx" / "sfx-manifest.json"
SR = 48000
TARGET = -18.0

# event: (kenney file, keep_ms, fade_out_ms, ladder LUFS, description, intended use)
CRAFT = {
    "page":   ("bookFlip2.ogg", 520, 160, -26.0, "a real paper page flip", "craft skins: a new sheet / page turn (replaces whoosh on transitions)"),
    "place":  ("bookPlace1.ogg", 300, 120, -26.5, "a sheet or card laid down on paper", "craft skins: a paper piece / photo lands (replaces pop)"),
    "snip":   ("knifeSlice.ogg", 360, 120, -26.0, "a quick blade cut", "papercut: a cut / a piece removed"),
    "stamp":  ("bookClose.ogg", 380, 140, -25.0, "a soft heavy thump", "a seal is pressed / a verdict lands (replaces success in craft skins)"),
    "rustle": ("cloth2.ogg", 420, 160, -28.5, "a dry paper-like rustle", "craft skins: small paper handling / tick (replaces click)"),
    "latch":  ("metalClick.ogg", 220, 80, -27.5, "a small metal click", "a loupe lands / an instrument clicks into place"),
}


def decode(src: Path) -> np.ndarray:
    with tempfile.TemporaryDirectory() as td:
        w = Path(td) / "a.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(w)], check=True)
        with wave.open(str(w)) as fh:
            x = np.frombuffer(fh.readframes(fh.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return x


def encode(x: np.ndarray, dst: Path) -> None:
    with tempfile.TemporaryDirectory() as td:
        w = Path(td) / "a.wav"
        with wave.open(str(w), "wb") as fh:
            fh.setnchannels(1); fh.setsampwidth(2); fh.setframerate(SR)
            fh.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(w), "-c:a", "libvorbis", "-q:a", "5", str(dst)], check=True)


def process(src: Path, keep_ms: int, fade_ms: int) -> np.ndarray:
    x = decode(src)
    thr = 10 ** (-45 / 20) * np.max(np.abs(x))
    start = int(np.argmax(np.abs(x) > thr))
    x = x[max(0, start - int(0.004 * SR)):]
    x = x[: int(keep_ms * SR / 1000)]
    n = int(fade_ms * SR / 1000)
    if n and len(x) > n:
        x[-n:] *= np.linspace(1, 0, n) ** 2
    x[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    meter = pyln.Meter(SR, block_size=0.1)
    ceil = 10 ** (-1.8 / 20)  # Vorbis 编码会抬一点峰值：留 0.8 dB 余量到 -1 dBFS
    # 归一到 -18 LUFS；瞬态型素材（翻页、咔嗒）峰值会顶出天花板 → tanh 软限幅后再归一，迭代几次收敛
    for _ in range(6):
        lu = meter.integrated_loudness(np.concatenate([x, np.zeros(int(0.1 * SR), np.float32)]))
        x = x * 10 ** ((TARGET - lu) / 20)
        if np.max(np.abs(x)) <= ceil:
            break
        x = (ceil * np.tanh(x / ceil)).astype(np.float32)
    return x


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    src_dir = Path(argv[0])
    audio = src_dir / "Audio" if (src_dir / "Audio").is_dir() else src_dir
    man = json.loads(MAN.read_text(encoding="utf-8"))
    events = [e for e in man["events"] if e["event"] not in CRAFT]
    meter = pyln.Meter(SR, block_size=0.1)
    for ev, (fname, keep, fade, ladder, desc, use) in CRAFT.items():
        x = process(audio / fname, keep, fade)
        dst = PUB / "sfx" / "lib" / f"{ev}.ogg"
        encode(x, dst)
        y = decode(dst)
        lu = meter.integrated_loudness(np.concatenate([y, np.zeros(int(0.1 * SR), np.float32)]))
        peak = 20 * np.log10(np.max(np.abs(y)) + 1e-9)
        win = int(0.005 * SR)
        rms = np.sqrt(np.convolve(y ** 2, np.ones(win) / win, mode="same"))
        offset_ms = round(float(np.argmax(rms)) / SR * 1000, 1)
        gain = round(10 ** ((ladder - TARGET) / 20), 3)
        events.append({
            "event": ev, "file": f"sfx/lib/{ev}.ogg", "sha256": hashlib.sha256(dst.read_bytes()).hexdigest(), "bytes": dst.stat().st_size,
            "duration_s": round(len(y) / SR, 3), "loudness_lufs_100ms": round(float(lu), 1), "peak_dbfs": round(float(peak), 1),
            "channels": 1, "sample_rate": SR, "codec": "vorbis",
            "source": {"pack": "Kenney RPG Audio", "url": "https://kenney.nl/assets/rpg-audio", "file": f"Audio/{fname}", "author": "Kenney Vleugels (kenney.nl)"},
            "description": desc, "intended_use": use, "license": "CC0-1.0 (Kenney RPG Audio, recorded samples)",
            "tuned": {"keep_ms": keep, "fade_out_ms": fade}, "gain": gain, "offsetMs": offset_ms,
            "timing_note": "offsetMs = transient position; the engine starts the file that much earlier so the hit lands on the visual frame",
        })
        man["mix"]["ladder_lufs"][ev] = ladder
        print(f"{ev:7s} ← {fname:16s} {len(y) / SR:.2f}s  {lu:6.1f} LUFS  peak {peak:5.1f}  offset {offset_ms:6.1f} ms  gain {gain}")
    man["events"] = events
    MAN.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("manifest updated; now sync src/sfx.ts SFX_GAIN / SFX_OFFSET_MS from the printed values")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
