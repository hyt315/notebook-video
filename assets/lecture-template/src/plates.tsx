import React from 'react';
import {Easing, interpolate, staticFile} from 'remotion';
import {THEME} from './theme/active';
import {TYPE} from './kit';

// ============================================================================
// plates.tsx · 实拍素材框（ShotPlate）
//
// 用真实截图/官方图表当论据，比代码画出来的近似图更硬。风格仍按 cel 皮肤锁定：
// 2.5px 墨线 + 硬偏移阴影 + 纯平填充；推进只用 transform（确定性、无重排）。
// 帧参数名用 `f`（与 media/stagekit/charts 一致；fxkit 那一族才用 frame）。
// ============================================================================

const C = THEME.palette;
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const easeOut = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)});

export const ShotPlate: React.FC<{
  x: number; y: number; w: number; h: number; f: number;
  src: string;
  /** 出现节拍（本镜本地帧） */
  at?: number;
  /** 图上角标（说明这是什么图） */
  caption?: string;
  /** 右上角小标（如"官方图表"） */
  badge?: string;
  /** 推近焦点（0–1 归一化坐标），配合 zoom 使用 */
  focus?: {fx: number; fy: number};
  /** 目标放大倍率；1 = 不推近 */
  zoom?: number;
  /** 推进时长（帧） */
  dur?: number;
  fit?: 'cover' | 'contain';
  /** 底部署名/来源 */
  source?: string;
  z?: number;
}> = ({x, y, w, h, f, src, at = 0, caption, badge, focus = {fx: 0.5, fy: 0.5}, zoom = 1, dur = 90, fit = 'cover', source, z = 74}) => {
  const inP = easeOut(f, at, at + 22);
  const opP = easeOut(f, at, at + 16);
  const zP = easeOut(f, at + 6, at + 6 + dur);
  const k = 1 + (Math.max(1, zoom) - 1) * zP;
  // 焦点保持在画面内：把焦点拉到中心再放大
  const dx = (0.5 - focus.fx) * 100 * (k - 1);
  const dy = (0.5 - focus.fy) * 100 * (k - 1);
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, zIndex: z, opacity: opP, transform: `translateY(${(1 - inP) * 22}px) scale(${0.975 + 0.025 * inP})`}}>
      <div style={{position: 'absolute', inset: 0, background: C.paper, border: `2.5px solid ${C.ink}`, borderRadius: 12, boxShadow: `3.5px 3.5px 0 ${C.ink}`, overflow: 'hidden'}}>
        <img
          src={staticFile(src)}
          style={{
            position: 'absolute', inset: 0, width: '100%', height: '100%',
            objectFit: fit,
            transform: `scale(${k}) translate(${dx}%, ${dy}%)`,
            transformOrigin: '50% 50%',
          }}
        />
      </div>
      {caption && (
        <div style={{position: 'absolute', left: -2, top: -34, background: C.ink, color: C.white, borderRadius: 8, padding: '5px 14px', fontSize: 20, fontWeight: 700, opacity: easeOut(f, at + 8, at + 24)}}>{caption}</div>
      )}
      {badge && (
        <div style={{position: 'absolute', right: 0, top: -30, background: `${C.blue}18`, color: C.blue, border: `1.5px solid ${C.blue}66`, borderRadius: 999, padding: '3px 12px', fontSize: 16, fontWeight: 700, opacity: easeOut(f, at + 12, at + 28)}}>{badge}</div>
      )}
      {source && (
        <div style={{position: 'absolute', left: 4, bottom: -30, fontSize: 15, color: C.muted, fontFamily: 'Space,Kai', opacity: easeOut(f, at + 20, at + 36)}}>{source}</div>
      )}
    </div>
  );
};

export const PLATES_VERSION = 'plates-v1 · ShotPlate · 实拍素材框 · f 帧参数';
