import React, {useEffect} from 'react';
import {cancelRender, continueRender, delayRender, useCurrentFrame} from 'remotion';

// ============================================================================
// CanvasBoundsGate · 渲染期「画布越界」门禁（v2 · 简版，2026-09-22 换实现）
//
// 为什么需要它（2026-09-21，用户在接触表上**用眼睛**看出来的那一类）：
//   `NotebookVideoShowcase` 第 ⑥ 页第三站的标签块越出画布右缘被裁 ——
//   文案「按 Flash 结算」实际渲成「按 Flash 结」。根因是 `Corridor x={100} w={1720}`
//   让标签块伸到设计 x=2010，而组件内标签块固定 `left: pts[i]-150, width: 300`。
//   这一件**四道渲染期门禁 + 构建期一条都没响**：`ClippingGate` 只认 SVG 图元（没有 div）；
//   `CardFitGate` 只量"卡片内容有没有溢出卡片"；`OverlapGate` 只量元素互相压；`FillGate` 只量铺到多低；
//   构建期 `coords-lint.py` 明确把 `Corridor`/`ZoomStage` 这类**布局件**排除在外（它们的 x/w 是容器坐标）。
//   于是整条「越界 → 被画布裁掉 → 文字少半截」的链路一个门禁都没响，只能靠人眼抽查。本件补这个洞。
//
// 判据（v2）：**含文字的叶元素**（HTML 叶 + SVG `text`/`tspan`）的**墨迹矩形**，扣掉会裁切的祖先之后，
//   仍越出视口（= composition 尺寸）≥ 6 像素 → 出声；**落定态**（有效不透明度 ≥0.98）越界 ≥ 20 像素 → 硬拦。
//
// v2 相对 v1（468 行）砍掉的四件**复杂度**，每件都写了"为什么砍"（2026-09-22 实测，不是猜）：
//   ① 不做**设计坐标回折**（`[data-design-root]` 实测比例 k、`ShotCamera` 逆变换、世界层判定）。
//      v1 为此养了三个近似函数；实测两种口径在接触表上抓到的是**同一批**真缺陷
//      （第 ⑥ 页 `26px × 2`、第 ③ 页 `27px`），而在 2560×1440 的片子上它一次真缺陷都没报出过。
//      代价如实写：片子上的阈值是**输出像素**（20px ≈ 15 设计像素），换 `--scale` 时判据跟着输出走。
//   ② 不做**图形 / 版面件**分支（SVG 图元、"有可见边框或实底且含文字"的块）。v1 的那半边与
//      `ClippingGate`（图元被 svg 视口或 overflow 祖先裁掉）会在**同一批元素上重复报**。
//      只判文字叶元素天然避开这个重复 —— 这也是把它砍掉最主要的原因。
//   ③ 不做"铺底/底托 ≥92% 画布"、"z ≥ 140 锁定 chrome 层"、"小型取景框内的放大内容"那一整套排除：
//      它们的存在意义全是"别让**图形/版面块**误报"，而 v2 根本不判图形/版面块。
//   ④ 不做按帧抽样 / 事件帧 `watch`：v2 每帧都量（一次 DOM 扫描 + Range 取字），少一层采样逻辑。
//   判据收窄的**代价**（如实写）：一个越出画布、但一个文字都没有的装饰块（`Tape` 那类斜纹胶带）
//   不会被它抓到。那件事 `ClippingGate` 也不管（它只判"有裁切祖先"的情形）—— 这是**已知的空白**，
//   不是这条门禁的失职：这条门禁的名字与职责就是"文字有没有被画布切掉"。
//
// 挂载策略（v2 改动，理由留在这里，免得下次又被"统一成 block"）：
//   · 接触表（`NotebookVideoShowcase`）保持 **block**：越界的件是**整件看不见 / 被切掉一块**，
//     而接触表是"看见才会用"的唯一入口 —— 目录页缺件 = 画错了，必须中断渲染
//     （第 ③ 页第 5 件落在画布外 466px 就是这么漏掉的）。
//   · 片子（`NotebookVideoFilm`）取 **warn**：这一版判据在**片子**上的价值尚未被证明
//     （实测来源全是接触表），而它的硬拦发生在**交付渲染的最后一刻** —— 判据一旦误报，
//     代价是"整片渲到最后一帧被打断、不出片"，远贵于漏报一处 20px 的裁切。
//     出水照样在渲染日志里，交付前人工确认（口径见 references/composition-gate.md §5.2/§6）。
//
// 与 `ClippingGate` 同一条纪律（这个仓库踩过的坑，一条都不重犯）：
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
/** 硬拦阈值（像素）：约半个字高。实测接触表那处「按 Flash 结算」被裁 26px（字被切掉一截）。 */
const BLOCK_PX = 20;
/** 落定 = 有效不透明度 ≥ 此值（入场途中元素还在画布外飞，那是运动，不是版面错误）。 */
const OPAQUE_FOR_SETTLED = 0.98;
const REPORT_EVERY = 150;

