"""过程词 / 内部版本号守护：指令文档里写版本史、事故复述会被 validate-skill 拦下。"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("vsc_process", ROOT / "scripts" / "validate-skill-consistency.py")
VSC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VSC)


class ProcessWordsTest(unittest.TestCase):
    def test_internal_version_is_caught(self):
        self.assertTrue(VSC.process_word_hits("这条规则 v3.7 修复了字幕超长"))
        self.assertTrue(VSC.process_word_hits("3.6.0 起手账页是承载层"))
        self.assertTrue(VSC.process_word_hits("3.1.x 的旧画布"))

    def test_incident_wording_is_caught(self):
        self.assertTrue(VSC.process_word_hits("这里踩过两次假阳性"))
        self.assertTrue(VSC.process_word_hits("上一版是 465 行的实现"))

    def test_dependency_versions_and_plain_numbers_pass(self):
        for ok in ("perfect-freehand 1.2.3（MIT）", "`@paper-design/shaders@0.0.82`", "Remotion 4.0.539",
                   "BudouX 0.9.2", "WCAG 2.2 SC 1.4.3", "展开 22 帧，相隔 0.5 秒", "`mimo-v2.5-tts`"):
            self.assertEqual(VSC.process_word_hits(ok), [], ok)

    def test_shipped_agent_docs_are_clean(self):
        self.assertEqual(VSC.check_process_words(), [])


if __name__ == "__main__":
    unittest.main()
