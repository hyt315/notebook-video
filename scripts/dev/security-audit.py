#!/usr/bin/env python3
"""security-audit.py — 发布前的安全与许可复核（P2-31）

四类问题，都能在发布前用机器判：

  1. **依赖许可有记录**：package.json 里的每个包都要在 `DEPENDENCIES.md` 里出现。
     没记录的依赖 = 用户拿到包以后不知道它是什么许可、能不能商用。
  2. **字体授权成对**：每个 .ttf/.otf 都要有同家族的 LICENSE 文件。OFL 要求分发时随附许可。
  3. **敏感文件不进库**：.env / 私钥 / .npmrc（可能带 token）/ 凭据 json。
  4. **源码里没有硬编码凭据**：`sk-…` / `ghp_…` / `AKIA…` / PEM 私钥块。

用法：python scripts/dev/security-audit.py [--quiet]
退出码 0 = 全过；1 = 有需要处理的问题。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {"node_modules", ".git", "dist", "__pycache__", ".cache", "renders", ".tools", ".venv"}

SENSITIVE_NAMES = {".env", ".env.local", ".npmrc", "id_rsa", "id_ed25519", "credentials.json",
                   "secrets.json", "auth.json", ".netrc"}
SENSITIVE_SUFFIX = (".pem", ".key", ".pfx", ".p12")
SECRET_PATTERNS = [
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}"), "OpenAI 风格密钥 sk-…"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}"), "GitHub token ghp_…"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), "GitHub fine-grained token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "PEM 私钥"),
]
SCAN_SUFFIX = (".py", ".mjs", ".js", ".ts", ".tsx", ".json", ".yml", ".yaml", ".sh", ".md", ".txt")


def walk(root: Path):
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_file():
            yield p


def check_dependency_records() -> list[str]:
    problems = []
    pkg = ROOT / "assets" / "lecture-template" / "package.json"
    doc_p = ROOT / "DEPENDENCIES.md"
    if not pkg.is_file() or not doc_p.is_file():
        return ["缺 package.json 或 DEPENDENCIES.md，无法核对依赖记录"]
    data = json.loads(pkg.read_text(encoding="utf-8"))
    declared = list(data.get("dependencies", {})) + list(data.get("devDependencies", {}))
    doc = doc_p.read_text(encoding="utf-8")
    missing = [name for name in declared if name not in doc]
    if missing:
        problems.append("DEPENDENCIES.md 未记录这些依赖：" + "、".join(missing))
    return problems


def check_font_licences() -> list[str]:
    problems = []
    fonts = ROOT / "assets" / "fonts"
    if not fonts.is_dir():
        return ["找不到 assets/fonts/"]
    licences = [p.name for p in fonts.iterdir() if p.name.upper().startswith("LICENSE")]
    for f in fonts.iterdir():
        if f.suffix.lower() not in (".ttf", ".otf"):
            continue
        # 家族前缀取前 4 个字符：LXGWWenKaiLite → lxgw（许可证文件名只写到厂商名），
        # NotoSerifSC → noto。不要用完整家族名匹配——许可文件是按厂商命名的，不是按字重。
        family = f.stem.split("-")[0][:4]
        if not any(family.lower() in lic.lower() for lic in licences):
            problems.append(f"{f.name} 没有同家族的 LICENSE（OFL 要求分发时随附）")
    return problems


def check_sensitive_files() -> list[str]:
    problems = []
    for p in walk(ROOT):
        rel = p.relative_to(ROOT).as_posix()
        if p.name in SENSITIVE_NAMES:
            problems.append(f"敏感文件进库：{rel}")
        elif p.suffix.lower() in SENSITIVE_SUFFIX:
            problems.append(f"疑似私钥/证书进库：{rel}")
    return problems


def check_hardcoded_secrets() -> list[str]:
    problems = []
    for p in walk(ROOT):
        if p.suffix.lower() not in SCAN_SUFFIX:
            continue
        if p.stat().st_size > 2_000_000:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern, label in SECRET_PATTERNS:
            if pattern.search(text):
                problems.append(f"{p.relative_to(ROOT).as_posix()} 里有{label}")
    return problems


def main() -> int:
    quiet = "--quiet" in sys.argv
    groups = [
        ("依赖许可记录", check_dependency_records()),
        ("字体授权", check_font_licences()),
        ("敏感文件", check_sensitive_files()),
        ("硬编码凭据", check_hardcoded_secrets()),
    ]
    total = 0
    for title, problems in groups:
        if problems:
            total += len(problems)
            print(f"  FAIL {title}")
            for p in problems[:12]:
                print(f"       - {p}")
            if len(problems) > 12:
                print(f"       … 还有 {len(problems) - 12} 条")
        elif not quiet:
            print(f"  OK   {title}")
    print(f"security-audit：{'PASS · 四类检查全过' if not total else f'FAILED · {total} 条待处理'}")
    return 0 if not total else 1


if __name__ == "__main__":
    sys.exit(main())
