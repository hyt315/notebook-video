from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-facts.py"


def run(story: dict, *extra: str) -> tuple[int, str]:
    td = tempfile.mkdtemp(prefix="nv-facts-")
    (Path(td) / "story.json").write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), td, *extra],
                       capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    return r.returncode, r.stdout + r.stderr


def base_story() -> dict:
    return {"chapters": [{"shots": [
        {"id": "S1", "content": {"text": "哈希表用拉链法解决冲突"},
         "claim": {"kind": "fact", "source": "wiki-hash", "text": "拉链法"}},
        {"id": "S2", "content": {"text": "像查电话簿"},
         "claim": {"kind": "analogy", "note": "电话簿比喻"}},
        {"id": "S3", "content": {"text": "1998 年提出的算法"}},
    ]}], "sources": [
        {"id": "wiki-hash", "kind": "fact", "title": "哈希表", "url": "https://zh.wikipedia.org/wiki/Hash_table"},
        {"id": "phonebook", "kind": "analogy", "note": "电话簿比喻"},
    ]}


class FactsBoundaryTest(unittest.TestCase):
    """P2-22 的边界（先钉死这条，免得被当成事实核查器）：

    **保证**：标注本身合法 —— 引用的来源存在、类比没被当事实、AI 生成物不当来源。
    **不保证**：事实、数字、历史说法**正确**。那要人工审读。
    """

    def test_doc_states_the_boundary(self):
        doc = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("引擎不能保证的", doc)
        self.assertIn("人工审读", doc)
        self.assertIn("不是无差别硬门禁", doc)

    def test_legal_marks_pass(self):
        rc, out = run(base_story())
        self.assertEqual(rc, 0, out)
        self.assertIn("P0=0", out)

    def test_no_marks_at_all_is_not_a_hard_gate(self):
        """「不宜做成无差别硬门禁」：一镜都没有 claim 也不能拦。"""
        s = {"chapters": [{"shots": [{"id": "S1", "content": {"text": "随便讲讲"}}]}]}
        rc, out = run(s)
        self.assertEqual(rc, 0, out)


class MarksLegalityTest(unittest.TestCase):
    """P0 只拦标注自己说不通的三种情况。"""

    def test_unknown_source_is_p0(self):
        s = base_story()
        s["sources"] = [{"id": "other", "kind": "fact", "title": "x"}]
        rc, out = run(s)
        self.assertEqual(rc, 1)
        self.assertIn("在 sources 里不存在", out)

    def test_analogy_with_source_is_p0(self):
        """类比不被当成机制事实——挂到文献上会被当成事实引用。"""
        s = base_story()
        s["chapters"][0]["shots"][1]["claim"] = {"kind": "analogy", "source": "wiki-hash"}
        rc, out = run(s)
        self.assertEqual(rc, 1)
        self.assertIn("类比不是机制事实", out)

    def test_ai_generated_description_is_not_a_source(self):
        """AI 生成的 see / ink 描述不能当事实来源。"""
        s = base_story()
        s["sources"] = [{"id": "ink", "kind": "generated", "title": "ink 描述"}]
        rc, out = run(s)
        self.assertEqual(rc, 1)
        self.assertIn("AI 生成", out)

    def test_duplicate_source_id_is_p0(self):
        s = base_story()
        s["sources"].append({"id": "wiki-hash", "kind": "fact", "title": "dup"})
        rc, out = run(s)
        self.assertEqual(rc, 1)
        self.assertIn("重复", out)


class MissingMarksTest(unittest.TestCase):
    """缺标注只提示（P1），不拦出片。"""

    def test_fact_without_source_only_hints(self):
        s = base_story()
        s["sources"] = []
        s["chapters"][0]["shots"][0]["claim"] = {"kind": "fact", "text": "拉链法"}
        rc, out = run(s)
        self.assertEqual(rc, 0, out)      # P1 不拦
        self.assertIn("可核验断言没标来源", out)

    def test_fact_source_without_url_or_title_hints(self):
        s = base_story()
        s["sources"][0] = {"id": "wiki-hash", "kind": "fact"}
        rc, out = run(s)
        self.assertEqual(rc, 0, out)
        self.assertIn("无从查起", out)


class ReviewListTest(unittest.TestCase):
    """人工审读清单：含数字/年份的未标注文本——机器判不了对错，但保证它们被看见。"""

    def test_numbers_without_mark_go_to_review(self):
        rc, out = run(base_story(), "--review")
        self.assertEqual(rc, 0, out)
        self.assertIn("1998", out)
        self.assertIn("人工审读清单", out)

    def test_marked_shot_is_not_listed(self):
        s = base_story()
        s["chapters"][0]["shots"][2]["claim"] = {"kind": "fact", "source": "wiki-hash"}
        _, out = run(s, "--review")
        self.assertNotIn("1998 年提出的算法", out)

    def test_review_can_be_json(self):
        rc, out = run(base_story(), "--json")
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertIn("review", data)
        self.assertEqual(data["review"][0]["shot"], "S3")
        self.assertTrue(any("1998" in n for n in data["review"][0]["numbers"]))


class ClaimPlacementTest(unittest.TestCase):
    """claim 写在 shot 上或 content 上都认；一镜可有多条。"""

    def test_claim_on_content_counts(self):
        s = {"chapters": [{"shots": [{"id": "S1", "content": {"text": "x",
             "claim": {"kind": "fact", "source": "w"}}}]}],
             "sources": [{"id": "w", "kind": "fact", "title": "t", "url": "u"}]}
        rc, out = run(s)
        self.assertEqual(rc, 0, out)

    def test_multiple_claims_per_shot(self):
        s = {"chapters": [{"shots": [{"id": "S1", "content": {"text": "x"}, "claim": [
            {"kind": "fact", "source": "w"},
            {"kind": "analogy", "note": "比喻"},
        ]}]}], "sources": [{"id": "w", "kind": "fact", "title": "t"}]}
        rc, out = run(s)
        self.assertEqual(rc, 0, out)


if __name__ == "__main__":
    unittest.main()
