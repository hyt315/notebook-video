import React from 'react';
import * as RadixDialog from '@radix-ui/react-dialog';
import * as RadixPopover from '@radix-ui/react-popover';
import * as RadixTooltip from '@radix-ui/react-tooltip';
import * as RadixDropdownMenu from '@radix-ui/react-dropdown-menu';
import {THEME} from '../theme/active';
import {TYPE} from '../kit';
import {prog} from './ui';
import {fitsWithin} from './fittext';

// ============================================================================
// overlay.tsx — 拟真弹层（Radix 的 dialog / popover / tooltip / dropdown-menu）
//
// 替换掉什么：此前所有「界面感」都压在 `ConsoleWindow` 一个件上——要表达
// 「弹出一个确认框」「下拉里选一项」「气泡说明」只能画静态线框。
// 这四件正是软件类讲解的高频语法，而 Radix 给的是**结构+状态机**，外观仍归我们。
//
// ⚠️ 本轮实测（diag-upgrade 页①）得到的两条硬结论：
//   1. Portal 默认落 `document.body` —— 那是 Remotion 画布**之外**。
//      必须 `container={本组件自己的宿主节点}`。实测指到画面根后四件全部完整可见，
//      Dialog 的测量矩形与给定坐标逐像素一致（x=480 y=130 w=420 h=134）。
//   2. Popover / Tooltip / DropdownMenu 走的是 floating-ui，**落位是异步的**
//      （computePosition 在微任务里才 resolve；实测要 8 轮渲染才稳定在目标位）。
//      所以本层不用它的「自动避让」，而是**把锚点钉在我们给的坐标上**
//      （`Anchor` 就是一个 0×0 的定位点 + `side/align/sideOffset` 固定），
//      落点因此是 f(帧号) 的确定值，而不是测量出来的。同一帧渲两次哈希一致（已实测）。
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
  /** 用哪种 Radix primitive（默认由 kind 推出） */
  children?: React.ReactNode;
}> = ({f, kind = 'dialog', x, y, width, steps, title, body, items, selected, confirm, cancel, tone, pointer, children}) => {
  const [host, setHost] = React.useState<HTMLDivElement | null>(null);
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

  // 引线三角已并入 Box（见上），这里不再单独渲染
  const hostStyle: React.CSSProperties = {position: 'absolute', left: 0, top: 0, width: '100%', height: '100%'};

  return (
    <div ref={setHost as never} style={hostStyle}>
      {kind === 'dialog' ? (
        <RadixDialog.Root open={open} modal={false}>
          <RadixDialog.Portal container={host}>
            {/* Dialog 不走 floating：坐标由我们给，落点逐像素确定 */}
            <RadixDialog.Content style={{position: 'absolute', left: x, top: y, outline: 'none'}} aria-describedby={undefined}>
              {/* Title 只给读屏用：**必须视觉隐藏**，否则它会占掉文档流的一行，
                  把弹层整体往下推（实测第一版就是这样，标题跑到了盒子外面）。
                  这里用手写的 visually-hidden，免得为了一行样式再加一个 Radix 包。 */}
              <RadixDialog.Title
                style={{position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap', margin: 0}}
              >
                {title ?? '弹窗'}
              </RadixDialog.Title>
              {inner}
            </RadixDialog.Content>
          </RadixDialog.Portal>
        </RadixDialog.Root>
      ) : null}
      {kind === 'popover' ? (
        <RadixPopover.Root open={open}>
          <RadixPopover.Anchor asChild>
            {/* 锚点就是坐标本身：0×0，钉死在 (x,y) */}
            <div style={{position: 'absolute', left: x, top: y, width: 0, height: 0}} />
          </RadixPopover.Anchor>
          <RadixPopover.Portal container={host}>
            <RadixPopover.Content side="bottom" align="start" sideOffset={pointer ? 2 : 12} style={{outline: 'none'}}>
              {inner}
            </RadixPopover.Content>
          </RadixPopover.Portal>
        </RadixPopover.Root>
      ) : null}
      {kind === 'menu' ? (
        <RadixDropdownMenu.Root open={open} modal={false}>
          <RadixDropdownMenu.Trigger asChild>
            <div style={{position: 'absolute', left: x, top: y, width: 0, height: 0}} />
          </RadixDropdownMenu.Trigger>
          <RadixDropdownMenu.Portal container={host}>
            <RadixDropdownMenu.Content align="start" side="bottom" sideOffset={pointer ? 2 : 12} style={{outline: 'none'}}>
              {inner}
            </RadixDropdownMenu.Content>
          </RadixDropdownMenu.Portal>
        </RadixDropdownMenu.Root>
      ) : null}
      {kind === 'tooltip' ? (
        <RadixTooltip.Provider delayDuration={0} skipDelayDuration={0} disableHoverableContent>
          <RadixTooltip.Root open={open}>
            <RadixTooltip.Trigger asChild>
              <div style={{position: 'absolute', left: x, top: y, width: 0, height: 0}} />
            </RadixTooltip.Trigger>
            <RadixTooltip.Portal container={host}>
              <RadixTooltip.Content side="bottom" align="start" sideOffset={pointer ? 2 : 12} style={{outline: 'none'}}>
                {inner}
              </RadixTooltip.Content>
            </RadixTooltip.Portal>
          </RadixTooltip.Root>
        </RadixTooltip.Provider>
      ) : null}
    </div>
  );
};
