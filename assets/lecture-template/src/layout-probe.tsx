import {useEffect, useMemo} from 'react';
import {cancelRender, continueRender, delayRender} from 'remotion';

// ============================================================================
// LayoutProbe · 渲染期浏览器门禁共用的测量骨架
//
// OverlapGate / ClippingGate / FillGate / CanvasBoundsGate / MascotGate 都在出图路径上量 DOM，
// 骨架完全相同，判据各自留在自己的文件里。骨架要守住三件事：
//   1. 逐帧持柄：被抽样的帧先 delayRender，量完才 continueRender。Remotion 截帧不等
//      requestAnimationFrame，没有 handle 的测量永远晚于出图，门禁等于不存在。
//   2. 等字体就绪再量（不能直接跳过：出片路径上测量那一刻 fonts 常是 loading，跳过 = 每帧都跳过）。
//   3. 硬拦不被吞：cancelRender() 的实现是 throw。若它被测量函数外层的 catch 吞掉、随后又
//      continueRender，handle 归零会让 remotion_renderReady = true，而渲染器取状态时 "ready"
//      优先于 "cancelled"，结果是报了硬拦却照样出图 rc=0。所以 block() 先置 blocked，
//      此后 release() 一律空转（handle 永不释放），blocked 之后异常原样抛出。
// ============================================================================

/** 覆盖率日志间隔（帧）：门禁每隔这么多帧报一次「量过、无问题」，日志里没有它 = 没跑。 */
export const REPORT_EVERY = 150;

/** 测量回调收到的控制柄：block(msg) 硬拦（先由门禁自己 console.warn 出声，再调它）。 */
export type ProbeControl = {block: (msg: string) => never};

export type ProbeOptions = {
  /** delayRender 的标签（日志里能看到是哪道门哪一帧） */
  label: string;
  /** 自家 catch 里打日志用的前缀，如 '[OverlapGate]' */
  tag: string;
  /** 本帧是否量；false 时不开 handle */
  active?: boolean;
  /** delayRender 超时（毫秒）；不填用 Remotion 默认值 */
  timeoutInMilliseconds?: number;
  /** 是否等 document.fonts 就绪再量，默认 true */
  waitFonts?: boolean;
};

/**
 * 在出图路径上跑一次 DOM 测量。measure 正常返回即放行本帧；调 ctl.block(msg) 即硬拦。
 * deps 与 useEffect 的依赖数组同义。
 */
export const useLayoutProbe = (
  opts: ProbeOptions,
  measure: (ctl: ProbeControl) => void,
  deps: readonly unknown[],
) => {
  const {label, tag, active = true, timeoutInMilliseconds, waitFonts = true} = opts;
  useEffect(() => {
    if (!active) return;
    const handle =
      timeoutInMilliseconds === undefined
        ? delayRender(label)
        : delayRender(label, {timeoutInMilliseconds});
    let released = false;
    let cancelled = false;
    let blocked = false;
    const release = () => {
      if (released || blocked) return;
      released = true;
      continueRender(handle);
    };
    const ctl: ProbeControl = {
      block: (msg: string): never => {
        // 硬拦：blocked 置位后 handle 永不释放；cancelRender 抛出的异常由下面的 catch 原样放行
        blocked = true;
        cancelRender(new Error(msg));
        throw new Error(msg); // cancelRender 已经抛了；这一行只为类型上的 never
      },
    };
    const run = () => {
      if (cancelled) {
        release();
        return;
      }
      try {
        measure(ctl);
      } catch (e) {
        if (blocked) throw e;
        if (typeof console !== 'undefined') console.warn(tag, e);
      }
      release();
    };
    const id = requestAnimationFrame(() => {
      if (waitFonts && document.fonts && document.fonts.status !== 'loaded') {
        document.fonts.ready.then(() => { if (!cancelled) run(); }).catch(() => run());
        return;
      }
      run();
    });
    return () => {
      cancelled = true;
      cancelAnimationFrame(id);
      release();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, ...deps]);
};

/** 抽样：每 sampleEvery 帧量一次，另加 watch 事件帧前后各 pad 帧。 */
export const useSampledFrame = (raw: number, sampleEvery: number, watch: number[] | undefined, pad: number) => {
  const watchKey = (watch || []).join(',');
  const hot = useMemo(() => {
    const s = new Set<number>();
    (watch || []).forEach((x) => {
      for (let d = -pad; d <= pad; d++) s.add(Math.round(x) + d);
    });
    return s;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchKey, pad]);
  return {hot, should: raw % sampleEvery === 0 || hot.has(raw)};
};

/** 元素与其祖先的**有效**不透明度乘积（<0.02 一律当 0：还没出现 / 已经走了）。 */
export const effectiveOpacity = (el: Element) => {
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
