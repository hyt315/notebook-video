#!/usr/bin/env python3
"""Bind editor-approved semantic subtitle lines to exact TTS word boundaries.

The approved lines stay the semantic authority. What changed (2026-09-22) is that a cue
boundary is no longer trusted just because it lands on a TTS word: it must also land where
the *language* allows a break. A fixed-width character wrap is not a rule, it is a patch --
wrapping `很多人以为 push 就是把文件传到服务器。` at 17 characters produced `传到服` / `务器。`
and no gate could see it, because Chinese TTS reports one word per character, so every
character position looked like a legal word boundary.

Break rule (`references/subtitle-timing.md`):
  legal   = BudouX phrase boundaries + positions right after clause punctuation
  illegal = inside a word, inside an ASCII/digit token, before a closing mark,
            after an opening bracket, or inside a protected phrase
An approved boundary that violates the rule is moved to the nearest legal position. The cue
count can only stay equal or shrink (a boundary that lands on its neighbour merges an empty
cue away). Legal positions come from the BudouX model the template already depends on,
resolved from the project's `node_modules`; without it the mechanical half of the rule still
runs and the tool says so on stderr instead of silently dropping a check.
"""

from __future__ import annotations

import argparse
import bisect
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

WHITESPACE = re.compile(r"\s+")

# 断在收尾标点之后 = 合法（宽集合：省略号/破折号之后也算合法断点）。
BREAK_AFTER = "，。！？；：、’”％‰℃°〕〉》」』】,…—·;,.!?)]}"
# 避头尾：这些不能起行（窄集合：只收标准禁则字符，不误伤有意起行的省略号/破折号）。
NO_LINE_START = "，。、；：！？）》」』】”’％‰℃°·,.;:!?)]}"
# 避头尾：这些不能收行。
NO_LINE_END = "‘“（《「『【〔〈([{"
# 拉丁/数字串：内部一律不许断（`push`、`github.com`、`hyt315`、`3090`）。
ASCII_RUN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._%+\-/:@#]*")

# BudouX 桥：把整段文本交给短语切分模型，回传 chunk 数组（无损，可拼回原文）。
# 离线、纯函数、版本由项目 lock 锁死；只读模型，不写任何东西。
BUDOUX_BRIDGE = """
import {pathToFileURL} from "node:url";
let raw = "";
process.stdin.setEncoding("utf8");
for await (const chunk of process.stdin) raw += chunk;
const root = process.argv[1];
const {texts} = JSON.parse(raw);
const budoux = await import(pathToFileURL(root + "/budoux/module/index.js").href);
const parser = budoux.loadDefaultSimplifiedChineseParser();
process.stdout.write(JSON.stringify(texts.map((text) => parser.parse(text))));
"""


def normalized(text: str) -> str:
    return WHITESPACE.sub("", text)


def ascii_interior(text: str) -> set[int]:
    """Offsets strictly inside an ASCII/digit token — never a legal break."""
    blocked: set[int] = set()
    for match in ASCII_RUN.finditer(text):
        blocked.update(range(match.start() + 1, match.end()))
    return blocked


def punctuation_breaks(text: str) -> set[int]:
    """Offsets right after a clause mark — always a legal break, always a good one."""
    return {index + 1 for index, char in enumerate(text) if char in BREAK_AFTER and index + 1 < len(text)}


def head_tail_blocked(text: str) -> set[int]:
    """避头尾：不许让收尾标点起行，也不许让开引号收行。"""
    blocked: set[int] = set()
    last = len(text) - 1
    for index, char in enumerate(text):
        if index > 0 and char in NO_LINE_START:
            blocked.add(index)
        if index < last and char in NO_LINE_END:
            blocked.add(index + 1)
    return blocked


def protected_spans(stream: str, phrases: list[str]) -> tuple[set[int], list[str]]:
    """Offsets inside a protected phrase — never a legal break."""
    blocked: set[int] = set()
    missing: list[str] = []
    for phrase in phrases:
        starts = [match.start() for match in re.finditer(re.escape(phrase), stream)]
        if not starts:
            missing.append(phrase)
            continue
        for start in starts:
            blocked.update(range(start + 1, start + len(phrase)))
    return blocked, missing


def find_budoux_root(explicit: str | None, bases: list[Path]) -> Path | None:
    marker = Path("budoux") / "module" / "index.js"
    if explicit:
        given = Path(explicit)
        for candidate in (given, given / "node_modules"):
            if (candidate / marker).is_file():
                return candidate
        raise SystemExit(f"--budoux-dir does not contain {marker}: {explicit}")
    seen: set[Path] = set()
    for base in bases:
        current = base.resolve()
        for _ in range(8):
            modules = current / "node_modules"
            if modules not in seen:
                seen.add(modules)
                if (modules / marker).is_file():
                    return modules
            if current.parent == current:
                break
            current = current.parent
    return None


