#!/usr/bin/env python3
"""validate-media.py — 真实素材门禁（构建期）。只用标准库；视频检查需要 ffprobe。

用法：python validate-media.py PROJECT

P0（拦）
  · manifests/media.json 里的文件不在 public/media/；kind 与扩展名不符；
  · 放大糊：显示尺寸（含区域推近倍数）/ 原图像素 > 1.5（按 1920×1080 交付算）；
  · 视频不是 H.264 + 恒定 30fps + yuv420p（跑 prepare-media.py 转码）；
  · source:"web" 缺 url / license / credit，或 license 不在可用清单（NC / ND / 全部权利保留 / 未知 → 用组件重画）；
  · src/media.json 与 manifests/media.json 不一致（跑 prepare-media.py 同步）；
  · focus / highlight / callout 引用了不存在的区域；区域坐标不在 0–1。
P1（提示）
  · muted:false（会出声，确认是有意的）；登记了但没被任何场景用到；2560×1440 交付时放大 > 1.5。
署名一定显示：MediaFrame 对 source:"web" 素材无条件画署名徽章，没有关掉它的参数（本门禁同时确认源码里没人绕过）。
"""
from __future__ import annotations

import json
import re
import struct
import subprocess
import sys
from pathlib import Path

UPSCALE_MAX = 1.5
LICENSE_OK = re.compile(r"^(cc0|cc-by(-sa)?(-[0-9.]+)?|public[- ]domain|pd|pexels|unsplash|pixabay|mit|apache-2\.0|own|user|official-docs)$", re.I)
EXT = {"image": {".png", ".jpg", ".jpeg", ".webp"}, "video": {".mp4"}, "gif": {".gif"}}


def img_size(p: Path) -> tuple[int, int] | None:
    b = p.read_bytes()[:65536]
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", b[16:24])
    if b[:2] == b"\xff\xd8":
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xFF:
                i += 1
                continue
            mk = b[i + 1]
            if mk in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP" and b[12:16] == b"VP8X":
        return 1 + int.from_bytes(b[24:27], "little"), 1 + int.from_bytes(b[27:30], "little")
    return None


