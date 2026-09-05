import React from 'react';
import {AbsoluteFill} from 'remotion';
import {useCanvas} from './canvas';
import type {Theme} from './types';

// ============================================================================
// STICKER 主题：卡通贴纸·手账风（LOCKED）
// 设计语言：白边贴纸、和纸胶带、马克笔高亮、手绘涂鸦、糖果色。
// 色彩系统：粉色为主角色，蓝/绿按粉彩同阶梯推导（高明度低刺激），不许跳出档位。
// 本文件所有数值均为锁定值，制作时整体引用，不得调参。
// ============================================================================

const palette: Theme['palette'] = {
  ink: '#4a3b2f',
  muted: '#9a8a76',
  blue: '#5ca9e0',
  blueLight: 'rgba(92,169,224,0.30)',
  orange: '#ff8fa3',
  orangeLight: 'rgba(255,143,163,0.28)',
  green: '#61d188',
  greenLight: 'rgba(97,209,136,0.30)',
  gold: '#ffd166',
  red: '#e85d5d',
  navy: '#4a3b2f',
  paper: '#ffffff',
  paperWarm: '#f4f9f4',
  paperBase: '#f4f9f4',
  line: 'rgba(74,59,47,0.42)',
  lineOrange: 'rgba(255,143,163,0.62)',
  lineBlue: 'rgba(92,169,224,0.62)',
  lineGreen: 'rgba(97,209,136,0.62)',
  white: '#ffffff',
  // 场景层柔色
  skyTint: '#e8f4fb',
  blueLine: 'rgba(92,169,224,0.40)',
  dotIdle: '#d8ccb6',
  mutedFill: 'rgba(154,138,118,0.32)',
  mutedBar: 'rgba(154,138,118,0.30)',
  mutedWash: 'rgba(154,138,118,0.20)',
  orangeSoft: '#ffb3c0',
  orangeDeep: '#f2798f',
  gaugeTrack: 'rgba(74,59,47,0.22)',
  greenGlow: 'rgba(97,209,136,0.32)',
  stageTint: 'rgba(244,249,244,0.5)',
  headerAccent: '#5ca9e0',
  headerSub: '#9a8a76',
};

const aesthetic: Theme['aesthetic'] = {
  subtitleSafeWidth: 1334, paperRadius: 22, paperOutline: 0,
  textureOpacity: 0, gridOpacity: .10, gradeWarmth: 0, gradeVignette: .04,
};

// 贴纸影：柔和双层扩散影（加深版，保证白边卡在浅底上可辨识），白边由 Paper 的 outline 承担。
const paperShadow = (lift: number) =>
  `0 ${4 + 4 * lift}px 0 rgba(74,59,47,${0.12 + 0.05 * lift}),0 ${10 + 12 * lift}px ${22 + 16 * lift}px rgba(74,59,47,${0.17 + 0.07 * lift})`;

// ---- 手绘涂鸦（按画布比例锁定锚点，形状比例不随画布拉伸） ----------------
const doodle = {
  heart: (cx: number, cy: number, s: number) =>
    `M${cx} ${cy + s * 0.32} C${cx - s} ${cy - s * 0.5} ${cx - s * 0.34} ${cy - s * 1.04} ${cx} ${cy - s * 0.36} C${cx + s * 0.34} ${cy - s * 1.04} ${cx + s} ${cy - s * 0.5} ${cx} ${cy + s * 0.32} Z`,
  cross: (cx: number, cy: number, s: number) =>
    `M${cx - s / 2} ${cy - s / 2} l${s} ${s} M${cx + s / 2} ${cy - s / 2} l${-s} ${s}`,
  wave: (x: number, y: number, w: number) =>
    `M${x} ${y} q${w * 0.25} ${-w * 0.28} ${w * 0.5} 0 t${w * 0.5} 0`,
  spiral: (cx: number, cy: number, s: number) =>
    `M${cx} ${cy} c${s * 0.5} ${-s * 0.2} ${s * 0.85} ${s * 0.25} ${s * 0.5} ${s * 0.6} c${-s * 0.35} ${s * 0.3} ${-s * 0.85} ${-s * 0.05} ${-s * 0.5} ${-s * 0.6}`,
  zig: (x: number, y: number, w: number) =>
    `M${x} ${y} q${w * 0.16} ${-w * 0.32} ${w * 0.33} 0 q${w * 0.16} ${w * 0.32} ${w * 0.33} 0`,
};

