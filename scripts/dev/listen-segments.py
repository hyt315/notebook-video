#!/usr/bin/env python3
"""listen-segments.py · DEV-ONLY：把成片切成三段，供固定盲听（P2-20）。

电平合格 ≠ 听感合格。响度 / 峰值 / 削波这些数字抓不到三件事：
  旁白下拟音是否掩字、连续翻页是否机械、静音占位与真人声的动态差异。
这三件只能用**同一套耳朵、同一套段落**反复听——所以段落要固定，不能每次现挑。

三段（与本脚本的切点一致，改这里就改协议）：
  1. 开场      0 – 20 s   人声刚进来时拟音在不在、压不压字
  2. 连续转场  密集翻页区  连着 3 次以上翻页，听机械感（P2-20 的音色轮换就为这一段）
  3. 结论      末 20 s    收束音效、配乐尾、最后一个字的可懂度

用法：
  python scripts/dev/listen-segments.py mix.wav out_dir
  → out_dir/seg1-open.wav / seg2-turns.wav / seg3-close.wav + segments.json（切点与听法）

打分（每段 1–5，记进 segments.json 的 `verdict`）：
  可懂度 intelligibility   1=听不清关键辅音 … 5=字字清楚
  疲劳   fatigue           1=30 秒就烦 … 5=听完全片不累
  机械感 mechanical        1=明显在循环 … 5=听不出是同一采样（连续转场段才打）

依赖：ffmpeg（无 numpy）。维护者可选，普通用户渲染不需要。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

FPS = 30
OPEN_S = 20.0
CLOSE_S = 20.0
MIN_TURN_GAP_S = 2.5      # 相邻翻页在此间隔内算「连续」
MIN_TURNS = 3             # 连续翻页至少这么多次才算「密集区」


def probe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        raise SystemExit(f"读不到时长：{path}（{e}）") from e


def find_turn_run(plan: list[dict], total: float) -> tuple[float, float] | None:
    """音效计划里找最密集的一段连续翻页。plan 项要有 {event, hit}（帧）。"""
    hits = sorted((c["hit"] / FPS) for c in plan if c.get("event") == "page" and "hit" in c)
    best: tuple[int, float, float] | None = None  # (次数, 起, 止)
    i = 0
    while i < len(hits):
        j = i
        while j + 1 < len(hits) and hits[j + 1] - hits[j] <= MIN_TURN_GAP_S:
            j += 1
        n = j - i + 1
        if n >= MIN_TURNS and (best is None or n > best[0]):
            best = (n, hits[i], hits[j])
        i = j + 1
    if not best:
        return None
    # 前后各留 3 s 听上下文
    return max(0.0, best[1] - 3.0), min(total, best[2] + 3.0)


def cut(src: Path, dst: Path, start: float, end: float) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
         "-i", str(src), "-c", "copy", str(dst)],
        check=True, timeout=120)


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    mix = Path(argv[1])
    out = Path(argv[2])
    if not mix.is_file():
        print(f"找不到 {mix}", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    total = probe_duration(mix)

    plan_path = mix.parent / "sfx-plan.json"
    plan = []
    if plan_path.is_file():
        try:
            plan = json.loads(plan_path.read_text(encoding="utf-8")).get("plan", [])
        except json.JSONDecodeError:
            plan = []

    segs = []
    # 1. 开场
    a, b = 0.0, min(OPEN_S, total)
    segs.append(("seg1-open", a, b, "人声刚进来时拟音在不在、压不压字；开场字的可懂度"))
    # 2. 连续转场
    run = find_turn_run(plan, total) if plan else (total * 0.4, total * 0.4 + 12.0)
    if run and run[1] - run[0] >= 4.0:
        segs.append(("seg2-turns", run[0], run[1], "连着 3 次以上翻页：听机械感、纸声是否同质"))
    else:
        # 没有音效计划或翻页不够密集 → 取中段 12 s，并在报告里说明
        mid = max(0.0, total / 2 - 6.0)
        segs.append(("seg2-turns", mid, min(total, mid + 12.0),
                     "（未找到 ≥3 次连续翻页，取中段）听转场声是否同质、是否压旁白"))
    # 3. 结论
    a = max(0.0, total - CLOSE_S)
    segs.append(("seg3-close", a, total, "收束音效、配乐尾、最后一个字的可懂度"))

    files = []
    for name, a, b, listen_for in segs:
        if b - a < 1.0:
            continue
        dst = out / f"{name}.wav"
        cut(mix, dst, a, b)
        files.append({"name": name, "start_s": round(a, 2), "end_s": round(b, 2),
                      "file": dst.name, "listen_for": listen_for,
                      "verdict": {"intelligibility": None, "fatigue": None, "mechanical": None}})

    report = {
        "source": str(mix),
        "duration_s": round(total, 2),
        "protocol": "P2-20 三段盲听（固定段落，不要每次现挑）",
        "scoring": {
            "intelligibility": "1=关键辅音听不清 … 5=字字清楚（每段都打）",
            "fatigue": "1=30 秒就烦 … 5=听完全片不累（每段都打）",
            "mechanical": "1=明显在循环 … 5=听不出是同一采样（只在 seg2 打）",
        },
        "pass_bar": {
            "intelligibility": "≥4，且关键辅音不被拟音掩（seg1 重点）",
            "mechanical": "≥3（seg2；音色轮换后应 ≥4）",
            "fatigue": "≥3",
            "level": "电平指标不退化（validate-audio-levels.py 仍 PASS）",
        },
        "segments": files,
    }
    (out / "segments.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"三段已切到 {out}/：")
    for f in files:
        print(f"  {f['file']:<18} {f['start_s']:6.2f} – {f['end_s']:.2f} s   {f['listen_for']}")
    print(f"打分表：{out / 'segments.json'}（填 verdict 后归档）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
