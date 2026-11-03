#!/usr/bin/env python3
"""measure-reveal.py · 出现方式的代理指标（3.5.1 T-P1-06）

只报告，不拦：退出码恒为 0。门禁要拦的是客观问题，这一项是给人和评审看的。

用法：
    python scripts/measure-reveal.py PROJECT [PREVIEW_MP4] [--json]

两部分：
  静态（总是跑，读 compose 产出的 src/story.ts）
      每镜 same=同帧开始最大数 / gap=相邻开始最小间隔 / conc=同时在长最大数 /
      pre=开镜前 6 帧内已开始的元素数（预铺）/ afterEnd=开始帧晚于所属句终点的事件数。
      手写场景工程没有 src/story.ts → 打印一句说明后跳到 G 部分。
  生长比 G（给了 PREVIEW_MP4 才跑）
      每镜取「切入 +24 帧」与「镜尾 −2 帧」两帧，缩到 320×180 灰度，裁掉上 10%、下 20%（字幕带），
      边缘 = |gx|+|gy| > 36；G = 末帧边缘里切入 +24 帧时还不存在的比例。镜长 < 34 帧的跳过。
      定义与 tools/growth.py（numpy 版）相同，这里用标准库重写，逐帧流式读取，不整段进内存。

只用 Python 标准库；G 部分需要 ffmpeg 在 PATH 上。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

W, H = 320, 180
FRAME = W * H
TOP, BOT = int(H * 0.10), int(H * 0.80)      # 裁掉上 10%、下 20%
ARRIVE = 24                                   # 到场帧偏移
MIN_SHOT = ARRIVE + 10
EDGE = 36
NOTE_DUR = {"circle": 14, "underline": 12, "arrow": 12, "note": 24}


def load_story(project: Path):
    """读 compose 产出的 src/story.ts；手写工程没有它，返回 None。"""
    p = project / "src" / "story.ts"
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8")
    m = re.search(r"=\s*(\{.*\})\s*(?:as const)?;?\s*$", text, re.S)
    if not m:
        return None
    return json.loads(m.group(1))


def dur_of(e: dict) -> int:
    if "dur" in e:
        return int(e["dur"])
    n = len("".join(e.get("lines") or []) or e.get("text") or "")
    return max(12, min(45, n * 4 if n > 0 else round(e.get("w", 0) / 40)))


def events_of(sh: dict) -> list[tuple[str, int, int]]:
    ev: list[tuple[str, int, int]] = []
    for fr in (sh.get("sketch") or {}).get("frames") or []:
        if fr.get("do") == "enter":
            ev.append(("sketch", fr["at"], 45))
        elif fr.get("do") in ("point", "swap", "mark", "count"):
            ev.append(("sk-" + fr["do"], fr["at"], 12))
    for e in sh.get("elements") or []:
        ev.append((e["id"], e["at"], dur_of(e)))
    for a in sh.get("annotate") or []:
        ev.append(("ann-" + a["kind"], a["at"], NOTE_DUR.get(a["kind"], 12)))
    for t in sh.get("tips") or []:
        ev.append(("tip", t["at"], 10))
    return ev


def static_rows(project: Path) -> list[dict]:
    story = load_story(project)
    if story is None:
        return []
    rows = []
    for sid, sh in story.items():
        ev = events_of(sh)
        if not ev:
            continue
        starts = sorted(a for _, a, _ in ev)
        same = max(starts.count(a) for a in starts)
        gaps = [b - a for a, b in zip(starts, starts[1:])]
        end = max(a + d for _, a, d in ev) + 1
        conc = max(sum(1 for _, a, d in ev if a <= f < a + d) for f in range(end))
        pre = sum(1 for _, a, _ in ev if a < 6)
        line_ends = sh.get("lineEnds") or [0]
        after = sum(1 for _, a, _ in ev if a > line_ends[-1])
        rows.append({"shot": sid, "n": len(ev), "same": same,
                     "gap": min(gaps) if gaps else 99, "conc": conc,
                     "pre": pre, "afterEnd": after})
    return rows


def edge_mask(frame: bytes) -> list[bool]:
    """|gx|+|gy| > 36，形状按 numpy 版：gx 取 [:-1,:]，gy 取 [:,:-1]。"""
    h = BOT - TOP
    out = [False] * ((h - 1) * (W - 1))
    base = TOP * W
    k = 0
    for y in range(h - 1):
        row = base + y * W
        nxt = row + W
        for x in range(W - 1):
            v = frame[row + x]
            gx = v - frame[row + x + 1]
            gy = v - frame[nxt + x]
            out[k] = (abs(gx) + abs(gy)) > EDGE
            k += 1
    return out


def read_frames(mp4: Path, wanted: dict[int, str]) -> dict[str, bytes]:
    """一次解码，只留需要的帧（不整段进内存）。"""
    kept: dict[str, bytes] = {}
    if not wanted:
        return kept
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(mp4), "-vf",
                             f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    last = max(wanted)
    idx = 0
    try:
        while idx <= last:
            buf = proc.stdout.read(FRAME)
            if not buf or len(buf) < FRAME:
                break
            key = wanted.get(idx)
            if key is not None:
                kept[key] = buf
            idx += 1
    finally:
        proc.stdout.close()
        proc.kill()
        proc.wait()
    return kept


def growth_rows(project: Path, mp4: Path) -> list[dict]:
    man = project / "manifests" / "shots.json"
    if not man.is_file():
        print(f"REVEAL growth: 没有 {man.relative_to(project)}，跳过", file=sys.stderr)
        return []
    shots = json.loads(man.read_text(encoding="utf-8")).get("shots") or []
    wanted: dict[int, str] = {}
    plan = []
    for s in shots:
        a, b = int(s["from"]), int(s["to"]) - 2
        if b - a < MIN_SHOT:
            continue
        plan.append((s["id"], a, b))
        wanted[a + ARRIVE] = f"{s['id']}:arrive"
        wanted[b] = f"{s['id']}:end"
    frames = read_frames(mp4, wanted)
    rows = []
    for sid, a, b in plan:
        f0, f1 = frames.get(f"{sid}:arrive"), frames.get(f"{sid}:end")
        if f0 is None or f1 is None:
            continue
        e0, e1 = edge_mask(f0), edge_mask(f1)
        grown = sum(1 for i, v in enumerate(e1) if v and not e0[i])
        tot = sum(e1)
        rows.append({"shot": sid, "growth": round(grown / max(1, tot), 2),
                     "arrival": round(sum(1 for i, v in enumerate(e1) if v and e0[i]) / max(1, tot), 2)})
    return rows


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--json"]
    as_json = "--json" in sys.argv[1:]
    if not args:
        print(__doc__.split("用法：")[1].split("两部分")[0].strip(), file=sys.stderr)
        return 0
    project = Path(args[0])
    mp4 = Path(args[1]) if len(args) > 1 else None

    rows = static_rows(project)
    if not rows:
        print("静态检查：手写场景工程没有 story.ts，跳过")
    else:
        for r in rows:
            print("%-6s n=%2d same=%d gap=%2d conc=%d pre=%d afterEnd=%d"
                  % (r["shot"], r["n"], r["same"], r["gap"], r["conc"], r["pre"], r["afterEnd"]))
        summary = {"shots": len(rows),
                   "same>1": sum(1 for r in rows if r["same"] > 1),
                   "gap<12": sum(1 for r in rows if r["gap"] < 12),
                   "conc>2": sum(1 for r in rows if r["conc"] > 2),
                   "pre>1": sum(1 for r in rows if r["pre"] > 1),
                   "afterEnd": sum(1 for r in rows if r["afterEnd"] > 0)}
        print("REVEAL static: shots=%(shots)d same>1:%(same>1)d gap<12:%(gap<12)d "
              "conc>2:%(conc>2)d pre>1:%(pre>1)d afterEnd:%(afterEnd)d" % summary)

    grown = growth_rows(project, mp4) if mp4 else []
    if grown:
        vals = sorted(r["growth"] for r in grown)
        for r in grown:
            print("  %-6s growth=%.2f arrival=%.2f" % (r["shot"], r["growth"], r["arrival"]))
        print("REVEAL growth: median=%.2f min=%.2f" % (vals[len(vals) // 2], vals[0]))

    if as_json:
        payload = {"project": str(project), "static": rows, "growth": grown}
        print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
