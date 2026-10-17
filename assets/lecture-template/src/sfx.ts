// ============================================================================
// sfx.ts · 语义音效表（v4.3）
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
 * 混音增益（线性）。库里每个文件都已归一到同一响度（-18 LUFS/100ms），
 * 这里的 0.30–0.55（约 -5…-10 dB）把它们压到约 -24…-28 LUFS，比人声目标 -16 LUFS 低 8–12 LU：
 * 听得见、但永远在人声下面（ducked）。不要在场景里再乘一层小音量（双重衰减曾让音效完全听不见）。
 */
export const SFX_GAIN: Record<SfxEvent, number> = {
  whoosh: 0.42, pop: 0.45, click: 0.38, typing: 0.34, success: 0.5,
  error: 0.36, chart: 0.4, highlight: 0.4, chapter: 0.55, riser: 0.36,
};
/** 音乐床（-30 LUFS 源）播放增益：0.28 ≈ -41 LUFS，远在人声与音效之下（0.5 时实测把音效只托高 6–12 dB，偏闷）。 */
export const BED_GAIN = 0.28;
/** riser 文件时长（帧，30fps）：riser 排在「命中帧 − 这么多帧」开始，正好在命中帧到顶。 */
export const RISER_FRAMES = 45;
/** 两个音效之间的最小间隔（帧）：更近的后来者被丢掉（优先级高的先排）。 */
const MIN_GAP = 6;

export type SfxCue = {event: SfxEvent; at: number; vol: number; src: string};
type Override = {event: string; beat?: number; at?: number; vol?: number};
type ShotLike = {
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
    if (!isFirst) out.push({event: 'riser', at: -RISER_FRAMES});
  } else if (!isFirst) {
    out.push({event: 'whoosh', at: 0});
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
  const sorted = raw.filter((r) => r.at >= 0 && r.at < total)
    .sort((a, b) => PRIORITY.indexOf(a.event) - PRIORITY.indexOf(b.event) || a.at - b.at);
  const kept: typeof raw = [];
  for (const r of sorted) {
    if (r.event !== 'riser' && kept.some((k) => k.event !== 'riser' && Math.abs(k.at - r.at) < MIN_GAP)) continue;
    kept.push(r);
  }
  return kept.sort((a, b) => a.at - b.at)
    .map((r) => ({event: r.event, at: r.at, vol: r.vol ?? SFX_GAIN[r.event], src: SFX_FILES[r.event]}));
};
