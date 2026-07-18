# Notebook Video

[English](README.md) | [简体中文](README.zh-CN.md)

[![Validate](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml/badge.svg)](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/hyt315/notebook-video)](https://github.com/hyt315/notebook-video/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/hyt315/notebook-video/total)](https://github.com/hyt315/notebook-video/releases)
[![Contributors](https://img.shields.io/github/contributors/hyt315/notebook-video)](CONTRIBUTORS.md)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

把中文科普脚本变成可复现的 2K 手账动画：语义字幕、确定性动效、跨平台渲染与自动质检，一条流程完成。

[下载最新版](https://github.com/hyt315/notebook-video/releases/latest) · [安装为 Agent Skill](#安装为-agent-skill) · [查看 30 秒示例](assets/demo/notebook-video-demo.mp4)

[![Notebook Video 官方工程实际渲染的四场景示例](assets/demo/notebook-video-demo.webp)](assets/demo/notebook-video-demo.mp4)

> 这段预览由仓库里的官方 Remotion 工程真实渲染，不是概念图。公开 MP4 特意移除了配音，避免仓库转发来源不明的第三方音频。

## 它解决什么问题

- **一条生产流程：** 脚本、分镜、TTS 时间数据、语义字幕、动效、渲染和质检不再散落。
- **画面可复现：** 2560×1440 暖白工程手账系统直接固化在代码中，不让不同 AI 每次重新猜风格。
- **中文字幕可读：** 按语义和停顿断句，产品名、数字、单位和固定术语不被拆开。
- **开头真正留人：** 1.5 秒内给出有依据的爆点或矛盾，8 秒内建立问题，正文用证据回收。
- **交付还能继续改：** 可同时产出 H.264/AAC 成片、质检证据和完整 Remotion 源码工程。
- **三平台同一套命令：** macOS、Windows、Linux 共用 Node 启动器，`.sh` 和 `.cmd` 只作为快捷入口。

## 安装为 Agent Skill

必须安装完整仓库；`SKILL.md` 会调用同目录下的 `scripts/`、`references/` 和 `assets/`。

| AI Agent | 用户级安装命令 | 如何调用 |
| --- | --- | --- |
| Codex | `git clone https://github.com/hyt315/notebook-video.git ~/.agents/skills/notebook-video` | 在提示词中写 `$notebook-video`，或通过 `/skills` 选择 |
| Claude Code | `git clone https://github.com/hyt315/notebook-video.git ~/.claude/skills/notebook-video` | 要求 Claude Code 使用 `notebook-video` skill |
| Cursor | `git clone https://github.com/hyt315/notebook-video.git ~/.cursor/skills/notebook-video` | 要求 Cursor Agent 使用 `notebook-video` skill |

如果只想让某个项目使用，可分别克隆到项目里的 `.agents/skills/notebook-video`、`.claude/skills/notebook-video` 或 `.cursor/skills/notebook-video`。新安装后没有被识别时，重启对应 Agent。

Windows PowerShell 示例：

```powershell
git clone https://github.com/hyt315/notebook-video.git "$HOME\.agents\skills\notebook-video"
```

也可以把下面这段话直接交给代码 Agent：

```text
请安装 https://github.com/hyt315/notebook-video 中的 Agent Skill。
保留完整仓库结构，确认 SKILL.md 可见，并执行它自带的验证命令。
```

## 下载

```bash
# HTTPS
git clone https://github.com/hyt315/notebook-video.git

# SSH
git clone git@github.com:hyt315/notebook-video.git

# GitHub CLI
gh repo clone hyt315/notebook-video

# 下载 main 分支 ZIP
curl -L https://github.com/hyt315/notebook-video/archive/refs/heads/main.zip -o notebook-video-main.zip

# 只查看原始 SKILL.md（单文件不是完整安装包）
curl -L https://raw.githubusercontent.com/hyt315/notebook-video/main/SKILL.md -o SKILL.md
```

浏览器直接下载：[最新 Release](https://github.com/hyt315/notebook-video/releases/latest) · [main 分支 ZIP](https://github.com/hyt315/notebook-video/archive/refs/heads/main.zip)

## 五分钟跑通示例

克隆仓库后，先验证技能并创建可编辑工程：

```bash
node scripts/notebook-video.mjs check-deps
node scripts/notebook-video.mjs validate-skill
node scripts/notebook-video.mjs new-project ./my-video
node scripts/notebook-video.mjs prepare-browser ./my-video
```

修改 `my-video/narration.txt`、`storyboard.md`、语义字幕文本和场景对象。按 Provider 中立接口提供 `audio/narration.mp3` 与逐词时间 JSON，再生成字幕、渲染并质检：

```bash
node scripts/notebook-video.mjs build-semantic-captions ./my-video/audio/narration.mp3.json ./my-video/manifests/semantic-caption-lines.txt ./my-video/manifests/caption-cues.json --lead-ms 60
node scripts/notebook-video.mjs render ./my-video ./my-video/renders/final.mp4
node scripts/notebook-video.mjs validate-video ./my-video/renders/final.mp4 EXPECTED_SECONDS ./my-video/renders/contact-sheet.jpg
```

`prepare-browser` 和 `render` 会在需要时自动安装锁定版本的 npm 依赖。Windows 可在 Command Prompt 或 PowerShell 运行相同 Node 命令。受限容器无法读取网卡信息时，在渲染命令前设置 `REMOTION_USE_NETWORK_SHIM=1`。

## 环境要求

- Node.js 20 或更高版本
- Python 3.9 或更高版本
- `PATH` 中可以调用 FFmpeg 与 FFprobe
- 能运行 Remotion/Chrome 的环境

仓库不包含账号、API Key 或私人配置，只保留依赖清单和锁定版本。`node_modules`、渲染浏览器、外部 TTS、缓存和成片都在本机按需生成并从源码包排除。字体和少量程序生成音效是为了跨设备稳定渲染而保留的资产，并附许可证。详见 [DEPENDENCIES.md](DEPENDENCIES.md)。

## 仓库结构

- `SKILL.md`：Agent 的完整操作合同和强制流程。
- `assets/example-project/`：唯一官方 Remotion 渲染引擎。
- `assets/demo/`：由官方引擎真实渲染的公开示例。
- `scripts/`：跨平台工程、字幕、渲染、打包与质检工具。
- `references/`：视觉、时间、开头、性能和兼容性约束。
- `assets/fonts/`：内置字体及原始许可证。

## 验证修改

```bash
node scripts/notebook-video.mjs validate-skill
node scripts/notebook-video.mjs validate-official-example
```

如果修改画面或时间轴，还要渲染受影响片段、查看规定关键帧，并执行 `SKILL.md` 中的视频与字幕检查。没有真实渲染证据，不要修改锁定视觉系统或核心渲染器。

## 许可证与第三方材料

项目代码和技能内容使用 Apache-2.0。Source Han Sans 与 Smiley Sans 继续使用 SIL OFL 1.1。示例音效由程序生成并在工程内注明。Remotion 使用 source-available 的 Remotion License，并非 OSI 定义的开源许可证，部分组织可能需要商业许可。TTS 保持 Provider 中立，仓库不打包任何 TTS 客户端或凭据。

商用前请阅读 [NOTICE](NOTICE)、[DEPENDENCIES.md](DEPENDENCIES.md) 和生成工程里的 Remotion 提示。

## 参与贡献与安全

本项目由 [hyt315](https://github.com/hyt315) 与 ChatGPT 的 Codex 模式协作完成。具体贡献与署名见 [CONTRIBUTORS.md](CONTRIBUTORS.md)。

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)、[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) 和 [CHANGELOG.md](CHANGELOG.md)。安全问题请通过 [GitHub 私密漏洞报告](SECURITY.md) 提交，不要公开发 Issue。
