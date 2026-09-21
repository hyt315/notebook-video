import React from 'react';
import {measureText} from '@remotion/layout-utils';
import {loadDefaultSimplifiedChineseParser} from 'budoux';
import LineBreaker from 'linebreak';
import {continueRender, delayRender, staticFile} from 'remotion';
import {THEME} from '../theme/active';
import {TYPE} from '../kit';

// ============================================================================
// fittext.tsx — 中文文字测量与「反推字号」
//
// 解决什么问题：技能的 fitH() 能按「行数 × 行高」估出容器高度，但估不出
// 「这段话在这个字号下会不会换行」。卡片文字被裁的根因就在这——估的高度
// 比真实排版矮。本层反过来做：给容器宽度和行数上限，反推字号并返回断好的行。
//
// ⚠️ 为什么不用 @remotion/layout-utils 的 fitTextOnNLines：
//    它的实现是 `text.split(' ')` —— 按**空格**切词。中文没有空格，整段会被
//    当成一个不可断的「词」，于是只能塞进一行，字号被压到 maxBoxWidth/字数
//    （实测：44 字、738px 容器 → 16.77px/1 行，而正确答案是 46px/3 行）。
//    它对空格分词的语言是对的，对中文是失效的，而且**不会报错，只会静默给出
//    一个很小的字号**。所以本层只用它的 measureText（实测准确、严格线性，
//    已验证 46px 时 44 字 = 2024px、比值 2.300），断行与二分自己做。
// ============================================================================

const C = THEME.palette;

/** 等待主题字体就绪；未就绪时挂起渲染（delayRender），就绪后继续。 */
export const useFontsReady = (families: string[] = ['Kai'], sizes = [400, 700]) => {
  const [ready, setReady] = React.useState(false);
  const [handle] = React.useState(() => delayRender('waiting for theme fonts before measuring text'));
  React.useEffect(() => {
    let live = true;
    const jobs: Promise<unknown>[] = [document.fonts.ready as unknown as Promise<unknown>];
    for (const family of families) for (const weight of sizes) jobs.push(document.fonts.load(`${weight} 46px ${family}`) as unknown as Promise<unknown>);
    Promise.all(jobs)
      .then(() => live && setReady(true))
      .catch(() => live && setReady(true));
    return () => {
      live = false;
    };
  }, []);
  React.useEffect(() => {
    if (ready) continueRender(handle);
  }, [ready, handle]);
  return ready;
};

// ---- 词组边界（budoux）：让断行尽量落在词与词之间，而不是任意字之间 ----
// 中文正文本来就能任意字断行，但**标题**断在词中间会很难看。
// budoux 给出词组切分点，断行时优先在这些位置断。
let zhParser: ReturnType<typeof loadDefaultSimplifiedChineseParser> | null = null;
const wordBreaks = (chars: string[]): Set<number> => {
  try {
    if (!zhParser) zhParser = loadDefaultSimplifiedChineseParser();
    const segs = zhParser.parse(chars.join(''));
    const breaks = new Set<number>();
    let acc = 0;
    for (const seg of segs) {
      acc += [...seg].length;
      breaks.add(acc);
    }
    return breaks;
  } catch {
    return new Set<number>();
  }
};

