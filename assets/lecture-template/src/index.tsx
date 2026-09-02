import React,{useEffect,useRef,useState} from 'react';
import {AbsoluteFill,Composition,Easing,Sequence,cancelRender,continueRender,delayRender,interpolate,interpolateColors,registerRoot,spring,staticFile,useCurrentFrame as useRawCurrentFrame} from 'remotion';
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
const BASE_FPS=30,FPS=30,MOTION_FPS=30,TIMELINE_SCALE=1,DURATION=1126,DESIGN_SCALE=4/3;
// Canvas switch: pick the delivery canvas of this production.
// '16:9' landscape players (default) / '4:3' taller mobile landscape / '3:4' portrait feeds.
// The template ships all three layouts; the portrait set uses *P scenes (single-column stacking).
const CANVAS='16:9' as const;
const MODES={'16:9':{compW:2560,compH:1440,designW:1920,designH:1080,subMar:188,subBottom:34,subH:112,safe:1334,subFont:44},'4:3':{compW:1920,compH:1440,designW:1440,designH:1080,subMar:60,subBottom:34,subH:112,safe:1060,subFont:44},'3:4':{compW:1440,compH:1920,designW:1080,designH:1440,subMar:50,subBottom:40,subH:104,safe:900,subFont:40}} as const;
const MODE=MODES[CANVAS],isPortrait=CANVAS==='3:4';
const useCurrentFrame=()=>useRawCurrentFrame()*BASE_FPS/FPS/TIMELINE_SCALE;
const deliveryFrame=(designFrame:number)=>Math.round(designFrame*FPS*TIMELINE_SCALE/BASE_FPS);

// LOCKED AESTHETIC CORE: ordinary production runs must not edit this block.
const C={ink:'#2b2924',muted:'#8a7a63',blue:'#2869b7',orange:'#ed5a32',green:'#43866a',gold:'#d2a128',red:'#bd4b3d',navy:'#2d3b4c',paper:'#fffef9',paperWarm:'#f8f2e5',paperBase:'#f5efe3',line:'#554e42',white:'#fff'};
const TYPE={displayXL:58,displayL:50,displayML:45,displayM:43,displayS:36,displayXS:34,titleXL:32,titleL:30,titleM:28,titleS:27,titleXS:26,bodyL:26,bodyM:24,bodyS:23,labelL:22,labelM:21,labelS:20,microL:18,microS:16,subtitle:MODE.subFont};
const AESTHETIC={subtitleSafeWidth:MODE.safe,paperRadius:14,paperOutline:1.1,textureOpacity:.018,gridOpacity:.05,gradeWarmth:.028,gradeVignette:.045};

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
const easeOutSoft=(f:number,a:number,b:number,from=0,to=1)=>interpolate(f,[a,b],[from,to],{...clamp,easing:Easing.bezier(.16,1,.3,1)});
const pop=(f:number,start:number,stiffness=132)=>spring({frame:f-start,fps:BASE_FPS,config:{damping:17,stiffness,mass:.86}});
const paperShadow=(lift:number)=>`0 1px 2px rgba(61,47,33,.10),0 ${6+10*lift}px ${16+18*lift}px rgba(61,47,33,${.08+.10*lift}),0 ${18+26*lift}px ${30+34*lift}px rgba(49,35,22,${.06+.08*lift}),inset 0 1px 0 rgba(255,255,255,.7)`;

const AssetGate=()=>{const [handle]=useState(()=>delayRender('waiting for fonts',{timeoutInMilliseconds:120000}));useEffect(()=>{let live=true;Promise.all([document.fonts.load('400 40px Kai'),document.fonts.load('700 40px Kai'),document.fonts.load('600 40px Clash'),document.fonts.load('500 40px Space'),document.fonts.ready]).then(()=>{if(live)continueRender(handle)}).catch(error=>{if(live)cancelRender(error)});return()=>{live=false}},[handle]);return null};

