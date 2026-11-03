#!/usr/bin/env python3
"""生成可上传的 notebook-video 技能 ZIP。

只收运行所需的白名单内容；`.git`、测试、缓存、渲染产物、社区治理与发行历史
不会因为碰巧放在工作树里就被带进上传包。默认不含按需下载的大字体；
要完全离线运行时加 --include-fonts。

用法：
  python scripts/package-skill.py --check-only
  python scripts/package-skill.py
  python scripts/package-skill.py --include-fonts --output dist/notebook-video-offline.zip
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
# README 里链到 CHANGELOG / CONTRIBUTING / SECURITY / README.en，这四个都很小。
# 早先把它们排除在包外，结果是**用户解包后点 README 就断链**，而入口文档完全正常——
# 打包自检（在解包目录里跑 validate-skill-consistency）当场就报出来了。带上更便宜。
ROOT_FILES = ("SKILL.md", "README.md", "README.en.md", "LICENSE", "NOTICE", "DEPENDENCIES.md",
              "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md", "manifest.json")
RUNTIME_DIRS = ("agents", "assets", "blueprints", "examples", "references", "scripts")
REQUIRED = ROOT_FILES + ("scripts/notebook-video.mjs", "assets/lecture-template/package.json")
SKIP_DIRS = {".git", ".github", ".pytest_cache", "__pycache__", "node_modules", "renders", "dist", "build", ".bundle"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".log", ".tmp", ".mp4", ".mov", ".webm", ".zip"}
SKIP_NAMES = {".DS_Store", "Thumbs.db"}
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def excluded(path: Path, include_fonts: bool) -> bool:
    r = rel(path)
    parts = PurePosixPath(r).parts
    if any(part in SKIP_DIRS for part in parts):
        return True
    if path.name in SKIP_NAMES or path.suffix.lower() in SKIP_SUFFIXES:
        return True
    # 字体是命令按需下载的运行缓存，不是源码；离线包可显式带上。
    if not include_fonts and r.startswith("assets/fonts/") and path.suffix.lower() in {".ttf", ".otf"}:
        return True
    return False


def collect_files(include_fonts: bool = False) -> list[Path]:
    missing = [r for r in REQUIRED if not (ROOT / r).is_file()]
    if missing:
        raise ValueError(f"技能必需文件缺失：{missing}")
    files = [ROOT / r for r in ROOT_FILES]
    for dirname in RUNTIME_DIRS:
        base = ROOT / dirname
        if not base.is_dir():
            raise ValueError(f"技能运行目录缺失：{dirname}/")
        files.extend(p for p in base.rglob("*") if p.is_file() and not excluded(p, include_fonts))
    return sorted(set(files), key=rel)


def validate_skill_links(files: list[Path]) -> list[str]:
    """包内**所有** Markdown 的本地链接都要落到包内存在的文件。

    只查 SKILL.md 是不够的：references/ 之间互相指的路径一旦打包改变（比如某个文件被排除），
    用户点过去就是断链，而入口文档完全正常。所以逐篇查，路径按引用方所在目录解析。
    """
    included = {rel(p) for p in files}
    problems = []
    # README 是**面向仓库**的：它链到 CONTRIBUTING / CHANGELOG / SECURITY / README.en，
    # 这几个按发行策略不随包分发。所以 README 不参与包内链接检查（不是忘了，是明确排除）。
    docs = [p for p in files if p.suffix.lower() in (".md", ".markdown") and rel(p) not in LINK_CHECK_EXCLUDE]
    for md in docs:
        base = PurePosixPath(rel(md)).parent
        text = md.read_text(encoding="utf-8", errors="replace")
        for target in LINK_RE.findall(text):
            target = target.strip().split("#", 1)[0]
            if not target or "://" in target or target.startswith(("mailto:", "#")):
                continue
            if target.startswith("/"):           # 仓库绝对路径不是包内路径
                continue
            path = (base / target)
            normalised = []
            for part in path.parts:              # 手工消解 ..，避免依赖文件名系统语义
                if part == "..":
                    if normalised:
                        normalised.pop()
                elif part not in (".", ""):
                    normalised.append(part)
            resolved = PurePosixPath(*normalised).as_posix() if normalised else ""
            # 指向**目录**的链接（README 的 `examples/`）只要包里有该目录下的文件就算有效
            is_dir_link = bool(resolved) and any(x.startswith(resolved + "/") for x in included)
            if not resolved or (resolved not in included and not is_dir_link):
                problems.append(f"{rel(md)} 链接未进入上传包：{target}")
    return problems


FIXED_DATE = (1980, 1, 1, 0, 0, 0)      # 固定时间戳：同输入必须得到同字节
LINK_CHECK_EXCLUDE = {"README.md"}      # 见 validate_skill_links 的注释


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_rev() -> dict:
    """包要能追溯到源码版本。工作树脏就明说，别让 manifest 看起来比实际干净。"""
    try:
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                             text=True, encoding="utf-8", timeout=20)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True,
                               text=True, encoding="utf-8", timeout=20)
        return {"git_rev": rev.stdout.strip() or None, "git_dirty": bool(dirty.stdout.strip())}
    except (OSError, subprocess.SubprocessError):
        return {"git_rev": None, "git_dirty": None}


def _write_entry(zf: zipfile.ZipFile, name: str, data: bytes) -> None:
    """固定时间戳 + 固定权限：同输入必须得到同字节，否则两次构建的 hash 不一样，就等于没有指纹。"""
    info = zipfile.ZipInfo(name, FIXED_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    zf.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build(output: Path, include_fonts: bool) -> dict:
    files = collect_files(include_fonts)
    problems = validate_skill_links(files)
    if problems:
        raise ValueError("\n".join(problems))
    output.parent.mkdir(parents=True, exist_ok=True)
    version = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8")).get("version", "0.0.0")
    rows = [{"path": rel(p), "bytes": p.stat().st_size, "sha256": _sha256(p)} for p in files]
    manifest = {
        "name": "notebook-video",
        "version": version,
        "files": len(rows),
        "bytes": sum(r["bytes"] for r in rows),
        "include_fonts": include_fonts,
        "sha256": rows,
        **_git_rev(),
    }
    blob = json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True).encode("utf-8")
    with zipfile.ZipFile(output, "w") as zf:
        for path, row in zip(files, rows):
            _write_entry(zf, f"notebook-video/{row['path']}", path.read_bytes())
        _write_entry(zf, "notebook-video/BUILD-MANIFEST.json", blob)
    return {"count": len(files), "raw": manifest["bytes"], "packed": output.stat().st_size,
            "version": version, "sha256": _sha256(output), "git": _git_rev()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", type=Path, default=ROOT / "dist" / "notebook-video-skill.zip")
    ap.add_argument("--include-fonts", action="store_true", help="包含按需下载的 TTF/OTF，制作离线包")
    ap.add_argument("--check-only", action="store_true", help="只检查清单与 SKILL.md 链接，不写 ZIP")
    args = ap.parse_args()
    try:
        files = collect_files(args.include_fonts)
        problems = validate_skill_links(files)
        if problems:
            raise ValueError("\n".join(problems))
        if args.check_only:
            print(f"PASS · {len(files)} 个文件 · {sum(p.stat().st_size for p in files) / 1024 / 1024:.1f} MiB（未压缩）")
            print("上传白名单与 SKILL.md 本地链接完整。")
            return 0
        built = build(args.output.resolve(), args.include_fonts)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"打包失败：{exc}", file=sys.stderr)
        return 1
    print(f"已生成：{args.output.resolve()}")
    print(f"{built['count']} 个文件 · {built['raw'] / 1024 / 1024:.1f} MiB → {built['packed'] / 1024 / 1024:.1f} MiB")
    print(f"版本 {built['version']} · SHA256 {built['sha256']}")
    git = built["git"]
    if git.get("git_rev"):
        print(f"源码 {git['git_rev']}{'（工作树有未提交改动）' if git.get('git_dirty') else ''}")
    print("未包含：.git / tests / 缓存 / 渲染产物（README 引用的发行文档已随包）" + ("。" if args.include_fonts else " / 按需下载字体。"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
