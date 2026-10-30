#!/usr/bin/env python3
"""Tests for scripts/validate-opening.py (3.3.0 cold-open gate)."""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("vo", ROOT / "scripts" / "validate-opening.py")
vo = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(vo)


def project(skin: str, shots: list[dict], cues: list[dict], title: str = "细胞为什么叫细胞") -> Path:
    d = Path(tempfile.mkdtemp(prefix="nv-open-"))
    (d / "src" / "theme").mkdir(parents=True)
    (d / "manifests").mkdir()
    (d / "src" / "theme" / "active.ts").write_text(f"import {{THEME}} from './{skin}';\nexport {{THEME}};\n", encoding="utf-8")
    (d / "src" / "story.ts").write_text(f"export const STORY = {{title: '{title}'}};\n", encoding="utf-8")
    (d / "manifests" / "shots.resolved.json").write_text(json.dumps({"shots": shots}, ensure_ascii=False), encoding="utf-8")
    (d / "manifests" / "caption-cues.json").write_text(json.dumps({"cues": cues}, ensure_ascii=False), encoding="utf-8")
    return d


COLD = dict(
    shots=[{"id": "S1", "from": 0, "beatsAbs": [0, 40, 75], "hero": {"name": "一立方英寸软木", "kind": "graphic"}},
           {"id": "S2", "from": 200, "beatsAbs": [210]}],
    cues=[{"text": "一立方英寸软木里，有十二亿间小屋子。", "start_ms": 300}],
)


class StaticOpening(unittest.TestCase):
    def run_check(self, skin: str, shots, cues, **kw) -> dict:
        d = project(skin, shots, cues, **kw)
        try:
            return vo.check(d)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_cold_open_passes(self):
        r = self.run_check("journal", **COLD)
        self.assertEqual(r["p0"], [], r)

    def test_cell_v1_opening_is_blocked_for_craft(self):
        shots = [{"id": "S1", "from": 0, "beatsAbs": [18, 79], "hero": {"name": "软木塞", "kind": "graphic"}}]
        cues = [{"text": "「细胞」这个词，", "start_ms": 600}]
        r = self.run_check("journal", shots, cues)
        codes = {x[:2] for x in r["p0"]}
        self.assertEqual(codes, {"O1", "O4", "O5"}, r)

    def test_flat_only_warns(self):
        shots = [{"id": "S1", "from": 0, "beatsAbs": [40], "hero": {"name": "x"}}]
        r = self.run_check("flat", shots, [{"text": "今天我们来聊聊缓存", "start_ms": 1500}])
        self.assertEqual(r["p0"], [])
        self.assertTrue(any(x.startswith("O2") for x in r["p1"]))
        self.assertTrue(any(x.startswith("O5") for x in r["p1"]))

    def test_title_card_first_shot(self):
        shots = [{"id": "S1", "from": 0, "beatsAbs": [0, 30, 60], "hero": {"name": "细胞为什么叫细胞", "kind": "text"}}]
        r = self.run_check("papercut", shots, COLD["cues"])
        self.assertTrue(any(x.startswith("O3") for x in r["p0"]), r)
        shots[0]["hero"] = {"name": "x", "kind": "title"}
        self.assertTrue(any(x.startswith("O3") for x in self.run_check("papercut", shots, COLD["cues"])["p0"]))

    def test_banned_openers(self):
        for text in ("你知道吗？咖啡渍有一圈深边", "大家好，今天", "今天我们来了解二维码", "“细胞”这个词最早"):
            self.assertTrue(any(re.search(pat, text, re.I) for pat, _ in vo.BANNED_OPENERS), text)
        self.assertFalse(any(re.search(pat, "一立方英寸软木里有十二亿间屋子", re.I) for pat, _ in vo.BANNED_OPENERS))


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg not installed")
class PixelOpening(unittest.TestCase):
    def video(self, src: str) -> Path:
        out = Path(tempfile.mkdtemp(prefix="nv-open-v-")) / "v.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", src, "-t", "4", "-pix_fmt", "yuv420p", str(out)], check=True)
        return out

    def test_blank_paper_fails_and_moving_frame_passes(self):
        blank = self.video("color=c=0xF2EADB:s=320x180:r=30")
        issues, status = vo.pixel_checks(blank)
        self.assertEqual(status, "checked")
        self.assertTrue(any(x.startswith("O6 第 0 帧") for x in issues), issues)
        self.assertTrue(any(x.startswith("O7") for x in issues), issues)
        busy = self.video("testsrc2=s=320x180:r=30")
        issues, _ = vo.pixel_checks(busy)
        self.assertEqual(issues, [], issues)
        shutil.rmtree(blank.parent, ignore_errors=True)
        shutil.rmtree(busy.parent, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
