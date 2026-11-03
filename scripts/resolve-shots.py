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
import hashlib
import io
import json
import re
import sys
from pathlib import Path

FPS = 30
STAGE_CX, STAGE_CY = 960.0, 540.0


def ms_frame(ms: float) -> int:
    return int(round(ms * FPS / 1000))


# ---- shotCam 的隐式默认（TS 权威 = assets/lecture-template/src/shotkit.tsx，逐条对应行号）----
# 省略 to 时按 intent 回落（`o.to ?? <值>`），不再一律回落成 from —— 回落成 from = 不动，
# 既骗过渲染（成片静止）又触发 validate-shot-motion 的"声明运镜却不动"P0（误拦省略参数的镜）。
# · establish 1.03（shotkit.tsx:113） push-in 1.12（:116） pull-back 1.0（:119） reveal 1.08（:125）
# · pan-follow / micro-orbit / still 的 to 回落 from（`o.to ?? o.from ?? 1`，:122/:128/:109）
DEFAULT_TO = {"establish": 1.03, "push-in": 1.12, "reveal": 1.08, "pull-back": 1.0}
# pull-back 省略 from 时**只抬 k1**（f=at 那一帧，shotkit.tsx:119 的 `o.from ?? 1.12`：先推近再拉远），
# head（f=0）仍是 `o.from ?? 1`（shotkit.tsx:108）—— head/k1 默认值不同是 TS 原样行为，照抄。
DEFAULT_FROM_K1 = {"pull-back": 1.12}
# micro-orbit 省略 rotY 时 TS 默认 6°（shotkit.tsx:128 的 `rotY: o.rotY ?? 6`）；其余 intent 不用 rotY。
DEFAULT_ROT_Y = {"micro-orbit": 6.0}


def expand_cam(cam: dict, duration: int) -> list[dict]:
    """与 assets/lecture-template/src/shotkit.tsx 的 shotCam() 同形（改一处要同步另一处）。

    本函数是渲染键展开的**唯一真源**：resolve 写进 shots.resolved.json / src/shots.ts，
    validate-shot-motion.py 直接 import 本函数走后备路径——默认值只维护这一份。"""
    if cam.get("keys"):
        return cam["keys"]
    intent = cam.get("intent", "still")
    at = int(cam.get("at", 0))
    span = int(cam.get("dur", 38))
    x = float(cam.get("x", STAGE_CX))
    y = float(cam.get("y", STAGE_CY))
    frm = float(cam.get("from", 1.0))
    to = float(cam.get("to", DEFAULT_TO.get(intent, frm)))
    fx = float(cam.get("fromX", x))
    fy = float(cam.get("fromY", y))
    rot = float(cam.get("rotY", DEFAULT_ROT_Y.get(intent, 0.0)))
    hold = max(at + span, duration)
    head = {"f": 0, "x": fx, "y": fy, "s": frm}
    k1 = float(cam.get("from", DEFAULT_FROM_K1.get(intent, 1.0)))
    if intent in ("establish", "push-in", "pull-back", "reveal"):
        return [head, {"f": at, "x": x, "y": y, "s": k1}, {"f": at + span, "x": x, "y": y, "s": to}, {"f": hold, "x": x, "y": y, "s": to}]
    if intent == "pan-follow":
        # 平移想走多远，缩放就自动抬到能覆盖它（maxPan = 960*(1-1/s)），否则运行时会被静默削减
        # 成几乎不动（旧版演示片 S6 只剩 ±37px）。显式写了更大的 from/to 照用。
        need_dx = max(abs(fx - STAGE_CX), abs(x - STAGE_CX))
        need_dy = max(abs(fy - STAGE_CY), abs(y - STAGE_CY))
        need = max(STAGE_CX / max(1.0, STAGE_CX - need_dx), STAGE_CY / max(1.0, STAGE_CY - need_dy))
        need = round(need + 0.005, 3) if need > 1.0 + 1e-9 else 1.0
        frm = max(frm, need)
        to = max(to, need)
        head = {"f": 0, "x": fx, "y": fy, "s": frm}
        return [head, {"f": at, "x": fx, "y": fy, "s": frm}, {"f": at + span, "x": x, "y": y, "s": to}, {"f": hold, "x": x, "y": y, "s": to}]
    if intent == "micro-orbit":
        return [{**head, "rotY": 0}, {"f": at, "x": x, "y": y, "s": frm, "rotY": 0}, {"f": at + span, "x": x, "y": y, "s": to, "rotY": rot}, {"f": hold, "x": x, "y": y, "s": to, "rotY": rot}]
    # still：尾帧缩放对齐 shotkit 的 tail `s: o.to ?? o.from ?? 1`（shotkit.tsx:109/:130）——
    # 显式写了 to 的 still 以前在这里被**整枚丢掉**（PY 用 frm，TS 用 to），Δ 可达 0.20；
    # 现在 to 默认回落 frm，两者一致，只有"写了 to 却不动"的镜会按新行为真的推到 to。
    return [head, {"f": duration, "x": x, "y": y, "s": to}]


# 3.2.0 内容自动放大（与 src/cinema.tsx 的 CINEMA.fit* 同值）：anchor（本镜内容的外接矩形）占内容带
# （安全区）面积不足 FIT_MIN 时，引擎把整镜按 anchor 中心推近到 FIT_TARGET；推近受三条上限钳制：
# anchor 放大后仍完整落在内容带内、TEXT_ZOOM_MAX（与场景 ShotCamera 相乘后）、FIT_MAX_S。
FIT_MIN, FIT_TARGET, FIT_HI = 0.60, 0.72, 0.80
FIT_MAX_S = 1.30
TEXT_ZOOM_MAX = 1.35


