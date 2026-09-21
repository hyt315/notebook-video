#!/usr/bin/env python3
"""Overlay-component coordinate reporter (只读，不挡渲染).

ASTRA 教训：StampSeal 的 x/y 写成了场景坐标，实际相对卡片，飞出屏外但
渲染零报错。Remotion 静态扫不到运行时坐标系，本脚本做诚实的事：
列出所有覆盖层组件 (StampSeal/Burst/Callout/ChipContract/Funnel/ChatThread) 的数字 x/y，超过整画布
(1920x1080 / 1080x1440) 直接报错；x>1000 或 y>700 的打 WARN，提醒人工
确认是场景坐标还是卡片相对坐标（见 references/fxkit.md 坐标铁律）。

用法：python scripts/coords-lint.py PROJECT_DIR [--strict]
--strict 下 WARN 也算失败（发版前用）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

OVERLAYS = ("StampSeal", "Burst", "Callout", "ChipContract", "Funnel", "ChatThread")
# 老模块里的覆盖层类件（不在 src/components/ 下，但同样是"场景坐标"语义）
LEGACY_OVERLAYS = ("StampBanner",)
COORD = re.compile(r"\b([xy])=\{(\d+)\}")
PROP_BLOCK = re.compile(r"export\s+const\s+([A-Z]\w*)\s*:\s*React\.FC<\{(.*?)\}>", re.S)


def overlays_of(root: Path) -> tuple[str, ...]:
    """名单 = 写死的历史件 ∪ **从源码推导**的覆盖层类组件。

    推导**只扫 `src/components/**`**（v3.1 封装层，那里的 x/y 是"场景坐标"语义）+ 上面两份明确名单。

    ⚠️ 第一版扫了整棵树，于是在标准模板上多报一条假阳性
    `VERIFY-FRAME scenes.tsx:180 ZoomStage x=1250`（复核实测：旧版只有 1 条 WARN）——
    `ZoomStage` / `StageFrame` / `Corridor` / `CoverPanel` / `ConsoleWindow` 这些是**布局件**，
    它们的 x/y 是版面坐标，写 1250 完全合法，不该进"场景坐标还是卡片相对坐标？"的人工确认档。
    """
    found = set()
    layer = root / "src" / "components"
    if layer.is_dir():
        for tsx in sorted(layer.rglob("*.tsx")):
            text = tsx.read_text(encoding="utf-8", errors="ignore")
            for m in PROP_BLOCK.finditer(text):
                props = m.group(2)
                if re.search(r"\bx\s*[?:]", props) and re.search(r"\by\s*[?:]", props):
                    found.add(m.group(1))
    return tuple(sorted(found | set(OVERLAYS) | set(LEGACY_OVERLAYS)))


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    strict = "--strict" in sys.argv
    errors: list[str] = []
    warns: list[str] = []
    overlays = overlays_of(root)   # 名单 = 历史 6 件 ∪ 源码推导
    for src in (root / "src",):
        if not src.is_dir():
            print(f"no src/ under {root}")
            return 2
        # 递归扫子目录：v3.1 起组件封装层在 src/components/，不递归会整层漏检
        for tsx in sorted(src.rglob("*.tsx")):
            text = tsx.read_text(encoding="utf-8", errors="ignore")
            for match in COORD.finditer(text):
                axis, value = match.group(1), int(match.group(2))
                window = text[max(0, match.start() - 400):match.start()]
                comp = "?"
                for name in overlays:
                    if name in window:
                        comp = name
                line = text.count("\n", 0, match.start()) + 1
                where = f"{tsx.name}:{line} {comp} {axis}={value}"
                if value > 1920 or (axis == "y" and value > 1440):
                    errors.append(f"OFF-CANVAS {where}")
                elif comp != "?" and (value > 1000 if axis == "x" else value > 700):
                    warns.append(f"VERIFY-FRAME {where}（场景坐标还是卡片相对坐标？）")
                elif comp == "ChatThread" and axis == "y" and 0 < value < 170:
                    warns.append(f"VERIFY-TOP-CHROME {where}（y={value} < 170 且靠近左上角时，警惕遮挡全局顶栏章节卡 x:92..484 y:74..164）")
    for w in warns:
        print(f"WARN: {w}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1
    print(f"coords-lint: {len(warns)} warnings, 0 errors"
          + (" (strict: warnings fail)" if strict else ""))
    return 1 if (strict and warns) else 0


if __name__ == "__main__":
    raise SystemExit(main())
