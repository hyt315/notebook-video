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
// 转场清单（全片只用这 3 式，禁止每镜自创）：
//   cut        硬切（默认，最常用）
//   handoff    承接位移：同一对象跨镜延续，缩小移位让位
//   reveal     揭示：遮罩跟随，与 shotkit 的 reveal intent 共用时间线
//
// 帧约定：所有组件接收显式 f（本镜本地帧）。
// ============================================================================

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
// 原来还有 BASE_FPS 与 easeOut 两个局部 helper，本文件从头到尾没用过（tsc TS6133）。
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

/**
 * 转场清单：全片只用这 3 式。
 * ⚠️ 校验脚本**不读这里** —— `scripts/validate-composition.py` 自带同一份集合（其 `TRANSITIONS`），
 * 多样性的判据也在那边（按 shot 表的 `transition` 字段统计，与这个数组无关）。这里改了什么，
 * 门禁不会跟着变；两处必须人肉保持一致。
 */
export const TRANSITIONS = ['cut', 'handoff', 'reveal'] as const;
// v3.0.1：whip / paper-turn 已删除——它们在两条成片里零引用，且 whip 要真生效必须改交接引擎。
// cut 的真实实现是引擎的 10 帧叠帧（index.tsx），handoff 需要 carrier 声明，reveal 由 RevealMask 实现。
export type TransitionKind = (typeof TRANSITIONS)[number];

/**
 * 本模块版本串。清单**从 `TRANSITIONS` 派生**（不要让第二份手写副本再出现）：
 * 上一轮漂过一次 —— 数组已经删到 3 式，这串里还留着已删的 whip / paper-turn
 * （这串会渲进接触表第 ④ 页的页脚，所以"漂"是会被看见的）。
 * ⚠️ `scripts/validate-composition.py` 里仍自带一份集合（那份是判据，必须手写一致），
 * 改动 `TRANSITIONS` 时两处一起改。
 */
export const INSERT_VERSION = `insert-v3 · RevealMask · 转场清单（${TRANSITIONS.join('/')}）`;
