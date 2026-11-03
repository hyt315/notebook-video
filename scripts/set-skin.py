#!/usr/bin/env python3
"""set-skin.py · 一次把皮肤改到位（active.ts + story.json + shots.json）

为什么需要这个命令：皮肤的**真源是 src/theme/active.ts**（渲染端 import 它），
但背景库按 `manifests/shots.json` 的 `theme` 挑图，而 `story.json` 的 theme 会被
compose-story 写回 shots.json。三处任意一处漏改，出来的就是
「A 皮肤的组件 + B 皮肤的纸」——2026-10-31 实测踩过：只改 active.ts 做跨皮肤对照，
五族渲出来全是点阵纸，结论全废。

这个命令只做一件事：把三处写成同一个值，然后告诉你下一步要重跑什么。
不改内容、不改画面、不碰排版。

用法：
    python scripts/set-skin.py PROJECT_DIR SKIN [--rebuild]

    SKIN     flat | cel | journal | papercut | archive（或别名 手账 / 剪纸 / 档案 / 扁平 / 漫画）
    --rebuild  顺手重跑 compose-story + resolve-shots（需要 story.json 与音频就绪）

退出码：0 成功 / 1 有文件写不进去 / 2 用法错误
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SKINS = ("flat", "cel", "journal", "papercut", "archive")
ALIAS = {
    "扁平": "flat", "矢量": "flat", "flat": "flat",
    "漫画": "cel", "赛璐璐": "cel", "cel": "cel",
    "手账": "journal", "手帐": "journal", "journal": "journal",
    "剪纸": "papercut", "papercut": "papercut",
    "档案": "archive", "archive": "archive",
}
ACTIVE_TS = """// 主题开关（LOCKED）：本文件只允许改写 import 来源路径，由 new-project --style / set-skin.py 写入。
// 可选值：./flat ./cel ./journal ./papercut ./archive
// 注意：必须保持「先 import 再 export」两行形式，单行再导出在打包器下会失效。
import {{THEME}} from './{skin}';
export {{THEME}};
"""


def set_active(project: Path, skin: str) -> bool:
    p = project / "src" / "theme" / "active.ts"
    if not p.parent.is_dir():
        print(f"  ! 没有 {p.parent}（不是 notebook-video 工程？）", file=sys.stderr)
        return False
    p.write_text(ACTIVE_TS.format(skin=skin), encoding="utf-8")
    print(f"  ✓ {p.relative_to(project)} → {skin}")
    return True


def set_json_theme(path: Path, skin: str, label: str) -> bool:
    if not path.is_file():
        print(f"  · {label} 不存在，跳过")
        return True
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"  ! {label} 不是合法 JSON：{e}", file=sys.stderr)
        return False
    if doc.get("theme") == skin:
        print(f"  · {label} theme 已经是 {skin}")
        return True
    doc["theme"] = skin
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  ✓ {label} theme → {skin}")
    return True


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    rebuild = "--rebuild" in argv
    if len(args) < 2:
        print("用法：python scripts/set-skin.py PROJECT_DIR SKIN [--rebuild]", file=sys.stderr)
        print(f"  SKIN 可选：{' / '.join(SKINS)}", file=sys.stderr)
        return 2
    project = Path(args[0]).resolve()
    if not project.is_dir():
        print(f"工程目录不存在：{project}", file=sys.stderr)
        return 2
    skin = ALIAS.get(args[1].strip().lower(), ALIAS.get(args[1].strip()))
    if skin not in SKINS:
        print(f"不认识的皮肤：{args[1]!r}；可选 {' / '.join(SKINS)}", file=sys.stderr)
        return 2

    print(f"set-skin：{project.name} → {skin}")
    ok = set_active(project, skin)
    ok &= set_json_theme(project / "story.json", skin, "story.json")
    ok &= set_json_theme(project / "manifests" / "shots.json", skin, "manifests/shots.json")
    if not ok:
        return 1

    if rebuild:
        here = Path(__file__).resolve().parent
        story = project / "story.json"
        if story.is_file():
            print("  … compose-story")
            r = subprocess.run([sys.executable, str(here / "compose-story.py"), str(story), str(project)],
                               cwd=str(project), capture_output=True, text=True, encoding="utf-8", errors="ignore")
            print("   ", (r.stdout or "").strip().splitlines()[-1] if r.stdout.strip() else f"rc={r.returncode}")
        print("  … resolve-shots")
        r = subprocess.run([sys.executable, str(here / "resolve-shots.py"), str(project)],
                           cwd=str(project), capture_output=True, text=True, encoding="utf-8", errors="ignore")
        tail = (r.stdout or "").strip().splitlines()
        print("   ", tail[-1] if tail else f"rc={r.returncode}")
        if r.returncode:
            for line in (r.stderr or "").strip().splitlines()[:6]:
                print("   ", line, file=sys.stderr)
            return 1
        print("  ✓ 已重建 shots.json / story.ts / shots.resolved.json")
    else:
        print("  下一步：重跑 compose-story（若改了 story.json）与 resolve-shots，再 preview")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
