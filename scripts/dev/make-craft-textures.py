#!/usr/bin/env python3
"""make-craft-textures.py · DEV-ONLY: regenerate the craft skins' locked paper / light-table rasters.

Ordinary users never run this. The finished files are committed under
assets/lecture-template/public/bg/ (backgrounds, 2560×1440 JPEG) and public/craft/ (tiles, PNG with alpha),
and registered with sha256 in manifests/visual-assets.json by --register.

Deterministic: every texture is a pure function of a fixed seed (numpy.random.default_rng(seed)).
Needs numpy + Pillow on the maintainer's machine only (not a runtime dependency).

    python scripts/dev/make-craft-textures.py [--register]

What is drawn (all calm in the central ~70 %, decoration only at edges):
  journal   warm cotton paper: 3 octaves of smooth value noise ±3.5 %, ~4000 short curved fibres, fine grain,
            soft vignette. chapter = a pale watercolour bloom in the lower-left corner; quiet = flattest.
  papercut  warm rice paper with long fibres and dye mottling. chapter = a red sawtooth border strip at the
            top edge; quiet = flattest.
  archive   backlit light table: cool near-white glow brightest at the centre, a faint ruler scale along the
            bottom edge, glass dust. chapter = a darker frame edge; quiet = glow only.
The method (value-noise paper + fibres) follows the paper recipe described in lemo-opuscar's
styles/watercolor/STYLE.md (MIT, © 2026 LemoLab) — re-implemented here, no code copied.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
TPL = ROOT / "assets" / "lecture-template"
BG = TPL / "public" / "bg"
CRAFT = TPL / "public" / "craft"
W, H = 2560, 1440


def value_noise(rng, w, h, cell):
    gw, gh = w // cell + 3, h // cell + 3
    g = rng.random((gh, gw)).astype(np.float32)
    img = Image.fromarray((g * 255).astype(np.uint8)).resize((gw * cell, gh * cell), Image.BICUBIC)
    a = np.asarray(img, dtype=np.float32)[:h, :w] / 255.0
    return a - 0.5


def octaves(rng, w, h, cells=(320, 110, 36), amps=(1.0, 0.55, 0.3)):
    out = np.zeros((h, w), np.float32)
    for c, a in zip(cells, amps):
        out += a * value_noise(rng, w, h, c)
    return out / sum(amps)


def fibres(rng, w, h, n, length, color, alpha, width=1):
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y = rng.random() * w, rng.random() * h
        ang = rng.random() * math.pi
        L = length * (0.4 + rng.random())
        bend = (rng.random() - 0.5) * 0.9
        pts = []
        for k in range(7):
            t = k / 6
            a = ang + bend * t
            pts.append((x + math.cos(a) * L * t, y + math.sin(a) * L * t))
        a = int(alpha * (0.35 + 0.65 * rng.random()))
        d.line(pts, fill=(*color, a), width=width)
    return layer


def grain(rng, w, h, amount):
    return (rng.standard_normal((h, w)).astype(np.float32) * amount)


def vignette(w, h, strength, power=2.2):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = (x / w - 0.5) * 2, (y / h - 0.5) * 2
    r = np.sqrt(nx ** 2 * 0.85 + ny ** 2)
    return 1 - strength * np.clip(r, 0, 1.5) ** power


def to_img(base_rgb, lum):
    arr = np.clip(np.array(base_rgb, np.float32)[None, None, :] * lum[..., None], 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def paper(seed, base, fibre_col, n_fibres, fibre_len, fibre_alpha, mottle=0.035, vig=0.06):
    rng = np.random.default_rng(seed)
    lum = 1 + mottle * octaves(rng, W, H) * 2 + grain(rng, W, H, 0.012)
    lum *= vignette(W, H, vig)
    img = to_img(base, lum).convert("RGBA")
    img.alpha_composite(fibres(rng, W, H, n_fibres, fibre_len, fibre_col, fibre_alpha))
    img.alpha_composite(fibres(rng, W, H, n_fibres // 3, fibre_len * 0.6, (255, 255, 255), fibre_alpha // 2))
    return img, rng


def wash_bloom(img, rng, cx, cy, rad, color, alpha):
    """A pale watercolour bloom: noisy-edged blob, darker rim (pooled edge), soft granulation."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - cx) / rad) ** 2 + ((y - cy) / (rad * 0.8)) ** 2)
    edge = 1 + 0.22 * octaves(rng, W, H, (180, 60, 20), (1, .6, .3)) * 2
    m = np.clip((edge - d) * 3.0, 0, 1)
    rim = np.clip(1 - np.abs(edge - d - 0.06) * 14, 0, 1) * 0.6
    a = np.clip((m * 0.55 + rim) * alpha * (1 + grain(rng, W, H, 0.25)), 0, 255).astype(np.uint8)
    layer = Image.new("RGBA", (W, H), (*color, 0))
    layer.putalpha(Image.fromarray(a))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.2)))


