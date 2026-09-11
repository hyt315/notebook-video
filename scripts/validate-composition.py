#!/usr/bin/env python3
"""validate-composition.py · 构图与活性门禁（P0 阻断渲染 / P1 仅警告）

这是整套体系里**唯一能把"审美"变成门禁**的部分，也是让改进不随时间退化的保障。
没有它，v2.8 的强制条款再多也会像今天一样全部空转——规范强制使用活性组件、
实现引用数为 0，9 个校验脚本没有一条能发现。

检查项（判据与档位见 references/composition-gate.md）：

  P0-1  骨架重复度        相邻场景不得同骨架；全片 ≥3 种；未知骨架名 → fail
  P0-2  活性组件覆盖率     每个讲解场景 ≥1 个活性组件；**且每个名字必须能在场景文件里找到**
  P0-3  镜头意图多样性     全片 ≥3 种 intent（不含 still）
  P0-4  密度硬条款         3–5 个功能分区；下 1/4 填满（**不再被 explanation:false 绕过**）
  P0-5  介质多样性         全片 ≥3 种不同视觉介质，且取值必须在闭合集合内
  P0-6  枚举闭合           转场 / 入场 / 介质 / 骨架 / 意图 全是闭合集合，写错名字即 fail
  P1-7  单镜过长           单镜 > 300 帧（10s）提示锯开（基准 4–6s、最长 ≤9s）
  P1-8  骨架指纹重复       同一 (骨架,意图,转场,入场) 组合每出现一次就提示
  P1-9  镜长分布           最长/最短 < 2 倍、或 >80% 镜头集中在同一档 → 读起来是节拍器
  P1-10 主角尺寸           hero 必须声明，且 size 是"主体短边设计像素"（图形 ≥255 / 大字 ≥144）
  P1-11 转场 / 入场多样性  ≥2 种 / ≥3 种
  P1-12 状态变化间隔       汇总报告（带帧区间与所涉台词），不再每镜刷 1 条

用法：
    python scripts/validate-composition.py PROJECT_DIR [--strict] [--json]
退出码：0 通过（可含 P1）/ 1 存在 P0（或 --strict 下存在 P1）/ 2 用法或文件错误
零第三方依赖，Python 3.10+ 标准库。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# 闭合集合：写错名字必须被拦下（v2.11 前这些字段是自由字符串，
# 实测把 media 写成 ["FAKE_MEDIUM_A",...]、live 写成 ["NO_SUCH_COMPONENT"] 也能 P0=0 通过）
SKELETONS = {"Stage", "Corridor", "Split", "Zoom"}
INTENTS = {"establish", "push-in", "pull-back", "pan-follow", "reveal", "micro-orbit", "still"}
TRANSITIONS = {"cut", "handoff", "whip", "reveal", "paper-turn"}
ENTRIES = {"rise", "slide", "fade", "zoom"}
MEDIA_KINDS = {"chart", "console", "code", "graphic", "text", "metric"}

MIN_SKELETONS = 3
MIN_MEDIA = 3
MIN_INTENTS = 3
MIN_TRANSITIONS = 2
MIN_ENTRIES = 3
ZONE_RANGE = (3, 5)
MAX_EXPLANATION_FALSE = 1     # 一部片最多 1 镜可以不走"讲解场景"的活性要求（章节卡）
MAX_SHOT_FRAMES = 300         # 单镜上限 10s
MIN_LENGTH_RATIO = 2.0        # 最长/最短 倍数下限（测出来是节拍器）
MAX_BAND_SHARE = 0.8          # 同一时长档最多占 80%
MAX_BEAT_GAP = 120            # 文档的慢章节上限（3–4s）；超过它才算越界
SLOW_GAP = 90                 # 汇总时把 >3s 的间隔也列出来（供评审，不判缺陷）
HERO_MIN_GRAPHIC = 255        # a2e 720p 的 170px × 1.5（设计空间 1920×1080）
HERO_MIN_TEXT = 144           # a2e 720p 的 96px × 1.5

BANDS = ((0, 60, "≤2s"), (61, 120, "2–4s"), (121, 240, "4–8s"), (241, 10 ** 9, ">8s"))


def load(project: Path) -> dict:
    shots_path = project / "manifests" / "shots.resolved.json"
    if not shots_path.exists():
        raise SystemExit(f"缺少 {shots_path}；先运行 python scripts/resolve-shots.py PROJECT_DIR")
    return json.loads(shots_path.read_text(encoding="utf-8"))


def scene_source(project: Path) -> str:
    """场景文件全文：用来确认 live 里的名字真的被引用过（而不是编出来的）。"""
    src = project / "src"
    text = ""
    if src.is_dir():
        for p in sorted(src.glob("*.tsx")):
            text += p.read_text(encoding="utf-8", errors="replace")
    return text


def check(data: dict, scene_text: str = "") -> tuple[list[dict], list[dict], list[str]]:
    p0: list[dict] = []
    p1: list[dict] = []
    notes: list[str] = []
    shots = data.get("shots", [])
    if not shots:
        p0.append({"id": "-", "issue": "shots.json 没有 shots"})
        return p0, p1, notes

    # ---- P0-6 枚举闭合（先做，后面的多样性统计才有意义）----
    unknown_intents = {s.get("cameraIntent", "still") for s in shots} - INTENTS
    if unknown_intents:
        p0.append({"id": "-", "issue": f"未知镜头意图 {sorted(unknown_intents)}；只能是 {sorted(INTENTS)}"})
    bad_tr = {s.get("transition", "cut") for s in shots} - TRANSITIONS
    if bad_tr:
        p0.append({"id": "-", "issue": f"未知转场 {sorted(bad_tr)}；只能是 {sorted(TRANSITIONS)}"})
    bad_en = {s.get("entry", "rise") for s in shots} - ENTRIES
    if bad_en:
        p0.append({"id": "-", "issue": f"未知入场方式 {sorted(bad_en)}；只能是 {sorted(ENTRIES)}"})
    bad_media = {m for s in shots for m in (s.get("media") or [])} - MEDIA_KINDS
    if bad_media:
        p0.append({"id": "-", "issue": f"未知介质 {sorted(bad_media)}；只能是 {sorted(MEDIA_KINDS)}"})

    # ---- P0-1 骨架重复度 ----
    seq = [(s["id"], s.get("skeleton", "?")) for s in shots]
    for (a_id, a), (b_id, b) in zip(seq, seq[1:]):
        if a == b:
            p0.append({"id": b_id, "issue": f"与上一镜同骨架（{a}）；相邻场景必须不同骨架"})
    kinds = {k for _, k in seq}
    unknown = kinds - SKELETONS
    if unknown:
        p0.append({"id": "-", "issue": f"未知骨架 {sorted(unknown)}；只能是 {sorted(SKELETONS)}"})
    if len(kinds & SKELETONS) < MIN_SKELETONS:
        p0.append({"id": "-", "issue": f"全片仅 {len(kinds & SKELETONS)} 种骨架，要求 ≥{MIN_SKELETONS} 种"})

    # ---- P0-2 活性组件覆盖率（含"名字可解析"）+ P0-4 密度 ----
    # explanation:false 只能豁免"活性组件"这一条，且全片最多 1 镜；
    # zones / bottomFill 与 explanation 无关，永远校验（旧版一个 false 就能把整块跳过）。
    non_expl = [s["id"] for s in shots if s.get("explanation", True) is False]
    if len(non_expl) > MAX_EXPLANATION_FALSE:
        p0.append({"id": "-", "issue": f"{len(non_expl)} 镜标了 explanation:false（{non_expl}），最多允许 {MAX_EXPLANATION_FALSE} 镜"})
    live_names: set[str] = set()
    for s in shots:
        sid = s["id"]
        if s.get("explanation", True) is not False:
            live = [x for x in (s.get("live") or []) if x]
            if not live:
                p0.append({"id": sid, "issue": "讲解场景没有任何活性组件（纯卡片堆）；禁止"})
            for name in live:
                live_names.add(str(name))
                if scene_text and not re.search(r"\b" + re.escape(str(name)) + r"\b", scene_text):
                    p0.append({"id": sid, "issue": f"活性组件 “{name}” 在场景文件里找不到（没 import 也没渲染）；写名字前先在接触表里看见它"})
        zones = s.get("zones")
        if zones is None:
            p0.append({"id": sid, "issue": "缺少 zones（本镜功能分区数）"})
        elif not isinstance(zones, int) or not (ZONE_RANGE[0] <= zones <= ZONE_RANGE[1]):
            p0.append({"id": sid, "issue": f"功能分区 {zones!r}，契约要求 {ZONE_RANGE[0]}–{ZONE_RANGE[1]} 个整数"})
        if s.get("bottomFill") is not True:
            p0.append({"id": sid, "issue": "下 1/4 未填满（底边须接近 y=876）；画面下半空洞是 PPT 感的主要来源"})

    # ---- P0-3 镜头意图多样性 ----
    intents = {s.get("cameraIntent", "still") for s in shots}
    if len(intents - {"still"}) < MIN_INTENTS:
        p0.append({"id": "-", "issue": f"全片仅 {len(intents - {'still'})} 种镜头意图，要求 ≥{MIN_INTENTS} 种"})

    # ---- P0-5 介质多样性 ----
    media: set[str] = set()
    for s in shots:
        for m in s.get("media") or []:
            media.add(m)
    if len(media) < MIN_MEDIA:
        p0.append({"id": "-", "issue": f"全片仅 {len(media)} 种视觉介质 {sorted(media)}，要求 ≥{MIN_MEDIA} 种"})

    # ---- P1 单镜过长（工艺项，不阻断；结构由作者决定）----
    for s in shots:
        if int(s.get("duration", 0)) > MAX_SHOT_FRAMES:
            p1.append({"id": s["id"], "issue": f"单镜 {s['duration']} 帧（{s['duration'] / 30:.1f}s）超过 {MAX_SHOT_FRAMES} 帧参考上限；基准是单镜 4–6s、最长 ≤9s"})

    # ---- P1-8 骨架指纹重复 ----
    fp: dict[tuple, list[str]] = {}
    for s in shots:
        key = (s.get("skeleton"), s.get("cameraIntent"), s.get("transition"), s.get("entry"))
        fp.setdefault(key, []).append(s["id"])
    for key, ids in fp.items():
        if len(ids) > 1:
            p1.append({"id": "-", "issue": f"骨架指纹 {key} 出现 {len(ids)} 次（{ids}）；隔镜重复会让观众觉得“这段我看过”"})

    # ---- P1-9 镜长分布 ----
    durs = [int(s.get("duration", 0)) for s in shots]
    if len(durs) >= 3:
        lo, hi = min(durs), max(durs)
        ratio = hi / max(1, lo)
        if ratio < MIN_LENGTH_RATIO:
            p1.append({"id": "-", "issue": f"最长/最短镜头仅 {ratio:.2f} 倍（{hi}/{lo}），全片一个速度=节拍器；建议 2.5–3 倍以上"})
        share = {}
        for d in durs:
            for a, b, name in BANDS:
                if a <= d <= b:
                    share[name] = share.get(name, 0) + 1
                    break
        worst = max(share.items(), key=lambda kv: kv[1])
        if worst[1] / len(durs) > MAX_BAND_SHARE:
            p1.append({"id": "-", "issue": f"{worst[1]}/{len(durs)} 镜落在同一时长档（{worst[0]}）；长短要错开"})
        if not any(d <= 120 for d in durs):
            p1.append({"id": "-", "issue": "全片没有 ≤4s 的短镜；插入镜/重音镜头都该在这一档"})

    # ---- P1-10 主角尺寸 ----
    for s in shots:
        hero = s.get("hero") or {}
        size = hero.get("size")
        kind = hero.get("kind", "text")
        if size is None:
            p1.append({"id": s["id"], "issue": "未声明 hero（主角）"})
            continue
        floor = HERO_MIN_GRAPHIC if kind == "graphic" else HERO_MIN_TEXT
        if int(size) < floor:
            p1.append({"id": s["id"], "issue": f"hero.size={size}（{kind}）低于 {floor}；这个字段必须是**主体短边设计像素**，不是随便填的数"})

    # ---- P1-11 转场 / 入场多样性 ----
    transitions = [s.get("transition", "cut") for s in shots]
    if len(set(transitions)) < MIN_TRANSITIONS:
        p1.append({"id": "-", "issue": f"全片仅 {len(set(transitions))} 种转场，建议 ≥{MIN_TRANSITIONS} 种"})
    entries = [s.get("entry", "rise") for s in shots]
    if len(set(entries)) < MIN_ENTRIES:
        p1.append({"id": "-", "issue": f"全片仅 {len(set(entries))} 种入场方式，建议 ≥{MIN_ENTRIES} 种"})

    # ---- P1-12 状态变化间隔（汇总，带帧区间归因）----
    runs = []
    for s in shots:
        frames = sorted(int(b) for b in (s.get("beatsAbs") or []))
        if not frames:
            p1.append({"id": s["id"], "issue": "未声明 beats（状态变化帧），无法判断节奏"})
            continue
        marks = [int(s["from"])] + frames + [int(s["to"])]
        gaps = [(b - a, a, b) for a, b in zip(marks, marks[1:])]
        if not gaps:
            continue
        worst, a, b = max(gaps)
        if worst > SLOW_GAP:
            runs.append((worst, s["id"], a, b))
    over = [r for r in runs if r[0] > MAX_BEAT_GAP]
    near = [r for r in runs if SLOW_GAP < r[0] <= MAX_BEAT_GAP]
    if over:
        detail = "；".join(f"{i}({w}帧 f={a}-{b})" for w, i, a, b in sorted(over, reverse=True)[:4])
        p1.append({"id": "-", "issue": f"{len(over)} 处变化间隔 >{MAX_BEAT_GAP} 帧（4s），已超出文档的慢章节上限（3–4s）：{detail}"})
    if near:
        detail = "；".join(f"{i}({w}帧 f={a}-{b})" for w, i, a, b in sorted(near, reverse=True)[:4])
        p1.append({"id": "-", "issue": f"{len(near)} 处变化间隔在 3–4s（慢章节正常范围，但连成片会让节奏偏平）；若这些区段画面完全静止，按 motion-design 补一次呼吸：{detail}"})

    # 覆盖率自述：让"没报"和"没跑"可区分
    notes.append(f"已校验：枚举 5 类 / live {len(live_names)} 个名字 / hero {len(shots)} 镜 / 时长 {len(durs)} 镜")
    return p0, p1, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--strict", action="store_true", help="把 P1 也当作失败")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"项目目录不存在：{project}", file=sys.stderr)
        return 2
    data = load(project)
    p0, p1, notes = check(data, scene_source(project))
    if args.json:
        print(json.dumps({"p0": p0, "p1": p1, "notes": notes, "shots": len(data.get("shots", []))}, ensure_ascii=False, indent=2))
    else:
        shots = data.get("shots", [])
        print(f"validate-composition · {len(shots)} 镜")
        for item in p0:
            print(f"  P0 {item['id']}: {item['issue']}")
        for item in p1:
            print(f"  P1 {item['id']}: {item['issue']}")
        for n in notes:
            print(f"  ·· {n}")
        verdict = "PASS" if not p0 and not (args.strict and p1) else "FAIL"
        print(f"结论：P0={len(p0)} P1={len(p1)} → {verdict}")
    if p0:
        return 1
    if args.strict and p1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
