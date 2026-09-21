import React from 'react';
import rough from 'roughjs';
import {THEME} from '../theme/active';
import {prog} from './ui';

// ============================================================================
// sketch.tsx — 手绘风（roughjs）
//
// 为什么值得单独一件：技能的定位是「手账风」，而手绘标注、圈画、下划线
// 是这个风格的核心修辞动作。手写 SVG 画出来的是**规则椭圆**——一眼就是电脑画的。
// roughjs 给线条加手抖与重复笔触，才是真的像手画。
//
// 确定性：roughjs 用种子化伪随机，**同一个 seed 永远画出同一笔迹**，
// 不破坏"同一份代码渲出同一支片"（dependency-policy.md 判据第二条）。
// ⚠️ 两处例外，都是实测抓到的（见下面 fillStyle 的注释）：
//   ① `fillStyle:'dots'` 的填充器无条件调 `Math.random()` → **已从本组件移除**；
//   ② `seed: 0` 是假值 → roughjs 的 LCG 退回 `Math.random()` → 所有填充失效。
//
// 帧驱动：画完的每条路径都会按帧号设 strokeDasharray/Offset，
// 所以手绘线条可以"自己画出来"，而不是淡入。
// ============================================================================

const C = THEME.palette;

export type SketchPrim =
  | {kind: 'rect'; x: number; y: number; w: number; h: number}
  | {kind: 'ellipse'; cx: number; cy: number; w: number; h: number}
  | {kind: 'circle'; cx: number; cy: number; d: number}
  | {kind: 'line'; x1: number; y1: number; x2: number; y2: number}
  | {kind: 'polygon'; points: [number, number][]};

export type SketchStyle = {
  stroke?: string;
  strokeWidth?: number;
  fill?: string;
  /** 抖动强度：1 是默认，越大越"草" */
  roughness?: number;
  /** 线条重描次数 */
  bowing?: number;
  seed?: number;
  /**
   * 填充方式（roughjs 的招牌能力）。**手账风的关键质感就在这里**——
   * 只有空心描边会显得单薄，加上排线/交叉排线/点阵才像真的手绘本。
   *   'hachure'（默认）单排线 · 'zigzag' 锯齿线 · 'cross-hatch' 交叉排线
   *   'dashed' 虚线 · 'zigzag-line' 锯齿描边 · 'solid' 实心
   *
   * ⚠️ **没有 `'dots'`**（实测，2026-09-21）：roughjs 的 `dots` 填充器在
   * `bundled/rough.cjs.js` 里**无条件调用 `Math.random()` 两次/每点**
   * （`M=d-s+2*Math.random()*s, k=v-s+2*Math.random()*s`，`dotsOnLines` 内），
   * **与 seed 无关**——其余填充器都走种子化 LCG，只有它走真随机。
   * 后果是同一帧渲两次像素不一致（实测接触表第 ⑭ 页同一帧渲三次得到三个不同哈希，
   * 差异全部落在 dots 那一格），直接违反「同一份代码渲出同一支片」。
   * → 需要点状质感时用 `'dashed'` 或 `hachureGap` 调大的 `hachure`。
   *
   * ⚠️ **`seed` 不要传 0**：roughjs 的 LCG 是 `this.seed ? … : Math.random()`，
   * 0 是假值 → 整条随机链退回 `Math.random()`，**所有填充都会变得不可复现**。
   */
  fillStyle?: 'hachure' | 'solid' | 'zigzag' | 'cross-hatch' | 'dashed' | 'zigzag-line';
  /** 填充线粗细 */
  fillWeight?: number;
  /** 排线角度（度） */
  hachureAngle?: number;
  /** 排线间距 */
  hachureGap?: number;
};

/**
 * SketchFx — 手绘风图形。
 *
 * 用法一（只画图形）：`<SketchFx f={f} width={600} height={300} draw={[{kind:'circle',cx:200,cy:150,d:180}]} />`
 * 用法二（图形 + 内容）：把 children 传进来，图形画在下层，内容叠在上面。
 */
