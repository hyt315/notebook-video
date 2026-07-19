# Visual director and generated-image workflow

Use this reference before storyboarding scenes. The skill remains provider-neutral: image generation is an optional capability enhancement, not a runtime requirement.

## 1. Choose the visual mode from meaning

Assign exactly one primary mode to every scene before building it.

| Scene meaning | Primary mode | Typical treatment |
|---|---|---|
| Concrete object, place, person, atmosphere or visual transformation | `image-text` | Generated or supplied image plus Remotion labels, highlights, arrows and conclusion text |
| Contrast, slogan, misconception, keyword or emotional beat | `pure-text` | Scale, replacement, underline, staggered explanation and typographic rhythm |
| Process, system, relationship, quantity or state transition | `pure-graphic` | SVG paths, nodes, tracks, cards and state changes |

Use `image-text` as the normal choice when a concrete subject benefits from being seen. Use the other modes deliberately; do not force a bitmap into an abstract relationship or turn every sentence into a poster.

## 2. Detect available image capability

Before the storyboard, inspect the current environment for an image-generation tool.

- In Codex, use the built-in `imagegen` skill and image-generation tool when available.
- In another agent or local environment, use an equivalent authorized provider, user-supplied assets or licensed assets.
- If no generator is available, keep the same storyboard and replace the image layer with native SVG/Remotion illustration. Do not block the whole video.
- Honor a user request to avoid generated images or external services.

When image generation is available and not prohibited, generate original support art by default for hero shots, concrete explanations and atmosphere shots where it materially improves comprehension or promotion value. Do not ask for another confirmation unless a required reference image is missing.

## 3. Generate assets for animation

The generated bitmap is an input layer, never the finished video.

Every prompt should specify:

1. subject and explanatory purpose;
2. the official warm-ivory notebook/cut-paper/watercolor art direction;
3. 16:9 or the exact target crop;
4. the side or region that must remain visually quiet for overlays;
5. separated subjects that can be highlighted independently;
6. no baked captions, labels, charts, logos or UI text;
7. no decorative clutter in the subtitle safe area.

Generate diagrams, arrows, exact labels and data with SVG/HTML inside Remotion. Image models provide atmosphere and concrete objects; Remotion provides exact information.

## 4. Register provenance

Store each used raster in `public/illustrations/` and record it in `manifests/visual-assets.json` with:

- stable ID and relative file path;
- `source_type`: `ai-generated`, `user-supplied` or `licensed-third-party`;
- provider or source URL when applicable;
- prompt summary or original-asset description;
- intended scene and crop policy;
- rights note;
- `baked_text: false` for generated assets.

Do not keep unused generations in the deliverable. Never commit an asset with uncertain redistribution rights.

## 5. Animate image and information separately

Treat the bitmap, each callout, each arrow and each explanation line as independent parts.

- Give the image a restrained reveal, crop wipe or 2–5% push-in.
- Add callouts only after the viewer can recognize the image.
- Time each callout to the matching narration phrase.
- Remove annotations before the image exits when the next scene changes subject.
- Keep text as live Remotion typography; do not rely on text rendered inside the bitmap.
- Prefer one image with two or three sequential annotations over several static image cards.

## 6. Enforce scene lifetime

Use start-inclusive and end-exclusive scene windows. A scene owns all of its image, text, SVG and annotation layers. At the scene end, either unmount the whole group or drive every obsolete part to zero opacity or fully outside the canvas.

Before the next scene enters, inspect these frames:

1. last readable hold;
2. middle of exit;
3. first clean frame;
4. first frame of the next scene.

No outgoing label, hidden corner, arrow head, shadow or generated-image crop may remain beneath the next scene.

## 7. Review for video, not slides

Reject the scene if the image is merely placed on a card while unrelated text appears beside it. The image and overlays must answer the same question in the same few seconds. A useful image scene normally follows this rhythm:

`recognize image → locate object → explain relation → land conclusion → clear scene`

Across the whole film, vary the primary mode according to content so the result can include image-plus-text, pure text and pure graphic scenes without feeling like a moving slide deck.
