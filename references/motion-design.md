# Motion design contract

## Contents

- [Cadence](#cadence)
- [Standard motions](#standard-motions)
- [Camera Micro-Framing Invariant](#camera-micro-framing-invariant-镜头微运镜与防出界铁律)
- [Anti-PPT Functional Component Invariant](#anti-ppt-functional-component-invariant-反-ppt-实体交互组件铁律)
- [Transitions](#transitions)
- [Stop-motion accent](#stop-motion-accent)
- [Rejection flags](#rejection-flags)

## Cadence

Deliver at native 30fps. Keep scene constants, physical poses, subtitle reveal and output in the same 30fps coordinate system. Do not duplicate frames into a 60fps container. For an intentional stop-motion accent, quantize only that component to 15fps so each pose holds for two output frames.

The global camera moves: **CameraRig** wraps every scene as one continuous track on the delivery canvas (per-canvas keyframe tables: 16:9 and 3:4; 4:3 reuses the landscape track). Keep scale always >=1 so the canvas never shows outside the stage, and keep the built-in exponential lag follow-focus. Use a subtle focus adjustment only when it supports attention; it is not required per chapter. Chrome and subtitles remain outside the rig.

Keep stable layout coordinates fixed and animate movement with `translate3d`, rotate, scale and opacity. Mount only the active scene, plus the incoming scene during a short transition.

## Standard motions

- Camera push: chapter level, subtle breathing scale 1.00 ~ 1.018, horizontal drift strictly bounded within ±15px (x between 945 and 975), focus follows narration target without displacing active elements.
- JumpInText title: per-glyph 3D flip-in (rotateX ~88deg from the baseline, 12px rise, spring over-bounce, ~1.6-frame stagger). Always for chapter and scene titles.
- WaveText latin: per-letter wave typing with a color gradient (10-frame wave, 4 keyframe offsets), for CTA latin strings.
- Figure roll-in: multi-keyframe rotation (150deg to 360deg with a mid-scale bulge) instead of a plain pop for emblem graphics.
- Subtitle reveal: one word at a time with a short 6px fade-slide and the cue file's lead (normally 60ms, at most 80ms); do not apply a second lead to the cue start; all trailing punctuation strictly eliminated; never a decorative bar.
- Paper entry: cubic ease-out, one 8–13% overshoot, settle within about 0.8s.
- Paper lift: raise position and increase shadow distance/blur while lowering shadow alpha.
- Paper landing: close/darken shadow, compress no more than 3%, then settle once.
- Curved transfer: follow the same SVG geometry as the visible rail; do not approximate with a different sine path.
- Directed data line: animate `stroke-dashoffset` only from sender to receiver during transfer.
- Check state: scale 0 → 1.12 → 1 and add one soft chime.
- Slot insertion: remain above the base until crossing the slot, then pass behind the front lip.
- Complete exit: move the entire component outside the canvas or remove it after it is fully out; never leave a clipped corner.
- Character reaction: move separate arms, face or body parts; do not wobble one flattened character image.

## Camera Micro-Framing Invariant (镜头微运镜与防出界铁律)

To eliminate the static PPT feeling while preventing any active narration content from being pushed out of frame:

1. **Strict Spatial Bounds (硬性位移约束)**:
   - On 16:9 canvas (1920×1080 design stage):
     - Horizontal position `x` is strictly bounded within `[945, 975]` (drift `≤ ±15px`);
     - Vertical position `y` is strictly bounded within `[538, 542]` (drift `≤ ±4px`);
     - Scale `s` is strictly bounded within `[1.00, 1.018]` (gentle breathing);
   - On 3:4 portrait canvas (1080×1440 design stage):
     - Horizontal position `x` is strictly bounded within `[530, 550]`, vertical `y` within `[710, 730]`, scale `s` within `[1.00, 1.02]`.

2. **Semantic Synchronization (语意跟随)**:
   - When narration explains the left card, concept, or terminal, the camera micro-drifts gently leftward (`x ≈ 948`);
   - When narration shifts to the right data, benchmark, code block, or CTA, the camera micro-floats rightward (`x ≈ 974`);
   - When transitioning between chapters or holding both sides, reset to center (`x = 960, s = 1.00`).

3. **Absolute Rejection Flags**:
   - Reject offsets outside the selected canvas bounds above; portrait uses its own (540,720) center;
   - Moving camera away from the currently narrated card is strictly rejected;
   - Any camera motion that causes the active narration card to come within 60px of the viewport edge is strictly rejected.

## Anti-PPT Functional Component Invariant (组件防 PPT 化与功能实体化)

Prefer an observable operation over a generic bullet stack. Reuse these specialized components only when they actually match the content; they are not mandatory and their idle motion alone does not explain a mechanism:

- `BrainwaveEEG`: Oscilloscope cognitive pulse wave; flatlines to a straight red line upon session exit, memory flush, or failure.
- `VectorRadarSonar`: Circular radar display with rotating scan line, vector cluster dots, and ANN metrics.
- `BM25TokenRibbon`: Dynamic inverted index symbol meter with token tags and match scores.
- `HookMountBay`: Modular connector dock where agent hook plug visibly inserts into target port and lights up green.
- `RedactionScanner`: Real-time security preview with a red laser scanner sweeping over sensitive tokens and masking them to `[REDACTED_SECRET_KEY_*****]`.
- `ChipContract`: Floating micro-hardware chip contract with LED indicators and pin headers moving along data pipelines.

## Locked motion pack

- Spring presets: use `popS(f, start, preset)` with `SPRINGS` — `snappy` for small UI ticks and code lines, `soft` (identical to the legacy `pop`) for cards and lists, `bouncy` for callouts and celebratory beats. Do not hand-tune new damping/stiffness values per scene.
- Scene transitions: wrap the incoming scene in `TransitionIn` (`flip` = page turn when the metaphor changes, `slide` = cover-over for a lateral topic shift, `wipe` = edge reveal for a detail focus). Default to non-overlapping cuts. A deliberate overlap may mount at most two scenes with explicit ownership and no duplicate labels. A persistent image bridge can instead span the attention shift inside one scene without changing timeline duration. Only the incoming scene carries the transition effect. Use at most one transition style per film and keep clean cuts elsewhere.
- Camera script: build new keyframe tracks with `camScript(x, y, duration).hold(f).to(f, {x, y, s}).done()` instead of raw keyframe tables; it guarantees first/last frame coverage. The same easing and exponential lag follow-focus apply.
- Stop-motion accent: `useSteppedFrame(15)` quantizes a component to 15fps so each pose holds two output frames. Reserve it for sticker-style charm; never apply it to subtitles, transfers or the camera.
- Component motion stays inside the locked library: `Connector` animates dash flow only during transfer, `Checklist` rows slide in with staggered `soft` springs, `CodeBlock` lines enter with `snappy` springs, `CountUp` eases with the standard soft-out curve.

## Scene grammar

Build progressively:

1. stable chapter and hero;
2. supporting semantic parts;
3. relationship or transfer;
4. local feedback;
5. readable hold;
6. remove obsolete parts completely.

Aim for meaningful semantic changes around spoken beats, often 2–4 seconds apart; allow a longer intentional reading hold. Do not count random drift, blinking cursors, animated texture, global zoom or constant line motion.

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
