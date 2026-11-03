// ============================================================================
// render-log.mjs · 每次渲染写一行结构化耗时（P1-13）
//
// 为什么需要：以前性能只能靠终端里零散的墙钟实测，说不清一次优化省在 bundle、
// 浏览器启动、逐帧、编码还是拼接；也无法判断"这次快了"是不是因为热缓存。
//
// 这里只做三件事，全部可单测（不依赖 Remotion）：
//   1. classifyExit：把退出归到 ok / cancelled / stalled / process-error 四类之一；
//   2. appendRunLog：往 `<工程>/renders/render-log.jsonl` 追加一行（失败也写）；
//   3. summarize：从这些行算出各阶段的中位数 / p95 —— 报告不再靠手抄终端。
//
// 一行就是一次运行。追加而不是覆盖：三次取中位数要求保留历史。
// ============================================================================

import fs from 'node:fs';
import path from 'node:path';

export const RUN_LOG_REL = 'renders/render-log.jsonl';
export const RUN_LOG_SCHEMA = 1;

/**
 * 四类退出必须能分开：混成一句"失败"就没法判断该修代码还是该加内存。
 *   ok             正常交付
 *   cancelled      用户 Ctrl-C / 信号（不算缺陷，也不该写 failed）
 *   stalled        看门狗判定"一动不动"（8 分钟无输出）
 *   process-error  子进程非零退出 / 我们自己的 fail()
 */
export const classifyExit = ({ok = false, signal = null, stalled = false, code = 0} = {}) => {
  if (ok) return 'ok';
  if (stalled) return 'stalled';
  if (signal) return 'cancelled';
  return code === 0 ? 'ok' : 'process-error';
};

const round = (ms) => Math.round(ms);

/** 追加一行 JSONL。目录不存在就建；写日志失败不能拖垮渲染本身。 */
export const appendRunLog = (project, entry, {file = null, now = new Date()} = {}) => {
  const target = file || path.join(project, RUN_LOG_REL);
  const row = {schema: RUN_LOG_SCHEMA, at: now.toISOString(), ...entry};
  try {
    fs.mkdirSync(path.dirname(target), {recursive: true});
    fs.appendFileSync(target, `${JSON.stringify(row)}\n`);
    return {ok: true, file: target};
  } catch (e) {
    return {ok: false, file: target, error: String(e && e.message ? e.message : e)};
  }
};

export const readRunLog = (project, {file = null} = {}) => {
  const target = file || path.join(project, RUN_LOG_REL);
  let text = '';
  try { text = fs.readFileSync(target, 'utf8'); } catch { return []; }
  return text.split('\n').filter((l) => l.trim()).map((l) => {
    try { return JSON.parse(l); } catch { return null; }
  }).filter(Boolean);
};

const median = (xs) => {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  const mid = s.length >> 1;
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
};

const p95 = (xs) => {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  return s[Math.min(s.length - 1, Math.ceil(s.length * 0.95) - 1)];
};

/**
 * 按阶段汇总。阶段集合不写死：不同渲染路径（有 / 无卷页窗口、是否续跑）
 * 走的阶段本来就不同，写死会让"这一阶段没跑"和"这一阶段是 0 ms"混在一起。
 */
export const summarize = (rows, {state = 'ok'} = {}) => {
  const picked = rows.filter((r) => (state === 'all' ? true : r.state === state));
  const stages = {};
  for (const row of picked) {
    for (const [name, ms] of Object.entries(row.stages || {})) {
      if (typeof ms !== 'number') continue;
      (stages[name] ||= []).push(ms);
    }
  }
  const out = {runs: picked.length, stages: {}};
  for (const [name, xs] of Object.entries(stages)) {
    out.stages[name] = {n: xs.length, median: round(median(xs)), p95: round(p95(xs)),
                        min: round(Math.min(...xs)), max: round(Math.max(...xs))};
  }
  const totals = picked.map((r) => r.stages?.total).filter((x) => typeof x === 'number');
  if (totals.length) {
    out.total = {n: totals.length, median: round(median(totals)), p95: round(p95(totals)),
                 min: round(Math.min(...totals)), max: round(Math.max(...totals))};
  }
  return out;
};

export const formatSummary = (summary, {state = 'ok'} = {}) => {
  if (!summary.runs) return `没有 state=${state} 的历史记录`;
  const lines = [`最近 ${summary.runs} 次 state=${state} 的渲染（毫秒）`];
  const rows = Object.entries(summary.stages)
    .sort((a, b) => (b[1].median ?? 0) - (a[1].median ?? 0));
  for (const [name, s] of rows) {
    lines.push(`  ${name.padEnd(12)} 中位 ${String(s.median).padStart(7)} · p95 ${String(s.p95).padStart(7)} · ${s.min}–${s.max}（n=${s.n}）`);
  }
  if (summary.total) {
    lines.push(`  ${'合计'.padEnd(11)} 中位 ${String(summary.total.median).padStart(7)} · p95 ${String(summary.total.p95).padStart(7)} · ${summary.total.min}–${summary.total.max}`);
  }
  return lines.join('\n');
};
