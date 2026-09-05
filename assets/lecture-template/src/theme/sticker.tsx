import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
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

// 背景（LOCKED）：固定资产图，每比例一张（2560×1440 / 1920×1440 / 1440×1920），
// 像素与画布一一对应；含薄荷网格纸、四角涂鸦、和纸胶带。禁止改回代码自绘背景。
const BG_BY_MODE = {'16:9': 'bg-sticker-169.jpg', '4:3': 'bg-sticker-43.jpg', '3:4': 'bg-sticker-34.jpg'} as const;

const Background: React.FC = () => {
  const {canvas} = useCanvas();
  return <AbsoluteFill style={{background: palette.paperBase}}>
    <Img src={staticFile(BG_BY_MODE[canvas])} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
  </AbsoluteFill>;
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
