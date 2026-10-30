#!/usr/bin/env python3
"""validate-ocr.py — 字幕「真的读得出」：对成片（或静帧）抽字幕帧做 OCR，核对文本与可读性。

为什么要它：几何门禁（CaptionFitGate 量像素宽、validate-presentation 算对比度）证明字幕"放得下、颜色够"，
但证明不了"读得出"——衬底被画面吃掉、字被推近切掉、字体没加载变成豆腐块、字太小，这些只有看图才知道。
本脚本用 RapidOCR（Apache-2.0，https://github.com/RapidAI/RapidOCR）读每条字幕的定格帧，和 caption-cues.json 的原文比。

用法
  python scripts/validate-ocr.py PROJECT --video renders/final.mp4      # 成片：每条 cue 抽一帧（完整显示后）
  python scripts/validate-ocr.py PROJECT --stills renders/stills         # 静帧：fNNNNN.png 里落在 cue 内的那些
        [--json out.json] [--band 0.26] [--min-px 80] [--require]

判据（每条 cue）
  ✗ P0  OCR 文本与 cue 原文相似度 < 0.60（字幕缺失 / 被遮 / 被切 / 豆腐块）
  · P1  相似度 < 0.90，或识别置信度均值 < 0.85（读得出但吃力：衬底弱、纹理干扰）
  · P1  字高（检测框高度，按 1440 高折算）< --min-px（缺省 80 ≈ 96 px 字号的字身）
只看画面底部 --band（缺省 26%）的字幕带；文本比较前做 NFKC、去空白与标点。

依赖：ffmpeg（抽帧、裁切）；RapidOCR 可选——
  pip install rapidocr onnxruntime        （或旧版 rapidocr_onnxruntime）
没装时打印 SKIPPED 并以 0 退出（不阻断出片）；加 --require 则以 3 退出。
也可以把装了 RapidOCR 的解释器写进环境变量 NOTEBOOK_VIDEO_OCR_PYTHON，脚本会用它重新执行自己。
退出码：0 通过 / 跳过；1 有 P0；2 用法错误；3 --require 且没装 RapidOCR。
"""
from __future__ import annotations

import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

FPS = 30
SIM_P0 = 0.60
SIM_P1 = 0.90
SCORE_P1 = 0.85
DEFAULT_BAND = 0.26
# 与 src/index.tsx Subtitle 的 lead = round(FPS*.18) 同口径：下一条字幕提前这么多秒出现
NEXT_CUE_LEAD = 0.18
SAMPLE_GUARD = 0.07   # 再留约 2 帧，避开 5 帧淡入
DEFAULT_MIN_PX = 80.0   # @1440：96 px 字号的汉字字身检测框约 85–100 px

_PUNCT = re.compile(r"[\s\u3000-\u303f\uff00-\uff0f\uff1a-\uff20\uff3b-\uff40\uff5b-\uff65\u2010-\u206f!-/:-@\[-`{-~·•…—–]+")


# ---------------------------------------------------------------- 纯函数（tests/test_ocr.py 覆盖）
def normalize(text: str) -> str:
    """NFKC → 去空白与中英文标点 → 小写。"""
    return _PUNCT.sub("", unicodedata.normalize("NFKC", text or "")).lower()


def similarity(expected: str, got: str) -> float:
    a, b = normalize(expected), normalize(got)
    if not a:
        return 1.0
    if not b:
        return 0.0
    # 字幕带里可能还读到画内的其他字：取"原文在 OCR 串里的最佳对齐"，而不是整串比
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    matched = sum(block.size for block in sm.get_matching_blocks())
    return matched / len(a) if len(b) >= len(a) else 2 * matched / (len(a) + len(b))


