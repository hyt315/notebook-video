import React from 'react';
import {getInputProps, HtmlInCanvas, interpolate, Easing} from 'remotion';
import {pageTurn} from '@remotion/effects/page-turn';

// ============================================================================
// fx.tsx · 真翻页 / 揭纸转场（@remotion/effects 的 pageTurn，WebGPU）
//
// 为什么单独一层：pageTurn 要 WebGPU + HTML-in-canvas。Remotion 缺省的 Chrome Headless Shell
// 没有 WebGPU 适配器（实测 157.0.8080.0 / linux-arm64：`No WebGPU adapter available`），
// 只有完整版 Chrome（Chrome for Testing ≥ 149，--headless=new）配上软件 Vulkan（SwiftShader）
// 才画得出来。所以这层**默认关**：只有渲染器先用探针画过一张、核对过像素，才通过 inputProps
// `{nvFx: 'on'}` 打开（scripts/notebook-video.mjs 的 resolveFx）。没打开时 pageturn / peel
// 自动退回旧转场（FX_FALLBACK），绝不会因为浏览器不支持而整片渲染失败。
//
// 纪律：几何参数全是帧的纯函数（interpolate + 固定缓动）；pageTurn 本身无随机 → 同一帧渲两次结果相同。
// ============================================================================

export type CurlKind = 'pageturn' | 'peel';

/** 渲染器探针通过后才为 true（`--props '{"nvFx":"on"}'`）。Studio / 普通 still 缺省 false → 退回旧转场。 */
export const FX_ENABLED: boolean = (() => {
  try { return (getInputProps() as {nvFx?: string})?.nvFx === 'on'; } catch { return false; }
})();

/** 不支持 WebGPU 时的退回转场：翻页 → 纸面横移（slide），揭纸 → 新纸落下（drop）。 */
export const FX_FALLBACK: Record<CurlKind, 'slide' | 'drop'> = {pageturn: 'slide', peel: 'drop'};

/** 翻页比普通转场慢一点：14 帧（0.47 s）翻一页看起来像被风吹走；22 帧（0.73 s）是手翻的速度。 */
export const CURL_FRAMES = 22;

export const isCurl = (k: string | null | undefined): k is CurlKind => k === 'pageturn' || k === 'peel';

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const ease = Easing.bezier(0.3, 0, 0.3, 1); // 起手稍慢（掀起页角）、中段匀速、落定柔（实测 0.42/0.22 时中段 8 帧就翻完，看不清卷曲）

/**
 * 卷页几何（设计坐标 1920×1080 下的比例值；foldRadius 按设计像素给，渲染时乘像素密度）。
 *   pageturn：近乎竖直的折线（-78°，下角领先），从右缘外扫到左缘外 —— 手账 / 档案册翻到下一页；
 *   peel    ：对角折线（315°），从右下角外扫到左上角外 —— 剪纸从底板上揭起来。
 * 起止都留出「折线倾斜 + 卷曲半径」的余量：p=0 时整页平铺，p=1 时整页离开画面。
 */
export const curlParams = (kind: CurlKind, p: number) => {
  const e = ease(Math.max(0, Math.min(1, p)));
  if (kind === 'peel') {
    const t = interpolate(e, [0, 1], [1.24, -0.18], clamp);
    return {foldPosition: [t, t] as [number, number], foldDirection: 315, foldRadius: 110, lightDirection: -45, backPageOpacity: 0.12};
  }
  return {foldPosition: [interpolate(e, [0, 1], [1.1, -0.16], clamp), 0.5] as [number, number], foldDirection: -78, foldRadius: 150, lightDirection: -40, backPageOpacity: 0.16};
};

/**
 * 卷起来的那一页：children = 上一镜的整页（背景 + 内容），盖在新一页之上，随 p 卷走。
 * pixelDensity 必须等于设计坐标 → 输出像素的倍数（2560/1920 = 4/3），否则卷页按 1920 宽画、放大后发糊。
 */
export const PageCurl: React.FC<{kind: CurlKind; p: number; paper: string; density: number; children: React.ReactNode}> = ({kind, p, paper, density, children}) => {
  const c = curlParams(kind, p);
  return (
    <HtmlInCanvas width={1920} height={1080} pixelDensity={density}
      effects={[pageTurn({foldPosition: c.foldPosition, foldDirection: c.foldDirection, foldRadius: c.foldRadius * density, lightDirection: c.lightDirection, backPageOpacity: c.backPageOpacity, paperColor: paper})]}>
      <div style={{position: 'absolute', inset: 0, overflow: 'hidden'}}>{children}</div>
    </HtmlInCanvas>
  );
};

/** 新一页上、卷曲边缘前方的一道软阴影（pageTurn 不往下层投影；没有它，新页像贴在卷页后面的平面）。 */
export const curlShadow = (kind: CurlKind, p: number): React.CSSProperties | null => {
  if (p <= 0 || p >= 1) return null;
  const c = curlParams(kind, p);
  const a = (0.22 * Math.sin(Math.PI * Math.min(1, p))).toFixed(3);
  if (kind === 'peel') {
    const pos = (c.foldPosition[0] * 100).toFixed(2);
    return {background: `linear-gradient(135deg, transparent calc(${pos}% - 2%), rgba(40,25,10,${a}) ${pos}%, transparent calc(${pos}% + 9%))`};
  }
  const x = (c.foldPosition[0] * 100).toFixed(2);
  return {background: `linear-gradient(${90 - 12}deg, transparent calc(${x}% - 1%), rgba(40,25,10,${a}) calc(${x}% + 0.5%), transparent calc(${x}% + 7%))`};
};

/**
 * 渲染器的探针：320×180，红页卷走一半露出蓝页。notebook-video.mjs 渲一帧、读像素：
 * 左侧必须仍是红页（卷页画出来了）、右侧必须是蓝页（卷走的部分透明）——两者都对才开 fx。
 */
export const FxProbe: React.FC = () => (
  <div style={{position: 'absolute', inset: 0, background: '#0000ff'}}>
    <HtmlInCanvas width={320} height={180}
      effects={[pageTurn({foldPosition: [0.55, 0.5], foldDirection: -90, foldRadius: 12, backPageOpacity: 0, paperColor: '#00ff00'})]}>
      <div style={{position: 'absolute', inset: 0, background: '#ff0000'}} />
    </HtmlInCanvas>
  </div>
);
