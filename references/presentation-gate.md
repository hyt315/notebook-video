# Presentation gate: what code can prove, and what it cannot

`validate-presentation.py` is a build-time arithmetic and source-inspection aid. It is not a learning-quality score. `validate-composition.py` separately requires exactly one shot to cover each narration cue, a non-placeholder `coreRelation` and `visualCarrier` for every shot, and a recognizable visual JSX node when scene source is available. These checks catch omissions, not semantic truth: current implementation is authoritative; use both validators and keep fixtures in `scripts/negative-gate-check.py` aligned.

## P0: demonstrable integrity failures

The checker blocks stale/missing `shots.resolved.json` records, timing declarations outside a shot or its stated cue, beats that materially precede or trail the spoken idea, invalid cue references, and explicit color pairs below the applicable contrast requirement. P0 means a concrete integrity/accessibility failure that can be checked from project data; it does not mean the scene must be visually active.

A shot may have no `beats`, and a narration cue need not trigger a new visual event. Every cue must still be covered by a shot whose declared visual carrier supports its core relation. A stable, readable diagram may continue to be explained or read. If a beat is declared, its timing must be correct; the checker also warns when a legal beat sits close to the timing tolerance. Missing carrier/relationship declarations or a scene with no visible JSX node are blocking omissions; whether the declared scene actually explains the narration remains a human judgment.

Text/background contrast follows WCAG 2.2 SC 1.4.3 where applicable: 4.5:1 for ordinary text and 3:1 for large text. WCAG 2.2 SC 1.2.2 requires synchronized captions for prerecorded media but does **not** define a universal reading-speed, character-per-second, or minimum-display-time threshold.

## P1: useful prompts, not universal thresholds

The validator reports its configured subtitle reading-speed, line-length, line-count, beat-clustering, small-font, palette-role, and optional author-note observations as P1. These are review prompts, not WCAG compliance verdicts or automatic reasons to add motion, delete content, or reject a coherent composition. Inspect the rendered output in its intended size, language, viewing context, and audience.

The project currently uses a 9 weighted-character-per-second and 16 weighted-character-per-line reference to find cues that may need review. These values are operational defaults, not universal human limits. A 13-design-pixel font is a code search reference, not proof of legibility in final output pixels. Read the reported cue at phone size and, when possible, on the actual target device.

## Optional teaching-design notes

`move`, `evidence`, `hold`, `misconception`, `noMisconception`, and `why` are optional planning prompts, not required per-shot fields. They can help an author state an intent, but cannot prove that the visual teaches it.

- If `move` is supplied, an unknown suggestion produces a P1 note; repeated or omitted moves are allowed.
- If `hold` is supplied, its type is checked; no minimum still duration is enforced.
- If misconception fields conflict, or `noMisconception` lacks its optional reason, the script may prompt review; omission is valid.
- If `evidence` is supplied, the checker only verifies that its name appears as JSX in scene source somewhere. It does not establish that the named element appears in that shot, changes over time, is correct, or explains the narration. A cross-shot match is a known limitation.

## Human review remains necessary

Read and listen through the whole film at full speed. Verify that important changes and highlights refer to the currently spoken idea, leave time to read diagrams/captions, and do not add distracting sound. Still frames can be correct. A useful comparison is between a visual cue synchronized with the spoken reference and the same cue when it is absent, early, or late—but do not make highlighting mandatory on every line.

The checks do not evaluate factual truth, pedagogical transfer, viewer comfort, aesthetic preference, visual hierarchy, whether a diagram is self-explanatory, or whether a hold feels too long. Only viewer evaluation can support those claims.

## Regression proof

Run `python scripts/negative-gate-check.py`. Fixtures should prove that concrete timing, contrast, missing-source, missing-cue-coverage, missing-core-relation, missing-visual-carrier, and empty-scene failures are caught. They should also prove that a genuinely visual static camera, repeated layout, absent beat, unfilled lower frame, and omitted optional teaching note pass without a complexity quota.
