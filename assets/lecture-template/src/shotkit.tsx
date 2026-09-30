import React from 'react';
import {Easing, interpolate} from 'remotion';
import {THEME} from './theme/active';
import {CanvasMode, MODES, useCanvas} from './theme/canvas';

// ============================================================================
// shotkit · optional, bounded camera helpers
//
// A still camera is a valid default. Use movement only when it clarifies a
// spatial relation, sequence, comparison, or change of focus. When framing
// changes, `anchor` records the essential region; `safeCheck()` uses the same
// geometry as scripts/validate-shot-motion.py to verify it stays in view.
//
// Camera intent and movement notes describe author choices, not quotas. This
// module keeps technical zoom/pan limits and leaves the decision to move—or to
// hold on a readable frame—to the instructional design.
//
// Chrome / chapter cards / captions remain in screen space outside the camera.
// Without 3D keyframes the camera uses translate+scale.
// ============================================================================

// `still` is an explicit, supported camera intent. It does not count against
// any movement budget; a static frame may be clearest for teaching or reading.
export type ShotIntent = 'still' | 'establish' | 'push-in' | 'pull-back' | 'pan-follow' | 'reveal' | 'micro-orbit';

/** 相机关键帧：f=该 shot 的本地帧；x/y=注视点（设计坐标）；s=缩放。 */
export type CamKey = {f: number; x: number; y: number; s: number; rotY?: number};

/** Optional anchor: essential content that must remain visible when framing changes. */
export type Anchor = {x: number; y: number; w: number; h: number};

/** 相机设计坐标；STAGE remains the backwards-compatible 16:9 default. */
export type StageSpec = {w: number; h: number; cx: number; cy: number};
export const STAGE: StageSpec = {w: 1920, h: 1080, cx: 960, cy: 540};
export const stageFor = (canvas: CanvasMode): StageSpec => {
  const mode = MODES[canvas];
  return {w: mode.designW, h: mode.designH, cx: mode.designW / 2, cy: mode.designH / 2};
};

/** 相机缩放硬上限。含文字的镜头用 TEXT_ZOOM_MAX，纯图形镜头可到 GRAPHIC_ZOOM_MAX。 */
export const TEXT_ZOOM_MAX = 1.35;
export const GRAPHIC_ZOOM_MAX = 1.6;

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

/**
 * Pan safety budget: camera translation moves the full scene, so at s=1.00
 * 任何平移都会把内容推出画面、露出边缘（实测：pan-follow 在 s=1.0 下把左侧站名裁掉）。
 *
 * 几何上，缩放为 s 时可见窗半宽 = 960/s，只要窗口仍落在 1920×1080 舞台内就不会露边，
 * 因此可用的最大平移量为：
 *     maxPanX = 960 * (1 - 1/s)      maxPanY = 540 * (1 - 1/s)
 * A requested pan therefore needs enough zoom to cover the exposed edge
 * (s=1.06 → ±54px; s=1.12 → ±103px).
 * camAt() 会按此钳制；scripts/validate-shot-motion.py 用同一公式检查，
 * 请求量超出预算时记 P1（说明平移会被削减）。
 */
export const panBudget = (s: number, stage: StageSpec = STAGE) => ({
  x: stage.cx * (1 - 1 / Math.max(1, s)),
  y: stage.cy * (1 - 1 / Math.max(1, s)),
});

const clampPan = (x: number, y: number, s: number, stage: StageSpec = STAGE) => {
  const b = panBudget(s, stage);
  return {
    x: Math.min(stage.cx + b.x, Math.max(stage.cx - b.x, x)),
    y: Math.min(stage.cy + b.y, Math.max(stage.cy - b.y, y)),
  };
};
const easeInOut = Easing.inOut(Easing.cubic);

/** Suggested durations for helper-generated camera moves (frames), not a movement quota. */
export const CAM_DUR = {short: 30, std: 38, long: 45} as const;

