#!/usr/bin/env python3
"""Real-browser smoke tests. Uses synthetic media, never calls a speech/image API.

Usage: python scripts/render-smoke.py WORK_DIRECTORY [--browser PATH] [--video]
WORK_DIRECTORY must be empty and outside this repository. Outputs are retained.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zlib

ROOT=Path(__file__).resolve().parents[1]


def png_fixture(path):
    width,height=3840,1920
    rows=[]
    for y in range(height):
        row=bytearray([0]); py=y/6
        for x in range(width):
            px=x/6
            color=(248,239,218)
            if int(px)%40==0 or int(py)%40==0: color=(231,222,201)
            if 144<py<156 and 85<px<555: color=(40,105,183)
            for cx,cy in [(105,150),(285,150),(465,150)]:
                if abs(px-cx)<45 and abs(py-cy)<45: color=(255,253,247)
                if abs(px-cx)<36 and abs(py-cy)<36: color=(40,105,183) if cx!=465 else (210,161,40)
            row.extend(color)
        rows.append(bytes(row))
    def chunk(kind,data):
        return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b''))


SMOKE_SOURCE=r"""import React from 'react';
import {AbsoluteFill,Composition,Img,registerRoot,staticFile,useCurrentFrame} from 'remotion';
import {EvidenceBridge} from './recipes/EvidenceBridge';
import {EvidenceZoom,FitCard,KenBurnsImg} from './fxkit';
import {CardFitGate} from './layout-gate';
import {THEME} from './theme/active';
const Demo=()=>{const f=useCurrentFrame();return <AbsoluteFill style={{background:THEME.palette.paperBase}}><div style={{position:'absolute',width:1920,height:1080,transform:'scale(1.3333333333)',transformOrigin:'0 0',fontFamily:'Kai',color:THEME.palette.ink}}>
<style>{`@font-face{font-family:Kai;src:url(${staticFile('LXGWWenKaiLite-Regular.ttf')})}*{box-sizing:border-box}`}</style>
<CardFitGate/><THEME.Background/>
<div style={{position:'absolute',left:180,top:74,fontSize:38}}>整体 → 定位细节 → 回到解释</div>
<div style={{position:'absolute',right:180,top:140,fontSize:22}}>代码绘制的测试插图 · 非真实测量数据</div>
<div style={{position:'absolute',left:180,top:240}}><EvidenceBridge src="illustrations/smoke.png" label="同一个节点，成为解释的证据" width={1560} height={660} inset={{x:980,y:60,scale:.36}} beats={{expand:60,focus:96,conclude:160,return:240}} fx={.73} fy={.47}>
<div style={{position:'absolute',left:30,top:20,fontSize:46}}>{f<240?'先建立整体关系':'细节回到同一条解释'}</div>
<svg width={900} height={400} style={{position:'absolute',left:0,top:100}}><path d="M150 200 H750" stroke={THEME.palette.blue} strokeWidth={8}/>{[150,450,750].map((x,i)=><g key={i}><circle cx={x} cy={200} r={65} fill={i===2?THEME.palette.gold:THEME.palette.blue}/><text x={x} y={210} fontSize={28} textAnchor="middle" fill="white">{['输入','处理','结果'][i]}</text></g>)}</svg>
<FitCard x={30} y={460} w={800} h={110} frame={f} start={0} exitStart={350}><div style={{fontSize:28}}>主视觉解释关系，辅助图片补充可观察的细节</div></FitCard>
</EvidenceBridge></div>
<div style={{position:'absolute',bottom:50,left:180,right:180,textAlign:'center',fontSize:32}}>{f<60?'先看结构，再看局部':f<240?'图片接过注意力，字幕和画布保持稳定':'不改变音频时间轴，也不堆叠新页面'}</div>
</div></AbsoluteFill>};
const Missing=()=> <EvidenceZoom src="missing-image.png" frame={160}/>;
const Overflow=()=> <><CardFitGate/><div data-fit-card style={{position:'absolute',width:200,height:80,border:'2px solid black',background:'white'}}><div style={{position:'absolute',left:10,top:100}}>overflow fixture</div></div></>;
const Root=()=> <><Composition id="EvidenceBridgeDemo" component={Demo} width={2560} height={1440} fps={30} durationInFrames={360}/><Composition id="MissingImage" component={Missing} width={640} height={360} fps={30} durationInFrames={1}/><Composition id="Overflow" component={Overflow} width={640} height={360} fps={30} durationInFrames={1}/></>;
registerRoot(Root);
"""


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('work',type=Path);parser.add_argument('--browser');parser.add_argument('--video',action='store_true')
    args=parser.parse_args(); work=args.work.resolve()
    if work.is_relative_to(ROOT) or (work.exists() and any(work.iterdir())):
        raise SystemExit('Work directory must be empty and outside the repository')
    work.mkdir(parents=True,exist_ok=True)
    project=work/'lecture'
    shutil.copytree(ROOT/'assets/lecture-template',project)
    npm=['npm'] if os.name!='nt' else ['node',str(Path(shutil.which('node')).parent/'node_modules/npm/bin/npm-cli.js')]
    subprocess.run([*npm,'ci','--no-audit','--no-fund'],cwd=project,check=True)
    (project/'public/illustrations').mkdir(exist_ok=True)
    png_fixture(project/'public/illustrations/smoke.png')
    (project/'src/smoke.tsx').write_text(SMOKE_SOURCE,encoding='utf-8')
    subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','37.54','-ac','2',str(project/'public/narration.mp3')],check=True)
    cli=project/'node_modules/@remotion/cli/remotion-cli.js'
    subprocess.run(['node','-e',r"""
