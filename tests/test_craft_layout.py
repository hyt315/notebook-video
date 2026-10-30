#!/usr/bin/env python3
"""3.3.0 component fixes: ArchivePhoto hierarchy constants, LoupeMedia credit avoidance, FillGate per-skin + one-line summary.

Static consistency checks over the TSX (no browser): the numbers the docs promise are the numbers the code uses."""
from __future__ import annotations

import math
import random
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "lecture-template" / "src"
MEDIA = (SRC / "craft" / "media.tsx").read_text(encoding="utf-8")
LENS = (SRC / "craft" / "lens.tsx").read_text(encoding="utf-8")
FILL = (SRC / "fill-gate.tsx").read_text(encoding="utf-8")
CLI = (ROOT / "scripts" / "notebook-video.mjs").read_text(encoding="utf-8")


def const(src: str, name: str) -> float:
    m = re.search(rf"export const {name}\s*=\s*([0-9.]+)", src)
    assert m, name
    return float(m.group(1))


def archive_mount(dw: float, dh: float, mount: float, frac: float) -> int:
    """Python mirror of archiveMount() in media.tsx."""
    k = 1 / frac - 1
    mmax = (-2 * (dw + dh) + math.sqrt(4 * (dw + dh) ** 2 + 16 * k * dw * dh)) / 8
    return max(0, min(int(mount), math.floor(mmax)))


