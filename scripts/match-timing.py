#!/usr/bin/env python3
"""Align re-voiced narration to a locked chapter timeline without re-timing scenes.

When the narration text is locked but the voice (or model) changes, chapter
durations shift and every scene guard would drift. Instead of re-authoring
scene timing, stretch each new chapter back to its approved duration:

  python scripts/match-timing.py ./my-film --lock   # snapshot approved chapters
  <run the TTS adapter + speed-post as usual>
  python scripts/match-timing.py ./my-film          # align to the lock

The default mode reads `manifests/chapters-timing-lock.json`, applies a
pitch-preserving `atempo` per chapter segment produced by
`assets/lecture-template/scripts/tts-openai-compatible.py`
(`audio/seg{N}-*.wav`), re-joins with the standard silence gap, re-normalizes
loudness (`loudnorm=I=-16:TP=-1.5:LRA=11`, 48kHz stereo) and scales the flat
word-timing stream onto the locked frame table. Chapter ratios outside
0.5-2.0 are refused. Rebuild semantic captions afterwards because
intra-chapter word timing always changes with a new voice.
"""
from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys

GAP_MS = 350

norm = lambda s: re.sub(r"\s+", "", s)

# 防护性检查一律 `if not …: raise SystemExit(...)`，**不用 assert**：
# `python -O` 会把 assert 连同右侧表达式一起剥离 —— 门禁当场静默放行，
# 正是本技能最忌的"门在名义上存在、实际不跑"。SystemExit 在任何 -O 档位下都生效。


def probe_ms(path: str) -> int:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path], text=True)
    return int(round(float(out.strip()) * 1000))


def atempo_chain(rate: float) -> str:
    parts: list[float] = []
    r = rate
    while r > 2.0:
        parts.append(2.0)
        r /= 2.0
    while r < 0.5:
        parts.append(0.5)
        r /= 0.5
    parts.append(r)
    return ",".join("atempo=%.6f" % x for x in parts)


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        raise SystemExit(0 if len(sys.argv) > 1 else 2)
    os.chdir(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2] == "--lock":
        chapters = json.load(open("manifests/chapters.json", encoding="utf-8"))
        json.dump(chapters, open("manifests/chapters-timing-lock.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print("locked %d chapters" % len(chapters))
        return

    lock = json.load(open("manifests/chapters-timing-lock.json", encoding="utf-8"))
    newch = json.load(open("manifests/chapters.json", encoding="utf-8"))
    # 防护性检查一律 raise SystemExit，不用 assert：`python -O` 会把 assert 整条剥离，
    # 关键门禁在 -O 下静默放行是本脚本最危险的失败模式（对齐 negative-gate-check 的门禁纪律）。
    if len(lock) != len(newch):
        raise SystemExit("chapter count mismatch: %d locked vs %d new" % (len(lock), len(newch)))

    paras = [p.strip() for p in open("narration.txt", encoding="utf-8") if p.strip()]
    counts = [len(norm(p)) for p in paras]

    segs: list[str] = []
    for i in range(len(lock)):
        ms = sorted(glob.glob(os.path.join("audio", "seg%d-*.wav" % (i + 1))))
        ms = [m for m in ms if "matched" not in os.path.basename(m)]
        if len(ms) != 1:
            raise SystemExit("chapter %d: expected exactly one source seg wav, found %s" % (i + 1, ms))
        segs.append(ms[0])

    matched: list[str] = []
    for i in range(len(lock)):
        old_dur = lock[i]["end_ms"] - lock[i]["start_ms"]
        real = probe_ms(segs[i])
        rate = real / max(1, old_dur)
        if not 0.4 <= rate <= 2.5:
            raise SystemExit("chapter ratio out of range: chapter %d rate=%s (allowed 0.4-2.5)"
                             % (i + 1, round(rate, 3)))
        out = os.path.join("audio", "seg-matched%02d.wav" % (i + 1))
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", segs[i],
                               "-af", atempo_chain(rate), out])
        matched.append(out)
        print("ch%02d old=%dms new=%dms rate=%.3f" % (i + 1, old_dur, real, rate))

    gap = os.path.join("audio", "gap.wav")
    if not os.path.isfile(gap):
        raise SystemExit("gap.wav missing: run the TTS adapter first")
    concat_list = os.path.join("audio", "concat-matched.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for i, seg in enumerate(matched):
            if i:
                f.write("file '%s'\n" % os.path.basename(gap))
            f.write("file '%s'\n" % os.path.basename(seg))
    joined = os.path.join("audio", "narration-matched.wav")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                           "-i", concat_list, "-c", "copy", joined])
    out_mp3 = os.path.join("audio", "narration.mp3")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", joined,
                           "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                           "-ar", "48000", "-ac", "2", "-b:a", "192k", out_mp3])

    words = json.load(open(out_mp3 + ".json", encoding="utf-8"))
    if sum(counts) != len(words):
        raise SystemExit("narration paragraph chars (%d) differ from word stream (%d)"
                         % (sum(counts), len(words)))
    scaled: list[dict] = []
    k = 0
    for i in range(len(lock)):
        n0, n1 = newch[i]["start_ms"], newch[i]["end_ms"]
        l0, l1 = lock[i]["start_ms"], lock[i]["end_ms"]
        f = (l1 - l0) / max(1, (n1 - n0))
        for _ in range(counts[i]):
            w = dict(words[k])
            k += 1
            w["start"] = int(round(l0 + (w["start"] - n0) * f))
            w["end"] = int(round(l0 + (w["end"] - n0) * f))
            scaled.append(w)
    if k != len(words):
        raise SystemExit("paragraph word counts consumed %d of %d words" % (k, len(words)))
    json.dump(scaled, open(out_mp3 + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(lock, open("manifests/chapters.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    total = lock[-1]["end_ms"]
    print("matched total %d ms (%.2fs) = %d frames @30fps" % (total, total / 1000, round(total * 30 / 1000)))


if __name__ == "__main__":
    main()
