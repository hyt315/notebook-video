import React,{useEffect,useRef,useState} from 'react';
import {AbsoluteFill,Composition,Easing,Sequence,cancelRender,continueRender,delayRender,interpolate,registerRoot,spring,staticFile,useCurrentFrame as useRawCurrentFrame} from 'remotion';
import {Audio} from '@remotion/media';
import cueData from './caption-cues.json';

// ============================================================================
// LECTURE TEMPLATE · 讲课式默认模板（纯代码 SVG，不依赖任何生图能力）
//
// 本文件分三层，改写时只碰第三层：
//   第一层 LOCKED：美学核心 + 字幕/背景/章节条/资产门，一律不改。
//   第二层 组件库：Paper、LineIcon、CheckBadge、Mascot、StepRail 等，
//            直接复用；需要新图形时仿照它们的写法新增组件。
//   第三层 场景内容：COPY、SCENE 边界、各 Scene* 组件、Sound 音效表，
//            换题材时重写这一层。
//
// 帧号来源（机械流程，照做即可）：
//   1. 先跑 TTS 适配器拿到 audio/narration.mp3.json，再用官方
//      build-semantic-captions 生成 manifests/caption-cues.json。
//   2. 打印每条 cue 的帧区间：round(start_ms*30/1000) 到
//      round(speech_end_ms*30/1000)。
//   3. 场景边界 = 每章首条 cue 的起始帧；元素出现帧 = 对应台词的起始帧
//      减去场景起始帧（场景内部用本地帧 l）。说到哪，亮到哪。
//
// 画面组织六规范见 references/lecture-composition.md。
// ============================================================================

// Keep authored scene time separate from delivery frames.
const BASE_FPS=30,FPS=30,MOTION_FPS=30,TIMELINE_SCALE=1,DURATION=900,DESIGN_SCALE=4/3;
const useCurrentFrame=()=>useRawCurrentFrame()*BASE_FPS/FPS/TIMELINE_SCALE;
const deliveryFrame=(designFrame:number)=>Math.round(designFrame*FPS*TIMELINE_SCALE/BASE_FPS);

// LOCKED AESTHETIC CORE: ordinary production runs must not edit this block.
const C={ink:'#2b2924',muted:'#746956',blue:'#2869b7',orange:'#ed5a32',green:'#43866a',gold:'#d2a128',red:'#bd4b3d',navy:'#2d3b4c',paper:'#fffdf7',paperWarm:'#f7ecd8',paperBase:'#f3e4c4',line:'#514a40',white:'#fff'};
const TYPE={displayXL:58,displayL:50,displayML:45,displayM:43,displayS:36,displayXS:34,titleXL:32,titleL:30,titleM:28,titleS:27,titleXS:26,bodyL:26,bodyM:24,bodyS:23,labelL:22,labelM:21,labelS:20,microL:18,microS:16,subtitle:40};
const AESTHETIC={subtitleSafeWidth:1334,paperRadius:12,paperOutline:1.6,textureOpacity:.026,gridOpacity:.09,gradeWarmth:.055,gradeVignette:.06};

// EDITABLE CONTENT SURFACE — 换题材时从这里开始改
const COPY={
  chapterTitles:['代码不再孤独','第一步 · 参与','发布与运营','三个AI技能'],
  chromeKicker:'GITHUB 新手三部曲',
  header:'开源之路 / OPEN SOURCE',
  headerSub:'CONTRIBUTE · PREP · OPS / EP0',
} as const;

const clamp={extrapolateLeft:'clamp' as const,extrapolateRight:'clamp' as const};
const msFrame=(ms:number)=>Math.round(ms*FPS/1000);
const captions=((cueData as any).cues as any[]).map(c=>({...c,startFrame:msFrame(c.start_ms),endFrame:msFrame(c.speech_end_ms),words:c.words.map((w:any)=>({...w,startFrame:msFrame(w.start),endFrame:msFrame(w.end)}))}));
const q=(f:number)=>{const step=BASE_FPS/MOTION_FPS;return Math.floor(f/step)*step};
const ease=(f:number,a:number,b:number,from=0,to=1)=>interpolate(f,[a,b],[from,to],{...clamp,easing:Easing.inOut(Easing.cubic)});
const pop=(f:number,start:number,stiffness=120)=>spring({frame:f-start,fps:BASE_FPS,config:{damping:15,stiffness,mass:.76}});
const paperShadow=(lift:number)=>`${4+14*lift}px ${6+20*lift}px ${1+20*lift}px rgba(61,47,33,${.27-.13*lift}),0 ${12+30*lift}px ${22+34*lift}px rgba(49,35,22,${.105+.025*lift}),inset 0 1px 0 rgba(255,255,255,.72)`;

