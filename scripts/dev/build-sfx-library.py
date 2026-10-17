#!/usr/bin/env python3
"""build-sfx-library.py · DEV-ONLY: rebuild the prebuilt SFX library with earshot.

Ordinary users never run this. The finished files are committed under
assets/lecture-template/public/sfx/lib/ together with sfx-manifest.json.

Tool: earshot 0.2.0 (https://github.com/Leonxlnx/earshot, MIT) — `earshot forge` recipes render
every sound in code (physical/modal synthesis, no recorded samples); `earshot` CLAP matching is the
quality check. Install (dev machine only):
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install git+https://github.com/Leonxlnx/earshot
Run:
    python scripts/dev/build-sfx-library.py            # render + normalise + encode + QC + manifest
    python scripts/dev/build-sfx-library.py --no-qc    # skip the CLAP model check (faster)

Pipeline per event: render a seed-bank entry of an earshot forge recipe (picked by ranking every
seed-bank render of the candidate recipes against the event description with `earshot rank`),
optional trim/fade, mono mixdown, loudness-normalise to TARGET_LUFS (K-weighted, 100 ms blocks)
with a sample-peak ceiling, encode Ogg Vorbis mono 48 kHz, then `earshot match` against the event
description and write sha256 / duration / loudness / peak / match into the manifest.
"""
from __future__ import annotations

import argparse, hashlib, importlib, json, subprocess, sys, tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import pyloudnorm as pyln

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "lecture-template" / "public" / "sfx"
LIB = OUT / "lib"
TARGET_LUFS = -18.0      # every one-shot lands at the same short-block loudness
PEAK_CEIL_DB = -1.0      # sample-peak ceiling after normalisation
BED_LUFS = -30.0         # the optional music bed sits far below everything
SR = 48000

# event -> (recipe, seed-bank index, description, intended use, options)
PICKS = {
    "whoosh":    ("whoosh", 25, "a fast clean air whoosh for a slide transition", "shot transition / camera move / handoff", {}),
    "pop":       ("pop", 6, "a short soft tonal pop", "an element appears (first beat of a shot)", {}),
    "click":     ("click", 4, "a clean crisp user interface click tap", "a list item, step or toggle lands", {}),
    "typing":    ("keypress", [0, 6, 7, 8], "a quick run of soft digital keyboard typing ticks", "code / console lines being written", {"burst": True}),
    "success":   ("notify", 13, "a short bright positive success chime, task complete", "check mark, verdict, conclusion lands", {}),
    "error":     ("glitch", 10, "a short low digital error buzz, wrong answer", "a misconception is refuted / wrong value struck", {}),
    "chart":     ("zip", 9, "a quick rising tonal synth sweep as a bar chart grows", "bars / lines / rings grow", {}),
    "highlight": ("notify", 14, "a light bright ding highlighting a word", "a key word or number is highlighted", {}),
    "chapter":   ("shimmer", 10, "a bright short logo sting chime opening a new chapter", "chapter card / new section", {}),
    "riser":     ("riser", 1, "a soft short cinematic riser building into a reveal", "builds into a chapter or payoff (ends on the hit)", {"tail": 1.5}),
}


def render_entry(recipe: str, idx: int) -> np.ndarray:
    from earshot.forge import dsp, schema
    bank = json.loads((Path(importlib.import_module("earshot").__file__).parent / "forge" / "seeds" / f"{recipe}.json").read_text())
    e = bank["entries"][idx]
    mod, fn = schema.LEGACY.get(e.get("delivered") or "", (recipe, "render"))
    m = importlib.import_module(f"earshot.forge.recipes.{mod}")
    x = np.asarray(getattr(m, fn)(dict(e["params"]), dsp.rng(e.get("seed", 0))), dtype=np.float64)
    if x.ndim == 2:
        x = x.mean(axis=0 if x.shape[0] in (1, 2) and x.shape[1] > 2 else 1)
    return x / (np.max(np.abs(x)) + 1e-12)


def fade(x: np.ndarray, fin=0.0, fout=0.01) -> np.ndarray:
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if a: x[:a] *= np.linspace(0, 1, a)
    if b: x[-b:] *= np.linspace(1, 0, b)
    return x


def burst(keys: list[np.ndarray]) -> np.ndarray:
    """a short typing run: 6 key presses at uneven intervals, varied level (deterministic)."""
    times = [0.0, 0.082, 0.151, 0.247, 0.318, 0.402]
    gains = [1.0, 0.78, 0.9, 0.7, 0.85, 0.75]
    seg = int(0.14 * SR)
    out = np.zeros(int((times[-1] + 0.16) * SR))
    for i, t in enumerate(times):
        k = fade(keys[i % len(keys)][:seg], 0, 0.04)
        s = int(t * SR)
        out[s:s + len(k)] += gains[i] * k
    return out


def loud(x: np.ndarray, sr=SR) -> float:
    meter = pyln.Meter(sr, block_size=min(0.1, len(x) / sr * 0.9))
    return float(meter.integrated_loudness(x))


def normalise(x: np.ndarray, target: float) -> tuple[np.ndarray, float, float]:
    y = x * 10 ** ((target - loud(x)) / 20)
    pk = 20 * np.log10(np.max(np.abs(y)) + 1e-12)
    if pk > PEAK_CEIL_DB:
        # transient-heavy sounds (the typing run): soft-saturate the peaks instead of turning the
        # whole sound down, so it still reaches the shared loudness target
        c = 10 ** (PEAK_CEIL_DB / 20) * 0.98
        for _ in range(4):
            y = c * np.tanh(y / c)
            gap = target - loud(y)
            if abs(gap) < 0.5:
                break
            y = y * 10 ** (gap / 20)
        y = c * np.tanh(y / c)
    return y, loud(y), 20 * np.log10(np.max(np.abs(y)) + 1e-12)


