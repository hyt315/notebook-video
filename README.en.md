# Notebook Video · Chinese teaching-video skill

<div align="center">

**Turn one idea into a 16:9 Chinese teaching video: component scenes, an engine-level virtual camera and on-the-beat sound effects. One command renders it; objective gates fix what they can.**

[![Version](https://img.shields.io/badge/version-3.2.0-1f6feb)](CHANGELOG.md)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-555)](references/cross-platform-compatibility.md)
[![Themes](https://img.shields.io/badge/themes-flat%20%7C%20cel-ff7a59)](references/theme-system.md)
[![Validate](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml/badge.svg)](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-1f6feb)](SKILL.md)

[中文](README.md) | English

</div>

---

## What it is

`notebook-video` is an **Agent Skill** (a folder with a `SKILL.md`). Install it into Claude Code, Codex, Cursor or another agent,
ask for "a short explainer on hash tables", and the agent uses the blueprints, template and gates here to build a 30-second to
multi-minute Chinese teaching video with **React + TypeScript + [Remotion](https://www.remotion.dev/)**. You get the MP4 and the
full, editable source project.

- **Components, not slides**: every shot is a real code-drawn component — consoles, code diffs, checklists, stat rows, funnels,
  progress rings, stamp seals, verdict bars… — or a real screenshot / short screen recording.
- **The camera follows the narration**: an engine-level virtual camera pushes in by default, moves to whatever component the
  narration names, and cuts with whip pans or zoom-throughs.
- **Reproducible by weaker models**: five teaching blueprints name the skeleton and components for every shot, plus golden
  examples, a five-step workflow and one command. Anything that can be judged objectively is auto-fixed by the engine.

- **New in 3.7.0 — one paper per notebook, review before render**: hand-made skins default to `bgMode: "chapter"` (one paper per chapter; `"film"` keeps one for the whole film, `"shot"` rotates per shot), and decorative `busy` backgrounds stay off regular shots; `resolve-shots` generates `storyboard.md` from the real shot table for the independent review; for hand-made skins `make-video --render` stops until a review round is recorded (drafts pass `--skip-review`); silent films time whole-line captions at `--cps` (default 6.5 chars/s).

- **New in 3.4.0 — a background library**: 8 more light backgrounds per craft skin and 5 more for flat / cel (ruled notebook,
  xuan paper, window-flower papercut, a 1630 map, film strips, screentone, mesh gradients…), rotated by shot role with no two
  adjacent shots alike; every file records its source and licence (Paper Shaders rendered offline once, public-domain / CC0
  Commons textures, fixed-seed drawings) and a gate checks light ground and subtitle contrast.
  See [references/background-library.md](references/background-library.md).

- **New in 3.3.0 — decide what the idea is made of first**: a director layer (metaphor first → the medium is the metaphor → one
  native move at the turn → three candidate structures; `treatment.json` is gated), three light hand-made skins (`journal`
  field notebook / `papercut` red paper-cut / `archive` light table) with craft components (pressure ink, Chinese lettering
  that writes itself, watercolour washes, paper cuts, a loupe), and a **Wikimedia Commons / Openverse** search for every topic
  with licence filtering and on-screen credits.

One canvas only: **16:9** (2560×1440 delivery, 1920×1080 by default; 1920×1080 design space, native 30 fps). Five themes:
`flat` (default, calm modern edu illustration), `cel` (bold comic ink) and the 3.3.0 craft skins `journal` / `papercut` / `archive`.

## Key features

| Capability | Details |
| --- | --- |
| **Component scenes** | 4 skeletons (Stage / Split / Zoom / Corridor) and a component library (`ConsoleWindow`, `DiffView`, `HighlightCode`, `StatRow`, `Funnel`, `ProgressRing`, `KineticNumber`, `StampSeal`, `VerdictBar`, …), all coloured from theme tokens |
| **Virtual camera** | Default slow push-in per shot; `cinema.focus` pushes to the component a keyword names and pans between targets; whip / zoom-through transitions; background parallax; small content is enlarged to 60–80 % of the safe area; push-ins keep margins so titles are never cut |
| **On-the-beat SFX** | 10 code-synthesised semantic sounds (CC0) and an optional music bed; each cue carries `gain` / `offsetMs` and is pre-rolled so its transient lands on the visual hit (±1 frame); ≥150 ms spacing, ≈24/min cap; the bed ducks under each cue |
| **Real media** | Screenshots, ≤10 s recordings and GIFs inside `MediaFrame` (same card look as the components, optional browser / window / device chrome, region zoom, highlight boxes, callouts, credit badge); `prepare-media` transcodes, `validate-media` blocks blurry or unlicensed media |
| **Weak-model friendly** | 5 blueprints (concept / code-change / data-compare / process / pitfall) with a per-shot `$components` pick; golden examples in `examples/`; unfilled `<<placeholders>>` fail loudly |
| **One command** | `make-video.mjs`: resolve-shots → gates → tsc → stills contact sheet or full render → `renders/report.md`; `make-video.cmd` on Windows |
| **Gates & auto-fix** | Hard gates cover objective problems only (clipped framing, font floor, contrast ≥4.5:1, ≤16-character caption lines, ≤4.5 chars/s reading speed, frozen frames, A/V sync, SFX levels) and auto-fix what they can; subjective rules only advise |
| **Deterministic** | Every animation is a pure function of the frame (no `Math.random`, CSS animation or timers); no image-generation model, no online API required |

## Quick start

### 1. Install the skill

Send this to your agent:

> Please install the notebook-video skill: clone `https://github.com/hyt315/notebook-video` into your skills directory (e.g. `~/.claude/skills/notebook-video` or `~/.agents/skills/notebook-video`) and confirm it is installed.

Or install by hand:

| Platform | User level | Project level |
| --- | --- | --- |
| Claude Code | `git clone https://github.com/hyt315/notebook-video.git ~/.claude/skills/notebook-video` | `.claude/skills/notebook-video` |
| Codex | `git clone https://github.com/hyt315/notebook-video.git ~/.codex/skills/notebook-video` | `.codex/skills/notebook-video` |
| Cursor | `git clone https://github.com/hyt315/notebook-video.git ~/.cursor/skills/notebook-video` | `.cursor/skills/notebook-video` |
| Generic agents | `git clone https://github.com/hyt315/notebook-video.git ~/.agents/skills/notebook-video` | `.agents/skills/notebook-video` |

With GitHub CLI 2.90+: `gh skill install hyt315/notebook-video notebook-video --agent claude-code --scope user`

### 2. Prepare the environment

- **Node.js 18+**, **Python 3**, **ffmpeg / ffprobe** (frame extraction, transcoding, loudness)
- Before the first render, check dependencies and prepare the rendering Chromium:

```bash
node scripts/notebook-video.mjs check-deps
node scripts/notebook-video.mjs fonts   # first run downloads LXGW WenKai Lite (~28 MB, pinned version + sha256; new-project calls this automatically)
```

### 3. Make a video

```bash
# Create a project (copies the template; --style=flat or cel)
node scripts/notebook-video.mjs new-project ./my-video --style=flat

# After editing manifests/shots.json, src/scenes.tsx, src/film.ts and the captions:
node scripts/make-video.mjs ./my-video --stills                          # contact sheet of each shot's key moments
node scripts/make-video.mjs ./my-video --render ./my-video/final.mp4     # full render once the stills look right
```

On **Windows** (cmd / PowerShell) use the same `node` commands, or:

```bat
scripts\new-project.cmd .\my-video --style=flat
scripts\make-video.cmd .\my-video --stills
scripts\make-video.cmd .\my-video --render .\my-video\final.mp4
```

Reading the output: `✓ 自动修` (auto-fixed) lists what the engine changed for you; `· 建议` (advice) never blocks; only `✗` needs a fix, and each one says how.

## What a blueprint looks like

All blueprints follow the same teaching arc: **hook → one key term → break it down → example → pitfall → recap**. Only the `<<…>>` parts are edited, and `$components` tells the model what to use:

```json
{
  "role": "hook",
  "layout": "statement",
  "lines": ["<<一句反常识的现象，含 {{关键词}}>>", "<<一句追问>>"],
  "content": {"text": "<<屏上那句话（≤16 字）>>", "sub": "<<可选副句>>"},
  "$components": {"skeleton": "Stage", "components": ["Callout", "StampBanner", "FitTextBox"]}
}
```

`{{keyword}}` marks a sync point: when the narration reaches that word, the camera push-in, the component highlight and the sound effect land on the same frame. Filled-in examples live in [`examples/`](examples/) (hash-table concept, a caching code change, SSD vs HDD, a Git PR with a real screenshot).

Two routes:

- **Hand-written component scenes (recommended for delivery)**: `shots.json` + `scenes.tsx` in the project directory, adapted from the template's 8-shot example film. Manual: [references/handwritten-scenes.md](references/handwritten-scenes.md).
- **story.json draft (quick first cut)**: `node scripts/make-video.mjs examples/concept-hash-table.story.json ./draft --stills`; `compose-story.py` lays out, times and frames the shots. See [references/auto-engine.md](references/auto-engine.md).

## Real media

When viewers will later act on a real interface (say a GitHub PR page), a real screenshot beats a redraw:

```bash
python scripts/prepare-media.py ./my-video --add pr.png --id pr-page --region diff 0.01 0.31 0.69 0.17
```

```tsx
<MediaFrame f={f} id="pr-page" x={200} y={200} w={1060} h={662} focus="diff" focusAt={b[1]} />
```

- Recordings are converted to H.264 at constant 30 fps with audio stripped by default; `--trim` picks a segment.
- Source priority: the user's own files > your own captures of official pages > CC0 / CC-BY / Pexels / Unsplash. Web media must carry `url` / `license` / `credit`; the credit badge is drawn automatically. Without a compatible licence, redraw it with components.
- `validate-media` blocks missing files, upscaling beyond 1.5× (blurry), wrong codec / frame rate, missing licence or credit, and references to undefined regions.

Details: [references/real-media.md](references/real-media.md).

### Search Wikimedia Commons / Openverse first (3.3.0)

```bash
python scripts/commons-search.py search "Hooke Micrographia cork" --project ./my-video
python scripts/commons-search.py add ./my-video "File:Micrographia Schem 11.jpg" --id hooke-plate
python scripts/commons-search.py credits ./my-video   # → CREDITS.md
```

No API key, standard library only; public domain / CC0 / CC BY are accepted (CC BY-SA is excluded by default because share-alike
would reach the whole film), and `ArchivePhoto` / `PinnedPhoto` / `LoupeMedia` always draw the credit.
Details: [references/commons-media.md](references/commons-media.md).

## Themes

| Theme | Look | Select with |
| --- | --- | --- |
| `flat` (default) | Sky / cream surfaces, rounded cards, soft hard shadows; calm modern edu illustration | `--style=flat` |
| `cel` | Off-white comic paper, 3 px ink outlines, ink offset shadows, red / blue / yellow primaries | `--style=cel` |
| `journal` | Naturalist's field journal: warm cotton paper, taped sheets, pen notes, watercolour washes, vermilion as the only accent | `--style=journal` |
| `papercut` | Red window paper-cut: rice paper, red cut-outs with double contours, a deep-red banner subtitle | `--style=papercut` |
| `archive` | Archive light table: real archival objects on a cool backlit surface, one signal colour, a loupe | `--style=archive` |

Craft skins use 96 px@1440 Noto Serif SC Bold subtitles (downloaded on demand, sha256-checked) with no UI pill, and require a director
treatment `manifests/treatment.json` ([references/director-method.md](references/director-method.md)); components in
[references/craft-kit.md](references/craft-kit.md), style recipes in [references/style-recipes.md](references/style-recipes.md).

Each theme ships three locked backgrounds (main / chapter / quiet) with a calm central ~70 % safe area; the engine picks one per shot. Text uses dedicated `*Ink` colours so contrast always passes. Specs: [references/theme-system.md](references/theme-system.md), [theme-flat.md](references/theme-flat.md), [theme-cel.md](references/theme-cel.md), [theme-journal.md](references/theme-journal.md), [theme-papercut.md](references/theme-papercut.md), [theme-archive.md](references/theme-archive.md).

## Gates at a glance

| Stage | Checks | Typical catches |
| --- | --- | --- |
| Build time (Python) | `resolve-shots`, `validate-composition`, `validate-shot-motion`, `validate-frame-props`, `validate-presentation`, `validate-caption-sync`, `validate-semantic-breaks`, `validate-layering`, `validate-visual-plan`, `validate-audio-levels`, `validate-media` | Same layout in adjacent shots, content too small, wrong frame-prop name, low contrast, caption lines over 16 characters or too fast to read, SFX gain out of sync with the library, blurry media |
| Render time (in the browser) | `OverlapGate`, `ClippingGate`, `CanvasBoundsGate`, `FillGate`, `CaptionFitGate`, `MascotGate` | Overlapping text, clipped graphics, content off-canvas, caption overflow |
| Final film | `validate-video`, `validate-motion-gaps` | Wrong size / codec / colour tags, frames frozen too long |
| Skill self-checks | `validate-skill-consistency`, `selftest`, `negative-gate-check` | Docs naming components that do not exist, broken links; every gate must block a deliberately broken input |

Details: [references/composition-gate.md](references/composition-gate.md), [references/presentation-gate.md](references/presentation-gate.md), [references/quality-checklist.md](references/quality-checklist.md).

## Project structure

```text
notebook-video/
├── SKILL.md                     # Skill entry point: the 5-step workflow (what the agent reads)
├── manifest.json                # Name, version, licence
├── blueprints/                  # 5 teaching blueprints (concept / code-change / data-compare / process / pitfall)
├── examples/                    # Golden story.json examples, a real-media example, the weak-model test
├── assets/
│   ├── lecture-template/        # The only project template (Remotion + React + TS)
│   │   ├── src/                 # Engine (index / cinema / sfx), components, themes, gates, custom/ escape hatch
│   │   ├── manifests/           # shots.json, captions, media manifests
│   │   ├── public/              # Fonts, backgrounds, SFX library sfx/, real media media/
│   │   └── scripts/             # Optional TTS adapter, speed post-processing
│   └── fonts/                   # LXGW WenKai Lite (OFL-1.1, not committed; downloaded on first use)
├── scripts/                     # make-video, the notebook-video CLI, compose / resolve, gates, self-checks; .cmd / .sh wrappers
│   └── dev/                     # Maintainer tools (SFX library build and tuning)
├── references/                  # Author manuals and specs (camera, layouts, themes, SFX, captions, gates, cross-platform)
├── tests/                       # test_skill.py
└── CHANGELOG.md · CONTRIBUTING.md · NOTICE · DEPENDENCIES.md · LICENSE
```

## FAQ and limitations

- **Is there built-in voice-over?** No. Narration defaults to a silent placeholder and captions are timed at 4.5 characters per second. For a real voice or TTS, bring your own audio or point the template's `scripts/tts-openai-compatible.py` at your own OpenAI-compatible TTS endpoint (keys are read from environment variables only), then re-align with `scripts/match-timing.py`.
- **Does it use an image-generation model?** No, and image generation is not a default route. Scenes are drawn by components; use screenshots / recordings when a real interface matters.
- **Portrait or 4:3?** No. Since 3.2.0 the only canvas is 16:9; the 3.1.x 4:3 / 3:4 canvases, the `paper` / `sticker` skins and the `--classic` example project are gone, and older projects are not supported.
- **My topic needs a one-off diagram.** Copy `src/custom/RequestLane.tsx`, write your component and register it in `src/custom/index.ts`.
- **Does the story.json draft look as good as hand-written scenes?** Close, but not identical: draft layouts are drawn by `auto.tsx`. Use hand-written component scenes for delivery.
- **Is rendering slow?** Check with `--stills` first (key frames only). Full renders default to 1920×1080 delivery.
- **Are demo videos included?** No. To keep the repository light, rendered demos are not committed; run `--stills` to see the look locally.

## Contributing

Issues and pull requests are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). Before submitting, run:

```bash
python scripts/validate-skill-consistency.py
python scripts/selftest.py
python scripts/negative-gate-check.py
```

History: [CHANGELOG.md](CHANGELOG.md). Security reports: [SECURITY.md](SECURITY.md).

## Licence

[Apache License 2.0](LICENSE). Licences and attribution for the font (LXGW WenKai Lite, OFL-1.1, downloaded from the official release; set `NOTEBOOK_VIDEO_FONT_BASE_URL` for a mirror or drop the files into `assets/fonts/`), the sound effects (CC0) and third-party dependencies are in [NOTICE](NOTICE) and [DEPENDENCIES.md](DEPENDENCIES.md).

> **About Remotion's licence**: Apache-2.0 covers this repository's code only. The rendering engine [Remotion](https://www.remotion.dev/license) is
> **source-available, not open source**: individuals, non-profits and for-profit companies with **up to 3 employees** use it for free (including
> commercially); **for-profit companies with 4 or more employees need a Remotion Company License**. Generated projects include
> `REMOTION-LICENSE-NOTICE.md`. Media downloaded from Commons / Openverse keep their own licences; see the project's `CREDITS.md`.
