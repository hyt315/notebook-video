# Official aesthetic system

This document defines the aesthetic layer preserved by `warm-ivory-remotion-2k30-v8-performance`.
This package contains one official aesthetic track and one canonical example project.

## Locked production grammar

The v8 performance system preserves the actual four-act physical narrative, fixed camera, subtitle geometry, native 30fps paper motion, declarative audio tree, asset gate and final draw order. Do not introduce generic `Hero`, `Compare`, `Pipeline` or `Summary` scene families. Reuse the physical grammar demonstrated by the official example.

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
5. topic-specific scene objects that preserve the same physical ownership and motion grammar.

Stable semantic IDs must remain separate from display labels. Changing visible copy must not break scene branching, icon choice, z-order, transfer paths or slot occlusion.

## Visual rules

- Preserve the spacious four-act composition and one hero action per zone.
- Keep the clean torn-paper subtitle at one centered 40px line.
- Use browser-native caption measurement after the exact font is loaded.
- Use the official palette and type scale; do not invent per-scene styling.
- Use lift-linked paper shadows only for moving paper.
- Keep the grade static and restrained.
- Use the official line icons instead of system glyphs or emoji.
- Preserve the same persistent task-card, shared-track and physical-slot logic.

## Future updates

For future aesthetic changes, work in a disposable project copy, render the complete film, obtain user approval, and only then overwrite the official example and contract.
