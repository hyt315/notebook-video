// 把门禁 stdout 里的 P1 明细收进 renders/report.md 的「建议（不拦）」。
// 3.5.2 之前 make-video.mjs 里的正则只认 `P1 <编号>:` 这一种写法，其余门禁的建议
// 只在终端滚过去、报告里一条都没有。各 validate-*.py 实际有三种明细行：
//   `  P1 G-5: 好几件事挤在一拍上`   带编号 + 半角冒号（composition / presentation / shot-motion / facts）
//   `  P1 分镜相邻两镜同一张背景`    无冒号（backgrounds / audio-levels / fusion / frame-props）
//   `  · P1 中央 70 % 起伏`          带项目符号（media / opening / treatment）
// 汇总行 `结论：P0=0 P1=3 → PASS` 与 `…通过（P0 0，P1 3）` 不是明细，不能收。
// 这里只改「哪些建议被写进报告」，不改任何门禁判据、退出码或是否拦片。
const TAGGED = /^([-\w]+)\s*[:：]\s*(.+)$/;

export function collectP1(out, gate) {
  const line = /^\s*(?:·\s*)?P1\s+(.+)$/gm;   // 每次新建：避免 matchAll 共享 lastIndex
  const name = String(gate).replace(/\.py$/, '');
  return [...String(out || '').matchAll(line)].map((m) => {
    const body = m[1].trim();
    const tagged = body.match(TAGGED);
    return `${name}：${(tagged ? tagged[2] : body).trim()}`;
  });
}
