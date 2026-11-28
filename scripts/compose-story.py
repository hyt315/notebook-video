#!/usr/bin/env python3
"""compose-story.py · 内容表 → 可渲染工程（自动排版 + 自动修复 + 讲解规则）

弱模型只写 story.json（纯内容：章节 / 每镜版式 / 台词 / 版式内容），本脚本负责全部"质量"：

  1. 字幕   每行 ≤16 字，超了在标点 / 语义边界自动劈开（绝不劈开 {{术语}}、英文单词或数字）；
            无 TTS：按 4.5 字/秒自动排时间（逗号 +150 ms、句末 +300 ms），读不完就延长镜头；
            章节之间与镜间同样的间隔（不插章节卡 / 进度条）。
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
import difflib
import json
import math
import re
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import linework_index  # noqa: E402  （必须在 sys.path 之后导入）
import narration_contract  # noqa: E402
from story_camera import (  # noqa: E402  （必须在 sys.path 之后导入）
    SAFE, ZOOM_MAX, clamp_look, frame_rect, in_frame, move_frames, partial_clips, to_screen, union,
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
TREATMENT_MOVES: dict = {}   # 由 treatment.shots 展开：{镜号: move}，在 main() 里与 TREATMENT 一起填；move=still 的镜不推不扫
LINE_GAP_MS = 220              # 同镜两行之间
SHOT_GAP_MS = 320              # 镜与镜之间
CHAPTER_BREATH_MS = SHOT_GAP_MS  # 不再有章节呼吸 / 章节卡（保持默认组件风格）
FIRST_LEAD_MS = 700            # 片头（flat / cel）
# 手作皮肤冷开——validate-opening 对手作皮肤硬性要求「第一个可见事件 ≤ 6 帧」（O1），
# 而 auto 路线的节拍都挂在字幕上、最早只能落在第一句起点：700 ms = 第 21 帧，于是任何手作 story
# 走 auto 路线都必挂 O1（随包手作示例全挂的根因之一）。手作皮肤把第一句提前到 150 ms（第 4.5 帧）。
# flat / cel 不变（O1 对它们只是提示，且已交付片的时间轴不能动）。
FIRST_LEAD_MS_HANDMADE = 150
# 招牌镜起幅与推近落点的缩放比：略高于门禁线 1.12，留出取整余量
SIG_OPEN_RATIO = 1.13
# 音效稀疏上限（sfxDensity 缺省 sparse）：任一 10 秒窗口内至多 4 个；两个音效相距不超过 0.4 秒算同一拍
SFX_WINDOW_F = 300
SFX_SPARSE_MAX = 4
SFX_MERGE_F = 12
COLD_OPEN_SETTLE = 60          # 第一镜首个元素提前落定的帧数：≥ 任一元素的入场时长（O6 第 0 帧要有主体）
IS_HANDMADE = False            # main() 按 src/theme/active.ts 填
HANDMADE_SKINS = ("journal", "papercut", "archive")
END_TAIL_F = 42                # 片尾
# 字幕行宽 MAX_CHARS / 朗读速度 CPS / 标点停顿 / 术语语法 TERM_RE 的真源在 story_caption.py
# 不可变的从那儿 import；可变的 CPS / CHAR_MS 一律读 story_caption.xxx，
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
# 文字层在 story_text.py：字宽、折行、孤字调整、字号收敛、行高地板都归它。
# 这里只 import 并在模块级别名（`cs.wrap(...)` 等调用保持可用）；改折行规则时只动 story_text.py。
# 边界：split_caption 仍留在本文件（它要读 BudouX 规则，属于「字幕怎么切」而不是「字怎么排」）。


# ---------------------------------------------------------------- captions
# 字幕层在 story_caption.py：术语解析、>16 字怎么劈、断点来源、每句时长、朗读速度都归它。
# 这里只 import 回来，`cs.split_caption(...)` / `cs.time_cue(...)` 保持可用。
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


def sweep_track(els, base, keep=None, min_span=300):
    """横向扫镜：找出同一行里并排放的元素，给出 (起幅 look, 落幅 look)。

    一行多节点并排的流程 / 对比 / 柱状镜，在 16:9 里沿行横移既不切断邻居又富动感（pan-follow）。
    起幅对准最左元素、落幅对准最右元素；停留点校验不切字且 anchor（keep）始终完整在画。
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
    scy = (SAFE[1] + SAFE[3]) / 2
    best, best_span = None, 0.0
    s = max(1.04 if keep else 1.0, base["s"])
    while s <= ZOOM_MAX + 1e-9:
        hx, hy = 960.0 / s, 540.0 / s
        lo_x, hi_x = hx, 1920.0 - hx
        lo_y, hi_y = hy, 1080.0 - hy
        if keep is not None:
            lo_x = max(lo_x, keep["x"] + keep["w"] - hx + 0.5)
            hi_x = min(hi_x, keep["x"] + hx - 0.5)
            lo_y = max(lo_y, keep["y"] + keep["h"] - hy + 0.5)
            hi_y = min(hi_y, keep["y"] + hy - 0.5)
        if lo_x > hi_x or lo_y > hi_y:
            s = round(s + 0.02, 3)
            continue

        def aim(e, s=s, lo_x=lo_x, hi_x=hi_x, lo_y=lo_y, hi_y=hi_y):
            tx = min(hi_x, max(lo_x, e["x"] + e["w"] / 2))
            ty = min(hi_y, max(lo_y, e["y"] + e["h"] / 2 - (scy - 540) / s))
            return {"x": round(tx, 1), "y": round(ty, 1), "s": round(s, 3)}

        a, b = aim(first), aim(last)
        span = abs((b["x"] - a["x"]) * s)
        if span > best_span and not partial_clips((a["x"], a["y"]), a["s"], els) \
                and not partial_clips((b["x"], b["y"]), b["s"], els) \
                and (keep is None or (in_frame(keep, (a["x"], a["y"]), s) and in_frame(keep, (b["x"], b["y"]), s))):
            best, best_span = (a, b), span
        s = round(s + 0.02, 3)
    if best is None or best_span < min_span:
        return None
    return best


def path_intent(path) -> str:
    """镜头表的 cameraIntent 从真实路径读出来（门禁按它数运镜配额、意图种类），不按版式贴标签。"""
    ss = [k["s"] for k in path]
    scale_inc = max(ss) - ss[0]
    scale_dec = ss[0] - min(ss)
    net = ss[-1] - ss[0]
    pan = max(k["x"] for k in path) - min(k["x"] for k in path) + max(k["y"] for k in path) - min(k["y"] for k in path)
    if pan >= 120 and scale_inc < 0.08 and scale_dec < 0.08:
        return "pan-follow"
    if net <= -0.02 or (scale_dec >= 0.02 and scale_dec > scale_inc):
        return "pull-back"
    if scale_inc >= 0.02:
        return "push-in"
    if pan >= 20:
        return "pan-follow"
    return "still"


