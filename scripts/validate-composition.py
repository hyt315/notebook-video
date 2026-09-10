#!/usr/bin/env python3
"""validate-composition.py · 构图与活性门禁（P0 阻断渲染 / P1 仅警告）

这是整套体系里**唯一能把"审美"变成门禁**的部分，也是让改进不随时间退化的保障。
没有它，v2.8 的强制条款再多也会像今天一样全部空转——规范强制使用活性组件、
实现引用数为 0，9 个校验脚本没有一条能发现。

八项检查（判据与档位见 references/composition-gate.md）：
  P0-1 骨架重复度        相邻场景不得同骨架；全片 ≥3 种
  P0-2 活性组件覆盖率     每个讲解场景 ≥1 个机制演示组件；纯卡片堆 → fail
  P0-3 镜头意图多样性     全片 ≥3 种 intent（不含 still）
  P0-4 密度硬条款         3–5 个功能分区；下 1/4 填满
  P0-5 介质多样性         全片 ≥3 种不同视觉介质
  P1-6 转场多样性         ≥2 种，不得全 cut
  P1-7 入场方式多样性     ≥3 种
  P1-8 状态变化间隔       ≥每 120 帧（4s）一次画面变化；静止 >45 帧告警

用法：
    python scripts/validate-composition.py PROJECT_DIR [--strict] [--json]
退出码：0 通过（可含 P1）/ 1 存在 P0（或 --strict 下存在 P1）/ 2 用法或文件错误
零第三方依赖，Python 3.10+ 标准库。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKELETONS = {"Stage", "Corridor", "Split", "Zoom"}
MIN_SKELETONS = 3
MIN_MEDIA = 3
MIN_INTENTS = 3
MIN_TRANSITIONS = 2
MIN_ENTRIES = 3
MAX_BEAT_GAP = 120
STATIC_RUN_WARN = 45
ZONE_RANGE = (3, 5)


def load(project: Path) -> dict:
    shots_path = project / "manifests" / "shots.resolved.json"
    if not shots_path.exists():
        raise SystemExit(f"缺少 {shots_path}；先运行 python scripts/resolve-shots.py PROJECT_DIR")
    return json.loads(shots_path.read_text(encoding="utf-8"))


def check(data: dict) -> tuple[list[dict], list[dict]]:
    p0: list[dict] = []
    p1: list[dict] = []
    shots = data.get("shots", [])
    if not shots:
        p0.append({"id": "-", "issue": "shots.json 没有 shots"})
        return p0, p1

    # P0-1 骨架重复度
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

    # P0-2 活性组件覆盖率 + P0-4 密度
    for s in shots:
        sid = s["id"]
        if not s.get("explanation", True):
            continue
        live = [x for x in (s.get("live") or []) if x]
        if not live:
            p0.append({"id": sid, "issue": "讲解场景没有任何活性组件（纯卡片堆）；禁止"})
        zones = s.get("zones")
        if zones is None:
            p0.append({"id": sid, "issue": "缺少 zones（本镜功能分区数）"})
        elif not (ZONE_RANGE[0] <= int(zones) <= ZONE_RANGE[1]):
            p0.append({"id": sid, "issue": f"功能分区 {zones} 个，契约要求 {ZONE_RANGE[0]}–{ZONE_RANGE[1]} 个"})
        if s.get("bottomFill") is not True:
            p0.append({"id": sid, "issue": "下 1/4 未填满（底边须接近 y=876）；画面下半空洞是 PPT 感的主要来源"})

    # P0-3 镜头意图多样性
    intents = {s.get("cameraIntent", "still") for s in shots}
    if len(intents - {"still"}) < MIN_INTENTS:
        p0.append({"id": "-", "issue": f"全片仅 {len(intents - {'still'})} 种镜头意图，要求 ≥{MIN_INTENTS} 种"})

    # P0-5 介质多样性
    media: set[str] = set()
    for s in shots:
        for m in s.get("media") or []:
            media.add(m)
    if len(media) < MIN_MEDIA:
        p0.append({"id": "-", "issue": f"全片仅 {len(media)} 种视觉介质 {sorted(media)}，要求 ≥{MIN_MEDIA} 种"})

    # P1-6 转场多样性
    transitions = [s.get("transition", "cut") for s in shots]
    if len(set(transitions)) < MIN_TRANSITIONS:
        p1.append({"id": "-", "issue": f"全片仅 {len(set(transitions))} 种转场，建议 ≥{MIN_TRANSITIONS} 种"})

    # P1-7 入场多样性
    entries = [s.get("entry", "rise") for s in shots]
    if len(set(entries)) < MIN_ENTRIES:
        p1.append({"id": "-", "issue": f"全片仅 {len(set(entries))} 种入场方式，建议 ≥{MIN_ENTRIES} 种"})

    # P1-8 状态变化间隔
    for s in shots:
        frames = sorted(int(b) for b in (s.get("beatsAbs") or []))
        if not frames:
            p1.append({"id": s["id"], "issue": "未声明 beats（状态变化帧），无法判断节奏"})
            continue
        marks = [s["from"]] + frames + [s["to"]]
        gaps = [b - a for a, b in zip(marks, marks[1:])]
        worst = max(gaps) if gaps else 0
        if worst > MAX_BEAT_GAP:
            p1.append({"id": s["id"], "issue": f"最长 {worst} 帧（{worst / 30:.1f}s）无画面变化，超过 {MAX_BEAT_GAP} 帧（4s）"})
        if worst > STATIC_RUN_WARN and worst <= MAX_BEAT_GAP:
            p1.append({"id": s["id"], "issue": f"最长静止 {worst} 帧，建议补一次呼吸/位移"})
    return p0, p1


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
    p0, p1 = check(data)
    if args.json:
        print(json.dumps({"p0": p0, "p1": p1, "shots": len(data.get("shots", []))}, ensure_ascii=False, indent=2))
    else:
        shots = data.get("shots", [])
        print(f"validate-composition · {len(shots)} 镜")
        for item in p0:
            print(f"  P0 {item['id']}: {item['issue']}")
        for item in p1:
            print(f"  P1 {item['id']}: {item['issue']}")
        verdict = "PASS" if not p0 and not (args.strict and p1) else "FAIL"
        print(f"结论：P0={len(p0)} P1={len(p1)} → {verdict}")
    if p0:
        return 1
    if args.strict and p1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
