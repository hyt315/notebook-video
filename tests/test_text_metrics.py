#!/usr/bin/env python3
"""P2-17 · 文字测量真源：长标点 / 全角括号 / 数字单位 / 中英混排 / 两行标题。

旧版用字符类系数（全角 1.0 / ASCII 0.56）加 LEAN=1.06 补标点，实测补不准：
「——」估 0.56×2=1.12em，实为 2.0em；「“引号”」估 1.12em，实为 0.7em。
这批夹具钉住「不再依赖逐案例补偿」——量宽只问真字体，不问系数。
"""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


tm = load("tm", "scripts/text_metrics.py")
cs = load("cs", "scripts/compose-story.py")

# 真字体（LXGW WenKai Lite Regular）的实测 em 宽度。手抄自 hmtx，防解析器漂了没人发现。
REAL = {
    "今": 1.0, "天": 1.0,
    "「": 1.0, "」": 1.0,
    "—": 1.0, "…": 1.0,
    "（": 1.0, "）": 1.0,
    "“": 0.35, "”": 0.35,
    "–": 0.5,
    # ASCII 用实测（LXGW WenKai Lite Regular 的 hmtx，upem=1000）
    "a": 0.575, "b": 0.573, "H": 0.7, "e": 0.543, "l": 0.263, "o": 0.562,
    "A": 0.69, "P": 0.618, "I": 0.304,
    " ": 0.35,   # LXGW 的空格不是 0.25
}


class RealMetricsTest(unittest.TestCase):
    def test_cjk_is_one_em(self):
        for ch in "今天哈希表":
            self.assertAlmostEqual(tm.advance_em(ch), 1.0, places=3, msg=ch)

    def test_long_punctuation_is_full_width(self):
        """「—」「…」在字符类里是 0.56（U+2014/U+2026 不在全角区），真字体是 1.0em。"""
        for ch in "—…†‡":
            self.assertAlmostEqual(tm.advance_em(ch), 1.0, places=3,
                                   msg=f"{ch!r} 必须是全宽，否则长标点句会被估窄 44%")

    def test_curly_quotes_are_narrow_in_kai(self):
        """弯曲引号在霞鹜文楷里是 0.35em，不是 0.56——估宽会浪费 60%。"""
        for ch in "“”‘’":
            self.assertAlmostEqual(tm.advance_em(ch), 0.35, places=2, msg=ch)

    def test_fullwidth_brackets_are_full_width(self):
        for ch in "（）【】《》〔〕":
            self.assertAlmostEqual(tm.advance_em(ch), 1.0, places=3, msg=ch)

    def test_ascii_matches_font_not_the_056_constant(self):
        for ch, w in REAL.items():
            self.assertAlmostEqual(tm.advance_em(ch), w, places=2, msg=f"{ch!r} 期望 {w}")

    def test_known_strings_have_exact_width(self):
        cases = [
            ("今天", 2.0), ("——", 2.0), ("……", 2.0),
            ("（注）", 3.0), ("“ab”", 0.35 + 0.575 + 0.573 + 0.35),
            ("Hello", 0.7 + 0.543 + 0.263 + 0.263 + 0.562),

        ]
        for s, em in cases:
            self.assertAlmostEqual(tm.text_width(s, 100) / 100, em, places=2, msg=s)

    def test_serif_differs_from_kai_on_quotes(self):
        """同一批标点在 NotoSerifSC 里是全宽、在 Kai 里是 0.35——不能共用一张表。"""
        kai = tm.get("kai")
        serif = tm.get("serif")
        self.assertAlmostEqual(kai.advance_em("“"), 0.35, places=2)
        self.assertAlmostEqual(serif.advance_em("“"), 1.0, places=2)


class NoCaseCompensationTest(unittest.TestCase):
    """验收条款「不再依赖逐案例补偿」：把 LEAN 那类乘法从代码里删干净。"""

    def test_lean_multiplier_is_gone(self):
        # P2-24 起文字层在 story_text.py；两个文件都扫，防止有人把它加回任一处。
        src = "\n".join((ROOT / "scripts" / f).read_text(encoding="utf-8")
                        for f in ("compose-story.py", "story_text.py"))
        self.assertNotIn("LEAN = 1.06", src)
        self.assertNotIn("LEAN =", src.replace("SAFE_LH", "").replace("safe_lh", ""))
        # 注释里提它作为历史可以，但不能再有乘法
        for line in src.splitlines():
            if line.strip().startswith("#"):
                continue
            self.assertNotIn("* LEAN", line)
            self.assertNotIn("*LEAN", line)

    def test_width_needs_no_safety_factor(self):
        """「——……」这类旧版必须乘 LEAN 才不切字的句子，现在 1.0 系数即准。"""
        s = "「你说的对」——但是（注意）这里……"
        self.assertAlmostEqual(cs.text_w(s, 100) / 100, s.count("「") + s.count("」")
                               + s.count("—") + s.count("但") + s.count("是")
                               + s.count("（") + s.count("注") + s.count("意")
                               + s.count("）") + s.count("这") + s.count("里")
                               + s.count("…") + s.count("你") + s.count("说")
                               + s.count("的") + s.count("对"), places=2)

    def test_ascii_no_longer_overestimated(self):
        self.assertLess(cs.text_w("Hello", 100), 250, "真值约 233，旧估算是 280")


