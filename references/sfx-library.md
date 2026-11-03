# SFX library

The template ships a small, finished sound-effect library so ordinary AI tools (Windows included) never have to
generate, download or tune sounds. Files live in `assets/lecture-template/public/sfx/lib/`, described by
`public/sfx/sfx-manifest.json` (sha256, duration, loudness, peak, source recipe, license, intended use).

## Events

Nine events plus an optional bed (3.8.0 slimmed 16 → 9; see `src/sfx.ts` for why each cut one went).

The cut seven, and why they were not worth keeping:

| removed | why |
|---|---|
| `whoosh` | every pageturn now gets `page`, on every skin; whoosh only fired on non-pageturn transitions in `normal` |
| `click`, `rustle` | middle-beat ticks that only `normal` used, and `highlight` already covers the same slot |
| `typing` | only middle beats of code / console shots |
| `riser` | only `normal`; also the one library sound earshot scored `no match` (z 1.63) |
| `snip`, `latch` | papercut-only, and only reachable when a story names them explicitly |

Old stories that name a removed event now fail in `resolve-shots.py` with an explicit message instead of going silent.

| event | file | when the engine uses it |
|---|---|---|
| `pop` | `sfx/lib/pop.ogg` | first beat of a shot (first element appears) |
| `chart` | `sfx/lib/chart.ogg` | middle beats when `media` has `chart` or `metric` |
| `highlight` | `sfx/lib/highlight.ogg` | last beat of a non-conclusive shot; every other middle beat |
| `success` | `sfx/lib/success.ogg` | last beat when `live` has Checklist / StampSeal / VerdictBar / StampBanner / MetricGrid / CheckBadge, or `move` is 收束/结论 |
| `error` | `sfx/lib/error.ogg` | beat 1 of a shot with a `misconception` and ≥ 3 beats |
| `chapter` | `sfx/lib/chapter.ogg` | 2 frames into each chapter's first shot |
| `page` | `sfx/lib/page.ogg` | 3 frames into any pageturn shot (auto / pageturn / peel / pageflip) — an action sound, never thinned |
| `place` | `sfx/lib/place.ogg` | hand-made skins: replaces `pop` |
| `stamp` | `sfx/lib/stamp.ogg` | hand-made skins: replaces `success` |
| (bed) | `sfx/lib/bed.ogg` | optional quiet music bed, looped under the whole film |

Priority when two cues fall within 6 frames: chapter > success > stamp > error > page > chart > highlight > pop > place.

## Override per shot (manifests/shots.json)

```json
"sfx": "none"                                     // no sound for this shot
"sfx": [{"event": "success", "beat": 2}]           // replace the automatic cue on beat 2
"sfx": [{"event": "error", "at": 40, "vol": 0.3}]  // add a cue at local frame 40
"sfxAuto": false                                   // only the explicit cues above
```

`resolve-shots.py` validates the field and passes it into `src/shots.ts`; the engine reads it in `planSfx`.

## Medium mapping (3.8.0)

Only the hand-made media (`journal` / `papercut` / `archive`) remap **automatic** punctuation sounds:

| automatic UI sound | hand-made sound |
|---|---|
| `pop` | `place` |
| `success` | `stamp` |

`page` is not in this table on purpose: a pageturn gets paper sound on **every** skin, because it is an action,
not punctuation.

`flat` and `cel` also declare `craft` (ink colour, fonts, default transition), but that is a **capability
configuration**, not a hand-made medium. They keep the UI sounds above. The single authority is
`src/theme/medium.ts` → `isHandmadeMedium()`; `auto.tsx` and `sfx.ts` must both use it, and a story's explicit
`sfx` entries are never rewritten by this mapping.

## Levels

All one-shots: -18 LUFS (K-weighted, 100 ms blocks), sample peak ≤ -1 dBFS, mono 48 kHz Ogg Vorbis (4–15 KB each).
Mix gains in `SFX_GAIN` (0.34–0.55) keep them 8–12 LU under narration at -16 LUFS. `validate-audio-levels.py`
checks hashes against the manifest, peaks, the loudness tolerance, the event/file mapping in `src/sfx.ts` and the
gain range.

## Provenance and rebuild (maintainers only)

