"""Tests for resilient TTS alignment, pause-midpoint shot cuts, and file-engine helpers."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


CS = _load("cs_sync_test", SCRIPTS / "compose-story.py")
TTS = _load("tts_sync_test", SCRIPTS / "tts.py")


class _Problems:
    def __init__(self):
        self.fixes, self.hints, self.errors = [], [], []

    def fix(self, m): self.fixes.append(m)
    def hint(self, m): self.hints.append(m)
    def err(self, m): self.errors.append(m)


class TtsSyncReliabilityTest(unittest.TestCase):
    def _sample_comp(self):
        cues = [
            {"text": "第一句说完停顿，", "start_ms": 0, "speech_end_ms": 1400, "reveal_end_ms": 1400, "start": 0.0, "speech_end": 1.4, "reveal_end": 1.4, "words": []},
            {"text": "第二句从这开始。", "start_ms": 1700, "speech_end_ms": 3300, "reveal_end_ms": 3300, "start": 1.7, "speech_end": 3.3, "reveal_end": 3.3, "words": []},
        ]
        shots = [
            {"sid": "S1", "start_ms": 0, "line_cues": [[0]], "terms": []},
            {"sid": "S2", "start_ms": 1550, "line_cues": [[1]], "terms": [{"cue": 1, "start": 2, "ms": 2000}]},
        ]
        return {"cues": cues, "shots": shots, "total_ms": 4700}

    def test_retime_fallback_handles_minor_punctuation_mismatch_and_pause_cut(self):
        comp = self._sample_comp()
        # Omit comma & replace "二" with "2" (spoken ratio well >= 0.90)
        words = [
            {"part": "第", "start": 100, "end": 300},
            {"part": "一", "start": 300, "end": 500},
            {"part": "句", "start": 500, "end": 700},
            {"part": "说", "start": 700, "end": 900},
            {"part": "完", "start": 900, "end": 1100},
            {"part": "停", "start": 1100, "end": 1300},
            {"part": "顿", "start": 1300, "end": 1500},
            {"part": "第", "start": 2100, "end": 2300},
            {"part": "2", "start": 2300, "end": 2500},
            {"part": "句", "start": 2500, "end": 2700},
            {"part": "从", "start": 2700, "end": 2900},
            {"part": "这", "start": 2900, "end": 3100},
            {"part": "开", "start": 3100, "end": 3300},
            {"part": "始", "start": 3300, "end": 3500},
        ]
        p = _Problems()
        ok = CS.retime_to_tts(comp, words, p)
        self.assertTrue(ok, p.hints)
        self.assertTrue(p.fixes)
        # Preserve exact cue text characters in words
        for c in comp["cues"]:
            self.assertEqual("".join(w["part"] for w in c["words"]), c["text"])
        # Inter-shot cut must fall strictly inside the real pause between S1 end (<=1505) and S2 start (2100)
        s1_end = comp["cues"][0]["speech_end_ms"]
        s2_start = comp["cues"][1]["start_ms"]
        cut_ms = comp["shots"][1]["start_ms"]
        self.assertLessEqual(s1_end, 1505)
        self.assertEqual(s2_start, 2100)
        self.assertGreater(cut_ms, s1_end)
        self.assertLess(cut_ms, s2_start)

    def test_retime_aborts_when_script_differs_too_much(self):
        comp = self._sample_comp()
        words = [{"part": ch, "start": i * 100, "end": (i + 1) * 100} for i, ch in enumerate("完全不相关的一段新台词测试样本")]
        p = _Problems()
        ok = CS.retime_to_tts(comp, words, p)
        self.assertFalse(ok)
        self.assertTrue(p.hints)

    def test_even_split_bounds_and_punctuation_weights(self):
        chars = list("快慢，止。")
        res = TTS.even_split(chars, 2000, speech_start_ms=200, speech_end_ms=1700)
        self.assertEqual(res[0]["start"], 200)
        self.assertEqual(res[-1]["end"], 1700)
        # Comma gets shorter slice than sentence-ending period
        comma_dur = res[2]["end"] - res[2]["start"]
        period_dur = res[4]["end"] - res[4]["start"]
        self.assertLess(comma_dur, period_dur)

    def test_check_spoken_form_flags_ascii_operators(self):
        hits = TTS.check_spoken_form(["耗时 >= 10ms 时看 https://example.com", "正常中文一句。"])
        self.assertEqual(len(hits), 1)


if __name__ == "__main__":
    unittest.main()
