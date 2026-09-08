---
name: notebook-video
version: 2.8.0
description: Create complete Chinese 2K warm-ivory engineering-notebook explainer and promotional videos with React, TypeScript and Remotion. The default visual route is lecture composition: multi-zone scenes drawn entirely with code (SVG diagrams, mascots, progressive checklists, annotation stickers) synchronized frame-accurately to Chinese TTS word timing, so production never depends on an image-generation model; image generation is an optional add-on offered to the user for concrete hero scenes. Includes native-30fps motion, active-scene mounting, complete exits, declarative audio, H.264/AAC rendering, provenance manifests and automated QA. Use when the user asks to 做科普视频, 手账风视频, 定格动画, AI 视频, 产品宣传片, 介绍一个概念, 讲解产品或技能, 制作 30 秒到数分钟视频, 网站动画转 MP4, 加中文配音/字幕/音效, 快速生成 2K 视频, or combine animated text and diagrams without producing a moving slide deck.
---

# Create notebook explainer videos

Build a finished, validated MP4 and editable Remotion project. Treat this as a low-freedom production system, not a visual prompt. Remotion is the only visual rendering engine in the current skill.

**Default visual route: lecture composition.** Every scene is drawn with code (SVG + rich synchronized text), so any AI in any environment can reproduce the established style without an image-generation model — read [references/lecture-composition.md](references/lecture-composition.md), [references/motion-design.md](references/motion-design.md) and [references/visual-system.md](references/visual-system.md) before directing scenes. Image generation is an optional add-on: ask the user once whether they want generated support art for concrete hero scenes, and only then use it for that subset.

## Use the official engine first

The official default is `warm-ivory-remotion-2k30-v9-visual-director`.

Before changing scenes, read:

1. [references/locked-style-contract.json](references/locked-style-contract.json)
2. [references/remotion-architecture.md](references/remotion-architecture.md)
3. [references/visual-system.md](references/visual-system.md)
4. [references/lecture-composition.md](references/lecture-composition.md)
5. [references/official-skills-exemplar.md](references/official-skills-exemplar.md)
6. [references/performance-design.md](references/performance-design.md)
7. [references/visual-director.md](references/visual-director.md)

Start every project by copying a bundled template through `new-project`; do not rebuild the engine from memory. The default copy is `assets/lecture-template` (pure code-drawn lecture route); `--classic` copies `assets/example-project`, the visual-director exemplar whose hero scene demonstrates the optional image add-on. The source projects and locked contract are authoritative. Create projects in an empty directory so stale files from an earlier run cannot survive.

**Theme selection.** The lecture template ships four locked skins selected once at kickoff: `paper` (default warm-ivory notebook), `cel` (anime cel-shading storyboard), `sticker` (cartoon sticker journal) and `flat` (modern flat geometric). Pass `--style=<id>` to `new-project` and read only that theme's contract afterwards — [references/theme-system.md](references/theme-system.md) explains the boundary, and each theme doc is mutually exclusive by design so an A×16:9 production never loads the other skins' rules. Themes swap palette, card skin, background decoration and subtitle chrome only; every layout coordinate, type scale, motion contract and QA gate is shared and unchanged.

Keep these official elements locked until the user approves a future rendered replacement:

- React + TypeScript + Remotion rendering core;

- locked premium motion contracts shipped in the template and carried into every new production: CameraRig dual-canvas lag camera, JumpInText per-glyph 3D flip titles, WaveText letter-wave CTA typing, multi-keyframe figure roll-ins and per-word subtitle reveal (see references/motion-design.md);

- fixed native 30fps motion, render and delivery on one of three locked canvases: 2560×1440 (16:9), 1920×1440 (4:3) or 1440×1920 (3:4 portrait), chosen once at kickoff;

- no duplicate-frame upconversion; use 60fps only when motion is authored natively at 60fps;

- mount only the active scene, with at most two scenes during a short transition;

- animate moving objects with transforms instead of per-frame layout properties;

- bright layered warm-ivory notebook background;

- stable upper-left chapter card and upper-right technical header;

- bottom-pinned pure caption text with per-word reveal, no decorative bar, no dark border or side artifacts;

