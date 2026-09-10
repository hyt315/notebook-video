import React, {useEffect, useRef} from 'react';
import {Easing, interpolate, spring} from 'remotion';
import {THEME} from './theme/active';
import {CoverPanel} from './shotkit';

// ============================================================================
// stagekit · 大主体骨架 v1（N 个独立边框 → 1 个主体 + 附着信息）
//
// 为什么需要它：v2.8 的四个场景结构同构（Paper + 标题 + 编号列表 + 贴标），
// 换内容不换结构，读起来就是「四个 PPT 页」。本层提供一个「活体主体」：
// 同一实例常驻不卸载，随旁白在 5–6 个 phase 之间演化状态。
//
// 三条硬标准（references/scene-skeletons.md）：
//   1. 占主体：16:9 下 ≥1024×620 设计像素，或占画幅宽 ≥60%；
//   2. 有状态机：≥5 拍，每拍 2–4 秒，全程同一实例；
//   3. 能装东西：main / rail / stamp 三个命名槽。
//
// 坐标铁律：x/y 永远相对于最近的 positioned 祖先。放进 Paper/StageFrame 内部
// 时坐标变成「框内相对坐标」；只有直接放在场景根下才是舞台坐标。
//
// 帧约定：所有组件接收显式 f（本镜本地帧），不自己读 useCurrentFrame，
// 与 fxkit 一致，便于在 ShotCamera 内组合。
// ============================================================================

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const BASE_FPS = 30;
const ease = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.inOut(Easing.cubic)});
const popS = (f: number, start: number, stiffness = 132) => spring({frame: f - start, fps: BASE_FPS, config: {damping: 17, stiffness, mass: 0.86}});

/** 一个状态拍：at=该拍起始帧（本镜本地帧），state=给渲染用的语义状态。 */
export type Phase = {at: number; state: string; label?: string; caption?: string};

export type StageCtx = {
  /** 当前拍序号 */
  index: number;
  /** 当前拍 */
  phase: Phase;
  /** 上一拍（第一拍时等于当前拍） */
  prev: Phase;
  /** 本拍已过帧数 */
  local: number;
  /** 本拍进度 0→1 */
  t: number;
  /** 本拍总长（帧） */
  span: number;
  /** 下一拍起始帧；无下一拍时给一个很远的数 */
  nextAt: number;
  /** 状态是否刚变（用于 12 帧交叉） */
  entering: number;
};

/**
 * useStageMachine：把「旁白句子」翻译成「主体状态」。
 * 这是把 AI 从「算几十个魔法帧号」降到「每句台词一个帧号」的关键。
 */
export const useStageMachine = (phases: Phase[], f: number): StageCtx => {
  const list = phases.length ? phases : [{at: 0, state: 'idle'}];
  let index = 0;
  for (let i = 0; i < list.length; i++) if (f >= list[i].at) index = i;
  const phase = list[index];
  const prev = list[Math.max(0, index - 1)];
  const nextAt = index + 1 < list.length ? list[index + 1].at : phase.at + 1e9;
  const span = Math.max(1, Math.min(nextAt, phase.at + 150) - phase.at);
  const local = f - phase.at;
  const t = Math.max(0, Math.min(1, local / span));
  return {index, phase, prev, local, t, span, nextAt, entering: ease(f, phase.at, phase.at + 12)};
};

