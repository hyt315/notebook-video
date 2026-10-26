// ============================================================================
// craft/paper.tsx · 纸与颜料（3.3.0）
//
//   PaperSheet  一张自由放置的纸（不是 UI 卡片）：毛边 / 撕边、纤维、贴面投影、可选胶带；可「放下来」入场
//   WashBlob    一团水彩淡彩：噪声边缘 + 三遍叠色（积水深边）+ 颗粒，按进度「晕开」
//   CutPaper    一片剪纸：任意 SVG 路径（evenodd 支持镂空洞）+ 切口亮/暗边 + 纸厚投影；12 fps 跳帧入场
//   Seal        一方红印：按下去的三帧（放大→落定→墨色不匀）
//
// 全部只由帧号驱动，噪声来自 @remotion/noise（确定性 seed）。颜色取当前皮肤 THEME.palette / THEME.craft。
// 手法参考：lemo-opuscar styles/watercolor 与 styles/papercut-red 的 STYLE.md（MIT，© 2026 LemoLab）——重写，无代码复制。
// ============================================================================
import React from 'react';
import {staticFile} from 'remotion';
import {noise2D} from '@remotion/noise';
import {THEME} from '../theme/active';
import {FibreOverlay, TapeStrip} from '../theme/craft-common';
import {prog} from './ink';

const C = THEME.palette;

/** 噪声扰动的闭合轮廓（圆 / 矩形边），返回 SVG path。 */
const noisyRing = (cx: number, cy: number, rx: number, ry: number, amp: number, seed: string, n = 72) => {
  const pts = Array.from({length: n}, (_, i) => {
    const a = (i / n) * Math.PI * 2;
    const k = 1 + amp * (noise2D(seed, Math.cos(a) * 1.3, Math.sin(a) * 1.3) * 0.7 + noise2D(seed + 'f', Math.cos(a) * 4, Math.sin(a) * 4) * 0.3);
    return [cx + rx * k * Math.cos(a), cy + ry * k * Math.sin(a)];
  });
  return 'M ' + pts.map((q) => q.map((v) => v.toFixed(1)).join(' ')).join(' L ') + ' Z';
};

/** 毛边矩形（手撕 / 毛边纸）的 clip-path polygon（百分比）。 */
const deckle = (seed: string, amp: number, n = 28) => {
  const side = (k: number, f: (t: number, j: number) => [number, number]) => Array.from({length: n}, (_, i) => f(i / n, noise2D(seed + k, i * 0.7, k) * amp));
  const pts = [
    ...side(0, (t, j) => [t * 100, Math.max(0, j)]),
    ...side(1, (t, j) => [100 - Math.max(0, j), t * 100]),
    ...side(2, (t, j) => [100 - t * 100, 100 - Math.max(0, j)]),
    ...side(3, (t, j) => [Math.max(0, j), 100 - t * 100]),
  ];
  return `polygon(${pts.map(([x, y]) => `${x.toFixed(2)}% ${y.toFixed(2)}%`).join(',')})`;
};

export type PaperSheetProps = {
  f: number; x: number; y: number; w: number; h: number;
  /** 入场帧：纸从上方 30px 处放下来，影子先大后小 */
  at?: number; rot?: number; color?: string;
  edge?: 'clean' | 'deckle' | 'torn';
  tape?: boolean; seed?: string; children?: React.ReactNode; style?: React.CSSProperties;
};

export const PaperSheet: React.FC<PaperSheetProps> = ({f, x, y, w, h, at = 0, rot = 0, color = C.paper, edge = 'deckle', tape = false, seed = 'sheet', children, style}) => {
  const p = prog(f, at, 12);
  if (p <= 0) return null;
  const lift = 1 - p;
  const clip = edge === 'clean' ? undefined : deckle(seed, edge === 'torn' ? 1.6 : 0.45, edge === 'torn' ? 40 : 28);
  return <div style={{position: 'absolute', left: x, top: y - 30 * lift, width: w, height: h, transform: `rotate(${rot + lift * 2}deg)`, opacity: Math.min(1, p * 2.5),
    filter: `drop-shadow(0 ${2 + 14 * lift}px ${4 + 18 * lift}px rgba(60,40,15,${0.22 - 0.06 * lift}))`, ...style}}>
    <div style={{position: 'absolute', inset: 0, background: color, clipPath: clip}}>
      <FibreOverlay opacity={THEME.craft?.fibre ?? 0.4} />
    </div>
    {tape && <TapeStrip x={w / 2 - 70} y={-14} w={140} rot={-3} />}
    <div style={{position: 'absolute', inset: 0}}>{children}</div>
  </div>;
};

export type WashBlobProps = {
  f: number; at: number; dur?: number;
  cx: number; cy: number; rx: number; ry?: number;
  color?: string; opacity?: number; seed?: string;
  /** 晕开的方向感：0 = 中心向外，1 = 从左往右扫 */
  sweep?: number;
};

