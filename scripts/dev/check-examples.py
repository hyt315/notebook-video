#!/usr/bin/env python3
"""所有正例 story 示例必须过完整构建期硬门禁（3.5.4）。

体检发现：随包 14 个 story 示例里 7 个过不了自己的硬门禁，而 CI 从没跑过它们。
本脚本对 examples/ 下每个 *.story.json（examples/negative/ 除外）：
  new-project 到临时目录 → make-video STORY PROJ --skip-review（compose → 15 道门禁 → tsc，不渲染）
rc≠0 即失败。examples/negative/ 下的负例反过来：必须在 make-video 里被拦（rc≠0），
且输出里要出现该负例 README 表格登记的预期判据关键字。

node_modules：默认软链 assets/lecture-template/node_modules（CI 在 npm ci 之后跑本步骤）；
也可 --node-modules DIR 指定；都没有则由 make-video 自己 npm ci（每个工程约 1 分钟）。

用法：python3 scripts/dev/check-examples.py [--only NAME ...] [-j 2] [--keep]
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EX = ROOT / "examples"
NEG = EX / "negative"


def positives() -> list[Path]:
    return sorted(p for p in EX.rglob("*.story.json") if NEG not in p.parents)


def negatives() -> dict[Path, str]:
    """examples/negative/README.md 的表格：| `文件名` | 预期拦下的判据关键字 | 说明 |"""
    out: dict[Path, str] = {}
    readme = NEG / "README.md"
    if not readme.is_file():
        return out
    for m in re.finditer(r"^\|\s*`([^`]+\.story\.json)`\s*\|\s*`([^`]+)`\s*\|", readme.read_text(encoding="utf-8"), re.M):
        out[NEG / m.group(1)] = m.group(2)
    return out


def run_one(story: Path, nm: Path | None, keep_root: Path | None) -> tuple[Path, int, str]:
    base = Path(tempfile.mkdtemp(prefix="nbv-ex-", dir=keep_root))
    proj = base / story.name.replace(".story.json", "")
    try:
        r = subprocess.run(["node", str(ROOT / "scripts" / "notebook-video.mjs"), "new-project", str(proj),
                            f"--style={_theme(story)}"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode:
            return story, r.returncode, "new-project 失败\n" + r.stdout[-1500:] + r.stderr[-1500:]
        if nm and nm.is_dir() and not (proj / "node_modules").exists():
            os.symlink(nm, proj / "node_modules")
        # 手作皮肤示例自带导演层：<名>.treatment.json 与 story 同目录（与 make-video 新建工程时的行为一致）
        tr = story.with_name(story.name.replace(".story.json", ".treatment.json"))
        if tr.is_file():
            shutil.copyfile(tr, proj / "manifests" / "treatment.json")
        r = subprocess.run(["node", str(ROOT / "scripts" / "make-video.mjs"), str(story), str(proj), "--skip-review"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
        return story, r.returncode, r.stdout + r.stderr
    finally:
        if keep_root is None:
            shutil.rmtree(base, ignore_errors=True)


def _theme(story: Path) -> str:
    import json
    try:
        return str(json.loads(story.read_text(encoding="utf-8")).get("theme") or "flat")
    except ValueError:
        return "flat"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None, help="只跑这些示例（文件名去掉 .story.json）")
    ap.add_argument("-j", type=int, default=2)
    ap.add_argument("--node-modules", default=None)
    ap.add_argument("--keep", default=None, help="把工程留在这个目录下（排查用）")
    ap.add_argument("--skip-negatives", action="store_true")
    a = ap.parse_args()
    nm = Path(a.node_modules) if a.node_modules else ROOT / "assets" / "lecture-template" / "node_modules"
    keep = Path(a.keep) if a.keep else None
    if keep:
        keep.mkdir(parents=True, exist_ok=True)
    pos = positives()
    neg = {} if a.skip_negatives else negatives()
    if a.only:
        want = set(a.only)
        pos = [p for p in pos if p.name.replace(".story.json", "") in want]
        neg = {p: k for p, k in neg.items() if p.name.replace(".story.json", "") in want}
    jobs = [(p, None) for p in pos] + [(p, k) for p, k in neg.items()]
    bad: list[str] = []
    with ThreadPoolExecutor(max_workers=max(1, a.j)) as ex:
        futs = {ex.submit(run_one, p, nm, keep): (p, k) for p, k in jobs}
        for f in futs:
            p, key = futs[f]
            story, rc, out = f.result()
            rel = story.relative_to(ROOT)
            if key is None:
                ok = rc == 0
                print(f"  {'✓' if ok else '✗'} 正例 {rel}  rc={rc}")
                if not ok:
                    bad.append(str(rel))
                    print("\n".join(l for l in out.splitlines() if re.search(r"P0|✗|FAIL|Error|错误", l))[:2500])
            else:
                ok = rc != 0 and key in out
                print(f"  {'✓' if ok else '✗'} 负例 {rel}  rc={rc}  预期判据「{key}」{'命中' if key in out else '未命中'}")
                if not ok:
                    bad.append(str(rel))
    if bad:
        print(f"FAIL {len(bad)} 个示例不符合预期：{', '.join(bad)}")
        return 1
    print(f"OK 正例 {len(pos)} 个全部过门禁；负例 {len(neg)} 个全部按预期被拦")
    return 0


if __name__ == "__main__":
    sys.exit(main())