type IntentOpts = {
  /** 整镜长度（帧） */
  duration: number;
  /** 本镜的静止注视点；缺省用画面中心 */
  x?: number;
  y?: number;
  /** 起止缩放；intent 有默认值 */
  from?: number;
  to?: number;
  /** pan-follow：起始注视点 */
  fromX?: number;
  fromY?: number;
  /** 运镜开始帧（默认 0）与时长 */
  at?: number;
  dur?: number;
  /** micro-orbit：绕 Y 轴角度 */
  rotY?: number;
  /** 目标设计画幅；省略时兼容原16:9坐标。 */
  stage?: StageSpec;
};

/**
 * 把 intent 展开成关键帧序列。纯函数、无随机、无状态。
 * 刻意只暴露少量参数：曲线形状由 intent 决定，调用方改不出「AI 乱写相机」那种曲线。
 */
export const shotCam = (intent: ShotIntent, o: IntentOpts): CamKey[] => {
  const stage = o.stage ?? STAGE;
  const x = o.x ?? stage.cx;
  const y = o.y ?? stage.cy;
  const at = o.at ?? 0;
  const dur = o.dur ?? CAM_DUR.std;
  const end = o.duration;
  const holdEnd = Math.max(at + dur, end);
  // ⚠️ tsc TS2739：这两个原本声明成 `CamKey[]` 却赋了一个关键帧对象 ——
  // 于是 shotCam 返回的是 `[CamKey[], CamKey, CamKey[]]` 这种**嵌套数组**，
  // 不是合法关键帧序列，camAt 读到的是垃圾（渲染不报错，只是运镜不对）。
  const head: CamKey = {f: 0, x: o.fromX ?? x, y: o.fromY ?? y, s: o.from ?? 1};
  const tail: CamKey = {f: end, x, y, s: o.to ?? o.from ?? 1};
  switch (intent) {
    // 章节开场建立空间：先稳定 0.5s 再微推，收在 1.03
    case 'establish':
      return [head, {f: at, x, y, s: o.from ?? 1}, {f: at + dur, x, y, s: o.to ?? 1.03}, {f: holdEnd, x, y, s: o.to ?? 1.03}];
    // 聚焦细节／揭示重点：推近到目标缩放
    case 'push-in':
      return [head, {f: at, x, y, s: o.from ?? 1}, {f: at + dur, x, y, s: o.to ?? 1.12}, {f: holdEnd, x, y, s: o.to ?? 1.12}];
    // 章节收束、拉远：从推近态回到 1.00
    case 'pull-back':
      return [head, {f: at, x, y, s: o.from ?? 1.12}, {f: at + dur, x, y, s: o.to ?? 1}, {f: holdEnd, x, y, s: o.to ?? 1}];
    // 对象沿轨道移动时跟随：从 fromX/fromY 移到 x/y，缩放不变
    case 'pan-follow':
      return [head, {f: at, x: o.fromX ?? x, y: o.fromY ?? y, s: o.from ?? 1}, {f: at + dur, x, y, s: o.to ?? o.from ?? 1}, {f: holdEnd, x, y, s: o.to ?? o.from ?? 1}];
    // 擦除揭示：与转场共用时间线，遮罩跟随镜头推进
    case 'reveal':
      return [head, {f: at, x, y, s: o.from ?? 1}, {f: at + dur, x, y, s: o.to ?? 1.08}, {f: holdEnd, x, y, s: o.to ?? 1.08}];
    // 单体 hero 微环绕：rotY ≤ 6°
    // ⚠️ 已知差异（批7 F6，**只记不改**）：TS 侧末 hold 帧（下面第 4 键）不带 rotY，
    // camAt 取 `k.rotY ?? 0` → 收尾把环绕角摆回 0°；而 resolved 数据侧（scripts/resolve-shots.py
    // 的 expand_cam）第 4 键**保留 rotY**（收尾停在摆到位的角度）。两侧行为不一致，
    // 改哪一侧属行为决策，等用户拍板——拍板前别"顺手对齐"任何一侧。
    case 'micro-orbit':
      return [head, {f: at, x, y, s: o.from ?? 1, rotY: 0}, {f: at + dur, x, y, s: o.to ?? o.from ?? 1, rotY: o.rotY ?? 6}, {f: holdEnd, x, y, s: o.to ?? o.from ?? 1}];
    default:
      return [head, tail];
  }
};