- pure bottom subtitle with soft text shadow, no dark border, side marks, locator or ring;

- LXGW WenKai Lite as the unified CJK typeface plus Clash Display / Space Grotesk Latin accents;

- TTS word timing converted once to integer absolute frames;

- independent semantic parts with explicit z-order, entry and complete exit;

- a spatial density budget: one hero action per zone, no temporary stack in the center;

- shared-track continuity when one object changes state across several stations;

- real slot geometry: insertable parts cross the slot, move behind the front lip and disappear fully;

- declarative narration and action effects inside the Remotion component tree;

- font/audio/image asset preload gate before the first frame;

- a visual plan selecting lecture-route pure text/graphic scenes by default, with image-plus-text only after the user accepts the add-on;

- optional generated imagery as preloaded Remotion assets with prompt, crop and rights records;

- H.264/AAC output, automated QA, contact sheets and editable source package.

Do not write an experimental change into this skill until the user sees the rendered film and explicitly approves it.

## Execution discipline and safety (Zero-Mutation 原则)

执行纪律与安全约束（Zero-Mutation 原则）：脚本检测与视觉审查恪守纯只读排查原则，绝不擅自变动系统配置；对于完整渲染（render）、依赖安装或大构架重写等治理对策，须用户明确授权后方可执行。

## Preserved aesthetic layer

The official example already includes the centralized palette, type scale, paper surface, lift-linked shadow, unified line icons, restrained static grade, browser-native subtitle measurement and a clearly marked `COPY` block. Ordinary production runs edit content and timing, not this aesthetic core. Read [references/official-aesthetic-system.md](references/official-aesthetic-system.md).

## Deliverables

Unless the user asks for less, deliver:

1. narration and time-coded storyboard;
2. a visual plan identifying each scene as `image-text`, `pure-text` or `pure-graphic`;
3. semantic part manifest with layer and exit contracts;
4. `visual-assets.json` with source, prompt summary, crop policy and rights for every raster;
5. Chinese narration plus word timing JSON;
6. one-line semantic caption cues plus a protected-phrase manifest;
7. delivery-canvas H.264/AAC MP4 (2560×1440 or 1920×1440);
8. 24-frame contact sheet and motion checks for long films;
9. editable source ZIP with fonts, licenses, audio and manifests;
10. delivery fact card verified against the baseline table below.

### 交付指标事实卡 (Fact Card)

| 层级 | 检查项 (Metric/Item) | 测量实值 (Value) | 正常基线 (Baseline) | 状态判定 (Status) |
|---|---|---|---|:---:|
| L1 基础层 | 交付画幅与帧率 | 2560×1440 / 1920×1440 | 锁定 30fps 原生无重复帧 | 🟢 正常 |
| L1 基础层 | 响度与音频混音 | -16 LUFS / -1.5 dBTP | 48kHz 立体声 AAC | 🟢 正常 |
| L2 核心层 | 字幕与台词对齐 | 词级整帧同步 (msFrame) | 零断行拆分/零边缘伪影 | 🟢 正常 |
| L3 校验层 | 黑帧与图层穿透 | 0 处黑帧 / 零残留碎片 | 所有元件完整离场与遮挡 | 🟢 正常 |

Do not stop at prompts, still images, a silent animation or an unvalidated render.

## Create a project

Use the cross-platform Node launcher. Replace `<SKILL_DIR>` with the skill directory. The same universal command works in macOS Terminal, Windows Command Prompt and Windows PowerShell. macOS/Linux may use the `.sh` aliases and Windows may use `scripts\notebook-video.cmd`; every wrapper delegates to the same Node implementation. Python 辅助脚本（`scripts/*.py`）严格基于 Python 3.10+ 标准库实现，零第三方 pip 依赖 / zero external python dependencies.

