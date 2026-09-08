import React from 'react';
import {Easing, interpolate, spring, staticFile, useCurrentFrame} from 'remotion';
import {THEME} from './theme/active';

// ============================================================================
// fxkit · 固定动效组件库 v1（反 PPT 专用）
// 设计原则：零新依赖（只用 remotion 原生 spring/interpolate）、只做
// transform/opacity 位移动画、cel 皮肤（2.5px 墨线 + 硬偏移阴影 + 纯平填充，
// 无渐变无模糊阴影）、30fps 确定性（无随机数，伪方差来自序号哈希）。
// 防出格铁律：所有文字容器高度必须由 fitH() 显式算出，禁止手写"看着差不多"
// 的固定高度——本片 S3/S5 的出格 bug 全部因此产生。
// 用法：import {FitCard, Typewriter, PayPop, StampSeal, ...} from './fxkit';
// 每个组件都接受 frame（本地帧）+ start，exitStart 出现即完整离场。
// 坐标铁律：x/y 永远相对于最近的 positioned 祖先。放在 Paper 卡片内部时，
// 坐标是"卡片相对坐标"（如卡片宽 1040，右下角 x≈850）；只有直接放在场景根
// div 下才是场景坐标。跨层放错是隐形 bug（渲染不报错但飞出屏）。
// ============================================================================

const C = THEME.palette;
const Burst = (THEME.extras as any).Burst as React.FC<{x:number;y:number;size:number;text:string;color?:string}>;

// 与主模板一致的字阶镜像（只取本库用到的档位）
export const FX_T = {displayL:50, displayS:36, titleM:28, titleS:27, titleXS:26, bodyM:24, labelL:22, labelM:21, labelS:20, microL:18} as const;

const clamp = {extrapolateLeft:'clamp' as const, extrapolateRight:'clamp' as const};
const BASE_FPS = 30;
const q = (f:number)=>f; // 调用方已做 q()；本库直接使用传入帧
const ease = (f:number,a:number,b:number,from=0,to=1)=>interpolate(f,[a,b],[from,to],{...clamp,easing:Easing.inOut(Easing.cubic)});
const easeOutSoft = (f:number,a:number,b:number,from=0,to=1)=>interpolate(f,[a,b],[from,to],{...clamp,easing:Easing.bezier(.16,1,.3,1)});
const SPRINGS = {snappy:{damping:16,stiffness:200,mass:.8},soft:{damping:17,stiffness:132,mass:.86},bouncy:{damping:11,stiffness:160,mass:.9}} as const;
const popS = (f:number,start:number,preset:keyof typeof SPRINGS='soft')=>spring({frame:f-start,fps:BASE_FPS,config:SPRINGS[preset]});
const useF = (frame?:number)=>frame??useCurrentFrame();
// 序号哈希伪方差（确定性）：0~1
const hash01 = (i:number)=>{const x=Math.sin(i*127.1+311.7)*43758.5453;return x-Math.floor(x);};

/** fitH：卡片内容高度 = 各行高 + 行间距 + 上下垫。调用方把行数算清楚再定高。 */
export const fitH = (rows:{h:number;gapAfter?:number}[],padTop:number,padBottom:number)=>{
  let h = padTop+padBottom;
  rows.forEach((r,i)=>{h+=r.h;if(i<rows.length-1)h+=(r.gapAfter??0);});
  return Math.ceil(h);
};

/** 离场样式：exitStart 之后 15 帧整体下移淡出（完整离场契约）。 */
const exitStyle = (f:number,exitStart:number|undefined):React.CSSProperties=>{
  if(exitStart===undefined) return {};
  const p = ease(f,exitStart,exitStart+15);
  return {opacity:1-p, transform:`translateY(${40*p}px)`};
};

