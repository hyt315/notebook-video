---
name: notebook-video
description: Turn a topic into a Chinese 16:9 teaching video with React, TypeScript and Remotion. Draft-paper narration, no pen on screen; each element appears only when the voice-over reaches it and grows in progressively. Notebook pages (the `page` layout with real archival media, a magnifier, handwriting, a red seal) alternate with explaining components (flow, compare, bars, numbers, code). Themes are flat / cel components, or journal / papercut / archive hand-made skins with a director layer. Includes optional teaching blueprints, golden examples, and one command (`node scripts/make-video.mjs`, `make-video.cmd` on Windows) that runs hard gates with auto-fixes and renders stills or the MP4. Real media from Wikimedia Commons / Openverse with on-screen credits; TTS (edge-tts or your own recording) drives caption timing; semantic SFX, no BGM, no runtime image-generation or network asset calls. Use when the user asks to 做科普视频, 讲解视频, 概念讲解, 代码讲解, 数据对比视频, 流程讲解, 踩坑提醒, 产品讲解, 30 秒到数分钟的中文讲解短片, 或把一段文字讲解做成 MP4.
---

# notebook-video · 草稿纸讲解：讲到哪，长到哪

**第一原则**：画面像一张边讲边写的草稿纸，画面上没有笔。每样东西在旁白讲到它时才出现、一点点长出来；同一时刻不冒出一堆。「画什么」和「什么时候出现」冲突时，以草稿纸节奏为准（细节见 [draftpaper.md](references/draftpaper.md#reveal-rules)）。

## 去哪读

| 你要做什么 | 读 |
|---|---|
| **写讲稿**（讲清一件事、误解优先、`$asks`、好坏对照） | [narration.md](references/narration.md) |
| 定讲法、写导演层（手作路线必读）、冷开与节奏 | [director.md](references/director.md) |
| 出现规则、草稿纸版式与动效 | [draftpaper.md](references/draftpaper.md) |
| 镜头表、骨架、手写场景逃生舱、画布与配方 | [scenes.md](references/scenes.md) |
| 挑组件：帧参数铁律、手作材质、线稿、手账页 | [components.md](references/components.md)；53 件选型查 [media.md#component-index](references/media.md#component-index) |
| 运镜导演、虚拟摄影机、翻页转场 | [camera.md](references/camera.md) |
| 介质路由、开源图库检索、自备素材、背景库 | [media.md](references/media.md) |
| 旁白 TTS、字幕断句、音效电平 | [audio-captions.md](references/audio-captions.md) |
| auto 引擎、环境、Windows、性能、完整工作流 | [technique.md](references/technique.md)（[#skill-workflow](references/technique.md#skill-workflow)） |
| 门禁分级、交付清单与排雷 | [checks.md](references/checks.md) |
| 评审卡（5 项 1–5 分） | [rubric.md](references/rubric.md) |
| 皮肤契约（按所选皮肤读 1 篇） | [themes/](references/themes/system.md)：`flat` / `cel` / `journal` / `papercut` / `archive` |

**必读路径**：`auto` 路线读 [narration.md](references/narration.md) + [draftpaper.md](references/draftpaper.md#reveal-rules) + [technique.md](references/technique.md)；手作路线加读 [director.md](references/director.md)、[components.md](references/components.md#craft-kit)、[camera.md](references/camera.md) 与对应皮肤篇。

## 画面分工与选路线

| 呈现形态 | 职责 | 写法要点 |
|---|---|---|
| **手账页** | 承载真图版、照片、放大镜、手写与朱印 | `layout: "page"`（`plate` / `loupe` / `ink`），容器是纸不套圆角框 |
| **组件** | 拆开、对比、算清数据与过程 | `flow` / `compare` / `list` / `bars` / `number` / `code` |
| **直书页** | 单一核心关系或锤子句，字号定层级 | `type`；每行 ≤10 字、≤5 行、全片 ≤40% |

| 题目类型 | `mode`（`validate-fusion` 契约） | 皮肤 | 起手式 |
|---|---|---|---|
| 软件、代码、数据、操作教程 | `component`（手账 ≤12%，组件 ≥60%） | `flat`（默认）/ `cel` | `blueprints/`（`concept` / `code-change` / `data-compare` / `process` / `pitfall`） |
| 科普、自然、历史、"为什么" | `hybrid`（手账 20–75%，组件 ≥25%） | 手作：`journal` / `papercut` / `archive` | 写 `treatment.json` + 照 `examples/recipes/cork-page.story.json`（同名 `.treatment.json` 会自动带入） |
| 单位、几何、算法、纯结构 | `freeform`（手账 ≥40%，多框组件 ≤10%） | `journal` | 照 `examples/recipes/jie-freeform.story.json`（连同同名 `.treatment.json`） |

- `medium-metaphor` / `kishotenketsu` / `mystery` / `scale-ladder` / `experiment`（`$route: handwritten-craft`）仅作手写分镜结构族与 `treatment.candidates[].family` 参考，不可直接喂 `make-video`。
- 主题物（`subject_of_film`，无实物可用 `"abstract"`/`"software"` + `subject_why`）全片须至少出现一次，否则 P0；线稿仅作标本速写（`content.figure` 限宽 360px）；全片留 2–3 个**锤子帧**（`"recipe": "hammer"` 或 `StampBanner`/`HandLettering`/`Seal`）。
- 仅 16:9 横屏，默认交付 `2560×1440`（`--scale=1`；`--scale=0.75` 出 `1920×1080`）。有实物先跑 `commons-search.py` 只收 PD / CC0 / CC BY（见 [media.md#commons-media](references/media.md#commons-media)）。
- **手写场景逃生舱**：逐镜手调编辑 `manifests/shots.json` + `src/scenes.tsx`，定制件在 `src/custom/index.ts` 注册；仅 `fxkit` 与 `toolkit`（`Callout`/`Checklist`）传 `frame={f}`，其余传 `f={f}`（[scenes.md#handwritten-scenes](references/scenes.md#handwritten-scenes)）。

## 五步命令

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project ./my-video --style=flat
# 填好 my-story.json（每镜写清 $asks，1–3 句，相邻换骨架；可选同名 my-story.treatment.json）
node "<SKILL_DIR>/scripts/make-video.mjs" my-story.json ./my-video --stills
node "<SKILL_DIR>/scripts/notebook-video.mjs" tts ./my-video
node "<SKILL_DIR>/scripts/make-video.mjs" ./my-video --render ./my-video/final.mp4
```

Windows 使用相同 `node` 命令或 `scripts\notebook-video.cmd` / `scripts\make-video.cmd`。

- **先看 `--stills`，用户同意后再 `--render`**；局部动态看 `notebook-video preview ./my-video --seconds=30`，全片抽检看 `notebook-video sweep ./my-video`，两版量化对照看 `notebook-video eval-project`。
- 改了 `story.json` 必须重跑 `compose-story` 再跑 `tts`（手写 `narration.txt` 加 `--allow-stale`）；缺真实旁白时 `--render` 自动阻断；默认无 BGM、音效稀疏。
- 字幕行宽 ≤ `CAPTION_MAX_CHARS`（16，去句末标点逐字计 P0）、时长基准 `READ_CPS`（4.5）、读速硬上限 `CPS_MAX`（9.0）；`renders/report.md` 首屏含「讲清楚」评审分（手作路线建议开独立新会话按 [rubric.md](references/rubric.md) 评审，组件路线可选，`--skip-review` 可关闭提示）及成片摘要。
- 中断续渲加 `--resume`；交付自动产出 `renders/captions.srt` 与 `renders/poster.jpg`。

## 读输出与何时停下问用户

- `✓ 自动修` = 已修复；`· 建议`（P1）按需采纳；`✗`（P0）必须改，详见 `renders/gates.json`。被判「空」时在空洞补属于主体的信息层，禁止放大卡片凑面积或预铺（[checks.md#render-gates](references/checks.md#render-gates)）。
- 自检：`node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-skill`、`python scripts/selftest.py`、`python scripts/negative-gate-check.py`（出现 `did NOT run` 视为故障）。
- **必须停下一次问完的场景**：1）准备 `--render` 整片前；2）需新增 npm 依赖前（`scripts/*.py` 严禁依赖三方 pip 包）；3）**引擎不能保证的**：`validate-facts` 不是无差别硬门禁，出片前跑 `notebook-video validate-facts <工程> --review` 人工审读，主要事实（核心数字/年份/因果）或素材找不到合规出处时停下问用户；4）同一个 `✗` 连续两轮修不掉时（给出报错原文）。