/** Static camera path. Still is valid for any duration and does not require an anchor. */
export const stillCam = (duration: number, x?: number, y?: number, s = 1, stage: StageSpec = STAGE): CamKey[] => {
  const cx = x ?? stage.cx;
  const cy = y ?? stage.cy;
  return [
    {f: 0, x: cx, y: cy, s},
    {f: Math.max(0, duration - 1), x: cx, y: cy, s},
  ];
};

/** 插值求某帧的相机状态。 */
export const camAt = (keys: readonly CamKey[], f: number, stage: StageSpec = STAGE): {x: number; y: number; s: number; rotY: number} => {
  if (keys.length === 0) return {x: stage.cx, y: stage.cy, s: 1, rotY: 0};
  if (keys.length === 1 || f <= keys[0].f) {
    const k = keys[0];
    const c = clampPan(k.x, k.y, k.s, stage);
    return {x: c.x, y: c.y, s: k.s, rotY: k.rotY ?? 0};
  }
  let i = 0;
  while (i < keys.length - 2 && f > keys[i + 1].f) i++;
  const a = keys[i];
  const b = keys[i + 1];
  const p = interpolate(f, [a.f, Math.max(a.f + 1, b.f)], [0, 1], {...clamp, easing: easeInOut});
  const s = a.s + (b.s - a.s) * p;
  const c = clampPan(a.x + (b.x - a.x) * p, a.y + (b.y - a.y) * p, s, stage);
  return {
    x: c.x,
    y: c.y,
    s,
    rotY: (a.rotY ?? 0) + ((b.rotY ?? 0) - (a.rotY ?? 0)) * p,
  };
};

/** 相机变换：注视点 (x,y) 落在画面中心，缩放 s。与旧 CameraRig 公式一致 → 兼容。 */
export const camTransform = (x: number, y: number, s: number, stage: StageSpec = STAGE): string =>
  `translate(${stage.cx - x * s}px,${stage.cy - y * s}px) scale(${s})`;

/** 可见窗（设计坐标）。anchor 必须落在其中。 */
export const visibleWindow = (x: number, y: number, s: number, stage: StageSpec = STAGE) => ({
  left: x - stage.cx / s,
  right: x + stage.cx / s,
  top: y - stage.cy / s,
  bottom: y + stage.cy / s,
});

export type SafeViolation = {f: number; axis: 'x' | 'y'; need: number; got: number};

/**
 * 出界数学证明：逐关键帧检查 anchor 是否完整落在可见窗内。
 * 纯算术、零渲染。脚本 scripts/validate-shot-motion.py 用同一套数学复核 shots.json。
 */
export const safeCheck = (keys: readonly CamKey[], anchor: Anchor, zoomMax: number, stage: StageSpec = STAGE): SafeViolation[] => {
  const bad: SafeViolation[] = [];
  const span = Math.max(...keys.map((k) => k.f), 1);
  const step = Math.max(1, Math.round(span / Math.max(2, Math.ceil(span / 8))));
  for (const k of keys) {
    if (k.s > zoomMax + 1e-6) bad.push({f: k.f, axis: 'x', need: zoomMax, got: k.s});
  }
  for (let f = 0; f <= span; f += step) {
    const c = camAt(keys, f, stage);
    const w = visibleWindow(c.x, c.y, c.s, stage);
    if (anchor.x < w.left) bad.push({f, axis: 'x', need: anchor.x, got: w.left});
    if (anchor.x + anchor.w > w.right) bad.push({f, axis: 'x', need: anchor.x + anchor.w, got: w.right});
    if (anchor.y < w.top) bad.push({f, axis: 'y', need: anchor.y, got: w.top});
    if (anchor.y + anchor.h > w.bottom) bad.push({f, axis: 'y', need: anchor.y + anchor.h, got: w.bottom});
  }
  return bad;
};

