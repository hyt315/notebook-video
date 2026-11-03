#!/usr/bin/env python3
"""validate-elem-kinds.py · 元素种类必须在渲染器里真有实现

为什么需要这条门禁（3.6.2，实测漏过一次）：
`flow` 版式生成 `kind: "node"` 的节点。`auto.tsx` 的 `ElemView` 早期只处理到
`archive / lettering / stamp / handnote / loupe / figure / media / region`，
**没有 `node`** → switch 落到 default 返回 null，节点整个不画；
后来加了 `case 'node'` 又把 `Box` 的 CSS 写成了非法的 `inset: 0, border: ..., border: ...`，
React 抛 error #130，整片渲染在第 566 帧直接失败。

两次都是「排版器生成了一个渲染器不认识的 kind」。片长几十秒，`--stills` 只截前几镜，
`validate-fusion` / `validate-composition` / `validate-opening` 全都不看这个，于是整片渲染
才发现——那时已经跑了几分钟。

判据很窄，只做一件事：**compose-story 能产出的每一种 `kind`，`auto.tsx` 里必须有对应的
`case '<kind>'`**。两个方向都读源码，不引入运行期依赖。

用法：
    python scripts/validate-elem-kinds.py PROJECT_OR_TEMPLATE
退出码：0 通过 / 1 有缺 / 2 用法错误。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# 排版器里出现过的 kind 都是 `el("<元素id>", "<kind>", ...)` 的第二个参数。
# 第一个参数可以是非 f-string 字面量（"text" / "verdict"）或 f-string（f"step{i+1}"）：
# 两种都要认，否则 flow 的 node、list 的 item 会被当成"从没产出过"，判据等于没跑。
EL_CALL = re.compile(r'\bel\(\s*(?:f)?"[^"]*"\s*,\s*"([a-z_]+)"')
# 渲染器的种类分发统一写成 `case '<kind>':`（可多个 case 并排共用一段实现）。
# case 后面只可能是 `'x':` / `'x'` / `{`（case 值里再用表达式时会写成 `'x': {`），
# 现在只取 `case 'a':` / `case 'a': case 'b':` 这一种，够覆盖 ElemView 的写法。
CASE = re.compile(r"case\s+((?:'[a-z_]+'\s*(?::|(?=case)))+)")
# 不是 ElemView 的种类：custom 走 AutoShot 里的独立分支，不经过 ElemView 的 switch。
NOT_ELEM_KINDS = {"custom"}


def kinds_emitted(*sources: str) -> set[str]:
    """从排版器的 `el(id, kind, ...)` 调用里取 kind。

    逐个 `el(` 起头扫描括号深度，避免正则跨过嵌套的 `el(...)` 或把参数里的字符串当 id。
    一行里两次 el 调用很常见（`els += [el(...), el(...)]`），所以不能只按行切。

    P2-24 第四切片起版式在 `story_layout.py`（主文件只剩流水线），所以要接受多份源码拼着扫。
    """
    compose_src = "\n".join(sources)
    found: set[str] = set()
    for m in re.finditer(r"\bel\(", compose_src):
        i, depth = m.end(), 1
        while i < len(compose_src) and depth:
            ch = compose_src[i]
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        inner = compose_src[m.end():i]
        args = _split_top(inner)
        if len(args) >= 2:
            k = re.fullmatch(r"\s*(?:f)?[\"']([a-z_]+)[\"']\s*", args[1])
            if k:
                found.add(k.group(1))
    return found


def _split_top(text: str) -> list[str]:
    """按深度 0 的逗号切开参数列表（字符串里的逗号不算）。"""
    out, buf, depth, quote = [], [], 0, None
    for ch in text:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch in "([{":
            depth += 1
            buf.append(ch)
        elif ch in ")]}":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            out.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    out.append("".join(buf))
    return out


def kinds_handled(auto_src: str) -> set[str]:
    """只取 ElemView 那个 switch 里的 case：`tone()` 里也有 `case 'blue':`，
    把整份文件扫一遍会把颜色键当成"已处理的 kind"。
    """
    start = auto_src.find("const ElemView")
    if start < 0:
        return set()
    body = auto_src[start:]
    end = body.find("\nconst ", 10)
    if end > 0:
        body = body[:end]
    found: set[str] = set()
    for group in CASE.findall(body):
        found.update(re.findall(r"'([a-z_]+)'", group))
    return found


def kinds_in_output(story_ts_text: str) -> set[str]:
    """从 compose 的**真实产物**（`src/story.ts` 里的 STORY 表）取 kind。

    为什么要这一层：`kinds_emitted` 扫的是排版器源码里 `el(...)` 的字面量，
    能证明"代码里写过什么"，不能证明"这次真的排出了什么"。产物是唯一的事实——
    它同时覆盖模板自带元素与 compose 中途构造的 kind。
    """
    m = re.search(r"export const STORY[^=]*=\s*", story_ts_text)
    if not m:
        return set()
    start = story_ts_text.index("{", m.end())
    depth, end = 0, None
    for i in range(start, len(story_ts_text)):
        if story_ts_text[i] == "{":
            depth += 1
        elif story_ts_text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        return set()
    try:
        table = json.loads(story_ts_text[start:end + 1])
    except ValueError:
        return set()
    out: set[str] = set()
    for shot in table.values():
        for e in (shot or {}).get("elements", []) or []:
            k = e.get("kind")
            if isinstance(k, str):
                out.add(k)
    return out - NOT_ELEM_KINDS


def check(project: Path) -> list[str]:
    auto = project / "src" / "auto.tsx"
    # 工程目录（new-project 会拷一份 compose 进 scripts/）与技能模板（compose 在技能根）
    # 两种布局都要能查：找不到工程内那份就退到技能自带的这份。
    # 版式在 story_layout.py（P2-24 起），主文件只剩 compose/build；旧工程可能只有前者。
    # 优先用工程里自带的那份（用户工程可能落后于技能），都没有才退到技能模板。
    here = Path(__file__).resolve().parent
    local = [project / "scripts" / "story_layout.py", project / "scripts" / "compose-story.py"]
    sources = [p for p in local if p.is_file()] or [p for p in (here / "story_layout.py", here / "compose-story.py") if p.is_file()]
    if not auto.is_file():
        return [f"missing {auto}"]
    if not sources:
        return [f"missing {here / 'compose-story.py'} / story_layout.py"]
    emitted = kinds_emitted(*(p.read_text(encoding="utf-8") for p in sources)) - NOT_ELEM_KINDS
    handled = kinds_handled(auto.read_text(encoding="utf-8"))
    if not emitted:
        return ["排版器（story_layout.py / compose-story.py）里一个 el(...) 都没解析出来 —— 判据无法执行（格式变了？）"]
    missing = sorted(emitted - handled)
    errors = [
        f"元素种类 {kind!r} 由 compose-story 排版出来，但 {auto.name} 的 ElemView 里没有 "
        f"case '{kind}' —— 这一镜的这类元素会被静默丢弃（default 分支返回 null），"
        f"或者在渲染到那一镜时整片失败。加上 case 分支，或用 validate-fusion 的规则改用别的版式"
        for kind in missing
    ]
    # 工程里已有排版产物时，按**产物**再查一遍：源码扫描能证明"写过"，产物才证明"真排出来了"。
    story_ts = project / "src" / "story.ts"
    if story_ts.is_file():
        actual = kinds_in_output(story_ts.read_text(encoding="utf-8"))
        for kind in sorted(actual - handled):
            errors.append(
                f"src/story.ts 实际排出了元素种类 {kind!r}，但 {auto.name} 的 ElemView 里没有 "
                f"case '{kind}' —— 这一镜的这类元素会被静默丢弃")
        # 产物里的 kind 如果源码扫描没认出来，说明 el(...) 的解析规则又跟不上排版器了
        # （f-string id 那次就是这样：node/item/option 全被当成"从没产出过"）。
        for kind in sorted(actual - emitted):
            errors.append(
                f"src/story.ts 排出了 {kind!r}，但 kind_emitted 没从 compose-story.py 里扫到它 —— "
                f"判据跟不上排版器的写法了（更新 EL_CALL 的解析）")
    errors.extend(stale_shots(project))
    return errors


def stale_shots(project: Path) -> list[str]:
    """`src/shots.ts` 必须来自 `manifests/shots.json`。

    实测踩过：手改 story.json 后只跑了 compose-story（只写 manifests/shots.json、
    src/story.ts），漏跑 resolve-shots，于是 `src/shots.ts` 还是**模板带来的 8 镜**，
    而 story 里只有 3 镜。渲染器按 shots.ts 取镜号，`SCENES['S5']` 拿不到 → 白屏；
    storyboard 与片子对不上，静帧却是对的（前几镜号刚好重合），整片渲染才崩。
    """
    man = project / "manifests" / "shots.json"
    src = project / "src" / "shots.ts"
    if not man.is_file() or not src.is_file():
        return []
    try:
        man_ids = {s.get("id") for s in json.loads(man.read_text(encoding="utf-8")).get("shots", [])}
    except (ValueError, AttributeError):
        return []
    ts_ids = set(re.findall(r"(?m)^\s*(S\d+):\s*\{id:'S\d+'", src.read_text(encoding="utf-8")))
    if not man_ids or not ts_ids:
        return []
    if man_ids != ts_ids:
        extra, lack = sorted(ts_ids - man_ids), sorted(man_ids - ts_ids)
        return [
            f"src/shots.ts 与 manifests/shots.json 不同步（只在 ts: {extra or '无'}；只在 json: {lack or '无'}）。"
            f"改了 story.json 之后必须跑 `notebook-video resolve-shots <工程>`"
            f"（或直接用 `make-video.mjs <story.json> <工程>` 一次走完）——否则渲染器还在按模板的旧镜号出片"
        ]
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path, help="工程目录，或 assets/lecture-template")
    args = ap.parse_args()
    project = args.project.resolve()
    if not project.is_dir():
        print(f"不是目录：{project}", file=sys.stderr)
        return 2
    errors = check(project)
    if errors:
        for e in errors:
            print(f"✗ {e}")
        return 1
    print(f"✓ 元素种类齐全：渲染器认识排版器会产出的每一种 kind（{project}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
