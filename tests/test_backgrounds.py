#!/usr/bin/env python3
"""Tests for the 3.3.0 background library: scripts/validate-backgrounds.py and the rotation in scripts/resolve-shots.py."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "assets" / "lecture-template"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


vb = load("vb", "scripts/validate-backgrounds.py")
rs = load("rs", "scripts/resolve-shots.py")
LIB = json.loads((TPL / "manifests" / "backgrounds.json").read_text(encoding="utf-8"))
bm = load("bm", "scripts/dev/bg_metrics.py")   # dev-only helper; imports numpy + pillow lazily inside measure()
HAVE_PIL = all(importlib.util.find_spec(m) is not None for m in ("numpy", "PIL"))


def project(theme: str = "journal", library: bool = True, mutate=None) -> Path:
    d = Path(tempfile.mkdtemp(prefix="nv-bgt-"))
    (d / "manifests").mkdir()
    (d / "src").mkdir()
    shutil.copy(TPL / "manifests" / "caption-cues.json", d / "manifests" / "caption-cues.json")
    doc = json.loads((TPL / "manifests" / "shots.json").read_text(encoding="utf-8"))
    doc["theme"] = theme
    if mutate:
        mutate(doc)
    (d / "manifests" / "shots.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    if library:
        shutil.copy(TPL / "manifests" / "backgrounds.json", d / "manifests" / "backgrounds.json")
    return d


class LibraryTest(unittest.TestCase):
    def test_template_library_passes(self):
        p0, _ = vb.check_library(TPL, min_per_skin={"journal": 8, "papercut": 8, "archive": 8, "flat": 4, "cel": 4})
        self.assertEqual(p0, [])

    def test_every_entry_has_source_and_licence(self):
        for e in LIB["backgrounds"]:
            self.assertIn(e["license"], vb.LICENSES, e["id"])
            self.assertIn(e["source"]["kind"], vb.SOURCE_KINDS, e["id"])
            self.assertTrue(e["attribution"], e["id"])
            if e["source"]["kind"] == "commons":
                self.assertTrue(e["source"]["url"].startswith("https://commons.wikimedia.org/"), e["id"])

    def test_counts_per_skin(self):
        n = {}
        for e in LIB["backgrounds"]:
            if not e.get("legacy"):
                n[e["skin"]] = n.get(e["skin"], 0) + 1
        for skin in ("journal", "papercut", "archive"):
            self.assertGreaterEqual(n.get(skin, 0), 8, skin)
        for skin in ("flat", "cel"):
            self.assertGreaterEqual(n.get(skin, 0), 4, skin)

    def test_ink_matches_theme_palette(self):
        import re
        for skin, ink in vb.INK.items():
            tsx = (TPL / "src" / "theme" / f"{skin}.tsx").read_text(encoding="utf-8")
            m = re.search(r"\bink:\s*'(#[0-9a-fA-F]{6})'", tsx)
            self.assertIsNotNone(m, skin)
            self.assertEqual(m.group(1).lower(), ink.lower(), skin)

    def test_contrast_math(self):
        self.assertAlmostEqual(vb.contrast(1.0, 0.0), 21.0, places=3)
        self.assertAlmostEqual(vb.hex_lum("#ffffff"), 1.0, places=4)
        p0, _ = vb.judge_metrics("journal", {"size": [2560, 1440], "mean_lum": 0.8, "zone_mean_lum": 0.8, "zone_p05_lum": 0.75, "centre_std": 0.01})
        self.assertEqual(p0, [])
        p0, _ = vb.judge_metrics("journal", {"size": [2560, 1440], "mean_lum": 0.8, "zone_mean_lum": 0.8, "zone_p05_lum": 0.08, "centre_std": 0.01})
        self.assertTrue(any("字幕区有深色装饰" in x for x in p0))

    @unittest.skipUnless(HAVE_PIL, "needs numpy + pillow (dev-only)")
    def test_recorded_metrics_match_pixels(self):
        self.assertEqual(bm.recheck(TPL), [])


class RotationTest(unittest.TestCase):
    def resolve(self, d: Path):
        text, out, problems = rs.resolve(d)
        return text, out, problems

    def test_auto_rotation_never_repeats_adjacent_and_is_deterministic(self):
        # 3.3.0: per-shot rotation is bgMode=shot (default only for flat / cel; handcraft skins opt in)
        for theme in ("flat", "cel", "journal", "papercut", "archive"):
            d = project(theme, mutate=lambda doc: doc.update(bgMode="shot"))
            try:
                _, a, p = self.resolve(d)
                _, b, _ = self.resolve(d)
                self.assertEqual(p, [])
                files = [r["bgFile"] for r in a]
                self.assertTrue(all(files), theme)
                self.assertTrue(all(x != y for x, y in zip(files, files[1:])), (theme, files))
                self.assertEqual(files, [r["bgFile"] for r in b])
                self.assertTrue(all(r["bg"].startswith(theme + "/") for r in a))
                # 轮换必须真的换：8 镜里至少出现 4 张不同的纸。
                # 原来钉的是 5。3.4.0 加入 use.layouts 后，每族「能承载这一镜版式」的纸变少
                # （papercut 只有 4 张放得下图版），硬要 5 只会逼人把「窗花角」塞给图版页——
                # 拿门禁逼出坏画面。真正吃重的是上面两条：相邻不重复、同种子同结果。
                self.assertGreaterEqual(len(set(files)), min(len(files), 4), (theme, files))
            finally:
                shutil.rmtree(d)

    def test_seed_changes_order(self):
        d1, d2 = project("journal", mutate=lambda doc: doc.update(bgMode="shot")), project("journal", mutate=lambda doc: doc.update(bgMode="shot", bgSeed=7))
        try:
            f1 = [r["bgFile"] for r in self.resolve(d1)[1]]
            f2 = [r["bgFile"] for r in self.resolve(d2)[1]]
            self.assertNotEqual(f1, f2)
        finally:
            shutil.rmtree(d1)
            shutil.rmtree(d2)

    def test_explicit_short_and_full_ids_and_legacy_names(self):
        def m(doc):
            doc["shots"][0]["bg"] = "ruled"
            doc["shots"][1]["bg"] = "journal/kraft"
            doc["shots"][2]["bg"] = "quiet"
        d = project("journal", mutate=m)
        try:
            _, out, p = self.resolve(d)
            self.assertEqual(p, [])
            self.assertEqual(out[0]["bgFile"], "bg/lib/journal-ruled.webp")
            self.assertEqual(out[1]["bg"], "journal/kraft")
            self.assertEqual(out[2]["bgFile"], "bg/bg-journal-quiet.jpg")
            self.assertNotIn("bgAuto", out[0])
        finally:
            shutil.rmtree(d)

    def test_role_pools(self):
        """3.4.0 的新契约：**能不能承载这种版式**优先于「角色池」。

        早先这里断言「bg 的 roles 含这一镜算出来的 role」。加入 use.layouts 之后，
        role 只在版式定了之后才细分（手账页永远按 main/quiet 挑干净纸，不会因为
        「它刚好开了一章」被派去做章节卡），所以旧断言会误报。
        真正要守的不变量是：**这一镜拿到的纸，必须认这一镜的版式**。
        """
        for theme in ("papercut", "journal", "archive", "flat", "cel"):
            d = project(theme, mutate=lambda doc: doc.update(bgMode="shot"))
            try:
                _, out, p = self.resolve(d)
                self.assertEqual(p, [], theme)
                lib = {e["id"]: e for e in LIB["backgrounds"]}
                for r in out:
                    e = lib[r["bg"]]
                    self.assertEqual(e.get("skin"), theme, r["id"])
                    ls = (e.get("use") or {}).get("layouts")
                    if ls:
                        lay = str(r.get("layout") or "")
                        cls = "page" if lay.startswith("page") else (
                            "chapter" if lay.startswith(("statement", "define", "quiz")) else "component")
                        self.assertIn(cls, ls, (theme, r["id"], r["bg"], cls, ls))
            finally:
                shutil.rmtree(d)

    def test_bg_rotate_false_and_no_library_keep_330_behaviour(self):
        for kw in ({"library": False}, {"mutate": lambda doc: doc.update(bgRotate=False)}):
            d = project("journal", **kw)
            try:
                text, out, p = self.resolve(d)
                self.assertEqual(p, [])
                self.assertNotIn("bgFile", text)
                self.assertTrue(all("bg" not in r for r in out))
            finally:
                shutil.rmtree(d)

    def test_unknown_or_foreign_bg_is_a_problem(self):
        for bg, needle in (("nope", "不在背景库"), ("archive/map", "属于 archive 皮肤")):
            d = project("journal", mutate=lambda doc, bg=bg: doc["shots"][0].update(bg=bg))
            try:
                _, _, p = self.resolve(d)
                self.assertTrue(any(needle in x for x in p), p)
            finally:
                shutil.rmtree(d)
        d = project("journal", library=False, mutate=lambda doc: doc["shots"][0].update(bg="ruled"))
        try:
            self.assertTrue(any("没有背景库" in x for x in self.resolve(d)[2]))
        finally:
            shutil.rmtree(d)

    def test_shots_gate_flags_adjacent_duplicate(self):
        d = project("flat", mutate=lambda doc: (doc["shots"][3].update(bg="dotgrid"), doc["shots"][4].update(bg="dotgrid")))
        try:
            text, out, _ = self.resolve(d)
            (d / "manifests" / "shots.resolved.json").write_text(json.dumps({"theme": "flat", "shots": out}), encoding="utf-8")
            p0, p1 = vb.check_shots(d)
            self.assertEqual(p0, [])
            self.assertTrue(any("相邻镜重复" in x for x in p1))
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