def compute_fit(anchor: dict | None, band: dict, keys: list[dict], mode) -> dict:
    """返回 {x, y, s, fill, fillAfter}：引擎的基准取景（注视点 + 缩放）。mode = "auto" | "none"。"""
    base = {"x": 960.0, "y": 540.0, "s": 1.0, "fill": 1.0, "fillAfter": 1.0}
    if not anchor or not band:
        return base
    aw, ah, bw, bh = float(anchor["w"]), float(anchor["h"]), float(band["w"]), float(band["h"])
    fill = (aw * ah) / max(1.0, bw * bh)
    base["fill"] = base["fillAfter"] = round(fill, 3)
    if mode == "none" or fill >= FIT_MIN:
        return base
    scene_s = max([float(k.get("s", 1.0)) for k in keys] or [1.0])
    s = min((FIT_TARGET / fill) ** 0.5, bw / aw, bh / ah, FIT_MAX_S, TEXT_ZOOM_MAX / max(1.0, scene_s))
    s = max(1.0, s)
    cx, cy = float(anchor["x"]) + aw / 2, float(anchor["y"]) + ah / 2
    hx, hy = 960.0 / s, 540.0 / s
    cx = min(1920.0 - hx, max(hx, cx))
    cy = min(1080.0 - hy, max(hy, cy))
    return {"x": round(cx, 1), "y": round(cy, 1), "s": round(s, 3), "fill": round(fill, 3), "fillAfter": round(fill * s * s, 3)}


REGIONS = ("left", "right", "top", "bottom", "center", "top-left", "top-right", "bottom-left", "bottom-right")
TRANSITIONS = ("auto", "cut", "reveal", "handoff", "whip", "whip-left", "whip-right", "zoom", "fade", "hard", "slide", "drop", "pageturn", "peel", "pageflip")


def region_rect(r: str, band: dict) -> dict:
    """与 src/cinema.tsx 的 regionRect 同式。"""
    x, y, w, h = band["x"], band["y"], band["w"], band["h"]
    hw, hh = w / 2, h / 2
    table = {
        "left": (x, y, hw, h), "right": (x + hw, y, hw, h), "top": (x, y, w, hh), "bottom": (x, y + hh, w, hh),
        "top-left": (x, y, hw, hh), "top-right": (x + hw, y, hw, hh), "bottom-left": (x, y + hh, hw, hh),
        "bottom-right": (x + hw, y + hh, hw, hh),
    }
    rx, ry, rw, rh = table.get(r, (x + w * 0.2, y + h * 0.15, w * 0.6, h * 0.7))
    return {"x": round(rx, 1), "y": round(ry, 1), "w": round(rw, 1), "h": round(rh, 1)}


