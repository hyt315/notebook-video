#!/usr/bin/env python3
"""compare-text-metrics.py — text_metrics.py 自写 TTF/OTF 解析 vs fontTools（MIT）的对照（维护者工具，不进包）。

用法（需要 fontTools，且先下载字体：node scripts/notebook-video.mjs fonts --serif）：
    python3 scripts/dev/compare-text-metrics.py            # 码点级 + 缓存级对照
    python3 scripts/dev/compare-text-metrics.py --layout   # 再用两种解析各跑一遍全部示例 story 的 compose，比产物哈希

判定：三层全一致才算「换 fontTools 不改变任何排版结果」：
  1. 每个字体每个码点的前进宽度（em）与 unitsPerEm、CJK 默认宽度；
  2. 由两边各自生成的 metrics.json 缓存逐字节；
  3. examples/ 下全部 story 的 compose 产物（shots.json / story.ts / film.ts / caption-cues 等）sha256。
退出码：0 全一致；1 有差异；2 缺 fontTools 或字体。
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import text_metrics as tm  # noqa: E402

PATCH = r'''
import importlib.util, runpy, sys
sys.path.insert(0, %(scripts)r)
import text_metrics as tm
if %(use_ft)r:
    spec = importlib.util.spec_from_file_location("cmp_tm", %(harness)r)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    tm.parse_font = mod.ft_parse
sys.argv = [%(script)r] + %(args)r
runpy.run_path(%(script)r, run_name="__main__")
'''


def ft_parse(path: Path):
    from fontTools.ttLib import TTFont
    f = TTFont(str(path), lazy=True)
    upem = f["head"].unitsPerEm
    hm = f["hmtx"].metrics
    adv = {cp: hm[g][0] / upem for cp, g in f.getBestCmap().items() if g in hm}
    cjk = [adv[cp] for cp in range(0x4E00, 0x4E00 + 2048) if cp in adv]
    d = max(set(cjk), key=cjk.count) if cjk else tm.CJK_IDEO_DEFAULT
    return tm.FontMetrics(upem, adv, cjk_default=d, source=path.name)


def compare_fonts() -> int:
    diffs = 0
    fonts = [(r, tm.FONT_DIR / n) for r, n in tm.FONT_FILES.items() if (tm.FONT_DIR / n).is_file()]
    if not fonts:
        print("没有可比的字体：先跑 node scripts/notebook-video.mjs fonts --serif")
        return -1
    for role, path in fonts:
        old, new = tm.parse_font(path), ft_parse(path)
        keys = set(old.advances) | set(new.advances)
        bad = [cp for cp in keys if old.advances.get(cp) != new.advances.get(cp)]
        same_meta = old.units_per_em == new.units_per_em and old.cjk_default == new.cjk_default
        print(f"{role:<9} {path.name:<28} 码点 old={len(old.advances)} new={len(new.advances)} "
              f"宽度不同={len(bad)} upem/cjk一致={same_meta}"
              + (f" 例：{[hex(c) for c in sorted(bad)[:5]]}" if bad else ""))
        diffs += len(bad) + (0 if same_meta else 1)
    # 缓存级：两边各自生成 metrics.json 内容
    old_cache = json.dumps(tm.build_cache(), ensure_ascii=False, separators=(",", ":"))
    real = tm.parse_font
    tm.parse_font = ft_parse
    try:
        new_cache = json.dumps(tm.build_cache(), ensure_ascii=False, separators=(",", ":"))
    finally:
        tm.parse_font = real
    same = old_cache == new_cache
    print(f"metrics.json 缓存逐字节一致：{same}（{len(old_cache)} 字节）")
    return diffs + (0 if same else 1)


def compose_hashes(use_ft: bool) -> dict[str, str]:
    import shutil
    out: dict[str, str] = {}
    stories = sorted(ROOT.glob("examples/**/*.story.json"))
    with tempfile.TemporaryDirectory(prefix="nv-tm-") as td:
        for s in stories:
            proj = Path(td) / s.relative_to(ROOT / "examples").as_posix().replace("/", "__").replace(".story.json", "")
            shutil.copytree(ROOT / "assets/lecture-template", proj, ignore=shutil.ignore_patterns("node_modules"))
            code = PATCH % {"scripts": str(ROOT / "scripts"), "use_ft": use_ft, "harness": str(Path(__file__).resolve()),
                            "script": str(ROOT / "scripts/compose-story.py"), "args": [str(s), str(proj)]}
            r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                               env={**os.environ, "PYTHONHASHSEED": "0"})  # compose 的 protected 同长短语顺序随哈希种子变
            if r.returncode:
                out[s.name] = f"compose-fail rc={r.returncode}"
                continue
            for f in sorted(proj.rglob("*")):
                if f.is_file() and f.suffix in (".ts", ".json", ".txt") and "node_modules" not in f.parts:
                    out[f"{s.name}:{f.relative_to(proj)}"] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def main(argv: list[str]) -> int:
    try:
        import fontTools  # noqa: F401
    except ModuleNotFoundError:
        print("需要 fontTools（pip install fonttools，MIT）；它只用于这份对照，技能运行不需要")
        return 2
    d = compare_fonts()
    if d < 0:
        return 2
    if "--layout" in argv:
        a, b = compose_hashes(False), compose_hashes(True)
        diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        fails = sorted(k for k in set(a) | set(b) if str(a.get(k)).startswith("compose-fail") != str(b.get(k)).startswith("compose-fail"))
        both = sorted(k for k in a if a[k].startswith("compose-fail") and b.get(k) == a[k])
        if both:
            print(f"两种解析都 compose 失败（夹具本身不完整，未参与比较）：{both}")
        print(f"compose 产物：{len(a)} 个文件，两种解析哈希不同 {len(diff)} 个" + (f"：{diff[:8]}" if diff else "")
              + (f"；compose 失败 {fails}" if fails else ""))
        d += len(diff) + len(fails)
    print("结论：" + ("一致" if d == 0 else f"有 {d} 处差异"))
    return 0 if d == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