def sawtooth_strip(img, y0, h, color, tooth=28):
    d = ImageDraw.Draw(img)
    d.rectangle([0, y0 + tooth, W, y0 + h], fill=color)
    pts = [(0, y0 + tooth)]
    for i in range(W // tooth + 2):
        pts += [(i * tooth + tooth / 2, y0), ((i + 1) * tooth, y0 + tooth)]
    pts += [(W, y0 + h), (0, y0 + h)]
    d.polygon(pts, fill=color)
    # cut holes: a row of small crescents (window-flower vocabulary)
    for i in range(W // 120 + 1):
        cx, cy = i * 120 + 60, y0 + tooth + (h - tooth) / 2
        d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=(0, 0, 0, 0))
        d.ellipse([cx - 12, cy - 22, cx + 22, cy + 12], fill=color)


def light_table(seed, variant):
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H * 0.46) / (H * 0.62)) ** 2)
    glow = 1.0 - 0.10 * np.clip(r, 0, 1.4) ** 1.8
    lum = glow + grain(rng, W, H, 0.006) + 0.006 * octaves(rng, W, H, (400, 120, 40))
    img = to_img((238, 242, 244), lum).convert("RGBA")
    d = ImageDraw.Draw(img)
    # dust
    for _ in range(260):
        px, py = rng.random() * W, rng.random() * H
        s = rng.random() * 2.2 + 0.4
        d.ellipse([px - s, py - s, px + s, py + s], fill=(120, 130, 136, int(40 + 50 * rng.random())))
    if variant != "quiet":
        # ruler scale along the bottom edge (mm ticks), the table's own measuring strip
        y0 = H - 46
        for i in range(0, W, 12):
            L = 22 if i % 120 == 0 else (14 if i % 60 == 0 else 8)
            d.line([(i + 6, y0), (i + 6, y0 + L)], fill=(92, 104, 112, 150), width=2)
    if variant == "chapter":
        # dark frame edge of the light box (top + left), like the bezel around the glass
        fr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fr)
        fd.rectangle([0, 0, W, 34], fill=(46, 52, 58, 255))
        fd.rectangle([0, 0, 34, H], fill=(46, 52, 58, 255))
        img.alpha_composite(fr.filter(ImageFilter.GaussianBlur(3)))
    return img


def fibre_tile(seed, size=512):
    """Transparent paper-fibre tile for cards (overlay at low opacity, repeats seamlessly enough at 512)."""
    rng = np.random.default_rng(seed)
    t = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    t.alpha_composite(fibres(rng, size, size, 220, 22, (120, 96, 60), 60))
    t.alpha_composite(fibres(rng, size, size, 120, 16, (255, 255, 255), 90))
    g = (np.clip(grain(rng, size, size, 18) + 18, 0, 40)).astype(np.uint8)
    noise = Image.new("RGBA", (size, size), (90, 70, 40, 0))
    noise.putalpha(Image.fromarray(g))
    t.alpha_composite(noise)
    return t


