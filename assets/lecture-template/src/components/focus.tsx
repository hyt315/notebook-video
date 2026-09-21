import React from 'react';
import {THEME} from '../theme/active';
import {prog} from './ui';

// ============================================================================
// focus.tsx — 注意力三件：把"其余压暗"这件事变成一件可复用的动作
//
// 替换掉什么：此前我们只会**往画面上加**——GlowFrame 整块发亮、ShimmerText 一句发光、
// Callout 圈一处、StampSeal 盖一下。全是"加东西强调"。而讲解视频里最有效的一手恰恰相反：
// **把不是重点的部分压下去**（focusing / 视觉钝化）。缺的从来不是"更亮的边框"，是"暗下去的背景"。
//
// 四种模式（闭合集，一镜只用一种）：
//   dim     四块半透明纸色盖住目标之外的一切 —— 最稳、最不容易做坏，缩略图/网格/表格首选
//   spot    目标上留一个亮斑，外围暗 —— 灯打在证据上
//   loupe   圆形放大镜：把 children 的某块区域放大显示（数字/小字/细节）
//   marker  目标外一圈手绘感描边，随时间画出（不依赖 roughjs，纯帧驱动的圆角矩形笔画）
//
// 纪律：只读 THEME；显隐/进度都是 f(帧号) 的纯函数；不用 CSS transition；
// 不改 children 的布局（dim/spot/marker 都是绝对定位覆盖层，pointer-events 关掉）。
// ============================================================================

const C = THEME.palette;

export type FocusMode = 'dim' | 'spot' | 'loupe' | 'marker';

export type FocusRect = {x: number; y: number; w: number; h: number};

const clamp01 = (v: number) => (v < 0 ? 0 : v > 1 ? 1 : v);

/** 入场曲线：ease-out（本件自带，不依赖 ui.prog 的线性——新层统一缓动是另一件待办）。
 *  实测依据：线性入场在 t=50% 时比 ease-out 落后 180px（探针 Probe-prog-ease 渲出来的数字）。 */
const easeOut3 = (v: number) => 1 - Math.pow(1 - clamp01(v), 3);

/** 遮罩浓度：dim/spot 用纸色半透明，四套皮肤都成立（不写死颜色）。 */
const VEIL = 0.72;

/**
 * 四块（或四边）纸色遮罩：把 rect 之外盖住。用四条而不是"整块 + 挖洞"，
 * 是因为 clip-path/evenodd 在不同浏览器与 Remotion 的截图路径上表现不一致——实测踩过。
 */
const Veil: React.FC<{rect: FocusRect; canvas: {w: number; h: number}; p: number; round?: number}> =
({rect, canvas, p, round = 0}) => {
  const a = VEIL * p;
  const style: React.CSSProperties = {position: 'absolute', background: C.paperBase, opacity: a, pointerEvents: 'none'};
  const x0 = Math.max(0, rect.x), y0 = Math.max(0, rect.y);
  const x1 = Math.min(canvas.w, rect.x + rect.w), y1 = Math.min(canvas.h, rect.y + rect.h);
  return (
    <>
      <div style={{...style, left: 0, top: 0, width: canvas.w, height: y0}} />
      <div style={{...style, left: 0, top: y1, width: canvas.w, height: Math.max(0, canvas.h - y1)}} />
      <div style={{...style, left: 0, top: y0, width: x0, height: Math.max(0, y1 - y0), borderRadius: round}} />
      <div style={{...style, left: x1, top: y0, width: Math.max(0, canvas.w - x1), height: Math.max(0, y1 - y0), borderRadius: round}} />
    </>
  );
};

/**
 * FocusFx — 一镜一次的"注意力动作"。`rect` 是**场景坐标**（与其它组件同一坐标系）。
 *
 * 用法：
 *   <FocusFx f={f} mode="dim" startAt={40} dur={18} rect={{x:200,y:300,w:900,h:420}} canvas={{w:1920,h:1080}}/>
 *   <FocusFx f={f} mode="loupe" rect={...} zoom={2.1} canvas={{w:1920,h:1080}}>{场景内容}</FocusFx>
 *
 * 退出：给 exitStart 就会在之后 18 帧内收回（其余组件都支持离场，这里不例外）。
 */
