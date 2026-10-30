#!/usr/bin/env python3
"""silent-timing.py — 无旁白片的字幕时间轴（静音占位的「假 TTS 词边界」），读速可配置（3.3.0）。

没有 TTS 时，字幕的读速就是整片的节奏。以前手写工程只能照 4.5 字/秒手搓 audio/narration.mp3.json，
那是给"有人念"的组件路线定的速度，在纯字幕的手作片里只有 Netflix 成人上限（9 字/秒）的一半，片子慢、静帧全是半句话。

用法：
    python scripts/silent-timing.py LINES_TXT OUT_JSON [--cps N] [--project DIR]
                                    [--start-ms 300] [--comma-ms 150] [--stop-ms 300] [--line-gap-ms 450] [--para-gap-ms 900]

  LINES_TXT  一行一句（就是 manifests/semantic-caption-lines.txt）；空行 = 段落停顿（多停 --para-gap-ms）。
  OUT_JSON   词边界列表 [{part, start, end}]，与 TTS 适配器契约相同（references/tts-audio.md），
             之后照常跑 build-semantic-captions.py 绑定成 caption-cues.json。
  --cps      读速（加权字/秒：汉字计 1，ASCII 字母 / 数字计 0.5，与 validate-presentation 同口径）。
             缺省：--project 是手作皮肤（journal / papercut / archive）→ 6.5；否则 4.5（组件路线的既有速度）。
             上限 9（validate-presentation 的成人档）。

词片切法：每个汉字一片，标点粘在前一个字上；连续的 ASCII 字母 / 数字是一片。逗号类后多停 --comma-ms，句末多停 --stop-ms。
只用标准库。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CRAFT = {"journal", "papercut", "archive"}
CPS_CRAFT = 6.5
CPS_COMPONENT = 4.5
CPS_MAX = 9.0
COMMA = set("，、；：,;:")
STOP = set("。！？!?…")
TRAIL = COMMA | STOP | set("」』”）)》")
LEAD = set("「『“（(《")


def skin_of(project: Path | None) -> str | None:
    if not project:
        return None
    a = project / "src" / "theme" / "active.ts"
    m = re.search(r"from\s+'\./(\w+)'", a.read_text(encoding="utf-8")) if a.is_file() else None
    return m.group(1) if m else None


def pieces(line: str) -> list[tuple[str, float]]:
    """把一句切成 (词片, 权重)。权重 = 朗读 / 阅读需要的"字"数。"""
    out: list[list] = []
    pending_lead = ""
    for tok in re.findall(r"[A-Za-z0-9][A-Za-z0-9.'’\-]*|\s+|.", line):
        if tok.isspace():
            if out:
                out[-1][0] += " "
            continue
        if tok in LEAD:
            pending_lead += tok
            continue
        if tok in TRAIL and out:
            out[-1][0] = out[-1][0].rstrip() + tok
            continue
        weight = 0.5 * len(tok) if re.match(r"[A-Za-z0-9]", tok) else 1.0
        out.append([pending_lead + tok, weight])
        pending_lead = ""
    if pending_lead and out:
        out[-1][0] += pending_lead
    return [(p.rstrip() if i == len(out) - 1 else p, w) for i, (p, w) in enumerate(out)]


def build(lines: list[str], cps: float, start_ms: int = 300, comma_ms: int = 150, stop_ms: int = 300,
          line_gap_ms: int = 450, para_gap_ms: int = 900) -> list[dict]:
    unit = 1000.0 / cps
    t = float(start_ms)
    words: list[dict] = []
    para = False
    for raw in lines:
        line = raw.strip()
        if not line:
            para = True
            continue
        if words:
            t += para_gap_ms if para else line_gap_ms
        para = False
        for part, weight in pieces(line):
            dur = unit * weight
            words.append({"part": part, "start": int(round(t)), "end": int(round(t + dur * 0.95))})
            t += dur
            tail = part.rstrip()[-1:]
            if tail in STOP:
                t += stop_ms
            elif tail in COMMA:
                t += comma_ms
    return words


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lines")
    ap.add_argument("out")
    ap.add_argument("--cps", type=float)
    ap.add_argument("--project", type=Path)
    ap.add_argument("--start-ms", type=int, default=300)
    ap.add_argument("--comma-ms", type=int, default=150)
    ap.add_argument("--stop-ms", type=int, default=300)
    ap.add_argument("--line-gap-ms", type=int, default=450)
    ap.add_argument("--para-gap-ms", type=int, default=900)
    a = ap.parse_args(argv)
    cps = a.cps or (CPS_CRAFT if skin_of(a.project) in CRAFT else CPS_COMPONENT)
    if not 1.0 <= cps <= CPS_MAX:
        print(f"--cps={cps} 超出 1–{CPS_MAX}（validate-presentation 的成人读速上限是 {CPS_MAX} 加权字/秒）", file=sys.stderr)
        return 2
    lines = Path(a.lines).read_text(encoding="utf-8").splitlines()
    words = build(lines, cps, a.start_ms, a.comma_ms, a.stop_ms, a.line_gap_ms, a.para_gap_ms)
    Path(a.out).write_text(json.dumps(words, ensure_ascii=False) + "\n", encoding="utf-8")
    end = words[-1]["end"] / 1000 if words else 0
    print(f"silent-timing: {len(words)} 个词片 · {cps:g} 字/秒 · 末字结束于 {end:.2f}s → {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
