---
name: notebook-video
description: Turn a topic into a Chinese 16:9 teaching video with React, TypeScript and Remotion. Draft-paper narration, no pen on screen; each element appears only when the voice-over reaches it and grows in progressively. Notebook pages (the `page` layout with real archival media, a magnifier, handwriting, a red seal) alternate with explaining components (flow, compare, bars, numbers, code). Themes are flat / cel components, or journal / papercut / archive hand-made skins with a director layer. Weak-model friendly, with teaching blueprints, golden examples and one command (`node scripts/make-video.mjs`, `make-video.cmd` on Windows) that runs hard gates with auto-fixes and renders stills or the MP4. Real media from Wikimedia Commons / Openverse with on-screen credits; TTS (edge-tts or your own recording) drives caption timing; semantic SFX, no BGM, no image-generation model. Use when the user asks to 做科普视频, 讲解视频, 概念讲解, 代码讲解, 数据对比视频, 流程讲解, 踩坑提醒, 产品讲解, 30 秒到数分钟的中文讲解短片, 或把一段文字讲解做成 MP4.
---

# notebook-video · 草稿纸讲解：讲到哪，长到哪

**第一原则**：画面像一张边讲边写的草稿纸，画面上没有笔。每样东西在旁白讲到它时才出现、一点点长出来；同一时刻不冒出一堆。「画什么」和「什么时候出现」冲突时，按草稿纸讲解。

