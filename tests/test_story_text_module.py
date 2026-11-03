#!/usr/bin/env python3
"""P2-24 第一切片 · 文字层的边界契约。

切出 `scripts/story_text.py` 的目的是「改折行规则只碰一个文件」，不是让主文件变短。
所以这批测试锁的不是某个折行结果（那在 test_wrap / test_text_metrics / compose-golden），
而是**边界本身**：

  1. 主文件必须真的在用它（re-export 同一批对象），不能留一份私有实现；
  2. 文字层不能反向依赖主文件（没有循环 import 的隐患）；
  3. 字号地板 / 行高地板 / 标点集只有一处定义（「共享常量必须先明确真源」）；
  4. `fit_text` 不依赖 Problems 的实现（任何 err/fix/hint 收集器都能用）；
  5. 上传包必须带上新模块（切出去但没打包 = 用户那边直接起不来）。
"""
from __future__ import annotations

import importlib.util
import re
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


st = load("st_contract", SCRIPTS / "story_text.py")
cs = load("cs_contract", SCRIPTS / "compose-story.py")


class FacadeTest(unittest.TestCase):
    """主文件是门面：同名对象必须是同一个实现，不能各写一份。"""

    FUNCS = ("wrap", "fit_text", "text_w", "safe_lh", "is_wide", "units", "cap_chars", "line_len")
    CONSTS = ("SAFE_LH", "MIN_FONT", "PUNCT")

    def test_entrypoint_uses_text_layer_functions(self):
        # 比较 __module__ 而不是对象 identity：测试里 compose-story 与 story_text 可能被
        # 加载成两个模块实例，identity 会假失败；函数归属哪个模块才是真契约。
        for name in self.FUNCS:
            self.assertTrue(hasattr(st, name), f"story_text 缺 {name}")
            self.assertEqual(getattr(cs, name).__module__, "story_text",
                             f"compose-story 的 {name} 不是 story_text 的实现（有人又写了一份）")

    def test_entrypoint_uses_text_layer_constants(self):
        # 常量比较取值（float 不保证同一对象）；「只有一处定义」由 SingleSourceOfTruthTest 锁。
        for name in self.CONSTS:
            self.assertTrue(hasattr(st, name), f"story_text 缺 {name}")
            self.assertEqual(getattr(cs, name), getattr(st, name),
                             f"compose-story 的 {name} 与 story_text 不同值（有人又写了一份）")

    def test_wrap_goes_through_the_same_function(self):
        # 同一批输入两个入口必须给同一结果；如果主文件留了副本，这里会先分叉再漂移。
        cases = ["木板长 47 呎 3 吋一个", "「你说的对」——但是（注意）这里……", "GPU 8 卡 × 32 GB"]
        for text in cases:
            for maxw in (140, 260, 420):
                self.assertEqual(cs.wrap(text, 40, maxw), st.wrap(text, 40, maxw))


class NoBackReferenceTest(unittest.TestCase):
    """文字层不能 import 主文件：主文件 import 它，反向依赖就是循环。"""

    def test_text_layer_does_not_import_entrypoint(self):
        src = (SCRIPTS / "story_text.py").read_text(encoding="utf-8")
        live = [ln for ln in src.splitlines() if not ln.strip().startswith("#")]
        for ln in live:
            if not re.match(r"\s*(import|from)\s+", ln):
                continue
            self.assertNotIn("compose", ln, f"story_text 反向依赖主文件：{ln.strip()}")

    def test_text_layer_only_imports_real_dependencies(self):
        src = (SCRIPTS / "story_text.py").read_text(encoding="utf-8")
        self.assertIn("import text_metrics as _tm", src,
                      "字宽必须问真字体（P2-17）；看不到这个 import 说明又回去数字宽了")


class SingleSourceOfTruthTest(unittest.TestCase):
    """共享常量只能有一处定义——两处定义就会悄悄分叉。"""

    def _defs(self, pattern: str) -> list[str]:
        hits = []
        for f in sorted(SCRIPTS.glob("*.py")):
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if re.match(pattern, line):
                    hits.append(f"{f.name}:{i}")
        return hits

    def test_safe_lh_defined_once(self):
        hits = self._defs(r"^SAFE_LH\s*=")
        self.assertEqual(len(hits), 1, f"SAFE_LH 定义处应唯一，实际 {hits}")
        self.assertTrue(hits[0].startswith("story_text.py:"), f"SAFE_LH 真源应在 story_text，实际 {hits}")

    def test_typography_constants_defined_once(self):
        for pattern, name in ((r"^MIN_FONT\s*=", "MIN_FONT"),
                              (r"^PUNCT\s*=", "PUNCT"),
                              (r"^TAIL_PUNCT_RE\s*=", "TAIL_PUNCT_RE")):
            hits = self._defs(pattern)
            self.assertEqual(len(hits), 1, f"{name} 定义处应唯一，实际 {hits}")
            self.assertTrue(hits[0].startswith("story_text.py:"), f"{name} 真源应在 story_text，实际 {hits}")


class DuckTypedCollectorTest(unittest.TestCase):
    """fit_text 只调用 p.err / p.fix / p.hint —— 不该知道 Problems 类长什么样。"""

    class Collector:
        def __init__(self):
            self.errors, self.fixes, self.hints = [], [], []

        def err(self, m): self.errors.append(m)
        def fix(self, m): self.fixes.append(m)
        def hint(self, m): self.hints.append(m)

    def test_fit_text_accepts_any_collector(self):
        p = self.Collector()
        lines, size, width, height = st.fit_text(p, "t", "一句话", 46, 600, 2)
        self.assertEqual(len(lines), 1)
        self.assertEqual(size, 46)
        self.assertGreater(width, 0)
        self.assertAlmostEqual(height, size * st.SAFE_LH, places=3)

    def test_fit_text_reports_when_it_cannot_fit(self):
        p = self.Collector()
        st.fit_text(p, "t", "很长的句子" * 12, 46, 200, 1)
        self.assertTrue(p.errors, "放不下时必须报错（而不是静默截断）")


class PackageIncludesModuleTest(unittest.TestCase):
    """切出去的模块必须进上传包；漏了就是「本地能跑、用户那边 ModuleNotFoundError」。"""

    def test_package_collects_text_layer(self):
        pk = load("pkg_contract", SCRIPTS / "package-skill.py")
        files = {p.relative_to(ROOT).as_posix() for p in pk.collect_files()}
        self.assertIn("scripts/story_text.py", files)
        self.assertIn("scripts/compose-story.py", files)


if __name__ == "__main__":
    unittest.main()
