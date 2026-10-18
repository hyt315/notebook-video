#!/usr/bin/env python3
"""tune-sfx.py · DEV-ONLY: tighten the weak cues and write per-cue gain / offsetMs into the manifest.

Ordinary users never run this — the tuned .ogg files and sfx-manifest.json are committed.
Needs numpy + soundfile + pyloudnorm + ffmpeg. Idempotent: it always starts from the untuned originals
kept in git (`git show 6c10ead:<file>` is NOT needed — the originals are read from --src, which defaults
to the current files; run it once per library rebuild).

What it does per cue (see TUNE):
  · trim leading near-silence and cut the tail where it only smears (fade-out instead of a long decay);
  · optional high-pass / low-pass to separate timbres that were too alike (highlight vs success);
  · re-normalise to -18 LUFS (100 ms) with a -1 dBFS ceiling, encode Ogg Vorbis mono 48 kHz;
  · measure the transient (5 ms RMS max) → `offsetMs`: the engine starts the file that much
    BEFORE the visual frame so the audible hit lands on the frame (±1 frame);
  · `gain` = the linear gain that puts the cue on its rung of the loudness ladder (audit-sfx.LADDER),
    so every cue sits 12–17 LU over the bed and the cues are balanced against each other.
"""
from __future__ import annotations

import hashlib, importlib.util, json, subprocess, sys, tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import pyloudnorm as pyln

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "assets" / "lecture-template" / "public"
MAN = PUB / "sfx" / "sfx-manifest.json"
SR = 48000
spec = importlib.util.spec_from_file_location("audit", Path(__file__).with_name("audit-sfx.py"))
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)  # type: ignore

# event: (start_ms, keep_ms, fade_out_ms, highpass_hz, lowpass_hz, fade_in_ms)
TUNE = {
    "whoosh":    (60, 260, 90, 250, 0, 4),      # was 359 ms with a 74 ms dead lead and the hit 4 f late
    "highlight": (0, 190, 120, 1800, 0, 0),     # was a 380 ms "notify" ring that read like a quieter success
    "riser":     (420, 1080, 12, 120, 0, 60),   # was 1.5 s with 0.54 s of near-silence; now 1.08 s, peak at the end
    "error":     (380, 210, 60, 0, 3200, 3),    # the glitch's buzz peaked at 537 ms (16 f late) — keep the hit
    "chapter":   (0, 900, 260, 0, 0, 0),        # shorter tail, hit handled by offsetMs
    "chart":     (0, 0, 0, 0, 0, 0),
    "pop": (0, 0, 0, 0, 0, 0), "click": (0, 0, 0, 0, 0, 0), "typing": (0, 0, 0, 0, 0, 0), "success": (0, 0, 0, 0, 0, 0),
}
# where the visual hit is, relative to the frame the engine schedules the cue on (documented in src/sfx.ts)
NOTE = {
    "whoosh": "scheduled at the transition midpoint (shot boundary + 7 f); offsetMs pulls the file earlier so the air peak lands there",
    "riser": "ends on the hit: scheduled so its peak (offsetMs) lands on the chapter's first frame",
}


def biquad(x: np.ndarray, kind: str, fc: float) -> np.ndarray:
    import math
    w0 = 2 * math.pi * fc / SR; q = 0.707; al = math.sin(w0) / (2 * q); c = math.cos(w0)
    if kind == "hp":
        b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]
    else:
        b = [(1 - c) / 2, 1 - c, (1 - c) / 2]
    a = [1 + al, -2 * c, 1 - al]
    b = [v / a[0] for v in b]; a = [1.0, a[1] / a[0], a[2] / a[0]]
    y = np.zeros_like(x); x1 = x2 = y1 = y2 = 0.0
    for i, v in enumerate(x):
        o = b[0] * v + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
        x2, x1, y2, y1 = x1, v, y1, o; y[i] = o
    return y


def process(x: np.ndarray, t) -> np.ndarray:
    st, keep, fo, hp, lp, fi = t
    s = int(st * SR / 1000)
    x = x[s:]
    if keep:
        x = x[: int(keep * SR / 1000)]
    if hp:
        x = biquad(x, "hp", hp)
    if lp:
        x = biquad(x, "lp", lp)
    if fi:
        n = min(len(x), int(fi * SR / 1000)); x[:n] *= np.linspace(0, 1, n)
    if fo:
        n = min(len(x), int(fo * SR / 1000)); x[-n:] *= np.linspace(1, 0, n) ** 2
    return x


def normalise(x: np.ndarray) -> np.ndarray:
    meter = pyln.Meter(SR, block_size=0.1)
    pad = np.concatenate([x, np.zeros(int(SR * 0.2))]) if len(x) < SR * 0.4 else x
    l = meter.integrated_loudness(pad)
    y = x * 10 ** ((-18.0 - l) / 20)
    pk = np.max(np.abs(y))
    ceil = 10 ** (-1 / 20)
    return y * (ceil / pk) if pk > ceil else y


def encode(x: np.ndarray, dst: Path) -> None:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, x.astype(np.float32), SR)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp.name, "-ac", "1", "-ar", str(SR), "-c:a", "libvorbis", "-q:a", "4", str(dst)], check=True)


def main() -> int:
    man = json.loads(MAN.read_text(encoding="utf-8"))
    bed_x, _ = audit.load(PUB / "sfx" / "lib" / "bed.ogg")
    bed_gain = 0.28
    for e in man["events"]:
        ev = e["event"]
        if ev not in TUNE:
            continue
        src = PUB / e["file"]
        x, sr = audit.load(src)
        assert sr == SR, sr
        t = TUNE[ev]
        if any(t) and not e.get("tuned"):
            y = normalise(process(x.copy(), t))
            encode(y, src)
            e["tuned"] = {"start_ms": t[0], "keep_ms": t[1], "fade_out_ms": t[2], "highpass_hz": t[3], "lowpass_hz": t[4], "fade_in_ms": t[5]}
        x, _ = audit.load(src)
        m = audit.measure(x, SR)
        gain = float(np.clip(10 ** ((audit.LADDER[ev] - m["lufs"]) / 20), 0.12, 0.9))
        e["gain"] = round(gain, 3)
        e["offsetMs"] = round(m["hit"], 1)
        if e.get("tuned"):
            e["duration_s"] = round(m["dur"] / 1000, 3)
            e["loudness_lufs_100ms"] = -18.0
            e["peak_dbfs"] = round(20 * np.log10(np.max(np.abs(x)) + 1e-12), 1)
            e["bytes"] = src.stat().st_size
            e["sha256"] = hashlib.sha256(src.read_bytes()).hexdigest()
        if ev in NOTE:
            e["timing_note"] = NOTE[ev]
    man["version"] = 2
    man.setdefault("mix", {})["bed_gain"] = bed_gain
    man["mix"]["ladder_lufs"] = audit.LADDER
    man["mix"]["min_gap_ms"] = 150
    man["mix"]["max_hits_per_min"] = 24
    man["mix"]["duck"] = {"depth": 0.45, "attack_frames": 2, "release_frames": 12}
    man["mix"]["note"] = (" each cue carries `gain` (linear, puts it on its loudness-ladder rung after the engine mix) and "
                          "`offsetMs` (transient position; the engine starts the file that much earlier so the hit lands on the "
                          "visual frame). The bed ducks to 45% under every cue. Weak models never set volumes by hand.")
    MAN.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("tuned + manifest written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
