# Notebook Video · Chinese teaching-video skill

<div align="center">

**Turn one idea into a 16:9 Chinese teaching video: a notebook page carries the real thing, components do the explaining, line drawings are optional — with an engine-level virtual camera that follows the narration, one command to render, and objective gates that fix what they can.**

[![Release](https://img.shields.io/github/v/release/hyt315/notebook-video?sort=semver)](https://github.com/hyt315/notebook-video/releases)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-555)](references/technique.md#cross-platform-compatibility)
[![Themes](https://img.shields.io/badge/themes-flat%20%7C%20cel%20%7C%20journal%20%7C%20papercut%20%7C%20archive-ff7a59)](references/themes/system.md)
[![Output](https://img.shields.io/badge/output-2560%C3%971440%20%7C%2016%3A9%2030fps-0ea5e9)](references/technique.md#environment-matrix)
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

- **Draft-paper narration**: no pen on screen — things appear only when the voice-over reaches them and grow in progressively: text unfolds left to right, a sketch is traced part by part, annotations are drawn as they are spoken; at most two things grow at once (rules in references/draftpaper.md#reveal-rules).
- **A notebook page carries the shot, not slides**: every shot is either a **page** (a real archival plate or specimen photo, a magnifier over it, handwriting and a red seal) or a **component** doing the explaining (consoles, code diffs, checklists, stat rows, bars, verdict strips…). **Line drawings are optional**: they only ever draw a specimen, because a clip-art sketch that fails to explain a concept reads worse than no drawing — so they live inside the page as a figure (`content.figure`, ≤19 % of the drawing width) instead of leading the shot.
- **The camera follows the narration**: an engine-level virtual camera directs `push-in`, `pull-back`, `pan-follow`, and `still` shots from content and pacing, highlights spoken keywords, and defaults to real page turns (`CURL_FRAMES` = 22) at chapter cuts and on craft skins while alternating `slide` and `fade` intra-chapter (overridable per shot).
- **Reproducible by weaker models**: seven fusion recipes decide where the sketch sits and how big the cards are — the author only fills content. Ten teaching blueprints (five component routes + five hand-made structure families) name the skeleton and components for every shot, plus golden examples, a five-step workflow and one command. Anything that can be judged objectively is auto-fixed by the engine.

- **One paper per notebook, review before render**: hand-made skins default to `bgMode: "chapter"` (one paper per chapter; `"film"` keeps one for the whole film, `"shot"` rotates per shot), and decorative `busy` backgrounds stay off regular shots; `resolve-shots` generates `storyboard.md` from the real shot table; the independent review scores it with the rubric in [references/rubric.md](references/rubric.md), and the scores lead `renders/report.md`; for hand-made skins `make-video --render` prints a P1 reminder until a review round is recorded (it still renders; `--skip-review` silences it); without running TTS, caption timing is estimated at the timing pace `--cps` (component default `READ_CPS` = 4.5 weighted chars/s, handmade estimate 6.5); use `notebook-video tts` to get word-level timing for a real film.

- **A background library**: 8 more light backgrounds per craft skin and 5 more for flat / cel (ruled notebook,
  xuan paper, window-flower papercut, a 1630 map, film strips, screentone, mesh gradients…), rotated by shot role with no two
  adjacent shots alike; every file records its source and licence (Paper Shaders rendered offline once, public-domain / CC0
  Commons textures, fixed-seed drawings) and a gate checks light ground and subtitle contrast.
  See [references/media.md#background-library](references/media.md#background-library).

- **Decide what the idea is made of first**: a director layer (metaphor first → the medium is the metaphor → one
  native move at the turn → three candidate structures; `treatment.json` is gated), three light hand-made skins (`journal`
  field notebook / `papercut` red paper-cut / `archive` light table) with craft components (pressure ink, Chinese lettering
  that writes itself, watercolour washes, paper cuts, a loupe), and a **Wikimedia Commons / Openverse** search for every topic
  with licence filtering and on-screen credits.

One canvas only: **16:9** (`2560×1440` delivery by default via `make-video --scale=1`; pass `--scale=0.75` for `1920×1080`; 1920×1080 design space, native 30 fps). Five themes:
`flat` (default, calm modern edu illustration), `cel` (bold comic ink) and the craft skins `journal` / `papercut` / `archive`.

## Key features

| Capability | Details |
| --- | --- |
| **Look at 30 seconds first** | `notebook-video preview <project>` renders one window (first 30 s, half resolution by default) plus a contact sheet and a loudness readout; `--shot=S6` narrows it to a single shot. Checking a revision no longer costs a full render. Timing varies a lot by machine, and the first run adds bundling time |
| **No shot left unchecked** | `notebook-video sweep <project>` grabs one settled frame per shot and tiles them into `renders/sweep-sheet.jpg` — eight shots in about 60 s, judged by the same empty-space thresholds the render uses. `preview` only covers the opening; on a longer film the tail silently escapes, and this closes that gap |
| **A delivery is not just an mp4** | A finished render also writes `renders/captions.srt` (the same line breaks burned into the film, not a re-recognition) and `renders/poster.jpg` (a settled frame of `treatment.signature_shot`, with captions suppressed). Standalone: `poster` / `export-srt` / `deliver` |
| **Compare two cuts** | `eval-project old/ new/` turns a film into comparable numbers (shot-length spread, variety of skeletons / media / transitions / camera intents, camera coverage, caption density, empty-space readings) and prints the delta. No score: thresholds live in the gates, in one place only |
| **Page + components** | Two kinds of shots alternate: a notebook page carrying the real thing (archival plate, magnifier, handwriting, seal) and components doing the explaining. Line drawings are optional specimen figures (`content.figure`, ≤19 % of drawing width); `validate-fusion` checks the page-plus-component mix |
| **Component scenes** | 4 skeletons (Stage / Split / Zoom / Corridor) and a component library (`ConsoleWindow`, `DiffView`, `HighlightCode`, `StatRow`, `Funnel`, `ProgressRing`, `KineticNumber`, `StampSeal`, `VerdictBar`, …), all coloured from theme tokens |
| **Virtual camera** | Directs `push-in`, `pull-back`, `pan-follow`, and `still` shots from content and layout; keyword highlights; page-turn chapter transitions with intra-chapter `slide` / `fade` variety; background parallax and title-safe framing |
| **On-the-beat SFX** | 9 semantic sounds (6 code-synthesised + 3 real-recorded Kenney RPG Audio CC0 foley effects, `public/sfx/lib/`), **no BGM by default** (a music bed loads only when `treatment.sound.music.use=true`); every cue carries `gain` / `offsetMs` and pre-rolls to land on the visual hit (±1 frame); `validate-silence` checks inter-sentence silence |
| **Real media** | Screenshots, ≤10 s recordings and GIFs inside `MediaFrame` (same card look as the components, optional browser / window / device chrome, region zoom, highlight boxes, callouts, credit badge); `prepare-media` transcodes, `validate-media` blocks blurry or unlicensed media |
| **Weak-model friendly** | 7 fusion recipes + 10 blueprints (5 component routes + 5 hand-made structure families) with a per-shot `$components` pick; golden examples in `examples/` (including `examples/recipes/`); unfilled `<<placeholders>>` fail loudly |
| **One command** | `make-video.mjs`: resolve-shots → gates → tsc → single-browser `--stills` contact sheet or 1440p full render → `renders/report.md` (with digest & review rubric at top); `make-video.cmd` on Windows |
| **Cross-project cache** | `deps-cache.mjs` & `browser-exec.mjs` share `node_modules` (by lockfile hash), `npm-cache`, cached `chrome-headless-shell`, and checksum-verified fonts under `NOTEBOOK_VIDEO_CACHE_DIR`, eliminating repeated installs across projects (`NOTEBOOK_VIDEO_SHARED_DEPS=0` disables linking) |
| **Gates & auto-fix** | Hard gates cover objective problems only (clipped framing, font floor, contrast ≥4.5:1, ≤16-character caption lines, ≤9.0 weighted chars/s (`CPS_MAX`) reading-speed cap (timing estimate `READ_CPS` = 4.5), overlay budget ≤5% / >30%, frame pacing / A-V offset / exposure / frozen frames, A/V sync, SFX levels) and auto-fix what they can; subjective rules only advise |
| **Deterministic** | Every animation is a pure function of the frame (no `Math.random`, CSS animation or timers); no image-generation model, no online API required |

## Recent changes ([v3.8.0](https://github.com/hyt315/notebook-video/releases/tag/v3.8.0))

- **1440p default output & lean bundles**: renders default to `2560×1440` (`--scale=1 --crf=18 --x264-preset=veryfast`), `--stills` reuses one browser session (`scripts/render-stills.mjs`), and `remotion.config.ts` disables/strips sourcemaps.
- **Open captions & composited motion**: all five themes share 64 design-px borderless paper-halo subtitles with compact top-left badges (≤5 % standing occlusion via `check_overlay_budget`) and composited reveals.
- **Multi-intent camera director & variant rhythm**: directs `push-in`, `pull-back`, `pan-follow`, and `still` shots (`CinemaSpec.driftDir`), keeps `auto` page turns at chapters with intra-chapter `slide` / `fade` variety, and seeds layout variants by title.
- **Resilient TTS & audio checks**: adds fuzzy spoken-stream fallback, pause-midpoint shot cuts, pinned shot-0 start, speech-bound weighted splitting, and spoken-form / clipping checks.
- **Cross-project resource reuse**: shares lockfile-hashed `node_modules`, `npm-cache`, cached headless Chromium discovery, and verified fonts across projects.

Per-release changes: [CHANGELOG.md](CHANGELOG.md).

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

- **Node.js 20+**, **Python 3**, **ffmpeg / ffprobe** (frame extraction, transcoding, loudness)
- Multiple video projects automatically reuse existing and user-cached `node_modules`, headless Chromium (`chrome-headless-shell`), and fonts across runs (matched by lockfile hash / checksum; missing assets are downloaded once and shared)
- Before the first render, check dependencies and prepare the rendering Chromium:

```bash
node scripts/notebook-video.mjs check-deps
node scripts/notebook-video.mjs fonts   # first run downloads LXGW WenKai Lite (~28 MB) and Clash Display (Fontshare; its licence forbids shipping it in the repo), pinned + sha256; new-project calls this automatically; offline, Clash falls back to Space Grotesk with a P1 note
```

### 3. Make a video

```bash
# 1) Create a project (--style=flat, cel, journal, papercut, or archive)
node scripts/notebook-video.mjs new-project ./my-video --style=flat

# 2) Write my-story.json from blueprints/ or examples/, then render the stills contact sheet:
node scripts/make-video.mjs my-story.json ./my-video --stills

# 3) Generate real Chinese voice-over and retime captions/shots:
node scripts/notebook-video.mjs tts ./my-video

# 4) Once stills & report look right, render the delivery MP4 (2560×1440 by default):
node scripts/make-video.mjs ./my-video --render ./my-video/final.mp4
```

On **Windows** (cmd / PowerShell) use the same `node` commands, or:

```bat
scripts\notebook-video.cmd new-project .\my-video --style=flat
scripts\make-video.cmd my-story.json .\my-video --stills
scripts\notebook-video.cmd tts .\my-video
scripts\make-video.cmd .\my-video --render .\my-video\final.mp4
```

For the handwritten-scene escape hatch (`manifests/shots.json`, `src/scenes.tsx`, `src/film.ts`), run `make-video ./my-video --stills` / `--render` directly.

Reading the output: `✓ 自动修` (auto-fixed) lists what the engine changed for you; `· 建议` (advice) never blocks; only `✗` needs a fix, and each one says how.

## What a blueprint looks like

Five component blueprints cover structured explainers and five handwritten-craft families cover metaphor/discovery stories (`blueprints/`). Only the `<<…>>` placeholders are edited, and `$components` tells the model what to use:

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

- **Hand-written component scenes (escape hatch for shot-by-shot layout)**: `shots.json` + `scenes.tsx` in the project directory, adapted from the template's 8-shot example film. Manual: [references/scenes.md#handwritten-scenes](references/scenes.md#handwritten-scenes).
- **story.json + blueprint (main route)**: `node scripts/make-video.mjs examples/concept-hash-table.story.json ./draft --stills`; `compose-story.py` lays out, times and frames the shots. See [references/technique.md#auto-engine](references/technique.md#auto-engine).

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

Details: [references/media.md#real-media](references/media.md#real-media).

### Search Wikimedia Commons / Openverse first

```bash
python scripts/commons-search.py search "Hooke Micrographia cork" --project ./my-video
python scripts/commons-search.py add ./my-video "File:Micrographia Schem 11.jpg" --id hooke-plate
python scripts/commons-search.py credits ./my-video   # → CREDITS.md
```

No API key, standard library only; public domain / CC0 / CC BY are accepted (CC BY-SA is excluded by default because share-alike
would reach the whole film), and `ArchivePhoto` / `PinnedPhoto` / `LoupeMedia` always draw the credit.
Details: [references/media.md#commons-media](references/media.md#commons-media).

## Themes

| Theme | Look | Select with |
| --- | --- | --- |
| `flat` (default) | Sky / cream surfaces, rounded cards, soft hard shadows; calm modern edu illustration | `--style=flat` |
| `cel` | Off-white comic paper, 3 px ink outlines, ink offset shadows, red / blue / yellow primaries | `--style=cel` |
| `journal` | Naturalist's field journal: warm cotton paper, taped sheets, pen notes, watercolour washes, vermilion as the only accent | `--style=journal` |
| `papercut` | Red window paper-cut: rice paper, red cut-outs with double contours, vermilion borderless subtitles | `--style=papercut` |
| `archive` | Archive light table: real archival objects on a cool backlit surface, one signal colour, a loupe | `--style=archive` |

All five themes use clean bottom-centred **64 design-px** (`85.3 px` @ 1440p) borderless text with a paper-tinted halo, keeping combined chrome + subtitle occlusion ≤ 5 %; craft skins also fetch Noto Serif SC Bold (~12 MB, sha256-checked) for hand-lettered display text and require a director
treatment `manifests/treatment.json` ([references/director.md#director-method](references/director.md#director-method)); components in
[references/components.md#craft-kit](references/components.md#craft-kit), style recipes in [references/director.md#style-recipes](references/director.md#style-recipes).

Each theme includes 8–11 light-ground backgrounds rotated by `bgMode` (`film` whole film / `chapter` per chapter, default for craft / `shot` per shot, default for flat & cel) with a calm central ~70 % safe area; see [references/media.md#background-library](references/media.md#background-library). Text uses dedicated `*Ink` colours so contrast always passes. Specs: [references/themes/system.md](references/themes/system.md), [references/themes/flat.md](references/themes/flat.md), [references/themes/cel.md](references/themes/cel.md), [references/themes/journal.md](references/themes/journal.md), [references/themes/papercut.md](references/themes/papercut.md), [references/themes/archive.md](references/themes/archive.md).

## Gates at a glance

| Stage | Checks | Typical catches |
| --- | --- | --- |
| Build time (Python) | `resolve-shots`, `validate-composition`, `validate-shot-motion`, `validate-presentation`, `validate-caption-sync`, `validate-semantic-breaks`, `validate-elem-kinds`, `validate-treatment`, `validate-opening`, `validate-facts`, `validate-layering`, `validate-visual-plan`, `validate-fusion`, `validate-glyphs`, `validate-silence`, `validate-audio-levels`, `validate-backgrounds`, `validate-media` | Content too small, low contrast, captions >16 chars or too fast, overlay >5% / >30%, missing subject or unhandled element kind, under-moving signature shot, blank frame 0, conflicting source claims, non-silent pauses, SFX drift, unverified backgrounds or blurry media |
| Render time (in the browser) | `OverlapGate`, `ClippingGate`, `CanvasBoundsGate`, `CardFitGate`, `CaptionFitGate`, `FillGate`, `SlotGuard`, `AssetGate` | Overlapping text, clipped graphics, content off-canvas, card/caption overflow, missing fonts or media |
| Final film | `validate-video`, `validate-motion-gaps`, `validate-opening`, `validate-silence`, `validate-ocr` | Wrong size/codec/bt709 tags, CFR stutter, A/V offset, dark/blown-out exposure, frozen frames, blank frame 0, noise floor |
| Skill self-checks | `validate-skill-consistency`, `selftest`, `negative-gate-check`, `dev/check-examples`, `dev/check-test-collection`, `dev/purity-smoke` | Docs naming components that do not exist, broken links; every gate must block a deliberately broken input; positive examples must pass and negatives must be blocked; a test file collects nothing; continuous and single-frame renders differ |

Gate results (including the in-browser render-time gates) are written to `renders/gates.json`: P0 only ever means the film is blocked, P1 goes to the report as advice; aesthetic and structural items (same skeleton / layout in adjacent shots, camera quotas, missing `$asks`) are P1 only. Frame props are required types checked by `tsc`; cross-language constants live in the template's `src/contract.json` only.

Details: [references/checks.md#composition-gate](references/checks.md#composition-gate), [references/checks.md#presentation-gate](references/checks.md#presentation-gate), [references/checks.md#quality-checklist](references/checks.md#quality-checklist).

## Project structure

```text
notebook-video/
├── SKILL.md                     # Skill entry point: the 5-step workflow (what the agent reads)
├── manifest.json                # Name, version, licence
├── blueprints/                  # 10 teaching blueprints (5 component routes + 5 hand-made structure families)
├── examples/                    # Positive story.json examples (CI requires all to pass the gates), real-media, weak-model test; negative/ deliberate negatives; cell-notebook/ docs only
├── assets/
│   ├── lecture-template/        # The only project template (Remotion + React + TS)
│   │   ├── src/                 # Engine (index / cinema / sfx), components, themes, gates, custom/ escape hatch; showcase-entry is the separate entry for component sheets
│   │   ├── manifests/           # shots.json, captions, media manifests
│   │   ├── public/              # Fonts, backgrounds (WebP), SFX library sfx/, real media media/
│   │   └── scripts/             # Optional TTS adapter, speed post-processing
│   └── fonts/                   # Download cache for LXGW WenKai Lite (OFL-1.1) and Clash Display (ITF FFL); not committed, fetched on first use
├── scripts/                     # make-video, notebook-video CLI, render-stills, deps-cache / browser-exec, compose / resolve, gates, self-checks; Windows entry points notebook-video.cmd / make-video.cmd only
│   └── dev/                     # Maintainer tools (one-command test-all.py, SFX and background library builds; not packaged)
├── references/                  # Author manuals and specs (narration, review rubric, camera, layouts, themes, linework, recipes, SFX, captions, gates, cross-platform), 11 files + themes/ 6
├── tests/                       # offline unit tests (a few skip when an optional dependency is missing or NV_ONLINE=1 is unset) (backgrounds / blueprints / camera / captions / media / fusion recipes / TTS / silence / gates / review …)
└── CHANGELOG.md · CONTRIBUTING.md · NOTICE · DEPENDENCIES.md · REUSE.toml (per-file licences) · LICENSE
```

## FAQ and limitations

- **Is there built-in voice-over?** There is a TTS command, not a voice model. `notebook-video tts <project>` uses edge-tts by default (needs network), or `--engine=file` for your own recording; both support word-level alignment, fuzzy spoken fallback, and pause-midpoint shot cuts (`faster-whisper` optional for recordings; otherwise speech-bound weighted character/punctuation splitting), plus spoken-form and clipping checks. Without real narration `--render` stops instead of shipping a silent film.
- **Does creating multiple video projects re-download dependencies and the browser?** No. `deps-cache.mjs` and `browser-exec.mjs` share lockfile-hashed `node_modules` and `npm-cache` under `NOTEBOOK_VIDEO_CACHE_DIR` via directory links, scan existing/cached `chrome-headless-shell` installations before downloading, and reuse checksum-verified fonts (`NOTEBOOK_VIDEO_SHARED_DEPS=0` disables dependency linking).
- **Does it use an image-generation model?** No, the skill never calls image models. Scenes are drawn by components; images come from the user, Wikimedia Commons / Openverse or other licensed sources, and screenshots / recordings cover real interfaces.
- **Portrait or 4:3?** No. The only canvas is 16:9; the earlier 4:3 / 3:4 canvases, the `paper` / `sticker` skins and the `--classic` example project are gone, and older projects are not supported.
- **My topic needs a one-off diagram.** Copy `src/custom/RequestLane.tsx`, write your component and register it in `src/custom/index.ts`.
- **Does story.json look as good as hand-written scenes?** Close, but not identical: its layouts are drawn by `auto.tsx`. Start with story.json + a blueprint; switch to hand-written component scenes when you need shot-by-shot layout control.
- **Is rendering slow?** Check `--stills` first (single browser session after one bundle). Full renders default to `2560×1440` (`--scale=0.75` gives `1920×1080`).
- **Are demo videos included?** No. To keep the repository light, rendered demos are not committed; run `--stills` to see the look locally.

## Making the skill package

Do not zip the whole working directory (`.git`, caches and local projects are not skill runtime content). Use the whitelist packager (use `python` instead of `python3` on Windows):

```bash
python scripts/package-skill.py --check-only   # only check the manifest and local links in SKILL.md
python scripts/package-skill.py                # write dist/notebook-video-skill.zip
python scripts/package-skill.py --include-fonts --output dist/notebook-video-offline.zip
```

The default package holds the entry point, runtime scripts, template, blueprints, core examples and reference material; it leaves out `.git`, `tests/`, `scripts/dev/`, `examples/{negative,regress,weak-model-test}/`, release-admin files such as `CHANGELOG.md`, caches, rendered output and the large on-demand fonts. Use `--include-fonts` only when you need a fully offline run (Clash Display's licence forbids redistribution, so no package ever includes it).

## Contributing

Issues and pull requests are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). Before submitting, run:

```bash
python3 scripts/dev/test-all.py   # one command: unit tests + selftest + negative checks + validate-skill + links + reuse lint (skipped if not installed)
```

History: [CHANGELOG.md](CHANGELOG.md). Security reports: [SECURITY.md](SECURITY.md).

## Licence

[Apache License 2.0](LICENSE). Licences and attribution for the fonts (LXGW WenKai Lite, OFL-1.1, downloaded from the official release — set `NOTEBOOK_VIDEO_FONT_BASE_URL` for a mirror or drop the files into `assets/fonts/`; Clash Display, ITF Free Font License, downloaded from Fontshare — mirror via `NOTEBOOK_VIDEO_CLASH_BASE_URL`), the sound effects (CC0) and third-party dependencies are in [NOTICE](NOTICE) and [DEPENDENCIES.md](DEPENDENCIES.md).

> **About Remotion's licence**: Apache-2.0 covers this repository's code only. The rendering engine [Remotion](https://www.remotion.dev/license) is
> **source-available, not open source**: individuals, non-profits and for-profit companies with **up to 3 employees** use it for free (including
> commercially); **for-profit companies with 4 or more employees need a Remotion Company License**. Generated projects include
> `REMOTION-LICENSE-NOTICE.md`. Media downloaded from Commons / Openverse keep their own licences; see the project's `CREDITS.md`.
