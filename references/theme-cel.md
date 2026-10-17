# Theme contract: cel (bold comic / manga)

Status: LOCKED. This theme ships fully implemented in `assets/lecture-template/src/theme/cel.tsx` (visual identity rebuilt in v4.1.0). Production runs select it with `new-project ./dir --style=cel` and never edit the theme file. Read this document instead of the other theme doc; the two style contracts are mutually exclusive by design (progressive disclosure).

## Design language

Bold comic / shonen-manga energy: off-white comic paper with halftone dots, near-black ink outlines, saturated primary red / blue / yellow in flat fills, hard offset ink shadows, speed lines and starbursts. Loud and graphic at the edges, clean paper in the middle where the content lives.

## Locked tokens (do not invent alternatives)

All hex values are vendored from Radix Colors v3 (MIT); the theme file names the scale and step next to each token.

- Canvas: 16:9 only (2560×1440 delivery, 1920×1080 design space; see canvas-modes.md).
- Surfaces: `paper` `#ffffff` (panels), `paperWarm` `#fdfdf9` (yellow 1), `paperBase` `#fefce9` (yellow 2, comic paper).
- Ink: `ink` `#111111` (gray-dark 1) for outlines and body text, `muted` `#63635e` (sand 11).
- Accents (fill → text-safe `*Ink`; every Ink is ≥ 4.6:1 on all three surfaces):

  | Slot | Fill | Ink | Radix source |
  |---|---|---|---|
  | orange (comic red, warm lead) | `#e5484d` | `#ce2c31` | red 9 / red 11 |
  | blue (co-lead) | `#0090ff` | `#0d74ce` | blue 9 / blue 11 |
  | gold (comic yellow) | `#ffe629` | `#956703` | yellow 9 / yellow 11 mixed 10% toward yellow 12 |
  | green | `#46a758` | `#2a7e3b` | grass 9 / grass 11 |
  | red | `#dc3e42` | `#ce2c31` | red 10 / red 11 |

  Yellow is a fill (bursts, highlight blocks, the subtitle's offset shadow); put `ink` text on it, never white.
- Panel skin: `3px` solid ink border, `8px` radius, hard offset ink shadow `4px 4px 0` growing to `8px 8px 0` with lift, never blurred. Every panel carries a deterministic micro-tilt of ±0.7° max hashed from its position; scene transforms compose on top of it.
- Backgrounds (LOCKED rasters, 2560×1440, `public/bg/`, registered with sha256 in `manifests/visual-assets.json`):
  - `bg-cel-main.jpg`: black halftone fan + yellow ink-outlined starburst bottom-left, speed lines top-right, red halftone + blue star bottom-right, blue halftone wedge top-left.
  - `bg-cel-chapter.jpg`: short speed-line ticks along the left and right edges, yellow starburst top-right, red halftone top-left, red star bottom-left, blue halftone bottom-right.
  - `bg-cel-quiet.jpg`: one small element per corner, for dense shots.

  The central ~70% of every variant is empty paper with no panel border or frame line. Never draw extra ornaments on top of the images, never restore a code-drawn background.
- Grade: ink corner vignette only (`inset 0 0 120px`, 0.03 alpha).
- Subtitle: white caption box, `3px` ink border, yellow offset block (`5px 5px 0`) outlined in ink, bold Kai text, padding 10×36. No tape, no solid bar. All trailing punctuation strictly suppressed.
- Header plate: the top-right technical header sits in a comic caption box (white, `3px` ink border, `4px 4px 0` ink shadow), because the top-right corner of every background carries speed lines or a starburst.

## Theme extra components

- `Burst` (explosion badge): 12-spike star, `3.6px` ink stroke, default yellow fill, rotated 10°. Use at most one per scene, on a hero or key beat, size 110–140. Import from `theme/cel.tsx` via `THEME.extras.Burst`; pass only `x`, `y`, `size`, `text` (≤3 chars).

## Scene adaptation rules

- Keep every layout coordinate, type scale, motion helper and frame contract from the lecture template. Do not redesign zones.
- Flat fills only: no gradients, no soft shadows, no blurred glows inside scene graphics. Depth comes from border weight and shadow offset.
- Dashed connector lines keep their animation contract; render them in ink or an accent color at full opacity.
- Emphasis color rotation (red → blue → green) follows the existing semantic color slots.

## Rejection flags

- Panel borders above 3px or ink shadows above 8px (bulky black slabs).
- Any blurred or soft drop shadow, or a full-frame translucent wash over the background.
- Trailing punctuation visible at the end of any subtitle cue.
- A header without its caption-box plate.
- More than one `Burst` per scene, or `Burst` text longer than 3 characters.
- Subtitle rendered as a bar, tape strip or any non-boxed shape.
- Restoring a code-drawn halftone/speed-line background, drawing ornaments on top of the locked images, a background with a busy centre, baked text or onomatopoeia, or a wrong-ratio image stretched onto the canvas.

## Background decoration zones

The union over the three variants (1920×1080 design space), declared in `cel.tsx`:
`(0,760,300,320)` bottom-left, `(1580,700,340,380)` bottom-right, `(1540,0,380,340)` top-right, `(0,0,240,230)` top-left, `(0,290,110,440)` left edge, `(1810,330,110,420)` right edge.

**Content that overlaps a decoration zone must sit on a `CoverPanel`** (`tone="paper"`). Keep the plate's `z` above the background and below the content. See [media-routing.md](media-routing.md) §4.
