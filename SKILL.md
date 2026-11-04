---
name: notebook-video
version: 3.5.3
description: Turn a topic into a Chinese 16:9 teaching video. Draft-paper narration comes first: there is no pen on screen, and everything appears only when the voice-over reaches it and grows in progressively — text unfolds along the reading direction, sketches trace part by part, annotations are drawn as they are spoken, at most two things grow at once. (flat / cel component themes, or the journal / papercut / archive hand-made skins driven by a metaphor-first director layer) with React, TypeScript and Remotion. Two kinds of shots alternate: a **notebook page** (`layout: "page"`) that carries the real thing — a mounted archival plate, a magnifier over it, handwriting and a red seal on paper — and **components** (flows, comparisons, bars, numbers, code) that do the explaining. Line drawings are optional (specimen sketches only), because a clip-art sketch explaining a concept reads worse than no drawing. Weak-model friendly: ten teaching blueprints (five component-route + five hand-made structure families) with per-shot component picks, golden examples, a five-step workflow and one cross-platform command (`node scripts/make-video.mjs <project>`, `make-video.cmd` on Windows) that resolves shots, runs hard gates with objective auto-fixes (no clipped titles, font floor, text contrast, ≤16-character captions at 4.5 chars/s, no dead tails, blurry-media check) and renders stills or the MP4. Tuned semantic sound effects land on the visual hit; no BGM by default. Every topic first searches Wikimedia Commons / Openverse for licence-filtered real media with automatic on-screen credits. TTS narration (edge-tts or your own recording) drives caption and shot timing; no image-generation model. Use when the user asks to 做科普视频, 讲解视频, 概念讲解, 代码讲解, 数据对比视频, 流程讲解, 踩坑提醒, 产品讲解, 30 秒到数分钟的中文讲解短片, 或把一段文字讲解做成 MP4.
---

# notebook-video · 草稿纸讲解：讲到哪，长到哪（手账页承载 + 组件讲解）

**第一原则 · 草稿纸讲解**：画面像一张边讲边写的草稿纸。画面上**没有笔**；每样东西都在旁白讲到它时才出现，一点点长出来，不整块弹出，同一时刻不冒出一堆。下面的「手账页 / 组件 / 直书页」管的是**画什么**，草稿纸讲解管的是**什么时候、怎么出现**；两者冲突时，按草稿纸讲解。

**出现规则**（auto 路线由引擎自动做到；手写场景路线照着写。全文见 [references/reveal-rules.md](references/reveal-rules.md)；版式、配色与组件搭配见 [references/draftpaper-design.md](references/draftpaper-design.md)）：
1. **跟着旁白**：一样东西在讲到它的那句话开始时才开始出现，不提前。
2. **长出来**：文字和卡片左→右展开，用时 = 字数 × 4 帧（最少 12、最多 45 帧）；线稿按部位依次描出，整幅 24–45 帧；圈注 14 帧，下划线和箭头 12 帧，手写小字 24 帧。手账页上的真图版、照片、截图可以整件「贴上」，但也要等讲到它的那句。
3. **不扎堆**：同一镜里，相邻两样东西开始出现至少隔 12 帧（0.4 秒）；同一时刻最多 2 样在长。
4. **不预铺**：镜头切进来时，纸上只有已经讲过的东西；开镜头 6 帧内最多 1 样东西开始出现。

画面由两种东西分工，**交替出现**：

| | 负责 | 长什么样 | 怎么写 |
|---|---|---|---|
| **手账页** | **承载**：把要讲的那个真东西摆到眼前 | 一页纸：装裱好的原版图版 / 标本、手写页眉、朱红印章、一行手写说明、放大镜 | `layout: "page"` + `content.page` = `plate` / `loupe` |
| **组件** | **讲解**：把概念拆开、对比、算清 | 流程、对比、清单、柱条、大数字、代码 | `flow` / `compare` / `list` / `bars` / `number` / `code` |