// ---- 1. FitCard：防出格卡片。h 必须经 fitH() 算出后传入，超高内容直接断言 zichtbaar ----
export const FitCard:React.FC<{
  x:number;y:number;w:number;h:number;pad?:number;borderColor?:string;lift?:number;z?:number;
  frame?:number;start?:number;exitStart?:number;children?:React.ReactNode;style?:React.CSSProperties;
}> = ({x,y,w,h,pad=24,borderColor=C.line,lift=0.25,z=70,frame,start=0,exitStart,children,style})=>{
  const f = useF(frame);
  const p = popS(f,start,'soft');
  return <div style={{position:'absolute',left:x,top:y,width:w,height:h,zIndex:z,background:C.paper||'#ffffff',border:`2.5px solid ${borderColor}`,borderRadius:10,boxShadow:`3px 3px 0 ${C.ink}`,padding:pad,overflow:'hidden',opacity:p,transform:`translateY(${26*(1-p)}px)`,...exitStyle(f,exitStart),...style}}>{children}</div>;
};

// ---- 2. Typewriter：打字机。cps=字符/帧，标点后自动停顿，块光标闪烁 ----
export const Typewriter:React.FC<{
  text:string;fontSize?:number;color?:string;fontFamily?:string;fontWeight?:number|string;
  start?:number;cps?:number;frame?:number;cursor?:boolean;style?:React.CSSProperties;
}> = ({text,fontSize=30,color=C.ink,fontFamily='Kai',fontWeight=700,start=0,cps=0.4,frame,cursor=true,style})=>{
  const f = useF(frame);
  const chars = String(text).split('');
  let budget = (f-start)*cps, shown = 0;
  for(const ch of chars){ if(budget<1) break; shown++; budget-=1; if(/[，。！？；：、,.!?;:]/.test(ch)) budget-=5*cps+2; }
  const blink = Math.floor(f/9)%2===0;
  return <span style={{fontSize,fontFamily,fontWeight,color,...style}}>{chars.slice(0,Math.max(0,shown)).join('')}{cursor&&shown<chars.length&&<span style={{display:'inline-block',width:fontSize*0.5,height:fontSize*1.05,marginLeft:6,background:color,verticalAlign:'-2px',opacity:blink?0.9:0.1}}/>}</span>;
};

// ---- 3. PayPop：到账通知弹窗。从上滑入 + 金额滚动 + 可选 StampSeal 盖章 ----
export const PayPop:React.FC<{
  x:number;y:number;w:number;app?:string;title?:string;amount?:string;time?:string;
  start?:number;stampAt?:number;stampText?:string;frame?:number;exitStart?:number;
}> = ({x,y,w,app='PayPal',title='到账通知',amount='$100',time,start=0,stampAt,stampText='已完成',frame,exitStart})=>{
  const f = useF(frame);
  const p = popS(f,start,'snappy');
  const slide = interpolate(p,[0,1],[-140,0]);
  return <div style={{position:'absolute',left:x,top:y,width:w,zIndex:94,opacity:p,transform:`translateY(${slide}px)`,...exitStyle(f,exitStart)}}>
    <div style={{background:'#ffffff',border:`2.5px solid ${C.ink}`,borderRadius:12,boxShadow:`3.5px 3.5px 0 ${C.ink}`,padding:'14px 18px',overflow:'hidden'}}>
      <div style={{display:'flex',alignItems:'center',gap:10}}>
        <span style={{width:38,height:38,borderRadius:99,background:C.green,color:'#fff',display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:700,fontSize:22,flex:'0 0 auto'}}>$</span>
        <span style={{fontSize:FX_T.labelL,fontWeight:700,color:C.ink}}>{app} · {title}</span>
        {time&&<span style={{marginLeft:'auto',fontSize:FX_T.labelS,fontWeight:700,color:C.ink,background:'#eef4ff',border:`1.5px solid ${C.blue}`,borderRadius:999,padding:'2px 10px',whiteSpace:'nowrap'}}>{time}</span>}
      </div>
      <div style={{fontFamily:'Space',fontWeight:700,fontSize:44,color:C.green,marginTop:6}}>{amount}</div>
    </div>
    {stampAt!==undefined&&f>=stampAt&&<StampSeal text={stampText} x={w-150} y={-26} size={104} start={stampAt} frame={f} color={C.green}/>}
  </div>;
};

