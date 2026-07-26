# Lecture composition: the default multi-zone visual route

This is the default visual route for every notebook video. It is pure
code-drawn SVG plus rich synchronized text, so it works in every
environment and never depends on an image-generation model. Follow the
steps mechanically; the template already contains a working example of
every pattern named here.

Image generation is an optional add-on, not part of this route. Before
production, ask the user once whether they want generated support art for
concrete hero scenes, and tell them plainly: the add-on's quality depends
entirely on the image-generation model of the current tool, and Codex
with its built-in image generation is the best-suited environment for it.
Only if they accept, follow [visual-director.md](visual-director.md) for
that subset of scenes. When declined or unavailable, produce everything
below with SVG only.

## The six rules

### 1. Pure code-drawn graphics

Every visual object — mascot, diagram, machine, chart, arrow — is SVG
written by hand inside the Remotion component tree. No bitmap is required.
Benefits you must exploit: strokes can grow (`strokeDasharray` +
`strokeDashoffset`), parts can move independently, and colors always match
the locked palette. Copy `Mascot`, `LineIcon`, `ConceptDiagram`-style
components from the template instead of inventing new drawing styles.

### 2. Multi-zone layout

A scene is not one hero object. Split the 1920×1080 design canvas into
3–5 functional zones, for example:

- left: explanation panel (`Paper` with a Smiley title + body copy);
- right or center: the graphic demonstration area;
- bottom or side: a progressive checklist or comparison cards;
- floating: small annotation stickers that appear on cue.

Keep the locked density budget: **each zone runs one main action at a
time**, unrelated cards stay ≥70px apart, and only one temporary transfer
object crosses the central corridor at once. Multi-zone means parallel
zones, never parallel actions inside one zone.

### 3. Text and graphics are co-stars

Text is not a caption garnish. Pair every graphic demonstration with
readable text that carries the same knowledge: checklists that tick item
by item, good/bad comparison cards, warning strips, step stickers. The
viewer should be able to learn from the text alone or the animation alone.

### 4. Frame-accurate speech sync

Every appearance frame comes from the caption cue table, never from
guessing. Mechanical procedure:

1. Run the TTS adapter, then `build-semantic-captions`, producing
   `manifests/caption-cues.json`.
2. Print the cue frame table:

   ```text
   python -c "import json; d=json.load(open('manifests/caption-cues.json',encoding='utf-8'))['cues']; [print(i+1, round(c['start_ms']*30/1000), round(c['speech_end_ms']*30/1000), c['text'][:16]) for i,c in enumerate(d)]"
   ```

3. Scene boundary = start frame of the first cue of each narration
   paragraph (the chapter-segmented adapter also writes
   `manifests/chapters.json` with exact chapter frames).
4. Element appearance frame = start frame of the line that speaks about it,
   minus the scene start frame (scenes use local frames `l`).
5. A checklist item lights up on the cue that says it; a lamp turns red on
   the cue that says "red"; a version digit brightens on the cue that names
   it. Speak it, then show it — never earlier than the previous cue.

### 5. Demonstrative animation

Animations must carry knowledge, not just decorate entries:

- a persistent task card travels a shared track and changes state at each
  station (process explanations);
- a card is copied/flies from one owner to another (fork, transfer, push);
- one line inside a log panel highlights (locating an error);
- gauges fill, digits light up positionally, growth chains light level by
  level (states and quantities).

Entries/exits still use the restrained `pop`/`ease` helpers; the knowledge
payload lives in what the object does between them.

### 6. Series component reuse

One channel, one visual IP. Reuse the same mascot, paper cards, badges and
list patterns across every episode of a series, and cross-reference
episodes in the closing scene. New graphics become reusable components
written next to the existing ones, in the same stroke and palette style.

## Working the template

`new-project` copies `assets/lecture-template`, a fully validated
900-frame film that demonstrates every rule. The source file is layered:

- **LOCKED layer** — aesthetic core, subtitle, background, chrome, gates:
  never edit.
- **Component library** — `Paper`, `LineIcon`, `CheckBadge`, `Mascot`,
  rails, gauges: reuse directly, extend by imitation.
- **Content layer** — `COPY`, scene boundaries, `Scene*` components,
  `Sound` frame lists: rewrite this layer for a new topic.

To change duration, follow the duration-extension invariant in
[remotion-architecture.md](remotion-architecture.md) and update
`DURATION`, the scene guards and `manifests/asset-manifest.json` together.

## Self-check before rendering

Answer every question with yes; fix the scene otherwise.

1. Does every scene have at least three populated zones (except a
   deliberate title/CTA scene)?
2. Can every animation start frame be traced to a specific cue line?
3. Is the bitmap count zero on this route (`visual-assets.json` assets
   empty), unless the user explicitly accepted the image add-on?
4. Does each zone run only one main action at a time, with ≥70px
   separation between unrelated cards?
5. Does at least one animation per explanatory scene demonstrate the
   mechanism (transfer, highlight, fill, state change) rather than only
   entering?
6. Do checklists tick exactly when their line is spoken?
7. Did the standard QA battery pass (`validate-visual-plan`,
   `validate-layering`, `validate-caption-sync`,
   `validate-semantic-breaks`, `validate-video`)?