// ---- 断行机会：改用 **UAX #14 真实算法**（`linebreak`，MIT，纯离线表）----
//
// 2026-09-21 换掉手写的两张字符表：那两张表是 UAX #14 的粗糙近似，实测在**中英混排**上会切错——
// 对 '在GitHub，全世界的开发者，' 我们的表允许 5 个非法断点（在G|itH、Git|Hub…），
// 对 '主页搜hyt315，…' 允许 5 个（hyt|315…），对 'notebook-video' 允许 13 个；
// 而 UAX #14 在这些位置**一律不许断**（拉丁/数字串内部不断）。纯中文时两者完全一致
// （实测 '第一步，参与别人的项目，' 与 '给容器宽度和行数上限，反推该用多大字号' 断点逐一相同），
// 所以这次换掉的正是"我们写得更差"的那部分。
// 确定性：算法 + 随包发布的 Unicode 表，纯函数，无 timer / 无 Math.random，版本由 lock 锁死。
const legalBreakCache = new Map<string, Set<number>>();
/** 该文本所有**合法**断行位置（断在 i 之前 = 第 i 个字符可以另起一行）。 */
const legalBreaks = (text: string): Set<number> => {
  const hit = legalBreakCache.get(text);
  if (hit) return hit;
  const out = new Set<number>();
  try {
    const lb = new LineBreaker(text);
    let bk: {position: number} | null;
    while ((bk = lb.nextBreak())) out.add(bk.position);
  } catch {
    /* 表缺失时退回"处处可断"（等同于旧行为），不让文字排版把渲染搞崩 */
    [...text].forEach((_, i) => i > 0 && out.add(i));
  }
  legalBreakCache.set(text, out);
  return out;
};

const REF_SIZE = 100; // 参考字号：宽度在此尺寸下量一次，再按比例缩放（实测严格线性）

const widthCache = new Map<string, number[]>();
/** 逐字宽度（在参考字号下量一次）；CJK 字体度量对字号严格线性，缩放安全。 */
const charWidths = (text: string, fontFamily: string, fontWeight: number): number[] => {
  const key = `${fontFamily}|${fontWeight}|${text}`;
  const hit = widthCache.get(key);
  if (hit) return hit;
  const chars = [...text];
  const widths: number[] = [];
  for (const ch of chars) {
    widths.push(ch === '\n' ? 0 : measureText({text: ch, fontFamily, fontSize: REF_SIZE, fontWeight}).width);
  }
  widthCache.set(key, widths);
  return widths;
};

/** 给定字号做贪心断行：能断在词组边界就断在词组边界，否则按字断（仍遵守避头尾）。纯算术，不调 DOM。 */
const layout = (text: string, widths: number[], fontSize: number, maxBoxWidth: number): string[] => {
  const scale = fontSize / REF_SIZE;
  const chars = [...text];
  const breaks = wordBreaks(chars);
  // 合法断点（UAX #14）：**优先**在这些位置断；一个都没有时才允许"应急断行"
  const legal = legalBreaks(text);
  const lines: string[] = [];
  let cur = '';
  let curW = 0;
  /** 当前行最后一个「可以断」的位置（词组边界）——优先退到这里断 */
  let lastWordEnd = -1;
  /** 上面对应的**绝对**字符位置（用于问 UAX #14：这里真的允许断吗） */
  let breakPos = -1;
  let widthAtWordEnd = 0;

  for (let i = 0; i < chars.length; i++) {
    const ch = chars[i];
    if (ch === '\n') {
      lines.push(cur);
      cur = '';
      curW = 0;
      continue;
    }
    const w = widths[i] * scale;
    if (cur !== '' && curW + w > maxBoxWidth) {
      // 避头尾：标点不该行首。但**只有在放得下时才拽到上一行**——
      // 否则行宽会超出容器，浏览器会再折一次，行数直接翻倍（实测过 3 行变 6 行）。
      // 宁可偶尔标点行首，也不能让行宽超容器。
      // 这里本来该断，但 UAX #14 说"不许在这个字符前断"（标点避头、拉丁串内部…）：
      // 只有在放得下时才把它留在本行；放不下就走下面的应急断行——
      // **宁可偶尔断在非法位置，也绝不让行宽超容器**（超了浏览器会二次折行，行数直接翻倍）。
      if (!legal.has(i) && curW + w <= maxBoxWidth) {
        cur += ch;
        curW += w;
        continue;
      }
      // 词组优先：溢出时**退到本行最后一个词组边界**断行，把整个词推到下一行。
      // 这是"不劈词"的正确规则——宁可这一行短一点，也不把词切成两半。
      // 没有可用边界时才按字断（此时仍遵守避头尾）。
      if (lastWordEnd > 0 && lastWordEnd < cur.length && legal.has(breakPos)) {
        const keep = cur.slice(lastWordEnd);
        const keepW = curW - widthAtWordEnd;
        lines.push(cur.slice(0, lastWordEnd));
        cur = keep + ch;
        curW = keepW + w;
        lastWordEnd = -1;
        widthAtWordEnd = 0;
        continue;
      }
      lines.push(cur);
      cur = ch;
      curW = w;
      lastWordEnd = -1;
      widthAtWordEnd = 0;
    } else {
      cur += ch;
      curW += w;
      if (breaks.has(i + 1)) {
        lastWordEnd = cur.length;
        breakPos = i + 1; // 绝对位置（相对 cur 的位置在断行时会变，必须存绝对量）
        widthAtWordEnd = curW;
      }
    }
  }
  if (cur !== '') lines.push(cur);
  return lines;
};

