import React, {useEffect, useMemo} from 'react';
import {cancelRender, continueRender, delayRender, useCurrentFrame} from 'remotion';

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

export type OverlapIssue = {kind: 'pair' | 'occluded'; frame: number; text: string; other: string; area: number;
  /** 参与双方是否都已落定（有效不透明度 ≥0.98）：只有落定的重叠才硬拦 */
  settled: boolean};

const THRESH_PX2 = 16;      // 报告阈值（约 4x4）
const BLOCK_PX2 = 256;      // 阻断阈值（约 16x16）
const OPAQUE_MIN = 0.35;    // 低于此透明度视为有意蒙层
const SKIP_Z = 145;         // 该 z 以上的层（章节卡 150 / 字幕 200）跳过；页眉 140 参与检查
const SAMPLE_EVERY = 15;    // 基础抽样桶（帧）
const EVENT_PAD = 2;        // 事件帧前后各多测几帧
const REPORT_EVERY = 150;   // 覆盖率日志间隔（帧）

// 非文字字符（2026-09-21，实测量出来的两轮）：
//   ① KaTeX 会插零宽字（U+200B 零宽空格、U+2061 函数应用符…）当排版占位，
//      而 `String.prototype.trim()` **不去掉它们**（它们不在 Unicode White_Space 里）。
//   ② KaTeX 还用**私有区码位**（U+E000–U+F8FF，如 U+E020 = "not" 斜杠）拼复合符号：
//      `≠` 就是"等号 + 一条斜杠"**故意叠着画**出来的。
// 这两类都不是"字"，却都会被当成含文字的叶元素。后果实测两次：
//   零宽字那次判成压住 `=` **6437px²**；私有区斜杠那次判成压住 `=` **6440px²**（且已落定，
//   直接硬拦）——两次都把整片渲染打断，而画面两次都是对的。
// 判据是"文字互相压"，字形级的私有区码位与不可见占位当然不算文字；
// 公式里的**真字**（P、记住、∣…）照旧参与判定，所以覆盖损失只限"复合符号内部"。
// ⚠️⚠️ 这个字符类**必须带 `u` 标志**，补充平面私用区必须写成 `\u{…}`。2026-09-21 独立核验实测：
// 原写法 `…\uf0000-\uffffd]/g`（无 u）会被正则引擎拆成 `\uf000` + `0` + `-` + `\uffff` + `d`，
// 于是字符类里凭空多出 **`U+0030`–`U+FFFF` 这一整段（65488 个码点）** ——
// 全部汉字、全部数字、除 `空格 ! " # $ % & ' ( ) * + , - . /` 以外的全部可打印 ASCII
// 都被替换成空串。后果不是"少判几个字"，而是**结构性失明**：
//   · `visibleText('重叠甲文字') === ''`、`visibleText('alpha') === ''`、`visibleText('12345') === ''`；
//   · 下面 texts 的收集条件是 `if (!visibleText(rawText).trim() …) continue`，
//     于是**任何整块是汉字的文字叶元素都进不了 texts**；
//   · 成片实测：87 条字幕文本 100% 被整条吞空；覆盖率日志里全片每帧只"已测 2 个文字块"
//     （最大值 13），而第 4200 帧画面上光 z<145 的汉字文字块就有 7 处以上。
// 修法就是补上 `u` 标志、把补充平面写成 `\u{…}`。为了不再悄悄复发，下面加了一次自检。
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
  // tsc TS2362：原来写成 `(布尔) * (数字) > 0.2` —— JS 能跑，但不是合法 TS 算术。
  // 语义等价改写：既要有实心/边框/渐变，自身不透明度也要过线。
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
    // ========================================================================
    // 2026-09-21 修（实测，本轮最重要的一条）：本门禁全文只有 `cancelRender`、
    // **一个 `delayRender` 都没有**，而测量排在 `requestAnimationFrame` 里。
    // Remotion 截帧**不会等 rAF 回调**，于是测量永远晚于出图 →
    // **门禁从装上那天起就没拦过任何一帧**（still 渲染里等于不存在；视频渲染同一路径同理）。
    // 这与 `CardFitGate` 当年是同一个病，只是那一个已经修过、这一个漏了。
    // 现在做法升级为**逐帧持柄**：每个被抽样的帧开一个 delayRender handle，测量结束才 continueRender。
    // Remotion 在 handle 清零前不截帧，门禁这才真的站在出图路径上。
    // （与 CardFitGate 的差别：它只守第一帧，这里每个抽样帧都守。）
    // ========================================================================
    const handle = delayRender(`OverlapGate @${raw}`);
    let released = false;
    const release = () => {
      if (released || blocked) return;
      released = true;
      continueRender(handle);
    };
    let cancelled = false;
    // 2026-09-21 实测修掉**第四处静默失效**（前三处：没有 delayRender / fonts 未就绪直接 return /
    // 采样点全落在竖直中线，见上）：`cancelRender()` 的实现是 **`throw error`**
    // （remotion/dist/cjs/cancel-render.js），而本门的判定整个包在
    // `try { … } catch (e) { console.warn(…) }` 里，于是：
    //   cancelRender 抛 → 被自己的 catch 吞掉 → 走到函数末尾的 release() → continueRender
    //   → `window.remotion_delayRenderHandles` 归零 → `window.remotion_renderReady = true`。
    // 渲染器取状态时 **"ready" 排在 "cancelled" 前面**
    // （@remotion/renderer/dist/seek-to-frame.js:46），于是硬拦命中时渲染照样成功、
    // PNG 照样写出来、退出码照样 0 —— 「报了硬拦却出图」。
    // 独立核验的隔离实验：FX-Probe-CancelRaf（rAF+cancel、不 catch 不 release）rc=1；
    // FX-Probe-CancelTryCatchRelease（逐字复刻本门结构）rc=0。差别就在这两行。
    // 处置：① 硬拦时置 `blocked`，此后 release() 一律空转 —— handle 永不释放；
    //       ② blocked 之后异常原样抛出，绝不再被本函数的 catch 吞掉。
    let blocked = false;
    const measure = () => {
      if (cancelled) { release(); return; }
      try {
        if (document.fonts && document.fonts.status !== 'loaded') {
          // ================================================================
          // 2026-09-21 修（本轮第二轮实测，**这才是"门禁从没拦过"的真正主因**）：
          // 原来这里是**直接 return**，理由是"字体未就绪时量出来的宽度无意义"。
          // 但在真实出片路径上，测量那一刻 `document.fonts.status` **一直是 'loading'**：
          // 补上 delayRender 之后重渲，日志里只有一行
          //   `"OverlapGate @4200" handle was cleared after 16ms`
          // —— 连每 150 帧一次的**覆盖率日志都没打出来**，说明每一帧都在这一行返回了。
          // 也就是说：即便补上了 delayRender，门禁依旧"每帧都跳过"，等于不存在。
          // （`CardFitGate` 的注释里记着同一个坑——"实测某帧 fonts=loading，整桶直接跳过"，
          //   它已经改成等 `document.fonts.ready` 了；`OverlapGate` 当时没跟上。）
          // 现在同样改为：**等字体就绪再量**，delayRender handle 一直持着，量完才放。
          // ================================================================
          document.fonts.ready.then(() => { if (!cancelled) measure(); }).catch(() => measure());
          return;
        }
        // SVG 分支（2026-09-21 修，实测）：选择器原来只有 `div,span,p`，
        // **整幅画在 <text>/<tspan> 里的字一个字都不看**——Chart 的轴标、PathDraw 的
        // 沿线标签、GeoView 的地名，这些元素互相压、被面板压，门禁是瞎的。
        // 现在把 SVG 文字节点一并纳入（getBoundingClientRect / elementsFromPoint 对 SVG 同样有效）。
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
          if (rect.width * rect.height < 4) continue;
          const text = rawText.trim().slice(0, 16);
          if (ignoreKey && ignore.some((ig) => text.startsWith(ig))) continue;
          texts.push({el, rect, text});
        }
        const issues: OverlapIssue[] = [];
        // ---- 「落定」判据（2026-09-21 实测补，第三条假阳性的正解）----
        // 本片的入场一律带位移+缩放（22 帧 easeOut 上浮 / 逐字波浪 / KaTeX 公式的缩放入场），
        // **入场途中元素的盒必然短暂互相咬住**：那是运动，不是版面错误。
        // 实测代价：JumpInText 的逐字波浪被判成"讲"压"得"1161px²；
        // KaTeX 的私有区字形在入场第 3 帧被判成压住 `=` 6315px² —— 两次都把整片渲染打断，
        // 而两次画面都是对的。
        // 判据改为：**只有参与双方都处在"落定"（有效不透明度 ≥ 0.98）的重叠才硬拦**，
        // 未落定的照旧进日志（报，不拦）。真正该拦的是"落定之后还压着"的版面错误
        // ——S14 那处遮挡正是落定态（弹层与手风琴都不透明度 1），所以这一改**不会放过它**。
        // （这也解释了为什么它必须先被修好才第一次响：没修 delayRender 之前它连"入场途中"都看不到。）
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
          // 2026-09-21 修（**第三条，也是"明明看得见却报无重叠"的真凶**）：
          // 原来三个采样点全落在文字框的**垂直中线**上（y 全是 height/2）。
          // 实测 S14 的那处遮挡是"弹层标题条把正文下半截切掉"——
          // 正文字形的墨迹在 685..703，标题条从 702 开始压；
          // 中线在 ~699，**正好落在压线之上**，三个点全判"没被压"，
          // 于是门禁报「已测 19 个文字块，无重叠」——画面上一眼能看见的遮挡，它看不见。
          // 现在补上 22% / 78% 两个高度层（各带左右两点）：**"上缘被切"和"下缘被切"都能命中**。
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
          // block 模式下也**先出声再拦**（2026-09-21 修）：旧版 block 只 cancelRender 不打印，
          // 一次整片渲染挂在某一帧，日志里只有一句"第几处"——想看全貌还得重渲一次。
          // 现在无论 warn / block 都打完整清单，一次中断就能定位全部问题。
          if (typeof console !== 'undefined') console.warn(msg);
          if (mode === 'block' && severe) {
            // 失败路径**不释放 handle**（blocked 置位后 release() 空转）：handle 留在
            // `remotion_delayRenderHandles` 里 → `remotion_renderReady` 保持 false →
            // 渲染器取到 "cancelled" → 渲染 rc≠0 中止、不产出任何图。
            // 异常由下面的 catch 原样放行（`if (blocked) throw e`），绝不吞。
            blocked = true;
            cancelRender(new Error(msg));
            return;
          }
        } else if (raw % REPORT_EVERY === 0 && typeof console !== 'undefined') {
          // 覆盖率：让"没报"与"没跑"可区分（旧版零输出两种含义混在一起）
          console.warn(`[OverlapGate] @${raw} 已测 ${texts.length} 个文字块，无重叠`);
        }
      } catch (e) {
        if (blocked) throw e;
        if (typeof console !== 'undefined') console.warn('[OverlapGate]', e);
      }
      release();
    };
    const id = requestAnimationFrame(measure);
    return () => {
      cancelled = true;
      cancelAnimationFrame(id);
      release();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [raw, should, mode, ignoreKey, sampleEvery, hot]);
  return null;
};

export const OVERLAP_GATE_VERSION = 'overlap-gate-v5 · 硬拦时 handle 不释放且异常不被自家 catch 吞（v4 报"硬拦"却照样出图 rc=0）+ INVISIBLE_CHARS 补 u 标志与 \\u{…} 补充平面转义（v4 的字符类吞掉 U+0030–U+FFFF，对全部汉字结构性失明）+ self-check + 逐帧 delayRender 持柄（v3 从未拦过任何一帧）+ SVG 文字分支（text/tspan）+ block 模式先出声再拦 · pairwise text overlap + paint-order occlusion · 15f grid + event frames · gradient-aware · locked overlays (incl. their subtrees) excluded as coverers';
