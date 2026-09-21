import React from 'react';
import * as RadixAccordion from '@radix-ui/react-accordion';
import * as RadixTabs from '@radix-ui/react-tabs';
import * as RadixSwitch from '@radix-ui/react-switch';
import * as RadixCheckbox from '@radix-ui/react-checkbox';
import * as RadixRadioGroup from '@radix-ui/react-radio-group';
import * as RadixSlider from '@radix-ui/react-slider';
import * as RadixToggleGroup from '@radix-ui/react-toggle-group';
import * as RadixProgress from '@radix-ui/react-progress';
// 2026-09-21：改用 **PrismLight + 按需注册语言**。原来用 `Prism` 全量入口，
// 把 180+ 种语言的词法定义全打进包；实际只用到 6 种（tsx/ts-js/python/bash/json/diff）。
// 功能不变、包体纯赚（见 dependency-policy §4.5 的"下一轮那一刀"）。
import {PrismLight as SyntaxHighlighter} from 'react-syntax-highlighter';
import langTsx from 'react-syntax-highlighter/dist/esm/languages/prism/tsx';
import langTypescript from 'react-syntax-highlighter/dist/esm/languages/prism/typescript';
import langJsx from 'react-syntax-highlighter/dist/esm/languages/prism/jsx';
import langJavascript from 'react-syntax-highlighter/dist/esm/languages/prism/javascript';
import langPython from 'react-syntax-highlighter/dist/esm/languages/prism/python';
import langBash from 'react-syntax-highlighter/dist/esm/languages/prism/bash';
import langJson from 'react-syntax-highlighter/dist/esm/languages/prism/json';
import langDiff from 'react-syntax-highlighter/dist/esm/languages/prism/diff';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import {FaGithub, FaReact, FaPython, FaNodeJs, FaDocker, FaGitAlt, FaNpm, FaCodeBranch} from 'react-icons/fa';
import {FiTerminal, FiLayers, FiPackage, FiCpu, FiDatabase, FiCloud} from 'react-icons/fi';
import {
  LuBrain, LuRocket, LuSparkles, LuCircleCheck, LuBot, LuBug, LuRuler, LuGauge, LuGitBranch, LuWorkflow,
  LuMilestone, LuWrench, LuZap, LuFileCode, LuServer, LuShieldCheck, LuChartLine, LuPuzzle, LuLightbulb, LuFlag,
} from 'react-icons/lu';
import {interpolate, spring} from 'remotion';
import {THEME} from '../theme/active';
import {TYPE, PillTag} from '../kit';
import {fitH} from '../fxkit';

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

// PrismLight 必须先注册语言，否则整段代码会退化成纯文本（不报错，只是没有高亮）。
// 别名一并注册：场景里写 language="ts" / "js" / "sh" 都是合法的。
const PRISM_LANGUAGES: Record<string, unknown> = {
  tsx: langTsx,
  typescript: langTypescript,
  ts: langTypescript,
  jsx: langJsx,
  javascript: langJavascript,
  js: langJavascript,
  python: langPython,
  py: langPython,
  bash: langBash,
  sh: langBash,
  shell: langBash,
  json: langJson,
  diff: langDiff,
};
for (const [name, def] of Object.entries(PRISM_LANGUAGES)) {
  (SyntaxHighlighter as unknown as {registerLanguage: (n: string, d: unknown) => void}).registerLanguage(name, def);
}

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

