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

**The default path is Lecture Composition (multi-zone pure code layout)**: All SVG diagrams, mascot graphics, checklists, and annotations are rendered directly in code, frame-accurately synchronized with TTS word timings — **completely eliminating dependencies on external AI image generation models**. Outputs crisp H.264/AAC 2K MP4 video along with fully editable Remotion source packages.

---

## ✨ Key Features

| Core Module | Capabilities | Value Delivered |
|---|---|---|
| 🎬 **Code-Driven Rendering** | React + TypeScript + Remotion renders; all SVGs and animations controlled purely via code | 100% consistent aesthetic reproduction across any AI environment |
| 📝 **Frame-Accurate TTS Sync** | Millisecond-level word timestamp alignment with automatic semantic captions & sound cues | Eliminates subtitle misalignment and audio-video desync |
| 📐 **3 Aspect Ratio Matrix** | 16:9 (2560×1440 2K Landscape), 4:3 (Classic), 3:4 (Portrait Feed) | One-click aspect ratio switching with mobile font-size bounds |
| 🎨 **Lecture Pure Code Path** | Multi-zone layout (Main Board + Mascot + Sticky Notes) drawn via pure SVG | Zero image generation API cost, fast rendering, clean typography |
| 🖼️ **Visual Director Path** | Optional image generation integration for key cinematic shots (`--classic` template) | Combines code precision with photorealistic creative flexibility |
| ✅ **Automated QA Gates** | CaptionFitGate, layered layout validation, semantic break checks | 100% guarantee of zero text overflows and zero layout collisions |

---

## 🎨 Visual Demos & Aspect Ratios

![Notebook Video Demo](assets/demo/notebook-video-demo.webp)

▶️ [Watch full demo video (MP4)](assets/demo/notebook-video-demo.mp4) · Hero Asset: [hero.png](assets/demo/hero.png)

### Default Canvas: 16:9 Landscape

| Aspect Ratio | Resolution | Video Demo | Best For |
|---|---|---|---|
| **16:9 Landscape** (Default) | 2560×1440 (2K) | [![16:9](assets/demo/notebook-video-demo.webp)](assets/demo/notebook-video-demo.mp4) | YouTube / Desktop / Lecture Walkthroughs |

---

## 📊 11-Step Video Pipeline Architecture

```
[Input: User provides technical concept / topic script]
                          │
     [Step 1~2: Lock Concept & Visual Direction] ─> Outline, storyboard, aspect ratio
                          │
     [Step 3: Word-Level TTS Audio Sync] ────────> Millisecond-accurate word timestamps
                          │
     [Step 4~5: Layout Layering & Code Drawing] ──> React components & SVG diagrams
                          │
     [Step 6~7: Animation Pacing & Multi-Canvas] -> Frame-accurate waveform sync
                          │
     [Step 8: Automated QA Gate Verification] ───> CaptionFitGate & collision check
                          │
     [Step 9~11: Remotion Rendering & Package] ──> Output 2K MP4 + Editable Source ZIP
```

---

## 🚀 Quick Start

This is an AI Agent Skill — install it into your AI assistant and you're ready.

### Option A: Paste one sentence into any Agent (recommended, most universal)

Send this to your AI assistant and it will detect the platform and clone to the right skills directory:

> Please install the notebook-video skill: clone `https://github.com/hyt315/notebook-video` into your skills directory (e.g. `~/.claude/skills/notebook-video` or `~/.agents/skills/notebook-video`) and confirm it works. When I ask to make an educational video, concept explainer, or showcase, use the 11-step Lecture Composition workflow to generate 2K videos.

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
├── SKILL.md                          # Core skill definition and 11-step pipeline
├── README.md                         # Chinese documentation
├── README.en.md                      # English documentation
├── CHANGELOG.md                      # Version history
├── LICENSE                           # MIT License
├── .gitignore                        # Git ignore rules
├── CONTRIBUTING.md                   # Contribution guide
├── CODE_OF_CONDUCT.md                # Code of conduct
├── SECURITY.md                       # Security policy
├── SUPPORT.md                        # Support channels
├── manifest.json                     # Skill manifest
├── agents/                           # Multi-agent metadata
├── assets/demo/                      # Demos & sample assets
├── scripts/
│   ├── notebook-video.mjs            # Cross-platform runner
│   ├── validate_repo.py              # Structure validator
│   └── selftest.py                   # Automated regression test runner
└── references/                       # Design systems & Remotion references
```

---

## ❓ FAQ

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

## 📄 License

Licensed under the [MIT License](LICENSE).

---

> 🌏 **中文版: [README.md](./README.md)**
