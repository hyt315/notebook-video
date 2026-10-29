#!/usr/bin/env python3
"""3.7.0 bgMode: handcraft skins keep one paper per chapter (or per film); flat / cel keep per-shot rotation."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "assets" / "lecture-template"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


rs = load("rs_bgmode", ROOT / "scripts" / "resolve-shots.py")
vb = load("vb_bgmode", ROOT / "scripts" / "validate-backgrounds.py")
LIB = {e["id"]: e for e in json.loads((TPL / "manifests" / "backgrounds.json").read_text(encoding="utf-8"))["backgrounds"]}

# Six shots, three chapters (2 + 3 + 1), so "same within chapter / different across" is observable.
CHAPTERS = ["A", "A", "B", "B", "B", "C"]


def project(theme: str, library: bool = True, mutate=None) -> Path:
    d = Path(tempfile.mkdtemp(prefix="nv-bgmode-"))
    (d / "manifests").mkdir()
    (d / "src").mkdir()
    shutil.copy(TPL / "manifests" / "caption-cues.json", d / "manifests" / "caption-cues.json")
    doc = json.loads((TPL / "manifests" / "shots.json").read_text(encoding="utf-8"))
    doc["theme"] = theme
    for s, ch in zip(doc["shots"], CHAPTERS + ["C"] * 10):
        s["chapter"] = ch
    if mutate:
        mutate(doc)
    (d / "manifests" / "shots.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    if library:
        shutil.copy(TPL / "manifests" / "backgrounds.json", d / "manifests" / "backgrounds.json")
    return d


def bgs(d: Path) -> list[tuple[str, str, str | None]]:
    _, out, problems = rs.resolve(d)
    assert not problems, problems
    return [(r["id"], r["chapter"], r.get("bg")) for r in out]


class BgModeTest(unittest.TestCase):
    def test_journal_defaults_to_chapter(self):
        rows = bgs(project("journal"))
        by_ch: dict[str, set] = {}
        for _, ch, bg in rows:
            by_ch.setdefault(ch, set()).add(bg)
        for ch, s in by_ch.items():
            self.assertEqual(len(s), 1, f"chapter {ch} should keep one paper: {s}")
        order = [next(iter(by_ch[c])) for c in ("A", "B", "C")]
        self.assertNotEqual(order[0], order[1])
        self.assertNotEqual(order[1], order[2])
        self.assertTrue(all(b.startswith("journal/") for b in order))

    def test_flat_defaults_to_shot(self):
        rows = bgs(project("flat"))
        for a, b in zip(rows, rows[1:]):
            self.assertNotEqual(LIB[a[2]]["file"], LIB[b[2]]["file"], (a, b))

    def test_film_mode_one_paper(self):
        for theme in ("journal", "papercut", "archive", "flat"):
            rows = bgs(project(theme, mutate=lambda d: d.update(bgMode="film")))
            self.assertEqual(len({bg for *_, bg in rows}), 1, theme)

    def test_explicit_bg_wins(self):
        def m(d):
            d["shots"][1]["bg"] = "kraft"
            d["shots"][3]["bg"] = "journal/graph"
        rows = bgs(project("journal", mutate=m))
        self.assertEqual(rows[1][2], "journal/kraft")
        self.assertEqual(rows[3][2], "journal/graph")
        # the chapter paper still holds for the other shots of chapter B
        self.assertEqual(rows[2][2], rows[4][2])

    def test_bgrotate_false_is_330_behaviour(self):
        d = project("journal", mutate=lambda d: d.update(bgRotate=False))
        _, out, problems = rs.resolve(d)
        self.assertEqual(problems, [])
        self.assertTrue(all("bgFile" not in r for r in out))

    def test_no_library_output_unchanged_vs_360(self):
        old_src = subprocess.run(["git", "show", "9decea6:scripts/resolve-shots.py"], cwd=ROOT, capture_output=True, text=True)
        if old_src.returncode != 0:
            self.skipTest("3.6.0 commit not in this clone")
        tmp = Path(tempfile.mkdtemp(prefix="nv-rs360-")) / "rs360.py"
        tmp.write_text(old_src.stdout, encoding="utf-8")
        old = load("rs360", tmp)
        for theme in ("journal", "flat"):
            d = project(theme, library=False)
            self.assertEqual(rs.resolve(d)[0], old.resolve(d)[0], theme)
            # and the CLI writes the same shots.resolved.json
            outs = []
            for script in (ROOT / "scripts" / "resolve-shots.py", tmp):
                subprocess.run([sys.executable, str(script), str(d)], check=True, capture_output=True)
                outs.append((d / "manifests" / "shots.resolved.json").read_bytes())
            self.assertEqual(outs[0], outs[1], theme)

    def test_busy_never_on_main(self):
        busy = {k for k, e in LIB.items() if e.get("busy")}
        self.assertGreaterEqual(len(busy), 8)
        for theme in ("journal", "papercut", "archive", "flat", "cel"):
            for mode in ("shot", "chapter", "film"):
                for seed in range(6):
                    d = project(theme, mutate=lambda doc: doc.update(bgMode=mode, bgSeed=seed))
                    _, out, problems = rs.resolve(d)
                    self.assertEqual(problems, [])
                    chapters = rs.chapter_starts(d, out)
                    for r in out:
                        role = "chapter" if r["id"] in chapters else ("quiet" if (r.get("zones") or 0) >= 4 else "main")
                        if role == "main" or mode != "shot":
                            self.assertNotIn(r.get("bg"), busy, (theme, mode, seed, r["id"]))

    def test_validate_shots_adjacency_only_in_shot_mode(self):
        for mode, expect_p1 in (("chapter", False), ("film", False)):
            d = project("journal", mutate=lambda doc: doc.update(bgMode=mode))
            subprocess.run([sys.executable, str(ROOT / "scripts" / "resolve-shots.py"), str(d)], check=True, capture_output=True)
            p0, p1 = vb.check_shots(d)
            self.assertEqual(p0, [])
            self.assertEqual(bool([x for x in p1 if "相邻" in x]), expect_p1, mode)
        # shot mode with a forced repeat is still reported
        def m(doc):
            doc["bgMode"] = "shot"
            doc["shots"][0]["bg"] = "ruled"
            doc["shots"][1]["bg"] = "ruled"
        d = project("journal", mutate=m)
        subprocess.run([sys.executable, str(ROOT / "scripts" / "resolve-shots.py"), str(d)], check=True, capture_output=True)
        self.assertTrue([x for x in vb.check_shots(d)[1] if "相邻" in x])

    def test_bad_mode_is_reported(self):
        _, _, problems = rs.resolve(project("journal", mutate=lambda d: d.update(bgMode="page")))
        self.assertTrue(any("bgMode" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
