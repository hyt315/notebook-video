#!/usr/bin/env python3
"""make-bg-library.py · DEV-ONLY: build the background library (3.4.0) and its manifest.

Ordinary users never run this. The finished images (lossy WebP q82, ~⅓ the size of an equivalent JPEG) are committed under assets/lecture-template/public/bg/lib/
and described (source, licence, attribution, sha256, contrast metrics) in assets/lecture-template/manifests/backgrounds.json.

    python scripts/dev/make-bg-library.py [--ps DIR] [--only ID,…]

Three kinds of source, in the order we prefer them (no wheel reinvented where a good one exists):
  paper-shaders  Paper Shaders (@paper-design/shaders 0.0.82, Apache-2.0) pre-rendered ONCE to PNG by
                 scripts/dev/prerender-paper-shaders.py (spec: scripts/dev/paper-shaders.spec.json); renders never run WebGL.
  commons        Public-domain / CC0 textures from Wikimedia Commons (kraft paper, Poly Haven hessian, a 1630 map),
                 fetched through the Commons API with a polite User-Agent, cached, licence re-checked at fetch time.
  procedural     Deterministic drawing (numpy.random.default_rng(seed) + Pillow): rules, grids, sticky notes,
                 papercut motifs, film strips. Helpers shared with make-craft-textures.py (value-noise paper + fibres).
Every image is composed to 2560×1440, kept light (mean relative luminance ≥ 0.55), quiet in the central 70 % and
readable under the subtitle (see scripts/validate-backgrounds.py). Needs numpy + Pillow (maintainer machine only).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
TPL = ROOT / "assets" / "lecture-template"
LIB = TPL / "public" / "bg" / "lib"
MANIFEST = TPL / "manifests" / "backgrounds.json"
CACHE = Path(os.environ.get("NV_DEV_CACHE", Path.home() / ".cache" / "notebook-video"))
PS_DIR = CACHE / "paper-shaders" / "renders"
W, H = 2560, 1440
GEN = "scripts/dev/make-bg-library.py"
PS_PKG = "@paper-design/shaders@0.0.82"
UA = {"User-Agent": "notebook-video-dev/3.4 (https://github.com/hyt315/notebook-video; background library build)"}


def _load(name: str, file: Path):
    spec = importlib.util.spec_from_file_location(name, file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CT = _load("make_craft_textures", Path(__file__).with_name("make-craft-textures.py"))      # paper(), fibres(), octaves(), grain(), wash_bloom()
VB = _load("bg_metrics", Path(__file__).with_name("bg_metrics.py"))                   # measure(), ZONE

# ---------------------------------------------------------------------------------------------------------------
# Commons sources (licence as published on the file page; re-checked by fetch())
# ---------------------------------------------------------------------------------------------------------------
COMMONS = {
    "kraft": {"title": "File:Kraft tileable 1024x1024.png", "width": None, "license": "PD",
              "author": "Coyau (own work)", "license_as_published": "Public domain (released by the author)"},
    "hessian": {"title": "File:Hessian 380 diff 8k (Rico Cilliers and colormass via Poly Haven).jpg", "width": 2600, "license": "CC0-1.0",
                "author": "Rico Cilliers (processing), colormass (photography) via Poly Haven", "license_as_published": "CC0"},
    "holland": {"title": "File:Helmink Antique map of Holland by Anonymous 3rd state by Frederick de Wit 1630.jpg", "width": 3400, "license": "PD",
                "author": "Anonymous, 3rd state by Frederick de Wit (1630); scan Leen Helmink", "license_as_published": "Public domain (PD-old)"},
}


def fetch(key: str) -> tuple[Image.Image, dict]:
    c = COMMONS[key]
    d = CACHE / "commons"
    d.mkdir(parents=True, exist_ok=True)
    meta_p, img_p = d / f"{key}.json", d / f"{key}.bin"
    if not (meta_p.exists() and img_p.exists()):
        q = {"action": "query", "format": "json", "titles": c["title"], "prop": "imageinfo", "iiprop": "url|size|extmetadata"}
        if c["width"]:
            q["iiurlwidth"] = c["width"]
        r = json.load(urllib.request.urlopen(urllib.request.Request(
            "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(q), headers=UA), timeout=60))
        ii = next(iter(r["query"]["pages"].values()))["imageinfo"][0]
        lic = (ii["extmetadata"].get("LicenseShortName") or {}).get("value", "")
        if not any(t in lic for t in ("Public domain", "CC0")):
            raise SystemExit(f"{c['title']}: licence on Commons is now {lic!r}, not PD/CC0 — refusing")
        url = ii.get("thumburl") if c["width"] else ii["url"]
        time.sleep(1.0)
        img_p.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read())
        meta_p.write_text(json.dumps({"page": ii["descriptionurl"], "license_short": lic, "w": ii["width"], "h": ii["height"]}))
    meta = json.loads(meta_p.read_text())
    return Image.open(img_p).convert("RGB"), meta


# ---------------------------------------------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------------------------------------------
def ps(name: str, soften: float = 1.1) -> Image.Image:
    """A Paper Shaders render. `soften` blurs the 1-px grain a little: H.264 throws that frequency away anyway,
    and keeping it would triple the JPEG size for nothing visible in the delivered video."""
    p = PS_DIR / f"{name}.png"
    if not p.exists():
        raise SystemExit(f"missing Paper Shaders render {p} — run scripts/dev/prerender-paper-shaders.py first")
    im = Image.open(p).convert("RGB")
    return im.filter(ImageFilter.GaussianBlur(soften)) if soften else im


def arr(im: Image.Image) -> np.ndarray:
    return np.asarray(im, dtype=np.float32)


def img(a: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def toward(im: Image.Image, color, k: float) -> Image.Image:
    """Blend k of the way toward a flat colour (lightens / tints a texture while keeping its grain)."""
    return img(arr(im) * (1 - k) + np.array(color, np.float32) * k)


def relevel(im: Image.Image, white, depth: float) -> Image.Image:
    """Keep the texture's *relative* detail but anchor it to a paper white: out = white - depth*(max - in)."""
    a = arr(im)
    mx = np.percentile(a.reshape(-1, 3), 99.5, axis=0)
    return img(np.array(white, np.float32) - depth * (mx - a))


def tile(src: Image.Image, scale: float = 1.0) -> Image.Image:
    if scale != 1.0:
        src = src.resize((int(src.width * scale), int(src.height * scale)), Image.LANCZOS)
    out = Image.new("RGB", (W, H))
    for y in range(0, H, src.height):
        for x in range(0, W, src.width):
            out.paste(src, (x, y))
    return out


def cover(src: Image.Image, box=None) -> Image.Image:
    if box:
        src = src.crop(box)
    s = max(W / src.width, H / src.height)
    src = src.resize((math.ceil(src.width * s), math.ceil(src.height * s)), Image.LANCZOS)
    l, t = (src.width - W) // 2, (src.height - H) // 2
    return src.crop((l, t, l + W, t + H))


