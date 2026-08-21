<div align="center">

# 📓 Notebook Video / 手账风教学视频制作

**Create 2K Chinese explainer videos entirely in code: React + SVG + Remotion, frame-accurate TTS word-timing, no image-generation model required.**

**English · [简体中文](./README.md)**

[![License: MIT](https://img.shields.io/github/license/hyt315/notebook-video)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-1f6feb)](SKILL.md)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](SKILL.md)
[![Remotion](https://img.shields.io/badge/Remotion-4.0-ff6b6b)](https://remotion.dev)

</div>

---

## What is this?

Create science explainer videos, notebook-style animations, product promos, or concept walkthroughs — **Notebook Video** is an AI Agent Skill that builds **2K warm-ivory engineering-notebook videos** with React, TypeScript and Remotion. The **default visual route is Lecture Composition**: multi-zone scenes drawn entirely with code (SVG diagrams, mascots, progressive checklists, annotation stickers) synchronized frame-accurately to Chinese TTS word timing, so production never depends on an image-generation model (image generation is an optional add-on). Outputs H.264/AAC MP4 + editable Remotion project.

### Core Features

| Feature | Description |
|---------|-------------|
| 🎬 **Code-driven video** | React + TypeScript + Remotion; SVG diagrams & animations fully controlled by code, reproducible in any AI environment |
| 📝 **Chinese TTS** | Frame-accurate TTS word-timing sync, auto-generated subtitles and sound effects |
| 🎨 **Lecture Composition** | Multi-zone scenes (content area + mascot + annotation stickers), no image-generation model required |
| 🚀 **One-command project** | `new-project` creates a full Remotion project from a template (lecture or classic), ready to edit |
| ✅ **Automated QA** | Multiple validation scripts (caption sync, layering, semantic breaks, visual plan) ensure output quality |
| 🔄 **Cross-platform** | Scripts for Windows/macOS/Linux (cmd + sh), support for multiple model platforms |

---

## 🚀 Quick Start

> ✨ **One-liner install into your AI agent**: paste this to your AI assistant and it will install itself:
>
> ```text
> Please install the notebook-video Skill: clone https://github.com/hyt315/notebook-video into your skills directory (Claude Code: ~/.claude/skills/notebook-video/; Cursor: ~/.cursor/skills/; Codex/ChatGPT: .agent/skills/ in your project), and verify that SKILL.md, references/, and scripts/ are all present. Whenever I want to create a "science explainer video / notebook-style animation / product promo / concept walkthrough", follow the SKILL.md workflow and use the Lecture Composition route.
> ```

Then pick your platform:

| Platform | Install |
|----------|---------|
| **Claude Code** | `git clone https://github.com/hyt315/notebook-video.git ~/.claude/skills/notebook-video` |
| **Cursor** | `git clone https://github.com/hyt315/notebook-video.git ~/.cursor/skills/notebook-video` |
| **Codex / ChatGPT** | `.agent/skills/notebook-video/` in your project (with `agents/openai.yaml`) |
| **Generic** | Any agent's skills directory |

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
├── SKILL.md                     # entry point
├── references/                  # 18 reference manuals (visual system/composition/captions/performance/QA)
├── scripts/                     # validation/creation/rendering/packaging scripts (cmd + sh)
├── assets/
│   ├── lecture-template/        # default route template (pure-code Lecture Composition)
│   ├── example-project/         # classic route exemplar (with optional image generation)
│   └── fonts/                   # Chinese fonts (Source Han Sans + Smiley Sans)
├── agents/openai.yaml
├── LICENSE / NOTICE
├── README.md  /  README.en.md  # bilingual docs (this file is English)
├── CHANGELOG.md
├── .github/                     # Issue/PR templates + CI + Dependabot
└── CONTRIBUTING.md / CODE_OF_CONDUCT.md / SECURITY.md
```

---

## ▶️ Quick Usage

Initialize project → edit scenes → render:

```bash
# 1. Create a new project (from template)
node scripts/new-project.mjs my-video

# 2. Enter project directory
cd my-video

# 3. Install dependencies
npm install

# 4. Preview in browser
npm run dev

# 5. Render final MP4
npm run render
```

See the full workflow in SKILL.md and references in `references/`.

---

## 🤝 Contribute / Feedback

- Report bugs / suggestions: use the repo's Issue templates
- Contribute: see [CONTRIBUTING.md](CONTRIBUTING.md); run validation scripts before any PR
- Security: see [SECURITY.md](SECURITY.md) (private vulnerability reporting, not public issues)

---

## 📜 License

[MIT](LICENSE) © 2026 hyt315 · Remotion components see [NOTICE](NOTICE)

> 🌏 **中文版: [README.md](./README.md)**