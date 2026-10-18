import React from 'react';
// 2026-10-17（3.2.0 · Phase 3）：12 个 Radix 包全部移除。Accordion / Tabs / ControlStack 只需要
// 结构 + 皮肤，渲染期没有交互，Radix 带来的只是 ARIA 外壳和 Slider 的 ResizeObserver 测量
// （确定性风险）。现在全部是纯 <div>，状态 100% 来自帧号。
// 代码高亮从 react-syntax-highlighter（Prism）换成 Shiki（同步核心 + JS 正则引擎，见 ./shiki.ts）。
import {highlightTokens} from './shiki';
import katex from 'katex';
import 'katex/dist/katex.min.css';
// 图标：lucide-react（ISC，线条）+ simple-icons（CC0，品牌 logo）。react-icons 已移除。
import {
  Brain, Rocket, Sparkles, CircleCheck, Bot, Bug, Ruler, Gauge, GitBranch, Workflow, Milestone, Wrench, Zap,
  FileCode, Server, ShieldCheck, ChartLine, Puzzle, Lightbulb, Flag, Terminal, Layers, Package, Cpu, Database, Cloud,
  ChevronDown, Check,
} from 'lucide-react';
import type {LucideIcon} from 'lucide-react';
import {siReact, siNodedotjs, siPython, siDocker, siGit, siNpm, siGithub} from 'simple-icons';
import {Easing, interpolate, spring} from 'remotion';
import {THEME} from '../theme/active';
import {TYPE, PillTag} from '../kit';
import {fitH} from '../fxkit';
// ⚠️ fitsWithin 在 ControlStack 里以 dev 自检调用，却**从未 import** —— tsc 报 TS2304。
// 与 stagekit 的 SlotGuard 同一种病：引用了不存在的标识符，而它挂在
// `process.env.NODE_ENV !== 'production'` 下，出片路径永远走不到 → 一路静默。
import {fitChineseTextOnNLines, fitsWithin} from './fittext';

// ============================================================================
// ui.tsx — 界面结构件（库提供结构，本层提供皮肤 + 帧驱动）
//
// 契约（见 references/dependency-policy.md §7）：
//   1. 场景 import 本层，不直接 import 原始库
//   2. 颜色/边框/圆角/阴影只从 THEME 取
//   3. 动画一律 f(帧号) 的纯函数：禁 CSS transition / setTimeout / Math.random
//   4. 文字容器高度用 fitH() 或 fitTextOnNLines() 算出
//   5. 正文纯墨色 C.ink；muted 只用于装饰性 kicker
// ============================================================================

const C = THEME.palette;
const RADIUS = THEME.aesthetic.paperRadius;

const TONE: Record<string, string> = {
  blue: C.blue,
  orange: C.orange,
  green: C.green,
  gold: C.gold,
  red: C.red,
};
const toneOf = (t?: string) => TONE[t ?? 'blue'] ?? C.blue;

/**
 * 帧驱动进度，带夹取。所有入场动画都走这个。
 *
 * 2026-09-21 修（实测）：原来是**匀速直线**（interpolate 不给 easing）。
 * 新层 36 处入场因此全都是"机械地滑到位"，而旧六模块的入场一律是缓出曲线，
 * 一屏之内两种运动质感并存，读起来就是"新组件不如老的顺"。
 * 现在统一用与 scenes 层 enterAt / fxkit easeOutSoft 同一条曲线
 * `bezier(.16,1,.3,1)`（先快后慢、尾巴长），新旧两层的入场手感就此对齐。
 * 数值型用法（图层描线进度、可滑动控件的 glide）走同一条曲线也是对的——
 * 它们要的同样是"落位时收住"，不是"匀着走完"。
 */