def vignette(im: Image.Image, strength: float, color=(60, 40, 20), power: float = 2.4) -> Image.Image:
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x / W - 0.5) * 2) ** 2 * 0.9 + ((y / H - 0.5) * 2) ** 2)
    k = (strength * np.clip(r / 1.3, 0, 1) ** power)[..., None]
    return img(arr(im) * (1 - k) + np.array(color, np.float32) * k)


class SS:
    """Supersampled RGBA overlay (2×) for anti-aliased lines and shapes; .paste() composites onto an RGB image."""
    def __init__(self, k: int = 2):
        self.k = k
        self.im = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def s(self, v):
        return [p * self.k for p in v] if isinstance(v, (list, tuple)) else v * self.k

    def line(self, pts, fill, width=1.0):
        self.d.line([(x * self.k, y * self.k) for x, y in pts], fill=fill, width=max(1, round(width * self.k)))

    def rect(self, box, fill=None, outline=None, width=1):
        self.d.rectangle(self.s(box), fill=fill, outline=outline, width=max(1, round(width * self.k)))

    def rrect(self, box, r, fill=None, outline=None, width=1):
        self.d.rounded_rectangle(self.s(box), r * self.k, fill=fill, outline=outline, width=max(1, round(width * self.k)))

    def ellipse(self, box, fill=None, outline=None, width=1):
        self.d.ellipse(self.s(box), fill=fill, outline=outline, width=max(1, round(width * self.k)))

    def poly(self, pts, fill=None, outline=None):
        self.d.polygon([(x * self.k, y * self.k) for x, y in pts], fill=fill, outline=outline)

    def layer(self, blur: float = 0) -> Image.Image:
        lay = self.im.resize((W, H), Image.LANCZOS)
        return lay.filter(ImageFilter.GaussianBlur(blur)) if blur else lay

    def paste(self, base: Image.Image, shadow: tuple | None = None) -> Image.Image:
        lay = self.layer()
        out = base.convert("RGBA")
        if shadow:  # (dx, dy, blur, alpha)
            dx, dy, bl, al = shadow
            a = lay.getchannel("A").filter(ImageFilter.GaussianBlur(bl)).point(lambda v: int(v * al))
            sh = Image.new("RGBA", (W, H), (50, 35, 20, 0))
            sh.putalpha(a)
            out.alpha_composite(sh, (dx, dy))
        out.alpha_composite(lay)
        return out.convert("RGB")


def rgba(hexs: str, a: float):
    h = hexs.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(255 * a))


def cream_paper(seed: int, base=(246, 240, 226), fib=2400, mottle=0.022) -> Image.Image:
    im, _ = CT.paper(seed, base, (150, 120, 80), fib, 24, 34, mottle=mottle, vig=0.05)
    return im.convert("RGB").filter(ImageFilter.GaussianBlur(1.4))


def dither(im: Image.Image, seed: int, amp: float = 1.2) -> Image.Image:
    """±1 LSB of fixed-seed noise: keeps 8-bit pastel gradients from banding after WebP / H.264."""
    return img(arr(im) + np.random.default_rng(seed).standard_normal((H, W, 1)).astype(np.float32) * amp)


def multiply(base: Image.Image, overlay: Image.Image) -> Image.Image:
    return ImageChops.multiply(base, overlay)


# ---------------------------------------------------------------------------------------------------------------
# recipes — each returns (Image, source dict, licence, attribution)
# ---------------------------------------------------------------------------------------------------------------
def src_proc(seed, note):
    return {"kind": "procedural", "generator": GEN, "seed": seed, "method": note}


def src_ps(shader_id, note):
    return {"kind": "paper-shaders", "package": PS_PKG, "generator": GEN, "prerender": "scripts/dev/prerender-paper-shaders.py",
            "spec": f"scripts/dev/paper-shaders.spec.json#{shader_id}", "upstream": "https://github.com/paper-design/shaders", "method": note}


def src_commons(key, note):
    c = COMMONS[key]
    meta = json.loads((CACHE / "commons" / f"{key}.json").read_text())
    return {"kind": "commons", "title": c["title"], "url": meta["page"], "author": c["author"],
            "license_as_published": c["license_as_published"], "generator": GEN, "method": note}


APACHE = ("Apache-2.0", "notebook-video contributors (generated)")


def journal_ruled():
    base = relevel(ps("ps-coldpress", 2.0), (250, 246, 236), 0.55)
    o = SS()
    for y in range(232, H - 40, 66):
        o.line([(0, y), (W, y)], rgba("#7fa6c8", 0.55), 2.2)
    o.line([(250, 0), (250, H)], rgba("#d0614f", 0.6), 2.2)
    o.line([(258, 0), (258, H)], rgba("#d0614f", 0.45), 1.6)
    return o.paste(base), src_ps("ps-coldpress", "cold-press paper + pale blue rules every 66 px from y=232, red double margin at x=250"), *APACHE


def journal_grid():
    base = relevel(ps("ps-coldpress", 2.0), (249, 247, 240), 0.5)
    o = SS()
    for x in range(0, W, 56):
        o.line([(x, 0), (x, H)], rgba("#8fb3a2", 0.42), 1.6)
    for y in range(0, H, 56):
        o.line([(0, y), (W, y)], rgba("#8fb3a2", 0.42), 1.6)
    # spiral binding along the left edge: punched holes + wire loops
    for y in range(70, H, 88):
        o.ellipse((34, y - 13, 60, y + 13), fill=rgba("#3a332c", 0.85))
        o.d.arc(o.s((-28, y - 22, 52, y + 18)), 250, 70, fill=rgba("#8d8f93", 1), width=7 * o.k)
        o.d.arc(o.s((-28, y - 22, 52, y + 18)), 255, 40, fill=rgba("#d5d7da", 1), width=3 * o.k)
    return o.paste(base, (2, 3, 3, 0.25)), src_ps("ps-coldpress", "cold-press paper + 5 mm green grid (56 px) + spiral binding on the left edge"), *APACHE


def journal_dots():
    base = cream_paper(1103, (247, 242, 230))
    o = SS()
    for y in range(60, H, 60):
        for x in range(60, W, 60):
            o.ellipse((x - 3, y - 3, x + 3, y + 3), fill=rgba("#8c7b66", 0.55))
    # elastic closure band on the right edge (bullet-journal notebook)
    o.rect((2448, 0, 2478, H), fill=rgba("#7a2e24", 0.95))
    o.rect((2448, 0, 2451, H), fill=rgba("#000000", 0.18))
    return o.paste(base, (-3, 0, 4, 0.35)), src_proc(1103, "value-noise cotton paper + 60 px dot grid + elastic closure band at the right edge"), *APACHE


