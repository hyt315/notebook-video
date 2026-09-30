---
name: notebook-video
version: 3.1.3
description: Create Chinese explainer and promotional videos with React, TypeScript and Remotion. Start from a clear learning outcome, a coherent chosen visual treatment, and a cue-indexed storyboard that gives every spoken cue readable visual support. Choose among static diagrams, text, data, images and animation for what best explains the relationship; paper, cel, sticker and flat are optional treatments, not required identities. Includes deterministic rendering, frame-safe camera geometry, narration/caption timing, reusable open-source components, audio, H.264/AAC delivery, technical validators, and human review. Use when the user asks to 做科普视频, 讲解概念/产品/技能, 做宣传片, 生成配音字幕, or turn Remotion compositions into a finished video.
---

# Create notebook explainer videos

Build a finished, validated MP4 **and** an editable Remotion project. Remotion is the renderer; composition
and data are authored in code, and all frame-dependent motion must be reproducible from the frame number.
Choose and record one coherent visual treatment for the film (the shipped paper treatment is a usable
default); select a storyboard from the subject, not from a quota. The particular style, component, or motion
recipe is flexible. The instructional task is not: every narration cue needs a readable visual carrier, and
each shot must identify the core relation it teaches. A visually coherent static diagram is valid support.

**Reproducibility and dependencies.** A default route should not require paid generative calls or
unrepeatable image output. This does **not** ban open-source libraries: reuse appropriate, lock-file-pinned
packages instead of rewriting mature components; see [dependency-policy.md](references/dependency-policy.md).
Project scripts remain Python-standard-library-only. The Remotion template has its own declared and locked
runtime dependencies. A component is useful only when it is actually rendered and supports the explanation.

**Do not substitute complexity for teaching.** A video is not improved by rotating through layouts, adding
motion, or filling whitespace unless those choices clarify the topic. The shot table and rendered scene
must provide real visual support for every cue; a static hold is not an excuse to omit that support. See
[scene-skeletons.md](references/scene-skeletons.md), [lecture-composition.md](references/lecture-composition.md),
and [quality-checklist.md](references/quality-checklist.md).

## Reference files（按需加载参考 · 读取时机如下）

Read only what the current production needs. **写任何场景之前，先读前五份**；其余按下面标注的时机读，不要一次全读。

**读取时机说明**：每条开头的加粗词就是读取时机 —— 「先读」= 动手前读；「必读」= 这一步不做完不许往下走；
「照抄」= 直接复用其代码形状；「逐条对照」= 完成后一条条核对；「何时读」= 满足该条件时才读；「仅当」= 只有该前提成立才读。

