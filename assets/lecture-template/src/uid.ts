import {useId} from 'react';

/**
 * SVG defs 的 id 前缀：**每个组件实例**唯一。
 *
 * 为什么不能用业务 id（spec.id / media id / seed）当 DOM id：
 * 转场期间上一镜与本镜同时挂载（见 index.tsx 的 FinalDemo），两镜里 `spec.id` 都叫 `n1`
 * 时就会渲染出两个 `<filter id="paint-n1-0">`。浏览器按文档取第一个，于是后一镜的颜料
 * 滤镜用了前一镜的 seed —— 画面看起来"脏了一点"，但没人能从日志里发现。同理，
 * 同一镜里两个 `WashBlob` 都用默认 seed 时，第二个的颗粒纹理会套第一个的 id。
 *
 * React 的 useId 由树位置决定：同一实例跨帧稳定（渲染可重放），不同实例（含转场里
 * 分属两个分支的同名组件）必然不同。开头的 `:` 会被去掉 —— SVG 的 `url(#…)` 不认它。
 */
export const useSvgId = (prefix: string): string => `${prefix}-${useId().replace(/[^\w-]/g, '')}`;

/** 同一进程里只警告一次：渲染一帧就 warn 一次会把日志冲掉，等于没告警。 */
const warned = new Set<string>();
export const warnOnce = (key: string, message: string): void => {
  if (warned.has(key)) return;
  warned.add(key);
  console.warn(message);
};
