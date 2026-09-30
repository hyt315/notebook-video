# Scene structures and the shot table

The template includes four composition helpers in `assets/lecture-template/src/stagekit.tsx` and `src/skeletons.tsx`. They solve recurring layout problems, but are not a mandatory taxonomy: a project need not use all of them, rotate among them, or force a fixed content density.

| Helper | Useful for | Consider another representation when |
|---|---|---|
| `StageFrame` | One subject or mechanism with named states, labels, or evidence | A single diagram, chart, or still image communicates the relationship more clearly |
| `Corridor` | An object/state moves through meaningful stations | No spatial path or process is part of the claim |
| `SplitStage` | Comparing aligned alternatives or before/after states | A table, overlaid graph, or sequential comparison makes values easier to compare |
| `ZoomStage` | Show context, inspect one detail, then restore context | The detail is already legible or a label/arrow is enough |

Do not force a minimum state count or make a large frame fill a fixed area. Still poses and static teaching holds are valid. **The optional items are the particular skin, skeleton, medium, movement and decorative treatment—not whether the narrated learning task receives visual support.**

## Cue-indexed shot table

`manifests/shots.json` is the semantic input. Every narration cue must be covered by exactly one shot. A shot may cover several cues; the same clear static diagram, labeled text, chart, image, or process view may support them when it genuinely explains all of them. A cue does **not** have to cause a new object, animation, sound, or camera move to appear.

Each shot must state two concise editorial facts:

- `coreRelation`: the concept, comparison, causal relation, or learning point the covered narration is meant to establish.
- `visualCarrier`: what the viewer actually sees that makes that relation legible (for example, a labeled diagram, a worked step, an aligned comparison, a highlighted source object, or readable text).

These fields and the source JSX are checked for missing declarations/nodes. They cannot prove that the chosen picture truly matches the spoken words; that remains a human review of the rendered film. A real visual can still be semantically wrong, so do not treat a passing validator as an instructional-quality certificate.

Example: one still visual supports a three-cue explanation without inventing motion:

```json
{
  "duration": 900,
  "canvas": "16:9",
  "shots": [{
    "id": "S1",
    "chapter": "What changes",
    "cues": [0, 2],
    "coreRelation": "The client request reaches the server before the response returns.",
    "visualCarrier": "A labeled request-and-response diagram remains visible through all three cues.",
    "camera": {"intent": "still"}
  }]
}
```

`resolve-shots.py` derives frame timing from `caption-cues.json`; do not hand-code absolute frame numbers for timing that can be resolved from cue data. It creates `src/shots.ts` and `manifests/shots.resolved.json`. Blocking checks cover a valid continuous timeline, cue indices in range, shot coverage of all narration cues, correct duration, and camera-key coverage.

`anchor` is required when a camera zoom, pan, or orbit changes framing; it identifies the rectangle containing essential content for geometric safety proof. A neutral still camera does not need an anchor. `beats`, `skeleton`, `media`, `live`, `zones`, `bottomFill`, `move`, `evidence`, `hold`, and `misconception` are optional authoring notes; none is a quality quota. If beats are supplied, they must reference valid cues and remain within the shot's timing.

## Existing helpers

Use geometry and transitions in `stagekit.tsx` / `skeletons.tsx` when they serve the scene; prefer one clear visual relationship over assembling several helpers. Edit project-local content first. Add a new reusable skeleton only when a recurring, demonstrated need cannot be handled well by an existing helper. A single scene can remain local to its project.