// Non-visual QA gate: measure every full cue with the real loaded font.
const CaptionFitGate=()=>{const ref=useRef<HTMLDivElement>(null),[done,setDone]=useState(false),[handle]=useState(()=>delayRender('measuring subtitle width',{timeoutInMilliseconds:60000}));useEffect(()=>{let live=true;Promise.all([document.fonts.load('400 40px Kai'),document.fonts.ready]).then(()=>requestAnimationFrame(()=>{if(!live)return;if(!ref.current){cancelRender(new Error('Subtitle measurement node is unavailable'));return}const rows=[...ref.current.querySelectorAll<HTMLElement>('[data-caption-fit]')];const overflow=rows.map((row,index)=>({index,width:row.getBoundingClientRect().width/DESIGN_SCALE,text:row.textContent||''})).filter(row=>row.width>AESTHETIC.subtitleSafeWidth+.5);if(overflow.length){cancelRender(new Error(`Subtitle overflow: ${overflow.map(x=>`#${x.index+1} ${Math.ceil(x.width)}px ${x.text}`).join(' | ')}`));return}setDone(true);continueRender(handle)})).catch(error=>{if(live)cancelRender(error)});return()=>{live=false}},[handle]);if(done)return null;return <div ref={ref} style={{position:'absolute',left:-10000,top:-10000,visibility:'hidden',fontFamily:'Kai,sans-serif',fontSize:MODE.subFont,fontWeight:400,whiteSpace:'nowrap',letterSpacing:1.2}}>{captions.map((cue:any,index:number)=><span key={index} data-caption-fit style={{display:'block',width:'max-content'}}>{String(cue.text).replace(/[，。！？；：、,.!?;:\s]+$/g,'')}</span>)}</div>};

const Fonts=()=> <style>{`
@font-face{font-family:Kai;src:url(${staticFile('LXGWWenKaiLite-Regular.ttf')}) format('truetype');font-weight:400}
@font-face{font-family:Kai;src:url(${staticFile('LXGWWenKaiLite-Medium.ttf')}) format('truetype');font-weight:700}
@font-face{font-family:Clash;src:url(${staticFile('fonts/ClashDisplay-Medium.woff2')}) format('woff2');font-weight:500}
@font-face{font-family:Clash;src:url(${staticFile('fonts/ClashDisplay-Semibold.woff2')}) format('woff2');font-weight:600}
@font-face{font-family:Clash;src:url(${staticFile('fonts/ClashDisplay-Bold.woff2')}) format('woff2');font-weight:700}
@font-face{font-family:Space;src:url(${staticFile('fonts/SpaceGrotesk-Latin.woff2')}) format('woff2');font-weight:400}
@font-face{font-family:Space;src:url(${staticFile('fonts/SpaceGrotesk-Latin.woff2')}) format('woff2');font-weight:500}
@font-face{font-family:Space;src:url(${staticFile('fonts/SpaceGrotesk-Latin.woff2')}) format('woff2');font-weight:600}
@font-face{font-family:Space;src:url(${staticFile('fonts/SpaceGrotesk-Latin.woff2')}) format('woff2');font-weight:700}
*{box-sizing:border-box}html,body{margin:0;background:${C.paperBase}}body{font-family:Kai,'Segoe UI',sans-serif;-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}
`}</style>;

const Background=()=> <>
  <AbsoluteFill style={{background:C.paperBase}}/>
  <div style={{position:'absolute',left:72,top:58,right:72,bottom:60,backgroundImage:`repeating-linear-gradient(0deg,transparent 0 53px,rgba(94,74,50,${AESTHETIC.gridOpacity}) 54px),repeating-linear-gradient(90deg,transparent 0 53px,rgba(94,74,50,${AESTHETIC.gridOpacity}) 54px),radial-gradient(circle at 22% 8%,rgba(255,255,255,.28),transparent 42%)`}}/>
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

// Mascot：系列吉祥物（代码绘制的 git 猫）。f 传本地帧可眨眼、自然呼吸，wave 挥手。
const Mascot:React.FC<{size?:number;f?:number;wave?:boolean}>=({size=180,f=0,wave=false})=>{
  const blink=(f%54)<3?0.12:1;
  const arm=wave?Math.sin(f*0.28)*20:6;
  const breath=1+0.016*Math.sin(f*0.16);
  return <svg width={size} height={size} viewBox="0 0 100 100" style={{overflow:'visible',transform:`scale(${breath})`,transformOrigin:'50% 90%'}}>
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
  </svg>;
};

// RollDigit：Tibo 式字符/数字 3D 滚轮翻牌——带 cos 投影压缩 + 3D 旋转 + 颜色过渡
const RollDigit:React.FC<{fromChar:string;toChar:string;start:number;duration?:number;frame?:number;fontSize:number;fontFamily?:string;fontWeight?:number|string;colorFrom?:string;colorTo?:string;style?:React.CSSProperties}>=({fromChar,toChar,start,duration=13,frame,fontSize,fontFamily,fontWeight=700,colorFrom=C.muted,colorTo=C.green,style})=>{
  const f=frame??q(useCurrentFrame());
  const progress=easeOutSoft(f,start,start+duration);
  const turnPhase=progress;
  const outgoingPhase=Math.max(0,Math.min(1,turnPhase/0.56));
  const incomingPhase=Math.max(0,Math.min(1,(turnPhase-0.44)/0.56));
  const outgoingTurn=interpolate(outgoingPhase,[0,1],[0,-90]);
  const incomingTurn=interpolate(incomingPhase,[0,1],[90,0]);
  const outgoingY=interpolate(outgoingPhase,[0,1],[0,-fontSize*0.32]);
  const incomingY=interpolate(incomingPhase,[0,1],[fontSize*0.32,0]);
  const outgoingScaleY=progress>=1?1:Math.max(0.001,Math.cos((Math.abs(outgoingTurn)*Math.PI)/180));
  const incomingScaleY=Math.max(0.001,Math.cos((Math.abs(incomingTurn)*Math.PI)/180));
  const color=interpolateColors(progress,[0,1],[colorFrom,colorTo]);
  return <span style={{display:'inline-block',position:'relative',overflow:'visible',verticalAlign:'baseline',perspective:600,...style}}>
    <span style={{display:'inline-block',color,fontSize,fontFamily,fontWeight,opacity:progress>=1||turnPhase<=0.56?1:0,transform:`translateY(${progress>=1?0:outgoingY}px) scaleY(${outgoingScaleY})`,transformOrigin:'50% 100%'}}>{fromChar}</span>
    <span style={{position:'absolute',left:0,top:0,color,fontSize,fontFamily,fontWeight,opacity:turnPhase>=0.44&&progress<1?1:0,transform:`translateY(${incomingY}px) scaleY(${incomingScaleY})`,transformOrigin:'50% 0%'}}>{toChar}</span>
  </span>;
};

// JumpInText：Tibo 式逐字入场——每个字独立 3D 翻转（rotateX）+ 上移 + 错峰弹出。
// items 支持多段（颜色/字体/字号混排），母容器带 perspective；stagger=每字错峰帧数。
// frame 可传本地帧（场景内），默认用全局帧。
const JumpInText:React.FC<{items:{text:string,color?:string,fontFamily?:string,fontSize?:number}[],fontSize:number,fontWeight?:number,start:number,stagger?:number,letterSpacing?:number,style?:React.CSSProperties,frame?:number}>=({items,fontSize,fontWeight=700,start,stagger=1.6,letterSpacing=0,style,frame})=>{
  const f=frame??q(useCurrentFrame());
  let seq=0;
  return <div style={{display:'flex',flexWrap:'wrap',justifyContent:'center',alignItems:'baseline',perspective:1200,...style}}>
    {items.map((seg,si)=>String(seg.text).split('').map((ch,ci)=>{const i=seq++;const p=pop(f,start+i*stagger);return <span key={`${si}-${ci}`} style={{display:'inline-block',fontSize:seg.fontSize||fontSize,fontWeight,fontFamily:seg.fontFamily||'inherit',color:seg.color,letterSpacing,opacity:p,transform:`translateY(${12*(1-p)}px) rotateX(${(1-p)*88}deg)`,transformOrigin:'50% 100%'}}>{ch===' '?'\u00a0':ch}</span>}))}
  </div>;
};

// WaveText：Tibo 式字母波浪打字——每字母 4 段关键帧波浪 + 颜色渐变
const WaveText:React.FC<{text:string;fontSize:number;colorFrom:string;colorTo:string;start:number;stagger?:number;frame?:number;fontFamily?:string;fontWeight?:number;letterSpacing?:number;style?:React.CSSProperties}>=({text,fontSize,colorFrom,colorTo,start,stagger=1.2,frame,fontFamily,fontWeight=600,letterSpacing=0,style})=>{
  const f=frame??q(useCurrentFrame());
  const ss=(v:number)=>{const t=Math.max(0,Math.min(1,v));return t*t*(3-2*t)};
  return <div style={{display:'flex',justifyContent:'center',alignItems:'baseline',...style}}>
    {text.split('').map((ch,i)=>{const age=f-(start+i*stagger);const wave=ss(age/10),col=interpolateColors(ss(age/8),[0,1],[colorFrom,colorTo]);const wx=interpolate(wave,[.0,.28,.64,1],[10,-3,1,0]);const wy=interpolate(wave,[.0,.28,.64,1],[14,-14,4,0]);return <span key={i} style={{display:'inline-block',fontSize,fontFamily,fontWeight,letterSpacing,color:col,opacity:ss((age+0.4)/1.5),transform:`translate(${wx}px,${wy}px)`}}>{ch}</span>})}
  </div>;
};

const cleanTail=(s:string)=>s.replace(/[，。！？；：、,.!?;:\s]+$/g,'');
const Subtitle=()=>{const f=useRawCurrentFrame(),lead=Math.round(FPS*.18),hold=Math.round(FPS*.05);let cue=captions.find((c:any)=>f>=c.startFrame-lead&&f<=c.endFrame+hold);if(!cue)cue=[...captions].reverse().find((c:any)=>c.startFrame<=f);const full=cue?cleanTail(cue.text):'';const words=cue?cue.words.filter((w:any)=>w.startFrame<=f+lead):[];return <div style={{position:'absolute',left:MODE.subMar,right:MODE.subMar,bottom:18,zIndex:200,display:'grid',placeItems:'center',textShadow:'0 2px 8px rgba(58,44,28,.28)'}}>
  <div style={{width:AESTHETIC.subtitleSafeWidth,display:'grid',placeItems:'center',fontFamily:'Kai',fontSize:TYPE.subtitle,lineHeight:1.18,letterSpacing:1.6,whiteSpace:'nowrap'}}><span style={{position:'relative'}}><span style={{visibility:'hidden'}}>{full}</span><span style={{position:'absolute',left:0,top:0}}>{words.map((w:any,wi:number)=>{const part=String(w.part);const prev=wi>0?String(words[wi-1].part):'';const spaced=(wi>0&&!/[\s，。！？；：、,.!?;:（(]$/.test(prev)&&!/^[\s，。！？；：、,.!?;:）)]/.test(part)&&!((/[A-Za-z0-9]$/.test(prev)&&/^[A-Za-z0-9]/.test(part))||(/[一-鿿]$/.test(prev)&&/^[一-鿿]/.test(part))))?'\u00a0':'';return <span key={wi} style={{display:'inline-block'}}>{spaced}{part.split('').map((ch:any,ci:number)=>{const p=interpolate(f,[w.startFrame+ci*.9,w.startFrame+ci*.9+2.5],[0,1],{...clamp,easing:Easing.bezier(.16,1,.3,1)});return <span key={ci} style={{display:'inline-block',opacity:p,transform:`translateY(${6*(1-p)}px)`}}>{ch}</span>})}</span>})}</span></span></div>
</div>};

const Chrome=()=>{const f=q(useCurrentFrame()),stage=f<213?0:f<416?1:f<682?2:3,starts=[0,213,416,682],local=f-starts[stage],p=pop(local,-8),titles=COPY.chapterTitles;return <>
  <Paper style={{left:isPortrait?40:92,top:isPortrait?80:74,width:isPortrait?330:392,height:isPortrait?76:82,zIndex:150,display:'flex',opacity:p,transform:`translateY(${14*(1-p)}px) scale(${.96+.04*p})`}}><div style={{width:isPortrait?60:72,background:C.orange,color:C.white,display:'grid',placeItems:'center',fontFamily:'Clash',fontWeight:600,fontSize:isPortrait?28:31}}>{String(stage+1).padStart(2,'0')}</div><div style={{padding:isPortrait?'8px 14px':'10px 16px'}}><div style={{fontSize:TYPE.microS,color:C.blue,fontWeight:700,letterSpacing:3.2,fontFamily:'Space,Kai'}}>{COPY.chromeKicker}</div><JumpInText key={stage} items={[{text:titles[stage]}]} fontSize={TYPE.titleS} start={starts[stage]+8} stagger={1.1} style={{marginTop:3}}/></div></Paper>
  <div style={{position:'absolute',right:isPortrait?40:88,top:isPortrait?76:70,zIndex:140,textAlign:'right'}}><div style={{fontSize:TYPE.labelM,fontWeight:700,letterSpacing:5,color:C.blue,fontFamily:'Clash,Space'}}>{COPY.header}</div><div style={{fontSize:TYPE.microL,marginTop:7,color:C.muted,fontFamily:'Space,Kai'}}>{COPY.headerSub}</div></div>
</>};

const stageFade=(f:number,start:number,end:number)=>ease(f,start,start+15)*ease(f,end-15,end,1,0);

// ---- 场景内容层（换题材时重写以下全部） -----------------------------------
// 每个场景的标准结构：多元素分区（讲解面板 + 图形演示区 + 清单/贴纸），
// 每个区域同一时刻只有一个主动作；所有时间常量都是“场景本地帧”，
// 来自对应台词的 cue 帧（见文件头部的机械流程）。

// SCENE 1 — code is lonely -> GitHub collaborative world
const NODES=[{x:250,y:150,c:C.orange,label:'仓库'},{x:930,y:120,c:C.gold,label:'Star'},{x:1000,y:360,c:C.green,label:'Fork'},{x:210,y:410,c:C.blue,label:'Issue'},{x:600,y:470,c:C.red,label:'PR'}];
const SceneWorld=()=>{const f=q(useCurrentFrame()),l=f,opacity=stageFade(f,0,202);const dim=ease(l,51,92,1,.42),roll=easeOutSoft(l,45,78),rollS=interpolate(roll,[0,.5,.82,1],[.82,1.06,.98,1]),rollR=interpolate(roll,[0,1],[150,360]),rollO=ease(l,43,62);return <div style={{position:'absolute',inset:0,opacity}}>
  <Paper style={{left:120,top:300,width:330,height:250,zIndex:60,padding:'26px 28px',borderColor:C.muted,opacity:dim,transform:`translateY(${26*(1-pop(l,4))}px) scale(${.94+.06*pop(l,4)})`}}>
    <JumpInText frame={l} items={[{text:'本地硬盘',color:C.muted}]} fontSize={TYPE.displayS} start={7}/>
    <div style={{fontSize:TYPE.bodyM,fontWeight:700,marginTop:8,color:C.muted}}>代码只躺在你电脑里</div>
    <div style={{position:'absolute',left:28,right:28,top:120,bottom:28}}>{[0,1,2,3].map(i=><div key={i} style={{height:12,margin:'11px 0',width:`${72-i*9}%`,background:'#cabfa8',borderRadius:4,opacity:pop(l,12+i*6)}}/>)}</div>
  </Paper>
  <div style={{position:'absolute',left:470,top:405,fontSize:70,color:C.orange,zIndex:75,opacity:ease(l,42,60),transform:`translateX(${-14*(1-ease(l,42,60))}px)`}}>→</div>
  <div style={{position:'absolute',left:600,top:200,width:1160,height:600,zIndex:72,opacity:rollO,transform:`rotate(${rollR}deg) scale(${rollS})`,transformOrigin:'50% 50%'}}>
    <svg width={1160} height={600} viewBox="0 0 1160 600" style={{overflow:'visible'}}>
      <circle cx={580} cy={300} r={140} fill="#e9f1fc" stroke={C.blue} strokeWidth={4}/>
      <ellipse cx={580} cy={300} rx={56} ry={140} fill="none" stroke={C.blue} strokeWidth={2} opacity={.45}/>
      <ellipse cx={580} cy={300} rx={110} ry={140} fill="none" stroke={C.blue} strokeWidth={2} opacity={.3}/>
      <line x1={440} y1={300} x2={720} y2={300} stroke={C.blue} strokeWidth={2} opacity={.45}/>
      <path d="M520 250 q30 -26 66 -6 q34 -16 52 14 q-10 34 -48 26 q-30 20 -60 -8 q-16 -30 -10 -26" fill={C.green} opacity={.25}/>
      {NODES.map((n,i)=>{const app=ease(l,72+i*9,98+i*9);const mx=(580+n.x)/2,my=(300+n.y)/2-46;return <g key={i} opacity={app}>
        <path d={`M580 300 Q${mx} ${my} ${n.x} ${n.y}`} fill="none" stroke={n.c} strokeWidth={3} strokeDasharray="9 8" strokeDashoffset={-l*3}/>
        <g transform={`scale(${.6+.4*pop(l,65+i*9)})`} style={{transformBox:'fill-box',transformOrigin:'center'} as any}>
          <rect x={n.x-38} y={n.y-30} width={76} height={60} rx={9} fill={C.paper} stroke={n.c} strokeWidth={3}/>
          <rect x={n.x-38} y={n.y-30} width={76} height={16} rx={9} fill={n.c} opacity={.85}/>
        </g>
      </g>;})}
    </svg>
    {NODES.map((n,i)=><div key={i} style={{position:'absolute',left:n.x-38,top:n.y-4,width:76,textAlign:'center',fontFamily:'Space,Kai',fontWeight:600,fontSize:TYPE.bodyM,color:n.c,opacity:ease(l,84+i*9,104+i*9)}}>{n.label}</div>)}
    <div style={{position:'absolute',left:512,top:286,color:C.blue,fontFamily:'Clash',fontWeight:600,fontSize:TYPE.microL,letterSpacing:1}}>GitHub</div>
  </div>
  <div style={{position:'absolute',left:150,top:600,zIndex:96,opacity:ease(l,95,117),transform:`translateY(${20*(1-ease(l,95,117))}px)`}}><Mascot size={150} f={l} wave/></div>
  <Paper style={{left:560,top:748,width:840,height:86,zIndex:85,display:'grid',placeItems:'center',borderColor:C.green,opacity:ease(l,124,143),transform:`translateY(${18*(1-pop(l,124))}px)`}}><JumpInText frame={l} items={[{text:'全世界的开发者，',color:C.ink},{text:'一起造软件',color:C.green}]} fontSize={TYPE.titleL} start={125}/></Paper>
</div>};

// SCENE 2 — step one: contribute a PR
const StepRail:React.FC<{active:number;l:number;start:number}>=({active,l,start})=>{const steps=[['01','参与',C.orange],['02','发布',C.blue],['03','运营',C.green]] as const;return <div style={{position:'absolute',left:360,top:180,width:1200,height:72,zIndex:78,display:'flex',gap:26,justifyContent:'center'}}>{steps.map((s,i)=>{const on=i===active,p=pop(l,start+i*7);return <div key={s[0]} style={{width:360,height:70,display:'flex',alignItems:'center',gap:16,padding:'0 22px',background:on?C.paper:'#efe3ca',border:`${on?3:2}px solid ${on?s[2]:'#c7b696'}`,borderRadius:12,boxShadow:on?'6px 8px 0 rgba(63,49,35,.2)':'none',opacity:p,transform:`translateY(${16*(1-p)}px) scale(${on?1:.96})`}}><span style={{width:38,height:38,borderRadius:99,background:on?s[2]:'#c7b696',color:C.white,display:'grid',placeItems:'center',fontFamily:'Clash',fontWeight:600,fontSize:22}}>{s[0]}</span><span style={{fontFamily:'Kai',fontWeight:700,fontSize:TYPE.titleM,color:on?s[2]:C.muted}}>{s[1]}</span></div>;})}</div>;};
const SceneContribute=()=>{const f=q(useCurrentFrame()),l=f-213,opacity=stageFade(f,198,404);const t=easeOutSoft(l,43,113);const merge=ease(l,105,134);const cardX=180+560*Math.min(1,t/0.72);const steps=['读懂项目规则','建立最小改动','提交你的 PR','通过 CI 与评审'];return <div style={{position:'absolute',inset:0,opacity}}>
  <StepRail active={0} l={l} start={6}/>
  <svg width="1920" height="1080" style={{position:'absolute',inset:0,zIndex:55}}>
    <path d="M150 560 H1080" fill="none" stroke="#c9b99e" strokeWidth={8}/>
    <path d="M150 700 H760 Q840 700 880 620 L910 566" fill="none" stroke={C.orange} strokeWidth={7} strokeDasharray="16 12" strokeDashoffset={-l*4} opacity={.9}/>
    <text x="150" y="540" fill={C.blue} fontFamily="Space,Kai" fontWeight="600" fontSize="30">main 主干</text>
    <text x="150" y="742" fill={C.orange} fontFamily="Space,Kai" fontWeight="600" fontSize="30">你的分支</text>
    <circle cx={910} cy={562} r={13} fill={merge>.4?C.green:'#c9b99e'} opacity={ease(l,99,120)}/>
  </svg>
  <Paper lift={Math.sin(Math.PI*t)*.5} style={{left:cardX,top:648,width:210,height:96,zIndex:96,padding:'16px 18px',borderColor:C.orange,opacity:ease(l,39,56)*ease(l,130,142,1,0),transform:`translateY(${-90*Math.sin(Math.PI*t)*(cardX<700?1:.4)}px)`}}><div style={{fontFamily:'Kai',fontWeight:700,fontSize:TYPE.titleS,color:C.orange}}>你的修改</div><div style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.labelL,marginTop:6,color:C.muted}}>commit</div></Paper>
  <Paper lift={.4} style={{left:840,top:430,width:250,height:108,zIndex:94,padding:'16px 20px',borderColor:C.green,opacity:merge,transform:`scale(${.7+.3*pop(l,109)})`}}><div style={{display:'flex',alignItems:'center',gap:12}}><span style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.titleM,color:C.green}}>Pull Request</span></div><div style={{fontSize:TYPE.labelL,fontWeight:700,marginTop:8,color:C.muted}}>把改动交给项目</div><div style={{position:'absolute',right:16,top:16,transform:`scale(${pop(l,130)})`}}><CheckBadge size={30}/></div></Paper>
  <Paper style={{left:1180,top:300,width:580,height:430,zIndex:76,padding:'34px 40px',borderColor:C.blue,transform:`translateX(${40*(1-pop(l,9))}px)`,opacity:pop(l,9)}}>
    <JumpInText frame={l} items={[{text:'第一步：参与开源',color:C.blue}]} fontSize={TYPE.displayS} start={11}/>
    <div style={{position:'absolute',left:40,right:40,top:116,bottom:104}}>{steps.map((s,i)=>{const p=pop(l,39+i*20);return <div key={s} style={{display:'flex',alignItems:'center',gap:16,height:48,marginBottom:8,opacity:p,transform:`translateX(${24*(1-p)}px)`}}><span style={{width:40,height:40,borderRadius:99,background:[C.orange,C.blue,C.green,C.gold][i],color:C.white,display:'grid',placeItems:'center',fontFamily:'Clash',fontWeight:600,fontSize:20}}>{i+1}</span><span style={{fontSize:TYPE.titleXS,fontWeight:700}}>{s}</span></div>;})}</div>
    <div style={{position:'absolute',left:40,right:40,bottom:34,height:44,background:'#eadcc1',border:`2px solid ${C.green}`,borderRadius:10,display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyL,color:C.green,letterSpacing:1,opacity:ease(l,120,140)}}>github-oss-contribute</div>
  </Paper>
</div>};

// SCENE 3 — step two & three: prep and operate
const Module:React.FC<{name:string;color:string;l:number;start:number;fromX:number;toX:number;toY:number;top?:number}>=({name,color,l,start,fromX,toX,toY,top=250})=>{const u=ease(l,start,start+44);const fade=ease(l,start+40,start+52,1,0);return <Paper lift={Math.sin(Math.PI*u)*.5} style={{left:fromX,top:250,width:190,height:56,zIndex:94,display:'grid',placeItems:'center',borderColor:color,opacity:ease(l,start,start+8)*fade,transform:`translate3d(${(toX-fromX)*u}px,${(toY-250)*u}px,0) scale(${1-.34*u})`}}><span style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyL,color}}>{name}</span></Paper>;};
const Gauge:React.FC<{label:string;color:string;v:number;x:number}>=({label,color,v,x})=><div style={{position:'absolute',left:x,top:0,width:130,textAlign:'center'}}><svg width={110} height={70} viewBox="0 0 110 70"><path d="M12 62 A43 43 0 0 1 98 62" fill="none" stroke="#d6c6aa" strokeWidth={9} strokeLinecap="round"/><path d="M12 62 A43 43 0 0 1 98 62" fill="none" stroke={color} strokeWidth={9} strokeLinecap="round" strokeDasharray={135} strokeDashoffset={135*(1-v)}/></svg><div style={{fontSize:TYPE.labelL,fontWeight:700,marginTop:2,color:C.ink}}>{label}</div></div>;
const SceneShip=()=>{const f=q(useCurrentFrame()),l=f-416,opacity=stageFade(f,399,669);const ver=ease(l,177,219);const rocket=easeOutSoft(l,177,236);const g1=ease(l,135,177),g2=ease(l,152,194),g3=ease(l,169,211);return <div style={{position:'absolute',inset:0,opacity}}>
  <Paper style={{left:120,top:250,width:560,height:470,zIndex:70,padding:'30px 34px',borderColor:C.orange,transform:`translateY(${26*(1-pop(l,5))}px) scale(${.95+.05*pop(l,5)})`,opacity:pop(l,5)}}>
    <JumpInText frame={l} items={[{text:'第二步：发布',color:C.orange}]} fontSize={TYPE.displayS} start={7}/>
    <div style={{fontSize:TYPE.titleXS,fontWeight:700,marginTop:8,color:C.muted}}>整理成专业开源仓库</div>
    <div style={{position:'absolute',left:150,top:170,width:260,height:210,background:'#efe3ca',border:`3px solid ${C.orange}`,borderRadius:'10px 10px 0 0'}}><div style={{position:'absolute',left:-1,right:-1,top:-30,height:30,background:C.orange,clipPath:'polygon(0 100%,10% 0,90% 0,100% 100%)'}}/><div style={{padding:'16px'}}>{['README','LICENSE','CI'].map((m,i)=><div key={m} style={{height:40,margin:'10px 0',background:C.paper,border:`2px solid ${[C.blue,C.green,C.gold][i]}`,borderRadius:6,display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyM,opacity:ease(l,44+i*22,64+i*22)}}>{m}</div>)}</div></div>
    <div style={{position:'absolute',left:34,right:34,bottom:30,height:42,background:'#eadcc1',border:`2px solid ${C.orange}`,borderRadius:10,display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyM,color:C.orange,opacity:ease(l,95,130)}}>github-oss-prep</div>
  </Paper>
  <Module name="README" color={C.blue} l={l} start={39} fromX={470} toX={300} toY={430}/>
  <Module name="LICENSE" color={C.green} l={l} start={61} fromX={470} toX={300} toY={480}/>
  <Paper style={{left:740,top:250,width:1020,height:470,zIndex:72,padding:'30px 40px',borderColor:C.navy,transform:`translateY(${26*(1-pop(l,89))}px) scale(${.95+.05*pop(l,89)})`,opacity:pop(l,89)}}>
    <JumpInText frame={l} items={[{text:'第三步：运营',color:C.navy}]} fontSize={TYPE.displayS} start={91}/>
    <div style={{fontSize:TYPE.titleXS,fontWeight:700,marginTop:8,color:C.muted}}>分流 · 审查 · 按时发版</div>
    <div style={{position:'absolute',left:60,top:150,right:60,height:120}}><Gauge label="Issue 分流" color={C.orange} v={g1} x={20}/><Gauge label="PR 审查" color={C.blue} v={g2} x={330}/><Gauge label="Release" color={C.green} v={g3} x={640}/></div>
    <div style={{position:'absolute',left:60,bottom:116,display:'flex',alignItems:'center',gap:16,opacity:ease(l,177,208)}}>
      <div style={{display:'flex',alignItems:'center',gap:4,padding:'4px 14px',background:C.paper,border:`2px solid ${C.line}`,borderRadius:10,boxShadow:paperShadow(0.15)}}>
        <span style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.titleL,color:C.ink}}>v1.</span>
        <RollDigit fromChar="0" toChar="1" start={182} duration={13} frame={l} fontSize={TYPE.displayS} fontFamily="Space" fontWeight={700} colorFrom={C.muted} colorTo={C.green}/>
      </div>
      <div style={{display:'flex',alignItems:'center',gap:6,color:C.green,fontFamily:'Space,Kai',fontWeight:700,fontSize:TYPE.bodyM,opacity:ease(l,194,212),transform:`translateX(${10*(1-ease(l,194,212))}px)`}}>
        <CheckBadge size={24}/> 准备发版
      </div>
    </div>
    <svg width={120} height={160} style={{position:'absolute',right:70,bottom:60,transform:`translateY(${-150*rocket}px)`,opacity:ease(l,175,197)}} viewBox="0 0 120 160"><path d="M60 6 C86 40 86 88 60 120 C34 88 34 40 60 6 Z" fill={C.paper} stroke={C.red} strokeWidth={4}/><circle cx={60} cy={54} r={13} fill="#e9f1fc" stroke={C.blue} strokeWidth={3}/><path d="M40 96 L24 128 L44 116 Z" fill={C.orange} stroke={C.red} strokeWidth={3} strokeLinejoin="round"/><path d="M80 96 L96 128 L76 116 Z" fill={C.orange} stroke={C.red} strokeWidth={3} strokeLinejoin="round"/><path d="M50 120 q10 24 20 0" fill={C.gold} opacity={.9}/></svg>
    <div style={{position:'absolute',left:40,right:40,bottom:30,height:42,background:'#eadcc1',border:`2px solid ${C.navy}`,borderRadius:10,display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyM,color:C.navy,opacity:ease(l,188,217)}}>github-oss-ops</div>
  </Paper>
</div>};

// SCENE 4 — three AI skills + CTA
const SKILLS=[['github-oss-contribute','参与别人的项目','EP 1',C.orange],['github-oss-prep','发布自己的作品','EP 2',C.blue],['github-oss-ops','运营与持续发版','EP 3',C.green]] as const;
const SceneSkills=()=>{const f=q(useCurrentFrame()),l=f-682,opacity=ease(f,662,692);const cta=ease(l,282,350);return <div style={{position:'absolute',inset:0,opacity}}>
  <div style={{position:'absolute',left:860,top:214,zIndex:75,textAlign:'center',opacity:pop(l,5),transform:`scale(${.7+.3*pop(l,5)})`}}><Mascot size={150} f={l} wave/><div style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.titleM,color:C.navy,marginTop:2,letterSpacing:3}}>AI AGENT</div></div>
  {SKILLS.map((s,i)=>{const p=pop(l,36+i*16);const x=200+i*530;return <Paper key={s[0]} lift={.25} style={{left:x,top:410,width:470,height:250,zIndex:94,padding:'28px 30px',borderColor:s[3],opacity:p,transform:`translateY(${34*(1-p)}px) scale(${.92+.08*p})`}}>
    <div style={{position:'absolute',right:24,top:22,fontFamily:'Clash',fontWeight:600,fontSize:TYPE.titleM,color:s[3],opacity:ease(l,60+i*16,84+i*16)}}>{s[2]}</div>
    <div style={{width:56,height:56,borderRadius:14,background:s[3],display:'grid',placeItems:'center',color:C.white}}><LineIcon kind={['play','project','report'][i] as IconKind} size={34} color={C.white} strokeWidth={2.2}/></div>
    <div style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.titleM,color:s[3],marginTop:16}}>{s[0]}</div>
    <div style={{fontSize:TYPE.titleXS,fontWeight:700,marginTop:12}}>{s[1]}</div>
    <div style={{position:'absolute',left:30,bottom:24,display:'flex',alignItems:'center',gap:10,color:C.muted,fontSize:TYPE.labelL,fontWeight:700}}><CheckBadge size={26}/>智能体陪你走完</div>
  </Paper>;})}
  <Paper style={{left:460,top:724,width:1000,height:104,zIndex:96,display:'grid',placeItems:'center',borderColor:C.orange,opacity:cta,transform:`translateY(${22*(1-cta)}px) scale(${.96+.04*pop(l,286)})`}}><div style={{display:'flex',alignItems:'center',gap:16}}><JumpInText frame={l} items={[{text:'主页搜',color:C.muted,fontSize:TYPE.titleM}]} fontSize={TYPE.titleM} start={287}/><WaveText frame={l} text="github.com/hyt315" fontSize={TYPE.displayS} colorFrom="#f0b39e" colorTo={C.orange} start={291} fontFamily="Space" fontWeight={600}/></div></Paper>
