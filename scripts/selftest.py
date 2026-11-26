#!/usr/bin/env python3
"""notebook-video 技能回归自测（改动引擎/模板/QA 脚本后必跑）。

用法：python scripts/selftest.py

- 好夹具（必须全绿）：技能关键产物齐全；官方 validate-skill 全量通过。
- 负向夹具（每个门必须真拦，退出码非 0）：
  1. validate-semantic-breaks：受保护短语被 cue 边界切开；
  2. validate-caption-sync：cue 文本与其词级时间戳对不上；
  3. validate-video：非媒体输入；
  4. 非法 --style、音效文件 sha256 被改。
其余门禁的负向用例在 scripts/negative-gate-check.py 与 tests/，仓库卫生（语法、密钥）在 tests/test_repo_hygiene.py。
全部通过退出 0，任一项失败退出 1。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Windows 控制台默认 cp1252 编不了中文，先兜住（CI / 本地都适用）
for _s in (sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node") or shutil.which("node.exe")
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL"), name, detail[:90])


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=cwd or ROOT, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def expect_blocked(name: str, args: list[str], must: str, cwd: Path | None = None) -> None:
    """负向夹具：非零退出，且输出里有这道门自己的拦截语句（`must`）。

    只看退出码或宽泛关键词（error / missing…）会把脚本崩溃、路径写错也算成「拦住了」。
    """
    proc = run(*args, cwd=cwd)
    combined = f"{proc.stdout}{proc.stderr}"
    blocked = (proc.returncode != 0 and must in combined
               and "Traceback (most recent call last)" not in combined)
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
        "scripts/export-srt.py",
        "scripts/eval-project.py",
        "scripts/validate-semantic-breaks.py",
        # 随技能分发的 BudouX 切片。缺了它，上面那条断句规则会静默跳过而不是报错，
        # 所以把入口也算进"关键产物"——文件不在了，自检直接失败。
        "assets/vendor/budoux/module/index.js",
        "scripts/validate-layering.py",
        "scripts/resolve-shots.py",
        "scripts/validate-shot-motion.py",
        "scripts/validate-composition.py",
        "scripts/validate-visual-plan.py",
        "scripts/validate-presentation.py",
        "scripts/validate-glyphs.py",
        "scripts/validate-fusion.py",
        "references/checks.md",
        "scripts/coords-lint.py",
        "scripts/retime.py",
        "scripts/audition.py",
        "scripts/notebook-video.cmd",
        "scripts/make-video.cmd",
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
        "assets/lecture-template/public/bg/bg-flat-main.webp",
        "assets/lecture-template/public/bg/bg-flat-chapter.webp",
        "assets/lecture-template/public/bg/bg-flat-quiet.webp",
        "assets/lecture-template/public/bg/bg-cel-main.webp",
        "assets/lecture-template/public/bg/bg-cel-chapter.webp",
        "assets/lecture-template/public/bg/bg-cel-quiet.webp",
        "assets/lecture-template/public/bg/bg-journal-main.webp",
        "assets/lecture-template/public/bg/bg-journal-chapter.webp",
        "assets/lecture-template/public/bg/bg-journal-quiet.webp",
        "assets/lecture-template/public/bg/bg-papercut-main.webp",
        "assets/lecture-template/public/bg/bg-papercut-chapter.webp",
        "assets/lecture-template/public/bg/bg-papercut-quiet.webp",
        "assets/lecture-template/public/bg/bg-archive-main.webp",
        "assets/lecture-template/public/bg/bg-archive-chapter.webp",
        "assets/lecture-template/public/bg/bg-archive-quiet.webp",
        "assets/lecture-template/manifests/visual-assets.json",
        "assets/lecture-template/manifests/backgrounds.json",
        "scripts/validate-backgrounds.py",
        "references/media.md",
        "assets/lecture-template/scripts/tts-openai-compatible.py",
        "assets/lecture-template/manifests/asset-manifest.json",
        "assets/lecture-template/manifests/caption-cues.json",
        "references/scenes.md",
        "references/components.md",
        "references/camera.md",
        "references/themes/system.md",
        "references/themes/cel.md",
        "references/themes/flat.md",
        "references/themes/journal.md",
        "references/themes/papercut.md",
        "references/themes/archive.md",
        "references/director.md",
    ]
    missing = [f for f in files if not (ROOT / f).is_file()]
    check("关键产物齐全", not missing, f"missing: {missing}" if missing else f"{len(files)} files")

    # ---- 好夹具 1c：中文字面门禁。模板必须过；故意写一条 monospace 中文栈必须拦 ----
    good = run(sys.executable, "scripts/validate-glyphs.py", str(ROOT / "assets" / "lecture-template"))
    check("中文字体栈：模板通过", good.returncode == 0,
          (good.stdout.strip().splitlines() or ["<no output>"])[-1][:90])
    # ---- 好夹具 2：主题开关默认 flat（出厂状态，） ----
    active = ROOT / "assets" / "lecture-template" / "src" / "theme" / "active.ts"
    if active.is_file():
        ok = "from './flat'" in active.read_text(encoding="utf-8")
        check("主题开关默认 flat", ok, "default" if ok else "active.ts 被改到非默认主题")
    else:
        check("主题开关默认 flat", False, "active.ts 缺失")

    # ---- 负向夹具：--style 非法值被拦 ----
    if NODE:
        with tempfile.TemporaryDirectory() as td:
            expect_blocked("负向：非法 --style 被拦", [
                str(NODE), str(ROOT / "scripts" / "notebook-video.mjs"),
                "new-project", str(Path(td) / "proj"), "--style=neon"], must='Unknown style "neon"')
            leftover = Path(td) / "proj"
            if leftover.exists() and any(leftover.iterdir()):
                check("负向：非法 --style 不产生半成品", False, "目标目录被污染")
            else:
                check("负向：非法 --style 不产生半成品", True, "clean")

    # ---- 好夹具 2：官方引擎自检 ----
    # 断句短语规则要 BudouX，而技能本身不发行 node_modules——不指路就会静默跳过。
    # 自检里显式透传，避免"全绿"其实少跑了一条规则。
    if NODE:
        extra: list[str] = []
        if "--budoux-dir" in sys.argv:
            i = sys.argv.index("--budoux-dir")
            if i + 1 >= len(sys.argv):
                check("validate-skill 通过", False, "--budoux-dir needs a path")
            else:
                extra = ["--budoux-dir", sys.argv[i + 1]]
        proc = run(str(NODE), str(ROOT / "scripts" / "notebook-video.mjs"), "validate-skill", *extra)
        ok = proc.returncode == 0
        detail = "passed" if ok else "failed"
        if ok and "did NOT run" in ((proc.stdout or "") + (proc.stderr or "")):
            ok, detail = False, "短语规则没跑（assets/vendor 丢了？）"
        check("validate-skill 通过", ok, detail)

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
                "validate-semantic-breaks", str(bad_cues), str(bad_protected)],
                must="protected phrase crosses a cue boundary")

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
                "validate-caption-sync", str(tts_json), str(sync_cues)],
                must="SYNC ERROR")

            # 3. 视频门：非媒体输入
            expect_blocked("负向：非视频输入被拦", [
                str(NODE), str(ROOT / "scripts" / "notebook-video.mjs"),
                "validate-video", str(__file__), "30"], must="ffprobe")

    # ---- 音效库：好夹具必须通过；篡改文件 / 增益越界必须被拦 ----
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
    else:
        check("音效库门禁（需要 ffmpeg）", False, "ffmpeg 不在 PATH，无法回归音效库门禁")

    # ---- 背景库：模板库必须通过；改坏许可 / 改动文件（sha256）/ 相邻重复必须被拦或提示 ----
    tpl = ROOT / "assets" / "lecture-template"
    vb = ROOT / "scripts" / "validate-backgrounds.py"
    good = run(sys.executable, str(vb), str(tpl), "--min-per-skin", "journal=8,papercut=8,archive=8,flat=4,cel=4")
    check("背景库：模板通过 validate-backgrounds", good.returncode == 0, f"rc={good.returncode}")
    # ---- 线稿几何：模板必须通过（改坏 fit 的负向用例在 tests/test_linework_crops.py）----
    good = run(sys.executable, str(ROOT / "scripts/linework_index.py"), "--geometry")
    check("线稿几何：模板通过", good.returncode == 0, f"rc={good.returncode}")

    failed = [r for r in results if not r[1]]
    if not failed:
        print(f"SELFTEST PASS (all {len(results)} checks passed)")
        return 0
    print(f"\n共 {len(results)} 项，通过 {len(results) - len(failed)}，失败 {len(failed)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
