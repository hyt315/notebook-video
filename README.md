# 📓 Notebook Video / 手账风教学视频制作

<div align="center">

**用代码绘制 2K 中文教学视频：React + SVG + Remotion，帧精确同步 TTS 配音，多画布比例适配。**

**Programmatic 2K animated video engine with React, SVG and Remotion — frame-accurate TTS synchronization with zero image model dependencies.**

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

做科普视频、手账风动画、产品宣传片、讲解一个技术概念——**Notebook Video** 是一个专为 AI Agent 打造的专业级视频制作技能。它使用 **React + TypeScript + Remotion** 纯代码绘制 2K 暖白手账风格教学视频。

**默认路线是 Lecture Composition（多区域纯代码排版）**：所有 SVG 图表、吉祥物插画、进度清单与注释贴纸全部由代码高保真绘制，帧精确同步中文 TTS 配音词时间，**完全不依赖外部生图大模型**。输出高质量 H.264/AAC MP4 以及完整可复用的 Remotion 源码工程包。

***

## ✨ 核心特性

| 核心模块                         | 覆盖功能                                                       | 带来价值                       |
| ---------------------------- | ---------------------------------------------------------- | -------------------------- |
| 🎬 **代码驱动全景渲染**              | React + TypeScript + Remotion 绘制，SVG 图表与动效完全由代码精确控制        | 任何 AI 环境均能 100% 稳定复现统一视觉风格 |
| 📝 **帧精确中文 TTS 同步**          | 毫秒级对齐 TTS 词级时间戳，自动生成语义断句字幕、音效与动画节拍                         | 告别字幕对不准、音画脱节的剪辑烦恼          |
| 📐 **三大主流画布比例**              | 16:9（2560×1440 讲座横屏）、4:3（1920×1440 经典）、3:4（1080×1440 竖屏社媒） | 同一套代码一键切换画幅，移动端自适应字号下限保障   |
| 🎨 **Lecture 纯代码主路线**        | 主内容看板 + 吉祥物插画 + 注释贴纸多区域排版，纯 SVG 矢量绘制                       | 零 API 生图消耗，秒级渲染，排版极度工整     |
| 🖼️ **Visual Director 附加路线** | 支持在关键主场景接入实拍或定制图像生成（`--classic` 模板路线）                      | 兼顾纯代码严谨性与实拍艺术表现力           |
| ✅ **全自动多重 QA 门禁**            | 字幕宽度实测门（CaptionFitGate）、分层布局校验、断句校验等多道自动化门禁                | 自动化确保 0 字幕溢出、0 视觉重叠、0 渲染崩溃 |

***

## 🎨 视觉成片与画幅演示

![Notebook Video 成片演示](assets/demo/notebook-video-demo.webp)

▶️ [观看完整演示视频（MP4）](assets/demo/notebook-video-demo.mp4) · 主视觉参考：[hero.png](assets/demo/hero.png)

### 默认画布：16:9 横屏

| 画布比例             | 分辨率            | 视频预览                                                                                 | 适用场景                       |
| ---------------- | -------------- | ------------------------------------------------------------------------------------ | -------------------------- |
| **16:9 横屏** (默认) | 2560×1440 (2K) | [![16:9](assets/demo/notebook-video-demo.webp)](assets/demo/notebook-video-demo.mp4) | B站 / YouTube / 讲座演练 / 官网宣传 |

***

## 📊 视频制作 11 步全流程架构

```
[输入: 用户提供知识主题 / 文案脚本]
                       │
     [Step 1~2: 锁定内容与视觉构思] ──> 确定大纲、分镜结构与画布比例
                       │
     [Step 3: 词级 TTS 配音生成] ───> 获取精准毫秒级词时间戳
                       │
     [Step 4~5: 场景分层与代码绘制] ─> 编写 React 组件与 SVG 矢量图表
                       │
     [Step 6~7: 动画节拍与多画幅适配] -> 帧精确对齐配音波形与字幕
                       │
     [Step 8: 自动化 QA 门禁扫描] ──> CaptionFitGate / 溢出与分层校验
                       │
     [Step 9~11: Remotion 渲染与交付] -> 输出 2K MP4 + 完整源码 ZIP
```

***

## 🚀 快速开始

这是一个标准的 AI Agent Skill —— 安装到你的 AI 助手后即可直接使用。

### 方式 A：把一句话发给任意 Agent（最推荐、最通用）

把下面这句话直接复制发送给你的 AI 助手，它会自动识别环境并克隆到正确的技能目录：

> 请安装 notebook-video 技能：克隆 `https://github.com/hyt315/notebook-video` 到你的 skills 目录（如 `~/.claude/skills/notebook-video` 或 `~/.agents/skills/notebook-video`），并确认安装成功。以后我要做「科普视频 / 手账风动画 / 产品宣传片 / 讲解概念」时，按 SKILL.md 的 11 步工作流制作 2K 视频。