- **三种呈现模式**（`story.json` 顶层 `"mode"`），配比不同，`validate-fusion` 按模式判：

| mode | 手账页 | 组件（含直书） | 什么时候用 |
|---|---|---|---|
| `hybrid`（默认） | 20–75% | ≥25% | 有物可看、也有结构要讲——绝大多数片 |
| `component`（全组件） | ≤12% | ≥60% | 内容本身就是结构（流程 / 对比 / 清单 / 数据），没有实物可拍 |
| `freeform`（全非组件） | ≥40% | 多框组件 ≤10% | 有物可看，或抽象但有几何可画；只有手账页 + 直书页 |

  模式是**门禁契约**，不是风格开关：声明 `component` 却整片是手账页，会被点名「别声明一套做另一套」。
- 主题里的那个东西全片**至少出现一次**（手账页图版说明 / 墨图标签 / 标本速写 / `see` → 全组件片还认组件镜的 `title`），否则判 **P0**。
- 手账页的容器是**纸**，不是卡片：不要给它套圆角框，也不要把图版做成"浏览器截图卡片"。
- 手账页写法见 [references/journal-page.md](references/journal-page.md)；最好的一支参考片是 [examples/cell-notebook](examples/cell-notebook/README.md)（49 秒 / 8 镜 / 真图版 + 放大镜 + 印章）；组件配方见 [references/recipes.md](references/recipes.md)。

**线稿是可选件，只做标本速写**（一件东西 + 尺寸线 + 手写名）。不要用简笔线稿去「解释」概念——
实测那种画面像剪贴画，比不画更差。`validate-fusion` 对「文字 + 简笔线稿」超过 20% 判 P1。线稿写法见 [references/linework.md](references/linework.md)。

组件是信息的主体，但**不是唯一的载体**：有真东西可看时用 `page`（手账页），只有一组关系要讲时用 `type`（直书页：靠字号、行距、对齐做层级，一个框都不出）。
直书页是「省掉框」，不是「省掉内容」——每行 ≤10 字、≤5 行，全片 ≤40%；超了就成一本排版册。写法见 [references/journal-page.md](references/journal-page.md)。
另外，每片留 2–3 个**锤子帧**（整章最该被记住的一句，满屏单独出现 1.5–2.5 秒），规则见 [references/pacing-rhythm.md](references/pacing-rhythm.md)。
锤子帧怎么做：组件路线用 `StampBanner`（或 `Callout` 放大到 displayL）独占一镜；手作路线用 `HandLettering` 手写满屏一句，或 `Seal` 印章大字——都放在媒介里，不是白底大字。
只有 16:9；五个皮肤：`flat`（默认）、`cel`，以及 3.3.0 的手作皮肤 `journal`（手账水彩）/ `papercut`（红色剪纸）/ `archive`（档案灯台）。
TTS 是正式步骤：`notebook-video tts <工程>`（默认 edge-tts；也可 `--engine=file` 用你自己的录音），字幕与镜头按**词级时间**对齐；没有真实旁白时 `--render` 会停在渲染前（静音占位只给 `--stills` / `preview`）。默认无 BGM，音效稀疏。

## 先选路线

| 题目 | `mode` | 路线 |
|---|---|---|
| 软件、产品、代码、操作教程（没有实物可拍） | `component` | `flat` / `cel` + 下面第 1–5 步 |
| 科普、自然、历史、"为什么"（有真东西可看） | `hybrid` | `journal` / `papercut` / `archive`，先走第 0 步导演层；手账页承载 + 组件讲概念 |
| 单位、几何、算法、纯结构（没实物但有形可画） | `freeform` | `journal`：手账页 + 直书页，多框组件 ≤10% |

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

**auto 路线（story.json）必读 2 份**：[auto-engine.md](references/auto-engine.md)、[reveal-rules.md](references/reveal-rules.md)；用到配方 / 线稿时再读 [recipes.md](references/recipes.md)、[linework.md](references/linework.md)。
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