/**
 * fitChineseTextOnNLines — 中文（含中英混排）的「反推字号 + 断行」。
 *
 * 返回能塞进 maxLines 行、且每行不超过 maxBoxWidth 的**最大**字号与断好的行。
 * 纯计算（measureText + 二分 + 算术断行），可复现、无副作用。
 */
export const fitChineseTextOnNLines = (opts: {
  text: string;
  maxLines: number;
  maxBoxWidth: number;
  fontFamily?: string;
  fontWeight?: number;
  maxFontSize?: number;
  minFontSize?: number;
}): {fontSize: number; lines: string[]} => {
  const {text, maxLines, maxBoxWidth, fontFamily = 'Kai', fontWeight = 400, maxFontSize = 120, minFontSize = 4} = opts;
  if (!text) return {fontSize: maxFontSize, lines: []};

  const widths = charWidths(text, fontFamily, fontWeight);
  const fits = (size: number) => layout(text, widths, size, maxBoxWidth).length <= maxLines;

  // 二分：找满足行数上限的最大字号
  let lo = minFontSize;
  let hi = maxFontSize;
  if (fits(hi)) {
    lo = hi;
  } else {
    for (let i = 0; i < 22 && hi - lo > 0.05; i++) {
      const mid = (lo + hi) / 2;
      if (fits(mid)) lo = mid;
      else hi = mid;
    }
  }
  const fontSize = Math.floor(lo * 10) / 10;
  return {fontSize, lines: layout(text, widths, fontSize, maxBoxWidth)};
};

/**
 * FitTextBox — 按容器宽度与行数上限自动定字号的文字块（**自带字体就绪门**）。
 *
 * 字体未就绪时 canvas 量到的是回退字体，算出的字号会偏小；组件内部会等到
 * 主题字体加载完再测量，所以调用方不需要记得这件事。
 *
 * 与 FitCard 的分工：FitCard 管「卡片多高」（fitH 算高度），FitTextBox 管
 * 「这段文字该多大」（实测反推字号）。两者一起用，卡片裁切从源头消失。
 */
