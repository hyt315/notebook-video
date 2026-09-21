import React from 'react';
import {hierarchy, pack as d3pack, partition as d3partition, tree as d3tree, treemap as d3treemap} from 'd3-hierarchy';
import {geoGraticule, geoOrthographic, geoPath} from 'd3-geo';
import {sankey, sankeyLinkHorizontal} from 'd3-sankey';
import {arc as d3arc} from 'd3-shape';
import QRCode from 'qrcode';
import {continueRender, delayRender, interpolate} from 'remotion';
import {THEME} from '../theme/active';
import {TYPE} from '../kit';
import {prog} from './ui';
import {fitChineseTextOnNLines} from './fittext';

// ============================================================================
// data.tsx — 结构化数据 → 图形（四个库都只做计算，画与皮肤由本层负责）
//
//   TreeView    ← d3-hierarchy   目录树 / 组织图 / 矩形树图 / 圆形打包 / 旭日图
//   GeoView     ← d3-geo         地球 / 地图 / 经纬网
//   SankeyChart ← d3-sankey      流量图（转化、分流、去向）
//   QrCode      ← qrcode         二维码（纯计算、不联网）
//
// 契约（dependency-policy.md §7）：颜色只读 THEME；动画是 f(帧号) 的纯函数；
// 四个库都是纯计算或纯字符串渲染，结果确定，可复现。
//
// ⚠️ 实测踩到的坑（treemap/pack/partition 三者共存时必读）：
//   这三个布局都是**有状态地写回节点**的（x0/x1/y0/y1 或 x/y/r）。
//   共用同一个 hierarchy() 根时，后跑的布局会覆盖先跑的结果——
//   第一次渲出来 treemap 全是 20px 细条就是这个原因。**每个布局各拿一个根。**
// ============================================================================

const C = THEME.palette;
const RADIUS = THEME.aesthetic.paperRadius;
const TONE = [C.blue, C.orange, C.green, C.gold, C.red] as const;

// ---------------------------------------------------------------------------
// TreeView — 目录树 / 组织图 / 矩形树图 / 圆形打包 / 旭日图
// ---------------------------------------------------------------------------
export type TreeNode = {name: string; children?: TreeNode[]; value?: number};
export type TreeVariant = 'tree' | 'treemap' | 'pack' | 'sunburst';

const sumOf = (n: TreeNode): number => (n.children && n.children.length ? n.children.reduce((a, c) => a + sumOf(c), 0) : (n.value ?? 1));

/**
 * fitNodeLabel — 节点的中文标签「反推字号 + 可读性降级」。
 *
 * 这是老问题（中文字号）在新图种上的重演：treemap 的窄矩形、pack 的小圆、
 * sunburst 的窄扇区都塞不下字。判定口径（实测得出，见 diag 页③）：
 *   1. 字号由 fitChineseTextOnNLines 反推（保证每行不超可用宽）；
 *   2. **同时**要求「行数 ≤ maxLines」与「整块高度 ≤ 可用高」——
 *      只看宽度是不够的：实测 treemap 里一个 150×60 的格子被反推到 34px 两行，
 *      整块 68px 高，直接顶出格子（宽度合规、高度溢出）；
 *   3. 反推结果 < MIN_LABEL_FONT → **降级：不画字**（改走图例/引线），
 *      而不是硬塞一个 6px 的瞎字号——那等于没有标签。
 *
 * maxLines 默认 2：留 3 行时，一个竖长格子会被排成「一字一行」的竖排标签，
 * 读起来不像标签而像装饰条。
 */
export const MIN_LABEL_FONT = 13;