export const FocusFx: React.FC<{
  f: number;
  mode?: FocusMode;
  /** 要留住的那块（场景坐标） */
  rect: FocusRect;
  /** 画布尺寸，用来铺满遮罩 */
  canvas: {w: number; h: number};
  /** 入场起始帧（本镜局部帧） */
  startAt?: number;
  dur?: number;
  /** 离场起始帧；给了就在 18 帧内收回 */
  exitStart?: number;
  /** loupe 的倍率 */
  zoom?: number;
  /** marker 的描边色 */
  tone?: string;
  /** 可选：在目标旁挂一句话 */
  label?: string;
  children?: React.ReactNode;
}> = ({f, mode = 'dim', rect, canvas, startAt = 0, dur = 18, exitStart, zoom = 2.1, tone, label, children}) => {
  const pin = easeOut3(prog(f, startAt, dur));                       // 入场（ease-out）
  const pout = exitStart === undefined ? 0 : clamp01(prog(f, exitStart, 18));
  const p = Math.max(0, pin - pout);                                 // 收回时反向
  if (p <= 0) return <>{mode === 'loupe' ? children : null}</>;
  const accent = tone ?? C.orange;

  if (mode === 'dim' || mode === 'spot') {
    return (
      <>
        <Veil rect={rect} canvas={canvas} p={p} round={mode === 'spot' ? 999 : 6} />
        {mode === 'spot' ? (
          <div
            style={{
              position: 'absolute', left: rect.x, top: rect.y, width: rect.w, height: rect.h,
              border: `3px solid ${accent}`, borderRadius: 12, opacity: p, pointerEvents: 'none',
              boxShadow: `0 0 0 6px ${C.paperBase}00`,
            }}
          />
        ) : null}
        {label ? (
          <div style={{position: 'absolute', left: rect.x, top: Math.max(0, rect.y - 44), fontSize: 24, color: accent, opacity: p, fontWeight: 700}}>
            {label}
          </div>
        ) : null}
      </>
    );
  }

  if (mode === 'marker') {
    // 手绘感：一圈圆角描边按周长"画出来"，用 dash 偏移做（纯帧驱动，无随机）
    const per = 2 * (rect.w + rect.h) + 8 * 18;   // 近似周长（含圆角）
    return (
      <>
        <svg width={canvas.w} height={canvas.h} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
          <rect
            x={rect.x} y={rect.y} width={rect.w} height={rect.h} rx={16}
            fill="none" stroke={accent} strokeWidth={6} strokeLinecap="round"
            strokeDasharray={per} strokeDashoffset={per * (1 - p)}
            transform={`rotate(${-0.5} ${rect.x + rect.w / 2} ${rect.y + rect.h / 2})`}
          />
        </svg>
        {label ? (
          <div style={{position: 'absolute', left: rect.x, top: Math.max(0, rect.y - 44), fontSize: 24, color: accent, opacity: p, fontWeight: 700}}>
            {label}
          </div>
        ) : null}
      </>
    );
  }

  // loupe：圆形放大镜——把 children 放大后按圆裁切，钉在 rect 中心
  const r = Math.min(rect.w, rect.h) / 2;
  const cx = rect.x + rect.w / 2, cy = rect.y + rect.h / 2;
  const rp = r * (0.6 + 0.4 * p);                                   // 镜片从小长到全尺寸
  return (
    <>
      {children}
      <div
        style={{
          position: 'absolute', left: cx - rp, top: cy - rp, width: rp * 2, height: rp * 2,
          borderRadius: 999, overflow: 'hidden', border: `5px solid ${accent}`,
          opacity: Math.min(1, p * 1.2), pointerEvents: 'none',
          boxShadow: THEME.paperShadow(0.9),
        }}
      >
        <div
          style={{
            position: 'absolute', left: -rect.x * zoom + (rp * 2) / 2 - (rect.w * zoom) / 2 + (rp * 2) / 2 - rp,
            top: -rect.y * zoom + (rp * 2) / 2 - (rect.h * zoom) / 2 + (rp * 2) / 2 - rp,
            width: canvas.w * zoom, height: canvas.h * zoom, transform: `scale(1)`, transformOrigin: '0 0',
          }}
        >
          <div style={{width: canvas.w, height: canvas.h, transform: `scale(${zoom})`, transformOrigin: '0 0', position: 'absolute', left: 0, top: 0}}>
            {children}
          </div>
        </div>
      </div>
    </>
  );
};

export const FOCUS_MODES: FocusMode[] = ['dim', 'spot', 'loupe', 'marker'];
