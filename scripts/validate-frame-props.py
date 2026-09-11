#!/usr/bin/env python3
"""validate-frame-props.py — 帧参数名门禁（P0）

病因（已在成片里实测到）：场景组件拿到的是**镜头内局部帧**（index.tsx 里
`<Scene f={f-s.from}/>`），而部分引擎组件把帧参数命名成 `frame`、部分命名成 `f`。
写错名字不会报错——组件会静默回落到 `useCurrentFrame()`（**全局帧**）。
结果是 `start={局部节拍}` 与全局帧比较，动画从镜头第一帧就是"完成态"，
看起来像"元素直接出现、没有进场动作"。

本脚本做两件事：
  1. 从引擎源码里提取每个导出组件的帧参数名（f / frame / 两者都收 / 都不收）。
  2. 逐个扫描场景文件里的 JSX 标签，检查实际传的参数名是否匹配。

判据：
  - 组件只收 `frame`，调用处却只给了 `f={...}`      → P0（静默回落）
  - 组件只收 `f`，调用处却只给了 `frame={...}`      → P0
  - 组件收帧参数，调用处两个都没给                  → P1（多数是漏传；局部帧场景下必错）
  - 组件不收帧参数，调用处传了 f 或 frame           → P1（多余属性，通常是从别的组件抄来的）

用法：
  python scripts/validate-frame-props.py <项目目录>
退出码：0 = 无 P0，1 = 有 P0。
"""
import os
import re
import sys

ENGINE_FILES = [
    "toolkit.tsx", "plates.tsx", "charts.tsx",
    "fxkit.tsx", "media.tsx", "kit.tsx", "stagekit.tsx", "skeletons.tsx",
    "insert.tsx", "shotkit.tsx", "scene-kit.tsx", "films.tsx",
]
# 场景文件/目录：只检查这些，因为只有它们运行在"镜头内局部帧"上下文
# 场景文件可能被拆成多份（scenes.tsx / scenes-a.tsx / scenes-kit.tsx …）。
# 旧版只匹配 "scenes.tsx"，一旦拆分就会一个文件都扫不到、静默空过——实测踩到过。
SCENE_HINT = "scene"

EXPORT_RE = re.compile(r"export\s+const\s+([A-Z]\w*)\s*[:=]")


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def match_braces(text, i):
    """text[i] 是 { < ( [ 之一，返回配对结束位置的下标（不含）。栈式配对，支持嵌套与字符串。"""
    openers = "{(<["
    closers = "})>]"
    stack = []
    quote = None
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'`":
            quote = ch
        elif ch in openers:
            stack.append(closers[openers.index(ch)])
        elif ch in closers:
            if stack and stack[-1] == ch:
                stack.pop()
                if not stack:
                    return i
        i += 1
    return len(text)


def split_top(text):
    """按顶层逗号/分号切分，返回每段的前导标识符。"""
    names, depth, cur = [], 0, ""
    for ch in text:
        if ch in "{[<(":
            depth += 1
        elif ch in "}]>)":
            depth -= 1
        if ch in ",;" and depth == 0:
            names.append(cur)
            cur = ""
        else:
            cur += ch
    names.append(cur)
    out = []
    for seg in names:
        m = re.match(r"\s*\.\.\.?\s*(\w+)|\s*(\w+)", seg)
        if m:
            out.append(m.group(1) or m.group(2))
    return out


def prop_names(text, start):
    """从 export 声明处提取该组件接收的参数名集合。"""
    # 搜索窗不得越到下一个 export const（否则常量会继承下一个组件的签名）
    nxt = text.find("export const", start + 1)
    limit = nxt if nxt != -1 else len(text)
    # 1) 优先取 React.FC<{...}> 的类型字面量（最可靠）
    m = re.compile(r"React\.FC\s*<").search(text, start, min(start + 2000, limit))
    if m:
        open_i = text.index("<", m.start())
        end_i = match_braces(text, open_i)
        inner = text[open_i + 1:end_i]
        if inner.lstrip().startswith("{"):
            brace_i = open_i + 1 + inner.index("{")
            inner = text[brace_i + 1:match_braces(text, brace_i)]
        # 类型块里允许写注释；注释会遮住它后面那个参数名，必须先剥掉
        inner = re.sub(r"/\*.*?\*/", " ", inner, flags=re.S)
        inner = re.sub(r"//[^\n]*", " ", inner)
        return set(split_top(inner))
    # 2) 退回解构参数 = ({a,b,c}) =>
    d = re.compile(r"=\s*\(\{").search(text, start, min(start + 2000, limit))
    if d:
        brace_i = text.index("{", d.start())
        inner = text[brace_i + 1:match_braces(text, brace_i)]
        inner = re.sub(r"/\*.*?\*/", " ", inner, flags=re.S)
        inner = re.sub(r"//[^\n]*", " ", inner)
        return set(split_top(inner))
    return set()


