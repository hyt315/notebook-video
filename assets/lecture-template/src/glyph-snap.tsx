// ============================================================================
// glyph-snap.tsx · 展开边按整字落（不把汉字切成半个）
//
// 问题：auto.tsx 的 enter() 用
// `clip-path: inset(... (1-p)*100% ...)` 做「左→右展开」，展开边是线性的，于是中间帧里
// 展开边经常落在一个字的中间——观众看到的是「被切开的字」，不是「写出来的字」。
//
// 做法（不改风格：仍是同一条左→右展开边，同样的起止帧，同样的落定态）：
//   · enter() 在展开中（0<p<1）给元素多带一个 CSS 自定义属性 `--nv-grow: p`（落定后不带，
//     落定态也不再有 clip-path）；
//   · 本组件每帧在 layout 阶段（DOM 已提交、截图之前）找出所有带 `--nv-grow` 的元素，
//     用 Range 量出元素里每个字的真实字框，把展开边往左退到「不落在任何字内部」的最近位置，
//     重写该元素的 clip-path。展开边只会后退、不会前进，所以永远不会提前露出没轮到的字。
//
// 纯度契约（同一帧的画面不能取决于之前渲过哪些帧）：
//   · 每一帧对**每个**展开中的元素都重算、重写，不读任何上一帧留下的值；
//   · 落定 / 未入场的元素不碰：它们的 clip-path 由 React 按 props 写（属性一变 React 就会覆盖）；
//   · 字体没就绪时先 delayRender 等字体，再量——否则 still 的第一帧会按回退字体量出错的字框。
//   「连续渲」与「单帧渲」必须逐像素一致。
// ============================================================================
import {useLayoutEffect} from 'react';
import {continueRender, delayRender, useCurrentFrame} from 'remotion';

export const GROW_VAR = '--nv-grow';
/** 展开时裁切框向盒外让出的余量（设计 px）：偏移影、柔影、描边都画在盒外，余量不够的那一截会在落定那一帧
 *  （clip-path 撤掉时）突然冒出来。展开边扫过「盒宽 + 余量」，最后一帧与落定态画面一致。 */
export const REVEAL_BLEED = 32;
/** 展开中的 clip-path：右边是展开边（距盒右缘 rightPx，可为负 = 伸到盒外），上下左向外让 REVEAL_BLEED。 */
export const revealClip = (right: string) =>
  `inset(calc(-6% - ${REVEAL_BLEED}px) ${right} calc(-6% - ${REVEAL_BLEED}px) calc(-2% - ${REVEAL_BLEED}px))`;
/** 退让容差（设计 px）：展开边离字框边缘不足 0.5px 的不算「切进字里」（亚像素取整）。 */
const EDGE_TOL = 0.5;

type Box = [number, number];

/** 元素内每个非空白字的水平字框（元素本地坐标，设计 px）。 */
const glyphBoxes = (el: HTMLElement, rectLeft: number, scale: number): Box[] => {
  const out: Box[] = [];
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  const range = document.createRange();
  for (let node = walker.nextNode() as Text | null; node; node = walker.nextNode() as Text | null) {
    const text = node.data;
    for (let i = 0; i < text.length;) {
      const cp = text.codePointAt(i) ?? 0;
      const len = cp > 0xffff ? 2 : 1;
      if (!/\s/.test(String.fromCodePoint(cp))) {
        range.setStart(node, i);
        range.setEnd(node, i + len);
        for (const r of Array.from(range.getClientRects())) {
          if (r.width <= 0 || r.height <= 0) continue;
          out.push([(r.left - rectLeft) / scale, (r.right - rectLeft) / scale]);
        }
      }
      i += len;
    }
  }
  range.detach?.();
  return out;
};

/** 把展开边 x 退到不落在任何字框内部的最近位置（不动点迭代：每次退到被切那个字的左缘）。 */
export const safeEdge = (x: number, boxes: Box[], tol = EDGE_TOL): number => {
  let e = x;
  for (let guard = 0; guard < 10000; guard++) {
    let moved = false;
    for (const [a, b] of boxes) {
      if (e > a + tol && e < b - tol) { e = a; moved = true; }
    }
    if (!moved) break;
  }
  return e;
};

const snapAll = () => {
  document.querySelectorAll<HTMLElement>('[style*="--nv-grow"]').forEach((el) => {
    const p = parseFloat(el.style.getPropertyValue(GROW_VAR));
    if (!(p > 0 && p < 1)) return;
    const w = el.offsetWidth;
    if (!w) return;
    const rect = el.getBoundingClientRect();
    const scale = rect.width / w || 1;
    // 展开边扫过「盒宽 + REVEAL_BLEED」，与 enter() 同一条线性轨迹
    const x = p * (w + REVEAL_BLEED);
    const e = safeEdge(x, glyphBoxes(el, rect.left, scale));
    // 与 enter() 同一形状（revealClip）：只有右边是展开边
    el.style.clipPath = revealClip(`${(w - e).toFixed(2)}px`);
  });
};

/** 挂在成片根上（FilmLayout），每帧一次。不渲染任何东西。 */
export const GlyphSnap = () => {
  const frame = useCurrentFrame();
  useLayoutEffect(() => {
    if (!document.querySelector('[style*="--nv-grow"]')) return;
    if (document.fonts.status === 'loaded') { snapAll(); return; }
    let live = true;
    const handle = delayRender('glyph-snap: waiting for fonts', {timeoutInMilliseconds: 60000});
    document.fonts.ready.then(() => { if (live) snapAll(); }).finally(() => continueRender(handle));
    return () => { live = false; };
  }, [frame]);
  return null;
};
