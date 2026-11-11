"""SKILL.md frontmatter 必须是合法 YAML，且 description ≤ 1024 字符（Agent Skills 规范上限）。

3.5.4 事故：description 一度长到 1805 字符；而且它是不加引号的纯标量，里面出现了
「comes first: there is」这种「冒号+空格」—— 严格的 YAML 解析器直接报
"mapping values are not allowed here"，整个 frontmatter 读不出来，技能可能根本无法被路由。
本测试不依赖 PyYAML（CI 只有标准库）；装了 PyYAML 时顺带做一次真解析。
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "SKILL.md"
MAX_DESCRIPTION = 1024
# 触发词：压缩 description 时不能把它们压没（路由靠这些词命中中文请求）
TRIGGERS = ("做科普视频", "讲解视频", "概念讲解", "代码讲解", "数据对比视频", "流程讲解", "踩坑提醒", "产品讲解", "MP4")


def frontmatter() -> str:
    text = SKILL.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md 必须以 --- frontmatter --- 开头"
    return m.group(1)


def fields(fm: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in fm.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s?(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


class SkillFrontmatterTest(unittest.TestCase):
    def test_description_length(self):
        d = fields(frontmatter()).get("description", "")
        self.assertTrue(d, "frontmatter 缺 description")
        self.assertLessEqual(len(d), MAX_DESCRIPTION,
                             f"description {len(d)} 字符 > {MAX_DESCRIPTION}：细节下沉到正文 / references，保留触发词")

    def test_description_keeps_triggers(self):
        d = fields(frontmatter()).get("description", "")
        for w in TRIGGERS:
            self.assertIn(w, d, f"description 里缺触发词「{w}」")

    def test_plain_scalars_are_valid_yaml(self):
        for k, v in fields(frontmatter()).items():
            if v[:1] in ("'", '"', "|", ">"):
                continue
            self.assertNotIn(": ", v, f"{k} 是不加引号的纯标量，含「: 」会让 YAML 解析失败")
            self.assertNotIn(" #", v, f"{k} 含「 #」会被 YAML 当成注释截断")
            self.assertFalse(v[:1] in "&*!%@`[]{},", f"{k} 以 YAML 特殊字符开头")

    def test_name(self):
        self.assertEqual(fields(frontmatter()).get("name"), "notebook-video")

    def test_real_yaml_parse_when_available(self):
        try:
            import yaml  # type: ignore
        except ImportError:
            self.skipTest("PyYAML 未安装；纯标量规则已由上一条覆盖")
        data = yaml.safe_load(frontmatter())
        self.assertEqual(data["name"], "notebook-video")
        self.assertLessEqual(len(data["description"]), MAX_DESCRIPTION)


if __name__ == "__main__":
    unittest.main()
