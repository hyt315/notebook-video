---
name: notebook-video
description: Create complete Chinese 2K warm-ivory engineering-notebook explainer videos with React, TypeScript and Remotion, using a fast native-30fps pipeline, active-scene mounting, transform-based motion, deterministic timing, Chinese TTS word timing, declarative audio, H.264/AAC rendering and automated QA. Use when the user asks to 做科普视频, 手账风视频, 定格动画, AI 视频, 介绍一个概念, 讲解产品或技能, 制作 30 秒到数分钟视频, 网站动画转 MP4, 加中文配音/字幕/音效, 快速生成 2K 视频, or reproduce the established notebook-video visual style consistently without wasting render time on duplicate frames.
---

# Create notebook explainer videos

Build a finished, validated MP4 and editable Remotion project. Treat this as a low-freedom production system, not a visual prompt. Remotion is the only visual rendering engine in the current skill.

## Use the official engine first

The official default is `warm-ivory-remotion-2k30-v8-performance`.

Before changing scenes, read:

1. [references/locked-style-contract.json](references/locked-style-contract.json)
2. [references/remotion-architecture.md](references/remotion-architecture.md)
3. [references/visual-system.md](references/visual-system.md)
4. [references/official-skills-exemplar.md](references/official-skills-exemplar.md)
5. [references/performance-design.md](references/performance-design.md)

Start every project by copying `assets/example-project`; do not rebuild the engine from memory. The source project and locked contract are authoritative. Create projects in an empty directory so stale files from an earlier run cannot survive.

Keep these official elements locked until the user approves a future rendered replacement:

- React + TypeScript + Remotion rendering core;
- fixed 2560×1440 camera and native 30fps motion, render and delivery;
- no duplicate-frame upconversion; use 60fps only when motion is authored natively at 60fps;
- mount only the active scene, with at most two scenes during a short transition;
- animate moving objects with transforms instead of per-frame layout properties;
- bright layered warm-ivory notebook background;
- stable upper-left chapter card and upper-right technical header;
- clean white lower torn-wave subtitle input with no dark side artifacts;
- orange left locator, blue right status ring and centered 40px Chinese text;
- Source Han Sans CN body and Smiley Sans display emphasis;
- TTS word timing converted once to integer absolute frames;
- independent semantic parts with explicit z-order, entry and complete exit;
- a spatial density budget: one hero action per zone, no temporary stack in the center;
- shared-track continuity when one object changes state across several stations;
- real slot geometry: insertable parts cross the slot, move behind the front lip and disappear fully;
- declarative narration and action effects inside the Remotion component tree;
- font/audio asset preload gate before the first frame;
- H.264/AAC output, automated QA, contact sheets and editable source package.

Do not write an experimental change into this skill until the user sees the rendered film and explicitly approves it.


## Preserved aesthetic layer

The official example already includes the centralized palette, type scale, paper surface, lift-linked shadow, unified line icons, restrained static grade, browser-native subtitle measurement and a clearly marked `COPY` block. Ordinary production runs edit content and timing, not this aesthetic core. Read [references/official-aesthetic-system.md](references/official-aesthetic-system.md).

## Deliverables

Unless the user asks for less, deliver:

1. narration and time-coded storyboard;
2. semantic part manifest with layer and exit contracts;
3. Chinese narration plus word timing JSON;
4. one-line semantic caption cues plus a protected-phrase manifest;
5. 2560×1440 H.264/AAC MP4;
6. 24-frame contact sheet and motion checks for long films;
7. editable source ZIP with fonts, licenses, audio and manifests.

Do not stop at prompts, still images, a silent animation or an unvalidated render.

## Create a project

