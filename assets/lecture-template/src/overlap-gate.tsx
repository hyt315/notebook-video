import React, {useEffect, useMemo} from 'react';
import {cancelRender, useCurrentFrame} from 'remotion';

// ============================================================================
// OverlapGate · 渲染期重叠 / 遮挡门禁（v2.11 修复版）
//
// 为什么需要它：这一版反复出现的缺陷（标题压列表、状态标签压站点编号、轨道圆点压进度环的
// 95%、印章压结论尾部、四张卡塌到同一点…）本质是**同一类**问题，靠"逐帧看图 + 手改坐标"
// 永远抓不全。CardFitGate 只管"文字是否溢出自己的卡片"，管不了"元素之间互相压"。
//
// 本门禁做两件事（都在真实浏览器里量真实渲染结果）：
//   1. **文字两两重叠**：取每个含文字的叶元素**画出来的**矩形（Range + getClientRects，
//      天然包含 transform 效果），两两求交；交叠面积超阈值即报告。
//   2. **文字被遮挡**：在每个文字块内取几个采样点调用 document.elementsFromPoint，
//      返回的是**绘制顺序**（自顶向下）。若文字之上还有"不透明、且不是它的祖先、
//      也没标 data-gate-allow"的元素，判定为被遮挡。
//
// v2.11 修掉四处"看不见"（都是实测出来的，不是推测）：
//   a. **抽样窗口**：只每 15 帧量一次，而本技能最密集的重叠都发生在短窗口里——
//      镜头交接 10 帧、页眉滑变 7–16 帧、数值滑动 14 帧。只按格子抽样必然漏掉它们。
//      现在改为：基础网格 15 帧 + **事件帧强制抽样**（镜头边界 ±2、节拍 ±2、相机关键帧 ±2，
//      由 index.tsx 通过 watch 传入）。
//   b. **渐变遮挡物看不见**：looksSolid 只看 backgroundColor，而本项目大量面板是
//      linear/radial-gradient（backgroundColor 解析为 transparent）→ 永远不算遮挡。现在把
//      backgroundImage !== 'none' 也算实心。
//   c. **顶部标题层被整体跳过**：SKIP_Z=140 把 z=140 的页眉连内容带祖先一起跳过，
//      页眉压正文这一类既不进成对检查、也不算遮挡。现在阈值提到 145（只跳过
//      章节卡 150 / 字幕 200 这两个锁定覆盖层），页眉 z=140 参与检查。
//   d. **多文本节点只按整块矩形量**：块级元素会被误判成"横跨整行"。现在只要有文本节点
//      就用 Range 取并集。
//
// 另外：每 5 秒打一次覆盖率。旧版"零输出"既可能是真干净、也可能是根本没跑——
// 这两件事必须能区分开，否则门禁等于没有。
//
// 用法：
//   <OverlapGate />                                  // 只警告（抽样调参时用）
//   <OverlapGate mode="block" />                     // 命中即 cancelRender（交付渲染用）
//   <OverlapGate watch={[100,101,102,...]} />        // 事件帧强制抽样
//   <OverlapGate ignore={['ClassName']} />           // 追加忽略的文本前缀
//
// 与 CardFitGate 的分工：CardFitGate 管"文字出卡片"，本门禁管"元素互相压"。
// ============================================================================

export type OverlapIssue = {kind: 'pair' | 'occluded'; frame: number; text: string; other: string; area: number};

const THRESH_PX2 = 16;      // 报告阈值（约 4x4）
const BLOCK_PX2 = 256;      // 阻断阈值（约 16x16）
const OPAQUE_MIN = 0.35;    // 低于此透明度视为有意蒙层
const SKIP_Z = 145;         // 该 z 以上的层（章节卡 150 / 字幕 200）跳过；页眉 140 参与检查
const SAMPLE_EVERY = 15;    // 基础抽样桶（帧）
const EVENT_PAD = 2;        // 事件帧前后各多测几帧
const REPORT_EVERY = 150;   // 覆盖率日志间隔（帧）

const isAncestor = (a: Element | null, b: Element | null) => {
  let n = b;
  while (n) {
    if (n === a) return true;
    n = n.parentElement;
  }
  return false;
};

/** 元素相对自身的不透明度乘积（0 = 完全透明 = 不构成遮挡）。 */
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

/** 是否"看起来是实心覆盖物"：有非透明背景、**或渐变背景**、或有边框。 */
const looksSolid = (el: Element) => {
  const s = getComputedStyle(el as HTMLElement);
  const bg = s.backgroundColor || '';
  const m = /rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/.exec(bg);
  const alpha = m ? (m[4] === undefined ? 1 : parseFloat(m[4])) : 0;
  const border = (parseFloat(s.borderTopWidth) || 0) > 0 ? 1 : 0;
  const gradient = s.backgroundImage && s.backgroundImage !== 'none' ? 1 : 0;
  return (alpha > OPAQUE_MIN || border > 0 || gradient > 0) * (parseFloat(s.opacity || '1') || 1) > 0.2;
};

