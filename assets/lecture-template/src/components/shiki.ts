// ============================================================================
// shiki.ts — 代码高亮引擎（Shiki，MIT）
//
// 为什么是**同步核心 + JS 正则引擎**：
//   · `createHighlighterCoreSync` + `createJavaScriptRegexEngine` 不加载 WASM、不发请求、
//     不走 Promise —— 第一次渲染就拿得到 token，不需要 delayRender，也不会因为
//     Windows 上 webpack 解析 .wasm 的路径问题而失败。
//   · 语言按需 import（8 个 grammar），不把 200+ 种语言打进包。
//   · 主题不是 Shiki 自带的：每个主题（flat / cel）的调色板在这里被翻译成一张
//     TextMate 主题（scope → THEME token），所以换主题 = 换颜色，语法色永远跟皮肤一致。
//
// 纪律：本文件只做「代码 → 着色 token」的纯计算，结果按 (语言, 代码) 缓存，
// 同一帧渲两次得到同一组 token（确定性）。
// ============================================================================
import {createHighlighterCoreSync} from 'shiki/core';
import type {HighlighterCore, ThemeRegistrationRaw} from 'shiki/core';
import {createJavaScriptRegexEngine} from 'shiki/engine/javascript';
import langTsx from '@shikijs/langs/tsx';
import langTypescript from '@shikijs/langs/typescript';
import langJsx from '@shikijs/langs/jsx';
import langJavascript from '@shikijs/langs/javascript';
import langPython from '@shikijs/langs/python';
import langShell from '@shikijs/langs/shellscript';
import langJson from '@shikijs/langs/json';
import langDiff from '@shikijs/langs/diff';
import {THEME} from '../theme/active';

const C = THEME.palette;
export const SHIKI_THEME_NAME = `notebook-video-${THEME.id}`;

/** 调色板 → TextMate 主题。文字色一律用 *Ink（文字安全色），填充色（orange/orangeDeep 等）不当字色。 */
const nvTheme: ThemeRegistrationRaw = {
  name: SHIKI_THEME_NAME,
  type: 'light',
  colors: {'editor.foreground': C.ink, 'editor.background': C.paper},
  settings: [
    {settings: {foreground: C.ink, background: C.paper}},
    {scope: ['comment', 'punctuation.definition.comment'], settings: {foreground: C.muted, fontStyle: 'italic'}},
    {scope: ['punctuation', 'meta.brace', 'keyword.operator', 'keyword.operator.assignment'], settings: {foreground: C.muted}},
    {
      scope: ['keyword', 'storage', 'storage.type', 'storage.modifier', 'keyword.control', 'variable.language', 'constant.language.import-export-all'],
      settings: {foreground: C.blueInk, fontStyle: 'bold'},
    },
    {scope: ['entity.name.type', 'entity.name.class', 'support.class', 'entity.other.inherited-class'], settings: {foreground: C.orangeInk, fontStyle: 'bold'}},
    {scope: ['entity.name.function', 'support.function', 'meta.function-call entity.name.function'], settings: {foreground: C.orangeInk}},
    {scope: ['string', 'string.quoted', 'string.template', 'punctuation.definition.string'], settings: {foreground: C.greenInk}},
    {scope: ['constant.numeric', 'constant.language', 'constant.language.boolean'], settings: {foreground: C.orangeInk}},
    {scope: ['support.type', 'support.type.builtin', 'support.variable', 'entity.name.type.primitive'], settings: {foreground: C.blueInk}},
    {scope: ['entity.other.attribute-name', 'support.type.property-name', 'meta.object-literal.key'], settings: {foreground: C.goldInk}},
    {scope: ['entity.name.tag', 'support.class.component'], settings: {foreground: C.blueInk}},
    {scope: ['markup.inserted', 'punctuation.definition.inserted'], settings: {foreground: C.greenInk}},
    {scope: ['markup.deleted', 'punctuation.definition.deleted'], settings: {foreground: C.redInk}},
    {scope: ['meta.diff.range', 'meta.diff.header', 'markup.changed'], settings: {foreground: C.blueInk, fontStyle: 'bold'}},
    {scope: ['variable.parameter'], settings: {foreground: C.ink, fontStyle: 'italic'}},
  ],
};

/** 场景里可写的语言名（含别名）→ Shiki 语言 id。不在表里的一律按纯文本渲染（不报错、不掉色）。 */
export const SHIKI_LANG_ALIASES: Record<string, string> = {
  tsx: 'tsx',
  typescript: 'typescript',
  ts: 'typescript',
  jsx: 'jsx',
  javascript: 'javascript',
  js: 'javascript',
  python: 'python',
  py: 'python',
  bash: 'shellscript',
  sh: 'shellscript',
  shell: 'shellscript',
  shellscript: 'shellscript',
  json: 'json',
  diff: 'diff',
  text: 'text',
  plaintext: 'text',
};

let highlighter: HighlighterCore | null = null;
const getHighlighter = () => {
  if (!highlighter) {
    highlighter = createHighlighterCoreSync({
      themes: [nvTheme],
      langs: [langTsx, langTypescript, langJsx, langJavascript, langPython, langShell, langJson, langDiff],
      engine: createJavaScriptRegexEngine(),
    });
  }
  return highlighter;
};

export type CodeToken = {content: string; color: string; bold: boolean; italic: boolean};

const cache = new Map<string, CodeToken[][]>();

/** 代码 → 每行一组着色 token。纯函数 + 缓存。 */
export const highlightTokens = (code: string, language: string): CodeToken[][] => {
  const lang = SHIKI_LANG_ALIASES[language.toLowerCase()] ?? 'text';
  const key = `${lang}\u0000${code}`;
  const hit = cache.get(key);
  if (hit) return hit;
  let lines: CodeToken[][];
  if (lang === 'text') {
    lines = code.split('\n').map((l) => [{content: l, color: C.ink, bold: false, italic: false}]);
  } else {
    const {tokens} = getHighlighter().codeToTokens(code, {lang, theme: SHIKI_THEME_NAME});
    lines = tokens.map((line) =>
      line.map((t) => ({
        content: t.content,
        color: t.color ?? C.ink,
        // Shiki FontStyle 位标志：1 = italic，2 = bold
        italic: ((t.fontStyle ?? 0) & 1) === 1,
        bold: ((t.fontStyle ?? 0) & 2) === 2,
      }))
    );
  }
  cache.set(key, lines);
  return lines;
};
