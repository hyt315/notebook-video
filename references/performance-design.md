# Performance design contract

## Contents

1. Frame-rate policy
2. Scene lifetime
3. Motion implementation
4. Static surfaces and measurement gates
5. Concurrency
6. Fast iteration
7. Acceptance rules

## 1. Frame-rate policy

Use one native frame rate through the whole default pipeline:

- motion: 30fps;
- Remotion composition: 30fps;
- H.264 delivery: 30fps.

Do not author 30 unique states and export them as duplicated 60fps frames. A 60fps container is allowed only when the visible motion is also authored at native 60fps, such as very fast camera movement, dense particles, real 60fps footage or an explicit user request. In that mode, update timing, duration, captions, audio cues and validation together; never use post-export frame duplication as a quality upgrade.

For an intentional stop-motion beat inside a 30fps film, quantize only that component to 15fps so each pose holds for two frames. Do not lower the whole composition.

## 2. Scene lifetime

Unmount scenes that cannot contribute pixels to the current frame. Do not keep a whole film mounted and hide inactive scenes with `opacity: 0`.

Use frame guards or short overlapping scene ranges. Mount one scene during normal playback and at most two during a transition. Keep shared chrome, subtitle, audio and static background outside scene guards.

The canonical exemplar uses global-frame guards because its scene components consume global design-time frames. If using Remotion `Sequence`, pass local time deliberately and do not accidentally shift global cue constants.

When extending duration with a timeline scale, use one scaled design-frame helper for **both** scene guards and internal motion. Raw delivery frames may not be used by a mount condition. Scale action-audio sequence starts through the same conversion. A scene that is visually scaled but mounted against raw frames will disappear before the film ends even though its internal animation is correct.

## 3. Motion implementation

Keep stable layout coordinates in `left` and `top`. Express per-frame movement through `transform: translate3d(...)`, combined with rotate and scale in one transform string. Prefer opacity and transforms over per-frame changes to `left`, `top`, `width`, `height`, margins or grid tracks.

Do not add `will-change` to every element. Use it only on a few long-lived moving layers when profiling shows a benefit. Preserve exact slot occlusion and z-order even when converting movement to transforms.

## 4. Static surfaces and measurement gates

Keep paper texture, grade, grid and fixed shadows deterministic and static. Do not animate noise. Reuse CSS gradients or pre-render a static bitmap only when it is visually identical at 2560×1440.

Wait for fonts and media before rendering. Keep the asset gate. Measure every subtitle after the exact font loads, then unmount the off-screen measurement tree after it passes. Never remove validation work merely to shorten startup.

## 5. Concurrency

Default to half the available logical CPUs, clamped to 2–6 workers. Higher concurrency can slow a 2K browser render through CPU, memory and encoder contention.

Run `benchmark-render` once per machine or after a major environment change. It renders the same 90-frame opening sample with several worker counts and reports the fastest setting. Export `REMOTION_CONCURRENCY` to reuse that result. Benchmark a representative dense range manually if the opening is unusually simple.

## 6. Fast iteration

Use `render-range` for changed scenes, subtitle checks and motion reviews. Keep scene boundaries in a manifest or storyboard so review ranges are reproducible. Do not render the full film after every small edit.

For long productions, keep scenes modular so unchanged sections can later be rendered and assembled independently. Treat segment concatenation as an advanced workflow: all segments must share codec, resolution, frame rate, pixel format and audio format, and transitions must not cross segment boundaries. Always perform one full final render unless a validated concat pipeline is already present in the project.

## 7. Acceptance rules

Reject a speed optimization if it changes layout, type, palette, subtitle geometry, object count, semantic timing, physical occlusion, audio synchronization or final 2K sharpness.

Accept a tiny cadence difference only when moving from the obsolete 20fps stepped pose system to native 30fps motion; this change should be smoother, not rougher. Compare at least one dense motion range and one subtitle-heavy range before final delivery.
