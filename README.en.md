# 📦 Notebook Video / Hand-drawn explainer videos

<div align="center">

**把一句话变成一支 2K 中文教学视频：纯代码绘制场景、帧精确对齐配音、镜头语言由门禁托底。**

**Turn one sentence into a 2K Chinese explainer video: code-drawn scenes, frame-accurate TTS sync, camera language enforced by automated gates.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/hyt315/notebook-video?sort=semver)](https://github.com/hyt315/notebook-video/releases)
[![Validate](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml/badge.svg)](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-1f6feb)](SKILL.md)
[![GitHub Stars](https://img.shields.io/github/stars/hyt315/notebook-video?style=social)](https://github.com/hyt315/notebook-video/stargazers)

English | [中文](README.md)

</div>

---

---

## 📖 What is this?

An AI-Agent **video production system**. Say "make me an explainer video about X" and it carries the job end to end: write the narration → synthesise Chinese TTS → read millisecond word timestamps → split into semantic subtitle lines → lay out a shot table → draw the scenes → run the gates → render a 2K film, and hand back an editable Remotion source tree alongside the MP4.

The hard part was never drawing something. It is making the result **not look like a slide deck**, keeping **captions in sync with the voice**, and keeping **elements from covering each other**. This skill turns all three into **gates that refuse to render**: skeletons must differ, media must differ, the camera must really move, captions must be measured with the real font, and text may not overlap — **a non-zero P0 count blocks the render**.

Every frame is drawn in code (React + SVG + Remotion) with **no image-generation model required**; when the argument needs "this really is the official UI / the official chart", a real screenshot can be dropped into a material plate.

---

---

## ✨ Features

| Feature | What it does | Why it matters |
| --- | --- | --- |
| **One sentence to a film** | Topic → 2K MP4: script → TTS → word timings → semantic captions → shot table → scenes → gates → render → contact sheet | No hand-placing frames, no sentence-by-sentence caption fiddling |
| **Four scene skeletons** | `Stage` (one subject evolves) / `Corridor` (an object travels a track) / `Split` (two-column contrast) / `Zoom` (wide → detail → annotation → wide); **no two adjacent scenes may share one, ≥3 per film** | Kills "four PowerPoint pages" structurally |
| **Content → medium routing** | Console window / chart / code diff / display type / metric grid / concept diagram; **≥3 media per film**, and every explanation scene carries at least one component that **changes state as the narration proceeds** | The frame stops being "card + paragraph" forever |
| **Restricted camera language** | Six intents per shot + an `anchor` out-of-bounds proof + a pan budget; **a declared move must actually move** | Real camera movement that can never push content off screen |
| **Fourteen quality gates** | 6 build-time: shot→frame resolution, out-of-bounds proof, composition & density, **frame-prop-name check**, **audio levels**, **presentation (beat↔cue alignment / caption reading budget / font size & contrast)**; 7 runtime: caption width, card overflow, **text-vs-text overlap and occlusion**, **clipped graphics**, **canvas bounds**, **measured lower-quarter density**, **main-slot occupancy**; 1 post-render: **whether the picture actually moves** | A non-zero P0 **blocks the render**; each gate also logs coverage so **"no warning" and "never ran" are distinguishable** |
| **Material plates** | Real screenshots / official charts sit inside the locked cel frame (2.5px ink outline + hard shadow) with a caption and a source line, and can drift slowly toward the point that matters; assets are registered in **both** `visual-assets.json` and `asset-manifest.json` (source / rights / baked text / checksum) | For claims that need "this really is the official thing"; anything a diagram explains better stays drawn |
| **Frame-accurate Chinese TTS sync** | Millisecond word timings → semantic sentence breaks → animation beats; trailing punctuation strictly stripped | No drifting captions, no audio-visual mismatch |
| **Four locked skins** | `paper` (warm ivory notebook, default) / `cel` (anime cel) / `sticker` / `flat` | One script, four moods |
| **Background readability contract** | The locked background bitmap is **never altered**; content that sits over decoration rides a **semi-transparent** feathered plate (panel 88%, plate centre 76%) | Readability without a solid white board — the film does not turn into a white slide |

---

---

## 🎨 Aspect Ratios (three locked canvases)
> To check the current version: `npm install` inside `assets/lecture-template`, then `npm run still` (single frame) or `npm run render` (full film). **For a delivery file, use `node scripts/notebook-video.mjs render <project> <output>`** — it rewrites the color metadata and normalizes loudness, which `npm run render` does not do (its output fails the `validate-video` color assertion).
> The contact sheet is the same: `node scripts/notebook-video.mjs showcase <project-dir>` now renders at **delivery spec** (2560×1440 / silent AAC / color tags rewritten, matching the file in `assets/demo/`). `--scale` accepts a decimal literal only — `--scale=4/3` is rejected by the CLI, use `1.3333333333333333`.

**Canvases**: three are locked — 16:9 (2560×1440), 4:3 (1920×1440) and 3:4 portrait (1440×1920), all native 30 fps. The bundled example film is authored in the **16:9 design space**; 4:3 / 3:4 need their own dedicated layout pass (**letterbox scaling is no longer presented as adaptation**).

## 📊 Production pipeline

```
[Input: topic / script]
        │
  ① Lock content ── narration.txt + semantic caption lines (one cue per line)
        │
  ② Write shot table ── manifests/shots.json
        │   declares only "which cues this shot covers" + skeleton / media /
        │   live components / camera intent / anchor
        │
  ③ Resolve ── resolve-shots.py → src/shots.ts (frame numbers and camera keyframes generated)
        │
  ④ Author scenes ── four skeletons + medium components; each shot wrapped in
        │   ShotCamera(keys, anchor); elements appear on the cue that narrates them
        │
  ⑤ Build-time gates ── validate-shot-motion.py (P0 = 0)
        │                validate-composition.py (P0 = 0)
        │
  ⑥ Render ── Remotion render + loudness normalisation (-16 LUFS / -1.5 dBTP)
        │
  ⑦ Runtime gates + delivery ── CaptionFitGate / CardFitGate / OverlapGate / ClippingGate / CanvasBoundsGate / FillGate / SlotGuard
                                (then validate-motion-gaps on the MP4: "nothing actually moved" is only visible there)
                                → 2K MP4 + contact sheet + editable source ZIP
```

---

---

## 🚀 Quick start

This is a standard AI Agent Skill — install it into your assistant and use it directly.

### Option A: paste one sentence (most portable)

Paste this into any agent and it will clone the skill into the right directory:

> Install the notebook-video skill: clone `https://github.com/hyt315/notebook-video` into your skills directory (e.g. `~/.claude/skills/notebook-video` or `~/.agents/skills/notebook-video`) and confirm it works. When I ask for an explainer video, a hand-drawn animation, a product promo or a concept walkthrough, follow SKILL.md and produce a 2K video.

### Option B: GitHub CLI 2.90+

```bash
gh skill install hyt315/notebook-video notebook-video --agent claude-code --scope user
```

### Option C: manual install

| Platform | User-level path | Project-level path |
| --- | --- | --- |
| **Claude Code** | `git clone https://github.com/hyt315/notebook-video.git ~/.claude/skills/notebook-video` | `.claude/skills/notebook-video` |
| **Codex** | `git clone https://github.com/hyt315/notebook-video.git ~/.codex/skills/notebook-video` | `.codex/skills/notebook-video` |
| **Cursor** | `git clone https://github.com/hyt315/notebook-video.git ~/.cursor/skills/notebook-video` | `.cursor/skills/notebook-video` |
| **Any agent** | `git clone https://github.com/hyt315/notebook-video.git ~/.agents/skills/notebook-video` | `.agents/skills/notebook-video` |

### Option D: local regression self-test (no render)

```bash
python scripts/selftest.py
```

---

---

## 📚 Worked example, end to end

Say you want a three-minute explainer on whether a new model is worth switching to. Four commands, no hand-edited frame numbers:

```text
# 1. Create the project (copy the template, lock a skin)
node scripts/notebook-video.mjs new-project ./my-video --style=cel

# 2. Write the narration and the subtitle lines (the two files must reconstruct each other;
#    write numbers the way they are spoken)
python <template>/scripts/tts-openai-compatible.py ./my-video     # TTS + word timings
python <template>/scripts/speed-post.py ./my-video 1.10           # deterministic pace fix
node scripts/notebook-video.mjs build-semantic-captions audio/narration.mp3.json manifests/semantic-caption-lines.txt manifests/caption-cues.json

# 3. Write the shot table — semantics only ("which sentences does this shot cover"), never frames
#    manifests/shots.json -> resolve-shots.py derives frames and camera keyframes

# 4. Gates, then render
python scripts/validate-frame-props.py ./my-video     # frame-prop names (the most common silent failure)
python scripts/validate-shot-motion.py ./my-video     # out-of-bounds proof / pan budget / move quotas
python scripts/validate-composition.py ./my-video     # skeletons / media / enums / pacing
python scripts/validate-audio-levels.py ./my-video    # sound effects may not be mastered too quietly
node scripts/notebook-video.mjs render ./my-video out.mp4
```

Runtime gates additionally stop text overlap, clipped cards and over-wide captions —
**a non-zero P0 count blocks the render** instead of surfacing when you watch the film frame by frame.

---

## ⚙️ Requirements

- **Node.js 18+** (Remotion render engine)
- **ffmpeg** (frame extraction, contact sheet, loudness normalisation; needed for QA)
- Before the first render, run `node scripts/notebook-video.mjs check-deps` to verify the environment and prepare the Chromium kernel

Frequently used commands (full list in `--help`):

```text
node scripts/notebook-video.mjs new-project   ./my-video --style=paper
node scripts/notebook-video.mjs resolve-shots ./my-video
python scripts/validate-frame-props.py        ./my-video
python scripts/validate-shot-motion.py        ./my-video
python scripts/validate-composition.py        ./my-video
node scripts/notebook-video.mjs showcase      ./my-video     # component contact sheet
node scripts/notebook-video.mjs render        ./my-video out.mp4
node scripts/notebook-video.mjs review-frames ./my-video r.mp4 0 570
```

---

---

## 🔒 Security and privacy

- **Read-only inspection first**: dependency and pre-flight checks only measure; they never change system environment variables or system configuration.
- **Zero-token local run**: rendering and all gates run on your machine with no online API quota; narration goes to your own TTS endpoint and the key is read from the environment only, never written to disk.
- **Deterministic and reproducible**: everything is code-driven; every animation is a pure function of the frame number (no `Math.random`, no CSS animations or timers). Scope matters: **stills / PNGs are byte-reproducible** (the same frame rendered twice hashes identically — that is how the contact sheet is verified), while **long MP4 segments are not**: x264's threading/look-ahead decisions make two consecutive 900-frame renders differ in md5, with pixel differences confined to a few edge pixels (max 76, mean 0.12, 95.2% of bytes identical) — encoder-level noise, not a content change.
- **Gates before prose**: whatever can be proved arithmetically at build time is checked there; only measurements that need real fonts and layout run in the browser.
- **Complete source delivery**: the MP4 ships together with the full, clean Remotion React source tree.

---

---

## 📥 Download

| Method | Command / link |
| --- | --- |
| **HTTPS** | `git clone https://github.com/hyt315/notebook-video.git` |
| **SSH** | `git clone git@github.com:hyt315/notebook-video.git` |
| **ZIP** | [Download ZIP](https://github.com/hyt315/notebook-video/archive/refs/heads/main.zip) |
| **Single file** | `curl -O https://raw.githubusercontent.com/hyt315/notebook-video/main/SKILL.md` |
| **Version history** | `CHANGELOG.md` |

---

---

## 📁 File Structure

```
notebook-video/
├── SKILL.md                          # Core skill definition and production workflow
├── manifest.json                     # Skill metadata (version lives here)
├── README.md / README.en.md          # Chinese / English documentation
├── CHANGELOG.md                      # Version history (currently v3.1.2)
├── LICENSE                           # Apache License 2.0
├── NOTICE                            # Third-party font / asset / dependency notices
├── CONTRIBUTING.md · CODE_OF_CONDUCT.md · SECURITY.md · SUPPORT.md
├── assets/
│   ├── demo/                         # Finished films & previews
│   ├── lecture-template/             # Official template (pure-code route, 8-shot example film)
│   └── example-project/              # Classic route example (optional image add-on)
├── scripts/                          # Python 3 stdlib / Node only — zero third-party deps
│   ├── notebook-video.mjs            # Cross-platform runner (incl. the showcase command)
│   ├── resolve-shots.py              # Shot table → frame numbers and camera keyframes
│   ├── validate-shot-motion.py       # Build-time: camera out-of-bounds proof + move quotas
│   ├── validate-composition.py       # Build-time: skeletons / live components / media / density
│   ├── validate-caption-sync.py      # Caption vs TTS word-boundary consistency
│   ├── validate-semantic-breaks.py   # Protected phrases never split
│   └── selftest.py                   # End-to-end regression suite
└── references/                       # Load-on-demand specs and manuals
    ├── scene-authoring.md            # ★ Scene authoring guide (copy this shape)
    ├── shot-language.md              # Camera intents, zoom budgets, out-of-bounds proof
    ├── scene-skeletons.md            # The four skeletons and the shot-table schema
    ├── media-routing.md              # Content→medium routing, A/B scenes, background contract
    ├── composition-gate.md           # Every gate's criteria and its fix
    ├── motion-design.md              # Multi-clock motion rules
    └── theme-*.md / visual-system.md # The four skin contracts
```

Source layers inside the template (`assets/lecture-template/src/`):

```
index.tsx           Engine: canvas / captions / chapter card / asset gate / runtime gates + shot handoff
shotkit.tsx         Shot layer: ShotCamera / 6 intents / anchor proof / depth layers / backing plate
stagekit.tsx        Skeleton "Stage": StageFrame + state machine + PhaseRail + SlotGuard（Attach 已删）
skeletons.tsx       Skeletons "Corridor" / "Split" / "Zoom"
media.tsx           Media: ConsoleWindow / MetricGrid / StampBanner
fxkit.tsx          motion components (FitCard / Typewriter / StampSeal / Funnel / ChatThread / ProgressRing / StaggerList / DiffView / SkeletonCard) — frame-driven
toolkit.tsx         rhetorical tools (Callout / Checklist / JumpInText)
│   └── components/       wrapped component layer (Accordion / Tabs / HighlightCode / Chart / StatRow / GlowFrame / PathDraw / FitTextBox …)
kit.tsx             Theme-agnostic atoms: PillTag / LineIcon / CheckBadge / TYPE
insert.tsx          B-roll inserts + the three transitions (cut / handoff / reveal)
overlap-gate.tsx    Runtime overlap / occlusion gate
clipping-gate.tsx   Runtime clipped-graphics gate (SVG primitives crossing a clipping ancestor)
canvas-bounds-gate.tsx Runtime canvas-bounds gate (text-bearing leaf elements whose ink rect leaves the canvas; blocks on the contact sheet, warns in a film)
fill-gate.tsx       Runtime measured density of the lower quarter (lowest info-element edge vs y=876)
showcase.tsx        Component contact sheet (18 pages, for AI to pick by sight)
scenes.tsx          Scene layer (8-shot example film; rewrite this layer per topic)
```

---

---

## ❓ FAQ

- **Q: How do you keep the result from looking like a slide deck?**\
  A: Four layers, all backed by gates — ① four structurally different skeletons with **no adjacent repeats**; ② **at least three visual media per film** and at least one live component per explanation scene; ③ at least three camera moves per chapter (budgeted by film length), so the framing really changes; ④ a gate blocks the render when P0 is non-zero.

- **Q: How do you guarantee text never collides or gets covered?**\
  A: At runtime **`OverlapGate`** samples every 15 frames and detects both text-vs-text overlap and paint-order occlusion (measuring real glyph rects with `Range.getClientRects()`), **`ClippingGate`** catches graphics clipped by an `overflow` ancestor or an `<svg>` viewport (the text gates cannot see a half-missing shape), **`CanvasBoundsGate`** catches **text-bearing leaf elements whose ink rect leaves the canvas** (a whole element cut off by the canvas edge; it blocks on the contact sheet and only warns in a film), **`FillGate`** measures whether the lower quarter is really filled (lowest edge of real information elements vs y=876 — the build-time check only reads whether the declared field exists), and **`SlotGuard`** reports how much of `StageFrame`'s main slot is actually used. Intentional overlaps (shot handoff, header swap, metric value replacement) must be declared with `data-gate-allow` — the allow-list may never hide two different pieces of information colliding. After the render, run **`validate-motion-gaps`** — a stretch where nothing moves is only visible there.

- **Q: Do I need to re-time everything after editing the script?**\
  A: No. The shot table only references cues; frame numbers, camera keyframes and SFX pinning are all derived from the TTS word timestamps by `resolve-shots.py`.

- **Q: Do I need expensive image generation AI models?**  
  A: No. The default Lecture Composition route uses 100% React + SVG code drawing with zero image generation costs.
- **Q: How does it ensure subtitles never overflow?**  
  A: The skill integrates `CaptionFitGate`, calculating exact pixel-level widths for every word before rendering.
- **Q: What formats are supported?**  
  A: Outputs standard 2K H.264/AAC MP4 videos compatible with YouTube, Bilibili, TikTok, and social platforms.

---

---

## 🤝 Contributing

Contributions are welcome! See `CONTRIBUTING.md`. If this skill helped you, please give it a [Star ⭐](https://github.com/hyt315/notebook-video/stargazers)!

---

---

## 📄 License

Released under Apache License 2.0 (full text in the LICENSE file at the repo root). Licences and attribution for bundled third-party material (the LXGW WenKai typeface, sound effects, Remotion dependencies, TTS providers) are recorded in NOTICE; the dependency inventory is in `DEPENDENCIES.md`.

---