def music_bed(seconds=32.0) -> np.ndarray:
    """procedural ambient pad: two slowly cross-fading four-note chords (Cmaj9 / Am9), soft sine
    partials with slow tremolo; loops seamlessly (period = seconds)."""
    t = np.arange(int(seconds * SR)) / SR
    chords = [[130.81, 196.0, 246.94, 293.66], [110.0, 164.81, 196.0, 246.94]]
    w = 0.5 - 0.5 * np.cos(2 * np.pi * t / seconds)          # 0..1..0 over the loop
    y = np.zeros_like(t)
    for ci, ch in enumerate(chords):
        g = w if ci else 1 - w
        for k, f in enumerate(ch):
            trem = 1 + 0.15 * np.sin(2 * np.pi * t / seconds * (k + 1))
            y += g * trem * (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)) / (k + 1.5)
    return y / np.max(np.abs(y))


def encode(x: np.ndarray, dst: Path, q: int = 3) -> None:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, x.astype(np.float32), SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp.name, "-ac", "1", "-ar", str(SR),
                        "-c:a", "libvorbis", "-q:a", str(q), "-map_metadata", "-1", str(dst)], check=True)


def decoded(dst: Path) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(dst), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.float32).astype(np.float64)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-qc", action="store_true")
    a = ap.parse_args()
    LIB.mkdir(parents=True, exist_ok=True)
    entries = []
    for ev, (recipe, idx, desc, use, opt) in PICKS.items():
        if opt.get("burst"):
            x = burst([render_entry(recipe, i) for i in idx])
        else:
            x = render_entry(recipe, idx)
        if opt.get("tail"):
            x = fade(x[-int(opt["tail"] * SR):], 0.25, 0.005)
        x = fade(x, 0.0, 0.008)
        x, _, _ = normalise(x, TARGET_LUFS)
        dst = LIB / f"{ev}.ogg"
        encode(x, dst)
        d = decoded(dst)
        entries.append({"event": ev, "file": f"sfx/lib/{ev}.ogg", "sha256": hashlib.sha256(dst.read_bytes()).hexdigest(),
                        "bytes": dst.stat().st_size, "duration_s": round(len(d) / SR, 3),
                        "loudness_lufs_100ms": round(loud(d), 1), "peak_dbfs": round(20 * np.log10(np.max(np.abs(d)) + 1e-12), 1),
                        "channels": 1, "sample_rate": SR, "codec": "vorbis",
                        "source": {"tool": "earshot forge 0.2.0", "recipe": recipe, "seed_bank_index": idx},
                        "description": desc, "intended_use": use,
                        "license": "CC0-1.0 (generated in code; no recorded samples)"})
        print(f"{ev:10s} {entries[-1]['duration_s']:5.2f}s {entries[-1]['loudness_lufs_100ms']:6.1f} LUFS "
              f"peak {entries[-1]['peak_dbfs']:5.1f} {entries[-1]['bytes']:6d} B", flush=True)
    bed, _, _ = normalise(music_bed(), BED_LUFS)
    bed_dst = LIB / "bed.ogg"
    encode(bed, bed_dst, q=2)
    bd = decoded(bed_dst)
    bed_entry = {"event": "bed", "file": "sfx/lib/bed.ogg", "sha256": hashlib.sha256(bed_dst.read_bytes()).hexdigest(),
                 "bytes": bed_dst.stat().st_size, "duration_s": round(len(bd) / SR, 3),
                 "loudness_lufs_100ms": round(loud(bd), 1), "peak_dbfs": round(20 * np.log10(np.max(np.abs(bd)) + 1e-12), 1),
                 "channels": 1, "sample_rate": SR, "codec": "vorbis",
                 "source": {"tool": "scripts/dev/build-sfx-library.py music_bed()", "recipe": "additive pad"},
                 "description": "quiet ambient pad, seamless 32 s loop", "intended_use": "optional music bed (loop)",
                 "license": "CC0-1.0 (generated in code)"}
    if not a.no_qc:
        from earshot import api
        for e in entries:
            r = api.match(str(OUT.parent / e["file"]), e["description"])
            e["qc"] = {"earshot_match_z": round(float(r.get("z", 0)), 2), "verdict": r.get("verdict")}
            print(f"  QC {e['event']:10s} z={e['qc']['earshot_match_z']:+.2f} {e['qc']['verdict']}", flush=True)
    manifest = {"version": 1, "target_lufs_100ms": TARGET_LUFS, "tolerance_lu": 1.5, "peak_ceiling_dbfs": PEAK_CEIL_DB,
                "bed_lufs_100ms": BED_LUFS,
                "mix": {"narration_target_lufs": -16, "note": "one-shots play at the engine's per-event gain (0.30-0.55, about -5..-10 dB), so they sit roughly 8-12 LU under narration; the bed plays at 0.28 (about -41 LUFS)."},
                "built_with": "earshot 0.2.0 (github.com/Leonxlnx/earshot, MIT) — dev-time only",
                "events": entries + [bed_entry]}
    (OUT / "sfx-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT / 'sfx-manifest.json'} ({len(entries)} one-shots + bed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
