// 媒介语义的唯一真源（3.8.0 · P1-10 + P1-34）
//
// 皮肤可以同时拥有两种完全不同的「craft」信息：
//   1. 能力配置：线稿墨色、字体、缺省转场。flat / cel 也需要它，不应等同于手作媒介。
//   2. 审美媒介：纸、剪刀、胶带、印章，以及与之匹配的拟音。
//
// 旧代码在 auto.tsx 与 sfx.ts 里都写 `Boolean(THEME.craft)`，于是 flat / cel 虽然只是
// 声明了线稿能力，却拿到了手作纸卡和纸片拟音。这里把判断收成一处：能力判断看「有没有配置」，
// 审美判断只认明确的手作媒介名单。新增中性皮肤时，不会再因为“顺手写了 craft”而变成手账。
export const HANDMADE_MEDIA = ['journal', 'papercut', 'archive'] as const;
export type HandmadeMedium = (typeof HANDMADE_MEDIA)[number];

export type MediumTheme = {
  craft?: {medium?: string} | null;
};

/** 皮肤是否声明了线稿 / 字体 / 转场等 craft 能力。不等于“是手作媒介”。 */
export const hasCraftConfig = (theme: MediumTheme | null | undefined): boolean => Boolean(theme?.craft);

/** 皮肤是否是手作媒介。视觉纸卡与自动拟音都必须只认这一个判断。 */
export const isHandmadeMedium = (theme: MediumTheme | null | undefined): boolean =>
  (HANDMADE_MEDIA as readonly string[]).includes(theme?.craft?.medium ?? '');