**先读** [references/locked-style-contract.json](references/locked-style-contract.json) — one 16:9 design-reference exemplar and shared technical invariants; its aesthetic values are not universal locks.
**先读** [references/dependency-policy.md](references/dependency-policy.md) — 依赖边界（什么能引、什么不能引）、已内置清单、组件纪律与「加一件＝换掉一件」的增长纪律（合规判据是「零引用」，不是一个拍脑袋的总数）。**动任何库或组件之前读这一份。**
**先读** [references/scene-authoring.md](references/scene-authoring.md) — 场景代码形状、cue覆盖与验证流程。
**先读** [references/scene-skeletons.md](references/scene-skeletons.md) — 四种可复用骨架与分镜表字段；骨架类别/数量不是配额。
**先读** [references/media-routing.md](references/media-routing.md) — 内容→视觉表征的候选思路与组件权威索引；按教学需要选，不按件数轮换。
**先读** [references/shot-language.md](references/shot-language.md) — 可选运镜、still镜头、缩放/平移安全预算与anchor证明。
**必读** [references/lecture-composition.md](references/lecture-composition.md) 与 [references/motion-design.md](references/motion-design.md) — 教学关系优先的构图和有意图的帧确定性动效。
**先读** [references/visual-system.md](references/visual-system.md) 与 [references/theme-system.md](references/theme-system.md) — 必须选一套连贯的视觉处理；具体paper/cel/sticker/flat规则按需查，可混合但要有理由。
**必读** [references/official-aesthetic-system.md](references/official-aesthetic-system.md) — 默认视觉资源、实现和可读性事实；区分可变外观与技术不变量。
**逐条对照** [references/composition-gate.md](references/composition-gate.md) 与 [references/quality-checklist.md](references/quality-checklist.md) — 每道门禁的判据、失败修法、交付事实卡。
**何时读**（改引擎结构/时长/渲染速度时）：[references/remotion-architecture.md](references/remotion-architecture.md) 与 [references/performance-design.md](references/performance-design.md)。
**何时读**（切字幕 / 合成配音时）：[references/subtitle-timing.md](references/subtitle-timing.md) 与 [references/tts-audio.md](references/tts-audio.md)。
**何时读**（策划脚本 / 编排章节时）：[references/narrative-hook.md](references/narrative-hook.md) 与 [references/pacing-rhythm.md](references/pacing-rhythm.md)。
**先读** [references/independent-parts.md](references/independent-parts.md) — 部件分解、z-order、进出场契约（动任何部件之前读）。
**必读** [references/fxkit.md](references/fxkit.md) 与 [references/media-routing.md](references/media-routing.md) 的「修辞动作 → 组件」表 — 选组件之前读：**`live` 里每个名字都要能在表上指到**（这是选型纪律；门禁实际查的是"这个名字必须真的出现在场景源码里"，见 `validate-composition.py`）；写 `f={f}` 与 `frame={f}` 的地方见 fxkit 的命名陷阱。修辞工具件（`Callout` / `Checklist` / `JumpInText`）在 `src/toolkit.tsx`；**新封装层在 `src/components/`（Radix 手风琴与标签页、语法高亮、d3 图表、零依赖炫效果、描线/几何、中文反推字号）——选型前先看这一层**。
> **"一共有哪些件"只查一处：[media-routing.md §5.1 组件权威索引](references/media-routing.md#51-组件权威索引53-件--选型只查这一处)**（53 件逐件：用途 / 何时用 / **何时别用** / 接触表第几页 / 真实使用记录）。
> `fxkit.md` 与 `showcase.tsx` 各自只保留实现细节与接触表版面，**不再维护组件清单**——别从接触表反推"有哪些件"，那里有 10 件根本没上。
**何时读**（确定画幅时）：[references/canvas-modes.md](references/canvas-modes.md)（3:4 另读 [references/portrait-illustration-system.md](references/portrait-illustration-system.md)）。
**何时读**：仅当用户接受了可选的生图附加路线时，读 [references/visual-director.md](references/visual-director.md)。
**何时读**（组装工程 / 抓 HTML / 跨平台排错时）：[references/official-skills-exemplar.md](references/official-skills-exemplar.md)、[references/html-capture.md](references/html-capture.md)、[references/cross-platform-compatibility.md](references/cross-platform-compatibility.md)、[references/windows-compatibility.md](references/windows-compatibility.md)。

## 开工前设计与实现契约

> **质量要求不等于风格配额。** 每条旁白 cue 必须由恰好一个分镜覆盖；每镜写 `coreRelation` 与 `visualCarrier`，场景源码实际绘出可见内容。选用并记录连贯的视觉处理和有目的的 storyboard。皮肤、骨架、组件、介质、运镜和动效具体套路可以按需选；静态图、图表、可读文字、过程画面均可承载教学，不要求全片持续运动。
>
> 1. 用 `new-project` 从模板开工；不要从记忆重建引擎。
> 2. 先写学习目标、受众、事实/数据来源和 narration/caption cues；保留理解主题所需信息。
> 3. 每镜标明核心学习关系 `coreRelation`、实际可见载体 `visualCarrier` 与覆盖的 cue；自动校验只能检查声明/节点，真人需判断语义是否吻合。
> 4. 对每句 cue 都明确画面如何帮助观众理解或读取；同一静态视觉可服务多句，但不可留 cue 无视觉支持。
> 5. 先从内容决定最清晰的表现：图、文本、数据、图像或状态变化；不为轮换骨架/介质/组件而加东西。
> 6. 选择且记录连贯的 visual treatment；paper 是默认可用方案，cel/sticker/flat/hybrid 只有在适配时使用，不能把风格决定留空。
> 7. 把有意义的高亮/声音/运动对准正在讲的对象；没有明确教学习作用时用静态/停顿，不强迫动画。
> 8. 分镜只写语义 cue index，不写推算帧号；用 `resolve-shots.py` 从 cue 时间生成连续时间线。
> 9. `anchor` 仅在镜头实际缩放/平移/轨道变化时必需；静止镜头合法。变换后必须通过几何安全证明。
> 10. 帧参数按组件 API 传递（`fxkit/toolkit` 用 `frame={f}`，其余按接口；`validate-frame-props.py` 检查常见静默错位）。
> 11. 用自适应文字尺寸/布局；根据最终输出、语言、播放尺寸和字体实测，不把设计像素等同于手机可读性。
> 12. 确认主题装饰与内容对比度、裁切、遮挡及字幕安全区；不要求占满画布或下沿。
> 13. 引用组件前确认代码确实渲染、且对理解/比较/定位/记忆有帮助；不因组件库较大就堆组件，也不因“零依赖”误读而手写成熟库。
> 14. 修改依赖遵循锁定和授权边界；新增依赖按 `dependency-policy.md` 核实许可、必要性与可复现性。
> 15. 构建期运行 `resolve-shots.py`、`validate-shot-motion.py`、`validate-composition.py`、`validate-presentation.py` 等对应门禁；修复真实问题，不为了通过而改阈值。
> 16. 渲染后读门禁覆盖率与警告；门禁未运行不能算通过。自动检查不会证明教学或舒适性。
> 17. 看关键帧/接触表，至少核对首尾、每个镜头边界、最长字幕、关键高亮及可能的裁切/遮挡。
> 18. 以正常速度带声观看完整成片，核对视觉是否讲对当句、阅读停留是否够、声音是否干扰。
> 19. 对 16:9 同时查原尺寸与 390px 手机预览；4:3、3:4 应单独适配并实测，没测就如实标记未知。
> 20. 交付 MP4、可编辑工程、关键技术事实与已知限制；没有外部受众评测时，不能声称盲评或学习效果已验证。

## Create a project

Always start by copying a bundled template through the launcher; never rebuild the engine from memory.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" check-deps
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-skill
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project ./notebook-video-project --style=paper
node "<SKILL_DIR>/scripts/notebook-video.mjs" prepare-browser ./notebook-video-project
```

- `assets/lecture-template` (default) is the pure-code route; `--classic` copies
  `assets/example-project`, a visual-director exemplar with the optional image add-on.
- Four bundled visual treatments: `paper` (default), `cel`, `sticker`, `flat`. Record a coherent treatment
  for the film; a restrained hybrid is acceptable when it serves the content. These are starting points,
  not locked film identities. Typography, contrast, subtitle safety and frame determinism remain technical
  checks independent of skin.
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
  ② choose a visual treatment and write the shot table — each shot records `coreRelation`,
     `visualCarrier` and semantic cue coverage; no hand-authored frame numbers
  ③ resolve           python "<SKILL_DIR>/scripts/resolve-shots.py" ./notebook-video-project
  ④ author scenes     match the spoken claim with readable content; use an existing helper when useful
  ⑤ build-time gates  resolve cue coverage and verify visual declarations and camera safety
  ⑥ render            render + loudness normalisation (−16 LUFS / −1.5 dBTP)
  ⑦ runtime gates     CaptionFitGate / CardFitGate / OverlapGate / ClippingGate / CanvasBoundsGate — read the console
                      (motion-gap analysis is an optional diagnostic; deliberate still frames are valid)
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

# see components before choosing them (18-page contact sheet (`SHOWCASE_PAGES`); a select filter grabs each page's frames 6 and 21 → two mid-page frames per page, tiled 6x6)
node "<SKILL_DIR>/scripts/notebook-video.mjs" showcase ./notebook-video-project

# ⑥ render, then iterate cheaply on ranges
node "<SKILL_DIR>/scripts/notebook-video.mjs" render ./notebook-video-project ./notebook-video-project/renders/final.mp4
node "<SKILL_DIR>/scripts/notebook-video.mjs" review-frames ./notebook-video-project ./notebook-video-project/renders/scene-review.mp4 START_FRAME END_FRAME
```

## The gates

| Gate | When | Catches | Blocking? |
|---|---|---|---|
| `resolve-shots.py` | build | timeline gaps/overlaps, coverage ≠ duration, cue index out of range, timing derived from narration cues | yes |
| `validate-shot-motion.py` | build | transformed camera keyframe leaves safe view, zoom exceeds budget, pan exceeds zoom-derived budget, **unknown intent names**; a still camera and no anchor for unchanged framing are valid | geometry/data errors yes; stale intent notes P1 |
| `validate-composition.py` | build | every cue covered by exactly one shot, missing `coreRelation`/`visualCarrier`, no recognizable visible JSX in authored scene, unknown transition/entry names, invalid cue references, missing scene function, **a beat index past the end** (otherwise it may resolve to `undefined`) | concrete omissions/errors yes (P0) |
| `validate-audio-levels.py` | build | **a sound-effect asset peaking below −12 dBFS** — it gets attenuated again at mix time and ends up inaudible | yes (P0) |
| `validate-presentation.py` | build | cue/beat timing integrity, explicit caption timeline errors, color contrast; subtitle speed/line/font-size heuristics prompt review and are not universal WCAG thresholds. It cannot decide whether a visual explains the narration. See [references/presentation-gate.md](references/presentation-gate.md) | integrity/contrast errors yes; heuristics P1 |
| `validate-frame-props.py` | build | **`f={f}` passed to an fxkit component (or `frame={f}` to the other modules)** — silently falls back to the global frame and kills the entrance animation | yes (P0) |
| `CaptionFitGate` | render | caption wider than the safe width, measured with the **current canvas and skin's real weight/spacing** | yes |
| `CardFitGate` | render | content taller/wider than its card (`scrollHeight > clientHeight`, 6px tolerance; clips only), waits for fonts, logs coverage every 5s | yes |
| `OverlapGate` | render (15-frame grid **+ every shot boundary, beat and camera keyframe**) | text-vs-text overlap and paint-order occlusion using real glyph rects; gradient backgrounds count as opaque; header layer (z=140) included | `mode="block"` in the bundled films |
| `ClippingGate` | render (same sampling as `OverlapGate`) | **图形被裁**：SVG/图形元素的真实 rect 越出最近的"会裁切"祖先（HTML 的 `overflow≠visible` 祖先，或所属 `<svg>` 视口；显式 `overflow:visible` 的 svg 按计算样式判、不算越界）——`CardFitGate` 只管 div/span 里的文字、`OverlapGate` 只管文字互相压，两者都看不见"缺了半边的球"（实测 S19 走廊圆心算在 x=0，左半边被 svg 视口裁掉，零报错） | `mode="block"` in the bundled films |
| `CanvasBoundsGate` | render (every frame) | Text ink leaves the composition viewport; distinguishes a transient animated edge from a settled severe overflow. Use together with `ClippingGate` for geometric clipping. See [references/composition-gate.md](references/composition-gate.md) §5.2. | configured `warn`/`block` by composition |
| `validate-motion-gaps.py` | optional post-render diagnostic | Finds long near-identical frame runs; subtitles can invalidate naïve measurements. Deliberate reading holds may be correct, so this tool never defines motion as a quality requirement. | no; interpret against narration and scene purpose |

Intentional overlaps (shot handoff, header swap, metric value replacement) must be declared with
`data-gate-allow`; the allow-list may never hide two different pieces of information colliding.

**A gate that prints nothing must be distinguishable from a gate that never ran.** `CardFitGate`,
`OverlapGate` and `ClippingGate` log coverage lines; if you see no coverage line at all,
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

## Execution discipline and safety

Read-only inspection should not silently mutate the user's machine or external services. When the user asks
for implementation, local source edits, dependency installation from an existing lockfile, and local
renders are within that requested scope; preserve originals or use an isolated project copy when practical.
Do not publish, push, change accounts, modify system configuration, or add an unapproved dependency as an
incidental side effect. Pause for confirmation before consequential external or irreversible actions.

**依赖分两种，纪律完全不同（这是本技能最容易被读错的一条）：**

| 情况 | 纪律 |
|---|---|
| 模板**已内置**的依赖（`assets/lecture-template/package.json` 已声明的） | **随 `npm install` 一次装好，无需任何额外授权，直接 `import` 使用。** 含 Radix、react-icons、react-syntax-highlighter、d3-scale/d3-shape，以及五个 `@remotion/*` 官方扩展（transitions / paths / shapes / layout-utils / noise） |
| 清单之外的**新**依赖 | 需用户明确授权后才能加进模板 |

判断边界见 [dependency-policy.md](references/dependency-policy.md)：**禁的是"按次付费、结果不可复现"的生成式模型，不是开源库。**

`scripts/*.py` 严格基于 Python 3.10+ **标准库**实现，**零第三方依赖**（standard library only, zero third-party
dependencies）——这是 `scripts/` 的边界，**不是**全技能禁用开源组件。Remotion and template dependencies
are declared and lockfile-pinned separately. Local changes should be tested and reported; a render is evidence,
not a substitute for human approval of publication or other consequential external actions.

## Scripts 清单（`.sh` / `.cmd` 都是同一套 Node 实现的平台包装器，行为完全一致）

```text
scripts/notebook-video.mjs          跨平台统一启动器（new-project / resolve-shots / render / review-frames / showcase / package …）
scripts/resolve-shots.py            分镜表 → 帧号与相机关键帧（唯一定源）
scripts/validate-shot-motion.py     构建期：实际相机变换的出界/缩放/平移安全证明；静止合法
scripts/validate-composition.py     构建期：逐cue覆盖、核心学习关系/视觉承载声明、可见JSX与输入一致性
scripts/validate-frame-props.py     构建期：fxkit 传 frame、其他模块传 f —— 写错即 P0（会静默回落到全局帧）
scripts/validate-audio-levels.py    构建期：音效素材峰值 < -12 dBFS 即 P0（录太轻 = 混音后等于没有音效）
scripts/validate-presentation.py    构建期：时间/对比度硬错误；字幕读速、字号和行长为需人工核对的提示
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
scripts/negative-gate-check.py     负向抽查：验证真实技术/视觉支持错误会拦，简洁静态教学画面会放行
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

The negative gate suite checks geometry and camera-safety failures, timeline and cue errors, visual
declaration/source omissions, text/contrast and frame-prop faults, plus relevant delivery failures. Positive
controls must show that repeated layouts, missing optional notes, unfilled whitespace, absent beats, a still
camera and a static diagram with readable cue support all pass. Each blocking fixture pins an expected
message so a failure for an unrelated reason cannot count as a successful check. Run the suite to see the
current fixture and assertion tally; do not treat the tally itself as a quality score.
**A gate that exists in name only is the most dangerous defect.**

```text
python "<SKILL_DIR>/scripts/negative-gate-check.py"
```
