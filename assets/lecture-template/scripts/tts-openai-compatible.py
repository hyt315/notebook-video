"""Chapter-segmented TTS adapter for any OpenAI-compatible chat TTS endpoint.

Provider-neutral: point it at any service that accepts a chat/completions
payload with an ``audio`` block and returns base64 audio (for example
MiMo-V2.5-TTS). Configure through environment variables only; never write
keys into project files.

  TTS_API_BASE      required, e.g. https://api.example.com/v1
  TTS_API_KEY       required, bearer token
  TTS_MODEL         required, e.g. mimo-v2.5-tts
  TTS_VOICE         optional, provider voice id (or pass as argv[2])
  TTS_STYLE_PROMPT  optional, spoken-style instruction for the user turn

Why chapter-segmented: each narration paragraph is synthesized separately,
then joined with a fixed silence gap. Every chapter boundary is measured
from real audio, so captions and scene cuts never drift on long films.
Per-character timings are derived inside each measured paragraph.

Outputs (the documented notebook-video adapter contract):
  - audio/narration.mp3        48kHz stereo, loudness-normalized to -16 LUFS
  - audio/narration.mp3.json   flat per-word [{part,start,end}] stream (ms)
  - manifests/chapters.json    [{index,start_ms,end_ms,text}] per paragraph;
                               chapter start/end frames = ms * fps / 1000
"""
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

GAP_MS = 350

norm = lambda s: re.sub(r"\s+", "", s)


def synthesize(api_base, api_key, model, voice, style_prompt, text, out_wav, retries=4):
    messages = []
    if style_prompt:
        messages.append({"role": "user", "content": style_prompt})
    messages.append({"role": "assistant", "content": text})
    audio_opts = {"format": "wav"}
    if voice:
        audio_opts["voice"] = voice
    payload = {"model": model, "messages": messages, "audio": audio_opts}
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                f"{api_base}/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            with open(out_wav, "wb") as f:
                f.write(base64.b64decode(body["choices"][0]["message"]["audio"]["data"]))
            return
        except Exception as e:  # transient proxy/SSL hiccups
            last = e
            print(f"[tts] attempt {attempt+1} failed: {e}; retrying ...")
            time.sleep(2 * (attempt + 1))
    raise last


def probe_ms(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path], text=True)
    return int(round(float(out.strip()) * 1000))


def main():
    project = sys.argv[1]
    api_base = os.environ["TTS_API_BASE"].rstrip("/")
    api_key = os.environ["TTS_API_KEY"]
    model = os.environ["TTS_MODEL"]
    voice = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("TTS_VOICE", "")
    style_prompt = os.environ.get("TTS_STYLE_PROMPT",
                                  "用清晰、温暖、有耐心的普通话讲解，语速适中，像面向新手的知识科普博主。")

    with open(os.path.join(project, "narration.txt"), encoding="utf-8") as f:
        paragraphs = [p.strip() for p in f if p.strip()]
    with open(os.path.join(project, "manifests", "semantic-caption-lines.txt"), encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    if norm("".join(lines)) != norm("".join(paragraphs)):
        raise SystemExit("semantic lines do not reconstruct narration.txt")

    # assign caption lines to paragraphs sequentially
    para_lines, cursor = [[] for _ in paragraphs], 0
    for pi, p in enumerate(paragraphs):
        built = ""
        while cursor < len(lines) and len(norm(built)) < len(norm(p)):
            para_lines[pi].append(lines[cursor]); built += lines[cursor]; cursor += 1
        if norm(built) != norm(p):
            raise SystemExit(f"paragraph {pi+1} does not end on a caption line boundary")

    audio_dir = os.path.join(project, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    seg_paths, seg_ms = [], []
    for i, p in enumerate(paragraphs):
        # cache key includes the text, so edited paragraphs always re-synthesize
        digest = hashlib.sha256(f"{model}|{voice}|{p}".encode("utf-8")).hexdigest()[:12]
        seg = os.path.join(audio_dir, f"seg{i+1}-{digest}.wav")
        if os.path.isfile(seg) and os.path.getsize(seg) > 1000:
            print(f"[tts] segment {i+1}/{len(paragraphs)}: cached")
        else:
            print(f"[tts] segment {i+1}/{len(paragraphs)}: {len(p)} chars ...")
            synthesize(api_base, api_key, model, voice, style_prompt, p, seg)
        seg_paths.append(seg); seg_ms.append(probe_ms(seg))

    silence = os.path.join(audio_dir, "gap.wav")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                           "-i", "anullsrc=r=24000:cl=mono", "-t", str(GAP_MS / 1000),
                           "-c:a", "pcm_s16le", silence])
    concat_list = os.path.join(audio_dir, "concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for i, seg in enumerate(seg_paths):
            if i: f.write(f"file '{os.path.basename(silence)}'\n")
            f.write(f"file '{os.path.basename(seg)}'\n")
    joined = os.path.join(audio_dir, "narration.wav")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                           "-i", concat_list, "-c", "copy", joined])
    out_mp3 = os.path.join(audio_dir, "narration.mp3")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", joined,
                           "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                           "-ar", "48000", "-ac", "2", "-b:a", "192k", out_mp3])

    words, chapters, t = [], [], 0
    for pi, p in enumerate(paragraphs):
        start, dur = t, seg_ms[pi]
        chars = [c for line in para_lines[pi] for c in line if not c.isspace()]
        step = dur / max(1, len(chars))
        for j, ch in enumerate(chars):
            words.append({"part": ch, "start": int(round(start + j * step)),
                          "end": int(round(start + (j + 1) * step))})
        chapters.append({"index": pi + 1, "start_ms": start, "end_ms": start + dur, "text": p[:18] + "…"})
        t = start + dur + GAP_MS

    # re-insert spaces so concatenated parts reconstruct lines exactly
    stream, k = [], 0
    for line in lines:
        pending = ""
        for ch in line:
            if ch.isspace():
                pending += ch; continue
            w = dict(words[k]); k += 1
            w["part"] = pending + w["part"]; pending = ""
            stream.append(w)
    assert k == len(words)

    with open(out_mp3 + ".json", "w", encoding="utf-8") as f:
        json.dump(stream, f, ensure_ascii=False, indent=2)
    with open(os.path.join(project, "manifests", "chapters.json"), "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)
    total = t - GAP_MS
    print(f"[tts] total {total} ms ({total/1000:.2f}s) = {round(total*30/1000)} design frames @30fps")
    for c in chapters:
        print(f"[tts] ch{c['index']}: {c['start_ms']}-{c['end_ms']} ms  (frames {round(c['start_ms']*30/1000)}-{round(c['end_ms']*30/1000)})  {c['text']}")


if __name__ == "__main__":
    main()
