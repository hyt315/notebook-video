"""画面三层门禁：主题物必须出现。

用用户那部片的形态做回归夹具：讲火箭、全片却是字卡 / 柱条 / 对比卡（原片 29 张抽帧里没有一枚火箭）。
这条必须 P0 失败并点名「火箭」——旧版没有任何门禁，这种片子照样全绿。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "scripts" / "compose-story.py"
GATE = ROOT / "scripts" / "validate-fusion.py"


def build(story: Path, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(COMPOSE), str(story), str(out)],
                          capture_output=True, text=True, timeout=180)


class FusionGate(unittest.TestCase):
    def test_components_only_rocket_fails(self):
        with tempfile.TemporaryDirectory() as td:
            r = build(ROOT / "examples" / "regress" / "rocket-components-only.story.json", td)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            g = subprocess.run([sys.executable, str(GATE), td], capture_output=True, text=True, timeout=60)
            self.assertEqual(g.returncode, 1, g.stdout + g.stderr)
            self.assertIn("P0", g.stdout)
            self.assertIn("火箭", g.stdout)

    def test_sketch_story_passes_p0(self):
        with tempfile.TemporaryDirectory() as td:
            r = build(ROOT / "examples" / "recipes" / "rocket-fusion.story.json", td)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            g = subprocess.run([sys.executable, str(GATE), td], capture_output=True, text=True, timeout=60)
            self.assertEqual(g.returncode, 0, g.stdout + g.stderr)
            self.assertIn("含线稿", g.stdout)

    def test_abstract_exempt_with_reason(self):
        with tempfile.TemporaryDirectory() as td:
            story = json.loads((ROOT / "examples" / "regress" / "rocket-components-only.story.json").read_text(encoding="utf-8"))
            story["subject_of_film"] = "abstract"
            story["subject_why"] = "这一题讲的是复利这个观念，没有可画的具体东西。"
            sp = Path(td) / "story.json"
            sp.write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")
            proj = Path(td) / "proj"
            r = build(sp, proj)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            g = subprocess.run([sys.executable, str(GATE), proj], capture_output=True, text=True, timeout=60)
            self.assertEqual(g.returncode, 0, g.stdout + g.stderr)


if __name__ == "__main__":
    unittest.main()
