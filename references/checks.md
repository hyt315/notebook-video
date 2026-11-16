# 检查：质量清单、美学系统、构图与呈现门禁

交付前的质量清单与美学系统，以及构图门禁、呈现门禁每类报错的含义和修法。门禁的实现口径、实测记录与历次修正经过在维护者手册（不随包发布）。

本篇各节：

- [Delivery acceptance checklist](#quality-checklist)
- [Official aesthetic system](#official-aesthetic-system)
- [构图门禁：把"审美"变成可执行检查](#composition-gate)
- [呈现效果门禁（`validate-presentation.py`）](#presentation-gate)

<a id="quality-checklist"></a>

## Delivery acceptance checklist

### Story

- The opening gives a concrete, verified payoff or tension within 1.5 seconds, before context; an honest open loop follows by 8 seconds, and the storyboard identifies a later evidence-based callback.
- Each scene has one main idea and one physical action; the visual story remains understandable without narration.
- A meaningful state changes every 2–4 seconds. The final message holds at least one second.

### Architecture

- React + TypeScript + Remotion is the primary renderer.
- TTS milliseconds convert once to integer frames; subtitle, animation and sound share the same FPS convention.
- Fonts and media resolve before the first rendered frame. Action audio is declared with its visible action.

### Visuals

- Background, chapter, header and subtitle match the canonical example.
- Every scene declares one primary **media kind** (`chart` / `console` / `code` / `graphic` / `text` / `metric`) — 默认路线的路由维度。`image-text` 只在场景用用户提供 / Commons / 授权图片时才出现（见 director.md#visual-director；技能不调用生图模型）。
- Images: concrete subjects use original, supplied or licensed imagery when seeing the subject materially improves comprehension. Imagery contains no baked labels, charts, logos or UI text; exact information remains in Remotion. Every raster is registered in `visual-assets.json` with source, prompt/description, crop policy and rights. Image scenes synchronize recognition, callout, relation and conclusion instead of placing a static image beside unrelated copy. Images receive only restrained crop reveal or push-in motion; annotations move independently.
- Objects: every independently moving object is an independent component with one home zone and one destination zone. Unrelated cards keep at least 70px separation, including airborne shadows. The central corridor contains at most one dominant temporary transfer object. A continuous process preserves one task object and changes its state at real stations. Floating objects stay above lower bases.
- Slots and exits: slot occlusion begins only after a visible crossing; inserted modules finish fully behind the front lip with no residual fragment; temporary components exit completely (no half corner remains).
- Shadows: dynamic shadow changes only when paper lifts; paper uses the engine's locked lift-linked contact/environment shadow recipe and no component invents a conflicting shadow.
- In the official engine: display, title, body, label and micro copy use the locked type scale; no system glyphs or emoji as production icons (locked line-icon language); the whole-film grade is static and restrained (no animated grain or moving light texture); ordinary production edits stay inside the [ordinary editable surface](#ordinary-editable-surface).
- Data dashes move only during a real transfer and in the correct direction. Text-bearing paper has visible padding on all sides.
- Exact Chinese text and real brand assets are preserved: no malformed labels, invented logos or softened Chinese glyphs.
- No large accidental empty area during a spoken explanation; no clutter from unrelated dots, scraps, steam or continuous movement; no effect stack, miniature card pile or unused half-visible layer; no global zoom, shake, animated noise, posterize or full-screen page turn.
- Shot camera: every shot declares one intent from the closed set (`establish` / `push-in` / `pull-back` / `pan-follow` / `reveal` / `micro-orbit` / `still`) plus an `anchor`; `scripts/validate-shot-motion.py` must prove the anchor stays fully visible at every keyframe (P0 = 0). Zoom ≤ 1.35 on shots carrying text. At least 3 camera moves per chapter (>=20s chapters; >=1 for shorter ones) and at least 3 distinct intents per film — a film with a frozen frame reads as page-turning.
- Scene skeletons: at least 3 of `Stage` / `Corridor` / `Split` / `Zoom`, and no two adjacent scenes share a skeleton (`scripts/validate-composition.py`).
- Visual media: at least 3 distinct media across the film, and every explanation scene carries at least one live component that changes state with the narration. A pure card-and-bullets scene is rejected.
- Density: every scene declares 3–5 functional zones and fills the lower quarter (bottom edge near y=876). An empty lower half is a PPT tell.
- Background readability: content that overlaps a locked background decoration zone (`theme.backgroundDecorZones`) must sit on a `CoverPanel`; the background bitmap itself stays untouched.
- Runtime overlap gate: after the first render, the console must show **no `OverlapGate` warnings** (text-vs-text overlap and paint-order occlusion, sampled every 15 frames). Intentional overlaps (shot handoff, header swap, metric value replacement) must be marked `data-gate-allow`; never use the allow-list to hide two different pieces of information colliding.
- Main-slot fill gate (render path): **no `SlotGuard` warnings** — the main slot of `StageFrame` hands over the whole remaining height (`h − pad×2 − header − stamp`), so the content must fill it (target ≥60%; the guard reports the occupancy every rendered frame and speaks up below 35%; a one-line content in a full-height slot measured 11%). Width is still yours to budget: `mainW = w − pad×2 − railW − 18`.
- Motion: progress-like bars animate `scaleX` (never `width`); numeric readouts use `tabular-nums` with fixed fraction digits; every element's multi-property entrance uses different clocks (see draftpaper.md#motion-design).
- Anti-PPT Functional Components: 技术概念（检索 / 记忆 / 上下文 / 契约 / 嵌入 / 安全）**不要**用一整排等大的要点卡去讲，要用**真的随旁白变化**的构件，从真实存在的里面挑：`ConsoleWindow` / `MetricGrid`（`media.tsx`）、`Funnel` / `ProgressRing` / `ChatThread`（`fxkit.tsx`）、`Chart` / `TreeView` / `NetworkGraph` / `ControlStack`（`src/components/`）。**不要把不可达（零 export、零 JSX 用法）的名字写成硬要求。**

### Subtitle

- Bottom-pinned pure caption text is present in every scene: one centered line, WenKai Lite 44px; no bar, torn contour, dark border, black side mark, inner line, orange locator or blue ring.
- `CaptionFitGate` measures every fully revealed cue with the loaded WenKai font in the real render browser; every cue fits within the canvas safe width.
- Partial reveal does not shift horizontally (hidden full-width placeholder).
- Internal punctuation remains; trailing punctuation (`，。！？；、,.!?;:`) is strictly stripped and hidden visually via `cleanFull` and gated character length. Trailing punctuation mark on screen is an immediate rejection flag.
- Caption segmentation is explicitly `semantic`, never `draft-character-count`.
- Every model/product name, benchmark, number-plus-unit expression and fixed technical term is listed in the protected-phrase manifest; no protected phrase crosses a cue boundary; no ASCII identifier is split between cues.
- Cue words flatten to the exact TTS word stream; caption timing leads measured speech by no more than about 80ms.

### Audio

- Correct voice and complete narration; no hidden voice delay.
- Effects land on visible actions; speech remains dominant.
- Integrated loudness is about -16 LUFS; true peak is no higher than -1.5dBTP.

### File validation

- H.264 video and AAC audio; audio 48kHz stereo.
- 2560×1440 at native 30fps unless the user explicitly requested a genuinely native high-frame-rate production.
- Video duration includes at least 0.7 seconds after narration; no black frames or truncated ending; no unintended scaling or softening pass.
- Contact sheet includes every scene. Films over 60 seconds include at least 24 evenly spaced frames plus dense motion sheets for the two most complex movements.
- Opening, scene boundaries, longest caption, hover/insert midpoints and closing frame are inspected manually. Opening range 0–360 is inspected at 0.5s, 2s, 4s, 8s and 10s; the primary claim is visible by 1.5s and the deferred question is paid off later.

Do not update the skill from a design proposal. Update only after the user approves the actual rendered film.

### Deliverables

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

The aesthetic layer preserved by the flat / cel track (see `locked-style-contract.json`): one official aesthetic track, one canonical project template (`assets/lecture-template`) and two locked skins, `flat` (default) and `cel`. (The old warm-ivory paper look and its `--classic` example were removed in 3.2.0.)

### Locked production grammar

The system preserves the per-shot restricted camera, subtitle geometry, native 30fps card motion, declarative audio tree, asset gate and final draw order while allowing the scene grammar to follow meaning. Before storyboarding, select one primary **media kind** for each scene (`chart` / `console` / `code` / `graphic` / `text` / `metric` — 默认路线的路由维度，见 media.md#media-routing); `image-text` only applies when a scene uses a user-supplied / Commons / licensed image; read `director.md#visual-director`.

Real images are an optional input layer: the skill does not call image models, so images come from the user, Commons / Openverse or other licensed sources, used for concrete subjects where they improve comprehension. Keep exact text, arrows, diagrams and timing in Remotion. A project must remain buildable with native SVG alone.

### Locked aesthetic core

Part of the official engine, not ordinary content-editing surfaces:

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
6. supplied raster assets in `public/illustrations/`;
7. topic-specific scene objects that preserve the same physical ownership and motion grammar;
8. **the wrapped component layer in `src/components/`** — reach for a ready-made wrapped component, parameterised per scene, before hand-writing SVG. The dependency boundary and component rules live in [technique.md#dependency-policy](technique.md#dependency-policy); the template's `package.json` already declares those libraries, so no separate authorisation is needed to use them.

Stable semantic IDs must remain separate from display labels. Changing visible copy must not break scene branching, icon choice, z-order, transfer paths or slot occlusion.

### Visual rules

- Preserve spacious composition and one hero action per zone; scene count follows the content.
- Choose image-plus-text, pure text or pure graphic mode from meaning rather than repeating one scene family.
- Treat bitmaps as animated assets, never as the finished scene; keep exact labels and diagrams outside the bitmap as live Remotion layers; record source, prompt summary, crop policy and rights for every raster asset.
- Keep the bottom-pinned pure caption text at one centered line (no torn bar); use browser-native caption measurement after the exact font is loaded.
- Use the official palette and type scale; do not invent per-scene styling.
- Use lift-linked paper shadows only for moving paper; keep the grade static and restrained.
- Never lay a full-frame translucent wash over the background: the three backgrounds per theme keep their central ~70% calm on purpose, and a wash turns the corner characters into ghosts.
- Icons: `LineIcon` (glyphs from `lucide-react`) is the primary icon language, not system glyphs or emoji. Topic-specific marks use `TopicIcon`: `simple-icons` for brands (single-colour paths, theme colour only) and `lucide-react` for line marks, with `strokeWidth` matched to `LineIcon`'s visual weight. See technique.md#dependency-policy §7.5.
- Preserve the same persistent task-card, shared-track and physical-slot logic.

### Locked official elements

Keep these locked until the user approves a future rendered replacement. For any aesthetic change: work in a disposable project copy, render the complete film, obtain user approval, and only then overwrite the template, the theme files and the contract. Do not write an experimental change into this skill until the user sees the rendered film and explicitly approves it.

- React + TypeScript + Remotion rendering core;
- locked premium motion contracts shipped in the template: `JumpInText` per-glyph 3D flip titles, `ShimmerText` sweep on CTA strings, multi-keyframe figure roll-ins, per-word subtitle reveal, and the shot layer (see [camera.md#shot-language](camera.md#shot-language));
- fixed native 30fps motion on the single locked canvas 2560×1440 (16:9); no duplicate-frame upconversion; 60fps only when motion is authored natively at 60fps;
- mount only the active scene, with at most two scenes during a short handoff;
- animate moving objects with transforms instead of per-frame layout properties (**progress bars animate `scaleX`, never `width`**);
- the active skin's three locked background rasters (`main` / `chapter` / `quiet`, `flat` default or `cel`), chosen per shot by the backdrop rule;
- stable top-left chapter card and top-right technical header, both **outside** the shot camera;
- bottom-pinned pure caption text with per-word reveal and soft text shadow; no decorative bar, dark border, side marks, locator or ring;
- LXGW WenKai Lite as the unified CJK typeface plus Clash Display / Space Grotesk Latin accents, with WenKai registered as the CJK fallback face of every Latin display family (`src/fonts.tsx`) so no text ever falls back to a system font;
- TTS word timing converted once to integer absolute frames;
- independent semantic parts with explicit z-order, entry and complete exit;
- a spatial density budget: one hero action per zone, no temporary stack in the center;
- a shot layer: one camera intent per shot from the closed set plus an `anchor` that `validate-shot-motion.py` must prove stays visible (restricted recipes, not free curves — and not frozen framing);
- four scene skeletons (`Stage` / `Corridor` / `Split` / `Zoom`), **no two adjacent scenes sharing one**, at least three per film;
- content→medium routing: at least three distinct visual media per film, at least one live state-changing component per explanation scene (**a pure card-and-bullets scene is a gate failure**);
- a shot table that references narration cues instead of hard-coded frame numbers ([scenes.md#scene-skeletons](scenes.md#scene-skeletons));
- background readability via `CoverPanel`: locked background bitmaps stay as they are; content overlapping a declared decoration zone sits on a feathered backing plate ([media.md#media-routing](media.md#media-routing));
- shared-track continuity when one object changes state across several stations;
- real slot geometry: insertable parts cross the slot, move behind the front lip and disappear fully;
- declarative narration and action effects inside the Remotion component tree;
- font/audio/image asset preload gate before the first frame;
- a visual plan selecting pure text/graphic scenes by default, with image-plus-text only after the user accepts the add-on;
- optional imagery as preloaded Remotion assets with prompt, crop and rights records;
- H.264/AAC output, automated QA, contact sheets and editable source package.

<a id="composition-gate"></a>

## 构图门禁：把"审美"变成可执行检查

脚本：`scripts/validate-composition.py`、`scripts/validate-shot-motion.py`。

### 1. 为什么必须有这一层

没有「会因为像 PPT 而拒绝渲染」的门禁，条款再多也会随时间退化。所以这里的规则**少而硬**：条款可以少，但写下的每一条都必须真的被检查。

### 2. 十一项检查

P0 七项（P0-1…P0-7）+ P1 四项（P1-7…P1-10）。

#### P0（阻断渲染）

| # | 检查 | 判据 |
|---|---|---|
| **P0-1** | 骨架重复度 | 相邻场景不得同骨架；全片 ≥3 种骨架（`Stage`/`Corridor`/`Split`/`Zoom`） |
| **P0-2** | 活性组件覆盖率 | 每个讲解场景（`explanation != false`）必须声明 ≥1 个活性组件；**纯卡片堆 → fail** |
| **P0-3** | 镜头意图多样性 | 全片 ≥3 种 intent（不含 `still`）；每章 ≥3 次运镜（**章节 <20s 时 ≥1 次**；后者在 `validate-shot-motion` 查） |
| **P0-4** | 密度硬条款 | 每镜 `zones` ∈ [3,5]（手作皮肤 journal / papercut / archive 为 [1,5]：一镜一个主体是手作片的常态，硬凑 3 区会逼出满屏卡片；皮肤以 `src/theme/active.ts` 为准）；**`bottomFill` 字段必须在**（缺字段=配置错误），只查存在性，填没填满由渲染期 `FillGate` 实测（见下方降级说明） |
| **P0-5** | 介质多样性 | 全片 ≥3 种不同视觉介质 |
| **P0-6** | 镜头出界证明 | 逐镜、逐关键帧证明 `anchor` 完整落在可见窗内（见 `camera.md#shot-language` §3） |
| **P0-7** | beats 下标越界 | 逐镜扫场景源码里的 `b[k]` 与 `SHOTS.Sx.beats[k]`（**两种写法都扫**），k 必须 < 该镜真实拍数。越界取到 `undefined`：传进 `interpolate` 会**整帧渲染失败**，传进比较则**那件东西永远不出现**（都不报错） |

#### P1（只警告，成片前人工确认）

| # | 检查 | 判据 |
|---|---|---|
| **P1-7** | 转场多样性 | ≥2 种（`cut` / `handoff` / `reveal`） |
| **P1-8** | 入场方式多样性 | ≥3 种（`rise` / `slide` / `fade` / `zoom`） |
| **P1-9** | 状态变化间隔 | 任意 120 帧（4s）内至少一次画面变化；静止 >45 帧提示补呼吸 |
| **P1-10** | 背景装饰可读性 | `contentBand` 与主题装饰区相交时须声明 `cover` |

> **P0-4 降级说明**：「画面下半空洞」是 PPT 感的主要来源之一，所以底部填充是 P0。但 `bottomFill` 是生成分镜表的脚本自己写的常量，
> 门禁查 `== true` 结构上不可能报错。所以声明位**只查字段在不在**；真实判据在**渲染期 `FillGate`**：
> 量画面（信息元素的最低边 vs y=876），不是量声明。原则：**声明能查的只有「写没写」，「做没做到」必须实测。**

#### 横向空洞（实测，只报不拦）

`FillGate` 除纵向外还量横向，**含手作皮肤**。拿同一批实测盒子落到 8×6 网格，每镜报四个数：
`cells`（48 格占用）/ `blank`（整列没有任何元素的列数）/ `largest`（最大单体面积 ÷ 画面面积）/ `widest`（最大单体横向跨度 ÷ 画宽）。

- **只报不拦**：它量的是版面审美，不是画错。
- 落盘 `<工程>/renders/fill-coverage.json`，**合并**写入、每条带 `at`（量的时间）：只量一镜不会抹掉其它镜，看 `at` 分新旧。
- **只有整片 `render` 和 `sweep` 落盘**；`preview` / `render-range` / `review-frames` 是窗口渲染，量到的是「窗口内最完整帧」，只打印不落盘。
- `sweep` 每镜取一帧量一遍，少一镜会明写「未量到」。

| 项 | 规则 | 为什么 |
|---|---|---|
| 取哪一帧 | 该镜**最完整的一帧**（格子数最多，平手时取 `largest` 更大者） | 量终点构图，不是入场过程（取第一帧会把入场展开误判成空洞） |
| 条状主体 | `widest ≥ 0.45` 画宽即视为不空，不看面积 | 一条横贯画面的格带面积天然小 |
| 组合装置 | `blank = 0` **且** `cells ≥ 24/48` 时视为不空，不看面积 | 多个中等元素拼成一个主体时 `largest` 按单个元素量天生很小 |
| 阈值 | `largest < 0.06`（且不属上面两种豁免）→ 主体过小；`blank ≥ 3/8` → 横向空洞 | 先量后定，取自实测基线 |

**镜头开头空着是正常的**（量的是最完整那一帧）：不要为了开头好看把东西提前摆上，出现规则见 [draftpaper.md#reveal-rules](draftpaper.md#reveal-rules)。

**空洞处补一层「属于主体」的东西**，不是补一句话。已验证的四个装置（例子在 `cell/src/scenes.tsx`）：

| 装置 | 什么时候用 | 例 |
|---|---|---|
| 尺寸线 + 两端刻度 + 数值 | 主体是一个有尺寸的实物，观众需要知道它多大 | S6（`dim-v`/`dim-t`/`dim-b`） |
| 局部放大 + 引线 | 主体由很多小单元组成，需要说明"其中一个是什么" | S5（右下 230×180 盒 + `s5-lead`） |
| 标尺 | 需要「量」这个动作本身，而不只是结果 | S5（`ruler` + 两端 `tick`） |
| 引线批注指回主体 | 有一个术语/数字要落到画面某处 | S4（`cells-lead` 从词拉到镜片） |

判据：**把这一层拿掉，主体还是不是完整的？** 是 → 那层是装饰（删）；不是 → 它是内容。

不该做：加「功能分区」凑覆盖率（逼作者往空白里塞清单）；放大卡片凑面积（`largest` 变大了，观众还是不知道看哪儿）；给空白处单独加一行字（把空场翻译成文字，没解决空）。

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
| P0-4 下 1/4 空洞 | 补一个真实信息元素（指标条 / 结论条 / 清单），**不是**放大现有卡片凑面积。判据在渲染期 `FillGate`：改完重渲那一镜的抽帧看 `[FillGate]` 出水，构建期只告诉你"字段写没写"。手作皮肤（journal / papercut / archive）不判纵向（大留白是设计）；flat / cel 的警告按镜头去重，渲染结束汇总成一行 `FillGate: N shots (S2,S5,…) bottom-quarter underfilled`。 |
| P0-5 介质单一 | 至少换一段内容用另一种介质（图表 / 控制台 / 大字 / 补丁）。 |
| P0-6 出界 | 收窄运镜幅度或把 `anchor` 改成真正的解说对象外框；**不要**把 anchor 改小来绕过检查。 |
| P1-9 长时间无变化 | 在最长间隔中点加一次状态变化（元素入场 / 数值变化 / 主体相位切换）。 |

> **不要把门禁改松来通过。** 某条判据在真实题材上系统性误报，说明判据要改，但要经过「出片验证 + 用户确认」，不是当场调阈值。

**修复顺序**：先修**组件级**（一次修好全部场景），再修**场景级坐标**。组件级根因的典型形态：缩放矩阵写错（`ZoomStage` 用三段式 `translate(框心) scale(k) translate(-焦点)`，并传 `contentW/contentH` 让缩放自动钳制）；相邻标签没有垂直预算（`Corridor` 状态标签放承载物**上方** 46px、站点标签下移 96px）；固定像素宽度撞上随 `railW` 变化的动态列宽；承载物盖住站点圆环与对勾（缩小承载物 / 把到站反馈画在环外侧）。

### 5. 与运行时门禁的分工

| 门禁 | 时机 | 抓什么 |
|---|---|---|
| `validate-shot-motion.py` / `validate-composition.py` | **构建期**（不渲染） | 构图 / 骨架 / 介质 / 镜头配方与出界 |
| `CardFitGate` | **渲染期**（浏览器内） | 文字溢出卡片 |
| `SlotGuard` | **渲染期**（出图路径，`StageFrame` 内） | main 槽的**占用率**（槽内有内容的最内层元素并集高度 ÷ 槽高，<35% 出声）：槽给足了、内容没填满；槽宽仍按 `mainW = w − pad×2 − railW − 18` 自己先算 |
| `OverlapGate` | **渲染期**（每 15 帧抽样） | **文字两两重叠 + 文字被遮挡**（有意覆盖用 `data-gate-allow` 白名单） |
| `CanvasBoundsGate` | **渲染期**（每帧） | **含文字的叶元素**（HTML 叶 + SVG `text`/`tspan`）的墨迹越出视口（= composition 尺寸，输出像素口径）。补的是其它门禁都不管的一类：`ClippingGate` 只认 SVG 图元、`CardFitGate` 只管卡片内溢出、`OverlapGate` 管互相压、`FillGate` 管铺到多低、构建期 `coords-lint.py` 排除布局件。见 §5.2 |
| `CaptionFitGate` | **渲染期** | 字幕超宽（按当前画幅与主题真实字重/字距测量） |
| `validate-caption-sync.py` / `validate-semantic-breaks.py` | 构建期 | 字幕与 TTS 词边界一致、保护短语不被切开 |
| `validate-presentation.py` | 构建期 | **呈现效果**：beat↔cue 时间接近、字幕阅读预算、字号地板与对比度——见 [checks.md#presentation-gate](checks.md#presentation-gate) |
| `notebook-video validate-video` | 交付前 | 时长、音视频编码、**色彩契约**（§6.1）、响度、黑帧 |

**分工原则**：能用算术在构建期证明的，不要留到渲染期；只有需要真实字体/布局测量的，才放在浏览器内。

#### 5.2 渲染期门禁 `CanvasBoundsGate`（画布越界）

**判据**：含文字的叶元素（HTML 叶 + SVG `text` / `tspan`）的**墨迹矩形**（文字用 `Range` 取并集，不用块宽），扣掉会裁切的祖先后，
仍越出视口 ≥ **6 像素** → 出声；**落定态**（有效不透明度 ≥ 0.98）**且**越界 ≥ **20 像素** → 硬拦（`cancelRender`，rc≠0 且不产出任何图；与 `ClippingGate` 同口径）。

- 「会裁切的祖先」= 取景框（`ZoomStage` 视口、接触表里 scale 过的格子），被它裁住的不算越界；铺满整个视口的祖先不算裁切。
- 阈值单位是**输出像素**（2560×1440 上 20px ≈ 15 设计像素），不做设计坐标回折；换 `--scale` 时判据跟着输出走。
- 入场途中元素在画布外飞是运动，只出声不拦。
- **相机不计入**：被运镜放大推到画布外的文字**会**出声（误报面存在），这是片子挂 `warn` 的原因之一（§6）。
- **不查**：一个字都没有的装饰块越出画布（`ClippingGate` 也不管，已知空白）；图形与版面件（与 `ClippingGate` 不重复报，同一处只报一次；SVG 文字既被 `<svg>` 视口裁又越出画布时两道各报一次，报的是两件事）。
- 每帧都量；整片渲染的耗时影响未实测，片子渲染变慢时这里是第一嫌疑。

**档位**：`mode="block"`（接触表）落定态 ≥20px 硬拦；`mode="warn"`（片子）只出声。覆盖率日志每 150 帧一次
`[CanvasBoundsGate] @帧 扫过 N 个文字叶，无越界`（探针开 `debug` 则每帧），让「没报」与「没跑」可区分——**扫过 0 个要当异常查**。

**怎么修**（别调阈值）：

1. 看日志里的文字与越界量（形如 `按 Flash 结算 越出右缘 26px`），直接定位组件。
2. **容器给窄一点 / 内容收回来**：例如 `Corridor` 端点标签块是 `pts[i] ± 150`，`x/w` 给太满就伸出画布，改成两端对称留白（`x={130} w={1580}`，口径见 `skeletons.tsx` 注释）。
3. 内容确实要出画布（有意出血/取景）：在组件上标 `data-gate-allow="<理由>"`，**不要**把阈值调大。
4. 接触表这类**目录 composition**：格子摆不下就换页或换格子表（一页 5 件用 `showcase.tsx` 的 `Grid5`，3 列 × 2 行），别让第 N 件落在画布外。

**负向夹具**：`scripts/negative-gate-check.py` 的 **AB0–AB4**（静态：接线、档位、硬拦纪律、判据收窄）。真渲染的夹具工程建在演示 / 交付工程**之外**（复用现成 `node_modules`，用完可删）；**别把渲染夹具塞进交付工程**。

### 6. 交付门槛

- `validate-composition.py` **P0 = 0**；`validate-shot-motion.py` **P0 = 0**；
- P1 项逐条人工确认（每条都要有结论，不能"没看"）；
- `CardFitGate` / `CaptionFitGate` 在整片渲染中没有触发 `cancelRender`；
- **`CanvasBoundsGate` 在片子（`NotebookVideoFilm`）上是 `warn`**：渲染日志里有 `[CanvasBoundsGate]` 出水就逐条人工确认（文字可能被画布切掉的嫌疑，不是自动放行）。不在片子上硬拦：判据的实测来源是接触表，硬拦发生在交付渲染最后一刻，误报代价是整片不出。等它在片子上抓到第一处真缺陷再谈升回 block；这条口径由 **AB3** 夹具守着；
- 接触表（`NotebookVideoShowcase`）的 `CanvasBoundsGate` 保持 **block**：件整件看不见 = 目录页缺件，属于画错了，不能退回 warn；
- **色彩契约**：`validate-video` 断言交付 mp4 的 `color_range / color_space / color_transfer / color_primaries` 精确等于 `tv / bt709 / bt709 / bt709`，任一项不符即 fail（打印实际值与修复提示），见 §6.1；
- 某条判据被人工判定为误报，**记录在案并说明理由**，不要静默放宽。

#### 6.1 色彩契约断言（`validate-video`）

生产端有两道（`--color-space=bt709` + 渲染后 `h264_metadata` 回写 SPS VUI，见 `technique.md#windows-compatibility`）；这一条是交付端的那道：谁把参数删了，片子照样渲得出来，但四项元数据会退化成 `pc / bt470bg / unknown / unknown`，严格播放器按 BT.601 + 满幅解释，饱和色偏移。

**判据**：四项精确等于 `tv / bt709 / bt709 / bt709`；缺字段一律按 `unknown` 报。**只认这一个组合**，不放宽成"看起来自洽"：

1. 交付都是 SDR 网络播放：`pc` 会被当有限幅解释而偏色，`bt470bg`（BT.601）与 `bt709` 矩阵不同同样偏色——放行等于把已修的缺陷放回来；
2. 自洽推不出合格：`pc + bt709×3` 字段自洽，但渲染端已按 `range=limited` 转换过像素（`technique.md#windows-compatibility` 第 1 条），放行等于把"标错范围"当合格；
3. 门禁职责是抓**漂移**，判据就该精确等于契约。

**只挂交付门**：Remotion 自己 stitch 出来的 raw mp4（未经 `h264_metadata` 回写）本来就不满足，所以不去卡渲染路径。

<a id="presentation-gate"></a>

## 呈现效果门禁（`validate-presentation.py`）

全技能现有 14 道门禁（构建期 6 + 渲染期 7 + 成片后验 1，表见 [scenes.md#handwritten-scenes](scenes.md#handwritten-scenes) 的 The gates），本道是构建期之一。
其它门禁查「画面里**有没有** / **够不够多** / **会不会撞**」；这一道查 **观众此刻该看哪里、读不读得过来、讲的和画的对不对得上**。
纯算术、不需要渲染、零新增数据模型。调研与依据见 `呈现效果调研.md`。

```bash
python scripts/validate-presentation.py PROJECT_DIR [--json]
# 或 CLI：
node scripts/notebook-video.mjs validate-presentation PROJECT_DIR
```

退出码：`0` = P0 为 0（通过）· `1` = 有 P0 · `2` = 用法/文件错误。

### 一、判据

#### G-1 时间接近（P0）——授权契约第 9 条「元素出现帧绑到讲到它的那一句」

| # | 断言 | 可计算形式 |
|---|---|---|
| ① | beat 落在本镜区间内 | `cueFrame(beat.cue) + beat.offset ∈ [shot.from, shot.to]`（**含 to 边界**：允许"切在下一句起点"的那一拍） |
| ② | beat 声明的 cue 属于本镜 | `cue ∈ [cueFirst, cueLast + 1]`（同上，允许 +1 的边界拍） |
| ③ | 不提前剧透 | `beat.offset ≥ −12 帧`（0.4s） |
| ③b | **不拖后**（不得晚于那句讲完） | `beat.offset ≤ 该句帧数 + 8`（`BEAT_LATE_FRAMES`）。超出 = "台词已经讲完，元素才出现" |
| ③b-P1 | 贴边预警 | 距上界只剩 ≤4 帧（`BEAT_TIGHT_FRAMES`）→ P1。**合法但脆**：配音或 cue 表一变就先从这里挤成 P0 |
| ④ | 每条 cue 至少有一拍 | 本镜 `cueFirst..cueLast` 全被 `beats` 覆盖；确实不需要的在 `shots.json` 里显式写 `silentCues: [i]`（**写出来才放行**） |

- **下界与上界缺一不可**；**8 帧容差是承重墙不是安全边际**：模板最紧的合法拍就是 `offset = 该句帧数`（"这句讲完时那拍出现"是设计约定），余量恰好 8 帧。
- **任何一次换配音 / 重算 cue 表，都必须重跑本门禁。** 修数据的方向永远是把拍挪回句内/句末，**不是把容差调大**。
- 判据是「beat 落在它声明的那句/那一镜的范围内、且不提前也不拖后」，**不是**调研报告原文的 `|beat − cueStart| ≤ 6 帧`：`beats` 本来就允许句内偏移（`{cue:13, offset:100}` = 同一句的第二拍），照抄会给正确数据报 P0。依据：temporal contiguity（PMC12691884）+ 视听线索同步实验（JEP 2019, DOI 10.1037/edu0000285）。

#### G-2 字幕阅读预算（P0）——Netflix 中文（简体）Timed Text Style Guide

| 判据 | 值 | 说明 |
|---|---|---|
| 阅读速度 | ≤ **9 加权字/秒** | 成人档（儿童 7）。**加权**：CJK 计 1、ASCII/数字计 0.5——不需要分词 |
| 单行宽度 | ≤ **16 加权字** | 同上 |
| 行数 | ≤ **2 行** | 同上 |

数据：`manifests/caption-cues.json` 的 `text / start_ms / speech_end_ms`（零新增数据）。

#### G-3 可读性底线（P0 地板 + P1 档位）

| 判据 | 档位 | 依凭 |
|---|---|---|
| 任何 `fontSize < 13` | **P0** | 13 = 技能自己的 `MIN_LABEL_FONT`（`contract.json`，`components/data.tsx` 导出），不是新魔数；从"图元标签"扩到全库 |
| `fontSize ∈ [13,16)` | P1（按文件聚合） | "标注 ≥16"档 |
| 正文色 `ink` / 反白 `white` on `ink` 对比度 < 4.5:1 | **P0** | WCAG 2.2 SC 1.4.3（大字号 3:1；**不四舍五入**，4.499 不通过） |
| `muted` on 表面 < 3.0 | **P0** | muted 是装饰性 kicker，按大字档判 |
| `muted` 3.0–4.5 | P1 | 同上，提示一档 |
| **`*Ink` 文字安全色**在任一纸面上 < 4.5:1 | **P0** | `blueInk/orangeInk/greenInk/goldInk/redInk` 专门用来当文字色（见 `themes/system.md`「文字安全色」）；这一条同时是这套机制的自检 |
| 被 `color:` 用过的**任意其它调色板键** on 纸面 < 4.5:1 | P1（按主题聚合） | 用原色（或 `orangeDeep` 这类填充 token）当文字色。**修法是换成对应的 Ink 变体，不是调松门禁** |
| 彩色填充上的白字 < 3.0 | P1（按主题聚合） | 见第三节 |

**强调色当文字色时**：① 这个词位本来就该是文字 → 换成对应的 `*Ink`；② token 同时还要当填充（如 `orangeDeep` 是章节序号渐变的深色端）→ **原值留给填充，文字位改 `orangeInk`**；③ token 只当文字用（如 `headerAccent` / `headerSub`）→ 就地压到过线（同色相按 WCAG 反解）。

**配对是声明的契约**，只有五类：正文 `ink on 表面`、深底反白 `white on ink`、彩色反白 `white on <强调色>`、次要文字 `muted on 表面`、彩字 `<强调色> on 表面`。不能用静态交叉或 `background:` 推断去猜"谁压在谁上面"（会把 `white on paper` 这种永远不会出现的组合报成 P0）。

**能力边界（别高估）**：只读 `theme/*.tsx` 里 `palette` 字面量、只认标准键名。拦得住"用标准键写错了色值"，拦不住"换个写法压低对比"：硬编码文字色（`style={{color:'#dcdcdc'}}`）完全不报；把正文色改名只报 P1；`linear-gradient()` / `conic-gradient()` 里的停靠色、SVG 的 `fill` / `stroke` 都读不到。量真实 DOM 的 computed color 属于渲染期 FocusGate（调研报告 §5.2，**未实现**）。

**扫描口径**：本门禁与 `import_integrity` 只扫"值位置"——扫描前把注释内部与字符串字面量内部抹成空格（长度与行号不变）。所以注释里的反例、模板字符串里的代码样例不算真代码；反过来，写在字符串里的可执行 import/字号（如从字符串生成场景源码）看不见，要靠人看（本技能不鼓励这种写法）。

#### G-14/G-15/G-16 讲法字段（P0/P1）——判据见 `director.md#narrative-moves` §4

`shots.json` 里 `move` / `evidence` / `hold` / `misconception(+noMisconception+why)` 是否写全、`move` 是否落在 10 个名字的闭集里、`hold` 是否 ≥ 标定线、误解二选一是否成立。判据、取值与标定在 [director.md#narrative-moves](director.md#narrative-moves) §2–§4，这里不重复。

**G-15 `evidence` 的口径**：只查一件事——名字必须**作为 JSX 用法**（`<名字 …>` / `<名字/>`）出现在该工程的**场景源码**里（扫前用 `noncode()` 抹掉注释与字符串，只在注释 / import / 字符串里出现的名字报 P0）。**不做**（写清代价）：

- **不做本镜作用域**：名字在本镜没用到、但在别的镜用了，会漏（夹具 AG 钉着这个语义）。
- **不做"是不是静态"**：指向一个本镜不动的静态卡片不会响（那一半只能做白名单，误报面实测存在：帧经 `ctx` 传进的 `PhaseRail` 会被判成静态）。
- **不做降级**：没有"本镜"这一层，无级可降。

原则：**宁可少报，不要假报告。**

**编号**：这一组不是 G-6。G-6 在调研报告里是"对比层结构闭合"（需要 `compare` 字段），未实现。本组用 `director.md#narrative-moves` §4 的编号：G-14 `move` 闭合 / G-15 `evidence` 真的会动 / G-16 误解与留白；G-17（`known → new` 闭合）未实现。**编号属于调研报告的清单，新门禁只能往后排。**

#### G-5 节拍拥挤（P1，代理指标）

同一镜内 **≥3 个 beat 落在 12 帧窗口** → P1（好几件事挤在一拍上，观众分不清该看哪）。报告原文的 G-5 是每帧新开始的入场动画数直方图，需要元素级 `enters` 声明，现有数据里没有，这里只做代理形式。

### 二、负向夹具（`scripts/negative-gate-check.py` 的 I–M · R · S · X · Y · AC–AE · AF–AK）

**每条判据都要有「喂坏输入必须拦住」的夹具 + 阴性对照**（名存实亡的门禁是最危险的缺陷）；判据加了而夹具没加，这道门仍然只是名义存在。`must_block:<子串>` 断言保证"因别的原因失败"不算通过。

| 夹具 | 喂了什么 | 期望 |
|---|---|---|
| I | S1 第二拍 `{cue:1, offset:-13}`（提前剧透） | P0 ③（用 S1：负 offset 若先撞①"落在镜外"就测不到③） |
| S | S1 第一拍 `offset=200`（讲完 6.7 s 后才出现） | P0 ③b |
| R | S7/cue13 第二拍推到距上界 2 帧（仍在容差内） | rc=0 + P1 贴边 |
| J | S2 的 beat 引用 S7 的 cue | P0 ①（落在本镜外） |
| K | cue1 写成 36 加权字 / 0.9s | P0 G-2 阅读速度 |
| L | 场景文件 `fontSize: 9` | P0 G-3 地板 |
| M | 主题 `ink` 改成近乎白色 | P0 正文色对比 |
| X | 删掉 S3 的 `move` | P0 缺 move（G-14） |
| Y | `flat` 的 `blueInk` 改成 `#eeeeee` | P0 文字安全色 |
| AC | S1–S3 的 `move` 都写 `引入` | P0 同一 move 连续 3 镜（G-14②：极大连续段 ≥3 即违规，最多连续 2 镜） |
| AD（对照） | 同样只改 2 镜 | rc=0 |
| AE | S1/S2 与 S4 都是 `引入`、S3 的 `move` 删掉 | P0 缺 move，且**不报**"连续"（缺 move 打断计数） |
| E（对照） | 原样分镜 | 通过 |
| AF | S1 `evidence` 改成源码里不存在的名字 | P0（且不走"静态"那一侧） |
| AG | S1 `evidence` 改成只在 S4 出现的 `StaggerList` | **rc=0**：钉住"不做本镜作用域"这条已知漏检；谁加回本镜作用域，它先失败 |
| AJ | S1 `evidence` 改成只在注释中留名的 `exitAt` | P0（注释里的名字不算用到） |
| AK（对照） | 原样 + 带模板 `src` | 通过 |

### 三、已知的真实缺陷（P1 报出来、处置留给人）

**彩色填充上的白字对比度不足**（flat / cel 上需逐色复测）：要么把填充色压深、要么给白字加描边，是纯审美取舍，**留给用户拍板**，不要替用户改主题配色。（强调色当文字色那一半已用 `*Ink` 文字安全色机制处理。）

### 四、还没做的

- G-4 屏上文字总量预算、G-6 对比层结构闭合（需要 `compare` 字段）、G-8 空间接近、G-13 信号-旁白对齐（需要序数词/实体名闭集）——都在调研报告的批次 B/C 里。
- G-5 的原始形式（元素级 `enters` 直方图）需要新声明。
- G-3 渲染期真实 DOM 对比度（FocusGate）。
