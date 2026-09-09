---
name: notebook-video
version: 2.9.0
description: Create editable Chinese explainer and promotional videos with React, SVG and Remotion. Use for 科普视频、手账风视频、知识讲解、产品宣传、中文配音字幕、网站动画转 MP4 and 30-second to multi-minute videos. Includes three native-30fps 2K canvases, four themes, reusable motion components, optional image-led storytelling, speech/caption timing, rendering and QA. No image-generation service is required.
---

# Notebook Video

Deliver a validated MP4 and editable project, not just a storyboard or silent preview. Default to Chinese narration, native 30fps and the bundled lecture template. Keep the established visual identity; improve how content is explained rather than adding decorative motion.

## Read only what this production needs

1. Start with [lecture composition](references/lecture-composition.md) and [shot recipes](references/shot-recipes.md). Choose an explanatory action before a component.
2. Read [Remotion architecture](references/remotion-architecture.md) when assembling scenes or changing duration; consult the [locked contract](references/locked-style-contract.json) for exact tokens.
3. Select one theme and canvas. Read [canvas modes](references/canvas-modes.md), then only the selected skin: [paper](references/visual-system.md), [cel](references/theme-cel.md), [sticker](references/theme-sticker.md) or [flat](references/theme-flat.md). Add [portrait guidance](references/portrait-illustration-system.md) for 3:4.
4. Load specialist references at the relevant step below. Do not read every theme, repeat the same analysis or reproduce the engine from memory.

The copied implementation is the starting point, not a requirement to reproduce its topic, card count or scene grammar. Preserve typography, palette, caption chrome, native frame rate, resource gates and declarative audio. Change scene content, composition and motion purpose to suit the subject.

## Permissions and scope

Dependency checks and validation are read-only, apart from explicitly requested QA outputs. Never change system settings as a diagnostic step. A request to produce or optimize a video authorizes the necessary project-local work and renders; confirm material unknown costs, external services, rights or destructive changes. Respect any explicit approval requirement for installs, renders, commits, pushes or PRs.

Use available, authorized tools. Do not assume an agent has image generation or TTS because of its product name. No provider, API key, proxy or voice is hardcoded into the workflow. Do not package credentials.

## 1. Lock the brief

Infer existing decisions from the conversation. Ask only about choices that materially affect output: claims, audience/platform, aspect ratio, voice, real brand assets, CTA or paid services. If unspecified, use 16:9, `paper`, a clear warm Mandarin voice and no prominent BGM. Do not re-ask a choice the user already made.

Supported canvases are 2560×1440 (16:9), 1920×1440 (4:3) and 1440×1920 (3:4), all native 30fps. The lecture template registers all three composition IDs; see the canvas reference before selecting a render ID.

Write narration and a compact storyboard with one question and one observable action per scene. Open with a verified consequence, contrast or question; do not invent statistics for a hook. Consult [narrative hook](references/narrative-hook.md) and [pacing](references/pacing-rhythm.md) when the opening or rhythm needs work.

## 2. Start from the working project

