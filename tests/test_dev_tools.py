"""开发期入口的冒烟：scripts/dev/test-all.py（一条命令跑全部检查）与 component-usage.py（组件使用率报告）。"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*argv):
    r = subprocess.run([sys.executable, *argv], cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=110)
    return r.returncode, r.stdout + r.stderr


class TestAll(unittest.TestCase):
    def test_lists_every_step(self):
        rc, out = run("scripts/dev/test-all.py", "--list")
        self.assertEqual(rc, 0)
        self.assertEqual(out.split(), ["unittest", "collection", "selftest", "negative", "validate-skill",
                                       "links", "reuse", "tsc"])

    def test_unknown_step_is_usage_error(self):
        self.assertEqual(run("scripts/dev/test-all.py", "nope")[0], 2)

    def test_runs_a_fast_step(self):
        rc, out = run("scripts/dev/test-all.py", "links")
        self.assertEqual(rc, 0, out)
        self.assertIn("PASS  links", out)


class ComponentUsage(unittest.TestCase):
    def test_report_shape(self):
        rc, out = run("scripts/dev/component-usage.py", "--json")
        self.assertEqual(rc, 0, out)
        rows = json.loads(out)
        self.assertGreater(len(rows), 50)
        names = {r["component"] for r in rows}
        self.assertTrue({"FitTextBox", "Callout", "Corridor", "Chart"} <= names)
        self.assertFalse(any(n.endswith("Gate") for n in names), "门禁件不算组件")
        fit = next(r for r in rows if r["component"] == "FitTextBox")
        self.assertGreater(fit["blueprints"], 0)


if __name__ == "__main__":
    unittest.main()
