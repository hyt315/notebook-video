#!/usr/bin/env python3
"""Tests for scripts/validate-treatment.py (director layer gate, 3.3.0)."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("vt", ROOT / "scripts" / "validate-treatment.py")
vt = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(vt)

GOOD = {
    "topic": "细胞为什么叫细胞", "question": "“细胞”这个词最早是什么意思？",
    "metaphor": {"idea": "空房间", "why_unique": "cell 本义是小房间"},
    "medium": {"skin": "journal", "why": "观察手账"},
    "native_move": {"what": "放大镜下格子被刷成房间", "at_sec": 30, "why_only_this_medium": "水彩晕开"},
    "candidates": [{"id": "A", "shape": "旅程"}, {"id": "B", "shape": "对比"}, {"id": "C", "shape": "倒计时"}],
    "chosen": "A", "chosen_why": "错误直觉", "logline": "一句话",
    "arc": {"setup": "s", "turn": "t", "ending": "e"}, "turn_to_you_sec": 30,
    "ending_echo": {"opening_image": "软木", "one_change": "房间里有了东西"},
    "benchmark": {"works": ["x"], "learn": ["构图"], "not_learn": ["角色"]},
    "shots": [{"id": "S1", "framing": "近", "move": "push-in", "why": "w"}],
    "signature_shot": "S3 放大镜",
    "commons": {"queries": ["Hooke cork"], "used": ["cork"]},
    "facts": [{"claim": "1665", "url": "https://www.gutenberg.org/ebooks/15491", "quote": "a great many little Boxes"}],
}


def project(skin: str, treatment: dict | None, searched: bool = True, media_ids=("cork",)) -> Path:
    d = Path(tempfile.mkdtemp(prefix="nv-treat-"))
    (d / "src" / "theme").mkdir(parents=True)
    (d / "manifests").mkdir()
    (d / "src" / "theme" / "active.ts").write_text(f"import {{THEME}} from './{skin}';\nexport {{THEME}};\n", encoding="utf-8")
    (d / "manifests" / "shots.resolved.json").write_text(json.dumps({"duration": 2100, "shots": [{"id": "S1"}]}), encoding="utf-8")
    (d / "manifests" / "media.json").write_text(json.dumps({"items": [{"id": i} for i in media_ids]}), encoding="utf-8")
    if searched:
        (d / "manifests" / "commons-log.json").write_text(json.dumps({"searches": [{"query": "Hooke cork"}]}), encoding="utf-8")
    if treatment is not None:
        (d / "manifests" / "treatment.json").write_text(json.dumps(treatment, ensure_ascii=False), encoding="utf-8")
    return d


class TreatmentGate(unittest.TestCase):
    def run_gate(self, d: Path) -> int:
        try:
            return vt.main([str(d)])
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_good_journal_passes(self):
        self.assertEqual(self.run_gate(project("journal", GOOD)), 0)

    def test_missing_treatment_blocks_craft_only(self):
        self.assertEqual(self.run_gate(project("journal", None)), 1)
        self.assertEqual(self.run_gate(project("flat", None)), 0)

    def test_placeholder_blocks(self):
        t = json.loads(json.dumps(GOOD))
        t["metaphor"]["idea"] = "<<只属于这个题的隐喻>>"
        self.assertEqual(self.run_gate(project("papercut", {**t, "medium": {"skin": "papercut", "why": "w"}})), 1)

    def test_two_candidates_block(self):
        t = {**GOOD, "candidates": GOOD["candidates"][:2]}
        self.assertEqual(self.run_gate(project("journal", t)), 1)

    def test_skin_mismatch_blocks(self):
        self.assertEqual(self.run_gate(project("archive", GOOD)), 1)

    def test_commons_must_be_searched(self):
        self.assertEqual(self.run_gate(project("journal", GOOD, searched=False)), 1)

    def test_used_media_must_exist(self):
        self.assertEqual(self.run_gate(project("journal", GOOD, media_ids=())), 1)

    def test_fact_needs_url_and_quote(self):
        t = {**GOOD, "facts": [{"claim": "x", "url": "gutenberg", "quote": ""}]}
        self.assertEqual(self.run_gate(project("journal", t)), 1)

    def test_native_move_beyond_duration(self):
        t = {**GOOD, "native_move": {**GOOD["native_move"], "at_sec": 999}}
        self.assertEqual(self.run_gate(project("journal", t)), 1)

    def test_example_template_is_all_placeholders(self):
        ex = json.loads((ROOT / "assets" / "lecture-template" / "manifests" / "treatment.example.json").read_text(encoding="utf-8"))
        self.assertEqual(self.run_gate(project("journal", ex)), 1)


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False, verbosity=1).result.wasSuccessful() else 1)
