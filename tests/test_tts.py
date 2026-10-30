"""TTS 正式步骤：--engine=file 要产出可用词级时间，compose 要按它重排字幕/镜头。

edge 引擎需要联网，不在这里测（由接受度测试人工跑）；这里钉住不依赖网络的那一半：
  · file 引擎：读 narration.txt + 现成音频 → 词级时间、meta、删掉静音占位标记；
  · compose 的 retime：cue 时间跟词表走、标点不丢、镜头起点跟着第一句字幕走。
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TTS = ROOT / "scripts" / "tts.py"
COMPOSE = ROOT / "scripts" / "compose-story.py"
FFMPEG = shutil.which("ffmpeg")


def load_compose():
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("compose_story_mod", COMPOSE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@unittest.skipUnless(FFMPEG, "需要 ffmpeg 生成占位音频")
class TtsFileEngine(unittest.TestCase):
    def test_file_engine_writes_words_and_meta(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / "audio").mkdir()
            (project / "narration.txt").write_text("你好，世界。\n第二句。\n", encoding="utf-8")
            (project / "audio" / ".silent-placeholder").write_text("x", encoding="utf-8")
            subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                            "-i", "anullsrc=r=48000:cl=mono", "-t", "3", "-q:a", "9",
                            str(project / "audio" / "narration.mp3")], check=True, timeout=60)
            r = subprocess.run([sys.executable, str(TTS), str(project), "--engine=file"],
                               capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            words = json.loads((project / "audio" / "narration.mp3.json").read_text(encoding="utf-8"))
            meta = json.loads((project / "audio" / "narration.meta.json").read_text(encoding="utf-8"))
            self.assertTrue(meta["estimated"])
            self.assertEqual("".join(w["part"] for w in words), "你好，世界。第二句。")
            self.assertFalse((project / "audio" / ".silent-placeholder").exists())
            self.assertLess(words[0]["start"], words[-1]["end"])

    def test_missing_audio_lists_two_ways(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / "narration.txt").write_text("一句话。\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(TTS), str(project), "--engine=file"],
                               capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 3)
            self.assertIn("两条路", r.stderr)
            self.assertIn("--engine=edge", r.stderr)


class Retime(unittest.TestCase):
    def test_cues_and_shots_follow_tts(self):
        cs = load_compose()
        words = []
        t = 1000
        for ch in "第一句。第二句。":
            words.append({"part": ch, "start": t, "end": t + 100})
            t += 120
        comp = {
            "cues": [
                {"text": "第一句。", "words": [], "start_ms": 700, "speech_end_ms": 1100},
                {"text": "第二句。", "words": [], "start_ms": 1200, "speech_end_ms": 1600},
            ],
            "shots": [
                {"start_ms": 700, "line_cues": [[0]]},
                {"start_ms": 1200, "line_cues": [[1]]},
            ],
            "total_ms": 2000,
        }
        p = cs.Problems()
        self.assertTrue(cs.retime_to_tts(comp, words, p))
        self.assertEqual(comp["cues"][0]["start_ms"], 1000)
        self.assertEqual("".join(w["part"] for w in comp["cues"][0]["words"]), "第一句。")
        self.assertEqual(comp["shots"][0]["start_ms"], 1000)  # 原起点 700 + 差值 300
        # 第二句从第 5 个字音开始（1000 + 4×120）；原起点 1200 → 1480
        self.assertEqual(comp["shots"][1]["start_ms"], 1480)

    def test_mismatch_refuses_instead_of_half_aligning(self):
        cs = load_compose()
        comp = {"cues": [{"text": "对不上。", "words": [], "start_ms": 0, "speech_end_ms": 100}],
                "shots": [{"start_ms": 0, "line_cues": [[0]]}], "total_ms": 500}
        p = cs.Problems()
        self.assertFalse(cs.retime_to_tts(comp, [{"part": "别", "start": 0, "end": 10}], p))
        self.assertTrue(p.hints)


if __name__ == "__main__":
    unittest.main()
