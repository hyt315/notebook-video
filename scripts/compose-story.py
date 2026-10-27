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

FPS = 30
CPS = 4.5                      # 中文朗读 / 阅读速度：4–5 字/秒，取 4.5
CHAR_MS = 1000 / CPS           # ≈ 222 ms
COMMA_MS, STOP_MS = 150, 300   # 句中逗号 / 句末停顿
LINE_GAP_MS = 220              # 同镜两行之间
SHOT_GAP_MS = 320              # 镜与镜之间
CHAPTER_BREATH_MS = SHOT_GAP_MS  # 不再有章节呼吸 / 章节卡（保持默认组件风格）
FIRST_LEAD_MS = 700            # 片头
END_TAIL_F = 42                # 片尾
MAX_CHARS = 16
MIN_FONT = 32                  # 手机可读地板（设计像素，1920 宽）
TYPE = {"display": 76, "title": 46, "body": 36}  # 三档字号；hero 数字另算（同镜仍 ≤3 种）
BAND = {"x": 200, "y": 214, "w": 1520, "h": 630}  # 内容带（页眉下、字幕上）
SAFE = (130, 196, 1790, 862)   # 屏幕安全框：推近后元素必须完整落在这里（顶 178 有遮罩、底是字幕）
ZOOM_MAX, ZOOM_MIN_FOCUS = 1.32, 1.08
PUNCT = "，。！？；：、,.!?;:"
TAIL_PUNCT_RE = re.compile(r"[，。！？；：、,.!?;:\s]+$")
TERM_RE = re.compile(r"\{\{([^}|]+)(?:\|([^}]+))?\}\}")
LAYOUTS = ("statement", "define", "number", "bars", "compare", "code", "flow", "list", "quiz", "custom", "media")
# 每种版式可以贴的骨架标签（validate-composition 要求相邻不同）：首选在前
SKELETONS = {"statement": ["Stage", "Zoom"], "define": ["Split", "Stage"], "number": ["Stage", "Zoom"],
             "bars": ["Zoom", "Stage"], "compare": ["Split", "Stage"], "code": ["Zoom", "Stage"],
             "flow": ["Corridor", "Stage"], "list": ["Stage", "Corridor"], "quiz": ["Split", "Stage"], "custom": ["Stage", "Zoom"], "media": ["Zoom", "Stage"]}
MEDIA = {"statement": ["text"], "define": ["text"], "number": ["metric", "text"], "bars": ["chart", "metric"],
         "compare": ["metric", "text"], "code": ["code", "text"], "flow": ["graphic", "text"], "list": ["text"],
         "quiz": ["text", "graphic"], "custom": ["graphic", "text"], "media": ["graphic", "console"]}
INTENTS = {"statement": "establish", "define": "push-in", "number": "push-in", "bars": "reveal", "compare": "pull-back",
           "code": "push-in", "flow": "reveal", "list": "establish", "quiz": "push-in", "custom": "reveal", "media": "push-in"}
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
def is_wide(ch: str) -> bool:
    return bool(re.match(r"[\u2e80-\u9fff\u3000-\u303f\uff00-\uffef]", ch))


def text_w(s: str, size: float, mono=False) -> float:
    if mono:
        return sum((1.0 if is_wide(c) else 0.6) for c in s) * size
    return sum((1.0 if is_wide(c) else (0.3 if c == " " else 0.56)) for c in s) * size


def units(s: str) -> float:
    """朗读单位：一个汉字 1；连续的英文/数字每 2 个字符算 1（至少 1）。"""
    n = 0.0
    for tok in re.findall(r"[A-Za-z0-9.%+\-_/]+|[\u2e80-\u9fff]|.", s):
        if re.match(r"[A-Za-z0-9]", tok):
            n += max(1.0, len(tok) / 2)
        elif is_wide(tok) and tok not in PUNCT:
            n += 1
    return n


def cap_chars(s: str) -> int:
    return len(TAIL_PUNCT_RE.sub("", re.sub(r"\s+", "", s)))


def line_len(s: str) -> float:
    """两套门禁口径取严：CaptionFitGate 逐字计（去句末标点）与 validate-presentation 的加权字数（CJK 与全角标点 1、ASCII 0.5）。"""
    w = sum(1.0 if ord(ch) > 0x2E80 else 0.5 for ch in re.sub(r"\s+", "", s))
    return max(cap_chars(s), w)


def wrap(text: str, size: float, maxw: float, mono=False) -> list[str]:
    """按宽度折行：中文按字、英文按词，不拆开英文单词 / 数字。"""
    toks = re.findall(r"[A-Za-z0-9.%+\-_/@()']+|\s+|.", text)
    lines, cur = [], ""
    for t in toks:
        if t.isspace() and not cur:
            continue
        if text_w(cur + t, size, mono) <= maxw or not cur:
            cur += t
        else:
            # 行首不放标点
            if t in PUNCT:
                cur += t
                continue
            # 优先在最近的标点后断行（不把「存起来」劈成「存起 / 来」）
            k = max(cur.rfind(q) for q in "，、；：,;:")
            if not mono and k >= 0 and len(cur) - k - 1 <= 6 and k >= len(cur) * 0.45:
                lines.append(cur[:k + 1].rstrip())
                cur = cur[k + 1:].lstrip() + t
                continue
            lines.append(cur.rstrip())
            cur = t.lstrip()
    if cur.strip():
        lines.append(cur.rstrip())
    # 避免孤字：末行只剩 ≤2 个字时，从上一行挪字过来（中文排版的基本礼貌）
    if len(lines) >= 2 and len(TAIL_PUNCT_RE.sub("", lines[-1])) <= 2 and not mono:
        prev = lines[-2]
        mt = re.search(r"([A-Za-z0-9.%+\-_/@()']+|[^\sA-Za-z0-9]{1,2})\s*$", prev)
        k = len(prev) - mt.start() if mt else 2
        if k < len(prev):
            lines[-2], lines[-1] = prev[:-k].rstrip(), prev[-k:].lstrip() + lines[-1]
    return lines or [""]