def resolve_cinema(s: dict, sid: str, frm: int, duration: int, cues: list, problems: list) -> dict:
    """分镜表 `cinema` 块 → 引擎可直接消费的形式（焦点的 beat/cue 换成本镜本地帧）。

    cinema: {
      drift: "auto" | "none" | 0.0–0.08,
      fit: "auto" | "none",            # 内容自动放大（anchor 占安全区 < 60% 时推近到 72%）
      focus: [{beat: 1 | at: 40 | cue: 5, region: "right" | x,y,w,h, zoom?: 1.25, hold?: 60}],
      pan: {worldW: 2800, beat?: 0, at?: 10, dur?: 90, dir?: "ltr" | "rtl"}
    }"""
    c = s.get("cinema") or {}
    band = s.get("contentBand") or {"x": 160, "y": 130, "w": 1600, "h": 760}
    beats = [(ms_frame(cues[int(bt["cue"])]["start_ms"]) + int(bt.get("offset", 0)) - frm) for bt in (s.get("beats") or [])]
    drift = c.get("drift", "auto")
    if not (drift in ("auto", "none") or isinstance(drift, (int, float))):
        problems.append(f"{sid}: cinema.drift 必须是 auto / none / 数字")
        drift = "auto"
    out: dict = {"drift": drift}
    if c.get("still"):
        out["still"] = True
    fit_mode = c.get("fit", "auto")
    if fit_mode not in ("auto", "none"):
        problems.append(f"{sid}: cinema.fit 必须是 auto / none")
        fit_mode = "auto"
    out["fit"] = compute_fit(s.get("anchor"), band, expand_cam(dict(s.get("camera") or {"intent": "still"}), duration), fit_mode)
    focus = []
    for i, fk in enumerate(c.get("focus") or []):
        if "beat" in fk:
            b = int(fk["beat"])
            if b < 0 or b >= len(beats):
                problems.append(f"{sid}: cinema.focus[{i}].beat={b} 越界（本镜 {len(beats)} 拍）")
                continue
            at = beats[b] + int(fk.get("offset", 0))
        elif "cue" in fk:
            at = ms_frame(cues[int(fk["cue"])]["start_ms"]) - frm + int(fk.get("offset", 0))
        else:
            at = int(fk.get("at", 0))
        if "region" in fk:
            if fk["region"] not in REGIONS:
                problems.append(f"{sid}: cinema.focus[{i}].region={fk['region']!r} 不是 {REGIONS} 之一")
                continue
            rect = region_rect(fk["region"], band)
        elif all(k in fk for k in ("x", "y", "w", "h")):
            rect = {k: float(fk[k]) for k in ("x", "y", "w", "h")}
        else:
            problems.append(f"{sid}: cinema.focus[{i}] 需要 region 或 x/y/w/h")
            continue
        default_hold = 60
        hold = int(fk.get("hold", default_hold))
        hold = max(10, min(hold, duration - at - 4))
        item = {"at": at, "hold": hold, "rect": rect}
        if fk.get("zoom") is not None:
            item["zoom"] = float(fk["zoom"])
        if fk.get("slide") is False:
            item["slide"] = False
        # keep = 推近时也必须完整入画的矩形（引擎会把推近倍数降到能装下「焦点 ∪ keep」，但不低于 focusMinZoom）。
        # 显式 keep:{x,y,w,h} / region；hero-number 版式缺省 keep = anchor（大数字在 anchor 里），左右各加 8% 字号的字形外溢余量；
        # keep:false 关掉。修演示片 S1：推近右侧终端时左侧「1.2 秒」被切掉半个字。
        kp = fk.get("keep")
        hero = s.get("hero") or {}
        if isinstance(kp, dict) and all(k in kp for k in ("x", "y", "w", "h")):
            item["keep"] = {k: float(kp[k]) for k in ("x", "y", "w", "h")}
        elif isinstance(kp, str) and kp in REGIONS:
            item["keep"] = region_rect(kp, band)
        elif kp is None and s.get("layout") == "hero-number" and hero.get("kind", "text") == "text" and s.get("anchor"):
            a = s["anchor"]; ov = round(0.08 * float(hero.get("size", 200)))
            item["keep"] = {"x": float(a["x"] - ov), "y": float(a["y"]), "w": float(a["w"] + 2 * ov), "h": float(a["h"])}
        elif kp not in (None, False):
            problems.append(f"{sid}: cinema.focus[{i}].keep 必须是 {{x,y,w,h}} / region / false")
        focus.append(item)
    # 镜尾收束。最后一个事件（拍点 / 焦点结束）到镜尾 > 45 帧（1.5 秒）时，画面只剩缓推，读起来是「卡住了」
    # （演示片 S6 / S8 的实测问题）。自动补一个轻推近到 anchor 的收束焦点；`cinema.settle: false` 关掉。
    last_evt = max([b for b in beats if b < duration] + [k["at"] + k["hold"] + 24 for k in focus] + [0])
    if c.get("settle", True) and not c.get("path") and duration - last_evt > 45:
        a = s.get("anchor") or band
        rect = {k: float(a[k]) for k in ("x", "y", "w", "h")}
        st = last_evt + 10
        focus.append({"at": st, "hold": max(10, duration - st - 6), "rect": rect, "zoom": 1.1, "settle": True})
    if focus:
        out["focus"] = focus
    pan = c.get("pan")
    if pan:
        ww = int(pan.get("worldW", 0))
        if ww <= 1920:
            problems.append(f"{sid}: cinema.pan.worldW={ww} 必须 > 1920（宽画布才需要横摇）")
        else:
            at = beats[int(pan["beat"])] if "beat" in pan and int(pan["beat"]) < len(beats) else int(pan.get("at", 10))
            dur = int(pan.get("dur", max(45, duration - at - 30)))
            out["pan"] = {"worldW": ww, "at": at, "dur": dur, "dir": pan.get("dir", "ltr")}
    # compose-story 预算好的相机路径（关键词推近 / 视线连续 / 速度上限都已算好）。原样透传。
    path = c.get("path")
    if path:
        ok = isinstance(path, list) and all(isinstance(k, dict) and all(q in k for q in ("at", "x", "y", "s")) for k in path)
        if not ok:
            problems.append(f"{sid}: cinema.path 必须是 [{{at,x,y,s}}] 列表")
        else:
            out["path"] = [{"at": int(k["at"]), "x": float(k["x"]), "y": float(k["y"]), "s": float(k["s"])} for k in path]
            out["fit"] = {"x": 960.0, "y": 540.0, "s": 1.0, "fill": out["fit"].get("fill", 1.0), "fillAfter": out["fit"].get("fillAfter", 1.0)}
    if s.get("transition") is not None and s["transition"] not in TRANSITIONS:
        problems.append(f"{sid}: transition={s['transition']!r} 不是 {TRANSITIONS} 之一")
    return out


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


BG_ROLES = ("main", "chapter", "quiet")


def chapter_starts(project: Path, out: list[dict]) -> set[str]:
    """章节首镜：优先读 src/film.ts 的 CHAPTER_SHOTS（引擎用的同一份），没有就按 chapter 名变化推。"""
    film = project / "src" / "film.ts"
    if film.is_file():
        m = re.search(r"CHAPTER_SHOTS\s*=\s*\[([^\]]*)\]", film.read_text(encoding="utf-8"))
        if m:
            ids = set(re.findall(r"['\"]([^'\"]+)['\"]", m.group(1)))
            if ids:
                return ids
    starts, prev = set(), object()
    for r in out:
        if r.get("chapter") != prev:
            starts.add(r["id"])
        prev = r.get("chapter")
    return starts


CRAFT_SKINS = ("journal", "papercut", "archive")
BG_MODES = ("film", "chapter", "shot")


