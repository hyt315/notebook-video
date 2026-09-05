import React from 'react';
import {AbsoluteFill} from 'remotion';
import {useCanvas} from './canvas';
import type {Theme} from './types';

// ============================================================================
// FLAT 主题：现代扁平·几何插画风（LOCKED）
// 设计语言：大色块、粗描边卡片、偏移实色影、孟菲斯点缀、实心底字幕条。
// 本文件所有数值均为锁定值，制作时整体引用，不得调参。
// ============================================================================

const palette: Theme['palette'] = {
  ink: '#191919',
  muted: '#6f6a63',
  blue: '#3b4ed8',
  blueLight: 'rgba(59,78,216,0.10)',
  orange: '#ff5d3b',
  orangeLight: 'rgba(255,93,59,0.10)',
  green: '#37c99b',
  greenLight: 'rgba(55,201,155,0.12)',
  gold: '#ffcf3f',
  red: '#e8382a',
  navy: '#191919',
  paper: '#ffffff',
  paperWarm: '#f2f4f7',
  paperBase: '#f2f4f7',
  line: 'rgba(25,25,25,0.16)',
  lineOrange: 'rgba(255,93,59,0.35)',
  lineBlue: 'rgba(59,78,216,0.35)',
  lineGreen: 'rgba(55,201,155,0.35)',
  white: '#ffffff',
  // 场景层柔色
  skyTint: '#e8ebfb',
  blueLine: 'rgba(59,78,216,0.40)',
  dotIdle: '#d9d4cb',
  mutedFill: 'rgba(111,106,99,0.22)',
  mutedBar: 'rgba(111,106,99,0.20)',
  mutedWash: 'rgba(111,106,99,0.12)',
  orangeSoft: '#ff8d70',
  orangeDeep: '#e04e2f',
  gaugeTrack: 'rgba(25,25,25,0.14)',
  greenGlow: 'rgba(55,201,155,0.35)',
  stageTint: 'rgba(242,244,247,0.5)',
  headerAccent: '#ffffff',
  headerSub: 'rgba(255,255,255,0.78)',
};

const aesthetic: Theme['aesthetic'] = {
  subtitleSafeWidth: 1334, paperRadius: 20, paperOutline: 3.5,
  textureOpacity: 0, gridOpacity: 0, gradeWarmth: 0, gradeVignette: 0,
};

// 偏移实色影：无模糊，固定 8px 墨色偏移，lift 只轻微加长（几何感不悬浮）。
const paperShadow = (lift: number) =>
  `${7 + 3 * lift}px ${7 + 3 * lift}px 0 rgba(25,25,25,0.9)`;

const Background: React.FC = () => {
  const {mode} = useCanvas();
  const dw = mode.designW, dh = mode.designH;
  return <>
    <AbsoluteFill style={{background: palette.paperBase}} />
    {/* 右上大圆色块：压出画面右缘，占右侧约 42%（demo 同款体量） */}
    <div style={{position: 'absolute', left: dw * 0.583, top: -dh * 0.13, width: dw * 0.51, height: dw * 0.51, borderRadius: '50%', background: palette.blue, opacity: 0.96}} />
    {/* 黄色圆角方块：卡片下方与字幕条上沿之间 */}
    <div style={{position: 'absolute', left: dw * 0.583, top: dh * 0.732, width: dw * 0.104, height: dw * 0.104, borderRadius: dw * 0.025, background: palette.gold, transform: 'rotate(14deg)'}} />
    {/* 孟菲斯点缀：按画布比例锁定锚点 */}
    <svg width={dw} height={dh} style={{position: 'absolute', inset: 0}} fill="none">
      <circle cx={dw * 0.125} cy={dh * 0.815} r={46} stroke={palette.orange} strokeWidth={10} />
      <path d={`M${dw * 0.853} ${dh * 0.089} l60 0 M${dw * 0.883} ${dh * 0.059} l0 60`} stroke={palette.gold} strokeWidth={12} strokeLinecap="round" />
      <path d={`M${dw * 0.063} ${dh * 0.278} q30 -40 60 0 t60 0`} stroke={palette.blue} strokeWidth={9} strokeLinecap="round" />
      {Array.from({length: 5}).map((_, r) => Array.from({length: 6}).map((_, c) =>
        <circle key={`${r}-${c}`} cx={dw * 0.056 + c * 26} cy={dh * 0.52 + r * 26} r={4.5} fill={palette.ink} opacity={0.35} />))}
    </svg>
  </>;
};

const Paper: Theme['Paper'] = ({children, style, lift = 0, borderColor}) =>
  <div style={{position: 'absolute', backgroundColor: palette.paper, border: `${aesthetic.paperOutline}px solid ${borderColor || palette.ink}`, borderRadius: aesthetic.paperRadius, color: palette.ink, boxShadow: paperShadow(lift), ...style}}>{children}</div>;

// 扁平风不加任何调色层：纯色块对比即为视觉语言。
const Grade: React.FC = () => null;

const SubtitleChrome: Theme['SubtitleChrome'] = ({mode, children}) =>
  <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 128, background: palette.ink, zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
    <div style={{width: 10, height: 44, background: palette.orange, borderRadius: 6, marginRight: 26}} />
    <div style={{fontFamily: 'Kai', fontSize: mode.subFont, fontWeight: 700, lineHeight: 1.18, letterSpacing: 1.6, color: palette.white, whiteSpace: 'nowrap'}}>
      {children}
    </div>
  </div>;

export const THEME: Theme = {
  id: 'flat',
  palette,
  aesthetic,
  paperShadow,
  Background,
  Paper,
  Grade,
  SubtitleChrome,
};
