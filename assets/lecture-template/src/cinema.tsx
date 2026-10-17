import React from 'react';
import {Easing, interpolate, spring} from 'remotion';
import {camAt, STAGE, TEXT_ZOOM_MAX} from './shotkit';

// ============================================================================
// cinema.tsx · 引擎级虚拟摄影机（v4.4）
//
// 为什么有这一层：v4.3 之前每一镜都是「静止舞台 + 卡片依次出现」，即使 ShotCamera 推了 3%，
// 观众感受仍是翻 PPT。本层在**引擎**里（index.tsx 的 FinalDemo / Backdrop）给每一镜套一台
// 虚拟摄影机，分镜表什么都不写也有：
//   1. drift   缓推/漂移：每镜 3–5% 的慢推或横移，镜与镜之间自动换方向（不会全片同一种推）；
//   2. focus   焦点跟随：分镜表 `cinema.focus` 声明「第几拍看哪里」，摄影机用弹簧曲线推近取景该区域，
//              拍结束后拉回；区域可写矩形，也可写 region 简写（left/right/top/bottom/center…）；
//   3. pan     宽画布横摇：`cinema.pan.worldW` > 1920 时，场景按更宽的世界排版，摄影机横摇扫过；
//   4. 转场     whip（甩镜：方向模糊 + 位移）/ zoom（推穿：放大淡出 + 新镜从远处推来）/ fade / hard；
//              缺省 auto：章节首镜 zoom，其余 whip，左右交替；
//   5. 视差     Backdrop 按 0.3 的系数跟随摄影机（背景比内容动得少 → 纵深）。
//
// 纪律：全部是**帧的纯函数**（interpolate / spring / Easing），无随机、无状态、无实时动画库；
// 同一帧渲两次结果相同。缩放受 TEXT_ZOOM_MAX 钳制（与场景自己的 ShotCamera 相乘后计算），
// 取景窗永远落在 1920×1080 舞台（或 pan 世界）之内 → 内容不会被推出画面、不会露出画布外。
// 数学与 scripts/validate-shot-motion.py 的 cinema 段同式。
// ============================================================================

export type Rect = {x: number; y: number; w: number; h: number};
export type FocusRegion = 'left' | 'right' | 'top' | 'bottom' | 'center' | 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
/** 已解析的焦点（resolve-shots 把 beat 换成本镜本地帧 at）。 */
export type FocusKey = {at: number; hold: number; zoom?: number; rect: Rect};
export type CinemaSpec = {
  drift?: 'auto' | 'none' | number;
  focus?: readonly FocusKey[];
  pan?: {worldW: number; at: number; dur: number; dir?: 'ltr' | 'rtl'} | null;
};
export type TransitionKind = 'whip' | 'whip-left' | 'whip-right' | 'zoom' | 'fade' | 'hard';

/** 默认值：观感调好的常数，普通作者不需要改。 */
export const CINEMA = {
  driftAmt: 0.045, // 每镜慢推 4.5%
  driftPanPx: 22, // 横移漂移幅度（设计像素）
  focusFill: 0.72, // 焦点区域占可见窗的比例
  focusMinZoom: 1.1, // 推近至少 10%，否则观众感觉不到
  focusIn: 20, // 推近时长（帧）
  focusOut: 24, // 拉回时长（帧）
  focusHold: 60, // 缺省停留（帧）
  transition: 14, // 转场时长（帧）
  parallax: 0.3, // 背景跟随系数
  bgOverscan: 1.06, // 背景预放大，给视差留出不露边的余量
} as const;

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const easeIO = Easing.bezier(0.45, 0, 0.2, 1); // 起步柔、收尾长 —— 「运动模糊」式的缓动
const smooth = (f: number, a: number, b: number) => interpolate(f, [a, Math.max(a + 1, b)], [0, 1], {...clamp, easing: easeIO});

