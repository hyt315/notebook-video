"""仓库卫生：脚本能被解析、被追踪文件里没有疑似 API Key。

只对维护者有意义（用户装好的技能不会改脚本），所以放在单测里，不进 selftest。
"""
from __future__ import annotations

import ast
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY = re.compile(r"sk-[A-Za-z0-9]{16,}")
SKIP_DIRS = {".git", "node_modules", "renders", ".cache", ".tools", "__pycache__"}
SUFFIX = {".md", ".py", ".mjs", ".tsx", ".ts", ".json", ".txt", ".cmd", ".sh", ".cjs", ".yml", ".yaml"}


def tracked_files() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True,
                             encoding="utf-8", errors="replace").stdout.splitlines()
    except OSError:
        out = []
    if out:
        return [ROOT / p for p in out if (ROOT / p).is_file()]
    return [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in SUFFIX
            and not any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts)]


class RepoHygiene(unittest.TestCase):
    def test_scripts_parse(self):
        errors = []
        for f in sorted((ROOT / "scripts").glob("*.py")):
            try:
                ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            except SyntaxError as exc:
                errors.append(f"{f.name}: {exc}")
        self.assertEqual(errors, [])

    def test_no_key_like_tokens(self):
        me = Path(__file__).resolve()
        hits, unreadable = [], []
        for f in tracked_files():
            if f.resolve() == me:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError as exc:
                unreadable.append(f"{f.relative_to(ROOT)} ({exc.__class__.__name__})")
                continue
            if KEY.search(text):
                hits.append(str(f.relative_to(ROOT)))
        self.assertEqual(unreadable, [], "有文件没读到，密钥扫描不完整")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
