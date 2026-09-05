#!/usr/bin/env python3
"""notebook-video 技能回归自测（改动引擎/模板/QA 脚本后必跑）。

用法：python scripts/selftest.py

- 好夹具（必须全绿）：技能关键产物齐全；官方 validate-skill 全量通过。
- 负向夹具（每个门必须真拦，退出码非 0）：
  1. validate-semantic-breaks：受保护短语被 cue 边界切开；
  2. validate-caption-sync：cue 文本与其词级时间戳对不上；
  3. validate-video：非媒体输入。
全部通过退出 0，任一项失败退出 1。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node") or shutil.which("node.exe")
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL"), name, detail[:90])


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=cwd or ROOT, capture_output=True, text=True)


def expect_blocked(name: str, args: list[str], cwd: Path | None = None) -> None:
    proc = run(*args, cwd=cwd)
    combined = f"{proc.stdout}{proc.stderr}".lower()
    blocked = proc.returncode != 0 and ("error" in combined or "unknown" in combined
                                        or "failure" in combined or "not found" in combined
                                        or "missing" in combined or "invalid" in combined)
    check(name, blocked, f"rc={proc.returncode} (blocked as expected)" if blocked else f"rc={proc.returncode} (unexpectedly allowed)")


def main() -> int:
    if not NODE:
        check("node 可用", False, "node 未安装，无法回归")
    else:
        check("node 可用", True, NODE)

    # ---- 好夹具 1：关键产物齐全 ----
    files = [
        "SKILL.md", "CHANGELOG.md",
        "scripts/notebook-video.mjs",
        "scripts/validate-caption-sync.py",
        "scripts/validate-semantic-breaks.py",
        "scripts/validate-layering.py",
        "scripts/validate-visual-plan.py",
        "scripts/validate-video.cmd",
        "assets/lecture-template/src/index.tsx",
        "assets/lecture-template/src/theme/active.ts",
        "assets/lecture-template/src/theme/canvas.ts",
        "assets/lecture-template/src/theme/types.ts",
        "assets/lecture-template/src/theme/paper.tsx",
        "assets/lecture-template/src/theme/cel.tsx",
        "assets/lecture-template/src/theme/sticker.tsx",
        "assets/lecture-template/src/theme/flat.tsx",
        "assets/lecture-template/scripts/tts-openai-compatible.py",
        "assets/lecture-template/manifests/asset-manifest.json",
        "assets/lecture-template/manifests/caption-cues.json",
        "references/lecture-composition.md",
        "references/visual-system.md",
        "references/canvas-modes.md",
        "references/theme-system.md",
        "references/theme-cel.md",
        "references/theme-sticker.md",
        "references/theme-flat.md",
    ]
    missing = [f for f in files if not (ROOT / f).is_file()]
    check("关键产物齐全", not missing, f"missing: {missing}" if missing else f"{len(files)} files")

    # ---- 好夹具 2：主题开关默认 paper（出厂状态） ----
    active = ROOT / "assets" / "lecture-template" / "src" / "theme" / "active.ts"
    if active.is_file():
        ok = "from './paper'" in active.read_text(encoding="utf-8")
        check("主题开关默认 paper", ok, "default" if ok else "active.ts 被改到非默认主题")
    else:
        check("主题开关默认 paper", False, "active.ts 缺失")

    # ---- 负向夹具：--style 非法值被拦 ----
    if NODE:
        with tempfile.TemporaryDirectory() as td:
            expect_blocked("负向：非法 --style 被拦", [
                str(NODE), str(ROOT / "scripts" / "notebook-video.mjs"),
                "new-project", str(Path(td) / "proj"), "--style=neon"])
            leftover = Path(td) / "proj"
            if leftover.exists() and any(leftover.iterdir()):
                check("负向：非法 --style 不产生半成品", False, "目标目录被污染")
            else:
                check("负向：非法 --style 不产生半成品", True, "clean")

    # ---- 好夹具 2：官方引擎自检 ----
    if NODE:
        proc = run(str(NODE), str(ROOT / "scripts" / "notebook-video.mjs"), "validate-skill")
        check("validate-skill 通过", proc.returncode == 0, "passed" if proc.returncode == 0 else "failed")

    # ---- 负向夹具 ----
    if NODE:
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)

            # 1. 语义断行门：受保护短语被拆到两条 cue
            bad_cues = td / "bad-cues.json"
            bad_protected = td / "protected.txt"
            bad_protected.write_text("github.com/hyt315\n", encoding="utf-8")
            bad_cues.write_text(json.dumps({
                "segmentation": "semantic",
                "cues": [
                    {"index": 1, "start_ms": 0, "speech_end_ms": 1000, "text": "主页搜 github.com/"},
                    {"index": 2, "start_ms": 1000, "speech_end_ms": 2000, "text": "hyt315，现在出发"},
                ],
            }, ensure_ascii=False), encoding="utf-8")
            expect_blocked("负向：保护短语跨 cue 被拦", [
                str(NODE), str(ROOT / "scripts" / "notebook-video.mjs"),
                "validate-semantic-breaks", str(bad_cues), str(bad_protected)])

            # 2. 字幕同步门：cue 文本与词级时间戳不一致
            words = [{"part": "你", "start": 0, "end": 100},
                     {"part": "好", "start": 100, "end": 200}]
            tts_json = td / "words.json"
            tts_json.write_text(json.dumps(words), encoding="utf-8")
            sync_cues = td / "sync-cues.json"
            sync_cues.write_text(json.dumps({
                "segmentation": "semantic",
                "cues": [
                    {"index": 1, "start_ms": 0, "speech_end_ms": 200,
                     "text": "不好",
                     "words": [{"part": "不", "start": 0, "end": 100},
                               {"part": "好", "start": 100, "end": 200}]},
                ],
            }, ensure_ascii=False), encoding="utf-8")
            expect_blocked("负向：字幕同步失败被拦", [
                str(NODE), str(ROOT / "scripts" / "notebook-video.mjs"),
                "validate-caption-sync", str(tts_json), str(sync_cues)])

            # 3. 视频门：非媒体输入
            expect_blocked("负向：非视频输入被拦", [
                str(NODE), str(ROOT / "scripts" / "notebook-video.mjs"),
                "validate-video", str(__file__), "30"])

    failed = [r for r in results if not r[1]]
    if not failed:
        print(f"SELFTEST PASS (all {len(results)} checks passed)")
        return 0
    print(f"\n共 {len(results)} 项，通过 {len(results) - len(failed)}，失败 {len(failed)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