const Background: React.FC = () => {
  const {mode} = useCanvas();
  const dw = mode.designW, dh = mode.designH;
  return <>
    <AbsoluteFill style={{background: palette.paperBase}} />
    <AbsoluteFill style={{backgroundImage: `repeating-linear-gradient(0deg,transparent 0 41px,rgba(120,95,70,${aesthetic.gridOpacity}) 42px),repeating-linear-gradient(90deg,transparent 0 41px,rgba(120,95,70,${aesthetic.gridOpacity}) 42px)`}} />
    <svg width={dw} height={dh} style={{position: 'absolute', inset: 0}} fill="none" strokeLinecap="round">
      <path d={doodle.heart(dw * 0.90, dh * 0.17, 30)} stroke={palette.orange} strokeWidth={5} />
      <path d={doodle.cross(dw * 0.855, dh * 0.25, 26)} stroke={palette.blue} strokeWidth={5} />
      <path d={doodle.wave(dw * 0.06, dh * 0.865, 120)} stroke={palette.green} strokeWidth={5} />
      <path d={doodle.spiral(dw * 0.928, dh * 0.815, 44)} stroke={palette.gold} strokeWidth={5} />
      <path d={doodle.zig(dw * 0.13, dh * 0.148, 60)} stroke={palette.gold} strokeWidth={5} />
    </svg>
  </>;
};

// 白边贴纸卡：内圈细墨线（贴纸印刷边）+ 外圈白边（模切边）+ 加深软影，三层保证边界可见。
const Paper: Theme['Paper'] = ({children, style, lift = 0}) =>
  <div style={{position: 'absolute', backgroundColor: palette.paper, borderRadius: aesthetic.paperRadius, border: '2.5px solid rgba(74,59,47,0.55)', outline: '5px solid #ffffff', color: palette.ink, boxShadow: paperShadow(lift), ...style}}>{children}</div>;

const Grade: React.FC = () => <AbsoluteFill style={{pointerEvents: 'none', zIndex: 190}}>
  <AbsoluteFill style={{boxShadow: `inset 0 0 130px rgba(74,59,47,${aesthetic.gradeVignette})`}} />
</AbsoluteFill>;

// 和纸胶带（锁定构件）：斜纹 + 撕边 clip-path，场景层只给 x/y/宽/角度/色。
export const Tape: React.FC<{x: number; y: number; w?: number; rot?: number; color?: string}> =
  ({x, y, w = 150, rot = -4, color = 'rgba(255,209,102,.75)'}) => (
    <div style={{
      position: 'absolute', left: x, top: y, width: w, height: 38, background: color,
      transform: `rotate(${rot}deg)`, opacity: 0.9, zIndex: 5,
      clipPath: 'polygon(2% 0,98% 6%,100% 94%,0 100%)',
      backgroundImage: 'repeating-linear-gradient(45deg,rgba(255,255,255,.35) 0 8px,transparent 8px 16px)',
    }} />
  );

const SubtitleChrome: Theme['SubtitleChrome'] = ({mode, children}) =>
  <div style={{position: 'absolute', left: 0, right: 0, bottom: 42, zIndex: 200, display: 'flex', justifyContent: 'center'}}>
    <div style={{position: 'relative'}}>
      <Tape x={-50} y={-20} w={130} rot={-8} color="rgba(92,169,224,.75)" />
      <div style={{background: palette.white, borderRadius: 18, padding: '14px 36px', boxShadow: '0 8px 22px rgba(74,59,47,.18)', maxWidth: mode.safe}}>
        <div style={{fontFamily: 'Kai', fontSize: mode.subFont, fontWeight: 700, lineHeight: 1.18, letterSpacing: 1.6, color: palette.ink, whiteSpace: 'nowrap'}}>
          {children}
        </div>
      </div>
    </div>
  </div>;

export const THEME: Theme = {
  id: 'sticker',
  palette,
  aesthetic,
  paperShadow,
  Background,
  Paper,
  Grade,
  SubtitleChrome,
  extras: {Tape},
};
