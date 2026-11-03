#!/usr/bin/env python3
"""P2-24 第五切片 · 写盘层的边界契约。

这一层的变化原因是「产物格式」，所以测试不重复 compose-golden 的"整份输出一字不差"，
而是锁四件拆分时容易坏、坏了又不容易发现的事：

  1. **量的是当前朗读速度，不是快照**：`break_rule` 要写"这份字幕按几字每秒排的"。
     若输出层 `from story_caption import CPS`，`--cps 6` 之后产物里仍写 4.5——
     CLI 看着生效，字幕时长也对，只有 manifest 在骗人；
  2. **不许覆盖真实词级时间**：有 `audio/narration.meta.json` 时，
     `audio/narration.mp3.json` 是真 TTS 写的，compose 覆盖它 = 字幕与音频脱同步；
  3. **未注册的定制组件在写盘前拦**，而且"不是完整工程"时只提示、不假装查过；
  4. **单一真源**：这些函数只能定义在 `story_output.py`，主文件只做门面。
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
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


out = load("output_contract", SCRIPTS / "story_output.py")
cs = load("cs_output_contract", SCRIPTS / "compose-story.py")
cap = sys.modules["story_caption"]


class Collector:
    def __init__(self):
        self.errors, self.fixes, self.hints = [], [], []

    def err(self, m): self.errors.append(m)
    def fix(self, m): self.fixes.append(m)
    def hint(self, m): self.hints.append(m)


STORY = {"title": "测试片", "chapters": [{"title": "第一章", "shots": [{"id": "S1", "content": {}}]}]}
COMP = {
    "cues": [{"text": "一句话。", "words": [{"w": "一句话", "start_ms": 0, "end_ms": 400},
                                        {"w": "。", "start_ms": 400, "end_ms": 600}],
              "start_ms": 0, "end_ms": 1200, "speech_end_ms": 1200}],
    "protected": ["哈希"],
    "chapter_first": [0],
}
OUT_SHOTS = [{"id": "S1", "layout": "statement"}]
STORY_TS = {"S1": {"layout": "statement", "content": {"title": "标题"}}}


def write(proj: Path, p=None):
    out.write_project(STORY, COMP, OUT_SHOTS, STORY_TS, 36, proj, p)


class FacadeTest(unittest.TestCase):
    NAMES = ("js", "registered_customs", "check_customs", "write_narration_contract",
             "write_project", "write_media")

    def test_entrypoint_uses_output_layer(self):
        for name in self.NAMES:
            self.assertTrue(hasattr(cs, name), f"主文件缺门面 {name}")
            self.assertEqual(getattr(cs, name).__module__, "story_output",
                             f"{name} 不是 story_output 的实现（写盘逻辑又回主文件了）")
            self.assertIs(getattr(cs, name), getattr(sys.modules["story_output"], name))


class BreakRuleTest(unittest.TestCase):
    """`break_rule` 必须量当前 cps —— 这是唯一会变的输入。"""

    def tearDown(self):
        cap.set_cps(4.5)

    def _break_rule(self, cps: float) -> str:
        cap.set_cps(cps)
        with tempfile.TemporaryDirectory() as td:
            write(Path(td))
            doc = json.loads((Path(td) / "manifests" / "caption-cues.json").read_text(encoding="utf-8"))
        return doc["break_rule"]

    def test_break_rule_reflects_current_cps(self):
        for cps in (4.5, 6.0):
            rule = self._break_rule(cps)
            self.assertIn(str(cps), rule, f"break_rule 没跟着 --cps {cps} 变：{rule}")
            self.assertIn("compose-story", rule)

    def test_two_runs_differ(self):
        # 同一个进程里连跑两次：如果哪一层缓存了旧值，这两次会一样。
        self.assertNotEqual(self._break_rule(4.5), self._break_rule(6.0))


class TtsPreservationTest(unittest.TestCase):
    def test_real_word_times_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td)
            (proj / "audio").mkdir(parents=True)
            (proj / "audio" / "narration.meta.json").write_text('{"text_sha256":"abc"}', encoding="utf-8")
            write(proj)
            self.assertFalse((proj / "audio" / "narration.mp3.json").exists(),
                             "有 TTS meta 时仍覆盖了真实词级时间 —— 字幕会与音频脱同步")

    def test_without_tts_we_do_write_word_times(self):
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td)
            write(proj)
            f = proj / "audio" / "narration.mp3.json"
            self.assertTrue(f.is_file(), "没有 TTS 时必须写出估算词时间，否则字幕没有词级锚点")
            words = json.loads(f.read_text(encoding="utf-8"))
            self.assertEqual([w["w"] for w in words], ["一句话", "。"])


class StaleNarrationHintTest(unittest.TestCase):
    def test_hash_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td)
            (proj / "audio").mkdir(parents=True)
            (proj / "audio" / "narration.meta.json").write_text('{"text_sha256":"old"}', encoding="utf-8")
            p = Collector()
            write(proj, p)
            self.assertTrue(any("上一版" in h for h in p.hints),
                            f"旁白指纹不一致时必须提示重跑 tts，实际 hints={p.hints}")


class CustomsTest(unittest.TestCase):
    def _project(self, root: Path, registry: str | None) -> Path:
        (root / "src" / "custom").mkdir(parents=True, exist_ok=True)
        if registry is not None:
            (root / "src" / "index.tsx").write_text("export const X = 1;\n", encoding="utf-8")
            (root / "src" / "custom" / "index.ts").write_text(registry, encoding="utf-8")
        return root

    def test_reads_only_the_custom_table_keys(self):
        src = """import RequestLane from './RequestLane';