def bg_mode(shots_doc: dict, problems: list[str] | None = None) -> str:
    """3.3.0：背景切换粒度。显式 bgMode 优先；否则手作皮肤 chapter、flat / cel shot。"""
    m = shots_doc.get("bgMode")
    if m is None:
        return "chapter" if shots_doc.get("theme", "cel") in CRAFT_SKINS else "shot"
    if m not in BG_MODES:
        if problems is not None:
            problems.append(f"bgMode={m!r} 不是 {' / '.join(BG_MODES)} 之一")
        return "shot"
    return m


SFX_DENSITIES = ("sparse", "normal")


def sfx_density(shots_doc: dict, problems: list[str] | None = None) -> str:
    """3.3.0：音效密度。缺省 sparse（每镜一记）；normal 是 3.3.0 的「一拍一个」。

    为什么缺省改成 sparse：旁白由使用者自行后配（任意 TTS 或真人），技能不知道以后有没有人声，
    按 24 条/分钟铺满会跟说话抢注意力。老工程想要原样，写 "sfxDensity": "normal"。
    """
    d = shots_doc.get("sfxDensity")
    if d is None:
        return "sparse"
    if d not in SFX_DENSITIES:
        if problems is not None:
            problems.append(f"sfxDensity={d!r} 不是 {' / '.join(SFX_DENSITIES)} 之一（缺省 sparse）")
        return "sparse"
    return d


