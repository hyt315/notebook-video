import React from 'react';
import {evolvePath, getBoundingBox, getLength, getPointAtLength, getTangentAtLength, interpolatePath} from '@remotion/paths';
import {
  makeArrow,
  makeCallout,
  makeCircle,
  makeEllipse,
  makeHeart,
  makePolygon,
  makeRect,
  makeSpark,
  makeStar,
  makeTriangle,
  Pie,
} from '@remotion/shapes';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {slide} from '@remotion/transitions/slide';
import {wipe} from '@remotion/transitions/wipe';
import {clockWipe} from '@remotion/transitions/clock-wipe';
import {iris} from '@remotion/transitions/iris';
// 2026-09-21：把包里**全部** 19 种官方转场都登记进来（此前只封了 5 种，
// 其余 14 种"装了但没人知道名字"，等于不存在）。全部在 `diag-upgrade` 页⑥
// 逐个实渲过一帧（含 WebGL 着色器那几种，见该页的结论）。
import {flip} from '@remotion/transitions/flip';
import {bookFlip} from '@remotion/transitions/book-flip';
import {dissolve} from '@remotion/transitions/dissolve';
import {ripple} from '@remotion/transitions/ripple';
import {swap} from '@remotion/transitions/swap';
import {crosswarp} from '@remotion/transitions/crosswarp';
import {crossZoom} from '@remotion/transitions/cross-zoom';
import {zoomBlur} from '@remotion/transitions/zoom-blur';
import {zoomInOut} from '@remotion/transitions/zoom-in-out';
import {blurSlide} from '@remotion/transitions/blur-slide';
import {dreamyZoom} from '@remotion/transitions/dreamy-zoom';
import {filmBurn} from '@remotion/transitions/film-burn';
import {linearBlur} from '@remotion/transitions/linear-blur';
import {none} from '@remotion/transitions/none';
import {pushCut} from '@remotion/transitions/push-cut';
import {THEME} from '../theme/active';
import {TYPE} from '../kit';
import {prog} from './ui';

// ============================================================================
// pathfx.tsx — 路径 / 几何 / 转场（@remotion 官方扩展）
//
// 这三个包与渲染引擎同厂、按帧驱动设计，不存在「库自带时间动画」的冲突，
// 是引入成本最低的一类扩展。加依赖时优先考虑这一族。
// ============================================================================

const C = THEME.palette;

// `ShapeInfo` 是 `@remotion/shapes` 内部 utils/shape-info 的类型，**没有从包根导出**
// （tsc TS2305，此前一直靠 `any` 混过去）。用 ReturnType 就地取：与库里那个类型
// 逐字段相同，且不依赖深路径导入。
type ShapeInfo = ReturnType<typeof makeRect>;

/**
 * PathDraw — 描线生长。
 * 给一个 0→1 的进度就得到 dash 参数，不用自己算路径长度。
 * 传 strokeDasharray/strokeDashoffset 给 <path> 即可。
 */
export const usePathDraw = (path: string, progress: number) => evolvePath(progress, path);

/** 由路径实测边界反推 viewBox——不要猜图形坐标。 */
export const viewBoxOf = (path: string, pad = 26) => {
  const b = getBoundingBox(path);
  return `${b.x1 - pad} ${b.y1 - pad} ${b.x2 - b.x1 + pad * 2} ${b.y2 - b.y1 + pad * 2}`;
};

/**
 * PathDraw — 把一条 SVG 路径按帧画出来，并可选带一个沿线跑的点、
 * 或一个**沿线朝向**的箭头（getTangentAtLength：小车沿路线跑并转向）。
 */
