import React from 'react';
import {Easing, interpolate} from 'remotion';
import {THEME} from './theme/active';
import {useCanvas} from './theme/canvas';

// ============================================================================
// shotkit · 镜头层 v1（每个 shot 一段受限相机）
//
// 为什么需要它：v2.8 的 CameraRig 是「全片一条关键帧轨道」，且被
// Camera Micro-Framing Invariant 锁在 x∈[945,975] / s∈[1.00,1.018]
// ——景别变化 1.8%，等同定焦，观众感受到的是「翻页」。
//
// 本层的做法：把「自由曲线」换成「带内置不变量的受限配方」。
//   1. 每镜声明一个 intent（六个之一）+ 少量参数，曲线由 intent 决定；
//   2. 每镜额外声明 anchor（本镜必须始终可见的矩形）；
//   3. safeCheck() 用纯算术证明 anchor 在任意关键帧都落在可见窗内——
//      不需要渲染，脚本与运行时共用同一份数学（见 scripts/validate-shot-motion.py）。
//
// 铁律（Shot Camera Invariant）：
//   - 每镜 ≥1 次运镜、≤1 次；单次 30–45 帧 easeInOut；整片运镜配额见
//     references/shot-language.md；
//   - 含文字的镜头 zoom ≤ 1.35（纯图形镜头可到 1.60，硬上限 1.60）；
//   - Chrome / 章节卡 / 字幕永远在相机之外（屏幕空间），不受任何运镜影响；
//   - 无 3D 关键帧时走纯 translate+scale 路径，渲染结果与旧版逐像素一致。
// ============================================================================

export type ShotIntent = 'establish' | 'push-in' | 'pull-back' | 'pan-follow' | 'reveal' | 'micro-orbit';

/** 相机关键帧：f=该 shot 的本地帧；x/y=注视点（设计坐标）；s=缩放。 */
export type CamKey = {f: number; x: number; y: number; s: number; rotY?: number};

/** anchor：本镜必须始终可见的矩形（设计坐标）。 */
export type Anchor = {x: number; y: number; w: number; h: number};

/** 设计坐标系（与 index.tsx 的 1920×1080 舞台一致）。 */
export const STAGE = {w: 1920, h: 1080, cx: 960, cy: 540} as const;

/** 相机缩放硬上限。含文字的镜头用 TEXT_ZOOM_MAX，纯图形镜头可到 GRAPHIC_ZOOM_MAX。 */
export const TEXT_ZOOM_MAX = 1.35;
export const GRAPHIC_ZOOM_MAX = 1.6;

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

/**
 * 平移安全预算（**镜头铁律之二**）：相机平移会整层移动内容，所以在 s=1.00 时
 * 任何平移都会把内容推出画面、露出边缘（实测：pan-follow 在 s=1.0 下把左侧站名裁掉）。
 *
 * 几何上，缩放为 s 时可见窗半宽 = 960/s，只要窗口仍落在 1920×1080 舞台内就不会露边，
 * 因此可用的最大平移量为：
 *     maxPanX = 960 * (1 - 1/s)      maxPanY = 540 * (1 - 1/s)
 * 即 **想平移多少，就必须先缩放到能覆盖它**（s=1.06 → ±54px；s=1.12 → ±103px）。
 * camAt() 会按此钳制；scripts/validate-shot-motion.py 用同一公式检查，
 * 请求量超出预算时记 P1（说明平移会被削减）。
 */
export const panBudget = (s: number) => ({
  x: STAGE.cx * (1 - 1 / Math.max(1, s)),
  y: STAGE.cy * (1 - 1 / Math.max(1, s)),
});

const clampPan = (x: number, y: number, s: number) => {
  const b = panBudget(s);
  return {
    x: Math.min(STAGE.cx + b.x, Math.max(STAGE.cx - b.x, x)),
    y: Math.min(STAGE.cy + b.y, Math.max(STAGE.cy - b.y, y)),
  };
};
const easeInOut = Easing.inOut(Easing.cubic);

/** 运镜默认时长（帧）：shot-language.md 规定单次 30–45 帧。 */
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
};

/**
 * 把 intent 展开成关键帧序列。纯函数、无随机、无状态。
 * 刻意只暴露少量参数：曲线形状由 intent 决定，调用方改不出「AI 乱写相机」那种曲线。
 */
