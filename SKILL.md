---
name: notebook-video
version: 2.9.0
description: Create complete Chinese 2K warm-ivory engineering-notebook explainer and promotional videos with React, TypeScript and Remotion. The default visual route is pure code-drawn composition (SVG diagrams, mascots, progressive checklists, annotation stickers) synchronized frame-accurately to Chinese TTS word timing, so production never depends on an image-generation model; image generation is an optional add-on offered to the user for concrete hero scenes. Includes a per-shot restricted camera with an out-of-bounds proof, four scene skeletons with a content-to-medium routing table, a cue-indexed shot table, native-30fps motion, active-scene mounting, complete exits, declarative audio, H.264/AAC rendering and six automated quality gates. Use when the user asks to 做科普视频, 手账风视频, 定格动画, AI 视频, 产品宣传片, 介绍一个概念, 讲解产品或技能, 制作 30 秒到数分钟视频, 网站动画转 MP4, 加中文配音/字幕/音效, 快速生成 2K 视频, or combine animated text and diagrams without producing a moving slide deck.
---

# Create notebook explainer videos

Build a finished, validated MP4 **and** an editable Remotion project. This is a low-freedom production
system, not a visual prompt: Remotion is the only renderer, every scene is drawn in code, and every
animation is a pure function of the frame number. The established style must be reproducible by any AI
in any environment — no image model required.

**The film must not look like a slide deck.** That is enforced structurally and by gates, not by taste:
four different scene skeletons with no adjacent repeats, at least three visual media per film, at least
one live state-changing component per explanation scene, and a camera that really moves. See
[scene-skeletons.md](references/scene-skeletons.md), [media-routing.md](references/media-routing.md)
and [shot-language.md](references/shot-language.md).

## Reference files（按需加载参考 · 读取时机如下）

Read only what the current production needs. **写任何场景之前，先读前五份**；其余按下面标注的时机读，不要一次全读。

**读取时机说明**：每条开头的加粗词就是读取时机 —— 「先读」= 动手前读；「必读」= 这一步不做完不许往下走；
「照抄」= 直接复用其代码形状；「逐条对照」= 完成后一条条核对；「何时读」= 满足该条件时才读；「仅当」= 只有该前提成立才读。

**先读** [references/locked-style-contract.json](references/locked-style-contract.json) — binding tokens、坐标与 rejection flags.
**照抄** [references/scene-authoring.md](references/scene-authoring.md) — 场景代码的标准形状与八个坑；不要重新发明。
**照抄** [references/scene-skeletons.md](references/scene-skeletons.md) — 四种骨架与分镜表结构（写分镜表前必读）。
**先读** [references/media-routing.md](references/media-routing.md) — 内容→介质路由、A/B 场景、背景可读性契约。
**先读** [references/shot-language.md](references/shot-language.md) — 六个镜头意图、缩放预算、anchor 出界证明、平移预算。
**必读** [references/lecture-composition.md](references/lecture-composition.md) 与 [references/motion-design.md](references/motion-design.md) — 构图规范与多时钟动效六律。
**何时读**（选定皮肤后只读那一份）： [references/visual-system.md](references/visual-system.md) (paper, default) **or** [references/theme-cel.md](references/theme-cel.md) **or** [references/theme-sticker.md](references/theme-sticker.md) **or** [references/theme-flat.md](references/theme-flat.md); the boundary is in [references/theme-system.md](references/theme-system.md).
**必读** [references/official-aesthetic-system.md](references/official-aesthetic-system.md) — 不许改的锁定元素清单。
**逐条对照** [references/composition-gate.md](references/composition-gate.md) 与 [references/quality-checklist.md](references/quality-checklist.md) — 每道门禁的判据、失败修法、交付事实卡。
**何时读**（改引擎结构/时长/渲染速度时）：[references/remotion-architecture.md](references/remotion-architecture.md) 与 [references/performance-design.md](references/performance-design.md)。
**何时读**（切字幕 / 合成配音时）：[references/subtitle-timing.md](references/subtitle-timing.md) 与 [references/tts-audio.md](references/tts-audio.md)。
**何时读**（策划脚本 / 编排章节时）：[references/narrative-hook.md](references/narrative-hook.md) 与 [references/pacing-rhythm.md](references/pacing-rhythm.md)。
**先读** [references/independent-parts.md](references/independent-parts.md) — 部件分解、z-order、进出场契约（动任何部件之前读）。
**先读** [references/fxkit.md](references/fxkit.md) — 选任何动效组件之前读：18 个构件、props 与 `frame` vs `f` 的命名陷阱。
**何时读**（确定画幅时）：[references/canvas-modes.md](references/canvas-modes.md)（3:4 另读 [references/portrait-illustration-system.md](references/portrait-illustration-system.md)）。
**何时读**：仅当用户接受了可选的生图附加路线时，读 [references/visual-director.md](references/visual-director.md)。
**何时读**（组装工程 / 抓 HTML / 跨平台排错时）：[references/official-skills-exemplar.md](references/official-skills-exemplar.md)、[references/html-capture.md](references/html-capture.md)、[references/cross-platform-compatibility.md](references/cross-platform-compatibility.md)、[references/windows-compatibility.md](references/windows-compatibility.md)。

