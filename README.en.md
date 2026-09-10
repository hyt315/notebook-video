# 📓 Notebook Video / notebook-video

<div align="center">

**Programmatic 2K animated video engine with React, SVG and Remotion — frame-accurate TTS synchronization with zero image model dependencies.**

**用代码绘制 2K 中文教学视频：React + SVG + Remotion，帧精确同步 TTS 配音，多画布比例适配。**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/hyt315/notebook-video?sort=semver)](CHANGELOG.md)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-1f6feb)](SKILL.md)
[![Remotion](https://img.shields.io/badge/Remotion-4.0-ff6b6b)](https://remotion.dev)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](SKILL.md)
[![GitHub Stars](https://img.shields.io/github/stars/hyt315/notebook-video?style=social)](https://github.com/hyt315/notebook-video/stargazers)

[English](./README.en.md) | [中文](./README.md)

</div>

---

## 📖 What is this?

Explainer videos, animated educational lectures, product showcases, or technical walkthroughs — **Notebook Video** is a professional-grade video creation skill built for AI Agents. It programmatically renders warm 2K notebook-style videos using **React, TypeScript, and Remotion**.

**The default path is pure code-drawn composition**: all SVG diagrams, mascots, checklists and annotations are drawn in code and frame-accurately synchronised with TTS word timings — **no image-generation model required**. Outputs crisp H.264/AAC 2K MP4 plus a fully editable Remotion source package.

This release (v2.9.0) fixes the two failure modes AI-made videos hit most often:

- **It looked like a slide deck.** Every scene used to be the same "card + text" layout. Now there are **four structurally different scene skeletons**, a **content → medium routing table**, and a **per-shot restricted camera** — all enforced by gates.
- **Text collided and got covered.** The old checks only caught text overflowing its own card. There is now a **runtime overlap/occlusion gate** that tells you exactly which frame, which two texts, and how many pixels.

The existing strengths are unchanged: word-accurate caption sync, real-font measurement, four locked skins, zero third-party Python dependencies.

---

## ✨ Key Features

| Core Module | Capabilities | Value Delivered |
|---|---|---|
| 🎬 **Code-Driven Rendering** | React + TypeScript + Remotion; every SVG and animation is a pure function of the frame number | Identical output on any machine, no image model required |
| 🎥 **Shot layer (restricted recipes + out-of-bounds proof)** | Each shot declares one of six camera intents (establish / push-in / pull-back / pan-follow / reveal / micro-orbit) plus an `anchor`; a build-time check proves arithmetically that the anchor stays inside the frame at every keyframe | The camera really moves — and **can never push the narrated content off screen** |
| 🧩 **Four scene skeletons** | `Stage` (one subject evolving) / `Corridor` (an object travelling a track) / `Split` (two columns) / `Zoom` (whole → focus → annotate → back). **No two adjacent scenes may share a skeleton; at least three per film** | Structurally eliminates the "four identical slides" problem |
| 🎯 **Content → medium routing** | Console window / chart / code patch / display type / metric grid / diagram. **At least three media per film, and at least one live state-changing component per explanation scene** | The frame is no longer only "card plus text" |
| 🗂 **Shot table + resolver** | The shot table only declares *which narration cues a shot covers*; frame numbers are derived from the TTS word timestamps by `resolve-shots.py` | Rewrite the script without hand-editing dozens of frame numbers; SFX pinning follows automatically |
| 📝 **Frame-Accurate TTS Sync** | Millisecond word timestamps → semantic captions → animation beats; trailing punctuation strictly stripped | Eliminates subtitle misalignment and audio-video desync |
| ✅ **Six quality gates (2 build-time + 4 runtime)** | Build-time: camera out-of-bounds proof, composition & diversity. Runtime: caption width, card overflow, **text-vs-text overlap and occlusion**, **slot overflow** | Gates **refuse to render**, instead of just documenting a rule |
| 🎨 **Four locked skins** | paper (default) / cel / sticker / flat | One script, four aesthetics |
| 🔒 **Background readability contract** | The locked background bitmaps are kept untouched; content that overlaps a decoration sits on a feathered backing plate | The art stays, the text stays readable |
| 🖼️ **Optional image add-on** | The `--classic` template can use real or generated imagery for concrete hero scenes, with provenance recorded | Off by default, zero cost |

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

## 🚀 Quick Start

This is an AI Agent Skill — install it into your AI assistant and you're ready.

### Option A: Paste one sentence into any Agent (recommended, most universal)

Send this to your AI assistant and it will detect the platform and clone to the right skills directory:

> Please install the notebook-video skill: clone `https://github.com/hyt315/notebook-video` into your skills directory (e.g. `~/.claude/skills/notebook-video` or `~/.agents/skills/notebook-video`) and confirm it works. When I ask to make an educational video, concept explainer, or showcase, follow the workflow in SKILL.md to generate a 2K video.

### Option B: GitHub CLI 2.90+ (one command)

```bash
gh skill install hyt315/notebook-video notebook-video --agent claude-code --scope user
```

### Option C: Manual per-platform install

| Platform | User-level Path | Project-level Path |
|---|---|---|
| **Claude Code** | `git clone https://github.com/hyt315/notebook-video.git ~/.claude/skills/notebook-video` | `.claude/skills/notebook-video` |
| **Codex** | `git clone https://github.com/hyt315/notebook-video.git ~/.codex/skills/notebook-video` | `.codex/skills/notebook-video` |
| **Cursor** | `git clone https://github.com/hyt315/notebook-video.git ~/.cursor/skills/notebook-video` | `.cursor/skills/notebook-video` |
| **General Agents** | `git clone https://github.com/hyt315/notebook-video.git ~/.agents/skills/notebook-video` | `.agents/skills/notebook-video` |

### Option D: Run local regression selftest

```powershell
python scripts/selftest.py
```

---

## ⚙️ Prerequisites & Dependency Check

- **Node.js 18+** (required for Remotion engine);
- Run dependency preflight check: `node scripts/notebook-video.mjs check-deps`.

---

## 🔒 Safety & Reproducibility Principles

- **Zero-Harm Preflight**: Dependency verification runs read-only without modifying system environments;
- **Deterministic Output**: Pure code-driven animation guarantees identical output across renders;
- **Full Source Delivery**: Delivers both final 2K MP4 video and editable Remotion React source code.

---

## 📥 Download

| Method | Command / Link |
|---|---|
| **HTTPS** | `git clone https://github.com/hyt315/notebook-video.git` |
| **SSH** | `git clone git@github.com:hyt315/notebook-video.git` |
| **GitHub CLI** | `gh repo clone hyt315/notebook-video` |
| **ZIP** | [Download ZIP](https://github.com/hyt315/notebook-video/archive/refs/heads/main.zip) |
| **Tarball** | [Download Tar](https://github.com/hyt315/notebook-video/archive/refs/heads/main.tar.gz) |
| **Single file (SKILL.md)** | `curl -O https://raw.githubusercontent.com/hyt315/notebook-video/main/SKILL.md` |

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
fxkit.tsx           18 motion components (multi-clock motion)
kit.tsx             Theme-agnostic atoms: PillTag / LineIcon / CheckBadge / TYPE
insert.tsx          B-roll inserts + the five transitions
overlap-gate.tsx    Runtime overlap / occlusion gate
showcase.tsx        Component contact sheet (6 pages, for AI to pick by sight)
scenes.tsx          Scene layer (8-shot example film; rewrite this layer per topic)
```

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

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md). If this skill helped you, please give it a [Star ⭐](https://github.com/hyt315/notebook-video/stargazers)!

---

## 📌 Version note

- **v2.9.0 (current)** — the main line. It absorbs the good ideas from the earlier v2.9 / v3.0 experiments (restricted camera recipes, content routing, a structured shot table) while fixing what made them worse (v2.9 dropped the mandatory clauses and the films became empty; v3.0 traded creative freedom for "limited-length text" and flattened the delivery). **The v2.9 and v3.0 branches and their old tags have been deleted; only `main` remains.**

---

## 📄 License

Licensed under the [MIT License](LICENSE).

---

> 🌏 **中文版: [README.md](./README.md)**
