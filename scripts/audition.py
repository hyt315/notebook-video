#!/usr/bin/env python3
"""TTS 试听条 + 多音字扫描（本地，零 API 调用，只用已合成的 seg 缓存）。

1. 试听条：把 audio/seg*.wav 每段取前 3 秒拼成 audition.mp3（约30秒），
   成片前先听 30 秒，读错在源头改 narration.txt，不返工。
2. 多音字扫描：内置高危表扫 narration.txt，命中报行号 + 替换建议。
   （TTS 没有拼音通道，错读只能在源头改写，见技能 tts-audio.md）

用法：python scripts/audition.py PROJECT_DIR
产物：PROJECT_DIR/audio/audition.mp3
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# 高危多音字：原文片段 -> 改写建议（全部生产验证过）
RISKY = [
    ("重装", "重新装", "重 chóng/zhòng，系统语境常被读错"),
    ("重命名", "重新命名", "重 chóng/zhòng"),
    ("输一行", "输入一条", "行 háng/xíng"),
    ("一行代码", "一条代码", "行 háng/xíng"),
    ("一模一样", "长得一样", "模 mú/mó"),
    ("钉在", "贴在", "钉 dìng/dīng"),
    ("朝阳", "向阳", "朝 cháo/zhāo（专有名词除外）"),
    ("行长", "银行行长", "行 háng/xíng（消歧义）"),
    ("数不清", "数不过来", "数 shǔ/shù"),
    ("角色", None, "角 jué/jiǎo： lamda 语境一般正确，抽听确认即可"),
    ("差", None, "差 chā/chà：’不差/分毫不差’一般正确，抽听确认即可"),
]


def scan(narration: Path) -> int:
    lines = narration.read_text(encoding="utf-8").splitlines()
    hits = 0
    for i, line in enumerate(lines, 1):
        for raw, fix, note in RISKY:
            if raw in line:
                hits += 1
                advice = f"建议改为含“{fix}”的说法" if fix else "抽听试听条确认"
                print(f"  L{i}: 命中“{raw}”（{note}），{advice}")
    if not hits:
        print("多音字扫描：干净")
    return hits


def audition(project: Path) -> int:
    audio = project / "audio"
    segs = sorted(audio.glob("seg*.wav"))
    if not segs:
        print("没有 seg 缓存，先跑 TTS 适配器")
        return 1
    cuts, lists = [], []
    for k, seg in enumerate(segs):
        cut = audio / f"_audit{k}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(seg),
                        "-t", "3", str(cut)], check=True)
        cuts.append(cut)
        lists.append(f"file '{cut.name}'")
    (audio / "_audit.txt").write_text("\n".join(lists) + "\n", encoding="utf-8")
    out = audio / "audition.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(audio / "_audit.txt"), "-ar", "48000", "-ac", "2",
                    "-b:a", "128k", str(out)], check=True)
    for cut in cuts:
        cut.unlink()
    (audio / "_audit.txt").unlink()
    dur = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(out)], text=True)
    print(f"试听条：{out}（{float(dur.strip()):.1f}s，{len(segs)} 段首句连播）")
    return 0


def main() -> int:
    project = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    print("--- 多音字扫描 ---")
    scan(project / "narration.txt")
    print("--- 试听条 ---")
    return audition(project)


if __name__ == "__main__":
    raise SystemExit(main())
