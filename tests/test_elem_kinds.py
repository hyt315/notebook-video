"""3.6.2 · 元素种类门禁（validate-elem-kinds.py）

事故记录（两次都出自同一类"排版器生成了渲染器不认识的东西"）：
1. `flow` 版式排版出 `kind: "node"`，`auto.tsx` 的 ElemView 只有 archive / lettering / stamp /
   handnote / loupe / figure / media / region → switch 落到 default 返回 null，**节点整镜不画**，
   没有任何门禁报错（--stills 只截前几镜，front matter 全绿）。
2. 补上 `case 'node'` 时 CSS 写成了 `inset: 0, border: ..., border: ...`，React 抛 error #130，
   整片渲染到第 566 帧直接失败——那时已经跑了几分钟。

所以这条门禁只做一件事：**compose-story 能产出的每一种 kind，渲染器里必须有 case**。
它是静态源码比对，不渲染、不联网。只用标准库 unittest（CI 不装 pytest）。
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "validate-elem-kinds.py"
TEMPLATE = ROOT / "assets" / "lecture-template"


def run(project: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(project)],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )


def load_gate():
    spec = importlib.util.spec_from_file_location("vek_unittest", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


class ElemKindsTest(unittest.TestCase):
    def test_template_passes(self):
        """模板本身必须通过：它同时是全片渲染的起点。"""
        r = run(TEMPLATE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_case_is_caught(self):
        """把 node 分支改名 → 必须点名 node（而不是静默通过）。"""
        src = (TEMPLATE / "src" / "auto.tsx").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory(prefix="nv-elem-kinds-") as td:
            proj = Path(td) / "p"
            (proj / "src").mkdir(parents=True)
            (proj / "src" / "auto.tsx").write_text(src.replace("case 'node':", "case 'nodeX':"), encoding="utf-8")
            r = run(proj)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("'node'", r.stdout)

    def test_fstring_ids_are_parsed(self):
        """flow / list / quiz 的元素 id 是 f"step{i+1}" 这种 f-string。

        第一版判据只认 `el("字面量", …)`，于是 node / item / option 被当作"从没产出过"，
        判据等于没跑——这条用例就是钉住那个 bug。
        """
        mod = load_gate()
        emitted = mod.kinds_emitted((ROOT / "scripts" / "story_layout.py").read_text(encoding="utf-8"),
                            (ROOT / "scripts" / "compose-story.py").read_text(encoding="utf-8"))
        for kind in ("node", "item", "option", "codeline", "bar", "panel", "card", "timer"):
            with self.subTest(kind=kind):
                self.assertIn(kind, emitted, f"{kind} 没被解析出来 —— f-string id 的 el() 调用被漏掉了")

    def test_handled_set_excludes_color_keys(self):
        """`tone()` 里的 case 'blue' 不是 ElemView 的种类，不能被当成"已处理"。"""
        mod = load_gate()
        text = (TEMPLATE / "src" / "auto.tsx").read_text(encoding="utf-8")
        handled = mod.kinds_handled(text)
        self.assertTrue({"node", "panel"} <= handled)
        self.assertFalse({"blue", "green", "gold", "red"} & handled)


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# P1-15：上面那组是"源码里写过什么"；下面这组是"这次真的排出了什么"。
# 两者不一致时，只有跑出来的产物说了算——f-string id 那次就是源码扫描漏掉了 node/item/option，
# 判据等于没跑，而渲染到那一镜才发现整块没画。
# ---------------------------------------------------------------------------

CORPUS = (
    "examples/concept-hash-table.story.json",   # flow / compare / define / number
    "examples/code-change-cache.story.json",    # code / quiz / bars / custom
    "examples/data-ssd-vs-hdd.story.json",      # list / bars / compare
    "examples/recipes/jie-freeform.story.json", # page(ink) / type
    "examples/recipes/cork-page.story.json",    # page(loupe) / compare
)


def compose_kinds(story: str) -> set[str]:
    """跑一遍 compose，从产物 src/story.ts 取这次真实排出的 kind。"""
    with tempfile.TemporaryDirectory(prefix="nv-elem-") as td:
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "compose-story.py"),
                            story, td, "--report", str(Path(td) / "report.json")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
        if r.returncode != 0:
            raise AssertionError(f"compose 失败（{story}）：{(r.stdout or '')[-400:]}")
        ts = Path(td) / "src" / "story.ts"
        if not ts.is_file():
            raise AssertionError(f"compose 没写出 src/story.ts（{story}）")
        return load_gate().kinds_in_output(ts.read_text(encoding="utf-8"))


class EmittedKindsAreRealTest(unittest.TestCase):
    def test_corpus_output_is_covered_by_the_renderer(self):
        mod = load_gate()
        handled = mod.kinds_handled((TEMPLATE / "src" / "auto.tsx").read_text(encoding="utf-8"))
        static = mod.kinds_emitted((ROOT / "scripts" / "story_layout.py").read_text(encoding="utf-8"),
                                   (ROOT / "scripts" / "compose-story.py").read_text(encoding="utf-8")) - mod.NOT_ELEM_KINDS
        seen: set[str] = set()
        for story in CORPUS:
            seen |= compose_kinds(story)
        # 语料要真的覆盖到多种元素，否则这条测试只是空转
        self.assertGreaterEqual(len(seen), 16, f"语料只排出 {sorted(seen)} 种元素，覆盖面太窄")
        self.assertEqual(sorted(seen - handled), [],
                         f"这些 kind 是真排出来的，但 ElemView 里没有 case：{sorted(seen - handled)}")
        # 产物里有、源码扫描却没认出来 → 判据又跟不上排版器的写法了
        self.assertEqual(sorted(seen - static), [],
                         f"kind_emitted 漏掉了这些真实产物：{sorted(seen - static)}")

    def test_output_with_unknown_kind_fails_the_gate(self):
        """把产物里塞一个 ElemView 不认识的 kind → 门禁必须点名它。"""
        with tempfile.TemporaryDirectory(prefix="nv-elem-") as td:
            proj = Path(td) / "p"
            (proj / "src").mkdir(parents=True)
            (proj / "src" / "auto.tsx").write_text(
                (TEMPLATE / "src" / "auto.tsx").read_text(encoding="utf-8"), encoding="utf-8")
            (proj / "src" / "story.ts").write_text(
                'export const STORY: Record<string, any> = {"S1":{"elements":['
                '{"id":"x","kind":"wobble","x":0,"y":0,"w":1,"h":1,"text":"","size":0,"role":"body","at":0}]}};\n',
                encoding="utf-8")
            r = run(proj)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("wobble", r.stdout)
