#!/usr/bin/env python3
"""Tests for the hand-made story blueprints (3.6.0): four new structures + the cold-open medium-metaphor."""
from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("vt_bp", ROOT / "scripts" / "validate-treatment.py")
vt = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(vt)

CRAFT_EXPORTS = set()
for m in re.finditer(r"export\s*\{([^}]*)\}", (ROOT / "assets/lecture-template/src/craft/index.ts").read_text(encoding="utf-8")):
    CRAFT_EXPORTS |= {x.strip() for x in m.group(1).split(",") if x.strip()}
CRAFT = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "blueprints").glob("*.json")
         if json.loads(p.read_text(encoding="utf-8")).get("$route") == "handwritten-craft"}


class CraftBlueprints(unittest.TestCase):
    def test_five_structures_exist(self):
        self.assertEqual(set(CRAFT), {"medium-metaphor", "kishotenketsu", "mystery", "scale-ladder", "experiment"})

    def test_each_has_family_fits_and_beats(self):
        for name, bp in CRAFT.items():
            self.assertEqual(bp.get("family"), name, name)
            self.assertIn(bp["family"], vt.FAMILIES)
            self.assertTrue(str(bp.get("fits", "")).strip(), f"{name}: fits")
            self.assertGreaterEqual(len(bp["beats"]), 4, name)
            for b in bp["beats"]:
                self.assertTrue(b.get("$why"), f"{name}/{b.get('id')}: $why")
                self.assertIn("camera", b["$components"], f"{name}/{b.get('id')}")

    def test_component_names_exist(self):
        for name, bp in CRAFT.items():
            for b in bp["beats"]:
                for item in b["$components"].get("craft", []):
                    bare = re.sub(r"[（(][^）)]*[）)]", "", item)  # 括号里是说明，不是组件名
                    for tok in re.findall(r"\b([A-Z][A-Za-z]+)\b", bare):
                        self.assertIn(tok, CRAFT_EXPORTS, f"{name}/{b['id']}: {tok} is not a src/craft export")

    def test_cold_open_first_beat(self):
        for name, bp in CRAFT.items():
            first = bp["beats"][0]
            self.assertTrue(first["at"].startswith("0–"), name)
            self.assertNotEqual(first["role"], "title", name)
            for line in first.get("caption", []):
                self.assertNotRegex(line, r"这个词|你知道吗|今天我们", name)
        mm = CRAFT["medium-metaphor"]
        self.assertEqual(mm["beats"][0]["role"], "cold-open")
        title = next(b for b in mm["beats"] if b["role"] == "title")
        self.assertIn("≥ 10 s", title["at"])

    def test_rules_link_opening_and_camera_docs(self):
        for name, bp in CRAFT.items():
            rules = " ".join(bp["$rules"])
            self.assertIn("narrative-hook.md", rules, name)
            self.assertIn("camera-language.md", rules, name)


if __name__ == "__main__":
    unittest.main()