/** 水彩淡彩：三遍半透明叠色（每遍轮廓略不同 → 边缘积色变深），外加颗粒纹理。 */
export const WashBlob: React.FC<WashBlobProps> = ({f, at, dur = 26, cx, cy, rx, ry = rx * 0.82, color = C.blue, opacity = 0.34, seed = 'wash', sweep = 0}) => {
  const p = prog(f, at, dur);
  if (p <= 0) return null;
  const grow = 0.25 + 0.75 * Math.sqrt(p);
  const W = rx * 2.6, H = ry * 2.6, ox = cx - W / 2, oy = cy - H / 2;
  const id = `wash-${seed}`;
  const passes = [0, 1, 2].map((k) => noisyRing(W / 2, H / 2, rx * grow * (1 - k * 0.05), ry * grow * (1 - k * 0.05), 0.16 + 0.03 * k, `${seed}${k}`));
  const sweepClip = sweep > 0 ? `inset(0 ${(1 - Math.min(1, p * 1.3)) * 100 * sweep}% 0 0)` : undefined;
  return <svg style={{position: 'absolute', left: ox, top: oy, overflow: 'visible', clipPath: sweepClip}} width={W} height={H} aria-hidden>
    <defs>
      <filter id={`${id}-soft`} x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation={1.4} /></filter>
      <pattern id={`${id}-gran`} width={512} height={512} patternUnits="userSpaceOnUse"><image href={staticFile('craft/granulation-tile.png')} width={512} height={512} /></pattern>
      <clipPath id={`${id}-clip`}><path d={passes[0]} /></clipPath>
    </defs>
    <g filter={`url(#${id}-soft)`}>
      {passes.map((d, k) => <path key={k} d={d} fill={color} opacity={opacity / 2.2} />)}
      {/* 积水深边：外轮廓描一道更浓的细边 */}
      <path d={passes[0]} fill="none" stroke={color} strokeWidth={3} opacity={opacity * 0.9} />
    </g>
    <rect width={W} height={H} fill={`url(#${id}-gran)`} clipPath={`url(#${id}-clip)`} opacity={0.5 * p} />
  </svg>;
};

export type CutPaperProps = {
  f: number; at?: number;
  /** 剪纸轮廓（设计坐标的 SVG path；evenodd：内部子路径就是剪掉的洞） */
  d: string; color?: string;
  /** 剪纸「双轮廓」：在边内侧再剪一道细缝（px，0 = 不剪） */
  inset?: number;
  /** 12 fps 跳帧入场（剪纸动画的手感）；false = 平滑 */
  stepped?: boolean;
  /** 背光：洞里透出暖光（「洞即是光」） */
  backlit?: number;
  /** 同一镜里有多片带 inset 的剪纸时给不同 id（SVG clipPath 需要唯一 id） */
  id?: string;
};

export const CutPaper: React.FC<CutPaperProps> = ({f, at = 0, d, color = THEME.craft?.accent ?? C.orange, inset = 0, stepped = true, backlit = 0, id: cid = 'cp'}) => {
  const ff = stepped ? Math.floor(f / 2.5) * 2.5 : f;
  const p = prog(ff, at, 8);
  if (p <= 0) return null;
  const pop = p < 1 ? 1.06 - 0.06 * p : 1;
  return <svg style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', transformOrigin: 'center', transform: `scale(${pop})`, opacity: Math.min(1, p * 3)}} width={1920} height={1080} aria-hidden>
    {backlit > 0 && <path d={d} fill="#ffd27a" opacity={backlit} filter="blur(18px)" />}
    {/* 纸厚：紧贴软影 + 右下切口暗边 */}
    <path d={d} fillRule="evenodd" fill="rgba(60,15,5,0.35)" transform="translate(2,4)" filter="blur(2.5px)" />
    <path d={d} fillRule="evenodd" fill={color} />
    <path d={d} fillRule="evenodd" fill="none" stroke="rgba(255,240,220,0.5)" strokeWidth={1.2} transform="translate(-0.8,-0.8)" />
    {inset > 0 && <>
      <defs><clipPath id={`cut-${cid}`}><path d={d} clipRule="evenodd" fillRule="evenodd" /></clipPath></defs>
      {/* 双轮廓：在边内 inset px 处剪一道 3px 细缝（先用纸色描 2×(inset+1.5) 宽，再用原色描 2×(inset−1.5) 宽，只保留形内） */}
      <g clipPath={`url(#cut-${cid})`}>
        <path d={d} fill="none" stroke={C.paperBase} strokeWidth={2 * (inset + 1.5)} strokeLinejoin="round" />
        <path d={d} fill="none" stroke={color} strokeWidth={2 * Math.max(0, inset - 1.5)} strokeLinejoin="round" />
      </g>
    </>}
  </svg>;
};

/** 一方红印（篆刻感的方章）：3 帧按下（1.35 → 1），印泥不匀用噪声遮罩。 */
export const Seal: React.FC<{f: number; at: number; x: number; y: number; size?: number; text: string; color?: string; rot?: number}> =
  ({f, at, x, y, size = 120, text, color = THEME.craft?.accent ?? C.orange, rot = -4}) => {
    if (f < at) return null;
    const t = Math.min(1, (f - at) / 3);
    const s = 1.35 - 0.35 * t;
    const chars = [...text].slice(0, 4);
    const fs = chars.length <= 1 ? size * 0.62 : chars.length === 2 ? size * 0.4 : size * 0.36;
    return <div style={{position: 'absolute', left: x, top: y, width: size, height: size, transform: `rotate(${rot}deg) scale(${s})`, opacity: 0.5 + 0.45 * t,
      border: `${Math.max(4, size / 20)}px solid ${color}`, borderRadius: size * 0.06, color, display: 'grid', placeItems: 'center',
      gridTemplateColumns: chars.length > 2 ? '1fr 1fr' : '1fr', fontFamily: 'Serif,Kai', fontWeight: 900, fontSize: fs, lineHeight: 1, padding: size * 0.08,
      maskImage: `radial-gradient(circle at 30% 70%, rgba(0,0,0,0.75), #000 60%)`}}>
      {chars.map((c, i) => <span key={i}>{c}</span>)}
    </div>;
  };
