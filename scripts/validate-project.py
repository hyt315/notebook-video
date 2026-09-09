#!/usr/bin/env python3
"""Run data gates together before spending time on a browser render."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('project',type=Path)
    args=parser.parse_args()
    p=args.project.resolve(); scripts=Path(__file__).resolve().parent
    gates=[('validate-visual-plan.py',[p]),('validate-layering.py',[p/'manifests/asset-manifest.json']),
           ('validate-caption-sync.py',[p/'audio/narration.mp3.json',p/'manifests/caption-cues.json']),
           ('validate-semantic-breaks.py',[p/'manifests/caption-cues.json',p/'manifests/protected-caption-phrases.txt'])]
    for script,paths in gates:
        subprocess.run([sys.executable,str(scripts/script),*map(str,paths)],check=True)
    manifest=json.loads((p/'manifests/asset-manifest.json').read_text(encoding='utf-8'))
    words=json.loads((p/'audio/narration.mp3.json').read_text(encoding='utf-8'))
    if manifest['duration_frames'] < int(words[-1]['end']*30/1000+.5)+21:
        raise SystemExit('ERROR: leave at least 21 frames (0.7s at 30fps) after the last spoken word')
    timing=p/'manifests/tts-segments.json'
    if timing.exists() and json.loads(timing.read_text(encoding='utf-8')).get('timing_quality')=='estimated-character':
        print('REVIEW REQUIRED: character timing is estimated; listen before claiming word-level alignment')
    print('Project data gates passed. Browser geometry, actual audio and narrative review are still required.')


if __name__=='__main__':
    main()
