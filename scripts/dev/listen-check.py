#!/usr/bin/env python3
"""listen-check.py · DEV-ONLY: objective SFX listen-check without rendering video.

Inputs (all produced by an audio-only Remotion render — no video frames are encoded):
  mix.wav    full mix      npx remotion render src/index.tsx NotebookVideoFilm mix.wav --codec=wav
  sfx.wav    SFX-only stem (same render with narration + bed volume 0)
  plan.json  {"plan": planSfx(...)}  (bundle a 3-line script with esbuild that prints planSfx)

Reports integrated loudness, true peak (4x oversampled), clipped samples, each cue's measured
transient vs its visual hit frame (pass: |err| <= 1 frame at 30 fps), the minimum gap between cues
(pass: >= 150 ms), and the bed ducking depth (bed = mix - sfx; valid when narration is a silent placeholder).
Needs numpy, soundfile, pyloudnorm, scipy.

Usage: python scripts/dev/listen-check.py mix.wav sfx.wav plan.json
"""
import json, sys
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import resample_poly

FPS = 30

def stats(name, x, sr):
    L = pyln.Meter(sr).integrated_loudness(x)
    tp = 20 * np.log10(np.abs(resample_poly(x, 4, 1, axis=0)).max() + 1e-12)
    print(f"{name}: I={L:.2f} LUFS  TP={tp:.2f} dBTP  clipped={int((np.abs(x) >= 0.999).sum())}")

def main(mix_p, sfx_p, plan_p):
    plan = json.load(open(plan_p))["plan"]
    m, sr = sf.read(mix_p); s, _ = sf.read(sfx_p)
    stats("mix", m, sr); stats("sfx", s, sr)
    mono = s.mean(1) if s.ndim > 1 else s
    k = int(sr * 0.005); env = np.sqrt(np.convolve(mono ** 2, np.ones(k) / k, "same"))
    bad = []
    for c in plan:
        if c["event"] == "riser":  # riser peaks at its end, which coincides with the chapter hit
            continue
        st = int(c["at"] / FPS * sr)
        err = (st + int(np.argmax(env[st:st + int(sr * 0.6)]))) / sr * FPS - c["hit"]
        print(f"  {c['event']:<9} hit {c['hit']:>5}  err {err:+.2f} f")
        if abs(err) > 1: bad.append(c)
    hits = sorted(c["hit"] for c in plan if c["event"] != "riser")
    gap = min(np.diff(hits)) / FPS * 1000 if len(hits) > 1 else 1e9
    print(f"cues off by >1 frame: {len(bad)}   min gap: {gap:.0f} ms")
    b = (m - s); b = b.mean(1) if b.ndim > 1 else b; F = sr / FPS
    r = lambda a, z: 20 * np.log10(np.sqrt((b[int(a * F):int(z * F)] ** 2).mean()) + 1e-12)
    d = [r(c["hit"] + 1, c["hit"] + 4) - r(c["hit"] - 25, c["hit"] - 15) for c in plan if 40 < c["hit"] < len(b) / F - 50]
    if d: print(f"bed ducking under cues: median {np.median(d):.1f} dB")
    sys.exit(1 if bad or gap < 150 else 0)

if __name__ == "__main__":
    main(*sys.argv[1:4])