</div>};


// ---- 3:4 portrait scene set (single-column stacking) -------------
// Same beat structure as the landscape scenes; pick with CANVAS='3:4'.
const StepRailP:React.FC<{active:number;l:number;start:number}>=({active,l,start})=>{const steps=[['01','参与',C.orange],['02','发布',C.blue],['03','运营',C.green]] as const;return <div style={{position:'absolute',left:70,top:190,width:940,height:68,zIndex:78,display:'flex',gap:20,justifyContent:'center'}}>{steps.map((s,i)=>{const on=i===active,p=pop(l,start+i*7);return <div key={s[0]} style={{width:300,height:64,display:'flex',alignItems:'center',gap:12,padding:'0 14px',background:on?C.paper:'#efe3ca',border:`${on?3:2}px solid ${on?s[2]:'#c7b696'}`,borderRadius:12,boxShadow:on?'5px 7px 0 rgba(63,49,35,.2)':'none',opacity:p,transform:`translateY(${14*(1-p)}px) scale(${on?1:.96})`}}><span style={{width:32,height:32,borderRadius:99,background:on?s[2]:'#c7b696',color:C.white,display:'grid',placeItems:'center',fontFamily:'Clash',fontWeight:600,fontSize:19}}>{s[0]}</span><span style={{fontFamily:'Kai',fontWeight:700,fontSize:TYPE.titleXS,color:on?s[2]:C.muted}}>{s[1]}</span></div>;})}</div>;};

