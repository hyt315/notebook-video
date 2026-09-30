# Optional visual treatment: cel

The `cel` implementation in `assets/lecture-template/src/theme/cel.tsx` offers a high-contrast drawn language: dark outlines, flatter fills, and hard-edged depth. It can help separate diagram regions, stages, or actors. It is not a requirement to add speed lines, bursts, or motion to every scene.

## Use when it helps

Choose cel-like treatment when a drawn/diagrammatic look supports recognition or makes a sequence easier to read—for example, when comparing distinct states, marking a physical edge, or showing a causal transformation. Keep exact values and labels live in Remotion.

Use a quiet white/neutral background and one or two semantic accent colors. The bundled cel background includes visible corner decorations; if they interfere with real content, use the existing backing-panel helper, crop/position an asset safely, or choose a quieter surface. Do not add ornaments merely to fill space. A concentrated or static diagram is valid.

## Boundaries

Use foreground/background color pairs that meet applicable contrast requirements. Strong fills are safer as shapes than as small text; choose a text-safe color when needed. Thick outlines, halftone textures, speed lines, and burst stickers are options, not minimum requirements. Inspect their rendered effect at the actual playback size and at scene transitions.

The implementation has a base canvas, palette, and card skin that the CLI can select. A project may keep that stable while its content uses other well-supported visual forms. Do not copy third-party designs or assets without checking their rights.