// ---- 4. StampSeal：印章砸下。2.6x → 1 回弹 + -8° 旋转 ----
export const StampSeal:React.FC<{
  text:string;color?:string;size?:number;x?:number;y?:number;start?:number;frame?:number;
}> = ({text,color=C.red,size=110,x=0,y=0,start=0,frame})=>{
  const f = useF(frame);
  if(f<start) return null;
  const p = easeOutSoft(f,start,start+9);
  const scale = interpolate(p,[0,1],[2.6,1]);
  return <div style={{position:'absolute',left:x,top:y,width:size,height:size,zIndex:98,opacity:Math.min(1,p*1.6),transform:`scale(${scale}) rotate(-8deg)`}}>
    <div style={{width:'100%',height:'100%',borderRadius:999,border:`4px solid ${color}`,display:'grid',placeItems:'center',background:'rgba(255,255,255,0.82)'}}>
      <span style={{fontWeight:700,fontSize:size*0.24,color,whiteSpace:'nowrap'}}>{text}</span>
    </div>
  </div>;
};

// ---- 5. Funnel：尝试漏斗。N 次尝试 → 宽进窄出 → 命中。widths 为归一化比例 ----
export const Funnel:React.FC<{
  x:number;y:number;w:number;rows:{label:string;sub:string;count:string;color:string;ratio:number}[];
  start?:number;stagger?:number;frame?:number;exitStart?:number;
}> = ({x,y,w,rows,start=0,stagger=22,frame,exitStart})=>{
  const f = useF(frame);
  return <div style={{position:'absolute',left:x,top:y,width:w,...exitStyle(f,exitStart)}}>
    {rows.map((r,i)=>{
      const s = start+i*stagger, p = popS(f,s,'soft');
      const wp = easeOutSoft(f,s+8,s+34);
      return <div key={r.label} style={{position:'relative',opacity:p,transform:`translateX(${-30*(1-p)}px)`,marginBottom:i<rows.length-1?14:0}}>
        <div style={{display:'flex',alignItems:'baseline',gap:10,marginBottom:6}}>
          <span style={{fontSize:FX_T.titleXS,fontWeight:700,color:C.ink}}>{r.label}</span>
          <span style={{fontSize:FX_T.labelL,fontWeight:700,color:r.color}}>{r.sub}</span>
          <span style={{marginLeft:'auto',fontFamily:'Space',fontWeight:700,fontSize:FX_T.titleM,color:r.color}}>{r.count}</span>
        </div>
        <div style={{height:26,background:'#efe9dc',borderRadius:99,border:`2px solid ${C.ink}`,overflow:'hidden'}}>
          <div style={{height:'100%',width:`${Math.max(4,r.ratio*100*wp)}%`,background:r.color,borderRadius:99}}/>
        </div>
        {[0,1,2].map(d=>{
          const cyc = (f-s-10+d*9+hash01(i*3+d)*9)%36;
          const dy = cyc<0?0:(cyc/36)*40;
          return <span key={d} style={{position:'absolute',left:`calc(${r.ratio*100}% - 4px)`,marginLeft:d*14-14,top:34+dy,width:8,height:8,borderRadius:99,background:r.color,opacity:cyc<0?0:Math.max(0,0.9-dy/50)}}/>;
        })}
      </div>;
    })}
  </div>;
};