export const PathDraw: React.FC<{
  f: number;
  path: string;
  startAt: number;
  durationInFrames?: number;
  width: number;
  height: number;
  viewBox: string;
  strokeWidth?: number;
  tone?: string;
  showDot?: boolean;
  /** 沿线运动的箭头：用 getTangentAtLength 让它跟着路径转向 */
  showArrow?: boolean;
  dashedGhost?: boolean;
}> = ({
  f,
  path,
  startAt,
  durationInFrames = 60,
  width,
  height,
  viewBox,
  strokeWidth = 10,
  tone,
  showDot = false,
  showArrow = false,
  dashedGhost = true,
}) => {
  const p = prog(f, startAt, durationInFrames);
  const {strokeDasharray, strokeDashoffset} = usePathDraw(path, p);
  const a = tone ?? C.blue;
  const total = getLength(path);
  const at = (q: number) => getPointAtLength(path, total * q);
  const dot = showDot ? at(p) : null;
  const arrow = showArrow ? at(p) : null;
  // 朝向：切线角（度）。getTangentAtLength 直接给这一点的走向，不用自己差分。
  const tangent = showArrow ? getTangentAtLength(path, total * p) : null;
  return (
    <svg width={width} height={height} viewBox={viewBox} style={{overflow: 'visible'}}>
      {dashedGhost ? <path d={path} fill="none" stroke={C.line} strokeWidth={Math.max(2, strokeWidth * 0.4)} strokeDasharray="10 14" /> : null}
      <path d={path} fill="none" stroke={a} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={strokeDasharray} strokeDashoffset={strokeDashoffset} />
      {dot ? <circle cx={dot.x} cy={dot.y} r={strokeWidth * 1.8} fill={C.orange} stroke={C.ink} strokeWidth={5} /> : null}
      {arrow && tangent ? (
        <g transform={`translate(${arrow.x},${arrow.y}) rotate(${(Math.atan2(tangent.y, tangent.x) * 180) / Math.PI})`}>
          <path
            d={makeArrow({length: 118, headWidth: 62, headLength: 62, shaftWidth: 24}).path}
            fill={C.orange}
            stroke={C.ink}
            strokeWidth={4}
            transform="translate(-14,-31)"
          />
        </g>
      ) : null}
    </svg>
  );
};

/**
 * MorphShape — 形状连续变形（方变圆、圆变星）。
 * 用 interpolatePath 在两个 path 字符串之间插值。
 */
export const MorphShape: React.FC<{
  f: number;
  fromPath: string;
  toPath: string;
  startAt: number;
  durationInFrames?: number;
  width: number;
  height: number;
  viewBox?: string;
  strokeWidth?: number;
  tone?: string;
}> = ({f, fromPath, toPath, startAt, durationInFrames = 60, width, height, viewBox, strokeWidth = 12, tone}) => {
  const p = prog(f, startAt, durationInFrames);
  const d = interpolatePath(p, fromPath, toPath);
  return (
    <svg width={width} height={height} viewBox={viewBox ?? viewBoxOf(d, 40)} style={{overflow: 'visible'}}>
      <path d={d} fill="none" stroke={tone ?? C.green} strokeWidth={strokeWidth} strokeLinejoin="round" />
    </svg>
  );
};

/**
 * 参数化几何图形：由 make* 算出 path，再用 evolvePath 描线。
 *
 * `@remotion/shapes` 有 22 个导出，此前只用了 5 个。补进来的三个正是
 * 讲解片高频的**修辞动作**：callout 是「标注框」、arrow 是「指向」、
 * heart 是「要点/喜欢」。手写这三个的 path 既费劲又不好看。
 */
export const SHAPES = {
  star: (inner = 110, outer = 250) => makeStar({points: 5, innerRadius: inner, outerRadius: outer}),
  hexagon: (r = 230) => makePolygon({points: 6, radius: r}),
  triangle: (r = 240) => makePolygon({points: 3, radius: r}),
  circle: (r = 250) => makeCircle({radius: r}),
  spark: (w = 440, h = 440) => makeSpark({width: w, height: h}),
  /** 气泡/标注框：左下方带一个尖角，正好接引线 */
  // ⚠️ tsc 的 TS2353/TS2345 在这里抓出四处**静默失效**（这四件一直没被用过，所以从没暴露）：
  //   · makeCallout 的尖角参数叫 `pointerBaseWidth`，不是 `tipWidth` → 尖角宽度一直取默认
  //   · makeHeart / makeEllipse 没有 `width`（分别是 height+aspectRatio / rx+ry）
  //   · makeTriangle 的 `direction` 是**必填**
  // 都是「传了参数、库当没看见」。
  callout: (w = 460, h = 260, tipW = 90) => makeCallout({width: w, height: h, pointerBaseWidth: tipW}),
  arrow: (len = 420) => makeArrow({length: len, headWidth: 150, headLength: 130, shaftWidth: 56}),
  heart: (size = 300) => makeHeart({height: size, aspectRatio: 1}),
  ellipse: (w = 460, h = 300) => makeEllipse({rx: w / 2, ry: h / 2}),
  rect: (w = 440, h = 300) => makeRect({width: w, height: h, cornerRadius: 16}),
  triangleShape: (len = 300) => makeTriangle({length: len, direction: 'right'}),
} as const;

