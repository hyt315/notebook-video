// ============================================================================
// sfx.ts · 语义音效表
//
// 音效库是**预制**的（public/sfx/lib/*.ogg + public/sfx/sfx-manifest.json）：
// 开发期用 earshot（github.com/Leonxlnx/earshot，MIT）在代码里合成、统一响度（-18 LUFS/100ms、
// 峰值 ≤ -1 dBFS）、用 CLAP 匹配做质检后提交进仓库。普通用户**不需要**装 earshot。
// 重建：python scripts/dev/build-sfx-library.py（只在维护者机器上跑）。
//
// 引擎按分镜表的语义自动排音效（planSfx）；分镜表每镜可写 `sfx` 字段覆盖：
//   "sfx": "none"                                  本镜不出任何自动音效
//   "sfx": [{"event": "success", "beat": 2}]        替换第 2 拍的自动音效
//   "sfx": [{"event": "error", "at": 40, "vol": 0.3}] 在本镜本地帧 40 额外加一个
//   "sfxAuto": false                               关掉本镜自动规则，只用显式条目
// 事件名只能是 SFX_EVENTS 里的九个（3.8.0 瘦身：16 → 9；保留 4 个手作拟音 page / place / stamp）；
// 音量缺省取 SFX_GAIN（已按「人声下方 8–12 LU」调好）。
//
// 3.8.0 删掉的是「重复」与「几乎用不到」的七种：whoosh（所有转场已改走 page）、
// click / rustle（中拍只在 normal 出现，与 highlight 重叠）、typing（只在代码镜的中拍）、
// riser（只在 normal 出现，且是库里唯一被 earshot 判 no match 的）、snip / latch（papercut 专用，极窄）。
// ============================================================================

import {THEME} from './theme/active';
import {isPageTurnKind} from './transitions/meta';
import {isHandmadeMedium, type MediumTheme} from './theme/medium';

export const SFX_EVENTS = ['pop', 'success', 'error', 'chart', 'highlight', 'chapter', 'page', 'place', 'stamp'] as const;
export type SfxEvent = (typeof SFX_EVENTS)[number];

/** 事件 → 文件（与 sfx-manifest.json 一一对应；validate-audio-levels.py 会核对）。 */
export const SFX_FILES: Record<SfxEvent, string> = {
  pop: 'sfx/lib/pop.ogg',
  success: 'sfx/lib/success.ogg',
  error: 'sfx/lib/error.ogg',
  chart: 'sfx/lib/chart.ogg',
  highlight: 'sfx/lib/highlight.ogg',
  chapter: 'sfx/lib/chapter.ogg',
  // 手作拟音（Kenney RPG Audio，CC0 真录音；scripts/dev/import-craft-sfx.py 入库）
  page: 'sfx/lib/page.ogg',
  place: 'sfx/lib/place.ogg',
  stamp: 'sfx/lib/stamp.ogg',
};
export const SFX_BED = 'sfx/lib/bed.ogg';
/**
 * 音色轮换（P2-20）：连续翻页若每次都是同一段纸声，3 次之后就显得机械。
 * 这里给「重复率最高的动作拟音」准备同源微变体（音高/滤波略不同，瞬态位置差 <0.5 ms，
 * 共用同一个 offsetMs 与 gain）。planSfx 按事件出现次序轮换：主文件 → 变体 → 主文件 → …
 * 变体元数据在 sfx-manifest.json 的 `variants[]` 里，validate-audio-levels 一并核对。
 */
export const SFX_VARIANTS: Partial<Record<SfxEvent, readonly string[]>> = {
  page: ['sfx/lib/page-b.ogg', 'sfx/lib/page-c.ogg'],
};

/**
 * 混音增益（线性）— 3.2.0 起与 public/sfx/sfx-manifest.json 的每条 `gain` **同值**（validate-audio-levels 核对）。
 * 每个 cue 由 scripts/dev/tune-sfx.py 放到「响度阶梯」上（chapter −24 … highlight −27 LUFS），
 * 全部比音乐床高 11–17 LU、比人声 −16 LUFS 低 8–14 LU。不要在场景里再乘一层小音量。
 */
