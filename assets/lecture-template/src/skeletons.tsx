import React from 'react';
import {Easing, interpolate, spring} from 'remotion';
import {THEME} from './theme/active';

// ============================================================================
// skeletons · 四种场景骨架 v2
//
//   Stage    单体舞台：一个主体在空间中演变（5–6 态）        → stagekit.StageFrame
//   Corridor 走廊：持久对象沿共享轨道移动，站点留下完成态      → 本文件 Corridor
//   Split    双栏对比：两侧各自入场，差异高亮                 → 本文件 SplitStage
//   Zoom     整体→聚焦→标注→回整体（纯代码局部放大，非图片）  → 本文件 ZoomStage
//
// v2 修掉的三类系统性缺陷（全部由静态坐标审计 + 逐帧审计发现）：
//   1. Corridor 的状态标签原本在承载物**下方 116px**，与站点标签只剩 3.6px 间距，
//      于是「标签压圆环、圆环压数字」在每个站点都发生 → 标签改到承载物**上方 46px**，
//      站点标签下移，两者之间留 40px 预算。
//   2. ZoomStage 的缩放矩阵**数学错误**：transform 写成 translate 再 scale，而 translate
//      用的是未缩放单位，于是「想聚焦的点」并不落在框心，且放大后内容被框裁掉
//      （实测四个场景被裁 100–500px）→ 改成标准 `translate(框心) scale(k) translate(-焦点)`
//      三段式，并按内容尺寸钳制 zoom 上限。
//   3. SplitStage 原本两侧同时同向入场、胜出只有一次边框跳变 → 改左先右后 6 帧、
//      分隔线先画后落徽章、胜出按「先让输的一方暗下去再点亮赢的一方」的因果顺序。
// ============================================================================

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const BASE_FPS = 30;
const easeIO = (f: number, a: number, b: number, from = 0, to = 1) => interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.inOut(Easing.cubic)});
const easeOut = (f: number, a: number, b: number, from = 0, to = 1) => interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)});
const easeIn = (f: number, a: number, b: number, from = 0, to = 1) => interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.in(Easing.quad)});
const popS = (f: number, start: number, stiffness = 150) => spring({frame: f - start, fps: BASE_FPS, config: {damping: 17, stiffness, mass: 0.86}});
/** 单向脉冲：0→1→0（拿来做「点一下」的强调，而不是永久呼吸）。 */
const pulse = (f: number, at: number, dur = 14) => Math.sin(Math.PI * Math.max(0, Math.min(1, (f - at) / dur)));

export const SKELETONS = ['Stage', 'Corridor', 'Split', 'Zoom'] as const;
export type SkeletonKind = (typeof SKELETONS)[number];

// ---------------------------------------------------------------------------
// Corridor · 走廊骨架
// 一个持久对象沿共享轨道穿过若干站点，每到一个站点改一次状态。
//
// v2 关键约定（修复重叠）：
//   · 对象状态标签在承载物**上方** `LABEL_ABOVE = 46px`（不要放下面——会和站点标签打架）；
//   · 站点标签在轨道下方 `STATION_DY = 96px`，与状态标签之间留出 ≥40px；
//   · 逐段 easeInOut + 每站停留 DWELL 帧（一次性全程缓动会让对象「路过」站点而不是「到站」）；
//   · 到达反馈 = 圆环脉冲 + 对勾**描线**（checkmark 是笔画，应当画出来而不是缩放入场）；
//   · 承载物只在**停驻时**呼吸，行驶中不呼吸（永久 idle 抖动不算语义变化）。
// ---------------------------------------------------------------------------
export type Station = {
  label: string;
  /** 对象到达本站点的帧（本镜本地帧） */
  at: number;
  detail?: string;
  color?: string;
  /** 到达后对象上显示的状态文字（渲染在承载物上方） */
  state?: string;
};

const DWELL = 10;      // 每站停留帧数
const LABEL_ABOVE = 46; // 状态标签相对承载物顶边的上移量
const STATION_DY = 96;  // 站点标签相对轨道中心的下移量

