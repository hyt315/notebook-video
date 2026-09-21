import React from 'react';
import {scaleBand, scaleLinear} from 'd3-scale';
import {csvParse} from 'd3-dsv';
import {
  arc as d3arc,
  area as d3area,
  curveMonotoneX,
  line as d3line,
  lineRadial,
  pie as d3pie,
  stack as d3stack,
  stackOffsetExpand,
  stackOffsetNone,
  stackOffsetWiggle,
} from 'd3-shape';
import {THEME} from '../theme/active';
import {TYPE} from '../kit';
import {prog} from './ui';
import {fitChineseTextOnNLines, fitsWithin} from './fittext';

// ============================================================================
// chart.tsx — 图表（d3-scale / d3-shape 只负责计算，画还是我们画）
//
// 为什么用 d3 而不是图表组件库：d3-scale 只做「数据→刻度」、d3-shape 只做
// 「数据→路径」，两者都是纯数学——零渲染、零动画、零样式，与帧驱动天然相容。
// 而 recharts / nivo 这类自带时间驱动动画与样式体系，会和皮肤与可复现性打架。
//
// 变体（variant）说明：这些不是新组件，是同一件的参数——
//   line（默认）折线+柱 · area 面积 · stack 堆叠 · stackExpand 百分比堆叠
//   stream 河流图 · radar 雷达 · pie 饼图/环形
// 单序列用 data/csv；多序列用 series。**所有变体共用同一套内边距**，
// 所以 fitH() 的高度契约不因变体而变（见文件末的 BOX 常量）。
// ============================================================================

const C = THEME.palette;

/** 绘图区内边距——**所有变体共用**，高度契约因此稳定。 */
export const CHART_BOX = {padL: 96, padR: 48, padT: 40, padB: 78, titleH: 44} as const;

export type ChartDatum = {label: string; value: number};
export type ChartSeries = {name: string; values: number[]; tone?: string};
export const CHART_VARIANTS = ['line', 'area', 'stack', 'stackExpand', 'stream', 'radar', 'pie'] as const;

export type ChartVariant = 'line' | 'area' | 'stack' | 'stackExpand' | 'stream' | 'radar' | 'pie';

const TONE = [C.blue, C.orange, C.green, C.gold, C.red];

/**
 * csvToChartData — CSV 文本 → 图表数据（d3-dsv 只做解析，不做渲染）。
 * 约定两列：第一列是标签，第二列是数值。真实数据进图表的入口，
 * 不必再把数据手抄成数组。
 */
export const csvToChartData = (csv: string): ChartDatum[] =>
  csvParse(csv.trim())
    .map((row) => {
      const cells = Object.values(row);
      return {label: String(cells[0] ?? ''), value: Number(cells[1] ?? 0)};
    })
    .filter((d) => d.label !== '' && Number.isFinite(d.value));

/**
 * csvToChartSeries — CSV → 多序列（首列标签，其余每列一个序列）。
 * 堆叠 / 河流 / 雷达 / 饼图要的是这张形状，不必让作者手写矩阵。
 */
export const csvToChartSeries = (csv: string): {labels: string[]; series: ChartSeries[]} => {
  const rows = csvParse(csv.trim());
  if (rows.length === 0) return {labels: [], series: []};
  const cols = Object.keys(rows[0]);
  const labels = rows.map((r) => String(r[cols[0]] ?? ''));
  const series = cols.slice(1).map((col) => ({name: col, values: rows.map((r) => Number(r[col] ?? 0))}));
  return {labels, series};
};

const tickStyle = {fontFamily: 'Space,monospace', fontSize: TYPE.microS, fill: C.muted} as const;

/** 左侧 Y 轴 + 横向网格：折线/面积/堆叠/河流共用。 */
const YAxis: React.FC<{ticks: number[]; y: (v: number) => number; innerW: number; unit: string}> = ({ticks, y, innerW, unit}) => (
  <>
    {ticks.map((t, i) => (
      <g key={i}>
        <line x1={0} x2={innerW} y1={y(t)} y2={y(t)} stroke={C.line} strokeWidth={1.5} strokeDasharray="6 8" />
        <text x={-18} y={y(t) + 7} textAnchor="end" {...tickStyle}>
          {t}
          {unit}
        </text>
      </g>
    ))}
  </>
);

