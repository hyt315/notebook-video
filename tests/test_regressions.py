import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PipelineTests(unittest.TestCase):
    def test_legacy_audio_package_round_trip(self):
        pack=load('package-project')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'legacy';(p/'audio').mkdir(parents=True)
            source=p/'audio/seg1-original.wav';source.write_bytes(b'legacy active audio')
            output=Path(td)/'legacy.zip';pack.package(p,output)
            extracted=Path(td)/'extracted'
            with zipfile.ZipFile(output) as z:z.extractall(extracted)
            self.assertEqual(source.read_bytes(),(extracted/'audio/seg1-original.wav').read_bytes())
            (p/'audio/seg1-another-voice.wav').write_bytes(b'another voice')
            before=output.read_bytes()
            with self.assertRaisesRegex(ValueError,'Ambiguous legacy'):
                pack.package(p,output)
            self.assertEqual(before,output.read_bytes())

    def test_active_audio_survives_packaging_and_invalid_manifest_preserves_archive(self):
        pack=load('package-project')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'project'; (p/'audio').mkdir(parents=True); (p/'manifests').mkdir()
            active=p/'audio/seg1-current.wav'; active.write_bytes(b'active PCM fixture')
            (p/'audio/seg1-obsolete.wav').write_bytes(b'old voice')
            manifest=p/'manifests/tts-segments.json'
            manifest.write_text(json.dumps({'segments':[{'path':'audio/seg1-current.wav','sha256':hashlib.sha256(active.read_bytes()).hexdigest()}]}))
            output=Path(td)/'project.zip'; pack.package(p,output)
            with zipfile.ZipFile(output) as z:
                self.assertIn('audio/seg1-current.wav',z.namelist())
                self.assertNotIn('audio/seg1-obsolete.wav',z.namelist())
            before=output.read_bytes();active.unlink()
            with self.assertRaises(ValueError): pack.package(p,output)
            self.assertEqual(before,output.read_bytes())

    def test_template_sync_validates_before_writing_and_preserves_unchanged_mtime(self):
        for template in ['lecture-template','example-project']:
            with self.subTest(template=template),tempfile.TemporaryDirectory() as td:
                p=Path(td);(p/'audio').mkdir();(p/'manifests').mkdir()
                (p/'sync.cjs').write_bytes((ROOT/'assets'/template/'sync-render-inputs.cjs').read_bytes())
                (p/'audio/narration.mp3').write_bytes(b'audio fixture')
                (p/'manifests/caption-cues.json').write_text('{}')
                run=lambda:subprocess.run(['node',str(p/'sync.cjs')],capture_output=True)
                self.assertNotEqual(run().returncode,0)
                self.assertFalse((p/'public/narration.mp3').exists())
                (p/'audio/narration.mp3.json').write_text('[]')
                self.assertEqual(run().returncode,0)
                target=p/'src/caption-cues.json';before=target.stat().st_mtime_ns
                self.assertEqual(run().returncode,0)
                self.assertEqual(before,target.stat().st_mtime_ns)

    def test_review_plan_and_half_frame_tail(self):
        p=ROOT/'assets/lecture-template'
        manifest=json.loads((p/'manifests/asset-manifest.json').read_text())
        words=json.loads((p/'audio/narration.mp3.json').read_text())
        cues=json.loads((p/'manifests/caption-cues.json').read_text())['cues']
        self.assertGreaterEqual(manifest['duration_frames'],int(words[-1]['end']*30/1000+.5)+21)
        review=load('review-plan').review_plan(manifest,cues)
        frames={item['frame'] for item in review['frames']}
        self.assertIn(manifest['duration_frames']-1,frames)
        for scene in manifest['scenes']:
            self.assertIn(scene['start_frame'],frames)
            for beat in scene.get('beats',[]): self.assertIn(beat['frame'],frames)
        self.assertTrue(all(0<=start<=end<manifest['duration_frames'] for start,end in review['ranges']))

    def test_packaging_excludes_secrets_caches_and_links(self):
        pack = load('package-project')
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'project'
            p.mkdir()
            for name in ['.env', '.env.local', 'tts.env', '.npmrc', 'private.key', 'source.tsx', '.env.example']:
                (p / name).write_text('dummy')
            (p / 'audio').mkdir()
            for name in ['seg-matched01.wav', 'narration.mp3', 'narration.mp3.json']:
                (p / 'audio' / name).write_text('dummy')
            outside = Path(td) / 'outside'
            outside.write_text('secret')
            try:
                (p / 'linked.txt').symlink_to(outside)
            except OSError:
                pass
            output = p / 'bundle.zip'
            pack.package(p, output)
            pack.package(p, output)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(set(z.namelist()), {'source.tsx', '.env.example', 'audio/narration.mp3', 'audio/narration.mp3.json'})

    def test_retime_failure_does_not_mutate(self):
        retime = load('retime').retime
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / 'src').mkdir(); (p / 'manifests').mkdir()
            source = p / 'src/index.tsx'; manifest = p / 'manifests/asset-manifest.json'
            source.write_text('const DURATION = 100;')
            manifest.write_text(json.dumps({'duration_frames': 100, 'scenes': [{}, {}]}))
            before = (source.read_bytes(), manifest.read_bytes())
            for duration, bounds in [(200, [0, 200]), (200, [0, 300, 200]), (200, [0, 0, 200]), (-1, [0, -1])]:
                with self.subTest(bounds=bounds), self.assertRaises(ValueError):
                    retime(p, duration, bounds)
                self.assertEqual(before, (source.read_bytes(), manifest.read_bytes()))
            retime(p, 200, [0, 120, 200])
            self.assertIn('DURATION=200', source.read_text())
            self.assertEqual(json.loads(manifest.read_text())['scenes'][1]['start_frame'], 120)

    def test_caption_invalid_timings(self):
        validate = load('validate-caption-sync').validate
        words = [{'part': '测试', 'start': 100, 'end': 200}]
        good = {'segmentation': 'semantic', 'cues': [{'text': '测试', 'words': words, 'start_ms': 40, 'speech_end_ms': 200, 'reveal_end_ms': 200}]}
        self.assertEqual(validate(words, good), [])
        for start, end in [(-1, 200), (100, 99), (100, 100), (100.5, 200), (True, 200)]:
            with self.subTest(start=start, end=end):
                badwords = [{'part': '测试', 'start': start, 'end': end}]
                data = copy.deepcopy(good); data['cues'][0]['words'] = badwords
                self.assertTrue(validate(badwords, data))
        for key, value in [('speech_end_ms', -999), ('reveal_end_ms', 199), ('start_ms', -1)]:
            data = copy.deepcopy(good); data['cues'][0][key] = value
            self.assertTrue(validate(words, data))
        self.assertTrue(validate([], {'segmentation': 'semantic', 'cues': []}))
        self.assertTrue(validate(words, good, 90))

    def test_caption_builder_rejects_invalid_source_before_writing(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            words=p/'words.json'; lines=p/'lines.txt'; out=p/'cues.json'
            words.write_text('[{"part":"Hi","start":1000,"end":-1}]')
            lines.write_text('Hi')
            proc=subprocess.run([sys.executable,str(ROOT/'scripts/build-semantic-captions.py'),str(words),str(lines),str(out)],capture_output=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertFalse(out.exists())

    @unittest.skipIf(os.name == 'nt', 'POSIX executable stubs; Windows uses real media integration tests')
    def test_media_qa_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); video=p/'video.mp4'; video.write_bytes(b'fixture')
            probe={'streams':[{'codec_type':'video','codec_name':'h264','width':2560,'height':1440,'r_frame_rate':'30/1'}, {'codec_type':'audio','codec_name':'aac','sample_rate':'48000','channels':2}], 'format':{'duration':'1'}}
            def stub(name, body):
                file=p/name; file.write_text('#!'+sys.executable+'\n'+body); file.chmod(0o755)
            for mode in ['black-failure','loudness-failure','missing-sheet','bad-duration']:
                data=copy.deepcopy(probe)
                if mode=='bad-duration': data['format']['duration']='N/A'
                stub('ffprobe','print('+repr(json.dumps(data))+')\n')
                stub('ffmpeg',f"""import sys
mode={mode!r}
args=' '.join(sys.argv)
if 'blackdetect' in args and mode=='black-failure': sys.exit(9)
if 'loudnorm' in args:
 if mode=='loudness-failure': sys.exit(8)
 print('Input Integrated: -16.0 LUFS\\nInput True Peak: -2.0 dBTP',file=sys.stderr)
""")
                env={**os.environ,'PATH':str(p)+os.pathsep+os.environ['PATH']}
                result=subprocess.run(['node',str(ROOT/'scripts/notebook-video.mjs'),'validate-video',str(video),'1',str(p/'contact.jpg')],capture_output=True,text=True,env=env)
                with self.subTest(mode=mode):
                    self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
                    self.assertNotIn('No black frames detected.',result.stdout)


if __name__ == '__main__':
    unittest.main()
