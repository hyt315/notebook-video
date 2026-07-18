# Official Final Motion System exemplar

The binding exemplar is the 30-second “Final Motion System” Remotion project, configured at native 2560×1440 and 30fps with native 30fps physical motion. It preserves the established aesthetic complexity while avoiding duplicate frames and inactive-scene work.

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
- one semantic action per spatial zone;
- one persistent task card for a continuous process;
- a shared visible track with state changes at real stations;
- module convergence to one measured slot, then full occlusion behind its front lip;
- large readable objects distributed across the wide canvas instead of a central effect pile.

Topic-specific heroes, copy, props and scene metaphors must change for the new subject.

## Approved architecture story

The exemplar demonstrates the intended production grammar:

1. contrast a stable base with a disordered effect stack;
2. reorganize effects into an object system with explicit ownership;
3. show independent script, voice, caption and visual work zones;
4. move one task card through a shared track and change its state at each station;
5. converge independent modules into a physical assembly slot with correct occlusion;
6. validate and end with concrete MP4, project and QA artifacts.

The same grammar may be adapted to other topics without mentioning software architecture.

## Rejection conditions

Reject the render if:

- any non-Remotion visual renderer is introduced without explicit user approval;
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
