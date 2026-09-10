# Official aesthetic system

This document defines the aesthetic layer preserved by `warm-ivory-remotion-2k30-v9-visual-director`.
This package contains one official aesthetic track and one canonical example project.

## Locked production grammar

The v9 system preserves the fixed camera, subtitle geometry, native 30fps paper motion, declarative audio tree, asset gate and final draw order while allowing the scene grammar to follow meaning. Before storyboarding, select `image-text`, `pure-text` or `pure-graphic` for each scene. Read `visual-director.md`.

Generated imagery is an optional input layer. When an authorized image-generation tool is available, use it for concrete subjects and promotional hero shots where it improves comprehension. Keep exact text, arrows, diagrams and timing in Remotion. A project must remain buildable with user-supplied, licensed or native SVG assets when image generation is unavailable.

## Locked aesthetic core

The following values and helpers are part of the official engine and are not ordinary content-editing surfaces:

- `C`: approved semantic palette roles;
- `TYPE`: display, title, body, label and micro typography scale;
- `AESTHETIC`: subtitle width, paper radius/outline, texture, grid and grade values;
- `paperShadow(lift)`: contact and environment shadow linked to real paper lift;
- `LineIcon` and `CheckBadge`: one consistent line-icon language;
- `Grade`: restrained static whole-film warmth and vignette.

Semantic colors must come from `C`; material-specific neutral shades may remain inside the locked component implementation. Do not introduce new inline semantic colors, system glyphs, emoji, independent shadows or animated grain. Small optical adjustments are allowed only when they preserve the official visual result.

## Ordinary editable surface

Ordinary production models should primarily edit:

1. the `COPY` block in `src/index.tsx`;
2. `narration.txt`;
3. semantic caption lines and protected phrases;
4. scene timing constants when required by narration;
5. the visual plan and `manifests/visual-assets.json`;
6. generated or supplied raster assets in `public/illustrations/`;
7. topic-specific scene objects that preserve the same physical ownership and motion grammar.

Stable semantic IDs must remain separate from display labels. Changing visible copy must not break scene branching, icon choice, z-order, transfer paths or slot occlusion.

## Visual rules

- Preserve spacious composition and one hero action per zone; scene count follows the content.
- Choose image-plus-text, pure text or pure graphic mode from meaning rather than repeating one scene family.
- Treat generated bitmaps as animated assets, never as the finished scene.
- Keep exact labels and diagrams outside the bitmap as live Remotion layers.
- Record source, prompt summary, crop policy and rights for every raster asset.
- Keep the bottom-pinned pure caption text at one centered line (no torn bar).
- Use browser-native caption measurement after the exact font is loaded.
- Use the official palette and type scale; do not invent per-scene styling.
- Use lift-linked paper shadows only for moving paper.
- Keep the grade static and restrained.
- Use the official line icons instead of system glyphs or emoji.
- Preserve the same persistent task-card, shared-track and physical-slot logic.

## Future updates

For future aesthetic changes, work in a disposable project copy, render the complete film, obtain user approval, and only then overwrite the official example and contract.

## Locked official elements (原文迁自 SKILL.md)

Keep these official elements locked until the user approves a future rendered replacement:

- React + TypeScript + Remotion rendering core;
- locked premium motion contracts shipped in the template: `JumpInText` per-glyph 3D flip titles, `WaveText` letter-wave CTA typing, multi-keyframe figure roll-ins, per-word subtitle reveal, and the v2.9 shot layer (see [shot-language.md](shot-language.md));
- fixed native 30fps motion, rendered and delivered on one of three locked canvases: 2560×1440 (16:9), 1920×1440 (4:3) or 1440×1920 (3:4 portrait), chosen once at kickoff;
- no duplicate-frame upconversion; use 60fps only when motion is authored natively at 60fps;
- mount only the active scene, with at most two scenes during a short handoff;
- animate moving objects with transforms instead of per-frame layout properties (**progress bars animate `scaleX`, never `width`**);
- bright layered warm-ivory notebook background;
- stable top-left chapter card and top-right technical header, both **outside** the shot camera;
- bottom-pinned pure caption text with per-word reveal, no decorative bar, no dark border or side artifacts;
- pure bottom subtitle with soft text shadow, no dark border, side marks, locator or ring;
- LXGW WenKai Lite as the unified CJK typeface plus Clash Display / Space Grotesk Latin accents;
- TTS word timing converted once to integer absolute frames;
- independent semantic parts with explicit z-order, entry and complete exit;
- a spatial density budget: one hero action per zone, no temporary stack in the center;
- a shot layer: every shot declares one camera intent from the closed set plus an `anchor` that `validate-shot-motion.py` must prove stays visible (restricted recipes, not free curves — and not frozen framing);
- four scene skeletons (`Stage` / `Corridor` / `Split` / `Zoom`) with **no two adjacent scenes sharing one**, and at least three per film;
- content→medium routing: at least three distinct visual media per film, and at least one live state-changing component per explanation scene (**a pure card-and-bullets scene is a gate failure**);
- a shot table that references narration cues instead of hard-coded frame numbers ([scene-skeletons.md](scene-skeletons.md));
- background readability via `CoverPanel`: the locked background bitmaps stay as they are, and content overlapping a declared decoration zone sits on a feathered backing plate ([media-routing.md](media-routing.md));
- shared-track continuity when one object changes state across several stations;
- real slot geometry: insertable parts cross the slot, move behind the front lip and disappear fully;
- declarative narration and action effects inside the Remotion component tree;
- font/audio/image asset preload gate before the first frame;
- a visual plan selecting pure text/graphic scenes by default, with image-plus-text only after the user accepts the add-on;
- optional generated imagery as preloaded Remotion assets with prompt, crop and rights records;
- H.264/AAC output, automated QA, contact sheets and editable source package.

Do not write an experimental change into this skill until the user sees the rendered film and explicitly approves it.
