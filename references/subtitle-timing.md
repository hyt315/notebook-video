# Subtitle timing and absolute-frame contract

## Meaning chooses the boundary; word timing binds it

Never choose a final subtitle boundary from character count. First listen to or read the narration and author one semantic phrase per line. Split only at a punctuation mark, clause boundary or real spoken pause. Then use the TTS JSON `part`, `start` and `end` milliseconds to bind those approved lines back to exact word boundaries.

### A word boundary is not a legal break (the trap that shipped a broken film)

"Ends on a TTS word" proves nothing in Chinese: the adapter reports **one word per character**, so every character position looks like a legal word boundary and `传到服` / `务器。` binds cleanly. A real production hit exactly that — a fixed-width wrap at 17 characters cut `服务器` into two cues, and `什么` the same way — and no gate saw it, because the only thing checking breaks was the hand-written phrase list, which `服务器` was not on. **A phrase list is a patch; the rule below is the fix.**

### The break rule (implemented in `build-semantic-captions.py` and `validate-semantic-breaks.py`)

A cue boundary is legal only if it is one of:

1. a **BudouX phrase boundary** — `budoux.loadDefaultSimplifiedChineseParser()`, the model `package.json` already depends on; or
2. the position **right after a clause mark** (`，。！？；：、…—` and the ASCII equivalents).

And never if it is:

3. inside an **ASCII/digit token** (`push`, `github.com`, `hyt315`, `3090`) — BudouX will happily split Latin runs, so this rule is mandatory;
4. **避头尾** — a cue may not *start* with `，。、；：！？）》」』】”’％‰℃°·` and may not *end* with `“‘（《「『【〔〈`;
5. inside a **protected phrase** from the manifest.

The builder keeps the approved lines as the semantic authority and only **moves a boundary that violates the rule**, to the nearest legal position. It never re-wraps a legal line, so regenerating an approved project is a no-op (both shipped templates regenerate byte-identically). Cue count can only stay equal or shrink: a stray `。` or `，` that a mechanical wrap orphaned onto its own line gets absorbed back into the sentence it closes.

Preferring a clause-mark break on an equidistant tie is load-bearing — without it a boundary sitting just before `，` is pushed backwards into the middle of the preceding word.

### Self-test it (do this, do not assume)

```text
# 1. Build. The tool prints every boundary it had to move and why, and warns about long cues.
node "<SKILL_DIR>/scripts/notebook-video.mjs" build-semantic-captions audio/narration.mp3.json manifests/semantic-caption-lines.txt manifests/caption-cues.json --lead-ms 60 --protected-phrases manifests/protected-caption-phrases.txt

# 2. Gate it. `phrase rule: enforced` on the last line is the proof the rule ran; if it says
#    SKIPPED, BudouX was not resolvable and the word-cut rule did NOT run.
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-semantic-breaks manifests/caption-cues.json manifests/protected-caption-phrases.txt
```

Both tools find BudouX by walking up from the caption file to the project's `node_modules`. **If the project has not run `npm ci` yet, the phrase rule is skipped and the tools say so on stderr** — they print `WARNING: BudouX ...`, the validator still exits 0, and the cue file records `"break_rule": "mechanical-only (BudouX unavailable)"`. That degradation is loud on purpose: a silently skipped check is the same defect as no check. Pass `--budoux-dir PATH` to point at any `node_modules` that has `budoux`.

To see the rule actually work on a project that has no `node_modules`, point at one that does and feed it the fixture:

```text
python scripts/validate-semantic-breaks.py bad-cues.json protected.txt --budoux-dir /path/to/node_modules
# a cue pair cut as '上网就是连到一台服' / '务器。' reports:
#   SEMANTIC BREAK ERROR: cue 1/2: break at character 9 splits a word or ASCII token: '一台服' | '务器。'
```

`--no-budoux` runs the mechanical half only (rules 3–5), which needs no model and still catches orphaned punctuation and split product names.

### Width is a separate, softer budget

Character count stays a drafting hint, never a break rule. `--warn-chars N` is off by default and only *warns* when a cue exceeds N characters: no character threshold can be both useful and false-alarm-free, because the shipped templates legitimately run to 19 characters (`在GitHub，全世界的开发者，` is only 16) and `CaptionFitGate` measures the real pixel width in the render browser, rejecting anything over `mode.safe`. When a cue is too wide, **rewrite the narration** or accept more cues; never push the boundary into the middle of a word to hit a number.

## Protected phrases: the curated last mile

Before building cues, create `manifests/protected-caption-phrases.txt`, one phrase per line. It must contain:

- every product, company, person and model name;
- every benchmark or technical proper noun;
- every number together with its unit or comparison target;
- fixed technical phrases such as `上下文窗口` or `完整权重`;
- any short phrase whose meaning becomes incomplete if divided.

Examples of forbidden breaks include `Kimi K` / `3`, `DeepSeek` / `时刻`, `上下` / `文窗口`, `完整权` / `重`, and `Opus` / `四点八`. If a protected phrase is too wide, rewrite the narration; never split the phrase.

This list is the **last mile, not the safety net**. It cannot be complete — `服务器` was missing from a 17-phrase list and that omission shipped — so it exists for names and curated phrases that outrank the model, while the rule above catches the general case. A phrase that no longer appears in the narration is a gate failure, not a harmless leftover: keep the list in step with the script.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" build-semantic-captions audio/narration.mp3.json manifests/semantic-caption-lines.txt manifests/caption-cues.json --lead-ms 60 --protected-phrases manifests/protected-caption-phrases.txt
```

Keep complete clauses, product names and short tails together. Character count is only a drafting hint; pixel width is authoritative.


## Convert once to frames

At the data boundary:

```ts
const msFrame = (ms: number) => Math.round(ms * FPS / 1000);
```

Create `startFrame` and `endFrame` for cues and words once. Subtitle, animation and audio cues must use the same `FPS` and frame convention. Do not compare seconds or milliseconds inside scene components.

## Reveal behavior

- Reveal at measured word starts with about 60ms of visual lead, equal to two frames at 30fps.
- Keep the completed cue until the next cue.
- Reserve the complete phrase width from the first word.
- Keep the pinned pure caption text fixed (no bar, no locator, no ring).
- Preserve internal punctuation.
- Hide only trailing punctuation visually.
- Keep one line within 1334px.

## Validation

Run the browser fit gate plus both file validators after any narration edit:

```text
# CaptionFitGate runs automatically during Remotion render. It measures the bundled font,
# converts delivery-scaled width back to design pixels, and rejects widths over 1334px.
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-caption-sync audio/narration.mp3.json manifests/caption-cues.json
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-semantic-breaks manifests/caption-cues.json manifests/protected-caption-phrases.txt
```

Reject word-stream mismatch, non-semantic segmentation, a break that is not a BudouX phrase boundary or a clause break, a cue starting with a closing mark, an ASCII model/product token split, a protected phrase crossing a cue boundary, overflow, horizontal jitter, two-line text, trailing visual punctuation, dark subtitle side marks or a changed contour.

The word-cut rule is the one that catches what the phrase list misses, so read the validator's last line: it ends with `phrase rule: enforced (BudouX from …)` when the rule ran, and with the word skipped followed by "BudouX not found" when it did not — in that case only the mechanical checks and the phrase list were applied.
