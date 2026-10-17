import React from 'react';
import {
  Check, SquarePlay, SquareMenu, FileText, Star, GitFork, GitBranch, Rocket, Shield, SquareTerminal, Cloud, Link, Bug, Search,
  User, Clock, Download, Upload, Folder, ChartNoAxesColumn, Globe, Lock, Mail, CalendarDays, Heart, Settings,
} from 'lucide-react';
import type {LucideIcon} from 'lucide-react';
import {THEME} from './theme/active';

// ============================================================================
// kit · 主题无关的原子组件（从 index.tsx 抽出，供模板场景与工程场景共同引用）
//
// 抽取原因：这些原子此前定义在 index.tsx 内部，导致工程侧无法复用，只能各写一份；
// 也是「能力存在但不可达」的一部分。抽出后 index.tsx 与工程都从这里 import。
//
// 只放**主题无关**的原子。带题材的构件（如模板里的 git 猫吉祥物 Mascot）留在
// 各自的场景文件里，换题材时重画。
// ============================================================================

const C = THEME.palette;
export const TYPE = {displayXL: 58, displayL: 50, displayML: 45, displayM: 43, displayS: 36, displayXS: 34, titleXL: 32, titleL: 30, titleM: 28, titleS: 27, titleXS: 26, bodyL: 26, bodyM: 24, bodyS: 23, labelL: 22, labelM: 21, labelS: 20, microL: 18, microS: 16, subtitle: 44} as const;

/** PillTag：胶囊贴标。 */
export const PillTag: React.FC<{text: string; color?: string; bg?: string; fontSize?: number; fontFamily?: string; fontWeight?: number | string; style?: React.CSSProperties}> = ({text, color = C.orange, bg = C.orangeLight, fontSize = TYPE.microS, fontFamily = 'Space,Kai', fontWeight = 700, style}) => (
  <span style={{display: 'inline-flex', alignItems: 'center', padding: '4px 12px', borderRadius: 999, background: bg, color, fontSize, fontFamily, fontWeight, letterSpacing: 0.8, border: `1px solid ${color}2a`, ...style}}>{text}</span>
);

/**
 * LineIcon：锁定线性图标集。v4.2 起字形来自 lucide-react（ISC），不再手绘 SVG。
 * API 不变：26 个 kind 名、size、color、strokeWidth（仍按 32 视窗的笔画粗细传，
 * 内部换算到 lucide 的 24 视窗：w × 24/32，所以默认 2.2 落在 1.65）。
 * 换题材从这里挑，不要新造风格；需要更多字形时直接从 lucide-react 加映射。
 */
export type IconKind = 'check' | 'play' | 'project' | 'report' | 'star' | 'fork' | 'branch' | 'rocket' | 'shield' | 'terminal' | 'cloud' | 'link' | 'bug' | 'search' | 'user' | 'clock' | 'download' | 'upload' | 'folder' | 'chart' | 'globe' | 'lock' | 'mail' | 'calendar' | 'heart' | 'settings';

export const LINE_ICON_GLYPHS: Record<IconKind, LucideIcon> = {
  check: Check, play: SquarePlay, project: SquareMenu, report: FileText, star: Star, fork: GitFork, branch: GitBranch,
  rocket: Rocket, shield: Shield, terminal: SquareTerminal, cloud: Cloud, link: Link, bug: Bug, search: Search, user: User,
  clock: Clock, download: Download, upload: Upload, folder: Folder, chart: ChartNoAxesColumn, globe: Globe, lock: Lock,
  mail: Mail, calendar: CalendarDays, heart: Heart, settings: Settings,
};

export const LineIcon: React.FC<{kind: IconKind; size?: number; color?: string; strokeWidth?: number}> = ({kind, size = 28, color = 'currentColor', strokeWidth = 2.2}) => {
  const Glyph = LINE_ICON_GLYPHS[kind];
  if (!Glyph) throw new Error(`[LineIcon] 未知 kind "${String(kind)}"。合法值：${Object.keys(LINE_ICON_GLYPHS).join(', ')}`);
  return <Glyph size={size} color={color} strokeWidth={(strokeWidth * 24) / 32} aria-hidden="true" />;
};

/** CheckBadge：对勾圆徽章。 */
export const CheckBadge: React.FC<{size?: number}> = ({size = 30}) => (
  <span style={{width: size, height: size, borderRadius: 999, background: C.green, color: C.white, display: 'inline-grid', placeItems: 'center', flex: '0 0 auto', boxShadow: `0 2px 8px ${C.greenGlow}`}}>
    <LineIcon kind="check" size={size * 0.62} color={C.white} strokeWidth={2.7} />
  </span>
);

export const KIT_VERSION = 'kit-v2 · PillTag / LineIcon(26 glyphs, lucide-react) / CheckBadge';
