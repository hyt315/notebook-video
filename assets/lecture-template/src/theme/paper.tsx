import React from 'react';
import {AbsoluteFill} from 'remotion';
import type {Theme} from './types';

// ============================================================================
// PAPER 主题（默认）：暖米纸笔记本 —— 原 v9 锁定美学核原样搬迁，一个值都不许动。
// 任何修改必须让默认主题渲染结果与搬迁前逐像素一致。
// ============================================================================

const palette: Theme['palette'] = {
  ink: '#1a1918',
  muted: '#766e65',
  blue: '#2563eb',
  blueLight: 'rgba(37,99,235,0.08)',
  orange: '#d95a34',
  orangeLight: 'rgba(217,90,52,0.08)',
  green: '#16a34a',
  greenLight: 'rgba(22,163,74,0.08)',
  gold: '#d97706',
  red: '#dc2626',
  navy: '#1e293b',
  paper: '#ffffff',
  paperWarm: '#faf5ee',
  paperBase: '#faf7f2',
  line: 'rgba(60,50,40,0.11)',
  lineOrange: 'rgba(217,90,52,0.25)',
  lineBlue: 'rgba(37,99,235,0.25)',
  lineGreen: 'rgba(22,163,74,0.25)',
  white: '#ffffff',
};

const aesthetic: Theme['aesthetic'] = {
  subtitleSafeWidth: 1334, paperRadius: 16, paperOutline: 1.0,
  textureOpacity: .012, gridOpacity: .035, gradeWarmth: .022, gradeVignette: .035,
};

const paperShadow = (lift: number) =>
  `0 2px 6px rgba(40,32,24,${0.04 + 0.04 * lift}),0 ${8 + 12 * lift}px ${20 + 24 * lift}px rgba(40,32,24,${0.05 + 0.06 * lift}),inset 0 1px 0 rgba(255,255,255,0.9)`;

const Background: React.FC = () => <>
  <AbsoluteFill style={{background: palette.paperBase}} />
  <div style={{position: 'absolute', left: 60, top: 50, right: 60, bottom: 50, backgroundImage: `repeating-linear-gradient(0deg,transparent 0 53px,rgba(90,75,60,${aesthetic.gridOpacity}) 54px),repeating-linear-gradient(90deg,transparent 0 53px,rgba(90,75,60,${aesthetic.gridOpacity}) 54px),radial-gradient(circle at 20% 10%,rgba(255,255,255,0.7),transparent 45%),radial-gradient(circle at 80% 85%,rgba(217,90,52,0.04),transparent 50%)`}} />
  <AbsoluteFill style={{opacity: aesthetic.textureOpacity, mixBlendMode: 'multiply', backgroundImage: 'radial-gradient(#30251a 0.5px,transparent .7px)', backgroundSize: '8px 8px'}} />
</>;

const Paper: Theme['Paper'] = ({children, style, lift = 0, borderColor}) =>
  <div style={{position: 'absolute', backgroundColor: palette.paper, backgroundImage: 'radial-gradient(circle at 18% 9%,rgba(255,255,255,0.9),transparent 36%),linear-gradient(175deg,#ffffff 0%,#fdfbf8 100%)', border: `${aesthetic.paperOutline}px solid ${borderColor || palette.line}`, borderRadius: aesthetic.paperRadius, color: palette.ink, boxShadow: paperShadow(lift), ...style}}>{children}</div>;

const Grade: React.FC = () => <AbsoluteFill style={{pointerEvents: 'none', zIndex: 190}}>
  <AbsoluteFill style={{opacity: aesthetic.gradeWarmth, mixBlendMode: 'soft-light', background: 'radial-gradient(circle at 24% 8%,rgba(255,249,224,.9),transparent 48%),linear-gradient(180deg,rgba(255,244,216,.14),rgba(84,55,28,.08))'}} />
  <AbsoluteFill style={{boxShadow: `inset 0 0 150px rgba(66,42,22,${aesthetic.gradeVignette})`}} />
</AbsoluteFill>;

const SubtitleChrome: Theme['SubtitleChrome'] = ({mode, children}) =>
  <div style={{position: 'absolute', left: mode.subMar, right: mode.subMar, bottom: 20, zIndex: 200, display: 'grid', placeItems: 'center'}}>
    <div style={{width: mode.safe, display: 'grid', placeItems: 'center', fontFamily: 'Kai', fontSize: mode.subFont, lineHeight: 1.18, letterSpacing: 1.6, color: palette.ink, textShadow: '0 1px 4px rgba(255,255,255,0.8), 0 2px 10px rgba(40,30,20,0.15)', whiteSpace: 'nowrap'}}>
      {children}
    </div>
  </div>;

export const THEME: Theme = {
  id: 'paper',
  palette,
  aesthetic,
  paperShadow,
  Background,
  Paper,
  Grade,
  SubtitleChrome,
};
