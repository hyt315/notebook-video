# Theme system: shared contract

Status: LOCKED. Four themes ship with the skill: `paper` (default warm-ivory notebook), `cel`, `sticker`, `flat`. All four are fully implemented in `assets/lecture-template/src/theme/`. A production selects its theme once at kickoff via `new-project ./dir --style=<id>` and then reads only its own contract:

- paper (default): the existing visual-system.md remains its contract; no separate file.
- cel → `theme-cel.md`
- sticker → `theme-sticker.md`
- flat → `theme-flat.md`

## 文字安全色：每支强调色必须给**两个**值（`*Ink` 约定）

四套皮肤里每支强调色都是一对：**原色**（`blue` / `orange` / `green` / `gold` / `red`）与**文字安全色**（`blueInk` / `orangeInk` / `greenInk` / `goldInk` / `redInk`）。

- **为什么要 Ink**：原色是按"填充与描边"挑的（鲜艳、面积大、当色块看），拿来当**文字**压在纸上时对比度常常只有 2–3:1 —— 低于 WCAG 2.2 SC 1.4.3 要求正文的 4.5:1，小字尤其糊。Ink 变体是**同色相按 WCAG 反解压暗**出来的那个值（例：sticker 的 `blue #5ca9e0 → blueInk #40759c`，等比例压暗到 4.64:1），不是另挑一个颜色。
- **唯一一条规则**：**填充位与描边位继续用原色，文字位（`color:`）一律用 Ink 变体。** 两种反向错法都要避免：① 嫌麻烦把原色调深 —— 填充也一起毁掉、皮肤变脏；② 为了省一个 token 在文字上用原色 —— 门禁会点名，且小字确实读不清。
- **门禁会查**（`validate-presentation.py` 的 G-3 可读性底线；判据与当前状态见 `presentation-gate.md`）：
  ① 五个 `*Ink` 各自必须在 `paper / paperWarm / paperBase` 上都过 4.5:1，**不过报 P0** —— 这一条同时是新增机制的自检：没有它，加了 Ink 也没人验；
  ② 任何被当文字色用过的调色板键（源码里的 `color: C.<key>`）低于 4.5:1，按主题聚合成 P1，并点名是哪个键。
- **`headerAccent` / `headerSub` 也算文字位**（它们只当文字用，实现在 `index.tsx` 的章节技术头部），必须自己过 4.5:1。实测 sticker 的 `headerAccent` 原来直接等于 `blue`（2.40:1）、`headerSub` 等于 `muted`（3.14:1）→ 已按同一办法压暗（`#40759c` / `#7b6f5f`）。
- 这一对值**不能用装饰色的原值凑**：`orangeDeep` 这类"深色端/渐变端"token 是给填充用的，当文字时在该皮肤上只有 2.5–4.2:1（实测），照样要换 Ink。

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
- motion helpers (`q`, `ease`, `pop`, springs, `JumpInText`);（`CameraRig` 已删除，不要再列）
- scene composition rules, zone budgets, stacking and exit contracts;
- audio tree, asset gates and QA validators.

The engine (`src/index.tsx`) reads `THEME` from `src/theme/active.ts` and performs zero style branching. `active.ts` contains exactly two lines (import + export) and is written by the CLI, never hand-edited.

## Adding a theme later (author-facing, not for productions)

1. Implement the `Theme` interface from `theme/types.ts` in a new `theme/<id>.tsx`; optional locked decorative components go in `THEME.extras`.
2. Anchor all decoration by canvas ratio (`useCanvas()`), never absolute pixels, so all three canvases stay consistent.
3. 让新 id 能被选中：`theme/active.ts` 改成 import 新主题，并把它加进 `scripts/notebook-video.mjs` 的 `new-project --style=` 取值（v3.1 的取值是 paper / cel / sticker / flat；**没有 THEME_IDS 这个常量**）。
4. Write `references/theme-<id>.md` as a contract (locked tokens, extras usage, rejection flags).
5. Render frames at 100/300/550/900 on 16:9 plus one frame each on 4:3 and 3:4, and register the contract in validate-skill before merging.