def build() -> list[Path]:
    BG.mkdir(parents=True, exist_ok=True)
    CRAFT.mkdir(parents=True, exist_ok=True)
    out = []
    # journal
    for i, v in enumerate(("main", "chapter", "quiet")):
        img, rng = paper(100 + i, (243, 236, 221), (150, 120, 80), 4200 if v != "quiet" else 2600, 26, 46,
                         mottle=0.035 if v != "quiet" else 0.022, vig=0.07)
        if v == "chapter":
            wash_bloom(img, rng, W * 0.06, H * 0.92, 420, (120, 156, 170), 70)
            wash_bloom(img, rng, W * 0.95, H * 0.06, 260, (214, 150, 110), 55)
        p = BG / f"bg-journal-{v}.jpg"
        img.convert("RGB").save(p, quality=90, optimize=True)
        out.append(p)
    # papercut
    for i, v in enumerate(("main", "chapter", "quiet")):
        img, rng = paper(200 + i, (240, 228, 206), (170, 130, 90), 2600, 48, 40, mottle=0.04, vig=0.08)
        if v == "chapter":
            strip = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sawtooth_strip(strip, H - 92, 92, (196, 32, 30, 255))
            strip = strip.rotate(180)  # 放在上沿：下沿是字幕横批的位置，红压红会糊
            sh = strip.filter(ImageFilter.GaussianBlur(5))
            shadow = Image.new("RGBA", (W, H), (40, 10, 5, 0))
            shadow.putalpha(sh.getchannel("A").point(lambda a: a * 0.35))
            img.alpha_composite(shadow, (4, 5))
            img.alpha_composite(strip)
        p = BG / f"bg-papercut-{v}.jpg"
        img.convert("RGB").save(p, quality=90, optimize=True)
        out.append(p)
    # archive
    for i, v in enumerate(("main", "chapter", "quiet")):
        p = BG / f"bg-archive-{v}.jpg"
        light_table(300 + i, v).convert("RGB").save(p, quality=92, optimize=True)
        out.append(p)
    for name, img in (("fibre-tile.png", fibre_tile(400)),):  # 颜料颗粒改由 WashBlob 的 SVG feTurbulence 实时生成（3.3.0）
        p = CRAFT / name
        img.save(p, optimize=True)
        out.append(p)
    return out


def register(paths: list[Path]) -> None:
    """背景进 visual-assets.json + asset-manifest.json（与 flat / cel 背景同一登记方式）；纹理块进 public/craft/craft-manifest.json。"""
    man = TPL / "manifests" / "visual-assets.json"
    doc = json.loads(man.read_text(encoding="utf-8"))
    assets = doc.setdefault("assets", [])
    am_path = TPL / "manifests" / "asset-manifest.json"
    am = json.loads(am_path.read_text(encoding="utf-8"))
    tiles = {}
    for p in paths:
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        if p.parent.name == "craft":
            tiles[p.name] = sha
            continue
        rel = p.relative_to(TPL).as_posix()
        theme, variant = p.stem.split("-")[1], p.stem.split("-")[2]
        e = next((a for a in assets if a.get("id") == p.stem), None)
        if e is None:
            e = {"id": p.stem}
            assets.append(e)
        e.update({"path": rel, "source_type": "user-supplied",
                  "provider": "code-generated by scripts/dev/make-craft-textures.py (maintainer-only dev tool, fixed seed; no AI model)",
                  "prompt_summary": f"procedural {theme} texture, variant {variant}",
                  "use_context": f"{theme} theme Background variant '{variant}', 16:9 canvas, full-bleed Background layer",
                  "crop_policy": "cover-pixel-exact (2560x1440 = canvas)",
                  "rights": "project-owned (Apache-2.0, generated by this repository)", "baked_text": False, "sha256": sha})
        if p.stem not in am["visual_asset_ids"]:
            am["visual_asset_ids"].append(p.stem)
        for sc in am["scenes"]:
            ids = sc.setdefault("visual_asset_ids", [])
            if f"bg-flat-{variant}" in ids and p.stem not in ids:
                ids.append(p.stem)
    man.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    am_path.write_text(json.dumps(am, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (CRAFT / "craft-manifest.json").write_text(json.dumps({"tiles": tiles, "generator": "scripts/dev/make-craft-textures.py"}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ps = build()
    for p in ps:
        print(p.relative_to(ROOT), hashlib.sha256(p.read_bytes()).hexdigest()[:12])
    if "--register" in sys.argv:
        register(ps)
        print("registered in manifests/visual-assets.json")
