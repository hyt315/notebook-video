#!/usr/bin/env python3
"""Reject caption cues whose boundaries cut something the language keeps whole.

Three checks, strongest first:

1. **Phrase rule** — a cue boundary must land on a BudouX phrase boundary or right after a
   clause mark. This is the general rule; it catches `传到服` / `务器。` and any other
   mid-word cut that nobody thought to list. Needs the BudouX model from the project's
   `node_modules`. When that is missing the check is skipped **loudly on stderr** and the
   exit code is unaffected — that keeps this script runnable on a bare fixture — BUT a
   skip that reports success is exactly the failure mode this gate exists for, so the
   delivery path passes **`--require-budoux`**: with that flag a missing model is an error
   (non-zero exit) and the run says how to fix it (install deps, or `--no-budoux` to skip
   on purpose). Default behaviour is unchanged for everyone else.
2. **Mechanical rules** — never let a closing mark start a cue, never let an opening
   bracket end one, never split an ASCII/digit token. Always on, no model needed.
3. **Protected phrases** — `manifests/protected-caption-phrases.txt` must appear intact.
   Kept as a curated last mile for names and fixed phrases the model should not overrule;
   it is no longer the only thing standing between a word cut and the render.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

RULE_SOURCE = Path(__file__).resolve().parent / "build-semantic-captions.py"


def load_rule_module():
    """The break rule lives in the builder; import it instead of keeping a second copy."""
    spec = importlib.util.spec_from_file_location("_semantic_break_rule", RULE_SOURCE)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load the break rule from {RULE_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("caption_cues_json", type=Path)
    parser.add_argument("protected_phrases_txt", type=Path)
    parser.add_argument("--budoux-dir", default=None,
                        help="directory holding node_modules (default: search up from the caption file)")
    parser.add_argument("--no-budoux", action="store_true",
                        help="skip the phrase rule on purpose, e.g. for a fixture outside a project")
    parser.add_argument("--require-budoux", action="store_true",
                        help="fail (non-zero) instead of skipping when BudouX is not resolvable "
                             "— use this on the delivery path, where 'SKIPPED' must never pass for 'checked'")
    args = parser.parse_args()

    if args.no_budoux and args.require_budoux:
        raise SystemExit("--no-budoux and --require-budoux contradict each other: pass one of them, not both")

    rule = load_rule_module()

    data = json.loads(args.caption_cues_json.read_text(encoding="utf-8"))
    cues = data.get("cues") if isinstance(data, dict) else None
    if not isinstance(cues, list) or not cues:
        raise SystemExit("Expected a non-empty caption file with cues")
    if data.get("segmentation") != "semantic":
        raise SystemExit("Caption segmentation must be semantic")

    phrases = [
        normalized(line)
        for line in args.protected_phrases_txt.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not phrases:
        raise SystemExit("Protected phrase manifest must not be empty")

    texts = [normalized(str(cue.get("text", ""))) for cue in cues]
    stream = "".join(texts)
    boundaries: list[int] = []
    cursor = 0
    for text in texts[:-1]:
        cursor += len(text)
        boundaries.append(cursor)

    failures: list[str] = []

    # ---- 1. 短语规则：断点必须落在可断的位置 ----
    node = shutil.which("node") or shutil.which("node.exe")
    root = None if args.no_budoux else rule.find_budoux_root(
        args.budoux_dir, [args.caption_cues_json.parent, Path.cwd()])
    if root and not node:
        raise SystemExit("node is required to run the BudouX phrase rule (or pass --no-budoux)")
    if root and node:
        legal = rule.budoux_breaks(node, root, stream) | rule.punctuation_breaks(stream)
        legal -= rule.ascii_interior(stream)
        legal -= rule.head_tail_blocked(stream)
        for index, boundary in enumerate(boundaries, 1):
            if boundary not in legal:
                left = stream[max(0, boundary - 3):boundary]
                right = stream[boundary:boundary + 3]
                if right and right[0] in rule.NO_LINE_START:
                    why = f"would start a cue with the closing mark {right[0]!r} (避头尾)"
                else:
                    why = "splits a word or ASCII token"
                failures.append(
                    f"cue {index}/{index + 1}: break at character {boundary} {why}: "
                    f"{left!r} | {right!r}"
                )
        rule_state = f"enforced (BudouX from {root})"
    else:
        # 找不到 BudouX：默认**跳过但不失败**（夹具目录里本来就没有 node_modules，这条不该拦它们）。
        # 但"跳过"与"跑过"的收尾文字在这里几乎一样 —— 那正是本门禁最怕的"看起来通过、其实没跑"，
        # 所以两个处置同时给：① 交付路径用 `--require-budoux` 把跳过变成失败；② 告警写得足够刺眼。
        detail = ("BudouX is not resolvable from any project node_modules, so the phrase rule "
                  "(the one that catches a word cut that is not on the protected list) did NOT run.")
        fix = ("Fix one of: run `npm ci` in the project · pass --budoux-dir <node_modules> · "
               "on the delivery path pass --require-budoux · to skip on purpose, pass --no-budoux.")
        if args.require_budoux:
            raise SystemExit(f"SEMANTIC BREAK ERROR: --require-budoux was given, but {detail}\n  {fix}")
        rule_state = "SKIPPED — BudouX not found (the phrase rule did NOT run)"
        print(
            "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            f"WARNING: {detail}\n"
            "         This run enforced ONLY the mechanical rules + the protected phrase list,\n"
            "         so the result below is NOT a phrase-rule pass.\n"
            f"         {fix}\n"
            "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",
            file=sys.stderr)

    # ---- 2. 机械规则：避头尾 + ASCII 词内不断（不需要模型）----
    for index, text in enumerate(texts, 1):
        if text and text[0] in rule.NO_LINE_START:
            failures.append(f"cue {index}: starts with a closing mark {text[0]!r} — a stray "
                            f"punctuation fragment, not a semantic line: {text!r}")
        if text and text[-1] in rule.NO_LINE_END:
            failures.append(f"cue {index}: ends with an opening bracket {text[-1]!r}: {text!r}")
    for index, (left, right) in enumerate(zip(texts, texts[1:]), 1):
        if left and right and re.search(r"[A-Za-z0-9]$", left) and re.match(r"[A-Za-z0-9]", right):
            failures.append(
                f"cue {index}/{index + 1}: ASCII product, model, benchmark or number token is split"
            )

    # ---- 3. 保护短语：人工表的最后一道（不再是唯一一道）----
    for phrase in phrases:
        starts = [match.start() for match in re.finditer(re.escape(phrase), stream)]
        if not starts:
            failures.append(f"protected phrase not found in captions: {phrase}")
            continue
        for start in starts:
            end = start + len(phrase)
            crossed = sorted(point for point in boundaries if start < point < end)
            if crossed:
                failures.append(f"protected phrase crosses a cue boundary: {phrase}")

    if failures:
        for failure in failures:
            print(f"SEMANTIC BREAK ERROR: {failure}")
        raise SystemExit(f"{len(failures)} semantic caption break failure(s)")
    print(f"Validated {len(cues)} semantic cues and {len(phrases)} protected phrases "
          f"(phrase rule: {rule_state})")


if __name__ == "__main__":
    main()