def usages(proj: Path) -> list[dict]:
    """场景源码里的 <MediaFrame …>（字面量 id / w / h / focus / focusZoom），以及 auto 草稿的 story.ts。"""
    out = []
    for f in (proj / "src").rglob("*.tsx"):
        if f.name == "media-frame.tsx":
            continue
        s = f.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"<MediaFrame\b(.*?)/>", s, re.S):
            t = m.group(1)
            g = lambda k, pat=r"\{?\"?([\w.-]+)\"?\}?": (re.search(rf"\b{k}=" + pat, t) or [None, None])[1]
            lit = re.search(r"\bid=(?:\"([\w.-]+)\"|\{['\"]([\w.-]+)['\"]\})", t)
            if not lit:
                continue  # 非字面量 id（例如 auto.tsx 里的 e.media）：由 story.ts 那一路检查
            u = {"file": f.name, "id": lit.group(1) or lit.group(2), "w": g("w"), "h": g("h"), "focus": g("focus"), "focusZoom": g("focusZoom"),
                 "regions": re.findall(r"region:\s*['\"]([\w-]+)['\"]", t) + re.findall(r"highlight=\{\[([^\]]*)\]\}", t)}
            out.append(u)
    st = proj / "src" / "story.ts"
    if st.is_file():
        s = st.read_text(encoding="utf-8")
        for m in re.finditer(r"\{[^{}]*\"kind\":\s*\"media\"[^{}]*\}", s):
            try:
                e = json.loads(m.group(0))
                out.append({"file": "story.ts", "id": e.get("media"), "w": e.get("w"), "h": e.get("h"), "focus": e.get("region"), "focusZoom": None, "regions": []})
            except json.JSONDecodeError:
                pass
    return out


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    proj = Path(argv[0]).resolve()
    man = proj / "manifests" / "media.json"
    p0, p1 = [], []
    if not man.is_file():
        print("validate-media · 没有 manifests/media.json（本片不用真实素材）\n结论：P0=0 P1=0 → PASS")
        return 0
    doc = json.loads(man.read_text(encoding="utf-8"))
    items = {e.get("id"): e for e in doc.get("items", [])}
    srcj = proj / "src" / "media.json"
    if items and (not srcj.is_file() or json.loads(srcj.read_text(encoding="utf-8")) != doc):
        p0.append("src/media.json 与 manifests/media.json 不一致 —— 跑 python scripts/prepare-media.py <工程> 同步")
    for mid, e in items.items():
        f = proj / "public" / "media" / str(e.get("file", ""))
        kind = e.get("kind")
        if not f.is_file():
            p0.append(f"{mid}: 文件 public/media/{e.get('file')} 不存在")
            continue
        if kind not in EXT or f.suffix.lower() not in EXT[kind]:
            p0.append(f"{mid}: kind={kind} 与文件 {f.name} 不符（动图 / 非 MP4 视频先跑 prepare-media.py 转成 H.264 MP4）")
        for r in e.get("focusRegions", []) or []:
            if not all(0 <= r.get(k, -1) <= 1 for k in "xywh") or r["x"] + r["w"] > 1.0001 or r["y"] + r["h"] > 1.0001:
                p0.append(f"{mid}: 区域 {r.get('id')} 坐标必须是 0–1 的相对值且不出界")
        if e.get("source") == "web":
            miss = [k for k in ("url", "license", "credit") if not e.get(k)]
            if miss:
                p0.append(f"{mid}: 网上来的素材必须写 {' / '.join(miss)}（署名会显示在画面上）")
            elif not LICENSE_OK.match(str(e["license"]).strip()):
                p0.append(f"{mid}: 许可「{e['license']}」不能用于本片（NC / ND / 全部权利保留 / 未知）—— 换 CC0 / CC-BY / Pexels / Unsplash 素材，或用组件重画")
        if e.get("muted") is False:
            p1.append(f"{mid}: muted:false —— 素材原声会进成片，确认是有意的")
        if kind == "video":
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,r_frame_rate,avg_frame_rate,pix_fmt,width,height", "-of", "json", str(f)], capture_output=True, text=True)
            try:
                v = json.loads(r.stdout)["streams"][0]
            except (json.JSONDecodeError, KeyError, IndexError):
                p0.append(f"{mid}: ffprobe 读不了视频（ffmpeg 没装或文件坏了）")
                continue
            if v.get("codec_name") != "h264" or v.get("r_frame_rate") != "30/1" or v.get("avg_frame_rate") != "30/1" or v.get("pix_fmt") != "yuv420p":
                p0.append(f"{mid}: 视频 {v.get('codec_name')} {v.get('avg_frame_rate')} {v.get('pix_fmt')} —— 需要 H.264 恒定 30fps yuv420p：跑 prepare-media.py")
            size = (v.get("width"), v.get("height"))
        else:
            size = img_size(f)
        if not size or not size[0]:
            p0.append(f"{mid}: 读不出像素尺寸")
            continue
        e["_px"] = size
    used = set()
    for u in usages(proj):
        mid = u["id"]
        used.add(mid)
        e = items.get(mid)
        if not e:
            p0.append(f"{u['file']}: <MediaFrame id=\"{mid}\"> 在 manifests/media.json 里没有登记")
            continue
        regs = {r["id"] for r in e.get("focusRegions", []) or []}
        for rid in [u["focus"]] + [x.strip(" '\"") for x in ",".join(u["regions"]).split(",") if x.strip(" '\"")]:
            if rid and rid not in regs:
                p0.append(f"{u['file']}: 素材 {mid} 没有区域「{rid}」（可用：{sorted(regs) or '无'}）")
        try:
            w, h = float(u["w"]), float(u["h"])
        except (TypeError, ValueError):
            continue
        if "_px" not in e:
            continue
        iw, ih = e["_px"]
        k = min(w / iw, h / ih)
        zoom = 1.0
        if u["focus"] and u["focus"] in regs:
            r = next(r for r in e["focusRegions"] if r["id"] == u["focus"])
            try:
                zoom = float(u["focusZoom"]) if u["focusZoom"] else min(2.4, max(1.0, 0.8 * min(1 / r["w"], 1 / r["h"])))
            except ValueError:
                zoom = 2.4
        up = k * zoom
        if up > UPSCALE_MAX:
            p0.append(f"{mid}: 原图 {iw}×{ih} 显示成 {w:.0f}×{h:.0f}（推近 ×{zoom:.2f}）= 放大 {up:.2f} 倍 > {UPSCALE_MAX} 会糊 —— 换更大的原图、缩小显示框或降低 focusZoom")
        elif up * 4 / 3 > UPSCALE_MAX:
            p1.append(f"{mid}: 2560×1440 交付时放大 {up * 4 / 3:.2f} 倍（1080p 交付没问题）")
    for mid in items:
        if mid not in used:
            p1.append(f"{mid}: 登记了但没有场景用到")
    for f in (proj / "src").rglob("*.tsx"):
        if f.name != "media-frame.tsx" and re.search(r"data-media-credit|hideCredit", f.read_text(encoding="utf-8", errors="ignore")):
            p0.append(f"{f.name}: 不许自己画 / 关掉署名徽章（MediaFrame 会自动显示）")
    print(f"validate-media · {len(items)} 条素材")
    for x in p0:
        print(f"  ✗ P0 {x}")
    for x in p1:
        print(f"  · P1 {x}")
    print(f"结论：P0={len(p0)} P1={len(p1)} → {'FAIL' if p0 else 'PASS'}")
    return 1 if p0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
