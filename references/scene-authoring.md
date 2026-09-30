# Scene authoring: from learning goal to a rendered explanation

This guide is a workflow, not a copy-this-layout mandate. Reuse the template engine and components where helpful, but let each film's content determine its storyboard and visual form.

## 1. Before the shot table

1. State the intended viewer, viewing context, and one or more learning outcomes.
2. Write the factual narration and semantic caption cues; check claims, units, examples and source provenance.
3. Decide which information belongs in speech, captions, and visuals. Keep what the viewer needs; remove irrelevant decoration, not evidence or explanation.
4. Choose and record a coherent visual treatment for the film. If the user has no preference, the shipped `paper` treatment is a sensible explicit default. `cel`, `sticker`, `flat`, or a restrained hybrid may fit another audience or concept. Do not leave the choice implicit or select a skin solely to fill a quota.
5. Sketch the storyboard as relationships first: what must the viewer notice, compare, follow, or infer? A storyboard may reuse a layout; it need not rotate through all helper types.

## 2. Cue-indexed shot plan

`manifests/shots.json` is the semantic source of truth. Write cue indices, not frame numbers; `resolve-shots.py` derives timing from the caption cues. Each cue must be covered by exactly one shot. A single shot and one clear static image may support several cues when that image genuinely explains them.

Every shot must include:

- `coreRelation`: the key concept, comparison, causal link, step, or takeaway it teaches.
- `visualCarrier`: the visible diagram, text, chart, image, code/UI, example, or meaningful state depiction that supports the relation.
- `cues`: inclusive first/last narration cue indices covered by that shot.

The particular medium, skeleton, skin, camera move, beat-level reveal and animation are chosen only when they improve explanation. Missing visual support is not optional: a shot that is merely decorative or blank does not satisfy the task. These declarations make omissions inspectable but cannot prove semantic correctness; that is decided by reviewing the actual film with its narration.

Example of a readable static relationship; there is no movement quota:

```json
{
  "duration": 900,
  "theme": "paper",
  "canvas": "16:9",
  "shots": [{
    "id": "S1",
    "chapter": "Request and response",
    "cues": [0, 2],
    "coreRelation": "A request reaches the server before the server returns a response.",
    "visualCarrier": "A labeled two-way arrow diagram remains on screen through these cues.",
    "camera": {"intent": "still"},
    "transition": "cut"
  }]
}
```

A production manifest with additional constraints (audio duration, tail frames, protected phrases, canvas mode) must obey the values of that project. Do not copy the example duration blindly.

## 3. Draw the scene

- Use one clearly organized visual hierarchy. Assign space for captions and labels, and choose their size by testing the final output at its actual intended display size.
- Put highlights beside or on the object currently being described; synchronize changes to the word or phrase they refer to. No change is needed while a stable image is still being read or reasoned about.
- Use an existing component when it performs a clear job. Prefer direct diagram/text/SVG when simpler. Do not implement a mature open-source component from scratch merely to avoid a permitted, locked dependency.
- Components and compositional helpers are not goals by themselves. Verify that a cited component is called and visible in the rendered scene and contributes to understanding.
- `ShotCamera` is useful when a shot has a chosen move. A static camera is valid; omit an `anchor` if framing never changes. When a zoom, pan, or orbit changes framing, define the essential-content `anchor` and let the safety validator check every camera key.
- Keep time frame-deterministic: animations must be pure functions of the Remotion frame, not CSS autoplay, wall-clock timers or random values. If an element enters, use cue-derived timing when the narration gives a meaningful anchor.

## 4. Validate and render

Run from the project directory:

```text
python scripts/resolve-shots.py PROJECT
python scripts/validate-shot-motion.py PROJECT
python scripts/validate-composition.py PROJECT
python scripts/validate-presentation.py PROJECT
npm run typecheck
npm run render
```

The checks can verify timeline integrity, cue coverage, required relation/carrier declarations, recognizable scene JSX, and geometric camera safety. They cannot check whether the content is true, whether the picture actually explains the words, or whether the pacing feels comfortable.

After a representative still/contact sheet, render the whole film. Inspect first/last frames, each shot boundary, longest captions, key diagrams/highlights, visible overlaps/clipping, and any frame with fast movement. Then watch the **complete film at normal speed with audio**: compare each spoken phrase with the visual, allow enough time to read, and listen for distracting or mistimed sound. Review the 16:9 output at native size and in a 390-pixel-wide phone preview; evaluate other aspect ratios separately and label them untested if not rendered.

A rendered example or creator review is not a blind audience study. Do not claim improved learning, comfort, or comprehension without appropriately blinded viewers and a fit-for-purpose task.