export const Corridor: React.FC<{
  x: number;
  y: number;
  w: number;
  f: number;
  stations: Station[];
  from?: number;
  to?: number;
  laneY?: number;
  z?: number;
  startBanner?: {at: number; text: string};
  /** 站点标签字号（默认 28）。标签是长 ASCII（如包名）时传 22，避免换行破坏对称。 */
  labelSize?: number;
}> = ({x, y, w, f, stations, from, to, laneY = 96, z = 72, startBanner, labelSize = 28}) => {
  const C = THEME.palette;
  const n = stations.length;
  const pts = stations.map((_, i) => x + (w / Math.max(1, n - 1)) * i);
  const laneScreenY = 40 + laneY;
  const carrierSize = 104; // 略小于站点圆环直径，避免完全盖住「到达」反馈
  const carrierTop = laneScreenY - carrierSize / 2;

  // 逐段行进：leg i 从 pts[i-1] 到 pts[i]，在 stations[i].at 处到站，然后停留 DWELL。
  // 用「当前帧落在哪一段」推导位置，纯函数、可乱序渲染。
  const legAt = (i: number) => stations[i].at;
  let cx = pts[0];
  for (let i = 1; i < n; i++) {
    const arrive = legAt(i);
    const start = legAt(i - 1) + DWELL;
    const u = easeIO(f, start, arrive);
    cx = pts[i - 1] + (pts[i] - pts[i - 1]) * u;
    if (f < arrive) break;
    cx = pts[i];
  }
  const arrived = stations.reduce((k, s) => (f >= s.at ? k + 1 : k), 0);
  const current = [...stations].reverse().find((s) => f >= s.at);
  const accent = current?.color ?? C.blue;
  // 只在停驻（到站后 DWELL 内）呼吸；行驶中不呼吸。
  const dwellLocal = current ? f - current.at : 0;
  const breathing = dwellLocal >= 0 && dwellLocal <= DWELL ? 1 + 0.02 * Math.sin(dwellLocal * 0.045) : 1;
  // 最后一段加衰减残影（只加一段，不要每段都拖尾——那是第二个持续运动）
  const trailing = arrived >= n && f - stations[n - 1].at < 20;

  return (
    <div style={{position: 'absolute', left: 0, top: y, width: 1920, height: 460, zIndex: z}}>
      {startBanner && (
        <div style={{position: 'absolute', left: x, top: 0, opacity: easeOut(f, startBanner.at, startBanner.at + 14), fontSize: 26, fontWeight: 700, color: C.muted}}>{startBanner.text}</div>
      )}
      <svg width={1920} height={460} viewBox="0 0 1920 460" style={{position: 'absolute', left: 0, top: 40}}>
        <line x1={pts[0]} y1={laneY} x2={pts[n - 1]} y2={laneY} stroke={C.line} strokeWidth={10} strokeLinecap="round" />
        <line x1={pts[0]} y1={laneY} x2={cx} y2={laneY} stroke={C.blue} strokeWidth={10} strokeLinecap="round" />
        {pts.map((px, i) => {
          const s = stations[i];
          const at = s.at;
          const on = f >= at;
          const color = s.color ?? C.blue;
          const ring = pulse(f, at, 16);            // 到达脉冲：0→1→0
          const checkP = easeOut(f, at, at + 12);      // 对勾描线
          return (
            <g key={s.label}>
              <circle cx={px} cy={laneY} r={52} fill={C.paperBase} stroke={on ? color : C.line} strokeWidth={3.5} />
              {ring > 0 && <circle cx={px} cy={laneY} r={52 + 26 * ring} fill="none" stroke={color} strokeWidth={3} opacity={0.28 * (1 - ring)} />}
              {on && (
                <path
                  d={`M${px - 14} ${laneY} l10 11 22-26`}
                  stroke={C.green} strokeWidth={7} fill="none" strokeLinecap="round" strokeLinejoin="round"
                  pathLength={1} strokeDasharray={1} strokeDashoffset={1 - checkP}
                />
              )}
            </g>
          );
        })}
      </svg>
      {stations.map((s, i) => {
        const on = f >= s.at;
        const color = s.color ?? C.blue;
        // 站点文字三拍入场：编号 → 标签 → 说明（先到站、再确认、后解释）
        const numP = easeOut(f, s.at, s.at + 10);
        const labP = easeOut(f, s.at + 3, s.at + 16);
        const detP = easeOut(f, s.at + 8, s.at + 22);
        return (
          <div key={s.label} style={{position: 'absolute', left: pts[i] - 150, top: 40 + laneY + STATION_DY, width: 300, textAlign: 'center'}}>
            <div style={{fontFamily: 'Space', fontSize: 17, color: C.blue, marginBottom: 4, opacity: numP, letterSpacing: 6 * (1 - numP)}}>0{i + 1}</div>
            <div style={{fontSize: labelSize, fontWeight: 700, color: on ? color : C.muted, opacity: on ? labP : 0.4, transform: `translateY(${(1 - labP) * 14}px)`, whiteSpace: labelSize <= 24 ? 'nowrap' : undefined}}>{s.label}</div>
            {s.detail && <div style={{fontSize: 21, fontWeight: 600, color: C.muted, marginTop: 6, opacity: detP, transform: `translateY(${(1 - detP) * 10}px)`}}>{s.detail}</div>}
          </div>
        );
      })}
      {/* 衰减残影：只在最后一段刚到时出现 */}
      {trailing && [1, 2, 3, 4].map((k) => (
        <div key={k} style={{position: 'absolute', left: cx - carrierSize / 2 - k * 14, top: carrierTop, width: carrierSize, height: carrierSize, opacity: 0.18 / k, transform: 'scale(1)', pointerEvents: 'none'}}>
          <svg width={carrierSize} height={carrierSize} viewBox="0 0 120 112"><rect x={10} y={9} width={100} height={91} rx={22} fill={C.green} /></svg>
        </div>
      ))}
      {/* 持久对象：状态随站点改变，全程不卸载 */}
      <div style={{position: 'absolute', left: cx - carrierSize / 2, top: carrierTop, width: carrierSize, height: carrierSize, transform: `scale(${breathing})`, transformOrigin: 'center'}}>
        <svg width={carrierSize} height={carrierSize} viewBox="0 0 120 112">
          <rect x={10} y={9} width={100} height={91} rx={22} fill={arrived >= n ? C.green : accent} />
          <path d="M34 36H86M34 51H73M34 66H63" stroke="#fff" strokeWidth={5} strokeLinecap="round" />
          {arrived >= n && <path d="m70 79 8 8 19-23" fill="none" stroke="#fff" strokeWidth={6} strokeLinecap="round" strokeLinejoin="round" />}
        </svg>
      </div>
      {/* 状态标签：在承载物**上方**（下方会与站点标签重叠）。
          切换时：当前标签跟随承载物；上一个标签锚在**它自己的站点 x** 上淡出——
          若让它跟着承载物走，两个标签会叠在一起（实测门禁报到 3500px²）。 */}
      {stations.map((s, i) => {
        if (!s.state) return null;
        const isCurrent = current === s;
        const isLeaving = !isCurrent && stations[i + 1] === current;
        if (!isCurrent && !isLeaving) return null;
        const nextAt = stations[i + 1]?.at ?? s.at;
        const p = isCurrent ? easeOut(f, s.at, s.at + 12) : 1 - easeIn(f, nextAt, nextAt + 6);
        if (p <= 0.01) return null;
        const labelX = isCurrent ? cx : pts[i];
        return (
          <div key={`st-${s.label}`} style={{position: 'absolute', left: labelX - 122, top: carrierTop - LABEL_ABOVE, width: 244, textAlign: 'center', opacity: p, transform: `translateY(${(isCurrent ? 1 - p : -(1 - p)) * 12}px)`}}>
            <span style={{fontSize: 20, fontWeight: 700, color: isCurrent ? accent : C.muted, whiteSpace: 'nowrap'}}>{s.state}</span>
          </div>
        );
      })}
    </div>
  );
};

