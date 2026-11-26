import React,{useEffect,useRef,useState} from 'react';
import {AbsoluteFill,Composition,Easing,Img,Sequence,cancelRender,continueRender,delayRender,interpolate,registerRoot,staticFile,useCurrentFrame as useRawCurrentFrame} from 'remotion';
import {Audio} from '@remotion/media';
import cueData from '../manifests/caption-cues.json';  // 字幕只有这一份（manifests/），不再复制进 src/
import CONTRACT from './contract.json';

// ============================================================================
// LECTURE TEMPLATE · 讲课式默认模板（纯代码 SVG，不依赖任何生图能力）
//
// 本文件分三层，改写时只碰第三层：
//   第一层 LOCKED：美学核心 + 字幕/背景/章节条/资产门，一律不改。
//   第二层 组件库：Paper（卡片）、LineIcon、CheckBadge、PillTag、StampBanner 等，
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
// 画面组织六规范见 references/scenes.md#lecture-composition。
// ============================================================================

// Keep authored scene time separate from delivery frames.
import {MODES, CanvasContext, useCanvas} from './theme/canvas';
import {THEME} from './theme/active';
import {TYPE} from './kit';
import {clamp, EASE} from './motion';
// 视觉体系四层：镜头 / 骨架 / 介质 / 门禁。用法见 references/camera.md#shot-language、
// references/scenes.md#scene-skeletons、references/media.md#media-routing、references/checks.md#composition-gate。
// 四层组件按需 import —— tsconfig 开了 noUnusedLocals，导了不用会被 tsc 判错，
// 所以这里只留本文件真用到的，其余列名备查：
//   shotkit    CoverPanel / ShotCamera / camAt / shotCam / stillCam
//   stagekit   PhaseRail / StageFrame / useStageMachine
//   insert     RevealMask / TRANSITIONS / useHandoff
//   media      ConsoleWindow / MetricGrid / StampBanner
//   skeletons  Corridor / SplitStage / ZoomStage
import {OverlapGate} from './overlap-gate';
import {ClippingGate} from './clipping-gate';
import {FillGate} from './fill-gate';
import {CanvasBoundsGate} from './canvas-bounds-gate';
import {MascotGate} from './mascot-gate';
import {GROW_VAR, GlyphSnap, REVEAL_BLEED, revealClip} from './glyph-snap';
import {planSfx, bedDuckAt, voiceDuckFactor, SFX_BED, BED_GAIN} from './sfx';
import {MUSIC_ON} from './audio-config';
import {CINEMA, cinemaCamAt, cinemaMask, cinemaTransform, parallaxTransform, resolveTransition, transitionFrames, transitionStyle, whipOffset} from './cinema';
import {FxProbe, PageCurl, curlShadow, isCurl} from './fx';
import {PageFold} from './transitions/pagefold';
import {SHOTS, SHOT_IDS, SHOT_TOTAL, SFX_DENSITY} from './shots';
import {SCENES} from './scenes';
import {AssetGate, FontFaces, loadThemeFonts} from './fonts';
import type {BgVariant} from './theme/types';
const BASE_FPS=30,FPS=CONTRACT.FPS,MOTION_FPS=30,TIMELINE_SCALE=1,DURATION=SHOT_TOTAL,DESIGN_SCALE=4/3;
const useCurrentFrame=()=>useRawCurrentFrame()*BASE_FPS/FPS/TIMELINE_SCALE;
const deliveryFrame=(designFrame:number)=>Math.round(designFrame*FPS*TIMELINE_SCALE/BASE_FPS);

// LOCKED AESTHETIC CORE：美学核由主题包提供（src/theme/active.ts 选定），
// 调色板 / 美学参数 / 卡片皮肤 / 背景 / 调色层全部来自 THEME，本层不做任何风格判断。
const C=THEME.palette;
const AESTHETIC=THEME.aesthetic;
const Background=THEME.Background;
const Grade=THEME.Grade;

// EDITABLE CONTENT SURFACE — 换题材时改 src/film.ts（auto 流程会自动生成它）
import {COPY, CHAPTER_SHOTS} from './film';
import * as FILM from './film';
import {captionGap} from './caption-gap';
// 章节卡标题的自适应字号（同一能力的唯一实现，不在调用处另行估算）。
import {fitChineseTextOnNLines} from './components/fittext';

/** 方向模糊滤镜（SVG feGaussianBlur，只在 X 方向）。id 唯一，按帧给 stdDeviation。
 *  svg-id: singleton —— 进 / 出各一枚、固定在合成层，不随镜头重复（见下方 url(#nv-whip-*)）。 */