### 方式 B：GitHub CLI 2.90+（一行命令）

```bash
gh skill install hyt315/notebook-video notebook-video --agent claude-code --scope user
```

### 方式 C：多平台手动安装

| 平台              | 用户级安装路径                                                                                  | 项目级安装路径                         |
| --------------- | ---------------------------------------------------------------------------------------- | ------------------------------- |
| **Claude Code** | `git clone https://github.com/hyt315/notebook-video.git ~/.claude/skills/notebook-video` | `.claude/skills/notebook-video` |
| **Codex**       | `git clone https://github.com/hyt315/notebook-video.git ~/.codex/skills/notebook-video`  | `.codex/skills/notebook-video`  |
| **Cursor**      | `git clone https://github.com/hyt315/notebook-video.git ~/.cursor/skills/notebook-video` | `.cursor/skills/notebook-video` |
| **通用 Agents**   | `git clone https://github.com/hyt315/notebook-video.git ~/.agents/skills/notebook-video` | `.agents/skills/notebook-video` |

### 方式 D：本地运行回归自测

```powershell
python scripts/selftest.py
```

***

## ⚙️ 前置依赖与极速体检

- **Node.js 18+**（Remotion 渲染引擎依赖）；

- 首次渲染前使用 `node scripts/notebook-video.mjs check-deps` 进行环境依赖自动检测与 Chromium 内核准备。

***

## 🔒 质量与安全原则

- **零破坏只读检查**：依赖体检与前置校验默认只读测量，不擅自修改系统环境变量；

- **确定性可复现**：纯代码驱动，杜绝大模型偶发随机性导致的画面崩坏；

- **全源码完整交付**：成片不仅交付 MP4，同时交付整套干净的 Remotion React 源码包。

***

## 📥 下载与获取

| 方式                 | 命令 / 链接                                                                           |
| ------------------ | --------------------------------------------------------------------------------- |
| **HTTPS**          | `git clone https://github.com/hyt315/notebook-video.git`                          |
| **SSH**            | `git clone git@github.com:hyt315/notebook-video.git`                              |
| **GitHub CLI**     | `gh repo clone hyt315/notebook-video`                                             |
| **ZIP 压缩包**        | [下载 ZIP](https://github.com/hyt315/notebook-video/archive/refs/heads/main.zip)    |
| **Tar 归档**         | [下载 Tar](https://github.com/hyt315/notebook-video/archive/refs/heads/main.tar.gz) |
| **单文件 (SKILL.md)** | `curl -O https://raw.githubusercontent.com/hyt315/notebook-video/main/SKILL.md`   |

***

## 📁 文件结构

```
notebook-video/
├── SKILL.md                          # 核心技能定义与 11 步视频工作流
├── README.md                         # 中文说明文档
├── README.en.md                      # 英文说明文档
├── CHANGELOG.md                      # 版本发布记录
├── LICENSE                           # MIT 开源许可证
├── .gitignore                        # Git 忽略规则
├── CONTRIBUTING.md                   # 社区贡献指南
├── CODE_OF_CONDUCT.md                # 行为准则
├── SECURITY.md                       # 安全策略
├── SUPPORT.md                        # 支持渠道
├── manifest.json                     # 技能元数据清单
├── agents/                           # 多 Agent 平台元数据
├── assets/demo/                      # 视频与动图预览资产
├── scripts/
│   ├── notebook-video.mjs            # 跨平台 Node 统一启动器
│   ├── validate-official-example.py  # 官方示例一致性验证器
│   └── selftest.py                   # 自动化回归自测脚本
└── references/                       # 视觉设计、TTS 节拍与 Remotion 手册
```

***

## ❓ 常见问题 (FAQ)

- **Q: 制作视频必须花钱调用生图 AI API 吗？**\
  A: 完全不需要。默认的 Lecture Composition 路线 100% 采用 React + SVG 代码绘制多区域场景，零生图成本。

- **Q: 为什么字幕不会出现遮挡或换行截断？**\
  A: 技能内置 `CaptionFitGate` 真实测量门，在渲染前精确计算每个文字的像素级宽度，彻底杜绝溢出。

- **Q: 渲染出的视频支持哪些平台？**\
  A: 输出标准 H.264/AAC 编码的 2K MP4 视频，原生支持 B站、YouTube、抖音、小红书、微信视频号全平台。

***

## 🤝 参与贡献

欢迎提交 Issue 与 Pull Request！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。如果这个技能对你有帮助，欢迎在 GitHub 上点个 [Star ⭐](https://github.com/hyt315/notebook-video/stargazers)！

***

## 📄 开源协议

本项目采用 [MIT 许可证](LICENSE) 开源。

***

> 🌏 **English:** **[README.en.md](./README.en.md)**

