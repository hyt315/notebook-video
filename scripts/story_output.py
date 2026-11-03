#!/usr/bin/env python3
"""story_output.py — compose-story 的「写盘产物」（P2-24 第五切片，最后一片）

从 `compose-story.py` 切出的第六块：把内存里的 comp / story_ts 变成工程文件。
这一块的变化原因是**产物格式**——story.ts 的字段、scenes.tsx 的导出形状、customs 的
注册检查、旁白契约的位置。改这些时只该动这个文件，不该让时间轴与版式跟着重跑。

边界：
  - **在这里**：`js()`（TS 里的 JSON 字面量）、`registered_customs` / `check_customs`
    （未注册的定制组件在写盘前拦）、`write_narration_contract`（旁白内容指纹）、
    `write_project`（manifests + src）、`write_media`（public/media + prepare-media）。
  - **不在这里**：story.json 怎么解析（`compose`）、镜头时间怎么算（`build`）、
    元素怎么摆（`story_layout`）、字怎么折（`story_text`）。
  - **唯一共享的可变量是朗读速度**：`break_rule` 里要写当前 cps，必须读
    `story_caption.CPS` 的**当前值**（`--cps` 会改它），不能 import 快照。

为什么 `p=None` 还能跑：门禁对象是 duck type（只要 `err` / `hint`），
负向夹具与「只算帧数」的干跑不传它，这里不做额外校验。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import narration_contract  # noqa: E402  （必须在 sys.path 之后导入）
import story_caption as _cap  # noqa: E402  （CPS 是运行期可变量，必须读当前值）
from story_caption import MAX_CHARS  # noqa: E402


def js(v) -> str:
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"))


CUSTOM_KEY_RE = re.compile(r"(?m)^\s*([A-Za-z_$][\w$]*)\s*(?::|,|$)")


def registered_customs(proj: Path) -> set[str]:
    """读 `src/custom/index.ts` 的 CUSTOM 表，返回已注册的组件名。

    为什么不用正则扫全文：注册表里还有 import、注释、以及 `RequestLane,` 这种简写；
    只取 `export const CUSTOM = { … }` 这一层花括号里的键，才是真正能渲染的名字。
    """
    f = proj / "src" / "custom" / "index.ts"
    if not f.is_file():
        return set()
    text = f.read_text(encoding="utf-8")
    m = re.search(r"export const CUSTOM\b[^=]*=\s*\{", text)
    if not m:
        return set()
    i, depth, start = m.end(), 1, m.end()
    while i < len(text) and depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return set(CUSTOM_KEY_RE.findall(text[start:i - 1]))


def check_customs(p: Problems, proj: Path, story_ts: dict) -> None:
    """P0：story.json 引用了未注册的定制组件 → 构建期停止。

    旧行为是渲染期用一行红字顶替（成片 74 秒处真的出过这行红字），既没有门禁也不出片失败。
    现在在写盘前拦：说清组件名、哪几镜、注册文件、照抄哪个范例。
    """
    need = sorted({v.get("custom") for v in story_ts.values() if v.get("custom")})
    if not need:
        return
    # 只有"完整工程"里才有注册表可核对。compose 也常被用来往空目录做一次干跑
    # （负向夹具 / 只算帧数），那里没有 src/index.tsx —— 此时不冒充"查过了"，给一条提示，
    # 运行期还有 cancelRender 兜底。
    if not (proj / "src" / "index.tsx").is_file():
        p.hint(
            f"这个目录还不是完整工程（没有 src/index.tsx），无法核对定制组件 {', '.join(need)} 是否注册；"
            f"写进真实工程后 compose 会再查一次。"
        )
        return
    have = registered_customs(proj)
    reg = proj / "src" / "custom" / "index.ts"
    for name in need:
        if name in have:
            continue
        shots = [sid for sid, v in story_ts.items() if v.get("custom") == name]
        p.err(
            f"{'、'.join(shots)}：定制组件 {name} 未注册 —— 在 {reg} 的 CUSTOM 表里加一行 `{name},`。"
            f"组件本体照抄 src/custom/RequestLane.tsx：新建 src/custom/{name}.tsx，"
            f"导出 `const {name}: React.FC<CustomProps>`；story.json 里写 \"component\":\"{name}\"。"
            f"（未注册的定制组件以前会渲染成一行红字继续出片，现在直接停止。）"
        )


def write_narration_contract(proj: Path, text: str, lines: int, p) -> None:
    """记录这份旁白是什么（TTS 合成时据此判断"音频到底念的是哪一版"）。

    同时检查上一次 TTS 的音频是否已经过期：音频没重跑就出片，是最难发现的一类错——
    字幕单看都对，只有听的时候才发现口型对不上。
    """
    doc = narration_contract.write(proj, text, source="compose-story", lines=lines)
    meta_p = proj / "audio" / "narration.meta.json"
    if p is None or not meta_p.is_file():
        return
    try:
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
    except ValueError:
        return
    old = meta.get("text_sha256")
    if old and old != doc["text_sha256"]:
        p.hint(
            "audio/narration.mp3 是**上一版**旁白合成的（内容指纹不一致）："
            "字幕会按新文本排，声音还是旧的。出片前重跑 tts。"
        )


def write_project(story, comp, out_shots, story_ts, total, proj: Path, p=None):
    (proj / "manifests").mkdir(parents=True, exist_ok=True)
    (proj / "audio").mkdir(exist_ok=True)
    (proj / "src").mkdir(exist_ok=True)
    cues = comp["cues"]
    cdoc = {"source": "audio/narration.mp3.json", "lead_ms": 60, "segmentation": "semantic",
            "break_rule": f"compose-story (silent, {_cap.CPS} chars/s, ≤{MAX_CHARS} chars per line)", "cues": cues}
    txt = json.dumps(cdoc, ensure_ascii=False, indent=1) + "\n"
    (proj / "manifests" / "caption-cues.json").write_text(txt, encoding="utf-8")
    (proj / "src" / "caption-cues.json").write_text(txt, encoding="utf-8")
    # 有 TTS 的 meta 时，audio/narration.mp3.json 是**真实词级时间**，compose 不许覆盖它
    # （覆盖后字幕会退回"按 4.5 字/秒估算"，与音频脱同步，而且看不出来）。
    if not (proj / "audio" / "narration.meta.json").is_file():
        words = [w for c in cues for w in c["words"]]
        (proj / "audio" / "narration.mp3.json").write_text(json.dumps(words, ensure_ascii=False) + "\n", encoding="utf-8")
    narration_text = "\n".join(c["text"] for c in cues) + "\n"
    (proj / "narration.txt").write_text(narration_text, encoding="utf-8")
    write_narration_contract(proj, narration_text, len(cues), p)
    (proj / "manifests" / "protected-caption-phrases.txt").write_text("# compose-story：术语表与 protect 列表，字幕不许切开\n" + "\n".join(comp["protected"]) + "\n", encoding="utf-8")
    (proj / "manifests" / "semantic-caption-lines.txt").write_text("\n".join(c["text"] for c in cues) + "\n", encoding="utf-8")
    # 3.5.0：融合门禁要读的东西（主题物 / 每镜配方 / 有没有线稿 / 关掉声音看到什么）。
    # 写进工程而不是让门禁回头找 story.json：工程可能被单独拷走 / 手改，story 不一定在旁边。
    rec_by = {r["id"]: r for r in out_shots}
    _ink_label = {}
    _see_of = {}
    _n = 0
    for _ch in (story.get("chapters") or []):
        for _sh in (_ch.get("shots") or []):
            _n += 1
            _sid = _sh.get("id") or f"S{_n}"   # story 里常常不写 id，compose 自己编号，这里要跟着编
            _in = ((_sh.get("content") or {}).get("ink") or {})
            if isinstance(_in, dict) and _in.get("label"):
                _ink_label[_sid] = str(_in["label"])
            # see 只存在于 story 的镜头上；story_ts 是压缩过的视图，没有它。
            if _sh.get("see"):
                _see_of[_sid] = str(_sh["see"])
    shots_f = {}
    for sid, st in story_ts.items():
        sk = st.get("sketch") or {}
        rec = rec_by.get(sid) or {}
        shots_f[sid] = {
            # see 只写在 story 的镜头上，out_shots 里没有（它到 presentation 阶段才带）。
            # 只读 rec 会让「全组件片靠 see 点名主题物」这条永远拿不到证据。
            "see": _see_of.get(sid) or rec.get("see") or "", "recipe": rec.get("recipe"),
            "layout": rec.get("layout", st.get("layout")),
            "sketch": bool(sk), "annotate": bool(st.get("annotate")),
            "sketch_label": " ".join(str(x) for x in [sk.get("label", ""), *((sk.get("parts") or {}).values())]),
            "sketch_draw": sk.get("draw", ""),
            # 3.6.0：手账页（承载）与它的真图版。validate-fusion 靠这三个字段判断
            # 「讲细胞却一张细胞图都没有」以及「全片都是手账页、概念没讲清」。
            "page": rec.get("page"), "media_id": rec.get("media_id"),
            "media_label": rec.get("media_label") or "",
            # 墨图（page + ink）：作者画在纸上的一张图，同样是「这个主题物出现过了」的证据。
            # 没有它，讲几何/数据的片子会被 fusion 门禁判成「全片没拍到主题物」，
            # 逼人去凑一张真图版——那是拿门禁逼出假内容。
            "ink_label": _ink_label.get(sid, ""),
            # 全组件模式（mode=component）没有手账页可放主题物，主题物只能靠
            # 「这一镜讲的是什么」来点名。给 title 让门禁有地方找证据。
            "title": str(((story_ts.get(sid) or {}).get("content") or {}).get("title") or ""),
        }
    # 呈现模式（3.7.0）：hybrid（默认）/ component（全组件）/ freeform（全非组件）。
    # 它不是风格开关，是**门禁契约**——三种模式的手账页与组件配额不同，
    # 写错模式会被 validate-fusion 按对应区间判，而不是一律按 20/75/25 判。
    _mode = str(story.get("mode") or "hybrid").lower()
    fusion = {"subject_of_film": story.get("subject_of_film", ""), "subject_why": story.get("subject_why", ""),
              "mode": _mode, "shots": shots_f}
    (proj / "manifests" / "fusion.json").write_text(json.dumps(fusion, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # camera:"still" → 关掉引擎的持续慢推/横移。
    # 默认的 drift 每镜都在推 4.5% 或横移 22px，看久了就是「画面一直在晃」；
    # 静止机位不等于不动——压章、写字、起笔都在动，只是画框不动。
    if str(story.get("camera") or "") == "still":
        for _s in out_shots:
            _s["cinema"] = {**(_s.get("cinema") or {}), "drift": "none", "still": True}
    sdoc = {"$comment": "AUTO-GENERATED by scripts/compose-story.py from story.json — 改内容请改 story.json 后重跑",
            "duration": total, "theme": story.get("theme", "flat"), "mode": _mode,
            "canvas": "16:9", "shots": out_shots}
    # 题材（可选）：story.json 顶层写 "topic": "science" 之类，resolve-shots 会优先挑
    # backgrounds.json 里 use.fits 含该题材的纸。不写就只按版式 + 角色轮换（3.3.0 行为）。
    if story.get("topic"):
        sdoc["topic"] = story["topic"]
    (proj / "manifests" / "shots.json").write_text(json.dumps(sdoc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    chapters = [c.get("title", "") for c in story["chapters"]]
    # 3.5.0 · captions.mode：line（默认，整行随 TTS 句子出现）/ typewriter（逐字，保留可选）。
    # 写进 film.ts，引擎侧（index.tsx）优先读它；老工程没有这个导出时按皮肤默认走。
    cap_mode = str((story.get("captions") or {}).get("mode", "line")).lower()
    reveal = "line" if cap_mode in ("line", "") else "type"
    film = ("// AUTO-GENERATED by scripts/compose-story.py — 禁止手改（改 story.json）。\n"
            f"export const COPY = {js({'chapterTitles': chapters, 'chromeKicker': story.get('kicker', 'NOTEBOOK-VIDEO'), 'header': story.get('header', story.get('title', '')), 'headerSub': story.get('headerSub', '')})} as const;\n"
            f"export const CHAPTER_SHOTS = {js(comp['chapter_first'])} as const;\n"
            f"export const CAPTION_REVEAL = '{reveal}' as const;\n"
            "")
    (proj / "src" / "film.ts").write_text(film, encoding="utf-8")
    st = ("// AUTO-GENERATED by scripts/compose-story.py — 禁止手改（改 story.json）。\n"
          "import type {StoryShot} from './auto';\n"
          f"export const STORY: Record<string, StoryShot> = {js(story_ts)};\n")
    (proj / "src" / "story.ts").write_text(st, encoding="utf-8")
    customs = sorted({v["custom"] for v in story_ts.values() if v.get("custom")})
    lines = ["// AUTO-GENERATED by scripts/compose-story.py — 每镜都由引擎的 AutoShot 渲染（版式 + 关键词同步 + 门禁）。",
             "// 手写定制画面放在 src/custom/，在 src/custom/index.ts 注册，story.json 里用 layout:\"custom\" 引用。",
             "import React from 'react';", "import {AutoShot} from './auto';", "import {SHOTS} from './shots';", ""]
    for s in out_shots:
        lines.append(f"const {s['id']}: React.FC<{{f: number}}> = ({{f}}) => <AutoShot id=\"{s['id']}\" f={{f}} />;")
    lines.append("")
    # 3.6.2：`Record<keyof typeof SHOTS, …>` 在镜数少于模板默认 8 镜时会把 tsc 打红
    # （模板 shots.ts 的键是 S1…S8，只有 4 镜的故事生成 S1…S4 → 缺 S5–S8）。
    # 用 Partial 兜住：SCENES 只承诺"模板里声明的这些键"，键集由 shots.ts 决定，不在这里重复写死。
    lines.append("export const SCENES: Partial<Record<keyof typeof SHOTS, React.FC<{f: number}>>> = {" + ", ".join(s["id"] for s in out_shots) + "};")
    lines.append(f"export const SCENES_VERSION = 'auto-scenes · {len(out_shots)} shots · custom: {', '.join(customs) or 'none'}';")
    (proj / "src" / "scenes.tsx").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_media(story, proj: Path) -> None:
    """story.json 顶层 media → public/media/ + manifests/media.json，再交给 prepare-media.py 探测 / 转码 / 同步 src/media.json。"""
    import shutil
    import subprocess
    mdir = proj / "public" / "media"
    mdir.mkdir(parents=True, exist_ok=True)
    items = []
    for m in story["media"]:
        src = Path(story["_dir"]) / m["file"]
        ext = src.suffix.lower()
        kind = "image" if ext in (".png", ".jpg", ".jpeg", ".webp") else "gif" if ext == ".gif" else "video"
        if src.is_file():
            shutil.copyfile(src, mdir / f"{m['id']}{ext}")
        e = {k: v for k, v in m.items() if k not in ("file", "width", "height")}
        e.update(file=f"{m['id']}{ext}", kind=m.get("kind", kind), source=m.get("source", "user"), muted=m.get("muted", True))
        items.append(e)
    (proj / "manifests" / "media.json").write_text(json.dumps({"items": items}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, str(Path(__file__).with_name("prepare-media.py")), str(proj)])
