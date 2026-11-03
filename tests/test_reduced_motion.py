from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTO = ROOT / "assets" / "lecture-template" / "src" / "auto.tsx"
CINEMA = ROOT / "assets" / "lecture-template" / "src" / "cinema.tsx"
RM = ROOT / "assets" / "lecture-template" / "src" / "reduced-motion.ts"
CLI = ROOT / "scripts" / "notebook-video.mjs"
GOLDEN_STORY = ROOT / "tests" / "fixtures" / "compose-golden" / "text__src_story.ts"


class ReducedMotionWiringTest(unittest.TestCase):
    """P2-21 验收③：减少动态后内容顺序完整。

    降低动态是**预览 / 可访问性**方案，成片语义不能变：元素仍按 `at` 逐个出现，
    只是不动（不淡入、不上浮、不逐字、相机不漂、转场不甩）。所以每个动效入口
    都必须读 REDUCED_MOTION 而不是自顾自地插值。
    """

    def test_module_reads_input_props(self):
        src = RM.read_text(encoding="utf-8")
        self.assertIn("getInputProps", src)
        self.assertIn("nvReducedMotion", src)

    def test_enter_and_reveal_are_wired(self):
        src = AUTO.read_text(encoding="utf-8")
        self.assertIn("import {REDUCED_MOTION} from './reduced-motion';", src)
        # enter：reduced 时直接到位
        self.assertIn("if (REDUCED_MOTION) return {opacity: f >= at ? 1 : 0};", src)
        # RevealText：reduced 时不逐字显现
        self.assertIn("REDUCED_MOTION ? (f >= at ? 1 : 0)", src)

    def test_camera_and_transition_are_wired(self):
        src = CINEMA.read_text(encoding="utf-8")
        self.assertIn("import {REDUCED_MOTION} from './reduced-motion';", src)
        self.assertIn("if (REDUCED_MOTION) return 'fade';", src)   # 转场退化为 fade，不是 hard
        self.assertIn("REDUCED_MOTION ? 0 :", src)                  # drift 归零

    def test_transition_fades_not_hard(self):
        """fade 是「换过来」，hard 是「切断」——降低动态不该把换镜的语义砍掉。"""
        src = CINEMA.read_text(encoding="utf-8")
        self.assertIn("if (REDUCED_MOTION) return 'fade';", src)
        self.assertNotIn("if (REDUCED_MOTION) return 'hard';", src)


