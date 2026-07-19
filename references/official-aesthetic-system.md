# Official aesthetic system

This document defines the aesthetic layer preserved by `warm-ivory-remotion-2k30-v9-visual-director`.
This package contains one official aesthetic track and one canonical example project.

## Locked production grammar

The v9 system preserves the fixed camera, subtitle geometry, native 30fps paper motion, declarative audio tree, asset gate and final draw order while allowing the scene grammar to follow meaning. Before storyboarding, select `image-text`, `pure-text` or `pure-graphic` for each scene. Read [visual-director.md](visual-director.md).

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
- Keep the clean torn-paper subtitle at one centered 40px line.
- Use browser-native caption measurement after the exact font is loaded.
- Use the official palette and type scale; do not invent per-scene styling.
- Use lift-linked paper shadows only for moving paper.
- Keep the grade static and restrained.
- Use the official line icons instead of system glyphs or emoji.
- Preserve the same persistent task-card, shared-track and physical-slot logic.

## Future updates

For future aesthetic changes, work in a disposable project copy, render the complete film, obtain user approval, and only then overwrite the official example and contract.
