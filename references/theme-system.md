# Theme system: optional visual treatments

The template currently implements four base treatments in `assets/lecture-template/src/theme/`: `paper` (CLI default), `cel`, `sticker`, and `flat`. They provide reusable palette, surface, type-support, and decorative assets. They are not four mandatory production genres, and a project does not need to demonstrate all four. A base treatment can stay consistent while individual diagrams, typography, or topic-specific art use another compatible visual language when that helps explain the material.

The CLI's `--style=<id>` selects the base theme implementation. A project may use that selector for a stable base; it does not force every scene to use theme extras or add decorative texture. Do not mix styles randomly or count styles as evidence of quality. Do not change shared theme code solely to satisfy a generic artistic preference; test an actual rendered example first.

## Bundled example background review

The official eight-shot example's three aspect ratios were previewed at 390px for each optional treatment. Keep the default `paper` field and the `cel` corner illustration unchanged; the latter matches the user's preference and remains outside the card/text fields. The old `flat` bitmap put a large mascot behind the 3:4 conclusion area, and the `sticker` grid/doodles occupied open process areas without conveying process information. Those two themes now use their existing pale base colors; keep flat's hard-offset color blocks and sticker's tape/card accents. Former `public/bg-flat-*` and `public/bg-sticker-*` files remain as inactive source assets and are not registered as rendered assets. No new raster art was needed.

## Invariants and practical checks

- Keep semantic color roles coherent. Use foreground/background combinations with adequate contrast. For ordinary text, WCAG 2.2 SC 1.4.3's contrast minimum is 4.5:1; for large text it is 3:1. Decorative palette colors are not automatically safe text colors.
- Preserve the output canvas geometry and caption-safe area unless deliberately creating and verifying a separate layout for that canvas.
- Make text, numbers, labels, and meaningful audio cues live/editable when possible. Do not raster-bake exact information that may change.
- Check background decoration behind real scene content. A `CoverPanel` or alternate crop is an option if content is actually obscured; empty-space filling is not a goal.
- Text and visual hierarchy must survive the intended playback size. The code's font tokens and design-space pixels alone do not prove phone readability.

## Reuse and dependencies

Project history distinguishes three boundaries: `scripts/*.py` use only the Python standard library; the Remotion template ships pinned open-source dependencies in its package lock; and a new unlisted dependency requires approval. Mature open-source components may be reused where licensed and helpful. “Zero dependency” does not mean hand-reimplement every component. A component should be evaluated by its licence, reproducibility, actual use in rendered frames, and explanatory contribution—not by the total number of components or styles.

When adding a dependency or asset, follow [dependency-policy.md](dependency-policy.md). No dependency has been added as part of this local review.
