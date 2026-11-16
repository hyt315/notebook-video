# 技术：auto 引擎、环境、跨平台与性能

auto 路线（story.json → compose）的引擎行为、运行环境、Windows / 跨平台和渲染性能。

本篇各节：

- [auto 引擎：story.json → 成片](#auto-engine)
- [环境矩阵：这台机器能出什么片](#environment-matrix)
- [Cross-platform compatibility contract](#cross-platform-compatibility)
- [Windows-specific compatibility notes](#windows-compatibility)
- [Performance design contract](#performance-design)
- [依赖政策：什么能引，什么不能引](#dependency-policy)
- [Remotion architecture contract](#remotion-architecture)
- [完整工作流（原 SKILL.md 正文：路线、五步、预览与体检、交付、引擎保证）](#skill-workflow)

<a id="auto-engine"></a>

> 注：auto 路线（story.json + 蓝图 + `make-video`）是**主路线**；要逐镜手调版面时再改写成手写场景（逃生舱，见 SKILL.md）。`statement` 不再是默认版式，它渲染成一张 默认组件风格的卡片而不是满屏大字页；没有章节卡 / 章节进度条。

## auto 引擎：story.json → 成片

`scripts/compose-story.py` 把纯内容的 story.json 变成可渲染工程；`src/auto.tsx` 的 `AutoShot` 只负责画。
几何全部在 Python 里算（门禁也在那里跑），所以弱模型写不坏版面。`scripts/make-video.mjs` 把整条链串起来。

### story.json

```json
{
  "title": "…", "theme": "flat", "kicker": "栏目", "header": "标题 / EN", "headerSub": "副标题",
  "glossary": {"术语": "≤18 字的释义"},
  "protect": ["字幕里不许切开的短语"],
  "chapters": [{"title": "章名", "shots": [{"role": "hook", "layout": "statement", "lines": ["…{{词}}…"], "content": {…}}]}]
}
```

`role`（可选）∈ hook / pre / breakdown / example / misconception / recap —— 决定叙事动作（`move`），蓝图已填好。

**保护短语**：字幕断句时不能切开的词。compose 自动收这几样东西里**真出现在台词里**的词：`subject_of_film`、每个线稿 / 墨图（`content.ink`）/ 页内示意图（`content.figure`）的 `label` 与 `parts` 的值（2–8 个字）。收完还是空的，compose 直接报错，请在 story.json 顶层写 `"protect": ["词1", "词2"]`。

### 字幕与时间（无 TTS）

| 规则 | 值 | 修法 |
|---|---|---|
| 读速 | 4.5 字/秒（英文 / 数字每 2 个字符算 1 字） | 自动：镜头时长 = 台词时长 |
| 每行 | ≤16 字 | 自动：在标点 / 中点最近的安全位置劈开；不劈 `{{术语}}`、`protect`、英文单词、数字 |
| 停顿 | 逗号 +150 ms、句末 +120 ms、行间 220 ms、镜间 320 ms | — |
| 章节呼吸 | 900 ms（章节引导卡在这段里出现） | — |
| 镜头边界 | 下一镜首句前 160 ms；章节首镜从呼吸开始 | 不再出现「上一镜尾部空等」（演示片 S6/S8 的问题） |

### 关键词同步

`{{词}}` → 在本镜元素里找（id、文字、柱名、代码行、步骤名、面板标题，忽略空格）；优先具体件（代码行、柱、节点、条目、选项、数字、面板）。
找不到 → 在段落（statement / define / note）里找短语，整块元素用 默认组件风格的强调（强调色描边 + 轻微抬升，配合推近）；不再画下划线 / 底色带。
`{{词|id}}` 直接指定。时刻 = 该词在字幕里的那一拍。元素出现晚于点名 → 自动提前到点名前 6 帧。

### 相机路径

1. 全景：所有元素的外接框取进安全框（`SAFE = 130,196 → 1790,862`），内容小于内容带 60% 时最多放大到 1.18。
2. 视线连续：上一镜最后的注视点（屏幕坐标）→ 本镜第一个元素先摆在那里，30 帧内滑到全景。
3. 每个关键词：推近到该元素（≤1.32 倍，<1.08 就只高亮不推）；**取景搜索**：逐级降倍数、横纵平移，
   直到没有任何文字元素被取景窗切成两半（同时按 ×1.035 再验一次，给运行时的慢推和微漂移留余量）。
4. 限速：屏幕位移 ≤28 px/帧、缩放 ≤0.012/帧（16–34 帧一段）；同一时刻只有一个主运动；同一元素连续点名只推一次。
5. 回全景：离下一个关键词还有 >75 帧才回。
6. 镜尾：最后一个事件到镜尾 >36 帧 → 自动加 3% 收束慢推。运行时永远叠加微漂移（缩放 ±0.5%、位移 ±5 px）和 1.5% 慢推。

### 自动修 vs 报错

| 情况 | 处理 |
|---|---|
| 字幕 >16 字 | 自动拆行 |
| 文字放不下 | 先换行（标点优先、避孤字），再降字号到 32px 地板；还不行才报错，写明要删到几个字 |
| 字号 <32 | 自动放大 |
| 同屏强调 >3 | 多出的降为正文 |
| 相邻同版式 | statement / number / define 自动换变体；其他只提示 |
| 推近会切字 | 自动降倍数 / 平移；实在不行只高亮不推 |
| 释义气泡挡字 | 换位置（下 / 上 / 右 / 左 / 角落）；都挡就省略并提示 |
| 关键词在画面上找不到 | **报错**，列出可用 id |
| 蓝图占位符没填 | **报错** |

### 软建议（不拦）

一镜一概念（>7 个新元素或 >4 个关键词目标）、每镜字号 >3 种、图标预算（每镜 1 / 每分钟 4）、
「装饰多文字少」（装饰 ≥3 且文字 <12 字 → 精简装饰或换 define / list）、连续 3 镜同一节奏、卡片版式的留白。

### 定制画面（逃生口）

见 SKILL.md 第 5 步与 `src/custom/RequestLane.tsx`。`CustomProps = {f, shot, el(id) → {in, hi, el}, line(i), C}`。

### 门禁分工

make-video 的硬门禁：`validate-shot-motion`、`validate-presentation`、`validate-audio-levels`、
`validate-caption-sync`、`validate-semantic-breaks`、`tsc --noEmit`（帧参数名与漏传），渲染期 `CaptionFitGate` / `CardFitGate` / `OverlapGate` / `ClippingGate`，
成片 `validate-motion-gaps`。`validate-composition`（骨架 / 组件多样性）是为手写场景设计的结构门禁，auto 片只作参考输出。

<a id="environment-matrix"></a>

## 环境矩阵：这台机器能出什么片

`notebook-video capabilities` 把环境判成三档。三档不是"好/中/差"的评分，而是**用户会看到什么差别**。

| 判定 | 含义 | 用户会遇到的 |
|---|---|---|
| `full` 全能力 | 硬依赖齐、有带 WebGPU 的 Chromium、字体齐 | 卷页是真卷页；语义断句生效 |
| `degraded` 折页降级 | 能出片，但没找到带 WebGPU 的 Chromium | `pageturn` / `peel` 退成 CSS 折痕翻页；片照出，只是没有纸背弧面 |
| `unsupported` 不支持 | 缺 ffmpeg / ffprobe / Python / npm，或 Node < 20 | 连合成都做不了。每条缺项都打印出补它的命令 |

### 怎么自检

```bash
node scripts/notebook-video.mjs capabilities          # 人读
node scripts/notebook-video.mjs capabilities --json   # 给脚本用；unsupported 时退码 1
```

`--json` 的字段：`platform` / `node` / `level` / `blockers[]`（每项含 `fix`）/ `capabilities` /
`pageTurn` / `fonts` / `budoux` / `concurrency`。

### 已验证与未验证（别把下表当成"三平台都测过"）

| 平台 | 状态 | 依据 |
|---|---|---|
| Windows 11 x64 · Node 22 | **已实测**（2026-11-02） | `capabilities` → `full`；整片渲染链路此前完整跑通（约 3 分 25 秒）；2026-11-02 的 `tests/test_capabilities.py` 锁住判定逻辑 |
| macOS | **未实测** | 只做了代码路径审查：`findPython` 认 `python3`；`npmInvocation` 非 Windows 分支走 `npm`；字体下载走 `https` |
| Linux | **未实测** | CI 在 `ubuntu-latest` 上跑单测与门禁，但**不跑真实渲染**（无 GPU、无 Chromium 下载），所以只证明"脚本能跑"，不证明"片能出" |
| 低配机（4 核 / 8 GB） | **未实测** | `suggestedConcurrency()` 会把它压到 2–3；但没有实测帧率与内存峰值 |

未实测的三行，谁有条件谁补：跑完 `capabilities` + 一次 `preview`，把 `level`、耗时、峰值内存记进上表。
在那之前，**本文件不承诺这三个平台的表现**。

### 已知的"能出片但不对"的陷阱

- **BudouX 未装**：语义断句会以 SKIPPED 形式跳过，rc 仍是 0。交付路径带 `--require-budoux`，
  这时会**失败**而不是静默跳过——这是刻意的：宁可拦住，也不要交出一份"看起来检查过"的字幕。
- **缺 NotoSerifSC**：手作皮肤（journal / papercut / archive）渲染时 Chrome 抛网络错误（报错里不写"字体"两个字），
  报错里不会提"缺字体"。`capabilities` 的 `fonts.serif` 就是提前看这个。
- **缺 ffmpeg**：`validate-video` 与音轨合成都不可用，但 `compose` 仍能跑完写出工程——
  于是"排版成功"容易被误当成"能出片"。

<a id="cross-platform-compatibility"></a>

## Cross-platform compatibility contract

### Non-negotiable parity

macOS and Windows must use the same Remotion source, package lock, fonts, audio, manifests, component tree, timeline, codec arguments and QA thresholds. Platform support may change only command launch, executable discovery and filesystem operations.

### Universal command

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" --help
```

macOS/Linux may use `.sh` aliases. Windows may use `.cmd` aliases. Both delegate to the same `notebook-video.mjs`.

### Requirements on both systems

- Node.js 18 or newer with npm;
- Python 3;
- FFmpeg with `ffmpeg` and `ffprobe`;
- network access for the first npm install and Remotion browser preparation, unless dependencies and the tested browser are already present.

Run:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" check-deps
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project "./notebook-video-project"
node "<SKILL_DIR>/scripts/notebook-video.mjs" prepare-browser "./notebook-video-project"
```

### macOS notes

Use Terminal with the universal Node command; executable permission on `.sh` files is optional because the Node entry does not depend on it. Do not copy `node_modules` from Windows. Install dependencies on the Mac through the launcher. On Apple Silicon and Intel, npm selects the native packages from the pinned lockfile.

### Windows notes

Command Prompt and PowerShell are both supported. The `.cmd` wrapper does not require changing PowerShell execution policy. Python is detected as `py -3`, `python` or `python3`. Do not copy `node_modules` from macOS. Keep rendering projects outside OneDrive or other sync folders to avoid file locks.

### Paths

Always quote paths. Spaces and non-ASCII names are supported, but short local paths reduce Windows long-path and antivirus problems. The launcher accepts either slash style.

### Rendering browser

The default is Remotion's tested browser, prepared by `prepare-browser` or automatically during render. This provides the best visual parity. In a restricted environment, set `REMOTION_BROWSER_EXECUTABLE` to an existing compatible browser executable before `prepare-browser` or `render`. A manual override is an environment workaround, not a different rendering engine, and should be followed by the full visual QA.

Examples:

macOS/Linux:
```text
export REMOTION_BROWSER_EXECUTABLE="/absolute/path/to/chrome"
```

Windows Command Prompt:
```text
set REMOTION_BROWSER_EXECUTABLE=C:\absolute\path\to\chrome.exe
```

Windows PowerShell:
```text
$env:REMOTION_BROWSER_EXECUTABLE = "C:\absolute\path\to\chrome.exe"
```

### Output parity

The launcher uses identical Remotion and FFmpeg settings on both platforms: H.264 video, 2560×1440, native 30fps, normalized narration near -16 LUFS, 48kHz stereo AAC at 192kbps and `faststart`. Run the same video QA after every render regardless of operating system.

<a id="windows-compatibility"></a>

## Windows-specific compatibility notes

### Contents

- [Goal](#goal)
- [Supported entry point](#supported-entry-point)
- [Required applications](#required-applications)
- [Paths](#paths)
- [Python launcher differences](#python-launcher-differences)
- [npm and native packages](#npm-and-native-packages)
- [Rendering browser](#rendering-browser)
- [FFmpeg output parity](#ffmpeg-output-parity)
- [Common Windows failures](#common-windows-failures)

The binding two-platform contract is `technique.md#cross-platform-compatibility`.

### Goal

Windows support must not change the Remotion component tree, scene timing, fonts, assets, codec settings, subtitle geometry, physical-motion quantization or final aesthetic. Only the command-launch and filesystem layer differs by operating system.

### Supported entry point

Use the cross-platform Node launcher from Command Prompt, PowerShell, macOS or Linux:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" --help
```

Windows also includes a Command Prompt wrapper that does not require changing PowerShell execution policy:

```text
"<SKILL_DIR>\scripts\notebook-video.cmd" --help
```

Every subcommand (`check-deps`, `new-project`, `sync`, `render`, `validate-video`, `package`, `prepare-media`, …) goes through this one wrapper, e.g. `"<SKILL_DIR>\scripts\notebook-video.cmd" new-project .\my-video`. The only other wrapper is `make-video.cmd`.

### Required applications

Make these commands available on `PATH`:

- Node.js 18 or newer, including npm;
- Python 3, exposed as `py -3`, `python`, or `python3`;
- FFmpeg, including `ffmpeg` and `ffprobe`.

A separate `zip` program, Bash, GNU `sed`, `grep`, `awk`, `install`, `cmp`, `cp` or `chmod` is not required on Windows. Packaging uses Python's standard `zipfile` implementation.

After installation, close and reopen the terminal before running:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" check-deps
```

### Paths

Always quote paths. The launcher accepts spaces, non-ASCII folder names and either slash style. Prefer short project paths when possible, for example:

```text
D:/VideoProjects/notebook-video-project
```

Do not create the project inside a cloud-sync folder while rendering. File locking by OneDrive or antivirus software can interrupt Chromium, npm or FFmpeg temporary files. Copy the finished source ZIP into the sync folder after packaging instead.

### Python launcher differences

The Node launcher automatically tries these commands:

1. Windows `py -3`;
2. `python`;
3. `python3`.

Do not hard-code `python3` in Windows workflows.

### npm and native packages

The pinned `package-lock.json` already contains the Remotion, Rspack and esbuild Windows x64 packages. Run the normal project creation workflow and let the launcher execute `npm ci`. Never copy an existing `node_modules` directory from macOS or Linux to Windows; native packages must be installed on the current operating system.

### Rendering browser

Prepare the pinned Remotion browser after project creation:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" prepare-browser "D:/VideoProjects/notebook-video-project"
```

Remotion manages its rendering browser. If a restricted network prevents the browser binary from being prepared, resolve that environment constraint rather than changing the visual engine. The optional network shim remains opt-in through `REMOTION_USE_NETWORK_SHIM=1` and does not alter the rendered component tree.

### FFmpeg output parity

The cross-platform launcher invokes the same FFmpeg arguments on all systems:

- H.264 video from Remotion is stream-copied;
- the copied stream carries one self-consistent color contract — `pix_fmt=yuv420p`, `color_range=tv`, `color_space=bt709`, `color_transfer=bt709`, `color_primaries=bt709`;
- narration is normalized toward -16 LUFS;
- 48kHz stereo AAC at 192kbps;
- `faststart` is enabled;
- final QA verifies H.264/AAC, 2560×1440, native 30fps, duration, loudness, true peak and black frames.

Therefore Windows adaptation must not produce a different visual style or timeline.

#### Why the color contract is pinned

Remotion's own default is `--color-space=default`, which emits no color flags at all: the encoder writes `yuvj420p` (full range) with `color_space=bt470bg` and `color_transfer`/`color_primaries` missing. Players that find no transfer/matrix fall back to BT.601 and interpret a full-range signal as limited range, so saturated colors shift slightly on strict players.

Two steps are required, in this order, because neither alone is enough:

1. `--color-space=bt709` on the Remotion render. It passes `-colorspace:v bt709 -color_primaries:v bt709 -color_trc:v bt709 -color_range tv` **and** (since `@remotion/renderer` 4.0.83) really converts the pixels to limited range through `zscale=matrix=709:matrixin=709:range=limited`. Without this step the frames stay full-range, and merely re-tagging them would expand the contrast.
2. A `h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0` bitstream filter on the copy, applied in place by `scripts/notebook-video.mjs`. FFmpeg ignores `-color_primaries`/`-color_trc` on a copied stream ("has not been used for any stream"), and Remotion's own final stitch re-muxes with `-c:v copy` the same way, so `--color-space=bt709` alone still leaves `color_primaries` and `color_transfer` reported as `unknown`.

Verified on `@remotion/cli` 4.0.526 and Windows FFmpeg: a 30-frame `render-range` and a full `render` both report `yuv420p / tv / bt709 / bt709 / bt709`, and a decoded frame matches the Chrome screenshot pixel-for-pixel within ±1 on a neutral background.

### Common Windows failures

#### `npx remotion` hangs and has to be killed

Symptom: `npx remotion ...` never returns. The process burned 2.3 seconds of CPU over 15 minutes, spawned no child process and printed nothing at all, so it could only be killed.

Cause: `npx` adds a package-resolution layer that this workflow does not need. The launcher, the `.cmd`/`.sh` wrappers and the template's `npm run render` / `npm run still` scripts all resolve the already-installed local CLI instead, which costs nothing extra. When the local `remotion` cannot be resolved, `npx` has to reach the registry, and that is the step that waits without output — the exact "low CPU, zero output, no children" shape above. Measured on this machine: in a project that already has `node_modules`, `npx remotion --version` returns in 1.9s (Git Bash), 1.6s (cmd.exe) and 3.1s (PowerShell) — no faster than the local CLI; in a directory without `node_modules` it either fails fast with the npm error "could not determine executable to run" (2.3s) or retries silently for ~71s before giving up with an npm ECONNREFUSED error when the registry is unreachable. There is no scenario in which `npx` is the better call.

Correct command — call the local CLI directly and point it at the already-cached browser, which bundles in about 2 seconds:

```text
cd "<PROJECT_DIRECTORY>"
node node_modules/@remotion/cli/remotion-cli.js render src/index.tsx NotebookVideoFilm renders/out.mp4 --browser-executable="%LOCALAPPDATA%\remotion-browser\chrome-headless-shell\win64\chrome-headless-shell.exe"
```

`scripts/notebook-video.mjs` already does exactly this (it also falls back to that cached browser automatically on Windows when `REMOTION_BROWSER_EXECUTABLE` is unset), so prefer `node "<SKILL_DIR>/scripts/notebook-video.mjs" render ...` or `notebook-video.cmd render ...`. Never rewrite the documented workflow as `npx remotion ...`.

#### Command is not recognized

Reopen the terminal after installing Node, Python or FFmpeg, then run `check-deps` again. Confirm the application directory was added to the user or system `PATH`.

#### PowerShell blocks scripts

Use `node scripts/notebook-video.mjs ...` or the `.cmd` wrapper. Neither requires changing PowerShell execution policy.

#### npm installation fails with locked files

Close Remotion Studio, editors and Explorer preview panes that are using the project. Delete only the project's `node_modules` directory and run render again; do not copy `node_modules` from another operating system.

#### Very long path error

Move the skill and project closer to the drive root. Avoid deeply nested cloud folders. The source package preserves relative project paths, so moving the folder does not change the film.

#### Antivirus blocks Chromium or FFmpeg

Allow the installed Node, Remotion browser and FFmpeg executables, or render in a trusted local working directory. Do not disable asset validation or switch renderers to bypass the block.

### make-video

`node scripts\make-video.mjs story.json .\my-video --stills`（或 `scripts\make-video.cmd`）。全程只用 Node 的 `spawn(shell:false)` + `path.join`，
Python 按 `py -3` → `python` → `python3` 顺序查找，ffmpeg 需在 PATH 上；不依赖 bash / sed / 符号链接。`npm` 在 Windows 上调用 `npm.cmd`。

<a id="performance-design"></a>

## Performance design contract

### Contents

1. Frame-rate policy
2. Scene lifetime
3. Motion implementation
4. Static surfaces and measurement gates
5. Concurrency
6. Fast iteration
7. Acceptance rules

### 1. Frame-rate policy

Use one native frame rate through the whole default pipeline:

- motion: 30fps;
- Remotion composition: 30fps;
- H.264 delivery: 30fps.

Do not author 30 unique states and export them as duplicated 60fps frames. A 60fps container is allowed only when the visible motion is also authored at native 60fps, such as very fast camera movement, dense particles, real 60fps footage or an explicit user request. In that mode, update timing, duration, captions, audio cues and validation together; never use post-export frame duplication as a quality upgrade.

For an intentional stop-motion beat inside a 30fps film, quantize only that component to 15fps so each pose holds for two frames. Do not lower the whole composition.

### 2. Scene lifetime

Unmount scenes that cannot contribute pixels to the current frame. Do not keep a whole film mounted and hide inactive scenes with `opacity: 0`.

Use frame guards or short overlapping scene ranges. Mount one scene during normal playback and at most two during a transition. Keep shared chrome, subtitle, audio and static background outside scene guards.

The canonical exemplar uses global-frame guards because its scene components consume global design-time frames. If using Remotion `Sequence`, pass local time deliberately and do not accidentally shift global cue constants.

When extending duration with a timeline scale, use one scaled design-frame helper for **both** scene guards and internal motion. Raw delivery frames may not be used by a mount condition. Scale action-audio sequence starts through the same conversion. A scene that is visually scaled but mounted against raw frames will disappear before the film ends even though its internal animation is correct.

### 3. Motion implementation

Keep stable layout coordinates in `left` and `top`. Express per-frame movement through `transform: translate3d(...)`, combined with rotate and scale in one transform string. Prefer opacity and transforms over per-frame changes to `left`, `top`, `width`, `height`, margins or grid tracks.

Do not add `will-change` to every element. Use it only on a few long-lived moving layers when profiling shows a benefit. Preserve exact slot occlusion and z-order even when converting movement to transforms.

### 4. Static surfaces and measurement gates

Keep paper texture, grade, grid and fixed shadows deterministic and static. Do not animate noise. Reuse CSS gradients or pre-render a static bitmap only when it is visually identical at 2560×1440.

Wait for fonts and media before rendering. Keep the asset gate. Measure every subtitle after the exact font loads, then unmount the off-screen measurement tree after it passes. Never remove validation work merely to shorten startup.

### 5. Concurrency

Default to half the available logical CPUs, clamped to 2–6 workers. Higher concurrency can slow a 2K browser render through CPU, memory and encoder contention.

To pick a worker count, run a short `preview` window two or three times with different `REMOTION_CONCURRENCY` values and compare the `Done in Ns` line (a 30-second window is enough — the opening is representative for throughput). Export `REMOTION_CONCURRENCY` with the fastest setting to reuse it. Do this once per machine or after a major environment change; benchmark a representative dense range manually if the opening is unusually simple.

### 5.5 Where the time goes

Every `render` appends one line to `<project>/renders/render-log.jsonl`: stage milliseconds, frames, concurrency, scale, whether the page-curl path ran and how many segments it rendered, whether `--resume` was used, and the state of the run (`ok` / `cancelled` / `stalled` / `process-error`). Failures are logged too — the `stage` field is the breakpoint.

Read it back with:

```bash
node scripts/notebook-video.mjs timings <project> [--state=ok|failed|stalled|cancelled|all]
```

That prints median / p95 / range per stage, so "this change made it faster" is a number, not an impression. A single render is not evidence: compare at least three runs of the same fixture, and check `resumed` and `fx.bundleCount` before believing a drop — a warm cache and a skipped bundle look exactly like an optimization.

Stage names are stable and mean what they say: `prepare` (fonts + asset sync), `fx-probe`, `fingerprint`, `fast` / `render` (the Remotion pass), `bundle`, `segments`, `splice`, `tag`, `loudprobe`, `finalize`.

### 6. Fast iteration

Use `render-range` for changed scenes, subtitle checks and motion reviews. Keep scene boundaries in a manifest or storyboard so review ranges are reproducible. Do not render the full film after every small edit.

For long productions, keep scenes modular so unchanged sections can later be rendered and assembled independently. Treat segment concatenation as an advanced workflow: all segments must share codec, resolution, frame rate, pixel format and audio format, and transitions must not cross segment boundaries. Always perform one full final render unless a validated concat pipeline is already present in the project.

### 7. Acceptance rules

Reject a speed optimization if it changes layout, type, palette, subtitle geometry, object count, semantic timing, physical occlusion, audio synchronization or final 2K sharpness.

Accept a tiny cadence difference only when moving from the obsolete 20fps stepped pose system to native 30fps motion; this change should be smoother, not rougher. Compare at least one dense motion range and one subtitle-heavy range before final delivery.

<a id="dependency-policy"></a>

## 依赖政策：什么能引，什么不能引

> 这份文件是依赖边界的**唯一定源**。与其它文档冲突时，以本文为准。
>
> 它存在的原因是一次真实的、代价很大的误读：技能原本写着一句「零第三方依赖」（本意只是说
> `scripts/` 下的 Python 脚本不许有依赖），却被执行 AI 读成了「整个技能不许用任何第三方库」。
> 结果是所有成熟组件都不敢碰，画面元素全部手写 SVG——**恰好做出了最难复现的结果**，
> 而这条规矩的本意正是"任何环境都能复现"。本文件用来钉死这个边界。

### 一、一句话边界

> **禁的是「按次付费、结果不可复现」的生成式模型；不是开源库。**

### 二、三类依赖，三种纪律

| 类别 | 例子 | 纪律 |
|---|---|---|
| ❌ **禁止**（默认路线） | 生图模型 API、生视频模型 API、任何按次计费的生成服务 | 默认路线**绝不用**。它们按调用付费，且同一提示词两次返回不同画面，风格锁不住。技能不调用它们；需要真实图片时用用户提供 / Commons / 授权图片，见 [director.md#visual-director](director.md#visual-director) |
| ✅ **允许，且鼓励** | 开源、免费、可被 lock 文件锁死版本的 React 库 | **直接 `import` 用，不需要额外授权、不需要"先证明现有件做不到"**。装已在模板 `package.json` 里，`npm install` 一次到位 |
| ⚠️ **需授权** | 清单之外的新库 | 先问用户，同意后才加进模板 |

**同目录的本地模块不算依赖。** `scripts/*.py` 之间可以互相 `import`（`gatelib.py`、`story_camera.py`、
`gates_compose.py` 都是这么来的）。"只用 Python 标准库"说的是**不许引第三方包**——
把一个 1500 行的文件拆成几个小文件，不违反这条，也不需要授权。

#### `assets/vendor/` 是唯一允许分发第三方代码的地方

正常情况下第三方库只进 `node_modules`，仓库里不留副本（见 `NOTICE` 第 8 条）。
唯一例外是**技能自己要用、但 `npm install` 拿不到**的东西——因为技能不发行 `node_modules`：

| 目录 | 是什么 | 为什么必须在仓库里 |
|---|---|---|
| `assets/vendor/budoux/` | BudouX 0.9.2 的简体中文切片（Apache-2.0，约 80 KB） | 字幕断句规则要分词。没有它，新克隆的仓库里这条规则**静默跳过**，而"跳过"在报告里几乎等于"通过" |

进这个目录的条件（三条全中才允许）：① 许可证允许再分发；② 体积在百 KB 级、且不可裁；
③ 少了它某道门禁会**假通过**（不是"体验差一点"，是"报绿但没验"）。

进去之后必须做四件事：许可证原文随包放、`NOTICE` 登记版本与版权、`assets/vendor/README.md`
写清来源/改动/升级步骤、补一条守护测试（删目录、覆盖入口、丢 `type":"module"` 都必须立刻失败）。

### 三、三条判据（拿不准时按顺序自问）

1. **要钱吗？** 按次计费 / 按量计费的生成式 API → 禁止。免费开源 → 通过。
2. **能复现吗？** 同一输入两次跑出不同结果（模型采样、随机种子没固定）→ 禁止。给定种子/帧号必然得到同一结果 → 通过。
3. **可能被 lock 锁死版本吗？** 能写进 `package-lock.json` → 通过。只能调远程接口、版本随时变 → 禁止。

三条全过才叫"允许"。**注意：第 2 条和第 3 条与"是否第三方"无关**——自研代码同样会因为
`Math.random()` 或 `setTimeout` 而不可复现。判断的对象是**行为**，不是**来源**。

### 四、模板已内置的依赖（无需授权，直接用）

`assets/lecture-template/package.json` 已声明以下依赖，`new-project` 之后一次 `npm install` 全部就位。

#### 4.1 UI 与结构（解决"技能里根本没有这类形态"）

| 包 | 解决什么 |
|---|---|
| `shiki` + `@shikijs/langs` | **代码语法高亮**（`HighlightCode`）：VS Code 同款 TextMate 语法。用**同步核心** `createHighlighterCoreSync` + **JS 正则引擎**（不加载 WASM、不走 Promise、不需要 `delayRender`，Windows 下也没有 `.wasm` 路径问题）；语言按需 import 8 个；**主题由调色板生成**（`src/components/shiki.ts`），所以 flat / cel 的语法色永远跟皮肤一致。MIT |
| `lucide-react` | **线条图标**：`LineIcon`（kit，26 个 kind）与 `TopicIcon` / `IconWall` 的线条字形。1,500+ 字形、同一套 24 视窗描边语法、`strokeWidth` 可调。ISC |
| `simple-icons` | **品牌 logo**（React / Node.js / Python / Docker / Git / npm / GitHub …）：单色 path 数据，颜色由皮肤给。CC0-1.0（无署名义务；**商标权仍归各品牌**，只用于指代该技术，不暗示背书） |
| `diff`（jsdiff） | **补丁计算**（`DiffView` 的 `before` / `after` 模式）：`diffLines` 给出增删行，不再手写 `-`/`+`。BSD-3-Clause |
| `flubber` | **形状变形插值**（`MorphShape`）：任意两个闭合形状重采样后一一配对，纯函数 `t → path`。MIT |
| `@visx/axis` / `@visx/grid` / `@visx/shape` | **图表的坐标轴、网格与线/面积/柱**（`Chart`）：纯 SVG、零动画、零测量（刻度字用我们自己的 `<text>`，不用 `@visx/text` 的量字）。d3 仍负责刻度与布局。MIT |
| `d3-scale` / `d3-shape` | 图表计算：数据→刻度、数据→SVG 路径。**纯数学，零渲染零动画零样式** |

#### 4.2 数据与素材计算（纯计算，全部确定性）

| 包 | 解锁什么 | 备注 |
|---|---|---|
| `d3-hierarchy` | **目录树 / 组织图 / 树状图**（`TreeView` 的 `treemap` / `pack` / `sunburst` 三个变体） | 与 `d3-scale` 同族；`hierarchy()` + `tree()` 给出每个节点的坐标。⚠️ 三个布局都是**有状态地写回节点**的，共用同一个 `hierarchy()` 根会互相覆盖——每个布局各拿一个根 |
| `d3-force` | **关系网**（`NetworkGraph`）：谁连着谁，没有层级也没有方向 | 源码级核实 `Math.random` **0 处**（用固定种子 LCG）。**必须**：初值显式给定 + 迭代次数写死 + 立刻 `.stop()` 掉内部 d3-timer；算完还要按包围盒等比归一化，否则会溢出画框（实测） |
| `d3-geo` | 地图 / 地球 / 经纬网 | **陆地数据的接线已完成**：`GeoView` 现在画真陆地轮廓，数据来自下面两行的 `world-atlas` + `topojson-client`。无数据时（或 `graticule` 单开）仍是经纬网与投影框 |
| `world-atlas` | **世界陆地的预简化 TopoJSON** —— `GeoView` 的陆地轮廓 | ISC、整包 8.2 MB（110m / 50m / 10m 各两个文件）。⚠️ **只用 `land-110m.json` 那一档**（**55 KB** / 130 条弧，2026-09-22 实测）：世界尺度下轮廓够用，50m / 10m 是国界与省界级细节，本件不需要、也不该进 bundle。**它没有国界、没有城市点、没有地名**——只有陆地块，想要国界得换 `countries-110m.json` 并另立一件（别偷偷扩 `GeoView` 的语义） |
| `topojson-client` | **TopoJSON → GeoJSON**（`feature()`），转出来的 GeoJSON 交给已装的 `d3-geo` 画路径 | ISC、68 KB、Mike Bostock（TopoJSON 作者本人维护）。本仓库只用到 `feature()` 一个函数。**类型是本地声明**（`assets/lecture-template/src/external-types.d.ts`）——**没有为它加 `@types/topojson-client`**，那是第三个包；`GeoJSON.*` 命名空间来自已声明的 `@types/d3-geo` 的传递依赖 `@types/geojson`，不额外装东西 |
| `d3-sankey` | **流量图**（转化、分流、去向） | 带宽按数值分配 |
| `d3-dsv` | 解析 CSV / TSV | **真实数据进图表的入口**——不再手写数据数组 |
| `roughjs` | **手绘风图形**（线条带手抖） | 手账风的天然契合件。**seed 固定 → 每次渲染同一笔迹**；用 `rough.svg()` 而非内部路径。⚠️ **两个实测例外**（2026-09-21，接触表 ⑭ 页同帧多渲抓到）：① `fillStyle:'dots'` 的填充器在 `dotsOnLines` 里**无条件调 `Math.random()` 两次/每点**，与 seed 无关 → **已从 `SketchStyle` 移除**（同一帧渲三次三个哈希，差异全在 dots 那格）；② `seed: 0` 是假值，roughjs 的 LCG 写成 `this.seed ? … : Math.random()`，传 0 会让**所有**填充退回真随机 |
| `qrcode` | 二维码（收尾"扫码看仓库"） | 纯计算、不联网；`QRCode.toString(..., {type:'svg'})` 输出 SVG 字符串 |
| `katex` | **数学公式**静态渲染 | 需 `import 'katex/dist/katex.min.css'`；无动画，确定性 |
| `budoux` | **中文按词组断行** | Google 出品；`loadDefaultSimplifiedChineseParser().parse(text)` 返回词组数组。用于**标题**断行（正文中文可任意字断行） |
| `@cto.af/linebreak` | **UAX #14 断行算法**（避头尾 + "拉丁/数字串内部不断"的正解） | `new Rules({string:true}).breaks(text)` → 每个断点带 `position`。MIT、60 KB、**UAX #14 / Unicode 17**、2026-03 发版、依赖树干净（`@cto.af/unicode-trie-runtime` → `fflate`，都是现代在维护的包）、纯函数无 timer/random。此前 `fittext.tsx` 手写两张字符表做避头尾，实测只是粗糙近似且**错在中英混排**：10 条真实文本里它允许 **36 个非法断点**（`在G\|itHub`、`hyt\|315`、`第三个A\|I技能`、`S\|1：`…），换 UAX #14 后 **36 → 0**（纯中文用例两者完全一致）。⚠️ **选包口径**（用户 2026-09-21 定的原则：依赖要通用、能用新的就不用旧的）：先用的是 foliojs 的 `linebreak@1.1.0`，但它**钉死 `base64-js@0.0.8`（2014 年）**、且 2022 年后没再发版 → 换成 `@cto.af/linebreak`（自述是前者那包的 refresh），实测两包在同一批文本上**断点逐一相同**，换包零行为变化（同名页面重渲逐字节一致）。另外：**不要回头试 `Intl.Segmenter({granularity:"line"})`**——`line` 粒度不在 ECMA-402 规范内，Node 24 直接抛 `RangeError` |

> **已移除**（Phase 3「能用成熟开源件就不手写」）：12 个 `@radix-ui/*` 包、`react-syntax-highlighter`（+ `@types/react-syntax-highlighter`）、`react-icons`。
> Radix 那四件（`Accordion` / `Tabs` / `ControlStack` / `OverlayFrame`）渲染期没有交互，Radix 只贡献 ARIA 外壳，
> 却带来 Portal 落到画布外、floating-ui **异步**定位（实测 8 轮渲染才稳）、Slider 的 ResizeObserver 测量三个确定性风险 → 改成纯 `<div>`，位置与状态全部由帧号算出。
> 随之显式声明了 `@types/react`（devDependency）：它以前是 Radix 的传递依赖，删掉 Radix 后 `tsc` 会找不到 React 类型。

> **实测**：这张表的 **10 个**依赖已在独立验证工程 `demo-video` 里逐个渲染验证（目录树 / 地球 / 流量图 / CSV / 手绘 / 二维码 / 公式 / 中文词组断行 / 关系网 / UAX #14 断行），全部能在各皮肤下正确读 `THEME`（当时验证时为四套，保留 flat / cel 两套）。
> **两个地图数据包（2026-09-22 加）的验证口径不同**：它们不是独立组件，而是 `GeoView` 的实现细节，所以不进 `demo-video`——验证落在**本模板自己的接触表 ⑬ 页**（`node scripts/notebook-video.mjs showcase <proj>`，然后 Read 那张接触表看图上的陆地轮廓与标记点）。
> **体积**：10 个包 + 传递依赖合计约 **12 MB**（12 MB 是 2026-09-21 对当时表里 8 个包的实测值；后来补进 `d3-force` 与 `@cto.af/linebreak`——自述 60 KB——量级不变。其中 `katex` 4.6 MB 与 `budoux` 3.2 MB 是大头，且几乎全是字体与模型数据）。地图那两个再加 **8.2 MB**（`world-atlas` 整包；实际进 bundle 的只有 `land-110m.json` 的 55 KB）+ **68 KB**（`topojson-client`）。相比之下 Chrome 无头浏览器 270 MB——**这点体积可以忽略**。（图标两包：`lucide-react` 约 36 MB、`simple-icons` 约 17 MB，都按命名导出 tree-shake，进 bundle 的只有用到的字形；比被换掉的 `react-icons` 85 MB 还小。）

> **这两个包给"新建工程"增加步骤吗？——不增加，一步都没有。**
> `new-project` 复制模板时 `package.json` 里已经带着这两行，`npm install` / `npm ci` 一次到位；数据在**打包期**随 `import` 进 bundle，所以：
> **不需要** sync 复制进 `public/`、**不需要**手工下载数据文件、**不需要**改任何配置、**不需要**额外的 lock 步骤。
> 渲染期零 IO（没有 fetch、没有 delayRender 持柄），`notebook-video render` / `showcase` / `remotion still` 每条路径都一样。
> 唯一要记住的是：**换档位（110m → 50m）改 `data.tsx` 的 import 一行**，文件已经在 `node_modules` 里，不用再装包。

#### 4.3 Remotion 官方扩展（天生帧驱动安全）

| 包 | 解锁什么效果 |
|---|---|
| `@remotion/transitions` | 20 种演示型转场：fade / slide / wipe / flip / clockWipe / iris / dissolve / ripple / zoom-blur / film-burn / book-flip / swap / crosswarp … 用 `TransitionSeries` 串联 |
| `@remotion/paths` | `evolvePath`（描线生长）、`getPointAtLength`（沿线运动）、`interpolatePath`（`MorphShape engine="remotion"` 的旧路径；默认已换 flubber）、`warpPath`、`cutPath`、`getBoundingBox` |
| `@remotion/shapes` | 参数化几何图形：圆 / 椭圆 / 矩形 / 三角 / 多边形 / 星 / Pie / 心形 / 箭头 / 对话气泡 / 星芒，`make*()` 直接给出 path 字符串 |
| `@remotion/layout-utils` | `measureText`（实测文字宽高，**准确且严格线性**：已验证 46px 时 44 字 = 2024px）、`fillTextBox`。**治卡片裁切的正解**。⚠️ **不要用 `fitTextOnNLines` 处理中文**，见第 5.1 节 |
| `@remotion/noise` | `noise2D/3D`：给同一 seed 得到同一结果，可做有机抖动、自然呼吸而不破坏可复现性 |
| `@remotion/effects` | 画布特效（WebGL2 / WebGPU）。本模板只用 `pageTurn()` 做手作皮肤的真翻页 / 揭纸转场（`src/fx.tsx`）；它要 WebGPU，缺省 Headless Shell 画不了，所以由渲染器探针决定开不开，详见 [camera.md#fx-effects](camera.md#fx-effects)。`fractalNoise()` 评估过，不进渲染期（同文件 §4） |

> 选型理由：这五个与渲染引擎同厂，**按帧驱动设计**，不存在"库自带时间动画"的冲突，是引入成本最低、
> 风险最小的一类扩展。加依赖时优先考虑这一族。
> （曾经还有第六个 `@remotion/motion-blur`——已删：它的两个再导出件**零引用**，
> 而唯一想用它表达的"速度峰值"并不在七种合法运镜意图里，装它等于给自己开一个不该用的后门。）

> **两个名字很像的包，别搞混（也别说错）**：`@remotion/media` 与 `@remotion/media-utils`。
>
> | | `@remotion/media` | `@remotion/media-utils` |
> |---|---|---|
> | 在模板 `package.json` 里声明了吗 | **有**（`<Audio>` / `<Video>` 组件，影片的音频树用它） | **没有** |
> | 它从哪来 | 直接依赖 | **`@remotion/cli` 的传递依赖**（`remotion` 本身不依赖它） |
> | 给什么 | 播放媒体元素 | 媒体分析工具函数 |
>
> `@remotion/media-utils` 实测（4.0.526，读 `dist/index.d.ts`）导出的**运行时函数有 12 个**：
> `getAudioData` · `getAudioDuration` · `getAudioDurationInSeconds` · `getWaveformPortion` ·
> `visualizeAudio` · `visualizeAudioWaveform` · `createSmoothSvgPath` · `useAudioData` ·
> `useWindowedAudioData` · `getImageDimensions` · `getVideoMetadata` · `audioBufferToDataUrl`
> ——**给的是波形/时长的数据，不是一个现成的波形或频谱组件**（包里没有 `<AudioWaveform>` 这种东西，
> 要画还是得自己画。<del>"只导出 4 个函数"是 2026-09-20 那份调研报告的错记</del>）。
> **技能没有封装它、也没有用它**：它**不在依赖清单**里（要用得先走 §二 的"需授权"），
> 而且说不出来它能替换掉哪个平淡表达（代码库里没有"用静态竖条假装声波"的写法要它来治）。
> 所以：**不要因为看到 `visualizeAudioWaveform` 这个名字，就以为技能"有波形/频谱能力"**——
> 那是这个包的函数名，不是本技能已具备的能力；也不要为它新造组件。

#### 4.4 已封装的组件（全部登记在路由表里）

| 依赖 | 封装成的组件 | 渲染验证 |
|---|---|---|
| `d3-hierarchy` | `TreeView`（目录树 / 组织图 / **矩形树图 / 圆形打包 / 旭日图**） | ✅ 接触表 ⑬⑯ |
| `d3-geo` | `GeoView`（真地图：陆地轮廓 + 经纬网 + 经纬度标记点） | ✅ 接触表 ⑬ |
| `world-atlas` + `topojson-client` | **并入 `GeoView`，不单独封件**（一个是数据、一个是解码器，画面语言仍归 `GeoView`） | ✅ 接触表 ⑬ |
| `d3-sankey` | `SankeyChart`（流量图） | ✅ 接触表 ⑬ |
| `d3-force` | `NetworkGraph`（关系网，固定迭代 + 显式初值） | ✅ 接触表 ⑯ |
| `qrcode` | `QrCode`（二维码） | ✅ 接触表 ⑬ |
| `roughjs` | `SketchFx`（手绘风，**含六种确定性 `fillStyle`**：hachure / solid / zigzag / cross-hatch / dashed / zigzag-line，即 `SketchStyle['fillStyle']` 的全部取值；`'dots'` 因内部调 `Math.random()` 已移除）+ `sketchCircleArea` / `sketchUnderline` / `sketchBox` | ✅ 接触表 ⑭ |
| `katex` | `MathBlock`（公式块） | ✅ 接触表 ⑭ |
| `d3-dsv` | 并入 `Chart` 的数据入口（`csv` prop）+ `csvToChartData()` / `csvToChartSeries()` | ✅ 接触表 ⑭ |
| `budoux` | 并入 `fitChineseTextOnNLines()`（断行优先落词组边界） | ✅ 接触表 ⑭ |
| `d3-shape` / `d3-scale` | `Chart` 的 7 个 `variant`（line / area / stack / stackExpand / stream / radar / pie），柱宽由 `scaleBand` 给出 | ✅ 接触表 ⑮ |
| `@visx/axis` / `@visx/grid` / `@visx/shape` | `Chart` 的坐标轴、网格、折线（`LinePath`）、面积（`AreaClosed` / `Area`）、柱（`Bar`）；雷达与饼仍用 d3-shape | ✅ 接触表 ⑨⑭⑮ |
| `shiki` + `@shikijs/langs` | `HighlightCode`（语法色 = 调色板生成的 TextMate 主题） | ✅ 接触表 ⑨ |
| `lucide-react` + `simple-icons` | `LineIcon`（kit）、`TopicIcon` / `IconWall` | ✅ 接触表 ⑩⑫；参考片 S3 S7（`CardHead`） |
| `diff` | `DiffView` 的 `before` / `after` 模式 + `diffToLines()` | ✅ 接触表 ② |
| `flubber` | `MorphShape`（默认引擎） | ✅ 接触表 ⑪ |
| （无依赖） | `ControlStack`（六种控件，帧 → 状态的显式表）、`OverlayFrame`（dialog / popover / tooltip / menu，钉在给定坐标）、`Accordion`、`Tabs` | ✅ 接触表 ⑨⑫⑰ |
| `@remotion/shapes` / `@remotion/paths` | `SHAPES`（含 callout / arrow / heart）+ `PathDraw showArrow`（`getTangentAtLength` 沿线朝向）；`@remotion/shapes` 的 Pie 不再封装（饼图/份额改走 `Chart variant="pie"` 与 `ProgressRing`） | ✅ 接触表 ⑩⑪⑰ |

**全部封装完成、全部有渲染记录、全部登记进路由表**——「零引用」判据无一触发。
（补记：`@remotion/motion-blur` 这一行**已整行删除**——它封装出来的两个名字从未进过任何画面，
连接触表都没上，属于本条判据的正面案例；Pie 也不再封装，理由见上一行。）

> **关于 budoux 的诚实结论**：它是**辅助不是保证**。实测它对"反推"「并返回」这类词也会切错
> （切成 `反|推该`、`并返|回断`），模型本身不够准。所以：**标题可以依赖它的断点，正文别指望**。
> 断行仍然是"能落在词组边界就落，落不了按字断并遵守避头尾"。

> **教训留档**（这条清单本来是"待办"）：技能曾累积 23 件"从未出现在任何画面里"的组件，
> 起因正是"装了/建了却没人用"。**引入依赖 ≠ 获得能力**——封装成组件 + 登记进路由表 + 真的渲染过，三件都做到才算。

#### 4.5 代码高亮：Shiki（替换 `react-syntax-highlighter` / PrismLight）

`src/components/shiki.ts` 是唯一的高亮入口，`HighlightCode` 只消费它算出的 token：

- **同步、确定性**：`createHighlighterCoreSync` + `createJavaScriptRegexEngine`。第一次渲染就拿到 token，
  不加载 WASM、不发请求、不需要 `delayRender`；结果按 `(语言, 代码)` 缓存。
- **语言按需注册**（`SHIKI_LANG_ALIASES`）：tsx / typescript(ts) / jsx / javascript(js) / python(py) /
  shellscript(bash, sh, shell) / json / diff。**不在表里的语言按纯文本渲染**（不报错、不崩）；
  要加语言：`import lang from '@shikijs/langs/<id>'`，放进 `langs` 数组，再在别名表里补一行。
- **主题不是 Shiki 自带的**：当前 `THEME.palette` 被翻译成一张 TextMate 主题（关键字 = `blueInk`、
  字符串 = `greenInk`、函数/类型/数字 = `orangeInk`、属性 = `goldInk`、注释 = `muted` 斜体、diff 增删 = `greenInk` / `redInk`）。
  文字一律用 `*Ink` 文字安全色，填充色不当字色。
- **Code Hike 没有引入**：它的 token 级过渡要靠"上一步代码状态的 DOM 快照"做 FLIP 动画（逐帧有状态、要测 DOM），
  与 Remotion 每帧独立、可乱序并发渲染的模型冲突；它还自带另一套高亮器（`@code-hike/lighter`），会和 Shiki 形成两套语法色。
  逐行聚焦（`HighlightCode`）、逐字敲出（`Typewriter`）、改了什么（`DiffView`）已覆盖讲解片的代码语法。

### 五、零依赖也能做的"炫效果"（优先做这些）

社区组件库里最抓眼的效果，**八成不需要任何依赖**——它们的底层只是 CSS/SVG 数学。做成组件时优先走这条路：

| 效果 | 实现 |
|---|---|
| 流光边框 / 渐变描边 | `conic-gradient` 旋转角绑帧号 |
| 光晕 / 聚光焦点 | 多层 `radial-gradient` + `blur` + `mix-blend-mode` |
| 3D 倾斜卡片 | `perspective` + `rotateX/rotateY`，角度绑帧号 |
| 遮罩擦除转场 | `clip-path: inset()` 按帧推进 |
| 文字闪过一道光 | `background-clip:text` + 移动的渐变遮罩 |
| 描线生长 / 路径流动 | `strokeDasharray` / `strokeDashoffset`（或 `evolvePath`） |
| 网格 / 点阵 / 噪点背景 | `repeating-linear-gradient` |
| 数字滚动 / 逐字生成 | 逐帧取整 / 取字符 |

**纪律：这些一律写成 `f(帧号)` 的纯函数**，禁止 `animation: ... infinite`、`transition`、`setTimeout`。

#### 5.1 已知地雷：库不一定适配中文

引库不是无脑照搬。**上线前必须用中文实测过**，因为有些库是按拉丁文假设写的。已知的坑：

| 库 / API | 问题 | 处置 |
|---|---|---|
| `@remotion/layout-utils` 的 `fitTextOnNLines` | 实现是 `text.split(' ')`——按**空格**分词。中文没有空格，整段被当成一个不可断的「词」，于是只能塞进一行，字号被压到 `maxBoxWidth ÷ 字数`（实测：44 字 / 738px 容器 → **16.77px / 1 行**，而正确答案是 46px / 3 行）。**它不报错，只静默给出一个极小的字号** | 改用 `src/components/fittext.tsx` 的 **`fitChineseTextOnNLines`**（自研：`measureText` + 二分 + CJK 避头尾断行）。断行必须保证**每行不超过容器宽**，否则浏览器会二次折行（实测 3 行被折成 6 行） |

**通用教训**：引入任何"处理文字"的库，先用一段中文跑一遍，把结果量出来看——不要看文档示例（示例都是英文）。

### 六、为什么不直接粘贴网上的组件库

21st.dev、Aceternity UI、Magic UI、shadcn/ui 这类**分享型组件库**（别人写好源码、复制即用）确实是最快的
"炫效果"来源，但**不能原样粘进本技能**，三堵墙：

| 墙 | 具体表现 |
|---|---|
| **Tailwind 墙** | 它们的写法是 `className="relative flex h-[500px] overflow-hidden rounded-lg border"`。本技能不用 Tailwind，样式一律是 inline style + `THEME`。粘进来类名全部不生效，画面直接塌 |
| **时间驱动墙** | 它们的动画是 `animation: 3s infinite` 或自动播放的 motion。视频按帧渲染，**同一帧可能被渲染多次**，时间驱动的动画每次结果都不同——这正是十四道门禁要防的事 |
| **审美墙** | 它们绝大多数是暗色科技 SaaS 落地页风格（黑底极光、流星、光束）。本技能的皮肤是扁平几何 / 动漫赛璐璐，硬搬会打架 |

**正确用法：取"效果配方"，不取"实现"。** 把它拆成第五节的 CSS/SVG 数学，重新用 `THEME` 上色、用帧号驱动，
然后做成**本技能自己的组件**。效果是别人的，皮肤和可复现性是我们的。

### 七、引入库之后必须遵守的组件纪律

新组件不是"直接暴露库"，而是**包一层再给场景用**：

1. **封装一层**：场景 `import` 的是 `src/components/` 里的封装件，不直接 `import` 原始库。
   理由：库是无样式的，直接引用会让每个场景写出不同的边框/圆角/阴影，违反"不得发明 per-scene 样式"。
2. **只读皮肤**：颜色 / 边框 / 圆角 / 阴影只能从 `THEME` 取，不得硬编码。
3. **帧驱动**：动画是 `f(帧号)` 的纯函数。禁止 CSS transition、`setTimeout`、`Math.random()`。
4. **高度算出来**：文字容器高度用 `fitH()` 或 `fitTextOnNLines()` 得出，禁止手写"看着差不多"。
5. **图标限定**：两个包，各管一段，**不许混着用同一个意思**：
   - `lucide-react` ＝ 线条图标。`LineIcon`（kit，26 个 kind）与 `TopicIcon` 的线条字形都来自它，
     同一套 24 视窗描边语法。`LineIcon` 的 `strokeWidth` 仍按旧的 32 视窗口径传（默认 2.2），内部换算为 ×24/32；
     `TopicIcon` 默认 1.65，两者混排笔画重量一致。
   - `simple-icons` ＝ 品牌 logo（React / Node.js / Python / Docker / Git / npm / GitHub）。只取 `path`，
     **不用 `hex` 品牌色**；按 0.84 缩一档，让实心剪影与线条图标视觉面积相当。
   **锁定的 `LineIcon` 仍是主图标语言**（卡片小标题旁）；`TopicIcon` 只用于题材性标识。
   图标**只用 THEME 给的 color**，不许用自带 fill 或多色。`react-icons` 已移除（Font Awesome 品牌是 CC BY 4.0，需署名）。
6. **进路由表**：新组件必须同时登记进 [media.md#media-routing](media.md#media-routing) 的「内容→介质」与
   「修辞动作→组件」两张表，否则会重演"组件在仓库里吃灰"的老问题。
7. **弹层不 Portal、不异步定位**：`OverlayFrame` 是父容器里的一个绝对定位 `<div>`，左上角 = 给定的 `(x, y)`
   （popover / tooltip / menu 再向下留 12px，有引线时 2px）。用 Radix 时的两个坑正是去掉它的理由：
   Portal 默认挂 `document.body`（画布之外），以及 floating-ui 的 `computePosition` 在微任务里才 resolve（实测 8 轮渲染才稳）。
   **不要再为弹层引入任何会测量或 Portal 的库**；需要锚点相对定位时，自己算坐标。
   **Toast 不要引**：它带 `duration` 计时器，与帧驱动正面冲突。
8. **不用时间驱动的动画库**：framer-motion / Motion、react-spring、GSAP、NumberFlow（Web Animations API）、
   rough-notation（CSS 动画）一律不引。所有动画只用 Remotion 的 `useCurrentFrame` / `interpolate` / `spring`。

### 八、组件总数：一条纪律，不是一个数字

**纪律：加一件 = 换掉一件。** 新效果优先做成既有组件的**参数或变体**（`Paper variant="glow"`、
`FitCard tilt={...}`），**不要为新效果新开组件**——否则"引入社区效果"会把库顶到 30 件以上，重演吃灰。
（`src/components/` 是 **27 件**：删掉 PieDraw 与 `@remotion/motion-blur` 的那两个再导出。）

**不要设一个拍脑袋的数字上限。** 实测过一遍：库的地板由两部分撑住，砍不动——

| 类别 | 件数 | 为什么砍不动 |
|---|---|---|
| 引擎 / 结构件（`validate-composition.py` 的 `STRUCTURAL` 集合：3 骨架 + `ShotCamera` `StageFrame` `PhaseRail` `CoverPanel` + `LineIcon` `CheckBadge` `PillTag` `StampBanner` `FitCard` `CardHead` `Shot`） | 14 | `validate-composition.py` 的 `STRUCTURAL` 集合就是这份名单；骨架门禁要求 ≥3 种且相邻不得重复 |
| 表意件（修辞动作各一件） | 42 | 逐对核对后，真正"同一修辞动作、两套实现"的只有 4–5 对，且每对都各有一点对方没有的能力 |

- **故本节的合规判据是「零引用」而不是「总数」**：任何组件只要**从未出现在任何画面里**（参考片或接触表），
  就是待删除项。按这条清掉过 23 件。
- 想让库"更窄"而不是"更小"：走 [media.md#media-routing](media.md#media-routing) 的**单一首选**——每行只给一个建议，
  其余标注「何时才用」。一行并列三个平级选项 = 没给建议。

> **历史教训（两条，都很硬）**：
> ① 本技能曾累积到 49 件组件，其中 **23 件（47%）从未在任何画面里出现过**，而其中 **21 件早已登记在路由表上**——
>    说明"补决策入口"不是解药，**规矩必须同时给许可**（这就是本文件存在的原因）。
> ② 反过来，"总数压到 20 件"同样不可达：逐件点算的地板是 **53 件**（`src/components/` 27 + 其余 8 个模块 26；口径 = 各模块对外 `export` 的大写 React 组件，与 [components.md#fxkit](components.md#fxkit) 的 27 件同口径，渲染期门禁件 `SlotGuard` 不算件），其中 `STRUCTURAL` 14 件豁免多样性检查；再往下就是删引擎件或在用的表意件。
>    **别对着一个数字做有损合并。**

### 九、模板 → 工程同步清单（改完模板不等于工程拿到了）

> **一句话教训（本轮实测）**：真实工程 `overview-film` 里有一份**自己的组件副本**（`src/components/`、`src/fxkit.tsx`、
> 五道渲染期门禁、主题包……都是复制过去的）。模板里的组件升级、新依赖、新接线**不会自动过去** ——
> 实测：模板的 `GeoView` 已经能画真陆地轮廓（`world-atlas` + `topojson-client`，见 §4.2），
> 而长片 `package.json` 里这两个包是 **0 处**、`src/components/data.tsx` 里也没有 `world-atlas` import，
> 所以长片至今画的是**旧版经纬网**。要长片渲出真地图，必须跑完下面这套同步。

**共享面（要同步）**：`src/components/**`（含 `fittext.tsx`）、`src/fxkit.tsx` / `media.tsx` / `stagekit.tsx` /
`skeletons.tsx` / `toolkit.tsx` / `kit.tsx` / `shotkit.tsx` / `insert.tsx`、**五道渲染期门禁所在的四个文件**
（`clipping-gate.tsx` 里的 `ClippingGate` + `CardFitGate`、`fill-gate.tsx`、`overlap-gate.tsx`、`canvas-bounds-gate.tsx`）、
`src/theme/**`、`external-types.d.ts`（本地类型声明，缺它 `topojson-client` 编译不过）、以及 `package.json` 的依赖表。
**工程私有（不要覆盖）**：`scenes.tsx`、`shots.ts`、`caption-cues.json`、`manifests/**`、`audio/**`、`public/**`、
`storyboard.md` —— 这些是这一部片子自己的内容，模板里的是"另一个片子"。

**步骤（照做即可）**

1. **先比版本串**：两边的 `src/components/index.ts` 的 `COMPONENTS_VERSION`（还有 `SHOWCASE_VERSION` /
   `SCENES_VERSION`）。不一样 = 有人改了模板没同步工程，先问清"这轮要同步什么"，别整目录乱拷。
2. **列出真实差异**：`diff -rq assets/lecture-template/src <工程>/src`。**`Only in 模板`** 的共享面文件（例：
   `canvas-bounds-gate.tsx`、`external-types.d.ts`）= 工程缺件，要新增；**`Only in 工程`** 的（例：`storyboard.md`）
   一律不动。
3. **依赖要一起搬（最容易漏的一步）**：模板 `package.json` 里新增的包必须**同时**加进工程 `package.json`，
   并在工程里跑一次 `npm install`（或 `npm install --package-lock-only` 后用 `npm ci`）让 `package-lock.json` 一起更新。
   **只拷源码不装包 = 渲染到那一帧才报"找不到模块"**，前面所有门禁都拦不住。
4. **接线别漏**：新件要挂在设计根 / 片子上才算生效（`data-design-root`、门禁的 `mode="warn" / "block"` 两档、`CardFitGate`
   的 `data-fit-skip`……）。**把组件文件拷过去 ≠ 生效**：实测长片的
   `index.tsx` 里 `CanvasBoundsGate` 是 0 处挂载 —— 门禁文件搬过去了也没在跑。
5. **同步后跑门禁（都在工程目录里跑）**：`npx tsc --noEmit`（帧参数名，`f={f}` vs `frame={f}`，以及漏传）、
   `validate-composition.py <工程>`（`live` 名字必须真的出现在场景源码里、结构/时长）、`validate-presentation.py`、
   `validate-layering.py`、`validate-motion-gaps.py`；渲染期那五道 Gate 会在 still / render 时自己报。
   技能侧再跑 `scripts/negative-gate-check.py` 与 `validate-skill-consistency.py`。
6. **最后一定要"看得见"**：渲一帧 still（或接触表）并 **Read 看图**。tsc 通过、门禁全绿，都不等于新件真的画出来了。
   例：`remotion still src/index.tsx NotebookVideoFilm out/x.png --frame=<该镜的落定帧>`。
7. **方向是单向的**：模板 → 工程。工程里为这部片子做的临时改动**不要回流模板**；只有"任何片子都该有的修复"
   才回模板，并且回完要重跑第 5 步。

> 附：本机渲染的两个坑（实测）——① `npx remotion` 可能挂死（零输出、低 CPU）：改用工程内的
> `./node_modules/.bin/remotion`；② 工程侧没装 Chrome Headless Shell 时它会**联网下载 113 MB**，
> 想复用已有的浏览器就传 `--browser-executable "<另一个工程>/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe"`。

<a id="remotion-architecture"></a>

## Remotion architecture contract

### Contents

1. Project structure
2. Deterministic data flow
3. Required components
4. Scene and layer ownership
5. Audio ownership
6. Rendering and fallback rules

### 1. Project structure

Use the canonical tree copied by the cross-platform `scripts/notebook-video.mjs new-project` command:

```text
project/
├── src/index.tsx
├── public/
│   ├── fonts and licenses
│   ├── narration.mp3
│   ├── illustrations/
│   └── sfx/
├── audio/narration.mp3.json
├── manifests/
│   ├── semantic-caption-lines.txt
│   ├── protected-caption-phrases.txt
│   ├── caption-cues.json
│   ├── asset-manifest.json
│   └── visual-assets.json
├── narration.txt
├── storyboard.md
├── package.json
└── renders/
```

Remotion is the only visual renderer. Python is limited to validation and deterministic data conversion.

### 2. Deterministic data flow

Use this order:

1. narration text;
2. visual-mode decision during storyboarding and image-capability check;
3. generated, supplied or native support-art plan plus raster provenance;
4. TTS audio plus measured word milliseconds;
5. editor-authored semantic caption lines and protected phrases;
6. semantic cues bound to exact TTS words and validated against protected boundaries;
7. one-time millisecond-to-frame conversion;
8. scene cut frames and object cue frames;
9. React component tree;
10. Remotion frame render;
11. FFmpeg loudness normalization and validation.

Define delivery and design-time frame rates explicitly. Keep both at 30fps by default. Convert timing at module load or in a preprocessing script:

```ts
const msFrame = (ms: number) => Math.round(ms * FPS / 1000);
const cues = rawCues.map((cue) => ({
  ...cue,
  startFrame: msFrame(cue.start_ms),
  endFrame: msFrame(cue.speech_end_ms),
  words: cue.words.map((word) => ({
    ...word,
    startFrame: msFrame(word.start),
    endFrame: msFrame(word.end),
  })),
}));
```

Never recompute timing differently in subtitles, animation and sound.

### 3. Required components

Copy rather than recreate:

- `AssetGate`: delays render until fonts and media are ready.
- `Img`: renders registered raster support art while callouts remain separate components.
- `Background`: fixed page, grid and static texture.
- `Paper`: owns its surface, outline and dynamic shadow.
- `Subtitle`: bottom-pinned pure caption text with per-word reveal; no bar, no dark border.
- `Chrome`: stable chapter and technical header.
- `Sound`: narration and action effects with frame-based `Sequence`.

Keep the component implementations in the canonical example until the user approves a future rendered replacement. The preserved aesthetic system keeps the same component grammar and separates stable semantic IDs from editable display copy.

### 4. Scene and layer ownership

Use a native 30fps output and 30fps design timeline. Keep the helper explicit so an intentional native-rate or longer-duration variant can update the whole timing boundary consistently:

```ts
const BASE_FPS = 30;
const FPS = 30;
const MOTION_FPS = 30;
const TIMELINE_SCALE = 1;
const designFrame = useCurrentFrame() * BASE_FPS / FPS / TIMELINE_SCALE;
const step = BASE_FPS / MOTION_FPS;
const q = (frame: number) => Math.floor(frame / step) * step;
const deliveryFrame = (frame: number) => Math.round(frame * FPS * TIMELINE_SCALE / BASE_FPS);
```

Text reveal, measured TTS boundaries, physical paper poses and action audio use native 30fps frames. Keep timing conversion centralized. For a local stop-motion beat, quantize that component to 15fps; do not change the composition.

#### Duration extension invariant

The default scene is a 900-frame design timeline. If narration requires a longer delivery while retaining the same authored scene geometry, set `TIMELINE_SCALE` and `DURATION` together (`DURATION = 900 * TIMELINE_SCALE`). Every scene mount guard, animation cue, caption boundary and action-audio `<Sequence from>` must derive from `useCurrentFrame()`, `q()` or `deliveryFrame()`; never read raw `useRawCurrentFrame()` in a scene. Before a full render, range-render across every scene boundary and inspect the final frame. This prevents an extended composition from unmounting all scenes or leaving sound cues at the original timing.

#### Long-film path: keep `TIMELINE_SCALE = 1`

For a newly authored long film (verified at 4996 frames / 22 chapters), the simplest consistent setup is to keep `TIMELINE_SCALE = 1` and set `DURATION` to the total delivery frame count, authoring every mount guard, cue, boundary and sound frame directly in delivery frames. This satisfies the invariant above with no fractional scale math. (The bundled lecture template ships a 1126-frame timeline; the 900-frame figure matches the visual-director example project.)

#### Authoring pitfall: adjacent generic-annotated arrow components

The pinned bundler has been observed to misparse `const X: React.FC<A> = (props) => { ... }` when it immediately follows a component whose body ends in dense JSX (for example a `.map` returning nested elements). The reported error points at the innocent following line (`Expected identifier but found "("`), so do not edit the reported line first. Workarounds that all parse reliably: write the component as a `function` declaration, return the preceding value from an explicit `<div>` instead of a bare `<>` fragment split across lines, or separate the two components with a plain statement. Isolate the trigger by transforming growing prefixes of the file with the bundler's esbuild `tsx` loader before touching scene logic.

Mount only scenes that can contribute pixels. Keep one scene mounted normally and at most two during a transition. Never hide every inactive scene with opacity. Read `technique.md#performance-design`.

Use start-inclusive and end-exclusive scene windows. A scene group owns its image, text, SVG and annotation layers. When the subject changes, unmount the outgoing group at its end frame; do not leave a hidden raster, callout or shadow under the next scene.

Assign one owner to every visible object. A parent that uses transform, opacity, filter or isolation creates a stacking context; therefore sibling z-index values do not escape it. Keep objects that must overlap across a container in the same intended stacking context.

Model entry, active and exit phases. At exit, move the whole component beyond the frame or set opacity to zero only after it is fully outside. Do not clip a portion and leave the remainder visible.

### 5. Audio ownership

Use `@remotion/media` `<Audio>` for narration. Use `<Sequence from={frame}>` for action sounds. Keep the cue in the same file or data source as the visible action frame.

Do not build the action timeline in an unrelated shell script. FFmpeg may normalize and encode after Remotion, but it must not introduce an undocumented narration delay.

### 6. Rendering and fallback rules

Render with the pinned package versions in the canonical `package-lock.json`. The cross-platform Node launcher is authoritative on Windows, macOS and Linux; shell wrappers are only aliases and must not contain separate render logic. The bundled network-interface shim is an opt-in compatibility aid only; enable it with `REMOTION_USE_NETWORK_SHIM=1` when a restricted runtime requires it, never by default. If a cloud environment cannot run Remotion, report the constraint before changing engines. Do not silently fall back to another renderer, real-time browser capture or generated video clips because their output will not match the approved system.

Use website capture only when the user explicitly asks to record an existing interactive site; see `media.md#html-capture`.

<a id="skill-workflow"></a>


## 完整工作流（原 SKILL.md 正文）

**第一原则 · 草稿纸讲解**：画面像一张边讲边写的草稿纸。画面上**没有笔**；每样东西都在旁白讲到它时才出现，一点点长出来，不整块弹出，同一时刻不冒出一堆。下面的「手账页 / 组件 / 直书页」管的是**画什么**，草稿纸讲解管的是**什么时候、怎么出现**；两者冲突时，按草稿纸讲解。

**出现规则**（auto 路线由引擎自动做到；手写场景路线照着写。全文见 [references/draftpaper.md#reveal-rules](draftpaper.md#reveal-rules)；版式、配色与组件搭配见 [references/draftpaper.md#draftpaper-design](draftpaper.md#draftpaper-design)）：
1. **跟着旁白**：一样东西在讲到它的那句话开始时才开始出现，不提前。
2. **长出来**：文字和卡片左→右展开，用时 = 字数 × 4 帧（最少 12、最多 45 帧）；线稿按部位依次描出，整幅 24–45 帧；圈注 14 帧，下划线和箭头 12 帧，手写小字 24 帧。手账页上的真图版、照片、截图可以整件「贴上」，但也要等讲到它的那句。
3. **不扎堆**：同一镜里，相邻两样东西开始出现至少隔 12 帧（0.4 秒）；同一时刻最多 2 样在长。
4. **不预铺**：镜头切进来时，纸上只有已经讲过的东西；开镜头 6 帧内最多 1 样东西开始出现。

画面由两种东西分工，**交替出现**：

| | 负责 | 长什么样 | 怎么写 |
|---|---|---|---|
| **手账页** | **承载**：把要讲的那个真东西摆到眼前 | 一页纸：装裱好的原版图版 / 标本、手写页眉、朱红印章、一行手写说明、放大镜 | `layout: "page"` + `content.page` = `plate` / `loupe` |
| **组件** | **讲解**：把概念拆开、对比、算清 | 流程、对比、清单、柱条、大数字、代码 | `flow` / `compare` / `list` / `bars` / `number` / `code` |

- **三种呈现模式**（`story.json` 顶层 `"mode"`），配比不同，`validate-fusion` 按模式判：

| mode | 手账页 | 组件（含直书） | 什么时候用 |
|---|---|---|---|
| `hybrid`（默认） | 20–75% | ≥25% | 有物可看、也有结构要讲——绝大多数片 |
| `component`（全组件） | ≤12% | ≥60% | 内容本身就是结构（流程 / 对比 / 清单 / 数据），没有实物可拍 |
| `freeform`（全非组件） | ≥40% | 多框组件 ≤10% | 有物可看，或抽象但有几何可画；只有手账页 + 直书页 |

  模式是**门禁契约**，不是风格开关：声明 `component` 却整片是手账页，会被点名「别声明一套做另一套」。
- 主题里的那个东西全片**至少出现一次**（手账页图版说明 / 墨图标签 / 标本速写 / `see` → 全组件片还认组件镜的 `title`），否则判 **P0**。
- 手账页的容器是**纸**，不是卡片：不要给它套圆角框，也不要把图版做成"浏览器截图卡片"。
- 手账页写法见 [references/components.md#journal-page](components.md#journal-page)；参考片 [examples/cell-notebook](../examples/cell-notebook/README.md) **仅文档**（导演层 + 分镜 + 旁白，不含 story.json 与素材，不能直接跑）；能直接跑的手账页配方是 [examples/recipes/cork-page.story.json](../examples/recipes/cork-page.story.json)（4 镜，自带导演层，素材按提示用 commons-search 取一次）；组件配方见 [references/scenes.md#recipes](scenes.md#recipes)。

**线稿是可选件，只做标本速写**（一件东西 + 尺寸线 + 手写名）。不要用简笔线稿去「解释」概念——
实测那种画面像剪贴画，比不画更差。`validate-fusion` 对「文字 + 简笔线稿」超过 20% 判 P1。线稿写法见 [references/components.md#linework](components.md#linework)。

组件是信息的主体，但**不是唯一的载体**：有真东西可看时用 `page`（手账页），只有一组关系要讲时用 `type`（直书页：靠字号、行距、对齐做层级，一个框都不出）。
直书页是「省掉框」，不是「省掉内容」——每行 ≤10 字、≤5 行，全片 ≤40%；超了就成一本排版册。写法见 [references/components.md#journal-page](components.md#journal-page)。
另外，每片留 2–3 个**锤子帧**（整章最该被记住的一句，满屏单独出现 1.5–2.5 秒），规则见 [references/director.md#pacing-rhythm](director.md#pacing-rhythm)。
锤子帧怎么做：组件路线用 `StampBanner`（或 `Callout` 放大到 displayL）独占一镜；手作路线用 `HandLettering` 手写满屏一句，或 `Seal` 印章大字——都放在媒介里，不是白底大字。
只有 16:9；五个皮肤：`flat`（默认）、`cel`，以及手作皮肤 `journal`（手账水彩）/ `papercut`（红色剪纸）/ `archive`（档案灯台）。
TTS 是正式步骤：`notebook-video tts <工程>`（默认 edge-tts；也可 `--engine=file` 用你自己的录音），字幕与镜头按**词级时间**对齐；没有真实旁白时 `--render` 会停在渲染前（静音占位只给 `--stills` / `preview`）。默认无 BGM，音效稀疏。

### 先选路线

| 题目 | `mode` | 路线 |
|---|---|---|
| 软件、产品、代码、操作教程（没有实物可拍） | `component` | `flat` / `cel` + 下面第 1–5 步 |
| 科普、自然、历史、"为什么"（有真东西可看） | `hybrid` | `journal` / `papercut` / `archive`，先走第 0 步导演层；手账页承载 + 组件讲概念 |
| 单位、几何、算法、纯结构（没实物但有形可画） | `freeform` | `journal`：手账页 + 直书页，多框组件 ≤10% |

**不论哪条路线，每个选题都先搜一次 Commons / Openverse**（真东西几乎总能让片子更好）：
`python scripts/commons-search.py search "<英文关键词>" --project ./my-video`，能用的 `add` 进来，交付前 `credits` 生成 `CREDITS.md`。
许可只收公有领域 / CC0 / CC BY，署名自动上屏。见 [references/media.md#commons-media](media.md#commons-media)。

### 第 0 步 · 导演层（手作路线必做）

照 [references/director.md#director-method](director.md#director-method) 写 `manifests/treatment.json`（模板 `manifests/treatment.example.json`）：
一个生活问题 → 只属于这个题的隐喻 → 媒介（皮肤）为什么是它 → 顿悟点的**原生动作** → 三个候选结构选一个 → 对标学 / 不学 → 镜头表每镜写理由。
蓝图用 `blueprints/medium-metaphor.json`。`validate-treatment.py` 在手作皮肤下把缺项记 P0（`make-video` 自动跑）。
媒介的八个轴与"不是什么"见 [references/director.md#style-recipes](director.md#style-recipes)；组件见 [references/components.md#craft-kit](components.md#craft-kit)
（`InkPath` / `HandNote` / `HandLettering` / `WashBlob` / `CutPaper` / `Loupe` / `PinnedPhoto` / `ArchivePhoto` …）。
开场钩子、节奏、运镜分别见 [references/director.md#narrative-hook](director.md#narrative-hook)、[references/director.md#pacing-rhythm](director.md#pacing-rhythm)、[references/camera.md#camera-language](camera.md#camera-language)。
**手作路线只必读 4 份**：[references/director.md#director-method](director.md#director-method)、[references/components.md#craft-kit](components.md#craft-kit)、[references/camera.md#camera-language](camera.md#camera-language)、`references/themes/<皮肤>.md`；其余按需查（`references/scenes.md#lecture-composition` 等仅限组件路线）。

**auto 路线（story.json）必读 2 份**：[references/technique.md#auto-engine](technique.md#auto-engine)、[references/draftpaper.md#reveal-rules](draftpaper.md#reveal-rules)；用到配方 / 线稿时再读 [references/scenes.md#recipes](scenes.md#recipes)、[references/components.md#linework](components.md#linework)。
先做 3 张风格帧（`--stills`），像了再做全片；**整片渲染前**由新会话只看联系表 + 自动生成的 `storyboard.md` + `treatment.json` 做七项独立评审，写进 `review.rounds`（手作皮肤没评审时 `make-video --render` 给一条 P1 提示、照常渲染；`--skip-review` 关掉提示）。

### 第 1 步 · 选一个蓝图

| 你要讲的 | 蓝图 | 路线 |
|---|---|---|
| 一个词 / 一个原理 | `blueprints/concept.json` | 组件 |
| 一次代码改动 | `blueprints/code-change.json` | 组件 |
| 几组数字说明一个结论 | `blueprints/data-compare.json` | 组件 |
| 一件事分几步发生 | `blueprints/process.json` | 组件 |
| 一个常见错误 | `blueprints/pitfall.json` | 组件 |
| "为什么"类科普：一个错误直觉被一个原生动作推翻 | `blueprints/medium-metaphor.json` | 手作（默认） |
| 一个现象的来历，适合"起—承—转—合"慢慢翻出意外 | `blueprints/kishotenketsu.json` | 手作 |
| 一个有悬念的"谁 / 为什么"，线索逐条揭开 | `blueprints/mystery.json` | 手作 |
| 大小 / 多少超出直觉，要一级一级比出来（尺度、数量） | `blueprints/scale-ladder.json` | 手作 |
| 能用一次对照实验说清的因果（变一个量，看结果） | `blueprints/experiment.json` | 手作 |

组件路线的蓝图每一镜都写了 `$components`：该用的**骨架**（Stage / Split / Zoom / Corridor）和**组件**。照它选，别自己发明版式。
手作路线的蓝图写的是结构和节拍；三个候选结构至少来自 2 个结构族（见 [references/director.md#director-method](director.md#director-method) 第 5 步）。

### 第 2 步 · 建工程，照抄示例片的结构

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project ./my-video --style=flat
```

手作路线换成 `--style=journal`（或 `papercut` / `archive`），会按需下载 Noto Serif SC Bold（字幕字体，OFL）。

**翻页是缺省，不是选项。** 任何皮肤、任何 story，只要不写 `transition`，镜间一律翻页：
`pageturn`（纸被卷起来，WebGPU）→ 画不了就退到 `pageflip`（纯 CSS 的折痕翻页，无依赖），
两者**同向**（近乎竖直的折线、下角领先，从右往左翻）。所以 story 里**不需要**写
`"transition": "pageturn"`，写了反而会把自定义皮肤的选择固定死。
`whip`（甩镜）/ `zoom` / `slide` / `drop` 仍可用，但都要显式写。

**翻页一定有纸声**（`page` 拟音，转场第 3 帧命中）。它是动作音，不是标点：
`sfxDensity: sparse` 只削标点，不削动作；换章那一镜 chapter 与 page 并存，不会互相吃掉。

渲染器先画一张探针验收 WebGPU 卷页；通过就换完整版 Chromium 只渲转场那 22 帧，再按帧号拼回快速渲染的整片
（`transition-plan.mjs` 的 `curlWindows` 定窗口 + `fx-browser.mjs` 的 `spliceArgs` 拼回）。缺完整版 Chromium 时探针失败，全片照常出，
翻页自动降级成折痕版并在报告里记 P1（[references/camera.md#fx-effects](camera.md#fx-effects)）。
装浏览器：`npx playwright install chromium`（国内加 `PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright`）。

工程里已有一部完整的示例片（8 镜）。**照着改，不要从零写**：

- `manifests/shots.json`：每镜一行（`skeleton` / `live` 组件 / `cameraIntent` / `beats` / `transition`）——镜头表是唯一真相；
- `src/scenes.tsx`：每镜一个 React 组件，用 `live` 里列的组件画出来，动画只用帧号 `f`；
- `src/film.ts`：片名、章节标题；
- `manifests/caption-cues.json` + `audio/narration.mp3.json`：字幕（每行 ≤16 字）。

> **抄结构，不要抄片子。** 拿到模板最容易犯的错是把它再演一遍——同样的镜序、同样的招牌镜头、同样的收尾。
> 改完跑一次 `eval-project "<SKILL_DIR>/assets/lecture-template" ./my-video`，看
> **版式种类 / 介质种类 / 转场种类 / 镜长分布 / 最大推近**这几行有没有真的不同；全都一样就说明你只是在换文案。
> 这是测量不是打分——"像不像"没有客观界线，但两列摆在一起你自己看得出来。

组件怎么选：[references/media.md#media-routing](media.md#media-routing)（修辞动作 → 组件表）、[references/components.md#fxkit](components.md#fxkit)。
完整作者手册（骨架、镜头语言、门禁细节）：[references/scenes.md#handwritten-scenes](scenes.md#handwritten-scenes)。

### 第 3 步 · 写台词与镜头表

- 一镜 1–3 句，一句一个意思；字幕超 16 字由 `build-semantic-captions.py` 在合法断点自动拆（不拆词、英文、数字）。
- 要观众「看那里」时，在镜头表写 `cinema.focus`（推近到那个组件的矩形）；不写也有缺省缓推。
- 相邻两镜换骨架；一镜一个概念；关键数字用 `KineticNumber` 数过去。
- 背景：手作皮肤默认 `bgMode: "chapter"`（每章一张纸、章内沿用），flat / cel 默认 `"shot"`（逐镜轮换）；全片一张纸写 `"bgMode": "film"`，完全不轮换写 `"bgRotate": false`。不写就自动选——每个皮肤有 8–11 张风格各异的亮底背景（手账：横线本 / 方格 / 点阵 / 牛皮纸 / 水彩纸 / 便签墙 / 旧书页 / 坐标纸；剪纸：红纸衬边 / 宣纸 / 窗花 / 祥云 / 挂笺 / 洒金…；档案：档案袋 / 旧报纸 / 古地图 / 卡片目录 / 胶片 / 展柜布面…），逐镜模式按镜头角色挑、相邻两镜不重复，装饰重的（`busy`）不进常规镜。某一镜要特定的纸，就写 `"bg": "oldpage"`；清单与许可见 [references/media.md#background-library](media.md#background-library)。
- 帧参数名：`fxkit` 组件传 `frame={f}`，其余模块传 `f={f}`（帧参数是必填类型，传错或漏传 `tsc` 报错）。

### 第 4 步 · 一条命令

```text
node "<SKILL_DIR>/scripts/make-video.mjs" ./my-video --stills
node "<SKILL_DIR>/scripts/make-video.mjs" ./my-video --render ./my-video/final.mp4
```

Windows 用同一条 `node` 命令（或 `scripts\make-video.cmd`）。依次做：resolve-shots（自动修）→ 门禁 → tsc → 静帧接触表 / 渲染 → 抽帧报告 `renders/report.md`；`--render` 后若装了 RapidOCR，会用 `validate-ocr.py` 抽字幕帧 OCR，核对字幕真的读得出（没装就跳过并提示）。

**旁白顺序（auto 路线）**：`compose-story` 先写出 `narration.txt` → 你跑 `notebook-video tts <工程>` 生成音频 → `make-video` 里第二次 compose 按词级时间重排字幕与镜头。
**改了 story 必须重跑 compose 再 tts**：`story.json` 比 `narration.txt` 新时 tts 会直接停下，告诉你先跑 compose——
否则它会读旧的旁白，**出半截音频而且不报错**。自己手写 narration（不跟 story 走）时加 `--allow-stale`。
**先看 `--stills` 静帧，再渲整片**（整片渲染要先征得用户同意）。手作皮肤 `treatment.json` 的 `review.rounds` 为空时 `--render` 给一条 P1 提示（建议先做独立评审；照常渲染，`--skip-review` 关掉提示）。`--render` 默认 1920×1080；响度目标 −16 LUFS（静音旁白片与真人声片相同）。

**渲染中途失败别整片重渲**：`notebook-video render <工程> <输出> --resume`。raw 中间产物只在**成功交付后**才删除，
所以渲染/响度/封装任一环节失败都能接着做；输入（场景、素材、音频、story）没变就跳过整片渲染，直接做响度与封装。
渲染若**一动不动**（不是慢），看门狗会在 8 分钟无输出时中止并给出下一步（`REMOTION_STALL_MS` 可调）。

**改完一版想确认"有没有变好"**：`node "<SKILL_DIR>/scripts/notebook-video.mjs" eval-project 旧工程 新工程`。
它把片子拆成可比的数据（镜长分布、版式/介质/转场种类、运镜覆盖、字幕密度、空场读数）并给出 Δ。
**它不打分**——判据只在门禁里存一处，两处各写一份阈值就会漂移。看到 Δ 之后，好坏仍由门禁 + 独立评审判。

**读输出**：`✓ 自动修` = 引擎替你改了什么；`· 建议` 不拦；`✗` 才要改——每条都写了怎么改。同一个 ✗ 连续两次没改过来，停下来把报错原文告诉用户。

**交付不止一个 mp4**。`--render` 成功后会自动再出两样（都失败不拦片，只记一笔）：

| 产物 | 怎么来的 | 给谁 |
|---|---|---|
| `renders/captions.srt` | `export-srt` 从 `manifests/caption-cues.json` 导出（就是画面里那套断句，不是重新识别） | 上传平台要字幕轨、或别人要翻译 |
| `renders/poster.jpg` | `poster` 渲一帧静帧。默认取 `treatment.signature_shot` 声明的招牌镜头的**落定窗口**（动作做完、还没到切点），并且**不画字幕** | 封面 / 缩略图 / 文档配图 |

单独用：`notebook-video poster <工程> [out.jpg] [--shot=S4|--frame=759]`、`notebook-video export-srt <cues.json> <out.srt>`；
两样一起重出用 `notebook-video deliver <工程>`（改封面构图、换字幕都不必再渲整片）。
不要拿几何中点当封面：中点经常正好压在最后一拍上，封面里会出现半截正在被写的字。

**看动起来对不对，别直接渲整片**：`node "<SKILL_DIR>/scripts/notebook-video.mjs" preview ./my-video --seconds=30`
（默认 0.5 倍分辨率；**翻页预览里就有**——不开 fx 时走纯 CSS 的折痕翻页，速度不受影响。
30 秒窗口的耗时看机器：作者开发机约 40 秒，2 核 / 8 GB 的 Linux 实测约 5 分钟（含打包）；同时给接触片和响度读数。单镜验：`--shot=S6`。
`--fx=on` 是把翻页升级成 GPU 卷页（纸真的弯起来、带纸背透光），它会切完整版 Chromium
（预览 0.5x 下约 1.8 秒/帧，交付分辨率约 3 秒/帧），所以别拿它渲 30 秒窗口，
**要看卷页就只截转场那 30 来帧**：
`--from=<跨镜边界前一秒> --seconds=1.2 --fx=on`（作者开发机实测 61 秒出片，慢机器上会长数倍）。
跨镜边界在 `manifests/shots.resolved.json` 的 `from` 里，除以帧率就是秒。带翻页时不给全片耗时推算，
因为只有转场帧走 WebGPU，线性外推会得假数字。）
想量「是不是边讲边长」：`python scripts/measure-reveal.py <工程> renders/preview-*.mp4`（只报告，不拦；读法见 references/draftpaper.md#reveal-rules）。
预览结束会打一行 `FillGate coverage`：每镜 `cells`（48 格占用）/ `blank`（全空的列）/ `largest`（最大单体占画面）/ `widest`（最大横向跨度），
`largest<0.06` 判「主体过小」，但有两条豁免：`widest≥0.45`（面积小但横跨够的条状主体——标尺、格带、时间轴）
和 `blank=0` 且 `cells≥24`（照片+引线+网格这类多个中等元素拼成一个主体，没有单个"大件"）。
`blank≥3/8` 判「横向空洞」。被判空时**不要放大卡片凑面积**，按 [references/checks.md#composition-gate](checks.md#composition-gate) 的写法改：空洞处补一层属于主体的东西。**不要为了让开头满而把东西提前摆上**——FillGate 量的是每镜最完整的那一帧，开头空着是草稿纸的正常状态。

**片子比 30 秒长时，别看开头就下结论。** `preview --seconds=30` 只覆盖前六镜，cell 的 S7/S8 就是这么漏的
（补跑 `--from=32` 才发现 S7 右下角空 30%）。全片一次量完用 `sweep`——每镜截一张落定态、拼成一张体检表，八镜约 60 秒：

```bash
node "<SKILL_DIR>/scripts/notebook-video.mjs" sweep ./my-video          # 0.5x，八镜一张表
node "<SKILL_DIR>/scripts/notebook-video.mjs" sweep ./my-video --plan   # 只算会量哪几帧，不起浏览器
node "<SKILL_DIR>/scripts/notebook-video.mjs" sweep ./my-video --json   # 给脚本读（stdout 只有 JSON）
```

它按镜取「切点前最近的一个 **15 的倍数**帧」，两个条件都不是随手写的：必须是 15 的倍数，因为 FillGate 只在
`frame % 15 === 0` 上采样，取别处会得到**零数据**——而零数据和"这镜没问题"在屏幕上长得一模一样；必须落在**后半段**，
因为入场帧几乎必然是空的，拿它判空场会把每一镜都打成空洞（FillGate 第一版就是这么误报的）。
产出三样：终端八行表、`renders/sweep-sheet.jpg`（每镜一格，一眼看完构图）、`renders/sweep.json`（含每镜量的是第几帧，可复查）。
数字可能比整片渲染略低（整片在整镜里扫，sweep 只取一帧，差 2–3 格属正常），但**判定用的是同一套阈值**
（`assessCoverage()`，渲染收尾那行 `FillGate coverage` 也走它——阈值只有一处）。

**覆盖率留档只有两个来源**：整片 `render` 和 `sweep`。`preview` / `render-range` / `review-frames` 是**窗口**渲染，
量到的是"窗口内最完整帧"，不是"整镜最完整帧"——实测 60 帧窗口把 S1 记成 cells=25，整镜是 28。
这几个命令只打印、不写 `fill-coverage.json`，免得一次"看一眼"的预览把某镜的覆盖率改成假数字。

### 第 5 步 · （需要时）定制组件

题目需要一张只属于它的图（比如「请求怎么穿过缓存」）时，照抄 `src/custom/RequestLane.tsx` 写一个组件，在 `src/custom/index.ts` 注册，
然后在 `scenes.tsx` 里像其他组件一样用。纪律：只用 `f` 驱动动画；文字 ≥32px；文字色用 `C.ink` / `C.muted` / `C.*Ink`。

### （需要时）真实截图 / 录屏

观众以后要在那个界面上操作（例如 GitHub 的 PR 页）时，可以把真实截图或 ≤10 秒的录屏放进 `MediaFrame`（同一套卡片外观）：
`python scripts/prepare-media.py ./my-video --add pr.png --id pr-page --region diff 0.01 0.31 0.69 0.17`，然后在场景里
`<MediaFrame f={f} id="pr-page" x={200} y={200} w={1060} h={662} focus="diff" focusAt={b[1]} />`。
来源优先级：用户文件 > 自己截的官方页面 > CC0 / CC-BY / Pexels / Unsplash（写清 url / license / credit，署名自动上屏）。
**没有兼容许可就用组件重画。** 细节与门禁：[references/media.md#real-media](media.md#real-media)。

### 引擎替你保证的

**硬门禁（客观）**：取景不切断标题 / 标签（推近自动留边、回退倍数）；字号地板；文字对比度 ≥4.5:1；背景库每张都有来源与许可、亮底、字幕区对比度够（`validate-backgrounds.py`）；字幕每行 ≤16 字、读速（组件路线 ≤4.5 字/秒、手作路线 6.5 字/秒）；
画面不静止超过约 1 秒（镜尾 >1.5 秒无事件自动补收束慢推）；音画同步；音效文件 sha256 与增益 / 提前量和 manifest 一致。
**软建议（主观，只提示）**：同屏强调数、每镜字号种类、装饰预算、快慢交替、留白。

**引擎不能保证的（P2-22，说清楚免得当成事实核查器）**：故事里的**事实、数字、历史说法是否正确**。
门禁能验结构、时长、画面、引用格式、可读性、复现，唯独验不了「这句话对不对」——那是人工审读的事。
`validate-facts.py` 只保证**标注本身合法**（引用的来源存在、类比不被当机制事实、AI 生成的 see/ink
描述不当来源），并把「含数字/年份的未标注文本」列成审读清单（`--review`）供人工核对。
**可核验断言**（数字、年份、机制）要么写 `claim: {kind:"fact", source:"<sources 里的 id>"}`，
要么明确标成 `claim: {kind:"analogy"}`（解释性比喻，不能当机制事实）。**过渡句、观点、比喻不必逐条标注**——
所以这不是无差别硬门禁：缺标注只提示（P1），标注自己说不通才拦（P0）。

**人工审读节点**：出片前跑一次 `validate-facts PROJECT --review`，把清单里的数字/年份逐条核对。
AI 生成的图（`content.ink` / `content.figure` 的 label）是**说明性文字**，不是事实来源。
**开场**：`validate-opening.py` 管前 3 秒——第 0 帧就有东西在发生、首条字幕 ≤1 s、片名不当第一镜、前 3 秒 ≥3 拍、第一句不是泛问句——这几条写法规则记 P1；`--video` 的像素复核（第 0 帧空纸、开场画面不动）在手作皮肤记 P0。

**音效**：只挂在真事件上；每条 cue 按 manifest 的 `offsetMs` 提前起播，让瞬态落在视觉命中帧；间隔 ≥150 ms；默认**无 BGM**（只有 `treatment.sound.music.use=true` 才加载音乐床，并在音效下闪避）。密度由片级 `sfxDensity` 决定：缺省 `sparse`（每镜一记：换章的镜给章节声、其余给末拍，误区镜另留反转音），写 `"sfxDensity": "normal"` 回到「一拍一个」。旁白是 TTS 生成的，音效必须压在人声下，所以默认就该克制。

### auto 路线（story.json，主路线）

用 `node scripts/make-video.mjs my-story.json ./draft --stills` 从蓝图直接出片（`compose-story.py` 自动排版、关键词同步、字幕定时）。
它用这几种版式：**`page`**（手账页，`content.page` = `plate` / `loupe`）、`define` / `number` / `bars` / `compare` / `code` / `flow` / `list` / `quiz` / `custom` / `media`；`statement` 只渲染成一张卡片，不是缺省版式。
要用配方和线稿就走这条路线；要逐镜手调版面，再改写成第 2–3 步的手写场景。细节见 [references/technique.md#auto-engine](technique.md#auto-engine)；示例 `examples/*.story.json`。
