# Delivery acceptance checklist

## Story

- A concrete, verified payoff or tension is visible within 1.5 seconds; an honest open loop follows by 8 seconds.
- Each scene has one main idea and one physical action.
- The visual story remains understandable without narration.
- The opening gives a concrete, verified payoff or tension before context, and the storyboard identifies a later evidence-based callback.
- A meaningful state changes every 2–4 seconds.
- The final message holds at least one second.

## Architecture

- React + TypeScript + Remotion is the primary renderer.
- TTS milliseconds convert once to integer frames.
- Subtitle, animation and sound share the same FPS convention.
- Fonts and media resolve before the first rendered frame.
- Action audio is declared with its visible action.

## Visuals

- Background, chapter, header and subtitle match the canonical example.
- Every scene declares one primary mode: `image-text`, `pure-text` or `pure-graphic`.
- Concrete subjects use original, supplied or licensed imagery when seeing the subject materially improves comprehension.
- Generated imagery contains no baked labels, charts, logos or UI text; exact information remains in Remotion.
- Every raster is registered in `visual-assets.json` with source, prompt/description, crop policy and rights.
- Image scenes synchronize recognition, callout, relation and conclusion instead of placing a static image beside unrelated copy.
- Generated images receive only restrained crop reveal or push-in motion; annotations move independently.
- Every independently moving object is an independent component.
- Every large object has one home zone and one destination zone.
- Unrelated cards keep at least 70px separation, including airborne shadows.
- The central corridor contains at most one dominant temporary transfer object.
- A continuous process preserves one task object and changes its state at real stations.
- Floating objects stay above lower bases.
- Slot occlusion begins only after a visible crossing.
- Inserted modules finish fully behind the front lip with no residual fragment.
- Temporary components exit completely; no half corner remains.
- Dynamic shadow changes only when paper lifts.
- In the official v9 engine, paper uses its locked lift-linked contact/environment shadow recipe; no component invents a conflicting shadow.
- In the official v9 engine, display, title, body, label and micro copy use its locked type scale.
- In the official v9 engine, system glyphs and emoji are not used as production icons; use its locked line-icon language.
- In the official v9 engine, the whole-film grade is static and restrained; no animated grain or moving light texture.
- In the official v9 engine, ordinary production edits stay inside `COPY`, narration, semantic captions, visual plan, registered image assets, timing and topic-specific scene objects.
- Data dashes move only during a real transfer and in the correct direction.
- Text-bearing paper has visible padding on all sides.
- Exact Chinese text and real brand assets are preserved.
- No malformed labels, invented logos or softened Chinese glyphs.
- No large accidental empty area during a spoken explanation.
- No clutter from unrelated dots, scraps, steam or continuous movement.
- No effect stack, miniature card pile or unused half-visible layer remains on screen.
- No global zoom, shake, animated noise, posterize or full-screen page turn.

## Subtitle

- Clean white torn-wave input is present in every scene.
- No dark border, black side mark, inner line or rounded search-bar shape.
- One centered line, 40px Source Han Sans CN.
- `CaptionFitGate` measures every fully revealed cue with the loaded Source Han font in the real render browser; every cue fits within 1334px.
- Partial reveal does not shift horizontally.
- Orange locator and blue ring remain fixed.
- Internal punctuation remains; trailing punctuation is hidden visually.
- Caption segmentation is explicitly `semantic`, never `draft-character-count`.
- Every model/product name, benchmark, number-plus-unit expression and fixed technical term is listed in the protected-phrase manifest.
- No protected phrase crosses a cue boundary; no ASCII identifier is split between cues.
- Cue words flatten to the exact TTS word stream.
- Caption timing leads measured speech by no more than about 80ms.

## Audio

- Correct voice and complete narration.
- No hidden voice delay.
- Effects land on visible actions.
- Speech remains dominant.
- Integrated loudness is about -16 LUFS.
- True peak is no higher than -1.5dBTP.

## File validation

- H.264 video and AAC audio are present.
- 2560×1440 at native 30fps unless the user explicitly requested a genuinely native high-frame-rate production.
- Audio is 48kHz stereo.
- Video duration includes at least 0.7 seconds after narration.
- No black frames or truncated ending.
- No unintended scaling or softening pass.
- Contact sheet includes every scene.
- Films over 60 seconds include at least 24 evenly spaced frames plus dense motion sheets for the two most complex movements.
- Opening, scene boundaries, longest caption, hover/insert midpoints and closing frame are inspected manually.
- Opening range 0–360 is inspected at 0.5s, 2s, 4s, 8s and 10s; the primary claim is visible by 1.5s and the deferred question is paid off later.

Do not update the skill from a design proposal. Update only after the user approves the actual rendered film.
