#!/usr/bin/env python3
"""P1-13 / P1-14：分阶段耗时记录 + 卷页管线的失败清理与保留。

为什么这两条要一起测：它们都在回答同一个问题——**失败之后还能不能查**。
耗时日志负责"慢在哪、断在哪一步"，管线的保留策略负责"现场还在不在"。
两条都不应该靠渲染一遍整片来验证，所以逻辑都在 render-log.mjs / fx-pipeline.mjs，
探针只调它们（不 import Remotion）。
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
        self.assertGreaterEqual(payload["total"], 30, "探针检查项太少，可能没跑全")


class RenderLogWiringTest(unittest.TestCase):
    def test_every_stage_is_timed(self):
        """阶段名是报告的分组键：改渲染流程时忘了包 stage()，报告里就会少一段。"""
        src = CLI.read_text(encoding="utf-8")
        for name in ("prepare", "fx-probe", "fingerprint", "loudprobe", "finalize"):
            self.assertIn(f"stage('{name}'", src, f"{name} 没被计时")
        self.assertIn("stage('fast'", src)
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


class FxPipelineWiringTest(unittest.TestCase):
    def test_render_uses_the_pipeline_instead_of_inline_code(self):
        src = CLI.read_text(encoding="utf-8")
        self.assertIn("runFxPipeline({", src)
        self.assertIn("FxStageError", src)
        # 旧的"出错只留一句 fail"必须消失：它不说是哪一步、现场在哪
        self.assertNotIn("卷页片段打包失败（尚未开始片段渲染）。", src)

    def test_temp_dirs_are_pruned_on_start(self):
        src = CLI.read_text(encoding="utf-8")
        self.assertIn("pruneFxTemp(", src)
        self.assertIn("const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), FX_TMP_PREFIX));", src)

    def test_retention_policy_is_documented_where_it_runs(self):
        src = (SCRIPTS / "fx-pipeline.mjs").read_text(encoding="utf-8")
        self.assertIn("export const FX_RETAIN_HOURS = 24;", src)
        self.assertIn("保留期内的目录**不能**删", src)


if __name__ == "__main__":
    unittest.main()
