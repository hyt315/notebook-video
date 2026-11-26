"""3.6.2 · 手作皮肤的「纸感」纪律：组件不能在手账纸上长成 PPT

事故记录（3.6.1 样张实测）：手账纸 + `layout:"compare"` 渲染出来是两张大白卡片，
16px 圆角、2px UI 描边、悬浮阴影——旁边那页是真图版 + 手写 + 印章，切过去像两张片子拼的。
根因：`auto.tsx` 的 `ElemView` 里 panel / node / card 的容器样式只有一套（按组件皮肤写的），
手作皮肤没有变体。

判据（静态源码，不渲染）：
  · 手作分支存在（`HANDMADE_MEDIUM` 常量 + `paperCard` + `Tape`）；
    （3.5.4：原 `CRAFT` 布尔已改名 `HANDMADE_MEDIUM = isHandmadeMedium(THEME)`——
    flat / cel 也声明 craft 能力，"手作媒介"要单独判。本文件此前是 pytest 风格裸函数，
    `unittest discover` 收集不到，从未运行；现改为 unittest.TestCase。）
  · panel / node / card 三个容器的背景走 `...paperCard`，不再各自写 `background: C.paper`；
  · 手作分支的圆角是 2（不是 16 / 18 / 20）；抄成圆角卡片就退回 PPT。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

AUTO = Path(__file__).resolve().parent.parent / "assets" / "lecture-template" / "src" / "auto.tsx"


def _text() -> str:
    return AUTO.read_text(encoding="utf-8")


class CraftPaperTest(unittest.TestCase):
    def test_craft_variant_exists(self):
        t = _text()
        self.assertIn("const HANDMADE_MEDIUM = isHandmadeMedium(THEME)", t)
        self.assertIn("const paperCard:", t)
        self.assertIn("const Tape:", t)

    def test_panels_and_nodes_use_paper_card(self):
        t = _text()
        # 四个容器（panel / node / card|note|quote / item）都以 paperCard 打底
        self.assertGreaterEqual(t.count("...paperCard"), 4, "panel / node / card / item 都要走纸感变体")
        self.assertIn("borderRadius: 2", t, "手作纸片的圆角必须是 2px（裁纸的直角，不是 UI 卡片）")
        # 唯一允许保留组件圆角的地方是 flat / cel 分支（paperCard 的三元 else）
        flat_branch = re.search(
            r"paperCard: React\.CSSProperties = HANDMADE_MEDIUM\s*\?\s*\{[^}]*\}\s*:\s*\{([^}]*)\}", t)
        self.assertTrue(flat_branch, "paperCard 必须写成 HANDMADE_MEDIUM ? 纸感 : 组件皮肤 的三元")
        self.assertIn("borderRadius: THEME.aesthetic.paperRadius", flat_branch.group(1))  # 组件皮肤圆角由主题给（flat 22 / cel 8）
        # panel / node / card / item 四处容器不再各自写死圆角（那是事故原样）
        for marker in ("case 'panel'", "case 'node'", "case 'card': case 'note': case 'quote'", "case 'item'"):
            i = t.find(marker)
            self.assertGreaterEqual(i, 0, f"找不到 {marker}")
            seg = t[i: i + 900]
            self.assertNotIn("borderRadius: 16", seg, f"{marker} 又在容器上写死圆角了")
            self.assertNotIn("borderRadius: 20", seg, f"{marker} 又在容器上写死圆角了")

    def test_craft_has_tape(self):
        """纸片左上角要有和纸胶带——这是「贴上去的」和「弹出来的」之间唯一的物理差别。"""
        tape_calls = re.findall(r"\{HANDMADE_MEDIUM && <Tape", _text())
        self.assertGreaterEqual(len(tape_calls), 2, "panel 与 node 都要贴胶带")

    def test_list_items_have_container_but_no_craft_tape(self):
        """全组件清单需要纸卡层次，但不能顺手贴胶带、加随机倾角。"""
        t = _text()
        start = t.index("case 'item'")
        seg = t[start:t.index("case 'option'", start)]
        self.assertIn("...paperCard", seg)
        self.assertNotIn("<Tape", seg)
        self.assertNotIn("tiltOf", seg)
        self.assertIn("alignItems: 'center'", seg)


if __name__ == "__main__":
    unittest.main()
