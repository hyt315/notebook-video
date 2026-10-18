import React from 'react';
import {THEME} from '../theme/active';
import {TYPE} from '../kit';
import {prog} from './ui';
import {fitsWithin} from './fittext';

// ============================================================================
// overlay.tsx — 拟真弹层（dialog / popover / tooltip / menu）
//
// 3.2.0（Phase 3）：去掉 Radix（dialog / popover / tooltip / dropdown-menu 四个包）。
// 以前的实测结论正是去掉它的理由：
//   1. Portal 默认落到 document.body（画布之外），必须手动把 container 指回画面；
//   2. popover / tooltip / menu 走 floating-ui，落位是**异步**测量出来的
//      （实测要 8 轮渲染才稳定）——我们本来就把锚点钉死在给定坐标上，
//      所以那层测量只剩风险、没有收益。
// 现在弹层就是父容器里一个绝对定位的 <div>：dialog 的左上角 = (x, y)；
// popover / tooltip / menu 的左上角 = (x, y + 间距)，与原来 side="bottom" align="start" 的落点一致。
// 落点是 f(帧号) 的确定值，不测量、不 Portal、不异步。
//
// 纪律：只读 THEME；显隐与入场都是 f(帧号) 的纯函数；不用 CSS transition。
// ============================================================================

const C = THEME.palette;
const RADIUS = THEME.aesthetic.paperRadius;

export type OverlayKind = 'dialog' | 'popover' | 'tooltip' | 'menu';

/**
 * overlayOpenAt — 弹层的显隐也是「显式的表」：给一串 [帧号, 开关] 即可。
 * 返回当前帧的状态与前一次切换的进度（用于入场动画）。
 */
export const overlayStateAt = (steps: {at: number; open: boolean}[], f: number) => {
  const sorted = steps.slice().sort((a, b) => a.at - b.at);
  let cur = sorted[0]?.open ?? false;
  let lastAt = sorted[0]?.at ?? 0;
  for (const s of sorted) {
    if (s.at <= f) {
      cur = s.open;
      lastAt = s.at;
    }
  }
  return {open: cur, since: lastAt};
};

const Box: React.FC<{
  width: number;
  kind: OverlayKind;
  title?: string;
  tone: string;
  p: number;
  children?: React.ReactNode;
  footer?: string;
  pointer?: {dx: number; dy: number; side: 'top' | 'bottom' | 'left' | 'right'};
}> = ({width, kind, title, tone, p, children, footer, pointer}) => (
  <div
    style={{
      width,
      position: 'relative',
      opacity: p,
      transform: `translateY(${(1 - p) * -18}px) scale(${0.94 + 0.06 * p})`,
      transformOrigin: 'top left',
      background: C.paper,
      border: `2.5px solid ${C.ink}`,
      borderRadius: RADIUS,
      boxShadow: THEME.paperShadow(0.95),
    }}
  >
    {/* 引线三角：作为盒子的子节点，锚在盒子边缘（永远跟着盒子走，不跟着坐标走） */}
    {pointer ? (
      <span
        style={{
          position: 'absolute',
          left: pointer.side === 'left' ? -12 : pointer.side === 'right' ? width - 16 : pointer.dx - 14,
          top: pointer.side === 'top' ? -14 : pointer.side === 'bottom' ? undefined : pointer.dy - 14,
          bottom: pointer.side === 'bottom' ? -14 : undefined,
          width: 28,
          height: 28,
          background: C.paper,
          borderRight: `2.5px solid ${C.ink}`,
          borderBottom: `2.5px solid ${C.ink}`,
          transform: `rotate(${pointer.side === 'top' ? 45 : pointer.side === 'bottom' ? 225 : pointer.side === 'left' ? 315 : 135}deg)`,
          zIndex: 3,
        }}
      />
    ) : null}
    {kind === 'dialog' ? (
      <div style={{height: 54, background: C.ink, display: 'flex', alignItems: 'center', gap: 10, padding: '0 20px'}}>
        {[C.orange, C.gold, C.green].map((dot, i) => (
          <span key={i} style={{width: 15, height: 15, borderRadius: 999, background: dot}} />
        ))}
        <span style={{marginLeft: 10, color: C.white, fontFamily: 'Space,monospace', fontSize: TYPE.microS, letterSpacing: 1.1}}>
          {title ?? 'CONFIRM'}
        </span>
      </div>
    ) : title ? (
      <div style={{borderBottom: `2px dashed ${C.line}`, padding: '14px 20px', fontFamily: 'Kai,sans-serif', fontSize: TYPE.bodyM, fontWeight: 700, color: tone}}>
        {title}
      </div>
    ) : null}
    <div style={{padding: '18px 20px'}}>{children}</div>
    {footer ? (
      <div style={{borderTop: `2px dashed ${C.line}`, padding: '12px 20px', fontFamily: 'Space,Kai,monospace', fontSize: TYPE.microS, color: C.muted}}>
        {footer}
      </div>
    ) : null}
  </div>
);