export const fitNodeLabel = (text: string, boxW: number, boxH: number, maxFont = 34, maxLines = 2, fontFamily = 'Kai') => {
  const box = Math.max(24, boxW);
  const h = Math.max(20, boxH);
  let size = 0;
  let lines: string[] = [text];
  for (let f = maxFont; f >= 8; f -= 1) {
    const r = fitChineseTextOnNLines({text, maxLines, maxBoxWidth: box, maxFontSize: f, fontFamily});
    if (r.fontSize <= f && r.lines.length * r.fontSize * 1.32 <= h) {
      size = r.fontSize;
      lines = r.lines;
      break;
    }
  }
  return {fontSize: size, lines, show: size >= MIN_LABEL_FONT, box};
};

/**
 * fitOneLine — **单行**节点名：先按反推字号放下，放不下就截断加省略号。
 *
 * 与 `fitNodeLabel` 的分工：那个用于"放不下就不画字、改走图例"的图种（treemap / pack /
 * sunburst 有图例兜底）；目录树的节点**不能没有名字**（一个空框等于一个谜语），
 * 所以降到下限字号还放不下时，截断成 `notebook-vi…` 这种写法。
 *
 * 实测动机（接触表 ⑬ 页 frame 375）：根节点 `notebook-video`（14 个半角字符）
 * 在 116px 的框里、按 16px 字号画出来宽出框沿两侧，而它当时**根本没过任何反推**。
 */
export const fitOneLine = (text: string, boxW: number, maxFont: number, fontFamily = 'Kai', maxLines = 1) => {
  const box = Math.max(20, boxW);
  const fits = (t: string, f: number) =>
    fitChineseTextOnNLines({text: t, maxLines, maxBoxWidth: box, maxFontSize: f, fontFamily}).fontSize >= f;
  if (fits(text, maxFont)) return {text, fontSize: maxFont};
  for (let f = maxFont - 1; f >= MIN_LABEL_FONT; f -= 1) {
    if (fits(text, f)) return {text, fontSize: f};
  }
  // 到下限字号仍放不下 → 逐字砍到放得下（二分，纯函数）
  let lo = 0;
  let hi = text.length;
  while (lo < hi) {
    const mid = Math.ceil((lo + hi) / 2);
    if (fits(`${text.slice(0, mid)}…`, MIN_LABEL_FONT)) lo = mid;
    else hi = mid - 1;
  }
  return {text: lo > 0 ? `${text.slice(0, lo)}…` : '…', fontSize: MIN_LABEL_FONT};
};

