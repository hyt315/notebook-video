"""冷开：第一镜最先出现的元素在第 0 帧已经落定（validate-opening O6：手作皮肤 P0、组件皮肤 P1）。

背景：auto 路线的元素都挂在台词上入场，第一镜第一个元素最早也要第 3 帧才开始展开，
第 0 帧只有底纸和页眉（实测非背景像素 3.2% < 8%），手作皮肤成片必挂 O6。
组件皮肤同样适用（第 0 帧只有空背景，等于开场半秒的空镜）；冷开的第一镜以全景起幅。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
STORY = SKILL / "examples" / "concept-hash-table.story.json"


def compose(skin: str | None) -> dict:
    with tempfile.TemporaryDirectory() as td:
        if skin:
            (Path(td) / "src" / "theme").mkdir(parents=True)
            (Path(td) / "src" / "theme" / "active.ts").write_text(
                f"import {{THEME}} from './{skin}';\nexport {{THEME}};\n", encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "compose-story.py"), str(STORY), td,
                            "--report", str(Path(td) / "report.json")],
                           capture_output=True, text=True, encoding="utf-8", errors="ignore", env=env)
        if r.returncode:
            raise AssertionError(r.stderr[-800:])
        ts = (Path(td) / "src" / "story.ts").read_text(encoding="utf-8")
    m = re.search(r'"S1":(\{.*?"icons":\d+\})', ts, re.S)
    return json.loads(m.group(1))


def compose_shot(skin: str | None) -> dict:
    """第一镜在 manifests/shots.json 里的记录（含相机路径）。"""
    with tempfile.TemporaryDirectory() as td:
        if skin:
            (Path(td) / "src" / "theme").mkdir(parents=True)
            (Path(td) / "src" / "theme" / "active.ts").write_text(
                f"import {{THEME}} from './{skin}';\nexport {{THEME}};\n", encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "compose-story.py"), str(STORY), td,
                            "--report", str(Path(td) / "report.json")],
                           capture_output=True, text=True, encoding="utf-8", errors="ignore", env=env)
        if r.returncode:
            raise AssertionError(r.stderr[-800:])
        shots = json.loads((Path(td) / "manifests" / "shots.json").read_text(encoding="utf-8"))["shots"]
    return shots[0]


class ColdOpen(unittest.TestCase):
    def setUp(self):
        if not STORY.is_file():
            self.skipTest(f"缺示例 story：{STORY}")

    def test_handmade_first_element_settled_at_frame0(self):
        els = compose("archive")["elements"]
        self.assertTrue(any(e["at"] < 0 for e in els), [e["at"] for e in els])

    def test_flat_first_element_settled_at_frame0(self):
        # 组件皮肤同样冷开：第一镜最先出现的那个元素提前落定，其余元素照常按台词出现
        els = compose(None)["elements"]
        early = [e for e in els if e["at"] < 0]
        self.assertEqual(len(early), 1, [e["at"] for e in els])
        self.assertTrue(all(e["at"] >= 0 for e in els if e is not early[0]), [e["at"] for e in els])

    def test_cold_open_first_shot_starts_wide(self):
        # 冷开的第一镜以全景 1.00× 起幅（题眼在第 0 帧完整入画），往里推交给关键词运镜
        for skin in (None, "archive"):
            with self.subTest(skin=skin or "flat"):
                path = compose_shot(skin)["cinema"]["path"]
                self.assertEqual((path[0]["at"], path[0]["s"]), (0, 1.0), path)


if __name__ == "__main__":
    unittest.main()
