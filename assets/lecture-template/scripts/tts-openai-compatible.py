#!/usr/bin/env python3
"""Chapter-segmented, provider-neutral OpenAI-compatible chat TTS.

Required environment: TTS_API_BASE, TTS_API_KEY, TTS_MODEL. Optional:
TTS_VOICE (or argv[2]), TTS_STYLE_PROMPT. Outputs narration.mp3, its flat
[{part,start,end}] JSON, chapters.json, and ordered tts-segments.json.
Chapter boundaries are measured; character timestamps are estimates, not
forced alignment. Cached audio is validated 48kHz stereo signed 16-bit PCM.
"""
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import wave

GAP_MS = 350
SAMPLE_RATE = 48000
TIMING_QUALITY = "estimated-character"
norm = lambda s: re.sub(r"\s+", "", s)


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cache_key(api_base, model, voice, style_prompt, text):
    config = {"endpoint": api_base.rstrip("/") + "/chat/completions",
              "model": model, "voice": voice, "style_prompt": style_prompt,
              "text": text, "format": "wav", "cache_version": 2,
              "pcm": "48000-stereo-s16le"}
    return hashlib.sha256(json.dumps(config, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def pcm_frames(path):
    with wave.open(str(path), "rb") as f:
        if (f.getframerate(), f.getnchannels(), f.getsampwidth(), f.getcomptype()) != (SAMPLE_RATE, 2, 2, "NONE"):
            raise ValueError(f"not normalized PCM: {path}")
        frames = f.getnframes()
        if frames <= 0:
            raise ValueError(f"empty audio: {path}")
        remaining = frames
        while remaining:
            chunk = f.readframes(min(remaining, SAMPLE_RATE))
            if not chunk or len(chunk) % 4:
                raise ValueError(f"truncated PCM: {path}")
            remaining -= len(chunk) // 4
        return frames


def normalize_audio(source, target, filters=None, frames=None):
    chain = [filters] if filters else []
    chain.append("aresample=48000")
    if frames is not None:
        if frames <= 0:
            raise ValueError("audio sample count must be positive")
        chain.extend([f"apad=whole_len={frames}", f"atrim=end_sample={frames}"])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-xerror", "-i", str(source),
                    "-map", "0:a:0", "-af", ",".join(chain), "-ar", "48000", "-ac", "2",
                    "-c:a", "pcm_s16le", str(target)], check=True)
    actual = pcm_frames(target)
    if frames is not None and actual != frames:
        raise ValueError("incorrect normalized sample count")
    return actual


def encode_mp3(source, target):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-xerror", "-i", str(source),
                    "-ar", "48000", "-ac", "2", "-b:a", "192k", str(target)], check=True)


