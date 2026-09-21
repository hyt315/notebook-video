import React, {useEffect, useMemo} from 'react';
import {cancelRender, continueRender, delayRender, useCurrentFrame} from 'remotion';

// ============================================================================
// ClippingGate · 渲染期「图形被裁」门禁（v1）
//
// 为什么需要它（2026-09-21，用户在成片 2:58 亲眼看出来的那一类）：
//   `CardFitGate` 只量 **div/span 里的文字**有没有溢出自己的卡片；
//   `OverlapGate` 只量 **文字与文字**互相压。
//   两者都不看**图形**。于是「SVG 图形越出容器被裁掉」这件事**两道门都管不着**：
//   实测 S19 的走廊把站点圆心算在 x=0，圆从 −52 跨到 +52，左半边被 `<svg>` 视口裁掉
//   （对勾路径从 −14 起笔也一起没了）—— 渲出来是一颗缺了半边的球，**零报错、零警告**，
//   只有人眼看出来。这一件门就是补这个洞。
//
// 判据：**图形元素的真实 rect 越出最近的「会裁切」祖先盒子** 即报。
//   · 会裁切祖先（HTML 侧）= 第一个 overflow-x/y ≠ visible 的祖先；
//   · 会裁切祖先（SVG 侧）  = 所属 `<svg>` 的视口（浏览器对 `<svg viewBox>` 的 UA 默认就是
//     `overflow:hidden`）。显式写了 `overflow:visible` 的 svg（PathDraw / SketchFx 就是）
//     不裁切，继续往上找 —— 这一点必须按**计算样式**判，不能假设。
//
// 与 OverlapGate 同一条纪律：
//   · 测量排在 rAF 里 → **必须持 delayRender**，否则截帧先于测量，门禁等于不存在（那边踩过）；
//   · 字体未就绪时 `document.fonts.ready` **要等**，不能 return（那边也踩过）；
//   · 只有**落定**（元素与裁切祖先的有效不透明度都 ≥0.98）的越界才硬拦，
//     入场途中被位移/缩放甩出一点的只报不拦 —— 那是运动，不是版面错误；
//   · 每 150 帧打一次覆盖率：让「没报」与「没跑」可区分。
//   · **硬拦时必须让 handle 保持未释放、并且不让自家 catch 吞掉 cancelRender 的异常**
//     —— 这条是 v2 补的，v1 命中硬拦照样出图 rc=0（见 measure() 里的长注释）。
//
// 刻意**排除**的东西：
//   · 文字（`text`/`tspan` 除外由它自己管）——文字溢出归 CardFitGate；
//   · 顶层全幅底/调色层（`<AbsoluteFill>` 这类 HTML 铺满层，不是图形，选择器根本不含 div）；
//   · 标了 `data-gate-allow` / `data-gate-skip` 的子树 —— 有意裁切（取景框、揭示遮罩）
//     必须在组件上**显式声明**，而不是靠门禁猜。
// ============================================================================

export type ClipIssue = {
  kind: 'clip';
  frame: number;
  text: string;
  other: string;
  overflow: number;
  settled: boolean;
};

/** 容差（output px）。设计像素 ×4/3 得到 output，这里 ≈3 设计像素，吸收描边与取整。 */
const TOL = 4;
/** 硬拦阈值（output px）：超过它才算「真的缺了一块」。≈48 设计像素，肉眼一眼可见。 */
const BLOCK_PX = 24;
const OPAQUE_FOR_SETTLED = 0.98;
const SAMPLE_EVERY = 15;
const EVENT_PAD = 2;
const REPORT_EVERY = 150;