export const TreeView: React.FC<{
  f: number;
  data: TreeNode;
  startAt: number;
  width: number;
  height: number;
  /** tree（默认目录树）· treemap 矩形树图 · pack 圆形打包 · sunburst 旭日图 */
  variant?: TreeVariant;
  /** 每层节点出现的间隔帧数（按层级逐层展开） */
  step?: number;
  nodeW?: number;
  nodeH?: number;
  /** 降级标签要不要在右上角汇总列出（默认列，避免"没字也看不懂"） */
  legend?: boolean;
}> = ({f, data, startAt, width, height, variant = 'tree', step = 14, nodeW = 104, nodeH = 30, legend = true}) => {
  const toneAt = (depth: number, i = 0) => (depth === 0 ? C.ink : TONE[(depth + i) % TONE.length]);

  // ---------------- 目录树（默认形态） ----------------
  // ⚠️ 两处实测逼出来的修正（接触表 ⑬ 页 frame 375）：
  //   ① 原来用 `d3.tree().size([...])`：size() 会把布局**归一化**到给定宽度，
  //      而框宽是固定的像素——同一份数据量出来同层相邻节点中心只隔 95px，
  //      框宽 116px，于是每对兄弟都首尾相接（重叠 21px）。
  //      正解：改用 `nodeSize` 在「槽」单位里布局（1 槽 = 1 个兄弟位，不被归一化），
  //      渲染时把 1 槽换成 `slotW` 像素 → 相邻中心的距离恒 ≥ slotW ≥ 框宽 + 间距。
  //   ② 节点标签当时**完全没过反推**，`notebook-video` 这类长名直接宽出框沿。
  //      正解：标签走 `fitOneLine`（反推字号，放不下就截断加省略号）。
  // 空间不够时（叶子多）等比缩框**和**字，而不是让它们互相压。
  if (variant === 'tree') {
    const gapX = 22; // 兄弟框之间的**最小**水平间距
    const gapY = 26; // 层与层之间在最小高度之外追加的垂直间距
    const sep = (a: {parent?: unknown}, b: {parent?: unknown}) => (a.parent === b.parent ? 1 : 1.45);
    const laid = d3tree<TreeNode>().nodeSize([1, 1]).separation(sep)(hierarchy(data));
    const nodes = laid.descendants();
    const us = nodes.map((n) => n.x);
    const minU = Math.min(...us);
    const spanU = Math.max(1e-6, Math.max(...us) - minU);
    const maxDepth = Math.max(...nodes.map((n) => n.depth));
    // 同层入场错峰的**总窗口**（帧）：一层不管有多少节点，都在这个窗口内错开完。
    // 每个节点的间隔 = min(5, 窗口 / (该层节点数 − 1))，节点越多间隔越小。
    const SIBLING_SPREAD = 24;
    const levelCounts = new Map<number, number>();
    for (const n of nodes) levelCounts.set(n.depth, (levelCounts.get(n.depth) ?? 0) + 1);
    const widestLevel = Math.max(1, ...levelCounts.values());
    const siblingGap = Math.min(5, SIBLING_SPREAD / Math.max(1, widestLevel - 1));
    const availW = Math.max(80, width - 16);
    // 框宽上限由**两个约束联立**解出（不是拍脑袋）：
    //   内容宽 = spanU·slotW + boxW ≤ availW  与  slotW ≥ boxW + gapX
    //   ⇒ boxW ≤ (availW − gapX·spanU) / (spanU + 1)
    // 第一次写的时候漏了 "+ boxW" 这一项，实测左右两端各被裁掉 4px（ui 左沿 / references 右沿）。
    const boxW = Math.max(30, Math.round(Math.min(nodeW, (availW - gapX * spanU) / (spanU + 1))));
    const slotW = Math.min(boxW + gapX * 2, Math.max(boxW + gapX, (availW - boxW) / spanU));
    const xOf = (u: number) => (u - minU) * slotW + (width - (spanU * slotW + boxW)) / 2 + boxW / 2;
    // 竖向：浅树把高度铺开（好看），深树按可用高度收紧（不裁切）
    const dy = Math.max(nodeH + 20, Math.min(nodeH + 120, maxDepth > 0 ? (height - nodeH - 8) / maxDepth : nodeH + 120));
    const yOf = (d: number) => d * dy + nodeH / 2;
    const totalH = maxDepth * dy + nodeH;
    if (process.env.NODE_ENV !== 'production' && boxW < 70) {
      console.warn(
        `[TreeView.tree] 本层有 ${Math.round(spanU) + 1} 个并排位、可用宽 ${Math.round(availW)}px，节点框被压到 ${boxW}px（标签只能靠截断）。` +
          `放大 width、减少同层节点，或改用 variant="treemap"。`
      );
    }
    const nodeColor = (depth: number) => (depth === 0 ? C.ink : depth === 1 ? TONE[0] : TONE[1]);
    return (
      <svg width={width} height={height} viewBox={`0 0 ${width} ${Math.max(height, totalH + 8)}`}>
        {laid.links().map((l, i) => {
          const p = prog(f, startAt + l.target.depth * step, 16);
          const sx = xOf(l.source.x);
          const tx = xOf(l.target.x);
          const sy = yOf(l.source.depth) + nodeH / 2;
          const ty = yOf(l.target.depth) - nodeH / 2;
          const mx = (sx + tx) / 2;
          return (
            <path
              key={`l${i}`}
              d={`M${sx},${sy} C${mx},${sy} ${mx},${ty} ${tx},${ty}`}
              fill="none"
              stroke={C.line}
              strokeWidth={2.4}
              strokeDasharray={1000}
              strokeDashoffset={1000 * (1 - p)}
              opacity={p}
            />
          );
        })}
        {nodes.map((n, i) => {
          const siblingsAtDepth = nodes.filter((x) => x.depth === n.depth).indexOf(n);
          // 同层错峰**按总窗口封顶**：不管这一层有多少节点，错开都在 SIBLING_SPREAD 帧内走完。
          // 原来是「序号 × 5 帧」——10 个叶子的一层要 45 帧、加上层间隔与 18 帧淡入，
          // 最后一格要到第 ~91 帧才画完（实测），3 秒以内的镜头里等于"缺了一块"。
          const p = prog(f, startAt + n.depth * step + siblingsAtDepth * siblingGap, 18);
          const tone = nodeColor(n.depth);
          const x = xOf(n.x);
          const y = yOf(n.depth);
          const lab = fitOneLine(n.data.name, boxW - 16, n.depth === 0 ? 16 : 15, 'Space,Kai,monospace');
          return (
            <g key={`n${i}`} transform={`translate(${x},${y})`} opacity={p} style={{transform: `translate(${x}px, ${y}px) scale(${0.86 + 0.14 * p})`}}>
              <rect x={-boxW / 2} y={-nodeH / 2} width={boxW} height={nodeH} rx={7} fill={n.depth === 0 ? C.ink : C.paper} stroke={tone} strokeWidth={2.4} />
              <text textAnchor="middle" y={lab.fontSize * 0.35} fontFamily="Space,Kai,monospace" fontSize={lab.fontSize} fontWeight={700} fill={n.depth === 0 ? C.white : C.ink}>
                {lab.text}
              </text>
            </g>
          );
        })}
      </svg>
    );
  }

  // ---------------- 矩形树图：面积 = 数值 ----------------
  if (variant === 'treemap') {
    const root = d3treemap<TreeNode>().size([width, height]).paddingInner(7).paddingOuter(5)(hierarchy(data).sum(sumOf));
    const leaves = root.leaves();
    const hidden: string[] = [];
    return (
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{overflow: 'visible'}}>
        {leaves.map((n, i) => {
          const w = n.x1 - n.x0;
          const h = n.y1 - n.y0;
          const lab = fitNodeLabel(n.data.name, w - 16, h - 10);
          const p = prog(f, startAt + i * 5, 18);
          const tone = toneAt(n.depth, i);
          if (!lab.show) hidden.push(n.data.name);
          return (
            <g key={`t${i}`} opacity={p}>
              <rect x={n.x0} y={n.y0} width={w} height={h} rx={7} fill={`${tone}22`} stroke={tone} strokeWidth={2.6} />
              {lab.show
                ? lab.lines.map((ln, k) => (
                    <text
                      key={k}
                      x={n.x0 + w / 2}
                      y={n.y0 + h / 2 + lab.fontSize * 0.5 + (k - (lab.lines.length - 1) / 2) * lab.fontSize * 1.32}
                      textAnchor="middle"
                      fontFamily="Kai,sans-serif"
                      fontSize={lab.fontSize}
                      fontWeight={700}
                      fill={C.ink}
                    >
                      {ln}
                    </text>
                  ))
                : null}
            </g>
          );
        })}
        {legend && hidden.length ? <Legend items={hidden} width={width} /> : null}
      </svg>
    );
  }

  // ---------------- 圆形打包 / 气泡图 ----------------
  if (variant === 'pack') {
    const root = d3pack<TreeNode>().size([width, height]).padding(9)(hierarchy(data).sum(sumOf));
    const leaves = root.leaves();
    const hidden: string[] = [];
    return (
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{overflow: 'visible'}}>
        {root.descendants().map((n, i) => {
          const p = prog(f, startAt + (n.depth + 1) * step + i * 2, 18);
          const tone = toneAt(n.depth, i);
          return (
            <circle
              key={`c${i}`}
              cx={n.x}
              cy={n.y}
              r={Math.max(0, n.r * p)}
              fill={n.children ? 'none' : `${tone}22`}
              stroke={n.children ? C.line : tone}
              strokeWidth={n.children ? 1.6 : 2.6}
            />
          );
        })}
        {leaves.map((n, i) => {
          // 圆内可用盒：内接正方形边长 = r·√2，再按经验收到 1.25r（实测 1.3r 时 5 字标签仍溢出）
          const lab = fitNodeLabel(n.data.name, n.r * 1.25, n.r * 1.25, 30);
          if (!lab.show) hidden.push(n.data.name);
          const p = prog(f, startAt + (n.depth + 1) * step + i * 2, 18);
          return lab.show ? (
            <g key={`pl${i}`} opacity={p}>
              {lab.lines.map((ln, k) => (
                <text
                  key={k}
                  x={n.x}
                  y={n.y + lab.fontSize * 0.5 + (k - (lab.lines.length - 1) / 2) * lab.fontSize * 1.3}
                  textAnchor="middle"
                  fontFamily="Kai,sans-serif"
                  fontSize={lab.fontSize}
                  fontWeight={700}
                  fill={C.ink}
                >
                  {ln}
                </text>
              ))}
            </g>
          ) : null;
        })}
        {legend && hidden.length ? <Legend items={hidden} width={width} /> : null}
      </svg>
    );
  }

  // ---------------- 旭日图（partition + d3-shape 的 arc） ----------------
  const root = d3partition<TreeNode>()
    .size([2 * Math.PI, Math.min(width, height) / 2 - 34])
    .padding(0.012)(hierarchy(data).sum(sumOf));
  const cx = width / 2;
  const cy = height / 2;
  // ⚠️ d3.arc 的**默认访问器**读的是 {startAngle,endAngle,innerRadius,outerRadius}，
  // 不是 partition 节点上的 {x0,x1,y0,y1}。不设访问器直接传 partition 节点，
  // 返回的是 null（不是报错）——实测第一次渲出来旭日图的**环一个都没画**，只剩标签。
  const arcGen = d3arc<{x0: number; x1: number; y0: number; y1: number}>()
    .startAngle((v) => v.x0)
    .endAngle((v) => v.x1)
    .innerRadius((v) => v.y0)
    .outerRadius((v) => v.y1);
  const hidden: string[] = [];
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{overflow: 'visible'}}>
      <g transform={`translate(${cx},${cy})`}>
        {root.descendants().map((n, i) => {
          const p = prog(f, startAt + n.depth * step + (i % 7) * 3, 20);
          const tone = toneAt(n.depth, i);
          const a0 = n.x0;
          const a1 = n.x0 + (n.x1 - n.x0) * p;
          const d = arcGen({x0: a0, x1: a1, y0: n.y0, y1: n.y1});
          return (
            <path
              key={`s${i}`}
              d={d ?? ''}
              fill={n.depth === 0 ? C.ink : n.children ? `${tone}33` : `${tone}2e`}
              stroke={n.depth === 0 ? C.ink : tone}
              strokeWidth={2.2}
              opacity={p}
            />
          );
        })}
        {root.descendants().map((n, i) => {
          if (n.depth === 0) return null;
          const mid = (n.x0 + n.x1) / 2;
          const mr = (n.y0 + n.y1) / 2;
          // 扇区可用宽 = 弧长 × 0.86（留出两侧描边余量），可用高 = 环宽 × 0.8
          const availW = (n.x1 - n.x0) * mr * 0.86;
          const availH = (n.y1 - n.y0) * 0.8;
          // ⚠️ 实测（本页 frame 465）：**必须 maxLines=1**。扇区里的字是沿切线写成
          // **一整行**的（下面 <text> 直接渲染 n.data.name），而 fitNodeLabel 默认按
          // 2 行反推字号——两者不一致时，反推说"放得下"，实际单行超出弧长，
          // 「帧参数名 / 构图与活性」会横着压到隔壁扇区上。按单行反推后：
          // 放不下的（弧长 60px 只能给到 12px 字号）自动降级进图例。
          const lab = fitNodeLabel(n.data.name, availW, availH, 24, 1);
          if (!lab.show) hidden.push(n.data.name);
          const p = prog(f, startAt + n.depth * step + (i % 7) * 3, 20);
          // 标签沿**切线**方向排（不是沿半径）——环宽只有 ~55px，径向放不下几个字，
          // 而弧长有 100+px。并且下半圈的切线会倒过来写，必须翻 180°：
          // 实测第一版没翻，圆心下方的「依赖政策 / 介质路由」全是倒着的。
          const deg = (mid * 180) / Math.PI;
          const flip = deg > 90 && deg < 270;
          return lab.show ? (
            <text
              key={`st${i}`}
              transform={`rotate(${deg}) translate(0,${-mr}) rotate(${flip ? 180 : 0})`}
              textAnchor="middle"
              y={lab.fontSize * 0.35}
              fontFamily="Kai,sans-serif"
              fontSize={lab.fontSize}
              fontWeight={700}
              fill={C.ink}
              opacity={p}
            >
              {n.data.name}
            </text>
          ) : null;
        })}
      </g>
      {legend && hidden.length ? <Legend items={hidden} width={width} /> : null}
    </svg>
  );
};