const WhipBlur: React.FC<{id: string; amount: number}> = ({id, amount}) => (
  <svg width={0} height={0} style={{position: 'absolute'}} aria-hidden>
    <filter id={id} x="-20%" y="-5%" width="140%" height="110%" colorInterpolationFilters="sRGB">
      <feGaussianBlur stdDeviation={`${Math.max(0, amount).toFixed(2)} 0`} />
    </filter>
  </svg>
);

const CHAPTER_STARTS=CHAPTER_SHOTS.map((id)=>SHOTS[id].from);

const msFrame=(ms:number)=>Math.round(ms*FPS/1000);
const captions=((cueData as any).cues as any[]).map(c=>({...c,startFrame:msFrame(c.start_ms),endFrame:msFrame(c.speech_end_ms),words:c.words.map((w:any)=>({...w,startFrame:msFrame(w.start),endFrame:msFrame(w.end)}))}));
const q=(f:number)=>{const step=BASE_FPS/MOTION_FPS;return Math.floor(f/step)*step};

// Clash Display 不入库（ITF FFL 禁止经仓库再分发），按需从 Fontshare 下载到工程 public/fonts/；离线没下到时
// 这两条 load 会因 404 拒绝，catch 掉后 CSS 栈 'Clash,Space,Kai' 自然落到 Space Grotesk（P1 提示由 CLI 打出）。
// FontGate：字体就绪之前**不挂载画面层**。章节卡标题等组件在 render 里同步量字宽，而量字宽的两层缓存
// （fittext.tsx 的 widthCache、@remotion/layout-utils 的 wordCache）会永久记下字体就绪前的回退宽度；
// 单帧 still 与连续渲染会因此量出不同字号。就绪标志是单调的（只会 false→true），两种渲法截图时都为 true。
let FONTS_OK=false;
const useFontGate=()=>{const [ok,setOk]=useState(FONTS_OK);const [handle]=useState(()=>FONTS_OK?null:delayRender('FontGate: theme fonts before mounting the film',{timeoutInMilliseconds:120000}));useEffect(()=>{if(ok){if(handle!==null)continueRender(handle);return}let live=true;loadThemeFonts().then(()=>{FONTS_OK=true;if(live)setOk(true)}).catch(()=>{/* AssetGate 会 cancelRender 并给出可读的报错 */});return()=>{live=false}},[ok,handle]);return ok};

