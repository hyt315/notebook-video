import React from 'react';
import type {BgVariant, Theme} from './types';
import {PaperSubtitle, chromeIn, makeBackground, tiltOf} from './craft-common';

// ============================================================================
// ARCHIVE 主题（3.3.0，LOCKED）：档案灯台。冷白的背光台面，上面摆着真实的档案物件
// （Commons 上的公有领域扫描件、老照片、手稿、显微照片），放大镜压上去，物件在镜片里「活」过来。
// 适合：考据、溯源、"这句话最早是谁说的"、历史上的第一张图、真实数据。
// 原生动作：放大镜里负片转正、一行字亮起、两份记录并排、台面拉远变索引（见 references/theme-archive.md）。
// 纪律：物件必须是真的（不生成、不重画来冒充）；一个信号色；没有做旧滤镜（干净、现代、安静）。
// 色值全部锁定；*Ink 在三种面上 ≥ 4.7:1。
// ============================================================================

const palette: Theme['palette'] = {
  ink: '#1d2328', muted: '#505b65',
  blue: '#3b6ea5', blueInk: '#2a5584', blueLight: 'rgba(59,110,165,0.14)',
  orange: '#e0481f', orangeInk: '#ad330e', orangeLight: 'rgba(224,72,31,0.13)',   // 信号色：标注、读数、锚点
  green: '#3f8a6a', greenInk: '#2b6a50', greenLight: 'rgba(63,138,106,0.14)',
  gold: '#d9a020', goldInk: '#7a560b',
  red: '#d33a2c', redInk: '#a5251a', navy: '#1d2328',
  paper: '#ffffff', paperWarm: '#f7f5ef', paperBase: '#edf0f2',
  line: 'rgba(29,35,40,0.30)', lineOrange: 'rgba(224,72,31,0.65)', lineBlue: 'rgba(59,110,165,0.6)', lineGreen: 'rgba(63,138,106,0.6)',
  white: '#ffffff',
  skyTint: '#e4eaee', blueLine: 'rgba(59,110,165,0.42)', dotIdle: '#ccd3d8',
  mutedFill: 'rgba(80,91,101,0.22)', mutedBar: 'rgba(80,91,101,0.18)', mutedWash: 'rgba(80,91,101,0.12)',
  orangeSoft: '#f2a48c', orangeDeep: '#ad330e', gaugeTrack: 'rgba(29,35,40,0.12)',
  greenGlow: 'rgba(63,138,106,0.3)', stageTint: 'rgba(237,240,242,0.6)',
  headerAccent: '#1d2328', headerSub: '#505b65',
};

const aesthetic: Theme['aesthetic'] = {
  subtitleSafeWidth: 1334, paperRadius: 2, paperOutline: 0,
  textureOpacity: 0, gridOpacity: 0, gradeWarmth: 0, gradeVignette: 0.06,
  subtitleWeight: 700, subtitleLetterSpacing: 2, subtitlePadX: 88,
  subtitleSize: 72, subtitleFamily: 'NotoSerifSC',
};

// 物件躺在发光台面上：极浅、偏冷、贴面的影。
const paperShadow = (lift: number) =>
  `0 ${1 + 4 * lift}px ${4 + 14 * lift}px rgba(20,30,40,${0.14 + 0.08 * lift})`;

const BACKGROUNDS: Record<BgVariant, string> = {
  main: 'bg/bg-archive-main.jpg', chapter: 'bg/bg-archive-chapter.jpg', quiet: 'bg/bg-archive-quiet.jpg',
};
const Background = makeBackground(palette.paperBase, BACKGROUNDS);

// 卡片 = 档案纸：白纸、细灰边，躺在台面上；微倾 ±0.4°。
const Paper: Theme['Paper'] = ({children, style, lift = 0, borderColor}) => {
  const {transform, ...rest} = style ?? {};
  const tilt = tiltOf(style, 0.4);
  return <div style={{position: 'absolute', backgroundColor: palette.paper, border: `1px solid ${borderColor ? borderColor : 'rgba(29,35,40,0.16)'}`,
    borderRadius: aesthetic.paperRadius, color: palette.ink, boxShadow: paperShadow(lift), ...rest,
    transform: `${transform ? transform + ' ' : ''}rotate(${tilt}deg)`}}>
    {children}
  </div>;
};

const Grade: React.FC = () => <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 190,
  boxShadow: `inset 0 0 240px rgba(20,30,40,${aesthetic.gradeVignette})`}} />;

// 字幕 = 博物馆说明签：白条、细墨边、左侧一道信号色竖线。
const SubtitleChrome = PaperSubtitle({ink: palette.ink, halo: 'transparent', size: 72, bottom: 34,
  plate: {background: 'rgba(255,255,255,0.96)', padding: '8px 44px 12px 52px', boxShadow: '0 2px 8px rgba(20,30,40,0.16)',
    borderLeft: `8px solid ${palette.orange}`}});

// 章节标识：左上编目号「ARCHIVE · 01 / 标题」，等宽小字 + 章名。
const Chrome: Theme['Chrome'] = (p) => {
  const k = chromeIn(p);
  return <div style={{position: 'absolute', left: 92, top: 64, zIndex: 150, opacity: k, transform: `translateX(${(1 - k) * -10}px)`}}>
    <div style={{fontFamily: 'Space,Kai', fontWeight: 600, fontSize: 24, letterSpacing: 5, color: palette.orangeInk}}>No. {String(p.stage + 1).padStart(3, '0')}</div>
    <div style={{fontFamily: 'NotoSerifSC,Kai', fontWeight: 700, fontSize: 36, color: palette.ink, letterSpacing: 2, marginTop: 2, whiteSpace: 'nowrap'}}>{p.title}</div>
  </div>;
};

// 背景装饰区：chapter 变体上沿与左沿的灯箱边框、下沿刻度尺。
const backgroundDecorZones = [{x: 0, y: 0, w: 1920, h: 28}, {x: 0, y: 0, w: 28, h: 1080}, {x: 0, y: 1040, w: 1920, h: 40}];

export const THEME: Theme = {
  id: 'archive', palette, aesthetic, paperShadow, backgrounds: BACKGROUNDS, Background, Paper, Grade, SubtitleChrome, Chrome,
  backgroundDecorZones,
  craft: {medium: 'archive', fibre: 0, inkLine: palette.orange, handFamily: 'Kai', bodyFamily: 'NotoSerifSC,Kai', accent: palette.orange,
    transition: 'pageturn', fonts: ['700 40px NotoSerifSC']},
};
