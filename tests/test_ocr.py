#!/usr/bin/env python3
"""Tests for scripts/validate-ocr.py (3.3.0). Pure functions run everywhere (standard library only);
the end-to-end case runs only where RapidOCR, ffmpeg drawtext and a font are available, and is skipped otherwise."""
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
spec = importlib.util.spec_from_file_location("vocr", ROOT / "scripts" / "validate-ocr.py")
vocr = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(vocr)

CUES = [
    {"text": "胡克切了一片软木，", "start": 0.0, "reveal_end": 1.2},
    {"text": "看见许多小盒子。", "start": 2.0, "reveal_end": 3.1},
    {"text": "他叫它们 cells", "start": 4.0, "reveal_end": 5.0},
]


class EngineProbe(unittest.TestCase):
    """3.3.0：onnxruntime 与解释器不兼容时 import 即段错误，try/except 拦不住。
    必须先在子进程里探测，否则用户看到的是「脚本崩溃」而不是「跳过」。"""

    def test_crashing_interpreter_is_reported_not_raised(self):
        ok, why = vocr._probe([sys.executable, "-c", "import sys; sys.exit(139)"])
        self.assertFalse(ok)
        self.assertIn("rc=139", why)

    def test_missing_engine_reports_install_hint(self):
        ok, why = vocr._probe([sys.executable, "-c", "import sys; sys.exit(3)"])
        self.assertFalse(ok)
        self.assertIn("没装 RapidOCR", why)

    def test_healthy_interpreter_is_available(self):
        ok, why = vocr._probe([sys.executable, "-c", "import sys; sys.exit(0)"])
        self.assertTrue(ok)
        self.assertEqual(why, "")


class Reexec(unittest.TestCase):
    """3.3.0: NOTEBOOK_VIDEO_OCR_PYTHON must work when it points at a venv python (a symlink)."""
    @unittest.skipIf(sys.platform == "win32", "Windows 创建符号链接需要管理员/开发者模式（WinError 1314），venv 也不用符号链接")
    def test_venv_symlink_to_current_interpreter_reexecs(self):
        with tempfile.TemporaryDirectory() as d:
            link = Path(d) / "venv" / "bin" / "python"
            link.parent.mkdir(parents=True)
            link.symlink_to(sys.executable)
            self.assertEqual(link.resolve(), Path(sys.executable).resolve())   # the old check saw "same"
            self.assertTrue(vocr.should_reexec(str(link), sys.executable, {}))

    def test_same_path_or_guard_or_unset_does_not_reexec(self):
        self.assertFalse(vocr.should_reexec(sys.executable, sys.executable, {}))
        self.assertFalse(vocr.should_reexec("/opt/x/python", sys.executable, {"_NV_OCR_REEXEC": "1"}))
        self.assertFalse(vocr.should_reexec(None, sys.executable, {}))
        self.assertFalse(vocr.should_reexec("", sys.executable, {}))


class ReadingOrder(unittest.TestCase):
    """3.3.0: OCR lines are joined in reading order, not in the engine's output order."""
    # cell-v3 cue9 实测：署名签 4 行在上，字幕一行被拆成两段且倒序吐出
    LINES = [
        {"text": "Schem.XI", "score": 0.99, "h": 32, "x": 60, "y": 17},
        {"text": "Robert Hooke (1635-1703)·公有领域·", "score": 0.95, "h": 30, "x": 140, "y": 52},
        {"text": "Wikimedia Commons", "score": 0.97, "h": 25, "x": 90, "y": 78},
        {"text": "cella:小房间", "score": 0.98, "h": 116, "x": 1080, "y": 195},
        {"text": "拉丁语", "score": 0.99, "h": 101, "x": 760, "y": 197},
    ]

    def test_same_row_left_to_right(self):
        got = "".join(x["text"] for x in vocr.reading_order(self.LINES))
        self.assertTrue(got.endswith("拉丁语cella:小房间"), got)

    def test_judge_passes_after_reordering(self):
        res = vocr.judge("拉丁语 cella：小房间。", self.LINES, 281, 0.26, 80)
        self.assertEqual(res["level"], "ok", res)
        self.assertEqual(res["sim"], 1.0)

    def test_lines_without_coordinates_keep_engine_order(self):
        lines = [{"text": "b", "score": 1, "h": 10}, {"text": "a", "score": 1, "h": 10}]
        self.assertEqual([x["text"] for x in vocr.reading_order(lines)], ["b", "a"])

    def test_line_helper_box_centre(self):
        ln = vocr._line("x", 0.9, [[0, 10], [100, 10], [100, 50], [0, 50]])
        self.assertEqual((ln["x"], ln["y"], ln["h"]), (50.0, 30.0, 40.0))


