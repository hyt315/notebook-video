"""上传包必须小而完整：白名单之外一概不带，入口文档不许断链。"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_skill", ROOT / "scripts/package-skill.py")
PKG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PKG)


class SkillPackageTest(unittest.TestCase):
    def test_runtime_whitelist_excludes_local_junk(self):
        files = [PKG.rel(p) for p in PKG.collect_files()]
        self.assertIn("SKILL.md", files)
        self.assertIn("scripts/notebook-video.mjs", files)
        self.assertIn("examples/recipes/jie-freeform.story.json", files)
        for r in files:
            self.assertFalse(r.startswith((".git/", ".github/", "tests/", "dist/", "scripts/dev/", "docs/")), r)
            self.assertNotIn("__pycache__", r)
            self.assertNotIn("node_modules", r)
            self.assertFalse(r.endswith((".pyc", ".mp4", ".zip")), r)

    def test_downloaded_fonts_are_opt_in(self):
        # 只判路径，不往共享的 assets/fonts/ 里写占位文件：结果不取决于这台机器下没下过字体。
        fonts = ROOT / "assets" / "fonts"
        for name in ("LXGWWenKaiLite-Regular.ttf", "NotoSerifSC-Bold.otf"):
            self.assertTrue(PKG.excluded(fonts / name, include_fonts=False), name)
            self.assertFalse(PKG.excluded(fonts / name, include_fonts=True), name)
        self.assertTrue(PKG.excluded(fonts / "ClashDisplay-Bold.woff2", include_fonts=True))
        self.assertIn("assets/fonts/LICENSE-OFL-1.1-LXGW.txt", {PKG.rel(p) for p in PKG.collect_files()})

    def test_skill_links_are_inside_package(self):
        self.assertEqual(PKG.validate_skill_links(PKG.collect_files()), [])

    def test_zip_has_one_skill_root_and_no_tests(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "skill.zip"
            PKG.build(out, include_fonts=False)
            with zipfile.ZipFile(out) as zf:
                names = zf.namelist()
                self.assertIn("notebook-video/SKILL.md", names)
                self.assertTrue(all(n.startswith("notebook-video/") for n in names))
                self.assertFalse(any(n.startswith("notebook-video/tests/") for n in names))
                self.assertEqual(zf.testzip(), None)


if __name__ == "__main__":
    unittest.main()
