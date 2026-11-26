"""帧参数是必填类型：传错名字或漏传，tsc 必须报错（取代原 validate-frame-props.py 的负向用例）。

需要模板依赖（typescript）。模板里没有 node_modules 时，用 NV_E2E_NODE_MODULES 指向一份装好的依赖；
都没有就 skip 并写明原因。只跑 tsc --noEmit，不打包、不渲染。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "assets" / "lecture-template"
NODE = shutil.which("node")
DEPS = Path(os.environ["NV_E2E_NODE_MODULES"]) if os.environ.get("NV_E2E_NODE_MODULES") else TPL / "node_modules"
TSC = DEPS / "typescript" / "bin" / "tsc"

BAD_SCENE = """import React from 'react';
import {Typewriter} from './fxkit';
import {Callout} from './toolkit';
export const WrongName: React.FC<{f: number}> = ({f}) => <Typewriter f={f} text="x" />;
export const Missing: React.FC<{f: number}> = () => <Callout x={0} y={0} w={10} h={10} start={0} text="x" />;
"""


def _link_dir(src: Path, dst: Path) -> None:
    try:
        os.symlink(src, dst, target_is_directory=True)
    except OSError:
        if sys.platform != "win32":
            raise
        subprocess.run(["cmd", "/c", "mklink", "/J", str(dst), str(src)], check=True, capture_output=True)


def _unlink_dir(dst: Path) -> None:
    if dst.is_symlink() or (sys.platform == "win32" and dst.exists()):
        try:
            os.rmdir(dst)
        except OSError:
            pass


@unittest.skipUnless(NODE, "node 未安装")
@unittest.skipUnless(TSC.is_file(), "没有 typescript 依赖：在模板跑 npm ci，或设 NV_E2E_NODE_MODULES")
class FrameTypesTest(unittest.TestCase):
    def test_wrong_or_missing_frame_prop_fails_tsc(self):
        with tempfile.TemporaryDirectory(prefix="nv-frame-types-") as td:
            proj = Path(td)
            shutil.copytree(TPL / "src", proj / "src")
            shutil.copytree(TPL / "manifests", proj / "manifests")  # index.tsx import ../manifests/caption-cues.json（#14）
            shutil.copy(TPL / "tsconfig.json", proj / "tsconfig.json")
            nm = proj / "node_modules"
            _link_dir(DEPS, nm)
            try:
                (proj / "src" / "zz-frame-negative.tsx").write_text(BAD_SCENE, encoding="utf-8")
                r = subprocess.run([NODE, str(TSC), "--noEmit", "-p", "."], cwd=proj,
                                   capture_output=True, text=True, timeout=300)
            finally:
                _unlink_dir(nm)
            out = r.stdout + r.stderr
            self.assertNotEqual(r.returncode, 0, out)
            bad = [ln for ln in out.splitlines() if "zz-frame-negative.tsx" in ln]
            self.assertTrue(any("(4," in ln for ln in bad), f"传错名（f 给 fxkit）没被 tsc 拦：{out}")
            self.assertTrue(any("(5," in ln and "frame" in ln for ln in bad), f"漏传 frame 没被 tsc 拦：{out}")
            others = [ln for ln in out.splitlines() if "error TS" in ln and "zz-frame-negative.tsx" not in ln]
            self.assertEqual(others, [], "模板本身应当 0 个类型错误")


if __name__ == "__main__":
    unittest.main()
