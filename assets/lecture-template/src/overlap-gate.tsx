import React, {useEffect} from 'react';
import {cancelRender, useCurrentFrame} from 'remotion';

// ============================================================================
// OverlapGate · 渲染期重叠 / 遮挡门禁（v2.10.2 新增）
//
// 为什么需要它：这一版反复出现的缺陷（标题压列表、状态标签压站点编号、轨道圆点压进度环的
// 95%、印章压结论尾部、四张卡塌到同一点…）本质是**同一类**问题，靠"逐帧看图 + 手改坐标"
// 永远抓不全。CardFitGate 只管"文字是否溢出自己的卡片"，管不了"元素之间互相压"。
//
// 本门禁做两件事（都在真实浏览器里量真实渲染结果，每 15 帧抽样一次，成本可忽略）：
//   1. **文字两两重叠**：取每个含文字的叶元素**画出来的**矩形（getBoundingClientRect，
//      天然包含 transform 效果），两两求交；交叠面积超阈值即报告。
//   2. **文字被遮挡**：在每个文字块内取几个采样点调用 document.elementsFromPoint，
//      返回的是**绘制顺序**（自顶向下）。若文字之上还有"不透明、且不是它的祖先、
//      也没标 data-gate-allow"的元素，判定为被遮挡。
//
// 判定口径刻意保守（宁可漏报也不误报，否则会拦住正常渲染）：
//   · 透明的覆盖物（opacity < 0.35）视为有意的蒙层，不算遮挡；
//   · 祖先元素不算遮挡（父容器本来就在上面）；
//   · 标了 `data-gate-allow` 的元素视为有意覆盖（印章压卡片这类）；
//   · 交叠 < 16px² 不算（亚像素/圆角误报）；
//   · z-index ≥ 140 的层（章节卡 150 / 字幕 200）跳过，它们本来就该压在最上面。
//
// 用法：
//   <OverlapGate />                    // 只警告（默认，先校准）
//   <OverlapGate mode="block" />       // 命中即 cancelRender，阻断渲染（校准后启用）
//   <OverlapGate ignore={['ClassName']} />  // 追加忽略的文本前缀
//
// 与 CardFitGate 的分工：CardFitGate 管"文字出卡片"，本门禁管"元素互相压"。
// ============================================================================

export type OverlapIssue = {kind: 'pair' | 'occluded'; frame: number; text: string; other: string; area: number};

const THRESH_PX2 = 16;      // 报告阈值（约 4x4）
const BLOCK_PX2 = 256;      // 阻断阈值（约 16x16）
const OPAQUE_MIN = 0.35;    // 低于此透明度视为有意蒙层
const SKIP_Z = 140;         // 该 z 以上的层（章节卡/字幕）跳过
const SAMPLE_EVERY = 15;    // 抽样桶（帧）

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

/** 是否"看起来是实心覆盖物"：有非透明背景或边框。 */
const looksSolid = (el: Element) => {
  const s = getComputedStyle(el as HTMLElement);
  const bg = s.backgroundColor || '';
  const m = /rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/.exec(bg);
  const alpha = m ? (m[4] === undefined ? 1 : parseFloat(m[4])) : 0;
  const border = (parseFloat(s.borderTopWidth) || 0) > 0 ? 1 : 0;
  return alpha * (parseFloat(s.opacity || '1')) > OPAQUE_MIN || border > 0;
};

export const OverlapGate: React.FC<{mode?: 'warn' | 'block'; ignore?: string[]; sampleEvery?: number}> = ({mode = 'warn', ignore = [], sampleEvery = SAMPLE_EVERY}) => {
  const f = Math.floor(useCurrentFrame() / sampleEvery) * sampleEvery;
  const ignoreKey = ignore.join('|');
  useEffect(() => {
    const id = requestAnimationFrame(() => {
      try {
        if (document.fonts && document.fonts.status !== 'loaded') return; // 字体未就绪时量出来的宽度无意义
        const all = Array.from(document.querySelectorAll<HTMLElement>('div,span,p'));
        // 收集"文字叶元素"：有文字、没有子元素、不在跳过名单里、z<140、可见
        const texts: {el: HTMLElement; rect: DOMRect; text: string}[] = [];
        for (const el of all) {
          const raw = el.textContent || '';
          if (!raw.trim() || el.children.length > 0) continue;
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
          // 用 Range 量**真实字形**矩形：块级元素的 rect 是整块宽度，
          // 居中文本会被误判成"横跨整行"，从而和旁边的元素误报重叠。
          let rect = el.getBoundingClientRect();
          const tn = Array.from(el.childNodes).filter((n) => n.nodeType === 3 && (n.nodeValue || '').trim());
          if (tn.length === 1) {
            const r = document.createRange();
            r.selectNodeContents(tn[0]);
            const rs = Array.from(r.getClientRects());
            if (rs.length) {
              const x0 = Math.min(...rs.map((q) => q.left)), x1 = Math.max(...rs.map((q) => q.right));
              const y0 = Math.min(...rs.map((q) => q.top)), y1 = Math.max(...rs.map((q) => q.bottom));
              rect = new DOMRect(x0, y0, x1 - x0, y1 - y0);
            }
          }
          if (rect.width * rect.height < 4) continue;
          const text = raw.trim().slice(0, 16);
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
            if (area >= THRESH_PX2) issues.push({kind: 'pair', frame: f, text: a.text, other: b.text, area});
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
              if (!looksSolid(el)) return false;                             // 透明/蒙层不算
              return true;
            });
            if (coverers.length) {
              const c = coverers[0] as HTMLElement;
              issues.push({kind: 'occluded', frame: f, text: t.text, other: (c.textContent || c.tagName).trim().slice(0, 16), area: 9999});
              break;
            }
          }
        }
        if (issues.length) {
          const head = issues.slice(0, 5).map((x) => (x.kind === 'pair' ? `“${x.text}”压“${x.other}”(${Math.round(x.area)}px²)` : `“${x.text}”被“${x.other}”遮挡`)).join(' | ');
          const worst = Math.max(...issues.map((x) => x.area));
          const severe = issues.some((x) => x.kind === 'occluded') || worst >= BLOCK_PX2;
          const msg = `[OverlapGate] @${f} 共 ${issues.length} 处：${head}`;
          if (mode === 'block' && severe) cancelRender(new Error(msg));
          else if (typeof console !== 'undefined') console.warn(msg);
        }
      } catch (e) {
        if (typeof console !== 'undefined') console.warn('[OverlapGate]', e);
      }
    });
    return () => cancelAnimationFrame(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [f, mode, ignoreKey, sampleEvery]);
  return null;
};

export const OVERLAP_GATE_VERSION = 'overlap-gate-v1 · pairwise text overlap + paint-order occlusion · sampled every 15f';
