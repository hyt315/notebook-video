import React from 'react';
import {Easing, interpolate, spring} from 'remotion';
import {THEME} from './theme/active';

// ============================================================================
// media · 视觉介质层 v2（内容 → 视觉形式 的落地件）
//
// 介质清单与对应组件（references/media-routing.md 有完整路由表）：
//   数据/对比   → fxkit: CompareBars / ProgressRing      本文件: MetricGrid
//   软件/流程   → 本文件: ConsoleWindow
//   技术代码    → fxkit: DiffView / Typewriter
//   结构关系    → fxkit: TimeRail / StaggerList
//   抽象概念    → Mascot + SVG 概念图 + stagekit 主体
//   强调信息    → 数值滚动（MetricGrid 内置）/ StampBanner
//   证据细节    → fxkit: EvidenceZoom
//   场景衔接    → shotkit 运镜 + insert 转场
//
// ── v2 的动效原则（"丝滑"来自多时钟，不是更花的曲线）────────────────────
// 1. **同一元素的多个属性用不同时钟**（number-flow：位移 900ms / 透明度 450ms）。
//    同长同曲线读作"一个刚体弹出"，错开 4–14 帧才读作"东西落下来"。
// 2. **入场与出场曲线不同**：出场快而急（ease-in quad），入场慢而稳（bezier(.16,1,.3,1)）。
// 3. **不要只动透明度**：每个淡入都配 10–24px 位移或 2–6% 缩放。
// 4. **数值用 tabular-nums + 固定小数位**，否则数字会横向抖动（"不丝滑"的常见真因）。
// 5. **进度条动 scaleX，不动 width**：width 是布局属性，会重排，且会让圆角胶囊在动画中间被拉变形。
// 6. **过冲只给物体，不给数值**：印章/横幅可以弹，百分比不能弹（会显示错误的数）。
// ============================================================================

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const BASE_FPS = 30;
const easeOut = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)});
const easeIn = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.in(Easing.quad)});
const easeIO = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.inOut(Easing.cubic)});
/** 单向脉冲 0→1→0（强调一下，而不是永久呼吸）。 */
const pulse = (f: number, at: number, dur = 14) => Math.sin(Math.PI * Math.max(0, Math.min(1, (f - at) / dur)));

export type ConsoleRow = {text: string; tone?: 'cmd' | 'info' | 'ok' | 'warn' | 'out'; at?: number};

// 数值形态解析：把 "¥1.00" / "1.42×" / "0.9s" 拆成 前缀+数+后缀，就能做数值滚动；
// 拆不出来（如"已超过"）就退化为整串上滚。
type NumParts = {prefix: string; value: number; suffix: string; decimals: number};
const parseNum = (s: string): NumParts | null => {
  const m = /^([^\d\-+]*)(-?\d+(?:\.\d+)?)(.*)$/.exec(String(s));
  if (!m) return null;
  const decimals = (m[2].split('.')[1] ?? '').length;
  return {prefix: m[1], value: parseFloat(m[2]), suffix: m[3], decimals};
};

// ---------------------------------------------------------------------------
// ConsoleWindow：控制台/终端窗口介质。
// v2：行"被写出来"（clip 擦除 + 位移 + 光标接棒）、ok/warn 行一闪、状态胶囊脉冲刷新、
//     末行一道扫描、高度按内容自适应（旧版默认高度比内容高约 120px，整块死黑）。
// ---------------------------------------------------------------------------
const ROW_INTERVAL = 16; // 行间默认节奏（帧）。旧的 9 帧（300ms）太快，光标读不出"移动"
const ROW_REVEAL = 14;

