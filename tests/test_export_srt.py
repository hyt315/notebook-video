"""export-srt.py 的格式锁。

字幕导出看着"只要拼字符串"，但错了的后果很隐蔽：播放器不报错，只是**字幕整段错位**
或者两条叠在一起。这里锁四件事：编号从 1 连续、时间码格式合法、每条 end>start、
相邻两条不重叠。另外锁一条业务规则：`speech_end_ms` 是结束时间（不是 `reveal_end_ms`）。
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
SCRIPT = ROOT / "scripts" / "export-srt.py"


def run(cues: list[dict], *extra: str) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "cues.json"
        out = Path(td) / "out.srt"
        src.write_text(json.dumps({"cues": cues}, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), str(src), str(out), *extra],
            capture_output=True, text=True, encoding="utf-8",
        )
        body = out.read_text(encoding="utf-8") if out.is_file() else ""
        return proc.returncode, body, proc.stdout + proc.stderr


def parse(srt: str) -> list[tuple[int, str, str, str]]:
    blocks = [b for b in srt.strip().split("\n\n") if b.strip()]
    rows = []
    for block in blocks:
        lines = block.split("\n")
        index = int(lines[0])
        start, end = [x.strip() for x in lines[1].split("-->")]
        rows.append((index, start, end, "\n".join(lines[2:])))
    return rows


class ExportSrt(unittest.TestCase):
    def test_numbering_timing_and_no_overlap(self) -> None:
        cues = [
            {"text": "第一句。", "start_ms": 0, "speech_end_ms": 1200},
            {"text": "第二句，长一点。", "start_ms": 1200, "speech_end_ms": 3400},
            {"text": "第三句", "start_ms": 5000, "speech_end_ms": 6100},
        ]
        code, srt, log = run(cues)
        self.assertEqual(code, 0, log)
        rows = parse(srt)
        self.assertEqual([r[0] for r in rows], [1, 2, 3], "编号必须从 1 连续")
        for _, start, end, text in rows:
            self.assertRegex(start, r"^\d{2}:\d{2}:\d{2},\d{3}$")
            self.assertRegex(end, r"^\d{2}:\d{2}:\d{2},\d{3}$")
            self.assertTrue(text.strip(), "字幕文本不能为空")
        self.assertEqual(rows[0][1], "00:00:00,000")
        self.assertEqual(rows[1][2], "00:00:03,400", "结束时间取 speech_end_ms")
        # 严格递增：后一条的开始不早于前一条的结束
        for prev, nxt in zip(rows, rows[1:]):
            self.assertLessEqual(prev[2], nxt[1], "相邻两条不能重叠")

    def test_zero_length_cue_is_widened_not_dropped(self) -> None:
        # start == end 在 SRT 里是非法的（播放器会吞掉这条），必须补 1ms 而不是丢掉。
        code, srt, log = run([{"text": "嗯。", "start_ms": 800, "speech_end_ms": 800}])
        self.assertEqual(code, 0, log)
        rows = parse(srt)
        self.assertEqual(len(rows), 1, "不许把零长 cue 丢掉")
        self.assertEqual(rows[0][1], "00:00:00,800")
        self.assertEqual(rows[0][2], "00:00:00,801")

    def test_offset_cannot_go_negative(self) -> None:
        code, srt, log = run([{"text": "开头", "start_ms": 100, "speech_end_ms": 900}], "--offset-ms", "-500")
        self.assertEqual(code, 0, log)
        self.assertEqual(parse(srt)[0][1], "00:00:00,000", "负时间要夹到 0，不能出现 -00:00:00")

    def test_empty_input_fails_loudly(self) -> None:
        code, _, log = run([{"text": "   ", "start_ms": 0, "speech_end_ms": 500}])
        self.assertNotEqual(code, 0, "一句都没有时要报错，不能产出空文件")
        self.assertIn("no non-empty cue", log)


if __name__ == "__main__":
    unittest.main()