def journal_kraft():
    k, _ = fetch("kraft")
    base = toward(tile(k), (247, 236, 214), 0.58)
    base = img(arr(base) + CT.grain(np.random.default_rng(1104), W, H, 2.0)[..., None])
    o = SS()
    # stitched spine: dashed thread along the left edge
    for y in range(20, H, 46):
        o.line([(70, y), (70, y + 26)], rgba("#f4ead6", 0.95), 4)
        o.line([(71, y + 1), (71, y + 27)], rgba("#5a3d22", 0.35), 1.5)
    return o.paste(base), src_commons("kraft", "Commons kraft tile (PD) tiled 2.5×, blended 58 % toward cream, saddle stitching on the left"), "PD", \
        "Kraft paper texture by Coyau, public domain, via Wikimedia Commons"


def journal_watercolor():
    base = relevel(ps("ps-coldpress", 1.4), (251, 248, 240), 0.9).convert("RGBA")
    rng = np.random.default_rng(1105)
    CT.wash_bloom(base, rng, W * 0.96, H * 0.02, 470, (104, 150, 182), 105)
    CT.wash_bloom(base, rng, W * 0.01, H * 1.00, 400, (214, 160, 84), 92)
    CT.wash_bloom(base, rng, W * 0.03, H * 0.04, 230, (190, 120, 140), 70)
    return base.convert("RGB"), src_ps("ps-coldpress", "Paper Shaders cold-press grain at full depth + three pale watercolour blooms in the corners"), *APACHE


def journal_sticky():
    base = cream_paper(1106, (246, 241, 229))
    notes = [((-30, -40, 300, 250), "#f7e27a", -6), ((2300, -60, 2620, 210), "#f5b8c4", 5),
             ((-150, 600, 150, 880), "#b9e2c9", 4), ((2420, 540, 2720, 820), "#b8d6f2", -5)]
    out = base
    for i, (box, col, rot) in enumerate(notes):
        o = SS(1)
        x0, y0, x1, y1 = box
        o.rect(box, fill=rgba(col, 1))
        o.rect((x0, y0, x1, y0 + 34), fill=rgba("#000000", 0.05))  # glue strip
        for yy in range(y0 + 90, y1 - 30, 42):  # faint pencil lines
            o.line([(x0 + 40, yy), (x1 - 50 - (yy * 13 % 60), yy)], rgba("#6b5a46", 0.22), 3)
        lay = o.layer().rotate(rot, center=((x0 + x1) / 2, (y0 + y1) / 2), resample=Image.BICUBIC)
        sh = Image.new("RGBA", (W, H), (60, 40, 20, 0))
        sh.putalpha(lay.getchannel("A").filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.28)))
        o2 = out.convert("RGBA")
        o2.alpha_composite(sh, (4, 7))
        o2.alpha_composite(lay)
        out = o2.convert("RGB")
    return out, src_proc(1106, "value-noise paper + four pastel sticky notes half off the edges (no text)"), *APACHE


def journal_oldpage():
    p = toward(ps("ps-oldpage"), (243, 232, 205), 0.55)
    p = relevel(p, (246, 236, 212), 1.0)
    p = vignette(p, 0.22, (150, 105, 50))
    rng = np.random.default_rng(1107)
    o = SS(1)
    for _ in range(140):  # foxing: small rust-brown spots, mostly near the edges
        x, y = rng.random() * W, rng.random() * H
        if max(abs(x / W - 0.5), abs(y / H - 0.5)) * 2 < 0.55 + 0.4 * rng.random():
            continue
        r = 2 + rng.random() * 9
        o.ellipse((x - r, y - r * 0.8, x + r, y + r * 0.8), fill=(150, 95, 40, int(30 + 50 * rng.random())))
    p = o.paste(p.filter(ImageFilter.GaussianBlur(0)))
    p = img(arr(p))
    x = np.arange(W, dtype=np.float32)[None, :, None]
    gutter = 1 - 0.16 * np.exp(-x / 70.0) - 0.05 * np.exp(-x / 260.0)   # binding shadow: this is the right-hand page of a book
    return img(arr(p) * gutter), src_ps("ps-oldpage", "Paper Shaders paper texture (fibre, foxing drops) softened 55 %, burnt-edge vignette, gutter shadow on the left"), *APACHE


def journal_graph():
    base = cream_paper(1108, (250, 248, 242), fib=1200, mottle=0.012)
    o = SS()
    for i, x in enumerate(range(0, W, 16)):
        o.line([(x, 0), (x, H)], rgba("#e39a6a", 0.55 if i % 5 == 0 else 0.22), 1.6 if i % 5 == 0 else 1.0)
    for i, y in enumerate(range(0, H, 16)):
        o.line([(0, y), (W, y)], rgba("#e39a6a", 0.55 if i % 5 == 0 else 0.22), 1.6 if i % 5 == 0 else 1.0)
    return o.paste(base), src_proc(1108, "millimetre graph paper: 16 px minor, 80 px major orange rules on near-white paper"), *APACHE


def papercut_hongzhi():
    base = relevel(ps("ps-xuan", 2.0), (250, 246, 236), 0.5)
    o = SS()
    red, top, side, bot, tooth = rgba("#c4231f", 1), 92, 92, 22, 22
    o.rect((0, 0, W, top), fill=red); o.rect((0, 0, side, H), fill=red); o.rect((W - side, 0, W, H), fill=red); o.rect((0, H - bot, W, H), fill=red)
    for x in range(side, W - side, tooth):  # sawtooth cut along the inner edge (top)
        o.poly([(x, top), (x + tooth / 2, top + 16), (x + tooth, top)], fill=red)
    for y in range(top, H - bot, tooth):
        o.poly([(side, y), (side + 16, y + tooth / 2), (side, y + tooth)], fill=red)
        o.poly([(W - side, y), (W - side - 16, y + tooth / 2), (W - side, y + tooth)], fill=red)
    lay = o.layer()
    holes = SS()
    for x in range(140, W - 100, 160):
        holes.poly([(x, 30), (x + 14, 46), (x, 62), (x - 14, 46)], fill=(255, 255, 255, 255))
        holes.ellipse((x + 66, 40, x + 78, 52), fill=(255, 255, 255, 255))
    a = ImageChops.subtract(lay.getchannel("A"), holes.layer().getchannel("A"))
    lay.putalpha(a)
    gold = SS()
    gold.rect((side + 26, top + 26, W - side - 26, H - bot - 6), outline=rgba("#c9a14a", 0.85), width=3)   # bottom rule at y≈1411, below the subtitle band
    out = base.convert("RGBA")
    sh = Image.new("RGBA", (W, H), (60, 10, 5, 0)); sh.putalpha(a.filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(v * 0.35)))
    out.alpha_composite(sh, (3, 5)); out.alpha_composite(lay); out.alpha_composite(gold.layer())
    return out.convert("RGB"), src_ps("ps-xuan", "xuan paper (Paper Shaders fibre) mounted in a red cut-paper frame with sawtooth inner edge, cut holes, gold rule"), *APACHE


