# Theme contract: sticker (cartoon sticker journal)

Status: LOCKED. This theme ships fully implemented in `assets/lecture-template/src/theme/sticker.tsx`. Production runs select it with `new-project ./dir --style=sticker` and never edit the theme file. Read this document instead of the other theme docs; the three style contracts are mutually exclusive by design (progressive disclosure).

## Design language

Cartoon sticker journal: white-outlined sticker cards, washi tape, marker highlights and hand-drawn doodles on grid paper. Energy is soft, cute and craft-like.

## Locked tokens (do not invent alternatives)

- Canvas: identical to the shared canvas contract (16:9 / 4:3 / 3:4). Layout coordinates are unchanged from the default; only skin and decoration change.

- Base surface: pale mint `#f4f9f4` grid paper (42px pitch, 0.10 alpha). Never cream — the mint undertone is the sticker theme's signature.

- Ink: `#4a3b2f` for text and outlines.

- Accents: pink `#ff8fa3` (primary/orange slot), sky `#8ecae6` / blue `#4f9fd8`, mint `#7fd8be` / green `#4fb894`, butter `#ffd166` (gold slot).

- Card skin: pure white sticker with a `5px` white outline (the sticker edge) and a soft two-layer shadow (no border). Radius `22px`. Lift deepens the shadow only; the outline never changes.

- Background doodles (locked, by canvas-ratio anchors): heart (top-right), cross (below it), wave (bottom-left), spiral (bottom-right), zigzag (top-left). All 5px stroked, single accent colors. Nothing else may be drawn on the background.

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

- Ink borders on cards (that is the cel theme's language).

- Tapes exceeding one per corner or rotating outside −14°…+10°.

- Card tilt beyond ±2°, or any tilt applied to a moving card.

- Newly invented background doodles, or subtitle rendered as a boxed/barred shape.

