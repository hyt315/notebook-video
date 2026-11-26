import {Easing, interpolate, spring} from 'remotion';

// 帧驱动动效的共用件：两端钳制、缓动曲线、区间插值、不过冲的弹簧。只依赖 remotion，任何模块都可 import。
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
export const EASE = {out: Easing.bezier(0.16, 1, 0.3, 1), in: Easing.in(Easing.quad), io: Easing.inOut(Easing.cubic)};
const tween = (easing: (t: number) => number) => (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing});
/** f 在 [a, b] 帧间从 from 走到 to：入场 easeOut（先快后稳），出场 easeIn（快而急），位移 easeIO。 */
export const easeOut = tween(EASE.out);
export const easeIn = tween(EASE.in);
export const easeIO = tween(EASE.io);
/** 弹簧只取「先快后稳」的手感；overshootClamping 让它不越过终值（草稿纸不回弹）。 */
export const SPRINGS = {snappy: {damping: 16, stiffness: 200, mass: 0.8}, soft: {damping: 17, stiffness: 132, mass: 0.86}} as const;
export const popS = (f: number, start: number, preset: keyof typeof SPRINGS = 'soft') =>
  spring({frame: f - start, fps: 30, config: {...SPRINGS[preset], overshootClamping: true}});
