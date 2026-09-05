import React from 'react';
import {AbsoluteFill} from 'remotion';
import {useCanvas} from './canvas';
import type {Theme} from './types';

// ============================================================================
// CEL 主题：动漫赛璐璐·分镜风（LOCKED）
// 设计语言：粗墨线、平涂高饱和、硬偏移投影、半调网点、速度线。
// 色彩系统：蓝/红双主角（同档 饱和度≈80 明度≈54），绿/金按同阶梯推导，不许跳出档位。
// 本文件所有数值均为锁定值，制作时整体引用，不得调参。
// ============================================================================

const palette: Theme['palette'] = {
  ink: '#14110f',
  muted: '#7a6f63',
  blue: '#2b6de8',
  blueLight: 'rgba(43,109,232,0.17)',
  orange: '#e8382a',
  orangeLight: 'rgba(232,56,42,0.17)',
  green: '#24bc6e',
  greenLight: 'rgba(36,188,110,0.17)',
  gold: '#f2b721',
  red: '#e8382a',
  navy: '#14110f',
  paper: '#ffffff',
  paperWarm: '#fdfdfb',
  paperBase: '#fdfdfb',
  line: 'rgba(20,17,15,0.45)',
  lineOrange: 'rgba(232,56,42,0.58)',
  lineBlue: 'rgba(43,109,232,0.58)',
  lineGreen: 'rgba(36,188,110,0.58)',
  white: '#ffffff',
  // 场景层柔色
  skyTint: '#e4edfd',
  blueLine: 'rgba(43,109,232,0.38)',
  dotIdle: '#d6c8b4',
  mutedFill: 'rgba(122,111,99,0.33)',
  mutedBar: 'rgba(122,111,99,0.30)',
  mutedWash: 'rgba(122,111,99,0.18)',
  orangeSoft: '#f2795e',
  orangeDeep: '#c22a20',
  gaugeTrack: 'rgba(20,17,15,0.22)',
  greenGlow: 'rgba(36,188,110,0.35)',
  stageTint: 'rgba(255,246,232,0.5)',
  headerAccent: '#2b6de8',
  headerSub: '#7a6f63',
};

const aesthetic: Theme['aesthetic'] = {
  subtitleSafeWidth: 1334, paperRadius: 8, paperOutline: 4.5,
  textureOpacity: 0, gridOpacity: 0, gradeWarmth: 0, gradeVignette: .028,
};

// 硬偏移墨影：无模糊，随 lift 同步加大位移（举起感），不使用柔和投影。
const paperShadow = (lift: number) =>
  `${7 + 7 * lift}px ${7 + 7 * lift}px 0 rgba(20,17,15,0.92)`;

// 分镜格微旋转（LOCKED）：由卡片位置哈希出 ±1° 内的固定倾角，
// 同一张卡永远同一个角度，与动效 transform 叠加而不冲突。
const panelTilt = (style?: React.CSSProperties) => {
  const left = Number(style?.left ?? 0), top = Number(style?.top ?? 0);
  return (((Math.round(left) + Math.round(top)) % 5) - 2) * 0.5;
};