/** 坐标轴：Y 轴在 x=0、X 轴在 y=innerH（与折线变体完全一致的位置）。 */
const Axes: React.FC<{innerW: number; innerH: number; labels: string[]; at: (i: number) => number}> = ({innerW, innerH, labels, at}) => (
  <>
    <line x1={0} x2={innerW} y1={innerH} y2={innerH} stroke={C.ink} strokeWidth={3} />
    <line x1={0} x2={0} y1={0} y2={innerH} stroke={C.ink} strokeWidth={3} />
    {labels.map((l, i) => (
      <text key={l + i} x={at(i)} y={innerH + 46} textAnchor="middle" {...tickStyle}>
        {l}
      </text>
    ))}
  </>
);

export const Chart: React.FC<{
  f: number;
  /** 单序列：直接给数据数组，或者给 csv 文本（二选一，csv 优先） */
  data?: ChartDatum[];
  csv?: string;
  /** 多序列（stack / stackExpand / stream / radar / pie 用） */
  series?: ChartSeries[];
  /** 多序列时 X 轴的标签 */
  labels?: string[];
  variant?: ChartVariant;
  startAt: number;
  width: number;
  height: number;
  title: string;
  unit?: string;
  showBars?: boolean;
  tone?: string;
  /** 环形图的中心孔径（0 = 实心饼） */
  innerRadius?: number;
}> = ({
  f,
  data,
  csv,
  series,
  labels,
  variant = 'line',
  startAt,
  width,
  height,
  title,
  unit = '',
  showBars = true,
  tone,
  innerRadius = 0.52,
}) => {
  const accent = tone ?? C.blue;
  const rows = csv ? csvToChartData(csv) : (data ?? []);
  const {padL, padR, padT, padB, titleH} = CHART_BOX;
  const innerW = width - padL - padR;
  const innerH = height - padT - padB - titleH;
  const grow = prog(f, startAt, 46);
  const titleNode = title ? (
    <div style={{fontFamily: 'Kai,sans-serif', fontSize: TYPE.labelL, fontWeight: 700, color: C.ink, height: titleH}}>{title}</div>
  ) : null;
  const svgH = height - titleH;

  // ---- 多序列：d3-shape 的 stack（三种 offset）+ 雷达 + 饼 ----
  const multi = series && series.length > 0 ? series : null;
  const n = multi ? multi[0].values.length : rows.length;
  const axisLabels = labels ?? rows.map((d) => d.label);

  type StackPoint = {xIndex: number; y0: number; y1: number; series: ChartSeries; si: number};

  let stackPoints: StackPoint[] = [];
  let stackSvg: React.ReactNode = null;
  let maxStack = 1;

  // ⚠️ 变体名写错时**必须响亮地失败**，不许静默渲出一张空图。
  // 实测（overview-film 第 1 章 S2，f=420）：`variant="bar"` 不在闭合集里 →
  // `body` 落到 null → 画面上只剩标题、没有柱子，而十道门禁没有一道能拦（构图门禁只查 live 名字存在）。
  // 这种"没报错但坏了"正是本技能最怕的一类失败，所以在这里直接抛。
  if (!(CHART_VARIANTS as readonly string[]).includes(variant)) {
    throw new Error(
      `Chart: 未知 variant "${String(variant)}"。合法值：${CHART_VARIANTS.join(' / ')}` +
      `（"柱状"要用默认的 line 变体并靠 series 驱动，或改用 StatRow / MetricGrid）`);
  }
  if (multi && (variant === 'stack' || variant === 'stackExpand' || variant === 'stream')) {
    const offset = variant === 'stackExpand' ? stackOffsetExpand : variant === 'stream' ? stackOffsetWiggle : stackOffsetNone;
    // ⚠️ d3stack 的入参是「数据点数组」，每个点按 key 取值：points[i][si]。
    // 直接传 series 数组等于**转置错**——实测第一次渲出来三块面积只铺了 40% 宽、
    // 而且是三条近似水平的带（每列被当成了一个数据点）。这里显式转置。
    const wide = multi.map((s) => s.values);
    const points: number[][] = Array.from({length: n}, (_, i) => multi.map((s) => s.values[i] ?? 0));
    void wide;
    const st = d3stack<number>()
      .keys(multi.map((_, si) => String(si)))
      .offset(offset)(points as never);
    let maxStackRaw = 1;
    for (const layer of st) for (const p of layer) maxStackRaw = Math.max(maxStackRaw, p[1]);
    maxStack = maxStackRaw;
    const xb = scaleLinear()
      .domain([0, Math.max(1, n - 1)])
      .range([0, innerW]);
    const yStack = scaleLinear().domain([0, maxStack]).range([innerH, 0]);
    const yExpand = scaleLinear().domain([0, 1]).range([innerH, 0]);
    const yOf = (v: number) => (variant === 'stackExpand' ? yExpand(v) : yStack(v));
    for (let si = 0; si < st.length; si++) {
      const layer = st[si];
      // stream（河流图）把基线也做成起伏的，看起来才像流量而不是堆叠
      for (let i = 0; i < layer.length; i++) {
        const p = layer[i];
        const y0 = variant === 'stream' ? p[0] - (p[1] - p[0]) / 2 : p[0];
        stackPoints.push({xIndex: i, y0, y1: p[1], series: multi[si], si});
      }
    }
    const xAt = (i: number) => xb(i);

    stackSvg = (
      <g transform={`translate(${padL},${padT})`}>
        <YAxis ticks={variant === 'stackExpand' ? [0, 0.25, 0.5, 0.75, 1] : yStack.ticks(5)} y={(v) => yOf(v)} innerW={innerW} unit={variant === 'stackExpand' ? '' : unit} />
        {multi.map((s, si) => {
          const pts = stackPoints.filter((p) => p.si === si);
          const areaGen = d3area<StackPoint>()
            .x((p) => xAt(p.xIndex))
            .y0((p) => yOf(p.y0))
            .y1((p) => yOf(p.y1))
            .curve(curveMonotoneX);
          const q = prog(f, startAt + 6 + si * 7, 34);
          const toneS = s.tone ?? TONE[si % TONE.length];
          return <path key={s.name} d={areaGen(pts) ?? ''} fill={`${toneS}99`} stroke={toneS} strokeWidth={3} opacity={q} />;
        })}
        <Axes innerW={innerW} innerH={innerH} labels={axisLabels} at={xAt} />
        {variant === 'stream'
          ? null
          : multi.map((s, si) => (
              <g key={`lg${s.name}`} transform={`translate(${si * 250},${-26})`}>
                <rect width={22} height={22} rx={5} fill={s.tone ?? TONE[si % TONE.length]} stroke={C.ink} strokeWidth={2} />
                <text x={32} y={17} fontFamily="Kai,sans-serif" fontSize={TYPE.microL} fontWeight={700} fill={C.ink}>
                  {s.name}
                </text>
              </g>
            ))}
      </g>
    );
  }

  // ---- 雷达图：lineRadial + scaleLinear ----
  let radarSvg: React.ReactNode = null;
  // ⚠️ 第二层静默失败（同一帧渲出来的）：**多序列 + line/area 没有绘制路径**——
  // `body = multi ? (radar ? radarSvg : pie ? pieSvg : stackSvg) : singleSvg`，
  // 而 stackSvg 只在 stack/stackExpand/stream 下才被定义 → 这里会落到 undefined，
  // 画面上只剩标题、没有图。多序列想画"两条线"，要么用 stack 系列变体，
  // 要么拆成两张单序列 Chart（本片第 1 章 S2 就是拆开画的）。
  // 实测口径：`series`（**任意条数**，1 条也算）走的是 multi 路径，而 multi 路径只实现了
  // stack / stackExpand / stream / radar / pie —— 配 line/area 会落到 undefined，渲出空图。
  // 想画折线要用**单序列的 `data`/`csv`**（ChartDatum = {label, value}）。
  if (multi && !(['stack', 'stackExpand', 'stream', 'radar', 'pie'] as readonly string[]).includes(variant)) {
    throw new Error(
      `Chart: 用了 series（${series?.length ?? 0} 条）就必须配 stack / stackExpand / stream / radar / pie，` +
      `当前 variant="${String(variant)}" 会渲出空图。单条折线请改用 data={[{label, value}, …]} 或 csv。`);
  }
  if (multi && variant === 'radar') {
    // 雷达的外接圆受**较短边**限制，所以留白只按轴标签需要的一圈算（56）——
    // 之前用 74 时半径只剩 135px，四个维度挤在中间，远看像个墨点。
    const rMax = Math.min(innerW, innerH) / 2 - 56;
    const cxr = innerW / 2;
    const cyr = innerH / 2;
    const maxV = Math.max(1, ...multi.flatMap((s) => s.values));
    const rScale = scaleLinear().domain([0, maxV]).range([0, rMax]);
    const angle = (i: number) => (i * 2 * Math.PI) / Math.max(1, n);
    radarSvg = (
      <g transform={`translate(${padL + cxr},${padT + cyr})`}>
        {/* 蛛网环 */}
        {[0.25, 0.5, 0.75, 1].map((k) => (
          <polygon
            key={k}
            points={Array.from({length: n}, (_, i) => `${Math.sin(angle(i)) * rMax * k},${-Math.cos(angle(i)) * rMax * k}`).join(' ')}
            fill="none"
            stroke={C.line}
            strokeWidth={1.6}
          />
        ))}
        {Array.from({length: n}, (_, i) => (
          <line key={i} x1={0} y1={0} x2={Math.sin(angle(i)) * rMax} y2={-Math.cos(angle(i)) * rMax} stroke={C.line} strokeWidth={1.6} />
        ))}
        {multi.map((s, si) => {
          const q = prog(f, startAt + 6 + si * 8, 34);
          const toneS = s.tone ?? TONE[si % TONE.length];
          // 生长动画：半径整体缩放到 q（纯函数，同一帧多次渲染结果一致）
          const rScaled = lineRadial<number>()
            .angle((_, i) => angle(i))
            .radius((v) => rScale(v) * q)
            .curve(curveMonotoneX);
          return (
            <g key={s.name}>
              <path d={rScaled(s.values) ?? ''} fill={`${toneS}33`} stroke={toneS} strokeWidth={4} strokeLinejoin="round" opacity={q} />
            </g>
          );
        })}
        {/* 轴标签：反推字号，不让中文溢出相邻轴的夹角 */}
        {axisLabels.map((l, i) => {
          const lx = Math.sin(angle(i)) * (rMax + 40);
          const ly = -Math.cos(angle(i)) * (rMax + 26);
          const box = 132;
          const fit = fitChineseTextOnNLines({text: l, maxLines: 1, maxBoxWidth: box, maxFontSize: TYPE.microL});
          if (process.env.NODE_ENV !== 'production') fitsWithin({text: l, boxWidth: box, fontSize: fit.fontSize, label: `Chart radar 轴标签[${i}]`});
          return (
            <text key={l + i} x={lx} y={ly + 6} textAnchor="middle" fontFamily="Kai,sans-serif" fontSize={fit.fontSize} fontWeight={700} fill={C.ink}>
              {l}
            </text>
          );
        })}
        {multi.map((s, si) => (
          <g key={`rl${s.name}`} transform={`translate(${-cxr + 12},${cyr - 30 + si * 30})`}>
            <rect width={22} height={22} rx={5} fill={s.tone ?? TONE[si % TONE.length]} stroke={C.ink} strokeWidth={2} />
            <text x={32} y={17} fontFamily="Kai,sans-serif" fontSize={TYPE.microL} fontWeight={700} fill={C.ink}>
              {s.name}
            </text>
          </g>
        ))}
      </g>
    );
  }

  // ---- 饼图 / 环形图：pie + arc ----
  let pieSvg: React.ReactNode = null;
  if (multi && variant === 'pie') {
    const rMax = Math.min(innerW * 0.62, innerH) / 2 - 8;
    const cxp = innerW * 0.32;
    const cyp = innerH / 2;
    // 饼图的「一个序列 = 一个扇区」：取每个序列的第一个值当面积，序列名当标签。
    // （不要用 multi[0].values 的整列——那是堆叠/河流的取法，饼图会只剩一块 100%。）
    const sliceVals = multi.map((s) => s.values[0] ?? 0);
    const pieGen = d3pie<number>()
      .value((v) => v)
      .sort(null);
    const arcs = pieGen(sliceVals);
    const total = sliceVals.reduce((a, b) => a + b, 0) || 1;
    const arcGen = d3arc<{startAngle: number; endAngle: number}>()
      .innerRadius(rMax * innerRadius)
      .outerRadius(rMax);
    pieSvg = (
      <g transform={`translate(${padL + cxp},${padT + cyp})`}>
        {arcs.map((a, i) => {
          const q = prog(f, startAt + 4 + i * 6, 30);
          const a0 = a.startAngle;
          const a1 = a0 + (a.endAngle - a0) * q;
          const toneS = multi[i]?.tone ?? TONE[i % TONE.length];
          const mid = (a0 + a1) / 2;
          const labelR = rMax * (innerRadius > 0.2 ? (1 + innerRadius) / 2 : 0.62);
          const lx = Math.sin(mid) * labelR;
          const ly = -Math.cos(mid) * labelR;
          const pct = Math.round(((a.endAngle - a.startAngle) / (2 * Math.PI)) * 100);
          return (
            <g key={i} opacity={q}>
              <path d={arcGen({startAngle: a0, endAngle: a1}) ?? ''} fill={toneS} stroke={C.ink} strokeWidth={3} />
              {pct >= 7 ? (
                <text x={lx} y={ly + 7} textAnchor="middle" fontFamily="Space,monospace" fontSize={TYPE.microL} fontWeight={700} fill={C.white}>
                  {Math.round((sliceVals[i] / total) * 100)}%
                </text>
              ) : null}
            </g>
          );
        })}
        {/* 图例在右侧：饼内塞不下的名字走这里（而不是硬塞进扇区） */}
        {multi.map((s, i) => {
          const q = prog(f, startAt + 10 + i * 5, 24);
          const fit = fitChineseTextOnNLines({text: `${s.name}　${sliceVals[i]}`, maxLines: 1, maxBoxWidth: 300, maxFontSize: TYPE.bodyM});
          return (
            <g key={s.name} transform={`translate(${cxp + rMax * 0.75},${-(multi.length * 34) / 2 + i * 34})`} opacity={q}>
              <rect width={26} height={26} rx={6} y={-14} fill={s.tone ?? TONE[i % TONE.length]} stroke={C.ink} strokeWidth={2.4} />
              <text x={38} y={7} fontFamily="Kai,sans-serif" fontSize={fit.fontSize} fontWeight={700} fill={C.ink}>
                {fit.lines[0]}
              </text>
            </g>
          );
        })}
      </g>
    );
  }

  // ---- 单序列：line（默认）/ area ----
  const isArea = variant === 'area';
  // scaleBand 取代原来手算的 barW：柱宽、柱心、X 轴刻度位置全部由刻度尺给出
  const band = scaleBand<string>()
    .domain(rows.map((d, i) => `${d.label}#${i}`))
    .range([0, innerW])
    .padding(0.42);
  const bandAt = (i: number) => (band(`${rows[i].label}#${i}`) ?? 0) + band.bandwidth() / 2;
  const x = scaleLinear()
    .domain([0, Math.max(1, rows.length - 1)])
    .range([0, innerW]);
  // area 变体：X 覆盖整宽（首尾贴边）；折线/柱用 band 中心
  const xAt = (i: number) => (isArea ? x(i) : bandAt(i));
  const y = scaleLinear()
    .domain([0, Math.max(...rows.map((d) => d.value), 1) * 1.15])
    .nice()
    .range([innerH, 0]);

  const path = d3line<ChartDatum>()
    .x((_, i) => xAt(i))
    .y((d) => y(d.value))
    .curve(curveMonotoneX)(rows);
  const areaPath = d3area<ChartDatum>()
    .x((_, i) => xAt(i))
    .y0(innerH)
    .y1((d) => y(d.value))
    .curve(curveMonotoneX)(rows);
  const barW = band.bandwidth();
  const barGrow = prog(f, startAt + 10, 40);
  const dashLen = 6000;
  void barW;

  const singleSvg = (
    <g transform={`translate(${padL},${padT})`}>
      <YAxis ticks={y.ticks(5)} y={y} innerW={innerW} unit={unit} />
      {showBars && !isArea
        ? rows.map((d, i) => {
            const hh = innerH - y(d.value);
            const q = prog(f, startAt + 6 + i * 5, 26);
            const bw = band.bandwidth();
            return (
              <rect
                key={d.label + i}
                x={(band(`${d.label}#${i}`) ?? 0) + bw * 0.18}
                y={innerH - hh * barGrow}
                width={bw * 0.64}
                height={hh * barGrow}
                fill={`${accent}22`}
                stroke={accent}
                strokeWidth={2}
                opacity={q}
                rx={4}
              />
            );
          })
        : null}
      {isArea && areaPath ? <path d={areaPath} fill={`${accent}33`} stroke="none" opacity={grow} /> : null}
      {path ? (
        <path
          d={path}
          fill="none"
          stroke={accent}
          strokeWidth={6}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={dashLen}
          strokeDashoffset={dashLen * (1 - grow)}
        />
      ) : null}
      <Axes innerW={innerW} innerH={innerH} labels={rows.map((d) => d.label)} at={xAt} />
      {rows.map((d, i) => {
        const q = prog(f, startAt + 8 + (i / Math.max(1, rows.length - 1)) * 36, 12);
        // 面积变体的首尾点是**贴着绘图区边缘**的（X 铺满整宽），数值标签若仍居中，
        // 头一个标签会伸到 Y 轴刻度字的下面（实测 frame 435：「12」压在「20k」上）。
        // 所以只在两端改成 start/end 锚点——标签始终留在绘图区内。
        const edge = isArea && rows.length > 1 && (i === 0 || i === rows.length - 1);
        const anchor = edge ? (i === 0 ? 'start' : 'end') : 'middle';
        return (
          <g key={i} transform={`translate(${xAt(i)},${y(d.value)})`} opacity={q}>
            <circle r={13 * q + 4} fill={C.paper} stroke={accent} strokeWidth={5} />
            <text y={-34} textAnchor={anchor} fontFamily="Space,monospace" fontSize={TYPE.microL} fontWeight={700} fill={C.ink}>
              {d.value}
            </text>
          </g>
        );
      })}
    </g>
  );

  const body = multi ? (variant === 'radar' ? radarSvg : variant === 'pie' ? pieSvg : stackSvg) : singleSvg;

  return (
    <div style={{width, height, position: 'relative'}}>
      {titleNode}
      <svg width={width} height={svgH} style={{overflow: 'visible'}}>
        {body}
      </svg>
    </div>
  );
};