// ---- 6. ChatThread：对话气泡。typing 三点 12 帧 → 气泡 pop，左右交替 ----
export const ChatThread:React.FC<{
  x:number;y:number;w:number;msgs:{side:'l'|'r';text:string;at:number}[];frame?:number;exitStart?:number;
}> = ({x,y,w,msgs,frame,exitStart})=>{
  const f = useF(frame);
  let dy = 0;
  return <div style={{position:'absolute',left:x,top:y,width:w,...exitStyle(f,exitStart)}}>
    {msgs.map((m,i)=>{
      const typing = f>=m.at&&f<m.at+12, shown = f>=m.at+12;
      const y0 = dy;
      if(shown) dy+=52; else if(typing) dy+=40;
      if(!typing&&!shown) return null;
      const mine = m.side==='r';
      return <div key={i} style={{position:'absolute',top:y0,left:mine?'auto':0,right:mine?0:'auto',maxWidth:'82%',opacity:shown?popS(f,m.at+12,'snappy'):1,transform:shown?`translateY(${14*(1-popS(f,m.at+12,'snappy'))}px) scale(${.92+.08*popS(f,m.at+12,'snappy')})`:'none'}}>
        {typing
          ? <span style={{display:'inline-flex',gap:5,background:'#ffffff',border:`2px solid ${C.ink}`,borderRadius:14,padding:'10px 14px'}}>{[0,1,2].map(d=><span key={d} style={{width:8,height:8,borderRadius:99,background:C.ink,opacity:.35+.55*Math.abs(Math.sin(f*0.5+d*0.9))}}/>)}</span>
          : <span style={{display:'inline-block',background:mine?C.blue:'#ffffff',color:mine?'#fff':C.ink,border:`2px solid ${mine?C.blue:C.ink}`,boxShadow:`2.5px 2.5px 0 ${C.ink}`,borderRadius:14,fontSize:FX_T.labelL,fontWeight:700,padding:'10px 16px'}}>{m.text}</span>}
      </div>;
    })}
    <div style={{height:dy}}/>
  </div>;
};

// ---- 7. MailScan：邮件确认。列表 → 激光扫过 → 目标行高亮 → 密钥打码，全程定高不溢出 ----
export const MailScan:React.FC<{
  x:number;y:number;w:number;rows:{from:string;subject:string;at:number}[];secret?:string;
  start?:number;frame?:number;exitStart?:number;
}> = ({x,y,w,rows,secret='收款邮箱',start=0,frame,exitStart})=>{
  const f = useF(frame);
  const rowH = 64, headH = 40, secH = 46;
  const h = 16+headH+10+rows.length*(rowH+8)+10+secH+16;
  return <div style={{position:'absolute',left:x,top:y,width:w,height:h,zIndex:74,background:'#14110f',border:`2.5px solid ${C.ink}`,borderRadius:10,boxShadow:`3px 3px 0 ${C.ink}`,padding:'16px 18px',overflow:'hidden',opacity:popS(f,start,'soft'),...exitStyle(f,exitStart)}}>
    <div style={{display:'flex',alignItems:'center',gap:8,height:headH}}>
      <span style={{width:10,height:10,borderRadius:99,background:C.green}}/>
      <span style={{fontFamily:'Space',fontSize:13,fontWeight:700,color:'#e8e8e8',letterSpacing:1}}>GMAIL · PAYPAL 通知</span>
      <span style={{marginLeft:'auto',fontSize:11,fontWeight:700,color:C.green,background:'#143823',padding:'2px 10px',borderRadius:999}}>{f>=start+rows.length*26+30?'已确认到账':'等待邮件'}</span>
    </div>
    <div style={{position:'relative',marginTop:10}}>
      {rows.map((r,i)=>{
        const at = start+i*26, hot = f>=at+30;
        return <div key={i} style={{height:rowH,marginBottom:8,background:hot?'#1e3a2a':'#1f1b18',border:`1.5px solid ${hot?C.green:'#3a332e'}`,borderRadius:8,padding:'8px 12px',opacity:f>=at?popS(f,at,'snappy'):0,overflow:'hidden'}}>
          <div style={{fontSize:13,fontWeight:700,color:hot?C.green:'#c9c2b8',whiteSpace:'nowrap'}}>{r.from}</div>
          <div style={{fontSize:15,fontWeight:700,color:'#fff',whiteSpace:'nowrap'}}>{r.subject}</div>
        </div>;
      })}
      {f>=start&&f<start+rows.length*26+34&&<div style={{position:'absolute',left:0,right:0,height:3,background:'#ff3b30',top:interpolate(ease(f,start,start+rows.length*26+34),[0,1],[0,rows.length*(rowH+8)])}}/>}
    </div>
    <div style={{height:secH,marginTop:10,background:'#1f1b18',borderRadius:8,display:'flex',alignItems:'center',gap:10,padding:'0 12px',overflow:'hidden'}}>
      <span style={{fontSize:13,fontWeight:700,color:'#888',whiteSpace:'nowrap'}}>{secret}</span>
      <span style={{fontSize:13,fontWeight:700,color:C.green,whiteSpace:'nowrap'}}>{f>=start+rows.length*26+30?'[已打码 · 绝不泄露]':'读取中…'}</span>
    </div>
  </div>;
};

