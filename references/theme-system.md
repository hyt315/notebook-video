# Theme system: shared contract

Status: LOCKED. Four themes ship with the skill: `paper` (default warm-ivory notebook), `cel`, `sticker`, `flat`. All four are fully implemented in `assets/lecture-template/src/theme/`. A production selects its theme once at kickoff via `new-project ./dir --style=<id>` and then reads only its own contract:

- paper (default): the existing visual-system.md remains its contract; no separate file.
- cel → [theme-cel.md](theme-cel.md)
- sticker → [theme-sticker.md](theme-sticker.md)
- flat → [theme-flat.md](theme-flat.md)

## What a theme changes — and what it must never change

A theme swaps skin and decoration only:

- palette tokens (`C.*`) and aesthetic constants;
- card skin (border, radius, shadow signature);
- background decoration (canvas-ratio anchored);
- global grade layer;
- subtitle container chrome.

A theme never touches:

- canvas modes, design coordinates and the 4/3 delivery scale;
- type scale, font stack and the caption measurement gate;
- motion helpers (`q`, `ease`, `pop`, springs, CameraRig, JumpInText, WaveText, RollDigit);
- scene composition rules, zone budgets, stacking and exit contracts;
- audio tree, asset gates and QA validators.

The engine (`src/index.tsx`) reads `THEME` from `src/theme/active.ts` and performs zero style branching. `active.ts` contains exactly two lines (import + export) and is written by the CLI, never hand-edited.

## Adding a theme later (author-facing, not for productions)

1. Implement the `Theme` interface from `theme/types.ts` in a new `theme/<id>.tsx`; optional locked decorative components go in `THEME.extras`.
2. Anchor all decoration by canvas ratio (`useCanvas()`), never absolute pixels, so all three canvases stay consistent.
3. Add the id to `THEME_IDS` in `scripts/notebook-video.mjs`.
4. Write `references/theme-<id>.md` as a contract (locked tokens, extras usage, rejection flags).
5. Render frames at 100/300/550/900 on 16:9 plus one frame each on 4:3 and 3:4, and register the contract in validate-skill before merging.
