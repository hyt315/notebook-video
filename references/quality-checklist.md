# Delivery acceptance checklist

## 目录

- [Story](#story)
- [Architecture](#architecture)
- [Visuals](#visuals)
- [Subtitle](#subtitle)
- [Audio](#audio)
- [File validation](#file-validation)
- [Deliverables（交付物与事实卡）](#deliverables-原文迁自-skillmd)
## Story

- A concrete, verified payoff or tension is visible within 1.5 seconds; an honest open loop follows by 8 seconds.
- Each scene has one main idea and one physical action.
- The visual story remains understandable without narration.
- The opening gives a concrete, verified payoff or tension before context, and the storyboard identifies a later evidence-based callback.
- A meaningful state changes every 2–4 seconds.
- The final message holds at least one second.

## Architecture

- React + TypeScript + Remotion is the primary renderer.
- TTS milliseconds convert once to integer frames.
- Subtitle, animation and sound share the same FPS convention.
- Fonts and media resolve before the first rendered frame.
- Action audio is declared with its visible action.

## Visuals

- Background, chapter, header and subtitle match the canonical example.
- Every scene declares one primary mode: `image-text`, `pure-text` or `pure-graphic`.
- Concrete subjects use original, supplied or licensed imagery when seeing the subject materially improves comprehension.
- Generated imagery contains no baked labels, charts, logos or UI text; exact information remains in Remotion.
- Every raster is registered in `visual-assets.json` with source, prompt/description, crop policy and rights.
- Image scenes synchronize recognition, callout, relation and conclusion instead of placing a static image beside unrelated copy.
- Generated images receive only restrained crop reveal or push-in motion; annotations move independently.
- Every independently moving object is an independent component.
- Every large object has one home zone and one destination zone.
- Unrelated cards keep at least 70px separation, including airborne shadows.
- The central corridor contains at most one dominant temporary transfer object.
- A continuous process preserves one task object and changes its state at real stations.
- Floating objects stay above lower bases.
- Slot occlusion begins only after a visible crossing.
- Inserted modules finish fully behind the front lip with no residual fragment.
- Temporary components exit completely; no half corner remains.
- Dynamic shadow changes only when paper lifts.
- In the official v9 engine, paper uses its locked lift-linked contact/environment shadow recipe; no component invents a conflicting shadow.
- In the official v9 engine, display, title, body, label and micro copy use its locked type scale.
- In the official v9 engine, system glyphs and emoji are not used as production icons; use its locked line-icon language.
- In the official v9 engine, the whole-film grade is static and restrained; no animated grain or moving light texture.
- In the official v9 engine, ordinary production edits stay inside `COPY`, narration, semantic captions, visual plan, registered image assets, timing and topic-specific scene objects.
- Data dashes move only during a real transfer and in the correct direction.
- Text-bearing paper has visible padding on all sides.
- Exact Chinese text and real brand assets are preserved.
- No malformed labels, invented logos or softened Chinese glyphs.
- No large accidental empty area during a spoken explanation.
- No clutter from unrelated dots, scraps, steam or continuous movement.
- No effect stack, miniature card pile or unused half-visible layer remains on screen.
- No global zoom, shake, animated noise, posterize or full-screen page turn.
- Shot camera: every shot declares one intent from the closed set (`establish` / `push-in` / `pull-back` / `pan-follow` / `reveal` / `micro-orbit` / `still`) plus an `anchor`; `scripts/validate-shot-motion.py` must prove the anchor stays fully visible at every keyframe (P0 = 0). Zoom ≤ 1.35 on shots carrying text. At least 3 camera moves per chapter and at least 3 distinct intents per film — a film with a frozen frame reads as page-turning.
- Scene skeletons: at least 3 of `Stage` / `Corridor` / `Split` / `Zoom`, and no two adjacent scenes share a skeleton (`scripts/validate-composition.py`).
- Visual media: at least 3 distinct media across the film (chart / console / code / graphic / text / metric), and every explanation scene carries at least one live component that changes state with the narration. A pure card-and-bullets scene is rejected.
- Density: every scene declares 3–5 functional zones and fills the lower quarter (bottom edge near y=876). An empty lower half is a PPT tell.
- Background readability: content that overlaps a locked background decoration zone (`theme.backgroundDecorZones`) must sit on a `CoverPanel`; the background bitmap itself stays untouched.
- Runtime overlap gate: after the first render, the console must show **no `OverlapGate` warnings** (text-vs-text overlap and paint-order occlusion, sampled every 15 frames). Intentional overlaps (shot handoff, header swap, metric value replacement) must be marked `data-gate-allow`; never use the allow-list to hide two different pieces of information colliding.
- Slot overflow gate (dev mode): **no `SlotGuard` warnings** — every component inside `StageFrame`'s main slot must be no wider than `mainW = w − pad×2 − railW − 18`.
- Motion: progress-like bars animate `scaleX` (never `width`); numeric readouts use `tabular-nums` with fixed fraction digits; every element's multi-property entrance uses different clocks (see motion-design.md).
- Anti-PPT Functional Components: Technical concepts (search, memory, context, contracts, embeddings, security) MUST use active animated components (`BrainwaveEEG`, `VectorRadarSonar`, `BM25TokenRibbon`, `HookMountBay`, `RedactionScanner`, `ChipContract`) rather than generic bullet text cards.

## Subtitle

- Bottom-pinned pure caption text is present in every scene (no bar, no torn contour).
- No dark border, black side mark, inner line, orange locator or blue ring.
- One centered line, WenKai Lite 44px (40px on 3:4).
- `CaptionFitGate` measures every fully revealed cue with the loaded WenKai font in the real render browser; every cue fits within the canvas safe width.
- Partial reveal does not shift horizontally (hidden full-width placeholder).
- Internal punctuation remains; trailing punctuation (`，。！？；、,.!?;:`) is strictly stripped and hidden visually via `cleanFull` and gated character length. Trailing punctuation mark on screen is an immediate rejection flag.
- Caption segmentation is explicitly `semantic`, never `draft-character-count`.
- Every model/product name, benchmark, number-plus-unit expression and fixed technical term is listed in the protected-phrase manifest.
- No protected phrase crosses a cue boundary; no ASCII identifier is split between cues.
- Cue words flatten to the exact TTS word stream.
- Caption timing leads measured speech by no more than about 80ms.

## Audio

- Correct voice and complete narration.
- No hidden voice delay.
- Effects land on visible actions.
- Speech remains dominant.
- Integrated loudness is about -16 LUFS.
- True peak is no higher than -1.5dBTP.

## File validation

- H.264 video and AAC audio are present.
- 2560×1440 at native 30fps unless the user explicitly requested a genuinely native high-frame-rate production.
- Audio is 48kHz stereo.
- Video duration includes at least 0.7 seconds after narration.
- No black frames or truncated ending.
- No unintended scaling or softening pass.
- Contact sheet includes every scene.
- Films over 60 seconds include at least 24 evenly spaced frames plus dense motion sheets for the two most complex movements.
- Opening, scene boundaries, longest caption, hover/insert midpoints and closing frame are inspected manually.
- Opening range 0–360 is inspected at 0.5s, 2s, 4s, 8s and 10s; the primary claim is visible by 1.5s and the deferred question is paid off later.

Do not update the skill from a design proposal. Update only after the user approves the actual rendered film.

## Deliverables (原文迁自 SKILL.md)

Unless the user asks for less, deliver:

1. narration and time-coded storyboard (derived from the shot table);
2. a visual plan — for v2.9 this is the shot table itself: skeleton, media, live components, camera intent, anchor, zones, bottom-fill, transition, entry, beats;
3. semantic part manifest with layer and exit contracts;
4. `visual-assets.json` with source, prompt summary, crop policy and rights for every raster;
5. Chinese narration plus word timing JSON;
6. one-line semantic caption cues plus a protected-phrase manifest;
7. delivery-canvas H.264/AAC MP4 (2560×1440 for 16:9);
8. contact sheet and motion checks for long films;
9. editable source ZIP with fonts, licenses, audio and manifests;
10. delivery fact card verified against the baseline table below.

### 交付指标事实卡 (Fact Card)

| 层级 | 检查项 (Metric/Item) | 测量实值 (Value) | 正常基线 (Baseline) | 状态判定 (Status) |
|---|---|---|---|---|
| L1 基础层 | 交付画幅与帧率 | 2560×1440 | 锁定 30fps 原生无重复帧 | 🟢 正常 |
| L1 基础层 | 响度与音频混音 | −16 LUFS / −1.5 dBTP | 48kHz 立体声 AAC | 🟢 正常 |
| L2 核心层 | 字幕与台词对齐 | 词级整帧同步 (msFrame) | 零断行拆分/零边缘伪影 | 🟢 正常 |
| L3 校验层 | 黑帧与图层穿透 | 0 处黑帧 / 零残留碎片 | 所有元件完整离场与遮挡 | 🟢 正常 |
| L3 校验层 | 构图门禁 | P0 = 0 | 骨架相邻不同款 / 活性组件覆盖 / 介质 ≥3 | 🟢 正常 |
| L3 校验层 | 重叠门禁 | OverlapGate 零警告 | 有意覆盖须标 `data-gate-allow` | 🟢 正常 |

Do not stop at prompts, still images, a silent animation or an unvalidated render.
