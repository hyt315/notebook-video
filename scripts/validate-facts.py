#!/usr/bin/env python3
"""validate-facts · 内容事实质量的标注与审读（P2-22）。

**这条门禁保证什么、不保证什么**（先说清，免得当成事实核查器）：

    保证的：标注**本身**合法 —— 引用的来源存在、类比没被当事实、AI 生成的图不当来源。
    不保证的：story 里的事实、数字、历史说法**正确**。那需要人工审读。

所以它**不是无差别硬门禁**（清单 P2-22 明说「不宜做成无差别硬门禁」）：
    · 不强制每镜都有 claim —— 过渡句、观点、比喻不必逐条标注；
    · 缺标注只报 P1 提示，不拦出片；
    · P0 只拦**标注自己说不通**的三种情况（引用不存在的来源 / 类比带来源 / 来源不是文献）。

作者在 story.json 里写：

    "sources": [
      {"id": "wiki-hash", "kind": "fact", "title": "哈希表", "url": "https://…"},
      {"id": "phonebook", "kind": "analogy", "note": "查电话簿的比喻——不是哈希表的真实机制"}
    ]

镜上（或 content 上）挂 claim：

    "claim": {"kind": "fact", "source": "wiki-hash", "text": "哈希表用拉链法解决冲突"}
    "claim": {"kind": "analogy", "note": "像查电话簿"}

**AI 生成的 see / ink 描述不能当事实来源**：`content.ink.label`、`content.figure` 是本片自己
画的说明图，不是文献。`sources[].kind` 只有 `fact`（外部来源）与 `analogy`（比喻）两种，
写 `generated` / `internal` 会被拦——来源必须是**片外**的可查资料。

人工审读清单（`--review`）把「含数字 / 年份的未标注文本」列出来：这些是最容易错的
可核验断言，机器判不了对错，但可以保证它们**被看见**。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VALID_SOURCE_KINDS = ("fact", "analogy")
VALID_CLAIM_KINDS = ("fact", "analogy")

# 含数字 / 年份 / 单位的文本片段 —— 可核验断言的启发式。机器判不了对错，但能把它们列出来。
NUM_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|％|倍|万|亿|年|秒|毫秒|帧|字|次|个|条|种|层|bit|字节|KB|MB|GB)?")
YEAR_RE = re.compile(r"(?:19|20)\d{2}\s*年")


def load_story(project: Path) -> dict | None:
    f = project / "story.json"
    if not f.is_file():
        f = project / "manifests" / "story.json"
    if not f.is_file():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def shots_of(story: dict) -> list[tuple[str, dict]]:
    out = []
    for ci, ch in enumerate(story.get("chapters") or []):
        for si, sh in enumerate(ch.get("shots") or []):
            sid = sh.get("id") or f"C{ci + 1}S{si + 1}"
            out.append((sid, sh))
    return out


def claims_of(shot: dict) -> list[tuple[str, dict]]:
    """claim 可以写在 shot 上，也可以写在 content 上（一条镜可能有多条断言 → 传数组）。"""
    out = []
    for where, obj in (("shot", shot), ("content", shot.get("content") or {})):
        c = obj.get("claim")
        if isinstance(c, dict):
            out.append((where, c))
        elif isinstance(c, list):
            out.extend((where, x) for x in c if isinstance(x, dict))
    return out


def check_facts(story: dict) -> tuple[list[dict], list[dict]]:
    """P0 只拦标注自己说不通的；P1 提示缺标注。**不**要求每镜都有 claim。"""
    p0: list[dict] = []
    p1: list[dict] = []

    sources = story.get("sources") or []
    ids = set()
    for s in sources:
        if not isinstance(s, dict):
            continue
        sid = str(s.get("id") or "").strip()
        kind = str(s.get("kind") or "").strip()
        if not sid:
            p0.append({"id": "sources", "issue": f"来源条目缺 id：{json.dumps(s, ensure_ascii=False)[:60]}"})
            continue
        if sid in ids:
            p0.append({"id": "sources", "issue": f"来源 id 重复：{sid!r}"})
        ids.add(sid)
        if kind not in VALID_SOURCE_KINDS:
            p0.append({"id": f"sources:{sid}", "issue": (
                f"来源 {sid!r} 的 kind={kind!r} 不在 {VALID_SOURCE_KINDS} —— "
                f"来源必须是片外的文献（fact）或明确标注的比喻（analogy）；"
                f"AI 生成的 see / ink 描述不是事实来源")})
        if kind == "fact" and not (s.get("url") or s.get("title")):
            p1.append({"id": f"sources:{sid}", "issue": f"事实来源 {sid!r} 既没 url 也没 title —— 审读时无从查起"})

    for sid, shot in shots_of(story):
        for where, c in claims_of(shot):
            kind = str(c.get("kind") or "").strip()
            src = str(c.get("source") or "").strip()
            label = f"{sid}.{where}"
            if kind not in VALID_CLAIM_KINDS:
                p0.append({"id": label, "issue": f"claim.kind={kind!r} 不在 {VALID_CLAIM_KINDS}"})
                continue
            if src and src not in ids:
                p0.append({"id": label, "issue": (
                    f"claim.source={src!r} 在 sources 里不存在（现有：{' / '.join(sorted(ids)) or '无'}）—— "
                    f"引用了不存在的来源，审读时对不上")})
            if kind == "analogy" and src:
                p0.append({"id": label, "issue": (
                    f"claim.kind=analogy 却带了 source={src!r} —— "
                    f"类比不是机制事实，挂到文献上会被当成事实引用。"
                    f"比喻写 kind=analogy + note（说明它只是帮助理解）")})
            if kind == "fact" and not src:
                p1.append({"id": label, "issue": (
                    f"可核验断言没标来源（{str(c.get('text') or c.get('note') or '')[:20]}…）—— "
                    f"写 source 指向 sources 里的文献，或改成 kind=analogy 并说明它是比喻")})
    return p0, p1


def review_list(story: dict) -> list[dict]:
    """人工审读清单：含数字 / 年份的**未标注**文本。机器判不了对错，但保证它们被看见。"""
    out = []
    for sid, shot in shots_of(story):
        claimed = bool(claims_of(shot))
        texts = []
        c = shot.get("content") or {}
        for k, v in list(c.items()) + [(k, v) for k, v in shot.items() if k not in ("content", "claim")]:
            if isinstance(v, str) and v.strip():
                texts.append((k, v))
        for k, v in texts:
            hits = NUM_RE.findall(v) + YEAR_RE.findall(v)
            if hits and not claimed:
                out.append({"shot": sid, "field": k, "text": v, "numbers": sorted(set(hits))})
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--review", action="store_true", help="打印人工审读清单（含数字/年份的未标注文本）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv[1:])
    project = Path(a.project).resolve()
    story = load_story(project)
    if story is None:
        print(f"读不到 story.json：{project}", file=sys.stderr)
        return 2

    p0, p1 = check_facts(story)
    review = review_list(story)

    if a.json:
        print(json.dumps({"p0": p0, "p1": p1, "review": review}, ensure_ascii=False, indent=2))
    else:
        print("validate-facts · 内容事实质量的标注与审读（P2-22）")
        print("  这条只保证标注合法，不保证事实正确 —— 事实对错要人工审读。")
        for item in p0:
            print(f"  P0 {item['id']}: {item['issue']}")
        for item in p1:
            print(f"  P1 {item['id']}: {item['issue']}")
        if a.review:
            print(f"\n人工审读清单（{len(review)} 条含数字/年份的未标注文本 —— 机器判不了对错，但它们被看见了）：")
            for r in review:
                print(f"  {r['shot']}.{r['field']}: {r['text'][:50]}  数字: {' / '.join(r['numbers'][:5])}")
            if not review:
                print("  （没有）")
        print(f"结论：P0={len(p0)} P1={len(p1)} → {'PASS' if not p0 else 'FAIL'}"
              f"（P1 不拦出片；P0 是标注自己说不通）")
    return 1 if p0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
