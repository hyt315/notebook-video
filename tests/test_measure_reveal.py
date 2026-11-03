"""T-P1-06：scripts/measure-reveal.py 的静态指标（same / gap / conc / pre）。

用手造的 story.ts 而不是跑 compose：这两个指标是纯函数，输入固定才谈得上判据。
G 部分需要真视频，放端到端验收里量，不在这里造假帧。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "measure-reveal.py"

STORY = {
    "S1": {
        "elements": [
            {"id": "a", "at": 0, "dur": 60},
            {"id": "b", "at": 0, "dur": 60},
            {"id": "c", "at": 6, "dur": 60},
        ],
        "lineEnds": [80],
        "lines": ["一"],
    },
    "S2": {
        "elements": [{"id": "d", "at": 0, "dur": 20}],
        "lineEnds": [80],
        "lines": ["二"],
    },
}


def run(story: dict) -> dict:
    with tempfile.TemporaryDirectory() as td:
        project = Path(td)
        (project / "src").mkdir()
        (project / "src" / "story.ts").write_text(
            "export const STORY = " + json.dumps(story, ensure_ascii=False) + ";\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(TOOL), str(project), "--json"],
                           capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, r.stdout + r.stderr
        payload = json.loads([l for l in r.stdout.splitlines() if l.startswith("{")][-1])
        return {row["shot"]: row for row in payload["static"]}


class StaticMetrics(unittest.TestCase):
    def setUp(self):
        self.rows = run(STORY)

    def test_same_frame_starts_are_counted(self):
        # a、b 都在第 0 帧开始 → 同帧最大数 2
        self.assertEqual(self.rows["S1"]["same"], 2)

    def test_smallest_gap_is_reported(self):
        # 0 / 0 / 6：两个元素同帧开始，最小间隔就是 0（这正是「扎堆」要报的信号）
        self.assertEqual(self.rows["S1"]["gap"], 0)
        # 只有一记的镜头没有相邻间隔，按定义记 99（不参与 gap<12 的统计）
        self.assertEqual(self.rows["S2"]["gap"], 99)

    def test_concurrent_growth_is_counted(self):
        # 第 10 帧时三个元素同时在长
        self.assertEqual(self.rows["S1"]["conc"], 3)

    def test_pre_roll_counts_elements_started_before_frame_6(self):
        self.assertEqual(self.rows["S1"]["pre"], 2)
        self.assertEqual(self.rows["S2"]["pre"], 1)

    def test_clean_shot_has_no_problems(self):
        self.assertEqual(self.rows["S2"]["same"], 1)
        self.assertEqual(self.rows["S2"]["conc"], 1)


class HandwrittenProject(unittest.TestCase):
    def test_project_without_story_ts_is_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run([sys.executable, str(TOOL), td], capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 0, "只报告的工具不该因缺少 story.ts 退出非零")
            self.assertIn("手写场景工程没有 story.ts", r.stdout)


if __name__ == "__main__":
    unittest.main()
