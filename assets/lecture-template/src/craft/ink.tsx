// ============================================================================
// craft/ink.tsx · 墨线与手写（3.3.0）
//
//   InkPath       一笔有压感的墨线，按进度 p 从起点「画出来」（perfect-freehand，MIT，steveruizok）
//   Underline     手划的下划线 / 圈注（InkPath 的便捷封装）
//   HandNote      钢笔小注 + 引线：引线先长到标本，字再从左往右写出（批注层）
//   HandLettering 中文字真的被「写」出来：霞鹜文楷字形轮廓（opentype.js，MIT）先描边、再填墨
//
// 纪律（与引擎一致）：只用帧号驱动，无随机数（抖动全部来自 @remotion/noise 的确定性噪声 + seed）；
// 文字颜色用 THEME.palette.ink / *Ink；画内必读文字 ≥ CRAFT_TYPE.label（48 设计 px ≈ 64 px@1440）。
// ============================================================================
import React, {useEffect, useState} from 'react';
import {continueRender, delayRender, staticFile, interpolate, Easing} from 'remotion';
import {getStroke} from 'perfect-freehand';
import {getLength, getPointAtLength} from '@remotion/paths';
import {noise2D} from '@remotion/noise';
import {parse as parseFont, type Font} from 'opentype.js';
import {THEME} from '../theme/active';

const C = THEME.palette;
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
export const easeInk = Easing.bezier(0.45, 0, 0.2, 1);

/** 手作场景的字号阶梯（设计 px）。画内必读标签 ≥ label（≈ 64 px@1440，用户规范），每帧 ≤ 3 个。 */
export const CRAFT_TYPE = {hero: 132, display: 88, title: 64, label: 48, note: 44, micro: 30} as const;

/** 帧 → 0..1 进度（at 起，dur 帧内画完）。 */
export const prog = (f: number, at: number, dur: number) => interpolate(f, [at, at + Math.max(1, dur)], [0, 1], {...clamp, easing: easeInk});

/** 把 SVG 路径采样成点列（等弧长），给 InkPath 用。 */
export const samplePath = (d: string, n = 64): [number, number][] => {
  const L = getLength(d);
  return Array.from({length: n + 1}, (_, i) => {const p = getPointAtLength(d, (L * i) / n) ?? {x: 0, y: 0}; return [p.x, p.y];});
};

/** 手的抖动：沿法线方向的低频噪声位移（确定性）。 */
const wobble = (pts: [number, number][], amp: number, seed: string) => pts.map(([x, y], i) => {
  const a = i / Math.max(1, pts.length - 1);
  return [x + amp * noise2D(seed + 'x', a * 3, 0), y + amp * noise2D(seed + 'y', a * 3, 1)] as [number, number];
});

/** perfect-freehand 轮廓 → 闭合 SVG path。 */
export const strokeToPath = (outline: number[][]) => {
  if (outline.length < 2) return '';
  const d = outline.reduce((acc, [x0, y0], i, arr) => {const [x1, y1] = arr[(i + 1) % arr.length]; acc.push(x0, y0, (x0 + x1) / 2, (y0 + y1) / 2); return acc;}, ['M', ...outline[0], 'Q'] as (string | number)[]);
  return d.join(' ') + ' Z';
};

export type InkPathProps = {
  /** 二选一：SVG 路径（设计坐标）或点列 */
  d?: string; points?: [number, number][];
  /** 0..1 画到哪里（用 prog(f, at, dur) 算） */
  p: number;
  size?: number; color?: string; opacity?: number;
  /** 笔压随速度变细的程度（0 = 马克笔等粗，0.6 = 蘸水笔） */
  thinning?: number; wobbleAmp?: number; seed?: string;
};

/** 一笔墨线。整条线的点列先算好，p 只截取前缀 → 任一帧可单独渲染。 */
export const InkPath: React.FC<InkPathProps> = ({d, points, p, size = 7, color = THEME.craft?.inkLine ?? C.ink, opacity = 0.92, thinning = 0.55, wobbleAmp = 1.6, seed = 'ink'}) => {
  if (p <= 0) return null;
  const base = points ?? (d ? samplePath(d, 96) : []);
  const pts = wobble(base, wobbleAmp, seed);
  const n = Math.max(2, Math.round(pts.length * Math.min(1, p)));
  const outline = getStroke(pts.slice(0, n), {size, thinning, smoothing: 0.6, streamline: 0.4, simulatePressure: true, last: p >= 1,
    start: {taper: size * 2.5}, end: {taper: p >= 1 ? size * 3 : 0}});
  const xs = pts.map((q) => q[0]), ys = pts.map((q) => q[1]);
  const pad = size * 3;
  const minX = Math.min(...xs) - pad, minY = Math.min(...ys) - pad, W = Math.max(...xs) - minX + pad, H = Math.max(...ys) - minY + pad;
  return <svg style={{position: 'absolute', left: minX, top: minY, overflow: 'visible', pointerEvents: 'none'}} width={W} height={H} viewBox={`${minX} ${minY} ${W} ${H}`} aria-hidden>
    <path d={strokeToPath(outline)} fill={color} opacity={opacity} />
  </svg>;
};

