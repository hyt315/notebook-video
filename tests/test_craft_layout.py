#!/usr/bin/env python3
"""3.7.0 component fixes: ArchivePhoto hierarchy constants, LoupeMedia credit avoidance, FillGate per-skin + one-line summary.

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
        self.assertRegex(MEDIA, r"CREDIT_FONT = 20")
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
        self.assertIn("!SKIN_SKIPPED &&", FILL)

    def test_one_line_per_shot_and_summary(self):
        self.assertIn("[FillGate] underfilled ${sid}", FILL)
        self.assertIn("warned.has(sid)", FILL)
        self.assertNotIn("下 1/4 已填", FILL)  # the periodic "all good" lines are gone
        self.assertIn("bottom-quarter underfilled", CLI)
        self.assertIn("runRemotionFiltered(nodeArgs, project)", CLI)


if __name__ == "__main__":
    unittest.main()
