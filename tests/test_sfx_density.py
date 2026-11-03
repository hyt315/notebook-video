#!/usr/bin/env python3
"""3.3.0 sfxDensity: 缺省 sparse（每镜一记），normal 保留 3.3.0 的「一拍一个」。

为什么改缺省：旁白由使用者自行后配（任意 TTS 或真人），技能不知道以后有没有人声，
按 24 条/分钟铺满会跟说话抢注意力。音效是标点，不是配乐。
"""
from __future__ import annotations

import importlib.util
import json
import re
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
        # 3.8.0 瘦身后转场不再叠 riser / whoosh：换章只有 chapter，翻页只有 page
        self.assertNotIn("'riser'", src)
        self.assertNotIn("'whoosh'", src)
        self.assertIn("if (isChapter) out.push({event: 'chapter', at: 2});", src)

    def test_normal_branch_unchanged(self):
        """normal 必须还是 3.3.0 的逐拍循环——老工程写 normal 后结果不变。"""
        src = SFX_TS.read_text(encoding="utf-8")
        self.assertIn("s.beats.forEach((b, i) => {", src)


class PageTurnFoleyTest(unittest.TestCase):
    """3.9.0：翻页是**动作**，不是标点——所以每次翻页都要有纸声，sparse 也不能削。

    之前 sparse 下非章节镜的转场完全无声：画面里一张纸翻过去，观众读到的是「转场特效」，
    不是「翻了一页」。翻页改成缺省之后，这个缺口会出现在每一部片子的每一次换页上。
    """

    def test_page_turn_always_has_paper_sound(self):
        src = SFX_TS.read_text(encoding="utf-8")
        # P2-23：翻页判定改读 transitions/meta.ts 的 isPageTurnKind（注册表是唯一真源）
        self.assertIn(
            "if (!isFirst && isPageTurnKind(s.transition ?? 'auto')) out.push({event: 'page', at: PAGE_HIT});",
            src)
        self.assertIn("import {isPageTurnKind} from './transitions/meta';", src)
        # 不该再有第二个翻页 Set——新增翻页类型时漏改的症状是「画面翻了页、听不见纸」
        self.assertNotIn("PAGE_TURN_TRANSITIONS", src)

    def test_foley_is_not_deduplicated_as_punctuation(self):
        """换章那一镜 chapter 先占位，page 若按标点互斥就会被 MIN_GAP 丢掉。"""
        src = SFX_TS.read_text(encoding="utf-8")
        self.assertIn("const FOLEY = new Set<SfxEvent>(['page']);", src)
        # 集合必须是模块级：planSfx 每镜都跑，在函数里 new Set 是白做的功
        self.assertIn("if (!FOLEY.has(r.event) && kept.some((k) => !FOLEY.has(k.event)", src)


class VocabularyTest(unittest.TestCase):
    """3.8.0 瘦身：16 → 9。事件表、库文件、manifest 三处必须同一套名字。

    删掉的七种不是「不好听」，是「用不上」或「重复」：whoosh 被 page 取代，
    click / rustle 与 highlight 重叠且只在 normal 出现，typing 只服务代码镜，
    riser 只在 normal 出现且是库里唯一被 earshot 判 no match 的，snip / latch 只属 papercut。
    """

    KEEP = ['pop', 'success', 'error', 'chart', 'highlight', 'chapter', 'page', 'place', 'stamp']

    def test_event_list_is_the_slimmed_nine(self):
        src = SFX_TS.read_text(encoding="utf-8")
        m = re.search(r"export const SFX_EVENTS = \[([^\]]*)\] as const;", src)
        self.assertIsNotNone(m, "SFX_EVENTS 不见了")
        self.assertEqual(re.findall(r"'([a-z]+)'", m.group(1)), self.KEEP)

    def test_library_has_exactly_these_files(self):
        lib = TPL / "public" / "sfx" / "lib"
        files = {p.stem for p in lib.glob("*.ogg")} - {"bed"}
        # 变体（P2-20 翻页轮换）不算事件，但是库里的合法文件
        man = json.loads((TPL / "public" / "sfx" / "sfx-manifest.json").read_text(encoding="utf-8"))
        variants = set()
        for e in man["events"]:
            for v in e.get("variants") or []:
                variants.add(Path(v["file"]).stem)
        self.assertEqual(files - variants, set(self.KEEP), "库文件和事件表对不上（有孤儿文件或缺点）")
        self.assertTrue(variants <= files, f"manifest 声明的变体缺文件：{variants - files}")

    def test_manifest_matches_event_list(self):
        doc = json.loads((TPL / "public" / "sfx" / "sfx-manifest.json").read_text(encoding="utf-8"))
        names = [e["event"] for e in doc["events"] if e["event"] != "bed"]
        self.assertEqual(sorted(names), sorted(self.KEEP))



class EarshotAuditBoundaryTest(unittest.TestCase):
    """P1-35：earshot 是维护者离线质检，不是运行时依赖。

    缺 earshot 时这条工具必须**优雅跳过**（exit 0 + 说明），不能报错挡住出片——
    普通用户渲染一支视频不该被要求装 1.1GB 模型。
    """

    def test_missing_earshot_skips_cleanly(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "dev" / "sfx-earshot-audit.py")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT,
                           env={**__import__("os").environ, "PATH": ""})  # 清 PATH 保证找不到 earshot
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("不需要", r.stdout, "要说清渲染不需要它")
        self.assertIn("skipped", r.stdout, "要说清是跳过不是失败")

    def test_document_states_the_boundary(self):
        doc = (ROOT / "references" / "sfx-library.md").read_text(encoding="utf-8")
        self.assertIn("维护者离线质检", doc)
        self.assertIn("1.1GB", doc)


if __name__ == "__main__":
    unittest.main()
