"""常驻画面遮挡面积（<=5% 整洁线 / >30% 低质线）门禁单测。"""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("vp_overlay", ROOT / "scripts" / "validate-presentation.py")
VP = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(VP)


class OverlayBudgetTest(unittest.TestCase):
    def _proj(self, td: str, skin: str, chrome_w: int, chrome_h: int, header_plate: bool = False,
              sub_size: int = 64, cue_text: str = "这是一段十四字的清晰字幕展示。", border_box: bool = False) -> Path:
        p = Path(td)
        (p / "src" / "theme").mkdir(parents=True)
        (p / "manifests").mkdir(parents=True)
        (p / "src" / "theme" / "active.ts").write_text(f"import {{THEME}} from './{skin}';\nexport {{THEME}};\n", encoding="utf-8")
        (p / "src" / "theme" / "canvas.ts").write_text(f"export const MODES={{'16:9':{{subFont:{sub_size}}}}};\n", encoding="utf-8")
        skin_body = f"const aesthetic={{subtitleSize:{sub_size}}};\n"
        if border_box:
            skin_body += "const SubtitleChrome=()=> <div style={{border:'3px solid #111'}}/>;\n"
        (p / "src" / "theme" / f"{skin}.tsx").write_text(skin_body, encoding="utf-8")
        hp = "...THEME.headerPlate" if header_plate else ""
        (p / "src" / "index.tsx").write_text(
            f"const Chrome=()=>{{ return <div style={{{{width:{chrome_w},height:{chrome_h}}}}}>{hp}</div>;\n}};\n",
            encoding="utf-8",
        )
        (p / "manifests" / "caption-cues.json").write_text(json.dumps({"cues": [{"text": cue_text}]}, ensure_ascii=False), encoding="utf-8")
        return p

    def test_compact_chrome_and_64px_halo_stay_under_5_percent(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._proj(td, "flat", 268, 52, cue_text="这是一段十四字的清晰字幕展示。")
            p0, p1 = VP.check_overlay_budget(p)
            self.assertEqual((p0, p1), ([], []), (p0, p1))

    def test_heavy_chrome_triggers_p1_above_5_percent(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._proj(td, "cel", 392, 90, header_plate=True, sub_size=72, border_box=True)
            p0, p1 = VP.check_overlay_budget(p)
            self.assertEqual(p0, [])
            self.assertTrue(any("5%" in x["issue"] for x in p1), p1)

    def test_massive_overlay_triggers_p0_above_30_percent(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._proj(td, "flat", 1200, 600)
            p0, _p1 = VP.check_overlay_budget(p)
            self.assertTrue(any("30%" in x["issue"] for x in p0), p0)


if __name__ == "__main__":
    unittest.main()