export const SketchFx: React.FC<{
  f: number;
  width: number;
  height: number;
  draw: SketchPrim[];
  startAt?: number;
  drawFrames?: number;
  style?: SketchStyle;
  /** 每个图形错开出现的帧数 */
  stagger?: number;
  children?: React.ReactNode;
}> = ({f, width, height, draw, startAt = 0, drawFrames = 34, style, stagger = 10, children}) => {
  const ref = React.useRef<SVGSVGElement>(null);

  React.useEffect(() => {
    const svg = ref.current;
    if (!svg) return;
    svg.innerHTML = ''; // 每帧重画前先清空，否则会叠加出越来越重的笔迹
    const rc = rough.svg(svg);
    const base = {seed: 1, roughness: 1.5, stroke: C.ink, strokeWidth: 2.6, ...style};
    // ---- seed 运行期护栏（2026-09-21）----
    // roughjs 的 LCG 写作 `this.seed ? imul(48271, seed) : Math.random()`：**0 是假值**，
    // 于是 `seed: 0`（或第一个图形算出的 `0 + 0*7`）会让整条随机链退回真随机，
    // 所有笔迹每帧都不一样 —— 直接违反"同一份代码渲出同一支片"。
    // 处置：告警 + **自动换成非零种子**，保证"给 0 也不会产出不确定结果"。
    // ⚠️ 这条告警**刻意不加 `NODE_ENV !== 'production'` 门**（本仓库其它开发期告警是加的）：
    // 渲染包由 webpack 以 production 模式打包，`process.env.NODE_ENV` 会被替换成
    // 'production'，加门等于"真正出片的那条路径上永远看不到告警"（实测确认过）。
    // 它只在作者真的传了 0 时才响，正常渲染零噪音。
    if (!base.seed) {
      console.warn(
        '[SketchFx] style.seed 传了 0（或会被算成 0）：roughjs 把 0 当成"没给种子"，' +
          '整条随机链会退回 Math.random()，同一帧渲两次笔迹不同。已自动改用 seed=1；请显式传一个非零整数。'
      );
      base.seed = 1;
    }

    draw.forEach((prim, i) => {
      const s = base.seed + i * 7;
      const node =
        prim.kind === 'rect'
          ? rc.rectangle(prim.x, prim.y, prim.w, prim.h, {...base, seed: s})
          : prim.kind === 'ellipse'
            ? rc.ellipse(prim.cx, prim.cy, prim.w, prim.h, {...base, seed: s})
            : prim.kind === 'circle'
              ? rc.circle(prim.cx, prim.cy, prim.d, {...base, seed: s})
              : prim.kind === 'line'
                ? rc.line(prim.x1, prim.y1, prim.x2, prim.y2, {...base, seed: s, fill: undefined})
                : rc.polygon(prim.points, {...base, seed: s});
      svg.appendChild(node);

      // 帧驱动：让这一组路径按进度"自己画出来"
      const p = prog(f, startAt + i * stagger, drawFrames);
      node.querySelectorAll('path').forEach((path) => {
        try {
          const len = (path as SVGPathElement).getTotalLength();
          path.style.strokeDasharray = `${len}`;
          path.style.strokeDashoffset = `${len * (1 - p)}`;
        } catch {
          /* getTotalLength 对空路径会抛，忽略 */
        }
      });
    });
  }, [f, draw, startAt, drawFrames, stagger, style]);

  return (
    <div style={{position: 'relative', width, height}}>
      <svg ref={ref} width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0, overflow: 'visible'}} />
      {children ? <div style={{position: 'absolute', inset: 0}}>{children}</div> : null}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 常用形状的便捷构造器（纯函数，不是组件——按 dependency-policy §8「效果不新开组件」）
// ---------------------------------------------------------------------------

/** 手绘圈住一块区域（配合 Callout 式的"圈重点"修辞动作）。 */
export const sketchCircleArea = (x: number, y: number, w: number, h: number): SketchPrim => ({
  kind: 'ellipse',
  cx: x + w / 2,
  cy: y + h / 2,
  w: w + 26,
  h: h + 22,
});

/** 手绘下划线。 */
export const sketchUnderline = (x: number, y: number, w: number): SketchPrim => ({kind: 'line', x1: x, y1: y, x2: x + w, y2: y});

/** 手绘方框。 */
export const sketchBox = (x: number, y: number, w: number, h: number): SketchPrim => ({kind: 'rect', x, y, w, h});
