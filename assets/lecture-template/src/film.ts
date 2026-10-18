// 片级文案与章节（3.2.0 从 index.tsx 抽出）。
// auto 流程（scripts/compose-story.py）会按 story.json 覆盖本文件；手写场景的工程直接改这里。
export const COPY = {
  chapterTitles: ['代码不再孤独', '入场三步', '第二步 · 发布', '第三步 · 运营与三技能'],
  chromeKicker: 'GITHUB 新手三部曲',
  header: '开源之路 / OPEN SOURCE',
  headerSub: 'CONTRIBUTE · PREP · OPS / EP0',
} as const;
// 章节 = 分镜表里各章首镜。章节卡与页眉由此驱动，不手写帧号。
export const CHAPTER_SHOTS = ['S1', 'S2', 'S4', 'S5'] as const;
