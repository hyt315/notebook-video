"""渲染包装层的结构性回归：不启动浏览器，只锁定昂贵/易错的调用关系。"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "scripts" / "notebook-video.mjs").read_text(encoding="utf-8")


class RenderPipelineTest(unittest.TestCase):
    def test_curl_frames_render_in_the_same_pass(self):
        """卷页（WebGL2）与其余帧同一遍渲完：没有片段拼接，也没有为卷页压低并发。"""
        self.assertNotIn("spliceArgs", SRC)
        self.assertNotIn("curlBundle", SRC)
        self.assertNotIn("FX_CONCURRENCY", SRC)
        self.assertIn("if (fx.on) mergedProps.nvFx = 'on';", SRC)
        self.assertFalse((ROOT / "scripts" / "fx-pipeline.mjs").exists())

    def test_render_entry_has_one_default(self):
        # 成片入口只有一个缺省值；showcase 显式传自己的入口（src/showcase-entry.tsx）。
        self.assertIn("const remotionRender = async ({project, entry = REMOTION_ENTRY_POINT,", SRC)
        self.assertIn("remotionCli, 'render', entry, composition, output", SRC)
        self.assertEqual(SRC.count("entry: SHOWCASE_ENTRY_POINT"), 1)

    def test_positional_args_do_not_swallow_flags(self):
        self.assertRegex(SRC, r"const positional = \(args \|\| \[\]\)\.filter\(\(a\) => !String\(a\)\.startsWith\('--'\)\);")
        self.assertIn("[projectArg, outputArg, composition = 'NotebookVideoFilm'] = positional", SRC)


if __name__ == "__main__":
    unittest.main()