def papercut_xuan():
    base = relevel(ps("ps-xuan"), (251, 248, 240), 0.75).convert("RGBA")
    rng = np.random.default_rng(1202)
    base.alpha_composite(CT.fibres(rng, W, H, 900, 70, (160, 135, 100), 34))
    o = SS()
    # a small red seal in the lower-right corner, outside the subtitle band
    o.rrect((2262, 1236, 2392, 1366), 10, fill=rgba("#b8261f", 0.9))
    o.rrect((2276, 1250, 2378, 1352), 6, outline=rgba("#fbf6ea", 0.9), width=5)
    o.line([(2327, 1262), (2327, 1340)], rgba("#fbf6ea", 0.9), 6); o.line([(2290, 1300), (2364, 1300)], rgba("#fbf6ea", 0.9), 6)
    return o.paste(base.convert("RGB")), src_ps("ps-xuan", "Paper Shaders long-fibre paper as xuan + 900 extra long fibres + small blank seal bottom-right"), *APACHE


def papercut_kraft():
    k, _ = fetch("kraft")
    base = toward(tile(k, 0.75), (250, 232, 206), 0.6)
    o = SS()
    # red string tie across the top-left corner, with a knot
    o.line([(0, 330), (420, 0)], rgba("#b8261f", 1), 9)
    o.line([(0, 360), (460, 0)], rgba("#b8261f", 1), 9)
    o.ellipse((166, 158, 214, 206), fill=rgba("#9e1d18", 1))
    o.line([(190, 182), (150, 300)], rgba("#b8261f", 1), 8); o.line([(190, 182), (236, 296)], rgba("#b8261f", 1), 8)
    return o.paste(base, (3, 5, 4, 0.3)), src_commons("kraft", "Commons kraft tile (PD) at 0.75× blended 60 % toward warm cream + red string tie top-left"), "PD", \
        "Kraft paper texture by Coyau, public domain, via Wikimedia Commons"


def papercut_origami():
    p = toward(ps("ps-origami"), (251, 241, 236), 0.5)
    return relevel(p, (251, 243, 238), 1.0), src_ps("ps-origami", "Paper Shaders crumple facets read as folded-paper creases, softened 50 % toward blush white"), *APACHE


def _rosette(o: SS, cx, cy, R, col, quarter=None):
    """Window-flower rosette: petals of a polar rose with cut-out rings and diamond holes (drawn as alpha holes later)."""
    pts = []
    for i in range(361):
        t = math.radians(i)
        r = R * (0.72 + 0.28 * abs(math.cos(4 * t)))
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    o.poly(pts, fill=col)


def papercut_lattice():
    base = relevel(ps("ps-xuan", 2.0), (251, 247, 238), 0.5)
    red = rgba("#c4231f", 1)
    o, holes = SS(), SS()
    for cx, cy, R in ((0, 0, 330), (W, 0, 330), (0, H, 250), (W, H, 250)):
        _rosette(o, cx, cy, R, red)
        for rr in (0.72, 0.48, 0.26):  # concentric cut rings
            holes.d.ellipse(holes.s((cx - R * rr, cy - R * rr, cx + R * rr, cy + R * rr)), outline=(255, 255, 255, 255), width=10 * holes.k)
        for k in range(16):  # radial diamond holes
            t = k * math.pi / 8
            for rr in (0.36, 0.60):
                x, y = cx + R * rr * math.cos(t), cy + R * rr * math.sin(t)
                holes.poly([(x, y - 13), (x + 9, y), (x, y + 13), (x - 9, y)], fill=(255, 255, 255, 255))
    lay = o.layer()
    a = ImageChops.subtract(lay.getchannel("A"), holes.layer().getchannel("A"))
    lay.putalpha(a)
    out = base.convert("RGBA")
    sh = Image.new("RGBA", (W, H), (60, 10, 5, 0)); sh.putalpha(a.filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(v * 0.35)))
    out.alpha_composite(sh, (3, 5)); out.alpha_composite(lay)
    return out.convert("RGB"), src_ps("ps-xuan", "xuan paper + four corner window-flower rosettes (polar rose, cut rings, diamond holes)"), *APACHE


def papercut_sajin():
    base = relevel(ps("ps-xuan", 2.0), (252, 246, 236), 0.45)
    rng = np.random.default_rng(1206)
    o = SS()
    for _ in range(2600):
        x, y = rng.random() * W, rng.random() * H
        # density: high at the edges, almost none in the centre
        d = max(abs(x / W - 0.5) * 2, abs(y / H - 0.5) * 2)
        if rng.random() > d ** 3:
            continue
        s = 3 + rng.random() * 10
        pts = [(x + s * math.cos(t) * (0.5 + rng.random()), y + s * math.sin(t) * (0.5 + rng.random()))
               for t in np.linspace(0, 2 * math.pi, 5 + int(rng.random() * 3), endpoint=False)]
        g = int(150 + rng.random() * 60)
        o.poly(pts, fill=(214, g, 70, int(160 + rng.random() * 90)))
    return o.paste(base), src_ps("ps-xuan", "xuan paper + gold-leaf flecks (sprinkled-gold paper), dense at the edges and fading to none in the centre"), *APACHE


def _cloud(o: SS, x, y, s, col):
    """Auspicious cloud (xiangyun): a body of overlapping circles with a curling tail."""
    for dx, dy, r in ((0, 0, 1.0), (1.2, -0.25, 0.8), (2.2, 0.1, 0.65), (-1.0, 0.2, 0.7), (0.6, 0.55, 0.6), (1.7, 0.5, 0.55)):
        o.ellipse((x + (dx - r) * s, y + (dy - r) * s, x + (dx + r) * s, y + (dy + r) * s), fill=col)


def papercut_cloud():
    base = relevel(ps("ps-xuan", 2.0), (251, 246, 237), 0.5)
    red = rgba("#c4231f", 1)
    o, holes = SS(), SS()
    for x, y, s in ((150, 150, 96), (2240, 150, 90), (560, 84, 52), (1880, 74, 48)):
        _cloud(o, x, y, s, red)
        for dx, dy, r in ((0, 0, 1.0), (1.2, -0.25, 0.8), (2.2, 0.1, 0.65), (-1.0, 0.2, 0.7)):
            cx, cy = x + dx * s, y + dy * s
            for k in (0.62, 0.34):
                holes.d.arc(holes.s((cx - r * s * k, cy - r * s * k, cx + r * s * k, cy + r * s * k)), 200, 520, fill=(255, 255, 255, 255), width=int(s * 0.12) * holes.k)
    lay = o.layer()
    a = ImageChops.subtract(lay.getchannel("A"), holes.layer().getchannel("A"))
    lay.putalpha(a)
    out = base.convert("RGBA")
    sh = Image.new("RGBA", (W, H), (60, 10, 5, 0)); sh.putalpha(a.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.3)))
    out.alpha_composite(sh, (3, 4)); out.alpha_composite(lay)
    return out.convert("RGB"), src_ps("ps-xuan", "xuan paper + four cut-paper auspicious clouds along the top edge (circle bodies, spiral cut lines)"), *APACHE


