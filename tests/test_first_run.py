#!/usr/bin/env python3
"""P1-14 / P1-29 的剩余可测项：首次运行会遇到什么。

清单里挂着的两条：
- **P1-14**：看门狗杀父之后，子进程树有没有一起走（Windows 上是 taskkill /T 的活）。
- **P1-29**：字体下载失败 / 断网时，报错能不能指名「缺什么、去哪补、怎么换镜像」；
  `new-project` 在干净目录里的首跑产物齐不齐。

这两条以前都是"改完没验"。这里各给一个可重复跑的实证。
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "notebook-video.mjs"
SMOKE = ROOT / "scripts" / "dev" / "kill-tree-smoke.mjs"
FONTS = ROOT / "assets" / "fonts"


def node(*args: str, env: dict | None = None) -> tuple[int, str]:
    r = subprocess.run(["node", str(CLI), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env or os.environ.copy())
    return r.returncode, (r.stdout or "") + (r.stderr or "")


class ProcessTreeTest(unittest.TestCase):
    def test_grandchild_dies_with_parent(self):
        # 真起三段进程：本测试 → 父（模拟 render）→ 孙（模拟 Chrome），用产品代码的 killTree。
        r = subprocess.run(["node", str(SMOKE)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        out = (r.stdout or "") + (r.stderr or "")
        self.assertEqual(r.returncode, 0, f"进程树没杀干净：\n{out[-1200:]}")
        self.assertIn("没有留孤儿", out)


class FontDownloadFailureTest(unittest.TestCase):
    """断网/镜像挂掉时，报错必须能照着修。"""

    def test_missing_font_offline_gives_actionable_error(self):
        moved: list[tuple[Path, Path]] = []
        try:
            for f in sorted(FONTS.glob("*.ttf")) + sorted(FONTS.glob("*.otf")):
                bak = f.with_name(f.name + ".pytest-bak")
                f.rename(bak)
                moved.append((f, bak))
            env = os.environ.copy()
            env["NOTEBOOK_VIDEO_FONT_BASE_URL"] = "http://127.0.0.1:9/nope"   # 一定连不上
            rc, out = node("fonts", env=env)
            self.assertNotEqual(rc, 0, "字体缺失 + 连不上，却返回了成功")
            # 三条信息缺一不可：缺哪个文件、去哪下、怎么换镜像
            self.assertIn("Font download failed", out)
            self.assertIn("manually", out)
            self.assertIn("NOTEBOOK_VIDEO_FONT_BASE_URL", out)
            self.assertNotIn("Traceback", out, "打印了 JS 栈而不是可读错误")
        finally:
            for f, bak in moved:
                if bak.exists():
                    bak.rename(f)

    def test_fonts_are_restored(self):
        # 上一组把字体临时搬走过：这条确保它真的被搬回来了（否则后续渲染全废）
        self.assertTrue(list(FONTS.glob("*.ttf")) or list(FONTS.glob("*.otf")),
                        "字体没恢复 —— 后面所有渲染都会因缺字体失败")


class NewProjectFirstRunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._td = tempfile.TemporaryDirectory()
        cls.proj = Path(cls._td.name) / "proj"
        r = subprocess.run(["node", str(CLI), "new-project", str(cls.proj)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        cls.rc, cls.out = r.returncode, (r.stdout or "") + (r.stderr or "")

    @classmethod
    def tearDownClass(cls):
        cls._td.cleanup()

    def test_first_run_succeeds(self):
        self.assertEqual(self.rc, 0, f"new-project 首次运行失败：\n{self.out[-1200:]}")

    def test_required_files_exist(self):
        # new-project 给的是**可渲染的工程骨架**；story.json 由作者写（不是首跑产物）。
        for rel in ("src/index.tsx", "src/theme/active.ts", "manifests/visual-assets.json",
                    "package.json", "scripts/tts-openai-compatible.py"):
            self.assertTrue((self.proj / rel).is_file(), f"首跑缺 {rel}")

    def test_skill_entry_is_callable_from_the_new_project(self):
        # 首跑最常见的坑：工程建好了，但 skill 的脚本不认它。这里跑一次只读的校验。
        r = subprocess.run(["node", str(CLI), "validate-visual-plan", str(self.proj)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0,
                         f"新建工程过不了 validate-visual-plan：\n{(r.stdout or '')[-800:]}{(r.stderr or '')[-800:]}")


if __name__ == "__main__":
    unittest.main()
