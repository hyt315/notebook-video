#!/usr/bin/env python3
"""validate-shot-motion.py · camera geometry safety check

Static framing is valid and needs no meaningless anchor. Whenever a camera transform changes the view,
require an explicit essential-content anchor and check the visible window at every key. Also validate
timeline coverage, transform limits and runtime pan-clamping risks. A declared move that did not occur is
only a P1 note; it is not an instruction to animate.

Geometry constants below use the template's 16:9 1920×1080 design space. The 4:3 and 3:4 layouts have
not been adequately tested; do not treat this validator as proof of their safety until it is extended and
the corresponding layouts are rendered and reviewed.

Camera geometry (must stay in sync with assets/lecture-template/src/shotkit.tsx):
    可见窗 left = x - 960/s, right = x + 960/s, top = y - 540/s, bottom = y + 540/s
    The rendered camera keys are expanded by resolve-shots.py, so this check does not create a second
    timing source. A still view at the neutral center cannot crop the stage.

用法：
    python scripts/validate-shot-motion.py PROJECT_DIR
    python scripts/validate-shot-motion.py PROJECT_DIR --json
退出码：0 通过（可含 P1 警告）/ 1 存在 P0 违规 / 2 用法或文件错误
零第三方依赖，Python 3.10+ 标准库。
"""
from __future__ import annotations

import argparse
import importlib.util
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
ROT_MAX = 6.0  # micro-orbit 的 rotY 上限（度）；仅限作者主动选择该运动时


def visible_window(x: float, y: float, s: float) -> tuple[float, float, float, float]:
    return (x - STAGE_CX / s, x + STAGE_CX / s, y - STAGE_CY / s, y + STAGE_CY / s)


def pan_budget(s: float) -> tuple[float, float]:
    """与 shotkit.panBudget 同式：缩放为 s 时允许的最大平移量（否则会露出边缘）。"""
    k = 1.0 - 1.0 / max(1.0, s)
    return STAGE_CX * k, STAGE_CY * k


# 渲染键展开的**唯一真源**在 resolve-shots.py（它同时喂渲染）：本门禁 import 复用，
# 不再手写第二份同形展开——两份各自演化正是"validate 与渲染不一致"的病灶（2026-09 收口）。
# importlib 按文件路径加载，同 validate-semantic-breaks.py 载入 build-semantic-captions 的先例；
# resolve-shots.py 的 CLI/写盘全在 `if __name__ == "__main__"` 守护里，import 无副作用。
_RESOLVE_SOURCE = Path(__file__).resolve().parent / "resolve-shots.py"


def _load_expand_cam():
    spec = importlib.util.spec_from_file_location("_resolve_shots_expand", _RESOLVE_SOURCE)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法从 {_RESOLVE_SOURCE} 载入 expand_cam：相机展开没有第二真源，载入失败=门禁自身故障")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.expand_cam


expand_cam = _load_expand_cam()


def cam_keys(shot: dict) -> list[dict]:
    """解析后的记录把展开好的关键帧放在顶层 keys（唯一真源）；不要再去"猜"一遍。
    后备路径（陈旧/手改的 resolved 缺 keys）直接调 resolve-shots.expand_cam，
    隐式默认（intent 的 to / pull-back 的 from / micro-orbit 的 rotY）与渲染端 shotCam 同源。"""
    if shot.get("keys"):
        return shot["keys"]
    return expand_cam(shot.get("camera") or {}, int(shot["duration"]))


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
        has_transform = any(
            abs(k.get("s", 1.0) - 1.0) > 1e-6
            or abs(k.get("x", STAGE_CX) - STAGE_CX) > 1e-6
            or abs(k.get("y", STAGE_CY) - STAGE_CY) > 1e-6
            or abs(k.get("rotY", 0.0)) > 1e-6
            for k in keys
        )
        # A neutral still camera cannot crop the stage, so requiring a hand-authored
        # rectangle there adds paperwork without adding a safety proof. Any transform
        # still requires an explicit teaching-content anchor.
        if not anchor and has_transform:
            p0.append({"id": sid, "issue": "相机有zoom/pan/orbit变换却缺少 anchor；无法证明教学主体不出界"})
        frames = [k["f"] for k in keys]
        if frames != sorted(frames):
            p0.append({"id": sid, "issue": "相机关键帧 f 不是单调递增"})
        if frames[0] != 0 or frames[-1] != s["duration"]:
            p0.append({"id": sid, "issue": f"相机关键帧必须覆盖 [0,{s['duration']}]，实际 [{frames[0]},{frames[-1]}]"})
        cam = s.get("camera") or {}
        intent = s.get("cameraIntent", cam.get("intent", "still"))
        if intent != "still" and keys:
            first = keys[0]
            has_camera_change = any(
                abs(k.get("s", 1.0) - first.get("s", 1.0)) > 0.005
                or abs(k.get("x", STAGE_CX) - first.get("x", STAGE_CX)) > 1.0
                or abs(k.get("y", STAGE_CY) - first.get("y", STAGE_CY)) > 1.0
                or abs(k.get("rotY", 0.0) - first.get("rotY", 0.0)) > 0.1
                for k in keys[1:]
            )
            if not has_camera_change:
                p1.append({"id": sid, "issue": (
                    f"cameraIntent={intent!r} 但关键帧没有可见相机变化；这是可选注记与实现不一致，"
                    "修正注记或忽略即可，不代表镜头必须运动")})
        hero = s.get("hero") or {}
        hero_kind = hero.get("kind", "text") if isinstance(hero, dict) else "text"
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
            if anchor:
                ax, ay, aw, ah = anchor["x"], anchor["y"], anchor["w"], anchor["h"]
                for axis, need, lo, hi in (("x", ax, left, right), ("x", ax + aw, left, right), ("y", ay, top, bottom), ("y", ay + ah, top, bottom)):
                    if need < lo - 0.5:
                        p0.append({"id": sid, "f": k["f"], "issue": f"anchor 出界：{axis}={need:.0f} < 可见边界 {lo:.0f}"})
                    elif need > hi + 0.5:
                        p0.append({"id": sid, "f": k["f"], "issue": f"anchor 出界：{axis}={need:.0f} > 可见边界 {hi:.0f}"})

    # ---- 背景装饰区可读性：内容压到装饰区必须声明 cover ----
    decor = DECOR_ZONES.get(theme, [])
    for s in shots:
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