def collect_components(root):
    """{组件名: (收 f?, 收 frame?, 出处文件)}"""
    comps = {}
    search_dirs = [os.path.join(root, "src"), os.path.join(root, "engine", "src")]
    for base in search_dirs:
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            if not name.endswith(".tsx"):
                continue
            text = read(os.path.join(base, name))
            for m in EXPORT_RE.finditer(text):
                cname = m.group(1)
                names = prop_names(text, m.start())
                af, afr = "f" in names, "frame" in names
                comps[cname] = (af, afr, name)
    return comps


def jsx_tags(text):
    """产出 (组件名, 属性文本, 行号)。用花括号深度找标签结尾，避免 style={{...}} 里的 > 干扰。"""
    out = []
    for m in re.finditer(r"<([A-Z]\w*)", text):
        cname = m.group(1)
        i = m.end()
        depth = 0
        while i < len(text):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            elif ch == ">" and depth == 0:
                break
            elif ch == "/" and depth == 0 and i + 1 < len(text) and text[i + 1] == ">":
                break
            i += 1
        attrs = text[m.end():i]
        line = text.count("\n", 0, m.start()) + 1
        out.append((cname, attrs, line))
    return out


def has_attr(attrs, name):
    return re.search(r"(?<![A-Za-z0-9_$])" + name + r"\s*=", attrs) is not None


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/validate-frame-props.py <项目目录>")
        return 2
    root = os.path.abspath(sys.argv[1])
    comps = collect_components(root)
    if not comps:
        print(f"未在 {root} 找到引擎组件（检查 src/ 是否存在）")
        return 2

    scenes = []
    for base, _dirs, files in os.walk(os.path.join(root, "src")):
        for name in files:
            if name.endswith(".tsx") and name not in ENGINE_FILES and SCENE_HINT in name.lower():
                scenes.append(os.path.join(base, name))
    if not scenes:
        print(f"未在 {root}/src 找到场景文件（*{SCENE_HINT}）")
        return 2

    p0, p1 = [], []
    for path in scenes:
        rel = os.path.relpath(path, root).replace("\\", "/")
        text = read(path)
        for cname, attrs, line in jsx_tags(text):
            if cname not in comps:
                continue  # 非引擎组件（HTML 原生或未导出）不判
            accepts_f, accepts_frame, origin = comps[cname]
            gave_f = has_attr(attrs, "f")
            gave_frame = has_attr(attrs, "frame")
            where = f"{rel}:{line} <{cname}>"
            if accepts_frame and not accepts_f:
                if gave_f and not gave_frame:
                    p0.append(f"{where} 该组件只认 frame={{...}}，这里写的是 f={{...}} → 静默回落到全局帧，进场动画失效（{origin}）")
                elif not gave_f and not gave_frame:
                    p1.append(f"{where} 未传帧参数，将回落到全局帧；应写 frame={{f}}")
            elif accepts_f and not accepts_frame:
                if gave_frame and not gave_f:
                    p0.append(f"{where} 该组件只认 f={{...}}，这里写的是 frame={{...}} → 静默回落到全局帧（{origin}）")
                elif not gave_f and not gave_frame:
                    p1.append(f"{where} 未传帧参数，应写 f={{f}}")
            elif accepts_f and accepts_frame:
                if not gave_f and not gave_frame:
                    p1.append(f"{where} 两个帧参数都没传（该组件两者都收）")
            else:
                if gave_f or gave_frame:
                    p1.append(f"{where} 传了帧参数但该组件不使用（多余属性，通常是从别的组件抄来的）")

    # 防呆：组件表为空说明引擎源码没被读到，此时"PASS"是假阳性（实测过这种静默漏判）
    if len(comps) < 20:
        print(f"帧参数名门禁 · 只解析到 {len(comps)} 个组件，引擎源码可能没读到（ENGINE_FILES={ENGINE_FILES}）；不给出 PASS")
        return 2
    print(f"帧参数名门禁 · {len(scenes)} 个场景文件 · 引擎组件 {len(comps)} 个")
    for x in p0:
        print(f"  P0 {x}")
    for x in p1:
        print(f"  P1 {x}")
    verdict = "PASS" if not p0 else "FAIL"
    print(f"结论：P0={len(p0)} P1={len(p1)} → {verdict}")
    return 1 if p0 else 0


if __name__ == "__main__":
    sys.exit(main())
