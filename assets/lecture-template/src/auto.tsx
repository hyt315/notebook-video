import React, {useEffect} from 'react';
import {Easing, cancelRender, interpolate} from 'remotion';
import {THEME} from './theme/active';
import {isHandmadeMedium} from './theme/medium';
import {KineticNumber, drawOn} from './cinema';
import {REDUCED_MOTION} from './reduced-motion';
import {STORY} from './story';
import {CUSTOM} from './custom';
import {MediaFrame} from './media-frame';
import {SketchLayer} from './linework/sketch';
import type {SketchSpec} from './linework/types';
import {HandLettering, HandNote, InkCircle, InkPath, Underline} from './craft/ink';
import {Seal} from './craft/paper';
import {ArchivePhoto, LoupeMedia} from './craft/media';

// ============================================================================
// auto.tsx · 3.2.0 内容驱动的镜头渲染器（AutoShot）
//
// story.json（纯内容）→ scripts/compose-story.py（排版 / 关键词 / 相机 / 自动修）→ src/story.ts → 这里画。
// 本层只负责「画」，几何全部在 compose-story 里算好（门禁也在那里跑），所以弱模型写不坏版面。
//
// 克制原则：
//   · 出现（3.5.1 草稿纸）：沿阅读方向左→右展开，线性；不淡入、不上浮、不回弹。见 references/reveal-rules.md
//   · 强调 = 底色带 + 左侧标记条 + 加粗（不只靠颜色，色弱观众也看得出）；同时只强调一个元素，其余略暗。
//   · 文字色一律走主题的 *Ink 变体（WCAG AA ≥4.5:1），原色只做填充 / 描边。
//   · 帧的纯函数：没有任何 useState / 随机 / 实时动画。
// ============================================================================

const C = THEME.palette;
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const ease = Easing.bezier(0.16, 1, 0.3, 1);

export type Elem = {
  id: string; kind: string; x: number; y: number; w: number; h: number; text: string; size: number; role: string;
  at: number; lines?: string[]; lh?: number; align?: string; [k: string]: any;
};
export type FocusOut = {id: string; at: number; until: number; term: string; sub: {x: number; y: number; w: number; h: number} | null; cam: boolean};
export type Tip = {term: string; x: number; y: number; w: number; h: number; lines: string[]; size: number; at: number; until: number; below: boolean};
export type StoryShot = {
  layout: string; variant: string; elements: Elem[]; focus: FocusOut[]; tips: Tip[];
  lines: number[]; lineEnds: number[]; think: number; custom: string | null; icons: number;
  /** 3.5.0：线稿层（compose 已把 acts 换算成本镜帧号，并给好画面方框） */
  sketch?: (SketchSpec & {box: {x: number; y: number; w: number; h: number}}) | null;
  /** 3.5.0：讲解层的圈注 / 下划线 / 引线 / 手写小字（design 坐标） */
  annotate?: Array<{kind: 'circle' | 'underline' | 'arrow' | 'note'; x: number; y: number; w: number; h: number; at: number; text?: string; seed: string}> | null;
};

/** 色调 → {填充, 文字安全色, 浅底}。文字永远用 ink（自动满足对比度）。 */
export const tone = (t?: string) => {
  switch (t) {
    case 'blue': return {fill: C.blue, ink: C.blueInk, light: C.blueLight};
    case 'green': return {fill: C.green, ink: C.greenInk, light: C.greenLight};
    case 'gold': return {fill: C.gold, ink: C.goldInk, light: C.orangeLight};
    case 'red': return {fill: C.red, ink: C.redInk, light: C.orangeLight};
    default: return {fill: C.orange, ink: C.orangeInk, light: C.orangeLight};
  }
};

/** 出现（3.5.1 草稿纸）：沿阅读方向左→右展开，线性，dur 帧；不淡入、不上浮、不缩放。见 references/reveal-rules.md
 *  reduced-motion（P2-21）：直接到位——元素仍按 `at` 出现（内容顺序不变），只是不动。 */
export const enter = (f: number, at: number, _rise = 14, dur = 18): React.CSSProperties => {
  if (REDUCED_MOTION) return {opacity: f >= at ? 1 : 0};
  const p = interpolate(f, [at, at + dur], [0, 1], {...clamp, easing: Easing.linear});
  if (p <= 0) return {opacity: 0};
  return {clipPath: `inset(-6% ${((1 - p) * 100).toFixed(2)}% -6% -2%)`};
};
/** 展开时长：clamp(字数 × 4, 12, 45) 帧；没字的按宽度 / 40。与 scripts/story_acts.py grow_dur() 同一公式。 */
export const growDur = (e: {text?: string; lines?: string[]; w: number}) => {
  const n = ((e.lines ?? []).join('') || e.text || '').length;
  return Math.max(12, Math.min(45, n > 0 ? n * 4 : Math.round(e.w / 40)));
};

