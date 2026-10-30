#!/usr/bin/env python3
"""validate-fusion.py · 「手账页承载 + 组件讲概念」配比门禁（3.6.0）

它回答两件事，都是成片评审里最刺眼的：
  · 讲细胞，全片没有一张细胞图（只有组件卡片在讲）；
  · 反过来，全片都是手账页，概念其实一句没讲清。

3.6.0 改口径：**线稿不再是主线**。实测（cell 片 vs 线稿样张）线稿当解释图时
画面像剪贴画，比不画更差；讲解视频需要的是「一页有人在研究的手账」——
真图版 / 标本 + 手写批注，再由组件把概念讲透。所以：
  手账页（layout=page）  = 承载：演示某件事、给你看那个真东西
  组件（flow/compare/…） = 讲解：把概念拆开、对比、算清
  线稿                  = 可选：只在标本速写里用，不再计入「必须有」

判据（P0 一条，其余 P1）：
  P0  主题物从未出现：subject 不在任何一镜的 手账页说明 / 线稿标签 / see 里。
      `subject_of_film` 写 `abstract`（纯观念题）/ `software`（软件操作题）时豁免，但要写 `subject_why`。
  P1  手账页 < 20%：全片没有承载，观众看不到「真的东西」。
  P1  手账页 > 75%：变成图册，概念没有讲清的部分。
  P1  组件 < 25%：概念靠什么讲？手账页只负责「看」，不负责「懂」。
  P1  「简笔线稿当解释图」> 20%（layout=statement/define + sketch、且不是手账页）：
      实测这种镜头比不画更差；要么换成手账页放真素材，要么删掉线稿只留文字。
  P1  锤子帧 > 3。
  P1  see 写成了文字描述（以「出现/显示」开头，或含「字幕/文字」）。

用法：python scripts/validate-fusion.py PROJECT_DIR [--json]
退出码：0 通过 / 1 有 P0 / 2 用法错误。零第三方依赖。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PAGE_LAYOUTS = {"page"}
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

    page_share = share(lambda sid, s: s.get("layout") in PAGE_LAYOUTS)
    sketch_share = share(lambda sid, s: s.get("sketch"))
    annotated_share = share(lambda sid, s: s.get("annotate"))
    component_share = share(lambda sid, s: s.get("layout") in COMPONENT_LAYOUTS)
    text_share = share(lambda sid, s: s.get("layout") in TEXT_LAYOUTS and s.get("recipe") != "hammer")
    # 线稿当解释图：文字版式里塞一张简笔插画。实测比不画更差（P2 样张 / cell 片对比）
    sketch_as_explainer = share(lambda sid, s: s.get("layout") in TEXT_LAYOUTS
                                and s.get("sketch") and s.get("layout") not in PAGE_LAYOUTS
                                and s.get("recipe") != "hammer")
    hammer = [sid for sid, s in shots.items() if s.get("recipe") == "hammer"]

    subject = str(fusion.get("subject_of_film") or "").strip()
    if subject and subject not in EXEMPT:
        # 「出现」的三种证据都算：手账页的真图版说明、标本速写的标签、see 里的画面描述
        hay = " ".join(
            f"{s.get('media_label', '')} {s.get('sketch_label', '')} {s.get('sketch_draw', '')} {s.get('see', '')}"
            for s in shots.values()
        )
        if subject not in hay:
            pages = [sid for sid, s in shots.items() if s.get("layout") in PAGE_LAYOUTS]
            p0.append(
                f"主题物「{subject}」全片没有出现：没有任何一镜拍到它（手账页的真图版说明 / 线稿标签 / see 里都没有）。"
                f"修法：给讲它的那一镜加一页手账——`\"layout\":\"page\"` + "
                f"`\"content\":{{\"page\":\"plate\",\"media\":\"<素材id>\",\"catalogue\":\"…\",\"title\":\"…\","
                f"\"big\":\"{subject}\",\"note\":\"…\"}}`（真图版从 manifests/media.json 里挑；"
                f"没有可用素材就先跑 commons-search.py）。确属纯观念题时写 `\"subject_of_film\":\"abstract\"` 并补 subject_why。"
                + (f" 当前手账页：{', '.join(pages) or '一页都没有'}。" if pages else "")
            )
    elif not subject:
        p1.append("story 没有写 subject_of_film（主题里的那个东西）—— 没有它就无法判断「讲细胞却没有一张细胞图」。"
                  "写一个名词，或写 abstract / software + subject_why。")

    if page_share < 0.20:
        p1.append(f"手账页只占 {page_share:.0%} < 20%：全片没有「承载」——观众看不到真的东西，只看到卡片在讲。"
                  f"挑 1–2 镜写成 `\"layout\":\"page\"`（plate 放真图版 / loupe 用放大镜看细节）。")
    if page_share > 0.75:
        p1.append(f"手账页占 {page_share:.0%} > 75%：变成翻图册了，概念没有讲清的部分。"
                  f"把讲「为什么 / 差多少 / 分几步」的镜头换回 flow / compare / bars / number。")
    if component_share < 0.25:
        p1.append(f"组件只占 {component_share:.0%} < 25%：概念靠什么讲？手账页负责「看」，组件负责「懂」；"
                  f"至少 1/4 片长要是 flow / compare / bars / number 这类推理版面。")
    if sketch_as_explainer > 0.20:
        p1.append(f"「文字 + 简笔线稿」镜头占 {sketch_as_explainer:.0%} > 20%：实测这类画面比不画更差（像剪贴画）。"
                  f"要么改成手账页放真素材，要么删掉 sketch 只留文字。")
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
                    p1.append(f"{sid}: 自拼线稿 {n} 个形 > 12 —— 画得太深了，线稿只做标本速写；删到 ≤10，或换成真图版。")
            except ValueError:
                p1.append(f"{sid}: sketch.draw 的 shapes 不是合法 JSON。")
        label = str(s.get("sketch_label") or "")
        if any(w in label for w in ("剖面", "内部", "拆解", "爆炸图")):
            p1.append(f"{sid}: 线稿标签「{label}」在画内部结构 —— 线稿只画外形与 1–2 个识别特征；内部结构请用真图版。")
        see = str(s.get("see") or "").strip()
        if see and (re.match(r"^(出现|显示|包含|画面出现)", see) or "字幕" in see or "文字" in see):
            p1.append(f"{sid}: see=「{see[:24]}」写成了文字描述；写「关掉声音观众看到什么」，"
                      f"例：『一页手账，右边是 1665 年原版铜版画，放大镜压在上面』。")

    if a.json:
        print(json.dumps({"p0": p0, "p1": p1,
                          "shares": {"page": round(page_share, 3), "sketch": round(sketch_share, 3),
                                     "component": round(component_share, 3), "text": round(text_share, 3),
                                     "annotated": round(annotated_share, 3),
                                     "sketch_as_explainer": round(sketch_as_explainer, 3)}},
                         ensure_ascii=False, indent=2))
    else:
        print(f"validate-fusion · 手账页 {page_share:.0%} · 组件 {component_share:.0%} · 纯文字 {text_share:.0%}"
              f" · 线稿 {sketch_share:.0%}（当解释图 {sketch_as_explainer:.0%}）· 讲解层 {annotated_share:.0%}"
              f" · 锤子帧 {len(hammer)}")
        for x in p0:
            print(f"  P0 {x}")
        for x in p1:
            print(f"  P1 {x}")
        print(f"结论：P0={len(p0)} P1={len(p1)} → {'PASS' if not p0 else 'FAIL'}")
    return 1 if p0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
