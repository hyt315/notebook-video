"""P1-09 / P1-08：线稿库的构建期契约 + SVG defs 的实例唯一 id。

两条都是「渲染成功但画面错了」的隐形故障：

P1-09 · 线稿名 / 部位名写错
    `draw: "lib:hourglass"`（库里没有这个线稿）→ `resolveSketchDef` 返回 null →
    `SketchLayer` 直接 return null，那一镜**什么都没画**。渲染照样成功、时长照样对、
    空白门禁被文字填满也可能通过。部位名写错则画整图（与旁白不符）。
    第一次跑这个检查就在真实探针工程 `_probe/story.json` 里抓到一处 `lib:hourglass`
    （已修为 `lib:clock`）—— 说明它不是假想问题。

P1-08 · SVG filter / mask id 跨镜碰撞
    转场期间上一镜与本镜同时挂载。两镜里 `spec.id` 都叫 `n1` 时，会渲染出两个
    `<filter id="paint-n1-0">`；浏览器取第一个，于是后一镜的颜料滤镜用了前一镜的 seed。
    同理：`WashBlob` 默认 seed 都叫 `wash`、`CutPaper` 默认 id 都叫 `cp`、
    `MediaFrame` 用素材 id 当 mask id。

只用标准库 unittest（CI 不装 pytest）。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TEMPLATE = ROOT / "assets" / "lecture-template"
SRC = TEMPLATE / "src"

sys.path.insert(0, str(SCRIPTS))
import linework_index as li  # noqa: E402


class LibraryParseTest(unittest.TestCase):
    def test_every_sketch_has_parts(self):
        lib = li.load_library()
        self.assertGreaterEqual(len(lib), 31, "线稿库解析出的数量明显偏少，解析规则可能失效了")
        self.assertEqual(lib["chiplog"], ("hull", "line", "plank"))
        self.assertEqual(lib["rocket"], ("payload", "stage2", "stage1"))

    def test_parse_failure_is_loud_not_silent(self):
        with self.assertRaises(li.LibraryParseError):
            li.parse_library("export const SKETCHES = {};\n")
        with self.assertRaises(li.LibraryParseError):
            li.parse_library("// 没有 SKETCHES\n")

    def test_sketch_without_parts_is_rejected(self):
        text = "export const SKETCHES = {\n  empty: {\n    label: 'x',\n    fit: [0, 0, 10, 10],\n  },\n};\n"
        with self.assertRaises(li.LibraryParseError):
            li.parse_library(text)


class SelectionTest(unittest.TestCase):
    def test_missing_sketch_is_an_error_with_the_real_names(self):
        problems = li.check_selection("lib:hourglass", None)
        self.assertEqual(len(problems), 1)
        self.assertIn("lib:hourglass", problems[0])
        self.assertIn("不在线稿库", problems[0])
        self.assertIn("共 31 个", problems[0])

    def test_typo_gets_a_suggestion(self):
        problems = li.check_selection("lib:chiplg", None)
        self.assertEqual(len(problems), 1)
        self.assertIn("lib:chiplog", problems[0], "拼写接近时必须给出候选，否则作者只能猜")

    def test_unknown_part_lists_valid_parts(self):
        problems = li.check_selection("lib:chiplog", ["hull", "planks"])
        self.assertEqual(len(problems), 1)
        self.assertIn("planks", problems[0])
        self.assertIn("hull / line / plank", problems[0])

    def test_valid_selection_passes(self):
        self.assertEqual(li.check_selection("lib:chiplog", ["hull", "line"]), [])
        self.assertEqual(li.check_selection("lib:chiplog", None), [])
        self.assertEqual(li.check_selection("lib:rocket", ["stage1"]), [])

    def test_record_form_keys_are_checked_too(self):
        """`parts: {hull: "船尾"}` 是 point 的标注表，键同样是部位名。"""
        self.assertEqual(li.check_selection("lib:chiplog", {"hull": "船尾"}), [])
        self.assertTrue(li.check_selection("lib:chiplog", {"haull": "船尾"}))

    def test_shapes_have_only_the_whole_part(self):
        self.assertEqual(li.check_selection("shapes:[{\"k\":\"rect\"}]", ["all"]), [])
        self.assertTrue(li.check_selection("shapes:[{\"k\":\"rect\"}]", ["hull"]))

    def test_trace_is_left_to_the_photo_recipe(self):
        self.assertEqual(li.check_selection("trace:pr-page", ["whatever"]), [])


class ComposeWiringTest(unittest.TestCase):
    def test_compose_checks_before_writing(self):
        # P2-24 第三切片起 resolve_sketch 在 story_acts.py；断言跟着实现文件走，契约不变。
        src = (SCRIPTS / "story_acts.py").read_text(encoding="utf-8")
        fn = src[src.index("def resolve_sketch("):]
        fn = fn[:fn.index("def resolve_annotate(")]
        self.assertIn("linework_index.check_selection(", fn)
        self.assertIn("p.err(", fn.split("linework_index.check_selection(")[1].split("for msg")[1])
        # 有问题时不能继续往下产出一个"没有图"的 sketch
        self.assertIn("if problems:\n        return None", fn)


def draw_specs(node, out=None):
    """draw 规格散落在 shot.sketch / content.ink / content.figure，递归收一遍。"""
    out = [] if out is None else out
    if isinstance(node, dict):
        if "draw" in node:
            out.append(node)
        for v in node.values():
            draw_specs(v, out)
    elif isinstance(node, list):
        for v in node:
            draw_specs(v, out)
    return out


class ComposeRejectsBadSketchTest(unittest.TestCase):
    """端到端：写错部位名 → compose 必须失败，而不是产出一份"少画一镜"的工程。"""

    def _run(self, story: dict) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "story.json"
            p.write_text(json.dumps(story, ensure_ascii=False, indent=1), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(SCRIPTS / "compose-story.py"), str(p), td,
                 "--report", str(Path(td) / "report.json"), "--check"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT,
            )

    @classmethod
    def _story_with(cls, parts) -> dict:
        story = json.loads((ROOT / "examples" / "recipes" / "jie-freeform.story.json").read_text(encoding="utf-8"))
        for spec in draw_specs(story):
            if str(spec.get("draw", "")).startswith("lib:"):
                spec["parts"] = parts
                return story
        raise AssertionError("夹具 story 里没有可改的 lib: 线稿")

    def test_unknown_part_fails_the_build(self):
        r = self._run(self._story_with(["hull", "planks"]))
        self.assertEqual(r.returncode, 1, r.stdout[-1500:])
        self.assertIn("planks", r.stdout)
        self.assertIn("不在", r.stdout)

    def test_unknown_sketch_name_fails_the_build(self):
        story = self._story_with(["hull"])
        for spec in draw_specs(story):
            if str(spec.get("draw", "")).startswith("lib:"):
                spec["draw"] = "lib:hourglass"
                break
        r = self._run(story)
        self.assertEqual(r.returncode, 1, r.stdout[-1500:])
        self.assertIn("hourglass", r.stdout)


class UniqueSvgIdTest(unittest.TestCase):
    """源码级契约：DOM id 不得再拼业务 id。"""

    def test_shared_hook_exists(self):
        text = (SRC / "uid.ts").read_text(encoding="utf-8")
        self.assertIn("useId()", text)
        self.assertIn("warnOnce", text)

    def test_sketch_uses_instance_id_but_keeps_deterministic_seed(self):
        text = (SRC / "linework" / "sketch.tsx").read_text(encoding="utf-8")
        self.assertIn("const svgUid = useSvgId('paint');", text)
        self.assertIn("const pid = `${svgUid}-${i}`;", text)
        self.assertNotIn("const pid = `paint-${uid}-${i}`;", text)
        # seed 仍由 spec.id 定死：同一线稿必须每帧同一张图
        self.assertIn("const seedKey = String(spec.id ?? 'sk')", text)
        self.assertIn("const paintSeed = [...seedKey].reduce(", text)

    def test_hook_is_called_before_any_early_return(self):
        """组件会在入场前 return null；hook 若在那之后调用就违反 hooks 规则。"""
        for rel, hook in (("linework/sketch.tsx", "useSvgId('paint')"),
                          ("craft/paper.tsx", "useSvgId('wash')"),
                          ("craft/paper.tsx", "useSvgId('cut')"),
                          ("media-frame.tsx", "useSvgId('mf')")):
            text = (SRC / rel).read_text(encoding="utf-8")
            call = text.index(hook)
            body_start = text.rindex("React.FC<", 0, call)   # 本组件的定义起点
            head = text[body_start:call]
            self.assertNotIn("return null;", head, f"{rel}: {hook} 必须在组件内任何 return 之前")

    def test_no_svg_def_id_is_built_from_a_shared_business_id(self):
        banned = [
            "const id = `wash-${seed}`",
            "clipPath id={`cut-${cid}`}",
            "const mid = `mf-hi-${id}`",
        ]
        joined = "\n".join(p.read_text(encoding="utf-8") for p in SRC.rglob("*.tsx"))
        for b in banned:
            self.assertNotIn(b, joined, f"仍有从业务 id 拼出来的 SVG def id：{b}")

    @staticmethod
    def _def_id_exprs(text: str):
        """扫出每个 <filter|clipPath|mask|…> 的 id 表达式（跳过注释里的例子）。"""
        out = []
        for m in re.finditer(r"<(?:filter|clipPath|mask|pattern|linearGradient|radialGradient)\b", text):
            if "svg-id: singleton" in text[max(0, m.start() - 400):m.start() + 200]:
                continue
            seg = text[m.start():m.start() + 500]
            cut = seg.find("/>")
            newline = seg.find("\n")
            seg = seg[:min(x for x in (cut, newline, len(seg)) if x >= 0)]
            i = seg.find("id=")
            if i < 0:
                continue
            j = i + 3
            if seg[j] == '"':
                out.append(seg[j + 1:seg.index('"', j + 1)])
            elif seg[j] == "{":
                depth = 0
                for k in range(j, len(seg)):
                    if seg[k] == "{":
                        depth += 1
                    elif seg[k] == "}":
                        depth -= 1
                        if depth == 0:
                            out.append(seg[j + 1:k])
                            break
        return out

    @staticmethod
    def _refs(expr: str) -> set[str]:
        """表达式里真正被读取的变量：模板字面量只取 ${…} 里的部分。"""
        holes = re.findall(r"\$\{([^{}]*)\}", expr)
        body = " ".join(holes) if holes else expr
        return {n for n in re.findall(r"[A-Za-z_$][\w$]*", body)}

    def test_every_template_svg_def_is_unique_per_instance(self):
        """凡是 <filter/clipPath/mask id=…>，id 必须追溯到 useSvgId（不能是业务 id）。

        例外只有一处：`cinema.tsx` 的方向模糊滤镜是全片唯一的两个常量（进 / 出各一枚，
        由 index.tsx 的 `url(#nv-whip-in|out)` 引用），只挂在合成层，不随镜头重复。
        """
        singleton = {"nv-whip-in", "nv-whip-out"}
        offenders = []
        for p in SRC.rglob("*.tsx"):
            if p.name == "uid.ts":
                continue
            text = p.read_text(encoding="utf-8")
            for expr in self._def_id_exprs(text):
                if expr.strip("`\"' ") in singleton:
                    continue
                ok = False
                for name in self._refs(expr):
                    if name == "svgUid":
                        ok = True
                        break
                    decl = re.search(rf"const\s+{re.escape(name)}\s*=\s*`([^`]*)`", text)
                    if decl and "svgUid" in decl.group(1):
                        ok = True
                        break
                if not ok:
                    offenders.append(f"{p.name}: id={{{expr}}}")
        self.assertEqual(offenders, [], "这些 SVG def id 没带实例前缀，跨镜同时挂载会互相覆盖：\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
