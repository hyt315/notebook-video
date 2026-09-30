# Notebook Video / AI 教学视频制作 Skill

<div align="center">

**把讲解目标转成有明确分镜、配音时间线与可复现渲染的教学视频；由创作者选择适合内容的视觉语言。**

**Turn a learning goal into a storyboarded, voice-timed, reproducibly rendered explainer—with visual choices made for the subject, not for quota.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/hyt315/notebook-video?sort=semver)](https://github.com/hyt315/notebook-video/releases)
[![Validate](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml/badge.svg)](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-1f6feb)](SKILL.md)
[![GitHub Stars](https://img.shields.io/github/stars/hyt315/notebook-video?style=social)](https://github.com/hyt315/notebook-video/stargazers)

[English](README.en.md) | 中文

</div>

---

---

## 📖 这是什么？

这是一个给 AI 助手用的**教学视频制作 Skill 与 Remotion 项目模板**：帮助创作者明确学习目标、讲稿、配音/字幕时间线、逐镜教学关系与可见画面承载，再制作、验证并渲染可编辑的视频工程。语音和图片服务由使用者选择；工具不假定某一家生成模型或供应商。

质量不由“镜头动了几次、用了几种组件”来替代。Skill 要求每个旁白 cue 都被一个有明确学习关系、实际可见的视觉载体支持；静态图文可以连贯解释多个 cue，不必逐句增加动画。自动门禁负责检查 cue 覆盖、真实画面节点、时序、字幕适配、重叠、裁切和相机几何等可机械验证事项；教学清晰、舒适度和语义是否说画一致，仍需要完整带声观看并在目标播放尺寸复核。

画面全部由代码绘制（React + SVG + Remotion），默认**不依赖任何生图模型**；需要「这确实是官方界面 / 官方图表」这类论据时，也可以把真实截图装进实拍素材框。

---

---

## ✨ 核心特性

| 核心特性 | 功能说明 | 带来价值 |
| --- | --- | --- |
| **目标驱动的分镜** | 全片记录一个连贯的基础视觉处理；每镜写明所教核心关系与可见画面载体；所有旁白 cue 必须落到讲得清的图文/图表/过程画面 | 不会把“可选风格套路”误解为“可不做视觉教学” |
| **内容适配的视觉方法** | 模板提供 Stage、Corridor、Split、Zoom 等构图助手，以及图表、代码、文字、截图、手绘等组件 | 按知识类型选择；没有骨架轮换、介质数量或组件总数配额 |
| **静态与动态皆可** | 相机静止是合法默认；只有缩放/平移/绕转改变取景时才要求关键内容 anchor 与几何安全证明 | 有意义的变化服务解释；停留时间服务阅读和推理 |
| **可验证的工程门禁** | cue 覆盖和教学声明、关键帧/画幅安全、字幕/卡片适配、文字重叠/遮挡、图形和文字裁切、音频/视频有效性 | 自动化只阻断能可靠判定的错误；覆盖率与视觉效果不伪装成教学效果分数 |
| **帧精确声画时间线** | 字词时间戳驱动字幕与作者声明的视觉事件；同一图像可支持连续多个 cue，无须每句都增加运动 | 保持词与字幕同步，同时尊重阅读和思考停顿 |
| **四种可选基础视觉处理** | `paper`（默认）/ `cel` / `sticker` / `flat`；可按内容局部混合 | 每片要明确选一种连贯基调，但无须把皮肤当作整片不可改的身份 |
| **可复用开源组件** | Python 工具脚本仅用标准库；Remotion 模板以 lockfile 锁定开源运行依赖；新依赖需审核，组件以许可、可复现、真实入帧和解释贡献评估 | 不误读“零依赖”而重复手写成熟组件，也不堆入从未渲染的库 |
| **真实素材来源登记** | 截图、图像、图表等按 manifest 记录来源和授权，并确认它们在成片中可见、支持对应主张 | 真实性与可追溯性，而非装饰素材数量 |

---

---

## 🎨 画幅与验证状态

> 想核对当前版本：在 `assets/lecture-template` 里 `npm install` 后跑 `npm run still`（抽帧）；**要出片请走交付链路** `node scripts/notebook-video.mjs render <工程> <输出>` —— 它会做色彩元数据回写与响度归一，而 `npm run render` **不做**这一步，产出的文件过不了 `validate-video` 的色彩断言。
> 接触表同理：`node scripts/notebook-video.mjs showcase <工程目录>` 现在**直接出交付规格**（2560×1440 / 静音 AAC / 色彩四项回写，与 `assets/demo/` 里那份一致）。`--scale` 只吃十进制字面量 —— `--scale=4/3` 会被 CLI 拒绝，要写 `1.3333333333333333`。

本轮将官方八镜样例分别以 16:9（2560×1440）、4:3（1920×1440）与 3:4（1440×1920）重排并完整静音渲染。每比例均检查了八镜390px接触表、七处切点以及卡片适配、文字重叠、图形裁切和画布边界。该证据只覆盖随仓库提供的官方八镜模板，不代表任意新项目自动适配；也未做真人盲评、真实设备测试或音频/TTS验证。详见 [`references/canvas-modes.md`](references/canvas-modes.md)。

***

---

## 📊 制作全流程

```
[输入：知识主题 / 文案脚本]
        │
  ① 锁内容 ── narration.txt + 语义字幕行（一行一条 cue）
        │
  ② 写分镜表 ── manifests/shots.json
        │    记录 cue 覆盖、核心关系与实际视觉承载；构图/组件/相机意图按需选填
        │
  ③ 解析 ────── resolve-shots.py → src/shots.ts（帧号与相机关键帧全部自动生成）
        │
  ④ 写场景 ──── 按内容选构图与组件；仅在相机移动时声明并验证 anchor
        │    需要逐步揭示时才把视觉事件绑定到 cue；阅读停顿可用静帧
        │
  ⑤ 构建期校验 ─ 检查 cue 覆盖、教学声明及已声明相机移动的几何安全
        │
  ⑥ 渲染 ────── Remotion 渲染 + 响度归一（-16 LUFS / -1.5 dBTP）
        │
  ⑦ 渲染检查 + 交付 ─ 字幕/卡片适配、重叠/遮挡、图形裁切、画布边界
                        （静态镜头有效；可选画面诊断不是教学质量分）
                        → 2K MP4 + 18 页接触表 + 可编辑源码 ZIP
```

***

---

## 🚀 快速开始

这是一个标准的 AI Agent Skill —— 安装到你的 AI 助手后即可直接使用。

### 方式 A：把一句话发给任意 Agent（最推荐、最通用）

把下面这句话直接复制发送给你的 AI 助手，它会自动识别环境并克隆到正确的技能目录：

> 请安装 notebook-video 技能：克隆 `https://github.com/hyt315/notebook-video` 到你的 skills 目录（如 `~/.claude/skills/notebook-video` 或 `~/.agents/skills/notebook-video`），并确认安装成功。以后我要做「科普视频 / 手账风动画 / 产品宣传片 / 讲解概念」时，按 SKILL.md 的工作流制作 2K 视频。

### 方式 B：GitHub CLI 2.90+（一行命令）

```bash
gh skill install hyt315/notebook-video notebook-video --agent claude-code --scope user
```

### 方式 C：多平台手动安装

| 平台 | 用户级安装路径 | 项目级安装路径 |
| --- | --- | --- |
| **Claude Code** | `git clone https://github.com/hyt315/notebook-video.git ~/.claude/skills/notebook-video` | `.claude/skills/notebook-video` |
| **Codex** | `git clone https://github.com/hyt315/notebook-video.git ~/.codex/skills/notebook-video` | `.codex/skills/notebook-video` |
| **Cursor** | `git clone https://github.com/hyt315/notebook-video.git ~/.cursor/skills/notebook-video` | `.cursor/skills/notebook-video` |
| **通用 Agents** | `git clone https://github.com/hyt315/notebook-video.git ~/.agents/skills/notebook-video` | `.agents/skills/notebook-video` |

### 方式 D：本地回归自测（不渲染）

```bash
python scripts/selftest.py
```

---

---

## 📚 端到端实战演示

假设你要做一支《某个新模型值不值得切》的 3 分钟科普片。全程四条命令、零手改帧号：

```text
# ① 建工程（复制模板，锁定皮肤）
node scripts/notebook-video.mjs new-project ./my-video --style=cel

# ② 写旁白与字幕行（两份文件必须逐字互相还原；数字写成中文读法）
#    narration.txt          每行 = 一个语音段（= 一章）
#    manifests/semantic-caption-lines.txt   字幕行，拼接后等于旁白原文
python <模板>/scripts/tts-openai-compatible.py ./my-video     # 配音 + 词级时间戳
python <模板>/scripts/speed-post.py ./my-video 1.10           # 定速（不改音高，全时间轴同步缩放）
node scripts/notebook-video.mjs build-semantic-captions audio/narration.mp3.json manifests/semantic-caption-lines.txt manifests/caption-cues.json

# ③ 写分镜表（只写"这一镜覆盖哪几句旁白"，绝不写帧号）
#    manifests/shots.json → resolve-shots.py 推出帧号与相机关键帧

# ④ 跑门禁 → 渲染
python scripts/validate-frame-props.py ./my-video     # 帧参数名（最高频的静默事故）
python scripts/validate-shot-motion.py ./my-video     # 出界证明 / 平移预算 / 运镜配额
python scripts/validate-composition.py ./my-video     # 骨架 / 介质 / 枚举 / 节奏
python scripts/validate-audio-levels.py ./my-video    # 音效素材不能录太轻
node scripts/notebook-video.mjs render ./my-video out.mp4
```

渲染期还会自动拦下"文字互相压""卡片内容被裁""字幕超宽"——**P0 不为 0 就不会出片**，
而不是等你逐帧看图时才发现。

---

## ⚙️ 前置依赖

- **Node.js 18+**（Remotion 渲染引擎依赖）
- **ffmpeg**（抽帧、接触表、响度归一；做 QA 时需要）
- 首次渲染前用 `node scripts/notebook-video.mjs check-deps` 做环境体检与 Chromium 内核准备

常用命令（完整列表见 `--help`）：

```text
node scripts/notebook-video.mjs new-project   ./my-video --style=paper
node scripts/notebook-video.mjs resolve-shots ./my-video
python scripts/validate-frame-props.py        ./my-video
python scripts/validate-shot-motion.py        ./my-video
python scripts/validate-composition.py        ./my-video
node scripts/notebook-video.mjs showcase      ./my-video     # 组件接触表（看图选型）
node scripts/notebook-video.mjs render        ./my-video out.mp4
node scripts/notebook-video.mjs review-frames ./my-video r.mp4 0 570
```

---

---

## 🔒 安全与隐私原则

- **纯只读 / 先审后改**：依赖体检与前置校验默认只读测量，不擅自修改系统环境变量与系统配置；
- **零 Token 本地运行**：渲染与门禁全部在本机完成，不需要任何在线 API 额度；配音走你自己的 TTS 端点，密钥只从环境变量读取、不落盘；
- **确定性可复现**：纯代码驱动，所有动画都是帧号的纯函数（禁用 `Math.random`、禁用 CSS 动画与计时器）。**口径要说清**：**still / PNG 逐字节可复现**（同一帧渲两次哈希一致，接触表就是这么验的）；**长片段 mp4 不保证逐字节**——x264 在长片段上的多线程/前瞻决策会让连渲两次的 md5 不同，实测像素差只落在边缘少数点（最大 76、平均 0.12、95.2% 字节相同），属编码层噪声而非内容差异；
- **门禁优先**：能用算术在构建期证明的，就不留到渲染期；只有需要真实字体 / 布局测量的才放在浏览器内；
- **全源码完整交付**：成片不仅交付 MP4，同时交付整套干净的 Remotion React 源码包。

---

---

## 📥 下载与获取

| 方式 | 命令 / 链接 |
| --- | --- |
| **HTTPS** | `git clone https://github.com/hyt315/notebook-video.git` |
| **SSH** | `git clone git@github.com:hyt315/notebook-video.git` |
| **ZIP** | [下载 ZIP](https://github.com/hyt315/notebook-video/archive/refs/heads/main.zip) |
| **单文件** | `curl -O https://raw.githubusercontent.com/hyt315/notebook-video/main/SKILL.md` |
| **版本记录** | `CHANGELOG.md` |

---

---

## 📁 文件结构

```
notebook-video/
├── SKILL.md                          # 核心技能定义与制作工作流
├── manifest.json                     # 技能元数据（版本号在此）
├── README.md / README.en.md          # 中英文说明
├── CHANGELOG.md                      # 版本发布记录（当前 v3.1.3）
├── assets/
│   ├── demo/                         # 成片与动图预览
│   ├── lecture-template/             # 官方模板（纯代码路线，含 8 镜示例片）
│   └── example-project/              # 经典路线示例（可选生图附加）
├── scripts/                          # 全部为 Python 标准库 / Node（本目录不引第三方包）
│   ├── notebook-video.mjs            # 跨平台统一启动器（含 showcase 等命令）
│   ├── resolve-shots.py              # 分镜表 → 帧号与相机关键帧
│   ├── validate-shot-motion.py       # 构建期：已声明相机移动的几何安全
│   ├── validate-composition.py       # 构建期：cue 覆盖、教学关系与视觉承载
│   ├── validate-caption-sync.py      # 字幕与 TTS 词边界一致
│   ├── validate-semantic-breaks.py   # 保护短语不被切断
│   ├── selftest.py                   # 端到端回归自测
│   └── …                             # TTS 对齐、重定时、打包、依赖体检等
└── references/                       # 按需加载的规范与手册
    ├── scene-authoring.md            # ★ 场景编写说明书（照着抄）
    ├── shot-language.md              # 镜头意图、缩放预算、出界证明
    ├── scene-skeletons.md            # 四种骨架与分镜表结构
    ├── media-routing.md              # 内容→介质路由、A/B 场景、背景契约
    ├── composition-gate.md           # 全部门禁的判据与修法
    ├── motion-design.md              # 多时钟动效六律
    ├── theme-*.md / visual-system.md # 四套皮肤契约
    └── …                             # TTS、字幕、画布、性能与跨平台手册
```

模板内的源码分层（`assets/lecture-template/src/`）：

```
index.tsx          引擎：画布/字幕/章节卡/资产门/渲染期门禁 + 镜头边界交接
shotkit.tsx        可选相机辅助：静态/受限移动、条件式 anchor 证明、景深 / 底托
stagekit.tsx       可选 Stage 布局助手、状态与进度表达
skeletons.tsx      骨架 Corridor / Split / Zoom
media.tsx          介质：ConsoleWindow / MetricGrid / StampBanner
fxkit.tsx          9 个动效构件（多时钟动效）
toolkit.tsx       修辞工具件：Callout(画圈标注)/Checklist(清单)/JumpInText(逐字跳入) …… 可直接 import
│   └── components/      封装组件层：Accordion/Tabs/HighlightCode/Chart/StatRow/GlowFrame/PathDraw/FitTextBox …… 场景从这里 import
kit.tsx            主题无关原子：PillTag / LineIcon / CheckBadge / TYPE
insert.tsx         B 场景插入镜头 + 3 式转场（cut / handoff / reveal）
overlap-gate.tsx   渲染期重叠/遮挡门禁（事件帧抽样：镜头边界/节拍/相机关键帧）
clipping-gate.tsx  渲染期图形被裁门禁（SVG 图元越出会裁切的祖先）
canvas-bounds-gate.tsx 渲染期画布越界门禁（含文字的叶元素，墨迹 rect 越出画布；接触表 block、片子 warn）
fill-gate.tsx      可选的遗留画面诊断，不强制铺满画布
showcase.tsx       组件接触表（18 页，供 AI 看图选型）
scenes.tsx         场景层（示例片 8 镜；换题材重写这一层）
```

***

---

## ❓ 常见问题 (FAQ)

- **Q：做视频要花钱调用生图 API 吗？**\
  A：不需要。默认路线 100% 用 React + SVG 代码绘制，零生图成本。

- **Q：那能用开源的 UI 组件库吗？**\
  A：能，而且鼓励。被禁的只有「按次付费、结果不可复现」的生成式模型；开源库随模板一次 `npm install` 装好就能直接 `import`，不需要额外授权。边界见 `references/dependency-policy.md`。

- **Q：怎么避免只是把幻灯片变成视频？**\
  A：从学习目标与每条 cue 的画面承载开始：镜头表要说明核心关系和实际可见的视觉载体，再用真实分镜与带声成片检查它是否讲得通。需要对比、流程图或逐步推导时才选择相应构图；不强制骨架轮换、三种介质或每镜运动。模板门禁能抓技术问题，不能仅凭一个自动分数证明“不是 PPT”或证明教学有效。

- **Q：自动检查能抓哪些画面问题？**\
  A：实际运行的 `OverlapGate` 检查抽样帧中的文字重叠/遮挡，`ClippingGate` 与 `CanvasBoundsGate` 查图形/文字裁切，`CaptionFitGate` 检查字幕适配；具体范围由检查器覆盖率报告说明。`validate-shot-motion.py` 对声明的相机移动检查 anchor 与画布边界。遗留 `FillGate`、`SlotGuard` 和 `validate-motion-gaps` 不是教学质量门禁，也不要求画面填满或持续运动。自动检查不能替代全片观看。

- **Q：字幕为什么不会溢出或被裁？**\
  A：`CaptionFitGate` 在真实渲染浏览器里用**当前画布与当前主题**的真实字号/字重/字距测量每一条字幕；超过安全宽直接拒绝渲染。

- **Q：改动台词要重新对帧吗？**\
  A：不用。分镜表只写"这一镜覆盖哪几句"，帧号、镜头关键帧、音效钉帧都由 `resolve-shots.py` 从 TTS 词级时间戳推出。

- **Q：静止画面会被判不合格吗？**\
  A：不会。静止的图表、示意图、公式或文字画面，只要能清楚承载当前 cue 并留出理解时间，就是有效选择。相机不动不等于画面没有视觉内容。

- **Q：四种视觉处理都必须轮流用吗？**\
  A：不必。项目需为整片选定连贯的基调，`paper`、`cel`、`sticker`、`flat` 是可选基础方案；局部组件仍按内容需要选择和调整，不按组件数达标。

- **Q：当前哪些画幅经过验证？**\
  A：官方八镜样例已分别按 16:9、4:3 和 3:4 布局、静音渲染并检查接触表与画面边界、重叠和裁切；这只验证随仓库提供的样例，不代表任意新项目自动适配。未做盲评或真实设备测试，也未验证音频/TTS。

- **Q：支持哪些平台？**\
  A：输出标准 H.264/AAC 的 2K MP4，原生适配 B站、YouTube、抖音、小红书、微信视频号。

***

---

## 🤝 参与贡献

欢迎提交 Issue 与 Pull Request！详见 `CONTRIBUTING.md`。如果这个技能对你有帮助，欢迎在 GitHub 上点个 [Star ⭐](https://github.com/hyt315/notebook-video/stargazers)！

***

---

## 📄 开源协议

本项目采用 Apache License 2.0 开源（协议全文见仓库根 LICENSE 文件）。随包第三方素材（LXGW 楷体正文、音效、Remotion 依赖、TTS 提供方等）的授权与归属见 NOTICE 文件，第三方依赖清单见 `DEPENDENCIES.md`。