/** 关键词强调权重（0..1）：说到这个词时 8 帧升起，until 后 12 帧落下。 */
export const hiWeight = (shot: StoryShot, id: string, f: number) => {
  let w = 0;
  for (const k of shot.focus) {
    if (k.id !== id || k.sub) continue;
    const up = interpolate(f, [k.at - 2, k.at + 6], [0, 1], clamp);
    const down = interpolate(f, [k.until, k.until + 12], [1, 0], clamp);
    w = Math.max(w, Math.min(up, down));
  }
  return w;
};
/** 当前是否有别的元素被强调（用于把其余元素轻微压暗：同屏焦点 ≤3）。 */
const anyHi = (shot: StoryShot, f: number) => Math.max(0, ...shot.focus.filter((k) => !k.sub).map((k) => Math.min(interpolate(f, [k.at - 2, k.at + 6], [0, 1], clamp), interpolate(f, [k.until, k.until + 12], [1, 0], clamp))));

const Lines: React.FC<{lines?: string[]; text: string; size: number; lh?: number; color?: string; weight?: number; align?: string}> = ({lines, text, size, lh = 1.35, color = C.ink, weight = 400, align}) => {
  // 中文行高下限 1.42：汉字字形（含标点、括号）在高过 lineHeight 时会直接压到上一行。
  // 实测（flow 节点，字号 46）：lh=1.25 压住 414px²；1.32 仍压 274px²（「1665/借来」）
  // 和 282px²（「今天/住户」，纯汉字——所以这不是「数字字形特殊」，是 46px 中文本身就需要更高行距）。
  // 1.42（= 65.3px）之后两行彻底分开。这里统一兜底，而不是在每个调用点记一个魔法数。
  // 行高下限与排版端 SAFE_LH（scripts/compose-story.py）必须同数——
  // validate-skill-consistency 的 'SAFE_LH compose vs auto.tsx safeLh' 钉死两边。
  // 排版按更小的 lh 算框高 → 下一行压进上一行的行盒（OverlapGate 硬拦）。
  const safeLh = Math.max(lh, 1.42);
  return (
  <div style={{position: 'relative', fontSize: size, lineHeight: safeLh, color, fontWeight: weight, textAlign: (align as any) ?? 'left', whiteSpace: 'nowrap'}}>
    {(lines ?? [text]).map((l, i) => <div key={i}>{l}</div>)}
  </div>
  );
};

// ---------------------------------------------------------------- 3.6.2 手作皮肤的纸感变体
// 问题（3.6.1 样张实测）：手账纸上，compare 的 panel / flow 的 node 仍是「白卡片 + 圆角 + 2px 边框」，
// 一眼就是贴上去的 PPT 组件。纸上的东西应该是：一张裁下的纸、一条和纸胶带、两条淡彩，
// 勾边用墨而不是 UI 描边。只在手作皮肤（THEME.craft 存在）下换，flat / cel 保持原样。
// 纸卡、胶带、倾角与墨圈只属于手作媒介。flat / cel 也声明 craft（线稿色、字体、转场），
// 但那是能力配置，不是“手作”；旧版把两者混成一个布尔值，导致中立皮肤也长出纸卡。
const HANDMADE_MEDIUM = isHandmadeMedium(THEME);
/** 纸片倾角：由元素 id 确定性算出（±0.8°），同一元素每一帧都一样。 */
const tiltOf = (id: string) => {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) % 1000;
  return ((h / 1000) * 2 - 1) * 0.8;
};
const paperCard: React.CSSProperties = HANDMADE_MEDIUM
  ? {background: C.paper, borderRadius: 2, border: '1px solid rgba(70,50,25,0.16)',
     boxShadow: '0 3px 10px rgba(70,50,25,0.22), 0 0 0 1px rgba(70,50,25,0.06)'}
  : {background: C.paper, borderRadius: 16, border: `2px solid ${C.line}`};
/** 和纸胶带：贴在纸片左上角，半透明淡彩，随纸片一起倾。
 *  0.5 的不透明度在纸色底上几乎看不见（实测截图里完全没存在感），
 *  改成 0.72 + 两端撕口 + 一条亮边——「贴上去的」这件事必须一眼能认出来。 */
