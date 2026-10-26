#!/usr/bin/env python3
"""Tests for scripts/validate-composition.py: the zone contract is relaxed to 1–5 for hand-made skins (3.3.0)."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-composition.py"
spec = importlib.util.spec_from_file_location("vc", SCRIPT)
vc = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(vc)


def shot(i: int, skeleton: str, zones: int, intent: str, media: str) -> dict:
    return {"id": f"S{i}", "skeleton": skeleton, "zones": zones, "bottomFill": True, "cameraIntent": intent,
            "media": [media, "text"], "live": ["InkPath"], "transition": "slide", "entry": "rise",
            "from": (i - 1) * 150, "to": i * 150, "duration": 150, "beats": [0, 60], "beatsAbs": [(i - 1) * 150, (i - 1) * 150 + 60],
            "hero": {"name": "x", "size": 400, "kind": "graphic"}}


def doc(theme: str, zones: int) -> dict:
    return {"theme": theme, "shots": [shot(1, "Stage", zones, "push-in", "graphic"), shot(2, "Split", zones, "pan-follow", "metric"),
                                      shot(3, "Zoom", zones, "reveal", "chart")]}


class ZoneRange(unittest.TestCase):
    def zone_issues(self, theme: str, zones: int) -> list[str]:
        p0, _p1, _notes = vc.check(doc(theme, zones))
        return [x["issue"] for x in p0 if "功能分区" in x["issue"]]

    def test_component_skins_keep_3_to_5(self):
        self.assertTrue(self.zone_issues("flat", 1), "flat: one zone must still be P0")
        self.assertTrue(self.zone_issues("cel", 2))
        self.assertFalse(self.zone_issues("flat", 3))

    def test_craft_skins_allow_a_single_subject(self):
        for skin in ("journal", "papercut", "archive"):
            self.assertFalse(self.zone_issues(skin, 1), skin)
            self.assertFalse(self.zone_issues(skin, 2), skin)

    def test_upper_bound_still_holds_for_craft(self):
        self.assertTrue(self.zone_issues("journal", 6))
        self.assertTrue(self.zone_issues("journal", 0))

    def test_cli_reads_skin_from_active_theme(self):
        d = Path(tempfile.mkdtemp(prefix="nv-vc-"))
        try:
            (d / "manifests").mkdir()
            (d / "src" / "theme").mkdir(parents=True)
            data = doc("flat", 1)          # 分镜表写着 flat，但渲染用的是 journal
            (d / "manifests" / "shots.resolved.json").write_text(json.dumps(data), encoding="utf-8")
            (d / "src" / "theme" / "active.ts").write_text("import {THEME} from './journal';\nexport {THEME};\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), str(d), "--json"], capture_output=True, text=True)
            out = json.loads(r.stdout)
            self.assertFalse([x for x in out["p0"] if "功能分区" in x["issue"]], r.stdout)
            (d / "src" / "theme" / "active.ts").write_text("import {THEME} from './flat';\nexport {THEME};\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), str(d), "--json"], capture_output=True, text=True)
            self.assertTrue([x for x in json.loads(r.stdout)["p0"] if "功能分区" in x["issue"]], r.stdout)
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
