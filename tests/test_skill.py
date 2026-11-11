#!/usr/bin/env python3
"""Standard regression test entry point for notebook-video.

3.5.4：此前只是一个 `main()` 脚本，`unittest discover` 收集到 0 条，从未在单测里运行。
现包成 TestCase：跑 `scripts/selftest.py`，rc≠0 即失败，并把输出尾部带进失败信息。
仍可直接 `python tests/test_skill.py` 运行。
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_selftest() -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "selftest.py")],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class SelftestTest(unittest.TestCase):
    def test_selftest_passes(self):
        proc = run_selftest()
        self.assertEqual(proc.returncode, 0,
                         f"selftest rc={proc.returncode}\n{(proc.stdout + proc.stderr)[-3000:]}")


if __name__ == "__main__":
    unittest.main()
