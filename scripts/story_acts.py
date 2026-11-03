#!/usr/bin/env python3
"""story_acts.py — compose-story 的「动作怎么落到帧」与「复现算不算重复」（P2-24 第三切片）

从 `compose-story.py` 切出的第四块（前三块：`story_camera.py` / `story_text.py` / `story_caption.py`）。
切它的直接原因是版式层：`lay_page` 要调 `resolve_ink_acts` 与 `check_draw`。若这层还留在主文件，
把 `lay_*` 切出去时就会形成「版式 import 主文件、主文件 import 版式」的环。

边界：
  - **在这里**：`@L1` / `@L1.3` 怎么换算成本镜帧号（`resolve_act_at`）、墨图与速写两套动词表、
    `content.ink.acts` 的校验（`resolve_ink_acts`）、跨镜复现的指纹与判定（P2-19）、
    线稿规格的构建期核对（P1-09，`check_draw` / `resolve_sketch`）、标注层的矩形与起始帧。
  - **不在这里**：元素怎么摆（`lay_*`）、旁白与字幕（`story_caption`）、时间轴怎么串（`build`）。
  - **共享底座**：帧号换算只走 `story_time.frame`；不在这里定义 FPS。
  - 依赖收集器只看 `p.err / p.fix / p.hint`，不需要 `Problems` 类本身。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import linework_index  # noqa: E402  （必须在 sys.path 之后导入）
from story_time import frame  # noqa: E402


# ---------- 3.5.1 出现排程（references/reveal-rules.md 规则 ③）----------
REVEAL_GAP = 12          # 同一镜里相邻两次「开始出现」至少隔 12 帧
REVEAL_CONC = 2          # 同一时刻最多 2 个东西在长
SKETCH_ENTER_SCHED = 45  # 线稿描出时长按上限 45 帧排（sketch.tsx 实际 clamp(12×部位数, 24, 45)）
ACT_DUR = 12             # 线稿 point / swap / mark / count
ANNOT_DUR = {"circle": 14, "underline": 12, "arrow": 12, "note": 24}


def grow_dur(e: dict) -> int:
    """文字 / 卡片沿阅读方向展开的帧数：clamp(字数 × 4, 12, 45)；没字的按宽度 /40。与 auto.tsx growDur 同一公式。"""
    n = len("".join(e.get("lines") or []) or str(e.get("text") or ""))
    return max(12, min(45, n * 4 if n > 0 else round(e["w"] / 40)))


def schedule_reveals(els: list, sk_out, ann_out: list, tips: list) -> None:
    """把一镜里所有「开始出现」事件排开：间隔 ≥ REVEAL_GAP，同时在长 ≤ REVEAL_CONC。只会往后推，不会提前。"""
    ev = []  # (期望帧, 类别序, 时长, 写回对象)
    if sk_out:
        for fr in sk_out.get("frames", []):
            if fr["do"] == "enter":
                ev.append((fr["at"], 0, SKETCH_ENTER_SCHED, fr))
            elif fr["do"] in ("point", "swap", "mark", "count"):
                ev.append((fr["at"], 2, ACT_DUR, fr))
    for e in els:
        e["dur"] = int(e.get("revealDur") or 0) or grow_dur(e)
        ev.append((e["at"], 1, e["dur"], e))
    for a in ann_out:
        ev.append((a["at"], 3, ANNOT_DUR.get(a["kind"], 12), a))
    for t in tips:
        ev.append((t["at"], 4, 10, t))
    ev.sort(key=lambda x: (x[0], x[1]))
    placed = []
    for want, cls, du, obj in ev:
        if cls == 3:  # 标注：等它圈的那个元素长完 +2 帧
            tgt = next((x for x in els if x["x"] == obj["x"] and x["y"] == obj["y"]), None)
            if tgt:
                want = max(want, tgt["at"] + tgt["dur"] + 2)
        s = int(want)
        if placed:
            s = max(s, max(a for a, _ in placed) + REVEAL_GAP)
            ends = sorted(a + d for a, d in placed)
            if len(ends) >= REVEAL_CONC:
                s = max(s, ends[-REVEAL_CONC])  # 第 REVEAL_CONC 晚结束的那个长完，才能再开始
        placed.append((s, du))
        shift = s - obj["at"]
        obj["at"] = s
        if cls == 4:
            obj["until"] = obj["until"] + shift
        if cls == 1 and obj.get("revealAt") is not None:
            obj["revealAt"] = obj["revealAt"] + shift


def resolve_act_at(at, line_start, line_cues, cues, frm):
    """把 act 的 at 解析成本镜帧号。

    支持：数字（本镜帧）/ "@L1"（第 1 句开始）/ "@L1.3"（第 1 句第 3 个字音开始）。
    解析不了返回 None（调用方报 P1，不猜）。
    """
    if isinstance(at, (int, float)):
        return int(at)
    m = re.match(r"^@L?(\d+)(?:\.(\d+))?$", str(at or "").strip())
    if not m:
        return None
    li = int(m.group(1)) - 1
    if not (0 <= li < len(line_start)):
        return None
    if not m.group(2):
        return int(line_start[li])
    wi = int(m.group(2)) - 1
    for ci in line_cues[li]:
        words = cues[ci]["words"]
        if 0 <= wi < len(words):
            return frame(words[wi]["start"]) - frm
        wi -= len(words)
    return int(line_start[li])


SKETCH_VERBS = ("enter", "point", "drop", "swap", "count", "mark", "exit")
# 页内墨图（content.ink）开放的动词。enter 由 content.ink.at 决定，count 会撞版面——
# 见 resolve_ink_acts 的说明。别再单开一套动词表：帧映射、target 校验都与 shot.sketch 共用。
INK_VERBS = ("point", "drop", "swap", "mark", "exit")


def resolve_ink_acts(p, sid, raw, line_start, line_cues, cues, frm, draw, dur, visible=None):
    """content.ink.acts：作者只写「第几句旁白做什么」，帧号在这里换算。

    为什么不在 lay_page 里做：@n 要等 cues 排完才有 line_start，而 lay_page 跑在那之前。
    为什么复用 resolve_act_at：页内墨图不是第二套动画系统——同一批动词、同一套时间写法、
    同一份 target 校验，才不会出现「sketch 能写 @L2，ink 只能手算帧」这种两套规矩。
    """
    if not raw:
        return []
    if not isinstance(raw, list):
        p.err(f"{sid}: content.ink.acts 要是数组（每项 {{'do': …, 'target': …, 'at': '@L2'}}）")
        return []
    if len(raw) > 3:
        p.hint(f"{sid}: content.ink.acts 有 {len(raw)} 个动作 —— 一镜 1–3 个就够；"
               f"动作要改变观众的理解，不是让画面一直在动")
    frames, targets = [], []
    for i, a in enumerate(raw):
        if not isinstance(a, dict):
            p.err(f"{sid}: content.ink.acts[{i}] 要是对象")
            continue
        verb = a.get("do")
        if verb in ("enter", "count"):
            p.err(f"{sid}: content.ink.acts[{i}].do={verb!r} 在页内墨图里不开放"
                  f"（入场用 content.ink.at；count 会把同一个形复制成 n 份，先单独评估版面）")
            continue
        if verb not in INK_VERBS:
            p.err(f"{sid}: content.ink.acts[{i}].do={verb!r} 不是 {' / '.join(INK_VERBS)} 之一")
            continue
        at = resolve_act_at(a.get("at"), line_start, line_cues, cues, frm)
        if at is None:
            p.hint(f"{sid}: content.ink.acts[{i}].at={a.get('at')!r} 解析不了 —— 用数字帧、@L1 或 @L1.3")
            continue
        target = a.get("target")
        if verb != "exit" and not target:
            p.err(f"{sid}: content.ink.acts[{i}] 是 {verb}，但没写 target（要点哪个部位）")
            continue
        if target:
            targets.append(target)
            if isinstance(visible, (list, tuple)) and target not in visible:
                p.err(f"{sid}: content.ink.acts[{i}].target={target!r} 不在 content.ink.parts 里"
                      f"（这一页只画 {' / '.join(str(v) for v in visible)}，动作指向看不见的部位等于没做）")
                continue
        frames.append({"at": max(0, min(dur - 1, at)), "do": verb,
                       "target": target, "mark": a.get("mark"), "text": a.get("text")})
    for msg in linework_index.check_targets(draw, targets):
        p.err(f"{sid}: content.ink {msg}")
    frames.sort(key=lambda x: x["at"])
    return frames


# ---------------------------------------------------------------- 有意复现 vs 无意重复（P2-19）
# 跨镜复现不该一律禁止：回忆、前后对照、结论回扣都需要再现同一个主题物。
# 但「同图 + 同局部 + 同动作」连续出现两次、又没声明意图，观众读到的就是「这段我看过」。
# 所以门禁只拦**无意**的完全重复；构图、动作、信息量三者至少一项有变化即放行。

def visual_fp(spec) -> tuple:
    """同一张图的同一个局部 → 同一指纹。parts 为空 = 整图。"""
    if not isinstance(spec, dict):
        return ()
    draw = str(spec.get("draw") or "")
    if not draw:
        return ()
    parts = tuple(sorted(str(x) for x in (spec.get("parts") or [])))
    return (draw, parts)


def action_fp(acts) -> tuple:
    """同一套动作（忽略时刻）→ 同一指纹。"""
    return tuple((str(a.get("do")), str(a.get("target") or "")) for a in (acts or []) if isinstance(a, dict))


def info_fp(spec) -> tuple:
    """信息量：这张图在说什么。"""
    if not isinstance(spec, dict):
        return ()
    return (str(spec.get("label") or ""), str(spec.get("big") or ""), str(spec.get("note") or ""))


def _shot_visuals(sh) -> list[tuple[str, tuple, tuple, tuple, dict]]:
    """一镜里所有可复现的画面（墨图 / 页内示意图 / 标本速写），带出处。"""
    out = []
    c = sh.get("content") or {}
    for where, spec in (("content.ink", c.get("ink")), ("content.figure", c.get("figure"))):
        fp = visual_fp(spec)
        if fp:
            out.append((where, fp, action_fp((spec or {}).get("acts")), info_fp(spec), spec if isinstance(spec, dict) else {}))
    sk = sh.get("sketch")
    fp = visual_fp(sk)
    if fp:
        out.append(("shot.sketch", fp, action_fp((sk or {}).get("acts")), info_fp(sk), sk if isinstance(sk, dict) else {}))
    return out


def check_reprises(p: "Problems", shots: list) -> None:
    """跨镜复现：无意完全重复拦下，有意复现（recallOf / variantOf）放行但仍要有一处变化。"""
    seen: dict[tuple, list[tuple[int, str, tuple, tuple]]] = {}   # 视觉指纹 → [(序号, sid, 动作, 信息)]
    # 先记全表：指向未来镜时要说「必须指向更早的」，不能说「不存在」
    order: dict[str, int] = {}
    for i, sh in enumerate(shots):
        order.setdefault(str(sh.get("sid") or f"S{i + 1}"), i)
    for i, sh in enumerate(shots):
        sid = sh.get("sid") or f"S{i + 1}"
        c = sh.get("content") or {}
        intent = (sh.get("recallOf") or sh.get("variantOf")
                  or c.get("recallOf") or c.get("variantOf"))
        intent_kind = ("recallOf" if (sh.get("recallOf") or c.get("recallOf"))
                       else ("variantOf" if (sh.get("variantOf") or c.get("variantOf")) else None))
        if intent:
            t = str(intent)
            if t not in order:
                p.err(f"{sid}: {intent_kind}={t!r} 指向的镜头不存在（可用：{' / '.join(list(order)[:12])}）")
            elif order[t] >= i:
                p.err(f"{sid}: {intent_kind}={t!r} 必须指向**更早**的镜头（复现是回看，不是预告）")
        for where, fp, afp, ifp, _spec in _shot_visuals(sh):
            if not fp:
                continue
            for j, p_sid, p_afp, p_ifp in seen.get(fp, []):
                same_act = afp == p_afp
                same_info = ifp == p_ifp
                consecutive = (j == i - 1)
                if not same_act:
                    continue  # 动作变了 = 信息量变了，本来就不是重复
                local = ("整图" if not fp[1] else "/".join(fp[1]))
                # 判定顺序：先看意图，再看是否连续 —— 有意复现不被「连续」误拦
                if intent and same_info:
                    # 标了意图但构图、动作、信息量全同 —— 那不是复现，是复制
                    p.err(f"{sid}: 标了 {intent_kind} 但与 {p_sid} 的构图、动作、信息量全同 —— "
                          f"复现也要有一处变化（换 acts 换演示、换 label 换说法；换 parts 则是另一个局部）")
                elif intent:
                    pass  # 有意 + 有变化 = 正解（回忆 / 前后对照 / 结论回扣）
                elif consecutive:
                    p.err(f"{sid}: 与上一镜 {p_sid} 同图同局部同动作（{where} 的 {fp[0]} / {local}）"
                          f"连续出现 —— 换一个局部（parts）、换一个动作，或写 recallOf=\u300a{p_sid}\u300b 表明这是有意回扣")
                elif same_info:
                    p.err(f"{sid}: 与 {p_sid} 同图同局部同动作同标签（{where}），但没声明意图 —— "
                          f"要么写 recallOf=\u300a{p_sid}\u300b / variantOf=\u300a{p_sid}\u300b（回忆、前后对照、结论回扣都算有意），"
                          f"要么改 parts / acts / label 之一")
                else:
                    p.hint(f"{sid}: 与 {p_sid} 同图同局部同动作但换了说法（label）—— "
                           f"若这是回忆 / 对照 / 回扣，写 recallOf=\u300a{p_sid}\u300b 或 variantOf=\u300a{p_sid}\u300b 更明确")
            seen.setdefault(fp, []).append((i, sid, afp, ifp))


def check_draw(p, sid, where, spec):
    """任何进画面的线稿规格都要在构建期核对（P1-09）。

    `content.ink` / `content.figure` 走的是 el(...) 直接进元素表，不经过 resolve_sketch；
    只查 shot.sketch 会漏掉这两条最常见的路径。
    """
    if not isinstance(spec, dict):
        return
    for msg in linework_index.check_selection(spec.get("draw"), spec.get("parts")):
        p.err(f"{sid}: {where} {msg}")


def resolve_sketch(p, sid, sk, line_start, line_cues, cues, frm):
    """校验 + 换算 sketch.acts；返回可直接进 story.ts 的对象。"""
    if not isinstance(sk, dict) or not sk.get("draw"):
        p.err(f"{sid}: sketch 需要 draw（lib:<名字> / shapes:[…]）")
        return None
    # 线稿名与部位名必须在**构建期**核对：名字错了引擎只会画空或画整图（P1-09），
    # 成片看起来「少了一张图」，却在渲染日志里只留一行 warn。
    problems = linework_index.check_selection(sk.get("draw"), sk.get("parts"))
    for msg in problems:
        p.err(f"{sid}: {msg}")
    if problems:
        return None
    frames = []
    if not (sk.get("acts") or []):
        sk = dict(sk, acts=[{"at": "@L1", "do": "enter"}])  # 3.5.1：acts 不写 = 第 1 句开始时描出（不再整镜静态出现）
    for i, a in enumerate(sk.get("acts") or []):
        verb = a.get("do")
        if verb not in SKETCH_VERBS:
            p.err(f"{sid}: sketch.acts[{i}].do={verb!r} 不是七个动词之一（{' / '.join(SKETCH_VERBS)}）")
            continue
        at = resolve_act_at(a.get("at"), line_start, line_cues, cues, frm)
        if at is None:
            p.hint(f"{sid}: sketch.acts[{i}].at={a.get('at')!r} 解析不了 —— 用数字帧、@L1 或 @L1.3")
            continue
        # 未用到的键直接省略，不写 None：story.ts 是按 StoryShot 类型检查的字面量，
        # `target?: string` 不接受 null（TS2322），而 `point` 拿到 "" 又会指向不存在的部位。
        frames.append({k: v for k, v in {"at": max(0, at), "do": verb, "target": a.get("target"),
                                         "n": a.get("n"), "mark": a.get("mark")}.items()
                       if v is not None})
    out = {k: v for k, v in sk.items() if k != "acts"}
    out["frames"] = frames
    return out


def resolve_annotate(p, sid, ann, els, line_start, line_cues=None, cues=None, frm=None):
    """annotate:[{target, kind, text, at}] → 带矩形与帧号的叠加层。"""
    out = []
    for i, a in enumerate(ann or []):
        kind = a.get("kind")
        if kind not in ("circle", "underline", "arrow", "note"):
            p.hint(f"{sid}: annotate[{i}].kind={kind!r} 不是 circle / underline / arrow / note 之一")
            continue
        target = a.get("target")
        e = next((x for x in els if x["id"] == target), None)
        if not e:
            p.hint(f"{sid}: annotate[{i}].target={target!r} 找不到画面元素 —— 写元素 id（可用：{', '.join(x['id'] for x in els[:8])}）")
            continue
        if a.get("at") is not None:
            at = resolve_act_at(a.get("at"), line_start, line_cues or [], cues or [], frm or 0)
            if at is None:
                p.hint(f"{sid}: annotate[{i}].at={a.get('at')!r} 解析不了 —— 用 @L1 或 @L1.3")
                continue
        else:
            li = int(a.get("line", 0))
            at = int(line_start[min(li, max(0, len(line_start) - 1))]) if line_start else 0
            if "line" in a:
                p.hint(f"{sid}: annotate[{i}].line 是 0 起数的旧写法 —— 改成 \"at\": \"@L{li + 1}\"（与 sketch.acts 同一写法）")
        out.append({"kind": kind, "x": e["x"], "y": e["y"], "w": e["w"], "h": e["h"], "at": at,
                    "text": a.get("text", ""), "seed": f"{sid}-{target}"})
    return out
