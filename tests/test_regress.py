"""回归集：examples/ 下全部 story（≥10 份）走 compose → resolve → 两道构建期门禁，产物逐字节钉住。

不渲染。每份 story 在模板副本里跑 compose-story.py 与 resolve-shots.py，记下产物的 sha256，
再跑 validate-shot-motion / validate-presentation（统一结果 NV_GATE_JSON）记下 P0/P1 条数。
与 tests/fixtures/regress.json 比对：

- 只改结构、行为不变 → 必须原样通过；
- 有意改了排版 / 字幕 / 相机 / 门禁判据 → `NV_REGRESS_UPDATE=1 python3 -m unittest tests/test_regress.py`
  重写快照，并在提交说明里写清哪些 story 变了、为什么。

单份 story 的逐字段快照见 test_compose_golden.py（concept-hash-table）；这里管覆盖面。
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "assets" / "lecture-template"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "regress.json"
ARTIFACTS = ("narration.txt", "src/shots.ts", "src/story.ts", "src/film.ts", "src/scenes.tsx",
             "manifests/shots.json", "manifests/shots.resolved.json", "manifests/caption-cues.json",
             "manifests/protected-caption-phrases.txt")
GATES = ("validate-shot-motion.py", "validate-presentation.py")


def stories():
    return sorted(ROOT.glob("examples/**/*.story.json"))


def run_one(story: Path, td: str) -> dict:
    proj = Path(td) / story.stem
    shutil.copytree(TPL, proj, ignore=shutil.ignore_patterns("node_modules", "renders"))
    env = {**os.environ, "PYTHONHASHSEED": "random", "PYTHONIOENCODING": "utf-8"}
    out = {}
    for step in (["compose-story.py", str(story), str(proj)], ["resolve-shots.py", str(proj)]):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / step[0]), *step[1:]], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", env=env, timeout=110)
        if r.returncode:
            return {"error": f"{step[0]} rc={r.returncode}: {(r.stdout + r.stderr).strip().splitlines()[-1:]}"}
    for rel in ARTIFACTS:
        f = proj / rel
        out[rel] = hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else None
    for g in GATES:
        jl = Path(td) / f"{story.stem}-{g}.jsonl"
        subprocess.run([sys.executable, str(ROOT / "scripts" / g), str(proj)], capture_output=True,
                       env={**env, "NV_GATE_JSON": str(jl)}, timeout=110)
        recs = [json.loads(x) for x in jl.read_text(encoding="utf-8").splitlines()] if jl.exists() else []
        out[g] = {lv: sum(1 for r in recs if r["level"] == lv) for lv in ("P0", "P1")}
    return out


class RegressSet(unittest.TestCase):
    def test_examples_compose_unchanged(self):
        items = stories()
        self.assertGreaterEqual(len(items), 10, "回归集至少 10 份 story")
        got = {}
        with tempfile.TemporaryDirectory(prefix="nv-regress-") as td:
            for s in items:
                got[s.relative_to(ROOT).as_posix()] = run_one(s, td)
        if os.environ.get("NV_REGRESS_UPDATE") == "1":
            FIXTURE.write_text(json.dumps(got, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
            self.skipTest(f"已重写 {FIXTURE.name}（{len(got)} 份）")
        want = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(sorted(want), sorted(got), "examples/ 里的 story 增删了：更新快照")
        for name in want:
            for key in sorted(set(want[name]) | set(got[name])):
                self.assertEqual(want[name].get(key), got[name].get(key), f"{name} · {key} 变了")


if __name__ == "__main__":
    unittest.main()
