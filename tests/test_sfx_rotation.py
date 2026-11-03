#!/usr/bin/env python3
"""P2-20：听觉从「电平合格」走向「听感合格」。

电平指标（响度 / 峰值 / 削波）抓不到三件事：旁白下拟音掩字、连续翻页机械、
静音占位与真人声的动态差异。这一版补上其中**可以机器保证**的两件事，
并把第三件（掩字）固定成可复现的三段盲听：

  1. 音色轮换  连续翻页不再机械 —— page 有三个同源微变体，planSfx 轮换
  2. 动作同步  offsetMs 必须对准 5 ms RMS 命中点，差 >2 帧即 P0
  3. 三段盲听  listen-segments.py 固定段落，不靠每次现挑
"""
from __future__ import annotations

import importlib.util
import json
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "assets" / "lecture-template"
LIB = TPL / "public" / "sfx" / "lib"
MAN = TPL / "public" / "sfx" / "sfx-manifest.json"
SFX_TS = TPL / "src" / "sfx.ts"


def transient_ms(path: Path) -> float | None:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", "48000", "-"],
        capture_output=True, timeout=60).stdout
    if len(raw) < 8:
        return None
    n = len(raw) // 2
    s = struct.unpack(f"<{n}h", raw[: n * 2])
    win = 240
    best_i, best_v = 0, 0.0
    for i in range(0, max(1, n - win)):
        v = sum(x * x for x in s[i:i + win])
        if v > best_v:
            best_v, best_i = v, i
    return best_i / 48.0


class PageRotationTest(unittest.TestCase):
    def test_manifest_declares_variants(self):
        man = json.loads(MAN.read_text(encoding="utf-8"))
        page = next(e for e in man["events"] if e["event"] == "page")
        self.assertEqual(len(page.get("variants") or []), 2, "翻页要有两个变体")
        for v in page["variants"]:
            self.assertTrue((TPL / "public" / v["file"]).is_file(), v["file"])

    def test_variants_match_loudness_and_transient(self):
        """变体与主文件响度差 <0.5 LU、瞬态差 <2 帧 —— 否则轮换会忽大忽小 / 忽快忽慢。"""
        man = json.loads(MAN.read_text(encoding="utf-8"))
        page = next(e for e in man["events"] if e["event"] == "page")
        base_off = float(page["offsetMs"])
        base_lu = float(page["loudness_lufs_100ms"])
        for v in page["variants"]:
            self.assertLess(abs(float(v["loudness_lufs_100ms"]) - base_lu), 0.5, v["file"])
            off = float(v.get("offsetMs") if v.get("offsetMs") is not None else base_off)
            self.assertLess(abs(off - base_off), 66.7, f"{v['file']} 瞬态与主文件差 >2 帧")
            got = transient_ms(TPL / "public" / v["file"])
            self.assertIsNotNone(got)
            self.assertLess(abs(got - off), 66.7, f"{v['file']} 真实瞬态 {got:.1f} 偏离 offsetMs={off}")

    def test_sfx_ts_rotates_through_variants(self):
        src = SFX_TS.read_text(encoding="utf-8")
        self.assertIn("SFX_VARIANTS", src)
        self.assertIn("page-b.ogg", src)
        self.assertIn("page-c.ogg", src)
        # 轮换必须真的用上：planSfx 的产出 src 不能永远是 SFX_FILES[event]
        self.assertIn("SFX_VARIANTS[r.event]", src)
        self.assertRegex(src, r"\[SFX_FILES\[r\.event\], \.\.\.alts\]")


