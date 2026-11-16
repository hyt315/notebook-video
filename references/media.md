# 介质路由、真实素材与背景库

内容 → 介质 → 组件的路由表，真实素材（Commons / Openverse、截图录屏、HTML 截取）与背景库。

本篇各节：

- [内容 → 视觉介质 路由](#media-routing)
- [真实素材：先搜 Wikimedia Commons / Openverse](#commons-media)
- [真实素材（截图 / 录屏 / 动图）](#real-media)
- [HTML and website capture](#html-capture)
- [背景库 · Background library](#background-library)

<a id="media-routing"></a>

## 内容 → 视觉介质 路由

> 状态：**生效**。落地件：`assets/lecture-template/src/media.tsx`、`fxkit.tsx`、`kit.tsx`。
> 门禁：`scripts/validate-composition.py`（介质多样性 ≥3 种）。

### 目录

- [1. 要解决的问题](#1-要解决的问题)
- [2. 路由表](#2-路由表)
- [3. A 场景 / B 场景](#3-a-场景--b-场景a-roll--b-roll-的本土化)
- [4. 背景契约](#4-背景契约必读)
- [5. 组件在哪个模块](#5-组件在哪个模块可达性)
- [5.1 组件权威索引（53 件 · 选型只查这一处）](#51-组件权威索引53-件--选型只查这一处)
- [6. 让组件"看得见"：接触表](#6-让组件看得见接触表)
- [7. 自检](#7-自检)

### 1. 要解决的问题

早期版本的四个场景之所以像 PPT，**不是因为没用图片，而是因为全是同一种介质：卡片 + 文字**。

反过来，真正让视频不像 PPT 的，是**同一支片子里出现了不同的视觉介质**。
这一层解决的就是"这段内容该用什么形式表达"。

同时它也是"给一堆组件让 AI 拼积木"这条路的修复：那种做法失败的原因不是组件不好，
而是**缺"什么时候该用哪个"的决策入口**——组件在仓库里吃灰（实测 34 个库里 32 个引用数为 0）。

### 2. 路由表

> **每行只给一个「首选」**，其余标注了「何时才用」。一行里并列三个平级选项，等于没给建议——
> 实测教训：路由表里有名字的组件照样一件不用（23 件从未出现在任何画面里，其中 **21 件早已登记在本表**）。
> **加组件 = 换掉一件**；总数上限见 [technique.md#dependency-policy](technique.md#dependency-policy) §8。
> 本表管"这段内容该配哪个件"；**"一共有些什么件、每件的用途/边界/接触表页/真实使用记录"只看 [§5.1 组件权威索引](#51-组件权威索引53-件--选型只查这一处)**。


| 内容类型 | 视觉介质 | 组件（模块） |
|---|---|---|
| 数据 / 对比 | 趋势 / 分布 / 多值对比 → **`Chart`（`components/`，d3 算刻度与路径）**，按语义选 `variant`：折线（默认）/ `area` 面积 / `stackExpand` 百分比堆叠 / `stream` 河流 / `radar` 多维 / `pie` 份额；只有一个百分比 → `ProgressRing`（fxkit）；只有前后两值成对 → `MetricGrid`（media） |
| 软件流程 / 界面 | 窗口壳 + 内部线框 | `ConsoleWindow`（media）、`HighlightCode` 的窗口壳（components）；**要"弹出来的框"（确认框 / 下拉选择 / 说明气泡 / 提示）→ `OverlayFrame`（components，纯 div 弹层）** |
| 技术代码 | 有语法高亮的源码 → **`HighlightCode`（`components/`）**；讲一个字一个字敲出来 → `Typewriter`；讲改了什么 → `DiffView`（均 fxkit） |
| 结构关系 | 两者有连线/路径 → **`PathDraw`（`components/`）**；**"谁连着谁"的网（没有层级也没有方向）→ `NetworkGraph`（components，d3-force）**；逐条列清单 → `Checklist`（toolkit）；只是逐行出现 → `StaggerList`（fxkit） |
| 分步展开 / 折叠面板 | 手风琴 | **`Accordion`（components）** ← 技能此前**没有**这个形态，遇到只能"再堆一张卡片" |
| 多方案 / 多标签切换 | 标签页 | **`Tabs`（components）** ← 同上，此前零覆盖 |
| 配置 / 选项 / 参数 | **控件状态随旁白变化**（开关拨动、复选打勾、单选改选、滑块拖动、分段切换、进度推进） | **`ControlStack`（components，六种控件，纯 div）** ← 此前完全没有"控件被改变"这个形态，只能写一张文字卡片假装「这个选项被打开了」。帧 → 状态是一张显式的表（`steps: [{at, value}]`），纯函数可复算 |
| 技术栈 / 品牌标识 | 图标墙 | **`IconWall` / `TopicIcon`（components，simple-icons 品牌 + lucide-react 线条）** |
| 抽象概念 | 概念图 + 主体 | `StageFrame`（stagekit）+ SVG |
| 强调信息 | 让一句话发光 → **`ShimmerText`**；给整块卡加动效边框 → **`GlowFrame`**（均 `components/`）；逐字砸出来 → `JumpInText`（toolkit）；盖章定论 → `StampSeal`（fxkit） |
| 几何 / 图形强调 | 参数化图形 | **`ShapeDraw` / `SHAPES`（components，@remotion/shapes）** ← 五角星/六边形/星芒/**标注框 callout**/**箭头 arrow**/**心形 heart** 都不用手画。**饼图/份额别找图形件**：有数据用 `Chart variant="pie"`（带扇区百分比 + 图例），只有一个百分比用 `ProgressRing` |
| 指向 / 沿线运动 | 箭头沿路径跑并自动转向 | **`PathDraw` 的 `showArrow`（components，`getTangentAtLength`）** ← 此前要自己差分算切线 |
| 证据 / 细节 | 纯代码局部放大 | `ZoomStage`（skeletons） |
| 指标结论 | 一个主角数字 → **`KineticNumber`**（`cinema.tsx`）；一排指标卡（数字随帧滚动）→ **`StatRow`**；全宽收束条 → **`VerdictBar`**（均在 `components/`）；前后值成对 → `MetricGrid`；吸底盖章 → `StampBanner`（media） |
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
| 快速运镜 / 冲刺 | 速度感 | **本技能不提供运动模糊件**（已删 `@remotion/motion-blur` 依赖及其两个再导出：全仓库零引用，"速度峰值"也从来不在七种合法运镜意图里）。快甩靠**帧内位移 + 速度线**表达，不要手绘模糊去凑 |
| 让画面"活一点" | 有机抖动 | **`NoiseJitter`（components，noise2D 同种子同结果）** |
| 文字排版 | 反推字号 | **`FitTextBox` / `fitChineseTextOnNLines`（components/fittext）** ← 治卡片文字被裁的正解。图元标签（treemap 格子 / 气泡 / 扇区）用 **`fitNodeLabel`**：宽度与高度**都要**过，反推字号低于 13px 就**降级不画字**并进图例 |
| 逐条揭示 | 遮罩擦除 | **`ClipReveal`（components，clip-path 按帧推进；旧件 `RevealMask` 在 `insert.tsx`）** |

**硬约束（门禁 P0）**：全片 ≥3 种不同介质；**每个讲解场景 ≥1 个活性组件**（会随旁白变化状态的演示件），
"一盒子弹"式纯卡片堆禁止。

### 3. A 场景 / B 场景（A-roll / B-roll 的本土化）

参考项目用 A/B 双轨解决"碎片感 vs 呆板感"的两难。讲解片里不需要实拍剪辑意义上的双轨，只需要：

- **A 场景 = 主线演化轨**：一个主体常驻，随旁白换内部状态（`StageFrame`）。
  **不是卡片轮播。**
- **B 场景 = 辅助取证轨**：换一种**视觉介质**插入 0.8–2 秒（24–60 帧），说完即回。
  **B 不是"另一个场景"，而是 A 的一次注意力转移**；不留残片、不另起场景。
- 实现：`skeletons.ZoomStage`（B 段由场景自身在区间外返回 `null`，物理上保证无残片）
  （整体→聚焦→标注→回整体）。

**A↔B 的关系**：B 结束时必须回到 A 的同一状态，观众不丢上下文。

**注意**：早期的 `recipes/EvidenceBridge.tsx` 就是这个思路的图片版实现，可回收使用。

### 4. 背景契约（**必读**）

#### 4.1 背景图是锁定的、好看的，不换

两套皮肤 `flat` / `cel` 都用固定资产背景位图（16:9 一张），**画幅级、高对比**的装饰（cel 的左下爆炸贴、
右下速度线；flat 的右下卡通角色）。它们很好看，**不要替换、不要重绘**。

但**内容压到装饰上时，文字会被吃掉**。所以契约是：

> **内容压在装饰区之上时，必须坐在 `CoverPanel` 上**（`BackgroundMute` 已删除）。

#### 4.2 机制

主题通过 `theme.backgroundDecorZones` 声明装饰区矩形（1920×1080 设计坐标，三张背景变体的并集）：
`cel` 6 个、`flat` 4 个。

```tsx
// 局部兜底：给这一块内容一个底托（tone='paper' 走卡片皮肤，tone='wash' 只铺柔和底色）
<CoverPanel x={200} y={640} w={1000} h={220} tone="paper">
  <YourContent />
</CoverPanel>
```

**没有成片级整幅底托。** 三张背景变体（main / chapter / quiet）的中央约 70% 都是安静的安全区，
装饰只在四边与四角；整幅半透明 wash 会把四角的吉祥物和装饰洗成"幽灵"，所以模板的 `Shot` 外壳已经删掉它。
内容真压到装饰区时，只给**那一块**垫 `tone='paper'` 的底托。

**z 序铁律（务必照做）**：底托（`CoverPanel`）必须落在**背景之上、内容之下**（`z={-1}`）。

- 若确实要用 `tone='wash'` 垫一块局部底色，必须用**负 z**（`z={-1}`）。
  ⚠️ **不要用正 z**：CSS 里正 `z-index` 稳定压过所有 `z-index: auto` 的元素，
  而场景里的构件绝大多数就是 auto —— 实测把 wash 设到 `z=5` 时，整镜内容被压成 15% 不透明，
  全片看起来"大片空白"，排查了很久才发现。
- 局部卡片 `tone='paper'` 用默认 `z={42}`（它是内容的**父节点**，所以不冲突）。
- wash **不能是硬边矩形**（见下节），要去掉描边环并羽化四边；而且不要铺满整幅。

#### 4.2.1 底托必须羽化，不能是硬边矩形

wash **不能用纯色矩形**——硬边会在下沿留一条肉眼可见的接缝（实测：在 38 秒处
底托下沿横切过爆炸贴，形成一条明显的水平分界线）。用径向渐变让四边柔化进背景装饰：

```tsx
<CoverPanel x={70} y={92} w={1780} h={846} tone="wash" z={-1} pad={0}
  style={{boxShadow: 'none', borderRadius: 0,
    background: `radial-gradient(125% 118% at 50% 50%, ${C.paperBase}F5 58%, ${C.paperBase}D6 82%, ${C.paperBase}00 100%)`}} />
```

同时**去掉 1px 描边环**（`boxShadow: 'none'`），否则会出现一个"贴着内容的方框"。

#### 4.3 门禁

`validate-shot-motion.py` 的 P1 检查：若某镜 `contentBand` 与主题装饰区相交但未声明 `cover`，
报"文字可能被装饰吃掉"。级别 P1（警告），成片前人工确认。

#### 4.4 面板要填满，不要留大片空白

用户会明确感到"白色面板比以前差"，而逐帧比对证明**像素没变**——变的感受来自**空白**：
满的面板像纸，空的面板像刺眼的白盒子。所以：

- 面板的内容带要按可用高度排布（本模板 `StageFrame` 的 main 区高度 = `h − pad×2 − headH − stampH`），
  不要在 520px 高的框里只放 196px 高的内容；
- 拿不准时**居中**内容，或缩小框高，而不是让下方留 58% 空白；
- **不要**用降低不透明度来"救"空白面板——那只会让文字更难读。

#### 4.5 有意覆盖要显式声明（门禁白名单）

`OverlapGate`（渲染期重叠/遮挡门禁）会报告所有文字重叠与被遮挡。**有意**的重叠必须显式标注，
否则会被当成缺陷：

| 场景 | 标注 |
|---|---|
| 镜头边界的交接叠帧 | `data-gate-allow="handoff"` |
| 头部/标题的滑变双层 | `data-gate-allow="swap"` |
| 指标新旧数值的替换 | `data-gate-allow="value-swap"` |
| 整块要跳过的区域 | `data-gate-skip` |

**约定**：白名单只允许出现在"同一信息在同一位置替换"和"镜头交接"两类情形；
不允许用白名单掩盖两个不同信息互相压字。

### 5. 组件在哪个模块（可达性）

| 模块 | 内容 | 约定 |
|---|---|---|
| `src/kit.tsx` | `PillTag` `LineIcon`(26 字形) `CheckBadge` `TYPE` | 主题无关原子，工程侧同样可引用 |
| **`src/components/`** | **新封装层（唯一入口 `./components`，27 件 = 本层实现 27，无库再导出）：`Accordion` `Tabs` `ControlStack` `OverlayFrame` `NetworkGraph` `HighlightCode` `MathBlock` `TopicIcon` `IconWall` `Chart` `StatRow` `TreeView` `GeoView` `SankeyChart` `QrCode` `SketchFx` `FocusFx` `GlowFrame` `ShimmerText` `ClipReveal` `NoiseJitter` `VerdictBar` `PathDraw` `MorphShape` `ShapeDraw` `SceneTransitions` `FitTextBox`**（+ `SHAPES` / `PRESENTATIONS` / `fitChineseTextOnNLines` 等工具；件数口径见 [components.md#fxkit](components.md#fxkit)） | **帧参数名统一是 `f`**；颜色只读 `THEME`；见 [technique.md#dependency-policy](technique.md#dependency-policy) §7 |
| `src/fxkit.tsx` | 9 件（`FitCard` `Typewriter` `StampSeal` `Funnel` `ChatThread` `ProgressRing` `StaggerList` `DiffView` `SkeletonCard`） | **帧参数名是 `frame`** |
| `src/media.tsx` | `ConsoleWindow` `MetricGrid` `StampBanner` | **帧参数名是 `f`** |
| `src/stagekit.tsx` | `StageFrame` `PhaseRail` `useStageMachine`（Attach 已删除） | `f` |
| `src/skeletons.tsx` | `Corridor` `SplitStage` `ZoomStage` | `f` |
| `src/insert.tsx` | `RevealMask` `useHandoff` `TRANSITIONS` | `f` |
| `src/shotkit.tsx` | `ShotCamera` `CoverPanel` `safeCheck` | `f` |
| `src/index.tsx` | 引擎层，**对场景不导出任何组件**（只有 16:9 一个 Composition `NotebookVideoFilm`，`Film4x3` / `Film3x4` 已删除）：`Paper` / `Subtitle` / `Chrome` 是**模块私有 `const`**（未 `export`，场景文件 import 不到，只能用引擎自己的画面）；曾经那 6 件"反 PPT 交互件"定义在本文件内部、零 export 且零渲染，**已删除**（见 [checks.md#quality-checklist](checks.md#quality-checklist) 的历史注） | 引擎层 |
| `src/toolkit.tsx` | 修辞工具件：`Callout` `Checklist` `JumpInText` | 工具层 |

> **⚠️ 布局陷阱**：同一容器里**不要混用"文档流内的标题"和"绝对定位组件"**。
> 绝对定位组件的 `x/y` 是相对容器原点的，而文档流内的标题也占着容器顶部——
> 两者会**精确重叠**（实测：走廊场景的"整个过程对你是透明的"和列表第一行叠成了一团乱字）。
> 修法二选一：给绝对定位组件显式 `y`（让它排在标题下方），或把标题也改成绝对定位。

> **⚠️ 帧参数名不一致是一个真实陷阱**：`fxkit` 用 `frame`，其它模块用 `f`。
> 给 fxkit 组件传 `f={f}` 会被静默忽略，组件回落到 `useCurrentFrame()`（全局帧），
> 于是动画时间轴整体错位（症状：`Frame NaN` 与"动画早播/晚播"）。
> **给 fxkit 传 `frame={f}`，给新模块传 `f={f}`。** 拿不准就查上表。

### 5.1 组件权威索引（53 件 · 选型只查这一处）

> **这是全技能唯一一份组件清单。** [components.md#fxkit](components.md#fxkit) 的清单段只保留 fxkit 自己的参数与动效细节，
> `showcase.tsx` 只保留接触表的版面与版本串（`SHOWCASE_VERSION` —— 它**不在任何画面上渲染**，只是给人读的），源码注释只解释实现——**件数、用途、何时用/别用、接触表页号、
> 使用记录一律以本表为准**。要改组件先改这里，别在别处另起一份清单（本仓库吃过"文档抄文档、数字一路漂"的亏）。

**口径**（逐件点算，可复现）：各模块**对外 `export` 的 React 组件** = `src/components/` 27 件（本层实现 27；删掉 PieDraw 与两个库再导出后，这一层已无再导出）
+ 其余 8 个模块 26 件（`kit` 3 / `fxkit` 9 / `media` 3 / `stagekit` 2 / `skeletons` 3 / `insert` 1 / `shotkit` 2 / `toolkit` 3）。
**不算件的**：渲染期门禁（`SlotGuard` 与四道 `*Gate`）、主题包件（`Paper` / `Background` / `Grade` / `SubtitleChrome`，
以及 cel 皮肤导出的 `Burst`）、各模块的大写常量与 type-only 导出。
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
| `TopicIcon`（components） | 单个题材图标（simple-icons 品牌 + lucide-react 线条，笔画重量对齐 `LineIcon`） | 技术栈/品牌标识的**单点** | 成排→`IconWall`；图标与内容无关时别用 | ⑫ | 未使用 |
| `IconWall`（components） | 图标墙（弹簧错峰入场） | 技术栈/依赖清单要具象成一堵墙 | 图标不是内容时别用（纯装饰） | ⑩ | 未使用 |
| `Chart`（components） | d3 算刻度与路径；7 个 `variant`（line/area/stack/stackExpand/stream/radar/pie），可直接喂 CSV | 数据/趋势/分布/多值对比；真实数据进图 | 只有一个百分比→`ProgressRing`；只有前后两值→`MetricGrid`；柱状用默认 line + `series` 驱动（未知 `variant` 直接抛错） | ①⑨⑭⑮ | 未使用 |
| `StatRow`（components） | 指标卡一行，数字随帧滚动（字符串值直显） | 报一个大数字；等权指标并排 | 数值已在 `MetricGrid` 里滚动时别重复 | 未展示 | 参考片 S1 |
| `KineticNumber`（cinema，引擎运动件，不计入 53 件） | 关键数字的动态排版：计数 + 落定弹出 + 下划线扫入，字号 170–380 | 一镜的主角就是一个数（耗时、倍数、降幅）；讲到这个数的那一拍 | 一镜里并排三个以上的数（用 `StatRow` / `MetricGrid`）；全片超过 35% 的镜都用它 | 未展示 | 演示片片 S1 / S4 / S7 / S8 |
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
| `MorphShape`（components） | 形状连续变形（flubber：任意两闭合形状；`engine="remotion"` 用 `interpolatePath`） | 讲"同一个东西形态变了" | 没有"变形"语义时别用（纯装饰） | ⑪ | 未使用 |
| `ShapeDraw` / `SHAPES`（components） | 参数化几何（星 / 六边形 / 三角 / 圆 / 星芒 / callout 标注框 / arrow 箭头 / heart / 椭圆 / 矩形） | 需要一个标注框 / 箭头 / 星标，不想手写 path | 图标→`TopicIcon`；形状要有语义，别撒装饰 | ⑩⑰ | 未使用 |
| `SceneTransitions`（components） | 官方 20 种转场全部登记（几何式 9 + 着色器式 11） | 场景衔接要真的"换场"（不止硬切/淡出） | `flip` 在 50% 处正好侧对镜头（那一格看着像空的属正常，要看就截 25%/75%）；`none` 是硬切 | ⑪ | 未使用 |
| `FitTextBox`（components） | 中文反推字号 + 断行（自带字体就绪门） | 固定宽 + 行数上限要定字号（治卡片文字被裁的正解） | 管"卡片多高"用 `FitCard` / `fitH()`（分工不同，见 [components.md#fxkit](components.md#fxkit)） | ③⑩⑭ | 未使用 |
| `PillTag`（kit） | 胶囊贴标 | 页眉 kicker、标签行 | 别当正文（小字号） | 未展示 | 参考片 S1 S3 + 引擎页眉 |
| `LineIcon`（kit） | 26 字形线条图标（lucide-react） | 卡片小标题旁的图标 | 大图 / 插图→`TopicIcon` | 未展示 | 参考片 S3 S7（`CardHead`） |
| `CheckBadge`（kit） | 对勾圆徽章 | "已完成"这类状态标记 | 要"盖章"的体量时→`StampSeal` | 未展示 | 参考片 S4 S7 |
| `FitCard`（fxkit） | 防出格卡片（`h` 必须经 `fitH()` 算） | 任何文字卡片 | 禁止手写"看着差不多"的固定高度 | ③ | 参考片 S3 S4 |
| `Typewriter`（fxkit） | 打字机（标点分级停顿、块光标） | "一个字一个字敲出来" | 讲"改了什么"→`DiffView`；整段代码→`HighlightCode` | ② | 参考片 S3 |
| `StampSeal`（fxkit） | 印章砸下（2.6x→1 回弹，-8°） | 盖章定论 | 字数 >4 会溢出圆 | ③ | 参考片 S2 S6 |
| `Funnel`（fxkit） | 尝试漏斗（宽进窄出 + 计数 + 滴落点） | 逐级递减的漏斗 / 收束 | 只有一个百分比→`ProgressRing` | ③ | 参考片 S5 |
| `ChatThread`（fxkit） | 对话气泡（typing 三点→pop，左右交替） | 模拟 AI 对话 / Prompt 交互 | 条数建议 2–3 条（1 问 + 1~2 答），否则溢出窗口高度 | ④ | 参考片 S7 |
| `ProgressRing`（fxkit） | 进度环（dashoffset 填充 + 中央标签） | **只有一个**百分比 | 多份额对比→`Chart`；有前后值→`MetricGrid` | ① | 参考片 S5 |
| `DiffView`（fxkit） | 补丁 diff（红删绿加，逐行滑入；`before`/`after` 由 jsdiff 算行） | 讲"改了什么" | 不是补丁语义（无增无删）时别用 | ② | 参考片 S3 |
| `SkeletonCard`（fxkit） | 骨架→内容（等待 beats 先占位） | 已知要等（拉取 / 计算有过程） | 内容本来就该立刻出现时别用 | ③ | 参考片 S7 |
| `StaggerList`（fxkit） | 级联列表（逐行滑入 + 微旋转） | 只是"逐行出现"、防 bullets 堆砌 | 同句内相邻至少 12 帧（见 [draftpaper.md#reveal-rules](draftpaper.md#reveal-rules)）；要完成态→`Checklist` | ① | 参考片 S4 |
| `ConsoleWindow`（media） | 控制台 / 终端窗口介质 | 表现"正在跑"、命令行 | 必须给 `h`，否则高度由内容撑；带行号高亮的代码→`HighlightCode` | ② | 参考片 S1 |
| `MetricGrid`（media） | 指标网格（before→after **替换**，数字滚动） | 有前后值成对 | 只有一个值→`StatRow` | ② | 参考片 S8 |
| `StampBanner`（media） | 结论吸底条（三段式落定 + 底色闪） | 砸一句结论、吸底 | 一镜别砸两条 | 未展示 | 参考片 S1 S5 S8 |
| `StageFrame`（stagekit） | 活体主体框（header / main / rail / stamp） | 一个主体持续演化（≥5 拍） | 只有 2–3 拍时别用（状态机撑不起来） | 未展示 | 参考片 S1 S5 S8 |
| `PhaseRail`（stagekit） | 状态进度轨（把状态机显式画出来） | 要把"推进到第几步"给观众看见 | 静态内容别用（没有状态可推） | ④ | 参考片 S1 S5 |
| `Corridor`（skeletons） | 走廊 / 流程骨架（到站 + 停留 + 对勾描线） | 演示一段流程 | 站点 <3 个时改用 `StaggerList` | ⑥ | 参考片 S2 S6 |
| `SplitStage`（skeletons） | 双栏对比骨架（先暗输方，再亮赢方） | 两个**对等**对象对比 | 两方不是同一维度时别用 Split | ⑥ | 参考片 S4 |
| `ZoomStage`（skeletons） | 整体→聚焦→标注→回整体（B 段插入） | 要放大看局部（0.8–2s 取证） | 会缩放，静止元素别用 | ⑥ | 参考片 S3 S7 |
| `RevealMask`（insert） | 镜头级遮罩揭示（ltr/rtl/ttb） | 镜头进场要"揭开" | 逐条揭示→`ClipReveal` | 未展示 | 参考片 8 镜共用的 `Shot` 外壳（实际只有 S3/S7 传了 `reveal`） |
| `ShotCamera`（shotkit） | 受限相机外壳（只做 transform/opacity） | 每一镜都要（相机就是镜头语言） | 页眉 / 章节卡 / 字幕要放在它**之外**（否则被运镜带动） | 未展示 | 参考片 8 镜 |
| `CoverPanel`（shotkit） | 局部底托 / 卡片底（`tone='wash'` 必须 `z={-1}` 且羽化） | 内容压到背景装饰区时 | 不铺整幅、不能用正 z、不能是硬边矩形 | 未展示 | 参考片 8 镜 |
| `Callout`（toolkit） | 圈住一处 + 引线 + 手写标注 | 圈住 / 指出一处 | 画面已有高亮时别叠（重复编码） | ⑦ | 参考片 S1 |
| `Checklist`（toolkit） | 带完成态的清单（`done` 后序号变对勾） | 列一份清单、要完成态 | 项 >6 会溢出；只是逐行出现→`StaggerList` | ⑦ | 参考片 S3 |
| `JumpInText`（toolkit） | 逐字跳入（字色激活） | 念一句口号（钩子与收尾） | 全片最多 1–2 处；讲解中段用会显浮夸 | ⑧ | 引擎章节条（全片，`index.tsx`） |

**两处缺口（本表如实标出，别当成"覆盖完整"；处置见 [technique.md#dependency-policy](technique.md#dependency-policy) §8）**

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

### 6. 让组件"看得见"：接触表

> **件数与页号只查 [§5.1 组件权威索引](#51-组件权威索引53-件--选型只查这一处)**；本节只讲接触表这个机制本身怎么用、怎么渲。
> 下面提到的"18 件 / 26 件 / 53 件"是**口径说明**，不是清单——清单在 §5.1。

`src/showcase.tsx` 注册了一个 `NotebookVideoShowcase` Composition：
**18 页 × 1 秒**，1920×1080 原生，把旧层的 **18 件**组件（口径：逐个数过 `showcase.tsx` 里真实出现过的 JSX 标签 ——
`fxkit` 9 + `media` 2 + `stagekit` 1（`PhaseRail`）+ `skeletons` 3 + `toolkit` 3，含修辞工具件 3 件；
**另一个口径别混用**：旧模块**对外 export** 是 26 件（`components/index.ts` 的「53 件地板」注释），
差 8 件是因为接触表没有把它们逐件渲染 —— `showcase.tsx` 的 `SHOWCASE_VERSION` 串与本节都按"实际渲染"这一个口径）
+ 第 ⑤ 页 6 种运镜意图 + 第 ⑥ 页四种骨架（`StageFrame` 只在标题里点名、未渲染）
+ 新封装层 10 页（第 ⑨–⑱ 页，25 件：⑨–⑰ 的 24 件 + ⑱ 的 `FocusFx` 整页专属）+ 新能力 3 页（图表变体 / 层级与关系 / 弹层与形状）全部渲染一遍。
**接触表没覆盖的 10 件**逐件列在 §5.1 的「两处缺口」里（哪些不该进接触表、哪些该进没进，那里都写了）。

```text
node scripts/notebook-video.mjs showcase PROJECT_DIR          # 渲染接触表 mp4（交付规格：2560×1440 / 静音 AAC / 色彩四项回写）
node scripts/notebook-video.mjs showcase PROJECT_DIR --sheet   # 只要接触表 jpg（select 按帧号取每页第 6/21 帧：两张中段图，6×6 共 36 格）
```

> 交付规格说明：composition 原生画布是 1920×1080，那支 mp4 是**交付物**（组件接触表成片），
> 所以渲染时按 4/3 放大到 2560×1440、补一条静音 AAC 音轨、回写色彩四项（这条命令曾按默认参数跑，
> 出的是 1920×1080 / 无音轨 / 无色彩标记的调试版，会把交付文件静默换成调试版）。

**为什么需要它**：读 props 文档很难想象构件长什么样；让执行 AI **看图选型**，
比读文字描述准确得多。这是"能力存在但不可达"的直接解法。

#### 已修复：第 ⑪ 页 `SceneTransitions` 那一格，此前在抽出来的 JPG 里等于看不见（两因一起修）

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
  其它"页中段才有动作"的格也受益。（注意：先用 `-ss 0.2 + fps=2` 做偏移抽样，实测落点
  偏到第 12/27 帧——seek 与 fps 取整叠加不可靠，才换成按帧号 select，**别再改回去**。）

核验口径：想看 `flip` 这类"50% 处侧对镜头"的转场，仍按 §5.1 `SceneTransitions` 行的提示截 25% / 75%；
默认串的是 `wipe`，抽帧位（6 / 21）不需要为它特殊照顾。

### 7. 自检

- [ ] 全片 ≥3 种介质，且每个讲解场景 ≥1 个活性组件；
- [ ] 每一段内容都问过"这块内容该用什么**介质**"，而不是"用哪张卡片"；
- [ ] 压到背景装饰区的内容都坐在 `CoverPanel` 上；
- [ ] 用到的构件都能在 **§5.1 组件权威索引**里指到；新构件要同时登记进索引（并视情形加进接触表——
      引擎外壳 / 原子件不需要进接触表，见 §5.1「两处缺口」）；
- [ ] 没有把 wash 底板的 z 设到内容之上。

---

### 修辞动作 → 组件

上面那张表路由的是**内容类型**（数据 / 流程 / 对比…）。这一张路由的是**你此刻要做的修辞动作**——
"我要强调这一点""我要念一句口号""我要表现两者的关系"。写场景前先在这里查一遍：
**`live` 里写的每个名字，都应该能在这张表（或 `components.md#fxkit` 的组件表）里指到。**

| 修辞动作 | 首选 | 备选 | **何时别用** |
|---|---|---|---|
| 圈住/指出一处 | `Callout`（画圈+引线+手写标注，`toolkit.tsx`） | `ZoomStage`（要放大才能用） | 画面已有高亮时别叠（重复编码）；`ZoomStage` 会缩放，静止元素别用 |
| 表现两者关系/因果 | `PathDraw`（描线生长，`components/`） | `Corridor`（隐含顺序） | 已有导轨/时间轴时别叠；**关系是"网"而不是"链"时改用 `NetworkGraph`** |
| 表现"谁连着谁"（无层级、无方向） | `NetworkGraph`（力导向，`components/`） | `TreeView`（有层级时才用） | 别用树硬画网状关系——树会凭空造出一个不存在的上下级 |
| 表现"某个设置被改了" | `ControlStack`（控件状态随旁白变化，`components/`） | `Accordion` `Tabs`（是"展开/切换"，不是"被改动"） | 一行一个控件，别把 6 种控件塞进一镜；控件是主角时才用（否则它抢戏） |
| 表现"弹出来一个框" | `OverlayFrame`（dialog / menu / popover / tooltip，`components/`） | `ConsoleWindow`（整块界面，`media.tsx`） | 弹层别一次冒三个；弹层压在背景装饰区时同样要坐 `CoverPanel` |
| 表现"箭头沿路线跑过去" | `PathDraw` 的 `showArrow`（`components/`，`getTangentAtLength`） | `MorphShape`（形状变形） | 路径短于 200px 时箭头会盖住整条线 |
| 强调一瞬（警告感） | `GlowFrame`（流光边框，`components/`） | `ShimmerText`（只强调一句话时） | 二选一，别叠用；要"真的变了个状态"就用 `ControlStack`，不是靠倾斜 |
| 砸一句结论 | `StampBanner` | — | 一镜别砸两条（两条会互压底线） |
| 认证/盖章 | `StampSeal` | — | 字数 >4 会溢出圆 |
| 念一句口号 | `JumpInText`（逐字跳入） / `ShimmerText`（闪光，`components/`） | `StampBanner` | 全片最多 1–2 处（钩子与收尾）；讲解中段用会显浮夸 |
| 报一个大数字 | `StatRow`（`components/`，数字随帧滚动） | `MetricGrid`（有前后值时） | 数字已在 `MetricGrid` 里滚动时别重复 |
| 对比两方（对等） | `SplitStage` | `StatRow`（不等权时，`components/`） | 两方不是同一维度时别用 Split |
| 列一份清单 | `Checklist`（带完成态，`toolkit.tsx`） | `StaggerList` | 项 >6 会溢出；`StaggerList` 的 `stagger` 取 12（相邻开始至少 12 帧） |
| 演示一段流程 | `Corridor` | `PathDraw`（描线生长，`components/`） | 站点 <3 个时改用 `StaggerList` |
| 一个主体持续演化 | `StageFrame`（≥5 拍） | `Corridor` | 只有 2–3 拍时别用（状态机撑不起来） |
| 证明"这是官方/真实" | `HighlightCode` 的窗口壳（`components/`） | — | 纯代码路线不做实拍框；能用代码画清的别用实拍（需要实拍时用用户提供 / Commons / 授权图片，技能不调用生图模型） |
| 表现"正在跑/正在写" | `ConsoleWindow` / `HighlightCode` | `Typewriter` | `ConsoleWindow` 一定给 `h`，否则高度由内容撑 |
| 模拟 AI 对话 / Prompt 交互 | `ChatThread`（`fxkit`） | `Tabs`（多方案对比时，`components/`） | 对话条数建议 2–3 条（1 问 + 1~2 答），避免溢出窗口高度 |
| 页面形态 | `HighlightCode` 的窗口壳（`components/`） | `ConsoleWindow`（终端形态） | 终端内容用 `ConsoleWindow`；带行号/高亮的代码用 `HighlightCode` |

**两条纪律**：① 加组件 = **换掉**画面里的一个元素，不是往里加元素；② 一个组件只有落在"它擅长的那个修辞动作"上才算数——
找不到对应动作就别加（为凑多样性堆组件，是这张表要防的事）。

<a id="commons-media"></a>

## 真实素材：先搜 Wikimedia Commons / Openverse

> 工具：`scripts/commons-search.py`（只用 Python 标准库；下载后的入库 / 转码复用 `prepare-media.py`）。
> 原则：**每个选题先搜一次**。1665 年的铜版画、第一张 X 光片、真实的显微照片、一段历史录音——真东西几乎总能让片子更好。
> 能找到就用；找不到也没关系，写清搜了什么（搜索记录会落进 `manifests/commons-log.json`，导演层门禁看它）。

### 两个源

| 源 | 规模 / 内容 | 接口 | 为什么用它 |
|---|---|---|---|
| [Wikimedia Commons](https://commons.wikimedia.org/) | 1 亿多个文件：图片、视频、声音；每个文件都有结构化许可元数据（`extmetadata`） | MediaWiki Action API `https://commons.wikimedia.org/w/api.php`，免 key | 首选：覆盖最大、元数据最规整、大量公有领域历史图版 |
| [Openverse](https://openverse.org/)（MIT，WordPress 基金会维护） | 聚合 Flickr、博物馆图片与 Freesound、Jamendo 等声音 | `https://api.openverse.org/v1/`，免 key | 补声音（Commons 的声音搜索大半是读音录音）与博物馆图；请求时只要 `cc0,pdm,by` |

没有引入 pywikibot（重、要配账号）或 mwclient（第三方依赖，违背"scripts 只用标准库"）：直接 HTTP 的薄客户端足够。

### 三条命令

```text
# 1) 搜。带 --project 会记搜索日志、缓存 API 响应（.cache/commons/，同一查询不重复打 API）
python scripts/commons-search.py search "Hooke Micrographia cork" --project ./my-video
python scripts/commons-search.py search "pencil writing" --type audio --project ./my-video
python scripts/commons-search.py search "cork cells microscope" --source openverse --project ./my-video

# 2) 选一条入库：查许可、写 url / license / credit / 结构化署名，走 prepare-media 转码与尺寸登记
python scripts/commons-search.py add ./my-video "File:Micrographia Schem 11.jpg" --id hooke-plate --width 2560
python scripts/commons-search.py add ./my-video "openverse:audio:<id>" --id scratch --trim 0 4

# 3) 交付前写成片署名清单（也给发布简介用）
python scripts/commons-search.py credits ./my-video     # → CREDITS.md
```

**按声音分类筛**：`--audio-category music|sound_effect`，只配 `--source openverse --type audio`，对应 Openverse API 的
`category` 查询参数（官方文档：<https://api.openverse.org/v1/#tag/audio/operation/audio_search>，可选值 `audiobook` / `music` /
`news` / `podcast` / `pronunciation` / `sound_effect`，这里只开放配乐 `music` 和音效 `sound_effect` 两类）。
它和 Commons 的 `--category`（Commons 分类）是两回事，不能混用；许可门禁不变（请求仍只要 `cc0,pdm,by`，结果再过一遍白名单）。

```text
python scripts/commons-search.py search "rain" --type audio --source openverse --audio-category sound_effect
```

> 2026-10-29 实测：Openverse 线上 API 带 `category` 时对 "rain" 返回 0 条（sound_effect）、对 "piano" 返回 HTTP 500（music），
> 不带 `category` 正常返回。参数名与取值以官方文档为准；线上筛选恢复前，可以先不加分类搜，再按标题挑。

搜索结果每条给出：标题、尺寸、许可（已归一）、作者、页面链接；不合格的许可直接不列。

### 许可白名单

| 许可 | 默认 | 说明 |
|---|---|---|
| 公有领域（PD-*、PDM）、CC0 | ✓ | 不要求署名，本工具照样署名（好习惯，也方便核查） |
| CC BY 1.0–4.0 | ✓ | 必须署名：作者 + 许可 + 来源链接（TASL），自动生成并强制上屏 |
| CC BY-SA | ✗（`--allow-by-sa` 才收） | "相同方式共享"：用它做的改编作品（整条片子很可能算）须以 CC BY-SA 发布。短视频平台的发布条款通常与此冲突，缺省不用；收了会在 manifest 记 `shareAlike:true`，`validate-media` 提示一次，CREDITS.md 写明义务 |
| GFDL、FAL、NC、ND、无版本的 "Attribution"、Flickr 的 "No known restrictions"、未知 | ✗ | 一律排除（"无已知限制" ≠ 公有领域） |

### 放进画面：用 craft 组件，不要裸贴

| 素材 | 组件（[components.md#craft-kit](components.md#craft-kit)） |
|---|---|
| 历史图版、扫描件、手稿 | `ArchivePhoto`（纸托 + 编目签署名）；要"看近"用 `LoupeMedia` |
| 现代照片、标本照 | `PinnedPhoto`（白边 + 胶带 + 手写说明 + 署名） |
| 声音 | `MediaAudio`（按帧起播；拟音音量放在音效阶梯附近） |
| 界面截图 / 录屏 | 仍用 `MediaFrame`（[media.md#real-media](media.md#real-media)） |

署名规则：`source:"web"` 的素材**一定**在画面上显示署名；片尾 / 简介再放 `CREDITS.md` 全文。
清晰度：`validate-media` 按组件的字面量 `w` / `h` 与推近倍数算放大比，>1.5 倍会糊 → P0（用 `--width` 取更大的缩略图或缩小显示框）。

### API 礼仪

- 必带 User-Agent（项目地址 + 联系方式），可用环境变量 NOTEBOOK_VIDEO_UA 覆盖；
- 串行请求，相邻请求 ≥1 秒，`maxlag=5`；429 / 503 按 `Retry-After` 退避，最多重试 4 次；
- 缩略图走 Commons 的 `iiurlwidth`（服务器端缩放），不下原图大文件。

### 测试

`tests/test_commons.py`：离线夹具（`tests/fixtures/`）覆盖许可归一、BY-SA 排除、署名串、Openverse 结果解析、`--audio-category` 请求参数与许可过滤、CREDITS 生成；不访问网络。

<a id="real-media"></a>

## 真实素材（截图 / 录屏 / 动图）

把用户给的或合法找来的截图、短录屏放进片子里，和组件场景混排（例如 Git 协作课里放一张真实的 PR 页面截图）。
外观沿用默认组件风格的卡片语言：`MediaFrame` = 主题卡片（`THEME.Paper`）+ 可选外壳（browser 地址栏 / window 三圆点 / device 手机边框）+ 署名徽章。

### 什么时候用真实素材，什么时候用组件画

| 用真实素材 | 用组件画（默认） |
|---|---|
| 观众以后要在**那个界面**上操作（GitHub PR 页、设置页、报错弹窗） | 讲原理、讲结构、讲数字（组件更清楚，也能逐步出现） |
| 「这是真的」本身就是论据（真实报错、真实数据面板） | 素材里的字太小、太乱，推近后也读不清 |
| 一个短操作过程（≤10 秒录屏） | 找不到许可兼容的素材 → **一律用组件重画** |

### 素材从哪来（按优先级）

1. 用户自己给的文件（`source: "user"`）；
2. 自己截的图 / 自己录的屏（官方文档页、自己的仓库）—— 也记 `source: "user"`，`credit` 写来源；
3. 许可宽松的图库：Wikimedia Commons（CC0 / CC-BY / CC-BY-SA）、Pexels、Unsplash、Pixabay —— 记 `source: "web"`，**必须**写 `url` / `license` / `credit`，署名会自动显示在画面上。

**绝不**使用别人的视频 / 图片而没有兼容许可（NC 非商用、ND 禁止演绎、全部权利保留、来源不明都不行）。拿不准就用组件重画。

### 三步

```text
python "<SKILL_DIR>/scripts/prepare-media.py" ./my-video --add ./pr.png --id pr-page --region diff 0.01 0.31 0.69 0.17
python "<SKILL_DIR>/scripts/prepare-media.py" ./my-video --add ./demo.mov --id clip --trim 2.0 9.5          # 视频自动转 H.264 恒定 30fps、去音轨
python "<SKILL_DIR>/scripts/validate-media.py" ./my-video                                                  # make-video 也会自动跑
```

Windows：`scripts\notebook-video.cmd prepare-media` 同参数。素材进 `public/media/`，登记在 `manifests/media.json`（同步一份到 `src/media.json`）。

`manifests/media.json` 每条：`{id, file, kind: image|video|gif, source: user|web, url, license, credit, trimStartSec, trimEndSec, focusRegions: [{id, x, y, w, h}], muted}`。
区域坐标是 **0–1 的相对值**（相对原图宽高）。`muted` 缺省 true；写 `false` 才保留原声（门禁会提示）。动图会被转成 MP4（`kind` 变 `video`，帧驱动播放）。

### 手写场景里用

```tsx
import {MediaFrame} from './media-frame';
<MediaFrame f={f} id="pr-page" x={200} y={200} w={1060} h={662} chrome="browser"
  focus="diff" focusAt={b[1]} highlight={['merge']} highlightAt={b[2]}
  callouts={[{region: 'diff', text: '只改了三行', at: b[1] + 20}]} />
```

- `focus`：在卡片**内部**推近到某个区域（不露出素材外的空白）；也可以只在镜头表 `cinema.focus` 推近整张卡片——二选一，别叠两层大倍数。
- `highlight`：只描框不推近；`callouts`：区域旁边的一句话标签。
- 视频从入场帧 `at` 开始播，`trimStartSec`→`trimEndSec` 播完停在最后一帧。全部由帧号驱动。
- `src/media.json` 必须存在（模板自带空的 `{"items": []}`）。

### auto 草稿里用（story.json）

顶层写 `media` 列表（`file` 相对 story.json），镜头写 `"layout": "media"`：

```json
"media": [{"id": "pr-page", "file": "pr.png", "source": "user", "focusRegions": [{"id": "diff", "label": "改动", "x": 0.01, "y": 0.31, "w": 0.69, "h": 0.17}]}],
"shots": [{"layout": "media", "lines": ["先看中间的 {{改动|diff}}。"], "content": {"media": "pr-page", "chrome": "browser", "caption": "绿色是新增"}}]
```

台词里 `{{词|区域id}}` → 念到时给那个区域描框并推近镜头。完整例子：`examples/real-media/git-pr.story.json`（截图是脚本生成的占位图）。

### 门禁（validate-media.py）

P0：文件不存在 / 类型不符；放大超过 1.5 倍（含区域推近，按 1080p 交付）；视频不是 H.264 + 恒定 30fps + yuv420p；
`source: web` 缺 url / license / credit 或许可不兼容；引用了不存在的区域；区域坐标出界；`src/media.json` 未同步；场景源码自己画或关掉署名徽章。
P1：`muted: false`；登记了没用到；2K 交付时放大超过 1.5 倍。

### 高亮与推近的注意事项

- `highlight` / `focus` 的区域框画在视口坐标里：4 px 橙色描边 + 白内圈 + 抬升阴影，区域外压一层 0.16 的淡暗幕，缩小看也一眼能找到；区域推近后露出不足 90% 的框不画（不会出现被切掉的半个框）。
- 镜头表 `cinema.focus` 推近画面别处时，旁边的 MediaFrame 卡片可能被推出画面一半——给那条 focus 写 `keep: {x,y,w,h}`（卡片的矩形），引擎会降低推近倍数把两者都装下。
- `w` / `h` 请写数字或同文件 `const`（`w={W}`、`w={W * 0.6}` 都能量）；写成布局对象字段时 validate-media 量不出放大倍数，只按占满画布估并给 P1 提醒。

### Highlight & push-in notes

Region highlights are drawn in viewport space (4 px orange stroke, white inner ring, lift shadow, 0.16 veil outside); boxes < 90 % visible after a region zoom are hidden. When a shot-level `cinema.focus` pushes in elsewhere, add `keep: {x,y,w,h}` for the MediaFrame card. Write `w`/`h` as numbers or same-file consts so validate-media can measure upscaling.

<a id="html-capture"></a>

## HTML and website capture

Use this route only when the user explicitly asks to record an existing interactive website. New notebook explainers use the canonical Remotion project instead.

### Preferred website route: deterministic frames

Expose a frame-controlled function such as `window.renderAt(seconds)` or drive animation time from a query parameter. For every output frame:

1. Load the local page in Chromium.
2. Set the exact animation time.
3. Capture a PNG at the delivery dimensions.
4. Encode the ordered PNG sequence with FFmpeg.
5. Add narration and audio in a separate assembly pass.

This is more reproducible than real-time screen capture and avoids dropped frames, cursor movement, browser chrome and notification leaks.

### Fallback: real-time recording

Use only when the page cannot expose deterministic time. Hide browser chrome, notifications and the pointer. Fix viewport size and device scale. Record a silent master first, then assemble clean audio afterward.

Never substitute real-time recording for the Remotion renderer merely because both use Chromium. Never treat recording as validation. Inspect the resulting video stream duration, dimensions, frame rate and scene boundaries.

<a id="background-library"></a>

## 背景库 · Background library

> 每个皮肤原有 `main / chapter / quiet` 三张锁定背景；背景库再给每个手作皮肤（journal / papercut / archive）
> 新增 8 张、flat / cel 各新增 5 张风格各异、符合皮肤媒介的背景，旧的三张原样保留并入库（标 legacy）。
> Every craft skin gains 8 backgrounds and flat / cel gain 5 each; the three original rasters stay, marked legacy.

### 1. 怎么用 / Usage

#### 换纸粒度 `bgMode`/ How often the paper changes

`manifests/shots.json` 顶层的 `bgMode` 决定多久换一次背景：

| `bgMode` | 行为 | 默认给谁 |
|---|---|---|
| `"chapter"` | 只在章节首镜换纸，章内所有镜头沿用同一张；跨章不与上一章同一张 | journal / papercut / archive（手作皮肤：全片是"一本手账"，逐镜换纸会打断媒介连续性） |
| `"film"` | 全片一张纸 | —（想要最强的"一本书"感时手动写） |
| `"shot"` | 逐镜轮换（下面的规则） | flat / cel |

- `chapter` / `film` 模式下那张纸要撑满章内的常规镜头，所以只从 `roles` 含 `main`、且没有标 `busy` 的背景里挑。
- **改回逐镜轮换：** 顶层写 `"bgMode": "shot"`。**完全不轮换：** `"bgRotate": false`（优先级高于 `bgMode`）。
- 显式写了 `bg` 的镜头永远用它自己的，只影响那一镜，章内其他镜头照样沿用章节纸。
- `validate-backgrounds --shots` 只在 `bgMode=shot` 时把"相邻两镜同一张"记 P1；`chapter` / `film` 模式同章同纸是设计如此，不报。

**装饰重的背景 `"busy": true`：** 便签墙、窗花、洒金笺、祥云、挂笺、红纸衬边、集中线、放射光在 `backgrounds.json` 里标了 `busy`。
自动选择时它们**不会分给 `main` 角色**（也不会当章节纸），只给章节卡或安静镜；想用在某一镜就显式写 `bg`。

#### 逐镜轮换（`bgMode: "shot"`）/ Per-shot rotation

`resolve-shots` 按镜头角色从库里给每镜挑一张：

| 镜头 | 角色 | 候选 |
|---|---|---|
| 章节首镜（`src/film.ts` 的 `CHAPTER_SHOTS`；没有就看 `chapter` 名变化） | `chapter` | 本皮肤 `roles` 含 `chapter` 的背景 |
| `zones ≥ 4` 的信息密集镜 | `quiet` | `roles` 含 `quiet` 的背景 |
| 其余 | `main` | `roles` 含 `main`、且不是 `busy` 的背景 |

挑法是纯函数：最久没用过的优先（从没用过的最先），同分按 `sha1(bgSeed:镜号:id)` 定序；**永不与上一镜同一张**（候选只剩一张时除外）。
同一分镜表 + 同一 `bgSeed` → 同一结果。想换一套组合，在 `manifests/shots.json` 顶层写 `"bgSeed": 7`（任意值）。

**指定某一镜：** 在那一镜写 `bg`：

```jsonc
{ "id": "S3", "bg": "ruled" }            // 简写：本皮肤的 journal/ruled
{ "id": "S4", "bg": "journal/oldpage" }  // 全名
{ "id": "S5", "bg": "quiet" }            // 原有三张之一（main / chapter / quiet），照旧可用
```

写了不存在的名字或别的皮肤的背景，`resolve-shots` 直接报错并列出本皮肤可选的名字。

**关掉轮换：** `manifests/shots.json` 顶层写 `"bgRotate": false`。没有 `manifests/backgrounds.json` 的旧工程
本来就不轮换，`resolve-shots` 的输出逐字节不变。

**看一眼全部背景：** `python scripts/dev/bg-gallery.py out.jpg`（需要 numpy + pillow；每张图都按 96 px 交付字号压一行墨色字幕，不加衬底，即门禁量的最坏情况）。

#### 引擎怎么画 / How the engine draws it

`resolve-shots` 把选中的库 id 写进 `src/shots.ts` 的 `bg`，文件路径写进 `bgFile`；`src/index.tsx` 的 `Backdrop`
有 `bgFile` 就直接铺这张 2560×1440 的图（`objectFit: cover`，底色 `palette.paperBase`），没有就按原有的 `main / chapter / quiet` 走 `THEME.Background`。
相邻两镜背景不同时交叉淡化 10 帧，背景随摄影机视差移动。`Theme` 接口没有变。

### 2. 门禁 / Gates

`scripts/validate-backgrounds.py`（标准库；CLI：`notebook-video validate-backgrounds`；`make-video` 构建期自动跑）：

| 级别 | 判据 |
|---|---|
| P0 | manifest 缺字段；文件不在 `public/` 下或不存在；sha256 不符（改图没重跑生成器） |
| P0 | 许可不在白名单（PD / CC0-1.0 / CC-BY-2.0–4.0 / Apache-2.0）；CC BY 缺署名或来源链接；Commons 来源缺标题 / 链接 / 作者 / 原许可 |
| P0 | 不是亮底：整幅平均相对亮度 < 0.55 |
| P0 | 字幕区（交付坐标 x 391–2169、y 1236–1404）：皮肤墨色 vs 区内平均 < 7:1，或 vs 区内最暗 5 %（4 px 模糊后）< 4.5:1。按「字幕衬底不存在」量：journal 本来就没有衬底，其余皮肤有衬底，这条是保底 |
| P1 | 中央 70 % 起伏（1/8 降采样后亮度标准差）> 0.05：背景可能和内容抢 |
| P1 | 皮肤缺某个角色的背景（轮换会退回到全部背景里挑） |
| P1 | `--shots`：分镜里相邻两镜同一张背景（仅 `bgMode=shot` 时报；只可能来自显式 `bg`） |

亮度 / 对比度指标在生成时算好写进 manifest 并与 sha256 绑定；维护者用 `python scripts/dev/bg_metrics.py assets/lecture-template` 从像素按同一算法重算比对（numpy + pillow；单元测试会跑）。
`--min-per-skin journal=8,…` 只数新增的库背景（不含 legacy 三张），CI 与 `validate-skill` 用它守住数量。

### 3. 来源与做法 / Where they come from

按用户「不造轮子」的原则，优先级：

1. **Paper Shaders**（[paper-design/shaders](https://github.com/paper-design/shaders)，`@paper-design/shaders@0.0.82`，Apache-2.0）——纸纹（冷压水彩纸、长纤维宣纸、
   帘纹纸、旧纸 foxing、揉皱折痕）、mesh 渐变、点阵、半调网点。它是 WebGL：因为逐帧 WebGL 在纯 CPU（SwiftShader）上太贵而暂缓。
   做法是**离线预渲一次**：`scripts/dev/prerender-paper-shaders.py` 用无头 Chromium 把 `scripts/dev/paper-shaders.spec.json` 里每个着色器
   以静态参数（speed 0、固定 seed）渲成 2560×1440 PNG，再由生成器合成、压成 WebP 入库。**渲染期零 WebGL、零新 npm 依赖**。
2. **Wikimedia Commons 的公有领域 / CC0 纹理**（用 `scripts/commons-search.py` 搜，CC0 / PD 优先）：牛皮纸（Coyau，PD）、
   粗麻布（Poly Haven「Hessian 380」，CC0）、1630 年荷兰古地图（PD）。生成器取图时重新核对 Commons 页面上的许可，变了就拒绝。
3. **确定性程序生成**（numpy + pillow，固定 seed，2× 超采样抗锯齿）：横线 / 方格 / 坐标纸、便签、剪纸窗花 / 祥云 / 挂笺 / 洒金、
   档案袋扣绳、报纸版式（灰条，不含真实文字，避免 OCR 门禁误读）、胶片齿孔、账簿栏线、漫画分格 / 集中线 / 网点。纸底复用 `make-craft-textures.py`。

重建（只有维护者需要；普通用户永远不跑）：

```bash
pip install playwright numpy pillow && playwright install chromium
python scripts/dev/prerender-paper-shaders.py          # → ~/.cache/notebook-video/paper-shaders/renders/*.png
python scripts/dev/make-bg-library.py                   # → public/bg/lib/*.webp + manifests/backgrounds.json（sha256 + 指标）
python scripts/dev/bg_metrics.py assets/lecture-template
python scripts/validate-backgrounds.py assets/lecture-template --min-per-skin journal=8,papercut=8,archive=8,flat=4,cel=4
```

同一输入两次构建逐字节相同（已验证）。体积：34 张库背景 WebP 共约 2.7 MB（有损 q82；两张大面积浅色渐变用 q95 保住抖动、防色带）。
纸纹的 1 px 颗粒先轻微模糊再编码：H.264 交付时本来就会丢掉这个频段，留着只会让文件大三倍。

**加自己的背景**：把 2560×1440 的图放进工程 `public/bg/lib/`，在工程的 `manifests/backgrounds.json` 里照现有条目加一条（`source` / `license` / `attribution`
必填，`sha256` 自己算，`metrics` 用 `python scripts/dev/bg_metrics.py 图片` 的输出），再重跑 `resolve-shots`。BY-SA / NC / ND 不收。

### 4. 清单与许可 / Inventory and licences

Paper Shaders 与程序生成的图由本仓库生成，随仓库以 Apache-2.0 发布；Commons 来源的图保留原许可（PD / CC0），署名照样写上（好习惯，也便于核查）。
完整字段（seed、着色器参数、合成步骤、sha256、对比度指标）见 `assets/lecture-template/manifests/backgrounds.json`。

#### journal

| id | 名称 | 角色 | 来源 | 许可 | 署名 / 出处 |
|---|---|---|---|---|---|
| `journal/ruled` | 横线本 | main / quiet | Paper Shaders 预渲 | Apache-2.0 | `ps-coldpress` · @paper-design/shaders@0.0.82 |
| `journal/grid` | 方格本（线圈） | main / chapter | Paper Shaders 预渲 | Apache-2.0 | `ps-coldpress` · @paper-design/shaders@0.0.82 |
| `journal/dots` | 点阵本 | main / quiet | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1103 |
| `journal/kraft` | 牛皮纸本 | main / chapter | Wikimedia Commons | PD | [File:Kraft tileable 1024x1024.png](https://commons.wikimedia.org/wiki/File:Kraft_tileable_1024x1024.png) · Coyau (own work) |
| `journal/watercolor` | 水彩纸 | chapter / main | Paper Shaders 预渲 | Apache-2.0 | `ps-coldpress` · @paper-design/shaders@0.0.82 |
| `journal/sticky` | 便签墙 | chapter / main | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1106 |
| `journal/oldpage` | 旧书页 | main / chapter | Paper Shaders 预渲 | Apache-2.0 | `ps-oldpage` · @paper-design/shaders@0.0.82 |
| `journal/graph` | 坐标纸 | quiet / main | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1108 |
| `journal/main` | 棉纸·常规 *(legacy)* | main | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |
| `journal/chapter` | 棉纸·章节 *(legacy)* | chapter | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |
| `journal/quiet` | 棉纸·安静 *(legacy)* | quiet | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |

#### papercut

| id | 名称 | 角色 | 来源 | 许可 | 署名 / 出处 |
|---|---|---|---|---|---|
| `papercut/hongzhi` | 红纸衬边 | chapter | Paper Shaders 预渲 | Apache-2.0 | `ps-xuan` · @paper-design/shaders@0.0.82 |
| `papercut/xuan` | 宣纸 | main / quiet | Paper Shaders 预渲 | Apache-2.0 | `ps-xuan` · @paper-design/shaders@0.0.82 |
| `papercut/kraft` | 牛皮纸·红绳 | main / chapter | Wikimedia Commons | PD | [File:Kraft tileable 1024x1024.png](https://commons.wikimedia.org/wiki/File:Kraft_tileable_1024x1024.png) · Coyau (own work) |
| `papercut/origami` | 折纸纹 | main / quiet | Paper Shaders 预渲 | Apache-2.0 | `ps-origami` · @paper-design/shaders@0.0.82 |
| `papercut/lattice` | 窗花角 | chapter / main | Paper Shaders 预渲 | Apache-2.0 | `ps-xuan` · @paper-design/shaders@0.0.82 |
| `papercut/sajin` | 洒金笺 | main / chapter | Paper Shaders 预渲 | Apache-2.0 | `ps-xuan` · @paper-design/shaders@0.0.82 |
| `papercut/cloud` | 祥云 | chapter / main | Paper Shaders 预渲 | Apache-2.0 | `ps-xuan` · @paper-design/shaders@0.0.82 |
| `papercut/menjian` | 挂笺 | chapter | Paper Shaders 预渲 | Apache-2.0 | `ps-xuan` · @paper-design/shaders@0.0.82 |
| `papercut/main` | 米纸·常规 *(legacy)* | main | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |
| `papercut/chapter` | 米纸·章节 *(legacy)* | chapter | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |
| `papercut/quiet` | 米纸·安静 *(legacy)* | quiet | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |

#### archive

| id | 名称 | 角色 | 来源 | 许可 | 署名 / 出处 |
|---|---|---|---|---|---|
| `archive/envelope` | 档案袋 | chapter / main | Wikimedia Commons | PD | [File:Kraft tileable 1024x1024.png](https://commons.wikimedia.org/wiki/File:Kraft_tileable_1024x1024.png) · Coyau (own work) |
| `archive/newsprint` | 旧报纸 | main | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1302 |
| `archive/map` | 古地图 | chapter / main | Wikimedia Commons | PD | [File:Helmink Antique map of Holland by Anonymous 3rd state by Frederick de Wit 1630.jpg](https://commons.wikimedia.org/wiki/File:Helmink_Antique_map_of_Holland_by_Anonymous_3rd_state_by_Frederick_de_Wit_1630.jpg) · Anonymous, 3rd state by Frederick de Wit (1630); scan Leen Helmink |
| `archive/catalog` | 卡片目录 | main / quiet | Paper Shaders 预渲 | Apache-2.0 | `ps-laid` · @paper-design/shaders@0.0.82 |
| `archive/filmstrip` | 胶片灯箱 | main / chapter | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1305 |
| `archive/linen` | 展柜布面 | main / quiet | Wikimedia Commons | CC0-1.0 | [File:Hessian 380 diff 8k (Rico Cilliers and colormass via Poly Haven).jpg](https://commons.wikimedia.org/wiki/File:Hessian_380_diff_8k_(Rico_Cilliers_and_colormass_via_Poly_Haven).jpg) · Rico Cilliers (processing), colormass (photography) via Poly Haven |
| `archive/ledger` | 登记簿 | quiet / main | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1307 |
| `archive/vellum` | 描图纸 | quiet / main | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1308 |
| `archive/main` | 灯箱·常规 *(legacy)* | main | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |
| `archive/chapter` | 灯箱·章节 *(legacy)* | chapter | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |
| `archive/quiet` | 灯箱·安静 *(legacy)* | quiet | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |

#### flat

| id | 名称 | 角色 | 来源 | 许可 | 署名 / 出处 |
|---|---|---|---|---|---|
| `flat/mesh-dawn` | 晨光渐变 | main / quiet | Paper Shaders 预渲 | Apache-2.0 | `ps-mesh-dawn` · @paper-design/shaders@0.0.82 |
| `flat/mesh-mint` | 薄荷渐变 | main / quiet | Paper Shaders 预渲 | Apache-2.0 | `ps-mesh-mint` · @paper-design/shaders@0.0.82 |
| `flat/dotgrid` | 点阵 | quiet / main | Paper Shaders 预渲 | Apache-2.0 | `ps-dotgrid` · @paper-design/shaders@0.0.82 |
| `flat/sunrise` | 暖角渐变 | chapter / main | Paper Shaders 预渲 | Apache-2.0 | `ps-grain-sun` · @paper-design/shaders@0.0.82 |
| `flat/shapes` | 几何角饰 | chapter / main | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1405 |
| `flat/main` | 天空吉祥物·常规 *(legacy)* | main | AI 生成 | Apache-2.0 | 见 `manifests/visual-assets.json` |
| `flat/chapter` | 天空吉祥物·章节 *(legacy)* | chapter | AI 生成 | Apache-2.0 | 见 `manifests/visual-assets.json` |
| `flat/quiet` | 天空吉祥物·安静 *(legacy)* | quiet | AI 生成 | Apache-2.0 | 见 `manifests/visual-assets.json` |

#### cel

| id | 名称 | 角色 | 来源 | 许可 | 署名 / 出处 |
|---|---|---|---|---|---|
| `cel/halftone` | 网点角 | main / chapter | Paper Shaders 预渲 | Apache-2.0 | `ps-halftone-corners` · @paper-design/shaders@0.0.82 |
| `cel/speedlines` | 集中线 | chapter | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1502 |
| `cel/panels` | 分格边 | main / chapter | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1503 |
| `cel/screentone` | 渐变网点 | main / quiet | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1504 |
| `cel/sunburst` | 放射光 | chapter | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1505 |
| `cel/main` | 漫画角饰·常规 *(legacy)* | main | AI 生成 | Apache-2.0 | 见 `manifests/visual-assets.json` |
| `cel/chapter` | 漫画角饰·章节 *(legacy)* | chapter | AI 生成 | Apache-2.0 | 见 `manifests/visual-assets.json` |
| `cel/quiet` | 漫画角饰·安静 *(legacy)* | quiet | AI 生成 | Apache-2.0 | 见 `manifests/visual-assets.json` |

---

### 选纸：从「按角色轮换」到「按内容 + 版式」

每张背景多了一个 `use` 块（`manifests/backgrounds.json`）：

```json
"use": {
  "layouts": ["page", "component"],   // 这张纸能承载哪些版式
  "tone": "warm",                     // 冷暖（连续性参考）
  "fits": ["science", "craft"],       // 适合哪些题材
  "note": "点阵极淡、满幅均匀，真图版与组件都不抢"
}
```

#### 三个判定，按顺序生效

1. **版式**（最硬）：`page` = 手账页（要放真图版 + 大字 + 印章，必须中心干净、边角不抢）；
   `component` = 组件镜（卡片盖住中间，容得下中等纹理）；`chapter` = 纯字卡（可以最花）。
   一镜如果是手账页，**就算它刚好开了一章**也按 page 挑纸——章节首镜不降级。
   这条实测抓过一个真 bug：S1 是 page，却因为是章节首镜拿到了 `cel/speedlines`（全幅集中线），
   真图版直接废掉。
2. **题材**（可选）：`story.json` 顶层写 `"topic": "science"`，compose 写进 `shots.json`，
   resolve 只在 `use.fits` 命中的纸里挑；命中为空则退回只按版式（不报错，但也不保证贴题）。
   可用值：`science` / `craft` / `eastern` / `concept` / `story`。
3. **角色 + 轮换**：`main` / `chapter` / `quiet`，同 `bgMode`（手作三族默认一章一张纸，
   flat / cel 逐镜换）。永不与上一镜同一张。

#### 为什么不用「按背景自动调色」

算过：卡片色 `#fbf6ea`（lum 0.96）对最暗的纸（`papercut/chapter` 0.66）明度比只有 **1.42**。
而 49 张纸的 `zone_mean_lum` 全部落在 0.66–0.97，**没有一张暗到需要浅墨**。
也就是说：卡片的可读性从来不是靠「换个更亮的色」解决的，靠的是**描边 + 阴影 + 纸条卡片**
（`paperCard` 的 1px 墨边 + 三层阴影）。硬做「背景→调色」只会把已经成立的视觉弄花。
真正的失配发生在**选错纸**，不在配色。

#### 换皮肤要三处一起改

```bash
python scripts/set-skin.py <工程> journal --rebuild
```

皮肤有两个来源：`src/theme/active.ts`（渲染端 import 它）与 `manifests/shots.json` 的 `theme`
（背景库按它挑图）。只改一处会渲出「A 皮肤的组件 + B 皮肤的纸」——**没有任何门禁看得见的坏组合**。
`set-skin.py` 一次写全三处（`active.ts` + `story.json` + `shots.json`），`--rebuild` 顺手重跑
compose + resolve。resolve 现在一律以 `active.ts` 为准，不同步时只提示、不阻断。
