// ============================================================================
// linework/sketch.tsx · 线稿层渲染器（3.5.0）
//
// 输入：一镜的 sketch spec（compose 已把 acts 的 @引用换算成本镜帧号）+ 一个画面方框。
// 输出：皮肤墨色的简笔线稿，7 个动词（enter / point / drop / swap / count / mark / exit）。
//
// 纪律：
//   · 只用帧 f 驱动，没有 useState / 随机（渲染可重放）；
//   · 线稿只用皮肤自己的 ink + 一个强调色；单帧强调色面积 ≤15%（point 只描边、dim 其余）；
//   · 不在这一层做运镜：镜头推近由 cinema 负责，线稿只是被拍的东西。
// ============================================================================
import React from 'react';
import {Easing, interpolate} from 'remotion';
import {THEME} from '../theme/active';
import {useSvgId, warnOnce} from '../uid';
import {PART_CROP} from './crops';
import {SKETCHES} from './library';
import type {Fill, Prim, SketchAct, SketchDef, SketchSpec} from './types';

const C = THEME.palette;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const INK = () => THEME.craft?.inkLine ?? C.ink;
const ACCENT = () => THEME.craft?.accent ?? C.orange;

type State = {
  entered: number;
  exited: number | null;
  point: {target: string; at: number} | null;
  dropped: Record<string, number>;
  swapped: Record<string, number>;
  count: {n: number; at: number} | null;
  mark: {target?: string; kind: 'check' | 'cross' | 'circle'; at: number} | null;
};

const stateAt = (acts: SketchAct[], f: number): State => {
  const s: State = {entered: 0, exited: null, point: null, dropped: {}, swapped: {}, count: null, mark: null};
  for (const a of acts) {
    if (a.at > f) break;
    if (a.do === 'enter') s.entered = a.at;
    else if (a.do === 'exit') s.exited = a.at;
    else if (a.do === 'point' && a.target) s.point = {target: a.target, at: a.at};
    else if (a.do === 'drop' && a.target) s.dropped[a.target] = a.at;
    else if (a.do === 'swap' && a.target) s.swapped[a.target] = a.at;
    else if (a.do === 'count') s.count = {n: Math.max(2, a.n ?? 3), at: a.at};
    else if (a.do === 'mark') s.mark = {target: a.target, kind: a.mark ?? 'check', at: a.at};
  }
  return s;
};

const fillOf = (f: Fill | undefined): string => {
  if (f === 'wash') return `${ACCENT()}14`;
  if (f === 'accent') return ACCENT();
  if (f === 'ink') return INK();
  if (f === 'paper') return C.paper;
  return 'none';
};

/** 颜料滤镜：轮廓出格 + 内部未涂满。
 *
 * 为什么不能直接 fill。矢量填充把「形状」和「颜色」合成同一条边界：颜色精确停在线上，
 * 说明线是先验的容器；而手绘的颜料有动量，会越过线（出格），也会挂不匀（留白）。
 * 均匀色块 100% 可预测，视觉系统编码一次就判定为背景，注意力随即离开——这就是
 * 「填得越干净越像贴纸」的真正原因。
 *
 * 一个滤镜做三件事：
 *   feTurbulence(低频) + feDisplacementMap  → 轮廓整体歪掉（出格，2 个数量级尺度）
 *   feTurbulence(高频) + feColorMatrix      → alpha = 1.5 - 2.6·噪声，约四成不着色（挂不匀）
 *   feComposite in                          → 用上面那张 alpha 去打洞，只作用于填充、不动描边
 * 放在 filter 里而不是每帧算，是因为它必须确定性（seed 来自 id），渲染才可重放。
 */
const paintFilter = (svgUid: string, seed: number) => (
  <filter id={svgUid} x="-25%" y="-25%" width="150%" height="150%" colorInterpolationFilters="sRGB">
    <feTurbulence type="fractalNoise" baseFrequency="0.14" numOctaves="2" seed={seed} result="warp" />
    <feDisplacementMap in="SourceGraphic" in2="warp" scale="2.1" xChannelSelector="R" yChannelSelector="G" result="wob" />
    <feTurbulence type="fractalNoise" baseFrequency="0.42" numOctaves="2" seed={seed + 17} result="grain" />
    <feColorMatrix in="grain" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.6 1.5" result="holes" />
    <feComposite in="wob" in2="holes" operator="in" />
  </filter>
);

