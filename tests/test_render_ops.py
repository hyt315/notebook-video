#!/usr/bin/env python3
"""分阶段耗时记录：失败之后还能查「慢在哪、断在哪一步」。

不靠渲染一遍整片来验证：逻辑在 render-log.mjs，探针只调它（不 import Remotion）。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CLI = SCRIPTS / "notebook-video.mjs"
PROBE = ROOT / "tests" / "fixtures" / "render_ops_probe.mjs"


class RenderOpsProbeTest(unittest.TestCase):
    def test_probe(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node 不可用")
        r = subprocess.run([node, str(PROBE)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180,
                           env={**__import__("os").environ, "NV_SCRIPTS": str(SCRIPTS)})
        self.assertEqual(r.returncode, 0, r.stdout[-3000:] + r.stderr[-2000:])
        payload = json.loads(r.stdout[r.stdout.index("{"):])
        self.assertTrue(payload["ok"], payload)
        self.assertGreaterEqual(payload["total"], 12, "探针检查项太少，可能没跑全")


class RenderLogWiringTest(unittest.TestCase):
    def test_every_stage_is_timed(self):
        """阶段名是报告的分组键：改渲染流程时忘了包 stage()，报告里就会少一段。"""
        src = CLI.read_text(encoding="utf-8")
        for name in ("prepare", "fx-probe", "fingerprint", "loudprobe", "finalize"):
            self.assertIn(f"stage('{name}'", src, f"{name} 没被计时")
        self.assertIn("stage('render'", src)

    def test_failure_is_logged_not_only_printed(self):
        src = CLI.read_text(encoding="utf-8")
        self.assertIn("flushRunLog()", src)
        self.assertIn("appendRunLog(RUN.project", src)
        # 退出钩子里必须调用：fail() 是 process.exit，只有 exit 事件能保证收尾
        exit_hook = src[src.index("process.once('exit'"):]
        exit_hook = exit_hook[:exit_hook.index("release();")]
        self.assertIn("flushRunLog()", exit_hook)

    def test_four_exit_kinds_are_distinguishable(self):
        src = (SCRIPTS / "render-log.mjs").read_text(encoding="utf-8")
        for kind in ("cancelled", "stalled", "process-error", "ok"):
            self.assertIn(kind, src)
        cli = CLI.read_text(encoding="utf-8")
        self.assertIn("EXIT_INFO.signal = sig", cli, "信号退出必须与失败区分（Ctrl-C 不是缺陷）")
        self.assertIn("EXIT_INFO.stalled = true", cli, "看门狗中止必须有自己的归因")

    def test_timings_command_reads_the_same_file(self):
        src = CLI.read_text(encoding="utf-8")
        self.assertIn("case 'timings': return timings(args);", src)
        self.assertIn("RUN_LOG_REL", src)


if __name__ == "__main__":
    unittest.main()
