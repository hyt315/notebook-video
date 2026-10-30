---
name: notebook-video
version: 3.3.0
description: Turn a topic into a Chinese 16:9 teaching video (flat / cel component themes, or the journal / papercut / archive hand-made skins driven by a metaphor-first director layer) with React, TypeScript and Remotion. Every shot is a code-drawn component scene — consoles, diffs, checklists, stat rows, funnels, progress rings, kinetic numbers, stamp seals, verdict bars, or a real screenshot / screen recording in a MediaFrame — moved by an engine-level virtual camera that pushes in on whatever the narration names. Weak-model friendly: five teaching blueprints with per-shot component picks, golden examples, a five-step workflow and one cross-platform command (`node scripts/make-video.mjs <project>`, `make-video.cmd` on Windows) that resolves shots, runs hard gates with objective auto-fixes (no clipped titles, font floor, text contrast, ≤16-character captions at 4.5 chars/s, no dead tails, blurry-media check) and renders stills or the MP4. Tuned semantic sound effects land on the visual hit and duck the music bed. Every topic first searches Wikimedia Commons / Openverse for licence-filtered real media with automatic on-screen credits. No built-in TTS and no image-generation model. Use when the user asks to 做科普视频, 讲解视频, 概念讲解, 代码讲解, 数据对比视频, 流程讲解, 踩坑提醒, 产品讲解, 30 秒到数分钟的中文讲解短片, 或把一段文字讲解做成 MP4.
---

# notebook-video · 用组件场景讲清一件事

画面 = **组件场景**：每一镜都是真组件（控制台、代码差异、清单、数字行、漏斗、进度环、印章、结论条……），
由引擎虚拟摄影机推近 / 跟随 / 横摇。**常规镜头不要做满屏大字的「文字页」**——一句话也要放进卡片（`Callout` / `StampBanner`）里；
例外是每片 2–3 个**锤子帧**（整章最该被记住的一句，满屏单独出现 1.5–2.5 秒），规则见 [references/pacing-rhythm.md](references/pacing-rhythm.md)。
锤子帧怎么做：组件路线用 `StampBanner`（或 `Callout` 放大到 displayL）独占一镜；手作路线用 `HandLettering` 手写满屏一句，或 `Seal` 印章大字——都放在媒介里，不是白底大字。
只有 16:9；五个皮肤：`flat`（默认）、`cel`，以及 3.3.0 的手作皮肤 `journal`（手账水彩）/ `papercut`（红色剪纸）/ `archive`（档案灯台）。
没有 TTS：旁白是静音占位，字幕整行出现；组件路线按 4.5 字/秒定时，手作路线用 `silent-timing` 按 6.5 字/秒（`--cps N` 可改）。

## 先选路线

| 题目 | 路线 |
|---|---|
| 软件、产品、代码、操作教程 | **组件路线**：`flat` / `cel` + 下面第 1–5 步 |
| 科普、自然、历史、"为什么"类问题 | **手作路线**：先走第 0 步导演层，皮肤选 `journal` / `papercut` / `archive`，画面用 `src/craft/` 组件，再接第 2–4 步 |

**不论哪条路线，每个选题都先搜一次 Commons / Openverse**（真东西几乎总能让片子更好）：
`python scripts/commons-search.py search "<英文关键词>" --project ./my-video`，能用的 `add` 进来，交付前 `credits` 生成 `CREDITS.md`。
许可只收公有领域 / CC0 / CC BY，署名自动上屏。见 [references/commons-media.md](references/commons-media.md)。

## 第 0 步 · 导演层（手作路线必做）

