# 技术：auto 引擎、环境、跨平台、性能与完整工作流

本篇汇总 `compose-story` 引擎机制、跨平台与 Windows 注意事项、依赖政策及完整交付流程。所有跨语言数值常量以 `assets/lecture-template/src/contract.json` 为唯一真源。

<a id="auto-engine"></a>
## 1. auto 引擎（`story.json` → 可渲染工程）

`scripts/compose-story.py` 将纯内容 `story.json` 编译为可渲染 Remotion 工程（输出 `narration.txt`、`manifests/caption-cues.json`、`manifests/shots.json`、`src/story.ts`、`src/scenes.tsx` 等），自动处理：

| 维度 | 引擎规则（数值来源） | 自动修复 / 报错行为 |
|---|---|---|
| 帧率 | `FPS`（30） | 全链路绝对帧换算统一读 `contract.json` |
| 排时长基准读速 | `READ_CPS`（4.5）加权字/秒（手作估算可用 `--cps=6.5`） | 无 TTS 时按读速 + 标点停顿（逗号 150ms、句末 300ms）排镜长 |
| 字幕每行字数 | ≤ `CAPTION_MAX_CHARS`（16）字（同步门禁逐字符 P0） | 超长自动在合法语义断点拆行，不劈 `{{术语}}` / `protect` / 英文 / 数字 |
| 字幕读速硬上限 | `CPS_MAX`（9.0）加权字/秒 | 由 `validate-presentation.py` 判 P0（与 `READ_CPS` 区分） |
| 画面正文最小字号 | `MIN_FONT`（32px）；代码扫描绝对地板 `MIN_LABEL_FONT`（13px） | 先换行再缩字号，到地板仍放不下则报错并提示需删字数 |
| 焦点推近上限 | 含字镜总缩放 ≤ `TEXT_ZOOM_MAX`（1.35），auto 搜索上限 `ZOOM_MAX`（1.32），纯图形 ≤ `GRAPHIC_ZOOM_MAX`（1.6） | 逐级降倍与平移，确保取景窗不切断任何文字 |
| 镜尾防静止 | 镜尾 > 1.5s 无事件自动补收束慢推；成片静止上限 `DEFAULT_MAX_STATIC`（2.5s），锤子镜 `HAMMER_MAX_STATIC`（3.0s） | 避免触发 `validate-motion-gaps.py` P0 |
| 讲稿问题字段 | 每镜应填 `$asks`（回答观众的哪个问题） | 未填或保留模板示例记 P1 提示，不拦出片 |

- **`story.json` 关键顶层字段**：`title`、`theme`（默认 `flat`）、`mode`（`hybrid`/`component`/`freeform`，门禁契约）、`subject_of_film`（主题物，须至少在某一镜 `see`/`title` 或图版中出现）、`glossary`（术语大白话表）、`protect`（不可跨字幕切开的词数组，须原样出现在台词中）。
- **关键词联动硬规则**：台词里的 `{{词}}` 必须在当镜画面元素文字中找得到，否则 `compose-story.py` 报 P0；若画面字面不同，显式写成 `{{词|元素id}}`（报错信息会列出当镜可用 `id`）。
- 引擎支持的 13 种版式：`statement`、`define`、`number`、`bars`、`compare`、`code`、`flow`、`list`、`quiz`、`custom`、`media`、`page`、`type`。
- 蓝图里的 `<<…>>` 占位符未替换会在 compose 期直接判 P0 并列出剩余位置。

<a id="environment-matrix"></a>
## 2. 环境矩阵

| 依赖 | 最低要求 | 用途 | 缺失时表现 |
|---|---|---|---|
| Python | 3.10+（仅标准库） | 排版、时间轴解析、全部 20 道 Python 门禁 | 无法运行构建期管线 |
| Node.js | 18+ | `notebook-video.mjs` / `make-video.mjs` / Remotion | 无法运行 CLI 与渲染 |
| FFmpeg / FFprobe | 系统 PATH 可用 | 联系表拼图、响度归一化、媒体转码、静止段检测 | 转码/拼图/成片门禁失败 |
| Chromium / Chrome | Remotion 自动下载或 `REMOTION_BROWSER_EXECUTABLE` | `--stills` / `preview` / `--render` 浏览器渲染 | 仅能跑离线构建期门禁，无法出图/出片 |
| `edge-tts`（可选） | Python CLI 或自备录音 | 生成真实中文配音与词级时间戳 | 静音占位仅用于 `--stills`/`preview`，`--render` 会停 |

**开工前自检**：`node scripts/notebook-video.mjs check-deps` 看 Python / Node / FFmpeg 是否就位；`capabilities`（加 `--json` 给脚本读，不支持时退码 1）报出这台机器能出到哪一级，`blockers[]` 每项带修法；首次出图前可跑 `prepare-browser` 预取渲染浏览器。

**能跑完但结果不对的陷阱**：
- 没装 BudouX 时语义断句会标 SKIPPED 跳过、退码仍为 0；交付路径自动加 `--require-budoux`，这时会失败而不是静默跳过。
- 手作皮肤缺 Noto Serif SC 时，Chrome 只报网络错误、不提缺字体；先看 `capabilities` 的 `fonts.serif`，缺了跑 `notebook-video fonts --serif`。
- 缺 FFmpeg 时 compose 照样写出工程，但 `validate-video` 与音轨合成都不可用，「排版成功」不等于「能出片」。

<a id="cross-platform-compatibility"></a>
## 3. 跨平台兼容契约

