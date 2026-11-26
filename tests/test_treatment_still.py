"""treatment 写 move=still 时 compose 真的不推镜。

auto 路线真正渲染的运镜在 cinema.path：move=still 的镜不加推近、招牌镜、收束慢推，
镜头表的 intent 也由这条路径读出。
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
            s1 = next(s for s in shots if s["id"] == "S1")
            self.assertEqual(s1["camera"]["intent"], "still")
            path = s1["cinema"]["path"]  # 真正渲染的运镜在 cinema.path：整镜不推不移
            self.assertEqual({(k["x"], k["y"], k["s"]) for k in path}, {(path[0]["x"], path[0]["y"], path[0]["s"])})


if __name__ == "__main__":
    unittest.main()
