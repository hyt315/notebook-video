import {THEME} from './theme/active';
import React from 'react';
import {Easing, interpolate, spring} from 'remotion';
import {camAt, STAGE, TEXT_ZOOM_MAX} from './shotkit';
import {FX_ENABLED, FX_FALLBACK, CURL_FRAMES} from './fx';

// ============================================================================
// cinema.tsx · 引擎级虚拟摄影机
//
// 为什么有这一层：早期版本每一镜都是「静止舞台 + 卡片依次出现」，即使 ShotCamera 推了 3%，
// 观众感受仍是翻 PPT。本层在**引擎**里（index.tsx 的 FinalDemo / Backdrop）给每一镜套一台
// 虚拟摄影机，分镜表什么都不写也有：
//   0. fit     内容自动放大：anchor 占安全区（内容带）不足 60% 时，整镜按 anchor 中心推近到 72%
//              （resolve-shots 预算成 cinema.fit，validate-shot-motion 复核 60–80%）；
//   1. drift   缓推/漂移：每镜 3–5% 的慢推或横移，镜与镜之间自动换方向（不会全片同一种推）；
//   2. focus   焦点跟随：分镜表 `cinema.focus` 声明「第几拍看哪里」，摄影机用弹簧曲线推近取景该区域，
//              拍结束后拉回；区域可写矩形，也可写 region 简写（left/right/top/bottom/center…）；
//   3. pan     宽画布横摇：`cinema.pan.worldW` > 1920 时，场景按更宽的世界排版，摄影机横摇扫过；
//   4. 转场     whip（甩镜：方向模糊 + 位移）/ zoom（推穿：放大淡出 + 新镜从远处推来）/ fade / hard；
//              缺省 auto：章节首镜 zoom，其余 whip，左右交替；
//              3.5.0 pageturn / peel：真卷页（src/fx.tsx，WebGPU），渲染器探针不通过时自动退回 slide / drop；
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
export type FocusKey = {at: number; hold: number; zoom?: number; rect: Rect; settle?: boolean; /** false = 不做「不切字」滑动，注视点固定在矩形中心 */ slide?: boolean; /** 推近时也必须完整入画的矩形（例如旁边的大数字）；引擎降低推近倍数（不低于 focusMinZoom）装下「焦点 ∪ keep」 */ keep?: Rect};
/** resolve-shots 预算好的基准取景（内容自动放大）：注视点 + 缩放；fill = anchor 占内容带面积比。 */
export type FitSpec = {x: number; y: number; s: number; fill?: number; fillAfter?: number};
export type CinemaSpec = {
  drift?: 'auto' | 'none' | number;
  fit?: FitSpec;
  focus?: readonly FocusKey[];
  pan?: {worldW: number; at: number; dur: number; dir?: 'ltr' | 'rtl'} | null;
  /** compose-story 预算的相机路径（关键词推近 / 视线连续 / 限速）。有它就不用 fit/drift/focus。 */
  path?: readonly PathKey[];
};
export type PathKey = {at: number; x: number; y: number; s: number};
export type TransitionKind = 'whip' | 'whip-left' | 'whip-right' | 'zoom' | 'fade' | 'hard' | 'slide' | 'drop' | 'pageturn' | 'peel';

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
  fitMin: 0.6, // 内容自动放大：anchor 占内容带面积 < 60% 才放大
  fitTarget: 0.72, // 放大到 72%（60–80% 区间中段）
  maskTop: 178, // 推近时世界层顶部遮罩的实心起点（设计 y）；页眉 / 章节卡底边约 164
  maskCut: 160, // 门禁口径：y < maskCut 视作已被遮罩隐去
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

/** 焦点推近时焦点矩形到画面边缘的最小屏幕边距（px，设计坐标）。 */
export const FOCUS_PAD = 28;

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

/** fw = 焦点推近权重（0 = 无焦点，1 = 完全推近）；引擎据此给世界层加顶部羽化遮罩、给门禁打 data-cinema-focus。 */
export type CamState = {x: number; y: number; s: number; tx: number; fw?: number};

