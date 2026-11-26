#!/usr/bin/env python3
"""版式输入的两条契约：直书页逐行 reveal 各自生效；flow 缺 label 报一句能照改的话而不是崩溃。"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


layout = load("layout_inputs", SCRIPTS / "story_layout.py")


class P:
    def __init__(self):
        self.errors, self.fixes, self.hints = [], [], []

    def err(self, m): self.errors.append(m)
    def fix(self, m): self.fixes.append(m)
    def hint(self, m): self.hints.append(m)


class TypeRowsReveal(unittest.TestCase):
    def test_each_row_keeps_its_own_reveal(self):
        p = P()
        rows = [{"text": "第一行写法", "reveal": "slide"}, {"text": "第二行写法"}, {"text": "第三行写法", "reveal": "type"}]
        els = layout.lay_type(p, "S1", {"rows": rows}, "a")
        got = [e.get("reveal") for e in els if e.get("kind") == "text" and str(e.get("id", "")).startswith("row")]
        self.assertEqual(got, ["slide", "type", "type"], els)


class FlowLabel(unittest.TestCase):
    def test_example_in_error_uses_label(self):
        self.assertIn('"label"', layout._EXAMPLES["flow"])
        self.assertNotIn('"text"', layout._EXAMPLES["flow"])

    def test_missing_label_is_an_error_not_a_crash(self):
        p = P()
        out = layout.lay_flow(p, "S2", {"steps": [{"text": "第一步"}, {"text": "第二步"}]}, "a")
        self.assertEqual(out, [])
        self.assertTrue(any("label" in e for e in p.errors), p.errors)


if __name__ == "__main__":
    unittest.main()


# ---- 评审卡：五项 1–5 分（references/rubric.md）能被 validate-treatment 读懂 ----
import copy  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
import tempfile  # noqa: E402

vt = load("vt_review", SCRIPTS / "validate-treatment.py")
_tt = load("tt_review", Path(__file__).resolve().parent / "test_treatment.py")


def _review_soft(scores: dict) -> str:
    t = copy.deepcopy(_tt.GOOD)
    t["review"] = {"rounds": [{"scores": scores}]}
    d = _tt.project("journal", t)
    try:
        _, soft, _ = vt.check(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return "\n".join(soft)


class ReviewRubric(unittest.TestCase):
    FULL = {k: 5 for k in ("复述核心概念", "先打掉常见误解", "专属例子或隐喻", "画面时机帮助理解", "记住的锤子句")}

    def test_five_key_full_marks_no_review_hint(self):
        self.assertNotIn("最后一轮评审", _review_soft(self.FULL))

    def test_five_key_low_score_is_flagged(self):
        s = dict(self.FULL, 记住的锤子句=3)
        self.assertIn("记住的锤子句=3", _review_soft(s))

    def test_legacy_ten_point_rounds_still_judged(self):
        legacy = {k: 9 for k in vt.REVIEW_KEYS}
        self.assertNotIn("最后一轮评审", _review_soft(legacy))
        legacy["叙事完整"] = 6
        self.assertIn("叙事完整=6", _review_soft(legacy))


class TemplateTreatmentOnNewFilm(unittest.TestCase):
    def _hard(self, with_fusion: bool):
        t = copy.deepcopy(_tt.GOOD)
        t["$about"] = "模板示例片的导演层（GitHub 三部曲）"
        d = _tt.project("journal", t)
        if with_fusion:
            (d / "manifests" / "fusion.json").write_text("{}", encoding="utf-8")
        try:
            hard, soft, _ = vt.check(d)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        return hard, soft

    def test_composed_project_gets_one_clear_p0(self):
        hard, soft = self._hard(True)
        self.assertEqual(len(hard), 1, hard)
        self.assertIn("模板示例片", hard[0])

    def test_template_itself_is_judged_normally(self):
        hard, _ = self._hard(False)
        self.assertFalse(any("模板示例片" in h for h in hard), hard)


class HandwrittenBlueprintIntoCompose(unittest.TestCase):
    def test_compose_names_the_route(self):
        import subprocess
        import sys as _sys
        root = SCRIPTS.parent
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run([_sys.executable, str(SCRIPTS / "compose-story.py"),
                                str(root / "blueprints" / "medium-metaphor.json"), str(Path(td) / "p")],
                               capture_output=True, text=True, encoding="utf-8")
        out = r.stdout + r.stderr
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("handwritten-craft", out)
        self.assertNotIn("Traceback", out)


class ScriptConstantDrift(unittest.TestCase):
    def test_doc_value_must_match_script_constant(self):
        root = SCRIPTS.parent
        with tempfile.TemporaryDirectory() as td:
            dst = Path(td) / "s"
            shutil.copytree(root, dst, ignore=shutil.ignore_patterns("node_modules", "tests", ".git"))
            p = dst / "scripts" / "validate-presentation.py"
            p.write_text(p.read_text(encoding="utf-8").replace("CPS_MAX = 9.0", "CPS_MAX = 11.0"), encoding="utf-8")
            p = dst / "scripts" / "silent-timing.py"
            p.write_text(p.read_text(encoding="utf-8").replace("CPS_MAX = 9.0", "CPS_MAX = 11.0"), encoding="utf-8")
            m = load("vsc_drift", dst / "scripts" / "validate-skill-consistency.py")
            probs = m.check_contract_numeric_consistency()
        self.assertTrue(any("`CPS_MAX`" in x for x in probs), probs)
