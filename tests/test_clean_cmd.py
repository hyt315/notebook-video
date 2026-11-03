#!/usr/bin/env python3
"""P2-32 · `clean` 命令的安全边界。

清理命令的危险不在"删不掉"，在"删多了"。所以这里锁的是**不许删什么**：
故事源文件、用户素材、成片、耗时记录、别人的目录。默认还必须只预演。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "notebook-video.mjs"


def run(*args: str) -> tuple[int, str]:
    r = subprocess.run(["node", str(CLI), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def make_project(root: Path) -> Path:
    """造一个「已经渲过一次」的工程：中间产物 + 成片 + 耗时记录 + 用户内容。"""
    proj = root / "proj"
    (proj / "renders" / "sweep").mkdir(parents=True)
    (proj / "src").mkdir()
    (proj / "renders" / "film.raw.mp4").write_bytes(b"x" * 2048)
    (proj / "renders" / "film.render.json").write_text('{"schema":1}', encoding="utf-8")
    (proj / "renders" / "film-contact.jpg").write_bytes(b"y" * 1024)
    (proj / "renders" / "sweep" / "S1.jpg").write_bytes(b"z" * 512)
    (proj / "renders" / "film.mp4").write_bytes(b"v" * 4096)          # 成片
    (proj / "renders" / "render-log.jsonl").write_text('{"state":"ok"}\n', encoding="utf-8")
    (proj / "story.json").write_text('{"title":"x"}', encoding="utf-8")
    (proj / "src" / "index.tsx").write_text("export default 1;\n", encoding="utf-8")
    return proj


class CleanTest(unittest.TestCase):
    def test_missing_renders_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out = run("clean", td)
            self.assertEqual(rc, 0, out)
            self.assertIn("没有", out)

    def test_dry_run_lists_but_deletes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(Path(td))
            rc, out = run("clean", str(proj))
            self.assertEqual(rc, 0, out)
            self.assertIn("film.raw.mp4", out)
            self.assertIn("dry-run", out)
            self.assertTrue((proj / "renders" / "film.raw.mp4").is_file(), "预演就删了文件")

    def test_yes_removes_temp_but_keeps_film_and_log(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(Path(td))
            rc, out = run("clean", str(proj), "--yes")
            self.assertEqual(rc, 0, out)
            self.assertFalse((proj / "renders" / "film.raw.mp4").exists(), "raw 没删")
            self.assertFalse((proj / "renders" / "film.render.json").exists(), "resume 元数据没删")
            self.assertFalse((proj / "renders" / "sweep").exists(), "sweep 目录没删")
            # 不许动的
            self.assertTrue((proj / "renders" / "film.mp4").is_file(), "成片被删了（要 --all 才删）")
            self.assertTrue((proj / "renders" / "render-log.jsonl").is_file(), "耗时记录被删了")
            self.assertTrue((proj / "story.json").is_file(), "故事源被删了")
            self.assertTrue((proj / "src" / "index.tsx").is_file(), "用户源码被删了")

    def test_all_also_removes_the_film(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(Path(td))
            rc, out = run("clean", str(proj), "--yes", "--all")
            self.assertEqual(rc, 0, out)
            self.assertFalse((proj / "renders" / "film.mp4").exists(), "--all 没删成片")
            self.assertTrue((proj / "renders" / "render-log.jsonl").is_file(), "--all 也不该删耗时记录")

    def test_refuses_while_render_lock_is_held(self):
        # 锁在 = 有进程正握着这些 raw。此时清理等于删掉别人正在写的文件。
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(Path(td))
            key = subprocess.run(
                ["node", "--input-type=module", "-e",
                 f"import {{projectKeyFor}} from {json.dumps((ROOT / 'scripts' / 'render-lock.mjs').as_uri())};"
                 f"console.log(projectKeyFor({json.dumps(str(proj))}))"],
                capture_output=True, text=True, check=True).stdout.strip()
            lock = Path(tempfile.gettempdir()) / f"nv-render-{key}.lock"
            lock.write_text(json.dumps({"pid": 999999, "startedAt": "test"}), encoding="utf-8")
            try:
                rc, out = run("clean", str(proj), "--yes")
                self.assertNotEqual(rc, 0, "有锁时仍执行了清理")
                self.assertIn("正在渲染", out)
                self.assertTrue((proj / "renders" / "film.raw.mp4").is_file(), "拒绝时仍删了文件")
            finally:
                lock.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
