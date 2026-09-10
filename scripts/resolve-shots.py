#!/usr/bin/env python3
"""resolve-shots.py · 分镜表解析器（cue 帧号 → 生成 TS 常量）

解决 v2.8 的老问题：帧号是手写魔法数字（`ease(l,95,130)`、`starts=[0,213,416,682]`、
7 组音效绝对帧数组）。改一句台词就要手改几十处，且极易漏改。

本工具的做法（借 anything2explainer 的 token 思路，但拒绝它"把帧号硬编码进源码"的落法）：
    1. 你在 manifests/shots.json 里**只声明这台镜头覆盖哪几句 cue**（`cues: [起, 止]`），
       以及节拍、镜头意图、骨架、介质、活性组件等语义字段；
    2. 本脚本从 caption-cues.json 的 TTS 词级时间戳推出所有绝对帧号；
    3. 生成 src/shots.ts（含已展开的相机关键帧表），场景代码只 import 常量。

于是"改台词 → 重跑解析"即可，不再手改帧号。生成物带 AUTO-GENERATED 头，禁止手改。

用法：
    python scripts/resolve-shots.py PROJECT_DIR [--check]
    --check 只校验不写盘（用于 CI / 门禁）
退出码：0 成功 / 1 校验失败（断档、覆盖不符、cue 越界）/ 2 用法或文件错误
零第三方依赖，Python 3.10+ 标准库。
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

FPS = 30
STAGE_CX, STAGE_CY = 960.0, 540.0


def ms_frame(ms: float) -> int:
    return int(round(ms * FPS / 1000))


def expand_cam(cam: dict, duration: int) -> list[dict]:
    """与 assets/lecture-template/src/shotkit.tsx 的 shotCam() 同形（改一处要同步另一处）。"""
    if cam.get("keys"):
        return cam["keys"]
    intent = cam.get("intent", "still")
    at = int(cam.get("at", 0))
    span = int(cam.get("dur", 38))
    x = float(cam.get("x", STAGE_CX))
    y = float(cam.get("y", STAGE_CY))
    frm = float(cam.get("from", 1.0))
    to = float(cam.get("to", frm))
    fx = float(cam.get("fromX", x))
    fy = float(cam.get("fromY", y))
    rot = float(cam.get("rotY", 0.0))
    hold = max(at + span, duration)
    head = {"f": 0, "x": fx, "y": fy, "s": frm}
    if intent in ("establish", "push-in", "pull-back", "reveal"):
        return [head, {"f": at, "x": x, "y": y, "s": frm}, {"f": at + span, "x": x, "y": y, "s": to}, {"f": hold, "x": x, "y": y, "s": to}]
    if intent == "pan-follow":
        return [head, {"f": at, "x": fx, "y": fy, "s": frm}, {"f": at + span, "x": x, "y": y, "s": to}, {"f": hold, "x": x, "y": y, "s": to}]
    if intent == "micro-orbit":
        return [{**head, "rotY": 0}, {"f": at, "x": x, "y": y, "s": frm, "rotY": 0}, {"f": at + span, "x": x, "y": y, "s": to, "rotY": rot}, {"f": hold, "x": x, "y": y, "s": to, "rotY": rot}]
    return [head, {"f": duration, "x": x, "y": y, "s": frm}]


def js(v) -> str:
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return "'" + v.replace("\\", "\\\\").replace("'", "\\'") + "'"
    if isinstance(v, list):
        return "[" + ",".join(js(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ",".join(f"{k}:{js(x)}" for k, x in v.items()) + "}"
    raise TypeError(type(v))


def ts_key(ident: str) -> str:
    return ident if ident.replace("_", "").isalnum() and not ident[0].isdigit() else "'" + ident + "'"


def resolve(project: Path) -> tuple[str, list[dict], list[str]]:
    shots_doc = json.loads((project / "manifests" / "shots.json").read_text(encoding="utf-8"))
    cues_doc = json.loads((project / "manifests" / "caption-cues.json").read_text(encoding="utf-8"))
    cues = cues_doc["cues"]
    shots = shots_doc.get("shots", [])
    problems: list[str] = []
    out: list[dict] = []
    cursor = 0
    # 第一遍：求每镜的 from（= 其首句 cue 的起始帧；首镜固定 0）
    starts: list[int] = []
    for i, s in enumerate(shots):
        idx = s.get("cues")
        if not idx or len(idx) != 2:
            problems.append(f"{s.get('id', '?')}: 缺少 cues:[起,止]")
            starts.append(-1)
            continue
        a = int(idx[0])
        if a < 0 or a >= len(cues):
            problems.append(f"{s.get('id', '?')}: cues 起点 {a} 越界")
            starts.append(-1)
            continue
        starts.append(int(s["from"]) if s.get("from") is not None else (0 if i == 0 else ms_frame(cues[a]["start_ms"])))
    for s in shots:
        sid = s["id"]
        idx = s.get("cues")
        if not idx or len(idx) != 2:
            problems.append(f"{sid}: 缺少 cues:[起,止]")
            continue
        a, b = int(idx[0]), int(idx[1])
        if a < 0 or b >= len(cues) or a > b:
            problems.append(f"{sid}: cues [{a},{b}] 越界（共 {len(cues)} 条）")
            continue
        tail = int(s.get("tail", 24))
        i = len(out)
        frm = starts[i] if i < len(starts) else cursor
        if frm < 0:
            continue
        if s.get("to") is not None:
            to = int(s["to"])
        elif i + 1 < len(starts) and starts[i + 1] >= 0:
            to = starts[i + 1]
        else:
            to = ms_frame(cues[b]["speech_end_ms"]) + tail
        if frm != cursor:
            problems.append(f"{sid}: from={frm} 与上一镜止帧 {cursor} 不连续（断档或重叠）")
        duration = to - frm
        if duration <= 0:
            problems.append(f"{sid}: duration={duration} 非正")
            continue
        cam = dict(s.get("camera") or {"intent": "still"})
        keys = expand_cam(cam, duration)
        rec = {
            "id": sid,
            "chapter": s.get("chapter", ""),
            "skeleton": s.get("skeleton", "Stage"),
            "media": list(s.get("media") or []),
            "live": list(s.get("live") or []),
            "from": frm,
            "to": to,
            "duration": duration,
            "cueFirst": a,
            "cueLast": b,
            "keys": keys,
            "anchor": s.get("anchor"),
            "hero": s.get("hero"),
            "cover": s.get("cover"),
            "transition": s.get("transition", "cut"),
            "entry": s.get("entry", "rise"),
            "explanation": bool(s.get("explanation", True)),
            "zones": s.get("zones"),
            "bottomFill": s.get("bottomFill"),
            "contentBand": s.get("contentBand"),
            "cameraIntent": cam.get("intent", "still"),
            # beats：以本镜本地帧表示（场景组件直接消费）
            "beats": [(ms_frame(cues[int(bt["cue"])]["start_ms"]) + int(bt.get("offset", 0)) - frm) for bt in (s.get("beats") or [])],
            # beatsAbs：绝对帧（门禁消费）
            "beatsAbs": [(ms_frame(cues[int(bt["cue"])]["start_ms"]) + int(bt.get("offset", 0))) for bt in (s.get("beats") or [])],
        }
        out.append(rec)
        cursor = to
    total = cursor
    declared = shots_doc.get("duration")
    if declared and int(declared) != total:
        problems.append(f"shots.json duration={declared} 与实际覆盖 {total} 不符")
    head = [
        "// AUTO-GENERATED by scripts/resolve-shots.py — 禁止手改。",
        "// 改台词/节奏 → 改 manifests/shots.json 与 caption-cues.json → 重跑解析。",
        "// 相机关键帧已展开，场景里直接 <ShotCamera keys={SHOTS.S1.keys} ... />。",
        "",
        f"export const SHOT_TOTAL = {total};",
        "",
        "export const SHOTS = {",
    ]
    body = []
    for r in out:
        body.append(f"  {ts_key(r['id'])}: {js(r)},")
    tail_lines = ["} as const;", "", "export type ShotId = keyof typeof SHOTS;", "", f"export const SHOT_IDS = {js([r['id'] for r in out])} as const;", ""]
    return "\n".join(head + body + tail_lines), out, problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"项目目录不存在：{project}", file=sys.stderr)
        return 2
    text, out, problems = resolve(project)
    for r in out:
        print(f"  {r['id']:>6} {r['from']:>5}–{r['to']:<5} {r['duration']:>5}f  {r['skeleton']:<8} {r['chapter']}")
    if problems:
        for p in problems:
            print(f"  ! {p}", file=sys.stderr)
        return 1
    if args.check:
        print("resolve-shots --check：通过（未写盘）")
        return 0
    target = project / "src" / "shots.ts"
    with io.open(target, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    theme_id = json.loads((project / "manifests" / "shots.json").read_text(encoding="utf-8")).get("theme", "cel")
    resolved = {"duration": out[-1]["to"] if out else 0, "theme": theme_id, "shots": out}
    with io.open(project / "manifests" / "shots.resolved.json", "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(resolved, ensure_ascii=False, indent=2))
    print(f"已写出 {target} 与 manifests/shots.resolved.json（{len(out)} 镜，共 {out[-1]['to'] if out else 0} 帧）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
