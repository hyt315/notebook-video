#!/usr/bin/env python3
"""P2-24 第二切片 · 字幕层的边界契约。

切出 `scripts/story_caption.py` 的风险不在"函数搬没搬"，而在**可变量**：
`CPS` / `CHAR_MS` 是运行期被 `--cps` 改写的。如果主文件留一份副本，CLI 看着生效、
字幕时长却没变——这种 bug 不会报错，只会让成片节奏和作者预期不符。

所以这批测试锁四件事：
  1. 主文件用的是字幕层的实现（函数归属、模块对象）；
  2. 主文件里**没有** CPS / CHAR_MS 副本（有就是定时炸弹）；
  3. `set_cps()` 是唯一写入点，且改完 `time_cue` 立刻跟着变（4.5 → 6.0 时长必须变短）；
  4. 拆行仍守行宽上限、不劈术语 / 英文词；新模块必须进上传包。
"""
from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


cap = load("cap_contract", SCRIPTS / "story_caption.py")
cs = load("cs_caption_contract", SCRIPTS / "compose-story.py")


class FacadeTest(unittest.TestCase):
    FUNCS = ("parse_line", "setup_break_rule", "legal_breaks", "split_caption", "tokens", "time_cue")

    def test_entrypoint_uses_caption_layer_functions(self):
        for name in self.FUNCS:
            self.assertTrue(hasattr(cap, name), f"story_caption 缺 {name}")
            self.assertEqual(getattr(cs, name).__module__, "story_caption",
                             f"compose-story 的 {name} 不是 story_caption 的实现（有人又写了一份）")

    def test_entrypoint_reads_the_same_module_object(self):
        # compose-story 里 `import story_caption as _cap`；必须是同一个模块实例，
        # 否则 set_cps 改了 A、time_cue 读的是 B。
        self.assertIs(cs._cap, sys.modules["story_caption"])

    def test_no_local_copies_of_mutable_pacing(self):
        # 只要主文件还叫 CPS / CHAR_MS，就说明有人把它 import 成了快照（或又定义了一份）。
        for name in ("CPS", "CHAR_MS"):
            self.assertFalse(hasattr(cs, name),
                             f"compose-story 里不该有 {name} 副本；请读 story_caption.{name}")


class SingleSourceTest(unittest.TestCase):
    def _defs(self, pattern: str) -> list[str]:
        hits = []
        for f in sorted(SCRIPTS.glob("*.py")):
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if re.match(pattern, line):
                    hits.append(f"{f.name}:{i}")
        return hits

    def test_pacing_and_width_defined_once(self):
        for pattern, name in ((r"^CPS\s*=", "CPS"),
                              (r"^CHAR_MS\s*=", "CHAR_MS"),
                              (r"^MAX_CHARS\s*=", "MAX_CHARS"),
                              (r"^TERM_RE\s*=", "TERM_RE"),
                              (r"^COMMA_MS\s*,", "COMMA_MS/STOP_MS")):
            hits = self._defs(pattern)
            self.assertEqual(len(hits), 1, f"{name} 定义处应唯一，实际 {hits}")
            self.assertTrue(hits[0].startswith("story_caption.py:"),
                            f"{name} 真源应在 story_caption，实际 {hits}")

    def test_no_global_pacing_assignment_outside_caption_layer(self):
        # set_cps 之外不许出现 `global CPS` —— 那等于绕过唯一写入点。
        src = (SCRIPTS / "compose-story.py").read_text(encoding="utf-8")
        self.assertNotIn("global CPS", src)
        self.assertIn("_cap.set_cps(", src, "--cps 必须走 story_caption.set_cps()")


class SetCpsTest(unittest.TestCase):
    def tearDown(self):
        cap.set_cps(4.5)

    def test_set_cps_changes_cue_duration(self):
        text = "这一句话有二十来个汉字，用来量朗读时长。"
        words_slow, end_slow = cap.time_cue(text, 0)
        cap.set_cps(6.0)
        words_fast, end_fast = cap.time_cue(text, 0)
        self.assertEqual(len(words_slow), len(words_fast))
        self.assertLess(end_fast, end_slow, "提高字/秒后 cue 必须变短（否则就是读到了旧 CHAR_MS）")
        self.assertAlmostEqual(cap.CHAR_MS, 1000 / 6.0, places=6)

    def test_set_cps_rejects_nothing_but_stores_float(self):
        cap.set_cps(3)
        self.assertIsInstance(cap.CPS, float)
        self.assertAlmostEqual(cap.CHAR_MS, 1000 / 3.0, places=6)


class SplitDisciplineTest(unittest.TestCase):
    def test_lines_respect_max_chars(self):
        text = "这一句故意写得很长，用来验证拆行以后每一行都不会超过上限，也不会把词语劈开。"
        parts = cap.split_caption(text, [], [])
        self.assertGreater(len(parts), 1)
        for piece, _ in parts:
            self.assertLessEqual(cap.line_len(piece), cap.MAX_CHARS, f"超长行：{piece!r}")

    def test_ascii_word_is_not_split(self):
        text = "把 report_generator 这个名字完整地留在同一行里，不要从中间断开。"
        parts = cap.split_caption(text, [], [])
        joined = "".join(p for p, _ in parts)
        self.assertEqual(joined.replace(" ", ""), text.replace(" ", ""))
        self.assertTrue(any("report_generator" in p for p, _ in parts), parts)

    def test_term_offsets_survive_split(self):
        raw = "先看{{缓存|L3}}再决定后面每一步该怎么走，这句话足够长会被拆成两行。"
        text, terms = cap.parse_line(raw)
        self.assertEqual(text, "先看缓存再决定后面每一步该怎么走，这句话足够长会被拆成两行。")
        parts = cap.split_caption(text, terms, [])
        # 术语要么整段在第一行，要么整段在第二行；重算偏移后必须还能落回词首。
        rebuilt = []
        for piece, pt in parts:
            for t in pt:
                rebuilt.append(piece[t["start"]:t["start"] + len(t["text"])])
        self.assertEqual(rebuilt, ["缓存"], f"术语被劈开或偏移错了：{parts}")


class PackageIncludesModuleTest(unittest.TestCase):
    def test_package_collects_caption_layer(self):
        pk = load("pkg_caption_contract", SCRIPTS / "package-skill.py")
        files = {p.relative_to(ROOT).as_posix() for p in pk.collect_files()}
        self.assertIn("scripts/story_caption.py", files)


if __name__ == "__main__":
    unittest.main()
