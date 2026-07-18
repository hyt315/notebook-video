# Motion design contract

## Cadence

Deliver at native 30fps. Keep scene constants, physical poses, subtitle reveal and output in the same 30fps coordinate system. Do not duplicate frames into a 60fps container. For an intentional stop-motion accent, quantize only that component to 15fps so each pose holds for two output frames.

Keep the camera fixed. Motion belongs to independently modeled objects.

Keep stable layout coordinates fixed and animate movement with `translate3d`, rotate, scale and opacity. Mount only the active scene, plus the incoming scene during a short transition.

## Standard motions

- Paper entry: cubic ease-out, one 8–13% overshoot, settle within about 0.8s.
- Paper lift: raise position and increase shadow distance/blur while lowering shadow alpha.
- Paper landing: close/darken shadow, compress no more than 3%, then settle once.
- Curved transfer: follow the same SVG geometry as the visible rail; do not approximate with a different sine path.
- Directed data line: animate `stroke-dashoffset` only from sender to receiver during transfer.
- Check state: scale 0 → 1.12 → 1 and add one soft chime.
- Slot insertion: remain above the base until crossing the slot, then pass behind the front lip.
- Complete exit: move the entire component outside the canvas or remove it after it is fully out; never leave a clipped corner.
- Character reaction: move separate arms, face or body parts; do not wobble one flattened character image.

## Scene grammar

Build progressively:

1. stable chapter and hero;
2. supporting semantic parts;
3. relationship or transfer;
4. local feedback;
5. readable hold;
6. remove obsolete parts completely.

Cause one meaningful semantic change every 2–4 seconds. Do not count random drift, blinking cursors, animated texture, global zoom or constant line motion.

## Spatial density budget

- Divide the 1920×1080 design stage, rendered inside the 2560×1440 composition, into explicit work zones before animating.
- Give each large object a stable home zone and reserve the center corridor for transfer only.
- Keep unrelated paper objects at least 70px apart, including their airborne shadows.
- Allow one dominant transfer object in the corridor at a time.
- Prefer 3–5 large semantic objects over 8–12 small decorative objects.
- Remove, cover or move completed objects fully before the next semantic group arrives.
- If the frame feels crowded, increase object size and redistribute it; do not solve crowding by shrinking everything.

## Continuous process rule

When the narration describes one task moving through several steps, keep one persistent task card. Move it along one visible path and change its label, color or status at each station. Do not replace it with a newly spawned card unless the narration explicitly describes a new object.

## Physical assembly rule

Model the slot, front lip, inserted part and status feedback as separate layers. Keep the part above the base before crossing the slot. After crossing, lower its z-order beneath the front lip and fade or translate it to complete invisibility. At the end of insertion, assert that no pixel-sized corner remains outside the machine.

## Duration guidance

- 30 seconds: 5–7 scenes.
- 60 seconds: 3–4 acts with small internal steps.
- 2–3 minutes: 8–12 sections, usually 10–20 seconds each.

Use a clean cut when the metaphor changes. Continue progressive construction while the same concept develops.

## Restraint

Do not apply every effect to every object. Dynamic shadow requires actual lift. Data pulses require an active transfer. Sound requires a visible action. Keep fixed panels fixed.
