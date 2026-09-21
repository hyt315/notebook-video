import React from 'react';
import {THEME} from '../theme/active';
import {prog} from './ui';

// ============================================================================
// focus.tsx — 注意力三件：把"其余压暗"这件事变成一件可复用的动作
//
// 替换掉什么：此前我们只会**往画面上加**——GlowFrame 整块发亮、ShimmerText 一句发光、
// Callout 圈一处、StampSeal 盖一下。全是"加东西强调"。而讲解视频里最有效的一手恰恰相反：
// **把不是重点的部分压下去**（focusing / 视觉钝化）。缺的从来不是"更亮的边框"，是"暗下去的背景"。
//
// 四种模式（闭合集，一镜只用一种）：
//   dim     四块压暗遮罩盖住目标之外的一切（暗色 + multiply，是真的往下压）—— 缩略图/网格/表格首选
//   spot    目标上留一个亮斑，外围暗 —— 灯打在证据上
//   loupe   圆形放大镜：把 children 的某块区域放大显示（数字/小字/细节）
//   marker  目标外一圈手绘感描边，随时间画出（不依赖 roughjs，纯帧驱动的圆角矩形笔画）
//
// 纪律：只读 THEME；显隐/进度都是 f(帧号) 的纯函数；不用 CSS transition；
// 不改 children 的布局（dim/spot/marker 都是绝对定位覆盖层，pointer-events 关掉）。
// ============================================================================

const C = THEME.palette;

export type FocusMode = 'dim' | 'spot' | 'loupe' | 'marker';

export type FocusRect = {x: number; y: number; w: number; h: number};

const clamp01 = (v: number) => (v < 0 ? 0 : v > 1 ? 1 : v);

/** 入场曲线：ease-out（本件自带，不依赖 ui.prog 的线性——新层统一缓动是另一件待办）。
 *  实测依据：线性入场在 t=50% 时比 ease-out 落后 180px（探针 Probe-prog-ease 渲出来的数字）。 */
const easeOut3 = (v: number) => 1 - Math.pow(1 - clamp01(v), 3);

/**
 * 遮罩浓度。
 *
 * 2026-09-21 修（三个原因叠加，全部有单帧实测数字，探针见交付报告）：
 *   ① **颜色是纸色** —— 原来是 `background: C.paperBase`，而纸色底上的纸色遮罩
 *      等于没画：亮底 249.2 → 247.4（Δ-1.9），中灰块 128 → **214（反而提亮了 86）**。
 *      "把其余压暗"这句话一个字都没画出来。改成 `muted` + `multiply`：亮底 → 146.8、
 *      中灰 128 → 76.1，是真的往下压；`muted` 四套皮肤都有，比写死一个灰更稳。
 *   ② **不是覆盖层** —— 原来没有 z-index，只有 `position:absolute`，于是"写在内容前面"
 *      就被内容盖住（DOM 顺序从来不是契约）。见 SCENE_ANCHOR 的 zIndex。
 *   ③ **坐标随宿主漂移** —— 注释写"rect 是场景坐标"，实现却按最近的定位祖先算：
 *      放进 `left:200,top:300` 的包裹层，蒙版整体偏出画布左边与上边（左缘 60px 处
 *      实测 247.3 = 完全没被盖到），"洞"也落在别处。见 SCENE_ANCHOR 的 position。
 */
const VEIL = 0.72;
const VEIL_COLOR_KEY = 'muted' as const;
const VEIL_BLEND: React.CSSProperties['mixBlendMode'] = 'multiply';

