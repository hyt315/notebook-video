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

The skill ships `scripts/tts.py`: `notebook-video tts <project>` uses **edge-tts** (detected at run time, not bundled; install with `pip install edge-tts`) or `--engine=file` for your own recording. edge-tts calls Microsoft's online speech service, so it needs network access and its output is subject to that service's terms — check them yourself before publishing commercially. `--engine=file` has no word timing: it spreads the audio evenly over the characters (punctuation included), so captions are only approximately aligned. Hand-written projects get their captions rebuilt automatically after `tts` . The provider-neutral contract below still applies if you use another provider.

### Provider-neutral TTS contract

The project does not bundle generated narration. Before synthesis, record the provider, voice, generation date, governing terms and whether public/commercial redistribution is allowed.

No TTS package, SDK or key is bundled; `scripts/tts.py` only detects edge-tts at run time. An AI implementing this skill should inspect the tools available in the user's environment and write a small adapter for the selected provider.

The adapter must write:

```json
[
  {"part": "第一段语音片段", "start": 120, "end": 680},
  {"part": "下一段", "start": 700, "end": 1050}
]
```

Save the audio as `audio/narration.mp3` and the array as `audio/narration.mp3.json`. Times are integer milliseconds, monotonically increasing, and every item contains non-empty `part`, `start` and `end` fields. The concatenated `part` text must match the narration used for semantic subtitle lines after whitespace normalization.

Possible providers include a platform TTS tool, Azure Speech, another commercial API, a local speech model, or Microsoft Edge Read Aloud. This list is advisory only. Do not install or call a provider without user authorization, and verify that its terms cover the intended distribution.

### Recommended adapter: chapter-segmented, OpenAI-compatible

The lecture template ships `scripts/tts-openai-compatible.py`, a ready adapter for any endpoint that accepts a `chat/completions` payload with an `audio` block and returns base64 audio (MiMo-V2.5-TTS is one example). Configure it only through environment variables — `TTS_API_BASE`, `TTS_API_KEY`, `TTS_MODEL`, optional `TTS_VOICE` and `TTS_STYLE_PROMPT` — and never write keys into project files.

Why it is the recommended shape for long films: it synthesizes each narration paragraph separately, measures every segment's real duration with ffprobe, joins segments with a fixed silence gap, and derives per-character word timings inside each measured paragraph. Chapter boundaries therefore come from real audio, so captions and scene cuts never drift. Besides the canonical outputs it writes `manifests/chapters.json` (`[{index,start_ms,end_ms,text}]`); chapter frames are `round(ms * fps / 1000)` and become the scene boundaries in `src/index.tsx` and `manifests/asset-manifest.json`.

Segment audio is cached by a hash of model, voice and paragraph text, so editing one paragraph re-synthesizes only that paragraph.

**Narration paragraphs are file lines.** The adapter makes **one chapter per non-empty line** of `narration.txt`, so a narration written as a single long line yields a single chapter — the whole film then stretches or squeezes as one block and per-line alignment is impossible. Write one line per semantic sentence (the same split as `manifests/semantic-caption-lines.txt`); both files must still be equal after whitespace normalization, so line breaks are free.

#### Verified endpoint: Xiaomi MiMo open platform (no key in this file)

查通的接入配方（2026-09-21 实跑验证，配音用 `白桦`）：

| 项 | 值 |
|---|---|
| Base URL | `https://api.xiaomimimo.com/v1` |
| 鉴权 | `Authorization: Bearer $TTS_API_KEY`（`sk-` 开头） |
| 模型列表 | `GET /v1/models` → `mimo-v2.5` / `mimo-v2.5-asr` / `mimo-v2.5-pro` / **`mimo-v2.5-tts`** / `mimo-v2.5-tts-voiceclone` / `mimo-v2.5-tts-voicedesign` |
| TTS 模型 | `mimo-v2.5-tts` |
| 音色表 | `mimo_default` · `冰糖` · `茉莉` · `苏打` · **`白桦`（男声）** · `Mia` · `Chloe` · `Milo` · `Dean`。没有 `/v1/voices` 接口——**故意传一个不存在的音色**，400 报错的 `message` 里会列出全部可选音色 |
| 请求 | `POST /v1/chat/completions`，body `{"model":"mimo-v2.5-tts","messages":[{"role":"assistant","content":"<要念的文本>"}],"audio":{"format":"wav","voice":"白桦"}}`。可选的 `{"role":"user","content":"<风格指令>"}` 放在 assistant 之前——实测它会改变输出的时长与语气（同一句话 2.24s → 3.52s），不是被忽略的装饰 |
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

