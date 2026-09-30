# 内容 → 视觉介质 路由

> Status: component/routing reference. Implementations live in `assets/lecture-template/src/media.tsx`, `fxkit.tsx`, `kit.tsx`, and `src/components/`.
> This is a menu of candidates—not a diversity requirement. The composition gate checks per-cue visual support and source integrity, not how many media types a film uses.

## 目录

- [1. 要解决的问题](#1-要解决的问题)
- [2. 路由表](#2-路由表)
- [3. A 场景 / B 场景](#3-a-场景--b-场景a-roll--b-roll-的本土化)
- [4. 背景契约](#4-背景契约必读)
- [5. 组件在哪个模块](#5-组件在哪个模块可达性)
- [5.1 组件权威索引（53 件 · 选型只查这一处）](#51-组件权威索引53-件--选型只查这一处)
- [6. 让组件"看得见"：接触表](#6-让组件看得见接触表)
- [7. 自检](#7-自检)

## 1. 要解决的问题

This section helps decide how a topic should be expressed, not how to make every film visually diverse.
Cards, text, diagrams, charts, photographs, code and animation are all legitimate when they serve the
learning task. A repetitive card sequence may fail because its teaching relationships are unclear—not
because it lacks a minimum number of media types. Conversely, a varied film can still be confusing.

Use the map as a selection aid when an appropriate helper exists. The package inventory is not a prompt
to assemble components. Verify that any component used is actually rendered and contributes to the
explanation; if a simple SVG or text layout communicates better, use that instead.

## 2. 路由表

> Each row suggests a likely starting point and when another form may fit. It is not a command to use a
> listed component. A well-chosen default can help authors; no component or medium count is a quality goal.
> Adding reusable dependencies/components remains subject to [dependency-policy.md](dependency-policy.md),
> while an individual film should use only what it needs. Inventory details remain in [§5.1](#51-组件权威索引53-件--选型只查这一处).


| 内容类型 | 视觉介质 | 组件（模块） |
|---|---|---|
| 数据 / 对比 | 趋势 / 分布 / 多值对比 → **`Chart`（`components/`，d3 算刻度与路径）**，按语义选 `variant`：折线（默认）/ `area` 面积 / `stackExpand` 百分比堆叠 / `stream` 河流 / `radar` 多维 / `pie` 份额；只有一个百分比 → `ProgressRing`（fxkit）；只有前后两值成对 → `MetricGrid`（media） |
| 软件流程 / 界面 | 窗口壳 + 内部线框 | `ConsoleWindow`（media）、`HighlightCode` 的窗口壳（components）；**要"弹出来的框"（确认框 / 下拉选择 / 说明气泡 / 提示）→ `OverlayFrame`（components，Radix 弹层）** |
| 技术代码 | 有语法高亮的源码 → **`HighlightCode`（`components/`）**；讲一个字一个字敲出来 → `Typewriter`；讲改了什么 → `DiffView`（均 fxkit） |
| 结构关系 | 两者有连线/路径 → **`PathDraw`（`components/`）**；**"谁连着谁"的网（没有层级也没有方向）→ `NetworkGraph`（components，d3-force）**；逐条列清单 → `Checklist`（toolkit）；只是逐行出现 → `StaggerList`（fxkit） |
| 分步展开 / 折叠面板 | 手风琴 | **`Accordion`（components，Radix）** ← 技能此前**没有**这个形态，遇到只能"再堆一张卡片" |
| 多方案 / 多标签切换 | 标签页 | **`Tabs`（components，Radix）** ← 同上，此前零覆盖 |
| 配置 / 选项 / 参数 | **控件状态随旁白变化**（开关拨动、复选打勾、单选改选、滑块拖动、分段切换、进度推进） | **`ControlStack`（components，Radix 六个纯受控 primitive）** ← 此前完全没有"控件被改变"这个形态，只能写一张文字卡片假装「这个选项被打开了」。帧 → 状态是一张显式的表（`steps: [{at, value}]`），纯函数可复算 |
| 技术栈 / 品牌标识 | 图标墙 | **`IconWall` / `TopicIcon`（components，react-icons：`fa` 品牌 + `fi`/`lu` 线条）** |
| 抽象概念 | 概念图 + 主体 | `StageFrame`（stagekit）+ SVG |
| 强调信息 | 让一句话发光 → **`ShimmerText`**；给整块卡加动效边框 → **`GlowFrame`**（均 `components/`）；逐字砸出来 → `JumpInText`（toolkit）；盖章定论 → `StampSeal`（fxkit） |
| 几何 / 图形强调 | 参数化图形 | **`ShapeDraw` / `SHAPES`（components，@remotion/shapes）** ← 五角星/六边形/星芒/**标注框 callout**/**箭头 arrow**/**心形 heart** 都不用手画。**饼图/份额别找图形件**：有数据用 `Chart variant="pie"`（带扇区百分比 + 图例），只有一个百分比用 `ProgressRing` |
| 指向 / 沿线运动 | 箭头沿路径跑并自动转向 | **`PathDraw` 的 `showArrow`（components，`getTangentAtLength`）** ← 此前要自己差分算切线 |
| 证据 / 细节 | 纯代码局部放大 | `ZoomStage`（skeletons） |
| 指标结论 | 适合时可选 `StatRow`、`MetricGrid` 或 `VerdictBar`；吸底不是必要位置，数值不必动画 |
| 对话 / 交互 / 提示词 | 拟真对话窗 / 气泡 | `ChatThread`（fxkit） |
| 层级 / 树状结构 | 目录树 / 组织图 → `TreeView`；**占比与层级用"面积＝数值"表达 → `TreeView` 的 `variant`：`treemap` 矩形树图 / `pack` 圆形打包 / `sunburst` 旭日图**（均在 `components/`，d3-hierarchy） |
| 地理 / 全球视野 | 地球 / 地图 | **`GeoView`（`components/`，d3-geo + `world-atlas` 陆地轮廓）** ← 画的是**真陆地轮廓**（`land-110m`，55 KB 进 bundle）并可叠经纬度标记点；`projection="flat"`（naturalEarth1）看全局、默认正交投影可 `spin` 自转。**不含国界与地名**（要国界得换 `countries-110m.json` 并另立一件，别偷偷扩 `GeoView` 的语义） |
| 流量 / 转化去向 | 流量图 | **`SankeyChart`（`components/`，d3-sankey）** |
| 真实数据进图 | 图表 | **`Chart` 直接喂 CSV**（`csv="阶段,数量\n…"`，d3-dsv 解析；多序列用 `csvToChartSeries()`；不必再手抄数据数组） |
| 手绘强调 / 圈画 / 下划线 | 手绘风图形 | **`SketchFx`（`components/`，roughjs）** + `sketchCircleArea` / `sketchUnderline` / `sketchBox`，`fillStyle` 六种**确定性**填充（hachure 单排线 / solid 实心 / zigzag / cross-hatch 交叉排线 / dashed 虚线 / zigzag-line；`SketchStyle` 类型里就是这 6 个值。hachure 斜线是手账风招牌）。seed 固定 → 每次渲染同一笔迹。**`'dots'` 已移除**：它的填充器内部无条件调 `Math.random()`，同一帧渲两次像素不一致（实测） |
| 数学 / 公式 | 公式块 | **`MathBlock`（`components/`，katex）**。静态渲染、确定性；此前只能手写 HTML 硬排 |
| 收尾引导 | 二维码 | **`QrCode`（`components/`，qrcode）**。纯计算不联网 |
| 收束 / 漏斗 | 漏斗 / 进度 | `Funnel` `ProgressRing`（fxkit） |
| 场景衔接 | 运镜 + 转场 | **`SceneTransitions`（components，**全部 20 种官方转场已登记**，不必再手写）**、`shotkit` + `insert`（3 式手写转场）。转场名 = 官方包名去掉连字符：`fade` `slide` `wipe` `flip` `clockWipe` `iris` `dissolve` `ripple` `zoomBlur` `filmBurn` `bookFlip` `swap` `crosswarp` `crossZoom` `zoomInOut` `dreamyZoom` `blurSlide` `linearBlur` `pushCut` `none`（= `PRESENTATIONS` 的键）。**11 种是 WebGL 着色器式**（blurSlide / crossZoom / crosswarp / dissolve / dreamyZoom / filmBurn / linearBlur / ripple / swap / zoomBlur / zoomInOut；`pathfx.tsx` 的 `PRESENTATIONS` 里就是这么分组的），**`bookFlip` 属几何式**（纯 CSS/SVG，与 fade/slide/wipe/clockWipe/iris/flip/pushCut/none 一组）。本机无头渲染**实测全部可用**（`diag-upgrade` 页⑥ 逐格截在转场中点，25%/50%/75% 三帧各不同）；`flip` 在 50% 处正好侧对镜头（那一格看着是空的属正常），要看效果就截 25% / 75%。`none` 是硬切。**`@remotion/transitions` 里 `Math.random` 0 处**，全部帧驱动 |
| 快速运镜 / 冲刺 | 速度感 | **本技能不提供运动模糊件**（v3.1.1 已删 `@remotion/motion-blur` 依赖及其两个再导出：全仓库零引用，"速度峰值"也从来不在七种合法运镜意图里）。快甩靠**帧内位移 + 速度线**表达，不要手绘模糊去凑 |
| 让画面"活一点" | 有机抖动 | **`NoiseJitter`（components，noise2D 同种子同结果）** |
| 文字排版 | 反推字号 | **`FitTextBox` / `fitChineseTextOnNLines`（components/fittext）** ← 治卡片文字被裁的正解。图元标签（treemap 格子 / 气泡 / 扇区）用 **`fitNodeLabel`**：宽度与高度**都要**过，反推字号低于 13px 就**降级不画字**并进图例 |
| 逐条揭示 | 遮罩擦除 | **`ClipReveal`（components，clip-path 按帧推进；旧件 `RevealMask` 在 `insert.tsx`）** |

**Instructional requirement:** every narration cue must have readable visual support and every shot must
name the relation it teaches and its actual visual carrier. The carrier may remain static across multiple
cues. There is no minimum number of media types, active components, transitions, layouts or camera moves.
Do not use component variety as a proxy for whether an explanation is clear.

## 3. A 场景 / B 场景（A-roll / B-roll 的本土化）

An A/B-style main/supporting visual is one optional way to preserve context while inspecting a detail. It is
not a required two-track grammar. A direct diagram, a text-only explanation, or one stable image may be
clearer and shorter.

- **Main view**: preserve the subject, data, or claim as the stable context.
- **Detail view**: optionally inspect one relevant part and return to context; no requirement to change media.
- A magnified view or `ZoomStage` can be useful when detail would otherwise be too small, but avoid a zoom when a label or callout is sufficient.

When using a detail insert, return to a state that preserves the relevant context; do not use the insert solely to create motion.

**注意**：v2.9 的 `recipes/EvidenceBridge.tsx` 就是这个思路的图片版实现，可回收使用。

## 4. 背景契约（**必读**）

### 4.1 Background treatment is a design choice

The shipped `paper`, `cel`, `sticker`, and `flat` backgrounds are optional exemplars, not immutable. A project may use, adapt, or omit a background treatment. Whatever the choice, check contrast and obstruction against the actual scene content. When content overlaps an unavoidable decorative region, a local backing plate such as `CoverPanel` may restore legibility:

> **内容压在装饰区之上时，必须坐在 `CoverPanel` 上**（v3.0.1 起 `BackgroundMute` 已删除：它在 paper/sticker 皮肤下必然返回 null，是条死路）。

### 4.2 机制

主题通过 `theme.backgroundDecorZones` 声明装饰区矩形（1920×1080 设计坐标）：
`cel` 4 个、`flat` 2 个、`paper` / `sticker` 为空（本来就干净）。

```tsx
// 局部兜底：给这一块内容一个底托（tone='paper' 走卡片皮肤，tone='wash' 只铺柔和底色）
<CoverPanel x={200} y={640} w={1000} h={220} tone="paper">
  <YourContent />
</CoverPanel>

// 成片级兜底：在装饰区之上、内容之下铺羽化暖底（保留装饰形状可辨）
<CoverPanel x={70} y={92} w={1780} h={846} tone="wash" z={-1} />
```

**z 序铁律（实测踩过，务必照做）**：底托（`CoverPanel`）必须落在**背景之上、内容之下**（`z={-1}`）。

- 整幅垫底的 `tone='wash'` 必须用**负 z**（`z={-1}`）。
  ⚠️ **不要用正 z**：CSS 里正 `z-index` 稳定压过所有 `z-index: auto` 的元素，
  而场景里的构件绝大多数就是 auto —— 实测把 wash 设到 `z=5` 时，整镜内容被压成 15% 不透明，
  全片看起来"大片空白"，排查了很久才发现。
- 局部卡片 `tone='paper'` 用默认 `z={42}`（它是内容的**父节点**，所以不冲突）。
- 整幅 wash **不能是硬边矩形**（见下节），要去掉描边环并羽化四边。

### 4.2.1 底托必须羽化，不能是硬边矩形

整幅垫底的 wash **不能用纯色矩形**——硬边会在下沿留一条肉眼可见的接缝（实测：在 38 秒处
底托下沿横切过爆炸贴，形成一条明显的水平分界线）。用径向渐变让四边柔化进背景装饰：

```tsx
<CoverPanel x={70} y={92} w={1780} h={846} tone="wash" z={-1} pad={0}
  style={{boxShadow: 'none', borderRadius: 0,
    background: `radial-gradient(125% 118% at 50% 50%, ${C.paperBase}F5 58%, ${C.paperBase}D6 82%, ${C.paperBase}00 100%)`}} />
```

同时**去掉 1px 描边环**（`boxShadow: 'none'`），否则会出现一个"贴着内容的方框"。

### 4.3 门禁

`validate-shot-motion.py` 的 P1 检查：若某镜 `contentBand` 与主题装饰区相交但未声明 `cover`，
报"文字可能被装饰吃掉"。级别 P1（警告），成片前人工确认。

### 4.4 Whitespace is allowed

Do not fill a panel or the lower quarter solely to satisfy a density target. Give the actual content a
balanced hierarchy; if a panel feels too large, resize or restyle it when that improves the scene. Keep
legibility and caption space, not occupied-area percentage, as the criterion.

### 4.5 有意覆盖要显式声明（门禁白名单）

`OverlapGate`（渲染期重叠/遮挡门禁）会报告所有文字重叠与被遮挡。**有意**的重叠必须显式标注，
否则会被当成缺陷：

| 场景 | 标注 |
|---|---|
| 显式 handoff 的交接叠帧（当前镜声明 handoff，并与上一镜共享 carrier） | `data-gate-allow="handoff"` |
| 头部/标题的滑变双层 | `data-gate-allow="swap"` |
| 指标新旧数值的替换 | `data-gate-allow="value-swap"` |
| 整块要跳过的区域 | `data-gate-skip` |

**约定**：白名单只允许出现在"同一信息在同一位置替换"和"镜头交接"两类情形；
不允许用白名单掩盖两个不同信息互相压字。

## 5. 组件在哪个模块（可达性）

| 模块 | 内容 | 约定 |
|---|---|---|
| `src/kit.tsx` | `PillTag` `LineIcon`(26 字形) `CheckBadge` `TYPE` | 主题无关原子，工程侧同样可引用 |
| **`src/components/`** | **新封装层（唯一入口 `./components`，27 件 = 本层实现 27，v3.1.1 起无库再导出）：`Accordion` `Tabs` `ControlStack` `OverlayFrame` `NetworkGraph` `HighlightCode` `MathBlock` `TopicIcon` `IconWall` `Chart` `StatRow` `TreeView` `GeoView` `SankeyChart` `QrCode` `SketchFx` `FocusFx` `GlowFrame` `ShimmerText` `ClipReveal` `NoiseJitter` `VerdictBar` `PathDraw` `MorphShape` `ShapeDraw` `SceneTransitions` `FitTextBox`**（+ `SHAPES` / `PRESENTATIONS` / `fitChineseTextOnNLines` 等工具；件数口径见 [fxkit.md](fxkit.md)） | **帧参数名统一是 `f`**；颜色只读 `THEME`；见 [dependency-policy.md](dependency-policy.md) §7 |
| `src/fxkit.tsx` | 9 件（`FitCard` `Typewriter` `StampSeal` `Funnel` `ChatThread` `ProgressRing` `StaggerList` `DiffView` `SkeletonCard`） | **帧参数名是 `frame`** |
| `src/media.tsx` | `ConsoleWindow` `MetricGrid` `StampBanner` | **帧参数名是 `f`** |
| `src/stagekit.tsx` | `StageFrame` `PhaseRail` `useStageMachine`（Attach 已于 v3.1 删除） | `f` |
| `src/skeletons.tsx` | `Corridor` `SplitStage` `ZoomStage` | `f` |
| `src/insert.tsx` | `RevealMask` `useHandoff` `TRANSITIONS` | `f` |
| `src/shotkit.tsx` | `ShotCamera` `CoverPanel` `safeCheck` | `f` |
| `src/index.tsx` | 引擎层，**对场景只导出两个 Composition（`Film4x3` / `Film3x4`）**：`Paper` / `Subtitle` / `Chrome` 是**模块私有 `const`**（未 `export`，场景文件 import 不到，只能用引擎自己的画面）；曾经那 6 件"反 PPT 交互件"定义在本文件内部、零 export 且零渲染，**已于 v3.1 删除**（见 [quality-checklist.md](quality-checklist.md) 的历史注） | 引擎层 |
| `src/toolkit.tsx` | 修辞工具件：`Callout` `Checklist` `JumpInText` | 工具层 |

> **⚠️ 布局陷阱（实测踩过）**：同一容器里**不要混用"文档流内的标题"和"绝对定位组件"**。
> 绝对定位组件的 `x/y` 是相对容器原点的，而文档流内的标题也占着容器顶部——
> 两者会**精确重叠**（实测：走廊场景的"整个过程对你是透明的"和列表第一行叠成了一团乱字）。
> 修法二选一：给绝对定位组件显式 `y`（让它排在标题下方），或把标题也改成绝对定位。

> **⚠️ 帧参数名不一致是一个真实陷阱**：`fxkit` 用 `frame`，v2.10 新增模块用 `f`。
> 给 fxkit 组件传 `f={f}` 会被静默忽略，组件回落到 `useCurrentFrame()`（全局帧），
> 于是动画时间轴整体错位（实测踩过：`Frame NaN` 与"动画早播/晚播"）。
> **给 fxkit 传 `frame={f}`，给新模块传 `f={f}`。** 拿不准就查上表。

## 5.1 组件权威索引（53 件 · 选型只查这一处）

> **这是全技能唯一一份组件清单。** [fxkit.md](fxkit.md) 的清单段只保留 fxkit 自己的参数与动效细节，
> `showcase.tsx` 只保留接触表的版面与版本串（`SHOWCASE_VERSION` —— 它**不在任何画面上渲染**，只是给人读的），源码注释只解释实现——**件数、用途、何时用/别用、接触表页号、
> 使用记录一律以本表为准**。要改组件先改这里，别在别处另起一份清单（本仓库吃过"文档抄文档、数字一路漂"的亏）。

**口径**（逐件点算，可复现）：各模块**对外 `export` 的 React 组件** = `src/components/` 27 件（本层实现 27；v3.1.1 删掉 PieDraw 与两个库再导出后，这一层已无再导出）
+ 其余 8 个模块 26 件（`kit` 3 / `fxkit` 9 / `media` 3 / `stagekit` 2 / `skeletons` 3 / `insert` 1 / `shotkit` 2 / `toolkit` 3）。
**不算件的**：渲染期门禁（`SlotGuard` 与四道 `*Gate`）、主题包件（`Paper` / `Background` / `Grade` / `SubtitleChrome`，
以及 cel / sticker 皮肤导出的 `Burst` / `Tape`）、各模块的大写常量与 type-only 导出。
**帧参数名**：`fxkit` 与 `toolkit` 传 `frame={f}`，其余全部传 `f={f}`（写错静默错位，见 §5 警告）。
（复核命令：对上面 9 个模块文件抽 `^export const X: React.FC` 的 X 去重计数，再与 `src/components/index.ts` 的
导出名单对齐；`SlotGuard` 与四道 Gate 按口径剔除。数出来必须是 **27 + 26 = 53**，不是就说明有件偷偷加了没登记。）

- **接触表列** = `showcase.tsx` 里**真实渲染过的页号**（多页出现就把页号都列出；"未展示" = 接触表上看不见这件）。
- **使用记录列** = 参考片 `assets/lecture-template/src/scenes.tsx`（8 镜，`S1`–`S8`）或引擎 `index.tsx` 里**真实出现过的位置**；
  "未使用" = 这些位置里都找不到它（**不等于"从没渲染过"** —— 真实工程里用到的写在格子里，如 `FocusFx`）。

| 组件 | 一句话用途 | 何时用 | 何时别用 | 接触表 | 使用记录 |
|---|---|---|---|---|---|
| `Accordion`（components） | 手风琴：展开项随帧累积 | 并列要点要**逐项展开/收起**，一屏放不下 | 只是"逐行出现"→`StaggerList`；"被改动的控件"→`ControlStack` | ⑦⑨ | 未使用 |
| `Tabs`（components） | 标签页：激活项由帧号决定 | 2–4 个**对等方案**切换，且"切换"本身是讲解内容 | 不是"切换"而是"被改动"→`ControlStack` | ④⑨ | 未使用 |
| `ControlStack`（components） | 六个受控控件（开关/复选/单选/分段/滑块/进度），`steps:[{at,value}]` 是帧→状态表 | 讲"某个设置被改了"：旁白说到哪、控件变到哪 | 一行一个控件，别把 6 种塞进一镜；控件不是主角时别用（抢戏） | ⑫ | 未使用 |
| `OverlayFrame`（components） | 拟真弹层（dialog/menu/popover/tooltip，Portal 指到画面根） | 讲"弹出来一个框"：确认框 / 下拉 / 气泡 / 提示 | 一次别冒三个；压在背景装饰区时同样要坐 `CoverPanel` | ⑰ | 未使用 |
| `NetworkGraph`（components） | d3-force 关系网（固定迭代 + 显式初值） | "谁连着谁"——无层级、无方向的网 | 有层级时用 `TreeView`（树会凭空造出一个不存在的上下级） | ⑯ | 未使用 |
| `HighlightCode`（components） | 语法高亮 + 行号 + 逐行聚焦 | 要"这是官方/真实代码"的窗口壳（页面形态） | 终端形态→`ConsoleWindow`；逐字敲→`Typewriter`；纯代码路线不做实拍框 | ⑨ | 未使用 |
| `MathBlock`（components） | katex 公式块（静态、确定性） | 有公式/推导要展示（此前只能手写 HTML 硬排） | 无动画——别当装饰塞公式 | ⑭ | 未使用 |
| `TopicIcon`（components） | 单个题材图标（react-icons：`fa` 品牌 + `fi`/`lu` 线条，笔画重量对齐 `LineIcon`） | 技术栈/品牌标识的**单点** | 成排→`IconWall`；图标与内容无关时别用 | ⑫ | 未使用 |
| `IconWall`（components） | 图标墙（弹簧错峰入场） | 技术栈/依赖清单要具象成一堵墙 | 图标不是内容时别用（纯装饰） | ⑩ | 未使用 |
| `Chart`（components） | d3 算刻度与路径；7 个 `variant`（line/area/stack/stackExpand/stream/radar/pie），可直接喂 CSV | 数据/趋势/分布/多值对比；真实数据进图 | 只有一个百分比→`ProgressRing`；只有前后两值→`MetricGrid`；柱状用默认 line + `series` 驱动（未知 `variant` 直接抛错） | ①⑨⑭⑮ | 未使用 |
| `StatRow`（components） | 指标卡一行，数字随帧滚动（字符串值直显） | 报一个大数字；等权指标并排 | 数值已在 `MetricGrid` 里滚动时别重复 | 未展示 | 参考片 S1 |
| `TreeView`（components） | 目录树/组织图 + treemap/pack/sunburst（面积＝数值） | 有层级；或"占比 + 层级"用面积表达 | 无层级的网状关系→`NetworkGraph` | ⑬⑯ | 未使用 |
| `GeoView`（components） | 地球 / 真陆地轮廓（d3-geo + world-atlas `land-110m`） | 地理 / 全球视野；叠经纬度标记点讲"节点/站点分布" | **不含国界与地名**（要国界得换 `countries-110m.json` 并另立一件）；`flat` 与正交两种投影别混用在同一组对比之外 | ⑬ | 未使用（接触表 ⑬ 已渲真地图 + 4 个标记点） |
| `SankeyChart`（components） | 流量图（d3-sankey） | 流量在环节之间怎么分流 | 逐级递减的漏斗→`Funnel` | ⑬ | 未使用 |
| `QrCode`（components） | 二维码（纯计算、不联网） | 收尾引导"扫码看仓库" | 中途别放（观众不会暂停扫码） | ⑬ | 未使用 |
| `SketchFx`（components） | 手绘风图形（roughjs；seed 固定→每次同一笔迹，6 种**确定性** `fillStyle`） | 手绘强调：圈画 / 下划线 / 方框（手账风招牌） | 要精确几何→`ShapeDraw`；`'dots'` 已移除（内部无条件调 `Math.random()`，同帧两次不一致） | ⑭ | 未使用 |
| `FocusFx`（components） | 一镜一次的"注意力动作"（dim / spot / loupe / marker） | 要把注意力压到一块矩形区域 | 一镜一次；画面已有高亮或缩放时别叠 | ⑱（整页专属，四态按帧轮转） | 参考片没用，但真实工程 `overview-film` S8 真的渲了它 |
| `GlowFrame`（components） | 流光边框（conic-gradient 绑帧号） | 强调一瞬（警告感） | 与 `ShimmerText` 二选一别叠；要"真的变了个状态"→`ControlStack` | ⑧⑩ | 未使用 |
| `ShimmerText`（components） | 文字闪过一道光 | 只强调**一句话** | 与 `GlowFrame` 二选一；讲中段用会显浮夸 | ⑧ | 未使用 |
| `ClipReveal`（components） | 遮罩擦除（clip-path 按帧推进） | 逐条揭示（不只是淡入） | 镜头级交接→`RevealMask`（`insert`） | ⑫ | 未使用 |
| `NoiseJitter`（components） | 有机抖动（noise2D 同种子同结果） | 让静止物"活一点"（手绘 / 贴纸感） | 别给**文字**用（抖动伤可读性） | ⑫ | 未使用 |
| `VerdictBar`（components） | 全宽结论条（填满底部，收束场景） | 收束场景，且底部要填满 | 一镜一条；别与 `StampBanner` 同时砸（两条互压底线） | 未展示 | 参考片 S8 |
| `PathDraw`（components） | 描线生长 + 沿线运动的点 / 沿线转向的箭头（`getTangentAtLength`） | 表现两者关系 / 因果；箭头沿路线跑 | 路径短于 200px 时箭头会盖住整条线；已有导轨/时间轴时别叠 | ⑪⑰ | 未使用 |
| `MorphShape`（components） | 形状连续变形（`interpolatePath`） | 讲"同一个东西形态变了" | 没有"变形"语义时别用（纯装饰） | ⑪ | 未使用 |
| `ShapeDraw` / `SHAPES`（components） | 参数化几何（星 / 六边形 / 三角 / 圆 / 星芒 / callout 标注框 / arrow 箭头 / heart / 椭圆 / 矩形） | 需要一个标注框 / 箭头 / 星标，不想手写 path | 图标→`TopicIcon`；形状要有语义，别撒装饰 | ⑩⑰ | 未使用 |
| `SceneTransitions`（components） | 官方 20 种转场全部登记（几何式 9 + 着色器式 11） | 场景衔接要真的"换场"（不止硬切/淡出） | `flip` 在 50% 处正好侧对镜头（那一格看着像空的属正常，要看就截 25%/75%）；`none` 是硬切 | ⑪ | 未使用 |
| `FitTextBox`（components） | 中文反推字号 + 断行（自带字体就绪门） | 固定宽 + 行数上限要定字号（治卡片文字被裁的正解） | 管"卡片多高"用 `FitCard` / `fitH()`（分工不同，见 [fxkit.md](fxkit.md)） | ③⑩⑭ | 未使用 |
| `PillTag`（kit） | 胶囊贴标 | 页眉 kicker、标签行 | 别当正文（小字号） | 未展示 | 参考片 S1 S3 + 引擎页眉 |
| `LineIcon`（kit） | 26 字形线条图标 | 卡片小标题旁的图标 | 大图 / 插图→`TopicIcon` | 未展示 | 参考片 S3 S7（`CardHead`） |
| `CheckBadge`（kit） | 对勾圆徽章 | "已完成"这类状态标记 | 要"盖章"的体量时→`StampSeal` | 未展示 | 参考片 S4 S7 |
| `FitCard`（fxkit） | 防出格卡片（`h` 必须经 `fitH()` 算） | 任何文字卡片 | 禁止手写"看着差不多"的固定高度 | ③ | 参考片 S3 S4 |
| `Typewriter`（fxkit） | 打字机（标点分级停顿、块光标） | "一个字一个字敲出来" | 讲"改了什么"→`DiffView`；整段代码→`HighlightCode` | ② | 参考片 S3 |
| `StampSeal`（fxkit） | 印章砸下（2.6x→1 回弹，-8°） | 盖章定论 | 字数 >4 会溢出圆 | ③ | 参考片 S2 S6 |
| `Funnel`（fxkit） | 尝试漏斗（宽进窄出 + 计数 + 滴落点） | 逐级递减的漏斗 / 收束 | 只有一个百分比→`ProgressRing` | ③ | 参考片 S5 |
| `ChatThread`（fxkit） | 对话气泡（typing 三点→pop，左右交替） | 模拟确有意义的对话 / Prompt 交互 | 依可读高度安排回合；长对话拆镜，避免填充无关气泡 | ④ | 参考片 S7 |
| `ProgressRing`（fxkit） | 进度环（dashoffset 填充 + 中央标签） | **只有一个**百分比 | 多份额对比→`Chart`；有前后值→`MetricGrid` | ① | 参考片 S5 |
| `DiffView`（fxkit） | 补丁 diff（红删绿加，逐行滑入） | 讲"改了什么" | 不是补丁语义（无增无删）时别用 | ② | 参考片 S3 |
| `SkeletonCard`（fxkit） | 骨架→内容（等待 beats 先占位） | 已知要等（拉取 / 计算有过程） | 内容本来就该立刻出现时别用 | ③ | 参考片 S7 |
| `StaggerList`（fxkit） | 级联列表（逐行滑入 + 微旋转） | 顺序本身有助于理解时 | 按阅读节奏实看；错峰过慢可能读成逐条淡入；要完成态→`Checklist` | ① | 参考片 S4 |
| `ConsoleWindow`（media） | 控制台 / 终端窗口介质 | 表现"正在跑"、命令行 | 必须给 `h`，否则高度由内容撑；带行号高亮的代码→`HighlightCode` | ② | 参考片 S1 |
| `MetricGrid`（media） | 指标网格（before→after **替换**，数字滚动） | 有前后值成对 | 只有一个值→`StatRow` | ② | 参考片 S8 |
| `StampBanner`（media） | 结论吸底条（三段式落定 + 底色闪） | 一条结论确需突出时 | 多条结论按教学关系分开，或改用普通文字；不设每片使用次数 | 未展示 | 参考片 S1 S5 S8 |
| `StageFrame`（stagekit） | 活体主体框（header / main / rail / stamp） | 同一主体的状态或关系变化适合放在统一框架中时 | 可只呈现少量关键状态；静态或简单关系用更简洁的图形即可，无最少拍数 | 未展示 | 参考片 S1 S5 S8 |
| `PhaseRail`（stagekit） | 状态进度轨（把状态机显式画出来） | 要把"推进到第几步"给观众看见 | 静态内容别用（没有状态可推） | ④ | 参考片 S1 S5 |
| `Corridor`（skeletons） | 走廊 / 流程骨架（到站 + 停留 + 对勾描线） | 空间化路径能更清楚地表达流程时 | 简单流程也可用直线、标签或静态图；按内容选最简清晰形式 | ⑥ | 参考片 S2 S6 |
| `SplitStage`（skeletons） | 双栏对比骨架（先暗输方，再亮赢方） | 两个**对等**对象对比 | 两方不是同一维度时别用 Split | ⑥ | 参考片 S4 |
| `ZoomStage`（skeletons） | 整体→聚焦→标注→回整体（B 段插入） | 要放大看局部（0.8–2s 取证） | 会缩放，静止元素别用 | ⑥ | 参考片 S3 S7 |
| `RevealMask`（insert） | 镜头级遮罩揭示（ltr/rtl/ttb） | 镜头进场要"揭开" | 逐条揭示→`ClipReveal` | 未展示 | 参考片 8 镜共用的 `Shot` 外壳（实际只有 S3/S7 传了 `reveal`） |
| `ShotCamera`（shotkit） | 受限相机外壳（只做 transform/opacity） | 需要统一镜头变换/透明度外壳时；静态 key 合法 | 运动可选；页眉 / 章节卡 / 字幕应保持稳定，不随主体镜头移动 | 未展示 | 参考片 8 镜 |
| `CoverPanel`（shotkit） | 底托 / 卡片底（`tone='wash'` 必须 `z={-1}` 且羽化） | 内容压到背景装饰区时 | 整幅 wash 不能用正 z、不能是硬边矩形 | 未展示 | 参考片 8 镜 |
| `Callout`（toolkit） | 圈住一处 + 引线 + 手写标注 | 圈住 / 指出一处 | 画面已有高亮时别叠（重复编码） | ⑦ | 参考片 S1 |
| `Checklist`（toolkit） | 带完成态的清单（`done` 后序号变对勾） | 列一份清单、要完成态 | 项 >6 会溢出；只是逐行出现→`StaggerList` | ⑦ | 参考片 S3 |
| `JumpInText`（toolkit） | 逐字跳入（字色激活） | 一句重点确需文字动作强调时 | 普通讲解文字无需跳动；按语义和小屏可读性决定，不设全片次数上限 | ⑧ | 引擎章节条（全片，`index.tsx`） |

**两处缺口（本表如实标出，别当成"覆盖完整"；处置见 [dependency-policy.md](dependency-policy.md) §8）**

- **未上接触表 10 件** = 旧模块 8 件（`PillTag` `LineIcon` `CheckBadge` `StampBanner` `StageFrame` `RevealMask` `ShotCamera` `CoverPanel`）
  + 封装层 2 件（`StatRow` `VerdictBar`）。
  前者**不该进接触表**（原子 / 引擎外壳 / 已在参考片里天天出现，占格子不如留给没有画面的件）；
  后者**该进而没进**：`StatRow` `VerdictBar` 已在参考片里出现（S1 / S8）。
  （`FocusFx` 曾是这一档里最特殊的一件——它所有覆盖层挂 `SCENE_ANCHOR`（`position: fixed` + 场景坐标 +
  zIndex 160），塞进 900×470 的 Tile 会被舞台 transform 变成包含块、把"压暗其余整页"演残，
  所以**进不了格子**。现在它上了第 ⑱ 页：**整页专属**，dim / spot / loupe / marker 每 8 帧轮转一态。
  核验口径要如实：接触表抽帧的两格只取到 **dim / loupe 两态**（四态里覆盖 2/4，抽帧位由页帧号决定，
  碰不齐四态），**spot / marker 两态得以 showcase 成片 mp4 为准**——别拿 JPG 两格当"四态都见过"。
  旧版同列的 PieDraw / CameraMotionBlur / Trail 已删 —— 后两个是**真·零渲染**，按本技能自己的
  「零引用」判据走；PieDraw 被 `Chart variant="pie"` 与 `ProgressRing` 上下夹住、自己没标签没数值。
  第 ⑪ 页空出的那格换成了 pathfx 家族的组合用法：标注框 + 引线。）
- **未使用 25 件**（口径 = 参考片 `scenes.tsx` + 引擎 `index.tsx`；说的是"没进参考片"，**不等于"从没渲染过"**）
  = **全部在新封装层**（`Accordion` … `TreeView`）；旧模块 26 件**全部**在参考片里用过。
  这 25 件**全部在接触表上看得见**（`FocusFx` 在第 ⑱ 页整页专属轮转四态；它在真实工程里也有渲染记录——
  `overview-film` 的 `src/scenes.tsx` `import` 在 L8、`<FocusFx f={f} mode="dim" …/>` 在 L274，
  `shots.ts` 的 S8 `live` / `evidence` 也点了名）。这 25 件是**新旧并存的过渡态**，不算缺陷：
  新件要替掉旧件必须动参考片的 `scenes.tsx`，得单独一轮做。

## 6. 让组件"看得见"：接触表

> **件数与页号只查 [§5.1 组件权威索引](#51-组件权威索引53-件--选型只查这一处)**；本节只讲接触表这个机制本身怎么用、怎么渲。
> 下面提到的"18 件 / 26 件 / 53 件"是**口径说明**，不是清单——清单在 §5.1。

`src/showcase.tsx` 注册了一个 `NotebookVideoShowcase` Composition：
**18 页 × 1 秒**，1920×1080 原生，把旧层的 **18 件**组件（口径：逐个数过 `showcase.tsx` 里真实出现过的 JSX 标签 ——
`fxkit` 9 + `media` 2 + `stagekit` 1（`PhaseRail`）+ `skeletons` 3 + `toolkit` 3，含修辞工具件 3 件；
**另一个口径别混用**：旧模块**对外 export** 是 26 件（`components/index.ts` 的「53 件地板」注释），
差 8 件是因为接触表没有把它们逐件渲染 —— `showcase.tsx` 的 `SHOWCASE_VERSION` 串与本节都按"实际渲染"这一个口径）
+ 第 ⑤ 页 6 种运镜意图 + 第 ⑥ 页四种骨架（`StageFrame` 只在标题里点名、未渲染）
+ 新封装层 10 页（第 ⑨–⑱ 页，25 件：⑨–⑰ 的 24 件 + ⑱ 的 `FocusFx` 整页专属）+ v3.1 新能力 3 页（图表变体 / 层级与关系 / 弹层与形状）全部渲染一遍。
**接触表没覆盖的 10 件**逐件列在 §5.1 的「两处缺口」里（哪些不该进接触表、哪些该进没进，那里都写了）。

```text
node scripts/notebook-video.mjs showcase PROJECT_DIR          # 渲染接触表 mp4（交付规格：2560×1440 / 静音 AAC / 色彩四项回写）
node scripts/notebook-video.mjs showcase-sheet PROJECT_DIR    # 再抽接触表 jpg（select 按帧号取每页第 6/21 帧：两张中段图，6×6 共 36 格）
```

> 交付规格说明：composition 原生画布是 1920×1080，那支 mp4 是**交付物**（`assets/demo/` 里那份），
> 所以渲染时按 4/3 放大到 2560×1440、补一条静音 AAC 音轨、回写色彩四项（v3.1.1 之前这条命令按默认参数跑，
> 出的是 1920×1080 / 无音轨 / 无色彩标记的调试版，会把交付文件静默换成调试版）。

**为什么需要它**：读 props 文档很难想象构件长什么样；让执行 AI **看图选型**，
比读文字描述准确得多。这是"能力存在但不可达"的直接解法。

### 已修复：第 ⑪ 页 `SceneTransitions` 那一格，此前在抽出来的 JPG 里等于看不见（两因一起修）

旧版这一节写的是「只记录，未修」。两个病灶都在，缺一都不能让转场在 JPG 里现身：

- **页内超程**：旧参数 `durations=[20,20,20,20] transitionDuration=10` → 总长 `80 − 3×10 = 50` 帧 > 页 30 帧，
  第 3 个转场（30–40 帧）**整段在页外**，mp4 里也永远看不到；
- **抽样只抽页首帧**：旧 `showcase-sheet` 用 `ffmpeg -vf fps=1,scale=1280:-1,tile=6x3`，每页 30 帧 = 1 秒，
  抽到的恰好是**每页第 0 帧**——在任何转场开始之前，JPG 里只有第一段色块。

修法（本轮，两处都要，改一处没用）：

- `showcase.tsx` 第 ⑪ 页改 `durations=[12,12,12,12] transitionDuration={6}` →
  总长 `4×12 − 3×6 = 30` 帧，三个转场正好落在**第 6–12 / 12–18 / 18–24 帧**，全部页内，mp4 里三段转场齐了；
- `scripts/notebook-video.mjs` 的 `showcase()` 抽帧改为 select 滤镜按帧号精确取帧：
  `-vf "select='eq(mod(n,30),6)+eq(mod(n,30),21)',scale=640:-1,tile=6x6"` →
  每页取**第 6 与第 21 帧**两张中段图（36 帧 = 18 页正好铺满 6×6）。第 ⑪ 页的第 21 帧实测
  正好是第 3 个转场的 50% 处——wipe 的中态在接触表 JPG 里直接看得见；顺带每页都多了一张中段图，
  其它"页中段才有动作"的格也受益。（踩过的坑：先用 `-ss 0.2 + fps=2` 做偏移抽样，实测落点
  偏到第 12/27 帧——seek 与 fps 取整叠加不可靠，才换成按帧号 select，**别再改回去**。）

核验口径：想看 `flip` 这类"50% 处侧对镜头"的转场，仍按 §5.1 `SceneTransitions` 行的提示截 25% / 75%；
默认串的是 `wipe`，抽帧位（6 / 21）不需要为它特殊照顾。

## 7. Review checklist

- [ ] The complete narration is assigned to shots; each shot states its core learning relation and actual visible carrier.
- [ ] Every cue has readable support; a stable diagram may serve multiple cues while it remains relevant.
- [ ] The chosen visual treatment keeps content, background, labels and captions legible together; use a backing panel only when needed.
- [ ] Any component used appears in the scene source and rendered output, and has an instructional/editorial job.
- [ ] Camera transforms and graphics stay in bounds; there is no requirement to move the camera or fill unused space.

---

## 修辞动作 → 组件（v3.0.1）

上面那张表路由的是**内容类型**（数据 / 流程 / 对比…）。这一张列出一些可能的**修辞动作**，供需要时查阅；不需要每镜挑一件组件。若 `live` 写在shot table里，它只是作者注记，不是构图门槛。

| 修辞动作 | 首选 | 备选 | **何时别用** |
|---|---|---|---|
| 圈住/指出一处 | `Callout`（画圈+引线+手写标注，`toolkit.tsx`） | `ZoomStage`（要放大才能用） | 画面已有高亮时别叠（重复编码）；`ZoomStage` 会缩放，静止元素别用 |
| 表现两者关系/因果 | `PathDraw`（描线生长，`components/`） | `Corridor`（隐含顺序） | 已有导轨/时间轴时别叠；**关系是"网"而不是"链"时改用 `NetworkGraph`** |
| 表现"谁连着谁"（无层级、无方向） | `NetworkGraph`（力导向，`components/`） | `TreeView`（有层级时才用） | 别用树硬画网状关系——树会凭空造出一个不存在的上下级 |
| 表现"某个设置被改了" | `ControlStack`（控件状态随旁白变化，`components/`） | `Accordion` `Tabs`（是"展开/切换"，不是"被改动"） | 只呈现解释当下操作所需的控件；若标签拥挤或失去焦点，拆镜或简化 |
| 表现"弹出来一个框" | `OverlayFrame`（dialog / menu / popover / tooltip，`components/`） | `ConsoleWindow`（整块界面，`media.tsx`） | 避免多个弹层同时遮挡信息；若比较本身需要多层，检查层级与阅读顺序 |
| 表现"箭头沿路线跑过去" | `PathDraw` 的 `showArrow`（`components/`，`getTangentAtLength`） | `MorphShape`（形状变形） | 路径短于 200px 时箭头会盖住整条线 |
| 强调一瞬（警告感） | `GlowFrame`（流光边框，`components/`） | `ShimmerText`（只强调一句话时） | 两种强调同时出现时确认各自有不同教学作用，避免重复编码；要"真的变了个状态"就用 `ControlStack` |
| 砸一句结论 | `StampBanner` | — | 多条结论可能挤压画面；按教学关系拆分，或用普通文字/列表 |
| 认证/盖章 | `StampSeal` | — | 字数 >4 会溢出圆 |
| 念一句口号 | `JumpInText`（逐字跳入） / `ShimmerText`（闪光，`components/`） | `StampBanner` | 选择一个适合语气的处理；重复强调可能干扰，但没有通用次数上限 |
| 报一个大数字 | `StatRow`（`components/`，数字随帧滚动） | `MetricGrid`（有前后值时） | 数字已在 `MetricGrid` 里滚动时别重复 |
| 对比两方（对等） | `SplitStage` | `StatRow`（不等权时，`components/`） | 两方不是同一维度时别用 Split |
| 列一份清单 | `Checklist`（带完成态，`toolkit.tsx`） | `StaggerList` | 项目数可能超过组件容量时分组或拆镜；错峰按阅读与旁白校准 |
| 演示一段流程 | `Corridor` | `PathDraw`（描线生长，`components/`） | 简单路径也可直接用静态线、标签或箭头；选择最清楚的表达 |
| 一个主体持续演化 | `StageFrame`（用于确有状态过程时） | `Corridor` | 若内容没有状态变化，静态图或另一种简单构图可能更清楚 |
| 证明"这是官方/真实" | `HighlightCode` 的窗口壳（`components/`） | — | 纯代码路线不做实拍框；能用代码画清的别用实拍（实拍只能走可选生图附加路线） |
| 表现"正在跑/正在写" | `ConsoleWindow` / `HighlightCode` | `Typewriter` | `ConsoleWindow` 一定给 `h`，否则高度由内容撑 |
| 模拟 AI 对话 / Prompt 交互 | `ChatThread`（`fxkit`） | `Tabs`（多方案对比时，`components/`） | 按窗口可读高度安排回合；长对话拆镜，避免无关气泡分散注意 |
| 页面形态 | `HighlightCode` 的窗口壳（`components/`） | `ConsoleWindow`（终端形态） | 终端内容用 `ConsoleWindow`；带行号/高亮的代码用 `HighlightCode` |

**两条边界**：① 可复用组件库扩张遵循 [dependency-policy.md](dependency-policy.md) §8 的“加一件=换掉一件”或说明新增能力与证据；这不意味着单部成片必须替换或堆叠画面元素。② 组件必须执行它擅长的动作并真实出现在成片里；找不到必要用途就不用它。不要把风格多样性当作组件使用目标。
