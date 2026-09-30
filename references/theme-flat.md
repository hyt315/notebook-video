# Optional visual treatment: flat

The `flat` implementation in `assets/lecture-template/src/theme/flat.tsx` offers clean geometric shapes, restrained edges, and simple color blocks. It can serve direct comparison, data, process, and low-decoration diagrams. Flat does not mean “remove important detail”; the right amount of information depends on the lesson.

## Use when it helps

Start with a clear background, a small semantic palette, stable baselines, and precise labels. A chart or relationship may need no card at all. A character, monster, shadow, gradient, pill subtitle, or corner decoration is optional. Avoid adding a mascot or floating shapes unless they help explain or orient the viewer.

The former per-canvas mascot background was reviewed on the bundled eight-shot sample at 390px. Its large bottom-right character appeared behind the 3:4 conclusion area, so the template now uses a quiet cool gray-blue field. The white cards, semantic colors, hard-offset shadows, and blue subtitle treatment remain the `flat` visual language. The old `public/bg-flat-*` bitmaps are retained as inactive source assets, not loaded by this theme. Keep text live and inspect actual glyph size/contrast at output dimensions.

## Boundaries

Choose colours for meaning and contrast, not to satisfy a prescribed rotation. A fill color that fails contrast should not be used behind small white text. Gridlines, axes, reference labels, and baselines are part of the data when needed. Still and sparse frames are valid when they make the comparison clearer.