// ---- 8. TimeRail：时间轨道。圆点沿轨行进，到 tick 弹出事件卡 ----
export const TimeRail:React.FC<{
  x:number;y:number;w:number;ticks:{t:string;label:string;color:string;at:number}[];frame?:number;exitStart?:number;
}> = ({x,y,w,ticks,frame,exitStart})=>{
  const f = useF(frame);
  const first = ticks[0]?.at??0, last = ticks[ticks.length-1]?.at??1;
  const prog = ease(f,first,last+40);
  return <div style={{position:'absolute',left:x,top:y,width:w,...exitStyle(f,exitStart)}}>
    <div style={{position:'relative',height:10,background:'#efe9dc',border:`2px solid ${C.ink}`,borderRadius:99,overflow:'hidden'}}>
      <div style={{position:'absolute',left:0,top:0,bottom:0,width:`${prog*100}%`,background:C.blue}}/>
    </div>
    <div style={{position:'relative',height:0}}>
      <div style={{position:'absolute',left:`calc(${prog*100}% - 11px)`,top:-26,width:22,height:22,borderRadius:99,background:C.orange,border:`2.5px solid ${C.ink}`}}/>
    </div>
    <div style={{display:'flex',justifyContent:'space-between',marginTop:22}}>
      {ticks.map(t=>{
        const p = f>=t.at?popS(f,t.at,'bouncy'):0;
        return <div key={t.t} style={{opacity:p,transform:`translateY(${-12*(1-p)}px) scale(${.8+.2*p})`,background:'#fff',border:`2px solid ${t.color}`,borderRadius:8,boxShadow:`2.5px 2.5px 0 ${C.ink}`,padding:'6px 12px',textAlign:'center'}}>
          <div style={{fontFamily:'Space',fontWeight:700,fontSize:FX_T.labelL,color:t.color}}>{t.t}</div>
          <div style={{fontSize:FX_T.labelS,fontWeight:700,color:C.ink,whiteSpace:'nowrap'}}>{t.label}</div>
        </div>;
      })}
    </div>
  </div>;
};

// ---- 9. CompareBars：对比条。两条宽度动画 + 差值 chip ----
export const CompareBars:React.FC<{
  x:number;y:number;w:number;rows:{label:string;pct:number;color:string;value:string}[];delta?:string;
  start?:number;stagger?:number;frame?:number;exitStart?:number;
}> = ({x,y,w,rows,delta,start=0,stagger=16,frame,exitStart})=>{
  const f = useF(frame);
  return <div style={{position:'absolute',left:x,top:y,width:w,...exitStyle(f,exitStart)}}>
    {rows.map((r,i)=>{
      const s = start+i*stagger, wp = easeOutSoft(f,s+6,s+36);
      return <div key={r.label} style={{marginBottom:i<rows.length-1?12:0,opacity:popS(f,s,'soft')}}>
        <div style={{display:'flex',alignItems:'baseline',marginBottom:5}}>
          <span style={{fontSize:FX_T.labelL,fontWeight:700,color:C.ink}}>{r.label}</span>
          <span style={{marginLeft:'auto',fontFamily:'Space',fontWeight:700,fontSize:FX_T.titleXS,color:r.color}}>{r.value}</span>
        </div>
        <div style={{height:20,background:'#efe9dc',border:`2px solid ${C.ink}`,borderRadius:99,overflow:'hidden'}}>
          <div style={{height:'100%',width:`${Math.max(3,r.pct*100*wp)}%`,background:r.color,borderRadius:99}}/>
        </div>
      </div>;
    })}
    {delta&&f>=start+rows.length*stagger&&<div style={{marginTop:10,opacity:popS(f,start+rows.length*stagger,'bouncy')}}><span style={{fontSize:FX_T.labelL,fontWeight:700,color:C.green,background:'#e3f5e9',border:`1.5px solid ${C.green}`,borderRadius:999,padding:'4px 14px'}}>{delta}</span></div>}
  </div>;
};

