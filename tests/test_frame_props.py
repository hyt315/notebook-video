#!/usr/bin/env python3
"""Tests for scripts/validate-frame-props.py: named / intersection prop types (craft components, 3.3.0)."""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-frame-props.py"
spec = importlib.util.spec_from_file_location("vfp", SCRIPT)
vfp = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(vfp)

CRAFT = """
import React from 'react';
export type BlobProps = {
  f: number; at: number;
  /** callback with an arrow type must not end the type early */
  render?: (inside: boolean) => React.ReactNode;
  color?: string;
};
export const Blob: React.FC<BlobProps> = ({f, at}) => null;
type Base = {f: number; id: string; x: number};
export const Photo: React.FC<Base & {caption?: string}> = ({f, id}) => null;
export const Lit: React.FC<{frame: number; text: string}> = ({frame}) => null;
export const Plain: React.FC<{text: string}> = ({text}) => null;
"""


def project(scene: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix="nv-vfp-"))
    (d / "src" / "craft").mkdir(parents=True)
    (d / "src" / "craft" / "kit.tsx").write_text(CRAFT, encoding="utf-8")
    # 门禁要求 ≥20 个导出组件才给结论（防"源码没读到"的假 PASS）
    filler = "\n".join(f"export const Filler{i}: React.FC<{{f: number}}> = ({{f}}) => null;" for i in range(20))
    (d / "src" / "filler.tsx").write_text("import React from 'react';\n" + filler + "\n", encoding="utf-8")
    (d / "src" / "scenes.tsx").write_text(scene, encoding="utf-8")
    return d


def run(d: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(SCRIPT), str(d)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


class NamedTypes(unittest.TestCase):
    def test_named_and_intersection_types_resolve(self):
        text = CRAFT
        comps = {}
        for m in vfp.EXPORT_RE.finditer(text):
            comps[m.group(1)] = vfp.prop_names(text, m.start())
        self.assertIn("f", comps["Blob"])
        self.assertIn("color", comps["Blob"], "arrow type `=>` must not truncate the type literal")
        self.assertIn("f", comps["Photo"])
        self.assertIn("caption", comps["Photo"])
        self.assertEqual(comps["Lit"], {"frame", "text"})

    def test_craft_component_with_f_passes_without_noise(self):
        d = project("const S = ({f}) => <><Blob f={f} at={3} /><Photo f={f} id='x' x={1} /><Lit frame={f} text='a' /></>;\n")
        try:
            code, out = run(d)
            self.assertEqual(code, 0, out)
            self.assertNotIn("不使用", out, out)
        finally:
            shutil.rmtree(d)

    def test_frame_passed_to_named_type_component_blocks(self):
        d = project("const S = ({f}) => <Blob frame={f} at={3} />;\n")
        try:
            code, out = run(d)
            self.assertEqual(code, 1, out)
            self.assertIn("只认 f", out)
        finally:
            shutil.rmtree(d)

    def test_extra_frame_prop_on_frameless_component_still_reported(self):
        d = project("const S = ({f}) => <Plain f={f} text='a' />;\n")
        try:
            code, out = run(d)
            self.assertIn("不使用", out)
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
