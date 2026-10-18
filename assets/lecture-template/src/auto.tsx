import React from 'react';
import {Easing, interpolate} from 'remotion';
import {THEME} from './theme/active';
import {KineticNumber, drawOn} from './cinema';
import {STORY} from './story';
import {CUSTOM} from './custom';

// ============================================================================
// auto.tsx · v4.5 内容驱动的镜头渲染器（AutoShot）
//
// story.json（纯内容）→ scripts/compose-story.py（排版 / 关键词 / 相机 / 自动修）→ src/story.ts → 这里画。
// 本层只负责「画」，几何全部在 compose-story 里算好（门禁也在那里跑），所以弱模型写不坏版面。
//
// 克制原则（v4.5）：
//   · 入场只有「淡入 + 14px 上浮」一种，不回弹、不旋转、不闪；statement 版式只淡入。
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

/** 入场：淡入 + 上浮 14px，18 帧，无回弹。 */
export const enter = (f: number, at: number, rise = 14): React.CSSProperties => {
  const p = interpolate(f, [at, at + 18], [0, 1], {...clamp, easing: ease});
  return {opacity: p, transform: rise ? `translateY(${((1 - p) * rise).toFixed(2)}px)` : undefined};
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

const Lines: React.FC<{lines?: string[]; text: string; size: number; lh?: number; color?: string; weight?: number; align?: string}> = ({lines, text, size, lh = 1.35, color = C.ink, weight = 400, align}) => (
  <div style={{position: 'relative', fontSize: size, lineHeight: lh, color, fontWeight: weight, textAlign: (align as any) ?? 'left', whiteSpace: 'nowrap'}}>
    {(lines ?? [text]).map((l, i) => <div key={i}>{l}</div>)}
  </div>
);

/** 强调：沿用 v4.4 的强调语言 —— 强调色描边 + 轻微抬升阴影（配合镜头推近），不用底色带 / 标记条。 */
const HiBox: React.FC<{w: number; t?: string; pad?: number; radius?: number}> = ({w, t, pad = 10, radius = 14}) => {
  if (w <= 0.01) return null;
  const tt = tone(t);
  return <div style={{position: 'absolute', inset: -pad, borderRadius: radius, border: `3px solid ${tt.fill}`, boxShadow: `0 10px 28px rgba(0,0,0,${0.12 * w})`, opacity: w, boxSizing: 'border-box'}} />;
};

const Box: React.FC<{e: Elem; f: number; dim: number; style?: React.CSSProperties; children: React.ReactNode; rise?: number}> = ({e, f, dim, style, children, rise}) => (
  <div data-auto-el={e.id} style={{position: 'absolute', left: e.x, top: e.y, width: e.w, height: e.h, ...enter(f, e.at, rise), ...style}}>
    <div style={{position: 'absolute', inset: 0, opacity: dim}}>{children}</div>
  </div>
);

const CODE_FONT = "'JetBrains Mono','DejaVu Sans Mono',Consolas,Menlo,monospace,Kai"; // Kai 兜底：代码注释里的中文不出豆腐块
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
  const dim = e.kind === 'codebox' ? 1 : 1 - 0.32 * Math.max(0, others - w);
  const tt = tone(e.tone);
  const bold = w > 0.5 ? 700 : undefined;
  switch (e.kind) {
    case 'text': {
      const color = e.role === 'muted' ? C.muted : C.ink;
      const weight = e.role === 'display' || e.role === 'title' ? 700 : e.role === 'accent' ? 700 : 400;
      return <Box e={e} f={f} dim={dim} rise={shot.layout === 'statement' ? 0 : 14}><HiBox w={w} /><Lines lines={e.lines} text={e.text} size={e.size} lh={e.lh} color={e.role === 'accent' ? C.orangeInk : color} weight={bold ?? weight} align={e.align} /></Box>;
    }
    case 'card': case 'note': case 'quote': {
      const bg = e.kind === 'quote' ? 'transparent' : C.paper;
      return <Box e={e} f={f} dim={dim}>
        <HiBox w={w} pad={4} />
        <div style={{position: 'absolute', inset: 0, background: bg, borderRadius: 16, border: e.kind === 'quote' ? 'none' : `2px solid ${C.line}`, borderLeft: `6px solid ${e.kind === 'note' ? C.orange : e.kind === 'quote' ? C.mutedBar : C.blue}`, padding: e.pad ?? 22, boxSizing: 'border-box'}}>
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
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 4, textAlign: 'center', fontSize: e.size, color: C.ink, fontWeight: bold}}>{e.text}</div>
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
      return <div data-auto-el={e.id} {...(isAfter || e.morphTo ? {'data-gate-allow': 'morph'} : {})} style={{position: 'absolute', left: e.x, top: e.y, width: e.w, height: e.h, transform: en.transform, opacity: Math.min(Number(en.opacity), op) * dim}}>
        <HiBox w={w} pad={4} t={e.tone} />
        <div style={{position: 'absolute', inset: 0, background: C.paper, borderRadius: 20, border: `2px solid ${C.line}`, borderTop: `8px solid ${t2.fill}`, padding: '26px 34px', boxSizing: 'border-box'}}>
          <div style={{fontSize: e.size, fontWeight: 700, color: t2.ink, whiteSpace: 'nowrap'}}>{e.title}</div>
          {num !== null && <div style={{fontSize: 120, fontWeight: 700, color: C.ink, fontFamily: 'Clash,Space,Kai', lineHeight: 1.15, fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap'}}>{num}<span style={{fontSize: 52, marginLeft: 8}}>{e.unit}</span></div>}
          {(e.items as any[]).map((it, i) => <div key={i} style={{marginTop: 22, ...enter(f, e.at + 6 + i * 5, 8)}}><Lines lines={it.lines} text="" size={it.size} /></div>)}
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
      return <Box e={e} f={f} dim={dim}>
        <HiBox w={w} pad={4} />
        <div style={{position: 'absolute', inset: 0, background: C.paper, borderRadius: 18, border: `2px solid ${e.hot ? C.orange : C.line}`, padding: '24px 22px', boxSizing: 'border-box'}}>
          <Lines lines={e.lines} text={e.text} size={e.size} weight={700} lh={1.25} color={e.hot ? C.orangeInk : C.ink} />
          {e.note && <div style={{marginTop: 16}}><Lines lines={e.noteLines} text={e.note} size={e.noteSize} color={C.muted} lh={1.4} /></div>}
        </div>
      </Box>;
    case 'item': {
      const mark = e.style === 'check' ? '✓' : e.style === 'plain' ? '·' : String(e.n);
      return <Box e={e} f={f} dim={dim}>
        <HiBox w={w} pad={8} />
        <div style={{position: 'absolute', left: 0, top: 6, width: 56, height: 56, borderRadius: 28, background: C.blueLight, color: C.blueInk, fontSize: 32, fontWeight: 700, display: 'grid', placeItems: 'center', fontFamily: 'Clash,Space,Kai'}}>{mark}</div>
        <div style={{position: 'absolute', left: 84, top: 6}}><Lines lines={e.lines} text={e.text} size={e.size} lh={e.lh} weight={bold} /></div>
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
  const o = interpolate(f, [t.at, t.at + 10, t.until - 10, t.until], [0, 1, 1, 0], clamp);
  if (o <= 0) return null;
  return <div data-gate-allow="glossary" style={{position: 'absolute', left: t.x, top: t.y, width: t.w, height: t.h, opacity: o, transform: `translateY(${(1 - o) * (t.below ? -8 : 8)}px)`, zIndex: 5}}>
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
      {Comp ? <Comp {...props} /> : <div style={{position: 'absolute', left: 200, top: 400, fontSize: 40, color: C.redInk}}>未注册的定制组件：{shot.custom}</div>}
      {shot.tips.map((t, i) => <TipView key={i} t={t} f={f} />)}
    </div>;
  }
  return <div style={{position: 'absolute', inset: 0}}>
    {els.map((e) => <ElemView key={e.id} e={e} f={f} shot={shot} all={els} />)}
    {shot.tips.map((t, i) => <TipView key={i} t={t} f={f} />)}
  </div>;
};