def budoux_breaks(node: str, root: Path, text: str) -> set[int]:
    payload = json.dumps({"texts": [text]}, ensure_ascii=False)
    proc = subprocess.run(
        [node, "--input-type=module", "-e", BUDOUX_BRIDGE, str(root)],
        input=payload, capture_output=True, text=True, encoding="utf-8",
    )
    if proc.returncode != 0:
        raise SystemExit(f"BudouX segmentation failed (node exit {proc.returncode}): {proc.stderr.strip()[:400]}")
    chunks = json.loads(proc.stdout)
    if not chunks or "".join(chunks[0]) != text:
        raise SystemExit("BudouX segmentation is not lossless; refusing to guess break positions")
    breaks: set[int] = set()
    offset = 0
    for chunk in chunks[0][:-1]:
        offset += len(chunk)
        breaks.add(offset)
    return breaks


def nearest_legal(legal: list[int], target: int, low: int, high: int, preferred: set[int]) -> int | None:
    """Closest legal offset to `target` within [low, high].

    A break right after a clause mark is preferred when it is at most one character
    further away than the alternative: moving a boundary onto punctuation keeps the mark
    with the sentence it closes, and without that preference a boundary sitting just before
    a `，` would be pushed backwards into the middle of the preceding word.
    """
    start = bisect.bisect_left(legal, low)
    stop = bisect.bisect_right(legal, high)
    if start >= stop:
        return None
    index = bisect.bisect_left(legal, target, start, stop)
    candidates = [legal[i] for i in (index - 1, index, index + 1) if start <= i < stop]
    if not candidates:
        return None
    return min(candidates, key=lambda offset: (abs(offset - target) - (0.5 if offset in preferred else 0.0), offset))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("words_json", type=Path)
    parser.add_argument("lines_txt", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("--lead-ms", type=int, default=60)
    parser.add_argument("--protected-phrases", type=Path,
                        help="manifests/protected-caption-phrases.txt: never break inside these")
    parser.add_argument("--budoux-dir", default=None,
                        help="directory holding node_modules (default: search up from the project)")
    parser.add_argument("--no-budoux", action="store_true",
                        help="skip phrase segmentation; only the mechanical half of the rule runs")
    parser.add_argument("--warn-chars", type=int, default=0,
                        help="warn (never break) when a cue exceeds this many characters; "
                             "off by default because width is a pixel question and the shipped "
                             "templates legitimately run to 19 characters")
    args = parser.parse_args()

    words = json.loads(args.words_json.read_text(encoding="utf-8"))
    raw_lines = [line for line in args.lines_txt.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not isinstance(words, list) or not words or not raw_lines:
        raise SystemExit("Expected a non-empty TTS word list and semantic line list")
    for word in words:
        if not all(key in word for key in ("part", "start", "end")):
            raise SystemExit(f"Malformed timing item: {word!r}")

    # ---- 字符流与词级偏移：中文 TTS 逐字报词，所以"落在词边界"根本不构成约束 ----
    word_texts = [normalized(str(word["part"])) for word in words]
    word_starts: set[int] = set()
    offset = 0
    for text in word_texts:
        word_starts.add(offset)
        offset += len(text)
    total = offset
    stream = "".join(word_texts)

    raw_stream = "".join(raw_lines)
    if normalized(raw_stream) != stream:
        raise SystemExit(
            f"Semantic lines do not match the TTS word stream "
            f"({len(normalized(raw_stream))} vs {total} characters)"
        )
    raw_index = [index for index, char in enumerate(raw_stream) if not char.isspace()]

    approved: list[int] = []
    line_end = 0
    for line in raw_lines:
        line_end += len(normalized(line))
        approved.append(line_end)
    if approved and approved[-1] != total:
        raise SystemExit("Semantic lines do not cover the whole TTS word stream")
    approved.pop()  # the final boundary is the end of the stream, not a break

    # ---- 可断位置 ----
    phrases: list[str] = []
    if args.protected_phrases:
        phrases = [normalized(line)
                   for line in args.protected_phrases.read_text(encoding="utf-8").splitlines()
                   if line.strip() and not line.lstrip().startswith("#")]
    legal = set(word_starts)
    node = shutil.which("node") or shutil.which("node.exe")
    root = None if args.no_budoux else find_budoux_root(
        args.budoux_dir,
        [args.lines_txt.parent, args.output_json.parent, Path.cwd()],
    )
    if root and not node:
        raise SystemExit("node is required to run the BudouX break rule (or pass --no-budoux)")
    if root and node:
        legal &= budoux_breaks(node, root, stream) | punctuation_breaks(stream)
        break_rule = f"budoux+punctuation ({root})"
    else:
        # 没有分词模型时只禁止"可证明是错的"位置，绝不猜词边界、绝不误改合法断点。
        break_rule = "mechanical-only (BudouX unavailable)"
        print(f"WARNING: BudouX not found under any project node_modules -- the phrase rule is "
              f"NOT enforced, only ASCII tokens, stray punctuation and protected phrases. "
              f"Run `npm ci` in the project (or pass --budoux-dir) to enforce it.", file=sys.stderr)
    legal -= ascii_interior(stream)
    legal -= head_tail_blocked(stream)
    if phrases:
        spans, missing = protected_spans(stream, phrases)
        legal -= spans
        for phrase in missing:
            print(f"WARNING: protected phrase not found in the word stream: {phrase}", file=sys.stderr)
    legal_sorted = sorted(legal)

    # ---- 修断点：只在非法时移动，且移到最近的合法位置 ----
    preferred = punctuation_breaks(stream)
    placed: list[int] = []
    repairs: list[tuple[int, int, int]] = []
    previous = 0
    for index, boundary in enumerate(approved, 1):
        target = nearest_legal(legal_sorted, boundary, previous, total, preferred)
        if target is None:
            raise SystemExit(
                f"Cue {index} cannot be placed on a legal break: no legal position in "
                f"[{previous}, {total}] near character {boundary}"
            )
        if target != boundary:
            repairs.append((index, boundary, target))
        placed.append(target)
        previous = target

    def raw_slice(start: int, end: int) -> str:
        if end <= start or start < 0 or end > total:
            return ""
        return raw_stream[raw_index[start]:raw_index[end - 1] + 1].strip()

    bounds = [0, *placed, total]
    cues = []
    cursor = 0
    for index, (start, end) in enumerate(zip(bounds, bounds[1:]), 1):
        text = raw_slice(start, end)
        if not text:
            continue
        target = normalized(text)
        consumed = []
        built = ""
        while len(built) < len(target):
            if cursor >= len(words):
                raise SystemExit(f"Cue {index} runs past the end of the TTS word list: {text!r}")
            consumed.append({
                "part": str(words[cursor]["part"]),
                "start": int(words[cursor]["start"]),
                "end": int(words[cursor]["end"]),
            })
            built += word_texts[cursor]
            cursor += 1
        if built != target:
            raise SystemExit(f"Cue {index} does not end on a TTS word boundary: {text!r} != {built!r}")
        start_ms = max(0, consumed[0]["start"] - args.lead_ms)
        end_ms = consumed[-1]["end"]
        cues.append({
            "text": text,
            "words": consumed,
            "start_ms": start_ms,
            "speech_end_ms": end_ms,
            "reveal_end_ms": end_ms,
            "start": round(start_ms / 1000, 3),
            "speech_end": round(end_ms / 1000, 3),
            "reveal_end": round(end_ms / 1000, 3),
        })

    if cursor != len(words):
        raise SystemExit(f"Unmatched TTS words: {len(words) - cursor}")

    result = {
        "source": str(args.words_json),
        "lead_ms": args.lead_ms,
        "segmentation": "semantic",
        "break_rule": break_rule,
        "cues": cues,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Created {len(cues)} semantic subtitle cues: {args.output_json}")
    print(f"Break rule: {break_rule}")
    if repairs:
        print(f"Repaired {len(repairs)} boundary/boundaries that would have cut a word:")
        for index, was, now in repairs:
            print(f"  approved boundary {index}: character {was} -> {now} "
                  f"({raw_slice(max(0, now - 2), now)}|{raw_slice(now, min(total, now + 2))})")
    if args.warn_chars > 0:
        long_cues = [(index, len(normalized(cue["text"])), cue["text"])
                     for index, cue in enumerate(cues, 1) if len(normalized(cue["text"])) > args.warn_chars]
        if long_cues:
            print(f"WARNING: {len(long_cues)} cue(s) exceed {args.warn_chars} characters -- "
                  f"CaptionFitGate measures the real pixel width and may reject the render. "
                  f"Re-author the narration instead of breaking inside a word.", file=sys.stderr)
            for index, length, text in long_cues:
                print(f"  cue {index}: {length} chars {text!r}", file=sys.stderr)


if __name__ == "__main__":
    main()
