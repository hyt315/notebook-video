#!/usr/bin/env python3
"""视觉矩阵：五皮肤 × 三模式的最小对照（P1-16）。

不是"渲染成功"清单，是**每格一张接触表 + 一份缺陷记录**：
纸卡语言有没有串皮、翻页方向一不一致、背景装饰压不压内容、同一故事跨皮肤还读不读得懂。
这些只有真渲出来、逐格看图才知道——`tsc` 全绿、门禁全过，也可能把 papercut 的纸片装饰
放进了 flat 的干净页面。

用法（要先有装好的 Remotion 依赖）：
    python scripts/dev/visual-matrix.py --out ../_matrix --deps <某工程的 node_modules>

产出：`<out>/<skin>-<story>.jpg`（接触表）+ `<out>/<skin>-<story>.json`（sweep 量到的覆盖率）。
缺依赖时它会直接说明，不会默默出一堆空表。

⚠ **跑矩阵期间不要并发跑别的渲染**（另一个 sweep / poster / preview）。Remotion 的 webpack 缓存
是机器级共享的：并发时会打出 `Webpack config change detected. Clearing cache...`，然后整格渲染失败——
症状是 journal 起全部 `sheet: null`，看起来像"手作皮肤渲不出来"，其实是被自己踩的（实测踩过一次）。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TPL = ROOT / "assets" / "lecture-template"
CLI = ROOT / "scripts" / "notebook-video.mjs"
SET_SKIN = ROOT / "scripts" / "set-skin.py"

# 默认矩阵：三种模式各一个代表，版式尽量铺开（flow / compare / define / number / page / type）。
# list 版式在 jie-component 里，作为可选第四列（--stories 里带上即可）。
DEFAULT_STORIES = [
    ("component", "examples/concept-hash-table.story.json"),
    ("freeform", "examples/recipes/jie-freeform.story.json"),
    ("hybrid", "examples/recipes/jie-hybrid.story.json"),
]
DEFAULT_SKINS = ["flat", "cel", "journal", "papercut", "archive"]


def link_node_modules(src: Path, dst: Path) -> bool:
    try:
        if os.name == "nt":
            r = subprocess.run(f'cmd /c mklink /J "{dst}" "{src}"', capture_output=True, text=True, timeout=60)
        else:
            os.symlink(src, dst, target_is_directory=True)
            r = None
        return dst.exists() and (r is None or r.returncode == 0)
    except OSError:
        return False


def run(cmd, cwd=None, timeout=600):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def build_cell(skin: str, story_path: Path, deps: Path, work: Path, out: Path, scale: float) -> dict:
    """一格 = 一个皮肤 × 一个故事。返回 {ok, sheet, coverage, problems}。"""
    project = work / f"proj-{skin}-{story_path.stem}"
    shutil.copytree(TPL, project,
                    ignore=shutil.ignore_patterns("node_modules", "renders", "build-test", "*.log"))
    if not link_node_modules(deps, project / "node_modules"):
        return {"ok": False, "problems": ["无法把 node_modules 链进临时工程（junction/symlink 不可用）"]}

    # 故事的 theme 必须与工程皮肤一致：否则 validate-treatment 的 P0 会先拦（媒介即隐喻）。
    story = json.loads(story_path.read_text(encoding="utf-8"))
    story["theme"] = skin
    story_file = work / f"story-{skin}-{story_path.stem}.json"
    story_file.write_text(json.dumps(story, ensure_ascii=False, indent=1), encoding="utf-8")

    r = run([sys.executable, str(ROOT / "scripts" / "compose-story.py"), str(story_file), str(project),
             "--report", str(project / "manifests" / "compose-report.json")])
    if r.returncode != 0:
        return {"ok": False, "problems": [f"compose 失败：{(r.stdout or '')[-400:]}"]}
    run([sys.executable, str(SET_SKIN), str(project), skin])
    # compose 只写 manifests/shots.json 与 src/story.ts；`src/shots.ts` 要 resolve-shots 才更新。
    # 漏掉这一步的话 shots.ts 还是模板的 8 镜，sweep 会量出 S5–S8 的空白格（这条是实测踩到的）。
    r = run([sys.executable, str(ROOT / "scripts" / "resolve-shots.py"), str(project)])
    if r.returncode != 0:
        return {"ok": False, "problems": [f"resolve-shots 失败：{(r.stdout or '')[-400:]}"]}
    duration = int(json.loads((project / "manifests" / "shots.json").read_text(encoding="utf-8"))["duration"])
    audio = project / "audio" / "narration.mp3"
    audio.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
             "-i", "anullsrc=r=48000:cl=mono", "-t", f"{duration / 30:.3f}", "-q:a", "9", str(audio)])
    r = run([os.environ.get("NODE") or shutil.which("node") or "node", str(CLI), "sync", str(project)], timeout=300)
    if r.returncode != 0:
        return {"ok": False, "problems": [f"sync 失败：{(r.stdout or '')[-400:]}"]}

    r = run([os.environ.get("NODE") or shutil.which("node") or "node", str(CLI), "sweep", str(project),
             f"--scale={scale}", "--cols=4", "--json"], timeout=1200)
    sheet = project / "renders" / "sweep-sheet.jpg"
    cov = {}
    try:
        cov = json.loads(r.stdout[r.stdout.index("{"):])
    except ValueError:
        pass
    problems = []
    if r.returncode != 0:
        # 只看 stdout 尾巴会截到 JSON 结构，真正的报错在 stderr（Chrome 的 console / cancelRender）
        problems.append(f"sweep 失败：{(r.stderr or r.stdout or '')[-600:]}")
    if not sheet.is_file():
        problems.append("没有出接触表 renders/sweep-sheet.jpg")
    # sweep 报"量不到"通常就是 shots.ts 与故事不同步（模板 8 镜 vs 故事 4 镜）——
    # 表上会多出几格纯背景的空镜，看起来像"皮肤把内容吃掉了"，其实是镜号不对。
    if cov.get("missing"):
        problems.append(f"sweep 量不到这些镜：{cov['missing']}（src/shots.ts 与故事不同步？）")
    key = f"{skin}-{story_path.stem}"
    if sheet.is_file():
        shutil.copy(sheet, out / f"{key}.jpg")
    (out / f"{key}.json").write_text(
        json.dumps({"skin": skin, "story": str(story_path), "mode": story.get("mode"),
                    "shots": cov.get("rows"), "missing": cov.get("missing"), "failed": cov.get("failed"),
                    "problems": problems}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": not problems and sheet.is_file(), "sheet": str(out / f"{key}.jpg"),
            "coverage": cov, "problems": problems}


def render_transition_frames(skin: str, story_path: Path, deps: Path, work: Path, out: Path) -> dict:
    """翻页方向证据：渲一张**转场中段**的帧（镜头起点 + 11，卷页 22 帧的中点）。

    接触表取的是每镜末段（内容已落定），看不出翻页往哪边翻；这条专门补那一维。
    """
    project = work / f"tr-{skin}-{story_path.stem}"
    shutil.copytree(TPL, project,
                    ignore=shutil.ignore_patterns("node_modules", "renders", "build-test", "*.log"))
    if not link_node_modules(deps, project / "node_modules"):
        return {"ok": False, "problems": ["无法链接 node_modules"]}
    story = json.loads(story_path.read_text(encoding="utf-8"))
    story["theme"] = skin
    story_file = work / f"tr-story-{skin}-{story_path.stem}.json"
    story_file.write_text(json.dumps(story, ensure_ascii=False, indent=1), encoding="utf-8")
    r = run([sys.executable, str(ROOT / "scripts" / "compose-story.py"), str(story_file), str(project),
             "--report", str(project / "manifests" / "compose-report.json")])
    if r.returncode != 0:
        return {"ok": False, "problems": [f"compose 失败：{(r.stdout or '')[-300:]}"]}
    run([sys.executable, str(SET_SKIN), str(project), skin])
    r = run([sys.executable, str(ROOT / "scripts" / "resolve-shots.py"), str(project)])
    if r.returncode != 0:
        return {"ok": False, "problems": [f"resolve-shots 失败：{(r.stdout or '')[-300:]}"]}
    duration = int(json.loads((project / "manifests" / "shots.json").read_text(encoding="utf-8"))["duration"])
    audio = project / "audio" / "narration.mp3"
    audio.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
             "-i", "anullsrc=r=48000:cl=mono", "-t", f"{duration / 30:.3f}", "-q:a", "9", str(audio)])
    node = os.environ.get("NODE") or shutil.which("node") or "node"
    run([node, str(CLI), "sync", str(project)], timeout=300)
    resolved = json.loads((project / "manifests" / "shots.resolved.json").read_text(encoding="utf-8"))["shots"]
    problems = []
    for shot in resolved[1:]:
        frame = int(shot["from"]) + 11          # 卷页 22 帧的中点
        out_jpg = out / f"{skin}-{story_path.stem}-transition-{shot['id']}.jpg"
        r = run([node, str(CLI), "poster", str(project), str(out_jpg), f"--frame={frame}", "--scale=0.3"],
                timeout=300)
        if r.returncode != 0 or not out_jpg.is_file():
            problems.append(f"{shot['id']} 第 {frame} 帧：{(r.stdout or '')[-200:]}")
            continue
        # 只留前两处转场：方向看一两处就够，多了只是重复
        if len(list(out.glob(f"{skin}-{story_path.stem}-transition-*.jpg"))) >= 2:
            break
    return {"ok": not problems, "problems": problems}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="矩阵输出目录")
    ap.add_argument("--deps", default=os.environ.get("NV_E2E_NODE_MODULES", ""),
                    help="一份装好的 node_modules（Remotion 依赖）")
    ap.add_argument("--skins", default=",".join(DEFAULT_SKINS))
    ap.add_argument("--stories", default="", help="逗号分隔的 story.json 路径（缺省用三种模式各一）")
    ap.add_argument("--scale", type=float, default=0.2)
    ap.add_argument("--transitions", action="store_true",
                    help="另渲每皮肤 2 张转场中段帧（翻页方向证据）")
    a = ap.parse_args()
    deps = Path(a.deps) if a.deps else TPL / "node_modules"
    if not deps.is_dir():
        print(f"没有可用的 Remotion 依赖：{deps}\n"
              f"先在资产模板跑 npm ci，或用 --deps 指向一份装好的 node_modules。", file=sys.stderr)
        return 2
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if a.stories:
        stories = [(Path(p).stem, Path(p).resolve()) for p in a.stories.split(",") if p.strip()]
    else:
        stories = [(name, ROOT / rel) for name, rel in DEFAULT_STORIES]
    skins = [s.strip() for s in a.skins.split(",") if s.strip()]

    rows = []
    with tempfile.TemporaryDirectory(prefix="nv-matrix-") as td:
        work = Path(td)
        for skin in skins:
            for name, story in stories:
                print(f"[{skin} × {name}] 渲染中 …", flush=True)
                res = build_cell(skin, story, deps, work, out, a.scale)
                state = "OK" if res.get("ok") else "FAIL"
                note = " · ".join(res.get("problems") or []) or f"{len((res.get('coverage') or {}).get('rows') or [])} 镜已量到"
                print(f"[{skin} × {name}] {state}  {note}", flush=True)
                rows.append({"skin": skin, "story": name, **{k: v for k, v in res.items() if k != "coverage"},
                             "rows": len((res.get("coverage") or {}).get("rows") or []),
                             "missing": (res.get("coverage") or {}).get("missing"),
                             "failed": (res.get("coverage") or {}).get("failed")})
    (out / "matrix.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.transitions:
        story = stories[0][1]
        print(f"\n转场中段帧（{story.name}）：", flush=True)
        with tempfile.TemporaryDirectory(prefix="nv-matrix-tr-") as td:
            for skin in skins:
                res = render_transition_frames(skin, story, deps, Path(td), out)
                print(f"[{skin}] {'OK' if res['ok'] else 'FAIL'}  {' · '.join(res['problems']) or '已出图'}",
                      flush=True)
                rows.append({"skin": skin, "story": f"{story.stem}-transition", **res})
        (out / "matrix.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    bad = [r for r in rows if not r.get("ok")]
    print(f"\n矩阵完成：{len(rows) - len(bad)}/{len(rows)} 格出表 → {out}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