// ---- 10. ProgressRing：进度环。stroke-dashoffset 旋转填充 + 中央标签 ----
export const ProgressRing:React.FC<{
  size?:number;pct:number;label?:string;color?:string;start?:number;duration?:number;frame?:number;
}> = ({size=96,pct,label,color=C.green,start=0,duration=36,frame})=>{
  const f = useF(frame);
  const p = easeOutSoft(f,start,start+duration);
  const R = (size-14)/2, len = 2*Math.PI*R;
  return <div style={{width:size,height:size,position:'relative',flex:'0 0 auto'}}>
    <svg width={size} height={size}>
      <circle cx={size/2} cy={size/2} r={R} fill="none" stroke="#efe9dc" strokeWidth={11}/>
      <circle cx={size/2} cy={size/2} r={R} fill="none" stroke={color} strokeWidth={11} strokeLinecap="round" strokeDasharray={len} strokeDashoffset={len*(1-Math.max(0,Math.min(1,pct))*p)} transform={`rotate(-90 ${size/2} ${size/2})`}/>
    </svg>
    <div style={{position:'absolute',inset:0,display:'grid',placeItems:'center',textAlign:'center'}}>
      <div><div style={{fontFamily:'Space',fontWeight:700,fontSize:22,color}}>{Math.round(pct*100*p)}%</div>{label&&<div style={{fontSize:11,fontWeight:700,color:C.ink}}>{label}</div>}</div>
    </div>
  </div>;
};

// ---- 11. ShakeX：强调抖动。落点后 ±amp 衰减摆 3 次（锤框/警告用） ----
export const ShakeX:React.FC<{start?:number;dur?:number;amp?:number;frame?:number;children?:React.ReactNode}> = ({start=0,dur=20,amp=7,frame,children})=>{
  const f = useF(frame);
  const t = f-start;
  const dx = t<0||t>dur?0:amp*Math.sin(t*1.9)*(1-t/dur);
  return <div style={{position:'absolute',inset:0,pointerEvents:'none',transform:`translateX(${dx}px)`}}>{children}</div>;
};

// ---- 12. BurstCallout：cel 爆炸贴纸安全 wrapper（超 3 字自动截断，保证皮肤契约） ----
export const BurstCallout:React.FC<{x:number;y:number;size?:number;text:string;color?:string;start?:number;frame?:number}> = ({x,y,size=120,text,color,start=0,frame})=>{
  const f = useF(frame);
  if(f<start||!Burst) return null;
  return <div style={{position:'absolute',inset:0,zIndex:97,opacity:popS(f,start+8,'bouncy')}}><Burst x={x} y={y} size={size} text={String(text).slice(0,3)} color={color}/></div>;
};

// ---- 13. StaggerList：通用 stagger 列表（ Linear 式"秩序感"级联，防 bullets 堆砌） ----
export const StaggerList:React.FC<{
  x:number;y:number;w:number;items:{icon?:string;text:string;sub?:string;color:string}[];start?:number;stagger?:number;frame?:number;exitStart?:number;
}> = ({x,y,w,items,start=0,stagger=14,frame,exitStart})=>{
  const f = useF(frame);
  return <div style={{position:'absolute',left:x,top:y,width:w,...exitStyle(f,exitStart)}}>
    {items.map((it,i)=>{
      const s = start+i*stagger, p = popS(f,s,'soft');
      return <div key={it.text} style={{display:'flex',alignItems:'center',gap:12,marginBottom:i<items.length-1?10:0,opacity:p,transform:`translateX(${30*(1-p)}px) rotate(${(1-p)*1.2}deg)`}}>
        <span style={{width:34,height:34,borderRadius:99,background:it.color,color:'#fff',display:'grid',placeItems:'center',fontFamily:'Space',fontWeight:700,fontSize:16,flex:'0 0 auto',border:`2px solid ${C.ink}`}}>{it.icon??i+1}</span>
        <span style={{fontSize:FX_T.titleXS,fontWeight:700,color:C.ink}}>{it.text}</span>
        {it.sub&&<span style={{fontSize:FX_T.labelM,fontWeight:700,color:it.color}}>{it.sub}</span>}
      </div>;
    })}
  </div>;
};

