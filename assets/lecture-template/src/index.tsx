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
import {Mascot, RollDigit, JumpInText, WaveText, CodeBlock, BrowserChrome, Connector, Checklist, CountUp, ProgressBar, Callout} from './toolkit';
import type {IconKind} from './kit';
import {PillTag, LineIcon, CheckBadge, TYPE} from './kit';
// v2.10 视觉体系四层：镜头 / 骨架 / 介质 / 门禁。用法见 references/shot-language.md、
// scene-skeletons.md、media-routing.md、composition-gate.md。
import {CoverPanel, DepthLayers, ShotCamera, camAt, shotCam, stillCam} from './shotkit';
import {Attach, PhaseRail, StageFrame, useStageMachine} from './stagekit';
import {InsertShot, RevealMask, TRANSITIONS, useHandoff} from './insert';
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
  // v2.11 修复三处静默失效（实测量出来的，不是推测）：
  //   a. 旧版开头 `if(document.fonts.status!=='loaded') return;` —— 实测某帧 fonts=loading，
  //      整桶直接跳过，且从不等待字体就绪（字幕门是 await document.fonts.ready 的）；
  //      被压到 40px 的卡片明明算出溢出，也走不到报警那一步。现改为等字体就绪后补测。
  //   b. 旧版用 offsetParent 链做累加再 `if(m!==card) return;` —— 实测 87 个文字块里 18 个
  //      在链上断裂（逐字动画的 span、Takeaway 文本等），这些文字**从未被校验过**。
  //      现改用 getBoundingClientRect 与卡片的 padding 盒比较（与 OverlapGate 同一口径，
  //      天然包含 transform，不依赖 offsetParent）。
  //   c. 旧版零输出既可能是"全部合格"也可能是"根本没跑"。现每 5 秒打一次覆盖率。
  useEffect(()=>{
    let cancelled=false;
    const measure=()=>{
      try{
        const bad:string[]=[];
        // "卡片"= 有不透明/渐变底 **且** 有边框的元素（纯渐变无边框的整幅底托不算卡片）
        const solid=(el:Element)=>{const s=getComputedStyle(el as HTMLElement);
          const m=/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/.exec(s.backgroundColor||'');
          const alpha=m?(m[4]===undefined?1:parseFloat(m[4])):0;
          const grad=s.backgroundImage&&s.backgroundImage!=='none'?1:0;
          return ((alpha>0.9||grad>0)&&parseFloat(s.borderTopWidth)>0);};
        let cards=0;
        // 判据是"卡片内容是否超出卡片"（overflow 的定义）：
        // 逐叶元素比较 rect 会被内联元素的行盒外延误报（实测单字“费”出 3px，其实没溢出）。
        // scrollHeight 会把溢出的内容也算进去，和 overflow 属性无关，是最稳的口径。
        document.querySelectorAll<HTMLElement>('div,span').forEach((card)=>{
          if(!solid(card)) return;
          if(card.closest('[data-fit-skip]')) return;
          if(!card.textContent||!card.textContent.trim()) return;
          if(card.getBoundingClientRect().width<8) return;
          // 只判会被裁剪的容器：overflow:visible 的容器用 scrollHeight 会把绝对定位子元素
          // 也算进去（实测 MetricGrid 虚增 180–213px，其实没有任何文字被裁）
          if(getComputedStyle(card).overflow==='visible') return;
          const cz=parseInt(getComputedStyle(card).zIndex||'0',10);
          if(cz>=145) return;                       // 章节卡 150 / 字幕 200 是锁定覆盖层，各自由门
          cards++;
          // 容差 6px：内联元素的行盒取整会产生 3–4px 的“假溢出”，真裁切一般 ≥10px
          const oB=card.scrollHeight-card.clientHeight,oR=card.scrollWidth-card.clientWidth;
          // vertical overflow clips whole lines -> report on its own (6px tolerance).
          // horizontal overflow is usually a decoration (leader line, focus dot, hard shadow) crossing the
          // content box; only flag it when *text* really crosses the edge (8px tolerance).
          let textOver = 0, textSample = '';
          if (oR > 8) {
            const cr3 = card.getBoundingClientRect();
            const lim3 = cr3.right - (parseFloat(getComputedStyle(card).borderRightWidth) || 0);
            card.querySelectorAll<HTMLElement>('div,span,p').forEach((tel) => {
              if (!tel.textContent || !tel.textContent.trim() || tel.children.length > 0) return;
              const r3 = tel.getBoundingClientRect();
              if (r3.width * r3.height < 4) return;
              const o = r3.right - lim3;
              if (o > textOver) { textOver = o; textSample = (tel.textContent || '').trim().slice(0, 10); }
            });
          }
          // 竖向容差 10px：不足一行高（≥30px）的差异读作降部/行盒舍入，不是“丢了一行”；
          // 真裁切实测都在 25px 以上（S2 卡片 25px、控制台 27px）。
          if (oB > 10 || textOver > 8) bad.push(`@${f} \u5361\u7247\u201c${(card.textContent||'').trim().slice(0,10)}\u201d\u6ea2\u51fa ${Math.round(Math.max(oB, textOver))}px${textSample ? '\uff08\u6587\u5b57\uff1a' + textSample + '\uff09' : ''}`);
        });
        if(bad.length) cancelRender(new Error(`Card overflow: ${bad.slice(0,4).join(' | ')}`));
        else if(cards&&f%150===0&&typeof console!=='undefined') console.warn(`[CardFitGate] @${f} \u5df2\u6d4b ${cards} \u5f20\u5361\u7247\uff0c\u65e0\u6ea2\u51fa`);
      }catch(e){if(typeof console!=='undefined') console.warn('[CardFitGate]',e);}
    };
    const id=requestAnimationFrame(()=>{
      if(document.fonts.status==='loaded'){measure();return;}
      document.fonts.ready.then(()=>{if(!cancelled) measure();}).catch(()=>{});
    });
    return ()=>{cancelled=true;cancelAnimationFrame(id);};
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

// RollDigit：Tibo 式字符/数字 3D 滚轮翻牌——带 cos 投影压缩 + 3D 旋转 + 颜色过渡

const smoothStep=(v:number)=>{const t=Math.max(0,Math.min(1,v));return t*t*(3-2*t)};

// JumpInText：完全移植 Tibo 源码的“4段双轴弹性波浪回弹 + 字色激活”动效（经视效平衡调谐）

// WaveText：Tibo 式字母波浪打字——每字母 4 段关键帧波浪 + 颜色渐变

// ---- 通用组件扩展（v2.5 新增）------------------------------------------
// SPRINGS：弹性预设三档。soft 与历史 pop() 默认参数完全一致，旧场景行为不变。
const SPRINGS={snappy:{damping:16,stiffness:200,mass:.8},soft:{damping:17,stiffness:132,mass:.86},bouncy:{damping:11,stiffness:160,mass:.9}} as const;
const popS=(f:number,start:number,preset:keyof typeof SPRINGS='soft')=>spring({frame:f-start,fps:BASE_FPS,config:SPRINGS[preset]});

// useSteppedFrame：停帧点缀（默认 15fps，每个姿势占两输出帧，契约见 motion-design.md）。
const useSteppedFrame=(stepFps=15)=>{const f=useCurrentFrame();return Math.floor(f*stepFps/BASE_FPS)*BASE_FPS/stepFps};

// CodeBlock：终端风代码窗——三灯标题栏 + 语法色行 + 逐行滑入，精致墨边紧凑投影。

// BrowserChrome：浏览器窗口——三灯 + 锁 + URL 胶囊，内容区放 children。

// Connector：曲线连接件——贝塞尔弧线 + 可选流向虚线 / 箭头 / 标签，替代场景层手写 SVG。

// Checklist：编号步骤清单——圆形序号 + 文案逐个滑入；done 给完成数，序号变对勾。

// CountUp：数字滚动计数——easeOutSoft 进度 + 颜色过渡，支持前后缀。

// ProgressBar：进度条——轨道 + 填充 + 可选标签/百分比，v 由场景驱动（0~1）。

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
// 中间节拍轮换用的三种"落位/切换"音（必须在 SFX 之前声明：flatMap 立即执行）
const SECOND=['sfx/drop.ogg','sfx/toggle.ogg','sfx/click.ogg'];
const SFX=SHOT_IDS.flatMap((id)=>{
  const s=SHOTS[id];
  const isChapter=(CHAPTER_STARTS as readonly number[]).includes(s.from);
  const list:{src:string;at:number;vol:number}[]=[];
  // v3.0.1：音效从"按镜头比例"改为**绑定节拍（beats）**。
  // 旧规则把 whoosh 钉在时长的 42% 处——那一帧画面上什么都没有，正是 tts-audio.md 明令禁止的
  // "把音效放在看不见的动作上"。节拍数组本身就是"讲到这一句"的时刻，视觉也在这里落，
  // 所以按节拍钉帧既对得上画面，又沿用同一套自动重定时机制。
  if (isChapter) list.push({src:'sfx/paper-rustle.wav',at:s.from+4,vol:0.38});   // 换章：翻纸
  s.beats.forEach((b:number,i:number)=>{
    const at=s.from+b;
    if(i===0) list.push({src:'sfx/paper-tap.wav',at,vol:0.34});                  // 首拍：落纸
    else if(i===s.beats.length-1) list.push({src:'sfx/chime.wav',at,vol:0.40});   // 末拍：完成音
    else list.push({src:SECOND[i%SECOND.length],at,vol:0.30});                    // 中间拍：轮换落位/切换/轻击
  });
  if(s.cameraIntent!=='still') list.push({src:'sfx/click.ogg',at:s.from+(s.keys[2]?.f??30),vol:0.26});
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


// 门禁事件帧（v2.11）：本技能最密集的重叠都发生在短窗口里——镜头交接 10 帧、页眉滑变 7–16 帧、数值滑动 14 帧。
// 只按 15 帧网格抽样必然漏掉它们，所以把镜头边界、节拍、相机关键帧都交给 OverlapGate 强制抽样。
const WATCH=(()=>{const out:number[]=[];SHOT_IDS.forEach((id:string)=>{const s:any=(SHOTS as any)[id];out.push(s.from-1,s.from,s.from+1,s.to-1,s.to);(s.beats||[]).forEach((b:number)=>out.push(s.from+b));(s.keys||[]).forEach((k:any)=>out.push(s.from+k.f));});return out;})();
const FilmLayout:React.FC<{canvas:CanvasMode}>=({canvas})=>{
  const mode=MODES[canvas]||MODES['16:9'];
  const isPortrait=canvas==='3:4';
  return <CanvasContext.Provider value={{canvas,isPortrait,mode}}>
    <AbsoluteFill style={{overflow:'hidden',background:C.paperBase}}>
      <div style={{position:'absolute',left:0,top:0,width:mode.designW,height:mode.designH,transform:`scale(${mode.scale})`,transformOrigin:'0 0',fontFamily:'Kai,sans-serif',color:C.ink,overflow:'hidden'}}>
        <Fonts/><AssetGate/><CaptionFitGate/><CardFitGate/><OverlapGate mode="block" watch={WATCH}/><Sound/><Background/>
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
