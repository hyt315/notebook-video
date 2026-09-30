import React from 'react';
import {AbsoluteFill} from 'remotion';
import type {Theme} from './types';

// ============================================================================
// STICKER 主题：卡通贴纸·手账风（LOCKED）
// 设计语言：白边贴纸、和纸胶带、马克笔高亮、糖果色与安静薄荷色底。
// 色彩系统：粉色为主角色，蓝/绿按粉彩同阶梯推导（高明度低刺激），不许跳出档位。
// 移除跨越开放流程留白的网格/角落涂鸦位图；贴纸语汇由卡片、胶带和标注承担。
// ============================================================================

const palette: Theme['palette'] = {
  ink: '#4a3b2f',
  muted: '#9a8a76',
  blue: '#5ca9e0',
  // 文字安全色：同色相压暗，过 4.5 比 1（从 WCAG 反解出来的）。
  // 约定：原色只用于填充与描边；当文字色一律用对应的 Ink 变体（presentation-gate 会查）。
  blueInk: '#40759c',
  blueLight: 'rgba(92,169,224,0.30)',
  orange: '#ff8fa3',
  // 文字安全色：同色相压暗，过 4.5 比 1（从 WCAG 反解出来的）。
  // 约定：原色只用于填充与描边；当文字色一律用对应的 Ink 变体（presentation-gate 会查）。
  orangeInk: '#a25b68',
  orangeLight: 'rgba(255,143,163,0.28)',
  green: '#61d188',
  // 文字安全色：同色相压暗，过 4.5 比 1（从 WCAG 反解出来的）。
  // 约定：原色只用于填充与描边；当文字色一律用对应的 Ink 变体（presentation-gate 会查）。
  greenInk: '#3a7d52',
  greenLight: 'rgba(97,209,136,0.30)',
  gold: '#ffd166',
  // 文字安全色：同色相压暗，过 4.5 比 1（从 WCAG 反解出来的）。
  // 约定：原色只用于填充与描边；当文字色一律用对应的 Ink 变体（presentation-gate 会查）。
  goldInk: '#856d35',
  red: '#e85d5d',
  // 文字安全色：同色相压暗，过 4.5 比 1（从 WCAG 反解出来的）。
  // 约定：原色只用于填充与描边；当文字色一律用对应的 Ink 变体（presentation-gate 会查）。
  redInk: '#bc4b4b',
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
  // 头部两色**当文字用**（index.tsx 的章节技术头部就压在这两个色上），
  // 所以它们和 5 个 *Ink 一样必须过 4.5:1 —— 原来 headerAccent 直接等于 blue、
  // headerSub 等于 muted，实测 2.40 / 3.14（on paperBase），门禁判 P1。
  // 处置同 *Ink：**同色相按 WCAG 反解压暗**（headerAccent = blue→blueInk 的同一个值，
  // headerSub = muted 压暗一档），原值不再当文字色用。
  headerAccent: '#40759c',
  headerSub: '#7b6f5f',
};

const aesthetic: Theme['aesthetic'] = {
  subtitleSafeWidth: 1334, paperRadius: 22, paperOutline: 0,
  textureOpacity: 0, gridOpacity: 0, gradeWarmth: 0, gradeVignette: .04,
  subtitleWeight: 700, subtitleLetterSpacing: 1.6, subtitlePadX: 72,
};

// 贴纸影：柔和双层扩散影（加深版，保证白边卡在浅底上可辨识），白边由 Paper 的 outline 承担。
const paperShadow = (lift: number) =>
  `0 ${4 + 4 * lift}px 0 rgba(74,59,47,${0.12 + 0.05 * lift}),0 ${10 + 12 * lift}px ${22 + 16 * lift}px rgba(74,59,47,${0.17 + 0.07 * lift})`;

// 安静的浅薄荷色底；避免网格纹理与流程线/状态点在手机尺寸争夺注意力。
const Background: React.FC = () => <AbsoluteFill style={{background: palette.paperBase}} />;

// 背景保持纯色，无画幅级装饰，因此无需按画布声明遮挡区。
const backgroundDecorZones: Theme['backgroundDecorZones'] = [];

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
  backgroundDecorZones,
  extras: {Tape},
};