The underlying scripts in `scripts/`:
- `scripts/notebook-video.mjs`: cross-platform CLI implementation;
- `scripts/notebook-video.cmd`: Windows Command Prompt launcher;
- `scripts/new-project.cmd` / `new-project.sh` (shell alias): project initialization;
- `scripts/prepare-browser.sh` / `scripts/prepare-browser.cmd`: Remotion headless browser preparation;
- `scripts/check-deps.sh` / `scripts/check-deps.cmd`: environment dependency checker;
- `scripts/sync-project-assets.sh` / `scripts/sync-project-assets.cmd`: sync project assets and manifest;
- `scripts/render-remotion.sh` / `scripts/render-remotion.cmd`: Remotion render pipeline invocation;
- `scripts/validate-video.sh` / `scripts/validate-video.cmd`: video delivery validation;
- `scripts/package-project.sh` / `scripts/package-project.cmd` / `scripts/package-project.py`: package project for export;
- `scripts/build-semantic-captions.py`: semantic line break and cue builder;
- `scripts/match-timing.py`: automated speech timing alignment;
- `scripts/validate-visual-plan.py`: visual plan validation;
- `scripts/validate-layering.py`: asset layering and z-order validation;
- `scripts/validate-caption-sync.py`: caption word timing synchronization check;
- `scripts/validate-semantic-breaks.py`: protected phrase and cue break validation;
- `scripts/validate-official-example.py`: official example and style contract validation;
- `scripts/validate-skill-consistency.py`: dual-template and repository-wide consistency gate;
- `scripts/selftest.py`: end-to-end regression test suite.

All Python checkers and shell wrappers are invoked through `scripts/notebook-video.mjs` (or run directly for QA/selftest).

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" check-deps
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-skill
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project ./notebook-video-project --style=cel
node "<SKILL_DIR>/scripts/notebook-video.mjs" prepare-browser ./notebook-video-project
```

The default copy is the lecture template: a validated 30-second film whose source is layered into a locked core, a reusable component library (paper cards, mascot, icons, checklists, rails, gauges) and a clearly marked content layer to rewrite per topic. It is the canonical proof for multi-zone lecture composition, frame-accurate speech sync, demonstrative animation and series component reuse. `new-project ./dir --classic` instead copies the original 30-second Visual Director exemplar (image-plus-text callouts and physical slot insertion) for productions that accepted the image add-on. In both cases preserve the helpers, subtitle component, background, chapter/header modules, audio tree, resource gates and final draw order; replace topic-specific narration, copy, timings, imagery and scene objects.

## Production workflow

### 1. Lock the content

Infer known choices from the conversation. Confirm only choices that materially change the result: factual claims, platform/aspect ratio, real brand assets, CTA, voice or music.

Ask the user once at kickoff which canvas mode this production uses: **16:9** (default, landscape players), **4:3** (taller mobile presence) or **3:4 portrait** (native for portrait feeds such as Douyin), and which theme skin: **paper** (default warm-ivory), **cel** (anime cel-shading), **sticker** (cartoon sticker journal) or **flat** (modern flat geometric). Both answers are passed to `new-project` (`--style=<id>`) and decide every skin decision; read only the selected theme's contract in [references/theme-cel.md](references/theme-cel.md), [references/theme-sticker.md](references/theme-sticker.md) or [references/theme-flat.md](references/theme-flat.md) (the paper default keeps [references/visual-system.md](references/visual-system.md)). The canvas answer decides every layout coordinate; read [references/canvas-modes.md](references/canvas-modes.md) for the parameter table shared by both modes. On **3:4 portrait** also read [references/portrait-illustration-system.md](references/portrait-illustration-system.md): the illustration is the hero, in-scene text is a short label (full narration lives in the subtitle strip), and a persistent faint ambient layer plus a code-drawn figure cast, highlighter markers and contrast labels keep the tall frame from reading empty.

Default to Chinese, warm female narration, no prominent BGM and a duration appropriate to the content. Use the cold-open contract in [references/narrative-hook.md](references/narrative-hook.md): lead with a verified consequence or tension in the first 1.5 seconds, open an honest loop by 8 seconds, then return to normal explanation and later pay that loop off with evidence. Plan the film's energy curve with [references/pacing-rhythm.md](references/pacing-rhythm.md): hammer frames, fast/slow chapter alternation, chapter breathing and a sparse ending beat. Give each scene one main idea and one physical action.

Before writing the storyboard, assign one provisional visual mode to every planned scene along the default lecture route, and ask the user once whether they want the optional image-generation add-on for concrete hero scenes. Include the modes in the compact narration/storyboard presented before an expensive render when the topic or claims are not already approved. A direct request to continue an established series is sufficient approval to proceed.

### 2. Direct the visuals

Read [references/lecture-composition.md](references/lecture-composition.md) first; it defines the default route (multi-zone scenes, code-drawn graphics, cue-frame sync, demonstrative animation). Then read [references/visual-director.md](references/visual-director.md) for mode selection details. Before implementing scenes, write a compact visual plan with scene ID, time range, narration purpose, primary mode and complete-exit frame.

Choose the mode from meaning:

- process, system, quantity or relationship → `pure-graphic` (default for explanations);

- contrast, slogan, misconception or keyword → `pure-text`;

- concrete subject, environment or transformation → `pure-graphic` on the default route, or `image-text` only when the user accepted the image add-on.

The add-on question is asked once per production: some environments have no image model and many have weak ones, so generated art is an enhancement the user opts into, never a requirement that blocks production. When offering it, state plainly that the result depends on the image-generation quality of the current tool, and that the built-in image generation in Codex is the best-suited environment for this add-on. When accepted and available, generate bitmaps without baked labels, charts or UI text; request crop-safe negative space and separated subjects; put exact Chinese copy, arrows, highlights and diagrams in Remotion. Copy only used images into `public/illustrations/`, register them in `assets/lecture-template/manifests/visual-assets.json`, preload them in `AssetGate`, and animate them with a restrained reveal or push-in plus phrase-timed annotations. On the default route `visual-assets.json` stays empty.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-visual-plan ./notebook-video-project
```

