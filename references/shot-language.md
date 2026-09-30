# Camera and shot framing: optional movement, provable safety

The camera helpers in `assets/lecture-template/src/shotkit.tsx` provide deterministic framing. Their purpose is to keep the essential subject in view when a shot uses camera transforms—not to make every shot move. A still camera is a valid default.

## Supported intents

The intent is a description for authoring and zoom budgets. It is not a requested movement count.

| Intent | Use when it helps | Notes |
|---|---|---|
| `establish` | Establish a scene or spatial relationship | A small move is optional |
| `push-in` | Inspect a detail or focus attention | Prefer legible larger text over raster-softened camera zoom |
| `pull-back` | Restore context or show more of a relationship | Keep the relevant objects in the safe view |
| `pan-follow` | Follow a meaningful object along a route | Pan must be covered by zoom budget |
| `reveal` | A reveal itself communicates the idea | Coordinate with the visual reveal, not as generic transition |
| `micro-orbit` | A spatially meaningful hero merits subtle orbit | Avoid when it distorts labels or diagram geometry |
| `still` | No camera motion | Valid for any duration; not a failure |

## Camera-safe geometry

The current safe-pan implementation is based on a **1920×1080 design space** with center `(960, 540)`. At scale `s`, the visible window half-size is `960/s` by `540/s`; the approximate safe-pan budget is:

```text
maxPanX = 960 × (1 − 1/s)
maxPanY = 540 × (1 − 1/s)
```

`camAt()` clamps a path to the budget. `validate-shot-motion.py` checks the requested path, zoom limits, angle limit, timeline/keyframe coverage, and the `anchor` when the camera transform changes. Keep the validator and runtime formula in sync: a declared path that will be silently clamped is a concrete implementation mismatch.

An `anchor` is the rectangular region containing the information that must remain visible. Supply it for any zoom, pan, or orbit path. A neutral `still` path has no framing change and does not need an anchor. If an anchor is supplied for a still shot, it can document the important subject, but it does not create a movement obligation.

## Boundaries and canvas status

For text-bearing shots, the current zoom budget is 1.35; graphic-only shots may use up to 1.60. These are implementation safeguards against clipping/softening, not targets. The current camera proof assumes the 16:9 1920×1080 design space. The 16:9 route is the primary target and must still be rendered and inspected for each changed film. 4:3 and 3:4 camera/layout behavior is **not adequately verified** here; do not infer that the 16:9 proof validates those aspect ratios.

Page headers, captions, and chapter chrome should remain outside a moving subject layer if that keeps them stable and readable. Movement and foreground composition must be considered together; a safe camera anchor does not prove that captions or labels are comfortable at phone size.

## Example shot metadata

```json
{
  "id": "S1",
  "cues": [0, 3],
  "camera": {"intent": "still"}
}
```

A moving shot adds the path and anchor:

```json
{
  "id": "S2",
  "cues": [4, 6],
  "camera": {
    "intent": "pan-follow", "at": 10, "dur": 45,
    "fromX": 900, "fromY": 540, "x": 1020, "y": 540,
    "from": 1.08, "to": 1.08
  },
  "anchor": {"x": 300, "y": 260, "w": 1320, "h": 500}
}
```

`resolve-shots.py` expands the semantic camera description into frame-keyed data. Do not hand-edit generated camera keys. Run `python scripts/validate-shot-motion.py PROJECT_DIR` to check the declared path. Then inspect actual frames at scene boundaries and during the move; the checker proves geometry, not visual quality.

## Review questions

Ask whether the move explains a relationship, exposes evidence, or guides attention to the currently spoken object. If its answer is no, leave the camera still. Check that motion does not conflict with the caption strip, distort a comparison, create edge exposure, or make a useful label hard to read. There is no minimum number of moves or distinct intents.