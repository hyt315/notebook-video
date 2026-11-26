import React,{useEffect,useState} from 'react';
import {cancelRender,continueRender,delayRender,staticFile} from 'remotion';
import {THEME} from './theme/active';

// ============================================================================
// 字体表（LOCKED）：全部字体都随工程打包在 public/ 下，渲染**从不**依赖系统字体
// （Windows / macOS / Linux / CI 容器出图一致）。
//
// CJK 兜底：Clash / Space / Caveat 是只含拉丁字形的展示字体，
// `fontFamily:'Clash,Space'` 遇到中文时会落到系统字体，在没有中文字体的环境里渲成豆腐块。
// 所以给这三个族各追加一条 **unicode-range 限定的 @font-face**，指向随包的 LXGW WenKai Lite
// （OFL-1.1，public/LICENSE-OFL-1.1-LXGW.txt）：浏览器按字符挑字面，拉丁字符仍用原字体，
// 中日韩字符与全角标点自动落到 WenKai。于是任何 `fontFamily:'Space'` / `'Clash,Space'`
// 的写法都不会再出豆腐，调用处不用记得补 Kai。
// NotoSerifSC = Noto Serif SC Bold（OFL-1.1，notofonts/noto-cjk Serif2.003，按需下载，不入库）。
// 只有手作皮肤（journal / papercut / archive）用它，皮肤在 THEME.craft.fonts 里声明，AssetGate 校验；
// flat / cel 工程里这个 @font-face 指向的文件不存在也没关系（浏览器只在用到时才下载字体）。
// Clash Display（ITF Free Font License，禁止经仓库再分发）不随仓库发，CLI 首次用到时从 Fontshare
// 按 sha256 锁定下载到工程 public/fonts/；离线缺文件时调用处的 'Clash,Space,Kai' 栈回落到 Space Grotesk。
// ============================================================================

/** 中日韩统一表意文字 + 扩展 A + 兼容表意 + CJK 标点 + 全角形式 + 假名 + 注音 + 中文常用符号。 */
export const CJK_UNICODE_RANGE =
  'U+2E80-2FDF, U+3000-303F, U+3040-30FF, U+3100-312F, U+31A0-31FF, U+3200-33FF, U+3400-4DBF, U+4E00-9FFF, U+F900-FAFF, U+FE30-FE4F, U+FF00-FFEF';

const kaiRegular = () => staticFile('LXGWWenKaiLite-Regular.ttf');
const kaiMedium = () => staticFile('LXGWWenKaiLite-Medium.ttf');

/**
 * 给一个拉丁展示字体族补上 WenKai 的 CJK 字面。weights 必须与该族原有 @font-face 的
 * font-weight 描述符**逐字相同**：Chrome 先按描述符分组挑字重，再在组内按 unicode-range 拼字，
 * 描述符不同的兜底字面会被分到别的组、根本不参与拼字。400 及以下用 Regular，其余用 Medium。
 */
const cjkFallbackFaces = (family: string, weights: string[]) => weights.map((w) =>
  `@font-face{font-family:${family};src:url(${parseInt(w, 10) <= 400 ? kaiRegular() : kaiMedium()}) format('truetype');font-weight:${w};unicode-range:${CJK_UNICODE_RANGE}}`).join('\n');

/** 所有 composition（成片与接触表）都挂这一个组件；bg = html/body 底色。 */
export const FontFaces: React.FC<{bg: string}> = ({bg}) => <style>{`
@font-face{font-family:Kai;src:url(${kaiRegular()}) format('truetype');font-weight:400}
@font-face{font-family:Kai;src:url(${kaiMedium()}) format('truetype');font-weight:700}
@font-face{font-family:Clash;src:url(${staticFile('fonts/ClashDisplay-Medium.woff2')}) format('woff2');font-weight:500}
@font-face{font-family:Clash;src:url(${staticFile('fonts/ClashDisplay-Semibold.woff2')}) format('woff2');font-weight:600}
@font-face{font-family:Clash;src:url(${staticFile('fonts/ClashDisplay-Bold.woff2')}) format('woff2');font-weight:700}
@font-face{font-family:Space;src:url(${staticFile('fonts/SpaceGrotesk-Latin.woff2')}) format('woff2');font-weight:400}
@font-face{font-family:Space;src:url(${staticFile('fonts/SpaceGrotesk-Latin.woff2')}) format('woff2');font-weight:500}
@font-face{font-family:Space;src:url(${staticFile('fonts/SpaceGrotesk-Latin.woff2')}) format('woff2');font-weight:600}
@font-face{font-family:Space;src:url(${staticFile('fonts/SpaceGrotesk-Latin.woff2')}) format('woff2');font-weight:700}
@font-face{font-family:Caveat;src:url(${staticFile('fonts/Caveat-Latin.woff2')}) format('woff2');font-weight:400 700}
@font-face{font-family:NotoSerifSC;src:url(${staticFile('NotoSerifSC-Bold.otf')}) format('opentype');font-weight:400 900}
${cjkFallbackFaces('Clash', ['500', '600', '700'])}
${cjkFallbackFaces('Space', ['400', '500', '600', '700'])}
${cjkFallbackFaces('Caveat', ['400 700'])}
*{box-sizing:border-box}html,body{margin:0;background:${bg}}body{font-family:Kai,'Segoe UI',sans-serif;-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}
`}</style>;

// 主题字体一次性加载（AssetGate 与 FontGate 共用同一份清单）。
// 含 700 Clash：数字镜（KineticNumber）用它，不预载时单帧 still 量字框的那一刻它还没加载，GlyphSnap 的展开边
// 会与连续渲不同。只加这一个字重：预载 Space 700 会改变章节标题的排版。
// ⚠️ 先等一帧并强制一次样式计算再 load：FontFaces 的 <style> 刚插入时 @font-face 还没注册进
// document.fonts，此刻 load() 匹配不到任何字体、立即 resolve。FontGate 不先挂画面层，必须自己触发加载。
export const loadThemeFonts=()=>new Promise<void>((r)=>requestAnimationFrame(()=>r())).then(()=>{void document.body.offsetHeight;}).then(()=>Promise.all([document.fonts.load('400 40px Kai'),document.fonts.load('700 40px Kai'),document.fonts.load('600 40px Clash').catch(()=>[]),document.fonts.load('700 40px Clash').catch(()=>[]),document.fonts.load('500 40px Space'),document.fonts.load('400 40px Caveat'),...(THEME.craft?.fonts??[]).map(fd=>document.fonts.load(fd)),document.fonts.ready]));
export const AssetGate=()=>{const [handle]=useState(()=>delayRender('waiting for fonts',{timeoutInMilliseconds:120000}));useEffect(()=>{let live=true;loadThemeFonts().then(()=>{if(!live)return;const missing=(THEME.craft?.fonts??[]).filter(fd=>!document.fonts.check(fd,'细胞'));if(missing.length){cancelRender(new Error(`Theme font missing: ${missing.join(', ')} — run: node scripts/notebook-video.mjs fonts --serif, then new-project/sync again (Noto Serif SC, OFL)`));return}continueRender(handle)}).catch(error=>{if(live)cancelRender(error)});return()=>{live=false}},[handle]);return null};
