#!/usr/bin/env python3
"""Tests for the 3.5.0 real page-turn transitions (pageturn / peel via @remotion/effects pageTurn, WebGPU).

Offline: no browser is started. The browser probe itself is exercised end-to-end by
`node scripts/notebook-video.mjs fx-probe PROJECT --force` (see references/fx-effects.md).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "assets" / "lecture-template"
SRC = TPL / "src"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class PageTurnContract(unittest.TestCase):
    def test_transition_lists_include_curl_kinds(self):
        ins = re.search(r"export const TRANSITIONS = \[([^\]]*)\]", read("assets/lecture-template/src/insert.tsx")).group(1)
        rs = re.search(r"^TRANSITIONS = \(([^)]*)\)", read("scripts/resolve-shots.py"), re.M).group(1)
        vc = re.search(r"^TRANSITIONS = \{([^}]*)\}", read("scripts/validate-composition.py"), re.M).group(1)
        for kind in ("pageturn", "peel"):
            self.assertIn(f"'{kind}'", ins)
            self.assertIn(f'"{kind}"', rs)
            self.assertIn(f'"{kind}"', vc)
        self.assertIn("'pageturn' | 'peel'", read("assets/lecture-template/src/cinema.tsx"))

    def test_fallback_is_the_old_medium_transition(self):
        fx = read("assets/lecture-template/src/fx.tsx")
        self.assertRegex(fx, r"FX_FALLBACK[^=]*=\s*\{pageturn: 'slide', peel: 'drop'\}")
        # 缺省关：只有渲染器探针通过、传了 {nvFx:'on'} 才开
        self.assertIn("?.nvFx === 'on'", fx)
        cin = read("assets/lecture-template/src/cinema.tsx")
        self.assertIn("if (d === 'pageturn' || d === 'peel') return fx ? d : FX_FALLBACK[d];", cin)
        self.assertIn("return isChapter ? 'drop' : fx ? craft : FX_FALLBACK[craft];", cin)

    def test_hand_made_skins_default_to_real_page_turn(self):
        want = {"journal": "pageturn", "archive": "pageturn", "papercut": "peel"}
        for skin, kind in want.items():
            m = re.search(r"transition:\s*'([\w-]+)'", read(f"assets/lecture-template/src/theme/{skin}.tsx"))
            self.assertEqual(m.group(1), kind, skin)
        for skin in ("flat", "cel"):  # 非手作皮肤不受影响
            self.assertNotRegex(read(f"assets/lecture-template/src/theme/{skin}.tsx"), r"transition:\s*'(pageturn|peel)'")

    def test_curl_frames_match_between_composition_and_renderer(self):
        a = re.search(r"export const CURL_FRAMES\s*=\s*(\d+)", read("assets/lecture-template/src/fx.tsx")).group(1)
        b = re.search(r"^export const CURL_FRAMES\s*=\s*(\d+)", read("scripts/fx-browser.mjs"), re.M).group(1)
        self.assertEqual(a, b)

    def test_probe_composition_is_registered(self):
        idx = read("assets/lecture-template/src/index.tsx")
        self.assertIn('<Composition id="NotebookVideoFxProbe"', idx)
        self.assertIn("export const FX_PROBE_COMPOSITION = 'NotebookVideoFxProbe';", read("scripts/fx-browser.mjs"))
        # 卷页那一层必须按输出像素密度画，否则 2560 交付里发糊
        self.assertIn("density={MODES['16:9'].scale", idx)

    def test_curl_geometry_is_a_pure_function_of_progress(self):
        fx = read("assets/lecture-template/src/fx.tsx")
        body = fx[fx.index("export const curlParams"):fx.index("export const PageCurl")]
        for banned in ("Math.random", "Date.now", "performance.now", "random("):
            self.assertNotIn(banned, body)

    def test_renderer_reports_p1_when_fx_is_unavailable(self):
        mv = read("scripts/make-video.mjs")
        self.assertIn("P1 真卷页未开启", mv)
        self.assertIn(".fx-probe.json", mv)

    def test_remotion_packages_pinned_to_one_exact_version(self):
        pkg = json.loads((TPL / "package.json").read_text(encoding="utf-8"))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        rem = {k: v for k, v in deps.items() if k == "remotion" or k.startswith("@remotion/")}
        self.assertIn("@remotion/effects", rem)
        self.assertEqual(len(set(rem.values())), 1, rem)
        version = next(iter(rem.values()))
        self.assertRegex(version, r"^\d+\.\d+\.\d+$", "Remotion 全家必须 --save-exact 同版本")
        lock = json.loads((TPL / "package-lock.json").read_text(encoding="utf-8"))
        for name in rem:
            self.assertEqual(lock["packages"][f"node_modules/{name}"]["version"], version, name)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_renderer_self_test(self):
        r = subprocess.run(["node", str(ROOT / "scripts" / "fx-browser.mjs"), "--self-test"], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
