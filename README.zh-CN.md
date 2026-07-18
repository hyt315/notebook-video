# Notebook Video

[English](README.md) | [简体中文](README.zh-CN.md)

[![Validate](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml/badge.svg)](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/hyt315/notebook-video)](https://github.com/hyt315/notebook-video/releases)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

一个采用 Apache-2.0 许可证、面向中文科普视频的 Agent Skill 与 Remotion 工程模板。它把脚本、Provider 中立的中文 TTS 输入、语义字幕、2K/30fps 渲染、自动质检和可编辑源码包放在同一条跨平台流程中。字体、音效和 Remotion 继续遵循各自许可证。

## 核心能力

- 原生输出 2560×1440、30fps、H.264/AAC 视频。
- 固定暖白工程手账视觉系统，避免每次由 AI 重新猜风格。
- 中文配音、逐词时间数据、语义字幕和不可拆分短语保护。
- macOS、Windows、Linux 共用一个 Node 启动器；`.sh` 和 `.cmd` 只是快捷入口。
- 自动检查黑帧、字幕溢出、时间同步、图层退出、响度和输出格式。
- 开头 1.5 秒先给真实爆点或矛盾，8 秒内建立悬念，并在后文用证据回收。

## 环境要求

- Node.js 20 或更高版本
- Python 3.9 或更高版本
- `PATH` 中可调用 FFmpeg 与 FFprobe
- 能运行 Remotion/Chrome 的环境

仓库不包含账号、API Key 或私人配置。所有本地凭据都应保存在仓库之外。

仓库只保留依赖清单和锁定版本，不上传已经安装的依赖。`node_modules`、渲染浏览器、外部 TTS 工具、缓存和成片都会在本机按需下载或生成，并从源码包排除。字体和少量程序生成音效是有意保留的运行资产：它们用于保证不同电脑渲染一致，并附带许可证。详见 [DEPENDENCIES.md](DEPENDENCIES.md)。

## 快速开始

```bash
node scripts/notebook-video.mjs check-deps
node scripts/notebook-video.mjs validate-skill
node scripts/notebook-video.mjs new-project ./my-video
node scripts/notebook-video.mjs prepare-browser ./my-video
```

`prepare-browser` 会在需要时自动执行锁定版本的 `npm ci`；直接运行 `render` 也会做相同检查，不要求用户手动管理 `node_modules`。

编辑新项目中的 `narration.txt`、`storyboard.md`、语义字幕和场景内容。先用任意合适的 TTS 生成 `audio/narration.mp3` 和符合接口规范的逐词时间 JSON，然后执行：

```bash
node scripts/notebook-video.mjs build-semantic-captions ./my-video/audio/narration.mp3.json ./my-video/manifests/semantic-caption-lines.txt ./my-video/manifests/caption-cues.json --lead-ms 60
node scripts/notebook-video.mjs sync ./my-video
node scripts/notebook-video.mjs render ./my-video ./my-video/renders/final.mp4
node scripts/notebook-video.mjs validate-video ./my-video/renders/final.mp4 EXPECTED_SECONDS ./my-video/renders/contact-sheet.jpg
```

Windows 可以直接使用相同的 Node 命令，也可以调用 `scripts\*.cmd`。在受限容器中如 Remotion 无法读取网卡信息，可在渲染命令前设置 `REMOTION_USE_NETWORK_SHIM=1`。

## 必须保留的设计约束

- 以 `assets/example-project/` 为唯一官方引擎，不从提示词重新搭建。
- 原生 30fps 制作和交付，不把重复帧伪装成 60fps。
- 只挂载当前场景；转场期间最多同时存在两个场景。
- 动画优先使用 transform，不逐帧触发布局计算。
- 字幕按语义与停顿断句，产品名、数字单位和固定术语不得被拆开。
- 每次最终交付必须包含 MP4、质检结果和可编辑源码包。

完整生产规则在 [SKILL.md](SKILL.md)，视觉、字幕、性能、跨平台和质检细则位于 `references/`。

## 验证改动

```bash
node scripts/notebook-video.mjs validate-skill
node scripts/notebook-video.mjs validate-official-example
```

涉及画面或时间轴的改动还必须渲染对应片段并人工查看关键帧；最终版本需要完整渲染和视频质检。

## 第三方材料

- Source Han Sans CN 与 Smiley Sans 使用 SIL Open Font License 1.1，许可证保留在 `assets/fonts/`。
- 示例 WAV 音效为程序生成，复用说明位于 `assets/example-project/public/sfx/LICENSE.txt`。
- Remotion、React 及其依赖继续遵循各自许可证。
- Remotion 使用自有的 source-available 许可证，并不是 OSI 定义的开源软件。个人和符合条件的小团队可免费使用，其他组织可能需要购买许可；新建工程会自动保留许可提示。
- TTS 层保持 Provider 中立，仓库不内置任何 TTS 客户端。Edge 在线朗读可以和商业 TTS、平台 TTS 一样作为外部参考，但需要 AI 或使用者按接口规范自行接入，并确认服务条款。

更多信息见 [NOTICE](NOTICE)、[CONTRIBUTING.md](CONTRIBUTING.md)、[SECURITY.md](SECURITY.md) 和 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。