Rendered in code with **earshot** 0.2.0 (`earshot forge` recipes; https://github.com/Leonxlnx/earshot, MIT) — no
recorded samples — and quality-checked with `earshot rank` / `earshot match` (CLAP). License: CC0-1.0.
Users never install earshot. To rebuild: `python scripts/dev/build-sfx-library.py` (needs torch CPU + earshot).

## Rebuilt highlight (3.8.0)

`highlight` was the weakest sound still in use: `notify #14` with an 1800 Hz high-pass and a 190 ms cut, earshot
CLAP match z 2.04 ("weak"). It is also the single most repeated cue in a sparse film (last beat of every
non-conclusive shot), so a thin tick gets heard twenty times.

The rebuild takes a ready-made sound from earshot's own bank instead of another seed of the same recipe:
`earshot sfx render pro_notify/ding_2296` — a clean short bell, 0.26 s, spectral centroid 3.1 kHz, 6 ms attack.
It passes earshot's model-free audit (`earshot sfx check`: no clicks, no cut tail, no clipping, no DC), is
normalised to the same −18 LUFS / 100 ms, and its transient sits at 8.5 ms (`offsetMs`) instead of 58 ms.
Candidates were compared on measured duration / centroid / attack, not by ear — one-off script kept in
`_acceptance-3.8.0/build-highlight.py`, not shipped.

## Layered pop and chart

`pop` and `chart` were the two weakest sounds of the first library build (earshot CLAP match z 2.49 / 2.47, "weak"):
under narration they read as a faint "plip" and a thin sweep. The final build rebuilds both as **layered** designs in
`scripts/dev/build-sfx-library.py` (its LAYERS table):

| Event | Layers (earshot forge recipe #seed, gain) | Match z |
|---|---|---|
| `pop` | round low body `popin #14` (−3 dB) + bright bubble tick `pop #7` (0 dB) + trimmed sub hit `impact #6` (120 ms, −18 dB) | 3.01 strong |
| `chart` | upward tonal zip `zip #5` (0 dB) + `zip #0` 10 ms later (−2 dB) + landing thump `popin #10` at 200 ms (−8 dB) | 3.15 strong |

A rising four-note arpeggio for `chart` was tried and rejected (CLAP read it as "no match", z 0.95).
Rebuild only these two: `python scripts/dev/build-sfx-library.py --only pop,chart` (the other entries and
files are kept byte-for-byte).

## 调音：每个 cue 的 `gain` 与 `offsetMs`

- 每条 manifest 记录新增 `gain`（线性，把 cue 放到响度阶梯上：chapter −24 · success −25 · pop −25.5 · error / chart −26 · highlight / page −27 · place −26.5 · stamp −25 LUFS，全部比音乐床高 11–17 LU）与 `offsetMs`（文件开头到瞬态的距离）。
- 引擎（`src/sfx.ts`）按 `offsetMs` **提前**起播，瞬态落在视觉命中帧（±1 帧）；`page` 的命中点是转场第 3 帧（纸刚被掀起）。
- 去拥挤：两个 cue 间隔 ≥150 ms（5 帧，优先级高的留下）；任意 10 秒最多 4 个（≈24 次/分钟）。音乐床在每个 cue 命中前 2 帧到后 14 帧闪避到 45%。
- auto 片（story.json）只在真事件上出声：数字落定 `pop`、图表生长 `chart`、关键词第一次推近 `highlight`、答案揭晓 / 改之后出现 `success` / `pop`；章节 `chapter`、每次翻页 `page`。
- `validate-audio-levels.py` 每次出片打印一行「压人声 N 个（事件名）」：显式音效时刻正好落在某句旁白 `[start_ms, speech_end_ms]` 内的条数。自动音效（换章 `chapter`、翻页 `page`）落在换镜帧上、旁白还没开口，实测不产生重叠；会压到说话的只有作者在 story.json 里写的 `sfx`。**只报告不拦截**——少量压人是正常的动作拟音（图表生长、元素落位），全片都压才是问题。
- 维护者：`python scripts/dev/audit-sfx.py [--legacy]` 打分（时序 40 + 电平 30 + 音色 30），`python scripts/dev/tune-sfx.py` 修剪 + 写回 manifest（需 numpy / soundfile / pyloudnorm；普通用户不用跑）。`validate-audio-levels.py` 核对 `SFX_GAIN` / `SFX_OFFSET_MS` 与 manifest 一致。

## 离线质检（维护者可选，3.8.0）

earshot 的定位是**维护者离线质检**，不是运行时依赖——上传包只带成品音频、配方与许可；
普通用户渲染一支视频不得被要求下载 1.1GB 模型或装 PyTorch。

`python scripts/dev/sfx-earshot-audit.py`（缺 earshot 时打印安装提示并 exit 0，不挡出片）：

1. `earshot measure`（无模型、不联网）复核每个 OGG 的 LUFS / 真峰值 / 包络，
   与 `scripts/dev/audit-sfx.py`（numpy + pyloudnorm）的数字并排。两个工具实现不同，
   **LUFS ±0.5 LU / 真峰值 ±0.3 dBFS 以内属正常**；超了脚本会点名，要能解释差异来源。
2. `--mix <成片>` 时用 `earshot timeline` 看真实事件密度与命中点（配合 `--cues`）。
   **先分析、不改声音**：密度/命中点记录下来，改不改由人工盲听决定。

明确不做的三件事：

- 不用 `realness` / CLAP 分数单独决定入库——它们只作参考，必须保留人工盲听与无模型检查；
- 不因工具版本升级重生成整库（只有确有音色缺口才用 `sfx` / `forge` 出候选，
  且衍生配方必须保留源录音许可）；
- `critique` 不直接拿发布宣传片风格当目标——要先有「中文教学旁白 + 克制拟音」的自有 profile。

**验收口径**：同一音频新旧工具测量差异可解释；质检报告可复现（`--json`）；
生成候选经同条件盲听优于旧版才替换；无 earshot 的干净环境仍可正常出片。

## 三段盲听协议（P2-20 · 维护者）

电平合格 ≠ 听感合格。响度 / 峰值 / 削波抓不到三件事：
**旁白下拟音是否掩字**、**连续翻页是否机械**、**静音占位与真人声的动态差异**。
这三件只能用同一套耳朵、同一套段落反复听——段落固定，不能每次现挑。

```
python scripts/dev/listen-segments.py mix.wav out_dir
```

产出 `seg1-open.wav` / `seg2-turns.wav` / `seg3-close.wav` + `segments.json`（切点与打分表）：

| 段 | 取自 | 听什么 | 及格线 |
|---|---|---|---|
| 开场 | 0–20 s | 人声刚进来时拟音在不在、压不压字 | 可懂度 ≥4，关键辅音不被掩 |
| 连续转场 | 最密集的 ≥3 次翻页区 | 机械感、纸声是否同质 | 机械感 ≥3（轮换后应 ≥4） |
| 结论 | 末 20 s | 收束音效、配乐尾、最后一个字 | 可懂度 ≥4，疲劳 ≥3 |

打分 1–5 写进 `segments.json` 的 `verdict`，归档到工程。**先盲听、不改声音**——
改不改由人耳决定；工具只负责把「听哪三段」固定下来。

### 音色轮换（2026-11-01 起）

连续翻页若每次都是同一段纸声，3 次之后就机械。`page` 现在有三个同源微变体
（`page.ogg` / `page-b.ogg` / `page-c.ogg`，音高与滤波略不同、瞬态位置差 <0.5 ms、
响度差 <0.5 LU），`planSfx` 按出现次序轮换。变体元数据在 `sfx-manifest.json` 的
`variants[]`，与主文件同一套质量口径（sha256 / 峰值下限 / 响度容差 / 瞬态同步）。

### 动作音同步（验收：≤2 帧）

`offsetMs` = 文件开头到听感命中点的距离，引擎提前这么多起播，命中点就落在视觉帧上。
**命中点的量法是 5 ms RMS 最大值**（与 `scripts/dev/tune-sfx.py` 一致），
不能用「最大绝对值采样」——chart 是上升扫弦、chapter 是闪音，峰值在尾巴上，
用峰值判会误报 140 ms 误差。`validate-audio-levels.py` 现在会逐文件对账，
差 >2 帧（66.7 ms）即 P0。

### 随旁白 ducking：先盲听再决定

人声 −16 LUFS、拟音 −24…−27 LUFS、音乐床 ≈ −41 LUFS（且在每个 cue 下闪避到 45%）。
按阶梯，拟音已在人声下方 8–14 LU。**是否仍掩字由 seg1 盲听判定**：
若掩，优先下调该事件的 `gain` 阶梯（改 manifest + sfx.ts 两处同值），
而不是继续加音效数量；确有必要再做包络跟随的 ducking（需要旁白包络，属后续项）。