// ---------------------------------------------------------------------------
// ShotCamera：把一个 shot 的全部内容包进受限相机。
// 只做 transform/opacity；Chrome 与字幕不在其内，因此永不被运镜带动。
// ---------------------------------------------------------------------------
export const ShotCamera: React.FC<{
  // `readonly`：调用方传的是 shots.ts（`as const`）里解析出来的关键帧字面量，
  // 那是只读元组，赋给 `CamKey[]` 会 TS2322。本件只读不写，放开只读正好对上。
  keys: readonly CamKey[];
  /** 本镜本地帧 */
  f: number;
  /** anchor 与 zoom 上限：开发期断言用，生产期为 0 开销 */
  anchor?: Anchor;
  zoomMax?: number;
  children?: React.ReactNode;
}> = ({keys, f, anchor, zoomMax = TEXT_ZOOM_MAX, children}) => {
  const {canvas} = useCanvas();
  const stage = stageFor(canvas);
  const c = camAt(keys, f, stage);
  if (process.env.NODE_ENV !== 'production' && anchor) {
    const bad = safeCheck(keys, anchor, zoomMax, stage);
    if (bad.length) console.warn('[shotkit] anchor 出界', bad.slice(0, 3));
  }
  // 3D 路径：有 rotY 时用 CSS zoom 而非 transform:scale，避免 Chromium 先光栅化再放大导致文字发虚。
  if (keys.some((k) => (k.rotY ?? 0) !== 0)) {
    return (
      <div style={{position: 'absolute', inset: 0, perspective: 1400}}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            transformOrigin: '0 0',
            zoom: c.s,
            transform: `translate(${stage.cx - c.x}px,${stage.cy - c.y}px) rotateY(${c.rotY}deg)`,
          }}
        >
          {children}
        </div>
      </div>
    );
  }
  return (
    <div style={{position: 'absolute', inset: 0, transformOrigin: '0 0', transform: camTransform(c.x, c.y, c.s, stage)}}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Depth coefficients for optional parallax treatment. Use only when depth
// clarifies the scene; they are not a required visual effect.
// ---------------------------------------------------------------------------
export const DEPTH = {far: 0.35, mid: 0.7, near: 1} as const;

export const CoverPanel: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  tone?: 'paper' | 'wash';
  pad?: number;
  z?: number;
  radius?: number;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}> = ({x, y, w, h, tone = 'wash', pad = 0, z = 42, radius, children, style}) => {
  const C = THEME.palette;
  const r = radius ?? THEME.aesthetic.paperRadius;
  if (tone === 'paper') {
    const Paper = THEME.Paper;
    return (
      <div style={{position: 'absolute', left: x, top: y, zIndex: z, ...style}}>
        <Paper lift={0.18} style={{width: w, height: h, padding: pad}}>
          {children}
        </Paper>
      </div>
    );
  }
  return (
    <div
      style={{
        position: 'absolute',
        left: x - pad,
        top: y - pad,
        width: w + pad * 2,
        height: h + pad * 2,
        zIndex: z,
        borderRadius: r,
        background: `${C.paperBase}E8`,
        boxShadow: `0 0 0 1px ${C.line}, 0 6px 18px ${C.paperBase}00`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

/**
 * Optional, deterministic ambient motion helper. Do not add it merely to avoid
 * stillness: a quiet hold is valid. Use only when subtle motion has a clear
 * visual purpose and does not compete with the instructional carrier.
 */
export const ambientBreath = (f: number, period = 150, amp = 0.03) => {
  const a = Math.min(0.04, Math.max(0, amp));
  const p = Math.min(180, Math.max(120, period));
  return 1 + a * (0.5 - 0.5 * Math.cos((f / p) * Math.PI * 2));
};

export const SHOTKIT_VERSION = 'shotkit-v3 · 6 intents · anchored safety · pan budget · ambientBreath';
