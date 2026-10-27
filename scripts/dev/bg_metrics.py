#!/usr/bin/env python3
"""bg_metrics.py · DEV-ONLY: measure a background the way scripts/validate-backgrounds.py judges it.

    python scripts/dev/bg_metrics.py assets/lecture-template          # re-measure every library file, compare with the manifest
    python scripts/dev/bg_metrics.py some-background.webp             # print the four metrics of one file

The runtime gate is stdlib-only and trusts the metrics recorded in manifests/backgrounds.json (bound to the file by
sha256). This module recomputes them from pixels (numpy + pillow, maintainer machine only); make-bg-library.py
uses it to write the manifest and tests/test_backgrounds.py uses it to prove the recorded numbers are real.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("validate_backgrounds", ROOT / "scripts" / "validate-backgrounds.py")
VB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(VB)
W, H, ZONE, CENTRE = VB.W, VB.H, VB.ZONE, VB.CENTRE


def measure(path: Path) -> dict:
    """Pillow + numpy 实现（生成器与 --recompute 共用）。返回四个指标，保留 4 位小数。"""
    import numpy as np
    from PIL import Image, ImageFilter
    im = Image.open(path).convert("RGB")
    if im.size != (W, H):
        return {"size": list(im.size)}
    a = np.asarray(im, dtype=np.float32) / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    lum = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    x0, y0, x1, y1 = ZONE
    blur = np.asarray(im.crop(ZONE).filter(ImageFilter.GaussianBlur(4)), dtype=np.float32) / 255.0
    bl = np.where(blur <= 0.04045, blur / 12.92, ((blur + 0.055) / 1.055) ** 2.4)
    blum = 0.2126 * bl[..., 0] + 0.7152 * bl[..., 1] + 0.0722 * bl[..., 2]
    cx0, cy0, cx1, cy1 = CENTRE
    small = im.crop(CENTRE).resize(((cx1 - cx0) // 8, (cy1 - cy0) // 8), Image.BOX)
    s = np.asarray(small, dtype=np.float32) / 255.0
    sl = np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)
    slum = 0.2126 * sl[..., 0] + 0.7152 * sl[..., 1] + 0.0722 * sl[..., 2]
    return {
        "size": [W, H],
        "mean_lum": round(float(lum.mean()), 4),
        "zone_mean_lum": round(float(lum[y0:y1, x0:x1].mean()), 4),
        "zone_p05_lum": round(float(np.percentile(blum, 5)), 4),
        "centre_std": round(float(slum.std()), 4),
    }


def recheck(root: Path) -> list[str]:
    """Re-measure every manifest entry; return the mismatches (tolerance 0.002)."""
    bad = []
    for e in json.loads((root / "manifests" / "backgrounds.json").read_text(encoding="utf-8"))["backgrounds"]:
        fresh = measure(root / e["file"])
        for k, v in fresh.items():
            if k != "size" and abs(float((e.get("metrics") or {}).get(k, -1)) - v) > 0.002:
                bad.append(f"[{e['id']}] {k}: recorded {(e.get('metrics') or {}).get(k)} != measured {v}")
    return bad


if __name__ == "__main__":
    t = Path(sys.argv[1])
    if t.is_dir():
        problems = recheck(t)
        print("\n".join(problems) or "bg_metrics: every recorded metric matches the pixels")
        sys.exit(1 if problems else 0)
    print(json.dumps(measure(t)))