// ---------------------------------------------------------------------------
// StageFrame：活体主体框。
//   header  顶部标题条（常驻，随 phase 换文案）
//   main    主体区（默认 68% 高）——由调用方按 ctx.phase.state 渲染不同状态
//   rail    右侧/底部伴随信息槽（可选）
//   stamp   结论吸底条（可选，落定后常驻 ≥1s）
// ---------------------------------------------------------------------------
export const StageFrame: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  f: number;
  phases: Phase[];
  header?: (ctx: StageCtx) => React.ReactNode;
  rail?: (ctx: StageCtx) => React.ReactNode;
  stamp?: (ctx: StageCtx) => React.ReactNode;
  children: (ctx: StageCtx) => React.ReactNode;
  borderColor?: string;
  lift?: number;
  z?: number;
  railW?: number;
  pad?: number;
}> = ({x, y, w, h, f, phases, header, rail, stamp, children, borderColor, lift = 0.24, z = 70, railW = 0, pad = 26}) => {
  const C = THEME.palette;
  const ctx = useStageMachine(phases, f);
  // 入场：位移/缩放与透明度用**不同时钟**（22px 上浮 26 帧、透明度 20 帧、描影 30 帧）。
  // 同一时长会让整块读成「一个刚体出现」；错开 4–6 帧才读成「纸落下来」。
  const opIn = ease(f, 0, 20);
  const mvIn = ease(f, 0, 26);
  const shadowIn = ease(f, 0, 30);
  const railPx = rail ? railW || Math.round(w * 0.26) : 0;
  const headH = header ? 56 : 0;
  const stampH = stamp ? 56 : 0;
  // main 槽真正可用的宽/高——给槽内组件传宽度前必须先算这两个数（见 scene-authoring.md）。
  const mainW = w - pad * 2 - (rail ? railPx + 18 : 0);
  const mainH = h - pad * 2 - headH - stampH - (stamp ? 14 : 0) - (header ? 14 : 0);
  const Paper = THEME.Paper;
  // 头部滑变：由 phase.at 派生（不要用 ref 记「上一帧」——Remotion 逐帧乱序渲染，ref 不可靠）
  const swapP = ease(f, ctx.phase.at, ctx.phase.at + 16);
  const outP = ease(f, ctx.phase.at, ctx.phase.at + 7);
  const prevPhase = ctx.index > 0 ? phases[ctx.index - 1] : null;
  const swapping = !!prevPhase && swapP < 1;
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, zIndex: z, opacity: opIn, transform: `translateY(${22 * (1 - mvIn)}px) scale(${0.97 + 0.03 * mvIn})`}}>
      <Paper lift={lift * shadowIn} borderColor={borderColor} style={{width: w, height: h, padding: pad}}>
        {header && (
          <div style={{position: 'relative', height: headH, display: 'flex', alignItems: 'center', borderBottom: `1.5px solid ${C.line}`, paddingBottom: 10, overflow: 'hidden'}}>
            {swapping && (
              <div data-gate-allow="swap" style={{position: 'absolute', left: 0, right: 0, display: 'flex', alignItems: 'center', opacity: 1 - outP, transform: `translateY(${-8 * outP}px)`}}>
                {header({...ctx, phase: prevPhase!, index: ctx.index - 1})}
              </div>
            )}
            <div data-gate-allow="swap" style={{position: 'absolute', left: 0, right: 0, display: 'flex', alignItems: 'center', opacity: swapping ? ease(f, ctx.phase.at + 4, ctx.phase.at + 16) : 1, transform: `translateY(${8 * (1 - ease(f, ctx.phase.at + 4, ctx.phase.at + 16))}px)`}}>
              {header(ctx)}
            </div>
          </div>
        )}
        <div style={{display: 'flex', gap: 18, height: h - pad * 2 - headH - stampH - (stamp ? 14 : 0), marginTop: header ? 14 : 0}}>
          <div style={{position: 'relative', flex: 1, minWidth: 0}}>{children(ctx)}{process.env.NODE_ENV !== 'production' && <SlotGuard f={f} mainW={mainW} mainH={mainH} tag={(phases[0] && (phases[0].label || phases[0].state)) || 'stage'} />}</div>
          {rail && <div style={{position: 'relative', width: railPx, flex: `0 0 ${railPx}px`}}>{rail(ctx)}</div>}
        </div>
        {stamp && <div style={{position: 'relative', height: stampH, marginTop: 14, borderTop: `1.5px dashed ${C.line}`, display: 'flex', alignItems: 'center'}}>{stamp(ctx)}</div>}
      </Paper>
    </div>
  );
};

