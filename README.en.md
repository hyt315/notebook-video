<div align="center">

# 📓 Notebook Video / 手账风教学视频制作

**Create 2K Chinese explainer videos entirely in code: React + SVG + Remotion, frame-accurate TTS word-timing, no image-generation model required.**

**English · [简体中文](./README.md)**

[![License: MIT](https://img.shields.io/github/license/hyt315/notebook-video)](LICENSE)
[![Release](https://img.shields.io/github/v/release/hyt315/notebook-video?sort=semver)](https://github.com/hyt315/notebook-video/releases)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-1f6feb)](SKILL.md)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](SKILL.md)
[![Remotion](https://img.shields.io/badge/Remotion-4.0-ff6b6b)](https://remotion.dev)
[![Stars](https://img.shields.io/github/stars/hyt315/notebook-video?style=social)](https://github.com/hyt315/notebook-video/stargazers)

</div>

---

## 📖 What is this?

Science explainers, notebook-style animations, product promos, concept walkthroughs — **Notebook Video** is an AI Agent Skill that builds **2K warm-ivory engineering-notebook videos** with React, TypeScript and Remotion. The **default visual route is Lecture Composition**: multi-zone scenes drawn entirely with code (SVG diagrams, mascots, progressive checklists, annotation stickers), synchronized frame-accurately to Chinese TTS word timing — **no image-generation model required** (image generation is an optional add-on). Outputs H.264/AAC MP4 + an editable Remotion source package.

### ✨ Core Features

| Feature | Description |
|---------|-------------|
| 🎬 **Code-driven video** | Drawn with React + TypeScript + Remotion; SVG diagrams & animations fully controlled by code, reproducible in any AI environment |
| 📝 **Chinese TTS narration** | Frame-accurate word-timing sync, auto-generated semantic captions and sound effects, multiple model platforms supported |
| 🎨 **Lecture Composition default route** | Multi-zone scenes (content area + mascot + annotation stickers), pure code-drawn, no image generation needed |
| 🖼️ **Optional image add-on** | For photographic hero visuals, generate images for specific hero scenes (Visual Director route, `--classic` template) |
| 📐 **Three canvases** | 16:9 (2560×1440), 4:3 (1920×1440), 3:4 portrait, with a built-in mobile-readability type floor |
| ✅ **Automated QA** | Caption width measured gate (CaptionFitGate), layering validation, semantic break validation, visual plan validation and more |
| 🔄 **Cross-platform unified commands** | One Node launcher behaves identically on macOS Terminal / Windows CMD / PowerShell |

---

## 📚 Demo

![Notebook Video demo](assets/demo/notebook-video-demo.webp)

▶️ [Watch the full demo video (MP4)](assets/demo/notebook-video-demo.mp4) · Hero visual: [hero.png](assets/demo/hero.png)

**Three canvas versions** (same project, switched by the `CANVAS` flag):

| Canvas | Preview | Download |
| --- | --- | --- |
| 16:9 landscape (default) | [![16:9](assets/demo/notebook-video-demo.webp)](assets/demo/notebook-video-demo.mp4) | [notebook-video-demo.mp4](assets/demo/notebook-video-demo.mp4) |
| 4:3 mobile-friendly | [![4:3](assets/demo/notebook-video-demo-43.webp)](assets/demo/notebook-video-demo-43.mp4) | [notebook-video-demo-43.mp4](assets/demo/notebook-video-demo-43.mp4) |
| 3:4 portrait (Douyin) | [![3:4](assets/demo/notebook-video-demo-34.webp)](assets/demo/notebook-video-demo-34.mp4) | [notebook-video-demo-34.mp4](assets/demo/notebook-video-demo-34.mp4) |

> This is the real output style of the lecture-template route: warm-ivory notebook surface, code-drawn multi-zone scenes, word-level synced captions.

---

## 🚀 Quick Start

> ✨ **One-liner install into your AI agent**: paste this to your AI assistant and it will install itself:
>
> ```text
> Please install the notebook-video Skill: clone https://github.com/hyt315/notebook-video into your skills directory (Claude Code: ~/.claude/skills/notebook-video/; Cursor: ~/.cursor/skills/; Codex/ChatGPT: .agent/skills/ in your project), and verify that SKILL.md, references/, and scripts/ are all present. Whenever I want to create a "science explainer video / notebook-style animation / product promo / concept walkthrough", follow the SKILL.md workflow and use the Lecture Composition route.
> ```

### Install command (one line)

| Platform | Install |
|----------|---------|
| **Claude Code** | `git clone https://github.com/hyt315/notebook-video.git ~/.claude/skills/notebook-video` |
| **Codex** | `git clone https://github.com/hyt315/notebook-video.git ~/.codex/skills/notebook-video` |
| **Cursor** | `git clone https://github.com/hyt315/notebook-video.git ~/.cursor/skills/notebook-video` |

### Skills directory paths

| Platform | Personal (global) | Project-level |
|----------|-------------------|---------------|
| **Claude Code** | `~/.claude/skills/` | `.claude/skills/` (project root) |
| **Codex** | `~/.codex/skills/` | `.codex/skills/` (project root) |
| **Cursor** | `~/.cursor/skills/` | `.cursor/skills/` or `.agents/skills/` (project root) |

> Each Skill must live in its own folder — never drop SKILL.md directly into the skills/ root.

---

## 💬 When to trigger

Say any of these to your AI agent to trigger this skill:

- "Make a science explainer video" / "notebook-style animation" / "stop-motion style"
- "Make an AI video" / "product promo"
- "Introduce a concept" / "explain a product or skill"
- "Create a 30-second to several-minute video" / "turn website animation into MP4"
- "Add Chinese narration/subtitles/SFX" / "quickly generate a 2K video"

## ⚙️ Prerequisites

- **Node.js** (for the unified launcher and Remotion rendering)
- Browser kernel (`prepare-browser` sets up Chromium automatically before first render)
- A Chinese TTS service (any supported model platform)
- Unsure about dependencies? Run a check: `node "<SKILL_DIR>/scripts/notebook-video.mjs" check-deps`

## 📦 Deliverables

A full production delivers (unless you ask for less):

1. Narration script + time-coded storyboard
2. Visual plan marking each scene as `image-text`, `pure-text` or `pure-graphic`
3. Semantic part manifest with layer and exit contracts
4. `visual-assets.json` with source, prompt summary, crop policy and rights for every raster
5. Chinese narration + word-timing JSON
6. One-line semantic caption cues + protected-phrase manifest
7. Delivery-canvas H.264/AAC MP4 (2560×1440 or 1920×1440)
8. 24-frame contact sheet and motion checks for long films
9. Editable source ZIP with fonts, licenses, audio and manifests

---

## 📥 Download / Install

```bash
# HTTPS
git clone https://github.com/hyt315/notebook-video.git

# SSH
git clone git@github.com:hyt315/notebook-video.git

# GitHub CLI
gh repo clone hyt315/notebook-video

# ZIP
# https://github.com/hyt315/notebook-video/archive/refs/heads/main.zip

# Single file (SKILL.md only)
curl -O https://raw.githubusercontent.com/hyt315/notebook-video/main/SKILL.md
```

---

## 📁 File Structure (Core)

```
notebook-video/
├── SKILL.md                     # entry point (11-step production workflow)
├── references/                  # 18 reference manuals (visual system/composition/captions/performance/QA/cross-platform)
├── scripts/
│   └── notebook-video.mjs       # unified Node launcher (check-deps/new-project/render/package…)
├── assets/
│   ├── lecture-template/        # default route template (pure-code Lecture Composition, 30s film)
│   ├── example-project/         # classic route exemplar (Visual Director, with image add-on)
│   └── fonts/                   # Chinese fonts (Source Han Sans + Smiley Sans, licensed)
├── agents/openai.yaml
├── LICENSE / NOTICE
├── README.md  /  README.en.md  # bilingual docs (this file is English)
├── CHANGELOG.md
├── .github/                     # Issue/PR templates + CI(validate) + Dependabot
└── CONTRIBUTING.md / CODE_OF_CONDUCT.md / SECURITY.md
```

---

## ▶️ Quick Usage

Everything runs through the **unified Node launcher** (identical on macOS Terminal / Windows CMD / PowerShell):

```bash
# 0. Dependency check + skill self-check
node "<SKILL_DIR>/scripts/notebook-video.mjs" check-deps
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-skill

# 1. Create a new project (lecture template by default; --classic for the image add-on route)
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project ./notebook-video-project

# 2. Prepare browser kernel (before first render)
node "<SKILL_DIR>/scripts/notebook-video.mjs" prepare-browser ./notebook-video-project

# 3. Produce via the 11-step workflow in SKILL.md (lock content → direct visuals → TTS → layers → animate → render → validate)

# 4. Package the deliverable source ZIP
node "<SKILL_DIR>/scripts/notebook-video.mjs" package ./notebook-video-project ./source.zip
```

Two template routes:

| Route | Command | Best for |
|-------|---------|----------|
| **Lecture (default)** | `new-project ./dir` | Pure code-drawn multi-zone composition, no image generation |
| **Classic** | `new-project ./dir --classic` | Image-plus-text callouts with physical slot insertion, when accepting the image add-on |

---

## 🤝 Contributing / Feedback

- Report bugs / suggestions: use the repo's Issue templates
- Contribute: see [CONTRIBUTING.md](CONTRIBUTING.md); run `validate-skill` and related validation scripts before any PR
- Security: see [SECURITY.md](SECURITY.md) (private vulnerability reporting, not public issues)

---

## 📜 License

[MIT](LICENSE) © 2026 hyt315 · Remotion components see [NOTICE](NOTICE)

> 🌏 **中文版: [README.md](./README.md)**