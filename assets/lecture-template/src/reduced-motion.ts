import {getInputProps} from 'remotion';

/**
 * reduced-motion（P2-21 降低动态）。
 *
 * 开启方式：`--props '{"nvReducedMotion":"on"}'`，CLI 的 `--reduced-motion` 会代劳。
 * 缺省 false —— **成片不受影响**。这是给预览 / 可访问性用的降动态方案：
 *   · 相机不动（drift / focus / pan 全关，取景定死）
 *   · 元素直接到位（不淡入、不上浮、不逐字）
 *   · 转场退化为 fade（保「换镜」的语义，去掉卷页 / 甩镜的剧烈运动）
 * 内容顺序与语义**不变**：元素仍按 `at` 逐个出现，只是不动。验收是「减少动态后内容顺序完整」。
 */
export const REDUCED_MOTION: boolean = (() => {
  try { return (getInputProps() as {nvReducedMotion?: string})?.nvReducedMotion === 'on'; } catch { return false; }
})();
