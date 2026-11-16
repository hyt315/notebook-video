# 检查：质量清单、美学系统、构图与呈现门禁

交付前的质量清单与美学系统，以及构图门禁、呈现门禁每类报错的含义和修法。

本篇各节：

- [Delivery acceptance checklist](#quality-checklist)
- [Official aesthetic system](#official-aesthetic-system)
- [构图门禁：把"审美"变成可执行检查](#composition-gate)
- [呈现效果门禁（`validate-presentation.py`）](#presentation-gate)

<a id="quality-checklist"></a>

## Delivery acceptance checklist

### 目录

- [Story](#story)
- [Architecture](#architecture)
- [Visuals](#visuals)
- [Subtitle](#subtitle)
- [Audio](#audio)
- [File validation](#file-validation)
- [Deliverables（交付物与事实卡）](#deliverables-原文迁自-skillmd)
### Story

- A concrete, verified payoff or tension is visible within 1.5 seconds; an honest open loop follows by 8 seconds.
- Each scene has one main idea and one physical action.
- The visual story remains understandable without narration.
- The opening gives a concrete, verified payoff or tension before context, and the storyboard identifies a later evidence-based callback.
- A meaningful state changes every 2–4 seconds.
- The final message holds at least one second.

### Architecture

- React + TypeScript + Remotion is the primary renderer.
- TTS milliseconds convert once to integer frames.
- Subtitle, animation and sound share the same FPS convention.
- Fonts and media resolve before the first rendered frame.
- Action audio is declared with its visible action.

### Visuals

- Background, chapter, header and subtitle match the canonical example.
- Every scene declares one primary **media kind** (`chart` / `console` / `code` / `graphic` / `text` / `metric`) — 这是默认路线的路由维度。`image-text` 只在场景用用户提供 / Commons / 授权图片时才出现（见 director.md#visual-director；技能不调用生图模型）。
- Concrete subjects use original, supplied or licensed imagery when seeing the subject materially improves comprehension.
- Generated imagery contains no baked labels, charts, logos or UI text; exact information remains in Remotion.
- Every raster is registered in `visual-assets.json` with source, prompt/description, crop policy and rights.
- Image scenes synchronize recognition, callout, relation and conclusion instead of placing a static image beside unrelated copy.
- Generated images receive only restrained crop reveal or push-in motion; annotations move independently.
- Every independently moving object is an independent component.
- Every large object has one home zone and one destination zone.
- Unrelated cards keep at least 70px separation, including airborne shadows.
- The central corridor contains at most one dominant temporary transfer object.
- A continuous process preserves one task object and changes its state at real stations.
- Floating objects stay above lower bases.
- Slot occlusion begins only after a visible crossing.
- Inserted modules finish fully behind the front lip with no residual fragment.
- Temporary components exit completely; no half corner remains.
- Dynamic shadow changes only when paper lifts.
- In the official engine, paper uses its locked lift-linked contact/environment shadow recipe; no component invents a conflicting shadow.
- In the official engine, display, title, body, label and micro copy use its locked type scale.
- In the official engine, system glyphs and emoji are not used as production icons; use its locked line-icon language.
- In the official engine, the whole-film grade is static and restrained; no animated grain or moving light texture.
- In the official engine, ordinary production edits stay inside `COPY`, narration, semantic captions, visual plan, registered image assets, timing and topic-specific scene objects.
- Data dashes move only during a real transfer and in the correct direction.
- Text-bearing paper has visible padding on all sides.
- Exact Chinese text and real brand assets are preserved.
- No malformed labels, invented logos or softened Chinese glyphs.
- No large accidental empty area during a spoken explanation.
- No clutter from unrelated dots, scraps, steam or continuous movement.
- No effect stack, miniature card pile or unused half-visible layer remains on screen.
- No global zoom, shake, animated noise, posterize or full-screen page turn.
- Shot camera: every shot declares one intent from the closed set (`establish` / `push-in` / `pull-back` / `pan-follow` / `reveal` / `micro-orbit` / `still`) plus an `anchor`; `scripts/validate-shot-motion.py` must prove the anchor stays fully visible at every keyframe (P0 = 0). Zoom ≤ 1.35 on shots carrying text. At least 3 camera moves per chapter (>=20s chapters; >=1 for shorter ones) and at least 3 distinct intents per film — a film with a frozen frame reads as page-turning.
- Scene skeletons: at least 3 of `Stage` / `Corridor` / `Split` / `Zoom`, and no two adjacent scenes share a skeleton (`scripts/validate-composition.py`).
- Visual media: at least 3 distinct media across the film (chart / console / code / graphic / text / metric), and every explanation scene carries at least one live component that changes state with the narration. A pure card-and-bullets scene is rejected.
- Density: every scene declares 3–5 functional zones and fills the lower quarter (bottom edge near y=876). An empty lower half is a PPT tell.
- Background readability: content that overlaps a locked background decoration zone (`theme.backgroundDecorZones`) must sit on a `CoverPanel`; the background bitmap itself stays untouched.
- Runtime overlap gate: after the first render, the console must show **no `OverlapGate` warnings** (text-vs-text overlap and paint-order occlusion, sampled every 15 frames). Intentional overlaps (shot handoff, header swap, metric value replacement) must be marked `data-gate-allow`; never use the allow-list to hide two different pieces of information colliding.
- Main-slot fill gate (render path): **no `SlotGuard` warnings** — the main slot of `StageFrame` hands over the whole remaining height (`h − pad×2 − header − stamp`), so the content must fill it (target ≥60%; the guard reports the occupancy every rendered frame and speaks up below 35%). A one-line content in a full-height slot is the measured failure mode (11%). Width is still yours to budget: `mainW = w − pad×2 − railW − 18`.
- Motion: progress-like bars animate `scaleX` (never `width`); numeric readouts use `tabular-nums` with fixed fraction digits; every element's multi-property entrance uses different clocks (see draftpaper.md#motion-design).
- Anti-PPT Functional Components: 技术概念（检索 / 记忆 / 上下文 / 契约 / 嵌入 / 安全）**不要**用一整排等大的要点卡去讲，要用**真的随旁白变化**的构件。可选件从真实存在的里面挑：`ConsoleWindow`（`media.tsx`）、`MetricGrid`（`media.tsx`）、`Funnel` / `ProgressRing` / `ChatThread`（`fxkit.tsx`）、`Chart` / `TreeView` / `NetworkGraph` / `ControlStack`（`src/components/`）。
  > 历史注：本条曾经点名 BrainwaveEEG / VectorRadarSonar / BM25TokenRibbon / HookMountBay / RedactionScanner / ChipContract 六件并要求 MUST use —— 那六件定义在 `index.tsx` 内部、**零 export、且没有任何一处 JSX 渲染过**，按本技能自己的「零引用」判据正是待删除项，已删除。**不要再把不可达的名字写成硬要求。**

### Subtitle

- Bottom-pinned pure caption text is present in every scene (no bar, no torn contour).
- No dark border, black side mark, inner line, orange locator or blue ring.
- One centered line, WenKai Lite 44px.
- `CaptionFitGate` measures every fully revealed cue with the loaded WenKai font in the real render browser; every cue fits within the canvas safe width.
- Partial reveal does not shift horizontally (hidden full-width placeholder).
- Internal punctuation remains; trailing punctuation (`，。！？；、,.!?;:`) is strictly stripped and hidden visually via `cleanFull` and gated character length. Trailing punctuation mark on screen is an immediate rejection flag.
- Caption segmentation is explicitly `semantic`, never `draft-character-count`.
- Every model/product name, benchmark, number-plus-unit expression and fixed technical term is listed in the protected-phrase manifest.
- No protected phrase crosses a cue boundary; no ASCII identifier is split between cues.
- Cue words flatten to the exact TTS word stream.
- Caption timing leads measured speech by no more than about 80ms.

### Audio

- Correct voice and complete narration.
- No hidden voice delay.
- Effects land on visible actions.
- Speech remains dominant.
- Integrated loudness is about -16 LUFS.
- True peak is no higher than -1.5dBTP.

### File validation

- H.264 video and AAC audio are present.
- 2560×1440 at native 30fps unless the user explicitly requested a genuinely native high-frame-rate production.
- Audio is 48kHz stereo.
- Video duration includes at least 0.7 seconds after narration.
- No black frames or truncated ending.
- No unintended scaling or softening pass.
- Contact sheet includes every scene.
- Films over 60 seconds include at least 24 evenly spaced frames plus dense motion sheets for the two most complex movements.
- Opening, scene boundaries, longest caption, hover/insert midpoints and closing frame are inspected manually.
- Opening range 0–360 is inspected at 0.5s, 2s, 4s, 8s and 10s; the primary claim is visible by 1.5s and the deferred question is paid off later.

Do not update the skill from a design proposal. Update only after the user approves the actual rendered film.

### Deliverables (原文迁自 SKILL.md)

Unless the user asks for less, deliver:

1. narration and time-coded storyboard (derived from the shot table);
2. a visual plan — this is the shot table itself: skeleton, media, live components, camera intent, anchor, zones, bottom-fill, transition, entry, beats;
3. semantic part manifest with layer and exit contracts;
4. `visual-assets.json` with source, prompt summary, crop policy and rights for every raster;
5. Chinese narration plus word timing JSON;
6. one-line semantic caption cues plus a protected-phrase manifest;
7. delivery-canvas H.264/AAC MP4 (2560×1440 for 16:9);
8. contact sheet and motion checks for long films;
9. editable source ZIP with fonts, licenses, audio and manifests;
10. delivery fact card verified against the baseline table below.

#### 交付指标事实卡 (Fact Card)

| 层级 | 检查项 (Metric/Item) | 测量实值 (Value) | 正常基线 (Baseline) | 状态判定 (Status) |
|---|---|---|---|---|
| L1 基础层 | 交付画幅与帧率 | 2560×1440 | 锁定 30fps 原生无重复帧 | 🟢 正常 |
| L1 基础层 | 响度与音频混音 | −16 LUFS / −1.5 dBTP | 48kHz 立体声 AAC | 🟢 正常 |
| L2 核心层 | 字幕与台词对齐 | 词级整帧同步 (msFrame) | 零断行拆分/零边缘伪影 | 🟢 正常 |
| L3 校验层 | 黑帧与图层穿透 | 0 处黑帧 / 零残留碎片 | 所有元件完整离场与遮挡 | 🟢 正常 |
| L3 校验层 | 构图门禁 | P0 = 0 | 骨架相邻不同款 / 活性组件覆盖 / 介质 ≥3 | 🟢 正常 |
| L3 校验层 | 重叠门禁 | OverlapGate 零警告 | 有意覆盖须标 `data-gate-allow` | 🟢 正常 |

Do not stop at prompts, still images, a silent animation or an unvalidated render.

<a id="official-aesthetic-system"></a>

## Official aesthetic system

This document defines the aesthetic layer preserved by the flat / cel track (see `locked-style-contract.json`).
This package contains one official aesthetic track, one canonical project template (`assets/lecture-template`) and two locked skins: `flat` (default) and `cel`. The old warm-ivory paper look and its `--classic` example project were removed in 3.2.0.

### Locked production grammar

The system preserves the per-shot restricted camera, subtitle geometry, native 30fps card motion, declarative audio tree, asset gate and final draw order while allowing the scene grammar to follow meaning. Before storyboarding, select one primary **media kind** for each scene (`chart` / `console` / `code` / `graphic` / `text` / `metric` — 默认路线的路由维度，见 media.md#media-routing); `image-text` only applies when a scene uses a user-supplied / Commons / licensed image; read `director.md#visual-director`.

Real images are an optional input layer: the skill does not call image models, so images come from the user, Commons / Openverse or other licensed sources, used for concrete subjects where they improve comprehension. Keep exact text, arrows, diagrams and timing in Remotion. A project must remain buildable with native SVG alone.

### Locked aesthetic core

The following values and helpers are part of the official engine and are not ordinary content-editing surfaces:

- `C`: approved semantic palette roles;
- `TYPE`: display, title, body, label and micro typography scale;
- `AESTHETIC`: subtitle width, paper radius/outline, texture, grid and grade values;
- `paperShadow(lift)`: contact and environment shadow linked to real paper lift;
- `LineIcon` and `CheckBadge`: one consistent line-icon language;
- `Grade`: restrained static whole-film vignette (flat ships none; cel a 3% ink corner vignette).

Semantic colors must come from `C`; material-specific neutral shades may remain inside the locked component implementation. Do not introduce new inline semantic colors, system glyphs, emoji, independent shadows or animated grain. Small optical adjustments are allowed only when they preserve the official visual result.

### Ordinary editable surface

Ordinary production models should primarily edit:

1. the `COPY` block in `src/index.tsx`;
2. `narration.txt`;
3. semantic caption lines and protected phrases;
4. scene timing constants when required by narration;
5. the visual plan and `manifests/visual-assets.json`;
6. generated or supplied raster assets in `public/illustrations/`;
7. topic-specific scene objects that preserve the same physical ownership and motion grammar;
8. **the wrapped component layer in `src/components/`** — import and use the components that ship with the
   template, parameterised per scene. This is an explicitly permitted surface: reach for a ready-made
   wrapped component before hand-writing SVG. The dependency boundary and the component rules live in
   [technique.md#dependency-policy](technique.md#dependency-policy); the template's `package.json` already declares those
   libraries, so no separate authorisation is needed to use them.

Stable semantic IDs must remain separate from display labels. Changing visible copy must not break scene branching, icon choice, z-order, transfer paths or slot occlusion.

### Visual rules

- Preserve spacious composition and one hero action per zone; scene count follows the content.
- Choose image-plus-text, pure text or pure graphic mode from meaning rather than repeating one scene family.
- Treat generated bitmaps as animated assets, never as the finished scene.
- Keep exact labels and diagrams outside the bitmap as live Remotion layers.
- Record source, prompt summary, crop policy and rights for every raster asset.
- Keep the bottom-pinned pure caption text at one centered line (no torn bar).
- Use browser-native caption measurement after the exact font is loaded.
- Use the official palette and type scale; do not invent per-scene styling.
- Use lift-linked paper shadows only for moving paper.
- Keep the grade static and restrained.
- Never lay a full-frame translucent wash over the background: the three backgrounds per theme keep their central ~70% calm on purpose, and a wash turns the corner characters into ghosts.
- Use the official line icons (`LineIcon`) as the primary icon language, instead of system glyphs or emoji.
  `LineIcon` glyphs come from `lucide-react`. Topic-specific marks (brand logos, technology identities) use
  `TopicIcon`: `simple-icons` for brands (single-colour paths, theme colour only) and `lucide-react` for line marks,
  with `strokeWidth` matched to `LineIcon`'s visual weight. See technique.md#dependency-policy §7.5.
- Preserve the same persistent task-card, shared-track and physical-slot logic.

### Future updates

For future aesthetic changes, work in a disposable project copy, render the complete film, obtain user approval, and only then overwrite the template, the theme files and the contract.

### Locked official elements (原文迁自 SKILL.md)

Keep these official elements locked until the user approves a future rendered replacement:

- React + TypeScript + Remotion rendering core;
- locked premium motion contracts shipped in the template: `JumpInText` per-glyph 3D flip titles, `ShimmerText` sweep on CTA strings, multi-keyframe figure roll-ins, per-word subtitle reveal, and the shot layer (see [camera.md#shot-language](camera.md#shot-language));
- fixed native 30fps motion, rendered and delivered on the single locked canvas: 2560×1440 (16:9);
- no duplicate-frame upconversion; use 60fps only when motion is authored natively at 60fps;
- mount only the active scene, with at most two scenes during a short handoff;
- animate moving objects with transforms instead of per-frame layout properties (**progress bars animate `scaleX`, never `width`**);
- the active skin's three locked background rasters (`main` / `chapter` / `quiet`, `flat` default or `cel`), chosen per shot by the backdrop rule;
- stable top-left chapter card and top-right technical header, both **outside** the shot camera;
- bottom-pinned pure caption text with per-word reveal, no decorative bar, no dark border or side artifacts;
- pure bottom subtitle with soft text shadow, no dark border, side marks, locator or ring;
- LXGW WenKai Lite as the unified CJK typeface plus Clash Display / Space Grotesk Latin accents, with WenKai registered as the CJK fallback face of every Latin display family (`src/fonts.tsx`) so no text ever falls back to a system font;
- TTS word timing converted once to integer absolute frames;
- independent semantic parts with explicit z-order, entry and complete exit;
- a spatial density budget: one hero action per zone, no temporary stack in the center;
- a shot layer: every shot declares one camera intent from the closed set plus an `anchor` that `validate-shot-motion.py` must prove stays visible (restricted recipes, not free curves — and not frozen framing);
- four scene skeletons (`Stage` / `Corridor` / `Split` / `Zoom`) with **no two adjacent scenes sharing one**, and at least three per film;
- content→medium routing: at least three distinct visual media per film, and at least one live state-changing component per explanation scene (**a pure card-and-bullets scene is a gate failure**);
- a shot table that references narration cues instead of hard-coded frame numbers ([scenes.md#scene-skeletons](scenes.md#scene-skeletons));
- background readability via `CoverPanel`: the locked background bitmaps stay as they are, and content overlapping a declared decoration zone sits on a feathered backing plate ([media.md#media-routing](media.md#media-routing));
- shared-track continuity when one object changes state across several stations;
- real slot geometry: insertable parts cross the slot, move behind the front lip and disappear fully;
- declarative narration and action effects inside the Remotion component tree;
- font/audio/image asset preload gate before the first frame;
- a visual plan selecting pure text/graphic scenes by default, with image-plus-text only after the user accepts the add-on;
- optional generated imagery as preloaded Remotion assets with prompt, crop and rights records;
- H.264/AAC output, automated QA, contact sheets and editable source package.

Do not write an experimental change into this skill until the user sees the rendered film and explicitly approves it.

<a id="composition-gate"></a>

## 构图门禁：把"审美"变成可执行检查

> 状态：**生效**。脚本：`scripts/validate-composition.py`、`scripts/validate-shot-motion.py`。

### 目录

- [1. 为什么必须有这一层](#1-为什么必须有这一层)
- [2. 十一项检查](#2-十一项检查)
- [3. 怎么跑](#3-怎么跑)
- [4. 失败时怎么办](#4-失败时怎么办)
- [5. 与运行时门禁的分工](#5-与运行时门禁的分工)
- [6. 交付门槛](#6-交付门槛)

### 1. 为什么必须有这一层

早期版本有大量强制条款，但**全部空转**：

- 早期 SKILL.md 与 `checks.md#quality-checklist` 明文强制技术概念必须使用活性组件（这两处条款现已由 `validate-composition.py` 的判据落地） —— 实测 34 个库组件里 **32 个引用数为 0**；
- 明文禁止"卡片堆文字" —— 样板片自己就是卡片堆；
- 9 个校验脚本**没有一条**能发现这件事。

**没有"会因为像 PPT 而拒绝渲染"的门禁，条款再多也会随时间退化。** 这一层就是那个门禁。

同时它也是"减负"的前提：条款可以少，但被检查的条款必须真的被执行。所以这里的规则**少而硬**。

### 2. 十一项检查

> 数法（2026-09-22 复核）：**P0 七项**（P0-1…P0-7）+ **P1 四项**（P1-7…P1-10）= 十一项。
> 本节标题原先写"八项检查"、目录那条链接又写"十项检查"且锚点指向 `#2-八项检查` —— 三个数互不相同，
> 现按实际条数统一成"十一项检查"（标题、目录链接文字、锚点三处一致；`#2-八项检查` 这个旧锚点已不存在）。

#### P0（阻断渲染）

| # | 检查 | 判据 |
|---|---|---|
| **P0-1** | 骨架重复度 | 相邻场景不得同骨架；全片 ≥3 种骨架（`Stage`/`Corridor`/`Split`/`Zoom`） |
| **P0-2** | 活性组件覆盖率 | 每个讲解场景（`explanation != false`）必须声明 ≥1 个活性组件；**纯卡片堆 → fail** |
| **P0-3** | 镜头意图多样性 | 全片 ≥3 种 intent（不含 `still`）；每章 ≥3 次运镜（**章节 <20s 时 ≥1 次**；后者在 `validate-shot-motion` 查） |
| **P0-4** | 密度硬条款 | 每镜 `zones` ∈ [3,5]（手作皮肤 journal / papercut / archive 为 [1,5]：一镜一个主体是手作片的常态，硬凑 3 区会逼出满屏卡片；皮肤以 `src/theme/active.ts` 为准）；**`bottomFill` 字段必须在**（缺字段=配置错误）。⚠️ 2026-09-21 降级：这里**只查存在性**，"到底填满了没有"由渲染期 `FillGate` 实测——见下 |
| **P0-5** | 介质多样性 | 全片 ≥3 种不同视觉介质 |
| **P0-6** | 镜头出界证明 | 逐镜、逐关键帧证明 `anchor` 完整落在可见窗内（见 `camera.md#shot-language` §3） |
| **P0-7** | beats 下标越界 | 逐镜扫场景源码里的 `b[k]` 与 `SHOTS.Sx.beats[k]`（**两种写法都扫**），k 必须 < 该镜真实拍数。越界取到的是 `undefined`：传进 `interpolate` 会**整帧渲染失败**，传进比较则**那件东西永远不出现**（两种都在成片里实测过，都不报错） |

#### P1（只警告，成片前人工确认）

| # | 检查 | 判据 |
|---|---|---|
| **P1-7** | 转场多样性 | ≥2 种（`cut` / `handoff` / `reveal`） |
| **P1-8** | 入场方式多样性 | ≥3 种（`rise` / `slide` / `fade` / `zoom`） |
| **P1-9** | 状态变化间隔 | 任意 120 帧（4s）内至少一次画面变化；静止 >45 帧提示补呼吸 |
| **P1-10** | 背景装饰可读性 | `contentBand` 与主题装饰区相交时须声明 `cover` |

> **P0-4 的来历与降级**：早期版本官方样片的接触表里，多个采样帧中部大片空白、下 1/4 常常空着——
> "画面下半空洞"是 PPT 感的主要来源之一。所以 `bottomFill` 是 P0。
>
> ⚠️ **2026-09-21 降级（这道门原来永远不会失败）**：本门禁原来校验 `bottomFill == true`，
> 而这个字段是生成分镜表的脚本**自己写死的常量**（`make-shots.py` 每一镜都写 `true`），
> `resolve-shots.py` 再原样透传——**生成器写 true、门禁要求 true，结构上不可能报错**。
> 实测成片里 17/21 镜的下 1/4 是空的，它一次都没响。
> 现在声明位**只查字段在不在**（缺字段是真配置错误）；真实判据交给**渲染期的 `FillGate`**：
> 它量的是画面（信息元素的最低边 vs y=876），不是声明。
> 判分方式随门禁阶段而变：**声明能查的只有"写没写"，"做没做到"必须实测**。

#### 横向空洞（实测，先只报不拦）

> **为什么加**：`FillGate` 原来只量纵向（信息元素最低边到不到 y=876），而且 `journal / papercut / archive`
> 三个手作皮肤**整条跳过**——cell 正是 journal。于是评审连着两轮说「八镜里五镜主体缩在一角、
> 四到七成画面是空的」，门禁一次都没响。
>
> **量什么**：拿同一批实测盒子落到 8×6 网格，每镜报四个数：
> `cells`（48 格占用）/ `blank`（整列没有任何元素的列数）/ `largest`（最大单体面积 ÷ 画面面积）/
> `widest`（最大单体横向跨度 ÷ 画宽）。
>
> **现在只报不拦**：它量的是版面审美，不是画错。数字同时落盘 `<工程>/renders/fill-coverage.json`。
> 落盘是**合并**写入、每条带 `at`（量的时间）：跑 `preview --shot=S6` 只量 S6，不会把其它镜的数字抹掉，
> 所以一个文件里可能同时有"刚量的"和"几轮前量的"，看 `at` 就知道哪条旧了。

##### 口径（这一版改过一次，第一版是错的）

第一版取「该镜第一帧」量。但镜头入场本来就在画元素（`entry` 有 22 帧展开），
于是六镜全被判成空洞——**那是假阳性**，评审说的「五镜」被这个口径"复现"出来纯属巧合。
现在的口径：

| 项 | 规则 | 为什么 |
|---|---|---|
| 取哪一帧 | 该镜**最完整的一帧**（格子数最多，平手时取 `largest` 更大者） | 量的是这一镜的终点构图，不是入场过程 |
| 条状主体 | `widest ≥ 0.45` 画宽即视为不空，不看面积 | 一条横贯画面的格带面积天然小；和 `fillAfter` 对文字版式豁免同理 |
| 组合装置 | `blank = 0` **且** `cells ≥ 24/48` 时视为不空，不看面积 | 照片 + 引线 + 网格这类「多个中等元素拼成一个主体」的版式，`largest` 按单个元素量天生只有 3%，但画面既不缩在一角也不算碎。S7 就是被这条误判的 |
| 阈值 | `largest < 0.06`（且不属上面两种豁免）→ 主体过小；`blank ≥ 3/8` → 横向空洞 | 先量后定：从这批数字里取，不靠感觉。前两条豁免对应「面积这个指标量不准」的两种情形：太细太长、太碎但铺满 |

##### 基线（cell 全片 8 镜，修正口径后）

```
S1 cells=28/48 blank=1/8 largest=0.16 widest=0.44
S2 cells=23/48 blank=1/8 largest=0.26 widest=0.43
S3 cells=19/48 blank=1/8 largest=0.08 widest=0.32
S4 cells=32/48 blank=0/8 largest=0.29 widest=0.82
S5 cells=27/48 blank=0/8 largest=0.03 widest=0.84   ← 靠条状豁免过
S6 cells=28/48 blank=0/8 largest=0.14 widest=0.36
S7 cells=24/48 blank=0/8 largest=0.02 widest=0.37   ← 靠组合豁免过（改前网格只到画高 64%，右下空掉 30%）
S8 cells=28/48 blank=0/8 largest=0.15 widest=0.43
```

（这张表是 `sweep` 一条命令量出来的，不是拼几次预览拼的。口径是「每镜切点前最近的 15 倍数帧」，
和整片渲染时「整镜里扫、取最完整帧」差 2–3 格——整片渲染那次数出 S5=30、S8=30，判定不变。）
**覆盖率落盘只有两个来源**：整片 `render` 和 `sweep`。`preview` / `render-range` / `review-frames` 是窗口渲染，
量到的是「窗口内最完整帧」（60 帧窗口把 S1 记成 25，整镜是 28），只打印不落盘，免得假数字冒充整镜读数。

**八镜全部过阈值。** 真正改过的只有 S5、S6、S7 三镜，而且都不是「排不满」：
S5/S6 是「先画骨架、再往骨架上填」，S7 是「主体只铺到画高 64%，下半空着」。

> 一个已经堵上的坑：默认 `preview --seconds=30` 只覆盖前六镜（0–900 帧）。
> **S7/S8 是补跑 `--from=32 --seconds=18` 才被量到的**——在此之前它们的空场从没进过任何检查。
> 现在不用记这件事了：`sweep` 每镜取一帧量一遍（八镜约 60 秒），
> 少一镜会明写「未量到」，不会再出现「全过其实只量了前六镜」。

##### 一条可复用的写法（比阈值更重要）

> FillGate 量的是**每镜最完整的那一帧**（`fill-gate.tsx` 取「最完整的那一帧」），所以镜头开头空着是正常的。不要为了开头好看把东西提前摆上——出现规则见 [draftpaper.md#reveal-rules](draftpaper.md#reveal-rules)。

**空洞处补一层「属于主体」的东西**，不是补一句话。已验证的四个装置：

| 装置 | 什么时候用 | 位置 |
|---|---|---|
| 尺寸线 + 两端刻度 + 数值 | 主体是一个有尺寸的实物，观众需要知道它多大 | `cell/src/scenes.tsx` S6（`dim-v`/`dim-t`/`dim-b`） |
| 局部放大 + 引线 | 主体由很多小单元组成，需要说明"其中一个是什么" | S5（右下 230×180 盒 + `s5-lead`） |
| 标尺 | 需要「量」这个动作本身，而不只是结果 | S5（`ruler` + 两端 `tick`） |
| 引线批注指回主体 | 有一个术语/数字要落到画面某处 | S4（`cells-lead` 从词拉到镜片） |

判据很简单：**把这一层拿掉，主体还是不是完整的？** 是 → 那层是装饰（S6 原来浮在空白里的
「1 立方英寸：边长 2.54 厘米」就属于这类，已删）；不是 → 它是内容。

##### 不该做什么

- 加「功能分区」凑覆盖率：会逼作者往空白里塞清单（见 `fill-gate.tsx` 注释）。
- 放大卡片凑面积：`largest` 变大了，观众还是不知道该看哪儿。
- 给空白处单独加一行字：那是把空场翻译成了文字，没解决空。

### 3. 怎么跑

```text
# 先解析分镜表（生成 src/shots.ts 与 shots.resolved.json）
python scripts/resolve-shots.py PROJECT_DIR

# 构图与活性门禁
python scripts/validate-composition.py PROJECT_DIR
python scripts/validate-composition.py PROJECT_DIR --strict     # P1 也算失败（交付前建议）
python scripts/validate-composition.py PROJECT_DIR --json       # 机器可读

# 镜头出界证明 + 每章运镜配额
python scripts/validate-shot-motion.py PROJECT_DIR
```

退出码：`0` 通过（可含 P1）/ `1` 存在 P0（或 `--strict` 下存在 P1）/ `2` 用法或文件错误。
设了环境变量 `NV_GATE_JSON=<文件>` 时，每条 P0 / P1 另外追加一行统一格式的 JSON（见 `technique.md#auto-engine`「门禁分工」）；make-video 汇总成 `renders/gates.json`。
两者都是**纯标准库、只读**，可直接放进 CI。

### 4. 失败时怎么办

| 失败项 | 正确修法 |
|---|---|
| P0-1 相邻同骨架 | 换骨架，**不是**改 `shots.json` 里的字符串。构图真的不同才算换。 |
| P0-2 纯卡片堆 | 找出这一段"机制是什么"，换成能演示它的构件（见 `media.md#media-routing` §2）。 |
| P0-3 运镜不足 | 给章节首镜加 `establish`，给聚焦处加 `push-in`；不要为了凑数加无意义甩镜。 |
| P0-4 下 1/4 空洞 | 补一个真实信息元素（指标条 / 结论条 / 清单），**不是**放大现有卡片凑面积。这一条的**判据现在在渲染期 `FillGate`**：改完要重渲那一镜的抽帧看 `[FillGate]` 出水，构建期只会告诉你"字段写没写"。手作皮肤（journal / papercut / archive）不判这一条（大留白是设计）；flat / cel 的警告按镜头去重，渲染结束汇总成一行 `FillGate: N shots (S2,S5,…) bottom-quarter underfilled`。 |
| P0-5 介质单一 | 至少换一段内容用另一种介质（图表 / 控制台 / 大字 / 补丁）。 |
| P0-6 出界 | 收窄运镜幅度或把 `anchor` 改成真正的解说对象外框；**不要**把 anchor 改小来绕过检查。 |
| P1-9 长时间无变化 | 在最长间隔中点加一次状态变化（元素入场 / 数值变化 / 主体相位切换）。 |

> **不要把门禁改松来通过。** 如果某条判据在真实题材上系统性误报，说明判据要改，
> 但那要经过"出片验证 + 用户确认"，而不是当场调阈值。

#### 4.6 修复顺序（实战经验）

先修**组件级**（一次修好全部场景），再修**场景级坐标**。本版实测的四个组件级根因：

1. `ZoomStage` 的缩放矩阵 math 写错（`translate` 用未缩放单位）+ 没有按内容尺寸设上限
   → 四个场景被裁 100–500px。**修法**：三段式 `translate(框心) scale(k) translate(-焦点)`
   ＋ 传 `contentW/contentH` 让缩放自动钳制。
2. `Corridor` 的状态标签与站点标签之间没有垂直预算（只剩 3.6px）→ 四个走廊场景全部压字。
   **修法**：状态标签放到承载物**上方** 46px，站点标签下移 96px。
3. 固定像素宽度撞上随 `railW` 变化的动态列宽（`w=1060 > mainW=1035`），不透明控制台压住轨道文字。
4. 承载物 124×110 完全盖住站点圆环与对勾 → 缩小承载物 / 把到站反馈画在环外侧。

### 5. 与运行时门禁的分工

| 门禁 | 时机 | 抓什么 |
|---|---|---|
| `validate-shot-motion.py` / `validate-composition.py` | **构建期**（不渲染） | 构图 / 骨架 / 介质 / 镜头配方与出界 |
| `CardFitGate` | **渲染期**（浏览器内） | 文字溢出卡片（早期版本实测抓到 4 处真实出格） |
| `SlotGuard` | **渲染期**（出图路径，`StageFrame` 内） | `StageFrame` main 槽的**占用率**（槽内有内容的最内层元素并集高度 ÷ 槽高，<35% 出声）——抓的是"槽给足了、内容没填满"（实测一镜 428px 的槽只用了 11%）；槽宽仍按 `mainW = w − pad×2 − railW − 18` 自己先算 |
| `OverlapGate` | **渲染期**（浏览器内，每 15 帧抽样） | **文字两两重叠 + 文字被遮挡**（本版实测抓出 3 类真实缺陷；有意覆盖用 `data-gate-allow` 白名单） |
| `CanvasBoundsGate` | **渲染期**（浏览器内，每帧） | **含文字的叶元素**（HTML 叶 + SVG `text`/`tspan`）的**墨迹 rect 越出视口**（= composition 尺寸，输出像素口径）。这是此前**四道门禁都不管**的一类：`ClippingGate` 只认 SVG 图元、`CardFitGate` 只管卡片内溢出、`OverlapGate` 管互相压、`FillGate` 管铺到多低，而构建期 `coords-lint.py` 明确把 `Corridor`/`ZoomStage`/`StageFrame` 这类**布局件**排除在外 —— 第 ⑥ 页「按 Flash 结算」被画布右缘裁掉就是这么漏过去的。**v2 只判文字叶元素**（不判图形/版面件、不做设计坐标回折），判据与代价见 §5.2 |
| `CaptionFitGate` | **渲染期**（浏览器内） | 字幕超宽（按当前画幅与主题真实字重/字距测量） |
| `validate-caption-sync.py` / `validate-semantic-breaks.py` | 构建期 | 字幕与 TTS 词边界一致、保护短语不被切开 |
| `validate-presentation.py` | 构建期 | **呈现效果**：beat↔cue 时间接近、字幕阅读预算（Netflix 中文规范）、字号地板 13px 与正文色对比度（WCAG 4.5:1）。现有门禁都没问过「讲与画对不对得上、读不读得过来」——见 [checks.md#presentation-gate](checks.md#presentation-gate) |
| `notebook-video validate-video` | 交付前 | 时长、音视频编码、**色彩契约**（四项元数据，见 §6.1）、响度、黑帧 |

**分工原则**：能用算术在构建期证明的，不要留到渲染期；只有需要真实字体/布局测量的，
才放在浏览器内。

#### 5.2 渲染期门禁 `CanvasBoundsGate`（画布越界 · v2 简版）

**来历（实测，不是假设）**：接触表第 ⑥ 页第三站的标签块越出画布右缘被裁 ——
文案「按 Flash 结算」实际渲成「按 Flash 结」。根因是 `Corridor x={100} w={1720}`
让标签块伸到设计 x=2010，而组件内标签块固定 `left: pts[i]-150, width: 300`。
**这一件当时是用户用眼睛看出来的，四道渲染期门禁 + 构建期一条都没响**：
`ClippingGate` 的选择器里没有 div（这是 div 画的布局件）、`CardFitGate` 只量卡片内、
`OverlapGate` 只量互相压、`FillGate` 只量铺多低，`coords-lint.py` 又把布局件排除在外。

**判据（v2 · 2026-09-22 换实现）**：
**含文字的叶元素**（HTML 叶 + SVG `text` / `tspan`）的**墨迹矩形**，扣掉会裁切的祖先后，
仍越出视口（= composition 尺寸）≥ **6 像素** → 出声；**落定态**（有效不透明度 ≥ 0.98）越界 ≥ **20 像素** →
硬拦（`cancelRender`，rc≠0 且不产出任何图）。
文件规模：**468 行 → 231 行**（其中判据代码 144 行 + 75 行"为什么"注释 —— 本仓库惯例；
仓库外那份参考简版是 117 行（代码 108）+ 硬拦纪律的 `release()` 处置）。

- 判据点落在**墨迹**上：文字用 `Range` 取并集（块级元素整块宽不是字，居中文字会被整块宽误判）。
- **硬拦条件是「落定态 + ≥20 像素」两条同时成立**（与 `ClippingGate` 同口径）。
  ⚠️ 与仓库外那份参考简版有一处**有意差异**：参考版的**代码**是"任何 >6px 越界即硬拦"（与它自己文件头的
  注释不一致 —— 那里写的是"落定态且越界 ≥20 设计像素"）。本仓库取后者：入场途中元素还在画布外飞是运动、
  不是版面错误，在交付渲染的最后一刻为它硬拦不划算。实测这次抓到的两处（26px / 27px）**都在门槛之上**，
  两种口径的命中结果一致。
- 「扣掉会裁切的祖先」= 取景框（`ZoomStage` 视口、接触表里 scale 过的格子）是**有意**裁切，
  被它裁住的部分不算越界；铺满整个视口的祖先不算裁切（与它求交是恒等操作，却会把"越出画布"一起抹掉）。
- 阈值单位是**输出像素**（`2560×1440` 输出上 20px ≈ 15 设计像素）：**不做设计坐标回折**。

**它不查什么 / v2 砍掉的四件（每件都写了代价，别高估这道门禁）**：

| 不做 | v1 怎么做 | 为什么砍 | 代价（如实写） |
|---|---|---|---|
| 设计坐标回折 | `[data-design-root]` 实测比例 k + `ShotCamera` 等比特换求逆 + 世界层判定（3 个近似函数） | 两种口径在接触表上抓到的是**同一批**真缺陷；在 2560×1440 的片子上它一次真缺陷都没报出过 | 片子上的阈值是**输出像素**；换 `--scale` 时判据跟着输出走，不跟设计坐标 |
| 图形 / 版面件分支 | SVG 图元 +「有可见边框或实底且含文字」的块 | 这半边与 `ClippingGate`（图元被 `<svg>` 视口或 `overflow` 祖先裁）**在同一批元素上重复报** —— 只判文字叶元素天然避开这个重复 | 越出画布但**一个字都没有**的装饰块（如斜纹胶带类纯图形装饰）不判；`ClippingGate` 也不管它（那是"没有裁切祖先"的情形）—— **已知空白** |
| 一整套排除规则 | `z ≥ 140` 锁定 chrome 层 / 铺底底托 ≥92% 画布 / 小型取景框内的放大内容 | 三条的存在意义全是"别让**图形/版面块**误报"，而 v2 根本不判图形与版面块 | 无：那三类本来就不是文字叶元素（chrome 层里的**文字**会被判，实测接触表上零报告） |
| 按帧抽样 + 事件帧 `watch` | 每 15 帧 + 关键帧强制抽样 | 少一层采样逻辑；一次 DOM 扫描 + Range 量字在帧预算内 | 每帧都量：**整片渲染没有实测过**（本次只跑了 still，每帧测量对整片耗时的实际影响未被证明；片子上若发现渲染变慢，这里是第一嫌疑） |

- **相机不计入**：v2 没有相机逆变换，所以被运镜放大推到画布外的文字**会**出声（那是运镜，不是版面错误）。
  这就是**片子那条挂 `warn` 而不是 `block`** 的原因（见 §6）。实测抽帧：模板片子帧 300 / 900 零报告，
  但这条误报面**存在**，在这里写清楚 —— 它也是"片子不上 block"这个决定的依据之一。

**何时会响**：

- **硬拦（`cancelRender`，rc≠0 且不产出图）**：仅在 `mode="block"`（接触表）下，
  元素**已落定**（有效不透明度 ≥ 0.98）且在输出像素里越出 ≥ **20 像素**。
  落定前（入场途中元素还在画布外飞）只出声不拦 —— 那是运动，不是版面错误。
- **只出声**：`mode="warn"` 档（片子）；未落定的越界。
- **覆盖率日志**：每 150 帧一次 `[CanvasBoundsGate] @帧 扫过 N 个文字叶，无越界`
  （探针里开 `debug` 则每帧都打）—— 让「没报」与「没跑」可区分。扫过 **0** 个要当异常查。

**怎么修**（按出现顺序处理，别调阈值）：

1. 看日志里的文字与越界量（形如 `按 Flash 结算 越出右缘 26px`）—— 直接能定位到组件。
2. **容器给窄一点 / 内容收回来**：本例是 `Corridor` 的 `x/w` 给太满，
   让端点标签块（`pts[i] ± 150`）伸出了画布 —— 改成 `x={130} w={1580}`（两端对称留 190px）。
   `skeletons.tsx` 里的注释记着这条口径。
3. 内容确实要出画布（有意出血/取景）：在组件上标 `data-gate-allow="<理由>"`，
   **不要**把阈值调大 —— 那会让"半个字被裁"这类缺陷重新变得看不见。
4. 接触表这类**目录 composition**：格子摆不下就换页或改成两行，别让第 N 件落在画布外（见下）。

**真实命中之一（已修，可当"这条门禁到底抓什么"的实例）**：接触表第 ③ 页声明 **5 件**、
而 `Grid4` 只有 **4 格**，第 5 件（`FitTextBox · 中文反推字号（封装层）`）被摆到 `top=1076`，
整格落在 1080 高的画布外 **466px** —— 渲出来的第 ③ 页只有 4 格，那件组件在接触表上**根本看不见**。

修法：给"一页 5 件"一张自己的格子表（`showcase.tsx` 的 `Grid5`：3 列 × 2 行，格子 610×470，
舞台等比 0.7），**不是**往 4 格里塞第 5 件 —— 画布高 1080 放不下第三行，宽 1920 也放不下 3 个 900 宽的格子
（3×610 + 2×25 间隙 + 2×20 边距 = 1920，刚好铺满且左右对称；纵向沿用 76 / 576 两行，页间节奏不变）。
第一版门禁的验收记录见 CHANGELOG 归档：17 页在 block 下逐页抽帧，**每页 rc=0 且有图、零报告**；
与修前对比**只有第 ③ 页的像素变了，其余 16 页逐字节相同**。

**v2 的实测（2026-09-22，夹具工程 `.tmp-simplify-verify`，复用现成 `node_modules`，用完可删）**：

| 场景 | 怎么造 | 期望 | 实测 |
|---|---|---|---|
| 原样接触表 6 页（帧 35 / 65 / 95 / 155 / 275 / 395） | 直接用**修好后**的 `showcase.tsx` | rc=0、有图、零报告 | rc=0、有图；4 页开着 `debug` 各打出一条覆盖率：**扫过 27 / 25 / 20 / 74 个文字叶，无越界** |
| 第 ⑥ 页缺陷（帧 155，`mode="block"`） | 把 `Corridor` 改回历史值 `x={100} w={1720}` | rc≠0、不出图、点名同一处 | **rc=1、无图**、`共 2 处文字越出画布（落定态 2 处）：按 Flash 结算 越出右缘 26px \| 账单只按 Flash 价 越出右缘 26px` |
| 第 ③ 页缺陷（帧 65，`mode="block"`） | 第 ③ 页改回 `Grid4`（第 5 件落回画布外） | rc≠0、不出图 | **rc=1、无图**、`共 1 处文字越出画布（落定态 1 处）：FitTextBox · 越出下缘 27px` |
| 片子（帧 300 / 900，`mode="warn"`） | 原样模板片子 | rc=0、有图 | rc=0、有图；帧 300 的覆盖率：`扫过 15 个文字叶，无越界`（该帧两道门禁同挂，见下） |

**与 `ClippingGate` 的重复报（v1 遗留问题，v2 的实测对照）**：v1 在"图形越出 `<svg>` 视口"那半边与
`ClippingGate` 会对**同一批元素**各报一次。v2 只判文字叶元素，所以同一处**只会有一次报告**。
实测（把 `ClippingGate(mode="warn", sampleEvery=1)` 与 `CanvasBoundsGate` 挂在**同一条 composition** 上）：
第 ⑥ 页缺陷那一帧（帧 150）`CanvasBoundsGate` 报 2 处（26px × 2），`ClippingGate` 同帧打的是
`图形要素扫过 16 个，无被裁` —— **它跑了、但没有对同一处出声**。反过来也成立：帧 395 上
`ClippingGate` 报了 `path 超出 svg[svg 视口] 20833px`（那是**图形**被容器裁，不是文字出画布），
`CanvasBoundsGate` 同帧报的是"扫过 74 个文字叶，无越界" —— 两道门禁各管各的，交集不在同一处。
残留的理论重叠面（写清楚，不假装为零）：SVG `text` / `tspan` 若**既越出 `<svg>` 视口、可见部分又越出画布**，
两道门会各报一次 —— 但那时报的是**两件事**（"被容器裁了一半" vs "文字还出了画布"），不是重复。

**负向夹具（渲染期门禁没法在构建期跑）**：`scripts/negative-gate-check.py` 的 **AB0–AB4**（静态检查：
接线、档位、硬拦纪律、判据收窄各一条）；真渲染的夹具工程建在演示目录之外（本次是 `.tmp-simplify-verify`，
与技能仓库同级、复用现成 `node_modules`、可随时删掉重建）。**别把渲染夹具塞进交付工程里**：
它的存在意义就是"喂坏输入必须拦住"，留在工程里只会污染成片。

### 6. 交付门槛

- `validate-composition.py` **P0 = 0**；
- `validate-shot-motion.py` **P0 = 0**；
- P1 项逐条人工确认（每条都要有结论，不能"没看"）；
- `CardFitGate` / `CaptionFitGate` 在整片渲染中没有触发 `cancelRender`；
- **`CanvasBoundsGate` 在片子（`NotebookVideoFilm`）上是 `warn`**（2026-09-22 改，与接触表**不同档**）：
  渲染日志里要确认**有没有** `[CanvasBoundsGate]` 的出水 —— 有出水就逐条人工确认（那是"文字可能被画布切掉"
  的嫌疑，不是自动放行）；它**不再**在片子上硬拦。理由：v2 判据的实测来源全是接触表，
  而硬拦发生在**交付渲染的最后一刻**，判据一旦误报，代价是整片不出（见 §5.2 的"砍掉的四件"）。
  等它在片子上抓到第一处真缺陷，再谈升回 block —— 这条口径由 `negative-gate-check.py` 的 **AB3** 夹具守着。
- 接触表（`NotebookVideoShowcase`）的 `CanvasBoundsGate` 保持 **block**：
  第 ③ 页那处真实越界（第 5 件落在画布外 466px）已修在 `showcase.tsx` 的 `Grid5`（见 §5.2）。
  件整件看不见 = 目录页缺件，属于画错了，不能退回 warn；
- **色彩契约（新增）**：`validate-video` 断言交付 mp4 的
  `color_range / color_space / color_transfer / color_primaries` 精确等于 `tv / bt709 / bt709 / bt709`，
  任一项不符即 fail（打印实际值与修复提示）。见 §6.1；
- 若某条判据被人工判定为误报，**记录在案并说明理由**，不要静默放宽。

#### 6.1 色彩契约断言（`validate-video`）

**补的是什么缺口**：色彩这一层，生产端有两道（`--color-space=bt709` + 渲染后 `h264_metadata` 回写 SPS VUI，
见 `technique.md#windows-compatibility`），**交付端一道都没有** —— 谁把参数删了不会被发现：片子照样渲得出来、
看上去也正常，但四项元数据退化成 `pc / bt470bg / unknown / unknown`，严格播放器按 BT.601 + 满幅解释，
饱和色偏移。

**判据**：四项精确等于 `tv / bt709 / bt709 / bt709`。缺字段的流 ffprobe 不返回该项，一律按 `unknown` 报出来。

**为什么只认这一个组合，"等价组合"论证如下**（不要把它放宽成"看起来自洽就行"）：

1. 交付画布都是 SDR 网络播放：`pc`（满幅）会被当有限幅解释而压暗/偏色，`bt470bg`（BT.601）与 `bt709`
   矩阵不同，同样偏色 —— 这两项就是本仓库上一轮修掉的缺陷本身，放行等于把缺陷放回来；
2. "自洽"无法只从这四项推出来：`pc + bt709×3` 在字段上也自洽，但**不是本链路产的片**
   （渲染端已按 `range=limited` 转换过像素，见 `technique.md#windows-compatibility` 第 1 条），
   放行它等于把"标错范围"当合格；
3. 门禁的职责是抓**漂移**，判据就该精确等于契约，而不是"看起来合理"。

**只挂交付门**：Remotion 自己 stitch 出来的 raw mp4（未经 `h264_metadata` 回写）本来就不满足这四项，
所以这条断言只在 `validate-video` 上，不去卡渲染路径。

**正反对照（实跑）**：

- 反例 —— 老片 `overview-film/renders/film.mp4`（四项里两项 unknown）→ **rc=1**：
  `color_range = pc（合同要求 tv）` · `color_space = bt470bg` · `color_transfer = unknown` ·
  `color_primaries = unknown`，附 `pix_fmt=yuvj420p`；
- 正例 —— **新渲的短片段**（`render-range` 第 300–599 帧，2560×1440）→ **rc=0**：
  `container valid: H.264/AAC 2560x1440 30fps, 10.048s` /
  `color valid: color_range=tv color_space=bt709 color_transfer=bt709 color_primaries=bt709 (pix_fmt=yuv420p)` /
  `audio valid: -17.1 LUFS, -3.8 dBTP` / `No black frames detected.`

<a id="presentation-gate"></a>

## 呈现效果门禁（`validate-presentation.py`）

> **数量口径**（2026-09-22 复核）：本道加入时全技能 9 道门禁、它是第 10 道；**现在是 14 道** ——
> 构建期 6 + 渲染期 7 + 成片后验 1（表见 [scenes.md#handwritten-scenes](scenes.md#handwritten-scenes) 的 The gates），本道是构建期那 6 道之一。
> 其它门禁查的是「画面里**有没有** / **够不够多** / **会不会撞**」。这一道查的是它们**都没问过**的那一层：
> **观众此刻该看哪里、读不读得过来、讲的和画的对不对得上。**
> 纯算术、不需要渲染、零新增数据模型——与其它构建期门禁同一形态。调研与依据见 `呈现效果调研.md`。

运行：

```bash
python scripts/validate-presentation.py PROJECT_DIR [--json]
# 或 CLI：
node scripts/notebook-video.mjs validate-presentation PROJECT_DIR
```

退出码：`0` = P0 为 0（通过）· `1` = 有 P0 · `2` = 用法/文件错误。

### 一、判据（每条都给可计算形式）

#### G-1 时间接近（P0）——把授权契约第 9 条变成代码

契约原文：「元素出现帧绑到讲到它的那一句」。数据早就有（`shots.json` 的 `beats` 是从 cue 推出来的），**只缺断言**。

| # | 断言 | 可计算形式 |
|---|---|---|
| ① | beat 落在本镜区间内 | `cueFrame(beat.cue) + beat.offset ∈ [shot.from, shot.to]`（**含 to 边界**：允许"切在下一句起点"的那一拍） |
| ② | beat 声明的 cue 属于本镜 | `cue ∈ [cueFirst, cueLast + 1]`（同上，允许 +1 的边界拍） |
| ③ | 不提前剧透 | `beat.offset ≥ −12 帧`（0.4s） |
| ③b | **不拖后**（不得晚于那句讲完） | `beat.offset ≤ 该句帧数 + 8`（`BEAT_LATE_FRAMES`）。超出 = "台词已经讲完，元素才出现"，与台词脱节 |
| ③b-P1 | 贴边预警 | 距上界只剩 ≤4 帧（`BEAT_TIGHT_FRAMES`）→ P1。**合法但脆**：配音或 cue 表一变就先从这里挤成 P0 |
| ④ | 每条 cue 至少有一拍 | 本镜 `cueFirst..cueLast` 全被 `beats` 覆盖；确实不需要的必须在 `shots.json` 里显式写 `silentCues: [i]`（**要写出来才放行**） |

> ⚠️ **下界与上界缺一不可，而且 8 帧这条容差是「承重墙」不是安全边际**（复核两轮实测后如实写清）：
> · 第一版只有③（防提前），`{cue:0, offset:200}`（台词讲完 6.7 s 才出现）实测 **PASS** —— 这是复核抓到的真漏洞，③b 就是补它的。
> · 上界贴着真实数据：**模板最紧的合法拍就是 `offset = 该句帧数`**（"这句讲完时那拍出现"是设计约定），
>   把 8 帧容差**整个吃掉**（实测余量恰好 8 帧）。demo 上更紧：S8/cue14 只剩 **2 帧**、S7/cue13 剩 **5 帧**（修数据前）。
> · 所以：**任何一次换配音 / 重算 cue 表，都必须重跑本门禁**；"上界贴着数据"这件事不许被当成有安全边际。
>   贴边的合法拍会被 ③b-P1 单独点名，好让下一个人先看见它，而不是等它变成 P0。
> · 修数据的方向永远是"把拍挪回句内/句末"，**不是把容差调大**——调大就放走了"讲完才出现"这类脱节。

> ⚠️ **与调研报告原文的差异（重要）**：报告写的形式是 `|beat − cueStart| ≤ 6 帧`。
> **照抄会给正确的数据报 P0**：我们的 `beats` 本来就允许句内偏移（`{cue:13, offset:100}` = "同一句的第二拍"），
> 现有的 S7/S8 各有一处，逐字判会被报成偏差 96–100 帧。所以真实可检查的形式是
> **"beat 落在它声明的那句/那一镜的范围内、且不提前也不拖后"**，而不是"必须贴住句首 6 帧"。
> 这条判据的实证依据：temporal contiguity（PMC12691884 逐字定义）+ 视听线索同步实验（JEP 2019, DOI 10.1037/edu0000285）。

#### G-2 字幕阅读预算（P0）——Netflix 中文（简体）Timed Text Style Guide

| 判据 | 值 | 说明 |
|---|---|---|
| 阅读速度 | ≤ **9 加权字/秒** | 成人档（儿童 7）。**加权**：CJK 计 1、ASCII/数字计 0.5 —— **不需要分词**，正好绕开"按空格分词对中文失效"的坑 |
| 单行宽度 | ≤ **16 加权字** | 同上 |
| 行数 | ≤ **2 行** | 同上 |

数据：`manifests/caption-cues.json` 的 `text / start_ms / speech_end_ms`（**零新增数据**）。

#### G-3 可读性底线（P0 地板 + P1 档位）

| 判据 | 档位 | 依凭 |
|---|---|---|
| 任何 `fontSize < 13` | **P0** | 13 = 技能自己的 `MIN_LABEL_FONT`（`components/data.tsx`），**不是新魔数**；报告建议把这条既有政策从"图元标签"扩到全库 |
| `fontSize ∈ [13,16)` | P1（按文件聚合） | "标注 ≥16"档 |
| 正文色 `ink` / 反白 `white` on `ink` 对比度 < 4.5:1 | **P0** | WCAG 2.2 SC 1.4.3（大字号 3:1；**不四舍五入**，4.499 不通过） |
| `muted` on 表面 < 3.0 | **P0** | muted 是装饰性 kicker，按大字档判 |
| `muted` 3.0–4.5 | P1 | 同上，提示一档 |
| **`*Ink` 文字安全色**在任一纸面上 < 4.5:1 | **P0** | `blueInk/orangeInk/greenInk/goldInk/redInk` 是**专门**用来当文字色的（约定与来历见 `themes/system.md` 的"文字安全色"一节）：它们不过，就等于"把强调色压暗到能当文字用"这个约定是空话。**这一条同时是新增机制的自检**——没有它，加了 Ink 也没人验 |
| 被 `color:` 用过的**任意其它调色板键** on 纸面 < 4.5:1 | P1（按主题聚合） | 用原色（或 `orangeDeep` 这类填充 token）当文字色。**修法是换成对应的 Ink 变体，不是调松门禁** |
| 彩色填充上的白字 < 3.0 | P1（按主题聚合） | 见下"已知真实缺陷" |

> **遇到"强调色当文字色"该怎么做（本轮的处置，照做就行）**：① 这个词位本来就该是文字 → 换成对应的 `*Ink`；
> ② 这个 token 同时还要当填充（如 `orangeDeep` 是章节序号渐变的深色端）→ **原值保留给填充，文字位改 `orangeInk`**；
> ③ 这个 token 只当文字用（如 `headerAccent` / `headerSub`）→ 就地把它压到过线（同色相按 WCAG 反解）。
> 实测这一步在模板上把 `flat: orangeDeep`（4.19:1）这条 P1 清掉了（同批另两条落在已删除的皮肤上）。

> ⚠️ **这道对比度检查的能力边界（复核实测，别高估它）**：它只读 `theme/*.tsx` 里 `palette` 那个字面量，
> 且只认**标准键名**。实测两条绕过路径都走得通：
> ① **硬编码文字色**（`<div style={{color:'#dcdcdc', background:'#faf7f2'}}>` = **1.28:1**，本仓 `contrast()` 复算 = 1.283）→ **rc=0 完全不报**；
> ② **把正文色改名**（palette 里加 `fg:'#eeeeee'` 并当文字色用）→ 只报 P1，不阻断。
> 同一类漏检面还有两种常见写法：**`linear-gradient()` / `conic-gradient()` 里的停靠色**（颜色在字符串里，
> 且是两层叠加后的实际对比）、**SVG 元素的 `fill` / `stroke`**（不是 `color`）——都读不到。
> 也就是说：**它能拦"用标准键写错了色值"，拦不住"换个写法压低对比"**。
> 真要在渲染期量真实 DOM 的 computed color/背景（连硬编码、渐变、SVG fill 一起抓），属于 T2 的 FocusGate
> （尚未实现）/G-9 那一批（调研报告 §5.2），**本轮没做**。

> ✅ **扫描口径（第三轮复核提出后已修）**：本门禁与 `import_integrity` 都**只扫"值位置"**——
> 扫描前把注释内部与**字符串字面量内部**统一抹成空格（长度与行号一字不动，所以行号永远等于编辑器里那一行）。
> 于是：注释里的反例（"`fontSize: 8` 是禁止写法"）、**模板字符串里的代码样例**
> （接触表/测试页里 `const CODE = \`import X from './y';\`` 就是，本仓库确实这么写）都不再被当成真代码。
> 遗留边界（写清楚，不死磕）：**如果哪天真的把可执行的 import/字号写在字符串里**（例如从字符串生成场景源码），
> 那道门禁看不见它——这类写法本技能不鼓励，真出现时要靠人看。
> 反过来的边界也在：**注释里的确写错的代码**不会被拦（这正是我们要的，注释里的反例是文档，不是缺陷）。

> ⚠️ **这里容易出假阳性**：判对比度时**不能用静态交叉去猜"谁会压在谁上面"**。
> 第一版把 `white × paper` 全交叉算了一遍 → `white on paper = 1.00:1` 被报成 P0（白字**永远不会**压在白纸上）；
> 第二版改用 `background: C.x` 推断，结果 `background: C.paper`（卡片底色）又把 `white on paper` 请了回来。
> 结论：**配对必须是声明的契约**——正文 `ink on 表面`、深底反白 `white on ink`、彩色反白 `white on <强调色>`、
> 次要文字 `muted on 表面`、彩字 `<强调色> on 表面`，就这五类，写在脚本里。

#### G-14/G-15/G-16 讲法字段（P0/P1）——**判据见 `director.md#narrative-moves` §4**

本脚本还有第二组检查：`shots.json` 里的 `move` / `evidence` / `hold` / `misconception(+noMisconception+why)`
四类**讲法字段**是否写全、`move` 是否落在 10 个名字的闭集里、`hold` 是否 ≥ 标定线、误解二选一是否成立。
判据、取值与标定过程都在 [director.md#narrative-moves](director.md#narrative-moves) §2–§4，这里不重复。

> ⚠️ **这一条此前是名存实亡的（G-15 的 `evidence`，2026-09-22 补，当天又按实测二次简化）**：文档把判法写成
> "该名字必须出现在本镜场景源码里，且它所在的 JSX 块内有帧驱动的量；**静态元素不算证据**"，而代码里读
> `evidence` 的唯一一处是 `if not ev:`（**只查字段非空**）—— 名字写成不存在的、或指向一个不动的卡片，
> 门禁都不会响。这与 `CardFitGate` / `OverlapGate` / `bottomFill` 是同一类病（文档里有、代码里没有）。
>
> **现在的口径（比旧实现更窄，但不留做不到的承诺）**：只查**一件事** ——
> `evidence` 的名字必须**作为 JSX 用法**（`<名字 …>` / `<名字/>`）出现在该工程的**场景源码**里
> （扫前用 `noncode()` 抹掉注释与字符串，所以**只在注释/import/字符串里出现的名字会被报出来**，P0）。
> 判据、算法与"怎么判的"三段都在 [director.md#narrative-moves](director.md#narrative-moves) §2，这里不重复。
>
> **不做哪半边（写清代价，别高估它）**：
> · **不做本镜作用域**：名字在本镜没用到、但在**别的镜**用了，会**漏**（夹具 AG 现在就是这个语义：必须放行）。
> · **不做"是不是静态"**：不解析 JSX 结构、不看帧驱动 —— 指向一个在本镜里不动的静态卡片**不会响**。
>   砍掉它的理由：那一半只能做白名单判定，而误报面实测到了（帧经 `ctx` 传进组件的 `PhaseRail` 会被判成静态，
>   而它恰是动作表推荐的首选件 —— 判成 P0 就是"照文档写、门禁拦你"）。
> · **不做降级**：旧实现在"切不出本镜"时要降级并自报 P1 —— 现在没有"本镜"这一层，无级可降。
>
> **为什么敢砍**（实测）：旧实现是 465 行（手写 JSX 遍历 + 本镜切片 + 帧驱动白名单 + 降级分支），
> 它在接触表上抓到的真缺陷与本版**是同一批**。取舍与本技能其它判据一致：**宁可少报，不要假报告**。
> **真实工程 overview-film 的 S2 就是这条判据抓到的真缺陷**（`MetricGrid` 已被换成手绘行 + `Chart`，
> 只在注释里留名）—— 这一条**新口径仍然抓得住**（夹具 AJ 钉的就是它）。

> ⚠️ **编号（2026-09-21 修撞号）**：这一组**不是 G-6**。G-6 在调研报告里是"**对比层结构闭合**"（需要 `compare` 字段），
> 至今**未实现**（见本文第四节）。本组用 `director.md#narrative-moves` §4 的编号：G-14 `move` 闭合 / G-15 `evidence` 真的会动 /
> G-16 误解与留白；G-17（`known → new` 闭合）尚未实现。
> 判断依据：**编号属于调研报告的清单，新门禁只能往后排**——两边都叫 G-6 会让"哪道门在报"变成猜谜。

#### G-5 节拍拥挤（P1，**代理指标**）

同一镜内 **≥3 个 beat 落在 12 帧窗口** → P1（好几件事挤在一拍上，观众分不清该看哪）。

> ⚠️ 报告原文的 G-5 是"每帧**新开始的入场动画数**直方图"，那需要元素级的 `enters` 声明，**现有数据里没有**。
> 这里只做数据支持得了的代理形式，差距写在 Known gaps 里。

### 二、这道门禁自带负向夹具（`scripts/negative-gate-check.py` 的 I–M · R · S · X · Y · AC–AE · AF–AK）

**每条判据都有"喂坏输入必须拦住"的证据 + 阴性对照**（技能铁律：名存实亡的门禁是最危险的缺陷——
本轮刚抓到 `CardFitGate` 从装上那天起就没拦过一次）。
下表输出是**实跑抄录**；`must_block:<子串>` 断言保证"因别的原因失败"不算通过。

| 夹具 | 喂了什么坏输入 | 门禁实际报的 |
|---|---|---|
| I | 把 S1 的第二拍改成 `{cue:1, offset:-13}`（提前剧透） | `P0 S1: beat(cue1) offset=-13 早于该句 13 帧（上限 12）` |
| **S** | 把 S1 的第一拍推到 `offset=200`（该句 31 帧，讲到 6.7 s 后才出现） | `P0 S1: beat(cue0) offset=200 晚于该句结束 169 帧（上限 8 帧容差；该句 31 帧）` |
| **R** | 把 S7/cue13 的第二拍推到 `offset=112`（该句 106 帧 → 距上界只剩 2 帧，**仍在容差内**） | **rc=0**（放行）+ `P1 S7: beat(cue13) 距容差上界只剩 2 帧…合法但**贴边**` |
| J | 让 S2 的 beat 引用 S7 的 cue | `P0 S2: beat(cue13+0) 落在 803 帧，超出本镜 [213,286]` |
| K | 把 cue1 写成 36 加权字 / 0.9s | `P0 cue1: 阅读速度 40.0 字/秒 > 9.0` |
| L | 写一个 `fontSize: 9` 的场景文件 | `P0 src: src\tooSmall.tsx:1 fontSize:9 低于绝对地板 13` |
| M | 把主题的 `ink` 改成近乎白色（压白底） | `P0 theme:flat: 正文色 ink on paper = 1.12:1 < 4.5` |
| **X** | 删掉 S3 的 `move`（讲法字段 G-14） | `P0 S3: 缺 move（叙事动作）：讲法规范要求每镜声明它在这一章里干哪件事` |
| **Y** | 把 `flat` 的 `blueInk` 改成 `#eeeeee`（文字安全色） | `P0 theme:flat: 文字安全色没过 4.5:1（它们是**专门**用来当文字色的）：blueInk 1.07:1(on paperWarm)` |
| **AC** | 把 S1–S3 三镜的 `move` 都写成同一个 `引入`（同一 `move` 连续 3 镜，G-14②） | `P0 S1–S3: 同一 move 连续 3 镜：S1→S2→S3 都是 «引入»（上限 2 镜，判据 = 文档的「同一个 move 不得连续 ≥3 镜」…）` |
| **AD**（对照） | 同样的改法**只改 2 镜**（连续 2 镜，上限之内） | **rc=0**（放行）+ `结论：P0=0 P1=0 → PASS` —— 证明这条不是"见到重复就拦"，上限就是 2 镜 |
| **AE** | S1/S2 与 S4 都是 `引入`、中间 S3 的 `move` 删掉（夹一镜缺 move） | `P0 S3: 缺 move（叙事动作）：讲法规范要求每镜声明它在这一章里干哪件事` **且不报**「同一 move 连续」（`must_absent`：缺 move 打断计数，不许把两侧拼成 S1→S2→S4 的假"连续 3 镜"） |
| E（对照） | **原样分镜** | `validate-presentation` **通过**（证明门不是"见谁拦谁"） |
| **AF** | S1 的 `evidence` 改成一个**源码里不存在**的名字（夹具用的是 GhostWidget 这类假名） | `P0 S1: evidence=«GhostWidget» 在场景源码（scenes.tsx）里**找不到这个用法**…`（并断言**不许**走成"静态"那一侧） |
| **AG**（改写） | S1 的 `evidence` 改成 `StaggerList`（它**只在 S4** 出现） | **rc=0（放行）** —— 这条夹具的**语义变了**：它不再测"本镜作用域"（那一层已按实测砍掉），而是把"**已知漏检**"钉在明处：名字没在本镜用到、只在别的镜用了，判据看不见。谁哪天加回本镜作用域，它会先失败（那是有意的信号） |
| **AJ** | S1 的 `evidence` 改成 `exitAt`（模板里**只在注释中留名**的已删小助手） | `P0 S1: evidence=«exitAt» …**找不到这个用法**` —— 注释里的名字不算"用到"（`noncode()` 那一层） |
| **AK**（对照） | **原样 + 带模板 `src`** | `validate-presentation` **通过** —— 模板 8 镜的 `evidence` 个个合格（E 用例没有 src，走不到这条判据） |

> ⚠️ X 与 Y 是**本轮新增判据的夹具**（判据加了而夹具没加，这道门仍然只是名义存在）。
> Y 还兼作"新增机制的自检"：五个 `*Ink` 是专门用来当文字色的，喂一个过不了 4.5:1 的进去必须报 P0。

> ⚠️ AC–AE 是 **G-14②（同一 `move` 不得连续 ≥3 镜）判据、文档口径与夹具同版落地**的那一组
> （口径写回 [director.md#narrative-moves](director.md#narrative-moves) §2：**极大连续段 ≥3 镜即违规，最多连续 2 镜**，P0）。
> AD 是阴性对照；AE 专钉"缺 move 打断计数"这条口径 —— 判据第一版写成 `continue`（跳过但那一段不断开）时，
> 夹具当场抓出「S1→S2→S4 连续 3 镜」这句用户照着改不了的假话。

> ⚠️ AF–AK 是 **G-15（`evidence`）同版落地**的那一组，也是"这条判据此前**只查字段非空**"的直接证据：
> AF/AJ 钉 **P0 那一半**（不存在 / 只在注释里），AK 是阴性对照，AG 钉住"**不做本镜作用域**"这条口径的**代价**。
> **删掉的两条夹具**（AH/AI 帧驱动 vs 静态、AL 降级）对应的能力在二次简化里被砍掉了 ——
> 夹具不留，但代价逐条写进了 [director.md#narrative-moves](director.md#narrative-moves) §2 与本文的 G-15 段，
> **不留做不到的承诺**；`validate-presentation.py` 里那段注释同样列出了"不做什么、代价是什么"。

> ⚠️ 夹具 I 的第一版**根本没测到③**：它给 S2 的 `cue4` 加负 offset，而那个 cue 的帧号恰好等于 S2 镜起点，
> 任何负 offset 都先撞判据①"落在镜外"→ 永远走不到"提前剧透"。复核读完整输出才发现，现改用 S1 的 cue1。

### 三、已知的真实缺陷（P1 报出来、处置留给人）

跑一遍现有分镜，**P0 = 0**，但 P1 里有一条必须点名：

> **皮肤的强调色当文字色时对比度不足**（当时四套皮肤合计口径，其中两套已删除）：gold 1.35–2.94:1、green 1.78–3.04:1、orange 2.03–3.54:1、
> orangeDeep 2.49–2.83:1（大字档需 3.0、小字需 4.5）。彩色填充上的白字同样有问题。
> 这是**真实的可读性缺陷**（不是判据太严），但它属于**审美决定**：要么把这几支色值调深、要么约定
> "这些色只用于图形填充、当文字时改用 `ink`"。**没有替用户改主题的配色**，只把数字与用到处报出来。
>
> ✅ **2026-09-21 的处置（部分落地）**：约定已经落成机制 —— 每支强调色补一个 `*Ink` 文字安全色
> （同色相按 WCAG 反解压暗，见 `themes/system.md`），五个 Ink 现在都过 4.5:1；
> 又把**残留的三个"用填充色当文字"的色名**按同一办法清掉：`number/boolean` 的语法高亮从 `orangeDeep`
> 换成 `orangeInk`（原值继续留给章节序号渐变）。
> 于是 `flat: orangeDeep` 这条 P1 消失。
> **仍未处理的是另一半**：彩色填充上的白字（在现存 flat / cel 上需逐色复测）
> —— 那要么把填充色压深、要么给白字加描边，是纯审美取舍，**留给用户拍板**。

### 四、还没做的

- G-4 屏上文字总量预算、G-6 对比层结构闭合（需要 `compare` 字段）、G-8 空间接近、G-13 信号-旁白对齐
  （需要序数词/实体名闭集）——都在调研报告的批次 B/C 里。
- G-5 的原始形式（元素级 `enters` 直方图）需要新声明，见 Known gaps。
