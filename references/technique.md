# 技术：auto 引擎、环境、跨平台、性能与完整工作流

本篇汇总 `compose-story` 引擎机制、环境矩阵、跨平台契约、性能断点与依赖政策。数值真源为 `assets/lecture-template/src/contract.json`。

<a id="auto-engine"></a>
## 1. auto 引擎（`story.json` → 可渲染工程）

`scripts/compose-story.py` 将纯内容 `story.json` 编译为可渲染工程，自动处理以下维度：

| 维度 | 引擎规则（真源常量） | 自动修复 / 报错行为 |
|---|---|---|
| 帧率与排时长 | `FPS`（30）；无 TTS 基准 `READ_CPS`（4.5，手作可 `--cps=6.5`），含标点停顿 | 有真实 TTS 时自动按 `audio/narration.meta.json` 词级时间重排（失配 ≤10% 用可读音字流兜底对齐，≥10% 报提示保留原时序）；镜间切点落在句间静音中点 |
| 字幕行宽与读速 | 每行 ≤ `CAPTION_MAX_CHARS`（16）；读速上限 `CPS_MAX`（9.0） | 超长按语义与保护短语自动拆行；超速由 `validate-presentation.py` 判 P0 |
| 字号与缩放 | auto 正文地板 `MIN_FONT`（32px）；含字总缩放 ≤ `TEXT_ZOOM_MAX`（1.35）、auto 搜索上限 `ZOOM_MAX`（1.32）、图形 ≤ `GRAPHIC_ZOOM_MAX`（1.6） | 降倍与平移避让标题，防切字；放不下先换行再缩字至地板后报错 |
| 多样性与反同质 | 基于标题哈希交替选用版式变体（`left`/`mirror`/`center`），相邻换版式 | 结合文本/结构由相机导演驱动多意图运镜，避免模板味 |
| 讲稿与占位符 | 每镜须填 `$asks`；禁止遗留蓝图 `<<…>>` 占位符 | 缺 `$asks` 记 P1；未填占位符直接判 P0 |

- **`story.json` 顶层关键字段**：`title`、`theme`（默认 `flat`）、`mode`（`hybrid`/`component`/`freeform`）、`subject_of_film`（纯软件/抽象结构可写 `"software"`/`"abstract"` 并配 `subject_why`）、`glossary`（大白话术语表）、`protect`（不劈开词组数组）、`transition`（整片默认；单镜可在 shot 上写 `transition` 覆盖）、`camera: "still"`（定机）。若 `my-story.json` 同目录存在同名 `my-story.treatment.json`，`make-video` 新建工程时自动带入 `manifests/treatment.json`。
- **关键词联动**：台词 `{{词}}` 须匹配当镜元素文本或显式 `{{词|元素id}}`，念到时自动高亮与触发焦点/提示（可用 13 版式：`statement`/`define`/`number`/`bars`/`compare`/`code`/`flow`/`list`/`quiz`/`custom`/`media`/`page`/`type`）。

<a id="environment-matrix"></a>
## 2. 环境矩阵

| 依赖 | 最低要求 | 用途 | 缺失时表现 |
|---|---|---|---|
| Python | 3.10+（仅标准库） | 排版、时间轴解析、全套 Python 门禁 | 构建期无法运行 |
| Node.js | 20+ | `notebook-video.mjs` / `make-video.mjs` / Remotion | 无法运行 CLI 与渲染 |
| FFmpeg / FFprobe | PATH 可用 | 拼表、响度归一化、转码、帧流畅度/曝光/静音检测 | 渲染前/后门禁与合流失败 |
| Chromium / Chrome | Remotion 缓存或 `REMOTION_BROWSER_EXECUTABLE` | `--stills` / `preview` / `--render` 浏览器渲染 | 无法出图/出片 |
| `edge-tts`（可选） | Python CLI 或 `--engine=file` | 生成中文配音与词级时间 | 无真实配音时 `--render` 自动阻断 |

- **自检命令**：`node scripts/notebook-video.mjs check-deps` 与 `capabilities`（`--json` 不支持时退码 1）；预下浏览器运行 `prepare-browser`。
- **依赖与资源跨工程复用**：多视频工程优先复用本地用户缓存目录（`NOTEBOOK_VIDEO_CACHE_DIR`，默认操作系统标准缓存路径）下同 `package-lock.json` 哈希的 `node_modules`、`npm-cache`、已有的 `chrome-headless-shell` 渲染浏览器与校验过 `sha256` 的字体文件，缺什么才按需下载一次并写入共享缓存（停用共享依赖链接可设 `NOTEBOOK_VIDEO_SHARED_DEPS=0`）。
- **常见隐性故障**：交付自动加 `--require-budoux`，缺 `budoux` 直接拦截而非静默跳过；手作皮肤缺 Noto Serif SC 时先 `notebook-video fonts --serif`。

