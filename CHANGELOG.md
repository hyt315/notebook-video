# Changelog

All notable changes are recorded here. The project follows semantic versioning.

## [2.4.0] - 2026-09-05

### Changed

- **Theme backgrounds switched to locked fixed raster assets (主题背景改为固定资产图)**: `cel` / `sticker` / `flat` now render one AI-generated background image per canvas ratio instead of code-drawn SVG decorations — 9 pixel-exact JPEGs (`public/bg-<theme>-<169|43|34>.jpg`, 2560×1440 / 1920×1440 / 1440×1920) auto-selected via `useCanvas()`. The images carry the full background language (cel: aged paper + halftone + burst star + speed lines; sticker: mint grid paper + corner doodles + washi tape; flat: peeking geometric monsters on grained gray-blue paper). The retired SVG background code is deleted; the `paper` default theme stays code-drawn and untouched. All 9 assets are registered in `manifests/visual-assets.json` with sha256 provenance, and the three theme contracts now record the fixed-raster rule with "never restore the SVG background" rejection flags.

## [2.3.0] - 2026-09-05

### Changed

- **Per-theme color systems re-derived on locked S/L steps (三主题配色同阶梯重推导)**: every accent now sits on one saturation/lightness step under a single lead hue per theme — `cel` keeps blue+red co-leads (S≈80/L≈54) with green `#24bc6e` and gold `#f2b721` lifted onto the step; `sticker` keeps the pink lead and lifts blue `#5ca9e0` / green `#61d188` into the pastel band; `flat` keeps the indigo lead with coral `#f05f42`, mint `#41d27b` and sun `#f0c63c` derived underneath. Theme contracts record the step rule with a "no off-step colors" flag.
- **`flat` redesign: geometric little monsters (几何小怪兽)** replaces the mega-circle + Memphis set: a locked indigo blob monster (bottom-right) and a coral square monster (bottom-left, −8° tilt) with star / exclamation / squiggle props; the chapter header switches to dark ink on the pale base (the white-on-circle pairing is gone with the circle).
- **`flat` card & subtitle**: cards drop the 3.5px ink border + white inset liner for a 2px neutral gray hairline plus a colored offset solid shadow (indigo by default, follows the scene's semantic accent color); the full-width ink subtitle bar becomes a floating indigo pill with hard offset ink shadow and coral/mint dots.

### Fixed

- **Invisible frames on non-default themes**: example/annotation boxes across `cel`/`sticker`/`flat` used hairlines at 0.11–0.18 alpha and fills at 0.08–0.10 alpha that melted into the cards; line tokens now start at 0.42–0.45 alpha and light fills at 0.17–0.30. `sticker` cards gain a 2.5px soft-brown print edge plus a deepened two-layer shadow so the white die-cut edge stays readable on the mint page. `paper` (default) is untouched and renders byte-identical.

## [2.2.0] - 2026-09-05

### Added

- **Theme pack system (四主题皮肤体系)**: the lecture template's locked aesthetic core is now a pluggable skin behind a one-line `src/theme/active.ts` switch, selected at kickoff via `new-project ./dir --style=<id>` and enforced per-theme by contract docs and QA gates. Layout coordinates, type scale, motion contracts and validators are shared and unchanged; themes swap palette, card skin, background decoration, grade and subtitle chrome only. Progressive disclosure preserved: a production reads exactly one theme contract.
  - *`paper` (default)*: the original warm-ivory notebook, byte-identical rendering (SSIM 1.0 regression on frames 100/300/550/900).
  - *`cel` (动漫赛璐璐·分镜风)*: near-white base, 5px ink borders with hard offset shadows, deterministic ±1° panel tilt, halftone dots and speed lines, boxed ink subtitle, locked `Burst` explosion-sticker extra.
  - *`sticker` (卡通贴纸·手账风)*: pale mint grid paper, white-outlined sticker cards, hand-drawn doodles, washi-tape subtitle chip, locked `Tape` extra.
  - *`flat` (现代扁平·几何风)*: cool gray-blue base, indigo mega-circle, Memphis accents, thick ink borders with white inset liner, solid ink subtitle bar with dual accent ticks.
- **Scene soft-color tokens**: ~20 previously hardcoded scene colors (globe tint, branch lines, merge dots, idle fills, chapter-number gradient, CTA wave start, gauge tracks, check glow, stage tint, header pair) now route through 13 mandatory `ThemePalette` tokens; every theme ships its own set with `paper` keeping pixel-identical historical values.
- **Theme docs & gates**: `references/theme-system.md` plus per-theme contracts (`theme-cel.md`, `theme-sticker.md`, `theme-flat.md`) written as locked checklists with rejection flags; `validate-skill` verifies the theme pack integrity and a paper-defaulting switch; `selftest` grows to 9 checks including illegal `--style` rejection without polluting the target directory.
- **Single 16:9 demo in sticker skin**: the bundled demo asset is now one 16:9 (2560×1440) full-film rendered in the `sticker` theme, replacing the old three-canvas demo set; `assets/demo/demo-43/34` files and README ratio matrix rows are removed accordingly.

## [2.1.1] - 2026-09-03

### Added

- **Re-voicing workflow (`scripts/match-timing.py`)**: when the narration text is locked but the voice (or model) changes, snapshot the approved `manifests/chapters.json` with `--lock`, then align the new synthesis back to it — per-chapter pitch-preserving `atempo`, standard-gap re-join, loudness re-normalization and word-timing rescale. Chapter starts, scene guards and sound frames do not move; rebuild semantic captions afterwards. Verified on a 4996-frame / 22-chapter production across three voice passes.

### Fixed

- **Case-insensitive visual-asset hashes**: `validate-visual-plan` now accepts uppercase `sha256` digests (e.g. from `Get-FileHash`) instead of rejecting them as mismatches.

### Docs

- **Long-film path** (`references/remotion-architecture.md`): for newly authored long films keep `TIMELINE_SCALE = 1` and set `DURATION` to the total delivery frame count with all timing authored in delivery frames; notes the bundled template ships a 1126-frame timeline.
- **Bundler authoring pitfall** (`references/remotion-architecture.md`): documents the observed misparse of adjacent generic-annotated arrow components after dense JSX (error misreported on the following line) with verified workarounds.
- **Re-voicing procedure** (`references/tts-audio.md`): lock → synthesize → speed-post → match → rebuild-captions sequence.

## [2.1.0] - 2026-09-02

### Changed

- **Elastic Glyph Wave Typography (4段双轴弹性波浪跳字与点亮系统)**:
  - *Tibo-style 4-Stage Overshoot JumpInText*: fully ported and tuned the physical spring wave trajectory (`waveY: [14px, -6px, 1.5px, 0px]`, `waveX: [3px, -1px, 0px, 0px]`, `rotX: [40deg, -5deg, 0deg]`), delivering tactile bounce and per-glyph ignition color transition (`activeColor -> ink`).
  - *Caveat Latin Handwriting Sub-system*: integrated `Caveat-Latin.woff2` hand-drawn annotation stickers (`lonely code`, `start small`, `packaging`, `ongoing triage`, `always by your side`) for rich multi-tier typographic hierarchy.
  - *Zero-Overlap & Zero-Flicker Transitions*: implemented strict lifecycle boundary isolation (`396~412f` exit, `416f` mount) eliminating the 14s transition collision; replaced floating Module overlays with smooth `Staggered Stack Inset` file lists, completely curing 16s flicker and 17s card-header collisions.
  - *Canonical Tri-Aspect Rendering Engine*: cleanly unified responsive rendering across all 3 official 2K canvases (16:9 `2560×1440`, 4:3 `1920×1440`, 3:4 `1440×1920`) with dedicated layout compositions (`NotebookVideoFilm-16x9`, `NotebookVideoFilm-4x3`, `NotebookVideoFilm-3x4`).

## [2.0.0] - 2026-09-02

### Changed

- **Cinematic Motion & Audio System (质感与音效体系大版本跃迁)**:
  - *Tibo-style 3D Mechanical RollDigit*: added `RollDigit` component utilizing projection-compressed `rotateX` 3D flipping with `cos` perspective scaling, replacing plain pop-in transitions for numerical and version releases (`v1.0` -> `v1.1` release with green `RELEASED` badge).
  - *Idle Life & Micro-Interactions*: upgraded mascot with sinusoidal breathing motion (`1 + 0.016*sin(f*0.16)`) and natural arm-waving lifespans.
  - *Curated Audio & Lo-Fi BGM System*: integrated ambient Lo-Fi background track (`bgm.mp3`) with gentle fade-in and decay at volume `0.08` (voice-safe), accompanied by high-frequency CC0 UI feedback audio cues (`toggle.ogg` mechanical flip, `click.ogg` step trigger, `drop.ogg` card magnetic snap-in).
  - *Three-Canvas Demo Suite Refreshed*: fully re-rendered 2K demos and animated WebP previews across all three delivery formats — 16:9 (`notebook-video-demo.mp4` / `.webp`), 4:3 (`notebook-video-demo-43.mp4` / `.webp`), and 3:4 portrait (`notebook-video-demo-34.mp4` / `.webp`).
  - *Native Browser Rendering Engine*: configured direct native Chrome/Edge binary binding for instant multi-threaded zero-download rendering.

## [1.9.0] - 2026-09-02

### Changed

- **Premium motion upgrade (质感升级固化)**: the lecture template is now a cinematic-quality baseline that any future skill video inherits:
  - *CameraRig dual-canvas camera*: per-canvas keyframe tables (16:9 landscape and 3:4 portrait), Tibo-style exponential lag follow-focus, per-chapter slow push-ins.
  - *JumpInText / WaveText*: per-glyph 3D flip-in (rotateX + stagger + spring) for chapter and scene titles; per-letter wave typing with color gradient for the CTA latin string.
  - *Subtitle redesign*: torn-paper bar removed, pure centered text pinned near the bottom, per-word/per-character fade-slide with a 180ms lead; word spacing only at CJK<->Latin boundaries.
  - *Globe intro*: multi-keyframe rotate-in (150deg to 360deg with a mid-scale bulge) replacing the plain pop-in.
  - *Palette softened*: lighter ivory paper, reduced grid/texture/vignette, soft layered card shadows and thinner outlines.
- **Typography**: unified to LXGW WenKai Lite (SIL OFL 1.1; Regular + Medium) for all CJK copy, with Clash Display / Space Grotesk Latin accents. Legacy Smiley Sans / Source Han Sans assets, font-faces and license files are removed; the example-project is unified to the same stack.
- **MiMo narration**: the 30s demo timeline was re-voiced through the MiMo TTS adapter (37.55s), and the whole scene timeline was remapped word-by-word to 1126 frames (new scene starts 0/213/416/682; caption cues rebuilt to 16 semantic lines). Narration audio stays unbundled per repository convention.
- **Demo assets**: `assets/demo/notebook-video-demo.mp4` and its animated webp are refreshed for 16:9 only; the 4:3 and 3:4 previews keep the previous renders.

## [1.8.0] - 2026-09-02

### Changed

- **Widen Dependency Compatibility (拓宽依赖与通用兼容)**:
  - Widen React & ReactDOM dependency range to `^18.2.0 || ^19.0.0` across example projects and lecture templates, eliminating peer dependency lockups and enabling seamless execution on both React 18 and React 19 environments.
  - Widen Remotion dependency range to `^4.0.0` (`remotion`, `@remotion/cli`, `@remotion/media`), allowing automatic minor/patch upgrades without breaking style locks.
  - Relax Node.js engine requirement to `>=18`.
  - Refactor `validate-official-example.py` and `validate-skill-consistency.py` to validate semantic version ranges rather than brittle exact string equality.
  - Bump `browserslist` transitive dependency to `4.28.8` to resolve high severity advisory (GHSA-c83g-rgw3-j3cx).

## [1.7.0] - 2026-09-01

### Changed

- **Background redesigned to a full-canvas paper surface** (`Background` in the lecture template): the warm radial desk band outside the page, the 1.7px page outline and the offset page shadow are removed. The ivory surface (`C.paperBase`) now covers the whole canvas; the 54px grid and static dot texture stay inside the inner rule. On narrow/phone frames the paper is no longer surrounded by nested rails and rings.
- **Card text alignment fixes** in the lecture template: node card labels (`仓库/Star/Issue/Fork/PR`) are drawn inside the card whitespace instead of hanging below the card edge, and the step list in the contribution scene is compacted (item height 56→48, gap 12→8, container `top/bottom` 120/96→116/104) so the bottom `github-oss-contribute` pill no longer overlaps the fourth step.
- **TTS adapter** (`tts-openai-compatible.py`): the `voice` field is now omitted when empty instead of sending `"voice": ""` — MiMo voicedesign models reject the empty string with HTTP 400.
- **Demo assets replaced**: `assets/demo/notebook-video-demo.mp4` (1280×720) and `notebook-video-demo.webp` are fresh renders of the updated template with chapter-synced narration, no black/letterbox frames and the new full-canvas background. New canvas variants were added: `notebook-video-demo-43.mp4` (4:3) and `notebook-video-demo-34.mp4` (3:4 portrait) with matching animated webp previews, and the READMEs now show a three-canvas demo gallery.

### Added

- **One template, three canvases**: the lecture template ships a `CANVAS` switch (`'16:9' | '4:3' | '3:4'`) in `src/index.tsx`. Composition, film wrapper, subtitle strip, chrome and safe-width values come from the locked per-mode table; the 4:3 landscape reuses the landscape scene set inside a scaled wrapper, and the 3:4 portrait film uses its own single-column `*P` scene set (verified in the rendered demo). The template caption data set was refreshed to the 30s chapter-synced timeline (scene cuts 216/396/600).

### Docs

- `references/visual-system.md` background section and `references/locked-style-contract.json` background tokens updated to the full-canvas contract (`outer_gradient`/`page_outline`/`page_shadow` now `null`, `page_bounds` = full canvas).

## [1.6.2] - 2026-07-31

### Changed

- `references/tts-audio.md` and the SKILL.md TTS step add a **polyphone (多音字) handling** rule: rewrite easily-misread polyphones into reading-unambiguous, meaning-equivalent phrases directly in `narration.txt` (and mirror them into `manifests/semantic-caption-lines.txt`) instead of relying on TTS context or SSML. The adapter feeds plain text with no pinyin channel and the narration doubles as subtitle text, so a wrong reading can only be prevented at the source; keeping replacements close in character count means chapter frames barely shift. Ships a table of production-verified rewrites (重装→重新装, 批量重命名→批量重新命名, 输一行命令→输入一条命令, 钉在屏幕上→贴在屏幕上, 一模一样→长得一样) and a reminder to update matching on-screen card text.

## [1.6.1] - 2026-07-30

### Changed

- `references/portrait-illustration-system.md` gains a "choosing the vehicle" section: illustration-first is about role, not a mandate to draw everything — pick text-forward panels/checklists for definitions, lists, comparisons, sources and shock numbers, and illustration for scenes/processes, with every beat legible from the text alone or the animation alone. Two guardrails added: an inline icon must render smaller than its container box (or it spills over the corners), and stacked panels/lines need ≥50px vertical gaps to avoid a phone-screen overlap.

## [1.6.0] - 2026-07-27

### Added

- `references/portrait-illustration-system.md`: the illustration-first grammar for 3:4 portrait, verified on a produced pilot. Codifies the text-vs-graphic role split (in-scene text is a short label; full narration lives in the subtitle strip), a reusable code-drawn figure cast with subtle idle motion, a persistent faint **Ambient** scatter layer that removes empty negative space, a text-emphasis kit (highlighter marker, hand-drawn underline, contrast label pair, fast pop count-up), the three-band scene structure (heading / hero illustration / payoff), and proven process/checklist/end beat patterns.
- Guardrails carried into the doc: author strictly in the 1080×1440 design space (coordinates beyond 1080 clip), keep chapter-chrome `stage` boundaries identical to the scene-cut frames, and check the contact sheet for any transient mostly-background frame or a `0`-dwelling counter.

### Changed

- SKILL.md portrait kickoff now points to `references/portrait-illustration-system.md` alongside `canvas-modes.md`.

## [1.5.0] - 2026-07-27

### Added

- Third locked canvas: **3:4 portrait** (1440×1920 delivery, 1080×1440 design space) for portrait feeds such as Douyin. Full parameter column in `references/canvas-modes.md` plus a portrait authoring procedure: single-column stacked zones, subtitle strip at the bottom (margins 50, bottom 40, height 104), Smiley subtitle at 40px with a 900px width gate. Verified on a produced pilot; 9:16 was tested and rejected (dead lower band under platform UI).
- `validate-video` accepts the 1440×1920 container; `validate-visual-plan` canvas gate now knows all three modes and additionally cross-checks the design-space height and the subtitle strip bottom offset.
- `references/locked-style-contract.json` defines the 3:4 mode (bounds, safe width, per-mode subtitle font sizes).

### Changed

- SKILL.md kickoff question offers three canvases; canvas-modes.md consolidated per-mode subtitle sizes (44 landscape / 40 portrait) that v1.4.0 left stated only for landscape.

## [1.4.0] - 2026-07-27

### Added

- Standard delivery pace: the lecture template now ships `scripts/speed-post.py`, a deterministic post-synthesis step (`atempo=1.10`, pitch unchanged, loudness re-normalized) that also scales every timestamp in `narration.mp3.json` and `manifests/chapters.json` by the same factor. Documented in `references/tts-audio.md`; raw teaching-tone synthesis measures ~305 chars/min and prompt wording cannot hit a target pace reliably, so 336 chars/min is fixed in post.
- Save-hook ending contract in `references/pacing-rhythm.md`: knowledge-genre closing cards ask for a save with a concrete future moment (algorithms weight saves above completion for this genre), pair it with a code-drawn star animation, and keep platform references to the compliant wording without account names or links.
- Full-canvas vertical budget in `references/canvas-modes.md`: card bottoms reach ~40px above the subtitle strip; an empty lower quarter is a layout defect on phone screens.
- Three new pre-render self-check items in `references/lecture-composition.md`: body copy is pure ink (muted reserved for decorative kickers), cards consume the vertical budget, and SVG elements keep 24px clearance with no label over a graphic.

### Changed

- Subtitle strip refined: font switches to bundled Smiley Sans (designed for video subtitles, SIL OFL) at 44px with 1.2px tracking; the meaning-free blue ring decoration is removed while the orange locator bar stays. Template, caption width gate and `references/locked-style-contract.json` updated together. Verified on a produced pilot and a full episode.

## [1.3.1] - 2026-07-26

### Fixed

- `validate-visual-plan` now cross-checks canvas-mode consistency inside `src/index.tsx`: the `Composition` width (2560 or 1920) must agree with the film wrapper design width, `subtitleSafeWidth` and the subtitle strip margins. A mixed-mode file — for example a 4:3 film keeping the 16:9 subtitle margins, which shipped once and misplaced the subtitle strip — now fails validation with a precise error instead of passing silently.
- `references/canvas-modes.md` marks the four 4:3 values as change-together and adds the pre-render `validate-visual-plan` step.

## [1.3.0] - 2026-07-26

### Added

- `references/canvas-modes.md`: two delivery canvases now coexist — 16:9 (2560×1440, default) and 4:3 (1920×1440, taller mobile presence). The mode is asked once at kickoff and decides every layout coordinate; the reference carries the full parameter table (design space, subtitle strip margins, subtitle safe width, two-column budgets), a mechanical 4:3 re-layout procedure and the mobile-readability font floor. Both modes were verified on full-length productions.
- `references/pacing-rhythm.md`: the energy-curve contract — hammer frames (one full-screen quotable line per 60–90 seconds), fast/slow chapter alternation with per-segment TTS pace instructions, breathing gaps between chapters, reduced density at the close, plus a pre-render pacing gate.
- Three proven first-sentence templates in `references/narrative-hook.md` (result first / curiosity gap / conflict-contrast) with an action-density gate for the first 3 seconds, and a ban on audience-labeling or roadmap openers.

### Changed

- `SKILL.md` kickoff now asks the canvas mode (16:9 or 4:3) once per production and binds the copywriting step to the cold-open and pacing contracts.
- `validate-video` accepts both locked canvases (2560×1440 and 1920×1440); the locked style contract defines both modes including subtitle bounds.
- Lecture template font floor raised for phone readability: body 26 / label 22 / footnote 18 (titles and subtitles unchanged).

## [1.2.0] - 2026-07-26

### Added

- `assets/lecture-template/`, the new default project template: a fully validated 30-second lecture-composition film with layered source (locked core, reusable component library, clearly marked content layer) proven across a produced multi-episode series.
- `references/lecture-composition.md`: the default multi-zone code-drawn visual route — six binding rules (pure SVG graphics, multi-zone layout, text/graphic co-stars, cue-frame speech sync, demonstrative animation, series component reuse), a mechanical cue-to-frame procedure and a pre-render self-check list, written so weaker models can reproduce the established style by imitation.
- `scripts/tts-openai-compatible.py` inside the template: a provider-neutral, chapter-segmented TTS adapter for any OpenAI-compatible chat TTS endpoint, configured only through environment variables; measures real segment durations so chapter boundaries never drift, writes `manifests/chapters.json`, and caches segments by text hash.
- `new-project ./dir --classic` to copy the original visual-director exemplar for productions that accepted the image add-on.

### Changed

- Lecture composition is now the default visual route; image generation became an optional add-on offered to the user once per production, with an explicit note that its result depends on the current tool's image quality and that Codex's built-in image generation is the best-suited environment for it.
- `new-project` copies the lecture template by default; smoke tests cover both routes.
- `SKILL.md`, both landing pages and `references/tts-audio.md` updated for the default-route/add-on split and the recommended chapter-segmented TTS adapter (Edge Read Aloud remains the zero-key fallback).

## [1.1.0] - 2026-07-19

### Added

- A provider-neutral visual-director stage that selects `image-text`, `pure-text` or `pure-graphic` for every scene from the narration meaning.
- Optional Codex image-generation enhancement with complete fallbacks for other agents and local environments.
- Generated-image prompt, crop, provenance and redistribution records through `manifests/visual-assets.json`.
- `validate-visual-plan` for scene modes, start-inclusive/end-exclusive lifetimes, raster existence, SHA-256 integrity and provenance.
- An official Remotion image-plus-text example with the bitmap, callouts and exact labels animated as independent layers.
- Microsoft Edge Read Aloud as the preferred zero-key Mandarin TTS adapter when available and appropriate.

### Changed

- Upgraded the official style contract from v8 performance to v9 visual director while preserving 2K/30fps rendering, semantic subtitles, declarative audio, complete exits and automated QA.
- Updated the skill metadata, English/Chinese landing pages and project scaffolding for image-generation-aware production.

## [1.0.3] - 2026-07-18

### Fixed

- Corrected contributor attribution so GitHub recognizes the Codex collaborator instead of the unrelated `noreply` account.
- Clarified the current naming: ChatGPT is the desktop application, while Codex remains its coding mode and GitHub contributor identity.

## [1.0.2] - 2026-07-18

### Added

- A real 30-second animated showcase and four-scene preview rendered by the official engine.
- Direct release, ZIP, HTTPS, SSH, GitHub CLI and raw-contract download paths.
- Verified user-level and repository-level installation examples for Codex, Claude Code and Cursor.
- A five-minute first-run example and an AI-assisted installation prompt.

### Changed

- Rewrote the English and Chinese landing pages around the output, shortest install path and real evidence.
- Refined repository description, topics and tracked release metadata for discoverability.

## [1.0.1] - 2026-07-18

### Fixed

- CI now checks Python syntax without creating forbidden `__pycache__` files.
- GitHub Actions upgraded to pinned v7 commits with the current runtime.
- CI installs its declared FFmpeg/FFprobe system dependency before validation.
- Dependabot no longer proposes unreviewed changes to the style-locked Remotion engine.

## [1.0.0] - 2026-07-18

### Added

- Cross-platform Node launcher for the full notebook-video workflow.
- Official 2K/30fps Remotion example with synchronized narration, semantic captions and licensed fonts.
- Automated skill, layering, caption, render and packaging validation.
- English and Simplified Chinese project documentation.
- Apache License 2.0 project licensing and third-party notices.
- Provider-neutral TTS audio and word-timing adapter contract.
- Locked 900-frame asset manifest aligned with the canonical 30-second composition.

### Security

- Repository ignores credentials, private keys, caches, generated renders and local environment files.