export const ConsoleWindow: React.FC<{
  x: number;
  y: number;
  w: number;
  h?: number;
  f: number;
  title?: string;
  rows: ConsoleRow[];
  start?: number;
  rowGap?: number;
  status?: {text: string; tone?: 'idle' | 'ok' | 'warn'};
  side?: React.ReactNode;
  sideW?: number;
  z?: number;
  exitStart?: number;
  cursor?: boolean;
  /** 'log'：逐行写入（默认）；'typing'：逐字打出来 */
  variant?: 'log' | 'typing';
}> = ({x, y, w, h, f, title = 'console', rows, start = 0, rowGap = 44, status, side, sideW = 260, z = 74, exitStart, cursor = true, variant = 'log'}) => {
  const C = THEME.palette;
  const opIn = easeOut(f, 0, 14);
  const mvIn = easeOut(f, 0, 18);
  const out = exitStart === undefined ? 0 : easeIO(f, exitStart, exitStart + 15);
  // 高度自适应，不留死黑：必须算上自己的上下内边距(28)与真实行高(~36)，
  // 且行间距用的是 max(6,rowGap-22)（与下面 body 的 gap 保持一致）。
  // 旧式 `24 + rows*rowGap` 在 rowGap=64/5 行时比内容矮 27px，最后一行被裁掉。
  // body height: prefer the caller's explicit h; otherwise let the browser size it to content.
  // Any hand-rolled row-height estimate drifts with font/weight (measured: 27px short with the old
  // `24 + rows*rowGap`, still 12px short with an estimate), and the last row gets clipped by hidden overflow.
  const bodyH = h;
  const tone = (t?: string) => (t === 'ok' ? C.green : t === 'warn' ? C.gold : t === 'cmd' ? C.blue : t === 'out' ? '#e8e8e8' : '#bdb6ac');
  const statusTone = status?.tone === 'ok' ? C.green : status?.tone === 'warn' ? C.gold : C.blue;
  const rowAt = (r: ConsoleRow, i: number) => r.at ?? start + i * ROW_INTERVAL;
  const lastAt = rows.reduce((m, r, i) => Math.max(m, rowAt(r, i)), 0);
  let cursorRow = -1;
  rows.forEach((r, i) => { if (f >= rowAt(r, i)) cursorRow = i; });
  const cursorTravel = cursorRow > 0 ? easeOut(f, rowAt(rows[cursorRow], cursorRow) - 4, rowAt(rows[cursorRow], cursorRow) + 4) : 1;
  const blink = 0.15 + 0.8 * (0.5 + 0.5 * Math.cos((f / 16) * Math.PI * 2));
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w + (side ? sideW + 14 : 0), zIndex: z, opacity: opIn * (1 - out), transform: `translateY(${20 * (1 - mvIn) + 26 * out}px) scale(${0.99 + 0.01 * mvIn})`}}>
      <div style={{display: 'flex', gap: 14}}>
        <div style={{flex: 1, minWidth: 0, background: '#14110f', border: `2.5px solid ${C.ink}`, borderRadius: 12, boxShadow: `3.5px 3.5px 0 ${C.ink}`, overflow: 'hidden'}}>
          <div style={{height: 38, background: '#1f1b18', display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 14, borderBottom: '1.5px solid #2d2621'}}>
            {[C.red, C.gold, C.green].map((c, i) => {
              const p = easeOut(f, 2 + i * 3, 12 + i * 3);
              return <span key={i} style={{width: 10, height: 10, borderRadius: 99, background: c, border: '1px solid #000', opacity: p, transform: `scale(${0.6 + 0.4 * p})`}} />;
            })}
            <span style={{marginLeft: 8, fontFamily: 'Space,monospace', fontWeight: 600, fontSize: 13, letterSpacing: 1, color: '#fdfdfb', opacity: 0.85}}>{title}</span>
            {status && (
              <span style={{marginLeft: 'auto', marginRight: 12, fontFamily: 'Space,monospace', fontSize: 11, fontWeight: 700, background: `${statusTone}22`, color: statusTone, border: `1px solid ${statusTone}66`, borderRadius: 999, padding: '2px 10px', whiteSpace: 'nowrap', transform: `scale(${1 + 0.06 * pulse(f, lastAt, 10)})`}}>{status.text}</span>
            )}
          </div>
          <div style={{height: bodyH ?? 'auto', padding: '14px 18px', display: 'flex', flexDirection: 'column', gap: Math.max(6, rowGap - 22), position: 'relative'}}>
            {rows.map((r, i) => {
              const at = rowAt(r, i);
              if (f < at) return null;
              const isLast = i === rows.length - 1;
              const glyphP = easeOut(f, at, at + 8);
              const textP = easeOut(f, at + 2, at + ROW_REVEAL);
              const wideP = variant === 'typing' ? easeOut(f, at, at + Math.max(14, r.text.length * 2)) : textP;
              const flash = (r.tone === 'ok' || r.tone === 'warn') ? (1 - easeOut(f, at, at + 14)) : 0;
              const sweep = isLast ? pulse(f, at + 16, 20) : 0;
              return (
                <div key={i} style={{position: 'relative', display: 'flex', alignItems: 'center', gap: 10, fontFamily: 'Space,Kai,monospace', fontWeight: 600, fontSize: 22, color: tone(r.tone), borderRadius: 6, padding: '2px 6px', overflow: 'hidden', background: flash > 0.02 ? `${tone(r.tone)}22` : 'transparent'}}>
                  {r.tone === 'cmd' && <span style={{color: C.green, opacity: glyphP, transform: `scale(${0.7 + 0.3 * glyphP})`}}>❯</span>}
                  {r.tone === 'ok' && <span style={{color: C.green, opacity: glyphP, transform: `scale(${0.7 + 0.3 * glyphP})`}}>✓</span>}
                  <span style={{whiteSpace: 'nowrap', clipPath: `inset(0 ${(1 - wideP) * 100}% 0 0)`, transform: `translateX(${(1 - textP) * 14}px)`}}>{r.text}</span>
                  {cursor && cursorRow === i && (
                    <span style={{display: 'inline-block', width: 8, height: 19, marginLeft: 2, background: C.green, opacity: blink, transform: `translateX(${(1 - cursorTravel) * -14}px)`}} />
                  )}
                  {sweep > 0.02 && (
                    <span style={{position: 'absolute', top: 0, bottom: 0, left: `${-10 + sweep * 120}%`, width: 3, background: tone(r.tone), opacity: 0.75 * (1 - sweep)}} />
                  )}
                </div>
              );
            })}
          </div>
        </div>
        {side && <div style={{width: sideW, flex: `0 0 ${sideW}px`, position: 'relative'}}>{side}</div>}
      </div>
    </div>
  );
};