/**
 * 只挑**会落在画面上的图形元素**。
 * 刻意**不含** `svg` / `g` 这类纯容器：它们自己不上色，而「容器盒子比画布宽」是常事
 * —— 实测 Corridor 的 `<svg width={1920}>` 放在 design x=140 的盒子里，盒子一直伸到 2060，
 * 越出 1920 画布 140px，但它**什么都不画**在那里，报它就是纯噪音。
 * 真正会被裁的是**画东西的那些元素**（圆、路径、线、文字…），它们各自的 rect 才是判据。
 * 也刻意不含 `div/span`：文字与版面归 CardFitGate，HTML 侧的取景框（ZoomStage 那种）
 * 是**有意**裁切，应该由作者标 `data-gate-allow` 声明，而不是让门禁去猜。
 */
const GRAPHIC_SEL =
  'canvas,video,circle,ellipse,rect,line,polyline,polygon,path,text,tspan,image,foreignObject';

const isSvg = (el: Element): el is SVGElement =>
  typeof SVGElement !== 'undefined' && el instanceof SVGElement;
const isSvgRoot = (el: Element): el is SVGSVGElement =>
  typeof SVGSVGElement !== 'undefined' && el instanceof SVGSVGElement;

/** 元素与其祖先的**有效**不透明度乘积（0 表示完全透明）。 */
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
 * 最近的「会裁切」祖先盒子。
 * SVG 子元素：先看所属 `<svg>` —— 它默认裁切；显式 `overflow:visible` 的会跳过继续往上找。
 * 再往上：HTML 里第一个 overflow ≠ visible 的祖先。
 */
const clipBoxOf = (el: Element): {box: DOMRect; who: Element} | null => {
  let n: Element | null = el.parentElement;
  while (n && n !== document.documentElement && n !== document.body) {
    if (isSvgRoot(n)) {
      const s = getComputedStyle(n);
      const clips = s.overflow !== 'visible' || s.overflowX !== 'visible' || s.overflowY !== 'visible';
      if (clips) {
        const r = n.getBoundingClientRect();
        if (r.width > 1 && r.height > 1) return {box: r, who: n};
      }
    } else if (!isSvg(n)) {
      const s = getComputedStyle(n);
      if (s.overflowX !== 'visible' || s.overflowY !== 'visible') {
        const r = n.getBoundingClientRect();
        if (r.width > 1 && r.height > 1) return {box: r, who: n};
      }
    }
    n = n.parentElement;
  }
  return null;
};

