import React from 'react';
import {forceCenter, forceCollide, forceLink, forceManyBody, forceSimulation} from 'd3-force';
import {THEME} from '../theme/active';
import {TYPE} from '../kit';
import {prog} from './ui';
import {fitNodeLabel} from './data';

// ============================================================================
// network.tsx — 关系网络（d3-force）
//
// 替换掉什么：技能此前只有「树」（d3-hierarchy）与「流向」（d3-sankey），
// 要表达「谁连着谁」这种**没有层级、没有方向**的关系，只能硬套树——
// 而树会凭空造出一个不存在的上下级。力导向是这类内容的唯一正确布局。
//
// 确定性（本轮实测，见 diag-upgrade 页②）：
//   · d3-force 的 dist 里 `Math.random` **0 处**；它用固定种子的 LCG
//     （`s = (1664525·s + 1013904223) % 2^32`，种子 1）并把 random 传给各 force。
//   · 本组件另外做两件保险：**初值显式给定**（按序号摆一圈，不用库的默认螺旋）、
//     **迭代次数写死**（默认 300），并立刻 `.stop()` 掉 d3-force 内部的 d3-timer，
//     只允许我们用固定次数驱动。
//   · 实测：同一帧渲两次，PNG 的 SHA-256 完全一致。
//
// 布局归一化（也是实测逼出来的）：力导向的自然结果会溢出给定画框
// （第一次渲出来有节点被裁在框外）。所以算完之后按**节点包围盒**等比缩放并居中，
// 这一步同样是纯函数，可复算。
// ============================================================================

const C = THEME.palette;

export type NetworkNode = {id: string; label: string; tone?: string; r?: number};
export type NetworkLink = {source: string; target: string; value?: number};

type PNode = NetworkNode & {x: number; y: number; vx: number; vy: number};

/** 纯函数：给定同样的输入，返回同样的坐标（不读时间、不读随机）。 */
export const layoutNetwork = (
  nodes: NetworkNode[],
  links: NetworkLink[],
  opts: {width: number; height: number; iterations?: number; pad?: number; nodeR?: number}
) => {
  const {width, height, iterations = 300, pad = 46, nodeR = 52} = opts;
  const rOf = (n: NetworkNode) => n.r ?? nodeR;
  const ps: PNode[] = nodes.map((n, i) => {
    // 初值显式给定（按序号摆一圈）——不依赖库的默认初始位置
    const a = (i / Math.max(1, nodes.length)) * Math.PI * 2;
    return {...n, x: width / 2 + Math.cos(a) * Math.min(width, height) * 0.3, y: height / 2 + Math.sin(a) * Math.min(width, height) * 0.3, vx: 0, vy: 0};
  });
  const pl: {source: PNode; target: PNode; value?: number}[] = [];
  for (const l of links) {
    const s = ps.find((p) => p.id === l.source);
    const t = ps.find((p) => p.id === l.target);
    if (s && t) pl.push({source: s, target: t, value: l.value});
  }
  const sim = forceSimulation(ps as never)
    .force(
      'link',
      forceLink(pl as never)
        .id((d: never) => (d as unknown as PNode).id)
        .distance(Math.min(width, height) * 0.34)
        .strength(0.75)
    )
    .force('charge', forceManyBody().strength(-Math.min(width, height) * 2.6))
    .force('center', forceCenter(width / 2, height / 2).strength(0.16))
    .force('collide', forceCollide().radius((d: never) => (rOf(d as unknown as PNode) + 14) as never))
    .stop(); // 停掉内部 d3-timer：布局只由下面的固定迭代驱动
  for (let i = 0; i < iterations; i++) sim.tick();

  // ---- 归一化：等比缩放 + 居中，保证节点（含半径）全部落在画框内 ----
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  for (const n of ps) {
    const r = rOf(n);
    minX = Math.min(minX, n.x - r);
    maxX = Math.max(maxX, n.x + r);
    minY = Math.min(minY, n.y - r);
    maxY = Math.max(maxY, n.y + r);
  }
  const availW = Math.max(1, width - pad * 2);
  const availH = Math.max(1, height - pad * 2);
  const scale = Math.min(1, availW / Math.max(1, maxX - minX), availH / Math.max(1, maxY - minY));
  const w2 = (maxX - minX) * scale;
  const h2 = (maxY - minY) * scale;
  const offX = (width - w2) / 2;
  const offY = (height - h2) / 2;
  const at = (n: PNode) => ({x: offX + (n.x - minX) * scale, y: offY + (n.y - minY) * scale, r: rOf(n) * scale});
  return {nodes: ps.map((n) => ({n, ...at(n)})), links: pl.map((l) => ({...l}))};
};

/**
 * NetworkGraph — 力导向关系网。
 *
 * 用法：
 *   <NetworkGraph f={f} startAt={10} width={820} height={520}
 *     nodes={[{id:'cli',label:'命令行'},{id:'srv',label:'服务端'},…]}
 *     links={[{source:'cli',target:'srv'},…]} />
 */