// ---------------------------------------------------------------------------
// PhaseRail：状态进度轨。把「状态机」显式画出来——观众能看见主体在推进，
// 这是「主线演化」和「卡片轮播」在观感上的分水岭。
// ---------------------------------------------------------------------------
export const PhaseRail: React.FC<{phases: Phase[]; ctx: StageCtx; w?: number; color?: string}> = ({phases, ctx, w = 260, color}) => {
  const C = THEME.palette;
  const on = color ?? C.blue;
  // 当前绝对帧：phase.at + local。所有动画都从 phases[].at 派生 → 乱序渲染也确定。
  const f = ctx.phase.at + ctx.local;
  return (
    <div style={{width: w, display: 'flex', flexDirection: 'column', gap: 0}}>
      {phases.map((p, i) => {
        const done = i < ctx.index;
        const active = i === ctx.index;
        const take = ease(f, p.at, p.at + 14);          // 本拍「接管」的进度
        const rowIn = ease(f, p.at - 14, p.at + 6);     // 行入场（比接管略早，先有行再有态）
        const pulse = active ? 1 + 0.18 * Math.sin(Math.PI * Math.min(1, take)) : 0;
        const halo = active ? (1 - take) * 7 : 0;        // 接管瞬间的光晕，随进度收掉
        const dotScale = active ? 1 + pulse * 0.18 : done ? 0.94 : 1;
        const connector = ease(f, p.at + 2, p.at + 14); // 连到下一拍的线：接管后画出
        return (
          <div key={p.state}>
            <div style={{display: 'flex', alignItems: 'center', gap: 10, opacity: done || active ? 1 : 0.34, transform: `translateX(${(1 - rowIn) * -12}px)`}}>
              <span
                style={{
                  width: 22, height: 22, borderRadius: 99, flex: '0 0 auto', display: 'grid', placeItems: 'center',
                  background: done ? C.green : active ? on : C.mutedFill,
                  color: C.white, fontFamily: 'Space', fontWeight: 700, fontSize: 12,
                  boxShadow: halo > 0.4 ? `0 0 0 ${halo}px ${on}22` : 'none',
                  transform: `scale(${dotScale})`,
                }}
              >
                {done ? '✓' : i + 1}
              </span>
              <span style={{fontSize: 21, fontWeight: 700, color: active ? on : C.ink, whiteSpace: 'nowrap'}}>{p.label ?? p.state}</span>
            </div>
            {i < phases.length - 1 && (
              <div style={{marginLeft: 10, width: 2, height: 12, background: done ? C.green : C.line, transformOrigin: 'top center', transform: `scaleY(${done ? 1 : connector})`}} />
            )}
          </div>
        );
      })}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Attach：附着信息。原本要新开一张说明卡的，改成挂在主体附近的贴标，
// 这样画面里只有一个主体、若干附着信息，而不是一排并列卡片。
// ---------------------------------------------------------------------------
export const Attach: React.FC<{
  x: number;
  y: number;
  w?: number;
  f: number;
  at?: number;
  exitStart?: number;
  color?: string;
  tone?: 'wash' | 'paper';
  children?: React.ReactNode;
  style?: React.CSSProperties;
}> = ({x, y, w = 300, f, at = 0, exitStart, color, tone = 'wash', children, style}) => {
  const C = THEME.palette;
  const p = popS(f, at, 160);
  const out = exitStart === undefined ? 0 : ease(f, exitStart, exitStart + 15);
  const h = typeof (style as {height?: number})?.height === 'number' ? (style as {height: number}).height : 0;
  return (
    <div style={{opacity: p * (1 - out), transform: `translateY(${14 * (1 - p) + 30 * out}px)`, ...style}}>
      {h > 0 ? (
        <CoverPanel x={x} y={y} w={w} h={h} tone={tone} pad={14} style={{position: 'absolute', ...(color ? {boxShadow: `0 0 0 1.5px ${color}`} : {})}}>
          {children}
        </CoverPanel>
      ) : (
        <div style={{position: 'absolute', left: x, top: y, width: w, padding: '10px 14px', borderRadius: 12, background: tone === 'paper' ? C.paper : `${C.paperBase}E8`, boxShadow: `0 0 0 1.5px ${color ?? C.line}`, fontSize: 22, fontWeight: 700, color: C.ink}}>{children}</div>
      )}
    </div>
  );
};

/** 槽内溢出守卫（只警告，不阻断）：main 槽的内容若超出可用宽/高，说明某个组件的宽度
 *  超过了「w − pad×2 − railW − 18」。这是"控制台压住轨道"那一类缺陷的通用防线。 */
const SlotGuard: React.FC<{f: number; mainW: number; mainH: number; tag: string}> = ({f, mainW, mainH, tag}) => {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const id = requestAnimationFrame(() => {
      try {
        const el = ref.current;
        if (!el || typeof console === 'undefined') return;
        const dw = el.scrollWidth - mainW;
        const dh = el.scrollHeight - mainH;
        if (dw > 2) console.warn(`[SlotGuard] ${tag} @${f}: main 槽内容超出可用宽度 ${Math.round(dw)}px（available=${mainW}）。把子组件宽度改为 ≤ ${mainW}，或加大 railW。`);
        if (dh > 2) console.warn(`[SlotGuard] ${tag} @${f}: main 槽内容超出可用高度 ${Math.round(dh)}px（available=${mainH}）。`);
      } catch (e) { /* 忽略：只是提示 */ }
    });
    return () => cancelAnimationFrame(id);
  });
  return <div ref={ref} style={{position: 'absolute', width: mainW, height: mainH, overflow: 'hidden', pointerEvents: 'none', opacity: 0}} />;
};

export const STAGEKIT_VERSION = 'stagekit-v3 · StageFrame + state machine + PhaseRail + Attach + SlotGuard + header swap';