Use the cross-platform Node launcher. Replace `<SKILL_DIR>` with the skill directory. The same universal command works in macOS Terminal, Windows Command Prompt and Windows PowerShell. macOS/Linux may use the `.sh` aliases and Windows may use `scripts\notebook-video.cmd`; every wrapper delegates to the same Node implementation.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" check-deps
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-skill
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project ./notebook-video-project
node "<SKILL_DIR>/scripts/notebook-video.mjs" prepare-browser ./notebook-video-project
```

The copied project is the official 30-second Final Motion System project. It is the canonical proof for spacious composition, independent work zones, shared-track state changes, physical slot insertion and validated delivery. Preserve its helpers, subtitle component, background, chapter/header modules, audio tree, resource gate and final draw order. Replace topic-specific narration, copy, timings and scene objects.

## Production workflow

### 1. Lock the content

Infer known choices from the conversation. Confirm only choices that materially change the result: factual claims, platform/aspect ratio, real brand assets, CTA, voice or music.

Default to Chinese, 16:9, warm female narration, no prominent BGM and a duration appropriate to the content. Use the cold-open contract in [references/narrative-hook.md](references/narrative-hook.md): lead with a verified consequence or tension in the first 1.5 seconds, open an honest loop by 8 seconds, then return to normal explanation and later pay that loop off with evidence. Give each scene one main idea and one physical action.

Present a compact narration/storyboard before an expensive render when the topic or claims are not already approved. A direct request to continue an established series is sufficient approval to proceed.

### 2. Generate TTS and semantic captions

Default target: a clear, warm Mandarin voice at a moderately brisk rate. Select the actual provider and voice from the user's available tools and licensing needs.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" build-semantic-captions ./notebook-video-project/audio/narration.mp3.json ./notebook-video-project/manifests/semantic-caption-lines.txt ./notebook-video-project/manifests/caption-cues.json --lead-ms 60

node "<SKILL_DIR>/scripts/notebook-video.mjs" sync ./notebook-video-project
```

Read [references/subtitle-timing.md](references/subtitle-timing.md). Author the semantic lines manually from meaning and speech pauses before binding them to TTS words. Also author `manifests/protected-caption-phrases.txt`; include every product/model name, benchmark name, number-plus-unit expression, fixed technical term and short phrase whose meaning breaks if split. Character count is never allowed to choose a final caption boundary.

The repository does not bundle or install a TTS client. Use an available platform TTS, commercial API, local model or another provider that fits the user's environment. Edge Read Aloud may be mentioned only as an external reference, never assumed or installed automatically. Adapt every provider to the same `narration.mp3` and word-timing JSON contract. Never commit generated narration unless its source, voice and redistribution rights are documented. Read [references/tts-audio.md](references/tts-audio.md).

Convert milliseconds to frames once at the data boundary with `Math.round(ms * fps / 1000)`. Components compare integers only. Keep protected phrases, complete clauses and short sentence tails together.

### 3. Model independent parts and layers

Read [references/independent-parts.md](references/independent-parts.md). Every object that moves at a different time is a separate component with:

- stable ID and scene;
- layer role and numeric z-order;
- entry, active and complete-exit frames;
- motion and occlusion contracts;
- narrative reason for decorative motion.

Before animating, assign every moving object one home zone and one destination zone. Keep at least 70px visual separation between unrelated cards. Do not let more than one temporary transfer object occupy the central corridor at once. If a scene becomes crowded, enlarge and redistribute the objects or remove completed parts; never shrink everything into a pile.

Floating objects stay above lower bases. Insertable cards pass behind a front lip only after crossing a real slot. Used objects leave completely; never leave a clipped corner or hidden fragment.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-layering ./notebook-video-project/manifests/asset-manifest.json
```

### 4. Preserve the visual contract

Reuse the exact components in `assets/example-project/src/index.tsx`:

- `Background`, `Paper`;
- `Subtitle`, `Chrome`;
- `AssetGate`, `Sound`;
- stepped-frame helpers `q`, `ease`, `pop`.

Do not replace the subtitle input with a straight box, rounded search bar, dark bordered strip or inner sine line. Do not add global camera motion, random drift, animated noise, heavy blur or unrelated particles.

### 5. Animate progressively

Read [references/motion-design.md](references/motion-design.md) and, for the opening, [references/narrative-hook.md](references/narrative-hook.md). Build each scene in this order:

1. chapter and hero;
2. three to seven supporting semantic parts;
3. relationship path or physical transfer;
4. local feedback;
5. readable hold;
6. complete exit for obsolete parts.

For a process explanation, prefer one persistent task object moving through a shared track and changing state over spawning a new card at every step. Reuse a track only while the metaphor remains the same. When the metaphor changes, clear the old scene completely before the next one enters.

Add a meaningful state change every 2–4 seconds. Use dynamic shadow only when a paper object lifts: farther/softer while airborne, closer/darker on landing. Use one restrained overshoot. Move SVG dash offsets only while data is transferring.

### 6. Keep audio declarative

Read [references/tts-audio.md](references/tts-audio.md). Put narration and action effects in the Remotion tree with `<Audio>` and frame-based `<Sequence>`. Preview the real mix before export.

Use effects only on visible actions. Keep speech primary. Do not add an untracked narration delay. Use FFmpeg after render only for encoding, loudness normalization and validation, not for inventing the timeline.

### 7. Preload assets

Keep `AssetGate` active. Wait for `document.fonts.ready` and all audio/image assets before `continueRender()`. Never remove the gate to make a render start faster.

### 8. Render and normalize

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" render ./notebook-video-project ./notebook-video-project/renders/final.mp4
```

