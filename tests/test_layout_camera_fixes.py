#!/usr/bin/env python3
"""排版与运镜的几处一致性契约：代码行估宽、行高单位、门禁读真实相机路径、重新居中的边界、ms→帧取整、招牌镜。"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


layout = load("layout_fix", SCRIPTS / "story_layout.py")


class P:
    def __init__(self):
        self.errors, self.fixes, self.hints = [], [], []

    def err(self, m): self.errors.append(m)
    def fix(self, m): self.fixes.append(m)
    def hint(self, m): self.hints.append(m)


class CodeWidth(unittest.TestCase):
    CODE = "v = cache.get(key)  # 先查缓存，命中就直接返回，否则回源到数据库再写回缓存\nreturn v"

    def test_cjk_comment_fits_codeline_or_errors(self):
        p = P()
        els = layout.lay_code(p, "S1", {"code": self.CODE, "lang": "python"}, None)
        lines = [e for e in els if e["kind"] == "codeline"]
        worst = max(layout.text_w(e["text"].expandtabs(4), e["size"], mono=True) - e["w"] for e in lines)
        self.assertTrue(worst <= 0 or p.errors, f"代码行按等宽估超出行宽 {worst:.0f}px 却没报错")

    def test_lh_is_ratio(self):
        p = P()
        els = layout.lay_code(p, "S1", {"code": "x = 1\ny = 2", "note": "说明"}, None)
        for e in els:
            if "lh" in e:
                self.assertLess(e["lh"], 3, f"{e['id']}: lh={e['lh']} 应是行高倍数，不是像素")


if __name__ == "__main__":
    unittest.main()


class MsToFrame(unittest.TestCase):
    """Python 侧所有 ms→帧换算与渲染端 index.tsx 的 Math.round(ms*FPS/1000) 一致（.5 向上）。"""
    MS = list(range(0, 6000, 50)) + [150, 350, 16.7, 1016.65]

    def test_half_rounds_up_like_js(self):
        st = load("st_fix", SCRIPTS / "story_time.py")
        self.assertEqual(st.frame(150), 5)
        self.assertEqual(st.frame(350), 11)

    def test_resolve_and_presentation_share_story_time(self):
        st = load("st_fix2", SCRIPTS / "story_time.py")
        rs = load("rs_fix", SCRIPTS / "resolve-shots.py")
        vp = load("vp_fix", SCRIPTS / "validate-presentation.py")
        for ms in self.MS:
            self.assertEqual(rs.ms_frame(ms), st.frame(ms), ms)
            self.assertEqual(vp.ms_frame(ms), st.frame(ms), ms)

    def test_matches_node_math_round(self):
        import shutil
        if not shutil.which("node"):
            self.skipTest("no node")
        st = load("st_fix3", SCRIPTS / "story_time.py")
        js = subprocess.run(["node", "-e", f"console.log(JSON.stringify({json.dumps(self.MS)}.map(ms=>Math.round(ms*{st.FPS}/1000))))"],
                            capture_output=True, text=True, check=True).stdout
        self.assertEqual(json.loads(js), [st.frame(ms) for ms in self.MS])


def compose_example(rel: str, td: str, skin: str | None = None, treatment: bool = False) -> Path:
    """模板副本里跑 compose-story + resolve-shots，返回工程目录。"""
    import shutil
    story = ROOT / "examples" / rel
    proj = Path(td) / story.stem
    shutil.copytree(ROOT / "assets" / "lecture-template", proj, ignore=shutil.ignore_patterns("node_modules", "renders"))
    if skin:
        subprocess.run([sys.executable, str(SCRIPTS / "set-skin.py"), str(proj), skin], check=True, capture_output=True)
    tr = story.with_name(story.name.replace(".story.json", ".treatment.json"))
    if treatment and tr.exists():
        shutil.copy(tr, proj / "manifests" / "treatment.json")
    for step in (["compose-story.py", str(story), str(proj)], ["resolve-shots.py", str(proj)]):
        r = subprocess.run([sys.executable, str(SCRIPTS / step[0]), *step[1:]], capture_output=True, text=True, timeout=300)
        assert r.returncode == 0, r.stdout + r.stderr
    return proj


def story_ts(proj: Path) -> dict:
    m = re.search(r"export const STORY[^=]*=\s*(\{.*\});", (proj / "src" / "story.ts").read_text(encoding="utf-8"), re.S)
    return json.loads(m.group(1))


class Recenter(unittest.TestCase):
    def test_compare_flow_keep_own_position(self):
        import tempfile
        src = json.loads((ROOT / "examples" / "concept-hash-table.story.json").read_text(encoding="utf-8"))
        shots = [sh for ch in src["chapters"] for sh in ch["shots"]]
        with tempfile.TemporaryDirectory() as td:
            got = story_ts(compose_example("concept-hash-table.story.json", td))
            for i, lay in ((2, "flow"), (4, "compare")):
                own = {e["id"]: e["y"] for e in layout.LAY[lay](P(), f"S{i + 1}", json.loads(json.dumps(shots[i]["content"])), None)}
                out = {e["id"]: e["y"] for e in got[f"S{i + 1}"]["elements"]}
                for k, y in own.items():
                    self.assertAlmostEqual(out[k], round(y, 1), delta=0.11, msg=f"{lay} S{i + 1}.{k} 被重新居中挪动了")


def gate(proj: Path, script: str) -> list[dict]:
    import os
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        jl = f.name
    subprocess.run([sys.executable, str(SCRIPTS / script), str(proj)], capture_output=True, text=True, timeout=300,
                   env={**os.environ, "NV_GATE_JSON": jl})
    recs = [json.loads(x) for x in Path(jl).read_text(encoding="utf-8").splitlines() if x.strip()]
    Path(jl).unlink()
    return recs


class GateReadsRealPath(unittest.TestCase):
    """auto 路线的运镜全在 cinema.path：门禁按 path 查，镜头表的 intent 由 path 读出，keys 不再带装饰运镜。"""

    def setUp(self):
        self.vsm = load("vsm_fix", SCRIPTS / "validate-shot-motion.py")

    def shot(self, path, keys=None, intent="push-in"):
        return {"id": "S1", "from": 0, "to": 100, "duration": 100, "anchor": {"x": 600, "y": 400, "w": 700, "h": 300},
                "camera": {"intent": intent}, "cameraIntent": intent, "hero": {"kind": "text"},
                "keys": keys or [{"f": 0, "x": 960, "y": 540, "s": 1.0}, {"f": 100, "x": 960, "y": 540, "s": 1.0}],
                "cinema": {"path": path}}

    def test_path_monotonic_and_zoom_checked(self):
        back = self.shot([{"at": 0, "x": 960, "y": 540, "s": 1.0}, {"at": 40, "x": 960, "y": 540, "s": 1.1},
                          {"at": 40, "x": 960, "y": 540, "s": 1.12}])
        p0, _ = self.vsm.check([back], 100)
        self.assertTrue(any("单调" in x["issue"] for x in p0), p0)
        deep = self.shot([{"at": 0, "x": 960, "y": 540, "s": 1.0}, {"at": 40, "x": 960, "y": 540, "s": 1.5}])
        p0, _ = self.vsm.check([deep], 100)
        self.assertTrue(any("缩放" in x["issue"] for x in p0), p0)

    def test_examples_intent_matches_path_and_keys_flat(self):
        import tempfile
        cs = load("cs_fix", SCRIPTS / "compose-story.py")
        with tempfile.TemporaryDirectory() as td:
            proj = compose_example("concept-hash-table.story.json", td)
            res = json.loads((proj / "manifests" / "shots.resolved.json").read_text(encoding="utf-8"))
        for s in res["shots"]:
            path = s["cinema"]["path"]
            self.assertEqual(s["cameraIntent"], cs.path_intent(path), s["id"])
            self.assertTrue(all(abs(k["s"] - 1.0) < 1e-9 for k in s["keys"]), f"{s['id']}: path 镜的 keys 应恒为 1.0")

    def test_still_camera_prints_no_push_fixes(self):
        import tempfile
        story = json.loads((ROOT / "examples" / "concept-hash-table.story.json").read_text(encoding="utf-8"))
        story["camera"] = "still"
        with tempfile.TemporaryDirectory() as td:
            import shutil
            proj = Path(td) / "p"
            shutil.copytree(ROOT / "assets" / "lecture-template", proj, ignore=shutil.ignore_patterns("node_modules", "renders"))
            (proj / "manifests" / "treatment.json").write_text(json.dumps({"signature_shot": "S3：推近", "shots": []}), encoding="utf-8")
            sp = Path(td) / "still.story.json"
            sp.write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")
            out = subprocess.run([sys.executable, str(SCRIPTS / "compose-story.py"), str(sp), str(proj)], capture_output=True, text=True).stdout
            subprocess.run([sys.executable, str(SCRIPTS / "resolve-shots.py"), str(proj)], capture_output=True, check=True)
            recs = gate(proj, "validate-shot-motion.py")
        fixes = [l for l in out.splitlines() if "自动修" in l and re.search(r"招牌镜|慢推|推近|推到", l)]
        self.assertEqual(fixes, [], "camera:still 却打印了推近类自动修")
        self.assertFalse([r for r in recs if "几乎不动" in r.get("message", "")], "camera:still 却收到「声明运镜却不动」提示")


class SignatureDeadlock(unittest.TestCase):
    def test_jie_hybrid_handmade_no_signature_p0(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            proj = compose_example("recipes/jie-hybrid.story.json", td, skin="journal", treatment=True)
            recs = gate(proj, "validate-treatment.py") + gate(proj, "validate-shot-motion.py")
            t = json.loads((proj / "manifests" / "treatment.json").read_text(encoding="utf-8"))
        self.assertEqual([r["message"] for r in recs if r["level"] == "P0"], [])
        self.assertRegex(str(t["signature_shot"]), r"^S\d", "招牌镜必须落在镜头表里的某一镜")