/**
 * ShapeDraw — 把参数化图形画进一个格子里，支持描线进度。
 */
export const ShapeDraw: React.FC<{
  f: number;
  shape: ShapeInfo;
  startAt: number;
  durationInFrames?: number;
  size: number;
  tone?: string;
  label?: string;
  filled?: boolean;
}> = ({f, shape, startAt, durationInFrames = 45, size, tone, label, filled = true}) => {
  const p = prog(f, startAt, durationInFrames);
  const {strokeDasharray, strokeDashoffset} = usePathDraw(shape.path, p);
  const a = tone ?? C.gold;
  return (
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10}}>
      <svg width={size} height={size} viewBox={viewBoxOf(shape.path)}>
        <path
          d={shape.path}
          fill={filled ? `${a}22` : 'none'}
          stroke={a}
          strokeWidth={10}
          strokeLinejoin="round"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
        />
      </svg>
      {label ? <span style={{fontFamily: 'Space,Kai,monospace', fontSize: TYPE.microS, color: C.ink}}>{label}</span> : null}
    </div>
  );
};

/** PieDraw — 唯一自带 progress 的图形组件，直接绑帧号即可。 */
export const PieDraw: React.FC<{f: number; startAt: number; durationInFrames?: number; radius?: number; spin?: boolean; tone?: string}> = ({
  f,
  startAt,
  durationInFrames = 70,
  radius = 95,
  spin = false,
  tone,
}) => {
  const p = prog(f, startAt, durationInFrames);
  const a = tone ?? C.blue;
  return (
    <Pie
      radius={radius}
      progress={p}
      rotation={spin ? (f * Math.PI * 2) / 300 : 0}
      fill={`${a}33`}
      stroke={a}
      strokeWidth={8}
    />
  );
};

// ---------------------------------------------------------------------------
// 转场：20 种官方演示型转场，不用再手写（含 blurSlide；`PRESENTATIONS` 的键即全部）
//
// 全部登记（2026-09-21 补齐余下 14 种）。每项收一个统一的 ctx，返回官方的
// presentation 对象——调用方是 `SceneTransitions`，或直接用 PRESENTATIONS[name](ctx)。
// `none` 是真的"不转场"（硬切），要"什么都不做"时用它而不是随便挑一个。
// ---------------------------------------------------------------------------
export type PresentationCtx = {
  direction: 'from-left' | 'from-right' | 'from-top' | 'from-bottom';
  width: number;
  height: number;
};

