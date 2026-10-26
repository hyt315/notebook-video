#!/usr/bin/env python3
"""commons-search.py — 从 Wikimedia Commons 找真实素材（图 / 视频 / 声音），按许可白名单过滤，下载进工程并自动署名。

只用 Python 标准库（urllib）+ ffmpeg（由 prepare-media.py 调用）。API 无需 key：https://commons.wikimedia.org/w/api.php

用法
  # 1. 搜（每个选题先搜一次；带 --project 会把这次搜索记进 manifests/commons-log.json，导演层门禁看它）
  python scripts/commons-search.py search "Hooke cork" [--type image|video|audio] [--category "Micrographia"]
         [--min-px 1200] [--limit 12] [--allow-by-sa] [--project ./my-video] [--json out.json] [--source commons|openverse]

  # 2. 选中一条，下载进工程（自动查许可、写 url / license / credit、生成上屏署名，走 prepare-media 入库与转码）
  python scripts/commons-search.py add ./my-video "File:Micrographia Schem 11.jpg" --id cork-plate
         [--width 2560] [--region cells 0.1 0.2 0.3 0.3] [--allow-by-sa] [--trim 0 8]

  # 第二个源：Openverse（https://api.openverse.org，MIT，免 key）——聚合 Flickr / 博物馆图片与 Freesound / Jamendo 声音，
  # 请求时只要 cc0 / pdm / by。add 时把标题写成 "openverse:image:<id>" 或 "openverse:audio:<id>"（search 结果里原样给出）。
  python scripts/commons-search.py search "paper rustle" --type audio --source openverse --project ./my-video
  python scripts/commons-search.py add ./my-video "openverse:audio:30d3f72b-…" --id rustle

  # 3. 交付前生成 CREDITS.md（成片署名清单，也给发布简介用）
  python scripts/commons-search.py credits ./my-video

许可白名单（默认）
  ✓ 公有领域（Public domain / PD-*）、CC0                      —— 不要求署名，但本工具照样署名（好习惯，也方便核查）
  ✓ CC BY 1.0–4.0                                                 —— 必须署名：作者 + 许可 + 来源链接，本工具自动生成
  ✗ CC BY-SA（默认排除）  —— "相同方式共享"：用它做的改编作品（整条片子很可能算）须以 CC BY-SA 发布。
                            短视频平台的发布条款通常与此冲突，所以缺省不用；确认接受时加 --allow-by-sa，manifest 会记 shareAlike:true，
                            validate-media 提示一次，CREDITS.md 写明成片的相应义务。
  ✗ GFDL / FAL / NC / ND / "Attribution"（无版本的自定义署名）/ "No restrictions"（Flickr Commons 无已知限制 ≠ PD）/ 未知 → 一律排除

礼仪（API etiquette）
  · 必带 User-Agent（含项目地址与联系方式），可用环境变量 NOTEBOOK_VIDEO_UA 覆盖；
  · 串行请求，相邻请求 ≥ 1 秒；maxlag=5；429 / 503 按 Retry-After 退避，最多重试 4 次；
  · 带 --project 时 API 响应缓存在 PROJECT/.cache/commons/（同一查询不重复打 API）。
退出码：0 成功；1 业务失败（许可不合格、找不到文件……每条都写了怎么改）；2 用法错误。
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
OPENVERSE = "https://api.openverse.org/v1"
UA = os.environ.get("NOTEBOOK_VIDEO_UA") or "notebook-video-commons/1.0 (https://github.com/hyt315/notebook-video; commons-search.py)"
SCRIPT_DIR = Path(__file__).resolve().parent
MIN_INTERVAL = 1.0
_last_request = [0.0]

EXTMETA = "LicenseShortName|UsageTerms|LicenseUrl|Artist|Credit|AttributionRequired|Copyrighted|Restrictions|ObjectName|ImageDescription|DateTimeOriginal"
TYPE_FILTER = {"image": "filetype:bitmap", "video": "filetype:video", "audio": "filetype:audio", "any": ""}
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
AUDIO_EXT = {".ogg", ".oga", ".opus", ".mp3", ".wav", ".flac"}
VIDEO_EXT = {".webm", ".ogv", ".mp4", ".mov"}
PRONUNCIATION = re.compile(r"^File:(LL-Q\d+|[A-Z][a-z]{1,2}(-[a-z]{2,4})?-[^.]+\.(ogg|oga|wav|mp3|flac)$)")


# ---------------------------------------------------------------- 许可判定（纯函数，tests/test_commons.py 覆盖）
def classify_license(short: str, usage: str = "", url: str = "", restrictions: str = "") -> dict:
    """把 Commons 的 extmetadata 许可字段归一。

    返回 {"verdict": "ok"|"sa"|"reject", "license": 归一化 id（validate-media 白名单认得的形式）,
          "attribution": 是否必须署名, "reason": 中文说明}
    """
    s = " ".join(x for x in (short, usage) if x).strip()
    low = s.lower()
    u = (url or "").lower()
    if restrictions and re.search(r"trademark|personality|insignia", restrictions, re.I):
        # 商标 / 肖像权 / 徽章：版权许可之外的限制，仍可用但要提醒
        extra = f"（另有非版权限制：{restrictions}）"
    else:
        extra = ""
    if not low:
        return {"verdict": "reject", "license": "unknown", "attribution": True, "reason": "没有许可信息"}
    if re.search(r"\bnc\b|non-?commercial", low) or re.search(r"\bnd\b|no-?deriv", low):
        return {"verdict": "reject", "license": "nc-nd", "attribution": True, "reason": "NC（非商用）/ ND（禁止演绎）不能用于短视频"}
    if "gfdl" in low or "gnu free documentation" in low:
        return {"verdict": "reject", "license": "gfdl", "attribution": True, "reason": "GFDL 要求随作品附全文许可，不适合视频"}
    if re.search(r"\bfal\b|free art", low):
        return {"verdict": "reject", "license": "fal", "attribution": True, "reason": "Free Art License 是相同方式共享类，缺省排除"}
    if "no restrictions" in low or "no known copyright" in low:
        return {"verdict": "reject", "license": "no-known-restrictions", "attribution": True,
                "reason": "「无已知版权限制」不等于公有领域，缺省排除（确有需要先人工核实来源）"}
    if low.startswith("cc0") or "cc0" in low or "publicdomain/zero" in u:
        return {"verdict": "ok", "license": "cc0", "attribution": False, "reason": "CC0" + extra}
    if re.search(r"public ?domain|^pd\b|\bpd-", low) or "publicdomain/mark" in u:
        return {"verdict": "ok", "license": "public-domain", "attribution": False, "reason": "公有领域" + extra}
    m = re.search(r"cc[ -]by(?:[ -](sa))?(?:[ -]([0-9.]+))?", low)
    if m:
        ver = m.group(2) or ""
        lid = "cc-by" + ("-sa" if m.group(1) else "") + (f"-{ver}" if ver else "")
        if m.group(1):
            return {"verdict": "sa", "license": lid, "attribution": True,
                    "reason": "CC BY-SA：相同方式共享——用它的改编作品须同样以 CC BY-SA 发布，缺省排除（--allow-by-sa 可放行）"}
        return {"verdict": "ok", "license": lid, "attribution": True, "reason": "CC BY：须署名（作者 + 许可 + 链接）" + extra}
    if low in ("attribution", "attribution only"):
        return {"verdict": "reject", "license": "attribution-custom", "attribution": True, "reason": "自定义「Attribution」许可，条款不明确，缺省排除"}
    return {"verdict": "reject", "license": "unknown", "attribution": True, "reason": f"不认识的许可「{s[:60]}」，缺省排除"}


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def strip_html(s: str) -> str:
    if not s:
        return ""
    p = _Text()
    p.feed(s)
    t = html.unescape(" ".join(p.parts))
    return re.sub(r"\s+", " ", t).strip()


def meta(ii: dict, key: str) -> str:
    v = (ii.get("extmetadata") or {}).get(key, {}).get("value", "")
    return v if isinstance(v, str) else str(v)


def describe(page: dict) -> dict:
    """一条 API page → 候选记录（含许可判定、署名串）。"""
    ii = (page.get("imageinfo") or [{}])[0]
    title = page.get("title", "")
    lic = classify_license(meta(ii, "LicenseShortName"), meta(ii, "UsageTerms"), meta(ii, "LicenseUrl"), meta(ii, "Restrictions"))
    credit_src = strip_html(meta(ii, "Credit"))
    artist = strip_html(meta(ii, "Artist"))
    if not artist or artist.lower() in ("unknown author", "unknown", "anonymous"):
        # 无作者（常见于博物馆数字化件）：用来源机构兜底，例如 "Wellcome Collection gallery (2018-03-30): https://…" → "Wellcome Collection gallery"
        inst = re.split(r"[:(（]|https?://", credit_src)[0].strip(" .,;") if credit_src else ""
        if not inst and credit_src:
            # 署名栏只有链接（如 Wellcome Images）：取第一个链接的域名作来源机构
            m = re.search(r"https?://(?:www\.)?([\w.-]+)", credit_src)
            inst = m.group(1) if m else ""
        artist = inst if inst and len(inst) <= 60 and "own work" not in inst.lower() else "Unknown author"
    page_url = ii.get("descriptionurl") or ("https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")))
    short = meta(ii, "LicenseShortName") or lic["license"]
    rec = {
        "title": title,
        "pageUrl": page_url,
        "mime": ii.get("mime", ""),
        "width": ii.get("width") or 0,
        "height": ii.get("height") or 0,
        "durationSec": ii.get("duration"),
        "bytes": ii.get("size") or 0,
        "url": ii.get("url", ""),
        "thumbUrl": ii.get("thumburl", ""),
        "artist": artist[:160],
        "creditSource": credit_src[:200],
        "licenseShort": short,
        "licenseUrl": meta(ii, "LicenseUrl"),
        "description": strip_html(meta(ii, "ImageDescription"))[:240],
        **{k: lic[k] for k in ("verdict", "license", "attribution", "reason")},
    }
    rec["credit"] = credit_line(rec)
    return rec


def short_author(author: str) -> str:
    """上屏署名里的作者：≥3 位作者写成「第一作者 et al.」（画面上放得下、读得完）；完整名单留在 CREDITS.md。"""
    names = [n.strip() for n in re.split(r",|;|、| and | & ", author or "") if n.strip()]
    return f"{names[0]} et al." if len(names) >= 3 else (author or "").strip()


def credit_line(rec: dict) -> str:
    """上屏 / CREDITS 用的一行署名（TASL：Title-Author-Source-License）。"""
    name = re.sub(r"^File:", "", rec["title"])
    name = re.sub(r"\.[A-Za-z0-9]{2,5}$", "", name)
    lic = rec.get("licenseShort") or rec.get("license")
    author = short_author(rec.get("artist") or "Unknown author")
    if author.lower() in ("unknown author", "unknown", "anonymous"):
        author = "佚名"
    return f"{author} · {lic} · Wikimedia Commons"[:120] if rec.get("license") != "public-domain" else f"{author} · 公有领域 · Wikimedia Commons"[:120]


# ---------------------------------------------------------------- HTTP
def http_json(params: dict, cache_dir: Path | None) -> dict:
    params = {"format": "json", "formatversion": "2", "maxlag": "5", **params}
    url = API + "?" + urllib.parse.urlencode(params)
    key = hashlib.sha1(url.encode()).hexdigest()
    if cache_dir:
        cf = cache_dir / f"{key}.json"
        if cf.is_file():
            return json.loads(cf.read_text(encoding="utf-8"))
    data = json.loads(http_get(url))
    if "error" in data:
        raise SystemExit(f"✗ Commons API 报错：{data['error'].get('code')} {data['error'].get('info', '')[:160]}")
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / f"{key}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def http_get(url: str, binary: bool = False):
    for attempt in range(5):
        wait = MIN_INTERVAL - (time.monotonic() - _last_request[0])
        if wait > 0:
            time.sleep(wait)
        _last_request[0] = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
                return body if binary else body.decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 4:
                ra = e.headers.get("Retry-After")
                delay = float(ra) if ra and ra.isdigit() else 2 ** (attempt + 1)
                print(f"  · Commons 限速（HTTP {e.code}），{delay:.0f} 秒后重试", file=sys.stderr)
                time.sleep(min(delay, 60))
                continue
            raise SystemExit(f"✗ 下载失败 HTTP {e.code}：{url[:120]}")
        except urllib.error.URLError as e:
            if attempt < 4:
                time.sleep(2 ** (attempt + 1))
                continue
            raise SystemExit(f"✗ 连不上 Commons（{e.reason}）。检查网络，或稍后重试。")
    raise SystemExit("✗ 多次重试仍失败")


# ---------------------------------------------------------------- 命令
def opt(args: list[str], name: str, n: int = 1, default=None):
    if name not in args:
        return default
    i = args.index(name)
    vals = args[i + 1:i + 1 + n]
    return vals if n > 1 else (vals[0] if vals else default)


ARITY = {"--type": 1, "--category": 1, "--limit": 1, "--min-px": 1, "--project": 1, "--json": 1, "--id": 1,
         "--width": 1, "--region": 5, "--trim": 2, "--allow-by-sa": 0, "--keep-pronunciations": 0, "--source": 1}


def positionals(args: list[str]) -> list[str]:
    out, i = [], 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            i += 1 + ARITY.get(a, 0)
            continue
        out.append(a)
        i += 1
    return out


def search(query: str, kind: str = "image", category: str | None = None, limit: int = 12,
           thumb_w: int = 1280, cache_dir: Path | None = None, keep_pron: bool = False) -> list[dict]:
    terms = [TYPE_FILTER.get(kind, "")]
    if category:
        terms.append(f'incategory:"{category.replace(" ", "_")}"')
    terms.append(query)
    params = {
        "action": "query", "generator": "search", "gsrsearch": " ".join(t for t in terms if t),
        "gsrnamespace": "6", "gsrlimit": str(min(max(limit, 1), 50)),
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiextmetadatafilter": EXTMETA,
        "iiurlwidth": str(thumb_w),
    }
    data = http_json(params, cache_dir)
    pages = sorted(data.get("query", {}).get("pages", []), key=lambda p: p.get("index", 0))
    recs = [describe(p) for p in pages]
    if kind == "audio" and not keep_pron:
        # Commons 的声音搜索结果大半是读音录音（Lingua Libre「LL-Q…」、「En-us-…」），对拟音没用，缺省滤掉
        recs = [r for r in recs if not PRONUNCIATION.search(r["title"])]
    return recs


def fileinfo(title: str, thumb_w: int, cache_dir: Path | None) -> dict:
    if not title.startswith("File:"):
        title = "File:" + title
    data = http_json({"action": "query", "titles": title, "prop": "imageinfo",
                      "iiprop": "url|size|mime|extmetadata", "iiextmetadatafilter": EXTMETA,
                      "iiurlwidth": str(thumb_w)}, cache_dir)
    pages = data.get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing"):
        raise SystemExit(f"✗ Commons 上没有「{title}」——从 search 的结果里原样复制 File: 标题")
    return describe(pages[0])


def log_search(proj: Path, query: str, kind: str, category: str | None, recs: list[dict], source: str = "commons") -> None:
    lf = proj / "manifests" / "commons-log.json"
    doc = json.loads(lf.read_text(encoding="utf-8")) if lf.is_file() else {"searches": []}
    doc.setdefault("searches", []).append({
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "source": source, "query": query, "type": kind, "category": category,
        "results": len(recs), "usable": sum(1 for r in recs if r["verdict"] == "ok"),
        "top": [{"title": r["title"], "license": r["license"], "verdict": r["verdict"]} for r in recs[:8]],
    })
    lf.parent.mkdir(parents=True, exist_ok=True)
    lf.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- Openverse（第二个源）
OV_LICENSE = {"cc0": "CC0", "pdm": "Public domain", "by": "CC BY"}


def ov_describe(r: dict, kind: str) -> dict:
    """Openverse 结果 → 与 Commons 相同的候选记录。"""
    short = OV_LICENSE.get(r.get("license", ""), r.get("license", "")).strip()
    if r.get("license") == "by" and r.get("license_version"):
        short = f"CC BY {r['license_version']}"
    lic = classify_license(short, "", r.get("license_url") or "")
    rec = {
        "title": f"openverse:{kind}:{r.get('id')}", "pageUrl": r.get("foreign_landing_url") or r.get("detail_url", ""),
        "mime": f"{'audio' if kind == 'audio' else 'image'}/{r.get('filetype') or ''}".rstrip("/"),
        "width": r.get("width") or 0, "height": r.get("height") or 0,
        "durationSec": (r.get("duration") or 0) / 1000 if kind == "audio" else None,
        "bytes": r.get("filesize") or 0, "url": r.get("url", ""), "thumbUrl": r.get("thumbnail") or "",
        "artist": (r.get("creator") or "Unknown author")[:160], "creditSource": f"{r.get('provider', '')} via Openverse",
        "licenseShort": short, "licenseUrl": r.get("license_url") or "", "description": (r.get("title") or "")[:240],
        **{k: lic[k] for k in ("verdict", "license", "attribution", "reason")},
        "displayTitle": r.get("title") or "", "provider": r.get("provider", ""),
    }
    rec["credit"] = f"{short_author(rec['artist'])} · {short} · {rec['provider'] or 'Openverse'}"[:120] if rec["license"] != "public-domain" else f"{short_author(rec['artist'])} · 公有领域 · {rec['provider'] or 'Openverse'}"[:120]
    return rec


def ov_search(query: str, kind: str, limit: int, cache_dir: Path | None) -> list[dict]:
    if kind not in ("image", "audio"):
        raise SystemExit("✗ Openverse 只有图片和声音（--type image|audio）")
    url = f"{OPENVERSE}/{'audio' if kind == 'audio' else 'images'}/?" + urllib.parse.urlencode(
        {"q": query, "license": "cc0,pdm,by", "page_size": str(min(max(limit, 1), 20)), "mature": "false"})
    data = cached_json(url, cache_dir)
    return [ov_describe(r, kind) for r in data.get("results", [])]


def ov_fileinfo(title: str, cache_dir: Path | None) -> dict:
    m = re.fullmatch(r"openverse:(image|audio):([\w-]+)", title)
    if not m:
        raise SystemExit(f"✗ Openverse 标题格式是 openverse:image:<id> 或 openverse:audio:<id>（收到 {title}）")
    kind, oid = m.groups()
    data = cached_json(f"{OPENVERSE}/{'audio' if kind == 'audio' else 'images'}/{oid}/", cache_dir)
    return ov_describe(data, kind)


def cached_json(url: str, cache_dir: Path | None) -> dict:
    key = hashlib.sha1(url.encode()).hexdigest()
    if cache_dir and (cache_dir / f"{key}.json").is_file():
        return json.loads((cache_dir / f"{key}.json").read_text(encoding="utf-8"))
    data = json.loads(http_get(url))
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / f"{key}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def cmd_search(args: list[str]) -> int:
    pos = positionals(args)
    if not pos:
        print(__doc__)
        return 2
    query = pos[0]
    kind = opt(args, "--type", default="image")
    if kind not in TYPE_FILTER:
        print(f"✗ --type 只能是 {', '.join(TYPE_FILTER)}")
        return 2
    category = opt(args, "--category")
    limit = int(opt(args, "--limit", default="12"))
    min_px = int(opt(args, "--min-px", default="1000" if kind == "image" else "0"))
    allow_sa = "--allow-by-sa" in args
    proj = Path(opt(args, "--project")).resolve() if opt(args, "--project") else None
    cache = proj / ".cache" / "commons" if proj else None
    source = opt(args, "--source", default="commons")
    if source == "openverse":
        recs = ov_search(query, kind, limit, cache)
    elif source == "commons":
        recs = search(query, kind, category, limit, cache_dir=cache, keep_pron="--keep-pronunciations" in args)
    else:
        print("✗ --source 只能是 commons 或 openverse")
        return 2
    if proj:
        log_search(proj, query, kind, category, recs, source)
    shown = 0
    print(f"{'Openverse' if source == 'openverse' else 'Commons'} · 「{query}」{f' · 分类 {category}' if category else ''} · {kind} · {len(recs)} 条")
    for r in recs:
        long_edge = max(r["width"], r["height"])
        usable = r["verdict"] == "ok" or (r["verdict"] == "sa" and allow_sa)
        small = kind in ("image", "video") and long_edge < min_px
        mark = "✓" if usable and not small else "✗"
        why = r["reason"] if not usable else (f"太小（长边 {long_edge}px < {min_px}）" if small else r["reason"])
        dims = f"{r['width']}×{r['height']}" if r["width"] else (f"{r['durationSec']:.1f}s" if r.get("durationSec") else "")
        shown_title = r['title'] + (f"  「{r['displayTitle'][:40]}」" if r.get('displayTitle') else "")
        print(f"  {mark} {shown_title[:110]}\n      {dims} {r['mime']} · {r['licenseShort']} · {r['artist'][:40]} — {why}")
        shown += mark == "✓"
    print(f"可用 {shown} 条。下一步：python scripts/commons-search.py add <工程> \"File:…\" --id <素材id>")
    jo = opt(args, "--json")
    if jo:
        Path(jo).write_text(json.dumps(recs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


def pick_download(rec: dict, width: int) -> tuple[str, str]:
    """返回 (下载地址, 扩展名)。图片：原图不大于 width×1.25 且 < 30 MB 用原图，否则用缩略图；视频 / 声音一律原文件。"""
    ext = Path(urllib.parse.urlparse(rec["url"]).path).suffix.lower()
    if rec["mime"].startswith("image/") and ext not in (".svg", ".tif", ".tiff", ".gif"):
        if rec["width"] <= width * 1.25 and rec["bytes"] < 30_000_000:
            return rec["url"], ext
        if rec["thumbUrl"]:
            return rec["thumbUrl"], Path(urllib.parse.urlparse(rec["thumbUrl"]).path).suffix.lower() or ".jpg"
    if rec["mime"].startswith("image/") and rec["thumbUrl"]:
        # svg / tif / gif → 用 Commons 渲染好的 PNG/JPG 缩略图
        return rec["thumbUrl"], Path(urllib.parse.urlparse(rec["thumbUrl"]).path).suffix.lower() or ".png"
    return rec["url"], ext


def cmd_add(args: list[str]) -> int:
    pos = positionals(args)
    if len(pos) < 2 or not opt(args, "--id"):
        print("用法：commons-search.py add PROJECT \"File:标题\" --id 素材id [--width 2560] [--region id x y w h] [--allow-by-sa] [--trim 0 8]")
        return 2
    proj = Path(pos[0]).resolve()
    if not (proj / "manifests").is_dir():
        print(f"✗ {proj} 不是 notebook-video 工程（没有 manifests/）—— 先 new-project")
        return 1
    mid = opt(args, "--id")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,40}", mid):
        print("✗ --id 只用小写字母 / 数字 / 连字符，例如 cork-plate")
        return 2
    width = int(opt(args, "--width", default="2560"))
    rec = ov_fileinfo(pos[1], proj / ".cache" / "commons") if pos[1].startswith("openverse:") else fileinfo(pos[1], width, proj / ".cache" / "commons")
    allow_sa = "--allow-by-sa" in args
    if rec["verdict"] == "reject" or (rec["verdict"] == "sa" and not allow_sa):
        print(f"✗ {rec['title']}：{rec['reason']}\n  换一条（search 结果里打 ✓ 的），或用组件重画。")
        return 1
    url, ext = pick_download(rec, width)
    kind = "audio" if (rec["mime"].startswith("audio/") or ext in AUDIO_EXT or rec["mime"] == "application/ogg") and not rec["width"] else None
    tmpdir = proj / ".cache" / "commons" / "dl"
    tmpdir.mkdir(parents=True, exist_ok=True)
    src = tmpdir / f"{mid}{ext}"
    print(f"↓ {rec['title']}（{rec['licenseShort']}）← {url[:100]}")
    src.write_bytes(http_get(url, binary=True))
    cmd = [sys.executable, str(SCRIPT_DIR / "prepare-media.py"), str(proj), "--add", str(src), "--id", mid,
           "--source", "web", "--url", rec["pageUrl"], "--license", rec["license"], "--credit", rec["credit"]]
    for i, a in enumerate(args):
        if a == "--region":
            cmd += ["--region", *args[i + 1:i + 6]]
    tr = opt(args, "--trim", 2)
    if tr:
        cmd += ["--trim", *tr]
    if kind == "audio":
        cmd += ["--keep-audio"]
    r = subprocess.run(cmd)
    if r.returncode:
        return r.returncode
    # 补 Commons 专属字段（prepare-media 已写好通用字段）
    for name in ("manifests/media.json", "src/media.json"):
        f = proj / name
        doc = json.loads(f.read_text(encoding="utf-8"))
        e = next(x for x in doc["items"] if x["id"] == mid)
        e["commons"] = {k: rec[k] for k in ("title", "pageUrl", "artist", "licenseShort", "licenseUrl", "attribution", "creditSource")}
        if rec["title"].startswith("openverse:"):
            e["commons"]["source"] = "openverse"
            e["commons"]["displayTitle"] = rec.get("displayTitle", "")
        e["commons"]["fetched"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        e["commons"]["original"] = {"width": rec["width"], "height": rec["height"], "mime": rec["mime"]}
        if rec["verdict"] == "sa":
            e["shareAlike"] = True
        f.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lf = proj / "manifests" / "commons-log.json"
    if lf.is_file():
        lg = json.loads(lf.read_text(encoding="utf-8"))
        lg.setdefault("picked", []).append({"id": mid, "title": rec["title"], "license": rec["license"]})
        lf.write_text(json.dumps(lg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"✓ {mid}: 已入库，署名「{rec['credit']}」会随组件上屏。交付前跑：commons-search.py credits {proj}")
    return 0


def build_credits(items: list[dict]) -> str:
    """media.json items → CREDITS.md 文本（纯函数，测试覆盖）。"""
    web = [e for e in items if e.get("source") == "web"]
    lines = ["# CREDITS · 第三方素材", "",
             "本片使用的第三方素材，按出现顺序列出（作者 · 标题 · 许可 · 来源）。", ""]
    sa = False
    for e in web:
        c = e.get("commons") or {}
        title = c.get("displayTitle") or re.sub(r"^File:", "", c.get("title", "")) or e.get("id")
        lic = c.get("licenseShort") or e.get("license")
        lic_url = c.get("licenseUrl") or ""
        author = c.get("artist") or e.get("credit", "")
        lines.append(f"- **{title}** — {author}。{lic}{f'（{lic_url}）' if lic_url else ''}。来源：{e.get('url')}")
        if e.get("shareAlike"):
            sa = True
    if not web:
        lines.append("- （无）")
    lines += ["", "字体：LXGW WenKai Lite、Noto Serif SC（SIL OFL 1.1）。音效：notebook-video 内置库（见 public/sfx/LICENSE.txt）。"]
    if sa:
        lines += ["", "**相同方式共享**：本片含 CC BY-SA 素材，成片作为改编作品应以 CC BY-SA 4.0（或兼容版本）发布，并在发布简介里写明。"]
    lines += ["", "发布简介用（短版）：", "", "素材：" + "；".join(
        (e.get("credit") or "") for e in web) if web else ""]
    return "\n".join(lines).rstrip() + "\n"


def cmd_credits(args: list[str]) -> int:
    if not args:
        print("用法：commons-search.py credits PROJECT")
        return 2
    proj = Path(args[0]).resolve()
    man = proj / "manifests" / "media.json"
    items = json.loads(man.read_text(encoding="utf-8")).get("items", []) if man.is_file() else []
    txt = build_credits(items)
    (proj / "CREDITS.md").write_text(txt, encoding="utf-8")
    print(txt)
    print(f"✓ 已写 {proj / 'CREDITS.md'}")
    return 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "search":
        return cmd_search(rest)
    if cmd == "add":
        return cmd_add(rest)
    if cmd == "credits":
        return cmd_credits(rest)
    print(f"✗ 不认识的子命令「{cmd}」（search / add / credits）")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