def papercut_menjian():
    base = relevel(ps("ps-xuan", 2.0), (251, 247, 238), 0.5)
    cols = ["#c4231f", "#e0567a", "#d9a13a", "#c4231f", "#3f7f5f"]
    o, holes = SS(), SS()
    o.line([(0, 22), (W, 22)], rgba("#7a4a2a", 0.9), 3)
    n, wf = 11, 170
    gap = (W - n * wf) / (n + 1)
    for i in range(n):
        x0 = gap + i * (wf + gap)
        col = rgba(cols[i % len(cols)], 1)
        y1 = 178
        pts = [(x0, 18), (x0 + wf, 18), (x0 + wf, y1)]
        for k in range(8, -1, -1):  # sawtooth tassel bottom
            pts.append((x0 + wf * k / 8, y1 + (14 if k % 2 else 0)))
        o.poly(pts, fill=col)
        cx = x0 + wf / 2
        holes.ellipse((cx - 30, 62, cx + 30, 122), outline=(255, 255, 255, 255), width=7)
        holes.poly([(cx, 76), (cx + 15, 92), (cx, 108), (cx - 15, 92)], fill=(255, 255, 255, 255))
        for dx in (-58, 58):
            holes.ellipse((cx + dx - 7, 85, cx + dx + 7, 99), fill=(255, 255, 255, 255))
        holes.line([(x0 + 12, 40), (x0 + wf - 12, 40)], (255, 255, 255, 255), 4)
        holes.line([(x0 + 12, 148), (x0 + wf - 12, 148)], (255, 255, 255, 255), 4)
    lay = o.layer()
    a = ImageChops.subtract(lay.getchannel("A"), holes.layer().getchannel("A"))
    lay.putalpha(a)
    out = base.convert("RGBA")
    sh = Image.new("RGBA", (W, H), (60, 10, 5, 0)); sh.putalpha(a.filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(v * 0.32)))
    out.alpha_composite(sh, (3, 6)); out.alpha_composite(lay)
    return out.convert("RGB"), src_ps("ps-xuan", "xuan paper + a row of hanging cut-paper door flags (menjian) along the top edge"), *APACHE


def archive_envelope():
    k, _ = fetch("kraft")
    base = toward(tile(k, 1.25), (246, 234, 210), 0.55)
    o = SS()
    # flap edge across the top and the string-and-button closure
    o.poly([(0, 0), (W, 0), (W, 120), (W / 2 + 140, 196), (W / 2 - 140, 196), (0, 120)], fill=rgba("#c9a46e", 0.55))
    o.line([(0, 120), (W / 2 - 140, 196), (W / 2 + 140, 196), (W, 120)], rgba("#7a5a32", 0.45), 3)
    for cx, cy in ((W / 2, 196), (W / 2, 300)):
        o.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=rgba("#8b6a42", 1))
        o.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=rgba("#e9dcc0", 1))
    o.line([(W / 2, 196), (W / 2 - 26, 250), (W / 2, 300), (W / 2 + 28, 248), (W / 2, 196)], rgba("#efe3c8", 1), 5)
    # faint blank stamp frame top-right
    o.rrect((2190, 240, 2470, 360), 8, outline=rgba("#a3382c", 0.45), width=5)
    o.line([(2210, 300), (2450, 300)], rgba("#a3382c", 0.35), 3)
    return o.paste(base, (2, 4, 3, 0.3)), src_commons("kraft", "Commons kraft tile (PD) at 1.25× lightened 55 %, envelope flap, string-and-button closure, blank stamp frame"), "PD", \
        "Kraft paper texture by Coyau, public domain, via Wikimedia Commons"


def archive_newsprint():
    rng = np.random.default_rng(1302)
    base = cream_paper(1302, (240, 236, 224), fib=800, mottle=0.03)
    o = SS(1)
    o.rect((120, 70, W - 120, 78), fill=rgba("#2a2a2a", 0.32)); o.rect((120, 86, W - 120, 89), fill=rgba("#2a2a2a", 0.32))
    o.rect((120, 104, W - 120, 106), fill=rgba("#2a2a2a", 0.22))
    cols, x0, gw = 6, 120, (W - 240)
    cw = (gw - 5 * 40) / cols
    for c in range(cols):
        cx = x0 + c * (cw + 40)
        if c:
            o.line([(cx - 20, 140), (cx - 20, H - 60)], rgba("#2a2a2a", 0.14), 2)
        y = 150
        while y < H - 70:
            if rng.random() < 0.06:  # headline block
                o.rect((cx, y, cx + cw * (0.6 + 0.35 * rng.random()), y + 26), fill=rgba("#2a2a2a", 0.16)); y += 48; continue
            ln = cw * (1.0 if rng.random() > 0.12 else 0.3 + 0.5 * rng.random())
            o.rect((cx, y, cx + ln, y + 9), fill=rgba("#2a2a2a", 0.085)); y += 21
    lay = o.layer(0.6)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    calm = 1 - 0.7 * np.exp(-(((x - W / 2) / (W * 0.34)) ** 2 + ((y - H * 0.5) / (H * 0.36)) ** 2))   # print fades where the content sits
    lay.putalpha(Image.fromarray((np.asarray(lay.getchannel("A"), np.float32) * calm).astype(np.uint8)))
    out = base.convert("RGBA"); out.alpha_composite(lay)
    return vignette(out.convert("RGB"), 0.16, (170, 150, 110)), src_proc(1302, "newsprint: greeked six-column page (grey bars, no real text), masthead rules, yellowed edges"), *APACHE


def archive_map():
    m, _ = fetch("holland")
    m = cover(m, (int(m.width * 0.16), int(m.height * 0.24), int(m.width * 0.84), int(m.height * 0.80)))
    g = np.asarray(m.convert("L").filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float32) / 255.0
    paper = np.array((243, 236, 218), np.float32)
    inkc = np.array((120, 95, 60), np.float32)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x / W - 0.5) * 2) ** 2 + ((y / H - 0.5) * 2) ** 2)
    depth = 0.10 + 0.18 * np.clip(r / 1.2, 0, 1) ** 1.6     # faint in the centre, a little stronger at the edges
    darkness = (1 - g) * depth
    out = paper[None, None, :] * (1 - darkness[..., None]) + inkc * darkness[..., None]
    return vignette(img(out), 0.12, (150, 115, 70)), src_commons("holland", "1630 map of Holland (PD) cropped to the land/sea interior, desaturated, ink at 10–28 % over parchment"), "PD", \
        "Map of Holland, anonymous, 3rd state by Frederick de Wit (1630), public domain, via Wikimedia Commons (scan: Leen Helmink)"