**音色是否真的生效，可以不听声音就验**：同一句话分别用两个音色合成，比对返回的
base64 长度/哈希，再对 WAV 做一次自相关基频估计——男声 `白桦`（整段中位 ≈140 Hz）与女声
`冰糖`（≈258 Hz）差得足够远，参数被忽略时这个差异会立刻消失。

### Stale narration is a content question, not a clock question

`compose-story` writes `manifests/narration.contract.json`: the SHA-256 of the normalized narration text, a line/text snapshot, and the character count. `tts.py` compares the current `narration.txt` against that hash before synthesising.

Why not mtime: re-saving an old draft makes it *newer* than `narration.txt` and slips past a timestamp check, while `git checkout` or copying a project refreshes mtimes and trips it for no reason. A mismatch now prints the first differing line on both sides and the exact commands to fix it.

- Writing narration by hand: pass `--allow-stale`; it prints a loud notice and records `allow_stale: true` in `narration.meta.json`.
- Projects without a contract keep the old mtime check as a fallback and say so.
- `narration.meta.json` records `text_sha256`, `timeline` (`measured` / `estimated`), voice, rate and any backup path, so the audio itself is traceable to a text version.
- `--engine=file` only has **estimated** timings (evenly divided by character count). It refuses to overwrite an existing measured timeline unless you add `--force-estimate`, and any rewrite is backed up to `narration.mp3.json.bak-<timestamp>` and logged.
- When compose rewrites `narration.txt` while an older audio exists, it prints a hint: the subtitles follow the new text but the voice is still the previous take.

### Standard delivery pace

Raw synthesis with a patient teaching prompt lands near 305 characters per minute, which viewers on short-video platforms read as slow. Prompt wording cannot control pace precisely (any "faster" instruction overshoots past 400), so pace is fixed deterministically after synthesis: run the bundled `<PROJECT_DIR>/scripts/speed-post.py PROJECT_DIR 1.10`, which applies `atempo=1.10` (pitch unchanged), re-normalizes loudness, and divides every timestamp in `narration.mp3.json` and `manifests/chapters.json` by the same factor. The result is 336 characters per minute, verified across full productions. Every downstream consumer (captions, scene boundaries, sound tables) stays self-consistent because they all derive from the scaled timing files. Run it once, immediately after synthesis and before building captions; never re-run it on already-scaled output.

#### The narration drives the timeline, not the other way round

A voice change means the narration's own length is the truth. Do **not** hold a pre-existing frame table and squeeze the audio into it: per-chapter `atempo` for that purpose reaches 1.5× and viewers hear the rush. The correct order is:

```text
<adapter>                                  # 自然语速合成（不加 speed-post 也行）
[可选的逐句微补偿：见下]                     # 只抹平句间快慢，不凑时长
resolve-shots.py PROJECT_DIR               # 镜头帧/时长从新的 cue 表重新派生（不改分镜表语义）
validate-video VIDEO <new duration>        # 期望时长用新的总帧数 / fps
```

