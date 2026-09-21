import React from 'react';

// ============================================================================
// 画布引擎（LOCKED）：三种锁定画布与共享设计坐标，所有主题共用同一份。
// 主题文件通过 useCanvas() 感知当前比例，装饰坐标按比例各自锁死。
// ============================================================================
export const MODES = {
  '16:9': {compW: 2560, compH: 1440, designW: 1920, designH: 1080, subMar: 188, subBottom: 34, subH: 112, safe: 1334, subFont: 44, scale: 4 / 3},
  '4:3':  {compW: 1920, compH: 1440, designW: 1440, designH: 1080, subMar: 60,  subBottom: 34, subH: 112, safe: 1060, subFont: 44, scale: 4 / 3},
  '3:4':  {compW: 1440, compH: 1920, designW: 1080, designH: 1440, subMar: 50,  subBottom: 40, subH: 104, safe: 900,  subFont: 40, scale: 4 / 3},
} as const;
export type CanvasMode = keyof typeof MODES;
// tsc TS2322：`typeof MODES['16:9']` 只认 16:9 那一种，于是 index.tsx 的
// `MODES[canvas] || MODES['16:9']`（三种模式的联合）塞不进 Context 的 mode 槽。
// 三个模式的键名完全一致、只有数值不同，取属性不受影响 —— 改成**三种模式的联合**。
export type ModeSpec = (typeof MODES)[keyof typeof MODES];

export const CanvasContext = React.createContext<{canvas: CanvasMode; isPortrait: boolean; mode: ModeSpec}>({
  canvas: '16:9',
  isPortrait: false,
  mode: MODES['16:9'],
});
export const useCanvas = () => React.useContext(CanvasContext);
