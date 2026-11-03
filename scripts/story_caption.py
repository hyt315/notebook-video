#!/usr/bin/env python3
"""story_caption.py — compose-story 的「字幕怎么切、每句多久」（P2-24 第二切片）

从 `compose-story.py` 切出的第三块（前两块：`story_camera.py` 取景、`story_text.py` 文字）。
切它的理由同样是**变化原因**：字幕行宽、断点规则、朗读速度、标点停顿是一类改动；
版式、相机、输出格式改动不该碰这些，反之亦然。

边界：
  - **在这里**：术语占位符 `{{…}}` 的解析、>16 字怎么劈、断点来源（BudouX / 避头尾 / ASCII 词内不拆）、
    每个词的时间、朗读速度 `CPS` 与它的**唯一**写入点 `set_cps()`。
  - **不在这里**：字有多宽（`story_text.text_w`）、一行算几个字（`story_text.line_len`）、
    时间轴怎么衔接镜头（`compose-story.build` 的 `LINE_GAP_MS` / `SHOT_GAP_MS`）。
  - **状态**：`_RULE` 是断点规则模块的缓存（由 `setup_break_rule(project)` 装载），只增不减；
    `CPS` / `CHAR_MS` 是运行期可变的（`--cps` / story.cps），**只能通过 `set_cps()` 改**——
    外部直接赋值会让 `time_cue` 读到旧值，这正是把常量搬进模块时最容易踩的坑。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from story_text import PUNCT, line_len, units  # noqa: E402  （必须在 sys.path 之后导入）

CPS = 4.5                      # 中文朗读 / 阅读速度：4–5 字/秒，取 4.5
CHAR_MS = 1000 / CPS           # ≈ 222 ms
COMMA_MS, STOP_MS = 150, 300   # 句中逗号 / 句末停顿
MAX_CHARS = 16                 # 单行字幕上限（门禁与拆行共用这一份）
TERM_RE = re.compile(r"\{\{([^}|]+)(?:\|([^}]+))?\}\}")


def set_cps(cps: float) -> None:
    """`--cps` / story.cps 的唯一切入点。

    为什么要有这个函数：`time_cue` 读的是本模块的 `CHAR_MS`。若调用方只改自己模块里的
    同名变量，字幕时长会**悄悄**停在 4.5 字/秒——CLI 看着生效，产物没变。
    """
    global CPS, CHAR_MS
    CPS = float(cps)
    CHAR_MS = 1000 / float(cps)


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
    # 空文本是合法输入（整行只有空白 / 作者写漏）：返回空词表与零时长，
    # 不要用 words[-1] 崩在这里——调用方那时已经报过「台词为空」，需要的是继续走完并给出可读错误。
    if not words:
        return [], int(round(start_ms))
    return words, int(round(words[-1]["end"]))
