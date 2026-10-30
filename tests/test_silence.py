"""句间静音门禁：music.use=false 时，成片的句间空隙必须真的安静。

旧版音乐床写死循环（treatment 里 use=false 也关不掉），145 秒成片里没有一处 0.4 秒静音。
这里用 ffmpeg 现造两段 4 秒片子验证判据本身：
  · 静音轨 → 通过；
  · 持续正弦音（模拟配乐）→ 必须 P0。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-silence.py"
FFMPEG = shutil.which("ffmpeg")


def make_project(root: Path, music: bool) -> Path:
    project = root / "proj"
    (project / "manifests").mkdir(parents=True)
    cues = {
        "cues": [
            {"text": "第一句。", "start_ms": 0, "speech_end_ms": 1200},
            {"text": "第二句。", "start_ms": 2600, "speech_end_ms": 3800},
        ]
    }
    (project / "manifests" / "caption-cues.json").write_text(json.dumps(cues, ensure_ascii=False), encoding="utf-8")
    (project / "manifests" / "treatment.json").write_text(
        json.dumps({"sound": {"music": {"use": music}}}, ensure_ascii=False), encoding="utf-8")
    return project


def make_video(path: Path, tone: bool) -> None:
    audio = "sine=frequency=440:sample_rate=48000:duration=4" if tone else "anullsrc=r=48000:cl=stereo"
    subprocess.run(
        [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", "color=c=white:s=320x180:d=4",
         "-f", "lavfi", "-i", f"{audio}:d=4" if tone else audio,
         "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(path)],
        check=True, timeout=120,
    )


@unittest.skipUnless(FFMPEG, "需要 ffmpeg")
class SilenceGate(unittest.TestCase):
    def run_gate(self, project: Path, video: Path) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), str(project), str(video)],
                              capture_output=True, text=True, timeout=300)

    def test_silent_gap_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = make_project(root, music=False)
            video = root / "v.mp4"
            make_video(video, tone=False)
            r = self.run_gate(project, video)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("句间安静", r.stdout)

    def test_continuous_music_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = make_project(root, music=False)
            video = root / "v.mp4"
            make_video(video, tone=True)
            r = self.run_gate(project, video)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("P0", r.stdout)

    def test_music_on_skips(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = make_project(root, music=True)
            video = root / "v.mp4"
            make_video(video, tone=True)
            r = self.run_gate(project, video)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("跳过", r.stdout)


if __name__ == "__main__":
    unittest.main()
