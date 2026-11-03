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
            self.assertFalse(r.startswith((".git/", ".github/", "tests/", "dist/")), r)
            self.assertNotIn("__pycache__", r)
            self.assertNotIn("node_modules", r)
            self.assertFalse(r.endswith((".pyc", ".mp4", ".zip")), r)

    def test_downloaded_fonts_are_opt_in(self):
        default = {PKG.rel(p) for p in PKG.collect_files()}
        offline = {PKG.rel(p) for p in PKG.collect_files(include_fonts=True)}
        self.assertFalse(any(r.startswith("assets/fonts/") and r.endswith((".ttf", ".otf")) for r in default))
        self.assertTrue(any(r.startswith("assets/fonts/") and r.endswith((".ttf", ".otf")) for r in offline))
        self.assertIn("assets/fonts/LICENSE-OFL-1.1-LXGW.txt", default)

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
