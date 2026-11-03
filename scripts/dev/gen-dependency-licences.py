#!/usr/bin/env python3
"""gen-dependency-licences.py — 生成/校验顶层依赖的许可表（P2-31）

为什么需要：`DEPENDENCIES.md` 原来只记了 4 个包（手写的，写到哪算哪），而 `package.json`
声明了 46 个。发布出去的技能包带着 500+ 个传递依赖，用户却查不到它们是什么许可——
商用评估第一步就卡住。

做法：从 `package-lock.json` 取**已锁定版本**的 license 字段（不是查 npm registry，离线可跑），
把 package.json 声明的直接依赖整理成表，写进 `DEPENDENCIES.md` 的固定标记之间。
锁文件里没有 license 的（Remotion 的平台二进制）单独列出并注明由 Remotion License 覆盖。

用法：
  python scripts/dev/gen-dependency-licences.py            # 重新生成表
  python scripts/dev/gen-dependency-licences.py --check    # 只校验表是否最新（CI 用）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "assets" / "lecture-template" / "package.json"
LOCK = ROOT / "assets" / "lecture-template" / "package-lock.json"
DOC = ROOT / "DEPENDENCIES.md"
BEGIN = "<!-- BEGIN GENERATED LICENCES -->"
END = "<!-- END GENERATED LICENCES -->"

# 少数包在 lock 里没有 license 字段（Remotion 平台二进制，随主包同许可）
LICENCE_OVERRIDES = {"@remotion/compositor-*": "Remotion License"}
NOTE_OVERRIDES = {
    "@remotion/cli": "Remotion License（npm 元数据为 UNLICENSED，以仓库 LICENSE.md 为准）",
    "remotion": "Remotion License（公司规模超过阈值需商业授权）",
    "@remotion/effects": "Remotion License（含 EffectCraft MIT 改编，见包内 THIRD_PARTY_LICENSES.md）",
}


def licence_of(entry: dict) -> str:
    lic = entry.get("license")
    if isinstance(lic, str) and lic:
        return lic
    if isinstance(lic, dict) and lic.get("type"):
        return str(lic["type"])
    return "见包内 LICENSE"


def build_table() -> str:
    pkg = json.loads(PKG.read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8")).get("packages", {})
    rows = ["| 包 | 锁定版本 | 许可 | 类型 |", "|---|---|---|---|"]
    missing = []
    for kind, deps in (("运行时", pkg.get("dependencies", {})), ("构建/类型", pkg.get("devDependencies", {}))):
        for name in sorted(deps):
            entry = lock.get(f"node_modules/{name}")
            if not entry:
                missing.append(name)
                continue
            lic = NOTE_OVERRIDES.get(name) or licence_of(entry)
            rows.append(f"| `{name}` | {entry.get('version', '?')} | {lic} | {kind} |")
    if missing:
        rows.append("")
        rows.append("锁文件里找不到这些直接依赖（package.json 与 lock 不同步？）：" + "、".join(f"`{m}`" for m in missing))
    rows.append("")
    rows.append("传递依赖共 "
                f"{sum(1 for k in lock if k.startswith('node_modules/'))} 个，许可以上表为准的同一 lockfile 为准；"
                "全量清单：`node -e \"const l=require('./assets/lecture-template/package-lock.json');"
                "for(const[k,v]of Object.entries(l.packages))if(k)console.log(v.license||'?',k)\"`。")
    return "\n".join(rows)


def main() -> int:
    check = "--check" in sys.argv
    table = build_table()
    doc = DOC.read_text(encoding="utf-8")
    block = f"{BEGIN}\n\n## 直接依赖许可（自动生成，勿手改）\n\n{table}\n\n{END}"
    if BEGIN in doc and END in doc:
        head, rest = doc.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        new_doc = head + block + tail
    else:
        new_doc = doc.rstrip() + "\n\n" + block + "\n"
    if check:
        if new_doc != doc:
            print("DEPENDENCIES.md 的许可表过期了 —— 跑 python scripts/dev/gen-dependency-licences.py")
            return 1
        print("PASS · 许可表与 lockfile 一致")
        return 0
    DOC.write_text(new_doc, encoding="utf-8", newline="\n")
    print(f"已更新 {DOC.relative_to(ROOT)}（{table.count(chr(10)) - 1} 个直接依赖）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
