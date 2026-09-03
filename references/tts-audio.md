# TTS and declarative audio

## Contents

- [Provider-neutral TTS contract](#provider-neutral-tts-contract)
- [Recommended adapter](#recommended-adapter-chapter-segmented-openai-compatible)
- [Standard delivery pace](#standard-delivery-pace)
- [Polyphone handling](#polyphone-handling)
- [Zero-key fallback adapter](#zero-key-fallback-adapter)
- [Remotion audio tree](#remotion-audio-tree)
- [Sound vocabulary](#sound-vocabulary)
- [Mix and export](#mix-and-export)
- [Re-voicing without re-timing](#re-voicing-without-re-timing)

## Provider-neutral TTS contract

The project does not bundle generated narration. Before synthesis, record the provider, voice, generation date, governing terms and whether public/commercial redistribution is allowed.

No TTS package, SDK, key or provider-specific command is bundled. An AI implementing this skill should inspect the tools available in the user's environment and write a small adapter for the selected provider.

The adapter must write:

```json
[
  {"part": "第一段语音片段", "start": 120, "end": 680},
  {"part": "下一段", "start": 700, "end": 1050}
]
```

Save the audio as `audio/narration.mp3` and the array as `audio/narration.mp3.json`. Times are integer milliseconds, monotonically increasing, and every item contains non-empty `part`, `start` and `end` fields. The concatenated `part` text must match the narration used for semantic subtitle lines after whitespace normalization.

Possible providers include a platform TTS tool, Azure Speech, another commercial API, a local speech model, or Microsoft Edge Read Aloud. This list is advisory only. Do not install or call a provider without user authorization, and verify that its terms cover the intended distribution.

## Recommended adapter: chapter-segmented, OpenAI-compatible

The lecture template ships `scripts/tts-openai-compatible.py`, a ready adapter for any endpoint that accepts a `chat/completions` payload with an `audio` block and returns base64 audio (MiMo-V2.5-TTS is one example). Configure it only through environment variables — `TTS_API_BASE`, `TTS_API_KEY`, `TTS_MODEL`, optional `TTS_VOICE` and `TTS_STYLE_PROMPT` — and never write keys into project files.

Why it is the recommended shape for long films: it synthesizes each narration paragraph separately, measures every segment's real duration with ffprobe, joins segments with a fixed silence gap, and derives per-character word timings inside each measured paragraph. Chapter boundaries therefore come from real audio, so captions and scene cuts never drift. Besides the canonical outputs it writes `manifests/chapters.json` (`[{index,start_ms,end_ms,text}]`); chapter frames are `round(ms * fps / 1000)` and become the scene boundaries in `src/index.tsx` and `manifests/asset-manifest.json`.

Segment audio is cached by a hash of model, voice and paragraph text, so editing one paragraph re-synthesizes only that paragraph.

## Standard delivery pace

Raw synthesis with a patient teaching prompt lands near 305 characters per minute, which viewers on short-video platforms read as slow. Prompt wording cannot control pace precisely (any "faster" instruction overshoots past 400), so pace is fixed deterministically after synthesis: run the bundled `scripts/speed-post.py PROJECT_DIR 1.10`, which applies `atempo=1.10` (pitch unchanged), re-normalizes loudness, and divides every timestamp in `narration.mp3.json` and `manifests/chapters.json` by the same factor. The result is 336 characters per minute, verified across full productions. Every downstream consumer (captions, scene boundaries, sound tables) stays self-consistent because they all derive from the scaled timing files. Run it once, immediately after synthesis and before building captions; never re-run it on already-scaled output.

## Polyphone handling

Chinese TTS is unreliable on polyphones (多音字): one character has several readings and the model guesses from context, so 重装 ("reinstall", 重 = chóng) is often voiced as zhòng. The adapter feeds plain narration text with no pinyin/SSML channel, and `narration.txt` is also the subtitle source, so a wrong reading cannot be patched after synthesis.

Fix it at the source. While writing `narration.txt`, rewrite every easily-misread polyphone into a reading-unambiguous, meaning-equivalent phrase, and mirror the same edit into `manifests/semantic-caption-lines.txt`. This removes the ambiguity entirely (100% reliable) instead of hoping the model reads context correctly, and keeping the replacement close in character count means chapter frames barely shift. Production-verified rewrites:

- 重装（电脑/系统）→ 重新装（重 zhòng vs chóng）
- 批量重命名 → 批量重新命名（重）
- 输一行命令 → 输入一条命令（行 háng vs xíng）
- 钉在屏幕上 → 贴在屏幕上（钉 dìng vs dīng）
- 一模一样 → 长得一样（模 mú vs mó）

Also update any on-screen card text that echoes the rewritten phrase so caption, narration and graphics stay consistent. Polyphones a modern model usually reads correctly in context (调色 tiáo, 时长 cháng, 模型 mó) may stay, but spot-check them at QA. When a mispronunciation still slips through, edit `narration.txt` at the source and re-run synthesis → speed-post → captions → render; never attempt a post-hoc audio patch.

## Zero-key fallback adapter

When no OpenAI-compatible endpoint or paid provider is selected, prefer Edge Read Aloud if the environment can reach it and the intended use fits its terms. For Mandarin, start with a warm neural voice such as `zh-CN-XiaoxiaoNeural`, then adjust rate from the real narration duration rather than from character count.

Use a currently available client as an external adapter; do not add it to the skill dependencies. If the environment requires an HTTP proxy, pass the live `HTTPS_PROXY` value to the client for that invocation. Never copy a transient proxy endpoint into project files. Preserve the service-provided word-boundary JSON and adapt it to the canonical array contract below.

Target a clear, warm Mandarin voice at a moderately brisk rate. Synthesize fresh audio after every narration change and keep the generated word-boundary JSON.

Check English abbreviations, model names and numbers by listening. Do not infer duration from text length.

## Remotion audio tree

Put narration in the component tree:

```tsx
<Audio src={staticFile('narration.mp3')} volume={1} />
```

Put action effects at their visible action frames:

```tsx
<Sequence from={actionFrame} layout="none">
  <Audio src={staticFile('sfx/paper-tap.wav')} volume={0.18} />
</Sequence>
```

Use the same absolute frame value for the action and its sound. Preview the real mix before export.

## Sound vocabulary

- paper slide/lift: filtered pink-noise rustle;
- data transfer: short high-passed whoosh;
- landing or click: 30–100ms tap;
- pass/completion: 150–400ms soft chime.

Do not place effects on invisible actions or every small movement.

## Mix and export

- Narration is primary.
- No hidden narration delay.
- Optional BGM remains roughly -25 to -30dB under speech and requires user approval.
- Target about -16 LUFS and at most -1.5dBTP.
- Export 48kHz stereo AAC at about 192kbps.

Use FFmpeg after Remotion for normalization and encoding only. Do not maintain a separate action timeline in a shell script.

## Re-voicing without re-timing

When the narration text is locked but the voice changes (another voice design or model), keep every scene frame valid by aligning the new audio to the approved timeline instead of re-authoring scenes:

```text
python scripts/match-timing.py ./my-film --lock
python <TTS adapter> ./my-film
python scripts/speed-post.py ./my-film 1.10
python scripts/match-timing.py ./my-film
node "<SKILL_DIR>/scripts/notebook-video.mjs" build-semantic-captions ./my-film/audio/narration.mp3.json ./my-film/manifests/semantic-caption-lines.txt ./my-film/manifests/caption-cues.json --lead-ms 60
```

`--lock` snapshots the approved `manifests/chapters.json` to `manifests/chapters-timing-lock.json`. The default mode stretches each new chapter to its locked duration (`atempo`, pitch unchanged), re-joins with the standard gap, re-normalizes loudness and scales the word timings onto the locked frame table, so chapter starts, scene guards and sound frames do not move. Ratios outside 0.5–2.0 per chapter are refused. Rebuild captions afterwards because intra-chapter word timing always changes with a new voice.
