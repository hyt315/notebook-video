"""sweep 的采样点必须落在「落定态」，不是「入场帧」。

`sweep` 存在的理由就是补漏检（`preview` 只盖前 30 秒，尾巴从来没被量过），
所以它自己最容易犯的错是**量错帧**：

- 落到镜头开头 → 量的是入场空场，八镜全报空洞；
- 落到 15 的倍数以外 → FillGate 根本不采样，八镜全「通过」。

两种错都不会让命令失败，只会在屏幕上给出一张看着合理的表 —— 这正是这个项目
已经犯过三次的那类错（数字合理，但不是它声称的那个东西）。所以这里用 `--plan`
（纯计算，不起浏览器、不需要工程能跑）把规则钉死：

  每镜一个点 · 落在后半段 · 尽量靠后 · 优先落在 15 的网格上。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "notebook-video.mjs"
NODE = shutil.which("node")
GRID = 15


def shot(sid: str, start: int, end: int) -> dict:
    return {"id": sid, "from": start, "to": end, "duration": end - start}


@unittest.skipUnless(NODE, "node not installed")
class SweepPlan(unittest.TestCase):
    def plan(self, shots: list[dict], *extra: str, with_file: bool = True):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        if with_file:
            (root / "manifests").mkdir()
            (root / "manifests" / "shots.resolved.json").write_text(
                json.dumps({"duration": max((s["to"] for s in shots), default=0), "shots": shots}, ensure_ascii=False),
                encoding="utf-8",
            )
        return subprocess.run(
            [NODE, str(CLI), "sweep", str(root), "--plan", *extra],
            capture_output=True, text=True, timeout=120,
        )

    def picks(self, shots: list[dict], *extra: str) -> list[dict]:
        r = self.plan(shots, *extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)["picks"]

    # ── 落点 ────────────────────────────────────────────────────────────────
    def test_normal_shot_picks_last_grid_frame(self):
        # 115 帧的镜：切点前最近的网格帧是 105，落在后半段（中点 57 之后）
        [p] = self.picks([shot("S1", 0, 115)])
        self.assertEqual(p["frame"], 105)
        self.assertTrue(p["onGrid"])

    def test_shot_offset_is_respected(self):
        # 从 1000 开始的镜，采样点不能落回 0 附近（那是全片第一帧）
        [p] = self.picks([shot("S2", 1000, 1100)])
        self.assertEqual(p["frame"], 1095)
        self.assertTrue(p["onGrid"])

    def test_never_lands_in_the_first_half(self):
        for start, end in [(0, 115), (0, 32), (0, 47), (500, 560), (900, 1472)]:
            [p] = self.picks([shot("S", start, end)])
            midpoint = start + (end - 1 - start + 1) // 2
            self.assertGreaterEqual(p["frame"], midpoint, f"{start}-{end} 落到了前半段")

    def test_grid_frame_preferred_over_last_frame(self):
        # 后半段里有网格点就必须用网格点（否则 FillGate 不采样 → 零数据）
        [p] = self.picks([shot("S", 0, 32)])
        self.assertEqual(p["frame"], 30)
        self.assertEqual(p["frame"] % GRID, 0)
        self.assertTrue(p["onGrid"])

    # ── 短镜边界 ────────────────────────────────────────────────────────────
    def test_short_shot_does_not_pick_the_entry_frame(self):
        # 15 帧整的镜：唯一的网格点是 0（入场帧）。宁可退回末帧并标 onGrid=false，
        # 也不能量 0 —— 那必然是一个假空洞。
        [p] = self.picks([shot("S", 0, 15)])
        self.assertEqual(p["frame"], 14)
        self.assertFalse(p["onGrid"])

    def test_short_shot_uses_last_frame_when_no_grid_in_second_half(self):
        [p] = self.picks([shot("S", 100, 115)])
        self.assertEqual(p["frame"], 114)
        self.assertFalse(p["onGrid"])

    # ── 输入异常 ────────────────────────────────────────────────────────────
    def test_invalid_range_is_skipped_not_crashed(self):
        r = self.plan([shot("S1", 0, 100), {"id": "S2", "from": 200, "to": 200, "duration": 0}])
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual([p["id"] for p in data["picks"]], ["S1"])
        self.assertEqual([s["id"] for s in data["skipped"]], ["S2"])

    def test_picks_stay_ordered_and_unique(self):
        shots = [shot(f"S{i}", i * 100, i * 100 + 100) for i in range(1, 6)]
        picks = self.picks(shots)
        self.assertEqual([p["id"] for p in picks], [s["id"] for s in shots])
        frames = [p["frame"] for p in picks]
        self.assertEqual(frames, sorted(set(frames)))

    def test_missing_manifest_explains_what_to_run(self):
        r = self.plan([], with_file=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("resolve-shots", r.stderr + r.stdout)

    def test_typo_flag_is_rejected(self):
        # `--scal=0.3` 不能默默按 0.5 跑完 —— 那样你以为看的是 30%，其实是 50%
        r = self.plan([shot("S1", 0, 100)], "--scal=0.3")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--scal", r.stderr + r.stdout)

    def test_scale_out_of_range_is_rejected(self):
        for bad in ("0.05", "1.5", "abc"):
            r = self.plan([shot("S1", 0, 100)], f"--scale={bad}")
            self.assertEqual(r.returncode, 2, f"--scale={bad} 应该被拒")
            self.assertIn("--scale", r.stderr + r.stdout)

    # ── 落盘纪律 ────────────────────────────────────────────────────────────
    def test_window_renders_never_persist_coverage(self):
        """`preview` / `render-range` / `review-frames` 只量窗口，量到的是"窗口内最完整帧"，
        不是"整镜最完整帧"（实测 60 帧窗口把 S1 记成 25，整镜是 28）。留档会骗人。
        覆盖率落盘只有两个来源：整片 `render` 和 `sweep`。这里锁住这条纪律。"""
        cli = CLI.read_text(encoding="utf-8")

        def tail_of(fn_name: str) -> str:
            i = cli.index(f"const {fn_name} = async")
            j = cli.index("\n};", i)
            return cli[i:j]

        for fn in ("preview", "renderRange", "reviewFrames"):
            body = tail_of(fn)
            self.assertIn("persist: false", body, f"{fn} 不该把窗口覆盖率写进 fill-coverage.json")

        # 但渲染收尾本身要 still 能落盘（sweep 合并后统一写，整片 render 直接写）
        self.assertIn("if (persist) writeCoverage(cwd, coverage);", cli)


if __name__ == "__main__":
    unittest.main()