const SceneWorldP=()=>{const f=q(useCurrentFrame()),l=f,opacity=stageFade(f,0,202);const dim=ease(l,51,92,1,.42),roll=easeOutSoft(l,45,78),rollS=interpolate(roll,[0,.5,.82,1],[.82,1.06,.98,1]),rollR=interpolate(roll,[0,1],[150,360]),rollO=ease(l,43,62);return <div style={{position:'absolute',inset:0,opacity}}>
  <Paper style={{left:60,top:200,width:960,height:230,zIndex:60,padding:'22px 26px',borderColor:C.muted,opacity:dim,transform:`translateY(${26*(1-pop(l,4))}px) scale(${.94+.06*pop(l,4)})`}}>
    <JumpInText frame={l} items={[{text:'本地硬盘',color:C.muted}]} fontSize={TYPE.displayS} start={7}/>
    <div style={{fontSize:TYPE.bodyM,fontWeight:700,marginTop:8,color:C.muted}}>代码只躺在你电脑里</div>
    <div style={{position:'absolute',left:26,right:26,top:118,bottom:20}}>{[0,1,2,3].map(i=><div key={i} style={{height:13,margin:'10px 0',width:`${72-i*9}%`,background:'#cabfa8',borderRadius:4,opacity:pop(l,12+i*6)}}/>)}</div>
  </Paper>
  <div style={{position:'absolute',left:516,top:452,fontSize:62,color:C.orange,zIndex:75,opacity:ease(l,42,60),transform:`translateY(${-10*(1-ease(l,42,60))}px)`}}>↓</div>
  <div style={{position:'absolute',left:80,top:540,width:1160,height:600,zIndex:72,transform:'scale(0.776)',transformOrigin:'left top',opacity:rollO}}>
    <svg width={1160} height={600} viewBox="0 0 1160 600" style={{overflow:'visible'}}>
      <circle cx={580} cy={300} r={140} fill="#e9f1fc" stroke={C.blue} strokeWidth={4}/>
      <ellipse cx={580} cy={300} rx={56} ry={140} fill="none" stroke={C.blue} strokeWidth={2} opacity={.45}/>
      <ellipse cx={580} cy={300} rx={110} ry={140} fill="none" stroke={C.blue} strokeWidth={2} opacity={.3}/>
      <line x1={440} y1={300} x2={720} y2={300} stroke={C.blue} strokeWidth={2} opacity={.45}/>
      <path d="M520 250 q30 -26 66 -6 q34 -16 52 14 q-10 34 -48 26 q-30 20 -60 -8 q-16 -30 -10 -26" fill={C.green} opacity={.25}/>
      {NODES.map((n,i)=>{const app=ease(l,72+i*9,98+i*9);const mx=(580+n.x)/2,my=(300+n.y)/2-46;return <g key={i} opacity={app}>
        <path d={`M580 300 Q${mx} ${my} ${n.x} ${n.y}`} fill="none" stroke={n.c} strokeWidth={3} strokeDasharray="9 8" strokeDashoffset={-l*3}/>
        <g transform={`scale(${.6+.4*pop(l,65+i*9)})`} style={{transformBox:'fill-box',transformOrigin:'center'} as any}>
          <rect x={n.x-38} y={n.y-30} width={76} height={60} rx={9} fill={C.paper} stroke={n.c} strokeWidth={3}/>
          <rect x={n.x-38} y={n.y-30} width={76} height={16} rx={9} fill={n.c} opacity={.85}/>
        </g>
      </g>;})}
    </svg>
    {NODES.map((n,i)=><div key={i} style={{position:'absolute',left:n.x-38,top:n.y-4,width:76,textAlign:'center',fontFamily:'Space,Kai',fontWeight:600,fontSize:TYPE.bodyM,color:n.c,opacity:ease(l,84+i*9,104+i*9)}}>{n.label}</div>)}
    <div style={{position:'absolute',left:512,top:286,color:C.blue,fontSize:TYPE.microL,fontWeight:700}}>GitHub</div>
  </div>
  <div style={{position:'absolute',left:860,top:1010,zIndex:96,opacity:ease(l,95,117),transform:`translateY(${18*(1-ease(l,95,117))}px)`}}><Mascot size={105} f={l} wave/></div>
  <Paper style={{left:50,top:1130,width:980,height:86,zIndex:85,display:'grid',placeItems:'center',borderColor:C.green,opacity:ease(l,124,143),transform:`translateY(${18*(1-pop(l,124))}px)`}}><div style={{fontSize:TYPE.titleL,fontWeight:700}}>全世界的开发者，<span style={{color:C.green}}>一起造软件</span></div></Paper>
</div>};