class Normalize(unittest.TestCase):
    def test_strips_punct_space_and_width(self):
        self.assertEqual(vocr.normalize("他叫它们　Cells！"), "他叫它们cells")
        self.assertEqual(vocr.normalize("1/18 英寸，"), "118英寸")

    def test_similarity_exact_and_empty(self):
        self.assertEqual(vocr.similarity("看见许多小盒子。", "看见许多小盒子"), 1.0)
        self.assertEqual(vocr.similarity("看见许多小盒子", ""), 0.0)

    def test_similarity_ignores_extra_text_in_band(self):
        # 字幕带里还读到了画内的批注：原文全部命中即满分
        self.assertEqual(vocr.similarity("看见许多小盒子", "No.02看见许多小盒子 Scheme XI"), 1.0)

    def test_similarity_partial(self):
        s = vocr.similarity("看见许多小盒子", "看见许多")
        self.assertTrue(0.6 < s < 0.9, s)


class Timing(unittest.TestCase):
    def test_sample_after_reveal_and_before_next(self):
        ts = vocr.cue_sample_times(CUES)
        self.assertAlmostEqual(ts[0], 1.45)
        self.assertAlmostEqual(ts[1], 3.35)
        self.assertAlmostEqual(ts[2], 5.25)

    def test_sample_clipped_by_next_cue(self):
        ts = vocr.cue_sample_times([{"text": "a", "start": 0, "reveal_end": 0.9}, {"text": "b", "start": 1.0, "reveal_end": 1.5}])
        # 3.3.0：下一条提前 0.18 s 出现，取样点 = 1.0 − 0.18 − 0.07（旧值 0.88 读到的是下一句）
        self.assertAlmostEqual(ts[0], 0.75)

    def test_sample_never_inside_next_cue_lead(self):
        # cell-v3 的真实间隔：cue3 3.822–4.797，cue4 5.107（旧算法取 4.987，画面已是 cue4）
        cues = [{"text": "很多人都以为，", "start": 3.822, "reveal_end": 4.797},
                {"text": "它生来就指「生命单位」。", "start": 5.107, "reveal_end": 6.544}]
        ts = vocr.cue_sample_times(cues)
        self.assertLess(ts[0], 5.107 - vocr.NEXT_CUE_LEAD)
        self.assertGreaterEqual(ts[0], 4.797)
        self.assertEqual(vocr.cue_at(cues, ts[0]), 0)
        self.assertIsNone(vocr.cue_at(cues, 5.0))   # 进入下一条的提前量：不再算 cue3

    def test_lead_matches_subtitle_component(self):
        src = (ROOT / "assets" / "lecture-template" / "src" / "index.tsx").read_text(encoding="utf-8")
        self.assertIn("lead=Math.round(FPS*.18)", src)
        self.assertAlmostEqual(vocr.NEXT_CUE_LEAD, 0.18)

    def test_cue_at(self):
        self.assertIsNone(vocr.cue_at(CUES, 0.5))      # 还在逐字显示
        self.assertEqual(vocr.cue_at(CUES, 1.5), 0)
        self.assertEqual(vocr.cue_at(CUES, 3.5), 1)
        self.assertIsNone(vocr.cue_at(CUES, 9.0))

    def test_ms_fields(self):
        ts = vocr.cue_sample_times([{"text": "a", "start_ms": 0, "reveal_end_ms": 1000}])
        self.assertAlmostEqual(ts[0], 1.25)