/** 单个基本形。描出进度 p：path/line 用 dash 画线，闭合形用淡入。
 *  填充与描边分成两层：填充过 paint 滤镜（出格 + 打洞），描边保持干净——
 *  线稿的线一旦被打洞就断成芝麻点，那不是手绘，那是信号不好。 */
const PrimView: React.FC<{p: Prim; prog: number; color: string; sw: number; paint?: string; key?: React.Key}> = ({p, prog, color, sw, paint}) => {
  if (prog <= 0) return null;
  const fill = p.k === 'line' ? 'none' : fillOf('fill' in p ? p.fill : undefined);
  const dash = {pathLength: 1, strokeDasharray: 1, strokeDashoffset: 1 - prog} as const;
  const strokeCommon = {
    stroke: color,
    strokeWidth: sw,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    fill: 'none',
  };
  const o = Math.min(1, prog * 1.8);
  const fillLayer = fill === 'none' ? null : p.k === 'path'
    ? <path d={p.d} fill={fill} stroke="none" opacity={Math.min(1, prog * 1.6)} filter={paint ? `url(#${paint})` : undefined} />
    : p.k === 'rect'
      ? <rect x={p.x} y={p.y} width={p.w} height={p.h} rx={p.rx ?? 0} fill={fill} stroke="none" opacity={o} filter={paint ? `url(#${paint})` : undefined} />
      : p.k === 'circle'
        ? <circle cx={p.cx} cy={p.cy} r={p.r} fill={fill} stroke="none" opacity={o} filter={paint ? `url(#${paint})` : undefined} />
        : null;
  const strokeLayer = p.k === 'path'
    ? <path d={p.d} {...strokeCommon} {...dash} />
    : p.k === 'line'
      ? <line x1={p.x1} y1={p.y1} x2={p.x2} y2={p.y2} {...strokeCommon} {...dash} />
      : p.k === 'rect'
        ? <rect x={p.x} y={p.y} width={p.w} height={p.h} rx={p.rx ?? 0} {...strokeCommon} opacity={o} />
        : <circle cx={p.cx} cy={p.cy} r={p.r} {...strokeCommon} opacity={o} />;
  return <>{fillLayer}{strokeLayer}</>;
};

const PrimGroup: React.FC<{prims: Prim[]; prog: number; color: string; sw: number; paint?: string}> = ({prims, prog, color, sw, paint}) => (
  <>
    {prims.map((p, i) => (
      // 同组基本形同时起笔、错峰收尾：第 i 个延后一点，整体仍在 prog 内完成
      <PrimView key={i} p={p} prog={Math.max(0, Math.min(1, prog * 1.35 - i * 0.06))} color={color} sw={sw} paint={paint} />
    ))}
  </>
);

type Fit = [number, number, number, number];
const fitOf = (def: SketchDef): Fit => def.fit ?? [0, 0, 100, 100];
const relPos = (fit: Fit, x: number, y: number): [number, number] => {
  const [fx, fy, fw, fh] = fit;
  return [((x - fx) / fw) * 100, ((y - fy) / fh) * 100];
};

