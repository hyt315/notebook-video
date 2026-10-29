// ============================================================================
// craft/lens.tsx · 放大镜（3.3.0）
//
//   <Loupe f x y r zoom target={{x,y}} render={(inside) => <…/>} />
//
// 「看近一点」的原生动作：镜片落到物件上（阴影由大变小），镜片里是同一画面放大 zoom 倍、
// 以 target 为中心；render(inside) 被调用两次——镜外 inside=false，镜内 inside=true，
// 所以镜片里可以「变」：负片转正、一行字亮起、空盒子被刷成房间……这正是档案灯台 / 手账的顿悟点。
// 只由帧号驱动；镜片之外的世界不受影响（不需要相机推近，也不触发取景门禁）。
// ============================================================================
import React from 'react';
import {interpolate, Easing} from 'remotion';
import {THEME} from '../theme/active';

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

export type LoupeProps = {
  f: number;
  /** 镜片圆心（设计坐标）与半径 */
  x: number; y: number; r: number;
  /** 镜片里放大倍数（1.6–3） */
  zoom?: number;
  /** 镜片对准的世界坐标（缺省 = 圆心正下方） */
  target?: {x: number; y: number};
  /** 落下帧：从右上方移入并「落」到台面上 */
  at?: number;
  /** 画面：inside=true 时画镜片里的版本 */
  render: (inside: boolean) => React.ReactNode;
  /** 只要镜片、不要手柄 */
  handle?: boolean;
  /** 手柄方向（度，0 = 向右、90 = 向下；缺省 45 = 右下）。LoupeMedia 按署名位置自动选 */
  handleAngle?: number;
};

/** 手柄几何（落定后）：从镜框外缘伸出，长 0.95r、粗 34。 */
export const LOUPE_HANDLE_THICK = 34;
export const loupeHandleBox = (cx: number, cy: number, r: number, angle: number) => {
  const a = (angle * Math.PI) / 180, c = Math.cos(a), s = Math.sin(a);
  const sx = cx + 0.96 * r * c, sy = cy + 0.96 * r * s, ex = sx + 0.95 * r * c, ey = sy + 0.95 * r * s;
  const pad = LOUPE_HANDLE_THICK / 2 + 10; // 半粗 + 投影
  return {sx, sy, left: Math.min(sx, ex) - pad, top: Math.min(sy, ey) - pad, right: Math.max(sx, ex) + pad, bottom: Math.max(sy, ey) + pad};
};
type Rect = {left: number; top: number; right: number; bottom: number};
const overlapArea = (a: Rect, b: Rect) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
/** 选一个手柄方向，让手柄的包围盒不压任何一个 avoid 矩形（署名框）；都压就取压得最少的。 */
export const pickHandleAngle = (cx: number, cy: number, r: number, avoid: Rect[], candidates = [45, 135, -45, -135, 90, 0, 180, -90]) => {
  let best = candidates[0], bestA = Infinity;
  for (const ang of candidates) {
    const b = loupeHandleBox(cx, cy, r, ang);
    const area = avoid.reduce((acc, x) => acc + overlapArea(b, {left: x.left - 6, top: x.top - 6, right: x.right + 6, bottom: x.bottom + 6}), 0);
    if (area === 0) return ang;
    if (area < bestA) { bestA = area; best = ang; }
  }
  return best;
};

export const Loupe: React.FC<LoupeProps> = ({f, x, y, r, zoom = 2.2, target, at = 0, render, handle = true, handleAngle = 45}) => {
  const p = interpolate(f, [at, at + 16], [0, 1], {...clamp, easing: Easing.bezier(0.2, 0.9, 0.25, 1)});
  const lift = 1 - p;
  const cx = x + 260 * lift, cy = y - 200 * lift;
  const t = target ?? {x: cx, y: cy};
  const C = THEME.palette;
  const rim = THEME.id === 'archive' ? '#2b3238' : '#3a2e24';
  return <>
    {render(false)}
    {p > 0 && <>
      {/* 投影：落下时大而淡，落定后小而实 */}
      <div style={{position: 'absolute', left: cx - r + 14 + 30 * lift, top: cy - r + 22 + 40 * lift, width: r * 2, height: r * 2, borderRadius: '50%',
        background: 'rgba(20,20,20,0.22)', filter: `blur(${10 + 20 * lift}px)`, opacity: p}} />
      {/* 镜内：同一画面放大，以 target 为中心 */}
      <div style={{position: 'absolute', left: cx - r, top: cy - r, width: r * 2, height: r * 2, borderRadius: '50%', overflow: 'hidden', opacity: Math.min(1, p * 1.6),
        background: C.paperBase}}>
        <div style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, transformOrigin: '0 0',
          transform: `translate(${r - t.x * zoom}px, ${r - t.y * zoom}px) scale(${zoom})`}}>
          {render(true)}
        </div>
        {/* 玻璃：上沿高光 + 边缘暗角 */}
        <div style={{position: 'absolute', inset: 0, borderRadius: '50%', boxShadow: `inset 0 0 ${r * 0.25}px rgba(0,0,0,0.28)`,
          background: 'radial-gradient(circle at 32% 26%, rgba(255,255,255,0.32), rgba(255,255,255,0) 38%)'}} />
      </div>
      {/* 镜框 */}
      <div style={{position: 'absolute', left: cx - r - 10, top: cy - r - 10, width: r * 2 + 20, height: r * 2 + 20, borderRadius: '50%',
        border: `12px solid ${rim}`, boxShadow: 'inset 0 0 0 2px rgba(255,255,255,0.18)', opacity: Math.min(1, p * 1.6)}} />
      {handle && (() => {
        const hb = loupeHandleBox(cx, cy, r, handleAngle);
        return <div style={{position: 'absolute', left: hb.sx, top: hb.sy - LOUPE_HANDLE_THICK / 2, width: r * 0.95, height: LOUPE_HANDLE_THICK, borderRadius: LOUPE_HANDLE_THICK / 2, background: rim,
          transformOrigin: '0 50%', transform: `rotate(${handleAngle}deg)`, opacity: Math.min(1, p * 1.6), boxShadow: '0 6px 10px rgba(0,0,0,0.25)'}} />;
      })()}
    </>}
  </>;
};
