# SFX library (v4.3)

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