### 3. Generate TTS and semantic captions

Default target: a clear, warm Mandarin voice at a moderately brisk rate. Select the actual provider and voice from the user's available tools and licensing needs.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" build-semantic-captions ./notebook-video-project/audio/narration.mp3.json ./notebook-video-project/manifests/semantic-caption-lines.txt ./notebook-video-project/manifests/caption-cues.json --lead-ms 60

node "<SKILL_DIR>/scripts/notebook-video.mjs" sync ./notebook-video-project
```

Read [references/subtitle-timing.md](references/subtitle-timing.md). Author the semantic lines manually from meaning and speech pauses before binding them to TTS words. Also author `assets/lecture-template/manifests/protected-caption-phrases.txt`; include every product/model name, benchmark name, number-plus-unit expression, fixed technical term and short phrase whose meaning breaks if split. Character count is never allowed to choose a final caption boundary.

Rewrite easily-misread polyphones (多音字) into reading-unambiguous synonyms directly in the narration source (e.g. 重装→重新装, 输一行命令→输入一条命令, 一模一样→长得一样) and mirror the edit into the caption lines: the TTS path has no reliable pinyin/SSML channel and `narration.txt` doubles as the subtitle text, so a wrong reading can only be prevented at the source. See [references/tts-audio.md](references/tts-audio.md).

The repository does not bundle or install a TTS client. Use an available platform TTS, commercial API, local model or another provider that fits the user's environment. The lecture template ships `assets/lecture-template/scripts/tts-openai-compatible.py`, a provider-neutral chapter-segmented adapter for any OpenAI-compatible chat TTS endpoint (configured only through `TTS_API_BASE`/`TTS_API_KEY`/`TTS_MODEL` environment variables); it measures each paragraph's real duration so chapter boundaries and scene cuts never drift, and writes `chapters.json` with exact chapter frames (into the project `manifests/` folder). When no such endpoint is selected, prefer Microsoft Edge Read Aloud as the zero-key adapter when it is reachable and its terms fit the intended use. Do not hardcode a proxy. Adapt every provider to the same `narration.mp3` and word-timing JSON contract. Never commit generated narration unless its source, voice and redistribution rights are documented. Read [references/tts-audio.md](references/tts-audio.md).

Convert milliseconds to frames once at the data boundary with `Math.round(ms * fps / 1000)`. Components compare integers only. Keep protected phrases, complete clauses and short sentence tails together.

**Subtitle Trailing Punctuation Strip Invariant**: Chinese and English sentence-final punctuation marks (`，。！？；、,.!?;:`) must be strictly stripped from the end of subtitle display lines. The Subtitle component in `index.tsx` enforces `cue.full.replace(/[，。！？；、,.!?;:\s]+$/, '')` as `cleanFull` and gates progressive character sequence rendering against `targetChars.length`. Trailing punctuation marks in the final rendered subtitle strip are strictly forbidden and constitute an immediate QA rejection flag.

### 4. Model independent parts and layers

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

### 5. Preserve the visual contract

Reuse the exact components in the copied template (`assets/lecture-template/src/index.tsx`, or `assets/example-project/src/index.tsx` with `--classic`):

- `Background`, `Paper`;

- `Subtitle`, `Chrome`;

- `AssetGate`, `Sound`;

- the code-drawn component library (`Mascot`, `LineIcon` (26 locked glyphs), `CheckBadge`, `PillTag`, `CodeBlock`, `BrowserChrome`, `Connector`, `Checklist`, `CountUp`, `ProgressBar`, `Callout`, `Gauge`, `StepRail`, plus the 6 anti-PPT interactive components: `BrainwaveEEG`, `VectorRadarSonar`, `BM25TokenRibbon`, `HookMountBay`, `RedactionScanner`, `ChipContract`, plus the fxkit motion kit in `assets/lecture-template/src/fxkit.tsx` (see [references/fxkit.md](references/fxkit.md): `FitCard`/`fitH`, `Typewriter`, `PayPop`, `StampSeal`, `Funnel`, `ChatThread`, `MailScan`, `TimeRail`, `CompareBars`, `ProgressRing`, `ShakeX`, `BurstCallout`, `StaggerList`, `KenBurnsImg`, `EvidenceZoom`, `DiffView`, `ConfettiPop`, `SkeletonCard`)) or, on the classic route, generated `Img` layers and their independent callouts;

- stepped-frame helpers `q`, `ease`, `pop`, plus the motion pack: `SPRINGS`/`popS` spring presets (snappy/soft/bouncy), `TransitionIn` scene transitions (flip/slide/wipe), `camScript` camera-track builder and `useSteppedFrame` stop-motion accent.

Do not replace the subtitle input with a straight box, rounded search bar, dark bordered strip or inner sine line. Do not add global camera motion, random drift, animated noise, heavy blur or unrelated particles.

### 6. Animate progressively

Read [references/motion-design.md](references/motion-design.md) and, for the opening, [references/narrative-hook.md](references/narrative-hook.md). Build each scene in this order:

1. chapter and hero;
2. three to seven supporting semantic parts;
3. relationship path or physical transfer;
4. local feedback;
5. readable hold;
6. complete exit for obsolete parts.

For a process explanation, prefer one persistent task object moving through a shared track and changing state over spawning a new card at every step. Reuse a track only while the metaphor remains the same. When the metaphor changes, clear the old scene completely before the next one enters.

Add a meaningful state change every 2–4 seconds. Use dynamic shadow only when a paper object lifts: farther/softer while airborne, closer/darker on landing. Use one restrained overshoot. Move SVG dash offsets only while data is transferring.

**Camera Micro-Framing Invariant**: The virtual camera coordinate $X$ must remain strictly within $[945, 975]$ (maximum $\pm 15\text{px}$ displacement from the 960px center), and camera scale $S$ within $[1.00, 1.018]$. Large camera pans ($> 30\text{px}$) that displace the active narrative content or push cards off-screen are strictly forbidden and constitute a critical QA rejection.

**Anti-PPT Functional Component Invariant**: Pure static card stacks ("a box with bullets") are forbidden for complex mechanisms. Technical concepts (search, memory, context, contracts, embeddings, security) MUST use active, purpose-built animated components (e.g. `BrainwaveEEG`, `VectorRadarSonar`, `BM25TokenRibbon`, `HookMountBay`, `RedactionScanner`, `ChipContract`) rather than generic text boxes.

### 7. Keep audio declarative

Read [references/tts-audio.md](references/tts-audio.md). Put narration and action effects in the Remotion tree with `<Audio>` and frame-based `<Sequence>`. Preview the real mix before export.

Use effects only on visible actions. Keep speech primary. Do not add an untracked narration delay. Use FFmpeg after render only for encoding, loudness normalization and validation, not for inventing the timeline.

### 8. Preload assets

Keep `AssetGate` active. Wait for `document.fonts.ready` and all audio/image assets before `continueRender()`. Register every raster in `assets/lecture-template/manifests/visual-assets.json`; unused generations do not belong in the project. Never remove the gate to make a render start faster.

### 9. Render and normalize

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" render ./notebook-video-project ./notebook-video-project/renders/final.mp4
```

