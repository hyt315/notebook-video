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
import {MODES, CanvasMode, CanvasContext, useCanvas} from './theme/canvas';
import {THEME} from './theme/active';
import type {IconKind} from './kit';
import {PillTag, LineIcon, CheckBadge, TYPE} from './kit';
// v2.10 视觉体系四层：镜头 / 骨架 / 介质 / 门禁。用法见 references/shot-language.md、
// scene-skeletons.md、media-routing.md、composition-gate.md。
import {BackgroundMute, CoverPanel, DepthLayers, ShotCamera, camAt, shotCam, stillCam} from './shotkit';
import {Attach, PhaseRail, StageFrame, useStageMachine} from './stagekit';
import {InsertShot, PaperTurn, RevealMask, TRANSITIONS, WhipStreak, useHandoff} from './insert';
import {ConsoleWindow, MetricGrid, StampBanner} from './media';
import {Corridor, SplitStage, ZoomStage} from './skeletons';
import {Showcase, SHOWCASE_PAGES} from './showcase';
import {OverlapGate} from './overlap-gate';
import {SHOTS, SHOT_IDS, SHOT_TOTAL} from './shots';
import {SCENES} from './scenes';
const BASE_FPS=30,FPS=30,MOTION_FPS=30,TIMELINE_SCALE=1,DURATION=SHOT_TOTAL,DESIGN_SCALE=4/3;
const useCurrentFrame=()=>useRawCurrentFrame()*BASE_FPS/FPS/TIMELINE_SCALE;
const deliveryFrame=(designFrame:number)=>Math.round(designFrame*FPS*TIMELINE_SCALE/BASE_FPS);

// LOCKED AESTHETIC CORE：美学核由主题包提供（src/theme/active.ts 选定），
// 调色板 / 美学参数 / 卡片皮肤 / 背景 / 调色层全部来自 THEME，本层不做任何风格判断。
const C=THEME.palette;
const AESTHETIC=THEME.aesthetic;
const paperShadow=THEME.paperShadow;
const Background=THEME.Background;
const Grade=THEME.Grade;

// EDITABLE CONTENT SURFACE — 换题材时从这里开始改
const COPY={
  chapterTitles:['代码不再孤独','入场三步','第二步 · 发布','第三步 · 运营与三技能'],
  chromeKicker:'GITHUB 新手三部曲',
  header:'开源之路 / OPEN SOURCE',
  headerSub:'CONTRIBUTE · PREP · OPS / EP0',
} as const;

// 章节 = 分镜表里各章首镜。章节卡与页眉由此驱动，不手写帧号。
const CHAPTER_SHOTS=['S1','S2','S4','S5'] as const;
const CHAPTER_STARTS=CHAPTER_SHOTS.map((id)=>SHOTS[id].from);

const clamp={extrapolateLeft:'clamp' as const,extrapolateRight:'clamp' as const};
const msFrame=(ms:number)=>Math.round(ms*FPS/1000);
const captions=((cueData as any).cues as any[]).map(c=>({...c,startFrame:msFrame(c.start_ms),endFrame:msFrame(c.speech_end_ms),words:c.words.map((w:any)=>({...w,startFrame:msFrame(w.start),endFrame:msFrame(w.end)}))}));
const q=(f:number)=>{const step=BASE_FPS/MOTION_FPS;return Math.floor(f/step)*step};
const ease=(f:number,a:number,b:number,from=0,to=1)=>interpolate(f,[a,b],[from,to],{...clamp,easing:Easing.inOut(Easing.cubic)});
const easeOutSoft=(f:number,a:number,b:number,from=0,to=1)=>interpolate(f,[a,b],[from,to],{...clamp,easing:Easing.bezier(.16,1,.3,1)});
const pop=(f:number,start:number,stiffness=132)=>spring({frame:f-start,fps:BASE_FPS,config:{damping:17,stiffness,mass:.86}});

const AssetGate=()=>{const [handle]=useState(()=>delayRender('waiting for fonts',{timeoutInMilliseconds:120000}));useEffect(()=>{let live=true;Promise.all([document.fonts.load('400 40px Kai'),document.fonts.load('700 40px Kai'),document.fonts.load('600 40px Clash'),document.fonts.load('500 40px Space'),document.fonts.load('400 40px Caveat'),document.fonts.ready]).then(()=>{if(live)continueRender(handle)}).catch(error=>{if(live)cancelRender(error)});return()=>{live=false}},[handle]);return null};

// CardFitGate：卡片防出格门。逐桶（15 帧）扫描已挂载场景：每个含文字的叶元素，
// 用 offset 链（天然无视 transform 位移动画）累加其相对"最近卡片祖先"
// （首个有不透明底 + 实线边框的祖先，即 Paper/FitCard 类卡片）的位置，
// 超出卡片 padding 盒 2px 即 cancelRender。z>=140 的 chrome/字幕层跳过
// （模板锁定层，各自有门）。无 delayRender NFC 阻塞；字体未就绪的桶跳过。
const CardFitGate=()=>{
  const f=q(useCurrentFrame());
  const bucket=Math.floor(f/15);
  useEffect(()=>{
    const id=requestAnimationFrame(()=>{
      try{
        if(document.fonts.status!=='loaded') return;
        const bad:string[]=[];
        const opaque=(el:Element)=>{const s=getComputedStyle(el as HTMLElement);const bg=s.backgroundColor;const m=/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/.exec(bg);const alpha=m?(m[4]===undefined?1:parseFloat(m[4])):0;return alpha>0.9&&parseFloat(s.borderTopWidth)>0;};
        document.querySelectorAll<HTMLElement>('div,span').forEach((el)=>{
          if(!el.textContent||!el.textContent.trim()||el.children.length>0) return;
          if(el.closest('[data-fit-skip]')) return;
          let card:HTMLElement|null=null,n:HTMLElement|null=el.parentElement;
          while(n&&n!==document.body){if(opaque(n)){card=n;break;}n=n.parentElement;}
          if(!card) return;
          const z=parseInt(getComputedStyle(card).zIndex||'0',10);
          if(z>=140) return;
          let x=0,y=0,m:HTMLElement|null=el;
          while(m&&m!==card){x+=m.offsetLeft;y+=m.offsetTop;m=m.offsetParent as HTMLElement|null;}
          if(m!==card) return;
          const overB=y+el.offsetHeight-card.clientHeight,overR=x+el.offsetWidth-card.clientWidth;
          if(overB>2||overR>2) bad.push(`@${f} “${(el.textContent||'').trim().slice(0,10)}”出${Math.max(0,Math.ceil(overB))}px`);
        });
        if(bad.length) cancelRender(new Error(`Card overflow: ${bad.slice(0,4).join(' | ')}`));
      }catch(e){if(typeof console!=='undefined') console.warn('[CardFitGate]',e);}
    });
    return ()=>cancelAnimationFrame(id);
  },[bucket]);
  return null;
};

