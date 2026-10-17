import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import type {BgVariant, Theme} from './types';

// ============================================================================
// FLAT 主题（默认）：安静、现代、友好的教育插画风（LOCKED）
// 设计语言：天空蓝 / 奶油色底面 + 白卡 + 主题色硬偏移影；一个自信的主蓝，
// 珊瑚 + 薄荷两个暖/冷辅色，阳光黄只做高亮；不用浑浊的灰。
//
// 色值来源：Radix Colors v3（MIT，© 2021 Radix，https://github.com/radix-ui/colors）。
// 只把十六进制值抄进来（vendored），运行时不依赖任何包。每个值后面注明 Radix 色阶与级数：
//   step 9  = 实色填充（按钮、色块、描边）
//   step 11 = Radix 设计给「浅底上的文字」用的级数；本主题的 *Ink 再向 step 12 混 8–10%，
//             使它在**全部三个表面**（paper / paperWarm / paperBase）上都 ≥ 4.6:1
//             （validate-presentation 的门槛是 4.5，留 0.1 余量防取整）。
// 约定：原色（blue/orange/green/gold/red）只用于填充与描边；当文字色一律用对应的 *Ink。
// 本文件所有数值均为锁定值，制作时整体引用，不得调参。
// ============================================================================

const palette: Theme['palette'] = {
  ink: '#1c2024',          // slate 12
  muted: '#60646c',        // slate 11
  blue: '#0090ff',         // blue 9 · 主角色
  blueInk: '#0d6fc6',      // blue 11 → 12 混 8%（白/奶油/天空底上 ≥ 4.6:1）
  blueLight: 'rgba(0,144,255,0.14)',
  orange: '#e54d2e',       // tomato 9 · 珊瑚
  orangeInk: '#d13415',    // tomato 11
  orangeLight: 'rgba(229,77,46,0.14)',
  green: '#29a383',        // jade 9 · 薄荷绿
  greenInk: '#207d64',     // jade 11 → 12 混 8%
  greenLight: 'rgba(41,163,131,0.16)',
  gold: '#ffc53d',         // amber 9 · 阳光黄（只做高亮/色块，上面放 ink 字）
  goldInk: '#a25f03',      // amber 11 → 12 混 10%
  red: '#e5484d',          // red 9
  redInk: '#ce2c31',       // red 11
  navy: '#113264',         // blue 12
  paper: '#ffffff',        // 卡片面
  paperWarm: '#fefbe9',    // amber 2 · 奶油
  paperBase: '#f1fafd',    // sky 2 · 天空底
  line: 'rgba(28,32,36,0.34)',
  lineOrange: 'rgba(229,77,46,0.60)',
  lineBlue: 'rgba(0,144,255,0.60)',
  lineGreen: 'rgba(41,163,131,0.60)',
  white: '#ffffff',
  // 场景层柔色
  skyTint: '#e6f4fe',      // blue 3
  blueLine: 'rgba(0,144,255,0.42)',
  dotIdle: '#cdced6',      // slate 7
  mutedFill: 'rgba(96,100,108,0.26)',
  mutedBar: 'rgba(96,100,108,0.22)',
  mutedWash: 'rgba(96,100,108,0.14)',
  orangeSoft: '#f5a898',   // tomato 7
  orangeDeep: '#d13415',   // tomato 11
  gaugeTrack: 'rgba(28,32,36,0.14)',
  greenGlow: 'rgba(41,163,131,0.35)',
  stageTint: 'rgba(230,244,254,0.55)',
  headerAccent: '#113264', // blue 12（在天空底上 ≥ 11:1）
  headerSub: '#60646c',
};

const aesthetic: Theme['aesthetic'] = {
  subtitleSafeWidth: 1334, paperRadius: 22, paperOutline: 0,
  textureOpacity: 0, gridOpacity: 0, gradeWarmth: 0, gradeVignette: 0,
  subtitleWeight: 700, subtitleLetterSpacing: 1.6, subtitlePadX: 108,
};

// 偏移实色影：无模糊、无墨边（扁平语言）。场景层直接调用时用主蓝；
// Paper 卡片按 borderColor 换对应彩色影。
const paperShadow = (lift: number) =>
  `${6 + 3 * lift}px ${6 + 3 * lift}px 0 ${palette.blue}`;