/** 手划下划线：x1→x2，略带上扬与抖动。 */
export const Underline: React.FC<{x: number; y: number; w: number; p: number; color?: string; size?: number; seed?: string}> = ({x, y, w, p, color = THEME.craft?.accent ?? C.orange, size = 8, seed = 'ul'}) =>
  <InkPath d={`M ${x} ${y} C ${x + w * 0.3} ${y - 6}, ${x + w * 0.7} ${y + 5}, ${x + w} ${y - 4}`} p={p} color={color} size={size} seed={seed} />;

/** 手划椭圆圈注（圈一个东西）。 */
export const InkCircle: React.FC<{cx: number; cy: number; rx: number; ry: number; p: number; color?: string; size?: number; seed?: string}> = ({cx, cy, rx, ry, p, color = THEME.craft?.accent ?? C.orange, size = 7, seed = 'circ'}) => {
  // 画 1.12 圈（首尾交叠，手圈的样子），起笔在左上
  const pts: [number, number][] = Array.from({length: 97}, (_, i) => {const a = -2.4 + (i / 96) * Math.PI * 2 * 1.12; const k = 1 + 0.04 * Math.sin(i / 9); return [cx + rx * k * Math.cos(a), cy + ry * k * Math.sin(a)];});
  return <InkPath points={pts} p={p} color={color} size={size} seed={seed} />;
};

export type HandNoteProps = {
  f: number; at: number;
  /** 文字左上角（设计坐标） */
  x: number; y: number; text: string;
  /** 引线终点（指向的东西）；不写就没有引线 */
  to?: {x: number; y: number};
  size?: number; color?: string; family?: string; maxWidth?: number;
};

/** 钢笔批注：引线 8 帧长到目标，字随后从左往右「写」出（clip），纸色光晕保证 ≥ 7:1。 */
export const HandNote: React.FC<HandNoteProps> = ({f, at, x, y, text, to, size = CRAFT_TYPE.note, color = C.ink, family = THEME.craft?.handFamily ?? 'Kai', maxWidth = 900}) => {
  const lead = to ? prog(f, at, 10) : 1;
  const write = prog(f, at + (to ? 8 : 0), Math.max(10, text.length * 2.2));
  if (f < at) return null;
  const halo = C.paper;
  const startX = x - 10, startY = y + size * 0.62;
  return <>
    {to && <InkPath d={`M ${startX} ${startY} Q ${(startX + to.x) / 2} ${Math.min(startY, to.y) - 30}, ${to.x} ${to.y}`} p={lead} size={4} color={color} thinning={0.3} seed={`hn${x}${y}`} />}
    {to && lead >= 1 && <div style={{position: 'absolute', left: to.x - 6, top: to.y - 6, width: 12, height: 12, borderRadius: 6, background: color, opacity: 0.85}} />}
    <div style={{position: 'absolute', left: x, top: y, maxWidth, fontFamily: family, fontSize: size, fontWeight: 700, color, lineHeight: 1.2, whiteSpace: 'nowrap',
      clipPath: `inset(-20% ${100 - write * 100}% -20% -4%)`, textShadow: `0 0 8px ${halo}, 0 0 3px ${halo}`}}>{text}</div>
  </>;
};

// ---- HandLettering：字形轮廓 → 「写」出来 -------------------------------------------------
let FONT_CACHE: Promise<Font> | null = null;
const loadKai = () => FONT_CACHE ??= fetch(staticFile('LXGWWenKaiLite-Medium.ttf')).then((r) => r.arrayBuffer()).then((b) => parseFont(b));

/**
 * 一行中文被写出来：先沿字形轮廓描墨（stroke-dash），再填墨。适合片名 / 关键词 / 结论（≤ 10 字）。
 * 字体：随包的 LXGW WenKai Lite Medium（OFL）。只用帧号驱动；字形解析在 delayRender 里完成。
 */
export const HandLettering: React.FC<{f: number; at: number; text: string; x: number; y: number; size?: number; color?: string; perChar?: number}> =
  ({f, at, text, x, y, size = CRAFT_TYPE.display, color = C.ink, perChar = 9}) => {
    const [font, setFont] = useState<Font | null>(null);
    const [handle] = useState(() => delayRender('HandLettering: parse LXGW WenKai', {timeoutInMilliseconds: 60000}));
    useEffect(() => {let live = true; loadKai().then((ft) => {if (live) {setFont(ft); continueRender(handle);}}).catch((e) => {throw e;}); return () => {live = false;};}, [handle]);
    if (!font) return null;
    let cursor = 0;
    const glyphs = [...text].map((ch, i) => {
      const path = font.getPath(ch, cursor, size, size);
      const adv = font.getAdvanceWidth(ch, size);
      cursor += adv;
      const d = path.toPathData(2);
      const t0 = at + i * perChar;
      const outline = prog(f, t0, perChar * 1.4);
      const fill = prog(f, t0 + perChar * 0.9, perChar * 0.8);
      // pathLength=100 把每个字的轮廓总长归一，描边进度与字的笔画多少无关
      return <path key={i} d={d} fill={color} fillOpacity={fill} stroke={color} strokeWidth={Math.max(1.5, size / 48)} strokeLinejoin="round"
        pathLength={100} strokeDasharray={100} strokeDashoffset={100 * (1 - outline)} opacity={outline > 0 ? 1 : 0} />;
    });
    return <svg style={{position: 'absolute', left: x, top: y, overflow: 'visible'}} width={cursor} height={size * 1.25} aria-label={text}>{glyphs}</svg>;
  };
