# TTS and declarative audio

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

## Preferred zero-key adapter

When the user has not selected a paid provider, prefer Edge Read Aloud if the environment can reach it and the intended use fits its terms. For Mandarin, start with a warm neural voice such as `zh-CN-XiaoxiaoNeural`, then adjust rate from the real narration duration rather than from character count.

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