def fit_text(p: Problems, where: str, text: str, size: int, maxw: float, max_lines: int, lh=1.3, mono=False):
    """先换行，再降字号（不低于 MIN_FONT），仍放不下 → 报错并给出可容纳的字数。"""
    s = size
    while True:
        ls = wrap(text, s, maxw, mono)
        if len(ls) <= max_lines:
            if s != size:
                p.fix(f"{where}: 字号 {size}→{s} 以放进 {max_lines} 行")
            w = max(text_w(l, s, mono) for l in ls)
            return ls, s, w, len(ls) * s * lh
        if s <= MIN_FONT:
            cap = int(maxw / (MIN_FONT * 1.0)) * max_lines
            p.err(f"{where}: 「{text[:14]}…」在 {MIN_FONT}px 下仍超过 {max_lines} 行 —— 请删到约 {cap} 个汉字以内，或拆成两镜")
            return ls[:max_lines], s, maxw, max_lines * s * lh
        s = max(MIN_FONT, s - 2)


# ---------------------------------------------------------------- captions
def parse_line(raw: str):
    """'{{缓存|L3}}让结果复用' → clean text + terms[(start_char, text, target)]"""
    out, terms, pos = "", [], 0
    for m in TERM_RE.finditer(raw):
        out += raw[pos:m.start()]
        terms.append({"start": len(out), "text": m.group(1).strip(), "target": (m.group(2) or "").strip() or None})
        out += m.group(1).strip()
        pos = m.end()
    out += raw[pos:]
    return out, terms


# 断点规则与 validate-semantic-breaks 同一份（build-semantic-captions.py 里的 BudouX + 避头尾 + ASCII 词内不断）。
# 找得到 BudouX（工程 node_modules）就用它挑断点，保证拆出来的行一定过语义断点门禁（弱模型实测补上的）。
_RULE = {"mod": None, "node": None, "root": None, "cache": {}}


def setup_break_rule(project: Path) -> None:
    import importlib.util, shutil
    src = Path(__file__).with_name("build-semantic-captions.py")
    spec = importlib.util.spec_from_file_location("_nv_break_rule", src)
    if spec is None or spec.loader is None:
        return
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        return
    _RULE["mod"] = mod
    _RULE["node"] = shutil.which("node") or shutil.which("node.exe")
    try:
        _RULE["root"] = mod.find_budoux_root(None, [project, Path(__file__).resolve().parents[1] / "assets" / "lecture-template", Path.cwd()])
    except Exception:
        _RULE["root"] = None


def legal_breaks(text: str):
    """text（含空格）里允许断开的下标集合；规则模块不可用时返回 None（退回本地启发式）。"""
    m = _RULE["mod"]
    if m is None:
        return None
    norm = re.sub(r"\s+", "", text)
    if norm not in _RULE["cache"]:
        legal = m.punctuation_breaks(norm)
        if _RULE["root"] and _RULE["node"]:
            try:
                legal |= m.budoux_breaks(_RULE["node"], _RULE["root"], norm)
            except Exception:
                pass
        legal -= m.ascii_interior(norm)
        legal -= m.head_tail_blocked(norm)
        _RULE["cache"][norm] = legal
    legal = _RULE["cache"][norm]
    out, k = set(), 0
    for i, ch in enumerate(text):
        if k in legal and i > 0 and not text[i - 1].isspace():
            out.add(i)
        if not ch.isspace():
            k += 1
    # 空格后的位置等价于空格前
    for i, ch in enumerate(text):
        if ch.isspace() and i in out:
            pass
    return {i + (1 if i < len(text) and text[i].isspace() else 0) for i in out}


def split_caption(text: str, terms: list, protected: list[str]):
    """>16 字的字幕在合法断点劈开：优先标点，其次最靠近中点的「安全位置」（不在术语 / 英文 / 数字 / 保护短语里）。"""
    if line_len(text) <= MAX_CHARS:
        return [(text, terms)]
    banned = set()
    for t in terms:
        banned.update(range(t["start"] + 1, t["start"] + len(t["text"])))
    for ph in protected:
        for m in re.finditer(re.escape(ph), text):
            banned.update(range(m.start() + 1, m.end()))
    for m in re.finditer(r"[A-Za-z0-9.%_\-]+", text):
        banned.update(range(m.start() + 1, m.end()))
    n = len(text)
    legal = legal_breaks(text)
    ok = (lambda i: i in legal) if legal is not None else (lambda i: True)
    cands = [i + 1 for i, ch in enumerate(text[:-1]) if ch in "，、；：,;:" and i + 1 not in banned and ok(i + 1)]
    if not cands:
        cands = [i for i in range(2, n - 1) if i not in banned and text[i] not in PUNCT and ok(i)]
    if not cands:
        cands = [i for i in range(2, n - 1) if i not in banned and text[i] not in PUNCT]
    mid = n / 2
    cut = min(cands, key=lambda i: (line_len(text[:i]) > MAX_CHARS) + (line_len(text[i:]) > MAX_CHARS) * 1 + abs(i - mid) / n)
    a, b = text[:cut], text[cut:]
    lead = len(b) - len(b.lstrip())
    b = b.lstrip()
    a = a.rstrip()
    ta = [t for t in terms if t["start"] < cut]
    tb = [{**t, "start": max(0, t["start"] - cut - lead)} for t in terms if t["start"] >= cut]
    return split_caption(a, ta, protected) + split_caption(b, tb, protected)


