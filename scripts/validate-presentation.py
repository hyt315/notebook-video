#!/usr/bin/env python3
"""validate-presentation.py · 呈现效果门禁（T1：纯算术，不渲染）

它回答的是**其它门禁都没问过**的问题：观众此刻该看哪里、读不读得过来。
现有的门禁查的是"画面里有没有 / 够不够多 / 会不会撞"；这一道查"讲与画对不对得上、读得动吗"。
（数量口径 2026-09-22 复核：全技能 14 道门禁 = 构建期 6 + 渲染期 7 + 成片后验 1，
  表见 SKILL.md 的 The gates；本道是构建期那 6 道之一 —— 数字变了以那张表为准，别在本文件里改。）
每条判据都是纯算术（读 manifests 与源码字面量），零新增数据模型、不需要渲染。

判据（可计算形式见下）：

  G-1 时间接近（P0）——把授权契约第 9 条「元素出现帧绑到讲到它的那一句」变成代码
    ① 每个 beat 的绝对帧 ∈ [shot.from, shot.to]（含边界：允许"切在下一句起点"的那一拍）
    ② 每个 beat 声明的 cue ∈ [cueFirst, cueLast] 或 = cueLast+1（同上）
    ③ 每个 beat 的 offset ≥ −12 帧（元素不得早于它那句 0.4s 以上出现 = 防提前剧透）
    ③b 每个 beat 的 offset ≤ 该句帧数 + 8（**不得晚于那句讲完**：台词讲完了元素才出现 = 脱节）。
       上界与下界缺一不可——第一版只有③，`{cue:0, offset:200}`（讲完 6.7s 才出现）照样 PASS。
    ⚠️ 8 帧这条容差是**承重墙**：模板最紧的合法拍就是 `offset = 该句帧数`（"句末那拍"是设计约定），
       把容差整个吃掉。所以另外报一条 P1（`BEAT_TIGHT_FRAMES=4`）：距上界 ≤4 帧就预警。
       实测口径见 references/presentation-gate.md §G-1；**每次换配音 / 重算 cue 都要重跑本门禁**。
    ④ 每条 cue 在本镜内至少有一个 beat；确实不需要的必须在 shots.json 里显式声明
       `silentCues: [cueIndex, ...]`（显式声明才放行——这就是"要求写出结论"的做法）
    ⚠️ 与调研报告原文的差异（报告写的是 `|beat − cueStart| ≤ 6`）：**照抄会给正确的数据报错**。
       我们的 beats 本来就允许句内偏移（`{cue:13, offset:100}` 是"同一句的第二拍"，
       S7/S8 各有一处，实测会被逐字判为偏差 96–100 帧）。所以真正的可检查形式是
       "beat 落在它声明的那句/那一镜的范围内、且不提前也不拖后"，而不是"必须贴住句首 6 帧"。

  G-2 字幕阅读预算（P0）——Netflix 中文（简体）Timed Text Style Guide
    · 阅读速度 ≤ 9 加权字/秒（成人档；加权：CJK 计 1，ASCII/数字计 0.5，**不需要分词**）
    · 单行 ≤ 16 加权字；≤ 2 行

  G-3 可读性底线（P0 地板 + P1 档位）
    · P0：任何 `fontSize: <13` 的字面量（13 = 技能自己的 `MIN_LABEL_FONT` 口径，不是新魔数）
    · P1：13–15（低于"标注 ≥16"档）
    · P0：正文色（ink / white）落在主题各表面上 < 4.5:1（WCAG 2.2 SC 1.4.3，不四舍五入）
    · P1：`muted` on 表面 < 4.5（它是装饰性 kicker，按大字 3:1 判）
    · P1：强调色当**文字色**时低于要求（<24px 要 4.5、≥24px 或 ≥18.5px 粗体要 3.0）
      —— 这一条是**已知的真实缺陷**（四套皮肤里 gold/green 当文字色只有 1.4–3.3:1），
      怎么处置（调深色值 / 约定这些色只用于图形）是审美决定，留给用户，见 CHANGELOG。

  G-5 节拍拥挤（P1，代理指标）
    · 同一镜内 ≥3 个 beat 落在 12 帧窗口 → P1（"好几件事挤在一拍上"）
    · ⚠️ 调研报告原文的 G-5 是"每帧新开始的入场动画数直方图"，那需要元素级的 `enters` 声明
      （现有数据没有）→ 这里只做数据支持得了的代理形式，并在文档里写明差距。

退出码：0 通过（P0=0）/ 1 有 P0 / 2 用法或文件错误。零第三方依赖，Python 3.10+。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FPS = 30
BEAT_SPOILER_FRAMES = 12   # 3-③：不得早于所属 cue 超过 12 帧（0.4s）
BEAT_LATE_FRAMES = 8       # G-1③b：允许晚于该句结束的容差（帧）
# G-1③b 贴边预警：这条容差是**承重墙**不是安全边际。实测（模板）最紧的合法拍
# offset = 该句帧数（"元素在这句讲完时出现"就是设计约定），把 8 帧全部吃掉——
# 也就是说任何一次配音重跑（句子变短）都会先从这里把合法拍挤成 P0。
# 所以剩余容差 ≤4 帧时先报 P1：让"脆"这件事在变成 P0 之前就被看见。
BEAT_TIGHT_FRAMES = 4      # G-1③b-P1：距上界只剩这么多帧 = 贴边
BEAT_CLUSTER_FRAMES = 12   # G-5：聚簇窗口
BEAT_CLUSTER_MAX = 3       # G-5：窗口内 ≥3 个 beat 才算拥挤
CPS_MAX = 9.0              # G-2：Netflix 中文成人档
LINE_MAX = 16              # G-2：单行加权字上限
FONT_FLOOR = 13            # G-3：绝对地板（= components/data.tsx 的 MIN_LABEL_FONT）
FONT_LABEL_MIN = 16        # G-3：标注档
CONTRAST_TEXT = 4.5        # WCAG 2.2 SC 1.4.3 正文
CONTRAST_LARGE = 3.0       # 大字号（≥24px 或 ≥18.5px 粗体）

norm = lambda s: re.sub(r"\s+", "", s)

VALUE_POS = "=([{,:;?|&!+*-<>~^"   # `noncode` 用：引号只有出现在"值位置"才开字符串


def noncode(text: str) -> str:
    """把"不是代码"的位置（注释内部 + **字符串字面量内部**）换成空格，**长度与行号一字不动**。

    为什么是"抹掉"而不是"按行过滤"：抹掉之后正则照旧能跑，行号与列位置都还是原始的，
    所以报出来的行号永远等于编辑器里那一行（第二轮复核抓到过 464 vs 真实 467 的漂移）。

    四条必须同时成立，每条都是实测踩出来的：
    ① 注释里写历史反例（"fontSize: 9 是禁止的写法"）不该判 P0；
    ② 块注释**按跨行数补回等量换行**，否则整体行号上移；
    ③ `//` 只有在**字符串外**才是注释——否则 `background:"url(https://…)"` 之后写的 fontSize
       会被整行吃掉，成了漏检面；
    ④ 引号只在**值位置**才开字符串（前一个代码位置的非空白字符属于 `=([{,:;?|&!+*-<>~^` 或行首）：
       JSX 文本里的撇号（`don't`）不该毒化整行；而 `'…'` / `"…"` 不跨行，行尾未闭合就收尾。
    ⑤（第三轮复核指出）**字符串里放代码样例**是本仓库的常规写法——接触表/测试页里
       `const CODE = `import {...} from './x';`` 就是。字符串里的 import / `fontSize: 8`
       不是真的代码，扫进去就是假 P0；反过来，它也不该给 import_integrity 贡献"幽灵导出"。

    ⚠️ 这份实现原先是 `check_readability` 里的闭包（函数体一字未改，只是搬到模块层），
    因为 G-15（`evidence` 有没有被当成 JSX 用）也要用同一套口径：**注释里写到的组件名不算"用到"** ——
    这正是 overview-film S2 的实况（`evidence: MetricGrid` 只出现在一行注释里，代码里已换成手绘）。
    一份实现两个用点，改这里两个判据同时生效。
    """
    out = [ch if ch not in "\n" else "\n" for ch in text]
    i, n, quote, prev = 0, len(text), "", ""

    def blank(lo: int, hi: int) -> None:
        for k in range(lo, hi):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        ch = text[i]
        if quote:
            blank(i, i + 1)
            if ch == "\\" and i + 1 < n:      # 转义：连下一个字符一起吃掉
                blank(i + 1, i + 2)
                i += 2
                continue
            if ch == quote:
                quote = ""
            elif ch == "\n" and quote != "`":
                quote = ""                     # '…' / "…" 不跨行：行尾未闭合就收尾
            i += 1
            continue
        if ch in "'\"`" and (prev == "" or prev in VALUE_POS):
            quote = ch
            blank(i, i + 1)
        elif text.startswith("//", i):
            j = text.find("\n", i)
            blank(i, n if j < 0 else j)        # 吃到行尾；换行留着（行号不变）
            i = n if j < 0 else j
            continue
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            blank(i, n if j < 0 else j + 2)    # 块注释内部全抹，换行不抹
            i = n if j < 0 else j + 2
            continue
        elif not ch.isspace():
            prev = ch
        i += 1
    return "".join(out)


def ms_frame(ms: float) -> int:
    return int(round(ms * FPS / 1000))


def weighted_len(text: str) -> float:
    """加权字数：CJK 计 1，ASCII/数字计 0.5，标点计 0.5（不需要分词）。"""
    out = 0.0
    for ch in re.sub(r"\s+", "", text):
        out += 1.0 if ord(ch) > 0x2E80 else 0.5
    return out


def weighted_line_lens(text: str) -> list[float]:
    """**逐行**加权字数（Netflix 的 16 字/行是**每行**的上限，不是整条）。

    ⚠️ 复核抓到的实现错（第一版）：我把文本先 `re.sub(r"\\s+","")` 再去量整条，
    于是"两行、每行 9 字（合计 18）"被判成 `单行 19 加权字 > 16` —— **误杀合法的两行字幕**，
    而报错文案还自称"单行"。现在按字面实现：先按换行切行，再逐行量。
    """
    lines = [l for l in text.split("\n")] or [text]
    return [weighted_len(l) for l in lines if l.strip()] or [0.0]


# ---------------------------------------------------------------- G-1 / G-2 / G-5
def check_timeline(project: Path) -> tuple[list, list]:
    p0, p1 = [], []
    shots_doc = json.loads((project / "manifests" / "shots.json").read_text(encoding="utf-8"))
    resolved_doc = json.loads((project / "manifests" / "shots.resolved.json").read_text(encoding="utf-8"))
    cues = json.loads((project / "manifests" / "caption-cues.json").read_text(encoding="utf-8"))["cues"]
    resolved = resolved_doc["shots"] if isinstance(resolved_doc, dict) and "shots" in resolved_doc else resolved_doc
    declared = shots_doc["shots"] if isinstance(shots_doc, dict) and "shots" in shots_doc else shots_doc

    by_id = {s["id"]: s for s in resolved}
    for dec in declared:
        sid = dec.get("id", "?")
        rec = by_id.get(sid)
        if not rec:
            continue
        cue_first, cue_last = int(rec["cueFirst"]), int(rec["cueLast"])
        silent = {int(x) for x in (dec.get("silentCues") or [])}
        covered: set[int] = set()
        for bt in dec.get("beats") or []:
            ci = int(bt["cue"])
            off = int(bt.get("offset", 0))
            frame = ms_frame(cues[ci]["start_ms"]) + off if 0 <= ci < len(cues) else -1
            # ① 落在本镜区间内（含 to 边界）
            if frame < rec["from"] or frame > rec["to"]:
                p0.append({"id": sid, "issue": f"beat(cue{ci}+{off}) 落在 {frame} 帧，超出本镜 [{rec['from']},{rec['to']}]"})
            # ② 声明的 cue 在本镜的 cue 区间内（允许 cueLast+1 = 切在下一句起点）
            if not (cue_first <= ci <= cue_last + 1):
                p0.append({"id": sid, "issue": f"beat 声明 cue{ci}，超出本镜 cue 区间 [{cue_first},{cue_last}]"})
            # ③ 不提前剧透
            if off < -BEAT_SPOILER_FRAMES:
                p0.append({"id": sid, "issue": f"beat(cue{ci}) offset={off} 早于该句 {abs(off)} 帧（上限 {BEAT_SPOILER_FRAMES}）"})
            # ③b **也不能太晚**：beat 必须落在它声明那句的区间内（+ 容差）。
            # 复核抓到的口径漏洞：第一版只防"早"，`offset=+200`（台词讲完 6.7s 才出现）
            # 照样 PASS —— 契约"元素出现帧绑到讲到它的那一句"是**双向**的。
            # 上界 = 该句时长 + 容差，且不得晚于本镜结束。
            cue_ms = int(cues[ci]["speech_end_ms"]) - int(cues[ci]["start_ms"]) if 0 <= ci < len(cues) else 0
            limit = ms_frame(cue_ms) + BEAT_LATE_FRAMES
            if off > limit:
                p0.append({"id": sid, "issue": f"beat(cue{ci}) offset={off} 晚于该句结束 {off - ms_frame(cue_ms)} 帧（上限 {BEAT_LATE_FRAMES} 帧容差；该句 {ms_frame(cue_ms)} 帧）：元素在旁白讲完后才出现 = 与台词脱节"})
            elif limit - off <= BEAT_TIGHT_FRAMES:
                p1.append({"id": sid, "issue": f"beat(cue{ci}) 距容差上界只剩 {limit - off} 帧（该句 {ms_frame(cue_ms)} 帧 / offset={off}）：合法但**贴边**，配音或 cue 表一变就可能落成 P0 —— 请把它挪回句中或句末"})
            if cue_first <= ci <= cue_last:
                covered.add(ci)
        # ④ 每条 cue 至少有一拍（除非显式声明 silentCues）
        for ci in range(cue_first, cue_last + 1):
            if ci not in covered and ci not in silent:
                p0.append({"id": sid, "issue": f"cue{ci}「{cues[ci]['text'][:10]}」在本镜内没有任何 beat（若确实不需要，在本镜声明 silentCues:[{ci}]）"})
        # G-5 代理：同一镜内 ≥3 个 beat 挤在 12 帧窗口
        abs_beats = sorted(rec.get("beatsAbs") or [])
        for i in range(len(abs_beats) - BEAT_CLUSTER_MAX + 1):
            win = abs_beats[i : i + BEAT_CLUSTER_MAX]
            if win[-1] - win[0] <= BEAT_CLUSTER_FRAMES:
                p1.append({"id": sid, "issue": f"{BEAT_CLUSTER_MAX} 个 beat 挤在 {win[-1]-win[0]} 帧内（f={win[0]}–{win[-1]}）：多件事挤在一拍，观众分不清该看哪"})
                break

    # G-2 字幕阅读预算
    for i, cu in enumerate(cues, 1):
        text = str(cu.get("text", ""))
        dur = max(0.001, (int(cu["speech_end_ms"]) - int(cu["start_ms"])) / 1000.0)
        line_lens = weighted_line_lens(text)      # 逐行量（Netflix 的 16 字/行是每行的上限）
        wl = sum(line_lens)
        cps = wl / dur
        if cps > CPS_MAX:
            p0.append({"id": f"cue{i}", "issue": f"阅读速度 {cps:.1f} 字/秒 > {CPS_MAX}（{wl:.0f} 加权字 / {dur:.1f}s）：{text[:16]}"})
        worst = max(line_lens)
        if worst > LINE_MAX:
            p0.append({"id": f"cue{i}", "issue": f"某一**行** {worst:.0f} 加权字 > {LINE_MAX}（本 cue 共 {len(line_lens)} 行）：{text[:16]}"})
        if len([l for l in text.split("\n") if l.strip()]) > 2:
            p0.append({"id": f"cue{i}", "issue": f"字幕超过 2 行：{text[:16]}"})
    return p0, p1


# ----------------------------------------------------------------------- G-3
FONT_RE = re.compile(r"fontSize:\s*([0-9]{1,3})")
TYPE_RE = re.compile(r"fontSize:\s*TYPE\.(\w+)")


def parse_type_table(project: Path) -> dict:
    for p in project.rglob("kit.tsx"):
        m = re.search(r"export const TYPE\s*=\s*\{([^}]*)\}", p.read_text(encoding="utf-8"))
        if m:
            return {k: float(v) for k, v in re.findall(r"(\w+):\s*([0-9.]+)", m.group(1))}
    return {}


def parse_palette(path: Path) -> dict:
    s = path.read_text(encoding="utf-8")
    i = s.find("palette")
    if i < 0:
        return {}
    j, k = s.find("{", i), None
    k = s.find("\n};", j)
    if k < 0:
        k = s.find("\n}", j)
    return {m.group(1): m.group(2) for m in re.finditer(r"(\w+):\s*'([^']+)'", s[j:k])}


def _srgb(c: float) -> float:
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rel_lum(hexs: str) -> float:
    h = hexs.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _srgb(r) + 0.7152 * _srgb(g) + 0.0722 * _srgb(b)


def contrast(a: str, b: str) -> float:
    la, lb = rel_lum(a), rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def check_readability(project: Path) -> tuple[list, list]:
    p0, p1 = [], []
    src = project / "src"
    if not src.is_dir():
        return p0, p1
    types = parse_type_table(project)
    band: dict[str, list[tuple[int, int]]] = {}   # 13–15 档：按文件聚合，避免一条一处刷屏
    files = sorted(list(src.rglob("*.tsx")))
    # 抹注释/字符串的实现已提到模块层 `noncode()`（G-15 也要用同一套口径，理由见那里的 docstring）

    for f in files:
        for n, line in enumerate(noncode(f.read_text(encoding="utf-8")).splitlines(), 1):
            rel = f"{f.relative_to(project)}:{n}"
            for m in FONT_RE.finditer(line):
                size = int(m.group(1))
                if size < FONT_FLOOR:
                    p0.append({"id": "src", "issue": f"{rel} fontSize:{size} 低于绝对地板 {FONT_FLOOR}（口径 = MIN_LABEL_FONT）"})
                elif size < FONT_LABEL_MIN:
                    band.setdefault(str(f.relative_to(project)), []).append((n, size))
            for m in TYPE_RE.finditer(line):
                size = types.get(m.group(1))
                if size is None:
                    p1.append({"id": "src", "issue": f"{rel} TYPE.{m.group(1)} 不在字号表里"})
                elif size < FONT_FLOOR:
                    p0.append({"id": "src", "issue": f"{rel} TYPE.{m.group(1)}={size} 低于绝对地板 {FONT_FLOOR}"})

    for rel, items in sorted(band.items()):
        sizes = sorted({s for _, s in items})
        p1.append({"id": "src", "issue": f"{rel} 有 {len(items)} 处字号在 13–15（{'/'.join(str(x) for x in sizes)}px，低于标注档 {FONT_LABEL_MIN}；行号 {', '.join(str(n) for n, _ in items[:6])}{' 等' if len(items) > 6 else ''}）"})

    # ---- 主题对比度：只判"真的会同时出现"的配对 ----
    #
    # ⚠️ 第一版这里犯了个典型的假阳性：把"每个文字色 × 每个表面"全都交叉算了一遍，
    # 于是 `white on paper = 1.00:1` 被报成 P0——而白字**永远不会**放在白纸上。
    # 现在改成按代码里真实出现的用法取配对（同一次运行里扫出来的 `color: C.x` / `background: C.x`）：
    #   · 正文：ink on {paper, paperWarm, paperBase}
    #   · 深底上的字：white on ink
    #   · 反白按钮：white on <任何被当 background 用过的强调色>
    #   · 次要文字：muted on {paper, paperWarm, paperBase}（按大字 3:1 判，低于 4.5 只提示）
    #   · 强调色当文字色：<被当 color 用过的强调色> on {paper, paperWarm, paperBase}（P1，按主题聚合）
    # ⚠️ 第二处假阳性（第一版与第二版都踩过）：**不能用"静态交叉"去猜"谁会压在谁上面"**。
    # 第一版把 white × paper 报成 P0（白字永远不压白纸）；第二版又靠 `background: C.x` 推断，
    # 结果 `background: C.paper`（卡片底色）把 `white on paper` 又请了回来。
    # 结论：这里的配对必须是**声明的契约**，不是推断。契约来自本技能自己的用法：
    #   · 正文      ink   on {paper, paperWarm, paperBase}            → P0（<4.5 阻断）
    #   · 深底反白  white on {ink}                                     → P0
    #   · 彩色反白  white on {blue, orange, orangeDeep, green, gold, red, navy}  → P1 聚合
    #     （PillTag / StampBanner / VerdictBar / 按钮都会用这些色当填充 + 白字）
    #   · 次要文字  muted on {paper, paperWarm, paperBase}             → 大字档 3:1
    #   · 彩字      <强调色> on {paper, paperWarm, paperBase}          → P1 聚合
    ACCENT_FILLS = ("blue", "orange", "orangeDeep", "green", "gold", "red", "navy")
    # 文字安全色（2026-09-21 加）：主题里为每种强调色提供的 *Ink 变体，**专门用于当文字**。
    # 它们必须过 4.5:1（正文档），否则"压暗到能当文字用"这个约定就是空话 ——
    # 这一条同时是**新增机制的自检**：没有它，加了 Ink 也不会有人验。
    ACCENT_INKS = ("blueInk", "orangeInk", "greenInk", "goldInk", "redInk")
    used_as_text: dict[str, set[str]] = {}
    for f in files:
        body = f.read_text(encoding="utf-8")
        for m in re.finditer(r"color:\s*(?:C|THEME\.palette)\.(\w+)", body):
            used_as_text.setdefault(m.group(1), set()).add(f.name)

    for tf in sorted((src / "theme").glob("*.tsx")):
        pal = parse_palette(tf)
        if not pal:
            continue
        name = tf.stem
        surfaces = ["paper", "paperWarm", "paperBase"]
        hexed = {k: v for k, v in pal.items() if isinstance(v, str) and v.startswith("#")}

        def worst(fg: str) -> tuple[float, str] | None:
            if fg not in hexed:
                return None
            items = [(contrast(hexed[fg], hexed[bg]), bg) for bg in surfaces if bg in hexed]
            return min(items) if items else None

        # 正文色（P0）
        if "ink" in hexed:
            for bg in surfaces:
                if bg in hexed:
                    c = contrast(hexed["ink"], hexed[bg])
                    if c < CONTRAST_TEXT:
                        p0.append({"id": f"theme:{name}", "issue": f"正文色 ink on {bg} = {c:.2f}:1 < {CONTRAST_TEXT}"})
        # 深底反白（P0）
        if "white" in hexed and "ink" in hexed:
            c = contrast(hexed["white"], hexed["ink"])
            if c < CONTRAST_TEXT:
                p0.append({"id": f"theme:{name}", "issue": f"反白文字 white on ink = {c:.2f}:1 < {CONTRAST_TEXT}"})
        # 彩色反白 + 彩字：**按主题各聚合成一条**，否则一套皮肤就是几十条噪声
        ink_bad = []
        for a in ACCENT_INKS:
            if a not in hexed:
                continue
            w = min((contrast(hexed[a], hexed[bg]), bg) for bg in surfaces if bg in hexed)
            if w[0] < CONTRAST_TEXT:
                ink_bad.append(f"{a} {w[0]:.2f}:1(on {w[1]})")
        if ink_bad:
            p0.append({"id": f"theme:{name}", "issue": "文字安全色没过 4.5:1（它们是**专门**用来当文字色的）：" + " · ".join(ink_bad)})
        white_bad = [f"{a} {contrast(hexed['white'], hexed[a]):.2f}:1" for a in ACCENT_FILLS if a in hexed and "white" in hexed and contrast(hexed["white"], hexed[a]) < CONTRAST_LARGE]
        if white_bad:
            p1.append({"id": f"theme:{name}", "issue": f"彩色填充上的白字对比不足（需 3.0）：{' · '.join(white_bad)}"})
        tone_bad = []
        for fg in sorted(used_as_text):
            if fg in {"ink", "white", "muted", "paper", "paperWarm", "paperBase"}:
                continue
            w = worst(fg)
            if w and w[0] < CONTRAST_TEXT:
                tone_bad.append(f"{fg} {w[0]:.2f}:1(on {w[1]}){' ✗<3' if w[0] < CONTRAST_LARGE else ''}")
        if tone_bad:
            users = sorted({f for fg, fs in used_as_text.items() if fg not in {"ink", "white", "muted"} for f in fs})
            p1.append({"id": f"theme:{name}", "issue": f"强调色当文字色对比不足（大字需 3.0 / 小字需 4.5）：{' · '.join(tone_bad)}；用在 {', '.join(users[:3])}{' 等' if len(users) > 3 else ''}——真缺陷，处置见 CHANGELOG"})
        # 次要文字（muted）
        if "muted" in hexed:
            w = worst("muted")
            if w and w[0] < CONTRAST_LARGE:
                p0.append({"id": f"theme:{name}", "issue": f"muted on {w[1]} = {w[0]:.2f}:1 < {CONTRAST_LARGE}"})
            elif w and w[0] < CONTRAST_TEXT:
                p1.append({"id": f"theme:{name}", "issue": f"muted 最差 {w[0]:.2f}:1（on {w[1]}）< {CONTRAST_TEXT}：muted 是装饰性 kicker，按大字 3:1 可接受，提示一档"})
    return p0, p1


# ------------------------------------------------- G-14/G-15/G-16 讲法字段完整性
# 编号说明（2026-09-21 修撞号）：这一组原来标成 "G-6"，而 **G-6 是调研报告里"对比层结构闭合"**
# 的编号（见 references/presentation-gate.md 的"还没做的"）。本组的编号以
# references/narrative-moves.md §4 为准：G-14 `move` 闭合 / G-15 `evidence` 被当成 JSX 用 /
# G-16 误解与留白（G-17 known→new 闭合尚未实现）。
# ⚠️ G-15 的档次在 2026-09-22 从"真的会动（本镜 + 帧驱动链）"退回"名字被当成 JSX 用"：
#    口径、代价与"不做哪半边"逐条写在下面 check_evidence 那一节，也写回了 narrative-moves.md §2。
#
# 为什么加这一条（2026-09-21）：`narrative-moves.md` 把 move / evidence / hold /
# misconception 四个槽位写成**必填**，但**十道门禁没有一道读过它们**，而且：
#   · `resolve-shots.py` 在把 shots.json 解析成 shots.resolved.json 时**把这四个字段整组丢掉**
#     （那份解析结果里只有 skeleton/live/keys/beats… 没有 move/evidence/hold/misconception）
#     → 下游所有读 resolved 的门禁**根本看不到它们**，想查也没得查；
#   · 实测：把 S19 的 move 删掉，改前全部门禁照旧 PASS。
# 这一条读**作者手写的 shots.json**（字段的唯一定源），并把 resolve 的透传一并修好（同一轮）。
MOVES = {"引入", "定位", "推进", "传递", "对比", "拆分/合并", "累积", "收束", "反证", "回看"}
HOLD_MIN = 40        # 留白预算下限：narrative-moves.md 里**标定**出来的线（不是拍的）
MOVE_MIN_KINDS = 5   # 全片至少用到几种叙事动作（10 种里挑）：只写 1–2 种等于没有编排
MOVE_RUN_LIMIT = 3   # G-14②：同一 move **连续 ≥3 镜**即违规（文档原文"不得连续 ≥3 镜"，含 3）


def check_narrative(project: Path) -> tuple[list, list]:
    p0, p1 = [], []
    doc = json.loads((project / "manifests" / "shots.json").read_text(encoding="utf-8"))
    shots = doc["shots"] if isinstance(doc, dict) and "shots" in doc else doc
    kinds: dict[str, int] = {}
    for s in shots:
        sid = s.get("id", "?")
        mv = str(s.get("move") or "").strip()
        ev = str(s.get("evidence") or "").strip()
        hold = s.get("hold")
        if not mv:
            p0.append({"id": sid, "issue": "缺 move（叙事动作）：讲法规范要求每镜声明它在这一章里干哪件事"})
        elif mv not in MOVES:
            p0.append({"id": sid, "issue": f"move=«{mv}» 不在叙事动作表里（只能是 {'/'.join(sorted(MOVES))}）"})
        else:
            kinds[mv] = kinds.get(mv, 0) + 1
        if not ev:
            p0.append({"id": sid, "issue": "缺 evidence（该镜内真的会变的那件组件）：没有它就没法验证「讲到哪亮到哪」"})
        if hold is None:
            p0.append({"id": sid, "issue": "缺 hold（留白预算，单位帧）"})
        elif not isinstance(hold, int) or hold < HOLD_MIN:
            p0.append({"id": sid, "issue": f"hold={hold!r} 低于标定线 {HOLD_MIN} 帧"})
        mis = str(s.get("misconception") or "").strip()
        nomis = bool(s.get("noMisconception"))
        why = str(s.get("why") or "").strip()
        if mis and nomis:
            p0.append({"id": sid, "issue": "同时写了 misconception 与 noMisconception：只能二选一"})
        elif not mis and not nomis:
            p0.append({"id": sid, "issue": "必须二选一：misconception（本镜要拆掉的误解）或 noMisconception(+why)"})
        elif nomis and not why:
            p0.append({"id": sid, "issue": "标了 noMisconception 却没写 why（为什么不设误解）"})

    # ---- G-14② 同一 move 不得连续 ≥3 镜（2026-09-22 补：这条规则写了两处、**从来没有门禁**）----
    # 文档原文（narrative-moves.md §2）：「闭合 10 个，**同一个 `move` 不得连续 ≥3 镜**」，§4 把
    # 它列进 G-14 —— 但本脚本此前只查了"每镜的 move 是不是 10 个名字之一"，**没有任何连续镜检查**。
    # 也就是说这条规则从落地起就没被执行过：写 3 镜连续 `引入` 的片子照旧 PASS。
    #
    # 级别 = P0，依据是这条规则的出处（`呈现效果调研.md` §5.7）：「同一种 `move` 不得连续 ≥3 镜
    # **（与骨架重复检查同级）**」—— 而相邻同骨架在 `validate-composition.py` 是 **P0（P0-1）**；
    # narrative-moves.md §2 用的也是"**不得**"（禁令），不是"建议"。
    # ⚠️ §4 那一行的级别格原先写的是 "P0 / P1"，读起来像"连续这半条算 P1"——两种读法都说得通，
    #    这里按出处取 P0，并**把口径写回文档**（narrative-moves.md §2/§4 已改成显式 P0），不再靠猜。
    #
    # 口径：按 shots.json 的镜序逐镜比较（= 成片顺序：resolve-shots 要求 from 连续，两者必然一致），
    #      同一 move 的**极大连续段** ≥3 镜即报一条，报出**哪几镜、连续了几个、什么 move**。
    #      缺 move / 不在闭集的镜**打断计数**：它自己已经另报 P0，既不在这里重复刷屏，
    #      也不许把它两侧的段接成一条假的"连续"——第一版写成 `continue`（跳过但不打断），
    #      于是 `引入,引入,缺move,引入` 被报成"S1→S2→S4 连续 3 镜"，那是一句用户照着改不了的假话
    #      （负向夹具 AE 抓到的）。
    runs: list[tuple[str, list[str]]] = []
    run_move: str | None = None
    run_ids: list[str] = []
    for s in shots:
        mv = str(s.get("move") or "").strip()
        if mv not in MOVES:
            if run_move is not None:
                runs.append((run_move, run_ids))
            run_move, run_ids = None, []
            continue
        if mv != run_move:
            if run_move is not None:
                runs.append((run_move, run_ids))
            run_move, run_ids = mv, []
        run_ids.append(s.get("id", "?"))
    if run_move is not None:
        runs.append((run_move, run_ids))
    for mv, ids in runs:
        if len(ids) >= MOVE_RUN_LIMIT:
            p0.append({"id": f"{ids[0]}–{ids[-1]}", "issue": (
                f"同一 move 连续 {len(ids)} 镜：{'→'.join(ids)} 都是 «{mv}»（上限 {MOVE_RUN_LIMIT - 1} 镜，"
                f"判据 = 文档的「同一个 move 不得连续 ≥{MOVE_RUN_LIMIT} 镜」）：连续同动作会让观众觉得"
                f"这几镜在干同一件事，请换一个叙事动作或把其中两镜合并")})

    if kinds and len(kinds) < MOVE_MIN_KINDS:
        p1.append({"id": "-", "issue": f"全片只用到 {len(kinds)} 种叙事动作（{sorted(kinds)}），建议 ≥{MOVE_MIN_KINDS} 种"})
    return p0, p1


# ------------------------------------------------- G-15 `evidence` 是不是真用在源码里（v2 简版）
#
# ⚠️ 这条判据此前**名存实亡**：文档（`narrative-moves.md` §2 / `presentation-gate.md` §G-15）把它写成
# 必填且"静态元素不算证据"，而本脚本读 `evidence` 的唯一一处是 `if not ev:`（**只查字段非空**）——
# 名字写成源码里根本不存在的，门禁一声不响（负向夹具 AF 钉的就是这个）。
#
# v2（2026-09-22 按实测简化，替掉上一版 465 行的手写 JSX 结构解析）**只查一件事**：
#
#   `evidence` 的名字必须**作为 JSX 用法**（`<名字 …>` / `<名字/>`）出现在该工程的**场景源码**里。
#
# 口径（三句话说完，没有隐藏的第四句）：
#   · 扫描前用 `noncode()` 把注释与字符串抹成空格 → **注释里写到的名字不算"用到"**
#     （真实工程 overview-film 的 S2 就是这么烂掉的：`MetricGrid` 被换成手绘行 + `Chart`，
#      只在注释里留了一句"这里本来用 MetricGrid"；"文件里搜得到名字"那种判法会**假通过**）。
#     同理，import 行与字符串里的代码样例也都不算 —— 只有 JSX 用法算。
#   · 场景源码 = `src/**` 里名字带 `scene` 的 .tsx（与 validate-frame-props.py 的 SCENE_HINT 同一口径）；
#     一个都没有时退到 `src/**/*.tsx`；连 .tsx 都没有就报一条 P1 说明**这条判据没生效**
#     （让"没报"与"没跑"可区分，与其它门禁的覆盖率日志同一用意）。
#   · 名字后面必须紧跟空白 / `/` / `>`（`(?![A-Za-z0-9_$])`），免得 `Widget2` 被 `Widget` 蒙混过去。
#
# **不做**的（口径已同步写回 `narrative-moves.md` §2 与 `presentation-gate.md` §G-15，别高估它）：
#   · 不做**本镜作用域**：名字只要在该工程的场景源码里被 JSX 用到就算过 ——
#     **一个名字在本镜没用到、但在别的镜用了，会漏**。这正是"降复杂度"买来的代价，
#     负向夹具 AG 把这个口径**钉住**（它现在必须 rc=0，谁哪天加回本镜作用域，这条夹具会先失败）。
#   · 不做**帧驱动判定**（"那个元素到底动不动"）：那要解析 JSX 结构 + 维护一张帧驱动白名单，
#     而它的误报面已经实测到了 —— 帧经 `ctx` 这类不透明参数传进组件的写法会被判成静态，
#     而动作表「推进」推荐的 `PhaseRail` 恰好就是这种写法。判成 P0 等于"照文档写、门禁拦你"。
#   · 不做**降级**：v1 在"切不出本镜"时要降级并自报一条 P1 —— 现在没有"本镜"这一层，无级可降。
#
# 代价与取舍（写清楚，免得下一个人以为它比实际更强）：
#   这条判据现在拦得住「名字写错 / 只出现在注释里 / 只出现在 import 行或字符串里」，
#   **拦不住**「指向一个在本镜里从头到尾不动的静态卡片」（只要那个名字在别处被 JSX 用到过）。
#   要把那半边找回来，得把本镜作用域 + 帧驱动白名单一起加回来 —— 就是被砍掉的那 465 行。
#   本仓库的取舍：**宁可少报，也不要一堆假报告 + 一条没人愿意维护的判据**。

_EVIDENCE_NAME = "(?![A-Za-z0-9_$])"


def _evidence_used(code: str, name: str) -> bool:
    """`name` 有没有**作为 JSX 用法**出现（`<Name …>` / `<Name/>`）。注释与字符串已由 noncode() 抹掉。"""
    return re.search(r"<" + re.escape(name) + _EVIDENCE_NAME, code) is not None


def _scene_files(project: Path) -> list[Path]:
    """名字里带 `scene` 的 .tsx（与 validate-frame-props.py 的 SCENE_HINT 同一口径）。"""
    src = project / "src"
    if not src.is_dir():
        return []
    return [p for p in sorted(src.rglob("*.tsx")) if "scene" in p.name.lower()]


def check_evidence(project: Path) -> tuple[list, list]:
    p0, p1 = [], []
    src = project / "src"
    if not src.is_dir():
        return p0, p1                            # 没源码：与 check_readability 同口径，静默跳过
    doc = json.loads((project / "manifests" / "shots.json").read_text(encoding="utf-8"))
    shots = doc["shots"] if isinstance(doc, dict) and "shots" in doc else doc

    files = _scene_files(project) or sorted(src.rglob("*.tsx"))
    if not files:
        p1.append({"id": "-", "issue": (
            f"G-15（`evidence` 真的用在源码里）**没生效**：{project.name}/src 下找不到场景源码"
            "（名字里带 scene 的 .tsx，退一步看任一 .tsx）——这一条只能查「名字有没有被当成 JSX 用」，"
            "没有源码就无从判起")})
        return p0, p1
    where = "、".join(p.name for p in files)
    code = "\n".join(noncode(p.read_text(encoding="utf-8")) for p in files)

    for s in shots:
        sid = s.get("id", "?")
        ev = str(s.get("evidence") or "").strip()
        if not ev:
            continue                             # 缺字段已由 check_narrative 报过，不重复刷屏
        if _evidence_used(code, ev):
            continue
        p0.append({"id": sid, "issue": (
            f"evidence=«{ev}» 在场景源码（{where}）里**找不到这个用法**：名字要么写错了、"
            f"要么从来没被当成 JSX 用渲染出来（只写在注释 / 字符串 / import 行里都不算「用到」）。"
            f"G-15 要求 `evidence` 指向真的会变的那件东西，指向一个不存在的用法 = 这条声明无法被验证"
            f"（判据与**已知边界**见 narrative-moves.md §2）")})
    return p0, p1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    project = Path(args.project).resolve()
    if not (project / "manifests").is_dir():
        print(f"项目目录里没有 manifests/：{project}", file=sys.stderr)
        return 2

    p0, p1 = [], []
    try:
        a, b = check_timeline(project)
        p0 += a
        p1 += b
    except FileNotFoundError as e:
        print(f"缺少必需文件：{e}", file=sys.stderr)
        return 2
    a, b = check_readability(project)
    p0 += a
    p1 += b
    a, b = check_narrative(project)
    p0 += a
    p1 += b
    a, b = check_evidence(project)      # G-15：`evidence` 被当成 JSX 用出现在场景源码里（v2 简版口径）
    p0 += a
    p1 += b

    if args.json:
        print(json.dumps({"p0": p0, "p1": p1}, ensure_ascii=False, indent=2))
    else:
        print("validate-presentation · 呈现效果门禁（T1 纯算术）")
        for item in p0:
            print(f"  P0 {item['id']}: {item['issue']}")
        for item in p1:
            print(f"  P1 {item['id']}: {item['issue']}")
        print(f"结论：P0={len(p0)} P1={len(p1)} → {'PASS' if not p0 else 'FAIL'}")
    return 1 if p0 else 0


if __name__ == "__main__":
    sys.exit(main())