const assert=require('node:assert/strict'),esbuild=require('esbuild');
for(const name of ['image-focus','process-path']) esbuild.buildSync({entryPoints:[`src/${name}.ts`],bundle:true,platform:'node',format:'cjs',outfile:`${name}.cjs`,logLevel:'silent'});
const {focusTransform}=require('./image-focus.cjs');
for(const fx of [0,.1,.5,.9,1]) for(const fy of [0,.5,1]) for(let n=0;n<=100;n++){
 const r=focusTransform(900,500,fx,fy,1.8,n/100);
 assert(r.x<=0&&r.y<=0&&r.x+900*r.scale>=900-1e-8&&r.y+500*r.scale>=500-1e-8);
 if(n===0) assert.deepEqual([r.x,r.y,r.scale],[0,0,1]);
}
assert.throws(()=>focusTransform(900,500,.5,.5,.5,1));
const {followBranch}=require('./process-path.cjs');
const r={start:{x:260,y:700},knee:{x:760,y:700},control:{x:840,y:700},turn:{x:880,y:620},end:{x:910,y:560}};
for(const [p,want] of [[0,r.start],[.72,r.knee],[.92,r.turn],[1,r.end]]){
 const got=followBranch(r,p);assert(Math.abs(got.x-want.x)<1e-8&&Math.abs(got.y-want.y)<1e-8);
}
console.log('PASS image focus bounds and shared path endpoints');
"""],cwd=project,check=True)
    browser=args.browser or os.environ.get('REMOTION_BROWSER_EXECUTABLE')
    reports=[]
    def render(name,comp,entry='src/index.tsx',frame=950,expect=None,video=False):
        out=work/(name+('.mp4' if video else '.png'))
        cmd=['node',str(cli),'render' if video else 'still',entry,comp,str(out),'--concurrency=2']
        cmd+=['--codec=h264'] if video else [f'--frame={frame}']
        if browser: cmd+=['--browser-executable='+browser]
        result=subprocess.run(cmd,cwd=project,capture_output=True,text=True)
        log=result.stdout+result.stderr
        (work/(name+'.log')).write_text(log,encoding='utf-8')
        passed=(result.returncode!=0 and expect in log) if expect else (result.returncode==0 and out.is_file() and out.stat().st_size>0)
        reports.append({'case':name,'passed':passed,'expected_error':expect})
        print(('PASS ' if passed else 'FAIL ')+name,flush=True)
        if not passed: print(log[-5000:]); raise RuntimeError(name)
    active=project/'src/theme/active.ts'
    for theme in ['paper','cel','sticker','flat']:
        active.write_text(f"import {{THEME}} from './{theme}';\nexport {{THEME}};\n")
        for canvas,comp in [('169','NotebookVideoFilm'),('43','NotebookVideoFilm-4x3'),('34','NotebookVideoFilm-3x4')]:
            render(f'{theme}-{canvas}',comp)
        render(f'{theme}-fxkit','EvidenceBridgeDemo','src/smoke.tsx',175)
    active.write_text("import {THEME} from './paper';\nexport {THEME};\n")
    render('paper-fxkit-repeat','EvidenceBridgeDemo','src/smoke.tsx',175)
    if (work/'paper-fxkit-repeat.png').read_bytes() != (work/'paper-fxkit.png').read_bytes():
        raise RuntimeError('Repeated frame differs: deterministic rendering regression')
    manifest=json.loads((project/'manifests/asset-manifest.json').read_text())
    boundaries={0,manifest['duration_frames']-1}
    for scene in manifest['scenes'][1:]: boundaries.update([scene['start_frame']-1,scene['start_frame']])
    for frame in sorted(boundaries):
        render(f'boundary-{frame}','NotebookVideoFilm',frame=frame)
    render('missing-image','MissingImage','src/smoke.tsx',0,'Error loading image')
    render('overflow','Overflow','src/smoke.tsx',0,'Card overflow')
    cues=project/'src/caption-cues.json'; original=cues.read_text(encoding='utf-8')
    data=json.loads(original);data['cues'][0]['text']='测试字幕宽度'*5
    cues.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
    try:
        render('portrait-caption-overflow','NotebookVideoFilm-3x4',frame=0,expect='Subtitle overflow')
        render('four-three-caption-overflow','NotebookVideoFilm-4x3',frame=0,expect='Subtitle overflow')
    finally: cues.write_text(original,encoding='utf-8')
    if args.video: render('evidence-bridge','EvidenceBridgeDemo','src/smoke.tsx',video=True)
    narration=project/'public/narration.mp3'
    project=work/'classic'
    shutil.copytree(ROOT/'assets/example-project',project)
    shutil.copyfile(narration,project/'public/narration.mp3')
    subprocess.run([*npm,'ci','--no-audit','--no-fund'],cwd=project,check=True)
    cli=project/'node_modules/@remotion/cli/remotion-cli.js'
    render('classic-template','NotebookVideoFilm',frame=290)
    (work/'results.json').write_text(json.dumps(reports,indent=2)+'\n')
    print(f'{len(reports)} real-browser checks passed; synthetic audio/image fixtures only. Results: {work}')


if __name__=='__main__': main()