def join_pcm(parts, target):
    """Parts are normalized WAV paths or exact silence sample counts."""
    with wave.open(str(target), "wb") as out:
        out.setparams((2, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
        for part in parts:
            if isinstance(part, int):
                if part < 0:
                    raise ValueError("negative silence")
                while part:
                    n = min(part, SAMPLE_RATE)
                    out.writeframesraw(b"\0" * (n * 4))
                    part -= n
            else:
                pcm_frames(part)
                with wave.open(str(part), "rb") as source:
                    while True:
                        chunk = source.readframes(SAMPLE_RATE)
                        if not chunk:
                            break
                        out.writeframesraw(chunk)


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def chapter_samples(chapter):
    result = []
    for edge in ("start", "end"):
        ms = chapter[edge + "_ms"]
        sample = chapter.get(edge + "_sample", round(ms * SAMPLE_RATE / 1000))
        if not isinstance(sample, int) or isinstance(sample, bool) or sample < 0:
            raise ValueError("invalid chapter sample boundary")
        if abs(sample * 1000 / SAMPLE_RATE - ms) > 0.501:
            raise ValueError("chapter sample and millisecond boundaries disagree")
        result.append(sample)
    return tuple(result)


def validate_chapters(data):
    if not isinstance(data, list) or not data:
        raise ValueError("chapters must be a nonempty list")
    previous_ms = previous_sample = 0
    for i, ch in enumerate(data, 1):
        if not isinstance(ch, dict) or ch.get("index") != i:
            raise ValueError("chapter indices must be ordered and contiguous")
        start, end = ch.get("start_ms"), ch.get("end_ms")
        if not number(start) or not number(end) or start < previous_ms or end <= start:
            raise ValueError("invalid or overlapping chapter interval")
        s, e = chapter_samples(ch)
        if s < previous_sample or e <= s:
            raise ValueError("invalid or overlapping chapter sample interval")
        previous_ms, previous_sample = end, e
    return data


def map_words(words, chapters, paragraphs):
    validate_chapters(chapters)
    if not isinstance(words, list) or not words or len(paragraphs) != len(chapters):
        raise ValueError("word/chapter/narration mapping is incomplete")
    groups = [[] for _ in chapters]
    ci, previous = 0, 0
    for w in words:
        if not isinstance(w, dict) or not isinstance(w.get("part"), str) or not norm(w["part"]):
            raise ValueError("invalid word part")
        start, end = w.get("start"), w.get("end")
        if type(start) is not int or type(end) is not int or start < previous or end <= start:
            raise ValueError("invalid or overlapping word interval")
        while ci < len(chapters) - 1 and start >= chapters[ci + 1]["start_ms"]:
            ci += 1
        ch = chapters[ci]
        if start < ch["start_ms"] or end > ch["end_ms"]:
            raise ValueError("word is outside its chapter interval")
        groups[ci].append(w)
        previous = end
    for group, text in zip(groups, paragraphs):
        if not group or norm("".join(w["part"] for w in group)) != norm(text):
            raise ValueError("word parts do not reconstruct chapter narration")
    return groups


def active_segments(project, count=None, paragraphs=None):
    root = Path(project).resolve()
    manifest = root / "manifests/tts-segments.json"
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        entries = data.get("segments") if isinstance(data, dict) else None
        if not isinstance(entries, list) or not entries or (count is not None and len(entries) != count):
            raise ValueError("invalid active segment manifest")
        paths = []
        for i, entry in enumerate(entries, 1):
            if not isinstance(entry, dict) or entry.get("index") != i or not isinstance(entry.get("path"), str):
                raise ValueError("invalid active segment entry")
            relative = Path(entry["path"])
            path = (root / relative).resolve()
            if relative.is_absolute() or not path.is_relative_to(root / "audio") or path in paths:
                raise ValueError("invalid active segment path")
            if file_hash(path) != entry.get("sha256"):
                raise ValueError("active segment hash mismatch")
            frames = pcm_frames(path)
            if frames != entry.get("samples"):
                raise ValueError("active segment sample count mismatch")
            if paragraphs is not None and entry.get("text_sha256") != hashlib.sha256(norm(paragraphs[i - 1]).encode()).hexdigest():
                raise ValueError("active segment narration mismatch")
            paths.append(path)
        return paths
    groups = {}
    for path in (root / "audio").glob("seg*.wav"):
        match = re.fullmatch(r"seg([1-9][0-9]*)-(?!matched)[^.]+\.wav", path.name)
        if match and "matched" not in path.name:
            groups.setdefault(int(match[1]), []).append(path)
    expected = count if count is not None else len(groups)
    if not expected or set(groups) != set(range(1, expected + 1)) or any(len(v) != 1 for v in groups.values()):
        raise ValueError("ambiguous or missing segment cache; run TTS to publish an active manifest")
    return [groups[i][0] for i in range(1, expected + 1)]


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
                f"{api_base}/chat/completions", data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=180) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            with tempfile.TemporaryDirectory(prefix=".tts-", dir=Path(out_wav).parent) as tmp:
                raw, pcm = Path(tmp) / "download.wav", Path(tmp) / "normalized.wav"
                raw.write_bytes(base64.b64decode(body["choices"][0]["message"]["audio"]["data"], validate=True))
                normalize_audio(raw, pcm)
                os.replace(pcm, out_wav)
            return
        except Exception as e:
            last = e
            # Provider errors may contain credentials or response text.
            print(f"[tts] attempt {attempt + 1} failed ({type(e).__name__})")
            if attempt + 1 < retries:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError("TTS download or audio validation failed") from last


def load_env(project):
    candidates = [Path(project) / "tts.env", Path(project) / ".env",
                  Path(__file__).parent / "../tts.env", Path(__file__).parent / "../../tts.env"]
    for p in candidates:
        if p.is_file():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def main():
    project = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    load_env(project)
    api_base = os.environ.get("TTS_API_BASE", "").strip().rstrip("/")
    api_key = os.environ.get("TTS_API_KEY", "")
    model = os.environ.get("TTS_MODEL", "").strip()
    url = urllib.parse.urlsplit(api_base)
    if not api_key or not model or url.scheme not in ("https", "http") or not url.netloc:
        raise ValueError("TTS_API_BASE, TTS_API_KEY and TTS_MODEL must be explicitly configured")
    if url.username or url.password or url.query or url.fragment:
        raise ValueError("TTS_API_BASE must not contain credentials, query or fragment")
    voice = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("TTS_VOICE", "")
    style = os.environ.get("TTS_STYLE_PROMPT", "")
    paragraphs = [p.strip() for p in (project / "narration.txt").read_text(encoding="utf-8").splitlines() if p.strip()]
    lines = [p.strip() for p in (project / "manifests/semantic-caption-lines.txt").read_text(encoding="utf-8").splitlines() if p.strip()]
    if not paragraphs or norm("".join(lines)) != norm("".join(paragraphs)):
        raise ValueError("semantic lines do not reconstruct narration.txt")
    para_lines, cursor = [[] for _ in paragraphs], 0
    for pi, paragraph in enumerate(paragraphs):
        built = ""
        while cursor < len(lines) and len(norm(built)) < len(norm(paragraph)):
            para_lines[pi].append(lines[cursor])
            built += lines[cursor]
            cursor += 1
        if norm(built) != norm(paragraph):
            raise ValueError(f"paragraph {pi + 1} does not end on a caption line boundary")
    audio = project / "audio"
    audio.mkdir(exist_ok=True)
    paths, entries = [], []
    for i, paragraph in enumerate(paragraphs, 1):
        digest = cache_key(api_base, model, voice, style, paragraph)
        path = audio / f"seg{i}-{digest}.wav"
        try:
            pcm_frames(path)
        except (OSError, ValueError, wave.Error, EOFError):
            synthesize(api_base, api_key, model, voice, style, paragraph, path)
        frames = pcm_frames(path)
        paths.append(path)
        entries.append({"index": i, "path": path.relative_to(project).as_posix(),
                        "sha256": file_hash(path), "samples": frames, "config_hash": digest,
                        "text_sha256": hashlib.sha256(norm(paragraph).encode()).hexdigest()})
    words, chapters, parts, position = [], [], [], 0
    for i, lines_for_para in enumerate(para_lines):
        if i:
            parts.append(GAP_MS * SAMPLE_RATE // 1000)
            position += parts[-1]
        start, end = position, position + entries[i]["samples"]
        chars = []
        for line in lines_for_para:
            pending = ""
            for char in line:
                if char.isspace():
                    pending += char
                else:
                    chars.append(pending + char)
                    pending = ""
        for j, char in enumerate(chars):
            words.append({"part": char, "start": round((start + (end - start) * j / len(chars)) / 48),
                          "end": round((start + (end - start) * (j + 1) / len(chars)) / 48)})
        chapters.append({"index": i + 1, "start_ms": round(start / 48), "end_ms": round(end / 48),
                         "start_sample": start, "end_sample": end, "text": paragraphs[i][:18] + "…",
                         "timing_quality": TIMING_QUALITY, "chapter_timing_quality": "measured"})
        position = end
        parts.append(paths[i])
    map_words(words, chapters, paragraphs)
    manifest = {"version": 1, "sample_rate": SAMPLE_RATE, "channels": 2,
                "timing_quality": TIMING_QUALITY, "chapter_timing_quality": "measured", "segments": entries}
    with tempfile.TemporaryDirectory(prefix=".tts-publish-", dir=audio) as tmp:
        tmp = Path(tmp)
        join_pcm(parts, tmp / "joined.wav")
        normalize_audio(tmp / "joined.wav", tmp / "narration.wav", "loudnorm=I=-16:TP=-1.5:LRA=11", position)
        encode_mp3(tmp / "narration.wav", tmp / "narration.mp3")
        write_json(tmp / "words.json", words)
        write_json(tmp / "chapters.json", chapters)
        write_json(tmp / "segments.json", manifest)
        for source, target in [("narration.wav", audio / "narration.wav"), ("narration.mp3", audio / "narration.mp3"),
                               ("words.json", audio / "narration.mp3.json"), ("chapters.json", project / "manifests/chapters.json"),
                               ("segments.json", project / "manifests/tts-segments.json")]:
            os.replace(tmp / source, target)
    print(f"[tts] total {position / 48:.3f} ms; word timing quality: {TIMING_QUALITY}")


if __name__ == "__main__":
    main()
