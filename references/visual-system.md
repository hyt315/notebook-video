# Locked visual system: warm ivory Remotion notebook

Treat this as a low-freedom system. Copy the canonical components from `assets/example-project/src/index.tsx`.

## Canvas and camera

- 2560×1440, native 30fps, fixed camera.
- Preserve a 1920×1080 design coordinate system and scale it by 4/3 inside the native 2K composition.
- Animate physical paper poses natively at 30fps; do not create duplicate delivery frames.
- Keep subtitle space clear from y=925 downward.
- Do not add global zoom, shake, breathing, parallax, animated grain or depth-of-field.

## Background

Use the official `Background` implementation unchanged:

- warm radial desk outside the page;
- ivory page from `(42,28)` to `(1878,1052)`;
- inner rule from `(72,58)` to `(1848,1020)`;
- 54px low-contrast grid;
- static restrained dot texture controlled by `AESTHETIC.textureOpacity`;
- fixed shadows and no frame-to-frame texture change.

Background marks remain subordinate to all semantic objects.

## Typography

- Source Han Sans CN Regular: subtitles and body.
- Source Han Sans CN Bold: headings.
- Smiley Sans: short display emphasis only.
- Subtitle: 40px.
- Avoid readable text below 17px.
- Include fonts and license files in the editable package.

## Paper and depth

Use the official v7 `Paper` implementation unchanged. The paper surface, outline and shadow move together; do not add unused wrapper primitives merely to satisfy documentation.

At rest, use a close dark offset shadow. When a card lifts, increase x/y offset and blur while lowering alpha. On landing, return to the close shadow and permit one restrained spring overshoot.

Do not add dynamic shadow to fixed panels. Do not use large permanent blurred halos.

## Chapter and header

- Chapter card: left 92, top 74, width 350, height 82, z=150.
- Technical header: right 88, top 70, z=140.
- Keep the chapter stable within a section. Use in-scene micro labels for smaller beats.

## Subtitle input

Use the exact `Subtitle` component. It is a clean white torn paper strip:

- left/right: 188px;
- bottom: 34px;
- height: 112px;
- no border;
- exact canonical clip-path polygon;
- two restrained brown drop shadows;
- orange locator 28px from the left;
- blue ring 24px from the right;
- 1334px safe text width;
- one centered 40px line.

The previous dark outline produced black side artifacts and is forbidden. The paper contour supplies the edge. Do not draw an inner sine line, cursor, progress line, rounded search bar or dark endpoint.

Reserve the fully revealed phrase width so partial reveal never shifts. Hide trailing punctuation visually while keeping it in timing data.

## Information density

Use one hero, three to seven supporting semantic parts, a visible relationship and local feedback. Keep enough negative space to identify the hierarchy. Do not fill empty space with decorative text, loose dots or unrelated paper scraps.

## Materials

Use CSS/SVG paper components for exact labels. Generated images may supply topic-specific illustrations, but do not bake final Chinese labels or multiple independently moving parts into one raster image.