**翻页是缺省，不是选项。** 任何皮肤、任何 story，只要不写 `transition`，镜间一律翻页：
`pageturn`（纸被卷起来，WebGPU）→ 画不了就退到 `pageflip`（纯 CSS 的折痕翻页，无依赖），
两者**同向**（近乎竖直的折线、下角领先，从右往左翻）。所以 story 里**不需要**写
`"transition": "pageturn"`，写了反而会把自定义皮肤的选择固定死。
`whip`（甩镜）/ `zoom` / `slide` / `drop` 仍可用，但都要显式写。

**翻页一定有纸声**（`page` 拟音，转场第 3 帧命中）。它是动作音，不是标点：
`sfxDensity: sparse` 只削标点，不削动作；换章那一镜 chapter 与 page 并存，不会互相吃掉。

渲染器先画一张探针验收 WebGPU 卷页；通过就换完整版 Chromium 只渲转场那 22 帧，再按帧号拼回快速渲染的整片
（`transition-plan.mjs` 的 `curlWindows` 定窗口 + `fx-browser.mjs` 的 `spliceArgs` 拼回）。缺完整版 Chromium 时探针失败，全片照常出，
翻页自动降级成折痕版并在报告里记 P1（[references/fx-effects.md](references/fx-effects.md)）。
装浏览器：`npx playwright install chromium`（国内加 `PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright`）。

工程里已有一部完整的示例片（8 镜）。**照着改，不要从零写**：

- `manifests/shots.json`：每镜一行（`skeleton` / `live` 组件 / `cameraIntent` / `beats` / `transition`）——镜头表是唯一真相；
- `src/scenes.tsx`：每镜一个 React 组件，用 `live` 里列的组件画出来，动画只用帧号 `f`；
- `src/film.ts`：片名、章节标题；
- `manifests/caption-cues.json` + `audio/narration.mp3.json`：字幕（每行 ≤16 字）。

> **抄结构，不要抄片子。** 拿到模板最容易犯的错是把它再演一遍——同样的镜序、同样的招牌镜头、同样的收尾。
> 改完跑一次 `eval-project "<SKILL_DIR>/assets/lecture-template" ./my-video`，看
> **版式种类 / 介质种类 / 转场种类 / 镜长分布 / 最大推近**这几行有没有真的不同；全都一样就说明你只是在换文案。
> 这是测量不是打分——"像不像"没有客观界线，但两列摆在一起你自己看得出来。

组件怎么选：[references/media-routing.md](references/media-routing.md)（修辞动作 → 组件表）、[references/fxkit.md](references/fxkit.md)。
完整作者手册（骨架、镜头语言、门禁细节）：[references/handwritten-scenes.md](references/handwritten-scenes.md)。

## 第 3 步 · 写台词与镜头表

- 一镜 1–3 句，一句一个意思；字幕超 16 字由 `build-semantic-captions.py` 在合法断点自动拆（不拆词、英文、数字）。
- 要观众「看那里」时，在镜头表写 `cinema.focus`（推近到那个组件的矩形）；不写也有缺省缓推。
- 相邻两镜换骨架；一镜一个概念；关键数字用 `KineticNumber` 数过去。
- 背景（3.3.0）：手作皮肤默认 `bgMode: "chapter"`（每章一张纸、章内沿用），flat / cel 默认 `"shot"`（逐镜轮换）；全片一张纸写 `"bgMode": "film"`，完全不轮换写 `"bgRotate": false`。不写就自动选——每个皮肤有 8–11 张风格各异的亮底背景（手账：横线本 / 方格 / 点阵 / 牛皮纸 / 水彩纸 / 便签墙 / 旧书页 / 坐标纸；剪纸：红纸衬边 / 宣纸 / 窗花 / 祥云 / 挂笺 / 洒金…；档案：档案袋 / 旧报纸 / 古地图 / 卡片目录 / 胶片 / 展柜布面…），逐镜模式按镜头角色挑、相邻两镜不重复，装饰重的（`busy`）不进常规镜。某一镜要特定的纸，就写 `"bg": "oldpage"`；清单与许可见 [references/background-library.md](references/background-library.md)。
- 帧参数名：`fxkit` 组件传 `frame={f}`，其余模块传 `f={f}`（传错不报错只会错位，`validate-frame-props.py` 会抓）。