照 [references/director-method.md](references/director-method.md) 写 `manifests/treatment.json`（模板 `manifests/treatment.example.json`）：
一个生活问题 → 只属于这个题的隐喻 → 媒介（皮肤）为什么是它 → 顿悟点的**原生动作** → 三个候选结构选一个 → 对标学 / 不学 → 镜头表每镜写理由。
蓝图用 `blueprints/medium-metaphor.json`。`validate-treatment.py` 在手作皮肤下把缺项记 P0（`make-video` 自动跑）。
媒介的八个轴与"不是什么"见 [references/style-recipes.md](references/style-recipes.md)；组件见 [references/craft-kit.md](references/craft-kit.md)
（`InkPath` / `HandNote` / `HandLettering` / `WashBlob` / `CutPaper` / `Loupe` / `PinnedPhoto` / `ArchivePhoto` …）。
开场钩子、节奏、运镜分别见 [references/narrative-hook.md](references/narrative-hook.md)、[references/pacing-rhythm.md](references/pacing-rhythm.md)、[references/camera-language.md](references/camera-language.md)。
**手作路线只必读 4 份**：[director-method.md](references/director-method.md)、[craft-kit.md](references/craft-kit.md)、[camera-language.md](references/camera-language.md)、`references/theme-<皮肤>.md`；其余按需查（`lecture-composition.md` 等仅限组件路线）。
先做 3 张风格帧（`--stills`），像了再做全片；**整片渲染前**由新会话只看联系表 + 自动生成的 `storyboard.md` + `treatment.json` 做七项独立评审，写进 `review.rounds`（手作皮肤没评审时 `make-video --render` 会停下，草稿用 `--skip-review` 显式跳过）。

## 第 1 步 · 选一个蓝图

| 你要讲的 | 蓝图 | 路线 |
|---|---|---|
| 一个词 / 一个原理 | `blueprints/concept.json` | 组件 |
| 一次代码改动 | `blueprints/code-change.json` | 组件 |
| 几组数字说明一个结论 | `blueprints/data-compare.json` | 组件 |
| 一件事分几步发生 | `blueprints/process.json` | 组件 |
| 一个常见错误 | `blueprints/pitfall.json` | 组件 |
| "为什么"类科普：一个错误直觉被一个原生动作推翻 | `blueprints/medium-metaphor.json` | 手作（默认） |
| 一个现象的来历，适合"起—承—转—合"慢慢翻出意外 | `blueprints/kishotenketsu.json` | 手作 |
| 一个有悬念的"谁 / 为什么"，线索逐条揭开 | `blueprints/mystery.json` | 手作 |
| 大小 / 多少超出直觉，要一级一级比出来（尺度、数量） | `blueprints/scale-ladder.json` | 手作 |
| 能用一次对照实验说清的因果（变一个量，看结果） | `blueprints/experiment.json` | 手作 |

组件路线的蓝图每一镜都写了 `$components`：该用的**骨架**（Stage / Split / Zoom / Corridor）和**组件**。照它选，别自己发明版式。
手作路线的蓝图写的是结构和节拍；三个候选结构至少来自 2 个结构族（见 [references/director-method.md](references/director-method.md) 第 5 步）。