// 背景（LOCKED）：三张固定资产图，均为 2560×1440（与 16:9 画布 1:1 逐像素），渲染时 cover。
// 中央约 70% 是安静的内容安全区，装饰只在四边与四角：
//   main    右下角蓝色圆头机器人（天线 + 黄球）从底边探头，左下薄荷山丘 + 珊瑚小方块探头
//   chapter 稍饱和的天空 + 中央奶油色柔光，机器人在左下挥手，珊瑚小方块在右下
//   quiet   最安静：只剩右下角机器人头顶 + 左下一线山丘，给信息密集的镜头
// 禁止改回代码自绘背景；换图要连同 manifests/visual-assets.json 的 sha256 一起换。
const BACKGROUNDS: Record<BgVariant, string> = {
  main: 'bg/bg-flat-main.jpg',
  chapter: 'bg/bg-flat-chapter.jpg',
  quiet: 'bg/bg-flat-quiet.jpg',
};

const Background: Theme['Background'] = ({variant = 'main'}) => (
  <AbsoluteFill style={{background: palette.paperBase}}>
    <Img src={staticFile(BACKGROUNDS[variant])} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
  </AbsoluteFill>
);

// 白卡：2px 极浅墨边（界定上/左缘）+ 实色硬偏移影（界定右下缘）；场景传 borderColor 时影子同步变色。
const Paper: Theme['Paper'] = ({children, style, lift = 0, borderColor}) =>
  <div style={{position: 'absolute', backgroundColor: palette.paper, border: '2px solid rgba(28,32,36,0.14)', borderRadius: aesthetic.paperRadius, color: palette.ink, boxShadow: `${6 + 3 * lift}px ${6 + 3 * lift}px 0 ${borderColor || palette.blue}`, ...style}}>{children}</div>;

// 扁平风不加任何调色层：纯色块对比即为视觉语言。
const Grade: React.FC = () => null;

// 悬浮圆角字幕条：深一级的主蓝胶囊（白字 ≥ 4.6:1）+ 海军蓝硬偏移影，两侧珊瑚 / 阳光黄小圆点。
const SubtitleChrome: Theme['SubtitleChrome'] = ({mode, children}) =>
  <div style={{position: 'absolute', left: 0, right: 0, bottom: 40, zIndex: 200, display: 'flex', justifyContent: 'center'}}>
    <div style={{background: palette.blueInk, borderRadius: 999, padding: '15px 40px', boxShadow: `0 6px 0 ${palette.navy}`, display: 'flex', alignItems: 'center', maxWidth: mode.safe}}>
      <div style={{width: 12, height: 12, background: palette.orange, borderRadius: '50%', marginRight: 22, flexShrink: 0}} />
      <div style={{fontFamily: 'Kai', fontSize: mode.subFont, fontWeight: 700, lineHeight: 1.18, letterSpacing: 1.6, color: palette.white, whiteSpace: 'nowrap'}}>
        {children}
      </div>
      <div style={{width: 12, height: 12, background: palette.gold, borderRadius: '50%', marginLeft: 22, flexShrink: 0}} />
    </div>
  </div>;

// 背景装饰区（LOCKED 声明）：三张背景图里装饰所占矩形的**并集**（1920×1080 设计坐标）。
// 内容压到这些区域时必须坐在 CoverPanel（tone='paper'）上。
const backgroundDecorZones = [
  {x: 1500, y: 840, w: 420, h: 240},   // 右下：蓝色机器人（main / quiet）· 薄荷山丘 + 珊瑚小方块（chapter）
  {x: 0, y: 840, w: 400, h: 240},      // 左下：薄荷山丘 + 珊瑚小方块（main / quiet）· 蓝色机器人（chapter）
  {x: 0, y: 120, w: 190, h: 260},      // 左上：小云
  {x: 1730, y: 120, w: 190, h: 260},   // 右上：小云
];

export const THEME: Theme = {
  id: 'flat',
  palette,
  aesthetic,
  paperShadow,
  backgrounds: BACKGROUNDS,
  Background,
  Paper,
  Grade,
  backgroundDecorZones,
  SubtitleChrome,
};
