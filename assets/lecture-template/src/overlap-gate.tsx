import React from 'react';
import {useCurrentFrame} from 'remotion';
import {REPORT_EVERY, effectiveOpacity, useLayoutProbe, useSampledFrame} from './layout-probe';

// ============================================================================
// OverlapGate · 渲染期重叠 / 遮挡门禁
//
// 管「元素之间互相压」（标题压列表、标签压编号、印章压结论…）；CardFitGate 只管文字溢出自己的卡片。
//
// 本门禁做两件事（都在真实浏览器里量真实渲染结果）：
//   1. **文字两两重叠**：取每个含文字的叶元素**画出来的**矩形（Range + getClientRects，
//      天然包含 transform 效果），两两求交；交叠面积超阈值即报告。
//   2. **文字被遮挡**：在每个文字块内取几个采样点调用 document.elementsFromPoint，
//      返回的是**绘制顺序**（自顶向下）。若文字之上还有"不透明、且不是它的祖先、
//      也没标 data-gate-allow"的元素，判定为被遮挡。
//
// 口径：
//   a. **抽样**：基础网格 15 帧 + **事件帧强制抽样**（镜头边界 / 节拍 / 相机关键帧各 ±2，
//      由 index.tsx 通过 watch 传入）——最密集的重叠发生在镜头交接、页眉滑变这类 7–16 帧的短窗口里。
//   b. **渐变也算实心**：backgroundImage !== 'none' 视同不透明背景（大量面板是渐变底）。
//   c. **SKIP_Z = 145**：只跳过章节卡 150 / 字幕 200 两个锁定覆盖层，页眉 z=140 参与检查。
//   d. **多文本节点用 Range 取并集**，块级元素不按整块矩形量（否则误判成横跨整行）。
//   每 5 秒打一次覆盖率，让「没报」与「没跑」可区分。
//
// 用法：
//   <OverlapGate />                                  // 只警告（抽样调参时用）
//   <OverlapGate mode="block" />                     // 命中即 cancelRender（交付渲染用）
//   <OverlapGate watch={[100,101,102,...]} />        // 事件帧强制抽样
//   <OverlapGate ignore={['ClassName']} />           // 追加忽略的文本前缀
//
// 与 CardFitGate 的分工：CardFitGate 管"文字出卡片"，本门禁管"元素互相压"。
// ============================================================================

export type OverlapIssue = {kind: 'pair' | 'occluded'; frame: number; text: string; other: string; area: number;
  /** 参与双方是否都已落定（有效不透明度 ≥0.98）：只有落定的重叠才硬拦 */
  settled: boolean};

const THRESH_PX2 = 16;      // 报告阈值（约 4x4）
const BLOCK_PX2 = 256;      // 阻断阈值（约 16x16）
const OPAQUE_MIN = 0.35;    // 低于此透明度视为有意蒙层
const SKIP_Z = 145;         // 该 z 以上的层（章节卡 150 / 字幕 200）跳过；页眉 140 参与检查
const SAMPLE_EVERY = 15;    // 基础抽样桶（帧）
const EVENT_PAD = 2;        // 事件帧前后各多测几帧

// 非文字字符：不参与「文字互相压」判定。
//   ① KaTeX 插的零宽字（U+200B、U+2061…）——`trim()` 去不掉它们；
//   ② KaTeX 的私有区码位（U+E000–U+F8FF）——如 `≠` 是"等号 + 斜杠"故意叠画出来的。
// 公式里的真字照旧参与判定，覆盖损失只限复合符号内部。
// ⚠️ 这个字符类**必须带 `u` 标志**，补充平面私用区必须写成 `\u{…}`：不带 u 时
// `\uf0000-\uffffd` 会被拆成 `\uf000` `0` `-` `\uffff` `d`，等于把 U+0030–U+FFFF（全部汉字、数字、字母）
// 都当成不可见字符吞掉，门禁对文字结构性失明。下面的自检就是防这个。
const INVISIBLE_CHARS = /[\u200b-\u200f\u2060-\u2064\ufeff\u00ad\ue000-\uf8ff\u{f0000}-\u{ffffd}\u{100000}-\u{10fffd}]/gu;
const visibleText = (s: string) => s.replace(INVISIBLE_CHARS, '');
// 自检：普通汉字 / 字母 / 数字**绝不能被吞**。吞掉即说明字符类又写坏了（少了 u 标志、或转义写错），
// 那种情况下本门的文字收集会静默失真，宁可在渲染日志里大声报出来。
if (typeof console !== 'undefined' && visibleText('重A0') !== '重A0') {
  console.warn(
    '[OverlapGate] INVISIBLE_CHARS 自检失败：它吞掉了可见文字（重A0 → "' +
      visibleText('重A0') +
      '"）。本门的文字收集会失真，请检查正则的 u 标志与 \\u{…} 转义。'
  );
}

