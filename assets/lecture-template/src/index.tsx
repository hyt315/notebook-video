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
const MODES={
  '16:9':{compW:2560,compH:1440,designW:1920,designH:1080,subMar:188,subBottom:34,subH:112,safe:1334,subFont:44,scale:4/3},
  '4:3':{compW:1920,compH:1440,designW:1440,designH:1080,subMar:60,subBottom:34,subH:112,safe:1060,subFont:44,scale:4/3},
  '3:4':{compW:1440,compH:1920,designW:1080,designH:1440,subMar:50,subBottom:40,subH:104,safe:900,subFont:40,scale:4/3},
} as const;
type CanvasMode=keyof typeof MODES;
const CanvasContext=React.createContext<{canvas:CanvasMode;isPortrait:boolean;mode:typeof MODES['16:9']}>({
  canvas:'16:9',
  isPortrait:false,
  mode:MODES['16:9'],
});
const useCanvas=()=>React.useContext(CanvasContext);
const useCurrentFrame=()=>useRawCurrentFrame()*BASE_FPS/FPS/TIMELINE_SCALE;
const deliveryFrame=(designFrame:number)=>Math.round(designFrame*FPS*TIMELINE_SCALE/BASE_FPS);

// LOCKED AESTHETIC CORE: modern premium palette inspired by clean lecture & top SaaS motion.
const C={
  ink:'#1a1918',
  muted:'#766e65',
  blue:'#2563eb',
  blueLight:'rgba(37,99,235,0.08)',
  orange:'#d95a34',
  orangeLight:'rgba(217,90,52,0.08)',
  green:'#16a34a',
  greenLight:'rgba(22,163,74,0.08)',
  gold:'#d97706',
  red:'#dc2626',
  navy:'#1e293b',
  paper:'#ffffff',
  paperWarm:'#faf5ee',
  paperBase:'#faf7f2',
  line:'rgba(60,50,40,0.11)',
  lineOrange:'rgba(217,90,52,0.25)',
  lineBlue:'rgba(37,99,235,0.25)',
  lineGreen:'rgba(22,163,74,0.25)',
  white:'#ffffff'
};
const TYPE={displayXL:58,displayL:50,displayML:45,displayM:43,displayS:36,displayXS:34,titleXL:32,titleL:30,titleM:28,titleS:27,titleXS:26,bodyL:26,bodyM:24,bodyS:23,labelL:22,labelM:21,labelS:20,microL:18,microS:16,subtitle:44};
const AESTHETIC={subtitleSafeWidth:1334,paperRadius:16,paperOutline:1.0,textureOpacity:.012,gridOpacity:.035,gradeWarmth:.022,gradeVignette:.035};

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
const paperShadow=(lift:number)=>`0 2px 6px rgba(40,32,24,${0.04+0.04*lift}),0 ${8+12*lift}px ${20+24*lift}px rgba(40,32,24,${0.05+0.06*lift}),inset 0 1px 0 rgba(255,255,255,0.9)`;

const AssetGate=()=>{const [handle]=useState(()=>delayRender('waiting for fonts',{timeoutInMilliseconds:120000}));useEffect(()=>{let live=true;Promise.all([document.fonts.load('400 40px Kai'),document.fonts.load('700 40px Kai'),document.fonts.load('600 40px Clash'),document.fonts.load('500 40px Space'),document.fonts.load('400 40px Caveat'),document.fonts.ready]).then(()=>{if(live)continueRender(handle)}).catch(error=>{if(live)cancelRender(error)});return()=>{live=false}},[handle]);return null};

