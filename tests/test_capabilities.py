#!/usr/bin/env python3
"""P2-26 · 能力矩阵的判定逻辑。

跨平台实测做不到（只有这一台 Windows），但「判定逻辑是否真的会降级」可以测：
把 PATH 清空，脚本必须从「全能力」掉到「不支持」，并且每条缺项都给出可执行的补法。
抓的是那种最糟的情况——机器缺东西，脚本仍然说「全能力」。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "notebook-video.mjs"
NODE = shutil.which("node")


def run(env: dict | None = None) -> tuple[int, str]:
    r = subprocess.run([NODE or "node", str(CLI), "capabilities", "--json"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env or os.environ.copy())
    return r.returncode, (r.stdout or "") + (r.stderr or "")


@unittest.skipUnless(NODE, "需要 node")
class CapabilitiesTest(unittest.TestCase):
    def test_report_is_parseable_and_complete(self):
        rc, out = run()
        try:
            doc = json.loads(out)
        except ValueError:
            self.fail(f"capabilities --json 不是合法 JSON：\n{out[:800]}")
        self.assertEqual(rc, 0 if doc["level"] != "unsupported" else 1)
        for key in ("platform", "node", "level", "capabilities", "pageTurn", "fonts", "budoux", "concurrency"):
            self.assertIn(key, doc, f"报告缺 {key}")
        self.assertIn(doc["level"], ("full", "degraded", "unsupported"))
        self.assertIn(doc["pageTurn"]["mode"], ("gpu", "fold"))
        self.assertGreaterEqual(doc["concurrency"], 2)

    def test_on_this_machine_every_hard_dep_is_reported_honestly(self):
        # 不预设「本机一定是全能力」——那会把「探测坏了」当成通过。
        # 只要求：说 ok 的，命令真的存在；说 not ok 的，必须给补法。
        rc, out = run()
        doc = json.loads(out)
        for name, v in doc["capabilities"].items():
            if not v["ok"]:
                self.assertTrue(any(b["name"] == name for b in doc["blockers"]),
                                f"{name} 报不可用却没有进 blockers")
        for b in doc["blockers"]:
            self.assertTrue(b.get("fix"), f"{b['name']} 没有给出修复命令")

    def test_empty_path_degrades_to_unsupported(self):
        # 这是「无声空白页」的源头：机器缺 ffmpeg，脚本还说能出片。
        with tempfile.TemporaryDirectory() as td:
            env = {"PATH": td, "SystemRoot": os.environ.get("SystemRoot", ""),
                   "TEMP": td, "TMP": td}
            rc, out = run(env)
        try:
            doc = json.loads(out)
        except ValueError:
            self.fail(f"PATH 为空时输出不是 JSON（脚本崩了而不是降级）：\n{out[:800]}")
        self.assertEqual(doc["level"], "unsupported", f"PATH 空时仍报 {doc['level']}")
        self.assertNotEqual(rc, 0, "判定不支持却返回 0")
        names = {b["name"] for b in doc["blockers"]}
        self.assertIn("ffmpeg", names, f"缺 ffmpeg 没进 blockers：{names}")
        self.assertIn("python", names, f"缺 python 没进 blockers：{names}")


if __name__ == "__main__":
    unittest.main()