/**
 * OverlayFrame — 一个弹层：显隐与内容都由帧号决定。
 *
 * 用法（父容器需要 position:relative；本件自己铺满父容器）：
 *   <OverlayFrame f={f} kind="dialog" x={520} y={240} width={620}
 *     steps={[{at:20,open:true},{at:96,open:false}]}
 *     title="确认升级" body="把 model 改成 v4.1-flash？" tone={C.orange}
 *     confirm="确定" cancel="取消" />
 */
export const OverlayFrame: React.FC<{
  f: number;
  kind?: OverlayKind;
  /** 弹层左上角（相对父容器） */
  x: number;
  y: number;
  width: number;
  steps: {at: number; open: boolean}[];
  title?: string;
  body?: string;
  /** menu 型：选项列表（`on` 是静态选中，配合 `selected` 用不到） */
  items?: {text: string; on?: boolean}[];
  /**
   * menu 型：**帧 → 选中项下标**的显式表（与 ControlStack 的 steps 同一套写法）。
   * 单选语义：最后一个 at ≤ f 的 value 生效——不是"累积高亮"。
   * 给了它就以它为准，用来表达"下拉里选了一项"。
   */
  selected?: {at: number; value: number}[];
  /** dialog 型的两个按钮 */
  confirm?: string;
  cancel?: string;
  tone?: string;
  /** 引线三角指向的点（相对弹层左上角） */
  pointer?: {dx: number; dy: number; side: 'top' | 'bottom' | 'left' | 'right'};
  /** 自定义弹层内容（给了就替代 body / items） */
  children?: React.ReactNode;
}> = ({f, kind = 'dialog', x, y, width, steps, title, body, items, selected, confirm, cancel, tone, pointer, children}) => {
  const {open, since} = overlayStateAt(steps, f);
  const p = open ? prog(f, since, 18) : 0;
  const accent = tone ?? C.blue;
  let choiceIdx = -1;
  if (selected) for (const s of selected) if (s.at <= f) choiceIdx = s.value;

  if (process.env.NODE_ENV !== 'production') {
    if (body) fitsWithin({text: body, boxWidth: width - 48, fontSize: TYPE.bodyS, label: 'OverlayFrame body'});
    if (title) fitsWithin({text: title, boxWidth: width - 48, fontSize: TYPE.bodyM, fontWeight: 700, label: 'OverlayFrame title'});
  }

  const inner = (
    <Box width={width} kind={kind} title={title} tone={accent} p={p} footer={kind === 'dialog' || kind === 'menu' ? 'Esc 关闭 · 点外面也可关闭' : undefined} pointer={pointer}>
      {children ??
        (items ? (
          <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
            {items.map((it, i) => {
              const on = selected ? i === choiceIdx : it.on === true;
              return (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '10px 14px',
                    borderRadius: 8,
                    background: on ? `${accent}26` : 'transparent',
                    border: `2px solid ${on ? accent : 'transparent'}`,
                    fontFamily: 'Kai,sans-serif',
                    fontSize: TYPE.bodyM,
                    color: C.ink,
                    fontWeight: on ? 700 : 400,
                  }}
                >
                  <span style={{width: 12, height: 12, borderRadius: 999, background: on ? accent : C.mutedFill, border: `1.5px solid ${C.ink}`, flex: '0 0 auto'}} />
                  {it.text}
                </div>
              );
            })}
          </div>
        ) : (
          <>
            {body ? <div style={{fontFamily: 'Kai,sans-serif', fontSize: TYPE.bodyS, lineHeight: 1.7, color: C.ink}}>{body}</div> : null}
            {confirm || cancel ? (
              <div style={{display: 'flex', gap: 14, justifyContent: 'flex-end', marginTop: 20}}>
                {cancel ? (
                  <span style={{padding: '10px 26px', borderRadius: RADIUS - 4, border: `2.5px solid ${C.ink}`, background: C.paperWarm, fontFamily: 'Kai,sans-serif', fontSize: TYPE.bodyM, color: C.ink}}>
                    {cancel}
                  </span>
                ) : null}
                {confirm ? (
                  <span style={{padding: '10px 26px', borderRadius: RADIUS - 4, border: `2.5px solid ${C.ink}`, background: accent, fontFamily: 'Kai,sans-serif', fontSize: TYPE.bodyM, fontWeight: 700, color: C.white}}>
                    {confirm}
                  </span>
                ) : null}
              </div>
            ) : null}
          </>
        ))}
    </Box>
  );

  // 引线三角已并入 Box。弹层直接画在父容器里（父容器需要 position:relative）。
  if (!open && p === 0) return <div style={{position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', pointerEvents: 'none'}} />;
  const gap = kind === 'dialog' ? 0 : pointer ? 2 : 12;
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', pointerEvents: 'none'}}>
      <div role={kind === 'dialog' ? 'dialog' : kind === 'tooltip' ? 'tooltip' : kind === 'menu' ? 'menu' : 'group'} aria-label={title} style={{position: 'absolute', left: x, top: y + gap}}>
        {inner}
      </div>
    </div>
  );
};
