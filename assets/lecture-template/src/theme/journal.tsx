import React from 'react';
import type {BgVariant, Theme} from './types';
import {FibreOverlay, PaperSubtitle, TapeStrip, chromeIn, makeBackground, tiltOf} from './craft-common';

// ============================================================================
// JOURNAL 主题（3.3.0，LOCKED）：博物学家手账 / 水彩笔记本。
// 媒介：一页暖白棉纸；东西被「画上去、贴上去、写上去」——水彩淡彩、钢笔批注、胶带贴的照片。
// 适合：观察、发现、实验记录、生物 / 自然 / 历史上的「有人第一次看见」。
// 原生动作（见 references/theme-journal.md）：晕染即揭示、标本 + 批注、放大镜压在贴进来的真照片上、雾洗回白纸。
// 不是：矢量插画套水彩滤镜；不是暗底；没有 UI 胶囊。
// 色值全部锁定；*Ink 在三种纸面上 ≥ 4.7:1（validate-presentation 门禁核对）。
// ============================================================================

const palette: Theme['palette'] = {
  ink: '#2b2420', muted: '#5b4f44',
  blue: '#4f7d95', blueInk: '#2f5a70', blueLight: 'rgba(79,125,149,0.16)',      // 雨水蓝（淡彩）
  orange: '#c8442a', orangeInk: '#a2311b', orangeLight: 'rgba(200,68,42,0.14)',  // 朱砂：唯一强调色
  green: '#6f8f5a', greenInk: '#435d37', greenLight: 'rgba(111,143,90,0.16)',    // 鼠尾草绿
  gold: '#d8a23a', goldInk: '#79560f',                                           // 赭黄（色块用，字用 goldInk）
  red: '#b83a32', redInk: '#982a23', navy: '#2c3e50',
  paper: '#fbf6ea', paperWarm: '#f6eedc', paperBase: '#efe6d2',
  line: 'rgba(43,36,32,0.34)', lineOrange: 'rgba(200,68,42,0.6)', lineBlue: 'rgba(79,125,149,0.6)', lineGreen: 'rgba(111,143,90,0.6)',
  white: '#fffdf7',
  skyTint: '#e4ecea', blueLine: 'rgba(79,125,149,0.42)', dotIdle: '#d8cdb8',
  mutedFill: 'rgba(91,79,68,0.22)', mutedBar: 'rgba(91,79,68,0.18)', mutedWash: 'rgba(91,79,68,0.12)',
  orangeSoft: '#e8a58f', orangeDeep: '#a2311b', gaugeTrack: 'rgba(43,36,32,0.14)',
  greenGlow: 'rgba(111,143,90,0.35)', stageTint: 'rgba(246,238,220,0.6)',
  headerAccent: '#2b2420', headerSub: '#5b4f44',
};

const aesthetic: Theme['aesthetic'] = {
  subtitleSafeWidth: 1334, paperRadius: 3, paperOutline: 0,
  textureOpacity: 0.55, gridOpacity: 0, gradeWarmth: 0.04, gradeVignette: 0.10,
  subtitleWeight: 700, subtitleLetterSpacing: 2, subtitlePadX: 68,
  subtitleSize: 72, subtitleFamily: 'Serif',
};

// 纸在纸上：极短、偏暖、贴面的投影（不是 UI 卡片的悬浮影）。
const paperShadow = (lift: number) =>
  `0 ${1 + 3 * lift}px ${3 + 10 * lift}px rgba(70,50,25,${0.16 + 0.1 * lift}), 0 0 0 1px rgba(70,50,25,0.06)`;

const BACKGROUNDS: Record<BgVariant, string> = {
  main: 'bg/bg-journal-main.jpg', chapter: 'bg/bg-journal-chapter.jpg', quiet: 'bg/bg-journal-quiet.jpg',
};
const Background = makeBackground(palette.paperBase, BACKGROUNDS);

// 卡片 = 一张裁下来的纸，用两条胶带贴在本子上；微倾 ±0.8°。borderColor 只染胶带（语义色仍可读出）。
const Paper: Theme['Paper'] = ({children, style, lift = 0, borderColor}) => {
  const {transform, ...rest} = style ?? {};
  const tilt = tiltOf(style, 0.8);
  const tape = borderColor ? `${borderColor}55` : undefined;
  return <div style={{position: 'absolute', backgroundColor: palette.paper, border: '1px solid rgba(70,50,25,0.10)', borderRadius: aesthetic.paperRadius,
    color: palette.ink, boxShadow: paperShadow(lift), ...rest, transform: `${transform ? transform + ' ' : ''}rotate(${tilt}deg)`}}>
    <FibreOverlay opacity={aesthetic.textureOpacity} radius={aesthetic.paperRadius} />
    <TapeStrip x={-22} y={-12} w={96} rot={-24} color={tape} />
    <TapeStrip x={-1} y={-12} w={96} rot={22} color={tape} />
    {children}
  </div>;
};
// 纤维层与胶带都是绝对定位的兄弟节点：不改变 children 的排版（调用方常给 Paper 写 display:flex）。

const Grade: React.FC = () => <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 190,
  boxShadow: `inset 0 0 220px rgba(90,60,20,${aesthetic.gradeVignette})`, background: `rgba(255,220,160,${aesthetic.gradeWarmth})`, mixBlendMode: 'multiply'}} />;

const SubtitleChrome = PaperSubtitle({ink: palette.ink, halo: 'rgba(250,245,232,0.92)', size: 72});

// 章节标识：左上角一行钢笔小字「No.01 — 标题」，下面一条手划线；不要右上技术页眉。
const Chrome: Theme['Chrome'] = (p) => {
  const k = chromeIn(p);
  return <div style={{position: 'absolute', left: 96, top: 62, zIndex: 150, opacity: k, transform: `translateY(${(1 - k) * 8}px)`}}>
    <div style={{fontFamily: 'Kai', fontWeight: 700, fontSize: 34, color: palette.ink, letterSpacing: 2, whiteSpace: 'nowrap'}}>
      <span style={{fontFamily: 'Caveat,Kai', fontSize: 38, color: palette.orangeInk, marginRight: 14}}>No.{String(p.stage + 1).padStart(2, '0')}</span>{p.title}
    </div>
    <svg width={360} height={14} style={{display: 'block', marginTop: 2}} aria-hidden>
      <path d={`M2 8 C 80 ${4 + 3 * Math.sin(p.stage)}, 200 11, ${2 + 356 * k} 6`} stroke={palette.orange} strokeWidth={3} fill="none" strokeLinecap="round" opacity={0.75} />
    </svg>
  </div>;
};

// 背景装饰区：chapter 变体的两团水彩晕（左下、右上）。
const backgroundDecorZones = [
  {x: 0, y: 760, w: 420, h: 320},
  {x: 1640, y: 0, w: 280, h: 230},
];

export const THEME: Theme = {
  id: 'journal', palette, aesthetic, paperShadow, backgrounds: BACKGROUNDS, Background, Paper, Grade, SubtitleChrome, Chrome,
  backgroundDecorZones,
  craft: {medium: 'journal', fibre: 0.55, inkLine: palette.ink, handFamily: 'Kai', bodyFamily: 'Serif,Kai', accent: palette.orange,
    transition: 'slide', fonts: ['700 40px Serif']},
};