/** StatRow — 指标卡一行。数字随帧滚动；字符串值直接显示（供"标签/值"型卡片复用）。 */
export const StatRow: React.FC<{
  f: number;
  startAt: number;
  items: {value: number | string; suffix?: string; label: string; tone: string}[];
  width: number;
  height?: number;
  gap?: number;
}> = ({f, startAt, items, width, height = 150, gap = 22}) => {
  // 卡片是固定尺寸、文案是变量——开发期用实测宽度自检，文案比卡片宽就在控制台出声
  const cardInnerW = (width - gap * Math.max(0, items.length - 1)) / Math.max(1, items.length) - 60 - 14;
  return (
    <div style={{display: 'flex', gap, width, height}}>
      {items.map((it, i) => {
        const p = prog(f, startAt + i * 8, 26);
        const shown = typeof it.value === 'number' ? `${Math.round(it.value * p)}${it.suffix ?? ''}` : it.value;
        if (process.env.NODE_ENV !== 'production') {
          fitsWithin({text: String(shown), boxWidth: cardInnerW, fontSize: TYPE.displayXS, fontWeight: 700, label: `StatRow[${i}] 值`});
          fitsWithin({text: it.label, boxWidth: cardInnerW, fontSize: TYPE.labelS, label: `StatRow[${i}] 标签`});
        }
        return (
          <div
            key={i}
            style={{
              flex: 1,
              background: C.paper,
              border: `2.5px solid ${C.ink}`,
              borderLeft: `14px solid ${it.tone}`,
              borderRadius: THEME.aesthetic.paperRadius,
              boxShadow: THEME.paperShadow(0.5),
              padding: '24px 30px',
              opacity: p,
              transform: `translateY(${(1 - p) * 18}px)`,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
            }}
          >
            <div style={{fontFamily: 'Space,Kai,monospace', fontSize: TYPE.displayXS, fontWeight: 700, color: it.tone}}>{shown}</div>
            <div style={{fontFamily: 'Kai,sans-serif', fontSize: TYPE.labelS, color: C.ink, marginTop: 8}}>{it.label}</div>
          </div>
        );
      })}
    </div>
  );
};
