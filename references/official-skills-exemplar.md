# Official exemplar

The binding exemplar is the lecture template itself: an 8-shot, 1150-frame Remotion film configured at native 2560×1440 and 30fps (design space 1920×1080), skinned by one of two locked themes, `flat` (default) and `cel`. It demonstrates the four scene skeletons, five camera intents and the full gate stack on one topic (an open-source onboarding explainer).

The v4.0 `--classic` warm-ivory example project (`example-project`, the old visual-director exemplar) was removed in v4.1.0. Its paper look is gone; nothing in the skill copies or validates it any more.

## Required starting point

Run `node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project <PROJECT_DIRECTORY> [--style=flat|cel]`. It copies the exact runnable source, pinned dependencies, caption timing, the three locked backgrounds per theme, open-license fonts and procedural action sounds.

Canonical sources:

- `assets/lecture-template/src/index.tsx` (engine: gates, subtitle, chrome, backdrop, audio tree)
- `assets/lecture-template/src/scenes.tsx` (scene layer: copy this structure, replace the content)
- `assets/lecture-template/src/theme/` (the two locked skins)
- `assets/lecture-template/package-lock.json`
- `references/locked-style-contract.json`

## What remains reusable

Keep these components and behaviors:

- `AssetGate`, `CaptionFitGate`, `Background`, `Paper`;
- the theme's `SubtitleChrome` with the per-word reveal from `Subtitle`;
- stable `Chrome` chapter/header system;
- the backdrop rule: chapter shots on the `chapter` background, dense shots (zones ≥ 4) on `quiet`, the rest on `main`, with a `bg` override in the shot table;
- stepped physical frame helper `q`;
- dynamic shadow tied to actual lift;
- declarative `Sound` tree;
- integer-frame caption preprocessing;
- complete exit of obsolete components;
- `manifests/visual-assets.json` provenance and crop contracts for every raster;
- one semantic action per spatial zone;
- large readable objects distributed across the wide canvas instead of a central effect pile.

Topic-specific heroes, copy, props and scene metaphors must change for the new subject.

## Rejection conditions

Reject the render if:

- any non-Remotion visual renderer is introduced without explicit user approval;
- a generated image is treated as the complete video instead of an asset animated and explained by Remotion;
- exact labels or diagrams are baked into generated imagery;
- a raster asset lacks provenance, crop policy or redistribution notes;
- the background, subtitle or chapter system is reconstructed from memory;
- a full-frame translucent wash is laid over the background (it ghosts the corner characters);
- shadows remain identical while cards lift;
- cards disappear by clipping and leave a visible fragment;
- temporary cards overlap unrelated zones or collect in a central pile;
- action sounds are added in an unrelated post-production timeline;
- fonts may render before the preload gate resolves, or any text depends on a system font;
- the output lacks actual video QA.