export const NetworkGraph: React.FC<{
  f: number;
  nodes: NetworkNode[];
  links: NetworkLink[];
  startAt: number;
  width: number;
  height: number;
  /** 写死的迭代次数（确定性前提之一） */
  iterations?: number;
  /** 默认节点半径 */
  nodeR?: number;
  /** 是否画节点名（默认画；放不下时自动降级为只画圆点） */
  showLabels?: boolean;
  /** 拖尾：让布局"从散到聚"而不是直接落定 */
  settleFrames?: number;
}> = ({f, nodes, links, startAt, width, height, iterations = 300, nodeR = 52, showLabels = true, settleFrames = 0}) => {
  const {nodes: laid, links: laidLinks} = layoutNetwork(nodes, links, {width, height, iterations, nodeR});
  const pos = new Map(laid.map((p) => [p.n.id, p]));
  // ---- 入场错峰**按总窗口封顶**（与 TreeView 同一套公式）----
  // 原来是 `i * 5`：节点/连线一多，入场就线性拖长（20 个节点要 95 帧、100 个要 495 帧，
  // 3 秒以内的镜头里等于"还没画完就切走了"）。现在每个元素的间隔 =
  // min(5, 窗口 / (数量 − 1))：**≤6 个元素时与旧公式完全相同**（间隔仍是 5 帧），
  // 再多就在固定窗口内压缩，一批无论多少元素都在窗口内错开完。
  const LINK_WINDOW = 25;
  const NODE_WINDOW = 25;
  const linkGap = Math.min(5, LINK_WINDOW / Math.max(1, laidLinks.length - 1));
  const nodeGap = Math.min(5, NODE_WINDOW / Math.max(1, laid.length - 1));
  const settle = settleFrames > 0 ? prog(f, startAt, settleFrames) : 1;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{overflow: 'visible'}}>
      {laidLinks.map((l, i) => {
        const s = pos.get(l.source.id);
        const t = pos.get(l.target.id);
        if (!s || !t) return null;
        const p = prog(f, startAt + 4 + i * linkGap, 26);
        // 生长：从起点"长"到终点（终点坐标按进度插值，纯函数）
        const ex = s.x + (t.x - s.x) * p;
        const ey = s.y + (t.y - s.y) * p;
        return (
          <g key={`l${i}`}>
            <line x1={s.x} y1={s.y} x2={t.x} y2={t.y} stroke={C.line} strokeWidth={2.4} strokeDasharray="9 12" opacity={0.5 * p} />
            <line x1={s.x} y1={s.y} x2={ex} y2={ey} stroke={C.lineOrange} strokeWidth={4} opacity={p} />
          </g>
        );
      })}
      {laid.map((p, i) => {
        const q = prog(f, startAt + 10 + i * nodeGap, 24);
        const tone = p.n.tone ?? [C.blue, C.orange, C.green, C.gold, C.red][i % 5];
        // 标签先反推字号；字号掉到 MIN_LABEL_FONT 以下就只留圆点（图例里也有名字）。
        // ⚠️ 实测（接触表 frame 465）：**必须 maxLines=1**。默认的 2 行会把「服务端」
        // 拆成「服务 / 端」，一个孤字吊在下面怎么看都是坏的；按单行反推字号反而更大
        // （归一化后 r≈43 的圆给到 18.6px，一行 56px 宽，圆的弦长 87px 完全放得下）。
        const lab = fitNodeLabel(p.n.label, p.r * 1.3, p.r * 1.3, 30, 1);
        const r = p.r * (0.6 + 0.4 * q) * (settleFrames > 0 ? 1 : 1);
        return (
          <g key={p.n.id} opacity={q}>
            <circle
              cx={p.x}
              cy={p.y}
              r={r}
              fill={C.paper}
              stroke={tone}
              strokeWidth={4}
              style={{transform: settleFrames > 0 ? `scale(${0.92 + 0.08 * settle})` : undefined, transformOrigin: `${p.x}px ${p.y}px`}}
            />
            <circle cx={p.x} cy={p.y} r={r * 0.62} fill={`${tone}26`} stroke="none" />
            {showLabels && lab.show
              ? lab.lines.map((ln, k) => (
                  <text
                    key={k}
                    x={p.x}
                    y={p.y + lab.fontSize * 0.5 + (k - (lab.lines.length - 1) / 2) * lab.fontSize * 1.3}
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
      {showLabels
        ? laid
            .filter((p) => !fitNodeLabel(p.n.label, p.r * 1.3, p.r * 1.3, 30, 1).show)
            .map((p, i) => (
              <text key={`lg${i}`} x={12} y={20 + i * 22} fontFamily="Space,Kai,monospace" fontSize={TYPE.microS} fill={C.muted}>
                {`○ ${p.n.label}`}
              </text>
            ))
        : null}
    </svg>
  );
};
