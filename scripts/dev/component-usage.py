#!/usr/bin/env python3
"""component-usage.py — 组件使用率报告（静态 grep，维护者工具，不进包；不渲染）。

    python3 scripts/dev/component-usage.py            # Markdown 表：每件组件在各处被引用几次
    python3 scripts/dev/component-usage.py --json     # 同样的数据，JSON
    python3 scripts/dev/component-usage.py --unused   # 只列零引用的件（「零引用即待删」的候选，见 technique.md#dependency-policy §8）

组件 = 模板 src/ 下各模块 `export const|function` 出来的 PascalCase 名（门禁件、入口文件、showcase，
以及主题 / 字体 / 转场 / 卷页这些基础设施除外）。引用来源分四栏：
  blueprints   blueprints/*.json 里 `$components` 的 skeleton / components
  examples     examples/**/*.story.json 里出现的同名字符串（`$components`、`component` 等）
  template     模板的 scenes.tsx / auto.tsx / custom/*.tsx 里的 `<Name` 用法（真正进画面的写法）
  docs         references/ 下 Markdown 里提到的次数（有没有文档）
showcase.tsx 单列（它是组件陈列页，不算真实用法）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "lecture-template" / "src"
SKIP = re.compile(r"(-gate\.tsx|^index\.tsx|^showcase\.tsx|^scenes\.tsx|^auto\.tsx)$")
# 引擎 / 主题 / 字体 / 转场这些基础设施不是「场景里挑来用的组件」，不计
INFRA = ("custom/", "theme/", "transitions/", "fonts.tsx", "fx.tsx", "glyph-snap.tsx", "craft-sheet.tsx")
EXPORT = re.compile(r"^export (?:const|function) ([A-Z][a-z]\w*)", re.M)


def components() -> dict[str, str]:
    out: dict[str, str] = {}
    for f in sorted(SRC.rglob("*.tsx")):
        rel = f.relative_to(SRC).as_posix()
        if rel.startswith(INFRA) or SKIP.search(f.name):
            continue
        for name in EXPORT.findall(f.read_text(encoding="utf-8")):
            out.setdefault(name, rel)
    return out


def json_strings(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from json_strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from json_strings(v)
    elif isinstance(o, str):
        yield o


def count_json(files, names) -> dict[str, int]:
    c = dict.fromkeys(names, 0)
    for f in files:
        for s in json_strings(json.loads(f.read_text(encoding="utf-8"))):
            for n in re.findall(r"[A-Z][a-z]\w*", s):
                if n in c:
                    c[n] += 1
    return c


def count_jsx(files, names) -> dict[str, int]:
    c = dict.fromkeys(names, 0)
    for f in files:
        for n in re.findall(r"<([A-Z][a-z]\w*)\b", f.read_text(encoding="utf-8")):
            if n in c:
                c[n] += 1
    return c


def count_docs(names) -> dict[str, int]:
    text = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "references").rglob("*.md"))
    return {n: len(re.findall(rf"\b{n}\b", text)) for n in names}


def report() -> list[dict]:
    comps = components()
    names = list(comps)
    bp = count_json(sorted((ROOT / "blueprints").glob("*.json")), names)
    ex = count_json(sorted((ROOT / "examples").rglob("*.story.json")), names)
    tpl = count_jsx([SRC / "scenes.tsx", SRC / "auto.tsx", *sorted((SRC / "custom").glob("*.tsx"))], names)
    show = count_jsx([SRC / "showcase.tsx"], names)
    docs = count_docs(names)
    rows = [{"component": n, "module": comps[n], "blueprints": bp[n], "examples": ex[n], "template": tpl[n],
             "showcase": show[n], "docs": docs[n]} for n in names]
    rows.sort(key=lambda r: (r["blueprints"] + r["examples"] + r["template"], r["component"]))
    return rows


def main(argv: list[str]) -> int:
    rows = report()
    if "--json" in argv:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    unused = [r for r in rows if r["blueprints"] + r["examples"] + r["template"] == 0]
    if "--unused" in argv:
        for r in unused:
            print(f"{r['component']:<20} {r['module']:<26} showcase={r['showcase']} docs={r['docs']}")
        return 0
    print("| 组件 | 模块 | blueprints | examples | template | showcase | docs |")
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['component']} | {r['module']} | {r['blueprints']} | {r['examples']} | {r['template']} | {r['showcase']} | {r['docs']} |")
    print(f"\n共 {len(rows)} 件；蓝图 / 示例 / 模板场景里零引用 {len(unused)} 件；文档零提及 {sum(1 for r in rows if not r['docs'])} 件。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
