// ============================================================================
// transitions/pagefold.tsx · 折痕翻页（没有 WebGPU 时的纯 CSS 版）
//
// 为什么不能用 rotateY 转整页：绕右缘 → 整页均匀收窄，读作「被抽走」；绕左缘 → 近大远小把右缘
// 顶出画面，读作「朝观众扑来」。观众认的翻页不是「一个矩形在转」，是**一条折痕扫过纸面**：
// 右下角先翘起，翻过去的那半张露出纸背。所以这里不做 3D 旋转，只做「沿一条折线翻折」。
//
// 折线写成 x − K·y = c，法线 (1,−K) 正好是 CSS 的 atan2(1,K) 渐变方向，
// 于是「切出折线两侧」= 两个硬边渐变遮罩，位置就是 (1−e)·100%——纯比例，不需要裁剪多边形。
// 被折走的那半张绕折线转 180°，在 2D 里等价于关于折线镜像，于是纸背朝观众、正文反着出现，
// 所以纸背要盖住镜像的字，只留一点透光。
//
// 折线方向与 GPU 卷页**共用** transitions/meta.ts 的 PAGETURN_FOLD_DIRECTION：
// 预览走 CSS、成片走 GPU，两种翻页方向不一样，观众会以为换了转场。
// K = tan(12°) 就是那个 78°——不要在这里再写一次角度。
// ============================================================================

import React from 'react';
import {AbsoluteFill, Easing} from 'remotion';
import {PAGETURN_FOLD_DIRECTION} from './meta';

const PAGE_W = 1920, PAGE_H = 1080;
export const FOLD_K = Math.tan((90 - Math.abs(PAGETURN_FOLD_DIRECTION)) * Math.PI / 180);
export const FOLD_DEG = Math.atan2(1, FOLD_K) * 180 / Math.PI;
export const FOLD_SPAN = PAGE_W + FOLD_K * PAGE_H;   // 折线扫过整页要走的跨度

const clamp01 = (v: number) => Math.min(1, Math.max(0, v));
/** 渐变 stop 一律夹回 [0,100]：折线扫出画面后 x 会变成负数 / 超过 100，别让它们漏进 CSS。 */
const pct = (v: number) => Math.min(100, Math.max(0, v));
// 模块级建一次，别每帧重建缓动函数（转场期间每帧都跑）。
const foldEase = Easing.bezier(0.22, 0, 0.18, 1);
/** 折痕扫过整页用转场的前 92%，剩下 8% 留给纸背淡出。 */
const FOLD_TRAVEL = 0.92;

export const PageFold = ({p, paper, backPage, children}: {p: number; paper: string; backPage?: React.ReactNode; children: React.ReactNode}) => {
  const t = clamp01(p);
  // 缓动起手要快（0.73 秒里前 0.2 秒没动静，观众只会觉得卡了一下），落定要长。
  // 输入必须先夹回 [0,1]：t>0.92 时 t/FOLD_TRAVEL 会超过 1，贝塞尔外推会让折线冲到画面外更深的位置。
  const e = foldEase(clamp01(t / FOLD_TRAVEL));
  const c = PAGE_W - e * FOLD_SPAN;             // 折线 x − K·y = c
  const x = (1 - e) * 100;                      // 折线在渐变轴上的位置（%）
  const back = clamp01((e - 0.16) / 0.40);      // 纸背：刚起折只有一条窄边，越翻越实
  // 折完不能「整屏纸背 → 硬切新页」：纸还要向左滑出画面，否则最后两帧像闪了一下。
  const leave = clamp01((t - 0.82) / 0.18);
  const edge = (a: string) => ({WebkitMaskImage: a, maskImage: a});
  const grad = (stops: string) => `linear-gradient(${FOLD_DEG}deg,${stops})`;
  return (
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden', opacity: 1 - leave,
      transform: `translate(${-110 * leave}px, ${-30 * leave}px)`}}>
      {/* A：还没被折走的那部分。折线内侧压一道纸背投下的软影，纸才不会像一张贴纸。 */}
      <div style={{position: 'absolute', inset: 0, ...edge(grad(`#000 ${pct(x)}%,transparent ${pct(x)}%`))}}>
        {children}
        <AbsoluteFill style={{background: grad(`transparent ${pct(x - 9)}%,rgba(48,32,12,${(0.30 * back).toFixed(3)}) ${pct(x)}%,transparent ${pct(x)}%`)}}/>
      </div>
      {/* 折起的那块空出来了，下面是新页——翻起来的纸要在这里投影，否则新页像一张贴纸铺在桌上。 */}
      <AbsoluteFill style={{background: grad(`transparent ${pct(x)}%,rgba(52,34,12,${(0.26 * back).toFixed(3)}) ${pct(x + 2)}%,transparent ${pct(x + 14)}%`)}}/>
      {/* B：折过去的那半张。绕折线转 180° = 关于折线镜像，看到的是纸的背面。 */}
      <div style={{position: 'absolute', inset: 0, transform: `rotate3d(${FOLD_K},1,0,180deg)`,
        transformOrigin: `${c + FOLD_K * PAGE_H / 2}px ${PAGE_H / 2}px`, ...edge(grad(`transparent ${pct(x)}%,#000 ${pct(x)}%`))}}>
        {/* 纸背只带纸，不带场景：透光看见的是纸的纹理，不是清晰的反字（那反而假），
            而且这样转场帧不必把上一镜的整个场景渲染第二遍。 */}
        {backPage ?? children}
        {/* 纸背：盖掉镜像的正文，只留一点透光（太实像贴了张白纸，太透会看到反字） */}
        <AbsoluteFill style={{background: paper, opacity: 0.86 + 0.10 * back}}/>
        {/* 纸背的受光：离折痕越远越亮，纸才有弯过去的感觉，不是一块平色块 */}
        <AbsoluteFill style={{background: grad(`rgba(255,255,255,0.02) ${pct(x)}%,rgba(255,255,255,0.34) ${pct(x + 26)}%,rgba(255,255,255,0.10) 100%`)}}/>
        {/* 折痕内侧暗部 */}
        <AbsoluteFill style={{background: grad(`rgba(62,42,16,${(0.20 * back).toFixed(3)}) ${pct(x)}%,transparent ${pct(x + 16)}%`)}}/>
        {/* 纸的厚度边：折线上一道细高光，缺了它折角像印上去的 */}
        <AbsoluteFill style={{background: grad(`transparent ${pct(x)}%,rgba(255,255,255,0.55) ${pct(x + 0.8)}%,transparent ${pct(x + 3)}%`)}}/>
      </div>
    </div>
  );
};
