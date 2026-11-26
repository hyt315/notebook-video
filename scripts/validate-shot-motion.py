#!/usr/bin/env python3
"""validate-shot-motion.py · 镜头出界证明门禁（P0，可阻断渲染）

把"相机契约"从"靠自觉"变成"可执行证明"。把相机锁死在极窄的区间里（景别变化 1.8%，等同定焦）
等于全片没有镜头在动；放开而不校验又会让可见窗出画。两个极端都是"没有校验"造成的。
本脚本用纯算术证明"镜头运动后，本镜声明必须可见的 anchor
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
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract import C  # noqa: E402  跨语言常量：assets/lecture-template/src/contract.json
from gate_report import finish  # noqa: E402  统一结果：设了 NV_GATE_JSON 就逐条追加一行 JSON

FPS = C["FPS"]
STAGE_CX, STAGE_CY = float(C["STAGE"]["cx"]), float(C["STAGE"]["cy"])

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
TEXT_ZOOM_MAX = C["TEXT_ZOOM_MAX"]
GRAPHIC_ZOOM_MAX = C["GRAPHIC_ZOOM_MAX"]
ROT_MAX = float(C["ORBIT_ROT"])  # micro-orbit 的 rotY 上限（度）= shotkit 默认环绕角
CAM_DUR = (C["CAM_DUR"]["short"], C["CAM_DUR"]["long"])  # 单次运镜时长（帧），references/camera.md#shot-language
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
    """本镜真正渲染的相机关键帧。有 cinema.path 时引擎直接走 pathCamAt（auto 路线），按 path 查，补到镜尾；
    否则用解析后顶层的 keys（唯一真源）。后备路径（陈旧/手改的 resolved 缺 keys）直接调 resolve-shots.expand_cam，
    隐式默认（intent 的 to / pull-back 的 from / micro-orbit 的 rotY）与渲染端 shotCam 同源。"""
    path = (shot.get("cinema") or {}).get("path")
    if path:
        ks = [{"f": int(k["at"]), "x": float(k["x"]), "y": float(k["y"]), "s": float(k["s"])} for k in path]
        return ks + ([{**ks[-1], "f": int(shot["duration"])}] if ks[-1]["f"] < int(shot["duration"]) else [])
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
        if not anchor:
            p0.append({"id": sid, "issue": "缺少 anchor（本镜必须始终可见的矩形）；无法证明不出界"})
            continue
        frames = [k["f"] for k in keys]
        has_path = bool((s.get("cinema") or {}).get("path"))
        if any(b < a or (has_path and b == a) for a, b in zip(frames, frames[1:])):
            p0.append({"id": sid, "issue": "相机关键帧 f 不是单调递增" + ("（cinema.path 的 at 必须严格递增）" if has_path else "")})
        if frames[0] != 0 or frames[-1] != s["duration"]:
            p0.append({"id": sid, "issue": f"相机关键帧必须覆盖 [0,{s['duration']}]，实际 [{frames[0]},{frames[-1]}]"})
        cam = s.get("camera") or {}
        intent = s.get("cameraIntent", cam.get("intent", "still"))
        hero_kind = (s.get("hero") or {}).get("kind", "text")
        zmax = GRAPHIC_ZOOM_MAX if hero_kind == "graphic" else TEXT_ZOOM_MAX
        # path 镜的 intent 是从路径读出的描述，不是声明的预算：只受总缩放上限约束
        cap = zmax if has_path else min(INTENT_MAX_ZOOM.get(intent, 1.0), zmax)
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

        # ---- 运镜时长 ----
        if intent != "still":
            span = int(cam.get("dur", C["CAM_DUR"]["std"]))
            if not (CAM_DUR[0] <= span <= CAM_DUR[1]):
                p1.append({"id": sid, "issue": f"单次运镜 {span} 帧，建议 {CAM_DUR[0]}–{CAM_DUR[1]} 帧"})
            moving = sum(1 for a, b in zip(keys, keys[1:]) if abs(a["s"] - b["s"]) > 1e-6 or abs(a["x"] - b["x"]) > 1e-6 or abs(a["y"] - b["y"]) > 1e-6)
            if moving > 1:
                p1.append({"id": sid, "issue": f"本镜有 {moving} 段位移，约定每镜 ≤1 次运镜"})
            # P1：声明了运镜却几乎不动 → 点名提示。多样性与配额本身也是 P1，
            # 这里点名是为了不让「改名成 push-in」把那两条提示悄悄消掉。
            scale_span = max(k["s"] for k in keys) - min(k["s"] for k in keys)
            pan_span = (max(k["x"] for k in keys) - min(k["x"] for k in keys)) + (max(k["y"] for k in keys) - min(k["y"] for k in keys))
            if scale_span < 0.02 - 1e-9 and pan_span < 20 - 1e-9:
                p1.append({"id": sid, "issue": f"声明 intent={intent} 但关键帧几乎不动（Δs={scale_span:.3f}, Δ平移={pan_span:.1f}px）；把 still 改名成运镜不算运镜"})

    # ---- 每章运镜配额（P1，提示不阻断）----
    chapters: dict[str, list[dict]] = {}
    for s in shots:
        chapters.setdefault(s.get("chapter", "-"), []).append(s)
    for name, group in chapters.items():
        moves = [s for s in group if s.get("cameraIntent", "still") != "still"]
        seconds = sum(s["duration"] for s in group) / FPS
        need = CHAPTER_MIN_MOVES_LONG if seconds >= CHAPTER_LONG_SECONDS else CHAPTER_MIN_MOVES_SHORT
        if len(moves) < need:
            p1.append({"id": f"chapter:{name}", "issue": f"本章（{seconds:.1f}s）仅 {len(moves)} 次运镜，配额 ≥{need}"})
    total_moves = sum(1 for s in shots if s.get("cameraIntent", "still") != "still")
    film_need = max(4, -(-int(duration) // (FILM_MOVES_MIN_PER_12S * FPS)))
    if total_moves < film_need:
        p1.append({"id": "-", "issue": f"全片仅 {total_moves} 次运镜，按片长 {duration / FPS:.1f}s 要求 ≥{film_need} 次"})
    all_intents = {s.get("cameraIntent", "still") for s in shots}
    if len(all_intents - {"still"}) < 3:
        p1.append({"id": "-", "issue": f"全片仅 {len(all_intents - {'still'})} 种镜头意图（不含 still），要求 ≥3 种"})

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
    p1 += check_beat_gaps(shots)
    p0c, p1c = check_cinema(shots)
    return p0 + p0c, p1 + p1c


# ---------------------------------------------------------------------------
# 引擎摄影机（src/cinema.tsx，resolve-shots 预算的 cinema 块）
#   · 内容自动放大：anchor 占内容带（安全区）面积放大后应落在 60–80%。
#     放大后仍 < 45% → P0（引擎已推到上限仍太小：内容本身画小了，PPT 感的头号来源）；
#     45–60% → P1；> 90% → P1（太满、没有呼吸空间；80–90% 视作 anchor 外接框的正常余量）。
#   · 焦点推近：focus.zoom × 场景缩放不超过 TEXT_ZOOM_MAX；焦点矩形放大后必须放得进画面。
#   · 缺 cinema 块 → P1（没重跑 resolve-shots，引擎只剩缺省漂移、没有自动放大）。
FIT_P0, FIT_LO, FIT_HI_WARN = 0.45, 0.60, 0.90
# 修法与 references/checks.md#render-gates「被判空怎么修」同一句；红线：不改小 anchor
FILL_FIX = "在空洞处补属于本镜主体的信息层，anchor 如实框住它（不改小 anchor、不放大卡片凑面积），目标 60–80%"


def check_cinema(shots: list[dict]) -> tuple[list[dict], list[dict]]:
    p0: list[dict] = []
    p1: list[dict] = []
    for s in shots:
        sid = s["id"]
        cin = s.get("cinema")
        if not isinstance(cin, dict):
            p1.append({"id": sid, "issue": "没有 cinema 块（旧解析结果？重跑 resolve-shots.py 才有内容自动放大 / 焦点推近）"})
            continue
        fit = cin.get("fit") or {}
        fa = fit.get("fillAfter")
        if isinstance(fa, (int, float)):
            text_first = str(s.get("layout") or "").split("-")[0] in ("statement", "define", "quiz", "list", "custom", "type")
            if fa < FIT_P0 and text_first:
                p1.append({"id": sid, "issue": f"内容占安全区 {fa:.0%}：卡片 / 定制版式，留白是有意的（只提示）—— 若显得空，加大字号或补一句副标题"})
            elif fa < FIT_P0:
                p0.append({"id": sid, "issue": f"内容只占安全区 {fa:.0%}（自动放大已到上限）：{FILL_FIX}"})
            elif fa < FIT_LO:
                p1.append({"id": sid, "issue": f"内容占安全区 {fa:.0%} < 60%：偏小，{FILL_FIX}"})
            elif fa > FIT_HI_WARN:
                p1.append({"id": sid, "issue": f"anchor 占安全区 {fa:.0%} > 90%：太满，没有呼吸空间：精简本镜内容或拆成两镜"})
        scene_s = max([float(k.get("s", 1.0)) for k in cam_keys(s)] or [1.0])
        for i, fk in enumerate(cin.get("focus") or []):
            r = fk.get("rect") or {}
            z = fk.get("zoom")
            if z is not None and float(z) * scene_s > TEXT_ZOOM_MAX + 1e-6:
                p1.append({"id": sid, "issue": f"cinema.focus[{i}].zoom={z} × 场景缩放 {scene_s} > {TEXT_ZOOM_MAX}，引擎会钳制"})
            if r and (float(r.get("w", 0)) * max(1.1, float(z or 1.1)) > 1920 + 1 or float(r.get("h", 0)) * max(1.1, float(z or 1.1)) > 1080 + 1):
                p1.append({"id": sid, "issue": f"cinema.focus[{i}] 焦点矩形放大后放不进画面（会被钳到可容纳的缩放）"})
            if not (0 <= int(fk.get("at", 0)) < s["duration"]):
                p0.append({"id": sid, "issue": f"cinema.focus[{i}].at={fk.get('at')} 不在本镜 [0,{s['duration']}) 内"})
    return p0, p1


# ---------------------------------------------------------------------------
# 节拍空档（P1，**代理指标**，不是判据）
#
# beats 是**旁白节拍**，不是**画面事件**：元素绑在某一拍上，但它的入场动画可能在 30 帧内就演完了，
# 离下一拍还有几十帧什么都不动。按 40% 这类阈值判，节奏正常的镜会被判死、真正停住的镜反而 PASS。
# 所以这条**只当"这一镜是不是整段没词"的粗筛**，定在 60%（抓明显异常）；
# 真正的判据是 `validate-motion-gaps.py`（量成片里画面到底动没动，T3 后验）。
BEAT_GAP_MAX_RATIO = 0.60


def check_beat_gaps(shots: list[dict]) -> list[dict]:
    out: list[dict] = []
    for s in shots:
        beats = sorted(int(b) for b in (s.get("beats") or []))
        dur = int(s.get("duration") or 0)
        if dur <= 0 or not beats:
            continue
        marks = [0] + beats + [dur]
        gaps = [marks[i + 1] - marks[i] for i in range(len(marks) - 1)]
        worst = max(gaps)
        ratio = worst / dur
        if ratio > BEAT_GAP_MAX_RATIO:
            out.append(
                {
                    "id": s["id"],
                    "issue": f"相邻节拍最大间隔 {worst} 帧 = 镜长的 {ratio * 100:.0f}%（上限 {BEAT_GAP_MAX_RATIO:.0%}）："
                    f"这一段没有任何新事件绑定，旁白在讲、画面容易被读作停住",
                }
            )
    return out


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
    return finish("validate-shot-motion", p0, p1, "manifests/shots.resolved.json",
                  payload={"p0": p0, "p1": p1, "shots": len(shots), "duration": duration} if args.json else None,
                  header=f"validate-shot-motion · {len(shots)} 镜 / {duration} 帧 / theme={theme}",
                  item0=lambda x: f"{x['id']} f={x.get('f', '-')}: {x['issue']}")


if __name__ == "__main__":
    sys.exit(main())