The launcher runs `npm ci` automatically when dependencies are absent. It resolves macOS and Windows paths, invokes the pinned Remotion CLI through Node and uses the same render arguments on both systems. `prepare-browser` may be run once after project creation; restricted environments may provide an exact browser path through `REMOTION_BROWSER_EXECUTABLE`.

Render the composition at 2560×1440 and 30fps. Keep motion, Remotion rendering and final delivery at the same rate. Do not render 30 unique poses into a 60fps duplicate-frame container: it doubles browser work without adding smoothness. Keep the 1920×1080 design coordinate system inside a native 2K composition and scale it by 4/3 so CSS, SVG and text rasterize at delivery resolution. Normalize to about -16 LUFS with a true peak no higher than -1.5dBTP, 48kHz stereo AAC. Preserve video duration and add `faststart`.

Run a short concurrency benchmark once on a new machine, then reuse its recommendation:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" benchmark-render ./notebook-video-project
```

During iteration, render only the changed scene range for review. Frame numbers are native 30fps frames. Always make one full render for final delivery. If the narration requires a longer delivery than the canonical 900-frame timeline, read the **Duration extension invariant** in [references/remotion-architecture.md](references/remotion-architecture.md) before editing: scene guards, motion and action-audio must share the same scaled design-time helper, then range-render every scene boundary before the full render.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" render-range ./notebook-video-project ./notebook-video-project/renders/scene-review.mp4 START_FRAME END_FRAME
```

### 9. Validate the actual result

Read [references/quality-checklist.md](references/quality-checklist.md).

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-video ./notebook-video-project/renders/final.mp4 EXPECTED_SECONDS ./notebook-video-project/renders/contact-sheet.jpg

# Subtitle width is measured inside the real Remotion browser by CaptionFitGate
# after the exact bundled font loads. The 4/3 delivery scale is converted back
# to design pixels before comparison with the locked 1334px safe width.

node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-caption-sync ./notebook-video-project/audio/narration.mp3.json ./notebook-video-project/manifests/caption-cues.json

node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-semantic-breaks ./notebook-video-project/manifests/caption-cues.json ./notebook-video-project/manifests/protected-caption-phrases.txt
```

Inspect the opening, every scene boundary, longest caption, every hover/insert midpoint and final frame. For films over 60 seconds, inspect a 24-frame sheet plus at least two dense motion sheets covering the most complex movements. The opening also needs a 0–360-frame range render and the cold-open review gate from [references/narrative-hook.md](references/narrative-hook.md).

Reject any render containing black frames, subtitle overflow, a protected phrase split across cues, mechanically character-counted captions, dark side marks on the subtitle, missing fonts, half-visible exited objects, incorrect stacking, static data lines during transfer or action sounds without visible actions.

### 10. Package

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" package ./notebook-video-project ./notebook-video-project-source.zip
```

Include narration, timing JSON, source, manifests, chosen audio, fonts and licenses. Exclude `node_modules`, caches, temporary frames, unused voices and secrets.

## Resource map

- [references/locked-style-contract.json](references/locked-style-contract.json): binding tokens, coordinates and rejection flags.
- [references/official-aesthetic-system.md](references/official-aesthetic-system.md): locked aesthetic core and ordinary editable surface.
- [references/remotion-architecture.md](references/remotion-architecture.md): project structure, data flow and component contracts.
- [references/official-skills-exemplar.md](references/official-skills-exemplar.md): canonical project and reuse rules.
- [references/visual-system.md](references/visual-system.md): exact background, cards, subtitle and typography.
- [references/independent-parts.md](references/independent-parts.md): decomposition, stacking and exit rules.
- [references/motion-design.md](references/motion-design.md): motion curves and scene rhythm.
- [references/narrative-hook.md](references/narrative-hook.md): binding cold-open, callback and opening review rules.
- [references/subtitle-timing.md](references/subtitle-timing.md): semantic captions and integer-frame conversion.
- [references/tts-audio.md](references/tts-audio.md): TTS, declarative effects and mix.
- [references/quality-checklist.md](references/quality-checklist.md): delivery acceptance criteria.
- [references/performance-design.md](references/performance-design.md): binding 30fps pipeline, scene lifetime, transform, caching, concurrency and range-render rules.
- [references/cross-platform-compatibility.md](references/cross-platform-compatibility.md): binding macOS/Windows parity contract, universal commands and browser preparation.
- [references/windows-compatibility.md](references/windows-compatibility.md): additional Windows setup, path rules and troubleshooting without changing render output.
