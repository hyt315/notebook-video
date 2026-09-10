import React from 'react';
import {Easing, interpolate} from 'remotion';
import {THEME} from './theme/active';

// ============================================================================
// insert · 辅助取证层（B 场景）+ 转场清单 v1
//
// 两个概念（references/media-routing.md）：
//   A 场景 = 主线演化轨：一个主体常驻，随旁白换内部状态（StageFrame）。
//   B 场景 = 辅助取证轨：换一种视觉介质插 0.8–2 秒，说完即回。
//            B 不是「另一个场景」，而是 A 的一次注意力转移；不留残片、不另起场景。
//
// 转场清单（全片只用这 5 式，禁止每镜自创）：
//   cut        硬切（默认，最常用）
//   handoff    承接位移：同一对象跨镜延续，缩小移位让位
//   whip       甩镜：1–3 帧快甩 + 手绘速度线（零依赖，不用 motion-blur 包）
//   reveal     揭示：遮罩跟随，与 shotkit 的 reveal intent 共用时间线
//   paper-turn 纸翻：只在章节切换用
//
// 帧约定：所有组件接收显式 f（本镜本地帧）。
// ============================================================================

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const BASE_FPS = 30;
const easeOut = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)});
const easeIO = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.inOut(Easing.cubic)});

export type Pose = {x: number; y: number; scale: number};

/**
 * useHandoff：承接位移。上一镜的对象不会消失再重画，而是缩小移位、让位给新主体。
 * 返回一个在 frames 帧内从 prev 过渡到 next 的姿态；prev 为空时直接返回 next。
 */
export const useHandoff = (prev: Pose | null | undefined, next: Pose, f: number, frames = 16): Pose => {
  if (!prev) return next;
  const p = easeIO(f, 0, frames);
  return {
    x: prev.x + (next.x - prev.x) * p,
    y: prev.y + (next.y - prev.y) * p,
    scale: prev.scale + (next.scale - prev.scale) * p,
  };
};

// ---------------------------------------------------------------------------
// InsertShot：B 场景插入镜头。dur 硬约束 24–60 帧（0.8–2s），
// 结束后完全卸载（返回 null），不留隐藏碎片——这是「不另起场景」的物理保证。
// ---------------------------------------------------------------------------
export const INSERT_MIN = 24;
export const INSERT_MAX = 60;