export const FXKIT_VERSION = 'fxkit-v2 · 18 components · cel-locked · no new deps';

// ---- 14. KenBurnsImg：克制推近。只放大不移出框（父容器须 overflow:hidden），scale 1→zoom ----
export const KenBurnsImg:React.FC<{
  src:string;zoom?:number;dur?:number;start?:number;frame?:number;fit?:'width'|'height';style?:React.CSSProperties;
}> = ({src,zoom=1.045,dur=90,start=0,frame,fit='width',style})=>{
  const f = useF(frame);
  const p = easeOutSoft(f,start,start+dur);
  return <div style={{overflow:'hidden',...style}}>
    {fit==='width'
      ? <img src={staticFile(src)} style={{width:'100%',display:'block',transform:`scale(${1+(zoom-1)*p})`,transformOrigin:'50% 45%'}}/>
      : <img src={staticFile(src)} style={{height:'100%',width:'auto',margin:'0 auto',display:'block',transform:`scale(${1+(zoom-1)*p})`,transformOrigin:'50% 50%'}}/>}
  </div>;
};

// ---- 15. EvidenceZoom：证据三节拍。识别（全景）→定位（推近焦点）→落结论（chip） ----
export const EvidenceZoom:React.FC<{
  src:string;fx?:number;fy?:number;zoom?:number;at?:number;label?:string;
  frame?:number;style?:React.CSSProperties;
}> = ({src,fx=0.5,fy=0.5,zoom=1.8,at=0,label,frame,style})=>{
  const f = useF(frame);
  if(f<at) return null;
  const box = (style||{}) as {width?:number;height?:number};
  const W = typeof box.width==='number'?box.width:900, H = typeof box.height==='number'?box.height:260;
  const p = easeOutSoft(f,at+40,at+100);
  const s = 1+(zoom-1)*p;
  const tx = (0.5-fx)*W*s, ty = (0.5-fy)*H*s;
  const chip = f>=at+100?popS(f,at+100,'bouncy'):0;
  return <div style={{position:'relative',overflow:'hidden',...style}}>
    <img src={staticFile(src)} style={{width:'100%',display:'block',transform:`translate(${tx}px,${ty}px) scale(${s})`,transformOrigin:'0 0'}}/>
    {label&&chip>0&&<span style={{position:'absolute',left:12,bottom:12,fontSize:FX_T.labelL,fontWeight:700,color:'#fff',background:C.green,border:`2px solid ${C.ink}`,borderRadius:999,padding:'4px 16px',opacity:chip,transform:`translateY(${10*(1-chip)}px)`,whiteSpace:'nowrap'}}>{label}</span>}
  </div>;
};

