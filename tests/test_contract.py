"""src/contract.json 是跨语言常量的唯一来源：Python 侧读到的值与 JSON 一致，TS 侧都 import 它。"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TPL_SRC = ROOT / "assets" / "lecture-template" / "src"
C = json.loads((TPL_SRC / "contract.json").read_text(encoding="utf-8"))


def load(name: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ContractTest(unittest.TestCase):
    def test_python_constants_come_from_contract(self):
        cases = [
            ("story_time", "FPS", C["FPS"]),
            ("resolve-shots", "FPS", C["FPS"]),
            ("validate-presentation", "FPS", C["FPS"]),
            ("validate-motion-gaps", "FPS", C["FPS"]),
            ("validate-ocr", "FPS", C["FPS"]),
            ("story_caption", "MAX_CHARS", C["CAPTION_MAX_CHARS"]),
            ("validate-caption-sync", "MAX_CHARS", C["CAPTION_MAX_CHARS"]),
            ("story_caption", "CPS", C["READ_CPS"]),
            ("silent-timing", "CPS_COMPONENT", C["READ_CPS"]),
            ("story_text", "SAFE_LH", C["SAFE_LH"]),
            ("validate-presentation", "FONT_FLOOR", C["MIN_LABEL_FONT"]),
            ("resolve-shots", "TEXT_ZOOM_MAX", C["TEXT_ZOOM_MAX"]),
            ("validate-shot-motion", "TEXT_ZOOM_MAX", C["TEXT_ZOOM_MAX"]),
            ("validate-shot-motion", "GRAPHIC_ZOOM_MAX", C["GRAPHIC_ZOOM_MAX"]),
            ("validate-shot-motion", "STAGE_CX", C["STAGE"]["cx"]),
            ("validate-shot-motion", "STAGE_CY", C["STAGE"]["cy"]),
            ("resolve-shots", "STAGE_CX", C["STAGE"]["cx"]),
            ("validate-shot-motion", "CAM_DUR", (C["CAM_DUR"]["short"], C["CAM_DUR"]["long"])),
            ("validate-shot-motion", "FPS", C["FPS"]),
            ("validate-shot-motion", "ROT_MAX", C["ORBIT_ROT"]),
            ("resolve-shots", "DEFAULT_ROT_Y", {"micro-orbit": C["ORBIT_ROT"]}),
        ]
        for mod, attr, want in cases:
            with self.subTest(mod=mod, attr=attr):
                self.assertEqual(getattr(load(mod), attr), want)

    def test_grow_dur_uses_contract(self):
        acts = load("story_acts")
        g = C["GROW"]
        self.assertEqual(acts.grow_dur({"text": "一" * 100, "w": 0}), g["max"])
        self.assertEqual(acts.grow_dur({"text": "一", "w": 0}), g["min"])
        self.assertEqual(acts.grow_dur({"text": "一" * 5, "w": 0}), 5 * g["perChar"])
        self.assertEqual(acts.grow_dur({"text": "a" * 100, "w": 0, "kind": "codeline"}), g["codelineMax"])

    def test_ts_side_imports_contract(self):
        for rel in ("index.tsx", "shotkit.tsx", "auto.tsx", "components/data.tsx", "transitions/meta.ts"):
            with self.subTest(file=rel):
                self.assertIn("contract.json'", (TPL_SRC / rel).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