## 第 2 步 · 建工程，照抄示例片的结构

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project ./my-video --style=flat
```

手作路线换成 `--style=journal`（或 `papercut` / `archive`），会按需下载 Noto Serif SC Bold（字幕字体，OFL）。
手作皮肤的镜间转场缺省是**真翻页**（journal / archive `pageturn`、papercut `peel`，WebGPU）：渲染器先画一张探针验收，机器画不了就自动退回 `slide` / `drop` 并在报告里记 P1，不会渲染失败（[references/fx-effects.md](references/fx-effects.md)）。

工程里已有一部完整的示例片（8 镜）。**照着改，不要从零写**：
- `manifests/shots.json`：每镜一行（`skeleton` / `live` 组件 / `cameraIntent` / `beats` / `transition`）——镜头表是唯一真相；
- `src/scenes.tsx`：每镜一个 React 组件，用 `live` 里列的组件画出来，动画只用帧号 `f`；
- `src/film.ts`：片名、章节标题；
- `manifests/caption-cues.json` + `audio/narration.mp3.json`：字幕（每行 ≤16 字）。

组件怎么选：[references/media-routing.md](references/media-routing.md)（修辞动作 → 组件表）、[references/fxkit.md](references/fxkit.md)。
完整作者手册（骨架、镜头语言、门禁细节）：[references/handwritten-scenes.md](references/handwritten-scenes.md)。

## 第 3 步 · 写台词与镜头表

- 一镜 1–3 句，一句一个意思；字幕超 16 字由 `build-semantic-captions.py` 在合法断点自动拆（不拆词、英文、数字）。
- 要观众「看那里」时，在镜头表写 `cinema.focus`（推近到那个组件的矩形）；不写也有缺省缓推。
- 相邻两镜换骨架；一镜一个概念；关键数字用 `KineticNumber` 数过去。
- 背景（3.3.0 / 3.3.0）：手作皮肤默认 `bgMode: "chapter"`（每章一张纸、章内沿用），flat / cel 默认 `"shot"`（逐镜轮换）；全片一张纸写 `"bgMode": "film"`，完全不轮换写 `"bgRotate": false`。不写就自动选——每个皮肤有 8–11 张风格各异的亮底背景（手账：横线本 / 方格 / 点阵 / 牛皮纸 / 水彩纸 / 便签墙 / 旧书页 / 坐标纸；剪纸：红纸衬边 / 宣纸 / 窗花 / 祥云 / 挂笺 / 洒金…；档案：档案袋 / 旧报纸 / 古地图 / 卡片目录 / 胶片 / 展柜布面…），逐镜模式按镜头角色挑、相邻两镜不重复，装饰重的（`busy`）不进常规镜。某一镜要特定的纸，就写 `"bg": "oldpage"`；清单与许可见 [references/background-library.md](references/background-library.md)。
- 帧参数名：`fxkit` 组件传 `frame={f}`，其余模块传 `f={f}`（传错不报错只会错位，`validate-frame-props.py` 会抓）。

## 第 4 步 · 一条命令

```text
node "<SKILL_DIR>/scripts/make-video.mjs" ./my-video --stills
node "<SKILL_DIR>/scripts/make-video.mjs" ./my-video --render ./my-video/final.mp4
```

Windows 用同一条 `node` 命令（或 `scripts\make-video.cmd`）。依次做：resolve-shots（自动修）→ 门禁 → tsc → 静帧接触表 / 渲染 → 抽帧报告 `renders/report.md`；`--render` 后若装了 RapidOCR，会用 `validate-ocr.py` 抽字幕帧 OCR，核对字幕真的读得出（没装就跳过并提示）。
**先看 `--stills` 静帧，再渲整片**（整片渲染要先征得用户同意）。手作皮肤 `treatment.json` 的 `review.rounds` 为空时 `--render` 会停下（先做独立评审；草稿用 `--skip-review` 显式跳过）。`--render` 默认 1920×1080；响度目标 −16 LUFS（静音旁白片与真人声片相同）。

**读输出**：`✓ 自动修` = 引擎替你改了什么；`· 建议` 不拦；`✗` 才要改——每条都写了怎么改。同一个 ✗ 连续两次没改过来，停下来把报错原文告诉用户。

**看动起来对不对，别直接渲整片**：`node "<SKILL_DIR>/scripts/notebook-video.mjs" preview ./my-video --seconds=30`
（默认 0.5 倍分辨率、关翻页；30 秒约 40 秒出片，同时给接触片和响度读数。单镜验：`--shot=S6`。
`--fx=on` 才带翻页——它会切完整版 Chromium、每帧约 3 秒，别拿它做预览。）
预览结束会打一行 `FillGate coverage`：每镜 `cells`（48 格占用）/ `blank`（全空的列）/ `largest`（最大单体占画面）/ `widest`（最大横向跨度），
`largest<0.06` 或 `blank≥3/8` 会点名。被判空时**不要放大卡片凑面积**，按 [references/composition-gate.md](references/composition-gate.md) §3.8.0 的两条写法改：结构先满再演过程、空洞处补一层属于主体的东西。

## 第 5 步 · （需要时）定制组件

题目需要一张只属于它的图（比如「请求怎么穿过缓存」）时，照抄 `src/custom/RequestLane.tsx` 写一个组件，在 `src/custom/index.ts` 注册，
然后在 `scenes.tsx` 里像其他组件一样用。纪律：只用 `f` 驱动动画；文字 ≥32px；文字色用 `C.ink` / `C.muted` / `C.*Ink`。

## （需要时）真实截图 / 录屏

观众以后要在那个界面上操作（例如 GitHub 的 PR 页）时，可以把真实截图或 ≤10 秒的录屏放进 `MediaFrame`（同一套卡片外观）：
`python scripts/prepare-media.py ./my-video --add pr.png --id pr-page --region diff 0.01 0.31 0.69 0.17`，然后在场景里
`<MediaFrame f={f} id="pr-page" x={200} y={200} w={1060} h={662} focus="diff" focusAt={b[1]} />`。
来源优先级：用户文件 > 自己截的官方页面 > CC0 / CC-BY / Pexels / Unsplash（写清 url / license / credit，署名自动上屏）。
**没有兼容许可就用组件重画。** 细节与门禁：[references/real-media.md](references/real-media.md)。

## 引擎替你保证的

**硬门禁（客观）**：取景不切断标题 / 标签（推近自动留边、回退倍数）；字号地板；文字对比度 ≥4.5:1；背景库每张都有来源与许可、亮底、字幕区对比度够（`validate-backgrounds.py`）；字幕每行 ≤16 字、读速（组件路线 ≤4.5 字/秒、手作路线 6.5 字/秒）；
画面不静止超过约 1 秒（镜尾 >1.5 秒无事件自动补收束慢推）；音画同步；音效文件 sha256 与增益 / 提前量和 manifest 一致。
**软建议（主观，只提示）**：同屏强调数、每镜字号种类、装饰预算、快慢交替、留白。
**开场**：`validate-opening.py` 管前 3 秒——第 0 帧就有东西在发生、首条字幕 ≤1 s、片名不当第一镜、前 3 秒 ≥3 拍、第一句不是泛问句（`--video` 还会读像素复核）。

**音效**：只挂在真事件上；每条 cue 按 manifest 的 `offsetMs` 提前起播，让瞬态落在视觉命中帧；间隔 ≥150 ms；音乐床在音效下闪避。密度由片级 `sfxDensity` 决定：缺省 `sparse`（每镜一记：换章的镜给章节声、其余给末拍，误区镜另留反转音），写 `"sfxDensity": "normal"` 回到「一拍一个」。旁白由使用者后配，所以默认就该克制。

## 可选 · auto 草稿（story.json）

赶时间时可以先用 `node scripts/make-video.mjs my-story.json ./draft --stills` 从蓝图直接出草稿（`compose-story.py` 自动排版、关键词同步、字幕定时）。
它用组件式版式（define / number / bars / compare / code / flow / list / quiz / custom / media）；`statement` 只渲染成一张卡片，不是缺省版式。
正式交付仍建议改写成第 2–3 步的组件场景。细节见 [references/auto-engine.md](references/auto-engine.md)；示例 `examples/*.story.json`。

## 更多

- 音效库与调音：[references/sfx-library.md](references/sfx-library.md)
- 主题：[references/theme-flat.md](references/theme-flat.md)、[references/theme-cel.md](references/theme-cel.md)、[references/theme-journal.md](references/theme-journal.md)、[references/theme-papercut.md](references/theme-papercut.md)、[references/theme-archive.md](references/theme-archive.md)
- 导演层与手作：[references/director-method.md](references/director-method.md)、[references/style-recipes.md](references/style-recipes.md)、[references/craft-kit.md](references/craft-kit.md)
- 开场 / 节奏 / 运镜：[references/narrative-hook.md](references/narrative-hook.md)、[references/pacing-rhythm.md](references/pacing-rhythm.md)、[references/camera-language.md](references/camera-language.md)
- 真实素材：[references/commons-media.md](references/commons-media.md)、[references/real-media.md](references/real-media.md)
- 背景库：[references/background-library.md](references/background-library.md)
- 真翻页 / 揭纸转场：[references/fx-effects.md](references/fx-effects.md)
- Windows：[references/windows-compatibility.md](references/windows-compatibility.md)
- 自检：`node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-skill`、`python scripts/selftest.py`、`python scripts/negative-gate-check.py`

依赖纪律：`scripts/*.py` 只用 Python 3.10+ 标准库；模板已内置的 npm 依赖随 `npm ci` 安装，新增依赖要用户同意。
