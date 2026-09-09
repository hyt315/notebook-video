# Lecture composition: explain one thing at a time

The default route uses code-drawn SVG and live typography. It works without an image generator, but does not prohibit useful supplied, licensed or authorized generated imagery. See [visual director](visual-director.md) for the single image-capability policy.

## Choose the action before the layout

Give each scene one question, one main subject and one visible operation. Select supporting zones only when they answer the same question. One dominant diagram, object or image is often stronger than three equally weighted cards.

- Process: a persistent task moves along the actual route and changes state on arrival.
- Comparison: keep a common baseline and change the meaningful variable.
- Evidence: establish the context, locate the relevant detail, then return to the explanation.
- Conclusion: retire completed material and leave one readable takeaway.

Use the [shot recipes](shot-recipes.md) as combinations of existing helpers, not a fixed film grammar. Cards, diagrams, code, images and typography are tools, not quotas. Do not force unrelated technical widgets into a subject to satisfy an “anti-PPT” rule.

## Spatial hierarchy

Keep one main action visible at a time. A supplementary label, progress rail or image inset can remain quiet until its narration beat. Maintain separation between unrelated objects; do not shrink everything to fit. Put full narration in the subtitle strip and only the necessary labels in the scene.

For portrait, start with a dominant illustration and short labels. For 4:3, the supplied composition scales the landscape stage rather than fully reflowing it; inspect small scene typography on the intended player. All canvases retain native-size captions.

## Timing

1. Produce audio and semantic caption cues before finalizing motion.
2. Convert milliseconds once with `Math.round(ms * 30 / 1000)` (Python equivalent for nonnegative milliseconds: `int(ms * 30 / 1000 + .5)`).
3. Put scene windows in `manifests/asset-manifest.json`. The lecture template reads them for scene mounting, chapter chrome and scene-local time. Windows are start-inclusive/end-exclusive.
4. Use a cue's word start for an emphasis beat, minus the scene start exactly once. Estimated character timing must be listened to; it is not measured word alignment.
5. Optional scene `beats: [{frame, action}]` describe the absolute review points. They do not schedule components automatically.

The bundled lecture boundaries are 0, 213, 416, 682 and 1148; the final 21 frames protect the narration tail. Re-author semantic animation and sound after a narration change. `retime` validates metadata but cannot infer the new meaning.

## Working the template

- Preserve the aesthetic core, font/caption gates, chrome and declarative audio.
- Reuse the theme-backed `Paper`, icon set, mascot, checklist, rail and existing motion helpers.
- Change `COPY`, narration, cue selection, scene content and action timings per topic.
- `fxkit` is optional and importable in every theme. Some components retain cel-oriented styling; use `THEME.Paper` for theme-native containers rather than assuming every fxkit card automatically adopts the selected skin.
- The final skills scene demonstrates cue-timed assistance activation and retirement before the CTA. The branch demonstration shares its path data between stroke and moving object.

## Review

Watch the operation between entry and exit, not only the entrance animation. Can the viewer tell what changed and why? Does supporting art reinforce rather than repeat the narration? Are temporary parts retired? Does the next shot preserve a useful subject, direction or context?

Run project data gates, inspect the review plan's boundaries and beats, then perform one full render and actual audio/pixel review. A deliberate quiet hold is allowed; an accidental empty stage is not. A passing validator does not certify a good explanation.
