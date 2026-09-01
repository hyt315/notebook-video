<div align="center">

# 📓 Notebook Video / 手账风教学视频制作

**用代码绘制 2K 中文教学视频：React + SVG + Remotion，帧精确同步 TTS 配音，无需图像生成模型。**

**简体中文 · [English](./README.en.md)**

[![License: MIT](https://img.shields.io/github/license/hyt315/notebook-video)](LICENSE)
[![Release](https://img.shields.io/github/v/release/hyt315/notebook-video?sort=semver)](https://github.com/hyt315/notebook-video/releases)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-1f6feb)](SKILL.md)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](SKILL.md)
[![Remotion](https://img.shields.io/badge/Remotion-4.0-ff6b6b)](https://remotion.dev)
[![Stars](https://img.shields.io/github/stars/hyt315/notebook-video?style=social)](https://github.com/hyt315/notebook-video/stargazers)

</div>

---

## 📖 这是什么？

做科普视频、手账风动画、产品宣传片、讲解一个概念——**Notebook Video** 是一个 AI Agent Skill，用 **React + TypeScript + Remotion** 绘制 2K 暖白手账风格教学视频。**默认路线是 Lecture Composition**：多区域场景全部用代码绘制（SVG 图表、吉祥物、进度清单、注释贴纸），帧精确同步中文 TTS 词时间，**不依赖图像生成模型**（图像生成是可选的附加项）。输出 H.264/AAC MP4 + 可编辑的 Remotion 项目源码包。

### ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🎬 **代码驱动视频** | React + TypeScript + Remotion 绘制，SVG 图表/动画完全由代码控制，任何 AI 环境都能复现一致风格 |
| 📝 **中文 TTS 配音** | 帧精确的 TTS 词时间同步，自动生成语义字幕与音效，支持多模型平台 |
| 🎨 **Lecture Composition 默认路线** | 多区域场景（主内容区 + 吉祥物 + 注释贴纸），纯代码绘制，不依赖图像生成 |
| 🖼️ **图像生成可选附加** | 需要实拍感主视觉时，可为具体主场景生成图像（Visual Director 路线，`--classic` 模板） |
| 📐 **三种画布** | 16:9（2560×1440）、4:3（1920×1440）、3:4 竖屏，移动端可读性字号下限内置 |
| ✅ **自动化 QA** | 字幕宽度实测门（CaptionFitGate）、分层校验、语义断句校验、视觉计划校验等多道质量门 |
| 🔄 **跨平台统一命令** | 同一个 Node 启动器在 macOS Terminal / Windows CMD / PowerShell 下行为一致 |

---

## 📚 演示示例

![Notebook Video 成片演示](assets/demo/notebook-video-demo.webp)

▶️ [观看完整演示视频（MP4）](assets/demo/notebook-video-demo.mp4) · 主视觉参考：[hero.png](assets/demo/hero.png)

**三种画幅版本**（同一工程，`CANVAS` 开关切换）：

| 画幅 | 预览 | 下载 |
| --- | --- | --- |
| 16:9 横屏（默认） | [![16:9](assets/demo/notebook-video-demo.webp)](assets/demo/notebook-video-demo.mp4) | [notebook-video-demo.mp4](assets/demo/notebook-video-demo.mp4) |
| 4:3 竖屏友好 | [![4:3](assets/demo/notebook-video-demo-43.webp)](assets/demo/notebook-video-demo-43.mp4) | [notebook-video-demo-43.mp4](assets/demo/notebook-video-demo-43.mp4) |
| 3:4 竖屏（抖音） | [![3:4](assets/demo/notebook-video-demo-34.webp)](assets/demo/notebook-video-demo-34.mp4) | [notebook-video-demo-34.mp4](assets/demo/notebook-video-demo-34.mp4) |

> 以上即 lecture-template 路线的真实产出风格：暖白手账底、代码绘制的多区域场景、词级同步字幕。

---

## 🚀 快速开始

> ✨ **一句话装进 AI Agent**：把下面这段话直接发给你的 AI 助手，它会自动完成安装——
>
> ```text
> 请安装 notebook-video Skill：把 https://github.com/hyt315/notebook-video 克隆到你的 skills 目录（Claude Code：~/.claude/skills/notebook-video/；Cursor：~/.cursor/skills/；Codex/ChatGPT：项目内 .agent/skills/），并确认 SKILL.md、references/、scripts/ 都在。以后我要做「科普视频 / 手账风动画 / 产品宣传片 / 讲解概念」时，按 SKILL.md 的流程用 Lecture Composition 路线制作。
> ```

### 安装命令（一行）

| 平台 | 安装命令 |
|------|----------|
| **Claude Code** | `git clone https://github.com/hyt315/notebook-video.git ~/.claude/skills/notebook-video` |
| **Codex** | `git clone https://github.com/hyt315/notebook-video.git ~/.codex/skills/notebook-video` |
| **Cursor** | `git clone https://github.com/hyt315/notebook-video.git ~/.cursor/skills/notebook-video` |

### Skills 目录路径说明

| 平台 | 个人级（全局） | 项目级 |
|------|---------------|--------|
| **Claude Code** | `~/.claude/skills/` | `.claude/skills/`（项目根目录） |
| **Codex** | `~/.codex/skills/` | `.codex/skills/`（项目根目录） |
| **Cursor** | `~/.cursor/skills/` | `.cursor/skills/` 或 `.agents/skills/`（项目根目录） |

> 每个 Skill 都要有自己的文件夹，不要把 SKILL.md 直接扔进 skills/ 根目录。

---

## 💬 触发方式

对 AI 说以下任意一类话，即会触发本技能：

- 「做科普视频」「做手账风视频」「做定格动画」
- 「做一个 AI 视频」「产品宣传片」
- 「介绍一个概念」「讲解产品/技能」
- 「制作 30 秒到几分钟的视频」「网站动画转 MP4」
- 「加中文配音/字幕/音效」「快速生成 2K 视频」

## ⚙️ 前置条件

- **Node.js**（运行统一启动器与 Remotion 渲染）
- 浏览器内核（首次渲染前用 `prepare-browser` 自动准备 Chromium）
- 中文 TTS 服务（任选支持的模型平台）
- 不确定依赖是否齐全？跑一次体检：`node "<SKILL_DIR>/scripts/notebook-video.mjs" check-deps`

## 📦 输出交付物

一次完整制作会交付（除非你要求精简）：

1. 旁白文稿 + 时间码分镜脚本
2. 视觉计划（每个场景标注 `image-text` / `pure-text` / `pure-graphic`）
3. 语义分段清单（含图层与出场契约）
4. `visual-assets.json`（每张位图的来源、提示词摘要、裁剪策略与版权）
5. 中文旁白 + 词级时间 JSON
6. 单行语义字幕 cues + 受保护短语清单
7. 交付画布 H.264/AAC MP4（2560×1440 或 1920×1440）
8. 长片附 24 帧 contact sheet 与运动检查
9. 可编辑源码 ZIP（含字体、许可证、音频与清单）

---

## 📥 下载 / 安装

```bash
# HTTPS
git clone https://github.com/hyt315/notebook-video.git

# SSH
git clone git@github.com:hyt315/notebook-video.git

# GitHub CLI
gh repo clone hyt315/notebook-video

# ZIP
# https://github.com/hyt315/notebook-video/archive/refs/heads/main.zip

# 单文件（仅 SKILL.md）
curl -O https://raw.githubusercontent.com/hyt315/notebook-video/main/SKILL.md
```

---

## 📁 文件结构（核心）

```
notebook-video/
├── SKILL.md                     # 技能入口（11 步生产工作流）
├── references/                  # 18 个参考手册（视觉系统/构图/字幕/性能/QA/跨平台等）
├── scripts/
│   └── notebook-video.mjs       # 统一 Node 启动器（check-deps/new-project/render/package…）
├── assets/
│   ├── lecture-template/        # 默认路线模板（纯代码 Lecture Composition，30 秒成片）
│   ├── example-project/         # 经典路线示例（Visual Director，含图像附加项）
│   └── fonts/                   # 中文字体（思源黑体 + Smiley Sans，含许可证）
├── agents/openai.yaml
├── LICENSE / NOTICE
├── README.md  /  README.en.md  # 双语说明（本文件为中文）
├── CHANGELOG.md
├── .github/                     # Issue/PR 模板 + CI(validate) + Dependabot
└── CONTRIBUTING.md / CODE_OF_CONDUCT.md / SECURITY.md
```

---

## ▶️ 快速使用

所有操作通过**统一 Node 启动器**完成（macOS Terminal / Windows CMD / PowerShell 通用）：

```bash
# 0. 依赖体检 + 技能自检
node "<SKILL_DIR>/scripts/notebook-video.mjs" check-deps
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-skill

# 1. 创建新项目（默认 lecture 模板；--classic 为图像附加路线）
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project ./notebook-video-project

# 2. 准备浏览器内核（首次渲染前）
node "<SKILL_DIR>/scripts/notebook-video.mjs" prepare-browser ./notebook-video-project

# 3. 按 SKILL.md 的 11 步工作流制作（锁内容 → 导视觉 → TTS → 分层 → 动画 → 渲染 → 校验）

# 4. 打包交付源码 ZIP
node "<SKILL_DIR>/scripts/notebook-video.mjs" package ./notebook-video-project ./source.zip
```

两条模板路线：

| 路线 | 命令 | 适用 |
|------|------|------|
| **Lecture（默认）** | `new-project ./dir` | 纯代码绘制，多区域构图，不依赖图像生成 |
| **Classic** | `new-project ./dir --classic` | 图文标注 + 物理插槽，接受图像生成附加项时使用 |

---

## 🤝 贡献 / 反馈

- 报 Bug / 提建议：用仓库的 Issue 模板
- 贡献：见 [CONTRIBUTING.md](CONTRIBUTING.md)，改动前跑 `validate-skill` 与相关验证脚本
- 漏洞报告：见 [SECURITY.md](SECURITY.md)（私有漏洞报告，勿走公开 Issue）

---

## 📜 License

[MIT](LICENSE) © 2026 hyt315 · Remotion 组件许可见 [NOTICE](NOTICE)

> 🌏 **English version: [README.en.md](./README.en.md)**