const Background: React.FC = () => {
  const {mode} = useCanvas();
  return <>
    <AbsoluteFill style={{background: palette.paperBase}} />
    {/* 半调网点：右上汇聚渐隐（所有比例共用百分比锚点） */}
    <AbsoluteFill style={{
      backgroundImage: `radial-gradient(${palette.ink} 1.8px, transparent 2.4px)`,
      backgroundSize: '20px 20px', opacity: 0.11,
      WebkitMaskImage: 'radial-gradient(circle at 88% 8%, black 0%, transparent 48%)',
      maskImage: 'radial-gradient(circle at 88% 8%, black 0%, transparent 48%)',
    }} />
    {/* 半调网点：左下弱呼应 */}
    <AbsoluteFill style={{
      backgroundImage: `radial-gradient(${palette.ink} 1.6px, transparent 2.2px)`,
      backgroundSize: '18px 18px', opacity: 0.08,
      WebkitMaskImage: 'radial-gradient(circle at 6% 96%, black 0%, transparent 42%)',
      maskImage: 'radial-gradient(circle at 6% 96%, black 0%, transparent 42%)',
    }} />
    {/* 速度线：左上 16 束扇形汇聚 */}
    <svg width={mode.designW} height={mode.designH} style={{position: 'absolute', inset: 0}}>
      {Array.from({length: 16}).map((_, i) => {
        const ang = (i / 16) * Math.PI / 2.2 + 0.12;
        const x1 = -40 + Math.cos(ang) * 260, y1 = -40 + Math.sin(ang) * 260;
        const x2 = -40 + Math.cos(ang) * 680, y2 = -40 + Math.sin(ang) * 680;
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={palette.ink} strokeWidth={3.6} opacity={0.22} />;
      })}
    </svg>
  </>;
};

const Paper: Theme['Paper'] = ({children, style, lift = 0, borderColor}) => {
  const {transform, ...rest} = style ?? {};
  const tilt = panelTilt(style);
  return <div style={{position: 'absolute', backgroundColor: palette.paper, border: `5px solid ${borderColor || palette.ink}`, borderRadius: aesthetic.paperRadius, color: palette.ink, boxShadow: paperShadow(lift), ...rest, transform: `${transform ? transform + ' ' : ''}rotate(${tilt}deg)`}}>{children}</div>;
};

// 赛璐璐只保留极轻墨角暗角，不加暖色柔光。
const Grade: React.FC = () => <AbsoluteFill style={{pointerEvents: 'none', zIndex: 190}}>
  <AbsoluteFill style={{boxShadow: `inset 0 0 120px rgba(20,17,15,${aesthetic.gradeVignette})`}} />
</AbsoluteFill>;

const SubtitleChrome: Theme['SubtitleChrome'] = ({mode, children}) =>
  <div style={{position: 'absolute', left: 0, right: 0, bottom: 44, zIndex: 200, display: 'flex', justifyContent: 'center'}}>
    <div style={{background: palette.white, border: `5px solid ${palette.ink}`, boxShadow: `8px 8px 0 ${palette.ink}`, padding: '12px 34px', maxWidth: mode.safe}}>
      <div style={{fontFamily: 'Kai', fontSize: mode.subFont, fontWeight: 700, lineHeight: 1.18, letterSpacing: 1.6, color: palette.ink, whiteSpace: 'nowrap'}}>
        {children}
      </div>
    </div>
  </div>;

// 爆炸贴（锁定构件）：12 角星形 + 3.4px 墨边，场景层只给 x/y/size/text。
export const Burst: React.FC<{x: number; y: number; size: number; text: string; color?: string}> =
  ({x, y, size, text, color = palette.gold}) => {
    const spikes = 12, pts: string[] = [];
    for (let i = 0; i < spikes * 2; i++) {
      const r = i % 2 === 0 ? 50 : 38, a = (i / (spikes * 2)) * Math.PI * 2 - Math.PI / 2;
      pts.push(`${50 + r * Math.cos(a)},${50 + r * Math.sin(a)}`);
    }
    return (
      <div style={{position: 'absolute', left: x, top: y, width: size, height: size, transform: 'rotate(10deg)'}}>
        <svg viewBox="0 0 100 100" width={size} height={size} style={{overflow: 'visible'}}>
          <polygon points={pts.join(' ')} fill={color} stroke={palette.ink} strokeWidth={3.4} strokeLinejoin="round" />
        </svg>
        <div style={{position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', fontFamily: 'Kai', fontWeight: 700, fontSize: size * 0.24, color: palette.ink}}>{text}</div>
      </div>
    );
  };

export const THEME: Theme = {
  id: 'cel',
  palette,
  aesthetic,
  paperShadow,
  Background,
  Paper,
  Grade,
  SubtitleChrome,
  extras: {Burst},
};
