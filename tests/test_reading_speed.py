#!/usr/bin/env python3
"""Tests for the 3.3.0 configurable reading speed (silent-timing.py, compose-story --cps) and cue duration gate."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("st", ROOT / "scripts" / "silent-timing.py")
st = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(st)


class SilentTiming(unittest.TestCase):
    def test_speed_is_configurable(self):
        slow = st.build(["一二三四五六七八九十"], 4.5)
        fast = st.build(["一二三四五六七八九十"], 6.5)
        self.assertAlmostEqual((slow[-1]["start"] - slow[0]["start"]) / 9, 1000 / 4.5, delta=2)
        self.assertAlmostEqual((fast[-1]["start"] - fast[0]["start"]) / 9, 1000 / 6.5, delta=2)

    def test_default_depends_on_skin(self):
        d = Path(tempfile.mkdtemp())
        (d / "src" / "theme").mkdir(parents=True)
        (d / "src" / "theme" / "active.ts").write_text("import {THEME} from './journal';\nexport {THEME};\n", encoding="utf-8")
        lines = d / "l.txt"
        lines.write_text("细胞\n", encoding="utf-8")
        out = d / "w.json"
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "silent-timing.py"), str(lines), str(out), "--project", str(d)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("6.5 字/秒", r.stdout)
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "silent-timing.py"), str(lines), str(out), "--cps", "12"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_pieces_keep_punctuation_and_spaces(self):
        ps = [p for p, _ in st.pieces("「细胞」来自拉丁语 cella：小房间。")]
        self.assertEqual(ps[0], "「细")
        self.assertIn("胞」", ps)
        self.assertIn("语 ", ps)          # 尾随空格留在词片里，渲染端 captionGap 补成 \u00a0
        self.assertIn("cella：", ps)
        self.assertEqual(ps[-1], "间。")
        weights = dict(st.pieces("cella 一"))
        self.assertEqual(weights["cella "], 2.5)

    def test_pauses(self):
        w = st.build(["一，二。", "三"], 5.0, comma_ms=150, stop_ms=300, line_gap_ms=450)
        self.assertEqual(w[1]["start"] - w[0]["start"], 200 + 150)
        self.assertEqual(w[2]["start"] - w[1]["start"], 200 + 300 + 450)

    def test_compose_story_accepts_cps(self):
        src = (ROOT / "scripts" / "compose-story.py").read_text(encoding="utf-8")
        self.assertIn('ap.add_argument("--cps"', src)
        self.assertIn('cps = a.cps or story.get("cps")', src)


class CueDuration(unittest.TestCase):
    def run_sync(self, starts: list[int]) -> subprocess.CompletedProcess:
        d = Path(tempfile.mkdtemp())
        words, cues = [], []
        for i, s0 in enumerate(starts):
            w = {"part": f"字{i}", "start": s0, "end": s0 + 300}
            words.append(w)
            cues.append({"text": w["part"], "words": [w], "start_ms": s0, "speech_end_ms": s0 + 300})
        (d / "w.json").write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
        (d / "c.json").write_text(json.dumps({"segmentation": "semantic", "cues": cues}, ensure_ascii=False), encoding="utf-8")
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "validate-caption-sync.py"), str(d / "w.json"), str(d / "c.json"),
                               "--max-lead-ms", "0"], capture_output=True, text=True)

    def test_too_short_cue_fails(self):
        r = self.run_sync([0, 600, 2000])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cue 1: on screen 0.60s < 0.83s", r.stdout)

    def test_long_cue_only_warns(self):
        r = self.run_sync([0, 9000, 11000])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("SYNC WARN: cue 1: on screen 9.00s > 7.0s", r.stdout)


if __name__ == "__main__":
    unittest.main()