// Non-visual QA gate: measure every full cue with the real loaded font.
// 画幅感知（v2.10 修复）：字号 / 字重 / 字距 / 安全宽全部取自当前 canvas 与主题。
// 旧版硬编码 16:9 的 44px/400/1334，导致 4:3 与 3:4 的字幕超宽静默通过、渲染后被裁切；
// 同时没有计入主题字幕框的内边距（cel 64px / sticker 72px / flat 108px）。
// 判定：> mode.safe 记 fail（真的会被裁切）；> mode.safe - subtitlePadX 只 warn（会顶到内边）。
const CaptionFitGate=()=>{const {mode}=useCanvas();const safe=mode.safe,innerSafe=safe-(AESTHETIC.subtitlePadX??0),weight=AESTHETIC.subtitleWeight??400,ls=AESTHETIC.subtitleLetterSpacing??1.6;const ref=useRef<HTMLDivElement>(null),[done,setDone]=useState(false),[handle]=useState(()=>delayRender('measuring subtitle width',{timeoutInMilliseconds:60000}));useEffect(()=>{let live=true;Promise.all([document.fonts.load(`${weight} ${mode.subFont}px Kai`),document.fonts.ready]).then(()=>requestAnimationFrame(()=>{if(!live)return;if(!ref.current){cancelRender(new Error('Subtitle measurement node is unavailable'));return}const rows=[...ref.current.querySelectorAll<HTMLElement>('[data-caption-fit]')];const widths=rows.map((row,index)=>({index,width:row.getBoundingClientRect().width/DESIGN_SCALE,text:row.textContent||''}));const overflow=widths.filter(row=>row.width>safe+.5);const tight=widths.filter(row=>row.width>innerSafe+.5&&row.width<=safe+.5);if(tight.length&&typeof console!=='undefined')console.warn(`[CaptionFitGate] ${tight.length} 条字幕超过内边距安全宽 ${innerSafe}px（未裁切但会顶到字幕框内边）：${tight.map(x=>`#${x.index+1} ${Math.ceil(x.width)}px`).join(' | ')}`);if(overflow.length){cancelRender(new Error(`Subtitle overflow: ${overflow.map(x=>`#${x.index+1} ${Math.ceil(x.width)}px>${safe}px ${x.text}`).join(' | ')}`));return}setDone(true);continueRender(handle)})).catch(error=>{if(live)cancelRender(error)});return()=>{live=false}},[handle,mode.subFont,safe,innerSafe,weight,ls]);if(done)return null;return <div ref={ref} style={{position:'absolute',left:-10000,top:-10000,visibility:'hidden',fontFamily:'Kai,sans-serif',fontSize:mode.subFont,fontWeight:weight,whiteSpace:'nowrap',letterSpacing:ls}}>{captions.map((cue:any,index:number)=><span key={index} data-caption-fit style={{display:'block',width:'max-content'}}>{String(cue.text).replace(/[，。！？；：、,.!?;:\s]+$/g,'')}</span>)}</div>};

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

// ---- 可复用组件库 -------------------------------------------

// Paper：卡片容器，皮肤由主题包提供（src/theme/active.ts）。
const Paper=THEME.Paper;

// LineIcon / PillTag / CheckBadge 已抽到 src/kit.tsx（主题无关原子，工程侧同样可引用）。

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
    <span style={{display:'inline-block',color,fontSize,fontFamily,fontWeight,opacity:turnPhase<=0.56?1:0,transform:`translateY(${progress>=1?0:outgoingY}px) scaleY(${outgoingScaleY})`,transformOrigin:'50% 100%'}}>{fromChar}</span>
    <span style={{position:'absolute',left:0,top:0,color,fontSize,fontFamily,fontWeight,opacity:turnPhase>=0.44?1:0,transform:`translateY(${incomingY}px) scaleY(${incomingScaleY})`,transformOrigin:'50% 0%'}}>{toChar}</span>
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

// ---- 通用组件扩展（v2.5 新增）------------------------------------------
// SPRINGS：弹性预设三档。soft 与历史 pop() 默认参数完全一致，旧场景行为不变。
const SPRINGS={snappy:{damping:16,stiffness:200,mass:.8},soft:{damping:17,stiffness:132,mass:.86},bouncy:{damping:11,stiffness:160,mass:.9}} as const;
const popS=(f:number,start:number,preset:keyof typeof SPRINGS='soft')=>spring({frame:f-start,fps:BASE_FPS,config:SPRINGS[preset]});

// useSteppedFrame：停帧点缀（默认 15fps，每个姿势占两输出帧，契约见 motion-design.md）。
const useSteppedFrame=(stepFps=15)=>{const f=useCurrentFrame();return Math.floor(f*stepFps/BASE_FPS)*BASE_FPS/stepFps};

// CodeBlock：终端风代码窗——三灯标题栏 + 语法色行 + 逐行滑入，精致墨边紧凑投影。
const CodeBlock:React.FC<{title?:string;lines:{text:string;color?:string;prefix?:string;start?:number}[];start?:number;frame?:number;stagger?:number;cursor?:boolean;style?:React.CSSProperties}>=({title='terminal',lines,start=0,frame,stagger=8,cursor=false,style})=>{
  const f=frame??q(useCurrentFrame());
  return <div style={{background:'#14110f',border:`2.2px solid ${C.ink}`,borderRadius:10,boxShadow:`3.5px 3.5px 0 ${C.ink}`,overflow:'hidden',...style}}>
    <div style={{height:34,background:'#1f1b18',display:'flex',alignItems:'center',gap:7,paddingLeft:14,borderBottom:'1.5px solid #2d2621'}}>
      {[C.red,C.gold,C.green].map((c,i)=><span key={i} style={{width:10,height:10,borderRadius:99,background:c,border:'1px solid #000'}}/>)}
      <span style={{marginLeft:8,fontFamily:'Space,monospace',fontWeight:600,fontSize:13,letterSpacing:1,color:'#fdfdfb',opacity:.85}}>{title}</span>
    </div>
    <div style={{padding:'14px 18px',display:'flex',flexDirection:'column',gap:9}}>
      {lines.map((ln,i)=>{
        const lnStart = ln.start ?? (start + i * stagger);
        if (f < lnStart) return null;
        const p=popS(f,lnStart,'snappy');
        const isTail=cursor&&(i===lines.length-1||(lines[i+1]&&f<(lines[i+1].start??(start+(i+1)*stagger))));
        return <div key={i} style={{display:'flex',alignItems:'center',fontFamily:'Space,Kai,monospace',fontWeight:600,fontSize:TYPE.bodyM,color:ln.color||'#fdfdfb',opacity:p,transform:`translateX(${18*(1-p)}px)`,whiteSpace:'nowrap'}}>
          {ln.prefix&&<span style={{color:C.green,marginRight:8}}>{ln.prefix}</span>}
          {ln.text}
          {isTail&&<span style={{display:'inline-block',width:8,height:18,marginLeft:6,background:C.green,opacity:Math.floor(f/8)%2?0.15:0.95}}/>}
        </div>;
      })}
    </div>
  </div>;
};

// BrowserChrome：浏览器窗口——三灯 + 锁 + URL 胶囊，内容区放 children。
const BrowserChrome:React.FC<{url:string;children?:React.ReactNode;lift?:number;style?:React.CSSProperties}>=({url,children,lift=.2,style})=>
  <Paper lift={lift} borderColor={C.line} style={{padding:0,overflow:'hidden',...style}}>
    <div style={{height:44,background:C.mutedWash,display:'flex',alignItems:'center',gap:12,padding:'0 16px',borderBottom:`1px solid ${C.line}`}}>
      <div style={{display:'flex',gap:7}}>{[C.red,C.gold,C.green].map((c,i)=><span key={i} style={{width:11,height:11,borderRadius:99,background:c}}/>)}</div>
      <div style={{flex:1,maxWidth:460,display:'flex',alignItems:'center',gap:7,background:C.paper,border:`1px solid ${C.line}`,borderRadius:999,padding:'4px 14px',color:C.muted}}>
        <LineIcon kind="lock" size={14} color={C.muted} strokeWidth={2.6}/>
        <span style={{fontFamily:'Space',fontWeight:600,fontSize:15,letterSpacing:.4,whiteSpace:'nowrap',overflow:'hidden'}}>{url}</span>
      </div>
    </div>
    <div style={{position:'relative'}}>{children}</div>
  </Paper>;

// Connector：曲线连接件——贝塞尔弧线 + 可选流向虚线 / 箭头 / 标签，替代场景层手写 SVG。
const Connector:React.FC<{from:{x:number;y:number};to:{x:number;y:number};bend?:number;color?:string;flow?:boolean;arrow?:boolean;label?:string;labelColor?:string;width?:number;frame?:number;style?:React.CSSProperties}>=({from,to,bend=46,color=C.blue,flow=false,arrow=true,label,labelColor,width=2.8,frame,style})=>{
  const f=frame??q(useCurrentFrame());
  const mx=(from.x+to.x)/2,my=(from.y+to.y)/2-bend;
  const ang=Math.atan2(to.y-my,to.x-mx)*180/Math.PI;
  const minX=Math.min(from.x,to.x,mx)-40,minY=Math.min(from.y,to.y,my)-40;
  const W=Math.max(from.x,to.x,mx)-minX+80,H=Math.max(from.y,to.y,my)-minY+80;
  return <div style={{position:'absolute',left:minX,top:minY,width:W,height:H,pointerEvents:'none',...style}}>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{overflow:'visible'}}>
      <path d={`M${from.x-minX} ${from.y-minY} Q${mx-minX} ${my-minY} ${to.x-minX} ${to.y-minY}`} fill="none" stroke={color} strokeWidth={width} strokeLinecap="round" strokeDasharray={flow?'9 8':undefined} strokeDashoffset={flow?-f*3:0}/>
      {arrow&&<path d="M0 0l-11 -6.5v13z" fill={color} transform={`translate(${to.x-minX} ${to.y-minY}) rotate(${ang})`}/>}
    </svg>
    {label&&<span style={{position:'absolute',left:mx-minX,top:my-minY,transform:'translate(-50%,-50%)',fontFamily:'Space,Kai',fontWeight:700,fontSize:TYPE.labelM,color:labelColor||color,background:C.paper,padding:'2px 10px',borderRadius:999,border:`1px solid ${color}55`,whiteSpace:'nowrap'}}>{label}</span>}
  </div>;
};

// Checklist：编号步骤清单——圆形序号 + 文案逐个滑入；done 给完成数，序号变对勾。
const Checklist:React.FC<{items:string[];start:number;frame?:number;stagger?:number;colors?:string[];done?:number;rowH?:number;fontSize?:number;style?:React.CSSProperties}>=({items,start,frame,stagger=20,colors,done=-1,rowH=48,fontSize=TYPE.titleXS,style})=>{
  const f=frame??q(useCurrentFrame());
  const defaults=[C.orange,C.blue,C.green,C.gold,C.red,C.navy];
  return <div style={{display:'flex',flexDirection:'column',...style}}>
    {items.map((s,i)=>{const p=popS(f,start+i*stagger,'soft');const checked=done>=0?i<done:false;
      return <div key={s} style={{display:'flex',alignItems:'center',gap:16,height:rowH,opacity:p,transform:`translateX(${24*(1-p)}px)`}}>
        <span style={{width:38,height:38,borderRadius:99,background:colors?.[i]||defaults[i%defaults.length],color:C.white,display:'grid',placeItems:'center',fontFamily:'Clash',fontWeight:600,fontSize:19,flex:'0 0 auto'}}>{checked?<LineIcon kind="check" size={22} color={C.white} strokeWidth={2.7}/>:i+1}</span>
        <span style={{fontSize,fontWeight:700}}>{s}</span>
      </div>;})}
  </div>;
};

// CountUp：数字滚动计数——easeOutSoft 进度 + 颜色过渡，支持前后缀。
const CountUp:React.FC<{to:number;from?:number;start:number;duration?:number;frame?:number;fontSize?:number;fontFamily?:string;fontWeight?:number|string;color?:string;colorFrom?:string;prefix?:string;suffix?:string;style?:React.CSSProperties}>=({to,from=0,start,duration=30,frame,fontSize=TYPE.displayS,fontFamily='Space',fontWeight=700,color=C.green,colorFrom=C.muted,prefix='',suffix='',style})=>{
  const f=frame??q(useCurrentFrame());
  const p=easeOutSoft(f,start,start+duration);
  const v=Math.round(from+(to-from)*p);
  const col=interpolateColors(p,[0,1],[colorFrom,color]);
  return <span style={{fontFamily,fontSize,fontWeight,color:col,fontVariantNumeric:'tabular-nums',...style}}>{prefix}{v}{suffix}</span>;
};

// ProgressBar：进度条——轨道 + 填充 + 可选标签/百分比，v 由场景驱动（0~1）。
const ProgressBar:React.FC<{v:number;color?:string;height?:number;label?:string;showPct?:boolean;style?:React.CSSProperties}>=({v,color=C.green,height=14,label,showPct=false,style})=>{
  const pct=Math.round(Math.max(0,Math.min(1,v))*100);
  return <div style={{...style}}>
    {(label||showPct)&&<div style={{display:'flex',justifyContent:'space-between',alignItems:'baseline',marginBottom:6}}>
      {label&&<span style={{fontSize:TYPE.labelL,fontWeight:700,color:C.ink}}>{label}</span>}
      {showPct&&<span style={{fontFamily:'Space',fontWeight:700,fontSize:TYPE.labelL,color}}>{pct}%</span>}
    </div>}
    <div style={{height,background:C.gaugeTrack,borderRadius:99,overflow:'hidden'}}>
      <div style={{height:'100%',width:`${pct}%`,background:color,borderRadius:99}}/>
    </div>
  </div>;
};

// Callout：手绘标注——双描边椭圆圈 + Caveat 手写字，整体弹入。
const Callout:React.FC<{x:number;y:number;w:number;h:number;text:string;textDy?:number;textDx?:number;color?:string;rotate?:number;start:number;frame?:number;fontSize?:number;style?:React.CSSProperties}>=({x,y,w,h,text,textDy=-46,textDx=0,color=C.orange,rotate=-2,start,frame,fontSize=22,style})=>{
  const f=frame??q(useCurrentFrame());
  const p=popS(f,start,'bouncy');
  return <div style={{position:'absolute',left:x,top:y,width:w,height:h,zIndex:96,opacity:p,transform:`scale(${.7+.3*p}) rotate(${rotate}deg)`,transformOrigin:'50% 50%',...style}}>
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{overflow:'visible'}}>
      <ellipse cx={w/2} cy={h/2} rx={w/2-3} ry={h/2-3} fill="none" stroke={color} strokeWidth={2.6} strokeLinecap="round" transform={`rotate(-1.5 ${w/2} ${h/2})`}/>
      <ellipse cx={w/2} cy={h/2} rx={w/2-7} ry={h/2-6} fill="none" stroke={color} strokeWidth={1.6} opacity={.55} strokeDasharray="5 7" transform={`rotate(2 ${w/2} ${h/2})`}/>
    </svg>
    <div style={{position:'absolute',left:'50%',top:textDy,transform:`translateX(calc(-50% + ${textDx}px))`,fontFamily:'Caveat',fontSize,color,fontWeight:600,whiteSpace:'nowrap'}}>{text}</div>
  </div>;
};

// TransitionIn：锁定转场三式，只包入场场景（出场场景保持静止或自行淡出）。
// flip=纸张翻入（隐喻切换时用）/ slide=滑盖覆盖 / wipe=边缘擦除。
const TransitionIn:React.FC<{kind:'flip'|'slide'|'wipe';start:number;duration?:number;frame?:number;color?:string;children?:React.ReactNode}>=({kind,start,duration=16,frame,color=C.orange,children})=>{
  const f=frame??q(useCurrentFrame());
  const {mode}=useCanvas();
  const p=easeOutSoft(f,start,start+duration);
  if(p<=0)return null;
  if(kind==='flip')return <div style={{position:'absolute',inset:0,perspective:1600}}>
    <div style={{position:'absolute',inset:0,transform:`rotateY(${-70*(1-p)}deg)`,transformOrigin:'0 50%',opacity:Math.min(1,p*2.2),boxShadow:`14px 0 44px rgba(40,30,20,${.18*(1-p)})`}}>{children}</div>
  </div>;
  if(kind==='slide')return <div style={{position:'absolute',inset:0,transform:`translateX(${(1-p)*mode.designW}px)`,boxShadow:`-16px 0 48px rgba(40,30,20,${.2*p})`}}>{children}</div>;
  return <div style={{position:'absolute',inset:0,overflow:'hidden'}}>
    <div style={{position:'absolute',inset:0,clipPath:`inset(0 ${(1-p)*100}% 0 0)`}}>{children}</div>
    <div style={{position:'absolute',top:0,bottom:0,left:`calc(${p*100}% - 3px)`,width:6,background:color,opacity:p<1?1:0}}/>
  </div>;
};

// ---- 标准化新奇交互组件库（防 PPT 化与功能实体化）------------------------
// 1. BrainwaveEEG：脑电/示波仪（动态活跃认知脉冲 -> 会话中断/清空瞬间拉平直线 Flatline）
const BrainwaveEEG: React.FC<{ frame: number; deadStart?: number; width?: number | string }> = ({ frame, deadStart = 99999, width = '100%' }) => {
  const isDead = frame >= deadStart;
  const pDead = ease(frame, deadStart, deadStart + 16);
  const W = 680, H = 48;
  const pts: string[] = [];
  const freq = 0.14;
  for (let x = 0; x <= W; x += 6) {
    const normX = x / W;
    const wave = Math.sin(frame * freq + normX * 18) * Math.cos(normX * 8);
    const spike = (x > 220 && x < 260) ? Math.sin((x - 220) / 40 * Math.PI) * 16 : 0;
    const y = H / 2 - (wave * 8 + spike) * (1 - pDead);
    pts.push(`${x},${y.toFixed(1)}`);
  }
  return (
    <div style={{ width, background: '#121212', borderRadius: 8, border: `2px solid ${isDead ? C.red : '#2b303c'}`, padding: '8px 14px', position: 'relative', overflow: 'hidden', boxShadow: `2.5px 2.5px 0 ${C.ink}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 8, height: 8, borderRadius: 99, background: isDead ? C.red : C.green, boxShadow: `0 0 6px ${isDead ? C.red : C.green}` }} />
          <span style={{ fontFamily: 'Space,monospace', fontSize: 12, fontWeight: 700, color: isDead ? C.red : '#adb5bd', letterSpacing: 0.8 }}>
            {isDead ? 'ALERT: CONTEXT FLUSHED (FLATLINE)' : 'LIVE AGENT COGNITIVE PULSE'}
          </span>
        </div>
        <span style={{ fontFamily: 'Space,monospace', fontSize: 11, color: isDead ? C.red : C.green, fontWeight: 700 }}>
          {isDead ? '0 RECALLED' : 'SYNCED: 100%'}
        </span>
      </div>
      <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} style={{ overflow: 'visible' }}>
        <line x1="0" y1={H / 2} x2={W} y2={H / 2} stroke="#222" strokeWidth="1" strokeDasharray="4 4" />
        <polyline points={pts.join(' ')} fill="none" stroke={isDead ? C.red : C.green} strokeWidth={isDead ? 2.5 : 1.8} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
};

// 2. VectorRadarSonar：向量雷达声呐仪（360°旋转波束扫描 + 高维语义聚类点高亮）
const VectorRadarSonar: React.FC<{ frame: number; color?: string }> = ({ frame, color = C.blue }) => {
  const rot = (frame * 3.5) % 360;
  const dots = [
    { x: 45, y: 35, col: C.blue }, { x: 105, y: 65, col: C.green }, { x: 70, y: 95, col: C.gold },
    { x: 125, y: 30, col: C.blue }, { x: 35, y: 105, col: C.green }, { x: 90, y: 115, col: C.blue },
  ];
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '12px 16px', background: '#f5f9ff', border: `2px solid ${color}`, borderRadius: 10, boxShadow: `2.5px 2.5px 0 ${color}` }}>
      <div style={{ position: 'relative', width: 78, height: 78, flex: '0 0 78px', background: '#0e1726', borderRadius: 999, border: `2px solid ${color}`, overflow: 'hidden' }}>
        <svg width="78" height="78" viewBox="0 0 140 140">
          <circle cx="70" cy="70" r="26" fill="none" stroke="rgba(43,109,232,0.35)" strokeWidth="1.2" />
          <circle cx="70" cy="70" r="52" fill="none" stroke="rgba(43,109,232,0.35)" strokeWidth="1.2" />
          <line x1="70" y1="0" x2="70" y2="140" stroke="rgba(43,109,232,0.25)" strokeWidth="1" />
          <line x1="0" y1="70" x2="140" y2="70" stroke="rgba(43,109,232,0.25)" strokeWidth="1" />
          {dots.map((d, i) => (
            <circle key={i} cx={d.x} cy={d.y} r="3.5" fill={d.col} style={{ opacity: 0.8 + 0.2 * Math.sin(frame * 0.25 + i) }} />
          ))}
          <g transform={`rotate(${rot} 70 70)`}>
            <line x1="70" y1="70" x2="140" y2="70" stroke={color} strokeWidth="2.2" opacity="0.95" />
            <polygon points="70,70 140,40 140,70" fill="rgba(43,109,232,0.28)" />
          </g>
        </svg>
      </div>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 18, fontWeight: 700, color }}>向量雷达检索空间</span>
          <span style={{ fontSize: 11, background: color, color: '#fff', padding: '1px 6px', borderRadius: 4, fontWeight: 700 }}>EMBEDDINGS</span>
        </div>
        <div style={{ fontSize: 13, color: '#444', marginTop: 3, lineHeight: 1.3, fontWeight: 600 }}>高维语义聚类 · 毫秒级最近邻检索 (ANN)</div>
        <div style={{ display: 'flex', gap: 6, marginTop: 5 }}>
          <span style={{ fontSize: 11, fontFamily: 'Space,monospace', background: '#e1ecfe', color, padding: '2px 6px', borderRadius: 4, fontWeight: 700 }}>Append-Only</span>
          <span style={{ fontSize: 11, fontFamily: 'Space,monospace', background: '#e1ecfe', color, padding: '2px 6px', borderRadius: 4, fontWeight: 700 }}>Local Zero-Cloud</span>
        </div>
      </div>
    </div>
  );
};

// 3. BM25TokenRibbon：BM25 符号倒排标尺（动态词频矩阵与代码变量命中标签）
const BM25TokenRibbon: React.FC<{ frame: number; tokens?: { name: string; score: string; active: boolean }[] }> = ({ frame, tokens = [
  { name: 'auth_spec', score: '0.98', active: true },
  { name: 'rs256_key', score: '0.94', active: true },
  { name: 'db_pool', score: '0.91', active: false },
  { name: 'redis_ttl', score: '0.86', active: false },
] }) => {
  return (
    <div style={{ padding: '12px 16px', background: '#fffcf0', border: `2px solid ${C.gold}`, borderRadius: 10, boxShadow: `2.5px 2.5px 0 ${C.gold}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 18, fontWeight: 700, color: C.ink }}>BM25 符号倒排矩阵</span>
          <span style={{ fontSize: 11, background: C.gold, color: C.ink, padding: '1px 6px', borderRadius: 4, fontWeight: 700 }}>INVERTED INDEX</span>
        </div>
        <span style={{ fontSize: 11, fontFamily: 'Space,monospace', color: '#666', fontWeight: 600 }}>{tokens.filter(t => t.active).length} Tokens Matched</span>
      </div>
      <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {tokens.map((tk, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, background: tk.active ? '#fff' : '#f8f8f8', border: `1.5px solid ${tk.active ? C.gold : '#ccc'}`, borderRadius: 6, padding: '3px 8px', boxShadow: tk.active ? `1.5px 1.5px 0 ${C.ink}` : 'none' }}>
            <span style={{ fontFamily: 'Space,monospace', fontSize: 12, fontWeight: 700, color: C.ink }}>#{tk.name}</span>
            <span style={{ fontFamily: 'Space,monospace', fontSize: 11, background: tk.active ? '#fff3cd' : '#eee', color: tk.active ? '#b07200' : '#888', padding: '1px 4px', borderRadius: 3, fontWeight: 700 }}>{tk.score}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// 4. HookMountBay：自动钩子卡扣插槽（物理插头卡入 + 锁紧变绿灯）
const HookMountBay: React.FC<{ frame: number; dockStart?: number; portLabel?: string; hookName?: string }> = ({ frame, dockStart = 0, portLabel = '~/.claude/settings.json', hookName = 'funes_hook' }) => {
  const isDocked = frame >= dockStart;
  const dockP = easeOutSoft(frame, dockStart, dockStart + 20);
  return (
    <div style={{ background: '#1c1815', border: `2.2px solid ${C.ink}`, borderRadius: 10, padding: '12px 16px', boxShadow: `3px 3px 0 ${C.ink}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 10, height: 10, borderRadius: 99, background: isDocked ? C.green : C.gold, boxShadow: `0 0 8px ${isDocked ? C.green : C.gold}` }} />
          <span style={{ fontFamily: 'Space,monospace', fontSize: 12, fontWeight: 700, color: isDocked ? C.green : C.gold, letterSpacing: 0.8 }}>
            {isDocked ? 'AGENT HOOK: MOUNTED & LOCKED' : 'WAITING FOR HOOK INJECTION'}
          </span>
        </div>
        <span style={{ fontSize: 11, fontFamily: 'Space,monospace', color: '#999' }}>PORT: {portLabel}</span>
      </div>
      <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, transform: `translateX(${interpolate(dockP, [0, 1], [-18, 0])}px)` }}>
          <div style={{ background: '#2b6de8', color: '#fff', fontSize: 12, fontWeight: 700, padding: '4px 10px', borderRadius: 6, border: '1.2px solid #000' }}>
            🔌 {hookName}
          </div>
          <span style={{ color: isDocked ? C.green : '#666', fontSize: 15 }}>➔</span>
          <div style={{ background: isDocked ? '#ebfbee' : '#2d2825', border: `1.8px solid ${isDocked ? C.green : '#444'}`, color: isDocked ? C.green : '#888', fontSize: 12, fontWeight: 700, padding: '4px 12px', borderRadius: 6 }}>
            {isDocked ? '✔ Session Hook Registered' : 'Empty Hook Port'}
          </div>
        </div>
        {isDocked && (
          <span style={{ fontSize: 11, background: '#1e382b', color: C.green, border: `1px solid ${C.green}`, padding: '2px 8px', borderRadius: 4, fontWeight: 700 }}>
            AUTO PASSIVE SYNC
          </span>
        )}
      </div>
    </div>
  );
};

// 5. RedactionScanner：敏感信息实时脱敏扫描仪（红外光束扫过实时掩码打码）
const RedactionScanner: React.FC<{ frame: number; scanStart?: number; rawKey?: string; redactedKey?: string }> = ({ frame, scanStart = 0, rawKey = 'sk-live-99882410941829', redactedKey = '[REDACTED_SECRET_KEY_*****]' }) => {
  const isScanning = frame >= scanStart;
  const p = ease(frame, scanStart, scanStart + 35);
  const scanX = interpolate(p, [0, 1], [0, 100]);
  return (
    <div style={{ background: '#14110f', border: `2.2px solid ${C.ink}`, borderRadius: 10, padding: '12px 16px', position: 'relative', overflow: 'hidden', boxShadow: `3px 3px 0 ${C.ink}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <LineIcon kind="shield" size={16} color={C.green} />
          <span style={{ fontFamily: 'Space,monospace', fontSize: 12, fontWeight: 700, color: '#e0e0e0', letterSpacing: 0.8 }}>
            GATEWAY SCANNER · SENSITIVE REDACTOR
          </span>
        </div>
        <span style={{ fontSize: 10, fontFamily: 'Space,monospace', background: p >= 0.8 ? '#143823' : '#332612', color: p >= 0.8 ? C.green : C.gold, padding: '1px 6px', borderRadius: 4, fontWeight: 700 }}>
          {p >= 0.8 ? 'PROTECTED (SANITIZED)' : 'INSPECTING TOKENS'}
        </span>
      </div>
      <div style={{ position: 'relative', background: '#1f1b18', padding: '8px 12px', borderRadius: 6, fontFamily: 'Space,monospace', fontSize: 13, display: 'flex', alignItems: 'center', justifyContent: 'space-between', overflow: 'hidden' }}>
        <div>
          <span style={{ color: '#888' }}>raw_trace: </span>
          <span style={{ color: p > 0.4 ? C.green : '#ff7b72', fontWeight: 700 }}>
            {p > 0.4 ? `api_key: "${redactedKey}"` : `api_key: "${rawKey}"`}
          </span>
        </div>
        {p > 0.6 && (
          <span style={{ background: C.green, color: '#fff', fontSize: 10, fontWeight: 700, padding: '1px 6px', borderRadius: 3 }}>
            PASSED
          </span>
        )}
        {isScanning && p < 1 && (
          <div style={{ position: 'absolute', left: `${scanX}%`, top: 0, bottom: 0, width: 2.5, background: '#ff3b30', boxShadow: '0 0 8px #ff3b30' }} />
        )}
      </div>
    </div>
  );
};

// 6. ChipContract：微硬件芯片流转卡（LED 灯 + 合约编号 + 沿管道流转）
const ChipContract: React.FC<{ x: number; y: number; title: string; subtitle?: string; scale?: number; opacity?: number }> = ({ x, y, title, subtitle, scale = 1, opacity = 1 }) => {
  return (
    <div style={{ position: 'absolute', left: x, top: y, zIndex: 95, padding: '10px 18px', background: '#0e1726', border: `2.2px solid ${C.blue}`, borderRadius: 10, boxShadow: `3.5px 3.5px 0 ${C.ink}`, opacity, transform: `translate(-50%, -50%) scale(${scale})`, display: 'flex', alignItems: 'center', gap: 12 }}>
      <div style={{ width: 10, height: 10, borderRadius: 99, background: C.green, boxShadow: `0 0 6px ${C.green}` }} />
      <div>
        <div style={{ fontSize: 11, fontFamily: 'Space,monospace', fontWeight: 700, color: C.blue, letterSpacing: 0.8 }}>{title}</div>
        {subtitle && <div style={{ fontSize: 15, fontWeight: 700, color: '#ffffff', marginTop: 1 }}>{subtitle}</div>}
      </div>
    </div>
  );
};

// camScript：镜头脚本构建器——链式声明 hold/to，自动补齐首尾帧，免手刻关键帧表。
// 铁律（Camera Micro-Framing Invariant）：X 轴位移严格约束在 [945, 975] 范围（漂移 <= ±15px），S 约束在 [1.00, 1.018]，绝不可大幅右甩导致左侧被讲解内容出界！
type CamKey={f:number;s:number;x:number;y:number};
const camScript=(x:number,y:number,duration:number)=>{
  const keys:CamKey[]=[{f:0,s:1,x,y}];let cur={x,y,s:1};
  const api={hold:(f:number)=>{keys.push({f,...cur});return api},to:(f:number,p:Partial<{x:number;y:number;s:number}>)=>{cur={...cur,...p};keys.push({f,...cur});return api},done:()=>{keys.push({f:duration,...cur});return keys}};
  return api;
};

// 严谨消除句末标点符号（保留句中逗号，句末逗号句号等一概消除）
const cleanTail=(s:string)=>s.replace(/[，。！？；：、,.!?;:\s]+$/g,'');
const Subtitle=()=>{
  const {mode}=useCanvas();
  const f=useRawCurrentFrame(),lead=Math.round(FPS*.18),hold=Math.round(FPS*.05);
  let cue=captions.find((c:any)=>f>=c.startFrame-lead&&f<=c.endFrame+hold);
  if(!cue)cue=[...captions].reverse().find((c:any)=>c.startFrame<=f);
  const full=cue?cleanTail(cue.text):'';
  const targetChars=full.length;
  const words=cue?cue.words.filter((w:any)=>w.startFrame<=f+lead):[];
  let charSeq=0;
  return <THEME.SubtitleChrome mode={mode}>
    <span style={{position:'relative'}}>
        <span style={{visibility:'hidden'}}>{full}</span>
        <span style={{position:'absolute',left:0,top:0}}>
          {words.map((w:any,wi:number)=>{
            const part=String(w.part);
            const prev=wi>0?String(words[wi-1].part):'';
            const spaced=(wi>0&&!/[\s，。！？；：、,.!?;:（(]$/.test(prev)&&!/^[\s，。！？；：、,.!?;:）)]/.test(part)&&!((/[A-Za-z0-9]$/.test(prev)&&/^[A-Za-z0-9]/.test(part))||(/[一-鿿]$/.test(prev)&&/^[一-鿿]/.test(part))))?'\u00a0':'';
            return <span key={wi} style={{display:'inline-block'}}>{spaced}{part.split('').map((ch:any,ci:number)=>{
              const idx=charSeq++;
              if(idx>=targetChars) return null; // 铁律：严格消除任何词尾带出的句末标点符号
              const p=interpolate(f,[w.startFrame+ci*.9,w.startFrame+ci*.9+2.5],[0,1],{...clamp,easing:Easing.bezier(.16,1,.3,1)});
              return <span key={ci} style={{display:'inline-block',opacity:p,transform:`translateY(${6*(1-p)}px)`}}>{ch}</span>;
            })}</span>;
          })}
        </span>
    </span>
  </THEME.SubtitleChrome>;
};

const Chrome=()=>{
  const {isPortrait}=useCanvas();
  const f=q(useCurrentFrame()),stage=Math.max(0,CHAPTER_STARTS.filter((x)=>f>=x).length-1),local=f-CHAPTER_STARTS[stage],p=pop(local,-8),titles=COPY.chapterTitles;
  return <>
    <Paper lift={0.3} style={{left:isPortrait?40:92,top:isPortrait?80:74,width:isPortrait?330:392,height:isPortrait?76:82,zIndex:150,display:'flex',alignItems:'center',opacity:p,transform:`translateY(${14*(1-p)}px) scale(${.96+.04*p})`,overflow:'hidden',padding:0}}>
      <div style={{width:isPortrait?60:72,height:'100%',background:`linear-gradient(135deg,${C.orange},${C.orangeDeep})`,color:C.white,display:'grid',placeItems:'center',fontFamily:'Clash',fontWeight:600,fontSize:isPortrait?28:31,boxShadow:'inset -2px 0 6px rgba(0,0,0,0.1)'}}>{String(stage+1).padStart(2,'0')}</div>
      <div style={{padding:isPortrait?'8px 14px':'10px 18px',flex:1}}>
        <div style={{display:'flex',alignItems:'center',gap:6}}>
          <PillTag text={COPY.chromeKicker} color={C.blue} bg={C.blueLight} fontSize={TYPE.microS}/>
        </div>
        <JumpInText key={stage} items={[{text:titles[stage]}]} fontSize={TYPE.titleS} start={CHAPTER_STARTS[stage]+8} stagger={1.1} style={{marginTop:3,justifyContent:'flex-start'}}/>
      </div>
    </Paper>
    <div style={{position:'absolute',right:isPortrait?40:88,top:isPortrait?76:70,zIndex:140,textAlign:'right'}}>
      <div style={{fontSize:TYPE.labelM,fontWeight:700,letterSpacing:4,color:C.headerAccent,fontFamily:'Clash,Space'}}>{COPY.header}</div>
      <div style={{fontSize:TYPE.microL,marginTop:6,color:C.headerSub,fontFamily:'Space,Kai'}}>{COPY.headerSub}</div>
    </div>
  </>;
};

const stageFade=(f:number,start:number,end:number)=>ease(f,start,start+15)*ease(f,end-15,end,1,0);

const HANDOFF=10; // 镜头边界的交接帧数：下一镜开始时把上一镜末帧叠上来淡出，避免出现空帧
const FinalDemo=()=>{
  // 只挂载活动镜头（性能契约）：由分镜表决定当前是哪一镜。
  const f=q(useCurrentFrame());
  let idx=0;
  for(let i=0;i<SHOT_IDS.length;i++){ if(f>=SHOTS[SHOT_IDS[i]].from) idx=i; }
  const id=SHOT_IDS[idx];
  const s=SHOTS[id];
  const prevId=idx>0?SHOT_IDS[idx-1]:null;
  const Scene=SCENES[id];
  const PrevScene=prevId?SCENES[prevId]:null;
  const handoffP=prevId?Math.max(0,1-(f-s.from)/HANDOFF):0;
  return <>
    {PrevScene&&prevId&&handoffP>0.01&&(
      <div data-gate-allow="handoff" style={{position:'absolute',inset:0,zIndex:130,opacity:handoffP}}><PrevScene f={SHOTS[prevId].duration-1}/></div>
    )}
    {f<s.to&&<Scene f={f-s.from}/>}
  </>;
};


// 音效钉帧（硬规则）：一律相对所属镜头起点推导，改台词重跑解析后自动跟着走。
const SFX=SHOT_IDS.flatMap((id)=>{
  const s=SHOTS[id];
  const isChapter=(CHAPTER_STARTS as readonly number[]).includes(s.from);
  const list:{src:string;at:number;vol:number}[]=[
    {src:isChapter?'sfx/paper-rustle.wav':'sfx/paper-tap.wav',at:s.from+(isChapter?4:2),vol:isChapter?0.12:0.13},
    {src:'sfx/data-whoosh.wav',at:s.from+Math.round(s.duration*0.42),vol:0.11},
  ];
  const lastBeat=s.beats.length?s.beats[s.beats.length-1]:0;
  if(lastBeat>24) list.push({src:'sfx/chime.wav',at:s.from+Math.max(0,lastBeat-20),vol:0.15});
  if(s.cameraIntent!=='still') list.push({src:'sfx/click.ogg',at:s.from+(s.keys[2]?.f??30),vol:0.16});
  return list;
});
const Sound=()=>{
  const f=useCurrentFrame();
  const bgmVol=interpolate(f,[0,30,DURATION-45,DURATION],[0,0.08,0.08,0],{...clamp,easing:Easing.linear});
  return <>
    <Audio src={staticFile('narration.mp3')} volume={1}/>
    <Audio src={staticFile('sfx/bgm.mp3')} volume={bgmVol} loop/>
    {SFX.map((x,i)=><Sequence key={`${x.src}-${i}`} from={deliveryFrame(x.at)} layout="none"><Audio src={staticFile(x.src)} volume={x.vol}/></Sequence>)}
  </>;
};


const FilmLayout:React.FC<{canvas:CanvasMode}>=({canvas})=>{
  const mode=MODES[canvas]||MODES['16:9'];
  const isPortrait=canvas==='3:4';
  return <CanvasContext.Provider value={{canvas,isPortrait,mode}}>
    <AbsoluteFill style={{overflow:'hidden',background:C.paperBase}}>
      <div style={{position:'absolute',left:0,top:0,width:mode.designW,height:mode.designH,transform:`scale(${mode.scale})`,transformOrigin:'0 0',fontFamily:'Kai,sans-serif',color:C.ink,overflow:'hidden'}}>
        <Fonts/><AssetGate/><CaptionFitGate/><CardFitGate/><OverlapGate/><Sound/><Background/>
        {<><Chrome/><FinalDemo/></>}
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
  {/* 官方模板示例片（8 镜 / 4 骨架）。本版场景按 1920×1080 设计空间编写：
      4:3 与 3:4 需要各自的版面重排，不再用 scale(0.75) 信箱化冒充适配
      （见 references/canvas-modes.md 与 portrait-illustration-system.md）。 */}
  <Composition id="NotebookVideoFilm" component={Film16x9} durationInFrames={DURATION} fps={FPS} width={2560} height={1440}/>
  {/* 组件接触表：6 页 × 1 秒，1fps 抽帧即得 6 张图，供 AI 看图选型 */}
  <Composition id="NotebookVideoShowcase" component={Showcase} durationInFrames={SHOWCASE_PAGES*30} fps={FPS} width={1920} height={1080}/>
</>;

registerRoot(Root);