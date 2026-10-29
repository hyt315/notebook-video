#!/usr/bin/env python3
"""3.7.0 sfxDensity: 缺省 sparse（每镜一记），normal 保留 3.6.0 的「一拍一个」。

为什么改缺省：旁白由使用者自行后配（任意 TTS 或真人），技能不知道以后有没有人声，
按 24 条/分钟铺满会跟说话抢注意力。音效是标点，不是配乐。
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "assets" / "lecture-template"
SFX_TS = TPL / "src" / "sfx.ts"
INDEX_TSX = TPL / "src" / "index.tsx"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


rs = load("rs_sfxdensity", ROOT / "scripts" / "resolve-shots.py")


def project(mutate=None) -> Path:
    d = Path(tempfile.mkdtemp(prefix="nv-sfxdensity-"))
    (d / "manifests").mkdir()
    (d / "src").mkdir()
    shutil.copy(TPL / "manifests" / "caption-cues.json", d / "manifests" / "caption-cues.json")
    doc = json.loads((TPL / "manifests" / "shots.json").read_text(encoding="utf-8"))
    if mutate:
        mutate(doc)
    (d / "manifests" / "shots.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return d


class ResolveTest(unittest.TestCase):
    def test_default_is_sparse(self):
        ts, _, problems = rs.resolve(project())
        self.assertEqual(problems, [])
        self.assertIn("export const SFX_DENSITY = 'sparse' as const;", ts)

    def test_normal_is_kept(self):
        ts, _, problems = rs.resolve(project(lambda d: d.update(sfxDensity="normal")))
        self.assertEqual(problems, [])
        self.assertIn("export const SFX_DENSITY = 'normal' as const;", ts)

    def test_invalid_value_is_reported(self):
        _, _, problems = rs.resolve(project(lambda d: d.update(sfxDensity="loud")))
        self.assertTrue(any("sfxDensity" in p for p in problems), problems)

    def test_resolved_json_carries_density(self):
        """CLI 跑完整流程（写盘）后，resolved 里要带 sfxDensity——validate/文档都读它。"""
        d = project()
        subprocess.run([sys.executable, str(ROOT / "scripts" / "resolve-shots.py"), str(d)],
                       check=True, capture_output=True)
        doc = json.loads((d / "manifests" / "shots.resolved.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["sfxDensity"], "sparse")


class EngineWiringTest(unittest.TestCase):
    """规则在 TS 里，Python 测试只能核对「接线」和「分支形状」；行为验证靠 make-video 出片。"""

    def test_index_passes_density_into_plan(self):
        src = INDEX_TSX.read_text(encoding="utf-8")
        self.assertIn("SFX_DENSITY", src)
        self.assertIn("DURATION,SFX_DENSITY)", src)

    def test_sparse_branch_keeps_only_last_beat(self):
        src = SFX_TS.read_text(encoding="utf-8")
        self.assertIn("export type SfxDensity = 'sparse' | 'normal';", src)
        self.assertIn("export const SFX_DENSITY_DEFAULT: SfxDensity = 'sparse';", src)
        # sparse 分支：换章的镜只留章节声，其余镜末拍一记 + 误区镜的第 2 拍
        self.assertIn("if (isChapter || !n) return out;", src)
        self.assertIn("s.beats[n - 1]", src)
        self.assertIn("s.misconception && n >= 3", src)
        # 转场音在 sparse 下只剩 chapter（riser / whoosh 只在 normal 出现）
        self.assertIn("if (!isFirst && !sparse) out.push({event: 'riser', at: 2});", src)
        self.assertIn("} else if (!isFirst && !sparse) {", src)

    def test_normal_branch_unchanged(self):
        """normal 必须还是 3.6.0 的逐拍循环——老工程写 normal 后结果不变。"""
        src = SFX_TS.read_text(encoding="utf-8")
        self.assertIn("s.beats.forEach((b, i) => {", src)


if __name__ == "__main__":
    unittest.main()