export const SFX_GAIN: Record<SfxEvent, number> = {
  pop: 0.419, success: 0.459, error: 0.409, chart: 0.419, highlight: 0.356,
  chapter: 0.49, page: 0.398, place: 0.376, stamp: 0.447,
};
/**
 * 瞬态位置（毫秒，= manifest `offsetMs`）：文件开头到听感「命中点」的距离。引擎把文件**提前**这么多开始播，
 * 命中点就正好落在视觉事件那一帧（±1 帧）。旧版没有这一步：error 晚 16 帧、chapter 晚 8 帧。
 */
export const SFX_OFFSET_MS: Record<SfxEvent, number> = {
  pop: 5.8, success: 6.1, error: 139.6, chart: 48, highlight: 8.5,
  chapter: 253.5, page: 39.8, place: 71.0, stamp: 74.7,
};
/** 音乐床（-30 LUFS 源）播放增益：0.28 ≈ -41 LUFS；每个 cue 期间再闪避到 BED_DUCK 倍。 */
export const BED_GAIN = 0.28;
export const BED_DUCK = 0.45;
/** 两个音效之间的最小间隔：150 ms（5 帧）。更近的后来者被丢掉（优先级高的先排）。 */
const MIN_GAP = 5;
// 哪些转场算「翻页」由 transitions/meta.ts 的 TRANSITION_META 统一声明（pageTurn: true）。
// P2-23 解耦：以前这里是第二个 Set，新增翻页类型时漏改的症状是「画面翻了页、听不见纸」。
// 纸声跟着翻页走，不跟着皮肤走。
/** 纸声的命中帧（本镜本地帧）：转场第 3 帧，纸刚被掀起的那一刻，不是转场结束。 */
const PAGE_HIT = 3;
/** 不是「标点」的声音：page 是翻页的动作拟音。它不参与下面的互斥。 */
const FOLEY = new Set<SfxEvent>(['page']);
/** 密度上限：任意 10 秒窗口最多 4 个（≈ 24 次/分钟）；超出的丢低优先级的。 */
const WINDOW = 300, WINDOW_MAX = 4;
const offF = (e: SfxEvent) => Math.round((SFX_OFFSET_MS[e] * 30) / 1000);

/** at = 开始播放帧；hit = 视觉命中帧；trim = 从文件开头跳过的帧数（命中帧早于瞬态偏移时，比如片头第 2 帧的 chapter）。 */
export type SfxCue = {event: SfxEvent; at: number; hit: number; vol: number; src: string; trim: number};
type Override = {event: string; beat?: number; at?: number; vol?: number};
type ShotLike = {
  /** 3.2.0 auto 层：真实视觉事件（元素出现 / 关键词高亮 / 数字落定），本镜本地帧。有它就不用 beats 猜。 */
  sfxEvents?: readonly {event: string; at: number}[];
  id: string; from: number; to: number; duration: number; beats: readonly number[];
  media?: readonly string[]; live?: readonly string[]; move?: string | null; misconception?: string | null;
  transition?: string; sfx?: unknown; sfxAuto?: boolean;
};

const CONCLUSIVE = ['Checklist', 'StampSeal', 'VerdictBar', 'StampBanner', 'MetricGrid', 'CheckBadge'];
const PRIORITY: SfxEvent[] = ['chapter', 'success', 'stamp', 'error', 'page', 'chart', 'highlight', 'pop', 'place'];

/**
 * 3.3.0 媒介化音效：手作媒介把自动规则里的 UI 音换成纸与手的声音——
 * 元素出现 pop → 纸片放下 place；结论 success → 盖章 stamp。
 * 只换**自动**排的音效；分镜表 sfx 字段里显式写的事件原样保留。
 * 3.8.0：判断改为 isHandmadeMedium —— flat / cel 也声明 craft（线稿色、字体、转场），
 * 但它们的自动音效仍是 UI 音，不再被误映射成纸片声。
 * 3.8.0 瘦身后只剩这两条映射（whoosh→page 已由转场分支直接排 page，click→rustle 随 click 一起删除）。
 */
const CRAFT_SFX: Partial<Record<SfxEvent, SfxEvent>> = {pop: 'place', success: 'stamp'};
const mediaSound = (e: SfxEvent, theme: MediumTheme = THEME): SfxEvent =>
  (isHandmadeMedium(theme) ? CRAFT_SFX[e] ?? e : e);