const SceneContributeP=()=>{const f=q(useCurrentFrame()),l=f-213,opacity=stageFade(f,198,404);const t=ease(l,43,113);const merge=ease(l,105,134);const cardX=80+520*Math.min(1,t/0.72);const steps=['读懂项目规则','建立最小改动','提交你的 PR','通过 CI 与评审'];return <div style={{position:'absolute',inset:0,opacity}}>
  <StepRailP active={0} l={l} start={6}/>
  <svg width={1080} height={1440} style={{position:'absolute',inset:0,zIndex:55}}>
    <path d="M80 640 H760" fill="none" stroke="#c9b99e" strokeWidth={8}/>
    <path d="M80 760 H590 Q660 760 700 700 L732 652" fill="none" stroke={C.orange} strokeWidth={7} strokeDasharray="16 12" strokeDashoffset={-l*4} opacity={.9}/>
    <text x="80" y="612" fill={C.blue} fontFamily="Space,Kai" fontWeight="600" fontSize="30">main 主干</text>
    <text x="80" y="802" fill={C.orange} fontFamily="Space,Kai" fontWeight="600" fontSize="30">你的分支</text>
    <circle cx={732} cy={648} r={13} fill={merge>.4?C.green:'#c9b99e'} opacity={ease(l,99,120)}/>
  </svg>
  <Paper lift={Math.sin(Math.PI*t)*.5} style={{left:cardX,top:700,width:210,height:96,zIndex:96,padding:'16px 18px',borderColor:C.orange,opacity:ease(l,39,56)*ease(l,130,142,1,0),transform:`translateY(${-90*Math.sin(Math.PI*t)*(cardX<400?1:.4)}px)`}}><div style={{fontFamily:'Kai',fontWeight:700,fontSize:TYPE.titleS,color:C.orange}}>你的修改</div><div style={{fontSize:TYPE.labelL,fontWeight:700,marginTop:6,color:C.muted}}>commit</div></Paper>
  <Paper lift={.4} style={{left:540,top:520,width:250,height:108,zIndex:94,padding:'16px 20px',borderColor:C.green,opacity:merge,transform:`scale(${.7+.3*pop(l,109)})`}}><div style={{display:'flex',alignItems:'center',gap:12}}><span style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.titleM,color:C.green}}>Pull Request</span></div><div style={{fontSize:TYPE.labelL,fontWeight:700,marginTop:8,color:C.muted}}>把改动交给项目</div><div style={{position:'absolute',right:16,top:16,transform:`scale(${pop(l,130)})`}}><CheckBadge size={30}/></div></Paper>
  <Paper style={{left:60,top:840,width:960,height:420,zIndex:76,padding:'26px 30px',borderColor:C.blue,transform:`translateX(${36*(1-pop(l,9))}px)`,opacity:pop(l,9)}}>
    <JumpInText frame={l} items={[{text:'第一步：参与开源',color:C.blue}]} fontSize={TYPE.displayS} start={11}/>
    <div style={{position:'absolute',left:30,right:30,top:104,bottom:112}}>{steps.map((s,i)=>{const p=pop(l,39+i*20);return <div key={s} style={{display:'flex',alignItems:'center',gap:16,height:48,marginBottom:10,opacity:p,transform:`translateX(${24*(1-p)}px)`}}><span style={{width:40,height:40,borderRadius:99,background:[C.orange,C.blue,C.green,C.gold][i],color:C.white,display:'grid',placeItems:'center',fontFamily:'Clash',fontWeight:600,fontSize:20}}>{i+1}</span><span style={{fontSize:TYPE.titleXS,fontWeight:700}}>{s}</span></div>;})}</div>
    <div style={{position:'absolute',left:30,right:30,bottom:30,height:44,background:'#eadcc1',border:`2px solid ${C.green}`,borderRadius:10,display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyL,color:C.green,letterSpacing:1,opacity:ease(l,120,140)}}>github-oss-contribute</div>
  </Paper>