def tokens(t: str):
    out = []
    for m in re.finditer(r"[A-Za-z0-9.%+\-_/]+|\s+|.", t):
        s = m.group(0)
        if s.isspace():
            if out:
                out[-1] = (out[-1][0] + s, out[-1][1])
            continue
        if s in PUNCT and out:
            out[-1] = (out[-1][0] + s, out[-1][1])
            continue
        out.append((s, m.start()))
    return out


def time_cue(text: str, start_ms: float):
    """返回 words（part/start/end/charStart）与 cue 结束。按 4.5 字/秒；逗号 +150，句末 +300。"""
    words, t = [], start_ms + 60
    for part, cs in tokens(text):
        core = part.rstrip(PUNCT + " ")
        d = CHAR_MS * max(1.0, units(core)) * 0.95
        words.append({"part": part, "start": int(round(t)), "end": int(round(t + d - 10)), "char": cs})
        t += d
        if part.rstrip().endswith(tuple("，、；：,;:")):
            t += COMMA_MS
        elif part.rstrip().endswith(tuple("。！？.!?")):
            t += STOP_MS * 0.4
    return words, int(round(words[-1]["end"]))


# ---------------------------------------------------------------- layout geometry
def el(id_, kind, x, y, w, h, text="", size=0, role="body", appear=0, **kw):
    d = {"id": id_, "kind": kind, "x": round(x, 1), "y": round(y, 1), "w": round(w, 1), "h": round(h, 1),
         "text": text, "size": size, "role": role, "appear": appear}
    d.update(kw)
    return d