// Non-visual QA gate: measure every full cue with the real loaded font.
const CaptionFitGate=()=>{const ref=useRef<HTMLDivElement>(null),[done,setDone]=useState(false),[handle]=useState(()=>delayRender('measuring subtitle width',{timeoutInMilliseconds:60000}));useEffect(()=>{let live=true;Promise.all([document.fonts.load('400 40px Kai'),document.fonts.ready]).then(()=>requestAnimationFrame(()=>{if(!live)return;if(!ref.current){cancelRender(new Error('Subtitle measurement node is unavailable'));return}const rows=[...ref.current.querySelectorAll<HTMLElement>('[data-caption-fit]')];const overflow=rows.map((row,index)=>({index,width:row.getBoundingClientRect().width/DESIGN_SCALE,text:row.textContent||''})).filter(row=>row.width>AESTHETIC.subtitleSafeWidth+.5);if(overflow.length){cancelRender(new Error(`Subtitle overflow: ${overflow.map(x=>`#${x.index+1} ${Math.ceil(x.width)}px ${x.text}`).join(' | ')}`));return}setDone(true);continueRender(handle)})).catch(error=>{if(live)cancelRender(error)});return()=>{live=false}},[handle]);if(done)return null;return <div ref={ref} style={{position:'absolute',left:-10000,top:-10000,visibility:'hidden',fontFamily:'Kai,sans-serif',fontSize:44,fontWeight:400,whiteSpace:'nowrap',letterSpacing:1.2}}>{captions.map((cue:any,index:number)=><span key={index} data-caption-fit style={{display:'block',width:'max-content'}}>{String(cue.text).replace(/[，。！？；：、,.!?;:\s]+$/g,'')}</span>)}</div>};

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
@font-face{font-family:Caveat;src:url(${staticFile('fonts/Caveat-Latin.woff2')}) format('woff2');font-weight:400 700}
*{box-sizing:border-box}html,body{margin:0;background:${C.paperBase}}body{font-family:Kai,'Segoe UI',sans-serif;-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}
`}</style>;

const Background=()=> <>
  <AbsoluteFill style={{background:C.paperBase}}/>
  <div style={{position:'absolute',left:60,top:50,right:60,bottom:50,backgroundImage:`repeating-linear-gradient(0deg,transparent 0 53px,rgba(90,75,60,${AESTHETIC.gridOpacity}) 54px),repeating-linear-gradient(90deg,transparent 0 53px,rgba(90,75,60,${AESTHETIC.gridOpacity}) 54px),radial-gradient(circle at 20% 10%,rgba(255,255,255,0.7),transparent 45%),radial-gradient(circle at 80% 85%,rgba(217,90,52,0.04),transparent 50%)`}}/>
  <AbsoluteFill style={{opacity:AESTHETIC.textureOpacity,mixBlendMode:'multiply',backgroundImage:'radial-gradient(#30251a 0.5px,transparent .7px)',backgroundSize:'8px 8px'}}/>
</>;

// ---- 可复用组件库 -------------------------------------------
const PillTag:React.FC<{text:string;color?:string;bg?:string;fontSize?:number;fontFamily?:string;fontWeight?:number|string;style?:React.CSSProperties}>=({text,color=C.orange,bg=C.orangeLight,fontSize=TYPE.microS,fontFamily='Space,Kai',fontWeight=700,style})=>{
  return <span style={{display:'inline-flex',alignItems:'center',padding:'4px 12px',borderRadius:999,background:bg,color,fontSize,fontFamily,fontWeight,letterSpacing:0.8,border:`1px solid ${color}2a`,...style}}>{text}</span>;
};

// Paper：现代通透纯白卡片容器。
const Paper:React.FC<{children:React.ReactNode;style?:React.CSSProperties;lift?:number;borderColor?:string}>=({children,style,lift=0,borderColor})=> <div style={{position:'absolute',backgroundColor:C.paper,backgroundImage:'radial-gradient(circle at 18% 9%,rgba(255,255,255,0.9),transparent 36%),linear-gradient(175deg,#ffffff 0%,#fdfbf8 100%)',border:`${AESTHETIC.paperOutline}px solid ${borderColor||C.line}`,borderRadius:AESTHETIC.paperRadius,color:C.ink,boxShadow:paperShadow(lift),...style}}>{children}</div>;

type IconKind='check'|'play'|'project'|'report';
const LineIcon:React.FC<{kind:IconKind,size?:number,color?:string,strokeWidth?:number}>=({kind,size=28,color='currentColor',strokeWidth=2.2})=>{const common={fill:'none',stroke:color,strokeWidth,strokeLinecap:'round' as const,strokeLinejoin:'round' as const};return <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">{kind==='check'&&<path {...common} d="M7 16.5l5.6 5.5L25 9.8"/>}{kind==='play'&&<><rect {...common} x="5" y="6" width="22" height="20" rx="3"/><path {...common} d="M13 11.5l8 4.5-8 4.5z"/></>}{kind==='project'&&<><rect {...common} x="6" y="7" width="20" height="18" rx="2.5"/><path {...common} d="M10 12h12M10 16h8M10 20h6"/></>}{kind==='report'&&<><path {...common} d="M9 5h10l5 5v17H9z"/><path {...common} d="M19 5v6h5M13 16h7M13 20h7"/></>}</svg>};
const CheckBadge:React.FC<{size?:number}>=({size=30})=><span style={{width:size,height:size,borderRadius:999,background:C.green,color:C.white,display:'inline-grid',placeItems:'center',flex:'0 0 auto',boxShadow:'0 2px 8px rgba(22,163,74,0.3)'}}><LineIcon kind="check" size={size*.62} color={C.white} strokeWidth={2.7}/></span>;

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

const smoothStep=(v:number)=>{const t=Math.max(0,Math.min(1,v));return t*t*(3-2*t)};

// JumpInText：完全移植 Tibo 源码的“4段双轴弹性波浪回弹 + 字色激活”动效（经视效平衡调谐）
const JumpInText:React.FC<{
  items:{text:string;color?:string;colorActive?:string;fontFamily?:string;fontSize?:number;fontWeight?:number|string;letterSpacing?:number}[];
  fontSize:number;
  fontWeight?:number|string;
  start:number;
  stagger?:number;
  letterSpacing?:number;
  style?:React.CSSProperties;
  frame?:number;
}>=({items,fontSize,fontWeight=700,start,stagger=1.2,letterSpacing=0,style,frame})=>{
  const f=frame??q(useCurrentFrame());
  let seq=0;
  return <div style={{display:'inline-flex',flexWrap:'wrap',justifyContent:'center',alignItems:'baseline',perspective:1000,...style}}>
    {items.map((seg,si)=>String(seg.text).split('').map((ch,ci)=>{
      const globalIdx=seq++;
      const letterStart=start+globalIdx*stagger;
      const age=f-letterStart;
      const waveProgress=smoothStep(age/7.5);
      const waveY=interpolate(waveProgress,[0,0.28,0.64,1],[14,-6,1.5,0]);
      const waveX=interpolate(waveProgress,[0,0.28,0.64,1],[3,-1,0,0]);
      const rotX=interpolate(waveProgress,[0,0.35,1],[40,-5,0]);
      const targetColor=seg.color||C.ink;
      const activeColor=seg.colorActive||(seg.color===C.ink?C.orange:seg.color||C.blue);
      const colorProgress=smoothStep(age/5.5);
      const charColor=interpolateColors(colorProgress,[0,1],[activeColor,targetColor]);
      const opacity=smoothStep((age+0.45)/1.4);
      return <span key={`${si}-${ci}`} style={{display:'inline-block',fontSize:seg.fontSize||fontSize,fontWeight:seg.fontWeight||fontWeight,fontFamily:seg.fontFamily||'inherit',letterSpacing:seg.letterSpacing??letterSpacing,color:charColor,opacity,transform:`translate(${waveX}px,${waveY}px) rotateX(${rotX}deg)`,transformOrigin:'50% 100%'}}>{ch===' '?'\u00a0':ch}</span>;
    }))}
  </div>;
};

// WaveText：Tibo 式字母波浪打字——每字母 4 段关键帧波浪 + 颜色渐变
const WaveText:React.FC<{text:string;fontSize:number;colorFrom:string;colorTo:string;start:number;stagger?:number;frame?:number;fontFamily?:string;fontWeight?:number;letterSpacing?:number;style?:React.CSSProperties}>=({text,fontSize,colorFrom,colorTo,start,stagger=1.2,frame,fontFamily,fontWeight=600,letterSpacing=0,style})=>{
  const f=frame??q(useCurrentFrame());
  return <div style={{display:'flex',justifyContent:'center',alignItems:'baseline',...style}}>
    {text.split('').map((ch,i)=>{const age=f-(start+i*stagger);const wave=smoothStep(age/10),col=interpolateColors(smoothStep(age/8),[0,1],[colorFrom,colorTo]);const wx=interpolate(wave,[.0,.28,.64,1],[10,-3,1,0]);const wy=interpolate(wave,[.0,.28,.64,1],[16,-16,4,0]);return <span key={i} style={{display:'inline-block',fontSize,fontFamily,fontWeight,letterSpacing,color:col,opacity:smoothStep((age+0.4)/1.5),transform:`translate(${wx}px,${wy}px)`}}>{ch}</span>})}
  </div>;
};

const cleanTail=(s:string)=>s.replace(/[，。！？；：、,.!?;:\s]+$/g,'');
const Subtitle=()=>{
  const {mode}=useCanvas();
  const f=useRawCurrentFrame(),lead=Math.round(FPS*.18),hold=Math.round(FPS*.05);
  let cue=captions.find((c:any)=>f>=c.startFrame-lead&&f<=c.endFrame+hold);
  if(!cue)cue=[...captions].reverse().find((c:any)=>c.startFrame<=f);
  const full=cue?cleanTail(cue.text):'';
  const words=cue?cue.words.filter((w:any)=>w.startFrame<=f+lead):[];
  return <div style={{position:'absolute',left:mode.subMar,right:mode.subMar,bottom:20,zIndex:200,display:'grid',placeItems:'center'}}>
    <div style={{width:mode.safe,display:'grid',placeItems:'center',fontFamily:'Kai',fontSize:mode.subFont,lineHeight:1.18,letterSpacing:1.6,color:C.ink,textShadow:'0 1px 4px rgba(255,255,255,0.8), 0 2px 10px rgba(40,30,20,0.15)',whiteSpace:'nowrap'}}>
      <span style={{position:'relative'}}>
        <span style={{visibility:'hidden'}}>{full}</span>
        <span style={{position:'absolute',left:0,top:0}}>
          {words.map((w:any,wi:number)=>{
            const part=String(w.part);
            const prev=wi>0?String(words[wi-1].part):'';
            const spaced=(wi>0&&!/[\s，。！？；：、,.!?;:（(]$/.test(prev)&&!/^[\s，。！？；：、,.!?;:）)]/.test(part)&&!((/[A-Za-z0-9]$/.test(prev)&&/^[A-Za-z0-9]/.test(part))||(/[一-鿿]$/.test(prev)&&/^[一-鿿]/.test(part))))?'\u00a0':'';
            return <span key={wi} style={{display:'inline-block'}}>{spaced}{part.split('').map((ch:any,ci:number)=>{
              const p=interpolate(f,[w.startFrame+ci*.9,w.startFrame+ci*.9+2.5],[0,1],{...clamp,easing:Easing.bezier(.16,1,.3,1)});
              return <span key={ci} style={{display:'inline-block',opacity:p,transform:`translateY(${6*(1-p)}px)`}}>{ch}</span>;
            })}</span>;
          })}
        </span>
      </span>
    </div>
  </div>;
};

const Chrome=()=>{
  const {isPortrait}=useCanvas();
  const f=q(useCurrentFrame()),stage=f<213?0:f<416?1:f<682?2:3,starts=[0,213,416,682],local=f-starts[stage],p=pop(local,-8),titles=COPY.chapterTitles;
  return <>
    <Paper lift={0.3} style={{left:isPortrait?40:92,top:isPortrait?80:74,width:isPortrait?330:392,height:isPortrait?76:82,zIndex:150,display:'flex',alignItems:'center',opacity:p,transform:`translateY(${14*(1-p)}px) scale(${.96+.04*p})`,overflow:'hidden',padding:0}}>
      <div style={{width:isPortrait?60:72,height:'100%',background:`linear-gradient(135deg,${C.orange},#e8704c)`,color:C.white,display:'grid',placeItems:'center',fontFamily:'Clash',fontWeight:600,fontSize:isPortrait?28:31,boxShadow:'inset -2px 0 6px rgba(0,0,0,0.1)'}}>{String(stage+1).padStart(2,'0')}</div>
      <div style={{padding:isPortrait?'8px 14px':'10px 18px',flex:1}}>
        <div style={{display:'flex',alignItems:'center',gap:6}}>
          <PillTag text={COPY.chromeKicker} color={C.blue} bg={C.blueLight} fontSize={TYPE.microS}/>
        </div>
        <JumpInText key={stage} items={[{text:titles[stage]}]} fontSize={TYPE.titleS} start={starts[stage]+8} stagger={1.1} style={{marginTop:3,justifyContent:'flex-start'}}/>
      </div>
    </Paper>
    <div style={{position:'absolute',right:isPortrait?40:88,top:isPortrait?76:70,zIndex:140,textAlign:'right'}}>
      <div style={{fontSize:TYPE.labelM,fontWeight:700,letterSpacing:4,color:C.blue,fontFamily:'Clash,Space'}}>{COPY.header}</div>
      <div style={{fontSize:TYPE.microL,marginTop:6,color:C.muted,fontFamily:'Space,Kai'}}>{COPY.headerSub}</div>
    </div>
  </>;
};

const stageFade=(f:number,start:number,end:number)=>ease(f,start,start+15)*ease(f,end-15,end,1,0);

// ---- 场景内容层 -----------------------------------
// SCENE 1 — code is lonely -> GitHub collaborative world (0 ~ 212 frames)
const NODES=[{x:250,y:150,c:C.orange,label:'仓库'},{x:930,y:120,c:C.gold,label:'Star'},{x:1000,y:360,c:C.green,label:'Fork'},{x:210,y:410,c:C.blue,label:'Issue'},{x:600,y:470,c:C.red,label:'PR'}];
const SceneWorld=()=>{
  const f=q(useCurrentFrame()),l=f;
  if(f>212) return null;
  const opacity=stageFade(f,0,205);
  const dim=ease(l,51,92,1,.42),roll=easeOutSoft(l,45,78),rollS=interpolate(roll,[0,.5,.82,1],[.82,1.06,.98,1]),rollR=interpolate(roll,[0,1],[150,360]),rollO=ease(l,43,62);
  return <div style={{position:'absolute',inset:0,opacity}}>
    {/* 右侧几何大切角舞台背板 */}
    <div style={{position:'absolute',left:560,top:170,width:1220,height:620,borderRadius:28,background:'linear-gradient(145deg,rgba(255,255,255,0.85),rgba(244,238,230,0.45))',border:`1px solid ${C.line}`,boxShadow:paperShadow(0.1),opacity:rollO}}/>
    
    <Paper lift={0.2} borderColor={C.muted} style={{left:120,top:300,width:350,height:260,zIndex:60,padding:'26px 28px',opacity:dim,transform:`translateY(${26*(1-pop(l,4))}px) scale(${.94+.06*pop(l,4)})`}}>
      <div style={{display:'flex',alignItems:'center',gap:8}}>
        <PillTag text="LOCAL HOST" color={C.muted} bg="rgba(118,110,101,0.1)"/>
        <span style={{fontFamily:'Caveat',fontSize:20,color:C.orange,transform:'rotate(-4deg)'}}>lonely code</span>
      </div>
      <JumpInText frame={l} items={[{text:'本地硬盘',color:C.ink,colorActive:C.orange}]} fontSize={TYPE.displayS} start={7} style={{justifyContent:'flex-start',marginTop:8}}/>
      <div style={{fontSize:TYPE.bodyM,fontWeight:700,marginTop:6,color:C.muted}}>代码只躺在你电脑里</div>
      <div style={{position:'absolute',left:28,right:28,top:136,bottom:24}}>
        {[0,1,2,3].map(i=><div key={i} style={{height:10,margin:'10px 0',width:`${76-i*11}%`,background:i===0?C.orange:'rgba(118,110,101,0.18)',borderRadius:4,opacity:pop(l,12+i*6)}}/>)}
      </div>
    </Paper>
    
    <div style={{position:'absolute',left:490,top:405,fontSize:60,color:C.orange,zIndex:75,opacity:ease(l,42,60),transform:`translateX(${-14*(1-ease(l,42,60))}px)`}}>→</div>
    
    <div style={{position:'absolute',left:600,top:200,width:1160,height:600,zIndex:72,opacity:rollO,transform:`rotate(${rollR}deg) scale(${rollS})`,transformOrigin:'50% 50%'}}>
      <svg width={1160} height={600} viewBox="0 0 1160 600" style={{overflow:'visible'}}>
        <circle cx={580} cy={300} r={140} fill="#eef5fc" stroke={C.blue} strokeWidth={3.5} opacity={0.95}/>
        <ellipse cx={580} cy={300} rx={56} ry={140} fill="none" stroke={C.blue} strokeWidth={1.8} opacity={.45}/>
        <ellipse cx={580} cy={300} rx={110} ry={140} fill="none" stroke={C.blue} strokeWidth={1.8} opacity={.3}/>
        <line x1={440} y1={300} x2={720} y2={300} stroke={C.blue} strokeWidth={1.8} opacity={.45}/>
        <path d="M520 250 q30 -26 66 -6 q34 -16 52 14 q-10 34 -48 26 q-30 20 -60 -8 q-16 -30 -10 -26" fill={C.green} opacity={.22}/>
        {NODES.map((n,i)=>{const app=ease(l,72+i*9,98+i*9);const mx=(580+n.x)/2,my=(300+n.y)/2-46;return <g key={i} opacity={app}>
          <path d={`M580 300 Q${mx} ${my} ${n.x} ${n.y}`} fill="none" stroke={n.c} strokeWidth={2.8} strokeDasharray="8 8" strokeDashoffset={-l*3.2}/>
          <g transform={`scale(${.6+.4*pop(l,65+i*9)})`} style={{transformBox:'fill-box',transformOrigin:'center'} as any}>
            <rect x={n.x-42} y={n.y-32} width={84} height={64} rx={12} fill={C.paper} stroke={n.c} strokeWidth={2.4} style={{boxShadow:paperShadow(0.2)} as any}/>
            <rect x={n.x-42} y={n.y-32} width={84} height={14} rx={12} fill={n.c} opacity={.9}/>
          </g>
        </g>;})}
      </svg>
      {NODES.map((n,i)=><div key={i} style={{position:'absolute',left:n.x-42,top:n.y-6,width:84,textAlign:'center',fontFamily:'Space,Kai',fontWeight:700,fontSize:TYPE.bodyM,color:n.c,opacity:ease(l,84+i*9,104+i*9)}}>{n.label}</div>)}
      <div style={{position:'absolute',left:512,top:286,color:C.blue,fontFamily:'Clash',fontWeight:600,fontSize:TYPE.microL,letterSpacing:1.5}}>GitHub</div>
    </div>
    
    <div style={{position:'absolute',left:150,top:595,zIndex:96,opacity:ease(l,95,117),transform:`translateY(${20*(1-ease(l,95,117))}px)`}}><Mascot size={150} f={l} wave/></div>
    
    <Paper lift={0.3} borderColor={C.green} style={{left:560,top:748,width:840,height:88,zIndex:85,display:'flex',alignItems:'center',justifyContent:'center',gap:12,opacity:ease(l,124,143),transform:`translateY(${18*(1-pop(l,124))}px)`}}>
      <PillTag text="GLOBAL OPEN SOURCE" color={C.green} bg={C.greenLight}/>
      <JumpInText frame={l} items={[{text:'全世界的开发者，',color:C.ink,colorActive:C.green},{text:'一起造软件',color:C.green,colorActive:C.orange}]} fontSize={TYPE.titleL} start={125}/>
    </Paper>
  </div>;
};

// SCENE 2 — step one: contribute a PR (213 ~ 414 frames, clean exit before 414)
const StepRail:React.FC<{active:number;l:number;start:number}>=({active,l,start})=>{
  const steps=[['01','参与',C.orange],['02','发布',C.blue],['03','运营',C.green]] as const;
  return <div style={{position:'absolute',left:360,top:180,width:1200,height:72,zIndex:78,display:'flex',gap:24,justifyContent:'center'}}>
    {steps.map((s,i)=>{const on=i===active,p=pop(l,start+i*7);
      return <div key={s[0]} style={{width:360,height:68,display:'flex',alignItems:'center',gap:16,padding:'0 24px',background:on?C.paper:'rgba(255,255,255,0.6)',border:`${on?2.4:1.2}px solid ${on?s[2]:C.line}`,borderRadius:14,boxShadow:on?paperShadow(0.3):'none',opacity:p,transform:`translateY(${16*(1-p)}px) scale(${on?1:.96})`}}>
        <span style={{width:36,height:36,borderRadius:99,background:on?s[2]:'rgba(118,110,101,0.2)',color:C.white,display:'grid',placeItems:'center',fontFamily:'Clash',fontWeight:600,fontSize:20}}>{s[0]}</span>
        <span style={{fontFamily:'Kai',fontWeight:700,fontSize:TYPE.titleM,color:on?s[2]:C.muted}}>{s[1]}</span>
      </div>;
    })}
  </div>;
};

const SceneContribute=()=>{
  const f=q(useCurrentFrame()),l=f-213;
  if(f<210||f>414) return null; // 严格区间硬隔离，杜绝 14 秒重叠！
  const intro=ease(f,213,228);
  const outro=ease(f,396,412,1,0); // 396~412 帧干净淡出
  const exitSlide=ease(f,396,412,0,36); // 退出时向左微滑
  const opacity=intro*outro;
  const t=easeOutSoft(l,43,113);const merge=ease(l,105,134);const cardX=180+560*Math.min(1,t/0.72);
  const steps=['读懂项目规则','建立最小改动','提交你的 PR','通过 CI 与评审'];
  return <div style={{position:'absolute',inset:0,opacity,transform:`translateX(${-exitSlide}px)`}}>
    <StepRail active={0} l={l} start={6}/>
    <svg width="1920" height="1080" style={{position:'absolute',inset:0,zIndex:55}}>
      <path d="M150 560 H1080" fill="none" stroke="rgba(37,99,235,0.25)" strokeWidth={7} strokeLinecap="round"/>
      <path d="M150 700 H760 Q840 700 880 620 L910 566" fill="none" stroke={C.orange} strokeWidth={6} strokeDasharray="14 10" strokeDashoffset={-l*4} opacity={.95}/>
      <text x="150" y="534" fill={C.blue} fontFamily="Space,Kai" fontWeight="600" fontSize="28">main 主干</text>
      <text x="150" y="742" fill={C.orange} fontFamily="Space,Kai" fontWeight="600" fontSize="28">你的分支</text>
      <circle cx={910} cy={562} r={14} fill={merge>.4?C.green:'#d8d0c4'} opacity={ease(l,99,120)} style={{filter:'drop-shadow(0 2px 6px rgba(0,0,0,0.15))'}}/>
    </svg>
    
    <Paper lift={Math.sin(Math.PI*t)*.4+0.1} borderColor={C.orange} style={{left:cardX,top:648,width:210,height:96,zIndex:96,padding:'16px 18px',opacity:ease(l,39,56)*ease(l,130,142,1,0),transform:`translateY(${-90*Math.sin(Math.PI*t)*(cardX<700?1:.4)}px)`}}>
      <div style={{fontFamily:'Kai',fontWeight:700,fontSize:TYPE.titleS,color:C.orange}}>你的修改</div>
      <div style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.labelL,marginTop:6,color:C.muted}}>commit</div>
    </Paper>
    
    <Paper lift={.4} borderColor={C.green} style={{left:840,top:426,width:260,height:112,zIndex:94,padding:'16px 20px',opacity:merge,transform:`scale(${.7+.3*pop(l,109)})`}}>
      <div style={{display:'flex',alignItems:'center',gap:12}}>
        <span style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.titleM,color:C.green}}>Pull Request</span>
      </div>
      <div style={{fontSize:TYPE.labelL,fontWeight:700,marginTop:8,color:C.muted}}>把改动交给项目</div>
      <div style={{position:'absolute',right:16,top:16,transform:`scale(${pop(l,130)})`}}><CheckBadge size={30}/></div>
    </Paper>
    
    <Paper lift={0.25} borderColor={C.blue} style={{left:1180,top:290,width:590,height:440,zIndex:76,padding:'34px 40px',transform:`translateX(${40*(1-pop(l,9))}px)`,opacity:pop(l,9)}}>
      <div style={{display:'flex',alignItems:'center',gap:8}}>
        <PillTag text="EP 1 · CONTRIBUTE" color={C.blue} bg={C.blueLight}/>
        <span style={{fontFamily:'Caveat',fontSize:20,color:C.blue,transform:'rotate(-2deg)'}}>start small</span>
      </div>
      <JumpInText frame={l} items={[{text:'第一步：参与开源',color:C.blue,colorActive:C.orange}]} fontSize={TYPE.displayS} start={11} style={{justifyContent:'flex-start',marginTop:8}}/>
      <div style={{position:'absolute',left:40,right:40,top:126,bottom:100}}>
        {steps.map((s,i)=>{const p=pop(l,39+i*20);
          return <div key={s} style={{display:'flex',alignItems:'center',gap:16,height:48,marginBottom:8,opacity:p,transform:`translateX(${24*(1-p)}px)`}}>
            <span style={{width:38,height:38,borderRadius:99,background:[C.orange,C.blue,C.green,C.gold][i],color:C.white,display:'grid',placeItems:'center',fontFamily:'Clash',fontWeight:600,fontSize:19}}>{i+1}</span>
            <span style={{fontSize:TYPE.titleXS,fontWeight:700}}>{s}</span>
          </div>;
        })}
      </div>
      <div style={{position:'absolute',left:40,right:40,bottom:32,height:44,background:C.greenLight,border:`1.5px solid ${C.green}`,borderRadius:12,display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyL,color:C.green,letterSpacing:1,opacity:ease(l,120,140)}}>
        github-oss-contribute
      </div>
    </Paper>
  </div>;
};

// SCENE 3 — step two & three: prep and operate (416 ~ 680 frames, absolute 0 overlap)
const Gauge:React.FC<{label:string;color:string;v:number;x:number}>=({label,color,v,x})=> <div style={{position:'absolute',left:x,top:0,width:130,textAlign:'center'}}>
  <svg width={110} height={70} viewBox="0 0 110 70">
    <path d="M12 62 A43 43 0 0 1 98 62" fill="none" stroke="rgba(60,50,40,0.12)" strokeWidth={8} strokeLinecap="round"/>
    <path d="M12 62 A43 43 0 0 1 98 62" fill="none" stroke={color} strokeWidth={8} strokeLinecap="round" strokeDasharray={135} strokeDashoffset={135*(1-v)}/>
  </svg>
  <div style={{fontSize:TYPE.labelL,fontWeight:700,marginTop:2,color:C.ink}}>{label}</div>
</div>;

const SceneShip=()=>{
  const f=q(useCurrentFrame()),l=f-416;
  if(f<415||f>680) return null; // 严格在 416 帧才挂载，彻底消灭 14 秒重叠！
  const intro=ease(f,416,432);
  const outro=ease(f,660,676,1,0);
  const exitSlide=ease(f,660,676,0,36);
  const opacity=intro*outro;
  const ver=ease(l,177,219);const rocket=easeOutSoft(l,177,236);
  const g1=ease(l,135,177),g2=ease(l,152,194),g3=ease(l,169,211);

  const stdFiles=[
    {name:'README.md',desc:'完整说明文档',color:C.blue,start:24},
    {name:'LICENSE',desc:'开源协议授权',color:C.green,start:48},
    {name:'CI / Actions',desc:'自动化质量门禁',color:C.gold,start:72},
  ];

  return <div style={{position:'absolute',inset:0,opacity,transform:`translateX(${-exitSlide}px)`}}>
    <Paper lift={0.2} borderColor={C.orange} style={{left:120,top:250,width:560,height:470,zIndex:70,padding:'26px 32px',transform:`translateY(${26*(1-pop(l,5))}px) scale(${.95+.05*pop(l,5)})`,opacity:pop(l,5)}}>
      <div style={{display:'flex',alignItems:'center',gap:8}}>
        <PillTag text="EP 2 · PREP" color={C.orange} bg={C.orangeLight}/>
        <span style={{fontFamily:'Caveat',fontSize:20,color:C.orange,transform:'rotate(3deg)'}}>packaging</span>
      </div>
      <JumpInText frame={l} items={[{text:'第二步：发布',color:C.orange,colorActive:C.blue}]} fontSize={TYPE.displayS} start={7} style={{justifyContent:'flex-start',marginTop:4,whiteSpace:'nowrap'}}/>
      <div style={{fontSize:TYPE.titleXS,fontWeight:700,marginTop:4,color:C.muted}}>整理成专业开源仓库</div>
      
      {/* 标准化文件仓库容器（平滑依次滑入点亮，彻底消除 16 秒瞬闪） */}
      <div style={{position:'absolute',left:40,right:40,top:148,height:218,background:'rgba(255,255,255,0.75)',border:`1.5px solid ${C.orange}`,borderRadius:'14px',boxShadow:paperShadow(0.12),overflow:'hidden'}}>
        <div style={{height:30,background:C.orange,display:'flex',alignItems:'center',paddingLeft:16}}>
          <span style={{fontFamily:'Space',color:C.white,fontWeight:700,fontSize:13,letterSpacing:1}}>STANDARDIZED TEMPLATE</span>
        </div>
        <div style={{padding:'8px 16px',display:'flex',flexDirection:'column',gap:6}}>
          {stdFiles.map((item,i)=>{
            const p=pop(l,item.start);
            return <div key={item.name} style={{height:46,background:C.paper,border:`1.5px solid ${item.color}`,borderRadius:10,display:'flex',alignItems:'center',justifyContent:'space-between',padding:'0 16px',boxShadow:paperShadow(0.15),opacity:p,transform:`translateX(${20*(1-p)}px) scale(${.96+.04*p})`}}>
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <span style={{width:10,height:10,borderRadius:99,background:item.color}}/>
                <span style={{fontFamily:'Space',fontWeight:700,fontSize:TYPE.bodyM,color:C.ink}}>{item.name}</span>
                <span style={{fontSize:TYPE.labelM,fontWeight:600,color:C.muted}}>({item.desc})</span>
              </div>
              <span style={{fontFamily:'Space',fontSize:12,fontWeight:700,color:item.color,background:`${item.color}15`,padding:'2px 8px',borderRadius:6}}>READY</span>
            </div>;
          })}
        </div>
      </div>
      <div style={{position:'absolute',left:34,right:34,bottom:24,height:40,background:C.orangeLight,border:`1.5px solid ${C.orange}`,borderRadius:12,display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyM,color:C.orange,opacity:ease(l,95,130)}}>
        github-oss-prep
      </div>
    </Paper>
    
    <Paper lift={0.25} borderColor={C.navy} style={{left:740,top:250,width:1020,height:470,zIndex:72,padding:'26px 36px',transform:`translateY(${26*(1-pop(l,89))}px) scale(${.95+.05*pop(l,89)})`,opacity:pop(l,89)}}>
      <div style={{display:'flex',alignItems:'center',gap:8}}>
        <PillTag text="EP 3 · OPS" color={C.blue} bg={C.blueLight}/>
        <span style={{fontFamily:'Caveat',fontSize:20,color:C.blue,transform:'rotate(-2deg)'}}>ongoing triage</span>
      </div>
      <JumpInText frame={l} items={[{text:'第三步：运营',color:C.navy,colorActive:C.green}]} fontSize={TYPE.displayS} start={96} style={{justifyContent:'flex-start',marginTop:4,whiteSpace:'nowrap'}}/>
      <div style={{fontSize:TYPE.titleXS,fontWeight:700,marginTop:4,color:C.muted}}>分流 · 审查 · 按时发版</div>
      
      <div style={{position:'absolute',left:60,top:140,right:60,height:120}}>
        <Gauge label="Issue 分流" color={C.orange} v={g1} x={20}/>
        <Gauge label="PR 审查" color={C.blue} v={g2} x={330}/>
        <Gauge label="Release" color={C.green} v={g3} x={640}/>
      </div>
      
      <div style={{position:'absolute',left:60,bottom:110,display:'flex',alignItems:'center',gap:16,opacity:ease(l,177,208)}}>
        <div style={{display:'flex',alignItems:'center',gap:4,padding:'6px 16px',background:C.paper,border:`1.5px solid ${C.line}`,borderRadius:12,boxShadow:paperShadow(0.2)}}>
          <span style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.titleL,color:C.ink}}>v1.</span>
          <RollDigit fromChar="0" toChar="1" start={182} duration={13} frame={l} fontSize={TYPE.displayS} fontFamily="Space" fontWeight={700} colorFrom={C.muted} colorTo={C.green}/>
        </div>
        <div style={{display:'flex',alignItems:'center',gap:6,color:C.green,fontFamily:'Space,Kai',fontWeight:700,fontSize:TYPE.bodyM,opacity:ease(l,194,212),transform:`translateX(${10*(1-ease(l,194,212))}px)`}}>
          <CheckBadge size={26}/> 准备发版
        </div>
      </div>
      
      <svg width={120} height={160} style={{position:'absolute',right:70,bottom:60,transform:`translateY(${-150*rocket}px)`,opacity:ease(l,175,197)}} viewBox="0 0 120 160">
        <path d="M60 6 C86 40 86 88 60 120 C34 88 34 40 60 6 Z" fill={C.paper} stroke={C.red} strokeWidth={3.5}/>
        <circle cx={60} cy={54} r={13} fill="#eef5fc" stroke={C.blue} strokeWidth={2.8}/>
        <path d="M40 96 L24 128 L44 116 Z" fill={C.orange} stroke={C.red} strokeWidth={2.8} strokeLinejoin="round"/>
        <path d="M80 96 L96 128 L76 116 Z" fill={C.orange} stroke={C.red} strokeWidth={2.8} strokeLinejoin="round"/>
        <path d="M50 120 q10 24 20 0" fill={C.gold} opacity={.9}/>
      </svg>
      
      <div style={{position:'absolute',left:40,right:40,bottom:24,height:40,background:C.blueLight,border:`1.5px solid ${C.navy}`,borderRadius:12,display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyM,color:C.navy,opacity:ease(l,188,217)}}>
        github-oss-ops
      </div>
    </Paper>
  </div>;
};

// SCENE 4 — three AI skills + CTA (682 ~ 1126 frames)
const SKILLS=[['github-oss-contribute','参与别人的项目','EP 1',C.orange],['github-oss-prep','发布自己的作品','EP 2',C.blue],['github-oss-ops','运营与持续发版','EP 3',C.green]] as const;
const SceneSkills=()=>{
  const f=q(useCurrentFrame()),l=f-682;
  if(f<680) return null;
  const opacity=ease(f,682,698);
  const cta=ease(l,282,350);
  return <div style={{position:'absolute',inset:0,opacity}}>
    <div style={{position:'absolute',left:860,top:205,zIndex:75,textAlign:'center',opacity:pop(l,5),transform:`scale(${.7+.3*pop(l,5)})`}}>
      <Mascot size={150} f={l} wave/>
      <div style={{fontFamily:'Space',fontWeight:700,fontSize:TYPE.titleM,color:C.navy,marginTop:4,letterSpacing:3}}>AI AGENT</div>
      <div style={{fontFamily:'Caveat',fontSize:22,color:C.orange,marginTop:2}}>always by your side</div>
    </div>
    
    {SKILLS.map((s,i)=>{
      const p=pop(l,36+i*16);const x=200+i*530;
      return <Paper key={s[0]} lift={.3} borderColor={s[3]} style={{left:x,top:410,width:470,height:256,zIndex:94,padding:'28px 30px',opacity:p,transform:`translateY(${34*(1-p)}px) scale(${.92+.08*p})`}}>
        <div style={{position:'absolute',right:24,top:24}}>
          <PillTag text={s[2]} color={s[3]} bg={`${s[3]}18`} fontSize={TYPE.labelS}/>
        </div>
        <div style={{width:56,height:56,borderRadius:16,background:s[3],display:'grid',placeItems:'center',color:C.white,boxShadow:`0 4px 14px ${s[3]}40`}}>
          <LineIcon kind={['play','project','report'][i] as IconKind} size={32} color={C.white} strokeWidth={2.4}/>
        </div>
        <div style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.titleM,color:s[3],marginTop:16}}>{s[0]}</div>
        <div style={{fontSize:TYPE.titleXS,fontWeight:700,marginTop:10}}>{s[1]}</div>
        <div style={{position:'absolute',left:30,bottom:24,display:'flex',alignItems:'center',gap:10,color:C.muted,fontSize:TYPE.labelL,fontWeight:700}}>
          <CheckBadge size={26}/>智能体陪你走完
        </div>
      </Paper>;
    })}
    
    <Paper lift={0.4} borderColor={C.orange} style={{left:460,top:724,width:1000,height:104,zIndex:96,display:'grid',placeItems:'center',opacity:cta,transform:`translateY(${22*(1-cta)}px) scale(${.96+.04*pop(l,286)})`}}>
      <div style={{display:'flex',alignItems:'center',gap:16}}>
        <JumpInText frame={l} items={[{text:'主页搜',color:C.muted,fontSize:TYPE.titleM}]} fontSize={TYPE.titleM} start={287}/>
        <WaveText frame={l} text="github.com/hyt315" fontSize={TYPE.displayS} colorFrom="#f09070" colorTo={C.orange} start={291} fontFamily="Space" fontWeight={700}/>
      </div>
    </Paper>
  </div>;
};

// ---- 3:4 portrait scene set (single-column stacking) -------------
const StepRailP:React.FC<{active:number;l:number;start:number}>=({active,l,start})=>{
  const steps=[['01','参与',C.orange],['02','发布',C.blue],['03','运营',C.green]] as const;
  return <div style={{position:'absolute',left:70,top:190,width:940,height:68,zIndex:78,display:'flex',gap:20,justifyContent:'center'}}>
    {steps.map((s,i)=>{const on=i===active,p=pop(l,start+i*7);
      return <div key={s[0]} style={{width:300,height:64,display:'flex',alignItems:'center',gap:12,padding:'0 16px',background:on?C.paper:'rgba(255,255,255,0.6)',border:`${on?2.4:1.2}px solid ${on?s[2]:C.line}`,borderRadius:14,boxShadow:on?paperShadow(0.3):'none',opacity:p,transform:`translateY(${14*(1-p)}px) scale(${on?1:.96})`}}>
        <span style={{width:34,height:34,borderRadius:99,background:on?s[2]:'rgba(118,110,101,0.2)',color:C.white,display:'grid',placeItems:'center',fontFamily:'Clash',fontWeight:600,fontSize:19}}>{s[0]}</span>
        <span style={{fontFamily:'Kai',fontWeight:700,fontSize:TYPE.titleXS,color:on?s[2]:C.muted}}>{s[1]}</span>
      </div>;
    })}
  </div>;
};

const SceneWorldP=()=>{
  const f=q(useCurrentFrame()),l=f;
  if(f>212) return null;
  const opacity=stageFade(f,0,205);
  const dim=ease(l,51,92,1,.42),roll=easeOutSoft(l,45,78),rollS=interpolate(roll,[0,.5,.82,1],[.82,1.06,.98,1]),rollR=interpolate(roll,[0,1],[150,360]),rollO=ease(l,43,62);
  return <div style={{position:'absolute',inset:0,opacity}}>
    <div style={{position:'absolute',left:50,top:460,width:980,height:560,borderRadius:24,background:'linear-gradient(145deg,rgba(255,255,255,0.85),rgba(244,238,230,0.45))',border:`1px solid ${C.line}`,boxShadow:paperShadow(0.1),opacity:rollO}}/>
    
    <Paper lift={0.2} borderColor={C.muted} style={{left:60,top:190,width:960,height:230,zIndex:60,padding:'22px 26px',opacity:dim,transform:`translateY(${26*(1-pop(l,4))}px) scale(${.94+.06*pop(l,4)})`}}>
      <div style={{display:'flex',alignItems:'center',gap:8}}>
        <PillTag text="LOCAL HOST" color={C.muted} bg="rgba(118,110,101,0.1)"/>
        <span style={{fontFamily:'Caveat',fontSize:20,color:C.orange,transform:'rotate(-4deg)'}}>lonely code</span>
      </div>
      <JumpInText frame={l} items={[{text:'本地硬盘',color:C.ink,colorActive:C.orange}]} fontSize={TYPE.displayS} start={7} style={{justifyContent:'flex-start',marginTop:6}}/>
      <div style={{fontSize:TYPE.bodyM,fontWeight:700,marginTop:6,color:C.muted}}>代码只躺在你电脑里</div>
      <div style={{position:'absolute',left:26,right:26,top:124,bottom:18}}>
        {[0,1,2,3].map(i=><div key={i} style={{height:10,margin:'10px 0',width:`${74-i*9}%`,background:i===0?C.orange:'rgba(118,110,101,0.18)',borderRadius:4,opacity:pop(l,12+i*6)}}/>)}
      </div>
    </Paper>
    
    <div style={{position:'absolute',left:516,top:438,fontSize:56,color:C.orange,zIndex:75,opacity:ease(l,42,60),transform:`translateY(${-10*(1-ease(l,42,60))}px)`}}>↓</div>
    
    <div style={{position:'absolute',left:80,top:520,width:1160,height:600,zIndex:72,transform:'scale(0.776)',transformOrigin:'left top',opacity:rollO}}>
      <svg width={1160} height={600} viewBox="0 0 1160 600" style={{overflow:'visible'}}>
        <circle cx={580} cy={300} r={140} fill="#eef5fc" stroke={C.blue} strokeWidth={3.5} opacity={0.95}/>
        <ellipse cx={580} cy={300} rx={56} ry={140} fill="none" stroke={C.blue} strokeWidth={1.8} opacity={.45}/>
        <ellipse cx={580} cy={300} rx={110} ry={140} fill="none" stroke={C.blue} strokeWidth={1.8} opacity={.3}/>
        <line x1={440} y1={300} x2={720} y2={300} stroke={C.blue} strokeWidth={1.8} opacity={.45}/>
        <path d="M520 250 q30 -26 66 -6 q34 -16 52 14 q-10 34 -48 26 q-30 20 -60 -8 q-16 -30 -10 -26" fill={C.green} opacity={.22}/>
        {NODES.map((n,i)=>{const app=ease(l,72+i*9,98+i*9);const mx=(580+n.x)/2,my=(300+n.y)/2-46;return <g key={i} opacity={app}>
          <path d={`M580 300 Q${mx} ${my} ${n.x} ${n.y}`} fill="none" stroke={n.c} strokeWidth={2.8} strokeDasharray="8 8" strokeDashoffset={-l*3.2}/>
          <g transform={`scale(${.6+.4*pop(l,65+i*9)})`} style={{transformBox:'fill-box',transformOrigin:'center'} as any}>
            <rect x={n.x-42} y={n.y-32} width={84} height={64} rx={12} fill={C.paper} stroke={n.c} strokeWidth={2.4} style={{boxShadow:paperShadow(0.2)} as any}/>
            <rect x={n.x-42} y={n.y-32} width={84} height={14} rx={12} fill={n.c} opacity={.9}/>
          </g>
        </g>;})}
      </svg>
      {NODES.map((n,i)=><div key={i} style={{position:'absolute',left:n.x-42,top:n.y-6,width:84,textAlign:'center',fontFamily:'Space,Kai',fontWeight:700,fontSize:TYPE.bodyM,color:n.c,opacity:ease(l,84+i*9,104+i*9)}}>{n.label}</div>)}
      <div style={{position:'absolute',left:512,top:286,color:C.blue,fontSize:TYPE.microL,fontWeight:700}}>GitHub</div>
    </div>
    
    <div style={{position:'absolute',left:860,top:1000,zIndex:96,opacity:ease(l,95,117),transform:`translateY(${18*(1-ease(l,95,117))}px)`}}><Mascot size={110} f={l} wave/></div>
    
    <Paper lift={0.3} borderColor={C.green} style={{left:50,top:1130,width:980,height:88,zIndex:85,display:'flex',alignItems:'center',justifyContent:'center',gap:12,opacity:ease(l,124,143),transform:`translateY(${18*(1-pop(l,124))}px)`}}>
      <PillTag text="OPEN SOURCE" color={C.green} bg={C.greenLight}/>
      <div style={{fontSize:TYPE.titleL,fontWeight:700}}>全世界的开发者，<span style={{color:C.green}}>一起造软件</span></div>
    </Paper>
  </div>;
};

const SceneContributeP=()=>{
  const f=q(useCurrentFrame()),l=f-213;
  if(f<210||f>414) return null;
  const intro=ease(f,213,228);
  const outro=ease(f,396,412,1,0);
  const exitSlide=ease(f,396,412,0,36);
  const opacity=intro*outro;
  const t=ease(l,43,113);const merge=ease(l,105,134);const cardX=80+520*Math.min(1,t/0.72);
  const steps=['读懂项目规则','建立最小改动','提交你的 PR','通过 CI 与评审'];
  return <div style={{position:'absolute',inset:0,opacity,transform:`translateX(${-exitSlide}px)`}}>
    <StepRailP active={0} l={l} start={6}/>
    <svg width={1080} height={1440} style={{position:'absolute',inset:0,zIndex:55}}>
      <path d="M80 640 H760" fill="none" stroke="rgba(37,99,235,0.25)" strokeWidth={7} strokeLinecap="round"/>
      <path d="M80 760 H590 Q660 760 700 700 L732 652" fill="none" stroke={C.orange} strokeWidth={6} strokeDasharray="14 10" strokeDashoffset={-l*4} opacity={.95}/>
      <text x="80" y="612" fill={C.blue} fontFamily="Space,Kai" fontWeight="600" fontSize="28">main 主干</text>
      <text x="80" y="802" fill={C.orange} fontFamily="Space,Kai" fontWeight="600" fontSize="28">你的分支</text>
      <circle cx={732} cy={648} r={14} fill={merge>.4?C.green:'#d8d0c4'} opacity={ease(l,99,120)} style={{filter:'drop-shadow(0 2px 6px rgba(0,0,0,0.15))'}}/>
    </svg>
    
    <Paper lift={Math.sin(Math.PI*t)*.4+0.1} borderColor={C.orange} style={{left:cardX,top:700,width:210,height:96,zIndex:96,padding:'16px 18px',opacity:ease(l,39,56)*ease(l,130,142,1,0),transform:`translateY(${-90*Math.sin(Math.PI*t)*(cardX<400?1:.4)}px)`}}>
      <div style={{fontFamily:'Kai',fontWeight:700,fontSize:TYPE.titleS,color:C.orange}}>你的修改</div>
      <div style={{fontSize:TYPE.labelL,fontWeight:700,marginTop:6,color:C.muted}}>commit</div>
    </Paper>
    
    <Paper lift={.4} borderColor={C.green} style={{left:540,top:520,width:260,height:112,zIndex:94,padding:'16px 20px',opacity:merge,transform:`scale(${.7+.3*pop(l,109)})`}}>
      <div style={{display:'flex',alignItems:'center',gap:12}}>
        <span style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.titleM,color:C.green}}>Pull Request</span>
      </div>
      <div style={{fontSize:TYPE.labelL,fontWeight:700,marginTop:8,color:C.muted}}>把改动交给项目</div>
      <div style={{position:'absolute',right:16,top:16,transform:`scale(${pop(l,130)})`}}><CheckBadge size={30}/></div>
    </Paper>
    
    <Paper lift={0.25} borderColor={C.blue} style={{left:60,top:840,width:960,height:430,zIndex:76,padding:'26px 30px',transform:`translateX(${36*(1-pop(l,9))}px)`,opacity:pop(l,9)}}>
      <div style={{display:'flex',alignItems:'center',gap:8}}>
        <PillTag text="EP 1 · CONTRIBUTE" color={C.blue} bg={C.blueLight}/>
        <span style={{fontFamily:'Caveat',fontSize:20,color:C.blue,transform:'rotate(-2deg)'}}>start small</span>
      </div>
      <JumpInText frame={l} items={[{text:'第一步：参与开源',color:C.blue,colorActive:C.orange}]} fontSize={TYPE.displayS} start={11} style={{justifyContent:'flex-start',marginTop:6}}/>
      <div style={{position:'absolute',left:30,right:30,top:110,bottom:100}}>
        {steps.map((s,i)=>{const p=pop(l,39+i*20);
          return <div key={s} style={{display:'flex',alignItems:'center',gap:16,height:48,marginBottom:8,opacity:p,transform:`translateX(${24*(1-p)}px)`}}>
            <span style={{width:38,height:38,borderRadius:99,background:[C.orange,C.blue,C.green,C.gold][i],color:C.white,display:'grid',placeItems:'center',fontFamily:'Clash',fontWeight:600,fontSize:19}}>{i+1}</span>
            <span style={{fontSize:TYPE.titleXS,fontWeight:700}}>{s}</span>
          </div>;
        })}
      </div>
      <div style={{position:'absolute',left:30,right:30,bottom:28,height:44,background:C.greenLight,border:`1.5px solid ${C.green}`,borderRadius:12,display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyL,color:C.green,letterSpacing:1,opacity:ease(l,120,140)}}>
        github-oss-contribute
      </div>
    </Paper>
  </div>;
};

