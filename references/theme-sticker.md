# Theme contract: sticker (cartoon sticker journal)

Status: LOCKED. This theme ships fully implemented in `assets/lecture-template/src/theme/sticker.tsx`. Production runs select it with `new-project ./dir --style=sticker` and never edit the theme file. Read this document instead of the other theme docs; the three style contracts are mutually exclusive by design (progressive disclosure).

## Design language

Cartoon sticker journal: white-outlined sticker cards, washi tape, marker highlights and hand-drawn doodles on grid paper. Energy is soft, cute and craft-like.

## Locked tokens (do not invent alternatives)

- Canvas: identical to the shared canvas contract (16:9 / 4:3 / 3:4). Layout coordinates are unchanged from the default; only skin and decoration change.

- Base surface: pale mint `#f4f9f4` grid paper (42px pitch, 0.10 alpha). Never cream — the mint undertone is the sticker theme's signature.

- Ink: `#4a3b2f` for text and outlines.

- Accents: pink `#ff8fa3` (primary/orange slot, the lead), sky `#8ecae6` / blue `#5ca9e0`, mint `#7fd8be` / green `#61d188`, butter `#ffd166` (gold slot). All accents sit on one pastel step (high lightness, low harshness) derived from the pink lead — never invent off-step colors.

- Card skin: pure white sticker with a `2.5px` soft-brown print edge (`rgba(74,59,47,0.55)`, the printed sticker art line), a `5px` white outline (the die-cut edge) and a soft two-layer shadow (deepened: 0.12/0.17 base alphas so the white edge stays readable on the mint page). Radius `22px`. Lift deepens the shadow only; the outline never changes.

- Background (LOCKED fixed raster): one AI-generated image per canvas ratio, selected automatically from `public/bg-sticker-<169|43|34>.jpg` (`16:9` 2560×1440, `4:3` 1920×1440, `3:4` 1440×1920 — pixel-exact, no crop, no stretch). The image carries the complete background language: pale mint grid paper with a uniform paper tone (no color patches), corner doodles (heart, cross, wave, spiral, zigzag) and washi-tape strips kept to the edges, center left clean — doodles never collide with the chapter tag (top-left) or the title header (top-right). The code-drawn grid/doodle background is retired; never restore it and never draw extra elements on top of the image.

- Grade: warm ink vignette (`inset 0 0 130px`, 0.04 alpha). No soft-light warmth.

- Subtitle: white rounded chip (radius 18, soft shadow) with one washi-tape strip on its top edge (sky-blue, −8°, 130px). Bold Kai text. No ink borders, no solid bar.

## Theme extra components

- `Tape` (washi tape): 38px tall, torn-edge clip-path, diagonal weave stripes. Use for sticking scene cards onto the page: one tape per card corner maximum, rotation between −14° and +10°, colors from the locked pastel set with 0.7–0.75 alpha. Access via `THEME.extras.Tape`; pass only `x`, `y`, `w` (90–160), `rot`, `color`.

## Scene adaptation rules

- Keep every layout coordinate, type scale, motion helper and frame contract from the default lecture template. Do not redesign zones.

- Cards may tilt: static scene cards may carry a fixed rotation between −2° and +2° for hand-placed feel. Motion cards stay axis-aligned while moving.

- Scene graphics use rounded terminals and candy fills; avoid hard ink outlines inside scenes (the sticker outline already frames each card).

- Emphasis color rotation (pink → blue → mint) follows the existing semantic color slots.

## Rejection flags

- Heavy ink borders on cards (5px cel-style ink frames); only the locked 2.5px soft-brown print edge is allowed.

- Tapes exceeding one per corner or rotating outside −14°…+10°.

- Card tilt beyond ±2°, or any tilt applied to a moving card.

- Newly invented background doodles, restoring the code-drawn grid/doodle background, drawing on top of the locked background image, or stretching a wrong-ratio image onto a canvas; subtitle rendered as a boxed/barred shape.

