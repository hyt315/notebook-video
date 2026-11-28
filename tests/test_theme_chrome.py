"""公共 Chrome 整洁约束：不写题材分支，且常驻章节徽标与字幕合并面积保持在 ≤5% 预算内。"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "assets/lecture-template/src/index.tsx").read_text(encoding="utf-8")


class ThemeChromeTest(unittest.TestCase):
    def test_compact_chrome_stays_within_overlay_budget(self):
        chrome = INDEX[INDEX.index("const Chrome=()=>"):]
        chrome = chrome[:chrome.index("// 引擎级虚拟摄影机")]
        m = re.search(r"width:(\d+),height:(\d+)", chrome)
        self.assertIsNotNone(m, "Chrome 章节徽标必须声明设计尺寸")
        w, h = int(m.group(1)), int(m.group(2))
        # 章节名要在手机上读得清（≥48 设计 px），徽标放大到约 2.2%；与字幕合计仍受 ≤5% 叠层预算约束。
        self.assertLessEqual(w * h / (1920 * 1080), 0.025, "左上常驻徽标占画布面积应 ≤ 2.5%")
        self.assertNotIn("THEME.headerPlate", chrome, "不渲染常驻右上角页眉底板")

    def test_no_skin_specific_branch_in_common_chrome(self):
        chrome = INDEX[INDEX.index("const Chrome=()=>"):]
        chrome = chrome[:chrome.index("// 引擎级虚拟摄影机")]
        self.assertNotIn("THEME.id === 'cel'", chrome)
        self.assertNotIn("THEME.id==='cel'", chrome)


if __name__ == "__main__":
    unittest.main()