The launcher runs `npm ci` automatically when dependencies are absent. It resolves macOS and Windows paths, invokes the pinned Remotion CLI through Node and uses the same render arguments on both systems. `prepare-browser` may be run once after project creation; restricted environments may provide an exact browser path through `REMOTION_BROWSER_EXECUTABLE`.

Render the composition at the kickoff canvas (2560×1440 for 16:9, 1920×1440 for 4:3, 1440×1920 for 3:4 portrait) and 30fps. Keep motion, Remotion rendering and final delivery at the same rate. Do not render 30 unique poses into a 60fps duplicate-frame container: it doubles browser work without adding smoothness. Keep the design coordinate system (1920×1080 or 1440×1080) inside the native composition and scale it by 4/3 so CSS, SVG and text rasterize at delivery resolution. Normalize to about -16 LUFS with a true peak no higher than -1.5dBTP, 48kHz stereo AAC. Preserve video duration and add `faststart`.

Run a short concurrency benchmark once on a new machine, then reuse its recommendation:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" benchmark-render ./notebook-video-project
```

During iteration, render only the changed scene range for review. Frame numbers are native 30fps frames. Always make one full render for final delivery. If the narration requires a longer delivery than the canonical 900-frame timeline, read the **Duration extension invariant** in [references/remotion-architecture.md](references/remotion-architecture.md) before editing: scene guards, motion and action-audio must share the same scaled design-time helper, then range-render every scene boundary before the full render.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" render-range ./notebook-video-project ./notebook-video-project/renders/scene-review.mp4 START_FRAME END_FRAME
```

