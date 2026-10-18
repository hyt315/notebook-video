import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import type {BgVariant, Theme} from './types';

// ============================================================================
// CEL 主题：漫画 / 少年漫分镜风（LOCKED）
// 设计语言：米白漫画纸 + 半调网点、近黑粗墨线、高饱和红 / 蓝 / 黄三原色平涂、硬偏移墨影、速度线。
//
// 色值来源：Radix Colors v3（MIT，© 2021 Radix，https://github.com/radix-ui/colors），
// 只抄十六进制值（vendored），运行时无依赖。step 9 = 实色填充；step 11 = 浅底文字级；
// goldInk 由 yellow 11 向 yellow 12 混 10%，使它在三个表面上都 ≥ 4.6:1。
// 约定：原色只用于填充与描边；当文字色一律用对应的 *Ink（presentation-gate 会查）。
// 本文件所有数值均为锁定值，制作时整体引用，不得调参。
// ============================================================================

const palette: Theme['palette'] = {
  ink: '#111111',          // gray dark 1 · 近黑墨
  muted: '#63635e',        // sand 11
  blue: '#0090ff',         // blue 9 · 漫画蓝
  blueInk: '#0d74ce',      // blue 11
  blueLight: 'rgba(0,144,255,0.16)',
  orange: '#e5484d',       // red 9 · 漫画红（cel 的暖色主角就是红）
  orangeInk: '#ce2c31',    // red 11
  orangeLight: 'rgba(229,72,77,0.16)',
  green: '#46a758',        // grass 9
  greenInk: '#2a7e3b',     // grass 11
  greenLight: 'rgba(70,167,88,0.16)',
  gold: '#ffe629',         // yellow 9 · 漫画黄（色块 + 墨字）
  goldInk: '#956703',      // yellow 11 → 12 混 10%
  red: '#dc3e42',          // red 10
  redInk: '#ce2c31',       // red 11
  navy: '#113264',         // blue 12
  paper: '#ffffff',        // 分镜格白
  paperWarm: '#fdfdf9',    // yellow 1
  paperBase: '#fefce9',    // yellow 2 · 米白漫画纸
  line: 'rgba(17,17,17,0.50)',
  lineOrange: 'rgba(229,72,77,0.62)',
  lineBlue: 'rgba(0,144,255,0.62)',
  lineGreen: 'rgba(70,167,88,0.62)',
  white: '#ffffff',
  // 场景层柔色
  skyTint: '#e6f4fe',      // blue 3
  blueLine: 'rgba(0,144,255,0.42)',
  dotIdle: '#cfceca',      // sand 7
  mutedFill: 'rgba(99,99,94,0.30)',
  mutedBar: 'rgba(99,99,94,0.26)',
  mutedWash: 'rgba(99,99,94,0.16)',
  orangeSoft: '#f4a9aa',   // red 7
  orangeDeep: '#ce2c31',   // red 11
  gaugeTrack: 'rgba(17,17,17,0.20)',
  greenGlow: 'rgba(70,167,88,0.35)',
  stageTint: 'rgba(255,250,184,0.45)',
  headerAccent: '#111111',
  headerSub: '#63635e',
};

const aesthetic: Theme['aesthetic'] = {
  subtitleSafeWidth: 1334, paperRadius: 8, paperOutline: 3,
  textureOpacity: 0, gridOpacity: 0, gradeWarmth: 0, gradeVignette: .03,
  subtitleWeight: 700, subtitleLetterSpacing: 1.6, subtitlePadX: 78,
};

// 硬偏移墨影：比旧版更有冲击力（4px 起步，举起时加到 8px），仍然无模糊。
const paperShadow = (lift: number) =>
  `${4 + 4 * lift}px ${4 + 4 * lift}px 0 ${palette.ink}`;

// 分镜格微旋转（LOCKED）：由卡片位置哈希出 ±0.7° 内的微倾角，灵动且不歪扭
const panelTilt = (style?: React.CSSProperties) => {
  const left = Number(style?.left ?? 0), top = Number(style?.top ?? 0);
  return (((Math.round(left) + Math.round(top)) % 5) - 2) * 0.35;
};

