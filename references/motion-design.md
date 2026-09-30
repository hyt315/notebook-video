# Motion design: make change carry meaning

Keep all frame-driven animation deterministic: the same source, asset, and frame should produce the same output. Use the template helpers and locked dependencies where they are useful; do not add a library merely to create more effects.

## Decide whether to move

Start from the learning task. Animate when a visible change explains a process, makes a comparison easier to follow, directs attention to the currently spoken object, or supplies meaningful feedback. A still image, formula, graph, or posture is valid when it gives the viewer time to orient, read, compare, or reason. There is no quota for camera moves, animated objects, effects, or ongoing background motion.

Avoid movement that only fills time, repeats an already clear cue, competes with captions or narration, or changes an object without an explanatory reason. Do not add music or a sound effect to every motion. Use a cue when it makes a real, perceptually useful event clearer; align it with the corresponding visual and spoken moment.

## When movement is useful

- Preserve a clear starting pose and destination state. Introduce one important change at a time when simultaneous changes would make the relationship hard to see.
- Match timing to spoken explanation and audience reading time. A transition can be quick; the meaning of the resulting frame may need to hold.
- Use easing, anticipation, follow-through, weight, or an arc where those physical cues clarify what is happening. They are craft techniques, not mandatory effects for every object.
- Keep labels, equations, numbers, and important reference geometry stable enough to read. Do not animate numerical values through states that could be mistaken for factual data.
- Prefer transforms for moving elements; do not create accidental layout reflow or clipped edges.
- If one entity changes state, consider keeping it visually identifiable across the change. If the concept is comparison, preserve aligned baselines and stable labels.

## Camera safety and framing

The camera is optional per shot; `still` is a valid default. When a camera path is used, provide an `anchor` describing the essential subject. `validate-shot-motion.py` verifies timeline coverage, camera bounds, safe pan/zoom, and anchor visibility at the keyed positions. Those geometric failures remain blocking because they can silently crop the teaching target. A declared non-still intent with no actual camera change is only a P1 note; it does not mean a shot must move.

Use the available intent vocabulary as descriptive tooling, not a required mix of intents. The output canvas and caption-safe area constrain camera paths. Inspect actual sampled frames because keyframe arithmetic does not prove all visual content is legible.

## Timing and audio

Captions, voice timing, visual events, and sound cues should use one documented frame-rate convention. Generated cue times must be reproducible. Preserve semantic words and units; do not speed through dense material to fit a predetermined shot count.

Where a highlight, pointer, or sound cue is used, check that it refers to the same object currently named in the narration. A stable frame with narration can be more informative than an animated but mismatched cue.

## Review

Inspect representative entrance, state-change, transition, and hold frames at actual output size. Watch and listen to the complete film at normal speed; contact sheets supplement but do not replace playback. A stillness detector is not a quality gate: it can report candidate intervals for human inspection, but it cannot know whether a pause is intentional.