# Theme contract: flat (modern flat geometric)

Status: LOCKED. This theme ships fully implemented in `assets/lecture-template/src/theme/flat.tsx`. Production runs select it with `new-project ./dir --style=flat` and never edit the theme file. Read this document instead of the other theme docs; the three style contracts are mutually exclusive by design (progressive disclosure).

## Design language

Modern flat geometric: bold color blocks, thick ink borders with offset solid shadows, Memphis accents, solid ink subtitle bar. Energy is confident and editorial, suited to product/promotional films.

## Locked tokens (do not invent alternatives)

- Canvas: identical to the shared canvas contract (16:9 / 4:3 / 3:4). Layout coordinates are unchanged from the default; only skin and decoration change.

- Base surface: cool light gray-blue `#f2f4f7`; cards pure white. The cool tone is the point: it must never drift back toward a warm paper white.

- Ink: `#191919` for borders, bars and body text.

- Accents: coral `#ff5d3b` (primary/orange slot), indigo `#3b4ed8` (blue slot), mint `#37c99b` (green slot), sun `#ffcf3f` (gold slot).

- Card skin: `3.5px` ink border with a `2px` white inset liner, `20px` radius, offset solid shadow `7px 7px 0 rgba(25,25,25,0.9)`; lift extends the offset slightly. No blur anywhere.

- Background (locked, canvas-ratio anchors): an indigo circle anchored top-right (diameter 42% of design width, partially off-canvas, 0.96 opacity) plus Memphis accents — coral open circle (bottom-left), sun cross (top-right, inside the circle zone), indigo double-wave (left), a 5×6 ink dot matrix (left-middle). Nothing else.

- Grade: none by design. Color contrast carries the composition; do not add soft-light warmth or vignette.

- Subtitle: full-width solid ink bar, 128px tall, coral tick (10×44) before the text and mint tick after; bold white Kai text. No box, no tape, no border.

## Scene adaptation rules

- Keep every layout coordinate, type scale, motion helper and frame contract from the default lecture template. Do not redesign zones.

- Scene graphics use geometric primitives (rects, circles, bars) with flat fills and hard-edged strokes; no gradients, no soft shadows, no blur.

- White cards keep full opacity so text stays readable against the background circle and color blocks.

- Emphasis color rotation (coral → indigo → mint) follows the existing semantic color slots.

- The indigo background circle occupies the top-right zone: keep chapter header text white-outlined if it overlaps (the header contract already reserves that corner; verify on the first frame).

## Rejection flags

- Any blur, gradient or vignette.

- Background color blocks beyond the locked circle and Memphis set.

- Subtitle rendered as a floating box or chip (that belongs to cel/sticker).

- Ink dot matrix or Memphis accents moved to non-locked positions.