export const prog = (f: number, from: number, dur = 22) =>
  interpolate(f - from, [0, dur], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

/**
 * presence — 「入场 → 常驻 → 离场」的通用存在感。
 *
 * 2026-09-21 修（实测）：新层 36 处入场**只进不出**，`exitStart` 出现 0 次
 * （旧六模块的组件件件支持离场）。后果是"一镜之内演第二件事"时，上一件事只能
 * 靠切镜消失——S14 就是这么把弹层叠在手风琴上、造成真实文字遮挡的。
 * 组件拿到 exitStart 就能主动让位：离场用 18 帧 ease-in 收掉并向上退 14px。
 *
 * 返回 {p 入场进度, out 离场进度(0=还在, 1=已走), op 综合不透明度, dx 位移}。
 */
export const presence = (f: number, startAt: number, exitStart?: number, durIn = 22) => {
  const p = prog(f, startAt, durIn);
  const out = exitStart === undefined ? 0 : prog(f, exitStart, 18);
  return {
    p,
    out,
    op: p * (1 - out),
    dx: (1 - p) * 22 - out * 14,
  };
};

// ---------------------------------------------------------------------------
// Accordion — 纯 div（3.2.0 起不再依赖 @radix-ui/react-accordion）
// 用法：<Accordion f={f} items={[{title, body, tone}]} startAt={18} step={58} />
// 展开项由帧号累积决定；**展开高度按真实文本折几行算出来**（不再猜行数）；支持 exitStart 让位。
// ---------------------------------------------------------------------------
export type AccordionItem = {title: string; body: string; tone?: 'blue' | 'orange' | 'green' | 'gold' | 'red'};

export const Accordion: React.FC<{
  f: number;
  items: AccordionItem[];
  startAt: number;
  step: number;
  width: number;
  rowH?: number;
  /** 每项内容**至少**留几行的展开高度（默认 2）。真实文本更长时按真实行数加高，不会裁字。 */
  bodyRows?: number;
  /** 离场起始帧：给了就在之后 18 帧内让位（让同一屏里的下一个元素有地方落） */
  exitStart?: number;
}> = ({f, items, startAt, step, width, rowH = 96, bodyRows = 2, exitStart}) => {
  const openedCount = Math.max(0, Math.min(items.length, Math.floor((f - startAt) / step) + 1));
  // 2026-09-21 修（实测）：展开高度原来是 `bodyRows` 行 × 行高**猜**出来的。
  // 正文短于 bodyRows 行时面板偏高（空白），长于 bodyRows 行时正文被 overflow:hidden
  // **裁掉尾巴**——接触表第 ⑭ 页实测过这件事（"Accordion 塞不进图表，是被裁剩一条"）。
  // 现在按**真实文本在当前宽度下折几行**算高度：用的是封装层自己的断行器（budoux + UAX#14），
  // 与渲染同字体同字号，所以"算出来几行"就是"画出来几行"。bodyRows 退化为**下限**（保观感一致）。
  const innerW = Math.max(120, width - 64); // 触发器左右各 32 padding
  const linesOf = (t: string) => {
    try {
      return fitChineseTextOnNLines({
        text: t,
        maxLines: 99,
        maxBoxWidth: innerW,
        fontFamily: 'Kai',
        fontWeight: 400,
        maxFontSize: TYPE.bodyS,
        minFontSize: TYPE.bodyS,
      }).lines.length;
    } catch {
      return bodyRows; // 量不出来就退回旧行为，不因为量测失败把画面搞坏
    }
  };
  const rows = Math.max(1, bodyRows, ...items.map((it) => linesOf(it.body)));
  const bodyH = fitH(
    Array.from({length: rows}, () => ({h: TYPE.bodyS * 1.72, gapAfter: 2})),
    30,
    30
  );

  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: 22, width}}>
      {items.map((item, i) => {
        const {p, op, dx} = presence(f, startAt + i * step, exitStart);
        const isOpen = i < openedCount;
        const accent = toneOf(item.tone);
        return (
          <div
            key={i}
            style={{
              background: C.paper,
              border: `2.5px solid ${isOpen ? accent : C.ink}`,
              borderRadius: RADIUS,
              boxShadow: THEME.paperShadow(isOpen ? 0.8 : 0.25),
              // 离场：整项（连内容块）一起收掉，不让残留文字压在后来者身上
              opacity: op,
              transform: `translateY(${dx}px)`,
            }}
          >
            <div style={{margin: 0}}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 20,
                  width: '100%',
                  boxSizing: 'border-box',
                  height: rowH,
                  padding: '0 32px',
                  background: 'transparent',
                  border: 'none',
                  cursor: 'default',
                  textAlign: 'left',
                  fontFamily: 'Kai,sans-serif',
                  color: C.ink,
                }}
              >
                <span
                  style={{
                    flex: '0 0 auto',
                    width: 50,
                    height: 50,
                    borderRadius: 999,
                    background: isOpen ? accent : C.mutedFill,
                    color: isOpen ? C.white : C.muted,
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily: 'Space,monospace',
                    fontSize: TYPE.labelL,
                    fontWeight: 700,
                  }}
                >
                  {i + 1}
                </span>
                <span style={{flex: 1, fontSize: TYPE.titleS, fontWeight: 700}}>{item.title}</span>
                {/* V 形箭头，展开时翻转；不要用「＋」转 45°，那会读成关闭按钮 */}
                <ChevronDown
                  size={30}
                  color={isOpen ? accent : C.muted}
                  strokeWidth={2.6}
                  style={{flex: '0 0 auto', transform: `rotate(${interpolate(p, [0, 1], [180, 0])}deg)`}}
                />
              </div>
            </div>
            {/* forceMount：关闭态也留在树上，高度与透明度全按帧驱动 */}
            <div style={{overflow: 'hidden'}}>
              <div style={{height: bodyH * p, opacity: p, overflow: 'hidden', padding: '0 32px'}}>
                <div
                  style={{
                    borderTop: `2px dashed ${C.line}`,
                    paddingTop: 22,
                    fontSize: TYPE.bodyS,
                    lineHeight: 1.72,
                    color: C.ink,
                    fontFamily: 'Kai,sans-serif',
                  }}
                >
                  {item.body}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Tabs — 纯 div（3.2.0 起不再依赖 @radix-ui/react-tabs）
// 用法：<Tabs f={f} tabs={[{key,label,title,body,points,verdict,tone}]} startAt={16} step={88} />
// 激活项由帧号决定；内容淡入不用 CSS 过渡。
// ---------------------------------------------------------------------------
export type TabItem = {
  key: string;
  label: string;
  title: string;
  body: string;
  points: {text: string; mark: string}[];
  verdict: string;
  tone: 'green' | 'gold' | 'orange' | 'blue';
};

export const Tabs: React.FC<{
  f: number;
  tabs: TabItem[];
  startAt: number;
  step: number;
  width: number;
  height: number;
}> = ({f, tabs, startAt, step, width, height}) => {
  const idx = Math.max(0, Math.min(tabs.length - 1, Math.floor((f - startAt) / step)));
  const active = tabs[idx];
  const p = prog(f, startAt + idx * step, 18);
  // 这里原有一个 `const accent = toneOf(active.tone)`，全函数没用过 —— 真正的取色
  // 在 Trigger 与 Content 里各自按 `toneOf(t.tone)` 算（tsc TS6133 抓出来的死变量）。

  return (
    <div style={{width, height, display: 'flex', flexDirection: 'column'}}>
      <div
        style={{
          display: 'flex',
          gap: 14,
          padding: 10,
          background: C.paperWarm,
          border: `2.5px solid ${C.ink}`,
          borderRadius: RADIUS,
          boxShadow: THEME.paperShadow(0.4),
          flex: '0 0 auto',
        }}
      >
        {tabs.map((t, i) => {
          const on = i === idx;
          return (
            <div
              key={t.key}
              style={{
                flex: 1,
                height: 78,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: 'none',
                borderRadius: 8,
                cursor: 'default',
                background: on ? toneOf(t.tone) : 'transparent',
                color: on ? C.white : C.ink,
                fontFamily: 'Kai,sans-serif',
                fontSize: TYPE.titleXS,
                fontWeight: 700,
                boxShadow: on ? 'inset 0 -6px 0 rgba(20,17,15,0.22)' : 'none',
              }}
            >
              {t.label}
            </div>
          );
        })}
      </div>

      {tabs.map((t) => {
        const on = t.key === active.key;
        const a = toneOf(t.tone);
        return (
          <div key={t.key} style={{display: on ? 'block' : 'none', flex: 1, minHeight: 0}}>
            <div
              style={{
                marginTop: 24,
                height: height - 122,
                opacity: p,
                transform: `translateY(${(1 - p) * 24}px)`,
                background: C.paper,
                border: `2.5px solid ${a}`,
                borderRadius: RADIUS,
                boxShadow: THEME.paperShadow(0.7),
                padding: '34px 40px',
                display: 'flex',
                flexDirection: 'column',
                gap: 22,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
                <PillTag text={t.verdict} color={C.white} bg={a} fontSize={TYPE.microL} />
                <span style={{fontSize: TYPE.titleM, fontWeight: 700, color: C.ink}}>{t.title}</span>
              </div>
              <div style={{fontSize: TYPE.bodyM, lineHeight: 1.8, color: C.ink, fontFamily: 'Kai,sans-serif'}}>{t.body}</div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 16, marginTop: 'auto'}}>
                {t.points.map((pt, i) => {
                  const q = prog(f, startAt + idx * step + 12 + i * 8, 16);
                  return (
                    <div
                      key={i}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 18,
                        opacity: q,
                        transform: `translateX(${(1 - q) * 24}px)`,
                        background: C.paperWarm,
                        border: `2.5px solid ${C.ink}`,
                        borderLeft: `14px solid ${a}`,
                        borderRadius: RADIUS,
                        padding: '18px 24px',
                      }}
                    >
                      <span
                        style={{
                          fontFamily: 'Space,monospace',
                          fontSize: TYPE.microS,
                          fontWeight: 700,
                          color: C.white,
                          background: a,
                          borderRadius: 6,
                          padding: '3px 10px',
                        }}
                      >
                        {pt.mark}
                      </span>
                      <span style={{fontFamily: 'Kai,sans-serif', fontSize: TYPE.bodyS, color: C.ink, lineHeight: 1.6}}>{pt.text}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ---------------------------------------------------------------------------
// ControlStack — 「控件状态随旁白变化」（六种控件，纯 div；3.2.0 起不再依赖 Radix）
//
// 为什么需要它：技能此前**完全没有**「控件被拨动」这个形态——要讲"这个选项被打开了"
// 只能写一张文字卡片假装。而 validate-composition.py 的硬门禁要求每个讲解场景
// ≥1 个真的随旁白变状态的构件，「配置 / 选项 / 参数」类内容最自然的语法就是控件本身。
//
// 六种控件（switch / checkbox / radio / segment / slider / progress）全部是纯 div。
//   以前用 Radix 的受控 primitive，但渲染期没有交互，Radix 只贡献了 ARIA 外壳，
//   而 Slider 的拇指靠 ResizeObserver 测量定位（确定性风险）。现在位置全是算出来的。
//
// 帧 → 状态是**一张显式的表**（`steps: [{at: 帧号, value}]`），纯函数、可复算：
//   离散件（开关/复选/单选/分段）在 at 帧**瞬间**切换；
//   连续件（滑块/进度条）在 at 帧之后的 glide 帧内线性滑到位（仍是 f 的纯函数）。
// ---------------------------------------------------------------------------
export type ControlStep = {at: number; value: number | boolean};

type ControlCommon = {label: string; note?: string; tone?: string; steps: ControlStep[]};

export type ControlRow =
  | (ControlCommon & {kind: 'switch'})
  | (ControlCommon & {kind: 'checkbox'})
  | (ControlCommon & {kind: 'radio'; options: string[]})
  | (ControlCommon & {kind: 'segment'; options: string[]})
  | (ControlCommon & {kind: 'slider'; min: number; max: number; unit?: string; step?: number})
  | (ControlCommon & {kind: 'progress'; unit?: string; max?: number});

const isDiscrete = (kind: ControlRow['kind']) => kind === 'switch' || kind === 'checkbox' || kind === 'radio' || kind === 'segment';

/**
 * controlStateAt — 帧号 → 该行控件的状态。**这是本组件唯一的"动画"来源，纯函数。**
 * 离散件返回 boolean 或选项下标；连续件返回数值（在 glide 帧内线性滑到位）。
 */
export const controlStateAt = (row: ControlRow, f: number, glide = 14): number | boolean => {
  const steps = row.steps.slice().sort((a, b) => a.at - b.at);
  if (steps.length === 0) return 0;
  let prev = steps[0];
  let next: ControlStep | undefined;
  for (const s of steps) {
    if (s.at <= f) prev = s;
    else {
      next = s;
      break;
    }
  }
  if (isDiscrete(row.kind) || !next) return prev.value;
  const t = prog(f, prev.at, glide);
  return Number(prev.value) + (Number(next.value) - Number(prev.value)) * t;
};

const ctrlTrack = (on: boolean, tone: string, w: number, h: number): React.CSSProperties => ({
  width: w,
  height: h,
  boxSizing: 'border-box',
  borderRadius: 999,
  background: on ? tone : C.mutedFill,
  border: `2.5px solid ${C.ink}`,
  boxShadow: THEME.paperShadow(0.25),
  position: 'relative',
  flex: '0 0 auto',
  transition: 'none',
});

/**
 * ControlStack — 一叠控件，状态随帧号变化。
 *
 * 用法：
 *   <ControlStack f={f} width={760} items={[
 *     {kind:'switch', label:'自动路由', tone:'green', steps:[{at:0,value:false},{at:24,value:true}]},
 *     {kind:'slider', label:'采样温度', min:0, max:1, unit:'', steps:[{at:38,value:0.2},{at:60,value:0.72}]},
 *   ]} />
 */
export const ControlStack: React.FC<{
  f: number;
  items: ControlRow[];
  width: number;
  /** 行高（标签可能换行时用 fitH 算出的值传进来；默认按单行标题算） */
  rowH?: number;
  gap?: number;
  /** 行容器从第几帧开始逐行入场 */
  startAt?: number;
  step?: number;
  /** 连续件滑动的时长 */
  glide?: number;
}> = ({f, items, width, rowH, gap = 18, startAt = 0, step = 8, glide = 14}) => {
  const h = rowH ?? fitH([{h: TYPE.titleXS * 1.3, gapAfter: 6}, {h: TYPE.bodyS * 1.3}], 26, 26);
  const labelW = Math.min(width * 0.42, 300);
  const ctrlW = Math.min(420, width - labelW - 96);

  return (
    <div style={{display: 'flex', flexDirection: 'column', gap, width}}>
      {items.map((row, i) => {
        const p = prog(f, startAt + i * step, 18);
        const accent = toneOf(row.tone);
        const state = controlStateAt(row, f, glide);
        const on = state === true;
        // 文案长度可变：开发期实测自检（与 StatRow / VerdictBar 同一套）
        if (process.env.NODE_ENV !== 'production') {
          fitsWithin({text: row.label, boxWidth: labelW - 24, fontSize: TYPE.titleXS, fontWeight: 700, label: `ControlStack[${i}] 标签`});
          if (row.note) fitsWithin({text: row.note, boxWidth: labelW - 24, fontSize: TYPE.bodyS, label: `ControlStack[${i}] 说明`});
        }

        return (
          <div
            key={i}
            style={{
              width,
              height: h,
              opacity: p,
              transform: `translateX(${(1 - p) * 22}px)`,
              background: C.paper,
              border: `2.5px solid ${C.ink}`,
              borderLeft: `14px solid ${accent}`,
              borderRadius: RADIUS,
              boxShadow: THEME.paperShadow(0.55),
              display: 'flex',
              alignItems: 'center',
              gap: 22,
              padding: '0 26px 0 22px',
            }}
          >
            <div style={{width: labelW, flex: '0 0 auto'}}>
              <div style={{fontFamily: 'Kai,sans-serif', fontSize: TYPE.titleXS, fontWeight: 700, color: C.ink, lineHeight: 1.3}}>{row.label}</div>
              {row.note ? (
                <div style={{fontFamily: 'Kai,sans-serif', fontSize: TYPE.bodyS, color: C.ink, opacity: 0.72, lineHeight: 1.3, marginTop: 2}}>
                  {row.note}
                </div>
              ) : null}
            </div>
            <div style={{flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 16}}>
              {/* ---- switch ---- */}
              {row.kind === 'switch' ? (
                <div style={{...ctrlTrack(on, accent, 104, 52), display: 'flex', alignItems: 'center'}}>
                  <span
                    style={{
                      display: 'block',
                      width: 38,
                      height: 38,
                      borderRadius: 999,
                      background: C.paper,
                      border: `2.5px solid ${C.ink}`,
                      boxShadow: THEME.paperShadow(0.35),
                      transform: `translateX(${on ? 52 : 4}px)`,
                      transition: 'none',
                    }}
                  />
                </div>
              ) : null}
              {/* ---- checkbox ---- */}
              {row.kind === 'checkbox' ? (
                <div
                  style={{
                    width: 50,
                    height: 50,
                    boxSizing: 'border-box',
                    borderRadius: 8,
                    background: on ? accent : C.paper,
                    border: `2.5px solid ${C.ink}`,
                    boxShadow: THEME.paperShadow(0.25),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flex: '0 0 auto',
                  }}
                >
                  
                    <Check size={34} color={on ? C.white : 'transparent'} strokeWidth={3.4} />
                  
                </div>
              ) : null}
              {/* ---- radio ---- */}
              {row.kind === 'radio' ? (
                <div style={{display: 'flex', gap: 18}}>
                  {(row.options ?? []).map((opt, k) => {
                    const sel = k === Number(state);
                    return (
                      <div
                        key={k}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 12,
                          background: 'transparent',
                          border: 'none',
                          padding: 0,
                          fontFamily: 'Kai,sans-serif',
                          fontSize: TYPE.bodyM,
                          color: C.ink,
                        }}
                      >
                        <span
                          style={{
                            width: 40,
                            height: 40,
                            borderRadius: 999,
                            background: C.paper,
                            border: `2.5px solid ${sel ? accent : C.ink}`,
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flex: '0 0 auto',
                          }}
                        >
                          <span style={{width: 18, height: 18, borderRadius: 999, background: sel ? accent : 'transparent'}} />
                        </span>
                        <span style={{fontWeight: sel ? 700 : 400}}>{opt}</span>
                      </div>
                    );
                  })}
                </div>
              ) : null}
              {/* ---- segment（分段控件）---- */}
              {row.kind === 'segment' ? (
                <div style={{display: 'flex', gap: 6, padding: 6, background: C.paperWarm, border: `2.5px solid ${C.ink}`, borderRadius: RADIUS}}>
                  {(row.options ?? []).map((opt, k) => {
                    const sel = k === Number(state);
                    return (
                      <div
                        key={k}
                        style={{
                          height: 46,
                          display: 'inline-flex',
                          alignItems: 'center',
                          boxSizing: 'border-box',
                          padding: '0 20px',
                          border: `2px solid ${sel ? C.ink : 'transparent'}`,
                          borderRadius: RADIUS - 4,
                          background: sel ? accent : 'transparent',
                          color: sel ? C.white : C.ink,
                          fontFamily: 'Kai,sans-serif',
                          fontSize: TYPE.bodyM,
                          fontWeight: 700,
                        }}
                      >
                        {opt}
                      </div>
                    );
                  })}
                </div>
              ) : null}
              {/* ---- slider ---- */}
              {row.kind === 'slider' ? (
                <>
                  {(() => {
                    // 纯 div 滑块：轨道 + 已选区间 + 拇指，位置 = (值 - min) / (max - min)，不测量 DOM。
                    const span = Math.max(1e-9, row.max - row.min);
                    const t = Math.max(0, Math.min(1, (Number(state) - row.min) / span));
                    const THUMB = 34;
                    return (
                      <div style={{position: 'relative', width: ctrlW, height: 44, flex: '0 0 auto'}}>
                        <div
                          style={{
                            position: 'absolute', left: 0, right: 0, top: 13, height: 18, boxSizing: 'border-box',
                            borderRadius: 999, background: C.mutedFill, border: `2.5px solid ${C.ink}`, overflow: 'hidden',
                          }}
                        >
                          <div style={{width: `${t * 100}%`, height: '100%', borderRadius: 999, background: accent}} />
                        </div>
                        <span
                          style={{
                            position: 'absolute', top: 5, left: t * (ctrlW - THUMB), width: THUMB, height: THUMB, boxSizing: 'border-box',
                            borderRadius: 999, background: C.paper, border: `3px solid ${C.ink}`, boxShadow: THEME.paperShadow(0.4),
                          }}
                        />
                      </div>
                    );
                  })()}
                  <span style={{fontFamily: 'Space,monospace', fontSize: TYPE.bodyM, fontWeight: 700, color: accent, minWidth: 96, textAlign: 'right'}}>
                    {Number(state).toFixed(2)}
                    {row.unit ?? ''}
                  </span>
                </>
              ) : null}
              {/* ---- progress ---- */}
              {row.kind === 'progress' ? (
                <>
                  <div
                    style={{position: 'relative', width: ctrlW, height: 34, boxSizing: 'border-box', borderRadius: 999, background: C.mutedFill, border: `2.5px solid ${C.ink}`, overflow: 'hidden', flex: '0 0 auto'}}
                  >
                    <div style={{width: `${Math.max(0, Math.min(100, (Number(state) / (row.max ?? 100)) * 100))}%`, height: '100%', background: accent}} />
                  </div>
                  <span style={{fontFamily: 'Space,monospace', fontSize: TYPE.bodyM, fontWeight: 700, color: accent, minWidth: 96, textAlign: 'right'}}>
                    {Math.round(Number(state))}
                    {row.unit ?? '%'}
                  </span>
                </>
              ) : null}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ---------------------------------------------------------------------------
// HighlightCode — Shiki（3.2.0 起替换 react-syntax-highlighter / Prism）
// 语法色来自 ./shiki.ts 里由当前主题调色板生成的 TextMate 主题（flat / cel 各一套）。
// token 是同步算出来的（无 WASM、无 Promise），所以不需要 delayRender。
// 帧驱动逐行聚焦：讲哪一行，哪一行亮起来。
// ---------------------------------------------------------------------------
export const HighlightCode: React.FC<{
  f: number;
  code: string;
  language: string;
  startAt: number;
  lineStep: number;
  height: number;
  width: number;
  title?: string;
  /** 代码字号（设计像素，缺省 TYPE.labelM=21）。成片的代码镜头请给 30–40：代码要大而清晰。 */
  fontSize?: number;
  /** 把高亮钉在某一行（0 起），不再随 lineStep 走；配合引擎 cinema.focus 推近到这一行。 */
  active?: number;
}> = ({f, code, language, startAt, lineStep, height, width, title, fontSize = TYPE.labelM, active}) => {
  const lines = highlightTokens(code, language);
  const lineCount = lines.length;
  const activeLine = active ?? Math.max(0, Math.min(lineCount - 1, Math.floor((f - startAt) / lineStep)));
  return (
    <div style={{width, height, display: 'flex', flexDirection: 'column'}}>
      <div
        style={{
          height: 62,
          background: C.ink,
          borderRadius: `${RADIUS}px ${RADIUS}px 0 0`,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '0 26px',
          flex: '0 0 auto',
        }}
      >
        {[C.orange, C.gold, C.green].map((dot, i) => (
          <span key={i} style={{width: 18, height: 18, borderRadius: 999, background: dot}} />
        ))}
        <span style={{marginLeft: 12, color: C.white, fontFamily: 'Space,monospace', fontSize: TYPE.microS, letterSpacing: 1.2}}>
          {title ?? language.toUpperCase()}
        </span>
      </div>
      <div
        style={{
          flex: 1,
          background: C.paper,
          border: `2.5px solid ${C.ink}`,
          borderTop: 'none',
          borderRadius: `0 0 ${RADIUS}px ${RADIUS}px`,
          boxShadow: THEME.paperShadow(0.9),
          padding: '30px 34px',
          overflow: 'hidden',
        }}
      >
        <pre style={{margin: 0, padding: 0, background: 'none', overflow: 'visible'}}>
          <code style={{display: 'block', fontFamily: 'Space,Consolas,monospace', fontSize, lineHeight: fontSize > 26 ? 1.6 : 1.95, whiteSpace: 'pre', color: C.ink}}>
            {lines.map((tokens, i) => {
              const on = i === activeLine;
              return (
                <span
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'baseline',
                    background: on ? `${C.blue}1f` : 'transparent',
                    borderLeft: `6px solid ${on ? C.blue : 'transparent'}`,
                    paddingLeft: 12,
                    marginLeft: -18,
                  }}
                >
                  <span
                    style={{
                      flex: '0 0 auto',
                      minWidth: '3.4em',
                      paddingRight: '1.5em',
                      textAlign: 'right',
                      color: C.muted,
                      fontFamily: 'Space,monospace',
                      fontSize: Math.max(TYPE.microS, Math.round(fontSize * 0.62)),
                      opacity: 0.8,
                      userSelect: 'none',
                    }}
                  >
                    {i + 1}
                  </span>
                  <span>
                    {tokens.length === 0 || (tokens.length === 1 && tokens[0].content === '') ? ' ' : null}
                    {tokens.map((t, k) => (
                      <span key={k} style={{color: t.color, fontWeight: t.bold ? 700 : undefined, fontStyle: t.italic ? 'italic' : undefined}}>
                        {t.content}
                      </span>
                    ))}
                  </span>
                </span>
              );
            })}
          </code>
        </pre>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// MathBlock — 数学公式（katex）
// 静态渲染、无动画，确定性。技能是讲解视频，公式是常见内容；
// 此前只能手写 HTML 硬排（上下标都难对齐），这个件把它变成一行。
// ---------------------------------------------------------------------------
export const MathBlock: React.FC<{
  f?: number;
  tex: string;
  startAt?: number;
  /** display 模式居中独占一行；inline 模式跟着文字走 */
  display?: boolean;
  fontSize?: number;
  tone?: string;
  align?: 'left' | 'center';
}> = ({f = 0, tex, startAt = 0, display = true, fontSize = 40, tone, align = 'center'}) => {
  const html = katex.renderToString(tex, {throwOnError: false, displayMode: display});
  const p = f ? prog(f, startAt, 24) : 1;
  return (
    <div
      style={{
        opacity: p,
        transform: `translateY(${(1 - p) * 14}px)`,
        fontSize,
        color: tone ?? C.ink,
        textAlign: align,
        lineHeight: 1.5,
      }}
      dangerouslySetInnerHTML={{__html: html}}
    />
  );
};

// ---------------------------------------------------------------------------
// Icon / IconWall — lucide-react（ISC，线条）+ simple-icons（CC0，品牌）
//
// 3.2.0 起替换 react-icons（fa / fi / lu 三族）：
//   · 线条图标直接用 lucide-react（以前的 fi / lu 本来就是 Feather / Lucide 的再打包）；
//   · 品牌 logo 用 simple-icons 的单色 path（CC0，无署名义务；商标规则仍适用），
//     替换掉 Font Awesome 品牌（CC BY 4.0，需署名）。
// **LineIcon（kit.tsx）也改成了 lucide 字形**，两处同一套笔画语法。
// 笔画重量：lucide 是 24 视窗 / strokeWidth 2；与 LineIcon 的 32 视窗 / 2.2 对齐
//   → 2.2 × 24/32 = 1.65。
// 纪律：图标**只用 THEME 给的 color**，不许用自带的品牌色或多色。
// ---------------------------------------------------------------------------
const ICON_WEIGHT_ALIGN = 1.65;

/** simple-icons 的一个品牌：只取 path 与标题，颜色仍由皮肤决定（不用 si.hex 品牌色）。 */
type BrandIcon = {title: string; path: string};

export const TOPIC_ICONS = {
  // ---- 品牌（simple-icons，实心单色）----
  react: siReact,
  node: siNodedotjs,
  python: siPython,
  docker: siDocker,
  git: siGit,
  npm: siNpm,
  github: siGithub,
  // ---- 线条（lucide-react）----
  branch: GitBranch,
  terminal: Terminal,
  layers: Layers,
  package: Package,
  cpu: Cpu,
  database: Database,
  cloud: Cloud,
  brain: Brain,
  bot: Bot,
  rocket: Rocket,
  sparkles: Sparkles,
  check: CircleCheck,
  bug: Bug,
  ruler: Ruler,
  gauge: Gauge,
  workflow: Workflow,
  milestone: Milestone,
  wrench: Wrench,
  zap: Zap,
  fileCode: FileCode,
  server: Server,
  shield: ShieldCheck,
  trend: ChartLine,
  puzzle: Puzzle,
  idea: Lightbulb,
  flag: Flag,
  refactor: GitBranch,
} as const satisfies Record<string, LucideIcon | BrandIcon>;

export type TopicIconName = keyof typeof TOPIC_ICONS;

export const TOPIC_ICON_TONE: Record<TopicIconName, string> = {
  react: C.blue,
  node: C.green,
  python: C.gold,
  docker: C.blue,
  git: C.orange,
  npm: C.red,
  github: C.ink,
  branch: C.orange,
  terminal: C.ink,
  layers: C.blue,
  package: C.orange,
  cpu: C.green,
  database: C.gold,
  cloud: C.blue,
  brain: C.orange,
  bot: C.green,
  rocket: C.red,
  sparkles: C.gold,
  check: C.green,
  bug: C.red,
  ruler: C.blue,
  gauge: C.green,
  workflow: C.blue,
  milestone: C.orange,
  wrench: C.ink,
  zap: C.gold,
  fileCode: C.blue,
  server: C.orange,
  shield: C.green,
  trend: C.blue,
  puzzle: C.gold,
  idea: C.gold,
  flag: C.red,
  refactor: C.orange,
};

/** 单个题材图标：字形来自 lucide-react / simple-icons，颜色/尺寸仍由皮肤决定。 */
export const TopicIcon: React.FC<{name: TopicIconName; size?: number; color?: string; strokeWidth?: number}> = ({
  name,
  size = 64,
  color,
  strokeWidth = ICON_WEIGHT_ALIGN,
}) => {
  const Glyph = TOPIC_ICONS[name] as LucideIcon | BrandIcon | undefined;
  // 名字不在表里时当场把合法名单报出来（否则 React 只会抛一句 minified #130）。
  if (!Glyph) {
    throw new Error(
      `[TopicIcon] 没有名为 "${String(name)}" 的图标。合法名字（${Object.keys(TOPIC_ICONS).length} 个）：` +
        Object.keys(TOPIC_ICONS).join(', ')
    );
  }
  const tone = color ?? TOPIC_ICON_TONE[name];
  if (typeof Glyph === 'object' && 'path' in Glyph) {
    // 品牌 logo 是实心剪影，24 视窗；按 0.84 缩一档，让视觉面积与线条图标相当。
    const s = size * 0.84;
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" role="img" aria-label={Glyph.title}>
        <g transform={`translate(${(24 - 24 * (s / size)) / 2} ${(24 - 24 * (s / size)) / 2}) scale(${s / size})`}>
          <path d={Glyph.path} fill={tone} />
        </g>
      </svg>
    );
  }
  const Line = Glyph as LucideIcon;
  return <Line size={size} color={tone} strokeWidth={strokeWidth} />;
};

/** 图标墙：弹簧错峰入场。等距排列，供「技术栈/依赖」类场景使用。 */
export const IconWall: React.FC<{
  f: number;
  names: TopicIconName[];
  startAt: number;
  step: number;
  columns?: number;
  tile?: number;
  gap?: number;
  showLabel?: boolean;
}> = ({f, names, startAt, step, columns = 7, tile = 196, gap = 22, showLabel = true}) => {
  return (
    <div style={{display: 'grid', gridTemplateColumns: `repeat(${columns}, ${tile}px)`, gap}}>
      {names.map((name, i) => {
        const delay = startAt + i * step;
        const s = spring({frame: f - delay, fps: 30, config: {damping: 14, stiffness: 110}});
        const p = Math.max(0, Math.min(1, s));
        const shown = f >= delay;
        return (
          <div
            key={name}
            style={{
              width: tile,
              height: tile,
              opacity: shown ? Math.min(1, p * 1.6) : 0,
              transform: `scale(${0.6 + p * 0.4})`,
              background: C.paper,
              border: `2.5px solid ${C.ink}`,
              borderRadius: RADIUS,
              boxShadow: THEME.paperShadow(0.6),
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 14,
            }}
          >
            <TopicIcon name={name} size={tile * 0.34} />
            {showLabel ? (
              <span style={{fontFamily: 'Space,Kai,monospace', fontSize: TYPE.microS, color: C.muted, letterSpacing: 0.6}}>{name}</span>
            ) : null}
          </div>
        );
      })}
    </div>
  );
};