const isEvent = (e: string): e is SfxEvent => (SFX_EVENTS as readonly string[]).includes(e);

/** 中间拍按介质选音：图表/指标 → chart；其余 → highlight。
 *  3.8.0 删掉 typing / click 后，代码镜的中拍也给 highlight——它是「轻点一记」的通用音。 */
const middleEvent = (s: ShotLike): SfxEvent => {
  const m = s.media ?? [];
  if (m.includes('chart') || m.includes('metric')) return 'chart';
  return 'highlight';
};

/** 音效密度（3.3.0 片级字段，写进 manifests/shots.json 顶层）：
 *  · sparse（缺省）：每镜只留末拍一记 + 章节/转场；误区镜额外保留第 2 拍的反转音。
 *    为什么改缺省：旁白由使用者自行后配（任意 TTS 或真人），不知道以后有没有人声，
 *    所以默认就该克制——音效是标点，不是配乐。
 *  · normal：3.3.0 的行为，每个 beat 一个音效（老工程想要原样就写 "sfxDensity": "normal"）。
 */
export type SfxDensity = 'sparse' | 'normal';
export const SFX_DENSITY_DEFAULT: SfxDensity = 'sparse';

/** 一镜的自动音效（本镜本地帧）。 */
export const autoSfxForShot = (s: ShotLike, isChapter: boolean, isFirst: boolean, density: SfxDensity = SFX_DENSITY_DEFAULT): {event: SfxEvent; at: number; beat?: number}[] => {
  const out: {event: SfxEvent; at: number; beat?: number}[] = [];
  // 3.9.0：翻页必须有纸声。这不是「标点」，是**动作拟音**——画面里一张纸翻过去却听不见纸，
  // 观众读到的是「转场特效」，不是「翻了一页」。sparse 只削标点，不削动作。
  // 判据与 cinema.tsx 的 resolveTransition 一致：auto / pageturn / peel / pageflip 都是翻页
  // （3.9.0 起所有皮肤的缺省转场就是 pageturn，所以不写 transition 的片子也有纸声）。
  if (!isFirst && isPageTurnKind(s.transition ?? 'auto')) out.push({event: 'page', at: PAGE_HIT});
  // 3.8.0 瘦身后，normal 模式也不再叠 riser / whoosh —— 换章已有 chapter、翻页已有 page，
  // 再叠一层只是重复；实测（cell 演示片 49 s）保留它们时是 24 条/分钟，去掉后才是「音效是标点」的量级。
  if (isChapter) out.push({event: 'chapter', at: 2});
  if (s.sfxEvents && s.sfxEvents.length) {
    s.sfxEvents.forEach((e) => { if (isEvent(e.event)) out.push({event: e.event, at: e.at}); });
    return out;
  }
  const n = s.beats.length;
  if (density === 'sparse') {
    // 「每镜一记」：换章的镜已经有章节声（out 里那条），不再加 beat 音；其余镜在末拍给一记。
    // 这样 8 镜的片子里 beat 音最多 8 条，加上章节声才是 8–12 条量级（cell 演示片实测 9 条 / 11 条每分钟）。
    if (isChapter || !n) return out;
    const conclusive = (s.live ?? []).some((x) => CONCLUSIVE.includes(x)) || s.move === '收束' || s.move === '结论';
    out.push({event: conclusive ? 'success' : 'highlight', at: s.beats[n - 1], beat: n - 1});
    // 误区镜的「反转」是叙事骨架，单独留一条
    if (s.misconception && n >= 3) out.push({event: 'error', at: s.beats[1], beat: 1});
    return out;
  }
  s.beats.forEach((b, i) => {
    let ev: SfxEvent;
    if (i === 0) ev = 'pop';
    else if (i === n - 1) {
      const conclusive = (s.live ?? []).some((x) => CONCLUSIVE.includes(x)) || s.move === '收束' || s.move === '结论';
      ev = conclusive ? 'success' : 'highlight';
    } else if (i === 1 && s.misconception && n >= 3) ev = 'error';
    else ev = middleEvent(s);
    out.push({event: ev, at: b, beat: i});
  });
  return out;
};

