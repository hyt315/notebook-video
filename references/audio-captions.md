# 旁白、字幕与音效

TTS（可插拔）、字幕断句与定时、语义音效库与闪避。

本篇各节：

- [TTS and declarative audio](#tts-audio)
- [Subtitle timing and absolute-frame contract](#subtitle-timing)
- [SFX library](#sfx-library)
- [音效与旁白的相对电平（P2-20 的剩余部分）](#audio-ducking)

<a id="tts-audio"></a>

## TTS and declarative audio

### Contents

- [Provider-neutral TTS contract](#provider-neutral-tts-contract)
- [Recommended adapter](#recommended-adapter-chapter-segmented-openai-compatible)
- [Standard delivery pace](#standard-delivery-pace)
- [Polyphone handling](#polyphone-handling)
- [Zero-key fallback adapter](#zero-key-fallback-adapter)
- [Remotion audio tree](#remotion-audio-tree)
- [Sound vocabulary](#sound-vocabulary-sfx-library-events)
- [Mix and export](#mix-and-export)
- [Re-voicing without re-timing](#re-voicing-without-re-timing)

### Status

The skill ships `scripts/tts.py`: `notebook-video tts <project>` uses **edge-tts** (detected at run time, not bundled; `pip install edge-tts`) or `--engine=file` for your own recording. edge-tts calls Microsoft's online service: it needs network access and its output is subject to that service's terms — check them before publishing commercially. `--engine=file`: with the optional `faster-whisper` (`pip install faster-whisper`) the recording is transcribed with word timestamps and matched character by character against `narration.txt` (only the times come from recognition; unmatched characters are interpolated). Without it — or with `NV_WHISPER=off`, or when fewer than 60% of spoken characters match — the audio is spread evenly over the characters (punctuation included), captions are only approximately aligned, and `audio/narration.meta.json` says `estimated: true`. Hand-written projects get captions rebuilt automatically after `tts`. The provider-neutral contract below applies to any other provider.

### Provider-neutral TTS contract

The project does not bundle generated narration. Before synthesis, record the provider, voice, generation date, governing terms and whether public/commercial redistribution is allowed.

No TTS package, SDK or key is bundled. Inspect the tools available in the user's environment and write a small adapter for the selected provider.

The adapter must write:

```json
[
  {"part": "第一段语音片段", "start": 120, "end": 680},
  {"part": "下一段", "start": 700, "end": 1050}
]
```

Save the audio as `audio/narration.mp3` and the array as `audio/narration.mp3.json`. Times are integer milliseconds, monotonically increasing, and every item contains non-empty `part`, `start` and `end` fields. The concatenated `part` text must match the narration used for semantic subtitle lines after whitespace normalization.

Possible providers (advisory only): a platform TTS tool, Azure Speech, another commercial API, a local speech model, or Microsoft Edge Read Aloud. Do not install or call a provider without user authorization, and verify that its terms cover the intended distribution.

### Recommended adapter: chapter-segmented, OpenAI-compatible

The lecture template ships `scripts/tts-openai-compatible.py`, a ready adapter for any endpoint that accepts a `chat/completions` payload with an `audio` block and returns base64 audio (MiMo-V2.5-TTS is one example). Configure it only through environment variables — `TTS_API_BASE`, `TTS_API_KEY`, `TTS_MODEL`, optional `TTS_VOICE` and `TTS_STYLE_PROMPT` — and never write keys into project files.

Why it suits long films: it synthesizes each narration paragraph separately, measures its real duration with ffprobe, joins segments with a fixed silence gap and derives per-character word timings inside each measured paragraph, so chapter boundaries come from real audio and captions and scene cuts never drift. Besides the canonical outputs it writes `manifests/chapters.json` (`[{index,start_ms,end_ms,text}]`); chapter frames are `round(ms * fps / 1000)` and become the scene boundaries in `src/index.tsx` and `manifests/asset-manifest.json`.

Segment audio is cached by a hash of model, voice and paragraph text, so editing one paragraph re-synthesizes only that paragraph.

**Narration paragraphs are file lines.** The adapter makes **one chapter per non-empty line** of `narration.txt`; a single long line yields one chapter and per-line alignment becomes impossible. Write one line per semantic sentence (the same split as `manifests/semantic-caption-lines.txt`); both files must still be equal after whitespace normalization, so line breaks are free.

#### Verified endpoint: Xiaomi MiMo open platform (no key in this file)

已验证的接入配方（配音用 `白桦`）：

| 项 | 值 |
|---|---|
| Base URL | `https://api.xiaomimimo.com/v1` |
| 鉴权 | `Authorization: Bearer $TTS_API_KEY`（`sk-` 开头） |
| 模型列表 | `GET /v1/models` → `mimo-v2.5` / `mimo-v2.5-asr` / `mimo-v2.5-pro` / **`mimo-v2.5-tts`** / `mimo-v2.5-tts-voiceclone` / `mimo-v2.5-tts-voicedesign` |
| TTS 模型 | `mimo-v2.5-tts` |
| 音色表 | `mimo_default` · `冰糖` · `茉莉` · `苏打` · **`白桦`（男声）** · `Mia` · `Chloe` · `Milo` · `Dean`。没有 `/v1/voices` 接口——**故意传一个不存在的音色**，400 报错的 `message` 里会列出全部可选音色 |
| 请求 | `POST /v1/chat/completions`，body `{"model":"mimo-v2.5-tts","messages":[{"role":"assistant","content":"<要念的文本>"}],"audio":{"format":"wav","voice":"白桦"}}`。可选的 `{"role":"user","content":"<风格指令>"}` 放在 assistant 之前——会真实改变时长与语气（同句 2.24s → 3.52s） |
| 响应 | `choices[0].message.audio.data` = **base64 的 WAV**（24kHz 单声道 16bit）；`content` 为空串 |
| 计费 | 按调用计费；余额不足时 ASR 等模型会返回 `402 {"type":"insufficient_balance"}`（TTS 仍可用） |

```bash
# key 只走环境变量；不要写进任何工程文件
export TTS_API_BASE='https://api.xiaomimimo.com/v1'
export TTS_API_KEY='sk-<YOUR_KEY>'
export TTS_MODEL='mimo-v2.5-tts'
export TTS_VOICE='白桦'
python ./my-film/scripts/tts-openai-compatible.py ./my-film   # 脚本由 new-project 拷进工程；技能自己的 scripts/ 里没有它
```

**不听也能验音色生效**：同句用两个音色合成，比对 base64 长度/哈希并做自相关基频估计——`白桦` ≈140 Hz、`冰糖` ≈258 Hz，参数被忽略时差异消失。

### Stale narration is a content question, not a clock question

`compose-story` writes `manifests/narration.contract.json`: the SHA-256 of the normalized narration text, a line/text snapshot, and the character count. `tts.py` compares the current `narration.txt` against that hash before synthesising.

Why not mtime: a re-saved old draft looks *newer* and slips past, while `git checkout` or copying trips it for no reason. A mismatch prints the first differing line on both sides and the exact fix commands.

- Writing narration by hand: pass `--allow-stale`; it prints a loud notice and records `allow_stale: true` in `narration.meta.json`.
- Projects without a contract keep the old mtime check as a fallback and say so.
- `narration.meta.json` records `text_sha256`, `timeline` (`measured` / `estimated`), voice, rate and any backup path, so the audio itself is traceable to a text version.
- `--engine=file` without faster-whisper only has **estimated** timings (evenly divided by character count). It refuses to overwrite an existing measured timeline unless you add `--force-estimate`, and any rewrite is backed up to `narration.mp3.json.bak-<timestamp>` and logged.
- When compose rewrites `narration.txt` over existing audio, it warns that subtitles follow the new text but the voice is the previous take.

### Standard delivery pace

Raw synthesis with a patient teaching prompt lands near 305 characters per minute (slow for short-video viewers); prompts cannot set pace precisely ("faster" overshoots past 400), so pace is fixed deterministically after synthesis: run the bundled `<PROJECT_DIR>/scripts/speed-post.py PROJECT_DIR 1.10`, which applies `atempo=1.10` (pitch unchanged), re-normalizes loudness, and divides every timestamp in `narration.mp3.json` and `manifests/chapters.json` by the same factor. The result is 336 characters per minute; captions, scene boundaries and sound tables stay consistent because they all derive from the scaled timing files. Run it once, immediately after synthesis and before building captions; never re-run it on already-scaled output.

#### The narration drives the timeline, not the other way round

A voice change means the narration's own length is the truth. Do **not** hold a pre-existing frame table and squeeze the audio into it: per-chapter `atempo` for that purpose reaches 1.5× and viewers hear the rush. The correct order is:

```text
<adapter>                                  # 自然语速合成（不加 speed-post 也行）
[可选的逐句微补偿：见下]                     # 只抹平句间快慢，不凑时长
resolve-shots.py PROJECT_DIR               # 镜头帧/时长从新的 cue 表重新派生（不改分镜表语义）
validate-video VIDEO <new duration>        # 期望时长用新的总帧数 / fps
```

- **Optional small per-chapter compensation for evenness.** Some engines articulate one sentence at 250 characters/min and the next at 170 (real articulation variance, ~1.49×, not just pauses). Target the **median** line pace and clamp per-chapter `atempo` to a modest band, e.g. `[0.85, 1.15]`; a band as tight as `[0.95, 1.05]` cannot close a 1.5× gap (it only reaches ~1.35×). Write the target per-chapter durations into `manifests/chapters-timing-lock.json` and run `match-timing.py PROJECT_DIR` (stretches each chapter to the locked duration, re-joins with the standard gap, re-normalizes loudness, rescales word timings). Measured: 170–254 → **195–216 characters/min (1.11×)** with multipliers 0.85–1.15.
- **Keep `narration.txt` one line per semantic sentence** so chapters exist at all. In `manifests/semantic-caption-lines.txt` author **semantic units** (a clause, a punctuation-to-punctuation run) and let `build-semantic-captions` own the display break. **Do not hand-wrap to a character budget** — break rule, `--warn-chars` and width: [Subtitle timing](#subtitle-timing). When a cue is too wide, rewrite the sentence, never break inside a word.
- If a project's `src/index.tsx` builds `DURATION` from a generated `SHOT_TOTAL` (the template does), `retime.py` cannot drive it — the duration is already derived, and only `manifests/asset-manifest.json` (`duration_frames` + per-scene frames) still needs the new numbers.

### Polyphone handling

Chinese TTS guesses polyphones (多音字) from context, so 重装 (重 = chóng) is often voiced zhòng. The adapter has no pinyin/SSML channel and `narration.txt` is also the subtitle source, so a wrong reading cannot be patched after synthesis.

Fix it at the source: while writing `narration.txt`, rewrite every easily-misread polyphone into a reading-unambiguous, meaning-equivalent phrase of similar length (chapter frames barely shift), and mirror the edit into `manifests/semantic-caption-lines.txt`. Verified rewrites:

- 重装（电脑/系统）→ 重新装（重 zhòng vs chóng）
- 批量重命名 → 批量重新命名（重）
- 输一行命令 → 输入一条命令（行 háng vs xíng）
- 钉在屏幕上 → 贴在屏幕上（钉 dìng vs dīng）
- 一模一样 → 长得一样（模 mú vs mó）

Also update any on-screen card text that echoes the rewritten phrase so caption, narration and graphics stay consistent. Polyphones a modern model usually reads correctly in context (调色 tiáo, 时长 cháng, 模型 mó) may stay, but spot-check them at QA. When a mispronunciation still slips through, edit `narration.txt` at the source and re-run synthesis → speed-post → captions → render; never attempt a post-hoc audio patch.

### Zero-key fallback adapter

When no OpenAI-compatible endpoint or paid provider is selected, prefer Edge Read Aloud if the environment can reach it and the intended use fits its terms. For Mandarin, start with a warm neural voice such as `zh-CN-XiaoxiaoNeural`, then adjust rate from the real narration duration rather than from character count.

Use a currently available client as an external adapter; do not add it to the skill dependencies. If a proxy is required, pass the live `HTTPS_PROXY` for that invocation only; never copy a transient proxy endpoint into project files. Preserve the service-provided word-boundary JSON and adapt it to the canonical array contract above.

Target a clear, warm Mandarin voice at a moderately brisk rate. Synthesize fresh audio after every narration change.

Check English abbreviations, model names and numbers by listening. Do not infer duration from text length.

### Remotion audio tree

Put narration in the component tree:

```tsx
<Audio src={staticFile('narration.mp3')} volume={1} />
```

Action effects come from the **prebuilt SFX library**, scheduled automatically from the shot table (`src/sfx.ts` → `planSfx`); do not hand-place `<Audio>` tags. Every cue is pinned to a shot start or a beat, so retiming and re-running `resolve-shots` moves the sounds with the picture. Events, rules and per-shot override: [SFX library](#sfx-library).

### Sound vocabulary (SFX library events)

`pop` · `chart` · `highlight` · `success` · `error` · `chapter` · `page` · `place` / `stamp` (hand-made equivalents of pop / success), plus optional `bed.ogg`; meanings in the [events table](#events). Nine events total; anything else is not a valid `sfx` event name.

Do not place effects on invisible actions or every small movement; the planner already drops cues closer than 6 frames.

### Mix and export

- Narration is primary.
- No hidden narration delay.
- The library is normalised to -18 LUFS (100 ms blocks, peak ≤ -1 dBFS); `SFX_GAIN` (0.30–0.55) puts effects 8–12 LU under the -16 LUFS narration target. The optional bed plays around -41 LUFS (BED_GAIN 0.28); set it to 0 if the user does not want music.
- Target about -16 LUFS and at most -1.5dBTP.
- Export 48kHz stereo AAC at about 192kbps.

Use FFmpeg after Remotion for normalization and encoding only. Do not maintain a separate action timeline in a shell script.

### Re-voicing without re-timing

When the narration text is locked but the voice changes (another voice design or model), keep every scene frame valid by aligning the new audio to the approved timeline instead of re-authoring scenes:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" match-timing ./my-film --lock
python <TTS adapter> ./my-film
python ./my-film/scripts/speed-post.py ./my-film 1.10
node "<SKILL_DIR>/scripts/notebook-video.mjs" match-timing ./my-film
node "<SKILL_DIR>/scripts/notebook-video.mjs" build-semantic-captions ./my-film/audio/narration.mp3.json ./my-film/manifests/semantic-caption-lines.txt ./my-film/manifests/caption-cues.json --lead-ms 60 --protected-phrases ./my-film/manifests/protected-caption-phrases.txt
```

`--lock` snapshots the approved `manifests/chapters.json` to `manifests/chapters-timing-lock.json`. The default mode stretches each new chapter to its locked duration (`atempo`, pitch unchanged), re-joins with the standard gap, re-normalizes loudness and scales the word timings onto the locked frame table, so chapter starts, scene guards and sound frames do not move. Ratios outside 0.5–2.0 per chapter are refused. Rebuild captions afterwards because intra-chapter word timing always changes with a new voice.

<a id="subtitle-timing"></a>

## Subtitle timing and absolute-frame contract

### Meaning chooses the boundary; word timing binds it

Never choose a final subtitle boundary from character count. First listen to or read the narration and author one semantic phrase per line. Split only at a punctuation mark, clause boundary or real spoken pause. Then use the TTS JSON `part`, `start` and `end` milliseconds to bind those approved lines back to exact word boundaries.

#### A word boundary is not a legal break

"Ends on a TTS word" proves nothing in Chinese: the adapter reports **one word per character**, so a mechanical wrap like `传到服` / `务器。` binds cleanly and only a phrase list would catch it. **A phrase list is a patch; the rule below is the fix.**

#### The break rule (implemented in `build-semantic-captions.py` and `validate-semantic-breaks.py`)

A cue boundary is legal only if it is one of:

1. a **BudouX phrase boundary** — `budoux.loadDefaultSimplifiedChineseParser()`, the model `package.json` already depends on; or
2. the position **right after a clause mark** (`，。！？；：、…—` and the ASCII equivalents).

And never if it is:

3. inside an **ASCII/digit token** (`push`, `github.com`, `hyt315`, `3090`) — BudouX will happily split Latin runs, so this rule is mandatory;
4. **避头尾** — a cue may not *start* with `，。、；：！？）》」』】”’％‰℃°·` and may not *end* with `“‘（《「『【〔〈`;
5. inside a **protected phrase** from the manifest.

The builder keeps the approved lines as the semantic authority and only **moves a boundary that violates the rule**, to the nearest legal position. It never re-wraps a legal line, so regenerating an approved project is a no-op (both shipped templates regenerate byte-identically). Cue count can only stay equal or shrink: a stray `。` or `，` that a mechanical wrap orphaned onto its own line gets absorbed back into the sentence it closes.

Preferring a clause-mark break on an equidistant tie is load-bearing — without it a boundary sitting just before `，` is pushed backwards into the middle of the preceding word.

#### Self-test it (do this, do not assume)

```text
# 1. Build. The tool prints every boundary it had to move and why, and warns about long cues.
node "<SKILL_DIR>/scripts/notebook-video.mjs" build-semantic-captions audio/narration.mp3.json manifests/semantic-caption-lines.txt manifests/caption-cues.json --lead-ms 60 --protected-phrases manifests/protected-caption-phrases.txt

# 2. Gate it. `phrase rule: enforced` on the last line is the proof the rule ran. The CLI now
#    closes the delivery path: it auto-detects the project's node_modules/budoux and always adds
#    --require-budoux, so a missing BudouX is a hard failure — never a silent SKIPPED pass.
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-semantic-breaks manifests/caption-cues.json manifests/protected-caption-phrases.txt
```

Both tools find BudouX in this order: explicit `--budoux-dir PATH` (any directory with `budoux/module/index.js`), then the project's `node_modules` (walking up from the caption file, at most eight levels; wins so the model tracks `package-lock.json`), then **the slice bundled at `assets/vendor/budoux/`** (BudouX 0.9.2, Apache-2.0, ~80 KB, simplified Chinese only — provenance in `assets/vendor/README.md`), which makes the rule run on a fresh clone.

On the delivery path the CLI injects `--require-budoux` and resolves the same way, so **the rule runs without a prior `npm ci`** and hard-fails only when even the bundled slice is gone (the message names both fixes: `npm ci` in the project, or `--budoux-dir`). Only an explicit `--no-budoux` opts out. Invoking the validator script directly keeps the loud-skip behavior (stderr `WARNING: BudouX ...`, exit 0) for bare fixtures; the validator never writes files — `"break_rule": "mechanical-only (BudouX unavailable)"` is what the **builder** (`build-semantic-captions.py`) stamps into the cue file when built without BudouX.

To watch the rule catch a bad break, feed the fixture (no `--budoux-dir` needed — the bundled slice covers it):

```text
python scripts/validate-semantic-breaks.py bad-cues.json protected.txt
# a cue pair cut as '上网就是连到一台服' / '务器。' reports:
#   SEMANTIC BREAK ERROR: cue 1/2: break at character 9 splits a word or ASCII token: '一台服' | '务器。'
```

`--no-budoux` runs the mechanical half only (rules 3–5), which needs no model and still catches orphaned punctuation and split product names.

#### Width is a separate, softer budget

Character count stays a drafting hint, never a break rule. `--warn-chars N` is off by default and only *warns* above N characters (shipped templates legitimately run to 19, so no threshold is both useful and false-alarm-free); `CaptionFitGate` measures the real pixel width in the render browser and rejects anything over `mode.safe`. When a cue is too wide, **rewrite the narration** or accept more cues; never push the boundary into the middle of a word to hit a number.

### Protected phrases: the curated last mile

Before building cues, create `manifests/protected-caption-phrases.txt`, one phrase per line. It must contain:

- every product, company, person and model name;
- every benchmark or technical proper noun;
- every number together with its unit or comparison target;
- fixed technical phrases such as `上下文窗口` or `完整权重`;
- any short phrase whose meaning becomes incomplete if divided.

Examples of forbidden breaks include `Kimi K` / `3`, `DeepSeek` / `时刻`, `上下` / `文窗口`, `完整权` / `重`, and `Opus` / `四点八`. If a protected phrase is too wide, rewrite the narration; never split the phrase.

This list is the **last mile, not the safety net**: it can never be complete, so it holds names and curated phrases that outrank the model, while the break rule catches the general case. A phrase that no longer appears in the narration is a gate failure, not a harmless leftover: keep the list in step with the script.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" build-semantic-captions audio/narration.mp3.json manifests/semantic-caption-lines.txt manifests/caption-cues.json --lead-ms 60 --protected-phrases manifests/protected-caption-phrases.txt
```

Keep complete clauses, product names and short tails together. Character count is only a drafting hint; pixel width is authoritative.


### Convert once to frames

At the data boundary:

```ts
const msFrame = (ms: number) => Math.round(ms * FPS / 1000);
```

Create `startFrame` and `endFrame` for cues and words once. Subtitle, animation and audio cues must use the same `FPS` and frame convention. Do not compare seconds or milliseconds inside scene components.

### Reveal behavior

- Reveal at measured word starts with about 60ms of visual lead, equal to two frames at 30fps.
- Keep the completed cue until the next cue.
- Reserve the complete phrase width from the first word.
- Keep the pinned pure caption text fixed (no bar, no locator, no ring).
- Preserve internal punctuation.
- Hide only trailing punctuation visually.
- Keep one line within 1334px.

### Validation

Run the browser fit gate plus both file validators after any narration edit:

```text
# CaptionFitGate runs automatically during Remotion render. It measures the bundled font,
# converts delivery-scaled width back to design pixels, and rejects widths over 1334px.
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-caption-sync audio/narration.mp3.json manifests/caption-cues.json
# Delivery path: the CLI auto-adds --require-budoux and resolves the model from the project's
# node_modules or, failing that, the slice bundled at assets/vendor/budoux/; only a missing
# bundle fails the gate instead of skipping quietly.
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-semantic-breaks manifests/caption-cues.json manifests/protected-caption-phrases.txt
```

Reject word-stream mismatch, non-semantic segmentation, a break that is not a BudouX phrase boundary or a clause break, a cue starting with a closing mark, an ASCII model/product token split, a protected phrase crossing a cue boundary, overflow, horizontal jitter, two-line text, trailing visual punctuation, dark subtitle side marks or a changed contour.

Read the validator's last line: `phrase rule: enforced (BudouX from …)` proves the word-cut rule ran, and on the delivery path (CLI) it is mandatory. `SKIPPED — BudouX not found` is reachable only via a deliberate `--no-budoux` or a direct script call with `assets/vendor/` missing; then only the mechanical checks and the phrase list were applied.

### Line length: at most 16 characters

Every subtitle line is at most **16 characters** after stripping trailing punctuation and whitespace
(ASCII counts one each, so GitHub costs 6). Long lines make the eye read a sentence instead of glancing at a phrase — a main "slide deck" tell.

- `build-semantic-captions.py --max-chars 16` (default) splits any approved line that is longer at the legal
  break nearest its middle (a break right after a clause mark wins if it costs ≤ 2 characters of balance).
  It never cuts inside a word, an ASCII token or a protected phrase; when a long line has no legal break it
  fails and asks you to shorten the narration.
- `validate-caption-sync.py --max-chars 16` (default) fails any cue that is still longer.
- The render-time `CaptionFitGate` blocks the render for the same reason (`CAPTION_MAX_CHARS` in `src/index.tsx`).
- `--max-chars 0` turns the rule off for a legacy project; do not ship that way.

<a id="sfx-library"></a>

## SFX library

The template ships a finished sound-effect library, so nothing is generated, downloaded or tuned at run time (Windows included). Files live in `assets/lecture-template/public/sfx/lib/`, described by
`public/sfx/sfx-manifest.json` (sha256, duration, loudness, peak, source recipe, license, intended use).

### Events

Nine events plus an optional bed. Removed events (`whoosh`, `click`, `rustle`, `typing`, `riser`, `snip`, `latch`; reasons in `src/sfx.ts`) fail in `resolve-shots.py` with an explicit message instead of going silent.

| event | file | when the engine uses it |
|---|---|---|
| `pop` | `sfx/lib/pop.ogg` | first beat of a shot (first element appears) |
| `chart` | `sfx/lib/chart.ogg` | middle beats when `media` has `chart` or `metric` |
| `highlight` | `sfx/lib/highlight.ogg` | last beat of a non-conclusive shot; every other middle beat |
| `success` | `sfx/lib/success.ogg` | last beat when `live` has Checklist / StampSeal / VerdictBar / StampBanner / MetricGrid / CheckBadge, or `move` is 收束/结论 |
| `error` | `sfx/lib/error.ogg` | beat 1 of a shot with a `misconception` and ≥ 3 beats |
| `chapter` | `sfx/lib/chapter.ogg` | 2 frames into each chapter's first shot |
| `page` | `sfx/lib/page.ogg` | 3 frames into any pageturn shot (auto / pageturn / peel / pageflip) — an action sound, never thinned |
| `place` | `sfx/lib/place.ogg` | hand-made skins: replaces `pop` |
| `stamp` | `sfx/lib/stamp.ogg` | hand-made skins: replaces `success` |
| (bed) | `sfx/lib/bed.ogg` | optional quiet music bed, looped under the whole film |

Priority when two cues fall within 6 frames: chapter > success > stamp > error > page > chart > highlight > pop > place.

### Override per shot (manifests/shots.json)

```json
"sfx": "none"                                     // no sound for this shot
"sfx": [{"event": "success", "beat": 2}]           // replace the automatic cue on beat 2
"sfx": [{"event": "error", "at": 40, "vol": 0.3}]  // add a cue at local frame 40
"sfxAuto": false                                   // only the explicit cues above
```

`resolve-shots.py` validates the field and passes it into `src/shots.ts`; the engine reads it in `planSfx`.

### Medium mapping

Only the hand-made media (`journal` / `papercut` / `archive`) remap **automatic** punctuation sounds:

| automatic UI sound | hand-made sound |
|---|---|
| `pop` | `place` |
| `success` | `stamp` |

`page` is not in this table on purpose: a pageturn gets paper sound on **every** skin, because it is an action,
not punctuation.

`flat` and `cel` declare `craft` (ink colour, fonts, default transition), but that is a **capability configuration**, not a hand-made medium; they keep the UI sounds. The single authority is
`src/theme/medium.ts` → `isHandmadeMedium()`; `auto.tsx` and `sfx.ts` must both use it, and a story's explicit
`sfx` entries are never rewritten by this mapping.

### Levels

All one-shots: -18 LUFS (K-weighted, 100 ms blocks), sample peak ≤ -1 dBFS, mono 48 kHz Ogg Vorbis (4–15 KB each).
Mix gains in `SFX_GAIN` (0.34–0.55) keep them 8–12 LU under narration at -16 LUFS. `validate-audio-levels.py`
checks hashes against the manifest, peaks, the loudness tolerance, the event/file mapping in `src/sfx.ts` and the
gain range.

### Provenance and rebuild (maintainers only)

Rendered in code with **earshot** 0.2.0 (`earshot forge` recipes; https://github.com/Leonxlnx/earshot, MIT) — no
recorded samples — and quality-checked with `earshot rank` / `earshot match` (CLAP). License: CC0-1.0.
Users never install earshot. To rebuild: `python scripts/dev/build-sfx-library.py` (needs torch CPU + earshot).

### Highlight source

`highlight` (the most repeated cue) is `earshot sfx render pro_notify/ding_2296`: a clean short bell, 0.26 s, spectral centroid 3.1 kHz, 6 ms attack; passes `earshot sfx check` (no clicks, cut tail, clipping or DC), normalised to −18 LUFS / 100 ms, transient at 8.5 ms (`offsetMs`). Chosen on measured duration / centroid / attack (one-off script `_acceptance-3.8.0/build-highlight.py`, not shipped).

### Layered pop and chart

`pop` and `chart` are **layered** designs in `scripts/dev/build-sfx-library.py` (its LAYERS table):

| Event | Layers (earshot forge recipe #seed, gain) | Match z |
|---|---|---|
| `pop` | round low body `popin #14` (−3 dB) + bright bubble tick `pop #7` (0 dB) + trimmed sub hit `impact #6` (120 ms, −18 dB) | 3.01 strong |
| `chart` | upward tonal zip `zip #5` (0 dB) + `zip #0` 10 ms later (−2 dB) + landing thump `popin #10` at 200 ms (−8 dB) | 3.15 strong |

Rebuild only these two: `python scripts/dev/build-sfx-library.py --only pop,chart` (the other entries and
files are kept byte-for-byte).

### 调音：每个 cue 的 `gain` 与 `offsetMs`

- 每条 manifest 记录新增 `gain`（线性，把 cue 放到响度阶梯上：chapter −24 · success −25 · pop −25.5 · error / chart −26 · highlight / page −27 · place −26.5 · stamp −25 LUFS，全部比音乐床高 11–17 LU）与 `offsetMs`（文件开头到瞬态的距离）。
- 引擎（`src/sfx.ts`）按 `offsetMs` **提前**起播，瞬态落在视觉命中帧（±1 帧）；`page` 的命中点是转场第 3 帧（纸刚被掀起）。
- 去拥挤：两个 cue 间隔 ≥150 ms（5 帧，优先级高的留下）；任意 10 秒最多 4 个（≈24 次/分钟）。音乐床在每个 cue 命中前 2 帧到后 14 帧闪避到 45%。
- auto 片（story.json）只在真事件上出声：数字落定 `pop`、图表生长 `chart`、关键词第一次推近 `highlight`、答案揭晓 / 改之后出现 `success` / `pop`；章节 `chapter`、每次翻页 `page`。
- `validate-audio-levels.py` 每次出片打印「压人声 N 个（事件名）」：显式音效落在某句旁白 `[start_ms, speech_end_ms]` 内的条数（自动的 `chapter` / `page` 落在换镜帧、旁白未开口，不重叠）。**只报告不拦截**——少量压人是正常动作拟音，全片都压才是问题。
- 维护者：`python scripts/dev/audit-sfx.py [--legacy]` 打分（时序 40 + 电平 30 + 音色 30），`python scripts/dev/tune-sfx.py` 修剪 + 写回 manifest（需 numpy / soundfile / pyloudnorm；普通用户不用跑）。`validate-audio-levels.py` 核对 `SFX_GAIN` / `SFX_OFFSET_MS` 与 manifest 一致。

### 离线质检（维护者可选）

earshot 是**维护者离线质检**，不是运行时依赖——包里只带成品音频、配方与许可；普通用户渲染不得被要求下载 1.1GB 模型或装 PyTorch。

`python scripts/dev/sfx-earshot-audit.py`（缺 earshot 时打印安装提示并 exit 0，不挡出片）：

1. `earshot measure`（无模型、不联网）复核每个 OGG 的 LUFS / 真峰值 / 包络，与 `scripts/dev/audit-sfx.py`（numpy + pyloudnorm）并排；**LUFS ±0.5 LU / 真峰值 ±0.3 dBFS 以内属正常**，超了脚本点名，须能解释差异来源。
2. `--mix <成片>` 时用 `earshot timeline` 看真实事件密度与命中点（配合 `--cues`）。**先分析、不改声音**，改不改由人工盲听决定。

明确不做的三件事：

- 不用 `realness` / CLAP 分数单独决定入库——只作参考，必须保留人工盲听与无模型检查；
- 不因工具升级重生成整库（确有音色缺口才用 `sfx` / `forge` 出候选，衍生配方必须保留源录音许可）；
- `critique` 不拿宣传片风格当目标——要先有「中文教学旁白 + 克制拟音」的自有 profile。

**验收口径**：新旧工具测量差异可解释；质检报告可复现（`--json`）；候选经同条件盲听优于旧版才替换；无 earshot 的环境仍可出片。

### 三段盲听协议（P2-20 · 维护者）

电平合格 ≠ 听感合格。电平抓不到：**旁白下拟音是否掩字**、**连续翻页是否机械**、**静音占位与真人声的动态差异**。只能用固定段落反复听，不能每次现挑。

```
python scripts/dev/listen-segments.py mix.wav out_dir
```

产出 `seg1-open.wav` / `seg2-turns.wav` / `seg3-close.wav` + `segments.json`（切点与打分表）：

| 段 | 取自 | 听什么 | 及格线 |
|---|---|---|---|
| 开场 | 0–20 s | 人声刚进来时拟音在不在、压不压字 | 可懂度 ≥4，关键辅音不被掩 |
| 连续转场 | 最密集的 ≥3 次翻页区 | 机械感、纸声是否同质 | 机械感 ≥3（轮换后应 ≥4） |
| 结论 | 末 20 s | 收束音效、配乐尾、最后一个字 | 可懂度 ≥4，疲劳 ≥3 |

打分 1–5 写进 `segments.json` 的 `verdict`，归档到工程。**先盲听、不改声音**——改不改由人耳决定。

#### 音色轮换

连续翻页同一纸声 3 次后就机械。`page` 有三个同源微变体
（`page.ogg` / `page-b.ogg` / `page-c.ogg`，音高与滤波略不同、瞬态位置差 <0.5 ms、
响度差 <0.5 LU），`planSfx` 按出现次序轮换。变体元数据在 `sfx-manifest.json` 的
`variants[]`，与主文件同一套质量口径（sha256 / 峰值下限 / 响度容差 / 瞬态同步）。

#### 动作音同步（验收：≤2 帧）

`offsetMs` = 文件开头到听感命中点的距离，引擎提前这么多起播，命中点就落在视觉帧上。
**命中点的量法是 5 ms RMS 最大值**（与 `scripts/dev/tune-sfx.py` 一致），不能用「最大绝对值采样」——chart、chapter 峰值在尾巴上，会误报 140 ms。`validate-audio-levels.py` 逐文件对账，差 >2 帧（66.7 ms）即 P0。

#### 随旁白 ducking：先盲听再决定

人声 −16 LUFS、拟音 −24…−27 LUFS、音乐床 ≈ −41 LUFS（且在每个 cue 下闪避到 45%）。
按阶梯，拟音已在人声下方 8–14 LU。**是否仍掩字由 seg1 盲听判定**：
若掩，优先下调该事件的 `gain` 阶梯（改 manifest + sfx.ts 两处同值），
而不是继续加音效数量；确有必要再做包络跟随的 ducking（需要旁白包络，属后续项）。

<a id="audio-ducking"></a>

## 音效与旁白的相对电平（P2-20 的剩余部分）

### 为什么这一条还没"做完"

P2-20 可机器保证的部分（变体轮换、同步门禁、盲听协议）已做完；**随旁白的包络 ducking** 刻意排在盲听之后——先听 seg1 确认音效真的掩字，再决定 ducking 还是调 gain 阶梯。没听就上 ducking，很可能压掉该有的强调音。

### 判定：先量，再听

```bash
# 1) 音效命中点与旁白区间是否真的重叠（机器可判，不需要耳朵）
python scripts/validate-audio-levels.py assets/lecture-template
python scripts/validate-audio-levels.py PROJECT --explain   # 每条事件的 offsetMs 与所在旁白句

# 2) 重叠段的相对电平（旁白 RMS vs 音效 RMS，同一 200 ms 窗口）
ffmpeg -ss <t> -t 0.2 -i audio/narration.mp3 -af "astats=metadata=1:reset=1" -f null - 2>&1 | grep "RMS level"
ffmpeg -ss <t> -t 0.2 -i renders/film.mp4 -af "astats=metadata=1:reset=1" -f null - 2>&1 | grep "RMS level"
```

判据（来自 `references/audio-captions.md#sfx-library` 的既有口径）：

| 情况 | 处置 |
|---|---|
| 音效峰值 ≤ 旁白 RMS −12 dB | 不用 ducking，现状即可 |
| 落在 −12…−6 dB 之间，且音效 < 300 ms | 先调该事件的 gain（在 `sfx-manifest.json` 里降 3 dB），不要全局 duck |
| > −6 dB，或音效 > 300 ms 且压住整句 | 上 ducking（下面的命令） |

### ducking 参数（听完再改，别凭感觉调）

- 深度 **−6 dB**（0.5 线性）。再深会让音效"消失"，观众以为漏了一声。
- 淡入/淡出 **各 120 ms**，余弦。硬切在纸片音上会有可闻的咔哒。
- 只在**旁白句内**压；句间空隙恢复原电平（空隙本来就是音效的位置）。
- 不压 `narration` 自身，只压 sfx 总线。

### 现成命令（把 CUE_JSON 换成工程的 caption-cues.json）

```bash
# 1) 从 cues 生成「旁白区间」的 ffmpeg 表达式（半开区间，含 120 ms 斜坡）
python - <<'PY' > /tmp/duck-expr.txt
import json, sys
cues = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "manifests/caption-cues.json", encoding="utf-8"))["cues"]
f = 0.12
terms = []
for c in cues:
    a, b = c["start_ms"] / 1000, c["speech_end_ms"] / 1000
    terms.append(f"if(between(t,{a:.3f},{a + f:.3f}),1-0.5*(t-{a:.3f})/{f},"
                 f"if(between(t,{b - f:.3f},{b:.3f}),1-0.5*({b:.3f}-t)/{f},"
                 f"if(between(t,{a:.3f},{b:.3f}),0.5,1)))")
print(terms[0] if terms else "1")
PY

# 2) 把表达式套到音效总线上（音效单独一轨时才成立；混在成片里就只能整轨压，会连旁白一起压）
ffmpeg -i sfx.wav -af "volume='$(cat /tmp/duck-expr.txt)':eval=frame" sfx-ducked.wav
```

**注意**：当前音效由 Remotion 渲染时与旁白一起混，**没有独立的 sfx 轨**，上面这段在现有产物上跑不了。前置工作是让渲染另出一条 sfx-only 音轨（`<Audio>` 分组 → 单独 composition 或 `--separate-audio-to`）——不是改参数的问题。

### 还差什么（诚实清单）

- [ ] 盲听 seg1，按上表落一个判定（需要人，约 15 分钟）
- [ ] 若判定要 ducking：先加 sfx-only 音轨输出，再套上面的表达式
- [ ] 静音占位 vs 真人声的动态差：现在两者用同一套电平门限，真人声的句间呼吸会被当成"静音"，
      需要按 `narration.meta.json` 是否来自 TTS 分流
- [ ] 泵感检测（duck 过度会让音效忽大忽小）：目前没有指标，只能听
