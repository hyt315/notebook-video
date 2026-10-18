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
// 事件名只能是 SFX_EVENTS 里的十个；音量缺省取 SFX_GAIN（已按「人声下方 8–12 LU」调好）。
// ============================================================================

export const SFX_EVENTS = ['whoosh', 'pop', 'click', 'typing', 'success', 'error', 'chart', 'highlight', 'chapter', 'riser'] as const;
export type SfxEvent = (typeof SFX_EVENTS)[number];

/** 事件 → 文件（与 sfx-manifest.json 一一对应；validate-audio-levels.py 会核对）。 */
export const SFX_FILES: Record<SfxEvent, string> = {
  whoosh: 'sfx/lib/whoosh.ogg',
  pop: 'sfx/lib/pop.ogg',
  click: 'sfx/lib/click.ogg',
  typing: 'sfx/lib/typing.ogg',
  success: 'sfx/lib/success.ogg',
  error: 'sfx/lib/error.ogg',
  chart: 'sfx/lib/chart.ogg',
  highlight: 'sfx/lib/highlight.ogg',
  chapter: 'sfx/lib/chapter.ogg',
  riser: 'sfx/lib/riser.ogg',
};
export const SFX_BED = 'sfx/lib/bed.ogg';

/**
 * 混音增益（线性）— 3.2.0 起与 public/sfx/sfx-manifest.json 的每条 `gain` **同值**（validate-audio-levels 核对）。
 * 每个 cue 由 scripts/dev/tune-sfx.py 放到「响度阶梯」上（chapter −24 … typing −30 LUFS），
 * 全部比音乐床高 11–17 LU、比人声 −16 LUFS 低 8–14 LU。不要在场景里再乘一层小音量。
 */
export const SFX_GAIN: Record<SfxEvent, number> = {
  whoosh: 0.338, pop: 0.419, click: 0.491, typing: 0.284, success: 0.459,
  error: 0.409, chart: 0.419, highlight: 0.356, chapter: 0.522, riser: 0.331,
};
/**
 * 瞬态位置（毫秒，= manifest `offsetMs`）：文件开头到听感「命中点」的距离。引擎把文件**提前**这么多开始播，
 * 命中点就正好落在视觉事件那一帧（±1 帧）。旧版没有这一步：error 晚 16 帧、chapter 晚 8 帧、whoosh 晚 4 帧。
 */
export const SFX_OFFSET_MS: Record<SfxEvent, number> = {
  whoosh: 71.6, pop: 5.8, click: 4.5, typing: 13.9, success: 6.1,
  error: 139.6, chart: 48, highlight: 58, chapter: 253.5, riser: 1066.7,
};
/** 音乐床（-30 LUFS 源）播放增益：0.28 ≈ -41 LUFS；每个 cue 期间再闪避到 BED_DUCK 倍。 */
export const BED_GAIN = 0.28;
export const BED_DUCK = 0.45;
/** riser 文件时长（帧，30fps）——3.2.0 起由 offsetMs 推：命中点落在章节首帧。 */
export const RISER_FRAMES = Math.round((SFX_OFFSET_MS.riser * 30) / 1000);
/** 两个音效之间的最小间隔：150 ms（5 帧）。更近的后来者被丢掉（优先级高的先排）。 */
const MIN_GAP = 5;
/** 密度上限：任意 10 秒窗口最多 4 个（≈ 24 次/分钟）；超出的丢低优先级的。 */
const WINDOW = 300, WINDOW_MAX = 4;
/** 转场音效的视觉命中点：转场中点（CINEMA.transition = 14 帧 → 7）。 */
const WHOOSH_HIT = 7;
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
const PRIORITY: SfxEvent[] = ['chapter', 'success', 'error', 'riser', 'whoosh', 'chart', 'typing', 'highlight', 'pop', 'click'];
const isEvent = (e: string): e is SfxEvent => (SFX_EVENTS as readonly string[]).includes(e);

