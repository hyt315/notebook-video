#!/usr/bin/env python3
"""Tests for the 3.3.0 real page-turn transitions (pageturn / peel via @remotion/effects pageTurn, WebGPU).

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
        # P2-23：CurlKind 的真源在 transitions/meta.ts（cinema 只 re-export TransitionKind）
        self.assertIn("'pageturn' | 'peel'", read("assets/lecture-template/src/transitions/meta.ts"))

    def test_fallback_without_gpu_is_css_pageflip(self):
        fx = read("assets/lecture-template/src/fx.tsx")
        meta = read("assets/lecture-template/src/transitions/meta.ts")
        # peel 退回 drop（「揭起」没有 CSS 等价物）；pageturn 退回 pageflip（折痕翻页），
        # 不是 slide —— 那是「横移」，观众认不出是翻页。P2-23：真源在 meta.ts 的 TRANSITION_META。
        self.assertRegex(meta, r"fallback: 'pageflip'")
        self.assertRegex(meta, r"fallback: 'drop'")
        # 缺省关：只有渲染器探针通过、传了 {nvFx:'on'} 才开
        self.assertIn("?.nvFx === 'on'", fx)
        cin = read("assets/lecture-template/src/cinema.tsx")
        # 3.9.0：退回值只写在 FX_FALLBACK 一处，cinema 引它，不再各写一份字面量。
        self.assertIn("if (d === 'pageturn') return fx ? d : FX_FALLBACK.pageturn;", cin)
        self.assertIn("if (d === 'peel') return fx ? d : FX_FALLBACK.peel;", cin)
        self.assertIn("if (craft === 'pageturn') return fx ? craft : FX_FALLBACK.pageturn;", cin)

    def test_every_skin_defaults_to_a_page_turn(self):
        # 3.9.0：翻页不再是「手作皮肤专属」。笔记本影片换一页就是翻一页，
        # 皮肤只决定翻的**方式**：papercut 从底板上揭起（peel），其余一律绕折痕翻过去（pageturn）。
        want = {"journal": "pageturn", "archive": "pageturn", "papercut": "peel",
                "flat": "pageturn", "cel": "pageturn"}
        for skin, kind in want.items():
            m = re.search(r"transition:\s*'([\w-]+)'", read(f"assets/lecture-template/src/theme/{skin}.tsx"))
            self.assertEqual(m.group(1), kind, skin)

    def test_compose_leaves_the_transition_to_the_engine(self):
        # 缺省值只能有一处。compose 缺省写 "auto"，由皮肤的 craft.transition 决定；
        # 3.9.0 之前它缺省写 fade，把皮肤声明的翻页**覆盖**掉了 ——
        # 于是只要 story 没显式写 "pageturn"，全片就一处翻页都没有（观众看到的是淡入淡出）。
        src = read("scripts/compose-story.py")
        self.assertIn(
            '"transition": (str(story.get("transition")) if (story.get("transition") and k > 0) else "auto")',
            src)

    def test_transition_whitelist_covers_engine_kinds(self):
        # 转场种类有两处列表：引擎的 TransitionKind（TS 类型）与分镜表校验的白名单。
        # 白名单可以多几个输入别名（auto / cut / reveal / handoff），但**不能漏**引擎认识的值——
        # 漏了的后果是「引擎支持、分镜表却报错」：使用者在文档里看到的写法会被拒绝。
        cin = read("assets/lecture-template/src/cinema.tsx")
        kinds = re.findall(r"'([\w-]+)'", re.search(r"export type TransitionKind = ([^;]+);", cin).group(1))
        rs = read("scripts/resolve-shots.py")
        allowed = set(re.findall(r'"([\w-]+)"', re.search(r"TRANSITIONS = \(([^)]+)\)", rs).group(1)))
        self.assertEqual([k for k in kinds if k not in allowed], [],
                         f"分镜表白名单缺少引擎认识的转场：{[k for k in kinds if k not in allowed]}")

    def test_fold_direction_is_defined_once(self):
        # CSS 折页与 GPU 卷页必须同向，而「同向」只能定义一次（P2-23 搬到 transitions/meta.ts）：
        # PageFold 的 K 由 PAGETURN_FOLD_DIRECTION 推导（transitions/pagefold.tsx），
        # 不许在 index.tsx 或 fx.tsx 里再写一遍角度。
        meta = read("assets/lecture-template/src/transitions/meta.ts")
        self.assertIn("export const PAGETURN_FOLD_DIRECTION = -78;", meta)
        fx = read("assets/lecture-template/src/fx.tsx")
        self.assertIn("foldDirection: PAGETURN_FOLD_DIRECTION,", fx)
        pf = read("assets/lecture-template/src/transitions/pagefold.tsx")
        self.assertIn("Math.tan((90 - Math.abs(PAGETURN_FOLD_DIRECTION))", pf)
        self.assertNotIn("= -78", pf)
        idx = read("assets/lecture-template/src/index.tsx")
        self.assertNotIn("Math.tan((90 - Math.abs(PAGETURN_FOLD_DIRECTION))", idx)

    def test_auto_falls_back_to_a_page_flip(self):
        # story 和皮肤都没表态时（自定义皮肤），auto 也必须落在翻页上，不能退回 whip / zoom。
        cin = read("assets/lecture-template/src/cinema.tsx")
        tail = cin.split("if (craft === 'slide' || craft === 'drop')")[1].split("};")[0]
        self.assertIn("return 'pageflip';", tail)
        self.assertNotIn("whip-left", tail)

    def test_curl_frames_match_between_composition_and_renderer(self):
        # P2-23：渲染侧的真源搬到 transitions/meta.ts（fx.tsx 只 re-export）；
        # 3.9.0：构建期的真源在转场计划（scripts/transition-plan.mjs）。两边必须同值。
        a = re.search(r"export const CURL_FRAMES\s*=\s*(\d+)",
                      read("assets/lecture-template/src/transitions/meta.ts")).group(1)
        b = re.search(r"export const CURL_FRAMES\s*=\s*(\d+)", read("scripts/transition-plan.mjs")).group(1)
        self.assertEqual(a, b)
        # fx.tsx 必须 re-export（不能有第二份字面量）
        fx = read("assets/lecture-template/src/fx.tsx")
        self.assertIn("export {CURL_FRAMES", fx)
        self.assertNotIn("export const CURL_FRAMES = ", fx)

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