def archive_catalog():
    base = relevel(ps("ps-laid", 2.0), (252, 249, 240), 0.45)
    o = SS()
    o.line([(0, 214), (W, 214)], rgba("#d0614f", 0.75), 3)
    for y in range(290, H - 30, 72):
        o.line([(0, y), (W, y)], rgba("#7fa6c8", 0.5), 2)
    o.ellipse((W / 2 - 44, 56, W / 2 + 44, 144), fill=rgba("#cfc8b8", 1))   # rod hole at the top
    o.ellipse((W / 2 - 44, 56, W / 2 + 44, 144), outline=rgba("#9d9484", 1), width=3)
    return o.paste(base), src_ps("ps-laid", "Paper Shaders laid-paper rows as an index card: red header rule, blue rules, catalogue rod hole at the top"), *APACHE


def archive_filmstrip():
    rng = np.random.default_rng(1305)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H * 0.46) / (H * 0.62)) ** 2)
    lum = 1.0 - 0.08 * np.clip(r, 0, 1.4) ** 1.8 + CT.grain(rng, W, H, 0.005)
    base = CT.to_img((240, 244, 246), lum)
    o = SS()
    for x0 in (0, W - 176):
        o.rect((x0, 0, x0 + 176, H), fill=rgba("#c98a3e", 0.5))
        for yy in range(10, H, 38):
            o.rrect((x0 + 14, yy, x0 + 36, yy + 22), 4, fill=rgba("#f4f6f7", 1))
            o.rrect((x0 + 140, yy, x0 + 162, yy + 22), 4, fill=rgba("#f4f6f7", 1))
        for yy in range(0, H, 240):
            o.rect((x0 + 48, yy + 8, x0 + 128, yy + 228), fill=rgba("#e7b277", 0.45))
    return o.paste(base), src_proc(1305, "light table + two amber film strips (sprocket holes, empty frames) down the left and right edges"), *APACHE


def archive_linen():
    h, _ = fetch("hessian")
    h = cover(h).filter(ImageFilter.GaussianBlur(1.0))
    base = relevel(toward(h, (236, 228, 212), 0.2), (244, 238, 226), 0.62)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    spot = 1 + 0.06 * np.exp(-(((x - W / 2) / (W * 0.45)) ** 2 + ((y - H * 0.35) / (H * 0.6)) ** 2))
    return img(arr(base) * spot[..., None]), src_commons("hessian", "Poly Haven hessian 380 diffuse (CC0) lightened to pale linen, vitrine spotlight from the top"), "CC0-1.0", \
        "Hessian 380 by Rico Cilliers & colormass (Poly Haven), CC0, via Wikimedia Commons"


def archive_ledger():
    base = cream_paper(1307, (243, 246, 234), fib=1000, mottle=0.015)
    o = SS()
    for y in range(250, H - 20, 54):
        o.line([(0, y), (W, y)], rgba("#8fb59a", 0.5), 1.8)
    for xx in (300, 1720, 1960, 2200):
        o.line([(xx, 160), (xx, H)], rgba("#c45a4a", 0.55), 2)
        o.line([(xx + 7, 160), (xx + 7, H)], rgba("#c45a4a", 0.4), 1.4)
    o.line([(0, 160), (W, 160)], rgba("#5f8f6c", 0.7), 3); o.line([(0, 170), (W, 170)], rgba("#5f8f6c", 0.5), 1.5)
    return o.paste(base), src_proc(1307, "ledger paper: pale green rules, red double money columns, double header rule"), *APACHE


def archive_vellum():
    base = cream_paper(1308, (238, 241, 243), fib=400, mottle=0.01)
    g = SS()
    for x in range(0, W, 64):
        g.line([(x, 0), (x, H)], rgba("#5b7387", 0.5), 2)
    for y in range(0, H, 64):
        g.line([(0, y), (W, y)], rgba("#5b7387", 0.5), 2)
    under = g.layer(3.5)  # the grid sits *under* frosted tracing paper: blurred and faint
    under.putalpha(under.getchannel("A").point(lambda v: int(v * 0.42)))
    out = base.convert("RGBA"); out.alpha_composite(under)
    o = SS()
    for cx, cy, rot in ((120, 60, -32), (W - 120, 60, 32)):
        tape = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(tape).rectangle((cx - 120, cy - 22, cx + 120, cy + 22), fill=(230, 214, 168, 225))
        tape = tape.rotate(rot, center=(cx, cy), resample=Image.BICUBIC)
        out.alpha_composite(tape)
    return o.paste(out.convert("RGB")), src_proc(1308, "frosted tracing vellum over a blurred 64 px grid, masking tape on the top corners"), *APACHE


def flat_mesh_dawn():
    return dither(ps("ps-mesh-dawn", 0), 1401), src_ps("ps-mesh-dawn", "Paper Shaders static mesh gradient, five pastel spots (peach, sky, blush, cream, mint)"), *APACHE


def flat_mesh_mint():
    return dither(ps("ps-mesh-mint", 0), 1402), src_ps("ps-mesh-mint", "Paper Shaders static mesh gradient, mint / sky / lemon"), *APACHE


def flat_dotgrid():
    return ps("ps-dotgrid", 0), src_ps("ps-dotgrid", "Paper Shaders dot grid, pale blue dots on cool white"), *APACHE


def flat_sunrise():
    return toward(ps("ps-grain-sun", 0.6), (253, 248, 240), 0.45), src_ps("ps-grain-sun", "Paper Shaders grain gradient (corners) peach / apricot, softened 45 % (its own grain prevents banding)"), *APACHE


def flat_shapes():
    base = img(np.full((H, W, 3), (247, 249, 252), np.float32))
    o = SS()
    o.ellipse((-160, -160, 260, 260), fill=rgba("#ffd77a", 0.9))
    o.rrect((2300, -60, 2640, 260), 60, fill=rgba("#9fd3c7", 0.9))
    o.ellipse((2380, 1150, 2760, 1530), fill=rgba("#ffb4a2", 0.85))
    o.poly([(-40, 1440), (240, 1440), (-40, 1150)], fill=rgba("#a9c5ff", 0.9))
    for x, y, c in ((330, 120, "#ffb4a2"), (2180, 300, "#ffd77a"), (190, 1010, "#9fd3c7")):
        o.ellipse((x - 14, y - 14, x + 14, y + 14), fill=rgba(c, 1))
    return o.paste(base), src_proc(1405, "flat pastel geometry in the four corners (circle, rounded square, triangle) on cool white"), *APACHE


