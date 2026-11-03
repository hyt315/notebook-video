#!/usr/bin/env python3
"""poster / deliver 的存在性测试。

之前 `poster` 在 usage、dispatch 和 `deliver` 里都被引用，但函数从来没定义——
一调用就 `ReferenceError: poster is not defined`。这不是「功能没做完」，是「命令挂在那里但必崩」。
这里用**调用级**断言把它钉住：只要再把函数删掉，usage 会变回 exit 1。
"""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "notebook-video.mjs"
TPL = ROOT / "assets" / "lecture-template"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    node = shutil.which("node")
    if not node:
        raise unittest.SkipTest("node 不可用")
    return subprocess.run([node, str(CLI), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)


class PosterCommandTest(unittest.TestCase):
    def test_poster_without_project_prints_usage(self):
        r = run_cli("poster")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("Usage: notebook-video poster", r.stdout + r.stderr)

    def test_deliver_without_project_prints_usage(self):
        r = run_cli("deliver")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("Usage: notebook-video deliver", r.stdout + r.stderr)

    def test_frame_and_shot_are_mutually_exclusive(self):
        r = run_cli("poster", str(TPL), "--frame=10", "--shot=S1")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("只能给一个", r.stdout + r.stderr)

    def test_unknown_flag_is_rejected(self):
        r = run_cli("poster", str(TPL), "--frames=10")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("不认这些参数", r.stdout + r.stderr)


class PosterWiringTest(unittest.TestCase):
    def test_poster_is_defined_and_called_by_deliver(self):
        src = CLI.read_text(encoding="utf-8")
        self.assertIn("const poster = async", src)
        self.assertIn("await poster([project]);", src)
        self.assertLess(src.index("const poster = async"), src.index("const deliver = async"))

    def test_poster_hides_captions(self):
        """封面上的字幕是重影——必须走 composition 的 hideCaptions，而不是后期裁掉。

        3.9.0 起 props 走 buildPropsArg 合并（hideCaptions / nvFx / nvReducedMotion 各有来源，
        --props 只接受一次，内联字面量会让后写的覆盖先写的），所以锁的是「hideCaptions 进 props 对象」。
        """
        src = CLI.read_text(encoding="utf-8")
        self.assertIn("const props = {hideCaptions: true};", src)
        self.assertIn("buildPropsArg(props)", src)
        self.assertNotIn('--props={"hideCaptions":true}', src, "不该退回内联字面量——那会和 fx/reduced-motion 的 props 打架")

    def test_poster_and_sweep_share_the_settled_frame_rule(self):
        """落定帧只能有一份规则：两处各写一遍，迟早一个改了一个没改。"""
        src = CLI.read_text(encoding="utf-8")
        self.assertIn("const settledFrame = (shot)", src)
        self.assertEqual(src.count("const settledFrame"), 1)
        sweep = src[src.index("const sweepFrames"):src.index("const sweepFrames") + 600]
        self.assertIn("settledFrame(s)", sweep)


if __name__ == "__main__":
    unittest.main()
