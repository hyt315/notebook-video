# Theme contract: cel (anime cel-shading storyboard)

Status: LOCKED. This theme ships fully implemented in `assets/lecture-template/src/theme/cel.tsx`. Production runs select it with `new-project ./dir --style=cel` and never edit the theme file. Read this document instead of the other theme docs; the three style contracts are mutually exclusive by design (progressive disclosure).

## Design language

Anime cel-shading storyboard: thick ink outlines, flat saturated fills, hard offset shadows, halftone dots and speed lines. Energy is loud and graphic.

## Locked tokens (do not invent alternatives)

- Canvas: identical to the shared canvas contract (16:9 / 4:3 / 3:4). Layout coordinates are unchanged from the default; only skin and decoration change.

- Base surface: pure bright white `#fdfdfb` paper; cards pure white `#ffffff`. Never tinted cream — the ink contrast carries the style, not a warm base.

- Ink: `#14110f` for outlines and body text.

- Accents: red `#e8382a` (primary/orange slot), blue `#2b6de8`, green `#24bc6e`, yellow `#f2b721` (gold slot). Blue and red are the co-leads (same saturation ≈80 / lightness ≈54 step); green and gold are derived on the same step — never invent off-step colors.

- Card skin: `2.5px` solid ink border, `10px` corner radius, hard offset ink shadow `3px 3px 0` (grows with lift, never blurs). Every card carries a deterministic micro-tilt of ±0.35° hashed from its position — the same card always keeps the same tilt, and scene motion transforms compose on top of it. Borders must never exceed 2.5px to avoid clunky black slab appearance.

- Background (LOCKED fixed raster): one AI-generated image per canvas ratio, selected automatically from `public/bg-cel-<169|43|34>.jpg` (`16:9` 2560×1440, `4:3` 1920×1440, `3:4` 1440×1920 — pixel-exact, no crop, no stretch). The image carries the complete background language: aged near-white paper with print grain, halftone dot fields, an explosion star with checkerboard accents at bottom-left, red/blue star marks and radiating speed lines at bottom-right — all decorations confined to three corner clusters, the center kept clean for content. The code-drawn halftone/speed-line background is retired; never restore it and never draw extra ornaments on top of the image.

- Grade: ink vignette only (`inset 0 0 120px`, 0.028 alpha). No warm soft-light layer. The paper must stay bright: never deepen decoration densities to compensate for weak contrast.

- Subtitle: centered white box with `2.5px` ink border and `3.5px 3.5px 0` ink offset shadow, bold Kai text. No tape, no solid bar. All trailing punctuation (，。！？等) strictly suppressed.

## Theme extra components

- `Burst` (explosion sticker): 12-spike star, `3.4px` ink stroke, default yellow fill, rotated 10°. Use at most one per scene, on a hero or key beat, size 110–140. Import from `theme/cel.tsx` via `THEME.extras.Burst`; pass only `x`, `y`, `size`, `text` (≤3 chars).

## Scene adaptation rules

- Keep every layout coordinate, type scale, motion helper and frame contract from the default lecture template. Do not redesign zones.

- Flat fills only: no gradients, no soft shadows, no blurred glows inside scene graphics. Depth comes from border weight and shadow offset.

- Dashed connector lines keep their animation contract; render them in ink or an accent color at full opacity.

- Emphasis color rotation (red → blue → green) follows the existing semantic color slots.

## Rejection flags

- Any card, block, or terminal border exceeding 2.5px, or shadow exceeding 4px (rejects bulky cartoon black slabs).

- Any blurred or soft drop shadow.

- Trailing punctuation visible at the end of any subtitle cue.

- Restoring the code-drawn halftone/speed-line background, drawing extra ornaments on top of the locked background image, or stretching a wrong-ratio image onto a canvas.

## Background decoration zones (v2.10)

The locked background bitmap carries **frame-scale, high-contrast** decorations: a yellow burst plus
halftone dots at the lower left, black speed lines and a red/blue star at the lower right, a red star
upper right and a small blue square at the left. They are part of the skin and are **not to be replaced
or repainted** — but text placed on top of them gets eaten.

`cel` therefore declares them in `theme.backgroundDecorZones`, and the rule is:

- **Content that overlaps a decoration zone must sit on a `CoverPanel`** (`tone="paper"` for hero
  content, `tone="wash"` for a quiet backing plate). Keep the plate's `z` **above the background and
  below the content** — a wash at `z=40` will cover absolutely positioned elements inside the scene
  (measured the hard way).
- Film-level fallback: use `CoverPanel` with `tone="wash"` and `z={-1}` (the old `BackgroundMute` was removed in v3.0.1 — it returned null on paper/sticker skins).
- Declared zones (1920×1080 design space): `(0,620,820,460)`, `(1230,560,690,520)`,
  `(1640,370,210,210)`, `(60,400,120,120)`.

See [media-routing.md](media-routing.md) §4 for the mechanics.

- A Burst sticker exceeding one per scene, or text longer than 3 characters.

- Subtitle rendered as a bar, tape strip or any non-boxed shape.

