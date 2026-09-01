# Canvas modes: 16:9, 4:3 and 3:4 portrait

Three delivery canvases coexist in this skill. Ask the user once at kickoff which one this production uses; the answer decides every layout coordinate for the film. Since v1.7.0 the lecture template ships all three layouts behind the `CANVAS` constant in `assets/lecture-template/src/index.tsx` (`'16:9' | '4:3' | '3:4'`): composition, wrapper, subtitle strip, chrome and safe-width values apply automatically, and the portrait film uses its bundled `*P` scene set. The tables below remain authoritative for custom layouts. All modes share the same aesthetic core, component library, subtitle pipeline, TTS workflow and QA gates. Nothing else about the production changes.

- **16:9** is the default for landscape platforms with a 16:9 player (for example Bilibili).
- **4:3** trades side width for a taller mobile presence: on a phone feed the same fonts render about one third larger. Choose it for landscape films whose primary audience watches on phones.
- **3:4 portrait** is the native shape for portrait feeds (for example Douyin). It shows near-fullscreen on a phone without the platform's bottom UI covering the frame, so the subtitle strip stays at the bottom as usual. Do not use 9:16: it is verified to leave a dead lower band under the platform UI and reads too long.

## Parameter table

| Parameter | 16:9 | 4:3 | 3:4 portrait |
| --- | --- | --- | --- |
| Composition (delivery) | 2560×1440 | 1920×1440 | 1440×1920 |
| Design coordinate space | 1920×1080 | 1440×1080 | 1080×1440 |
| Film wrapper `width`/`height` | 1920/1080 | 1440/1080 | 1080/1440 |
| Delivery scale | 4/3 | 4/3 | 4/3 |
| Subtitle strip `left/right` | 188 | 60 | 50 |
| Subtitle strip `bottom`/`height` | 34/112 | 34/112 | 40/104 |
| `TYPE.subtitle` (Smiley) | 44 | 44 | 40 |
| `AESTHETIC.subtitleSafeWidth` | 1334 | 1060 | 900 |
| Usable content width (after paper margins) | ~1700 | ~1250 | ~980 |
| Column layout | two columns | two narrowed columns | single column, cards stacked |

The multi-zone style is preserved in every mode — never reduce the number of zones to fit a narrower canvas; shrink card widths and paddings (landscape) or stack the zones vertically (portrait) instead.

## Authoring a 4:3 film

1. Start from the lecture template, then set the four 4:3 values above in `src/index.tsx` (`Composition` width, Film wrapper width, subtitle margins, `subtitleSafeWidth`). All four must change together — a real production shipped a 4:3 film with 16:9 subtitle margins because one of the four was missed.
2. Lay out scenes in the 1440-wide space. Convert a 16:9 two-column scene by narrowing both cards (not by dropping a zone); wide SVG diagrams may be wrapped in `transform:scale(0.85)` with `transformOrigin:'0 0'` instead of redrawing.
3. Caption lines must pass the 1060px width gate; prefer splitting a long semantic line over shrinking the subtitle font.
4. `validate-visual-plan` cross-checks the values against the `Composition` width and fails on any mixed-mode file, so run it before every render.

## Authoring a 3:4 portrait film

1. Set every 3:4 column value above together: `Composition` 1440×1920, wrapper 1080×1440, subtitle margins 50, bottom 40, height 104, `TYPE.subtitle` 40, `subtitleSafeWidth` 900. The caption width gate must measure at the same 40px Smiley setting.
2. Chapter chrome moves to y≈80; content region runs y≈200–1290; the subtitle strip sits at the bottom as in landscape modes.
3. Two-column scenes become stacked zones: full-width cards (~980 wide) laid top to bottom, each keeping its own bottom-anchored conclusion strip. Timeline SVGs stretch to ~900 wide — often larger than their landscape versions.
4. Caption lines must pass the 900px gate at 40px; portrait lines break shorter (about 13 CJK characters).
5. `validate-video` accepts 2560×1440, 1920×1440 and 1440×1920 containers; every other QA gate is unchanged.

## Mobile readability type floor (all modes)

Small text is the main reason films look blurry on phones. Titles and the subtitle are already large enough; the floor below raises only the small tiers. New projects must use:

```text
bodyL:26  bodyM:24  bodyS:23
labelL:22 labelM:21 labelS:20
microL:18 microS:16
```

Display/title tiers and the per-mode subtitle size stay as in the locked core. Never author content text below 16px design size; if a note only fits below that, cut it or move it into the narration.

## Full-canvas vertical budget

Content must use the full height between the chapter chrome and the subtitle strip: in the landscape modes card tops start near y=190 and card bottoms reach about y=876 (40px of breathing room above the strip); in 3:4 portrait the same rule gives a content region of roughly y=200–1290. An empty lower quarter is a layout defect, not negative space: on a phone the area just above the subtitle is the largest, most-read region of the frame. Bottom-anchored conclusion strips inside each card are the standard way to consume that height.