export const FitTextBox: React.FC<{
  text: string;
  maxLines: number;
  boxWidth: number;
  fontFamily?: string;
  fontWeight?: number;
  maxFontSize?: number;
  lineHeight?: number;
  color?: string;
  tone?: string;
  showMeasure?: boolean;
}> = ({
  text,
  maxLines,
  boxWidth,
  fontFamily = 'Kai',
  fontWeight = 400,
  maxFontSize = 46,
  lineHeight = 1.6,
  color,
  tone,
  showMeasure = false,
}) => {
  const fontsReady = useFontsReady([fontFamily]);
  if (!fontsReady) return <div style={{width: boxWidth}} />;

  const fitted = fitChineseTextOnNLines({text, maxLines, maxBoxWidth: boxWidth, fontFamily, fontWeight, maxFontSize});
  const styles: React.CSSProperties = {
    fontFamily: `${fontFamily},sans-serif`,
    fontSize: fitted.fontSize,
    fontWeight,
    lineHeight,
    color: color ?? C.ink,
  };
  return (
    <div style={{width: boxWidth}}>
      <div style={styles}>
        {fitted.lines.map((l, i) => (
          <div key={i}>{l}</div>
        ))}
      </div>
      {showMeasure ? (
        <div style={{marginTop: 12, fontFamily: 'Space,monospace', fontSize: TYPE.microS, color: tone ?? C.muted}}>
          字号 {fitted.fontSize.toFixed(1)}px ／ {fitted.lines.length} 行（上限 {maxLines}）／ 容器 {boxWidth}px
          {fitted.lines.length ? ` ／ 最宽行 ${Math.max(...fitted.lines.map((l) => measureText({text: l, fontFamily, fontSize: fitted.fontSize, fontWeight}).width)).toFixed(0)}px` : ''}
        </div>
      ) : null}
    </div>
  );
};

/**
 * assertFits — 文字宽度自检：超宽**抛错**。用于编写期（authoring）自查，
 * 或你自己在场景里调用，把"渲完才发现被裁"提前到渲染期。
 */
export const assertFits = (opts: {text: string; boxWidth: number; fontFamily?: string; fontSize: number; fontWeight?: number; label?: string}) => {
  const m = measureFits(opts);
  if (m.width > opts.boxWidth + 0.5) {
    throw new Error(
      `[TextFitGate] ${opts.label ?? 'text'} 超出容器：实测 ${m.width.toFixed(1)}px > 容器 ${opts.boxWidth}px（字号 ${opts.fontSize}px）。` +
        ` 用 <FitTextBox> 自动定字号，或把 maxLines 调大。`
    );
  }
  return m;
};

/**
 * fitsWithin — 同一次测量，但**只警告不抛错**。
 *
 * 这是 StatRow / VerdictBar 这类"固定尺寸卡片 + 可变文案"组件在开发期自用的检查：
 * 文案比卡片宽时在控制台出声，而不是把渲染打断。
 * 判定用的仍是同一套 measureText 实测，不是估算。
 */
export const fitsWithin = (opts: {text: string; boxWidth: number; fontFamily?: string; fontSize: number; fontWeight?: number; label?: string}) => {
  const m = measureFits(opts);
  if (m.width > opts.boxWidth + 0.5 && process.env.NODE_ENV !== 'production') {
    console.warn(
      `[TextFitGate] ${opts.label ?? 'text'} 文案比容器宽 ${(m.width - opts.boxWidth).toFixed(0)}px（实测 ${m.width.toFixed(1)} > ${opts.boxWidth}）——` +
        ` 固定尺寸卡片请缩短文案，或改用 <FitTextBox> 自动定字号。`
    );
  }
  return m;
};

const measureFits = (opts: {text: string; boxWidth: number; fontFamily?: string; fontSize: number; fontWeight?: number; label?: string}) => {
  const {text, fontFamily = 'Kai', fontSize, fontWeight = 400} = opts;
  if (typeof document !== 'undefined' && !document.fonts.check(`${fontWeight} ${fontSize}px ${fontFamily}`)) {
    console.warn(`[TextFitGate] 字体 ${fontFamily} 尚未就绪，测量可能不准——先调用 useFontsReady(['${fontFamily}'])`);
  }
  return measureText({text, fontFamily, fontSize, fontWeight});
};

/** 静态字体声明：复制到工程入口的 <style> 里（与 index.tsx 的 Fonts 保持一致）。 */
export const themeFontFaces = `
@font-face{font-family:Kai;src:url(${staticFile('LXGWWenKaiLite-Regular.ttf')}) format('truetype');font-weight:400}
@font-face{font-family:Kai;src:url(${staticFile('LXGWWenKaiLite-Medium.ttf')}) format('truetype');font-weight:700}
`;