/**
 * SCENE_ANCHOR —— 本件所有覆盖层（遮罩四条、spot 框、label、marker 描边、loupe 镜片）
 * 共用的锚点。两个属性各自解决一个真实的坑，别只改一处：
 *
 *   · `position: 'fixed'`：设计根（index.tsx 的 `data-design-root`）带
 *     `transform: scale(...)`，而 transform 会让该元素成为 fixed 后代的**包含块**——
 *     于是 left/top/width/height 一律按**场景坐标**解释，无论外面套了几层定位容器。
 *     这正是注释里承诺的"rect 是场景坐标"。前提：必须挂在设计根内部（整片都满足）。
 *   · `zIndex: 160` —— 把遮罩钉在**场景内容与全局 chrome 之上、屏幕空间层之下**。
 *     整片的层级梯子（改这个值前先数一遍它）：场景内容 ≤130（含 130 的镜头交接层）
 *     → 页眉 140 / 章节卡 150 → **本遮罩 160** → Grade 190（颗粒与暗角）
 *     → SubtitleChrome 200（四套皮肤一致）。
 *     ⚠️ 2026-09-21 修：这里原先是 9000，于是遮罩盖过字幕 —— S8 的字幕被 `multiply`
 *     同一档（实测同一帧的字形核心 25.1 → 15.1 = 墨色 × 0.594，而周围背景不动）。
 *     **z-index 压过 DOM 顺序**：旧注释写"Grade/Subtitle 排在场景之后，所以字幕不会被压暗"，
 *     那条理由在设了 z-index 之后**根本不成立**（这次事故的根子就是注释与实现不符）。
 *     取 160 之后：压暗照旧盖住场景内容与 chrome（"其余"确实暗下去），
 *     而 Grade / 字幕回到遮罩之上 —— 与"字幕是屏幕空间、不属于'其余'"的本意一致。
 */
const SCENE_ANCHOR: React.CSSProperties = {position: 'fixed', zIndex: 160};

/**
 * 四块（或四边）遮罩：把 rect 之外盖住。用四条而不是"整块 + 挖洞"，
 * 是因为 clip-path/evenodd 在不同浏览器与 Remotion 的截图路径上表现不一致——实测踩过。
 */
const Veil: React.FC<{rect: FocusRect; canvas: {w: number; h: number}; p: number; round?: number}> =
({rect, canvas, p, round = 0}) => {
  const a = VEIL * p;
  const style: React.CSSProperties = {
    ...SCENE_ANCHOR,
    background: C[VEIL_COLOR_KEY],
    mixBlendMode: VEIL_BLEND,
    opacity: a,
    pointerEvents: 'none',
  };
  const x0 = Math.max(0, rect.x), y0 = Math.max(0, rect.y);
  const x1 = Math.min(canvas.w, rect.x + rect.w), y1 = Math.min(canvas.h, rect.y + rect.h);
  return (
    <>
      <div style={{...style, left: 0, top: 0, width: canvas.w, height: y0}} />
      <div style={{...style, left: 0, top: y1, width: canvas.w, height: Math.max(0, canvas.h - y1)}} />
      <div style={{...style, left: 0, top: y0, width: x0, height: Math.max(0, y1 - y0), borderRadius: round}} />
      <div style={{...style, left: x1, top: y0, width: Math.max(0, canvas.w - x1), height: Math.max(0, y1 - y0), borderRadius: round}} />
    </>
  );
};

/**
 * FocusFx — 一镜一次的"注意力动作"。`rect` 是**场景坐标**（与其它组件同一坐标系）。
 *
 * 用法：
 *   <FocusFx f={f} mode="dim" startAt={40} dur={18} rect={{x:200,y:300,w:900,h:420}} canvas={{w:1920,h:1080}}/>
 *   <FocusFx f={f} mode="loupe" rect={...} zoom={2.1} canvas={{w:1920,h:1080}}>{场景内容}</FocusFx>
 *
 * 退出：给 exitStart 就会在之后 18 帧内收回（其余组件都支持离场，这里不例外）。
 */
