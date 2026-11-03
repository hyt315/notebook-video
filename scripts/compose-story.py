#!/usr/bin/env python3
"""compose-story.py · 3.2.0 内容表 → 可渲染工程（自动排版 + 自动修复 + 讲解规则）

弱模型只写 story.json（纯内容：章节 / 每镜版式 / 台词 / 版式内容），本脚本负责全部"质量"：

  1. 字幕   每行 ≤16 字，超了在标点 / 语义边界自动劈开（绝不劈开 {{术语}}、英文单词或数字）；
            无 TTS：按 4.5 字/秒自动排时间（逗号 +150 ms、句末 +300 ms），读不完就延长镜头；
            章节之间与镜间同样的间隔（3.2.0 去掉了章节卡 / 进度条）。
  2. 版式   10 种版式（statement / define / number / bars / compare / code / flow / list / quiz / custom）
            按设计坐标排好每个元素的矩形；三档字号（每镜 ≤3 种）；最小字号 32px（手机可读），
            放不下先换行、再降到地板、还不行才报错并说清楚要删到几个字。
  3. 关键词 台词里 {{术语}} 或 {{术语|元素id}} → 自动匹配画面元素：在念到这个词的那一帧高亮它、
            镜头推近取景它（不用写帧号）；术语表里的词第一次出现时自动弹出释义气泡。
  4. 镜头   每镜一条相机路径（cinema.path）：开头从上一镜最后的注视点接过来（视线连续），
            再拉到全景；每个关键词推近 → 停 → 回全景；速度有上限、同一时刻只有一个主运动；
            取景窗保证不切断任何标题 / 标签（不行就降低推近倍数或平移），永远保留微漂移（不冻结）。
  5. 音效   只挂在真事件上（元素出现、数字落定、图表生长、关键词第一次高亮、答案揭晓）。
  6. 门禁   每条规则先自动修，修不了才报错，错误信息写明怎么改。

用法：
    python scripts/compose-story.py STORY.json PROJECT_DIR [--report out.json]
产物（写进 PROJECT_DIR）：narration.txt、manifests/{caption-cues,shots,protected-caption-phrases}.json|txt、
audio/narration.mp3.json、src/{caption-cues.json,story.ts,film.ts,scenes.tsx}
退出码：0 通过（可含提示）/ 1 有修不了的问题 / 2 用法错误。零第三方依赖。
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import linework_index  # noqa: E402  （必须在 sys.path 之后导入）
import narration_contract  # noqa: E402
from story_camera import (  # noqa: E402  （必须在 sys.path 之后导入）
    SAFE, ZOOM_MAX, clamp_look, frame_rect, move_frames, partial_clips, to_screen, union,
)
from story_text import (  # noqa: E402  （必须在 sys.path 之后导入；文字层真源）
    MIN_FONT, PUNCT, SAFE_LH, TAIL_PUNCT_RE, cap_chars, fit_text, is_wide,
    line_len, safe_lh, text_w, units, wrap,
)
import story_caption as _cap  # noqa: E402  （字幕层真源；CPS / CHAR_MS 必须读它的当前值）
from story_caption import (  # noqa: E402
    COMMA_MS, MAX_CHARS, STOP_MS, legal_breaks, parse_line, setup_break_rule,
    split_caption, time_cue, tokens,
)
from story_time import FPS, frame  # noqa: E402  （帧率真源；时间轴与动作层共用）
from story_acts import (  # noqa: E402  （动作 / 复现层真源）
    INK_VERBS, SKETCH_VERBS, check_draw, check_reprises, resolve_act_at, resolve_annotate,
    resolve_ink_acts, resolve_sketch, schedule_reveals,
)
from story_layout import (  # noqa: E402  （版式层真源；下列名字是门面 re-export，外部别再从主文件找实现）
    BAND, FLOW_TOTAL_MAX, INK_BOX, LAY, PAGE_MEDIA, RECIPE_BOX, SKETCH_BOX, STORY_MEDIA, TYPE,
    check_content, clean_unit, el, lay_bars, lay_code, lay_compare, lay_custom, lay_define, lay_flow,
    lay_list, lay_media, lay_number, lay_page, lay_quiz, lay_recipe, lay_statement, lay_type,
)
from story_output import (  # noqa: E402  （写盘层真源）
    check_customs, js, registered_customs, write_media, write_narration_contract, write_project,
)

TREATMENT: dict = {}     # main() 读 manifests/treatment.json：signature_shot（招牌镜真推）+ shots[].move（运镜）
TREATMENT_MOVES: dict = {}   # 由 treatment.shots 展开：{镜号: move}，在 main() 里与 TREATMENT 一起填
LINE_GAP_MS = 220              # 同镜两行之间
SHOT_GAP_MS = 320              # 镜与镜之间
CHAPTER_BREATH_MS = SHOT_GAP_MS  # 不再有章节呼吸 / 章节卡（保持默认组件风格）
FIRST_LEAD_MS = 700            # 片头
END_TAIL_F = 42                # 片尾
# 字幕行宽 MAX_CHARS / 朗读速度 CPS / 标点停顿 / 术语语法 TERM_RE 的真源在 story_caption.py
# （P2-24 第二切片）。不可变的从那儿 import；可变的 CPS / CHAR_MS 一律读 story_caption.xxx，
# 不要在本地留副本——--cps 只改那边的真源。
ZOOM_MIN_FOCUS = 1.08          # 焦点推近的下限；SAFE / ZOOM_MAX 见 story_camera.py
LAYOUTS = ("statement", "define", "number", "bars", "compare", "code", "flow", "list", "quiz", "custom", "media", "page", "type")
# 每种版式可以贴的骨架标签（validate-composition 要求相邻不同）：首选在前
SKELETONS = {"statement": ["Stage", "Zoom"], "define": ["Split", "Stage"], "number": ["Stage", "Zoom"],
             "bars": ["Zoom", "Stage"], "compare": ["Split", "Stage"], "code": ["Zoom", "Stage"],
             "flow": ["Corridor", "Stage"], "list": ["Stage", "Corridor"], "quiz": ["Split", "Stage"], "custom": ["Stage", "Zoom"], "media": ["Zoom", "Stage"],
             "page": ["Stage", "Stage"], "type": ["Stage", "Stage"]}
MEDIA = {"statement": ["text"], "define": ["text"], "number": ["metric", "text"], "bars": ["chart", "metric"],
         "compare": ["metric", "text"], "code": ["code", "text"], "flow": ["graphic", "text"], "list": ["text"],
         "quiz": ["text", "graphic"], "custom": ["graphic", "text"], "media": ["graphic", "console"],
         "page": ["graphic", "text"], "type": ["text"]}
INTENTS = {"statement": "establish", "define": "push-in", "number": "push-in", "bars": "reveal", "compare": "pull-back",
           "code": "push-in", "flow": "reveal", "list": "establish", "quiz": "push-in", "custom": "reveal", "media": "push-in",
           "page": "establish", "type": "establish"}
ICON_BUDGET_SHOT, ICON_BUDGET_MIN = 1, 4

class Problems:
    def __init__(self):
        self.errors: list[str] = []
        self.fixes: list[str] = []
        self.hints: list[str] = []

    def err(self, m): self.errors.append(m)
    def fix(self, m): self.fixes.append(m)
    def hint(self, m): self.hints.append(m)


# ---------------------------------------------------------------- text metrics
# 文字层的实现搬到了 story_text.py（P2-24 第一切片）：字宽、折行、孤字调整、字号收敛、
# 行高地板都归它。这里只从那儿 import 并在模块级别名，既有调用点与 tests 的 `cs.wrap(...)`
# 全部保持可用；改折行规则时只动 story_text.py，不用在 2300 行里翻。
# 边界：split_caption 仍留在本文件（它要读 BudouX 规则，属于「字幕怎么切」而不是「字怎么排」）。


# ---------------------------------------------------------------- captions
# 字幕层搬到了 story_caption.py（P2-24 第二切片）：术语解析、>16 字怎么劈、断点来源、
# 每句时长、朗读速度都归它。这里只 import 回来，`cs.split_caption(...)` / `cs.time_cue(...)`
# 这类既有用法保持可用。
# 注意 CPS / CHAR_MS 是运行期可变的（--cps），**只能**经 story_caption.set_cps() 改，
# 本文件不再保留副本——否则 CLI 看着生效、字幕时长却没变。


# ---------------------------------------------------------------- linking
def match_element(term: str, target, els):
    if target:
        for e in els:
            if e["id"] == target:
                return e
        return None
    t = re.sub(r"\s+", "", term)
    best = None
    for e in els:
        if e["kind"] in ("arrow", "timer"):
            continue
        hay = " ".join([e["id"], str(e.get("text", "")), str(e.get("valueText", "")), str(e.get("title", ""))])
        if e["kind"] == "number":
            hay += f" {e['text']}{e.get('unit', '')}"
        hay = re.sub(r"\s+", "", hay)
        if t and t in hay:
            score = (0 if e["kind"] in ("codeline", "bar", "node", "item", "option", "number", "panel", "custom") else 1, len(hay))
            if best is None or score < best[0]:
                best = (score, e)
    return best[1] if best else None


def sub_rect(e, term):
    """statement / define 段落里的某个短语 → 它在折行后的矩形（逐字估宽）。"""
    lines = e.get("lines") or [e["text"]]
    size, lh = e["size"], e.get("lh", SAFE_LH)
    for li, line in enumerate(lines):
        k = line.find(term)
        if k < 0:
            continue
        lw = text_w(line, size)
        x0 = e["x"] + ((e["w"] - lw) / 2 if e.get("align") == "center" else 0)
        x = x0 + text_w(line[:k], size)
        return {"x": round(x, 1), "y": round(e["y"] + li * size * lh, 1), "w": round(text_w(term, size), 1), "h": round(size * lh, 1)}
    return None


# ---------------------------------------------------------------- camera
# 取景计算（to_screen / clamp_look / partial_clips / frame_rect / union / move_frames）
# 已切到 story_camera.py：纯函数组，单独可测。这里只保留调用。

# ---------------------------------------------------------------- main compose
def signature_shot_id(p: "Problems") -> str | None:
    """从 treatment.signature_shot 里取出镜号（"S4：…" / "招牌镜头 S4：…"）。

    treatment 与 story 是两份文件，作者写一处忘另一处是常态；取不到就返回 None，
    auto 排版照旧，不额外打扰（validate-treatment 自己会报）。
    """
    t = TREATMENT.get("signature_shot")
    if not t:
        return None
    m = re.search(r"\bS(\d+)\b", str(t))
    return f"S{m.group(1)}" if m else None


def sweep_track(els, base):
    """招牌镜的横移：找出同一行里并排放的元素，给出 (起幅 look, 落幅 look)。

    为什么需要它：一行 4 个节点并排的流程镜，在 16:9 里任何真推都会切断邻居的文字
    （安全框放不下「整行 + 一截」），但镜头沿这行扫过去既合法又有力——这正是
    treatment.move 里 pan-follow 的意思。返回 None = 这镜没有可横移的并排结构。

    起幅对准最左的元素、落幅对准最右的元素；两端都用 frame_rect 收口，
    保证「停住的时候」没有字被切断（运镜途中扫过是正常的，停留点不能切）。
    """
    cand = [e for e in els if e["kind"] not in ("arrow", "timer", "codebox", "title")
            and e.get("w", 0) > 0 and e.get("h", 0) > 0]
    if len(cand) < 2:
        return None
    # 按行分组：纵向中心相差不到半个元素高就算同一行
    rows: list[list[dict]] = []
    for e in sorted(cand, key=lambda e: e["y"]):
        cy = e["y"] + e["h"] / 2
        for row in rows:
            if abs((row[0]["y"] + row[0]["h"] / 2) - cy) < e["h"] * 0.6:
                row.append(e)
                break
        else:
            rows.append([e])
    rows = [r for r in rows if len(r) >= 2]
    if not rows:
        return None
    row = max(rows, key=lambda r: len(r))
    row.sort(key=lambda e: e["x"])
    first, last = row[0], row[-1]
    if last["x"] - first["x"] < 220:      # 挤在一起的两块，扫起来看不出位移
        return None
    # 起幅 / 落幅 = 对准最左 / 最右元素，倍率取「能扫出最大位移、且两端都不切字」的那个。
    # 为什么必须放大倍率才扫得动：s=1.01 时画面比设计稿只宽出 10px，clamp_look 把视点锁死在
    # 正中，位移恒为 0；倍率越大，视点才越能离开中心。但每档都要校验停留点不切字。
    scy = (SAFE[1] + SAFE[3]) / 2       # 安全框中心在 529，略高于画面中心（与 frame_rect 同源）
    best, best_span = None, 0.0
    s = max(1.0, base["s"])
    while s <= ZOOM_MAX + 1e-9:
        def aim(e, s=s):
            x, y = clamp_look(e["x"] + e["w"] / 2, e["y"] + e["h"] / 2 - (scy - 540) / s, s)
            return {"x": round(x, 1), "y": round(y, 1), "s": round(s, 3)}
        a, b = aim(first), aim(last)
        span = abs((b["x"] - a["x"]) * s)
        if span > best_span and not partial_clips((a["x"], a["y"]), a["s"], els) \
                and not partial_clips((b["x"], b["y"]), b["s"], els):
            best, best_span = (a, b), span
        s = round(s + 0.02, 3)
    if best is None or best_span < 300:    # 扫不开 = 观众看不出来，不如不扫
        return None
    return best


def compose(story: dict, p: Problems):
    sig_id = signature_shot_id(p)
    glossary = story.get("glossary") or {}
    STORY_MEDIA.clear()
    for m in story.get("media") or []:
        STORY_MEDIA[m.get("id")] = dict(m)
        if not m.get("width"):
            try:
                import subprocess as _sp
                src = Path(story.get("_dir", ".")) / m.get("file", "")
                r = _sp.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(src)], capture_output=True, text=True)
                w_, h_ = r.stdout.strip().split(",")[:2]
                STORY_MEDIA[m["id"]].update(width=int(w_), height=int(h_))
            except Exception:
                p.hint(f"media {m.get('id')}: 读不出尺寸（文件不存在或没装 ffprobe）—— 按 16:9 排版")
    # 3.5.1：保护短语自动收——主题物 + 线稿 / 墨图 / 页内示意图的 label 与 parts 值，只收台词原文里真出现的词（spec §5 E4）
    _said = "".join(parse_line(str(l_))[0] for ch_ in (story.get("chapters") or []) for s_ in (ch_.get("shots") or []) for l_ in (s_.get("lines") or []))
    _cand = [str(story.get("subject_of_film") or "")]
    for ch_ in story.get("chapters") or []:
        for s_ in ch_.get("shots") or []:
            for sk_ in (s_.get("sketch"), (s_.get("content") or {}).get("ink"), (s_.get("content") or {}).get("figure")):
                if isinstance(sk_, dict):
                    _pv = sk_.get("parts")
                    _cand += [str(sk_.get("label") or "")] + [str(v_) for v_ in (_pv.values() if isinstance(_pv, dict) else [])]
    auto_protect = [w_ for w_ in dict.fromkeys(_cand) if 2 <= len(w_) <= 8 and w_ in _said]
    protected = sorted(set(list(glossary.keys()) + list(story.get("protect") or []) + auto_protect), key=len, reverse=True)
    if not protected:
        p.hint("字幕保护短语为空（validate-semantic-breaks 会因此拦下）：在 story.json 顶层写 \"protect\": [\"……\"]（字幕里不能被切开的词，至少 1 个，必须原样出现在台词里），或在台词里用 {{术语}} 标出")
    chapters = story.get("chapters") or []
    if not chapters:
        p.err("story.json 需要 chapters:[{title, shots:[...]}]")
        return None
    shots, cues = [], []
    t_ms = FIRST_LEAD_MS
    sid_n = 0
    prev_layout = None
    prev_variant = None
    seen_terms = set()
    chapter_first = []
    for ci, ch in enumerate(chapters):
        if ci > 0:
            t_ms += CHAPTER_BREATH_MS
        for si, sh in enumerate(ch.get("shots") or []):
            sid_n += 1
            sid = sh.get("id") or f"S{sid_n}"
            lay = sh.get("layout")
            if lay not in LAYOUTS:
                p.err(f"{sid}: layout={lay!r} 不是 {LAYOUTS} 之一 —— 不确定就用 define / list / compare 这类组件版式（手账页用 page）")
                continue
            variant = sh.get("variant", "")
            # 自动修：相邻同版式 → 换镜像变体
            if lay == prev_layout and variant == prev_variant:
                alt = {"statement": "left", "number": "mirror", "define": "mirror"}.get(lay)
                if alt and variant != alt:
                    variant = alt
                    p.fix(f"{sid}: 与上一镜同版式 {lay}，自动换成变体 {alt}")
                else:
                    p.hint(f"{sid}: 与上一镜同为 {lay} 版式且没有可换的变体 —— 换一个组件版式（例如 list / compare / flow），或在两镜之间插一镜")
            content = sh.get("content") or {}
            recipe = sh.get("recipe")
            # 这四类配方自带版面，不跑原版式（原版式会要求 content.text 等必填项，弱模型会被无关报错挡住）
            if recipe in ("sketch-readout", "scene-verdict", "before-after", "hammer"):
                els = []
            elif check_content(p, sid, lay, content):
                els = LAY[lay](p, sid, content, variant)
            else:
                # 校验已报错（main 见 errors 就 return 1，不会写盘）；给一个占位元素，
                # 避免后面 build 对「空镜」做额外假设——把可读错误和生产崩溃分开。
                els = [el("text", "text", 240, 400, 480, 90, sid, TYPE["body"], "body", 0, lh=SAFE_LH)]
            sketch_box = SKETCH_BOX.get((sh.get("sketch") or {}).get("place") or "left") if sh.get("sketch") else None
            if recipe:
                r = lay_recipe(p, sid, recipe, content, variant)
                if r:
                    els, sketch_box = r
                elif recipe in RECIPE_BOX:
                    sketch_box = RECIPE_BOX[recipe]
                else:
                    if recipe == "photo-traced":
                        p.err(f"{sid}: recipe='photo-traced' 在 3.5.1 已移除（没有实现）——照片请用 layout: media，再用 annotate 圈出讲到的地方")
                        recipe = None
                        continue
                    p.hint(f"{sid}: recipe={recipe!r} 未知 —— 按组件路线走（有效：sketch-readout / component-annotated / scene-verdict / before-after / list-icons / data-with-object / hammer）")
                    recipe = None
            sk_raw = sh.get("sketch")
            if sk_raw and not sketch_box:
                sketch_box = SKETCH_BOX["left"]
            if lay not in ("custom", "bars", "statement", "type") and els:
                u = union(els)
                dy = BAND["y"] + (BAND["h"] - u["h"]) / 2 - u["y"]
                if abs(dy) > 8:
                    for e in els:
                        e["y"] = round(e["y"] + dy, 1)
            if ci > 0 and si == 0:
                pass
            shot_start_ms = t_ms - (CHAPTER_BREATH_MS if (ci > 0 and si == 0) else (SHOT_GAP_MS // 2 if sid_n > 1 else FIRST_LEAD_MS))
            if sid_n == 1:
                shot_start_ms = 0
            raw_lines = sh.get("lines") or []
            if not raw_lines:
                p.err(f"{sid}: lines 为空 —— 每镜至少一句台词")
                continue
            line_cues = []  # per authored line → list of cue indices
            terms_all = []
            think_after = None
            if lay == "quiz":
                think_after = 0
            for li, raw in enumerate(raw_lines):
                text, terms = parse_line(raw)
                parts = split_caption(text, terms, protected)
                if len(parts) > 1:
                    p.fix(f"{sid}: 第 {li + 1} 句 {line_len(text):g} 字 > {MAX_CHARS}，自动拆成 {len(parts)} 行：{' / '.join(TAIL_PUNCT_RE.sub('', a) for a, _ in parts)}")
                idxs = []
                for ptxt, pterms in parts:
                    words, end = time_cue(ptxt, t_ms)
                    cue = {"text": ptxt, "words": [{"part": w["part"], "start": w["start"], "end": w["end"]} for w in words],
                           "start_ms": int(t_ms), "speech_end_ms": end, "reveal_end_ms": end,
                           "start": round(t_ms / 1000, 3), "speech_end": round(end / 1000, 3), "reveal_end": round(end / 1000, 3)}
                    cues.append(cue)
                    idxs.append(len(cues) - 1)
                    for tm in pterms:
                        wi = max([i for i, w in enumerate(words) if w["char"] <= tm["start"]] or [0])
                        terms_all.append({**tm, "line": li, "ms": words[wi]["start"], "cue": len(cues) - 1})
                    t_ms = end + STOP_MS + LINE_GAP_MS
                line_cues.append(idxs)
                if think_after is not None and li == think_after:
                    t_ms += int(float(content.get("think", 3)) * 1000)
            t_ms += SHOT_GAP_MS - LINE_GAP_MS
            shots.append({"sid": sid, "layout": lay, "variant": variant, "chapter": ch.get("title", f"第{ci + 1}章"), "ci": ci,
                          "first_in_chapter": si == 0, "els": els, "line_cues": line_cues, "terms": terms_all, "content": content,
                          "start_ms": shot_start_ms, "icons": int(sh.get("icons", 0)), "custom": content.get("component"),
                          "role": sh.get("role") or ch.get("role"), "recipe": recipe, "sketch": sk_raw,
                          # 有意复现（P2-19）：recallOf=回扣先前那张图，variantOf=同一主题物的另一态。
                          # 两者都表示「这镜是故意再现的」，门禁据此放行；没有它们的同图同局部同动作才是无意重复。
                          "recallOf": sh.get("recallOf") or content.get("recallOf"),
                          "variantOf": sh.get("variantOf") or content.get("variantOf"),
                          "sketch_box": sketch_box, "annotate": sh.get("annotate") or content.get("annotate"),
                          "see": sh.get("see"),
                          "page": (content or {}).get("page") if lay == "page" else None,
                          "media": (content or {}).get("media") if lay == "page" else None,
                          "catalogue": (content or {}).get("catalogue") if lay == "page" else None,
                          "title": (content or {}).get("title") if lay == "page" else None,
                          "big": (content or {}).get("big") if lay == "page" else None,
                          "note": (content or {}).get("note") if lay == "page" else None})
            if si == 0:
                chapter_first.append(sid)
            prev_layout, prev_variant = lay, variant
    check_reprises(p, shots)
    total_ms = cues[-1]["speech_end_ms"] + END_TAIL_F * 1000 / FPS if cues else 0
    return {"shots": shots, "cues": cues, "total_ms": total_ms, "glossary": glossary, "protected": protected, "chapter_first": chapter_first}


def build(story, comp, p: Problems):
    sig_id = signature_shot_id(p)   # treatment 点名的招牌镜：这一镜真推（见下方相机路径）
    shots, cues = comp["shots"], comp["cues"]
    glossary = comp["glossary"]
    total = frame(comp["total_ms"])
    out_shots, story_ts = [], {}
    sk_seen = 0  # 3.5.1：已经排过的线稿镜头数，用来轮换 camera.intent（spec §5 E3）
    prev_gaze = None
    seen_gloss = set()
    used_skel = None
    minute_icons = 0
    # 叙事动作（validate-presentation 要求同一 move 不连续 ≥3 镜）：按蓝图角色 / 版式取，撞了就换近义动作
    ROLE_MOVE = {"hook": "引入", "pre": "定位", "breakdown": "拆分/合并", "example": "传递", "misconception": "反证", "recap": "收束"}
    LAY_MOVE = {"statement": "收束", "define": "定位", "number": "引入", "bars": "反证", "compare": "对比", "code": "定位",
                "flow": "拆分/合并", "list": "累积", "quiz": "反证", "custom": "传递", "media": "定位",
                "page": "定位", "type": "定位"}
    moves = []
    for k, sh in enumerate(shots):
        m = ROLE_MOVE.get(sh.get("role") or "", LAY_MOVE[sh["layout"]])
        if k == 0:
            m = "引入"
        elif k == len(shots) - 1:
            m = "收束"
        if len(moves) >= 2 and moves[-1] == moves[-2] == m:
            m = "推进" if m != "推进" else "累积"
        moves.append(m)
    for k, sh in enumerate(shots):
        sid = sh["sid"]
        frm = frame(sh["start_ms"])
        to = frame(shots[k + 1]["start_ms"]) if k + 1 < len(shots) else total
        dur = to - frm
        els = sh["els"]
        line_start = [frame(cues[ix[0]]["start_ms"]) - frm for ix in sh["line_cues"]]
        line_end = [frame(cues[ix[-1]]["speech_end_ms"]) - frm for ix in sh["line_cues"]]
        nl = len(line_start)
        # 页内墨图的动作：@n → 本镜帧号（要等 cues 排完，所以不在 lay_page 里做）
        for e in els:
            raw_acts = e.pop("inkActs", None)
            if raw_acts:
                e["frames"] = resolve_ink_acts(
                    p, sid, raw_acts, line_start, sh["line_cues"], cues, frm,
                    e.get("draw"), dur, e.get("parts") if isinstance(e.get("parts"), list) else None)
        # 元素出现帧：appear = 第几句；同句错峰 5 帧（≤8）
        per_line = {}
        for e in els:
            a = e["appear"]
            if isinstance(a, int) and a >= nl:
                a = nl - 1
            # 被关键词点名、且点名早于声明 → 不改；点名晚于出现 → 保持（先出现后强调）
            n = per_line.get(a, 0); per_line[a] = n + 1
            e["at"] = max(0, line_start[a]) + n * 12 if isinstance(a, int) else 0  # 3.5.1：不早于所属句；同句第 n 个再晚 12n 帧
            # 逐字呈现的节奏锁在旁白上：这一句有多少帧，就多少帧放完。
            # 不另配时间轴——否则旁白一快，字还没放完就被下一句盖掉。
            if e.get("reveal") in ("type", "slide"):
                _a = a if isinstance(a, int) else 0
                _a = max(0, min(_a, nl - 1))
                e["revealAt"] = e["at"] + 2
                e["revealDur"] = max(10, min(72, int(line_end[_a] - line_start[_a]) - 4))
        # afterBig：不占 appear 的「跟在大字后面」时序。
        # 手账页上「写完一行 → 落章」是两拍；若都用 appear=0，两拍会被压进同一帧，
        # 开场前 3 秒就只剩一个节拍（validate-opening O4 判 P0）。
        # 这里按大字真正写完的那一帧来盖：big 是 lettering，perChar=6，写完 ≈ at + 6*(n-1) + 10。
        for e in els:
            anchor_id = e.get("afterBig")
            if not anchor_id:
                continue
            host = next((x for x in els if x["id"] == anchor_id and x["kind"] == "lettering"), None)
            if host is None:
                continue
            nch = len(str(host.get("text") or ""))
            e["at"] = int(host["at"]) + max(10, 6 * (nch - 1)) + 10
            if e.get("afterBig"):
                del e["afterBig"]
        # markAppear：下划线要跟着旁白起笔，不能跟字的出现同一帧。
        # 纸上的强调是笔的动作——讲到那一句才划，划完就留着，不来回跳。
        for e in els:
            ia = e.pop("inkAt", None)
            if ia:
                e["at"] = max(int(e.get("at") or 0), int(ia))
        for e in els:
            ma = e.pop("markAppear", None)
            if ma is None:
                continue
            idx = int(ma) if isinstance(ma, int) else 1
            idx = max(0, min(idx, nl - 1))
            e["mark"] = int(line_start[idx]) + 8
        # flow / list 的并列项在自己的那一句里扎堆出现（一句字幕里塞 4 个节点，n 只摊开 15 帧），
        # 观众看到的是「一下全冒出来」——而流程镜的意义恰恰是一步一步走。
        #
        # 为什么不再按「字幕行」分组：一行只有 1 句字幕、却要放 4 个节点时（flow 的常态），
        # 按行分组会把 4 个节点全塞进这一句里，末尾那个只能贴到 dur-20 才出现——
        # 上一版成片里 step4「今天/住户」到 259/279 帧才冒头，箭头也就画不完（只剩一横杠）。
        # 并列项本来就是一个整体，应当跨整镜铺开：起点在首句字幕起后（第一项跟着标题走），
        # 终点在镜尾前留出 SETTLE 帧让最后一张被读得完。
        PEER_SETTLE = 40
        # 本镜「全部字幕句」的本地起帧（不是 story.json 的 lines 组——S4 写了 2 条 lines，
        # 旁白却读成 4 句；并列项要跟的是后者）。
        _cue_all = [ci_ for ix in sh["line_cues"] for ci_ in ix]
        cue_locals_peer = [frame(cues[ci_]["start_ms"]) - frm for ci_ in _cue_all]
        for group in ("node", "item"):
            peers = [e for e in els if e["kind"] == group]
            if len(peers) < 2:
                continue
            # 首项不能和标题同时冒头：标题 at=2 入场，首项至少晚 8 帧接力。
            t0 = max(0, line_start[0] - 8)
            if any(e["kind"] == "text" for e in els):
                t0 = max(t0, 10)
            # 排布策略，按「字幕句数 vs 并列项数」二分：
            #   (a) 句数 >= 项数：一项一句，跟着旁白走。这是**最好**的读法——说到「先是植物」
            #       时第二张纸正好贴上，声音和画面同一拍。S4 有 4 句字幕 4 个节点，属于这类。
            #   (b) 句数 <  项数：隔一句塞不下，就只能跨整镜均摊（旧逻辑），并留 SETTLE 帧收尾。
            # 早先一律走 (b)，结果 S4 的四个节点被均摊成 79 帧一格（2.6 秒一张），
            # 观众看到第 32 秒时画面里还只有三张，会误以为流程只有三步。
            #
            # 用 cue_list（**全部字幕句**）而不是 line_start（story.json 的 lines 组）：
            # story 里 S4 只写了 2 条 lines，但 TTS 把它读成了 4 句字幕；
            # 拿 2 去比 4 个节点会永远走 (b)，节点就永远跟不上旁白。
            n_cue = len(cue_locals_peer) if cue_locals_peer else len(line_start)
            if n_cue >= len(peers):
                for i, e in enumerate(peers):
                    # 第 i 项落到它该跟的那一句上（n_cue 句分给 n 项，最后一项跟最后一句）
                    j = round(i * (n_cue - 1) / max(1, len(peers) - 1))
                    e["at"] = int(max(t0, cue_locals_peer[j] - 2))
            else:
                # 终点不再贴近镜尾（dur - 40）：三张卡片摊到 141/181 帧，
                # 观众看到第 23 秒时画面里还是只有两张，最后一张只剩 1 秒可读。
                # 结构型版面（flow / list）要**先立起来再讲**，所以压到前 42%。
                t1 = max(t0 + 8 * len(peers), min(dur - PEER_SETTLE, dur * 0.42))
                step = (t1 - t0) / max(1, len(peers) - 1)
                for i, e in enumerate(peers):
                    e["at"] = int(round(t0 + i * step))
            if group == "node":
                # 箭头跟着它指向的那个节点出现：节点错峰铺开后，箭头留在原位就会先于节点冒出来
                for e in els:
                    if e["kind"] != "arrow":
                        continue
                    m = re.fullmatch(r"arrow(\d+)", e["id"])
                    if not m:
                        continue
                    target = next((x for x in peers if x["id"] == f"step{int(m.group(1)) + 1}"), None)
                    if target is not None:
                        # arrow{i} 画在 step{i-1} 和 step{i} 之间：跟着右侧那个节点一起画，
                        # 「上一格的箭头指向下一格，下一格同时出现」才是流程镜该有的读法。
                        e["at"] = max(0, target["at"] - 4)
        # 关键词 → 元素 / 子矩形
        focus = []
        for tm in sh["terms"]:
            tgt = match_element(tm["text"], tm["target"], els)
            rect = None
            if tgt is None:
                # 在段落里找短语
                for e in els:
                    if e["kind"] in ("text", "card", "note", "quote") and tm["text"] in (e.get("text") or ""):
                        rect = sub_rect(e, tm["text"])
                        if rect:
                            tgt = e
                            break
            if tgt is None:
                p.err(f"{sid}: 台词关键词 {{{{{tm['text']}}}}} 在画面上找不到对应元素 —— 让画面上出现这几个字，或写成 {{{{{tm['text']}|元素id}}}}（可用 id：{', '.join(e['id'] for e in els if e['kind'] not in ('arrow',))}）")
                continue
            if rect is None and sh["layout"] == "statement" and tgt["kind"] == "text":
                rect = sub_rect(tgt, re.sub(r"\s+", " ", tm["text"])) or sub_rect(tgt, tm["text"])
            if rect is None and tgt["kind"] in ("text", "card", "note", "quote") and len(re.sub(r"\s+", "", tm["text"])) < len(re.sub(r"\s+", "", tgt.get("text") or "")) - 1:
                rect = sub_rect(tgt, tm["text"])
            at = frame(tm["ms"]) - frm
            if tgt["at"] > at:
                tgt["at"] = max(0, at - 6)  # 关键词说到时元素必须已经在：提前出现
            focus.append({"id": tgt["id"], "at": at, "rect": rect or {k2: tgt[k2] for k2 in ("x", "y", "w", "h")}, "term": tm["text"],
                          "sub": bool(rect), "line": tm["line"]})
        focus.sort(key=lambda x: x["at"])
        # 一镜一概念 lint
        new_els = [e for e in els if e["kind"] not in ("arrow", "codeline", "timer")]
        if len(new_els) > 7 or len({f["id"] for f in focus}) > 4:
            p.hint(f"{sid}: 本镜新元素 {len(new_els)} 个 / 关键词目标 {len({f['id'] for f in focus})} 个 —— 一镜一个概念，建议在第 {max(1, nl // 2)} 句后拆成两镜")
        # 字号档位 ≤3（hero 数字算一档）
        sizes = sorted({int(e["size"]) for e in els if e.get("size") and e["kind"] not in ("arrow", "timer", "custom")})
        if len(sizes) > 3:
            p.hint(f"{sid}: 本镜用了 {len(sizes)} 种字号 {sizes}（目标 ≤3）")
        small = [e for e in els if e.get("size") and e["size"] < MIN_FONT and e["kind"] != "arrow"]
        for e in small:
            p.fix(f"{sid}.{e['id']}: 字号 {e['size']} < {MIN_FONT}，自动放大到 {MIN_FONT}")
            e["size"] = MIN_FONT
        # 焦点 ≤3：强调角色超过 3 个 → 降级
        acc = [e for e in els if e["role"] in ("hero", "accent", "display")]
        for e in acc[3:]:
            e["role"] = "body"
            p.fix(f"{sid}.{e['id']}: 同屏强调元素 >3，降为正文")
        # ---------- 相机路径 ----------
        content_els = list(els)
        # 空镜是合法状态（纯配方镜、或版式校验失败后的占位镜）：没有内容可取景时用整幅内容带，
        # 不能让 union([]) 抛 min() empty——那会把「作者写漏一个字段」变成「整片崩在栈里」。
        sk_box = sh.get("sketch_box") if sh.get("sketch") else None
        _u_els = content_els + ([{"x": sk_box["x"], "y": sk_box["y"], "w": sk_box["w"], "h": sk_box["h"]}] if sk_box else [])
        U = union(_u_els) if _u_els else dict(BAND)
        band_fill = (U["w"] * U["h"]) / (BAND["w"] * BAND["h"]) if content_els else 1.0
        over, _ = frame_rect(U, content_els, max_s=1.18 if band_fill < 0.6 else 1.06)
        path = []
        if prev_gaze is not None and focus:
            # 视线连续：本镜第一个出现的元素放在上一镜最后注视的屏幕位置附近，再滑到全景
            first = min(content_els, key=lambda e: e["at"])
            gx, gy = prev_gaze
            s0 = over["s"]
            look = clamp_look(first["x"] + first["w"] / 2 - (gx - 960) / s0, first["y"] + first["h"] / 2 - (gy - 540) / s0, s0)
            path.append({"at": 0, "x": round(look[0], 1), "y": round(look[1], 1), "s": s0})
            path.append({"at": 30, **over})
        else:
            path.append({"at": 0, **over})
        cur = {k_: path[-1][k_] for k_ in ("x", "y", "s")}  # 只带位置；不能带 at（{"at": t, **cur} 会被它覆盖）
        last_at = path[-1]["at"]
        focus_out = []
        for i, fk in enumerate(focus):
            # 同一元素连续点名 → 只推一次（保持）
            if focus_out and focus_out[-1]["id"] == fk["id"] and fk["at"] - focus_out[-1]["at"] < 90:
                focus_out[-1]["until"] = max(focus_out[-1]["until"], fk["at"] + 45)
                continue
            tgt, tries = frame_rect(fk["rect"] if not fk["sub"] else next(e for e in els if e["id"] == fk["id"]), els, max_s=ZOOM_MAX, min_s=1.0)
            if tgt["s"] < ZOOM_MIN_FOCUS:
                # 推不进去（会切到标题 / 标签）→ 只高亮、不推近
                tgt = None
            d = move_frames(cur, tgt) if tgt else 0
            start = max(last_at + 2, fk["at"] - int(d * 0.6))
            if tgt and start + d > dur - 6:
                tgt = None
            if tgt:
                path.append({"at": start, **cur}) if start > last_at + 2 else None
                path.append({"at": start + d, **tgt})
                cur = tgt; last_at = start + d
            nxt = focus[i + 1]["at"] if i + 1 < len(focus) else dur
            until = min(nxt - 4, fk["at"] + max(60, int(len(fk["term"]) * _cap.CHAR_MS * FPS / 1000) + 45), dur - 4)
            focus_out.append({"id": fk["id"], "at": fk["at"], "until": until, "term": fk["term"], "sub": fk["rect"] if fk["sub"] else None, "cam": bool(tgt)})
            # 回全景：下一焦点离得远（> 75 帧）才回，否则直接移到下一个
            if tgt and nxt - until > 75:
                back_d = move_frames(cur, over)
                path.append({"at": until, **cur})
                path.append({"at": until + back_d, **over})
                cur = over; last_at = until + back_d
        # 最后注视点（屏幕坐标）：推近中 → 画面中心；全景 → 最后强调元素的屏幕位置
        if focus_out:
            e = next(x for x in els if x["id"] == focus_out[-1]["id"])
            sx, sy, sw, sh_ = to_screen(e, (cur["x"], cur["y"]), cur["s"])
            prev_gaze = (sx + sw / 2, sy + sh_ / 2)
        else:
            prev_gaze = (960, 520)
        # 3.6.2 招牌镜：treatment.signature_shot 点名的那一镜，给一个「看得见的运镜」。
        # 为什么要有这条：auto 版式的运镜是统一 1.03 的呼吸推，一镜到底等于静帧；
        # 于是「写了招牌镜」和「版式做不到」互相打架——作者只能去改 treatment 逃避门禁。
        # 两条路，先试真推，推不进就横移：
        #   ① 真推：推最大的那个元素到 1.18 倍（有独占大主体的镜，如 page 的图版、单面板）；
        #   ② 横移：一行并排的元素（flow / list / compare）在 16:9 里推不得（推一点就切断邻居），
        #      但可以「镜头沿流程扫过去」——位移 300–1300px，这正是 treatment 里 pan-follow 的语义。
        if sig_id and sid == sig_id and not sh.get("sketch"):
            main = max((e for e in els if e["kind"] not in ("arrow", "timer", "codebox")),
                       key=lambda e: e["w"] * e["h"], default=None)
            tgt = None
            if main is not None:
                try:
                    # min_s 用门禁线（12%）而不是 1.18：一字排开的并列结构常常只放得下 1.15 左右，
                    # 死守 1.18 会让「本来能过门禁的镜」被判失败，白退到横移。
                    tgt, _ = frame_rect(main, els, max_s=1.24, min_s=1.12)
                except (ValueError, KeyError):
                    tgt = None
            if tgt and tgt["s"] >= 1.12:
                # 关键：起幅先回到「全景基准」。本镜的 anchor 推近往往已经 1.1 左右，
                # 从 1.1 再推到 1.15 观众只感到 4%，等于没推。招牌镜的演出应该是
                # 「先看全，再慢慢推近」——所以把全景放在开头，推近放在中段并保持到镜尾。
                wide = {"x": 960.0, "y": 540.0, "s": 1.0}
                land = max(20, int(dur * 0.55))
                start = max(2, land - move_frames(wide, tgt))
                if last_at <= 2 and start >= 6:
                    # 本镜前面还没有别的运镜：重置 path 为全景起幅，全程 1.0 到 start 再推
                    path = [{"at": 0, **wide}, {"at": start, **wide}]
                    cur = wide; last_at = 0
                else:
                    path.append({"at": max(last_at + 1, 1), **cur})
                    path.append({"at": start, **wide})
                    cur = wide
                path.append({"at": land, **tgt})
                cur = tgt; last_at = land
                p.fix(f"{sid}: 招牌镜 → 全景 1.00× 起，慢推到 {main['id']}（{tgt['s']:.2f}×）")
            else:
                sweep = sweep_track(els, over)
                if sweep:
                    a, b = sweep
                    d = move_frames(a, b)
                    start = max(last_at + 4, int(dur * 0.3))
                    if start + d < dur - 6:
                        path.append({"at": start, **cur}) if start > last_at + 2 else None
                        path.append({"at": start + d, **a})
                        path.append({"at": min(dur - 4, start + d + max(30, int(dur * 0.35))), **b})
                        cur = b; last_at = min(dur - 4, start + d + max(30, int(dur * 0.35)))
                        span = abs((b["x"] - a["x"]) * b["s"])
                        p.fix(f"{sid}: 招牌镜 → 推不进（会切邻居），改横移扫镜（{span:.0f}px）")
                    else:
                        p.hint(f"{sid}: treatment.signature_shot 点名了本镜，但本镜又推不进也横移不开——"
                               f"把招牌镜换成有并列元素或独占大主体的镜")
                else:
                    p.hint(f"{sid}: treatment.signature_shot 点名了本镜，但本镜只有一个静的主体——"
                           f"换成有并列元素（flow / list / compare）或有独占大主体的镜")
        # 结尾不留 >1.2 秒的「无新事件」：最后一个事件到镜尾太远 → 收束推近（慢推 3%）
        events = [e["at"] for e in els] + [f["at"] for f in focus_out] + line_end
        tail_gap = dur - max(events)
        if tail_gap > 36:
            path.append({"at": max(last_at + 1, dur - tail_gap + 6), **cur})
            path.append({"at": dur, "x": cur["x"], "y": cur["y"], "s": round(min(ZOOM_MAX, cur["s"] * 1.03), 3)})
            p.fix(f"{sid}: 结尾 {tail_gap} 帧无新事件 → 自动加收束慢推")
        # 释义气泡（术语第一次出现）
        tips = []
        for fk in focus_out:
            term = fk["term"]
            if term in glossary and term not in seen_gloss:
                seen_gloss.add(term)
                e = next(x for x in els if x["id"] == fk["id"])
                txt = f"{term}：{glossary[term]}"
                tls, ts, tw, th = fit_text(p, f"glossary.{term}", txt, TYPE["body"], 640, 2, lh=1.35)
                r = fk["sub"] or e
                W_, H_ = tw + 50, th + 36
                cands = [(r["x"] + r["w"] / 2 - W_ / 2, r["y"] + r["h"] + 18, True), (r["x"] + r["w"] / 2 - W_ / 2, r["y"] - H_ - 18, False),
                         (r["x"] + r["w"] + 24, r["y"], True), (r["x"] - W_ - 24, r["y"], True),
                         (BAND["x"] + BAND["w"] - W_, BAND["y"] + BAND["h"] - H_, True), (BAND["x"], BAND["y"] + BAND["h"] - H_, True)]
                place = None
                for cx_, cy_, below in cands:
                    cx_ = min(BAND["x"] + BAND["w"] - W_, max(BAND["x"], cx_))
                    if cy_ < BAND["y"] - 10 or cy_ + H_ > BAND["y"] + BAND["h"] + 20:
                        continue
                    hit = [o["id"] for o in els if o is not e and o["kind"] not in ("arrow", "codebox") and not (cx_ + W_ <= o["x"] or cx_ >= o["x"] + o["w"] or cy_ + H_ <= o["y"] or cy_ >= o["y"] + o["h"])]
                    if fk["sub"] is None and not (cx_ + W_ <= e["x"] or cx_ >= e["x"] + e["w"] or cy_ + H_ <= e["y"] or cy_ >= e["y"] + e["h"]):
                        hit.append(e["id"])
                    if not hit:
                        place = (cx_, cy_, below)
                        break
                if place is None:
                    p.hint(f"{sid}: 术语「{term}」的释义气泡放不下（四周都是文字）—— 已省略；想要它就在台词里直接解释")
                    continue
                tx, ty, below = place
                show = max(75, int(cap_chars(txt) / _cap.CPS * FPS))
                tips.append({"term": term, "x": round(tx, 1), "y": round(ty, 1), "w": round(W_, 1), "h": round(H_, 1), "lines": tls, "size": ts,
                             "at": fk["at"] + 6, "until": min(dur - 2, fk["at"] + 6 + show), "below": below})
                if show > fk["until"] - fk["at"]:
                    fk["until"] = min(dur - 4, fk["at"] + show)
        # 音效：只挂真事件
        # 3.5.1：线稿 / 标注先解析，再统一排程——必须在音效与 beats 之前，否则音效还对着排程前的帧（spec T-P0-07 (6)）
        sk_out = resolve_sketch(p, sid, sh.get("sketch"), line_start, sh["line_cues"], cues, frm) if sh.get("sketch") else None
        if sk_out is not None:
            sk_out["box"] = sh.get("sketch_box") or SKETCH_BOX["left"]
        ann_out = resolve_annotate(p, sid, sh.get("annotate"), els, line_start, sh["line_cues"], cues, frm)
        schedule_reveals(els, sk_out, ann_out or [], tips)
        _last = max([e["at"] for e in els] + [a_["at"] for a_ in (ann_out or [])] + [0])
        if line_end and _last > line_end[-1]:
            p.hint(f"{sid}: 这一镜东西太多，旁白讲完了还有东西在开始出现（第 {_last} 帧 > 末句结束第 {line_end[-1]} 帧）——删 1–2 个元素或拆成两镜")
        sfx = []
        for e in els:
            if e["kind"] == "number":
                sfx.append({"event": "pop", "at": e["at"] + 30})
            elif e["kind"] == "bar" and e["idx"] == 0:
                sfx.append({"event": "chart", "at": e["at"] + 22})
            elif e["kind"] == "codebox":
                sfx.append({"event": "typing", "at": e["at"] + 6})
        for fk in focus_out:
            if fk["cam"]:
                sfx.append({"event": "highlight", "at": fk["at"]})
        if sh["layout"] == "quiz" and nl > 1:
            sfx.append({"event": "success", "at": line_start[1]})
        if sh["layout"] == "compare":
            ap = [e for e in els if e["id"] == "after"]
            if ap:
                sfx.append({"event": "success" if sh["content"].get("mode") == "morph" else "pop", "at": ap[0]["at"] + 4})
        # 装饰 / 图标预算
        icons = sh["icons"]
        text_chars = sum(cap_chars(str(e.get("text") or "")) for e in els if e["kind"] not in ("arrow", "timer"))
        decor = icons + sum(1 for e in els if e["kind"] == "arrow")
        if icons > ICON_BUDGET_SHOT:
            p.hint(f"{sid}: 图标 {icons} 个 > 每镜 {ICON_BUDGET_SHOT}（能用字说清的就用字）")
        if decor >= 3 and text_chars < 12:
            p.hint(f"{sid}: 装饰多、文字少（装饰 {decor} / 文字 {text_chars} 字）—— 精简装饰，或换成 define / list 版式")
        # 骨架标签（相邻不同）
        opts = SKELETONS[sh["layout"]]
        skel = opts[0] if opts[0] != used_skel else opts[1]
        used_skel = skel
        # 慢推意图（场景层 ShotCamera）：真的会动 ≥0.02
        cam = {"intent": INTENTS[sh["layout"]], "at": 6, "dur": max(30, min(90, dur - 10)), "from": 1.0, "to": 1.025}
        # treatment.shots 写了 move 就以它为准：两份文件（导演意图 / 实际镜头表）本该一致，
        # 各写一套只会让 validate-treatment 天天报「写了不兑现」，作者于是去改门禁而不是改片。
        want = TREATMENT_MOVES.get(sid)
        if want in ("establish", "push-in", "pull-back", "pan-follow", "reveal", "still"):
            if want != cam["intent"]:
                cam["intent"] = want
                p.fix(f"{sid}: treatment 写 move={want} → 本镜运镜按它走（原按版式给 {INTENTS[sh['layout']]}）")
        if cam["intent"] == "pull-back":
            cam.update({"from": 1.03, "to": 1.0})
        if cam["intent"] == "reveal":
            cam.update({"to": 1.03})
        # 3.5.1：线稿镜头只做 1.00→1.03 的慢推（不切图），intent 在 establish / push-in / reveal 间轮换，
        # 否则 validate-shot-motion 判「不算运镜」和「全片 1 种意图」（spec §5 E3）。
        if sh.get("sketch"):
            cam = {"intent": ("establish", "push-in", "reveal")[sk_seen % 3], "at": 6, "dur": max(30, min(90, dur - 10)), "from": 1.0, "to": 1.03}
            sk_seen += 1
        beats = [{"cue": ci_, "offset": 0} for ix in sh["line_cues"] for ci_ in ix]
        # beats 不能只数字幕：镜内元素也是真画面变化（大字写完、盖章、放上手绘小图）。
        # 只看 cue 时，S1 这种「一句字幕读 3 秒、画面里却连着三个动作」的开场会被判成
        # 「前 3 秒只有 2 个节拍」（validate-opening O4 直接 P0），而屏幕上的画面明明是动的。
        # 这里把镜内元素的 at（本地帧）补成一拍：挂到「它前一条字幕」上，offset 取与那句起点的差。
        # 不能一律挂首个 cue —— 元素若在第二句才出现，offset 就会大过那一句的时长，
        # validate-presentation 判「元素在旁白讲完后才出现 = 与台词脱节」（S1/S4/S6 实测 P0×7）。
        cue_list = [ci_ for ix in sh["line_cues"] for ci_ in ix]
        cue_locals = [frame(cues[ci_]["start_ms"]) - frm for ci_ in cue_list]
        cue_dur = [frame(cues[ci_]["speech_end_ms"]) - frame(cues[ci_]["start_ms"]) for ci_ in cue_list]
        for e_ in (sh.get("els") or []):
            at_ = e_.get("at")
            if not isinstance(at_, int) or at_ <= 2:
                continue
            if any(abs(at_ - cl) < 12 for cl in cue_locals):
                continue
            # 归属：at_ 之前最近的那条字幕（第一句之前则归第一句，offset 夹到 0）
            owner = 0
            for i_, cl in enumerate(cue_locals):
                if cl <= at_:
                    owner = i_
            off = max(0, at_ - cue_locals[owner])
            # 超过该句时长就不算这一句的节拍（那是下一句之后的事，交给下一句的 cue 记）
            if cue_dur and off > cue_dur[owner]:
                continue
            beats.append({"cue": cue_list[owner], "offset": off})
        # 排序键必须落在「绝对帧」上：用 ms 排会因为 offset 是帧、start_ms 是毫秒而错序
        # （S1 实测 75 排到了 49 前面）。统一先换成绝对帧再排。
        for b in beats:
            b["_abs"] = frame(cues[int(b["cue"])]["start_ms"]) + int(b.get("offset", 0))
        beats.sort(key=lambda b: b["_abs"])
        dedup = []
        for b in beats:
            if dedup and b["_abs"] - dedup[-1]["_abs"] < 3:
                continue
            dedup.append(b)
        beats = dedup
        for b in beats:
            b.pop("_abs", None)
        a = {"x": round(U["x"], 1), "y": round(U["y"], 1), "w": round(U["w"], 1), "h": round(U["h"], 1)}
        # camera:"still" → 相机冻结在一帧不动。
        # 注意：只写 drift:"none" 是不够的——引擎有 path 时直接走 pathCamAt，drift 根本不参与。
        # 之前那点"一直在晃"就是 path 里的 1.0→1.025 慢推 + x 偏 20px 造成的。
        # 静止片里，动效只允许来自「笔画、压章、翻页、逐字」，不允许来自画框。
        if str(story.get("camera") or "") == "still":
            path = [{"at": 0, "x": 960.0, "y": 540.0, "s": 1.0}]
            focus_out = []
        # 3.5.0：线稿镜头不做推近 / 取景收紧——线稿在画面边上，任何 >1.05 的缩放都会把它顶出画框。
        if sh.get("sketch"):
            path = [{"at": 0, "x": 960.0, "y": 540.0, "s": 1.0}, {"at": max(31, dur - 12), "x": 960.0, "y": 540.0, "s": 1.03}]
            focus_out = []
        rec = {"id": sid, "chapter": sh["chapter"], "skeleton": skel, "layout": f"{sh['layout']}{('-' + sh['variant']) if sh['variant'] else ''}",
               "from": frm, "to": to, "cues": [sh["line_cues"][0][0], sh["line_cues"][-1][-1]],
               "media": MEDIA[sh["layout"]], "live": ["AutoShot"], "camera": cam, "anchor": a, "contentBand": BAND,
               "hero": {"name": sh["layout"], "size": int(max(U["w"], U["h"]) * 0.5), "kind": "text"}, "zones": 3, "bottomFill": True,
               "cover": "paper", "entry": "build", "beats": beats, "move": moves[k],
               "evidence": "AutoShot", "hold": 40, "noMisconception": True, "why": "auto 版式：内容由 story.json 给出",
               # 镜间转场：story 写了就一律用它；没写就是 "auto" —— 交给引擎按皮肤决定，
               # 而皮肤的缺省是翻页（pageturn / 无 GPU 时 pageflip）。
               # 3.9.0 之前这里缺省写 fade，把皮肤的翻页默认值**覆盖掉了**：
               # 于是只要 story 没显式写 "pageturn"，全片就没有一处翻页。默认值只能有一处。
               "transition": (str(story.get("transition")) if (story.get("transition") and k > 0) else "auto"),
               "cinema": {"drift": "none", "fit": "none", "path": path,
                          **({"still": True} if str(story.get("camera") or "") == "still" else {})}, "sfxEvents": sfx}
        if sh["layout"] == "quiz":
            rec["misconception"] = sh["content"].get("question"); rec.pop("noMisconception")
        # 手账页：把「拍到的是什么」也记进来。rec 的 "media" 已被骨架占用（graphic/text），
        # 所以真图版用 media_id —— validate-fusion 靠 media_label 判断主题物有没有出现。
        if sh["layout"] == "page":
            _c = sh.get("content") or {}
            rec["page"] = _c.get("page") or "plate"
            rec["media_id"] = _c.get("media")
            rec["media_label"] = " ".join(str(x) for x in [
                _c.get("catalogue") or "", _c.get("title") or "", _c.get("big") or "", _c.get("note") or ""]).strip()
        out_shots.append(rec)
        story_ts[sid] = {"layout": sh["layout"], "variant": sh["variant"], "elements": els, "focus": focus_out, "tips": tips,
                         "lines": line_start, "lineEnds": line_end, "think": int(float(sh["content"].get("think", 3)) * FPS) if sh["layout"] == "quiz" else 0,
                         "custom": sh["custom"], "icons": icons}
        if sk_out:
            story_ts[sid]["sketch"] = sk_out
        if ann_out:
            story_ts[sid]["annotate"] = ann_out
    # 节奏：快慢交替（同速 3 镜连排 → 提示）
    tempo = ["fast" if (s["to"] - s["from"]) < 150 or s["layout"].startswith(("number", "statement")) else "slow" for s in out_shots]
    for i in range(2, len(tempo)):
        if tempo[i] == tempo[i - 1] == tempo[i - 2]:
            p.hint(f"{out_shots[i]['id']}: 连续 3 镜都是 {tempo[i]} 节奏 —— 中间换一镜 number / quiz（快）或 code / flow（慢）")
    # 每分钟图标
    mins = max(1.0, total / FPS / 60)
    ic = sum(v["icons"] for v in story_ts.values())
    if ic / mins > ICON_BUDGET_MIN:
        p.hint(f"全片图标 {ic} 个 / {mins:.1f} 分钟 > 每分钟 {ICON_BUDGET_MIN} 个 —— 删掉装饰性图标")
    return out_shots, story_ts, total


# ---------------------------------------------------------------- acts / reprises / draw
# 动作与复现层搬到了 story_acts.py（P2-24 第三切片）：@L1.3 换算、两套动词表、content.ink.acts
# 校验、跨镜复现判定（P2-19）、线稿规格的构建期核对（P1-09）都归它。
# 为什么先切这层：lay_page 直接调 resolve_ink_acts / check_draw；不先切，版式层就没法独立。
# 帧号换算只走 story_time.frame；本文件不再定义 FPS / frame。


def tts_words(proj: Path) -> list[dict] | None:
    """读 TTS 产出的词级时间；没有 meta（= 不是 tts 生成的）就不算数。

    为什么认 meta 而不是认文件在不在：compose 自己也会写 audio/narration.mp3.json（静音估算），
    只认文件会把"自己的估算"当成"TTS 的真实时间"，然后拿它去重排——看起来对齐了，其实没动。
    """
    meta = proj / "audio" / "narration.meta.json"
    words_p = proj / "audio" / "narration.mp3.json"
    if not meta.is_file() or not words_p.is_file():
        return None
    try:
        words = json.loads(words_p.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return words if isinstance(words, list) and words else None


def _spoken(ch: str) -> bool:
    return ch.isalnum() or ch in "0123456789.%+-" or "\u4e00" <= ch <= "\u9fff"


def retime_to_tts(comp: dict, words: list[dict], p: "Problems") -> bool:
    """把字幕 cues 与镜头起点重排到 TTS 的真实词级时间上。

    字幕文本来自 compose 的语义断句，TTS 词表来自音频。两边按"可发音字符"逐个对；
    一旦对不上（数字读法、英文缩写差异）就整体放弃并说明——半套时间比没对齐更糟。
    """
    timeline: list[tuple[str, int, int]] = []
    for w in words:
        cs = [c for c in str(w.get("part", "")) if not c.isspace()]
        if not cs:
            continue
        try:
            a, b = int(w["start"]), int(w["end"])
        except (KeyError, TypeError, ValueError):
            continue
        for i, ch in enumerate(cs):
            timeline.append((ch, round(a + (b - a) * i / len(cs)), round(a + (b - a) * (i + 1) / len(cs))))
    # 词表里要**连标点一起**对：validate-caption-sync 比对的是 cue.text 与 words 的逐字拼接，
    # 只对齐"可发音字符"会让每条 cue 都少一个句号（实测 16 条 sync failure）。
    flat = timeline
    if not flat:
        return False
    idx = 0
    old_start: dict[int, int] = {}
    cues = comp["cues"]
    for ci, cue in enumerate(cues):
        chars = [c for c in cue["text"] if not c.isspace()]
        if not chars:
            continue
        seg = flat[idx:idx + len(chars)]
        if [c for c, _, _ in seg] != chars:
            p.hint(
                f"TTS 词表与第 {ci + 1} 句字幕对不上（音频说的字与字幕文本不一致）——"
                f"字幕/镜头沿用原有时序。修法：让 narration.txt 与字幕同文，或重跑 tts。"
            )
            return False
        old_start[ci] = int(cue["start_ms"])
        cue["words"] = [{"part": c, "start": st, "end": en} for c, st, en in seg]
        cue["start_ms"], cue["speech_end_ms"], cue["reveal_end_ms"] = seg[0][1], seg[-1][2], seg[-1][2]
        cue["start"], cue["speech_end"], cue["reveal_end"] = (
            round(cue["start_ms"] / 1000, 3), round(cue["speech_end_ms"] / 1000, 3), round(cue["reveal_end_ms"] / 1000, 3))
        idx += len(chars)
    # 镜头起点跟着它第一句字幕走（保持"台词前多久起镜"的相对关系）
    prev = 0
    for sh in comp["shots"]:
        ix = sh.get("line_cues") or []
        if ix and ix[0][0] in old_start:
            ci = ix[0][0]
            sh["start_ms"] = max(prev + 1, int(sh["start_ms"]) + (int(cues[ci]["start_ms"]) - old_start[ci]))
        else:
            sh["start_ms"] = max(prev + 1, int(sh.get("start_ms", prev + 1)))
        prev = int(sh["start_ms"])
    last_end = max((c["speech_end_ms"] for c in cues), default=0)
    # 有真实音频时间就**以它为准**（可以缩短）：compose 的估算是按 4.5 字/秒排的，
    # 而口播的实际语速常常到 5 字/秒以上，照估算值播出会留十几秒画面空转。
    if last_end:
        comp["total_ms"] = last_end + END_TAIL_F * 1000 // FPS
    p.hint(f"按 TTS 词级时间重排：{len(cues)} 句字幕 / {len(comp['shots'])} 镜（时间来自 audio/narration.meta.json）")
    return True


# ---------------------------------------------------------------- output
# 写盘层搬到了 story_output.py（P2-24 第五切片）：manifest / src/*.ts(x) / media / 旁白契约。
# 这里只 import 回来当门面，main() 的调用点不变。

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("story")
    ap.add_argument("project")
    ap.add_argument("--report")
    ap.add_argument("--check", action="store_true", help="只检查不写盘")
    # 3.3.0：读速可配置（加权字/秒，1–9）。也可在 story.json 顶层写 "cps"。缺省 4.5（组件路线的既有速度）。
    ap.add_argument("--cps", type=float, help="无 TTS 时的字幕读速（字/秒，1–9；缺省 4.5，或 story.json 的 cps）")
    a = ap.parse_args()
    sp = Path(a.story)
    if not sp.is_file():
        print(f"找不到 {sp}", file=sys.stderr)
        return 2
    try:
        story = json.loads(sp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"story.json 不是合法 JSON：第 {e.lineno} 行第 {e.colno} 列 —— {e.msg}", file=sys.stderr)
        return 1
    story["_dir"] = str(sp.parent.resolve())
    cps = a.cps or story.get("cps")
    if cps is not None:
        if not isinstance(cps, (int, float)) or not 1.0 <= float(cps) <= 9.0:
            print(f"cps={cps!r} 超出 1–9 字/秒（validate-presentation 的成人读速上限是 9）", file=sys.stderr)
            return 2
        _cap.set_cps(cps)
    setup_break_rule(Path(a.project))
    # treatment.signature_shot 决定哪一镜真推（3.6.2）；没有 treatment 就是 None，行为不变
    global TREATMENT, TREATMENT_MOVES
    tp = Path(a.project) / "manifests" / "treatment.json"
    try:
        TREATMENT = json.loads(tp.read_text(encoding="utf-8")) if tp.is_file() else {}
    except (ValueError, OSError):
        TREATMENT = {}
    # treatment.shots[].move → {镜号: 运镜}：导演层写了就按它走（见 build() 里的 cam 段）
    TREATMENT_MOVES = {s.get("id"): s.get("move") for s in (TREATMENT.get("shots") or [])
                       if isinstance(s, dict) and s.get("id") and s.get("move")}
    p = Problems()
    cap_mode = str((story.get("captions") or {}).get("mode", "line")).lower()
    if cap_mode not in ("line", "typewriter", "type"):
        p.err(f"captions.mode={cap_mode!r} 不是有效值 —— 用 \"line\"（默认，整行出现）或 \"typewriter\"（逐字打出）。")
    left = sorted(set(re.findall(r"<<([^>]*)>>", json.dumps(story, ensure_ascii=False))))
    if left:
        for x in left[:12]:
            print(f"  ✗ 蓝图占位符没填：<<{x}>> —— 换成你的内容（或删掉这一镜）")
        print(f"compose-story：还有 {len(left)} 处 <<占位符>> 没填")
        return 1
    comp = compose(story, p)
    if comp is not None:
        _tw = tts_words(Path(a.project))
        if _tw:
            retime_to_tts(comp, _tw, p)
        for c in comp["cues"]:
            if re.search(r"主页搜\s*(?!【)", c["text"]):
                p.hint(f"{c['text']!r} 里还留着示例账号 —— 换成你自己的，或写成「主页搜【你的账号】」；"
                       f"弱模型常原样抄走示例结尾。")
                break
    if comp is None or not comp["shots"]:
        for m in p.errors:
            print(f"  ✗ {m}")
        return 1
    out_shots, story_ts, total = build(story, comp, p)
    check_customs(p, Path(a.project), story_ts)
    for m in p.fixes:
        print(f"  ✓ 自动修：{m}")
    for m in p.hints:
        print(f"  · 建议：{m}")
    for m in p.errors:
        print(f"  ✗ {m}")
    print(f"compose-story：{len(out_shots)} 镜 / {len(comp['cues'])} 行字幕 / {total} 帧（{total / FPS:.1f} 秒）"
          f" · 自动修 {len(p.fixes)} · 建议 {len(p.hints)} · 错误 {len(p.errors)}")
    if a.report:
        Path(a.report).write_text(json.dumps({"fixes": p.fixes, "hints": p.hints, "errors": p.errors, "frames": total,
                                              "shots": [{k: s[k] for k in ('id', 'from', 'to', 'layout')} for s in out_shots]}, ensure_ascii=False, indent=1), encoding="utf-8")
    if p.errors:
        return 1
    if not a.check:
        write_project(story, comp, out_shots, story_ts, total, Path(a.project), p)
        if story.get("media"):
            write_media(story, Path(a.project))
    return 0


if __name__ == "__main__":
    sys.exit(main())