// 注释里的 Foo 不算
export const CUSTOM: Record<string, React.FC<CustomProps>> = {
  RequestLane,
  ShopCard: ShopCard,
};
"""
        with tempfile.TemporaryDirectory() as td:
            proj = self._project(Path(td), src)
            self.assertEqual(out.registered_customs(proj), {"RequestLane", "ShopCard"})

    def test_missing_registry_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(out.registered_customs(Path(td)), set())

    def test_unregistered_component_is_an_error(self):
        with tempfile.TemporaryDirectory() as td:
            proj = self._project(Path(td), "export const CUSTOM = {\n  RequestLane,\n};\n")
            p = Collector()
            out.check_customs(p, proj, {"S2": {"custom": "ShopCard"}})
            self.assertTrue(p.errors, "引用未注册组件却没报错")
            msg = p.errors[0]
            self.assertIn("ShopCard", msg)
            self.assertIn("S2", msg)
            # 路径随平台分隔符变，只断言"指向注册文件"这件事，不比字符串。
            self.assertIn("index.ts", msg)
            self.assertIn("CUSTOM", msg)

    def test_registered_component_passes(self):
        with tempfile.TemporaryDirectory() as td:
            proj = self._project(Path(td), "export const CUSTOM = {\n  ShopCard,\n};\n")
            p = Collector()
            out.check_customs(p, proj, {"S2": {"custom": "ShopCard"}})
            self.assertFalse(p.errors)

    def test_incomplete_project_only_hints(self):
        # compose 常被用来往空目录干跑（负向夹具 / 只算帧数）。那里没有注册表可核对，
        # 不能报错（会误杀），但也不能静默——要留一条提示。
        with tempfile.TemporaryDirectory() as td:
            p = Collector()
            out.check_customs(p, Path(td), {"S2": {"custom": "ShopCard"}})
            self.assertFalse(p.errors, "空目录干跑不该被判成未注册")
            self.assertTrue(p.hints, "空目录干跑也要提示「这台机器没法核对」")


class SingleSourceTest(unittest.TestCase):
    CHAIN = ("compose-story.py", "story_output.py")

    def test_output_functions_defined_once(self):
        hits = []
        for name in self.CHAIN:
            for i, line in enumerate((SCRIPTS / name).read_text(encoding="utf-8").splitlines(), 1):
                if re.match(r"^def (js|registered_customs|check_customs|write_narration_contract"
                            r"|write_project|write_media)\b", line):
                    hits.append(f"{name}:{i}")
        self.assertEqual(len(hits), 6, f"写盘函数应各定义一次，实际 {hits}")
        for h in hits:
            self.assertTrue(h.startswith("story_output.py:"), f"写盘函数定义回主文件了：{h}")

    def test_output_layer_has_no_reverse_import(self):
        src = (SCRIPTS / "story_output.py").read_text(encoding="utf-8")
        for ln in src.splitlines():
            if re.match(r"\s*(import|from)\s+", ln):
                self.assertNotIn("compose", ln, f"story_output 反向依赖主文件：{ln.strip()}")


class PackageIncludesModuleTest(unittest.TestCase):
    def test_package_collects_output_layer(self):
        pk = load("pkg_output_contract", SCRIPTS / "package-skill.py")
        files = {p.relative_to(ROOT).as_posix() for p in pk.collect_files()}
        self.assertIn("scripts/story_output.py", files)


if __name__ == "__main__":
    unittest.main()
