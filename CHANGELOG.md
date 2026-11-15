# Changelog

格式参照 [Keep a Changelog](https://keepachangelog.com/)：每个版本一节，每条改动一行。当前版本号以 `manifest.json` 为准。
Format follows Keep a Changelog: one section per release, one line per change. The current version lives in `manifest.json` only.

更早的完整记录（1.0.0 – 3.5.4，中英双写的长条目）已归档到仓库内的 `docs/history/CHANGELOG-legacy.md`（只在仓库里，不进发布包）。
The full earlier history (1.0.0 – 3.5.4) is archived in the repository at `docs/history/CHANGELOG-legacy.md` (repository only, not shipped).

## [Unreleased]

### Changed
- 发布包不再带 `scripts/dev/` 与 `docs/`；`.gitattributes` 用 export-ignore 标出开发期文件。 / The package no longer ships `scripts/dev/` or `docs/`.
- 删掉 15 个只做转发的 `.sh/.cmd`，命令统一走 `notebook-video <子命令>`，Windows 只留 `notebook-video.cmd`、`make-video.cmd`。 / Removed 15 forwarding wrappers; use `notebook-video <subcommand>`.
- 单元测试默认离线：需要下载字体的首跑用例只在已有字体或 `NV_ONLINE=1` 时运行。 / Unit tests run offline by default (`NV_ONLINE=1` enables the font-download cases).
- CHANGELOG 改为每条一行，旧档归档。 / One-line changelog; old history archived.

### Fixed
- 在仓库根跑渲染命令时下载到 `.remotion/` 的浏览器被当成生成目录（gitignore、自检、打包都排除）。 / `.remotion/` browser downloads are treated as generated files.

## [3.5.4] - 2026-11-11
- 止血版本：不改门禁判据与视觉风格，修掉整片渲染丢镜、逐字展开切半字、字体未就绪就量字三处画面问题，随包示例全部过得了自己的门禁。 / Stop-the-bleeding release: three render fixes, all bundled examples pass their own gates.

## [3.5.3] - 2026-11-04
- 小版本：补回该有的校验、让已有建议看得见、修掉文档漂移，不改门禁判据与画面。 / Restored checks, visible hints, doc drift fixes.

## [3.5.2] - 2026-11-04
- 「讲到哪长到哪」从开始帧对齐推进到真的长完、先后顺序对。 / Reveals now finish, in the right order.

## [3.5.1] - 2026-11-03
- 草稿纸讲解：东西只在旁白讲到时出现并长出来。 / Draft-paper narration.

## [3.5.0] - 2026-11-03
- 手账页承载真东西、组件负责讲清；渲染锁与断点续渲、`clean` 与 `capabilities` 命令；音效库收为 9 个。 / Journal pages, render lock and resume, `clean` / `capabilities`.

## [3.4.0] - 2026-10-30
- 30 秒预览与全片体检、可度量的版面空、字幕 / 封面 / 打包交付链路、自带中文分词模型。 / Preview and sweep, delivery chain, bundled segmenter.

## [3.3.0] - 2026-10-30
- 导演层与独立评审、三套手作皮肤、真翻页转场、背景库、运镜 / 开场 / 字幕 / 响度四道门禁。 / Director layer, hand-made skins, page turns, four new gates.

## 3.2.0 及更早 / 3.2.0 and earlier
- 见归档 `docs/history/CHANGELOG-legacy.md`。 / See the archive.
