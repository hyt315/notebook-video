// ============================================================================
// components/index.ts — 封装组件层（唯一入口）
//
// 场景只从这里 import；不要直接 import 原始库。理由见
// references/dependency-policy.md §7：库是无样式的，直接引用会让每个场景
// 写出不同的边框/圆角/阴影，违反「不得发明 per-scene 样式」。
//
//   import {Accordion, Tabs, Chart, ControlStack, GlowFrame} from './components';
//
// 组件纪律（四条铁律，全部有门禁或契约兜底）：
//   1. 颜色/边框/圆角/阴影只从 THEME 取
//   2. 动画是 f(帧号) 的纯函数：禁 CSS transition / setTimeout / Math.random
//   3. 文字容器高度用 fitH() 或 fitTextOnNLines() 算出，禁止手写
//   4. 新组件必须登记进 references/media-routing.md 的两张路由表
//
// 增长纪律（见 references/dependency-policy.md §8）：
//   · 加一件 = 换掉一件。新效果优先做成既有组件的**参数或变体**，不要为新效果新开组件。
//   · 合规判据是**「零引用」而不是「总数」**——任何组件只要从未出现在任何画面里
//     （参考片或接触表），就是待删除项。**不要对着一个数字做有损合并**：
//     引擎/结构件（STRUCTURAL）14 件砍不动，表意件逐对核对后真正重复的只有 4–5 对；
//     逐件点算的地板是 55 件（src/components/ 29 + 六个旧模块 26）。
//
// 本版（v3.1）新增/变更：
//   · 新增 `ControlStack`（Radix 六个纯受控控件）—— 换掉 `TiltCard`
//   · 新增 `OverlayFrame`（Radix 四个弹层，container 指到画面根）
//   · 新增 `NetworkGraph`（d3-force 关系网）
//   · `Chart` 加 variant：area / stack / stackExpand / stream / radar / pie
//   · `TreeView` 加 variant：treemap / pack / sunburst
//   · `SHAPES` 补 callout / arrow / heart / ellipse / rect；`PathDraw` 补沿线朝向箭头
//   · `TopicIcon` 放开 `lu`（Lucide）族，并把笔画重量对齐 `LineIcon`
// ============================================================================

// ---- 界面结构件（库提供结构，本层提供皮肤与帧驱动）----
export {Accordion, Tabs, ControlStack, controlStateAt, HighlightCode, MathBlock, TopicIcon, IconWall, TOPIC_ICONS, TOPIC_ICON_TONE, prog} from './ui';
export type {AccordionItem, TabItem, TopicIconName, ControlRow, ControlStep} from './ui';

// ---- 拟真弹层（Radix dialog / popover / tooltip / dropdown-menu）----
export {OverlayFrame, overlayStateAt} from './overlay';
export type {OverlayKind} from './overlay';

// ---- 关系网络（d3-force：谁连着谁，没有层级也没有方向）----
export {NetworkGraph, layoutNetwork} from './network';
export type {NetworkNode, NetworkLink} from './network';

// ---- 图表（d3-scale / d3-shape / d3-dsv 只算，画还是我们画）----
export {Chart, StatRow, csvToChartData, csvToChartSeries, CHART_BOX} from './chart';
export type {ChartDatum, ChartSeries, ChartVariant} from './chart';

// ---- 结构化数据 → 图形（d3-hierarchy / d3-geo / d3-sankey / qrcode）----
export {TreeView, GeoView, SankeyChart, QrCode, fitNodeLabel, fitOneLine, MIN_LABEL_FONT} from './data';
export type {TreeNode, TreeVariant, SankeyNodeIn, SankeyLinkIn} from './data';

// ---- 手绘风（roughjs）----
export {SketchFx, sketchCircleArea, sketchUnderline, sketchBox} from './sketch';
export type {SketchPrim, SketchStyle} from './sketch';

// ---- 注意力三件（把"其余压暗"变成动作：dim / spot / loupe / marker）----
export {FocusFx, FOCUS_MODES} from './focus';
export type {FocusMode, FocusRect} from './focus';

// ---- 零依赖「炫效果」----
export {GlowFrame, ShimmerText, ClipReveal, NoiseJitter, VerdictBar} from './effects';

// ---- 路径 / 几何 / 转场 / 运动模糊（@remotion 官方扩展）----
export {
  PathDraw,
  MorphShape,
  ShapeDraw,
  PieDraw,
  SHAPES,
  SceneTransitions,
  PRESENTATIONS,
  transitionsTotalFrames,
  usePathDraw,
  viewBoxOf,
  CameraMotionBlur,
  Trail,
} from './pathfx';
export type {PresentationName} from './pathfx';

// ---- 真实文字测量（治卡片裁切的正解）----
// 断行策略：优先落在 budoux 给出的**词组边界**，退化时按字断并遵守避头尾。
export {FitTextBox, fitChineseTextOnNLines, useFontsReady, assertFits, fitsWithin} from './fittext';

/** 封装层版本：接触表页脚与门禁用它确认"看到的是这一版"。 */
export const COMPONENTS_VERSION = 'components-v3 · 29 件 · 依赖见 package.json';
