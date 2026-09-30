import React, {useEffect, useMemo} from 'react';
import {cancelRender, continueRender, delayRender, useCurrentFrame} from 'remotion';
import {useCanvas} from './theme/canvas';

// ============================================================================
// FillGate · 「下 1/4 有没有填满」的**实测**门（v1）
//
// 为什么要新写一个（2026-09-21）：这条判据（composition-gate.md 的 P0-4
// 「zones ∈[3,5]；bottomFill == true（底边接近 y=876，下 1/4 不留空洞）」）**本来就有门禁**，
// 但它查的是清单里的一个布尔字段：
//     `if s.get("bottomFill") is not True: → P0`
// 而 `bottomFill` 是**生成分镜表的脚本自己写死的常量**（make-shots.py 里每一镜都写 `True`），
// `resolve-shots.py` 再原样透传 —— 于是「生成器写 True → 门禁要求 True」，
// **这道门在结构上永远不可能失败**。实测成片里 17/21 镜的下三分之一是空的，它一次都没响。
// 改成实测：**量画面上真实的信息元素铺到多低**，再和 y=876 这条线比。
//
// 判据：把「信息元素」的 rect 取并集，取其**最低边**（设计坐标）。
//   · 信息元素 = 有文字的元素 ∪ 有真实边框的元素 ∪ 有真实描边的图形。
//     这样自然排除掉渐变底/调色层/整幅铺底（它们不上色就是"底"，不是"信息"）。
//   · z ≥ 140 的子树（章节卡 150 / 字幕 200）跳过：页眉与字幕不算场景内容。
//   · 与另三道门同一条纪律：**逐帧持 delayRender**（否则截帧先于测量，装了等于没装）、
//     **等 `document.fonts.ready`**（不能像旧版 OverlapGate 那样直接 return）。
//
// 为什么默认 warn 而不是 block：
//   「铺到多低」是**版面审美**（P0-4 是硬条款，但它的口径"底边接近 y=876"本身是观感线），
//   而"文字被裁 / 元素互相压 / 图形被裁"那三件是**画错了**，已经有门禁在硬拦。
//   为一条观感线把整片渲染打断，代价大于收益 → 出声、进日志、可复查。
//   （**不设 NODE_ENV 门**：渲染包是 production 模式，dev-only 的门在出片路径上永远看不到。）
// ============================================================================

/** 内容底线（设计坐标）：composition-gate.md P0-4 的同一个数，不新造魔数。 */
const FLOOR_Y = 876;
/** 容差（设计像素）：卡片下沿与底线差几个像素不算空洞。 */
const TOL = 24;
const SKIP_Z = 140;
const SAMPLE_EVERY = 15;
const EVENT_PAD = 2;
const REPORT_EVERY = 150;

type Box = {left: number; top: number; right: number; bottom: number};

const hasInk = (el: Element): boolean => {
  const s = getComputedStyle(el as HTMLElement);
  const bw = Math.max(
    parseFloat(s.borderTopWidth) || 0,
    parseFloat(s.borderRightWidth) || 0,
    parseFloat(s.borderBottomWidth) || 0,
    parseFloat(s.borderLeftWidth) || 0
  );
  if (bw > 0) {
    // 边框还得有颜色（transparent / 无色的不算）
    const bc = s.borderTopColor || '';
    const m = /rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/.exec(bc);
    if (!m || (m[4] !== undefined ? parseFloat(m[4]) : 1) > 0.15) return true;
  }
  return false;
};

const isPaintedGraphic = (el: Element): boolean => {
  const tag = el.tagName.toLowerCase();
  if (!['circle', 'ellipse', 'rect', 'line', 'polyline', 'polygon', 'path', 'text', 'tspan'].includes(tag)) return false;
  const s = getComputedStyle(el as unknown as HTMLElement);
  const stroke = s.stroke || 'none';
  const fill = s.fill || 'none';
  const sw = parseFloat(s.strokeWidth || '0') || 0;
  return (stroke !== 'none' && sw > 0) || (fill !== 'none' && fill !== 'transparent');
};

const infoBoxOf = (el: HTMLElement): Box | null => {
  const s = getComputedStyle(el);
  if (s.visibility === 'hidden' || parseFloat(s.opacity || '1') < 0.06) return null;
  const z = parseInt(s.zIndex || '0', 10);
  if (!Number.isNaN(z) && z >= SKIP_Z) return null;
  let anc = el.parentElement;
  while (anc && anc !== document.body) {
    const az = parseInt(getComputedStyle(anc).zIndex || '0', 10);
    if (!Number.isNaN(az) && az >= SKIP_Z) return null;
    anc = anc.parentElement;
  }
  // ⚠️ 必须要求「叶子」：`textContent` 会把**后代**的文字也算进来，于是任何包裹层
  // （最典型的是设计根自己）都"有文字"，它的盒子是整幅 1920×1080 → 底线恒等于 1080，
  // 门禁永远 PASS。实测（临时诊断打印最低元素）就是这么露出来的：
  // 最低的 5 个元素全是 `1080:DIV`，也就是设计根自己。
  // 有边框的容器仍然算（卡片的边框是真实的信息边界），所以这条只加在"文字"这一支上。
  const texted = el.children.length === 0 && !!(el.textContent || '').trim();
  if (!texted && !hasInk(el) && !isPaintedGraphic(el)) return null;
  const r = el.getBoundingClientRect();
  if (r.width * r.height < 16) return null;
  return {left: r.left, top: r.top, right: r.right, bottom: r.bottom};
};

