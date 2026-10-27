#!/usr/bin/env python3
"""prerender-paper-shaders.py · DEV-ONLY: render Paper Shaders (Apache-2.0) to static PNGs, once, offline.

Why: Paper Shaders (https://github.com/paper-design/shaders, @paper-design/shaders) draws the best procedural
paper / grain / mesh-gradient / halftone textures we found, but it is WebGL. Running WebGL on every frame of a
render costs a lot on CPU-only machines (SwiftShader) and makes frames depend on the GPU stack. A background is
static, so we render each shader exactly once at 2560×1440 and commit the composed JPEG
(scripts/dev/make-bg-library.py). Renders never touch WebGL; ordinary users never run this script.

Needs (maintainer machine only): Node + npm (to fetch the pinned package and esbuild), Python `playwright`
with a Chromium (`pip install playwright && playwright install chromium`).

    python scripts/dev/prerender-paper-shaders.py [--spec scripts/dev/paper-shaders.spec.json] [--out DIR] [--only NAME,…]

Output: DIR/<name>.png (RGBA, 2560×1440 unless the spec says otherwise). Deterministic: every shader is static
(speed 0, fixed frame, fixed seed uniforms), so the same spec and package version give the same pixels on the same
renderer (SwiftShader); tiny cross-GPU differences do not matter because only the committed JPEG is used.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = "@paper-design/shaders@0.0.82"  # pinned: 0.0.x API is not stable yet
CACHE = Path(os.environ.get("NV_DEV_CACHE", Path.home() / ".cache" / "notebook-video")) / "paper-shaders"

JS = r"""
async ({shader, params, w, h, image}) => {
  const P = window.PS; const root = document.getElementById('root');
  root.innerHTML = ''; root.style.width = w + 'px'; root.style.height = h + 'px';
  const u = {u_fit:0,u_scale:1,u_rotation:0,u_originX:.5,u_originY:.5,u_offsetX:0,u_offsetY:0,u_worldWidth:0,u_worldHeight:0};
  for (const [k, v] of Object.entries(params)) {
    if (typeof v === 'string' && (v.startsWith('#') || v.startsWith('rgb'))) u[k] = P.getShaderColorFromString(v);
    else if (Array.isArray(v) && typeof v[0] === 'string') u[k] = v.map((c) => P.getShaderColorFromString(c));
    else u[k] = v;
  }
  const load = (src) => new Promise((r) => { const i = new Image(); i.onload = () => r(i); i.src = src; });
  u.u_noiseTexture = await load(P.getShaderNoiseTexture().src);
  if (image) {  // procedural source image for image-filter shaders (halftone): white field with dark radial blobs
    const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d');
    g.fillStyle = '#fff'; g.fillRect(0, 0, w, h);
    for (const [x, y, r] of image.blobs) {
      const gr = g.createRadialGradient(x * w, y * h, 0, x * w, y * h, r * w);
      gr.addColorStop(0, 'rgba(0,0,0,' + (image.peak ?? 0.85) + ')'); gr.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = gr; g.fillRect(0, 0, w, h);
    }
    u.u_image = await load(c.toDataURL('image/png')); u.u_imageAspectRatio = w / h;
  } else if (!('u_image' in u)) { u.u_image = await load(P.emptyPixel); }
  new P.ShaderMount(root, P[shader + 'FragmentShader'], u, {preserveDrawingBuffer: true, antialias: true}, 0, params.frame || 0, 1, w * h * 4);
  await new Promise((r) => setTimeout(r, 1200));
  return root.querySelector('canvas').toDataURL('image/png');
}
"""


def bundle() -> Path:
    out = CACHE / "ps.bundle.js"
    if out.exists():
        return out
    CACHE.mkdir(parents=True, exist_ok=True)
    npm = shutil.which("npm") or "npm"
    (CACHE / "package.json").write_text('{"private":true}\n')
    subprocess.run([npm, "i", "--no-audit", "--no-fund", PKG, "esbuild@0.25"], cwd=CACHE, check=True)
    (CACHE / "entry.js").write_text("import * as S from '@paper-design/shaders';\nwindow.PS = S;\n")
    esb = CACHE / "node_modules" / ".bin" / ("esbuild.cmd" if os.name == "nt" else "esbuild")
    subprocess.run([str(esb), "entry.js", "--bundle", "--format=iife", f"--outfile={out}"], cwd=CACHE, check=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=str(ROOT / "scripts" / "dev" / "paper-shaders.spec.json"))
    ap.add_argument("--out", default=str(CACHE / "renders"))
    ap.add_argument("--only", default="")
    ap.add_argument("--bundle", default="")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright  # dev-only dependency
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))["shaders"]
    only = {s for s in a.only.split(",") if s}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    js_bundle = Path(a.bundle) if a.bundle else bundle()
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = b.new_page(viewport={"width": 2600, "height": 1500}, device_scale_factor=1)
        pg.set_content('<html><body style="margin:0;background:#fff"><div id="root"></div></body></html>')
        pg.add_script_tag(content=js_bundle.read_text(encoding="utf-8"))
        for name, s in spec.items():
            if only and name not in only:
                continue
            url = pg.evaluate(JS, {"shader": s["shader"], "params": s["params"], "w": s.get("w", 2560), "h": s.get("h", 1440),
                                   "image": s.get("image")})
            (out / f"{name}.png").write_bytes(base64.b64decode(url.split(",", 1)[1]))
            print("rendered", name)
        b.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
