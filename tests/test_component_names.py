#!/usr/bin/env python3
"""件名一致性：模块对外导出的组件 ⇔ 文档的组件索引，两边一一对上。

- 组件库（components/ + kit / fxkit / media / stagekit / skeletons / insert / shotkit / toolkit）
  ⇔ references/media.md §5.1 表格第一列；
- craft/index.ts 的组件 ⇔ references/components.md 的 craft-kit 表格。

导出了却不在索引里 = 模型查不到的死件；索引里有却没导出 = 照抄就编译失败。
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "lecture-template" / "src"
LIB_MODULES = ["kit", "fxkit", "media", "stagekit", "skeletons", "insert", "shotkit", "toolkit"]
# 引擎运动件，索引里单列、不计件
ENGINE_ONLY = {"KineticNumber"}


def _react_exports(text: str) -> set[str]:
    return set(re.findall(r"export const ([A-Z]\w+)\s*:\s*React\.FC", text))


def _barrel_names(text: str) -> set[str]:
    names: set[str] = set()
    for m in re.finditer(r"export\s*\{([^}]*)\}", text):
        names |= {x.strip() for x in m.group(1).split(",") if x.strip()}
    return names


def _component_like(names: set[str]) -> set[str]:
    # PascalCase 才是组件；SHAPES / TYPE 这类全大写常量不算
    return {n for n in names if re.fullmatch(r"[A-Z][a-z]\w*", n)}


def _table_names(md: str, start: str, stop: str) -> set[str]:
    sec = md[md.index(start):]
    sec = sec[: sec.index(stop)]
    out: set[str] = set()
    for line in sec.splitlines():
        if line.startswith("| `"):
            first = line.split("|")[1]
            out |= set(re.findall(r"`([A-Z]\w+)`", first))
    return out


class ComponentNames(unittest.TestCase):
    def test_library_matches_media_index(self):
        exported: set[str] = set()
        for f in sorted((SRC / "components").glob("*.tsx")):
            exported |= _react_exports(f.read_text(encoding="utf-8"))
        exported &= _component_like(_barrel_names((SRC / "components" / "index.ts").read_text(encoding="utf-8")))
        for mod in LIB_MODULES:
            exported |= _react_exports((SRC / f"{mod}.tsx").read_text(encoding="utf-8"))
        md = (ROOT / "references" / "media.md").read_text(encoding="utf-8")
        listed = _table_names(md, "### 5.1 ", "### 6.") - ENGINE_ONLY - {"SHAPES"}
        self.assertEqual(sorted(exported - listed), [], "导出了但 media.md §5.1 没登记")
        self.assertEqual(sorted(listed - exported), [], "media.md §5.1 登记了但没有导出")

    def test_craft_matches_components_index(self):
        exported = _component_like(_barrel_names((SRC / "craft" / "index.ts").read_text(encoding="utf-8")))
        md = (ROOT / "references" / "components.md").read_text(encoding="utf-8")
        mentioned = set(re.findall(r"`<?([A-Z]\w+)", md))
        rows = _table_names(md, "## craft 组件", "### 组合配方")
        self.assertEqual(sorted(rows - exported), [], "components.md 的 craft 表登记了但没有导出")
        listed = mentioned
        self.assertEqual(sorted(exported - listed), [], "craft/index.ts 导出了但 components.md 没提到")


if __name__ == "__main__":
    unittest.main()
