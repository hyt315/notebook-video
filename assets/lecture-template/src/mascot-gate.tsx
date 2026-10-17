import React, {useEffect} from 'react';
import {continueRender, delayRender, useCurrentFrame} from 'remotion';
import {THEME} from './theme/active';

// ============================================================================
// MascotGate · 卡片压吉祥物 / 角落装饰（v4.3，warn）
//
// flat 的三张背景都在下方两角画了角色（蓝色机器人、珊瑚小方块 + 薄荷山丘），
// 大卡片（贴着 contentBand 底边 910、左右顶到 160/1760）会把它们**切掉半个头**——
// 角色被卡片截断读作「画错了」，比完全挡住更难看。
// 判据：任一「卡片」（不透明底 + 实线边框，z<140，非 data-gate-allow）与
// THEME.backgroundDecorZones 里**下方两角**的矩形相交超过 TOL 像素 → console.warn，
// 提示两种修法：缩小/上移卡片（内容区底边 ≤ 860），或给该镜写 `bg: 'quiet'`
// （quiet 变体的角色更低更小）。只在 watch 帧上量，useEffect + delayRender 兜住截帧。
// warn 而非 block：这是观感线，不该打断交付渲染。
// ============================================================================

const TOL = 24;
const SKIP_Z = 140;

const solidCard = (el: HTMLElement) => {
  const s = getComputedStyle(el);
  const m = /rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/.exec(s.backgroundColor || '');
  const alpha = m ? (m[4] === undefined ? 1 : parseFloat(m[4])) : 0;
  return alpha > 0.9 && parseFloat(s.borderTopWidth) > 0 && parseFloat(s.opacity || '1') > 0.5;
};

export const MascotGate: React.FC<{watch: number[]}> = ({watch}) => {
  const f = Math.round(useCurrentFrame());
  const zonesKey = JSON.stringify((THEME.backgroundDecorZones ?? []).filter((z) => z.y >= 700));
  useEffect(() => {
    const zones = JSON.parse(zonesKey) as {x: number; y: number; w: number; h: number}[];
    if (!zones.length || !watch.includes(f)) return;
    const handle = delayRender(`mascot-gate ${f}`, {timeoutInMilliseconds: 30000});
    let done = false;
    const finish = () => { if (!done) { done = true; continueRender(handle); } };
    const id = requestAnimationFrame(() => {
      try {
        const root = document.querySelector('[data-design-root]') as HTMLElement | null;
        if (!root) return;
        const rr = root.getBoundingClientRect();
        const k = rr.width / 1920;
        const hits: string[] = [];
        root.querySelectorAll<HTMLElement>('div').forEach((el) => {
          if (el.closest('[data-gate-allow]') || !solidCard(el)) return;
          let a: HTMLElement | null = el;
          while (a && a !== root) {
            const z = parseInt(getComputedStyle(a).zIndex || '0', 10);
            if (!Number.isNaN(z) && z >= SKIP_Z) return;
            a = a.parentElement;
          }
          const r = el.getBoundingClientRect();
          const b = {l: (r.left - rr.left) / k, t: (r.top - rr.top) / k, r: (r.right - rr.left) / k, btm: (r.bottom - rr.top) / k};
          for (const z of zones) {
            const ox = Math.min(b.r, z.x + z.w) - Math.max(b.l, z.x);
            const oy = Math.min(b.btm, z.y + z.h) - Math.max(b.t, z.y);
            if (ox > TOL && oy > TOL) hits.push(`card ${Math.round(b.l)},${Math.round(b.t)}–${Math.round(b.r)},${Math.round(b.btm)} overlaps corner decor ${z.x},${z.y} by ${Math.round(ox)}×${Math.round(oy)}px`);
          }
        });
        if (hits.length) console.warn(`[MascotGate] frame ${f}: ${hits.slice(0, 3).join(' | ')} → raise/shrink the card (content bottom ≤ 860) or set bg:'quiet' on this shot`);
      } finally {
        finish();
      }
    });
    return () => { cancelAnimationFrame(id); finish(); };
  }, [f, watch, zonesKey]);
  return null;
};