Use Node.js 20+, Python 3.10+ and FFmpeg/ffprobe. Python helpers use the standard library only.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" check-deps
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project ./film --style=paper
```

The target must be empty. `--style=paper|cel|sticker|flat` selects the lecture skin. `--classic` copies the original 16:9 visual-director example, not the multi-canvas theme system. Do not combine classic with a non-paper theme.

Keep fonts/licenses, `AssetGate`, `CaptionFitGate`, `CardFitGate`, subtitle/chrome and the audio tree. Lecture source separates the aesthetic core, component library and editable scene content. [Official exemplar](references/official-skills-exemplar.md) describes the older classic example.

## 3. Direct visuals from meaning

Use `manifests/asset-manifest.json` as the scene-window record. In the lecture template, scene mounting, chapter chrome and scene-local frames read those windows. Keep `duration_frames` and `DURATION` consistent. Storyboard prose explains the design; it is not another numeric timeline to maintain.

For each scene, record its question, main action, primary `visual_mode`, supporting visual if needed, and what carries into the next scene. Optional `beats` contain absolute `{frame, action}` entries for review, not a second animation engine.

| What the viewer needs to understand | Start with |
|---|---|
| Mechanism, process, relationship | One persistent object changing state or following the actual diagram path |
| Quantity or comparison | Common baseline, visible change, then a readable result |
| Concrete subject, context or evidence | Supplied/licensed image, screenshot or optional generated illustration; locate the relevant detail |
| Contrast, misconception or conclusion | Brief typography or replacement, then evidence or demonstration |

`pure-graphic`, `pure-text` and `image-text` describe the **dominant treatment**, not mutually isolated scene templates. A code diagram can own the explanation while an image supplies context, temporarily becomes the main view, and returns as an inset. A/B means a change of attention within the same argument, not mandatory alternating pages.

Reuse existing components first. [fxkit](references/fxkit.md) covers motion helpers; [shot recipes](references/shot-recipes.md) shows a small number of useful combinations, including `EvidenceBridge`. Add a component only when the existing ones cannot express a meaningful operation. Technical subject names do not mandate a particular radar/brain/security widget.

One dominant action is the density budget. Supporting zones are optional. Avoid narration duplicated as a bullet board, three equal cards in every shot, permanent busy backgrounds and an entry animation standing in for an explanation. A long reading hold may be intentional; a meaningless zoom is not a semantic beat.

### Images and assets

Read [visual director](references/visual-director.md) when a shot benefits from imagery. Inspect available tools and rights first. User-supplied and licensed assets do not require an image-generation opt-in. Offer generation once if it materially helps and is available, unless the user already authorized it. If unavailable or declined, use a suitable code-drawn illustration without blocking the film.

Use images for concrete appearance/context, not exact numbers, charts or UI labels. Render precise text/arrows in Remotion. Label schematic or generated imagery as illustration when it might be mistaken for documentary evidence. Store only used images in `public/illustrations/`; register source, description/prompt, crop, rights and SHA-256 in the project's `manifests/visual-assets.json`. Theme background rasters are already registered and do not count as generated topic art.

Use Remotion `Img`, including inside `KenBurnsImg`/`EvidenceZoom`; it waits for decoding and fails on missing assets. The lecture `AssetGate` waits for fonts; media components own their loading gates. Never bypass a failed gate with an empty placeholder in a final render.

## 4. Produce audio and bind semantic captions

Read [TTS/audio](references/tts-audio.md) and [subtitle timing](references/subtitle-timing.md).

1. Author semantic lines and protected phrases from meaning, not a character-count cut. Narration and lines must reconstruct the same text.
2. Generate `audio/narration.mp3` and integer-ms `{part,start,end}` timing JSON at `audio/narration.mp3.json`. Record voice/provider/rights.
3. Prefer measured provider word boundaries. The bundled OpenAI-compatible adapter measures **chapters**, but estimates character timing. Its `tts-segments.json` declares `timing_quality: estimated-character`; it is not forced alignment. Listen and correct important word beats before claiming tight synchronization.
4. Optional `speed-post.py` runs once on fresh synthesis, **before** captions and scene timing. It updates timing metadata and rejects accidental repeat processing. Do not treat a fixed speed multiplier as a universal speaking-rate target.
5. Build cues, then sync:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" build-semantic-captions ./film/audio/narration.mp3.json ./film/manifests/semantic-caption-lines.txt ./film/manifests/caption-cues.json --lead-ms 60
node "<SKILL_DIR>/scripts/notebook-video.mjs" sync ./film
```

Milliseconds become integer frames once via `Math.round(ms * fps / 1000)`. Use those frames for visual emphasis and action audio. Subtract the scene start exactly once for scene-local animation. Remotion `Sequence` already shifts `useCurrentFrame()` to local time; do not subtract its start again.

Keep one bottom-pinned caption line with stable full-text width and no bar/border. Strip trailing punctuation visually, retain internal punctuation and exact source spacing. `CaptionFitGate` measures the actual selected canvas/font. File validators check consistency, not whether the voice pronounced a word correctly.

