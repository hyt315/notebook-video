"""P1-07：旁白从「按 mtime 猜新旧」升级为「按内容指纹核对」。

三种错法这条测试各钉一遍：
  1. 旧文本被重新保存 → mtime 更新 → 旧检查放行（内容其实没变，不该拦；内容变了才该拦）；
  2. 改了 narration.txt 但没重跑 compose → 新检查必须拦，并指出第几行；
  3. `--engine=file` 按字数均分，会把实测时间轴换成估计值 → 必须显式确认且留备份。
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
SCRIPTS = ROOT / "scripts"
TTS = SCRIPTS / "tts.py"
COMPOSE = SCRIPTS / "compose-story.py"
FFMPEG = shutil.which("ffmpeg")

sys.path.insert(0, str(SCRIPTS))
import narration_contract as nc  # noqa: E402


class ContractUnitTest(unittest.TestCase):
    def test_normalization_ignores_whitespace_noise(self):
        a = nc.sha("第一句。\n第二句。\n")
        b = nc.sha("第一句。   \n\n第二句。")       # 行尾空格 + 末尾空行 + 无结尾换行
        self.assertEqual(a, b, "格式化噪声不该被当成改稿")
        self.assertNotEqual(a, nc.sha("第一句。\n第三句。\n"))

    def test_first_diff_points_at_the_line(self):
        d = nc.first_diff("甲\n乙\n丙\n", "甲\n乙改\n丙\n")
        self.assertFalse(d["same"])
        self.assertEqual(d["line"], 2)
        self.assertIn("第 2 行", nc.describe(d))
        self.assertIn("乙改", nc.describe(d))

    def test_first_diff_handles_added_and_removed_lines(self):
        self.assertEqual(nc.first_diff("甲\n", "甲\n乙\n")["line"], 2)
        self.assertEqual(nc.first_diff("甲\n乙\n", "甲\n")["line"], 2)
        self.assertTrue(nc.first_diff("甲\n", "甲\n")["same"])

    def test_same_algorithm_for_writer_and_reader(self):
        """compose 与 tts 必须用同一份实现，否则"指纹不同"会是假警报。"""
        compose_src = COMPOSE.read_text(encoding="utf-8")
        tts_src = TTS.read_text(encoding="utf-8")
        for src in (compose_src, tts_src):
            self.assertIn("narration_contract", src)
        self.assertNotIn("def narration_sha(", compose_src, "指纹算法不能在 compose 里再实现一份")


class ContractWiringTest(unittest.TestCase):
    def test_compose_writes_the_contract(self):
        story = ROOT / "examples" / "recipes" / "jie-freeform.story.json"
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run([sys.executable, str(COMPOSE), str(story), td],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=180, cwd=ROOT)
            self.assertEqual(r.returncode, 0, r.stdout[-1500:] + r.stderr[-800:])
            doc = json.loads((Path(td) / "manifests" / "narration.contract.json").read_text(encoding="utf-8"))
            text = (Path(td) / "narration.txt").read_text(encoding="utf-8")
            self.assertEqual(doc["text_sha256"], nc.sha(text))
            self.assertEqual(doc["lines"], len([x for x in text.splitlines() if x.strip()]))
            self.assertEqual(doc["text"], [x for x in text.splitlines() if x.strip()],
                             "契约要留文本快照，否则报错时说不清第几行")


@unittest.skipUnless(FFMPEG, "需要 ffmpeg 生成占位音频")
class StaleGateTest(unittest.TestCase):
    def _project(self, td: str, text: str) -> Path:
        project = Path(td)
        (project / "audio").mkdir()
        (project / "narration.txt").write_text(text, encoding="utf-8")
        (project / "story.json").write_text("{}", encoding="utf-8")
        subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                        "-i", "anullsrc=r=48000:cl=mono", "-t", "2", "-q:a", "9",
                        str(project / "audio" / "narration.mp3")], check=True, timeout=60)
        nc.write(project, text, source="compose-story")
        return project

    def _run(self, project: Path, *flags: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(TTS), str(project), "--engine=file", *flags],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=180)

    def test_changed_text_is_blocked_with_the_diff(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._project(td, "第一句。\n第二句。\n")
            (p / "narration.txt").write_text("第一句。\n第二句改了。\n", encoding="utf-8")
            r = self._run(p)
            self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
            self.assertIn("不一致", r.stderr)
            self.assertIn("第 2 行", r.stderr, "报错要指到具体行，不能只说「请重跑」")
            self.assertIn("compose-story.py", r.stderr)

    def test_newer_mtime_with_same_content_passes(self):
        """真正的改进：内容没变就不该拦，哪怕 story.json 更新（checkout 会刷新 mtime）。"""
        with tempfile.TemporaryDirectory() as td:
            p = self._project(td, "第一句。\n第二句。\n")
            (p / "story.json").write_text('{"v": 2}', encoding="utf-8")   # 比 narration.txt 新
            r = self._run(p)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_allow_stale_is_an_explicit_bypass(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._project(td, "第一句。\n")
            (p / "narration.txt").write_text("完全换了内容。\n", encoding="utf-8")
            r = self._run(p, "--allow-stale")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("--allow-stale", r.stdout, "绕过必须说出来，不能静默通过")
            meta = json.loads((p / "audio" / "narration.meta.json").read_text(encoding="utf-8"))
            self.assertTrue(meta["allow_stale"])


@unittest.skipUnless(FFMPEG, "需要 ffmpeg 生成占位音频")
class FileEngineTimelineTest(unittest.TestCase):
    def _project(self, td: str) -> Path:
        p = Path(td)
        (p / "audio").mkdir()
        (p / "narration.txt").write_text("第一句。\n", encoding="utf-8")
        subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                        "-i", "anullsrc=r=48000:cl=mono", "-t", "2", "-q:a", "9",
                        str(p / "audio" / "narration.mp3")], check=True, timeout=60)
        (p / "audio" / "narration.mp3.json").write_text(
            json.dumps([{"part": "第", "start": 0, "end": 100}], ensure_ascii=False), encoding="utf-8")
        (p / "audio" / "narration.meta.json").write_text(
            json.dumps({"engine": "edge", "timeline": "measured", "estimated": False}), encoding="utf-8")
        return p

    def test_estimated_timeline_never_overwrites_measured_silently(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._project(td)
            before = (p / "audio" / "narration.mp3.json").read_text(encoding="utf-8")
            r = subprocess.run([sys.executable, str(TTS), str(p), "--engine=file", "--allow-stale"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
            self.assertIn("实测", r.stderr)
            self.assertEqual((p / "audio" / "narration.mp3.json").read_text(encoding="utf-8"), before,
                             "被拦下时不能改动原文件")

    def test_force_estimate_backs_up_the_old_timeline(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._project(td)
            r = subprocess.run([sys.executable, str(TTS), str(p), "--engine=file",
                                "--allow-stale", "--force-estimate"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            backups = list((p / "audio").glob("narration.mp3.json.bak-*"))
            self.assertEqual(len(backups), 1, "改写时间轴必须留备份")
            meta = json.loads((p / "audio" / "narration.meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["timeline"], "estimated")
            # Windows 短路径（RUNNER~1）vs 长路径（runneradmin）：解析后比较
            self.assertEqual(Path(meta["backup"]).resolve(), backups[0].resolve())
            self.assertIn("按字数均分", r.stdout, "估计时间轴必须在输出里说清楚")


if __name__ == "__main__":
    unittest.main()
