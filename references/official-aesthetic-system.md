# Template visual assets and engineering invariants

The template contains a current 16:9-first visual implementation, reusable components, fonts, and palette tokens. These are tested starting points, not a requirement to make every video look like one pre-approved art direction. Use a project copy and render real frames before changing shared behavior; a style name, preview sheet, or palette alone cannot establish that an edit is better.

## Keep reliable engineering behavior

- Remotion is the bundled renderer. Frame-dependent output should be deterministic and use a single documented FPS convention.
- Reuse the lockfile and existing open-source component layer where licensed and helpful. `scripts/*.py` are standard-library-only; template dependencies are pinned. A new dependency not already listed needs approval.
- Keep content text and important data editable and sourceable. Raster artwork can provide a subject or atmosphere, but should not be the only source of an exact label, value, or relationship.
- Load licensed fonts and media before their first use. Keep source/rights notes for third-party and generated assets.
- Use the actual canvas dimensions, the correct subtitle-safe geometry, and frame-boundary timing. Each canvas requires its own layout validation; the presence of a canvas option is not evidence it has been tested.
- Preserve caption accuracy and synchronization. Use applicable WCAG contrast requirements, while treating reading speed and minimum hold-time values as project-specific review prompts.
- A component, background, shadow, effect, card skin, mascot, or camera path is optional unless the topic genuinely needs it. “Official” does not mean every scene must display it.

## Choose visual form from meaning

Sketch the teaching claim and evidence first. Choose between a static explanation, live diagram, chart, code excerpt, real interface, image, comparison, or sequence according to what makes the idea visible. A still frame can be the clearest visual. Negative space need not be filled; do not turn component, movement, media, scene-family, or style variety into acceptance thresholds.

`paper`, `cel`, `sticker`, and `flat` are available treatments in `theme-system.md`. Preserve the user's requested style when given. Otherwise choose a restrained base and adapt it when the subject or rendered result calls for a change. Check the actual text, assets, contrast, and composition in the rendered film.

## Review the rendered artifact

Inspect key frames and a contact sheet, then watch and listen to the whole output at normal speed. Review important information on the intended device/size. Record known untested canvases and limitations. Do not claim user or audience approval based on an automated gate or internal review.