#!/usr/bin/env python3
"""story_text.py — compose-story 的「文字怎么量、怎么折、怎么放进框」（P2-24 第一切片）

从 `compose-story.py` 切出的第二块（第一块是 `story_camera.py` 的取景计算）。
切它的理由不是行数，是**变化原因**：字宽、折行、孤字调整、字号收敛、行高地板
是同一类改动（P2-17 那一批全落在这里），每次调都要在 2300 行里翻；单独成文件后，
这类改动只碰这一个文件，改版式 / 时间轴的人不用读它。

边界（写清，避免又把别的东西塞回来）：
  - **在这里**：字宽（问 text_metrics 的真字体）、折行、孤字调整、字号收敛（fit_text）、
    行高地板 `SAFE_LH`、字幕字数口径（`cap_chars` / `line_len`）、朗读单位（`units`）。
  - **不在这里**：字幕怎么切（`split_caption`，仍留在 compose-story：它要读 BudouX 规则）、
    版式几何（`lay_*`）、时间轴（`compose` / `build`）。
  - **依赖方向**：只依赖 `text_metrics`（真字体度量），不依赖 Problems 的实现——
    `fit_text` 只调用 `p.err / p.fix / p.hint`，任何带这三个方法的收集器都能用。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import text_metrics as _tm  # noqa: E402  （必须在 sys.path 之后导入）

# 字号地板：低于它就是「手机上看不清」，不是审美选择（设计像素，1920 宽）。
MIN_FONT = 32
# 上屏标点集。折行「行首不放标点」、朗读停顿、字数口径共用这一份。
PUNCT = "，。！？；：、,.!?;:"
TAIL_PUNCT_RE = re.compile(r"[，。！？；：、,.!?;:\s]+$")

# 行高下限 = 渲染端 Lines 的 safeLh（assets/lecture-template/src/auto.tsx）。
# 排版端若按更小的 lh 算框高，下一行会落进上一行的行盒 → OverlapGate 硬拦（define 压字那条）。
# **唯一**行高真源；排版与渲染都对齐它，不再各自写 1.42。
# validate-skill-consistency 的数值对直接锚这一行（锚点文件已改到本模块）。
SAFE_LH = 1.42


def safe_lh(lh: float) -> float:
    return max(float(lh), SAFE_LH)


def is_wide(ch: str) -> bool:
    """全角/表意（含全宽通用标点）。只服务 mono 与无字体兜底。

    允许传入多字符 token（units() 的分词会给出 `/report` 这种）——
    多字符一律按「不是单个全角字」处理，与旧版正则语义一致。
    """
    if len(ch) != 1:
        return False
    cp = ord(ch)
    return (0x2E80 <= cp <= 0x9FFF or 0x3000 <= cp <= 0x303F
            or 0xFF00 <= cp <= 0xFFEF or ch in "—…†‡")


def text_w(s: str, size: float, mono=False, font: str = "kai") -> float:
    return _tm.text_width(s, size, role=font, mono=mono)


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
    """按宽度折行：中文按字、英文按词，不拆开英文单词 / 数字 / 破折号对。"""
    # 「——」是一个视觉单位，劈成两行的「—」/「—」读起来像两根杂线（实测 @maxw=200 会拆）。
    toks = re.findall(r"[A-Za-z0-9.%+\-_/@()']+|——|\s+|.", text)
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
            # 数字与中文单位不拆开（「47 呎 3 / 吋一个」这种断法，读的人要愣一下）。
            # tokenize 只保证不拆数字串本身；而「3」和「吋」之间还有**空格 token**，
            # 折行往往正好落在那个空格上——所以 t 是空格时同样要把数字一起挪到下一行。
            m = re.search(r"([0-9][A-Za-z0-9.%+\-_/@()']*)$", cur.rstrip())
            if m and (t.isspace() or re.match(r"[一-鿿]", t)):
                head = cur.rstrip()[:m.start()].rstrip()
                if head:  # 整行就是数字时不挪，否则会死循环
                    lines.append(head)
                    cur = cur.rstrip()[m.start():].lstrip() + t
                    continue
            lines.append(cur.rstrip())
            cur = t.lstrip()
    if cur.strip():
        lines.append(cur.rstrip())
    # 避免孤字：末行只剩 ≤2 个字时，从上一行挪字过来（中文排版的基本礼貌）
    if len(lines) >= 2 and len(TAIL_PUNCT_RE.sub("", lines[-1])) <= 2 and not mono:
        prev = lines[-2].rstrip()
        mt = re.search(r"([A-Za-z0-9.%+\-_/@()']+|[^\sA-Za-z0-9]{1,2})\s*$", prev)
        k = len(prev) - mt.start() if mt else 2
        # 但别把「数字 + 单位」拆开：prev 末尾是「47 呎 3 吋」时，只挪「吋」会留下「47 呎 3」，
        # 下一行以「吋」开头——比孤字更难读。这种情况整组（数字+单位）一起挪。
        mu = re.search(r"([0-9][A-Za-z0-9.%+\-_/@()']*\s*[一-鿿]{1,2})$", prev)
        if mu:
            k = len(prev) - mu.start()
        if 0 < k < len(prev):
            lines[-2], lines[-1] = prev[:-k].rstrip(), prev[-k:].lstrip() + lines[-1]
    return lines or [""]


def fit_text(p: "Problems", where: str, text: str, size: int, maxw: float, max_lines: int, lh=None, mono=False):
    """先换行，再降字号（不低于 MIN_FONT），仍放不下 → 报错并给出可容纳的字数。

    高度一律按 safe_lh(lh) 算：渲染端 Lines 有 `safeLh = max(lh, 1.42)` 的兜底，
    排版端若按更小的 lh 算，框高就比实际矮，下一行会压进上一行（OverlapGate 硬拦）。
    默认 lh 取 SAFE_LH；调用点仍可给更大的值（1.45 那种）。
    """
    lh = SAFE_LH if lh is None else lh
    s = size
    while True:
        ls = wrap(text, s, maxw, mono)
        if len(ls) <= max_lines:
            if s != size:
                p.fix(f"{where}: 字号 {size}→{s} 以放进 {max_lines} 行")
            w = max(text_w(l, s, mono) for l in ls)
            return ls, s, w, len(ls) * s * safe_lh(lh)
        if s <= MIN_FONT:
            cap = int(maxw / (MIN_FONT * 1.0)) * max_lines
            p.err(f"{where}: 「{text[:14]}…」在 {MIN_FONT}px 下仍超过 {max_lines} 行 —— 请删到约 {cap} 个汉字以内，或拆成两镜")
            return ls[:max_lines], s, maxw, max_lines * s * safe_lh(lh)
        s = max(MIN_FONT, s - 2)
