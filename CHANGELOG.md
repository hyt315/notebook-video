# Changelog

格式参照 [Keep a Changelog](https://keepachangelog.com/)：每个版本一节，每条改动一行。当前版本号以 `manifest.json` 为准。
Format follows Keep a Changelog: one section per release, one line per change. The current version lives in `manifest.json` only.

更早的完整记录（1.0.0 – 3.5.4，中英双写的长条目）已归档到仓库内的 `docs/history/CHANGELOG-legacy.md`（只在仓库里，不进发布包）。
The full earlier history (1.0.0 – 3.5.4) is archived in the repository at `docs/history/CHANGELOG-legacy.md` (repository only, not shipped).

## [3.9.0] - 2026-11-28

### Added
- 新增必跑字号门禁 `scripts/validate-typography.py`：按渲染布局与主题令牌计算字号，要读的字（字幕、章节标、卡片 / 对比栏 / 清单 / 流程主文案）低于 64 设计 px 即 P0；代码行与密集柱标可自动收缩，低于地板记 P1。零依赖，不依赖 OCR，不会 SKIPPED；已接入 `make-video` 构建期门禁。 / Added the always-on `validate-typography.py` gate: computed font sizes, P0 below 64 design px for readable text, no OCR, never skipped; wired into `make-video`.
- `list` 版式新增两列卡片网格变体 `grid`；组件皮肤按叙事关系调度 `whip` / `slide` / `zoom` / `fade` 转场。 / Two-column `grid` variant for `list`; narrative-aware transitions on component skins.
- 新增可跑配方 `examples/recipes/archive-first-msg` 与 `papercut-symmetry`（story + treatment）。 / New runnable recipes `archive-first-msg` and `papercut-symmetry`.
- `tts.py` 混音前把旁白自动归一化到 `-16 LUFS / -1.5 dBTP`（`--no-normalize` 关闭）；`validate-caption-sync.py` 可选 `--audio` 核对音频时长；`selftest` 增加对应检查。 / Pre-mix narration normalisation in `tts.py`; optional `--audio` check in `validate-caption-sync.py`.

### Changed
- 五套皮肤视觉重做：`archive` 改为冷白背光档案灯台与纯白纸卡，`flat` 改为淡天空蓝 / 奶油底配纯白卡片，`journal`、`papercut` 主背景重绘；五套皮肤一帧可辨，背景库总体积下降约 559 KB。 / Redrew the five skins so each is recognisable from one frame; background library about 559 KB smaller.
- `papercut` 字幕墨色加深至 `#6e0c10`（对比度 ≥ 7:1），字幕字号与墨色改为跨文件单一来源并做一致性校验。 / Deeper `papercut` caption ink; single source of truth for caption size and ink.
- 母带响度：真峰值目标收紧为 `-2.0 dBTP`（`loudnorm` 打到 `-2.6`、限幅 `-2.0`），`validate-video` 上限由 `-1.5` 收紧为 `-1.8 dBTP`。 / True-peak target tightened to -2.0 dBTP; `validate-video` ceiling now -1.8 dBTP.
- `validate-motion-gaps.py`：片尾最后 1.5 s 内的末镜自然定格放宽到 3.5 s 并单独标注，与 `ffmpeg freezedetect` 口径一致；片中静止段仍按 2.5 s 判 P0。 / Closing hold rule aligned with `freezedetect`; mid-film stills still 2.5 s.
- auto 路线排版：`story_layout.py` 三档字号由 76 / 46 / 36 提到 100 / 72 / 68 设计 px，内容带加宽到 1640 px，卡片按内容区放大；随包示例与配方 story 同步重写。 / Auto-route type scale raised to 100 / 72 / 68 design px with a wider content band; examples rewritten.
- 文档口径：运行时不调用生图模型、不联网取图，维护期预置背景在 `backgrounds.json` 登记来源、生成方式、许可与 `sha256`；精简 `narration.md` 示例对照。 / Docs clarify no runtime image generation or network fetches; pre-built backgrounds are fully registered.

### Fixed
- `make-video --render` 的相对路径按工程目录解析；已有工程在仍是模板默认导演层时也会同步示例自带的 `treatment.json`；未传 `--stills` / `--render` 时给出提示。 / Relative `--render` paths, treatment sync for existing projects, and a hint when nothing is rendered.
- auto 路线要读的字（结论、条目、注记、导语、手写说明）自动缩字的地板由 32 提到 64 设计 px，与字号门禁一致；放不下时报错并提示删字或拆镜，不再悄悄缩小。结论允许两行，两列网格条目允许四行；随包示例的超长文案相应精简。 / Readable auto-route text no longer shrinks below 64 design px (matching the typography gate); overflow now errors with a cut-or-split hint. Over-long example copy shortened.
- 示例导演层同步只在工程尚无导演层、或与模板默认导演层一致时进行，不再按文本关键词判断，避免覆盖作者已写的 `treatment.json`。 / Example treatment sync now only replaces a missing or untouched template treatment.
- `validate-media.py` 支持 VP8 / VP8L WebP 尺寸解析；`coords-lint.py` 增加 1080p 纵向越界检查；`validate-audio-levels.py` 对音效库实测响度偏离给出 P1。 / WebP VP8/VP8L sizes, 1080p Y-bounds, SFX loudness drift warning.

## [3.8.0] - 2026-11-27

### Added
- 新增 `scripts/deps-cache.mjs` 与增强版 `scripts/browser-exec.mjs`：跨工程按锁文件哈希与校验和优先扫描并复用本机/共享缓存的 `node_modules`、渲染浏览器与字体，首次缺失时仅安装或下载一次。 / Added `scripts/deps-cache.mjs` and enhanced `scripts/browser-exec.mjs` to scan and reuse cached `node_modules`, rendering browsers, and fonts across projects by lockfile hash and checksum, fetching once only when absent.
- 运镜导演支持多意图调度（`push-in` / `pull-back` / `pan-follow` / `still`、`CinemaSpec.driftDir`）与章节切换转场联动，并按镜标题分布版式变体。 / Multi-intent camera director (`push-in`, `pull-back`, `pan-follow`, `still`, `CinemaSpec.driftDir`), chapter-aware transitions, and title-seeded layout variants.
- `validate-presentation.py` 新增前景叠加占比检查（`check_overlay_budget`）；`validate-video` 新增逐帧节奏与曝光/对比度校验。 / Added foreground overlay budget checks in `validate-presentation.py`, plus frame pacing and exposure/contrast checks in `validate-video`.

### Changed
- 默认交付分辨率设为 2560×1440（`--scale=1 --crf=18 --x264-preset=veryfast`）；`--stills` 采用单浏览器会话连续出图；`remotion.config.ts` 关闭源码映射生成并剥离内置映射引用。 / Default render output set to 2560×1440 (`--scale=1 --crf=18 --x264-preset=veryfast`), `--stills` reuses one browser session, and `remotion.config.ts` disables and strips sourcemaps.
- 字幕默认采用 64px 纸色描边无框样式，精简顶部角标与前景叠加占比；进场与媒框显隐切换为 `clipPath` / `translateY` 合成属性动效。 / Open 64px paper-halo subtitles with compact top-left chapter badges; composited `clipPath` and `translateY` reveal/media transitions.
- TTS 对齐支持模糊匹配降级、音节加权切分、语音起止检测、口语规范与削波检查，以及句间停顿切镜；冷开重音重叠阶段人声压低触发系数为 `0.78`。 / Resilient TTS alignment with fuzzy fallback, weighted splitting, speech bounds, spoken-form/clipping checks, pause-midpoint shot cuts, and `0.78` cold-open ducking.
- `SKILL.md` 与 `references/` 围绕冷开承诺呼应与讲稿契约合并精简，`README.md` / `README.en.md` 口径与实现保持同步。 / Consolidated `SKILL.md` and `references/` around cold-open promise/payoff and narration contracts, and synced `README.md` / `README.en.md`.

### Fixed
- 修复 Windows 下目录链接、缺少 Whisper 的测试隔离、`ffprobe` 帧时间戳字段、同目录处理稿精确匹配及空卡片边界校验。 / Fixed Windows directory linking, Whisper-absent test isolation, `ffprobe` frame timestamp fields, sibling treatment lookup, and empty-deck bounds.

### Removed
- 移除静态样式镜像 `references/locked-style-contract.json`；`package-skill.py` 排除开发/示例文档并执行包内禁用模式扫描。 / Removed redundant `references/locked-style-contract.json` and excluded dev/example docs in `package-skill.py` with banned-pattern scanning.

## [3.7.0] - 2026-11-26

### Added
- 讲稿标准 `references/narration.md`（误解优先、每镜一问、好坏讲稿对照），组件路线与手作路线共用。 / Shared narration guide `references/narration.md` with good-vs-bad pairs.
- 「讲清楚」评审卡 `references/rubric.md`（5 项、1–5 分）；`validate-treatment` 按这五项读 `review.rounds`，`renders/report.md` 首屏显示评审分数或「未评审」。 / 5-item clarity rubric; review scores (or "unreviewed") lead `renders/report.md`.
- 蓝图与随包示例每镜写 `$asks`（这一镜回答观众的哪个问题），未填记 P1。 / `$asks` on every blueprint and example shot; P1 when missing.
- `notebook-video showcase` 改走独立入口 `src/showcase-entry.tsx`，成片入口不带样张依赖。 / Component sheets render from their own entry point.
- `validate-skill-consistency` 也核对文档引用的 `src/contract.json` 数值与脚本常量（如 `CPS_MAX`）。 / Consistency check covers contract values and script constants quoted in docs.

### Changed
- `references/` 精简为 11 篇 + `themes/` 6 篇，SKILL 路由加讲稿与评审卡；门禁执行的规则都有对应说明。 / References condensed to 11 + 6 files; every enforced rule stays documented.
- 画面：五套主题椭圆暗角与定向光，手作纸张双层投影，镜头去掉正弦呼吸，媒体框与卡片边线收细。 / Lighter framing, vignettes and paper shadows; no sine "breathing" camera.
- 动效统一为不过冲的缓动（`src/motion.ts`）；代码块按语言高亮（Shiki）；手写批注时长写进 `contract.json` 的 `ANNOT`。 / No-overshoot easing shared in `src/motion.ts`; Shiki code colouring; annotation timing in `ANNOT`.
- 主题背景与纸纤维纹理改用 WebP（`public/bg/bg-*.webp`、`public/craft/fibre-tile.webp`），包更小。 / Theme backgrounds and fibre tile are WebP (smaller package).
- 冷开：各皮肤第一镜的首个元素在第 0 帧已落定（O6 手作皮肤 P0、组件皮肤 P1）。 / Cold open: the first element is settled at frame 0 on every skin.
- 招牌镜推不进也扫不开时，compose 改选最近能推的一镜并写回 treatment。 / Compose reassigns an unmovable signature shot to the nearest movable one.
- 门禁口径：字幕行长 Python 与浏览器同一种数法（去句末标点、ASCII 计 1）；P0 只表示拦片；浏览器门禁结论写进 `renders/gates.json`；「画面空」的修法不再与「不改小 anchor」冲突。 / One caption-length count; P0 means blocking only; browser gates report to `gates.json`.
- 排版与运镜：代码行估宽、行高、ms→帧取整与浏览器一致；门禁按真实相机路径判；compare / flow 保持各自位置。 / Layout and camera estimates match the renderer; gates read the real camera path.
- 音频：与人声重叠的音效自动压低约 4 dB，带裁剪的音效起播微淡入；TTS 标点对齐失配时降级对齐，网络瞬断重试，缺 Whisper 模型时退回按字数均分。 / Voice-aware SFX ducking; resilient TTS alignment and retries.

### Fixed
- 配音后关键词高亮与推近跟着 TTS 重算；codebox 的失效音效 `typing` 改为 `highlight`。 / Term timings follow TTS; codebox uses the `highlight` SFX.
- 组件路线按作者的 `treatment.json` 运镜，模板示例 treatment 不套用（P1）；手作 story 工程留着模板 treatment 时只报一条 P0。 / Author treatment honoured; leftover template treatment gives one clear message.
- 直书页每行的 `reveal` 各自生效；flow 步骤缺 `label` 时给出可照改的报错。 / Per-row `reveal` on type pages; actionable error for flow steps without `label`.
- 手写场景蓝图（`$route: handwritten-craft`）喂给 `compose-story` 时直接说明路线；SKILL 选路线表指向可跑的 `examples/recipes/*.story.json`。 / Handwritten blueprints are named as such; route table points to runnable recipes.
- `medium-metaphor` 蓝图补上可省的片名拍，节拍不留空档。 / `medium-metaphor` blueprint timing has no gap.
- 文档与实现对齐：交付尺寸（缺省 `--scale=0.75` 出 1920×1080）、门禁等级、`data-gate-allow` 取值、锤子帧与 `recipe: "hammer"`、CC BY-SA 口径；补上 `recipe` / `sketch` / `annotate`、`sources` / `claim`、`cinema` 块与 `poster` / `deliver` / `clean` 的写法。 / Docs match the code on delivery size, gate levels and syntax.
- `selftest` 负例按各门禁自己的拦截语句判，崩溃不算拦住。 / Selftest negatives match each gate's own message; crashes no longer count as blocked.

### Removed
- `references/MOVED.md`；旧文档名锚点仍保留在新文件里。 / Removed `references/MOVED.md`; legacy anchors remain.
- JPEG / PNG 版主题背景与纸纤维纹理（由 WebP 取代）。 / JPEG / PNG backgrounds and tile (replaced by WebP).

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
