# 📓 Notebook Video / 手账风教学视频制作

<div align="center">

**用代码绘制 2K 中文教学视频：React + SVG + Remotion，帧精确同步 TTS 配音，镜头语言 + 四道质量门禁。**

**Programmatic 2K animated video engine with React, SVG and Remotion — frame-accurate TTS synchronisation, a real shot layer and four quality gates.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/hyt315/notebook-video?sort=semver)](CHANGELOG.md)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-1f6feb)](SKILL.md)
[![Remotion](https://img.shields.io/badge/Remotion-4.0-ff6b6b)](https://remotion.dev)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](SKILL.md)
[![GitHub Stars](https://img.shields.io/github/stars/hyt315/notebook-video?style=social)](https://github.com/hyt315/notebook-video/stargazers)

[English](./README.en.md) | [中文](./README.md)

</div>

***

## 📖 这是什么？

**Notebook Video** 是一个专为 AI Agent 打造的专业级视频制作技能。它用 **React + TypeScript + Remotion** 纯代码绘制 2K 暖白手账风格教学视频，**完全不依赖外部生图大模型**。

这一版（v3.0.0）解决了 AI 做视频最容易踩的两个坑：

- **画面像 PPT**：以前每个场景都是"一张卡片 + 一段文字"，换内容不换结构。现在有**四种构图不同的场景骨架**、**内容→视觉介质的路由**、以及**每镜独立的受限镜头**，并且这些都由门禁强制检查。
- **文字互相压、看不到**：以前只有"文字是否溢出卡片"的检查，元素之间互相遮挡没人管。现在有**渲染期重叠/遮挡门禁**，它会告诉你"哪一帧、哪两句话、压了多少像素"。

同时它保留了原有的强项：词级整帧字幕同步、真字体测量、四套锁定皮肤、零第三方 Python 依赖。

***

## ✨ 核心特性

| 核心模块 | 覆盖功能 | 带来价值 |
| --- | --- | --- |
| 🎥 **镜头层（受限配方 + 出界数学证明）** | 每个镜头声明六个意图之一（建立 / 推近 / 拉远 / 跟随 / 揭示 / 微环绕）＋一个 `anchor`；构建期用纯算术证明 anchor 在每个关键帧都在画面内 | 画面真的会动，而且**不可能把讲解内容推出画面** |
| 🧩 **四种场景骨架** | `Stage`（一个主体演化）/ `Corridor`（对象沿轨道穿站）/ `Split`（双栏对比）/ `Zoom`（整体→聚焦→标注→回整体），**相邻场景不得同骨架、全片 ≥3 种** | 从结构上消灭"四个 PPT 页" |
| 🎯 **内容 → 视觉介质路由** | 控制台窗 / 图表 / 代码补丁 / 大字 / 指标网格 / 概念图；**每支片 ≥3 种介质，每个讲解场景 ≥1 个会随旁白变状态的组件** | 画面不再只有"卡片+文字"一种介质 |
| 🗂 **分镜表 + 解析器** | 分镜表只写"这一镜覆盖哪几句旁白"，帧号由 `resolve-shots.py` 从 TTS 词级时间戳推出 | 改台词不用手改几十处帧号；音效钉帧自动跟随 |
| 📝 **帧精确中文 TTS 同步** | 毫秒级词时间戳 → 语义断句字幕 → 动画节拍；句末标点严格消除 | 告别字幕对不准、音画脱节 |
| ✅ **四道质量门禁（构建期 2 + 渲染期 4）** | 构建期：镜头出界证明、构图与多样性；渲染期：字幕宽度、卡片溢出、**文字重叠与遮挡**、**槽内溢出** | 门禁会**拒绝渲染**，而不是只写规则 |
| 🎨 **四套锁定皮肤** | paper（暖白手账，默认）/ cel（动漫赛璐璐）/ sticker（贴纸）/ flat（扁平几何） | 一套内容，四种气质 |
| 🔒 **背景可读性契约** | 锁定背景位图**保持原样不改**；压在装饰上的内容坐在羽化底托上 | 背景好看，文字也不会被吃掉 |
| 🖼️ **可选生图附加路线** | `--classic` 模板路线支持在关键主场景接入实拍/生成图，并登记来源与授权 | 需要实拍表现力时再开，默认零成本 |

***

## 🎨 视觉成片与画幅

![Notebook Video 成片演示](assets/demo/notebook-video-demo.webp)

▶️ [观看完整演示视频（MP4）](assets/demo/notebook-video-demo.mp4) · 主视觉参考：[hero.png](assets/demo/hero.png)

▶️ [组件库与动效演示（MP4）](assets/demo/notebook-video-components-demo.mp4) — 锁定图标集、代码窗 / 浏览器壳 / 连件 / 清单 / 计数 / 进度条 / 手绘标注、转场、文字动效、物理件与主题皮肤。

**画布**：锁定三种画布 —— 16:9（2560×1440）、4:3（1920×1440）、3:4 竖屏（1440×1920），均为原生 30fps。官方示例片按 **16:9 设计空间**编写；4:3 / 3:4 需要各自的版面重排（**不再用信箱化缩放冒充适配**），在做竖屏时按 `references/canvas-modes.md` 与 `references/portrait-illustration-system.md` 单独编写场景。

***

## 📊 制作全流程

```
[输入：知识主题 / 文案脚本]
        │
  ① 锁内容 ── narration.txt + 语义字幕行（一行一条 cue）
        │
  ② 写分镜表 ── manifests/shots.json
        │    只声明「这一镜覆盖哪几句 cue」＋骨架/介质/活性组件/镜头意图/anchor
        │
  ③ 解析 ────── resolve-shots.py → src/shots.ts（帧号与相机关键帧全部自动生成）
        │
  ④ 写场景 ──── 四种骨架 + 介质组件；每镜用 ShotCamera(keys, anchor) 包裹
        │    元素出现帧绑定到「讲到它的那一句」，入场 22 帧缓动
        │
  ⑤ 构建期门禁 ─ validate-shot-motion.py（P0 必须 0）
        │        validate-composition.py（P0 必须 0）
        │
  ⑥ 渲染 ────── Remotion 渲染 + 响度归一（-16 LUFS / -1.5 dBTP）
        │
  ⑦ 渲染期门禁 + 交付 ─ CaptionFitGate / CardFitGate / OverlapGate / SlotGuard
                        → 2K MP4 + 24 帧接触表 + 可编辑源码 ZIP
```

***

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

```powershell
python scripts/selftest.py
```

***

## ⚙️ 前置依赖

- **Node.js 18+**（Remotion 渲染引擎依赖）；

- **ffmpeg**（抽帧、接触表、响度归一）；做 QA 时需要；

- 首次渲染前使用 `node scripts/notebook-video.mjs check-deps` 做环境体检与 Chromium 内核准备。

常用命令（完整列表见 `--help`）：

```text
node scripts/notebook-video.mjs new-project  ./my-video --style=paper
node scripts/notebook-video.mjs resolve-shots ./my-video
python scripts/validate-shot-motion.py       ./my-video
python scripts/validate-composition.py       ./my-video
node scripts/notebook-video.mjs showcase     ./my-video      # 组件接触表（看图选型）
node scripts/notebook-video.mjs render       ./my-video out.mp4
node scripts/notebook-video.mjs review-frames ./my-video r.mp4 0 570
```

***

## 🔒 质量与安全原则

- **零破坏只读检查**：依赖体检与前置校验默认只读测量，不擅自修改系统环境变量；

- **确定性可复现**：纯代码驱动，所有动画都是帧号的纯函数（禁用 `Math.random`、禁用 CSS 动画与计时器），同一输入在任何机器上渲染一致；

- **门禁优先**：能用算术在构建期证明的，就不留到渲染期；只有需要真实字体/布局测量的才放在浏览器内；

- **全源码完整交付**：成片不仅交付 MP4，同时交付整套干净的 Remotion React 源码包。

***

## ❓ 常见问题 (FAQ)

- **Q：做视频要花钱调用生图 API 吗？**\
  A：不需要。默认路线 100% 用 React + SVG 代码绘制，零生图成本。

- **Q：怎么保证做出来不像 PPT？**\
  A：靠四层，而且都有门禁兜底：① 四种构图不同的骨架，**相邻场景不得同款**；② **每支片 ≥3 种视觉介质**、每个讲解场景至少一个会随旁白变状态的组件；③ 每章至少 3 次运镜（全片按片长配额），景别真的会变；④ 门禁 P0 不为 0 就**拒绝渲染**。

- **Q：怎么保证文字不会互相压、不会被盖住？**\
  A：渲染期有 `OverlapGate`（每 15 帧抽样，检测文字两两重叠与绘制顺序遮挡，用 `Range` 量真实字形矩形）与 `SlotGuard`（槽内内容超出可用宽）——它们会指出"哪一帧、哪两处、压了多少 px"。**有意的重叠**（镜头交接、标题滑变、数值替换）必须显式标 `data-gate-allow`，不允许用白名单掩盖两个不同信息互相压字。

- **Q：字幕为什么不会溢出或被裁？**\
  A：`CaptionFitGate` 在真实渲染浏览器里用**当前画布与当前主题**的真实字号/字重/字距测量每一条字幕；超过安全宽直接拒绝渲染。

- **Q：改动台词要重新对帧吗？**\
  A：不用。分镜表只写"这一镜覆盖哪几句"，帧号、镜头关键帧、音效钉帧都由 `resolve-shots.py` 从 TTS 词级时间戳推出。

- **Q：支持哪些平台？**\
  A：输出标准 H.264/AAC 的 2K MP4，原生适配 B站、YouTube、抖音、小红书、微信视频号。

***

## 📁 文件结构

```
notebook-video/
├── SKILL.md                          # 核心技能定义与制作工作流
├── manifest.json                     # 技能元数据（版本号在此）
├── README.md / README.en.md          # 中英文说明
├── CHANGELOG.md                      # 版本发布记录（当前 v3.0.0）
├── assets/
│   ├── demo/                         # 成片与动图预览
│   ├── lecture-template/             # 官方模板（纯代码路线，含 8 镜示例片）
│   └── example-project/              # 经典路线示例（可选生图附加）
├── scripts/                          # 全部为 Python 标准库 / Node，零第三方依赖
│   ├── notebook-video.mjs            # 跨平台统一启动器（含 showcase 等命令）
│   ├── resolve-shots.py              # 分镜表 → 帧号与相机关键帧
│   ├── validate-shot-motion.py       # 构建期：镜头出界证明 + 运镜配额
│   ├── validate-composition.py       # 构建期：骨架 / 活性组件 / 介质 / 密度
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
shotkit.tsx        镜头层：ShotCamera / 6 意图 / anchor 证明 / 景深 / 底托
stagekit.tsx       骨架 Stage：StageFrame + 状态机 + PhaseRail + Attach + SlotGuard
skeletons.tsx      骨架 Corridor / Split / Zoom
media.tsx          介质：ConsoleWindow / MetricGrid / StampBanner
fxkit.tsx          18 个动效构件（多时钟动效）
kit.tsx            主题无关原子：PillTag / LineIcon / CheckBadge / TYPE
insert.tsx         B 场景插入镜头 + 5 式转场
overlap-gate.tsx   渲染期重叠/遮挡门禁
showcase.tsx       组件接触表（6 页，供 AI 看图选型）
scenes.tsx         场景层（示例片 8 镜；换题材重写这一层）
```

***

## 🤝 参与贡献

欢迎提交 Issue 与 Pull Request！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。如果这个技能对你有帮助，欢迎在 GitHub 上点个 [Star ⭐](https://github.com/hyt315/notebook-video/stargazers)！

***

## 📄 开源协议

本项目采用 [MIT 许可证](LICENSE) 开源。

***

## 📌 版本说明

- **v3.0.0（当前）**：主线版本。已吸收早期 v2.9 / v3.0 两条试验线的优点（受限镜头配方、内容路由、结构化分镜表），并修复了它们各自的问题（v2.9 删掉了强制条款导致成片变空、v3.0 用"限量文本"换稳定性导致表达被压扁）。**v2.9 / v3.0 两条分支与它们的旧 tag 已删除，只保留 `main`。**

***

> 🌏 **English:** **[README.en.md](./README.en.md)**
