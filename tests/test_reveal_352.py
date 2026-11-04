"""3.5.2 出现时序回归锁（T-P0-02 / T-P0-03 / T-P0-04 / T-P0-05）。

在 v3.5.1（4fca099）上：test_annotation_after_target、test_finish_before_cut、
test_recipe_camera_gate、test_template_growth_no_crash、test_no_old_wording 应当失败；
3.5.2 完成后全部通过。只用标准库，不渲染，单机约 1 秒。
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
RECIPES = ("annotated", "data-with-object", "list-icons", "rocket-fusion")
SINGLE = ("annotated", "data-with-object", "list-icons")
CUT_MARGIN = 4      # 镜尾留 4 帧：转场开始前所有东西必须长完
ANN_AFTER = 2       # 标注在被标注元素长完 +2 帧后才开始


def _run(args, **kw):
    return subprocess.run([PY, *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=ROOT, **kw)


def _mr():
    spec = importlib.util.spec_from_file_location("mr", ROOT / "scripts" / "measure-reveal.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RevealTiming(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.proj, cls.compose = {}, {}
        for name in RECIPES:
            out = Path(cls.tmp.name) / name
            cls.compose[name] = _run([ROOT / "scripts" / "compose-story.py",
                                      ROOT / "examples" / "recipes" / f"{name}.story.json", out])
            cls.proj[name] = out
        cls.mr = _mr()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _shots(self, name):
        story = self.mr.load_story(self.proj[name]) or {}
        table = json.loads((self.proj[name] / "manifests" / "shots.json").read_text(encoding="utf-8"))
        length = {s["id"]: int(s["to"]) - int(s["from"]) for s in table["shots"]}
        return story, length

    def test_compose_ok(self):
        for name in RECIPES:
            self.assertEqual(self.compose[name].returncode, 0, f"{name}: {self.compose[name].stdout[-400:]}")

    def test_annotation_after_target(self):
        """圈 / 下划线不能早于它标的那一行：at ≥ 目标 at + 目标 dur + 2。"""
        for name in RECIPES:
            story, _ = self._shots(name)
            for sid, sh in story.items():
                els = sh.get("elements") or []
                for a in sh.get("annotate") or []:
                    tgt = next((e for e in els if e.get("x") == a.get("x") and e.get("y") == a.get("y")), None)
                    if tgt is None:
                        continue
                    need = int(tgt["at"]) + int(tgt.get("dur") or 0) + ANN_AFTER
                    self.assertGreaterEqual(a["at"], need,
                                            f"{name} {sid}: {a['kind']} 在第 {a['at']} 帧开始，"
                                            f"它标的 {tgt['id']} 第 {need - ANN_AFTER} 帧才长完")

    def test_finish_before_cut(self):
        """每样东西都要在切镜前 4 帧长完，观众才看得到完整的它。"""
        for name in RECIPES:
            story, length = self._shots(name)
            for sid, sh in story.items():
                for kind, at, dur in self.mr.events_of(sh):
                    self.assertLessEqual(at + dur, length[sid] - CUT_MARGIN,
                                         f"{name} {sid}: {kind} 第 {at}–{at + dur} 帧在长，"
                                         f"可本镜只有 {length[sid]} 帧")

    def test_recipe_camera_gate(self):
        """3 个配方样例在不放宽门禁的前提下通过运镜门禁（扩成 ≥4 镜）。"""
        for name in SINGLE:
            r = _run([ROOT / "scripts" / "resolve-shots.py", self.proj[name]])
            self.assertEqual(r.returncode, 0, f"{name} resolve-shots: {r.stdout[-300:]}{r.stderr[-300:]}")
            r = _run([ROOT / "scripts" / "validate-shot-motion.py", self.proj[name]])
            self.assertEqual(r.returncode, 0, f"{name}: {r.stdout[-400:]}")


class MeasureRevealHandwritten(unittest.TestCase):
    def test_template_growth_no_crash(self):
        """手写场景工程（只有 shots.resolved.json 带 from/to）：不崩、退出码 0。"""
        r = _run([ROOT / "scripts" / "measure-reveal.py", ROOT / "assets" / "lecture-template",
                  ROOT / "does-not-exist.mp4"])
        self.assertEqual(r.returncode, 0, r.stderr[-600:])
        self.assertNotIn("Traceback", r.stderr)


class OldWording(unittest.TestCase):
    PATTERNS = [r"easeOut \+ 上浮", r"一个框淡入", r"帧淡入）", r"每个淡入都配"]

    def test_no_old_wording(self):
        hits = []
        for md in (ROOT / "references").glob("*.md"):
            text = md.read_text(encoding="utf-8")
            for pat in self.PATTERNS:
                for m in re.finditer(pat, text):
                    line = text.count("\n", 0, m.start()) + 1
                    hits.append(f"{md.relative_to(ROOT).as_posix()}:{line} {pat}")
        self.assertEqual(hits, [], "旧出现口径残留：\n" + "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
