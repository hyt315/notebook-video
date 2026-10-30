#!/usr/bin/env python3
"""validate-opening.py — 开场 3 秒门禁（3.3.0）：第 0 帧就要有东西在发生，片名不当第一镜，第一句不是泛问句。

用法：
    python scripts/validate-opening.py PROJECT [--video MP4] [--json]

依据：references/narrative-hook.md 的冷开合约（先给结果 / 最怪的画面，再给背景）与 pacing-rhythm.md 的开场节奏；
YouTube 把"30 秒后还剩多少观众"单列为 Intro 指标，并建议把精彩内容提前（https://support.google.com/youtube/answer/9314415）。

静态检查（读 manifests/shots.resolved.json + manifests/caption-cues.json）：
  O1 第一个可见事件 ≤ 6 帧（第一镜第一个 beat，或第一条字幕的出现）
  O2 第一条字幕 ≤ 1.0 s 出现
  O3 片名不是第一镜的主角（hero.kind = "title"，或 hero.name 就是片名 / 写着"片名""标题"）
  O4 前 90 帧（3 s）至少 3 个 beat（所有镜头的 beatsAbs + 镜头切换）
  O5 第一句不是泛问句 / 寒暄（"X 这个词…""你知道吗""今天我们来聊""大家好"）
像素检查（--video，要 ffmpeg；没有就 SKIPPED）：
  O6 第 0 / 15 / 45 / 90 帧：非背景像素占比 > 8%（第 0 帧就有主体）
  O7 相邻两张（0→15、15→45、45→90）画面有变化（平均差 > 1.5 / 255）
档位：手作皮肤（journal / papercut / archive）记 P0，flat / cel 记 P1（老工程向后兼容）。
只用标准库（像素检查调用 ffmpeg 输出 rawvideo）。退出码：0 通过，1 有 P0，2 用法错误。
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

CRAFT = {"journal", "papercut", "archive"}
FPS = 30
FIRST_EVENT_MAX_FRAMES = 6
FIRST_CAPTION_MAX_SEC = 1.0
OPENING_WINDOW_FRAMES = 90
OPENING_MIN_BEATS = 3
PROBE_FRAMES = (0, 15, 45, 90)
INK_MIN_RATIO = 0.08          # 非背景像素占比下限
CHANGE_MIN = 1.5              # 相邻抽帧平均差下限（0–255）
SAMPLE_W, SAMPLE_H = 160, 90  # 像素检查的降采样尺寸
BANNED_OPENERS = (
    (r"^[「“\"]?[^，,。！？]{1,8}[」”\"]?这个(词|字|名字)", "“X 这个词…”"),
    (r"你知道吗|你有没有想过|你是否", "“你知道吗 / 你有没有想过”"),
    (r"^(今天|这期|本期)(我们)?(来|要)?(聊|讲|说|看|了解)", "“今天我们来聊…”"),
    (r"^(大家好|哈喽|嗨|hello)", "寒暄"),
)


def active_skin(proj: Path) -> str:
    a = proj / "src" / "theme" / "active.ts"
    m = re.search(r"from\s+'\./(\w+)'", a.read_text(encoding="utf-8")) if a.is_file() else None
    return m.group(1) if m else "flat"


def story_title(proj: Path) -> str:
    p = proj / "src" / "story.ts"
    if not p.is_file():
        return ""
    m = re.search(r"title\s*:\s*['\"]([^'\"]+)['\"]", p.read_text(encoding="utf-8"))
    return m.group(1).strip() if m else ""


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def static_checks(shots: list[dict], cues: list[dict], title: str) -> list[str]:
    out: list[str] = []
    first_cue_f = None
    if cues:
        c0 = cues[0]
        ms = c0.get("start_ms")
        if ms is None and c0.get("words"):
            ms = c0["words"][0].get("start")
        if isinstance(ms, (int, float)):
            first_cue_f = ms / 1000 * FPS
    beats = sorted(b for s in shots for b in (s.get("beatsAbs") or []) if isinstance(b, (int, float)))
    first_events = [b for b in beats[:1]] + ([first_cue_f] if first_cue_f is not None else [])
    first = min(first_events) if first_events else None
    if first is None or first > FIRST_EVENT_MAX_FRAMES:
        out.append(f"O1 第一个可见事件在第 {first:.0f} 帧（要 ≤ {FIRST_EVENT_MAX_FRAMES}）：第 0 帧就要有动作在发生——把第一镜第一个 beat 提到 0，或让主体在第 0 帧已经在画"
                   if first is not None else "O1 第一镜没有 beats、也没有字幕：开场第 0 帧什么都没发生")
    if first_cue_f is None:
        out.append("O2 没有字幕时间轴（manifests/caption-cues.json）：无法确认第一句什么时候出来")
    elif first_cue_f / FPS > FIRST_CAPTION_MAX_SEC:
        out.append(f"O2 第一条字幕在 {first_cue_f / FPS:.2f}s 才出现（要 ≤ {FIRST_CAPTION_MAX_SEC:.1f}s）")
    if shots:
        hero = shots[0].get("hero") or {}
        name = str(hero.get("name") or "")
        if hero.get("kind") == "title" or (title and name.strip() == title) or re.search(r"片名|标题|title", name, re.I):
            out.append(f"O3 第一镜的主角是片名（{name or hero.get('kind')}）：冷开先给最怪的画面 / 数字，片名推到 10s 以后或不要")
    window = [b for b in beats if b < OPENING_WINDOW_FRAMES]
    cuts = [s.get("from") for s in shots[1:] if isinstance(s.get("from"), (int, float)) and s["from"] < OPENING_WINDOW_FRAMES]
    n = len(window) + len(cuts)
    if n < OPENING_MIN_BEATS:
        out.append(f"O4 前 3 秒只有 {n} 个节拍（beats {window}{'、切换 ' + str(cuts) if cuts else ''}；要 ≥ {OPENING_MIN_BEATS}）：开场要密，前 90 帧至少三次画面变化")
    if cues:
        text = str(cues[0].get("text") or "").strip()
        for pat, label in BANNED_OPENERS:
            if re.search(pat, text, re.I):
                out.append(f"O5 第一句「{text}」是{label}开场：直接给结果或最怪的那个事实（narrative-hook.md 的冷开合约）")
                break
    return out


def grab_frames(video: Path, frames=PROBE_FRAMES) -> list[bytes] | None:
    if not shutil.which("ffmpeg"):
        return None
    sel = "+".join(f"eq(n\\,{f})" for f in frames)
    head = ["ffmpeg", "-v", "error", "-i", str(video), "-vf",
            f"select='{sel}',scale={SAMPLE_W}:{SAMPLE_H}:flags=area"]
    tail = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    # ffmpeg 7.1 起删除了 -vsync（本机 N-125608 直接 "Unrecognized option 'vsync'"），
    # 以前抽帧命令必然失败 → 像素检查静默 SKIPPED，等于 O6/O7 从来没真跑过。
    # 新版本用 -fps_mode passthrough，老版本退回 -vsync 0。
    raw = None
    for flag in (["-fps_mode", "passthrough"], ["-vsync", "0"]):
        try:
            raw = subprocess.run(head + flag + tail, capture_output=True, check=True, timeout=120).stdout
            break
        except (subprocess.SubprocessError, OSError):
            raw = None
    if raw is None:
        return None
    size = SAMPLE_W * SAMPLE_H * 3
    return [raw[i:i + size] for i in range(0, len(raw) - size + 1, size)]


def ink_ratio(px: bytes) -> float:
    """非背景像素占比：背景 = 画面最常见的颜色（量化到 16 级），与它差得远的像素算"有东西"。"""
    counts: dict[tuple, int] = {}
    n = len(px) // 3
    for i in range(0, len(px), 3):
        k = (px[i] >> 4, px[i + 1] >> 4, px[i + 2] >> 4)
        counts[k] = counts.get(k, 0) + 1
    bg = max(counts, key=counts.get)
    br, bgc, bb = (bg[0] << 4) + 8, (bg[1] << 4) + 8, (bg[2] << 4) + 8
    ink = 0
    for i in range(0, len(px), 3):
        if abs(px[i] - br) + abs(px[i + 1] - bgc) + abs(px[i + 2] - bb) > 60:
            ink += 1
    return ink / max(n, 1)


def mean_diff(a: bytes, b: bytes) -> float:
    return sum(abs(x - y) for x, y in zip(a, b)) / max(len(a), 1)


def pixel_checks(video: Path) -> tuple[list[str], str]:
    frames = grab_frames(video)
    if frames is None:
        return [], "SKIPPED（没有 ffmpeg 或视频读不出）"
    if len(frames) < len(PROBE_FRAMES):
        return [f"O6 只抽到 {len(frames)} 帧（视频短于 {PROBE_FRAMES[-1] / FPS:.0f}s？）"], "FAIL"
    out = []
    for f, px in zip(PROBE_FRAMES, frames):
        r = ink_ratio(px)
        if r <= INK_MIN_RATIO:
            out.append(f"O6 第 {f} 帧非背景像素只占 {r:.1%}（要 > {INK_MIN_RATIO:.0%}）：{'第 0 帧是空纸' if f == 0 else '开场画面太空'}")
    for (fa, a), (fb, b) in zip(zip(PROBE_FRAMES, frames), list(zip(PROBE_FRAMES, frames))[1:]):
        d = mean_diff(a, b)
        if d <= CHANGE_MIN:
            out.append(f"O7 第 {fa}→{fb} 帧几乎没变化（平均差 {d:.2f}）：开场 3 秒里画面要一直在变")
    return out, "checked"


def check(proj: Path, video: Path | None = None) -> dict:
    skin = active_skin(proj)
    rs = load(proj / "manifests" / "shots.resolved.json") or {}
    cc = load(proj / "manifests" / "caption-cues.json") or {}
    issues = static_checks(rs.get("shots") or [], cc.get("cues") or [], story_title(proj))
    pixel = "not requested"
    if video is not None:
        more, pixel = pixel_checks(video)
        issues += more
    craft = skin in CRAFT
    return {"skin": skin, "p0": issues if craft else [], "p1": [] if craft else issues, "pixel": pixel}


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    proj = Path(argv[0]).resolve()
    video = Path(argv[argv.index("--video") + 1]).resolve() if "--video" in argv else None
    r = check(proj, video)
    if "--json" in argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(f"validate-opening · 皮肤 {r['skin']}{'（手作皮肤：开场不合格即停）' if r['skin'] in CRAFT else '（只提示）'} · 像素检查 {r['pixel']}")
        for x in r["p0"]:
            print(f"  ✗ P0 {x}")
        for x in r["p1"]:
            print(f"  · P1 {x}")
        print(f"结论：P0={len(r['p0'])} P1={len(r['p1'])} → {'FAIL' if r['p0'] else 'PASS'}")
    return 1 if r["p0"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
