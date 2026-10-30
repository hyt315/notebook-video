# Notebook Video · 中文讲课视频技能

<div align="center">

**把一个知识点变成一支 16:9 中文讲课视频：组件场景 + 引擎虚拟镜头 + 对拍音效，一条命令出片，客观门禁自动修。**

[![Version](https://img.shields.io/badge/version-3.4.0-1f6feb)](CHANGELOG.md)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-555)](references/cross-platform-compatibility.md)
[![Themes](https://img.shields.io/badge/themes-flat%20%7C%20cel%20%7C%20journal%20%7C%20papercut%20%7C%20archive-ff7a59)](references/theme-system.md)
[![Validate](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml/badge.svg)](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-1f6feb)](SKILL.md)

中文 | [English](README.en.md)

</div>

---

## 这是什么

`notebook-video` 是一个 **Agent Skill**（一个带 `SKILL.md` 的文件夹）。装进 Claude Code、Codex、Cursor 等 AI 助手后，
你说「做一支讲哈希表的科普视频」，它就按这里的蓝图、模板和门禁，用 **React + TypeScript + [Remotion](https://www.remotion.dev/)**
做出一支 30 秒到数分钟的中文讲课视频，并交付 MP4 和整套可改的源码工程。

- **画面是组件，不是幻灯片**：每一镜都是代码画出来的真组件——控制台、代码差异、清单、数字行、漏斗、进度环、印章、结论条……
  也可以放进真实截图 / 短录屏。
- **镜头会跟着讲**：引擎级虚拟摄影机缺省缓推，讲到哪个词就推近到哪个组件，换镜用甩镜 / 推穿。
- **弱模型也能复刻**：10 个讲课蓝图（5 个组件路线 + 5 个手作结构族）逐镜写好该用的骨架与组件，加上黄金样例、短流程和一条命令；能客观判断的问题，引擎直接自动修。

- **一本手账一张纸、评审先于成片**：手作皮肤默认 `bgMode: "chapter"`（每章一张纸，章内沿用；`"film"` 全片一张、`"shot"` 逐镜轮换），
  装饰重的背景（`busy`）不进常规镜；`resolve-shots` 从实际镜头表自动生成 `storyboard.md` 给独立评审用；
  手作皮肤没做评审时 `make-video --render` 先停下（草稿用 `--skip-review`）；无 TTS 片按读速 `--cps`（缺省 6.5 字/秒）整行出字幕。

- **背景库**：每个手作皮肤再加 8 张、flat / cel 各加 5 张亮底背景（横线本、宣纸、窗花、古地图、胶片、网点、mesh 渐变……），
  不写就按镜头角色自动轮换、相邻两镜不重复；每张都登记了来源与许可（Paper Shaders 离线预渲、Commons 公有领域 / CC0 纹理、确定性程序生成），
  门禁核对亮底与字幕区对比度。见 [references/background-library.md](references/background-library.md)。

- **先想"用什么东西演"**：导演层（隐喻先行 → 媒介即隐喻 → 顿悟点的原生动作 → 三候选结构，`treatment.json` 有门禁）；
  三套亮底手作皮肤（`journal` 手账水彩 / `papercut` 红色剪纸 / `archive` 档案灯台）和 craft 材质组件（压感墨线、"写出来"的中文、水彩晕染、剪纸、放大镜）；
  每个选题先搜 **Wikimedia Commons / Openverse** 的真实素材，许可自动过滤、署名自动上屏。

只有一种画布：**16:9**（交付 2560×1440，缺省按 1920×1080 渲染；设计坐标 1920×1080，原生 30 fps）。五套皮肤：`flat`（默认，安静的现代教育插画风）、`cel`（粗描边漫画风），以及 3.3.0 的手作皮肤 `journal` / `papercut` / `archive`。

## 核心特性

| 能力 | 说明 |
| --- | --- |
| **组件场景** | 4 种骨架（Stage / Split / Zoom / Corridor）+ 组件库（`ConsoleWindow`、`DiffView`、`HighlightCode`、`StatRow`、`Funnel`、`ProgressRing`、`KineticNumber`、`StampSeal`、`VerdictBar` 等），配色全部走主题 token |
| **引擎虚拟镜头** | 每镜缺省缓推；`cinema.focus` 按台词关键词推近到对应组件、镜头横摇；甩镜 / 推穿转场；背景视差；内容太小时自动放大到安全区 60–80%；推近时自动留边，不切断标题 |
| **对拍音效** | 16 个代码合成的语义音效（CC0，`public/sfx/lib/`）+ 可选音乐床；每条 cue 带 `gain` / `offsetMs`，提前起播让瞬态落在视觉命中帧（±1 帧）；间隔 ≥150 ms、约 24 个/分钟封顶；音乐床在音效下自动闪避 |
| **真实素材** | 截图 / ≤10 秒录屏 / 动图放进 `MediaFrame`（与组件同一套卡片外观，可选浏览器 / 窗口 / 手机外壳，区域推近、描框、旁注、署名徽章）；`prepare-media` 一键转码，`validate-media` 拦糊图与许可缺失 |
| **弱模型友好** | 5 个蓝图（concept / code-change / data-compare / process / pitfall），每镜的 `$components` 写明骨架与组件；黄金样例 `examples/`；未填的 `<<占位符>>` 直接报错 |
| **一条命令** | `make-video.mjs`：resolve-shots → 门禁 → tsc → 静帧接触表或整片渲染 → `renders/report.md`；Windows 有 `make-video.cmd` |
| **交付不只是一个 mp4** | 整片渲完自动再出 `renders/captions.srt`（画面里那套断句，不是重新识别）和 `renders/poster.jpg`（取 `treatment.signature_shot` 的落定帧，且不画字幕）。单独重出：`poster` / `export-srt` / `deliver` |
| **改完能对比** | `eval-project 旧工程 新工程` 把片子拆成可比的数据（镜长分布、版式 / 介质 / 转场种类、运镜覆盖、字幕密度、空场读数）并给 Δ。**不打分**：阈值只在门禁里存一处 |
| **先看 30 秒再渲全片** | `notebook-video preview <工程>` 只渲一段（缺省前 30 秒、半分辨率）并出接触片和响度读数；`--shot=S6` 只看一镜。改一版看一版不必等整片，实测 30 秒片段约 40 秒出片 |
| **全片一镜不漏** | `notebook-video sweep <工程>` 每镜截一张落定态、拼成一张体检表（`renders/sweep-sheet.jpg`），八镜约 60 秒跑完，判空场用的是渲染期同一套阈值。`preview` 只看开头，片子长了尾巴容易漏——这一步补的就是它 |
| **门禁与自动修** | 硬门禁只管客观问题（取景切字、字号地板、对比度 ≥4.5:1、字幕每行 ≤16 字、读速（组件路线 ≤4.5 字/秒，手作路线 6.5 字/秒）、画面静止、音画同步、音效电平），能修的自动修；主观项只给建议 |
| **确定可复现** | 所有动画都是帧号的纯函数（不用 `Math.random`、CSS 动画、计时器）；不依赖生图模型，不需要在线 API |

## 3.4.0 新增

- **`preview`：改一版看一版**。只渲一段（缺省前 30 秒、半分辨率）并出接触片与响度读数；`--shot=S6` 只看一镜，`--from` / `--seconds` 任意窗口。不必等整片。
- **`sweep`：全片一镜不漏**。每镜取一帧落定态，拼成 `renders/sweep-sheet.jpg` 体检表；少一镜会明写「未量到」。`preview` 只看开头、片子长了尾巴容易漏——这一步补的就是它。
- **空场可度量**。FillGate 以 8×6 网格量化版面占用（`cells` / `blank` / `largest` / `widest`），「主体过小」有条状主体与组合装置两条豁免；数字落盘 `renders/fill-coverage.json`。
- **交付三件套**。`export-srt` 出 SRT 字幕、`poster` 出封面（取 `signature_shot` 的落定帧、不画字幕）、`deliver` 打包；整片渲完自动产出。
- **`eval-project` 改完能对比**。把片子拆成可比的数据（镜长分布、版式 / 介质 / 转场种类、运镜覆盖、字幕密度、空场读数）并给 Δ，只测量不打分。
- **自带中文分词**。BudouX 模型随仓库分发（`assets/vendor/budoux/`），短语断行在离线环境同样生效。

**旁白**：技能不内置 TTS。使用者可后配任意 TTS 或真人旁白，配好后跑 `match-timing.py` 重对齐即可。

## 快速开始

### 1. 安装技能

把这句话发给你的 AI 助手即可：

> 请安装 notebook-video 技能：克隆 `https://github.com/hyt315/notebook-video` 到你的 skills 目录（如 `~/.claude/skills/notebook-video` 或 `~/.agents/skills/notebook-video`），并确认安装成功。

或者手动安装：

| 平台 | 用户级 | 项目级 |
| --- | --- | --- |
| Claude Code | `git clone https://github.com/hyt315/notebook-video.git ~/.claude/skills/notebook-video` | `.claude/skills/notebook-video` |
| Codex | `git clone https://github.com/hyt315/notebook-video.git ~/.codex/skills/notebook-video` | `.codex/skills/notebook-video` |
| Cursor | `git clone https://github.com/hyt315/notebook-video.git ~/.cursor/skills/notebook-video` | `.cursor/skills/notebook-video` |
| 通用 Agents | `git clone https://github.com/hyt315/notebook-video.git ~/.agents/skills/notebook-video` | `.agents/skills/notebook-video` |

GitHub CLI 2.90+ 也可以：`gh skill install hyt315/notebook-video notebook-video --agent claude-code --scope user`

### 2. 准备环境

- **Node.js 18+**、**Python 3**、**ffmpeg / ffprobe**（抽帧、转码、响度）
- 第一次用前体检并准备渲染用的 Chromium：

```bash
node scripts/notebook-video.mjs check-deps
node scripts/notebook-video.mjs fonts   # 首次自动下载 LXGW 文楷 Lite（约 28 MB，固定版本 + sha256 校验；new-project 也会自动调用）
```

### 3. 出片

```bash
# 建工程（复制模板；--style=flat 或 cel）
node scripts/notebook-video.mjs new-project ./my-video --style=flat

# 改 manifests/shots.json、src/scenes.tsx、src/film.ts、字幕后：
node scripts/make-video.mjs ./my-video --stills                          # 先看每镜关键时刻的静帧接触表
node scripts/make-video.mjs ./my-video --render ./my-video/final.mp4     # 满意了再渲整片
```

**Windows**（cmd / PowerShell）用同一条 `node` 命令，或者：

```bat
scripts\new-project.cmd .\my-video --style=flat
scripts\make-video.cmd .\my-video --stills
scripts\make-video.cmd .\my-video --render .\my-video\final.mp4
```

读输出：`✓ 自动修` = 引擎替你改了什么；`· 建议` 不拦；`✗` 才需要改，每条都写了怎么改。

## 蓝图与镜头长什么样

每镜只改 `<<…>>` 里的内容，`$components` 告诉模型用什么：

```json
{
  "role": "hook",
  "layout": "statement",
  "lines": ["<<一句反常识的现象，含 {{关键词}}>>", "<<一句追问>>"],
  "content": {"text": "<<屏上那句话（≤16 字）>>", "sub": "<<可选副句>>"},
  "$components": {"skeleton": "Stage", "components": ["Callout", "StampBanner", "FitTextBox"]}
}
```

`{{关键词}}` 是同步点：讲到这个词时，镜头推近、组件高亮、音效落在同一帧。填好的完整样例见 [`examples/`](examples/)（哈希表概念、缓存代码改动、SSD 对比 HDD、Git PR 真实截图）。

两条路线：

- **手写组件场景（推荐，正式出片）**：工程目录里的 `shots.json` + `scenes.tsx`，照模板自带的 8 镜示例片改。手册：[references/handwritten-scenes.md](references/handwritten-scenes.md)。
- **story.json 草稿（快速起稿）**：`node scripts/make-video.mjs examples/concept-hash-table.story.json ./draft --stills`，由 `compose-story.py` 自动排版、定时、算镜头。说明：[references/auto-engine.md](references/auto-engine.md)。

## 真实素材

观众以后要在某个界面上操作（比如 GitHub 的 PR 页）时，放真截图比重画更有用：

```bash
python scripts/prepare-media.py ./my-video --add pr.png --id pr-page --region diff 0.01 0.31 0.69 0.17
```

```tsx
<MediaFrame f={f} id="pr-page" x={200} y={200} w={1060} h={662} focus="diff" focusAt={b[1]} />
```

- 录屏会被转成 H.264 恒定 30 fps、缺省去音轨；`--trim` 截取片段。
- 来源优先级：用户文件 > 自己截的官方页面 > CC0 / CC-BY / Pexels / Unsplash；网络素材必须写 `url` / `license` / `credit`，署名徽章自动上屏。没有兼容许可就用组件重画。
- `validate-media` 会拦：文件缺失、放大超过 1.5 倍（会糊）、编码 / 帧率不对、许可或署名缺失、引用了不存在的区域。

详见 [references/real-media.md](references/real-media.md)。

### 先搜 Wikimedia Commons / Openverse（3.3.0）

```bash
python scripts/commons-search.py search "Hooke Micrographia cork" --project ./my-video
python scripts/commons-search.py add ./my-video "File:Micrographia Schem 11.jpg" --id hooke-plate
python scripts/commons-search.py credits ./my-video   # → CREDITS.md
```

免 key、只用标准库；只收公有领域 / CC0 / CC BY（CC BY-SA 默认排除——"相同方式共享"会波及整条片子），署名由 `ArchivePhoto` / `PinnedPhoto` / `LoupeMedia` 强制上屏。
详见 [references/commons-media.md](references/commons-media.md)。

## 主题

| 皮肤 | 风格 | 选法 |
| --- | --- | --- |
| `flat`（默认） | 天空 / 奶油底面、圆角卡片、柔和硬影，安静的现代教育插画 | `--style=flat` |
| `cel` | 米白漫画纸、3px 墨边、墨色偏移影、红蓝黄三原色 | `--style=cel` |
| `journal` | 博物学家手账：暖白棉纸、胶带贴纸、钢笔批注、水彩淡彩，朱砂唯一强调 | `--style=journal` |
| `papercut` | 红色窗花剪纸：米色宣纸、红纸剪片、双轮廓、深红横批字幕 | `--style=papercut` |
| `archive` | 档案灯台：冷白背光台面上的真实档案物件，一个信号色，放大镜 | `--style=archive` |

手作皮肤的字幕是 96 px@1440 的 Noto Serif SC Bold（按需下载、校验 sha256），没有 UI 胶囊；它们要求先写导演层 `manifests/treatment.json`
（[references/director-method.md](references/director-method.md)），组件见 [references/craft-kit.md](references/craft-kit.md)，风格配方见 [references/style-recipes.md](references/style-recipes.md)。

每套皮肤有 8–11 张亮底背景，按 `bgMode` 轮换：`film` 全片一张 / `chapter` 每章一张（手作皮肤默认）/ `shot` 每镜一张（flat、cel 默认），中央约 70% 是内容安全区。清单与许可见 [references/background-library.md](references/background-library.md)。文字色有专门的 `*Ink` 安全色，保证对比度。规格：[references/theme-system.md](references/theme-system.md)、[theme-flat.md](references/theme-flat.md)、[theme-cel.md](references/theme-cel.md)、[theme-journal.md](references/theme-journal.md)、[theme-papercut.md](references/theme-papercut.md)、[theme-archive.md](references/theme-archive.md)。

## 门禁一览

| 阶段 | 检查 | 典型拦截 |
| --- | --- | --- |
| 构建期（Python） | `resolve-shots`、`validate-composition`、`validate-shot-motion`、`validate-frame-props`、`validate-presentation`、`validate-caption-sync`、`validate-semantic-breaks`、`validate-layering`、`validate-visual-plan`、`validate-audio-levels`、`validate-media` | 相邻两镜同版式、内容太小、帧参数名写错、对比度不足、字幕超 16 字或读不完、音效增益与库不一致、素材会糊 |
| 渲染期（浏览器内） | `OverlapGate`、`ClippingGate`、`CanvasBoundsGate`、`FillGate`、`CaptionFitGate`、`MascotGate` | 文字互相压、图形被裁、越出画布、字幕溢出 |
| 成片 | `validate-video`、`validate-motion-gaps` | 尺寸 / 编码 / 色彩标记不对、画面静止过久 |
| 技能自检 | `validate-skill-consistency`、`selftest`、`negative-gate-check` | 文档写了不存在的组件、断链；每道门禁喂坏输入必须拦住 |

细节：[references/composition-gate.md](references/composition-gate.md)、[references/presentation-gate.md](references/presentation-gate.md)、[references/quality-checklist.md](references/quality-checklist.md)。

## 项目结构

```text
notebook-video/
├── SKILL.md                     # 技能入口：5 步流程（Agent 读这个）
├── manifest.json                # 名称、版本、许可
├── blueprints/                  # 10 个讲课蓝图（组件路线 5 + 手作结构族 5）
├── examples/                    # 黄金样例 story.json、真实素材样例、弱模型测试
├── assets/
│   ├── lecture-template/        # 唯一的工程模板（Remotion + React + TS）
│   │   ├── src/                 # 引擎（index / cinema / sfx）、组件、主题、门禁、custom/ 逃生口
│   │   ├── manifests/           # shots.json、字幕、素材清单
│   │   ├── public/              # 字体、背景、音效库 sfx/、真实素材 media/
│   │   └── scripts/             # 可选 TTS 适配、变速后处理
│   └── fonts/                   # LXGW 文楷 Lite（OFL-1.1，不入库，首次使用时自动下载）
├── scripts/                     # make-video、notebook-video CLI、compose / resolve、各门禁、自检；.cmd / .sh 包装
│   └── dev/                     # 维护者工具（音效库构建与调校）
├── references/                  # 作者手册与规格（镜头、版式、主题、音效、字幕、门禁、跨平台）
├── tests/                       # 17 个离线单元测试（背景 / 蓝图 / 运镜 / 字幕 / 素材 / 音效密度 / 门禁 / 评审 …）
└── CHANGELOG.md · CONTRIBUTING.md · NOTICE · DEPENDENCIES.md · LICENSE
```

## 常见问题与限制

- **自带配音吗？** 不自带。默认旁白是静音占位，字幕按 4.5 字/秒定时。要真人声或 TTS：用你自己的音频，或用模板里的 `scripts/tts-openai-compatible.py` 接你自己的 OpenAI 兼容 TTS 端点（密钥只从环境变量读），再用 `scripts/match-timing.py` 重对齐。
- **要用生图模型吗？** 不用，也不支持把生图作为默认路线。画面由组件绘制，需要真实界面时用截图 / 录屏。
- **能做竖屏或 4:3 吗？** 不能。3.2.0 起只有 16:9；3.1.x 的 4:3 / 3:4 画布、`paper` / `sticker` 皮肤与 `--classic` 示例工程已删除，旧工程不再支持。
- **题目需要一张专属的图怎么办？** 照 `src/custom/RequestLane.tsx` 写一个组件，在 `src/custom/index.ts` 注册即可。
- **story.json 草稿和手写场景一样好看吗？** 接近但不等同。草稿版式由 `auto.tsx` 绘制；正式交付建议走手写组件场景。
- **渲染慢吗？** 先用 `--stills` 看静帧（只渲关键帧）；整片缺省按 1920×1080 交付。
- **仓库里有演示视频吗？** 没有。为保持仓库轻量，演示成片不入库；用 `--stills` 在本地出静帧即可看到效果。

## 参与贡献

欢迎 Issue 与 Pull Request，流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。提交前请跑：

```bash
python scripts/validate-skill-consistency.py
python scripts/selftest.py
python scripts/negative-gate-check.py
```

版本记录见 [CHANGELOG.md](CHANGELOG.md)，安全问题见 [SECURITY.md](SECURITY.md)。

## 开源协议

[Apache License 2.0](LICENSE)。所用字体（LXGW 文楷 Lite，OFL-1.1，从官方 Release 自动下载；可用 `NOTEBOOK_VIDEO_FONT_BASE_URL` 指定镜像，或手动放进 `assets/fonts/`）、音效（CC0）与第三方依赖的授权与归属见 [NOTICE](NOTICE) 与 [DEPENDENCIES.md](DEPENDENCIES.md)。

> **关于 Remotion 的许可**：本仓库的 Apache-2.0 只覆盖本仓库的代码。渲染引擎 [Remotion](https://www.remotion.dev/license) 是 **source-available（源码可见）而非开源**许可：
> 个人、非营利组织与 **不超过 3 名员工**的营利公司可免费使用（含商用）；**4 人及以上的营利公司需购买 Remotion 公司许可**。
> 生成的工程里带有 `REMOTION-LICENSE-NOTICE.md`。用 Commons / Openverse 下载的素材各自保留原许可，见工程的 `CREDITS.md`。
