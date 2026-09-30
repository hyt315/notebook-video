# Composition gates: verify omissions and technical errors, not aesthetic quotas

The build-time checks in `scripts/validate-composition.py` and `scripts/validate-shot-motion.py` verify inspectable facts about a shot plan and camera geometry. They do **not** score teaching quality, artistic taste, visual density, or the quantity of motion/components.

## What remains mandatory

Every narration cue must be covered by exactly one resolved shot. Each shot must declare a meaningful `coreRelation` (the idea/relationship it teaches) and `visualCarrier` (the actual visible support), and each authored shot function must contain a recognizable visual JSX node. An audio-only function, blank shot, or generic placeholder cannot count as the carrier. A still diagram can support one cue or a range of cues; it does not need a new animation for each sentence.

These are inspectable declarations and source-shape checks, **not semantic proof**. They cannot determine whether the displayed material truly explains the narration. Watch the render to establish that.

## Build checks

`validate-composition.py` blocks:

- no shots, missing cue metadata, a cue with zero or multiple covering shots, missing/placeholder `coreRelation` or `visualCarrier`, or a shot function with no recognizable visual JSX;
- a shot whose scene function cannot be found when scene sources exist;
- unknown camera-intent, transition, or entry enum values;
- a declared reveal transition with no matching reveal in its shot, an inconsistent cut/reveal declaration, or a handoff without a matching carrier in the next shot;
- an out-of-range local beat index, a reference to a nonexistent shot's beat list, or a relative import of a missing named export.

`validate-shot-motion.py` blocks:

- gaps/overlaps in the resolved shot timeline or failure to cover the declared duration;
- transformed camera keys whose frames are unordered or do not span the shot, zoom/rotation/pan outside safe limits, or a transformed camera without an explicit anchor;
- an essential-content anchor outside the visible window at any key, and a render camera declaration that runtime would silently clamp.

A neutral still camera needs no meaningless anchor. Declaring a non-still intent without actual change is a P1 note, not a reason to add motion. When a project supplies a `contentBand` and the selected `cel`/`flat` background treatment has a known decorative overlap, the composition checker can issue a P1 prompt to verify readability/cover; no background or skin is immutable.

## What is deliberately not a gate

The validators do not require a minimum number of skeletons, media types, active components, beat changes, transitions, entries, camera moves, occupied zones, or filled lower-screen area. Repetition, whitespace, and still frames can be appropriate. Lack of actual visual support is still a failure under the required cue/shot fields and source check above.

## Run

```text
python scripts/resolve-shots.py PROJECT_DIR
python scripts/validate-composition.py PROJECT_DIR
python scripts/validate-shot-motion.py PROJECT_DIR
```

Both checks use Python's standard library. Use `--json` for structured output and `--strict` to make composition P1 prompts fail a local test run. A P1 prompt is not automatically an aesthetic defect; review it against the rendered scene.

## Browser/runtime checks

The template separately runs `CaptionFitGate`, `CardFitGate`, `OverlapGate`, `ClippingGate`, and `CanvasBoundsGate` for layout, overlap, clipping and text-bound issues. The lower-quarter `FillGate` and `StageFrame`'s `SlotGuard` are not mounted as default quality requirements; `SlotGuard` remains available as an optional diagnostic. See each implementation and `SKILL.md` for the active gates. A motion-gap script is an optional post-render diagnostic, not a pass/fail quality rule.

Passing every automated gate does not establish factual accuracy, caption comfort, semantic alignment, learning, or audience preference. Review the complete rendered film with audio and intended display sizes.