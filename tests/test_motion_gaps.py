"""validate-motion-gaps 的判定（不跑 ffmpeg）：一般镜 ≥2.5 s 静止是 P0，锤子镜放宽到 3.0 s。"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("motion_gaps", ROOT / "scripts" / "validate-motion-gaps.py")
mg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mg)


def row(shot, dur):
    return {"shot": shot, "dur_s": dur}


class Judge(unittest.TestCase):
    def test_plain_shot_freeze_fails(self):
        self.assertEqual(len(mg.judge([row("S1", 2.5), row("S2", 2.4)], 2.5, set())), 1)

    def test_hammer_shot_gets_up_to_three_seconds(self):
        self.assertEqual(mg.judge([row("S3", 2.5), row("S3", 2.9)], 2.5, {"S3"}), [])

    def test_hammer_shot_beyond_limit_still_fails(self):
        self.assertEqual(len(mg.judge([row("S3", 3.0)], 2.5, {"S3"})), 1)

    def test_hammer_ids_from_fusion_and_live(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "manifests").mkdir()
            (p / "manifests" / "fusion.json").write_text(json.dumps(
                {"shots": {"S1": {"recipe": "hammer"}, "S2": {"recipe": None}}}), encoding="utf-8")
            shots = [{"id": "S2", "live": ["Callout"]}, {"id": "S4", "live": ["StampBanner"]}]
            self.assertEqual(mg.hammer_shots(p, shots), {"S1", "S4"})


if __name__ == "__main__":
    unittest.main()
