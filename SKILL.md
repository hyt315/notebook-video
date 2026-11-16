---
name: notebook-video
description: Turn a topic into a Chinese 16:9 teaching video with React, TypeScript and Remotion. Draft-paper narration, no pen on screen; each element appears only when the voice-over reaches it and grows in progressively. Notebook pages (the `page` layout with real archival media, a magnifier, handwriting, a red seal) alternate with explaining components (flow, compare, bars, numbers, code). Themes are flat / cel components, or journal / papercut / archive hand-made skins with a director layer. Weak-model friendly, with teaching blueprints, golden examples and one command (`node scripts/make-video.mjs`, `make-video.cmd` on Windows) that runs hard gates with auto-fixes and renders stills or the MP4. Real media from Wikimedia Commons / Openverse with on-screen credits; TTS (edge-tts or your own recording) drives caption timing; semantic SFX, no BGM, no image-generation model. Use when the user asks to 做科普视频, 讲解视频, 概念讲解, 代码讲解, 数据对比视频, 流程讲解, 踩坑提醒, 产品讲解, 30 秒到数分钟的中文讲解短片, 或把一段文字讲解做成 MP4.
---

# notebook-video · 草稿纸讲解：讲到哪，长到哪

**第一原则**：画面像一张边讲边写的草稿纸，画面上没有笔。每样东西在旁白讲到它时才出现、一点点长出来；同一时刻不冒出一堆。「画什么」和「什么时候出现」冲突时，按草稿纸讲解。