const isAncestor = (a: Element | null, b: Element | null) => {
  let n = b;
  while (n) {
    if (n === a) return true;
    n = n.parentElement;
  }
  return false;
};

/** 是否"看起来是实心覆盖物"：有非透明背景、**或渐变背景**、或有边框。 */
const looksSolid = (el: Element) => {
  const s = getComputedStyle(el as HTMLElement);
  const bg = s.backgroundColor || '';
  const m = /rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/.exec(bg);
  const alpha = m ? (m[4] === undefined ? 1 : parseFloat(m[4])) : 0;
  const border = (parseFloat(s.borderTopWidth) || 0) > 0 ? 1 : 0;
  const gradient = s.backgroundImage && s.backgroundImage !== 'none' ? 1 : 0;
  // 既要有实心/边框/渐变，自身不透明度也要过线。
  const op = parseFloat(s.opacity || '1') || 1;
  return op > 0.2 && (alpha > OPAQUE_MIN || border > 0 || gradient > 0);
};

export const OverlapGate: React.FC<{
  mode?: 'warn' | 'block';
  ignore?: string[];
  sampleEvery?: number;
  watch?: number[];
}> = ({mode = 'warn', ignore = [], sampleEvery = SAMPLE_EVERY, watch}) => {
  const raw = Math.round(useCurrentFrame());
  // 事件帧集合：镜头边界 / 节拍 / 相机关键帧，前后各扩 EVENT_PAD 帧
  const {hot, should} = useSampledFrame(raw, sampleEvery, watch, EVENT_PAD);
  const ignoreKey = ignore.join('|');
  // 骨架（逐帧持柄、等字体就绪再量、硬拦时 handle 不释放且异常不被自家 catch 吞）在 layout-probe.tsx。
  // 缺任一条都会静默失效：没有 delayRender 时截帧先于测量；字体未就绪直接 return 等于每帧都跳过；
  // cancelRender 的异常被自家 catch 吞掉再 release，会报了硬拦却照样出图 rc=0。
  useLayoutProbe({label: `OverlapGate @${raw}`, tag: '[OverlapGate]', active: should}, ({block}) => {
    // SVG 文字节点一并纳入（Chart 轴标、PathDraw 沿线标签、GeoView 地名都画在 <text>/<tspan> 里；
    // getBoundingClientRect / elementsFromPoint 对 SVG 同样有效）。
    const all = Array.from(document.querySelectorAll<HTMLElement>('div,span,p,text,tspan'));
    // 收集"文字叶元素"：有文字、没有子元素、不在跳过名单里、z<145、可见
    const texts: {el: HTMLElement; rect: DOMRect; text: string}[] = [];
    for (const el of all) {
      const rawText = el.textContent || '';
      if (!visibleText(rawText).trim() || el.children.length > 0) continue;
      if (el.closest('[data-gate-skip]')) continue;
      if (el.offsetParent === null && getComputedStyle(el).position !== 'fixed') continue;
      const s = getComputedStyle(el);
      if (s.visibility === 'hidden' || parseFloat(s.opacity || '1') < 0.08) continue;
      const z = parseInt(s.zIndex || '0', 10);
      if (!Number.isNaN(z) && z >= SKIP_Z) continue;
      let anc = el.parentElement;
      let skip = false;
      while (anc && anc !== document.body) {
        const az = parseInt(getComputedStyle(anc).zIndex || '0', 10);
        if (!Number.isNaN(az) && az >= SKIP_Z) { skip = true; break; }
        anc = anc.parentElement;
      }
      if (skip) continue;
      if (effectiveOpacity(el) < 0.2) continue;
      // 用 Range 量**真实字形**矩形（取并集）：块级元素的 rect 是整块宽度，
      // 居中文本会被误判成"横跨整行"，从而和旁边的元素误报重叠。
      let rect = el.getBoundingClientRect();
      const tns = Array.from(el.childNodes).filter((n) => n.nodeType === 3 && (n.nodeValue || '').trim());
      if (tns.length >= 1) {
        const rs = tns.flatMap((tn) => {
          const r = document.createRange();
          r.selectNodeContents(tn);
          return Array.from(r.getClientRects());
        });
        if (rs.length) {
          const x0 = Math.min(...rs.map((q) => q.left)), x1 = Math.max(...rs.map((q) => q.right));
          const y0 = Math.min(...rs.map((q) => q.top)), y1 = Math.max(...rs.map((q) => q.bottom));
          rect = new DOMRect(x0, y0, x1 - x0, y1 - y0);
        }
      }
      // 引擎推近时世界层顶部有羽化遮罩（src/cinema.tsx cinemaMask），y < maskCut 的部分看不见 → 只量可见部分
      const focusWorld = el.closest('[data-cinema-focus]') as HTMLElement | null;
      if (focusWorld) {
        const wr = focusWorld.getBoundingClientRect();
        const cut = wr.top + (parseFloat(focusWorld.getAttribute('data-cinema-focus') || '0') * wr.height) / 1080;
        if (rect.bottom <= cut) continue;
        if (rect.top < cut) rect = new DOMRect(rect.left, cut, rect.width, rect.bottom - cut);
      }
      if (rect.width * rect.height < 4) continue;
      const text = rawText.trim().slice(0, 16);
      if (ignoreKey && ignore.some((ig) => text.startsWith(ig))) continue;
      texts.push({el, rect, text});
    }
    const issues: OverlapIssue[] = [];
    // ---- 「落定」判据 ----
    // 入场一律带位移+缩放，入场途中元素的盒必然短暂互相咬住：那是运动，不是版面错误。
    // 所以**只有参与双方都已落定（有效不透明度 ≥ 0.98）的重叠才硬拦**，未落定的只进日志。
    const SETTLED_MIN = 0.98;
    const settled = (el: Element) => effectiveOpacity(el) >= SETTLED_MIN;
    // ---- 1) 文字两两重叠 ----
    for (let i = 0; i < texts.length; i++) {
      for (let j = i + 1; j < texts.length; j++) {
        const a = texts[i], b = texts[j];
        if (isAncestor(a.el, b.el) || isAncestor(b.el, a.el)) continue;
        // 有意覆盖层（镜头交接叠帧、头部滑变双层）不参与成对检查
        if (a.el.closest('[data-gate-allow]') || b.el.closest('[data-gate-allow]')) continue;
        const w = Math.min(a.rect.right, b.rect.right) - Math.max(a.rect.left, b.rect.left);
        const h = Math.min(a.rect.bottom, b.rect.bottom) - Math.max(a.rect.top, b.rect.top);
        if (w <= 0 || h <= 0) continue;
        const area = w * h;
        if (area >= THRESH_PX2)
          issues.push({
            kind: 'pair',
            frame: raw,
            text: a.text,
            other: b.text,
            area,
            settled: settled(a.el) && settled(b.el),
          });
      }
    }
    // ---- 2) 文字被遮挡 ----
    for (const t of texts) {
      // 采样点取 22% / 50% / 78% 三个高度层：只取垂直中线会漏掉「上缘被切」或「下缘被切」
      // （例如弹层标题条只压住正文下半截时，中线恰好在压线之上）。
      const pts: [number, number][] = [
        [t.rect.left + t.rect.width / 2, t.rect.top + t.rect.height * 0.22],
        [t.rect.left + t.rect.width / 2, t.rect.top + t.rect.height / 2],
        [t.rect.left + t.rect.width / 2, t.rect.top + t.rect.height * 0.78],
        [t.rect.left + t.rect.width * 0.22, t.rect.top + t.rect.height * 0.78],
        [t.rect.left + t.rect.width * 0.78, t.rect.top + t.rect.height * 0.78],
      ];
      for (const [px, py] of pts) {
        if (px < 0 || py < 0 || px > window.innerWidth || py > window.innerHeight) continue;
        const stack = document.elementsFromPoint(px, py);
        const idx = stack.indexOf(t.el);
        if (idx <= 0) continue; // 自己就是最上层 → 没被压
        const coverers = stack.slice(0, idx).filter((el) => {
          if (isAncestor(el, t.el) || isAncestor(t.el, el)) return false; // 祖先不算
          if (el === t.el) return false;
          if (el.closest('[data-gate-allow]')) return false;            // 有意覆盖
          if (el.closest('[data-gate-skip]')) return false;
          // 锁定覆盖层（章节卡 150 / 字幕 200）按设计压在场景之上，不算遮挡物。
          // 自身或其**祖先**带锁定 z 都算：字幕的文字 span 自身 z 是 auto，只看自身会误报。
          let zc = parseInt(getComputedStyle(el).zIndex || '0', 10);
          if (Number.isNaN(zc)) zc = 0;
          if (zc >= SKIP_Z) return false;
          let za = el.parentElement;
          while (za && za !== document.body) {
            const azc = parseInt(getComputedStyle(za).zIndex || '0', 10);
            if (!Number.isNaN(azc) && azc >= SKIP_Z) return false;
            za = za.parentElement;
          }
          if (!looksSolid(el)) return false;                             // 透明/蒙层不算
          return true;
        });
        if (coverers.length) {
          const c = coverers[0] as HTMLElement;
          issues.push({
            kind: 'occluded',
            frame: raw,
            text: t.text,
            other: (c.textContent || c.tagName).trim().slice(0, 16),
            area: 9999,
            // 遮挡物与被压文字都落定才算"真遮挡"；入场途中的滑动覆盖只报不拦
            settled: settled(t.el) && settled(c),
          });
          break;
        }
      }
    }
    if (issues.length) {
      const head = issues.slice(0, 5).map((x) => (x.kind === 'pair' ? `“${x.text}”压“${x.other}”(${Math.round(x.area)}px²)` : `“${x.text}”被“${x.other}”遮挡`)).join(' | ');
      const blocking = issues.filter((x) => x.settled && (x.kind === 'occluded' || x.area >= BLOCK_PX2));
      const severe = blocking.length > 0;
      const msg =
        `[OverlapGate] @${raw} 共 ${issues.length} 处（其中落定态 ${blocking.length} 处）：${head}` +
        (blocking.length ? ` ｜ 硬拦：${blocking.slice(0, 3).map((x) => (x.kind === 'pair' ? `“${x.text}”压“${x.other}”` : `“${x.text}”被“${x.other}”遮挡`)).join(' / ')}` : '');
      // block 模式下也**先出声再拦**：无论 warn / block 都打完整清单，一次中断就能定位全部问题。
      if (typeof console !== 'undefined') console.warn(msg);
      if (mode === 'block' && severe) {
        // 失败路径**不释放 handle**：handle 留在 `remotion_delayRenderHandles` 里 →
        // `remotion_renderReady` 保持 false → 渲染器取到 "cancelled" → 渲染 rc≠0 中止、不产出任何图。
        block(msg);
      }
    } else if (raw % REPORT_EVERY === 0 && typeof console !== 'undefined') {
      // 覆盖率：让"没报"与"没跑"可区分
      console.warn(`[OverlapGate] @${raw} 已测 ${texts.length} 个文字块，无重叠`);
    }
  }, [raw, should, mode, ignoreKey, sampleEvery, hot]);
  return null;
};

export const OVERLAP_GATE_VERSION = 'overlap-gate-v5 · 硬拦时 handle 不释放且异常不被自家 catch 吞（v4 报"硬拦"却照样出图 rc=0）+ INVISIBLE_CHARS 补 u 标志与 \\u{…} 补充平面转义（v4 的字符类吞掉 U+0030–U+FFFF，对全部汉字结构性失明）+ self-check + 逐帧 delayRender 持柄（v3 从未拦过任何一帧）+ SVG 文字分支（text/tspan）+ block 模式先出声再拦 · pairwise text overlap + paint-order occlusion · 15f grid + event frames · gradient-aware · locked overlays (incl. their subtrees) excluded as coverers';
