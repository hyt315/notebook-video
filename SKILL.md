---
name: notebook-video
version: 3.1.1
description: Create complete Chinese 2K warm-ivory engineering-notebook explainer and promotional videos with React, TypeScript and Remotion. The default visual route is pure code-drawn composition (SVG diagrams, mascots, progressive checklists, annotation stickers) synchronized frame-accurately to Chinese TTS word timing, so production never depends on an image-generation model; image generation is an optional add-on offered to the user for concrete hero scenes. Includes a per-shot restricted camera with an out-of-bounds proof, four scene skeletons with a content-to-medium routing table, a cue-indexed shot table, native-30fps motion, active-scene mounting, complete exits, declarative audio, H.264/AAC rendering and fourteen automated quality gates (including a frame-prop-name gate that catches the highest-frequency silent failure in this codebase). Use when the user asks to 做科普视频, 手账风视频, 定格动画, AI 视频, 产品宣传片, 介绍一个概念, 讲解产品或技能, 制作 30 秒到数分钟视频, 网站动画转 MP4, 加中文配音/字幕/音效, 快速生成 2K 视频, or combine animated text and diagrams without producing a moving slide deck.
---

# Create notebook explainer videos

Build a finished, validated MP4 **and** an editable Remotion project. This is a low-freedom production
system, not a visual prompt: Remotion is the only renderer, the **composition and its data** are authored
in code, and every animation is a pure function of the frame number. The established style must be
reproducible by any AI in any environment — no image-generation model required.

