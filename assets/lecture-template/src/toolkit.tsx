import React from 'react';
import {Easing, interpolate, interpolateColors, spring, useCurrentFrame} from 'remotion';
import {THEME} from './theme/active';
import {TYPE, LineIcon} from './kit';

// ============================================================================
// toolkit.tsx · 可被场景直接 import 的"修辞工具"组件（v3.0.1 从 index.tsx 迁出）
//
// 为什么独立成文件：这些组件原先定义在 index.tsx 里且**没有 export**，场景文件在物理上无法
// import —— 这是"仓库里 54 件组件、成片里 27 件零使用"的结构性真因之一。直接在 index.tsx 上
// export 会造成循环依赖（index → scenes → index），因此迁到本模块。
//
// 与 index.tsx 的关系：本文件**刻意不 import index.tsx**；下面几个 helper 与 index.tsx 的同名
// 实现一致但各自持有——这是为避免循环依赖而做的重复，不是疏忽。
// 注意：本项目的 MOTION_FPS == BASE_FPS == 30，所以 index.tsx 的 q() 实为恒等，这里同样不做量化。
//
// 怎么选：**先查 references/media-routing.md 的「修辞动作 → 组件」表**（含"何时别用"），
// 再决定用哪一件。表里标了禁用的动作请照做。
// ============================================================================

const C = THEME.palette;
const Paper = THEME.Paper;
const BASE_FPS = 30;
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const q = (f: number) => f;
const easeOutSoft = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, b], [from, to], {...clamp, easing: Easing.bezier(.16, 1, .3, 1)});
const smoothStep = (v: number) => { const t = Math.max(0, Math.min(1, v)); return t * t * (3 - 2 * t); };
const SPRINGS = {
  soft: {damping: 17, stiffness: 132, mass: .86},
  snappy: {damping: 20, stiffness: 190, mass: .8},
  bouncy: {damping: 12, stiffness: 170, mass: .9},
} as const;
const popS = (f: number, start: number, preset: keyof typeof SPRINGS = 'soft') =>
  spring({frame: f - start, fps: BASE_FPS, config: SPRINGS[preset]});

export const Mascot:React.FC<{size?:number;f?:number;wave?:boolean}>=({size=180,f=0,wave=false})=>{
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
export const RollDigit:React.FC<{fromChar:string;toChar:string;start:number;duration?:number;frame?:number;fontSize:number;fontFamily?:string;fontWeight?:number|string;colorFrom?:string;colorTo?:string;style?:React.CSSProperties}>=({fromChar,toChar,start,duration=13,frame,fontSize,fontFamily,fontWeight=700,colorFrom=C.muted,colorTo=C.green,style})=>{
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
export const JumpInText:React.FC<{
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
export const WaveText:React.FC<{text:string;fontSize:number;colorFrom:string;colorTo:string;start:number;stagger?:number;frame?:number;fontFamily?:string;fontWeight?:number;letterSpacing?:number;style?:React.CSSProperties}>=({text,fontSize,colorFrom,colorTo,start,stagger=1.2,frame,fontFamily,fontWeight=600,letterSpacing=0,style})=>{
  const f=frame??q(useCurrentFrame());
  return <div style={{display:'flex',justifyContent:'center',alignItems:'baseline',...style}}>
    {text.split('').map((ch,i)=>{const age=f-(start+i*stagger);const wave=smoothStep(age/10),col=interpolateColors(smoothStep(age/8),[0,1],[colorFrom,colorTo]);const wx=interpolate(wave,[.0,.28,.64,1],[10,-3,1,0]);const wy=interpolate(wave,[.0,.28,.64,1],[16,-16,4,0]);return <span key={i} style={{display:'inline-block',fontSize,fontFamily,fontWeight,letterSpacing,color:col,opacity:smoothStep((age+0.4)/1.5),transform:`translate(${wx}px,${wy}px)`}}>{ch}</span>})}
  </div>;
};
export const CodeBlock:React.FC<{title?:string;lines:{text:string;color?:string;prefix?:string;start?:number}[];start?:number;frame?:number;stagger?:number;cursor?:boolean;style?:React.CSSProperties}>=({title='terminal',lines,start=0,frame,stagger=8,cursor=false,style})=>{
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
export const BrowserChrome:React.FC<{url:string;children?:React.ReactNode;lift?:number;style?:React.CSSProperties}>=({url,children,lift=.2,style})=>
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
export const Connector:React.FC<{from:{x:number;y:number};to:{x:number;y:number};bend?:number;color?:string;flow?:boolean;arrow?:boolean;label?:string;labelColor?:string;width?:number;frame?:number;style?:React.CSSProperties}>=({from,to,bend=46,color=C.blue,flow=false,arrow=true,label,labelColor,width=2.8,frame,style})=>{
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
export const Checklist:React.FC<{items:string[];start:number;frame?:number;stagger?:number;colors?:string[];done?:number;rowH?:number;fontSize?:number;style?:React.CSSProperties}>=({items,start,frame,stagger=20,colors,done=-1,rowH=48,fontSize=TYPE.titleXS,style})=>{
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
export const CountUp:React.FC<{to:number;from?:number;start:number;duration?:number;frame?:number;fontSize?:number;fontFamily?:string;fontWeight?:number|string;color?:string;colorFrom?:string;prefix?:string;suffix?:string;style?:React.CSSProperties}>=({to,from=0,start,duration=30,frame,fontSize=TYPE.displayS,fontFamily='Space',fontWeight=700,color=C.green,colorFrom=C.muted,prefix='',suffix='',style})=>{
  const f=frame??q(useCurrentFrame());
  const p=easeOutSoft(f,start,start+duration);
  const v=Math.round(from+(to-from)*p);
  const col=interpolateColors(p,[0,1],[colorFrom,color]);
  return <span style={{fontFamily,fontSize,fontWeight,color:col,fontVariantNumeric:'tabular-nums',...style}}>{prefix}{v}{suffix}</span>;
};
export const ProgressBar:React.FC<{v:number;color?:string;height?:number;label?:string;showPct?:boolean;style?:React.CSSProperties}>=({v,color=C.green,height=14,label,showPct=false,style})=>{
  const pct=Math.round(Math.max(0,Math.min(1,v))*100);
  return <div style={{...style}}>
    {(label||showPct)&&<div style={{display:'flex',justifyContent:'space-between',alignItems:'baseline',marginBottom:6}}>
      {label&&<span style={{fontSize:TYPE.labelL,fontWeight:700,color:C.ink}}>{label}</span>}
      {showPct&&<span style={{fontFamily:'Space',fontWeight:700,fontSize:TYPE.labelL,color,fontVariantNumeric:'tabular-nums'}}>{pct}%</span>}
    </div>}
    <div style={{height,background:C.gaugeTrack,borderRadius:99,overflow:'hidden'}}>
      <div style={{height:'100%',width:'100%',background:color,borderRadius:99,transformOrigin:'left center',transform:`scaleX(${Math.max(0,Math.min(1,v))})`}}/>
    </div>
  </div>;
};
export const Callout:React.FC<{x:number;y:number;w:number;h:number;text:string;textDy?:number;textDx?:number;color?:string;rotate?:number;start:number;frame?:number;fontSize?:number;style?:React.CSSProperties}>=({x,y,w,h,text,textDy=-46,textDx=0,color=C.orange,rotate=-2,start,frame,fontSize=22,style})=>{
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

export const TOOLKIT_VERSION = 'toolkit-v1 · 11 修辞工具件 · 自包含（不依赖 index）';