/** 放不下字的格子 / 圆 / 扇区：在右上角列一行图例，别让观众对着空块猜。 */
const Legend: React.FC<{items: string[]; width: number}> = ({items, width}) => {
  // 条目过多时只列前 5 个（实测：8 条的一行会横穿出图框、压到隔壁格的字上——
  // 这行是 `textAnchor="end"` 靠右排的，越长越往左顶，而 SVG 是 overflow:visible）。
  const shown = items.slice(0, 5);
  const more = items.length - shown.length;
  return (
    <g transform={`translate(${width - 12},18)`}>
      <text textAnchor="end" fontFamily="Kai,sans-serif" fontSize={TYPE.microS} fontWeight={700} fill={C.muted}>
        {`过窄未标注：${shown.join(' · ')}${more > 0 ? ` …等 ${items.length} 项` : ''}`}
      </text>
    </g>
  );
};

// ---------------------------------------------------------------------------
// GeoView — 地球 / 地图（正交投影 + 经纬网）
// ---------------------------------------------------------------------------
export const GeoView: React.FC<{
  f: number;
  width: number;
  height: number;
  /** 自转速度（度/帧）；0 = 不转 */
  spin?: number;
  startAt?: number;
  /** 经纬网 / 赤道 / 外圈 */
  graticule?: boolean;
  tone?: string;
}> = ({f, width, height, spin = 0.35, startAt = 0, graticule = true, tone}) => {
  const a = tone ?? C.blue;
  const r = Math.min(width, height) / 2 - 12;
  const proj = geoOrthographic()
    .translate([width / 2, height / 2])
    .scale(r)
    .rotate([-100 - spin * Math.max(0, f - startAt), -22]);
  const path = geoPath(proj);
  const p = prog(f, startAt, 24);
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <circle cx={width / 2} cy={height / 2} r={r} fill={C.skyTint} stroke={C.ink} strokeWidth={3} opacity={p} />
      {graticule ? (
        <path d={path(geoGraticule()()) ?? ''} fill="none" stroke={C.blueLine} strokeWidth={1.2} opacity={p} />
      ) : null}
      <circle cx={width / 2} cy={height / 2} r={r} fill="none" stroke={a} strokeWidth={3.4} opacity={p} />
    </svg>
  );
};