<a id="cross-platform-compatibility"></a>
## 3. 跨平台兼容契约

- 统一入口为 `node scripts/notebook-video.mjs` 与 `node scripts/make-video.mjs`（Windows 同步提供 `.cmd`）；所有 Python 子进程强制开启 `PYTHONUTF8=1` 与 `PYTHONIOENCODING=utf-8`，路径拼接统一使用 `path.join` / `pathlib.Path`。

<a id="windows-compatibility"></a>
## 4. Windows 专项说明

- CLI 通过随 Node 安装的 `npm-cli.js` 执行 npm（避免 Node 20+ 直接 `spawn('npm.cmd')` 报 EINVAL），禁止在 Windows 使用 `npx remotion` 或把渲染工程放在云同步目录；自动加载 `scripts/windows-hide-console.cjs` 与 `rmSync(..., {maxRetries: 5})`。
- **排错**：命令找不到重开终端并跑 `check-deps`；PowerShell 拦策略改用 `node scripts/...` 或 `.cmd`；杀毒锁文件清当前工程 `node_modules` 重装，勿跨系统复制；路径过长移近盘符根目录。

<a id="performance-design"></a>
## 5. 性能与断点续渲

- **低成本验证梯次**：`--stills` 单浏览器会话按关键帧出接触表（成本远低于整片）；局部看动效用 `notebook-video preview <工程> --seconds=30`，全片抽检用 `sweep`。
- **渲染控制**：`scripts/render-lock.mjs` 防同工程并发写入；中断用 `render ... --resume` 续渲；可通过 `REMOTION_CONCURRENCY`、`NOTEBOOK_VIDEO_CRF`（默认 `18`）、`NOTEBOOK_VIDEO_X264_PRESET`（默认 `veryfast`）调节负载与编码速度。
- **轻量重出**：仅换封面用 `notebook-video poster`，重出字幕封面用 `deliver`，清理可重建产物用 `clean`（加 `--yes` 删除）。

<a id="dependency-policy"></a>
## 6. 依赖政策

- `scripts/*.py` 严禁引入三方强制依赖，只用 Python 标准库（`faster-whisper`、RapidOCR 为可选）。
- 前端依赖锁定在 `assets/lecture-template/package-lock.json`，**新增 npm 依赖须先获用户同意**。中文断行必须用 `fitChineseTextOnNLines`（禁用 `@remotion/layout-utils` `fitTextOnNLines`）。
- 字体（LXGW WenKai Lite、Noto Serif SC、Clash Display）按需校验 `sha256` 下载，支持 `NOTEBOOK_VIDEO_FONT_BASE_URL` 等镜像变量；离线时 Clash 自动回落 Space Grotesk 并提示 P1。

<a id="remotion-architecture"></a>
## 7. Remotion 架构契约

- 主合成入口 `assets/lecture-template/src/index.tsx` 的 `NotebookVideoFilm`，固定 `FPS`（30）、画布 `2560×1440`（内部 1920×1080 舞台缩放，`make-video` 默认 `--scale=1` 输出 2560×1440，可用 `--scale=0.75` 输出 1920×1080）。`remotion.config.ts` 关闭 sourcemap 并剥离三方源码注释以精简 bundle。
- 浏览器门禁共用 `layout-probe.tsx`，严禁使用随机数、系统时间或非确定性异步状态，保证同帧两次渲染像素完全一致。

<a id="skill-workflow"></a>
## 8. 完整工作流

1. **选题与讲稿**：写清核心结论与 `$asks`，按 [narration.md](narration.md) 写讲稿；手作路线按 [director.md](director.md) 写 `treatment.json` 并先搜 `commons-search.py` 图库。
2. **建工程与静帧检查**：`new-project` → 填好 `story.json`（含可复用同名 `.treatment.json`）→ `make-video ... --stills`。
3. **读报告与事实复核**：看 `renders/report.md` 首屏成片摘要与评审状态（手作建议新会话按 [rubric.md](rubric.md) 独立评分，组件可选）、`renders/gates.json` P0 归零，跑 `validate-facts <工程> --review`。
4. **配音与时间重排**：跑 `notebook-video tts <工程>` 生成旁白后重跑 `make-video` 对齐词级时间轴。
5. **用户同意后交付**：展示静帧与报告获用户确认后执行 `make-video <工程> --render <输出>.mp4`，交付 MP4、`renders/captions.srt`、`renders/poster.jpg` 与 `CREDITS.md`。
