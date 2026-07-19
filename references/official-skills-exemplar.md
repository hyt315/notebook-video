# Official Visual Director exemplar

The binding exemplar is a 30-second Remotion project configured at native 2560×1440 and 30fps with native 30fps physical motion. It preserves the established aesthetic complexity while demonstrating the three primary scene modes: image-plus-text, pure text and pure graphic.

## Required starting point

Run `node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project <PROJECT_DIRECTORY>`. It copies the exact runnable source, pinned dependencies, narration timing, open-license fonts and procedural action sounds.

Canonical sources:

- `assets/example-project/src/index.tsx`
- `assets/example-project/package-lock.json`
- `references/locked-style-contract.json`


## What remains reusable

Keep these components and behaviors:

- `AssetGate`, `CaptionFitGate`, `Background`, `Paper`;
- clean white `Subtitle` without a dark border;
- stable `Chrome` chapter/header system;
- directed rail paths with dash offset only during transfer;
- stepped physical frame helper `q`;
- dynamic shadow tied to actual lift;
- declarative `Sound` tree;
- integer-frame caption preprocessing;
- complete exit of obsolete components.
- `Img` assets preloaded through `AssetGate`;
- generated-image callouts kept as independent Remotion layers;
- `manifests/visual-assets.json` provenance and crop contracts;
- one semantic action per spatial zone;
- one persistent task card for a continuous process;
- a shared visible track with state changes at real stations;
- module convergence to one measured slot, then full occlusion behind its front lip;
- large readable objects distributed across the wide canvas instead of a central effect pile.

Topic-specific heroes, copy, props and scene metaphors must change for the new subject.

## Approved visual story

The exemplar demonstrates the intended production grammar:

1. contrast a stable base with a disordered effect stack;
2. reorganize effects into an object system with explicit ownership;
3. show independent script, voice, caption and visual work zones, with the visual zone combining an original image and live callouts;
4. move one task card through a shared track and change its state at each station;
5. converge independent modules into a physical assembly slot with correct occlusion;
6. validate and end with concrete MP4, project and QA artifacts.

The same engineering helpers may be adapted to other topics. The four-act subject matter is only an exemplar; production scenes must choose their primary visual mode from the narration meaning. Read [visual-director.md](visual-director.md).

## Rejection conditions

Reject the render if:

- any non-Remotion visual renderer is introduced without explicit user approval;
- a generated image is treated as the complete video instead of an asset animated and explained by Remotion;
- exact labels or diagrams are baked into generated imagery;
- a raster asset lacks provenance, crop policy or redistribution notes;
- the background, subtitle or chapter system is reconstructed from memory;
- the subtitle gains dark side marks, a straight border or an inner wave;
- shadows remain identical while cards lift;
- data lines move continuously without a transfer event;
- cards disappear by clipping and leave a visible fragment;
- temporary cards overlap unrelated zones or collect in a central pile;
- a process spawns disconnected replacement cards instead of preserving object continuity;
- an insertable part stays above the front lip after crossing the slot;
- action sounds are added in an unrelated post-production timeline;
- fonts may render before the preload gate resolves;
- the output lacks actual video QA.