const Tape: React.FC<{color: string}> = ({color}) => (
  <div style={{position: 'absolute', left: -22, top: -13, width: 104, height: 28, background: color,
    opacity: 0.72, transform: 'rotate(-3.5deg)', borderRadius: 1, pointerEvents: 'none',
    boxShadow: '0 1px 3px rgba(70,50,25,0.18), inset 0 0 0 1px rgba(255,255,255,0.25)',
    WebkitClipPath: 'polygon(2% 0, 100% 3%, 98% 100%, 0 96%)', clipPath: 'polygon(2% 0, 100% 3%, 98% 100%, 0 96%)'}} />
);
/** 纸片上的强调：墨圈（手画的、略不齐）而不是 UI 描边 + 抬升阴影。 */
const InkFrame: React.FC<{w: number; t?: string; pad?: number; rad?: number}> = ({w, t, pad = 10, rad = 4}) => {
  if (w <= 0.01) return null;
  const tt = tone(t);
  // 手作：墨线勾一圈（不粗、不发光，随强调淡入）；组件皮肤：仍是描边 + 抬升阴影
  return <div style={{position: 'absolute', inset: -pad, borderRadius: rad, opacity: w,
    border: `2.5px solid ${HANDMADE_MEDIUM ? tt.ink : tt.fill}`,
    boxShadow: HANDMADE_MEDIUM ? 'none' : `0 10px 28px rgba(0,0,0,${0.12 * w})`, boxSizing: 'border-box'}} />;
};

/** 强调：沿用默认组件风格的强调语言 —— 强调色描边 + 轻微抬升阴影（配合镜头推近），不用底色带 / 标记条。 */
const HiBox: React.FC<{w: number; t?: string; pad?: number; radius?: number}> = ({w, t, pad = 10, radius = 14}) => {
  if (w <= 0.01) return null;
  const tt = tone(t);
  return <div style={{position: 'absolute', inset: -pad, borderRadius: radius, border: `3px solid ${tt.fill}`, boxShadow: `0 10px 28px rgba(0,0,0,${0.12 * w})`, opacity: w, boxSizing: 'border-box'}} />;
};

const Box: React.FC<{e: Elem; f: number; dim: number; style?: React.CSSProperties; children: React.ReactNode; rise?: number}> = ({e, f, dim, style, children, rise}) => (
  <div data-auto-el={e.id} style={{position: 'absolute', left: e.x, top: e.y, width: e.w, height: e.h, ...enter(f, e.at, rise, (e as any).reveal ? 1 : ((e as any).dur ?? growDur(e))), ...style}}>
    <div style={{position: 'absolute', inset: 0, opacity: dim}}>{children}</div>
  </div>
);

/** 逐字呈现：把一行字按字符切开，按帧一个个放出来。
 *
 * 为什么不是整块淡入：整块出现等于「这一句是一张图」，观众要等它浮上来才读；
 * 逐字出现是「这句话正在被写」，读到哪跟到哪。而且它天然把节奏锁在旁白上——
 * 一旦说得快，字也出得快，不需要另配一套时间轴。
 *
 * mode：type = 打字机（只显形，不动）；slide = 从上方滑下（位移 0.55em，6 帧落定）。
 * dur 是本句可用的帧数，per = dur / 字数，最慢 3 帧/字、最快 0.6 帧/字。
 */
const RevealText: React.FC<{lines: string[]; size: number; lh: number; color: string; weight: number;
  align?: string; f: number; at: number; dur: number; mode: 'type' | 'slide'}> = ({lines, size, lh, color, weight, align, f, at, dur, mode}) => {
  const chars = lines.reduce((n, l) => n + [...l].length, 0) || 1;
  const per = Math.max(0.6, Math.min(3, (dur || chars * 1.5) / chars));
  let k = 0;
  return (
    <div style={{position: 'relative', fontSize: size, lineHeight: Math.max(lh, 1.42), color, fontWeight: weight,
      textAlign: (align as any) ?? 'left', whiteSpace: 'nowrap'}}>
      {lines.map((l, i) => (
        <div key={i}>
          {[...l].map((ch) => {
            const q = (f - (at + k * per)) / (mode === 'slide' ? 6 : 1.2);
            k += 1;
            // reduced-motion：不逐字显现，整句一起到位（内容顺序不变，只是不动）
            const o = REDUCED_MOTION ? (f >= at ? 1 : 0) : Math.max(0, Math.min(1, q));
            if (o <= 0) return <span key={`${i}-${k}`} style={{opacity: 0}}>{ch}</span>;
            return <span key={`${i}-${k}`} style={{display: 'inline-block', opacity: mode === 'type' ? 1 : o,
              transform: mode === 'slide' ? `translateY(${(1 - Math.min(1, Math.max(0, q))) * -0.55}em)` : undefined}}>{ch}</span>;
          })}
        </div>
      ))}
    </div>
  );
};

/** 手划下划线：跟着旁白起笔，从第一个字划到最后一个字。
 *  纸上的强调是笔的动作（划、圈、加墨），不是相机的动作（放大）。
 *  讲到那一句时才起笔，之后常驻——不做来回跳，那是空动。 */
