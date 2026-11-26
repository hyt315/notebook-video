"""门禁口径：字幕行长一种数法、P0 只表示拦片、画面空的修法不与红线冲突、浏览器门禁进 gates.json、按需检查。"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TPL = ROOT / "assets" / "lecture-template"
SRC = TPL / "src"
sys.path.insert(0, str(SCRIPTS))

LONG_TAIL = "一二三四五六七八九十甲乙丙丁戊己。"      # 16 字 + 句末标点：不上屏的标点不算
TWO_LINES = "九个字九个字九个字\n九个字九个字九个字"  # 18 字：字幕只有一行，换行不上屏
MIXED = "GPT4o模型发布于2024年5月十三日下午"        # ASCII 也按 1 字计
TEXTS = (LONG_TAIL, TWO_LINES, MIXED)


def _words(text: str) -> list[dict]:
    chars = [ch for ch in text if not ch.isspace()]
    return [{"part": ch, "start": 100 + 60 * i, "end": 150 + 60 * i} for i, ch in enumerate(chars)]


def _caption_sync_flags(text: str) -> bool:
    with tempfile.TemporaryDirectory() as td:
        words = _words(text)
        cue = {"text": text, "start_ms": 100, "speech_end_ms": words[-1]["end"], "words": words}
        (Path(td) / "w.json").write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
        (Path(td) / "c.json").write_text(json.dumps({"segmentation": "semantic", "cues": [cue]}, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPTS / "validate-caption-sync.py"), f"{td}/w.json", f"{td}/c.json"],
                           capture_output=True, text=True, encoding="utf-8")
        return "characters >" in r.stdout + r.stderr


def _presentation_line_flags(text: str) -> bool:
    with tempfile.TemporaryDirectory() as td:
        proj = Path(td) / "p"
        shutil.copytree(TPL, proj, ignore=shutil.ignore_patterns("node_modules"))
        cc = json.loads((proj / "manifests" / "caption-cues.json").read_text(encoding="utf-8"))
        cc["cues"][0]["text"] = text
        (proj / "manifests" / "caption-cues.json").write_text(json.dumps(cc, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPTS / "validate-presentation.py"), str(proj)],
                           capture_output=True, text=True, encoding="utf-8")
        out = r.stdout + r.stderr
        return bool(re.search(r"cue1.*(加权字 > 16|超过 2 行|字 > 16)", out))


def _ts_caption_chars(texts) -> list[int]:
    src = (SRC / "index.tsx").read_text(encoding="utf-8")
    defs = [m.group(0) for name in ("cleanTail", "captionChars")
            for m in [re.search(rf"^const {name}=.*;$", src, re.M)] if m]
    js = "\n".join(re.sub(r"\(([a-z]):string\)", r"(\1)", d) for d in defs)
    js += f"\nconsole.log(JSON.stringify({json.dumps(list(texts), ensure_ascii=False)}.map(captionChars)));"
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout)


class CaptionLineCount(unittest.TestCase):
    """同一条字幕：每道门禁要么都拦、要么都不拦，而且只由一道构建期门禁报出。"""

    def test_one_python_counter(self):
        from story_text import cap_chars
        self.assertEqual([cap_chars(t) > 16 for t in TEXTS], [False, True, True])
        src = (SCRIPTS / "validate-caption-sync.py").read_text(encoding="utf-8")
        self.assertIn("cap_chars", src)
        self.assertNotIn("default=16", src, "上限读 contract.json 的 CAPTION_MAX_CHARS")

    def test_ts_counter_matches_python(self):
        from story_text import cap_chars
        self.assertEqual(_ts_caption_chars(TEXTS), [cap_chars(t) for t in TEXTS])

    def test_build_gates_agree_and_report_once(self):
        from story_text import cap_chars
        for t in TEXTS:
            over = cap_chars(t) > 16
            flags = [_caption_sync_flags(t), _presentation_line_flags(t)]
            self.assertEqual(sum(flags), 1 if over else 0, (t, flags))
            self.assertEqual(flags[0], over, t)


if __name__ == "__main__":
    unittest.main()


def _js_defs(path: Path, names) -> str:
    """从 .mjs 里按名字截出顶层 const 定义（到下一条顶层语句为止）。"""
    src = path.read_text(encoding="utf-8")
    out = []
    for name in names:
        m = re.search(rf"^const {name} = .*?(?=^[^\s}}\])])", src, re.M | re.S)
        if not m:
            raise AssertionError(f"{path.name} 里找不到 const {name}")
        out.append(m.group(0))
    return "\n".join(out)


def _node(js: str):
    r = subprocess.run(["node", "--input-type=module", "-e", js], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise AssertionError(r.stderr)
    return json.loads(r.stdout)


class P0MeansBlocking(unittest.TestCase):
    """P0 只有一个含义：拦片。本路径不拦的门禁，它的 P0 记成 P1。"""

    def test_record_level_equals_blocking(self):
        js = "const rep = {hints: []}; const records = [];\n" + _js_defs(SCRIPTS / "make-video.mjs", ["say", "record"])
        js += """
