"""线稿库索引：把 `linework/library.ts` 的 sketch → 部位名读成 Python 表（构建期校验用）。

为什么必须在构建期查，而不是等渲染：

  · `draw: "lib:xxx"` 名字写错时 `resolveSketchDef` 返回 null，`SketchLayer` 直接 return null
    —— 那一镜**什么都没画**，但渲染照样成功、时长照样对、空白门禁也可能被文字填满而通过。
  · `parts` 里的名字写错时，旧版画整图（与旁白不符），新版在「一个都没命中」时也退回整图。
    两种都只是运行期 `console.warn`，日志里一闪而过，成片已经错了。

TS 是唯一真源（引擎直接 import 它），这里只做**只读**解析，不重复维护一份名单：

  · 顶格 2 空格的 `name: {`            → 一个线稿；
  · 其下 4 空格的 `parts: {`           → 进入部位表；
  · 部位表里 6 空格的 `key: {`         → 一个部位。

解析不到任何线稿时**不静默降级**：直接抛错让门禁失败，而不是变成「检查通过」。
"""
from __future__ import annotations

import difflib
import math
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIBRARY = ROOT / "assets" / "lecture-template" / "src" / "linework" / "library.ts"

_SKETCH_RE = re.compile(r"^  ['\"]?([A-Za-z0-9_-]+)['\"]?: \{")
_PARTS_RE = re.compile(r"^    parts: \{")
_PART_RE = re.compile(r"^      ['\"]?([A-Za-z0-9_-]+)['\"]?: \{")
_PARTS_END_RE = re.compile(r"^    \}")
_SELF_SHAPES = "all"      # shapes:[…] 只有一个整体部位（见 sketch.tsx shapesToDef）

# 单部位特写的「还看得清」下限：部位短边 ÷ 取景框短边。
# 低于它就该写 part.fit，否则选中这一部位时观众看到的是一小块缩在纸上的线。
# 0.45 是目测阈值（3.6.1 线稿画宽 ≤19% 画面时，0.45 → 部位短边约 8.5% 画宽）。
MIN_PART_SHARE = 0.45


class LibraryParseError(RuntimeError):
    """库文件结构变了、解析不到内容 —— 宁可报错，也不假装校验过。"""


def parse_library(text: str) -> dict[str, tuple[str, ...]]:
    anchor = "export const SKETCHES"
    if anchor not in text:
        raise LibraryParseError(f"找不到 `{anchor}`：库文件结构变了，线稿校验无法进行")
    body = text[text.index(anchor):]
    out: dict[str, list[str]] = {}
    current: str | None = None
    in_parts = False
    for line in body.splitlines():
        m = _SKETCH_RE.match(line)
        if m:
            current = m.group(1)
            out[current] = []
            in_parts = False
            continue
        if current is None:
            continue
        if not in_parts and _PARTS_RE.match(line):
            in_parts = True
            continue
        if in_parts:
            p = _PART_RE.match(line)
            if p:
                out[current].append(p.group(1))
            elif _PARTS_END_RE.match(line):
                in_parts = False
    result = {k: tuple(v) for k, v in out.items()}
    if not result:
        raise LibraryParseError("解析出 0 个线稿：库文件结构可能变了")
    empty = [k for k, v in result.items() if not v]
    if empty:
        raise LibraryParseError(f"这些线稿没解析出部位表：{', '.join(empty)}")
    return result


@lru_cache(maxsize=4)
def _load_cached(path: str, mtime: float) -> dict[str, tuple[str, ...]]:
    return parse_library(Path(path).read_text(encoding="utf-8"))


def load_library(path: Path | str | None = None) -> dict[str, tuple[str, ...]]:
    p = Path(path or DEFAULT_LIBRARY)
    try:
        mtime = p.stat().st_mtime
    except OSError as exc:
        raise LibraryParseError(f"读不到线稿库 {p}：{exc}") from exc
    return _load_cached(str(p), mtime)


