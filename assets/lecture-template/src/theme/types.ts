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
  /**
   * 3.3.0 新增（可选）：皮肤自己的字幕字号（设计 px）与字族。缺省 = mode.subFont（44）+ 'Kai'。
   * 手作皮肤用 72（= 交付 2560×1440 上的 96 px，用户字幕规范）+ 'Serif'（Noto Serif SC Bold）。
   * CaptionFitGate 按这里的真实字号 / 字族量宽度，所以皮肤与门禁永远一致。
   */
  subtitleSize?: number;
  subtitleFamily?: string;
}

/** 3.3.0：皮肤可选的章节标识（替代引擎缺省的「章节卡 + 右上技术页眉」）。 */
export interface ChromeProps {
  /** 章节序号（0 起）与本章标题；kicker / header / headerSub 来自 film.ts 的 COPY */
  stage: number; title: string; kicker: string; header: string; headerSub: string;
  /** 本章起始帧之后的本地帧（用于入场动画） */
  local: number;
}

/** 3.3.0：皮肤的「材质」声明 —— 给 craft 组件（src/craft/）读，旧皮肤不用写。 */
export interface ThemeCraft {
  /** 媒介名（写进 treatment.json 的 medium 应与之对应） */
  medium: 'journal' | 'papercut' | 'archive' | string;
  /** 卡片上叠的纸纤维纹理强度 0–1（public/craft/fibre-tile.png） */
  fibre: number;
  /** 墨线颜色（InkPath / HandNote 缺省色） */
  inkLine: string;
  /** 手写批注字族 */
  handFamily: string;
  /** 正文 / 标题字族（衬线 or 楷体） */
  bodyFamily: string;
  /** 唯一强调色（lemo 配方「一个强调色」纪律） */
  accent: string;
  /** 缺省转场（分镜表写 auto 时用） */
  transition: 'slide' | 'drop' | 'ink' | 'whip' | 'zoom' | 'fade';
  /** 需要额外加载的字体（AssetGate 会 load 并校验；缺字体则拒绝渲染并提示 `fonts --serif`） */
  fonts?: string[];
}

/**
 * 背景变体：每个主题三张锁定位图，中央约 70% 都是安静的内容安全区。
 *   main    常规镜头
 *   chapter 每章首镜（章节卡出现的那一镜），比 main 更有节庆感
 *   quiet   信息密集的镜头（zones ≥ 4），装饰最少
 * 引擎按分镜表自动选（index.tsx 的 bgVariantFor），分镜表可用 `bg` 字段显式覆盖。
 */
export type BgVariant = 'main' | 'chapter' | 'quiet';
export const BG_VARIANTS: readonly BgVariant[] = ['main', 'chapter', 'quiet'];

export interface Theme {
  id: 'flat' | 'cel' | 'journal' | 'papercut' | 'archive';
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
   * 页眉底板（可选，3.2.0）：右上角技术页眉的外壳样式。背景右上角有高对比装饰的主题
   * （cel 的速度线 / 爆炸星）必须给页眉垫一块底板，否则墨字会被装饰吃掉；flat 不需要。
   */
  headerPlate?: React.CSSProperties;
  /** 3.3.0（可选）：皮肤自己的章节标识。给了就替换引擎缺省 chrome（章节卡 + 技术页眉）。 */
  Chrome?: React.FC<ChromeProps>;
  /** 3.3.0（可选）：手作材质参数，src/craft/ 组件读取。 */
  craft?: ThemeCraft;
  /** 主题专属锁定构件（如赛璐璐爆炸贴 Burst），场景层只传内容参数。 */
  extras?: Record<string, React.FC<any>>;
  /**
   * 背景装饰区（可选）：三张背景位图里「画幅级、高对比」的锁定装饰所占矩形的并集
   * （1920×1080 设计坐标）。这些区域会吃掉压在上面的文字，因此：
   *   1. 内容压到装饰区时，必须坐在 CoverPanel（tone='paper'）上；
   *   2. 不要铺成片级整幅底托（3.2.0 删除：它把四角装饰洗成幽灵）；背景中央本就是安全区。
   * 背景图本身不改——它很好看；只解决可读性。
   */
  backgroundDecorZones?: {x: number; y: number; w: number; h: number}[];
}
