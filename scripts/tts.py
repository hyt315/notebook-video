#!/usr/bin/env python3
"""tts.py · 旁白合成（TTS 成为正式步骤，而不是外挂）

用法：
    python scripts/tts.py PROJECT [--engine=edge|file] [--voice=zh-CN-YunxiNeural] [--rate=+0%]

产物（写进 PROJECT）：
    audio/narration.mp3        旁白音轨
    audio/narration.mp3.json   词级时间 [{part,start,end}]，毫秒
    audio/narration.meta.json  {engine, voice, estimated, generated_at}
并删除 audio/.silent-placeholder（静音占位不算旁白）。

引擎：
  · edge  微软 Edge 在线语音（pip install edge-tts；需要联网）。词级时间来自 WordBoundary。
  · file  用户自备录音 / 别家 TTS：把音频放到 audio/narration.mp3，再跑本脚本。
          没有词级对齐时按字数均分（estimated=true，标点也占时长）——字幕仍按这个估计时间排，
          只能大致对上，正式交付请用 edge 引擎或自己对时间。

失败一律 rc=3 并给出**两条可走的路**（装 edge-tts / 换 --engine=file），
不许悄悄退回静音占位——那正是旧版"成片没人说话"的来源。
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import narration_contract  # noqa: E402  （必须在 sys.path 之后导入）

SPOKEN_EXTRA = "0123456789.%+-"


def spoken(ch: str) -> bool:
    return ch.isalnum() or ch in SPOKEN_EXTRA or "\u4e00" <= ch <= "\u9fff"


def split_chars(text: str) -> list[str]:
    return [c for c in text if not c.isspace()]


def read_lines(project: Path) -> list[str]:
    p = project / "narration.txt"
    if not p.is_file():
        return []
    return [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def fail(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 3


def merge_punctuation(words: list[dict], source: str) -> list[dict]:
    """把标点补回词级时间：Edge 的 WordBoundary 只给"读出来的词"，句号/逗号不在里面，
    而字幕校验比对的是 cue.text 的逐字拼接。缺标点 → 每条 cue 都判"text differs"。
    只有整条源文本按顺序对得上时才补；对不上就原样返回（交给 compose 报 P1，不硬改）。
    """
    src = [c for c in source if not c.isspace()]
    out: list[dict] = []
    wi, prev_end = 0, 0
    for ch in src:
        if wi < len(words) and words[wi]["part"] == ch:
            out.append(words[wi])
            prev_end = words[wi]["end"]
            wi += 1
        elif not ch.isalnum():
            out.append({"part": ch, "start": prev_end, "end": prev_end + 1})
        else:
            return words
    return out if wi == len(words) else words


def synth_edge(text: str, voice: str, rate: str, out_mp3: Path) -> tuple[list[dict], str]:
    try:
        import asyncio

        import edge_tts
    except ImportError:
        raise RuntimeError(
            "没有安装 edge-tts。两条路：\n"
            "  1) pip install edge-tts（然后重跑同一条命令）\n"
            "  2) 用你自己的录音：把音频放到 audio/narration.mp3，再跑 --engine=file"
        )
    words: list[dict] = []

    async def run() -> None:
        comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
        with out_mp3.open("wb") as f:
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    # offset / duration 单位是 100ns
                    a = round(chunk["offset"] / 10000)
                    b = round((chunk["offset"] + chunk["duration"]) / 10000)
                    cs = split_chars(chunk["text"])
                    for i, ch in enumerate(cs):
                        words.append({"part": ch,
                                      "start": round(a + (b - a) * i / max(1, len(cs))),
                                      "end": round(a + (b - a) * (i + 1) / max(1, len(cs)))})

    try:
        asyncio.run(run())
    except Exception as e:  # 网络 / 服务端 403 / 证书……
        detail = f"{e.__class__.__name__}: {e}"
        hint = ""
        if any(k in detail for k in ("403", "401", "Sec-MS-GEC", "Unauthorized")):
            # 实测：edge-tts 7.2.8 会被服务端 403（Sec-MS-GEC 校验变更），升到 7.3.1 即恢复。
            # 这时候「检查网络」是最没用的建议——网络是好的，是客户端太旧。
            hint = ("**这是 edge-tts 版本过旧的典型症状**（服务端改了 Sec-MS-GEC 校验），不是网络问题。\n"
                    "先升级再重试：pip install -U edge-tts\n\n")
        raise RuntimeError(
            f"edge-tts 合成失败：{detail}\n"
            f"{hint}"
            "两条路：\n"
            "  1) 检查网络后重试（edge-tts 需要连 speech.platform.bing.com）\n"
            "  2) 用你自己的录音：把音频放到 audio/narration.mp3，再跑 --engine=file"
        ) from e
    if not words:
        raise RuntimeError(
            "edge-tts 合成完成但没有返回词边界（boundary=WordBoundary 为空）——"
            "无法把字幕对齐到音频。两条路：\n"
            "  1) 升级 edge-tts 后重试：pip install -U edge-tts\n"
            "  2) 用你自己的录音：把音频放到 audio/narration.mp3，再跑 --engine=file"
        )
    return words, "edge"


def audio_duration_ms(path: Path) -> int | None:
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", str(path)],
                           capture_output=True, text=True, timeout=60)
        return round(float((r.stdout or "").strip()) * 1000)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def synth_file(project: Path, lines: list[str]) -> tuple[list[dict], str]:
    audio = project / "audio" / "narration.mp3"
    if not audio.is_file() or audio.stat().st_size == 0:
        raise RuntimeError(
            "audio/narration.mp3 不存在或为空。两条路：\n"
            "  1) 先把录音 / 别家 TTS 的音频放到 audio/narration.mp3，再重跑\n"
            "  2) 用在线引擎：python scripts/tts.py . --engine=edge"
        )
    total = audio_duration_ms(audio)
    if not total:
        raise RuntimeError("读不出 audio/narration.mp3 的时长（需要 ffprobe）")
    text = "".join(split_chars("".join(lines)))
    chars = [c for c in text if not c.isspace()]
    if not chars:
        raise RuntimeError("narration.txt 是空的：先写每行一句的旁白")
    # 留 200ms 尾部，其余按字数均分
    usable = max(1, total - 200)
    words = []
    for i, ch in enumerate(chars):
        a = round(usable * i / len(chars))
        b = round(usable * (i + 1) / len(chars))
        words.append({"part": ch, "start": a, "end": b})
    return words, "file"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    ap.add_argument("--engine", choices=["edge", "file"], default="edge")
    ap.add_argument("--voice", default="zh-CN-YunxiNeural")
    ap.add_argument("--rate", default="+0%")
    ap.add_argument("--allow-stale", action="store_true",
                    help="有意自己维护 narration.txt（不跟 story 走）时，跳过旁白内容核对")
    ap.add_argument("--force-estimate", action="store_true",
                    help="允许 --engine=file 用「按字数均分」的估计时间覆盖已有的真实词级时间")
    a = ap.parse_args()
    project = a.project.resolve()
    if not project.is_dir():
        print(f"没有这个工程目录：{project}", file=sys.stderr)
        return 2
    # 内容契约（P1-07）：compose 写出旁白的内容指纹，这里核对。
    # 旧实现只比 mtime——旧文本重新保存一次就比 narration.txt 新，检查直接被绕过；
    # 而 mtime 也挡不住"内容没变但被 checkout 刷新"的假警报。
    story = project / "story.json"
    narr = project / "narration.txt"
    lines = read_lines(project)
    if not lines:
        return fail("没有 narration.txt（每行一句旁白）。先跑 compose-story 生成，或自己写一份。")
    text = "\n".join(lines) + "\n"
    contract = narration_contract.read(project)
    if contract:
        want, got = contract["text_sha256"], narration_contract.sha(text)
        if want != got:
            snapshot = contract.get("text") or []
            detail = (narration_contract.describe(narration_contract.first_diff("\n".join(snapshot), text))
                      if snapshot else "（这份契约没有文本快照，只能比指纹）")
            if not a.allow_stale:
                return fail(
                    "narration.txt 与 compose 记录的内容不一致：旁白改过，但没有重新 compose。\n"
                    f"  {detail}\n"
                    "继续的话 TTS 念的是**新文本**，而镜头与字幕的断句还是 compose 的旧版 —— 出片后对不上口型。\n"
                    "下一步：\n"
                    f"  1) python scripts/compose-story.py \"{story}\" \"{project}\"\n"
                    "  2) 再跑 tts\n"
                    "如果你是有意自己写 narration.txt（不跟 story 走），加 --allow-stale。"
                )
            print("⚠ --allow-stale：跳过旁白内容核对，按当前 narration.txt 合成。")
            print(f"  {detail}")
    elif not a.allow_stale and story.is_file() and story.stat().st_mtime > narr.stat().st_mtime:
        return fail(
            "story.json 比 narration.txt 新：你大概改了 story 但还没重跑 compose-story。\n"
            "继续的话 TTS 会读**上一版**旁白，出半截音频且不报错。\n"
            "（这份工程没有 manifests/narration.contract.json，只能按时间判断。）\n"
            "下一步：\n"
            f"  1) python scripts/compose-story.py \"{story}\" \"{project}\"\n"
            "  2) 再跑 tts\n"
            "如果你是有意自己写 narration.txt（不跟 story 走），加 --allow-stale。"
        )
    out_mp3 = project / "audio" / "narration.mp3"
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    try:
        if a.engine == "edge":
            source = "\n".join(lines)
            words, engine = synth_edge(source, a.voice, a.rate, out_mp3)
            words = merge_punctuation(words, source)
            estimated = False
        else:
            words, engine = synth_file(project, lines)
            estimated = True
    except RuntimeError as e:
        return fail(f"✗ TTS 没有完成：{e}")
    words_p = project / "audio" / "narration.mp3.json"
    meta_p = project / "audio" / "narration.meta.json"
    prev_meta = {}
    if meta_p.is_file():
        try:
            prev_meta = json.loads(meta_p.read_text(encoding="utf-8"))
        except ValueError:
            prev_meta = {}
    # --engine=file 只有"按字数均分"的估计时间。用它覆盖一份真实测得的词级时间，
    # 等于把精确时间轴换成假的——而且画面只是"大致对得上"，很难当场发现。
    if estimated and prev_meta.get("timeline") == "measured" and words_p.is_file() and not a.force_estimate:
        return fail(
            "audio/narration.mp3.json 里有上一次 TTS **实测**的词级时间，"
            "--engine=file 只能用「按字数均分」的估计值覆盖它。\n"
            "继续会丢掉精确时间轴（画面仍在动，但对不上发音位置）。\n"
            "三条路：\n"
            "  1) 保留现有时间轴：只换音频，不要重跑 tts\n"
            "  2) 真的要重估：加 --force-estimate（会先把旧文件备份）\n"
            "  3) 换成 --engine=edge 重新合成，时间才重新测得出来"
        )
    payload = json.dumps(words, ensure_ascii=False, indent=2) + "\n"
    backup = None
    if words_p.is_file():
        prev = words_p.read_text(encoding="utf-8", errors="replace")
        if prev != payload:
            backup = words_p.with_name(f"{words_p.name}.bak-{datetime.now().strftime('%Y%m%dT%H%M%S')}")
            shutil.copy2(words_p, backup)
    words_p.write_text(payload, encoding="utf-8")
    meta = {"engine": engine, "voice": a.voice if engine == "edge" else None,
            "rate": a.rate if engine == "edge" else None, "estimated": estimated,
            "timeline": "estimated" if estimated else "measured",
            "text_sha256": narration_contract.sha(text),
            "contract": contract is not None,
            "allow_stale": bool(a.allow_stale),
            "backup": str(backup) if backup else None,
            "synthesized_at": datetime.now().isoformat(timespec="seconds"),
            "words": len(words), "lines": len(lines)}
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 3.5.1：手写场景路线（没有 manifests/fusion.json = 不是 compose 生成的工程）没人会重建字幕，
    # 不重建 validate-caption-sync 必挂（spec §5 E8）。auto 路线由 compose 按词级时间重排，这里不动。
    if not (project / "manifests" / "fusion.json").is_file():
        lines_txt = project / "manifests" / "semantic-caption-lines.txt"
        cues_out = project / "manifests" / "caption-cues.json"
        if lines_txt.is_file():
            cmd = [sys.executable, str(Path(__file__).with_name("build-semantic-captions.py")),
                   str(project / "audio" / "narration.mp3.json"), str(lines_txt), str(cues_out)]
            phrases = project / "manifests" / "protected-caption-phrases.txt"
            if phrases.is_file():
                cmd += ["--protected-phrases", str(phrases)]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                return fail("✗ 字幕没能按新旁白重建：\n" + (r.stderr or r.stdout)[-800:]
                            + "\n  手动重跑：python scripts/build-semantic-captions.py audio/narration.mp3.json manifests/semantic-caption-lines.txt manifests/caption-cues.json")
            (project / "src").mkdir(exist_ok=True)
            shutil.copyfile(cues_out, project / "src" / "caption-cues.json")
            print(f"tts：手写工程 → 已按词级时间重建字幕 {cues_out.relative_to(project)}（并同步到 src/）")
        else:
            print("tts：⚠ 没有 manifests/semantic-caption-lines.txt，字幕没有重建；validate-caption-sync 会失败", file=sys.stderr)
    marker = project / "audio" / ".silent-placeholder"
    if marker.exists():
        marker.unlink()
    print(f"tts：{len(lines)} 句 / {len(words)} 个字音 · 引擎 {engine}"
          f"{'（时间按字数估计）' if estimated else ''} → {out_mp3}")
    if estimated:
        print("⚠ --engine=file 的词级时间是**按字数均分**估出来的，不是从音频里测的：")
        print("   字幕与镜头只会「大致对齐」。要精确时间轴：--engine=edge，或自己提供")
        print("   audio/narration.mp3.json（别家 TTS 的词级时间），再用 --engine=file 只换音频。")
    if backup:
        print(f"时间轴已改写；旧文件备份在 {backup.name}")
    print("下一步：node scripts/make-video.mjs <工程> --render <out.mp4>（compose 会按词级时间重排字幕与镜头）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