## 第 4 步 · 一条命令

```text
node "<SKILL_DIR>/scripts/make-video.mjs" ./my-video --stills
node "<SKILL_DIR>/scripts/make-video.mjs" ./my-video --render ./my-video/final.mp4
```

Windows 用同一条 `node` 命令（或 `scripts\make-video.cmd`）。依次做：resolve-shots（自动修）→ 门禁 → tsc → 静帧接触表 / 渲染 → 抽帧报告 `renders/report.md`；`--render` 后若装了 RapidOCR，会用 `validate-ocr.py` 抽字幕帧 OCR，核对字幕真的读得出（没装就跳过并提示）。

**旁白顺序（auto 路线）**：`compose-story` 先写出 `narration.txt` → 你跑 `notebook-video tts <工程>` 生成音频 → `make-video` 里第二次 compose 按词级时间重排字幕与镜头。
**改了 story 必须重跑 compose 再 tts**：`story.json` 比 `narration.txt` 新时 tts 会直接停下，告诉你先跑 compose——
否则它会读上一版旁白，**出半截音频而且不报错**。自己手写 narration（不跟 story 走）时加 `--allow-stale`。
**先看 `--stills` 静帧，再渲整片**（整片渲染要先征得用户同意）。手作皮肤 `treatment.json` 的 `review.rounds` 为空时 `--render` 会停下（先做独立评审；草稿用 `--skip-review` 显式跳过）。`--render` 默认 1920×1080；响度目标 −16 LUFS（静音旁白片与真人声片相同）。

**渲染中途失败别整片重渲**：`notebook-video render <工程> <输出> --resume`。raw 中间产物只在**成功交付后**才删除，
所以渲染/响度/封装任一环节失败都能接着做；输入（场景、素材、音频、story）没变就跳过整片渲染，直接做响度与封装。
渲染若**一动不动**（不是慢），看门狗会在 8 分钟无输出时中止并给出下一步（`REMOTION_STALL_MS` 可调）。

**改完一版想确认"有没有变好"**：`node "<SKILL_DIR>/scripts/notebook-video.mjs" eval-project 旧工程 新工程`。
它把片子拆成可比的数据（镜长分布、版式/介质/转场种类、运镜覆盖、字幕密度、空场读数）并给出 Δ。
**它不打分**——判据只在门禁里存一处，两处各写一份阈值就会漂移。看到 Δ 之后，好坏仍由门禁 + 独立评审判。

**读输出**：`✓ 自动修` = 引擎替你改了什么；`· 建议` 不拦；`✗` 才要改——每条都写了怎么改。同一个 ✗ 连续两次没改过来，停下来把报错原文告诉用户。

**交付不止一个 mp4**。`--render` 成功后会自动再出两样（都失败不拦片，只记一笔）：

| 产物 | 怎么来的 | 给谁 |
|---|---|---|
| `renders/captions.srt` | `export-srt` 从 `manifests/caption-cues.json` 导出（就是画面里那套断句，不是重新识别） | 上传平台要字幕轨、或别人要翻译 |
| `renders/poster.jpg` | `poster` 渲一帧静帧。默认取 `treatment.signature_shot` 声明的招牌镜头的**落定窗口**（动作做完、还没到切点），并且**不画字幕** | 封面 / 缩略图 / 文档配图 |

单独用：`notebook-video poster <工程> [out.jpg] [--shot=S4|--frame=759]`、`notebook-video export-srt <cues.json> <out.srt>`；
两样一起重出用 `notebook-video deliver <工程>`（改封面构图、换字幕都不必再渲整片）。
不要拿几何中点当封面：中点经常正好压在最后一拍上，封面里会出现半截正在被写的字（cell 的 S5 就踩过两次）。

