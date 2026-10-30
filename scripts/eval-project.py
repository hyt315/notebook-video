#!/usr/bin/env python3
"""eval-project.py — 把一个成片工程当**数据**看一遍，并支持两版对比。

用法：
    python scripts/eval-project.py PROJECT
    python scripts/eval-project.py 旧工程 新工程      # 加一列 Δ
    python scripts/eval-project.py PROJECT --json

为什么要有它：门禁回答"有没有画错"，评审回答"好不好看"，但**优化有没有用**这两个都答不了——
改完一版，你只记得"好像顺了点"。这里把片子拆成可比的数：节奏、版式多样、介质、转场、
相机、字幕密度、空场读数。两版并排，改没改好一眼能看出来。

**它不下判断。** 阈值只在 `validate-composition.py` / `validate-caption-sync.py` / `validate-audio-levels.py`
里存在一处，这里不复制第二份——否则同一个数会在两处漂移（这个坑项目里已经踩过：
`cinema-camera.md` 正文和门禁表就曾对不上）。所以本脚本只输出数字与 Δ，判据请跑门禁。

只读 `manifests/` 与 `renders/` 里已有的文件，不渲染、不改工程。
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def pct(part: int, whole: int) -> float:
    return round(100.0 * part / whole, 1) if whole else 0.0


def weighted_chars(text: str) -> float:
    """与 silent-timing.py / validate-presentation.py 同口径的"加权字数"：
    汉字与标点计 1，ASCII 字母/数字计 0.5，空白不计。

    不能直接 len()：那会把 "GitHub" 按 6 字算，而生成器按 3 字算——
    两个都叫"字/秒"的数放在一起比，等于自造一个矛盾。
    """
    total = 0.0
    for ch in str(text):
        if ch.isspace():
            continue
        total += 0.5 if (ch.isascii() and ch.isalnum()) else 1.0
    return total


def measure(project: Path) -> dict:
    table = load(project / "manifests" / "shots.resolved.json")
    if not table:
        raise SystemExit(f"读不到镜头表：{project / 'manifests' / 'shots.resolved.json'}")
    shots = table.get("shots") or []
    if not shots:
        raise SystemExit(f"镜头表是空的：{project}")
    fps = 30.0
    durations = [float(s.get("duration") or 0) for s in shots]
    total_frames = float(table.get("duration") or sum(durations))
    secs = total_frames / fps

    mean_len = statistics.fmean(durations)
    cv = (statistics.pstdev(durations) / mean_len) if mean_len else 0.0
    ratio = (max(durations) / min(durations)) if min(durations) else 0.0

    skeletons = [str(s.get("skeleton") or "?") for s in shots]
    adj_repeat = sum(1 for a, b in zip(skeletons, skeletons[1:]) if a == b)
    skel_count: dict[str, int] = {}
    for k in skeletons:
        skel_count[k] = skel_count.get(k, 0) + 1

    media_kinds: set[str] = set()
    per_shot_media: list[int] = []
    for s in shots:
        m = s.get("media") or []
        media_kinds.update(str(x) for x in m)
        per_shot_media.append(len(m))

    live = set()
    for s in shots:
        live.update(str(x) for x in (s.get("live") or []))

    transitions = [str(s.get("transition") or "?") for s in shots]
    hard_cut = sum(1 for t in transitions if t in ("hard", "cut", "none"))

    cam_shots = 0
    max_zoom = 1.0
    over_text_cap = 0
    for s in shots:
        keys = s.get("keys") or []
        zs = [float(k.get("s") or 1.0) for k in keys if isinstance(k, dict)]
        peak = max(zs) if zs else 1.0
        if s.get("cinema") or s.get("cameraIntent"):
            cam_shots += 1
        max_zoom = max(max_zoom, peak)
        # 1.35 = TEXT_ZOOM_MAX（references/shot-language.md §相机上限）；只在这里统计，不当判据。
        if peak > 1.35 and "text" in [str(x) for x in (s.get("media") or [])]:
            over_text_cap += 1

    cues = (load(project / "manifests" / "caption-cues.json") or {}).get("cues") or []
    cue_chars = [weighted_chars(c.get("text") or "") for c in cues]
    cue_secs = [max(1e-6, (float(c.get("speech_end_ms", 0)) - float(c.get("start_ms", 0))) / 1000.0) for c in cues]
    cps = statistics.fmean([n / d for n, d in zip(cue_chars, cue_secs)]) if cues else 0.0

    cover = load(project / "renders" / "fill-coverage.json") or {}
    largest = [float(v.get("largest") or 0) for v in cover.values() if isinstance(v, dict)]
    blank = [float(v.get("blank") or 0) for v in cover.values() if isinstance(v, dict)]

    return {
        "片长": round(secs, 1),
        "镜数": len(shots),
        "平均镜长": round(mean_len / fps, 2),
        "最短镜": round(min(durations) / fps, 2),
        "最长镜": round(max(durations) / fps, 2),
        "镜长变异": round(cv, 2),
        "最长/最短": round(ratio, 2),
        "版式种类": len(skel_count),
        "最大版式占比%": pct(max(skel_count.values()), len(shots)),
        "相邻同版式": adj_repeat,
        "介质种类": len(media_kinds),
        "每镜介质数": round(statistics.fmean(per_shot_media), 2) if per_shot_media else 0.0,
        "组件种类": len(live),
        "转场种类": len(set(transitions)),
        "硬切占比%": pct(hard_cut, len(transitions)),
        "有运镜镜占比%": pct(cam_shots, len(shots)),
        "最大推近": round(max_zoom, 2),
        "文字镜超1.35": over_text_cap,
        "字幕条数": len(cues),
        "字幕条/分": round(len(cues) / (secs / 60.0), 1) if secs else 0.0,
        "加权字/秒": round(cps, 2),
        "最长字幕加权字数": round(max(cue_chars), 1) if cue_chars else 0,
        "空场:最小主体": round(min(largest), 2) if largest else None,
        "空场:最大空白列": int(max(blank)) if blank else None,
    }


def render(rows: list[tuple[str, dict, dict | None]]) -> str:
    width = max(len(k) for k, _, _ in rows)
    has_b = any(b is not None for _, _, b in rows)
    head = f"{'指标'.ljust(width)}  {'A'.rjust(8)}"
    if has_b:
        head += f"  {'B'.rjust(8)}  {'Δ'.rjust(8)}"
    out = [head, "-" * len(head)]
    for key, a, b in rows:
        line = f"{key.ljust(width)}  {str(a).rjust(8)}"
        if has_b:
            if b is None:
                line += f"  {'-'.rjust(8)}  {'-'.rjust(8)}"
            else:
                delta = b - a if isinstance(a, (int, float)) and isinstance(b, (int, float)) else None
                mark = ""
                if delta is not None and abs(delta) > 1e-9:
                    mark = f"{delta:+.2f}".rstrip("0").rstrip(".")
                line += f"  {str(b).rjust(8)}  {mark.rjust(8)}"
        out.append(line)
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Measure a finished notebook-video project, optionally diff two.")
    ap.add_argument("projects", nargs="+", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if len(args.projects) > 2:
        raise SystemExit("最多两个工程（A 旧 / B 新）")

    a = measure(args.projects[0])
    b = measure(args.projects[1]) if len(args.projects) == 2 else None
    if args.json:
        print(json.dumps({"A": {"project": str(args.projects[0]), "metrics": a},
                          **({"B": {"project": str(args.projects[1]), "metrics": b}} if b else {})},
                         ensure_ascii=False, indent=1))
        return 0

    rows = [(k, a[k], b[k] if b else None) for k in a]
    print(f"A = {args.projects[0]}" + (f"\nB = {args.projects[1]}" if b else ""))
    print()
    print(render(rows))
    if b:
        moved = [(k, a[k], b[k]) for k in a
                 if isinstance(a[k], (int, float)) and isinstance(b[k], (int, float)) and a[k] != b[k]]
        print(f"\n{len(moved)}/{len(a)} 项有变化。")
    print("\n只测量、不判分：阈值在 validate-composition / validate-caption-sync / validate-audio-levels 里，"
          "要判好坏请跑门禁与独立评审。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
