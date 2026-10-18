#!/usr/bin/env python3
"""audit-sfx.py · DEV-ONLY: score every cue in the prebuilt SFX library (v4.5).

Ordinary users never run this (it needs numpy + soundfile + pyloudnorm). It reads
assets/lecture-template/public/sfx/lib/*.ogg + sfx-manifest.json and prints, per cue:

  dur      file length (ms)
  lead     leading near-silence before the first sample above peak-30 dB (ms)
  hit      time of the transient (max of a 5 ms RMS envelope) from the file start (ms)
  err      |hit - offsetMs| in frames at 30 fps — how far the audible hit lands from the visual
           frame once the engine applies the manifest's offsetMs (start the file that much earlier)
  mix      LUFS (100 ms blocks) after the engine gain   (gain from sfx-manifest.json `gain`)
  vsBed    mix - bed mix (LU) — every event must sit clearly above the bed (>= 10 LU)
  vsLadder mix - the event's target rung (see LADDER) — 0 is perfect, |x| <= 1.5 passes
  cent     spectral centroid (Hz) — timbre brightness
  peakPos  hit / dur — where the energy peaks inside the file (risers must peak at the end)
  score    0-100 = timing 40 + level 30 + timbre 30

Usage:
    python scripts/dev/audit-sfx.py [--json out.json] [--legacy]   # --legacy ignores gain/offsetMs (v4.4 behaviour)
"""
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

import numpy as np
import soundfile as sf
import pyloudnorm as pyln

ROOT = Path(__file__).resolve().parents[2]
SFX = ROOT / "assets" / "lecture-template" / "public" / "sfx"
FPS = 30
# v4.4 engine gains (legacy) — used with --legacy to reproduce the "before" column
LEGACY_GAIN = {"whoosh": 0.42, "pop": 0.45, "click": 0.38, "typing": 0.34, "success": 0.5,
               "error": 0.36, "chart": 0.4, "highlight": 0.4, "chapter": 0.55, "riser": 0.36}
LEGACY_BED = 0.28
# loudness ladder (LUFS after gain): structural stings loudest, ticks quietest; all >= 10 LU over the bed.
LADDER = {"chapter": -24.0, "success": -25.0, "error": -26.0, "pop": -25.5, "chart": -26.0,
          "highlight": -27.0, "whoosh": -27.5, "riser": -28.0, "click": -28.5, "typing": -30.0}
# timbre expectations: (min centroid Hz, max centroid Hz, max duration ms, peak position range)
TIMBRE = {
    "whoosh": (900, 6000, 520, (0.15, 0.7)),
    "pop": (150, 3500, 260, (0.0, 0.35)),
    "click": (1500, 9000, 120, (0.0, 0.4)),
    "typing": (1200, 9000, 900, (0.0, 1.0)),
    "success": (900, 6000, 900, (0.0, 0.5)),
    "error": (150, 2500, 450, (0.0, 0.5)),
    "chart": (300, 5000, 700, (0.2, 1.0)),
    "highlight": (2000, 9000, 420, (0.0, 0.25)),
    "chapter": (900, 7000, 1400, (0.0, 0.45)),
    "riser": (500, 7000, 1700, (0.85, 1.0)),
}


def load(p: Path):
    x, sr = sf.read(str(p), always_2d=True)
    return x.mean(axis=1).astype(np.float64), sr


def measure(x: np.ndarray, sr: int) -> dict:
    peak = float(np.max(np.abs(x)) + 1e-12)
    thr = peak * 10 ** (-30 / 20)
    idx = np.nonzero(np.abs(x) >= thr)[0]
    lead = float(idx[0]) / sr * 1000 if len(idx) else 0.0
    win = max(1, int(sr * 0.005))
    env = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, mode="same"))
    hit = float(np.argmax(env)) / sr * 1000
    dur = len(x) / sr * 1000
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    freqs = np.fft.rfftfreq(len(x), 1 / sr)
    cent = float((spec * freqs).sum() / (spec.sum() + 1e-12))
    meter = pyln.Meter(sr, block_size=0.1)
    pad = np.concatenate([x, np.zeros(int(sr * 0.2))]) if len(x) < sr * 0.4 else x
    lufs = float(meter.integrated_loudness(pad))
    return {"dur": dur, "lead": lead, "hit": hit, "cent": cent, "lufs": lufs, "peakPos": hit / max(1.0, dur)}


