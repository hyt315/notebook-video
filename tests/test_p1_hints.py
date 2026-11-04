"""3.5.2：make-video 的 P1 建议收集必须认全三种明细行，且不误收汇总行。

只测「哪些建议被写进 report.md」，不碰门禁判据。收集逻辑在 scripts/p1-hints.mjs，
这里通过 Node 子进程跑真实实现，避免用另一套正则复刻一遍（那样测不到真东西）。
"""
import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")
SCRIPT = """
import {collectP1} from './scripts/p1-hints.mjs';
import fs from 'node:fs';
const d = JSON.parse(fs.readFileSync(0, 'utf8'));
console.log(JSON.stringify(collectP1(d.out, d.gate)));
"""


def collect(out: str, gate: str = "validate-backgrounds.py") -> list:
    r = subprocess.run(
        [NODE or "node", "--input-type=module", "-e", SCRIPT],
        input=json.dumps({"out": out, "gate": gate}, ensure_ascii=False),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT), env=os.environ.copy(), timeout=60,
    )
    assert r.returncode == 0, r.stderr[-400:]
    return json.loads(r.stdout.strip())


@unittest.skipUnless(NODE, "需要 Node")
class CollectP1(unittest.TestCase):
    def test_tagged_line_keeps_issue_only(self):
        # presentation / composition / shot-motion / facts 的写法（原正则唯一认得的一种）
        self.assertEqual(
            collect("  P1 G-5: 好几件事挤在一拍上\n", "validate-presentation.py"),
            ["validate-presentation：好几件事挤在一拍上"])

    def test_plain_line_is_not_truncated(self):
        # backgrounds / audio-levels / fusion / frame-props：无冒号，中文开头
        self.assertEqual(
            collect("  P1 分镜相邻两镜同一张背景（--shots）\n", "validate-backgrounds.py"),
            ["validate-backgrounds：分镜相邻两镜同一张背景（--shots）"])

    def test_bullet_prefix(self):
        # media / opening / treatment：`  · P1 ...`
        self.assertEqual(
            collect("  · P1 中央 70 % 起伏 > 0.05：背景会和内容抢\n", "validate-opening.py"),
            ["validate-opening：中央 70 % 起伏 > 0.05：背景会和内容抢"])
        self.assertEqual(
            collect("  · P1 中央 70 % 起伏\n", "validate-opening.py"),
            ["validate-opening：中央 70 % 起伏"])

    def test_fullwidth_colon_tag(self):
        self.assertEqual(
            collect("  P1 G-2：读速偏快\n", "validate-presentation.py"),
            ["validate-presentation：读速偏快"])

    def test_number_leading_line_loses_nothing(self):
        # 行首是数字时不能被 TAGGED 误当成编号吃掉
        self.assertEqual(
            collect("  P1 13–15（低于标注 16 档）\n"),
            ["validate-backgrounds：13–15（低于标注 16 档）"])

    def test_summary_lines_are_not_hints(self):
        out = ("结论：P0=0 P1=3 → PASS\n"
               "validate-backgrounds：通过（P0 0，P1 3）\n"
               "validate-media · 没有 manifests/media.json（本片不用真实素材）\n")
        self.assertEqual(collect(out), [])

    def test_mixed_and_empty(self):
        out = ("  P1 A-1: 第一条\n  P1 第二条\n  · P1 第三条\n结论：P0=0 P1=3 → PASS\n")
        self.assertEqual(collect(out, "g.py"), ["g：第一条", "g：第二条", "g：第三条"])
        self.assertEqual(collect("", "g.py"), [])


if __name__ == "__main__":
    unittest.main()