</div>};

const SceneShipP=()=>{const f=q(useCurrentFrame()),l=f-416,opacity=stageFade(f,399,669);const ver=ease(l,177,219);const rocket=ease(l,177,236);const g1=ease(l,135,177),g2=ease(l,152,194),g3=ease(l,169,211);return <div style={{position:'absolute',inset:0,opacity}}>
  <Paper style={{left:60,top:200,width:960,height:330,zIndex:70,padding:'24px 28px',borderColor:C.orange,transform:`translateY(${26*(1-pop(l,5))}px) scale(${.95+.05*pop(l,5)})`,opacity:pop(l,5)}}>
    <JumpInText frame={l} items={[{text:'第二步：发布',color:C.orange}]} fontSize={TYPE.displayS} start={7}/>
    <div style={{fontSize:TYPE.titleXS,fontWeight:700,marginTop:8,color:C.muted}}>整理成专业开源仓库</div>
    <div style={{position:'absolute',left:150,top:124,width:280,height:136,background:'#efe3ca',border:`3px solid ${C.orange}`,borderRadius:'10px 10px 0 0'}}><div style={{position:'absolute',left:-1,right:-1,top:-24,height:24,background:C.orange,clipPath:'polygon(0 100%,10% 0,90% 0,100% 100%)'}}/><div style={{padding:'12px'}}>{['README','LICENSE','CI'].map((m,i)=><div key={m} style={{height:32,margin:'5px 0',background:C.paper,border:`2px solid ${[C.blue,C.green,C.gold][i]}`,borderRadius:6,display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyM,opacity:ease(l,44+i*22,64+i*22)}}>{m}</div>)}</div></div>
    <div style={{position:'absolute',left:34,right:34,bottom:20,height:38,background:'#eadcc1',border:`2px solid ${C.orange}`,borderRadius:10,display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyM,color:C.orange,opacity:ease(l,95,130)}}>github-oss-prep</div>
  </Paper>
  <Module name="README" color={C.blue} l={l} start={39} fromX={940} toX={230} toY={336} top={470}/>
  <Module name="LICENSE" color={C.green} l={l} start={61} fromX={940} toX={230} toY={373} top={470}/>
  <Paper style={{left:60,top:560,width:960,height:600,zIndex:72,padding:'24px 28px',borderColor:C.navy,transform:`translateY(${26*(1-pop(l,71))}px) scale(${.95+.05*pop(l,71)})`,opacity:pop(l,71)}}>
    <JumpInText frame={l} items={[{text:'第三步：运营',color:C.navy}]} fontSize={TYPE.displayS} start={91}/>
    <div style={{fontSize:TYPE.titleXS,fontWeight:700,marginTop:8,color:C.muted}}>分流 · 审查 · 按时发版</div>
    <div style={{position:'absolute',left:28,top:180,right:28,height:120}}><Gauge label="Issue 分流" color={C.orange} v={g1} x={40}/><Gauge label="PR 审查" color={C.blue} v={g2} x={398}/><Gauge label="Release" color={C.green} v={g3} x={756}/></div>
    <div style={{position:'absolute',left:28,top:360,display:'flex',alignItems:'center',gap:16,opacity:ease(l,177,208)}}>
      <div style={{display:'flex',alignItems:'center',gap:4,padding:'4px 14px',background:C.paper,border:`2px solid ${C.line}`,borderRadius:10,boxShadow:paperShadow(0.15)}}>
        <span style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.titleL,color:C.ink}}>v1.</span>
        <RollDigit fromChar="0" toChar="1" start={182} duration={13} frame={l} fontSize={TYPE.displayS} fontFamily="Space" fontWeight={700} colorFrom={C.muted} colorTo={C.green}/>
      </div>
      <div style={{display:'flex',alignItems:'center',gap:6,color:C.green,fontFamily:'Space,Kai',fontWeight:700,fontSize:TYPE.bodyM,opacity:ease(l,194,212),transform:`translateX(${10*(1-ease(l,194,212))}px)`}}>
        <CheckBadge size={24}/> 准备发版
      </div>
    </div>
    <svg width={120} height={160} style={{position:'absolute',right:40,bottom:90,transform:`translateY(${-150*rocket}px)`,opacity:ease(l,175,197)}} viewBox="0 0 120 160"><path d="M60 6 C86 40 86 88 60 120 C34 88 34 40 60 6 Z" fill={C.paper} stroke={C.red} strokeWidth={4}/><circle cx={60} cy={54} r={13} fill="#e9f1fc" stroke={C.blue} strokeWidth={3}/><path d="M40 96 L24 128 L44 116 Z" fill={C.orange} stroke={C.red} strokeWidth={3} strokeLinejoin="round"/><path d="M80 96 L96 128 L76 116 Z" fill={C.orange} stroke={C.red} strokeWidth={3} strokeLinejoin="round"/><path d="M50 120 q10 24 20 0" fill={C.gold} opacity={.9}/></svg>
    <div style={{position:'absolute',left:34,right:34,bottom:24,height:42,background:'#eadcc1',border:`2px solid ${C.navy}`,borderRadius:10,display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyM,color:C.navy,opacity:ease(l,188,217)}}>github-oss-ops</div>
  </Paper>
