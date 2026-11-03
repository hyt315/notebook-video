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
# 直书页（type）：没有卡片，但它是**讲解**（把关系排成字），不是「字卡说不出东西」。
# 归到讲解层参与 20/75 的配比，同时单独设上限——全片都是直书，就退化成一本排版册。
TYPEFACE_LAYOUTS = {"type"}
TEXT_LAYOUTS = {"statement", "define"}
EXEMPT = {"abstract", "software"}

# 呈现模式（story.json 顶层 "mode"）。三套配额，不是三档风格。
#   page   手账页占比区间（承载：给你看那个真东西）
#   comp   组件（含直书）下限（讲解：把概念拆开、对比、算清）
#   comp_ceiling  多框组件的上限（只有 freeform 用：声明了不用组件，就别偷偷用）
#   subject  "run"   = 主题物必须至少出现一次（有手账页可承载）
#            "named" = 全组件片没有纸可贴，主题物只能靠 see / title 点名
MODES = {
    "hybrid":    {"page": (0.20, 0.75), "comp": 0.25, "comp_ceiling": None, "typeface": 0.40, "subject": "run",
                  "why": "混合：手账页负责「看」，组件负责「懂」"},
    "component": {"page": (0.00, 0.12), "comp": 0.60, "comp_ceiling": None, "typeface": 0.40, "subject": "named",
                  "why": "全组件：内容本身就是结构（流程 / 对比 / 清单 / 数据），没有实物可拍"},
    "freeform":  {"page": (0.40, 1.00), "comp": 0.00, "comp_ceiling": 0.10, "typeface": 0.55, "subject": "run",
                  "why": "全非组件：只有手账页与直书，零纸条卡"},
}


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
    mode = str(fusion.get("mode") or "hybrid").lower()
    if mode not in MODES:
        p0.append(f"mode={mode!r} 不认识：只支持 {' / '.join(MODES)}。"
                  f"它可以出现在 story.json 顶层，compose 会写进 fusion.json。")
        mode = "hybrid"
    rule = MODES[mode]
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
    typeface_share = share(lambda sid, s: s.get("layout") in TYPEFACE_LAYOUTS and s.get("recipe") != "hammer")
    component_share += typeface_share
    # 线稿当解释图：文字版式里塞一张简笔插画。实测比不画更差（P2 样张 / cell 片对比）
    sketch_as_explainer = share(lambda sid, s: s.get("layout") in TEXT_LAYOUTS
                                and s.get("sketch") and s.get("layout") not in PAGE_LAYOUTS
                                and s.get("recipe") != "hammer")
    hammer = [sid for sid, s in shots.items() if s.get("recipe") == "hammer"]

    subject = str(fusion.get("subject_of_film") or "").strip()
    if subject and subject not in EXEMPT:
        # 「出现」的证据：手账页的真图版说明、墨图标签、速写标签、see 的画面描述。
        # 全组件片没有纸，主题物只能靠这一镜**讲的是什么**（see / title）点名——
        # 否则「讲细胞却没有一处提到细胞」这种片子会被判通过，正是门禁该拦的。
        hay = " ".join(
            f"{s.get('media_label', '')} {s.get('ink_label', '')} {s.get('sketch_label', '')} "
            f"{s.get('sketch_draw', '')} {s.get('see', '')} {s.get('title', '')}"
            for s in shots.values()
        )
        if subject not in hay:
            pages = [sid for sid, s in shots.items() if s.get("layout") in PAGE_LAYOUTS]
            if rule["subject"] == "named":
                p0.append(
                    f"[全组件] 主题物「{subject}」全片没被点名：所有镜头的 see / title 里都没有它。"
                    f"全组件片没有手账页可贴，主题物只能靠语言指称——至少让一镜的 `see` 写出它"
                    f"（例：『三张卡片并列，标题分别写着 {subject} 的三个规格』），或者直接把 mode 改成 hybrid 并加一页手账。"
                )
            else:
                p0.append(
                    f"主题物「{subject}」全片没有出现：没有任何一镜拍到它（手账页的真图版说明 / 墨图标签 / 线稿标签 / see 里都没有）。"
                    f"修法：给讲它的那一镜加一页手账——`\"layout\":\"page\"` + "
                    f"`\"content\":{{\"page\":\"plate\",\"media\":\"<素材id>\",\"catalogue\":\"…\",\"title\":\"…\","
                    f"\"big\":\"{subject}\",\"note\":\"…\"}}`（真图版从 manifests/media.json 里挑；"
                    f"没有可用素材就先跑 commons-search.py）。确属纯观念题时写 `\"subject_of_film\":\"abstract\"` 并补 subject_why。"
                    + (f" 当前手账页：{', '.join(pages) or '一页都没有'}。" if pages else "")
                )
    elif not subject:
        p1.append("story 没有写 subject_of_film（主题里的那个东西）—— 没有它就无法判断「讲细胞却没有一张细胞图」。"
                  "写一个名词，或写 abstract / software + subject_why。")

    lo, hi = rule["page"]
    if page_share < lo:
        p1.append(f"[{mode}] 手账页只占 {page_share:.0%} < {lo:.0%}：全片没有「承载」——观众看不到真的东西，只看到卡片在讲。"
                  f"挑 1–2 镜写成 `\"layout\":\"page\"`（plate 放真图版 / ink 画墨图）。"
                  + ("" if mode != "component" else
                     f" 全组件模式本来就不该有手账页，所以这条只在**你想留一页当锚点**时才需要处理；"
                     f"确实一页都不要，把 page 压到 0 即可（上限 {hi:.0%} 仍生效）。"))
    if page_share > hi:
        if mode == "component":
            p1.append(f"[全组件] 手账页占 {page_share:.0%} > {hi:.0%}：mode 写的是 component，却塞了手账页。"
                      f"要么把这几镜改回 flow / compare / list（组件片不该靠纸承载），"
                      f"要么把 mode 改成 hybrid——两种都可以，但别声明一套做另一套。")
        else:
            p1.append(f"[{mode}] 手账页占 {page_share:.0%} > {hi:.0%}：变成翻图册了，概念没有讲清的部分。"
                      f"把讲「为什么 / 差多少 / 分几步」的镜头换回 flow / compare / bars / number。")
    if component_share < rule["comp"]:
        p1.append(f"[{mode}] 组件（含直书）只占 {component_share:.0%} < {rule['comp']:.0%}：概念靠什么讲？"
                  f"手账页负责「看」，组件负责「懂」；至少 {rule['comp']:.0%} 片长要是推理或直书版面。")
    if sketch_as_explainer > 0.20:
        p1.append(f"「文字 + 简笔线稿」镜头占 {sketch_as_explainer:.0%} > 20%：实测这类画面比不画更差（像剪贴画）。"
                  f"要么改成手账页放真素材，要么删掉 sketch 只留文字。")
    if rule["comp_ceiling"] is not None:
        multi = max(0.0, component_share - typeface_share)
        if multi > rule["comp_ceiling"]:
            p1.append(f"[全非组件] 多框组件占 {multi:.0%} > {rule['comp_ceiling']:.0%}：mode 声明的是 freeform，"
                      f"意思是「不用卡片讲」。真要留一处对比可以，但超过 {rule['comp_ceiling']:.0%} 就名不副实——"
                      f"要么删掉换成直书并列，要么把 mode 改成 hybrid。")
    if typeface_share > rule["typeface"]:
        p1.append(f"[{mode}] 直书页占 {typeface_share:.0%} > {rule['typeface']:.0%}：直书省掉了框，但没有东西可看——"
                  f"全片都这样会变成一本排版册。给一半镜头放回图（手账页）或纸条卡。")
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
        print(json.dumps({"mode": mode, "p0": p0, "p1": p1,
                          "shares": {"page": round(page_share, 3), "sketch": round(sketch_share, 3),
                                     "component": round(component_share, 3), "typeface": round(typeface_share, 3), "text": round(text_share, 3),
                                     "annotated": round(annotated_share, 3),
                                     "sketch_as_explainer": round(sketch_as_explainer, 3)}},
                         ensure_ascii=False, indent=2))
    else:
        print(f"validate-fusion · 模式 {mode}（{rule['why']}）· 手账页 {page_share:.0%} · 组件 {component_share:.0%}（含直书 {typeface_share:.0%}）· 纯文字 {text_share:.0%}"
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