/** 只挑**可能带墨迹**的元素：HTML 文字叶 + SVG `text`/`tspan`。 */
const TEXT_SEL = 'div,span,p,text,tspan';

type Box = {left: number; top: number; right: number; bottom: number};

/** 元素与其祖先的**有效**不透明度乘积（<0.02 一律当 0：还没出现 / 已经走了）。 */
const effectiveOpacity = (el: Element) => {
  let o = 1;
  let n: Element | null = el;
  while (n && n !== document.documentElement) {
    const v = parseFloat(getComputedStyle(n as HTMLElement).opacity || '1');
    if (!Number.isNaN(v)) o *= v;
    if (o < 0.02) return 0;
    n = n.parentElement;
  }
  return o;
};

/**
 * 元素的**墨迹矩形**：文字用 Range 取并集（真实字形），拿不到文本节点时退回 rect。
 * 块级容器整块宽不是字 —— 居中文字会被整块宽误判（`OverlapGate` 上踩过，这里同一处置）。
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
  useEffect(() => {
    const handle = delayRender(`CanvasBoundsGate @${raw}`, {timeoutInMilliseconds: 60000});
    let released = false;
    let cancelled = false;
    // 2026-09-21 实测过的坑（`ClippingGate` 与 `OverlapGate` 各踩过一次）：
    // `cancelRender()` 的实现是 **`throw error`**，而判定整个包在 `try { … } catch (e) { warn }` 里；
    // 抛出的异常一旦被自家 catch 吞掉、又走到 release()，handle 就归零 → `remotion_renderReady = true`
    // → 渲染器判 "ready"（优先于 "cancelled"）→ **报了硬拦却照样出图 rc=0**。
    // 处置：① 判定作出即置 `blocked`，此后 release() 一律空转（handle 永不释放）；
    //       ② blocked 之后异常原样抛出，绝不再被自家 catch 吞掉。
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
        const vw = window.innerWidth;   // Remotion 渲染时视口就是 composition 尺寸
        const vh = window.innerHeight;
        const issues: BoundsIssue[] = [];
        let scanned = 0;
        document.querySelectorAll<Element>(TEXT_SEL).forEach((el) => {
          if (el.closest('[data-gate-skip]') || el.closest('[data-gate-allow]')) return;
          if (!(el.textContent || '').trim()) return;    // 只看**含文字**的（装饰块/底托天然出局）
          if (el.children.length) return;                // 只看**叶元素**（容器整块宽不是墨迹）
          const cs = getComputedStyle(el as HTMLElement);
          if (cs.visibility === 'hidden' || cs.display === 'none') return;
          if (el.getClientRects().length === 0) return;  // 不参与布局（隐藏 / 未挂载）
          const op = effectiveOpacity(el);
          if (op < 0.05) return;                        // 还没出现 / 已经走了
          let box = inkBoxOf(el);
          if ((box.right - box.left) * (box.bottom - box.top) < 4) return; // 无实体的占位节点
          // 扣掉**会裁切的祖先**：取景框（`ZoomStage` 视口、接触表里 scale 过的格子）是有意裁切，
          // 被它裁住的部分不算越界。铺满整个视口的祖先不算裁切 —— 与它求交是恒等操作，
          // 却会把"越出画布"这件事一起抹掉（v1 实渲栽在这一条）。
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
          scanned++;
          const over = Math.max(-box.left, box.right - vw, -box.top, box.bottom - vh);
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
            // 硬拦：blocked 置位后 handle 永不释放；cancelRender 抛出的异常由下面的 catch 原样放行
            // （`if (blocked) throw e`）→ rc≠0 中止、不产出任何图。
            blocked = true;
            cancelRender(new Error(msg));
            return;
          }
        } else if ((debug || raw % REPORT_EVERY === 0) && typeof console !== 'undefined') {
          // 覆盖率：让「没报」与「没跑」可区分（旧门禁零输出两种含义混在一起）
          console.warn(`[CanvasBoundsGate] @${raw} 扫过 ${scanned} 个文字叶，无越界`);
        }
      } catch (e) {
        if (blocked) throw e;
        if (typeof console !== 'undefined') console.warn('[CanvasBoundsGate]', e);
      }
      release();
    };
    const id = requestAnimationFrame(() => {
      if (document.fonts && document.fonts.status !== 'loaded') {
        // 等字体就绪再量（不能直接 return —— 另外两道门禁都因此每帧跳过，等于不存在）
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
  }, [raw, mode, debug]);

  return null;
};

export const CANVAS_BOUNDS_GATE_VERSION =
  'canvas-bounds-gate-v2 · 只判**含文字的叶元素**（HTML 叶 + SVG text/tspan）的墨迹 rect 越出视口（= composition 尺寸），扣掉会裁切的祖先 · 输出像素口径，不做设计坐标回折 / 不判图形与版面件（与 ClippingGate 的重叠面因此消失）· delayRender 逐帧持柄 · 等字体就绪 · 每 150 帧覆盖率 · 落定态才硬拦 · 硬拦时 handle 不释放且异常不被自家 catch 吞';
