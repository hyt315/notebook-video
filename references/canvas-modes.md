# Canvas: 16:9 only

3.2.0 起本技能只有**一种**交付画布：16:9。4:3 与 3:4 竖屏（以及 `Film4x3` / `Film3x4`、对应背景图与门禁分支）已全部删除，不再支持。

## Spec

| Parameter | Value |
| --- | --- |
| Composition (delivery) | 2560×1440, native 30fps |
| Design coordinate space | 1920×1080 |
| Delivery scale | 4/3 (`MODES['16:9'].scale`) |
| Subtitle text `left/right` | 188 |
| Subtitle text `bottom` (contract value) | 34 |
| Subtitle font (WenKai Lite) | 44px |
| Subtitle safe width (`safe` / `subtitleSafeWidth`) | 1334 |
| Usable content width | ~1700 |
| Column layout | two columns |

These are contract values. They live in `assets/lecture-template/src/theme/canvas.ts` (`MODES['16:9']`) and in `scripts/validate-visual-plan.py` (`CANVAS_MODES[2560]`); `validate-skill-consistency.py` cross-checks the two. Each skin's `SubtitleChrome` has its own render-time `bottom` (`cel` 44 / `flat` 40); the classic example project hard-codes `bottom:18`.

`validate-visual-plan` rejects any `NotebookVideoFilm` Composition width other than 2560, and `validate-video` accepts only 2560×1440 containers.

## Mobile readability type floor

Small text is the main reason films look blurry on phones. Titles and the subtitle are already large enough; the floor below raises only the small tiers:

```text
bodyL:26  bodyM:24  bodyS:23
labelL:22 labelM:21 labelS:20
microL:18 microS:16
```

Never author content text below 16px design size; if a note only fits below that, cut it or move it into the narration.

## Full-canvas vertical budget

Content must use the full height between the chapter chrome and the subtitle strip: card tops start near y=190 and card bottoms reach about y=876 (40px of breathing room above the strip). An empty lower quarter is a layout defect, not negative space. Bottom-anchored conclusion strips inside each card are the standard way to consume that height.
