import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import type {BgVariant, ChromeProps, Theme} from './types';

// ============================================================================
// 手作皮肤共用件（3.3.0，LOCKED）：journal / papercut / archive 三套皮肤共用的背景、纸纤维、
// 字幕衬底与章节标识写法。皮肤之间只换「材料参数」，不在场景层做任何风格判断。
//
// 方法来源：材质 + 字幕 + 运镜 + 声音 + 原生动作的「配方」拆法，借鉴 lemo-opuscar 的 styles/*/STYLE.md
// （MIT，© 2026 LemoLab，https://github.com/lemomo-ai/lemo-opuscar）。此处为 Remotion 重写，无代码复制。
// ============================================================================

/** 位图背景（2560×1440，与画布逐像素），由 scripts/dev/make-craft-textures.py 确定性生成。 */
export const makeBackground = (base: string, files: Record<BgVariant, string>): Theme['Background'] =>
  ({variant = 'main'}) => (
    <AbsoluteFill style={{background: base}}>
      <Img src={staticFile(files[variant])} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    </AbsoluteFill>
  );

/** 纸纤维覆盖层：叠在卡片里，让「白卡」变成「一张纸」。opacity 0 = 不画。 */
export const FibreOverlay: React.FC<{opacity: number; radius?: number}> = ({opacity, radius = 0}) =>
  opacity <= 0 ? null : <div aria-hidden style={{position: 'absolute', inset: 0, borderRadius: radius, pointerEvents: 'none',
    backgroundImage: `url(${staticFile('craft/fibre-tile.png')})`, backgroundSize: '512px 512px', opacity, mixBlendMode: 'multiply'}} />;

/** 由卡片位置哈希出的确定性微倾角（±maxDeg），手放上去的纸不会横平竖直。 */
export const tiltOf = (style: React.CSSProperties | undefined, maxDeg: number) => {
  const left = Math.round(Number(style?.left ?? 0)), top = Math.round(Number(style?.top ?? 0));
  const h = ((left * 73856093) ^ (top * 19349663)) >>> 0;
  return ((h % 1000) / 1000 * 2 - 1) * maxDeg;
};

/** 半透明胶带（日式和纸胶带的质感：边缘锯齿、透出下面的纸）。 */
export const TapeStrip: React.FC<{x: number; y: number; w?: number; rot?: number; color?: string}> =
  ({x, y, w = 120, rot = -8, color = 'rgba(232,214,170,0.78)'}) =>
    <div aria-hidden style={{position: 'absolute', left: x, top: y, width: w, height: 30, background: color, transform: `rotate(${rot}deg)`,
      boxShadow: '0 1px 2px rgba(60,40,10,0.18)', zIndex: 2,
      clipPath: 'polygon(0 6%,4% 0,8% 8%,12% 0,16% 6%,20% 0,80% 0,84% 7%,88% 0,92% 6%,96% 0,100% 8%,100% 94%,96% 100%,92% 92%,88% 100%,84% 94%,80% 100%,20% 100%,16% 93%,12% 100%,8% 94%,4% 100%,0 92%)'}} />;

/**
 * 字幕：没有胶囊、没有色块——墨字直接写在纸上，下面垫一层纸色柔光晕（任何底上都 ≥7:1）。
 * size = 设计 px（72 = 交付 96 px）。family 缺省 'NotoSerifSC'（Noto Serif SC Bold；别叫 'Serif'——那是 CSS 通用族名关键字，会被解析成系统衬线体）。
 */
export const PaperSubtitle = (o: {ink: string; halo: string; family?: string; size: number; bottom?: number; letterSpacing?: number; plate?: React.CSSProperties}):
  Theme['SubtitleChrome'] => ({mode, children}) =>
  <div style={{position: 'absolute', left: 0, right: 0, bottom: o.bottom ?? 36, zIndex: 200, display: 'flex', justifyContent: 'center'}}>
    <div style={{position: 'relative', padding: '4px 34px 8px', maxWidth: mode.safe, ...o.plate}}>
      {!o.plate && <div aria-hidden style={{position: 'absolute', inset: '-10px -30px', borderRadius: 60,
        background: `radial-gradient(ellipse at center, ${o.halo} 0%, ${o.halo} 52%, transparent 76%)`, filter: 'blur(6px)'}} />}
      <div style={{position: 'relative', fontFamily: o.family ?? 'NotoSerifSC,Kai', fontSize: o.size, fontWeight: 700, lineHeight: 1.16,
        letterSpacing: o.letterSpacing ?? 2, color: o.ink, whiteSpace: 'nowrap',
        textShadow: o.plate ? undefined : `0 0 10px ${o.halo}, 0 0 4px ${o.halo}`}}>
        {children}
      </div>
    </div>
  </div>;

/** 章节标识的公共入场：本章开头 0→1，带 2 帧墨迹延迟。 */
export const chromeIn = (p: ChromeProps) => Math.max(0, Math.min(1, (p.local - 4) / 14));
