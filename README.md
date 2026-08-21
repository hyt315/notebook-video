<div align="center">

# 📓 Notebook Video / 手账风教学视频制作

**用代码绘制 2K 中文教学视频：React + SVG + Remotion，帧精确同步 TTS 配音，无需图像生成模型。**

**简体中文 · [English](./README.en.md)**

[![License: MIT](https://img.shields.io/github/license/hyt315/notebook-video)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-1f6feb)](SKILL.md)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](SKILL.md)
[![Remotion](https://img.shields.io/badge/Remotion-4.0-ff6b6b)](https://remotion.dev)

</div>

---

## 📖 这是什么？

做科普视频、手账风动画、产品宣传片、讲解一个概念——**Notebook Video** 是一个 AI Agent Skill，用 **React + TypeScript + Remotion** 绘制 2K 暖白手账风格教学视频。**默认路线是 Lecture Composition**：多区域场景全部用代码绘制（SVG 图表、吉祥物、进度清单、注释贴纸），帧精确同步中文 TTS 词时间，**不依赖图像生成模型**（图像生成是可选的附加项）。输出 H.264/AAC MP4 文件 + 可编辑的 Remotion 项目。

### ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🎬 **代码驱动视频** | React + TypeScript + Remotion，SVG 图表/动画完全由代码控制，AI 可复现一致风格 |
| 📝 **中文 TTS 配音** | 帧精确的 TTS 词时间同步，自动生成字幕、音效；支持多模型平台 |
| 🎨 **Lecture Composition** | 多区域场景（主内容区 + 吉祥物 + 注释贴纸），不依赖图像生成模型，任 AI 环境都能复现 |
| 🚀 **一键项目模板** | `new-project` 命令从模板创建完整 Remotion 项目（lecture 或 classic），即刻进入制作 |
| ✅ **自动化 QA** | 多套验证脚本（字幕同步、分层、语义断句、视觉计划），确保输出质量与一致性 |
| 🔄 **跨平台** | 提供 Windows/macOS/Linux 的脚本（cmd/sh），支持多种模型平台 |

---

## 🚀 快速开始

> ✨ **一句话装进 AI Agent**：把下面这段话直接发给你的 AI 助手，它会自动完成安装——
>
> ```text
> 请安装 notebook-video Skill：把 https://github.com/hyt315/notebook-video 克隆到你的 skills 目录（Claude Code：~/.claude/skills/notebook-video/；Cursor：~/.cursor/skills/；Codex/ChatGPT：项目内 .agent/skills/），并确认 SKILL.md、references/、scripts/ 都在。以后我要做「科普视频 / 手账风动画 / 产品宣传片 / 讲解概念」时，按 SKILL.md 的流程用 Lecture Composition 路线制作。
> ```

然后按平台选择安装方式：

| 平台 | 安装命令 |
|------|----------|
| **Claude Code** | `git clone https://github.com/hyt315/notebook-video.git ~/.claude/skills/notebook-video` |
| **Cursor** | `git clone https://github.com/hyt315/notebook-video.git ~/.cursor/skills/notebook-video` |
| **Codex / ChatGPT** | 项目内 `.agent/skills/notebook-video/`（配合 `agents/openai.yaml`） |
| **通用** | 任意 Agent 的 skills 目录 |

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
├── SKILL.md                     # 技能入口
├── references/                  # 18 个参考手册（视觉系统/构图/字幕/性能/QA 等）
├── scripts/                     # 验证/创建/渲染/打包脚本（cmd + sh 双平台）
├── assets/
│   ├── lecture-template/        # 默认路线模板（纯代码 Lecture Composition）
│   ├── example-project/         # 经典路线示例（含图像生成附加项）
│   └── fonts/                   # 中文字体（思源黑体 + Smiley Sans）
├── agents/openai.yaml
├── LICENSE / NOTICE
├── README.md  /  README.en.md  # 双语说明（本文件为中文）
├── CHANGELOG.md
├── .github/                     # Issue/PR 模板 + CI + Dependabot
└── CONTRIBUTING.md / CODE_OF_CONDUCT.md / SECURITY.md
```

---

## ▶️ 快速使用

初始化项目 → 编辑场景 → 渲染输出：

```bash
# 1. 创建新项目（从模板复制）
node scripts/new-project.mjs my-video

# 2. 进入项目目录
cd my-video

# 3. 安装依赖
npm install

# 4. 预览（浏览器）
npm run dev

# 5. 渲染最终 MP4
npm run render
```

详见 SKILL.md 的完整工作流和 `references/` 中的参考手册。

---

## 🤝 贡献 / 反馈

- 报 Bug / 提建议：用仓库的 Issue 模板
- 贡献：见 [CONTRIBUTING.md](CONTRIBUTING.md)，改动前跑验证脚本
- 漏洞报告：见 [SECURITY.md](SECURITY.md)（私有漏洞报告，勿走公开 Issue）

---

## 📜 License

[MIT](LICENSE) © 2026 hyt315 · Remotion 组件见 [NOTICE](NOTICE)

> 🌏 **English version: [README.en.md](./README.en.md)**