/** 帧驱动进度，带夹取。所有入场动画都走这个。 */
export const prog = (f: number, from: number, dur = 22) =>
  interpolate(f - from, [0, dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

// ---------------------------------------------------------------------------
// Accordion — @radix-ui/react-accordion
// 用法：<Accordion f={f} items={[{title, body, tone}]} startAt={18} step={58} />
// 展开项由帧号累积决定；展开高度用 fitH() 算出后动画，不测量 DOM。
// ---------------------------------------------------------------------------
export type AccordionItem = {title: string; body: string; tone?: 'blue' | 'orange' | 'green' | 'gold' | 'red'};

export const Accordion: React.FC<{
  f: number;
  items: AccordionItem[];
  startAt: number;
  step: number;
  width: number;
  rowH?: number;
  bodyRows?: number;
}> = ({f, items, startAt, step, width, rowH = 96, bodyRows = 2}) => {
  const openedCount = Math.max(0, Math.min(items.length, Math.floor((f - startAt) / step) + 1));
  const value = items.slice(0, openedCount).map((_, i) => String(i));
  const bodyH = fitH(
    Array.from({length: bodyRows}, () => ({h: TYPE.bodyS * 1.72, gapAfter: 2})),
    30,
    30
  );

  return (
    <RadixAccordion.Root type="multiple" value={value} style={{display: 'flex', flexDirection: 'column', gap: 22, width}}>
      {items.map((item, i) => {
        const p = prog(f, startAt + i * step);
        const isOpen = i < openedCount;
        const accent = toneOf(item.tone);
        return (
          <RadixAccordion.Item
            key={i}
            value={String(i)}
            style={{
              background: C.paper,
              border: `2.5px solid ${isOpen ? accent : C.ink}`,
              borderRadius: RADIUS,
              boxShadow: THEME.paperShadow(isOpen ? 0.8 : 0.25),
            }}
          >
            <RadixAccordion.Header style={{margin: 0}}>
              <RadixAccordion.Trigger
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 20,
                  width: '100%',
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
                <svg width="30" height="30" viewBox="0 0 30 30" style={{flex: '0 0 auto'}}>
                  <g
                    transform={`rotate(${interpolate(p, [0, 1], [180, 0])} 15 15)`}
                    fill="none"
                    stroke={isOpen ? accent : C.muted}
                    strokeWidth={3.4}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="7,12 15,20 23,12" />
                  </g>
                </svg>
              </RadixAccordion.Trigger>
            </RadixAccordion.Header>
            {/* forceMount：关闭态也留在树上，高度与透明度全按帧驱动 */}
            <RadixAccordion.Content forceMount style={{overflow: 'hidden'}}>
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
            </RadixAccordion.Content>
          </RadixAccordion.Item>
        );
      })}
    </RadixAccordion.Root>
  );
};

// ---------------------------------------------------------------------------
// Tabs — @radix-ui/react-tabs
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
  const accent = toneOf(active.tone);

  return (
    <RadixTabs.Root value={active.key} style={{width, height, display: 'flex', flexDirection: 'column'}}>
      <RadixTabs.List
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
            <RadixTabs.Trigger
              key={t.key}
              value={t.key}
              style={{
                flex: 1,
                height: 78,
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
            </RadixTabs.Trigger>
          );
        })}
      </RadixTabs.List>

      {tabs.map((t) => {
        const on = t.key === active.key;
        const a = toneOf(t.tone);
        return (
          <RadixTabs.Content key={t.key} value={t.key} forceMount style={{display: on ? 'block' : 'none', flex: 1, minHeight: 0}}>
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
          </RadixTabs.Content>
        );
      })}
    </RadixTabs.Root>
  );
};

// ---------------------------------------------------------------------------
// ControlStack — 「控件状态随旁白变化」（Radix 六个纯受控 primitive）
//
// 为什么需要它：技能此前**完全没有**「控件被拨动」这个形态——要讲"这个选项被打开了"
// 只能写一张文字卡片假装。而 validate-composition.py 的硬门禁要求每个讲解场景
// ≥1 个真的随旁白变状态的构件，「配置 / 选项 / 参数」类内容最自然的语法就是控件本身。
//
// 为什么 Radix 这六个是安全的（源码级核实，见调研报告 §2.3(8)）：
//   switch / checkbox / radio-group / slider / toggle-group / progress
//   产物里 **Portal 0 处、timer 0 处、Math.random 0 处** —— 纯受控 DOM 件。
//   状态完全由我们传的 value/checked 决定，在无交互环境里长得和有人点时一模一样。
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
  borderRadius: 999,
  background: on ? tone : C.mutedFill,
  border: `2.5px solid ${C.ink}`,
  boxShadow: THEME.paperShadow(0.25),
  position: 'relative',
  flex: '0 0 auto',
  transition: 'none',
});

