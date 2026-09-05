# Theme contract: cel (anime cel-shading storyboard)

Status: LOCKED. This theme ships fully implemented in `assets/lecture-template/src/theme/cel.tsx`. Production runs select it with `new-project ./dir --style=cel` and never edit the theme file. Read this document instead of the other theme docs; the three style contracts are mutually exclusive by design (progressive disclosure).

## Design language

Anime cel-shading storyboard: thick ink outlines, flat saturated fills, hard offset shadows, halftone dots and speed lines. Energy is loud and graphic.

## Locked tokens (do not invent alternatives)

- Canvas: identical to the shared canvas contract (16:9 / 4:3 / 3:4). Layout coordinates are unchanged from the default; only skin and decoration change.

- Base surface: pure bright white `#fdfdfb` paper; cards pure white `#ffffff`. Never tinted cream — the ink contrast carries the style, not a warm base.

- Ink: `#14110f` for outlines and body text.

- Accents: red `#e8382a` (primary/orange slot), blue `#2b6de8`, green `#1d9e57`, yellow `#ffc62b` (gold slot).

- Card skin: `5px` solid ink border, `8px` corner radius, hard offset ink shadow `7px 7px 0` (grows with lift, never blurs). Every card carries a deterministic micro-tilt of ±1° hashed from its position — the same card always keeps the same tilt, and scene motion transforms compose on top of it.

- Background decoration: halftone dot field (20px pitch, 0.11 opacity) fading from the top-right, a weaker echo at bottom-left (18px pitch, 0.08), and 16 speed lines fanning from the top-left corner (3.6px stroke, 0.22 opacity, 680px reach). Anchored by canvas ratio; identical on all three canvases.

- Grade: ink vignette only (`inset 0 0 120px`, 0.028 alpha). No warm soft-light layer. The paper must stay bright: never deepen decoration densities to compensate for weak contrast.

- Subtitle: centered white box with `5px` ink border and `8px 8px 0` ink offset shadow, bold Kai text. No tape, no solid bar.

## Theme extra components

- `Burst` (explosion sticker): 12-spike star, `3.4px` ink stroke, default yellow fill, rotated 10°. Use at most one per scene, on a hero or key beat, size 110–140. Import from `theme/cel.tsx` via `THEME.extras.Burst`; pass only `x`, `y`, `size`, `text` (≤3 chars).

## Scene adaptation rules

- Keep every layout coordinate, type scale, motion helper and frame contract from the default lecture template. Do not redesign zones.

- Flat fills only: no gradients, no soft shadows, no blurred glows inside scene graphics. Depth comes from border weight and shadow offset.

- Dashed connector lines keep their animation contract; render them in ink or an accent color at full opacity.

- Emphasis color rotation (red → blue → green) follows the existing semantic color slots.

## Rejection flags

- Any blurred or soft drop shadow.

- Halftone or speed-line densities differing from the locked values, or newly invented background ornaments.

- A Burst sticker exceeding one per scene, or text longer than 3 characters.

- Subtitle rendered as a bar, tape strip or any non-boxed shape.