class SafeLhTest(unittest.TestCase):
    def test_floor_matches_renderer(self):
        self.assertEqual(cs.SAFE_LH, 1.42)
        self.assertEqual(cs.safe_lh(1.2), 1.42)
        self.assertEqual(cs.safe_lh(1.42), 1.42)
        self.assertEqual(cs.safe_lh(1.5), 1.5)

    def test_fit_text_height_uses_floor(self):
        """传 lh=1.3 也必须按 1.42 报高——渲染端就是这么画的。"""
        class P:
            def err(self, m): pass
            def fix(self, m): pass
            def hint(self, m): pass

        ls, s, w, h = cs.fit_text(P(), "t", "哈希", 104, 800, 2, lh=1.3)
        self.assertAlmostEqual(h, 104 * 1.42, places=2)

    def test_fit_text_respects_larger_lh(self):
        class P:
            def err(self, m): pass
            def fix(self, m): pass
            def hint(self, m): pass

        _, _, _, h = cs.fit_text(P(), "t", "哈希", 104, 800, 2, lh=1.45)
        self.assertAlmostEqual(h, 104 * 1.45, places=2)


class WrapHardCasesTest(unittest.TestCase):
    """五类硬骨头在折行下都不断数字/单位、不丢标点。"""

    def test_long_punctuation_wraps_without_splitting_dash(self):
        for maxw in range(200, 800, 40):
            lines = cs.wrap("这是一个很长的句子——中间有破折号——后面还有", 40, maxw)
            for a, b in zip(lines, lines[1:]):
                self.assertFalse(a.endswith("—") and b.startswith("—"),
                                 f"破折号被拆成两行：{lines} @maxw={maxw}")

    def test_fullwidth_brackets_stay_closed(self):
        lines = cs.wrap("结论（注意：不是全部）成立", 40, 280)
        joined = "".join(lines)
        self.assertEqual(joined.count("（"), joined.count("）"))
        self.assertIn("（", joined)

    def test_number_and_unit_stay_together(self):
        for maxw in range(120, 460, 20):
            lines = cs.wrap("木板长 47 呎 3 吋一个", 40, maxw)
            for a, b in zip(lines, lines[1:]):
                a = a.rstrip()
                self.assertFalse(a and a[-1].isdigit() and b[:1] in "吋呎秒里米度节",
                                 f"数字与单位拆开：{lines} @maxw={maxw}")

    def test_mixed_cjk_latin_wraps_on_word_boundary(self):
        lines = cs.wrap("hash 表的时间复杂度是 O(1) 量级", 40, 200)
        for line in lines:
            self.assertNotIn("ha sh", line)
        self.assertEqual("".join(lines).replace(" ", ""),
                         "hash表的时间复杂度是O(1)量级")

    def test_two_line_title_gets_two_lines_not_three(self):
        class P:
            def __init__(self): self.errs = []
            def err(self, m): self.errs.append(m)
            def fix(self, m): pass
            def hint(self, m): pass

        p = P()
        ls, size, w, h = cs.fit_text(
            p, "t", "这是一个需要折成两行的讲解标题文字示例",
            56, 720, 2)
        self.assertLessEqual(len(ls), 2, ls)
        self.assertFalse(p.errs, p.errs)
        self.assertAlmostEqual(h, len(ls) * size * 1.42, places=1)

    def test_latin_width_is_per_glyph_not_a_constant(self):
        """旧估算给每个 ASCII 一律 0.56em。真值 l=0.263 / H=0.7 / 空格=0.35，逐字不同。"""
        for s, em in (("Hello", 2.331), ("Hello World", 5.391), ("ab", 1.148),
                      ("lll", 0.789)):
            real = cs.text_w(s, 100) / 100
            self.assertAlmostEqual(real, em, places=2, msg=s)
        # 窄字母串必须比常数估算窄（旧版会浪费一倍空间给 lll）
        self.assertLess(cs.text_w("lll", 100) / 100, 0.56 * 3)
        # 宽字母串可以比常数估算宽——所以才不能用一个系数补
        self.assertGreater(cs.text_w("ab", 100) / 100, 0.56 * 2)


class CacheAndFallbackTest(unittest.TestCase):
    def test_cache_is_small_enough_to_commit(self):
        data = json.loads((ROOT / "assets" / "fonts" / "metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(data["version"], 1)
        self.assertIn("kai", data["fonts"])
        n = sum(len(v["advances"]) for v in data["fonts"].values())
        self.assertGreater(n, 1000, "缓存码点太少，量宽会退回估算")
        self.assertLess(n, 20000, "缓存不该逐个存两万汉字（默认全宽即可）")

    def test_fallback_punct_table_covers_the_dangerous_ones(self):
        empty = tm.FontMetrics(1000, {}, fallback=True)
        self.assertAlmostEqual(empty.advance_em("—"), 1.0)
        self.assertAlmostEqual(empty.advance_em("…"), 1.0)
        self.assertAlmostEqual(empty.advance_em("“"), 0.35)
        self.assertAlmostEqual(empty.advance_em("A"), 0.56)
        self.assertAlmostEqual(empty.advance_em("汉"), 1.0)

    def test_parser_sees_both_cmap_formats(self):
        """TTF（kai，cmap4）与 OTF（serif）都要能解析。

        字体按需下载、不入库：干净克隆与 CI 上没有这两个文件，只能验缓存——
        那不是「解析器看得懂两种 cmap」，所以缺文件时跳过，不假装通过。
        """
        for role, name in (("kai", "LXGWWenKaiLite-Regular.ttf"), ("serif", "NotoSerifSC-Bold.otf")):
            if not (ROOT / "assets" / "fonts" / name).exists():
                self.skipTest(f"缺 {name}（按需下载）：解析器路径无从验证")
            m = tm.get(role)
            self.assertFalse(m.fallback, role)
            self.assertGreater(len(m.advances), 1000, role)


if __name__ == "__main__":
    unittest.main()
