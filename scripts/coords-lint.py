#!/usr/bin/env python3
"""Overlay-component coordinate reporter (只读，不挡渲染).

ASTRA 教训：StampSeal 的 x/y 写成了场景坐标，实际相对卡片，飞出屏外但
渲染零报错。Remotion 静态扫不到运行时坐标系，本脚本做诚实的事：
列出所有覆盖层组件 (StampSeal/BurstCallout/Callout/ChipContract/PayPop/
Funnel/ChatThread/MailScan/TimeRail/CompareBars) 的数字 x/y，超过整画布
(1920x1080 / 1080x1440) 直接报错；x>1000 或 y>700 的打 WARN，提醒人工
确认是场景坐标还是卡片相对坐标（见 references/fxkit.md 坐标铁律）。

用法：python scripts/coords-lint.py PROJECT_DIR [--strict]
--strict 下 WARN 也算失败（发版前用）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

OVERLAYS = ("StampSeal", "BurstCallout", "Burst", "Callout", "ChipContract", "PayPop",
            "Funnel", "ChatThread", "MailScan", "TimeRail", "CompareBars")
COORD = re.compile(r"\b([xy])=\{(\d+)\}")


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    strict = "--strict" in sys.argv
    errors: list[str] = []
    warns: list[str] = []
    for src in (root / "src",):
        if not src.is_dir():
            print(f"no src/ under {root}")
            return 2
        for tsx in sorted(src.glob("*.tsx")):
            text = tsx.read_text(encoding="utf-8", errors="ignore")
            for match in COORD.finditer(text):
                axis, value = match.group(1), int(match.group(2))
                window = text[max(0, match.start() - 400):match.start()]
                comp = "?"
                for name in OVERLAYS:
                    if name in window:
                        comp = name
                line = text.count("\n", 0, match.start()) + 1
                where = f"{tsx.name}:{line} {comp} {axis}={value}"
                if value > 1920 or (axis == "y" and value > 1440):
                    errors.append(f"OFF-CANVAS {where}")
                elif comp != "?" and (value > 1000 if axis == "x" else value > 700):
                    warns.append(f"VERIFY-FRAME {where}（场景坐标还是卡片相对坐标？）")
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
