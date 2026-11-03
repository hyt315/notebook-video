#!/usr/bin/env python3
"""text_metrics.py · 文字宽度的真源（P2-17）

排版端（compose）必须在**真实字体**上量字宽。此前用的是字符类系数
（全角 1.0 / ASCII 0.56 / 空格 0.3），再叠一个 `LEAN = 1.06` 当保险——
系数叠系数，换字体就失效，标点一多就切字。

本模块做三件事：
  1. 解析 TTF/OTF 的 cmap + hmtx，取出每个码点的**前进宽度**（em 为单位）；
  2. 把结果缓存成 `assets/fonts/metrics.json`（字体本体 12 MB 不入库，缓存可再生成）；
  3. 给出 `advance_em` / `text_width`，供 compose 的 `text_w` 调用。

边界（P2-17 要求写清）：
  - **compose 侧**（本模块）：字宽、折行、框高、字号收敛——只依赖前进宽度，真字体可解。
  - **浏览器侧**（fittext.tsx 的 measureText）：字距、hinting、复杂排版、最终 FitTextBox 复核。
    排版端估出的框给浏览器用，浏览器不推翻布局，只做最后一道 `fitChineseTextOnNLines`。

缺字体时退回字符类估算（并把 `fallback=True` 带出去），**不假装量过**。
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "assets" / "fonts"
CACHE_PATH = FONT_DIR / "metrics.json"

# 字体角色 → 文件。kai 是主测量字体（正文/标题/标签默认都走 Kai）。
FONT_FILES = {
    "kai": "LXGWWenKaiLite-Regular.ttf",
    "kai-bold": "LXGWWenKaiLite-Medium.ttf",
    "serif": "NotoSerifSC-Bold.otf",
}

# 缓存里存哪些码点的宽度。CJK 表意文字几乎全是 1.0 em，不逐个存——
# 只存「可能不是 1.0」的区段 + 一个默认值，缓存才能小到能入库。
RANGE_ASCII = range(0x20, 0x7F)
RANGE_LATIN1 = range(0xA0, 0x100)
RANGE_PUNCT = range(0x2000, 0x2070)     # 通用标点（引号、破折号、省略号）
RANGE_CJK_SYM = range(0x3000, 0x3040)   # CJK 标点（。、「」《》…）
RANGE_HALFWIDTH = range(0xFF00, 0xFF60) # 全角形式（！-～）
RANGE_HALFWIDTH2 = range(0xFF61, 0xFFA0)  # 半角片假名（极少用，但便宜）

CACHE_RANGES = (
    RANGE_ASCII, RANGE_LATIN1, RANGE_PUNCT,
    RANGE_CJK_SYM, RANGE_HALFWIDTH, RANGE_HALFWIDTH2,
)

# 表意文字默认前进宽度（em）。解析后会用实测值覆盖/确认。
CJK_IDEO_DEFAULT = 1.0

# 无字体、也无缓存时的最后一张表：**只**放字符类估算会错得离谱的标点
# （实测 LXGW WenKai：破折号/省略号 1.0em，弯曲引号 0.35em——字符类会估成 0.56）。
# 有真字体或缓存时这张表不用。宁可这张表粗一点，也不要用一个全局系数去乘。
FALLBACK_PUNCT = {
    ord("—"): 1.0, ord("…"): 1.0, ord("†"): 1.0, ord("‡"): 1.0,
    ord("–"): 0.5,
    ord("‘"): 0.35, ord("’"): 0.35, ord("“"): 0.35, ord("”"): 0.35,
    ord("•"): 0.392,
    ord("«"): 0.53, ord("»"): 0.53, ord("‹"): 0.53, ord("›"): 0.53,
}


# ---------------------------------------------------------------- 字体解析
class FontMetrics:
    """一个字体的前进宽度表。宽度单位是 em（1.0 = 与字号同宽）。"""

    __slots__ = ("units_per_em", "advances", "cjk_default", "fallback", "source")

    def __init__(self, units_per_em: int, advances: dict[int, float],
                 cjk_default: float = CJK_IDEO_DEFAULT, fallback: bool = False,
                 source: str = ""):
        self.units_per_em = units_per_em
        self.advances = advances          # 码点 → em
        self.cjk_default = cjk_default
        self.fallback = fallback
        self.source = source

    def advance_em(self, ch: str) -> float:
        cp = ord(ch)
        if cp in self.advances:
            return self.advances[cp]
        # 表意文字 / 假名 / 兼容区 → 字体默认全宽
        if (0x2E80 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF
                or 0x3040 <= cp <= 0x30FF or 0x3400 <= cp <= 0x4DBF):
            return self.cjk_default
        if not self.advances:
            # 真没数据（无字体、无缓存）：只兜底字符类会错的标点，其余按 ASCII 类
            return FALLBACK_PUNCT.get(cp, 0.56)
        return 0.56

    def text_width(self, s: str, size: float) -> float:
        return sum(self.advance_em(c) for c in s) * size


def _read_tables(data: bytes) -> dict[str, tuple[int, int]]:
    """sfnt 表目录 → {tag: (offset, length)}。"""
    if len(data) < 12:
        raise ValueError("字体太小，不是 sfnt")
    sfnt = data[:4]
    if sfnt not in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"):
        raise ValueError(f"不是 TTF/OTF（sfnt tag={sfnt!r}）")
    num_tables = struct.unpack(">H", data[4:6])[0]
    tables: dict[str, tuple[int, int]] = {}
    for i in range(num_tables):
        off = 12 + i * 16
        tag = data[off:off + 4].decode("ascii", "replace")
        toff, tlen = struct.unpack(">II", data[off + 8:off + 16])
        tables[tag] = (toff, tlen)
    return tables


def _parse_cmap(data: bytes, off: int) -> dict[int, int]:
    """cmap → {码点: glyph id}。优先 format 12（全 Unicode），否则 format 4（BMP）。"""
    num = struct.unpack(">H", data[off + 2:off + 4])[0]
    best = None
    for i in range(num):
        rec = off + 4 + i * 8
        plat, enc, sub = struct.unpack(">HHI", data[rec:rec + 8])
        fmt = struct.unpack(">H", data[off + sub:off + sub + 2])[0]
        # (0,3)/(0,4)/(3,10) 是 Unicode；(3,1) 是 BMP
        score = {(0, 4): 3, (0, 3): 2, (3, 10): 3, (3, 1): 1}.get((plat, enc), 0)
        if score and (best is None or score > best[0]):
            best = (score, off + sub, fmt)
    if best is None:
        raise ValueError("cmap 里没有 Unicode 子表")
    sub, fmt = best[1], best[2]
    mapping: dict[int, int] = {}
    if fmt == 12:
        n_groups = struct.unpack(">I", data[sub + 12:sub + 16])[0]
        for g in range(n_groups):
            go = sub + 16 + g * 12
            start, end, gid = struct.unpack(">III", data[go:go + 12])
            for cp in range(start, end + 1):
                mapping[cp] = gid + (cp - start)
    elif fmt == 4:
        seg_x2 = struct.unpack(">H", data[sub + 6:sub + 8])[0]
        seg = seg_x2 // 2
        ends = struct.unpack(f">{seg}H", data[sub + 14:sub + 14 + seg_x2])
        starts = struct.unpack(f">{seg}H", data[sub + 16 + seg_x2:sub + 16 + 2 * seg_x2])
        deltas = struct.unpack(f">{seg}h", data[sub + 16 + 2 * seg_x2:sub + 16 + 3 * seg_x2])
        range_off_pos = sub + 16 + 3 * seg_x2
        range_offs = struct.unpack(f">{seg}H", data[range_off_pos:range_off_pos + seg_x2])
        for i in range(seg):
            for cp in range(starts[i], ends[i] + 1):
                if cp == 0xFFFF:
                    continue
                if range_offs[i] == 0:
                    mapping[cp] = (cp + deltas[i]) & 0xFFFF
                else:
                    # glyphId = *(idRangeOffset/2 + (cp - start) + &idRangeOffset[i])
                    gi_pos = range_off_pos + i * 2 + range_offs[i] + (cp - starts[i]) * 2
                    gid = struct.unpack(">H", data[gi_pos:gi_pos + 2])[0]
                    mapping[cp] = (gid + deltas[i]) & 0xFFFF if gid else 0
    else:
        raise ValueError(f"cmap format {fmt} 不支持（只认 4 / 12）")
    return mapping


def parse_font(path: Path | str) -> FontMetrics:
    """解析 TTF/OTF 的前进宽度。只读 head / hhea / hmtx / cmap，不碰轮廓。"""
    p = Path(path)
    data = p.read_bytes()
    tables = _read_tables(data)
    for need in ("head", "hhea", "hmtx", "cmap"):
        if need not in tables:
            raise ValueError(f"{p.name} 缺 {need} 表")
    head = tables["head"][0]
    units_per_em = struct.unpack(">H", data[head + 18:head + 20])[0]
    hhea = tables["hhea"][0]
    num_hmetrics = struct.unpack(">H", data[hhea + 34:hhea + 36])[0]
    hmtx = tables["hmtx"][0]
    # hmtx：num_hmetrics 个 (advanceWidth:u16, lsb:i16)，之后只剩 lsb
    advances_by_gid: list[int] = []
    for g in range(num_hmetrics):
        aw = struct.unpack(">H", data[hmtx + g * 4:hmtx + g * 4 + 2])[0]
        advances_by_gid.append(aw)
    cmap = _parse_cmap(data, tables["cmap"][0])
    advances: dict[int, float] = {}
    for cp, gid in cmap.items():
        if gid < len(advances_by_gid):
            advances[cp] = advances_by_gid[gid] / units_per_em
    # CJK 表意的默认宽度：取「汉字区里最常见的前进宽度」
    cjk_widths = [advances[cp] for cp in range(0x4E00, 0x4E00 + 2048) if cp in advances]
    cjk_default = max(set(cjk_widths), key=cjk_widths.count) if cjk_widths else CJK_IDEO_DEFAULT
    return FontMetrics(units_per_em, advances, cjk_default=cjk_default, source=p.name)


# ---------------------------------------------------------------- 缓存
def _wanted(cp: int) -> bool:
    return any(cp in r for r in CACHE_RANGES)


def build_cache() -> dict:
    """从磁盘上的字体生成缓存。缺哪个字体就跳过哪个（缓存里不写假数据）。"""
    out: dict = {"version": 1, "fonts": {}}
    for role, name in FONT_FILES.items():
        path = FONT_DIR / name
        if not path.is_file():
            continue
        m = parse_font(path)
        sample = {str(cp): round(w, 4) for cp, w in sorted(m.advances.items()) if _wanted(cp)}
        out["fonts"][role] = {
            "source": name,
            "unitsPerEm": m.units_per_em,
            "cjkDefault": m.cjk_default,
            "advances": sample,
        }
    return out


def write_cache(path: Path | str = CACHE_PATH) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(build_cache(), ensure_ascii=False, separators=(",", ":")),
                 encoding="utf-8")
    return p


# ---------------------------------------------------------------- 加载（带缓存）
_METRICS: dict[str, FontMetrics] = {}
_LOADED = False


def _load_all() -> None:
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    # 1) 缓存
    if CACHE_PATH.is_file():
        try:
            data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        for role, spec in (data.get("fonts") or {}).items():
            adv = {int(k): float(v) for k, v in (spec.get("advances") or {}).items()}
            _METRICS[role] = FontMetrics(
                int(spec.get("unitsPerEm", 1000)), adv,
                cjk_default=float(spec.get("cjkDefault", CJK_IDEO_DEFAULT)),
                source=f"cache:{spec.get('source', role)}")
    # 2) 磁盘字体覆盖缓存（字体在就用真字体，缓存只当离线兜底）
    for role, name in FONT_FILES.items():
        path = FONT_DIR / name
        if path.is_file():
            try:
                _METRICS[role] = parse_font(path)
            except Exception as e:  # 解析失败不挡排版，退估算
                print(f"[text_metrics] {name} 解析失败，退回字符类估算：{e}", file=sys.stderr)


def get(role: str = "kai") -> FontMetrics:
    """取一个字体角色的度量。没有就退回字符类估算（fallback=True）。"""
    _load_all()
    if role in _METRICS:
        return _METRICS[role]
    if not _METRICS:
        return FontMetrics(1000, {}, fallback=True, source="estimate")
    # 角色缺失：用已加载里最接近的（serif 缺 → kai）
    return _METRICS.get("kai") or next(iter(_METRICS.values()))


def advance_em(ch: str, role: str = "kai") -> float:
    return get(role).advance_em(ch)


def text_width(s: str, size: float, role: str = "kai", mono: bool = False) -> float:
    """真实字宽（em × size）。mono=True 时沿用等宽近似（代码框不走 Kai）。"""
    if mono:
        return sum((1.0 if _is_wide(c) else 0.6) for c in s) * size
    return get(role).text_width(s, size)


def _is_wide(ch: str) -> bool:
    cp = ord(ch)
    return 0x2E80 <= cp <= 0x9FFF or 0x3000 <= cp <= 0x303F or 0xFF00 <= cp <= 0xFFEF


def fallback_used(role: str = "kai") -> bool:
    return get(role).fallback


# ---------------------------------------------------------------- CLI
def main(argv: list[str]) -> int:
    args = argv[1:]
    if "--write-cache" in args:
        p = write_cache()
        n = sum(len(v.get("advances") or {}) for v in build_cache()["fonts"].values())
        print(f"已写 {p}（{n} 个码点）")
        return 0
    if "--check" in args:
        _load_all()
        for role in FONT_FILES:
            m = get(role)
            print(f"{role:<10} {'FALLBACK' if m.fallback else 'real':<9} "
                  f"upem={m.units_per_em} cjk={m.cjk_default:.3f} "
                  f"n={len(m.advances)} src={m.source}")
        # 抽查几个真实宽度
        samples = ["今天", "Hello", "（注）", "3.14%", "哈希 hash", "……", "全角！"]
        for s in samples:
            w = text_width(s, 100)
            print(f"  {s!r:<16} @100px → {w:.1f}")
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