/** 中间拍按介质选音：代码/控制台 → typing；图表/指标 → chart；其余 click / highlight 交替。 */
const middleEvent = (s: ShotLike, i: number): SfxEvent => {
  const m = s.media ?? [];
  if (m.includes('code') || m.includes('console')) return 'typing';
  if (m.includes('chart') || m.includes('metric')) return 'chart';
  return i % 2 ? 'click' : 'highlight';
};

/** 一镜的自动音效（本镜本地帧）。 */
export const autoSfxForShot = (s: ShotLike, isChapter: boolean, isFirst: boolean): {event: SfxEvent; at: number; beat?: number}[] => {
  const out: {event: SfxEvent; at: number; beat?: number}[] = [];
  if (isChapter) {
    out.push({event: 'chapter', at: 2});
    // riser 的命中点（文件末尾）与 chapter 的命中点同帧——两者合成一个「落点」，不再相隔 2 帧（67 ms）各响一下。
    if (!isFirst) out.push({event: 'riser', at: 2});
  } else if (!isFirst) {
    out.push({event: 'whoosh', at: WHOOSH_HIT});
  }
  if (s.sfxEvents && s.sfxEvents.length) {
    s.sfxEvents.forEach((e) => { if (isEvent(e.event)) out.push({event: e.event, at: e.at}); });
    return out;
  }
  const n = s.beats.length;
  s.beats.forEach((b, i) => {
    let ev: SfxEvent;
    if (i === 0) ev = 'pop';
    else if (i === n - 1) {
      const conclusive = (s.live ?? []).some((x) => CONCLUSIVE.includes(x)) || s.move === '收束' || s.move === '结论';
      ev = conclusive ? 'success' : 'highlight';
    } else if (i === 1 && s.misconception && n >= 3) ev = 'error';
    else ev = middleEvent(s, i);
    out.push({event: ev, at: b, beat: i});
  });
  return out;
};

/** 整片音效表（绝对帧）。chapterStarts = 各章首镜的 from。 */
export const planSfx = (shots: readonly ShotLike[], chapterStarts: readonly number[], total: number): SfxCue[] => {
  const raw: {event: SfxEvent; at: number; vol?: number}[] = [];
  shots.forEach((s, idx) => {
    const ov = s.sfx;
    if (ov === 'none') return;
    const list: Override[] = Array.isArray(ov) ? (ov as Override[]) : [];
    let auto = s.sfxAuto === false ? [] : autoSfxForShot(s, chapterStarts.includes(s.from), idx === 0);
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
    auto.forEach((a) => raw.push({event: a.event, at: s.from + a.at}));
  });
  // 优先级高的先占位；与已占位的同类/异类音效相距 < MIN_GAP 帧的丢掉（riser 是铺底，不参与互斥）
  // r.at = 视觉命中帧；开始播放帧 = 命中帧 − 瞬态偏移
  const sorted = raw.filter((r) => r.at >= 0 && r.at < total)
    .sort((a, b) => PRIORITY.indexOf(a.event) - PRIORITY.indexOf(b.event) || a.at - b.at);
  const kept: typeof raw = [];
  for (const r of sorted) {
    if (r.event !== 'riser' && kept.some((k) => k.event !== 'riser' && Math.abs(k.at - r.at) < MIN_GAP)) continue;
    if (r.event !== 'riser' && kept.filter((k) => k.event !== 'riser' && Math.abs(k.at - r.at) < WINDOW / 2).length >= WINDOW_MAX) continue;
    kept.push(r);
  }
  return kept.sort((a, b) => a.at - b.at)
        // 命中帧 < 瞬态偏移时（片头 chapter：命中第 2 帧、偏移 8 帧），以前起播被夹到 0、瞬态晚 6 帧；
    // 现在改为从第 0 帧起播并跳过文件开头 trim 帧，瞬态仍落在命中帧。
    .map((r) => {
      const start = r.at - offF(r.event);
      return {event: r.event, at: Math.max(0, start), hit: r.at, vol: r.vol ?? SFX_GAIN[r.event], src: SFX_FILES[r.event], trim: Math.max(0, -start)};
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
