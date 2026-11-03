// ============================================================================
// transitions/meta.ts · 转场元数据的唯一真源（P2-23 解耦）
//
// 以前时长 / 方向 / 是否翻页 / 无 GPU 退回散在四处：
//   · 时长    cinema.tsx 的 transitionFrames（CURL_FRAMES / 硬编码 22 / CINEMA.transition）
//   · 方向    fx.tsx 的 PAGETURN_FOLD_DIRECTION
//   · 翻页    sfx.ts 的 PAGE_TURN_TRANSITIONS + cinema.tsx 的 resolveTransition + fx.tsx 的 isCurl
//   · 退回    fx.tsx 的 FX_FALLBACK
// 新增一种转场要改三四个文件，漏一处的症状是「渲出来是对的、音效不对」或「预览与成片翻向相反」。
//
// 现在：**新增一种转场 = 在 TRANSITION_META 里加一个条目 + 一个实现模块**。
// 时长 / 方向 / 翻页 / 退回 / 拟音都从这张表读，不再各处抄。
//
// 与 scripts/transition-plan.mjs 的 CURL_FRAMES 同值（tests/test_fx.py 交叉校验）：
// 转场计划（构建期算窗口）与渲染器（画卷页）必须用同一个帧数，否则窗口盖不住整段卷页。
// ============================================================================

export type TransitionKind =
  | 'whip' | 'whip-left' | 'whip-right'
  | 'zoom' | 'fade' | 'hard' | 'slide' | 'drop'
  | 'pageturn' | 'peel' | 'pageflip';

/** 需要 WebGPU 的卷页种类（无 GPU 时按 fallback 退回）。 */
export type CurlKind = 'pageturn' | 'peel';

/**
 * 折线方向（度）：近乎竖直、下角领先。
 * CSS 折痕（transitions/pagefold.tsx）与 GPU 卷页（fx.tsx 的 curlParams）**共用这一个值**——
 * 预览走 CSS、成片走 GPU，两种翻页方向不一样，观众会以为换了转场。
 */
export const PAGETURN_FOLD_DIRECTION = -78;

/** 卷页转场时长（帧）：与 scripts/transition-plan.mjs 的 CURL_FRAMES 同值（测试交叉校验）。 */
export const CURL_FRAMES = 22;

/** 普通转场（whip / zoom / fade / slide / drop）的缺省时长（帧）。 */
export const DEFAULT_TRANSITION_FRAMES = 14;

export type TransitionMeta = {
  /** 转场时长（帧）。hard 是硬切，但 transitionFrames 仍返回 14（与历史一致；index 对 hard 直接 p=1，不用它）。 */
  frames: number;
  /** 是否翻页 —— 纸声跟着它走（不跟皮肤走）。新增翻页类型时这里要标 true。 */
  pageTurn: boolean;
  /** 需要 WebGPU 的卷页种类（CurlKind：pageturn / peel）；缺省 = 不需要。 */
  gpu?: CurlKind;
  /** 无 GPU 时退回的转场（仍是「翻过去一页」，不是横移）。 */
  fallback?: TransitionKind;
  /** 折线方向（度）；只有沿折线翻的转场才有。 */
  foldDirection?: number;
};

/**
 * 转场注册表。**新增一种转场只改这里 + 加一个实现模块**：
 *   · 时长（frames）→ transitionFrames 读它
 *   · 纸声（pageTurn）→ sfx.ts 读它
 *   · GPU 需求与退回（gpu / fallback）→ fx.tsx 读它
 *   · 方向（foldDirection）→ pagefold.tsx 与 fx.tsx 共用
 */
export const TRANSITION_META: Record<TransitionKind, TransitionMeta> = {
  whip:         {frames: DEFAULT_TRANSITION_FRAMES, pageTurn: false},
  'whip-left':  {frames: DEFAULT_TRANSITION_FRAMES, pageTurn: false},
  'whip-right': {frames: DEFAULT_TRANSITION_FRAMES, pageTurn: false},
  zoom:         {frames: DEFAULT_TRANSITION_FRAMES, pageTurn: false},
  fade:         {frames: DEFAULT_TRANSITION_FRAMES, pageTurn: false},
  // 硬切没有动画，但 transitionFrames 保持 14（历史行为；index 对 hard 直接 p=1，不会用到）
  hard:         {frames: DEFAULT_TRANSITION_FRAMES, pageTurn: false},
  slide:        {frames: DEFAULT_TRANSITION_FRAMES, pageTurn: false},
  drop:         {frames: DEFAULT_TRANSITION_FRAMES, pageTurn: false},
  // 翻页三兄弟：时长都是 CURL_FRAMES（手翻一页的速度），纸声跟着走
  pageturn:     {frames: CURL_FRAMES, pageTurn: true, gpu: 'pageturn', fallback: 'pageflip', foldDirection: PAGETURN_FOLD_DIRECTION},
  peel:         {frames: CURL_FRAMES, pageTurn: true, gpu: 'peel', fallback: 'drop'},
  // 无 GPU 时的折痕翻页（transitions/pagefold.tsx）：纯 CSS，速度与卷页一致
  pageflip:    {frames: CURL_FRAMES, pageTurn: true},
};

/** 哪些转场算「翻页」——纸声跟着这张表走。`auto` 由皮肤缺省决定，缺省就是翻页。 */
export const isPageTurnKind = (k: string | null | undefined): boolean =>
  k === 'auto' || (k != null && TRANSITION_META[k as TransitionKind]?.pageTurn === true);

/** 需要 WebGPU 的卷页种类判定（无 GPU 时走 fallback）。 */
export const isCurl = (k: string | null | undefined): k is CurlKind => k === 'pageturn' || k === 'peel';

/** 无 GPU 时的退回映射（仍是「翻过去一页」，不是横移）。 */
export const FX_FALLBACK: Record<CurlKind, TransitionKind> = {
  pageturn: 'pageflip',
  peel: 'drop',
};

/** 转场时长（帧）：注册表是唯一真源。kind 为 null（首镜无转场）时按普通转场。 */
export const transitionFramesOf = (kind: TransitionKind | null | undefined): number =>
  (kind && TRANSITION_META[kind]?.frames) || DEFAULT_TRANSITION_FRAMES;
