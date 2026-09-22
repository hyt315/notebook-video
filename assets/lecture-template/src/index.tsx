import React,{useEffect,useRef,useState} from 'react';
import {AbsoluteFill,Composition,Easing,Sequence,cancelRender,continueRender,delayRender,interpolate,registerRoot,spring,staticFile,useCurrentFrame as useRawCurrentFrame} from 'remotion';
import {Audio} from '@remotion/media';
import cueData from './caption-cues.json';

// ============================================================================
// LECTURE TEMPLATE · 讲课式默认模板（纯代码 SVG，不依赖任何生图能力）
//
// 本文件分三层，改写时只碰第三层：
//   第一层 LOCKED：美学核心 + 字幕/背景/章节条/资产门，一律不改。
//   第二层 组件库：Paper、LineIcon、CheckBadge、PillTag、StampBanner 等，
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
import {JumpInText} from './toolkit';
import {PillTag, TYPE} from './kit';
// v2.10 视觉体系四层：镜头 / 骨架 / 介质 / 门禁。用法见 references/shot-language.md、
// scene-skeletons.md、media-routing.md、composition-gate.md。
// 四层组件按需 import —— tsconfig 开了 noUnusedLocals，导了不用会被 tsc 判错，
// 所以这里只留本文件真用到的，其余列名备查：
//   shotkit    CoverPanel / ShotCamera / camAt / shotCam / stillCam
//   stagekit   PhaseRail / StageFrame / useStageMachine
//   insert     RevealMask / TRANSITIONS / useHandoff
//   media      ConsoleWindow / MetricGrid / StampBanner
//   skeletons  Corridor / SplitStage / ZoomStage
import {Showcase, SHOWCASE_PAGES} from './showcase';
import {OverlapGate} from './overlap-gate';
import {ClippingGate} from './clipping-gate';
import {FillGate} from './fill-gate';
import {CanvasBoundsGate} from './canvas-bounds-gate';
import {SHOTS, SHOT_IDS, SHOT_TOTAL} from './shots';
import {SCENES} from './scenes';
const BASE_FPS=30,FPS=30,MOTION_FPS=30,TIMELINE_SCALE=1,DURATION=SHOT_TOTAL,DESIGN_SCALE=4/3;
const useCurrentFrame=()=>useRawCurrentFrame()*BASE_FPS/FPS/TIMELINE_SCALE;
const deliveryFrame=(designFrame:number)=>Math.round(designFrame*FPS*TIMELINE_SCALE/BASE_FPS);