def cel_halftone():
    return ps("ps-halftone-corners", 0.5), src_ps("ps-halftone-corners", "Paper Shaders halftone dots (hex grid) driven by corner blobs: ink-blue screentone in the corners"), *APACHE


def cel_speedlines():
    base = img(np.full((H, W, 3), (251, 249, 244), np.float32))
    rng = np.random.default_rng(1502)
    o = SS()
    cx, cy = W / 2, H * 0.46
    for _ in range(170):
        t = rng.random() * 2 * math.pi
        r0 = 0.78 + 0.25 * rng.random()
        ex, ey = math.cos(t), math.sin(t)
        # start outside an ellipse that covers the centre, run to beyond the frame
        x0, y0 = cx + ex * W * 0.5 * r0, cy + ey * H * 0.5 * r0
        x1, y1 = cx + ex * W * 0.9, cy + ey * H * 0.9
        wdt = 1.5 + rng.random() * 5
        o.poly([(x0, y0), (x1 - ey * wdt * 3, y1 + ex * wdt * 3), (x1 + ey * wdt * 3, y1 - ex * wdt * 3)], fill=rgba("#111111", 0.75))
    out = o.paste(base)
    a = arr(out)  # keep the subtitle band clean: lighten lines there
    yy = np.arange(H)[:, None, None]
    fade = np.clip((yy - 1180) / 60, 0, 1) * 0.85
    a = a * (1 - fade) + np.array((251, 249, 244), np.float32) * fade
    return img(a), src_proc(1502, "manga focus lines from the frame edge, centre and subtitle band left clear"), *APACHE


def cel_panels():
    base = img(np.full((H, W, 3), (226, 226, 222), np.float32))   # page margin
    o = SS()
    ink, white = rgba("#111111", 1), rgba("#fbfaf6", 1)
    o.rect((56, 56, W - 56, H - 22), fill=white, outline=ink, width=9)              # one big open panel = the stage
    o.rect((56, 56, 560, 330), fill=rgba("#ffffff", 1), outline=ink, width=9)        # inset panel top-left: a sun
    o.ellipse((150, 108, 290, 248), fill=rgba("#f2c94c", 1), outline=ink, width=6)
    for k in range(12):
        t = k * math.pi / 6
        o.line([(220 + 86 * math.cos(t), 178 + 86 * math.sin(t)), (220 + 118 * math.cos(t), 178 + 118 * math.sin(t))], ink, 6)
    o.rect((2120, 56, W - 56, 280), fill=rgba("#ffffff", 1), outline=ink, width=9)   # inset panel top-right: rain hatch
    for i in range(9):
        o.line([(2150 + i * 40, 80), (2200 + i * 40, 256)], rgba("#111111", 0.7), 5)
    return o.paste(base), src_proc(1503, "manga page: one big open panel as the stage, two small inset panels in the top corners (sun, rain hatch)"), *APACHE