export const shotCam = (intent: ShotIntent, o: IntentOpts): CamKey[] => {
  const x = o.x ?? STAGE.cx;
  const y = o.y ?? STAGE.cy;
  const at = o.at ?? 0;
  const dur = o.dur ?? CAM_DUR.std;
  const end = o.duration;
  const holdEnd = Math.max(at + dur, end);
  const head: CamKey[] = {f: 0, x: o.fromX ?? x, y: o.fromY ?? y, s: o.from ?? 1};
  const tail: CamKey[] = {f: end, x, y, s: o.to ?? o.from ?? 1};
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
    case 'micro-orbit':
      return [head, {f: at, x, y, s: o.from ?? 1, rotY: 0}, {f: at + dur, x, y, s: o.to ?? o.from ?? 1, rotY: o.rotY ?? 6}, {f: holdEnd, x, y, s: o.to ?? o.from ?? 1}];
    default:
      return [head, tail];
  }
};

/** 静止镜头（明确表示本镜不运镜）。still 是合法选择，但全片配额受限。 */
export const stillCam = (duration: number, x = STAGE.cx, y = STAGE.cy, s = 1): CamKey[] => [
  {f: 0, x, y, s},
  {f: duration, x, y, s},
];

/** 插值求某帧的相机状态。 */
export const camAt = (keys: CamKey[], f: number): {x: number; y: number; s: number; rotY: number} => {
  if (keys.length === 0) return {x: STAGE.cx, y: STAGE.cy, s: 1, rotY: 0};
  if (keys.length === 1 || f <= keys[0].f) {
    const k = keys[0];
    const c = clampPan(k.x, k.y, k.s);
    return {x: c.x, y: c.y, s: k.s, rotY: k.rotY ?? 0};
  }
  let i = 0;
  while (i < keys.length - 2 && f > keys[i + 1].f) i++;
  const a = keys[i];
  const b = keys[i + 1];
  const p = interpolate(f, [a.f, Math.max(a.f + 1, b.f)], [0, 1], {...clamp, easing: easeInOut});
  const s = a.s + (b.s - a.s) * p;
  const c = clampPan(a.x + (b.x - a.x) * p, a.y + (b.y - a.y) * p, s);
  return {
    x: c.x,
    y: c.y,
    s,
    rotY: (a.rotY ?? 0) + ((b.rotY ?? 0) - (a.rotY ?? 0)) * p,
  };
};

/** 相机变换：注视点 (x,y) 落在画面中心，缩放 s。与旧 CameraRig 公式一致 → 兼容。 */
export const camTransform = (x: number, y: number, s: number): string =>
  `translate(${STAGE.cx - x * s}px,${STAGE.cy - y * s}px) scale(${s})`;

/** 可见窗（设计坐标）。anchor 必须落在其中。 */
export const visibleWindow = (x: number, y: number, s: number) => ({
  left: x - STAGE.cx / s,
  right: x + STAGE.cx / s,
  top: y - STAGE.cy / s,
  bottom: y + STAGE.cy / s,
});

export type SafeViolation = {f: number; axis: 'x' | 'y'; need: number; got: number};

/**
 * 出界数学证明：逐关键帧检查 anchor 是否完整落在可见窗内。
 * 纯算术、零渲染。脚本 scripts/validate-shot-motion.py 用同一套数学复核 shots.json。
 */
