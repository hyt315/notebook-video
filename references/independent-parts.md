# Independent components and layer contracts

## Decompose by motion ownership

If two visible things enter, move, rotate, hide, light or exit at different frames, model them as separate React components or SVG groups.

Good parts include character body/arms, folder back/front, each card, each wire, buttons, status lights and badges. A flattened finished scene cut into rectangles is not independent modeling.

## Manifest fields

Every moving part requires:

```json
{
  "id": "source-card",
  "scene": 4,
  "z": 50,
  "layer_role": "floating",
  "occlusion_contract": "always-visible",
  "entry_frame": 1220,
  "exit_frame": 1430,
  "exit_contract": "fully-outside",
  "motion": ["curved-transfer", "dynamic-shadow"]
}
```

Use stable IDs in code and cue data.

## Layer roles

Order: background → wire → base → slot → status → floating → foreground → chrome → subtitle.

- Floating objects stay above base/slot/status objects unless explicitly being inserted.
- A slot may cover a card only after the card crosses a visible slot boundary.
- Chrome remains above scene content.
- Subtitle remains highest.

CSS transforms, opacity, filters and isolation create stacking contexts. Do not assume a child z-index can escape its parent. Put objects that must overlap in a shared intended context.

## Complete exit

Every temporary part needs an exit contract. Remove it only after it is completely outside the canvas, or fade the whole component after its geometry is no longer clipped. Never move only a portion behind an accidental container edge.

Inspect entry, midpoint, rest and exit frames at full 2560×1440 delivery resolution.

## Raster assets

Use generated raster images only for topic-specific illustration. Keep exact text, logos, wires and independently moving parts in code. Include transparent padding only when rotation requires it.

Register each used raster in `manifests/visual-assets.json`. Treat the bitmap, each highlight box, each arrow and each explanation line as separate parts with their own timing. Preload the bitmap in `AssetGate`. Generated assets must not contain baked labels or charts; request crop-safe negative space and add exact information in Remotion. Read [visual-director.md](visual-director.md).
