import React from 'react';
import {AbsoluteFill} from 'remotion';
import {useCanvas} from './canvas';
import type {Theme} from './types';

// ============================================================================
// FLAT 主题：现代扁平·几何小怪兽插画风（LOCKED）
// 设计语言：灰细边白卡 + 彩色硬偏移影、几何小怪兽背景、悬浮圆角彩条字幕。
// 色彩系统：靛蓝为主角色，珊瑚/薄荷/金黄按同档饱和度≈65-85 明度≈54-62 推导。
// 本文件所有数值均为锁定值，制作时整体引用，不得调参。
// ============================================================================

const palette: Theme['palette'] = {
  ink: '#191919',
  muted: '#6f6a63',
  blue: '#3b4ed8',
  blueLight: 'rgba(59,78,216,0.17)',
  orange: '#f05f42',
  orangeLight: 'rgba(240,95,66,0.17)',
  green: '#41d27b',
  greenLight: 'rgba(65,210,123,0.19)',
  gold: '#f0c63c',
  red: '#e8382a',
  navy: '#191919',
  paper: '#ffffff',
  paperWarm: '#f2f4f7',
  paperBase: '#f2f4f7',
  line: 'rgba(25,25,25,0.45)',
  lineOrange: 'rgba(240,95,66,0.62)',
  lineBlue: 'rgba(59,78,216,0.62)',
  lineGreen: 'rgba(65,210,123,0.62)',
  white: '#ffffff',
  // 场景层柔色
  skyTint: '#e8ebfb',
  blueLine: 'rgba(59,78,216,0.40)',
  dotIdle: '#cfc8bc',
  mutedFill: 'rgba(111,106,99,0.30)',
  mutedBar: 'rgba(111,106,99,0.28)',
  mutedWash: 'rgba(111,106,99,0.18)',
  orangeSoft: '#f59784',
  orangeDeep: '#d63d1f',
  gaugeTrack: 'rgba(25,25,25,0.22)',
  greenGlow: 'rgba(65,210,123,0.35)',
  stageTint: 'rgba(242,244,247,0.5)',
  headerAccent: '#191919',
  headerSub: '#6f6a63',
};

const aesthetic: Theme['aesthetic'] = {
  subtitleSafeWidth: 1334, paperRadius: 20, paperOutline: 0,
  textureOpacity: 0, gridOpacity: 0, gradeWarmth: 0, gradeVignette: 0,
};

// 偏移实色影：无模糊、无墨边，主题蓝实色偏移（几何感不悬浮）。
// 场景层直接调用时用默认蓝；Paper 卡片按 borderColor 换对应彩色影。
const paperShadow = (lift: number) =>
  `${7 + 3 * lift}px ${7 + 3 * lift}px 0 ${palette.blue}`;