export const FillGate: React.FC<{
  mode?: 'warn' | 'block';
  sampleEvery?: number;
  watch?: number[];
  floorY?: number;
}> = ({mode = 'warn', sampleEvery = SAMPLE_EVERY, watch, floorY = FLOOR_Y}) => {
  const raw = Math.round(useCurrentFrame());
  const {mode: canvasMode} = useCanvas();
  const watchKey = (watch || []).join(',');
  const hot = useMemo(() => {
    const s = new Set<number>();
    (watch || []).forEach((x) => {
      for (let d = -EVENT_PAD; d <= EVENT_PAD; d++) s.add(Math.round(x) + d);
    });
    return s;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchKey]);
  const should = raw % sampleEvery === 0 || hot.has(raw);

  useEffect(() => {
    if (!should) return;
    const handle = delayRender(`FillGate @${raw}`);
    let released = false;
    let cancelled = false;
    // 2026-09-21 实测修掉与 OverlapGate / ClippingGate 同源的「报而不拦」：
    // `cancelRender()` 的实现是 **`throw error`**，若它被本函数自己的 catch 吞掉、
    // 随后又 release()，handle 归零会让 `window.remotion_renderReady = true`；
    // 而渲染器取状态时 "ready" 优先于 "cancelled"
    // （@remotion/renderer/dist/seek-to-frame.js:46）→ 渲染照常成功。
    // 处置：硬拦时置 `blocked`（此后 release() 空转、handle 永不释放），
    // 且 blocked 之后异常原样抛出不吞。
    let blocked = false;
    const release = () => {
      if (released || blocked) return;
      released = true;
      continueRender(handle);
    };
    const measure = () => {
      if (cancelled) {
        release();
        return;
      }
      try {
        // 设计坐标 → 输出坐标的比例：从设计根实测，不假设（Remotion 的 --scale 会改它）
        const root = document.querySelector('[data-design-root]') as HTMLElement | null;
        if (!root) {
          release();
          return;
        }
        const rr = root.getBoundingClientRect();
        const k = rr.width / canvasMode.designW || 1;
        let bottom = -Infinity;
        let n = 0;
        document.querySelectorAll<HTMLElement>('div,span,p,svg,text,tspan,circle,ellipse,rect,path,line,polyline,polygon').forEach((el) => {
          if (el.closest('[data-gate-skip]')) return;
          if (el.closest('[data-gate-allow]')) return;
          const b = infoBoxOf(el);
          if (!b) return;
          n++;
          if (b.bottom > bottom) bottom = b.bottom;
        });
        if (!n || bottom === -Infinity) {
          release();
          return;
        }
        const designBottom = (bottom - rr.top) / k;
        const pass = designBottom >= floorY - TOL;
        if (!pass) {
          const msg =
            `[FillGate] @${raw} 内容底边只到 y=${Math.round(designBottom)}（设计坐标），` +
            `P0-4 要求接近 y=${floorY}（下 1/4 不留空洞）；本帧计 ${n} 个信息元素。` +
            `修法见 composition-gate.md：补一个**真实信息元素**（指标条/结论条/清单），不是放大现有卡片凑面积。`;
          if (typeof console !== 'undefined') console.warn(msg);
          if (mode === 'block') {
            // block 模式下才有拦的必要；blocked 置位后 handle 不再释放，
            // cancelRender 抛出的异常由下面的 catch 原样放行 → 渲染 rc≠0 且不产出图。
            blocked = true;
            cancelRender(new Error(msg));
            return;
          }
        } else if (raw % REPORT_EVERY === 0 && typeof console !== 'undefined') {
          console.warn(`[FillGate] @${raw} 内容底边 y=${Math.round(designBottom)} ≥ ${floorY}，下 1/4 已填（${n} 个信息元素）`);
        }
      } catch (e) {
        if (blocked) throw e;
        if (typeof console !== 'undefined') console.warn('[FillGate]', e);
      }
      release();
    };
    const id = requestAnimationFrame(() => {
      if (document.fonts && document.fonts.status !== 'loaded') {
        document.fonts.ready.then(() => { if (!cancelled) measure(); }).catch(() => measure());
        return;
      }
      measure();
    });
    return () => {
      cancelled = true;
      cancelAnimationFrame(id);
      release();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [raw, should, mode, sampleEvery, hot, floorY, canvasMode.designW]);

  return null;
};

export const FILL_GATE_VERSION =
  'fill-gate-v2 · 实测信息元素最低边 vs P0-4 的 y=876（替代原来那个"校验生成器自己写死的常量"的假门）· delayRender 逐帧持柄 · 等字体就绪 · 默认只出声不拦 · 硬拦时 handle 不释放且异常不被自家 catch 吞（v1 会出图 rc=0）';
