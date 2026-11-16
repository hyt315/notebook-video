# Changelog

格式参照 [Keep a Changelog](https://keepachangelog.com/)：每个版本一节，每条改动一行。当前版本号以 `manifest.json` 为准。
Format follows Keep a Changelog: one section per release, one line per change. The current version lives in `manifest.json` only.

更早的完整记录（1.0.0 – 3.5.4，中英双写的长条目）已归档到仓库内的 `docs/history/CHANGELOG-legacy.md`（只在仓库里，不进发布包）。
The full earlier history (1.0.0 – 3.5.4) is archived in the repository at `docs/history/CHANGELOG-legacy.md` (repository only, not shipped).

## [3.6.1] - 2026-11-16

### Changed
- 审美判据只点名不阻断：骨架 / 布局 / 意图 / 介质多样性、运镜配额、声明运镜却不动、G-14/G-15/G-16 纸面字段、treatment 纸面字段降为 P1；出界、枚举闭合、beats 越界、占位与自相矛盾仍是 P0。 / Aesthetic checks (diversity, camera quotas, paper fields) are now P1 warnings; technical errors stay P0.
- 锤子镜（`recipe=hammer`、StampBanner / HandLettering / Seal）静止上限放宽到 3.0 s，其余仍 2.5 s。 / Hammer shots may hold still up to 3.0 s.
- 真卷页改用 `@remotion/effects` 官方 pageTurn（WebGL2），探针不过退回 CSS 翻页；删掉自写的 fx 管线。 / Page curl uses the official `@remotion/effects` pageTurn.
- 字体下载合成一张表（LXGW / Noto Serif / Clash）；排版字宽优先读 metrics 缓存。 / Table-driven font downloads; layout reads the metrics cache first.
- `locked-style-contract.json` 只留描述字段，数值以 `src/contract.json` 为准。 / Numeric values now live only in `src/contract.json`.
- references 去掉版本注记与经过叙述，重复段改为链接（判据与等级不变）；更正 auto 转场说明为一律翻页。 / References trimmed; auto transitions documented as page turns.

- 五道浏览器门禁共用 `layout-probe.tsx` 的测量骨架；九个 P0/P1 型门禁的收尾统一到 `gate_report.finish()`，输出与退出码不变。 / Browser gates share one probe skeleton; validators share one finish routine.

### Removed
- 零引用的 Dimension / MagnifyInset / MediaAudio；WhipBlur、SlotGuard 改为引擎内部件。 / Removed unused Dimension, MagnifyInset, MediaAudio.

### Tests
- selftest 去掉与负向抽查、单测重复的项，语法与密钥检查移入单测；测试临时目录用完即删；负向抽查常见夹具收成 `shot_case`。 / Deduplicated selftest; temp dirs cleaned on exit.
- 回归快照覆盖 make-video 构建期 11 道门禁，逐条记录等级；新增件名一致性、motion-gaps、treatment 纸面字段用例；负向抽查新增 `must_quiet`。 / Regression snapshot covers 11 build-time gates with per-rule levels; new name-consistency and gate tests.

## [3.6.0] - 2026-11-16

### Changed
- 发布包不再带 `scripts/dev/` 与 `docs/`；`.gitattributes` 用 export-ignore 标出开发期文件。 / The package no longer ships `scripts/dev/` or `docs/`.
- 删掉 15 个只做转发的 `.sh/.cmd`，命令统一走 `notebook-video <子命令>`，Windows 只留 `notebook-video.cmd`、`make-video.cmd`。 / Removed 15 forwarding wrappers; use `notebook-video <subcommand>`.
- 单元测试默认离线：需要下载字体的首跑用例只在已有字体或 `NV_ONLINE=1` 时运行。 / Unit tests run offline by default (`NV_ONLINE=1` enables the font-download cases).
- CHANGELOG 改为每条一行，旧档归档；版本号只留在 `manifest.json`。 / One-line changelog, old history archived; version lives in `manifest.json` only.
- SKILL.md 改为路由式入口，references 51 篇合并为 9 篇 + `themes/` 6 篇；`validate-skill` 守护过程词与内部版本号。 / Router-style SKILL.md; references merged into 9 + 6 files; process-word guard.
- 形式性 P0 降为 P1（treatment 候选数、未搜 Commons、开场写法、手作皮肤缺评审），客观项仍拦片。 / Formal P0s downgraded to P1; objective checks still block.
- 跨语言常量收进模板 `src/contract.json`，TS 与 Python 同读一份。 / Shared constants in `src/contract.json`.
- 帧参数改为必填类型、由 `tsc` 检查，删除 `validate-frame-props.py`。 / Frame props are required types checked by `tsc`; `validate-frame-props.py` removed.
- 字幕只留 `manifests/caption-cues.json` 一份。 / One caption source of truth.
- `--engine=file` 可选 `faster-whisper` 词级对齐自己的录音，没装按字数均分。 / Optional faster-whisper alignment for your own recording.
- 门禁统一结果写 `renders/gates.json`，删除 `p1-hints.mjs`。 / Unified gate results in `renders/gates.json`; `p1-hints.mjs` removed.
- 逐文件许可登记 `REUSE.toml` + `LICENSES/`，CI 跑 `reuse lint`。 / Per-file licensing via REUSE.
- 一条命令跑完开发期检查：`python3 scripts/dev/test-all.py`；回归集 16 份；组件使用率报告。 / One-command checks, 16-story regression set.
- Clash Display 不再入库（ITF Free Font License §02 禁止经仓库再分发），首次用到时从 Fontshare 按 sha256 下载；离线回落 Space Grotesk 并给 P1 提示。 / Clash Display is downloaded on demand from Fontshare; offline falls back to Space Grotesk.
- 技能不调用生图模型：图来自用户、Commons / Openverse 或其他授权来源。 / The skill never calls image models.

### Fixed
- 在仓库根跑渲染命令时下载到 `.remotion/` 的浏览器被当成生成目录（gitignore、自检、打包都排除）。 / `.remotion/` browser downloads are treated as generated files.
- `text_metrics.py` 丢掉 gid ≥ numberOfHMetrics 的字形宽度，按 OpenType 规范修正（与 fontTools 对照一致）。 / Fixed advance widths for high glyph ids.
- compose-story 保护短语去重随 `PYTHONHASHSEED` 变序。 / Deterministic protected-phrase order.
- `visual-assets.json` 手作皮肤背景 `source_type` 改为 `code-generated`，与 `backgrounds.json` / NOTICE 一致；DEPENDENCIES 的字体与插图说法与实际一致。 / Registry fixes for craft backgrounds and DEPENDENCIES.

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