const SceneShipP=()=>{
  const f=q(useCurrentFrame()),l=f-416;
  if(f<415||f>680) return null;
  const intro=ease(f,416,432);
  const outro=ease(f,660,676,1,0);
  const exitSlide=ease(f,660,676,0,36);
  const opacity=intro*outro;
  const ver=ease(l,177,219);const rocket=ease(l,177,236);
  const g1=ease(l,135,177),g2=ease(l,152,194),g3=ease(l,169,211);
  return <div style={{position:'absolute',inset:0,opacity,transform:`translateX(${-exitSlide}px)`}}>
    <Paper lift={0.2} borderColor={C.orange} style={{left:60,top:190,width:960,height:340,zIndex:70,padding:'24px 28px',transform:`translateY(${26*(1-pop(l,5))}px) scale(${.95+.05*pop(l,5)})`,opacity:pop(l,5)}}>
      <div style={{display:'flex',alignItems:'center',gap:8}}>
        <PillTag text="EP 2 · PREP" color={C.orange} bg={C.orangeLight}/>
        <span style={{fontFamily:'Caveat',fontSize:20,color:C.orange,transform:'rotate(3deg)'}}>packaging</span>
      </div>
      <JumpInText frame={l} items={[{text:'第二步：发布',color:C.orange,colorActive:C.blue}]} fontSize={TYPE.displayS} start={7} style={{justifyContent:'flex-start',marginTop:4,whiteSpace:'nowrap'}}/>
      <div style={{fontSize:TYPE.titleXS,fontWeight:700,marginTop:4,color:C.muted}}>整理成专业开源仓库</div>
      <div style={{position:'absolute',left:40,right:40,top:138,height:148,background:'rgba(255,255,255,0.75)',border:`1.5px solid ${C.orange}`,borderRadius:'14px',boxShadow:paperShadow(0.12),overflow:'hidden'}}>
        <div style={{height:26,background:C.orange,display:'flex',alignItems:'center',paddingLeft:14}}><span style={{fontFamily:'Space',color:C.white,fontWeight:700,fontSize:12}}>STANDARDIZED TEMPLATE</span></div>
        <div style={{padding:'6px 14px',display:'flex',flexDirection:'column',gap:4}}>
          {[
            {name:'README.md',desc:'说明文档',color:C.blue,start:24},
            {name:'LICENSE',desc:'开源协议',color:C.green,start:48},
            {name:'CI / Actions',desc:'质量门禁',color:C.gold,start:72},
          ].map((item)=>{
            const p=pop(l,item.start);
            return <div key={item.name} style={{height:32,background:C.paper,border:`1.2px solid ${item.color}`,borderRadius:8,display:'flex',alignItems:'center',justifyContent:'space-between',padding:'0 12px',opacity:p,transform:`translateX(${16*(1-p)}px)`}}>
              <span style={{fontFamily:'Space',fontWeight:700,fontSize:TYPE.bodyM,color:C.ink}}>{item.name}</span>
              <span style={{fontFamily:'Space',fontSize:11,fontWeight:700,color:item.color}}>READY</span>
            </div>;
          })}
        </div>
      </div>
      <div style={{position:'absolute',left:34,right:34,bottom:20,height:40,background:C.orangeLight,border:`1.5px solid ${C.orange}`,borderRadius:12,display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyM,color:C.orange,opacity:ease(l,95,130)}}>github-oss-prep</div>
    </Paper>
    
    <Paper lift={0.25} borderColor={C.navy} style={{left:60,top:550,width:960,height:610,zIndex:72,padding:'24px 28px',transform:`translateY(${26*(1-pop(l,71))}px) scale(${.95+.05*pop(l,71)})`,opacity:pop(l,71)}}>
      <div style={{display:'flex',alignItems:'center',gap:8}}>
        <PillTag text="EP 3 · OPS" color={C.blue} bg={C.blueLight}/>
        <span style={{fontFamily:'Caveat',fontSize:20,color:C.blue,transform:'rotate(-2deg)'}}>ongoing triage</span>
      </div>
      <JumpInText frame={l} items={[{text:'第三步：运营',color:C.navy,colorActive:C.green}]} fontSize={TYPE.displayS} start={91} style={{justifyContent:'flex-start',marginTop:6}}/>
      <div style={{fontSize:TYPE.titleXS,fontWeight:700,marginTop:6,color:C.muted}}>分流 · 审查 · 按时发版</div>
      <div style={{position:'absolute',left:28,top:180,right:28,height:120}}><Gauge label="Issue 分流" color={C.orange} v={g1} x={40}/><Gauge label="PR 审查" color={C.blue} v={g2} x={398}/><Gauge label="Release" color={C.green} v={g3} x={756}/></div>
      <div style={{position:'absolute',left:28,top:360,display:'flex',alignItems:'center',gap:16,opacity:ease(l,177,208)}}>
        <div style={{display:'flex',alignItems:'center',gap:4,padding:'6px 16px',background:C.paper,border:`1.5px solid ${C.line}`,borderRadius:12,boxShadow:paperShadow(0.2)}}>
          <span style={{fontFamily:'Space',fontWeight:600,fontSize:TYPE.titleL,color:C.ink}}>v1.</span>
          <RollDigit fromChar="0" toChar="1" start={182} duration={13} frame={l} fontSize={TYPE.displayS} fontFamily="Space" fontWeight={700} colorFrom={C.muted} colorTo={C.green}/>
        </div>
        <div style={{display:'flex',alignItems:'center',gap:6,color:C.green,fontFamily:'Space,Kai',fontWeight:700,fontSize:TYPE.bodyM,opacity:ease(l,194,212),transform:`translateX(${10*(1-ease(l,194,212))}px)`}}>
          <CheckBadge size={26}/> 准备发版
        </div>
      </div>
      <svg width={120} height={160} style={{position:'absolute',right:40,bottom:90,transform:`translateY(${-150*rocket}px)`,opacity:ease(l,175,197)}} viewBox="0 0 120 160"><path d="M60 6 C86 40 86 88 60 120 C34 88 34 40 60 6 Z" fill={C.paper} stroke={C.red} strokeWidth={3.5}/><circle cx={60} cy={54} r={13} fill="#eef5fc" stroke={C.blue} strokeWidth={2.8}/><path d="M40 96 L24 128 L44 116 Z" fill={C.orange} stroke={C.red} strokeWidth={2.8} strokeLinejoin="round"/><path d="M80 96 L96 128 L76 116 Z" fill={C.orange} stroke={C.red} strokeWidth={2.8} strokeLinejoin="round"/><path d="M50 120 q10 24 20 0" fill={C.gold} opacity={.9}/></svg>
      <div style={{position:'absolute',left:34,right:34,bottom:24,height:44,background:C.blueLight,border:`1.5px solid ${C.navy}`,borderRadius:12,display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:600,fontSize:TYPE.bodyM,color:C.navy,opacity:ease(l,188,217)}}>github-oss-ops</div>
    </Paper>
  </div>;
};