const partAnchor = (def: SketchDef, id: string, crop?: Fit): [number, number] => {
  const part = def.parts[id];
  if (!part) return [50, 50];
  if (part.anchor) return part.anchor;
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (const p of part.prims) {
    if (p.k === 'circle') { x0 = Math.min(x0, p.cx - p.r); x1 = Math.max(x1, p.cx + p.r); y0 = Math.min(y0, p.cy - p.r); y1 = Math.max(y1, p.cy + p.r); }
    else if (p.k === 'rect') { x0 = Math.min(x0, p.x); x1 = Math.max(x1, p.x + p.w); y0 = Math.min(y0, p.y); y1 = Math.max(y1, p.y + p.h); }
    else if (p.k === 'line') { x0 = Math.min(x0, p.x1, p.x2); x1 = Math.max(x1, p.x1, p.x2); y0 = Math.min(y0, p.y1, p.y2); y1 = Math.max(y1, p.y1, p.y2); }
  }
  // 只有 path 的部位算不出包围盒（这一层不做路径解析）：用构建期生成的缺省取景框中心。
  // 以前一律 [50,50]，于是「绳与结」「灯丝」这类全 path 部位的引线总是指向画面正中。
  if (x0 > x1) return crop ? [crop[0] + crop[2] / 2, crop[1] + crop[3] / 2] : [50, 50];
  return [(x0 + x1) / 2, (y0 + y1) / 2];
};

const shapesToDef = (raw: string): SketchDef | null => {
  // draw 写成 `shapes:[{k:'rect',x,y,w,h},…]` —— 弱模型自拼，≤10 个形由 compose 门禁保证
  try {
    const arr = JSON.parse(raw) as Array<Record<string, unknown>>;
    const prims: Prim[] = [];
    for (const s of arr.slice(0, 12)) {
      const kind = String(s.k ?? s.kind ?? '');
      if (kind === 'rect') prims.push({k: 'rect', x: Number(s.x), y: Number(s.y), w: Number(s.w), h: Number(s.h), rx: Number(s.rx ?? 0)});
      else if (kind === 'circle') prims.push({k: 'circle', cx: Number(s.cx ?? s.x), cy: Number(s.cy ?? s.y), r: Number(s.r ?? 8)});
      else if (kind === 'line') prims.push({k: 'line', x1: Number(s.x1), y1: Number(s.y1), x2: Number(s.x2), y2: Number(s.y2)});
      else if (kind === 'path') prims.push({k: 'path', d: String(s.d ?? '')});
      else if (kind === 'dots') prims.push({k: 'circle', cx: Number(s.x), cy: Number(s.y), r: Number(s.r ?? 2)});
    }
    if (!prims.length) return null;
    return {label: '自拼线稿', parts: {all: {label: '整体', prims}}};
  } catch {
    return null;
  }
};

export const resolveSketchDef = (spec: SketchSpec): SketchDef | null => {
  const draw = String(spec.draw ?? '');
  if (draw.startsWith('lib:')) return SKETCHES[draw.slice(4)] ?? null;
  if (draw.startsWith('shapes:')) return shapesToDef(draw.slice(7));
  return null; // trace: 由照片配方单独处理
};

