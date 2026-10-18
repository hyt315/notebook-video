# SFX library

The template ships a small, finished sound-effect library so ordinary AI tools (Windows included) never have to
generate, download or tune sounds. Files live in `assets/lecture-template/public/sfx/lib/`, described by
`public/sfx/sfx-manifest.json` (sha256, duration, loudness, peak, source recipe, license, intended use).

## Events

| event | file | when the engine uses it |
|---|---|---|
| `whoosh` | `sfx/lib/whoosh.ogg` | start of every non-chapter shot (transition / handoff) |
| `pop` | `sfx/lib/pop.ogg` | first beat of a shot (first element appears) |
| `click` | `sfx/lib/click.ogg` | middle beats of plain graphic/text shots (alternates with `highlight`) |
| `typing` | `sfx/lib/typing.ogg` | middle beats when `media` has `code` or `console` |
| `chart` | `sfx/lib/chart.ogg` | middle beats when `media` has `chart` or `metric` |
| `highlight` | `sfx/lib/highlight.ogg` | last beat of a non-conclusive shot; alternating middle beats |
| `success` | `sfx/lib/success.ogg` | last beat when `live` has Checklist / StampSeal / VerdictBar / StampBanner / MetricGrid / CheckBadge, or `move` is 收束/结论 |
| `error` | `sfx/lib/error.ogg` | beat 1 of a shot with a `misconception` and ≥ 3 beats |
| `chapter` | `sfx/lib/chapter.ogg` | 2 frames into each chapter's first shot |
| `riser` | `sfx/lib/riser.ogg` | ends exactly on each chapter start after the first (starts 45 frames earlier) |
| (bed) | `sfx/lib/bed.ogg` | optional quiet music bed, looped under the whole film |

Priority when two cues fall within 6 frames: chapter > success > error > riser > whoosh > chart > typing > highlight > pop > click.

## Override per shot (manifests/shots.json)

```json
"sfx": "none"                                     // no sound for this shot
"sfx": [{"event": "success", "beat": 2}]           // replace the automatic cue on beat 2
"sfx": [{"event": "error", "at": 40, "vol": 0.3}]  // add a cue at local frame 40
"sfxAuto": false                                   // only the explicit cues above
```

`resolve-shots.py` validates the field and passes it into `src/shots.ts`; the engine reads it in `planSfx`.

## Levels

All one-shots: -18 LUFS (K-weighted, 100 ms blocks), sample peak ≤ -1 dBFS, mono 48 kHz Ogg Vorbis (4–15 KB each).
Mix gains in `SFX_GAIN` (0.34–0.55) keep them 8–12 LU under narration at -16 LUFS. `validate-audio-levels.py`
checks hashes against the manifest, peaks, the loudness tolerance, the event/file mapping in `src/sfx.ts` and the
gain range.

## Provenance and rebuild (maintainers only)

Rendered in code with **earshot** 0.2.0 (`earshot forge` recipes; https://github.com/Leonxlnx/earshot, MIT) — no
recorded samples — and quality-checked with `earshot rank` / `earshot match` (CLAP). License: CC0-1.0.
Users never install earshot. To rebuild: `python scripts/dev/build-sfx-library.py` (needs torch CPU + earshot).

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

- 每条 manifest 记录新增 `gain`（线性，把 cue 放到响度阶梯上：chapter −24 · success −25 · pop −25.5 · error / chart −26 · highlight −27 · whoosh −27.5 · riser −28 · click −28.5 · typing −30 LUFS，全部比音乐床高 11–17 LU）与 `offsetMs`（文件开头到瞬态的距离）。
- 引擎（`src/sfx.ts`）按 `offsetMs` **提前**起播，瞬态落在视觉命中帧（±1 帧）；whoosh 的命中点是转场中点（+7 帧），riser 的命中点是章节首帧。
- 去拥挤：两个 cue 间隔 ≥150 ms（5 帧，优先级高的留下）；任意 10 秒最多 4 个（≈24 次/分钟）。音乐床在每个 cue 命中前 2 帧到后 14 帧闪避到 45%。
- auto 片（story.json）只在真事件上出声：数字落定 `pop`、图表生长 `chart`、代码出现 `typing`、关键词第一次推近 `highlight`、答案揭晓 / 改之后出现 `success` / `pop`；章节 `chapter` + `riser`、镜间 `whoosh`。
- 维护者：`python scripts/dev/audit-sfx.py [--legacy]` 打分（时序 40 + 电平 30 + 音色 30），`python scripts/dev/tune-sfx.py` 修剪 + 写回 manifest（需 numpy / soundfile / pyloudnorm；普通用户不用跑）。`validate-audio-levels.py` 核对 `SFX_GAIN` / `SFX_OFFSET_MS` 与 manifest 一致。
