"""3.6.2 · 手作皮肤的「纸感」纪律：组件不能在手账纸上长成 PPT

事故记录（3.6.1 样张实测）：手账纸 + `layout:"compare"` 渲染出来是两张大白卡片，
16px 圆角、2px UI 描边、悬浮阴影——旁边那页是真图版 + 手写 + 印章，切过去像两张片子拼的。
根因：`auto.tsx` 的 `ElemView` 里 panel / node / card 的容器样式只有一套（按组件皮肤写的），
手作皮肤没有变体。

判据（静态源码，不渲染）：
  · 手作分支存在（`CRAFT` 常量 + `paperCard` + `Tape`）；
  · panel / node / card 三个容器的背景走 `...paperCard`，不再各自写 `background: C.paper`；
  · 手作分支的圆角是 2（不是 16 / 18 / 20）；抄成圆角卡片就退回 PPT。
"""

from __future__ import annotations

import re
from pathlib import Path

AUTO = Path(__file__).resolve().parent.parent / "assets" / "lecture-template" / "src" / "auto.tsx"


def _text() -> str:
    return AUTO.read_text(encoding="utf-8")


def test_craft_variant_exists():
    t = _text()
    assert "const CRAFT = Boolean((THEME as any).craft)" in t
    assert "const paperCard:" in t
    assert "const Tape:" in t


def test_panels_and_nodes_use_paper_card():
    t = _text()
    # 四个容器（panel / node / card|note|quote / item）都以 paperCard 打底
    assert t.count("...paperCard") >= 4, "panel / node / card / item 都要走纸感变体"
    assert "borderRadius: 2" in t, "手作纸片的圆角必须是 2px（裁纸的直角，不是 UI 卡片）"
    # 唯一允许保留组件圆角的地方是 flat / cel 分支（paperCard 的三元 else）
    flat_branch = re.search(r"paperCard: React\.CSSProperties = CRAFT\s*\?\s*\{[^}]*\}\s*:\s*\{([^}]*)\}", t)
    assert flat_branch, "paperCard 必须写成 CRAFT ? 纸感 : 组件皮肤 的三元"
    assert "borderRadius: 16" in flat_branch.group(1)
    # panel / node / card / item 四处容器不再各自写死圆角（那是事故原样）
    for marker in ("case 'panel'", "case 'node'", "case 'card': case 'note': case 'quote'", "case 'item'"):
        seg = t[t.find(marker): t.find(marker) + 900]
        assert "borderRadius: 16" not in seg and "borderRadius: 20" not in seg, f"{marker} 又在容器上写死圆角了"


def test_craft_has_tape():
    """纸片左上角要有和纸胶带——这是「贴上去的」和「弹出来的」之间唯一的物理差别。"""
    t = _text()
    tape_calls = re.findall(r"\{CRAFT && <Tape", t)
    assert len(tape_calls) >= 2, "panel 与 node 都要贴胶带"


def test_list_items_have_container_but_no_craft_tape():
    """全组件清单需要纸卡层次，但不能顺手贴胶带、加随机倾角。"""
    t = _text()
    start = t.index("case 'item'")
    seg = t[start:t.index("case 'option'", start)]
    assert "...paperCard" in seg
    assert "<Tape" not in seg
    assert "tiltOf" not in seg
    assert "alignItems: 'center'" in seg