/** 内容带（与模板 contentBand 缺省一致）→ region 简写对应的矩形。 */
export const regionRect = (r: FocusRegion, band: Rect = {x: 160, y: 130, w: 1600, h: 760}): Rect => {
  const {x, y, w, h} = band;
  const hw = w / 2, hh = h / 2;
  switch (r) {
    case 'left': return {x, y, w: hw, h};
    case 'right': return {x: x + hw, y, w: hw, h};
    case 'top': return {x, y, w, h: hh};
    case 'bottom': return {x, y: y + hh, w, h: hh};
    case 'top-left': return {x, y, w: hw, h: hh};
    case 'top-right': return {x: x + hw, y, w: hw, h: hh};
    case 'bottom-left': return {x, y: y + hh, w: hw, h: hh};
    case 'bottom-right': return {x: x + hw, y: y + hh, w: hw, h: hh};
    default: return {x: x + w * 0.2, y: y + h * 0.15, w: w * 0.6, h: h * 0.7};
  }
};

/** 取景窗钳制：缩放 s 时注视点只能在 [lo+half, hi-half] 内（世界宽 worldW）。 */
const clampLook = (x: number, y: number, s: number, worldW = STAGE.w) => {
  const hx = STAGE.cx / s, hy = STAGE.cy / s;
  return {x: Math.min(worldW - hx, Math.max(hx, x)), y: Math.min(STAGE.h - hy, Math.max(hy, y))};
};

/** 每镜的漂移方向（按镜序轮换）：0 正推 1 右移推 2 拉 3 左移推。 */
const driftPattern = (idx: number) => [
  {s0: 1, s1: 1, dx: 0},
  {s0: 1, s1: 1, dx: 1},
  {s0: 1, s1: 1, dx: 0, pull: true},
  {s0: 1, s1: 1, dx: -1},
][idx % 4];

export type CamState = {x: number; y: number; s: number; tx: number};

/**
 * 引擎摄影机在本镜本地帧 f 的状态（设计坐标、作用在场景 ShotCamera **之外**）。
 * sceneKeys：场景自己的 ShotCamera 关键帧（用于把总缩放钳在 TEXT_ZOOM_MAX 以内、把焦点矩形映射到屏幕）。
 */
export const cinemaCamAt = (spec: CinemaSpec | undefined, f: number, duration: number, idx: number, sceneKeys?: readonly any[], zoomMax = TEXT_ZOOM_MAX): CamState => {
  const sp = spec ?? {};
  const sc = sceneKeys && sceneKeys.length ? camAt(sceneKeys as any, f) : {x: STAGE.cx, y: STAGE.cy, s: 1, rotY: 0};
  const capS = Math.max(1, zoomMax / Math.max(1, sc.s)); // 引擎缩放上限（与场景缩放相乘后 ≤ zoomMax）
  // ---- 1. drift ----
  const amt = sp.drift === 'none' ? 0 : typeof sp.drift === 'number' ? Math.max(0, Math.min(0.08, sp.drift)) : CINEMA.driftAmt;
  const pat = driftPattern(idx);
  const t = smooth(f, 0, Math.max(30, duration));
  const ds = pat.pull ? 1 + amt * (1 - t) : 1 + amt * t;
  const s0 = Math.min(capS, ds);
  const look0 = clampLook(STAGE.cx + pat.dx * CINEMA.driftPanPx * (t - 0.5) * 2, STAGE.cy, s0);
  let x = look0.x, y = look0.y, s = s0;
  // ---- 2. focus（弹簧推近、缓拉回；多个焦点首尾相接时直接从一个移到下一个）----
  for (const k of sp.focus ?? []) {
    const end = k.at + k.hold;
    if (f < k.at - 1 || f > end + CINEMA.focusOut + 1) continue;
    const pin = spring({frame: f - k.at, fps: 30, config: {damping: 20, stiffness: 120, mass: 0.9}, durationInFrames: CINEMA.focusIn});
    const pout = smooth(f, end, end + CINEMA.focusOut);
    const w = Math.max(0, Math.min(1, pin) * (1 - pout));
    if (w <= 0) continue;
    // 焦点矩形（场景设计坐标）→ 经场景 ShotCamera 映射到屏幕坐标
    const r = k.rect;
    const mx = (px: number) => STAGE.cx - sc.x * sc.s + px * sc.s;
    const my = (py: number) => STAGE.cy - sc.y * sc.s + py * sc.s;
    const rw = r.w * sc.s, rh = r.h * sc.s;
    const fit = CINEMA.focusFill * Math.min(STAGE.w / rw, STAGE.h / rh);
    const fs = Math.min(capS, Math.max(CINEMA.focusMinZoom, k.zoom ?? fit), Math.min(STAGE.w / rw, STAGE.h / rh));
    const fl = clampLook(mx(r.x) + rw / 2, my(r.y) + rh / 2, fs);
    x = x + (fl.x - x) * w;
    y = y + (fl.y - y) * w;
    s = s + (fs - s) * w;
  }
  // ---- 3. 宽画布横摇（world pan）----
  let tx = 0;
  if (sp.pan && sp.pan.worldW > STAGE.w) {
    const p = smooth(f, sp.pan.at, sp.pan.at + sp.pan.dur);
    const span = sp.pan.worldW - STAGE.w;
    tx = (sp.pan.dir === 'rtl' ? 1 - p : p) * span;
  }
  const c = clampLook(x, y, s);
  return {x: c.x, y: c.y, s, tx};
};

