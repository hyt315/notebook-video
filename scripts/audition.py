#!/usr/bin/env python3
"""TTS 试听条 + 多音字扫描（本地，零 API 调用，只用已合成的 seg 缓存）。

1. 试听条：按 manifests/tts-segments.json 的当前顺序，每段取前 3 秒拼成 audition.mp3，
   成片前先听 30 秒，读错在源头改 narration.txt，不返工。
2. 多音字扫描：内置高危表扫 narration.txt，命中报行号 + 替换建议。
   （TTS 没有拼音通道，错读只能在源头改写，见技能 tts-audio.md）

用法：python scripts/audition.py PROJECT_DIR
产物：PROJECT_DIR/audio/audition.mp3
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "tts_audio", Path(__file__).resolve().parents[1] / "assets/lecture-template/scripts/tts-openai-compatible.py")
audio_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audio_helpers)

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
    paragraphs = [p.strip() for p in (project / "narration.txt").read_text(encoding="utf-8").splitlines() if p.strip()]
    segs = audio_helpers.active_segments(project, len(paragraphs), paragraphs)
    out = audio / "audition.mp3"
    with tempfile.TemporaryDirectory(prefix=".audition-", dir=audio) as tmp:
        tmp = Path(tmp)
        cuts = []
        for k, seg in enumerate(segs):
            cut = tmp / f"cut{k}.wav"
            audio_helpers.normalize_audio(seg, cut, "atrim=duration=3")
            cuts.append(cut)
        audio_helpers.join_pcm(cuts, tmp / "joined.wav")
        duration = audio_helpers.pcm_frames(tmp / "joined.wav") / audio_helpers.SAMPLE_RATE
        audio_helpers.encode_mp3(tmp / "joined.wav", tmp / "audition.mp3")
        os.replace(tmp / "audition.mp3", out)
    print(f"试听条：{out}（{duration:.1f}s，{len(segs)} 段首句连播）")
    return 0


def main() -> int:
    project = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    print("--- 多音字扫描 ---")
    scan(project / "narration.txt")
    print("--- 试听条 ---")
    return audition(project)


if __name__ == "__main__":
    raise SystemExit(main())
