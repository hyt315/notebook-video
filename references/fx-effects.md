# 真翻页 / 揭纸转场（`@remotion/effects`，3.5.0）

> 手作皮肤的「翻到下一页」不再是镜头横移，而是一页纸真的卷起来翻走：卷曲、折痕高光、纸背透出上一页的墨迹。
> The hand-made skins now turn a real page: the old page curls away with a shaded fold and its back showing through, instead of a camera pan.

## 1. 用法

| 转场 | 画面 | 缺省用在 | 无 WebGPU 时退回 |
|---|---|---|---|
| `pageturn` | 近乎竖直的折线（-78°，下角领先），整页从右往左翻走 | `journal`、`archive` 皮肤的 auto 转场 | `slide`（纸面横移） |
| `peel` | 对角折线（315°），从右下角往左上角揭起 | `papercut` 皮肤的 auto 转场 | `drop`（新纸落下） |

- 分镜表可以显式写 `"transition": "pageturn"` / `"peel"`（任何皮肤都行）；手作皮肤写 `auto`（或不写）就用皮肤缺省。
- 章节首镜仍然是 `drop`（换一张纸），所以一部片子至少两种转场。
- 卷页时长 22 帧（`CURL_FRAMES`，0.73 s，手翻的速度）；其余转场仍是 14 帧。
- 卷走的是上一镜的**整页**：背景（按上一镜末帧的视差位置）+ 内容；新的一页在下面不动，背景不交叉淡化。页眉、章节卡、字幕在纸面之上，不跟着卷。
- 几何（`src/fx.tsx` 的 `curlParams`）是进度 p 的纯函数，pageTurn 本身无随机：同一帧渲两次结果相同。

## 2. 为什么默认要探针

`pageTurn()` 需要 **WebGPU + HTML-in-canvas**。实测（2026-10-27，2 核 arm64、无 GPU 的 Linux 容器，Remotion 4.0.539）：

| 浏览器 / 参数 | WebGPU 适配器 | pageTurn 结果 |
|---|---|---|
| Remotion 缺省 Chrome Headless Shell 157.0.8080.0（老式无头），`--gl=angle` / `swangle` / 任意 Vulkan 参数 | 无 | 报错 `No WebGPU adapter available` |
| Chrome for Testing 156（Playwright `chromium-1248`），`--headless=new --gl=swangle` | 有（SwiftShader） | **不报错但卷页那一层全透明**（WebGPU 画布与合成器之间的共享纹理建不起来） |
| 同上，`--gl=vulkan`（Remotion 自带的 Vulkan 参数组） | 有 | 同样画空 |
| 同上，`--use-angle=vulkan --use-vulkan=swiftshader --enable-unsafe-swiftshader` + feature `Vulkan` | 有 | ✅ 正确 |

所以：只问 `navigator.gpu` 不够，必须真画一张、读像素。`scripts/fx-browser.mjs` 做这件事：

1. 本片没用到 `pageturn` / `peel`（分镜表 + 当前皮肤）→ 不探测，什么都不变。
2. 找完整版 Chromium：`NOTEBOOK_VIDEO_FX_BROWSER`，否则本机 Playwright 缓存（`PLAYWRIGHT_BROWSERS_PATH`、`~/.cache/ms-playwright`、macOS / Windows 的同名目录）里版本最高的 `chromium-*`（不要 `chromium_headless_shell-*`）。都没有 → 交给 Remotion `--chrome-mode=chrome-for-testing` 自动下载（Google 不发 linux-arm64 的 CfT，这一档在 arm64 Linux 上会失败 → 退回）。
3. Linux 上生成一个包装脚本当 `--browser-executable`（Remotion 4 的 CLI 不收任意 Chromium 参数）：合并 `--enable-features`、去掉 Remotion 自己的 GL 参数、换成上表最后一行那组、加 `--window-size=3840,2160`；浏览器目录里有 `vk_swiftshader_icd.json` 时再导出 `VK_ICD_FILENAMES` 指向它（Vulkan loader 不会自己去浏览器目录找 ICD；缺了它 ANGLE 报 `Internal Vulkan error (-7): A requested extension is not supported`，退回 GL 后 WebGPU 共享纹理建不起来，卷页层**悄悄画空**——实测容器重启丢了这个环境变量，探针立刻从通过变全白）。`NOTEBOOK_VIDEO_FX_FLAGS` 可整组替换（有真显卡的机器可以设为空串）。macOS / Windows 不包装，用 `--gl=angle`。
4. 渲 `NotebookVideoFxProbe`（320×180：红页卷走一半露出蓝底）一帧，读像素：左红右蓝才算通过。结论连同浏览器、参数、Remotion 版本写进 `renders/.fx-probe.json`，键不变就不重探。
5. 通过 → 成片渲染传 `{nvFx: 'on'}`；不通过 → 不传，合成里 `pageturn → slide`、`peel → drop`，片子照出，make-video 报告里记一条 **P1 真卷页未开启** 并写明原因。

