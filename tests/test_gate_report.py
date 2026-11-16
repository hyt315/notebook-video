"""门禁统一结果（scripts/gate_report.py）：每条 P0 / P1 一行同形状 JSON。

make-video.mjs 只读这一种格式把 P1 写进 report.md、把全部记录写进 renders/gates.json，
所以这里钉两件事：① 形状与拆分规则；② 终端里每一条 P0 / P1 明细都有一条对应记录
（数目一致 = 不会再有「只在终端滚过去、报告里没有」的建议）。
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "assets" / "lecture-template"
spec = importlib.util.spec_from_file_location("gate_report", ROOT / "scripts" / "gate_report.py")
gr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gr)

KEYS = {"gate", "id", "level", "file", "message", "fix"}
HUMAN = re.compile(r"^\s*(?:[✗·]\s*)?(P[01])\s", re.M)


def run_gate(args, cwd=ROOT):
    with tempfile.TemporaryDirectory(prefix="nv-gj-") as td:
        out_path = os.path.join(td, "g.jsonl")
        env = {**os.environ, "NV_GATE_JSON": out_path, "PYTHONIOENCODING": "utf-8"}
        r = subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=str(cwd), env=env, timeout=110)
        recs = []
        if os.path.exists(out_path):
            recs = [json.loads(line) for line in open(out_path, encoding="utf-8") if line.strip()]
        return r.returncode, r.stdout + r.stderr, recs


class RecordShape(unittest.TestCase):
    def test_dict_item_keeps_id(self):
        r = gr.record("validate-presentation.py", "P1", {"id": "S3", "issue": "好几件事挤在一拍上"}, 1, "f.json")
        self.assertEqual(r, {"gate": "validate-presentation", "id": "S3", "level": "P1", "file": "f.json",
                             "message": "好几件事挤在一拍上", "fix": ""})

    def test_tagged_string_and_fix_split(self):
        r = gr.record("validate-fusion", "P1", "S2: 线稿画了内部 —— 线稿只画外形", 4)
        self.assertEqual((r["id"], r["message"], r["fix"]), ("S2", "线稿画了内部", "线稿只画外形"))

    def test_plain_string_gets_numbered_id(self):
        r = gr.record("validate-backgrounds", "P1", "分镜相邻两镜同一张背景（--shots）", 2)
        self.assertEqual((r["id"], r["message"], r["fix"]), ("validate-backgrounds-P1-2", "分镜相邻两镜同一张背景（--shots）", ""))

    def test_number_or_chinese_lead_is_not_an_id(self):
        self.assertEqual(gr.record("g", "P1", "13–15（低于标注 16 档）", 1)["message"], "13–15（低于标注 16 档）")
        self.assertEqual(gr.record("g", "P1", "配乐：关", 1)["message"], "配乐：关")

    def test_no_env_writes_nothing(self):
        env = dict(os.environ)
        env.pop("NV_GATE_JSON", None)
        with tempfile.TemporaryDirectory() as td:
            code = "import sys; sys.path.insert(0, r'%s'); import gate_report; gate_report.emit('g', ['x'], ['y'])" % (ROOT / "scripts")
            subprocess.run([sys.executable, "-c", code], cwd=td, env=env, check=True)
            self.assertEqual(os.listdir(td), [])


class EveryHumanLineHasARecord(unittest.TestCase):
    """模板工程上逐个门禁：终端 P0 / P1 明细数 == JSON 记录数，且形状一致。"""

    GATES = [
        ["validate-shot-motion.py"], ["validate-presentation.py"], ["validate-glyphs.py"],
        ["validate-elem-kinds.py"], ["validate-fusion.py"], ["validate-audio-levels.py"],
        ["validate-media.py"], ["validate-treatment.py"], ["validate-opening.py"],
        ["validate-backgrounds.py"], ["validate-backgrounds.py", "--shots"], ["validate-composition.py"],
    ]

    def check(self, rc, out, recs, label):
        self.assertTrue(all(KEYS <= set(r) for r in recs), label)
        for lv in ("P0", "P1"):
            human = sum(1 for m in HUMAN.finditer(out) if m.group(1) == lv)
            self.assertEqual(human, sum(1 for r in recs if r["level"] == lv), f"{label} {lv}\n{out[-600:]}")
        self.assertEqual(rc != 0, any(r["level"] == "P0" for r in recs), label)

    def test_template_gates(self):
        seen = 0
        for g in self.GATES:
            rc, out, recs = run_gate([str(ROOT / "scripts" / g[0]), str(TPL), *g[1:]])
            self.check(rc, out, recs, " ".join(g))
            seen += len(recs)
        self.assertGreater(seen, 0, "模板上应有若干 P1，用来证明记录真的写出来了")

    def test_p0_record_on_blocking_gate(self):
        with tempfile.TemporaryDirectory(prefix="nv-gj-") as td:
            (Path(td) / "src" / "theme").mkdir(parents=True)
            (Path(td) / "src" / "theme" / "active.ts").write_text("export {theme} from './journal';\n", encoding="utf-8")
            rc, out, recs = run_gate([str(ROOT / "scripts" / "validate-treatment.py"), td])
        self.check(rc, out, recs, "treatment journal 缺 treatment.json")
        self.assertEqual(recs[0]["file"], "manifests/treatment.json")
        self.assertTrue(recs[0]["fix"].startswith("复制"))


class FinishTest(unittest.TestCase):
    """gate_report.finish：P0 / P1 型门禁共用的收尾（打印格式、退出码、--json、--strict）。"""

    def finish(self, *a, **k):
        import contextlib
        import io
        sys.path.insert(0, str(ROOT / "scripts"))
        import gate_report
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = gate_report.finish(*a, **k)
        return rc, buf.getvalue()

    def test_text_output_and_exit_codes(self):
        rc, out = self.finish("g", [{"id": "S1", "issue": "坏"}], ["提示"], header="g · 头", notes=["注"])
        self.assertEqual(rc, 1)
        self.assertEqual(out, "g · 头\n  P0 S1: 坏\n  P1 提示\n  ·· 注\n结论：P0=1 P1=1 → FAIL\n")
        rc, out = self.finish("g", [], ["x"], marks=("  ✗ P0 ", "  · P1 "), suffix="（尾）")
        self.assertEqual((rc, out), (0, "  · P1 x\n结论：P0=0 P1=1 → PASS（尾）\n"))

    def test_strict_and_json(self):
        rc, out = self.finish("g", [], ["x"], strict=True)
        self.assertEqual(rc, 1)
        self.assertTrue(out.endswith("→ FAIL\n"))
        rc, out = self.finish("g", [], ["x"], payload={"p1": ["x"]}, indent=1, strict=True)
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out), {"p1": ["x"]})


if __name__ == "__main__":
    unittest.main()
