#!/usr/bin/env python3
"""bg-gallery.py · DEV-ONLY: contact sheet of the background library (one row per skin, every background named).

    python scripts/dev/bg-gallery.py OUTPUT.jpg [--root assets/lecture-template] [--font FONT.ttf|otf]

Each tile is the real 2560×1440 file scaled down, with a 96 px (delivery) sample subtitle drawn in the skin's ink
straight onto the background — no plate, no halo — so the sheet shows the worst case the subtitle gate measures.
Legacy main / chapter / quiet rasters are marked "legacy". Needs Pillow.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
INK = {"flat": "#1c2024", "cel": "#111111", "journal": "#2b2420", "papercut": "#2a1a14", "archive": "#1d2328"}
SKINS = ("journal", "papercut", "archive", "flat", "cel")
FONT_CANDIDATES = [ROOT / "assets" / "fonts" / "NotoSerifSC-Bold.otf", ROOT / "assets" / "fonts" / "LXGWWenKaiLite-Medium.ttf",
                   Path("/workspace/tools/fonts/NotoSerifSC-Bold.otf")]


def main() -> int:
    out = Path(sys.argv[1])
    root = Path(sys.argv[sys.argv.index("--root") + 1]) if "--root" in sys.argv else ROOT / "assets" / "lecture-template"
    font_p = Path(sys.argv[sys.argv.index("--font") + 1]) if "--font" in sys.argv else next((p for p in FONT_CANDIDATES if p.exists()), None)
    if font_p is None:
        raise SystemExit("no CJK font found: pass --font (run `notebook-video fonts --serif` first)")
    lib = json.loads((root / "manifests" / "backgrounds.json").read_text(encoding="utf-8"))["backgrounds"]
    TW, TH, cols, pad, cap = 512, 288, 6, 14, 58
    rows = []
    for skin in SKINS:
        es = [e for e in lib if e["skin"] == skin and not e.get("legacy")] + [e for e in lib if e["skin"] == skin and e.get("legacy")]
        for i in range(0, len(es), cols):
            rows.append((skin, es[i:i + cols], i == 0))
    head = 46
    sheet_w = cols * (TW + pad) + pad + 150
    sheet_h = sum(TH + cap + pad + (head if first else 0) for _, _, first in rows) + pad
    sheet = Image.new("RGB", (sheet_w, sheet_h), (236, 236, 232))
    d = ImageDraw.Draw(sheet)
    f_lab = ImageFont.truetype(str(font_p), 20)
    f_sm = ImageFont.truetype(str(font_p), 15)
    f_head = ImageFont.truetype(str(font_p), 30)
    f_sub = ImageFont.truetype(str(font_p), round(96 * TW / 2560 * 1.0))  # 96 px at 2560 → scaled to the tile
    y = pad
    for skin, es, first in rows:
        if first:
            n_new = sum(1 for e in lib if e["skin"] == skin and not e.get("legacy"))
            d.text((pad, y + 6), f"{skin} · 新增 {n_new} 张 + legacy 3 张", font=f_head, fill=(30, 30, 30))
            y += head
        for j, e in enumerate(es):
            x = pad + j * (TW + pad)
            im = Image.open(root / e["file"]).convert("RGB").resize((TW, TH), Image.LANCZOS)
            td = ImageDraw.Draw(im)
            s = "字幕九十六像素可读"
            tw = td.textlength(s, font=f_sub)
            sy = round(1290 * TH / 1440)
            td.text(((TW - tw) / 2, sy), s, font=f_sub, fill=INK[skin])
            sheet.paste(im, (x, y))
            if e.get("legacy"):
                d.rectangle((x, y, x + 74, y + 24), fill=(60, 60, 60))
                d.text((x + 8, y + 2), "legacy", font=f_sm, fill=(255, 255, 255))
            d.text((x, y + TH + 5), f"{e['id']}  {e['name']['zh']}", font=f_lab, fill=(20, 20, 20))
            lic = e["license"] + ("" if e["source"]["kind"] != "commons" else " · Commons") + ("" if e["source"]["kind"] != "paper-shaders" else " · Paper Shaders")
            m = e.get("metrics") or {}
            d.text((x, y + TH + 31), f"{lic} · L̄={m.get('mean_lum', 0):.2f} · σ中={m.get('centre_std', 0):.3f}", font=f_sm, fill=(90, 90, 90))
        y += TH + cap + pad
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=86, optimize=True)
    print(f"{out} {sheet.size[0]}×{sheet.size[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
