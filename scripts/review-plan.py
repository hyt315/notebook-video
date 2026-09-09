#!/usr/bin/env python3
"""Build a deterministic, boundary-aware review list without rendering."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def review_plan(manifest, cues):
    duration=manifest['duration_frames']
    frames={0:'opening',min(45,duration-1):'opening claim',duration-1:'final hold'}
    for scene in manifest['scenes']:
        start,end=scene['start_frame'],scene['end_frame']
        for frame in [max(0,start-1),start,min(end-1,start+12),end-1]:
            frames[frame]=f"scene boundary: {scene['id']}"
        for beat in scene.get('beats',[]):
            frames[beat['frame']]=beat['action']
    if cues:
        longest=max(cues,key=lambda c:len(c['text']))
        frame=min(duration-1,int(longest['speech_end_ms']*30/1000+.5)-1)
        frames[max(0,frame)]='longest caption (character-count candidate; browser fit remains authoritative)'
    ranges=[]
    for frame in sorted(frames):
        start,end=max(0,frame-12),min(duration-1,frame+12)
        if ranges and start<=ranges[-1][1]+1: ranges[-1][1]=max(ranges[-1][1],end)
        else: ranges.append([start,end])
    return {'fps':30,'duration_frames':duration,'range_end_inclusive':True,
            'frames':[{'frame':f,'reason':frames[f]} for f in sorted(frames)],'ranges':ranges,
            'manual_checks':['blank content on nonblack background','transformed clipping/occlusion','speech alignment','meaningful action and continuity']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();p=args.project.resolve()
    subprocess.run([sys.executable,str(Path(__file__).with_name('validate-visual-plan.py')),str(p)],check=True)
    manifest=json.loads((p/'manifests/asset-manifest.json').read_text(encoding='utf-8'))
    cues=json.loads((p/'manifests/caption-cues.json').read_text(encoding='utf-8'))['cues']
    result=review_plan(manifest,cues)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"Review plan: {args.output} ({len(result['frames'])} key frames, {len(result['ranges'])} ranges)")


if __name__=='__main__': main()
