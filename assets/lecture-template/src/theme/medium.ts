// 媒介语义的唯一真源
//
// 皮肤可以同时拥有两种完全不同的「craft」信息：
//   1. 能力配置：线稿墨色、字体、缺省转场。flat / cel 也需要它，不应等同于手作媒介。
//   2. 审美媒介：纸、剪刀、胶带、印章，以及与之匹配的拟音。
//
// 若按 `Boolean(THEME.craft)` 判断，只声明了线稿能力的 flat / cel 也会拿到手作纸卡和纸片拟音。
// 这里把判断收成一处：能力判断看「有没有配置」，
// 审美判断只认明确的手作媒介名单。新增中性皮肤时，不会因为“顺手写了 craft”而变成手账。
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