def shot_anchor(sh) -> dict:
    """本镜 anchor：内容外接框（含线稿框）；空镜用整幅内容带。validate-shot-motion 证明它逐关键帧都在画面里。"""
    sk = sh.get("sketch_box") if sh.get("sketch") else None
    rs = list(sh["els"]) + ([{k: sk[k] for k in ("x", "y", "w", "h")}] if sk else [])
    return union(rs) if rs else dict(BAND)


def sig_target(els, keep):
    """招牌镜的推近落点：从最大的元素起，找第一个能推到 ≥1.12×、不切字、anchor 不出画的。"""
    for e in sorted((e for e in els if e["kind"] not in ("arrow", "timer", "codebox")), key=lambda e: -e["w"] * e["h"]):
        tgt, _ = frame_rect(e, els, max_s=1.24, min_s=1.12, keep=keep)
        if tgt["s"] >= 1.12:
            return e, tgt
    return None, None


def compose(story: dict, p: Problems):
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
    # 保护短语自动收——主题物 + 线稿 / 墨图 / 页内示意图的 label 与 parts 值，只收台词原文里真出现的词（spec §5 E4）
    _said = "".join(parse_line(str(l_))[0] for ch_ in (story.get("chapters") or []) for s_ in (ch_.get("shots") or []) for l_ in (s_.get("lines") or []))
    _cand = [str(story.get("subject_of_film") or "")]
    for ch_ in story.get("chapters") or []:
        for s_ in ch_.get("shots") or []:
            for sk_ in (s_.get("sketch"), (s_.get("content") or {}).get("ink"), (s_.get("content") or {}).get("figure")):
                if isinstance(sk_, dict):
                    _pv = sk_.get("parts")
                    _cand += [str(sk_.get("label") or "")] + [str(v_) for v_ in (_pv.values() if isinstance(_pv, dict) else [])]
    auto_protect = [w_ for w_ in dict.fromkeys(_cand) if 2 <= len(w_) <= 8 and w_ in _said]
    # dict.fromkeys 去重保序：set 的迭代顺序随 PYTHONHASHSEED 变，同长短语的先后（和产物）就不确定
    protected = sorted(dict.fromkeys(list(glossary.keys()) + list(story.get("protect") or []) + auto_protect), key=len, reverse=True)
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
    title_seed = zlib.crc32(str(story.get("title") or "").encode("utf-8"))
    AUTO_VARIANTS = {
        "statement": ("", "left"),
        "define": ("", "mirror"),
        "number": ("", "mirror"),
        "media": ("", "mirror"),
        "bars": ("", "center"),
        "code": ("", "mirror"),
        "list": ("", "grid"),
    }
    for ci, ch in enumerate(chapters):
        if ci > 0:
            t_ms += CHAPTER_BREATH_MS
        for si, sh in enumerate(ch.get("shots") or []):
            sid_n += 1
            sid = sh.get("id") or f"S{sid_n}"
            _ask = str(sh.get("$asks") or "").strip()
            if not _ask or _ask.startswith("例："):
                p.hint(f"{sid}: 缺 $asks（这一镜要回答观众的哪个问题）—— 写清问题；写不出就删掉这镜（见 references/narration.md）")
            lay = sh.get("layout")
            if lay not in LAYOUTS:
                p.err(f"{sid}: layout={lay!r} 不是 {LAYOUTS} 之一 —— 不确定就用 define / list / compare 这类组件版式（手账页用 page）")
                continue
            explicit_var = "variant" in sh and sh.get("variant") is not None
            variant = str(sh.get("variant") or "")
            if not explicit_var and lay == prev_layout:
                variant = prev_variant
            elif not explicit_var and lay in AUTO_VARIANTS:
                choices = AUTO_VARIANTS[lay]
                variant = choices[(title_seed + zlib.crc32(lay.encode("utf-8"))) % len(choices)]
            # 自动修：相邻同版式 → 换镜像变体
            if lay == prev_layout and variant == prev_variant:
                alt_pair = AUTO_VARIANTS.get(lay)
                alt = next((x for x in (alt_pair or ()) if x != variant), None)
                if alt is not None:
                    variant = alt
                    p.fix(f"{sid}: 与上一镜同版式 {lay}，自动换成变体 {alt or 'default'}")
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
                        p.err(f"{sid}: recipe='photo-traced' 已移除（没有实现）——照片请用 layout: media，再用 annotate 圈出讲到的地方")
                        recipe = None
                        continue
                    p.hint(f"{sid}: recipe={recipe!r} 未知 —— 按组件路线走（有效：sketch-readout / component-annotated / scene-verdict / before-after / list-icons / data-with-object / hammer）")
                    recipe = None
            sk_raw = sh.get("sketch")
            if sk_raw and not sketch_box:
                sketch_box = SKETCH_BOX["left"]
            if lay not in ("custom", "bars", "statement", "type", "compare", "flow") and els:
                # 挪到内容带正中（compare / flow 自己按视觉中心略偏上定位，不动）
                u = union(els)
                dy = BAND["y"] + (BAND["h"] - u["h"]) / 2 - u["y"]
                if abs(dy) > 8:
                    for e in els:
                        e["y"] = round(e["y"] + dy, 1)
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
                for pi, (ptxt, pterms) in enumerate(parts):
                    words, end = time_cue(ptxt, t_ms)
                    cue = {"text": ptxt, "words": [{"part": w["part"], "start": w["start"], "end": w["end"]} for w in words],
                           "start_ms": int(t_ms), "speech_end_ms": end, "reveal_end_ms": end,
                           "start": round(t_ms / 1000, 3), "speech_end": round(end / 1000, 3), "reveal_end": round(end / 1000, 3)}
                    cues.append(cue)
                    idxs.append(len(cues) - 1)
                    for tm in pterms:
                        wi = max([i for i, w in enumerate(words) if w["char"] <= tm["start"]] or [0])
                        terms_all.append({**tm, "line": li, "ms": words[wi]["start"], "cue": len(cues) - 1})
                    t_ms = end + ((180 if (ptxt.rstrip() and ptxt.rstrip()[-1] in '，、；：,;:') else 80) if pi < len(parts) - 1 else (STOP_MS + LINE_GAP_MS))
                line_cues.append(idxs)
                if think_after is not None and li == think_after:
                    t_ms += int(float(content.get("think", 3)) * 1000)
            t_ms += SHOT_GAP_MS - LINE_GAP_MS
            shots.append({"sid": sid, "layout": lay, "variant": variant, "chapter": ch.get("title", f"第{ci + 1}章"), "ci": ci,
                          "first_in_chapter": si == 0, "els": els, "line_cues": line_cues, "terms": terms_all, "content": content,
                          "start_ms": shot_start_ms, "icons": int(sh.get("icons", 0)), "custom": content.get("component"),
                          "role": sh.get("role") or ch.get("role"), "recipe": recipe, "sketch": sk_raw,
                          "transition": sh.get("transition"),
                          # 有意复现：recallOf=回扣先前那张图，variantOf=同一主题物的另一态。
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
    shots, cues = comp["shots"], comp["cues"]
    still_film = str(story.get("camera") or "") == "still"
    # 不推不扫的镜：全片 camera:"still"、线稿镜（线稿在画面边上，推近会顶出画框）、treatment 写 move=still
    frozen_ids = {sh["sid"] for sh in shots if still_film or sh.get("sketch") or TREATMENT_MOVES.get(sh["sid"]) == "still"}
    sig_ok = lambda sh: sh["sid"] not in frozen_ids and (  # noqa: E731
        sig_target(sh["els"], shot_anchor(sh))[0] is not None or sweep_track(sh["els"], {"s": 1.0}, shot_anchor(sh)) is not None)
    # treatment 点名的招牌镜要一个看得见的运镜（validate-treatment 硬查）。生成前就知道它推不进也扫不开时，
    # 改由最近的、推得进或扫得开的一镜担任，并同步写回 treatment（main 落盘）；全片都不行才留给作者。
    sig_id = signature_shot_id(p)
    k0 = next((k for k, sh in enumerate(shots) if sh["sid"] == sig_id), None)
    if k0 is not None and not sig_ok(shots[k0]):
        alt = min((k for k, sh in enumerate(shots) if sig_ok(sh)), key=lambda k: (abs(k - k0), -k), default=None)
        if alt is not None:
            new_id = shots[alt]["sid"]
            p.fix(f"{sig_id}: 招牌镜推不进也横移不开 → 改由 {new_id} 担任（已同步 treatment.signature_shot）")
            TREATMENT["signature_shot"] = f"{new_id}（{sig_id} 推不进也横移不开，compose 自动改选；原为：{TREATMENT['signature_shot']}）"
            sig_id = new_id
    glossary = comp["glossary"]
    total = frame(comp["total_ms"])
    out_shots, story_ts = [], {}
    prev_gaze = None
    seen_gloss = set()
    used_skel = None
    minute_icons = 0
    recent_intents: list[str] = []
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
        frm = 0 if k == 0 else frame(sh["start_ms"])
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
            e["at"] = max(0, line_start[a]) + n * 12 if isinstance(a, int) else 0  # 不早于所属句；同句第 n 个再晚 12n 帧
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
        # 为什么不按「字幕行」分组：一行只有 1 句字幕、却要放 4 个节点时（flow 的常态），
        # 按行分组会把 4 个节点全塞进这一句里，末尾那个要贴到镜尾才出现，箭头也就画不完。
        # 并列项本来就是一个整体，应当跨整镜铺开：起点在首句字幕起后（第一项跟着标题走），
        # 终点在镜尾前留出 SETTLE 帧让最后一张被读得完。
        PEER_SETTLE = 40
        # 本镜「全部字幕句」的本地起帧（而非 story.json 分行组；并列项对齐拆分后的真实句流）。
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
            #   (a) 句数 >= 项数：一项一句，跟着旁白走，保证声音和画面同拍。
            #   (b) 句数 <  项数：跨整镜均摊（前 42%），并留 SETTLE 帧收尾，留出阅读停顿。
            n_cue = len(cue_locals_peer) if cue_locals_peer else len(line_start)
            if n_cue >= len(peers):
                for i, e in enumerate(peers):
                    # 第 i 项落到它该跟的那一句上（n_cue 句分给 n 项，最后一项跟最后一句）
                    j = round(i * (n_cue - 1) / max(1, len(peers) - 1))
                    e["at"] = int(max(t0, cue_locals_peer[j] - 2))
            else:
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
        # 空镜是合法状态（纯配方镜、或版式校验失败后的占位镜）：shot_anchor 给整幅内容带，不让 union([]) 崩在栈里
        U = shot_anchor(sh)
        frozen = sid in frozen_ids
        band_fill = (U["w"] * U["h"]) / (BAND["w"] * BAND["h"]) if content_els else 1.0
        over, _ = frame_rect(U, content_els, max_s=1.18 if band_fill < 0.6 else 1.06)
        path = []
        gaze_in = prev_gaze if focus else None

        def gaze_frame(s0):
            """开镜取景：缩放 s0 下，让本镜第一个出现的元素落在上一镜最后注视的屏幕位置附近（视线连续）。"""
            if gaze_in is None or s0 <= 1.0 + 1e-9:
                return {"x": 960.0, "y": 540.0, "s": round(max(1.0, s0), 3)}
            first_ = min(content_els, key=lambda e: e["at"])
            look_ = clamp_look(first_["x"] + first_["w"] / 2 - (gaze_in[0] - 960) / s0,
                               first_["y"] + first_["h"] / 2 - (gaze_in[1] - 540) / s0, s0)
            return {"x": round(look_[0], 1), "y": round(look_[1], 1), "s": round(s0, 3)}

        is_sig = bool(sig_id and sid == sig_id and not frozen)
        pref_move = TREATMENT_MOVES.get(sid)
        director_done = False
        director_still = False

        if not frozen and not is_sig and dur >= 75:
            # 1) 横移扫镜（pan-follow）：flow / compare / bars 或 treatment 显式指定
            want_pan = (pref_move == "pan-follow") or (
                pref_move is None and sh["layout"] in ("flow", "compare", "bars") and recent_intents[-1:] != ["pan-follow"]
            )
            if want_pan:
                sw = sweep_track(els, over, U, min_span=120)
                if sw:
                    a, b = sw
                    hold_a = max(10, min(36, int(dur * 0.16)))
                    end_b = max(hold_a + 32, min(dur - 12, hold_a + max(36, move_frames(a, b))))
                    if end_b > hold_a:
                        path = [{"at": 0, **a}, {"at": hold_a, **a}, {"at": end_b, **b}]
                        cur = b; last_at = end_b
                        director_done = True
            # 2) 拉远交代全局（pull-back）：非冷开首镜，从主元素或特写取景缓缓拉回全景
            if not director_done and k > 0:
                want_pull = (pref_move == "pull-back") or (
                    pref_move is None and sh["layout"] in ("define", "statement", "list", "number", "compare", "code")
                    and (recent_intents[-1:] == ["push-in"] or ("pull-back" not in recent_intents[-2:] and k >= 1))
                )
                if want_pull:
                    cand_els = [e for e in content_els if e["kind"] not in ("arrow", "timer")]
                    focal = (next((x for x in els if x["id"] == focus[0]["id"]), None) if focus else None) or (
                        max(cand_els, key=lambda e: e["w"] * e["h"]) if cand_els else None
                    )
                    close_tgt = None
                    if focal is not None:
                        ct, _ = frame_rect(focal, els, max_s=1.22, min_s=1.06, keep=U)
                        if ct["s"] >= 1.06:
                            close_tgt = ct
                    if close_tgt is None and over["s"] >= 1.05:
                        close_tgt = over
                    if close_tgt is not None:
                        wide_end = {"x": 960.0, "y": 540.0, "s": 1.0}
                        if over["s"] >= 1.04 and close_tgt["s"] - over["s"] >= 0.04:
                            wide_end = over
                        hold_c = max(14, min(54, int(dur * 0.28)))
                        pull_end = max(hold_c + 34, min(dur - 12, hold_c + max(36, move_frames(close_tgt, wide_end))))
                        if pull_end > hold_c:
                            path = [{"at": 0, **close_tgt}, {"at": hold_c, **close_tgt}, {"at": pull_end, **wide_end}]
                            cur = wide_end; last_at = pull_end
                            director_done = True
            # 3) 呼吸推近或定机收束（still / push-in）
            if not director_done and k > 0 and sh.get("role") == "recap" and dur <= 165 and "still" not in recent_intents[-2:]:
                path = [{"at": 0, "x": 960.0, "y": 540.0, "s": 1.0}]
                cur = path[0]; last_at = 0
                director_done = True
                director_still = True

        if not director_done and prev_gaze is not None and focus:
            # 视线连续：本镜第一个出现的元素放在上一镜最后注视的屏幕位置附近，再滑到全景
            first = min(content_els, key=lambda e: e["at"])
            gx, gy = prev_gaze
            s0 = over["s"]
            look = clamp_look(first["x"] + first["w"] / 2 - (gx - 960) / s0, first["y"] + first["h"] / 2 - (gy - 540) / s0, s0)
            path.append({"at": 0, "x": round(look[0], 1), "y": round(look[1], 1), "s": s0})
            path.append({"at": 30, **over})
        elif not director_done and k == 0 and any(e["kind"] not in ("arrow", "timer") for e in content_els):
            # 冷开的第一镜：题眼在第 0 帧已落定，开场画面就是建立镜，取全景 1.00×；
            # 往里推交给本镜的关键词运镜，不在开场先裁掉一圈。
            path.append({"at": 0, "x": 960.0, "y": 540.0, "s": 1.0})
        elif not director_done:
            path.append({"at": 0, **over})

        cur = {k_: path[-1][k_] for k_ in ("x", "y", "s")}  # 只带位置；不能带 at（{"at": t, **cur} 会被它覆盖）
        last_at = path[-1]["at"]
        focus_out = []
        for i, fk in enumerate(focus):
            # 同一元素连续点名 → 只推一次（保持）
            if focus_out and focus_out[-1]["id"] == fk["id"] and fk["at"] - focus_out[-1]["at"] < 90:
                focus_out[-1]["until"] = max(focus_out[-1]["until"], fk["at"] + 45)
                continue
            if director_done:
                tgt = None
            else:
                tgt, tries = frame_rect(fk["rect"] if not fk["sub"] else next(e for e in els if e["id"] == fk["id"]), els,
                                        max_s=ZOOM_MAX, min_s=1.0, keep=U)
                if tgt["s"] < ZOOM_MIN_FOCUS or frozen:
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
            if not director_done and tgt and nxt - until > 75:
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
        # 招牌镜：treatment.signature_shot 点名的那一镜，给一个「看得见的运镜」。
        # 为什么要有这条：auto 版式的运镜是统一 1.03 的呼吸推，一镜到底等于静帧；
        # 于是「写了招牌镜」和「版式做不到」互相打架——作者只能去改 treatment 逃避门禁。
        # 两条路，先试真推，推不进就横移：
        #   ① 真推：推最大的那个元素到 1.18 倍（有独占大主体的镜，如 page 的图版、单面板）；
        #   ② 横移：一行并排的元素（flow / list / compare）在 16:9 里推不得（推一点就切断邻居），
        #      但可以「镜头沿流程扫过去」——位移 300–1300px，这正是 treatment 里 pan-follow 的语义。
        if sig_id and sid == sig_id and not frozen:
            # 落点下限用门禁线（12%）而不是 1.18：一字排开的并列结构常常只放得下 1.15 左右，死守 1.18 会白退到横移
            main, tgt = sig_target(els, U)
            if tgt:
                # 关键：起幅要比推近的落点松一截。本镜的 anchor 推近往往已经 1.1 左右，
                # 从 1.1 再推到 1.15 观众只感到 4%，等于没推。招牌镜的演出应该是
                # 「先看全，再慢慢推近」。起幅缩放取「落点 / SIG_OPEN_RATIO」（不低于 1.0），
                # 在这个缩放下仍按视线连续取景（gaze_frame）；只有起幅必须是 1.00× 时才没有视线偏移的余地。
                wide = {"x": 960.0, "y": 540.0, "s": 1.0}
                land = max(20, int(dur * 0.55))
                start = max(2, land - move_frames(wide, tgt))
                back_from = max(last_at + 1, 1)
                peak_now = max(k_["s"] for k_ in path)
                if last_at <= 2 and start >= 6:
                    # 本镜前面还没有别的运镜：起幅（视线连续）保持到 start，再慢推
                    open_ = gaze_frame(min(path[0]["s"], tgt["s"] / SIG_OPEN_RATIO))
                    path = [{"at": 0, **open_}, {"at": start, **open_}]
                    path.append({"at": land, **tgt})
                    cur = tgt; last_at = land
                    p.fix(f"{sid}: 招牌镜 → {open_['s']:.2f}× 起，慢推到 {main['id']}（{tgt['s']:.2f}×）")
                elif (len(path) >= 2 and peak_now >= 1.12 - 1e-9
                      and path[1]["at"] >= move_frames(wide, path[1])):
                    # 关键词运镜已经推到 ≥1.12×：只把开镜放松，开镜那一推 + 关键词推近合起来就是招牌推近，
                    # 不在中段插「拉回全景再推」（那是一来一回的空动）。
                    open_ = gaze_frame(min(path[0]["s"], peak_now / SIG_OPEN_RATIO))
                    path[0] = {"at": 0, **open_}
                    p.fix(f"{sid}: 招牌镜 → {open_['s']:.2f}× 起，随关键词推到 {peak_now:.2f}×")
                elif start >= back_from + move_frames(cur, wide) and land < dur - 6:
                    # 关键词运镜结束得早：先回到全景，再慢推（关键帧严格递增，不回写已有的运镜）
                    path.append({"at": back_from, **cur})
                    path.append({"at": start, **wide})
                    path.append({"at": land, **tgt})
                    cur = tgt; last_at = land
                    p.fix(f"{sid}: 招牌镜 → 回全景 1.00× 后慢推到 {main['id']}（{tgt['s']:.2f}×）")
                elif path[0]["at"] == 0 and back_from + move_frames(cur, tgt) <= dur - 6:
                    # 开镜取景本来就松：放松起幅，关键词运镜走完后再慢推到主体，推近落在镜尾段
                    open_ = gaze_frame(min(path[0]["s"], tgt["s"] / SIG_OPEN_RATIO))
                    path[0] = {"at": 0, **open_}
                    path.append({"at": back_from, **cur})
                    land = min(dur - 6, back_from + max(move_frames(cur, tgt), int(dur * 0.2)))
                    path.append({"at": land, **tgt})
                    cur = tgt; last_at = land
                    p.fix(f"{sid}: 招牌镜 → {open_['s']:.2f}× 起，关键词之后慢推到 {main['id']}（{tgt['s']:.2f}×）")
                else:
                    tgt = None
            if not (tgt and tgt["s"] >= 1.12):
                sweep = sweep_track(els, over, U)
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
                elif sh["layout"] == "page":
                    # 手账 / 档案页的图版几乎占满整页高（比推近后的安全框还高），auto 路线推不进也扫不开。
                    # 放大镜页本身就有「镜片放大」这个动作，只是它不是相机运镜，招牌镜门禁不认。
                    p.hint(f"{sid}: treatment.signature_shot 点名了 page 版式——图版占满整页高，auto 路线的相机推不进去。"
                           f"招牌镜改点一镜 flow / list / compare（自动横移扫镜）；要「放大镜压上真照片」当招牌，走手写场景（references/components.md 的 LoupeMedia）")
                else:
                    p.hint(f"{sid}: treatment.signature_shot 点名了本镜，但本镜只有一个静的主体——"
                           f"换成有并列元素（flow / list / compare）或有独占大主体的镜")
        # 结尾不留 >1.2 秒的「无新事件」：非 pull-back / pan-follow 时补收束运镜
        events = [e["at"] for e in els] + [f["at"] for f in focus_out] + line_end + [path[-1]["at"]]
        tail_gap = dur - max(events)
        cur_intent = path_intent(path)
        if tail_gap > 36 and not frozen and not director_still and cur_intent not in ("pull-back", "pan-follow"):
            t_st = max(last_at + 1, dur - tail_gap + 6)
            t_en = max(t_st + 8, dur - 8)
            if t_en < dur:
                next_s = round(max(1.0, cur["s"] * 0.97), 3) if (cur["s"] >= 1.04 and recent_intents[-1:] == ["push-in"]) else round(min(ZOOM_MAX, cur["s"] * 1.03), 3)
                nx, ny = clamp_look(cur["x"], cur["y"], next_s)
                if in_frame(U, (nx, ny), next_s) and not partial_clips((nx, ny), next_s, els):
                    path.append({"at": t_st, **cur})
                    path.append({"at": t_en, "x": round(nx, 1), "y": round(ny, 1), "s": next_s})
                    cur = path[-1]; last_at = t_en
                    if next_s > path[-2]["s"]:
                        p.fix(f"{sid}: 结尾 {tail_gap} 帧无新事件 → 自动加收束慢推")
                    else:
                        p.fix(f"{sid}: 结尾 {tail_gap} 帧无新事件 → 自动加收束缓拉")
        # 释义气泡（术语第一次出现）
        tips = []
        for fk in focus_out:
            term = fk["term"]
            if term in glossary and term not in seen_gloss:
                if sh['layout'] == 'define' and term == str(sh['content'].get('term') or '').strip():
                    seen_gloss.add(term); continue
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
        # 线稿 / 标注先解析，再统一排程——必须在音效与 beats 之前，否则音效还对着排程前的帧
        sk_out = resolve_sketch(p, sid, sh.get("sketch"), line_start, sh["line_cues"], cues, frm) if sh.get("sketch") else None
        if sk_out is not None:
            sk_out["box"] = sh.get("sketch_box") or SKETCH_BOX["left"]
        ann_out = resolve_annotate(p, sid, sh.get("annotate"), els, line_start, sh["line_cues"], cues, frm)
        _late = schedule_reveals(els, sk_out, ann_out or [], tips, shot_len=dur)
        for _name, _end, _lim in _late:
            p.hint(f"{sid}: {_name} 要到第 {_end} 帧才长完，可这一镜第 {_lim} 帧前就该全部长完——删 1–2 个元素、拆成两镜，或把这句旁白写长一点")
        _last = max([e["at"] for e in els] + [a_["at"] for a_ in (ann_out or [])] + [0])
        if line_end and _last > line_end[-1]:
            p.hint(f"{sid}: 这一镜东西太多，旁白讲完了还有东西在开始出现（第 {_last} 帧 > 末句结束第 {line_end[-1]} 帧）——删 1–2 个元素或拆成两镜")
        # 纸上只写关键词——整句交给旁白（设计规范 · 版式第 7 条）。只提示，不改退出码。
        for _e in els:
            _txt = "".join(_e.get("lines") or []) or str(_e.get("text") or "")
            _cap_max = 24 if _e.get("kind") == "quote" else 10   # 引文 ≤24 字，其余 ≤10 字（别叫 _cap：那是 story_caption 的模块别名）
            if _e.get("kind") in ("text", "card", "note", "quote") and len(_txt) > _cap_max and not _e.get("reveal"):
                p.hint(f"{sid}: 纸上「{_txt[:12]}…」有 {len(_txt)} 字——纸上只写关键词和数字（每处 ≤{_cap_max} 字），整句交给旁白")
        sfx = []
        for e in els:
            if e["kind"] == "number":
                sfx.append({"event": "pop", "at": e["at"] + 30})
            elif e["kind"] == "bar" and e["idx"] == 0:
                sfx.append({"event": "chart", "at": e["at"] + 22})
            elif e["kind"] == "codebox":
                sfx.append({"event": "highlight", "at": e["at"] + 6})
        for fk in focus_out:
            if fk["cam"]:
                sfx.append({"event": "highlight", "at": fk["at"], "_push": True})
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
        beats = [{"cue": ci_, "offset": 0} for ix in sh["line_cues"] for ci_ in ix]
        # beats 不能只数字幕：镜内元素也是真画面变化（大字写完、盖章、放上手绘小图）。
        # 只看 cue 时，S1 这种「一句字幕读 3 秒、画面里却连着三个动作」的开场会被判成
        # 「前 3 秒只有 2 个节拍」（validate-opening O4 直接 P0），而屏幕上的画面明明是动的。
        # 这里把镜内元素的 at（本地帧）补成一拍：挂到「它前一条字幕」上，offset 取与那句起点的差。
        # 不能一律挂首个 cue —— 元素若在第二句才出现，offset 就会大过那一句的时长，
        # validate-presentation 会判「元素在旁白讲完后才出现 = 与台词脱节」（P0）。
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
        # 排序键必须落在「绝对帧」上：用 ms 排会因为 offset 是帧、start_ms 是毫秒而错序。
        # 统一先换成绝对帧再排。
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
        # 不推不扫的镜，路径在这里定死（前面已跳过推近、招牌镜、收束慢推，不留假的自动修记录）：
        # 线稿镜只做 1.00→1.03 的慢推——线稿在画面边上，任何 >1.05 的缩放都会把它顶出画框；
        # 其余冻结在一帧（只写 drift:"none" 不够：有 path 时引擎直接走 pathCamAt）。静止片的动效只来自笔画、压章、翻页、逐字。
        # 路径最终自检：严格递增、不超缩放/平移安全窗、不切 anchor；任一越界退回安全全景
        clean_path = []
        for pk in path:
            s_val = max(1.0, min(ZOOM_MAX, float(pk["s"])))
            lx, ly = clamp_look(float(pk["x"]), float(pk["y"]), s_val)
            at_val = max(0, min(dur, int(pk["at"])))
            if clean_path and at_val <= clean_path[-1]["at"]:
                continue
            cand_k = {"at": at_val, "x": round(lx, 1), "y": round(ly, 1), "s": round(s_val, 3)}
            if in_frame(U, (cand_k["x"], cand_k["y"]), cand_k["s"]):
                clean_path.append(cand_k)
        if not clean_path or clean_path[0]["at"] != 0:
            clean_path = [{"at": 0, **over}]
        path = clean_path
        if frozen:
            path = [{"at": 0, "x": 960.0, "y": 540.0, "s": 1.0}] + (
                [{"at": max(31, dur - 12), "x": 960.0, "y": 540.0, "s": 1.03}] if sh.get("sketch") else [])
        if still_film or sh.get("sketch"):
            focus_out = []
        intent_now = path_intent(path)
        recent_intents.append(intent_now)
        cam = {"intent": intent_now}
        tr_sh = sh.get("transition")
        tr_top = story.get("transition")
        if k == 0:
            tr = "auto"
        elif tr_sh:
            tr = str(tr_sh)
        elif tr_top:
            tr = str(tr_top)
        elif sh.get("first_in_chapter") or IS_HANDMADE or sh["layout"] == "page":
            tr = "auto"
        else:
            tr = "slide" if sh["layout"] in ("flow", "compare", "bars") else "fade"
        drift_dir = "none" if (still_film or frozen or intent_now in ("pull-back", "pan-follow", "still")) else None
        rec = {"id": sid, "chapter": sh["chapter"], "skeleton": skel, "layout": f"{sh['layout']}{('-' + sh['variant']) if sh['variant'] else ''}",
               "from": frm, "to": to, "cues": [sh["line_cues"][0][0], sh["line_cues"][-1][-1]],
               "media": MEDIA[sh["layout"]], "live": ["AutoShot"], "camera": cam, "anchor": a, "contentBand": BAND,
               "hero": {"name": sh["layout"], "size": int(max(U["w"], U["h"]) * 0.5), "kind": "text"}, "zones": 3, "bottomFill": True,
               "cover": "paper", "entry": "build", "beats": beats, "move": moves[k],
               "evidence": "AutoShot", "hold": 40, "noMisconception": True, "why": "auto 版式：内容由 story.json 给出",
               "transition": tr,
               "cinema": {"drift": "none", "fit": "none", "path": path,
                          **({"driftDir": drift_dir} if drift_dir is not None else {}),
                          **({"still": True} if still_film else {})}, "sfxEvents": sfx}
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
        # 冷开：片子第 0 帧就要有主体（references/director.md#narrative-hook；validate-opening O6 手作皮肤 P0、
        # 组件皮肤 P1）。第一镜最先出现的那个元素（题眼）提前到镜头开始前就已落定（at 为负，组件按 at 插值、
        # clamp 后第 0 帧即完整），其余元素照常按台词出现。组件皮肤同样适用：第 0 帧是空背景，
        # 等于开场半秒的黑屏。
        if k == 0:
            lead = min((e for e in els if e["kind"] not in ("arrow", "timer")), key=lambda e: e.get("at") or 0, default=None)
            if lead is not None and (lead.get("at") or 0) >= 0:
                lead["at"] = -COLD_OPEN_SETTLE
        out_shots.append(rec)
        story_ts[sid] = {"layout": sh["layout"], "variant": sh["variant"], "elements": els, "focus": focus_out, "tips": tips,
                         "lines": line_start, "lineEnds": line_end, "think": int(float(sh["content"].get("think", 3)) * FPS) if sh["layout"] == "quiz" else 0,
                         "custom": sh["custom"], "icons": icons}
        if sk_out:
            story_ts[sid]["sketch"] = sk_out
        if ann_out:
            story_ts[sid]["annotate"] = ann_out
    thin_push_sfx(out_shots)
    # 节奏：快慢交替（同速 3 镜连排 → 提示）
    tempo = ["fast" if (s["to"] - s["from"]) < 150 else "slow" for s in out_shots]
    for i in range(2, len(tempo)):
        if tempo[i] == tempo[i - 1] == tempo[i - 2]:
            p.hint(f"{out_shots[i]['id']}: 连续 3 镜都是 {tempo[i]} 节奏 —— 中间换一镜 number / quiz（快）或 code / flow（慢）")
    # 每分钟图标
    mins = max(1.0, total / FPS / 60)
    ic = sum(v["icons"] for v in story_ts.values())
    if ic / mins > ICON_BUDGET_MIN:
        p.hint(f"全片图标 {ic} 个 / {mins:.1f} 分钟 > 每分钟 {ICON_BUDGET_MIN} 个 —— 删掉装饰性图标")
    return out_shots, story_ts, total


def thin_push_sfx(out_shots: list[dict]) -> None:
    """推近带出的高亮音效服从稀疏密度：离同镜别的音效太近就并进去，会让任一 10 秒窗口超过上限就不发。

    版式自带的音效（数字落定、图表起笔、对比揭晓）原样保留；推近音效按时间先后逐个判断。
    """
    fixed = sorted(sh["from"] + e["at"] for sh in out_shots for e in sh.get("sfxEvents") or [] if not e.get("_push"))
    kept: list[int] = []
    for sh in out_shots:
        if not sh.get("sfxEvents"):
            continue
        own = [sh["from"] + e["at"] for e in sh["sfxEvents"] if not e.get("_push")]
        keep_list = []
        for e in sh["sfxEvents"]:
            if not e.pop("_push", False):
                keep_list.append(e)
                continue
            t = sh["from"] + e["at"]
            if any(abs(t - o) <= SFX_MERGE_F for o in own):
                continue
            times = sorted(fixed + kept + [t])
            if any(sum(1 for u in times if w <= u < w + SFX_WINDOW_F) > SFX_SPARSE_MAX
                   for w in times if w <= t < w + SFX_WINDOW_F):
                continue
            kept.append(t); own.append(t)
            keep_list.append(e)
        sh["sfxEvents"][:] = keep_list


# ---------------------------------------------------------------- acts / reprises / draw
# 动作与复现层在 story_acts.py：@L1.3 换算、两套动词表、content.ink.acts 校验、
# 跨镜复现判定、线稿规格的构建期核对都归它（lay_page 直接调 resolve_ink_acts / check_draw）。
# 帧号换算只走 story_time.frame；本文件不定义 FPS / frame。


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


def _is_spoken_ch(ch: str) -> bool:
    return ch.isalnum() or ch in "0123456789.%+-" or "\u4e00" <= ch <= "\u9fff"


def retime_to_tts(comp: dict, words: list[dict], p: "Problems") -> bool:
    """把字幕 cues 与镜头起点重排到 TTS 的真实词级时间上。

    优先按字符精确匹配；若因数字/标点/英文缩写出现少量失配，则用 SequenceMatcher 按可发音字符对齐，
    对齐率 ≥ 0.90 时线性插值未对上的标点/字符并记录自动修；低于 0.90 时整片安全退回并提示。
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
    flat = timeline
    if not flat:
        return False
    idx = 0
    old_start: dict[int, int] = {}
    cues = comp["cues"]
    segs: dict[int, list] = {}
    exact_ok = True
    mismatch_ci = 0
    for ci, cue in enumerate(cues):
        chars = [c for c in cue["text"] if not c.isspace()]
        if not chars:
            continue
        seg = flat[idx:idx + len(chars)]
        if [c for c, _, _ in seg] != chars:
            exact_ok = False
            mismatch_ci = ci
            break
        segs[ci] = seg
        idx += len(chars)
    if not exact_ok:
        all_chars: list[tuple[int, str]] = [
            (ci, ch) for ci, cue in enumerate(cues) for ch in cue["text"] if not ch.isspace()
        ]
        spoken_idx = [i for i, (_, ch) in enumerate(all_chars) if _is_spoken_ch(ch)]
        heard = [(ch, st, en) for (ch, st, en) in flat if _is_spoken_ch(ch)]
        if not spoken_idx or not heard:
            p.hint(
                f"TTS 词表与第 {mismatch_ci + 1} 句字幕对不上（音频说的字与字幕文本不一致）——"
                f"字幕/镜头沿用原有时序。修法：让 narration.txt 与字幕同文，或重跑 tts。"
            )
            return False
        a_str = "".join(all_chars[i][1] for i in spoken_idx)
        b_str = "".join(h[0] for h in heard)
        times: dict[int, tuple[int, int]] = {}
        for blk in difflib.SequenceMatcher(None, a_str, b_str, autojunk=False).get_matching_blocks():
            for k in range(blk.size):
                _, s, e = heard[blk.b + k]
                times[spoken_idx[blk.a + k]] = (s, e)
        ratio = len(times) / len(spoken_idx)
        if ratio < 0.90:
            p.hint(
                f"TTS 词表与第 {mismatch_ci + 1} 句字幕对不上（匹配率 {ratio:.0%} < 90%）——"
                f"字幕/镜头沿用原有时序。修法：让 narration.txt 与字幕同文，或重跑 tts。"
            )
            return False
        first_sp: dict[int, int] = {}
        last_sp: dict[int, int] = {}
        for idx_a, (ci_a, ch_a) in enumerate(all_chars):
            if _is_spoken_ch(ch_a):
                if ci_a not in first_sp:
                    first_sp[ci_a] = idx_a
                last_sp[ci_a] = idx_a
        total_audio_ms = max((en for _, _, en in flat), default=0)
        aligned_flat: list[tuple[int, str, int, int]] = []
        i, prev_end_ms = 0, 0
        while i < len(all_chars):
            if i in times:
                s, e = times[i]
                s = max(s, prev_end_ms)
                e = max(e, s)
                aligned_flat.append((all_chars[i][0], all_chars[i][1], s, e))
                prev_end_ms = e
                i += 1
                continue
            j = i
            while j < len(all_chars) and j not in times:
                j += 1
            nxt = max(prev_end_ms, times[j][0] if j < len(all_chars) else total_audio_ms)
            # 先把句末标点（位于本句最后一个可读字符之后）紧贴前一音结尾，不吞掉句间静音间隔
            while i < j and not _is_spoken_ch(all_chars[i][1]) and all_chars[i][0] in last_sp and i > last_sp[all_chars[i][0]]:
                p_end = min(nxt, prev_end_ms + 1)
                aligned_flat.append((all_chars[i][0], all_chars[i][1], prev_end_ms, p_end))
                prev_end_ms = p_end
                i += 1
            # 再把句首符号/标点（位于本句第一个可读字符之前）收集出来，紧贴下一音起点
            lead_buf: list[int] = []
            while j > i and not _is_spoken_ch(all_chars[j - 1][1]) and all_chars[j - 1][0] in first_sp and (j - 1) < first_sp[all_chars[j - 1][0]]:
                lead_buf.append(j - 1)
                j -= 1
            lead_buf.reverse()
            if i < j:
                span_hi = max(prev_end_ms, nxt - len(lead_buf))
                n = j - i
                for k in range(n):
                    s = prev_end_ms + (span_hi - prev_end_ms) * k // n
                    e = prev_end_ms + (span_hi - prev_end_ms) * (k + 1) // n
                    aligned_flat.append((all_chars[i + k][0], all_chars[i + k][1], s, max(s, e)))
                prev_end_ms = span_hi
            for pos in lead_buf:
                l_start = max(prev_end_ms, nxt - 1)
                aligned_flat.append((all_chars[pos][0], all_chars[pos][1], l_start, nxt))
                prev_end_ms = nxt
            i = j + len(lead_buf)
        segs = {}
        for ci, ch, st, en in aligned_flat:
            segs.setdefault(ci, []).append((ch, st, en))
        p.fix(f"TTS 词表存在少量数字/标点差异，已按可读音字流兜底对齐（匹配率 {ratio:.0%}）")
    for ci, seg in segs.items():
        cue = cues[ci]
        old_start[ci] = int(cue["start_ms"])
        cue["words"] = [{"part": c, "start": st, "end": en} for c, st, en in seg]
        cue["start_ms"], cue["speech_end_ms"], cue["reveal_end_ms"] = seg[0][1], seg[-1][2], seg[-1][2]
        cue["start"], cue["speech_end"], cue["reveal_end"] = (
            round(cue["start_ms"] / 1000, 3), round(cue["speech_end_ms"] / 1000, 3), round(cue["reveal_end_ms"] / 1000, 3))
    # 镜头切点落在句间真实停顿中点：绝不切在前一句句尾发声完成之前，也不晚于下一句起音
    prev = 0
    prev_end_ms = 0
    for k_sh, sh in enumerate(comp["shots"]):
        ix = [ci_ for grp in (sh.get("line_cues") or []) for ci_ in grp]
        cur_end_ms = max((int(cues[ci_]["speech_end_ms"]) for ci_ in ix), default=prev_end_ms)
        if k_sh == 0:
            if int(sh.get("start_ms", 0)) == 0:
                sh["start_ms"] = 0
            elif ix and ix[0] in old_start:
                ci = ix[0]
                sh["start_ms"] = max(0, int(sh["start_ms"]) + (int(cues[ci]["start_ms"]) - old_start[ci]))
        elif ix and ix[0] in old_start:
            ci = ix[0]
            cur_start_ms = int(cues[ci]["start_ms"])
            if cur_start_ms - prev_end_ms >= 100:
                target_cut = min(cur_start_ms - 60, max(prev_end_ms + 80, (prev_end_ms + cur_start_ms) // 2))
                sh["start_ms"] = max(prev + 1, prev_end_ms, min(cur_start_ms, target_cut))
            else:
                sh["start_ms"] = max(prev + 1, prev_end_ms, int(sh["start_ms"]) + (cur_start_ms - old_start[ci]))
        else:
            sh["start_ms"] = max(prev + 1, prev_end_ms, int(sh.get("start_ms", prev + 1)))
        # 同步重算每镜关键词的时间戳 terms[].ms（漏算会让配音后中后段高亮/推近错拍）
        for tm in sh.get("terms") or []:
            ci = tm.get("cue")
            if isinstance(ci, int) and 0 <= ci < len(cues) and cues[ci].get("words"):
                cws = cues[ci]["words"]
                txt = str(cues[ci].get("text") or "")
                wi = sum(1 for ch in txt[:int(tm.get("start", 0))] if not ch.isspace())
                wi = max(0, min(wi, len(cws) - 1))
                tm["ms"] = int(cws[wi]["start"])
        prev = int(sh["start_ms"])
        prev_end_ms = max(prev_end_ms, cur_end_ms)
    last_end = max((c["speech_end_ms"] for c in cues), default=0)
    # 有真实音频时间就**以它为准**（可以缩短）：compose 的估算是按 4.5 字/秒排的，
    # 而口播的实际语速常常到 5 字/秒以上，照估算值播出会留十几秒画面空转。
    if last_end:
        comp["total_ms"] = last_end + END_TAIL_F * 1000 // FPS
    p.hint(f"按 TTS 词级时间重排：{len(cues)} 句字幕 / {len(comp['shots'])} 镜（时间来自 audio/narration.meta.json）")
    return True


# ---------------------------------------------------------------- output
# 写盘层在 story_output.py：manifest / src/*.ts(x) / media / 旁白契约。这里只 import 回来当门面。

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("story")
    ap.add_argument("project")
    ap.add_argument("--report")
    ap.add_argument("--check", action="store_true", help="只检查不写盘")
    # 读速可配置（加权字/秒，1–9）。也可在 story.json 顶层写 "cps"。缺省 4.5（组件路线的既有速度）。
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
    # treatment.signature_shot 决定哪一镜真推；没有 treatment 就是 None，行为不变
    global TREATMENT, TREATMENT_MOVES, FIRST_LEAD_MS, IS_HANDMADE
    TREATMENT, TREATMENT_MOVES, IS_HANDMADE, FIRST_LEAD_MS = {}, {}, False, 700
    _act = Path(a.project) / "src" / "theme" / "active.ts"
    try:
        _m = re.search(r"from\s+'\./(\w+)'", _act.read_text(encoding="utf-8"))
        if _m and _m.group(1) in HANDMADE_SKINS:
            FIRST_LEAD_MS = FIRST_LEAD_MS_HANDMADE
            IS_HANDMADE = True
    except OSError:
        pass
    tp = Path(a.project) / "manifests" / "treatment.json"
    try:
        TREATMENT = json.loads(tp.read_text(encoding="utf-8")) if tp.is_file() else {}
    except (ValueError, OSError):
        TREATMENT = {}
    # 模板自带的是示例片的 treatment；组件路线没改就留着时，不把它的运镜套到本片上。
    # 作者自己写的 treatment 两条路线都照用。
    TREATMENT_IS_TEMPLATE = (not IS_HANDMADE) and str(TREATMENT.get("$about") or "").startswith("模板示例片")
    if TREATMENT_IS_TEMPLATE:
        TREATMENT = {}
    sig0 = TREATMENT.get("signature_shot")   # build 生成前判定推不进时会改选，落盘时写回
    # treatment.shots[].move → {镜号: 运镜}：只有 still 会改路径（见 build() 的 frozen_ids）；其余运镜按真实路径记，validate-treatment 对照
    TREATMENT_MOVES = {s.get("id"): s.get("move") for s in (TREATMENT.get("shots") or [])
                       if isinstance(s, dict) and s.get("id") and s.get("move")}
    p = Problems()
    if TREATMENT_IS_TEMPLATE:
        p.hint("manifests/treatment.json 还是模板示例片的（GitHub 三部曲），本片不套用它的运镜 —— 要指定运镜就改成本片自己的 treatment")
    cap_mode = str((story.get("captions") or {}).get("mode", "line")).lower()
    if cap_mode not in ("line", "typewriter", "type"):
        p.err(f"captions.mode={cap_mode!r} 不是有效值 —— 用 \"line\"（默认，整行出现）或 \"typewriter\"（逐字打出）。")
    if story.get("$route") == "handwritten-craft" and not story.get("chapters"):
        print("  ✗ 这是手写场景路线的蓝图（$route: handwritten-craft），不是 story.json：照它的 $components 写 scenes.tsx；"
              "auto 路线请照 examples/recipes/*.story.json 写")
        return 1
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
        if TREATMENT.get("signature_shot") != sig0:
            tp.write_text(json.dumps(TREATMENT, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _dst_story = Path(a.project) / "story.json"
        if Path(a.story).resolve() != _dst_story.resolve():
            _dst_story.write_text(Path(a.story).read_text(encoding="utf-8"), encoding="utf-8")
        if story.get("media"):
            write_media(story, Path(a.project))
    return 0


if __name__ == "__main__":
    sys.exit(main())
