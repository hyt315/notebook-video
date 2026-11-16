"""--engine=file 的可选 faster-whisper 对齐：装了就按台词对齐，没装 / 关掉 / 对不上就退回按字数均分。

faster_whisper 用假模块代替（不装包、不下载模型）；音频时长打桩，不需要 ffmpeg。
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
_spec = importlib.util.spec_from_file_location("nv_tts", ROOT / "scripts" / "tts.py")
tts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tts)

LINES = ["你好，世界。", "第二句。"]


def fake_whisper(words):
    """造一个假的 faster_whisper 模块：transcribe 返回一个 segment，带给定的 (词, 起秒, 止秒)。"""
    mod = types.ModuleType("faster_whisper")

    class WhisperModel:
        def __init__(self, *a, **k):
            pass

        def transcribe(self, *a, **k):
            seg = types.SimpleNamespace(words=[types.SimpleNamespace(word=w, start=s, end=e) for w, s, e in words])
            return iter([seg]), None

    mod.WhisperModel = WhisperModel
    return mod


class FileEngineAlignTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.project = Path(self.td.name)
        (self.project / "audio").mkdir()
        (self.project / "audio" / "narration.mp3").write_bytes(b"x")
        self.env = mock.patch.dict(os.environ, {"NV_WHISPER": ""})
        self.env.start()
        self.dur = mock.patch.object(tts, "audio_duration_ms", return_value=3000)
        self.dur.start()

    def tearDown(self):
        self.dur.stop()
        self.env.stop()
        self.td.cleanup()

    def check_timeline(self, words):
        self.assertEqual("".join(w["part"] for w in words), "你好，世界。第二句。")
        prev = 0
        for w in words:
            self.assertLessEqual(prev, w["start"])
            self.assertLessEqual(w["start"], w["end"])
            prev = w["end"]

    def test_without_faster_whisper_falls_back_to_even_split(self):
        with mock.patch.dict(sys.modules, {"faster_whisper": None}):  # import 会抛 ImportError
            words, engine, estimated = tts.synth_file(self.project, LINES)
        self.assertEqual((engine, estimated), ("file", True))
        self.assertEqual(words, tts.even_split(list("你好，世界。第二句。"), 3000))
        self.check_timeline(words)

    def test_with_faster_whisper_uses_recognized_times(self):
        heard = [("你好", 0.10, 0.50), ("世界", 0.70, 1.10), ("第二", 1.60, 1.90), ("句", 1.90, 2.20)]
        with mock.patch.dict(sys.modules, {"faster_whisper": fake_whisper(heard)}):
            words, engine, estimated = tts.synth_file(self.project, LINES)
        self.assertEqual((engine, estimated), ("file+faster-whisper", False))
        self.check_timeline(words)
        by = {w["part"]: w for w in words if w["part"] not in "，。"}
        self.assertEqual((by["你"]["start"], by["好"]["end"]), (100, 500))
        self.assertEqual((by["世"]["start"], by["界"]["end"]), (700, 1100))
        self.assertEqual((by["句"]["start"], by["句"]["end"]), (1900, 2200))
        comma = words[2]
        self.assertEqual((comma["start"], comma["end"]), (500, 700))  # 标点填在前后两个字之间

    def test_recognition_error_inside_is_interpolated(self):
        heard = [("你好", 0.10, 0.50), ("视界", 0.70, 1.10), ("第二句", 1.60, 2.20)]  # 「世」听成「视」
        with mock.patch.dict(sys.modules, {"faster_whisper": fake_whisper(heard)}):
            words, engine, estimated = tts.synth_file(self.project, LINES)
        self.assertFalse(estimated)
        self.check_timeline(words)
        shi = words[3]
        self.assertEqual(shi["part"], "世")
        self.assertGreaterEqual(shi["start"], 500)
        self.assertLessEqual(shi["end"], 1100)

    def test_unrelated_recording_falls_back(self):
        heard = [("完全", 0.1, 0.5), ("不同", 0.5, 0.9), ("内容", 0.9, 1.3)]
        with mock.patch.dict(sys.modules, {"faster_whisper": fake_whisper(heard)}):
            words, engine, estimated = tts.synth_file(self.project, LINES)
        self.assertEqual((engine, estimated), ("file", True))

    def test_switched_off_by_env(self):
        heard = [("你好", 0.10, 0.50), ("世界", 0.70, 1.10), ("第二句", 1.60, 2.20)]
        with mock.patch.dict(os.environ, {"NV_WHISPER": "off"}), \
             mock.patch.dict(sys.modules, {"faster_whisper": fake_whisper(heard)}):
            _, engine, estimated = tts.synth_file(self.project, LINES)
        self.assertEqual((engine, estimated), ("file", True))


if __name__ == "__main__":
    unittest.main()