- **Optional small per-chapter compensation for evenness.** Some engines articulate one sentence at 250 characters/min and the next at 170 (measured on a real run: per-line c/min spread 1.49×, and the *voiced* rate showed the same 1.49× — so it is real articulation variance, not just pauses). Fix it by targeting the **median** line pace and clamping the per-chapter `atempo` to a modest band, e.g. `[0.85, 1.15]`; a band as tight as `[0.95, 1.05]` cannot close a 1.5× gap (it only reaches ~1.35×). Implement it by writing the target per-chapter durations into `manifests/chapters-timing-lock.json` and running `match-timing.py PROJECT_DIR` — the tool already stretches each chapter to a locked duration, re-joins with the standard gap, re-normalizes loudness and rescales the word timings. A real run went 170–254 → **195–216 characters/min (1.11×)** with multipliers 0.85–1.15 (none of them a rush).
- **Keep `narration.txt` one line per semantic sentence** so chapters exist at all (see above). For `manifests/semantic-caption-lines.txt`, author **semantic units** — a clause, a punctuation-to-punctuation run — and let the tool own the display break: `build-semantic-captions` splits a line only where the language allows it (BudouX phrase boundary or clause mark) and prints every boundary it had to move. **Do not hand-wrap to a character budget**: a mechanical wrap at N characters is what cut `服务器` into `传到服` / `务器。` in a shipped film, because Chinese TTS reports one word per character and so the cut bound cleanly. The film's `CaptionFitGate` aborts a render whose cue does not fit the safe width; `--warn-chars N` adds an optional character-count hint (off by default — the shipped templates legitimately run to 19 characters, so no threshold is both useful and false-alarm-free). When a cue is too wide, rewrite the sentence, never break inside a word.
- If a project's `src/index.tsx` builds `DURATION` from a generated `SHOT_TOTAL` (the template does), `retime.py` cannot drive it — the duration is already derived, and only `manifests/asset-manifest.json` (`duration_frames` + per-scene frames) still needs the new numbers.

### Polyphone handling

Chinese TTS is unreliable on polyphones (多音字): one character has several readings and the model guesses from context, so 重装 ("reinstall", 重 = chóng) is often voiced as zhòng. The adapter feeds plain narration text with no pinyin/SSML channel, and `narration.txt` is also the subtitle source, so a wrong reading cannot be patched after synthesis.

Fix it at the source. While writing `narration.txt`, rewrite every easily-misread polyphone into a reading-unambiguous, meaning-equivalent phrase, and mirror the same edit into `manifests/semantic-caption-lines.txt`. This removes the ambiguity entirely (100% reliable) instead of hoping the model reads context correctly, and keeping the replacement close in character count means chapter frames barely shift. Production-verified rewrites:

- 重装（电脑/系统）→ 重新装（重 zhòng vs chóng）
- 批量重命名 → 批量重新命名（重）
- 输一行命令 → 输入一条命令（行 háng vs xíng）
- 钉在屏幕上 → 贴在屏幕上（钉 dìng vs dīng）
- 一模一样 → 长得一样（模 mú vs mó）

Also update any on-screen card text that echoes the rewritten phrase so caption, narration and graphics stay consistent. Polyphones a modern model usually reads correctly in context (调色 tiáo, 时长 cháng, 模型 mó) may stay, but spot-check them at QA. When a mispronunciation still slips through, edit `narration.txt` at the source and re-run synthesis → speed-post → captions → render; never attempt a post-hoc audio patch.

### Zero-key fallback adapter

When no OpenAI-compatible endpoint or paid provider is selected, prefer Edge Read Aloud if the environment can reach it and the intended use fits its terms. For Mandarin, start with a warm neural voice such as `zh-CN-XiaoxiaoNeural`, then adjust rate from the real narration duration rather than from character count.

Use a currently available client as an external adapter; do not add it to the skill dependencies. If the environment requires an HTTP proxy, pass the live `HTTPS_PROXY` value to the client for that invocation. Never copy a transient proxy endpoint into project files. Preserve the service-provided word-boundary JSON and adapt it to the canonical array contract below.

Target a clear, warm Mandarin voice at a moderately brisk rate. Synthesize fresh audio after every narration change and keep the generated word-boundary JSON.

Check English abbreviations, model names and numbers by listening. Do not infer duration from text length.

### Remotion audio tree

Put narration in the component tree:

```tsx
<Audio src={staticFile('narration.mp3')} volume={1} />
```

Action effects come from the **prebuilt SFX library** and are scheduled automatically from the shot table
(`src/sfx.ts` → `planSfx`); you do not hand-place `<Audio>` tags. See `references/audio-captions.md#sfx-library` for the event list,
the automatic rules and the per-shot `sfx` override. Every cue is pinned to a shot start or a beat, so retiming the
narration and re-running `resolve-shots` moves the sounds with the picture.

### Sound vocabulary (SFX library events)

