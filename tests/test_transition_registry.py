from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "assets" / "lecture-template" / "src" / "transitions" / "meta.ts"
PAGEFOLD = ROOT / "assets" / "lecture-template" / "src" / "transitions" / "pagefold.tsx"
CINEMA = ROOT / "assets" / "lecture-template" / "src" / "cinema.tsx"
FX = ROOT / "assets" / "lecture-template" / "src" / "fx.tsx"
SFX = ROOT / "assets" / "lecture-template" / "src" / "sfx.ts"
INDEX = ROOT / "assets" / "lecture-template" / "src" / "index.tsx"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


class RegistryIsSingleSourceTest(unittest.TestCase):
    """P2-23 验收①：新增一种转场只需一个实现模块和一处注册。

    以前时长 / 方向 / 是否翻页 / 无 GPU 退回散在四处（cinema / fx / sfx / index），
    新增一种转场要改三四个文件，漏一处的症状是「渲出来是对的、音效不对」。
    现在注册表 TRANSITION_META 是唯一真源，其余都从它读。
    """

    def test_registry_declares_every_transition(self):
        meta = read(META)
        for kind in ("whip", "zoom", "fade", "hard", "slide", "drop",
                     "pageturn", "peel", "pageflip"):
            self.assertIn(f"{kind}:", meta.replace("'", "").replace('"', ""), f"注册表缺 {kind}")

    def test_cinema_reads_registry_not_hardcoded(self):
        src = read(CINEMA)
        self.assertIn("transitionFramesOf(kind)", src)
        # 不再硬编码 pageflip 的 22
        self.assertNotIn("pageflip' ? 22", src)
        self.assertNotIn(": 22 :", src)

    def test_sfx_reads_registry_not_a_second_set(self):
        src = read(SFX)
        self.assertIn("isPageTurnKind", src)
        self.assertNotIn("PAGE_TURN_TRANSITIONS", src, "不该再有第二个翻页 Set")

    def test_fx_re_exports_from_registry(self):
        src = read(FX)
        self.assertIn("from './transitions/meta'", src)
        self.assertIn("export {CURL_FRAMES, PAGETURN_FOLD_DIRECTION, isCurl, FX_FALLBACK}", src)
        # 不再有本地的字面量定义
        self.assertNotIn("export const PAGETURN_FOLD_DIRECTION = -78", src)
        self.assertNotIn("export const CURL_FRAMES = 22", src)

    def test_pagefold_is_out_of_index(self):
        """PageFold 与折线几何不再住在合成根文件里。"""
        idx = read(INDEX)
        self.assertIn("from './transitions/pagefold'", idx)
        self.assertNotIn("const PageFold =", idx)
        self.assertNotIn("const FOLD_K =", idx)
        pf = read(PAGEFOLD)
        self.assertIn("export const PageFold", pf)
        self.assertIn("export const FOLD_K", pf)


class FrameParityTest(unittest.TestCase):
    """P2-23 验收③：现有帧级对照一致（零行为变化）。

    改注册表前的实际时长：pageturn / peel / pageflip = 22 帧，其余 = CINEMA.transition = 14 帧。
    抽取后必须一模一样——不一致的症状是卷页窗口盖不住整段翻页，或转场提前结束。
    """

    def test_transition_frames_match_history(self):
        meta = read(META)
        # 翻页三兄弟 22 帧
        for kind in ("pageturn", "peel", "pageflip"):
            m = re.search(rf"{kind}:\s*\{{[^}}]*frames:\s*(\w+)", meta)
            self.assertIsNotNone(m, f"注册表没找到 {kind}")
            self.assertIn(m.group(1), ("CURL_FRAMES", "22"), f"{kind} 的帧数应是 22（或同源的 CURL_FRAMES）")
        # 其余 14 帧（DEFAULT_TRANSITION_FRAMES）
        for kind in ("whip", "zoom", "fade", "hard", "slide", "drop"):
            m = re.search(rf"{kind}:\s*\{{[^}}]*frames:\s*(\w+)", meta)
            self.assertIsNotNone(m, f"注册表没找到 {kind}")
            self.assertIn(m.group(1), ("DEFAULT_TRANSITION_FRAMES", "14"), f"{kind} 的帧数应是 14")

    def test_curl_frames_cross_checked_with_transition_plan(self):
        """卷页帧数必须与转场计划同值——窗口按它算，渲染按它画。"""
        a = re.search(r"export const CURL_FRAMES\s*=\s*(\d+)", read(META)).group(1)
        b = re.search(r"export const CURL_FRAMES\s*=\s*(\d+)",
                      read(ROOT / "scripts" / "transition-plan.mjs")).group(1)
        self.assertEqual(a, b)

    def test_fold_direction_single_source(self):
        """折线方向只有一个定义：CSS 折痕（pagefold）与 GPU 卷页（fx 的 curlParams）共用。"""
        meta = read(META)
        self.assertIn("export const PAGETURN_FOLD_DIRECTION = -78", meta)
        pf = read(PAGEFOLD)
        self.assertIn("from './meta'", pf)
        self.assertIn("PAGETURN_FOLD_DIRECTION", pf)
        self.assertNotIn("= -78", pf, "pagefold 不该再写一次角度")
        fx = read(FX)
        self.assertIn("foldDirection: PAGETURN_FOLD_DIRECTION", fx)


class PageTurnParityTest(unittest.TestCase):
    """纸声跟着翻页走：判定口径与历史一致（auto / pageturn / peel / pageflip 算翻页）。"""

    def test_page_turn_kinds_unchanged(self):
        meta = read(META)
        self.assertIn("k === 'auto'", meta, "auto 由皮肤缺省决定，缺省就是翻页")
        for kind in ("pageturn", "peel", "pageflip"):
            m = re.search(rf"{kind}:\s*\{{[^}}]*pageTurn:\s*(\w+)", meta)
            self.assertEqual(m.group(1), "true", f"{kind} 应是翻页（纸声跟着它）")
        for kind in ("whip", "zoom", "fade", "hard", "slide", "drop"):
            m = re.search(rf"{kind}:\s*\{{[^}}]*pageTurn:\s*(\w+)", meta)
            self.assertEqual(m.group(1), "false", f"{kind} 不是翻页（不该有纸声）")

    def test_fallback_still_turns_a_page(self):
        """无 GPU 退回**不等于不翻页**：pageturn→pageflip（折痕翻页），peel→drop。"""
        meta = read(META)
        self.assertIn("pageturn: 'pageflip'", meta.replace("fallback: ", "pageturn: "))
        self.assertIn("peel: 'drop'", meta.replace("fallback: ", "peel: "))


if __name__ == "__main__":
    unittest.main()
