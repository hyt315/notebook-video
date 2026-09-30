# Notebook Video / AI Explainer-Video Skill

<div align="center">

**把讲解目标转成有明确分镜、配音时间线与可复现渲染的教学视频；由创作者选择适合内容的视觉语言。**

**Turn a learning goal into a storyboarded, voice-timed, reproducibly rendered explainer—with visual choices made for the subject, not for quota.**

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

An AI-Agent **video-making skill and Remotion project template**. It helps the creator define a learning goal, narration, voice/caption timing, each shot's instructional relation and visible carrier, then build, validate, and render an editable film project. Speech and image services are chosen by the user; the workflow does not assume one generator or vendor.

Quality is not a proxy score made from camera moves or component counts. Every narration cue must map to a shot with a meaningful learning relation and a visible, readable carrier; a static diagram or text frame may coherently support several cues. Automated checks cover mechanically testable issues such as cue coverage, real scene content, timing, caption fit, overlap, clipping, and camera geometry. Clarity, comfort, and whether the picture actually explains the spoken line still require watching the complete film with sound at its intended viewing size.

Every frame is drawn in code (React + SVG + Remotion) with **no image-generation model required**; when the argument needs "this really is the official UI / the official chart", a real screenshot can be dropped into a material plate.

---

---

## ✨ Features

| Feature | What it does | Why it matters |
| --- | --- | --- |
| **Learning-goal-first storyboard** | Choose one coherent base treatment; declare each shot's core relation and visible carrier; every narration cue maps to explanatory picture, text, chart, or process | Optional skins and motion recipes do not mean optional visual teaching |
| **Content-fit visual methods** | Helpers include Stage, Corridor, Split, Zoom, charts, code, labels, screenshots, and hand-drawn forms | Choose what the subject needs; no skeleton rotation, media-count, or component-count quotas |
| **Still or moving, by purpose** | A static camera is a valid default; when zoom/pan/orbit changes framing, validate anchor visibility and geometry | Changes serve the explanation; holds leave time to read and reason |
| **Engineering checks** | Cue coverage and teaching declarations, declared camera geometry, caption/card fit, text overlap/occlusion, clipping/canvas bounds, audio/video validity | Block only mechanically testable failures; gate coverage is not an instructional-effect score |
| **Frame-timed audio-visual timeline** | Word timestamps drive captions and author-declared visual events; one image can support consecutive cues without a new animation for each sentence | Synchronize speech while respecting reading and thinking pauses |
| **Four optional base treatments** | `paper` (default) / `cel` / `sticker` / `flat`; components can still be selected or adapted locally | Choose a coherent treatment without locking every detail or cycling every skin |
| **Reusable open-source components** | Python scripts use the standard library; the Remotion template locks open-source runtime dependencies; new dependencies need review | Avoid misreading "zero dependencies" as "no open source," while excluding unused components that never reach a frame |
| **Source-registered assets** | Manifests record source and rights; rendered assets should be visible and support their related claim | Traceability, not decorative-asset quotas |

---

---

## 🎨 Aspect Ratios and Validation Status
> To check the current version: `npm install` inside `assets/lecture-template`, then `npm run still` (single frame) or `npm run render` (full film). **For a delivery file, use `node scripts/notebook-video.mjs render <project> <output>`** — it rewrites the color metadata and normalizes loudness, which `npm run render` does not do (its output fails the `validate-video` color assertion).
> The contact sheet is the same: `node scripts/notebook-video.mjs showcase <project-dir>` now renders at **delivery spec** (2560×1440 / silent AAC / color tags rewritten, matching the file in `assets/demo/`). `--scale` accepts a decimal literal only — `--scale=4/3` is rejected by the CLI, use `1.3333333333333333`.

The bundled eight-shot example has now been reflowed and rendered in 16:9 (2560×1440), 4:3 (1920×1440), and 3:4 (1440×1920). Each mode was reviewed with a 390px eight-shot contact sheet, all seven cut boundaries, and full-render card-fit, overlap, clipping, and canvas-bound checks. This evidence covers the bundled template only; it does not imply automatic adaptation of arbitrary new projects. No blinded human review, physical-device test, or audio/TTS validation was performed. See [`references/canvas-modes.md`](references/canvas-modes.md).

## 📊 Production pipeline

```
[Input: topic / script]
        │
  ① Lock content ── narration.txt + semantic caption lines (one cue per line)
        │
  ② Write shot table ── manifests/shots.json
        │   records cue coverage, core relation, and visible carrier;
        │   layout, components, and camera intent are chosen as needed
        │
  ③ Resolve ── resolve-shots.py → src/shots.ts (frame numbers and camera keyframes generated)
        │
  ④ Author scenes ── choose layouts/components to fit the subject; validate an
        │   anchor only when camera motion changes framing; static holds are valid
        │
  ⑤ Build-time checks ── cue coverage, teaching declarations, declared camera geometry
        │
  ⑥ Render ── Remotion render + loudness normalisation (-16 LUFS / -1.5 dBTP)
        │
  ⑦ Render checks + delivery ── caption/card fit, overlap/occlusion, clipping/canvas bounds
                                (optional diagnostics are not quality scores; static shots are valid)
                                → 2K MP4 + contact sheet + editable source ZIP
```

---

---

## 🚀 Quick start

This is a standard AI Agent Skill — install it into your assistant and use it directly.

### Option A: paste one sentence (most portable)

Paste this into your agent to install the skill in an appropriate directory under your permissions:

