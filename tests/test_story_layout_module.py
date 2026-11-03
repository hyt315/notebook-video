#!/usr/bin/env python3
"""P2-24 第四切片 · 版式层的边界契约。

版式是最大的一块，也是改得最频繁的一块。这批测试不重复 compose-golden 的"输出一字不差"，
而是锁三件在拆分时容易坏、坏了又不容易发现的事：

  1. **分发完整性**：`LAY` 的键必须等于 `LAYOUTS`（少一个 = 某种版式静默没有实现）；
  2. **共享可变对象**：`STORY_MEDIA` 是 dict，`compose()` 只 mutation 不 rebind；
     若主文件重新绑定（`STORY_MEDIA = {...}`），media 版式会看不到尺寸——不报错，只按 16:9 瞎排；
  3. **单一真源**：字号三档 / 内容带 / 取景框常量只能有一处定义（两处就会分叉）。
"""
from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


layout = load("layout_contract", SCRIPTS / "story_layout.py")
cs = load("cs_layout_contract", SCRIPTS / "compose-story.py")


class Collector:
    def __init__(self):
        self.errors, fixes, hints = [], [], []

    def err(self, m): self.errors.append(m)
    def fix(self, m): self.fixes.append(m)
    def hint(self, m): self.hints.append(m)


class FacadeTest(unittest.TestCase):
    def test_entrypoint_uses_layout_layer(self):
        self.assertEqual(cs.el.__module__, "story_layout",
                         "el() 不是 story_layout 的实现（调版式却改主文件，正是 P2-24 想去掉的事）")
        # 用 sys.modules 里的那份比 identity：测试若把 story_layout 另起名加载，
        # 会得到两个模块实例，identity 假失败。
        mod = sys.modules["story_layout"]
        for name, fn in mod.LAY.items():
            # LAY 的键是版式名（media / page / …），实现函数统一叫 lay_<版式名>。
            self.assertEqual(getattr(cs, "lay_" + name).__module__, "story_layout", name)
            self.assertIs(cs.LAY[name], fn)

    def test_every_declared_layout_has_an_implementation(self):
        # LAYOUTS 是「作者能写的版式名」，LAY 是「真有实现的那几个」；两边不一致 = 静默缺版式。
        self.assertEqual(set(cs.LAYOUTS), set(layout.LAY),
                         f"LAYOUTS 与 LAY 不一致：{set(cs.LAYOUTS) ^ set(layout.LAY)}")
        self.assertEqual(len(layout.LAY), 13)


class SharedMediaStateTest(unittest.TestCase):
    def tearDown(self):
        layout.STORY_MEDIA.clear()

    def test_entrypoint_reads_the_same_dict_object(self):
        self.assertIs(cs.STORY_MEDIA, sys.modules["story_layout"].STORY_MEDIA,
                      "STORY_MEDIA 不是同一个 dict —— compose 填的尺寸，版式看不到")

    def test_filling_the_dict_is_seen_by_lay_media(self):
        # 模拟 compose() 的填法：mutation，不是重新赋值。
        layout.STORY_MEDIA.clear()
        layout.STORY_MEDIA["m1"] = {"id": "m1", "width": 1600, "height": 900, "focusRegions": []}
        p = Collector()
        els = layout.lay_media(p, "S1", {"media": "m1"}, "a")
        self.assertTrue(els, "填了 media 之后 lay_media 仍然排不出元素")
        self.assertEqual(els[0]["media"], "m1")
        self.assertFalse(p.errors)

    def test_missing_media_is_reported(self):
        p = Collector()
        self.assertEqual(layout.lay_media(p, "S1", {"media": "nope"}, "a"), [])
        self.assertTrue(p.errors, "media id 不存在时必须报错，不能静默排空")


class SingleSourceTest(unittest.TestCase):
    CHAIN = ("compose-story.py", "story_layout.py", "story_text.py",
             "story_caption.py", "story_acts.py", "story_time.py")

    def _defs(self, pattern: str) -> list[str]:
        hits = []
        for name in self.CHAIN:
            for i, line in enumerate((SCRIPTS / name).read_text(encoding="utf-8").splitlines(), 1):
                if re.match(pattern, line):
                    hits.append(f"{name}:{i}")
        return hits

    def test_layout_constants_defined_once(self):
        for pattern, name in ((r"^TYPE\s*=", "TYPE"),
                              (r"^BAND\s*=", "BAND"),
                              (r"^FLOW_TOTAL_MAX\s*=", "FLOW_TOTAL_MAX"),
                              (r"^PAGE_MEDIA\s*=", "PAGE_MEDIA"),
                              (r"^INK_BOX\s*=", "INK_BOX"),
                              (r"^SKETCH_BOX\s*=", "SKETCH_BOX"),
                              (r"^RECIPE_BOX\s*=", "RECIPE_BOX"),
                              (r"^UNIT_TOKENS\s*=", "UNIT_TOKENS"),
                              (r"^STORY_MEDIA\s*:", "STORY_MEDIA")):
            hits = self._defs(pattern)
            self.assertEqual(len(hits), 1, f"{name} 定义处应唯一，实际 {hits}")
            self.assertTrue(hits[0].startswith("story_layout.py:"), f"{name} 真源应在 story_layout，实际 {hits}")

    def test_layout_layer_has_no_reverse_import(self):
        src = (SCRIPTS / "story_layout.py").read_text(encoding="utf-8")
        for ln in src.splitlines():
            if re.match(r"\s*(import|from)\s+", ln):
                self.assertNotIn("compose", ln, f"story_layout 反向依赖主文件：{ln.strip()}")


class ElTest(unittest.TestCase):
    def test_rounds_coordinates_and_keeps_extras(self):
        d = layout.el("x1", "text", 10.04, 20.06, 30.5, 40.49, "hi", 20, "body", 3, lines=["a"])
        self.assertEqual((d["x"], d["y"], d["w"], d["h"]), (10.0, 20.1, 30.5, 40.5))
        self.assertEqual(d["kind"], "text")
        self.assertEqual(d["lines"], ["a"])


class PackageIncludesModuleTest(unittest.TestCase):
    def test_package_collects_layout_layer(self):
        pk = load("pkg_layout_contract", SCRIPTS / "package-skill.py")
        files = {p.relative_to(ROOT).as_posix() for p in pk.collect_files()}
        self.assertIn("scripts/story_layout.py", files)


if __name__ == "__main__":
    unittest.main()
