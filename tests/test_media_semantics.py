#!/usr/bin/env python3
"""P1-34 媒介语义：flat/cel 只有 craft 能力，不是手作媒介。

旧版用 `Boolean(THEME.craft)` 同时决定纸卡与拟音，而 flat / cel 也声明 craft，
于是中性皮肤意外获得手作纸卡和纸片声。这里跑真正的 planSfx：同一镜头注入五套皮肤，
断言只有 journal / papercut / archive 发生拟音映射，且显式 sfx 不被改写。

需要 esbuild 才能执行 TS。源码树里的模板不常驻 node_modules：
CI 在 npm ci 之后单独跑本测试；本地可用 NOTEBOOK_VIDEO_NODE_MODULES=<deps> 指定。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "assets" / "lecture-template"
SFX = TPL / "src" / "sfx.ts"


def esbuild_pkg() -> Path | None:
    """返回装 esbuild 的 node_modules 目录（不是可执行文件）。

    注意别去调 `node_modules/esbuild/bin/esbuild`：那个路径在 Linux 上可能是
    ELF 原生二进制（不是 JS shim），`node <elf>` 会报 "Invalid or unexpected token"。
    走 JS API（require('esbuild').buildSync）两端都稳。
    """
    deps = os.environ.get("NOTEBOOK_VIDEO_NODE_MODULES")
    candidates = []
    if deps:
        candidates.append(Path(deps) / "esbuild")
    candidates.append(TPL / "node_modules" / "esbuild")
    return next((p for p in candidates if p.is_dir()), None)


class ThemeDeclarationsTest(unittest.TestCase):
    def test_five_skins_declare_the_expected_medium(self):
        for skin in ("flat", "cel", "journal", "papercut", "archive"):
            src = (TPL / "src" / "theme" / f"{skin}.tsx").read_text(encoding="utf-8")
            m = re.search(r"craft:\s*\{[^}]*?medium:\s*'([^']+)'", src, re.S)
            self.assertIsNotNone(m, skin)
            self.assertEqual(m.group(1), skin)

    def test_auto_and_sfx_share_one_semantic_helper(self):
        auto = (TPL / "src" / "auto.tsx").read_text(encoding="utf-8")
        sfx = SFX.read_text(encoding="utf-8")
        self.assertIn("isHandmadeMedium(THEME)", auto)
        self.assertIn("isHandmadeMedium(theme)", sfx)
        self.assertNotIn("Boolean((THEME as any).craft)", auto)
        self.assertNotIn("THEME.craft ? CRAFT_SFX", sfx)


class PlanSfxBehaviorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which("node")
        cls.esbuild = esbuild_pkg()
        if not cls.node or not cls.esbuild:
            raise unittest.SkipTest("node/esbuild unavailable (run after npm ci, or set NOTEBOOK_VIDEO_NODE_MODULES)")
        cls.tmp = Path(tempfile.mkdtemp(prefix="nv-medium-sfx-"))
        entry = cls.tmp / "entry.ts"
        entry.write_text(
            "import {planSfx} from " + json.dumps(SFX.as_posix()) + ";\n"
            "const shot = {id:'S1', from:0, to:120, duration:120, beats:[10,55,100], media:['text'], live:[], move:'收束', transition:'auto'};\n"
            "const themes = [['flat',{craft:{medium:'flat'}}],['cel',{craft:{medium:'cel'}}],"
            "['journal',{craft:{medium:'journal'}}],['papercut',{craft:{medium:'papercut'}}],"
            "['archive',{craft:{medium:'archive'}}]];\n"
            "const plans = Object.fromEntries(themes.map(([name, theme]) => [name, "
            "planSfx([shot],[0],180,'normal',theme).map(c => `${c.event}@${c.hit}`)]));\n"
            "const explicit = {event:'pop', beat:0};\n"
            "plans.explicit = planSfx([{...shot, sfxAuto:false, sfx:[explicit]}],[0],180,'normal',{craft:{medium:'journal'}})"
            ".map(c => `${c.event}@${c.hit}`);\n"
            "// 第二镜带翻页转场：翻页纸声属于动作拟音，五个皮肤共用同一条代码路径\n"
            "const two = [shot, {...shot, id:'S2', from:120, to:240, duration:120, transition:'pageturn'}];\n"
            "plans.foley = Object.fromEntries(themes.map(([name, theme]) => [name, "
            "planSfx(two,[0],240,'normal',theme).filter(c => c.event === 'page').map(c => `page@${c.hit}`)]));\n"
            "console.log(JSON.stringify(plans));\n",
            encoding="utf-8",
        )
        out = cls.tmp / "bundle.cjs"
        cfg = {
            "entryPoints": [str(entry)],
            "bundle": True,
            "platform": "node",
            "format": "cjs",
            "packages": "external",
            "jsx": "automatic",
            "outfile": str(out),
            "logLevel": "error",
        }
        script = (
            f"const esbuild = require({json.dumps(str(cls.esbuild))});\n"
            f"esbuild.buildSync({json.dumps(cfg)});\n"
        )
        build = subprocess.run([cls.node, "-e", script], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", cwd=TPL)
        if build.returncode:
            raise AssertionError(build.stdout + build.stderr)
        node_modules = cls.esbuild.parent
        run = subprocess.run([cls.node, str(out)], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=60,
                             env={**os.environ, "NODE_PATH": str(node_modules)})
        if run.returncode:
            raise AssertionError(run.stdout + run.stderr)
        cls.plans = json.loads(run.stdout)

    def test_neutral_skins_keep_ui_sounds(self):
        for skin in ("flat", "cel"):
            self.assertEqual(self.plans[skin], ["chapter@2", "pop@10", "highlight@55", "success@100"], skin)

    def test_handmade_skins_get_medium_sounds(self):
        # 3.8.0 瘦身后只剩 pop→place、success→stamp 两条映射；中拍统一是 highlight（不再分 click/rustle）。
        for skin in ("journal", "papercut", "archive"):
            self.assertEqual(self.plans[skin], ["chapter@2", "place@10", "highlight@55", "stamp@100"], skin)

    def test_explicit_sfx_is_not_rewritten(self):
        self.assertEqual(self.plans["explicit"], ["pop@10"])

    def test_non_first_shot_keeps_page_foley_for_every_skin(self):
        # 翻页纸声是**动作拟音**，不跟着媒介名单变：五个皮肤都该在第二镜翻页处听到纸声。
        # 判据写行为（跑一遍 planSfx），不再比对源码字符串——P2-23 把 Set 换成 isPageTurnKind()
        # 之后，旧的字符串锚点就假失败了，而行为其实没变。
        for skin in ("flat", "cel", "journal", "papercut", "archive"):
            self.assertEqual(self.plans["foley"][skin], ["page@123"], skin)


if __name__ == "__main__":
    unittest.main()
