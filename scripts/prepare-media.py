#!/usr/bin/env python3
"""prepare-media.py — 真实素材（截图 / 录屏 / 动图）入库与转码。只用标准库 + ffmpeg/ffprobe。

用法
  python prepare-media.py PROJECT                         # 重新探测 manifests/media.json 里全部素材、按需转码、同步 src/media.json
  python prepare-media.py PROJECT --add FILE --id pr-page   # FILE 可以是图片 / 视频 / 动图 / 声音 [--source user|web] [--url URL] [--license CC-BY-4.0]
                          [--credit "作者 / 站点"] [--trim 2.0 9.5] [--keep-audio] [--region diff 0.1 0.3 0.6 0.25]

做的事
  · 文件复制进 PROJECT/public/media/（文件名 = id + 扩展名）；
  · 探测宽高（ffprobe）写回 manifest 的 width/height；
  · 视频 / 动图：不是 H.264 + 恒定 30fps + yuv420p，或者带音轨但要静音 → 转成 H.264 CFR 30fps MP4（缺省去掉音轨）；
    动图转码后 kind 记为 video（OffthreadVideo 帧驱动播放），origKind 记 gif；
  · 同步一份到 PROJECT/src/media.json（组件从这里读）。
退出码：0 成功，1 失败（每条错误都写了怎么改）。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
VID_EXT = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".ogv"}
AUD_EXT = {".wav", ".mp3", ".ogg", ".oga", ".opus", ".flac", ".m4a"}


def probe(path: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"✗ ffprobe 读不了 {path.name}：{r.stderr.strip()[:200]}（文件坏了，或者 ffmpeg 没装进 PATH）")
    return json.loads(r.stdout)


def vstream(info: dict) -> dict:
    return next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})


def needs_transcode(info: dict, keep_audio: bool) -> list[str]:
    v = vstream(info)
    why = []
    if v.get("codec_name") != "h264":
        why.append(f"编码 {v.get('codec_name')} ≠ h264")
    if v.get("r_frame_rate") != "30/1" or v.get("avg_frame_rate") not in ("30/1", None):
        why.append(f"帧率 {v.get('avg_frame_rate')} ≠ 恒定 30fps")
    if v.get("pix_fmt") != "yuv420p":
        why.append(f"像素格式 {v.get('pix_fmt')} ≠ yuv420p")
    has_audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
    if has_audio and not keep_audio:
        why.append("带音轨（缺省静音，去掉）")
    return why


def transcode(src: Path, dst: Path, keep_audio: bool, trim: tuple[float, float] | None = None) -> None:
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if trim:
        cmd += ["-ss", f"{trim[0]}", "-to", f"{trim[1]}"]
    cmd += ["-i", str(src), "-vf", "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p", "-c:v", "libx264",
            "-preset", "medium", "-crf", "18", "-fps_mode", "cfr", "-movflags", "+faststart"]
    cmd += (["-c:a", "aac", "-ar", "48000", "-ac", "2"] if keep_audio else ["-an"])
    tmp = dst.with_name(dst.stem + ".tmp.mp4")
    r = subprocess.run(cmd + [str(tmp)], capture_output=True, text=True)
    if r.returncode:
        # 老版本 ffmpeg 没有 -fps_mode：退回 -vsync cfr
        cmd = [("-vsync" if c == "-fps_mode" else c) for c in cmd]
        r = subprocess.run(cmd + [str(tmp)], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"✗ 转码失败 {src.name}：{r.stderr.strip()[:300]}")
    tmp.replace(dst)


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("--"):
        print(__doc__)
        return 2
    proj = Path(argv[0]).resolve()
    args = argv[1:]
    man = proj / "manifests" / "media.json"
    doc = json.loads(man.read_text(encoding="utf-8")) if man.is_file() else {"items": []}
    items = doc.setdefault("items", [])
    mdir = proj / "public" / "media"
    mdir.mkdir(parents=True, exist_ok=True)

    def opt(name: str, n: int = 1):
        if name not in args:
            return None
        i = args.index(name)
        vals = args[i + 1:i + 1 + n]
        return vals if n > 1 else (vals[0] if vals else None)

    if "--add" in args:
        src = Path(opt("--add")).resolve()
        mid = opt("--id")
        if not src.is_file() or not mid:
            print("✗ --add 需要一个存在的文件和 --id")
            return 1
        ext = src.suffix.lower()
        kind = "image" if ext in IMG_EXT else "gif" if ext == ".gif" else "video" if ext in VID_EXT else "audio" if ext in AUD_EXT else None
        if ext in (".ogg", ".oga") and kind == "audio" and vstream(probe(src)):
            kind = "video"  # Ogg 容器里有视频流（Commons 的 .ogv 有时叫 .ogg）
        if not kind:
            print(f"✗ 不认识的素材类型 {ext}（图片 png/jpg/webp，视频 mp4/mov/webm，动图 gif，声音 wav/mp3/ogg/opus/flac）")
            return 1
        dst = mdir / f"{mid}{ext}"
        if src != dst:
            shutil.copyfile(src, dst)
        e = next((x for x in items if x["id"] == mid), None) or {"id": mid}
        if e not in items:
            items.append(e)
        e.update({"file": dst.name, "kind": kind, "source": opt("--source") or e.get("source", "user")})
        for k in ("url", "license", "credit"):
            if opt(f"--{k}"):
                e[k] = opt(f"--{k}")
        tr = opt("--trim", 2)
        if tr:
            e["trimStartSec"], e["trimEndSec"] = float(tr[0]), float(tr[1])
        e["muted"] = "--keep-audio" not in args
        # --region id x y w h（可重复）
        regs = [x for x in e.get("focusRegions", [])]
        for i, a in enumerate(args):
            if a == "--region":
                rid, *nums = args[i + 1:i + 6]
                regs = [r for r in regs if r["id"] != rid] + [{"id": rid, **dict(zip("xywh", map(float, nums)))}]
        if regs:
            e["focusRegions"] = regs

    bad = 0
    for e in items:
        f = mdir / e.get("file", "")
        if not f.is_file():
            print(f"✗ {e.get('id')}: public/media/{e.get('file')} 不存在 —— 用 --add 重新登记")
            bad += 1
            continue
        info = probe(f)
        v = vstream(info)
        if e.get("kind") == "audio":
            # 声音：统一转成 48 kHz 立体声 WAV（Remotion 解码最稳）；--trim 只记播放区间，不改文件
            if f.suffix.lower() != ".wav":
                out = f.with_suffix(".wav")
                tmp = out.with_name(out.stem + ".tmp.wav")
                cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(f), "-vn", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(tmp)]
                r = subprocess.run(cmd, capture_output=True, text=True)
                if r.returncode:
                    print(f"✗ {e['id']}: 声音转码失败：{r.stderr.strip()[:200]}")
                    bad += 1
                    continue
                tmp.replace(out)
                if out != f:
                    f.unlink()
                e["file"] = out.name
                info = probe(out)
            e["durationSec"] = round(float(info.get("format", {}).get("duration", 0) or 0), 3)
            e["muted"] = False
            print(f"✓ {e['id']}: audio {e['durationSec']}s ({e['file']})")
            continue
        if e.get("kind") in ("video", "gif"):
            why = needs_transcode(info, e.get("muted") is False)
            if e.get("kind") == "gif" or why:
                out = f.with_suffix(".mp4") if f.suffix.lower() != ".mp4" else f
                print(f"· {e['id']}: 转码 → {out.name}（{'；'.join(why) or 'gif → mp4'}）")
                transcode(f, out, e.get("muted") is False)
                if out != f:
                    f.unlink()
                if e["kind"] == "gif":
                    e["origKind"] = "gif"
                    e["kind"] = "video"
                e["file"] = out.name
                info = probe(out)
                v = vstream(info)
            e["durationSec"] = round(float(info.get("format", {}).get("duration", 0) or 0), 3)
        e["width"], e["height"] = int(v.get("width", 0)), int(v.get("height", 0))
        print(f"✓ {e['id']}: {e['kind']} {e['width']}×{e['height']} ({e['file']})")
    txt = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    man.parent.mkdir(parents=True, exist_ok=True)
    man.write_text(txt, encoding="utf-8")
    (proj / "src").mkdir(exist_ok=True)
    (proj / "src" / "media.json").write_text(txt, encoding="utf-8")
    print(f"已写 manifests/media.json 与 src/media.json（{len(items)} 条）。下一步：python validate-media.py {proj}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