def check_selection(draw: object, parts: object, library: dict[str, tuple[str, ...]] | None = None) -> list[str]:
    """返回问题清单（空 = 通过）。只看「名字对不对」，不看排版与画法。"""
    lib = load_library() if library is None else library
    d = str(draw or "")
    if d.startswith("lib:"):
        name = d[4:]
        if name not in lib:
            near = difflib.get_close_matches(name, list(lib), n=3)
            tip = f"；相近的：{' / '.join('lib:' + n for n in near)}" if near else ""
            return [f"draw=lib:{name} 不在线稿库里（共 {len(lib)} 个）{tip}"]
        allowed = lib[name]
    elif d.startswith("shapes:"):
        allowed = (_SELF_SHAPES,)
    else:
        return []       # trace：照片配方自己出线稿，部位名不在这里校验

    if isinstance(parts, dict):
        picked = [str(k) for k in parts]
    elif isinstance(parts, (list, tuple)):
        picked = [str(x) for x in parts]
    else:
        return []
    bad = [p for p in picked if p not in allowed]
    if not bad:
        return []
    return [f"parts 里的 {' / '.join(bad)} 不在 {d} 的部位表中"
            f"（可用：{' / '.join(allowed)}）"]


_NUM = r"-?\d*\.?\d+(?:[eE][-+]?\d+)?"
_PATH_TOKEN = re.compile(rf"[MmLlHhVvCcSsQqTtAaZz]|{_NUM}")
# 库里的四种基本形都过这四个 helper（见 library.ts 头部），加上个别内联对象写法。
_PRIM_HELPERS = (
    ("path", re.compile(r"\bd\('([^']*)'")),
    ("circle", re.compile(rf"\bc\(\s*({_NUM})\s*,\s*({_NUM})\s*,\s*({_NUM})")),
    ("rect", re.compile(rf"\br\(\s*({_NUM})\s*,\s*({_NUM})\s*,\s*({_NUM})\s*,\s*({_NUM})")),
    ("line", re.compile(rf"\bl\(\s*({_NUM})\s*,\s*({_NUM})\s*,\s*({_NUM})\s*,\s*({_NUM})")),
)
_INLINE_OBJ = re.compile(r"\{k:\s*'([a-z]+)'([^}]*)\}")


def _arc_points(x1: float, y1: float, rx: float, ry: float, phi_deg: float,
                large: int, sweep: int, x2: float, y2: float, n: int = 24) -> list[tuple[float, float]]:
    """SVG 端点式圆弧 → 采样点（F.6.5 中心参数化）。取包围盒用，24 段已足够（误差 <0.3 单位）。"""
    if rx == 0 or ry == 0:
        return [(x2, y2)]
    phi = math.radians(phi_deg)
    cosp, sinp = math.cos(phi), math.sin(phi)
    dx2, dy2 = (x1 - x2) / 2, (y1 - y2) / 2
    x1p = cosp * dx2 + sinp * dy2
    y1p = -sinp * dx2 + cosp * dy2
    rx, ry = abs(rx), abs(ry)
    lam = x1p * x1p / (rx * rx) + y1p * y1p / (ry * ry)
    if lam > 1:
        rx *= math.sqrt(lam)
        ry *= math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    coef = math.sqrt(max(0.0, num / den)) * (-1 if large == sweep else 1)   # SVG F.6.5.2：两者相等取负
    cxp = coef * rx * y1p / ry
    cyp = -coef * ry * x1p / rx
    cx = cosp * cxp - sinp * cyp + (x1 + x2) / 2
    cy = sinp * cxp + cosp * cyp + (y1 + y2) / 2

    def angle(ux: float, uy: float, vx: float, vy: float) -> float:
        dot = (ux * vx + uy * vy) / (math.hypot(ux, uy) * math.hypot(vx, vy))
        a = math.acos(max(-1.0, min(1.0, dot)))
        return -a if ux * vy - uy * vx < 0 else a

    ux, uy = (x1p - cxp) / rx, (y1p - cyp) / ry
    vx, vy = (-x1p - cxp) / rx, (-y1p - cyp) / ry
    th1 = angle(1, 0, ux, uy)
    dth = angle(ux, uy, vx, vy)
    if not sweep and dth > 0:
        dth -= 2 * math.pi
    elif sweep and dth < 0:
        dth += 2 * math.pi
    out = []
    for i in range(n + 1):
        t = th1 + dth * i / n
        out.append((cx + rx * math.cos(t) * cosp - ry * math.sin(t) * sinp,
                    cy + rx * math.cos(t) * sinp + ry * math.sin(t) * cosp))
    return out


