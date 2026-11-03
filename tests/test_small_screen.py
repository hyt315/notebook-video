from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_STORY = ROOT / "tests" / "fixtures" / "compose-golden" / "text__src_story.ts"


def load_gate():
    spec = importlib.util.spec_from_file_location("vp", ROOT / "scripts" / "validate-presentation.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


VP = load_gate()


def story_table() -> dict:
    ts = GOLDEN_STORY.read_text(encoding="utf-8")
    start = ts.index("{", ts.index("export const STORY"))
    return json.loads(ts[start:ts.rindex("}") + 1])


def make_project(story: dict | None = None, muted: str = "#8a8a8a") -> Path:
    """临时工程：src/story.ts（结构化 role/size）+ 一套 muted 对比度可控的主题。"""
    td = tempfile.mkdtemp(prefix="nv-small-screen-")
    proj = Path(td)
    (proj / "src" / "theme").mkdir(parents=True)
    (proj / "manifests").mkdir()
    base = GOLDEN_STORY.read_text(encoding="utf-8")
    if story is not None:
        start = base.index("{", base.index("export const STORY"))
        base = base[:start] + json.dumps(story, ensure_ascii=False) + base[base.rindex("}") + 1:]
    (proj / "src" / "story.ts").write_text(base, encoding="utf-8")
    (proj / "src" / "theme" / "flat.tsx").write_text(
        "const palette = {ink:'#222222', muted:'%s', white:'#ffffff', "
        "paper:'#ffffff', paperWarm:'#faf5ee', paperBase:'#faf7f2'};" % muted, encoding="utf-8")
    return proj


class CoreSentenceFloorTest(unittest.TestCase):
    """P2-21 验收①：360px 宽缩图仍能读核心句。

    核心句 = role=display/hero（每镜的主信息）。设计 1920 宽缩到 360px 是 5.33 倍缩，
    中文可读下限 12 CSS px → 设计字号必须 ≥64px。低于它就是「手机上读不清」。
    """

    def test_existing_story_passes(self):
        """golden 的核心句是 64/104/230 —— 全部 ≥64，不得被误拦。"""
        p0, _ = VP.check_small_screen(make_project())
        self.assertEqual([x for x in p0 if "核心句" in x["issue"]], [], p0)

    def test_display_below_floor_is_p0(self):
        d = story_table()
        for e in d["S1"]["elements"]:
            if e.get("role") == "display":
                e["size"] = 46
        p0, _ = VP.check_small_screen(make_project(d))
        hits = [x for x in p0 if "核心句" in x["issue"]]
        self.assertEqual(len(hits), 1, p0)
        self.assertIn("46", hits[0]["issue"])
        self.assertIn("64", hits[0]["issue"])
        self.assertIn("8.6px", hits[0]["issue"])   # 46 * 360/1920 —— 报错要说清缩图后多大

    def test_hero_below_floor_is_p0(self):
        d = story_table()
        for e in d["S4"]["elements"]:
            if e.get("role") == "hero":
                e["size"] = 60
        p0, _ = VP.check_small_screen(make_project(d))
        self.assertTrue(any("核心句" in x["issue"] and "60" in x["issue"] for x in p0), p0)

    def test_muted_can_be_small(self):
        """辅助文字（role=muted）不受核心句地板约束——它本来就不指望在缩图上读。"""
        d = story_table()
        for e in d["S1"]["elements"]:
            if e.get("role") == "muted":
                e["size"] = 24
        p0, _ = VP.check_small_screen(make_project(d))
        self.assertEqual([x for x in p0 if "核心句" in x["issue"]], [], p0)


class ScreenReadBudgetTest(unittest.TestCase):
    """P2-21 验收②（阅读预算那半）：一屏里观众要读的画面文字总量。

    只看桌面原图时 30 加权字「不挤」，缩到 360px 就是「读不完就得定格」。
    预算 40（实测示例 8–30，留 33% 余量）。
    """

    def test_existing_story_within_budget(self):
        _, p1 = VP.check_small_screen(make_project())
        self.assertEqual([x for x in p1 if "预算" in x["issue"]], [], p1)

    def test_over_budget_is_flagged(self):
        d = story_table()
        for e in d["S2"]["elements"]:
            e["text"] = (e.get("text") or "") + "补充说明文字若干让总量超过预算" * 3
        _, p1 = VP.check_small_screen(make_project(d))
        hits = [x for x in p1 if "预算" in x["issue"]]
        self.assertEqual(len(hits), 1, p1)
        self.assertIn("40", hits[0]["issue"])
        self.assertIn("拆镜", hits[0]["issue"])   # 要给改法

    def test_lines_are_counted_too(self):
        """有 lines 时按 lines 量（折行后的实际在屏文字），不是只量 text 字段。"""
        d = story_table()
        for e in d["S1"]["elements"]:
            if e.get("role") == "display":
                e["lines"] = ["这一行是折行后的文字，" * 6]
                e["text"] = ""
        _, p1 = VP.check_small_screen(make_project(d))
        self.assertTrue(any("预算" in x["issue"] for x in p1), p1)


class SmallScreenContrastTest(unittest.TestCase):
    """P2-21 验收②（对比度那半）：「大字 3:1」的豁免按缩图换算后不成立。

    设计 46px 缩到 360px 是 8.6px（小字），WCAG 的「大字」门槛是 24px normal——
    也就是说缩图语境下几乎没有大字，muted 那类 3:1 配对要按 4.5:1 重新看。
    """

    def test_muted_between_3_and_45_is_flagged(self):
        # #8a8a8a on #ffffff ≈ 3.5:1 —— 桌面按大字可接受，小屏不够
        _, p1 = VP.check_small_screen(make_project(muted="#8a8a8a"))
        hits = [x for x in p1 if "muted" in x["issue"] and "小屏" in x["issue"]]
        self.assertEqual(len(hits), 1, p1)
        self.assertIn("4.5", hits[0]["issue"])

    def test_muted_at_45_or_above_is_silent(self):
        _, p1 = VP.check_small_screen(make_project(muted="#6b6b6b"))   # ≈5.3:1
        self.assertEqual([x for x in p1 if "muted" in x["issue"]], [], p1)

    def test_no_story_file_skips_silently(self):
        """没 compose 产物时静默跳过（与 check_readability 同口径），不冒充通过。"""
        proj = Path(tempfile.mkdtemp(prefix="nv-ss-empty-"))
        (proj / "manifests").mkdir()
        (proj / "src").mkdir()
        p0, p1 = VP.check_small_screen(proj)
        self.assertEqual((p0, p1), ([], []))


if __name__ == "__main__":
    unittest.main()
