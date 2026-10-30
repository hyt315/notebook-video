#!/usr/bin/env python3
"""validate-fusion.py · 「画面三层」融合门禁（3.5.0）

它回答的是成片评审时最刺眼的那件事：**讲火箭，全片没有一枚火箭**。
旧版没有门禁，模型全走组件也照样绿。这里在构建期按片长统计三层配比并点名修法。

判据（P0 只有一条，其余 P1）：
  P0  主题物从未出现：story 写了 `subject_of_film`（如「火箭」），全片没有一条线稿/照片对应它。
      `subject_of_film` 写 `abstract`（纯观念题）/ `software`（软件操作题）时豁免，但要写 `subject_why`。
  P1  纯组件镜头 > 片长 30%
  P1  含线稿镜头 > 60%（「这是介绍片，不是原理片」）/ < 30%（回到纯组件的机械感）
  P1  纯文字镜头 > 10%（锤子帧不计）
  P1  锤子帧 > 3
  P1  单个自拼线稿 > 12 个形，或 label 里出现「剖面 / 内部 / 拆解」
  P1  `see` 写成了文字描述（以「出现/显示」开头，或含「字幕/文字」）

用法：python scripts/validate-fusion.py PROJECT_DIR [--json]
退出码：0 通过 / 1 有 P0 / 2 用法错误。零第三方依赖。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

COMPONENT_LAYOUTS = {"code", "flow", "list", "compare", "bars", "number", "media", "quiz", "custom"}
TEXT_LAYOUTS = {"statement", "define"}
EXEMPT = {"abstract", "software"}


def load(project: Path):
    fp = project / "manifests" / "fusion.json"
    rp = project / "manifests" / "shots.resolved.json"
    if not fp.is_file():
        return None, None
    try:
        fusion = json.loads(fp.read_text(encoding="utf-8"))
    except ValueError:
        return None, None
    shots = {}
    if rp.is_file():
        try:
            shots = {s["id"]: s for s in json.loads(rp.read_text(encoding="utf-8")).get("shots") or []}
        except ValueError:
            shots = {}
    return fusion, shots


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    project = a.project.resolve()
    if not project.is_dir():
        print(f"没有这个工程目录：{project}", file=sys.stderr)
        return 2
    fusion, resolved = load(project)
    if fusion is None:
        print("validate-fusion：没有 manifests/fusion.json（手写工程 / 没跑 compose）→ 跳过")
        return 0

    p0: list[str] = []
    p1: list[str] = []
    shots = fusion.get("shots") or {}
    dur = {sid: max(1, int(s.get("to", 0)) - int(s.get("from", 0))) for sid, s in resolved.items()}
    if not dur:
        # 没有 resolved：按镜数均分，只用于配比（会标注是估算）
        dur = {sid: 1 for sid in shots}
    total = sum(dur.values()) or 1

    def share(pred) -> float:
        return sum(dur.get(sid, 1) for sid, s in shots.items() if pred(sid, s)) / total

    sketch_share = share(lambda sid, s: s.get("sketch"))
    annotated_share = share(lambda sid, s: s.get("annotate"))
    component_share = share(lambda sid, s: not s.get("sketch") and not s.get("annotate") and s.get("layout") in COMPONENT_LAYOUTS)
    text_share = share(lambda sid, s: not s.get("sketch") and not s.get("annotate")
                       and s.get("layout") in TEXT_LAYOUTS and s.get("recipe") != "hammer")
    hammer = [sid for sid, s in shots.items() if s.get("recipe") == "hammer"]

    subject = str(fusion.get("subject_of_film") or "").strip()
    if subject and subject not in EXEMPT:
        hay = " ".join(f"{s.get('sketch_label', '')} {s.get('sketch_draw', '')}" for s in shots.values())
        if subject and subject not in hay:
            p0.append(
                f"主题物「{subject}」全片没有出现：没有任何一镜的 sketch.label / parts / draw 对应它。"
                f"修法：给讲它的那一镜加 `\"sketch\":{{\"draw\":\"lib:<名字>\",\"label\":\"{subject}\","
                f"\"acts\":[{{\"at\":\"@L1\",\"do\":\"enter\"}}]}}`，或确属纯观念题时写 "
                f"`\"subject_of_film\":\"abstract\"` 并补 `subject_why`。"
            )
    elif not subject:
        p1.append("story 没有写 subject_of_film（主题里的那个东西）—— 没有它就无法判断「讲火箭却没有火箭」。写一个名词，或写 abstract / software + subject_why。")

    if component_share > 0.30:
        p1.append(f"纯组件镜头占 {component_share:.0%} > 30%：画面只有信息层，观众认不出「在讲什么」。"
                  f"挑 1–2 镜改成 recipe ① sketch-readout 或 ② component-annotated。")
    if sketch_share > 0.60:
        p1.append(f"含线稿镜头占 {sketch_share:.0%} > 60%：这是介绍片，不是原理片；把 1–2 镜换回组件。")
    elif sketch_share < 0.30:
        p1.append(f"含线稿镜头只占 {sketch_share:.0%} < 30%：回到纯组件的机械感；给讲「东西」的镜头加 sketch。")
    if text_share > 0.10:
        p1.append(f"纯文字镜头占 {text_share:.0%} > 10%（锤子帧不计）：字卡说不出「东西长什么样」。")
    if len(hammer) > 3:
        p1.append(f"锤子帧 {len(hammer)} 个 > 3（{', '.join(hammer)}）：口号化，删到 ≤3。")

    # 画得太深 / 看描述写成了文字
    for sid, s in shots.items():
        draw = str(s.get("sketch_draw") or "")
        m = re.match(r"^shapes:(\[.*\])$", draw, re.S)
        if m:
            try:
                n = len(json.loads(m.group(1)))
                if n > 12:
                    p1.append(f"{sid}: 自拼线稿 {n} 个形 > 12 —— 画得太深了，这不是原理片；删到 ≤10。")
            except ValueError:
                p1.append(f"{sid}: sketch.draw 的 shapes 不是合法 JSON。")
        label = str(s.get("sketch_label") or "")
        if any(w in label for w in ("剖面", "内部", "拆解", "爆炸图")):
            p1.append(f"{sid}: 线稿标签「{label}」在画内部结构 —— 介绍片只画外形与 1–2 个识别特征。")
        see = str(s.get("see") or "").strip()
        if see and (re.match(r"^(出现|显示|包含|画面出现)", see) or "字幕" in see or "文字" in see):
            p1.append(f"{sid}: see=「{see[:24]}」写成了文字描述；写「关掉声音观众看到什么」，"
                      f"例：『火箭第一级脱落，旁边卡片写着占 85%』。")

    if a.json:
        print(json.dumps({"p0": p0, "p1": p1,
                          "shares": {"sketch": round(sketch_share, 3), "component": round(component_share, 3),
                                     "text": round(text_share, 3), "annotated": round(annotated_share, 3)}},
                         ensure_ascii=False, indent=2))
    else:
        print(f"validate-fusion · 含线稿 {sketch_share:.0%} · 纯组件 {component_share:.0%} · 纯文字 {text_share:.0%}"
              f" · 讲解层 {annotated_share:.0%} · 锤子帧 {len(hammer)}")
        for x in p0:
            print(f"  P0 {x}")
        for x in p1:
            print(f"  P1 {x}")
        print(f"结论：P0={len(p0)} P1={len(p1)} → {'PASS' if not p0 else 'FAIL'}")
    return 1 if p0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
