#!/usr/bin/env python3
"""CLI 入口的结构契约（P2-24 · mjs 侧）。

为什么不把 `notebook-video.mjs` 物理拆成多个模块：
`tests/` 里有 8 个文件直接读这个入口的源码做契约断言（锁顺序、锁参数、reduced-motion 的传递、
sweep 的取样口径）。拆一个函数要同时改模块与这些锚点，等于**让同一处行为修改触及更多文件**——
正好违背 P2-24 自己的判据。所以这里做的是结构治理：用固定格式的分段标记把 1700 行切成可导航的
17 段，改哪一块一眼能看到边界。

这条测试锁两件事：
  1. 分段标记还在（有人重排代码时别把导航弄丢）；
  2. 分段顺序与声明顺序一致（标记错位比没有标记更误导）。
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "notebook-video.mjs"

# 段落标题 → 该段第一个顶层声明。改结构时同步改这里，测试会告诉你漏了哪段。
SECTIONS = [
    ("基础工具", "const hideConsoleArgs"),
    ("字体", "const THEME_IDS"),
    ("工程准备", "const newProject"),
    ("渲染基础", "const suggestedConcurrency"),
    ("Remotion 调用", "const runRemotionFiltered"),
    ("运行日志与渲染锁", "let RUN"),
    ("render 命令", "const render"),
    ("render-range", "const renderRange"),
    ("preview", "const preview"),
    ("sweep", "const SWEEP_GRID"),
    ("审片", "const reviewFrames"),
    ("校验", "const validateVideo"),
    ("打包", "const packageProject"),
    ("showcase", "const SHOWCASE_DELIVERY_SCALE"),
    ("poster", "const signatureShotId"),
    ("deliver", "const deliver"),
    ("CLI", "const usage"),
]


class SectionHeaderTest(unittest.TestCase):
    def setUp(self):
        self.src = CLI.read_text(encoding="utf-8")
        self.lines = self.src.splitlines()

    def test_every_section_has_a_header_right_above_its_first_decl(self):
        missing = []
        for title, anchor in SECTIONS:
            idx = next((i for i, ln in enumerate(self.lines) if ln.startswith(anchor)), None)
            self.assertIsNotNone(idx, f"找不到声明 {anchor}（改名了？）")
            # 允许中间隔一行空行；标题必须紧贴（<=3 行内）
            window = "\n".join(self.lines[max(0, idx - 3):idx])
            if title not in window:
                missing.append(f"{title}（应出现在 {anchor} 前 3 行内）")
        self.assertFalse(missing, "分段标题缺失或位置漂移：\n  " + "\n  ".join(missing))

    def test_section_order_matches_declaration_order(self):
        positions = []
        for title, anchor in SECTIONS:
            positions.append(next(i for i, ln in enumerate(self.lines) if ln.startswith(anchor)))
        self.assertEqual(positions, sorted(positions),
                         "分段顺序与 SECTIONS 不一致：代码被重排了，标题也要跟着挪")

    def test_header_format_is_uniform(self):
        # 统一格式便于 grep：`// ---…` + `// 标题` + `// ---…`
        bars = [ln for ln in self.lines if re.fullmatch(r"// -{70}", ln)]
        self.assertEqual(len(bars), len(SECTIONS) * 2,
                         f"分隔线应有 {len(SECTIONS) * 2} 条（每段上下各一条），实际 {len(bars)}")


class NoDuplicateImplementationTest(unittest.TestCase):
    def test_cli_is_still_a_single_entry(self):
        # 入口只此一份：另外再出现 `const main = async` 之类就是要分叉了
        hits = (ROOT / "scripts" / "notebook-video.mjs").read_text(encoding="utf-8").count("const main = async")
        self.assertEqual(hits, 1, f"main() 应只有一份，实际 {hits}")


if __name__ == "__main__":
    unittest.main()