// ---- 几何小怪兽（锁定构件，按画布比例锚点，纯色平涂 + 墨点眼睛，禁止渐变） ----------
// 四角星路径：s 为外半径
const star4 = (cx: number, cy: number, s: number) => {
  const k = 0.24;
  const pts = [[0, -1], [k, -k], [1, 0], [k, k], [0, 1], [-k, k], [-1, 0], [-k, -k]];
  return pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${cx + x * s} ${cy + y * s}`).join(' ') + ' Z';
};

const Background: React.FC = () => {
  const {mode} = useCanvas();
  const dw = mode.designW, dh = mode.designH;
  const br = dw * 0.052; // 圆球怪半径
  const bs = dw * 0.058; // 方块怪边长
  return <>
    <AbsoluteFill style={{background: palette.paperBase}} />
    <svg width={dw} height={dh} style={{position: 'absolute', inset: 0}}>
      {/* 圆球小怪兽：右下角探头（靛蓝身体、呆毛、圆眼、微笑、小短腿），让出右上章节头 */}
      <g transform={`translate(${dw * 0.930}, ${dh * 0.860})`}>
        <line x1={0} y1={-br * 0.95} x2={0} y2={-br * 1.35} stroke={palette.blue} strokeWidth={br * 0.09} strokeLinecap="round" />
        <circle cy={-br * 1.45} r={br * 0.16} fill={palette.gold} />
        <circle r={br} fill={palette.blue} />
        <circle cx={-br * 0.36} cy={-br * 0.16} r={br * 0.26} fill="#fff" />
        <circle cx={br * 0.36} cy={-br * 0.16} r={br * 0.26} fill="#fff" />
        <circle cx={-br * 0.30} cy={-br * 0.10} r={br * 0.11} fill={palette.ink} />
        <circle cx={br * 0.30} cy={-br * 0.10} r={br * 0.11} fill={palette.ink} />
        <path d={`M${-br * 0.26} ${br * 0.34} Q0 ${br * 0.58} ${br * 0.26} ${br * 0.34}`} stroke={palette.ink} strokeWidth={br * 0.07} fill="none" strokeLinecap="round" />
        <rect x={-br * 0.44} y={br * 0.92} width={br * 0.20} height={br * 0.42} rx={br * 0.10} fill={palette.blue} />
        <rect x={br * 0.24} y={br * 0.92} width={br * 0.20} height={br * 0.42} rx={br * 0.10} fill={palette.blue} />
      </g>
      {/* 方块小怪兽：左下角歪头（珊瑚身体、圆眼、锯齿嘴、举小手） */}
      <g transform={`translate(${dw * 0.075}, ${dh * 0.845}) rotate(-8)`}>
        <line x1={-bs * 0.62} y1={-bs * 0.10} x2={-bs * 0.92} y2={-bs * 0.42} stroke={palette.orange} strokeWidth={bs * 0.09} strokeLinecap="round" />
        <line x1={bs * 0.62} y1={-bs * 0.10} x2={bs * 0.92} y2={-bs * 0.42} stroke={palette.orange} strokeWidth={bs * 0.09} strokeLinecap="round" />
        <rect x={-bs / 2} y={-bs / 2} width={bs} height={bs} rx={bs * 0.18} fill={palette.orange} />
        <circle cx={-bs * 0.18} cy={-bs * 0.12} r={bs * 0.15} fill="#fff" />
        <circle cx={bs * 0.18} cy={-bs * 0.12} r={bs * 0.15} fill="#fff" />
        <circle cx={-bs * 0.14} cy={-bs * 0.09} r={bs * 0.065} fill={palette.ink} />
        <circle cx={bs * 0.22} cy={-bs * 0.09} r={bs * 0.065} fill={palette.ink} />
        <path d={`M${-bs * 0.20} ${bs * 0.22} l${bs * 0.10} ${bs * 0.10} l${bs * 0.10} ${-bs * 0.10} l${bs * 0.10} ${bs * 0.10} l${bs * 0.10} ${-bs * 0.10}`} stroke={palette.ink} strokeWidth={bs * 0.05} fill="none" strokeLinecap="round" strokeLinejoin="round" />
        <rect x={-bs * 0.34} y={bs * 0.50} width={bs * 0.16} height={bs * 0.26} rx={bs * 0.08} fill={palette.orange} />
        <rect x={bs * 0.18} y={bs * 0.50} width={bs * 0.16} height={bs * 0.26} rx={bs * 0.08} fill={palette.orange} />
      </g>
      {/* 搞怪小元素：四角星、感叹号、波浪线 */}
      <path d={star4(dw * 0.185, dh * 0.140, dw * 0.020)} fill={palette.gold} />
      <path d={star4(dw * 0.790, dh * 0.620, dw * 0.013)} fill={palette.orange} />
      <g transform={`translate(${dw * 0.945}, ${dh * 0.480}) rotate(10)`}>
        <rect x={-dw * 0.007} y={-dw * 0.030} width={dw * 0.014} height={dw * 0.042} rx={dw * 0.007} fill={palette.green} />
        <circle cy={dw * 0.026} r={dw * 0.009} fill={palette.green} />
      </g>
      <path d={`M${dw * 0.045} ${dh * 0.340} q${dw * 0.016} ${-dw * 0.021} ${dw * 0.031} 0 t${dw * 0.031} 0`} stroke={palette.blue} strokeWidth={dw * 0.005} fill="none" strokeLinecap="round" />
    </svg>
  </>;
};

// 无框色影卡：白卡 + 2px 中性灰细边（界定上/左缘，非墨框）+ 实色硬偏移影（界定右下缘）；
// 场景传 borderColor 时影子同步变色。
const Paper: Theme['Paper'] = ({children, style, lift = 0, borderColor}) =>
  <div style={{position: 'absolute', backgroundColor: palette.paper, border: '2px solid rgba(25,25,25,0.30)', borderRadius: aesthetic.paperRadius, color: palette.ink, boxShadow: `${7 + 3 * lift}px ${7 + 3 * lift}px 0 ${borderColor || palette.blue}`, ...style}}>{children}</div>;

// 扁平风不加任何调色层：纯色块对比即为视觉语言。
const Grade: React.FC = () => null;

// 悬浮圆角彩条字幕：靛蓝胶囊 + 墨色硬偏移影（扁平语言），两侧橙/绿小圆头，不再贴底横杠。
const SubtitleChrome: Theme['SubtitleChrome'] = ({mode, children}) =>
  <div style={{position: 'absolute', left: 0, right: 0, bottom: 40, zIndex: 200, display: 'flex', justifyContent: 'center'}}>
    <div style={{background: palette.blue, borderRadius: 26, padding: '16px 40px', boxShadow: `7px 7px 0 rgba(25,25,25,0.9)`, display: 'flex', alignItems: 'center', maxWidth: mode.safe}}>
      <div style={{width: 12, height: 12, background: palette.orange, borderRadius: '50%', marginRight: 22, flexShrink: 0}} />
      <div style={{fontFamily: 'Kai', fontSize: mode.subFont, fontWeight: 700, lineHeight: 1.18, letterSpacing: 1.6, color: palette.white, whiteSpace: 'nowrap'}}>
        {children}
      </div>
      <div style={{width: 12, height: 12, background: palette.green, borderRadius: '50%', marginLeft: 22, flexShrink: 0}} />
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