def path_bbox(d: str) -> tuple[float, float, float, float] | None:
    """路径的包围盒 [x0,y0,x1,y1]（0–100 坐标系）。曲线按采样算，别用控制点（会虚胖）。"""
    toks = _PATH_TOKEN.findall(d or "")
    if not toks:
        return None
    pts: list[tuple[float, float]] = []
    i, cmd = 0, None
    cx = cy = sx = sy = 0.0

    def num() -> float:
        nonlocal i
        v = float(toks[i]); i += 1
        return v

    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in "Zz":
                cx, cy = sx, sy
                pts.append((cx, cy))
                continue
        if cmd is None:
            break
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            x, y = num(), num()
            cx, cy = (cx + x, cy + y) if rel else (x, y)
            sx, sy = cx, cy
            pts.append((cx, cy))
            cmd = "l" if rel else "L"      # M 之后的隐式坐标是直线
        elif c == "L":
            x, y = num(), num()
            cx, cy = (cx + x, cy + y) if rel else (x, y)
            pts.append((cx, cy))
        elif c == "H":
            x = num()
            cx = cx + x if rel else x
            pts.append((cx, cy))
        elif c == "V":
            y = num()
            cy = cy + y if rel else y
            pts.append((cx, cy))
        elif c in "CS":
            pts.append((cx, cy))
            ctrl = [(num(), num()) for _ in range(2)]
            if rel:
                ctrl = [(cx + a, cy + b) for a, b in ctrl]
            x, y = num(), num()
            ex, ey = (cx + x, cy + y) if rel else (x, y)
            p0, (p1, p2), p3 = (cx, cy), (ctrl[0], ctrl[1]), (ex, ey)
            for k in range(1, 17):
                u = k / 16
                a = (1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u * u, u ** 3
                pts.append((a[0] * p0[0] + a[1] * p1[0] + a[2] * p2[0] + a[3] * p3[0],
                            a[0] * p0[1] + a[1] * p1[1] + a[2] * p2[1] + a[3] * p3[1]))
            cx, cy = ex, ey
        elif c in "QT":
            pts.append((cx, cy))
            q = num(), num()
            qx, qy = (cx + q[0], cy + q[1]) if rel else q
            x, y = num(), num()
            ex, ey = (cx + x, cy + y) if rel else (x, y)
            for k in range(1, 17):
                u = k / 16
                a, b, cc = (1 - u) ** 2, 2 * (1 - u) * u, u * u
                pts.append((a * cx + b * qx + cc * ex, a * cy + b * qy + cc * ey))
            cx, cy = ex, ey
        elif c == "A":
            rx, ry, rot = num(), num(), num()
            large, sweep = int(num()), int(num())
            x, y = num(), num()
            ex, ey = (cx + x, cy + y) if rel else (x, y)
            pts.extend(_arc_points(cx, cy, rx, ry, rot, large, sweep, ex, ey))
            cx, cy = ex, ey
        else:
            i += 1                          # 不认识的命令：跳过，别死循环
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def prims_bbox(text: str) -> tuple[float, float, float, float] | None:
    """一段 TS 里所有基本形的并集包围盒。helper 与内联对象两种写法都认。"""
    boxes = []
    for kind, pat in _PRIM_HELPERS:
        for m in pat.finditer(text):
            if kind == "path":
                b = path_bbox(m.group(1))
                if b:
                    boxes.append(b)
                continue
            g = [float(x) for x in m.groups()[:4]]
            if kind == "circle":
                x, y, r = g[0], g[1], g[2]
                boxes.append((x - r, y - r, x + r, y + r))
            elif kind == "rect":
                boxes.append((g[0], g[1], g[0] + g[2], g[1] + g[3]))
            else:
                boxes.append((min(g[0], g[2]), min(g[1], g[3]), max(g[0], g[2]), max(g[1], g[3])))
    covered = "".join(m.group(0) for _, pat in _PRIM_HELPERS for m in pat.finditer(text))
    for m in _INLINE_OBJ.finditer(text):
        if m.group(0) in covered:
            continue                           # helper 展开后的对象字面量，别重复算
        attrs = dict(re.findall(rf"(\w+):\s*({_NUM})", m.group(2)))
        kind = m.group(1)
        f = lambda k, dflt=0.0: float(attrs.get(k, dflt))
        if kind == "circle":
            x, y, r = f("cx"), f("cy"), f("r", 8.0)
            boxes.append((x - r, y - r, x + r, y + r))
        elif kind == "rect":
            boxes.append((f("x"), f("y"), f("x") + f("w"), f("y") + f("h")))
        elif kind == "line":
            boxes.append((min(f("x1"), f("x2")), min(f("y1"), f("y2")),
                          max(f("x1"), f("x2")), max(f("y1"), f("y2"))))
        elif kind == "path" and "d" in m.group(2):
            b = path_bbox(re.search(r"d:\s*'([^']*)'", m.group(2)).group(1))
            if b:
                boxes.append(b)
    if not boxes:
        return None
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _arr(text: str, key: str) -> tuple[float, ...] | None:
    m = re.search(rf"\b{key}:\s*\[([-\d.,\s]+)\]", text)
    return tuple(float(x) for x in re.split(r"[,\s]+", m.group(1).strip()) if x) if m else None


def parse_geometry(text: str) -> dict[str, dict]:
    """线稿 → {名字: {fit, bbox, parts: {部位: {fit, anchor, bbox}}}}（0–100 坐标）。

    与 `parse_library` 分开：那个只认名字（很多门禁只要名字），这个要把基本形算成包围盒，
    开销大一些，只在几何校验时用。
    """
    anchor = "export const SKETCHES"
    if anchor not in text:
        raise LibraryParseError(f"找不到 `{anchor}`：库文件结构变了，线稿几何校验无法进行")
    body = text[text.index(anchor):]
    out: dict[str, dict] = {}
    cur: dict | None = None
    cur_part: str | None = None
    buf: list[str] = []
    in_parts = in_base = False

    def flush() -> None:
        nonlocal cur_part, buf
        if cur and cur_part:
            block = "\n".join(buf)
            cur["parts"][cur_part] = {
                "fit": _arr(block, "fit"),
                "anchor": _arr(block, "anchor"),
                "bbox": prims_bbox(block),
            }
        cur_part, buf = None, []

    for line in body.splitlines():
        m = _SKETCH_RE.match(line)
        if m:
            flush()
            cur = {"fit": None, "base": [], "parts": {}}
            out[m.group(1)] = cur
            in_parts = in_base = False
            continue
        if cur is None:
            continue
        if _PARTS_RE.match(line):
            in_parts, in_base = True, False
            continue
        if re.match(r"^    base: \[", line):
            in_base, in_parts = True, False
            cur["base"] = [line]
            continue
        if in_parts:
            p = _PART_RE.match(line)
            if p:
                flush()
                cur_part = p.group(1)
                buf = [line]
            elif _PARTS_END_RE.match(line):
                flush()
                in_parts = False
            elif cur_part:
                buf.append(line)
            continue
        if in_base:
            cur["base"].append(line)
            if re.match(r"^    \]", line):
                in_base = False
            continue
        fm = re.match(r"^    fit: \[([-\d.,\s]+)\]", line)
        if fm:
            cur["fit"] = tuple(float(x) for x in re.split(r"[,\s]+", fm.group(1).strip()) if x)
    flush()
    if not out:
        raise LibraryParseError("解析出 0 个线稿几何：库文件结构可能变了")
    for name, sk in out.items():
        boxes = [prims_bbox("\n".join(sk["base"]))] if sk["base"] else []
        boxes += [p["bbox"] for p in sk["parts"].values() if p["bbox"]]
        boxes = [b for b in boxes if b]
        sk["bbox"] = (min(b[0] for b in boxes), min(b[1] for b in boxes),
                      max(b[2] for b in boxes), max(b[3] for b in boxes)) if boxes else None
    return out


@lru_cache(maxsize=4)
def _load_geo_cached(path: str, mtime: float) -> dict[str, dict]:
    return parse_geometry(Path(path).read_text(encoding="utf-8"))


def load_geometry(path: Path | str | None = None) -> dict[str, dict]:
    p = Path(path or DEFAULT_LIBRARY)
    try:
        mtime = p.stat().st_mtime
    except OSError as exc:
        raise LibraryParseError(f"读不到线稿库 {p}：{exc}") from exc
    return _load_geo_cached(str(p), mtime)


def _inside(box: tuple[float, float, float, float], outer: tuple[float, float, float, float],
            tol: float = 0.0) -> tuple[float, float, float, float]:
    """内容超出取景框的四边量（正数 = 被裁掉多少），供报错说清"哪一边裁了多少"。"""
    x0, y0, x1, y1 = box
    ox, oy, ow, oh = outer
    return (max(0.0, ox - x0 - tol), max(0.0, oy - y0 - tol),
            max(0.0, x1 - (ox + ow) - tol), max(0.0, y1 - (oy + oh) - tol))


def geometry_problems(path: Path | str | None = None, min_share: float = MIN_PART_SHARE,
                      max_ratio: float = 4.5) -> tuple[list[str], list[str]]:
    """线稿几何自检，返回 (错误, 提示)。

    **错误**（会让画面真的不对，渲染期一声不响）：
      · 整图 fit / 部位 fit 没盖住图形 —— 内容画到框外（或被容器裁掉），特写只剩半边；
      · 引线落点不在取景框里 —— 单部位特写时那条线指向画外；
      · 框的宽高不为正、长宽比超过 4.5 —— 画出来是一条缝，不是特写。
    **提示**（能看，但偏小）：部位长边不到取景框的 45%，特写时观众得凑近看。
    """
    geo = load_geometry(path)
    auto = part_crops(path)
    errors: list[str] = []
    notes: list[str] = []
    for name, sk in geo.items():
        fit = sk.get("fit") or (0.0, 0.0, 100.0, 100.0)
        if fit[2] <= 0 or fit[3] <= 0:
            errors.append(f"{name}: fit={list(fit)} 宽高必须为正")
            continue
        if sk.get("bbox"):
            over = _inside(sk["bbox"], fit)
            if max(over) > 0:
                errors.append(f"{name}: 整图 fit={_fmt(fit)} 没盖住内容 "
                              f"（左 {over[0]:.1f} / 上 {over[1]:.1f} / 右 {over[2]:.1f} / 下 {over[3]:.1f} 画到框外）")
        for pname, part in sk["parts"].items():
            if part.get("fit"):
                crop, source = part["fit"], "部位 fit"
                if crop[2] <= 0 or crop[3] <= 0:
                    errors.append(f"{name}.{pname}: fit={list(crop)} 宽高必须为正")
                    continue
            else:
                # 没手写框 → 引擎会用生成的缺省框（src/linework/crops.ts），按它判
                crop, source = auto.get(name, {}).get(pname, fit), "缺省框"
            if part.get("bbox"):
                over = _inside(part["bbox"], crop)
                if max(over) > 0:
                    errors.append(f"{name}.{pname}: {source}={_fmt(crop)} 没盖住图形本身 "
                                  f"（左 {over[0]:.1f} / 上 {over[1]:.1f} / 右 {over[2]:.1f} / 下 {over[3]:.1f} 画到框外）")
            if part.get("anchor"):
                ax, ay = part["anchor"][:2]
                if not (crop[0] <= ax <= crop[0] + crop[2] and crop[1] <= ay <= crop[1] + crop[3]):
                    errors.append(f"{name}.{pname}: 引线落点 {[ax, ay]} 在{source} {_fmt(crop)} 之外"
                                  f"（单部位特写时这条线会指向画外）")
            if crop[3] and crop[2] / crop[3] > max_ratio:
                errors.append(f"{name}.{pname}: {source}={_fmt(crop)} 长宽比 {crop[2] / crop[3]:.1f} > {max_ratio}"
                              f"（画出来是一条缝，不像特写）")
            if part.get("bbox") and part.get("fit"):
                bw, bh = part["bbox"][2] - part["bbox"][0], part["bbox"][3] - part["bbox"][1]
                # 看**长边**占取景框的比例：一条横贯全图的绳、一根地面线本来就细，
                # 用短边判会把它们全判成"太小"，那不是缺陷，是形状。
                share = max(bw / crop[2], bh / crop[3]) if crop[2] and crop[3] else 0
                if share < min_share:
                    notes.append(f"{name}.{pname}: 手写 fit 让特写偏小（部位长边只占 {share:.0%} < {min_share:.0%}）")
    return errors, notes


def part_crops(path: Path | str | None = None) -> dict[str, dict[str, tuple[float, float, float, float]]]:
    """每个部位的**缺省**取景框（部位自己写了 fit 的不算，那一个由引擎优先用）。

    为什么要生成而不是手写：单部位特写要"框住这一部位、留一点边"，这件事完全由基本形决定。
    手写 26 个框，改一次 path 就要改一次框，忘改就裁掉一半（P1-12 说的漂移）。
    这里按真实包围盒算一次，落成 `src/linework/crops.ts`，引擎只读数据。
    """
    geo = load_geometry(path)
    out: dict[str, dict[str, tuple[float, float, float, float]]] = {}
    for name, sk in geo.items():
        fit = sk.get("fit") or (0.0, 0.0, 100.0, 100.0)
        crops: dict[str, tuple[float, float, float, float]] = {}
        for pname, part in sk["parts"].items():
            box = part.get("bbox")
            if part.get("fit") or not box:
                continue
            x0, y0, x1, y1 = box
            bw, bh = x1 - x0, y1 - y0
            pad = 0.12 * max(bw, bh)          # 留白按长边算：细长物件不会左右贴边
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            w, h = bw + 2 * pad, bh + 2 * pad
            # 一条地面线、一根指针：长边够长但短边近 0，框太小会变成极端长宽比 → 画面被放到失真。
            min_side = max(16.0, 0.35 * min(fit[2], fit[3]))
            if w < min_side:
                w = min_side
            if h < min_side:
                h = min_side
            nx, ny = cx - w / 2, cy - h / 2
            if w >= 100:
                nx, w = 0.0, 100.0
            else:
                nx = min(max(0.0, nx), 100.0 - w)
            if h >= 100:
                ny, h = 0.0, 100.0
            else:
                ny = min(max(0.0, ny), 100.0 - h)
            crops[pname] = tuple(round(v, 1) for v in (nx, ny, w, h))
        if crops:
            out[name] = crops
    return out


CROPS_HEADER = """// AUTO-GENERATED by `python scripts/linework_index.py --write-crops` —— 不要手改。
//
// 单部位特写的**缺省**取景框（0–100 坐标，已按部位包围盒留 12% 边）。
// 部位自己声明了 `fit` 时以 fit 为准（见 library.ts 的 chiplog），这份只是没有手写框时的兜底。
// 由真实基本形算出来，而不是手填：改 path 忘了改框，就会出现"特写框住半边"或"框太大看不见细节"。
// 校验：tests/test_linework_crops.py 把这份与 library.ts 重算结果逐项比对。
"""


def render_part_crops(crops: dict[str, dict[str, tuple[float, float, float, float]]]) -> str:
    lines = [CROPS_HEADER,
             "",
             "export type PartCrop = [number, number, number, number];",
             "",
             "export const PART_CROP: Record<string, Record<string, PartCrop>> = {"]
    for name in sorted(crops):
        body = ", ".join(f"{p}: [{_fmt(crops[name][p])[1:-1]}]" for p in sorted(crops[name]))
        lines.append(f"  {name}: {{{body}}},")
    lines.append("};")
    return "\n".join(lines) + "\n"


def write_part_crops(target: Path | str) -> Path:
    out = Path(target)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_part_crops(part_crops()), encoding="utf-8", newline="\n")
    return out