```bash
node scripts/notebook-video.mjs fx-probe <工程> [--force]   # 单独探测，打印 JSON
NOTEBOOK_VIDEO_FX=off node scripts/notebook-video.mjs render <工程> out.mp4   # 手动关掉
npx playwright install chromium   # 没有完整版 Chromium 时装一个（约 170 MB）
```

Studio 预览与普通 `remotion still` 缺省没有 `nvFx`，看到的是退回后的 slide / drop；要在 Studio 里看卷页，用 Chrome ≥ 149 打开 `chrome://flags/#canvas-draw-element` 并以 `--props='{"nvFx":"on"}'` 启动。

## 3. 渲染成本与「快速整片 + 卷页片段拼接」

实测同一工程（细胞片，2560×1440）：

| 路径 | 每帧 |
|---|---|
| 缺省 Headless Shell，concurrency 1 或 2 | ≈ 0.25 s（60 帧 24 s，含启动） |
| 完整版 Chrome + SwiftShader Vulkan，concurrency 1 | ≈ 3.1 s（60 帧 206 s） |
| 完整版 Chrome，concurrency 2 | **花屏**：第二个标签页截图超出窗口的部分重复平铺（`--window-size` 也救不了）→ 开 fx 时一律 concurrency 1 |

整片都走完整版 Chrome 会慢 10 倍以上，所以 `notebook-video render` 在开了 fx 时这样做：

1. 整片照常用 Headless Shell 渲（卷页处是退回的 slide），近无损 `crf 8`；
2. 每个卷页窗口（镜头起点起 22 帧，`curlWindows`，宁多勿少，相邻窗口合并）用完整版 Chrome 单独渲（`crf 8`、静音）；
3. ffmpeg 按帧号 `split / trim / concat` 拼回，只在这一遍编码到交付质量（`crf 16`、bt709 tv），再回写色彩标记、做响度规范化（与原流程相同）。

细胞片 4 处卷页：额外约 4 × (20 s 启动 + 22 帧 × 3 s) ≈ 6 分钟，加一遍重编码约 3 分钟（x264 medium ≈ 80 ms/帧）。
`render-range`（送审短片段）不拼接，整段走完整版 Chrome。`make-video --stills` 的静帧不走完整版 Chrome（静帧取镜头开场 / 关键词 / 镜尾，不落在卷页窗口里）。

## 4. `fractalNoise()` 评估结论：不默认开

`fractalNoise()`（WebGL2）可以做「纸纹的动态层」。实测：

- Headless Shell + `--gl=swangle`：2560×1440 全分辨率 ≈ 3.2 s/帧（30 帧 103 s）——整片叠一层要多 1.5 小时以上；
- 完整版 Chrome + 上面那组 Vulkan 参数：WebGL2 上下文建不起来（`createWebGL2ContextError`），**与 pageTurn 不能同在一个浏览器配置里**；
- 观感：纸本身不会动，逐帧演化的云纹在亮底上像「沸腾的纸」，盖过了墨线和水彩的手作感。1/4 分辨率 + 每 5 帧跳一次（6 fps 手绘抖动）便宜很多，但仍需要 `--gl=swangle` 整片渲染。

结论：现有的静态纤维纹理（`public/craft/fibre-tile.png`）+ 背景库里 Paper Shaders 离线预渲的纸纹，已经比动态噪声好且零运行时成本。`fractalNoise` 只作为**离线**生成静态纹理的候选（维护者工具里渲一次存成位图，与 3.4.0 处理 Paper Shaders 的方式相同），不进渲染期。

## 5. 许可

`@remotion/effects` 与 `remotion` 同属 Remotion 仓库，受 Remotion License 约束（npm 元数据写作 `UNLICENSED`，与已依赖的 `@remotion/transitions` 相同；以仓库根 `LICENSE.md` 为准）。其中 Fractal Noise 等着色器改编自 EffectCraft（MIT），见包内 `THIRD_PARTY_LICENSES.md`。本仓库不分发这些包，由 `npm ci` 安装。详见 `DEPENDENCIES.md`、`NOTICE`。
