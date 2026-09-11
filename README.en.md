# 📦 Notebook Video / Hand-drawn explainer videos

<div align="center">

**把一句话变成一支 2K 中文教学视频：纯代码绘制场景、帧精确对齐配音、镜头语言由门禁托底。**

**Turn one sentence into a 2K Chinese explainer video: code-drawn scenes, frame-accurate TTS sync, camera language enforced by automated gates.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/hyt315/notebook-video?sort=semver)](https://github.com/hyt315/notebook-video/releases)
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
| **Eight quality gates** | 4 build-time: shot→frame resolution, out-of-bounds proof, composition & density, **frame-prop-name check**; 4 runtime: caption width, card overflow, **text-vs-text overlap and occlusion**, slot overflow | A non-zero P0 **blocks the render**; each gate also logs coverage so **"no warning" and "never ran" are distinguishable** |
| **Material plates** | Real screenshots / official charts sit inside the locked cel frame (2.5px ink outline + hard shadow) with a caption and a source line, and can drift slowly toward the point that matters; assets are registered in **both** `visual-assets.json` and `asset-manifest.json` (source / rights / baked text / checksum) | For claims that need "this really is the official thing"; anything a diagram explains better stays drawn |
| **Frame-accurate Chinese TTS sync** | Millisecond word timings → semantic sentence breaks → animation beats; trailing punctuation strictly stripped | No drifting captions, no audio-visual mismatch |
| **Four locked skins** | `paper` (warm ivory notebook, default) / `cel` (anime cel) / `sticker` / `flat` | One script, four moods |
| **Background readability contract** | The locked background bitmap is **never altered**; content that sits over decoration rides a **semi-transparent** feathered plate (panel 88%, plate centre 76%) | Readability without a solid white board — the film does not turn into a white slide |

---

---

## 🎨 Visual Demos & Aspect Ratios

![Notebook Video Demo](assets/demo/notebook-video-demo.webp)

▶️ [Watch full demo video (MP4)](assets/demo/notebook-video-demo.mp4) · Hero Asset: [hero.png](assets/demo/hero.png)

▶️ [Component library showcase (v2.5, 54s)](assets/demo/notebook-video-components-demo.mp4) — 26 locked icons, seven components (CodeBlock / BrowserChrome / Connector / Checklist / CountUp / ProgressBar / Callout), three transitions, type motion, physical parts and all four theme skins, rendered in the cel theme.

**Canvases**: three are locked — 16:9 (2560×1440), 4:3 (1920×1440) and 3:4 portrait (1440×1920), all native 30 fps. The bundled example film is authored in the **16:9 design space**; 4:3 / 3:4 need their own dedicated layout pass (**letterbox scaling is no longer presented as adaptation**).

### Default Canvas: 16:9 Landscape

| Aspect Ratio | Resolution | Video Demo | Best For |
|---|---|---|---|
| **16:9 Landscape** (Default) | 2560×1440 (2K) | [![16:9](assets/demo/notebook-video-demo.webp)](assets/demo/notebook-video-demo.mp4) | YouTube / Desktop / Lecture Walkthroughs |

---

---

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
  ⑦ Runtime gates + delivery ── CaptionFitGate / CardFitGate / OverlapGate / SlotGuard
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
- **Deterministic and reproducible**: everything is code-driven; every animation is a pure function of the frame number (no `Math.random`, no CSS animations or timers).
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
| **Version history** | [CHANGELOG.md](CHANGELOG.md) |

---

---

## 📖 Where to read what

`references/` loads on demand, not all at once. The order that matters most:

| When | File | Why |
|---|---|---|
| **Before anything** | `locked-style-contract.json` | binding tokens, coordinates, rejection flags |
| **Before writing scenes** | `scene-authoring.md` · `scene-skeletons.md` | the canonical scene shape, four skeletons, ten recurring pitfalls |
| **Before choosing a component** | the gesture→component table in `media-routing.md` · `fxkit.md` | which component fits this rhetorical move, **when not to use it**, and the `frame` vs `f` trap |
| **Before the shot table** | `media-routing.md` · `shot-language.md` | content→medium routing, six camera intents, zoom and pan budgets |
| **Before writing** | `narrative-hook.md` · `pacing-rhythm.md` | the first three seconds, chapter energy and breathing |
| **Before delivery** | `composition-gate.md` · `quality-checklist.md` | every gate's criteria, the fix runbook, the delivery fact card |
| **Audio and captions** | `tts-audio.md` · `subtitle-timing.md` | polyphones, pace, word timings, sound vocabulary |
| **When something breaks** | `windows-compatibility.md` · `cross-platform-compatibility.md` · `performance-design.md` | platforms, paths, render performance |

---

## 📁 File Structure

```
notebook-video/
├── SKILL.md                          # Core skill definition and production workflow
├── manifest.json                     # Skill metadata (version lives here)
├── README.md / README.en.md          # Chinese / English documentation
├── CHANGELOG.md                      # Version history (currently v2.9.0)
├── LICENSE                           # MIT License
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
stagekit.tsx        Skeleton "Stage": StageFrame + state machine + PhaseRail + Attach + SlotGuard
skeletons.tsx       Skeletons "Corridor" / "Split" / "Zoom"
media.tsx           Media: ConsoleWindow / MetricGrid / StampBanner
fxkit.tsx
toolkit.tsx         rhetorical tools (Callout / Connector / WaveText / JumpInText / CountUp / Checklist / CodeBlock / BrowserChrome)
plates.tsx          ShotPlate — real screenshots and official charts inside the locked frame           18 motion components (multi-clock motion)
kit.tsx             Theme-agnostic atoms: PillTag / LineIcon / CheckBadge / TYPE
insert.tsx          B-roll inserts + the five transitions
overlap-gate.tsx    Runtime overlap / occlusion gate
showcase.tsx        Component contact sheet (6 pages, for AI to pick by sight)
scenes.tsx          Scene layer (8-shot example film; rewrite this layer per topic)
```

---

---

## ❓ FAQ

- **Q: How do you keep the result from looking like a slide deck?**\
  A: Four layers, all backed by gates — ① four structurally different skeletons with **no adjacent repeats**; ② **at least three visual media per film** and at least one live component per explanation scene; ③ at least three camera moves per chapter (budgeted by film length), so the framing really changes; ④ a gate blocks the render when P0 is non-zero.

- **Q: How do you guarantee text never collides or gets covered?**\
  A: A runtime **`OverlapGate`** samples every 15 frames and detects both text-vs-text overlap and paint-order occlusion (measuring real glyph rects with `Range.getClientRects()`), plus **`SlotGuard`** for content wider than its slot. Intentional overlaps (shot handoff, header swap, metric value replacement) must be declared with `data-gate-allow` — the allow-list may never hide two different pieces of information colliding.

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

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md). If this skill helped you, please give it a [Star ⭐](https://github.com/hyt315/notebook-video/stargazers)!

---

---

## 📄 License

Released under the [MIT License](LICENSE).

---

