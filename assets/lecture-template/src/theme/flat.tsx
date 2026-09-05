import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
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

// 背景（LOCKED）：固定资产图，每比例一张（2560×1440 / 1920×1440 / 1440×1920），
// 像素与画布一一对应；探头式小怪兽（右下靛蓝圆怪从底边探出上半身+左下薄荷山丘
// 珊瑚小怪探头）、浅灰蓝噪点纸面、85% 留白。禁止改回代码自绘背景。
const BG_BY_MODE = {'16:9': 'bg-flat-169.jpg', '4:3': 'bg-flat-43.jpg', '3:4': 'bg-flat-34.jpg'} as const;

const Background: React.FC = () => {
  const {canvas} = useCanvas();
  return <AbsoluteFill style={{background: palette.paperBase}}>
    <Img src={staticFile(BG_BY_MODE[canvas])} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
  </AbsoluteFill>;
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