// ---------------------------------------------------------------------------
// SankeyChart — 流量图
// ---------------------------------------------------------------------------
export type SankeyNodeIn = {name: string; tone?: string};
export type SankeyLinkIn = {source: number; target: number; value: number};

export const SankeyChart: React.FC<{
  f: number;
  nodes: SankeyNodeIn[];
  links: SankeyLinkIn[];
  startAt: number;
  width: number;
  height: number;
  nodeW?: number;
  /** 每条连线的生长时长 */
  growFrames?: number;
}> = ({f, nodes, links, startAt, width, height, nodeW = 20, growFrames = 22}) => {
  const gen = sankey<SankeyNodeIn & {tone?: string}, {}>()
    .nodeWidth(nodeW)
    .nodePadding(Math.max(14, height / 22))
    .extent([
      [2, 4],
      [width - 2, height - 4],
    ]);
  const laid = gen({
    nodes: nodes.map((n) => ({...n})),
    links: links.map((l) => ({...l})),
  } as never);
  const linkGen = sankeyLinkHorizontal();
  const toneOf = (n: SankeyNodeIn | undefined, i: number) => n?.tone ?? TONE[i % TONE.length];

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{overflow: 'visible'}}>
      {laid.links.map((l, i) => {
        const p = prog(f, startAt + 6 + i * 6, growFrames);
        const src = l.source as never as {tone?: string};
        const w = (l as never as {width: number}).width;
        return (
          <path
            key={`l${i}`}
            d={linkGen(l as never) ?? ''}
            fill="none"
            stroke={toneOf(src, i)}
            strokeWidth={Math.max(2, w * p)}
            opacity={0.42 * p}
          />
        );
      })}
      {laid.nodes.map((n, i) => {
        const p = prog(f, startAt, 18);
        const y0 = (n as never as {y0: number}).y0;
        const y1 = (n as never as {y1: number}).y1;
        const x0 = (n as never as {x0: number}).x0;
        const x1 = (n as never as {x1: number}).x1;
        const tone = toneOf(n as SankeyNodeIn, i);
        return (
          <g key={`n${i}`} opacity={p}>
            <rect x={x0} y={y0} width={nodeW} height={Math.max(6, (y1 - y0) * p)} fill={tone} stroke={C.ink} strokeWidth={2.2} />
            <text
              x={x1 + 10}
              y={(y0 + y1) / 2 + 6}
              fontFamily="Kai,sans-serif"
              fontSize={TYPE.microL}
              fontWeight={700}
              fill={C.ink}
            >
              {n.name}
            </text>
          </g>
        );
      })}
    </svg>
  );
};