**出现规则**（auto 路线由引擎做到，手写场景照着写；全文 [draftpaper.md](references/draftpaper.md#reveal-rules)）：
1. **跟着旁白**：讲到它的那句开始时才出现，不提前。
2. **长出来**：文字和卡片左→右展开，字数 × 4 帧（12–45 帧）；线稿按部位描出 24–45 帧；圈注 / 下划线 / 箭头 12 帧，手写小字 8 帧引线 + 每字 2.2 帧（`ANNOT`）。手账页的真图版可以整件「贴上」，也要等讲到它。
3. **不扎堆**：同一镜相邻两样开始出现至少隔 12 帧；同一时刻最多 2 样在长。
4. **不预铺**：切镜时纸上只有讲过的东西；开镜 6 帧内最多 1 样开始出现。

## 去哪读

| 你要做什么 | 读 |
|---|---|
| **写讲稿**（讲清一件事、误解优先、`$asks`、好坏对照） | [narration.md](references/narration.md) |
| 定讲法、写导演层（手作路线必读）、开场与节奏 | [director.md](references/director.md) |
| 出现、长出来、版式配色与动效 | [draftpaper.md](references/draftpaper.md) |
| 写镜头表、骨架、手写场景、线稿配方 | [scenes.md](references/scenes.md) |
| 挑组件：帧参数、手作材质、线稿、手账页 | [components.md](references/components.md)；53 件组件的何时用 / 何时别用只查 [media.md#component-index](references/media.md#component-index) |
| 运镜、虚拟摄影机、翻页转场 | [camera.md](references/camera.md) |
| 介质路由、真实素材（Commons / 截图录屏）、背景库 | [media.md](references/media.md) |
| 旁白 TTS、字幕断句、音效 | [audio-captions.md](references/audio-captions.md) |
| auto 引擎、环境、Windows、性能、依赖政策、完整工作流 | [technique.md](references/technique.md)（[#skill-workflow](references/technique.md#skill-workflow)） |
| 读门禁报告、质量清单、构图 / 呈现门禁怎么修 | [checks.md](references/checks.md) |
| 选定皮肤后的契约（只读那一篇） | [themes/](references/themes/system.md)：`flat` / `cel` / `journal` / `papercut` / `archive` |

**auto 路线必读**：[narration.md](references/narration.md) + [draftpaper.md](references/draftpaper.md) 的出现规则 + [technique.md](references/technique.md) 的 auto 引擎。**手作路线必读**：[narration.md](references/narration.md)、[director.md](references/director.md) 的导演层、[components.md](references/components.md) 的手作材质、[camera.md](references/camera.md) 与所选 `themes/` 一篇。其余按需查。

## 画面怎么分工

| | 负责 | 怎么写 |
|---|---|---|
| **手账页** | 承载：把真东西（原版图版、标本、照片、放大镜）摆到眼前 | `layout: "page"` + `content.page` = `plate` / `loupe` |
| **组件** | 讲解：拆开、对比、算清（流程、对比、清单、柱条、大数字、代码） | `flow` / `compare` / `list` / `bars` / `number` / `code` |
| **直书页** | 只有一组关系要讲时，靠字号行距做层级，不出框 | `type`；每行 ≤10 字、≤5 行，全片 ≤40% |

`story.json` 顶层 `"mode"` 是**门禁契约**（`validate-fusion` 按它判）：

| mode | 手账页 | 组件（含直书） | 用于 |
|---|---|---|---|
| `hybrid`（默认） | 20–75% | ≥25% | 有物可看、也有结构要讲 |
| `component` | ≤12% | ≥60% | 软件、代码、流程、数据，没有实物 |
| `freeform` | ≥40% | 多框组件 ≤10% | 有物可看或有几何可画，只用手账页 + 直书页 |

- 主题物全片**至少出现一次**（手账页说明 / 墨图标签 / 标本速写 / `see`，全组件片认 `title`/`see`），否则 P0。
- 手账页的容器是**纸**：不套圆角框，不把图版做成浏览器截图卡片。
- 线稿只做**标本速写**（一件东西 + 尺寸线 + 手写名），不用简笔线稿解释概念；「文字 + 简笔线稿」超 20% 记 P1。
- 每片留 2–3 个**锤子帧**（满屏 1.5–2.5 秒）：`story.json` 里给那一镜写 `"recipe": "hammer"` + `content.text`（静止上限按锤子镜放宽到 3.0 秒）；手写场景用 `StampBanner`，手作路线 `HandLettering` 或 `Seal`。
- 只有 16:9。皮肤：`flat`（默认）、`cel`；手作 `journal` / `papercut` / `archive`。

## 选路线

| 题目 | `mode` | 皮肤 | 蓝图 |
|---|---|---|---|
| 软件、产品、代码、操作教程 | `component` | `flat` / `cel` | `concept` / `code-change` / `data-compare` / `process` / `pitfall` |
| 科普、自然、历史、"为什么" | `hybrid` | 手作皮肤，先写导演层 | 照 `examples/recipes/cork-page.story.json`（连同同名 `.treatment.json`） |
| 单位、几何、算法、纯结构 | `freeform` | `journal` | 照 `examples/recipes/jie-freeform.story.json`（连同同名 `.treatment.json`） |

`medium-metaphor` / `kishotenketsu` / `mystery` / `scale-ladder` / `experiment` 这 5 个蓝图（`$route: handwritten-craft`）是手写场景路线的分镜结构，不是 `story.json`，不能喂给 `make-video`；auto 路线只用它们给 `treatment.candidates[].family` 选结构族。

**主路线**：`story.json` + 蓝图（`blueprints/*.json`，每镜写好 `$asks`、骨架与组件，照抄）→ `make-video`。
**逃生舱**（手调版面或专属图）：`manifests/shots.json` + `src/scenes.tsx`，定制组件在 `src/custom/index.ts` 注册（见 [scenes.md](references/scenes.md#handwritten-scenes)）。纪律：帧号驱动、文字 ≥32px、安全色 `C.ink` / `C.muted` / `C.*Ink`；`fxkit` 与 `toolkit`（`Callout`/`Checklist`）传 `frame={f}`，其余传 `f={f}`。
**手作路线先写导演层**：照 [director.md](references/director.md#director-method) 写 `manifests/treatment.json`。
**实物体材先搜图库**：`python scripts/commons-search.py search "<英文关键词>" --project ./my-video`，只收 PD / CC0 / CC BY，署名自动上屏（[media.md](references/media.md#commons-media)）。

## 五步命令

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project ./my-video --style=flat     # 1 建工程（手作换 --style=journal 等）
#   2 照蓝图写 my-story.json：按 narration.md 写清每镜 $asks，一镜 1–3 句，相邻换骨架
node "<SKILL_DIR>/scripts/make-video.mjs" my-story.json ./my-video --stills          # 3 compose → 门禁 → 静帧接触表
node "<SKILL_DIR>/scripts/notebook-video.mjs" tts ./my-video                         #   真实旁白（edge-tts，或 --engine=file）
node "<SKILL_DIR>/scripts/make-video.mjs" ./my-video --render ./my-video/final.mp4    # 5 读完输出、用户同意后再渲整片
```

Windows 用同一条 `node` 命令，或 `scripts\notebook-video.cmd` / `scripts\make-video.cmd`。第 4 步是**读输出**。

- **先看 `--stills`，再渲整片；整片渲染要先征得用户同意。** 动态预览用 `notebook-video preview ./my-video --seconds=30`，体检用 `notebook-video sweep ./my-video`。
- **改了 story 必须重跑 compose 再 tts**（手写 narration 加 `--allow-stale`）。无真实旁白时 `--render` 会停在渲染前。默认无 BGM，音效稀疏。
- **独立评审（P1 不拦，报告首屏呈现）**：手作皮肤整片渲染前建议由新会话按 [references/rubric.md](references/rubric.md) 评审并写入 `review.rounds`（组件路线同样可用该评审卡，作为可选步骤）；`renders/report.md` 首屏直接显示评审分数，未评审首行写「未评审」（`--skip-review` 关掉 P1 提示）。
- 字幕一行 ≤ `CAPTION_MAX_CHARS`（16）字（去句末标点逐字计，ASCII 计 1，P0）；排时长基准 `READ_CPS`（4.5）字/秒，硬门禁上限 `CPS_MAX`（9.0）字/秒。改完跑 `notebook-video eval-project` 对照客观指标。
- 续渲用 `notebook-video render <工程> <输出> --resume`。交付自动带 `renders/captions.srt` 与 `renders/poster.jpg`。

## 读输出

- `✓ 自动修` = 引擎已改；`· 建议`（P1）自行判断，不拦；`✗`（P0）必须改。明细见 `renders/gates.json`。
- 同一个 `✗` 连续两轮修不掉，**停下**把报错原文告诉用户。
- 被判「空」时**不要放大卡片凑面积**或预铺元素，在空洞处补一层属于主体的内容（[checks.md](references/checks.md#render-gates)）。
- **引擎不能保证的**：事实与数字对不对。`validate-facts` 只查标注是否合法（缺标注 P1、矛盾 P0，不是无差别硬门禁）；出片前跑 `notebook-video validate-facts <工程> --review` 人工审读。主要事实找不到出处时停下问用户（见下）。
- 自检：`node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-skill`、`python scripts/selftest.py`、`python scripts/negative-gate-check.py`。结论行出现 `did NOT run` 视为真故障。

## 何时停下问用户（一次问完）

- 要渲整片（`--render`）之前。
- 需要新增 npm 依赖时（`scripts/*.py` 仅用 Python 3.10+ 标准库）。
- 素材没有兼容许可、又画不出替代时；**主要事实**（核心论点依赖的数字、年份、因果）找不到出处时。
- 同一个 `✗` 两轮修不掉时。