const CTRL_CHECK = 'M6 15.5l5.4 5.4L22 9.6';

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
                <RadixSwitch.Root checked={state === true} style={ctrlTrack(on, accent, 104, 52)}>
                  <RadixSwitch.Thumb
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
                </RadixSwitch.Root>
              ) : null}
              {/* ---- checkbox ---- */}
              {row.kind === 'checkbox' ? (
                <RadixCheckbox.Root
                  checked={state === true}
                  style={{
                    width: 50,
                    height: 50,
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
                  <RadixCheckbox.Indicator forceMount>
                    <svg width={34} height={34} viewBox="0 0 28 28">
                      <path d={CTRL_CHECK} fill="none" stroke={on ? C.white : 'transparent'} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </RadixCheckbox.Indicator>
                </RadixCheckbox.Root>
              ) : null}
              {/* ---- radio ---- */}
              {row.kind === 'radio' ? (
                <RadixRadioGroup.Root value={String(state)} style={{display: 'flex', gap: 18}}>
                  {(row.options ?? []).map((opt, k) => {
                    const sel = k === Number(state);
                    return (
                      <RadixRadioGroup.Item
                        key={k}
                        value={String(k)}
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
                      </RadixRadioGroup.Item>
                    );
                  })}
                </RadixRadioGroup.Root>
              ) : null}
              {/* ---- segment（分段控件）---- */}
              {row.kind === 'segment' ? (
                <RadixToggleGroup.Root type="single" value={String(state)} style={{display: 'flex', gap: 6, padding: 6, background: C.paperWarm, border: `2.5px solid ${C.ink}`, borderRadius: RADIUS}}>
                  {(row.options ?? []).map((opt, k) => {
                    const sel = k === Number(state);
                    return (
                      <RadixToggleGroup.Item
                        key={k}
                        value={String(k)}
                        style={{
                          height: 46,
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
                      </RadixToggleGroup.Item>
                    );
                  })}
                </RadixToggleGroup.Root>
              ) : null}
              {/* ---- slider ---- */}
              {row.kind === 'slider' ? (
                <>
                  <RadixSlider.Root
                    value={[Number(state)]}
                    min={row.min}
                    max={row.max}
                    step={row.step ?? 0.01}
                    style={{position: 'relative', display: 'flex', alignItems: 'center', width: ctrlW, height: 44, flex: '0 0 auto'}}
                  >
                    <RadixSlider.Track style={{position: 'relative', flex: 1, height: 18, borderRadius: 999, background: C.mutedFill, border: `2.5px solid ${C.ink}`}}>
                      <RadixSlider.Range style={{position: 'absolute', height: '100%', borderRadius: 999, background: accent}} />
                    </RadixSlider.Track>
                    <RadixSlider.Thumb
                      style={{
                        display: 'block',
                        width: 34,
                        height: 34,
                        borderRadius: 999,
                        background: C.paper,
                        border: `3px solid ${C.ink}`,
                        boxShadow: THEME.paperShadow(0.4),
                      }}
                    />
                  </RadixSlider.Root>
                  <span style={{fontFamily: 'Space,monospace', fontSize: TYPE.bodyM, fontWeight: 700, color: accent, minWidth: 96, textAlign: 'right'}}>
                    {Number(state).toFixed(2)}
                    {row.unit ?? ''}
                  </span>
                </>
              ) : null}
              {/* ---- progress ---- */}
              {row.kind === 'progress' ? (
                <>
                  <RadixProgress.Root
                    value={Number(state)}
                    max={row.max ?? 100}
                    style={{position: 'relative', width: ctrlW, height: 34, borderRadius: 999, background: C.mutedFill, border: `2.5px solid ${C.ink}`, overflow: 'hidden', flex: '0 0 auto'}}
                  >
                    <RadixProgress.Indicator
                      style={{width: `${Math.max(0, Math.min(100, Number(state)))}%`, height: '100%', background: accent, transition: 'none'}}
                    />
                  </RadixProgress.Root>
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
// CodeBlock — react-syntax-highlighter（Prism）
// 皮肤由 THEME 接管：关掉库自带配色，语法色映射到调色板。
// 帧驱动逐行聚焦：讲哪一行，哪一行亮起来。
// ---------------------------------------------------------------------------
const syntaxSkin: Record<string, React.CSSProperties> = {
  'code[class*="language-"]': {
    color: C.ink,
    background: 'none',
    fontFamily: 'Space,Consolas,monospace',
    fontSize: TYPE.labelM,
    lineHeight: 1.95,
    whiteSpace: 'pre',
  },
  'pre[class*="language-"]': {background: 'none', margin: 0, padding: 0, overflow: 'visible'},
  comment: {color: C.muted, fontStyle: 'italic'},
  prolog: {color: C.muted},
  punctuation: {color: C.muted},
  keyword: {color: C.blue, fontWeight: 700},
  'class-name': {color: C.orange, fontWeight: 700},
  function: {color: C.orange},
  string: {color: C.green},
  number: {color: C.orangeDeep},
  boolean: {color: C.orangeDeep},
  operator: {color: C.muted},
  builtin: {color: C.blue},
  'attr-name': {color: C.gold},
  tag: {color: C.blue},
  selector: {color: C.green},
};

export const HighlightCode: React.FC<{
  f: number;
  code: string;
  language: string;
  startAt: number;
  lineStep: number;
  height: number;
  width: number;
  title?: string;
}> = ({f, code, language, startAt, lineStep, height, width, title}) => {
  const lineCount = code.split('\n').length;
  const activeLine = Math.max(0, Math.min(lineCount - 1, Math.floor((f - startAt) / lineStep)));
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
        <SyntaxHighlighter
          language={language}
          style={syntaxSkin as never}
          showLineNumbers
          wrapLines
          lineNumberStyle={{
            minWidth: '3.4em',
            paddingRight: '1.5em',
            color: C.muted,
            fontFamily: 'Space,monospace',
            fontSize: TYPE.microS,
            opacity: 0.8,
          }}
          lineProps={(lineNumber: number) => {
            const on = lineNumber - 1 === activeLine;
            return {
              style: {
                display: 'block',
                background: on ? `${C.blue}1f` : 'transparent',
                borderLeft: `6px solid ${on ? C.blue : 'transparent'}`,
                paddingLeft: 12,
                marginLeft: -18,
                transition: 'none',
              },
            };
          }}
        >
          {code}
        </SyntaxHighlighter>
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
// Icon / IconWall — react-icons（fa 品牌 + fi/lu 线条；见 dependency-policy §7.5）
//
// **LineIcon 仍是主图标语言**（`kit.tsx` 的 26 字形）；这里只做**题材性标识**：
// 品牌 logo、技术栈、单点概念的记号。三族的分工：
//   fa — 品牌实心（React / Python / GitHub …，唯一有品牌 logo 的一族）
//   fi — Feather 线条（287 字形，政策原有的那一套）
//   lu — Lucide 线条（1541 字形，**已实测与 fi 同源同款**：同名图标的 attr 与子节点
//        字节级相同；这次放开它是为了拿到 fi 里没有的 brain / rocket / sparkles /
//        circle-check / bot / milestone 等增量字形，不需要另装 35 MB 的 lucide-react）
//
// 实测发现（见本轮 diag 页④）：fi 与 lu 并排**肉眼无法分辨**，无风格漂移；
// 唯一可测的差异是 LineIcon（32 视窗 / strokeWidth 2.2）与 fi·lu（24 视窗 / 2）
// 的**视觉重量**——同一 size 下后者笔画更粗。所以这里统一压一档：
//   strokeWidth = 2.2 × 24/32 = 1.65，让混排时的笔画重量对齐 LineIcon。
// 纪律：图标**只用 THEME 给的 color**，不许用自带 fill 或多色。
// ---------------------------------------------------------------------------
const ICON_WEIGHT_ALIGN = 1.65;

export const TOPIC_ICONS = {
  react: FaReact,
  node: FaNodeJs,
  python: FaPython,
  docker: FaDocker,
  git: FaGitAlt,
  npm: FaNpm,
  github: FaGithub,
  branch: FaCodeBranch,
  terminal: FiTerminal,
  layers: FiLayers,
  package: FiPackage,
  cpu: FiCpu,
  database: FiDatabase,
  cloud: FiCloud,
  // ---- lu（Lucide）增量字形：fi 里没有，正是这次放开这一族的理由 ----
  brain: LuBrain,
  bot: LuBot,
  rocket: LuRocket,
  sparkles: LuSparkles,
  check: LuCircleCheck,
  bug: LuBug,
  ruler: LuRuler,
  gauge: LuGauge,
  workflow: LuWorkflow,
  milestone: LuMilestone,
  wrench: LuWrench,
  zap: LuZap,
  fileCode: LuFileCode,
  server: LuServer,
  shield: LuShieldCheck,
  trend: LuChartLine,
  puzzle: LuPuzzle,
  idea: LuLightbulb,
  flag: LuFlag,
  refactor: LuGitBranch,
} as const;

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

/** 单个题材图标：字形来自 react-icons，颜色/尺寸仍由皮肤决定。 */
export const TopicIcon: React.FC<{name: TopicIconName; size?: number; color?: string; strokeWidth?: number}> = ({
  name,
  size = 64,
  color,
  strokeWidth = ICON_WEIGHT_ALIGN,
}) => {
  const Glyph = TOPIC_ICONS[name];
  return <Glyph size={size} color={color ?? TOPIC_ICON_TONE[name]} strokeWidth={strokeWidth} />;
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