For multi-frame visual checks, prefer a single range render over several single stills: one bundle + one browser launch serves the whole range, and measured 4-frame checks drop from \~13s (four serial stills) to \~4s. The dedicated compound command additionally writes a contact sheet in the same call, so inspect the mp4 frame-by-frame and the jpg in one pass:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" review-frames ./notebook-video-project ./notebook-video-project/renders/scene-review.mp4 START_FRAME END_FRAME
```

### 10. Validate the actual result

Read [references/quality-checklist.md](references/quality-checklist.md).

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-video ./notebook-video-project/renders/final.mp4 EXPECTED_SECONDS ./notebook-video-project/renders/contact-sheet.jpg

# Subtitle width is measured inside the real Remotion browser by CaptionFitGate
# after the exact bundled font loads. The 4/3 delivery scale is converted back
# to design pixels before comparison with the locked safe width
# (1334px on 16:9, 1060px on 4:3, 900px on 3:4 portrait).

node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-caption-sync ./notebook-video-project/audio/narration.mp3.json ./notebook-video-project/manifests/caption-cues.json

node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-semantic-breaks ./notebook-video-project/manifests/caption-cues.json ./notebook-video-project/manifests/protected-caption-phrases.txt

node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-visual-plan ./notebook-video-project
```

Inspect the opening, every scene boundary, longest caption, every hover/insert midpoint and final frame. For films over 60 seconds, inspect a 24-frame sheet plus at least two dense motion sheets covering the most complex movements. The opening also needs a 0–360-frame range render and the cold-open review gate from [references/narrative-hook.md](references/narrative-hook.md).

Reject any render containing black frames, subtitle overflow, a protected phrase split across cues, mechanically character-counted captions, dark side marks on the subtitle, missing fonts, half-visible exited objects, incorrect stacking, static data lines during transfer, action sounds without visible actions, unregistered raster assets, generated text baked into imagery or a static image-card sequence that does not synchronize image, annotation and narration.

