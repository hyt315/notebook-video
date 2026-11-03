#!/usr/bin/env python3
"""P2-24 第三切片 · 动作 / 复现层与时间底座的边界契约。

这一片的前提是 `FPS` 只能有一个真源：`@L1.3` 换算、`build()` 的帧号、渲染模板的 fps
必须同数。所以除了「函数归属」，还要锁「FPS 只定义一次」「frame() 的运算顺序没变」。

另外 `resolve_act_at` 是作者最容易写错的地方（`@L1` / `@L1.3` / 数字帧三种写法），
它现在住在 story_acts.py，用行为测试钉住三种写法与两种失败路径。
"""
from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


acts = load("acts_contract", SCRIPTS / "story_acts.py")
stime = load("time_contract", SCRIPTS / "story_time.py")
cs = load("cs_acts_contract", SCRIPTS / "compose-story.py")


class FacadeTest(unittest.TestCase):
    # 只锁对外入口；visual_fp / action_fp / info_fp 是 check_reprises 的内部零件，不要求 re-export。
    FUNCS = ("resolve_act_at", "resolve_ink_acts", "resolve_sketch", "resolve_annotate",
             "check_draw", "check_reprises")

    def test_entrypoint_uses_acts_layer(self):
        for name in self.FUNCS:
            self.assertTrue(hasattr(acts, name), f"story_acts 缺 {name}")
            self.assertEqual(getattr(cs, name).__module__, "story_acts",
                             f"compose-story 的 {name} 不是 story_acts 的实现（有人又写了一份）")

    def test_entrypoint_uses_time_base(self):
        self.assertEqual(cs.frame.__module__, "story_time")
        self.assertEqual(cs.FPS, stime.FPS)

    def test_verb_tables_come_from_acts_layer(self):
        self.assertEqual(cs.SKETCH_VERBS, acts.SKETCH_VERBS)
        self.assertEqual(cs.INK_VERBS, acts.INK_VERBS)


# 判据脚本（validate-*/resolve-shots）各自有一份 FPS，且被一致性检查钉到模板值上；
# 「只定义一次」只对排版链路成立——这些文件才是同一份运行期代码。
COMPOSE_CHAIN = ("compose-story.py", "story_time.py", "story_acts.py",
                 "story_text.py", "story_caption.py", "story_camera.py")


class SingleSourceTest(unittest.TestCase):
    def _defs(self, pattern: str) -> list[str]:
        hits = []
        for name in COMPOSE_CHAIN:
            f = SCRIPTS / name
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if re.match(pattern, line):
                    hits.append(f"{name}:{i}")
        return hits

    def test_fps_defined_once(self):
        hits = self._defs(r"^FPS\s*=")
        self.assertEqual(len(hits), 1, f"FPS 定义处应唯一，实际 {hits}")
        self.assertTrue(hits[0].startswith("story_time.py:"), f"FPS 真源应在 story_time，实际 {hits}")

    def test_verb_tables_defined_once(self):
        for pattern, name in ((r"^SKETCH_VERBS\s*=", "SKETCH_VERBS"), (r"^INK_VERBS\s*=", "INK_VERBS")):
            hits = self._defs(pattern)
            self.assertEqual(len(hits), 1, f"{name} 定义处应唯一，实际 {hits}")
            self.assertTrue(hits[0].startswith("story_acts.py:"), f"{name} 真源应在 story_acts，实际 {hits}")

    def test_acts_layer_has_no_reverse_import(self):
        src = (SCRIPTS / "story_acts.py").read_text(encoding="utf-8")
        for ln in src.splitlines():
            if re.match(r"\s*(import|from)\s+", ln):
                self.assertNotIn("compose", ln, f"story_acts 反向依赖主文件：{ln.strip()}")


class FrameMathTest(unittest.TestCase):
    def test_round_trip(self):
        self.assertEqual(stime.frame(0), 0)
        self.assertEqual(stime.frame(1000), 30)
        self.assertEqual(stime.frame(33.33), 1)
        self.assertEqual(stime.frame(16.6), 0)   # 四舍五入，不是向上取整

    def test_compose_frame_is_the_same(self):
        self.assertEqual([cs.frame(x) for x in (0, 500, 1000, 2000)], [0, 15, 30, 60])


class ResolveActAtTest(unittest.TestCase):
    CUES = [{"words": [{"start": 100}, {"start": 1000}]}, {"words": [{"start": 2000}]}]

    def test_numeric_is_frame_in_shot(self):
        self.assertEqual(acts.resolve_act_at(12, [10], [[0]], self.CUES, 0), 12)
        self.assertEqual(acts.resolve_act_at(0, [10], [[0]], self.CUES, 4), 0)

    def test_line_start(self):
        self.assertEqual(acts.resolve_act_at("@L2", [10, 40], [[0], [1]], self.CUES, 0), 40)

    def test_word_start_is_absolute_then_shot_local(self):
        # 第 2 句第 2 个词从 2000ms 开始 = 第 60 帧；镜头从第 10 帧起 → 本镜第 50 帧
        self.assertEqual(acts.resolve_act_at("@L2.1", [10, 40], [[0], [1]], self.CUES, 10), 50)

    def test_unparseable_returns_none(self):
        self.assertIsNone(acts.resolve_act_at("later", [10], [[0]], self.CUES, 0))
        self.assertIsNone(acts.resolve_act_at("@L9", [10], [[0]], self.CUES, 0))
        self.assertIsNone(acts.resolve_act_at(None, [10], [[0]], self.CUES, 0))


class SketchValidationTest(unittest.TestCase):
    class Collector:
        def __init__(self):
            self.errors, fixes, hints = [], [], []

        def err(self, m): self.errors.append(m)
        def fix(self, m): pass
        def hint(self, m): pass

    def test_bad_part_blocks_and_returns_none(self):
        p = self.Collector()
        out = acts.resolve_sketch(p, "S1", {"draw": "lib:bulb", "parts": ["nope"]}, [0], [[0]], [{"words": [{"start": 0}]}], 0)
        self.assertIsNone(out, "部位名写错时必须返回 None（不能产出没图的 sketch）")
        self.assertTrue(p.errors, "必须报错并点名")

    def test_good_sketch_gets_frames(self):
        p = self.Collector()
        out = acts.resolve_sketch(p, "S1", {"draw": "lib:bulb", "acts": [{"do": "point", "at": 3}]},
                                  [0], [[0]], [{"words": [{"start": 0}]}], 0)
        self.assertIsNotNone(out)
        self.assertEqual(out["frames"], [{"at": 3, "do": "point"}])
        # 未用到的键必须整个省略而不是写 None：story.ts 里 `target?: string` 不吃 null
        for fr in out["frames"]:
            self.assertNotIn(None, fr.values(), f"帧里不能出现 null 值：{fr}")
        self.assertNotIn("acts", out)


class PackageIncludesModulesTest(unittest.TestCase):
    def test_package_collects_acts_and_time(self):
        pk = load("pkg_acts_contract", SCRIPTS / "package-skill.py")
        files = {p.relative_to(ROOT).as_posix() for p in pk.collect_files()}
        self.assertIn("scripts/story_acts.py", files)
        self.assertIn("scripts/story_time.py", files)


if __name__ == "__main__":
    unittest.main()
