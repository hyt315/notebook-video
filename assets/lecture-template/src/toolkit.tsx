import React from 'react';
import {interpolate, interpolateColors, spring, useCurrentFrame} from 'remotion';
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
// `Paper` / `clamp` / `easeOutSoft` 三个局部 helper 本文件从未用上（tsc TS6133）；
// easeOutSoft 是 clamp 与 Easing 的唯一使用者，三个一起删，连带去掉 Easing 的 import。
const BASE_FPS = 30;
// 与 index.tsx 的 q() 同义：工程里 MOTION_FPS == BASE_FPS == 30，步长为 1，量化即恒等。
// （方向说明：是 index 的量化在 step=1 时退化为恒等，并非本模块另起一套。）
const q = (f: number) => f;
const smoothStep = (v: number) => { const t = Math.max(0, Math.min(1, v)); return t * t * (3 - 2 * t); };
// 与 index.tsx 的三档**逐参数一致**：v3.0.1 迁移时这两个值被写成 20/190 与 12/170，
// 与工程其它地方（fxkit.tsx / index.tsx）不一致，会让搬到本模块的组件动感偏移。
const SPRINGS = {
  soft: {damping: 17, stiffness: 132, mass: .86},
  snappy: {damping: 16, stiffness: 200, mass: .8},
  bouncy: {damping: 11, stiffness: 160, mass: .9},
} as const;
const popS = (f: number, start: number, preset: keyof typeof SPRINGS = 'soft') =>
  spring({frame: f - start, fps: BASE_FPS, config: SPRINGS[preset]});

/**
 * 停帧点缀（`references/motion-design.md` 的 Stop-motion accent，LOCKED motion pack 里的一条）：
 * "`useSteppedFrame(15)` quantizes a component to 15fps so each pose holds two output frames.
 *  Reserve it for sticker-style charm; never apply it to subtitles, transfers or the camera."
 *
 * ⚠️ 2026-09-21：这条契约此前**全树没有实现** —— 文档在教作者用一个不存在的名字
 * （正是本技能自己定义的缺陷类「文档里有、代码里没有」）。现在放回**场景可 import 的这一层**，
 * 而不是删文档：停帧是贴纸风的正经手法（theme-sticker 的定格质感就靠它），删掉等于丢掉一种动效，
 * 而实现只有一行、零依赖。
 * 两个入口，按拿到的是哪一种帧号选：
 *   · `stepped(f, 15)` —— 组件拿的是**镜内局部帧**（`<Scene f={f-s.from}/>`）时用这个，
 *     与 `enterAt(f, …)` / `popS(f, …)` 同一口径；这是场景里的常规写法。
 *   · `useSteppedFrame(15)` —— 组件不接帧参数、只能读**全局帧**时用（chrome / 接触表）。
 *     场景里误用它 = 又一次"局部帧 vs 全局帧"事故（见 `validate-frame-props.py` 钉的那一类）。
 */
export const stepped = (f: number, stepFps = 15) => Math.floor((f * stepFps) / BASE_FPS) * BASE_FPS / stepFps;
export const useSteppedFrame = (stepFps = 15) => stepped(useCurrentFrame(), stepFps);

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
export const Callout:React.FC<{x:number;y:number;w:number;h:number;text:string;textDy?:number;textDx?:number;color?:string;rotate?:number;start:number;frame?:number;fontSize?:number;style?:React.CSSProperties}>=({x,y,w,h,text,textDy=-46,textDx=0,color=C.orange,rotate=-2,start,frame,fontSize=22,style})=>{
  const f=frame??q(useCurrentFrame());
  const p=popS(f,start,'bouncy');
  // 画圈的两道椭圆是 `fill="none"` 的 SVG，不是实心层——OverlapGate 的 looksSolid 本来就不会把它判成遮挡物，
  // 所以这里**不加** data-gate-allow：标注文字是"另一条信息"，必须继续参与重叠判定（白名单只留给"同位置换信息"和镜头交接）。
  return <div style={{position:'absolute',left:x,top:y,width:w,height:h,zIndex:96,opacity:p,transform:`scale(${.7+.3*p}) rotate(${rotate}deg)`,transformOrigin:'50% 50%',...style}}>
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{overflow:'visible'}}>
      <ellipse cx={w/2} cy={h/2} rx={w/2-3} ry={h/2-3} fill="none" stroke={color} strokeWidth={2.6} strokeLinecap="round" transform={`rotate(-1.5 ${w/2} ${h/2})`}/>
      <ellipse cx={w/2} cy={h/2} rx={w/2-7} ry={h/2-6} fill="none" stroke={color} strokeWidth={1.6} opacity={.55} strokeDasharray="5 7" transform={`rotate(2 ${w/2} ${h/2})`}/>
    </svg>
    {/* Caveat 只有拉丁字形：中文标注会回落到 Kai（模板自己的中文字体），必须显式写出来，别让浏览器挑默认字体 */}
    <div style={{position:'absolute',left:'50%',top:textDy,transform:`translateX(calc(-50% + ${textDx}px))`,fontFamily:'Caveat,Kai',fontSize,color,fontWeight:600,whiteSpace:'nowrap'}}>{text}</div>
  </div>;
};

export const TOOLKIT_VERSION = 'toolkit-v1 · 3 修辞工具件（Callout / Checklist / JumpInText）· 自包含';