class ArchivePhotoTest(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(const(MEDIA, "ARCHIVE_MIN_IMAGE_FRAC"), 0.7)
        self.assertEqual(const(MEDIA, "ARCHIVE_LABEL_MAX_FRAC"), 0.12)

    def test_constants_are_wired(self):
        self.assertRegex(MEDIA, r"1 / ARCHIVE_MIN_IMAGE_FRAC - 1")
        self.assertRegex(MEDIA, r"dh \* ARCHIVE_LABEL_MAX_FRAC")
        # the rendered card uses the computed padding and label sizes, not literals
        self.assertIn("padding: L.mount", MEDIA)
        self.assertIn("fontSize: L.labelFont", MEDIA)
        self.assertIn("fontSize: L.catalogueFont", MEDIA)
        self.assertNotRegex(MEDIA, r"fontWeight: 700, fontSize: 30, lineHeight: 1.2, color: C.ink, whiteSpace: 'nowrap'\}\}>\s*\{catalogue")

    def test_credit_font_not_reduced(self):
        # 3.3.0 评审 P1-10：署名从 20 提到 22（CC BY 要求可读），这条断言改为「不得低于 22」
        self.assertRegex(MEDIA, r"CREDIT_FONT = 2[2-9]")
        self.assertIn("fontSize: L.creditFont", MEDIA)

    def test_mount_formula_keeps_image_at_least_70_percent(self):
        rnd = random.Random(7)
        for _ in range(2000):
            dw, dh = rnd.uniform(40, 1600), rnd.uniform(40, 1000)
            m = archive_mount(dw, dh, 22, 0.7)
            self.assertGreaterEqual(dw * dh / ((dw + 2 * m) * (dh + 2 * m)), 0.7 - 1e-9, (dw, dh, m))
            self.assertLessEqual(m, 22)

    def test_label_font_cap(self):
        m = re.search(r"archiveLabelFont = \(dh: number\) => Math\.max\((\d+), Math\.min\(LABEL_FONT_MAX, Math\.floor\(dh \* ARCHIVE_LABEL_MAX_FRAC\)\)\)", MEDIA)
        self.assertIsNotNone(m)
        for dh in (100, 150, 250, 400):
            font = max(int(m.group(1)), min(30, math.floor(dh * 0.12)))
            if dh * 0.12 >= 12:
                self.assertLessEqual(font, dh * 0.12)


class LoupeMediaTest(unittest.TestCase):
    def test_handle_direction_is_chosen_from_the_credit_box(self):
        self.assertIn("export const pickHandleAngle", LENS)
        self.assertIn("handleAngle?: number", LENS)
        self.assertRegex(MEDIA, r"pickHandleAngle\(L\.x, L\.y, r, \[slip\]\)")
        self.assertIn("handleAngle={handleAngle}", MEDIA)

    def test_handle_geometry_mirror(self):
        """Mirror of loupeHandleBox/pickHandleAngle: a credit slip under the lens on the right sends the handle elsewhere."""
        def box(cx, cy, r, ang):
            a = math.radians(ang)
            c, s = math.cos(a), math.sin(a)
            sx, sy = cx + 0.96 * r * c, cy + 0.96 * r * s
            ex, ey = sx + 0.95 * r * c, sy + 0.95 * r * s
            pad = 17 + 10
            return (min(sx, ex) - pad, min(sy, ey) - pad, max(sx, ex) + pad, max(sy, ey) + pad)

        def hit(b, x):
            return max(0, min(b[2], x[2] + 6) - max(b[0], x[0] - 6)) * max(0, min(b[3], x[3] + 6) - max(b[1], x[1] - 6))

        cx, cy, r = 600, 400, 220
        slip = (560, 640, 1000, 720)  # credit line below-right of the lens
        self.assertGreater(hit(box(cx, cy, r, 45), slip), 0)  # the old fixed 45° handle covers it
        chosen = next(a for a in (45, 135, -45, -135, 90, 0, 180, -90) if hit(box(cx, cy, r, a), slip) == 0)
        self.assertNotEqual(chosen, 45)


class FillGateTest(unittest.TestCase):
    def test_handcraft_skins_skip_bottom_quarter(self):
        m = re.search(r"FILL_GATE_SKIP_SKINS = \[([^\]]*)\]", FILL)
        self.assertIsNotNone(m)
        self.assertEqual(sorted(re.findall(r"'(\w+)'", m.group(1))), ["archive", "journal", "papercut"])
        self.assertIn("THEME.id", FILL)
        # 3.8.0：手作皮肤只跳过「下 1/4」这一条判据，横向覆盖率照量。
        # 旧契约是整条短路（`!SKIN_SKIPPED &&`），结果是 journal 片子的横向空洞从来没被量过。
        self.assertIn("const checkFloor = !SKIN_SKIPPED;", FILL)
        self.assertIn("if (checkFloor && !pass)", FILL)
        self.assertIn("coverageSeen", FILL)
        self.assertIn("COVER_COLS", FILL)
        self.assertNotIn("!SKIN_SKIPPED &&", FILL)

    def test_one_line_per_shot_and_summary(self):
        self.assertIn("[FillGate] underfilled ${sid}", FILL)
        self.assertIn("warned.has(sid)", FILL)
        self.assertNotIn("下 1/4 已填", FILL)  # the periodic "all good" lines are gone
        self.assertIn("bottom-quarter underfilled", CLI)
        self.assertIn("runRemotionFiltered(nodeArgs, project)", CLI)



CANVAS = (SRC / "theme" / "canvas.ts").read_text(encoding="utf-8")


def canvas_num(key: str) -> float:
    m = re.search(rf"'16:9':\s*{{[^}}]*\b{key}:\s*([0-9.]+)", CANVAS)
    assert m, key
    return float(m.group(1))


def archive_safe_h(y, h, safe_bottom):
    """Python mirror of archiveSafeH() in media.tsx."""
    if y is None:
        return h
    return max(round(h * 0.5), min(h, math.floor(safe_bottom - y)))


class CreditAvoidsCaptionBand(unittest.TestCase):
    """3.3.0: an ArchivePhoto credit slip must stay out of the subtitle band (cell-v3 OCR read Schem. XI into cue 9)."""
    def setUp(self):
        self.design_h, self.sub_b, self.sub_h = canvas_num("designH"), canvas_num("subBottom"), canvas_num("subH")
        self.clear = const(MEDIA, "CAPTION_CLEAR")
        self.safe = self.design_h - self.sub_b - self.sub_h - self.clear

    def test_safe_line_derives_from_canvas(self):
        self.assertIn("CANVAS.designH - CANVAS.subBottom - CANVAS.subH - CAPTION_CLEAR", MEDIA)
        self.assertEqual(self.safe, 874)

    def test_safe_line_survives_a_signature_push(self):
        # 招牌镜头推 12.5%（以画面中心）：安全线推后仍在字幕框顶之上
        box_top = self.design_h - self.sub_b - self.sub_h
        cy = self.design_h / 2
        self.assertLess(cy + (self.safe - cy) * 1.125, box_top)

    def test_layout_receives_y_at_every_call_site(self):
        self.assertIn("label: ArchiveLabel = 'auto', y?: number)", MEDIA)
        self.assertIn("const h = archiveSafeH(y, frameH);", MEDIA)
        calls = re.findall(r"archiveLayout\(id, w, h, mount, [^;]*\);", MEDIA)
        self.assertEqual(len(calls), 2, calls)          # ArchivePhoto + LoupeMedia
        for c in calls:
            self.assertTrue(c.endswith("label, y);"), c)

    def test_safe_height_mirror(self):
        rnd = random.Random(7)
        for _ in range(2000):
            y, h = rnd.uniform(0, 900), rnd.uniform(200, 1000)
            hh = archive_safe_h(y, h, self.safe)
            self.assertLessEqual(hh, h)
            self.assertGreaterEqual(hh, round(h * 0.5))
            if self.safe - y >= h * 0.5:
                self.assertLessEqual(y + hh, self.safe + 1e-9)   # 底边不进字幕带
        self.assertEqual(archive_safe_h(None, 640, self.safe), 640)
        self.assertEqual(archive_safe_h(100, 800, self.safe), 774)  # cell 的 PLATE（y=100, h=800）


if __name__ == "__main__":
    unittest.main()
