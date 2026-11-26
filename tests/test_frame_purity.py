"""3.5.4 P0：渲染必须是帧号的纯函数（连续渲 == 单帧渲）。

3.5.3 的缺陷：auto.tsx 的 panel 写 `opacity: Math.min(Number(en.opacity), op) * dim`，入场后
enter() 不带 opacity → NaN → 浏览器拒收、保留上一帧的旧值 0 → 从 f0 连续渲时 S5 整镜消失，
单帧 still 却一切正常。这里锁三件事：
  1. 源码契约（离线、毫秒级）：NaN 写法不回来；展开中标记只在 0<p<1 时出现；FontGate / GlyphSnap 接线在；
     CI 真的跑 purity-smoke。
  2. 端到端（要渲染，默认 skip）：NV_RENDER_TESTS=1 且模板已 npm ci 时跑 scripts/dev/purity-smoke.mjs。
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "lecture-template" / "src"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


class PurityContract(unittest.TestCase):
    def test_no_nan_opacity_pattern(self):
        # Number(x.opacity) 在 x 不带 opacity 时就是 NaN；React 会把 "NaN" 写进 style，浏览器保留旧值。
        bad = []
        for f in SRC.rglob("*.tsx"):
            for i, line in enumerate(read(f).splitlines(), 1):
                if re.search(r"Number\(\s*\w+\.opacity\s*\)", line) and not line.lstrip().startswith("//"):
                    bad.append(f"{f.relative_to(ROOT)}:{i}")
        self.assertEqual(bad, [], "又出现了 Number(x.opacity) 这种会得到 NaN 的 opacity 写法")

    def test_panel_opacity_is_finite(self):
        auto = read(SRC / "auto.tsx")
        self.assertIn("const enOp = typeof en.opacity === 'number' ? en.opacity : 1;", auto)
        self.assertIn("opacity: Math.min(enOp, op) * dim", auto)

    def test_grow_marker_only_mid_grow(self):
        auto = read(SRC / "auto.tsx")
        body = auto[auto.index("export const enter"):auto.index("export const growDur")]
        self.assertIn("if (p < 1) (style as Record<string, string>)[GROW_VAR]", body,
                      "--nv-grow 只能在展开中带上")
        self.assertIn("if (p >= 1) return {};", body, "落定后不带 clip-path / --nv-grow：落定态 DOM 不随展开状态变化")
        self.assertLess(body.index("if (p >= 1) return {};"), body.index("clipPath: revealClip("),
                        "落定判断要在设 clip-path 之前")
        self.assertIn("revealClip(`calc(${((1 - p) * 100).toFixed(2)}% - ${(p * REVEAL_BLEED).toFixed(2)}px)`)", body,
                      "展开边沿「盒宽 + REVEAL_BLEED」线性扫过")
        snap = read(SRC / "glyph-snap.tsx")
        self.assertIn("inset(calc(-6% - ${REVEAL_BLEED}px) ${right} calc(-6% - ${REVEAL_BLEED}px) calc(-2% - ${REVEAL_BLEED}px))",
                      snap, "展开中 clip 的上下左边向外让出 REVEAL_BLEED")

    def test_glyph_snap_and_font_gate_wired(self):
        idx = read(SRC / "index.tsx")
        self.assertIn("<GlyphSnap/>", idx)
        self.assertIn("const fontsOk=useFontGate();", idx)
        self.assertIn("{fontsOk&&<>", idx, "画面层必须在字体就绪后才挂载（量字宽的缓存不能记下回退字体）")
        snap = read(SRC / "glyph-snap.tsx")
        self.assertIn("useLayoutEffect", snap)
        self.assertIn("delayRender", snap, "字体没就绪时必须先等字体再量字框")

    def test_ci_runs_purity_smoke(self):
        wf = read(ROOT / ".github" / "workflows" / "validate.yml")
        self.assertIn("node scripts/dev/purity-smoke.mjs", wf)
        npm_ci = wf.index("npm ci --prefer-offline")
        self.assertGreater(wf.index("node scripts/dev/purity-smoke.mjs"), npm_ci, "purity-smoke 要排在模板 npm ci 之后")


@unittest.skipUnless(os.environ.get("NV_RENDER_TESTS") == "1"
                     and (ROOT / "assets" / "lecture-template" / "node_modules" / "@remotion" / "renderer").exists()
                     and shutil.which("ffmpeg"),
                     "端到端渲染：设 NV_RENDER_TESTS=1 并先在模板 npm ci（CI 里由 validate.yml 单独一步跑）")
class PuritySmoke(unittest.TestCase):
    def test_purity_smoke(self):
        r = subprocess.run(["node", str(ROOT / "scripts" / "dev" / "purity-smoke.mjs"), "--windows=1", "--scale=0.2"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])


if __name__ == "__main__":
    unittest.main()
