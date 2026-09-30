# Canvas modes and validation status

A rendered aspect ratio is not merely a composition-size setting. Scene content, typography, subtitles and safe margins must be checked together. Composition registration is necessary but not sufficient: reusable helpers expose the active mode, and each scene must deliberately lay out its own content in that design space.

## Locked delivery specifications

| Parameter | 16:9 | 4:3 | 3:4 portrait |
| --- | --- | --- | --- |
| Composition | 2560×1440 | 1920×1440 | 1440×1920 |
| Design coordinate space | 1920×1080 | 1440×1080 | 1080×1440 |
| Scale | 4/3 | 4/3 | 4/3 |
| Subtitle left/right margin | 188 | 60 | 50 |
| Subtitle bottom margin | 34 | 34 | 40 |
| Subtitle safe width | 1334 | 1060 | 900 |
| Subtitle type size (WenKai Lite) | 44 | 44 | 40 |
| 390px-wide review viewport | 390×219 | 390×293 | 390×520 |

These values are defined in `assets/lecture-template/src/theme/canvas.ts`; `validate-visual-plan.py` cross-checks them against registered Composition dimensions and the theme's runtime subtitle offset. Once a project registers a secondary film Composition, the validator requires all three film IDs, their locked width/height values, and identical `durationInFrames` and `fps`.

## What was actually reviewed

### Bundled product template: official eight-shot example

The reusable lecture template now has registered 16:9, 4:3 and 3:4 film Compositions. Its shared camera, StageFrame/PhaseRail and Corridor helpers read the active design space; the official S1–S8 example separately reflows its content for each canvas instead of scaling or letterboxing the 16:9 page. Teaching copy, shot order, cues and the lesson's core relationships remain the same. Actual 390px review led to larger 4:3 secondary text in S4's repository comparison/evidence list and S6's skill labels/details, and larger 16:9 S4 comparison/evidence/explanation text; the wide comparison's two redundant summaries were shortened without changing the three README/LICENSE/CI teaching roles. S4's role notes and three evidence-item entrances were also retimed to complete before the cut. The comparison's losing-side text remains intentionally secondary and struck through, but the compounded opacity fade was reduced so that supporting explanation does not disappear at phone size.

All eight scenes of the official example were rendered as complete 1150-frame, 30 fps, silent H.264 videos in all three locked dimensions. Each mode has a 390px-wide, eight-shot contact sheet plus a full sequence of all seven scene boundaries (before / cut / after). The render also ran CardFitGate, OverlapGate, ClippingGate and CanvasBoundsGate. A first parallel render reported an isolated S2 vertical state-label overlap and a 4:3 bounds warning that did not reproduce in an exact-frame or 650–660 single-worker trace. The 3:4 state label was then anchored to its own prior station during transitions, and final full-film verification is run serially so the DOM-measuring gates inspect a stable frame.

Review outputs: `../../notebook-video-review/audit/official-template-final/` (full MP4s and per-mode logs) and `../../notebook-video-review/audit/official-template-final/mobile-390/` (390px shot and cut-boundary contact sheets).

### Separate comparison fixture: five-shot lesson sample

The five-shot teaching sample is an external audit fixture under `../../notebook-video-review/after-project/`, not the bundled eight-shot product example. Its original 16:9 content and lesson are retained; its own 4:3/3:4 scene variants are only used to compare the same five shots/cues across aspect ratios. The fixture was fully rerendered as a 900-frame, 30 fps, silent H.264 film in all three dimensions, with its own 390px contact sheets, hard-cut checks, and text-boundary / overlap / clipping gates. It is not evidence that every customer-authored film will auto-reflow.

Review outputs: `../../notebook-video-review/audit/aspect-final/` (full MP4s and per-mode logs) and `../../notebook-video-review/audit/aspect-final/mobile-390/` (390px previews and hard-cut sheets). The pre-reflow diagnostics remain under `../../notebook-video-review/after-project/renders/aspect-diagnostic/mobile-390/`.

## How to use these modes

1. Register the intended delivery Composition at the exact dimensions above. Do not resize or letterbox a 16:9 page and call it an aspect adaptation.
2. Read the active canvas mode through `useCanvas()` in each scene. Place and size the visual carrier, comparison, process, labels and conclusions deliberately for that design space; shared helpers such as `StageFrame`, `PhaseRail`, `Corridor` and camera safety checks accept mode-aware geometry.
3. Preserve the teaching relationship and the original cue timing when reflowing. A comparison may remain side-by-side at 4:3 and stack in 3:4; a process may change from horizontal to vertical while retaining its labels, state and order.
4. Keep subtitle text inside that mode's `safe` width and position its strip with the matching bottom margin. Check measured captions as well as the visible frame.
5. Render the complete film and inspect representative 390px frames, including every scene and scene boundaries. A valid canvas table, unit test, or design-pixel font value does not prove that the finished output is readable.
6. Treat whitespace and stillness as valid when the visible diagram continues to carry the narrated lesson. Do not add motion or objects to fill unused canvas.

## Scope and remaining limits

Three-mode support covers the registered runtime, shared helpers, and bundled eight-shot example; it does not automatically redesign arbitrary scenes in a new project. The five-shot fixture is reported separately above and must not be confused with the product template. The frame review was an agent self-review, not a blinded viewer study, and no real-phone or other physical-device test was performed. Audio, TTS, synchronization, phrase timing and learning outcomes remain outside this visual-only validation. No universal minimum design-pixel font size is declared: check the actual 390px target output for each text role and preserve non-cropping, non-overlap and subtitle-safe-area boundaries.
