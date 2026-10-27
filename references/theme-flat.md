# Theme contract: flat (calm modern edu illustration)

Status: LOCKED. This theme ships fully implemented in `assets/lecture-template/src/theme/flat.tsx`. It is the **default** skin (3.2.0+; visual identity rebuilt in 3.2.0): `new-project ./dir` (or `--style=flat`) selects it; production runs never edit the theme file. Read this document instead of the other theme doc; the two style contracts are mutually exclusive by design (progressive disclosure).

## Design language

Calm, modern, friendly explainer look: soft sky and cream surfaces, white cards with a hairline and a hard colored offset shadow, one confident primary blue, a warm coral and a mint green as secondaries, sunny yellow only as a highlight. Generous contrast, no muddy greys. A small round blue robot mascot (antenna with a yellow ball) and a coral square buddy peek in from the bottom corners of the background; they never enter the content area.

## Locked tokens (do not invent alternatives)

All hex values are vendored from Radix Colors v3 (MIT); the theme file names the scale and step next to each token.

- Canvas: 16:9 only (2560×1440 delivery, 1920×1080 design space; see canvas-modes.md).
- Surfaces: `paper` `#ffffff` (cards), `paperWarm` `#fefbe9` (amber 2, cream), `paperBase` `#f1fafd` (sky 2).
- Ink: `ink` `#1c2024` (slate 12) for body text, `muted` `#60646c` (slate 11) for secondary text.
- Accents (fill → text-safe `*Ink`; every Ink is ≥ 4.6:1 on all three surfaces):

  | Slot | Fill | Ink | Radix source |
  |---|---|---|---|
  | blue (lead) | `#0090ff` | `#0d6fc6` | blue 9 / blue 11 mixed 8% toward blue 12 |
  | orange (coral) | `#e54d2e` | `#d13415` | tomato 9 / tomato 11 |
  | green (mint) | `#29a383` | `#207d64` | jade 9 / jade 11 mixed 8% toward jade 12 |
  | gold (sunny highlight) | `#ffc53d` | `#a25f03` | amber 9 / amber 11 mixed 10% toward amber 12 |
  | red | `#e5484d` | `#ce2c31` | red 9 / red 11 |

  `navy` `#113264` (blue 12) is the dark fill and the header accent. Gold is a highlight fill only: put `ink` text on it, never white.
- Card skin: white card, `2px` hairline `rgba(28,32,36,0.14)`, `22px` radius, hard offset shadow `6px 6px 0` in the lead blue (a scene's `borderColor` recolors it), lift extends the offset by up to 3px. No ink border, no blur.
- Background library (3.4.0): five more light backgrounds — `flat/mesh-dawn`, `mesh-mint`, `dotgrid`, `sunrise`, `shapes` — rotate by shot role with no two adjacent shots alike; see [background-library.md](background-library.md). The three below stay as the `legacy` entries.
- Backgrounds (LOCKED rasters, 2560×1440, `public/bg/`, registered with sha256 in `manifests/visual-assets.json`):
  - `bg-flat-main.jpg`: soft sky → cream gradient with paper grain; the robot mascot peeks up from the bottom-right edge, a mint hill with the coral buddy sits at the bottom-left, tiny clouds and yellow dots in the top corners.
  - `bg-flat-chapter.jpg`: the same scene mirrored (mascot bottom-left, hill and buddy bottom-right) on a slightly richer sky with a soft cream glow behind the centre.
  - `bg-flat-quiet.jpg`: clouds removed, mascot and hill scaled down to a sliver at the bottom corners, for dense shots.

  The central ~70% of every variant is empty. The characters stay inside the bottom ~20% and the outer ~20% of the width. Never draw extra elements on top of the images, never restore a code-drawn background.
- Grade: none by design.
- Subtitle: floating pill in `blueInk` `#0d6fc6` (white text ≥ 4.6:1), fully rounded, padding 15×40, hard `0 6px 0` navy shadow, bottom-centered at 40px, coral dot before the text and sunny dot after; bold white Kai text.
- Header: sits directly on the sky in `navy` / `muted` (no plate).

## Scene adaptation rules

- Keep every layout coordinate, type scale, motion helper and frame contract from the lecture template. Do not redesign zones.
- Scene graphics use flat primitives (rects, circles, bars) with flat fills; no soft shadows, no blur.
- Cards keep full opacity. There is no full-frame wash behind shots; content sits directly on the calm centre of the background.
- Emphasis color rotation (coral → blue → mint) follows the existing semantic color slots.

## Rejection flags

- Any blur, vignette, or a full-frame translucent wash over the background.
- Restoring a code-drawn background, or drawing any element on top of the locked background images.
- Subtitle rendered as a full-width bar, or as a white chip with an ink border (that belongs to cel).
- Ink-bordered cards (cel's language).
- Muddy grey fills (`rgba(0,0,0,…)` washes over white cards); dim with the theme's navy at ≤ 10% instead.
- Replacing a background with off-palette colors, a busy centre, baked text, or a wrong-ratio image stretched onto the canvas.

## Background decoration zones

The union over the three variants (1920×1080 design space), declared in `flat.tsx`:
`(1500,840,420,240)` bottom-right, `(0,840,400,240)` bottom-left, `(0,120,190,260)` top-left cloud, `(1730,120,190,260)` top-right cloud.

Content overlapping a declared zone sits on a `CoverPanel` (`tone="paper"`, z below content). See [media-routing.md](media-routing.md) §4.
