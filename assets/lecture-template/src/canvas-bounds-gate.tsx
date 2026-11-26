import React from 'react';
import {useCurrentFrame} from 'remotion';
import {REPORT_EVERY, effectiveOpacity, useLayoutProbe} from './layout-probe';

// ============================================================================
// CanvasBoundsGate · 渲染期「画布越界」门禁
//
// 管「含文字的元素越出画布、字被切掉一截」：ClippingGate 只认 SVG 图元，CardFitGate 只量卡片内溢出，
// OverlapGate 只量互压，FillGate 只量铺到多低，构建期 coords-lint.py 不看 Corridor/ZoomStage 这类布局件。
//
// 判据：**含文字的叶元素**（HTML 叶 + SVG `text`/`tspan`）的**墨迹矩形**，扣掉会裁切的祖先之后，
//   仍越出视口（= composition 尺寸）≥ 6 像素 → 出声；**落定态**（有效不透明度 ≥0.98）越界 ≥ 20 像素 → 硬拦。
//   · 口径是**输出像素**（20px ≈ 15 设计像素），不做设计坐标回折；换 `--scale` 时判据跟着输出走。
//   · 只判文字叶元素，不判图形 / 版面件（那部分归 ClippingGate，避免同一元素重复报）；
//     因此一个越出画布、却不含文字的纯装饰块不归这道门管。
//   · 每帧都量，不做抽样；按需：只有墨迹越出画布的候选才读样式与祖先链。
//
// 挂载策略：
//   · 接触表（`NotebookVideoShowcase`）用 **block**：目录页缺件 = 画错了，必须中断渲染。
//   · 片子（`NotebookVideoFilm`）用 **warn**：硬拦发生在交付渲染的最后一刻，误报代价是整片不出；
//     出声照样进渲染日志，交付前人工确认（口径见 references/checks.md#render-gates）。
//
// 与 `ClippingGate` 同一条纪律：
//   · 测量排在 rAF 里 → **必须逐帧持 delayRender**，否则截帧先于测量，门禁等于不存在；
//   · 字体未就绪时 `document.fonts.ready` **要等**，不能 return（否则每帧都跳过）；
//   · 每 150 帧打一次覆盖率：让「没报」与「没跑」可区分；
//   · **硬拦时必须让 handle 保持未释放、并且不让自家 catch 吞掉 cancelRender 的异常**
//     —— `cancelRender()` 的实现是 `throw error`，被自家 catch 吞掉就会走到 release()
//     → `remotion_delayRenderHandles` 归零 → `remotion_renderReady = true`
//     （渲染器取状态时 "ready" 优先于 "cancelled"，见 @remotion/renderer/dist/seek-to-frame.js:46）
//     → **报了硬拦却照样出图 rc=0**。本件照抄 ClippingGate 的 `blocked` 处置。
// ============================================================================

export type BoundsIssue = {
  kind: 'bounds';
  frame: number;
  /** 元素的可读名（含文字前 12 字） */
  text: string;
  /** 越出的是哪条边 */
  edge: string;
  /** 越界量（像素） */
  over: number;
  settled: boolean;
};

/** 容差（像素）：行盒取整 / 亚像素抗锯齿会差几个像素，不算越界。 */
const TOL = 6;
/** 硬拦阈值（像素）：约半个字高，越过它字形就被切掉一截。 */
const BLOCK_PX = 20;
/** 落定 = 有效不透明度 ≥ 此值（入场途中元素还在画布外飞，那是运动，不是版面错误）。 */
const OPAQUE_FOR_SETTLED = 0.98;

/** 只挑**可能带墨迹**的元素：HTML 文字叶 + SVG `text`/`tspan`。 */
const TEXT_SEL = 'div,span,p,text,tspan';

type Box = {left: number; top: number; right: number; bottom: number};

/**
 * 元素的**墨迹矩形**：文字用 Range 取并集（真实字形），拿不到文本节点时退回 rect。
 * 块级容器整块宽不是字 —— 居中文字会被整块宽误判（与 `OverlapGate` 同一处置）。
 */
const inkBoxOf = (el: Element): Box => {
  const tns = Array.from(el.childNodes).filter((n) => n.nodeType === 3 && (n.nodeValue || '').trim());
  if (tns.length) {
    const rs = tns.flatMap((tn) => {
      const r = document.createRange();
      r.selectNodeContents(tn);
      return Array.from(r.getClientRects());
    });
    if (rs.length) {
      const l = Math.min(...rs.map((q) => q.left));
      const t = Math.min(...rs.map((q) => q.top));
      const rr = Math.max(...rs.map((q) => q.right));
      const b = Math.max(...rs.map((q) => q.bottom));
      if (rr - l > 0.5 && b - t > 0.5) return {left: l, top: t, right: rr, bottom: b};
    }
  }
  const r = el.getBoundingClientRect();
  return {left: r.left, top: r.top, right: r.right, bottom: r.bottom};
};

