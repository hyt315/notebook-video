# TTS, timing quality and declarative audio

## Provider-neutral contract

Use an available, authorized provider. Record voice, provider, terms and redistribution rights. Do not assume a platform has TTS, install a provider silently, hardcode a proxy or ship credentials.

Canonical files:

- `audio/narration.mp3`: actual narration.
- `audio/narration.mp3.json`: nonempty, ordered `{part,start,end}` items; integer milliseconds, `0 <= start < end`, no overlaps.
- `manifests/semantic-caption-lines.txt`: editor-approved semantic lines reconstructing the spoken text.
- `manifests/protected-caption-phrases.txt`: terms that must not cross a cue boundary.

Prefer measured word boundaries from the provider or an authorized aligner. Preserve them rather than replacing them with character-count estimates. File equality does not prove acoustic alignment.

## Bundled chapter adapter

`assets/lecture-template/scripts/tts-openai-compatible.py` supports a **chat/completions audio response**, not every endpoint marketed as OpenAI-compatible. Set `TTS_API_BASE`, `TTS_API_KEY`, `TTS_MODEL`; optionally `TTS_VOICE` and `TTS_STYLE_PROMPT`. Endpoint and model are required, with no hidden vendor fallback. One style applies to the whole run.

```text
python ./film/scripts/tts-openai-compatible.py ./film
```

The adapter checks narration/semantic-line agreement before synthesis. It normalizes each provider WAV to 48kHz stereo 16-bit PCM **before measuring or joining**, avoiding mixed-format concatenation errors. Inter-paragraph silence is 350ms at synthesis time.

Cache identity includes endpoint, model, voice, style, text and normalized format, excluding credentials. Downloads are decoded and validated before atomic cache publication. Editing one paragraph reuses unchanged requests.

`manifests/tts-segments.json` records the ordered active segment paths, hashes and sample counts. Historical cache files are not the current timeline. `chapters.json` carries measured sample/ms boundaries. Both declare `timing_quality: estimated-character`: the adapter measures chapter durations but spreads characters within them. **This is not word-level acoustic alignment.** Use chapter/phrase emphasis, listen to critical beats, and replace estimates with measured boundaries when available.

`.env`/`tts.env` loading is supported for local configuration, but those files must never be committed or delivered. The packager excludes known secret filenames; inspect unusually named configuration before sharing.

## Pace adjustment

Select tempo from the actual listening result, not a universal characters-per-minute claim. Optional:

```text
python ./film/scripts/speed-post.py ./film 1.10
```

Run immediately after fresh synthesis and before captions/scene authoring. The script validates timing first, stages audio and JSON, scales chapter samples/word times with the same tempo and records hashes in `manifests/speed-post.json`. Re-running on already processed audio is refused. Fresh synthesis permits a new pass. Tempo must be finite and within 0.5–2.0.

Validation or FFmpeg failure leaves canonical outputs unchanged. Publication uses individual atomic replacements, not a multi-file crash-atomic transaction; retain a project backup for important productions. MP3 container duration may include encoder padding; sample-exact claims apply to PCM WAV.

## Re-voice against an approved timeline

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" match-timing ./film --lock
python ./film/scripts/tts-openai-compatible.py ./film
node "<SKILL_DIR>/scripts/notebook-video.mjs" match-timing ./film
node "<SKILL_DIR>/scripts/notebook-video.mjs" build-semantic-captions ./film/audio/narration.mp3.json ./film/manifests/semantic-caption-lines.txt ./film/manifests/caption-cues.json --lead-ms 60
```

`--lock` snapshots chapter timing. Matching selects the current segments from `tts-segments.json`, not every cached voice. Legacy projects require an unambiguous numbered segment set. Keep narration text unchanged. The matcher uses each locked duration and each actual locked gap, including leading/trailing silence; it pads/trims normalized PCM segments to exact target samples. Speech tempo ratios outside 0.5–2.0 are rejected before publication.

Word items map by chapter interval, including multi-character items. Rebuild captions afterward: replacing a voice does not preserve its intra-chapter articulation. `audition` also uses the ordered active segment list so stale voices and chapter-10 lexical sorting do not contaminate previews.

## Pronunciation and missing providers

Listen for Chinese polyphones, English names, numbers and abbreviations. Rewrite ambiguous wording when appropriate and mirror the change in semantic lines. Synonym replacement reduces risk but cannot guarantee pronunciation. Do not claim an unheard voice is correct.

If no provider is available, ask for authorized TTS access or supplied narration. A reachable Edge Read Aloud adapter may be an option when its terms fit the use; it is not installed by the Skill. Synthetic audio is suitable only for clearly labeled render tests, never a substitute for a narrated delivery.

## Mix and effects

Keep narration and visible-action effects in the Remotion tree:

```tsx
<Audio src={staticFile('narration.mp3')} volume={1}/>
<Sequence from={actionFrame} layout="none">
  <Audio src={staticFile('sfx/paper-tap.wav')} volume={0.18}/>
</Sequence>
```

Use the same absolute frame for the visible action and its sound. Use one or two useful cues, not a sound on every movement. Narration stays primary; BGM is optional and subject to the brief. The lecture example contains a quiet music bed; remove it when the brief calls for no music.

FFmpeg normalizes/encodes after rendering, not a separate invented event timeline. Delivery target: about -16 LUFS, true peak ≤-1.5dBTP, 48kHz stereo AAC, H.264 with faststart. Measure the encoded result and listen to the complete mix.