class ReducedMotionFlagTest(unittest.TestCase):
    """CLI 的 --reduced-motion：纯布尔与 =on 都认，且不能被 parseFlags 当未知参数拒掉。"""

    @staticmethod
    def take(argv):
        """照抄 takeReducedMotion 的语义（node 里跑真函数，不复述实现）。"""
        r = subprocess.run(
            ["node", "-e", """
            const fs = require('fs');
            const src = fs.readFileSync(process.argv[1], 'utf8');
            const m = src.match(/const takeReducedMotion = [\\s\\S]*?\\n};/);
            if (!m) { console.error('takeReducedMotion not found'); process.exit(2); }
            eval(m[0] + '; globalThis.__fn = takeReducedMotion;');
            const out = globalThis.__fn(JSON.parse(process.argv[2]));
            console.log(JSON.stringify(out));
            """, str(CLI), json.dumps(argv)],
            capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
        if r.returncode != 0:
            raise AssertionError(f"取不到 takeReducedMotion：{r.stderr}")
        return json.loads(r.stdout)

    def test_bare_flag(self):
        on, rest = self.take(["proj", "out.mp4", "--reduced-motion"])
        self.assertTrue(on)
        self.assertEqual(rest, ["proj", "out.mp4"])

    def test_equals_on(self):
        on, rest = self.take(["--reduced-motion=on", "proj"])
        self.assertTrue(on)
        self.assertEqual(rest, ["proj"])

    def test_absent(self):
        on, rest = self.take(["proj", "--fx=off"])
        self.assertFalse(on)
        self.assertEqual(rest, ["proj", "--fx=off"])

    def test_source_wires_flag_into_render(self):
        src = CLI.read_text(encoding="utf-8")
        self.assertIn("const takeReducedMotion = (argv) => {", src)
        # 每个渲染入口都要把 reducedMotion 传下去（render / render-range / preview / poster）
        self.assertGreaterEqual(src.count("reducedMotion"), 6, "有渲染入口漏接 reducedMotion")


class PropsMergeTest(unittest.TestCase):
    """--props 只接受一次：nvFx / hideCaptions / nvReducedMotion 必须合并，不能互相覆盖。

    不合并的话 nvFx 会悄悄关掉（卷页退回折痕版），或者 reduced-motion 静默失效——
    两者都是「渲染成功、行为不对」的静默降级。
    """

    def test_merge_keeps_all_keys(self):
        r = subprocess.run(
            ["node", "-e", """
            const fs = require('fs'), os = require('os'), path = require('path');
            const src = fs.readFileSync(process.argv[1], 'utf8');
            const m = src.match(/const buildPropsArg = [\\s\\S]*?\\n};/);
            if (!m) { console.error('buildPropsArg not found'); process.exit(2); }
            eval(m[0] + '; globalThis.__bpa = buildPropsArg;');
            // 模拟 remotionRender 的合并：fx 的 props + reducedMotion
            const merged = {nvFx: 'on'};
            merged.nvReducedMotion = 'on';
            const arg = globalThis.__bpa(merged);
            const file = arg.slice('--props='.length);
            console.log(fs.readFileSync(file, 'utf8'));
            """, str(CLI)],
            capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        props = json.loads(r.stdout)
        self.assertEqual(props.get("nvFx"), "on")
        self.assertEqual(props.get("nvReducedMotion"), "on")

    def test_render_merges_fx_props_instead_of_overwriting(self):
        src = CLI.read_text(encoding="utf-8")
        # 合并而不是 push 两个 --props：fx.args 的 props 被读出来 Object.assign 进 mergedProps
        self.assertIn("Object.assign(mergedProps, JSON.parse(raw))", src)
        self.assertIn("if (reducedMotion) mergedProps.nvReducedMotion = 'on';", src)
        # 只推一次 --props（buildPropsArg 的产物）
        self.assertEqual(src.count("nodeArgs.push(buildPropsArg(mergedProps))"), 1)


class ContentOrderTest(unittest.TestCase):
    """验收③的静态保证：内容顺序不依赖动画。

    元素的 `at` 是语义顺序（说到哪、亮到哪）。动画只是表现——去掉动画后
    内容仍按 `at` 逐个到位，不靠淡入/上浮「补」信息。
    """

    def test_every_element_has_a_legal_appear_time(self):
        """每个元素都要有明确的出现时刻（at ≥ 0、有限）——去掉动画后仍按 at 逐个到位。

        不能要求 at 单调：flow 的并列项是**交错铺开**的（S3 实测 [8, 80, 76, 141, 137]），
        那是设计，不是乱序。要保证的是「每个元素都有时刻」，不是「时刻排成一条线」。
        """
        ts = GOLDEN_STORY.read_text(encoding="utf-8")
        start = ts.index("{", ts.index("export const STORY"))
        d = json.loads(ts[start:ts.rindex("}") + 1])
        for sid, shot in d.items():
            for e in shot.get("elements") or []:
                at = e.get("at")
                self.assertIsInstance(at, int, f"{sid}.{e.get('id')} 没有 at —— 去掉动画后它会在第 0 帧就出现")
                self.assertGreaterEqual(at, 0, f"{sid}.{e.get('id')} at={at} 是负数")

    def test_reduced_motion_does_not_change_story_table(self):
        """reduced motion 是渲染侧开关，**不能**改 story.ts 的内容——成片语义不变。"""
        src = CLI.read_text(encoding="utf-8")
        self.assertNotIn("story.ts", src.split("buildPropsArg")[0].split("takeReducedMotion")[-1])
        # 更直接：reducedMotion 只进 props，不进 compose/resolve 的任何参数
        self.assertIn("mergedProps.nvReducedMotion = 'on'", src)


if __name__ == "__main__":
    unittest.main()