export const ClippingGate: React.FC<{
  mode?: 'warn' | 'block';
  sampleEvery?: number;
  watch?: number[];
  /** 追加的忽略前缀（按元素的可读名匹配） */
  ignore?: string[];
}> = ({mode = 'warn', sampleEvery = SAMPLE_EVERY, watch, ignore = []}) => {
  const raw = Math.round(useCurrentFrame());
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
  const ignoreKey = ignore.join('|');

  useEffect(() => {
    if (!should) return;
    const handle = delayRender(`ClippingGate @${raw}`);
    let released = false;
    let cancelled = false;
    // 2026-09-21 实测修掉**第二处静默失效**（第一处是缺 delayRender，见文件头）：
    // `cancelRender()` 的实现是 **`throw error`**（remotion/dist/cjs/cancel-render.js），
    // 而本门禁的判定整个包在 `try { … } catch (e) { console.warn(…) }` 里，于是：
    //   cancelRender 抛 → 被自己的 catch 吞掉 → 走到函数末尾的 release() → continueRender
    //   → `window.remotion_delayRenderHandles` 归零 → `window.remotion_renderReady = true`。
    // 渲染器取状态时 **"ready" 排在 "cancelled" 前面**
    // （@remotion/renderer/dist/seek-to-frame.js:46 是
    //   `remotion_renderReady === true ? 'ready' : remotion_cancelledError !== undefined ? 'cancelled' : false`），
    // 所以命中硬拦时渲染照样成功、PNG 照样写出来、退出码照样 0（独立核验的隔离实验
    // FX-Probe-CancelTryCatchRelease 复现了这条链；FX-Probe-CancelRaf 则不触发）。
    // 处置：① 判定一旦作出就置 `blocked`，此后 release() 一律空转 —— handle 永不释放；
    //       ② blocked 之后异常原样抛出，绝不再被本函数的 catch 吞掉。
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
        const issues: ClipIssue[] = [];
        let checked = 0;
        document.querySelectorAll<Element>(GRAPHIC_SEL).forEach((el) => {
          if (el.closest('[data-gate-skip]')) return;
          if (el.closest('[data-gate-allow]')) return;
          const clip = clipBoxOf(el);
          if (!clip) return; // 没有会裁切的祖先 → 不可能被裁
          const r = el.getBoundingClientRect();
          if (r.width * r.height < 4) return; // 无实体的占位节点
          const op = effectiveOpacity(el);
          if (op < 0.05) return; // 还没出现 / 已经走了
          const over = Math.max(
            clip.box.left - r.left,
            r.right - clip.box.right,
            clip.box.top - r.top,
            r.bottom - clip.box.bottom
          );
          if (over <= TOL) return;
          checked++;
          const name =
            el.tagName.toLowerCase() +
            (isSvg(el) && el.getAttribute('class') ? `.${el.getAttribute('class')}` : '') +
            (el.textContent && el.textContent.trim() ? `「${el.textContent.trim().slice(0, 10)}」` : '');
          const who =
            clip.who.tagName.toLowerCase() +
            (clip.who.getAttribute('style')?.includes('overflow')
              ? '[overflow]'
              : '') +
            (isSvgRoot(clip.who) ? '[svg 视口]' : '[overflow 祖先]');
          if (ignoreKey && ignore.some((ig) => name.startsWith(ig))) return;
          issues.push({
            kind: 'clip',
            frame: raw,
            text: name,
            other: who,
            overflow: Math.round(over),
            settled: op >= OPAQUE_FOR_SETTLED && effectiveOpacity(clip.who) >= OPAQUE_FOR_SETTLED,
          });
        });
        if (issues.length) {
          const head = issues
            .slice(0, 5)
            .map((x) => `${x.text} 超出 ${x.other} ${x.overflow}px`)
            .join(' | ');
          const blocking = issues.filter((x) => x.settled && x.overflow >= BLOCK_PX);
          const msg = `[ClippingGate] @${raw} 共 ${issues.length} 处图形被裁（落定态 ${blocking.length} 处）：${head}`;
          if (typeof console !== 'undefined') console.warn(msg);
          if (mode === 'block' && blocking.length) {
            // 硬拦：blocked 置位后 handle 不再释放；cancelRender 会抛，异常被下面的 catch
            // 原样放行（`if (blocked) throw e`），渲染以 rc≠0 中止、不产出任何图。
            blocked = true;
            cancelRender(new Error(msg));
            return;
          }
        } else if (raw % REPORT_EVERY === 0 && typeof console !== 'undefined') {
          console.warn(`[ClippingGate] @${raw} 图形要素扫过 ${document.querySelectorAll(GRAPHIC_SEL).length} 个，无被裁`);
        }
        void checked;
      } catch (e) {
        if (blocked) throw e;
        if (typeof console !== 'undefined') console.warn('[ClippingGate]', e);
      }
      release();
    };
    const id = requestAnimationFrame(() => {
      if (document.fonts && document.fonts.status !== 'loaded') {
        // 等字体就绪再量（不能直接 return —— OverlapGate 曾因此在出片路径上每帧都跳过）
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
  }, [raw, should, mode, ignoreKey, sampleEvery, hot]);

  return null;
};

export const CLIPPING_GATE_VERSION =
  'clipping-gate-v2 · 图形 rect 越出最近裁切祖先（SVG 看视口 / HTML 看 overflow）· delayRender 逐帧持柄 · 等字体就绪 · 落定态才硬拦 · 硬拦时 handle 不释放且异常不被自家 catch 吞（v1 会出图 rc=0）· data-gate-allow 声明有意裁切';
