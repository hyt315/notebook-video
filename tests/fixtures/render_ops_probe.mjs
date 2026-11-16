// render_ops_probe.mjs · 用 node 直接验证 render-log.mjs 的行为。
// 模块不 import Remotion，所以可以在没有 node_modules 的环境里跑。
// 输出一行 JSON：{ok, checks:[{name, pass, detail}]}

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const mods = process.env.NV_SCRIPTS;
const {classifyExit, appendRunLog, readRunLog, summarize, formatSummary} = await import(
  'file://' + path.join(mods, 'render-log.mjs').replace(/\\/g, '/')
);

const checks = [];
const check = (name, pass, detail = '') => checks.push({name, pass: Boolean(pass), detail: String(detail)});
const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'nv-ops-'));

// ---- 1. 四类退出必须分开 ---------------------------------------------------
check('classify-ok', classifyExit({ok: true, code: 0}) === 'ok');
check('classify-cancelled', classifyExit({signal: 'SIGINT', code: 130}) === 'cancelled',
  classifyExit({signal: 'SIGINT', code: 130}));
check('classify-stalled', classifyExit({stalled: true, code: 1}) === 'stalled',
  classifyExit({stalled: true, code: 1}));
check('classify-process-error', classifyExit({code: 1}) === 'process-error');

// ---- 2. 运行日志：追加、读回、中位数可复算 ---------------------------------
{
  const dir = tmp();
  appendRunLog(dir, {state: 'ok', stages: {total: 100, bundle: 10, segments: 60}});
  appendRunLog(dir, {state: 'ok', stages: {total: 130, bundle: 20, segments: 70}});
  appendRunLog(dir, {state: 'ok', stages: {total: 160, bundle: 30, segments: 80}});
  appendRunLog(dir, {state: 'failed', stage: 'segment', stages: {total: 50, bundle: 10}});
  const rows = readRunLog(dir);
  check('runlog-appends', rows.length === 4, `${rows.length} 行`);
  check('runlog-keeps-state', rows[3].state === 'failed' && rows[3].stage === 'segment');
  const s = summarize(rows, {state: 'ok'});
  check('runlog-median-total', s.total.median === 130, JSON.stringify(s.total));
  check('runlog-median-bundle', s.stages.bundle.median === 20, JSON.stringify(s.stages.bundle));
  check('runlog-failed-excluded', s.stages.segments.n === 3, JSON.stringify(s.stages.segments));
  const all = summarize(rows, {state: 'all'});
  check('runlog-all-includes-failure', all.runs === 4 && all.stages.bundle.n === 4, JSON.stringify(all.stages.bundle));
  check('runlog-format-mentions-median', formatSummary(s).includes('中位'), formatSummary(s).split('\n')[0]);

  // 损坏行不能让整份日志作废
  fs.appendFileSync(path.join(dir, 'renders/render-log.jsonl'), '{坏行\n');
  check('runlog-survives-broken-line', readRunLog(dir).length === 4);
  fs.rmSync(dir, {recursive: true, force: true});
}

const failed = checks.filter((c) => !c.pass);
console.log(JSON.stringify({ok: failed.length === 0, total: checks.length, failed}, null, 1));
process.exit(failed.length ? 1 : 0);
