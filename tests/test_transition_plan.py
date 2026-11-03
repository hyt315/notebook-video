#!/usr/bin/env python3
"""P1-11：转场计划以结构化分镜表为输入，src/shots.ts 不再当第二份数据协议。

问题不在"正则写错了"，而在**它什么时候会悄悄错**：`from:` 与 `id:` 必须同一行、
字段顺序变了就漏、生成方式一换就漏——漏掉的后果不是报错，而是某处翻页退回折痕版，
渲染成功、时长照对、门禁照样过。

所以这组测试关心的不是"解析得对不对"，而是：
  ① 有 manifests/shots.resolved.json 时，shots.ts 无论怎么排版都不影响结果；
  ② 没有 manifest 的旧工程仍能跑，但**会说出来**走的是旧路径；
  ③ 判据（哪种转场算卷页）与引擎 cinema.tsx 的一致性能被测试发现，而不是靠人记。
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
CLI = ROOT / "scripts" / "transition-plan.mjs"
NODE = shutil.which("node")


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def mkproj(root: Path, shots, *, skin="journal", craft="pageturn", shots_ts=None) -> Path:
    """造一个最小工程：manifests/shots.resolved.json + src/theme/<skin>.tsx（+ 可选 src/shots.ts）。"""
    doc = {"duration": sum(s.get("duration", 0) for s in shots) or (shots[-1]["to"] if shots else 0),
           "theme": skin, "shots": shots}
    write(root / "manifests" / "shots.resolved.json", json.dumps(doc, ensure_ascii=False, indent=2))
    craft_line = f"transition: '{craft}', " if craft else ""
    write(root / "src" / "theme" / "active.ts",
          f"import {{THEME}} from './{skin}';\nexport {{THEME}};\n")
    write(root / "src" / "theme" / f"{skin}.tsx",
          "export const THEME: Theme = {\n  id: 'x',\n"
          f"  craft: {{medium: 'journal', {craft_line}fonts: []}},\n}};\n")
    if shots_ts is not None:
        write(root / "src" / "shots.ts", shots_ts)
    return root


def plan(project: Path) -> dict:
    if not NODE:
        raise unittest.SkipTest("node 不可用")
    r = subprocess.run([NODE, str(CLI), str(project), "--json"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    return json.loads(r.stdout)


SHOTS = [
    {"id": "S1", "from": 0, "to": 100, "duration": 100, "transition": "auto"},
    {"id": "S2", "from": 100, "to": 200, "duration": 100, "transition": "pageturn"},
    {"id": "S3", "from": 200, "to": 300, "duration": 100, "transition": "slide"},
    {"id": "S4", "from": 300, "to": 400, "duration": 100, "transition": "auto"},
]


class ManifestIsTheSourceTest(unittest.TestCase):
    def test_shots_ts_formatting_cannot_change_the_plan(self):
        """验收原文：字段顺序、换行、注释变化不影响结果。

        三种排版：原样紧凑、一镜多行加注释、以及一份**完全对不上**的 shots.ts（模拟生成方式变了）。
        有 manifest 时三者必须给出同一份窗口。
        """
        variants = {
            "compact": "S1:{id:'S1',from:0,to:100},S2:{id:'S2',from:100,to:200,transition:'pageturn'}",
            "multiline": "\n".join([
                "  S2: {",
                "    // 转场：翻到下页",
                "    transition: 'pageturn',",
                "    to: 200,",
                "    id: 'S2',",
                "    from: 100,",
                "  },",
            ]),
            "stale": "export const SHOTS = { S9: {id:'S9',from:0,to:10} };",
        }
        results = {}
        for name, ts in variants.items():
            with tempfile.TemporaryDirectory() as td:
                p = mkproj(Path(td) / "proj", SHOTS, shots_ts=ts)
                results[name] = plan(p)
        base = results["compact"]
        self.assertEqual(base["source"], "manifest")
        self.assertEqual(base["windows"], [[100, 121], [300, 321]], base["windows"])
        for name, got in results.items():
            self.assertEqual(got["windows"], base["windows"], f"{name} 排版影响了结果")
            self.assertEqual(got["source"], "manifest", name)

    def test_manifest_duration_is_used_for_total_frames(self):
        with tempfile.TemporaryDirectory() as td:
            p = mkproj(Path(td) / "proj", SHOTS)
            self.assertEqual(plan(p)["duration"], 400)

    def test_broken_manifest_falls_back_and_says_so(self):
        with tempfile.TemporaryDirectory() as td:
            p = mkproj(Path(td) / "proj", SHOTS,
                       shots_ts="S2: {id:'S2',from:100,to:200,transition:'pageturn'}")
            write(p / "manifests" / "shots.resolved.json", json.dumps({"shots": [{"id": "S1"}]}))
            got = plan(p)
            self.assertEqual(got["source"], "typescript")
            self.assertEqual(got["windows"], [[100, 121]], got["windows"])
            self.assertTrue(any("退回" in x for x in got["problems"]), got["problems"])

    def test_missing_manifest_falls_back_with_a_visible_problem(self):
        with tempfile.TemporaryDirectory() as td:
            p = mkproj(Path(td) / "proj", SHOTS,
                       shots_ts="export const SHOT_TOTAL = 400;\n  S2: {id:'S2',from:100,to:200,transition:'peel'},\n")
            (p / "manifests" / "shots.resolved.json").unlink()
            got = plan(p)
            self.assertEqual(got["source"], "typescript")
            self.assertEqual(got["windows"], [[100, 121]])
            self.assertEqual(got["duration"], 400)
            self.assertTrue(got["problems"])


class EffectiveTransitionTest(unittest.TestCase):
    def _kinds(self, declared, craft="pageturn"):
        with tempfile.TemporaryDirectory() as td:
            shots = [
                {"id": "S1", "from": 0, "to": 100, "transition": "pageturn"},
                {"id": "S2", "from": 100, "to": 200, "transition": declared},
                {"id": "S3", "from": 200, "to": 300, "transition": declared},
            ]
            got = plan(mkproj(Path(td) / "proj", shots, craft=craft))
            return got["boundaries"][1]["kind"], got["boundaries"][1]["curl"]

    def test_first_shot_never_has_a_transition(self):
        with tempfile.TemporaryDirectory() as td:
            got = plan(mkproj(Path(td) / "proj", SHOTS))
            self.assertIsNone(got["boundaries"][0]["kind"])
            self.assertFalse(got["boundaries"][0]["curl"])
            self.assertEqual(got["windows"][0][0], 100, "首镜不该进窗口")

    def test_explicit_plain_kinds_are_not_curl(self):
        for kind in ("hard", "fade", "zoom", "whip-left", "whip-right", "slide", "drop"):
            self.assertEqual(self._kinds(kind), (kind, False), kind)

    def test_explicit_curl_kinds(self):
        for kind in ("pageturn", "peel"):
            self.assertEqual(self._kinds(kind, craft="slide"), (kind, True), kind)

    def test_auto_follows_the_skin(self):
        self.assertEqual(self._kinds("auto", craft="pageturn"), ("pageturn", True))
        self.assertEqual(self._kinds("auto", craft="peel"), ("peel", True))
        self.assertEqual(self._kinds("auto", craft="slide"), ("slide", False))
        self.assertEqual(self._kinds("auto", craft="drop"), ("drop", False))
        # 皮肤没声明媒介转场 → pageflip（纯 CSS 折痕翻页，不需要 WebGPU）
        self.assertEqual(self._kinds("auto", craft=None), ("pageflip", False))

    def test_cut_reveal_handoff_are_not_their_own_kind(self):
        """引擎里 cut / reveal / handoff **没有**分支，它们和 auto 一样落到皮肤。别在这里"修好"它。"""
        for kind in ("cut", "reveal", "handoff"):
            self.assertEqual(self._kinds(kind, craft="pageturn"), ("pageturn", True), kind)
            self.assertEqual(self._kinds(kind, craft="slide"), ("slide", False), kind)

    def test_whip_alternates_by_shot_index(self):
        # 引擎按 idx % 2 交替：第二镜（index 1）是 whip-left。别"顺手"改成先右再左。
        self.assertEqual(self._kinds("whip"), ("whip-left", False))
        with tempfile.TemporaryDirectory() as td:
            shots = [{"id": f"S{i}", "from": i * 100, "to": (i + 1) * 100, "transition": "whip"} for i in range(4)]
            kinds = [b["kind"] for b in plan(mkproj(Path(td) / "proj", shots))["boundaries"]]
            self.assertEqual(kinds, [None, "whip-left", "whip-right", "whip-left"])

    def test_craft_transition_is_read_from_the_craft_block_only(self):
        """主题文件里别处也可能有 transition（相机 / 影片参数），不能抓到那一个。"""
        with tempfile.TemporaryDirectory() as td:
            p = mkproj(Path(td) / "proj", SHOTS, craft=None)
            write(p / "src" / "theme" / "journal.tsx",
                  "const CINEMA = {transition: 'zoom'};\nexport const THEME = {\n"
                  "  craft: {medium: 'journal', transition: 'peel'},\n};\n")
            got = plan(p)
            self.assertEqual(got["craftTransition"], "peel")
            # SHOTS 的 S4 写的是 auto —— 它才是"由皮肤决定"的那一镜
            self.assertEqual(got["boundaries"][3]["kind"], "peel")

    def test_unreadable_skin_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            p = mkproj(Path(td) / "proj", SHOTS, craft=None)
            (p / "src" / "theme" / "journal.tsx").unlink()
            got = plan(p)
            self.assertIsNone(got["craftTransition"])
            self.assertTrue(any("craft.transition" in x for x in got["problems"]), got["problems"])


class WindowGeometryTest(unittest.TestCase):
    def test_window_is_clipped_to_the_film(self):
        with tempfile.TemporaryDirectory() as td:
            shots = [{"id": "S1", "from": 0, "to": 390, "transition": "auto"},
                     {"id": "S2", "from": 390, "to": 400, "transition": "pageturn"}]
            self.assertEqual(plan(mkproj(Path(td) / "proj", shots))["windows"], [[390, 399]])

    def test_adjacent_windows_merge(self):
        with tempfile.TemporaryDirectory() as td:
            shots = [{"id": "S1", "from": 0, "to": 100, "transition": "auto"},
                     {"id": "S2", "from": 100, "to": 110, "transition": "pageturn"},
                     {"id": "S3", "from": 110, "to": 200, "transition": "peel"}]
            self.assertEqual(plan(mkproj(Path(td) / "proj", shots))["windows"], [[100, 131]])

    def test_separated_windows_stay_separate(self):
        with tempfile.TemporaryDirectory() as td:
            shots = [{"id": "S1", "from": 0, "to": 100, "transition": "auto"},
                     {"id": "S2", "from": 100, "to": 200, "transition": "pageturn"},
                     {"id": "S3", "from": 200, "to": 300, "transition": "hard"},
                     {"id": "S4", "from": 300, "to": 400, "transition": "pageturn"}]
            self.assertEqual(plan(mkproj(Path(td) / "proj", shots))["windows"], [[100, 121], [300, 321]])

    def test_out_of_order_manifest_is_sorted_and_reported(self):
        with tempfile.TemporaryDirectory() as td:
            shots = [{"id": "S2", "from": 100, "to": 200, "transition": "pageturn"},
                     {"id": "S1", "from": 0, "to": 100, "transition": "auto"}]
            got = plan(mkproj(Path(td) / "proj", shots))
            self.assertEqual([b["id"] for b in got["boundaries"]], ["S1", "S2"])
            self.assertTrue(any("排序" in p for p in got["problems"]), got["problems"])

    def test_duplicate_shot_id_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            shots = [{"id": "S1", "from": 0, "to": 100, "transition": "auto"},
                     {"id": "S1", "from": 100, "to": 200, "transition": "pageturn"}]
            got = plan(mkproj(Path(td) / "proj", shots))
            self.assertTrue(any("重复" in p for p in got["problems"]), got["problems"])


class SingleSourceTest(unittest.TestCase):
    """判据只能有一份：这里查的是"两处是否还在说同一件事"，而不是文本长什么样。"""

    def test_curl_frames_match_the_composition(self):
        # P2-23：渲染侧的真源在 transitions/meta.ts（fx.tsx 只 re-export，不再有第二份字面量）
        a = re.search(r"export const CURL_FRAMES\s*=\s*(\d+)",
                      (ROOT / "assets/lecture-template/src/transitions/meta.ts").read_text(encoding="utf-8")).group(1)
        b = re.search(r"export const CURL_FRAMES\s*=\s*(\d+)",
                      CLI.read_text(encoding="utf-8")).group(1)
        self.assertEqual(a, b)
        # fx.tsx 与 fx-browser.mjs 都只转出，不各存一份
        fx = (ROOT / "assets/lecture-template/src/fx.tsx").read_text(encoding="utf-8")
        self.assertNotIn("export const CURL_FRAMES = ", fx)
        self.assertIn("export {CURL_FRAMES", fx)
        fb = (ROOT / "scripts/fx-browser.mjs").read_text(encoding="utf-8")
        self.assertNotIn("export const CURL_FRAMES", fb)
        self.assertIn("from './transition-plan.mjs'", fb)

    def test_plain_kinds_match_the_engine(self):
        cin = (ROOT / "assets/lecture-template/src/cinema.tsx").read_text(encoding="utf-8")
        engine = set(re.findall(r"d === '([\w-]+)'", cin.split("const craft = THEME.craft?.transition;")[0]))
        engine -= {"pageturn", "peel", "whip"}  # 这三个另有分支（卷页 / 交替）
        plan_src = CLI.read_text(encoding="utf-8")
        ours = set(re.findall(r"'([\w-]+)'", re.search(r"const EXPLICIT_PLAIN = new Set\(\[([^\]]*)\]\)", plan_src).group(1)))
        self.assertEqual(engine - ours, set(), f"引擎有、计划没有：{engine - ours}")
        self.assertEqual(ours - engine, set(), f"计划有、引擎没有：{ours - engine}")

    def test_engine_still_falls_back_to_pageflip(self):
        """计划里 auto 的兜底是 pageflip；引擎尾段必须一致，否则「没卷页」的片子会两种翻法并存。"""
        cin = (ROOT / "assets/lecture-template/src/cinema.tsx").read_text(encoding="utf-8")
        tail = cin.split("if (craft === 'slide' || craft === 'drop')")[1].split("};")[0]
        self.assertIn("return 'pageflip';", tail)
        self.assertIn("return 'pageflip';", CLI.read_text(encoding="utf-8"))

    def test_render_reads_the_duration_from_the_manifest(self):
        src = (ROOT / "scripts/notebook-video.mjs").read_text(encoding="utf-8")
        body = src[src.index("const readFilmDuration"):]
        body = body[:body.index("\n};")]
        self.assertIn("readShotPlan", body)
        self.assertNotIn("SHOT_TOTAL", body, "总帧数不该再从 shots.ts 正则里抠")

    def test_cli_requires_a_project(self):
        if not NODE:
            self.skipTest("node 不可用")
        r = subprocess.run([NODE, str(CLI)], capture_output=True, text=True, timeout=30,
                           env={**os.environ})
        self.assertEqual(r.returncode, 2)
        self.assertIn("Usage", r.stderr)


if __name__ == "__main__":
    unittest.main()
