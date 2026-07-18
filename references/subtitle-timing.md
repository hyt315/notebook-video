# Subtitle timing and absolute-frame contract

## Meaning chooses the boundary; word timing binds it

Never choose a final subtitle boundary from character count. First listen to or read the narration and author one semantic phrase per line. Split only at a punctuation mark, clause boundary or real spoken pause. Then use the TTS JSON `part`, `start` and `end` milliseconds to bind those approved lines back to exact word boundaries.

Before building cues, create `manifests/protected-caption-phrases.txt`, one phrase per line. It must contain:

- every product, company, person and model name;
- every benchmark or technical proper noun;
- every number together with its unit or comparison target;
- fixed technical phrases such as `上下文窗口` or `完整权重`;
- any short phrase whose meaning becomes incomplete if divided.

Examples of forbidden breaks include `Kimi K` / `3`, `DeepSeek` / `时刻`, `上下` / `文窗口`, `完整权` / `重`, and `Opus` / `四点八`. If a protected phrase is too wide, rewrite the narration; never split the phrase.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" build-semantic-captions audio/narration.mp3.json manifests/semantic-caption-lines.txt manifests/caption-cues.json --lead-ms 60
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
- Keep the strip, orange locator and blue ring fixed.
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

Reject word-stream mismatch, non-semantic segmentation, a protected phrase crossing a cue boundary, an ASCII model/product token split, overflow, horizontal jitter, two-line text, trailing visual punctuation, dark subtitle side marks or a changed contour.