**看动起来对不对，别直接渲整片**：`node "<SKILL_DIR>/scripts/notebook-video.mjs" preview ./my-video --seconds=30`
（默认 0.5 倍分辨率；**翻页预览里就有**——不开 fx 时走纯 CSS 的折痕翻页，速度不受影响。
30 秒约 40 秒出片，同时给接触片和响度读数。单镜验：`--shot=S6`。
`--fx=on` 是把翻页升级成 GPU 卷页（纸真的弯起来、带纸背透光），它会切完整版 Chromium
（预览 0.5x 下约 1.8 秒/帧，交付分辨率约 3 秒/帧），所以别拿它渲 30 秒窗口，
**要看卷页就只截转场那 30 来帧**：
`--from=<跨镜边界前一秒> --seconds=1.2 --fx=on`（实测 61 秒出片）。
跨镜边界在 `manifests/shots.resolved.json` 的 `from` 里，除以帧率就是秒。带翻页时不给全片耗时推算，
因为只有转场帧走 WebGPU，线性外推会得假数字。）
想量「是不是边讲边长」：`python scripts/measure-reveal.py <工程> renders/preview-*.mp4`（只报告，不拦；读法见 references/reveal-rules.md）。
预览结束会打一行 `FillGate coverage`：每镜 `cells`（48 格占用）/ `blank`（全空的列）/ `largest`（最大单体占画面）/ `widest`（最大横向跨度），
`largest<0.06` 判「主体过小」，但有两条豁免：`widest≥0.45`（面积小但横跨够的条状主体——标尺、格带、时间轴）
和 `blank=0` 且 `cells≥24`（照片+引线+网格这类多个中等元素拼成一个主体，没有单个"大件"）。
`blank≥3/8` 判「横向空洞」。被判空时**不要放大卡片凑面积**，按 [references/composition-gate.md](references/composition-gate.md) 的写法改：空洞处补一层属于主体的东西。**不要为了让开头满而把东西提前摆上**——FillGate 量的是每镜最完整的那一帧，开头空着是草稿纸的正常状态。

**片子比 30 秒长时，别看开头就下结论。** `preview --seconds=30` 只覆盖前六镜，cell 的 S7/S8 就是这么漏的
（补跑 `--from=32` 才发现 S7 右下角空 30%）。全片一次量完用 `sweep`——每镜截一张落定态、拼成一张体检表，八镜约 60 秒：

```bash
node "<SKILL_DIR>/scripts/notebook-video.mjs" sweep ./my-video          # 0.5x，八镜一张表
node "<SKILL_DIR>/scripts/notebook-video.mjs" sweep ./my-video --plan   # 只算会量哪几帧，不起浏览器
node "<SKILL_DIR>/scripts/notebook-video.mjs" sweep ./my-video --json   # 给脚本读（stdout 只有 JSON）
```

它按镜取「切点前最近的一个 **15 的倍数**帧」，两个条件都不是随手写的：必须是 15 的倍数，因为 FillGate 只在
`frame % 15 === 0` 上采样，取别处会得到**零数据**——而零数据和"这镜没问题"在屏幕上长得一模一样；必须落在**后半段**，
因为入场帧几乎必然是空的，拿它判空场会把每一镜都打成空洞（FillGate 第一版就是这么误报的）。
产出三样：终端八行表、`renders/sweep-sheet.jpg`（每镜一格，一眼看完构图）、`renders/sweep.json`（含每镜量的是第几帧，可复查）。
数字可能比整片渲染略低（整片在整镜里扫，sweep 只取一帧，差 2–3 格属正常），但**判定用的是同一套阈值**
（`assessCoverage()`，渲染收尾那行 `FillGate coverage` 也走它——阈值只有一处）。

