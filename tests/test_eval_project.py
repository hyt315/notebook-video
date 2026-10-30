"""eval-project.py 的口径锁。

这个脚本最容易被"顺手改坏"的地方不是算法，而是**口径**：
把加权字数写成 `len()`，屏幕上是 3.0 还是 6.0 没人看得出来，但和 `silent-timing.py`
的 6.5 字/秒就不是同一个数了。所以这里锁住三件事：
  1. 加权：ASCII 字母/数字 0.5，汉字/标点 1（与 silent-timing / validate-presentation 同口径）；
  2. 没有空场读数时输出 None，而不是 0（0 会被读成"主体占比 0%"）；
  3. 两个工程并排时能给 Δ，且字段完全对齐。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval-project.py"


def make_project(root: Path, *, shots: list[dict], cues: list[dict], coverage: dict | None = None) -> Path:
    (root / "manifests").mkdir(parents=True)
    (root / "manifests" / "shots.resolved.json").write_text(json.dumps({
        "duration": sum(s["duration"] for s in shots),
        "shots": shots,
    }, ensure_ascii=False), encoding="utf-8")
    (root / "manifests" / "caption-cues.json").write_text(
        json.dumps({"cues": cues}, ensure_ascii=False), encoding="utf-8")
    if coverage is not None:
        (root / "renders").mkdir()
        (root / "renders" / "fill-coverage.json").write_text(
            json.dumps(coverage, ensure_ascii=False), encoding="utf-8")
    return root


def shot(**kw) -> dict:
    # 注意：`from` 是 Python 关键字，不能当关键字参数传——要改它只能用字典合并。
    base = {
        "id": "S1", "skeleton": "Stage", "media": ["text"], "live": ["HandNote"],
        "from": 0, "to": 90, "duration": 90, "transition": "hard",
        "keys": [{"f": 0, "s": 1.0}],
    }
    base.update(kw)
    return base


def at(start: int, end: int, **kw) -> dict:
    """造一个指定帧区间的镜头（`from` / `to` / `duration` 一起改，避免写漏）。"""
    return shot(**{"from": start, "to": end, "duration": end - start}, **kw)


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, encoding="utf-8")


class EvalProject(unittest.TestCase):
    def test_weighted_chars_per_second_matches_silent_timing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            # "GitHub" = 6 个 ASCII → 加权 3.0；时长 1 秒 → 3.0 字/秒（不是 6.0）
            proj = make_project(Path(td) / "p", shots=[shot()],
                                cues=[{"text": "GitHub", "start_ms": 0, "speech_end_ms": 1000}])
            out = run(str(proj), "--json")
            self.assertEqual(out.returncode, 0, out.stderr)
            m = json.loads(out.stdout)["A"]["metrics"]
            self.assertAlmostEqual(m["加权字/秒"], 3.0, places=2)

    def test_missing_coverage_is_none_not_zero(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(Path(td) / "p", shots=[shot()], cues=[])
            m = json.loads(run(str(proj), "--json").stdout)["A"]["metrics"]
            self.assertIsNone(m["空场:最小主体"], "没有读数必须是 None；0 会被读成'主体占 0%'")
            self.assertIsNone(m["空场:最大空白列"])

    def test_two_projects_line_up(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            a = make_project(Path(td) / "a", shots=[shot(), at(90, 180, id="S2")], cues=[])
            b = make_project(Path(td) / "b",
                             shots=[shot(), at(90, 180, id="S2"), at(180, 270, id="S3")],
                             cues=[], coverage={"S1": {"largest": "0.3", "blank": "0"}})
            out = run(str(a), str(b), "--json")
            self.assertEqual(out.returncode, 0, out.stderr)
            data = json.loads(out.stdout)
            self.assertEqual(set(data["A"]["metrics"]), set(data["B"]["metrics"]), "两版的指标字段必须完全对齐")
            self.assertEqual(data["A"]["metrics"]["镜数"], 2)
            self.assertEqual(data["B"]["metrics"]["镜数"], 3)
            self.assertIsNone(data["A"]["metrics"]["空场:最小主体"])
            self.assertAlmostEqual(data["B"]["metrics"]["空场:最小主体"], 0.3)

    def test_missing_shot_table_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = run(td)
            self.assertNotEqual(out.returncode, 0)
            self.assertIn("读不到镜头表", out.stderr)


if __name__ == "__main__":
    unittest.main()
