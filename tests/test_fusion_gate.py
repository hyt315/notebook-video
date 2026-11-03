"""配比门禁：手账页承载 + 组件讲概念（3.6.0 改口径）。

两组回归夹具：
  · 讲火箭、全片却是字卡 / 柱条 / 对比卡 → 主题物从未出现，P0 并点名「火箭」；
  · 手账页 + 组件交替（cork-page）→ P0=0 且 P1=0，这是新主线该有的样子。
线稿片（rocket-fusion）不再豁免：它仍 P0=0，但会被报「手账页 0%」——线稿不是必填项。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "scripts" / "compose-story.py"
GATE = ROOT / "scripts" / "validate-fusion.py"


def build(story: Path, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(COMPOSE), str(story), str(out)],
                          capture_output=True, text=True, timeout=180)


class FusionGate(unittest.TestCase):
    def test_components_only_rocket_fails(self):
        with tempfile.TemporaryDirectory() as td:
            r = build(ROOT / "examples" / "regress" / "rocket-components-only.story.json", td)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            g = subprocess.run([sys.executable, str(GATE), td], capture_output=True, text=True, timeout=60)
            self.assertEqual(g.returncode, 1, g.stdout + g.stderr)
            self.assertIn("P0", g.stdout)
            self.assertIn("火箭", g.stdout)

    def test_page_story_passes_both_gates(self):
        """手账页承载 + 组件讲解：这条必须 P0=0 且 P1=0。"""
        with tempfile.TemporaryDirectory() as td:
            r = build(ROOT / "examples" / "recipes" / "cork-page.story.json", td)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            g = subprocess.run([sys.executable, str(GATE), td], capture_output=True, text=True, timeout=60)
            self.assertEqual(g.returncode, 0, g.stdout + g.stderr)
            self.assertIn("P0=0 P1=0", g.stdout)
            self.assertRegex(g.stdout, r"手账页 6\d%")

    def test_linework_alone_is_not_enough(self):
        """全片只有线稿、没有手账页：P0 过（主题物出现了），但要被报「没有承载」。"""
        with tempfile.TemporaryDirectory() as td:
            r = build(ROOT / "examples" / "recipes" / "rocket-fusion.story.json", td)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            g = subprocess.run([sys.executable, str(GATE), td], capture_output=True, text=True, timeout=60)
            self.assertEqual(g.returncode, 0, g.stdout + g.stderr)
            self.assertIn("手账页只占 0%", g.stdout)

    # ---- 3.7.0 · 三种呈现模式共用一套约束，但配额不同 ----
    def _run_mode(self, td: str, story: dict, mode: str):
        story = dict(story, mode=mode)
        sp = Path(td) / f"{mode}.json"
        sp.write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")
        proj = Path(td) / mode
        r = build(sp, proj)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return subprocess.run([sys.executable, str(GATE), str(proj)], capture_output=True, text=True, timeout=60)

    def test_mode_switches_thresholds(self):
        """同一份全组件片：hybrid 会嫌「没有承载」，component 不嫌——配额随模式走。"""
        base = json.loads((ROOT / "examples" / "regress" / "rocket-components-only.story.json").read_text(encoding="utf-8"))
        base["subject_of_film"] = "abstract"
        base["subject_why"] = "这条只验模式契约，不讲具体东西。"
        with tempfile.TemporaryDirectory() as td:
            g_hy = self._run_mode(td, base, "hybrid")
            g_co = self._run_mode(td, base, "component")
            self.assertIn("手账页只占 0%", g_hy.stdout)
            self.assertNotIn("手账页只占 0%", g_co.stdout)
            # component 的组件下限是 60%，必须比 hybrid 的 25% 更严
            self.assertIn("60%", g_co.stdout)

    def test_component_mode_passes_when_subject_named(self):
        """全组件片没有纸可贴：主题物只要在某镜的 see 里被点名，就不该判 P0。"""
        story = json.loads((ROOT / "examples" / "regress" / "rocket-components-only.story.json").read_text(encoding="utf-8"))
        story["mode"] = "component"
        story["chapters"][0]["shots"][0]["see"] = "三张卡片并列，标题分别写着火箭的三段规格"
        with tempfile.TemporaryDirectory() as td:
            sp = Path(td) / "story.json"
            sp.write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")
            r = build(sp, Path(td) / "proj")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            g = subprocess.run([sys.executable, str(GATE), str(Path(td) / "proj")], capture_output=True, text=True, timeout=60)
            self.assertIn("P0=0", g.stdout, g.stdout)

    def test_freeform_mode_rejects_multi_card_layouts(self):
        """声明 freeform 却整片是卡片：必须被点名，不能默默按 hybrid 判。"""
        base = json.loads((ROOT / "examples" / "regress" / "rocket-components-only.story.json").read_text(encoding="utf-8"))
        base["subject_of_film"] = "abstract"
        base["subject_why"] = "只验模式契约。"
        with tempfile.TemporaryDirectory() as td:
            g = self._run_mode(td, base, "freeform")
            self.assertIn("名不副实", g.stdout, g.stdout)

    def test_freeform_recipe_passes(self):
        """全非组件样板：手账页 50% + 直书 50%，零卡片 → P0=0 P1=0。"""
        with tempfile.TemporaryDirectory() as td:
            r = build(ROOT / "examples" / "recipes" / "jie-freeform.story.json", td)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            g = subprocess.run([sys.executable, str(GATE), td], capture_output=True, text=True, timeout=60)
            self.assertIn("P0=0 P1=0", g.stdout, g.stdout)
            self.assertIn("模式 freeform", g.stdout)

    def test_abstract_exempt_with_reason(self):
        with tempfile.TemporaryDirectory() as td:
            story = json.loads((ROOT / "examples" / "regress" / "rocket-components-only.story.json").read_text(encoding="utf-8"))
            story["subject_of_film"] = "abstract"
            story["subject_why"] = "这一题讲的是复利这个观念，没有可画的具体东西。"
            sp = Path(td) / "story.json"
            sp.write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")
            proj = Path(td) / "proj"
            r = build(sp, proj)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            g = subprocess.run([sys.executable, str(GATE), proj], capture_output=True, text=True, timeout=60)
            self.assertEqual(g.returncode, 0, g.stdout + g.stderr)


if __name__ == "__main__":
    unittest.main()
