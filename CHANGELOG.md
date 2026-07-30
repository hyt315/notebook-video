# Changelog

All notable changes are recorded here. The project follows semantic versioning.

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