export const FocusFx: React.FC<{
  f: number;
  mode?: FocusMode;
  /** 要留住的那块（场景坐标） */
  rect: FocusRect;
  /** 画布尺寸，用来铺满遮罩 */
  canvas: {w: number; h: number};
  /** 入场起始帧（本镜局部帧） */
  startAt?: number;
  dur?: number;
  /** 离场起始帧；给了就在 18 帧内收回 */
  exitStart?: number;
  /** loupe 的倍率 */
  zoom?: number;
  /** marker 的描边色 */
  tone?: string;
  /** 可选：在目标旁挂一句话 */
  label?: string;
  children?: React.ReactNode;
}> = ({f, mode = 'dim', rect, canvas, startAt = 0, dur = 18, exitStart, zoom = 2.1, tone, label, children}) => {
  const pin = easeOut3(prog(f, startAt, dur));                       // 入场（ease-out）
  const pout = exitStart === undefined ? 0 : clamp01(prog(f, exitStart, 18));
  const p = Math.max(0, pin - pout);                                 // 收回时反向
  if (p <= 0) return <>{mode === 'loupe' ? children : null}</>;
  const accent = tone ?? C.orange;

  if (mode === 'dim' || mode === 'spot') {
    return (
      <>
        <Veil rect={rect} canvas={canvas} p={p} round={mode === 'spot' ? 999 : 6} />
        {mode === 'spot' ? (
          <div
            style={{
              ...SCENE_ANCHOR, left: rect.x, top: rect.y, width: rect.w, height: rect.h,
              border: `3px solid ${accent}`, borderRadius: 12, opacity: p, pointerEvents: 'none',
              boxShadow: `0 0 0 6px ${C.paperBase}00`,
            }}
          />
        ) : null}
        {label ? (
          <div style={{...SCENE_ANCHOR, left: rect.x, top: Math.max(0, rect.y - 44), fontSize: 24, color: accent, opacity: p, fontWeight: 700}}>
            {label}
          </div>
        ) : null}
      </>
    );
  }

  if (mode === 'marker') {
    // 手绘感：一圈圆角描边按周长"画出来"，用 dash 偏移做（纯帧驱动，无随机）
    const per = 2 * (rect.w + rect.h) + 8 * 18;   // 近似周长（含圆角）
    return (
      <>
        <svg width={canvas.w} height={canvas.h} style={{...SCENE_ANCHOR, left: 0, top: 0, pointerEvents: 'none'}}>
          <rect
            x={rect.x} y={rect.y} width={rect.w} height={rect.h} rx={16}
            fill="none" stroke={accent} strokeWidth={6} strokeLinecap="round"
            strokeDasharray={per} strokeDashoffset={per * (1 - p)}
            transform={`rotate(${-0.5} ${rect.x + rect.w / 2} ${rect.y + rect.h / 2})`}
          />
        </svg>
        {label ? (
          <div style={{...SCENE_ANCHOR, left: rect.x, top: Math.max(0, rect.y - 44), fontSize: 24, color: accent, opacity: p, fontWeight: 700}}>
            {label}
          </div>
        ) : null}
      </>
    );
  }

  // loupe：圆形放大镜——把 children 放大后按圆裁切，钉在 rect 中心
  const r = Math.min(rect.w, rect.h) / 2;
  const cx = rect.x + rect.w / 2, cy = rect.y + rect.h / 2;
  const rp = r * (0.6 + 0.4 * p);                                   // 镜片从小长到全尺寸
  return (
    <>
      {children}
      <div
        style={{
          ...SCENE_ANCHOR, left: cx - rp, top: cy - rp, width: rp * 2, height: rp * 2,
          borderRadius: 999, overflow: 'hidden', border: `5px solid ${accent}`,
          opacity: Math.min(1, p * 1.2), pointerEvents: 'none',
          boxShadow: THEME.paperShadow(0.9),
        }}
      >
        <div
          style={{
            position: 'absolute', left: -rect.x * zoom + (rp * 2) / 2 - (rect.w * zoom) / 2 + (rp * 2) / 2 - rp,
            top: -rect.y * zoom + (rp * 2) / 2 - (rect.h * zoom) / 2 + (rp * 2) / 2 - rp,
            width: canvas.w * zoom, height: canvas.h * zoom, transform: `scale(1)`, transformOrigin: '0 0',
          }}
        >
          <div style={{width: canvas.w, height: canvas.h, transform: `scale(${zoom})`, transformOrigin: '0 0', position: 'absolute', left: 0, top: 0}}>
            {children}
          </div>
        </div>
      </div>
    </>
  );
};

export const FOCUS_MODES: FocusMode[] = ['dim', 'spot', 'loupe', 'marker'];
