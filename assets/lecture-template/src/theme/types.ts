import React from 'react';
import type {ModeSpec} from './canvas';

// ============================================================================
// 主题契约（LOCKED）：每个主题必须完整实现以下接口，缺一不可。
// 主题只提供「皮肤与装饰」，不允许改动排版结构、字号阶梯与动效参数。
// ============================================================================

export interface ThemePalette {
  ink: string; muted: string;
  blue: string;
  blueInk: string; blueLight: string;
  orange: string;
  orangeInk: string; orangeLight: string;
  green: string;
  greenInk: string; greenLight: string;
  gold: string;
  goldInk: string; red: string; redInk: string; navy: string;
  paper: string; paperWarm: string; paperBase: string;
  line: string; lineOrange: string; lineBlue: string; lineGreen: string;
  white: string;
  // ---- 场景层柔色 token（引擎引用，主题必须提供）----
  // 注：paper / paperWarm / paperBase 是「卡片面 / 暖面 / 底面」的通用 token 名（Paper 卡片组件沿用），与已删除的 paper 主题无关。
  skyTint: string;      // 地球/舷窗淡色填充
  blueLine: string;     // git main 主干线
  dotIdle: string;      // 未点亮的合并圆点
  mutedFill: string;    // 步骤圆未激活底色
  mutedBar: string;     // 代码条未激活底色
  mutedWash: string;    // LOCAL HOST 胶囊底色
  orangeSoft: string;   // CTA 波浪字起始色
  orangeDeep: string;   // 章节序号渐变深色端
  gaugeTrack: string;   // 仪表盘轨道底色
  greenGlow: string;    // 对勾徽章投影色
  stageTint: string;    // 舞台背板暖色端
  headerAccent: string; // 技术头部主色（flat 上须在色块上可读）
  headerSub: string;    // 技术头部副色
}

export interface ThemeAesthetic {
  subtitleSafeWidth: number;
  paperRadius: number;
  paperOutline: number;
  textureOpacity: number;
  gridOpacity: number;
  gradeWarmth: number;
  gradeVignette: number;
  /**
   * 字幕实测参数（v2.10 新增）：CaptionFitGate 必须按主题真实渲染的字重/字距/内边距来量，
   * 否则门禁会漏判。subtitlePadX = 主题字幕框左右内边距之和（含装饰点），
   * 有效文字宽 = mode.safe - subtitlePadX。
   */
  subtitleWeight?: number;
  subtitleLetterSpacing?: number;
  subtitlePadX?: number;
}

/**
 * 背景变体（v4.1）：每个主题三张锁定位图，中央约 70% 都是安静的内容安全区。
 *   main    常规镜头
 *   chapter 每章首镜（章节卡出现的那一镜），比 main 更有节庆感
 *   quiet   信息密集的镜头（zones ≥ 4），装饰最少
 * 引擎按分镜表自动选（index.tsx 的 bgVariantFor），分镜表可用 `bg` 字段显式覆盖。
 */
export type BgVariant = 'main' | 'chapter' | 'quiet';
export const BG_VARIANTS: readonly BgVariant[] = ['main', 'chapter', 'quiet'];

export interface Theme {
  id: 'flat' | 'cel';
  palette: ThemePalette;
  aesthetic: ThemeAesthetic;
  /** 卡片阴影：lift 0=静止贴面，1=完全举起。签名与语义所有主题一致。 */
  paperShadow: (lift: number) => string;
  /** 三张背景位图（public/ 下的相对路径），与 manifests/visual-assets.json 一一对应。 */
  backgrounds: Record<BgVariant, string>;
  /** 整幅背景（含装饰），16:9 锁定坐标；variant 缺省为 main。 */
  Background: React.FC<{variant?: BgVariant}>;
  /** 卡片容器：props 契约与原 Paper 完全一致。 */
  Paper: React.FC<{children?: React.ReactNode; style?: React.CSSProperties; lift?: number; borderColor?: string}>;
  /** 全局调色层（柔光/暗角）。 */
  Grade: React.FC;
  /** 字幕容器：负责定位与外壳；内部的逐词浮现由引擎渲染为 children 传入。 */
  SubtitleChrome: React.FC<{mode: ModeSpec; children?: React.ReactNode}>;
  /**
   * 页眉底板（可选，v4.1）：右上角技术页眉的外壳样式。背景右上角有高对比装饰的主题
   * （cel 的速度线 / 爆炸星）必须给页眉垫一块底板，否则墨字会被装饰吃掉；flat 不需要。
   */
  headerPlate?: React.CSSProperties;
  /** 主题专属锁定构件（如赛璐璐爆炸贴 Burst），场景层只传内容参数。 */
  extras?: Record<string, React.FC<any>>;
  /**
   * 背景装饰区（可选）：三张背景位图里「画幅级、高对比」的锁定装饰所占矩形的并集
   * （1920×1080 设计坐标）。这些区域会吃掉压在上面的文字，因此：
   *   1. 内容压到装饰区时，必须坐在 CoverPanel（tone='paper'）上；
   *   2. 不要铺成片级整幅底托（v4.1 删除：它把四角装饰洗成幽灵）；背景中央本就是安全区。
   * 背景图本身不改——它很好看；只解决可读性。
   */
  backgroundDecorZones?: {x: number; y: number; w: number; h: number}[];
}
