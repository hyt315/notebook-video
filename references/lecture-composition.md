# Lecture composition: make the learning relationship easy to understand

A composition succeeds when it helps the intended viewer follow the claim, evidence and relation. A moving scene is not automatically more video-like or more educational than a static diagram. **What is mandatory is an explanation—not a prescribed aesthetic or a certain amount of motion.**

## Plan from the teaching task

1. Define the intended viewer, viewing context and observable learning outcome.
2. Identify what the viewer must notice, compare, track, or infer. Verify facts, examples, units and sources.
3. Select and record one coherent visual treatment for the film. A paper-like surface is the shipped default; cel, sticker, flat or a restrained hybrid may suit a particular subject or audience. Do not leave the visual plan blank or choose a style to satisfy a numeric diversity target.
4. Create a cue-indexed storyboard. Every narration cue must be assigned to exactly one shot. Every shot must name its `coreRelation` and actual visible `visualCarrier`; the chosen scene must make that relation legible, not merely decorate it.
5. Select the simplest effective representation: labeled diagram, graph, equation, code/UI, readable text, image, staged process, animated change, or a combination. Keep evidence and comparisons needed for understanding; remove irrelevant decoration rather than necessary information.
6. Set the hierarchy, reference links, caption space and reading time. Decide when content needs to appear or change; a stable, readable view may continue across several cues.

## Reusable composition patterns

`StageFrame`, `Corridor`, `SplitStage` and `ZoomStage` are optional helpers for state-on-one-subject, meaningful paths, aligned comparisons and detail views. Use, adapt, repeat, or omit them according to the explanation. Repeated layouts, large areas of whitespace, one medium, or few components are not failures by themselves. Conversely, leaving the visual support blank is not an acceptable interpretation of simplicity.

## Text, graphics and narration

Captions make required speech accessible; narration and image may deliberately divide or reinforce information. Do not assume every channel must independently repeat everything, nor delete captions without considering accessibility and the audience. Check that the combined channels are accurate, non-contradictory, and no more redundant than the task requires.

A highlight, color change, label or sound cue should refer to the object currently being discussed. When an accent is used, synchronize it to its spoken referent; a stable view is appropriate when viewers are reading or reasoning. Not every cue needs a new element, beat, sound or animation. The human review question is whether the displayed content supports the narrated idea at that moment.

## Timing, geometry and comfort

Use cue-derived frame times where available. `resolve-shots.py` maps narration cues to shots; `validate-presentation.py` catches specific timing/reference errors and emits review prompts for subtitle speed, line length and font size. Treat its thresholds as operational heuristics, not universal human limits or WCAG text-speed requirements.

Camera movement is optional. A still camera is valid. Define the essential-content `anchor` when a zoom, pan or orbit changes framing, so `validate-shot-motion.py` can prove crop safety. Check rendered labels and captions at intended output/playback size; a design-space pixel value is not proof of phone readability.

## Rendering and learning review

After a representative frame test, render the actual film and watch it at normal speed with its narration. Verify visual-to-speech alignment, factual accuracy, legibility, reading time, overlap/cropping, overall comfort and ending. The 16:9 target is relatively mature but must still be checked for the specific film. 4:3 and 3:4 require separate layout passes and remain unknown until actually rendered. Automated gates cannot establish comprehension, transfer, viewer comfort or preference; test with viewers before making those claims.