const SceneSkillsP=()=>{
  const f=q(useCurrentFrame()),l=f-682,opacity=ease(f,662,692);
  const cta=ease(l,282,350);
  return <div style={{position:'absolute',inset:0,opacity}}>
    <div style={{position:'absolute',left:470,top:205,zIndex:75,textAlign:'center',opacity:pop(l,-27),transform:`scale(${.7+.3*pop(l,-27)})`}}>
      <Mascot size={110} f={l} wave/>
      <div style={{fontFamily:'Space',fontWeight:700,fontSize:TYPE.titleM,color:C.navy,marginTop:2}}>AI AGENT</div>
    </div>
    {SKILLS.map((s,i)=>{
      const p=pop(l,10+i*16);const y=340+i*265;
      return <Paper key={s[0]} lift={.3} borderColor={s[3]} style={{left:60,top:y,width:960,height:250,zIndex:94,padding:'24px 28px',opacity:p,transform:`translateY(${34*(1-p)}px) scale(${.92+.08*p})`}}>
        <div style={{position:'absolute',right:24,top:22}}>
          <PillTag text={s[2]} color={s[3]} bg={`${s[3]}18`} fontSize={TYPE.labelS}/>
        </div>
        <div style={{position:'absolute',left:24,top:26,width:56,height:56,borderRadius:16,background:s[3],display:'grid',placeItems:'center',color:C.white,boxShadow:`0 4px 14px ${s[3]}40`}}><LineIcon kind={['play','project','report'][i] as IconKind} size={32} color={C.white} strokeWidth={2.4}/></div>
        <div style={{position:'absolute',left:104,top:34,fontFamily:'Space',fontWeight:600,fontSize:TYPE.titleM,color:s[3]}}>{s[0]}</div>
        <div style={{position:'absolute',left:104,top:82,fontSize:TYPE.titleXS,fontWeight:700}}>{s[1]}</div>
        <div style={{position:'absolute',left:28,bottom:22,display:'flex',alignItems:'center',gap:10,color:C.muted,fontSize:TYPE.labelL,fontWeight:700}}><CheckBadge size={26}/>智能体陪你走完</div>
      </Paper>;
    })}
    <Paper lift={0.4} borderColor={C.orange} style={{left:50,top:1170,width:980,height:96,zIndex:96,display:'grid',placeItems:'center',opacity:cta,transform:`translateY(${22*(1-cta)}px) scale(${.96+.04*pop(l,286)})`}}><div style={{display:'flex',alignItems:'center',gap:16}}><JumpInText frame={l} items={[{text:'主页搜',color:C.muted,fontSize:TYPE.titleM}]} fontSize={TYPE.titleM} start={287}/><WaveText frame={l} text="github.com/hyt315" fontSize={TYPE.displayS} colorFrom="#f09070" colorTo={C.orange} start={291} fontFamily="Space" fontWeight={700}/></div></Paper>
  </div>;
};

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
const camAt=(f:number,isPortrait:boolean)=>{const K=isPortrait?CAM_KEYS_P:CAM_KEYS_L;let i=0;while(i<K.length-2&&f>K[i+1].f)i++;const a=K[i],b=K[i+1];const t=interpolate(f,[a.f,b.f],[0,1],{...clamp,easing:camEase});return {s:a.s+(b.s-a.s)*t,x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t};};
const CameraRig:React.FC<{children:React.ReactNode}>=({children})=>{
  const {isPortrait}=useCanvas();
  const f=useCurrentFrame(),cw=isPortrait?1080:1920,ch=isPortrait?1440:1080;
  // Tibo 式解析滞后（跟焦感）：焦点对目标轨迹做指数加权采样，镜头慢半拍追上
  const cam=camAt(f,isPortrait);
  let wx=0,wy=0,ws=0;const N=14,SPAN=7;
  for(let k=0;k<N;k++){const age=k/(N-1)*SPAN;const w=Math.exp(-age/3.1);const c=camAt(f-age,isPortrait);wx+=c.x*w;wy+=c.y*w;ws+=w;}
  const x=wx/ws,y=wy/ws,s=cam.s,cx=cw/2,cy=ch/2;
  return <div style={{position:'absolute',left:0,top:0,width:cw,height:ch,transformOrigin:'0 0',transform:`translate(${cx-x*s}px,${cy-y*s}px) scale(${s})`}}>{children}</div>;
};

