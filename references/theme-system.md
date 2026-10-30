# Theme system: shared contract

Status: LOCKED. Five themes ship with the skill: `flat` (default, calm modern edu illustration) and `cel` (bold comic / manga) from 3.2.0, plus the hand-made skins `journal` / `papercut` / `archive` from 3.3.0. All are implemented in `assets/lecture-template/src/theme/`. A production selects its theme once at kickoff via `new-project ./dir [--style=flat|cel|journal|papercut|archive]` and then reads only its own contract:

- flat (default) → `theme-flat.md`
- cel → `theme-cel.md`
- journal → `theme-journal.md`
- papercut → `theme-papercut.md`
- archive → `theme-archive.md`

Route: 软件 / 产品 / 代码 / 图表类选题走组件路线（flat / cel）；科普、自然、历史、"为什么"类选题走手作路线（journal / papercut / archive），手作路线先写 `treatment.json`（见 `director-method.md`）。本节以前只列了两套皮肤，Agent 读到会以为手作三套不存在——2026-10-30 修正。

The former `paper` and `sticker` themes were removed in 3.2.0, and the warm-ivory `--classic` example project in 3.2.0; projects created with them are not supported. The palette token names `paper` / `paperWarm` / `paperBase`, the `Paper` card component and `CoverPanel tone="paper"` are generic card-surface names kept by both remaining themes — they do not refer to the removed theme.

## Shared engine chrome (every theme)

- Canvas: 16:9 only, 2560×1440 delivery / 1920×1080 design space, scale 4/3 (see `canvas-modes.md`).
- Chapter card: left 92, top 74, width 392, height 90, z=150. Technical header: right 88, top 70, z=140.
- Subtitle: one centered line, WenKai Lite 44px, letterSpacing 1.6, 1334px safe width; per-word reveal with 0.9-frame per-character stagger and a 180ms lead; trailing punctuation hidden. The theme's `SubtitleChrome` supplies only the container.
- Fonts: LXGW WenKai Lite Regular/Medium for CJK; Clash Display / Space Grotesk / Caveat for Latin accents. All faces are bundled in `public/` and declared once in `src/fonts.tsx` (used by the film and the showcase). Each Latin family also carries a `unicode-range`-limited WenKai face, so a stack such as `'Clash,Space'` renders Chinese with WenKai instead of a system font (no tofu on machines without CJK fonts, Windows included). Avoid readable text below 17px.
- Backdrop: each theme ships three locked 2560×1440 backgrounds, `main` / `chapter` / `quiet`, all with a calm central ~70% safe area and decoration only at edges and corners. The engine picks one per shot (`bgVariantFor` in `index.tsx`): first shot of a chapter → `chapter`; `zones ≥ 4` → `quiet`; otherwise `main`; a shot-table `bg` field overrides the rule. Adjacent shots on different variants cross-fade over the 10-frame handoff. There is no full-frame translucent wash behind shots (3.2.0 removed it: it ghosted the corner characters). **3.3.0:** the three rasters are now the `legacy` entries of a per-skin background library (`manifests/backgrounds.json`, 8 more per craft skin, 5 more for flat / cel); when the project has the library, `resolve-shots` assigns every shot one library background by role (chapter / quiet / main), never repeating the previous shot, and writes it as `bg` + `bgFile` into `src/shots.ts`; the engine draws `bgFile` directly. `"bgRotate": false` (or no library) keeps the rule above. See `background-library.md`.
- Header plate: a theme whose top-right corner carries high-contrast decoration supplies `headerPlate` (cel: a comic caption box); flat leaves it unset.

## Palette source: Radix Colors (vendored)

Both palettes are built on Radix Colors v3 (MIT, © 2021 Radix, <https://github.com/radix-ui/colors>). Only the hex values are copied into the theme files, each annotated with its Radix scale and step; there is no runtime dependency. The roles map onto the 12-step scales like this:

| Role | Radix step | Use |
|---|---|---|
| accent fill (`blue`, `orange`, `green`, `gold`, `red`) | step 9 | solid fills, strokes, pills with white text |
| `*Ink` | step 11, mixed 8–10% toward step 12 where needed | text in the accent hue; ≥ 4.6:1 on all three surfaces |
| `navy` | blue 12 | dark fills, flat subtitle shadow |
| `ink` / `muted` | slate (flat) or gray-dark-1 / sand (cel) 12 / 11 | body text / secondary text |
| `paperWarm` / `paperBase` | amber 2 + sky 2 (flat), yellow 1 + yellow 2 (cel) | surfaces |
| soft tokens (`skyTint`, `dotIdle`, `orangeSoft`, …) | steps 3 / 7 | washes, idle states, gradient ends |

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
- background decoration (three locked 16:9 rasters: main / chapter / quiet) and an optional header plate;
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
2. Supply three 2560×1440 background rasters (`public/bg/bg-<id>-main.jpg`, `-chapter.jpg`, `-quiet.jpg`) with a calm central ~70%, register each in `manifests/visual-assets.json` (sha256, prompt summary, rights), map them in the theme's `backgrounds` table, and declare the union of their `backgroundDecorZones` in 1920×1080 design coordinates.
3. 让新 id 能被选中：`theme/active.ts` 改成 import 新主题，并把它加进 `scripts/notebook-video.mjs` 的 `new-project --style=` 取值（3.2.0 的取值是 flat / cel）。
4. Write `references/theme-<id>.md` as a contract (locked tokens, extras usage, rejection flags).
5. Render stills of a chapter shot, a diagram shot and a dense shot (e.g. frames 150 / 780 / 400), and register the contract in validate-skill before merging.
