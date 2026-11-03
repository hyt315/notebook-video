#!/usr/bin/env python3
"""wrap 的中文排版纪律：数字与单位不拆开。

实测缺陷：flow 的 note「47 呎 3 吋」被折成「47 呎 3 / 吋一个」。
根因有两个，都得盖住：
  1. 折行点常落在「3」与「吋」之间的**空格 token** 上，只看「下一个 token 是不是 CJK」会漏；
  2. 孤字调整会把「吋」从「47 呎 3 吋」挪到下一行，同样把数字与单位拆开。
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cs_wrap", ROOT / "scripts" / "compose-story.py")
cs = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(cs)

UNITS = "吋呎秒里米度节"


class WrapTest(unittest.TestCase):
    def test_number_and_unit_stay_together(self):
        texts = [
            "木板长 47 呎 3 吋一个",
            "沙漏 28 秒一次，绳结间距 47 呎 3 吋",
            "一节等于 1.852 公里每小时",
            "流速 3 节，风向 45 度",
        ]
        for text in texts:
            for maxw in range(120, 460, 20):
                lines = cs.wrap(text, 40, maxw)
                for a, b in zip(lines, lines[1:]):
                    a = a.rstrip()
                    self.assertFalse(
                        a and a[-1].isdigit() and b[:1] in UNITS,
                        f"{text!r} @maxw={maxw} 把数字与单位拆开了：{lines}",
                    )

    def test_orphan_fix_does_not_split_unit(self):
        # 末行只剩「一个」时会触发孤字调整，这里正是「47 呎 3 / 吋一个」的来源
        lines = cs.wrap("木板长 47 呎 3 吋一个", 40, 270)
        self.assertEqual(lines, ["木板长 47 呎", "3 吋一个"])

    def test_english_words_still_not_split(self):
        lines = cs.wrap("the knot is 1.852 km/h exactly", 40, 200)
        self.assertNotIn("km/", lines)
        self.assertIn("km/h", " ".join(lines))


if __name__ == "__main__":
    unittest.main()
