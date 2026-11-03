#!/usr/bin/env python3
"""P2-18 · 选材可解释性。

以前只看得见结果（`bg=flat/sunrise`），看不见「为什么不是另一张」——于是"选错纸"永远只能靠眼睛发现，
没法复盘，也没法把「为什么这张好看」沉淀成规则。

这一组锁的是**解释与事实一致**：说了「避开上一镜」，那两张就真的不同；说了「N 张候选」，
那 N 就是按这一镜的角色与版式筛出来的。解释可以少说，不能乱说。

不写盘（`--check`），全部从 `--explain` 的输出来判——这样模板工程不会被测试改动。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets" / "lecture-template"
RESOLVE = ROOT / "scripts" / "resolve-shots.py"


def resolve(*args: str) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(RESOLVE), str(TEMPLATE), "--check", *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def parse(out: str) -> list[dict]:
    """把 --explain 的输出解析成 [{id, bg, why}]。"""
    rows, cur = [], None
    for line in out.splitlines():
        shot = re.match(r"^\s+(S\d+)\s+\d+–\d+", line)
        if shot:
            cur = {"id": shot.group(1), "bg": "", "why": ""}
            rows.append(cur)
            continue
        paper = re.match(r"^\s+纸\s+(\S+)\s+(.*)$", line)
        if paper and cur is not None:
            cur["bg"], cur["why"] = paper.group(1), paper.group(2).strip()
    return rows


class ExplainTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rc, cls.out = resolve("--explain")
        cls.rows = parse(cls.out)

    def test_resolve_passes_with_explanations(self):
        self.assertEqual(self.rc, 0, self.out[-1200:])
        self.assertGreaterEqual(len(self.rows), 4, f"没解析到镜头：\n{self.out[:600]}")

    def test_every_shot_gets_a_reason(self):
        for r in self.rows:
            self.assertTrue(r["why"], f"{r['id']} 没有选纸理由")
            self.assertNotEqual(r["why"], "无背景库 / 未轮换", f"{r['id']} 落在「没有理由」分支")


class ReasonMatchesRealityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rc, cls.out = resolve("--explain")
        cls.rows = parse(cls.out)
        cls.lib = {b["id"]: b for b in
                   json.loads((TEMPLATE / "manifests" / "backgrounds.json").read_text(encoding="utf-8"))["backgrounds"]}

    def test_auto_reason_names_role_layout_and_candidates(self):
        autos = [r for r in self.rows if r["why"].startswith("auto")]
        self.assertTrue(autos, "没有一镜是自动选纸？夹具失效")
        for r in autos:
            self.assertRegex(r["why"], r"role=(chapter|quiet|main)", f"{r['id']} 理由缺角色：{r['why']}")
            self.assertRegex(r["why"], r"layout=(page|chapter|component)", f"{r['id']} 理由缺版式：{r['why']}")
            self.assertRegex(r["why"], r"\d+ 张候选", f"{r['id']} 理由缺候选数：{r['why']}")

    def test_avoiding_previous_shot_is_true(self):
        prev = None
        for r in self.rows:
            if prev and "已避开上一镜" in r["why"]:
                self.assertNotEqual(r["bg"], prev["bg"], f"{r['id']} 说避开了上一镜，实际还是同一张")
            prev = r

    def test_chosen_id_exists_in_library(self):
        for r in self.rows:
            if r["bg"] and "/" in r["bg"]:
                self.assertIn(r["bg"], self.lib, f"{r['id']} 选了库里没有的 {r['bg']}")

    def test_candidate_count_is_plausible(self):
        # 候选数不能是 0（那说明筛空了还硬选），也不能超过本皮肤的背景总数
        skin_total = len([b for b in self.lib.values() if b.get("skin") == "flat"])
        for r in self.rows:
            m = re.search(r"(\d+) 张候选", r["why"])
            if m:
                n = int(m.group(1))
                self.assertGreater(n, 0, f"{r['id']} 候选数为 0")
                self.assertLessEqual(n, skin_total, f"{r['id']} 候选数 {n} 超过本皮肤总数 {skin_total}")

    def test_explicit_choice_says_explicit(self):
        for r in self.rows:
            if r["why"] and not r["why"].startswith(("auto", "chapter 模式", "film 模式")):
                self.assertIn("explicit", r["why"], f"{r['id']} 来源不明：{r['why']}")


if __name__ == "__main__":
    unittest.main()
