#!/usr/bin/env python3
"""Tests for the 3.6.0 camera / shot-length rules (references/camera-language.md §5).

validate-composition: shot-length coefficient of variation >= 0.35; a single composition > 12 s needs an in-shot
focus (cinema.focus) or an insert shot. resolve-shots passes the optional `insert` marker through.
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


vc = load("vc_cam", "validate-composition.py")

SKELS = ["Stage", "Split", "Zoom", "Corridor"]
INTENTS = ["push-in", "pan-follow", "reveal", "pull-back"]
MEDIA = ["graphic", "metric", "chart", "text"]


def film(durs: list[int], **extra) -> dict:
    shots, f = [], 0
    for i, d in enumerate(durs):
        s = {"id": f"S{i + 1}", "skeleton": SKELS[i % 4], "zones": 3, "bottomFill": True, "cameraIntent": INTENTS[i % 4],
             "media": [MEDIA[i % 4], "text"], "live": ["InkPath"], "transition": "slide", "entry": ["rise", "slide", "fade"][i % 3],
             "from": f, "to": f + d, "duration": d, "beats": [0, 30], "beatsAbs": [f, f + 30],
             "hero": {"name": "x", "size": 400, "kind": "graphic"}}
        s.update(extra.get(s["id"], {}))
        shots.append(s)
        f += d
    return {"theme": "journal", "shots": shots}


def p1(data: dict) -> list[str]:
    return [x["issue"] for x in vc.check(data)[1]]


class ShotLength(unittest.TestCase):
    def test_metronome_cv_flagged(self):
        even = film([240, 250, 260, 270, 250, 240])           # 8–9 s each: CV ≈ 0.04
        self.assertTrue(any("变异系数" in x for x in p1(even)))
        varied = film([90, 300, 120, 330, 100, 240])          # 3–11 s: CV ≈ 0.48
        self.assertFalse(any("变异系数" in x for x in p1(varied)))

    def test_long_single_composition_needs_focus_or_insert(self):
        long = film([90, 426, 120, 240])
        self.assertTrue(any(x.startswith("单镜 14.2s 一个构图到底") for x in p1(long)))
        focused = film([90, 426, 120, 240], S2={"cinema": {"focus": [{"at": 180, "zoom": 1.3, "hold": 60}]}})
        self.assertFalse(any("一个构图到底" in x for x in p1(focused)))
        settle_only = film([90, 426, 120, 240], S2={"cinema": {"focus": [{"at": 380, "zoom": 1.1, "settle": True}]}})
        self.assertTrue(any("一个构图到底" in x for x in p1(settle_only)), "the auto settle focus is not an in-shot focus change")
        insert = film([90, 426, 120, 240], S2={"insert": {"of": "S1"}})
        self.assertFalse(any("一个构图到底" in x for x in p1(insert)))


class InsertMarker(unittest.TestCase):
    def test_resolve_shots_passes_insert_through(self):
        src = (ROOT / "scripts" / "resolve-shots.py").read_text(encoding="utf-8")
        self.assertIn('rec["insert"] = {"of": ins["of"].strip()}', src)
        doc = (ROOT / "references" / "camera-language.md").read_text(encoding="utf-8")
        for needle in ("12%", "变异系数", "插入镜", "视线连续"):
            self.assertIn(needle, doc)


if __name__ == "__main__":
    unittest.main()