class Judge(unittest.TestCase):
    def test_ok(self):
        r = vocr.judge("看见许多小盒子。", [{"text": "看见许多小盒子。", "score": 0.99, "h": 92}], 1440, 0.26, 80)
        self.assertEqual(r["level"], "ok", r)

    def test_missing_subtitle_is_p0(self):
        r = vocr.judge("看见许多小盒子。", [], 1440, 0.26, 80)
        self.assertEqual(r["level"], "P0")
        r = vocr.judge("看见许多小盒子。", [{"text": "Scheme XI", "score": 0.9, "h": 40}], 1440, 0.26, 80)
        self.assertEqual(r["level"], "P0")

    def test_half_read_is_p1(self):
        r = vocr.judge("看见许多小盒子。", [{"text": "看见许多小盆", "score": 0.95, "h": 92}], 1440, 0.26, 80)
        self.assertEqual(r["level"], "P1")

    def test_low_confidence_is_p1(self):
        r = vocr.judge("看见许多小盒子", [{"text": "看见许多小盒子", "score": 0.6, "h": 92}], 1440, 0.26, 80)
        self.assertEqual(r["level"], "P1")
        self.assertIn("置信度", r["issue"])

    def test_small_glyphs_scaled_to_1440(self):
        # 720p 静帧里 40 px 高 = 80 px@1440 → 刚好够；30 px = 60 px@1440 → 偏小
        ok = vocr.judge("看见许多小盒子", [{"text": "看见许多小盒子", "score": 0.99, "h": 40}], 720, 0.26, 80)
        small = vocr.judge("看见许多小盒子", [{"text": "看见许多小盒子", "score": 0.99, "h": 30}], 720, 0.26, 80)
        self.assertEqual(ok["level"], "ok")
        self.assertEqual(small["level"], "P1")


class Cli(unittest.TestCase):
    def test_usage_errors(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate-ocr.py"), str(ROOT)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


def _font() -> str | None:
    if not shutil.which("fc-match"):
        return None
    out = subprocess.run(["fc-match", "-f", "%{file}", "sans"], capture_output=True, text=True).stdout.strip()
    return out if out and Path(out).is_file() else None


@unittest.skipUnless(vocr.load_engine() is not None and shutil.which("ffmpeg") and _font(), "RapidOCR / ffmpeg / font not available")
class EndToEnd(unittest.TestCase):
    """真 OCR：清楚的字幕通过；字幕被盖掉的同一帧必须被拦（P0）。"""

    def _project(self, td: Path, text: str) -> Path:
        (td / "manifests").mkdir()
        (td / "manifests" / "caption-cues.json").write_text(json.dumps({"cues": [{"text": text, "start": 0.0, "reveal_end": 0.0}]}), encoding="utf-8")
        return td

    def _still(self, path: Path, text: str, hidden: bool) -> None:
        draw = f"drawtext=fontfile='{_font()}':text='{text}':fontsize=48:fontcolor=0x222222:x=(w-text_w)/2:y=h-90"
        vf = draw + (",drawbox=x=0:y=ih-140:w=iw:h=140:color=0xf3ead8:t=fill" if hidden else "")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=0xf3ead8:s=1280x720", "-frames:v", "1", "-vf", vf, str(path)], check=True)

    def test_clear_passes_and_covered_fails(self):
        text = "HOOKE SAW LITTLE BOXES"
        for hidden, want in ((False, 0), (True, 1)):
            with tempfile.TemporaryDirectory() as d:
                td = self._project(Path(d), text)
                (td / "stills").mkdir()
                self._still(td / "stills" / "f00010.png", text, hidden)
                r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate-ocr.py"), str(td), "--stills", str(td / "stills"), "--min-px", "60"],
                                   capture_output=True, text=True)
                self.assertEqual(r.returncode, want, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