export type Metric = {label: string; before: string; after: string; win: boolean; color?: string};

// ---------------------------------------------------------------------------
// MetricGrid：指标网格介质。
// v2：数值按双时钟滚动（位移 27 帧 / 透明度 14 帧）+ tabular-nums + 固定小数位；
//     before→after 是"替换"（旧的快速向上退场、新的从下方稳稳落位），不是同时可见的交叉淡入；
//     进度条动 scaleX；对勾用显式 1.12 过冲落定。
// ---------------------------------------------------------------------------
export const MetricGrid: React.FC<{
  x: number;
  y: number;
  w: number;
  f: number;
  items: Metric[];
  cols?: number;
  start?: number;
  stagger?: number;
  cellH?: number;
  gap?: number;
  z?: number;
  exitStart?: number;
  title?: string;
}> = ({x, y, w, f, items, cols = 4, start = 0, stagger = 12, cellH = 168, gap = 16, z = 74, exitStart, title}) => {
  const C = THEME.palette;
  const out = exitStart === undefined ? 0 : easeIO(f, exitStart, exitStart + 15);
  const cellW = (w - gap * (cols - 1)) / cols;
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, zIndex: z, opacity: 1 - out}}>
      {title && <div style={{fontSize: 24, fontWeight: 700, color: C.muted, marginBottom: 12}}>{title}</div>}
      <div style={{display: 'flex', gap, flexWrap: 'wrap'}}>
        {items.map((m, i) => {
          const at = start + i * stagger;
          const cellOp = easeOut(f, at, at + 16);
          const cellMv = easeOut(f, at, at + 20);
          const accent = m.color ?? (m.win ? C.green : C.muted);
          const swapStart = at + 10;
          const swapP = easeOut(f, swapStart, swapStart + 27);   // 位移时钟
          const swapOp = easeOut(f, swapStart, swapStart + 14);  // 透明度时钟（约一半）
          const outP = easeIn(f, swapStart, swapStart + 6);      // 旧值更快向上退场（与新的错开，避免中途叠字）
          const barP = easeOut(f, at + 32, at + 54);
          const badgeP = easeOut(f, at + 28, at + 40);
          const num0 = parseNum(m.before), num1 = parseNum(m.after);
          const dec = num1 ? Math.max(num1.decimals, num0 ? num0.decimals : 0) : 0;
          const shown = num1 ? `${num1.prefix}${(num1.value * swapP).toFixed(dec)}${num1.suffix}` : m.after;
          return (
            <div key={m.label} style={{width: cellW, height: cellH, position: 'relative', background: C.paper, border: `2.5px solid ${accent}`, borderRadius: 12, boxShadow: `3px 3px 0 ${C.ink}`, padding: '16px 18px', opacity: cellOp, transform: `translateY(${24 * (1 - cellMv)}px) scale(${0.96 + 0.04 * cellMv})`}}>
              <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                <span style={{fontSize: 22, fontWeight: 700, color: C.ink}}>{m.label}</span>
                {m.win && badgeP > 0.02 && (
                  <span style={{width: 24, height: 24, borderRadius: 99, background: C.green, color: '#fff', display: 'grid', placeItems: 'center', fontSize: 15, fontWeight: 700, opacity: badgeP, transform: `scale(${0.001 + 1.12 * Math.max(0, Math.sin(Math.PI * Math.min(1, badgeP)))})`}}>✓</span>
                )}
              </div>
              <div style={{marginTop: 12, position: 'relative', height: 56, overflow: 'hidden', fontVariantNumeric: 'tabular-nums', fontFeatureSettings: '"tnum" 1'}}>
                {outP < 0.99 && (
                  <div data-gate-allow="value-swap" style={{position: 'absolute', left: 0, top: 0, fontFamily: 'Space', fontWeight: 700, fontSize: 30, color: C.muted, textDecoration: 'line-through', opacity: 1 - outP, transform: `translateY(${-56 * outP}px)`}}>{m.before}</div>
                )}
                <div data-gate-allow="value-swap" style={{position: 'absolute', left: 0, top: 0, fontFamily: 'Space', fontWeight: 700, fontSize: 38, color: accent, opacity: num1 ? swapOp : 1, transform: `translateY(${(1 - swapP) * 56}px)`}}>{shown}</div>
              </div>
              <div style={{position: 'absolute', left: 18, right: 18, bottom: 16, height: 8, background: C.gaugeTrack, borderRadius: 99, overflow: 'hidden'}}>
                <div style={{height: '100%', width: '100%', background: accent, borderRadius: 99, transformOrigin: 'left center', transform: `scaleX(${(m.win ? 0.92 : 0.4) * barP})`}} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// StampBanner：结论吸底条。三段式落定（冲击 6 帧 → 过冲到 1.03 → 回落 1）+ 底色一闪，
// 于是存在一个能指出来的"砸中那一帧"；原来的 spring 是渐近的，永远不会真正落定。
// ---------------------------------------------------------------------------
export const StampBanner: React.FC<{x: number; y: number; w: number; f: number; at: number; text: string; color?: string; z?: number}> = ({x, y, w, f, at, text, color, z}) => {
  const C = THEME.palette;
  const c = color ?? C.orange;
  if (f < at) return null;
  const impact = easeOut(f, at, at + 6);
  const over = pulse(f, at + 6, 14);   // 显式过冲，峰值在 at+13
  const flash = pulse(f, at, 22);
  const shock = pulse(f, at + 2, 20);
  const scale = 0.94 + 0.06 * impact + 0.03 * over;
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, zIndex: z ?? 92, opacity: impact, transform: `translateY(${(1 - impact) * 18}px) scale(${scale})`, transformOrigin: 'center'}}>
      <div style={{position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, height: 62, background: `${c}${Math.round((0.08 + 0.16 * flash) * 255).toString(16).padStart(2, '0')}`, border: `2px solid ${c}`, borderRadius: 14, fontSize: 28, fontWeight: 700, color: c}}>
        {shock > 0.02 && <span style={{position: 'absolute', inset: -2, borderRadius: 14, opacity: 0.5 * (1 - shock), boxShadow: `0 0 0 ${shock * 12}px ${c}33`, pointerEvents: 'none'}} />}
        <span style={{display: 'inline-block', transform: 'rotate(-8deg)'}}>◆</span>
        {text}
      </div>
    </div>
  );
};

/** 介质清单标识：校验脚本据此统计「一支片子里出现了几种介质」。 */
export const MEDIA_KINDS = ['graphic', 'chart', 'console', 'code', 'text', 'evidence', 'metric'] as const;
export type MediaKind = (typeof MEDIA_KINDS)[number];

export const MEDIA_VERSION = 'media-v2 · ConsoleWindow + MetricGrid + StampBanner · multi-clock motion';