def assign_backgrounds(project: Path, shots_doc: dict, out: list[dict], problems: list[str]) -> None:
    """3.3.0 背景库：给每镜定一张背景，写进 rec["bg"]（库 id）+ rec["bgFile"]（public/ 下相对路径）。

    · 显式 `bg`：库 id（'journal/ruled' 或简写 'ruled'）→ 用它；main / chapter / quiet → 用本皮肤的 legacy 那张。
    · 未写 `bg`：按镜头角色（章节首镜 chapter / zones ≥ 4 quiet / 其余 main）从「roles 含该角色」的库背景里轮换：
      先挑最久没用过的（从没用过的最优先），同分按 sha1(bgSeed:镜号:id) 定序；永不与上一镜同一张（候选只剩一张时除外）。
      纯函数：同一分镜表 + 同一 bgSeed → 同一结果。
    · 没有 manifests/backgrounds.json，或 shots.json 写了 "bgRotate": false → 不轮换（3.3.0 行为：
      引擎按 main / chapter / quiet 三张图自动选）；此时不出 bgFile 键，旧工程解析结果逐字节不变。
    · 3.3.0 `bgMode`（shots.json 工程级）：
        "shot"    逐镜轮换（上面的规则；flat / cel 默认）
        "chapter" 只在章节首镜换纸，章内沿用（journal / papercut / archive 默认：一本手账的媒介连续性）
        "film"    全片一张纸
      chapter / film 的"那张纸"要撑满章内所有常规镜，所以只从 roles 含 main 且非 busy 的背景里挑；
      跨章不与上一章同一张。显式 `bg` 永远优先，且只作用于那一镜。
    · `"busy": true` 的背景（装饰重）不分给 main 角色，只给章节卡 / 安静镜。
    """
    lib_p = project / "manifests" / "backgrounds.json"
    if not lib_p.is_file():
        for r in out:
            if r.get("bg") is not None and r["bg"] not in BG_ROLES:
                problems.append(f"{r['id']}: bg={r['bg']!r} 不是 main / chapter / quiet（本工程没有背景库 manifests/backgrounds.json）")
        return
    theme = shots_doc.get("theme", "cel")
    lib = json.loads(lib_p.read_text(encoding="utf-8")).get("backgrounds", [])
    every = {e["id"]: e for e in lib}
    mine = [e for e in lib if e.get("skin") == theme]
    rotate = bool(mine) and shots_doc.get("bgRotate", True) is not False
    seed = str(shots_doc.get("bgSeed", 0))
    mode = bg_mode(shots_doc, problems)
    chapters = chapter_starts(project, out)
    last_used: dict[str, int] = {}
    prev_file = None
    sheet = None          # chapter / film 模式下当前沿用的那张纸
    calm = [e for e in mine if "main" in (e.get("roles") or []) and not e.get("busy")] or [e for e in mine if not e.get("busy")] or mine

    # 「这张图能不能承载这种版式」——由库里的 use.layouts 声明（人工定，量不出来：
    # centre_std 只反映中心纹理，边角装饰完全量不到 —— papercut/hongzhi 中心 std 只有 0.0059，
    # 但红边极抢，放真图版就废）。没写 use 的旧库一律视为「哪种都行」，行为与 3.3.0 一致。
    def admits(e: dict, layout_cls: str) -> bool:
        use = e.get("use") or {}
        ls = use.get("layouts")
        return (not ls) or (layout_cls in ls)

    # 题材：story.json 的 topic（经 compose 写进 shots.json）。
    # 写了就优先挑 use.fits 命中该题材的纸——这是「按内容选纸」的唯一入口，
    # 不写则完全按版式 + 角色轮换（与 3.3.0 一致）。
    want_topic = str(shots_doc.get("topic") or "").strip()

    def fits_topic(e: dict) -> bool:
        if not want_topic:
            return True
        return want_topic in ((e.get("use") or {}).get("fits") or [])

    # 空命中只报一次（全片一条，否则每镜一条会刷屏）。
    # 静默回落是选材最大的隐患：「选错纸」看起来「挺好看」，适配度就这么被磨没了。
    topic_state = {"warned": False}

    def note_topic_miss() -> None:
        if want_topic and not topic_state["warned"]:
            topic_state["warned"] = True
            problems.append(
                f"topic={want_topic!r} 在背景库里没有 use.fits 命中，已退回按版式 + 角色选纸。"
                f" 要么给背景库补这个题材的 fits，要么改掉 story 的 topic。"
            )

    def layout_class(r: dict) -> str:
        """这一镜**画面形态**属于哪一类（决定它需要什么样的纸）。

        版式优先于「是不是章节首镜」：一镜如果本身是手账页（要放真图版 + 大字 + 印章），
        就算它刚好开了一章，也不能按章节卡去挑花纸——实测 bug：S1 是 page 但因为是章节首镜，
        拿到了 cel/speedlines（全幅集中线）与 flat/chapter（带吉祥物），图版直接废掉。
        章节的「视觉重音」交给转场和章节卡去给，不靠牺牲这一镜的纸。
        """
        lay = str(r.get("layout") or "")
        if lay.startswith("page"):
            return "page"
        # 只有**纯字卡**才算章节卡。不能把「开了一章」当理由：一章的第一镜往往就是内容镜
        # （清单 / 流程），给它配章节卡那种花纸，画面会盖过内容（实测 cel 的 list 拿到 speedlines，
        # flat 的 flow 拿到带吉祥物的 chapter）。章节的视觉重音交给转场去给。
        if lay.startswith(("statement", "define", "quiz")):
            return "chapter"
        return "component"

    def file_of(e: dict) -> str:
        f = str(e["file"])
        return f[len("public/"):] if f.startswith("public/") else f

    for i, r in enumerate(out):
        bg = r.get("bg")
        choice = None
        # P2-18：选材要能解释。以前只能看结果（bg=journal/ruled），看不出「为什么不是另一张」。
        # why 是一句人话，写进 shots.json 的 bgWhy，`--explain` 逐镜打印。
        why = ""
        if bg is not None:
            if bg in BG_ROLES:
                choice = every.get(f"{theme}/{bg}")       # legacy 那张；库里没有就交给引擎按变体名画
            else:
                bid = bg if "/" in bg else f"{theme}/{bg}"
                e = every.get(bid)
                if e is None:
                    names = ", ".join(sorted(x["id"].split("/", 1)[1] for x in mine)) or "（本皮肤没有库背景）"
                    problems.append(f"{r['id']}: bg={bg!r} 不在背景库；{theme} 皮肤可选：{names}")
                elif e.get("skin") != theme:
                    problems.append(f"{r['id']}: bg={bg!r} 属于 {e.get('skin')} 皮肤，当前皮肤是 {theme}")
                else:
                    # 显式指定照用（用户说了算），但**不适合这一镜**时必须出声：
                    # use.layouts 是「这张纸承载得了什么画面」的契约，绕过去不提示，
                    # 就会重演「图版页拿到全幅集中线」而没人知道为什么。
                    lcls = layout_class(r)
                    ls = (e.get("use") or {}).get("layouts") or []
                    if ls and lcls not in ls:
                        problems.append(
                            f"{r['id']}: 显式 bg={bg!r} 按库里的 use.layouts 适合 {ls}，而这一镜是 {lcls} 类；"
                            f"仍按你的指定使用。若画面被背景压住，换纸或删掉 bg 让引擎自动选。"
                        )
                    choice = e
                    why = f"explicit · story 里写了 bg={bg!r}" + ("（与这一镜的版式不匹配，已提示）" if ls and lcls not in ls else "")
        elif rotate and mode in ("chapter", "film"):
            if sheet is None or (mode == "chapter" and r["id"] in chapters):
                prev_sheet = file_of(sheet) if sheet is not None else None
                # 章节模式下一张纸要撑满整章（含图版页），所以**必须**是能承载 page 的那几张。
                # 早先还要求「page 与 component 都认」，结果每族只剩 1–2 张可选，
                # 整本书从头到尾一张纸（实测 journal/archive 八镜全是同一张），比换纸更难看。
                paper = [e for e in calm if admits(e, "page")] or calm
                # 有题材时先取「题材 + 版式」都认的那几张；取空了就退回只按版式。
                by_topic = [e for e in paper if fits_topic(e)]
                if not by_topic:
                    note_topic_miss()
                paper = by_topic or paper
                fresh = [e for e in paper if file_of(e) != prev_sheet] or paper
                sheet = min(fresh, key=lambda e: (last_used.get(e["id"], -1), hashlib.sha1(f"{seed}:{i}:{e['id']}".encode()).hexdigest()))
                why = (f"{mode} 模式 · 章节首镜换纸：{len(paper)} 张能承载 page 的纸里选最久没用过的"
                       + (f"，且契合 topic={want_topic}" if want_topic and by_topic else ""))
            else:
                why = f"{mode} 模式 · 沿用本章已定的一张（媒介连续性）"
            choice = sheet
            r["bgAuto"] = True
        elif rotate:
            lcls = layout_class(r)
            # 角色（chapter / quiet / main）只在已定版式之后再细分：
            # page 镜永远按 main/quiet 挑「干净纸」，不会被章节首镜的身份拖去挑花纸。
            role = "chapter" if lcls == "chapter" else ("quiet" if (r.get("zones") or 0) >= 4 else "main")
            lcls = layout_class(r)
            # 先按「这种版式承载得了」筛，再按题材优选，筛空了逐级退回——
            # 宁可退回，也不能让某一镜没有背景。
            by_role = [e for e in mine if role in (e.get("roles") or []) and not (role == "main" and e.get("busy"))]
            base = [e for e in by_role if admits(e, lcls)] or [e for e in mine if admits(e, lcls)] or by_role or mine
            cands = [e for e in base if fits_topic(e)]
            if not cands:
                note_topic_miss()
            cands = cands or base
            fresh = [e for e in cands if file_of(e) != prev_file] or cands
            choice = min(fresh, key=lambda e: (last_used.get(e["id"], -1), hashlib.sha1(f"{seed}:{i}:{e['id']}".encode()).hexdigest()))
            r["bgLayout"] = lcls
            r["bgAuto"] = True
            last = last_used.get(choice["id"])
            why = (f"auto · role={role} layout={lcls} · {len(cands)} 张候选"
                   + (f"（题材 {want_topic} 命中 {len([e for e in base if fits_topic(e)])} 张）" if want_topic else "")
                   + (f"，最久没用过（上次 S{last + 1}）" if last is not None else "，从没用过优先")
                   + (f"；已避开上一镜的 {prev_file}" if prev_file and file_of(choice) != prev_file else ""))
        if choice is not None:
            r["bg"] = choice["id"]
            r["bgFile"] = file_of(choice)
            if why:
                r["bgWhy"] = why
            last_used[choice["id"]] = i
            prev_file = r["bgFile"]
        else:
            prev_file = None