const preloadAudio=(src:string)=>new Promise<void>((resolve,reject)=>{const audio=new window.Audio(staticFile(src));audio.oncanplaythrough=()=>resolve();audio.onerror=()=>reject(new Error(`Required audio failed to load: ${src}`));audio.load()});
const AssetGate=()=>{const [handle]=useState(()=>delayRender('waiting for fonts and audio assets',{timeoutInMilliseconds:60000}));useEffect(()=>{let live=true;Promise.all([document.fonts.load('400 40px SourceHan'),document.fonts.load('700 40px SourceHan'),document.fonts.load('400 40px Smiley'),document.fonts.ready,...['narration.mp3','sfx/paper-rustle.wav','sfx/paper-tap.wav','sfx/data-whoosh.wav','sfx/chime.wav'].map(preloadAudio)]).then(()=>{if(live)continueRender(handle)}).catch(error=>{if(live)cancelRender(error)});return()=>{live=false}},[handle]);return null};

// Non-visual QA gate: measure every full cue with the real loaded font.
const CaptionFitGate=()=>{const ref=useRef<HTMLDivElement>(null),[done,setDone]=useState(false),[handle]=useState(()=>delayRender('measuring subtitle width',{timeoutInMilliseconds:60000}));useEffect(()=>{let live=true;Promise.all([document.fonts.load('400 40px SourceHan'),document.fonts.ready]).then(()=>requestAnimationFrame(()=>{if(!live)return;if(!ref.current){cancelRender(new Error('Subtitle measurement node is unavailable'));return}const rows=[...ref.current.querySelectorAll<HTMLElement>('[data-caption-fit]')];const overflow=rows.map((row,index)=>({index,width:row.getBoundingClientRect().width/DESIGN_SCALE,text:row.textContent||''})).filter(row=>row.width>AESTHETIC.subtitleSafeWidth+.5);if(overflow.length){cancelRender(new Error(`Subtitle overflow: ${overflow.map(x=>`#${x.index+1} ${Math.ceil(x.width)}px ${x.text}`).join(' | ')}`));return}setDone(true);continueRender(handle)})).catch(error=>{if(live)cancelRender(error)});return()=>{live=false}},[handle]);if(done)return null;return <div ref={ref} style={{position:'absolute',left:-10000,top:-10000,visibility:'hidden',fontFamily:'SourceHan,sans-serif',fontSize:40,fontWeight:400,whiteSpace:'nowrap'}}>{captions.map((cue:any,index:number)=><span key={index} data-caption-fit style={{display:'block',width:'max-content'}}>{String(cue.text).replace(/[，。！？；：、,.!?;:\s]+$/g,'')}</span>)}</div>};

const Fonts=()=> <style>{`
@font-face{font-family:SourceHan;src:url(${staticFile('SourceHanSansCN-Regular.otf')}) format('opentype');font-weight:400}
@font-face{font-family:SourceHan;src:url(${staticFile('SourceHanSansCN-Bold.otf')}) format('opentype');font-weight:700}
@font-face{font-family:Smiley;src:url(${staticFile('SmileySans-Oblique.otf')}) format('opentype')}
*{box-sizing:border-box}html,body{margin:0;background:${C.paperBase}}body{-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}
`}</style>;

const Background=()=> <>
  <AbsoluteFill style={{background:'radial-gradient(circle at 18% 10%,#fff9e7 0,#eeddbb 44%,#c89f6b 82%,#a57a4f 100%)'}}/>
  <div style={{position:'absolute',left:42,top:28,right:42,bottom:28,background:C.paperBase,border:'1.7px solid rgba(73,60,43,.40)',boxShadow:'22px 27px 0 rgba(75,57,38,.25),0 56px 104px rgba(42,25,12,.23),inset 0 1px 0 rgba(255,255,255,.42)'}}/>
  <div style={{position:'absolute',left:72,top:58,right:72,bottom:60,border:'1px solid rgba(90,72,48,.22)',backgroundImage:`repeating-linear-gradient(0deg,transparent 0 53px,rgba(94,74,50,${AESTHETIC.gridOpacity}) 54px),repeating-linear-gradient(90deg,transparent 0 53px,rgba(94,74,50,${AESTHETIC.gridOpacity}) 54px),radial-gradient(circle at 22% 8%,rgba(255,255,255,.28),transparent 42%)`}}/>
  <AbsoluteFill style={{opacity:AESTHETIC.textureOpacity,mixBlendMode:'multiply',backgroundImage:'radial-gradient(#3d2e1f 0.58px,transparent .75px)',backgroundSize:'7px 7px'}}/>
</>;

// ---- 可复用组件库（直接拿去用） -------------------------------------------
// Paper：手账纸片卡。万能容器；用 borderColor 区分语义色，lift 控制悬浮阴影。
const Paper:React.FC<{children:React.ReactNode,style?:React.CSSProperties,lift?:number}>=({children,style,lift=0})=><div style={{position:'absolute',backgroundColor:C.paper,backgroundImage:'radial-gradient(circle at 18% 9%,rgba(255,255,255,.78),transparent 34%),repeating-linear-gradient(0deg,rgba(89,67,42,.015) 0 1px,transparent 1px 4px),linear-gradient(155deg,#fffef9,#f7ead3)',border:`${AESTHETIC.paperOutline}px solid ${C.line}`,borderRadius:AESTHETIC.paperRadius,color:C.ink,boxShadow:paperShadow(lift),...style}}>{children}</div>;

// LineIcon：线性图标集。新增图标时在 IconKind 加名字、在 svg 里加分支即可。
type IconKind='check'|'play'|'project'|'report';
const LineIcon:React.FC<{kind:IconKind,size?:number,color?:string,strokeWidth?:number}>=({kind,size=28,color='currentColor',strokeWidth=2.2})=>{const common={fill:'none',stroke:color,strokeWidth,strokeLinecap:'round' as const,strokeLinejoin:'round' as const};return <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">{kind==='check'&&<path {...common} d="M7 16.5l5.6 5.5L25 9.8"/>}{kind==='play'&&<><rect {...common} x="5" y="6" width="22" height="20" rx="3"/><path {...common} d="M13 11.5l8 4.5-8 4.5z"/></>}{kind==='project'&&<><rect {...common} x="6" y="7" width="20" height="18" rx="2.5"/><path {...common} d="M10 12h12M10 16h8M10 20h6"/></>}{kind==='report'&&<><path {...common} d="M9 5h10l5 5v17H9z"/><path {...common} d="M19 5v6h5M13 16h7M13 20h7"/></>}</svg>};
// CheckBadge：绿色对勾徽章，配合“清单逐条点亮”模式使用（on 时 pop 弹出）。
const CheckBadge:React.FC<{size?:number}>=({size=30})=><span style={{width:size,height:size,borderRadius:999,background:C.green,color:C.white,display:'inline-grid',placeItems:'center',flex:'0 0 auto'}}><LineIcon kind="check" size={size*.62} color={C.white} strokeWidth={2.7}/></span>;

// Mascot：系列吉祥物（代码绘制的 git 猫）。f 传本地帧可眨眼，wave 挥手。
// 这是“系列 IP 复用”的示例：同一频道的片子重复使用同一吉祥物与组件。
const Mascot:React.FC<{size?:number;f?:number;wave?:boolean}>=({size=180,f=0,wave=false})=>{const blink=(f%54)<3?0.12:1;const arm=wave?Math.sin(f*0.28)*20:6;return <svg width={size} height={size} viewBox="0 0 100 100" style={{overflow:'visible'}}>
  <ellipse cx={50} cy={92} rx={30} ry={5} fill="rgba(61,47,33,.18)"/>
  <path d="M23 32 L31 8 L46 26 Z" fill={C.paper} stroke={C.line} strokeWidth={2.4} strokeLinejoin="round"/>
  <path d="M77 32 L69 8 L54 26 Z" fill={C.paper} stroke={C.line} strokeWidth={2.4} strokeLinejoin="round"/>
  <rect x={17} y={22} width={66} height={62} rx={24} fill={C.paper} stroke={C.line} strokeWidth={2.6}/>
  <ellipse cx={38} cy={45} rx={5} ry={6.5*blink} fill={C.ink}/>
  <ellipse cx={62} cy={45} rx={5} ry={6.5*blink} fill={C.ink}/>
  <circle cx={40} cy={44} r={1.4} fill={C.white}/><circle cx={64} cy={44} r={1.4} fill={C.white}/>
  <path d="M45 55 Q50 60 55 55" fill="none" stroke={C.ink} strokeWidth={2.2} strokeLinecap="round"/>
  <circle cx={30} cy={56} r={4} fill="rgba(237,90,50,.28)"/><circle cx={70} cy={56} r={4} fill="rgba(237,90,50,.28)"/>
  <g><path d="M42 74 L58 68 M42 74 L58 80" fill="none" stroke={C.blue} strokeWidth={2.6}/><circle cx={42} cy={74} r={3.6} fill={C.orange}/><circle cx={58} cy={68} r={3.6} fill={C.green}/><circle cx={58} cy={80} r={3.6} fill={C.gold}/></g>
  <g transform={`rotate(${arm} 82 60)`}><circle cx={87} cy={52} r={7.5} fill={C.paper} stroke={C.line} strokeWidth={2.2}/></g>
</svg>};

const cleanTail=(s:string)=>s.replace(/[，。！？；：、,.!?;:\s]+$/g,'');
const Subtitle=()=>{const f=useRawCurrentFrame(),lead=Math.round(FPS*.06),hold=Math.round(FPS*.267);let cue=captions.find((c:any)=>f>=c.startFrame-lead&&f<=c.endFrame+hold);if(!cue)cue=[...captions].reverse().find((c:any)=>c.startFrame<=f);const full=cue?cleanTail(cue.text):'';const shown=cue?cleanTail(cue.words.filter((w:any)=>w.startFrame<=f+lead).map((w:any)=>w.part).join('')):'';return <div style={{position:'absolute',left:188,right:188,bottom:34,height:112,zIndex:200,background:C.paper,clipPath:'polygon(0 8%,3% 3%,6% 7%,9% 2%,12% 6%,15% 1%,18% 5%,21% 2%,24% 7%,27% 2%,30% 5%,33% 1%,36% 6%,39% 2%,42% 7%,45% 1%,48% 5%,51% 2%,54% 7%,57% 2%,60% 5%,63% 1%,66% 6%,69% 2%,72% 7%,75% 2%,78% 5%,81% 1%,84% 6%,87% 2%,90% 7%,93% 2%,96% 5%,100% 3%,100% 95%,97% 99%,94% 94%,91% 100%,88% 95%,85% 99%,82% 94%,79% 99%,76% 95%,73% 100%,70% 94%,67% 99%,64% 95%,61% 100%,58% 94%,55% 99%,52% 95%,49% 100%,46% 94%,43% 99%,40% 95%,37% 100%,34% 94%,31% 99%,28% 95%,25% 100%,22% 94%,19% 99%,16% 95%,13% 100%,10% 94%,7% 99%,4% 95%,0 98%)',filter:'drop-shadow(7px 8px 0 rgba(92,75,55,.22)) drop-shadow(0 14px 20px rgba(48,35,22,.14))',display:'grid',placeItems:'center',padding:'0 105px'}}>
  <div style={{position:'absolute',left:28,top:28,bottom:28,width:10,borderRadius:4,background:C.orange}}/>
  <div style={{width:AESTHETIC.subtitleSafeWidth,display:'grid',placeItems:'center',fontSize:TYPE.subtitle,lineHeight:1.18,letterSpacing:.1,whiteSpace:'nowrap'}}><span style={{position:'relative'}}><span style={{visibility:'hidden'}}>{full}</span><span style={{position:'absolute',left:0,top:0}}>{shown}</span></span></div>
  <div style={{position:'absolute',right:24,top:34,width:44,height:44,borderRadius:99,border:`3.5px solid ${C.blue}`,display:'grid',placeItems:'center'}}><div style={{width:15,height:15,borderRadius:99,background:C.blue,boxShadow:`0 0 15px rgba(40,105,183,.55)`}}/></div>
</div>};

const Chrome=()=>{const f=q(useCurrentFrame()),stage=f<205?0:f<377?1:f<571?2:3,starts=[0,205,377,571],local=f-starts[stage],p=pop(local,-8),titles=COPY.chapterTitles;return <>
  <Paper style={{left:92,top:74,width:392,height:82,zIndex:150,display:'flex',opacity:p,transform:`translateY(${14*(1-p)}px) scale(${.96+.04*p})`}}><div style={{width:72,background:C.orange,color:C.white,display:'grid',placeItems:'center',fontFamily:'Smiley',fontSize:31}}>{String(stage+1).padStart(2,'0')}</div><div style={{padding:'10px 16px'}}><div style={{fontSize:TYPE.microS,color:C.blue,fontWeight:700,letterSpacing:2}}>{COPY.chromeKicker}</div><div style={{fontSize:TYPE.titleS,fontWeight:700,marginTop:3}}>{titles[stage]}</div></div></Paper>
  <div style={{position:'absolute',right:88,top:70,zIndex:140,textAlign:'right'}}><div style={{fontSize:TYPE.labelM,fontWeight:700,letterSpacing:4,color:C.blue}}>{COPY.header}</div><div style={{fontSize:TYPE.microL,marginTop:7,color:C.muted}}>{COPY.headerSub}</div></div>
</>};

const stageFade=(f:number,start:number,end:number)=>ease(f,start,start+15)*ease(f,end-15,end,1,0);

// ---- 场景内容层（换题材时重写以下全部） -----------------------------------
// 每个场景的标准结构：多元素分区（讲解面板 + 图形演示区 + 清单/贴纸），
// 每个区域同一时刻只有一个主动作；所有时间常量都是“场景本地帧”，
// 来自对应台词的 cue 帧（见文件头部的机械流程）。

// SCENE 1 — code is lonely -> GitHub collaborative world
const NODES=[{x:250,y:150,c:C.orange,label:'仓库'},{x:930,y:120,c:C.gold,label:'Star'},{x:1000,y:360,c:C.green,label:'Fork'},{x:210,y:410,c:C.blue,label:'Issue'},{x:600,y:470,c:C.red,label:'PR'}];
const SceneWorld=()=>{const f=q(useCurrentFrame()),l=f,opacity=stageFade(f,-5,205);const dim=ease(l,58,92,1,.42);return <div style={{position:'absolute',inset:0,opacity}}>
  <Paper style={{left:120,top:300,width:330,height:250,zIndex:60,padding:'26px 28px',borderColor:C.muted,opacity:dim,transform:`translateY(${26*(1-pop(l,5))}px) scale(${.94+.06*pop(l,5)})`}}>
    <div style={{fontFamily:'Smiley',fontSize:TYPE.displayS,color:C.muted}}>本地硬盘</div>
    <div style={{fontSize:TYPE.bodyM,fontWeight:700,marginTop:8,color:C.muted}}>代码只躺在你电脑里</div>
    <div style={{position:'absolute',left:28,right:28,top:120,bottom:28}}>{[0,1,2,3].map(i=><div key={i} style={{height:12,margin:'11px 0',width:`${72-i*9}%`,background:'#cabfa8',borderRadius:4,opacity:pop(l,14+i*6)}}/>)}</div>
  </Paper>
  <div style={{position:'absolute',left:470,top:405,fontFamily:'Smiley',fontSize:70,color:C.orange,zIndex:75,opacity:ease(l,48,68),transform:`translateX(${-14*(1-ease(l,48,68))}px)`}}>→</div>
  <div style={{position:'absolute',left:600,top:200,width:1160,height:600,zIndex:72,opacity:pop(l,55),transform:`scale(${.86+.14*pop(l,55)})`,transformOrigin:'50% 50%'}}>
    <svg width={1160} height={600} viewBox="0 0 1160 600" style={{overflow:'visible'}}>
      <circle cx={580} cy={300} r={140} fill="#e9f1fc" stroke={C.blue} strokeWidth={4}/>
      <ellipse cx={580} cy={300} rx={56} ry={140} fill="none" stroke={C.blue} strokeWidth={2} opacity={.45}/>
      <ellipse cx={580} cy={300} rx={110} ry={140} fill="none" stroke={C.blue} strokeWidth={2} opacity={.3}/>
      <line x1={440} y1={300} x2={720} y2={300} stroke={C.blue} strokeWidth={2} opacity={.45}/>
      <path d="M520 250 q30 -26 66 -6 q34 -16 52 14 q-10 34 -48 26 q-30 20 -60 -8 q-16 -30 -10 -26" fill={C.green} opacity={.25}/>
      {NODES.map((n,i)=>{const app=ease(l,72+i*9,98+i*9);const mx=(580+n.x)/2,my=(300+n.y)/2-46;return <g key={i} opacity={app}>
        <path d={`M580 300 Q${mx} ${my} ${n.x} ${n.y}`} fill="none" stroke={n.c} strokeWidth={3} strokeDasharray="9 8" strokeDashoffset={-l*3}/>
        <g transform={`scale(${.6+.4*pop(l,74+i*9)})`} style={{transformBox:'fill-box',transformOrigin:'center'} as any}>
          <rect x={n.x-38} y={n.y-30} width={76} height={60} rx={9} fill={C.paper} stroke={n.c} strokeWidth={3}/>
          <rect x={n.x-38} y={n.y-30} width={76} height={16} rx={9} fill={n.c} opacity={.85}/>
        </g>
      </g>;})}
    </svg>
    {NODES.map((n,i)=><div key={i} style={{position:'absolute',left:n.x-38,top:n.y+6,width:76,textAlign:'center',fontFamily:'Smiley',fontSize:TYPE.bodyM,color:n.c,opacity:ease(l,84+i*9,104+i*9)}}>{n.label}</div>)}
    <div style={{position:'absolute',left:512,top:286,color:C.blue,fontSize:TYPE.microL,fontWeight:700}}>GitHub</div>
  </div>
  <div style={{position:'absolute',left:150,top:600,zIndex:96,opacity:ease(l,96,120),transform:`translateY(${20*(1-ease(l,96,120))}px)`}}><Mascot size={150} f={l} wave/></div>
  <Paper style={{left:560,top:748,width:840,height:86,zIndex:85,display:'grid',placeItems:'center',borderColor:C.green,opacity:ease(l,128,150),transform:`translateY(${18*(1-pop(l,128))}px)`}}><div style={{fontSize:TYPE.titleL,fontWeight:700}}>全世界的开发者，<span style={{color:C.green}}>一起造软件</span></div></Paper>
</div>};

// SCENE 2 — step one: contribute a PR
const StepRail:React.FC<{active:number;l:number;start:number}>=({active,l,start})=>{const steps=[['01','参与',C.orange],['02','发布',C.blue],['03','运营',C.green]] as const;return <div style={{position:'absolute',left:360,top:180,width:1200,height:72,zIndex:78,display:'flex',gap:26,justifyContent:'center'}}>{steps.map((s,i)=>{const on=i===active,p=pop(l,start+i*7);return <div key={s[0]} style={{width:360,height:70,display:'flex',alignItems:'center',gap:16,padding:'0 22px',background:on?C.paper:'#efe3ca',border:`${on?3:2}px solid ${on?s[2]:'#c7b696'}`,borderRadius:12,boxShadow:on?'6px 8px 0 rgba(63,49,35,.2)':'none',opacity:p,transform:`translateY(${16*(1-p)}px) scale(${on?1:.96})`}}><span style={{width:38,height:38,borderRadius:99,background:on?s[2]:'#c7b696',color:C.white,display:'grid',placeItems:'center',fontFamily:'Smiley',fontSize:22}}>{s[0]}</span><span style={{fontFamily:'Smiley',fontSize:TYPE.titleM,color:on?s[2]:C.muted}}>{s[1]}</span></div>;})}</div>;};
const SceneContribute=()=>{const f=q(useCurrentFrame()),l=f-205,opacity=stageFade(f,200,377);const t=ease(l,44,104);const merge=ease(l,96,124);const cardX=180+560*Math.min(1,t/0.72);const steps=['读懂项目规则','建立最小改动','提交你的 PR','通过 CI 与评审'];return <div style={{position:'absolute',inset:0,opacity}}>
  <StepRail active={0} l={l} start={6}/>
  <svg width="1920" height="1080" style={{position:'absolute',inset:0,zIndex:55}}>
    <path d="M150 560 H1080" fill="none" stroke="#c9b99e" strokeWidth={8}/>
    <path d="M150 700 H760 Q840 700 880 620 L910 566" fill="none" stroke={C.orange} strokeWidth={7} strokeDasharray="16 12" strokeDashoffset={-l*4} opacity={.9}/>
    <text x="150" y="540" fill={C.blue} fontFamily="Smiley" fontSize="30">main 主干</text>
    <text x="150" y="742" fill={C.orange} fontFamily="Smiley" fontSize="30">你的分支</text>
    <circle cx={910} cy={562} r={13} fill={merge>.4?C.green:'#c9b99e'} opacity={ease(l,90,110)}/>
  </svg>
  <Paper lift={Math.sin(Math.PI*t)*.5} style={{left:cardX,top:648,width:210,height:96,zIndex:96,padding:'16px 18px',borderColor:C.orange,opacity:ease(l,40,58)*ease(l,120,132,1,0),transform:`translateY(${-90*Math.sin(Math.PI*t)*(cardX<700?1:.4)}px)`}}><div style={{fontFamily:'Smiley',fontSize:TYPE.titleS,color:C.orange}}>你的修改</div><div style={{fontSize:TYPE.labelL,fontWeight:700,marginTop:6,color:C.muted}}>commit</div></Paper>
  <Paper lift={.4} style={{left:840,top:430,width:250,height:108,zIndex:94,padding:'16px 20px',borderColor:C.green,opacity:merge,transform:`scale(${.7+.3*pop(l,100)})`}}><div style={{display:'flex',alignItems:'center',gap:12}}><span style={{fontFamily:'Smiley',fontSize:TYPE.titleM,color:C.green}}>Pull Request</span></div><div style={{fontSize:TYPE.labelL,fontWeight:700,marginTop:8,color:C.muted}}>把改动交给项目</div><div style={{position:'absolute',right:16,top:16,transform:`scale(${pop(l,120)})`}}><CheckBadge size={30}/></div></Paper>
  <Paper style={{left:1180,top:300,width:580,height:430,zIndex:76,padding:'34px 40px',borderColor:C.blue,transform:`translateX(${40*(1-pop(l,10))}px)`,opacity:pop(l,10)}}>
    <div style={{fontFamily:'Smiley',fontSize:TYPE.displayS,color:C.blue}}>第一步：参与开源</div>
    <div style={{position:'absolute',left:40,right:40,top:120,bottom:96}}>{steps.map((s,i)=>{const p=pop(l,40+i*20);return <div key={s} style={{display:'flex',alignItems:'center',gap:16,height:56,marginBottom:12,opacity:p,transform:`translateX(${24*(1-p)}px)`}}><span style={{width:40,height:40,borderRadius:99,background:[C.orange,C.blue,C.green,C.gold][i],color:C.white,display:'grid',placeItems:'center',fontFamily:'Smiley',fontSize:20}}>{i+1}</span><span style={{fontSize:TYPE.titleXS,fontWeight:700}}>{s}</span></div>;})}</div>
    <div style={{position:'absolute',left:40,right:40,bottom:34,height:44,background:'#eadcc1',border:`2px solid ${C.green}`,borderRadius:10,display:'grid',placeItems:'center',fontFamily:'Smiley',fontSize:TYPE.bodyL,color:C.green,letterSpacing:1,opacity:ease(l,110,130)}}>github-oss-contribute</div>
  </Paper>
</div>};

// SCENE 3 — step two & three: prep and operate
const Module:React.FC<{name:string;color:string;l:number;start:number;fromX:number;toX:number;toY:number}>=({name,color,l,start,fromX,toX,toY})=>{const u=ease(l,start,start+44);const fade=ease(l,start+40,start+52,1,0);return <Paper lift={Math.sin(Math.PI*u)*.5} style={{left:fromX,top:250,width:190,height:56,zIndex:94,display:'grid',placeItems:'center',borderColor:color,opacity:ease(l,start,start+8)*fade,transform:`translate3d(${(toX-fromX)*u}px,${(toY-250)*u}px,0) scale(${1-.34*u})`}}><span style={{fontFamily:'Smiley',fontSize:TYPE.bodyL,color}}>{name}</span></Paper>;};
const Gauge:React.FC<{label:string;color:string;v:number;x:number}>=({label,color,v,x})=><div style={{position:'absolute',left:x,top:0,width:130,textAlign:'center'}}><svg width={110} height={70} viewBox="0 0 110 70"><path d="M12 62 A43 43 0 0 1 98 62" fill="none" stroke="#d6c6aa" strokeWidth={9} strokeLinecap="round"/><path d="M12 62 A43 43 0 0 1 98 62" fill="none" stroke={color} strokeWidth={9} strokeLinecap="round" strokeDasharray={135} strokeDashoffset={135*(1-v)}/></svg><div style={{fontSize:TYPE.labelL,fontWeight:700,marginTop:2,color:C.ink}}>{label}</div></div>;
const SceneShip=()=>{const f=q(useCurrentFrame()),l=f-377,opacity=stageFade(f,372,571);const ver=ease(l,150,180);const rocket=ease(l,150,192);const g1=ease(l,120,150),g2=ease(l,132,162),g3=ease(l,144,174);return <div style={{position:'absolute',inset:0,opacity}}>
  <Paper style={{left:120,top:250,width:560,height:470,zIndex:70,padding:'30px 34px',borderColor:C.orange,transform:`translateY(${26*(1-pop(l,6))}px) scale(${.95+.05*pop(l,6)})`,opacity:pop(l,6)}}>
    <div style={{fontFamily:'Smiley',fontSize:TYPE.displayS,color:C.orange}}>第二步：发布</div>
    <div style={{fontSize:TYPE.titleXS,fontWeight:700,marginTop:8,color:C.muted}}>整理成专业开源仓库</div>
    <div style={{position:'absolute',left:150,top:170,width:260,height:210,background:'#efe3ca',border:`3px solid ${C.orange}`,borderRadius:'10px 10px 0 0'}}><div style={{position:'absolute',left:-1,right:-1,top:-30,height:30,background:C.orange,clipPath:'polygon(0 100%,10% 0,90% 0,100% 100%)'}}/><div style={{padding:'16px'}}>{['README','LICENSE','CI'].map((m,i)=><div key={m} style={{height:40,margin:'10px 0',background:C.paper,border:`2px solid ${[C.blue,C.green,C.gold][i]}`,borderRadius:6,display:'grid',placeItems:'center',fontFamily:'Smiley',fontSize:TYPE.bodyM,opacity:ease(l,44+i*22,64+i*22)}}>{m}</div>)}</div></div>
    <div style={{position:'absolute',left:34,right:34,bottom:30,height:42,background:'#eadcc1',border:`2px solid ${C.orange}`,borderRadius:10,display:'grid',placeItems:'center',fontFamily:'Smiley',fontSize:TYPE.bodyM,color:C.orange,opacity:ease(l,96,116)}}>github-oss-prep</div>
  </Paper>
  <Module name="README" color={C.blue} l={l} start={40} fromX={470} toX={300} toY={430}/>
  <Module name="LICENSE" color={C.green} l={l} start={62} fromX={470} toX={300} toY={480}/>
  <Paper style={{left:740,top:250,width:1020,height:470,zIndex:72,padding:'30px 40px',borderColor:C.navy,transform:`translateY(${26*(1-pop(l,90))}px) scale(${.95+.05*pop(l,90)})`,opacity:pop(l,90)}}>
    <div style={{fontFamily:'Smiley',fontSize:TYPE.displayS,color:C.navy}}>第三步：运营</div>
    <div style={{fontSize:TYPE.titleXS,fontWeight:700,marginTop:8,color:C.muted}}>分流 · 审查 · 按时发版</div>
    <div style={{position:'absolute',left:60,top:150,right:60,height:120}}><Gauge label="Issue 分流" color={C.orange} v={g1} x={20}/><Gauge label="PR 审查" color={C.blue} v={g2} x={330}/><Gauge label="Release" color={C.green} v={g3} x={640}/></div>
    <div style={{position:'absolute',left:60,bottom:120,display:'flex',alignItems:'center',gap:20,opacity:ease(l,150,172)}}><span style={{fontFamily:'Smiley',fontSize:TYPE.titleL,color:C.muted}}>v1.0</span><span style={{fontFamily:'Smiley',fontSize:TYPE.titleL,color:C.orange}}>→</span><span style={{fontFamily:'Smiley',fontSize:TYPE.displayS,color:C.green,transform:`scale(${.7+.3*pop(l,152)})`,display:'inline-block'}}>v1.1</span></div>
    <svg width={120} height={160} style={{position:'absolute',right:70,bottom:60,transform:`translateY(${-150*rocket}px)`,opacity:ease(l,148,164)}} viewBox="0 0 120 160"><path d="M60 6 C86 40 86 88 60 120 C34 88 34 40 60 6 Z" fill={C.paper} stroke={C.red} strokeWidth={4}/><circle cx={60} cy={54} r={13} fill="#e9f1fc" stroke={C.blue} strokeWidth={3}/><path d="M40 96 L24 128 L44 116 Z" fill={C.orange} stroke={C.red} strokeWidth={3} strokeLinejoin="round"/><path d="M80 96 L96 128 L76 116 Z" fill={C.orange} stroke={C.red} strokeWidth={3} strokeLinejoin="round"/><path d="M50 120 q10 24 20 0" fill={C.gold} opacity={.9}/></svg>
    <div style={{position:'absolute',left:40,right:40,bottom:30,height:42,background:'#eadcc1',border:`2px solid ${C.navy}`,borderRadius:10,display:'grid',placeItems:'center',fontFamily:'Smiley',fontSize:TYPE.bodyM,color:C.navy,opacity:ease(l,158,178)}}>github-oss-ops</div>
  </Paper>
</div>};

// SCENE 4 — three AI skills + CTA
const SKILLS=[['github-oss-contribute','参与别人的项目','EP 1',C.orange],['github-oss-prep','发布自己的作品','EP 2',C.blue],['github-oss-ops','运营与持续发版','EP 3',C.green]] as const;
const SceneSkills=()=>{const f=q(useCurrentFrame()),l=f-571,opacity=ease(f,566,581);const cta=ease(l,180,214);return <div style={{position:'absolute',inset:0,opacity}}>
  <div style={{position:'absolute',left:860,top:214,zIndex:75,textAlign:'center',opacity:pop(l,6),transform:`scale(${.7+.3*pop(l,6)})`}}><Mascot size={150} f={l} wave/><div style={{fontFamily:'Smiley',fontSize:TYPE.titleM,color:C.navy,marginTop:2}}>AI AGENT</div></div>
  {SKILLS.map((s,i)=>{const p=pop(l,30+i*16);const x=200+i*530;return <Paper key={s[0]} lift={.25} style={{left:x,top:410,width:470,height:250,zIndex:94,padding:'28px 30px',borderColor:s[3],opacity:p,transform:`translateY(${34*(1-p)}px) scale(${.92+.08*p})`}}>
    <div style={{position:'absolute',right:24,top:22,fontFamily:'Smiley',fontSize:TYPE.titleM,color:s[3],opacity:ease(l,60+i*16,84+i*16)}}>{s[2]}</div>
    <div style={{width:56,height:56,borderRadius:14,background:s[3],display:'grid',placeItems:'center',color:C.white}}><LineIcon kind={['play','project','report'][i] as IconKind} size={34} color={C.white} strokeWidth={2.2}/></div>
    <div style={{fontFamily:'Smiley',fontSize:TYPE.titleM,color:s[3],marginTop:16}}>{s[0]}</div>
    <div style={{fontSize:TYPE.titleXS,fontWeight:700,marginTop:12}}>{s[1]}</div>
    <div style={{position:'absolute',left:30,bottom:24,display:'flex',alignItems:'center',gap:10,color:C.muted,fontSize:TYPE.labelL,fontWeight:700}}><CheckBadge size={26}/>智能体陪你走完</div>
  </Paper>;})}
  <Paper style={{left:460,top:724,width:1000,height:104,zIndex:96,display:'grid',placeItems:'center',borderColor:C.orange,opacity:cta,transform:`translateY(${22*(1-cta)}px) scale(${.96+.04*pop(l,182)})`}}><div style={{display:'flex',alignItems:'center',gap:22,fontFamily:'Smiley',fontSize:TYPE.displayS}}><span style={{color:C.muted,fontSize:TYPE.titleM}}>主页搜</span><span style={{color:C.orange}}>github.com/hyt315</span></div></Paper>
</div>};

const FinalDemo=()=>{const f=q(useCurrentFrame());return <>{f<205&&<SceneWorld/>}{f>=205&&f<377&&<SceneContribute/>}{f>=377&&f<571&&<SceneShip/>}{f>=571&&<SceneSkills/>}</>};

// Sound：声音也是声明式的——rustle=换章，whoosh=传输，tap=元素入场，chime=完成。
// 帧号同样来自 cue 表；只在画面上真正发生动作的帧放音效。
const Sound=()=> <>
  <Audio src={staticFile('narration.mp3')} volume={1}/>
  {[5,210,382,576].map(f=><Sequence key={`r${f}`} from={deliveryFrame(f)} layout="none"><Audio src={staticFile('sfx/paper-rustle.wav')} volume={.13}/></Sequence>)}
  {[60,300,527].map(f=><Sequence key={`w${f}`} from={deliveryFrame(f)} layout="none"><Audio src={staticFile('sfx/data-whoosh.wav')} volume={.12}/></Sequence>)}
  {[20,90,235,300,417,439,461,601,617,633].map(f=><Sequence key={`t${f}`} from={deliveryFrame(f)} layout="none"><Audio src={staticFile('sfx/paper-tap.wav')} volume={.15}/></Sequence>)}
  {[150,325,540,765].map(f=><Sequence key={`c${f}`} from={deliveryFrame(f)} layout="none"><Audio src={staticFile('sfx/chime.wav')} volume={.18}/></Sequence>)}
</>;

const Grade=()=> <AbsoluteFill style={{pointerEvents:'none',zIndex:190}}><AbsoluteFill style={{opacity:AESTHETIC.gradeWarmth,mixBlendMode:'soft-light',background:'radial-gradient(circle at 24% 8%,rgba(255,249,224,.9),transparent 48%),linear-gradient(180deg,rgba(255,244,216,.14),rgba(84,55,28,.08))'}}/><AbsoluteFill style={{boxShadow:`inset 0 0 150px rgba(66,42,22,${AESTHETIC.gradeVignette})`}}/></AbsoluteFill>;
const Film=()=> <AbsoluteFill style={{overflow:'hidden',background:C.paperBase}}><div style={{position:'absolute',left:0,top:0,width:1920,height:1080,transform:'scale(1.3333333333)',transformOrigin:'0 0',fontFamily:'SourceHan,sans-serif',color:C.ink,overflow:'hidden'}}><Fonts/><AssetGate/><CaptionFitGate/><Sound/><Background/><FinalDemo/><Chrome/><Grade/><Subtitle/></div></AbsoluteFill>;
const Root=()=> <Composition id="NotebookVideoFilm" component={Film} durationInFrames={DURATION} fps={FPS} width={2560} height={1440}/>;
registerRoot(Root);