def cue_sample_times(cues: list[dict]) -> list[float]:
    """每条 cue 的取样时刻（秒）：完整显示之后 0.25 s，且不越过下一条的**出现**时刻。

    字幕组件（src/index.tsx Subtitle）让下一条提前 NEXT_CUE_LEAD（0.18 s）出现，所以取样上限是
    下一条开始 − NEXT_CUE_LEAD − SAMPLE_GUARD。3.3.0 用的是「下一条开始 − 0.12 s」，落在提前量里，
    读到的是下一句，误报 P0。"""
    out = []
    for i, c in enumerate(cues):
        start = float(c.get("start", c.get("start_ms", 0) / 1000))
        shown = float(c.get("reveal_end", c.get("reveal_end_ms", c.get("speech_end_ms", start * 1000)) / 1000))
        t = max(start, shown) + 0.25
        if i + 1 < len(cues):
            nxt = float(cues[i + 1].get("start", cues[i + 1].get("start_ms", 0) / 1000))
            t = min(t, max(start, nxt - NEXT_CUE_LEAD - SAMPLE_GUARD))
        out.append(round(t, 3))
    return out


def cue_at(cues: list[dict], t: float) -> int | None:
    """时刻 t（秒）显示的是哪条 cue（完整显示之后才算），没有返回 None。"""
    for i, c in enumerate(cues):
        start = float(c.get("start", c.get("start_ms", 0) / 1000))
        shown = float(c.get("reveal_end", c.get("reveal_end_ms", start * 1000) / 1000))
        end = float(cues[i + 1].get("start", cues[i + 1].get("start_ms", 0) / 1000)) - NEXT_CUE_LEAD if i + 1 < len(cues) else shown + 1.5
        if shown <= t < end:
            return i
    return None


def should_reexec(alt: str | None, current: str, env) -> bool:
    """Re-run under NOTEBOOK_VIDEO_OCR_PYTHON when it names another interpreter path.

    Paths are compared *without* resolving symlinks: a venv's bin/python is a symlink to the system
    python, so resolving made the venv look like "the same interpreter" and OCR was silently skipped.
    _NV_OCR_REEXEC guards against a loop when the target also lacks RapidOCR."""
    if not alt or env.get("_NV_OCR_REEXEC"):
        return False
    return os.path.abspath(os.path.expanduser(alt)) != os.path.abspath(current)


def _line(text: str, score, box) -> dict:
    """一条识别结果：文字、置信度、框高，以及框中心 (x, y)，用来排阅读顺序。"""
    xs, ys = [float(p[0]) for p in box], [float(p[1]) for p in box]
    return {"text": text, "score": float(score), "h": max(ys) - min(ys), "x": sum(xs) / len(xs), "y": sum(ys) / len(ys)}


