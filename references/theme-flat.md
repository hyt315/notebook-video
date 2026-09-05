# Theme contract: flat (modern flat geometric monsters)

Status: LOCKED. This theme ships fully implemented in `assets/lecture-template/src/theme/flat.tsx`. Production runs select it with `new-project ./dir --style=flat` and never edit the theme file. Read this document instead of the other theme docs; the three style contracts are mutually exclusive by design (progressive disclosure).

## Design language

Modern flat geometric with playful character: gray-hairline white cards with colored offset solid shadows, geometric little monsters peeking from the corners, stars / exclamation / squiggle props, floating rounded subtitle pill. Energy is confident, quirky and editorial.

## Locked tokens (do not invent alternatives)

- Canvas: identical to the shared canvas contract (16:9 / 4:3 / 3:4). Layout coordinates are unchanged from the default; only skin and decoration change.

- Base surface: cool light gray-blue `#f2f4f7`; cards pure white. The cool tone is the point: it must never drift back toward a warm paper white.

- Ink: `#191919` for monster pupils/mouths, prop dot matrix and body text.

- Accents: indigo `#3b4ed8` (blue slot, the lead), coral `#f05f42` (primary/orange slot), mint `#41d27b` (green slot), sun `#f0c63c` (gold slot). All accents are derived on one step (saturation ≈65–85, lightness ≈54–62) under the indigo lead — never invent off-step colors.

- Card skin: pure white card with a `2px` neutral gray hairline (`rgba(25,25,25,0.30)`, defines the top/left edges on the pale surface — not an ink frame), `20px` radius, offset solid shadow `7px 7px 0` in indigo `#3b4ed8` by default — when a scene passes a semantic accent color the shadow takes that color, so each card reads as a color-blocked tile; lift extends the offset slightly. No ink border, no inset liner, no blur anywhere.

- Background monsters (locked, canvas-ratio anchors, flat solid fills only):
  - **Round blob monster** bottom-right (`0.930w, 0.860h`, body radius `0.052w`, indigo): gold antenna ball, two white eyes with ink pupils looking toward the content, small smile arc, two stub legs. The top-right corner is reserved for the chapter header — nothing may overlap it.
  - **Square monster** bottom-left (`0.075w, 0.845h`, side `0.058w`, coral, −8° tilt): raised arms, white eyes with ink pupils, zigzag mouth, stub feet.
  - Props: gold 4-point star (`0.185w, 0.140h`), small coral star (`0.790w, 0.620h`), mint exclamation mark (`0.945w, 0.480h`, 10° tilt), indigo squiggle (left-middle). Nothing else may be drawn on the background.

- Grade: none by design. Color contrast carries the composition; do not add soft-light warmth or vignette.

- Subtitle: floating rounded pill (indigo `#3b4ed8`, radius 26, padding 16×40, hard offset ink shadow `7px 7px 0`), bottom-centered at 40px, coral dot before the text and mint dot after; bold white Kai text. No full-width bar, no box, no tape.

## Scene adaptation rules

- Keep every layout coordinate, type scale, motion helper and frame contract from the default lecture template. Do not redesign zones.

- Scene graphics use geometric primitives (rects, circles, bars) with flat fills and hard-edged strokes; no gradients, no soft shadows, no blur.

- White cards keep full opacity so text stays readable; the corner monsters never overlap the content zones — verify on the first frame of each scene.

- Emphasis color rotation (coral → indigo → mint) follows the existing semantic color slots.

## Rejection flags

- Any blur, gradient or vignette.

- The old giant indigo circle / Memphis set, or any background element beyond the locked monsters + props.

- Subtitle rendered as a full-width bar, or as a floating white chip (that belongs to cel/sticker).

- Ink-bordered cards or white inset liners (that is the cel theme's language; flat cards carry only the 2px gray hairline plus colored shadows).

- Monsters moved to non-locked positions, recolored, or given gradients/outlines.

