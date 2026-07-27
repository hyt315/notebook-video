# Canvas modes: 16:9 and 4:3

Two delivery canvases coexist in this skill. Ask the user once at kickoff which one this production uses; the answer decides every layout coordinate for the film. Both modes share the same aesthetic core, component library, subtitle pipeline, TTS workflow and QA gates. Nothing else about the production changes.

- **16:9** is the default for landscape platforms with a 16:9 player (for example Bilibili).
- **4:3** trades side width for a taller mobile presence: on a phone feed the same fonts render about one third larger. Choose it when the user's primary audience watches on phones.

## Parameter table

| Parameter | 16:9 | 4:3 |
| --- | --- | --- |
| Composition (delivery) | 2560×1440 | 1920×1440 |
| Design coordinate space | 1920×1080 | 1440×1080 |
| Film wrapper `width` | 1920 | 1440 |
| Delivery scale | 4/3 | 4/3 |
| Subtitle strip `left/right` | 188 | 60 |
| `AESTHETIC.subtitleSafeWidth` | 1334 | 1060 |
| Usable content width (after paper margins) | ~1700 | ~1250 |
| Two-column budget (left + right + gap) | up to 1030 + 600 | up to 830 + 390 |

Vertical space is identical in both modes (1080 design height); only horizontal layout changes. The multi-zone style is preserved in both modes — never reduce the number of zones to fit 4:3; shrink card widths and paddings instead.

## Authoring a 4:3 film

1. Start from the lecture template, then set the four 4:3 values above in `src/index.tsx` (`Composition` width, Film wrapper width, subtitle margins, `subtitleSafeWidth`). All four must change together — a real production shipped a 4:3 film with 16:9 subtitle margins because one of the four was missed.
2. Lay out scenes in the 1440-wide space. Convert a 16:9 two-column scene by narrowing both cards (not by dropping a zone); wide SVG diagrams may be wrapped in `transform:scale(0.85)` with `transformOrigin:'0 0'` instead of redrawing.
3. Caption lines must pass the 1060px width gate; prefer splitting a long semantic line over shrinking the subtitle font.
4. `validate-video` accepts both 2560×1440 and 1920×1440 containers; every other QA gate is unchanged.
5. `validate-visual-plan` cross-checks the four values against the `Composition` width and fails on any mixed-mode file, so run it before every render.

## Mobile readability type floor (both modes)

Small text is the main reason films look blurry on phones. Titles and the 40px subtitle are already large enough; the floor below raises only the small tiers. New projects must use:

```text
bodyL:26  bodyM:24  bodyS:23
labelL:22 labelM:21 labelS:20
microL:18 microS:16
```

Display/title tiers and `subtitle:40` stay as in the locked core. Never author content text below 16px design size; if a note only fits below that, cut it or move it into the narration.

## Full-canvas vertical budget

Content must use the full height between the chapter chrome and the subtitle strip: card tops start near y=190 and card bottoms reach about y=876 (40px of breathing room above the strip) in the 1080 design space. Two-column explainer scenes therefore use card heights near 686. An empty lower quarter is a layout defect, not negative space: on a phone the area just above the subtitle is the largest, most-read region of the frame. Bottom-anchored conclusion strips inside each card are the standard way to consume that height.