export const SketchLayer: React.FC<{spec: SketchSpec; f: number; box: {x: number; y: number; w: number; h: number}; scale?: number}> = ({spec, f, box, scale = 1}) => {
  // hook 必须在任何 return 之前调用：组件在入场前会 return null，位置一变就违反 hooks 规则。
  const svgUid = useSvgId('paint');
  const def = resolveSketchDef(spec);
  if (!def) {
    // 名字写错时引擎什么都不画：必须留痕，否则成片里只是"这一镜少了张图"（P1-09 构建期已拦，
    // 这里兜住手写 shots.ts 的情况）。
    warnOnce(`draw:${spec.id}`, `[Sketch] ${spec.id}: draw=${spec.draw} 解析不出线稿（lib 名字不存在 / shapes JSON 无效），这一镜是空的`);
    return null;
  }
  // 墨图页的 parts 数组是「只画这些部位」，不是 point 的标注表。
  // 旧版把它原样传进来却从不筛选，S1 写 ['hull','line']、S4 写 ['plank'] 结果都画整张 chiplog。
  const selected = Array.isArray(spec.parts) ? new Set(spec.parts) : null;
  const visibleParts = Object.entries(def.parts).filter(([id]) => !selected || selected.has(id));
  // 一个已知部位都没命中时不能悄悄画空：退回整图并保留渲染日志，让作者能修正拼写。
  const unknownSelection = selected && visibleParts.length === 0;
  if (unknownSelection && selected) warnOnce(`parts:${spec.id}:${[...selected].join(',')}`, `[Sketch] ${spec.id}: parts=[${[...selected].join(',')}] 在 ${spec.draw} 中都不存在，已画整图`);
  const partEntries = unknownSelection ? Object.entries(def.parts) : visibleParts;
  // 单部位特写：部位自己写的 fit 优先；没写的用构建期按真实基本形算出的缺省取景框
  // （src/linework/crops.ts）。两者都没有才退回整图——那时特写会小，但不会框错。
  const onlyName = selected && selected.size === 1 ? [...selected][0] : undefined;
  const only = onlyName ? def.parts[onlyName] : undefined;
  const cropFor = (id: string): Fit | undefined => {
    const draw = String(spec.draw ?? '');
    return draw.startsWith('lib:') ? PART_CROP[draw.slice(4)]?.[id] : undefined;
  };
  const viewFit = only?.fit ?? (onlyName ? cropFor(onlyName) : undefined) ?? fitOf(def);
  const partLabels = Array.isArray(spec.parts) ? undefined : spec.parts;
  const acts = (spec.frames ?? []).slice().sort((a, b) => a.at - b.at);
  const st = stateAt(acts, f);
  const start = spec.persist ? -999 : st.entered;
  if (f < start) return null;
  const enter = spec.persist ? 1 : interpolate(f, [start, start + 18], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const exit = st.exited === null ? 0 : interpolate(f, [st.exited, st.exited + 12], [0, 1], clamp);
  const opacity = enter * (1 - exit);
  if (opacity <= 0.01) return null;
  const ink = INK();
  const accent = ACCENT();
  // 颜料滤镜的 seed 由 spec.id 定死：每帧重算也得是同一张图，否则渲染不可重放。
  // 但 **DOM id 不能用它**——转场期间两镜同时挂载，同名 spec.id 会渲染出两个同 id 的 filter（P1-08）。
  const seedKey = String(spec.id ?? 'sk').replace(/[^\w-]/g, '');
  const paintSeed = [...seedKey].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7) % 900;
  // 三档线（仿 a2e 的「大外壳 > 内部结构 > 细节」）：轮廓最粗、内部次之、细节再细一档且偏暖灰。
  // 旧版所有线一个宽度 → 看起来像卡通用色块拼的剪贴画。
  const base = (THEME.id === 'cel' ? 1.35 : 0.95) / Math.max(0.6, scale);
  const pointId = st.point?.target;
  const pointP = st.point ? interpolate(f, [st.point.at, st.point.at + 8], [0, 1], clamp) : 0;
  const count = st.count ? st.count.n : 1;
  const countP = st.count ? interpolate(f, [st.count.at, st.count.at + 10], [0, 1], clamp) : 1;
  // count：把同一线稿复制 n 份，横排；每份错 3 帧入场
  const copies = Array.from({length: count}, (_, i) => i);
  const cw = 100 / Math.max(1, count);
  return (
    <div data-gate-allow="sketch" style={{position: 'absolute', left: box.x, top: box.y, width: box.w, height: box.h, opacity}}>
      {copies.map((i) => {
        const cp = st.count ? interpolate(f, [st.count.at + i * 3, st.count.at + i * 3 + 8], [0, 1], clamp) : 1;
        const cScale = count > 1 ? 0.55 + 0.45 * Math.min(1, countP) : 1;
        const pid = `${svgUid}-${i}`;
        return (
          <svg key={i} viewBox={viewFit.join(' ')}
               style={{position: 'absolute', left: `${i * cw}%`, top: 0, width: `${count > 1 ? cw : 100}%`, height: `${cScale * 100}%`, opacity: cp, overflow: 'visible'}}>
            <defs>{paintFilter(pid, paintSeed)}</defs>
            {def.base && <PrimGroup prims={def.base} prog={enter} color={ink} sw={base * 0.8} paint={pid} />}
            {partEntries.map(([id, part]) => {
              const dropAt = st.dropped[id];
              const dropP = dropAt === undefined ? 0 : interpolate(f, [dropAt, dropAt + 16], [0, 1], {...clamp, easing: Easing.in(Easing.cubic)});
              if (dropP >= 1) return null;
              const swapped = st.swapped[id] !== undefined;
              const prims = swapped && part.alt ? part.alt : part.prims;
              const isPoint = pointId === id;
              const dim = pointId && !isPoint ? 0.5 : 1;
              const [ax, ay] = partAnchor(def, id, cropFor(id));
              return (
                <g key={id} opacity={dim * (1 - dropP)}
                   transform={dropP > 0 ? `translate(${ax * 0.06 * dropP} ${24 * dropP}) rotate(${10 * dropP} ${ax} ${ay})` : undefined}>
                  <PrimGroup prims={prims} prog={enter} color={isPoint ? accent : part.detail ? C.muted : ink}
                             sw={isPoint ? base * 1.35 : part.detail ? base * 0.72 : base} paint={pid} />
                </g>
              );
            })}
          </svg>
        );
      })}
      {/* point 的手写标注：写在部位锚点右上方，不抢线稿 */}
      {st.point && pointP > 0 && st.dropped[st.point.target] === undefined && (() => {
        const [ax0, ay0] = partAnchor(def, st.point.target, cropFor(st.point.target));
        const [ax, ay] = relPos(viewFit, ax0, ay0);
        const label = st.point ? (partLabels?.[st.point.target] ?? def.parts[st.point.target]?.label ?? '') : '';
        if (!label) return null;
        // 标注放在线稿外侧：右侧锚点 → 标签往左，左侧锚点 → 往右；引线细、起点一个点（仿 a2e 的 leader）。
        const toLeft = ax > 52;
        const textX = toLeft ? ax - 12 : ax + 12;
        return (
          <>
            <svg viewBox={viewFit.join(' ')} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', overflow: 'visible', pointerEvents: 'none'}}>
              <line x1={ax0} y1={ay0} x2={ax0 + (toLeft ? -9 : 9)} y2={ay0 - 5} stroke={THEME.craft?.inkLine ?? C.ink} strokeWidth={0.5} opacity={0.75 * pointP} />
              <circle cx={ax0} cy={ay0} r={1.1} fill={accent} opacity={pointP} />
            </svg>
            <div style={{
              position: 'absolute', left: `${textX}%`, top: `${ay - 5}%`,
              transform: `translate(${toLeft ? '-100%' : '0'}, -50%) scale(${0.94 + 0.06 * pointP})`,
              fontFamily: THEME.craft?.handFamily ?? 'Kai', fontSize: 27, fontWeight: 700, color: accent,
              background: `${C.paper}E6`, padding: '1px 7px', borderRadius: 6, whiteSpace: 'nowrap', opacity: pointP,
            }}>{label}</div>
          </>
        );
      })()}
      {/* mark：勾 / 叉 / 圈 */}
      {st.mark && (() => {
        const p = interpolate(f, [st.mark.at, st.mark.at + 10], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
        const [ax0, ay0] = st.mark.target ? partAnchor(def, st.mark.target, cropFor(st.mark.target)) : [84, 16];
        const [ax, ay] = relPos(viewFit, ax0, ay0);
        const path = st.mark.kind === 'check' ? 'M -8 0 L -2 7 L 10 -9' : st.mark.kind === 'cross' ? 'M -8 -8 L 8 8 M 8 -8 L -8 8'
          : 'M 0 -10 A 11 9 0 1 0 0.1 -10';
        return (
          <svg viewBox="-20 -20 40 40" width={96} height={96} style={{position: 'absolute', left: `${ax}%`, top: `${ay}%`, transform: 'translate(calc(-50% + 118px), calc(-50% - 76px))', overflow: 'visible'}}>
            <path d={path} fill="none" stroke={st.mark.kind === 'cross' ? C.red : accent} strokeWidth={2.4} strokeLinecap="round"
                  pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />
          </svg>
        );
      })()}
    </div>
  );
};