def lay_statement(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    els = []
    maxw = 1360
    big = TYPE["display"] - 12  # statement 渲染成默认组件风格的卡片（Callout），不是满屏大字页
    ls, s, w, h = fit_text(p, f"{sid}.text", c["text"], big, maxw, 3, lh=1.32)
    kick = c.get("kicker")
    sub = c.get("sub")
    sub_h = 0
    if sub:
        sls, ss, sw, sub_h = fit_text(p, f"{sid}.sub", sub, TYPE["body"], maxw, 2, lh=1.45)
    total = h + (70 if kick else 0) + (sub_h + 40 if sub else 0)
    y = Y + (H - total) / 2
    left = variant == "left"
    bx = X + 60 if left else X + (W - w) / 2
    if kick:
        kw = text_w(kick, TYPE["body"])
        els.append(el("kicker", "text", bx if left else X + (W - kw) / 2, y, kw, TYPE["body"] * 1.3, kick, TYPE["body"], "muted", c.get("kickerAt", 0)))
        y += 70
    cw = min(W - 80, max(w + 120, 1080))
    cx = X + 40 if left else X + (W - cw) / 2
    els.append(el("text", "card", cx, y - 40, cw, h + 80, c["text"], s, "display", 0, lines=ls, align="left" if left else "center", lh=1.32, pad=40))
    y += h + 40
    if sub:
        sx = bx if left else X + (W - sw) / 2
        els.append(el("sub", "text", sx, y, sw, sub_h, sub, ss, "muted", c.get("subAt", 1), lines=sls, align="left" if left else "center", lh=1.45))
    return els


def lay_define(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    term = c["term"]
    ts = 104
    tw = text_w(term, ts)
    if tw > 620:
        ts = max(64, int(ts * 620 / tw)); tw = text_w(term, ts)
    ls, s, w, h = fit_text(p, f"{sid}.definition", c["definition"], TYPE["title"], 780, 4, lh=1.45)
    ex = c.get("example")
    els = []
    lx, rx = (X + 40, X + 720) if variant != "mirror" else (X + 900, X + 40)
    y0 = Y + 120
    els.append(el("term", "text", lx, y0, tw, ts * 1.2, term, ts, "display", 0))
    if c.get("reading"):
        els.append(el("reading", "text", lx, y0 + ts * 1.25 + 10, text_w(c["reading"], TYPE["body"]), TYPE["body"] * 1.3, c["reading"], TYPE["body"], "muted", 0))
    els.append(el("definition", "card", rx, y0, 800, h + 60, c["definition"], s, "body", c.get("definitionAt", 0), lines=ls, lh=1.45, pad=30))
    if ex:
        els_, es, ew, eh = fit_text(p, f"{sid}.example", ex, TYPE["body"], 760, 2, lh=1.45)
        els.append(el("example", "quote", rx, y0 + h + 100, 800, eh + 40, ex, es, "muted", c.get("exampleAt", 1), lines=els_, lh=1.45, pad=20))
    return els


def lay_number(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    val = float(c["value"])
    dec = int(c.get("decimals", 0 if float(val).is_integer() else 1))
    txt = f"{c.get('prefix', '')}{val:.{dec}f}"
    size = 230
    unit = c.get("unit", "")
    nw = text_w(txt, size) * 0.98 + text_w(unit, size * 0.42)
    if nw > 820:
        size = int(size * 820 / nw); nw = 820
    notes = c.get("notes") or []
    left = variant != "mirror"
    nx = X + 40 if left else X + W - nw - 40
    ny = Y + 110
    els = [el("number", "number", nx, ny, nw, size * 1.0, txt, size, "hero", 0, value=val, decimals=dec,
              prefix=c.get("prefix", ""), unit=unit, from_=float(c.get("from", 0)), tone=c.get("tone", "orange"))]
    if c.get("label"):
        lls, ls_, lw, lh_ = fit_text(p, f"{sid}.label", c["label"], TYPE["title"], 800, 1)
        els.append(el("label", "text", nx, ny + size * 1.05 + 24, lw, lh_, c["label"], ls_, "body", 0))
    rx = X + 960 if left else X + 40
    y = Y + 140
    for i, n in enumerate(notes[:3]):
        nls, ns, nw2, nh = fit_text(p, f"{sid}.notes[{i}]", n, TYPE["body"], 520, 2, lh=1.4)
        els.append(el(f"note{i + 1}", "note", rx, y, 560, nh + 28, n, ns, "body", c.get("notesAt", [0, 1, 2])[i] if isinstance(c.get("notesAt"), list) and i < len(c["notesAt"]) else min(i, 2), lines=nls, lh=1.4))
        y += nh + 60
    return els


def lay_bars(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    data = c["data"]
    if not 2 <= len(data) <= 6:
        p.err(f"{sid}: bars 需要 2–6 根柱子（现在 {len(data)}）—— 多了请合并成「其他」或拆镜")
        data = data[:6]
    els = []
    title = c.get("title", "")
    if title:
        tls, ts, tw, th = fit_text(p, f"{sid}.title", title, TYPE["title"], 1300, 1)
        els.append(el("title", "text", X + 40, Y + 4, tw, th, title, ts, "title", 0))
    top, bottom = Y + 130, Y + H - 70
    n = len(data)
    gap = 60
    bw = min(220, (W - 160 - gap * (n - 1)) / n)
    total = bw * n + gap * (n - 1)
    x0 = X + (W - total) / 2
    vmax = max(float(d["value"]) for d in data) or 1
    unit = c.get("unit", "")
    hl = c.get("highlight")
    for i, d in enumerate(data):
        v = float(d["value"])
        bh = max(8, (bottom - top - 60) * v / vmax)
        bx = x0 + i * (bw + gap)
        lab = str(d["label"])
        lsz = TYPE["body"]
        while text_w(lab, lsz) > bw + gap - 10 and lsz > MIN_FONT:
            lsz -= 2
        if text_w(lab, lsz) > bw + gap - 10:
            p.err(f"{sid}: 柱标签「{lab}」太长（{MIN_FONT}px 下宽 {text_w(lab, MIN_FONT):.0f} > {bw + gap - 10:.0f}）—— 缩到 {int((bw + gap - 10) / MIN_FONT)} 个汉字以内")
        vt = f"{v:g}{unit}"
        els.append(el(f"bar:{lab}", "bar", bx - gap / 2 + 4, bottom - bh - 56, bw + gap - 8, bh + 56 + 52, lab, lsz, "accent" if lab == hl else "body", c.get("barsAt", 0),
                      barX=bx, barW=bw, barH=bh, base=bottom, value=v, valueText=vt, idx=i, hot=lab == hl))
    return els


def lay_compare(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    mode = c.get("mode", "split")
    els = []

    def panel(key, side, x, w, appear):
        d = c[side]
        y = Y + 40
        parts = []
        tls, ts, tw, th = fit_text(p, f"{sid}.{side}.title", d.get("title", "之前" if side == "before" else "之后"), TYPE["title"], w - 60, 1)
        hh = th + 30
        if d.get("value") is not None:
            hh += 150
        items = d.get("items") or []
        ih = []
        for i, it in enumerate(items[:4]):
            ils, isz, iw, iht = fit_text(p, f"{sid}.{side}.items[{i}]", it, TYPE["body"], w - 90, 2, lh=1.35)
            ih.append((ils, isz, iht))
            hh += iht + 22
        return el(key, "panel", x, y, w, max(hh + 70, 300), d.get("title", ""), TYPE["title"], "body", appear,
                  side=side, title=d.get("title", "之前" if side == "before" else "之后"), value=d.get("value"), unit=d.get("unit", ""),
                  decimals=int(d.get("decimals", 0)), items=[{"lines": a, "size": b} for a, b, _ in ih], tone=d.get("tone", "orange" if side == "before" else "green"))

    if mode == "morph":
        e1 = panel("before", "before", X + 360, 800, 0)
        e2 = panel("after", "after", X + 360, 800, c.get("morphLine", 1))
        e2["y"] = e1["y"]
        h = max(e1["h"], e2["h"]); e1["h"] = e2["h"] = h
        e1["morphTo"] = "after"; e2["morph"] = True
        els += [e1, e2]
    else:
        w = 660
        e1 = panel("before", "before", X + 40, w, 0)
        e2 = panel("after", "after", X + W - w - 40, w, c.get("afterLine", 1))
        h = max(e1["h"], e2["h"]); e1["h"] = e2["h"] = h
        els += [e1, e2, el("arrow", "arrow", X + 40 + w + 20, Y + 40 + h / 2 - 30, W - 2 * w - 120, 60, "", 0, "decor", c.get("afterLine", 1))]
    if c.get("verdict"):
        vls, vs, vw, vh = fit_text(p, f"{sid}.verdict", c["verdict"], TYPE["body"], 1200, 1)
        vy = max(e["y"] + e["h"] for e in els if e["kind"] == "panel") + 34
        els.append(el("verdict", "text", X + (W - vw) / 2, vy, vw, vh, c["verdict"], vs, "accent", c.get("verdictLine", 2)))
    return els


def lay_code(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    lines = c["code"].rstrip("\n").split("\n")
    size = TYPE["body"]
    note = c.get("note")
    longest = max(len(l.expandtabs(4)) for l in lines)
    # 代码框按最长行定宽（不留大片空白），右侧注释拿走剩下的宽度
    boxw = min(1300 if not note else 1060, max(760, int(longest * size * 0.6 + 100))) if note else 1300
    while longest * size * 0.6 > boxw - 80 and size > MIN_FONT:
        size -= 2
    if longest * size * 0.6 > boxw - 80:
        p.err(f"{sid}: 代码最长一行 {longest} 字符，{MIN_FONT}px 下放不进 {boxw}px —— 每行请 ≤ {int((boxw - 80) / (MIN_FONT * 0.6))} 字符（折行或删减）")
    lh = size * 1.55
    maxl = int((H - 110) / lh)
    if len(lines) > maxl:
        p.err(f"{sid}: 代码 {len(lines)} 行，屏上最多 {maxl} 行 —— 只保留讲到的那几行（其余用 # ... 代替）")
        lines = lines[:maxl]
    boxh = 90 + len(lines) * lh + 30
    bx, by = X + 20, Y + max(0, (H - boxh) / 2)
    els = [el("code", "codebox", bx, by, boxw, boxh, c.get("title", ""), size, "body", 0, lang=c.get("lang", ""), lh=lh, nlines=len(lines))]
    for i, l in enumerate(lines):
        els.append(el(f"L{i + 1}", "codeline", bx + 30, by + 90 + i * lh, boxw - 60, lh, l, size, "body", 0, n=i + 1))
    if note:
        nwid = X + W - (bx + boxw + 40) - 40
        nls, ns, nw, nh = fit_text(p, f"{sid}.note", note, TYPE["title"], nwid - 50, 4, lh=1.4)
        els.append(el("note", "note", bx + boxw + 40, by + 20, nwid, nh + 50, note, ns, "accent", c.get("noteAt", 1), lines=nls, lh=1.4))
    return els


def lay_flow(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    steps = c["steps"]
    n = len(steps)
    if not 2 <= n <= 5:
        p.err(f"{sid}: flow 需要 2–5 步（现在 {n}）")
        steps = steps[:5]; n = len(steps)
    els = []
    title = c.get("title")
    if title:
        tls, ts, tw, th = fit_text(p, f"{sid}.title", title, TYPE["title"], 1300, 1)
        els.append(el("title", "text", X + 40, Y + 4, tw, th, title, ts, "title", 0))
    arrow = 90
    nw = (W - 80 - arrow * (n - 1)) / n
    ny = Y + 190
    for i, st in enumerate(steps):
        st = st if isinstance(st, dict) else {"label": st}
        lls, ls_, lw, lh_ = fit_text(p, f"{sid}.steps[{i}].label", st["label"], TYPE["title"], nw - 40, 2, lh=1.25)
        hh = lh_ + 60
        nlines = []
        if st.get("note"):
            nlines, ns, nww, nh = fit_text(p, f"{sid}.steps[{i}].note", st["note"], TYPE["body"], nw - 40, 3, lh=1.4)
            hh += nh + 20
        x = X + 40 + i * (nw + arrow)
        els.append(el(f"step{i + 1}", "node", x, ny, nw, max(hh, 200), st["label"], ls_, "accent" if st.get("hot") else "body",
                      st.get("at", min(i, 99)), lines=lls, note=st.get("note", ""), noteLines=nlines, noteSize=TYPE["body"], hot=bool(st.get("hot"))))
        if i:
            els.append(el(f"arrow{i}", "arrow", x - arrow + 10, ny + 70, arrow - 20, 50, "", 0, "decor", st.get("at", min(i, 99))))
    # 统一节点高度
    hmax = max(e["h"] for e in els if e["kind"] == "node")
    for e in els:
        if e["kind"] == "node":
            e["h"] = hmax
    return els


def lay_list(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    items = c["items"]
    if not 2 <= len(items) <= 5:
        p.err(f"{sid}: list 需要 2–5 条（现在 {len(items)}）—— 多了拆成两镜")
        items = items[:5]
    els = []
    y = Y + 10
    title = c.get("title")
    if title:
        tls, ts, tw, th = fit_text(p, f"{sid}.title", title, TYPE["title"], 1300, 1)
        els.append(el("title", "text", X + 80, y, tw, th, title, ts, "title", 0))
        y += th + 46
    rows = []
    for i, it in enumerate(items):
        ils, isz, iw, ih = fit_text(p, f"{sid}.items[{i}]", it, TYPE["title"] if len(items) <= 3 else TYPE["body"], 1200, 2, lh=1.35)
        rows.append((ils, isz, ih, it))
    gap = min(48, (Y + H - y - sum(r[2] + 24 for r in rows)) / max(1, len(rows)))
    for i, (ils, isz, ih, it) in enumerate(rows):
        els.append(el(f"item{i + 1}", "item", X + 80, y, 1320, ih + 24, it, isz, "body", i, lines=ils, lh=1.35, n=i + 1, style=c.get("style", "number")))
        y += ih + 24 + max(16, gap)
    return els


def lay_quiz(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    els = []
    qls, qs, qw, qh = fit_text(p, f"{sid}.question", c["question"], TYPE["title"] + 6, 1200, 2, lh=1.3)
    els.append(el("question", "text", X + 60, Y + 20, qw, qh, c["question"], qs, "title", 0, lines=qls, lh=1.3))
    y = Y + 20 + qh + 50
    for i, o in enumerate(c["options"][:4]):
        ols, os_, ow, oh = fit_text(p, f"{sid}.options[{i}]", o, TYPE["body"], 1000, 1)
        els.append(el(f"opt{i + 1}", "option", X + 60, y, 1100, oh + 36, o, os_, "body", 0, letter="ABCD"[i], correct=i == int(c.get("answer", 0))))
        y += oh + 36 + 22
    els.append(el("timer", "timer", X + 1260, Y + 40, 200, 200, "想一想", TYPE["body"], "accent", 0))
    return els


def lay_custom(p, sid, c, variant):
    if not c.get("component"):
        p.err(f"{sid}: custom 版式需要 content.component（src/custom/ 里注册的组件名）")
    els = []
    for i, e in enumerate(c.get("elements") or []):
        if not all(k in e for k in ("id", "x", "y", "w", "h")):
            p.err(f"{sid}: custom.elements[{i}] 需要 id/x/y/w/h（设计坐标）—— 引擎靠它们做关键词高亮与推近")
            continue
        els.append(el(e["id"], "custom", e["x"], e["y"], e["w"], e["h"], e.get("label", ""), int(e.get("size", TYPE["body"])),
                      e.get("role", "body"), e.get("appear", 0), isText=bool(e.get("isText", True))))
    return els


STORY_MEDIA: dict = {}   # compose() 开头从 story["media"] 填入：id → 条目（含 width/height）


def lay_media(p, sid, c, variant):
    """3.2.0 真实素材：一张截图 / 一段录屏放进 MediaFrame；区域（0–1 相对坐标）变成可被 {{词|区域id}} 点名的元素。"""
    mid = c.get("media")
    m = STORY_MEDIA.get(mid)
    if not m:
        p.err(f"{sid}: media 版式需要 content.media = 顶层 media 列表里的 id（现有：{sorted(STORY_MEDIA) or '无'}）")
        return []
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    chrome = c.get("chrome", "browser")
    ch = {"browser": 46, "window": 40}.get(chrome, 0)
    cap = c.get("caption")
    fw = W - 380 if cap else W - 120
    fx = X + (60 if variant != "mirror" else W - fw - 60)
    fy, fh = Y, H
    iw, ih = m.get("width") or 16, m.get("height") or 9
    vw, vh = fw, fh - ch
    k = min(vw / iw, vh / ih)
    dw, dh = iw * k, ih * k
    ox, oy = fx + (vw - dw) / 2, fy + ch + (vh - dh) / 2
    els = [el("media", "media", fx, fy, fw, fh, mid, 0, "body", 0, media=mid, chrome=chrome,
              region=c.get("region"), isText=False)]
    for r in m.get("focusRegions") or []:
        els.append(el(r["id"], "region", ox + r["x"] * dw, oy + r["y"] * dh, r["w"] * dw, r["h"] * dh, r.get("label", r["id"]), 0, "body",
                      0, isText=False))
    if cap:
        ls, s_, w_, h_ = fit_text(p, f"{sid}.caption", cap, TYPE["title"], 280, 5, lh=1.4)
        cx = fx + fw + 40 if variant != "mirror" else X + 20
        els.append(el("caption", "card", cx, fy + 60, 300, h_ + 60, cap, s_, "body", c.get("captionAt", 0), lines=ls, lh=1.4, pad=24))
    return els


LAY = {"media": lay_media, "statement": lay_statement, "define": lay_define, "number": lay_number, "bars": lay_bars, "compare": lay_compare,
       "code": lay_code, "flow": lay_flow, "list": lay_list, "quiz": lay_quiz, "custom": lay_custom}


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
    size, lh = e["size"], e.get("lh", 1.3)
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
def to_screen(r, look, s):
    return ((r["x"] - look[0]) * s + 960, (r["y"] - look[1]) * s + 540, r["w"] * s, r["h"] * s)


def clamp_look(x, y, s):
    hx, hy = 960 / s, 540 / s
    return (min(1920 - hx, max(hx, x)), min(1080 - hy, max(hy, y)))


def partial_clips(look, s, els):
    """取景窗（屏幕安全框）会切断哪些文字元素：一部分在框内、一部分在框外。"""
    bad = []
    for e in els:
        if e["kind"] in ("arrow", "codebox"):
            continue
        x, y, w, h = to_screen(e, look, s)
        inside = x >= SAFE[0] - 2 and y >= SAFE[1] - 2 and x + w <= SAFE[2] + 2 and y + h <= SAFE[3] + 2
        # 顶部遮罩：y < 140 完全隐去，140–178 是羽化带 → 文字底边必须在 150 以上才算「完全在框外」
        outside = x + w <= 0 or x >= 1920 or y + h <= 150 or y >= 1080
        if not inside and not outside:
            bad.append(e["id"])
    return bad


def frame_rect(r, els, max_s=ZOOM_MAX, min_s=1.0):
    """把矩形 r 取进安全框：先按 r 求最大推近，再逐级回退，直到没有任何文字元素被取景窗切断。"""
    pad = 36
    rw, rh = r["w"] + 2 * pad, r["h"] + 2 * pad
    sw, sh = SAFE[2] - SAFE[0], SAFE[3] - SAFE[1]
    s = max(min_s, min(max_s, 0.92 * min(sw / rw, sh / rh)))
    cx, cy = r["x"] + r["w"] / 2, r["y"] + r["h"] / 2
    scy = (SAFE[1] + SAFE[3]) / 2  # 安全框中心在 529，略高于画面中心
    tries = []
    offs = sorted(range(-480, 481, 40), key=abs)
    offy = sorted(range(-300, 301, 30), key=abs)
    while s >= min_s - 1e-9:
        seen = set()
        for dy in offy:
            for dx in offs:
                look = clamp_look(cx + dx / s, cy - (scy - 540) / s + dy / s, s)
                key = (round(look[0]), round(look[1]))
                if key in seen:
                    continue
                seen.add(key)
                sx, sy, sw_, sh_ = to_screen(r, look, s)
                if sx < SAFE[0] - 1 or sy < SAFE[1] - 1 or sx + sw_ > SAFE[2] + 1 or sy + sh_ > SAFE[3] + 1:
                    continue
                # 运行时还有 ≤3.5% 的慢推 + 微漂移：两个倍数都要不切字
                if not partial_clips(look, s, els) and not partial_clips(look, s * 1.035, els):
                    return {"x": round(look[0], 1), "y": round(look[1], 1), "s": round(s, 3)}, tries
        tries.append(round(s, 3))
        s -= 0.03
    return {"x": 960.0, "y": 540.0, "s": 1.0}, tries


def union(els):
    xs = [e["x"] for e in els]; ys = [e["y"] for e in els]
    x2 = [e["x"] + e["w"] for e in els]; y2 = [e["y"] + e["h"] for e in els]
    return {"x": min(xs), "y": min(ys), "w": max(x2) - min(xs), "h": max(y2) - min(ys)}


def move_frames(a, b):
    """速度上限：屏幕位移 ≤ 28 px/帧、缩放 ≤ 0.012/帧；至少 16 帧、至多 34 帧。"""
    dist = math.hypot((a["x"] - b["x"]) * max(a["s"], b["s"]), (a["y"] - b["y"]) * max(a["s"], b["s"]))
    return int(max(16, min(34, max(dist / 28, abs(a["s"] - b["s"]) / 0.012))))


# ---------------------------------------------------------------- main compose
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
    protected = sorted(set(list(glossary.keys()) + list(story.get("protect") or [])), key=len, reverse=True)
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
                p.err(f"{sid}: layout={lay!r} 不是 {LAYOUTS} 之一 —— 不确定就用 define / list / compare 这类组件版式")
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
            els = LAY[lay](p, sid, content, variant)
            if lay not in ("custom", "bars", "statement") and els:
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
                          "role": sh.get("role") or ch.get("role")})
            if si == 0:
                chapter_first.append(sid)
            prev_layout, prev_variant = lay, variant
    total_ms = cues[-1]["speech_end_ms"] + END_TAIL_F * 1000 / FPS if cues else 0
    return {"shots": shots, "cues": cues, "total_ms": total_ms, "glossary": glossary, "protected": protected, "chapter_first": chapter_first}


def frame(ms):
    return int(round(ms * FPS / 1000))


def build(story, comp, p: Problems):
    shots, cues = comp["shots"], comp["cues"]
    glossary = comp["glossary"]
    total = frame(comp["total_ms"])
    out_shots, story_ts = [], {}
    prev_gaze = None
    seen_gloss = set()
    used_skel = None
    minute_icons = 0
    # 叙事动作（validate-presentation 要求同一 move 不连续 ≥3 镜）：按蓝图角色 / 版式取，撞了就换近义动作
    ROLE_MOVE = {"hook": "引入", "pre": "定位", "breakdown": "拆分/合并", "example": "传递", "misconception": "反证", "recap": "收束"}
    LAY_MOVE = {"statement": "收束", "define": "定位", "number": "引入", "bars": "反证", "compare": "对比", "code": "定位",
                "flow": "拆分/合并", "list": "累积", "quiz": "反证", "custom": "传递", "media": "定位"}
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
        # 元素出现帧：appear = 第几句；同句错峰 5 帧（≤8）
        per_line = {}
        for e in els:
            a = e["appear"]
            if isinstance(a, int) and a >= nl:
                a = nl - 1
            # 被关键词点名、且点名早于声明 → 不改；点名晚于出现 → 保持（先出现后强调）
            n = per_line.get(a, 0); per_line[a] = n + 1
            e["at"] = max(0, line_start[a] - (8 if a == 0 else 2)) + min(n, 3) * 5 if isinstance(a, int) else 0
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
        U = union(content_els)
        band_fill = (U["w"] * U["h"]) / (BAND["w"] * BAND["h"])
        over, _ = frame_rect(U, els, max_s=1.18 if band_fill < 0.6 else 1.06)
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
            until = min(nxt - 4, fk["at"] + max(60, int(len(fk["term"]) * CHAR_MS * FPS / 1000) + 45), dur - 4)
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
                show = max(75, int(cap_chars(txt) / CPS * FPS))
                tips.append({"term": term, "x": round(tx, 1), "y": round(ty, 1), "w": round(W_, 1), "h": round(H_, 1), "lines": tls, "size": ts,
                             "at": fk["at"] + 6, "until": min(dur - 2, fk["at"] + 6 + show), "below": below})
                if show > fk["until"] - fk["at"]:
                    fk["until"] = min(dur - 4, fk["at"] + show)
        # 音效：只挂真事件
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
        if cam["intent"] == "pull-back":
            cam.update({"from": 1.03, "to": 1.0})
        if cam["intent"] == "reveal":
            cam.update({"to": 1.03})
        beats = [{"cue": ci_, "offset": 0} for ix in sh["line_cues"] for ci_ in ix]
        a = {"x": round(U["x"], 1), "y": round(U["y"], 1), "w": round(U["w"], 1), "h": round(U["h"], 1)}
        rec = {"id": sid, "chapter": sh["chapter"], "skeleton": skel, "layout": f"{sh['layout']}{('-' + sh['variant']) if sh['variant'] else ''}",
               "from": frm, "to": to, "cues": [sh["line_cues"][0][0], sh["line_cues"][-1][-1]],
               "media": MEDIA[sh["layout"]], "live": ["AutoShot"], "camera": cam, "anchor": a, "contentBand": BAND,
               "hero": {"name": sh["layout"], "size": int(max(U["w"], U["h"]) * 0.5), "kind": "text"}, "zones": 3, "bottomFill": True,
               "cover": "paper", "entry": "fade", "beats": beats, "move": moves[k],
               "evidence": "AutoShot", "hold": 40, "noMisconception": True, "why": "auto 版式：内容由 story.json 给出",
               "transition": "zoom" if sh["first_in_chapter"] and k > 0 else ("fade" if k > 0 else "auto"),
               "cinema": {"drift": "none", "fit": "none", "path": path}, "sfxEvents": sfx}
        if sh["layout"] == "quiz":
            rec["misconception"] = sh["content"].get("question"); rec.pop("noMisconception")
        out_shots.append(rec)
        story_ts[sid] = {"layout": sh["layout"], "variant": sh["variant"], "elements": els, "focus": focus_out, "tips": tips,
                         "lines": line_start, "lineEnds": line_end, "think": int(float(sh["content"].get("think", 3)) * FPS) if sh["layout"] == "quiz" else 0,
                         "custom": sh["custom"], "icons": icons}
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


def js(v) -> str:
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"))


def write_project(story, comp, out_shots, story_ts, total, proj: Path):
    (proj / "manifests").mkdir(parents=True, exist_ok=True)
    (proj / "audio").mkdir(exist_ok=True)
    (proj / "src").mkdir(exist_ok=True)
    cues = comp["cues"]
    cdoc = {"source": "audio/narration.mp3.json", "lead_ms": 60, "segmentation": "semantic",
            "break_rule": f"compose-story (silent, {CPS} chars/s, ≤{MAX_CHARS} chars per line)", "cues": cues}
    txt = json.dumps(cdoc, ensure_ascii=False, indent=1) + "\n"
    (proj / "manifests" / "caption-cues.json").write_text(txt, encoding="utf-8")
    (proj / "src" / "caption-cues.json").write_text(txt, encoding="utf-8")
    words = [w for c in cues for w in c["words"]]
    (proj / "audio" / "narration.mp3.json").write_text(json.dumps(words, ensure_ascii=False) + "\n", encoding="utf-8")
    (proj / "narration.txt").write_text("\n".join(c["text"] for c in cues) + "\n", encoding="utf-8")
    (proj / "manifests" / "protected-caption-phrases.txt").write_text("# compose-story：术语表与 protect 列表，字幕不许切开\n" + "\n".join(comp["protected"]) + "\n", encoding="utf-8")
    (proj / "manifests" / "semantic-caption-lines.txt").write_text("\n".join(c["text"] for c in cues) + "\n", encoding="utf-8")
    sdoc = {"$comment": "AUTO-GENERATED by scripts/compose-story.py from story.json — 改内容请改 story.json 后重跑",
            "duration": total, "theme": story.get("theme", "flat"), "canvas": "16:9", "shots": out_shots}
    (proj / "manifests" / "shots.json").write_text(json.dumps(sdoc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    chapters = [c.get("title", "") for c in story["chapters"]]
    film = ("// AUTO-GENERATED by scripts/compose-story.py — 禁止手改（改 story.json）。\n"
            f"export const COPY = {js({'chapterTitles': chapters, 'chromeKicker': story.get('kicker', 'NOTEBOOK-VIDEO'), 'header': story.get('header', story.get('title', '')), 'headerSub': story.get('headerSub', '')})} as const;\n"
            f"export const CHAPTER_SHOTS = {js(comp['chapter_first'])} as const;\n"
            "")
    (proj / "src" / "film.ts").write_text(film, encoding="utf-8")
    st = ("// AUTO-GENERATED by scripts/compose-story.py — 禁止手改（改 story.json）。\n"
          "import type {StoryShot} from './auto';\n"
          f"export const STORY: Record<string, StoryShot> = {js(story_ts)};\n")
    (proj / "src" / "story.ts").write_text(st, encoding="utf-8")
    customs = sorted({v["custom"] for v in story_ts.values() if v.get("custom")})
    lines = ["// AUTO-GENERATED by scripts/compose-story.py — 每镜都由引擎的 AutoShot 渲染（版式 + 关键词同步 + 门禁）。",
             "// 手写定制画面放在 src/custom/，在 src/custom/index.ts 注册，story.json 里用 layout:\"custom\" 引用。",
             "import React from 'react';", "import {AutoShot} from './auto';", "import {SHOTS} from './shots';", ""]
    for s in out_shots:
        lines.append(f"const {s['id']}: React.FC<{{f: number}}> = ({{f}}) => <AutoShot id=\"{s['id']}\" f={{f}} />;")
    lines.append("")
    lines.append("export const SCENES: Record<keyof typeof SHOTS, React.FC<{f: number}>> = {" + ", ".join(s["id"] for s in out_shots) + "};")
    lines.append(f"export const SCENES_VERSION = 'auto-scenes · {len(out_shots)} shots · custom: {', '.join(customs) or 'none'}';")
    (proj / "src" / "scenes.tsx").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_media(story, proj: Path) -> None:
    """story.json 顶层 media → public/media/ + manifests/media.json，再交给 prepare-media.py 探测 / 转码 / 同步 src/media.json。"""
    import shutil
    import subprocess
    mdir = proj / "public" / "media"
    mdir.mkdir(parents=True, exist_ok=True)
    items = []
    for m in story["media"]:
        src = Path(story["_dir"]) / m["file"]
        ext = src.suffix.lower()
        kind = "image" if ext in (".png", ".jpg", ".jpeg", ".webp") else "gif" if ext == ".gif" else "video"
        if src.is_file():
            shutil.copyfile(src, mdir / f"{m['id']}{ext}")
        e = {k: v for k, v in m.items() if k not in ("file", "width", "height")}
        e.update(file=f"{m['id']}{ext}", kind=m.get("kind", kind), source=m.get("source", "user"), muted=m.get("muted", True))
        items.append(e)
    (proj / "manifests" / "media.json").write_text(json.dumps({"items": items}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, str(Path(__file__).with_name("prepare-media.py")), str(proj)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("story")
    ap.add_argument("project")
    ap.add_argument("--report")
    ap.add_argument("--check", action="store_true", help="只检查不写盘")
    # 3.6.0：读速可配置（加权字/秒，1–9）。也可在 story.json 顶层写 "cps"。缺省 4.5（组件路线的既有速度）。
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
        global CPS, CHAR_MS
        CPS, CHAR_MS = float(cps), 1000 / float(cps)
    setup_break_rule(Path(a.project))
    p = Problems()
    left = sorted(set(re.findall(r"<<([^>]*)>>", json.dumps(story, ensure_ascii=False))))
    if left:
        for x in left[:12]:
            print(f"  ✗ 蓝图占位符没填：<<{x}>> —— 换成你的内容（或删掉这一镜）")
        print(f"compose-story：还有 {len(left)} 处 <<占位符>> 没填")
        return 1
    comp = compose(story, p)
    if comp is None or not comp["shots"]:
        for m in p.errors:
            print(f"  ✗ {m}")
        return 1
    out_shots, story_ts, total = build(story, comp, p)
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
        write_project(story, comp, out_shots, story_ts, total, Path(a.project))
        if story.get("media"):
            write_media(story, Path(a.project))
    return 0


if __name__ == "__main__":
    sys.exit(main())
