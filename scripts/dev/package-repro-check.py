#!/usr/bin/env python3
"""package-repro-check.py — 上传包的两条硬要求（P2-27）

1. **可复现**：同一棵树构建两次，字节一致。不可复现的包意味着「你上传的东西没法被验证」，
   也意味着发布记录里的 SHA 只是那一次运行的偶然值。
2. **白名单**：包里不能出现 tests / .git / node_modules / 缓存 / 渲染产物；
   同时**必须**含排版链路的全部模块（少一个 = 用户拿到包装不起来，且本地测试发现不了）。

用法：python scripts/dev/package-repro-check.py
退出码 0 = 两条都成立。
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "scripts" / "package-skill.py"

# 必须打进去的：少一个，用户的 compose 就跑不起来
REQUIRED = [
    "BUILD-MANIFEST.json",
    "SKILL.md",
    "scripts/compose-story.py",
    "scripts/story_text.py",
    "scripts/story_caption.py",
    "scripts/story_acts.py",
    "scripts/story_time.py",
    "scripts/story_layout.py",
    "scripts/story_output.py",
    "scripts/text_metrics.py",
    "scripts/notebook-video.mjs",
    "scripts/kill-tree.mjs",
    "assets/fonts/metrics.json",
]
# 绝不能出现的
FORBIDDEN_DIRS = ("tests/", ".git/", "node_modules/", ".cache/", "renders/", "__pycache__/")
FORBIDDEN_FILES = (".env", "id_rsa", "id_ed25519", "credentials.json", ".DS_Store")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(out: Path) -> None:
    r = subprocess.run([sys.executable, str(PKG), "--output", str(out)],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"package-skill.py 失败：\n{r.stdout[-800:]}\n{r.stderr[-800:]}")


def main() -> int:
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        a, b = Path(td) / "a.zip", Path(td) / "b.zip"
        build(a)
        build(b)
        sa, sb = sha256(a), sha256(b)
        print(f"  构建 A {sa[:16]}…  {a.stat().st_size} 字节")
        print(f"  构建 B {sb[:16]}…  {b.stat().st_size} 字节")
        if sa != sb:
            problems.append(f"两次构建字节不同：{sa} vs {sb}（有非确定输入：时间戳 / 路径 / 哈希顺序）")

        names = [n[len("notebook-video/"):] for n in zipfile.ZipFile(a).namelist()
                 if n.startswith("notebook-video/")]
        pretty = [n for n in names if not n.endswith("/")]
        print(f"  包内 {len(pretty)} 个文件")

        for req in REQUIRED:
            if req not in names:
                problems.append(f"包内缺 {req}")
        for name in pretty:
            if any(name.startswith(d) or f"/{d}" in name for d in FORBIDDEN_DIRS):
                problems.append(f"包里混进了不该上传的目录：{name}")
                break
            base = name.rsplit("/", 1)[-1]
            if base in FORBIDDEN_FILES:
                problems.append(f"包里混进了敏感/垃圾文件：{name}")

        man = json.loads(zipfile.ZipFile(a).read("notebook-video/BUILD-MANIFEST.json"))
        declared = man.get("files")
        # manifest 记录的是**被它覆盖的文件数**，不把自己算进去（package-skill.py 里 rows 不含 manifest）；
        # 所以包内文件数应正好多 1。判据写死这一点，别用「大致相等」糊过去。
        if isinstance(declared, int) and declared + 1 != len(pretty):
            problems.append(f"BUILD-MANIFEST 声明 {declared} 个（+自己=1），实际包内 {len(pretty)} 个")
        if not man.get("sha256"):
            problems.append("BUILD-MANIFEST 缺逐文件 sha256（无法验证包内容与清单一致）")
        if not man.get("version"):
            problems.append("BUILD-MANIFEST 缺 version（发布记录无法对应到具体版本）")

    for p in problems:
        print(f"  FAIL {p}")
    print("PASS · 上传包可复现、白名单完整" if not problems else f"FAILED · {len(problems)} 条不成立")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