// LOCKED AESTHETIC CORE：美学核由主题包提供（src/theme/active.ts 选定），
// 调色板 / 美学参数 / 卡片皮肤 / 背景 / 调色层全部来自 THEME，本层不做任何风格判断。
const C=THEME.palette;
const AESTHETIC=THEME.aesthetic;
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
  // 2026-09-21 实测修掉一处**静默失效**（由 demo 的 `CardFitFixture` 负例逼出来）：
  // 本门禁的测量排在 requestAnimationFrame 里，却**没有 delayRender 兜住截帧**，
  // 于是 still 渲染会先截图、门禁永远来不及量——"260px 卡片里塞 560px 图表"这种
  // 397px 的真溢出照样出图，门禁等于不存在（字幕门一直是 delayRender+continueRender 的，
  // 本门禁漏了这一步）。现在持有 handle 到首次测量完成，门禁才真的会拦。
  const [fitHandle]=useState(()=>delayRender('cardfit measure',{timeoutInMilliseconds:60000}));
  const firstDone=useRef(false);
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
    // 2026-09-21 独立核验：本门禁**目前是拦得住的**，因为 cancelRender 之后的
    // `continueRender(fitHandle)` 还在 try 块内，抛异常就跳过了。但这纯属结构巧合：
    // 谁把 continueRender 挪到 try 之外，它就会静默退化成「报而不拦」（另三道门禁踩过）。
    // 故补上与其余门禁同一处置：判定作出后 blocked 置位（handle 永不释放），异常原样抛出。
    let blocked=false;
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
          // 只跳"标记者自己"（hasAttribute），**不用 closest**：closest 会连后代一起放过，
          // 于是缩放取景框里所有卡片的真实裁切都会漏检（交叉复核用 A/B 实渲证明过 248px 的裁切被漏）。
          if(card.hasAttribute('data-fit-skip')) return;
          if(!card.textContent||!card.textContent.trim()) return;
          if(card.getBoundingClientRect().width<8) return;
          // 只判会被裁剪的容器：overflow:visible 的容器用 scrollHeight 会把绝对定位子元素
          // 也算进去（实测 MetricGrid 虚增 180–213px，其实没有任何文字被裁）
          if(getComputedStyle(card).overflow==='visible') return;
          const cz=parseInt(getComputedStyle(card).zIndex||'0',10);
          // 字幕 200 仍跳过（它由 CaptionFitGate 量）；章节卡 150 改为**量测并 warn**：
          // v3.0.2 之前它被静默跳过，于是"章节标题太长被裁"从来没有任何门禁报警（实测踩过）。
          if(cz>=200) return;
          if(cz>=145){
            const oBmc=card.scrollHeight-card.clientHeight, oRmc=card.scrollWidth-card.clientWidth;
            if((oBmc>2||oRmc>2)&&typeof console!=='undefined')
              console.warn(`[CardFitGate] @${f} 章节卡内容溢出 ${Math.max(oBmc,oRmc)}px（标题过长？）：“${(card.textContent||'').trim().slice(0,14)}”`);
            return;
          }
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
        if(bad.length){blocked=true;cancelRender(new Error(`Card overflow: ${bad.slice(0,4).join(' | ')}`));}
        else if(cards&&f%150===0&&typeof console!=='undefined') console.warn(`[CardFitGate] @${f} \u5df2\u6d4b ${cards} \u5f20\u5361\u7247\uff0c\u65e0\u6ea2\u51fa`);
        // 首次测量完成 → 放开截帧（失败路径会 cancelRender，本来就不会出图）
        if(!firstDone.current){firstDone.current=true;continueRender(fitHandle);}
      }catch(e){if(blocked) throw e; if(typeof console!=='undefined') console.warn('[CardFitGate]',e);}
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
const CaptionFitGate=()=>{const {mode}=useCanvas();const safe=mode.safe,innerSafe=safe-(AESTHETIC.subtitlePadX??0),weight=AESTHETIC.subtitleWeight??400,ls=AESTHETIC.subtitleLetterSpacing??1.6;const ref=useRef<HTMLDivElement>(null),[done,setDone]=useState(false),[handle]=useState(()=>delayRender('measuring subtitle width',{timeoutInMilliseconds:60000}));useEffect(()=>{let live=true;let blocked=false;Promise.all([document.fonts.load(`${weight} ${mode.subFont}px Kai`),document.fonts.ready]).then(()=>requestAnimationFrame(()=>{if(!live)return;if(!ref.current){blocked=true;cancelRender(new Error('Subtitle measurement node is unavailable'));return}const rows=[...ref.current.querySelectorAll<HTMLElement>('[data-caption-fit]')];const widths=rows.map((row,index)=>({index,width:row.getBoundingClientRect().width/DESIGN_SCALE,text:row.textContent||''}));const overflow=widths.filter(row=>row.width>safe+.5);const tight=widths.filter(row=>row.width>innerSafe+.5&&row.width<=safe+.5);if(tight.length&&typeof console!=='undefined')console.warn(`[CaptionFitGate] ${tight.length} 条字幕超过内边距安全宽 ${innerSafe}px（未裁切但会顶到字幕框内边）：${tight.map(x=>`#${x.index+1} ${Math.ceil(x.width)}px`).join(' | ')}`);if(overflow.length){blocked=true;cancelRender(new Error(`Subtitle overflow: ${overflow.map(x=>`#${x.index+1} ${Math.ceil(x.width)}px>${safe}px ${x.text}`).join(' | ')}`));return}setDone(true);continueRender(handle)})).catch(error=>{if(live&&!blocked){blocked=true;cancelRender(error)}});return()=>{live=false}},[handle,mode.subFont,safe,innerSafe,weight,ls]);if(done)return null;return <div ref={ref} style={{position:'absolute',left:-10000,top:-10000,visibility:'hidden',fontFamily:'Kai,sans-serif',fontSize:mode.subFont,fontWeight:weight,whiteSpace:'nowrap',letterSpacing:ls}}>{captions.map((cue:any,index:number)=><span key={index} data-caption-fit style={{display:'block',width:'max-content'}}>{String(cue.text).replace(/[，。！？；：、,.!?;:\s]+$/g,'')}</span>)}</div>};

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
// smoothStep / SPRINGS+popS / easeOutSoft 在 toolkit.tsx / fxkit.tsx 里各有自己的一份
// （两个模块为免循环依赖刻意各自持有，不是遗漏）；本文件没人调用就不再留副本 ——
// tsconfig 开了 noUnusedLocals，未被读取的局部声明会直接判错。

// JumpInText：完全移植 Tibo 源码的“4段双轴弹性波浪回弹 + 字色激活”动效（经视效平衡调谐）





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
    <Paper lift={0.3} style={{left:isPortrait?40:92,top:isPortrait?80:74,width:isPortrait?330:392,height:isPortrait?84:90,zIndex:150,display:'flex',alignItems:'center',opacity:p,transform:`translateY(${14*(1-p)}px) scale(${.96+.04*p})`,overflow:'hidden',padding:0}}>
      <div style={{width:isPortrait?60:72,height:'100%',background:`linear-gradient(135deg,${C.orange},${C.orangeDeep})`,color:C.white,display:'grid',placeItems:'center',fontFamily:'Clash',fontWeight:600,fontSize:isPortrait?28:31,boxShadow:'inset -2px 0 6px rgba(0,0,0,0.1)'}}>{String(stage+1).padStart(2,'0')}</div>
      <div style={{padding:isPortrait?'6px 12px':'8px 16px',flex:1,minWidth:0}}>
        <div style={{display:'flex',alignItems:'center',gap:6}}>
          <PillTag text={COPY.chromeKicker} color={C.blue} bg={C.blueLight} fontSize={TYPE.microS}/>
        </div>
        {(() => {
          // v3.0.2：固定卡片里放可变长标题，必须"按可用宽自适应字号 + 禁止换行"。
          // 实测可用内宽 286px（392 − 2 描边 − 72 编号块 − 32 内边距），而 TYPE.titleS=27px 时
          // 「第三步 · 运营与三技能」实算 282.96px —— 只差不到 1px 就会折行，折行后即被 82 高的框裁掉。
          // 这里按字数算字号：CJK 按 1 字宽、ASCII/空格/间隔号按 0.55 折算，并夹到 [19, TYPE.titleS]。
          const title = String(titles[stage] ?? '');
          const units = [...title].reduce((n, ch) => n + (/[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]/.test(ch) ? 1 : 0.55), 0) || 1;
          const availW = isPortrait ? 214 : 286;
          const fitSize = Math.max(19, Math.min(TYPE.titleS, Math.floor(availW / units)));
          return <JumpInText key={stage} items={[{text:title}]} fontSize={fitSize}
            start={CHAPTER_STARTS[stage]+8} stagger={1.1}
            style={{marginTop:3,justifyContent:'flex-start',flexWrap:'nowrap',whiteSpace:'nowrap',overflow:'hidden',maxWidth:availW}}/>;
        })()}
      </div>
    </Paper>
    <div style={{position:'absolute',right:isPortrait?40:88,top:isPortrait?76:70,zIndex:140,textAlign:'right',maxWidth:isPortrait?560:1180,overflow:'hidden'}}>
      <div style={{fontSize:TYPE.labelM,fontWeight:700,letterSpacing:4,color:C.headerAccent,fontFamily:'Clash,Space'}}>{COPY.header}</div>
      <div style={{fontSize:TYPE.microL,marginTop:6,color:C.headerSub,fontFamily:'Space,Kai'}}>{COPY.headerSub}</div>
    </div>
  </>;
};

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
// 会运镜的意图名单（`still` 刻意不在内）：给「静止镜不出咔哒声」这条规则一个真判据。
const CAM_MOTION=['establish','push-in','pull-back','pan-follow','reveal','micro-orbit'] as const;
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
  // tsc TS2367 抓出来的死比较：`s.cameraIntent` 的推断类型里根本没有 'still'
  // （shots.ts 生成时只写 establish/push-in/pull-back/pan-follow/reveal），所以 `!== 'still'` 恒真。
  // 这句的意图是「静止镜不加咔哒声」，实际一个都没排除。改成**正向名单**：
  // 名单里没有的值（含将来的 'still'）不加音 —— 语义与作者本意一致，类型也干净。
  if((CAM_MOTION as readonly string[]).includes(s.cameraIntent)) list.push({src:'sfx/click.ogg',at:s.from+(s.keys[2]?.f??30),vol:0.26});
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
// ⚠️ 2026-09-21 独立核验补：本项目约定「落定帧 = 镜尾 − 12」（抽帧留档看的就是它），
// 而 `to−12` 一般不是 15 的倍数、也不在下面那些事件帧里 —— 实测上一版 21 张落定帧里
// **只有 1 张**落在抽样集合上，于是「对每一镜跑一遍门禁」等于什么都没量。
// 处置：把每镜的落定帧显式加进 WATCH —— **你要看的那一帧，门禁必须先看过**。
const WATCH=(()=>{const out:number[]=[];SHOT_IDS.forEach((id:string)=>{const s:any=(SHOTS as any)[id];out.push(s.from-1,s.from,s.from+1,s.to-1,s.to);out.push(s.to-12);(s.beats||[]).forEach((b:number)=>out.push(s.from+b));(s.keys||[]).forEach((k:any)=>out.push(s.from+k.f));});return out;})();
const FilmLayout:React.FC<{canvas:CanvasMode}>=({canvas})=>{
  const mode=MODES[canvas]||MODES['16:9'];
  const isPortrait=canvas==='3:4';
  return <CanvasContext.Provider value={{canvas,isPortrait,mode}}>
    <AbsoluteFill style={{overflow:'hidden',background:C.paperBase}}>
      {/* data-design-root：FillGate 靠它把「输出像素」折回「设计像素」（ratio 实测，不假设 --scale）。
    缺了它 FillGate 会静默 return —— 门禁装了等于没装，所以这个属性是门禁契约的一部分。 */}
      <div data-design-root style={{position:'absolute',left:0,top:0,width:mode.designW,height:mode.designH,transform:`scale(${mode.scale})`,transformOrigin:'0 0',fontFamily:'Kai,sans-serif',color:C.ink,overflow:'hidden'}}>
        <Fonts/><AssetGate/><CaptionFitGate/><CardFitGate/><OverlapGate mode="block" watch={WATCH}/><ClippingGate mode="block" watch={WATCH}/>
        {/* CanvasBoundsGate（v2 简版）：只判「**含文字的叶元素**的墨迹 rect 越出画布」。
            片子这条取 warn 而不是 block（2026-09-22 改，与接触表那条**不再同档**）：
            v2 的判据实测来源全是接触表，它在**片子**上还没有抓到过真缺陷；
            而这条门禁的硬拦发生在**交付渲染的最后一刻** —— 判据一旦误报，
            代价是「整片渲到最后一帧被打断、不出片」，比漏报一处 20px 的裁切贵得多。
            出水照样进渲染日志（每 150 帧还有一条覆盖率），交付前人工确认；
            等它在片子上抓到第一处真缺陷，再谈升回 block。
            口径与实测见 references/composition-gate.md §5.2 / §6。 */}
        <CanvasBoundsGate mode="warn"/>
        {/* FillGate 默认 warn：P0-4 是"观感线"，为它打断整片渲染不划算；出水进日志、可复查 */}
        <FillGate mode="warn" watch={WATCH}/><Sound/><Background/>
        {<><Chrome/><FinalDemo/></>}
        <Grade/>
        <Subtitle/>
      </div>
    </AbsoluteFill>
  </CanvasContext.Provider>;
};

const Film16x9=()=> <FilmLayout canvas="16:9"/>;
// 4:3 / 3:4 两个交付画布**定义但默认不注册**（契约见 references/canvas-modes.md）：
// 切换时自己改 canvas 参数并重排版面，不许用 scale(0.75) 信箱化冒充适配。
// 导出是为了过 noUnusedLocals —— 它们的使用方式是「作者在下面 Root 里挂上去」，不是被 import。
export const Film4x3=()=> <FilmLayout canvas="4:3"/>;
export const Film3x4=()=> <FilmLayout canvas="3:4"/>;

// 接触表 composition 的渲染期门禁（v1）：
// `NotebookVideoShowcase` 此前**一道门禁都没有** —— 第 ⑥ 页第三站的标签块越出画布右缘被裁
// （文案「按 Flash 结算」渲成「按 Flash 结」）就是这么漏掉的，这是**结构性**原因：
// 门禁全挂在 FilmLayout 里，接触表那条 composition 不经过它。
// 挂 CanvasBoundsGate 而不是整套：接触表是**组件目录**，格子里的件被 Tile 的
// overflow:hidden 裁住是有意设计（那是取景框），闸门只该管「有没有越出画布」这一件。
//
// 这条取 **block**（**与片子那条不同档**：片子是 warn，理由见 FilmLayout 里的注释），
// 经过两轮实测才敢这么取：
//   · 第一轮：门禁上线当天就抓出接触表自己的一处**真实同类缺陷** —— 第 ③ 页声明 5 件，
//     而 `Grid4` 只有 4 格，第 5 件（`FitTextBox · 中文反推字号（封装层）`）被摆到 top=1076，
//     整格落在 1080 高的画布**外面** 466px：渲出来的第 ③ 页只有 4 格，那件组件在接触表上
//     **根本看不见**（图已核）。那一轮为不阻断 `showcase` / `showcase-sheet`，先取 warn 让它出声。
//   · 第二轮（本轮）：`showcase.tsx` 第 ③ 页改成 5 格表（`Grid5`，3 列 × 2 行，格子 610×470、
//     舞台等比 0.7），5 件全部落在画布内；17 页在 block 下逐页抽帧跑过一遍，每页 rc=0 且有图，
//     无一处误报 —— 于是把 warn 收敛回 block。
// 判据上的理由：越出画布 = 件**整件看不见**或被切掉一块，属于**画错了**，
// 与「图形被裁」「文字互相压」同级，不是 FillGate 那种观感线；
// 而接触表是「看见才会用」的唯一入口（references/media-routing.md §6），件看不见就该中断渲染，
// 不能默默出一张缺件的目录页。
// v2 简版换实现后的复验（2026-09-22）：原样 6 页（帧 35/65/95/155/275/395）rc=0 有图零报告；
// 把 `showcase.tsx` 的两处历史缺陷各改回去一次，这条 block 档仍然**各自抓住**（26px×2 / 27px，rc=1 不出图）。
// 口径与实测表见 references/composition-gate.md §5.2。
const ShowcaseComposition=()=> <>
  <Showcase/>
  <CanvasBoundsGate mode="block"/>
</>;

const Root=()=> <>
  {/* 官方模板示例片（8 镜 / 4 骨架）。本版场景按 1920×1080 设计空间编写：
      4:3 与 3:4 需要各自的版面重排，不再用 scale(0.75) 信箱化冒充适配
      （见 references/canvas-modes.md 与 portrait-illustration-system.md）。 */}
  <Composition id="NotebookVideoFilm" component={Film16x9} durationInFrames={DURATION} fps={FPS} width={2560} height={1440}/>
  {/* 组件接触表：17 页 × 1 秒（`SHOWCASE_PAGES`），1fps 抽帧即得 17 张图，供 AI 看图选型 */}
  <Composition id="NotebookVideoShowcase" component={ShowcaseComposition} durationInFrames={SHOWCASE_PAGES*30} fps={FPS} width={1920} height={1080}/>
</>;

registerRoot(Root);