</div>};

const SceneSkillsP=()=>{const f=q(useCurrentFrame()),l=f-682,opacity=ease(f,662,692);const cta=ease(l,282,350);return <div style={{position:'absolute',inset:0,opacity}}>
  <div style={{position:'absolute',left:470,top:205,zIndex:75,textAlign:'center',opacity:pop(l,-27),transform:`scale(${.7+.3*pop(l,-27)})`}}><Mascot size={110} f={l} wave/><div style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.titleM,color:C.navy,marginTop:2}}>AI AGENT</div></div>
  {SKILLS.map((s,i)=>{const p=pop(l,10+i*16);const y=340+i*265;return <Paper key={s[0]} lift={.25} style={{left:60,top:y,width:960,height:250,zIndex:94,padding:'24px 28px',borderColor:s[3],opacity:p,transform:`translateY(${34*(1-p)}px) scale(${.92+.08*p})`}}>
    <div style={{position:'absolute',right:24,top:22,fontFamily:'Clash',fontWeight:600,fontSize:TYPE.titleM,color:s[3],opacity:ease(l,60+i*16,84+i*16)}}>{s[2]}</div>
    <div style={{position:'absolute',left:24,top:26,width:56,height:56,borderRadius:14,background:s[3],display:'grid',placeItems:'center',color:C.white}}><LineIcon kind={['play','project','report'][i] as IconKind} size={34} color={C.white} strokeWidth={2.2}/></div>
    <div style={{position:'absolute',left:104,top:34,fontFamily:'Space',fontWeight:600,fontSize:TYPE.titleM,color:s[3]}}>{s[0]}</div>
    <div style={{position:'absolute',left:104,top:82,fontSize:TYPE.titleXS,fontWeight:700}}>{s[1]}</div>
    <div style={{position:'absolute',left:28,bottom:22,display:'flex',alignItems:'center',gap:10,color:C.muted,fontSize:TYPE.labelL,fontWeight:700}}><CheckBadge size={26}/>智能体陪你走完</div>
  </Paper>;})}
  <Paper style={{left:50,top:1170,width:980,height:96,zIndex:96,display:'grid',placeItems:'center',borderColor:C.orange,opacity:cta,transform:`translateY(${22*(1-cta)}px) scale(${.96+.04*pop(l,286)})`}}><div style={{display:'flex',alignItems:'center',gap:16}}><JumpInText frame={l} items={[{text:'主页搜',color:C.muted,fontSize:TYPE.titleM}]} fontSize={TYPE.titleM} start={287}/><WaveText frame={l} text="github.com/hyt315" fontSize={TYPE.displayS} colorFrom="#f0b39e" colorTo={C.orange} start={291} fontFamily="Space" fontWeight={600}/></div></Paper>