const InkRule: React.FC<{f: number; at: number; w: number; y: number; color: string}> = ({f, at, w, y, color}) => {
  const p = interpolate(f, [at, at + 9], [0, 1], clamp);
  if (p <= 0) return null;
  const L = Math.max(24, w + 6);
  return (
    <svg width={L + 10} height={18} style={{position: 'absolute', left: -3, top: y, overflow: 'visible', pointerEvents: 'none'}} aria-hidden>
      <path d={`M2 8 C ${L * 0.28} 4, ${L * 0.62} 12, ${L} 6`} stroke={color} strokeWidth={4} fill="none"
        strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} opacity={0.85} />
    </svg>
  );
};

// ⚠ 泛型族（monospace）必须排在最后：CSS 里泛型族之后的名字会被整条忽略。
// 旧值 `…,monospace,Kai` 于是让 Kai 从未参与回退——Linux 渲染机上 Consolas/Menlo 都不在，
// monospace 落到 DejaVu Sans Mono（无 CJK 字面），代码注释里的中文就成了豆腐块。
const CODE_FONT = "'JetBrains Mono','DejaVu Sans Mono',Consolas,Menlo,Kai,monospace";
const codeTokens = (line: string) => {
  const out: {t: string; c: string}[] = [];
  const re = /(#.*$|\/\/.*$)|("[^"]*"|'[^']*')|\b(def|return|import|from|class|if|else|for|in|const|let|function|await|async|new)\b|(@[\w.]+)|(\d+(?:\.\d+)?)/g;
  let last = 0, m: RegExpExecArray | null;
  while ((m = re.exec(line))) {
    if (m.index > last) out.push({t: line.slice(last, m.index), c: C.ink});
    out.push({t: m[0], c: m[1] ? C.muted : m[2] ? C.greenInk : m[3] ? C.blueInk : m[4] ? C.orangeInk : C.goldInk});
    last = m.index + m[0].length;
  }
  if (last < line.length) out.push({t: line.slice(last), c: C.ink});
  return out;
};

const ElemView: React.FC<{e: Elem; f: number; shot: StoryShot; all: Elem[]}> = ({e, f, shot}) => {
  const w = hiWeight(shot, e.id, f);
  const others = anyHi(shot, f);
  const dim = e.kind === 'codebox' || e.kind === 'media' ? 1 : 1 - 0.32 * Math.max(0, others - w);
  const tt = tone(e.tone);
  const bold = w > 0.5 ? 700 : undefined;
  switch (e.kind) {
    case 'text': {
      const color = e.role === 'muted' ? C.muted : C.ink;
      const weight = e.role === 'display' || e.role === 'title' ? 700 : e.role === 'accent' ? 700 : 400;
      const mk = (e as any).mark;
      const rv = (e as any).reveal;
      const body = rv === 'type' || rv === 'slide'
        ? <RevealText lines={e.lines ?? [e.text]} size={e.size} lh={e.lh ?? 1.35} color={e.role === 'accent' ? C.orangeInk : color}
            weight={bold ?? weight} align={e.align} f={f} at={(e as any).revealAt ?? e.at} dur={(e as any).revealDur ?? 30} mode={rv} />
        : <Lines lines={e.lines} text={e.text} size={e.size} lh={e.lh} color={e.role === 'accent' ? C.orangeInk : color} weight={bold ?? weight} align={e.align} />;
      return <Box e={e} f={f} dim={dim} rise={shot.layout === 'statement' ? 0 : 14}><HiBox w={w} />{body}
        {typeof mk === 'number' && <InkRule f={f} at={mk} w={e.w} y={e.h - 2} color={C.orangeInk} />}
      </Box>;
    }
    case 'card': case 'note': case 'quote': {
      return <Box e={e} f={f} dim={dim}>
        <HiBox w={w} pad={4} />
        <div style={{...paperCard, position: 'absolute', top: 0, bottom: 0, left: 0, right: 0,
          background: e.kind === 'quote' ? 'transparent' : C.paper,
          border: e.kind === 'quote' ? 'none' : (HANDMADE_MEDIUM ? '1px solid rgba(70,50,25,0.10)' : `2px solid ${C.line}`),
          borderLeft: `6px solid ${e.kind === 'note' ? C.orange : e.kind === 'quote' ? C.mutedBar : C.blue}`,
          boxShadow: e.kind === 'quote' ? 'none' : paperCard.boxShadow,
          padding: e.pad ?? 22, boxSizing: 'border-box'}}>
          <Lines lines={e.lines} text={e.text} size={e.size} lh={e.lh} color={e.kind === 'quote' ? C.muted : C.ink} weight={bold} align={e.align} />
        </div>
      </Box>;
    }
    case 'number':
      return <div data-auto-el={e.id} style={{position: 'absolute', left: e.x, top: e.y, opacity: dim}}>
        <KineticNumber f={f} at={e.at} from={e.from_ ?? 0} to={e.value} decimals={e.decimals} prefix={e.prefix} suffix={e.unit} size={e.size} color={tt.fill} ink={tt.ink} dur={30} />
      </div>;
    case 'bar': {
      const g = interpolate(f, [e.at + e.idx * 4, e.at + e.idx * 4 + 24], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
      const hot = e.hot || w > 0.3;
      const lx = e.barX - e.x;
      return <div data-auto-el={e.id} style={{position: 'absolute', left: e.x, top: e.y, width: e.w, height: e.h, opacity: interpolate(f, [e.at, e.at + 10], [0, 1], clamp) * dim}}>
        <HiBox w={w} pad={2} />
        <div style={{position: 'absolute', left: lx, width: e.barW, bottom: 52, height: e.barH * g, background: hot ? C.orange : C.lineBlue, borderRadius: '10px 10px 0 0'}} />
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 52 + e.barH * g + 8, textAlign: 'center', fontSize: e.size, fontWeight: 700, color: hot ? C.orangeInk : C.ink, opacity: g, fontFamily: 'Space,Kai'}}>{e.valueText}</div>
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 4, textAlign: 'center', fontSize: e.size, color: C.ink, fontWeight: bold, whiteSpace: 'nowrap'}}>{e.text}</div>
      </div>;
    }
    case 'codebox':
      return <Box e={e} f={f} dim={1} rise={10}>
        <div style={{position: 'absolute', inset: 0, background: C.paper, border: `2px solid ${C.line}`, borderRadius: 18, boxShadow: '0 10px 30px rgba(0,0,0,0.06)'}} />
        <div style={{position: 'absolute', left: 28, top: 22, fontSize: e.size, color: C.muted, fontFamily: 'Space,Kai', whiteSpace: 'nowrap'}}>{e.text}{e.lang ? ` · ${e.lang}` : ''}</div>
        <div style={{position: 'absolute', left: 0, right: 0, top: 76, height: 2, background: C.line}} />
      </Box>;
    case 'codeline': {
      const p = interpolate(f, [e.at + 6 + e.n * 2, e.at + 14 + e.n * 2], [0, 1], clamp);
      return <div data-auto-el={e.id} style={{position: 'absolute', left: e.x, top: e.y, width: e.w, height: e.h, opacity: p * dim}}>
        <HiBox w={w} pad={4} radius={8} />
        <div style={{position: 'relative', fontFamily: CODE_FONT, fontSize: e.size, lineHeight: `${e.h}px`, whiteSpace: 'pre', fontWeight: bold}}>
          {codeTokens(e.text).map((t, i) => <span key={i} style={{color: t.c}}>{t.t}</span>)}
        </div>
      </div>;
    }
    case 'panel': {
      const morph = e.morphTo ? STORY_AFTER(shot) : null;
      const outP = morph ? interpolate(f, [morph.at, morph.at + 16], [1, 0], clamp) : 1;
      const isAfter = !!e.morph;
      const op = isAfter ? interpolate(f, [e.at, e.at + 16], [0, 1], clamp) : outP;
      const t2 = tone(e.tone);
      const num = e.value != null ? countVal(f, e) : null;
      const en = enter(f, e.at, 14);
      return <div data-auto-el={e.id} {...(isAfter || e.morphTo ? {'data-gate-allow': 'morph'} : {})} style={{position: 'absolute', left: e.x, top: e.y, width: e.w, height: e.h, transform: `${en.transform ?? ''} rotate(${HANDMADE_MEDIUM && !isAfter ? tiltOf(e.id) : 0}deg)`, opacity: Math.min(Number(en.opacity), op) * dim}}>
        <InkFrame w={w} pad={4} t={e.tone} />
        <div style={{...paperCard, position: 'absolute', top: 0, bottom: 0, left: 0, right: 0,
          borderTop: HANDMADE_MEDIUM ? `5px solid ${t2.fill}` : `8px solid ${t2.fill}`,
          padding: HANDMADE_MEDIUM ? '30px 34px' : '26px 34px', boxSizing: 'border-box'}}>
          {HANDMADE_MEDIUM && <Tape color={t2.light} />}
          <div style={{fontSize: e.size, fontWeight: 700, color: t2.ink, whiteSpace: 'nowrap', fontFamily: HANDMADE_MEDIUM ? 'Kai' : undefined}}>{e.title}</div>
          {num !== null && <div style={{fontSize: 120, fontWeight: 700, color: C.ink, fontFamily: 'Clash,Space,Kai', lineHeight: 1.15, fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap'}}>{num}<span style={{fontSize: 52, marginLeft: 8}}>{e.unit}</span></div>}
          {(e.items as any[]).map((it, i) => <div key={i} style={{marginTop: 22, ...enter(f, e.at + 6 + i * 5, 8), borderLeft: HANDMADE_MEDIUM ? `2px solid ${C.line}` : 'none', paddingLeft: HANDMADE_MEDIUM ? 16 : 0}}><Lines lines={it.lines} text="" size={it.size} /></div>)}
        </div>
      </div>;
    }
    case 'arrow': {
      const p = drawOn(f, e.at, 16);
      return <svg data-auto-el={e.id} style={{position: 'absolute', left: e.x, top: e.y, overflow: 'visible'}} width={e.w} height={e.h}>
        <line x1={0} y1={e.h / 2} x2={Math.max(0, (e.w - 16) * p)} y2={e.h / 2} stroke={C.muted} strokeWidth={5} strokeLinecap="round" />
        {p > 0.9 && <path d={`M ${e.w - 22} ${e.h / 2 - 13} L ${e.w - 4} ${e.h / 2} L ${e.w - 22} ${e.h / 2 + 13}`} fill="none" stroke={C.muted} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" />}
      </svg>;
    }
    case 'node':
      // 流程节点：手作皮肤下也是一张裁下的纸条，热的那张压一条朱砂淡彩
      return <Box e={e} f={f} dim={dim}>
        <InkFrame w={w} pad={4} />
        <div style={{...paperCard, position: 'absolute', top: 0, bottom: 0, left: 0, right: 0,
          borderTop: HANDMADE_MEDIUM ? `5px solid ${e.hot ? C.orange : C.lineBlue}` : undefined,
          borderLeft: HANDMADE_MEDIUM ? 'none' : `2px solid ${e.hot ? C.orange : C.line}`,
          border: HANDMADE_MEDIUM ? '1px solid rgba(70,50,25,0.10)' : undefined,
          padding: HANDMADE_MEDIUM ? '26px 24px' : '24px 22px', boxSizing: 'border-box'}}>
          {HANDMADE_MEDIUM && <Tape color={e.hot ? C.orangeLight : C.blueLight} />}
          <Lines lines={e.lines} text={e.text} size={e.size} weight={700} lh={1.25} color={e.hot ? C.orangeInk : C.ink} />
          {e.note && <div style={{marginTop: 16, opacity: 0.85}}><Lines lines={e.noteLines} text={e.note} size={e.noteSize} color={C.muted} lh={1.4} /></div>}
        </div>
      </Box>;
    case 'item': {
      const mark = e.style === 'check' ? '✓' : e.style === 'plain' ? '·' : String(e.n);
      return <Box e={e} f={f} dim={dim}>
        <HiBox w={w} pad={8} />
        {/* 清单也是组件，不是「序号浮在背景上」。容器沿用 panel / node 的 paperCard，
            但不加 Tape / tilt：全组件模式要有层次，不能混进自由手账的随机性。 */}
        <div style={{...paperCard, position: 'absolute', inset: 0}} />
        <div style={{position: 'absolute', left: 20, top: '50%', transform: 'translateY(-50%)', width: 56, height: 56, borderRadius: 28, background: C.blueLight, color: C.blueInk, fontSize: 32, fontWeight: 700, display: 'grid', placeItems: 'center', fontFamily: 'Clash,Space,Kai'}}>{mark}</div>
        <div style={{position: 'absolute', left: 100, right: 24, top: 0, bottom: 0, display: 'flex', alignItems: 'center'}}><Lines lines={e.lines} text={e.text} size={e.size} lh={e.lh} weight={bold} /></div>
      </Box>;
    }
    case 'option': {
      const reveal = shot.lines.length > 1 ? interpolate(f, [shot.lines[1], shot.lines[1] + 10], [0, 1], clamp) : 0;
      const good = e.correct;
      return <Box e={e} f={f} dim={good ? 1 : 1 - 0.45 * reveal}>
        <div style={{position: 'absolute', inset: 0, borderRadius: 16, border: `3px solid ${good && reveal > 0 ? C.green : C.line}`, background: good ? `rgba(41,163,131,${0.14 * reveal})` : C.paper}} />
        <div style={{position: 'absolute', left: 22, top: 0, bottom: 0, display: 'flex', alignItems: 'center', gap: 22, fontSize: e.size, color: C.ink, whiteSpace: 'nowrap'}}>
          <span style={{fontFamily: 'Clash,Space,Kai', fontWeight: 700, color: C.blueInk}}>{e.letter}</span>
          <span style={{fontWeight: good && reveal > 0.5 ? 700 : 400, textDecoration: !good && reveal > 0.5 ? 'line-through' : 'none'}}>{e.text}</span>
          {reveal > 0.05 && <span style={{fontWeight: 700, color: good ? C.greenInk : C.muted, opacity: reveal}}>{good ? '✓ 对' : '✗'}</span>}
        </div>
      </Box>;
    }
    case 'timer': {
      const a = shot.lineEnds[0] ?? 0, b = shot.lines[1] ?? a + shot.think;
      const p = interpolate(f, [a, b], [0, 1], clamp);
      const vis = interpolate(f, [a - 6, a + 4, b, b + 10], [0, 1, 1, 0], clamp);
      const R = 80, L = 2 * Math.PI * R;
      return <div data-auto-el={e.id} style={{position: 'absolute', left: e.x, top: e.y, width: e.w, height: e.h, opacity: vis}}>
        <svg width={e.w} height={e.h} style={{position: 'absolute', inset: 0}}>
          <circle cx={e.w / 2} cy={e.h / 2} r={R} fill="none" stroke={C.mutedBar} strokeWidth={12} />
          <circle cx={e.w / 2} cy={e.h / 2} r={R} fill="none" stroke={C.blue} strokeWidth={12} strokeDasharray={L} strokeDashoffset={L * p} strokeLinecap="round" transform={`rotate(-90 ${e.w / 2} ${e.h / 2})`} />
        </svg>
        <div style={{position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', fontSize: e.size, fontWeight: 700, color: C.blueInk}}>{e.text}</div>
      </div>;
    }
    // ---------------------------------------------------------------- 3.6.0 手账页
    // 这一组不是「卡片」，是纸上的东西：装裱的真图版、手写大字、印章、批注、放大镜。
    // 语法抄自 cell 片（journal 皮肤）：容器是纸，不是圆角矩形；位置由 compose 的 page 版式算好。
    case 'archive':
      // 装裱好的真图版：ArchivePhoto 自带卡纸白边、编目签与 CC BY 署名，不要在外面再套框
      return <ArchivePhoto f={f} id={e.media} x={e.x} y={e.y} w={e.w} h={e.h} at={e.at}
        catalogue={e.catalogue} title={e.title} label={e.label ?? 'below'} />;
    case 'lettering':
      // 手写大字：年份 / 数字 / 一个词。手账页的「标题」是写上去的，不是排出来的
      return <HandLettering f={f} at={e.at} text={e.text} x={e.x} y={e.y} size={e.size} perChar={e.perChar ?? 6} />;
    case 'stamp':
      return <Seal f={f} at={e.at} x={e.x} y={e.y} size={e.w} text={e.text} />;
    case 'handnote':
      return <HandNote f={f} at={e.at} x={e.x} y={e.y} text={e.text} size={e.size} />;
    case 'loupe':
      // 放大镜压在图上：镜内是原图放大。look 是 0–1 相对坐标，lensAt 是落镜帧
      return <LoupeMedia f={f} id={e.media} x={e.x} y={e.y} w={e.w} h={e.h} at={e.at}
        catalogue={e.catalogue} title={e.title} label={e.label ?? 'below'}
        look={{x: (e.look ?? [0.5, 0.5])[0], y: (e.look ?? [0.5, 0.5])[1]}}
        lensAt={e.lensAt ?? e.at} r={e.r ?? 220} zoom={e.zoom ?? 2.4} />;
    case 'figure':
      // 页内示意图：手账页上「随手画的那张小图」。a2e 那套线稿在这里才有位置——
      // 它不解释概念，只帮观众认出「说的是哪件东西」，所以尺寸压在画宽 25% 以内。
      // 3.9.0：content.ink.acts 已由 compose 换算成本镜帧号（e.frames）。不写就只入场——
      // 旧 story 的画面因此一个像素都不变。
      return <SketchLayer f={f} box={{x: e.x, y: e.y, w: e.w, h: e.h}}
        spec={{id: e.id, draw: e.draw, label: e.label, parts: e.parts,
               frames: e.frames ?? [{at: e.figAt ?? 0, do: 'enter' as const}]}} />;
    case 'media':
      // 3.2.0 真实素材：MediaFrame 自带卡片外壳 / 署名徽章；区域推近由 content.region 指定
      return <Box e={e} f={f} dim={dim}><MediaFrame f={f} id={e.media} x={0} y={0} w={e.w} h={e.h} chrome={e.chrome} at={e.at} focus={e.region ?? undefined} focusAt={e.at + 24} highlight={shot.focus.filter((k) => f >= k.at && f <= k.until + 12 && shot.elements.some((x) => x.id === k.id && x.kind === 'region')).map((k) => k.id)} highlightAt={e.at} /></Box>;
    case 'region':
      return null; // 区域的高亮框由 MediaFrame 画（随区域推近一起缩放）；这里只提供被点名 / 推近的矩形
    default:
      return null;
  }
};

// morph 版式：after 面板出现的时刻
const STORY_AFTER = (shot: StoryShot) => shot.elements.find((x) => x.morph) ?? null;
const countVal = (f: number, e: Elem) => {
  const v = Number(e.value);
  const p = interpolate(f, [e.at + 4, e.at + 30], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  return (v * p).toFixed(e.decimals ?? 0);
};

const TipView: React.FC<{t: Tip; f: number}> = ({t, f}) => {
  const grow = interpolate(f, [t.at, t.at + 10], [0, 1], {...clamp, easing: Easing.linear});
  const o = interpolate(f, [t.until - 10, t.until], [1, 0], clamp);
  if (grow <= 0 || o <= 0) return null;
  return <div data-gate-allow="glossary" style={{position: 'absolute', left: t.x, top: t.y, width: t.w, height: t.h, opacity: o, clipPath: `inset(-6% ${((1 - grow) * 100).toFixed(2)}% -6% -2%)`, zIndex: 5}}>
    <div style={{position: 'absolute', inset: 0, background: C.navy, borderRadius: 14}} />
    <div style={{position: 'absolute', left: 25, top: 18, color: C.white, fontSize: t.size, lineHeight: 1.35, whiteSpace: 'nowrap'}}>{t.lines.map((l, i) => <div key={i}>{l}</div>)}</div>
  </div>;
};

/** 定制画面拿到的接口：元素入场进度、强调权重、主题色板、关键帧。 */
export type CustomProps = {
  f: number;
  shot: StoryShot;
  /** 元素 id → {in: 入场进度 0..1, hi: 关键词强调 0..1, el: 几何}；几何与 story.json 里写的一致 */
  el: (id: string) => {in: number; hi: number; el?: Elem};
  /** 第 i 句台词开始的本镜帧 */
  line: (i: number) => number;
  C: typeof C;
};

/** 讲解层：手绘圈注 / 下划线 / 箭头 / 手写小字。全部读皮肤墨色，跟着线稿层走。 */
const AnnotLayer: React.FC<{list: NonNullable<StoryShot['annotate']>; f: number}> = ({list, f}) => (
  <>
    {list.map((a, i) => {
      const p = interpolate(f, [a.at, a.at + 12], [0, 1], clamp);
      if (p <= 0) return null;
      if (a.kind === 'circle') return <InkCircle key={i} cx={a.x + a.w / 2} cy={a.y + a.h / 2} rx={a.w / 2 + 18} ry={a.h / 2 + 14} p={p} seed={a.seed} />;
      if (a.kind === 'underline') return <Underline key={i} x={a.x + 8} y={a.y + a.h - 6} w={a.w - 16} p={p} seed={a.seed} />;
      if (a.kind === 'note') return <HandNote key={i} f={f} at={a.at} x={a.x + a.w + 30} y={a.y - 12} text={a.text || ''} size={30} to={{x: a.x + a.w, y: a.y + a.h / 2}} />;
      return <InkPath key={i} d={`M ${a.x + a.w + 90} ${a.y + a.h / 2} Q ${a.x + a.w + 34} ${a.y + a.h / 2 - 8} ${a.x + a.w + 6} ${a.y + a.h / 2}`} p={p} size={5} seed={a.seed} />;
    })}
  </>
);

/** 未注册定制组件的运行时兜底：不再用一行红字顶替继续出片，而是整片渲染失败。
 *  构建期（compose-story / validate-visual-plan）已经拦过一次；这里只防"绕过构建直接渲染"。 */
const MissingCustom: React.FC<{name: string}> = ({name}) => {
  useEffect(() => {
    cancelRender(new Error(
      `未注册的定制组件：${name}。在 src/custom/index.ts 的 CUSTOM 表里注册它`
      + `（照抄 RequestLane.tsx 的写法），然后重跑 compose-story。`
    ));
  }, [name]);
  return null;
};

export const AutoShot: React.FC<{id: string; f: number}> = ({id, f}) => {
  const shot = STORY[id];
  if (!shot) return null;
  const els = shot.elements;
  if (shot.layout === 'custom') {
    const Comp = shot.custom ? CUSTOM[shot.custom] : undefined;
    const props: CustomProps = {
      f, shot, C,
      el: (eid) => { const e = els.find((x) => x.id === eid); return {in: e ? interpolate(f, [e.at, e.at + 18], [0, 1], {...clamp, easing: ease}) : 0, hi: hiWeight(shot, eid, f), el: e}; },
      line: (i) => shot.lines[Math.max(0, Math.min(i, shot.lines.length - 1))] ?? 0,
    };
    return <div style={{position: 'absolute', inset: 0}}>
      {Comp ? <Comp {...props} /> : <MissingCustom name={String(shot.custom)} />}
      {shot.tips.map((t, i) => <TipView key={i} t={t} f={f} />)}
    </div>;
  }
  return <div style={{position: 'absolute', inset: 0}}>
    {shot.sketch ? <SketchLayer spec={shot.sketch} f={f} box={shot.sketch.box} /> : null}
    {els.map((e) => <ElemView key={e.id} e={e} f={f} shot={shot} all={els} />)}
    {shot.annotate ? <AnnotLayer list={shot.annotate} f={f} /> : null}
    {shot.tips.map((t, i) => <TipView key={i} t={t} f={f} />)}
  </div>;
};