export const CanvasBoundsGate: React.FC<{
  mode?: 'warn' | 'block';
  /** 诊断用：每一帧都把扫过的文字叶数打出来（排误报时开） */
  debug?: boolean;
}> = ({mode = 'warn', debug = false}) => {
  const raw = Math.round(useCurrentFrame());
  // 骨架（逐帧持柄、等字体就绪、硬拦时 handle 不释放且异常不被自家 catch 吞）在 layout-probe.tsx
  useLayoutProbe({label: `CanvasBoundsGate @${raw}`, tag: '[CanvasBoundsGate]', timeoutInMilliseconds: 60000}, ({block}) => {
    const vw = window.innerWidth;   // Remotion 渲染时视口就是 composition 尺寸
    const vh = window.innerHeight;
    const issues: BoundsIssue[] = [];
    let scanned = 0;
    const overOf = (q: Box) => Math.max(-q.left, q.right - vw, -q.top, q.bottom - vh);
    document.querySelectorAll<Element>(TEXT_SEL).forEach((el) => {
      if (!(el.textContent || '').trim()) return;    // 只看**含文字**的（装饰块/底托天然出局）
      if (el.children.length) return;                // 只看**叶元素**（容器整块宽不是墨迹）
      if (el.closest('[data-gate-skip]') || el.closest('[data-gate-allow]')) return;
      // 引擎推近（data-cinema-focus）时画面是**有意**裁切的特写，版面是否越界在未推近的帧上量
      if (el.closest('[data-cinema-focus]')) return;
      let box = inkBoxOf(el);
      if ((box.right - box.left) * (box.bottom - box.top) < 4) return; // 无实体的占位节点
      scanned++;
      // 按需：裁切只会让墨迹变小，未裁切的墨迹都在画布内就不可能越界；样式与祖先链只对越界候选读。
      if (overOf(box) <= TOL) return;
      const cs = getComputedStyle(el as HTMLElement);
      if (cs.visibility === 'hidden' || cs.display === 'none') return;
      if (el.getClientRects().length === 0) return;  // 不参与布局（隐藏 / 未挂载）
      const op = effectiveOpacity(el);
      if (op < 0.05) return;                        // 还没出现 / 已经走了
      // 扣掉**会裁切的祖先**：取景框（`ZoomStage` 视口、接触表里 scale 过的格子）是有意裁切，
      // 被它裁住的部分不算越界。铺满整个视口的祖先不算裁切 —— 与它求交是恒等操作，
      // 却会把"越出画布"这件事一起抹掉。
      let n: Element | null = el.parentElement;
      while (n && n !== document.body) {
        const s = getComputedStyle(n as HTMLElement);
        if (s.overflowX !== 'visible' || s.overflowY !== 'visible') {
          const r = n.getBoundingClientRect();
          if (r.width > 1 && r.height > 1 && !(r.left <= 0.5 && r.top <= 0.5 && r.right >= vw - 0.5 && r.bottom >= vh - 0.5)) {
            box = {left: Math.max(box.left, r.left), top: Math.max(box.top, r.top), right: Math.min(box.right, r.right), bottom: Math.min(box.bottom, r.bottom)};
          }
        }
        n = n.parentElement;
      }
      if (box.right - box.left <= 0.5 || box.bottom - box.top <= 0.5) return; // 全被裁 → 看不见
      const over = overOf(box);
      if (over <= TOL) return;
      const edge = -box.left === over ? '左缘' : box.right - vw === over ? '右缘' : -box.top === over ? '上缘' : '下缘';
      issues.push({
        kind: 'bounds',
        frame: raw,
        text: `${(el.textContent || '').trim().slice(0, 12)} 越出${edge} ${Math.round(over)}px`,
        edge,
        over: Math.round(over),
        settled: op >= OPAQUE_FOR_SETTLED,
      });
    });

    if (issues.length) {
      const blocking = issues.filter((x) => x.settled && x.over >= BLOCK_PX);
      const msg =
        `[CanvasBoundsGate] @${raw} 共 ${issues.length} 处文字越出画布（落定态 ${blocking.length} 处）：` +
        issues.slice(0, 5).map((x) => x.text).join(' | ');
      if (typeof console !== 'undefined') console.warn(msg);
      if (mode === 'block' && blocking.length) {
        // 硬拦：handle 永不释放、异常不被吞（见 layout-probe.tsx）→ rc≠0 中止、不产出任何图。
        block(msg);
      }
    } else if ((debug || raw % REPORT_EVERY === 0) && typeof console !== 'undefined') {
      // 覆盖率：让「没报」与「没跑」可区分（旧门禁零输出两种含义混在一起）
      console.warn(`[CanvasBoundsGate] @${raw} 扫过 ${scanned} 个文字叶，无越界`);
    }
  }, [raw, mode, debug]);

  return null;
};

export const CANVAS_BOUNDS_GATE_VERSION =
  'canvas-bounds-gate-v2 · 只判**含文字的叶元素**（HTML 叶 + SVG text/tspan）的墨迹 rect 越出视口（= composition 尺寸），扣掉会裁切的祖先 · 输出像素口径，不做设计坐标回折 / 不判图形与版面件（与 ClippingGate 的重叠面因此消失）· delayRender 逐帧持柄 · 等字体就绪 · 每 150 帧覆盖率 · 落定态才硬拦 · 硬拦时 handle 不释放且异常不被自家 catch 吞';
