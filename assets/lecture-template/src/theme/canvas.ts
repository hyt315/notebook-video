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
export type ModeSpec = typeof MODES['16:9'];

export const CanvasContext = React.createContext<{canvas: CanvasMode; isPortrait: boolean; mode: ModeSpec}>({
  canvas: '16:9',
  isPortrait: false,
  mode: MODES['16:9'],
});
export const useCanvas = () => React.useContext(CanvasContext);
