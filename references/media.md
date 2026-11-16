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

> 落地件：`src/media.tsx`、`fxkit.tsx`、`kit.tsx`、`components/`。门禁：`scripts/validate-composition.py`（介质多样性 ≥3 种）。

- [1. 为什么要路由](#1-为什么要路由)
- [2. 路由表](#2-路由表)
- [3. A 场景 / B 场景](#3-a-场景--b-场景)
- [4. 背景契约](#4-背景契约必读)
- [5. 组件在哪个模块](#5-组件在哪个模块)
- [5.1 组件权威索引（53 件 · 选型只查这一处）](#51-组件权威索引53-件--选型只查这一处)
- [6. 接触表](#6-接触表)
- [7. 自检](#7-自检)
- [修辞动作 → 组件](#修辞动作--组件)

### 1. 为什么要路由

画面像 PPT，不是因为没用图片，而是**全片只有一种介质（卡片 + 文字）**；让片子不像 PPT 的是同一支片里出现不同的视觉介质。组件放在仓库里没人用，缺的是"什么内容该用哪个件"的决策入口——这一层就是那个入口。

### 2. 路由表

- **每行一个首选**，其余写明"何时才用"。
- **加组件 = 换掉一件**；总数上限见 [technique.md#dependency-policy](technique.md#dependency-policy) §8。
- 本表只管"这段内容配哪个件"；每件的用途、边界、接触表页、使用记录与实现注意只看 [§5.1](#51-组件权威索引53-件--选型只查这一处)。

| 内容类型 | 首选 → 条件分支（模块） |
|---|---|
| 数据 / 对比 / 趋势 / 分布 | **`Chart`**（components），按语义选 `variant`；真实数据直接喂 CSV（`csv="阶段,数量\n…"`，多序列 `csvToChartSeries()`，不手抄数组）。只有一个百分比 → `ProgressRing`（fxkit）；只有前后两值 → `MetricGrid`（media） |
| 软件流程 / 界面 | `ConsoleWindow`（media）或 `HighlightCode` 的窗口壳（components）；弹出来的框（确认框 / 下拉 / 气泡 / 提示）→ **`OverlayFrame`**（components） |
| 技术代码 | **`HighlightCode`**（components）；一个字一个字敲 → `Typewriter`；改了什么 → `DiffView`（均 fxkit） |
| 结构关系 | 两者有连线 / 路径 → **`PathDraw`**；无层级无方向的网 → `NetworkGraph`（均 components）；清单 → `Checklist`（toolkit）；只是逐行出现 → `StaggerList`（fxkit） |
| 分步展开 / 折叠 | **`Accordion`**（components） |
| 多方案 / 多标签切换 | **`Tabs`**（components） |
| 配置 / 选项 / 参数被改动 | **`ControlStack`**（components；帧→状态表 `steps: [{at, value}]`），别用文字卡假装"选项被打开了" |
| 技术栈 / 品牌标识 | **`IconWall`** / `TopicIcon`（components） |
| 抽象概念 | `StageFrame`（stagekit）+ SVG |
| 强调信息 | 一句话发光 → **`ShimmerText`**；整块卡动效边框 → **`GlowFrame`**（均 components）；逐字砸出 → `JumpInText`（toolkit）；盖章定论 → `StampSeal`（fxkit） |
| 几何 / 图形强调 | **`ShapeDraw` / `SHAPES`**（components）。份额 / 饼图别找图形件：有数据 `Chart variant="pie"`，只有一个百分比 `ProgressRing` |
| 指向 / 沿线运动 | **`PathDraw` 的 `showArrow`**（components） |
| 证据 / 细节 | `ZoomStage`（skeletons） |
| 指标结论 | 一个主角数字 → **`KineticNumber`**（cinema）；一排指标卡 → **`StatRow`**；全宽收束条 → **`VerdictBar`**（均 components）；前后值成对 → `MetricGrid`；吸底盖章 → `StampBanner`（media） |
| 对话 / 交互 / 提示词 | `ChatThread`（fxkit） |
| 层级 / 树状 | **`TreeView`**；占比 + 层级用面积表达 → `variant` = `treemap` / `pack` / `sunburst`（components） |
| 地理 / 全球视野 | **`GeoView`**（components） |
| 流量 / 转化去向 | **`SankeyChart`**（components） |
| 手绘强调 / 圈画 / 下划线 | **`SketchFx`**（components）+ `sketchCircleArea` / `sketchUnderline` / `sketchBox` |
| 数学 / 公式 | **`MathBlock`**（components） |
| 收尾引导 | **`QrCode`**（components） |
| 收束 / 漏斗 | `Funnel` / `ProgressRing`（fxkit） |
| 场景衔接 | **`SceneTransitions`**（components，20 种官方转场，不必手写）；手写 3 式：`shotkit` + `insert` |
| 快速运镜 / 冲刺 | 不提供运动模糊件（`@remotion/motion-blur` 已删；"速度峰值"不在七种合法运镜意图里）。用**帧内位移 + 速度线**表达，不要手绘模糊 |
| 让画面"活一点" | **`NoiseJitter`**（components） |
| 文字排版 / 卡片文字被裁 | **`FitTextBox` / `fitChineseTextOnNLines`**（components/fittext）；图元标签（treemap 格 / 气泡 / 扇区）用 **`fitNodeLabel`**：宽、高**都要**过，反推字号低于 13px（`MIN_LABEL_FONT`）就**不画字**、改进图例 |
| 逐条揭示 | **`ClipReveal`**（components）；镜头级揭示是 `RevealMask`（insert） |

**硬约束（门禁 P0）**：全片 ≥3 种不同介质；**每个讲解场景 ≥1 个活性组件**（随旁白变化状态的演示件）；禁止"一盒子弹"式纯卡片堆。

### 3. A 场景 / B 场景

- **A = 主线演化轨**：一个主体常驻，随旁白换内部状态（`StageFrame`），**不是卡片轮播**。
- **B = 辅助取证轨**：换一种**视觉介质**插入 0.8–2 秒（24–60 帧），说完即回。B 是 A 的一次注意力转移，不是另一个场景：不留残片、不另起场景。
- 实现：`skeletons.ZoomStage`（整体→聚焦→标注→回整体；B 段由场景在区间外返回 `null`，物理上保证无残片）。
- B 结束时必须回到 A 的**同一状态**，观众不丢上下文。

### 4. 背景契约（**必读**）

#### 4.1 背景锁定，不换

`flat` / `cel` 用固定 16:9 背景位图，四边与四角有高对比装饰（cel：左下爆炸贴、右下速度线；flat：右下卡通角色）。**不替换、不重绘。** 内容压到装饰区上会被吃字，所以：

> **内容压在装饰区之上时，必须坐在 `CoverPanel` 上**（`BackgroundMute` 已删除）。

#### 4.2 机制与 z 序

主题用 `theme.backgroundDecorZones` 声明装饰区矩形（1920×1080 设计坐标，取三张背景变体 main / chapter / quiet 的并集；`cel` 6 个、`flat` 4 个）。

```tsx
// tone='paper' 走卡片皮肤；tone='wash' 只铺柔和底色
<CoverPanel x={200} y={640} w={1000} h={220} tone="paper">
  <YourContent />
</CoverPanel>
```

- **没有成片级整幅底托**：三张变体中央约 70% 是安全区；整幅半透明 wash 会把四角吉祥物洗成"幽灵"（`Shot` 外壳已删掉它）。内容真压到装饰区时，只给**那一块**垫 `tone='paper'`。
- **z 序**：底托在背景之上、内容之下。`tone='wash'` 必须用**负 z**（`z={-1}`）；**不要用正 z**——正 `z-index` 会压过场景里大多数 `z-index: auto` 的构件（`z=5` 时整镜内容只剩约 15% 不透明）。`tone='paper'` 用默认 `z={42}`（它是内容的父节点，不冲突）。
- wash **不铺满整幅**。

#### 4.2.1 wash 要羽化，不能是硬边矩形

硬边会在下沿留一条可见接缝（横切过装饰）。用径向渐变把四边柔化进背景，并**去掉 1px 描边环**（`boxShadow: 'none'`，否则出现贴着内容的方框）：

```tsx
<CoverPanel x={70} y={92} w={1780} h={846} tone="wash" z={-1} pad={0}
  style={{boxShadow: 'none', borderRadius: 0,
    background: `radial-gradient(125% 118% at 50% 50%, ${C.paperBase}F5 58%, ${C.paperBase}D6 82%, ${C.paperBase}00 100%)`}} />
```

#### 4.3 门禁

`validate-shot-motion.py`（P1）：某镜 `contentBand` 与装饰区相交却未声明 `cover` → 报"文字可能被装饰吃掉"，成片前人工确认。

#### 4.4 面板要填满

空的白面板像刺眼的白盒子，满的像纸（像素没变，感受来自空白）：

- 内容按可用高度排布（`StageFrame` main 区高 = `h − pad×2 − headH − stampH`），别在 520px 高的框里只放 196px 内容；
- 拿不准就**居中**内容或缩小框高，不要让下方留大半空白；
- **不要**用降低不透明度"救"空面板（只会更难读）。

#### 4.5 有意覆盖要显式声明（门禁白名单）

`OverlapGate`（渲染期）报告所有文字重叠与遮挡；**有意**的重叠必须标注，否则按缺陷处理：

| 场景 | 标注 |
|---|---|
| 镜头边界的交接叠帧 | `data-gate-allow="handoff"` |
| 头部 / 标题的滑变双层 | `data-gate-allow="swap"` |
| 指标新旧数值的替换 | `data-gate-allow="value-swap"` |
| 整块跳过 | `data-gate-skip` |

白名单只用于"同一信息在同一位置替换"和"镜头交接"；**不许**用它掩盖两个不同信息互相压字。

### 5. 组件在哪个模块

| 模块 | 内容 | 帧参数 |
|---|---|---|
| `src/kit.tsx` | `PillTag` `LineIcon`（26 字形）`CheckBadge` `TYPE`：主题无关原子，工程侧可引用 | — |
| **`src/components/`** | 新封装层，唯一入口 `./components`，27 件全是本层实现（无库再导出）；另有 `SHAPES` / `PRESENTATIONS` / `fitChineseTextOnNLines` 等工具。颜色只读 `THEME`，见 [technique.md#dependency-policy](technique.md#dependency-policy) §7 | `f` |
| `src/fxkit.tsx` | 9 件：`FitCard` `Typewriter` `StampSeal` `Funnel` `ChatThread` `ProgressRing` `StaggerList` `DiffView` `SkeletonCard` | **`frame`** |
| `src/toolkit.tsx` | 修辞工具件 `Callout` `Checklist` `JumpInText` | **`frame`** |
| `src/media.tsx` | `ConsoleWindow` `MetricGrid` `StampBanner` | `f` |
| `src/stagekit.tsx` | `StageFrame` `PhaseRail` `useStageMachine`（Attach 已删） | `f` |
| `src/skeletons.tsx` | `Corridor` `SplitStage` `ZoomStage` | `f` |
| `src/insert.tsx` | `RevealMask` `useHandoff` `TRANSITIONS` | `f` |
| `src/shotkit.tsx` | `ShotCamera` `CoverPanel` `safeCheck` | `f` |
| `src/index.tsx` | 引擎层，**对场景不导出任何组件**：只有 16:9 一个 Composition `NotebookVideoFilm`（`Film4x3` / `Film3x4` 已删）；`Paper` / `Subtitle` / `Chrome` 是模块私有 `const`，场景 import 不到；曾在本文件内的 6 件零渲染"反 PPT 交互件"已删（见 [checks.md#quality-checklist](checks.md#quality-checklist)） | — |

> **⚠️ 帧参数名**：`fxkit` 与 `toolkit` 传 `frame={f}`，其余传 `f={f}`。帧参数是必填类型，传错名或漏传 `tsc` 报错；写错会让动画时间轴整体错位。

> **⚠️ 布局陷阱**：同一容器里**不要混用文档流标题和绝对定位组件**——绝对定位的 `x/y` 相对容器原点，会与占着顶部的标题精确重叠成一团乱字。二选一：给组件显式 `y` 排到标题下方，或把标题也改成绝对定位。

### 5.1 组件权威索引（53 件 · 选型只查这一处）

**全技能唯一一份组件清单。** [components.md#fxkit](components.md#fxkit) 只留 fxkit 参数与动效细节；`showcase.tsx` 只留接触表版面与 `SHOWCASE_VERSION`（给人读的串，不在画面上渲染）；源码注释只解释实现。件数、用途、何时用 / 别用、接触表页号、使用记录**以本表为准**；改组件先改这里，别处不另起清单。

**口径**：各模块对外 `export` 的 React 组件 = `src/components/` 27 件 + 其余 8 个模块 26 件（`kit` 3 / `fxkit` 9 / `media` 3 / `stagekit` 2 / `skeletons` 3 / `insert` 1 / `shotkit` 2 / `toolkit` 3）= **53**。不算件：渲染期门禁（`SlotGuard` 与四道 `*Gate`）、主题包件（`Paper` / `Background` / `Grade` / `SubtitleChrome`、cel 的 `Burst`）、大写常量与 type-only 导出。复核：对上述 9 个模块抽 `^export const X: React.FC` 去重计数，并与 `src/components/index.ts` 导出名单对齐，剔除 `SlotGuard` 与 Gate 后必须是 27 + 26；不是就说明有件加了没登记。

- **接触表** = `showcase.tsx` 里真实渲染过的页号（多页全列；"未展示" = 接触表上看不见）。
- **使用记录** = 参考片 `src/scenes.tsx`（`S1`–`S8`）或引擎 `index.tsx` 里真实出现的位置；"未使用" = 这些位置找不到，**不等于从没渲染过**（真实工程用到的写在格里）。

| 组件 | 用途 | 何时用 | 何时别用 / 注意 | 接触表 | 使用记录 |
|---|---|---|---|---|---|
| `Accordion`（components） | 手风琴，展开项随帧累积 | 并列要点逐项展开 / 收起，一屏放不下 | 只是逐行出现 → `StaggerList`；控件被改 → `ControlStack` | ⑦⑨ | 未使用 |
| `Tabs`（components） | 标签页，激活项由帧号决定 | 2–4 个对等方案切换，且切换本身是讲解内容 | "被改动"而非"切换" → `ControlStack` | ④⑨ | 未使用 |
| `ControlStack`（components） | 六种受控控件（开关 / 复选 / 单选 / 分段 / 滑块 / 进度，纯 div），`steps:[{at,value}]` 帧→状态，纯函数可复算 | 讲某个设置被改了：旁白说到哪、控件变到哪 | 一行一个控件，别把 6 种塞进一镜；控件不是主角时别用（抢戏） | ⑫ | 未使用 |
| `OverlayFrame`（components） | 拟真弹层 dialog / menu / popover / tooltip（纯 div，Portal 指到画面根） | 讲"弹出来一个框" | 一次别冒三个；压在装饰区同样要坐 `CoverPanel` | ⑰ | 未使用 |
| `NetworkGraph`（components） | d3-force 关系网（固定迭代 + 显式初值） | 谁连着谁：无层级、无方向 | 有层级用 `TreeView`；反过来别用树画网（凭空造出上下级） | ⑯ | 未使用 |
| `HighlightCode`（components） | 语法高亮 + 行号 + 逐行聚焦，带窗口壳 | 页面形态的代码；"这是官方 / 真实代码" | 终端 → `ConsoleWindow`；逐字敲 → `Typewriter`；纯代码路线不做实拍框 | ⑨ | 未使用 |
| `MathBlock`（components） | katex 公式块（静态、确定性） | 有公式 / 推导 | 无动画，别当装饰塞公式 | ⑭ | 未使用 |
| `TopicIcon`（components） | 单个题材图标（simple-icons 品牌 + lucide-react 线条，笔画对齐 `LineIcon`） | 技术栈 / 品牌的单点 | 成排 → `IconWall`；与内容无关时别用 | ⑫ | 未使用 |
| `IconWall`（components） | 图标墙（弹簧错峰入场） | 技术栈 / 依赖清单具象成一堵墙 | 图标不是内容时别用 | ⑩ | 未使用 |
| `Chart`（components） | d3 算刻度与路径；`variant`：line（默认）/ area / stack / stackExpand（百分比堆叠）/ stream / radar / pie（扇区百分比 + 图例）；可喂 CSV（d3-dsv） | 数据 / 趋势 / 分布 / 多值对比；真实数据进图 | 一个百分比 → `ProgressRing`；前后两值 → `MetricGrid`；柱状用默认 line + `series` 驱动；未知 `variant` 直接抛错 | ①⑨⑭⑮ | 未使用 |
| `StatRow`（components） | 一行指标卡，数字随帧滚动（字符串值直显） | 报一个大数字；等权指标并排；对比两方不等权时 | 数值已在 `MetricGrid` 里滚动时别重复 | 未展示 | 参考片 S1 |
| `KineticNumber`（cinema，引擎运动件，**不计入 53 件**） | 关键数字动态排版：计数 + 落定弹出 + 下划线扫入，字号 170–380 | 一镜的主角就是一个数（耗时、倍数、降幅），讲到它的那一拍 | 一镜并排 ≥3 个数（用 `StatRow` / `MetricGrid`）；全片超过 35% 的镜都用它 | 未展示 | 演示片 S1 / S4 / S7 / S8 |
| `TreeView`（components） | 目录树 / 组织图 + treemap / pack / sunburst（d3-hierarchy，面积 = 数值） | 有层级；或占比 + 层级 | 无层级的网 → `NetworkGraph` | ⑬⑯ | 未使用 |
| `GeoView`（components） | 真陆地轮廓（d3-geo + world-atlas `land-110m`，55 KB 进 bundle），可叠经纬度标记点；`projection="flat"`（naturalEarth1）看全局，默认正交投影可 `spin` 自转 | 地理 / 全球视野；节点 / 站点分布 | **不含国界与地名**：要国界得换 `countries-110m.json` 并另立一件，别扩 `GeoView` 语义；同一组对比之外别混用两种投影 | ⑬ | 未使用（⑬ 已渲真地图 + 4 个标记点） |
| `SankeyChart`（components） | 流量图（d3-sankey） | 流量在环节之间怎么分流 | 逐级递减的漏斗 → `Funnel` | ⑬ | 未使用 |
| `QrCode`（components） | 二维码（纯计算、不联网） | 收尾引导"扫码看仓库" | 中途别放（观众不会暂停扫码） | ⑬ | 未使用 |
| `SketchFx`（components） | 手绘风图形（roughjs，seed 固定 → 每次同一笔迹）；`fillStyle` 6 种确定性值：hachure（手账风招牌）/ solid / zigzag / cross-hatch / dashed / zigzag-line | 手绘强调：圈画 / 下划线 / 方框 | 要精确几何 → `ShapeDraw`；`'dots'` 已移除（内部调 `Math.random()`，同帧两次不一致） | ⑭ | 未使用 |
| `FocusFx`（components） | 一镜一次的注意力动作（dim / spot / loupe / marker） | 把注意力压到一块矩形区域 | 一镜一次；画面已有高亮或缩放时别叠 | ⑱（整页专属，四态按帧轮转） | 参考片没用；真实工程 `overview-film` S8 渲过 |
| `GlowFrame`（components） | 流光边框（conic-gradient 绑帧号） | 强调一瞬（警告感） | 与 `ShimmerText` 二选一；要"真的变了状态"→ `ControlStack` | ⑧⑩ | 未使用 |
| `ShimmerText`（components） | 文字闪过一道光 | 只强调一句话；念口号 | 与 `GlowFrame` 二选一；讲解中段用显浮夸 | ⑧ | 未使用 |
| `ClipReveal`（components） | 遮罩擦除（clip-path 按帧推进） | 逐条揭示（不只是淡入） | 镜头级交接 → `RevealMask` | ⑫ | 未使用 |
| `NoiseJitter`（components） | 有机抖动（noise2D，同种子同结果） | 让静止物活一点（手绘 / 贴纸感） | 别给文字用（伤可读性） | ⑫ | 未使用 |
| `VerdictBar`（components） | 全宽结论条（填满底部） | 收束场景且底部要填满 | 一镜一条；别与 `StampBanner` 同时砸（互压底线） | 未展示 | 参考片 S8 |
| `PathDraw`（components） | 描线生长 + 沿线运动的点 / 沿线转向的箭头（`showArrow`，`getTangentAtLength`，不用自己差分算切线） | 两者关系 / 因果；箭头沿路线跑；流程备选 | 路径短于 200px 时箭头盖住整条线；已有导轨 / 时间轴别叠；关系是网 → `NetworkGraph` | ⑪⑰ | 未使用 |
| `MorphShape`（components） | 形状连续变形（flubber；`engine="remotion"` 用 `interpolatePath`） | 同一个东西形态变了 | 没有变形语义别用 | ⑪ | 未使用 |
| `ShapeDraw` / `SHAPES`（components） | 参数化几何（@remotion/shapes）：星 / 六边形 / 三角 / 圆 / 星芒 / callout 标注框 / arrow / heart / 椭圆 / 矩形 | 要标注框 / 箭头 / 星标，不想手写 path | 图标 → `TopicIcon`；形状要有语义，别撒装饰；份额别用它 | ⑩⑰ | 未使用 |
| `SceneTransitions`（components） | 官方 20 种转场全部登记，名 = 官方包名去连字符（= `PRESENTATIONS` 的键）。几何式 9：`fade` `slide` `wipe` `flip` `clockWipe` `iris` `bookFlip` `pushCut` `none`；着色器式 11：`blurSlide` `crossZoom` `crosswarp` `dissolve` `dreamyZoom` `filmBurn` `linearBlur` `ripple` `swap` `zoomBlur` `zoomInOut`（分组同 `pathfx.tsx`）。本机无头渲染全部可用；`@remotion/transitions` 无 `Math.random`，全部帧驱动 | 场景衔接要真的换场 | `flip` 在 50% 处正好侧对镜头（看着空属正常，看效果截 25% / 75%）；`none` 是硬切 | ⑪ | 未使用 |
| `FitTextBox`（components） | 中文反推字号 + 断行（自带字体就绪门） | 固定宽 + 行数上限定字号（治卡片文字被裁） | 管卡片多高用 `FitCard` / `fitH()`（分工见 [components.md#fxkit](components.md#fxkit)） | ③⑩⑭ | 未使用 |
| `PillTag`（kit） | 胶囊贴标 | 页眉 kicker、标签行 | 别当正文 | 未展示 | 参考片 S1 S3 + 引擎页眉 |
| `LineIcon`（kit） | 26 字形线条图标（lucide-react） | 卡片小标题旁 | 大图 / 插图 → `TopicIcon` | 未展示 | 参考片 S3 S7（`CardHead`） |
| `CheckBadge`（kit） | 对勾圆徽章 | "已完成"状态 | 要盖章体量 → `StampSeal` | 未展示 | 参考片 S4 S7 |
| `FitCard`（fxkit） | 防出格卡片（`h` 必须经 `fitH()` 算） | 任何文字卡片 | 禁止手写"看着差不多"的固定高度 | ③ | 参考片 S3 S4 |
| `Typewriter`（fxkit） | 打字机（标点分级停顿、块光标） | 一个字一个字敲出来；正在写 | 改了什么 → `DiffView`；整段代码 → `HighlightCode` | ② | 参考片 S3 |
| `StampSeal`（fxkit） | 印章砸下（2.6x→1 回弹，-8°） | 盖章定论 / 认证 | 字数 >4 溢出圆 | ③ | 参考片 S2 S6 |
| `Funnel`（fxkit） | 尝试漏斗（宽进窄出 + 计数 + 滴落点） | 逐级递减 / 收束 | 只有一个百分比 → `ProgressRing` | ③ | 参考片 S5 |
| `ChatThread`（fxkit） | 对话气泡（typing 三点 → pop，左右交替） | 模拟 AI 对话 / Prompt 交互（多方案对比时备选 `Tabs`） | 2–3 条（1 问 + 1~2 答），否则溢出窗口高度 | ④ | 参考片 S7 |
| `ProgressRing`（fxkit） | 进度环（dashoffset + 中央标签） | **只有一个**百分比 | 多份额 → `Chart`；有前后值 → `MetricGrid` | ① | 参考片 S5 |
| `DiffView`（fxkit） | 补丁 diff（红删绿加逐行滑入；`before`/`after` 由 jsdiff 算行） | 讲改了什么 | 无增无删时别用 | ② | 参考片 S3 |
| `SkeletonCard`（fxkit） | 骨架 → 内容（等待 beats 先占位） | 已知要等（拉取 / 计算有过程） | 内容本该立刻出现时别用 | ③ | 参考片 S7 |
| `StaggerList`（fxkit） | 级联列表（逐行滑入 + 微旋转） | 只是逐行出现，防 bullets 堆砌 | 相邻开始至少 12 帧（`stagger` 取 12，见 [draftpaper.md#reveal-rules](draftpaper.md#reveal-rules)）；要完成态 → `Checklist` | ① | 参考片 S4 |
| `ConsoleWindow`（media） | 控制台 / 终端窗口（整块界面） | 正在跑、命令行；终端形态 | 必须给 `h`，否则高度由内容撑；带行号高亮的代码 → `HighlightCode` | ② | 参考片 S1 |
| `MetricGrid`（media） | 指标网格（before→after 替换，数字滚动） | 前后值成对 | 只有一个值 → `StatRow` | ② | 参考片 S8 |
| `StampBanner`（media） | 结论吸底条（三段式落定 + 底色闪） | 砸一句结论、吸底；口号备选 | 一镜别砸两条（互压底线） | 未展示 | 参考片 S1 S5 S8 |
| `StageFrame`（stagekit） | 活体主体框（header / main / rail / stamp） | 一个主体持续演化（≥5 拍） | 只有 2–3 拍别用（状态机撑不起来），备选 `Corridor` | 未展示 | 参考片 S1 S5 S8 |
| `PhaseRail`（stagekit） | 状态进度轨（状态机显式画出来） | 让观众看见推进到第几步 | 静态内容别用 | ④ | 参考片 S1 S5 |
| `Corridor`（skeletons） | 走廊 / 流程骨架（到站 + 停留 + 对勾描线，隐含顺序） | 演示一段流程；因果的备选 | 站点 <3 个改用 `StaggerList` | ⑥ | 参考片 S2 S6 |
| `SplitStage`（skeletons） | 双栏对比（先暗输方，再亮赢方） | 两个对等对象对比 | 两方不是同一维度别用 | ⑥ | 参考片 S4 |
| `ZoomStage`（skeletons） | 整体→聚焦→标注→回整体（B 段插入） | 放大看局部（0.8–2s 取证）；圈住一处的备选 | 会缩放，静止元素别用 | ⑥ | 参考片 S3 S7 |
| `RevealMask`（insert） | 镜头级遮罩揭示（ltr / rtl / ttb） | 镜头进场要"揭开" | 逐条揭示 → `ClipReveal` | 未展示 | 参考片 `Shot` 外壳（只有 S3 / S7 传了 `reveal`） |
| `ShotCamera`（shotkit） | 受限相机外壳（只做 transform / opacity） | 每一镜都要 | 页眉 / 章节卡 / 字幕放在它**之外**（否则被运镜带动） | 未展示 | 参考片 8 镜 |
| `CoverPanel`（shotkit） | 局部底托 / 卡片底 | 内容压到背景装饰区时 | 规则见 §4.2：wash 负 z、羽化、不铺整幅 | 未展示 | 参考片 8 镜 |
| `Callout`（toolkit） | 圈住一处 + 引线 + 手写标注 | 圈住 / 指出一处 | 画面已有高亮别叠（重复编码） | ⑦ | 参考片 S1 |
| `Checklist`（toolkit） | 带完成态的清单（`done` 后序号变对勾） | 列清单、要完成态 | 项 >6 溢出；只是逐行出现 → `StaggerList` | ⑦ | 参考片 S3 |
| `JumpInText`（toolkit） | 逐字跳入（字色激活） | 念一句口号（钩子与收尾） | 全片最多 1–2 处；讲解中段显浮夸 | ⑧ | 引擎章节条（`index.tsx`） |

**两处缺口（如实标出；处置见 [technique.md#dependency-policy](technique.md#dependency-policy) §8）**

- **未上接触表 10 件**：旧模块 8 件（`PillTag` `LineIcon` `CheckBadge` `StampBanner` `StageFrame` `RevealMask` `ShotCamera` `CoverPanel`）**不该进**（原子 / 引擎外壳 / 参考片里天天出现，格子留给没画面的件）；封装层 2 件 `StatRow` `VerdictBar` **该进而没进**（已在参考片 S1 / S8 出现）。
- `FocusFx` 覆盖层挂 `SCENE_ANCHOR`（`position: fixed` + 场景坐标 + zIndex 160），塞进 900×470 的格子会被舞台 transform 变成包含块、把"压暗整页"演残，所以它占第 ⑱ 整页，每 8 帧轮转一态。接触表 JPG 只抽到 **dim / loupe 两态**，spot / marker 以 showcase 成片 mp4 为准，别拿 JPG 当"四态都见过"。
- 已删：PieDraw（被 `Chart variant="pie"` 与 `ProgressRing` 夹住，自身无标签无数值）、CameraMotionBlur / Trail（零渲染，按"零引用"判据删）；第 ⑪ 页空出的格换成 pathfx 组合用法（标注框 + 引线）。
- **未使用 25 件**（口径 = 参考片 `scenes.tsx` + 引擎 `index.tsx`）全部在新封装层，且**全部在接触表上看得见**；旧模块 26 件全部在参考片里用过。`FocusFx` 有真实工程渲染记录（`overview-film` 的 `src/scenes.tsx` L8 import、L274 `<FocusFx f={f} mode="dim" …/>`，`shots.ts` S8 `live` / `evidence` 点名）。这是新旧并存的过渡态，不算缺陷：新件替旧件要动参考片 `scenes.tsx`，单独一轮做。

### 6. 接触表

件数与页号只查 [§5.1](#51-组件权威索引53-件--选型只查这一处)；本节只讲机制。**为什么要它**：读 props 很难想象构件长什么样，让执行 AI **看图选型**比读文字准——这是"能力存在但不可达"的解法。

`src/showcase.tsx` 注册 `NotebookVideoShowcase`：**18 页 × 1 秒**，1920×1080 原生，渲染：

- 旧层 **18 件**（按 `showcase.tsx` 里真实出现的 JSX 标签数：`fxkit` 9 + `media` 2 + `stagekit` 1（`PhaseRail`）+ `skeletons` 3 + `toolkit` 3）。别与"旧模块对外 export 26 件"混用：差的 8 件是接触表没逐件渲染的；`SHOWCASE_VERSION` 与本节都按"实际渲染"口径。
- 第 ⑤ 页 6 种运镜意图；第 ⑥ 页四种骨架（`StageFrame` 只在标题点名、未渲染）。
- 新封装层第 ⑨–⑱ 页共 25 件（⑨–⑰ 24 件 + ⑱ `FocusFx` 整页）+ 新能力 3 页（图表变体 / 层级与关系 / 弹层与形状）。
- 没覆盖的 10 件见 §5.1「两处缺口」。

```text
node scripts/notebook-video.mjs showcase PROJECT_DIR          # 接触表 mp4（交付规格：2560×1440 / 静音 AAC / 色彩四项回写）
node scripts/notebook-video.mjs showcase PROJECT_DIR --sheet   # 只要 jpg（select 按帧号取每页第 6 / 21 帧，6×6 共 36 格）
```

- mp4 是**交付物**：按 4/3 放大到 2560×1440、补静音 AAC、回写色彩四项；别按默认参数渲（出的是 1920×1080 / 无音轨 / 无色彩标记的调试版，会静默替换交付文件）。
- 第 ⑪ 页 `SceneTransitions` 必须**页内放得下**：`durations=[12,12,12,12] transitionDuration={6}` → 总长 `4×12 − 3×6 = 30` 帧，三个转场落在第 6–12 / 12–18 / 18–24 帧（总长超过 30 帧的转场在 mp4 里也看不见）。
- `--sheet` 用 `-vf "select='eq(mod(n,30),6)+eq(mod(n,30),21)',scale=640:-1,tile=6x6"` 按帧号精确取帧（每页 2 张中段图，36 帧 = 18 页铺满 6×6；第 ⑪ 页第 21 帧正好是第 3 个转场 50% 处）。**别改回** `fps=1`（只抽到每页第 0 帧，转场前）或 `-ss 0.2 + fps=2`（seek 与 fps 取整叠加，落点偏到第 12 / 27 帧）。
- 看 `flip` 一类转场按 §5.1 截 25% / 75%；默认串是 `wipe`，抽帧位不需要为它特殊照顾。

### 7. 自检

- [ ] 全片 ≥3 种介质，且每个讲解场景 ≥1 个活性组件；
- [ ] 每段内容都问过"该用什么**介质**"，而不是"用哪张卡片"；
- [ ] 压到背景装饰区的内容都坐在 `CoverPanel` 上；
- [ ] 用到的构件都能在 §5.1 指到；新构件同时登记进索引（引擎外壳 / 原子件不需要进接触表，见 §5.1「两处缺口」）；
- [ ] wash 底板的 z 没设到内容之上。

---

### 修辞动作 → 组件

§2 路由的是**内容类型**；这张路由**你此刻要做的修辞动作**。写场景前先查一遍：**`live` 里写的每个名字，都应能在这张表（或 [components.md#fxkit](components.md#fxkit) 的组件表）里指到。** 首选与备选的"何时别用"都在 §5.1 该件那一行。

| 修辞动作 | 首选 | 备选（何时才用） |
|---|---|---|
| 圈住 / 指出一处 | `Callout`（toolkit） | `ZoomStage`（要放大才能看清时） |
| 表现两者关系 / 因果 | `PathDraw`（components） | `Corridor`（隐含顺序时）；关系是"网"不是"链" → `NetworkGraph` |
| "谁连着谁"（无层级、无方向） | `NetworkGraph`（components） | `TreeView`（确有层级时） |
| "某个设置被改了" | `ControlStack`（components） | `Accordion` / `Tabs`（是展开 / 切换，不是被改动时） |
| "弹出来一个框" | `OverlayFrame`（components） | `ConsoleWindow`（整块界面时） |
| 箭头沿路线跑过去 | `PathDraw` 的 `showArrow` | `MorphShape`（讲形状变形时） |
| 强调一瞬（警告感） | `GlowFrame` | `ShimmerText`（只强调一句话时）；二选一不叠 |
| 砸一句结论 | `StampBanner` | — |
| 认证 / 盖章 | `StampSeal` | — |
| 念一句口号 | `JumpInText` / `ShimmerText` | `StampBanner` |
| 报一个大数字 | `StatRow` | `MetricGrid`（有前后值时） |
| 对比两方（对等） | `SplitStage` | `StatRow`（不等权时） |
| 列一份清单 | `Checklist` | `StaggerList`（不要完成态时） |
| 演示一段流程 | `Corridor` | `PathDraw` |
| 一个主体持续演化 | `StageFrame`（≥5 拍） | `Corridor` |
| 证明"这是官方 / 真实" | `HighlightCode` 的窗口壳 | —（能用代码画清的别用实拍；需要实拍时用用户提供 / Commons / 授权图片，技能不调用生图模型） |
| 表现"正在跑 / 正在写" | `ConsoleWindow` / `HighlightCode` | `Typewriter` |
| 模拟 AI 对话 / Prompt 交互 | `ChatThread` | `Tabs`（多方案对比时） |
| 页面形态 | `HighlightCode` 的窗口壳 | `ConsoleWindow`（终端形态） |

**两条纪律**：① 加组件 = **换掉**画面里的一个元素，不是往里加；② 组件只有落在它擅长的修辞动作上才算数——找不到对应动作就别加（为凑多样性堆组件正是这张表要防的）。

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