/** 摄影机变换（注视点 → 画面中心）。tx = 宽画布横摇偏移。 */
export const cinemaTransform = (c: CamState) => `translate(${STAGE.cx - c.x * c.s}px,${STAGE.cy - c.y * c.s}px) scale(${c.s}) translateX(${-c.tx}px)`;

/** 背景视差变换：系数 CINEMA.parallax，预放大 bgOverscan，保证不露边。 */
export const parallaxTransform = (c: CamState, whipX = 0) => {
  const k = CINEMA.parallax;
  const s = CINEMA.bgOverscan * (1 + (c.s - 1) * k);
  const room = (STAGE.w * (s - 1)) / 2;
  const dx = Math.max(-room, Math.min(room, -(c.x - STAGE.cx) * k * c.s - c.tx * 0.12 + whipX * 0.18));
  const roomY = (STAGE.h * (s - 1)) / 2;
  const dy = Math.max(-roomY, Math.min(roomY, -(c.y - STAGE.cy) * k * c.s));
  return `translate(${dx}px,${dy}px) scale(${s})`;
};

/** 自动转场：首镜无；章节首镜 zoom；其余 whip，左右交替。显式写的照用（cut/reveal 视作 auto，hard = 硬切）。 */
export const resolveTransition = (declared: string | undefined, idx: number, isChapter: boolean): TransitionKind | null => {
  if (idx === 0) return null;
  const d = declared ?? 'auto';
  if (d === 'hard') return 'hard';
  if (d === 'fade' || d === 'zoom' || d === 'whip-left' || d === 'whip-right') return d;
  if (d === 'whip') return idx % 2 ? 'whip-left' : 'whip-right';
  if (isChapter) return 'zoom';
  return idx % 2 ? 'whip-left' : 'whip-right';
};

export type TransStyle = {transform: string; opacity: number; blur: number};

/**
 * 转场样式：p ∈ [0,1] 为转场进度（镜头边界后 CINEMA.transition 帧）。
 * role = 'out'（上一镜末帧）或 'in'（本镜）。blur 是水平方向模糊量（交给 WhipBlur 滤镜）。
 */
export const transitionStyle = (kind: TransitionKind, p: number, role: 'in' | 'out'): TransStyle => {
  const e = easeIO(Math.max(0, Math.min(1, p)));
  if (kind === 'hard') return role === 'out' ? {transform: 'none', opacity: 0, blur: 0} : {transform: 'none', opacity: 1, blur: 0};
  if (kind === 'fade') return role === 'out' ? {transform: 'none', opacity: 1 - e, blur: 0} : {transform: 'none', opacity: 1, blur: 0};
  if (kind === 'zoom') {
    if (role === 'out') return {transform: `scale(${1 + 0.55 * e})`, opacity: 1 - Math.min(1, e * 1.6), blur: 14 * Math.sin(Math.PI * Math.min(1, e))};
    return {transform: `scale(${0.82 + 0.18 * e})`, opacity: Math.min(1, e * 1.8), blur: 10 * (1 - e)};
  }
  const dir = kind === 'whip-left' ? -1 : 1; // 内容向左甩出（-1）或向右
  const blurBell = Math.sin(Math.PI * Math.min(1, e));
  if (role === 'out') return {transform: `translateX(${dir * 1100 * e}px)`, opacity: 1 - Math.min(1, e * 1.4), blur: 60 * blurBell};
  return {transform: `translateX(${-dir * 900 * (1 - e)}px)`, opacity: Math.min(1, 0.15 + e * 1.4), blur: 60 * (1 - e) * blurBell + 18 * (1 - e)};
};