export const InsertShot: React.FC<{
  at: number;
  dur: number;
  f: number;
  z?: number;
  /** 入场方式：'wash' 羽化淡入（默认）/ 'slide' 侧滑 / 'scale' 弹入 */
  enter?: 'wash' | 'slide' | 'scale';
  children?: React.ReactNode;
}> = ({at, dur, f, z = 118, enter = 'wash', children}) => {
  if (dur < INSERT_MIN || dur > INSERT_MAX) {
    if (process.env.NODE_ENV !== 'production') console.warn(`[insert] dur 应在 ${INSERT_MIN}–${INSERT_MAX} 帧，收到 ${dur}`);
  }
  // 完全卸载：区间外返回 null，不保留任何残片
  if (f < at || f >= at + dur) return null;
  const local = f - at;
  const fin = Math.min(10, Math.round(dur * 0.22));
  const p = enter === 'scale' ? easeOut(local, 0, fin) : easeIO(local, 0, fin);
  const out = easeIO(local, dur - fin, dur);
  const shift = enter === 'slide' ? (1 - p) * 120 : 0;
  const scale = enter === 'scale' ? 0.9 + 0.1 * p : 1;
  return (
    <div style={{position: 'absolute', inset: 0, zIndex: z, opacity: p * (1 - out), transform: `translateX(${shift}px) translateY(${(1 - p) * 18}px) scale(${scale})`}}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// WhipStreak：手绘速度线。替代 @remotion/motion-blur 的零依赖方案——
// 甩镜读起来像真镜头，靠的是方向一致的速度线 + 极短时长，而不是采样模糊。
// ---------------------------------------------------------------------------
export const WhipStreak: React.FC<{f: number; at: number; dur?: number; dir?: 'left' | 'right'; color?: string}> = ({f, at, dur = 8, dir = 'right', color}) => {
  const C = THEME.palette;
  const c = color ?? C.ink;
  if (f < at || f > at + dur) return null;
  const p = easeOut(f, at, at + dur);
  const fade = 1 - Math.abs(p - 0.5) * 2;
  const k = dir === 'right' ? 1 : -1;
  const lines = [0, 1, 2, 3, 4, 5, 6, 7];
  return (
    <div style={{position: 'absolute', inset: 0, zIndex: 130, pointerEvents: 'none', opacity: fade * 0.85}}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
        {lines.map((i) => {
          const y = 120 + i * 118;
          const len = 300 + ((i * 137) % 520);
          const x0 = k > 0 ? -len + p * (1920 + len) : 1920 - p * (1920 + len);
          return <line key={i} x1={x0} y1={y} x2={x0 + k * len} y2={y} stroke={c} strokeWidth={i % 3 === 0 ? 5 : 2.5} strokeLinecap="round" opacity={0.18 + (i % 4) * 0.14} />;
        })}
      </svg>
    </div>
  );
};

// ---------------------------------------------------------------------------
// HandoffCarrier：跨镜延续的载体对象。把它放进两镜各自的 ShotCamera 内，
// 用 useHandoff 给出的姿态驱动，即可实现「同一对象跨镜延续」。
// ---------------------------------------------------------------------------
export const HandoffCarrier: React.FC<{
  pose: Pose;
  f: number;
  label?: string;
  complete?: boolean;
  size?: number;
  z?: number;
}> = ({pose, f, label, complete = false, size = 120, z = 96}) => {
  const C = THEME.palette;
  const breathe = 1 + 0.012 * Math.sin(f * 0.16);
  return (
    <div style={{position: 'absolute', left: pose.x - size / 2, top: pose.y - size / 2, width: size, height: size, zIndex: z, transform: `scale(${pose.scale * breathe})`, transformOrigin: 'center'}}>
      <svg width={size} height={size} viewBox="0 0 120 112">
        <rect x={10} y={9} width={100} height={91} rx={22} fill={complete ? C.green : C.blue} />
        <path d="M34 36H86M34 51H73M34 66H63" stroke="#fff" strokeWidth={5} strokeLinecap="round" />
        {complete && <path d="m70 79 8 8 19-23" fill="none" stroke="#fff" strokeWidth={6} strokeLinecap="round" strokeLinejoin="round" />}
      </svg>
      {label && <div style={{fontSize: 20, fontWeight: 700, textAlign: 'center', whiteSpace: 'nowrap', marginTop: 2, color: C.ink}}>{label}</div>}
    </div>
  );
};

// ---------------------------------------------------------------------------
// PaperTurn：纸翻转场（只用于章节切换）。
// ---------------------------------------------------------------------------
export const PaperTurn: React.FC<{f: number; at: number; dur?: number; children?: React.ReactNode}> = ({f, at, dur = 16, children}) => {
  if (f < at) return null;
  const p = easeOut(f, at, at + dur);
  if (p <= 0) return null;
  return (
    <div style={{position: 'absolute', inset: 0, perspective: 1600, zIndex: 120}}>
      <div style={{position: 'absolute', inset: 0, transform: `rotateY(${-70 * (1 - p)}deg)`, transformOrigin: '0 50%', opacity: Math.min(1, p * 2.2)}}>{children}</div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// RevealMask：揭示转场。与 shotkit 的 'reveal' intent 共用时间线，
// 遮罩推进与相机推进同向同速，让「转场」本身成为视觉表达而不是硬切前的淡出。
// ---------------------------------------------------------------------------
export const RevealMask: React.FC<{f: number; at: number; dur?: number; dir?: 'ltr' | 'rtl' | 'ttb'; children?: React.ReactNode}> = ({f, at, dur = 20, dir = 'ltr', children}) => {
  const p = easeIO(f, at, at + dur);
  const inset = dir === 'rtl' ? `0 0 0 ${p * 100}%` : dir === 'ttb' ? `0 0 ${(1 - p) * 100}% 0` : `0 ${(1 - p) * 100}% 0 0`;
  const edge = dir === 'ttb' ? {top: `${p * 100}%`, left: 0, right: 0, height: 6} : {top: 0, bottom: 0, left: `calc(${p * 100}% - 3px)`, width: 6};
  return (
    <div style={{position: 'absolute', inset: 0, zIndex: 120, overflow: 'hidden'}}>
      <div style={{position: 'absolute', inset: 0, clipPath: `inset(${inset})`}}>{children}</div>
      <div style={{position: 'absolute', ...edge, background: THEME.palette.orange, opacity: p < 1 ? 1 : 0}} />
    </div>
  );
};

/** 转场清单：全片只用这 5 式。校验脚本据此检查多样性。 */
export const TRANSITIONS = ['cut', 'handoff', 'whip', 'reveal', 'paper-turn'] as const;
export type TransitionKind = (typeof TRANSITIONS)[number];

export const INSERT_VERSION = 'insert-v1 · B-roll insert 24-60f · 5 transitions';
