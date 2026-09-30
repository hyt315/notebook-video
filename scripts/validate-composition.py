#!/usr/bin/env python3
"""validate-composition.py · 构图与活性门禁（P0 阻断渲染 / P1 仅警告）

这是整套体系里**唯一能把"审美"变成门禁**的部分，也是让改进不随时间退化的保障。
没有它，v2.8 的强制条款再多也会像今天一样全部空转——规范强制使用活性组件、
实现引用数为 0，9 个校验脚本没有一条能发现。

检查项（判据与档位见 references/composition-gate.md）：

  P0-1  骨架重复度        相邻场景不得同骨架；全片 ≥3 种；未知骨架名 → fail
  P0-2  活性组件覆盖率     每个讲解场景 ≥1 个活性组件；**且每个名字必须能在场景文件里找到**
  P0-3  镜头意图多样性     全片 ≥3 种 intent（不含 still）
  P0-4  密度硬条款         3–5 个功能分区；下 1/4 填满（**不再被 explanation:false 绕过**）
  P0-5  介质多样性         全片 ≥3 种不同视觉介质，且取值必须在闭合集合内
  P0-6  枚举闭合           转场 / 入场 / 介质 / 骨架 / 意图 全是闭合集合，写错名字即 fail
  P1-7  单镜过长           单镜 > 300 帧（10s）提示锯开（基准 4–6s、最长 ≤9s）
  P1-8  骨架指纹重复       同一 (骨架,意图,转场,入场) 组合每出现一次就提示
  P1-9  镜长分布           最长/最短 < 2 倍、或 >80% 镜头集中在同一档 → 读起来是节拍器
  P1-10 主角尺寸           hero 必须声明，且 size 是"主体短边设计像素"（图形 ≥255 / 大字 ≥144）
  P1-11 转场 / 入场多样性  ≥2 种 / ≥3 种
  P1-12 状态变化间隔       汇总报告（带帧区间与所涉台词），不再每镜刷 1 条

用法：
    python scripts/validate-composition.py PROJECT_DIR [--strict] [--json]
退出码：0 通过（可含 P1）/ 1 存在 P0（或 --strict 下存在 P1）/ 2 用法或文件错误
零第三方依赖，Python 3.10+ 标准库。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# 闭合集合：写错名字必须被拦下（v2.11 前这些字段是自由字符串，
# 实测把 media 写成 ["FAKE_MEDIUM_A",...]、live 写成 ["NO_SUCH_COMPONENT"] 也能 P0=0 通过）
SKELETONS = {"Stage", "Corridor", "Split", "Zoom"}
INTENTS = {"establish", "push-in", "pull-back", "pan-follow", "reveal", "micro-orbit", "still"}
TRANSITIONS = {"cut", "handoff", "reveal"}   # v3.0.1 收缩：whip / paper-turn 已删除
ENTRIES = {"rise", "slide", "fade", "zoom"}
MEDIA_KINDS = {"chart", "console", "code", "graphic", "text", "metric"}

MIN_SKELETONS = 3
MIN_MEDIA = 3
MIN_INTENTS = 3
MIN_TRANSITIONS = 2
MIN_ENTRIES = 3
ZONE_RANGE = (3, 5)
MAX_EXPLANATION_FALSE = 1     # 一部片最多 1 镜可以不走"讲解场景"的活性要求（章节卡）
MAX_SHOT_FRAMES = 300         # 单镜上限 10s
MIN_LENGTH_RATIO = 2.0        # 最长/最短 倍数下限（测出来是节拍器）
MAX_BAND_SHARE = 0.8          # 同一时长档最多占 80%
MAX_BEAT_GAP = 120            # 文档的慢章节上限（3–4s）；超过它才算越界
SLOW_GAP = 90                 # 汇总时把 >3s 的间隔也列出来（供评审，不判缺陷）
HERO_MIN_GRAPHIC = 255        # a2e 720p 的 170px × 1.5（设计空间 1920×1080）
HERO_MIN_TEXT = 144           # a2e 720p 的 96px × 1.5

BANDS = ((0, 60, "≤2s"), (61, 120, "2–4s"), (121, 240, "4–8s"), (241, 10 ** 9, ">8s"))


def load(project: Path) -> dict:
    shots_path = project / "manifests" / "shots.resolved.json"
    if not shots_path.exists():
        raise SystemExit(f"缺少 {shots_path}；先运行 python scripts/resolve-shots.py PROJECT_DIR")
    return json.loads(shots_path.read_text(encoding="utf-8"))


def scene_source(project: Path) -> str:
    """场景文件全文：用来确认 live 里的名字真的被引用过（而不是编出来的）。

    ⚠️ 必须**递归**扫（与同文件 import_integrity 的 rglob 对齐）：旧版写成
    `src.glob("*.tsx")` 只扫一层，场景文件放在子目录（src/scenes/ 等）时整段读不到，
    于是所有"需要场景源码"的 P0 判据因 `if scene_text` 为空而**静默跳过**——
    门在名义上存在、实际从未生效。场景源码读不到的镜由 check() 里的覆盖率
    自述补报 P0（"测量没跑成"不许混进"没报"）。
    """
    src = project / "src"
    text = ""
    if src.is_dir():
        for p in sorted(src.rglob("*.tsx")):
            text += p.read_text(encoding="utf-8", errors="replace")
    return text


def import_integrity(project: Path) -> tuple[list[dict], str]:
    """**import 的每个名字必须真的存在于目标模块的导出里**（P0）。

    为什么单列一条：清掉 23 件组件之后，`src/index.tsx` 还留着
    `import {Mascot, RollDigit, WaveText, CodeBlock, BrowserChrome, Connector, CountUp, ProgressBar} from './toolkit'`
    这样的语句——11 个名字指向已删除的导出。打包器对"缺失的具名导出"通常只告警不报错，
    于是在运行时变成静默的 `undefined`：**这正是本技能最怕的那类失败**（没报错，但坏了）。

    覆盖范围（第二轮复核实测后补齐——此前只扫 `src/*.tsx` 一层、正则只认 `'./名字'`）：
      · **递归**扫 `src/**`：组件层内部文件互引同样会静默失败；
      · 认得 `./x` / `../x` / 目录桶文件 `./components`（= `components/index.ts`）；
      · 跟随 `export * from './y'`；桶文件上的 `export {A} from './y'` 只在该名字
        真在 y 里时才认（否则坏名字会被桶文件"洗白"）；
      · **别名再导出**（第三轮复核指出后修）：`export {Accordion as MyAccordion} from './ui'` 里
        对外名是 `MyAccordion`、上游名是 `Accordion`——**比对用源名、登记用别名**；
        `export {default as Widget}` 的 `default` 追不到名字，归"核实不了"（放行），**不许判"不存在"**；
      · **只扫代码位置**：注释与**字符串字面量内部**先被抹成空格（长度/行号不变），
        所以模板字符串里的代码样例（接触表/测试页里那种 `const CODE = "import X from './y';"`）
        既不会被当成真 import，也不会给本检查贡献"幽灵导出"；
      · **穷举不了的（指向 npm 包、有环、超过 3 层）一律不报**，只记账——
        "会哭狼的检查等于没有检查"。
    """
    problems: list[dict] = []
    src = project / "src"
    if not src.is_dir():
        return problems, ""
    root = src.resolve()
    files = sorted(p for p in src.rglob("*") if p.is_file() and p.suffix in (".ts", ".tsx"))
    key_of = lambda p: p.relative_to(root).with_suffix("").as_posix()
    keys = {key_of(p) for p in files}
    path_of = {key_of(p): p for p in files}
    raw_body = {k: p.read_text(encoding="utf-8", errors="replace") for k, p in path_of.items()}

    # ⚠️ 必须先剥掉"不是代码"的部分再扫：用法示例常常写成
    # `// 用法：import {FitCard, Typewriter, ...} from './fxkit';`
    # 第一版没剥，于是 `...` 被当成一个名字报成 P0 —— 会哭狼的检查等于没有检查。
    def code_only(text: str) -> str:
        """把注释内部与**字符串字面量内部**换成空格，长度与行号一字不动。

        字符串也要抹，是因为**字符串里放代码样例**是本仓库的常规写法
        （接触表/测试页里的 `const CODE = `import {...} from './x';``）。第三轮复核指出：
        那种样例既会被当成真 import 扫（假 P0），也会给本检查贡献"幽灵导出"。
        引号只在**值位置**才算开字符串（前一个代码位置的非空白字符属于 `=([{,:;?|&!+*-<>~^` 或行首），
        免得 JSX 文本里的撇号（`don't`）毒化整行；`'…'`/`"…"` 不跨行，行尾未闭合即收尾。
        （与 `validate-presentation.py` 的同名函数是同一份实现，两个脚本各自独立、无共享模块。）
        """
        out = list(text)
        VALUE_POS = "=([{,:;?|&!+*-<>~^"
        i, n, quote, prev = 0, len(text), "", ""
        def blank(lo: int, hi: int) -> None:
            for k in range(lo, hi):
                if out[k] != "\n":
                    out[k] = " "
        while i < n:
            ch = text[i]
            if quote:
                blank(i, i + 1)
                if ch == "\\" and i + 1 < n:
                    blank(i + 1, i + 2)
                    i += 2
                    continue
                if ch == quote:
                    quote = ""
                elif ch == "\n" and quote != "`":
                    quote = ""
                i += 1
                continue
            if ch in "'\"`" and (prev == "" or prev in VALUE_POS):
                quote = ch
                blank(i, i + 1)
            elif text.startswith("//", i):
                j = text.find("\n", i)
                blank(i, n if j < 0 else j)
                i = n if j < 0 else j
                continue
            elif text.startswith("/*", i):
                j = text.find("*/", i + 2)
                blank(i, n if j < 0 else j + 2)
                i = n if j < 0 else j + 2
                continue
            elif not ch.isspace():
                prev = ch
            i += 1
        return "".join(out)

    def resolve_spec(spec: str, importer: Path) -> str | None:
        """相对路径 → 模块键；`./components` 落到 `components/index`。包名一律 None。"""
        if not spec.startswith("."):
            return None
        try:
            rel = (importer.parent / spec).resolve().relative_to(root).as_posix()
        except ValueError:
            return None
        for cand in (rel, rel + "/index"):
            if cand in keys:
                return cand
        return None

    def exports_of(key: str, depth: int = 0, seen: frozenset = frozenset()) -> tuple[set[str], set[str], bool]:
        """(确定存在的名字, 存在但核实不了的名字, 是否 open)。

        open=True 表示这个模块 `export * from '<包>'` —— 可能有任意名字，导入方一律豁免。
        "核实不了"与"不存在"必须分开：`export {X} from '<包名>'` 这类**库再导出**（v3.1.1 前的模板里
        真有过两条：`@remotion/motion-blur` 的 CameraMotionBlur / Trail；后来按「零引用」判据删了）
        里的名字**是真的**，把它当成不存在会让整条链上全是假 P0（第一版本版就这么错了）。
        """
        if depth > 3 or key in seen:
            return set(), set(), True
        body = code_only(raw_body[key])
        names = set(re.findall(r"export\s+(?:declare\s+)?(?:const|function|class|type|interface|let|var|enum)\s+(\w+)", body))
        uncertain: set[str] = set()
        # `export {A, B as C}`，也可能带 from（多行花括号：`[^}]*` 本来就跨行）
        # ⚠️ 认领的必须是**对外名**（别名），比对上游用的是**源名**：
        # `export {Accordion as MyAccordion} from './ui'` 里，上游有的是 `Accordion`，
        # 本模块对外给的是 `MyAccordion`。第一版拿别名去上游找 → 合法写法被判"导出不存在"
        # （第三轮复核抓到的潜在假阳性；技能文档正教人"新组件登记进 components/index.ts"，
        #  改名再导出是自然的下一步，所以必须现在改）。
        for m in re.finditer(r"export\s+(?:type\s+)?\{([^}]*)\}\s*(?:from\s*'([^']*)')?", body):
            pairs: list[tuple[str, str]] = []
            for part in m.group(1).split(","):
                part = part.strip()
                if not part:
                    continue
                bits = part.split(" as ")
                pairs.append((bits[0].strip(), (bits[-1] if len(bits) > 1 else bits[0]).strip()))
            if not m.group(2):
                names |= {alias for _src, alias in pairs if alias}
                continue
            sub = resolve_spec(m.group(2), path_of[key])
            if sub is None:
                uncertain |= {alias for _src, alias in pairs if alias}   # 从 npm 包再导出：名字是真的，只是我们看不见
                continue
            sub_names, sub_uncertain, sub_open = exports_of(sub, depth + 1, seen | {key})
            for src_name, alias in pairs:
                if not alias:
                    continue
                if src_name == "default":
                    # `export {default as Widget} from './bar'`：default 追不到名字 → 归"核实不了"，
                    # 不能判"不存在"（判了就是假 P0）。
                    uncertain.add(alias)
                elif src_name in sub_names or src_name in sub_uncertain or sub_open:
                    names.add(alias)
                # 源名在上游不存在 = 坏再导出：这里**不认领**它，让真正的导入点去报
        open_flag = False
        for m in re.finditer(r"export\s+\*\s+from\s*'([^']*)'", body):
            sub = resolve_spec(m.group(1), path_of[key])
            if sub is None:
                open_flag = True           # `export * from 'pkg'`：无法穷举
                continue
            sub_names, sub_uncertain, sub_open = exports_of(sub, depth + 1, seen | {key})
            names |= sub_names
            uncertain |= sub_uncertain
            open_flag = open_flag or sub_open
        return names, uncertain, open_flag

    checked = skipped = 0
    for key in sorted(keys):
        f = path_of[key]
        body = code_only(raw_body[key])
        for m in re.finditer(r"import\s*\{([^}]*)\}\s*from\s*'([^']*)'", body, re.S):
            spec = m.group(2)
            target = resolve_spec(spec, f)
            if target is None:
                continue              # 包 / 别名 / 路径对不上：不属本检查辖区
            avail, uncertain, open_flag = exports_of(target)
            if open_flag:
                skipped += 1          # 目标有 export * 无法穷举 → 宁可不报
                continue
            checked += 1
            for raw in m.group(1).split(","):
                token = raw.strip()
                if not token or token.startswith("type "):
                    continue
                name = token.split(" as ")[0].strip()
                if not re.fullmatch(r"[A-Za-z_$][\w$]*", name):
                    continue   # `...`、空串等不是合法标识符，直接跳过
                if name not in avail and name not in uncertain:
                    where = f"{target}.tsx" if (root / f"{target}.tsx").exists() else f"{target}.ts"
                    problems.append({"id": f"src/{key_of(f)}{f.suffix}",
                                     "issue": f"import 里引用了已不存在的导出 {name}（来自 '{spec}' → src/{where}）——打包器只告警，运行时是 undefined"})
    note = f"import_integrity：递归扫 {len(files)} 个 src 文件 / 核对 {checked} 条相对 import / {skipped} 条因 export * 无法穷举而豁免"
    return problems, note


def _shot_body(scene_text: str, sid: str) -> str:
    """切出某一镜的组件函数体（从本镜声明到下一条镜声明），并去掉注释 ——
    注释里写到的 `b[3]` 不算"用过一次"。

    识别的声明形态（批7 F1：此前只认 `const S…: React.FC<`，实测工程写
    `import {FC} from 'react'` + `export const S1: FC<…>` 或 `export function S1(...)`
    时 8/8 镜全片误报 P0"场景源码不可读"）：
      · `const S1Xxx: React.FC<…>` / `const S1Xxx: FC<…>`（`export` 前缀均可）
      · `function S1Xxx(...)` / `export function S1Xxx(...)`
      · `const S1Xxx = (props…): JSX.Element …`（箭头函数带返回类型标注）
    完全找不到函数体的语义不变：仍由 BF1 的"判据无法执行"P0 兜底。
    """
    marks = []
    for m in re.finditer(
        r"const (S\d+)[A-Za-z0-9_]*\s*:\s*(?:React\.)?FC<"
        r"|(?<![\w.$])function (S\d+)[A-Za-z0-9_]*\s*\("
        r"|const (S\d+)[A-Za-z0-9_]*\s*=\s*\([^)]*\)\s*:\s*JSX\.Element",
        scene_text,
    ):
        name = next(g for g in m.groups() if g)
        marks.append((name, m.start()))
    for i, (name, start) in enumerate(marks):
        if name != sid:
            continue
        end = marks[i + 1][1] if i + 1 < len(marks) else len(scene_text)
        body = scene_text[start:end]
        body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
        body = re.sub(r"//[^\n]*", "", body)
        return body
    return ""


def check(data: dict, scene_text: str = "") -> tuple[list[dict], list[dict], list[str]]:
    p0: list[dict] = []
    p1: list[dict] = []
    notes: list[str] = []
    shots = data.get("shots", [])
    if not shots:
        p0.append({"id": "-", "issue": "shots.json 没有 shots"})
        return p0, p1, notes

    # ---- 覆盖率自述：场景源码存在时，每一镜都必须找得到自己的场景函数体 ----
    # 病因（2026-09 修复）：scene_source 此前只扫 src 一层，子目录里的场景文件读不到，
    # 下面所有 `if scene_text` 判据（live 名字可解析 / 转场声明是否兑现 / beats 下标越界）
    # 就整段静默跳过，rc 照样 0 —— "没报"和"没跑"必须可区分。
    # 口径：工程里一份 .tsx 都没有时维持原行为（负向抽查的最小夹具只有分镜表，无从比对）；
    #       只要有场景源码，某镜在源码里切不出函数体就是**测量没跑成**，记 P0 点名。
    if scene_text:
        for s in shots:
            sid = s.get("id", "?")
            if not _shot_body(scene_text, sid):
                p0.append({"id": sid, "issue": (
                    "场景源码不可读，判据无法执行：在 src/**/*.tsx 里找不到本镜的场景函数"
                    "（`const S…: React.FC<` / `: FC<` / `function S1(…)` / "
                    "`const S1 = (…): JSX.Element` 诸形态之一）——凡是需要场景源码的判据（live 名字是否真被引用、"
                    "转场声明是否兑现、beats 下标越界）对本镜都没有跑成，不许当成已通过")})

    # ---- P0-6 枚举闭合（先做，后面的多样性统计才有意义）----
    unknown_intents = {s.get("cameraIntent", "still") for s in shots} - INTENTS
    if unknown_intents:
        p0.append({"id": "-", "issue": f"未知镜头意图 {sorted(unknown_intents)}；只能是 {sorted(INTENTS)}"})
    bad_tr = {s.get("transition", "cut") for s in shots} - TRANSITIONS
    if bad_tr:
        p0.append({"id": "-", "issue": f"未知转场 {sorted(bad_tr)}；只能是 {sorted(TRANSITIONS)}"})
    bad_en = {s.get("entry", "rise") for s in shots} - ENTRIES
    if bad_en:
        p0.append({"id": "-", "issue": f"未知入场方式 {sorted(bad_en)}；只能是 {sorted(ENTRIES)}"})
    bad_media = {m for s in shots for m in (s.get("media") or [])} - MEDIA_KINDS
    if bad_media:
        p0.append({"id": "-", "issue": f"未知介质 {sorted(bad_media)}；只能是 {sorted(MEDIA_KINDS)}"})

    # ---- P0 声明即承诺：声明的转场必须真的被实现 ----
    # 背景：两条成片都出现过"分镜表声明 handoff、代码里从未实现"，以及 SWE-2 的 S1
    # "表写 cut、代码写 reveal"。声明不兑现 = 分镜表在说谎，必须拦下。
    def shot_block(sid: str) -> str:
        # 收到本镜 </Shot> 为止：旧版窗口 400 字符，实测窗口长 413，会越过边界吞掉下一镜
        m = re.search(r"<Shot\b[^>]*\bid=\"%s\"[\s\S]*?</Shot>" % re.escape(sid), scene_text)
        return m.group(0) if m else ""

    # 只认布尔属性 reveal：允许 `reveal`、`reveal>`、`reveal >`、`reveal />`、换行后接 `>`；
    # 排除 revealAt / revealSpeed 这类同前缀属性（负向断言 `(?![A-Za-z0-9_$])`）。
    def has_reveal(blk: str) -> bool:
        return re.search(r'\breveal(?![A-Za-z0-9_$])', blk) is not None
    for i, s in enumerate(shots):
        tr = s.get("transition", "cut")
        # 场景源码缺失时（负向抽查的最小夹具只有分镜表）无从比对实现——跳过，只查分镜表内部自洽。
        # 与上面 live 名字的 `if scene_text` 同一口径：没源码不等于声明没兑现。
        blk = shot_block(s.get("id", "?")) if scene_text else ""
        if scene_text and tr == "reveal" and not has_reveal(blk):
            p0.append({"id": s.get("id", "?"), "issue": "声明 transition=reveal，但场景里该镜的 <Shot> 没有 reveal（声明没兑现）"})
        if scene_text and tr == "cut" and has_reveal(blk):
            p0.append({"id": s.get("id", "?"), "issue": "声明 transition=cut，但场景里写了 reveal（表与实现不一致）"})
        if tr == "handoff":
            carrier = (s.get("carrier") or "").strip()
            nxt = shots[i + 1] if i + 1 < len(shots) else None
            if not carrier:
                p0.append({"id": s.get("id", "?"), "issue": "声明 transition=handoff 但没有 carrier；引擎的镜间叠帧是全局生效的，没有 carrier 的 handoff 与 cut 没有区别 → 要么补 carrier，要么改成 cut"})
            elif not nxt or (nxt.get("carrier") or "").strip() != carrier:
                p0.append({"id": s.get("id", "?"), "issue": f"carrier=\"{carrier}\" 但下一镜没有声明同一个 carrier（交接对象跨镜不连续）"})

    # ---- P0-1 骨架重复度 ----
    seq = [(s.get("id", "?"), s.get("skeleton", "?")) for s in shots]
    for (a_id, a), (b_id, b) in zip(seq, seq[1:]):
        if a == b:
            p0.append({"id": b_id, "issue": f"与上一镜同骨架（{a}）；相邻场景必须不同骨架"})
    kinds = {k for _, k in seq}
    unknown = kinds - SKELETONS
    if unknown:
        p0.append({"id": "-", "issue": f"未知骨架 {sorted(unknown)}；只能是 {sorted(SKELETONS)}"})
    if len(kinds & SKELETONS) < MIN_SKELETONS:
        p0.append({"id": "-", "issue": f"全片仅 {len(kinds & SKELETONS)} 种骨架，要求 ≥{MIN_SKELETONS} 种"})

    # ---- P0-2 活性组件覆盖率（含"名字可解析"）+ P0-4 密度 ----
    # explanation:false 只能豁免"活性组件"这一条，且全片最多 1 镜；
    # zones / bottomFill 与 explanation 无关，永远校验（旧版一个 false 就能把整块跳过）。
    non_expl = [s.get("id", "?") for s in shots if s.get("explanation", True) is False]
    if len(non_expl) > MAX_EXPLANATION_FALSE:
        p0.append({"id": "-", "issue": f"{len(non_expl)} 镜标了 explanation:false（{non_expl}），最多允许 {MAX_EXPLANATION_FALSE} 镜"})
    live_names: set[str] = set()
    for s in shots:
        sid = s.get("id", "?")
        if s.get("explanation", True) is not False:
            live = [x for x in (s.get("live") or []) if x]
            if not live:
                p0.append({"id": sid, "issue": "讲解场景没有任何活性组件（纯卡片堆）；禁止"})
            for name in live:
                live_names.add(str(name))
                if scene_text and not re.search(r"\b" + re.escape(str(name)) + r"\b", scene_text):
                    p0.append({"id": sid, "issue": f"活性组件 “{name}” 在场景文件里找不到（没 import 也没渲染）；写名字前先在接触表里看见它"})
        zones = s.get("zones")
        if zones is None:
            p0.append({"id": sid, "issue": "缺少 zones（本镜功能分区数）"})
        elif not isinstance(zones, int) or not (ZONE_RANGE[0] <= zones <= ZONE_RANGE[1]):
            p0.append({"id": sid, "issue": f"功能分区 {zones!r}，契约要求 {ZONE_RANGE[0]}–{ZONE_RANGE[1]} 个整数"})
        # 逐镜取函数体，再去注释后扫描（两件都是实测踩出来的）：
        #   · 整份文件一起扫会把"某镜用了 b[9]"算到每一镜头上（夹具只改 S19 却报了 21 条）；
        #   · 不去注释会把解释性注释里写到的 `b[3]` 当成真代码（实测第一次跑误报两镜）。
        code_only = "" if not scene_text else _shot_body(scene_text, sid)
        if code_only:
            # ---- beats 下标越界（2026-09-21 加。**这条本来能救两次事故**）----
            # 场景里写 `SHOTS.Sx.beats[k]` 取节拍，而 beats 的长度由分镜的 cue 区间决定。
            # 一旦镜里只有 3 拍而场景写了 `b[3]`：
            #   · 传给 `interpolate`/`ClipReveal` 的 `from` 就是 undefined → 抛
            #     "inputRange must contain only numbers" → **整帧渲染失败**（S17 实测）；
            #   · 传给某个比较（`f >= at`）就**永远为假** → 那件东西**从头到尾不出现**，
            #     不报错、不警告（S15 的第三条聊天消息实测从未出现）。
            # 两种都不该靠人眼发现：这里用静态扫描把每个 `b[k]` 的 k 与真实拍数比一遍。
            #
            # ⚠️ 2026-09-21 收窄盲区：**同一个错误有两种写法，只认一种等于没拦**。
            # 原来只扫本地别名 `b[k]`（`const b = SHOTS.Sx.beats` 之后再取下标）——
            # 写成全路径 `SHOTS.S19.beats[9]` 就整条漏掉。现在两种都认：
            #   ① 别名：`b[k]`  → 与本镜拍数比；
            #   ② 全路径：`SHOTS.<id>.beats[k]` → 与被引用的那一镜的拍数比（镜号不一定是本镜）；
            #      引用了不存在的镜号也一并报（那是另一种真错，同样只会静默拿到 undefined）。
            shots_list = data.get("shots") if isinstance(data.get("shots"), list) else data
            by_id = {x.get("id"): x for x in shots_list if isinstance(x, dict)}
            rec = by_id.get(sid)
            beats_len = len((rec or {}).get("beats") or [])
            too_far: dict[str, str] = {}   # 去重键 → 报告文本，同一处只报一次

            def mark(expr: str, k: int, n: int, subject: str) -> None:
                if n and k >= n and expr not in too_far:
                    too_far[expr] = (f"场景里用了 {expr}，但{subject}只有 {n} 拍（下标 0–{n - 1}）："
                                     f"取到 undefined —— 要么抛错、要么那件东西永远不出现")

            if beats_len:
                for mm in re.finditer(r"\bb\[(\d+)\]", code_only):
                    mark(f"b[{mm.group(1)}]", int(mm.group(1)), beats_len, "本镜")
            for mm in re.finditer(r"\bSHOTS\.(\w+)\.beats\[(\d+)\]", code_only):
                ref = mm.group(1)
                if ref not in by_id:
                    p0.append({
                        "id": sid,
                        "issue": f"场景里引用了 SHOTS.{ref}.beats，但分镜表里没有 {ref} 这一镜："
                                 f"取到 undefined —— 要么抛错、要么那件东西永远不出现",
                    })
                    continue
                ref_idx = len((by_id.get(ref) or {}).get("beats") or [])
                mark(f"SHOTS.{ref}.beats[{mm.group(2)}]", int(mm.group(2)), ref_idx, f"{ref} 这一镜")
            for _expr in sorted(too_far):
                p0.append({"id": sid, "issue": too_far[_expr]})
        # 2026-09-21 降级（**这道门原来永远不会失败**）：它校验 `bottomFill == True`，
        # 而这个字段是生成分镜表的脚本**自己写死的常量**（make-shots.py 每一镜都写 True），
        # resolve-shots 再原样透传 —— 生成器写 True、门禁要求 True，结构上不可能报错。
        # 实测成片里 17/21 镜的下 1/4 是空的，它一次都没响。
        # 现在只查"字段在不在"（缺字段是真配置错误），真正的判据交给渲染期的 FillGate
        # （实测信息元素的最低边 vs y=876，量的是画面而不是声明）。
        if "bottomFill" not in s:
            p0.append({"id": sid, "issue": "缺 bottomFill 字段（下 1/4 密度的声明位；实测判据见渲染期 FillGate）"})

    # ---- P0-3 镜头意图多样性 ----
    intents = {s.get("cameraIntent", "still") for s in shots}
    if len(intents - {"still"}) < MIN_INTENTS:
        p0.append({"id": "-", "issue": f"全片仅 {len(intents - {'still'})} 种镜头意图，要求 ≥{MIN_INTENTS} 种"})

    # ---- P0-5 介质多样性 ----
    media: set[str] = set()
    for s in shots:
        for m in s.get("media") or []:
            media.add(m)
    if len(media) < MIN_MEDIA:
        p0.append({"id": "-", "issue": f"全片仅 {len(media)} 种视觉介质 {sorted(media)}，要求 ≥{MIN_MEDIA} 种"})

    # ---- P1 单镜过长（工艺项，不阻断；结构由作者决定）----
    for s in shots:
        dur = int(s.get("duration") or 0)
        if dur > MAX_SHOT_FRAMES:
            # 注意：f-string 里不要复用同种引号（PEP 701 只在 Python 3.12+ 合法，本脚本声明支持 3.10+）
            p1.append({"id": s.get("id", "?"), "issue": "单镜 %d 帧（%.1fs）超过 %d 帧参考上限；基准是单镜 4–6s、最长 ≤9s" % (dur, dur / 30, MAX_SHOT_FRAMES)})

    # ---- P1-8 骨架指纹重复 ----
    fp: dict[tuple, list[str]] = {}
    for s in shots:
        key = (s.get("skeleton"), s.get("cameraIntent"), s.get("transition"), s.get("entry"))
        fp.setdefault(key, []).append(s.get("id", "?"))
    for key, ids in fp.items():
        if len(ids) > 1:
            p1.append({"id": "-", "issue": f"骨架指纹 {key} 出现 {len(ids)} 次（{ids}）；隔镜重复会让观众觉得“这段我看过”"})

    # ---- P1-9 镜长分布 ----
    durs = [int(s.get("duration") or 0) for s in shots]
    if len(durs) >= 3:
        lo, hi = min(durs), max(durs)
        ratio = hi / max(1, lo)
        if ratio < MIN_LENGTH_RATIO:
            p1.append({"id": "-", "issue": f"最长/最短镜头仅 {ratio:.2f} 倍（{hi}/{lo}），全片一个速度=节拍器；建议 2.5–3 倍以上"})
        share = {}
        for d in durs:
            for a, b, name in BANDS:
                if a <= d <= b:
                    share[name] = share.get(name, 0) + 1
                    break
        worst = max(share.items(), key=lambda kv: kv[1])
        if worst[1] / len(durs) > MAX_BAND_SHARE:
            p1.append({"id": "-", "issue": f"{worst[1]}/{len(durs)} 镜落在同一时长档（{worst[0]}）；长短要错开"})
        if not any(d <= 120 for d in durs):
            p1.append({"id": "-", "issue": "全片没有 ≤4s 的短镜；插入镜/重音镜头都该在这一档"})

    # ---- P1-10 主角尺寸 ----
    for s in shots:
        hero = s.get("hero") or {}
        size = hero.get("size")
        kind = hero.get("kind", "text")
        if size is None:
            p1.append({"id": s.get("id", "?"), "issue": "未声明 hero（主角）"})
            continue
        floor = HERO_MIN_GRAPHIC if kind == "graphic" else HERO_MIN_TEXT
        if int(size) < floor:
            p1.append({"id": s.get("id", "?"), "issue": f"hero.size={size}（{kind}）低于 {floor}；这个字段必须是**主体短边设计像素**，不是随便填的数"})

    # ---- P1-11 转场 / 入场多样性 ----
    transitions = [s.get("transition", "cut") for s in shots]
    if len(set(transitions)) < MIN_TRANSITIONS:
        p1.append({"id": "-", "issue": f"全片仅 {len(set(transitions))} 种转场，建议 ≥{MIN_TRANSITIONS} 种"})
    entries = [s.get("entry", "rise") for s in shots]
    if len(set(entries)) < MIN_ENTRIES:
        p1.append({"id": "-", "issue": f"全片仅 {len(set(entries))} 种入场方式，建议 ≥{MIN_ENTRIES} 种"})

    # ---- P1-12 状态变化间隔（汇总，带帧区间归因）----
    runs = []
    for s in shots:
        frames = sorted(int(b) for b in (s.get("beatsAbs") or []))
        if not frames:
            p1.append({"id": s.get("id", "?"), "issue": "未声明 beats（状态变化帧），无法判断节奏"})
            continue
        marks = [int(s["from"])] + frames + [int(s["to"])]
        gaps = [(b - a, a, b) for a, b in zip(marks, marks[1:])]
        if not gaps:
            continue
        worst, a, b = max(gaps)
        if worst > SLOW_GAP:
            runs.append((worst, s.get("id", "?"), a, b))
    over = [r for r in runs if r[0] > MAX_BEAT_GAP]
    near = [r for r in runs if SLOW_GAP < r[0] <= MAX_BEAT_GAP]
    if over:
        detail = "；".join(f"{i}({w}帧 f={a}-{b})" for w, i, a, b in sorted(over, reverse=True)[:4])
        p1.append({"id": "-", "issue": f"{len(over)} 处变化间隔 >{MAX_BEAT_GAP} 帧（4s），已超出文档的慢章节上限（3–4s）：{detail}"})
    if near:
        detail = "；".join(f"{i}({w}帧 f={a}-{b})" for w, i, a, b in sorted(near, reverse=True)[:4])
        p1.append({"id": "-", "issue": f"{len(near)} 处变化间隔在 3–4s（慢章节正常范围，但连成片会让节奏偏平）；若这些区段画面完全静止，按 motion-design 补一次呼吸：{detail}"})

    # ---- P1 组件词汇多样性（阈值用 DeepSeek 与 SWE-2 两条成片实测校准）----
    # 结构件豁免：骨架/外壳/相机/底托/小标签本来就该反复出现，要求它们多样化是荒谬的。
    STRUCTURAL = {"StageFrame", "Corridor", "SplitStage", "ZoomStage", "PhaseRail",
                  "ShotCamera", "CoverPanel", "LineIcon", "CheckBadge", "PillTag",
                  "StampBanner", "FitCard", "CardHead", "Shot"}
    used: dict[str, set] = {}
    for s in shots:
        for name in (s.get("live") or []):
            if name and name not in STRUCTURAL:
                used.setdefault(name, set()).add(s.get("id", "?"))
    n_used = len(used)
    need = 10 if len(shots) >= 16 else (7 if len(shots) >= 8 else 5)
    if n_used < need:
        p1.append({"id": "-", "issue": f"可选组件只用了 {n_used} 件（{sorted(used)}），{len(shots)} 镜建议 ≥{need} 件；修辞动作 → 组件 见 media-routing.md"})
    for name, ids in used.items():
        share = len(ids) / max(1, len(shots))
        if share > 0.35:
            p1.append({"id": "-", "issue": f"“{name}” 出现在 {len(ids)}/{len(shots)} 镜（{share:.0%}）超过 35%；同一件高频复用要换表达"})
    # ---- P1 反堆砌：只出现 1 镜的可选件 = 堆砌指纹 ----
    lonely = sorted(n for n, ids in used.items() if len(ids) == 1)
    # 只在成片（≥12 镜）上判：短样板片里"一件只出现 1 镜"是正常演示，不算堆砌
    if len(shots) >= 12 and len(lonely) >= 5:
        p1.append({"id": "-", "issue": f"{len(lonely)} 件可选组件只出现在 1 个镜头里（{lonely}）——像是为凑多样性塞的，请人工确认它们是否真的承接了某个修辞动作"})
    # ---- P1 节拍密度：长镜但节拍稀疏 → 台词还在念，画面已经冻住 ----
    for s in shots:
        dur = int(s.get("duration") or 0); nb = len(s.get("beatsAbs") or [])
        if dur > 240 and nb < 3:
            p1.append({"id": s.get("id", "?"), "issue": f"本镜 {dur} 帧（{dur / 30:.1f}s）只有 {nb} 个节拍；画面会在台词中途静止，建议补节拍或锯开"})

    # 覆盖率自述：让"没报"和"没跑"可区分
    notes.append(f"已校验：枚举 5 类 / live {len(live_names)} 个名字 / hero {len(shots)} 镜 / 时长 {len(durs)} 镜")
    return p0, p1, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--strict", action="store_true", help="把 P1 也当作失败")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"项目目录不存在：{project}", file=sys.stderr)
        return 2
    data = load(project)
    p0, p1, notes = check(data, scene_source(project))
    ii_p0, ii_note = import_integrity(project)
    p0 += ii_p0
    if ii_note:
        notes.append(ii_note)
    if args.json:
        print(json.dumps({"p0": p0, "p1": p1, "notes": notes, "shots": len(data.get("shots", []))}, ensure_ascii=False, indent=2))
    else:
        shots = data.get("shots", [])
        print(f"validate-composition · {len(shots)} 镜")
        for item in p0:
            print(f"  P0 {item['id']}: {item['issue']}")
        for item in p1:
            print(f"  P1 {item['id']}: {item['issue']}")
        for n in notes:
            print(f"  ·· {n}")
        verdict = "PASS" if not p0 and not (args.strict and p1) else "FAIL"
        print(f"结论：P0={len(p0)} P1={len(p1)} → {verdict}")
    if p0:
        return 1
    if args.strict and p1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