def reading_order(lines: list[dict]) -> list[dict]:
    """按阅读顺序排：先分行（框中心高差 < 半个中位框高算同一行），行内从左到右。

    RapidOCR 的输出顺序不保证是阅读顺序：字形不同的两段（如宋体「拉丁语」+ 西文「cella：小房间」）
    同一行里会被倒着吐出来，拼起来与原文相似度掉到 0.7（cell-v3 cue9 误报）。没有坐标的旧结果保持原序。"""
    if not lines or any("x" not in x or "y" not in x for x in lines):
        return list(lines)
    hs = sorted(x["h"] for x in lines)
    tol = max(1.0, hs[len(hs) // 2] / 2)
    rows: list[list[dict]] = []
    for ln in sorted(lines, key=lambda x: x["y"]):
        if rows and abs(ln["y"] - sum(r["y"] for r in rows[-1]) / len(rows[-1])) < tol:
            rows[-1].append(ln)
        else:
            rows.append([ln])
    return [ln for row in rows for ln in sorted(row, key=lambda x: x["x"])]


def judge(expected: str, lines: list[dict], img_h: int, band: float, min_px: float) -> dict:
    """lines: [{text, score, h[, x, y]}]（h = 检测框高，像素；x/y = 框中心）。返回 {sim, score, px, level, issue}。"""
    lines = reading_order(lines)
    got = "".join(x["text"] for x in lines)
    sim = similarity(expected, got)
    best = [x for x in lines if similarity(x["text"], expected) > 0.3 or similarity(expected, x["text"]) > 0.3] or lines
    score = sum(x["score"] for x in best) / len(best) if best else 0.0
    px = (max(x["h"] for x in best) * 1440.0 / img_h) if best else 0.0
    level, issue = "ok", ""
    if sim < SIM_P0:
        level, issue = "P0", f"读不出：相似度 {sim:.2f} < {SIM_P0}（字幕被遮 / 被切 / 衬底被吃掉 / 字体没加载）"
    elif sim < SIM_P1:
        level, issue = "P1", f"读得吃力：相似度 {sim:.2f} < {SIM_P1}"
    elif score < SCORE_P1:
        level, issue = "P1", f"识别置信度 {score:.2f} < {SCORE_P1}（衬底弱或纹理干扰）"
    elif px and px < min_px:
        level, issue = "P1", f"字高约 {px:.0f} px@1440 < {min_px:.0f}（字号偏小）"
    return {"sim": round(sim, 3), "score": round(score, 3), "px": round(px, 1), "got": got, "level": level, "issue": issue}


# ---------------------------------------------------------------- OCR 与抽帧
def _quiet() -> None:
    import logging
    for name in ("RapidOCR", "rapidocr", "rapidocr_onnxruntime"):
        logging.getLogger(name).setLevel(logging.WARNING)


_PROBE_CODE = "\n".join([
    "import importlib, sys",
    "for m in ('rapidocr', 'rapidocr_onnxruntime'):",
    "    try:",
    "        importlib.import_module(m)",
    "        sys.exit(0)",
    "    except BaseException:",
    "        pass",
    "sys.exit(3)",
])


def _probe(argv: list[str]) -> tuple[bool, str]:
    """在子进程里试加载引擎，返回 (可用, 原因)。

    为什么不用 try/except：onnxruntime 与解释器/CPU 不兼容时，**import 那一刻就段错误**（rc=139 或
    SIGSEGV），异常拦不住，整个脚本直接被打死——用户看到的是「崩溃」而不是「跳过」。所以在子进程里试。
    """
    try:
        r = subprocess.run(argv, capture_output=True, timeout=180)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"探测子进程无法启动：{exc}"
    if r.returncode == 0:
        return True, ""
    if r.returncode == 3:
        return False, "没装 RapidOCR（pip install rapidocr onnxruntime，或设 NOTEBOOK_VIDEO_OCR_PYTHON）"
    return False, (f"RapidOCR 引擎无法加载：import 时进程异常退出（rc={r.returncode}），"
                   "常见于 onnxruntime 与本机 Python/CPU 不兼容；换一台机器或换解释器即可")


def engine_importable() -> tuple[bool, str]:
    return _probe([sys.executable, "-c", _PROBE_CODE])


def load_engine():
    ok, why = engine_importable()
    if not ok:
        load_engine.reason = why          # 给 main 打 SKIPPED 用
        return None
    try:
        from rapidocr import RapidOCR  # v2/v3
        _quiet()
        eng = RapidOCR()

        def run(path: str) -> list[dict]:
            r = eng(path)
            if r is None or getattr(r, "txts", None) is None:
                return []
            return [_line(t, s, b) for t, s, b in zip(r.txts, r.scores, r.boxes)]
        return run
    except ImportError:
        pass
    try:
        from rapidocr_onnxruntime import RapidOCR  # v1
        _quiet()
        eng = RapidOCR()

        def run(path: str) -> list[dict]:
            res, _ = eng(path)
            return [_line(t, s, b) for b, t, s in (res or [])]
        return run
    except ImportError:
        return None


def probe_height(path: Path) -> int:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True)
    try:
        return int(out.stdout.strip().splitlines()[0])
    except (ValueError, IndexError):
        return 0


def crop_band(src: Path, dst: Path, band: float, t: float | None = None) -> bool:
    vf = f"crop=iw:ih*{band}:0:ih*(1-{band})"
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if t is not None:
        cmd += ["-ss", f"{t:.3f}"]
    cmd += ["-i", str(src), "-frames:v", "1", "-vf", vf, str(dst)]
    return subprocess.run(cmd, capture_output=True).returncode == 0 and dst.is_file()


# ---------------------------------------------------------------- main
def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    proj = Path(argv[0]).resolve()
    opts = {"--video": None, "--stills": None, "--json": None, "--band": str(DEFAULT_BAND), "--min-px": str(DEFAULT_MIN_PX)}
    require = "--require" in argv
    i = 1
    while i < len(argv):
        if argv[i] in opts and i + 1 < len(argv):
            opts[argv[i]] = argv[i + 1]
            i += 2
        elif argv[i] == "--require":
            i += 1
        else:
            print(f"✗ 不认识的参数 {argv[i]}")
            return 2
    if not (opts["--video"] or opts["--stills"]):
        print("✗ 需要 --video FILE 或 --stills DIR")
        return 2
    cues_path = proj / "manifests" / "caption-cues.json"
    if not cues_path.is_file():
        print(f"✗ 找不到 {cues_path}")
        return 2
    cues = json.loads(cues_path.read_text(encoding="utf-8"))["cues"]

    run = load_engine()
    if run is None:
        alt = os.environ.get("NOTEBOOK_VIDEO_OCR_PYTHON")
        if should_reexec(alt, sys.executable, os.environ):
            env = dict(os.environ, _NV_OCR_REEXEC="1")
            return subprocess.run([alt, __file__, *argv], env=env).returncode
        print(f"validate-ocr · SKIPPED：{getattr(load_engine, 'reason', '没装 RapidOCR')}"
              "｜字幕像素级检查未执行（不阻断出片；发版前建议在能跑 RapidOCR 的机器上补一次）")
        return 3 if require else 0

    band, min_px = float(opts["--band"]), float(opts["--min-px"])
    jobs: list[tuple[int, Path, float | None]] = []   # (cue index, source, time)
    if opts["--video"]:
        video = Path(opts["--video"]).resolve()
        if not video.is_file():
            print(f"✗ 找不到成片 {video}")
            return 2
        for k, t in enumerate(cue_sample_times(cues)):
            jobs.append((k, video, t))
        src_h = probe_height(video)
    else:
        sdir = Path(opts["--stills"]).resolve()
        for png in sorted(sdir.glob("f*.png")):
            m = re.match(r"f(\d+)", png.stem)
            k = cue_at(cues, int(m.group(1)) / FPS) if m else None
            if k is not None:
                jobs.append((k, png, None))
        src_h = probe_height(jobs[0][1]) if jobs else 0
    if not jobs:
        print("validate-ocr · 没有落在字幕内的帧可查")
        return 0

    rows = []
    with tempfile.TemporaryDirectory(prefix="nv-ocr-") as td:
        for n, (k, src, t) in enumerate(jobs):
            crop = Path(td) / f"c{n:04d}.png"
            if not crop_band(src, crop, band, t):
                rows.append({"cue": k, "text": cues[k]["text"], "level": "P0", "issue": "抽帧失败", "sim": 0, "score": 0, "px": 0, "got": ""})
                continue
            res = judge(cues[k]["text"], run(str(crop)), src_h or 1440, band, min_px)
            res.update({"cue": k, "text": cues[k]["text"], "at": t if t is not None else src.name})
            rows.append(res)

    p0 = [r for r in rows if r["level"] == "P0"]
    p1 = [r for r in rows if r["level"] == "P1"]
    sims = [r["sim"] for r in rows]
    print(f"validate-ocr · {len(rows)} 帧（{'成片' if opts['--video'] else '静帧'}，源高 {src_h}px）· 平均相似度 {sum(sims) / len(sims):.2f}")
    for r in rows:
        if r["level"] != "ok":
            mark = "✗" if r["level"] == "P0" else "·"
            print(f"  {mark} {r['level']} cue{r['cue'] + 1}「{r['text']}」@{r['at']} — {r['issue']}；OCR「{r['got'][:40]}」")
    print(f"结论：P0={len(p0)} P1={len(p1)} → {'FAIL' if p0 else 'PASS'}")
    if opts["--json"]:
        Path(opts["--json"]).write_text(json.dumps({"rows": rows, "p0": len(p0), "p1": len(p1)}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if p0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