export const safeCheck = (keys: CamKey[], anchor: Anchor, zoomMax: number): SafeViolation[] => {
  const bad: SafeViolation[] = [];
  const span = Math.max(...keys.map((k) => k.f), 1);
  const step = Math.max(1, Math.round(span / Math.max(2, Math.ceil(span / 8))));
  for (const k of keys) {
    if (k.s > zoomMax + 1e-6) bad.push({f: k.f, axis: 'x', need: zoomMax, got: k.s});
  }
  for (let f = 0; f <= span; f += step) {
    const c = camAt(keys, f);
    const w = visibleWindow(c.x, c.y, c.s);
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
  keys: CamKey[];
  /** 本镜本地帧 */
  f: number;
  /** anchor 与 zoom 上限：开发期断言用，生产期为 0 开销 */
  anchor?: Anchor;
  zoomMax?: number;
  children?: React.ReactNode;
}> = ({keys, f, anchor, zoomMax = TEXT_ZOOM_MAX, children}) => {
  const c = camAt(keys, f);
  if (process.env.NODE_ENV !== 'production' && anchor) {
    const bad = safeCheck(keys, anchor, zoomMax);
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
            transform: `translate(${STAGE.cx - c.x}px,${STAGE.cy - c.y}px) rotateY(${c.rotY}deg)`,
          }}
        >
          {children}
        </div>
      </div>
    );
  }
  return (
    <div style={{position: 'absolute', inset: 0, transformOrigin: '0 0', transform: camTransform(c.x, c.y, c.s)}}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// DepthLayers：景深视差。系数阶梯 0.35 / 0.7 / 1.0，层数 ≤3。
// far/mid 层按系数分担相机的位移与缩放，产生真实纵深；层数越多越廉价，故 ≤3。
// ---------------------------------------------------------------------------
export const DEPTH = {far: 0.35, mid: 0.7, near: 1} as const;

export const DepthLayers: React.FC<{
  keys: CamKey[];
  f: number;
  far?: React.ReactNode;
  mid?: React.ReactNode;
  /** 近层（默认 = 主要内容，全量相机） */
  children?: React.ReactNode;
  /** 远层过扫比例：防止视差位移露出边缘（远层是整幅背景时必须给） */
  overscan?: number;
}> = ({keys, f, far, mid, children, overscan = 0.14}) => {
  const c = camAt(keys, f);
  const layer = (k: number, node?: React.ReactNode, bleed = 0) => {
    if (node === undefined || node === null) return null;
    const tx = (STAGE.cx - c.x * c.s) * k;
    const ty = (STAGE.cy - c.y * c.s) * k;
    const s = 1 + (c.s - 1) * k;
    const bw = STAGE.w * bleed;
    const bh = STAGE.h * bleed;
    return (
      <div
        style={{
          position: 'absolute',
          left: -bw,
          top: -bh,
          width: STAGE.w + bw * 2,
          height: STAGE.h + bh * 2,
          transformOrigin: '0 0',
          transform: `translate(${tx}px,${ty}px) scale(${s})`,
        }}
      >
        {node}
      </div>
    );
  };
  return (
    <>
      {layer(DEPTH.far, far, overscan)}
      {layer(DEPTH.mid, mid)}
      {layer(DEPTH.near, children)}
    </>
  );
};

// ---------------------------------------------------------------------------
// BackgroundMute：把主题锁定的背景装饰「垫底」，让压在上面的文字可读。
//
// 设计意图：背景图很好看，不该换掉；但当内容压到装饰上时，文字会被吃掉。
// 这里在装饰区之上、内容之下铺一层带羽化的暖底（不是硬边框），既盖住装饰、
// 又保留它的形状可辨。需要完整盖住时用 CoverPanel（真卡片底）。
// ---------------------------------------------------------------------------
export const BackgroundMute: React.FC<{zones?: number[]; opacity?: number; z?: number}> = ({zones, opacity = 0.74, z = 45}) => {
  const {mode} = useCanvas();
  const decor = (THEME as {backgroundDecorZones?: {x: number; y: number; w: number; h: number}[]}).backgroundDecorZones;
  if (!decor || decor.length === 0) return null;
  const pick = zones ?? decor.map((_, i) => i);
  const C = THEME.palette;
  return (
    <>
      {pick.map((i) => {
        const d = decor[i];
        if (!d) return null;
        // 比例适配：装饰坐标以 16:9 设计空间标定，其他画幅按宽度比例收缩
        const k = mode.designW / 1920;
        const x = d.x * k;
        const w = d.w * k;
        const h = d.h;
        const y = Math.min(d.y, mode.designH - h);
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: w,
              height: h,
              zIndex: z,
              pointerEvents: 'none',
              background: `radial-gradient(120% 100% at 50% 50%, ${C.paperBase}F2 46%, ${C.paperBase}B8 74%, transparent 100%)`,
              opacity,
            }}
          />
        );
      })}
    </>
  );
};

// ---------------------------------------------------------------------------
// CoverPanel：内容的「底托」。压到背景装饰上时用它保证对比度。
// tone='paper' 走主题卡片皮肤（有边框/阴影，用于主体内容）；
// tone='wash'  只铺一层柔和底色并圆角羽化（用于文字簇、贴标带），不成卡片感。
// ---------------------------------------------------------------------------
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
        boxShadow: `0 0 0 1px ${C.line}55, 0 6px 18px ${C.paperBase}00`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

/**
 * ambientBreath：每镜**唯一**的缓慢环境运动（Rule 5）。
 * 为什么需要：所有元素都"动完就永久静止"时，画面会像被暂停；一个几乎察觉不到的
 * 背景呼吸给前景提供参照，观感立刻"活"起来。
 * 预算（写死在函数里，防止被滥用）：幅度 ≤4%、周期 120–180 帧、正弦缓动、
 * **只能放在背景/次级元素上**，绝不放内容层（内容动会分散注意力，且违反"内容只在语义节点变化"）。
 */
export const ambientBreath = (f: number, period = 150, amp = 0.03) => {
  const a = Math.min(0.04, Math.max(0, amp));
  const p = Math.min(180, Math.max(120, period));
  return 1 + a * (0.5 - 0.5 * Math.cos((f / p) * Math.PI * 2));
};

export const SHOTKIT_VERSION = 'shotkit-v1.1 · 6 intents · anchored safety · pan budget by zoom · depth 0.35/0.7/1 · ambientBreath';