// ---------------------------------------------------------------------------
// QrCode — 二维码
// ---------------------------------------------------------------------------
export const QrCode: React.FC<{
  text: string;
  size?: number;
  /** 前景色，默认墨色；背景用透明 */
  tone?: string;
  label?: string;
}> = ({text, size = 220, tone, label}) => {
  const [svg, setSvg] = React.useState('');
  const [handle] = React.useState(() => delayRender('generating QR code'));
  React.useEffect(() => {
    let live = true;
    QRCode.toString(text, {type: 'svg', margin: 1, color: {dark: tone ?? C.ink, light: '#0000'}})
      .then((s) => {
        if (live) {
          setSvg(s);
          continueRender(handle);
        }
      })
      .catch(() => live && continueRender(handle));
    return () => {
      live = false;
    };
  }, [text, tone, handle]);

  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 24}}>
      <div
        style={{width: size, height: size, flex: '0 0 auto'}}
        dangerouslySetInnerHTML={{__html: svg.replace(/<svg /, `<svg width="${size}" height="${size}" `)}}
      />
      {label ? (
        <div style={{fontFamily: 'Kai,sans-serif', fontSize: TYPE.bodyM, color: C.ink, lineHeight: 1.7, maxWidth: 340}}>{label}</div>
      ) : null}
    </div>
  );
};
