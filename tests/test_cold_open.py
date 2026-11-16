"""手作皮肤冷开：第一镜最先出现的元素在第 0 帧已经落定（validate-opening O6，手作皮肤 P0）。

背景：auto 路线的元素都挂在台词上入场，第一镜第一个元素最早也要第 3 帧才开始展开，
第 0 帧只有底纸和页眉（实测非背景像素 3.2% < 8%），手作皮肤成片必挂 O6。
flat / cel 不动（O6 对它们只是提示，已交付片的时间轴不改）。
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


class ColdOpen(unittest.TestCase):
    def setUp(self):
        if not STORY.is_file():
            self.skipTest(f"缺示例 story：{STORY}")

    def test_handmade_first_element_settled_at_frame0(self):
        els = compose("archive")["elements"]
        self.assertTrue(any(e["at"] < 0 for e in els), [e["at"] for e in els])

    def test_flat_unchanged(self):
        els = compose(None)["elements"]
        self.assertTrue(all(e["at"] >= 0 for e in els), [e["at"] for e in els])


if __name__ == "__main__":
    unittest.main()
