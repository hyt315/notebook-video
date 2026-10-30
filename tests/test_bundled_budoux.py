"""The bundled BudouX slice must keep working on its own.

Why this file exists: `assets/vendor/budoux` is the only reason the caption
phrase rule can run on a fresh clone — the skill ships no `node_modules`, and
before 3.9.0 the rule silently reported "SKIPPED" there, which reads almost
exactly like "passed".  Three things can quietly break it:

  * someone deletes the directory while tidying up "unused" assets;
  * an upgrade copies upstream's `index.js` over ours, which drags in
    `linkedom` and fails with a module-not-found error at the worst moment;
  * `module/package.json` (`{"type": "module"}`) goes missing, so Node loads
    the ESM model as CommonJS.

Every one of those is silent until a delivery run fails, so they are asserted
here.  These tests skip when node is absent — the phrase rule skips there too,
and the caller is told so in the report.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "assets" / "vendor"
BUDOUX = VENDOR / "budoux"

# The bridge the validator actually uses (`BUDOUX_BRIDGE` in
# build-semantic-captions.py).  Duplicated on purpose: if that constant changes
# shape, this test should notice rather than keep passing against a stale copy.
BRIDGE = """
import {pathToFileURL} from "node:url";
let raw = "";
process.stdin.setEncoding("utf8");
for await (const chunk of process.stdin) raw += chunk;
const root = process.argv[1];
const {texts} = JSON.parse(raw);
const budoux = await import(pathToFileURL(root + "/budoux/module/index.js").href);
const parser = budoux.loadDefaultSimplifiedChineseParser();
process.stdout.write(JSON.stringify(texts.map((text) => parser.parse(text))));
"""


def segment(texts: list[str], root: Path) -> list[list[str]]:
    proc = subprocess.run(
        [shutil.which("node") or "node", "--input-type=module", "-e", BRIDGE, str(root)],
        input=json.dumps({"texts": texts}, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise AssertionError(f"BudouX bridge failed: {proc.stderr.strip()[:400]}")
    return json.loads(proc.stdout)


class BundledBudouXTest(unittest.TestCase):
    def test_files_are_present(self):
        """The slice must be self-contained: entry, parser, model, licence, ESM marker."""
        for rel in (
            "budoux/LICENSE",
            "budoux/module/index.js",
            "budoux/module/package.json",
            "budoux/module/parser.js",
            "budoux/module/data/models/zh-hans.js",
        ):
            with self.subTest(rel=rel):
                self.assertTrue((VENDOR / rel).is_file(), f"缺少 {rel}")

    def test_module_is_esm(self):
        """Otherwise Node parses `export const model` as CommonJS and every run dies."""
        declared = json.loads((BUDOUX / "module" / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(declared.get("type"), "module")

    def test_entry_does_not_pull_the_dom_path(self):
        """Our entry must not import html_processor: that needs `linkedom`, which is not vendored.

        Copying upstream's index.js over this file is the most likely way to break
        it, and the failure surfaces as a module-not-found *at render time*.
        """
        entry = (BUDOUX / "module" / "index.js").read_text(encoding="utf-8")
        code = "\n".join(
            line for line in entry.splitlines() if not line.lstrip().startswith("//")
        )
        self.assertNotIn("html_processor", code)
        self.assertNotIn("linkedom", code)
        self.assertIn("loadDefaultSimplifiedChineseParser", code)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_segments_real_captions_losslessly(self):
        """Chunks must reassemble to the input — the validator refuses to guess if not."""
        texts = [
            "GitHub 不只是一个放代码的地方它还是程序员的名片",
            "一千二百五十九万七千一百二十个立方英寸",
        ]
        chunks = segment(texts, VENDOR)
        self.assertEqual(len(chunks), len(texts))
        for original, parts in zip(texts, chunks):
            self.assertEqual("".join(parts), original)
            self.assertGreater(len(parts), 1, "segmentation produced a single chunk")

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_finder_falls_back_to_the_bundle(self):
        """`find_budoux_root` must reach the bundle with no project node_modules in sight."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "bsc", ROOT / "scripts" / "build-semantic-captions.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # A directory with no node_modules anywhere above it that matters: the
        # template's manifests dir, which is where the real call site sits.
        found = module.find_budoux_root(None, [ROOT / "assets" / "lecture-template" / "manifests"])
        self.assertIsNotNone(found, "没有兜底到 assets/vendor —— 短语规则会静默跳过")
        self.assertEqual(Path(found).resolve(), VENDOR.resolve())


if __name__ == "__main__":
    unittest.main()
