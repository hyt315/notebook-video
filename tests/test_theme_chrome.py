"""皮肤自己的页眉避让：公共 Chrome 不写题材分支。"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CEL = (ROOT / "assets/lecture-template/src/theme/cel.tsx").read_text(encoding="utf-8")
INDEX = (ROOT / "assets/lecture-template/src/index.tsx").read_text(encoding="utf-8")


class ThemeChromeTest(unittest.TestCase):
    def test_cel_header_clears_both_decor_and_chapter_plate(self):
        """右缘只证明不压爆炸星；可用宽度还要保证左缘不进入左上章节框。"""
        plate = CEL[CEL.index("const headerPlate"):]
        self.assertIn("const CEL_HEADER_RIGHT = 1920 - 1540 + 28;", CEL)
        self.assertIn("const CEL_CHAPTER_RIGHT = 92 + 392;", CEL)
        self.assertIn("const CEL_HEADER_MAX_W = 1920 - CEL_HEADER_RIGHT - CEL_CHAPTER_RIGHT - 28;", CEL)
        self.assertIn("right: CEL_HEADER_RIGHT", plate)
        self.assertIn("maxWidth: CEL_HEADER_MAX_W", plate)
        self.assertIn("...THEME.headerPlate", INDEX)

    def test_no_skin_specific_branch_in_common_chrome(self):
        chrome = INDEX[INDEX.index("const Chrome=()=>"):]
        chrome = chrome[:chrome.index("// 3.2.0 引擎级虚拟摄影机")]
        self.assertNotIn("THEME.id === 'cel'", chrome)
        self.assertNotIn("THEME.id==='cel'", chrome)


if __name__ == "__main__":
    unittest.main()
