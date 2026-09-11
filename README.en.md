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

## 📖 What is this?

An AI-Agent **video production system**. Say "make me an explainer video about X" and it carries the job end to end: write the narration → synthesise Chinese TTS → read millisecond word timestamps → split into semantic subtitle lines → lay out a shot table → draw the scenes → run the gates → render a 2K film, and hand back an editable Remotion source tree alongside the MP4.

The hard part was never drawing something. It is making the result **not look like a slide deck**, keeping **captions in sync with the voice**, and keeping **elements from covering each other**. This skill turns all three into **gates that refuse to render**: skeletons must differ, media must differ, the camera must really move, captions must be measured with the real font, and text may not overlap — **a non-zero P0 count blocks the render**.

Every frame is drawn in code (React + SVG + Remotion) with **no image-generation model required**; when the argument needs "this really is the official UI / the official chart", a real screenshot can be dropped into a material plate.

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

## 🔒 Security and privacy

- **Read-only inspection first**: dependency and pre-flight checks only measure; they never change system environment variables or system configuration.
- **Zero-token local run**: rendering and all gates run on your machine with no online API quota; narration goes to your own TTS endpoint and the key is read from the environment only, never written to disk.
- **Deterministic and reproducible**: everything is code-driven; every animation is a pure function of the frame number (no `Math.random`, no CSS animations or timers).
- **Gates before prose**: whatever can be proved arithmetically at build time is checked there; only measurements that need real fonts and layout run in the browser.
- **Complete source delivery**: the MP4 ships together with the full, clean Remotion React source tree.

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

## 📄 License

Released under the [MIT License](LICENSE).
