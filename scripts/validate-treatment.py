#!/usr/bin/env python3
"""validate-treatment.py — 导演层门禁：manifests/treatment.json 是否真的想清楚了（3.3.0）。

用法：python scripts/validate-treatment.py PROJECT [--json]

规则见 references/director-method.md 末表。要点：
  · 手作皮肤（journal / papercut / archive）：缺 treatment.json 或必填没填 = P0（阻断）；
  · flat / cel：同样的问题只记 P1（向后兼容：老工程没有这一层）；
  · 风格 / 节奏类建议（转向你的时间点、运镜种类、评审分数）永远是 P1；
  · 3.6.0：treatment 的 move / framing 对照镜头表（shots.resolved.json）的 cameraIntent / keys 缩放（P1）；
    招牌镜头实推 < 12% 记入 hard（手作 P0）；候选结构 family 至少 2 族（P1）；sound 段（P1）。
只用标准库。退出码：0 通过，1 有 P0，2 用法错误。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CRAFT = {"journal", "papercut", "archive"}
SKINS = CRAFT | {"flat", "cel"}
# 3.6.0：叙事结构族（候选结构至少 2 族，见 references/director-method.md 第 5 步、blueprints/*.json 的 family）
FAMILIES = ("medium-metaphor", "kishotenketsu", "mystery", "scale-ladder", "experiment", "one-take-journey", "myth-flip", "lecture-arc")
# 3.6.0：treatment 的景别 / 运镜要在镜头表里兑现（references/camera-language.md §2）
MOVES = ("establish", "push-in", "pull-back", "pan-follow", "reveal", "micro-orbit", "still")
SIGNATURE_PUSH_MIN = 0.12   # 招牌镜头至少真推 12%（缩放变化，或 cinema.focus 的 zoom）
FRAMING_RULES = {           # 景别 → 实际取景（镜头表 keys 的缩放 / 主体占画高）
    "全": "最松处缩放 ≤ 1.05",
    "中": "最松处缩放 ≤ 1.20",
    "近": "峰值缩放 ≥ 1.20，或主体 ≥ 1/2 画高",
    "特写": "插入镜、峰值缩放 ≥ 1.35（纯图形 ≥ 1.5），或主体 ≥ 2/3 画高",
}
REVIEW_KEYS = ("构图主体", "调度节奏", "隐喻媒介一致", "顿悟惊艳", "字幕可读", "手作质感色彩纪律", "叙事完整")
REQUIRED = ("topic", "question", "metaphor.idea", "metaphor.why_unique", "medium.skin", "medium.why",
            "native_move.what", "native_move.why_only_this_medium", "chosen", "chosen_why", "logline",
            "arc.setup", "arc.turn", "arc.ending", "ending_echo.opening_image", "ending_echo.one_change",
            "benchmark.learn", "benchmark.not_learn", "signature_shot")


def get(d: dict, dotted: str):
    for k in dotted.split("."):
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def placeholder(v) -> bool:
    s = json.dumps(v, ensure_ascii=False)
    return "<<" in s or ">>" in s


def active_skin(proj: Path) -> str:
    a = proj / "src" / "theme" / "active.ts"
    m = re.search(r"from\s+'\./(\w+)'", a.read_text(encoding="utf-8")) if a.is_file() else None
    return m.group(1) if m else "flat"


def camera_of(shot: dict) -> dict:
    """镜头表（shots.resolved.json）里一镜的实际取景：起幅 / 峰值缩放、推拉幅度、主体占画高。"""
    keys = [k for k in (shot.get("keys") or []) if isinstance(k.get("s"), (int, float))]
    ss = [float(k["s"]) for k in keys] or [1.0]
    focus = [f for f in ((shot.get("cinema") or {}).get("focus") or []) if not f.get("settle")]
    fz = max([float(f.get("zoom") or 1.0) for f in focus] + [1.0])
    start, peak = ss[0], max(ss) * fz
    push = max(max(ss) / max(min(ss), 1e-6), fz) - 1.0
    hero = shot.get("hero") or {}
    size = hero.get("size") if isinstance(hero.get("size"), (int, float)) else None
    frac = size * peak / 1080.0 if size else 0.0
    graphic_only = not ({"text", "code", "console"} & set(shot.get("media") or []))
    return {"start": start, "low": min(ss), "peak": peak, "push": push, "frac": frac, "insert": bool(shot.get("insert")),
            "graphic_only": graphic_only, "has_keys": bool(keys), "intent": shot.get("cameraIntent")}


def framing_ok(framing: str, c: dict) -> bool:
    if framing == "全":
        return c["low"] <= 1.05 + 1e-6
    if framing == "中":
        return c["low"] <= 1.20 + 1e-6
    if framing == "近":
        return c["peak"] >= 1.20 - 1e-6 or c["frac"] >= 0.5
    if framing in ("特写", "插入"):
        return c["insert"] or c["peak"] >= (1.5 if c["graphic_only"] else 1.35) - 1e-6 or c["frac"] >= 2 / 3
    return True


def signature_id(t: dict, ids: list[str]) -> str | None:
    sig = str(t.get("signature_shot") or "")
    m = re.match(r"\s*([A-Za-z]+\d+[A-Za-z]?)", sig)
    if m and m.group(1) in ids:
        return m.group(1)
    for i in ids:  # 写成 “招牌镜头 S4：…” 也认
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(i)}(?![0-9])", sig):
            return i
    return m.group(1) if m else None


def check_camera(t: dict, resolved: list[dict]) -> tuple[list[str], list[str]]:
    """treatment.shots（意图）⇄ shots.resolved.json（实际）。返回 (hard, soft)：招牌镜头没真推 = hard，其余 soft。"""
    hard: list[str] = []
    soft: list[str] = []
    real = {s.get("id"): s for s in resolved}
    for ts in t.get("shots") or []:
        sid = ts.get("id")
        if placeholder(ts) or sid not in real:
            continue
        c = camera_of(real[sid])
        mv = ts.get("move")
        if mv in MOVES and c["intent"] and mv != c["intent"]:
            soft.append(f"{sid}：treatment 写 move={mv}，镜头表 cameraIntent={c['intent']} —— 写了就要兑现（改镜头表或改 treatment）")
        fr = ts.get("framing")
        if c["has_keys"] and fr in FRAMING_RULES and not framing_ok(fr, c):
            soft.append(f"{sid}：treatment 写「{fr}」（{FRAMING_RULES[fr]}），实际最松 {c['low']:.2f}、峰值 {c['peak']:.2f}、主体约 {c['frac']:.0%} 画高 —— 景别没兑现")
    ids = [s.get("id") for s in resolved]
    sig = signature_id(t, ids)
    if sig and sig in real:
        c = camera_of(real[sig])
        if c["has_keys"] and not c["insert"] and c["push"] < SIGNATURE_PUSH_MIN - 1e-9:
            hard.append(f"招牌镜头 {sig} 实际只推了 {c['push']:.0%}（要 ≥ {SIGNATURE_PUSH_MIN:.0%}：keys 的缩放变化或 cinema.focus 的 zoom）—— 招牌镜头写了慢推就要真推")
    elif sig and ids:
        soft.append(f"signature_shot 指向的 {sig} 不在镜头表里")
    return hard, soft


def check_sound(t: dict) -> list[str]:
    snd = t.get("sound")
    if not isinstance(snd, dict) or placeholder(snd):
        return ["treatment.sound 没写完：原生动作前静多久、全片最重要的一声、配乐用不用（为什么）、每种媒介配什么拟音（references/director-method.md 第 8 步）"]
    out = []
    sil = snd.get("silence_before_native_move_sec")
    if not isinstance(sil, (int, float)) or sil < 0.5:
        out.append("sound.silence_before_native_move_sec 要 ≥ 0.5：原生动作之前留一口安静，第一声才响")
    if not str(snd.get("most_important_sound") or "").strip():
        out.append("sound.most_important_sound 没写：全片最重要的那一声是什么、在第几秒")
    mu = snd.get("music")
    if not isinstance(mu, dict) or not isinstance(mu.get("use"), bool) or not str(mu.get("why") or "").strip():
        out.append("sound.music 要写 {use: true|false, why}：用不用配乐都要有理由")
    if not snd.get("foley_per_medium"):
        out.append("sound.foley_per_medium 为空：每个原生动作（画线 / 晕染 / 剪 / 盖章）配什么材料声")
    return out


def check(proj: Path) -> tuple[list[str], list[str], str]:
    skin = active_skin(proj)
    hard: list[str] = []   # 手作皮肤记 P0、其它记 P1
    soft: list[str] = []   # 永远 P1
    tf = proj / "manifests" / "treatment.json"
    if not tf.is_file():
        hard.append("没有 manifests/treatment.json —— 复制 manifests/treatment.example.json 填好（references/director-method.md）")
        return hard, soft, skin
    try:
        t = json.loads(tf.read_text(encoding="utf-8"))
    except ValueError as e:
        hard.append(f"treatment.json 不是合法 JSON：{e}")
        return hard, soft, skin
    for k in REQUIRED:
        v = get(t, k)
        if v in (None, "", [], {}):
            hard.append(f"{k} 没填")
        elif placeholder(v):
            hard.append(f"{k} 还留着 <<…>> 占位")
    cands = t.get("candidates") or []
    if len(cands) != 3:
        hard.append(f"候选结构要恰好 3 个（现在 {len(cands)} 个）—— 第一个想到的往往是陈词滥调，写满三个再选")
    elif t.get("chosen") not in {c.get("id") for c in cands}:
        hard.append(f"chosen={t.get('chosen')!r} 不是候选 id 之一")
    elif any(placeholder(c) or not c.get("shape") for c in cands):
        hard.append("候选结构还有没写完的（shape 为空或留着 <<…>>）")
    fams = [c.get("family") for c in cands]
    bad_f = [f for f in fams if f and f not in FAMILIES]
    if len(cands) == 3 and (bad_f or None in fams or "" in fams):
        soft_family = f"candidates[].family 要从 {', '.join(FAMILIES)} 里选（{'未知：' + ', '.join(map(str, bad_f)) if bad_f else '有候选没写'}）"
    elif len(cands) == 3 and len(set(fams)) < 2:
        soft_family = f"三个候选结构都是 {fams[0]} 一族 —— 至少换一族（悬案 / 尺度阶梯 / 起承转合 / 对照实验…），否则只是同一条曲线的三种写法"
    else:
        soft_family = None
    ms = get(t, "medium.skin")
    if ms and ms in SKINS and ms != skin:
        hard.append(f"medium.skin={ms} 与工程皮肤 {skin} 不一致（媒介即隐喻：选定了就用它）")
    elif ms and ms not in SKINS and not placeholder(ms):
        hard.append(f"medium.skin={ms} 不是已有皮肤（{', '.join(sorted(SKINS))}）")
    # 片长
    dur = None
    rs = proj / "manifests" / "shots.resolved.json"
    if rs.is_file():
        try:
            dur = json.loads(rs.read_text(encoding="utf-8")).get("duration")
        except ValueError:
            pass
    secs = dur / 30 if dur else None
    at = get(t, "native_move.at_sec")
    if not isinstance(at, (int, float)) or at <= 0:
        hard.append("native_move.at_sec 要写原生动作发生在第几秒（> 0）")
    elif secs and at > secs:
        hard.append(f"native_move.at_sec={at} 超出片长 {secs:.1f} 秒")
    facts = t.get("facts") or []
    if not facts:
        hard.append("facts 为空 —— 每个数字 / 日期 / 人名都要有出处（url + 原文引文）")
    for i, fct in enumerate(facts):
        if placeholder(fct) or not re.match(r"https?://", str(fct.get("url", ""))) or not str(fct.get("quote", "")).strip():
            hard.append(f"facts[{i}]（{str(fct.get('claim', ''))[:20]}）缺 http(s) 链接或原文引文")
    # Commons：每个选题先搜
    log = proj / "manifests" / "commons-log.json"
    searches = []
    if log.is_file():
        try:
            searches = json.loads(log.read_text(encoding="utf-8")).get("searches", [])
        except ValueError:
            pass
    if not searches:
        hard.append("还没搜过 Commons —— python scripts/commons-search.py search \"<关键词>\" --project <工程>（找不到也要搜过）")
    media = proj / "manifests" / "media.json"
    ids = set()
    if media.is_file():
        try:
            ids = {e.get("id") for e in json.loads(media.read_text(encoding="utf-8")).get("items", [])}
        except ValueError:
            pass
    for u in get(t, "commons.used") or []:
        if not placeholder(u) and u not in ids:
            hard.append(f"commons.used 里的 {u} 不在 manifests/media.json —— 先 commons-search.py add")
    # 软建议
    if soft_family:
        soft.append(soft_family)
    soft.extend(check_sound(t))
    if rs.is_file():
        try:
            ch, cs = check_camera(t, json.loads(rs.read_text(encoding="utf-8")).get("shots") or [])
            hard.extend(ch)
            soft.extend(cs)
        except ValueError:
            pass
    ty = t.get("turn_to_you_sec")
    if secs and isinstance(ty, (int, float)) and ty > 0 and not (0.35 * secs <= ty <= 0.55 * secs):
        soft.append(f"turn_to_you_sec={ty} 在片长 {ty / secs:.0%} 处；建议 40–45%（35–55% 都算合理）")
    elif not isinstance(ty, (int, float)) or ty <= 0:
        soft.append("turn_to_you_sec 没写：片子什么时候转向「你」？")
    shots = [s for s in (t.get("shots") or []) if not placeholder(s)]
    if not shots:
        soft.append("treatment.shots 为空：每镜写景别 / 运镜 / 理由")
    else:
        moves = {s.get("move") for s in shots if s.get("move")}
        if len(moves) < 4:
            soft.append(f"运镜只有 {len(moves)} 种（{', '.join(sorted(moves))}）；建议 ≥4 种并有一个招牌镜头")
        nowhy = [s.get("id") for s in shots if not str(s.get("why", "")).strip()]
        if nowhy:
            soft.append(f"这些镜没写理由：{', '.join(map(str, nowhy))}")
        if rs.is_file():
            try:
                real = [s["id"] for s in json.loads(rs.read_text(encoding="utf-8"))["shots"]]
                miss = [x for x in real if x not in {s.get("id") for s in shots}]
                if miss:
                    soft.append(f"镜头表里的 {', '.join(miss)} 在 treatment.shots 里没有理由")
            except (ValueError, KeyError):
                pass
    rounds = get(t, "review.rounds") or []
    if not rounds:
        soft.append("还没有独立评审（review.rounds 为空）：新会话只看联系表 + 镜头表，七项打分")
    else:
        last = rounds[-1].get("scores", {})
        low = [f"{k}={last.get(k)}" for k in REVIEW_KEYS if not isinstance(last.get(k), (int, float)) or last.get(k) < 8]
        if low:
            soft.append(f"最后一轮评审有项 <8 或缺：{', '.join(low)} —— 改完再评")
    return hard, soft, skin


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    proj = Path(argv[0]).resolve()
    hard, soft, skin = check(proj)
    craft = skin in CRAFT
    p0 = hard if craft else []
    p1 = ([] if craft else hard) + soft
    if "--json" in argv:
        print(json.dumps({"skin": skin, "p0": p0, "p1": p1}, ensure_ascii=False, indent=1))
    else:
        print(f"validate-treatment · 皮肤 {skin}{'（手作皮肤：导演层必填）' if craft else '（导演层建议填）'}")
        for x in p0:
            print(f"  ✗ P0 {x}")
        for x in p1:
            print(f"  · P1 {x}")
        print(f"结论：P0={len(p0)} P1={len(p1)} → {'FAIL' if p0 else 'PASS'}")
    return 1 if p0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
