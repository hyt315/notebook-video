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
# 负整数字面量**已进识别、暂不设负向阈值（知情边界）**。批5 提交话术曾暗示 `-220`
# 这类写法从此会被拦——收回：三档阈值（OFF-CANVAS >1920/1440、软档 >1000/700、
# SMOOSH 0<y<170）全在正向，负值进得了 COORD 却够不着任何一档（实测 `x={-2000}` rc=0）。
# 不补负向阈值的依据是本轮扫描：**合法负坐标在模板与成片工程里真实存在**——
#   · lecture-template src/components/chart.tsx:82/354/445（SVG 局部坐标 `x={-18}`/`y={-14}`/`y={-34}` 刻度与徽标）
#   · lecture-template src/theme/sticker.tsx:113 `Tape x={-50} y={-20}`（Tape 就在推导名单里，出血贴边是设计意图）
#   · 成片工程 overview-film src/scenes.tsx:791 `Callout x={80} y={-40}`（覆盖层骑跨卡片上沿，正常构图）
# 任何"负即出画"的阈值都会先把这三处合法写法打假。要补须先按"覆盖层短边整件离开
# 舞台半幅"（如 x < -960）立据并重扫全部工程，属改判据动作——留给有实证的下批。
# 边界钉死在 `\{` 与 `\}` 之间：只认**纯整数字面量**，`x={a-1}` / `x={w-40}` 这类
# 表达式里 `-` 前面还有标识符字符，落不进 `\{(-?\d+)\}`，不会被误配。
COORD = re.compile(r"\b([xy])=\{(-?\d+)\}")
PROP_BLOCK = re.compile(r"export\s+const\s+([A-Z]\w*)\s*:\s*React\.FC<\{(.*?)\}>", re.S)


def overlays_of(root: Path) -> tuple[str, ...]:
    """名单 = 写死的历史件 ∪ **从源码推导**的覆盖层类组件。

    推导范围 = `src/components/**`（v3.1 封装层）+ `src/theme/**`（皮肤 extras 里的贴纸件）
    ∪ 上面两份明确名单。两处的 x/y 都是"场景坐标"语义：前者是弹层/贴纸件，后者是 `extras.Tape`
    这类贴在纸面上的贴纸。

    ⚠️ 第一版扫了整棵树，于是在标准模板上多报一条假阳性
    `VERIFY-FRAME scenes.tsx:180 ZoomStage x=1250`（复核实测：旧版只有 1 条 WARN）——
    `ZoomStage` / `StageFrame` / `Corridor` / `CoverPanel` / `ConsoleWindow` 这些是**布局件**，
    它们的 x/y 是版面坐标，写 1250 完全合法，不该进"场景坐标还是卡片相对坐标？"的人工确认档。
    收紧到这两层后实测：components → {OverlayFrame}、theme → {Burst, Tape}，布局件一个不进。
    `Tape` 因此回到名单里（第二轮复核指出它掉出去了）：它与 `Burst` 同族，都是贴在画面上的贴纸。
    """
    found = set()
    for sub in ("components", "theme"):
        layer = root / "src" / sub
        if not layer.is_dir():
            continue
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
                # 已知边界（刻意**不改**）：1920/1440 是两块锁画布 (1920x1080 / 1080x1440) 的
                # **并集**上限，不是本片画布的上限 —— 横屏片 y=1200 实际早已出界但这里不报。
                # 收紧成"按工程画布口径"要动 validate-visual-plan 的 canvas 判据链，动它=动契约。
                # 同为已知边界：OFF-CANVAS 只评**正向**（value > 上限）。负静态坐标已进识别、
                # 暂不设负向阈值——合法出血/局部坐标用例真实存在，理由与证据链见 COORD 处注释。
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
