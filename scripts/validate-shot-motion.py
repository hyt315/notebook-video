#!/usr/bin/env python3
"""validate-shot-motion.py · 镜头出界证明门禁（P0，可阻断渲染）

把"相机契约"从"靠自觉"变成"可执行证明"。v2.8 的 Camera Micro-Framing Invariant
把相机锁在 x∈[945,975] / s∈[1.00,1.018]（景别变化 1.8%，等同定焦），代价是全片
没有镜头在动；而 3:4 的 CAM_KEYS_P 反而越界 10 处、无人发现——两个极端都是
"没有校验"造成的。本脚本用纯算术证明"镜头运动后，本镜声明必须可见的 anchor
仍然完整落在可见窗内"，因此可以把"不出界"从"靠不动"换成"靠证明"。

数学（与 assets/lecture-template/src/shotkit.tsx 完全一致）：
    可见窗 left = x - 960/s, right = x + 960/s, top = y - 540/s, bottom = y + 540/s
    (x, y, s) 在相邻关键帧之间单调变化，而 left/right/top/bottom 对 x 与 s 都单调，
    因此一个区间的极值必在端点取得 → **只需逐关键帧校验即可得到精确结论**（非近似）。

用法：
    python scripts/validate-shot-motion.py PROJECT_DIR
    python scripts/validate-shot-motion.py PROJECT_DIR --json
退出码：0 通过（可含 P1 警告）/ 1 存在 P0 违规 / 2 用法或文件错误
零第三方依赖，Python 3.10+ 标准库。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

STAGE_CX, STAGE_CY = 960.0, 540.0

# 每个镜头意图的缩放预算（设计空间）。含文字的镜头上限更严，见 TEXT_ZOOM_MAX。
INTENT_MAX_ZOOM = {
    "establish": 1.05,
    "push-in": 1.35,
    "pull-back": 1.60,
    "pan-follow": 1.20,
    "reveal": 1.12,
    "micro-orbit": 1.10,
    "still": 1.00,
}
TEXT_ZOOM_MAX = 1.35
GRAPHIC_ZOOM_MAX = 1.60
ROT_MAX = 6.0  # micro-orbit 的 rotY 上限（度）
CAM_DUR = (30, 45)  # 单次运镜时长（帧），references/shot-language.md
# 每章运镜配额要有时长比例感：短视频章节只有 7 秒时强求 3 次是无意义的。
# 规则：章节 ≥20 秒 → ≥3 次；否则 ≥1 次。另有全片配额 ceil(秒/12)，下限 4。
CHAPTER_MIN_MOVES_LONG = 3
CHAPTER_LONG_SECONDS = 20
CHAPTER_MIN_MOVES_SHORT = 1
FILM_MOVES_MIN_PER_12S = 12  # 每 12 秒至少 1 次运镜


def visible_window(x: float, y: float, s: float) -> tuple[float, float, float, float]:
    return (x - STAGE_CX / s, x + STAGE_CX / s, y - STAGE_CY / s, y + STAGE_CY / s)


def pan_budget(s: float) -> tuple[float, float]:
    """与 shotkit.panBudget 同式：缩放为 s 时允许的最大平移量（否则会露出边缘）。"""
    k = 1.0 - 1.0 / max(1.0, s)
    return STAGE_CX * k, STAGE_CY * k


def cam_keys(shot: dict) -> list[dict]:
    """把 shots.json 里的 camera 声明显开成显式关键帧表（与 shotkit.shotCam 同形）。"""
    # 解析后的记录把展开好的关键帧放在顶层 keys（唯一真源）；不要再去"猜"一遍。
    if shot.get("keys"):
        return shot["keys"]
    cam = shot.get("camera") or {}
    if cam.get("keys"):
        return cam["keys"]
    intent = cam.get("intent", "still")
    dur = int(shot["duration"])
    at = int(cam.get("at", 0))
    span = int(cam.get("dur", 38))
    x = float(cam.get("x", STAGE_CX))
    y = float(cam.get("y", STAGE_CY))
    frm = float(cam.get("from", 1.0))
    to = float(cam.get("to", frm))
    fx = float(cam.get("fromX", x))
    fy = float(cam.get("fromY", y))
    rot = float(cam.get("rotY", 0.0))
    hold = max(at + span, dur)
    head = {"f": 0, "x": fx, "y": fy, "s": frm}
    if intent in ("establish", "push-in", "pull-back", "reveal"):
        return [head, {"f": at, "x": x, "y": y, "s": frm}, {"f": at + span, "x": x, "y": y, "s": to}, {"f": hold, "x": x, "y": y, "s": to}]
    if intent == "pan-follow":
        return [head, {"f": at, "x": fx, "y": fy, "s": frm}, {"f": at + span, "x": x, "y": y, "s": to}, {"f": hold, "x": x, "y": y, "s": to}]
    if intent == "micro-orbit":
        return [
            {**head, "rotY": 0.0},
            {"f": at, "x": x, "y": y, "s": frm, "rotY": 0.0},
            {"f": at + span, "x": x, "y": y, "s": to, "rotY": rot},
            {"f": hold, "x": x, "y": y, "s": to, "rotY": rot},
        ]
    return [head, {"f": dur, "x": x, "y": y, "s": frm}]


def check(shots: list[dict], duration: int, theme: str = 'cel') -> tuple[list[dict], list[dict]]:
    p0: list[dict] = []
    p1: list[dict] = []
    if not shots:
        p0.append({"id": "-", "issue": "shots.json 没有 shots"})
        return p0, p1

    # ---- 时间轴覆盖 ----
    cursor = 0
    for s in shots:
        if s["from"] != cursor:
            p0.append({"id": s["id"], "issue": f"时间轴断档/重叠：期望 from={cursor}，实际 {s['from']}"})
        cursor = s["to"]
    if cursor != duration:
        p0.append({"id": "-", "issue": f"最后一镜止于 {cursor}，DURATION={duration}，末帧空档"})

    # ---- 逐镜镜头校验 ----
    for s in shots:
        sid = s["id"]
        keys = cam_keys(s)
        anchor = s.get("anchor")
        if not anchor:
            p0.append({"id": sid, "issue": "缺少 anchor（本镜必须始终可见的矩形）；无法证明不出界"})
            continue
        frames = [k["f"] for k in keys]
        if frames != sorted(frames):
            p0.append({"id": sid, "issue": "相机关键帧 f 不是单调递增"})
        if frames[0] != 0 or frames[-1] != s["duration"]:
            p0.append({"id": sid, "issue": f"相机关键帧必须覆盖 [0,{s['duration']}]，实际 [{frames[0]},{frames[-1]}]"})
        cam = s.get("camera") or {}
        intent = s.get("cameraIntent", cam.get("intent", "still"))
        hero_kind = s.get("hero", {}).get("kind", "text")
        cap = min(INTENT_MAX_ZOOM.get(intent, 1.0), GRAPHIC_ZOOM_MAX if hero_kind == "graphic" else TEXT_ZOOM_MAX)
        for k in keys:
            if k["s"] < 1.0 - 1e-6:
                p0.append({"id": sid, "f": k["f"], "issue": f"缩放 s={k['s']} < 1.00（画面会露出画布外）"})
            if k["s"] > cap + 1e-6:
                p0.append({"id": sid, "f": k["f"], "issue": f"缩放 s={k['s']} 超过 intent={intent} 预算 {cap}"})
            if abs(k.get("rotY", 0.0)) > ROT_MAX + 1e-6:
                p0.append({"id": sid, "f": k["f"], "issue": f"rotY={k.get('rotY')} 超过 {ROT_MAX}°"})
            bx, by = pan_budget(k["s"])
            if abs(k["x"] - STAGE_CX) > bx + 0.5 or abs(k["y"] - STAGE_CY) > by + 0.5:
                # P0：运行时 camAt() 会按预算钳制平移，所以"声明超预算"= 作者以为的取景
                # 与最终渲染不一致（静默失效）。修法很简单：把 from 缩放提到能覆盖平移量。
                p0.append({"id": sid, "f": k["f"],
                           "issue": f"平移 ({k['x']:.0f},{k['y']:.0f}) 超出缩放 s={k['s']:.3f} 的安全预算 (±{bx:.0f},±{by:.0f})；运行时会被静默削减。想平移多少，就先把 from 缩放到能覆盖它（maxPan=960*(1-1/s)）"})
            bx2, by2 = pan_budget(k["s"])
            cxk = min(STAGE_CX + bx2, max(STAGE_CX - bx2, k["x"]))
            cyk = min(STAGE_CY + by2, max(STAGE_CY - by2, k["y"]))
            left, right, top, bottom = visible_window(cxk, cyk, k["s"])
            ax, ay, aw, ah = anchor["x"], anchor["y"], anchor["w"], anchor["h"]
            for axis, need, lo, hi in (("x", ax, left, right), ("x", ax + aw, left, right), ("y", ay, top, bottom), ("y", ay + ah, top, bottom)):
                if need < lo - 0.5:
                    p0.append({"id": sid, "f": k["f"], "issue": f"anchor 出界：{axis}={need:.0f} < 可见边界 {lo:.0f}"})
                elif need > hi + 0.5:
                    p0.append({"id": sid, "f": k["f"], "issue": f"anchor 出界：{axis}={need:.0f} > 可见边界 {hi:.0f}"})

        # ---- 运镜时长与配额 ----
        if intent != "still":
            span = int(cam.get("dur", 38))
            if not (CAM_DUR[0] <= span <= CAM_DUR[1]):
                p1.append({"id": sid, "issue": f"单次运镜 {span} 帧，建议 {CAM_DUR[0]}–{CAM_DUR[1]} 帧"})
            moving = sum(1 for a, b in zip(keys, keys[1:]) if abs(a["s"] - b["s"]) > 1e-6 or abs(a["x"] - b["x"]) > 1e-6 or abs(a["y"] - b["y"]) > 1e-6)
            if moving > 1:
                p1.append({"id": sid, "issue": f"本镜有 {moving} 段位移，约定每镜 ≤1 次运镜"})
            # P0：声明了运镜就必须真的动。否则"把 still 改名成 push-in"就能同时骗过
            # 意图多样性统计和每章运镜配额，而画面完全静止（v2.8 的老毛病换了件衣服）。
            scale_span = max(k["s"] for k in keys) - min(k["s"] for k in keys)
            pan_span = (max(k["x"] for k in keys) - min(k["x"] for k in keys)) + (max(k["y"] for k in keys) - min(k["y"] for k in keys))
            if scale_span < 0.02 - 1e-9 and pan_span < 20 - 1e-9:
                p0.append({"id": sid, "issue": f"声明 intent={intent} 但关键帧几乎不动（Δs={scale_span:.3f}, Δ平移={pan_span:.1f}px）；把 still 改名成运镜不算运镜"})

    # ---- 每章运镜配额 ----
    chapters: dict[str, list[dict]] = {}
    for s in shots:
        chapters.setdefault(s.get("chapter", "-"), []).append(s)
    for name, group in chapters.items():
        moves = [s for s in group if s.get("cameraIntent", "still") != "still"]
        seconds = sum(s["duration"] for s in group) / 30.0
        need = CHAPTER_MIN_MOVES_LONG if seconds >= CHAPTER_LONG_SECONDS else CHAPTER_MIN_MOVES_SHORT
        if len(moves) < need:
            p0.append({"id": f"chapter:{name}", "issue": f"本章（{seconds:.1f}s）仅 {len(moves)} 次运镜，配额 ≥{need}"})
    total_moves = sum(1 for s in shots if s.get("cameraIntent", "still") != "still")
    film_need = max(4, -(-int(duration) // (FILM_MOVES_MIN_PER_12S * 30)))
    if total_moves < film_need:
        p0.append({"id": "-", "issue": f"全片仅 {total_moves} 次运镜，按片长 {duration / 30:.1f}s 要求 ≥{film_need} 次"})
    all_intents = {s.get("cameraIntent", "still") for s in shots}
    if len(all_intents - {"still"}) < 3:
        p0.append({"id": "-", "issue": f"全片仅 {len(all_intents - {'still'})} 种镜头意图（不含 still），要求 ≥3 种"})

    # ---- 背景装饰区可读性：内容压到装饰区必须声明 cover ----
    decor = DECOR_ZONES.get(theme, [])
    for s in shots:
        if s.get("bottomFill") is False:
            continue
        band = s.get("contentBand")
        if not band or not decor:
            continue
        for zone in decor:
            if rect_overlap(band, zone):
                if not s.get("cover"):
                    p1.append({"id": s["id"], "issue": f"内容带与 {theme} 背景装饰区重叠，但未声明 cover（文字可能被装饰吃掉）"})
                break
    return p0, p1


DECOR_ZONES: dict[str, list[dict]] = {
    "cel": [
        {"x": 0, "y": 620, "w": 820, "h": 460},
        {"x": 1230, "y": 560, "w": 690, "h": 520},
        {"x": 1640, "y": 370, "w": 210, "h": 210},
        {"x": 60, "y": 400, "w": 120, "h": 120},
    ],
    "flat": [
        {"x": 1240, "y": 380, "w": 680, "h": 700},
        {"x": 0, "y": 700, "w": 780, "h": 380},
    ],
    "paper": [],
    "sticker": [],
}


def rect_overlap(a: dict, b: dict) -> bool:
    return not (a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"] or a["y"] + a["h"] <= b["y"] or b["y"] + b["h"] <= a["y"])


def load_shots(project: Path) -> tuple[list[dict], int, str]:
    shots_path = project / "manifests" / "shots.resolved.json"
    if not shots_path.exists():
        raise SystemExit(f"缺少 {shots_path}；先运行 python scripts/resolve-shots.py PROJECT_DIR")
    data = json.loads(shots_path.read_text(encoding="utf-8"))
    if not data.get("duration"):
        raise SystemExit(f"{shots_path} 缺少 duration；重新运行 resolve-shots.py")
    return data.get("shots", []), int(data["duration"]), data.get("theme", "cel")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"项目目录不存在：{project}", file=sys.stderr)
        return 2
    shots, duration, theme = load_shots(project)
    p0, p1 = check(shots, duration, theme)
    if args.json:
        print(json.dumps({"p0": p0, "p1": p1, "shots": len(shots), "duration": duration}, ensure_ascii=False, indent=2))
    else:
        print(f"validate-shot-motion · {len(shots)} 镜 / {duration} 帧 / theme={theme}")
        for item in p0:
            print(f"  P0 {item['id']} f={item.get('f', '-')}: {item['issue']}")
        for item in p1:
            print(f"  P1 {item['id']}: {item['issue']}")
        print(f"结论：P0={len(p0)} P1={len(p1)} → {'PASS' if not p0 else 'FAIL'}")
    return 1 if p0 else 0


if __name__ == "__main__":
    sys.exit(main())
