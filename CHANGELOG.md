# Changelog

All notable changes are recorded here. The project follows semantic versioning.

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
