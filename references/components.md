# 组件速查：fxkit、手作材质、线稿与手账页

本篇是选型速查入口；组件详细 props 以 `assets/lecture-template/src/` 源码类型定义为准（`tsc` 编译期校验）。

**帧参数铁律**：仅 `fxkit`（`src/fxkit.tsx`）与 `src/toolkit.tsx`（`Callout`/`Checklist`）传 `frame={f}`；`FitTextBox`/`PillTag` 不收帧参数；其余组件（`StampBanner`/`KineticNumber`/`StatRow`/`SplitStage`/`VerdictBar` 及全部 `craft`/`linework`）传 `f={f}`。漏传或传错 `tsc` 直接报错。

<a id="fxkit"></a>
## 1. 常用解释组件速查

| 组件 | 帧参数 | 常用关键属性 | 源码文件 |
|---|---|---|---|
| `Callout` / `Checklist` | `frame={f}` | `start`、`x`/`y`/`w`/`h`、`text`/`items`、文字色用 `C.ink`/`C.*Ink` | `src/toolkit.tsx` |
| `Funnel` / `ProgressRing` / `StampSeal` | `frame={f}` | 漏斗 / 占比环 / 阶段盖章动效件 | `src/fxkit.tsx` |
| `FitTextBox` / `PillTag` | 无帧参数 | 自动缩字文本框 / 术语标签徽章 | `src/components/fittext.tsx` / `src/kit.tsx` |
| `StampBanner` | `f={f}` | `at`、`text`（≤16 字组件锤子句） | `src/media.tsx` |
| `KineticNumber` | `f={f}` | `at`、`to`（数字）、`suffix`（单位）、`label` | `src/cinema.tsx` |
| `StatRow` | `f={f}` | 多指标并排卡 | `src/components/chart.tsx` |
| `SplitStage` | `f={f}` | 左右双栏对照舞台 | `src/skeletons.tsx` |
| `VerdictBar` | `f={f}` | 底部裁决条 | `src/components/effects.tsx` |
| `MediaFrame` | `f={f}` | `id`（须登记在 `manifests/media.json`）、字面量 `w`/`h`（禁止隐藏署名） | `src/media-frame.tsx` |

- **先看再选**：`node scripts/notebook-video.mjs showcase <工程>`（加 `--sheet` 出接触表）把库组件渲成多页接触表，选组件前先看图，比读 props 准；新增组件要同时加进接触表。
- **两条铁律**：文字容器高度一律用 `fitH()` 算，不手写固定高度；`x` / `y` 永远相对最近的定位祖先，在 `Paper` 里是卡片坐标，只有直接放在场景根下才是场景坐标，写错会飞出屏而渲染不报错。
- 其余现成封装组件：`Chart`/`HighlightCode`/`TreeView`/`NetworkGraph`/`ControlStack`/`OverlayFrame`/`MathBlock`/`GeoView`/`SankeyChart`/`SketchFx`/`FocusFx`/`PathDraw`/`MorphShape`/`TopicIcon`/`IconWall`/`QrCode` 导出在 `src/components/index.ts`；`DiffView` 在 `src/fxkit.tsx`（`frame={f}`），`ConsoleWindow`/`MetricGrid` 在 `src/media.tsx`，造轮子前先查 `notebook-video showcase --sheet`。

<a id="craft-kit"></a>
## 2. craft：手作材质组件（均传 `f={f}`）

面向 `journal` / `papercut` / `archive`（可经合成 `NotebookVideoCraftSheet` 查看样张）：
- **文字与印章**：`HandLettering`（≤10 字描墨填墨锤子帧）、`HandNote`（≤16 字手写批注，必填 `x`/`y`）、`Seal`（2–4 字朱砂印，必填 `x`/`y`）。
- **笔触与纸面**：`InkPath`、`Underline`、`InkCircle`、`PaperSheet`、`WashBlob`、`CutPaper`。
- **真图版与放大镜**：`Loupe`、`ArchivePhoto`、`PinnedPhoto`、`LoupeMedia`。
- **纸面附件**：`TapeStrip`（和纸胶带）、`FibreOverlay`（纸纤维覆盖层），从 `theme/craft-common` 重新导出。

<a id="linework"></a>
## 3. 线稿层（`sketch`）

- 线稿只做**标本速写**（单件实物 + 尺寸线 + 手写名，描出 24–45 帧），禁止用简笔线稿当概念流程图（超 20% 记 P1）。
- 交互语法：支持 7 个动词（`enter`/`point`/`drop`/`swap`/`count`/`mark`/`exit`）、`@L1`/`@L1.4` 时刻与 `content.ink.acts`；跨镜有意复现同一线稿须写 `recallOf` 或 `variantOf`，否则构建期拦截。内置 31 件 `lib:` 见 `src/linework/library.ts`，改动库后跑 `python scripts/linework_index.py --write-crops` 同步 `src/linework/crops.ts`。
- 动词：`enter` 按部位描出（首次出现）；`point` 点名一个部位（换强调色加粗、其余压暗、旁边手写名）；`drop` 部位脱落；`swap` 同位置换状态；`count` 复制成 N 个（`"n": 5`）；`mark` 落一个勾 / 叉 / 圈（`"mark": "check"`）；`exit` 退场。
- 常用部位 id：`rocket` → `payload` / `stage1` / `stage2`；`phone` → `body` / `screen` / `button`；`house` → `roof` / `body` / `door` / `window`；`person` → `head` / `body` / `arms` / `legs`；其余看 `library.ts` 的 `parts`。
- **库里没有时自拼**：`"draw": "shapes:[...]"`，基本形 `rect` / `circle` / `path` / `line` / `dots`，坐标是线稿自己的 0–100 方框。画法：轮廓剪影 → 加 1–2 个识别特征 → 停。
- **硬边界**：只画外形轮廓与门窗、屏幕、把手这类识别特征，一个小场景 3–6 个元素；不画剖面、内部结构、零件拆解、爆炸图、粒子流、管路循环。控制在 ≤10 个形；超过 12 个记 P1「画得太深了」，第 12 个之后的形不会画出来。
- 单帧强调色面积 ≤15%：`point` 只给一个部位换色，不铺色块。线稿只读皮肤的墨色与一个强调色，不自带颜色。
- **常见错误**：线稿没出现 → `draw` 名字拼错；部位点不亮 → `target` 不是该线稿的 part id；线稿被裁 → 有线稿的镜头引擎自动保持全景，不要手写 `cinema`；单部位特写只剩半边 → 手写的 `fit` 比图形小，`python scripts/linework_index.py --geometry` 会点名超出的一边。`fit` 是 0–100 坐标的取景框，必须盖住全部基本形；部位级 `fit` 只在单独选中该部位时生效。

<a id="journal-page"></a>
## 4. 手账页（`layout: "page"`）与直书页（`layout: "type"`）

手账页容器是**纸面本身**，不套圆角卡片；`big` ≤8 字且每页仅一句，`loupe` 全片 ≤2 次且 `zoom` ≤3，`content.figure` 尺寸上限 360，两页手账间穿插讲解组件。

```json
{"layout": "page", "see": "1665 原版铜版画", "content": {"page": "plate", "media": "hooke-plate", "note": "软木薄片", "stamp": "胡克"}}
{"layout": "page", "see": "放大镜细看软木格子", "content": {"page": "loupe", "media": "hooke-plate", "look": [0.52, 0.48], "zoom": 2.4, "note": "一格格空房间"}}
{"layout": "type", "see": "直书页锤子句", "content": {"rows": [{"text": "亮灯未必在"}, {"text": "熄灯一定不在", "mark": 1}]}}
```