`pop` appear · `chart` bars/lines grow · `highlight` key word/number / generic tick · `success` check/verdict ·
`error` misconception refuted · `chapter` chapter sting · `page` a sheet is turned (every pageturn) ·
`place` / `stamp` the hand-made equivalents of pop / success. Optional `bed.ogg` music bed (quiet pad loop).
Nine events total (slimmed from 16); anything else is not a valid `sfx` event name.

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

#### A word boundary is not a legal break (the trap that shipped a broken film)

"Ends on a TTS word" proves nothing in Chinese: the adapter reports **one word per character**, so every character position looks like a legal word boundary and `传到服` / `务器。` binds cleanly. A real production hit exactly that — a fixed-width wrap at 17 characters cut `服务器` into two cues, and `什么` the same way — and no gate saw it, because the only thing checking breaks was the hand-written phrase list, which `服务器` was not on. **A phrase list is a patch; the rule below is the fix.**

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

Both tools find BudouX in three steps, in this order: an explicit `--budoux-dir`, then the project's `node_modules` (walking up from the caption file, at most eight levels), then **the slice bundled with the skill at `assets/vendor/budoux/`** (BudouX 0.9.2, Apache-2.0, ~80 KB, simplified Chinese only — provenance in `assets/vendor/README.md`). Project dependencies win when present so the model version tracks `package-lock.json`; the bundled slice is what makes the rule run on a fresh clone, where the skill ships no `node_modules`.

On the delivery path (the CLI above) the CLI injects `--require-budoux` automatically and resolves the directory the same way, so **the rule now runs without a prior `npm ci`**. It only hard-fails when even the bundled slice is gone — that is a real breakage, and the message names both fixes (`npm ci` in the project, or `--budoux-dir`). Only an explicit `--no-budoux` opts out, and invoking the validator script directly keeps the loud-skip behavior (stderr `WARNING: BudouX ...`, exit 0) for bare fixtures — the validator itself never writes files; the cue-file record `"break_rule": "mechanical-only (BudouX unavailable)"` is what the **builder** (`build-semantic-captions.py`) stamps into the cue file when it built the cues without BudouX. Pass `--budoux-dir PATH` to point at any directory that has `budoux/module/index.js`.

To watch the rule catch a bad break, feed the fixture (no `--budoux-dir` needed — the bundled slice covers it):

```text
python scripts/validate-semantic-breaks.py bad-cues.json protected.txt
# a cue pair cut as '上网就是连到一台服' / '务器。' reports:
#   SEMANTIC BREAK ERROR: cue 1/2: break at character 9 splits a word or ASCII token: '一台服' | '务器。'
```

`--no-budoux` runs the mechanical half only (rules 3–5), which needs no model and still catches orphaned punctuation and split product names.

#### Width is a separate, softer budget

Character count stays a drafting hint, never a break rule. `--warn-chars N` is off by default and only *warns* when a cue exceeds N characters: no character threshold can be both useful and false-alarm-free, because the shipped templates legitimately run to 19 characters (`在GitHub，全世界的开发者，` is only 16) and `CaptionFitGate` measures the real pixel width in the render browser, rejecting anything over `mode.safe`. When a cue is too wide, **rewrite the narration** or accept more cues; never push the boundary into the middle of a word to hit a number.

### Protected phrases: the curated last mile

Before building cues, create `manifests/protected-caption-phrases.txt`, one phrase per line. It must contain:

- every product, company, person and model name;
- every benchmark or technical proper noun;
- every number together with its unit or comparison target;
- fixed technical phrases such as `上下文窗口` or `完整权重`;
- any short phrase whose meaning becomes incomplete if divided.

Examples of forbidden breaks include `Kimi K` / `3`, `DeepSeek` / `时刻`, `上下` / `文窗口`, `完整权` / `重`, and `Opus` / `四点八`. If a protected phrase is too wide, rewrite the narration; never split the phrase.

This list is the **last mile, not the safety net**. It cannot be complete — `服务器` was missing from a 17-phrase list and that omission shipped — so it exists for names and curated phrases that outrank the model, while the rule above catches the general case. A phrase that no longer appears in the narration is a gate failure, not a harmless leftover: keep the list in step with the script.

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