**What "no model dependency" means — and what it does not mean.** The line above bans **paid generative
models** (image/video generation APIs) from the default route: they cost money per call and return a
different picture every time, so the style cannot be reproduced. It does **not** ban open-source
libraries. Free, lock-file-pinned React packages are expected to be reused directly rather than
re-implemented — see [dependency-policy.md](references/dependency-policy.md). Hand-writing every UI
element from scratch is not a goal; it is the slowest way to a worse result. `assets/lecture-template`
ships a wrapped component layer under `src/components/` — reach for it before writing new SVG.

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
**先读** [references/dependency-policy.md](references/dependency-policy.md) — 依赖边界（什么能引、什么不能引）、已内置清单、组件纪律与「加一件＝换掉一件」的增长纪律（合规判据是「零引用」，不是一个拍脑袋的总数）。**动任何库或组件之前读这一份。**
**照抄** [references/scene-authoring.md](references/scene-authoring.md) — 场景代码的标准形状与八个坑；不要重新发明。
**照抄** [references/scene-skeletons.md](references/scene-skeletons.md) — 四种骨架与分镜表结构（写分镜表前必读）。
**先读** [references/media-routing.md](references/media-routing.md) — 内容→介质路由、**§5.1 组件权威索引（53 件逐件，选型只查这一处）**、A/B 场景、背景可读性契约。
**先读** [references/shot-language.md](references/shot-language.md) — 六个运镜意图（+ `still` = 合法取值 7 个）、缩放预算、anchor 出界证明、平移预算。
**必读** [references/lecture-composition.md](references/lecture-composition.md) 与 [references/motion-design.md](references/motion-design.md) — 构图规范与多时钟动效六律。
**何时读**（选定皮肤后只读那一份）： [references/visual-system.md](references/visual-system.md) (paper, default) **or** [references/theme-cel.md](references/theme-cel.md) **or** [references/theme-sticker.md](references/theme-sticker.md) **or** [references/theme-flat.md](references/theme-flat.md); the boundary is in [references/theme-system.md](references/theme-system.md).
**必读** [references/official-aesthetic-system.md](references/official-aesthetic-system.md) — 不许改的锁定元素清单。
**逐条对照** [references/composition-gate.md](references/composition-gate.md) 与 [references/quality-checklist.md](references/quality-checklist.md) — 每道门禁的判据、失败修法、交付事实卡。
**何时读**（改引擎结构/时长/渲染速度时）：[references/remotion-architecture.md](references/remotion-architecture.md) 与 [references/performance-design.md](references/performance-design.md)。
**何时读**（切字幕 / 合成配音时）：[references/subtitle-timing.md](references/subtitle-timing.md) 与 [references/tts-audio.md](references/tts-audio.md)。
**何时读**（策划脚本 / 编排章节时）：[references/narrative-hook.md](references/narrative-hook.md) 与 [references/pacing-rhythm.md](references/pacing-rhythm.md)。
**先读** [references/independent-parts.md](references/independent-parts.md) — 部件分解、z-order、进出场契约（动任何部件之前读）。
**必读** [references/fxkit.md](references/fxkit.md) 与 [references/media-routing.md](references/media-routing.md) 的「修辞动作 → 组件」表 — 选组件之前读：**`live` 里每个名字都要能在表上指到**（这是选型纪律；门禁实际查的是"这个名字必须真的出现在场景源码里"，见 `validate-composition.py`）；写 `f={f}` 与 `frame={f}` 的地方见 fxkit 的命名陷阱。修辞工具件（`Callout` / `Checklist` / `JumpInText`）在 `src/toolkit.tsx`；**新封装层在 `src/components/`（Radix 手风琴与标签页、语法高亮、d3 图表、零依赖炫效果、描线/几何、中文反推字号）——选型前先看这一层**。
> **"一共有哪些件"只查一处：[media-routing.md §5.1 组件权威索引](references/media-routing.md#51-组件权威索引53-件--选型只查这一处)**（53 件逐件：用途 / 何时用 / **何时别用** / 接触表第几页 / 真实使用记录）。
> `fxkit.md` 与 `showcase.tsx` 各自只保留实现细节与接触表版面，**不再维护组件清单**——别从接触表反推"有哪些件"，那里有 11 件根本没上。
**何时读**（确定画幅时）：[references/canvas-modes.md](references/canvas-modes.md)（3:4 另读 [references/portrait-illustration-system.md](references/portrait-illustration-system.md)）。
**何时读**：仅当用户接受了可选的生图附加路线时，读 [references/visual-director.md](references/visual-director.md)。
**何时读**（组装工程 / 抓 HTML / 跨平台排错时）：[references/official-skills-exemplar.md](references/official-skills-exemplar.md)、[references/html-capture.md](references/html-capture.md)、[references/cross-platform-compatibility.md](references/cross-platform-compatibility.md)、[references/windows-compatibility.md](references/windows-compatibility.md)。

## 开工前 20 行授权契约

> **只记这 20 行；它与后面任何参考冲突时，以这段为准。** 每一条都对应一个真实事故。
>
> 1. 先跑 `new-project` 复制模板，绝不从记忆重建引擎。
> 2. 分镜表只写语义：`cues` 里**绝不写帧号**，帧号由 `resolve-shots.py` 推。
> 3. 骨架按内容的**第一性**选，不按标题关键词：有机制在跑 → Stage/Corridor；两个对等对象 → Split；要放大看局部 → Zoom。平局时**用能演示机制的那个**。
> 4. 相邻两镜骨架必须不同，全片 ≥3 种；"卡片 + 文字列表"不算讲解。
> 5. 每个讲解场景 ≥1 个**真的随旁白变状态**的构件；`live` 里必须是你场景文件里真实 import 并渲染过的组件名——**写假名字等于没写**（门禁会查）。
> 6. `media` 只允许 6 个值：`chart | console | code | graphic | text | metric`。
> 7. 每镜必须有 `camera.intent`（7 选 1）与 `anchor`；含文字的镜头放大 `s ≤ 1.35`。
> 8. 声明了运镜就**必须真的动**：`max(s) − min(s) ≥ 0.02` 或 `|Δx| + |Δy| ≥ 20`（把 `still` 改名成 `push-in` 不算运镜）。
> 9. 元素出现帧绑到"讲到它的那一句"（`SHOTS.Sx.beats`），**禁止镜头开头一次铺完**。
> 10. 入场统一 `enterAt()`：22 帧 + 22px 上浮 + 0.975→1；同句内错峰 **≤8 帧**（18–30 帧会读成"一个个淡出来"，不是"成串落下"）。
> 11. 帧参数名：`fxkit` 全部传 `frame={f}`；`media / kit / stagekit / skeletons / insert / shotkit` 传 `f={f}`。**传错不报错，只会整体错位**——这是本技能最高频的真实事故（`validate-frame-props.py` 会抓）。
> 12. 卡片高度必须用 `fitH()` 算，禁止手写"看着差不多"的固定高度（渲染期 `CardFitGate` 会拦下真裁切）。
> 13. 给槽内组件传宽度前先算 `mainW = w − pad×2 − railW − 18`。
> 14. 绝对定位构件的 `x/y` 相对**最近的定位祖先**，与文档流标题共用容器原点会精确重叠；**flex 子项若只含绝对定位子元素，必须显式给宽高**，否则宽度塌成 0、多张卡会叠在同一点。
> 15. 整幅底托必须 `z={-1}` 且径向羽化；正 z 会把整镜内容压成半透明。
> 16. 下 1/4 必须填满（底边接近 y=876）；面板下半空洞就是 PPT。**判据在渲染期 `FillGate`**（实测信息元素的最低边，不是读 `shots.json` 里那个声明字段——见 `references/composition-gate.md` 的 P0-4 降级说明）。
> 17. 页眉 / 章节卡 / 字幕放在 `ShotCamera` **之外**。
> 18. 写场景文件后按顺序跑 `resolve-shots.py` → 构建期门禁，**P0 必须 = 0** 才允许渲染。
> 19. 门禁失败只允许改内容（换骨架 / 换介质 / 补元素 / 改高度），**不许改阈值、不许改判据**；连续两次不过就停下来报告。
> 20. 首次渲染后读控制台：`OverlapGate` / `ClippingGate` / `CardFitGate` / `FillGate` 的覆盖率与告警必须清零或显式 `data-gate-allow`；拿不准就先出接触表看图。T3 的 `validate-motion-gaps` 也要跑（画面真的没动这类缺陷只有它能抓）。

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
- **Text-safety colours (`*Ink`).** Every accent ships as a pair: the original (`blue`, `orange`,
  `green`, `gold`, `red`) and a WCAG-derived ink variant (`blueInk`, `orangeInk`, …) for the same hue.
  Fills and strokes keep the original; **text (`color:`) always uses the ink variant** — the original
  reads 2–3:1 on paper, well under the 4.5:1 that body text needs. `validate-presentation.py` enforces
  both halves (inks must pass, and any palette key used as `color:` is measured), and `headerAccent` /
  `headerSub` count as text positions too. Details: [references/theme-system.md](references/theme-system.md).
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
  ⑤ build-time gates  P0 must be 0
  ⑥ render            render + loudness normalisation (−16 LUFS / −1.5 dBTP)
  ⑦ runtime gates     CaptionFitGate / CardFitGate / OverlapGate / ClippingGate / CanvasBoundsGate / FillGate / SlotGuard — read the console
                      (then validate-motion-gaps on the finished MP4: "画面真的没动" is only visible there)
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

# see components before choosing them (17-page contact sheet (`SHOWCASE_PAGES`), 1 fps → one image per page)
node "<SKILL_DIR>/scripts/notebook-video.mjs" showcase ./notebook-video-project

# ⑥ render, then iterate cheaply on ranges
node "<SKILL_DIR>/scripts/notebook-video.mjs" render ./notebook-video-project ./notebook-video-project/renders/final.mp4
node "<SKILL_DIR>/scripts/notebook-video.mjs" review-frames ./notebook-video-project ./notebook-video-project/renders/scene-review.mp4 START_FRAME END_FRAME
```

## The gates

| Gate | When | Catches | Blocking? |
|---|---|---|---|
| `resolve-shots.py` | build | timeline gaps/overlaps, coverage ≠ duration, cue index out of range | yes |
| `validate-shot-motion.py` | build | anchor leaves the frame at any keyframe, zoom over budget, pan beyond the zoom-derived budget, camera-move quotas, **unknown intent names**, **a declared camera move that does not actually move** | yes (P0) |
| `validate-composition.py` | build | adjacent scenes sharing a skeleton, <3 skeletons, no live component in an explanation scene, **a `live` name that does not exist in the scene file**, <3 media, **unknown transition/entry/media names**, zones out of 3–5, lower quarter not filled, **`explanation:false` used to bypass density**, hero size, shot-length spread, repeated骨架 fingerprints, beat gaps (aggregated with frame ranges), **a beat index past the end (`b[k]` / `SHOTS.Sx.beats[k]` — both spellings; the value is `undefined`, so it either throws per frame or the element never appears)** | yes (P0) |
| `validate-audio-levels.py` | build | **a sound-effect asset peaking below −12 dBFS** — it gets attenuated again at mix time and ends up inaudible | yes (P0) |
| `validate-presentation.py` | build | **讲与画对不对得上、读不读得过来**：beat 必须落在它声明的那句/那一镜内且不提前剧透、每条 cue 至少有一拍；字幕 ≤9 加权字/秒、单行 ≤16、≤2 行；字号绝不低于 13px、正文色对比度 ≥4.5:1（WCAG 2.2 SC 1.4.3）。详见 [references/presentation-gate.md](references/presentation-gate.md) | yes (P0) |
| `validate-frame-props.py` | build | **`f={f}` passed to an fxkit component (or `frame={f}` to the other modules)** — silently falls back to the global frame and kills the entrance animation | yes (P0) |
| `CaptionFitGate` | render | caption wider than the safe width, measured with the **current canvas and skin's real weight/spacing** | yes |
| `CardFitGate` | render | content taller/wider than its card (`scrollHeight > clientHeight`, 6px tolerance; clips only), waits for fonts, logs coverage every 5s | yes |
| `OverlapGate` | render (15-frame grid **+ every shot boundary, beat and camera keyframe**) | text-vs-text overlap and paint-order occlusion using real glyph rects; gradient backgrounds count as opaque; header layer (z=140) included | `mode="block"` in the bundled films |
| `ClippingGate` | render (same sampling as `OverlapGate`) | **图形被裁**：SVG/图形元素的真实 rect 越出最近的"会裁切"祖先（HTML 的 `overflow≠visible` 祖先，或所属 `<svg>` 视口；显式 `overflow:visible` 的 svg 按计算样式判、不算越界）——`CardFitGate` 只管 div/span 里的文字、`OverlapGate` 只管文字互相压，两者都看不见"缺了半边的球"（实测 S19 走廊圆心算在 x=0，左半边被 svg 视口裁掉，零报错） | `mode="block"` in the bundled films |
| `CanvasBoundsGate` | render (every frame) | **含文字的叶元素**（HTML 叶 + SVG `text`/`tspan`）的**墨迹矩形**（`Range` 取字）越出 composition 视口：≥6px 出声、落定态（有效不透明度 ≥0.98）≥20px 硬拦。v2 只判这一半——**图形 / 版面件那半边与 `ClippingGate` 会在同一批元素上重复报，已砍**；砍掉的复杂度（设计坐标回折、`z≥140` 排除、按帧抽样）与代价写在件头注释里。**这是此前四道渲染期门禁都不管的一类**：`ClippingGate` 只认 SVG 图元、`CardFitGate` 只管卡片内溢出、`OverlapGate` 管互相压、`FillGate` 管铺到多低，构建期 `coords-lint.py` 又把 `Corridor`/`ZoomStage`/`StageFrame` 这类布局件排除在外 —— 接触表第 ⑥ 页「按 Flash 结算」被画布右缘裁成「按 Flash 结」就是这么漏过去的。判据见 [references/composition-gate.md](references/composition-gate.md) §5.2 | `mode="warn"` in the bundled film / `mode="block"` on the contact sheet (deliberately different gears; reasons in `index.tsx` and the gate's header) |
| `FillGate` | render (same sampling) | **下 1/4 实测密度**：信息元素（有文字/有边框/有描边）rect 并集的最低边 vs y=876（±24 容差），z≥140 的子树跳过。这是 P0-4 的**真实判据**——构建期只查 `bottomFill` 字段在不在（那个字段是生成器自己写死的 `true`，值判据结构上不可能失败） | warn（观感线；"画错了"那三类才硬拦） |
| `SlotGuard` | render (output path, inside `StageFrame`) | **fill of the main slot**: union height of the innermost content elements ÷ slot height; speaks up below 35% and prints the slot's `mainW×mainH` — catches "slot was big enough, content left it empty" (measured: a 428px slot used 11%) | warn |
| `validate-motion-gaps.py` | **post-render (T3, needs the MP4)** | **画面真的没动**：ffmpeg `freezedetect` 逐帧比对，连续"几乎完全相同"超过阈值（默认按镜长比例）即 P0。⚠️ 必须先裁掉字幕带，否则逐字上屏的字幕会把每一段静止都遮掉 | yes (P0) |

Intentional overlaps (shot handoff, header swap, metric value replacement) must be declared with
`data-gate-allow`; the allow-list may never hide two different pieces of information colliding.

**A gate that prints nothing must be distinguishable from a gate that never ran.** `CardFitGate`,
`OverlapGate`, `ClippingGate` and `FillGate` log a coverage line every 5 seconds (`已测 N 个字…` /
`扫过 N 个，无被裁` / `下 1/4 已填`); if you see no coverage line at all,
the gate did not execute — treat that as a failure, not as a pass.

Validation after rendering:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-video ./notebook-video-project/renders/final.mp4 EXPECTED_SECONDS ./notebook-video-project/renders/contact-sheet.jpg
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-caption-sync ./notebook-video-project/audio/narration.mp3.json ./notebook-video-project/manifests/caption-cues.json
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-semantic-breaks ./notebook-video-project/manifests/caption-cues.json ./notebook-video-project/manifests/protected-caption-phrases.txt
# The CLI closes the delivery path: it auto-detects <project>/node_modules/budoux (walking up from the
# caption file) and always adds --require-budoux. A missing BudouX is a hard failure, not a silent skip —
# installing project dependencies is a precondition, never a skippable item. Pass --no-budoux to opt out.
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-visual-plan ./notebook-video-project
```

Inspect the opening, every shot boundary, the longest caption and the final frame. Reject any render
with black frames, subtitle overflow, a split protected phrase, half-visible exited objects, incorrect
stacking, unregistered rasters, or generated text baked into imagery.

## Execution discipline and safety (Zero-Mutation 原则)

执行纪律与安全约束（Zero-Mutation 原则）：脚本检测与视觉审查恪守纯只读排查原则，绝不擅自变动系统配置；对于完整渲染（render）或引擎级重构等治理对策，须用户明确授权后方可执行。

**依赖分两种，纪律完全不同（这是本技能最容易被读错的一条）：**

| 情况 | 纪律 |
|---|---|
| 模板**已内置**的依赖（`assets/lecture-template/package.json` 已声明的） | **随 `npm install` 一次装好，无需任何额外授权，直接 `import` 使用。** 含 Radix、react-icons、react-syntax-highlighter、d3-scale/d3-shape，以及五个 `@remotion/*` 官方扩展（transitions / paths / shapes / layout-utils / noise） |
| 清单之外的**新**依赖 | 需用户明确授权后才能加进模板 |

判断边界见 [dependency-policy.md](references/dependency-policy.md)：**禁的是"按次付费、结果不可复现"的生成式模型，不是开源库。**

`scripts/*.py` 严格基于 Python 3.10+ **标准库**实现，**零第三方依赖**（standard library only, zero third-party
dependencies）——这条限定**只针对 `scripts/` 下的 Python 脚本**，不是对整个技能的约束。不要在本技能里写入实验性改动，直到用户看过渲染成片并明确批准。

## Scripts 清单（`.sh` / `.cmd` 都是同一套 Node 实现的平台包装器，行为完全一致）

```text
scripts/notebook-video.mjs          跨平台统一启动器（new-project / resolve-shots / render / review-frames / showcase / package …）
scripts/resolve-shots.py            分镜表 → 帧号与相机关键帧（唯一定源）
scripts/validate-shot-motion.py     构建期：镜头出界证明 + 运镜配额
scripts/validate-composition.py     构建期：骨架 / 活性组件 / 介质 / 密度 / 枚举闭合 / live 可解析 / 主角尺寸 / 镜长分布
scripts/validate-frame-props.py     构建期：fxkit 传 frame、其他模块传 f —— 写错即 P0（会静默回落到全局帧）
scripts/validate-audio-levels.py    构建期：音效素材峰值 < -12 dBFS 即 P0（录太轻 = 混音后等于没有音效）
scripts/validate-presentation.py    构建期：呈现效果（beat↔cue 对齐 / 字幕阅读预算 / 字号与对比度）——现有门禁都没问过的那一层
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
scripts/negative-gate-check.py     负向抽查：给六道构建期门禁喂"该拦的夹具"，验证它们真的会拦
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

For the build-time gates, run the negative spot-check — it feeds fifty-four fixtures to the gates (a shot table whose anchor leaves the frame, a pan beyond the zoom budget, adjacent scenes sharing a
skeleton, a shot with no live component, a timeline gap, a faked `live`/media name, a camera move that never
moves, a frame-prop typo in the fxkit layer and in the components layer, a beat that spoils its line, a beat
pointing at another shot's cue, a beat landing too late for its line, a beat legal but flush against that
tolerance, a caption read too fast, a font below the floor, body text the same colour as the paper, a text
colour that misses 4.5:1, a beat index past the end in all three spellings, imports of names that no longer
exist, a doc naming a component that does not exist, a canvas-bounds gate whose wiring was cut, whose gears
were "unified" or whose judgement was widened back, four `evidence` fixtures — one naming a widget that is not
in the scene source at all, one naming a widget only another shot uses (a **known miss**: it must pass), one
that only appears in a comment, and the untouched template with scene sources — and three narrative-`move`
run fixtures), the layering contract violated both ways, a visual plan with an invalid mode or an
uncovered frame gap, an inaudible sfx mix and a corrupt audio file (a failed measurement must hard-fail
the gate, not pass), an official-example copy with a tampered canvas, a scene source whose shot functions
cannot be found, a stale resolved timeline, and a BudouX-less delivery) plus negative controls, and
asserts each gate blocks, warns or passes as expected — 97 assertions, 48 of which pin or forbid the expected message
substring, so "failed for some other reason" cannot pass as a blocked fixture.
**A gate that exists in name only is the most dangerous defect.**

```text
python "<SKILL_DIR>/scripts/negative-gate-check.py"
```
