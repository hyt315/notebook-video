// render_ops_probe.mjs · 用 node 直接验证 render-log.mjs / fx-pipeline.mjs 的行为。
// 两个模块都不 import Remotion，所以可以在没有 node_modules 的环境里跑。
// 输出一行 JSON：{ok, checks:[{name, pass, detail}]}

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const mods = process.env.NV_SCRIPTS;
const {classifyExit, appendRunLog, readRunLog, summarize, formatSummary} = await import(
  'file://' + path.join(mods, 'render-log.mjs').replace(/\\/g, '/')
);
const {runFxPipeline, pruneFxTemp, FxStageError, FX_TMP_PREFIX} = await import(
  'file://' + path.join(mods, 'fx-pipeline.mjs').replace(/\\/g, '/')
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

// ---- 3. 卷页管线：成功清场、失败留场并点名阶段 ------------------------------
const runPipeline = async ({failAt, windows = [[10, 31], [40, 61]]}) => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), FX_TMP_PREFIX));
  const fastRaw = path.join(tmpDir, 'fast.mp4');
  fs.writeFileSync(fastRaw, 'fake');
  const calls = {bundle: 0, segments: [], splice: 0, tag: 0};
  const boom = (stage) => { throw new Error(`模拟 ${stage} 失败`); };
  let error = null;
  let result = null;
  try {
    result = await runFxPipeline({
      windows, tmpDir, fastRaw, raw: path.join(tmpDir, 'raw.mp4'),
      bundle: async () => { calls.bundle += 1; if (failAt === 'bundle') boom('bundle'); fs.mkdirSync(path.join(tmpDir, 'curl-bundle')); },
      renderSegment: async (a, b, seg) => { if (failAt === 'segment' && calls.segments.length === 1) boom('segment'); calls.segments.push([a, b]); fs.writeFileSync(seg, 'x'); },
      splice: async () => { calls.splice += 1; if (failAt === 'splice') boom('splice'); },
      tag: async () => { calls.tag += 1; if (failAt === 'tag') boom('tag'); },
      log: () => {},
    });
  } catch (e) {
    error = e;
  }
  return {error, result, calls, tmpDir, exists: fs.existsSync(tmpDir)};
};

{
  const ok = await runPipeline({failAt: null});
  check('pipeline-success', ok.error === null, ok.error && ok.error.message);
  check('pipeline-bundle-once', ok.calls.bundle === 1, `bundle ${ok.calls.bundle}`);
  check('pipeline-all-segments', ok.calls.segments.length === 2, JSON.stringify(ok.calls.segments));
  check('pipeline-timings', ok.result && ok.result.timings.bundleCount === 1
    && ok.result.timings.segmentsMs.length === 2 && ok.result.timings.windows === 2,
    JSON.stringify(ok.result && ok.result.timings));
  check('pipeline-success-cleans-tmp', ok.exists === false, ok.tmpDir);
  fs.rmSync(ok.tmpDir, {recursive: true, force: true});
}

for (const [stage, expectSegments] of [['bundle', 0], ['segment', 1], ['splice', 2], ['tag', 2]]) {
  const r = await runPipeline({failAt: stage});
  check(`pipeline-${stage}-stage-tag`, r.error instanceof FxStageError && r.error.stage === stage,
    r.error ? `${r.error.name}/${r.error.stage}: ${r.error.message}` : 'no error');
  check(`pipeline-${stage}-keeps-scene`, r.exists === true, r.tmpDir);
  check(`pipeline-${stage}-progress`, r.calls.segments.length === expectSegments,
    `已完成 ${r.calls.segments.length} 段`);
  const report = r.error && r.error.toReport({tmpDir: r.tmpDir});
  check(`pipeline-${stage}-report-has-path`, Boolean(report) && report.includes(r.tmpDir), report);
  fs.rmSync(r.tmpDir, {recursive: true, force: true});
}

{
  // 明确关掉保留策略时要立刻清场
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), FX_TMP_PREFIX));
  let threw = false;
  try {
    await runFxPipeline({
      windows: [[1, 2]], tmpDir, fastRaw: path.join(tmpDir, 'f.mp4'), raw: path.join(tmpDir, 'r.mp4'),
      bundle: async () => { throw new Error('x'); },
      renderSegment: async () => {}, splice: async () => {},
      retainOnFailure: false, log: () => {},
    });
  } catch { threw = true; }
  check('pipeline-retain-opt-out', threw && fs.existsSync(tmpDir) === false, tmpDir);
  fs.rmSync(tmpDir, {recursive: true, force: true});
}

// ---- 4. 保留策略：过期清、新鲜留 -------------------------------------------
{
  const dir = tmp();
  const old = path.join(dir, `${FX_TMP_PREFIX}old`);
  const fresh = path.join(dir, `${FX_TMP_PREFIX}fresh`);
  const other = path.join(dir, 'unrelated');
  for (const p of [old, fresh, other]) fs.mkdirSync(p);
  const oldTime = (Date.now() - 30 * 3600_000) / 1000;
  fs.utimesSync(old, oldTime, oldTime);
  const r = pruneFxTemp({dir, keepHours: 24});
  check('prune-removes-old', r.removed.length === 1 && !fs.existsSync(old), JSON.stringify(r.removed));
  check('prune-keeps-fresh', r.kept.length === 1 && fs.existsSync(fresh), JSON.stringify(r.kept));
  check('prune-ignores-unrelated', fs.existsSync(other));
  fs.rmSync(dir, {recursive: true, force: true});
}

const failed = checks.filter((c) => !c.pass);
console.log(JSON.stringify({ok: failed.length === 0, total: checks.length, failed}, null, 1));
process.exit(failed.length ? 1 : 0);