def resolve(project: Path) -> tuple[str, list[dict], list[str]]:
    shots_doc = json.loads((project / "manifests" / "shots.json").read_text(encoding="utf-8"))
    cues_doc = json.loads((project / "manifests" / "caption-cues.json").read_text(encoding="utf-8"))
    cues = cues_doc["cues"]
    shots = shots_doc.get("shots", [])
    problems: list[str] = []
    # 皮肤的**唯一真源**是 active.ts（渲染端 import 的就是它）。
    # shots.json 的 theme 只当声明，两者不一致时**按 active.ts 走**——注意这不是错误：
    # 下面所有下游（背景库、resolved 的 theme、storyboard）都用这个 theme，不会渲出
    # 「A 皮肤的组件 + B 皮肤的纸」。所以只在 main() 里打一行提示，不进 problems（不阻断构建）。
    # 早先把它当错误，结果测试夹具与旧工程（两者本来就不同步）全被判失败：
    # 门禁应该抓「真正会出错的事」，不能抓「两个键写法不同但结果正确」。
    declared = shots_doc.get("theme")
    actual = _active_skin(project, None)
    theme = actual or declared or "cel"
    shots_doc["theme"] = theme
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
            # 缺省 auto（章节首镜 zoom 推穿、其余 whip 甩镜）；cut/reveal 是旧写法，引擎按 auto 处理，hard = 真硬切
            "transition": s.get("transition", "auto"),
            # v3.0.1：由分镜表推导，场景层不再手写这个布尔（消除"表说 cut、代码写 reveal"的不一致）
            "reveal": s.get("transition", "auto") == "reveal",
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
            # ---- 讲法字段（2026-09-21 补：以前这四项**在这一步被整组丢掉**）----
            # 后果：shots.resolved.json 与 src/shots.ts 里都没有 move/evidence/hold/misconception，
            # 于是「讲法规范要求必填」这件事**下游根本看不见**，任何门禁都查不到（实测删掉也不报错）。
            # 现在原样透传：resolved 与 TS 两侧都能被门禁读到。
            "move": s.get("move"),
            "evidence": s.get("evidence"),
            "hold": s.get("hold"),
            "misconception": s.get("misconception"),
            "noMisconception": s.get("noMisconception"),
            "why": s.get("why"),
        }
        # 可选的背景覆盖：main / chapter / quiet（3.3.0 起的三张锁定图），或背景库里的一张（3.3.0：
        # 'journal/ruled' 或简写 'ruled'）。合法性与库背景的文件路径在 assign_backgrounds() 里统一解析。
        # 不写就不出这个键；没有 manifests/backgrounds.json 的旧工程解析结果逐字节不变。
        if s.get("bg") is not None:
            if not isinstance(s["bg"], str) or not s["bg"].strip():
                problems.append(f"{sid}: bg 必须是字符串（main / chapter / quiet 或背景库 id）")
            else:
                rec["bg"] = s["bg"].strip()
        # 音效覆盖（见 src/sfx.ts）。不写就不出键，旧分镜表解析结果逐字节不变。
        if s.get("sfx") is not None:
            sfx = s["sfx"]
            # 3.8.0 瘦身：16 → 9。删掉 whoosh / click / typing / riser / snip / latch / rustle，
            # 理由见 src/sfx.ts 顶部注释；旧分镜表若写了这些名字，这里会明确报错而不是出无声。
            events = {"pop", "success", "error", "chart", "highlight", "chapter", "page", "place", "stamp"}
            if sfx != "none" and not (isinstance(sfx, list) and all(isinstance(o, dict) and o.get("event") in events and ("beat" in o or "at" in o) for o in sfx)):
                problems.append(f"{sid}: sfx 必须是 \"none\" 或 [{{event, beat|at, vol?}}]，event ∈ {sorted(events)}")
            else:
                rec["sfx"] = sfx
        # 可选版式名（validate-composition 要求相邻两镜不同）。不写就不出键。
        if s.get("layout") is not None:
            rec["layout"] = str(s["layout"])
        # 3.3.0 插入镜标记：{"of": "S3"} = 这一镜是对 S3 某处的硬切特写（场景按特写尺寸重新排版，不靠放大）。
        # 门禁据此认景别（validate-treatment 的「特写」、validate-composition 的 >12s 构图）。不写就不出键。
        if s.get("insert") is not None:
            ins = s["insert"]
            if not (isinstance(ins, dict) and isinstance(ins.get("of"), str) and ins["of"].strip()):
                problems.append(f"{sid}: insert 必须是 {{\"of\": \"<镜头 id>\"}}（这一镜是对哪一镜的特写）")
            else:
                rec["insert"] = {"of": ins["of"].strip()}
        if s.get("sfxEvents") is not None:
            rec["sfxEvents"] = s["sfxEvents"]
        if s.get("sfxAuto") is not None:
            rec["sfxAuto"] = bool(s["sfxAuto"])
        # 引擎摄影机（src/cinema.tsx）。不写 cinema 也会输出缺省 {drift:'auto'}，引擎照样慢推/漂移。
        rec["cinema"] = resolve_cinema(s, sid, frm, duration, cues, problems)
        out.append(rec)
        cursor = to
    assign_backgrounds(project, shots_doc, out, problems)
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
        f"export const SFX_DENSITY = {js(sfx_density(shots_doc, problems))} as const;",
        "",
        "export const SHOTS = {",
    ]
    body = []
    for r in out:
        body.append(f"  {ts_key(r['id'])}: {js(r)},")
    tail_lines = ["} as const;", "", "export type ShotId = keyof typeof SHOTS;", "", f"export const SHOT_IDS = {js([r['id'] for r in out])} as const;", ""]
    return "\n".join(head + body + tail_lines), out, problems


