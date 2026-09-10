# 内容 → 视觉介质 路由

> 状态：**v2.10 生效**。落地件：`assets/lecture-template/src/media.tsx`、`fxkit.tsx`、`kit.tsx`。
> 门禁：`scripts/validate-composition.py`（介质多样性 ≥3 种）。

## 目录

- [1. 要解决的问题](#1-要解决的问题)
- [2. 路由表](#2-路由表)
- [3. A 场景 / B 场景](#3-a-场景--b-场景a-roll--b-roll-的本土化)
- [4. 背景契约](#4-背景契约必读)
- [5. 组件在哪个模块](#5-组件在哪个模块可达性)
- [6. 让组件"看得见"：接触表](#6-让组件看得见接触表)
- [7. 自检](#7-自检)

## 1. 要解决的问题

v2.8 的四个场景之所以像 PPT，**不是因为没用图片，而是因为全是同一种介质：卡片 + 文字**。

反过来，真正让视频不像 PPT 的，是**同一支片子里出现了不同的视觉介质**。
这一层解决的就是"这段内容该用什么形式表达"。

同时它也是"给一堆组件让 AI 拼积木"这条路的修复：那种做法失败的原因不是组件不好，
而是**缺"什么时候该用哪个"的决策入口**——组件在仓库里吃灰（实测 34 个库里 32 个引用数为 0）。

## 2. 路由表

| 内容类型 | 视觉介质 | 组件（模块） |
|---|---|---|
| 数据 / 对比 | 图表 | `CompareBars` `ProgressRing`（fxkit）、`MetricGrid`（media）、`Gauge`（场景层） |
| 软件流程 / 界面 | 窗口壳 + 内部线框 | `ConsoleWindow`（media）、`BrowserChrome`（engine） |
| 技术代码 | 终端窗 / 补丁 | `Typewriter` `DiffView` `SkeletonCard`（fxkit）、`CodeBlock`（engine） |
| 结构关系 | 连线 / 清单 / 轨道 | `Connector` `Checklist` `StepRail`（engine）、`StaggerList` `TimeRail`（fxkit） |
| 抽象概念 | 概念图 + 主体 | `StageFrame`（stagekit）+ SVG + `Mascot` |
| 强调信息 | 大字 / 逐字涌现 | `JumpInText` `WaveText`（engine）、`Typewriter` `StampSeal` `BurstCallout`（fxkit） |
| 证据 / 细节 | 纯代码局部放大 | `ZoomStage`（skeletons）、`EvidenceZoom` `EvidenceBridge`（fxkit / v2.9 回收） |
| 指标结论 | 指标网格 + 吸底条 | `MetricGrid` `StampBanner`（media） |
| 对话 / 通知 | 气泡 / 通知卡 | `ChatThread` `MailScan` `PayPop`（fxkit） |
| 收束 / 漏斗 | 漏斗 / 进度 | `Funnel` `ProgressRing`（fxkit） |
| 场景衔接 | 运镜 + 转场 | `shotkit` + `insert`（5 式转场） |

**硬约束（门禁 P0）**：全片 ≥3 种不同介质；**每个讲解场景 ≥1 个活性组件**（会随旁白变化状态的演示件），
"一盒子弹"式纯卡片堆禁止。

## 3. A 场景 / B 场景（A-roll / B-roll 的本土化）

参考项目用 A/B 双轨解决"碎片感 vs 呆板感"的两难。讲解片里不需要实拍剪辑意义上的双轨，只需要：

- **A 场景 = 主线演化轨**：一个主体常驻，随旁白换内部状态（`StageFrame`）。
  **不是卡片轮播。**
- **B 场景 = 辅助取证轨**：换一种**视觉介质**插入 0.8–2 秒（24–60 帧），说完即回。
  **B 不是"另一个场景"，而是 A 的一次注意力转移**；不留残片、不另起场景。
- 实现：`insert.InsertShot`（区间外返回 `null`，物理上保证无残片）+ `skeletons.ZoomStage`
  （整体→聚焦→标注→回整体）。

**A↔B 的关系**：B 结束时必须回到 A 的同一状态，观众不丢上下文。

**注意**：v2.9 的 `recipes/EvidenceBridge.tsx` 就是这个思路的图片版实现，可回收使用。

## 4. 背景契约（**必读**）

### 4.1 背景图是锁定的、好看的，不换

四套皮肤里 `cel` 与 `flat` 用的是固定资产背景位图，**画幅级、高对比**的装饰（cel 的左下爆炸贴、
右下速度线；flat 的右下卡通角色）。它们很好看，**不要替换、不要重绘**。

但**内容压到装饰上时，文字会被吃掉**。所以契约是：

> **内容压在装饰区之上时，必须坐在 `CoverPanel` 上；需要成片级兜底时用 `BackgroundMute`。**

### 4.2 机制

主题通过 `theme.backgroundDecorZones` 声明装饰区矩形（1920×1080 设计坐标）：
`cel` 4 个、`flat` 2 个、`paper` / `sticker` 为空（本来就干净）。

```tsx
// 局部兜底：给这一块内容一个底托（tone='paper' 走卡片皮肤，tone='wash' 只铺柔和底色）
<CoverPanel x={200} y={640} w={1000} h={220} tone="paper">
  <YourContent />
</CoverPanel>

// 成片级兜底：在装饰区之上、内容之下铺羽化暖底（保留装饰形状可辨）
<BackgroundMute zones={[0, 1]} opacity={0.74} />
```

**z 序铁律（实测踩过，务必照做）**：`BackgroundMute` / `CoverPanel` 必须落在**背景之上、内容之下**。

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

### 4.4 面板要填满，不要留大片空白

用户会明确感到"白色面板比以前差"，而逐帧比对证明**像素没变**——变的感受来自**空白**：
满的面板像纸，空的面板像刺眼的白盒子。所以：

- 面板的内容带要按可用高度排布（本模板 `StageFrame` 的 main 区高度 = `h − pad×2 − headH − stampH`），
  不要在 520px 高的框里只放 196px 高的内容；
- 拿不准时**居中**内容，或缩小框高，而不是让下方留 58% 空白；
- **不要**用降低不透明度来"救"空白面板——那只会让文字更难读。

### 4.5 有意覆盖要显式声明（门禁白名单）

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

## 5. 组件在哪个模块（可达性）

| 模块 | 内容 | 约定 |
|---|---|---|
| `src/kit.tsx` | `PillTag` `LineIcon`(26 字形) `CheckBadge` `TYPE` | 主题无关原子，工程侧同样可引用 |
| `src/fxkit.tsx` | 18 个动效构件（表格 / 漏斗 / 对话 / 印章 / 时间轨 …） | **帧参数名是 `frame`** |
| `src/media.tsx` | `ConsoleWindow` `MetricGrid` `StampBanner` | **帧参数名是 `f`** |
| `src/stagekit.tsx` | `StageFrame` `PhaseRail` `Attach` `useStageMachine` | `f` |
| `src/skeletons.tsx` | `Corridor` `SplitStage` `ZoomStage` | `f` |
| `src/insert.tsx` | `InsertShot` `RevealMask` `PaperTurn` `WhipStreak` `HandoffCarrier` `useHandoff` | `f` |
| `src/shotkit.tsx` | `ShotCamera` `DepthLayers` `CoverPanel` `BackgroundMute` `safeCheck` | `f` |
| `src/index.tsx` | `Paper` `Subtitle` `Chrome` `JumpInText` `WaveText` `RollDigit` `CodeBlock` `BrowserChrome` `Connector` `Checklist` `CountUp` `ProgressBar` `Callout` `TransitionIn` + 6 个反 PPT 交互组件 | 引擎层 |

> **⚠️ 布局陷阱（实测踩过）**：同一容器里**不要混用"文档流内的标题"和"绝对定位组件"**。
> 绝对定位组件的 `x/y` 是相对容器原点的，而文档流内的标题也占着容器顶部——
> 两者会**精确重叠**（实测：走廊场景的"整个过程对你是透明的"和列表第一行叠成了一团乱字）。
> 修法二选一：给绝对定位组件显式 `y`（让它排在标题下方），或把标题也改成绝对定位。

> **⚠️ 帧参数名不一致是一个真实陷阱**：`fxkit` 用 `frame`，v2.10 新增模块用 `f`。
> 给 fxkit 组件传 `f={f}` 会被静默忽略，组件回落到 `useCurrentFrame()`（全局帧），
> 于是动画时间轴整体错位（实测踩过：`Frame NaN` 与"动画早播/晚播"）。
> **给 fxkit 传 `frame={f}`，给新模块传 `f={f}`。** 拿不准就查上表。

## 6. 让组件"看得见"：接触表

`src/showcase.tsx` 注册了一个 `NotebookVideoShowcase` Composition：
6 页 × 1 秒，1920×1080 原生，把 16 个构件 + 6 种镜头意图 + 4 种骨架全部渲染一遍。

```text
node scripts/notebook-video.mjs showcase PROJECT_DIR          # 渲染接触表 mp4
node scripts/notebook-video.mjs showcase-sheet PROJECT_DIR    # 再抽 1fps 接触表 jpg
```

**为什么需要它**：读 props 文档很难想象构件长什么样；让执行 AI **看图选型**，
比读文字描述准确得多。这是"能力存在但不可达"的直接解法。

## 7. 自检

- [ ] 全片 ≥3 种介质，且每个讲解场景 ≥1 个活性组件；
- [ ] 每一段内容都问过"这块内容该用什么**介质**"，而不是"用哪张卡片"；
- [ ] 压到背景装饰区的内容都坐在 `CoverPanel` 上；
- [ ] 用到的构件都在接触表里出现过（新构件要加进接触表）；
- [ ] 没有把 wash 底板的 z 设到内容之上。
