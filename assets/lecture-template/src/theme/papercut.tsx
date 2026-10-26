import React from 'react';
import type {BgVariant, Theme} from './types';
import {FibreOverlay, PaperSubtitle, chromeIn, makeBackground, tiltOf} from './craft-common';

// ============================================================================
// PAPERCUT 主题（3.3.0，LOCKED）：红色窗花剪纸，正面光、米色宣纸底。
// 媒介：一切都是剪刀剪出来、平铺在另一张纸上的纸片；细节只来自「剪掉了什么」（洞即是线）。
// 适合：对称 / 复制 / 一变多 / 缺一块还能补回 / 结构与镂空（纠错码、细胞分裂、雪花、编码）。
// 原生动作：对折一刀展开成多份、碎纸片飞回原位、剪掉一角、背光透洞（见 references/theme-papercut.md）。
// 纪律：红不压红（底是米色纸家族）；金箔只留给全片一个时刻；不画渐变、不画描边。
// 色值全部锁定；*Ink 在三种纸面上 ≥ 4.7:1。
// ============================================================================

const palette: Theme['palette'] = {
  ink: '#2a1a14', muted: '#654b3b',
  blue: '#2f4e7a', blueInk: '#253f63', blueLight: 'rgba(47,78,122,0.14)',        // 靛青纸
  orange: '#d2201f', orangeInk: '#a3151a', orangeLight: 'rgba(210,32,31,0.12)',   // 中国红（主角材料）
  green: '#3e7d68', greenInk: '#2a5a4a', greenLight: 'rgba(62,125,104,0.14)',     // 玉绿纸
  gold: '#c9a13b', goldInk: '#735610',                                            // 金箔（全片只用一次）
  red: '#c8102e', redInk: '#990f21', navy: '#2a1a14',
  paper: '#fbf3e3', paperWarm: '#f4e7cf', paperBase: '#efe2c8',
  line: 'rgba(42,26,20,0.34)', lineOrange: 'rgba(210,32,31,0.6)', lineBlue: 'rgba(47,78,122,0.6)', lineGreen: 'rgba(62,125,104,0.6)',
  white: '#fffaf0',
  skyTint: '#efe2c8', blueLine: 'rgba(47,78,122,0.42)', dotIdle: '#dccbb0',
  mutedFill: 'rgba(101,75,59,0.22)', mutedBar: 'rgba(101,75,59,0.18)', mutedWash: 'rgba(101,75,59,0.12)',
  orangeSoft: '#e9938a', orangeDeep: '#a3151a', gaugeTrack: 'rgba(42,26,20,0.14)',
  greenGlow: 'rgba(62,125,104,0.35)', stageTint: 'rgba(244,231,207,0.6)',
  headerAccent: '#2a1a14', headerSub: '#654b3b',
};

const aesthetic: Theme['aesthetic'] = {
  subtitleSafeWidth: 1334, paperRadius: 0, paperOutline: 0,
  textureOpacity: 0.45, gridOpacity: 0, gradeWarmth: 0, gradeVignette: 0.08,
  subtitleWeight: 700, subtitleLetterSpacing: 3, subtitlePadX: 120,
  subtitleSize: 72, subtitleFamily: 'NotoSerifSC',
};

// 纸片的厚度：紧贴的软影 + 右下 1px 切口暗边（不是 UI 悬浮影）。
const paperShadow = (lift: number) =>
  `${1 + lift}px ${2 + 2 * lift}px ${2 + 4 * lift}px rgba(60,20,10,${0.22 + 0.08 * lift}), 1px 1px 0 rgba(60,20,10,0.25)`;

const BACKGROUNDS: Record<BgVariant, string> = {
  main: 'bg/bg-papercut-main.jpg', chapter: 'bg/bg-papercut-chapter.jpg', quiet: 'bg/bg-papercut-quiet.jpg',
};
const Background = makeBackground(palette.paperBase, BACKGROUNDS);

// 卡片 = 一张米色厚纸，内侧一圈红色「阴刻」双线（剪纸的双轮廓）；不倒圆角，微倾 ±0.5°。
const Paper: Theme['Paper'] = ({children, style, lift = 0, borderColor}) => {
  const {transform, ...rest} = style ?? {};
  const tilt = tiltOf(style, 0.5);
  const c = borderColor || palette.orange;
  return <div style={{position: 'absolute', backgroundColor: palette.paper, border: '1px solid rgba(60,20,10,0.12)', borderRadius: 0,
    color: palette.ink, boxShadow: `${paperShadow(lift)}, inset 0 0 0 7px ${palette.paper}, inset 0 0 0 9px ${c}, inset 0 0 0 13px ${palette.paper}, inset 0 0 0 14px ${c}`,
    ...rest, transform: `${transform ? transform + ' ' : ''}rotate(${tilt}deg)`}}>
    <FibreOverlay opacity={aesthetic.textureOpacity} />
    {children}
  </div>;
};

const Grade: React.FC = () => <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 190,
  boxShadow: `inset 0 0 200px rgba(80,30,10,${aesthetic.gradeVignette})`}} />;

// 字幕 = 一条深红横批（比画面里的红深一档，米色字 ≥ 7:1），两端燕尾，像贴上去的对联条。
const SubtitleChrome = PaperSubtitle({ink: '#fff6e6', halo: 'transparent', size: 72, letterSpacing: 3, bottom: 30,
  plate: {background: '#8f1216', padding: '10px 60px 14px', boxShadow: '2px 4px 6px rgba(60,10,5,0.35)',
    clipPath: 'polygon(0 0, 100% 0, calc(100% - 26px) 50%, 100% 100%, 0 100%, 26px 50%)'}});

// 章节标识：左上一枚红色方印（序号）+ 宋体章名；无技术页眉。
const Chrome: Theme['Chrome'] = (p) => {
  const k = chromeIn(p);
  const s = 0.9 + 0.1 * Math.min(1, k * 1.4);
  return <div style={{position: 'absolute', left: 92, top: 66, zIndex: 150, display: 'flex', alignItems: 'center', gap: 18, opacity: k}}>
    <div style={{width: 64, height: 64, background: palette.orange, color: '#fff6e6', display: 'grid', placeItems: 'center',
      fontFamily: 'NotoSerifSC,Kai', fontWeight: 700, fontSize: 32, transform: `scale(${s}) rotate(-3deg)`, boxShadow: '1px 2px 3px rgba(60,10,5,0.3)'}}>
      {String(p.stage + 1).padStart(2, '0')}</div>
    <div style={{fontFamily: 'NotoSerifSC,Kai', fontWeight: 700, fontSize: 34, color: palette.ink, letterSpacing: 4, whiteSpace: 'nowrap'}}>{p.title}</div>
  </div>;
};

// 背景装饰区：chapter 变体上沿的红色锯齿条。
const backgroundDecorZones = [{x: 0, y: 0, w: 1920, h: 72}];

export const THEME: Theme = {
  id: 'papercut', palette, aesthetic, paperShadow, backgrounds: BACKGROUNDS, Background, Paper, Grade, SubtitleChrome, Chrome,
  backgroundDecorZones,
  craft: {medium: 'papercut', fibre: 0.45, inkLine: palette.orange, handFamily: 'Kai', bodyFamily: 'NotoSerifSC,Kai', accent: palette.orange,
    transition: 'drop', fonts: ['700 40px NotoSerifSC']},
};
