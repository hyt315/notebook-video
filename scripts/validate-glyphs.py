#!/usr/bin/env python3
"""validate-glyphs.py · 中文字面门禁：上屏文字用的字体栈里，必须有一个真正带 CJK 字形的族。

为什么需要（2026-10-30 实测）：`CODE_FONT` 写成 `…,monospace,Kai` —— CSS 里**泛型族之后的名字
一律被忽略**，于是 Kai 从未参与回退；渲染机（Linux）没有 Consolas / Menlo，`monospace` 落到
DejaVu Sans Mono（无 CJK 字面），代码卡里的「输出：」就渲成豆腐块。调换字体顺序"看起来修了"，
但没有门禁时，下一次任何人写 `fontFamily:'Space,monospace'` 都会重犯。

判据（只看**静态声明的字体栈**，不需要渲染）：
  1. 栈里必须有一个「在 fonts.tsx 里声明过、且覆盖 CJK」的族（Kai / NotoSerifSC，或
     通过 `cjkFallbackFaces('X', …)` 补了 unicode-range CJK 字面的显示字体族）；
  2. 泛型族（monospace / sans-serif / serif / system-ui …）必须是**最后一个**；
  3. 引用的 CJK 族必须在 fonts.tsx 里真的用 @font-face 声明过（拼错名字 = 静默回退到系统字体）。

用法：
    python scripts/validate-glyphs.py PROJECT_DIRECTORY
退出码：0 通过 / 1 有 P0 / 2 用法错误。零第三方依赖。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

GENERIC = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-monospace", "emoji", "math"}
# 这两个是随包字体（OFL-1.1），@font-face 在 fonts.tsx 里声明，字面覆盖 CJK。
BASE_CJK = {"Kai", "NotoSerifSC"}

# 只认字面量。四种真实写法各一条（JSX 属性 / 对象样式 / 默认参数 / 常量）：
#   <text fontFamily="Kai,sans-serif">       → 双引号属性
#   style={{fontFamily: 'Space,Kai'}}        → 单引号
#   const CODE_FONT = "'JetBrains',…,Kai"    → 外层双引号、内层单引号
#   fontFamily = 'Kai'                       → 默认参数
STACK_RES = (
    re.compile(r'fontFamily\s*=\s*"([^"\n]+)"'),
    re.compile(r"fontFamily\s*[:=]\s*'([^'\n]+)'"),
    re.compile(r'fontFamily\s*[:=]\s*"([^"\n]+)"'),
    re.compile(r'(?:_FONT|FONT)\s*=\s*"([^"\n]+)"'),
    re.compile(r"(?:_FONT|FONT)\s*=\s*'([^'\n]+)'"),
)
# 动态拼接（`${family},sans-serif`）无法静态判定，跳过并计数，不冒充"查过了"。
DYNAMIC_RE = re.compile(r"fontFamily\s*[:=]\s*\{?\s*`")


def declared_cjk_families(fonts_tsx: Path) -> set[str]:
    """fonts.tsx 里真正声明了 CJK 字面的族：Kai / NotoSerifSC + cjkFallbackFaces('X', …)。"""
    if not fonts_tsx.is_file():
        return set(BASE_CJK)
    text = fonts_tsx.read_text(encoding="utf-8")
    families = set(re.findall(r"cjkFallbackFaces\(\s*['\"]([^'\"]+)['\"]", text))
    for name in BASE_CJK:
        if re.search(rf"font-family:\s*{re.escape(name)}\b", text):
            families.add(name)
    return families


def scan(project: Path) -> tuple[list[str], int, int]:
    src = project / "src"
    if not src.is_dir():
        return [f"src/ 不存在：{project} 不是一个可渲染工程"], 0, 0
    cjk = declared_cjk_families(src / "fonts.tsx")
    errors: list[str] = []
    checked = dynamic = 0
    for f in sorted(src.rglob("*")):
        if f.suffix not in (".tsx", ".ts") or f.name.endswith(".d.ts"):
            continue
        text = f.read_text(encoding="utf-8")
        dynamic += len(DYNAMIC_RE.findall(text))
        found: list[tuple[int, str]] = []
        for rx in STACK_RES:
            found += [(m.start(), m.group(1)) for m in rx.finditer(text)]
        for pos, raw in sorted(found):
            raw = raw.strip()
            if not raw or "${" in raw:
                continue
            checked += 1
            stack = [p.strip().strip("'\"") for p in raw.split(",") if p.strip()]
            if not stack:
                continue
            line = text.count("\n", 0, pos) + 1
            where = f"{f.relative_to(src)}:{line}"
            # 判据 1：栈里得有一个带 CJK 字面的族
            has_cjk = any(p in cjk for p in stack)
            if not has_cjk:
                errors.append(
                    f"{where}: 字体栈 {raw!r} 里没有任何带 CJK 字面的族 —— 中文会渲成豆腐块。"
                    f" 改成在泛型族**之前**加 {sorted(cjk)[0]!r}（例：'Consolas,Menlo,Kai,monospace'）。"
                )
                continue
            # 判据 2：泛型族必须是最后一个；泛型之后再写任何族都会被浏览器忽略
            for i, p in enumerate(stack):
                if p in GENERIC and i != len(stack) - 1:
                    errors.append(
                        f"{where}: 字体栈 {raw!r} 把泛型族 {p!r} 放在第 {i + 1} 位 —— "
                        f"CSS 会忽略它之后的所有族（{', '.join(stack[i + 1:])} 永远不会生效）。"
                        f" 泛型族必须放最后。"
                    )
                    break
    return errors, checked, dynamic


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    a = ap.parse_args()
    project = a.project.resolve()
    if not project.is_dir():
        print(f"没有这个工程目录：{project}", file=sys.stderr)
        return 2
    errors, checked, dynamic = scan(project)
    for e in errors:
        print(f"  ✗ P0 {e}")
    print(
        f"validate-glyphs：静态检查 {checked} 条字体栈 / 跳过 {dynamic} 条动态拼接 · "
        f"{'PASS' if not errors else f'FAIL（{len(errors)} 个 P0）'}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
