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

import ast
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
        "scripts/resolve-shots.py",
        "scripts/validate-shot-motion.py",
        "scripts/validate-composition.py",
        "scripts/validate-visual-plan.py",
        "scripts/validate-presentation.py",
        "references/presentation-gate.md",
        "scripts/coords-lint.py",
        "scripts/retime.py",
        "scripts/audition.py",
        "scripts/validate-video.cmd",
        "assets/lecture-template/src/index.tsx",
        "assets/lecture-template/src/fxkit.tsx",
        "assets/lecture-template/src/kit.tsx",
        "assets/lecture-template/src/shotkit.tsx",
        "assets/lecture-template/src/stagekit.tsx",
        "assets/lecture-template/src/skeletons.tsx",
        "assets/lecture-template/src/media.tsx",
        "assets/lecture-template/src/insert.tsx",
        "assets/lecture-template/src/showcase.tsx",
        "assets/lecture-template/src/theme/active.ts",
        "assets/lecture-template/src/theme/canvas.ts",
        "assets/lecture-template/src/theme/types.ts",
        "assets/lecture-template/src/theme/cel.tsx",
        "assets/lecture-template/src/theme/flat.tsx",
        "assets/lecture-template/src/theme/craft-common.tsx",
        "assets/lecture-template/src/theme/journal.tsx",
        "assets/lecture-template/src/theme/papercut.tsx",
        "assets/lecture-template/src/theme/archive.tsx",
        "assets/lecture-template/src/fonts.tsx",
        "assets/lecture-template/public/bg/bg-flat-main.jpg",
        "assets/lecture-template/public/bg/bg-flat-chapter.jpg",
        "assets/lecture-template/public/bg/bg-flat-quiet.jpg",
        "assets/lecture-template/public/bg/bg-cel-main.jpg",
        "assets/lecture-template/public/bg/bg-cel-chapter.jpg",
        "assets/lecture-template/public/bg/bg-cel-quiet.jpg",
        "assets/lecture-template/public/bg/bg-journal-main.jpg",
        "assets/lecture-template/public/bg/bg-journal-chapter.jpg",
        "assets/lecture-template/public/bg/bg-journal-quiet.jpg",
        "assets/lecture-template/public/bg/bg-papercut-main.jpg",
        "assets/lecture-template/public/bg/bg-papercut-chapter.jpg",
        "assets/lecture-template/public/bg/bg-papercut-quiet.jpg",
        "assets/lecture-template/public/bg/bg-archive-main.jpg",
        "assets/lecture-template/public/bg/bg-archive-chapter.jpg",
        "assets/lecture-template/public/bg/bg-archive-quiet.jpg",
        "assets/lecture-template/manifests/visual-assets.json",
        "assets/lecture-template/scripts/tts-openai-compatible.py",
        "assets/lecture-template/manifests/asset-manifest.json",
        "assets/lecture-template/manifests/caption-cues.json",
        "references/lecture-composition.md",
        "references/fxkit.md",
        "references/shot-language.md",
        "references/scene-skeletons.md",
        "references/media-routing.md",
        "references/composition-gate.md",
        "references/canvas-modes.md",
        "references/theme-system.md",
        "references/theme-cel.md",
        "references/theme-flat.md",
        "references/theme-journal.md",
        "references/theme-papercut.md",
        "references/theme-archive.md",
        "references/director-method.md",
        "references/craft-kit.md",
        "references/style-recipes.md",
        "references/commons-media.md",
    ]
    missing = [f for f in files if not (ROOT / f).is_file()]
    check("关键产物齐全", not missing, f"missing: {missing}" if missing else f"{len(files)} files")

    # ---- 好夹具 1b：脚本 AST 静态语法解析门禁 ----
    ast_errors = []
    for py_script in (ROOT / "scripts").glob("*.py"):
        try:
            ast.parse(py_script.read_text(encoding="utf-8"), filename=str(py_script))
        except SyntaxError as exc:
            ast_errors.append(f"{py_script.name}: Syntax error: {exc}")
    check("脚本 AST 语法解析", not ast_errors, f"errors: {ast_errors}" if ast_errors else "all scripts/*.py valid syntax")

    # ---- 好夹具 2：主题开关默认 flat（出厂状态，3.2.0 起） ----
    active = ROOT / "assets" / "lecture-template" / "src" / "theme" / "active.ts"
    if active.is_file():
        ok = "from './flat'" in active.read_text(encoding="utf-8")
        check("主题开关默认 flat", ok, "default" if ok else "active.ts 被改到非默认主题")
    else:
        check("主题开关默认 flat", False, "active.ts 缺失")

    # ---- 好夹具 3：密钥防呆（被追踪文件里不许出现疑似 API Key）----
    import re as _re
    _keypat = _re.compile(r"sk-[A-Za-z0-9]{16,}")
    try:
        _tracked = subprocess.run(["git", "ls-files"], cwd=ROOT,
                                  capture_output=True, text=True).stdout.splitlines()
    except Exception:
        _tracked = []
    if _tracked:
        _scan = [ROOT / p for p in _tracked if (ROOT / p).is_file() and (ROOT / p).name != "selftest.py"]
    else:
        _skip = {".git", "node_modules", "renders", ".cache", ".tools", "__pycache__"}
        _suffix = {".md", ".py", ".mjs", ".tsx", ".ts", ".json", ".txt", ".cmd", ".sh", ".cjs", ".yml", ".yaml"}
        _scan = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in _suffix
                 and not any(part in _skip for part in p.relative_to(ROOT).parts)
                 and p.name != "selftest.py"]
    _hits, _unreadable = [], []
    for _fp in _scan:
        try:
            _text = _fp.read_text(encoding="utf-8", errors="ignore")
        except OSError as _e:
            # 只吞「读不了这个文件」这一种情况；不吞解析/正则等其它异常，
            # 并且把跳过的文件记下来，让"漏扫"可见（宽捕获 + continue = 门静默放行）。
            _unreadable.append(f"{_fp.relative_to(ROOT)} ({_e.__class__.__name__})")
            continue
        if _keypat.search(_text):
            _hits.append(str(_fp.relative_to(ROOT)))
    if _unreadable:
        print("WARN 密钥防呆：以下文件未能读取，未参与扫描：" + ", ".join(_unreadable))
    check("密钥防呆", not _hits, f"leaks: {_hits}" if _hits else "no key-like tokens")

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

    # ---- 3.2.0 音效库：好夹具必须通过；篡改文件 / 增益越界必须被拦 ----
    if shutil.which("ffmpeg"):
        tpl = ROOT / "assets" / "lecture-template"
        good = run(sys.executable, str(ROOT / "scripts" / "validate-audio-levels.py"), str(tpl))
        check("音效库：模板通过 validate-audio-levels", good.returncode == 0, f"rc={good.returncode}")
        with tempfile.TemporaryDirectory() as td2:
            proj = Path(td2) / "p"
            (proj / "src").mkdir(parents=True)
            shutil.copytree(tpl / "public" / "sfx", proj / "public" / "sfx")
            shutil.copy(tpl / "src" / "sfx.ts", proj / "src" / "sfx.ts")
            with open(proj / "public" / "sfx" / "lib" / "pop.ogg", "ab") as fh:
                fh.write(b"x")
            r1 = run(sys.executable, str(ROOT / "scripts" / "validate-audio-levels.py"), str(proj))
            check("负向：音效文件被篡改（sha256）被拦", r1.returncode == 1 and "sha256" in r1.stdout, f"rc={r1.returncode}")
            shutil.copy(tpl / "public" / "sfx" / "lib" / "pop.ogg", proj / "public" / "sfx" / "lib" / "pop.ogg")
            ts = (proj / "src" / "sfx.ts").read_text(encoding="utf-8").replace("success: 0.459,", "success: 0.9,")
            if "success: 0.9," not in ts:
                raise SystemExit("selftest 夹具锚点没找到：src/sfx.ts 的 SFX_GAIN.success 写法变了（3.2.0 增益来自 manifest）")
            (proj / "src" / "sfx.ts").write_text(ts, encoding="utf-8")
            r2 = run(sys.executable, str(ROOT / "scripts" / "validate-audio-levels.py"), str(proj))
            check("负向：音效增益越界被拦", r2.returncode == 1 and "SFX_GAIN" in r2.stdout, f"rc={r2.returncode}")
    else:
        check("音效库门禁（需要 ffmpeg）", False, "ffmpeg 不在 PATH，无法回归音效库门禁")

    failed = [r for r in results if not r[1]]
    if not failed:
        print(f"SELFTEST PASS (all {len(results)} checks passed)")
        return 0
    print(f"\n共 {len(results)} 项，通过 {len(results) - len(failed)}，失败 {len(failed)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
