#!/usr/bin/env python3
"""story_layout.py — compose-story 的「每种版式把元素摆在哪」

从 `compose-story.py` 切出的第五块，也是最大的一块：`el()` 的元素构造、十三种版式的几何、
手账页 / 配方 / 版式页的取景框常量，以及版式分发表 `LAY`。

为什么按「版式」而不是按「函数大小」切：这一块的变化原因是**视觉**——
某个版式要挪位置、改字号、调留白时，只该动这个文件；而时间轴、字幕、输出格式的改动
不该把版式文件带上。主文件里剩下的 `compose()` / `build()` 仍然是流水线，不拆（§8.5）。

边界：
  - **在这里**：字号三档 `TYPE`、内容带 `BAND`、一字排开的宽度上限 `FLOW_TOTAL_MAX`、
    单位收敛 `clean_unit`、页内取景框常量、`STORY_MEDIA`（media 版式要从顶层 media 拿尺寸）。
  - **不在这里**：字宽与折行（`story_text`）、动作帧号（`story_acts`）、
    字幕与朗读速度（`story_caption`）、镜头时间轴（`build`）。
  - **共享可变状态**：`STORY_MEDIA` 是 dict，`compose()` 用 `clear()` / 赋值 / `update()` 填它，
    **不能重新绑定**（`story_layout.STORY_MEDIA = {...}` 会让本模块看到旧对象）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from story_text import MIN_FONT, SAFE_LH, fit_text, text_w  # noqa: E402
from story_acts import check_draw, resolve_ink_acts  # noqa: E402


TYPE = {"display": 76, "title": 46, "body": 36}  # 三档字号；hero 数字另算（同镜仍 ≤3 种）
BAND = {"x": 200, "y": 214, "w": 1520, "h": 630}  # 内容带（页眉下、字幕上）
SUBTITLE_CLEAR_Y = 890  # 距最厚字幕条(y≈940)留 50px 余量，抗 1.05× 缓推
# flow / compare 这类「一字排开」的版式，整组宽度上限。留白不是纯审美：满铺 1520 时
# 屏幕安全框（1660×666）被内容占满，相机没有任何可动余量，招牌镜想推都推不进去。
FLOW_TOTAL_MAX = 1300
# flow 节点顶上的步骤序号（01 / 02 …）字号，取 body 档。
FLOW_BADGE = TYPE["body"]

# 允许直接上屏的单位（符号 / 公制短单位）。故事里的 `unit` 只该写这一列里的东西；
# 写成「占比 %」「公斤燃料 / 公斤干重」这类说明句，会把柱顶读数拼成「85占比 %」并折行压到柱子上。
UNIT_TOKENS = (
    "%", "‰", "°C", "°", "×", "元", "万元", "亿元", "美元", "公斤", "千克", "克", "吨",
    "米", "公里", "千米", "厘米", "毫米", "秒", "分钟", "小时", "天", "年", "人", "次",
    "个", "倍", "度", "瓦", "千瓦", "伏", "安", "GB", "MB", "TB", "KB", "ms", "kg", "km",
    "cm", "mm", "kWh", "W", "V", "A", "Gbps", "Mbps", "万次", "亿次", "万", "亿",
)
UNIT_OK = set(UNIT_TOKENS)


class _Quiet:
    """试排用：只量字号，不记修复 / 提示（正式排版那一遍才记）。"""
    def fix(self, *_a, **_k): pass
    hint = err = fix


_QUIET = _Quiet()


def clean_unit(p: "Problems", sid: str, raw) -> str:
    """把 unit 收敛成一个真正的单位符号。

    规则：只接受 UNIT_TOKENS；带 % / ‰ / ° 的取符号；斜杠或空格分隔的取第一个合法单位；
    都不行就去掉单位（宁可不写，也不把说明文字拼进读数）。每次降级都报 P1 并给出改法。
    """
    u = str(raw or "").strip()
    if not u or u in UNIT_OK:
        return u
    for token in ("%", "‰", "°C", "°", "×"):
        if token in u:
            p.hint(f"{sid}: unit={raw!r} 不是单位，读数会拼成「85{u}」。已只保留 {token!r}；"
                   f"「{u.replace(token, '').strip()}」这类说明请写进 title 或 label。")
            return token
    for part in re.split(r"[\s/]+", u):
        for cand in sorted(UNIT_TOKENS, key=len, reverse=True):
            if part.startswith(cand):
                p.hint(f"{sid}: unit={raw!r} 太长，已收敛为 {cand!r}（其余的说明写进 title / label）。")
                return cand
    p.hint(f"{sid}: unit={raw!r} 不是可上屏的单位，已去掉 —— unit 只写符号（% / 公斤 / GB…），说明写进 title。")
    return ""


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
    # 术语框高与读音行高都走 SAFE_LH（与渲染端 Lines 的 safeLh 同一真源）。
    # 按 ts*1.2 排时 reading 会压进术语的行盒里（被 OverlapGate 硬拦）。
    term_h = ts * SAFE_LH
    els.append(el("term", "text", lx, y0, tw, term_h, term, ts, "display", 0, lh=SAFE_LH))
    if c.get("reading"):
        els.append(el("reading", "text", lx, y0 + term_h + 10, text_w(c["reading"], TYPE["body"]),
                      TYPE["body"] * SAFE_LH, c["reading"], TYPE["body"], "muted", 0, lh=SAFE_LH))
    els.append(el("definition", "card", rx, y0, 800, h + 60, c["definition"], s, "body", c.get("definitionAt", 0), lines=ls, lh=1.45, pad=30))
    if ex:
        els_, es, ew, eh = fit_text(p, f"{sid}.example", ex, TYPE["body"], 760, 2, lh=1.45)
        els.append(el("example", "quote", rx, y0 + h + 100, 800, eh + 40, ex, es, "muted", c.get("exampleAt", 1), lines=els_, lh=1.45, pad=20))
    return els


# 数字块（数字 + 单位）最宽多少：与注释列（480 + 间距 80）合起来 ≤ 1360，
# 整组在 1.16 倍推近下仍放得进安全框（1660 宽），且留出取景搜索的余量。
NUMBER_BLOCK_MAX = 800
# 数字块的下限宽度与字号上限：短数字按这个宽度放大，字号不超过 NUMBER_SIZE_MAX。
NUMBER_BLOCK_MIN = 640
NUMBER_SIZE_MAX = 320
# 上下排法（数字太宽、注释排到下面）时数字块的最宽值：1.16 倍推近下仍放得进安全框。
NUMBER_STACK_MAX = 1300
# 并排排法最多把数字缩到原字号的这个比例，再小就改上下排法。
NUMBER_SHRINK_MIN = 0.8


def hero_number_w(txt: str, unit: str, size: float) -> float:
    """大数字（KineticNumber：Clash 粗体）的上屏宽度估计，宁宽勿窄。"""
    w = 0.0
    for ch in txt:
        w += (0.46 if ch == "1" else 0.72) * size if ch.isdigit() else text_w(ch, size) * 1.15
    if unit:
        u = size * 0.42
        w += sum(text_w(ch, u) if ord(ch) > 0x2E80 else text_w(ch, u) * 1.15 for ch in unit) + size * 0.10
    return w + size * 0.04


def lay_number(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    # 缺 value 是作者写漏，不是运行时意外：给一条能照着改的话，不要抛 KeyError 让整片 compose 崩在栈里
    if "value" not in c:
        p.err(f'{sid}：layout="number" 必须给 content.value（要显示的数字），'
              f'例如 {{"value": 100, "unit": "万次", "label": "挨个比的最坏情况"}}；'
              f'如果只想放一句话，把 layout 改成 "statement"。')
        return []
    try:
        val = float(c["value"])
    except (TypeError, ValueError):
        p.err(f'{sid}：content.value 必须是数字（现在是 {c["value"]!r}）；'
              f'要显示带字母的文本请用 layout="statement"。')
        return []
    dec = int(c.get("decimals", 0 if float(val).is_integer() else 1))
    txt = f"{c.get('prefix', '')}{val:.{dec}f}"
    # 招牌数字：hero 档单独定字号（不占 TYPE 三档）。整组收拢后靠数字本身的分量撑起画面。
    size = 260
    unit = clean_unit(p, sid, c.get("unit", ""))
    notes = (c.get("notes") or [])[:3]
    left = variant != "mirror"
    # 预留宽度要**宽于**实际：数字用 Clash 粗体（「1」约 0.46em，其余每位约 0.72em，含 -0.02em 字距；
    # 这套字体没有等宽数字，tabular-nums 不生效），单位 0.42 倍字号、0.10em 外边距。
    # 按正文字体（Kai 数字 0.6em）去估会窄一截，「3000倍」实际比估值宽 15%，单位就压到旁边的注释上。
    nw = hero_number_w(txt, unit, size)
    # 两种排法：
    #   并排：数字块（数字 + 标签）在左、注释列在右，整组按实际宽度收拢后居中；
    #   上下：数字本身很宽（「1.852公里」），并排要把数字缩到 NUMBER_SHRINK_MIN 以下时，
    #         改成数字 + 标签在上、注释一行排在下面。
    # 两种都不把注释钉到内容带另一端：两端拉开时整组宽到 1480，任何 ≥1.12 的推近都会切断注释，
    # 数字镜就只能一个静帧到底。收拢后整组在 1.16 倍下仍放得进安全框，推近数字不切注释。
    stacked = bool(notes) and nw * NUMBER_SHRINK_MIN > NUMBER_BLOCK_MAX
    cap = NUMBER_STACK_MAX if stacked else NUMBER_BLOCK_MAX
    if nw > cap:
        size = int(size * cap / nw); nw = hero_number_w(txt, unit, size)
    elif nw < NUMBER_BLOCK_MIN:
        # 短数字（「1.2秒」）放大字号把数字块撑到 NUMBER_BLOCK_MIN，而不是留一大块空白：
        # 画面的分量来自数字本身。
        size = min(NUMBER_SIZE_MAX, int(size * NUMBER_BLOCK_MIN / nw)); nw = hero_number_w(txt, unit, size)
    lab = fit_text(p, f"{sid}.label", c["label"], TYPE["title"], 800, 1) if c.get("label") else None
    block_w = max(nw, lab[2] if lab else 0)
    notes_at = c.get("notesAt") if isinstance(c.get("notesAt"), list) else None
    NOTE_W, GAP = 480, 80
    if stacked:
        row_w = max(block_w, len(notes) * NOTE_W + 40 * (len(notes) - 1)) if len(notes) > 1 else max(block_w, NOTE_W)
        row_w = min(row_w, W - 80)
        group_w = max(block_w, row_w)
        gx = X + (W - group_w) / 2
        nx = gx if left else gx + group_w - block_w
        ny = Y + 40
    else:
        group_w = block_w + ((GAP + NOTE_W) if notes else 0)
        gx = X + (W - group_w) / 2
        nx = gx if left else gx + group_w - block_w
        ny = Y + 110
    els = [el("number", "number", nx, ny, nw, size * 1.0, txt, size, "hero", 0, value=val, decimals=dec,
              prefix=c.get("prefix", ""), unit=unit, from_=float(c.get("from", 0)), tone=c.get("tone", "orange"))]
    below = ny + size * 1.05 + 24
    if lab:
        lls, ls_, lw, lh_ = lab
        els.append(el("label", "text", nx, below, lw, lh_, c["label"], ls_, "body", 0))
        below += lh_
    if stacked:
        n_ = len(notes)
        each = (row_w - 40 * (n_ - 1)) / n_
        row = [fit_text(p, f"{sid}.notes[{i}]", n, TYPE["body"], each - 40, 2, lh=1.4) for i, n in enumerate(notes)]
        # 同一排的注释卡等高（取最高那张），一排读起来是同一级
        row_h = max(r[3] for r in row) + 28
        for i, (n, (nls, ns, nw2, nh)) in enumerate(zip(notes, row)):
            els.append(el(f"note{i + 1}", "note", gx + i * (each + 40), below + 34, each, row_h, n, ns, "body",
                          notes_at[i] if notes_at and i < len(notes_at) else min(i, 2), lines=nls, lh=1.4))
        return els
    rx = gx + block_w + GAP if left else gx
    y = Y + 140
    for i, n in enumerate(notes):
        nls, ns, nw2, nh = fit_text(p, f"{sid}.notes[{i}]", n, TYPE["body"], NOTE_W - 40, 2, lh=1.4)
        els.append(el(f"note{i + 1}", "note", rx, y, NOTE_W, nh + 28, n, ns, "body", notes_at[i] if notes_at and i < len(notes_at) else min(i, 2), lines=nls, lh=1.4))
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
    # 柱区上下收一点（整组高 ≈560）：整张图在 1.16 倍下仍放得进安全框，
    # 关键词 / 招牌镜推近到柱子时不切标题和柱底标签。
    top, bottom = Y + 110, Y + H - 112
    n = len(data)
    gap = 60
    bw = min(220, (W - 160 - gap * (n - 1)) / n)
    total = bw * n + gap * (n - 1)
    x0 = X + (W - total) / 2
    vmax = max(float(d["value"]) for d in data) or 1
    unit = clean_unit(p, sid, c.get("unit", ""))
    hl = c.get("highlight")
    for i, d in enumerate(data):
        v = float(d["value"])
        bh = max(8, (bottom - top - 60) * v / vmax)
        bx = x0 + i * (bw + gap)
        lab = str(d["label"])
        # 柱顶标签必须一行放下：>8 个汉字就报 P1（不自动折行——折下来的第二行会压在柱子上，
        # 成片 45 秒处「13公斤燃料 / 公斤干重」就是这么糊成两行的）。
        if len(lab) > 8:
            p.hint(f"{sid}: 柱标签「{lab}」{len(lab)} 字 > 8 —— 柱顶只放一个短标签，细节写进 title 或台词。")
        lsz = TYPE["body"]
        while text_w(lab, lsz) > bw + gap - 10 and lsz > MIN_FONT:
            lsz -= 2
        if text_w(lab, lsz) > bw + gap - 10:
            p.err(f"{sid}: 柱标签「{lab}」太长（{MIN_FONT}px 下宽 {text_w(lab, MIN_FONT):.0f} > {bw + gap - 10:.0f}）—— 缩到 {int((bw + gap - 10) / MIN_FONT)} 个汉字以内")
        vt = f"{v:g}{unit}"
        els.append(el(f"bar:{lab}", "bar", bx - gap / 2 + 4, bottom - bh - 56, bw + gap - 8, bh + 56 + 52, lab, lsz, "accent" if lab == hl else "body", c.get("barsAt", 0),
                      barX=bx, barW=bw, barH=bh, base=bottom, value=v, valueText=vt, idx=i, hot=lab == hl))
    return els


# compare 栏：标题行高、读数行高、上下内边距 + 顶边（与 auto.tsx 的 panel 一致）、栏高地板
PANEL_TITLE_LH = 1.3
PANEL_VALUE_H = 138
PANEL_PAD = 64
PANEL_MIN_H = 380


def lay_compare(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    mode = c.get("mode", "split")
    els = []
    pw = 800 if mode == "morph" else 620
    sides = [sd for sd in ("before", "after") if isinstance(c.get(sd), dict)]
    # 字号：栏标题 display 档、条目 title 档；两栏统一取能放下的最小那格（并排的两栏是同一级信息）。
    t_size = min([fit_text(_QUIET, f"{sid}.{sd}.title", c[sd].get("title", "之前" if sd == "before" else "之后"), TYPE["display"], pw - 68, 1)[1]
                  for sd in sides] or [TYPE["display"]])
    i_size = min([fit_text(_QUIET, f"{sid}.{sd}.items[{i}]", it, TYPE["title"], pw - 90, 2, lh=1.35)[1]
                  for sd in sides for i, it in enumerate((c[sd].get("items") or [])[:4])] or [TYPE["title"]])

    def panel(key, side, x, w, appear):
        d = c[side]
        y = Y + 40
        tls, ts, tw, th = fit_text(p, f"{sid}.{side}.title", d.get("title", "之前" if side == "before" else "之后"), t_size, w - 68, 1)
        # 高度按渲染端（auto.tsx 的 panel）逐项累加：标题单行、读数一行、每条目上间距 22
        hh = ts * PANEL_TITLE_LH
        if d.get("value") is not None:
            hh += PANEL_VALUE_H
        items = d.get("items") or []
        ih = []
        for i, it in enumerate(items[:4]):
            ils, isz, iw, iht = fit_text(p, f"{sid}.{side}.items[{i}]", it, i_size, w - 90, 2, lh=1.35)
            ih.append((ils, isz, iht))
            hh += iht + 22
        # 高度下限 PANEL_MIN_H 只是地板（validate-shot-motion 的「内容只占安全区」看整组外接框）；
        # 内容撑不满时多出来的高度上下均分（padY），不堆在卡片下半截。
        e = el(key, "panel", x, y, w, max(hh + PANEL_PAD, PANEL_MIN_H), d.get("title", ""), ts, "body", appear,
               side=side, title=d.get("title", "之前" if side == "before" else "之后"), value=d.get("value"), unit=clean_unit(p, f"{sid}.{side}", d.get("unit", "")),
               decimals=int(d.get("decimals", 0)), items=[{"lines": a, "size": b} for a, b, _ in ih], tone=d.get("tone", "orange" if side == "before" else "green"))
        e["_content"] = hh + PANEL_PAD
        return e

    def settle(panels, own_height=False):
        """两栏统一上下留白（padY），标题对齐。own_height：并排的两栏各按自己的内容定高，
        条目少的那栏不留底部空白；整组外接框仍由较高那栏（不低于地板）决定。"""
        h = max(e["h"] for e in panels)
        content = max(e["_content"] for e in panels)
        pad = round(max(0, h - content) / 2)
        for e in panels:
            own = e.pop("_content")
            e["h"] = round(own + 2 * pad, 1) if own_height and own < content else h
            e["padY"] = pad
        return h

    if mode == "morph":
        e1 = panel("before", "before", X + 360, 800, 0)
        e2 = panel("after", "after", X + 360, 800, c.get("morphLine", 1))
        e2["y"] = e1["y"]
        settle([e1, e2])
        e1["morphTo"] = "after"; e2["morph"] = True
        els += [e1, e2]
    else:
        # 两栏各 620，整组 1320 居中：留出两侧呼吸（几乎铺满时相机没有可动空间，招牌镜推不进去，画面也顶边）。
        w = 620
        cx = X + W / 2
        e1 = panel("before", "before", cx - 1320 / 2, w, 0)
        # afterLine 缺省 0：两栏同帧入场。
        # 对比的语义是「并列」，等第二句才出现右栏时右半屏是空的，缺一半就不是对比了。真要分先后，显式写 afterLine。
        e2 = panel("after", "after", cx + 1320 / 2 - w, w, c.get("afterLine", 0))
        h = settle([e1, e2], own_height=True)
        els += [e1, e2, el("arrow", "arrow", e1["x"] + w + 40, Y + 40 + h / 2 - 30, 1320 - 2 * w - 80, 60, "", 0, "decor", c.get("afterLine", 0))]
    vh = 0
    if c.get("verdict"):
        vls, vs, vw, vh = fit_text(p, f"{sid}.verdict", c["verdict"], TYPE["body"], 1200, 1)
        vy = max(e["y"] + e["h"] for e in els if e["kind"] == "panel") + 34
        els.append(el("verdict", "text", X + (W - vw) / 2, vy, vw, vh, c["verdict"], vs, "accent", c.get("verdictLine", 2)))
        vh += 34
    # 整组落在安全区中部（视觉中心略偏上），不贴着页眉、把下半张纸空出来
    group_h = max(e["h"] for e in els if e["kind"] == "panel") + vh
    dy = max(0, (H - 40 - group_h) * 0.42)
    for e in els:
        e["y"] = round(e["y"] + dy, 1)
    return els


def lay_code(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    lines = c["code"].rstrip("\n").split("\n")
    size = TYPE["body"]
    note = c.get("note")
    longest = max(text_w(l.expandtabs(4), 1, mono=True) for l in lines)  # em 宽：半角 0.6、全角 1.0（CODE_FONT 的中文回落 Kai）
    # 代码框按最长行定宽（不留大片空白），右侧注释拿走剩下的宽度
    boxw = min(1060, max(760, int(longest * size + 100))) if note else 1300
    while longest * size > boxw - 80 and size > MIN_FONT:
        size -= 2
    if longest * size > boxw - 80:
        p.err(f"{sid}: 代码最长一行约 {longest / 0.6:.0f} 个半角宽（中文算 2），{MIN_FONT}px 下放不进 {boxw}px —— 每行请 ≤ {int((boxw - 80) / (MIN_FONT * 0.6))} 个半角宽（折行或删减）")
    lh = 1.55; row = size * lh
    maxl = int((H - 110) / row)
    if len(lines) > maxl:
        p.err(f"{sid}: 代码 {len(lines)} 行，屏上最多 {maxl} 行 —— 只保留讲到的那几行（其余用 # ... 代替）")
        lines = lines[:maxl]
    boxh = 90 + len(lines) * row + 30
    bx, by = X + 20, Y + max(0, (H - boxh) / 2)
    els = [el("code", "codebox", bx, by, boxw, boxh, c.get("title", ""), size, "body", 0, lang=c.get("lang", ""), lh=lh, nlines=len(lines))]
    for i, l in enumerate(lines):
        els.append(el(f"L{i + 1}", "codeline", bx + 30, by + 90 + i * row, boxw - 60, row, l, size, "body", 0, n=i + 1))
    if note:
        nwid = X + W - (bx + boxw + 40) - 40
        nls, ns, nw, nh = fit_text(p, f"{sid}.note", note, TYPE["title"], nwid - 50, 4, lh=1.4)
        els.append(el("note", "note", bx + boxw + 40, by + 20, nwid, nh + 50, note, ns, "accent", c.get("noteAt", 1), lines=nls, lh=1.4))
    return els


def lay_flow(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    steps = c["steps"]
    bad = [i for i, st in enumerate(steps) if not isinstance(st, dict) or not st.get("label")]
    if bad:
        p.err(f'{sid}.steps[{bad[0]}]：每一步要写 label —— 照这个填：{_EXAMPLES["flow"]}')
        return []
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
    # 整行宽度收窄到 1300 并居中，两侧留呼吸。
    # 为什么：铺满 1520 的 4 节点，安全框几乎被占满，相机一点都推不进去（招牌镜直接做不出来）；
    # 收窄到 1300 后每个节点都能推到 1.15–1.25，而且画面两侧不再顶到边。
    total = min(W - 80, FLOW_TOTAL_MAX)
    nw = (total - 80 - arrow * (n - 1)) / n
    x0 = X + (W - total) / 2 + 20
    title_h = (els[0]["h"] + 46) if els else 24
    avail = H - title_h - 20
    # 节点高度由内容决定：步骤名用 display 档（最多两行）、注释用 title 档，顶上一枚步骤序号。
    # 同一排的字号统一取最小那格（同镜字号 ≤3 档，且并排的卡片读起来是同一级）。
    # node_min 只是地板：内容撑不满时，多出来的高度上下均分（PAD_Y），不堆在卡片下半截。
    node_min = max(240, int(avail * 0.62))
    inner = nw - 48
    steps = [st if isinstance(st, dict) else {"label": st} for st in steps]
    lab_size = min(fit_text(_QUIET, f"{sid}.steps[{i}].label", str(st["label"]), TYPE["display"], inner, 2, lh=SAFE_LH)[1]
                   for i, st in enumerate(steps))
    note_size = min([fit_text(_QUIET, f"{sid}.steps[{i}].note", st["note"], TYPE["title"], inner, 3, lh=SAFE_LH)[1]
                     for i, st in enumerate(steps) if st.get("note")] or [TYPE["title"]])
    badge_h = round(FLOW_BADGE * SAFE_LH) + 10
    fitted = []
    for i, st in enumerate(steps):
        # lh 与渲染端（auto.tsx 的 Lines）必须逐字一致，否则多出来那一截就让第二行压到第一行上
        # （被 OverlapGate 硬拦）。渲染端的兜底是 safeLh = max(用户给, SAFE_LH)。
        lls, ls_, lw, lh_ = fit_text(p, f"{sid}.steps[{i}].label", str(st["label"]), lab_size, inner, 2, lh=SAFE_LH)
        hh = badge_h + lh_ + 60
        nlines, ns = [], note_size
        if st.get("note"):
            nlines, ns, nww, nh = fit_text(p, f"{sid}.steps[{i}].note", st["note"], note_size, inner, 3, lh=SAFE_LH)
            hh += nh + 20
        fitted.append((st, lls, ls_, nlines, ns, hh))
    content_h = max(f[5] for f in fitted)
    node_h = max(content_h, node_min)
    pad_y = round((node_h - content_h) / 2)
    # 整排落在安全区中部（视觉中心略偏上）
    ny = Y + title_h + max(8, (avail - node_h) * 0.42)
    for i, (st, lls, ls_, nlines, ns, hh) in enumerate(fitted):
        x = x0 + i * (nw + arrow)
        els.append(el(f"step{i + 1}", "node", x, ny, nw, node_h, st["label"], ls_, "accent" if st.get("hot") else "body",
                      st.get("at", min(i, 99)), lines=lls, note=st.get("note", ""), noteLines=nlines, noteSize=ns, hot=bool(st.get("hot")),
                      n=i + 1, badge=FLOW_BADGE, padY=pad_y))
        if i:
            els.append(el(f"arrow{i}", "arrow", x - arrow + 10, ny + node_h / 2 - 25, arrow - 20, 50, "", 0, "decor", st.get("at", min(i, 99))))
    return els


def lay_list(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    items = c["items"]
    if not 2 <= len(items) <= 5:
        p.err(f"{sid}: list 需要 2–5 条（现在 {len(items)}）—— 多了拆成两镜")
        items = items[:5]
    title = c.get("title")
    tls, ts, tw, th = [], 0, 0.0, 0.0
    if title:
        tls, ts, tw, th = fit_text(p, f"{sid}.title", title, TYPE["title"], 1300, 1)
    rows = []
    for i, it in enumerate(items):
        ils, isz, iw, ih = fit_text(p, f"{sid}.items[{i}]", it, TYPE["title"] if len(items) <= 3 else TYPE["body"], 1200, 2, lh=1.35)
        rows.append((ils, isz, ih, it))
    # 整体垂直居中，间距固定 34。
    # 从顶端往下堆、把剩余空间摊进 gap 时，条目少则下半屏空着、条目多则挤成一团。居中 + 固定间距，条目多少都不会塌。
    GAP = 34.0
    body_h = sum(r[2] + 24 for r in rows) + GAP * max(0, len(rows) - 1)
    head_h = (th + 46) if title else 0.0
    y = Y + max(16.0, (H - head_h - body_h) / 2)
    els = []
    if title:
        els.append(el("title", "text", X + 80, y, tw, th, title, ts, "title", 0, lines=tls, lh=1.35))
        y += th + 46
    for i, (ils, isz, ih, it) in enumerate(rows):
        els.append(el(f"item{i + 1}", "item", X + 80, y, 1320, ih + 24, it, isz, "body", i, lines=ils, lh=1.35, n=i + 1, style=c.get("style", "number")))
        y += ih + 24 + GAP
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
# TREATMENT / TREATMENT_MOVES 不在这里：它们是导演层输入，只有 build / signature_shot_id / main 用，
# 留在 compose-story.py；搬进来会让版式模块背上看不到的使用者。


def lay_media(p, sid, c, variant):
    """真实素材：一张截图 / 一段录屏放进 MediaFrame；区域（0–1 相对坐标）变成可被 {{词|区域id}} 点名的元素。"""
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


# ---------------------------------------------------------------- 手账页 
# 语法来自 cell 片（journal 皮肤）：**容器是纸，不是卡片**。整页不产生任何 card / panel / 圆角框。
# 一页 = 装裱好的真图版（右，占画宽 45%）+ 手写大字（页标题）+ 印章 + 一行手写说明。
# 为什么另开一族而不是改现有版式：现有 10 个版式的视觉语言是「白卡片 + 圆角 + 边框」，
# 那是幻灯片的语言；手账页一旦套上卡片框，就退回成 PPT。
PAGE_MEDIA = {"x": 960, "y": 96, "w": 860, "h": 800}
# 墨图的画框比真图版收一圈：真图版是「贴上去的一张卡纸」，要顶到边；
# 墨图是「画在纸上的」，四周必须留出没画的空白，否则相机连推近的余量都没有
# （与真图版同尺寸时 anchor 会超出安全区，画面顶死）。
INK_BOX = {"x": 980, "y": 130, "w": 780, "h": 700}
PAGE_LEFT_X, PAGE_TEXT_W = 236, 600


def lay_page(p, sid, c, variant):
    """一页「有人在研究」的记录。

    content:
      page       plate（默认，真图版页）| loupe（放大镜页）
      media      真图版 id（manifests/media.json 的条目）
      catalogue  编目号（如 "Schem. XI"）
      title      图版名（如 "《显微图谱》1665"）
      big        手写大字：年份 / 数字 / 一个词（≤8 字）
      stamp      印章（2–3 字，朱砂）
      note       手写说明（一行，≤16 字）
      look       loupe 的镜心（0–1 相对图版，如 [0.25,0.42]）
      zoom       loupe 放大倍数（默认 2.6；>3 会糊，validate-media 会拦）
    """
    page = str(c.get("page") or "plate").strip()
    mid = c.get("media")
    ink = c.get("ink")
    if ink and not mid:
        page = "ink"
    if not mid and page != "ink":
        p.err(f"{sid}: page 版式需要 content.media（真图版）或 content.ink（墨图）")
        return []
    box = PAGE_MEDIA
    els = []
    if page == "ink":
        # 墨图：作者自己画在这一页上的图，不是贴上去的图版。
        # 区别不是大小，是「谁画的」——图版是外来证据（卡纸装裱、编目号、CC BY），
        # 墨图是这一页的主人画的（直接落在纸上，没有白边、没有署名）。
        # 有实物证据时用图版；讲几何、结构、数据时没有实物，用墨图——否则就只剩卡片在讲。
        if not isinstance(ink, dict) or not ink.get("draw"):
            p.err(f'{sid}: content.ink 要写 {{"draw": "lib:<名字>" 或 "shapes:[…]", "label": "<这张图叫什么>"}}')
            return []
        check_draw(p, sid, "content.ink", ink)
        ib = INK_BOX
        els.append(el("ink", "figure", ib["x"], ib["y"], ib["w"], ib["h"], "", 0, "body", 0,
                      draw=ink.get("draw"), label=ink.get("label"), parts=ink.get("parts"),
                      figAt=int(ink.get("at", 0)), inkAt=int(ink.get("delay", 0)),
                      # acts 先原样带着：@n（第几句旁白）要等 cues 排完才能换算成本镜帧号，
                      # 换算在 compose 主循环里做（见 resolve_ink_acts 的调用点），这里不落进 story.ts。
                      inkActs=ink.get("acts")))
    common = dict(media=mid, catalogue=c.get("catalogue"), title=c.get("title"))
    if page == "ink":
        pass
    elif page == "loupe":
        look = c.get("look") or [0.5, 0.5]
        try:
            look = [float(look['x']), float(look['y'])] if isinstance(look, dict) else [float(look[0]), float(look[1])]
        except (TypeError, ValueError, IndexError, KeyError):
            p.err(f"{sid}: content.look 要写 [x, y] 两个 0–1 的数（图版上的相对位置）")
            look = [0.5, 0.5]
        els.append(el("plate", "loupe", box["x"], box["y"], box["w"], box["h"], "", 0, "body", 0,
                      look=look, lensAt=int(c.get("lensAt", 34)), zoom=float(c.get("zoom", 2.6)),
                      r=int(c.get("r", 225)), **common))
    elif page == "plate":
        els.append(el("plate", "archive", box["x"], box["y"], box["w"], box["h"], "", 0, "body", 0, **common))
    else:
        p.err(f"{sid}: content.page={page!r} 不认识（这一族只有 plate / loupe；标本速写用 layout=statement + sketch）")
        return []

    # 左侧：手写大字当页标题。手账的标题是写上去的，不是排出来的。
    big = c.get("big")
    big_w = 0.0
    big_h = 0.0
    y = 214
    if big:
        # 字号按真字宽定。HandLettering 用 opentype.js 的 font.getAdvanceWidth 逐字累加排字，
        # 与 text_metrics 读的是同一份 hmtx（「——」「……」等标点按估算会偏窄）。真字宽下不需要安全系数。
        size = 104
        while text_w(str(big), size) > PAGE_TEXT_W and size > 64:
            size -= 4
        if text_w(str(big), size) > PAGE_TEXT_W:
            p.hint(f"{sid}: content.big={big!r} 太长（手写大字 ≤8 字）；把剩下的意思写进 note")
        big_w = text_w(str(big), size)
        big_h = size * 1.25
        # appear 是「第几句」不是帧号（compose 在这里换算成帧）：大字跟第一句一起写上去
        els.append(el("big", "lettering", PAGE_LEFT_X, y, big_w, big_h, str(big), size, "display", 0, perChar=6))
    # 印章：大字右侧 60px；没有大字就贴左上
    stamp = c.get("stamp")
    stamp_size = 124
    stamp_dropped = False
    if stamp:
        sx = PAGE_LEFT_X + (big_w + 60 if big else 0)
        sy = y + 4
        # 大字写满左侧那一栏时，右侧已经没有 124+60 的余量了：
        # 硬塞会把章盖在字上。
        # 这时把章落到大字下面一行——手账上「写完一行、在下面盖个章」本来就是常见的做法。
        if big and sx + stamp_size > 900:
            sx = PAGE_LEFT_X
            sy = y + big_h + 24
            stamp_dropped = True
        # 印章：字写完 → 盖章。
        # 为什么不让它 appear=0 就走：plate / big / stamp 会全挤在开头十几帧里，
        # 前三秒只剩一个节拍（validate-opening 的 O4 直接判 P0）。
        # 手账的动作顺序本来也是「写完这一行，再落章」——所以给它一个「大字写完帧」，
        # 由 compose 的 afterBig 字段承接（不占用 appear，appear 仍是「第几句」）。
        els.append(el("stamp", "stamp", sx, sy, stamp_size, stamp_size, str(stamp), 0, "body", 0,
                      afterBig=("big" if big else None)))
    # 手写说明：大字下方一行。
    # 字号 44–56：与手写大字差得太少会和「页标题」抢同一层级，一页上出现两行差不多大的字，
    # 就成了「排版」而不是「写上去的」。
    # 说明是附注，读者扫一眼就够，主视线仍在大字与图版上。
    note = c.get("note")
    note_y = y + (big_h + 34 if big else 0)
    # 章被挤到大字下面那一行时，批注必须再往下让出整枚章的高度。
    # 否则两者会落在同一行互压，而且 OverlapGate 抓不到（章是 SVG 路径，不在它的文字块集合里）——只能靠排版时算准。
    if stamp_dropped:
        note_y = y + big_h + 24 + stamp_size + 20
    if note:
        nsize = 56
        while text_w(str(note), nsize) > PAGE_TEXT_W + 100 and nsize > 40:
            nsize -= 4
        if text_w(str(note), nsize) > PAGE_TEXT_W + 100:
            p.hint(f"{sid}: content.note={note!r} 太长（一行手写说明 ≤16 字）")
        # 说明写在第二句（图版已经看过了，再补一句「这是第几篇」）；只有一句时跟第一句
        els.append(el("note", "handnote", PAGE_LEFT_X, note_y, max(220.0, text_w(str(note), nsize) * 1.15), nsize * 1.35,
                      str(note), nsize, "title", 1))
        note_y += nsize * 1.35 + 26
    # 页内示意图（可选）：手账页空白处随手画的一张小题图，配一行手写名。
    # 这是 a2e 那套线稿在本 skill 里唯一合适的位置：它不解释概念，只帮观众认出「说的是哪件东西」。
    # 尺寸硬压 360（画宽 19%）：再大就变成"线稿当解释图"，比不画更差。
    fig = c.get("figure")
    if fig:
        if not isinstance(fig, dict) or not fig.get("draw"):
            p.err(f"{sid}: content.figure 要写 {{\"draw\": \"lib:<名字>\", \"label\": \"<这东西叫什么>\"}}")
        else:
            check_draw(p, sid, "content.figure", fig)
            fy = max(note_y, 480)
            w = min(360, max(220, int(fig.get("size") or 340)), max(180, int(SUBTITLE_CLEAR_Y - fy)))
            # 跟着说明往下走且底边不超过 SUBTITLE_CLEAR_Y，防止压入字幕区
            els.append(el("figure", "figure", PAGE_LEFT_X, fy, w, w, "", 0, "body", 1,
                          draw=fig.get("draw"), label=fig.get("label"), parts=fig.get("parts"),
                          figAt=int(fig.get("at", 1))))
    return els


# ---------------------------------------------------------------- recipes 
# 八个融合配方的**版面**。内容 schema 尽量小：弱模型只填「卡片说什么 / 结论是什么」，
# 线稿怎么摆、卡片多大、引线从哪拉，都由这里算。
SKETCH_BOX = {
    "left": {"x": 150, "y": 200, "w": 620, "h": 650},
    "right": {"x": 1150, "y": 200, "w": 620, "h": 650},
    "center": {"x": 560, "y": 170, "w": 800, "h": 700},
    "corner": {"x": 1480, "y": 620, "w": 260, "h": 260},
}
RECIPE_BOX = {
    "data-with-object": {"x": 1440, "y": 600, "w": 280, "h": 280},
    "list-icons": {"x": 1250, "y": 210, "w": 420, "h": 420},
    "component-annotated": {"x": 1500, "y": 640, "w": 240, "h": 240},
}


def lay_recipe(p, sid, recipe, c, variant):
    """返回 (els, sketch_box) 或 None（None = 沿用原版式，只加一块小线稿）。"""
    X, Y, W = BAND["x"], BAND["y"], BAND["w"]
    if recipe == "sketch-readout":
        cards = c.get("cards") or ([c["text"]] if c.get("text") else [])
        if not cards:
            p.err(f"{sid}: sketch-readout 需要 content.cards（1–2 条读数卡）")
            return [], SKETCH_BOX["left"]
        els, y = [], Y + 40
        for i, t in enumerate(cards[:2]):
            ls, s_, w_, h_ = fit_text(p, f"{sid}.cards[{i}]", str(t), TYPE["body"], 700, 3, lh=1.35)
            els.append(el(f"card{i + 1}", "card", 900, y, 780, h_ + 64, str(t), s_, "body", i, lines=ls, lh=1.35, pad=26))
            y += h_ + 64 + 36
        return els, SKETCH_BOX["left"]
    if recipe == "scene-verdict":
        v = c.get("verdict") or c.get("text") or ""
        if not v:
            p.err(f"{sid}: scene-verdict 需要 content.verdict（一句结论）")
            return [], SKETCH_BOX["center"]
        ls, s_, w_, h_ = fit_text(p, f"{sid}.verdict", v, TYPE["title"], 1200, 1)
        x = BAND["x"] + (BAND["w"] - (w_ + 80)) / 2
        return [el("verdict", "card", x, 790, w_ + 80, h_ + 60, v, s_, "body", 99, lines=ls, lh=1.3, pad=26)], {"x": 560, "y": 150, "w": 800, "h": 560}
    if recipe == "before-after":
        els = []
        for i, key in enumerate(("before", "after")):
            lab = "改之前" if key == "before" else "改之后"
            t = c.get(key) or ""
            x = 200 + i * 960
            els.append(el(f"{key}Label", "text", x, 700, 420, 60, lab, TYPE["title"], "title", i))
            if t:
                ls, s_, w_, h_ = fit_text(p, f"{sid}.{key}", str(t), TYPE["body"], 520, 2, lh=1.35)
                els.append(el(key, "card", x, 770, 560, h_ + 50, str(t), s_, "body", 1, lines=ls, lh=1.35, pad=22))
        return els, {"x": 660, "y": 120, "w": 600, "h": 520}
    if recipe == "hammer":
        t = c.get("text") or ""
        if not t:
            p.err(f"{sid}: hammer 需要 content.text（全片最该记住的那一句）")
            return [], SKETCH_BOX["corner"]
        ls, s_, w_, h_ = fit_text(p, f"{sid}.text", str(t), 96, 1200, 2, lh=1.15)
        return [el("text", "text", (X + (W - w_) / 2), 360, w_, h_, str(t), s_, "display", 99, lines=ls, lh=1.15, align="center")], SKETCH_BOX["corner"]
    return None


def lay_type(p, sid, c, variant):
    """直书页：把话直接排在纸上，不出卡片。

    为什么要这一版式。卡片唯一不可替代的作用是「可指代」——能被箭头指、被圈注、
    被放大镜吃进去。如果这一屏没有任何东西需要被指着说（三个并列的量、一句结论、
    一行算式），框就只是多一层编码：观众要先认出「这是一个单元」，才读到字。
    直书页去掉这一层，只用字号、行距、对齐三件事做层级。

    content:
      rows  [{"text": "47 呎 3 吋", "note": "结与结之间", "mark": 1}, …]  1–5 行
      text  只有一行时的简写
      lead  可选：压在所有行上面的一行小字（排版体 muted）

    mark = 第几句讲到时起笔画下划线。纸上的强调是笔，不是相机（放大交给镜头找焦点）。
    """
    rows = c.get("rows")
    if not rows:
        if c.get("text"):
            rows = [{"text": c["text"]}]
        else:
            p.err(f"{sid}: type 版式需要 content.rows（1–5 行，每行 {{text, note?, mark?}}）或 content.text")
            return []
    if not isinstance(rows, list):
        p.err(f"{sid}: content.rows 要是数组")
        return []
    if len(rows) > 5:
        p.hint(f"{sid}: rows 有 {len(rows)} 行（直书页 ≤5 行）；多出来的会被挤得读不动，只排前 5 行")
        rows = rows[:5]

    has_note = any(isinstance(r, dict) and r.get("note") for r in rows)
    main_w = 820 if has_note else 1320
    note_x, note_w = PAGE_LEFT_X + 800, 470
    # 直书页的字必须比组件标题大一档：它的层级全靠字号与行距，字号一软，
    # 三行字看起来就是「一张没画完的字卡」（内容占不满安全区）。
    base = {1: 132, 2: 120, 3: 108, 4: 92, 5: 82}[len(rows)]

    laid = []
    for i, r in enumerate(rows):
        if isinstance(r, str):
            r = {"text": r}
        txt = str(r.get("text") or "")
        if not txt:
            p.err(f"{sid}.rows[{i}]: 缺 text")
            continue
        # lh 必须与渲染端 Lines 的下限（SAFE_LH）一致，否则量出的高度比实际小，
        # 行与行就会叠在一起。
        ls, s, w, h = fit_text(p, f"{sid}.rows[{i}]", txt, base, main_w, 2, lh=SAFE_LH)
        note = r.get("note")
        nl, ns, nw, nh = [], 0, 0.0, 0.0
        if note:
            nl, ns, nw, nh = fit_text(p, f"{sid}.rows[{i}].note", str(note),
                                      max(34, min(44, s - 40)), note_w, 2, lh=SAFE_LH)
        laid.append(dict(txt=txt, ls=ls, s=s, w=w, h=h, note=note, nl=nl, ns=ns, nw=nw, nh=nh,
                         mk=r.get("mark"), reveal=str(r.get("reveal", "type"))))
    if not laid:
        return []

    GAP = 34.0
    total = sum(max(d["h"], d["nh"]) for d in laid) + GAP * (len(laid) - 1)
    lead = c.get("lead")
    lead_h = 0.0
    lls, lsz, lw = [], 0, 0.0
    if lead:
        lls, lsz, lw, lead_h = fit_text(p, f"{sid}.lead", str(lead), 36, 1320, 2, lh=SAFE_LH)
        total += lead_h + 46
    y = BAND["y"] + (BAND["h"] - total) / 2
    els = []
    if lead:
        els.append(el("lead", "text", PAGE_LEFT_X, y, lw, lead_h, str(lead), lsz, "muted", 0,
                      lines=lls, align="left", lh=SAFE_LH))
        y += lead_h + 46
    for i, d in enumerate(laid):
        kw = dict(lines=d["ls"], align="left", lh=SAFE_LH,
                  reveal=d["reveal"])
        if isinstance(d["mk"], int) and not isinstance(d["mk"], bool):
            kw["markAppear"] = d["mk"]
        # 第 i 行跟第 i 句：说到哪一行，哪一行才开始写。
        # 不能一律 appear=0——那样三行会在同一帧同时开始打，旁白还在第一句，
        # 观众已经把最后一句读完了，后面两句就白念了。
        a = i
        els.append(el(f"row{i + 1}", "text", PAGE_LEFT_X, y, d["w"], d["h"], d["txt"], d["s"],
                      "display", a, **kw))
        if d["note"]:
            els.append(el(f"row{i + 1}note", "text", note_x, y + max(0.0, (d["h"] - d["nh"]) / 2),
                          d["nw"], d["nh"], str(d["note"]), d["ns"], "muted", a,
                          lines=d["nl"], align="left", lh=SAFE_LH))
        y += max(d["h"], d["nh"]) + GAP
    return els


# 每个版式真正会直接下标的 content 键。缺了不是「运行时意外」，是作者写漏——
# 例如写 "layout":"bars" 却只填 text：这里给出可照着改的报错，而不是在 lay_bars 里抛 KeyError。
# media / custom / number 有自己的检查（能给出更具体的改法），不在这里重复拦。
REQUIRED_CONTENT = {
    "statement": ("text",),
    "define": ("term", "definition"),
    "bars": ("data",),
    "compare": ("before", "after"),
    "code": ("code",),
    "flow": ("steps",),
    "list": ("items",),
    "quiz": ("question", "options"),
    # type 版式二选一：rows 或 text（lay_type 自己有分支），两样都没有才是空镜——那由 build 处理。
}

_EXAMPLES = {
    "statement": '{"text": "一句话结论", "sub": "补充一行"}',
    "define": '{"term": "术语", "reading": "拼音", "definition": "一句解释"}',
    "bars": '{"title": "读速对比", "data": [{"label": "SSD", "value": 500}]}',
    "compare": '{"before": {"title": "误解"}, "after": {"title": "实际"}}',
    "code": '{"code": "const x = 1"}',
    "flow": '{"steps": [{"label": "第一步"}, {"label": "第二步"}]}',
    "list": '{"title": "要点", "items": ["第一条", "第二条"]}',
    "quiz": '{"question": "哪个更快？", "options": ["A", "B"]}',
}


def check_content(p, sid, layout, content) -> bool:
    """版式必需字段的**入口校验**：缺了就报一条能照着改的话，返回 False 让调用方跳过该镜。

    为什么不靠 lay_* 自己兜：十几个版式各写一遍等于十几处可能忘；
    且报错时机在「已经进到版式内部」，那时局部变量已经半初始化，容易连带别的异常。
    """
    need = REQUIRED_CONTENT.get(layout)
    if not need:
        return True
    missing = [k for k in need if content.get(k) in (None, "", [], {})]
    if not missing:
        return True
    p.err(f'{sid}：layout="{layout}" 缺 content.{"、".join(missing)} —— '
          f'照这个填：{_EXAMPLES.get(layout, "")}；'
          f'如果这一镜不需要这些内容，换一个版式（LAYOUTS 里的其它名字）。')
    return False


LAY = {"media": lay_media, "page": lay_page, "statement": lay_statement, "define": lay_define, "number": lay_number, "bars": lay_bars, "compare": lay_compare,
       "code": lay_code, "flow": lay_flow, "list": lay_list, "quiz": lay_quiz, "custom": lay_custom,
       "type": lay_type}
