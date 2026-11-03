#!/usr/bin/env python3
"""P1-33：墨图页的动作（`content.ink.acts`）——不用卡片组件也能演示「指一处 → 变 → 圈结论」。

之前 `content.ink` 只传 draw / label / parts / at / delay，`auto.tsx` 的 `case 'figure'` 永远只发
一个 `enter`。底层 `SketchLayer` 早就支持 point / drop / swap / mark / exit，缺的是**内容契约**：
作者写不出「讲到这一句时，纸上发生了什么」。

这一版把 ink 接进同一套动作系统（不新造第二套动词、不要求作者手算帧）：
  · `at` 写法与 `shot.sketch` 完全相同（数字帧 / `@L1` / `@L1.3`）；
  · 帧号由 compose 按本镜 `lines` 换算，渲染层只吃结果；
  · 不写 acts 时元素里**没有** frames 键，引擎退回「只入场」——旧 story 的画面一个像素都不变。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURE = ROOT / "examples" / "recipes" / "jie-freeform.story.json"
SKETCH_TS = ROOT / "assets" / "lecture-template" / "src" / "auto.tsx"


def load_story() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def ink_shot(story: dict) -> dict:
    for shot in story["chapters"][0]["shots"]:
        if isinstance(shot.get("content"), dict) and "ink" in shot["content"]:
            return shot
    raise AssertionError("夹具里没有 content.ink 的镜头")


def build(story: dict) -> tuple[dict, str]:
    """跑一遍 compose，返回 (STORY 表, 终端输出)。"""
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "story.json"
        src.write_text(json.dumps(story, ensure_ascii=False, indent=1), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPTS / "compose-story.py"), str(src), td,
                            "--report", str(Path(td) / "report.json")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
        out = (r.stdout or "") + (r.stderr or "")
        table, shots = {}, []
        ts = Path(td) / "src" / "story.ts"
        if ts.is_file():
            text = ts.read_text(encoding="utf-8")
            start = text.index("{", text.index("export const STORY"))
            table = json.loads(text[start:text.rindex("}") + 1])
        sj = Path(td) / "manifests" / "shots.json"
        if sj.is_file():
            shots = json.loads(sj.read_text(encoding="utf-8"))["shots"]
        return {"rc": r.returncode, "table": table, "shots": shots, "out": out}, out


def figure(table: dict, sid: str) -> dict | None:
    for e in table.get(sid, {}).get("elements", []):
        if e.get("kind") == "figure":
            return e
    return None


class InkActsBuildTest(unittest.TestCase):
    def test_acts_become_local_frame_numbers(self):
        story = load_story()
        shot = ink_shot(story)
        shot["content"]["ink"]["acts"] = [
            {"do": "point", "target": "line", "at": "@L2", "text": "等距的结"},
            {"do": "mark", "target": "line", "mark": "circle", "at": "@L2.3"},
        ]
        res, out = build(story)
        self.assertEqual(res["rc"], 0, out[-1200:])
        sid = "S1"
        el = figure(res["table"], sid)
        self.assertIsNotNone(el, "墨图元素没生成")
        self.assertIn("frames", el)
        self.assertEqual([f["do"] for f in el["frames"]], ["point", "mark"])
        lines = res["table"][sid]["lines"]
        # @L2 = 本镜第 2 句开始。验收要求误差 ≤2 帧，这里直接要求落在同一帧。
        self.assertEqual(el["frames"][0]["at"], lines[1], el["frames"])
        # @L2.3 = 第 2 句第 3 个字音 → 略晚于第 2 句起点（约 2 个字 × 222 ms ≈ 15 帧）
        self.assertGreater(el["frames"][1]["at"], lines[1])
        self.assertLess(el["frames"][1]["at"], lines[1] + 45)
        self.assertIn("text", el["frames"][0])
        self.assertEqual(el["frames"][1]["mark"], "circle")
        self.assertNotIn("inkActs", el)

    def test_numeric_frames_pass_through(self):
        story = load_story()
        ink_shot(story)["content"]["ink"]["acts"] = [{"do": "point", "target": "hull", "at": 70}]
        res, out = build(story)
        self.assertEqual(res["rc"], 0, out[-1200:])
        self.assertEqual(figure(res["table"], "S1")["frames"][0]["at"], 70)

    def test_acts_are_sorted_and_clamped_to_the_shot(self):
        story = load_story()
        ink_shot(story)["content"]["ink"]["acts"] = [
            {"do": "mark", "target": "line", "mark": "check", "at": 99999},
            {"do": "point", "target": "hull", "at": 12},
        ]
        res, out = build(story)
        self.assertEqual(res["rc"], 0, out[-1200:])
        sid = "S1"
        frames = figure(res["table"], sid)["frames"]
        self.assertEqual([f["do"] for f in frames], ["point", "mark"], "动作要按帧排序")
        shot = next(x for x in res["shots"] if x["id"] == sid)
        self.assertLessEqual(frames[-1]["at"], shot["to"] - shot["from"] - 1)

    def test_without_acts_the_element_keeps_its_old_shape(self):
        """验收③：旧 story 不写 acts 时画面完全不变——连一个多余字段都不能多。"""
        plain, _ = build(load_story())
        self.assertEqual(plain["rc"], 0)
        el = figure(plain["table"], "S1")
        self.assertNotIn("frames", el)
        self.assertNotIn("inkActs", el)
        # 引擎在 frames 缺失时才补 enter
        self.assertIn("frames: e.frames ?? [{at: e.figAt ?? 0, do: 'enter' as const}]",
                      SKETCH_TS.read_text(encoding="utf-8"))


class InkActsRejectTest(unittest.TestCase):
    def _fail(self, acts) -> str:
        story = load_story()
        ink_shot(story)["content"]["ink"]["acts"] = acts
        res, out = build(story)
        self.assertEqual(res["rc"], 1, out[-1200:])
        return out

    def test_unknown_verb(self):
        out = self._fail([{"do": "wiggle", "target": "hull", "at": "@L2"}])
        self.assertIn("wiggle", out)
        self.assertIn("point / drop / swap / mark / exit", out)

    def test_enter_and_count_are_not_open_on_a_page(self):
        out = self._fail([{"do": "count", "target": "hull", "n": 3, "at": "@L2"}])
        self.assertIn("count", out)
        self.assertIn("content.ink.at", out)

    def test_target_must_exist_in_the_library(self):
        out = self._fail([{"do": "point", "target": "planks", "at": "@L2"}])
        self.assertIn("planks", out)
        self.assertIn("hull / line / plank", out, "报错要给出可用部位")

    def test_target_must_be_visible_on_this_page(self):
        # 这一页只画 hull+line，却要 point plank：动作指向看不见的部位
        out = self._fail([{"do": "point", "target": "plank", "at": "@L2"}])
        self.assertIn("content.ink.parts", out)

    def test_point_without_target(self):
        out = self._fail([{"do": "point", "at": "@L2"}])
        self.assertIn("没写 target", out)

    def test_too_many_acts_is_only_a_hint(self):
        story = load_story()
        ink_shot(story)["content"]["ink"]["acts"] = [
            {"do": "point", "target": "hull", "at": 20},
            {"do": "swap", "target": "line", "at": 40},
            {"do": "mark", "target": "line", "mark": "check", "at": 60},
            {"do": "exit", "at": 80},
        ]
        res, out = build(story)
        self.assertEqual(res["rc"], 0, out[-1200:])
        self.assertIn("1–3 个", out)


if __name__ == "__main__":
    unittest.main()
