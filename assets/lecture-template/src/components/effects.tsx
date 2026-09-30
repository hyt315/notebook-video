import React from 'react';
import {noise2D} from '@remotion/noise';
import {interpolate} from 'remotion';
import {THEME} from '../theme/active';
import {TYPE} from '../kit';
import {prog} from './ui';
import {fitsWithin} from './fittext';

// ============================================================================
// effects.tsx — 零依赖的「炫效果」
//
// 社区组件库里最抓眼的效果，八成不需要任何依赖——底层只是 CSS/SVG 数学。
// 本层把这些效果配方做成帧驱动的组件，皮肤仍归 THEME 管。
// 纪律：一律 f(帧号) 的纯函数，禁 animation/transition/setTimeout。
// ============================================================================

const C = THEME.palette;
const RADIUS = THEME.aesthetic.paperRadius;

/**
 * GlowFrame — 流光边框。
 * 用 conic-gradient 的起始角绑帧号，边框像光在绕行。子内容放在内层不透明卡片里。
 */
export const GlowFrame: React.FC<{
  f: number;
  durationInFrames?: number;
  width?: number | string;
  height?: number | string;
  thickness?: number;
  tone?: string;
  children?: React.ReactNode;
}> = ({f, durationInFrames = 300, width, height, thickness = 8, tone, children}) => {
  const spin = interpolate(f, [0, durationInFrames], [0, 360]);
  const a = tone ?? C.blue;
  return (
    <div
      style={{
        width,
        height,
        padding: thickness,
        borderRadius: RADIUS + thickness,
        background: `conic-gradient(from ${spin}deg, ${a}, ${C.gold}, ${C.orange}, ${C.green}, ${a})`,
        boxShadow: THEME.paperShadow(0.6),
      }}
    >
      <div
        style={{
          height: '100%',
          width: '100%',
          borderRadius: RADIUS,
          background: C.paper,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
        }}
      >
        {children}
      </div>
    </div>
  );
};

/**
 * ShimmerText — 文字闪过一道光。
 * background-clip:text + 移动的渐变遮罩，位置绑帧号。
 */
export const ShimmerText: React.FC<{
  f: number;
  text: string;
  fontSize?: number;
  periodInFrames?: number;
  sweep?: string;
}> = ({f, text, fontSize = TYPE.displayM, periodInFrames = 90, sweep}) => {
  const pos = interpolate(f % periodInFrames, [0, periodInFrames], [-40, 140]);
  return (
    <span
      style={{
        fontFamily: 'Kai,sans-serif',
        fontSize,
        fontWeight: 700,
        backgroundImage: `linear-gradient(100deg, ${C.ink} 35%, ${sweep ?? C.gold} 50%, ${C.ink} 65%)`,
        backgroundSize: '260% 100%',
        backgroundPosition: `${pos}% 0`,
        WebkitBackgroundClip: 'text',
        backgroundClip: 'text',
        color: 'transparent',
      }}
    >
      {text}
    </span>
  );
};

/**
 * RevealMask — 遮罩擦除。
 * clip-path: inset() 按帧推进，用于「逐条揭示」而不只是「淡入」。
 */
export const ClipReveal: React.FC<{
  f: number;
  from: number;
  durationInFrames?: number;
  direction?: 'left' | 'right' | 'up' | 'down';
  children?: React.ReactNode;
  style?: React.CSSProperties;
}> = ({f, from, durationInFrames = 34, direction = 'left', children, style}) => {
  const p = prog(f, from, durationInFrames);
  const rest = (1 - p) * 100;
  const clip =
    direction === 'left'
      ? `inset(0 ${rest}% 0 0)`
      : direction === 'right'
        ? `inset(0 0 0 ${rest}%)`
        : direction === 'up'
          ? `inset(0 0 ${rest}% 0)`
          : `inset(${rest}% 0 0 0)`;
  return <div style={{clipPath: clip, ...style}}>{children}</div>;
};

/**
 * NoiseJitter — 有机抖动。
 * noise2D 给同一 seed 得到同一结果，所以「随机感」不会破坏可复现性。
 * 适合手绘元素、贴纸、需要"活一点"的静止物。
 */
export const NoiseJitter: React.FC<{
  f: number;
  seed?: string;
  amplitude?: number;
  speed?: number;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}> = ({f, seed = 'jitter', amplitude = 10, speed = 0.02, children, style}) => {
  const dx = noise2D(`${seed}-x`, f * speed, 0) * amplitude;
  const dy = noise2D(`${seed}-y`, 0, f * speed) * amplitude;
  const rot = noise2D(`${seed}-r`, f * speed, 1) * (amplitude * 0.12);
  return <div style={{transform: `translate(${dx}px, ${dy}px) rotate(${rot}deg)`, ...style}}>{children}</div>;
};

/**
 * VerdictBar — 全宽结论条。
 * 每个场景用它收束并填满底部（内容底边 y=1168 的版式契约）。
 */
export const VerdictBar: React.FC<{f: number; delay: number; text: string; tag: string; tone: string; width: number}> = ({
  f,
  delay,
  text,
  tag,
  tone,
  width,
}) => {
  const p = prog(f, delay, 24);
  // 全宽条同样：文案长度可变，开发期实测自检
  if (process.env.NODE_ENV !== 'production') {
    fitsWithin({text, boxWidth: width - 80 - 120, fontSize: TYPE.titleXS, label: 'VerdictBar'});
  }
  return (
    <div
      style={{
        width,
        opacity: p,
        transform: `translateY(${(1 - p) * 26}px)`,
        background: C.ink,
        borderRadius: RADIUS,
        boxShadow: THEME.paperShadow(0.9),
        padding: '26px 40px',
        display: 'flex',
        alignItems: 'center',
        gap: 26,
      }}
    >
      <span
        style={{
          flex: '0 0 auto',
          fontFamily: 'Space,Kai,monospace',
          fontSize: TYPE.microL,
          fontWeight: 700,
          color: C.ink,
          background: tone,
          borderRadius: 6,
          padding: '6px 16px',
        }}
      >
        {tag}
      </span>
      <span style={{fontFamily: 'Kai,sans-serif', fontSize: TYPE.titleXS, color: C.white, lineHeight: 1.5}}>{text}</span>
    </div>
  );
};