## Create a project

Always start by copying a bundled template through the launcher; never rebuild the engine from memory.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" check-deps
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-skill
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project ./notebook-video-project --style=cel
node "<SKILL_DIR>/scripts/notebook-video.mjs" prepare-browser ./notebook-video-project
```

- `assets/lecture-template` (default) is the pure-code route; `--classic` copies
  `assets/example-project`, the visual-director exemplar that demonstrates the optional image add-on.
- Four skins, chosen once at kickoff: `paper` (default), `cel`, `sticker`, `flat`. Themes swap palette,
  card skin, background decoration and subtitle chrome only — every coordinate, type scale, motion
  contract and gate is shared.
- Three locked canvases at native 30 fps: 2560×1440 (16:9), 1920×1440 (4:3), 1440×1920 (3:4). The
  bundled example film is authored in the **16:9 design space**; 4:3 / 3:4 need their own layout pass —
  letterbox scaling is not adaptation.
- Create the project in an empty directory so stale files from an earlier run cannot survive.

## Production workflow

```text
[input: topic / script]
  ① lock content      narration.txt + semantic caption lines (one cue per line)
  ② write shot table  <project>/manifests/shots.json — semantic only, no frame numbers
  ③ resolve           python "<SKILL_DIR>/scripts/resolve-shots.py" ./notebook-video-project
  ④ author scenes     four skeletons + media routing; each shot wrapped in ShotCamera(keys, anchor)
  ⑤ build-time gates  both must report P0 = 0
  ⑥ render            render + loudness normalisation (−16 LUFS / −1.5 dBTP)
  ⑦ runtime gates     CaptionFitGate / CardFitGate / OverlapGate / SlotGuard — read the console
  ⑧ package           MP4 + contact sheet + editable source ZIP
```

Step-by-step detail and the per-step read list live in the numbered sections of
[references/scene-authoring.md](references/scene-authoring.md) (authoring) and
[references/lecture-composition.md](references/lecture-composition.md) (composition).

```text
# ②→③ the shot table is the single source of truth; never hand-edit the generated files
python "<SKILL_DIR>/scripts/resolve-shots.py" ./notebook-video-project
# it writes <project>/src/shots.ts (camera keyframes expanded) and <project>/manifests/shots.resolved.json

# ⑤ build-time gates — both must be P0 = 0 before spending render time
python "<SKILL_DIR>/scripts/validate-shot-motion.py" ./notebook-video-project
python "<SKILL_DIR>/scripts/validate-composition.py" ./notebook-video-project

# see components before choosing them (6-page contact sheet, 1 fps → one image per page)
node "<SKILL_DIR>/scripts/notebook-video.mjs" showcase ./notebook-video-project