> Install the notebook-video skill: clone `https://github.com/hyt315/notebook-video` into an appropriate skills directory and confirm installation. When I request an explainer video, follow SKILL.md: start from the learning goal, give every narration cue a clear visual carrier, and use still frames when they best support explanation or reading. Do not add motion or components merely to satisfy quotas.

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
# 1. Create the project (copy the template, choose a base visual treatment)
node scripts/notebook-video.mjs new-project ./my-video --style=cel

# 2. Write the narration and the subtitle lines (the two files must reconstruct each other;
#    write numbers the way they are spoken)
python <template>/scripts/tts-openai-compatible.py ./my-video     # TTS + word timings
python <template>/scripts/speed-post.py ./my-video 1.10           # deterministic pace fix
node scripts/notebook-video.mjs build-semantic-captions audio/narration.mp3.json manifests/semantic-caption-lines.txt manifests/caption-cues.json

# 3. Write the shot table (cue coverage, coreRelation, visualCarrier; never hand-write frames)
#    manifests/shots.json -> resolve-shots.py derives frames; camera keys only when motion is used

# 4. Gates, then render
python scripts/validate-frame-props.py ./my-video     # frame-prop names (the most common silent failure)
python scripts/validate-shot-motion.py ./my-video     # geometry safety for declared camera motion
python scripts/validate-composition.py ./my-video     # cue coverage, teaching declarations, carriers
python scripts/validate-audio-levels.py ./my-video    # sound effects may not be mastered too quietly
node scripts/notebook-video.mjs render ./my-video out.mp4
```

Render checks flag text overlap, clipped content, and caption fit issues. After automated checks, watch the full film with sound and inspect it at the intended mobile viewing size; gates do not substitute for blind review or demonstrate learning effectiveness.

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
├── CHANGELOG.md                      # Version history (currently v3.1.3)
├── LICENSE                           # Apache License 2.0
├── NOTICE                            # Third-party font / asset / dependency notices
├── CONTRIBUTING.md · CODE_OF_CONDUCT.md · SECURITY.md · SUPPORT.md
├── assets/
│   ├── demo/                         # Finished films & previews
│   ├── lecture-template/             # Official template (pure-code route, 8-shot example film)
│   └── example-project/              # Classic route example (optional image add-on)
├── scripts/                          # Python stdlib / Node CLI scripts; the Remotion template has locked runtime deps
│   ├── notebook-video.mjs            # Cross-platform runner (incl. the showcase command)
│   ├── resolve-shots.py              # Shot table → frame numbers and camera keyframes
│   ├── validate-shot-motion.py       # Build-time: geometry safety for declared camera motion
│   ├── validate-composition.py       # Build-time: cue coverage, teaching declarations, visible carriers
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
    └── theme-*.md / visual-system.md # Optional visual-treatment references
```

Source layers inside the template (`assets/lecture-template/src/`):

```
index.tsx           Engine: canvas / captions / chapter card / asset gate / runtime gates + shot handoff
shotkit.tsx         Optional camera helpers: still/restricted motion, conditional anchor proof, depth/backing plate
stagekit.tsx        Optional Stage layout helper, state and progress expression
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
fill-gate.tsx       Optional legacy visual diagnostic; no requirement to fill the canvas
showcase.tsx        Component contact sheet (18 pages, for AI to pick by sight)
scenes.tsx          Scene layer (8-shot example film; rewrite this layer per topic)
```

---

---

## ❓ FAQ

- **Q: How do you avoid merely turning slides into a video?**\
  A: Start with the learning goal and each cue's visible carrier. The shot plan states the core relation and what the viewer can actually see; then review the storyboard and the complete film with sound. Choose a comparison, process diagram, or reveal only when the subject calls for it. There are no skeleton-rotation, media-count, or per-shot motion quotas. Automated checks catch engineering failures, but cannot certify teaching effectiveness or prove a film is not slide-like with one score.

- **Q: What visual problems do automated checks catch?**\
  A: The active `OverlapGate` checks text overlap/occlusion in sampled frames; `ClippingGate` and `CanvasBoundsGate` check graphic/text clipping; `CaptionFitGate` checks caption fit. Coverage reports show what was actually inspected. `validate-shot-motion.py` checks anchor and canvas bounds for declared camera moves. Legacy `FillGate`, `SlotGuard`, and `validate-motion-gaps` are not teaching-quality gates and do not require a filled canvas or continuous movement. Automated checks never replace watching the full film.

- **Q: Do I need to re-time everything after editing the script?**\
  A: No. The shot table only references cues; frame numbers, camera keyframes and SFX pinning are all derived from the TTS word timestamps by `resolve-shots.py`.

- **Q: Will a static shot fail validation?**\
  A: No. A still diagram, example, formula, or text frame is valid when it clearly supports its cue and leaves time to read or reason. A static camera does not mean there is no visual content.

- **Q: Must all four visual treatments appear in one film?**\
  A: No. Choose one coherent base treatment for the film. `paper`, `cel`, `sticker`, and `flat` are optional starting points; local components may be selected or adapted to fit the subject, not to reach a count.

- **Q: Which aspect ratios have been validated?**\
  A: The official eight-shot sample has been separately laid out and silently rendered in 16:9, 4:3, and 3:4, with contact-sheet, canvas-bound, overlap, and clipping checks. This covers only the bundled sample, not automatic adaptation of arbitrary projects. No blind review, physical-device test, or audio/TTS validation was performed.

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
