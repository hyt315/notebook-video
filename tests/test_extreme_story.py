#!/usr/bin/env python3
"""P2-25 · 极端与长片夹具。

清单里列的未覆盖场景：60 秒以上、多章节、大量卷页窗口、长标题、空字幕、无音频、
5 项清单、复杂中英数字、重复运行与同工程并发。

这里不渲整片（那是 visual-matrix 的活），只跑**排版与规划**——因为「时长会不会算错、
章节索引会不会串、元素会不会排出画布」这些问题在 compose 阶段就已经决定了，
等渲完才发现要贵两个数量级。
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
COMPOSE = SCRIPTS / "compose-story.py"
CANVAS_W, CANVAS_H = 1920, 1080


def shot(layout: str, content: dict, lines: list[str] | None = None, role: str = "point") -> dict:
    """默认给一句台词：compose 的产品规则是「每镜至少一句」，空台词不是缺陷而是作者错误。"""
    return {"role": role, "layout": layout,
            "lines": lines if lines is not None else ["这一镜至少要说一句话。"],
            "content": content}


def story(chapters: list[dict], **extra) -> dict:
    doc = {"title": "压力测试", "theme": "flat", "kicker": "STRESS", "header": "压力测试",
           "chapters": chapters}
    doc.update(extra)
    return doc


def run_compose(doc: dict, cwd: Path, *args: str) -> tuple[int, str, Path]:
    """跑一遍 compose，返回 (rc, 合并输出, 工程目录)。工程目录里可读产物。"""
    story_p = cwd / "story.json"
    proj = cwd / "proj"
    story_p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    proj.mkdir(exist_ok=True)
    r = subprocess.run([sys.executable, str(COMPOSE), str(story_p), str(proj), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or ""), proj


def read_shots(proj: Path) -> dict:
    return json.loads((proj / "manifests" / "shots.json").read_text(encoding="utf-8"))


def read_cues(proj: Path) -> dict:
    return json.loads((proj / "manifests" / "caption-cues.json").read_text(encoding="utf-8"))


def read_elements(proj: Path) -> dict[str, list]:
    """每个镜头的元素矩形。它们在 src/story.ts（给引擎的视图），不在 manifests/shots.json（给门禁的视图）。"""
    txt = (proj / "src" / "story.ts").read_text(encoding="utf-8")
    body = txt.split("export const STORY: Record<string, StoryShot> = ", 1)[1].rsplit(";", 1)[0]
    doc = json.loads(body)
    return {sid: v.get("elements") or [] for sid, v in doc.items()}


class LongFilmTest(unittest.TestCase):
    """8 章 × 4 镜：时长、帧数、章节索引三者必须自洽。"""

    @classmethod
    def setUpClass(cls):
        cls._td = tempfile.TemporaryDirectory()
        cwd = Path(cls._td.name)
        chapters = []
        for c in range(8):
            shots = [shot("statement", {"text": f"第{c + 1}章第{s + 1}镜的说明文字在这儿"},
                          [f"第{c + 1}章第{s + 1}镜，念这一句大约十四字。"]) for s in range(4)]
            chapters.append({"title": f"第{c + 1}章", "shots": shots})
        cls.rc, cls.out, cls.proj = run_compose(story(chapters), cwd)
        cls.shots = read_shots(cls.proj) if cls.rc == 0 else {}
        cls.cues = read_cues(cls.proj) if cls.rc == 0 else {}

    @classmethod
    def tearDownClass(cls):
        cls._td.cleanup()

    def test_compose_succeeds(self):
        self.assertEqual(self.rc, 0, f"长片排版失败：\n{self.out[-1500:]}")

    def test_film_is_over_a_minute(self):
        total = self.shots["duration"]
        self.assertGreater(total / 30, 60, f"32 镜仍不到 60 秒（{total} 帧），夹具没造够长")

    def test_duration_matches_last_cue_plus_tail(self):
        # 帧数不是随便给的：最后一镜的结束必须落在 total 之内，且片尾留白不超过 3 秒
        last_end = max(c["speech_end_ms"] for c in self.cues["cues"])
        total_ms = self.shots["duration"] / 30 * 1000
        self.assertLessEqual(last_end, total_ms + 1, "字幕比成片还长")
        self.assertLess(total_ms - last_end, 3200, f"片尾空转 {round(total_ms - last_end)}ms，超过 3 秒")

    def test_every_shot_is_present_and_ordered(self):
        ids = [s["id"] for s in self.shots["shots"]]
        self.assertEqual(len(ids), 32)
        self.assertEqual(ids, sorted(ids, key=lambda x: int(x[1:])), "镜号不是递增的")

    def test_chapter_first_indexes(self):
        # CHAPTER_SHOTS 存的是**镜号**（S1 / S5 / …），不是数组下标；
        # 名字叫 FIRST 容易误会，这里按真实语义断言：每章第一镜，每章 4 镜。
        cf = json.loads((self.proj / "src" / "film.ts").read_text(encoding="utf-8")
                        .split("CHAPTER_SHOTS = ")[1].split(" as const")[0])
        self.assertEqual(len(cf), 8, f"章节索引应有 8 个，实际 {cf}")
        self.assertEqual(cf[0], "S1", "第一章必须从 S1 开始")
        nums = [int(x[1:]) for x in cf]
        self.assertEqual(nums, sorted(nums), "章节起点必须单调递增")
        self.assertEqual(nums, [1, 5, 9, 13, 17, 21, 25, 29], f"每章 4 镜，起点应为 1/5/9…，实际 {cf}")

    def test_no_element_outside_canvas(self):
        for sid, els in read_elements(self.proj).items():
            for e in els:
                self.assertGreaterEqual(e["x"], -1, f"{sid}/{e['id']} x 为负")
                self.assertGreaterEqual(e["y"], -1, f"{sid}/{e['id']} y 为负")
                self.assertLessEqual(e["x"] + e["w"], CANVAS_W + 1,
                                     f"{sid}/{e['id']} 右边出画：{e['x']}+{e['w']}")
                self.assertLessEqual(e["y"] + e["h"], CANVAS_H + 1,
                                     f"{sid}/{e['id']} 下边出画：{e['y']}+{e['h']}")


class DegenerateInputTest(unittest.TestCase):
    """空字幕、无 content、单镜。这些是弱模型最常写出来的东西，不能崩。"""

    def test_empty_lines_are_refused_with_a_reason(self):
        # 产品规则：每镜至少一句台词。所以这里要的是「明确拒绝」，不是「静默出空片」。
        doc = story([{"title": "空", "shots": [
            shot("statement", {"text": "只有主标题，没有台词"}, []),
            shot("statement", {"text": "第二镜"}, ["", "  "]),
        ]}])
        with tempfile.TemporaryDirectory() as td:
            rc, out, proj = run_compose(doc, Path(td))
            self.assertNotIn("Traceback", out, "空台词抛了未捕获异常")
            self.assertEqual(rc, 1, "空台词应当被拒（rc=1），不能静默出片")
            self.assertIn("台词", out, f"拒绝理由没说清是台词问题：\n{out[-600:]}")
            self.assertFalse((proj / "manifests" / "caption-cues.json").exists(),
                             "拒绝了却仍写出了字幕文件")

    def test_single_shot_film(self):
        doc = story([{"title": "一镜", "shots": [shot("statement", {"text": "只有一镜"})]}])
        with tempfile.TemporaryDirectory() as td:
            rc, out, proj = run_compose(doc, Path(td))
            self.assertEqual(rc, 0, out[-1200:])
            shots = read_shots(proj)
            self.assertEqual(len(shots["shots"]), 1)
            self.assertGreater(shots["duration"], 0)

    def test_missing_content_is_reported_not_crashed(self):
        # content 整个缺失：应当是「可读的错误」，不是 KeyError 栈
        doc = story([{"title": "缺", "shots": [{"role": "point", "layout": "statement", "lines": ["有台词"]}]}])
        with tempfile.TemporaryDirectory() as td:
            rc, out, proj = run_compose(doc, Path(td))
            self.assertNotIn("Traceback", out, "缺 content 时抛了未捕获异常")
            self.assertIn(rc, (0, 1))


class LongTitleTest(unittest.TestCase):
    def test_very_long_title_either_fits_or_refuses(self):
        title = "这是一个非常长的标题" * 8   # 80 字
        doc = story([{"title": "长标题", "shots": [shot("statement", {"text": title},
                                                       ["这一镜讲一个非常长的标题。"])]}])
        with tempfile.TemporaryDirectory() as td:
            rc, out, proj = run_compose(doc, Path(td))
            if rc != 0:
                # 拒绝时要能指导改法：说清删到多少字 / 降到多小
                self.assertTrue(any(k in out for k in ("字", "删", "拆")),
                                f"长标题报错没说怎么改：\n{out[-800:]}")
                return
            for e in read_elements(proj)["S1"]:
                self.assertLessEqual(e["x"] + e["w"], CANVAS_W + 1, f"{e['id']} 出画")
                self.assertLessEqual(e["y"] + e["h"], CANVAS_H + 1, f"{e['id']} 出画")


class ListLayoutTest(unittest.TestCase):
    def test_five_items_stay_inside_canvas(self):
        doc = story([{"title": "五项", "shots": [
            shot("list", {"title": "五项清单", "style": "check",
                          "items": ["第一项说明文字", "第二项说明文字", "第三项说明文字",
                                    "第四项说明文字", "第五项说明文字"]})]}])
        with tempfile.TemporaryDirectory() as td:
            rc, out, proj = run_compose(doc, Path(td))
            self.assertEqual(rc, 0, out[-1200:])
            for e in read_elements(proj)["S1"]:
                self.assertLessEqual(e["y"] + e["h"], CANVAS_H + 1,
                                     f"5 项清单排出画布：{e['id']} y={e['y']} h={e['h']}")


class MixedScriptTest(unittest.TestCase):
    """中英数字混排：不能把英文词、单位、破折号劈开。"""

    def test_wrap_keeps_words_units_and_dashes(self):
        with tempfile.TemporaryDirectory() as td:
            sys.path.insert(0, str(SCRIPTS))
            import story_text
            cases = [
                ("把 3.5 GB 的数据搬到 —— 另一块盘上", ["3.5", "GB"]),
                ("打开 http-server 这个命令行工具", ["http-server"]),
                ("延迟从 12 ms 降到 0.8 ms", ["12", "ms", "0.8"]),
            ]
            for text, must_keep in cases:
                lines = story_text.wrap(text, 36, 400)
                joined = "|".join(lines)
                for token in must_keep:
                    self.assertIn(token, joined, f"「{token}」被劈开了：{lines}")
                self.assertNotIn("——|", joined.replace("|—", ""), f"破折号被劈开：{lines}")


class IdempotentTest(unittest.TestCase):
    def test_same_story_twice_gives_identical_artifacts(self):
        doc = story([{"title": "幂等", "shots": [
            shot("statement", {"text": "同一份故事跑两次"}, ["同一份故事，跑两次结果要一样。"]),
            shot("number", {"value": 100, "unit": "万次", "label": "数字镜"}, ["一百万次。"]),
        ]}])
        outs = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as td:
                rc, out, proj = run_compose(doc, Path(td))
                self.assertEqual(rc, 0, out[-1000:])
                outs.append({
                    "shots": (proj / "manifests" / "shots.json").read_text(encoding="utf-8"),
                    "cues": (proj / "manifests" / "caption-cues.json").read_text(encoding="utf-8"),
                    "story": (proj / "src" / "story.ts").read_text(encoding="utf-8"),
                })
        self.assertEqual(outs[0], outs[1], "同一份 story 两次产出不同 —— 有隐藏的随机/时间依赖")


if __name__ == "__main__":
    unittest.main()