def cel_screentone():
    base = img(np.full((H, W, 3), (252, 251, 248), np.float32))
    o = SS()
    step = 22
    for y in range(0, H + step, step):
        for x in range(0 if (y // step) % 2 == 0 else step // 2, W + step, step):
            nx, ny = (x / W - 0.5) * 2, (y / H - 0.5) * 2
            d = math.sqrt(nx * nx * 0.75 + ny * ny * 0.9)          # elliptical: no hard box edge
            t = min(1.0, max(0.0, (d - 0.66) / 0.5))
            t = t * t * (3 - 2 * t)
            if y > 1150:  # soften (do not cut) under the subtitle band
                inside = min(1.0, max(0.0, (x - 200) / 260)) * min(1.0, max(0.0, (2360 - x) / 260))   # smooth in x too: no notch
                t *= 1 - 0.65 * min(1.0, (y - 1150) / 80) * inside
            r = 6.2 * t
            if r < 0.7:
                continue
            o.ellipse((x - r, y - r, x + r, y + r), fill=rgba("#6b7280", 0.6))
    return o.paste(base), src_proc(1504, "hand-laid screentone: dot radius grows smoothly from nothing inside a central ellipse to full at the edges"), *APACHE


def cel_sunburst():
    base = img(np.full((H, W, 3), (255, 250, 236), np.float32))
    o = SS()
    cx, cy = W / 2, -260
    n = 36
    for i in range(n):
        if i % 2:
            continue
        t0, t1 = math.pi * i / n, math.pi * (i + 1) / n
        o.poly([(cx, cy), (cx + math.cos(t0) * 4000, cy + math.sin(t0) * 4000), (cx + math.cos(t1) * 4000, cy + math.sin(t1) * 4000)],
               fill=rgba("#ffd84d", 0.42))
    out = arr(o.paste(base))
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    calm = np.exp(-(((x - W / 2) / (W * 0.30)) ** 2 + ((y - H * 0.52) / (H * 0.36)) ** 2))[..., None] * 0.8   # rays fade out behind the content
    out = out * (1 - calm) + np.array((255, 250, 236), np.float32) * calm
    return img(out), src_proc(1505, "pale yellow sunburst rays fanning down from above the frame (shoujo / title-card backdrop)"), *APACHE


# id, recipe, Chinese name, English name, roles
RECIPES = [
    ("journal/ruled", journal_ruled, "横线本", "ruled notebook", ["main", "quiet"]),
    ("journal/grid", journal_grid, "方格本（线圈）", "spiral grid notebook", ["main", "chapter"]),
    ("journal/dots", journal_dots, "点阵本", "dot-grid journal", ["main", "quiet"]),
    ("journal/kraft", journal_kraft, "牛皮纸本", "kraft notebook", ["main", "chapter"]),
    ("journal/watercolor", journal_watercolor, "水彩纸", "cold-press watercolour paper", ["chapter", "main"]),
    ("journal/sticky", journal_sticky, "便签墙", "sticky-note wall", ["chapter", "main"]),
    ("journal/oldpage", journal_oldpage, "旧书页", "foxed old page", ["main", "chapter"]),
    ("journal/graph", journal_graph, "坐标纸", "millimetre graph paper", ["quiet", "main"]),
    ("papercut/hongzhi", papercut_hongzhi, "红纸衬边", "red paper mount", ["chapter"]),
    ("papercut/xuan", papercut_xuan, "宣纸", "xuan paper", ["main", "quiet"]),
    ("papercut/kraft", papercut_kraft, "牛皮纸·红绳", "kraft with red string", ["main", "chapter"]),
    ("papercut/origami", papercut_origami, "折纸纹", "folded-paper creases", ["main", "quiet"]),
    ("papercut/lattice", papercut_lattice, "窗花角", "window-flower corners", ["chapter", "main"]),
    ("papercut/sajin", papercut_sajin, "洒金笺", "gold-fleck paper", ["main", "chapter"]),
    ("papercut/cloud", papercut_cloud, "祥云", "auspicious clouds", ["chapter", "main"]),
    ("papercut/menjian", papercut_menjian, "挂笺", "hanging door flags", ["chapter"]),
    ("archive/envelope", archive_envelope, "档案袋", "archive envelope", ["chapter", "main"]),
    ("archive/newsprint", archive_newsprint, "旧报纸", "old newsprint", ["main"]),
    ("archive/map", archive_map, "古地图", "antique map", ["chapter", "main"]),
    ("archive/catalog", archive_catalog, "卡片目录", "catalogue card", ["main", "quiet"]),
    ("archive/filmstrip", archive_filmstrip, "胶片灯箱", "film strips on a light table", ["main", "chapter"]),
    ("archive/linen", archive_linen, "展柜布面", "vitrine linen", ["main", "quiet"]),
    ("archive/ledger", archive_ledger, "登记簿", "ledger paper", ["quiet", "main"]),
    ("archive/vellum", archive_vellum, "描图纸", "tracing vellum", ["quiet", "main"]),
    ("flat/mesh-dawn", flat_mesh_dawn, "晨光渐变", "dawn mesh gradient", ["main", "quiet"]),
    ("flat/mesh-mint", flat_mesh_mint, "薄荷渐变", "mint mesh gradient", ["main", "quiet"]),
    ("flat/dotgrid", flat_dotgrid, "点阵", "dot grid", ["quiet", "main"]),
    ("flat/sunrise", flat_sunrise, "暖角渐变", "warm corner gradient", ["chapter", "main"]),
    ("flat/shapes", flat_shapes, "几何角饰", "corner shapes", ["chapter", "main"]),
    ("cel/halftone", cel_halftone, "网点角", "halftone corners", ["main", "chapter"]),
    ("cel/speedlines", cel_speedlines, "集中线", "focus lines", ["chapter"]),
    ("cel/panels", cel_panels, "分格边", "panel border", ["main", "chapter"]),
    ("cel/screentone", cel_screentone, "渐变网点", "screentone fade", ["main", "quiet"]),
    ("cel/sunburst", cel_sunburst, "放射光", "sunburst", ["chapter"]),
]

# Smooth pastel gradients keep their ±1 LSB dither only at a high WebP quality (q82 smooths it into 8×8 steps).
QUALITY = {"flat/mesh-dawn": 95, "flat/mesh-mint": 95}

LEGACY_NAMES = {
    "flat": ("天空吉祥物", "sky with mascots"), "cel": ("漫画角饰", "comic corner bursts"),
    "journal": ("棉纸", "cotton paper"), "papercut": ("米纸", "rice paper"), "archive": ("灯箱", "light table"),
}


def legacy_entries() -> list[dict]:
    """The 3.3.0 main / chapter / quiet rasters join the library unchanged (legacy: role)."""
    va = {a["id"]: a for a in json.loads((TPL / "manifests" / "visual-assets.json").read_text(encoding="utf-8"))["assets"]}
    out = []
    for skin in ("flat", "cel", "journal", "papercut", "archive"):
        zh, en = LEGACY_NAMES[skin]
        for role in ("main", "chapter", "quiet"):
            rel = f"public/bg/bg-{skin}-{role}.jpg"
            a = va.get(f"bg-{skin}-{role}", {})
            ai = a.get("source_type") == "ai-generated"
            out.append({
                "id": f"{skin}/{role}", "skin": skin, "file": rel, "legacy": role,
                "name": {"zh": f"{zh}·{ {'main': '常规', 'chapter': '章节', 'quiet': '安静'}[role]}", "en": f"{en} ({role})"},
                "roles": [role],
                "source": {"kind": "ai-generated" if ai else "procedural",
                           "generator": "Hark generate_image + scripted NumPy recomposition (see visual-assets.json)" if ai else "scripts/dev/make-craft-textures.py",
                           "method": a.get("prompt_summary", "")},
                "license": "Apache-2.0", "attribution": "notebook-video contributors" + (" (AI-generated, project-owned)" if ai else " (generated)"),
            })
    return out


def main() -> int:
    only = set()
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    global PS_DIR
    if "--ps" in sys.argv:
        PS_DIR = Path(sys.argv[sys.argv.index("--ps") + 1])
    LIB.mkdir(parents=True, exist_ok=True)
    old = {e["id"]: e for e in json.loads(MANIFEST.read_text(encoding="utf-8"))["backgrounds"]} if MANIFEST.exists() else {}
    entries = []
    for e in legacy_entries():
        e["sha256"] = hashlib.sha256((TPL / e["file"]).read_bytes()).hexdigest()
        e["metrics"] = old.get(e["id"], {}).get("metrics") if old.get(e["id"], {}).get("sha256") == e["sha256"] else VB.measure(TPL / e["file"])
        entries.append(e)
    for bid, fn, zh, en, roles in RECIPES:
        skin, name = bid.split("/")
        rel = f"public/bg/lib/{skin}-{name}.webp"
        p = TPL / rel
        if not only or bid in only or not p.exists() or bid not in old:
            im, source, lic, attribution = fn()
            assert im.size == (W, H), (bid, im.size)
            im.convert("RGB").save(p, "WEBP", quality=QUALITY.get(bid, 82), method=6)
            print(f"  built {bid:<22} {p.stat().st_size // 1024:>4} KB")
        else:
            prev = old[bid]
            source, lic, attribution = prev["source"], prev["license"], prev["attribution"]
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        metrics = old.get(bid, {}).get("metrics") if old.get(bid, {}).get("sha256") == sha else VB.measure(p)
        entries.append({"id": bid, "skin": skin, "file": rel, "name": {"zh": zh, "en": en}, "roles": roles,
                        "source": source, "license": lic, "attribution": attribution, "sha256": sha, "metrics": metrics})
    doc = {
        "$comment": "Background library (3.4.0). Generated by scripts/dev/make-bg-library.py — edit recipes there, not here. "
                    "A shot picks one by `bg` in manifests/shots.json (full id 'journal/ruled' or short 'ruled'); without `bg` "
                    "resolve-shots rotates through the entries whose roles include the shot's role, never repeating the previous shot. "
                    "Checked by scripts/validate-backgrounds.py (source + licence + sha256 + light + subtitle contrast).",
        "version": 1,
        "subtitle_zone": {"x0": VB.ZONE[0], "y0": VB.ZONE[1], "x1": VB.ZONE[2], "y1": VB.ZONE[3], "canvas": [W, H]},
        "backgrounds": entries,
    }
    MANIFEST.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum((TPL / e["file"]).stat().st_size for e in entries if not e.get("legacy"))
    print(f"wrote {MANIFEST.relative_to(ROOT)} · {len(entries)} entries · library WebP {total / 1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