**覆盖率留档只有两个来源**：整片 `render` 和 `sweep`。`preview` / `render-range` / `review-frames` 是**窗口**渲染，
量到的是"窗口内最完整帧"，不是"整镜最完整帧"——实测 60 帧窗口把 S1 记成 cells=25，整镜是 28。
这几个命令只打印、不写 `fill-coverage.json`，免得一次"看一眼"的预览把某镜的覆盖率改成假数字。

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

**引擎不能保证的（P2-22，说清楚免得当成事实核查器）**：故事里的**事实、数字、历史说法是否正确**。
门禁能验结构、时长、画面、引用格式、可读性、复现，唯独验不了「这句话对不对」——那是人工审读的事。
`validate-facts.py` 只保证**标注本身合法**（引用的来源存在、类比不被当机制事实、AI 生成的 see/ink
描述不当来源），并把「含数字/年份的未标注文本」列成审读清单（`--review`）供人工核对。
**可核验断言**（数字、年份、机制）要么写 `claim: {kind:"fact", source:"<sources 里的 id>"}`，
要么明确标成 `claim: {kind:"analogy"}`（解释性比喻，不能当机制事实）。**过渡句、观点、比喻不必逐条标注**——
所以这不是无差别硬门禁：缺标注只提示（P1），标注自己说不通才拦（P0）。

**人工审读节点**：出片前跑一次 `validate-facts PROJECT --review`，把清单里的数字/年份逐条核对。
AI 生成的图（`content.ink` / `content.figure` 的 label）是**说明性文字**，不是事实来源。
**开场**：`validate-opening.py` 管前 3 秒——第 0 帧就有东西在发生、首条字幕 ≤1 s、片名不当第一镜、前 3 秒 ≥3 拍、第一句不是泛问句（`--video` 还会读像素复核）。

**音效**：只挂在真事件上；每条 cue 按 manifest 的 `offsetMs` 提前起播，让瞬态落在视觉命中帧；间隔 ≥150 ms；默认**无 BGM**（只有 `treatment.sound.music.use=true` 才加载音乐床，并在音效下闪避）。密度由片级 `sfxDensity` 决定：缺省 `sparse`（每镜一记：换章的镜给章节声、其余给末拍，误区镜另留反转音），写 `"sfxDensity": "normal"` 回到「一拍一个」。旁白是 TTS 生成的，音效必须压在人声下，所以默认就该克制。

## 可选 · auto 路线（story.json）

赶时间时可以先用 `node scripts/make-video.mjs my-story.json ./draft --stills` 从蓝图直接出片（`compose-story.py` 自动排版、关键词同步、字幕定时）。
它用这几种版式：**`page`**（手账页，`content.page` = `plate` / `loupe`）、`define` / `number` / `bars` / `compare` / `code` / `flow` / `list` / `quiz` / `custom` / `media`；`statement` 只渲染成一张卡片，不是缺省版式。
要用配方和线稿就走这条路线；要逐镜手调版面，再改写成第 2–3 步的手写场景。细节见 [references/auto-engine.md](references/auto-engine.md)；示例 `examples/*.story.json`。

## 文档

全部 51 篇正文的索引按「你接下来要做什么」分组，见 [references/INDEX.md](references/INDEX.md)（索引本身不计入 51）。
作者通常只读 4 篇（见上文「手作路线只必读 4 份」），其余按需查。

- 自检：`node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-skill`、`python scripts/selftest.py`、`python scripts/negative-gate-check.py`
- 断句短语规则要 BudouX。**技能已自带一份**（`assets/vendor/budoux/`，Apache-2.0，80 KB 中文切片），所以三个自检命令都不用加参数就能真正跑这条规则；工程里装了 `node_modules` 时优先用工程那份（版本跟 `package-lock.json` 走）。结论行会写 `phrase rule: enforced (BudouX from …)`；如果出现 `did NOT run`，说明 `assets/vendor` 被删了——那是真故障，别当成通过。

依赖纪律：`scripts/*.py` 只用 Python 3.10+ 标准库；模板已内置的 npm 依赖随 `npm ci` 安装，新增依赖要用户同意。
