"""渲染包装层的结构性回归：不启动浏览器，只锁定昂贵/易错的调用关系。"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "scripts" / "notebook-video.mjs").read_text(encoding="utf-8")
# 3.8.0 起「打包 → 逐段 → 拼接 → 打标记」搬进 fx-pipeline.mjs（P1-14 要能测失败路径），
# 所以调用关系要跨两个文件一起断言。
FX = (ROOT / "scripts" / "fx-pipeline.mjs").read_text(encoding="utf-8")


class RenderPipelineTest(unittest.TestCase):
    def test_curl_windows_share_one_bundle(self):
        """N 个卷页窗口只能打包一次；片段 render 必须吃该 bundle。"""
        self.assertEqual(SRC.count("'--out-dir', curlBundle"), 1)
        # 管线里 bundle 在循环外只调一次，循环内只渲染片段
        self.assertEqual(FX.count("await bundle()"), 1)
        self.assertLess(FX.index("await bundle()"), FX.index("for (const [a, b] of windows)"))
        self.assertIn("entry: curlBundle", SRC)
        segment_call = SRC[SRC.index("renderSegment: (a, b, seg)"):SRC.index("splice: (fast, segs, out)")]
        self.assertNotIn("'bundle'", segment_call, "片段渲染里不能再次打包")

    def test_render_entry_has_one_default(self):
        self.assertIn("entry = REMOTION_ENTRY_POINT", SRC)
        self.assertIn("remotionCli, 'render', entry, composition, output", SRC)

    def test_positional_args_do_not_swallow_flags(self):
        self.assertRegex(SRC, r"const positional = \(args \|\| \[\]\)\.filter\(\(a\) => !String\(a\)\.startsWith\('--'\)\);")
        self.assertIn("[projectArg, outputArg, composition = 'NotebookVideoFilm'] = positional", SRC)


if __name__ == "__main__":
    unittest.main()
