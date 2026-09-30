# Delivery acceptance checklist

This checklist separates **hard technical failures**, **human visual review**, and **audience-learning evidence**. Passing scripts proves only the checks they actually perform; it does not prove the film is clear, comfortable, attractive, or educational.

## 1. Learning and story

- State the intended learning outcome and the important claim or relationship in plain language.
- Check factual claims, units, examples, calculations, and source provenance. A diagram, spoken claim, and displayed number that represent the same concept should derive from the same data/model where practical.
- Read the narration while viewing its corresponding frames. Every cue must have a readable visual carrier and each shot plan must state the core relation it teaches; verify that the rendered picture actually explains that relation. A cue does not have to produce a new animation: the viewer may still be reading or reasoning about the current image.
- Preserve the information needed to understand the topic. Remove irrelevant decoration, not necessary explanations, captions, comparisons, or evidence merely to make a scene look simpler.
- Allow still frames and reading holds when they help the viewer orient, inspect, or think. The required instructional task is visual support for the narration and its core relations; the chosen skin, camera moves, scene skeletons, media kinds, zones, state changes, and moving components have no minimum count.
- Treat a silent-viewing pass as a diagnostic, not a universal rule: some videos should work without narration; others intentionally rely on spoken explanation and accurate captions.

## 2. Visual design and comfort

- Choose a visual treatment because it supports the subject, audience, and intended tone. `paper`, `cel`, `sticker`, and `flat` are optional vocabularies, not required identities or quotas. A restrained hybrid is acceptable when it improves comprehension.
- Give each frame a readable hierarchy. Whitespace is allowed; do not fill it merely to satisfy an area or density target.
- Use a component only when it is actually rendered and helps explain, compare, locate, or remember something. A library inventory or attractive still frame alone is not evidence of usefulness.
- Check actual output-size contrast, glyph rendering, text wrapping, diagram labels, crop/overscan, and overlap. Follow WCAG contrast requirements where applicable; do not describe subtitle speed or minimum display time as WCAG thresholds.
- Inspect the 16:9 output at native size and as a 390-pixel-wide phone preview as a practical diagnostic, then check a real target device if available. This is not a universal pass/fail pixel threshold.
- **Canvas status:** 16:9 is the user's relatively mature target, but still needs review on each changed film; it is not presumed good. 4:3 and 3:4 have not been adequately tested here; report their status as unknown, not as good or defective.

## 3. Captions and audio

- Captions accurately represent the required speech and meaningful non-speech audio, use natural semantic breaks, and remain synchronized with the narration.
- Review the longest and fastest cues at the intended playback size. Reading-speed, line-length, and design-pixel measurements are prompts to inspect, not proof of comfort.
- Listen to the complete film at normal speed. Speech must be intelligible; no missing, clipped, delayed, or accidentally duplicated sections. Sound effects should correspond to a meaningful audible/visible event and should not compete with speech. The template defaults to narration-only; add music only after an otherwise-identical with/without A/B indicates it helps this lesson.
- Check measured duration, peak, loudness, sample rate, and channel layout against the requested delivery specification. Record measurements rather than claiming a target was met without checking it.

## 4. Render and delivery integrity

- Source compiles; lockfile and declared dependencies match the rendered project. Do not add a dependency just to imitate a reference project.
- Timeline, word timings, captions, animation, and sound use the same frame-rate convention. Frame output is deterministic.
- Confirm canvas dimensions, native frame rate, codec, audio stream, duration, and complete ending. Inspect first/last frames, scene boundaries, long captions, and representative key visual events.
- Review a contact sheet for overall pacing and hierarchy; if a scene contains rapid motion, additionally inspect a short frame strip. Do not use motion-gap software to classify deliberate stillness as a defect.
- Resolve actual clipping, overlap, missing assets, malformed text, stale timeline, and encoding errors. Do not alter a validator threshold only to make a render pass.

## 5. Audience evidence

A creator review is not a blind viewer test. If learning or comfort improvement is claimed, compare the same content and audio under blinded labels, with representative viewers who do not know the implementation. Ask about comfort, the intended takeaway, and a concrete transfer/application question; separate correctness from confidence or aesthetic preference. Record audience size and limitations. Do not invent or infer outside feedback when no participants were available.

## 6. Do not mistake these for goals

No minimum number of styles, media types, camera moves, animated elements, layout zones, effects, or components; no requirement to fill the lower quarter; no penalty for a static explanatory hold. Their use is judged by whether it helps the particular teaching task.
