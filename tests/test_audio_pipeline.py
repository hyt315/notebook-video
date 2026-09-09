"""Local audio pipeline regressions. No provider calls or third-party Python packages."""
import base64
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import wave

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets/lecture-template/scripts"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tts = load("test_tts", TEMPLATE / "tts-openai-compatible.py")
speed = load("test_speed", TEMPLATE / "speed-post.py")
match = load("test_match", ROOT / "scripts/match-timing.py")
audition = load("test_audition", ROOT / "scripts/audition.py")


def wav_bytes(rate=24000, channels=1, seconds=0.6, frequency=440):
    data = io.BytesIO()
    with wave.open(data, "wb") as out:
        out.setparams((channels, 2, rate, 0, "NONE", "not compressed"))
        out.writeframes(b"".join(struct.pack("<h", int(6000 * math.sin(2 * math.pi * frequency * n / rate))) * channels
                                 for n in range(round(rate * seconds))))
    return data.getvalue()


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class AudioPipelineTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(os.environ.get("AUDIO_TEST_TMP", tempfile.gettempdir()))
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="audio-pipeline-", dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "audio").mkdir()
        (self.root / "manifests").mkdir()
        (self.root / "narration.txt").write_text("Hello world\nSecond chapter\n", encoding="utf-8")
        (self.root / "manifests/semantic-caption-lines.txt").write_text("Hello world\nSecond chapter\n", encoding="utf-8")
        self.env = {"TTS_API_BASE": "https://voice.example.test/v1", "TTS_API_KEY": "secret-token",
                    "TTS_MODEL": "test-model", "TTS_VOICE": "voice-a", "TTS_STYLE_PROMPT": "clear"}
        self.payloads = [wav_bytes(), wav_bytes(44100, 2, 0.7, 660)]

    def invoke(self, module, *args):
        with mock.patch.object(sys, "argv", [module.__file__, str(self.root), *map(str, args)]):
            module.main()

    def provider(self, request, timeout):
        body = json.loads(request.data)
        text = body["messages"][-1]["content"]
        index = 0 if text == "Hello world" else 1
        return io.BytesIO(json.dumps({"choices": [{"message": {"audio": {
            "data": base64.b64encode(self.payloads[index]).decode()}}}]}).encode())

    def generate(self, **config):
        with mock.patch.dict(os.environ, self.env | config, clear=True), \
             mock.patch.object(tts.urllib.request, "urlopen", side_effect=self.provider) as provider:
            self.invoke(tts)
            return provider.call_count

    def read_json(self, rel):
        return json.loads((self.root / rel).read_text(encoding="utf-8"))

    def canonical(self):
        rels = ["audio/narration.mp3", "audio/narration.wav", "audio/narration.mp3.json",
                "audio/narration-matched.wav", "manifests/chapters.json", "manifests/tts-segments.json",
                "manifests/speed-post.json", "manifests/chapters-timing-lock.json"]
        return {rel: (self.root / rel).read_bytes() if (self.root / rel).exists() else None for rel in rels}

    def test_mixed_provider_formats_normalized_before_measuring(self):
        self.assertEqual(self.generate(), 2)
        paths = tts.active_segments(self.root, 2)
        self.assertEqual([tts.pcm_frames(p) for p in paths], [28800, 33600])
        self.assertEqual(tts.pcm_frames(self.root / "audio/narration.wav"), 79200)
        chapters = self.read_json("manifests/chapters.json")
        self.assertEqual([(c["start_ms"], c["end_ms"]) for c in chapters], [(0, 600), (950, 1650)])
        self.assertEqual([(c["start_sample"], c["end_sample"]) for c in chapters], [(0, 28800), (45600, 79200)])
        decoded = self.root / "decoded.wav"
        self.assertEqual(tts.normalize_audio(self.root / "audio/narration.mp3", decoded), 79200)

    def test_cache_config_covers_endpoint_style_model_voice_text_not_key(self):
        args = ["https://one.test/v1", "model", "voice", "style", "text"]
        original = tts.cache_key(*args)
        for i in range(len(args)):
            changed = args.copy()
            changed[i] += "other"
            self.assertNotEqual(tts.cache_key(*changed), original)
        self.assertEqual(self.generate(), 2)
        self.assertEqual(self.generate(TTS_API_KEY="rotated-secret"), 0)
        self.assertEqual(self.generate(TTS_STYLE_PROMPT="new style"), 2)
        self.assertEqual(self.generate(TTS_API_BASE="https://other.example.test/v1"), 2)
        manifest_text = (self.root / "manifests/tts-segments.json").read_text()
        self.assertNotIn("secret-token", manifest_text)
        self.assertNotIn("rotated-secret", manifest_text)

    def test_base_and_model_are_required_without_vendor_defaults(self):
        for missing in ("TTS_API_BASE", "TTS_MODEL"):
            with self.subTest(missing=missing), mock.patch.dict(os.environ, self.env | {missing: ""}, clear=True), \
                 mock.patch.object(tts, "synthesize") as synth:
                with self.assertRaises(ValueError):
                    self.invoke(tts)
                synth.assert_not_called()
        self.assertFalse((self.root / "audio/narration.mp3").exists())

    def test_invalid_download_does_not_replace_existing_cache(self):
        cache = self.root / "audio/existing.wav"
        cache.write_bytes(b"existing bytes")
        for data in ("not base64!", base64.b64encode(b"not a wav").decode(),
                     base64.b64encode(self.payloads[0][:1000]).decode()):
            response = json.dumps({"choices": [{"message": {"audio": {"data": data}}}]}).encode()
            with mock.patch.object(tts.urllib.request, "urlopen", return_value=io.BytesIO(response)):
                with self.assertRaises(RuntimeError):
                    tts.synthesize(self.env["TTS_API_BASE"], "secret", "model", "", "", "text", cache, retries=1)
            self.assertEqual(cache.read_bytes(), b"existing bytes")
        self.assertFalse(list((self.root / "audio").glob(".tts-*")))

    def test_corrupt_cache_is_replaced_with_valid_pcm(self):
        self.generate()
        path = tts.active_segments(self.root, 2)[0]
        path.write_bytes(b"bad cache")
        self.assertEqual(self.generate(), 1)
        self.assertEqual(tts.pcm_frames(path), 28800)

    def test_active_manifest_ignores_historical_and_matched_files(self):
        self.generate()
        old = tts.active_segments(self.root, 2)
        self.generate(TTS_VOICE="voice-b")
        active = tts.active_segments(self.root, 2)
        self.assertNotEqual(active, old)
        (self.root / "audio/seg-matched01.wav").write_bytes(b"stale")
        (self.root / "audio/seg1-matched.wav").write_bytes(b"stale")
        self.assertEqual(tts.active_segments(self.root, 2), active)
        with mock.patch.object(audition.audio_helpers, "normalize_audio", wraps=audition.audio_helpers.normalize_audio) as normalize:
            self.assertEqual(audition.audition(self.root), 0)
            self.assertEqual([c.args[0] for c in normalize.call_args_list], active)
        self.assertFalse(list((self.root / "audio").glob(".audition-*")))

    def test_legacy_selection_is_numeric_and_refuses_ambiguity(self):
        for i in range(1, 12):
            (self.root / f"audio/seg{i}-old.wav").write_bytes(b"fixture")
        (self.root / "audio/seg-matched01.wav").write_bytes(b"stale")
        paths = tts.active_segments(self.root, 11)
        self.assertEqual([p.name for p in paths], [f"seg{i}-old.wav" for i in range(1, 12)])
        (self.root / "audio/seg1-new.wav").write_bytes(b"fixture")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            tts.active_segments(self.root, 11)

    def test_manifest_hash_and_text_mismatch_are_refused(self):
        self.generate()
        with self.assertRaisesRegex(ValueError, "narration mismatch"):
            tts.active_segments(self.root, 2, ["Changed", "Second chapter"])
        path = tts.active_segments(self.root, 2)[0]
        path.write_bytes(path.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            tts.active_segments(self.root, 2)

    def test_timing_quality_keeps_flat_word_contract(self):
        self.generate()
        manifest = self.read_json("manifests/tts-segments.json")
        self.assertEqual(manifest["timing_quality"], "estimated-character")
        self.assertEqual(manifest["chapter_timing_quality"], "measured")
        self.assertTrue(all(set(w) == {"part", "start", "end"} for w in self.read_json("audio/narration.mp3.json")))
        self.invoke(speed, "1.10")
        self.assertEqual(self.read_json("manifests/speed-post.json")["timing_quality"], "estimated-character")

    def test_speed_repeat_guard_and_fresh_voice(self):
        self.generate()
        self.invoke(speed, 1.10)
        before = self.canonical()
        with self.assertRaisesRegex(ValueError, "already"):
            self.invoke(speed, 1.20)
        self.assertEqual(self.canonical(), before)
        self.payloads[0] = wav_bytes(frequency=880)
        self.generate(TTS_VOICE="fresh")
        self.invoke(speed, 1.10)
        self.assertEqual(len(self.read_json("manifests/speed-post.json")["processed_audio_sha256"]), 2)

    def test_invalid_tempos_preserve_canonical(self):
        self.generate()
        before = self.canonical()
        for tempo in ("nan", "inf", "0", "-1", "0.49", "2.01", "garbage"):
            with self.subTest(tempo=tempo), self.assertRaises(ValueError):
                self.invoke(speed, tempo)
            self.assertEqual(self.canonical(), before)

    def test_speed_invalid_json_and_mapping_preserve_canonical(self):
        self.generate()
        words = self.root / "audio/narration.mp3.json"
        valid = words.read_bytes()
        for bad in (b"{broken", b'[{"part":"wrong","start":0,"end":600}]'):
            words.write_bytes(bad)
            before = self.canonical()
            with mock.patch.object(speed.audio, "normalize_audio") as ffmpeg:
                with self.assertRaises(ValueError):
                    self.invoke(speed)
                ffmpeg.assert_not_called()
            self.assertEqual(self.canonical(), before)
        words.write_bytes(valid)

    def test_speed_encode_failure_preserves_canonical(self):
        self.generate()
        before = self.canonical()
        with mock.patch.object(speed.audio, "encode_mp3", side_effect=subprocess.CalledProcessError(1, "ffmpeg")):
            with self.assertRaises(subprocess.CalledProcessError):
                self.invoke(speed)
        self.assertEqual(self.canonical(), before)

    def test_adapter_encode_failure_preserves_canonical(self):
        self.generate()
        before = self.canonical()
        with mock.patch.object(tts, "encode_mp3", side_effect=subprocess.CalledProcessError(1, "ffmpeg")):
            with self.assertRaises(subprocess.CalledProcessError):
                self.generate(TTS_VOICE="another")
        self.assertEqual(self.canonical(), before)

    def make_leading_trailing_timeline(self):
        self.generate()
        paths = tts.active_segments(self.root, 2)
        joined = self.root / "padded.wav"
        tts.join_pcm([5280, paths[0], 16800, paths[1], 4320], joined)
        shutil.copyfile(joined, self.root / "audio/narration.wav")
        tts.encode_mp3(joined, self.root / "audio/narration.mp3")
        chapters = self.read_json("manifests/chapters.json")
        for ch in chapters:
            ch["start_ms"] += 110
            ch["end_ms"] += 110
            ch["start_sample"] += 5280
            ch["end_sample"] += 5280
        tts.write_json(self.root / "manifests/chapters.json", chapters)
        # Multi-character word items with pauses, deliberately not one per character.
        words = [{"part": "Hello ", "start": 120, "end": 300}, {"part": "world", "start": 350, "end": 690},
                 {"part": "Second ", "start": 1070, "end": 1290}, {"part": "chapter", "start": 1330, "end": 1730}]
        tts.write_json(self.root / "audio/narration.mp3.json", words)

    def test_match_after_speed_preserves_exact_samples_gaps_and_word_groups(self):
        self.make_leading_trailing_timeline()
        self.invoke(speed, 1.10)
        self.invoke(match, "--lock")
        lock = self.read_json("manifests/chapters-timing-lock.json")
        gap = lock[1]["start_sample"] - lock[0]["end_sample"]
        self.assertIn(gap, (15272, 15273))
        self.assertEqual(lock[-1]["timeline_total_samples"], round(88800 / 1.1))
        # Revoice leaves old caches behind, then follows the documented speed step.
        self.payloads = [wav_bytes(seconds=0.65, frequency=550), wav_bytes(32000, 1, 0.75, 770)]
        self.generate(TTS_VOICE="revoice")
        self.invoke(speed, 1.10)
        current = self.read_json("manifests/chapters.json")
        multi = []
        for text, ch in zip(("Hello world", "Second chapter"), current):
            multi.append({"part": text, "start": ch["start_ms"] + 10, "end": ch["end_ms"] - 15})
        tts.write_json(self.root / "audio/narration.mp3.json", multi)
        self.invoke(match)
        wav = self.root / "audio/narration.wav"
        self.assertEqual(tts.pcm_frames(wav), lock[-1]["timeline_total_samples"])
        self.assertEqual(wav.read_bytes(), (self.root / "audio/narration-matched.wav").read_bytes())
        result = self.read_json("manifests/chapters.json")
        self.assertEqual([(c["start_sample"], c["end_sample"]) for c in result],
                         [(c["start_sample"], c["end_sample"]) for c in lock])
        with wave.open(str(wav), "rb") as stream:
            for start, end in [(0, lock[0]["start_sample"]), (lock[0]["end_sample"], lock[1]["start_sample"]),
                               (lock[-1]["end_sample"], lock[-1]["timeline_total_samples"])]:
                stream.setpos(start + (end - start) // 3)
                self.assertEqual(stream.readframes(100), b"\0" * 400)
            for ch in lock:
                stream.setpos((ch["start_sample"] + ch["end_sample"]) // 2)
                self.assertNotEqual(stream.readframes(100), b"\0" * 400)
        scaled = self.read_json("audio/narration.mp3.json")
        self.assertEqual(len(scaled), 2)
        for old, source_ch, target, word in zip(multi, current, lock, scaled):
            ratio = (target["end_ms"] - target["start_ms"]) / (source_ch["end_ms"] - source_ch["start_ms"])
            self.assertEqual(word["part"], old["part"])
            for edge in ("start", "end"):
                self.assertEqual(word[edge], round(target["start_ms"] + (old[edge] - source_ch["start_ms"]) * ratio))
        self.assertTrue(all(c["timing_quality"] == "estimated-character" for c in result))

    def test_match_invalid_ratios_and_words_preserve_canonical(self):
        self.generate()
        self.invoke(match, "--lock")
        lock_path = self.root / "manifests/chapters-timing-lock.json"
        good_lock = lock_path.read_bytes()
        for duration in (200, 1400):
            lock = json.loads(good_lock)
            lock[0]["end_ms"] = duration
            lock[0]["end_sample"] = duration * 48
            lock[1]["start_ms"] = duration + 350
            lock[1]["end_ms"] = duration + 1050
            lock[1]["start_sample"] = (duration + 350) * 48
            lock[1]["end_sample"] = (duration + 1050) * 48
            lock[1]["timeline_total_samples"] = lock[1]["end_sample"]
            tts.write_json(lock_path, lock)
            before = self.canonical()
            with self.assertRaisesRegex(ValueError, "outside 0.5-2.0"):
                self.invoke(match)
            self.assertEqual(self.canonical(), before)
        lock_path.write_bytes(good_lock)
        words = self.read_json("audio/narration.mp3.json")
        words[0]["end"] = 999
        tts.write_json(self.root / "audio/narration.mp3.json", words)
        before = self.canonical()
        with self.assertRaises(ValueError):
            self.invoke(match)
        self.assertEqual(self.canonical(), before)

    def test_match_encode_failure_preserves_canonical(self):
        self.generate()
        self.invoke(match, "--lock")
        before = self.canonical()
        with mock.patch.object(match.audio, "encode_mp3", side_effect=subprocess.CalledProcessError(1, "ffmpeg")):
            with self.assertRaises(subprocess.CalledProcessError):
                self.invoke(match)
        self.assertEqual(self.canonical(), before)

    def test_legacy_match_accepts_mixed_segments_and_interval_words(self):
        self.generate()
        self.invoke(match, "--lock")
        paths = tts.active_segments(self.root, 2)
        for path, payload in zip(paths, self.payloads):
            path.write_bytes(payload)
        (self.root / "manifests/tts-segments.json").unlink()
        words = [{"part": "Hello world", "start": 0, "end": 600},
                 {"part": "Second chapter", "start": 950, "end": 1650}]
        tts.write_json(self.root / "audio/narration.mp3.json", words)
        self.invoke(match)
        self.assertEqual(tts.pcm_frames(self.root / "audio/narration.wav"), 79200)
        self.assertEqual(self.read_json("audio/narration.mp3.json"), words)
    def test_speed_corrupt_audio_and_invalid_chapters_preserve_canonical(self):
        self.generate()
        path = self.root / "manifests/chapters.json"
        valid = path.read_bytes()
        for bad in ([], [{"index": 1, "start_ms": 0, "end_ms": -1}],
                    [{"index": 1, "start_ms": 0, "end_ms": float("nan")}],
                    [{"index": 1, "start_ms": 0, "end_ms": 600, "end_sample": 48000}]):
            tts.write_json(path, bad)
            before = self.canonical()
            with self.assertRaises(ValueError):
                self.invoke(speed)
            self.assertEqual(self.canonical(), before)
        path.write_bytes(valid)
        (self.root / "audio/narration.mp3").write_bytes(b"corrupt audio")
        before = self.canonical()
        with self.assertRaises(subprocess.CalledProcessError):
            self.invoke(speed)
        self.assertEqual(self.canonical(), before)

    def test_match_ratio_endpoints_produce_exact_samples(self):
        self.generate()
        self.invoke(match, "--lock")
        lock_path = self.root / "manifests/chapters-timing-lock.json"
        original = lock_path.read_bytes()
        original_words = (self.root / "audio/narration.mp3.json").read_bytes()
        original_chapters = (self.root / "manifests/chapters.json").read_bytes()
        for rate in (0.5, 2.0):
            lock = json.loads(original)
            position = 0
            for ch, duration in zip(lock, (28800, 33600)):
                ch["start_sample"] = position
                ch["end_sample"] = position + round(duration / rate)
                ch["start_ms"] = round(ch["start_sample"] / 48)
                ch["end_ms"] = round(ch["end_sample"] / 48)
                position = ch["end_sample"] + 16800
            lock[-1]["timeline_total_samples"] = lock[-1]["end_sample"]
            tts.write_json(lock_path, lock)
            (self.root / "audio/narration.mp3.json").write_bytes(original_words)
            (self.root / "manifests/chapters.json").write_bytes(original_chapters)
            self.invoke(match)
            self.assertEqual(tts.pcm_frames(self.root / "audio/narration.wav"), lock[-1]["end_sample"])


if __name__ == "__main__":
    unittest.main()
