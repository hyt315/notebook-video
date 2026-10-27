#!/usr/bin/env python3
"""Tests for the 3.6.0 subtitle fixes: whole-line reveal, no empty halo, mixed CJK/Latin spacing, full-width punctuation."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "lecture-template" / "src"


def gap_js() -> str:
    ts = (SRC / "caption-gap.ts").read_text(encoding="utf-8")
    js = re.sub(r"\(prevRaw: string, partRaw: string\): string", "(prevRaw, partRaw)", ts).replace("export const", "const")
    assert ": string" not in js, "caption-gap.ts gained type annotations the test cannot strip"
    return js


@unittest.skipUnless(shutil.which("node"), "node not installed")
class CaptionGap(unittest.TestCase):
    def gaps(self, pairs: list[tuple[str, str]]) -> list[str]:
        code = gap_js() + f"\nconsole.log(JSON.stringify({json.dumps(pairs, ensure_ascii=False)}.map(([a,b])=>captionGap(a,b))));"
        r = subprocess.run(["node", "-e", code], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_trailing_space_in_previous_piece_becomes_nbsp(self):
        # cell 片第 10 条：词片 '语 ' + 'cella：' 旧版渲染成「拉丁语cella：」
        self.assertEqual(self.gaps([("语 ", "cella：")]), ["\u00a0"])

    def test_existing_rules_kept(self):
        got = self.gaps([("三个", "AI"), ("AI", "技能"), ("细", "胞"), ("cell", "s"), ("，", "AI"), ("AI", "，"), ("", "AI")])
        self.assertEqual(got, ["\u00a0", "\u00a0", "", "", "", "", ""])

    def test_no_space_inside_corner_quotes(self):
        self.assertEqual(self.gaps([("「", "cella"), ("cella", "」")]), ["", ""])


class SubtitleSource(unittest.TestCase):
    idx = (SRC / "index.tsx").read_text(encoding="utf-8")

    def test_line_reveal_is_default_for_craft_and_overridable(self):
        self.assertIn("(FILM as any).CAPTION_REVEAL??AESTHETIC.captionReveal??(THEME.craft?'line':'type')", self.idx)
        self.assertIn("captionReveal?: 'line' | 'type';", (SRC / "theme" / "types.ts").read_text(encoding="utf-8"))
        body = self.idx[self.idx.index("const Subtitle=()=>{"):self.idx.index("const Chrome=()=>{")]
        self.assertIn("if(line){", body)
        self.assertIn("LINE_FADE", body)

    def test_no_halo_before_the_first_character(self):
        body = self.idx[self.idx.index("const Subtitle=()=>{"):self.idx.index("const Chrome=()=>{")]
        self.assertIn("if(!cue||!targetChars||!words.length)return null;", body)

    def test_whitespace_not_counted_for_tail_trim(self):
        body = self.idx[self.idx.index("const Subtitle=()=>{"):self.idx.index("const Chrome=()=>{")]
        self.assertIn("full.replace(/\\s+/g,'').length", body)
        self.assertIn("filter((ch)=>!/\\s/.test(ch))", body)

    def test_halt_on_paper_subtitles(self):
        self.assertIn("fontFeatureSettings: '\"halt\"'", (SRC / "theme" / "craft-common.tsx").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
