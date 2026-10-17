import React from 'react';
import {staticFile} from 'remotion';

// ============================================================================
// 字体表（LOCKED）：全部字体都随工程打包在 public/ 下，渲染**从不**依赖系统字体
// （Windows / macOS / Linux / CI 容器出图一致）。
//
// CJK 兜底（v4.1）：Clash / Space / Caveat 是只含拉丁字形的展示字体。旧版页眉
// `fontFamily:'Clash,Space'` 遇到中文时落到系统字体，在没有中文字体的环境里渲成豆腐块。
// 现在给这三个族各追加一条 **unicode-range 限定的 @font-face**，指向随包的 LXGW WenKai Lite
// （OFL-1.1，public/LICENSE-OFL-1.1-LXGW.txt）：浏览器按字符挑字面，拉丁字符仍用原字体，
// 中日韩字符与全角标点自动落到 WenKai。于是任何 `fontFamily:'Space'` / `'Clash,Space'`
// 的写法都不会再出豆腐，调用处不用记得补 Kai。
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
${cjkFallbackFaces('Clash', ['500', '600', '700'])}
${cjkFallbackFaces('Space', ['400', '500', '600', '700'])}
${cjkFallbackFaces('Caveat', ['400 700'])}
*{box-sizing:border-box}html,body{margin:0;background:${bg}}body{font-family:Kai,'Segoe UI',sans-serif;-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}
`}</style>;
