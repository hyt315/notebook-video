import React from 'react';

// ============================================================================
// 画布引擎（LOCKED）：3.2.0 起只有一种画布 —— 16:9，交付 2560×1440，设计坐标 1920×1080，
// 交付缩放 4/3。所有主题共用这一份；主题文件通过 useCanvas() 读取字幕安全宽等参数。
// ============================================================================
export const MODES = {
  '16:9': {compW: 2560, compH: 1440, designW: 1920, designH: 1080, subMar: 188, subBottom: 34, subH: 112, safe: 1334, subFont: 44, scale: 4 / 3},
} as const;
export type CanvasMode = keyof typeof MODES;
export type ModeSpec = (typeof MODES)[CanvasMode];

export const CanvasContext = React.createContext<{canvas: CanvasMode; mode: ModeSpec}>({
  canvas: '16:9',
  mode: MODES['16:9'],
});
export const useCanvas = () => React.useContext(CanvasContext);
