#!/usr/bin/env python3
"""P2-19：区分「有意复现主题物」与「无意重复画面」。

跨镜复现不该一律禁止——回忆、前后对照、结论回扣都需要再现同一个主题物。
但「同图 + 同局部 + 同动作」连续出现两次、又没声明意图，观众读到的就是「这段我看过」。

story 层的意图标记（写在 shot 上或 content 上都行）：
  recallOf : 回扣先前那张图（回忆 / 结论回扣）
  variantOf: 同一主题物的另一态（前后对照）

门禁只拦**无意**的完全重复；构图（parts）、动作（acts）、信息量（label）三者至少一项有变化即放行。
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_cs():
    spec = importlib.util.spec_from_file_location("cs_rep", ROOT / "scripts" / "compose-story.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


cs = load_cs()
FIXTURE = ROOT / "examples" / "recipes" / "jie-freeform.story.json"


class P:
    def __init__(self):
        self.errors: list[str] = []
        self.hints: list[str] = []
        self.fixes: list[str] = []

    def err(self, m): self.errors.append(m)
    def hint(self, m): self.hints.append(m)
    def fix(self, m): self.fixes.append(m)


def mk(sid: str, ink: dict | None = None, **kw) -> dict:
    sh = {"sid": sid, "content": {"ink": ink or {
        "draw": "lib:chiplog", "parts": None, "acts": [], "label": "图"}},
        "sketch": None}
    sh.update(kw)
    return sh


def ink_of(label="图", parts=None, acts=None, draw="lib:chiplog") -> dict:
    return {"draw": draw, "parts": parts, "acts": acts or [], "label": label}


class IntentionalRepriseTest(unittest.TestCase):
    """有意复现不被误拦。"""

    def test_recall_with_new_label_passes(self):
        p = P()
        cs.check_reprises(p, [mk("S1"), mk("S2", ink_of(label="回看那一瞬"), recallOf="S1")])
        self.assertEqual(p.errors, [], p.errors)

    def test_variant_with_new_action_passes(self):
        p = P()
        cs.check_reprises(p, [
            mk("S1", ink_of(acts=[{"do": "point", "target": "line"}])),
            mk("S2", ink_of(acts=[{"do": "mark", "target": "line"}]), variantOf="S1"),
        ])
        self.assertEqual(p.errors, [], p.errors)

    def test_different_parts_is_not_a_repeat_at_all(self):
        """同一张线稿的不同局部（chiplog 的船身 vs 木板）本来就不是重复。"""
        p = P()
        cs.check_reprises(p, [
            mk("S1", ink_of(parts=["hull", "line"], label="船尾抛板与测速绳")),
            mk("S2", ink_of(parts=["plank"], label="木板入水的一瞬")),
        ])
        self.assertEqual(p.errors, [])
        self.assertEqual(p.hints, [])

    def test_intent_on_content_also_counts(self):
        p = P()
        s2 = mk("S2", ink_of(label="再看一次"))
        s2["content"]["recallOf"] = "S1"
        cs.check_reprises(p, [mk("S1"), s2])
        self.assertEqual(p.errors, [])


class UnintentionalRepeatTest(unittest.TestCase):
    """无意重复会被指出。"""

    def test_consecutive_same_figure_local_action_is_blocked(self):
        p = P()
        cs.check_reprises(p, [mk("S1"), mk("S2")])
        self.assertTrue(any("连续出现" in e for e in p.errors), p.errors)
        self.assertTrue(any("recallOf" in e for e in p.errors), p.errors)

    def test_nonconsecutive_full_repeat_without_intent_is_blocked(self):
        p = P()
        cs.check_reprises(p, [mk("S1"), mk("S2", ink_of(parts=["plank"])), mk("S3")])
        self.assertTrue(any("没声明意图" in e for e in p.errors), p.errors)

    def test_intent_but_identical_still_blocked(self):
        """标了 recallOf 但构图、动作、信息量全同 —— 那不是复现，是复制。"""
        p = P()
        cs.check_reprises(p, [mk("S1"), mk("S2", recallOf="S1")])
        self.assertTrue(any("全同" in e for e in p.errors), p.errors)

    def test_consecutive_same_action_is_flagged_even_with_new_label(self):
        """验收写明「同图同局部同动作连续出现会被指出」——换标签救不了连续。"""
        p = P()
        cs.check_reprises(p, [mk("S1"), mk("S2", ink_of(label="换个说法"))])
        self.assertTrue(any("连续出现" in e for e in p.errors), p.errors)

    def test_nonconsecutive_new_label_only_hints(self):
        p = P()
        cs.check_reprises(p, [mk("S1"), mk("S2", ink_of(parts=["plank"])),
                              mk("S3", ink_of(label="换个说法"))])
        self.assertEqual(p.errors, [])
        self.assertTrue(any("recallOf" in h for h in p.hints), p.hints)


class IntentReferenceTest(unittest.TestCase):
    def test_unknown_target_is_named(self):
        p = P()
        cs.check_reprises(p, [mk("S1"), mk("S2", ink_of(label="x"), recallOf="S9")])
        self.assertTrue(any("不存在" in e for e in p.errors), p.errors)

    def test_future_target_says_must_be_earlier(self):
        p = P()
        cs.check_reprises(p, [mk("S1", recallOf="S2"), mk("S2")])
        self.assertTrue(any("更早" in e for e in p.errors), p.errors)
        self.assertFalse(any("不存在" in e for e in p.errors), p.errors)


class CoverageTest(unittest.TestCase):
    def test_figure_and_sketch_paths_are_covered(self):
        for where, spec in (
            ("content.figure", {"draw": "lib:tree", "parts": ["leaf"], "acts": [], "label": "树叶"}),
            ("shot.sketch", {"draw": "lib:key", "parts": ["bow"], "acts": [], "label": "钥匙"}),
        ):
            p = P()
            a = {"sid": "S1", "content": {}, "sketch": None}
            b = {"sid": "S2", "content": {}, "sketch": None}
            if where == "content.figure":
                a["content"]["figure"] = dict(spec)
                b["content"]["figure"] = dict(spec)
            else:
                a["sketch"] = dict(spec)
                b["sketch"] = dict(spec)
            cs.check_reprises(p, [a, b])
            self.assertTrue(any(where in e for e in p.errors), (where, p.errors))

    def test_action_signature_ignores_timing(self):
        p = P()
        cs.check_reprises(p, [
            mk("S1", ink_of(acts=[{"do": "point", "target": "line", "at": 10}])),
            mk("S2", ink_of(acts=[{"do": "point", "target": "line", "at": "@L2"}])),
        ])
        # 时刻不同、动词与目标相同 → 仍是同动作（连续会被拦）
        self.assertTrue(any("连续出现" in e for e in p.errors), p.errors)

    def test_examples_stay_clean(self):
        """现有示例用同一张线稿的不同局部，不许被误拦。"""
        for rel in ("examples/recipes/jie-freeform.story.json",
                    "examples/recipes/jie-hybrid.story.json"):
            story = json.loads((ROOT / rel).read_text(encoding="utf-8"))
            with tempfile.TemporaryDirectory() as td:
                src = Path(td) / "story.json"
                src.write_text(json.dumps(story, ensure_ascii=False, indent=1), encoding="utf-8")
                r = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "compose-story.py"),
                     str(src), td, "--report", str(Path(td) / "report.json")],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
                self.assertEqual(r.returncode, 0, f"{rel} 不该被复现门禁拦下：{(r.stdout or '')[-500:]}")
                report = json.loads((Path(td) / "report.json").read_text(encoding="utf-8"))
                self.assertFalse([e for e in report.get("errors", []) if "同图" in e or "复现" in e],
                                 f"{rel} 有复现类错误：{report.get('errors')}")


if __name__ == "__main__":
    unittest.main()