// CardFitGate：卡片防出格门。逐桶（15 帧）扫描已挂载场景里会裁切的卡片（不透明/渐变底 + 实线边框），
// 内容超出卡片即 cancelRender。z>=200 的字幕层跳过（由 CaptionFitGate 量）。
const CardFitGate=()=>{
  const f=q(useCurrentFrame());
  const bucket=Math.floor(f/15);
  // 测量排在 requestAnimationFrame 里，必须持 delayRender 到首次测量完成，否则 still 渲染先截图、门禁来不及量。
  const [fitHandle]=useState(()=>delayRender('cardfit measure',{timeoutInMilliseconds:60000}));
  const firstDone=useRef(false);
  //   · 字体未就绪时等 document.fonts.ready 后补测，不跳过该桶；
  //   · 用 getBoundingClientRect / scrollHeight 判定（天然包含 transform，不依赖 offsetParent 链）；
  //   · 每 5 秒打一次覆盖率，让「全部合格」与「根本没跑」可区分。
  useEffect(()=>{
    let cancelled=false;
    // 判定作出后 blocked 置位（handle 永不释放）、异常原样抛出：continueRender 一旦被执行，
    // 门禁就会退化成「报而不拦」（与其余门禁同一处置）。
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
        // 逐叶元素比较 rect 会被内联元素的行盒外延误报（单字可出 3px，其实没溢出）。
        // scrollHeight 会把溢出的内容也算进去，和 overflow 属性无关，是最稳的口径。
        document.querySelectorAll<HTMLElement>('div,span').forEach((card)=>{
          if(!solid(card)) return;
          // 只跳"标记者自己"（hasAttribute），**不用 closest**：closest 会连后代一起放过，
          // 于是缩放取景框里所有卡片的真实裁切都会漏检。
          if(card.hasAttribute('data-fit-skip')) return;
          if(!card.textContent||!card.textContent.trim()) return;
          if(card.getBoundingClientRect().width<8) return;
          // 只判会被裁剪的容器：overflow:visible 的容器用 scrollHeight 会把绝对定位子元素
          // 也算进去（如 MetricGrid 会虚增上百像素，其实没有任何文字被裁）
          if(getComputedStyle(card).overflow==='visible') return;
          const cz=parseInt(getComputedStyle(card).zIndex||'0',10);
          // 字幕 200 跳过（它由 CaptionFitGate 量）；章节卡 150 **量测并 warn**（章节标题过长被裁）。
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
          // 竖向容差 10px：不足一行高（≥30px）的差异读作降部/行盒舍入，不是“丢了一行”（真裁切通常 ≥25px）。
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
// 字号 / 字重 / 字距 / 安全宽全部取自 16:9 canvas（MODES['16:9']）与当前主题，
// 并计入主题字幕框的内边距（cel 64px / flat 108px）。
// 判定：> mode.safe 记 fail（真的会被裁切）；> mode.safe - subtitlePadX 只 warn（会顶到内边）。
// 字幕只有一行，≤ CAPTION_MAX_CHARS 字：去掉句末标点与空白后逐字计，ASCII 也按 1 字计（= scripts/story_text.py 的 cap_chars）。
const CAPTION_MAX_CHARS=CONTRACT.CAPTION_MAX_CHARS;
const cleanTail=(s:string)=>s.replace(/[，。！？；：、,.!?;:\s]+$/g,'');
const captionChars=(t:string)=>[...cleanTail(String(t)).replace(/\s+/g,'')].length;
const CaptionFitGate=()=>{const {mode:baseMode}=useCanvas();const mode={...baseMode,subFont:AESTHETIC.subtitleSize??baseMode.subFont};const subFamily=AESTHETIC.subtitleFamily??'Kai';const safe=mode.safe,innerSafe=safe-(AESTHETIC.subtitlePadX??0),weight=AESTHETIC.subtitleWeight??400,ls=AESTHETIC.subtitleLetterSpacing??1.6;const ref=useRef<HTMLDivElement>(null),[done,setDone]=useState(false),[handle]=useState(()=>delayRender('measuring subtitle width',{timeoutInMilliseconds:60000}));useEffect(()=>{let live=true;let blocked=false;Promise.all([document.fonts.load(`${weight} ${mode.subFont}px ${subFamily}`),document.fonts.ready]).then(()=>requestAnimationFrame(()=>{if(!live)return;if(!ref.current){blocked=true;cancelRender(new Error('Subtitle measurement node is unavailable'));return}const longCues=captions.map((c:any,index:number)=>({index,n:captionChars(c.text),text:String(c.text)})).filter(x=>x.n>CAPTION_MAX_CHARS);if(longCues.length){blocked=true;cancelRender(new Error(`Subtitle too long (>${CAPTION_MAX_CHARS} chars per line): ${longCues.map(x=>`#${x.index+1} ${x.n}字 ${x.text}`).join(' | ')}`));return}const rows=[...ref.current.querySelectorAll<HTMLElement>('[data-caption-fit]')];const widths=rows.map((row,index)=>({index,width:row.getBoundingClientRect().width/DESIGN_SCALE,text:row.textContent||''}));const overflow=widths.filter(row=>row.width>safe+.5);const tight=widths.filter(row=>row.width>innerSafe+.5&&row.width<=safe+.5);if(tight.length&&typeof console!=='undefined')console.warn(`[CaptionFitGate] ${tight.length} 条字幕超过内边距安全宽 ${innerSafe}px（未裁切但会顶到字幕框内边）：${tight.map(x=>`#${x.index+1} ${Math.ceil(x.width)}px`).join(' | ')}`);if(overflow.length){blocked=true;cancelRender(new Error(`Subtitle overflow: ${overflow.map(x=>`#${x.index+1} ${Math.ceil(x.width)}px>${safe}px ${x.text}`).join(' | ')}`));return}setDone(true);continueRender(handle)})).catch(error=>{if(live&&!blocked){blocked=true;cancelRender(error)}});return()=>{live=false}},[handle,mode.subFont,subFamily,safe,innerSafe,weight,ls]);if(done)return null;const fitText=(cue:any)=>{const full=cleanTail(String(cue.text));const target=full.replace(/\s+/g,'').length;const ws=Array.isArray(cue.words)?cue.words:[];if(!ws.length)return full;let seq=0;return ws.map((w:any,wi:number)=>{const raw=String(w.part);const sp=wi>0?captionGap(String(ws[wi-1].part),raw):'';const cs=raw.split('').filter((ch:string)=>(!/\s/.test(ch))&&seq++<target).join('');return cs?sp+cs:'';}).join('');};return <div ref={ref} style={{position:'absolute',left:-10000,top:-10000,visibility:'hidden',fontFamily:`${subFamily},Kai,sans-serif`,fontSize:mode.subFont,fontWeight:weight,whiteSpace:'nowrap',letterSpacing:ls,fontFeatureSettings:THEME.craft?'"halt"':undefined}}>{captions.map((cue:any,index:number)=><span key={index} data-caption-fit style={{display:'block',width:'max-content'}}>{fitText(cue)}</span>)}</div>};

// 字体表（含 Clash / Space / Caveat 的 CJK 兜底）已抽到 src/fonts.tsx，成片与接触表共用。

// ---- 可复用组件库 -------------------------------------------

// Paper：卡片容器，皮肤由主题包提供（src/theme/active.ts）。
const Paper=THEME.Paper;

// LineIcon / PillTag / CheckBadge 在 src/kit.tsx；clamp / 缓动 / SPRINGS 在 src/motion.ts。

// 严谨消除句末标点符号（保留句中逗号，句末逗号句号等一概消除）
// 字幕出现方式：'line' = 整行一次出现（5 帧淡入）；'type' = 逐字淡入（卡拉 OK 式，配真人声时用）。
// 缺省：手作皮肤 line（无旁白片的整片节奏就是读速，逐字出现让每张静帧都是半句话），flat / cel 用 type。
// 工程可在 src/film.ts 里 `export const CAPTION_REVEAL = 'line' | 'type'` 覆盖。
const CAPTION_REVEAL:'line'|'type'=((FILM as any).CAPTION_REVEAL??AESTHETIC.captionReveal??(THEME.craft?'line':'type'))==='type'?'type':'line';
const LINE_FADE=5;
const Subtitle=({off=false}:{off?:boolean})=>{
  // 只有出封面帧（`notebook-video poster`）会传 off=true：字幕是烧在画面里的，
  // 而封面当缩略图时带一行半句话的字幕很难看。正片渲染永远走默认值，行为不变。
  if(off)return null;
  const {mode}=useCanvas();
  const f=useRawCurrentFrame(),lead=Math.round(FPS*.18),hold=Math.round(FPS*.05);
  let cue=captions.find((c:any)=>f>=c.startFrame-lead&&f<=c.endFrame+hold);
  if(!cue)cue=[...captions].reverse().find((c:any)=>c.startFrame<=f);
  const full=cue?cleanTail(cue.text):'';
  // 空白不计数（空格交给 captionGap 补成 \u00a0），这样尾标点裁切与词片里的空格无关
  const targetChars=full.replace(/\s+/g,'').length;
  const line=CAPTION_REVEAL==='line';
  const words=cue?cue.words.filter((w:any)=>(line?cue.startFrame:w.startFrame)<=f+lead):[];
  // 一个字都还没出来时不画字幕（否则纸色光晕会先出现一团空白）
  if(!cue||!targetChars||!words.length)return null;
  // type 模式外框跟着第一个字出现，句间不出现空字幕条
  if(!line&&f<(cue.words[0]?.startFrame??cue.startFrame))return null;
  // 占位层与可见层用**同一套**分词加空格规则渲染（含中英文词之间补的 \u00a0），占位宽 = 最终宽，
  // 末字不会顶进字幕框的右侧装饰点。
  const allWords=cue.words;
  const renderWords=(list:any[],animate:boolean)=>{
    let charSeq=0;
    return list.map((w:any,wi:number)=>{
      const raw=String(w.part);
      const spaced=wi>0?captionGap(String(list[wi-1].part),raw):'';
      const chars=raw.split('').filter((ch)=>!/\s/.test(ch));
      return <span key={wi} style={{display:'inline-block'}}>{spaced}{chars.map((ch:any,ci:number)=>{
        const idx=charSeq++;
        if(idx>=targetChars) return null; // 铁律：严格消除任何词尾带出的句末标点符号
        if(!animate) return <span key={ci} style={{display:'inline-block'}}>{ch}</span>;
        const p=interpolate(f,[w.startFrame+ci*.9,w.startFrame+ci*.9+2.5],[0,1],{...clamp,easing:EASE.out});
        return <span key={ci} style={{display:'inline-block',opacity:p,transform:`translateY(${6*(1-p)}px)`}}>{ch}</span>;
      })}</span>;
    });
  };
  const isLast=captions.length>0&&cue===captions[captions.length-1];
  const endFade=isLast&&f>cue.endFrame+12?interpolate(f,[cue.endFrame+12,cue.endFrame+27],[1,0],clamp):1;
  if(endFade<=0.01)return null;
  if(line){
    const p=interpolate(f,[cue.startFrame-lead,cue.startFrame-lead+LINE_FADE],[0,1],clamp)*endFade;
    // 外框也用同一个 p 控制，不先画空盒子
    return <div style={{opacity:p}}><THEME.SubtitleChrome mode={mode}>
      <span data-caption-line style={{position:'relative',display:'inline-block'}}>{renderWords(allWords,false)}</span>
    </THEME.SubtitleChrome></div>;
  }
  return <div style={{opacity:endFade}}><THEME.SubtitleChrome mode={mode}>
    <span style={{position:'relative'}}>
        <span style={{visibility:'hidden'}}>{renderWords(allWords,false)}</span>
        <span style={{position:'absolute',left:0,top:0}}>{renderWords(words,true)}</span>
    </span>
  </THEME.SubtitleChrome></div>;
};

const Chrome=()=>{
  const f=q(useCurrentFrame()),stage=Math.max(0,CHAPTER_STARTS.filter((x)=>f>=x).length-1),local=f-CHAPTER_STARTS[stage],titles=COPY.chapterTitles;
  // 皮肤自带章节标识（手作皮肤）时整块替换，不画章节卡。
  if(THEME.Chrome){const ThemeChrome=THEME.Chrome;return <ThemeChrome stage={stage} title={String(titles[stage]??'')} kicker={COPY.chromeKicker} header={COPY.header} headerSub={COPY.headerSub} local={local}/>;}
  // 章节卡：第 0 章第 0 帧即落定，切章左→右展开 18 帧；收窄为单行紧凑徽标（总常驻遮挡 ≤ 5%）。
  const g=stage===0?1:interpolate(local,[0,18],[0,1],clamp),grow=g<1?{clipPath:revealClip(`calc(${((1-g)*100).toFixed(2)}% - ${(g*REVEAL_BLEED).toFixed(2)}px)`),[GROW_VAR]:g.toFixed(4)}:{};
  return <Paper lift={0.3} style={{left:92,top:64,width:268,height:52,zIndex:150,display:'flex',alignItems:'center',...grow,overflow:'hidden',padding:0}}>
      <div style={{width:52,height:'100%',background:`linear-gradient(135deg,${C.orangeInk},${C.orangeDeep})`,color:C.white,display:'grid',placeItems:'center',fontFamily:'Clash,Space,Kai',fontWeight:600,fontSize:24,boxShadow:'inset -2px 0 6px rgba(0,0,0,0.1)'}}>{String(stage+1).padStart(2,'0')}</div>
      <div style={{padding:'0 14px',flex:1,minWidth:0}}>
        {(() => {
          const title = String(titles[stage] ?? '');
          const availW = 186;
          const {fontSize: measured} = fitChineseTextOnNLines({
            text: title, maxLines: 1, maxBoxWidth: availW,
            fontFamily: 'Kai', fontWeight: 700, maxFontSize: TYPE.labelL, minFontSize: 16,
          });
          const fitSize = Math.max(16, Math.min(TYPE.labelL, Math.floor(measured)));
          return <div style={{fontSize:fitSize,fontWeight:700,color:C.ink,whiteSpace:'nowrap',overflow:'hidden',maxWidth:availW}}>{title}</div>;
        })()}
      </div>
    </Paper>;
};

// 引擎级虚拟摄影机（src/cinema.tsx）：每镜自动慢推/漂移、按分镜表 `cinema.focus` 推近当前拍、
// 宽画布横摇、镜间 whip/zoom 转场、背景视差。分镜表什么都不写也有默认运动。
const shotIndexAt=(f:number)=>{let idx=0;for(let i=0;i<SHOT_IDS.length;i++){ if(f>=SHOTS[SHOT_IDS[i]].from) idx=i; }return idx;};
const camFor=(i:number,local:number)=>{const s:any=(SHOTS as any)[SHOT_IDS[i]];return cinemaCamAt(s.cinema,local,s.duration,i,s.keys);};
const transFor=(i:number)=>{const s:any=(SHOTS as any)[SHOT_IDS[i]];return resolveTransition(s.transition,i,(CHAPTER_STARTS as readonly number[]).includes(s.from));};

// 折痕翻页（卷页探针不通过时的纯 CSS 版）在 transitions/pagefold.tsx。
// 折线几何（FOLD_K / FOLD_DEG / FOLD_SPAN）与 PageFold 组件都在那里；折线方向与 GPU 卷页
// 共用 transitions/meta.ts 的 PAGETURN_FOLD_DIRECTION，预览（CSS）与成片（GPU）永远同向。

const FinalDemo=()=>{
  // 只挂载活动镜头（性能契约）：由分镜表决定当前是哪一镜；转场期间额外挂上一镜的末帧。
  const f=q(useCurrentFrame());
  const idx=shotIndexAt(f);
  const id=SHOT_IDS[idx];
  const s=SHOTS[id];
  const local=f-s.from;
  const prevId=idx>0?SHOT_IDS[idx-1]:null;
  // SCENES 是 Partial（镜数可以少于模板默认 8 镜）：取不到就渲染空镜，而不是把 undefined 当成组件
  const Scene=SCENES[id];
  const PrevScene=prevId?SCENES[prevId]:null;
  const kind=transFor(idx);
  const p=kind&&kind!=='hard'?local/transitionFrames(kind):1;
  const inTrans=p<1&&!!PrevScene;
  const curl=inTrans&&isCurl(kind)?kind:null; // 真卷页（只有渲染器探针通过、开了 fx 才会走到这里）
  const out=inTrans&&kind?transitionStyle(kind,p,'out'):null;
  const inn=inTrans&&kind?transitionStyle(kind,p,'in'):{transform:'none',opacity:1,blur:0};
  const cam=camFor(idx,local);
  // 世界层容器不动（遮罩挂在它上面，坐标=屏幕设计坐标），内层承载摄影机变换。
  const world=(c:any,child:React.ReactNode)=>{const m=cinemaMask(c.fw??0);return <div data-cinema-world {...(m?{'data-cinema-focus':String(CINEMA.maskCut)}:{})} style={{position:'absolute',inset:0,...(m?{WebkitMaskImage:m,maskImage:m}:{})}}><div style={{position:'absolute',inset:0,transformOrigin:'0 0',transform:cinemaTransform(c)}}>{child}</div></div>;};
  return <>
    {out&&<WhipBlur id="nv-whip-out" amount={out.blur}/>}
    {inTrans&&<WhipBlur id="nv-whip-in" amount={inn.blur}/>}
    {curl&&PrevScene&&prevId&&(
      // 卷走的是上一镜的「整页」：背景（按上一镜末帧的视差位置）+ 内容。新一页（Backdrop + 本镜）在下面不动。
      <div data-gate-allow="handoff" data-curl={curl} style={{position:'absolute',inset:0,zIndex:130}}>
        <PageCurl kind={curl} p={p} paper={THEME.palette.paperBase} density={MODES['16:9'].scale*(typeof window!=='undefined'?window.devicePixelRatio||1:1)}>
          <AbsoluteFill style={{transform:parallaxTransform(camFor(idx-1,SHOTS[prevId].duration-1)),transformOrigin:'960px 540px'}}><ShotBackground id={prevId}/></AbsoluteFill>
          {world(camFor(idx-1,SHOTS[prevId].duration-1),PrevScene?<PrevScene f={SHOTS[prevId].duration-1}/>:null)}
        </PageCurl>
      </div>
    )}
    {curl&&(()=>{const sh=curlShadow(curl,p);return sh?<div aria-hidden style={{position:'absolute',inset:0,zIndex:129,pointerEvents:'none',...sh}}/>:null;})()}
    {!curl&&PrevScene&&prevId&&out&&out.opacity>0.01&&(kind==='pageflip'?(
      // 真翻页：折痕扫过纸面。几何全在 PageFold 里，这里只喂「上一镜那一整页」。
      <div data-gate-allow="handoff" style={{position:'absolute',inset:0,zIndex:130}}>
        <PageFold p={p} paper={THEME.palette.paperBase} backPage={<AbsoluteFill><ShotBackground id={prevId}/></AbsoluteFill>}>
          <AbsoluteFill><ShotBackground id={prevId}/></AbsoluteFill>
          {world(camFor(idx-1,SHOTS[prevId].duration-1),PrevScene?<PrevScene f={SHOTS[prevId].duration-1}/>:null)}
        </PageFold>
      </div>
    ):(
      <div data-gate-allow="handoff" style={{position:'absolute',inset:0,zIndex:130,opacity:out.opacity,transform:out.transform,transformOrigin:out.origin??'960px 540px',background:out.bg,boxShadow:out.shadow,filter:out.blur>0.3?'url(#nv-whip-out)':undefined}}>
        {/* 翻起来的那一页要带着它自己的纸——只带内容的话，看起来像一张白卡在飞，
            而不是「这一页纸」。背景一起带上，翻过去的才是同一张手账。 */}
        {out.bg&&<AbsoluteFill><ShotBackground id={prevId}/></AbsoluteFill>}
        {world(camFor(idx-1,SHOTS[prevId].duration-1),PrevScene?<PrevScene f={SHOTS[prevId].duration-1}/>:null)}
      </div>
    ))}
    {f<s.to&&<div {...(inTrans?{'data-gate-allow':'handoff'}:{})} style={{position:'absolute',inset:0,opacity:inn.opacity,transform:inn.transform,transformOrigin:'960px 540px',filter:inn.blur>0.3?'url(#nv-whip-in)':undefined}}>
      {world(cam,Scene?<Scene f={local}/>:null)}
    </div>}
  </>;
};


// 背景：每镜一张，由分镜表推导，镜头交接时与上一镜的背景交叉淡化 tfDur 帧。
//   · 背景库：resolve-shots 已给每镜定好 `bgFile`（manifests/backgrounds.json 里的一张，显式 `bg` 或按角色自动轮换、
//     相邻不重复）→ 直接画这张图；
//   · 否则（没有 bgFile / `bgRotate:false`）：分镜表写了 `bg: 'main' | 'chapter' | 'quiet'` → 照写的用；
//     不写：章节首镜 → chapter；信息密集（zones ≥ 4）→ quiet；其余 → main。
// 所有背景的中央约 70% 都是安静的安全区，所以镜头内容直接压在背景上，不再铺整幅半透明底托。
// 背景按 CINEMA.parallax 跟随摄影机（视差），转场时随甩镜一起移动。
const bgVariantFor=(id:string):BgVariant=>{
  const s:any=(SHOTS as any)[id];
  if(s?.bg==='main'||s?.bg==='chapter'||s?.bg==='quiet') return s.bg;
  if((CHAPTER_STARTS as readonly number[]).includes(s.from)) return 'chapter';
  if((s.zones??0)>=4) return 'quiet';
  return 'main';
};
const bgFileFor=(id:string):string|null=>{const s:any=(SHOTS as any)[id];return typeof s?.bgFile==='string'?s.bgFile:null;};
const bgKeyFor=(id:string)=>bgFileFor(id)??`variant:${bgVariantFor(id)}`;
const ShotBackground:React.FC<{id:string}>=({id})=>{
  const file=bgFileFor(id);
  if(!file) return <Background variant={bgVariantFor(id)}/>;
  return <AbsoluteFill style={{background:THEME.palette.paperBase}}>
    <Img src={staticFile(file)} style={{width:'100%',height:'100%',objectFit:'cover'}}/>
  </AbsoluteFill>;
};
const Backdrop=()=>{
  const f=q(useCurrentFrame());
  const idx=shotIndexAt(f);
  const local=f-SHOTS[SHOT_IDS[idx]].from;
  const curId=SHOT_IDS[idx];
  const prevId=idx>0?SHOT_IDS[idx-1]:curId;
  const kind=transFor(idx);
  // 翻页（GPU 卷页与 CSS 折页都一样）时旧背景跟着那一页一起走，这里只画新背景。
  // 折页漏判的话，新页上还会叠着旧纸 14 帧——两张纸的纹理叠在一起，像印刷套色没对准。
  const carried=isCurl(kind)||kind==='pageflip';
  const tfDur=transitionFrames(kind);
  const p=!carried&&bgKeyFor(prevId)!==bgKeyFor(curId)?Math.max(0,1-local/tfDur):0;
  const tf=parallaxTransform(camFor(idx,local),whipOffset(kind,local/tfDur));
  return <AbsoluteFill style={{transform:tf,transformOrigin:'960px 540px'}}>
    <ShotBackground id={curId}/>
    {p>0.01&&<AbsoluteFill style={{opacity:p}}><ShotBackground id={prevId}/></AbsoluteFill>}
  </AbsoluteFill>;
};

// 音效：预制语义音效库 + 按分镜表语义自动排（src/sfx.ts 的 planSfx）。
// 一律相对所属镜头起点推导，改台词重跑 resolve-shots 后自动跟着走；每镜可用 `sfx` 字段覆盖。
// 混音：音效库统一 -18 LUFS(100ms)，SFX_GAIN 把它们压到人声（-16 LUFS）下方 8–12 LU；音乐床 ≈ -36 LUFS。
const SFX_PLAN=planSfx(SHOT_IDS.map((id)=>SHOTS[id] as any),CHAPTER_STARTS,DURATION,SFX_DENSITY);
const Sound=()=>{
  const captionRanges=captions.map((c:any)=>({startFrame:c.startFrame as number,endFrame:c.endFrame as number}));
  // 音乐床在每个音效下闪避（bedDuckAt），音量是帧的纯函数
  const bedVol=(fr:number)=>interpolate(fr,[0,30,DURATION-45,DURATION],[0,BED_GAIN,BED_GAIN,0],{...clamp,easing:Easing.linear})*bedDuckAt(fr,SFX_PLAN);
  return <>
    <Audio src={staticFile('narration.mp3')} volume={1}/>
    {/* 默认无 BGM。MUSIC_ON 由 sync-render-inputs.cjs 从 treatment.sound.music.use 生成；
        没有 treatment / use=false / 组件路线 → false，音乐床不加载。 */}
    {MUSIC_ON && <Audio src={staticFile(SFX_BED)} volume={(fr:number)=>bedVol(fr)} loop/>}
    {SFX_PLAN.map((x,i)=>{const v=x.vol*voiceDuckFactor(x.hit,x.event,captionRanges);return <Sequence key={`${x.event}-${i}`} from={deliveryFrame(x.at)} layout="none"><Audio src={staticFile(x.src)} volume={x.trim?(fr:number)=>v*Math.min(1,(fr+1)/2):v} trimBefore={x.trim||undefined}/></Sequence>;})}
  </>;
};


// 门禁事件帧：最密集的重叠发生在短窗口里（镜头交接 10 帧、页眉滑变 7–16 帧、数值滑动 14 帧），
// 只按 15 帧网格抽样会漏掉，所以把镜头边界、节拍、相机关键帧交给门禁强制抽样。
// 每镜的落定帧（镜尾 − 12，抽帧留档看的就是它）一般不在网格上，也显式加进 WATCH。
const WATCH=(()=>{const out:number[]=[];SHOT_IDS.forEach((id:string)=>{const s:any=(SHOTS as any)[id];out.push(s.from-1,s.from,s.from+1,s.to-1,s.to);out.push(s.to-12);(s.beats||[]).forEach((b:number)=>out.push(s.from+b));(s.keys||[]).forEach((k:any)=>out.push(s.from+k.f));});return out;})();
const FilmLayout:React.FC<{hideCaptions?:boolean}>=({hideCaptions})=>{
  const mode=MODES['16:9'];
  const fontsOk=useFontGate();
  return <CanvasContext.Provider value={{canvas:'16:9',mode}}>
    <AbsoluteFill style={{overflow:'hidden',background:C.paperBase}}>
      {/* data-design-root：FillGate 靠它把「输出像素」折回「设计像素」（比例从设计根量，不假设 --scale）。
    缺了它 FillGate 会静默 return —— 门禁装了等于没装，所以这个属性是门禁契约的一部分。 */}
      <div data-design-root style={{position:'absolute',left:0,top:0,width:mode.designW,height:mode.designH,transform:`scale(${mode.scale})`,transformOrigin:'0 0',fontFamily:'Kai,sans-serif',color:C.ink,overflow:'hidden'}}>
        <FontFaces bg={C.paperBase}/><AssetGate/><Sound/>{fontsOk&&<><CaptionFitGate/><CardFitGate/><OverlapGate mode="block" watch={WATCH}/><ClippingGate mode="block" watch={WATCH}/>
        {/* CanvasBoundsGate：只判「含文字的叶元素的墨迹 rect 越出画布」。片子用 warn（接触表用 block）：
            硬拦发生在交付渲染的最后一刻，误报代价是整片不出；出声进渲染日志，交付前人工确认。
            口径见 references/checks.md#render-gates。 */}
        <CanvasBoundsGate mode="warn"/>
        {/* FillGate 默认 warn：下 1/4 是"观感线"，为它打断整片渲染不划算；出声进日志、可复查 */}
        <FillGate mode="warn" watch={WATCH}/><MascotGate watch={WATCH}/><GlyphSnap/><Backdrop/>
        {<><Chrome/><FinalDemo/></>}
        <Grade/>
        <Subtitle off={hideCaptions}/></>}
      </div>
    </AbsoluteFill>
  </CanvasContext.Provider>;
};

// 只有 16:9 一种交付画布（2560×1440，设计坐标 1920×1080）。
const Film16x9=({hideCaptions}:{hideCaptions?:boolean}={})=> <FilmLayout hideCaptions={hideCaptions}/>;

// fx 探针（`notebook-video.mjs` 渲一帧读像素，决定这台机器能不能开真卷页）。320×180，不进成片。
const FxProbeComposition=()=> <FxProbe/>;

const Root=()=> <>
  {/* 官方模板示例片（8 镜 / 4 骨架），按 1920×1080 设计空间编写，交付 2560×1440（见 references/scenes.md#canvas-modes）。 */}
  <Composition id="NotebookVideoFilm" component={Film16x9} durationInFrames={DURATION} fps={FPS} width={2560} height={1440}/>
  {/* 真卷页能力探针（`notebook-video.mjs fx-probe`）：WebGL2 + HTML-in-canvas 画得出来才给成片开 pageturn / peel */}
  <Composition id="NotebookVideoFxProbe" component={FxProbeComposition} durationInFrames={1} fps={FPS} width={320} height={180}/>
</>;

registerRoot(Root);
