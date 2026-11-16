"""treatment 写 move=still 时 compose 真的不推镜。

背景：compose 先按版式给 1.00→1.025 的呼吸推，再按 treatment.shots[].move 改 intent；
改成 still 时 to 没跟着回到 1.0，validate-shot-motion 判 P0（still 镜头却放大 2.5%）。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
STORY = SKILL / "examples" / "concept-hash-table.story.json"


class StillMeansStill(unittest.TestCase):
    def test_still_move_keeps_scale(self):
        if not STORY.is_file():
            self.skipTest(f"缺示例 story：{STORY}")
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "manifests").mkdir()
            (Path(td) / "manifests" / "treatment.json").write_text(
                json.dumps({"shots": [{"id": "S1", "move": "still"}]}), encoding="utf-8")
            env = dict(os.environ, PYTHONIOENCODING="utf-8")
            r = subprocess.run([sys.executable, str(SKILL / "scripts" / "compose-story.py"), str(STORY), td,
                                "--report", str(Path(td) / "report.json")],
                               capture_output=True, text=True, encoding="utf-8", errors="ignore", env=env)
            self.assertEqual(r.returncode, 0, r.stderr[-800:])
            shots = json.loads((Path(td) / "manifests" / "shots.json").read_text(encoding="utf-8"))
            shots = shots["shots"] if isinstance(shots, dict) else shots
            cam = next(s for s in shots if s["id"] == "S1")["camera"]
            self.assertEqual(cam["intent"], "still")
            self.assertEqual(cam["from"], cam["to"])


if __name__ == "__main__":
    unittest.main()