/** 整片音效表（绝对帧）。chapterStarts = 各章首镜的 from。
 *  theme 仅供行为测试注入；生产调用省略，沿用当前皮肤。 */
export const planSfx = (shots: readonly ShotLike[], chapterStarts: readonly number[], total: number, density: SfxDensity = SFX_DENSITY_DEFAULT, theme: MediumTheme = THEME): SfxCue[] => {
  const raw: {event: SfxEvent; at: number; vol?: number}[] = [];
  shots.forEach((s, idx) => {
    const ov = s.sfx;
    if (ov === 'none') return;
    const list: Override[] = Array.isArray(ov) ? (ov as Override[]) : [];
    let auto = s.sfxAuto === false ? [] : autoSfxForShot(s, chapterStarts.includes(s.from), idx === 0, density);
    for (const o of list) {
      if (!isEvent(o.event)) continue;
      if (o.beat !== undefined) {
        auto = auto.filter((a) => a.beat !== o.beat);
        const b = s.beats[o.beat];
        if (b !== undefined) raw.push({event: o.event, at: s.from + b, vol: o.vol});
      } else if (o.at !== undefined) {
        raw.push({event: o.event, at: s.from + o.at, vol: o.vol});
      }
    }
    auto.forEach((a) => raw.push({event: mediaSound(a.event, theme), at: s.from + a.at}));
  });
  // 优先级高的先占位；与已占位的同类/异类音效相距 < MIN_GAP 帧的丢掉。
  // 豁免「不是标点」的声音：page 是翻页的**动作拟音**——
  // 换章那一镜 chapter 先占位，page 若按标点互斥就会被 MIN_GAP 丢掉，翻页又变回无声。
  const sorted = raw.filter((r) => r.at >= 0 && r.at < total)
    .sort((a, b) => PRIORITY.indexOf(a.event) - PRIORITY.indexOf(b.event) || a.at - b.at);
  const kept: typeof raw = [];
  for (const r of sorted) {
    if (!FOLEY.has(r.event) && kept.some((k) => !FOLEY.has(k.event) && Math.abs(k.at - r.at) < MIN_GAP)) continue;
    if (!FOLEY.has(r.event) && kept.filter((k) => !FOLEY.has(k.event) && Math.abs(k.at - r.at) < WINDOW / 2).length >= WINDOW_MAX) continue;
    kept.push(r);
  }
  return kept.sort((a, b) => a.at - b.at)
        // 命中帧 < 瞬态偏移时（片头 chapter：命中第 2 帧、偏移 8 帧），以前起播被夹到 0、瞬态晚 6 帧；
    // 现在改为从第 0 帧起播并跳过文件开头 trim 帧，瞬态仍落在命中帧。
    .map((r, i, arr) => {
      const start = r.at - offF(r.event);
      // 音色轮换：同事件按在最终计划里的出现次序换变体（主 → 变体 → 主…），
      // 翻页连着来时听起来是「同一叠纸的几页」，不是「同一个采样循环」。
      const seq = arr.slice(0, i + 1).filter((x) => x.event === r.event).length - 1;
      const alts = SFX_VARIANTS[r.event];
      const src = alts && alts.length ? [SFX_FILES[r.event], ...alts][seq % (1 + alts.length)] : SFX_FILES[r.event];
      return {event: r.event, at: Math.max(0, start), hit: r.at, vol: r.vol ?? SFX_GAIN[r.event], src, trim: Math.max(0, -start)};
    });
};

/** 音乐床闪避：每个 cue 命中前 2 帧到命中后 12 帧，床降到 BED_DUCK 倍（帧的纯函数）。 */
export const bedDuckAt = (f: number, plan: readonly SfxCue[]): number => {
  let k = 1;
  for (const c of plan) {
    const d = f - c.hit;
    if (d < -2 || d > 14) continue;
    const w = d < 0 ? (d + 2) / 2 : d <= 4 ? 1 : 1 - (d - 4) / 10;
    k = Math.min(k, 1 - (1 - BED_DUCK) * Math.max(0, Math.min(1, w)));
  }
  return k;
};