// ---------------------------------------------------------------------------
// SplitStage · 双栏对比骨架
// v2：左侧先入场 6 帧（同侧对称入场读作「两张幻灯片」）；分隔线先画、徽章后落；
//     胜出按因果顺序：先让输的一方暗/去饱和/下沉，再点亮赢的一方，最后落徽章。
// ---------------------------------------------------------------------------
export const SplitStage: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  f: number;
  left: {title: string; sub?: string; rows: string[]; color?: string};
  right: {title: string; sub?: string; rows: string[]; color?: string};
  winner?: 'left' | 'right' | null;
  winnerAt?: number;
  z?: number;
}> = ({x, y, w, h, f, left, right, winner = null, winnerAt = 0, z = 72}) => {
  const C = THEME.palette;
  const colW = (w - 40) / 2;
  const panel = (side: 'left' | 'right', data: {title: string; sub?: string; rows: string[]; color?: string}, cx: number) => {
    const color = data.color ?? (side === 'left' ? C.blue : C.green);
    const dir = side === 'left' ? -1 : 1;
    const lead = side === 'left' ? 0 : 6; // 左侧先来 6 帧
    const p = easeOut(f, lead, lead + 24);
    const isWin = winner === side;
    const lose = winner && !isWin;
    // 因果顺序：输方先暗（T）→ 赢方边框（T+4）→ 赢方放大（T+8）→ 徽章（T+20）
    const loseP = lose ? easeIO(f, winnerAt, winnerAt + 14) : 0;
    const winP = isWin ? easeOut(f, winnerAt + 4, winnerAt + 18) : 0;
    const zoomP = isWin ? pulse(f, winnerAt + 8, 14) : 0;
    const badgeP = isWin ? easeOut(f, winnerAt + 20, winnerAt + 30) : 0;
    return (
      <div
        style={{
          position: 'absolute', left: cx, top: 0, width: colW, height: h,
          opacity: p * (1 - loseP * 0.55),
          transform: `translateX(${dir * 60 * (1 - p)}px) translateY(${loseP * 6}px) scale(${(1 - loseP * 0.015) * (1 + zoomP * 0.03)})`,
        }}
      >
        <div style={{position: 'absolute', inset: 0, background: C.paper, border: `${2.5 + winP * 0.5}px solid ${isWin && winP > 0.3 ? color : C.line}`, borderRadius: 14, boxShadow: `${3 + winP * 2}px ${3 + winP * 2}px 0 ${isWin && winP > 0.3 ? color : C.ink}`, filter: loseP > 0 ? `saturate(${1 - loseP * 0.65})` : undefined}} />
        <div style={{position: 'absolute', left: 28, top: 24}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <span style={{width: 14, height: 14, borderRadius: 99, background: color}} />
            <span style={{fontFamily: 'Space', fontSize: 27, fontWeight: 700, color}}>{data.title}</span>
            {isWin && badgeP > 0.05 && (
              <span style={{fontSize: 20, fontWeight: 700, color: '#fff', background: color, borderRadius: 999, padding: '2px 12px', opacity: badgeP, transform: `scale(${0.8 + 0.35 * Math.sin(Math.PI * Math.min(1, badgeP))})`}}>胜出</span>
            )}
          </div>
          {data.sub && <div style={{fontSize: 21, fontWeight: 600, color: C.muted, marginTop: 6}}>{data.sub}</div>}
        </div>
        <div style={{position: 'absolute', left: 28, right: 28, top: 108, display: 'flex', flexDirection: 'column', gap: 14}}>
          {data.rows.map((r, i) => {
            const rp = easeOut(f, 8 + i * 10, 8 + i * 10 + 14);
            // 输方的行：逐行划掉（比整体降透明度更能说明「被否决」）
            const strike = lose ? easeOut(f, winnerAt + 6 + i * 4, winnerAt + 16 + i * 4) : 0;
            return (
              <div key={r} style={{position: 'relative', fontSize: 23, fontWeight: 700, color: isWin && winP > 0.5 ? color : C.ink, opacity: rp * (1 - loseP * 0.45), transform: `translateX(${16 * (1 - rp)}px)`}}>
                {r}
                {strike > 0 && <span style={{position: 'absolute', left: 0, top: '52%', height: 2, width: `${strike * 100}%`, background: C.muted, opacity: 0.7}} />}
              </div>
            );
          })}
        </div>
      </div>
    );
  };
  // 分隔线：先「画出来」，徽章才落上去
  const lineP = easeOut(f, 30, 44);
  const badgeP = easeOut(f, 44, 54);
  const badgeRing = pulse(f, 44, 16);
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, zIndex: z}}>
      {panel('left', left, 0)}
      {panel('right', right, colW + 40)}
      <div style={{position: 'absolute', left: colW + 19, top: 20, width: 3, height: h - 40, background: C.line, borderRadius: 2, transformOrigin: 'top center', opacity: lineP, transform: `scaleY(${lineP})`}} />
      {badgeP > 0.02 && (
        <div style={{position: 'absolute', left: colW - 4, top: h / 2 - 26, width: 56, height: 56, borderRadius: 99, background: C.paperBase, border: `2px solid ${C.line}`, display: 'grid', placeItems: 'center', fontFamily: 'Space', fontWeight: 700, fontSize: 22, color: C.muted, opacity: badgeP, boxShadow: badgeRing > 0.02 ? `0 0 0 ${badgeRing * 8}px ${C.line}` : 'none', transform: `scale(${0.9 + 0.25 * Math.sin(Math.PI * Math.min(1, badgeP))})`}}>VS</div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// ZoomStage · 整体 → 聚焦 → 标注 → 回整体
//
// v2 修掉两个致命问题：
//   · 变换顺序错误：原来 `translate(tx,ty) scale(k)` 的 tx 用未缩放单位，导致「要聚焦的点」
//     不落在框心、放大后内容被框裁掉（实测被裁 100–500px）。正确写法是
//     `translate(框心) scale(k) translate(-焦点)` 三段式。
//   · 没有缩放上限：按内容尺寸钳制 `k ≤ min(框宽/内容宽, 框高/内容高)`，否则必然裁切。
//     不知道内容尺寸时用保守默认，宁可少放大也不要裁掉内容。
// ---------------------------------------------------------------------------
export const ZoomStage: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  f: number;
  /** 聚焦点（相对框内的归一化坐标） */
  focus: {fx: number; fy: number};
  zoom?: number;
  /** 三个节拍帧：开始聚焦 / 标注出现 / 回到整体 */
  at: {focus: number; annotate: number; back: number};
  label?: string;
  z?: number;
  /** 内容的实际尺寸（设计像素）。给了就按它钳制缩放，避免放大后裁切。 */
  contentW?: number;
  contentH?: number;
  children?: React.ReactNode;
}> = ({x, y, w, h, f, focus, zoom = 1.9, at, label, z = 72, contentW, contentH, children}) => {
  const C = THEME.palette;
  // 缩放上限：内容放不进框就别放那么大。默认按「内容与框同尺寸」保守处理。
  const capW = w / Math.max(1, contentW ?? w);
  const capH = h / Math.max(1, contentH ?? h);
  const kMax = Math.max(1, Math.min(capW, capH));
  const k = 1 + (Math.min(zoom, kMax) - 1) * easeIO(f, at.focus, at.annotate) * (1 - easeIO(f, at.back, at.back + 26));
  const chip = easeOut(f, at.annotate, at.annotate + 18) * (1 - easeIn(f, at.back, at.back + 6));
  const dim = easeIO(f, at.focus, at.annotate) * (1 - easeIO(f, at.back, at.back + 20));
  const fxp = focus.fx * w;
  const fyp = focus.fy * h;
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, zIndex: z}}>
      <div style={{position: 'absolute', inset: 0, overflow: 'hidden', borderRadius: 14, background: C.paper, border: `2.5px solid ${C.line}`}}>
        {/* 三段式：先平移到框心，再缩放，再把焦点平移回原点 —— 这样焦点一定落在框心 */}
        <div style={{position: 'absolute', inset: 0, transformOrigin: '0 0', transform: `translate(${w / 2}px, ${h / 2}px) scale(${k}) translate(${-fxp}px, ${-fyp}px)`, filter: dim > 0 ? `brightness(${1 + dim * 0.04})` : undefined}}>{children}</div>
        {/* 框内暗角：让聚焦读成「打光」而不是单纯放大 */}
        {dim > 0.01 && <div style={{position: 'absolute', inset: 0, borderRadius: 14, boxShadow: `inset 0 0 0 9999px rgba(20,17,15,${0.1 * dim})`, pointerEvents: 'none'}} />}
        <div style={{position: 'absolute', inset: 0, boxShadow: `inset 0 0 0 2px ${C.line}`, borderRadius: 14, pointerEvents: 'none'}} />
      </div>
      {label && chip > 0.02 && (
        <>
          {/* 引线：从标注指向焦点，画出来（stroke 用 dashoffset 描线，不用缩放弹出） */}
          <svg width={w} height={h} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
            {(() => {
              const cx0 = 18, cy0 = h - 20, cx1 = fxp, cy1 = fyp;
              const lineP = easeOut(f, at.annotate + 2, at.annotate + 16);
              return <>
                <line x1={cx0} y1={cy0} x2={cx0 + (cx1 - cx0) * lineP} y2={cy0 + (cy1 - cy0) * lineP} stroke={C.muted} strokeWidth={1.5} strokeDasharray="6 6" />
                {lineP > 0.9 && <circle cx={cx1} cy={cy1} r={4} fill={C.orange} />}
              </>;
            })()}
          </svg>
          <div style={{position: 'absolute', left: 18, bottom: 18, opacity: chip, transform: `translateY(${(1 - chip) * 10}px)`, background: C.ink, color: C.white, borderRadius: 10, padding: '10px 18px', fontSize: 24, fontWeight: 700}}>{label}</div>
        </>
      )}
    </div>
  );
};

export const SKELETON_VERSION = 'skeletons-v2 · Stage/Corridor/Split/Zoom · state-label-above + correct zoom math';
