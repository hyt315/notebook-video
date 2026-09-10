import React from 'react';
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

/** LineIcon：锁定线性图标集（32 视窗 / 圆头描边）。换题材从这里挑，不要新造风格。 */
export type IconKind = 'check' | 'play' | 'project' | 'report' | 'star' | 'fork' | 'branch' | 'rocket' | 'shield' | 'terminal' | 'cloud' | 'link' | 'bug' | 'search' | 'user' | 'clock' | 'download' | 'upload' | 'folder' | 'chart' | 'globe' | 'lock' | 'mail' | 'calendar' | 'heart' | 'settings';

export const LineIcon: React.FC<{kind: IconKind; size?: number; color?: string; strokeWidth?: number}> = ({kind, size = 28, color = 'currentColor', strokeWidth = 2.2}) => {
  const common = {fill: 'none', stroke: color, strokeWidth, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      {kind === 'check' && <path {...common} d="M7 16.5l5.6 5.5L25 9.8" />}
      {kind === 'play' && (
        <>
          <rect {...common} x="5" y="6" width="22" height="20" rx="3" />
          <path {...common} d="M13 11.5l8 4.5-8 4.5z" />
        </>
      )}
      {kind === 'project' && (
        <>
          <rect {...common} x="6" y="7" width="20" height="18" rx="2.5" />
          <path {...common} d="M10 12h12M10 16h8M10 20h6" />
        </>
      )}
      {kind === 'report' && (
        <>
          <path {...common} d="M9 5h10l5 5v17H9z" />
          <path {...common} d="M19 5v6h5M13 16h7M13 20h7" />
        </>
      )}
      {kind === 'star' && <path {...common} d="M16 4.5l3.5 7.2 7.9 1.1-5.7 5.5 1.3 7.8-7-3.7-7 3.7 1.3-7.8-5.7-5.5 7.9-1.1z" />}
      {kind === 'fork' && (
        <>
          <circle {...common} cx="16" cy="6" r="2.6" />
          <circle {...common} cx="7" cy="26" r="2.6" />
          <circle {...common} cx="25" cy="26" r="2.6" />
          <path {...common} d="M16 8.6V15c0 3.2-5 3.8-7.2 6M16 15c0 3.2 5 3.8 7.2 6" />
        </>
      )}
      {kind === 'branch' && (
        <>
          <circle {...common} cx="9" cy="7" r="2.6" />
          <circle {...common} cx="9" cy="25" r="2.6" />
          <circle {...common} cx="23" cy="7" r="2.6" />
          <path {...common} d="M9 9.6v12.8M23 9.6c0 5.6-6.5 5.4-10.4 8.2" />
        </>
      )}
      {kind === 'rocket' && (
        <>
          <path {...common} d="M16 3c4.5 3.5 4.5 11 0 15.5C11.5 14 11.5 6.5 16 3z" />
          <circle {...common} cx="16" cy="10.5" r="1.8" />
          <path {...common} d="M12.4 15L8.7 21l3.1-1.6M19.6 15l3.7 6-3.1-1.6M14.5 20q1.5 4 3 0" />
        </>
      )}
      {kind === 'shield' && <path {...common} d="M16 4l9.5 3.6v7.9c0 5.6-4.2 9.6-9.5 11.5-5.3-1.9-9.5-5.9-9.5-11.5V7.6z" />}
      {kind === 'terminal' && (
        <>
          <rect {...common} x="4" y="6" width="24" height="20" rx="3" />
          <path {...common} d="M9 12.5l4.5 3.5-4.5 3.5M15.5 20h7" />
        </>
      )}
      {kind === 'cloud' && <path {...common} d="M9.5 22.5a4.8 4.8 0 0 1-.7-9.5 6.2 6.2 0 0 1 12.1 1.6 3.9 3.9 0 0 1-1.4 7.9z" />}
      {kind === 'link' && (
        <>
          <path {...common} d="M13.2 18.8l-1.9 1.9a4.3 4.3 0 0 1-6-6l1.9-1.9M18.8 13.2l1.9-1.9a4.3 4.3 0 0 0-6-6l-1.9 1.9" />
          <path {...common} d="M12 20l8-8" />
        </>
      )}
      {kind === 'bug' && (
        <>
          <rect {...common} x="10" y="11" width="12" height="13" rx="6" />
          <circle {...common} cx="16" cy="8" r="3" />
          <path {...common} d="M13.5 5.5L12 3M18.5 5.5L20 3M10 14.5H5.5M10 19H6M11 23l-2.5 2.5M22 14.5h4.5M22 19h4M21 23l2.5 2.5" />
        </>
      )}
      {kind === 'search' && (
        <>
          <circle {...common} cx="14" cy="14" r="8.5" />
          <path {...common} d="M20.5 20.5L27 27" />
        </>
      )}
      {kind === 'user' && (
        <>
          <circle {...common} cx="16" cy="11" r="5" />
          <path {...common} d="M6 27c1.5-5 5.5-7.5 10-7.5s8.5 2.5 10 7.5" />
        </>
      )}
      {kind === 'clock' && (
        <>
          <circle {...common} cx="16" cy="16" r="11" />
          <path {...common} d="M16 10v6l4.5 2.5" />
        </>
      )}
      {kind === 'download' && <path {...common} d="M16 4v13.5M10.5 12L16 17.5 21.5 12M6 22v3.5A2.5 2.5 0 0 0 8.5 28h15a2.5 2.5 0 0 0 2.5-2.5V22" />}
      {kind === 'upload' && <path {...common} d="M16 17.5V4M10.5 9.5L16 4l5.5 5.5M6 22v3.5A2.5 2.5 0 0 0 8.5 28h15a2.5 2.5 0 0 0 2.5-2.5V22" />}
      {kind === 'folder' && <path {...common} d="M4 9a2.5 2.5 0 0 1 2.5-2.5h6L16 10h9.5A2.5 2.5 0 0 1 28 12.5v11A2.5 2.5 0 0 1 25.5 26h-19A2.5 2.5 0 0 1 4 23.5z" />}
      {kind === 'chart' && <path {...common} d="M5 27h22M8.5 27v-8M16 27V9M23.5 27V15" />}
      {kind === 'globe' && (
        <>
          <circle {...common} cx="16" cy="16" r="11" />
          <ellipse {...common} cx="16" cy="16" rx="5" ry="11" />
          <path {...common} d="M5 16h22" />
        </>
      )}
      {kind === 'lock' && (
        <>
          <rect {...common} x="8" y="14" width="16" height="12" rx="2.5" />
          <path {...common} d="M11 14v-3.5a5 5 0 0 1 10 0V14M16 19v3" />
        </>
      )}
      {kind === 'mail' && (
        <>
          <rect {...common} x="4" y="7" width="24" height="18" rx="2.5" />
          <path {...common} d="M5 9.5l11 8 11-8" />
        </>
      )}
      {kind === 'calendar' && (
        <>
          <rect {...common} x="5" y="6.5" width="22" height="20" rx="2.5" />
          <path {...common} d="M5 12.5h22M11 4v5M21 4v5M11 17h3M18 17h3M11 21.5h3M18 21.5h3" />
        </>
      )}
      {kind === 'heart' && <path {...common} d="M16 26S5.5 19.5 5.5 12.3A5.8 5.8 0 0 1 16 8.6a5.8 5.8 0 0 1 10.5 3.7C26.5 19.5 16 26 16 26z" />}
      {kind === 'settings' && (
        <>
          <circle {...common} cx="16" cy="16" r="4.5" />
          <path {...common} d="M16 3.5v4M16 24.5v4M3.5 16h4M24.5 16h4M7.2 7.2l2.8 2.8M22 22l2.8 2.8M24.8 7.2L22 10M10 22l-2.8 2.8" />
        </>
      )}
    </svg>
  );
};

/** CheckBadge：对勾圆徽章。 */
export const CheckBadge: React.FC<{size?: number}> = ({size = 30}) => (
  <span style={{width: size, height: size, borderRadius: 999, background: C.green, color: C.white, display: 'inline-grid', placeItems: 'center', flex: '0 0 auto', boxShadow: `0 2px 8px ${C.greenGlow}`}}>
    <LineIcon kind="check" size={size * 0.62} color={C.white} strokeWidth={2.7} />
  </span>
);

export const KIT_VERSION = 'kit-v1 · PillTag / LineIcon(26 glyphs) / CheckBadge';