# ---- 3.3.0：storyboard.md 由实际镜头表生成（独立评审拿到的必须是这部片自己的镜头表）----
STORYBOARD_MARK = "AUTO-GENERATED by resolve-shots"
# 3.3.0 及以前模板自带的手写示例（new-project 原样拷进每个工程）：认得它，照样覆盖
TEMPLATE_STORYBOARD_HEAD = "# 时间码分镜：GitHub 开源三部曲 EP0（官方模板示例片）"
FRAMING_SHORT = {"全": "最松 ≤1.05", "中": "最松 ≤1.20", "近": "峰值 ≥1.20", "特写": "峰值 ≥1.35", "插入": "插入镜"}


def _active_skin(project: Path, fallback: str | None = None) -> str | None:
    """从 src/theme/active.ts 读实际渲染用的皮肤。读不到返回 fallback。

    为什么需要读它：皮肤的**真源**是 active.ts（渲染端 import 的是它），
    而背景库按 shots.json 的 `theme` 挑图。这两处一旦不一致，出来的片就是
    「flat 的组件 + journal 的纸」这种最坏组合，而且**没有任何门禁看得见**
    （实测：2026-10-31 想跨皮肤对照，只改了 active.ts，五族渲出来全是点阵纸）。
    所以这里统一由 active.ts 定皮肤，shots.json 的 theme 只当声明与兜底。
    """
    a = project / "src" / "theme" / "active.ts"
    m = re.search(r"from\s+'\./(\w+)'", a.read_text(encoding="utf-8")) if a.is_file() else None
    return m.group(1) if m else fallback


def _cell(v) -> str:
    return str(v).replace("|", "／").replace("\n", " ").strip() or "—"


