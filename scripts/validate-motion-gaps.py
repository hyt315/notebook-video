#!/usr/bin/env python3
"""validate-motion-gaps.py · 「画面上真的没动」门禁（T3：成片后验，需要已渲染的成片）

为什么需要它：一镜里元素早就停稳、下一件还没开始，画面可以整整几秒一动不动，而清单类门禁都会 PASS。

为什么别的门禁抓不到：
    · 「留白预算」（hold）判的是"**没有新增元素**的时间窗"。节拍之间漏了一段时，
      **确实**没有新增元素 —— 恰好符合留白的定义，所以它照旧放行。
      它区分不了「刻意留白」和「节拍之间漏了一段」。
    · 「节拍空档」（相邻 beat 间隔占镜长比例）也不行：出问题的镜拍间隔占比可能并不高，
      而节奏正常的镜反而更高 —— 按固定比例判会把好镜判死、把坏镜放过。
      根因是 beats 是**旁白节拍**，不是**画面事件**；元素绑在某一拍上、但它的动画早就跑完了。
    · 唯一的真值是**画面上到底动没动** → 只能量成片（或抽帧序列），量不了清单。

判据（量化）：
    逐帧比较相邻两帧的差异，连续「几乎完全相同」超过 `--max-static` 秒即 P0。
    实现在 ffmpeg 的 `freezedetect` 滤镜上（零新增依赖，本仓库已有 ffmpeg 前置）。

⚠️ 一个必须写下来的方法论坑：**必须先裁掉字幕带**。
    字幕是逐字上屏的，每一句都在动 → 不裁的话，**字幕会把每一段静止都遮掉**。
    `--crop-height` 只量字幕带以上的画面。

用法：
    python scripts/validate-motion-gaps.py <project> [--video renders/film.mp4]
                                           [--max-static 2.5] [--crop-height 0.87] [--json]

退出码：0 通过 / 1 有超标的静止段 / 2 用法或环境错误。零第三方依赖，Python 3.10+。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract import C  # noqa: E402  跨语言常量：assets/lecture-template/src/contract.json

# 字幕带以下的部分不参与判定：默认裁到画面高度的 87%
# （16:9 时设计坐标 y≈940/1080；字幕框在 y≈1010 起）
DEFAULT_CROP_H = 0.87
DEFAULT_MAX_STATIC = 2.5
FPS = float(C["FPS"])
# freezedetect 的噪声门限：-60dB 表示"两帧差异小于 -60dB 才算冻结"（很严，抓的是"几乎一模一样"）
NOISE = "-60dB"
MIN_SEG = 1.0  # 只统计 ≥1s 的段（低于 1s 的是正常呼吸/停顿）
# 锤子帧（满屏一句话，SKILL.md 规定停 1.5–2.5 s）本来就该静止：落在锤子镜里的静止段
# 放宽到 3.0 s（2.5 s + 前后半秒的入场收尾），超过仍是 P0。
HAMMER_MAX_STATIC = 3.0
# 片尾定格统一口径（与 ffmpeg freezedetect 同源）：末镜落在片尾最后 1.5s 内的自然收尾定格放宽至 3.5s，
# 并在报告中单独标注为 closing_hold；片中任何非片尾静止段仍严格按 max_static（2.5s）判 P0。
CLOSING_HOLD_MAX_STATIC = 3.5
CLOSING_TAIL_WINDOW_S = 1.5
HAMMER_LIVE = {"StampBanner", "HandLettering", "Seal"}


def hammer_shots(project: Path, shots: list) -> set:
    """锤子镜的 id：auto 路线看 manifests/fusion.json 的 recipe=hammer，手写路线看 live 里的锤子件。"""
    ids = {s.get("id") for s in shots if HAMMER_LIVE & set(s.get("live") or [])}
    fz = project / "manifests" / "fusion.json"
    if fz.is_file():
        per = (json.loads(fz.read_text(encoding="utf-8")).get("shots") or {})
        ids |= {sid for sid, v in per.items() if isinstance(v, dict) and v.get("recipe") == "hammer"}
    return ids


def judge(rows: list, max_static: float, hammers: set, total_s: float = 0.0) -> list:
    """超限的静止段：一般镜 ≥ max_static；锤子镜 ≥ HAMMER_MAX_STATIC；末镜片尾定格 ≥ CLOSING_HOLD_MAX_STATIC。"""
    def lim(r: dict) -> float:
        base = max(max_static, HAMMER_MAX_STATIC) if r.get("shot") in hammers else max_static
        if total_s > 0 and r.get("is_closing_hold"):
            return max(base, CLOSING_HOLD_MAX_STATIC)
        return base
    return [r for r in rows if r["dur_s"] >= lim(r)]


def run_freezedetect(video: Path, crop_h: float) -> list[tuple[float, float]]:
    if not shutil.which("ffmpeg"):
        print("找不到 ffmpeg：本门禁需要 ffmpeg（freezedetect）。", file=sys.stderr)
        raise SystemExit(2)
    vf = f"crop=iw:ih*{crop_h}:0:0,freezedetect=n={NOISE}:d={MIN_SEG}"
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vf", vf, "-an", "-f", "null", "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    out = proc.stdout + proc.stderr
    starts = [float(x) for x in re.findall(r"freeze_start:\s*([0-9.]+)", out)]
    durs = [float(x) for x in re.findall(r"freeze_duration:\s*([0-9.]+)", out)]
    return list(zip(starts, durs))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--video", default="renders/film.mp4")
    ap.add_argument("--max-static", type=float, default=DEFAULT_MAX_STATIC)
    ap.add_argument("--crop-height", type=float, default=DEFAULT_CROP_H)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    project = Path(args.project).resolve()
    video = project / args.video
    if not video.is_file():
        print(f"成片不存在：{video}（本门禁是 T3 后验，需要先渲染）", file=sys.stderr)
        return 2
    shots_path = project / "manifests" / "shots.resolved.json"
    if not shots_path.is_file():
        print(f"缺少 {shots_path}", file=sys.stderr)
        return 2
    doc = json.loads(shots_path.read_text(encoding="utf-8"))
    shots = doc["shots"] if isinstance(doc, dict) and "shots" in doc else doc

    def shot_of(frame: int) -> dict | None:
        for s in shots:
            if int(s["from"]) <= frame < int(s["to"]):
                return s
        return None

    segs = run_freezedetect(video, args.crop_height)
    rows = []
    for start, dur in segs:
        f0 = round(start * FPS)
        s = shot_of(f0)
        rows.append(
            {
                "start_s": round(start, 2),
                "dur_s": round(dur, 2),
                "dur_frames": round(dur * FPS),
                "from_abs": f0,
                "shot": (s or {}).get("id", "?"),
                "local_from": f0 - int(s["from"]) if s else None,
                "shot_len": int(s["duration"]) if s else None,
            }
        )
    rows.sort(key=lambda r: -r["dur_s"])

    hammers = hammer_shots(project, shots)
    total_s = max((int(s.get("to", 0)) for s in shots), default=0) / FPS
    last_shot_id = shots[-1].get("id") if shots else None
    for r in rows:
        end_s = r["start_s"] + r["dur_s"]
        r["is_closing_hold"] = bool(total_s > 0 and r.get("shot") == last_shot_id and end_s >= total_s - CLOSING_TAIL_WINDOW_S)
    bad = judge(rows, args.max_static, hammers, total_s=total_s)
    total = sum(r["dur_s"] for r in rows)

    if args.json:
        print(json.dumps({"segments": rows, "over": bad, "total_static_s": round(total, 1)}, ensure_ascii=False, indent=2))
    else:
        print("validate-motion-gaps · 画面静止后验（T3，量成片；已裁掉字幕带 %.0f%%）" % (args.crop_height * 100))
        print(f"  冻结段（≥{MIN_SEG}s）共 {len(rows)} 段，合计 {total:.1f}s")
        if rows:
            print("  ---- 最长的 10 段 ----")
            for r in rows[:10]:
                mark = "P0" if r in bad else ("锤" if r["shot"] in hammers and r["dur_s"] >= args.max_static else "  ")
                loc = f"{r['shot']} 本地帧 {r['local_from']}" if r["local_from"] is not None else "?"
                print(
                    f"  {mark} {r['start_s']:7.2f}s  {r['dur_s']:5.2f}s ({r['dur_frames']:>3} 帧)  {loc}"
                    f"  ← 该镜共 {r['shot_len']} 帧"
                )
        print(f"  结论：超 {args.max_static}s 的静止段 {len(bad)} 段 → {'PASS' if not bad else 'FAIL'}")
        if bad:
            print("  修法：给这一段补一个**真实事件**（让主体继续演化，或把下一件的入场提前），")
            print("        不是加装饰动画——旁白在讲、画面停着，观众读作卡住。")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