## 5. Animate and reuse

Read [motion design](references/motion-design.md) and, for transfers/occlusion, [independent parts](references/independent-parts.md).

- Recognition → operation/relation → consequence → readable hold. Retire obsolete supporting parts rather than stacking more.
- A moving object follows the **same geometry** as its drawn route. Change state on arrival, not before contact.
- Prefer a cut, local reveal or shared visual anchor. The `EvidenceBridge` recipe promotes one persistent image without shortening the narration timeline. Do not introduce transition overlap by silently subtracting frames from measured speech.
- Keep one scene mounted, at most two for a deliberate transition. Unmount each obsolete group completely.
- Use transforms for movement, deterministic frame-driven easing/springs, and restrained local camera focus. Keep global chrome and subtitles fixed. No CSS-time animation or unseeded randomness.
- A close-up inside a clipped image viewport is not global camera movement. Landscape rig limits are center ±15px and scale ≤1.018; portrait is centered at (540,720), within ±10px and scale ≤1.02.
- Keep narration and sound effects in Remotion `Audio`/`Sequence`, with each effect tied to a visible action. Do not invent a separate FFmpeg sound timeline.

`retime.py` validates and edits duration/scene metadata; it does **not** rewrite semantic action beats, camera keys or sound. After changed narration, review those against the new cues. Prefer `TIMELINE_SCALE=1` for newly authored long films. Leave at least 0.7s after the final spoken word and a readable final CTA.

## 6. Validate cheaply, then render

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-project ./film
node "<SKILL_DIR>/scripts/notebook-video.mjs" review-plan ./film ./film/renders/review-plan.json
node "<SKILL_DIR>/scripts/notebook-video.mjs" review-frames ./film ./film/renders/review.mp4 START_FRAME END_FRAME
```

The review plan selects opening/final frames, every cut, longest caption and declared beats. Render the affected ranges first. Review actual pixels: accidental blank content, clipping, unsafe crops, subtitle fit, track/slot geometry and unfinished exits. Black detection alone cannot find an empty ivory slide; static layout checks cannot prove transformed elements never collide.

After those checks, make one full native-canvas render:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" render ./film ./film/renders/final.mp4
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-video ./film/renders/final.mp4 EXPECTED_SECONDS ./film/renders/contact-sheet.jpg
```

The launcher uses the lockfile, installs dependencies if missing or changed, and reuses unchanged render inputs. `REMOTION_BROWSER_EXECUTABLE` can point to an existing browser; the network shim is opt-in only. `benchmark-render` measures concurrency; reuse its recommendation via `REMOTION_CONCURRENCY`. See [performance](references/performance-design.md) and [cross-platform troubleshooting](references/cross-platform-compatibility.md). Range renders and `npm run render` in a copied template are **raw previews**, not loudness-normalized delivery.

## 7. Review and deliver

Use [quality checklist](references/quality-checklist.md). Automated gates are necessary, not a guarantee of narrative quality. Listen to the whole narration, check protected terms, and review transitions/long holds against the storyboard. Inspect whether the visual actually explains the key claim. Record unresolved issues rather than printing a pre-filled green fact card.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" package ./film ./film-source.zip
```

Deliver the MP4, source ZIP, narration/storyboard, manifests, contact sheet and a short fact card with **measured** dimensions/fps/duration/audio/QA status. Include licensing notes and distinguish estimated timing from measured word alignment. ZIP packaging retains active or unambiguous legacy speech segments and excludes known credential filenames, obsolete caches, temporary segments, renders and symlinks; inspect it for unusually named secrets before sharing.

## Maintaining the Skill

```text
python "<SKILL_DIR>/scripts/selftest.py"
python -m unittest discover -s tests
```

Run the rendering smoke test after changing TSX, themes, image loading or layout gates; see [testing](references/testing.md). Preserve classic compatibility and all lecture canvases. Do not replace the established aesthetic or publish a release without the user's approval. Prefer tested repairs and a reusable example over an expanding catalog of rules/components.