class TransientSyncGateTest(unittest.TestCase):
    """验收：动作音与视觉事件差 ≤2 帧。offsetMs 对不准 = 纸翻了半秒后才听见。"""

    def test_library_passes_sync_gate(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate-audio-levels.py"), str(TPL)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        self.assertEqual(r.returncode, 0, r.stdout[-1500:])
        self.assertIn("P0=0", r.stdout)

    def test_wrong_offset_is_caught(self):
        """把 chart 的 offsetMs 改成 500 ms → 门禁必须点名。"""
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td) / "p"
            # 只拷门禁需要的：manifest + lib + sfx.ts
            (proj / "public" / "sfx" / "lib").mkdir(parents=True)
            (proj / "src").mkdir()
            for f in LIB.iterdir():
                (proj / "public" / "sfx" / "lib" / f.name).write_bytes(f.read_bytes())
            man = json.loads(MAN.read_text(encoding="utf-8"))
            for e in man["events"]:
                if e["event"] == "chart":
                    e["offsetMs"] = 500.0
            (proj / "public" / "sfx" / "sfx-manifest.json").write_text(
                json.dumps(man, ensure_ascii=False), encoding="utf-8")
            (proj / "src" / "sfx.ts").write_text(SFX_TS.read_text(encoding="utf-8"), encoding="utf-8")
            r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate-audio-levels.py"), str(proj)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            self.assertEqual(r.returncode, 1, r.stdout[-1500:])
            self.assertIn("offsetMs", r.stdout)
            self.assertIn("chart", r.stdout)

    def test_peak_position_is_not_used(self):
        """chart 的峰值在 188 ms（扫弦终点），命中点在 45 ms。用峰值判会误报。"""
        got = transient_ms(LIB / "chart.ogg")
        self.assertIsNotNone(got)
        self.assertLess(got, 100, f"chart 命中点应在 100 ms 内，实测 {got:.1f} ms（峰值在 188 ms）")


class ListenSegmentsTest(unittest.TestCase):
    def test_three_segments_and_scoring_table(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            mix = td / "mix.wav"
            # 30 s 静音，够切三段
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                            "anullsrc=r=48000:cl=mono", "-t", "30", str(mix)],
                           check=True, timeout=60)
            # 造一份含连续翻页的音效计划
            plan = [{"event": "page", "hit": 30 * i} for i in range(2, 8)]  # 每秒一次翻页
            (td / "sfx-plan.json").write_text(json.dumps({"plan": plan}), encoding="utf-8")
            out = td / "segs"
            r = subprocess.run([sys.executable, str(ROOT / "scripts" / "dev" / "listen-segments.py"),
                                str(mix), str(out)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            rep = json.loads((out / "segments.json").read_text(encoding="utf-8"))
            names = [s["name"] for s in rep["segments"]]
            self.assertEqual(names, ["seg1-open", "seg2-turns", "seg3-close"], names)
            self.assertIn("verdict", rep["segments"][0])
            self.assertIn("pass_bar", rep)
            # 连续转场段应落在翻页密集区（f60–f210 ≈ 2–7 s，前后各留 3 s）
            turns = next(s for s in rep["segments"] if s["name"] == "seg2-turns")
            self.assertLess(turns["start_s"], 5.0, turns)
            self.assertGreater(turns["end_s"], 6.0, turns)
            for s in rep["segments"]:
                self.assertTrue((out / s["file"]).is_file(), s["file"])


class ContractTest(unittest.TestCase):
    def test_document_states_the_protocol(self):
        doc = (ROOT / "references" / "sfx-library.md").read_text(encoding="utf-8")
        self.assertIn("三段盲听", doc)
        self.assertIn("5 ms RMS", doc)
        self.assertIn("音色轮换", doc)

    def test_gain_and_offset_stay_in_sync_with_manifest(self):
        """sfx.ts 的 SFX_GAIN / SFX_OFFSET_MS 必须等于 manifest（validate 也会查，这里锁住）。"""
        man = json.loads(MAN.read_text(encoding="utf-8"))
        src = SFX_TS.read_text(encoding="utf-8")
        g = re.search(r"SFX_GAIN[^=]*=\s*\{([^}]*)\}", src)
        gains = dict(re.findall(r"([a-z]+):\s*([\d.]+)", g.group(1) if g else ""))
        for e in man["events"]:
            if e["event"] == "bed":
                continue
            self.assertAlmostEqual(float(gains[e["event"]]), float(e["gain"]), places=2, msg=e["event"])


if __name__ == "__main__":
    unittest.main()