The word-cut rule is the one that catches what the phrase list misses, so read the validator's last line: it ends with `phrase rule: enforced (BudouX from …)` when the rule ran. On the delivery path (the CLI) that line is mandatory — the CLI passes `--require-budoux`, and the model itself ships with the skill, so an unresolvable BudouX means the bundle was deleted. The `SKIPPED — BudouX not found` tail only remains reachable via a deliberate `--no-budoux` or a direct script invocation where `assets/vendor/` is missing; there, only the mechanical checks and the phrase list were applied.

### Line length: at most 16 characters

Every subtitle line is at most **16 characters** after stripping the trailing punctuation and whitespace
(ASCII counts as one character each, so GitHub costs 6). Long lines are the second-largest source of the
"slide deck" feel: the eye has to read a sentence instead of glancing at a phrase.

- `build-semantic-captions.py --max-chars 16` (default) splits any approved line that is longer at the legal
  break nearest its middle (a break right after a clause mark wins if it costs ≤ 2 characters of balance).
  It never cuts inside a word, an ASCII token or a protected phrase; when a long line has no legal break it
  fails and asks you to shorten the narration.
- `validate-caption-sync.py --max-chars 16` (default) fails any cue that is still longer.
- The render-time `CaptionFitGate` blocks the render for the same reason (`CAPTION_MAX_CHARS` in `src/index.tsx`).
- `--max-chars 0` turns the rule off for a legacy project; do not ship that way.

<a id="sfx-library"></a>

## SFX library

The template ships a small, finished sound-effect library so ordinary AI tools (Windows included) never have to
generate, download or tune sounds. Files live in `assets/lecture-template/public/sfx/lib/`, described by
`public/sfx/sfx-manifest.json` (sha256, duration, loudness, peak, source recipe, license, intended use).

### Events

Nine events plus an optional bed (slimmed from 16; see `src/sfx.ts` for why each cut one went).

The cut seven, and why they were not worth keeping:

| removed | why |
|---|---|
| `whoosh` | every pageturn now gets `page`, on every skin; whoosh only fired on non-pageturn transitions in `normal` |
| `click`, `rustle` | middle-beat ticks that only `normal` used, and `highlight` already covers the same slot |
| `typing` | only middle beats of code / console shots |
| `riser` | only `normal`; also the one library sound earshot scored `no match` (z 1.63) |
| `snip`, `latch` | papercut-only, and only reachable when a story names them explicitly |

Old stories that name a removed event now fail in `resolve-shots.py` with an explicit message instead of going silent.

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

`flat` and `cel` also declare `craft` (ink colour, fonts, default transition), but that is a **capability
configuration**, not a hand-made medium. They keep the UI sounds above. The single authority is
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

### Rebuilt highlight

`highlight` was the weakest sound still in use: `notify #14` with an 1800 Hz high-pass and a 190 ms cut, earshot
CLAP match z 2.04 ("weak"). It is also the single most repeated cue in a sparse film (last beat of every
non-conclusive shot), so a thin tick gets heard twenty times.

The rebuild takes a ready-made sound from earshot's own bank instead of another seed of the same recipe:
`earshot sfx render pro_notify/ding_2296` — a clean short bell, 0.26 s, spectral centroid 3.1 kHz, 6 ms attack.
It passes earshot's model-free audit (`earshot sfx check`: no clicks, no cut tail, no clipping, no DC), is
normalised to the same −18 LUFS / 100 ms, and its transient sits at 8.5 ms (`offsetMs`) instead of 58 ms.
Candidates were compared on measured duration / centroid / attack, not by ear — one-off script kept in
`_acceptance-3.8.0/build-highlight.py`, not shipped.

### Layered pop and chart

`pop` and `chart` were the two weakest sounds of the first library build (earshot CLAP match z 2.49 / 2.47, "weak"):
under narration they read as a faint "plip" and a thin sweep. The final build rebuilds both as **layered** designs in
`scripts/dev/build-sfx-library.py` (its LAYERS table):

