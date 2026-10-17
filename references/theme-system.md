# Theme system: shared contract

Status: LOCKED. Two themes ship with the skill (v4.0.0+): `flat` (default, modern flat geometric) and `cel` (anime cel-shading). Both are fully implemented in `assets/lecture-template/src/theme/`. A production selects its theme once at kickoff via `new-project ./dir [--style=flat|cel]` and then reads only its own contract:

- flat (default) → `theme-flat.md`
- cel → `theme-cel.md`

The former `paper` and `sticker` themes were removed in v4.0.0; projects created with them are not supported. The palette token names `paper` / `paperWarm` / `paperBase`, the `Paper` card component and `CoverPanel tone="paper"` are generic card-surface names kept by both remaining themes — they do not refer to the removed theme.

## Shared engine chrome (every theme)

- Canvas: 16:9 only, 2560×1440 delivery / 1920×1080 design space, scale 4/3 (see `canvas-modes.md`).
- Chapter card: left 92, top 74, width 392, height 90, z=150. Technical header: right 88, top 70, z=140.
- Subtitle: one centered line, WenKai Lite 44px, letterSpacing 1.6, 1334px safe width; per-word reveal with 0.9-frame per-character stagger and a 180ms lead; trailing punctuation hidden. The theme's `SubtitleChrome` supplies only the container.
- Fonts: LXGW WenKai Lite Regular/Medium for CJK; Clash Display / Space Grotesk for Latin accents. Avoid readable text below 17px.

## 文字安全色：每支强调色必须给**两个**值（`*Ink` 约定）

两套皮肤里每支强调色都是一对：**原色**（`blue` / `orange` / `green` / `gold` / `red`）与**文字安全色**（`blueInk` / `orangeInk` / `greenInk` / `goldInk` / `redInk`）。

- **为什么要 Ink**：原色是按"填充与描边"挑的（鲜艳、面积大、当色块看），拿来当**文字**压在纸上时对比度常常只有 2–3:1 —— 低于 WCAG 2.2 SC 1.4.3 要求正文的 4.5:1，小字尤其糊。Ink 变体是**同色相按 WCAG 反解压暗**出来的那个值，不是另挑一个颜色。
- **唯一一条规则**：**填充位与描边位继续用原色，文字位（`color:`）一律用 Ink 变体。** 两种反向错法都要避免：① 嫌麻烦把原色调深 —— 填充也一起毁掉、皮肤变脏；② 为了省一个 token 在文字上用原色 —— 门禁会点名，且小字确实读不清。
- **门禁会查**（`validate-presentation.py` 的 G-3 可读性底线；判据与当前状态见 `presentation-gate.md`）：
  ① 五个 `*Ink` 各自必须在 `paper / paperWarm / paperBase` 上都过 4.5:1，**不过报 P0** —— 这一条同时是新增机制的自检：没有它，加了 Ink 也没人验；
  ② 任何被当文字色用过的调色板键（源码里的 `color: C.<key>`）低于 4.5:1，按主题聚合成 P1，并点名是哪个键。
- **`headerAccent` / `headerSub` 也算文字位**（它们只当文字用，实现在 `index.tsx` 的章节技术头部），必须自己过 4.5:1。
- 这一对值**不能用装饰色的原值凑**：`orangeDeep` 这类"深色端/渐变端"token 是给填充用的，当文字时在该皮肤上只有 2.5–4.2:1（实测），照样要换 Ink。

## What a theme changes — and what it must never change

A theme swaps skin and decoration only:

- palette tokens (`C.*`) and aesthetic constants;
- card skin (border, radius, shadow signature);
- background decoration (one locked 16:9 raster);
- global grade layer;
- subtitle container chrome.

A theme never touches:

- the 16:9 canvas, design coordinates and the 4/3 delivery scale;
- type scale, font stack and the caption measurement gate;
- motion helpers (`q`, `ease`, `pop`, springs, `JumpInText`);（`CameraRig` 已删除，不要再列）
- scene composition rules, zone budgets, stacking and exit contracts;
- audio tree, asset gates and QA validators.

The engine (`src/index.tsx`) reads `THEME` from `src/theme/active.ts` and performs zero style branching. `active.ts` contains exactly two lines (import + export) and is written by the CLI, never hand-edited.

## Adding a theme later (author-facing, not for productions)

1. Implement the `Theme` interface from `theme/types.ts` in a new `theme/<id>.tsx`; optional locked decorative components go in `THEME.extras`.
2. Supply one 2560×1440 background raster (`public/bg-<id>-169.jpg`) and declare its `backgroundDecorZones` in 1920×1080 design coordinates.
3. 让新 id 能被选中：`theme/active.ts` 改成 import 新主题，并把它加进 `scripts/notebook-video.mjs` 的 `new-project --style=` 取值（v4.0.0 的取值是 flat / cel）。
4. Write `references/theme-<id>.md` as a contract (locked tokens, extras usage, rejection flags).
5. Render frames at 100/300/550/900 on 16:9, and register the contract in validate-skill before merging.