export const OverlapGate: React.FC<{
  mode?: 'warn' | 'block';
  ignore?: string[];
  sampleEvery?: number;
  watch?: number[];
}> = ({mode = 'warn', ignore = [], sampleEvery = SAMPLE_EVERY, watch}) => {
  const raw = Math.round(useCurrentFrame());
  const watchKey = (watch || []).join(',');
  // 事件帧集合：镜头边界 / 节拍 / 相机关键帧，前后各扩 EVENT_PAD 帧
  const hot = useMemo(() => {
    const s = new Set<number>();
    (watch || []).forEach((x) => {
      for (let d = -EVENT_PAD; d <= EVENT_PAD; d++) s.add(Math.round(x) + d);
    });
    return s;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchKey]);
  const onGrid = raw % sampleEvery === 0;
  const should = onGrid || hot.has(raw);
  const ignoreKey = ignore.join('|');
  useEffect(() => {
    if (!should) return;
    const id = requestAnimationFrame(() => {
      try {
        if (document.fonts && document.fonts.status !== 'loaded') return; // 字体未就绪时量出来的宽度无意义
        const all = Array.from(document.querySelectorAll<HTMLElement>('div,span,p'));
        // 收集"文字叶元素"：有文字、没有子元素、不在跳过名单里、z<145、可见
        const texts: {el: HTMLElement; rect: DOMRect; text: string}[] = [];
        for (const el of all) {
          const rawText = el.textContent || '';
          if (!rawText.trim() || el.children.length > 0) continue;
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
          if (rect.width * rect.height < 4) continue;
          const text = rawText.trim().slice(0, 16);
          if (ignoreKey && ignore.some((ig) => text.startsWith(ig))) continue;
          texts.push({el, rect, text});
        }
        const issues: OverlapIssue[] = [];
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
            if (area >= THRESH_PX2) issues.push({kind: 'pair', frame: raw, text: a.text, other: b.text, area});
          }
        }
        // ---- 2) 文字被遮挡 ----
        for (const t of texts) {
          const pts: [number, number][] = [
            [t.rect.left + t.rect.width / 2, t.rect.top + t.rect.height / 2],
            [t.rect.left + t.rect.width * 0.25, t.rect.top + t.rect.height / 2],
            [t.rect.left + t.rect.width * 0.75, t.rect.top + t.rect.height / 2],
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
              // 锁定覆盖层（章节卡 150 / 字幕 200）按设计就压在场景之上，
              // 不能算遮挡——否则每片都会在片头被自己的章节卡拦下（实测踩到过）。
              // 锁定覆盖层：自身或其**祖先**带锁定 z（章节卡 150 / 字幕 200）都不算遮挡物。
              // 只看自身会漏——字幕的文字 span 自身 z 是 auto，于是字幕被当成"遮挡物"误报（实测）。
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
              issues.push({kind: 'occluded', frame: raw, text: t.text, other: (c.textContent || c.tagName).trim().slice(0, 16), area: 9999});
              break;
            }
          }
        }
        if (issues.length) {
          const head = issues.slice(0, 5).map((x) => (x.kind === 'pair' ? `“${x.text}”压“${x.other}”(${Math.round(x.area)}px²)` : `“${x.text}”被“${x.other}”遮挡`)).join(' | ');
          const worst = Math.max(...issues.map((x) => x.area));
          const severe = issues.some((x) => x.kind === 'occluded') || worst >= BLOCK_PX2;
          const msg = `[OverlapGate] @${raw} 共 ${issues.length} 处：${head}`;
          if (mode === 'block' && severe) cancelRender(new Error(msg));
          else if (typeof console !== 'undefined') console.warn(msg);
        } else if (raw % REPORT_EVERY === 0 && typeof console !== 'undefined') {
          // 覆盖率：让"没报"与"没跑"可区分（旧版零输出两种含义混在一起）
          console.warn(`[OverlapGate] @${raw} 已测 ${texts.length} 个文字块，无重叠`);
        }
      } catch (e) {
        if (typeof console !== 'undefined') console.warn('[OverlapGate]', e);
      }
    });
    return () => cancelAnimationFrame(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [raw, should, mode, ignoreKey, sampleEvery, hot]);
  return null;
};

export const OVERLAP_GATE_VERSION = 'overlap-gate-v3 · pairwise text overlap + paint-order occlusion · 15f grid + event frames · gradient-aware · locked overlays (incl. their subtrees) excluded as coverers';