// ---- 16. DiffView：补丁 diff。红删绿加，逐行滑入，等宽 Space 字体 ----
export const DiffView:React.FC<{
  x:number;y:number;w:number;title?:string;lines:{k:'-'|'+'|' ';text:string;at:number}[];frame?:number;exitStart?:number;
}> = ({x,y,w,title='patch.diff',lines,frame,exitStart})=>{
  const f = useF(frame);
  return <div style={{position:'absolute',left:x,top:y,width:w,background:'#14110f',border:`2.5px solid ${C.ink}`,borderRadius:10,boxShadow:`3px 3px 0 ${C.ink}`,overflow:'hidden',...exitStyle(f,exitStart)}}>
    <div style={{height:30,display:'flex',alignItems:'center',gap:7,paddingLeft:14,borderBottom:'1.5px solid #2d2621'}}>
      {[C.red,C.gold,C.green].map((c,i)=><span key={i} style={{width:9,height:9,borderRadius:99,background:c}}/>)}
      <span style={{marginLeft:6,fontFamily:'Space',fontWeight:600,fontSize:12,letterSpacing:1,color:'#fdfdfb',opacity:.85}}>{title}</span>
    </div>
    <div style={{padding:'12px 16px',display:'flex',flexDirection:'column',gap:7}}>
      {lines.map((ln,i)=>{
        if(f<ln.at) return null;
        const p = popS(f,ln.at,'snappy');
        const col = ln.k==='-'?'#ff7b72':ln.k==='+'?C.green:'#c9c2b8';
        return <div key={i} style={{display:'flex',gap:10,fontFamily:'Space,monospace',fontWeight:600,fontSize:15,color:ln.k===' '?'#fdfdfb':col,background:ln.k===' '?'none':ln.k==='-'?'rgba(255,59,48,.12)':'rgba(36,188,110,.12)',borderRadius:6,padding:'3px 10px',opacity:p,transform:`translateX(${16*(1-p)}px)`,whiteSpace:'nowrap',overflow:'hidden'}}><span>{ln.k}</span><span>{ln.text}</span></div>;
      })}
    </div>
  </div>;
};

// ---- 17. ConfettiPop：到账庆祝。N 碎片从中心炸开，旋转下落后淡出（确定性角度） ----
export const ConfettiPop:React.FC<{
  x:number;y:number;maxR?:number;n?:number;start?:number;dur?:number;frame?:number;
}> = ({x,y,maxR=260,n=26,start=0,dur=55,frame})=>{
  const f = useF(frame);
  if(f<start||f>start+dur) return null;
  const p = easeOutSoft(f,start,start+dur);
  const cols = [C.orange,C.blue,C.green,C.gold,C.red];
  return <div style={{position:'absolute',left:0,top:0,zIndex:97,pointerEvents:'none'}}>
    {Array.from({length:n}).map((_,i)=>{
      const ang = (i/n)*Math.PI*2+hash01(i)*0.5;
      const dist = (60+hash01(i+99)*(maxR-60))*p;
      const fade = f>start+dur-15?(start+dur-f)/15:1;
      return <span key={i} style={{position:'absolute',left:x+Math.cos(ang)*dist,top:y+Math.sin(ang)*dist*0.8+40*p, width:i%3===0?12:8,height:i%3===1?12:8,borderRadius:i%2?'99px':'2px',background:cols[i%cols.length],border:`1.5px solid ${C.ink}`,opacity:Math.max(0,fade),transform:`rotate(${i*47+p*220}deg)`}}/>;
    })}
  </div>;
};

// ---- 18. SkeletonCard：骨架→内容。等待 beats（如等评审）先占位，再 pop 出真内容 ----
export const SkeletonCard:React.FC<{
  x:number;y:number;w:number;h:number;rows?:number;start?:number;revealAt?:number;frame?:number;children?:React.ReactNode;
}> = ({x,y,w,h,rows=3,start=0,revealAt=60,frame,children})=>{
  const f = useF(frame);
  const shown = f>=revealAt, p = shown?popS(f,revealAt,'soft'):0;
  const pulse = 0.55+0.25*Math.sin(f*0.3);
  return <div style={{position:'absolute',left:x,top:y,width:w,height:h,background:'#ffffff',border:`2.5px solid ${C.ink}`,borderRadius:10,boxShadow:`3px 3px 0 ${C.ink}`,padding:20,overflow:'hidden',opacity:popS(f,start,'soft')}}>
    {!shown&&<div style={{display:'flex',flexDirection:'column',gap:12,opacity:pulse}}>{Array.from({length:rows}).map((_,i)=><div key={i} style={{height:22,borderRadius:6,background:'#e8e2d6',width:`${92-hash01(i)*30}%`}}/>)}</div>}
    {shown&&<div style={{opacity:p,transform:`translateY(${16*(1-p)}px)`}}>{children}</div>}
  </div>;
};
