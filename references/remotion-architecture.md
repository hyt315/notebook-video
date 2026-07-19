# Remotion architecture contract

## Contents

1. Project structure
2. Deterministic data flow
3. Required components
4. Scene and layer ownership
5. Audio ownership
6. Rendering and fallback rules

## 1. Project structure

Use the canonical tree copied by the cross-platform `scripts/notebook-video.mjs new-project` command:

```text
project/
├── src/index.tsx
├── src/caption-cues.json
├── public/
│   ├── fonts and licenses
│   ├── narration.mp3
│   ├── illustrations/
│   └── sfx/
├── audio/narration.mp3.json
├── manifests/
│   ├── semantic-caption-lines.txt
│   ├── protected-caption-phrases.txt
│   ├── caption-cues.json
│   ├── asset-manifest.json
│   └── visual-assets.json
├── narration.txt
├── storyboard.md
├── package.json
└── renders/
```

Remotion is the only visual renderer. Python is limited to validation and deterministic data conversion.

## 2. Deterministic data flow

Use this order:

1. narration text;
2. visual-mode decision during storyboarding and image-capability check;
3. generated, supplied or native support-art plan plus raster provenance;
4. TTS audio plus measured word milliseconds;
5. editor-authored semantic caption lines and protected phrases;
6. semantic cues bound to exact TTS words and validated against protected boundaries;
7. one-time millisecond-to-frame conversion;
8. scene cut frames and object cue frames;
9. React component tree;
10. Remotion frame render;
11. FFmpeg loudness normalization and validation.

Define delivery and design-time frame rates explicitly. Keep both at 30fps by default. Convert timing at module load or in a preprocessing script:

```ts
const msFrame = (ms: number) => Math.round(ms * FPS / 1000);
const cues = rawCues.map((cue) => ({
  ...cue,
  startFrame: msFrame(cue.start_ms),
  endFrame: msFrame(cue.speech_end_ms),
  words: cue.words.map((word) => ({
    ...word,
    startFrame: msFrame(word.start),
    endFrame: msFrame(word.end),
  })),
}));
```

Never recompute timing differently in subtitles, animation and sound.

## 3. Required components

Copy rather than recreate:

- `AssetGate`: delays render until fonts and media are ready.
- `Img`: renders registered raster support art while callouts remain separate components.
- `Background`: fixed page, grid and static texture.
- `Paper`: owns its surface, outline and dynamic shadow.
- `Subtitle`: fixed white torn input without a dark border.
- `Chrome`: stable chapter and technical header.
- `Sound`: narration and action effects with frame-based `Sequence`.

Keep the component implementations in the canonical example until the user approves a future rendered replacement. The preserved aesthetic system keeps the same component grammar and separates stable semantic IDs from editable display copy.

## 4. Scene and layer ownership

Use a native 30fps output and 30fps design timeline. Keep the helper explicit so an intentional native-rate or longer-duration variant can update the whole timing boundary consistently:

```ts
const BASE_FPS = 30;
const FPS = 30;
const MOTION_FPS = 30;
const TIMELINE_SCALE = 1;
const designFrame = useCurrentFrame() * BASE_FPS / FPS / TIMELINE_SCALE;
const step = BASE_FPS / MOTION_FPS;
const q = (frame: number) => Math.floor(frame / step) * step;
const deliveryFrame = (frame: number) => Math.round(frame * FPS * TIMELINE_SCALE / BASE_FPS);
```

Text reveal, measured TTS boundaries, physical paper poses and action audio use native 30fps frames. Keep timing conversion centralized. For a local stop-motion beat, quantize that component to 15fps; do not change the composition.

### Duration extension invariant

The default scene is a 900-frame design timeline. If narration requires a longer delivery while retaining the same authored scene geometry, set `TIMELINE_SCALE` and `DURATION` together (`DURATION = 900 * TIMELINE_SCALE`). Every scene mount guard, animation cue, caption boundary and action-audio `<Sequence from>` must derive from `useCurrentFrame()`, `q()` or `deliveryFrame()`; never read raw `useRawCurrentFrame()` in a scene. Before a full render, range-render across every scene boundary and inspect the final frame. This prevents an extended composition from unmounting all scenes or leaving sound cues at the original timing.

Mount only scenes that can contribute pixels. Keep one scene mounted normally and at most two during a transition. Never hide every inactive scene with opacity. Read [performance-design.md](performance-design.md).

Use start-inclusive and end-exclusive scene windows. A scene group owns its image, text, SVG and annotation layers. When the subject changes, unmount the outgoing group at its end frame; do not leave a hidden raster, callout or shadow under the next scene.

Assign one owner to every visible object. A parent that uses transform, opacity, filter or isolation creates a stacking context; therefore sibling z-index values do not escape it. Keep objects that must overlap across a container in the same intended stacking context.

Model entry, active and exit phases. At exit, move the whole component beyond the frame or set opacity to zero only after it is fully outside. Do not clip a portion and leave the remainder visible.

## 5. Audio ownership

Use `@remotion/media` `<Audio>` for narration. Use `<Sequence from={frame}>` for action sounds. Keep the cue in the same file or data source as the visible action frame.

Do not build the action timeline in an unrelated shell script. FFmpeg may normalize and encode after Remotion, but it must not introduce an undocumented narration delay.

## 6. Rendering and fallback rules

Render with the pinned package versions in the canonical `package-lock.json`. The cross-platform Node launcher is authoritative on Windows, macOS and Linux; shell wrappers are only aliases and must not contain separate render logic. The bundled network-interface shim is an opt-in compatibility aid only; enable it with `REMOTION_USE_NETWORK_SHIM=1` when a restricted runtime requires it, never by default. If a cloud environment cannot run Remotion, report the constraint before changing engines. Do not silently fall back to another renderer, real-time browser capture or generated video clips because their output will not match the approved system.

Use website capture only when the user explicitly asks to record an existing interactive site; see `html-capture.md`.