- 统一入口为 `node scripts/notebook-video.mjs <子命令>` 与 `node scripts/make-video.mjs`，Windows 同步提供 `scripts/notebook-video.cmd` 与 `scripts/make-video.cmd`。
- 所有 Python 子进程统一开启 `PYTHONUTF8=1` 与 `PYTHONIOENCODING=utf-8`，避免控制台编码导致门禁符号（`✓`/`✗`）抛错。
- 路径拼接统一使用 `path.join` / `pathlib.Path`，不在指令文档中写死 POSIX 专属 shell 脚本命令。

<a id="windows-compatibility"></a>
## 4. Windows 专项说明

- Node 18+ 禁止直接 `spawn('npm.cmd')`，CLI 自动优先调用随 Node 安装的 `npm-cli.js`。
- Windows 禁止写 `npx remotion`（易挂死），且勿在 OneDrive 等云同步目录执行渲染。
- 渲染时自动预加载 `scripts/windows-hide-console.cjs` 隐藏 Remotion 子进程闪烁的控制台窗口。
- 清理 `.bundle` 目录启用 `maxRetries` 以应对杀毒软件/索引器短暂锁文件。
- **常见故障**：命令找不到 → 装完 Node / Python / FFmpeg 后重开终端，再跑 `check-deps`；PowerShell 拦脚本 → 用 `node scripts/notebook-video.mjs …` 或 `.cmd`，不用改执行策略；npm 安装报文件被占用 → 关掉 Remotion Studio、编辑器和资源管理器预览，只删本工程的 `node_modules` 重来，不要从别的系统拷 `node_modules`；路径过长 → 把技能和工程挪近盘符根目录；杀毒拦 Chromium / FFmpeg → 把它们加白名单或换受信任目录，不要关掉素材校验或换渲染器绕过。

<a id="performance-design"></a>
## 5. 性能与断点续渲

- **先静帧再预览最后整片**：`--stills` 一次打包按关键帧出图，成本远低于整片渲染；看动态用 `notebook-video preview <工程> --seconds=30`，全片体检用 `notebook-video sweep <工程>`。
- **渲染锁与断点续渲**：`scripts/render-lock.mjs` 防止同一工程并发渲染损坏输出；中途中断用 `notebook-video render <工程> <输出> --resume` 续渲。
- **并发度**：可通过 `REMOTION_CONCURRENCY` 限制渲染线程，避免低内存机器 OOM。
- **只重出附件不重渲**：封面不满意用 `notebook-video poster <工程> [out.jpg] [--shot=S4|--frame=759]` 换一帧；字幕和封面一起重出用 `notebook-video deliver <工程>`。`notebook-video clean <工程>` 清 `renders/` 里可重建的中间产物（默认只预演，`--yes` 才删，`--all` 连成片一起删）。

<a id="dependency-policy"></a>
## 6. 依赖政策

- `scripts/*.py` 严格只用 Python 标准库，禁止要求用户额外 `pip install` 第三方包才能跑门禁（`faster-whisper`、RapidOCR 为可选增强，缺失时优雅降级）。
- 模板 `package.json` 已内置开源库可直接使用无需再次询问；中文断行必须用 `fitChineseTextOnNLines`，严禁用 `@remotion/layout-utils` 的 `fitTextOnNLines`（会把中文压成 16px 一行）。
- 模板前端依赖锁定在 `assets/lecture-template/package-lock.json`，如需新增 npm 依赖**必须先停下征得用户同意**。
- 字体：LXGW WenKai Lite、Noto Serif SC 与 Clash Display 均按表与 `sha256` 按需下载（支持 `NOTEBOOK_VIDEO_FONT_BASE_URL` 等镜像环境变量）；离线时 Clash Display 自动回落 Space Grotesk 并给 P1 提示。

<a id="remotion-architecture"></a>
## 7. Remotion 架构契约

- 合成入口位于 `assets/lecture-template/src/index.tsx`，主合成 ID 为 `NotebookVideoFilm`，固定 `FPS`（30）、合成画布 `2560×1440`（内部舞台缩放自 `1920×1080`）；`make-video` 缺省 `--scale=0.75` 交付 1920×1080，`--scale=1` 交付 2560×1440。
- 渲染期门禁（`CardFitGate`、`CaptionFitGate`、`OverlapGate`、`CanvasBoundsGate`）共用 `layout-probe.tsx` 探针骨架；其中 `CanvasBoundsGate` 在成片合成中保持 `mode="warn"`，避免误报阻断交付。
- 禁止在运行时使用 `Math.random()`、系统时间或非确定性异步状态；同一帧渲染两次必须像素一致。

<a id="skill-workflow"></a>
## 8. 完整工作流

1. **选题与准备**：明确一句话核心答案，按 [narration.md](narration.md) 写讲稿，手作路线先按 [director.md](director.md) 写 `manifests/treatment.json`，并用 `commons-search.py` 检索授权素材。
2. **建工程与编排**：`notebook-video new-project <工程> --style=<皮肤>` → 照蓝图填好 `story.json`（每镜写 `$asks`）→ `make-video story.json <工程> --stills`。
3. **读门禁与评审**：
   - 检查 `renders/gates.json` 与 `renders/report.md` 首屏：P0 必须全部归零，同一个 `✗` 连续两轮修不掉立即停下问用户。
   - 检查 `renders/report.md` 首屏评审卡状态（未评审会首行显示「未评审」）；手作路线建议开独立会话按 `references/rubric.md` 评审，组件路线可选。
   - 运行 `validate-facts <工程> --review` 核对数字与年份；主要事实缺出处须停下问用户。
4. **配音与重排**：跑 `notebook-video tts <工程>` 生成真实旁白后，重跑 `make-video` 让字幕与镜头对齐真实词流。
5. **征得同意后整片交付**：向用户展示静帧/报告并获得确认后，运行 `make-video <工程> --render <输出>.mp4`；交付物自动附带 `renders/captions.srt`、`renders/poster.jpg` 与署名清单。