// 背景（LOCKED）：三张固定资产图，均为 2560×1440（与 16:9 画布 1:1 逐像素），渲染时 cover。
// 中央约 70% 是空白漫画纸（内容安全区），装饰只在四角：
//   main    左下黑网点扇 + 黄色爆炸星，右上速度线，右下红网点 + 蓝星，左上蓝网点
//   chapter 左右边缘短速度线，右上黄色爆炸星，左上红网点，左下红星，右下蓝网点
//   quiet   最安静：四角各一个小元素，给信息密集的镜头
// 禁止改回代码自绘背景；换图要连同 manifests/visual-assets.json 的 sha256 一起换。
const BACKGROUNDS: Record<BgVariant, string> = {
  main: 'bg/bg-cel-main.jpg',
  chapter: 'bg/bg-cel-chapter.jpg',
  quiet: 'bg/bg-cel-quiet.jpg',
};

const Background: Theme['Background'] = ({variant = 'main'}) => (
  <AbsoluteFill style={{background: palette.paperBase}}>
    <Img src={staticFile(BACKGROUNDS[variant])} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
  </AbsoluteFill>
);

const Paper: Theme['Paper'] = ({children, style, lift = 0, borderColor}) => {
  const {transform, ...rest} = style ?? {};
  const tilt = panelTilt(style);
  return <div style={{position: 'absolute', backgroundColor: palette.paper, border: `${aesthetic.paperOutline}px solid ${borderColor || palette.ink}`, borderRadius: aesthetic.paperRadius, color: palette.ink, boxShadow: paperShadow(lift), ...rest, transform: `${transform ? transform + ' ' : ''}rotate(${tilt}deg)`}}>{children}</div>;
};

// 赛璐璐只保留极轻墨角暗角，不加暖色柔光。
const Grade: React.FC = () => <AbsoluteFill style={{pointerEvents: 'none', zIndex: 190}}>
  <AbsoluteFill style={{boxShadow: `inset 0 0 120px rgba(17,17,17,${aesthetic.gradeVignette})`}} />
</AbsoluteFill>;

// 字幕：白底对白框 + 3px 墨边 + 黄色硬偏移影（漫画对白框的「贴纸」感），左侧一枚红色三角指针。
const SubtitleChrome: Theme['SubtitleChrome'] = ({mode, children}) =>
  <div style={{position: 'absolute', left: 0, right: 0, bottom: 44, zIndex: 200, display: 'flex', justifyContent: 'center'}}>
    <div style={{position: 'relative', background: palette.white, border: `3px solid ${palette.ink}`, boxShadow: `5px 5px 0 ${palette.gold}, 5px 5px 0 3px ${palette.ink}`, padding: '10px 36px', maxWidth: mode.safe}}>
      <div style={{fontFamily: 'Kai', fontSize: mode.subFont, fontWeight: 700, lineHeight: 1.18, letterSpacing: 1.6, color: palette.ink, whiteSpace: 'nowrap'}}>
        {children}
      </div>
    </div>
  </div>;

// 页眉底板：漫画旁白框（白底 + 3px 墨边 + 墨色硬影），压在右上角速度线 / 爆炸星上也清楚可读。
const headerPlate: React.CSSProperties = {
  background: palette.white, border: `3px solid ${palette.ink}`, boxShadow: `4px 4px 0 ${palette.ink}`, padding: '10px 18px 9px',
};

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
          <polygon points={pts.join(' ')} fill={color} stroke={palette.ink} strokeWidth={3.6} strokeLinejoin="round" />
        </svg>
        <div style={{position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', fontFamily: 'Kai', fontWeight: 700, fontSize: size * 0.24, color: palette.ink}}>{text}</div>
      </div>
    );
  };

// 背景装饰区（LOCKED 声明）：三张背景图里装饰所占矩形的**并集**（1920×1080 设计坐标）。
// 内容压到这些区域时必须坐在 CoverPanel 上，否则墨色文字会被网点和速度线吃掉。
const backgroundDecorZones = [
  {x: 0, y: 760, w: 300, h: 320},      // 左下：网点扇 + 黄色爆炸星 / 红星
  {x: 1580, y: 700, w: 340, h: 380},   // 右下：红/蓝网点 + 蓝星 + 短速度线
  {x: 1540, y: 0, w: 380, h: 340},     // 右上：速度线 / 黄色爆炸星
  {x: 0, y: 0, w: 240, h: 230},        // 左上：蓝/红网点楔
  {x: 0, y: 290, w: 110, h: 440},      // 左缘：chapter 的短速度线
  {x: 1810, y: 330, w: 110, h: 420},   // 右缘：chapter 的短速度线
];

export const THEME: Theme = {
  id: 'cel',
  palette,
  aesthetic,
  paperShadow,
  backgrounds: BACKGROUNDS,
  Background,
  Paper,
  Grade,
  SubtitleChrome,
  backgroundDecorZones,
  headerPlate,
  extras: {Burst},
};
