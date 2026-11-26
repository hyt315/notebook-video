"""Tests for the auto camera director, transition choreography, and layout variety."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TPL = ROOT / "assets" / "lecture-template"


def _compose(story_path: Path, td: str, skin: str = "flat", mutate=None) -> tuple[Path, dict]:
    proj = Path(td) / "p"
    shutil.copytree(TPL, proj, ignore=shutil.ignore_patterns("node_modules", "renders"))
    subprocess.run([sys.executable, str(SCRIPTS / "set-skin.py"), str(proj), skin], check=True, capture_output=True)
    if mutate is not None:
        data = json.loads(story_path.read_text(encoding="utf-8"))
        mutate(data)
        src = Path(td) / "story.json"
        src.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    else:
        src = story_path
    r1 = subprocess.run([sys.executable, str(SCRIPTS / "compose-story.py"), str(src), str(proj)], capture_output=True, text=True)
    if r1.returncode != 0:
        raise AssertionError(r1.stdout + r1.stderr)
    r2 = subprocess.run([sys.executable, str(SCRIPTS / "resolve-shots.py"), str(proj)], capture_output=True, text=True)
    if r2.returncode != 0:
        raise AssertionError(r2.stdout + r2.stderr)
    r3 = subprocess.run([sys.executable, str(SCRIPTS / "validate-shot-motion.py"), str(proj)], capture_output=True, text=True)
    resolved = json.loads((proj / "manifests" / "shots.resolved.json").read_text(encoding="utf-8"))
    return proj, {"vsm_rc": r3.returncode, "vsm_out": r3.stdout + r3.stderr, "resolved": resolved}


class CameraDirectorTest(unittest.TestCase):
    def test_multi_intent_and_zero_motion_p0_on_core_examples(self):
        with tempfile.TemporaryDirectory() as td:
            _, res_a = _compose(ROOT / "examples" / "concept-hash-table.story.json", td)
            _, res_b = _compose(ROOT / "examples" / "data-ssd-vs-hdd.story.json", str(Path(td) / "b"))

        self.assertEqual(res_a["vsm_rc"], 0, res_a["vsm_out"])
        self.assertEqual(res_b["vsm_rc"], 0, res_b["vsm_out"])

        intents_a = {s["cameraIntent"] for s in res_a["resolved"]["shots"]} - {"still"}
        intents_b = {s["cameraIntent"] for s in res_b["resolved"]["shots"]} - {"still"}
        self.assertGreaterEqual(len(intents_a), 3, f"expected >=3 intents, got {intents_a}")
        self.assertGreaterEqual(len(intents_b), 3, f"expected >=3 intents, got {intents_b}")

        for s in res_a["resolved"]["shots"] + res_b["resolved"]["shots"]:
            if s["cameraIntent"] in ("pull-back", "pan-follow", "still"):
                self.assertEqual((s.get("cinema") or {}).get("driftDir"), "none", s["id"])

    def test_per_shot_transition_and_chapter_auto_defaults(self):
        def add_override(d: dict) -> None:
            d["chapters"][1]["shots"][0]["transition"] = "zoom"

        with tempfile.TemporaryDirectory() as td:
            _, info = _compose(ROOT / "examples" / "concept-hash-table.story.json", td, mutate=add_override)
        shots = info["resolved"]["shots"]
        self.assertEqual(shots[0]["transition"], "auto")
        self.assertEqual(shots[1]["transition"], "zoom")
        # Chapter boundary without explicit override remains "auto" (page turn)
        self.assertEqual(shots[2]["transition"], "auto")
        # Intra-chapter component cuts vary away from chapter turn
        self.assertIn(shots[3]["transition"], ("fade", "slide"))

    def test_topic_seeded_variants_avoid_cross_video_clones(self):
        with tempfile.TemporaryDirectory() as td:
            d1 = Path(td) / "t1"; d1.mkdir()
            d2 = Path(td) / "t2"; d2.mkdir()
            # Ensure different title seeds pick distinct variant parity on same structure
            _, a = _compose(ROOT / "examples" / "concept-hash-table.story.json", str(d1),
                            mutate=lambda d: d.__setitem__("title", "哈希表为什么快"))
            _, b = _compose(ROOT / "examples" / "concept-hash-table.story.json", str(d2),
                            mutate=lambda d: d.__setitem__("title", "固态硬盘到底快多少"))
        la = [s["layout"] for s in a["resolved"]["shots"]]
        lb = [s["layout"] for s in b["resolved"]["shots"]]
        self.assertNotEqual(la, lb, f"expected distinct variant assignments, both were {la}")


if __name__ == "__main__":
    unittest.main()