| Event | Layers (earshot forge recipe #seed, gain) | Match z |
|---|---|---|
| `pop` | round low body `popin #14` (−3 dB) + bright bubble tick `pop #7` (0 dB) + trimmed sub hit `impact #6` (120 ms, −18 dB) | 3.01 strong |
| `chart` | upward tonal zip `zip #5` (0 dB) + `zip #0` 10 ms later (−2 dB) + landing thump `popin #10` at 200 ms (−8 dB) | 3.15 strong |

A rising four-note arpeggio for `chart` was tried and rejected (CLAP read it as "no match", z 0.95).
Rebuild only these two: `python scripts/dev/build-sfx-library.py --only pop,chart` (the other entries and
files are kept byte-for-byte).

### 调音：每个 cue 的 `gain` 与 `offsetMs`

- 每条 manifest 记录新增 `gain`（线性，把 cue 放到响度阶梯上：chapter −24 · success −25 · pop −25.5 · error / chart −26 · highlight / page −27 · place −26.5 · stamp −25 LUFS，全部比音乐床高 11–17 LU）与 `offsetMs`（文件开头到瞬态的距离）。
- 引擎（`src/sfx.ts`）按 `offsetMs` **提前**起播，瞬态落在视觉命中帧（±1 帧）；`page` 的命中点是转场第 3 帧（纸刚被掀起）。
- 去拥挤：两个 cue 间隔 ≥150 ms（5 帧，优先级高的留下）；任意 10 秒最多 4 个（≈24 次/分钟）。音乐床在每个 cue 命中前 2 帧到后 14 帧闪避到 45%。
- auto 片（story.json）只在真事件上出声：数字落定 `pop`、图表生长 `chart`、关键词第一次推近 `highlight`、答案揭晓 / 改之后出现 `success` / `pop`；章节 `chapter`、每次翻页 `page`。
- `validate-audio-levels.py` 每次出片打印一行「压人声 N 个（事件名）」：显式音效时刻正好落在某句旁白 `[start_ms, speech_end_ms]` 内的条数。自动音效（换章 `chapter`、翻页 `page`）落在换镜帧上、旁白还没开口，实测不产生重叠；会压到说话的只有作者在 story.json 里写的 `sfx`。**只报告不拦截**——少量压人是正常的动作拟音（图表生长、元素落位），全片都压才是问题。
- 维护者：`python scripts/dev/audit-sfx.py [--legacy]` 打分（时序 40 + 电平 30 + 音色 30），`python scripts/dev/tune-sfx.py` 修剪 + 写回 manifest（需 numpy / soundfile / pyloudnorm；普通用户不用跑）。`validate-audio-levels.py` 核对 `SFX_GAIN` / `SFX_OFFSET_MS` 与 manifest 一致。

### 离线质检（维护者可选）

earshot 的定位是**维护者离线质检**，不是运行时依赖——上传包只带成品音频、配方与许可；
普通用户渲染一支视频不得被要求下载 1.1GB 模型或装 PyTorch。

`python scripts/dev/sfx-earshot-audit.py`（缺 earshot 时打印安装提示并 exit 0，不挡出片）：

1. `earshot measure`（无模型、不联网）复核每个 OGG 的 LUFS / 真峰值 / 包络，
   与 `scripts/dev/audit-sfx.py`（numpy + pyloudnorm）的数字并排。两个工具实现不同，
   **LUFS ±0.5 LU / 真峰值 ±0.3 dBFS 以内属正常**；超了脚本会点名，要能解释差异来源。
2. `--mix <成片>` 时用 `earshot timeline` 看真实事件密度与命中点（配合 `--cues`）。
   **先分析、不改声音**：密度/命中点记录下来，改不改由人工盲听决定。

明确不做的三件事：

- 不用 `realness` / CLAP 分数单独决定入库——它们只作参考，必须保留人工盲听与无模型检查；
- 不因工具版本升级重生成整库（只有确有音色缺口才用 `sfx` / `forge` 出候选，
  且衍生配方必须保留源录音许可）；
- `critique` 不直接拿发布宣传片风格当目标——要先有「中文教学旁白 + 克制拟音」的自有 profile。

**验收口径**：同一音频新旧工具测量差异可解释；质检报告可复现（`--json`）；
生成候选经同条件盲听优于旧版才替换；无 earshot 的干净环境仍可正常出片。

### 三段盲听协议（P2-20 · 维护者）

电平合格 ≠ 听感合格。响度 / 峰值 / 削波抓不到三件事：
**旁白下拟音是否掩字**、**连续翻页是否机械**、**静音占位与真人声的动态差异**。
这三件只能用同一套耳朵、同一套段落反复听——段落固定，不能每次现挑。

```
python scripts/dev/listen-segments.py mix.wav out_dir
```

产出 `seg1-open.wav` / `seg2-turns.wav` / `seg3-close.wav` + `segments.json`（切点与打分表）：

| 段 | 取自 | 听什么 | 及格线 |
|---|---|---|---|
| 开场 | 0–20 s | 人声刚进来时拟音在不在、压不压字 | 可懂度 ≥4，关键辅音不被掩 |
| 连续转场 | 最密集的 ≥3 次翻页区 | 机械感、纸声是否同质 | 机械感 ≥3（轮换后应 ≥4） |
| 结论 | 末 20 s | 收束音效、配乐尾、最后一个字 | 可懂度 ≥4，疲劳 ≥3 |

打分 1–5 写进 `segments.json` 的 `verdict`，归档到工程。**先盲听、不改声音**——
改不改由人耳决定；工具只负责把「听哪三段」固定下来。

#### 音色轮换（2026-11-01 起）

连续翻页若每次都是同一段纸声，3 次之后就机械。`page` 现在有三个同源微变体
（`page.ogg` / `page-b.ogg` / `page-c.ogg`，音高与滤波略不同、瞬态位置差 <0.5 ms、
响度差 <0.5 LU），`planSfx` 按出现次序轮换。变体元数据在 `sfx-manifest.json` 的
`variants[]`，与主文件同一套质量口径（sha256 / 峰值下限 / 响度容差 / 瞬态同步）。

#### 动作音同步（验收：≤2 帧）

`offsetMs` = 文件开头到听感命中点的距离，引擎提前这么多起播，命中点就落在视觉帧上。
**命中点的量法是 5 ms RMS 最大值**（与 `scripts/dev/tune-sfx.py` 一致），
不能用「最大绝对值采样」——chart 是上升扫弦、chapter 是闪音，峰值在尾巴上，
用峰值判会误报 140 ms 误差。`validate-audio-levels.py` 现在会逐文件对账，
差 >2 帧（66.7 ms）即 P0。

#### 随旁白 ducking：先盲听再决定

人声 −16 LUFS、拟音 −24…−27 LUFS、音乐床 ≈ −41 LUFS（且在每个 cue 下闪避到 45%）。
按阶梯，拟音已在人声下方 8–14 LU。**是否仍掩字由 seg1 盲听判定**：
若掩，优先下调该事件的 `gain` 阶梯（改 manifest + sfx.ts 两处同值），
而不是继续加音效数量；确有必要再做包络跟随的 ducking（需要旁白包络，属后续项）。

<a id="audio-ducking"></a>

## 音效与旁白的相对电平（P2-20 的剩余部分）

### 为什么这一条还没"做完"

清单里 P2-20 分两半：可机器保证的（变体轮换、同步门禁、盲听协议）已经做完；
剩下的是**随旁白的包络 ducking**，而它被刻意排在盲听之后——先听 seg1，确认"音效真的在掩字"，
再决定是压 ducking 还是调 gain 阶梯。没听就上 ducking，很可能压掉的是本来该有的强调音。

本文把「听完之后怎么执行」写死，避免下次又从头讨论参数。

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

**注意**：当前流水线的音效由 Remotion 在渲染时与旁白一起混，**没有独立的 sfx 轨**。
所以上面这段在现有产物上跑不了——要做 ducking，先得让渲染同时输出一条 sfx-only 音轨
（`<Audio>` 分组 → 单独 composition 或 `--separate-audio-to`），这是实现 ducking 的前置工作，
不是参数问题。这条写在这里，免得下次以为"改个参数就行"。

### 还差什么（诚实清单）

- [ ] 盲听 seg1，按上表落一个判定（需要人，约 15 分钟）
- [ ] 若判定要 ducking：先加 sfx-only 音轨输出，再套上面的表达式
- [ ] 静音占位 vs 真人声的动态差：现在两者用同一套电平门限，真人声的句间呼吸会被当成"静音"，
      需要按 `narration.meta.json` 是否来自 TTS 分流
- [ ] 泵感检测（duck 过度会让音效忽大忽小）：目前没有指标，只能听