const FinalDemo=()=>{
  const {isPortrait}=useCanvas();
  const f=q(useCurrentFrame());
  if(isPortrait)return <>{f<213&&<SceneWorldP/>}{f>=213&&f<416&&<SceneContributeP/>}{f>=416&&f<682&&<SceneShipP/>}{f>=682&&<SceneSkillsP/>}</>;
  return <>{f<213&&<SceneWorld/>}{f>=213&&f<416&&<SceneContribute/>}{f>=416&&f<682&&<SceneShip/>}{f>=682&&<SceneSkills/>}</>;
};

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

const FilmLayout:React.FC<{canvas:CanvasMode}>=({canvas})=>{
  const mode=MODES[canvas]||MODES['16:9'];
  const isPortrait=canvas==='3:4';
  return <CanvasContext.Provider value={{canvas,isPortrait,mode}}>
    <AbsoluteFill style={{overflow:'hidden',background:C.paperBase}}>
      <div style={{position:'absolute',left:0,top:0,width:mode.designW,height:mode.designH,transform:`scale(${mode.scale})`,transformOrigin:'0 0',fontFamily:'Kai,sans-serif',color:C.ink,overflow:'hidden'}}>
        <Fonts/><AssetGate/><CaptionFitGate/><Sound/><Background/>
        {canvas==='4:3'?<div style={{position:'absolute',left:0,top:(mode.designH-810)/2,width:1920,height:1080,transform:'scale(0.75)',transformOrigin:'top left'}}><Chrome/><CameraRig><FinalDemo/></CameraRig></div>:<><Chrome/><CameraRig><FinalDemo/></CameraRig></>}
        <Grade/>
        <Subtitle/>
      </div>
    </AbsoluteFill>
  </CanvasContext.Provider>;
};

const Film16x9=()=> <FilmLayout canvas="16:9"/>;
const Film4x3=()=> <FilmLayout canvas="4:3"/>;
const Film3x4=()=> <FilmLayout canvas="3:4"/>;

const Root=()=> <>
  <Composition id="NotebookVideoFilm" component={Film16x9} durationInFrames={DURATION} fps={FPS} width={2560} height={1440}/>
  <Composition id="NotebookVideoFilm-16x9" component={Film16x9} durationInFrames={DURATION} fps={FPS} width={2560} height={1440}/>
  <Composition id="NotebookVideoFilm-4x3" component={Film4x3} durationInFrames={DURATION} fps={FPS} width={1920} height={1440}/>
  <Composition id="NotebookVideoFilm-3x4" component={Film3x4} durationInFrames={DURATION} fps={FPS} width={1440} height={1920}/>
</>;
registerRoot(Root);