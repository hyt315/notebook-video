#!/usr/bin/env python3
"""P1-12：单部位特写的取景框必须有几何依据，不能靠手填后祈祷。

问题不在"框得好看不好看"，而在**框错的时候没有任何信号**：fit 比图形小 → 特写只剩半边；
fit 在图形外 → 整张图缩在框的一角；引线落点在框外 → 一条指向画外的线。渲染全都成功。

所以这里钉三件事：
  ① 包围盒算法本身对（圆弧方向、相对命令、闭合）；
  ② 库里的 fit 与生成的缺省框都盖得住图形，且不会小到看不清；
  ③ 生成物（src/linework/crops.ts）与 library.ts 同步 —— 改库不重跑生成，是最容易发生的一种漂移。
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import linework_index as li  # noqa: E402

LIB = ROOT / "assets" / "lecture-template" / "src" / "linework" / "library.ts"
CROPS = ROOT / "assets" / "lecture-template" / "src" / "linework" / "crops.ts"
SKETCH = ROOT / "assets" / "lecture-template" / "src" / "linework" / "sketch.tsx"


def near(a: float, b: float, tol: float = 0.6) -> bool:
    return abs(a - b) <= tol


class PathBBoxTest(unittest.TestCase):
    def test_straight_lines_and_close(self):
        self.assertEqual(li.path_bbox("M0 0 H10 V10 H0 Z"), (0.0, 0.0, 10.0, 10.0))

    def test_arc_bulges_to_the_right_side(self):
        # sweep=1 的两个半圆：一个在上、一个在下。方向搞反会让包围盒上下颠倒 ——
        # 这正是第一版的问题（`large != sweep` 写反），结果是灯头被判成 84 宽，库里的 fit 全对不上。
        self.assertEqual(li.path_bbox("M30 50 A20 20 0 0 1 70 50"), (30.0, 30.0, 70.0, 50.0))
        self.assertEqual(li.path_bbox("M30 50 A20 20 0 0 0 70 50"), (30.0, 50.0, 70.0, 70.0))

    def test_arc_uses_endpoint_parameterization(self):
        # 真实库里的灯泡轮廓：半径 22 从 (50,8) 到 (62,48)，圆心在左侧，最右到 ~71.4
        x0, y0, x1, y1 = li.path_bbox("M50 8 A22 22 0 0 1 62 48")
        self.assertTrue(near(x1, 71.4, 1.0), x1)
        self.assertTrue(near(y1, 48.0), y1)
        self.assertLess(x0, 55)

    def test_relative_commands(self):
        self.assertEqual(li.path_bbox("m 10 10 l 5 0 l 0 5 z"), (10.0, 10.0, 15.0, 15.0))

    def test_curve_does_not_use_control_points(self):
        # 控制点比曲线本身远：M0 0 C 0 100, 100 100, 100 0 的真实最高点只有 75
        x0, y0, x1, y1 = li.path_bbox("M0 0 C0 100 100 100 100 0")
        self.assertTrue(near(y1, 75.0, 1.5), f"曲线最高点应约 75，得到 {y1}")

    def test_bbox_of_prims_mixes_helpers_and_objects(self):
        box = li.prims_bbox("prims: [r(10, 10, 20, 20), c(50, 50, 5), {k: 'line', x1: 0, y1: 0, x2: 3, y2: 70}]")
        self.assertEqual(box, (0.0, 0.0, 55.0, 70.0))


class LibraryGeometryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geo = li.load_geometry()
        cls.crops = li.part_crops()

    def test_every_sketch_has_a_bbox(self):
        missing = [n for n, sk in self.geo.items() if not sk.get("bbox")]
        self.assertEqual(missing, [], "这些线稿解析不出任何基本形")

    def test_fits_cover_their_drawing(self):
        errors, _ = li.geometry_problems()
        self.assertEqual(errors, [])

    def test_crop_covers_the_part(self):
        for sketch, crops in self.crops.items():
            for part, crop in crops.items():
                box = self.geo[sketch]["parts"][part]["bbox"]
                over = li._inside(box, crop)
                self.assertEqual(max(over), 0, f"{sketch}.{part} 的缺省框 {crop} 没盖住 {box}")

    def test_crop_is_neither_tiny_nor_a_slit(self):
        for sketch, crops in self.crops.items():
            fit = self.geo[sketch]["fit"]
            for part, crop in crops.items():
                self.assertGreaterEqual(min(crop[2], crop[3]), 15.9, f"{sketch}.{part} 框太小 {crop}")
                self.assertLessEqual(crop[2] / crop[3], 4.5, f"{sketch}.{part} 长宽比过大 {crop}")
                self.assertGreaterEqual(min(crop[2], crop[3]), 0.349 * min(fit[2], fit[3]) - 0.1, f"{sketch}.{part}")

    def test_parts_with_their_own_fit_are_not_in_the_generated_table(self):
        # 一个部位只能有一个框的来源：手写优先，生成表里就不该再出现它的名字（两份数会漂）。
        for sketch, sk in self.geo.items():
            for part, info in sk["parts"].items():
                if info.get("fit"):
                    self.assertNotIn(part, self.crops.get(sketch, {}), f"{sketch}.{part} 手写了 fit 却还在 crops.ts 里")

    def test_every_part_is_selectable(self):
        # 能被 parts:[…] 单独点名的部位，必须有一个可用的框（手写或生成），否则单部位特写就是整张图。
        lacking = [f"{s}.{p}" for s, sk in self.geo.items() for p, i in sk["parts"].items()
                   if not i.get("fit") and p not in self.crops.get(s, {})]
        self.assertEqual(lacking, [])


class GeneratedArtifactTest(unittest.TestCase):
    def test_crops_file_is_in_sync(self):
        self.assertTrue(CROPS.is_file(), "缺少 src/linework/crops.ts")
        self.assertEqual(CROPS.read_text(encoding="utf-8"), li.render_part_crops(li.part_crops()),
                         "crops.ts 与 library.ts 不同步：跑 python scripts/linework_index.py --write-crops")

    def test_engine_prefers_the_handwritten_fit(self):
        src = SKETCH.read_text(encoding="utf-8")
        self.assertIn("import {PART_CROP} from './crops';", src)
        self.assertIn("only?.fit ?? (onlyName ? cropFor(onlyName) : undefined) ?? fitOf(def)", src)

    def test_path_only_parts_get_their_anchor_from_the_crop(self):
        """这一层不做路径解析，全 path 的部位以前一律落在 [50,50]（引线指向画面正中）。"""
        src = SKETCH.read_text(encoding="utf-8")
        self.assertIn("partAnchor(def, id, cropFor(id))", src)
        self.assertIn("return crop ? [crop[0] + crop[2] / 2, crop[1] + crop[3] / 2] : [50, 50];", src)


class NegativeGeometryTest(unittest.TestCase):
    def _with_library(self, mutate) -> list[str]:
        text = LIB.read_text(encoding="utf-8")
        broken = mutate(text)
        assert broken != text, "夹具没改到东西"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "library.ts"
            p.write_text(broken, encoding="utf-8")
            errors, _ = li.geometry_problems(p)
        return errors

    def test_shrinking_a_fit_is_an_error(self):
        errors = self._with_library(lambda t: t.replace("fit: [62, 0, 38, 34]", "fit: [70, 6, 18, 18]"))
        self.assertTrue(any("chiplog.hull" in e and "没盖住" in e for e in errors), errors)

    def test_shrinking_the_whole_drawing_fit_is_an_error(self):
        errors = self._with_library(lambda t: t.replace("    fit: [33, 1, 34, 96],", "    fit: [40, 20, 10, 10],"))
        self.assertTrue(any(e.startswith("rocket:") and "没盖住" in e for e in errors), errors)

    def test_anchor_outside_the_crop_is_an_error(self):
        errors = self._with_library(lambda t: t.replace("anchor: [86, 14], fit: [62, 0, 38, 34]", "anchor: [20, 90], fit: [62, 0, 38, 34]"))
        self.assertTrue(any("chiplog.hull" in e and "引线落点" in e for e in errors), errors)

    def test_nonsense_fit_is_an_error(self):
        errors = self._with_library(lambda t: t.replace("fit: [62, 0, 38, 34]", "fit: [62, 0, 0, 34]"))
        self.assertTrue(any("宽高必须为正" in e for e in errors), errors)

    def test_parse_failure_is_loud(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "library.ts"
            p.write_text("export const NOTHING = {};", encoding="utf-8")
            with self.assertRaises(li.LibraryParseError):
                li.parse_geometry(p.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
