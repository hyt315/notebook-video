# 📦 Notebook Video / 手账风教学视频制作

<div align="center">

**把一句话变成一支 2K 中文教学视频：纯代码绘制场景、帧精确对齐配音、镜头语言由门禁托底。**

**Turn one sentence into a 2K Chinese explainer video: code-drawn scenes, frame-accurate TTS sync, camera language enforced by automated gates.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/hyt315/notebook-video?sort=semver)](https://github.com/hyt315/notebook-video/releases)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-1f6feb)](SKILL.md)
[![GitHub Stars](https://img.shields.io/github/stars/hyt315/notebook-video?style=social)](https://github.com/hyt315/notebook-video/stargazers)

[English](README.en.md) | 中文

</div>

---

## 📖 这是什么？

这是一个给 AI 助手用的**视频生产系统**。你说一句「做一支讲 XX 的科普视频」，它负责把这件事从头做到尾：写口播稿 → 生成中文配音 → 取毫秒级词时间戳 → 切成语义断句的字幕 → 排分镜 → 画场景 → 跑门禁 → 渲染出 2K 成片，并同时交付可编辑的 Remotion 源码。

难点从来不是「能不能画出来」，而是画出来**像不像 PPT**、字幕**对不对得齐**、元素**会不会互相压**。这个技能把这三件事都做成**可被自动拒绝的门禁**：骨架必须换、视觉介质必须换、镜头必须真的动、字幕必须用真实字体实测放得下、文字不许互相压——**P0 不为 0 就拒绝渲染**。

画面全部由代码绘制（React + SVG + Remotion），默认**不依赖任何生图模型**；需要「这确实是官方界面 / 官方图表」这类论据时，也可以把真实截图装进实拍素材框。

---

## ✨ 核心特性

| 核心特性 | 功能说明 | 带来价值 |
| --- | --- | --- |
| **一句话成片** | 从主题到 2K MP4：写稿 → 配音 → 词级时间戳 → 语义断句字幕 → 分镜 → 场景 → 门禁 → 渲染 → 接触表验收 | 不用手工排帧、不用逐句对字幕 |
| **四种场景骨架** | `Stage`（一个主体演化）/ `Corridor`（对象沿轨道穿站）/ `Split`（双栏对比）/ `Zoom`（整体→聚焦→标注→回整体）；**相邻场景不得同款、全片 ≥3 种** | 从结构上消灭「四个 PPT 页」 |
| **内容 → 视觉介质路由** | 控制台窗 / 图表 / 代码补丁 / 大字 / 指标网格 / 概念图；**每支片 ≥3 种介质**，每个讲解场景至少一个**会随旁白变状态**的组件 | 画面不再只有「卡片 + 文字」一种介质 |
| **受限镜头语言** | 每镜 6 种意图 + `anchor` 出界证明 + 平移预算；**声明了运镜就必须真的动** | 有运镜但不失控：内容永远不会被推出画面 |
| **八道质量门禁** | 构建期 4：分镜→帧号解析、镜头出界证明、构图与密度、**帧参数名核对**；渲染期 4：字幕宽度、卡片溢出、**文字重叠与遮挡**、槽内溢出 | P0 不为 0 **拒绝渲染**；每次还打覆盖率，**「没报警」与「没运行」能区分开** |
| **实拍素材框** | 真实截图 / 官方图表装进锁定皮肤的墨线框（2.5px 描边 + 硬阴影），可缓慢推近到关键处；素材按 `visual-assets.json` + `asset-manifest.json` **双清单登记**（来源 / 授权 / 是否含文字 / 校验和） | 需要「这确实是官方 / 真实」的论据时用它；能用代码讲清的仍用画的 |
| **帧精确中文 TTS 同步** | 毫秒级词时间戳 → 语义断句 → 动画节拍；句末标点严格消除 | 告别字幕对不准、音画脱节 |
| **四套锁定皮肤** | `paper`（暖白手账，默认）/ `cel`（动漫赛璐璐）/ `sticker`（贴纸）/ `flat`（扁平几何） | 一套内容，四种气质 |
| **背景可读性契约** | 锁定背景位图**保持原样不改**；压在装饰上的内容坐在**半透明**羽化底托上（面板 88%、底托中心 76%） | 不靠「纯白挡板」换可读性，画面才不会变成白底 PPT |

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

## 🔒 安全与隐私原则

- **纯只读 / 先审后改**：依赖体检与前置校验默认只读测量，不擅自修改系统环境变量与系统配置；
- **零 Token 本地运行**：渲染与门禁全部在本机完成，不需要任何在线 API 额度；配音走你自己的 TTS 端点，密钥只从环境变量读取、不落盘；
- **确定性可复现**：纯代码驱动，所有动画都是帧号的纯函数（禁用 `Math.random`、禁用 CSS 动画与计时器）；
- **门禁优先**：能用算术在构建期证明的，就不留到渲染期；只有需要真实字体 / 布局测量的才放在浏览器内；
- **全源码完整交付**：成片不仅交付 MP4，同时交付整套干净的 Remotion React 源码包。

---

## 📥 下载与获取

| 方式 | 命令 / 链接 |
| --- | --- |
| **HTTPS** | `git clone https://github.com/hyt315/notebook-video.git` |
| **SSH** | `git clone git@github.com:hyt315/notebook-video.git` |
| **ZIP** | [下载 ZIP](https://github.com/hyt315/notebook-video/archive/refs/heads/main.zip) |
| **单文件** | `curl -O https://raw.githubusercontent.com/hyt315/notebook-video/main/SKILL.md` |
| **版本记录** | [CHANGELOG.md](CHANGELOG.md) |

---

## 📄 开源协议

本项目采用 [MIT 许可证](LICENSE) 开源。
