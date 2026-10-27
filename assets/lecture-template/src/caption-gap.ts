// caption-gap.ts · 字幕词片之间的空格规则（3.6.0 从 index.tsx 抽出，tests/test_captions.py 直接跑这个文件）。
// 只用纯 JS 语法加两处参数类型标注，测试端去掉类型后用 node 执行。

/**
 * 词片之间要不要补一个不折行空格（\u00a0）：中英 / 数字与汉字相邻时补；上一片以空白结尾（'语 '）也补——
 * 词片渲染成 inline-block，尾随空格会被折叠掉，旧规则又看到上一片以空白结尾就不补，于是「拉丁语 cella」变成「拉丁语cella」。
 */
export const captionGap = (prevRaw: string, partRaw: string): string => {
  if (!prevRaw) return '';
  const part = partRaw.replace(/^\s+/, '');
  if (!part || /^[，。！？；：、,.!?;:）)」』”]/.test(part)) return '';
  if (/\s$/.test(prevRaw)) return '\u00a0';
  if (/[，。！？；：、,.!?;:（(「『“]$/.test(prevRaw)) return '';
  if ((/[A-Za-z0-9]$/.test(prevRaw) && /^[A-Za-z0-9]/.test(part)) || (/[一-鿿]$/.test(prevRaw) && /^[一-鿿]/.test(part))) return '';
  return '\u00a0';
};