/** 方向模糊滤镜（SVG feGaussianBlur，只在 X 方向）。id 唯一，按帧给 stdDeviation。 */
export const WhipBlur: React.FC<{id: string; amount: number}> = ({id, amount}) => (
  <svg width={0} height={0} style={{position: 'absolute'}} aria-hidden>
    <filter id={id} x="-20%" y="-5%" width="140%" height="110%" colorInterpolationFilters="sRGB">
      <feGaussianBlur stdDeviation={`${Math.max(0, amount).toFixed(2)} 0`} />
    </filter>
  </svg>
);

/** 一个转场里摄影机的「甩」位移（给背景视差用）。 */
export const whipOffset = (kind: TransitionKind | null, p: number) => {
  if (!kind || p >= 1 || (kind !== 'whip-left' && kind !== 'whip-right')) return 0;
  const dir = kind === 'whip-left' ? -1 : 1;
  return -dir * 900 * (1 - easeIO(Math.max(0, Math.min(1, p))));
};

// ---------------------------------------------------------------------------
// 运动助手（场景与组件可直接用；全部是帧的纯函数）
// ---------------------------------------------------------------------------

/** 带回弹的入场（stagger 由调用方给 at）：返回 {opacity, transform}。 */
export const popIn = (f: number, at: number, opts: {from?: 'up' | 'down' | 'left' | 'right' | 'scale'; dist?: number; overshoot?: boolean} = {}): React.CSSProperties => {
  const sp = spring({frame: f - at, fps: 30, config: opts.overshoot === false ? {damping: 22, stiffness: 140} : {damping: 11, stiffness: 150, mass: 0.8}});
  const o = interpolate(f, [at, at + 8], [0, 1], clamp);
  const d = opts.dist ?? 40;
  const inv = 1 - sp;
  const tr = opts.from === 'left' ? `translateX(${-d * inv}px)` : opts.from === 'right' ? `translateX(${d * inv}px)` : opts.from === 'down' ? `translateY(${-d * inv}px)` : opts.from === 'scale' ? '' : `translateY(${d * inv}px)`;
  const sc = opts.from === 'scale' ? 0.6 + 0.4 * sp : 0.94 + 0.06 * sp;
  return {opacity: o, transform: `${tr} scale(${sc})`};
};

/** 空闲微动：极小的正弦漂浮（px），让「动完就静止」的元素保持呼吸。phase 用于错开。 */
export const idleFloat = (f: number, phase = 0, amp = 3, period = 120): string =>
  `translateY(${(amp * Math.sin(((f + phase * 37) / period) * Math.PI * 2)).toFixed(2)}px)`;

/** 计数数字：从 from 数到 to（ease-out），返回格式化字符串。 */
export const countUp = (f: number, at: number, to: number, opts: {from?: number; dur?: number; decimals?: number} = {}): string => {
  const p = interpolate(f, [at, at + (opts.dur ?? 34)], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const v = (opts.from ?? 0) + (to - (opts.from ?? 0)) * p;
  return v.toFixed(opts.decimals ?? 0);
};

/** 数字落定时的放大弹跳（kinetic typography）：返回 scale。 */
export const landPop = (f: number, landAt: number, amp = 0.18): number => {
  if (f < landAt) return 1;
  const sp = spring({frame: f - landAt, fps: 30, config: {damping: 8, stiffness: 220, mass: 0.6}});
  return 1 + amp * Math.sin(Math.PI * Math.min(1, sp)) * Math.max(0, 1 - (f - landAt) / 18);
};

/** 描线进度（连接线/箭头绘入）：0→1，配合 strokeDasharray/strokeDashoffset。 */
export const drawOn = (f: number, at: number, dur = 18) => interpolate(f, [at, at + dur], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});

export const CINEMA_VERSION = 'cinema-v1 · drift · focus · world-pan · whip/zoom transitions · parallax';