def score(ev: str, m: dict, gain: float, offset_ms: float, bed_mix: float) -> dict:
    err_ms = abs(m["hit"] - offset_ms)
    err_f = err_ms / (1000 / FPS)
    timing = 40.0 * max(0.0, 1.0 - max(0.0, err_f - 0.5) / 2.5)  # <=0.5 f full marks, 3 f -> 0
    mix = m["lufs"] + 20 * np.log10(max(gain, 1e-6))
    vs_bed = mix - bed_mix
    vs_ladder = mix - LADDER[ev]
    level = 30.0 * max(0.0, 1.0 - max(0.0, abs(vs_ladder) - 1.0) / 4.0)
    if vs_bed < 10:
        level *= 0.5
    lo, hi, maxdur, (p0, p1) = TIMBRE[ev]
    t = 30.0
    if not (lo <= m["cent"] <= hi):
        t -= 10
    if m["dur"] > maxdur:
        t -= 10 * min(1.0, (m["dur"] - maxdur) / maxdur + 0.5)
    if not (p0 <= m["peakPos"] <= p1):
        t -= 10
    return {"errFrames": round(err_f, 2), "mix": round(mix, 1), "vsBed": round(vs_bed, 1), "vsLadder": round(vs_ladder, 1),
            "score": round(timing + level + max(0.0, t))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--legacy", action="store_true", help="ignore manifest gain/offsetMs (v4.4 engine)")
    a = ap.parse_args()
    man = json.loads((SFX / "sfx-manifest.json").read_text(encoding="utf-8"))
    bed_x, bed_sr = load(SFX / "lib" / "bed.ogg")
    bed_gain = LEGACY_BED if a.legacy else float(man.get("mix", {}).get("bed_gain", LEGACY_BED))
    bed_mix = measure(bed_x, bed_sr)["lufs"] + 20 * np.log10(bed_gain)
    rows = []
    print(f"bed mix {bed_mix:.1f} LUFS (gain {bed_gain})")
    print(f"{'event':<10}{'dur':>6}{'lead':>6}{'hit':>6}{'off':>6}{'err_f':>7}{'mix':>7}{'vsBed':>7}{'vsLad':>7}{'cent':>7}{'pPos':>6}{'score':>7}")
    for e in man["events"]:
        ev = e["event"]
        if ev not in LADDER:
            continue
        x, sr = load(SFX.parent / e["file"])
        m = measure(x, sr)
        gain = LEGACY_GAIN[ev] if a.legacy else float(e.get("gain", LEGACY_GAIN[ev]))
        off = 0.0 if a.legacy else float(e.get("offsetMs", 0.0))
        s = score(ev, m, gain, off, bed_mix)
        rows.append({"event": ev, **{k: round(v, 3) for k, v in m.items()}, "gain": gain, "offsetMs": off, **s})
        print(f"{ev:<10}{m['dur']:>6.0f}{m['lead']:>6.0f}{m['hit']:>6.0f}{off:>6.0f}{s['errFrames']:>7.2f}{s['mix']:>7.1f}{s['vsBed']:>7.1f}{s['vsLadder']:>7.1f}{m['cent']:>7.0f}{m['peakPos']:>6.2f}{s['score']:>7}")
    print(f"mean score {np.mean([r['score'] for r in rows]):.1f}")
    if a.json:
        Path(a.json).write_text(json.dumps({"bedMix": round(bed_mix, 1), "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
