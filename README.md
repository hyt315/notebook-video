# Notebook Video

[English](README.md) | [简体中文](README.zh-CN.md)

[![Validate](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml/badge.svg)](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/hyt315/notebook-video)](https://github.com/hyt315/notebook-video/releases)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

An Apache-2.0-licensed Agent Skill and Remotion starter for creating Chinese 2K notebook-style explainer videos. It ships one cross-platform workflow for macOS, Windows and Linux: narration, provider-neutral Chinese TTS inputs, semantic captions, deterministic Remotion rendering, automated QA and an editable project package.

## What it does

- Produces 2560×1440 H.264/AAC video at native 30fps.
- Uses a fixed warm-ivory notebook visual system with Chinese narration, synced word timing and semantic captions.
- Keeps macOS, Windows and Linux on the same Node launcher and the same Remotion source; shell and `.cmd` files are convenience wrappers only.
- Includes automated checks for video format, loudness, black frames, caption timing, protected phrases and visual layers.
- Uses a retention-first opening: show a sourced payoff or tension immediately, create an honest open loop, then answer it with evidence later in the film.

## Requirements

- Node.js 20 or later
- Python 3.9 or later
- FFmpeg available on `PATH`
- A compatible Remotion/Chrome rendering environment

No account credentials or API keys are included. Keep any local secrets outside this repository.

The repository stores dependency manifests, not installed dependencies. `node_modules`, the rendering browser, external TTS tools, caches and rendered videos are downloaded or created locally on demand and are excluded from source packages. The bundled fonts and small procedural sound effects are intentional runtime assets: they keep rendering deterministic across machines and ship with their license notices. See [DEPENDENCIES.md](DEPENDENCIES.md).

In restricted containers where Remotion cannot enumerate network interfaces, prefix render commands with `REMOTION_USE_NETWORK_SHIM=1`. This compatibility path is built into the launcher and does not change the rendered frames.

## Quick start

Create a new editable video project:

```bash
node scripts/notebook-video.mjs check-deps
node scripts/notebook-video.mjs validate-skill
node scripts/notebook-video.mjs new-project ./my-video
node scripts/notebook-video.mjs prepare-browser ./my-video
```

`prepare-browser` runs the pinned `npm ci` installation automatically when needed. The `render` command performs the same dependency check, so users do not need to manage `node_modules` manually.

Edit `narration.txt`, `storyboard.md`, `manifests/semantic-caption-lines.txt`, protected phrases and the topic-specific scene content. Generate `audio/narration.mp3` and the documented word-timing JSON with any suitable TTS provider, then create captions and the finished MP4:

```bash
node scripts/notebook-video.mjs build-semantic-captions ./my-video/audio/narration.mp3.json ./my-video/manifests/semantic-caption-lines.txt ./my-video/manifests/caption-cues.json --lead-ms 60
node scripts/notebook-video.mjs sync ./my-video
node scripts/notebook-video.mjs render ./my-video ./my-video/renders/final.mp4
node scripts/notebook-video.mjs validate-video ./my-video/renders/final.mp4 EXPECTED_SECONDS ./my-video/renders/contact-sheet.jpg
```

Windows users can run the same Node commands in Command Prompt or PowerShell, or use the matching `.cmd` wrappers in `scripts/`.

## Opening rule

The opening is not a title sequence. Within 1.5 seconds it must show a concrete, verified payoff or tension; by 8 seconds it must leave a question the body can honestly answer. Record the opening payoff, deferred question and later callback in the storyboard. Read [references/narrative-hook.md](references/narrative-hook.md) before producing a video.

## Repository map

- `SKILL.md` — operating contract for the skill.
- `assets/example-project/` — runnable Remotion starter and its pinned dependencies.
- `scripts/` — cross-platform launcher, caption utilities, render and QA tools.
- `references/` — visual, timing, quality and compatibility contracts.
- `assets/fonts/` — bundled fonts with their original license notices.

## Validate a change

```bash
node scripts/notebook-video.mjs validate-skill
node scripts/notebook-video.mjs validate-official-example
```

For a changed video, also render the opening 0–360 frames, inspect 0.5s / 2s / 4s / 8s / 10s, and run all video and caption checks described in `SKILL.md`.

## Attribution and third-party materials

- Source Han Sans and Smiley Sans are included under the SIL Open Font License 1.1; preserve the license notices in `assets/fonts/`.
- The bundled sound effects are generated procedurally and their reuse note is at `assets/example-project/public/sfx/LICENSE.txt`.
- Remotion, React and other package licenses remain governed by their own terms in the generated project's lockfile and package metadata.
- Remotion is source-available under the Remotion License, not OSI-approved open-source software. Individuals and eligible teams may use it for free; other organizations may need a paid license. Every generated project includes a direct licensing notice.
- TTS is provider-neutral and no TTS client is bundled. Edge Read Aloud may be considered as an external reference, alongside commercial or platform TTS services, but the user or agent must implement the adapter and verify the provider's terms.

See [NOTICE](NOTICE) for the redistribution notes that should ship with a public release.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Do not change the locked visual system or core renderer without a fully rendered review and a passing validation run.

## Security and community

- Report security issues through [GitHub Private Vulnerability Reporting](SECURITY.md), not a public issue.
- Read the [Code of Conduct](CODE_OF_CONDUCT.md) before participating.
- See [CHANGELOG.md](CHANGELOG.md) for release-facing changes.
