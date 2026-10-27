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


def with_shots(d: Path, shots: list[dict]) -> Path:
    (d / "manifests" / "shots.resolved.json").write_text(json.dumps({"duration": 2100, "shots": shots}), encoding="utf-8")
    return d


def cam(sid: str, scales: list[float], intent: str = "push-in", **kw) -> dict:
    return {"id": sid, "cameraIntent": intent, "keys": [{"f": i * 60, "x": 960, "y": 540, "s": v} for i, v in enumerate(scales)],
            "hero": {"size": 300, "kind": "graphic"}, "media": ["graphic"], **kw}


class CameraAgainstShotTable(unittest.TestCase):
    """3.6.0：treatment 写的景别 / 运镜要在 shots.resolved.json 里兑现。"""

    def gate(self, skin: str, t: dict, shots: list[dict]):
        d = with_shots(project(skin, {**t, "medium": {"skin": skin, "why": "w"}}), shots)
        try:
            return vt.check(d)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_signature_push_under_12_percent_is_hard(self):
        t = {**GOOD, "signature_shot": "S1 放大镜慢推", "shots": [{"id": "S1", "framing": "近", "move": "push-in", "why": "w"}]}
        hard, _, _ = self.gate("journal", t, [cam("S1", [1.04, 1.09])])
        self.assertTrue(any("招牌镜头 S1" in h and "5%" in h for h in hard), hard)
        hard, _, _ = self.gate("journal", t, [cam("S1", [1.0, 1.15])])
        self.assertFalse(any("招牌镜头" in h for h in hard), hard)

    def test_signature_focus_zoom_counts_as_push(self):
        t = {**GOOD, "signature_shot": "招牌镜头 S1：推近", "shots": []}
        shot = cam("S1", [1.0, 1.0], cinema={"focus": [{"at": 30, "zoom": 1.25, "hold": 60}]})
        hard, _, _ = self.gate("journal", t, [shot])
        self.assertFalse(any("招牌镜头" in h for h in hard), hard)

    def test_signature_gate_is_p0_for_craft_p1_for_flat(self):
        t = {**GOOD, "signature_shot": "S1", "shots": []}
        d = with_shots(project("journal", t), [cam("S1", [1.0, 1.05])])
        self.assertEqual(TreatmentGate.run_gate(self, d), 1)
        d = with_shots(project("flat", {**t, "medium": {"skin": "flat", "why": "w"}}), [cam("S1", [1.0, 1.05])])
        self.assertEqual(TreatmentGate.run_gate(self, d), 0)

    def test_move_and_framing_must_match_shot_table(self):
        t = {**GOOD, "signature_shot": "S2", "shots": [
            {"id": "S1", "framing": "全", "move": "pan-follow", "why": "w"},
            {"id": "S2", "framing": "特写", "move": "push-in", "why": "w"}]}
        _, soft, _ = self.gate("journal", t, [cam("S1", [1.10, 1.12]), cam("S2", [1.0, 1.2])])
        self.assertTrue(any("S1" in x and "cameraIntent=push-in" in x for x in soft), soft)
        self.assertTrue(any("S1" in x and "「全」" in x for x in soft), soft)
        self.assertTrue(any("S2" in x and "「特写」" in x for x in soft), soft)
        # 特写兑现：峰值 1.5（纯图形）或插入镜
        _, soft, _ = self.gate("journal", t, [cam("S1", [1.0, 1.04], intent="pan-follow"), cam("S2", [1.0, 1.5])])
        self.assertFalse(any("景别没兑现" in x or "兑现（" in x for x in soft), soft)
        _, soft, _ = self.gate("journal", t, [cam("S1", [1.0], intent="pan-follow"), cam("S2", [1.0, 1.15], insert={"of": "S1"})])
        self.assertFalse(any("「特写」" in x for x in soft), soft)

    def test_pull_back_to_wide_counts_as_wide(self):
        t = {**GOOD, "shots": [{"id": "S1", "framing": "全", "move": "pull-back", "why": "w"}]}
        _, soft, _ = self.gate("journal", t, [cam("S1", [1.08, 1.0], intent="pull-back")])
        self.assertFalse(any("「全」" in x for x in soft), soft)


class FamiliesAndSound(unittest.TestCase):
    def soft(self, t: dict) -> list[str]:
        d = project("journal", t)
        try:
            return vt.check(d)[1]
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_candidates_need_two_families(self):
        same = [{"id": c, "family": "medium-metaphor", "shape": "x"} for c in "ABC"]
        self.assertTrue(any("一族" in x for x in self.soft({**GOOD, "candidates": same})))
        mixed = [{**same[0]}, {**same[1], "family": "mystery"}, {**same[2], "family": "scale-ladder"}]
        self.assertFalse(any("family" in x or "一族" in x for x in self.soft({**GOOD, "candidates": mixed})))
        unknown = [{**same[0]}, {**same[1], "family": "hero-journey"}, {**same[2]}]
        self.assertTrue(any("未知：hero-journey" in x for x in self.soft({**GOOD, "candidates": unknown})))

    def test_families_match_blueprints(self):
        fams = {json.loads(p.read_text(encoding="utf-8")).get("family") for p in (ROOT / "blueprints").glob("*.json")}
        self.assertTrue(fams - {None} <= set(vt.FAMILIES), fams)

    def test_sound_section(self):
        self.assertTrue(any("treatment.sound" in x for x in self.soft(GOOD)))
        snd = {"silence_before_native_move_sec": 0.8, "most_important_sound": "放大镜落桌，30 s",
               "music": {"use": False, "why": "字幕片，安静更像手账"}, "foley_per_medium": ["铅笔", "湿笔刷"]}
        self.assertFalse(any("sound" in x for x in self.soft({**GOOD, "sound": snd})))
        self.assertTrue(any("silence_before" in x for x in self.soft({**GOOD, "sound": {**snd, "silence_before_native_move_sec": 0.2}})))
        self.assertTrue(any("sound.music" in x for x in self.soft({**GOOD, "sound": {**snd, "music": {"use": True}}})))


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False, verbosity=1).result.wasSuccessful() else 1)