# ⑥ render, then iterate cheaply on ranges
node "<SKILL_DIR>/scripts/notebook-video.mjs" render ./notebook-video-project ./notebook-video-project/renders/final.mp4
node "<SKILL_DIR>/scripts/notebook-video.mjs" review-frames ./notebook-video-project ./notebook-video-project/renders/scene-review.mp4 START_FRAME END_FRAME
```

## The six gates

| Gate | When | Catches | Blocking? |
|---|---|---|---|
| `resolve-shots.py` | build | timeline gaps/overlaps, coverage ≠ duration, cue index out of range | yes |
| `validate-shot-motion.py` | build | anchor leaves the frame at any keyframe, zoom over budget, pan beyond the zoom-derived budget, camera-move quotas | yes (P0) |
| `validate-composition.py` | build | adjacent scenes sharing a skeleton, <3 skeletons, no live component in an explanation scene, <3 media, zones out of 3–5, lower quarter not filled, transition/entry variety, beat gaps | yes (P0) |
| `CaptionFitGate` | render | caption wider than the safe width, measured with the **current canvas and skin's real weight/spacing** | yes |
| `CardFitGate` | render | text overflowing its card | yes |
| `OverlapGate` | render (sampled every 15 frames) | text-vs-text overlap and paint-order occlusion, using real glyph rects | warn by default, `mode="block"` to block |
| `SlotGuard` | render (dev) | content wider than `StageFrame`'s main slot (`mainW = w − pad×2 − railW − 18`) | warn |

Intentional overlaps (shot handoff, header swap, metric value replacement) must be declared with
`data-gate-allow`; the allow-list may never hide two different pieces of information colliding.

Validation after rendering:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-video ./notebook-video-project/renders/final.mp4 EXPECTED_SECONDS ./notebook-video-project/renders/contact-sheet.jpg
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-caption-sync ./notebook-video-project/audio/narration.mp3.json ./notebook-video-project/manifests/caption-cues.json
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-semantic-breaks ./notebook-video-project/manifests/caption-cues.json ./notebook-video-project/manifests/protected-caption-phrases.txt
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-visual-plan ./notebook-video-project
```

Inspect the opening, every shot boundary, the longest caption and the final frame. Reject any render
with black frames, subtitle overflow, a split protected phrase, half-visible exited objects, incorrect
stacking, unregistered rasters, or generated text baked into imagery.

## Execution discipline and safety (Zero-Mutation 原则)

执行纪律与安全约束（Zero-Mutation 原则）：脚本检测与视觉审查恪守纯只读排查原则，绝不擅自变动系统配置；对于完整渲染（render）、依赖安装或大构架重写等治理对策，须用户明确授权后方可执行。

`scripts/*.py` 严格基于 Python 3.10+ **标准库**实现，**零第三方依赖**（standard library only, zero third-party
dependencies）。不要在本技能里写入实验性改动，直到用户看过渲染成片并明确批准。

## Scripts 清单（`.sh` / `.cmd` 都是同一套 Node 实现的平台包装器，行为完全一致）

```text
scripts/notebook-video.mjs          跨平台统一启动器（new-project / resolve-shots / render / review-frames / showcase / package …）
scripts/resolve-shots.py            分镜表 → 帧号与相机关键帧（唯一定源）
scripts/validate-shot-motion.py     构建期：镜头出界证明 + 运镜配额
scripts/validate-composition.py     构建期：骨架 / 活性组件 / 介质 / 密度
scripts/validate-caption-sync.py    字幕与 TTS 词边界一致
scripts/validate-semantic-breaks.py 保护短语不被切断
scripts/validate-visual-plan.py     视觉计划与清单一致
scripts/validate-layering.py        图层与离场契约
scripts/validate-official-example.py 官方示例一致性锁
scripts/validate-skill-consistency.py 仓库级一致性（双模板 + 文档链接 + 主题包完整性）
scripts/build-semantic-captions.py  语义字幕行 → cue 表
scripts/match-timing.py             换配音后重对齐章节时间轴
scripts/retime.py                   时长变化的机械重写（DURATION / 清单 / 音效建议表）
scripts/audition.py                 TTS 试听条 + 多音字扫描
scripts/coords-lint.py              覆盖层坐标越界体检
scripts/package-project.py         交付源码打包（排除 node_modules / renders / 密钥）
scripts/selftest.py                 端到端回归自测
scripts/check-deps.sh | .cmd        环境依赖体检
scripts/prepare-browser.sh | .cmd   Remotion 无头浏览器准备
scripts/new-project.sh | .cmd       建工程
scripts/sync-project-assets.sh | .cmd   同步 audio/ 与 manifests/ 进 public/ 与 src/
scripts/render-remotion.sh | .cmd   Remotion 渲染
scripts/validate-video.sh | .cmd    成片验收（编码 / 时长 / 响度 / 黑帧）
scripts/package-project.sh | .cmd   打包
```

## Regression self-test

```text
python "<SKILL_DIR>/scripts/selftest.py"
```

Good fixtures must pass and each broken fixture (protected phrase split across cues, mismatched caption
sync, non-video input) must be rejected by the matching gate.
