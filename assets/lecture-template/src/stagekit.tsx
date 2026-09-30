import React, {useEffect, useRef} from 'react';
import {Easing, continueRender, delayRender, interpolate} from 'remotion';
import {THEME} from './theme/active';
import {useCanvas} from './theme/canvas';

// ============================================================================
// stagekit · 可选的状态/分区布局助手
//
// 适合“同一对象跨几个解释状态演化”的镜头，不是所有场景的标准模板。静态图表、
// 单个清晰标签、截图、留白或不使用 StageFrame 都可以更适合当前内容。Phase、
// header、rail、stamp 与 main 槽按需采用；没有最少阶段数、面积或槽位填充配额。
//
// 坐标铁律：x/y 永远相对于最近的 positioned 祖先。放进 Paper/StageFrame 内部
// 时坐标变成「框内相对坐标」；只有直接放在场景根下才是舞台坐标。
//
// 帧约定：所有组件接收显式 f（本镜本地帧），不自己读 useCurrentFrame，
// 与 fxkit 一致，便于在 ShotCamera 内组合。
// ============================================================================

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
// popS / BASE_FPS 已删（tsc TS6133）：本文件的入场都写成了行内 ease()，popS 无调用方。
const ease = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.inOut(Easing.cubic)});

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
// SlotGuard：作者主动选择的 main 槽占用诊断。
//
// 2026-09-21 补：本文件此前**引用了 `SlotGuard`，却从来没有定义过它**（只有版本串里写着名字）。
// 全仓库搜不到定义，`tsc` 报 TS2304；因为在 dev 分支上才挂它，出片那条路径永远走不到，
// 于是「引用了不存在的标识符」一路静默 —— 只要进一次 Studio / dev 就是 ReferenceError。
// 实现逐字取自 overview-film 的 v5 版本（同仓库下游工程，已在成片里跑过）。
//
// 它量测主槽内内容的大致垂直覆盖率并发出诊断；小占用率可能是留白/静态图的有意选择，
// 需结合本镜的视觉任务判断，不为提高比例添加无关装饰。
//
// 为什么不默认挂载：槽位占用只是粗略观感代理，无法判断一段留白是否利于理解；
// 它仅供作者主动选择的布局诊断，不是统一质量要求，也不应为通过而添加装饰。
// 为观感标准打断整片渲染，代价远大于收益；
// 真正该硬拦的是「文字被裁」「元素互相压」，那两件已经有 CardFitGate 与 OverlapGate。
// 为什么不出声在 dev 门里：本仓库出片走 production 包，dev-only 的门看不到 ——
// 出声必须发生在出图路径上。（测量排在 rAF 里，所以同样持一个 delayRender，
// 不然又会变成「装了但没量过」。）
// ---------------------------------------------------------------------------
export const SlotGuard: React.FC<{f: number; mainW: number; mainH: number; tag: string}> = ({f, mainW, mainH, tag}) => {
  const ref = useRef<HTMLDivElement>(null);
  const slotW = mainW;
  const slotH = mainH;
  useEffect(() => {
    const host = ref.current?.parentElement;
    if (!host) return;
    const handle = delayRender(`SlotGuard @${Math.round(f)}`);
    let released = false;
    const release = () => {
      if (released) return;
      released = true;
      continueRender(handle);
    };
    const id = requestAnimationFrame(() => {
      try {
        const hr = host.getBoundingClientRect();
        if (hr.width < 4 || hr.height < 4) {
          release();
          return;
        }
        // 覆盖率 = 槽内所有"有内容的**最内层**元素"的并集高度占槽高的比例。
        // 用并集而不是逐个相加：槽里常有多层包裹的同一块内容，相加会虚高。
        // 只看最内层（没有元素子节点）：实测踩到过——把内容包一层 `height:'100%'` 的
        // 容器后，那个空壳的 rect 就是整个槽高，覆盖率会被虚报成 100%，
        // 于是「槽里只有一行字」这件事反而被这层壳藏起来了。看最内层就不会被骗。
        let top = Infinity;
        let bottom = -Infinity;
        let leaves = 0;
        host.querySelectorAll<HTMLElement>('div,span,svg,p,text,tspan').forEach((el) => {
          if (!(el.textContent || '').trim() && el.tagName.toLowerCase() !== 'svg') return;
          if (el.getAttribute('data-slot-guard')) return;
          if (el.children.length > 0 && el.tagName.toLowerCase() !== 'svg') return;
          const r = el.getBoundingClientRect();
          if (r.width * r.height < 16) return;
          leaves++;
          top = Math.min(top, r.top);
          bottom = Math.max(bottom, r.bottom);
        });
        const used = leaves ? Math.max(0, Math.min(hr.height, bottom - top)) : 0;
        const cover = used / hr.height;
        if (cover < 0.35 && typeof console !== 'undefined') {
          console.warn(
            `[SlotGuard] @${Math.round(f)} StageFrame「${tag}」main 槽垂直覆盖率 ${Math.round(cover * 100)}%` +
              `（${leaves} 个内容块 / 槽 ${Math.round(slotW)}×${Math.round(slotH)} 设计像素）。` +
              `这是几何诊断，不是质量分；请结合旁白和静态/动态画面的讲解作用判断。`
          );
        } else if (typeof console !== 'undefined') {
          console.warn(`[SlotGuard] @${Math.round(f)} 「${tag}」main 槽占用 ${Math.round(cover * 100)}%（${leaves} 块）`);
        }
      } catch (e) {
        if (typeof console !== 'undefined') console.warn('[SlotGuard]', e);
      }
      release();
    });
    return () => {
      cancelAnimationFrame(id);
      release();
    };
  }, [f, slotW, slotH, tag]);
  return <div ref={ref} data-slot-guard style={{position: 'absolute', width: 0, height: 0, pointerEvents: 'none'}} />;
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
  railH?: number;
  railPlacement?: 'side' | 'top' | 'bottom';
  pad?: number;
}> = ({x, y, w, h, f, phases, header, rail, stamp, children, borderColor, lift = 0.24, z = 70, railW = 0, railH, railPlacement = 'side', pad = 26}) => {
  const C = THEME.palette;
  const {canvas} = useCanvas();
  const placement = rail ? (canvas === '3:4' && railPlacement === 'side' ? 'bottom' : railPlacement) : 'side';
  const ctx = useStageMachine(phases, f);
  // 入场：位移/缩放与透明度用**不同时钟**（22px 上浮 26 帧、透明度 20 帧、描影 30 帧）。
  // 同一时长会让整块读成「一个刚体出现」；错开 4–6 帧才读成「纸落下来」。
  const opIn = ease(f, 0, 20);
  const mvIn = ease(f, 0, 26);
  const shadowIn = ease(f, 0, 30);
  const railPx = rail ? railW || Math.round((w - pad * 2) * 0.26) : 0;
  const headH = header ? 56 : 0;
  const stampH = stamp ? 56 : 0;
  const contentH = h - pad * 2 - headH - stampH - (stamp ? 14 : 0);
  const railHeight = rail ? railH ?? Math.round(contentH * 0.24) : 0;
  // main 槽真正可用的宽/高——给槽内组件传宽度前必须先算这两个数（见 scene-authoring.md）。
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
        <div style={{display: 'flex', flexDirection: placement === 'side' ? 'row' : 'column', gap: 18, height: contentH, marginTop: header ? 14 : 0, minHeight: 0}}>
          {rail && placement === 'top' && <div style={{position: 'relative', width: '100%', height: railHeight, flex: `0 0 ${railHeight}px`}}>{rail(ctx)}</div>}
          <div style={{position: 'relative', flex: '1 1 auto', minWidth: 0, minHeight: 0}}>{children(ctx)}</div>
          {rail && placement === 'bottom' && <div style={{position: 'relative', width: '100%', height: railHeight, flex: `0 0 ${railHeight}px`}}>{rail(ctx)}</div>}
          {rail && placement === 'side' && <div style={{position: 'relative', width: railPx, flex: `0 0 ${railPx}px`, minWidth: 0}}>{rail(ctx)}</div>}
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
export const PhaseRail: React.FC<{phases: Phase[]; ctx: StageCtx; w?: number; color?: string; orientation?: 'vertical' | 'horizontal'; fontSize?: number; dotSize?: number}> = ({phases, ctx, w = 260, color, orientation = 'vertical', fontSize = 21, dotSize = 22}) => {
  const C = THEME.palette;
  const on = color ?? C.blue;
  // 当前绝对帧：phase.at + local。所有动画都从 phases[].at 派生 → 乱序渲染也确定。
  const f = ctx.phase.at + ctx.local;
  if (orientation === 'horizontal') return (
    <div style={{width: w, display: 'flex', alignItems: 'center', gap: 12}}>
      {phases.map((p, i) => {
        const done = i < ctx.index;
        const active = i === ctx.index;
        const take = ease(f, p.at, p.at + 14);
        const rowIn = ease(f, p.at - 14, p.at + 6);
        const pulse = active ? 1 + 0.18 * Math.sin(Math.PI * Math.min(1, take)) : 0;
        const halo = active ? (1 - take) * 7 : 0;
        const dotScale = active ? 1 + pulse * 0.18 : done ? 0.94 : 1;
        const connector = ease(f, p.at + 2, p.at + 14);
        return <React.Fragment key={p.state}>
          <div style={{display: 'flex', alignItems: 'center', gap: 10, flex: '0 0 auto', opacity: done || active ? 1 : 0.34, transform: `translateY(${(1 - rowIn) * -8}px)`}}>
            <span style={{width: dotSize, height: dotSize, borderRadius: 99, flex: '0 0 auto', display: 'grid', placeItems: 'center', background: done ? C.green : active ? on : C.mutedFill, color: C.white, fontFamily: 'Space', fontWeight: 700, fontSize: Math.max(13, dotSize * 0.58), boxShadow: halo > 0.4 ? `0 0 0 ${halo}px ${on}22` : 'none', transform: `scale(${dotScale})`}}>{done ? '✓' : i + 1}</span>
            <span style={{fontSize, fontWeight: 700, color: active ? on : C.ink, whiteSpace: 'nowrap'}}>{p.label ?? p.state}</span>
          </div>
          {i < phases.length - 1 && <div style={{height: 2, flex: '1 1 18px', minWidth: 12, background: C.line, overflow: 'hidden'}}><div style={{height: '100%', width: `${100 * connector}%`, background: done ? C.green : on}} /></div>}
        </React.Fragment>;
      })}
    </div>
  );
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
                  color: C.white, fontFamily: 'Space', fontWeight: 700, fontSize: 13,
                  boxShadow: halo > 0.4 ? `0 0 0 ${halo}px ${on}22` : 'none',
                  transform: `scale(${dotScale})`,
                }}
              >
                {done ? '✓' : i + 1}
              </span>
              <span style={{fontSize, fontWeight: 700, color: active ? on : C.ink, whiteSpace: 'nowrap'}}>{p.label ?? p.state}</span>
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

export const STAGEKIT_VERSION = 'stagekit-v6 · optional StageFrame + state machine + PhaseRail / optional SlotGuard diagnostic + header swap';
