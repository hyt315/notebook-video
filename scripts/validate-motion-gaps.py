#!/usr/bin/env python3
"""validate-motion-gaps.py · 静止画面诊断（T3：需要已渲染的成片；结果不自动判败）

为什么需要它（2026-09-21，用户在成片 2:58 亲口报的那一类）：
    用户原话：「那个组件它没有动」——指的是一镜里**走廊早就停稳、下一件还没开始**，
    中间整整 2.5 秒画面一动不动。而当时**十道门禁全部 PASS**。

为什么别的门禁抓不到：
    · 「留白预算」（hold）判的是"**没有新增元素**的时间窗"。节拍之间漏了一段时，
      **确实**没有新增元素 —— 恰好符合留白的定义，所以它照旧放行。
      它区分不了「刻意留白」和「节拍之间漏了一段」。
    · 「节拍空档」（相邻 beat 间隔占镜长比例）也不行：实测本片 S19 的最大拍间隔只占
      **30.4%**，而 7 张**已被接受**的镜反而在 41–57% —— 按 40% 判会把好镜判死、把坏镜放过。
      根因是 beats 是**旁白节拍**，不是**画面事件**；元素绑在某一拍上、但它的动画早就跑完了。
    · 唯一的真值是**画面上到底动没动** → 只能量成片（或抽帧序列），量不了清单。

诊断（量化）：
    逐帧比较相邻两帧，列出连续「几乎完全相同」超过 `--max-static` 秒的片段，供人工
    对照该句旁白判断是有意停留还是意外卡住。静止可承载阅读、理解与记忆；本脚本不将
    它自动归类为缺陷，也不要求用无意义的环境运动填满时间。

⚠️ 一个必须写下来的方法论坑：**必须先裁掉字幕带**。
    字幕是逐字上屏的，每一句都在动 → 不裁的话，**字幕会把每一段静止都遮掉**。
    实测同一支片：全画幅只报 73 段、S19 的 2.5 秒**完全不在榜上**；
    裁掉字幕带后报 53 段，S19 的冻结段（本地帧 160..236）**清清楚楚地浮出来**。

用法：
    python scripts/validate-motion-gaps.py <project> [--video renders/film.mp4]
                                           [--max-static 2.5] [--crop-height 0.87] [--json]

退出码：0 诊断完成 / 2 用法或环境错误。零第三方依赖，Python 3.10+。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# 字幕带以下的部分不参与判定：默认裁到画面高度的 87%
# （16:9 时设计坐标 y≈940/1080；字幕框在 y≈1010 起）
DEFAULT_CROP_H = 0.87
DEFAULT_MAX_STATIC = 2.5
FPS = 30.0
# freezedetect 的噪声门限：-60dB 表示"两帧差异小于 -60dB 才算冻结"（很严，抓的是"几乎一模一样"）
NOISE = "-60dB"
MIN_SEG = 1.0  # 只统计 ≥1s 的段（低于 1s 的是正常呼吸/停顿）


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

    long_static = [r for r in rows if r["dur_s"] >= args.max_static]
    total = sum(r["dur_s"] for r in rows)

    if args.json:
        print(json.dumps({"segments": rows, "over": bad, "total_static_s": round(total, 1)}, ensure_ascii=False, indent=2))
    else:
        print("validate-motion-gaps · 静止画面诊断（T3；结果不自动判败；已裁掉字幕带 %.0f%%）" % (args.crop_height * 100))
        print(f"  冻结段（≥{MIN_SEG}s）共 {len(rows)} 段，合计 {total:.1f}s")
        if rows:
            print("  ---- 最长的 10 段 ----")
            for r in rows[:10]:
                mark = "看一眼" if r["dur_s"] >= args.max_static else "      "
                loc = f"{r['shot']} 本地帧 {r['local_from']}" if r["local_from"] is not None else "?"
                print(
                    f"  {mark} {r['start_s']:7.2f}s  {r['dur_s']:5.2f}s ({r['dur_frames']:>3} 帧)  {loc}"
                    f"  ← 该镜共 {r['shot_len']} 帧"
                )
        print(f"  供人工复核：≥{args.max_static}s 的段 {len(long_static)} 段")
        print("  请带声全速播放并对照这段所讲内容；有意静止不需要修，有信息脱节再修。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