**出现规则**（auto 路线由引擎做到，手写场景照着写；全文 [draftpaper.md](references/draftpaper.md#reveal-rules)）：
1. **跟着旁白**：讲到它的那句开始时才出现，不提前。
2. **长出来**：文字和卡片左→右展开，字数 × 4 帧（12–45 帧）；线稿按部位描出 24–45 帧；圈注 14、下划线 / 箭头 12、手写小字 24 帧。手账页的真图版可以整件「贴上」，也要等讲到它。
3. **不扎堆**：同一镜相邻两样开始出现至少隔 12 帧；同一时刻最多 2 样在长。
4. **不预铺**：切镜时纸上只有讲过的东西；开镜 6 帧内最多 1 样开始出现。

## 去哪读

| 你要做什么 | 读 |
|---|---|
| 定讲法、写导演层（手作路线必读）、开场与节奏 | [director.md](references/director.md) |
| 出现、长出来、版式配色与动效 | [draftpaper.md](references/draftpaper.md) |
| 写镜头表、骨架、手写场景、线稿配方 | [scenes.md](references/scenes.md) |
| 挑组件：fxkit、手作材质、线稿、手账页 | [components.md](references/components.md) |
| 运镜、虚拟摄影机、翻页转场 | [camera.md](references/camera.md) |
| 介质路由、真实素材（Commons / 截图录屏）、背景库 | [media.md](references/media.md) |
| 旁白 TTS、字幕断句、音效 | [audio-captions.md](references/audio-captions.md) |
| auto 引擎、环境、Windows、性能、依赖政策、**完整工作流细节** | [technique.md](references/technique.md)（工作流见 [#skill-workflow](references/technique.md#skill-workflow)） |
| 读门禁报告、质量清单、构图 / 呈现门禁怎么修 | [checks.md](references/checks.md) |
| 选定皮肤后的契约（只读那一篇） | [themes/](references/themes/system.md)：`flat` / `cel` / `journal` / `papercut` / `archive` |

**auto 路线必读**：draftpaper.md 的出现规则 + technique.md 的 auto 引擎。**手作路线必读**：director.md 的导演层、components.md 的手作材质、camera.md 的镜头语言、你那套皮肤的 themes/ 一篇。其余按需查。

## 画面怎么分工

| | 负责 | 怎么写 |
|---|---|---|
| **手账页** | 承载：把真东西（原版图版、标本、照片、放大镜）摆到眼前 | `layout: "page"` + `content.page` = `plate` / `loupe` |
| **组件** | 讲解：拆开、对比、算清（流程、对比、清单、柱条、大数字、代码） | `flow` / `compare` / `list` / `bars` / `number` / `code` |
| **直书页** | 只有一组关系要讲时，靠字号行距做层级，不出框 | `type`；每行 ≤10 字、≤5 行，全片 ≤40% |

`story.json` 顶层 `"mode"` 是**门禁契约**（`validate-fusion` 按它判，声明一套做另一套会被点名）：

| mode | 手账页 | 组件（含直书） | 用于 |
|---|---|---|---|
| `hybrid`（默认） | 20–75% | ≥25% | 有物可看、也有结构要讲 |
| `component` | ≤12% | ≥60% | 软件、代码、流程、数据，没有实物 |
| `freeform` | ≥40% | 多框组件 ≤10% | 有物可看或有几何可画，只用手账页 + 直书页 |

- 主题物全片**至少出现一次**（手账页说明 / 墨图标签 / 标本速写 / `see`，全组件片认 `title`），否则 P0。
- 手账页的容器是**纸**：不套圆角框，不把图版做成浏览器截图卡片。
- 线稿只做**标本速写**（一件东西 + 尺寸线 + 手写名），不用简笔线稿解释概念；「文字 + 简笔线稿」超过 20% 记 P1。
- 每片留 2–3 个**锤子帧**（整章最该记住的一句，满屏 1.5–2.5 秒）：组件路线 `StampBanner`，手作路线 `HandLettering` 或 `Seal`。
- 只有 16:9。皮肤：`flat`（默认）、`cel`；手作 `journal` / `papercut` / `archive`。

## 选路线

| 题目 | `mode` | 皮肤 | 蓝图 |
|---|---|---|---|
| 软件、产品、代码、操作教程 | `component` | `flat` / `cel` | `concept` / `code-change` / `data-compare` / `process` / `pitfall` |
| 科普、自然、历史、"为什么" | `hybrid` | 手作皮肤，先写导演层 | `medium-metaphor`（默认）/ `kishotenketsu` / `mystery` / `scale-ladder` / `experiment` |
| 单位、几何、算法、纯结构 | `freeform` | `journal` | 同上 |

**主路线**：`story.json` + 蓝图（`blueprints/*.json`，每镜写了该用的骨架与组件，照抄，别自己发明版式）→ `make-video`。
**逃生舱**（要逐镜手调版面、或强模型想拉高上限）：工程里的 `manifests/shots.json` + `src/scenes.tsx`，题目需要专属图时照抄 `src/custom/RequestLane.tsx` 写组件并在 `src/custom/index.ts` 注册。写法见 [scenes.md](references/scenes.md#handwritten-scenes)；纪律：动画只用帧号驱动，文字 ≥32px，文字色用 `C.ink` / `C.muted` / `C.*Ink`；`fxkit` 组件传 `frame={f}`，其余模块传 `f={f}`（帧参数必填，传错或漏传 tsc 报错）。

**手作路线先写导演层**：照 [director.md](references/director.md#director-method) 写 `manifests/treatment.json`（模板 `treatment.example.json`）——生活问题 → 只属于这个题的隐喻 → 皮肤为什么是它 → 顿悟点的原生动作 → 三个候选结构（至少 2 个结构族）选一个 → 对标学 / 不学 → 每镜写理由。

**每个选题都先搜一次 Commons / Openverse**：`python scripts/commons-search.py search "<英文关键词>" --project ./my-video`，能用的 `add`，交付前 `credits`。只收公有领域 / CC0 / CC BY，署名自动上屏；没有兼容许可就用组件重画（[media.md](references/media.md#commons-media)）。

## 五步命令

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project ./my-video --style=flat     # 1 建工程（手作换 --style=journal 等）
#   2 照抄蓝图写 my-story.json：一镜 1–3 句，一句一个意思，相邻两镜换骨架
node "<SKILL_DIR>/scripts/make-video.mjs" my-story.json ./my-video --stills          # 3 compose → 门禁 → 静帧接触表
node "<SKILL_DIR>/scripts/notebook-video.mjs" tts ./my-video                         #   真实旁白（edge-tts，或 --engine=file 用自己的录音）
node "<SKILL_DIR>/scripts/make-video.mjs" ./my-video --render ./my-video/final.mp4    # 5 读完输出、用户同意后再渲整片
```

Windows 用同一条 `node` 命令，或 `scripts\notebook-video.cmd` / `scripts\make-video.cmd`。第 4 步是**读输出**（下一节）。

- **先看 `--stills`，再渲整片；整片渲染要先征得用户同意。** 看动起来对不对用 `notebook-video preview ./my-video --seconds=30`，全片体检用 `notebook-video sweep ./my-video`。
- **改了 story 必须重跑 compose 再 tts**，否则 tts 读的是旧旁白，出半截音频而且不报错（自己手写 narration 时加 `--allow-stale`）。
- 没有真实旁白时 `--render` 会停在渲染前（静音占位只给 `--stills` / `preview`）。默认无 BGM，音效稀疏。
- 手作皮肤整片渲染前，由新会话只看联系表 + `storyboard.md` + `treatment.json` 做一轮独立评审，写进 `review.rounds`（没评审时 `--render` 只给 P1 提示，照常渲染；`--skip-review` 关掉提示）。
- 字幕每行 ≤16 字（超了自动在合法断点拆）。抄结构不抄片子：改完跑 `notebook-video eval-project "<SKILL_DIR>/assets/lecture-template" ./my-video` 看版式 / 介质 / 转场 / 镜长是否真的不同。
- 渲染中途失败用 `notebook-video render <工程> <输出> --resume`，别整片重渲。交付会自动带 `renders/captions.srt` 与 `renders/poster.jpg`。
- 预览、体检、FillGate 读数、封面、交付物的细节：[technique.md](references/technique.md#skill-workflow)。

## 读输出

- `✓ 自动修` = 引擎替你改了，不用管；`· 建议`（P1）自行判断，不拦；`✗`（P0）必须改，每条都写了怎么改。
- 同一个 ✗ 连续两轮没改过来，**停下**，把报错原文告诉用户。
- 被判「空」时**不要放大卡片凑面积**，也不要为了开头满把东西提前摆上：在空洞处补一层属于主体的东西（[checks.md](references/checks.md#composition-gate)）。
- **引擎不能保证的**：事实、数字、历史说法对不对。`validate-facts` 只查标注是否合法（缺标注只提示 P1，标注自相矛盾才拦 P0，不是无差别硬门禁）；出片前跑 `notebook-video validate-facts <工程> --review`，把清单里的数字、年份逐条人工审读。
- 自检：`node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-skill`、`python scripts/selftest.py`、`python scripts/negative-gate-check.py`。断句规则用随包的 BudouX；结论行出现 `did NOT run` 是真故障，别当通过。

## 何时停下问用户（一次问完）

- 要渲整片（`--render`）之前。
- 需要新增 npm 依赖时（`scripts/*.py` 只用 Python 3.10+ 标准库；模板已内置的依赖随 `npm ci` 安装）。
- 素材没有兼容许可、又画不出替代时；选题的关键事实找不到出处时。
- 同一个 ✗ 两轮修不掉时。