</div>};

// ---- CameraRig：全局镜头层（Tibo 式推拉/聚焦）。
const CAM_KEYS_L=[
  {f:0,s:1,x:960,y:540},
  {f:48,s:1,x:960,y:540},
  {f:143,s:1.14,x:1165,y:495},
  {f:197,s:1.16,x:1185,y:505},
  {f:248,s:1.02,x:700,y:610},
  {f:328,s:1.05,x:820,y:595},
  {f:390,s:1.03,x:880,y:580},
  {f:449,s:1,x:960,y:540},
  {f:613,s:1.03,x:960,y:485},
  {f:669,s:1.02,x:960,y:500},
  {f:740,s:1,x:960,y:540},
  {f:840,s:1.14,x:1495,y:535},
  {f:950,s:1.03,x:1060,y:592},
  {f:1056,s:1,x:960,y:552},
  {f:1126,s:1,x:960,y:540},
];
// 3:4 竖屏专属镜头（画布 1080×1440，中心 540×720）：叙事焦点按竖屏布局标定
const CAM_KEYS_P=[
  {f:0,s:1,x:540,y:720},
  {f:48,s:1,x:540,y:720},
  {f:143,s:1.12,x:530,y:760},
  {f:197,s:1.14,x:530,y:765},
  {f:248,s:1.02,x:410,y:690},
  {f:328,s:1.06,x:470,y:720},
  {f:390,s:1.03,x:520,y:700},
  {f:449,s:1,x:540,y:720},
  {f:613,s:1.03,x:540,y:640},
  {f:669,s:1.02,x:540,y:680},
  {f:740,s:1,x:540,y:720},
  {f:840,s:1.06,x:540,y:560},
  {f:950,s:1.12,x:540,y:1180},
  {f:1056,s:1.05,x:540,y:980},
  {f:1126,s:1,x:540,y:720},
];
const camEase=Easing.bezier(.33,.12,.22,1);
const camAt=(f:number)=>{const K=isPortrait?CAM_KEYS_P:CAM_KEYS_L;let i=0;while(i<K.length-2&&f>K[i+1].f)i++;const a=K[i],b=K[i+1];const t=interpolate(f,[a.f,b.f],[0,1],{...clamp,easing:camEase});return {s:a.s+(b.s-a.s)*t,x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t};};
const CameraRig:React.FC<{children:React.ReactNode}>=({children})=>{
  const f=useCurrentFrame(),cw=isPortrait?1080:1920,ch=isPortrait?1440:1080;
  // Tibo 式解析滞后（跟焦感）：焦点对目标轨迹做指数加权采样，镜头慢半拍追上
  const cam=camAt(f);
  let wx=0,wy=0,ws=0;const N=14,SPAN=7;
  for(let k=0;k<N;k++){const age=k/(N-1)*SPAN;const w=Math.exp(-age/3.1);const c=camAt(f-age);wx+=c.x*w;wy+=c.y*w;ws+=w;}
  const x=wx/ws,y=wy/ws,s=cam.s,cx=cw/2,cy=ch/2;
  return <div style={{position:'absolute',left:0,top:0,width:cw,height:ch,transformOrigin:'0 0',transform:`translate(${cx-x*s}px,${cy-y*s}px) scale(${s})`}}>{children}</div>;
};

const FinalDemo=()=>{const f=q(useCurrentFrame());if(isPortrait)return <>{f<213&&<SceneWorldP/>}{f>=213&&f<416&&<SceneContributeP/>}{f>=416&&f<682&&<SceneShipP/>}{f>=682&&<SceneSkillsP/>}</>;return <>{f<213&&<SceneWorld/>}{f>=213&&f<416&&<SceneContribute/>}{f>=416&&f<682&&<SceneShip/>}{f>=682&&<SceneSkills/>}</>};

// Sound：声音也是声明式的——BGM 垫底 + 精准音效（换章 rustle、传输 whoosh、要点 tap、完成 chime、点击 click、翻牌 toggle、吸附 drop）
const Sound=()=>{
  const f=useCurrentFrame();
  const bgmVol=interpolate(f,[0,30,DURATION-45,DURATION],[0,0.08,0.08,0],{...clamp,easing:Easing.linear});
  return <>
    <Audio src={staticFile('narration.mp3')} volume={1}/>
    <Audio src={staticFile('sfx/bgm.mp3')} volume={bgmVol} loop/>
    {[4,218,420,686].map(sf=><Sequence key={`r${sf}`} from={deliveryFrame(sf)} layout="none"><Audio src={staticFile('sfx/paper-rustle.wav')} volume={.12}/></Sequence>)}
    {[53,317,593].map(sf=><Sequence key={`w${sf}`} from={deliveryFrame(sf)} layout="none"><Audio src={staticFile('sfx/data-whoosh.wav')} volume={.11}/></Sequence>)}
    {[18,90,242,317,455,477,499,718,738,758].map(sf=><Sequence key={`t${sf}`} from={deliveryFrame(sf)} layout="none"><Audio src={staticFile('sfx/paper-tap.wav')} volume={.14}/></Sequence>)}
    {[143,343,611,988].map(sf=><Sequence key={`c${sf}`} from={deliveryFrame(sf)} layout="none"><Audio src={staticFile('sfx/chime.wav')} volume={.16}/></Sequence>)}
    {[256,470,724,975].map(sf=><Sequence key={`ck${sf}`} from={deliveryFrame(sf)} layout="none"><Audio src={staticFile('sfx/click.ogg')} volume={.18}/></Sequence>)}
    {[598].map(sf=><Sequence key={`tg${sf}`} from={deliveryFrame(sf)} layout="none"><Audio src={staticFile('sfx/toggle.ogg')} volume={.20}/></Sequence>)}
    {[45,225,430,700].map(sf=><Sequence key={`dp${sf}`} from={deliveryFrame(sf)} layout="none"><Audio src={staticFile('sfx/drop.ogg')} volume={.14}/></Sequence>)}
  </>;
};

const Grade=()=> <AbsoluteFill style={{pointerEvents:'none',zIndex:190}}><AbsoluteFill style={{opacity:AESTHETIC.gradeWarmth,mixBlendMode:'soft-light',background:'radial-gradient(circle at 24% 8%,rgba(255,249,224,.9),transparent 48%),linear-gradient(180deg,rgba(255,244,216,.14),rgba(84,55,28,.08))'}}/><AbsoluteFill style={{boxShadow:`inset 0 0 150px rgba(66,42,22,${AESTHETIC.gradeVignette})`}}/></AbsoluteFill>;
const Film=()=> <AbsoluteFill style={{overflow:'hidden',background:C.paperBase}}><div style={{position:'absolute',left:0,top:0,width:MODE.designW,height:MODE.designH,transform:'scale(1.3333333333)',transformOrigin:'0 0',fontFamily:'Kai,sans-serif',color:C.ink,overflow:'hidden'}}><Fonts/><AssetGate/><CaptionFitGate/><Sound/><Background/>{CANVAS==='4:3'?<div style={{position:'absolute',left:0,top:(MODE.designH-810)/2,width:1920,height:1080,transform:'scale(0.75)',transformOrigin:'top left'}}><Chrome/><CameraRig><FinalDemo/></CameraRig></div>:<><Chrome/><CameraRig><FinalDemo/></CameraRig></>}<Grade/><Subtitle/></div></AbsoluteFill>;
const Root=()=> <Composition id="NotebookVideoFilm" component={Film} durationInFrames={DURATION} fps={FPS} width={MODE.compW} height={MODE.compH}/>;
registerRoot(Root);