def storyboard_text(project: Path, shots_doc: dict, out: list[dict], cues: list[dict]) -> str:
    """镜头表 → Markdown。纯函数（同输入同输出），只读 shots.resolved 的同一份数据 + treatment.json 的意图。"""
    treat = {}
    tp = project / "manifests" / "treatment.json"
    if tp.is_file():
        try:
            treat = json.loads(tp.read_text(encoding="utf-8"))
        except ValueError:
            treat = {}
    tshots = {t.get("id"): t for t in (treat.get("shots") or []) if isinstance(t, dict)}
    sig = str(treat.get("signature_shot") or "")
    sig_id = (re.match(r"\s*([A-Za-z]+\d+[A-Za-z]?)", sig) or [None, None])[1]
    title = treat.get("topic") or shots_doc.get("title") or project.name
    total = out[-1]["to"] if out else 0
    skin = _active_skin(project, shots_doc.get("theme", "cel"))
    lines = [
        f"<!-- {STORYBOARD_MARK} · 由 resolve-shots 自动生成，手改会被覆盖（改 manifests/shots.json / treatment.json 后重跑 resolve-shots） -->",
        f"# 分镜 · {title}",
        "",
        f"- 总帧数 {total} · 时长 {total / FPS:.1f} 秒 · {FPS} fps · 皮肤 {skin} · {len(out)} 镜",
        "- 意图 = treatment.json 写的景别 / 运镜（没写 treatment 时为镜头表声明的运镜默认值）；实际 = 镜头表展开后的摄影机缩放（起→止，括号里是峰值，含 cinema.focus 推近）。",
        "",
        "| 镜 | 起–止 (s) | 景别 | 运镜 | 意图缩放 | 实际缩放 | 转场 | 背景 | 主要组件 | 字幕摘要 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    # 老工程显式写了非翻页转场：照用（尊重显式声明），但在分镜表里点一句怎么对齐新缺省。
    # 只写进 storyboard，不进 problems——这是迁移提示，不是缺陷。
    legacy = [r["id"] for r in out if r.get("transition") in ("fade", "zoom", "whip", "whip-left", "whip-right")]
    if legacy:
        lines.append(f"- ⚠ {len(legacy)} 镜显式写了非翻页转场（{', '.join(legacy[:8])}）。缺省已是翻页：要统一语言，删掉这些 transition 字段（或不写、写 auto）即可。")
    for r in out:
        t = tshots.get(r["id"], {})
        ks = [float(k["s"]) for k in (r.get("keys") or []) if isinstance(k.get("s"), (int, float))] or [1.0]
        focus = [f for f in ((r.get("cinema") or {}).get("focus") or []) if not f.get("settle")]
        fz = max([float(f.get("zoom") or 1.0) for f in focus] + [1.0])
        peak = max(ks) * fz
        actual = f"{ks[0]:.2f}→{ks[-1]:.2f}" + (f"（峰 {peak:.2f}）" if abs(peak - max(ks[0], ks[-1])) > 0.005 else "")
        move = t.get("move") or r.get("cameraIntent") or "still"
        framing = t.get("framing")
        if framing:
            intent = f"{framing}：{FRAMING_SHORT.get(framing, '—')}"
        else:
            intent = f"{r.get('cameraIntent', 'still')} 默认 {ks[0]:.2f}→{DEFAULT_TO.get(r.get('cameraIntent'), ks[-1]):.2f}"
        if sig_id == r["id"]:
            intent += "；招牌镜头 推≥12%"
        comps = list(r.get("live") or []) or list(r.get("media") or [])
        a, b = r.get("cueFirst", 0), r.get("cueLast", 0)
        cap = " / ".join(str(cues[i].get("text", "")) for i in range(a, b + 1) if 0 <= i < len(cues))
        cap = cap if len(cap) <= 28 else cap[:27] + "…"
        lines.append("| " + " | ".join(_cell(x) for x in (
            r["id"], f"{r['from'] / FPS:.2f}–{r['to'] / FPS:.2f}", framing or "—", move, intent, actual,
            r.get("transition", "auto"), r.get("bg") or "（引擎默认）", " · ".join(comps[:3]), cap)) + " |")
    return "\n".join(lines) + "\n"


def write_storyboard(project: Path, text: str) -> Path:
    """有自动生成标记（或是旧模板自带的示例）→ 覆盖 storyboard.md；用户手写的 → 写 storyboard.generated.md 并提示。"""
    target = project / "storyboard.md"
    if target.is_file():
        head = target.read_text(encoding="utf-8")[:400]
        if STORYBOARD_MARK not in head and not head.startswith(TEMPLATE_STORYBOARD_HEAD):
            target = project / "storyboard.generated.md"
            print("  ! storyboard.md 是手写的（没有自动生成标记），不覆盖；镜头表生成的分镜写到 storyboard.generated.md。"
                  "评审要用和镜头表一致的那份：确认后删掉手写版或改名即可。", file=sys.stderr)
    with io.open(target, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return target


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--explain", action="store_true",
                    help="逐镜打印「为什么选这张背景/纸」（P2-18）：角色、版式、候选数、轮换与题材")
    args = ap.parse_args()
    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"项目目录不存在：{project}", file=sys.stderr)
        return 2
    text, out, problems = resolve(project)
    # 皮肤两处不同步时只提示，不阻断：下游已全部按 active.ts 走（见 resolve() 里的说明）。
    _sj = json.loads((project / "manifests" / "shots.json").read_text(encoding="utf-8"))
    _decl, _act = _sj.get("theme"), _active_skin(project, None)
    if _decl is not None and _act and _decl != _act:
        print(f"  · 提示：shots.json theme={_decl!r} 与 active.ts={_act!r} 不同步，"
              f"本次按 active.ts 走；要消掉这条请跑 set-skin.py {project.name} {_act}")
    for r in out:
        print(f"  {r['id']:>6} {r['from']:>5}–{r['to']:<5} {r['duration']:>5}f  {r['skeleton']:<8} {r['chapter']}")
        if args.explain:
            bg = r.get("bg") or "（引擎按变体名画）"
            print(f"         纸 {bg:<22} {r.get('bgWhy') or '无背景库 / 未轮换'}")
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
    # 这里必须用 active.ts 的皮肤，不能重读 shots.json：上面 resolve() 只改了内存里的
    # shots_doc["theme"]，文件里可能还是旧值，重读会把「皮肤的纸」写错进 resolved。
    theme_id = _active_skin(project, json.loads((project / "manifests" / "shots.json").read_text(encoding="utf-8")).get("theme", "cel"))
    resolved = {"duration": out[-1]["to"] if out else 0, "theme": theme_id, "shots": out}
    shots_doc = json.loads((project / "manifests" / "shots.json").read_text(encoding="utf-8"))
    resolved["sfxDensity"] = sfx_density(shots_doc, problems)
    if (project / "manifests" / "backgrounds.json").is_file():
        # 3.3.0：告诉 validate-backgrounds 本片按什么粒度换背景（没有背景库的旧工程不出这个键，输出逐字节不变）
        resolved["bgMode"] = bg_mode(shots_doc) if shots_doc.get("bgRotate", True) is not False else "off"
    with io.open(project / "manifests" / "shots.resolved.json", "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(resolved, ensure_ascii=False, indent=2))
    cues = json.loads((project / "manifests" / "caption-cues.json").read_text(encoding="utf-8"))["cues"]
    sb = write_storyboard(project, storyboard_text(project, shots_doc, out, cues))
    print(f"已写出 {target}、manifests/shots.resolved.json 与 {sb.name}（{len(out)} 镜，共 {out[-1]['to'] if out else 0} 帧）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