### 11. Package

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" package ./notebook-video-project ./notebook-video-project-source.zip
```

Include narration, timing JSON, source, manifests, chosen audio, fonts and licenses. Exclude `node_modules`, caches, temporary frames, unused voices and secrets.

## Regression self-test

After any change to the engine, template, QA scripts or reference docs, run the bundled regression self-test. Good fixtures must pass and each broken fixture (protected phrase split across cues, mismatched caption sync, non-video input) must be rejected by the matching gate:

```text
python "<SKILL_DIR>/scripts/selftest.py"
```

## Reference Files (按需加载与行动指引)

- [references/locked-style-contract.json](references/locked-style-contract.json): 渲染引擎契约，定义 binding tokens, coordinates and rejection flags.
- [references/theme-system.md](references/theme-system.md): 选定主题时必读，定义 theme boundary 与四套锁定主题（paper/cel/sticker/flat）.
- [references/theme-cel.md](references/theme-cel.md): 当选用 cel 皮肤时必读其专属色彩与图层契约.
- [references/theme-sticker.md](references/theme-sticker.md): 当选用 sticker 皮肤时必读其专属贴纸边缘与阴影契约.
- [references/theme-flat.md](references/theme-flat.md): 当选用 flat 皮肤时必读其扁平几何与色块契约.
- [references/lecture-composition.md](references/lecture-composition.md): 制作讲解视频默认必读，包含多区域纯代码 SVG 构图、台词帧对齐与自检清单.
- [references/official-aesthetic-system.md](references/official-aesthetic-system.md): 调整画面风格前必读，定义暖象牙色锁定美学核心与普通编辑面.
- [references/remotion-architecture.md](references/remotion-architecture.md): 编写组件或调整时长前必读，定义项目结构、数据流与生命周期契约.
- [references/official-skills-exemplar.md](references/official-skills-exemplar.md): 组装工程时必读，定义官方示例项目规范与复用规则.
- [references/visual-system.md](references/visual-system.md): 绘制卡片与排版时必读，定义纸张质感、字阶与字幕坐标.
- [references/independent-parts.md](references/independent-parts.md): 拆解动态元件时必读，定义独立部件分解、z-order 与进出场规则.
- [references/motion-design.md](references/motion-design.md): 设定动效时必读，定义缓动曲线、图层进出节奏与镜头位移.
- [references/narrative-hook.md](references/narrative-hook.md): 策划脚本时必读，定义 1.5 秒黄金开场 hook、悬念与首屏评审门.
- [references/pacing-rhythm.md](references/pacing-rhythm.md): 编排章节时必读，定义全片重锤帧（Hammer frames）与快慢章节交替.
- [references/canvas-modes.md](references/canvas-modes.md): 确定画幅时必读，定义 16:9, 4:3 与 3:4 竖屏画布参数与字阶底线.
- [references/portrait-illustration-system.md](references/portrait-illustration-system.md): 制作 3:4 竖屏讲解视频时必读，定义竖屏插画主体、微环境与排版底线.
- [references/subtitle-timing.md](references/subtitle-timing.md): 切分台词时必读，定义语义字幕断行、保护短语与整帧对齐.
- [references/tts-audio.md](references/tts-audio.md): 合成配音时必读，定义 TTS 适配器、声明式音效与响度混音.
- [references/quality-checklist.md](references/quality-checklist.md): 交付成片前必读，逐条核对零黑帧、无溢出、无伪影的验收清单.
- [references/performance-design.md](references/performance-design.md): 优化渲染时必读，定义 30fps 原生管线、缓存、并发与局部试渲染.
- [references/visual-director.md](references/visual-director.md): 选用可选生图时必读，定义视觉模式决策、生图提示词与出场契约.
- [references/cross-platform-compatibility.md](references/cross-platform-compatibility.md): 跨平台运行时必读，定义 macOS/Windows 命令对齐与浏览器就绪.
- [references/windows-compatibility.md](references/windows-compatibility.md): 在 Windows 下遇到环境异常时必读排错指引.

