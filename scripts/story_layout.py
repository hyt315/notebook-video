#!/usr/bin/env python3
"""story_layout.py — compose-story 的「每种版式把元素摆在哪」（P2-24 第四切片）

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
# flow / compare 这类「一字排开」的版式，整组宽度上限。留白不是纯审美：满铺 1520 时
# 屏幕安全框（1660×666）被内容占满，相机没有任何可动余量，招牌镜想推都推不进去。
FLOW_TOTAL_MAX = 1300

# 允许直接上屏的单位（符号 / 公制短单位）。故事里的 `unit` 只该写这一列里的东西；
# 写成「占比 %」「公斤燃料 / 公斤干重」这类说明句，会把柱顶读数拼成「85占比 %」并折行压到柱子上。
UNIT_TOKENS = (
    "%", "‰", "°C", "°", "×", "元", "万元", "亿元", "美元", "公斤", "千克", "克", "吨",
    "米", "公里", "千米", "厘米", "毫米", "秒", "分钟", "小时", "天", "年", "人", "次",
    "个", "倍", "度", "瓦", "千瓦", "伏", "安", "GB", "MB", "TB", "KB", "ms", "kg", "km",
    "cm", "mm", "kWh", "W", "V", "A", "Gbps", "Mbps", "万次", "亿次", "万", "亿",
)
UNIT_OK = set(UNIT_TOKENS)


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
    # 以前按 ts*1.2 排，reading 会压进术语的行盒里（OverlapGate 硬拦「哈希」压「hash」）。
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


def lay_number(p, sid, c, variant):
    X, Y, W, H = BAND["x"], BAND["y"], BAND["w"], BAND["h"]
    # 缺 value 是作者写漏，不是运行时意外：给一条能照着改的话，不要抛 KeyError 让整片 compose 崩在栈里
    # （P2-25 长片/退化夹具抓到的：weak model 写 "layout":"number" 却只填 text 时整次 compose 失败）。
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
    size = 230
    unit = clean_unit(p, sid, c.get("unit", ""))
    # 预留宽度要**宽于**实际：数字用 tabular-nums 且字距 -0.02em，单位有 0.10em 的外边距，
    # 按 0.98 收窄去算会让「1.852」和「公里」叠在一起（实测两个像素级压字）。
    nw = text_w(txt, size) + text_w(unit, size * 0.42) + size * 0.12
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
        # 高度下限 300 → 380：compare 常常只有标题 + 两条短项，撑不满就显空，
        # 内容占地太小会被 validate-shot-motion 判「内容只占安全区」P0（画得太小=观众看不清）。
        return el(key, "panel", x, y, w, max(hh + 70, 380), d.get("title", ""), TYPE["title"], "body", appear,
                  side=side, title=d.get("title", "之前" if side == "before" else "之后"), value=d.get("value"), unit=clean_unit(p, f"{sid}.{side}", d.get("unit", "")),
                  decimals=int(d.get("decimals", 0)), items=[{"lines": a, "size": b} for a, b, _ in ih], tone=d.get("tone", "orange" if side == "before" else "green"))

    if mode == "morph":
        e1 = panel("before", "before", X + 360, 800, 0)
        e2 = panel("after", "after", X + 360, 800, c.get("morphLine", 1))
        e2["y"] = e1["y"]
        h = max(e1["h"], e2["h"]); e1["h"] = e2["h"] = h
        e1["morphTo"] = "after"; e2["morph"] = True
        els += [e1, e2]
    else:
        # 两栏各 620，整组 1320 居中：留出两侧呼吸（原来 660×2 + 间隙 = 1400 几乎铺满，
        # 相机没有可动空间，招牌镜推不进去，画面也顶边）。
        w = 620
        cx = X + W / 2
        e1 = panel("before", "before", cx - 1320 / 2, w, 0)
        # afterLine 缺省 0：两栏同帧入场。
        # 原来缺省 1（等第二句才出现），第 1 句时画面里只有左栏、右半屏空着——
        # 对比的语义是「并列」，缺一半就不是对比了。真要分先后，显式写 afterLine。
        e2 = panel("after", "after", cx + 1320 / 2 - w, w, c.get("afterLine", 0))
        h = max(e1["h"], e2["h"]); e1["h"] = e2["h"] = h
        els += [e1, e2, el("arrow", "arrow", e1["x"] + w + 40, Y + 40 + h / 2 - 30, 1320 - 2 * w - 80, 60, "", 0, "decor", c.get("afterLine", 0))]
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
    # 整行宽度收窄到 1300 并居中，两侧留呼吸。
    # 为什么：铺满 1520 的 4 节点，安全框几乎被占满，相机一点都推不进去（招牌镜直接做不出来）；
    # 收窄到 1300 后每个节点都能推到 1.15–1.25，而且画面两侧不再顶到边。
    total = min(W - 80, FLOW_TOTAL_MAX)
    nw = (total - 80 - arrow * (n - 1)) / n
    x0 = X + (W - total) / 2 + 20
    title_h = (els[0]["h"] + 46) if els else 24
    # 节点吃掉剩下的高度：给足，别让流程镜变成一排小方块（占比太低会被 shot-motion 判 P0）
    avail = H - title_h - 20
    node_min = max(240, int(avail * 0.62))
    # 0.18 → 0.42：原来整排节点贴着标题往下堆，下面空出一大截，
    # 观众第一眼读到的是「下半张纸没画完」。0.42 让整排落在安全区中部（视觉中心略偏上）。
    ny = Y + title_h + max(8, (avail - node_min) * 0.42)
    for i, st in enumerate(steps):
        st = st if isinstance(st, dict) else {"label": st}
        # lh 与渲染端（auto.tsx 的 Lines）必须逐字一致，否则多出来那一截就让第二行压到第一行上
        # （被 OverlapGate 硬拦）。渲染端现在的兜底是 safeLh = max(用户给, 1.42)：
        # 字号 46 时 1.25 压 414px²、1.32 压 274~282px²（「1665/借来」「今天/住户」都中招），
        # 1.42（=65.3px）才彻底分开。纯汉字的「今天/住户」也压，说明这是 46px 中文的固有行距需求，
        # 不是数字字形的特例。
        lls, ls_, lw, lh_ = fit_text(p, f"{sid}.steps[{i}].label", str(st["label"]), TYPE["title"], nw - 40, 2, lh=SAFE_LH)
        hh = lh_ + 60
        nlines = []
        if st.get("note"):
            _nlh = SAFE_LH  # 渲染端 safeLh 兜底，1.4 量出来的框会比实际矮
            nlines, ns, nww, nh = fit_text(p, f"{sid}.steps[{i}].note", st["note"], TYPE["body"], nw - 40, 3, lh=_nlh)
            hh += nh + 20
        x = x0 + i * (nw + arrow)
        els.append(el(f"step{i + 1}", "node", x, ny, nw, max(hh, node_min), st["label"], ls_, "accent" if st.get("hot") else "body",
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
    title = c.get("title")
    tls, ts, tw, th = [], 0, 0.0, 0.0
    if title:
        tls, ts, tw, th = fit_text(p, f"{sid}.title", title, TYPE["title"], 1300, 1)
    rows = []
    for i, it in enumerate(items):
        ils, isz, iw, ih = fit_text(p, f"{sid}.items[{i}]", it, TYPE["title"] if len(items) <= 3 else TYPE["body"], 1200, 2, lh=1.35)
        rows.append((ils, isz, ih, it))
    # 整体垂直居中，间距固定 34。
    # 原来从 BAND 顶端往下堆、把剩余空间摊进 gap：条目少时下半屏空着（读作「这张没做完」），
    # 条目多时 gap 被压到 16 又挤成一团。居中 + 固定间距，条目多少都不会塌。
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


# ---------------------------------------------------------------- 手账页 (3.6.0)
# 语法来自 cell 片（journal 皮肤）：**容器是纸，不是卡片**。整页不产生任何 card / panel / 圆角框。
# 一页 = 装裱好的真图版（右，占画宽 45%）+ 手写大字（页标题）+ 印章 + 一行手写说明。
# 为什么另开一族而不是改现有版式：现有 10 个版式的视觉语言是「白卡片 + 圆角 + 边框」，
# 那是幻灯片的语言；手账页一旦套上卡片框，就退回成 PPT（实测被评审判「像课件」）。
PAGE_MEDIA = {"x": 960, "y": 96, "w": 860, "h": 800}
# 墨图的画框比真图版收一圈：真图版是「贴上去的一张卡纸」，要顶到边；
# 墨图是「画在纸上的」，四周必须留出没画的空白，否则相机连推近的余量都没有
# （实测 860×800 时 anchor 占安全区 132%，画面顶死）。
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
            look = [float(look[0]), float(look[1])]
        except (TypeError, ValueError, IndexError):
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
        # 与 text_metrics 读的是同一份 hmtx——旧版用 1.0em 估算再乘 LEAN=1.06 补标点，
        # 实测「——」「……」估 0.56 实为 1.0em，LEAN 也盖不住（成片 S1 末尾「的」被裁那条）。
        # 真字宽下不再要安全系数。
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
        # 硬塞会把章盖在字上（实测「「细胞」这个名字的来历」末尾的「的」被压住）。
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
    # 3.6.2：原来是 64px——比手写大字（88）只小一点，而且和「页标题」抢同一层级，
    # 一页上出现两行差不多大的字，就成了「排版」而不是「写上去的」。降到 44–56：
    # 说明是附注，读者扫一眼就够，主视线仍在大字与图版上。
    note = c.get("note")
    note_y = y + (big_h + 34 if big else 0)
    # 章被挤到大字下面那一行时，批注必须再往下让出整枚章的高度。
    # 否则两者落在同一行：实测「胡克」章正好压在「第十八篇 · 软木」上，
    # 而且 OverlapGate 抓不到（章是 SVG 路径，不在它的文字块集合里）——只能靠排版时算准。
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
    # 尺寸硬压 360（画宽 19%）：再大就变成"线稿当解释图"，实测比不画更差。
    fig = c.get("figure")
    if fig:
        if not isinstance(fig, dict) or not fig.get("draw"):
            p.err(f"{sid}: content.figure 要写 {{\"draw\": \"lib:<名字>\", \"label\": \"<这东西叫什么>\"}}")
        else:
            check_draw(p, sid, "content.figure", fig)
            w = min(360, max(220, int(fig.get("size", 340)))
                    )
            # 跟着说明往下走：不写死 546，否则大字换成两行时图会压到说明上
            els.append(el("figure", "figure", PAGE_LEFT_X, max(note_y, 480), w, w, "", 0, "body", 1,
                          draw=fig.get("draw"), label=fig.get("label"), parts=fig.get("parts"),
                          figAt=int(fig.get("at", 1))))
    return els


# ---------------------------------------------------------------- recipes (3.5.0)
# 八个融合配方的**版面**。内容 schema 尽量小：弱模型只填「卡片说什么 / 结论是什么」，
# 线稿怎么摆、卡片多大、引线从哪拉，都由这里算。
SKETCH_BOX = {
    "left": {"x": 150, "y": 200, "w": 620, "h": 650},
    "right": {"x": 1150, "y": 200, "w": 620, "h": 650},
    "center": {"x": 560, "y": 170, "w": 800, "h": 700},
    "corner": {"x": 1480, "y": 700, "w": 280, "h": 280},
}
RECIPE_BOX = {
    "data-with-object": {"x": 1440, "y": 690, "w": 300, "h": 300},
    "list-icons": {"x": 1250, "y": 210, "w": 420, "h": 420},
    "component-annotated": {"x": 1500, "y": 720, "w": 240, "h": 240},
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
    """直书页（3.7.0）：把话直接排在纸上，不出卡片。

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
    # 三行字看起来就是「一张没画完的字卡」。实测 84px 时内容只占安全区 43%（P0）。
    base = {1: 132, 2: 120, 3: 108, 4: 92, 5: 82}[len(rows)]

    laid = []
    for i, r in enumerate(rows):
        if isinstance(r, str):
            r = {"text": r}
        txt = str(r.get("text") or "")
        if not txt:
            p.err(f"{sid}.rows[{i}]: 缺 text")
            continue
        # lh 必须与渲染端 Lines 的下限（1.42）逐字一致，否则量出的高度比实际小，
        # 行与行就会叠在一起——这个坑在 flow 节点上踩过一次（46px 时压 282px²）。
        ls, s, w, h = fit_text(p, f"{sid}.rows[{i}]", txt, base, main_w, 2, lh=1.42)
        note = r.get("note")
        nl, ns, nw, nh = [], 0, 0.0, 0.0
        if note:
            nl, ns, nw, nh = fit_text(p, f"{sid}.rows[{i}].note", str(note),
                                      max(34, min(44, s - 40)), note_w, 2, lh=1.42)
        laid.append(dict(txt=txt, ls=ls, s=s, w=w, h=h, note=note, nl=nl, ns=ns, nw=nw, nh=nh,
                         mk=r.get("mark")))
    if not laid:
        return []

    GAP = 34.0
    total = sum(max(d["h"], d["nh"]) for d in laid) + GAP * (len(laid) - 1)
    lead = c.get("lead")
    lead_h = 0.0
    lls, lsz, lw = [], 0, 0.0
    if lead:
        lls, lsz, lw, lead_h = fit_text(p, f"{sid}.lead", str(lead), 36, 1320, 2, lh=1.42)
        total += lead_h + 46
    y = BAND["y"] + (BAND["h"] - total) / 2
    els = []
    if lead:
        els.append(el("lead", "text", PAGE_LEFT_X, y, lw, lead_h, str(lead), lsz, "muted", 0,
                      lines=lls, align="left", lh=1.42))
        y += lead_h + 46
    for i, d in enumerate(laid):
        kw = dict(lines=d["ls"], align="left", lh=1.42,
                  reveal=str(r.get("reveal", "type")))
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
                          lines=d["nl"], align="left", lh=1.42))
        y += max(d["h"], d["nh"]) + GAP
    return els


# 每个版式真正会直接下标的 content 键。缺了不是「运行时意外」，是作者写漏——
# 弱模型常写 "layout":"bars" 却只填 text，以前会在 lay_bars 里抛 KeyError，
# 整次 compose 崩在栈里，读者只能看到一个 Python traceback（P2-25 夹具抓到的）。
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
    "flow": '{"steps": [{"text": "第一步"}, {"text": "第二步"}]}',
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
