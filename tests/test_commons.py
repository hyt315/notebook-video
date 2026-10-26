#!/usr/bin/env python3
"""Offline tests for scripts/commons-search.py (license normalisation, attribution, credits).

The fixture tests/fixtures/commons-imageinfo.json is a real MediaWiki API response captured on 2026-10-26,
so these tests never touch the network.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("commons_search", ROOT / "scripts" / "commons-search.py")
cs = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(cs)

vm_spec = importlib.util.spec_from_file_location("validate_media", ROOT / "scripts" / "validate-media.py")
vm = importlib.util.module_from_spec(vm_spec)
assert vm_spec.loader
vm_spec.loader.exec_module(vm)


class LicenseTests(unittest.TestCase):
    def v(self, short, usage="", url=""):
        return cs.classify_license(short, usage, url)

    def test_public_domain_and_cc0_are_ok(self):
        for s in ("Public domain", "PD-old-100", "PD-US", "CC0", "cc0 1.0"):
            r = self.v(s)
            self.assertEqual(r["verdict"], "ok", s)
            self.assertFalse(r["attribution"], s)

    def test_cc_by_ok_with_attribution(self):
        r = self.v("CC BY 4.0", "Creative Commons Attribution 4.0")
        self.assertEqual((r["verdict"], r["license"], r["attribution"]), ("ok", "cc-by-4.0", True))
        self.assertEqual(self.v("CC BY 3.0 us")["license"], "cc-by-3.0")

    def test_by_sa_is_excluded_by_default(self):
        r = self.v("CC BY-SA 4.0", "Creative Commons Attribution-Share Alike 4.0")
        self.assertEqual((r["verdict"], r["license"]), ("sa", "cc-by-sa-4.0"))
        self.assertIn("相同方式共享", r["reason"])

    def test_rejections(self):
        for s in ("CC BY-NC 2.0", "CC BY-ND 4.0", "GFDL", "FAL", "No restrictions", "Attribution", "", "All rights reserved"):
            self.assertEqual(self.v(s)["verdict"], "reject", s)

    def test_normalised_ids_pass_validate_media_whitelist(self):
        for s in ("Public domain", "CC0", "CC BY 4.0", "CC BY 2.0", "CC BY-SA 3.0"):
            lid = self.v(s)["license"]
            self.assertTrue(vm.LICENSE_OK.match(lid), f"{s} → {lid} not in validate-media whitelist")


class FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pages = json.loads((ROOT / "tests" / "fixtures" / "commons-imageinfo.json").read_text(encoding="utf-8"))["pages"]
        cls.recs = {p["title"]: cs.describe(p) for p in pages}

    def test_pd_plate(self):
        r = self.recs["File:Micrographia Schem 11.jpg"]
        self.assertEqual(r["verdict"], "ok")
        self.assertEqual(r["license"], "public-domain")
        self.assertIn("Hooke", r["artist"])
        self.assertNotIn("<", r["artist"])  # HTML stripped
        self.assertIn("公有领域", r["credit"])

    def test_cc_by_institution_fallback(self):
        r = self.recs["File:Robert Hooke, Micrographia, cork. Wellcome M0010579.jpg"]
        self.assertEqual(r["license"], "cc-by-4.0")
        self.assertIn("wellcome", r["artist"].lower())
        self.assertIn("CC BY 4.0", r["credit"])

    def test_by_sa_fixture(self):
        r = self.recs["File:Coffee Ring Effect using Coffee Image.png"]
        self.assertEqual(r["verdict"], "sa")

    def test_download_choice(self):
        r = dict(self.recs["File:Robert Hooke, Micrographia, cork. Wellcome M0010579.jpg"])
        url, ext = cs.pick_download(r, 1280)  # original 2697 px wide > 1280×1.25 → thumbnail
        self.assertEqual(url, r["thumbUrl"])
        url2, _ = cs.pick_download(r, 2560)   # 2697 ≤ 3200 → original
        self.assertEqual(url2, r["url"])

    def test_credits_markdown(self):
        items = []
        for i, r in enumerate(self.recs.values()):
            items.append({"id": f"m{i}", "source": "web", "url": r["pageUrl"], "license": r["license"], "credit": r["credit"],
                          "shareAlike": r["verdict"] == "sa",
                          "commons": {k: r[k] for k in ("title", "artist", "licenseShort", "licenseUrl")}})
        txt = cs.build_credits(items)
        self.assertIn("Micrographia Schem 11", txt)
        self.assertIn("CC BY-SA", txt)
        self.assertIn("相同方式共享", txt)
        self.assertEqual(len(re.findall(r"^- \*\*", txt, re.M)), 3)


class OpenverseTests(unittest.TestCase):
    def test_openverse_records(self):
        res = json.loads((ROOT / "tests" / "fixtures" / "openverse-audio.json").read_text(encoding="utf-8"))["results"]
        for r in res:
            rec = cs.ov_describe(r, "audio")
            self.assertTrue(rec["title"].startswith("openverse:audio:"))
            self.assertIn(rec["verdict"], ("ok",))  # request filters cc0 / pdm / by
            self.assertTrue(vm.LICENSE_OK.match(rec["license"]), rec["license"])
            self.assertIn(rec["provider"] or "Openverse", rec["credit"])

    def test_openverse_title_format(self):
        with self.assertRaises(SystemExit):
            cs.ov_fileinfo("openverse:video:abc", None)


class ParseTests(unittest.TestCase):
    def test_positionals_skip_option_values(self):
        args = ["./p", "File:A b.jpg", "--id", "a", "--region", "r", "0.1", "0.2", "0.3", "0.4", "--allow-by-sa", "--width", "1920"]
        self.assertEqual(cs.positionals(args), ["./p", "File:A b.jpg"])

    def test_pronunciation_filter(self):
        for t in ("File:LL-Q1860 (eng)-Flame-postage stamp.wav", "File:En-us-punched tape.oga", "File:En-uk-scissors.ogg"):
            self.assertTrue(cs.PRONUNCIATION.search(t), t)
        for t in ("File:Pencil scratchings.ogg", "File:Holga shuttersound.ogg", "File:Clapping hurray.ogg"):
            self.assertFalse(cs.PRONUNCIATION.search(t), t)


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False, verbosity=1).result.wasSuccessful() else 1)