const a = record([{gate: 'validate-composition', level: 'P0', message: 'm', fix: ''}], false);
const b = record([{gate: 'validate-composition', level: 'P0', message: 'm', fix: ''}], true);
console.log(JSON.stringify({a, b, all: records, hints: rep.hints}));"""
        r = _node(js)
        self.assertEqual((r["a"][0]["level"], r["a"][0]["blocking"]), ("P1", False))
        self.assertEqual((r["b"][0]["level"], r["b"][0]["blocking"]), ("P0", True))
        self.assertTrue(all((x["level"] == "P0") == x["blocking"] for x in r["all"]))
        self.assertEqual(len(r["hints"]), 1, "降成 P1 的记录进报告建议")

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg not installed")
    def test_opening_frame0_blank_is_p0_and_o7_is_p1(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("vo", SCRIPTS / "validate-opening.py")
        vo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vo)
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td) / "p"
            shutil.copytree(TPL, proj, ignore=shutil.ignore_patterns("node_modules", "public"))
            (proj / "src" / "theme" / "active.ts").write_text("export {theme} from './journal';\n", encoding="utf-8")
            mp4 = Path(td) / "v.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=0xF2EADB:s=320x180:r=30", "-t", "4",
                            "-pix_fmt", "yuv420p", str(mp4)], check=True)
            r = vo.check(proj, mp4)
            self.assertEqual(r["skin"], "journal")
            self.assertTrue(any(x.startswith("O6 第 0 帧") for x in r["p0"]), r)
            self.assertTrue(any(x.startswith("O7") for x in r["p1"]), r["p1"])


class EmptyFrameFix(unittest.TestCase):
    """画面空：去掉死门 bottomFill；修法不许和红线「严禁改小 anchor」冲突。"""

    def test_bottomfill_is_not_a_gate(self):
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td) / "p"
            shutil.copytree(TPL, proj, ignore=shutil.ignore_patterns("node_modules", "public"))
            for name in ("shots.json", "shots.resolved.json"):
                p = proj / "manifests" / name
                doc = json.loads(p.read_text(encoding="utf-8"))
                for s in doc["shots"]:
                    s.pop("bottomFill", None)
                p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPTS / "validate-composition.py"), str(proj)],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertNotIn("bottomFill", r.stdout + r.stderr)
            self.assertEqual(r.returncode, 0, r.stdout[-600:])

    def test_fill_hints_obey_red_line(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("vsm", SCRIPTS / "validate-shot-motion.py")
        vsm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vsm)
        shots = [{"id": f"S{i}", "duration": 90, "layout": "flow", "cinema": {"fit": {"fillAfter": fa}}}
                 for i, fa in enumerate((0.30, 0.50, 0.95), 1)]
        p0, p1 = vsm.check_cinema(shots)
        msgs = [x["issue"] for x in p0 + p1]
        self.assertEqual(len(msgs), 3, msgs)
        for m in msgs:
            self.assertNotRegex(m, r"收紧|写得比内容大|画大", m)
        for m in msgs[:2]:
            self.assertIn("不改小 anchor", m)
        fill = (SRC / "fill-gate.tsx").read_text(encoding="utf-8")
        self.assertNotIn("P0-4", fill, "FillGate 只报警，不能自称 P0")


class BrowserGatesInGatesJson(unittest.TestCase):
    """浏览器门禁的结论进 renders/gates.json，与 checks.md 一致。"""

    LOG = "\n".join([
        "[Tab 0, src/stagekit.tsx:127] [SlotGuard] @150 「代码」main 槽占用 89%（16 块）",
        "[Tab 0, src/overlap-gate.tsx:244] [OverlapGate] @150 已测 27 个文字块，无重叠",
        "[Tab 0, src/clipping-gate.tsx:158] [ClippingGate] @150 图形要素扫过 2 个，无被裁",
        "[Tab 0, src/canvas-bounds-gate.tsx:146] [CanvasBoundsGate] @150 共 1 处文字越出画布（落定态 0 处）：标题 越出左缘 30px",
        "[Tab 0, src/canvas-bounds-gate.tsx:146] [CanvasBoundsGate] @151 共 1 处文字越出画布（落定态 0 处）：标题 越出左缘 28px",
        "FillGate: 2 shots (S2,S5) bottom-quarter underfilled",
    ])

    def run_js(self, out: str, failed: bool, full: bool):
        js = "const rep = {hints: []}; const records = []; const results = []; const saveGates = () => {};\n"
        js += _js_defs(SCRIPTS / "make-video.mjs", ["say", "record", "BROWSER_GATES", "BLOCK_SIGNS", "browserGates"])
        js += f"\nbrowserGates({json.dumps(out, ensure_ascii=False)}, {{failed: {str(failed).lower()}, full: {str(full).lower()}, file: 'x'}});"
        js += "\nconsole.log(JSON.stringify(records));"
        return _node(js)

    def test_warnings_and_coverage(self):
        recs = self.run_js(self.LOG, failed=False, full=True)
        by = {r["gate"]: r for r in recs}
        self.assertEqual(by["CanvasBoundsGate"]["level"], "P1")
        self.assertIn("2 条报警", by["CanvasBoundsGate"]["message"])
        self.assertIn("FillGate", by)
        self.assertNotIn("SlotGuard", by, "覆盖率读数不是报警")
        self.assertNotIn("OverlapGate", by)
        self.assertTrue(all(not r["blocking"] for r in recs))
        self.assertTrue(all({"gate", "id", "level", "file", "message", "fix", "blocking"} <= set(r) for r in recs))

    def test_missing_coverage_is_did_not_run(self):
        recs = self.run_js("[Tab 0, x] [OverlapGate] @150 已测 3 个文字块，无重叠", failed=False, full=True)
        miss = sorted(r["gate"] for r in recs if "did NOT run" in r["message"])
        self.assertEqual(miss, ["CanvasBoundsGate", "ClippingGate"])
        self.assertEqual(self.run_js("", failed=False, full=False), [], "静帧不判 did NOT run（抽到的帧不一定有覆盖率读数）")

    def test_block_is_p0(self):
        # Remotion 报错后会附一段源码摘录：摘录里的 `[CaptionFitGate]`、`new Error(` 字样不能当成报警或拦截
        log = "\n".join([
            " Error  Subtitle too long (>16 chars per line): #1 18字 一二三四五六七八九十甲乙丙丁戊己庚辛",
            "202 │ const CaptionFitGate=()=>{console.warn(`[CaptionFitGate] ${n}`);cancelRender(new Error('x'))}",
        ])
        recs = self.run_js(log, failed=True, full=True)
        self.assertEqual([(r["gate"], r["level"], r["blocking"]) for r in recs], [("CaptionFitGate", "P0", True)])
        recs = self.run_js(" Error  [OverlapGate] @45 文字互压：甲 × 乙", failed=True, full=False)
        self.assertEqual([(r["gate"], r["level"]) for r in recs], [("OverlapGate", "P0")])


class OnDemandChecks(unittest.TestCase):
    """CanvasBounds / SlotGuard：不再每帧对整棵 DOM 读样式、不再每帧打日志；判据不变。"""

    def test_canvas_bounds_reads_style_only_for_candidates(self):
        src = (SRC / "canvas-bounds-gate.tsx").read_text(encoding="utf-8")
        body = src[src.index("querySelectorAll<Element>(TEXT_SEL)"):src.index("issues.push(")]
        cut = body.index("if (overOf(box) <= TOL) return;")
        for expensive in ("getComputedStyle(", "effectiveOpacity(el)", "el.parentElement"):
            self.assertGreater(body.index(expensive), cut, f"{expensive} 应在越界候选筛出之后")
        for kept in ("TOL = 6", "BLOCK_PX = 20", "OPAQUE_FOR_SETTLED = 0.98", "REPORT_EVERY", "if (el.children.length) return;"):
            self.assertIn(kept, src)

    def test_slot_guard_uses_probe_and_reports_periodically(self):
        src = (SRC / "stagekit.tsx").read_text(encoding="utf-8")
        guard = src[src.index("const SlotGuard"):src.index("export const StageFrame")]
        self.assertIn("useLayoutProbe(", guard)
        self.assertNotIn("delayRender(", guard)
        self.assertRegex(guard, r"else if \(at % REPORT_EVERY === 0\)")
        self.assertIn("cover < 0.35", guard)
