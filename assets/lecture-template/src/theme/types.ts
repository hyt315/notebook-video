import React from 'react';
import type {ModeSpec} from './canvas';

// ============================================================================
// 主题契约（LOCKED）：每个主题必须完整实现以下接口，缺一不可。
// 主题只提供「皮肤与装饰」，不允许改动排版结构、字号阶梯与动效参数。
// ============================================================================

export interface ThemePalette {
  ink: string; muted: string;
  blue: string; blueLight: string;
  orange: string; orangeLight: string;
  green: string; greenLight: string;
  gold: string; red: string; navy: string;
  paper: string; paperWarm: string; paperBase: string;
  line: string; lineOrange: string; lineBlue: string; lineGreen: string;
  white: string;
}

export interface ThemeAesthetic {
  subtitleSafeWidth: number;
  paperRadius: number;
  paperOutline: number;
  textureOpacity: number;
  gridOpacity: number;
  gradeWarmth: number;
  gradeVignette: number;
}

export interface Theme {
  id: 'paper' | 'cel' | 'sticker' | 'flat';
  palette: ThemePalette;
  aesthetic: ThemeAesthetic;
  /** 卡片阴影：lift 0=静止贴面，1=完全举起。签名与语义所有主题一致。 */
  paperShadow: (lift: number) => string;
  /** 整幅背景（含装饰），可用 useCanvas() 读取比例并给出该比例的锁定坐标。 */
  Background: React.FC;
  /** 卡片容器：props 契约与原 Paper 完全一致。 */
  Paper: React.FC<{children?: React.ReactNode; style?: React.CSSProperties; lift?: number; borderColor?: string}>;
  /** 全局调色层（柔光/暗角）。 */
  Grade: React.FC;
  /** 字幕容器：负责定位与外壳；内部的逐词浮现由引擎渲染为 children 传入。 */
  SubtitleChrome: React.FC<{mode: ModeSpec; children?: React.ReactNode}>;
  /** 主题专属锁定构件（如赛璐璐爆炸贴、贴纸胶带），场景层只传内容参数。 */
  extras?: Record<string, React.FC<any>>;
}
