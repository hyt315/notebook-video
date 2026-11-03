"""T-P1-12：配方链路与出现规则的端到端锁。

这些断言全部来自 3.5.1 的 P0 修复（null 键、运镜不动、保护短语为空、recipe 为 null、
photo-traced 未实现、出现扎堆）。它们不跑 tsc、不渲染——那两件在 R2 里做，这里只保证
「样例写得出来、门禁的输入是对的、排程真的生效」。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "scripts" / "compose-story.py"
REVEAL = ROOT / "scripts" / "measure-reveal.py"

RECIPES = ("annotated", "data-with-object", "list-icons", "rocket-fusion")
AUTO = ("code-change-cache", "concept-hash-table", "data-ssd-vs-hdd")


def compose(story: Path, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(COMPOSE), str(story), str(out)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class RecipeEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._td = tempfile.TemporaryDirectory()
        cls.root = Path(cls._td.name)
        cls.projects: dict[str, Path] = {}
        cls.results: dict[str, subprocess.CompletedProcess] = {}
        for name in RECIPES + AUTO:
            story = (ROOT / "examples" / "recipes" / f"{name}.story.json") if name in RECIPES \
                else (ROOT / "examples" / f"{name}.story.json")
            out = cls.root / name
            cls.results[name] = compose(story, out)
            cls.projects[name] = out

    @classmethod
    def tearDownClass(cls):
        cls._td.cleanup()

    def test_recipes_compose(self):
        for name in RECIPES:
            self.assertEqual(self.results[name].returncode, 0,
                             f"{name} compose 失败：\n{self.results[name].stdout[-800:]}")

    def test_no_null_frames(self):
        # 3.5.0 的招牌缺陷：story.ts 里写 null，tsc 报 23 条 TS2322
        for name in RECIPES:
            text = (self.projects[name] / "src" / "story.ts").read_text(encoding="utf-8")
            self.assertNotIn('": null', text, f"{name} 的 story.ts 又出现 null 字段")

    def test_fusion_recipe_not_null(self):
        for name in RECIPES:
            data = json.loads((self.projects[name] / "manifests" / "fusion.json").read_text(encoding="utf-8"))
            recipes = [v["recipe"] for v in data["shots"].values()]
            self.assertTrue(all(r for r in recipes), f"{name} 的 recipe 还是 null：{recipes}")

    def test_protect_auto(self):
        phrases = (self.projects["rocket-fusion"] / "manifests" / "protected-caption-phrases.txt") \
            .read_text(encoding="utf-8")
        for word in ("火箭", "第一级"):
            self.assertIn(word, phrases, f"保护短语里缺「{word}」")

    def test_protect_empty_hint(self):
        story = json.loads((ROOT / "examples" / "recipes" / "annotated.story.json").read_text(encoding="utf-8"))
        story.pop("protect", None)
        # 去掉台词里的 {{术语}} 标记，才真的没有任何可自动收的短语
        for ch in story.get("chapters") or []:
            for sh in ch.get("shots") or []:
                for line in sh.get("lines") or []:
                    sh["lines"][sh["lines"].index(line)] = line.replace("{{", "").replace("}}", "")
        tmp = self.root / "no-protect"
        tmp.mkdir(exist_ok=True)
        p = tmp / "story.json"
        p.write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")
        r = compose(p, tmp / "out")
        self.assertEqual(r.returncode, 0, r.stdout[-800:])
        self.assertIn("字幕保护短语为空", r.stdout,
                      "保护短语为空时必须提示（3.6 起样例可以不带 protect，不能报错退出）")

    def test_photo_traced_removed(self):
        story = json.loads((ROOT / "examples" / "recipes" / "rocket-fusion.story.json").read_text(encoding="utf-8"))
        story["chapters"][0]["shots"][0]["recipe"] = "photo-traced"
        tmp = self.root / "photo-traced"
        tmp.mkdir(exist_ok=True)
        p = tmp / "story.json"
        p.write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")
        r = compose(p, tmp / "out")
        self.assertNotEqual(r.returncode, 0, "photo-traced 已移除，却还当有效配方处理")
        self.assertIn("3.5.1 已移除", r.stdout)

    def test_reveal_schedule(self):
        # 讲到哪长到哪：不许同帧扎堆、不许间隔过密、不许同时在长超过 2 样
        for name in RECIPES + AUTO:
            r = subprocess.run([sys.executable, str(REVEAL), str(self.projects[name]), "--json"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(r.returncode, 0, r.stderr[-400:])
            payload = json.loads([l for l in r.stdout.splitlines() if l.startswith("{")][-1])
            for row in payload["static"]:
                sid = row["shot"]
                self.assertEqual(row["same"], 1, f"{name} {sid}：{row['same']} 样东西同帧开始")
                self.assertGreaterEqual(row["gap"], 12, f"{name} {sid}：相邻开始只隔 {row['gap']} 帧")
                self.assertLessEqual(row["conc"], 2, f"{name} {sid}：{row['conc']} 样同时在长")

    def test_sketch_camera_moves(self):
        # shots.json 里不标「这镜有没有线稿」——线稿写在 story.ts 的 sketch 上，按 id 对回去。
        import re as _re
        text = (self.projects["rocket-fusion"] / "src" / "story.ts").read_text(encoding="utf-8")
        m = _re.search(r"=\s*(\{.*\})\s*(?:as const)?;?\s*$", text, _re.S)
        self.assertIsNotNone(m, "story.ts 解析不了")
        story = json.loads(m.group(1))
        sketch_ids = {sid for sid, sh in story.items() if sh.get("sketch")}
        self.assertTrue(sketch_ids, "火箭样例应当有线稿镜头")

        shots = json.loads((self.projects["rocket-fusion"] / "manifests" / "shots.json")
                           .read_text(encoding="utf-8"))["shots"]
        picked = [s for s in shots if s["id"] in sketch_ids]
        self.assertEqual(len(picked), len(sketch_ids), "线稿镜头在镜头表里对不上")
        for s in picked:
            self.assertAlmostEqual(s["camera"]["to"], 1.03, places=3,
                                   msg=f"{s['id']} 的镜头又变回「不动」了")
        intents = {s["camera"]["intent"] for s in picked}
        self.assertGreaterEqual(len(intents), 2, f"线稿镜头只有 {len(intents)} 种意图，运镜被判重复")


if __name__ == "__main__":
    unittest.main()
