#!/usr/bin/env python3
"""P0-04：渲染锁与 raw 内容指纹的行为测试。

锁是为了挡住「两个进程写同一个 raw」，指纹是为了不再用 mtime 判断「输入变了没有」。
两条都必须能脱离 Remotion 验证——所以逻辑在 scripts/render-lock.mjs，探针只调它。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "notebook-video.mjs"
LOCK = ROOT / "scripts" / "render-lock.mjs"
PROBE = ROOT / "tests" / "fixtures" / "render_lock_probe.mjs"


class RenderLockTest(unittest.TestCase):
    def test_probe(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node 不可用")
        r = subprocess.run([node, str(PROBE)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("5/5 OK", r.stdout)

    def test_resume_no_longer_reads_mtime(self):
        """文档点名的旧实现：`--resume` 只比最新 mtime。它挡不住「内容回退但 mtime 更早」。"""
        src = CLI.read_text(encoding="utf-8")
        self.assertNotIn("newestInputMtime", src)
        self.assertIn("inputFingerprint(project)", src)
        self.assertIn("canResume({manifest:", src)

    def test_render_takes_lock_before_touching_project(self):
        """锁必须在 sync / 字体 / 渲染之前：sync 会写工程文件，那一步本身就有竞态。"""
        src = CLI.read_text(encoding="utf-8")
        self.assertIn("takeRenderLock(project, output)", src)
        lock = src.index("takeRenderLock(project, output)")
        self.assertLess(lock, src.index("await syncProjectAssets([project]);", lock), "锁必须在 sync 之前")
        self.assertLess(lock, src.index("await remotionRender({project", lock), "锁必须在渲染之前")

    def test_manifest_states_are_written(self):
        src = CLI.read_text(encoding="utf-8")
        for state in ("'running'", "'raw-complete'", "'delivered'", "'failed'"):
            self.assertIn(state, src, state)

    def test_lock_module_is_pure_node(self):
        """不许为了加锁引入依赖：这个模块只有 node 内置 import。"""
        src = LOCK.read_text(encoding="utf-8")
        for line in src.splitlines():
            if line.startswith("import "):
                self.assertIn("node:", line, line)
        mods = json.loads((ROOT / "assets" / "lecture-template" / "package.json").read_text(encoding="utf-8"))
        self.assertNotIn("proper-lockfile", json.dumps(mods))


if __name__ == "__main__":
    unittest.main()
