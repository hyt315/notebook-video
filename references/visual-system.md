# Visual system: choose the representation that explains the idea

This is a decision guide, not a locked art direction. Reuse the existing Remotion template, shared components, pinned dependencies, and tested output geometry. The author may select a restrained visual treatment that supports the subject; no one style, skeleton, media kind, or amount of animation is required.

## Before styling

1. Identify the audience, learning goal, exact claim, and any critical relationship or process.
2. Decide what viewers should notice, compare, or be able to do afterward.
3. Identify the best evidence: a real interface, data series, equation, diagram, source excerpt, physical object, or concise explanation.
4. Sketch the sequence of ideas and its audio/caption timing. Only then choose a visual treatment.
5. Render representative real frames early. A mood board or style label is not a substitute for a frame made with the actual text, diagrams, assets, and crop.

## Composition

Use the smallest composition that makes the knowledge visible—not the smallest amount of information. A single stable, well-labelled diagram may explain more than several decorative panels. A complex mechanism may need states, a transfer path, synchronized labels, or more than one representation. White space is allowed; every region need not contain an element.

Give the main subject, its relationship to the other elements, and the current explanation a clear hierarchy. Keep labels next to their referents. Use visual change only where it clarifies a claim, progression, contrast, or attention cue. Allow enough time for a new diagram or caption to be read.

## Visual treatments

`paper`, `cel`, `sticker`, and `flat` are optional sets of palette, surface, edge, and accent treatments implemented in `assets/lecture-template/src/theme/`. They describe visual vocabularies, not subject categories or goals. `paper` is the current CLI default; that default is not a rule that every object must look like paper. Use the base skin coherently, and selectively borrow a compatible visual device only when it adds meaning. Do not mix skins just to prove variety.

- **Paper:** quiet editorial/notebook cues; useful for annotation, note-taking, or procedural explanations. Texture, depth, and paper cards are optional, not a requirement for every panel.
- **Cel:** high-contrast outline and flat color; useful when distinct regions or a drawn sequence improve recognition. Speed lines and saturated accents are optional.
- **Sticker:** soft, playful accents; use where informality supports the audience and topic. Tape, doodles, tilt, and rounded cards are not mandatory.
- **Flat:** geometric shapes and clean type; often suitable for direct comparison, data, or low-decoration diagrams. Character art is optional.

Color contrast, legibility, geometry, and caption-safe space are more important than stylistic fidelity. Check rendered pixels, not only theme tokens. Do not bake exact wording, numerical values, or labels into raster art.

## Images and components

Use a raster image when seeing a real-world subject or atmosphere materially improves the explanation; otherwise Remotion SVG/HTML and live text may be clearer and more reproducible. Keep exact labels and data in the editable composition. Record asset provenance and rights.

Reuse a bundled open-source component when it solves the visual task well. The project's `scripts/` remain standard-library-only; the Remotion template uses its pinned lockfile dependencies. Do not add a new dependency without authorization. Do not add a component because a reference project looks impressive: verify it enters the actual frame and earns its place in the explanation.

## Final review

Review storyboards as rendered frames, then watch and listen to the full film. Verify semantic alignment, comfortable reading, and visual stability in the target delivery context. For this task, 16:9 is the primary but not presumptively successful canvas; 4:3 and 3:4 remain unverified until separately rendered and reviewed.