export const PRESENTATIONS = {
  // ---- 几何式（纯 CSS/SVG，无需 WebGL）----
  fade: () => fade(),
  slide: ({direction}: PresentationCtx) => slide({direction}),
  wipe: ({direction}: PresentationCtx) => wipe({direction}),
  clockWipe: ({width, height}: PresentationCtx) => clockWipe({width, height}),
  iris: ({width, height}: PresentationCtx) => iris({width, height}),
  flip: ({direction}: PresentationCtx) => flip({direction}),
  bookFlip: ({direction}: PresentationCtx) => bookFlip({direction}),
  // PushCutProps 里没有 `direction`（是 cutProgress/outgoingScale/…）：传了也没用。
  pushCut: () => pushCut({}),
  none: () => none(),
  // ---- 着色器式（走 WebGL；本机实测见 diag-upgrade 页⑥）----
  // 注意：这几个的 `props` 在类型上是**必填**（只是属性都可选），所以传 `{}` 而不是不传。
  dissolve: () => dissolve({spreadColor: C.paper, hotColor: C.orange}),
  ripple: () => ripple({}),
  swap: () => swap({depth: 0.6}),
  crosswarp: () => crosswarp({}),
  crossZoom: () => crossZoom({strength: 0.7}),
  zoomBlur: () => zoomBlur({}),
  zoomInOut: () => zoomInOut({}),
  blurSlide: ({direction}: PresentationCtx) => blurSlide({direction}),
  dreamyZoom: () => dreamyZoom({}),
  filmBurn: () => filmBurn({seed: 7}), // seed 写死：默认值也要确认是确定的（包里 Math.random 0 处）
  linearBlur: () => linearBlur({}),
} as const;

export type PresentationName = keyof typeof PRESENTATIONS;

/**
 * SceneTransitions — 把若干片段用指定转场串起来。
 *
 * 注意时长运算：TransitionSeries 的总长 = Σ片段长 − Σ转场长（转场是两镜重叠的部分）。
 *   例：6 段 × 60 帧、5 个 12 帧转场 → 360 − 60 = 300 帧
 *
 * 19 种可选（名称 = 官方包名去掉连字符；`clock-wipe`→`clockWipe`、`cross-warp`→`crosswarp`、
 * `cross-zoom`→`crossZoom`、`zoom-in-out`→`zoomInOut`、`blur-slide`→`blurSlide`、
 * `dreamy-zoom`→`dreamyZoom`、`film-burn`→`filmBurn`、`linear-blur`→`linearBlur`、
 * `push-cut`→`pushCut`、`book-flip`→`bookFlip`、`zoom-blur`→`zoomBlur`）：
 *   fade / slide / wipe / flip / clockWipe / iris / dissolve / ripple /
 *   zoomBlur / filmBurn / bookFlip / swap / crosswarp / crossZoom /
 *   zoomInOut / dreamyZoom / linearBlur / pushCut / none
 */
export const SceneTransitions: React.FC<{
  children: React.ReactNode[];
  durations: number[];
  transition: PresentationName;
  transitionDuration?: number;
  width: number;
  height: number;
  direction?: 'from-left' | 'from-right' | 'from-top' | 'from-bottom';
}> = ({children, durations, transition, transitionDuration = 16, width, height, direction = 'from-left'}) => {
  // TS2322：`PRESENTATIONS[transition]` 是 19 个工厂的联合，返回 19 种
  // TransitionPresentation<不同 Props>；TransitionSeries.Transition 只接受其中一种。
  // 运行时行为是对的（选中的那一个一定与 children 匹配），只是三个联合类型无法在
  // 编译期收敛 —— 收据化到组件自己的 prop 类型再交给它，比给每个工厂写重载更实在。
  const presentation = PRESENTATIONS[transition]({direction, width, height}) as unknown as
    React.ComponentProps<typeof TransitionSeries.Transition>['presentation'];
  return (
    <TransitionSeries>
      {children.map((child, i) => (
        <React.Fragment key={i}>
          {i > 0 ? <TransitionSeries.Transition presentation={presentation} timing={linearTiming({durationInFrames: transitionDuration})} /> : null}
          <TransitionSeries.Sequence durationInFrames={durations[i] ?? 60}>{child}</TransitionSeries.Sequence>
        </React.Fragment>
      ))}
    </TransitionSeries>
  );
};

/** 计算 TransitionSeries 的总时长，供 composition / Sequence 定长使用。 */
export const transitionsTotalFrames = (durations: number[], transitionDuration = 16) =>
  durations.reduce((a, b) => a + b, 0) - transitionDuration * Math.max(0, durations.length - 1);

// ---------------------------------------------------------------------------
// 运动模糊：@remotion/motion-blur
// ---------------------------------------------------------------------------
export {CameraMotionBlur, Trail} from '@remotion/motion-blur';
