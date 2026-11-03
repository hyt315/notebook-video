"""墨图部位筛选的契约回归（源结构检查，真实类型由 tsc 门禁覆盖）。"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKETCH = (ROOT / "assets/lecture-template/src/linework/sketch.tsx").read_text(encoding="utf-8")
TYPES = (ROOT / "assets/lecture-template/src/linework/types.ts").read_text(encoding="utf-8")
LIB = (ROOT / "assets/lecture-template/src/linework/library.ts").read_text(encoding="utf-8")


class LineworkPartsTest(unittest.TestCase):
    def test_array_parts_really_filter_the_drawing(self):
        self.assertIn("Array.isArray(spec.parts) ? new Set(spec.parts) : null", SKETCH)
        self.assertIn("filter(([id]) => !selected || selected.has(id))", SKETCH)
        self.assertIn("{partEntries.map(([id, part]) =>", SKETCH)
        self.assertNotIn("{Object.entries(def.parts).map(([id, part]) =>", SKETCH)

    def test_single_part_can_have_its_own_closeup_fit(self):
        self.assertIn("fit?: [number, number, number, number];", TYPES)
        # 3.9.0：手写 fit 优先，其次用构建期按真实包围盒算出的缺省框（crops.ts），都没有才退回整图。
        self.assertIn("only?.fit ?? (onlyName ? cropFor(onlyName) : undefined) ?? fitOf(def)", SKETCH)
        self.assertIn("plank: {label: '木板与水面', anchor: [20, 63], fit: [0, 48, 38, 32]", LIB)

    def test_unknown_parts_never_blank_the_frame(self):
        self.assertIn("visibleParts.length === 0", SKETCH)
        self.assertIn("unknownSelection ? Object.entries(def.parts) : visibleParts", SKETCH)
        self.assertIn("已画整图", SKETCH)

    def test_record_parts_remain_point_labels(self):
        self.assertIn("parts?: Record<string, string> | string[];", TYPES)
        self.assertIn("partLabels?.[st.point.target]", SKETCH)


if __name__ == "__main__":
    unittest.main()
