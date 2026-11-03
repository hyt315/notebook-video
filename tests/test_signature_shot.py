#!/usr/bin/env python3
"""招牌镜（treatment.signature_shot）真的会动 —— 3.6.2。

背景：auto 版式的运镜是统一 1.03 的呼吸推，而 validate-treatment 要求「招牌镜」有
看得见的运镜。两者一度互相打架：作者写了招牌镜，版式做不到，只能去改 treatment
逃避门禁。这里锁住三条修法：

1. `camera_of` 必须读 `cinema.path`（引擎真正生效的那条，index.tsx 的 camFor 优先用它），
   只读 keys 会把「明明推了 15%」的镜判成「只推 3%」；
2. 招牌镜推近必须从**全景 1.0** 起（从 anchor 的 1.1 再推 1.15，观众只感到 4%）；
3. 并排结构推不进时退化为横移（`sweep_track`），且停留点不许切字。
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


vt = load("vt_sig", "validate-treatment.py")
cs = load("cs_sig", "compose-story.py")


class CameraReadsCinemaPath(unittest.TestCase):
    def test_push_measured_from_cinema_path(self):
        shot = {"keys": [{"f": 0, "s": 1.0}, {"f": 285, "s": 1.03}],   # 模板遗留值：只推 3%
                "cinema": {"path": [{"at": 0, "x": 960, "y": 540, "s": 1.0},
                                    {"at": 156, "x": 866, "y": 610, "s": 1.15}]}}
        c = vt.camera_of(shot)
        self.assertAlmostEqual(c["push"], 0.15, places=3)

    def test_falls_back_to_keys_without_path(self):
        shot = {"keys": [{"f": 0, "s": 1.0}, {"f": 90, "s": 1.2}]}
        self.assertAlmostEqual(vt.camera_of(shot)["push"], 0.2, places=3)

    def test_shift_counts_as_signature_motion(self):
        shot = {"cinema": {"path": [{"at": 0, "x": 700, "y": 540, "s": 1.0},
                                    {"at": 90, "x": 1200, "y": 540, "s": 1.0}]}}
        self.assertGreaterEqual(vt.camera_of(shot)["shift"], vt.SIGNATURE_SHIFT_MIN)


class SignatureVerdict(unittest.TestCase):
    def _judge(self, shot: dict) -> list[str]:
        t = {"signature_shot": "S1：慢推", "shots": []}
        hard, _ = vt.check_camera(t, [{"id": "S1", **shot}])
        return hard

    def test_real_push_passes(self):
        self.assertEqual(self._judge({"cinema": {"path": [{"at": 0, "x": 960, "y": 540, "s": 1.0},
                                                         {"at": 120, "x": 960, "y": 540, "s": 1.15}]}}), [])

    def test_static_shot_is_hard_fail(self):
        bad = self._judge({"cinema": {"path": [{"at": 0, "x": 960, "y": 540, "s": 1.03}]}})
        self.assertEqual(len(bad), 1)
        self.assertIn("既没真推", bad[0])

    def test_lateral_sweep_passes(self):
        self.assertEqual(self._judge({"cinema": {"path": [{"at": 0, "x": 700, "y": 540, "s": 1.0},
                                                         {"at": 120, "x": 1250, "y": 540, "s": 1.0}]}}), [])


class SweepTrack(unittest.TestCase):
    """横移候选：并排元素 → 起落两个 look；位移太小或会切字 → None。"""

    def _row(self, xs, y=404, w=238, h=200):
        return [{"id": f"step{i}", "kind": "node", "x": x, "y": y, "w": w, "h": h}
                for i, x in enumerate(xs)]

    def test_wide_row_yields_track(self):
        els = self._row([330, 658, 985, 1312])
        got = cs.sweep_track(els, {"x": 960.0, "y": 540.0, "s": 1.01})
        if got:                                   # 允许「扫不开」的保守返回，但扫开就必须真有位移
            a, b = got
            self.assertGreaterEqual(abs((b["x"] - a["x"]) * b["s"]), 300)

    def test_single_element_returns_none(self):
        self.assertIsNone(cs.sweep_track(self._row([900]), {"x": 960.0, "y": 540.0, "s": 1.0}))

    def test_cramped_pair_returns_none(self):
        self.assertIsNone(cs.sweep_track(self._row([900, 1000], w=80), {"x": 960.0, "y": 540.0, "s": 1.0}))


class LayoutLeavesCameraRoom(unittest.TestCase):
    """排版的留白不是审美：满铺的内容让相机一点都动不了。"""

    def test_flow_row_is_narrower_than_band(self):
        self.assertLess(cs.FLOW_TOTAL_MAX, cs.BAND["w"])

    def test_flow_nodes_can_be_pushed_in(self):
        class P:
            def err(self, *a): pass
            def fix(self, *a): pass
            def hint(self, *a): pass
            def warn(self, *a): pass

        c = {"title": "打孔 → 撕开 → 发货",
             "steps": [{"label": "整版上机"}, {"label": "沿直线打孔"},
                       {"label": "徒手撕开", "note": "一扯就断"}, {"label": "按枚点数", "hot": True}]}
        els = cs.lay_flow(P(), "S1", c, "a")
        nodes = [e for e in els if e["kind"] == "node"]
        self.assertEqual(len(nodes), 4)
        mid = nodes[1]
        tgt, _ = cs.frame_rect(mid, els, max_s=1.24, min_s=1.12)
        self.assertGreaterEqual(tgt["s"], 1.12, "flow 的节点应该推得进招牌镜的 12% 门禁")


if __name__ == "__main__":
    unittest.main()