/**
 * 引擎摄影机在本镜本地帧 f 的状态（设计坐标、作用在场景 ShotCamera **之外**）。
 * sceneKeys：场景自己的 ShotCamera 关键帧（用于把总缩放钳在 TEXT_ZOOM_MAX 以内、把焦点矩形映射到屏幕）。
 */
export const cinemaCamAt = (spec: CinemaSpec | undefined, f: number, duration: number, idx: number, sceneKeys?: readonly any[], zoomMax = TEXT_ZOOM_MAX): CamState => {
  const sp = spec ?? {};
  if (sp.path && sp.path.length) return pathCamAt(sp.path, f, duration, sceneKeys, zoomMax);
  const sc = sceneKeys && sceneKeys.length ? camAt(sceneKeys as any, f) : {x: STAGE.cx, y: STAGE.cy, s: 1, rotY: 0};
  const capS = Math.max(1, zoomMax / Math.max(1, sc.s)); // 引擎缩放上限（与场景缩放相乘后 ≤ zoomMax）
  // ---- 0. fit（基准取景）+ 1. drift（围绕基准取景慢推/横移）----
  const fit = sp.fit ?? {x: STAGE.cx, y: STAGE.cy, s: 1};
  const amt = sp.drift === 'none' ? 0 : typeof sp.drift === 'number' ? Math.max(0, Math.min(0.08, sp.drift)) : CINEMA.driftAmt;
  const pat = driftPattern(idx);
  const t = smooth(f, 0, Math.max(30, duration));
  const ds = pat.pull ? 1 + amt * (1 - t) : 1 + amt * t;
  const s0 = Math.max(1, Math.min(capS, fit.s * ds));
  const look0 = clampLook(fit.x + (pat.dx * CINEMA.driftPanPx * (t - 0.5) * 2) / Math.max(1, fit.s), fit.y, s0);
  let x = look0.x, y = look0.y, s = s0;
  let fw = 0;
  // ---- 2. focus（弹簧推近、缓拉回；多个焦点首尾相接时直接从一个移到下一个）----
  for (const k of sp.focus ?? []) {
    const end = k.at + k.hold;
    if (f < k.at - 1 || f > end + CINEMA.focusOut + 1) continue;
    const pin = spring({frame: f - k.at, fps: 30, config: {damping: 20, stiffness: 120, mass: 0.9}, durationInFrames: CINEMA.focusIn});
    const pout = smooth(f, end, end + CINEMA.focusOut);
    const w = Math.max(0, Math.min(1, pin) * (1 - pout));
    if (w <= 0) continue;
    fw = Math.max(fw, w);
    // 焦点矩形（场景设计坐标）→ 经场景 ShotCamera 映射到屏幕坐标
    const r = k.rect;
    const mx = (px: number) => STAGE.cx - sc.x * sc.s + px * sc.s;
    const my = (py: number) => STAGE.cy - sc.y * sc.s + py * sc.s;
    const rw = r.w * sc.s, rh = r.h * sc.s;
    const fit = CINEMA.focusFill * Math.min(STAGE.w / rw, STAGE.h / rh);
    let fs = Math.min(capS, Math.max(CINEMA.focusMinZoom, k.zoom ?? fit), Math.min(STAGE.w / rw, STAGE.h / rh));
    // 3.2.0 keep：「焦点 ∪ keep」留 FOCUS_PAD 边距能装下所需的倍数 ≥ focusMinZoom 时，用它（只降不升）并以并集为取景范围；否则忽略 keep。
    let ux0 = mx(r.x), ux1 = mx(r.x) + rw, uy0 = my(r.y), uy1 = my(r.y) + rh, useKeep = false;
    if (k.keep) {
      const kx0 = Math.min(ux0, mx(k.keep.x)), kx1 = Math.max(ux1, mx(k.keep.x + k.keep.w));
      const ky0 = Math.min(uy0, my(k.keep.y)), ky1 = Math.max(uy1, my(k.keep.y + k.keep.h));
      const need = Math.min((STAGE.w - 2 * FOCUS_PAD) / (kx1 - kx0), (STAGE.h - 2 * FOCUS_PAD) / (ky1 - ky0));
      if (need >= CINEMA.focusMinZoom) { fs = Math.min(fs, need); ux0 = kx0; ux1 = kx1; uy0 = ky0; uy1 = ky1; useKeep = true; }
    }
    // 3.2.0 自动修（不切字）：焦点矩形留 FOCUS_PAD 屏幕边距完整入画的前提下，注视点横向尽量滑回基准取景中心，
    // 让非焦点内容（例如左侧大标题）少被推出画面；矩形比取景窗还宽时退回矩形中心。`slide: false` 关掉。
    const slide = (lo: number, hi: number, half: number, base: number) => {
      const a = hi - half + FOCUS_PAD / fs, b = lo + half - FOCUS_PAD / fs;
      return a <= b ? Math.min(b, Math.max(a, base)) : (lo + hi) / 2;
    };
    const rx0 = mx(r.x), ry0 = my(r.y);
    const fl = k.slide === false
      ? clampLook(rx0 + rw / 2, ry0 + rh / 2, fs)
      : useKeep
        ? clampLook(slide(ux0, ux1, STAGE.cx / fs, look0.x), slide(uy0, uy1, STAGE.cy / fs, ry0 + rh / 2), fs)
        : clampLook(slide(rx0, rx0 + rw, STAGE.cx / fs, look0.x), ry0 + rh / 2, fs); // 只横向滑：纵向下滑会把顶部标题推进页眉遮罩（实测演示片 S5）
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
  return {x: c.x, y: c.y, s, tx, fw: sp.pan && tx > 0 ? Math.max(fw, 1) : fw};
};

/**
 * 3.2.0 路径摄影机：在 compose-story 预算的关键帧之间用 easeIO 插值（速度上限已在预算时保证），
 * 叠加一层**永不停止的微漂移**（缩放 ±0.5%、位移 ±5px，周期 4–5 秒）+ 全镜 1.5% 慢推：
 * 推近后不会冻结，任何静止段都不超过 1 秒。fw（遮罩权重）随推近倍数上升。
 */
export const pathCamAt = (path: readonly PathKey[], f: number, duration: number, sceneKeys?: readonly any[], zoomMax = TEXT_ZOOM_MAX): CamState => {
  const sc = sceneKeys && sceneKeys.length ? camAt(sceneKeys as any, f) : {s: 1};
  const capS = Math.max(1, zoomMax / Math.max(1, sc.s));
  let k = path[0];
  let x = k.x, y = k.y, s = k.s;
  for (let i = 0; i < path.length; i++) {
    const a = path[i], b = path[i + 1];
    if (!b) { x = a.x; y = a.y; s = a.s; break; }
    if (f <= a.at) { x = a.x; y = a.y; s = a.s; break; }
    if (f < b.at) {
      const t = smooth(f, a.at, b.at);
      x = a.x + (b.x - a.x) * t; y = a.y + (b.y - a.y) * t; s = a.s + (b.s - a.s) * t;
      break;
    }
  }
  const push = 1 + 0.015 * Math.min(1, Math.max(0, f / Math.max(30, duration)));
  const ms = 1 + 0.005 * Math.sin((f / 140) * Math.PI * 2);
  const ss = Math.min(capS, Math.max(1, s * push * ms));
  const dx = 5 * Math.sin((f / 150) * Math.PI * 2 + 0.7) / ss, dy = 3.5 * Math.cos((f / 125) * Math.PI * 2) / ss;
  const c = clampLook(x + dx, y + dy, ss);
  return {x: c.x, y: c.y, s: ss, tx: 0, fw: Math.max(0, Math.min(1, (ss - 1.02) / 0.04))};
};

/**
 * 推近时的顶部羽化遮罩：焦点推近会把非焦点内容推到页眉 / 章节卡底下（实测 S3 卡片标题被页眉压住）。
 * 世界层在 y < CINEMA.maskTop 处按 fw 渐隐（羽化 38px），chrome 下方永远干净；不推近时（fw=0）完全不生效。
 * 门禁（OverlapGate）对带 data-cinema-focus 的世界层，只量 y ≥ maskCut 的可见部分（与遮罩同口径）。
 */
export const cinemaMask = (fw: number): string | undefined => {
  if (!fw || fw < 0.01) return undefined;
  const a = (1 - Math.min(1, fw)).toFixed(3);
  return `linear-gradient(to bottom, rgba(0,0,0,${a}) 0px, rgba(0,0,0,${a}) ${CINEMA.maskTop - 38}px, #000 ${CINEMA.maskTop}px, #000 100%)`;
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
export const resolveTransition = (declared: string | undefined, idx: number, isChapter: boolean, fx: boolean = FX_ENABLED): TransitionKind | null => {
  if (idx === 0) return null;
  const d = declared ?? 'auto';
  if (d === 'hard') return 'hard';
  if (d === 'fade' || d === 'zoom' || d === 'whip-left' || d === 'whip-right' || d === 'slide' || d === 'drop') return d;
  // 3.5.0：真卷页。渲染器没开 fx（浏览器没有 WebGPU / HTML-in-canvas）→ 退回 slide / drop，片子照样出。
  if (d === 'pageturn' || d === 'peel') return fx ? d : FX_FALLBACK[d];
  if (d === 'whip') return idx % 2 ? 'whip-left' : 'whip-right';
  // 3.3.0：手作皮肤的媒介内转场（纸在本子上横移 = 一张长卷上的横移镜头；新纸放下来 = drop）。
  // 皮肤声明了 craft.transition 时，auto 用它；章节首镜一律 drop（换一张纸）。
  // 3.5.0：手账 / 档案缺省 pageturn（翻到下一页），剪纸缺省 peel（从底板上揭起）；无 fx 时同上退回。
  const craft = THEME.craft?.transition;
  if (craft === 'pageturn' || craft === 'peel') return isChapter ? 'drop' : fx ? craft : FX_FALLBACK[craft];
  if (craft === 'slide' || craft === 'drop') return isChapter ? 'drop' : craft;
  if (isChapter) return 'zoom';
  return idx % 2 ? 'whip-left' : 'whip-right';
};

export type TransStyle = {transform: string; opacity: number; blur: number};

/** 转场时长（帧）：卷页 CURL_FRAMES，其余 CINEMA.transition。 */
export const transitionFrames = (kind: TransitionKind | null): number => (kind === 'pageturn' || kind === 'peel' ? CURL_FRAMES : CINEMA.transition);

/**
 * 转场样式：p ∈ [0,1] 为转场进度（镜头边界后 CINEMA.transition 帧）。
 * role = 'out'（上一镜末帧）或 'in'（本镜）。blur 是水平方向模糊量（交给 WhipBlur 滤镜）。
 */
export const transitionStyle = (kind: TransitionKind, p: number, role: 'in' | 'out'): TransStyle => {
  const e = easeIO(Math.max(0, Math.min(1, p)));
  if (kind === 'hard') return role === 'out' ? {transform: 'none', opacity: 0, blur: 0} : {transform: 'none', opacity: 1, blur: 0};
  if (kind === 'fade') return role === 'out' ? {transform: 'none', opacity: 1 - e, blur: 0} : {transform: 'none', opacity: 1, blur: 0};
  // pageturn / peel：两层都不动，卷页由 index.tsx 的 PageCurl（WebGPU）画在上一镜那一层上。
  if (kind === 'pageturn' || kind === 'peel') return {transform: 'none', opacity: 1, blur: 0};
  // slide：上一镜与本镜像同一张长纸上的两段，一起向左横移（镜头沿纸面平移，不模糊、不淡出）。
  if (kind === 'slide') return role === 'out' ? {transform: `translateX(${-1500 * e}px)`, opacity: 1, blur: 0} : {transform: `translateX(${1500 * (1 - e)}px)`, opacity: 1, blur: 0};
  // drop：一张新纸从上方落下盖住旧纸（旧内容压暗淡出，新内容带一点落定过冲）。
  if (kind === 'drop') {
    if (role === 'out') return {transform: `translateY(${18 * e}px) scale(${1 - 0.02 * e})`, opacity: 1 - Math.min(1, e * 1.25), blur: 0};
    const o = 1 - Math.pow(1 - e, 3);
    return {transform: `translateY(${-70 * (1 - o)}px) scale(${1.025 - 0.025 * o})`, opacity: Math.min(1, e * 2.2), blur: 0};
  }
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

/**
 * KineticNumber · 关键数字的动态排版（计数 + 落定缩放弹出 + 强调下划线扫入）。
 * 用在「讲到这个数」的那一拍：at = 该拍本地帧。全部是帧的纯函数。
 *   <KineticNumber f={f} at={at(1)} to={5} suffix="×" size={260} color={C.orange} label="更快" />
 * from→to 计数 dur 帧（缺省 30），落定瞬间放大 1.18 回弹；数字用等宽数字（tabular-nums）防止计数时抖宽。
 */
export const KineticNumber: React.FC<{
  f: number; at: number; to: number; from?: number; dur?: number; decimals?: number;
  prefix?: string; suffix?: string; size?: number; color?: string; ink?: string; label?: string; labelSize?: number;
  align?: 'left' | 'center' | 'right'; style?: React.CSSProperties;
}> = ({f, at, to, from = 0, dur = 30, decimals = 0, prefix = '', suffix = '', size = 200, color = '#f08a24', ink, label, labelSize, align = 'left', style}) => {
  const enter = spring({frame: f - at, fps: 30, config: {damping: 13, stiffness: 160, mass: 0.7}});
  const o = interpolate(f, [at, at + 6], [0, 1], clamp);
  const land = at + dur;
  const sc = (0.55 + 0.45 * enter) * landPop(f, land, 0.18);
  const bar = interpolate(f, [land - 2, land + 12], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const origin = align === 'center' ? '50% 70%' : align === 'right' ? '100% 70%' : '0% 70%';
  return (
    <div style={{display: 'inline-flex', flexDirection: 'column', alignItems: align === 'center' ? 'center' : align === 'right' ? 'flex-end' : 'flex-start', opacity: o, ...style}}>
      <div style={{position: 'relative', transform: `scale(${sc.toFixed(4)})`, transformOrigin: origin, lineHeight: 0.92, whiteSpace: 'nowrap'}}>
        <span style={{fontFamily: 'Clash,Space,Kai', fontWeight: 700, fontSize: size, color, fontVariantNumeric: 'tabular-nums', letterSpacing: -size * 0.02}}>
          {prefix}{countUp(f, at, to, {from, dur, decimals})}
        </span>
        {suffix && <span style={{fontFamily: 'Clash,Space,Kai', fontWeight: 700, fontSize: size * 0.5, color, marginLeft: size * 0.04}}>{suffix}</span>}
        <div style={{position: 'absolute', left: 0, bottom: -size * 0.06, height: Math.max(6, size * 0.045), width: `${(bar * 100).toFixed(2)}%`, background: color, borderRadius: 99, opacity: 0.85}} />
      </div>
      {label && <div style={{marginTop: size * 0.14, fontSize: labelSize ?? Math.max(30, size * 0.2), fontWeight: 700, color: ink ?? color, opacity: interpolate(f, [land - 6, land + 8], [0, 1], clamp)}}>{label}</div>}
    </div>
  );
};

export const CINEMA_VERSION = 'cinema-v1 · fit · drift · focus · world-pan · whip/zoom/pageturn transitions · parallax · kinetic numbers';