def _fmt(box: tuple[float, ...]) -> str:
    return "[" + ", ".join(f"{v:g}" for v in box) + "]"


def check_targets(draw: object, targets: list, library: dict[str, tuple[str, ...]] | None = None) -> list[str]:
    """动作的 target（point / drop / swap / mark 指向谁）必须是真的部位名。

    与 `check_selection` 分开：那边的报错说「parts 里的 X」，动作指向错的后果是
    **那个动作整条被引擎跳过**（`def.parts[id]` 取不到 → 画整图或不画），
    观众看到的是「说过要点这里，结果什么都没发生」。提示语要说清是哪个动作。
    """
    lib = load_library() if library is None else library
    d = str(draw or "")
    if not d.startswith("lib:"):
        return []      # shapes / trace 的部位名由作者自定，没有可对照的表
    name = d[4:]
    if name not in lib:
        return []      # 名字本身错了，check_selection 已经报过
    allowed = lib[name]
    bad = [str(t) for t in targets if t not in allowed]
    if not bad:
        return []
    return [f"动作 target 里的 {' / '.join(bad)} 不在 {d} 的部位表中（可用：{' / '.join(allowed)}）"]


def main(argv: list[str]) -> int:
    if "--write-crops" in argv:
        target = Path(argv[argv.index("--write-crops") + 1]) if len(argv) > argv.index("--write-crops") + 1 \
            else ROOT / "assets" / "lecture-template" / "src" / "linework" / "crops.ts"
        out = write_part_crops(target)
        n = sum(len(v) for v in part_crops().values())
        print(f"已写出 {out}（{n} 个部位的缺省取景框）")
        return 0
    if "--geometry" in argv:
        import sys as _sys
        i = argv.index("--geometry")
        target = argv[i + 1] if len(argv) > i + 1 and not argv[i + 1].startswith("--") else None
        errors, notes = geometry_problems(target)
        for e in errors:
            print(f"  ✗ {e}", file=_sys.stderr)
        for n in notes:
            print(f"  · {n}", file=_sys.stderr)
        print(f"线稿几何：{len(errors)} 个错误 · {len(notes)} 条提示")
        return 1 if errors else 0
    lib = load_library(argv[1] if len(argv) > 1 else None)
    for name, parts in lib.items():
        print(f"{name:<16} {' / '.join(parts)}")
    print(f"--- {len(lib)} 个线稿，"
          f"{sum(len(v) for v in lib.values())} 个部位 ---")
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv))
