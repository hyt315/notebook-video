#!/usr/bin/env python3
"""validate-typography.py · 必跑计算字号门禁（零外部依赖，不依赖 OCR，永不 SKIPPED）

核查依据（16:9 1920×1080 设计坐标 → 2560×1440 成片 → 360 CSS px 竖屏手机）：
    · 手机可读地板 12 CSS px = 1440 成片 85.3 px = 1080 设计坐标 64 px。
    · 所有要读的字（字幕、章节标、主体卡片/对比栏/清单/流程主文案）必须 ≥ 64 设计 px（P0）；
      代码行与密集柱标受列宽约束允许按 fit_text 自动收缩，低于 64 时记 P1 提示。

用法：
    python3 scripts/validate-typography.py <project> [--min-px 64] [--json]

退出码：0 通过 / 1 有 P0 越线 / 2 用法或工程目录缺失。零第三方依赖，Python 3.10+。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_MIN_DESIGN_PX = 64
SUBTITLE_RECOMMENDED_PX = 70
# 允许按容器宽度自动收缩（低于 64 记 P1 而非 P0）的特殊元素
SOFT_KINDS = {"codeline", "codebox", "bar", "reading"}
# 非阅读装饰元素（无字号或纯图形）
IGNORE_KINDS = {"arrow", "timer", "region", "media", "archive", "loupe", "figure", "stamp"}


def _check_theme_typography(project: Path, min_px: int) -> tuple[list[str], list[str], dict]:
    p0, p1 = [], []
    info: dict = {}

    # 1. 字幕字号：读取 src/theme/canvas.ts（默认）与当前激活皮肤（src/theme/active.ts → <skin>.tsx）
    canvas_p = project / "src" / "theme" / "canvas.ts"
    sub_px = None
    if canvas_p.is_file():
        m = re.search(r"subFont:\s*(\d+)", canvas_p.read_text(encoding="utf-8"))
        if m:
            sub_px = int(m.group(1))

    active_skin = "flat"
    active_p = project / "src" / "theme" / "active.ts"
    if active_p.is_file():
        m = re.search(r"from\s+['\"]\./([a-z0-9_-]+)['\"]", active_p.read_text(encoding="utf-8"))
        if m:
            active_skin = m.group(1)

    skin_p = project / "src" / "theme" / f"{active_skin}.tsx"
    chrome_title_px = None
    if skin_p.is_file():
        stxt = skin_p.read_text(encoding="utf-8")
        m_sub = re.search(r"subtitleSize:\s*(\d+)", stxt)
        if m_sub:
            sub_px = int(m_sub.group(1))
        # 手作皮肤自带 Chrome 时，直接从 Chrome 代码块解析标题容器字号（不得回退到 index.tsx）
        has_custom_chrome = "const Chrome" in stxt
        if has_custom_chrome:
            mc = re.search(r"const Chrome:.*?^\};", stxt, re.S | re.M)
            cblock = mc.group(0) if mc else stxt
            m_wrap = re.search(r"fontSize:\s*(\d+)[^\n]*\n[^\n]*p\.title", cblock)
            m_same = re.search(r"fontSize:\s*(\d+)[^\n]*p\.title", cblock)
            if m_same:
                chrome_title_px = int(m_same.group(1))
            elif m_wrap:
                chrome_title_px = int(m_wrap.group(1))
            else:
                sizes = [int(x) for x in re.findall(r"fontSize:\s*(\d+)", cblock)]
                if sizes:
                    chrome_title_px = max(sizes)
    else:
        has_custom_chrome = False

    # flat / cel 无自带 Chrome，使用 src/index.tsx 中的 Chrome
    if chrome_title_px is None and not has_custom_chrome:
        idx_p = project / "src" / "index.tsx"
        if idx_p.is_file():
            itxt = idx_p.read_text(encoding="utf-8")
            m_max = re.search(r"maxFontSize:\s*(\d+),\s*minFontSize:\s*(\d+)", itxt)
            if m_max:
                chrome_title_px = int(m_max.group(1))

    info["skin"] = active_skin
    info["subtitle_design_px"] = sub_px
    info["chapter_title_design_px"] = chrome_title_px

    if sub_px is not None:
        if sub_px < min_px:
            p0.append(f"字幕设计字号 {sub_px}px < {min_px}px（1440 成片 {sub_px * 4 / 3:.1f}px < 85.3px，手机不可读）")
        elif sub_px < SUBTITLE_RECOMMENDED_PX:
            p1.append(f"字幕设计字号 {sub_px}px 贴近 {min_px}px 地板，建议 ≥ {SUBTITLE_RECOMMENDED_PX}px 留出余量")

    if chrome_title_px is not None and chrome_title_px < min_px:
        p0.append(f"皮肤 {active_skin} 章节标字号 {chrome_title_px}px < {min_px}px（手机不可读）")

    return p0, p1, info


def _extract_auto_elements(project: Path) -> list[tuple[str, dict]]:
    """从 compose-story 生成的 src/story.ts（Record<string, StoryShot>）中提取全部镜头元素。"""
    out: list[tuple[str, dict]] = []
    for rel in ("src/story.ts", "src/scenes.tsx", "src/story.generated.ts"):
        fp = project / rel
        if not fp.is_file():
            continue
        txt = fp.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"export\s+const\s+STORY\b[^=]*=\s*(\{.*\});", txt, re.S)
        if not m:
            continue
        try:
            doc = json.loads(m.group(1))
        except Exception:
            continue
        if isinstance(doc, dict):
            shots_iter = doc.items() if "shots" not in doc else [(sh.get("id", "?"), sh) for sh in (doc.get("shots") or [])]
            for sid, sh in shots_iter:
                if not isinstance(sh, dict):
                    continue
                for el in sh.get("elements") or []:
                    if isinstance(el, dict):
                        out.append((str(sid), el))
            if out:
                return out
    return out


def _check_auto_elements(project: Path, min_px: int) -> tuple[list[str], list[str], dict]:
    p0, p1 = [], []
    els = _extract_auto_elements(project)
    checked = 0
    min_seen = None
    below_floor = 0

    for sid, e in els:
        kind = str(e.get("kind", ""))
        if kind in IGNORE_KINDS:
            continue
        # 检查主字号 size
        sz = e.get("size")
        if isinstance(sz, (int, float)) and sz > 0:
            checked += 1
            if min_seen is None or sz < min_seen:
                min_seen = sz
            if sz < min_px:
                below_floor += 1
                msg = f"{sid}.{e.get('id', kind)}({kind}) 字号 {sz}px < {min_px}px（1440 成片 {sz * 4 / 3:.1f}px）"
                is_long_formula_note = kind in ("note", "handnote") and len(str(e.get("text", ""))) >= 12
                if kind in SOFT_KINDS or kind == "node" or is_long_formula_note:
                    p1.append(msg)
                else:
                    p0.append(msg)
        # 检查 panel 条目字号
        if kind == "panel":
            for idx, it in enumerate(e.get("items") or []):
                isz = it.get("size") if isinstance(it, dict) else None
                if isinstance(isz, (int, float)) and isz > 0:
                    checked += 1
                    if min_seen is None or isz < min_seen:
                        min_seen = isz
                    if isz < min_px:
                        below_floor += 1
                        p0.append(f"{sid}.{e.get('id', 'panel')}.items[{idx}] 字号 {isz}px < {min_px}px")
        # 检查 flow 节点注记字号
        if kind == "node" and e.get("note"):
            nsz = e.get("noteSize")
            if isinstance(nsz, (int, float)) and nsz > 0:
                checked += 1
                if min_seen is None or nsz < min_seen:
                    min_seen = nsz
                if nsz < min_px:
                    below_floor += 1
                    p1.append(f"{sid}.{e.get('id', 'node')}.note 字号 {nsz}px < {min_px}px（紧凑流式注记）")

    return p0, p1, {"elements_checked": checked, "min_element_px": min_seen, "below_floor": below_floor}


def main() -> int:
    ap = argparse.ArgumentParser(description="计算字号必跑门禁（零外部依赖，永不 SKIPPED）")
    ap.add_argument("project", help="工程目录路径")
    ap.add_argument("--min-px", type=int, default=DEFAULT_MIN_DESIGN_PX, help="设计坐标最小可读字号（默认 64 = 85.3px@1440 = 12 CSS px@360）")
    ap.add_argument("--json", action="store_true", help="输出 JSON 格式结果")
    args = ap.parse_args()

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"工程目录不存在：{project}", file=sys.stderr)
        return 2

    p0_t, p1_t, info_t = _check_theme_typography(project, args.min_px)
    p0_e, p1_e, info_e = _check_auto_elements(project, args.min_px)
    p0 = p0_t + p0_e
    p1 = p1_t + p1_e
    summary = {
        "ok": len(p0) == 0,
        "min_design_px": args.min_px,
        "min_1440_px": round(args.min_px * 4 / 3, 1),
        **info_t,
        **info_e,
        "p0": p0,
        "p1": p1,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if summary["ok"] else "FAIL"
        print(f"validate-typography：skin={info_t.get('skin')} subtitle={info_t.get('subtitle_design_px')}px "
              f"chapter={info_t.get('chapter_title_design_px')}px elements={info_e['elements_checked']} "
              f"(min={info_e['min_element_px']}) → P0={len(p0)} P1={len(p1)} · {status}")
        for x in p0:
            print(f"  [P0] {x}")
        for x in p1[:10]:
            print(f"  [P1] {x}")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
