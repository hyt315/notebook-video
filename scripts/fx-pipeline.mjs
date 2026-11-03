// ============================================================================
// fx-pipeline.mjs · 卷页片段管线：分段执行 + 失败现场保留策略（P1-14）
//
// 现状（改造前）：`render` 里把「打包 → 逐段渲染 → 拼接 → 打色彩标记」写成一段
// 直线代码。任何一步失败都是同一个后果：抛错、进程退出，临时目录里留着
// `fast.mp4 + curl-bundle/ + curl-*.mp4`（实测一次几百 MB）。连续失败几次就能把
// 系统盘塞满，而且错误信息不说是哪一步、现场在哪。
//
// 这里把这段抽出来，目的只有一个：**让失败可定位、可控地占盘**。
//   · 每一步包一层 stage，错误信息里带阶段名和"已完成的进度"（打到第几段）；
//   · 成功 → 立刻删临时目录；
//   · 失败 → 保留现场并返回路径（能复现、能查），由 pruneFxTemp 在保留期后清；
//   · 每次启动先 prune 一次，所以"连续失败"不会无限累积。
//
// 不在这里判断"要不要重试"：重试策略属于调用方，这里只负责执行与收尾。
// ============================================================================

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

export const FX_TMP_PREFIX = 'nv-fx-';
export const FX_RETAIN_HOURS = 24;

export const FX_STAGE = {
  bundle: 'bundle',
  segment: 'segment',
  splice: 'splice',
  tag: 'tag',
};

export class FxStageError extends Error {
  constructor(stage, message, {cause = null, detail = ''} = {}) {
    super(message);
    this.name = 'FxStageError';
    this.stage = stage;
    this.detail = String(detail || '');
    this.cause = cause;
  }

  /** 给用户看的多行说明：阶段 + 已完成进度 + 现场路径 + 下一步。 */
  toReport({tmpDir = null} = {}) {
    const lines = [`卷页渲染在「${this.stage}」阶段失败：${this.message}`];
    if (this.detail) lines.push(this.detail);
    if (tmpDir) lines.push(`失败现场保留在：${tmpDir}（${FX_RETAIN_HOURS} 小时内不会被自动清理，可据此复现）`);
    if (this.stage === FX_STAGE.splice) lines.push('整片快速版已经渲完：修好拼接参数后重跑即可，不必重渲整片。');
    if (this.stage === FX_STAGE.segment) lines.push('已经渲好的片段仍在现场目录里；重跑会重新打包并覆盖同名片段。');
    return lines.join('\n');
  }
}

const rmDir = (dir) => {
  try {
    fs.rmSync(dir, {recursive: true, force: true, maxRetries: 5, retryDelay: 120});
    return true;
  } catch {
    return false;
  }
};

/**
 * 清理过期的卷页临时目录。
 * 保留期内的目录**不能**删：那是刚失败、用户还没看过的现场。
 */
export const pruneFxTemp = ({dir = os.tmpdir(), keepHours = FX_RETAIN_HOURS, now = Date.now(), log = () => {}} = {}) => {
  let names = [];
  try { names = fs.readdirSync(dir); } catch { return {removed: [], kept: []}; }
  const removed = [];
  const kept = [];
  for (const name of names) {
    if (!name.startsWith(FX_TMP_PREFIX)) continue;
    const abs = path.join(dir, name);
    let st;
    try { st = fs.statSync(abs); } catch { continue; }
    if (!st.isDirectory()) continue;      // nv-fx-probe-*.png 之类同前缀的文件不是这里的
    if (now - st.mtimeMs < keepHours * 3600_000) {
      kept.push(abs);
      continue;
    }
    if (rmDir(abs)) removed.push(abs);
  }
  if (removed.length) log(`清理了 ${removed.length} 个超过 ${keepHours} 小时的卷页临时目录`);
  return {removed, kept};
};

/**
 * 执行卷页管线。依赖全部注入，所以可以在不装 Remotion 的环境里测"失败怎么收尾"。
 *
 * @returns {{ok:true, timings:object, segs:string[]}}
 * @throws {FxStageError}
 */
export const runFxPipeline = async ({
  windows, tmpDir, fastRaw, raw,
  bundle, renderSegment, splice, tag = null,
  retainOnFailure = true,
  log = () => {},
} = {}) => {
  const timings = {bundleMs: 0, segmentsMs: [], spliceMs: 0, tagMs: 0, bundleCount: 0, windows: windows.length};
  let ok = false;
  try {
    let t0 = Date.now();
    try {
      await bundle();
    } catch (e) {
      throw new FxStageError(FX_STAGE.bundle, '卷页片段打包失败（尚未开始片段渲染）', {cause: e, detail: String(e && e.message ? e.message : e)});
    }
    timings.bundleMs = Date.now() - t0;
    timings.bundleCount = 1;
    log(`打包完成 ${(timings.bundleMs / 1000).toFixed(1)}s（供 ${windows.length} 段共用）`);

    const segs = [];
    for (const [a, b] of windows) {
      const seg = path.join(tmpDir, `curl-${a}.mp4`);
      t0 = Date.now();
      try {
        await renderSegment(a, b, seg);
      } catch (e) {
        throw new FxStageError(FX_STAGE.segment, `卷页片段 ${a}-${b} 渲染失败（已完成 ${segs.length}/${windows.length} 段）`, {
          cause: e, detail: `已完成：${segs.map((s) => path.basename(s)).join(', ') || '无'}`,
        });
      }
      const ms = Date.now() - t0;
      timings.segmentsMs.push({window: [a, b], ms});
      segs.push(seg);
      log(`片段 ${a}-${b} 完成 ${(ms / 1000).toFixed(1)}s`);
    }

    t0 = Date.now();
    try {
      await splice(fastRaw, segs, raw);
    } catch (e) {
      throw new FxStageError(FX_STAGE.splice, '卷页拼接失败（整片快速版还在现场，可直接重试拼接）', {cause: e, detail: String(e && e.message ? e.message : e)});
    }
    timings.spliceMs = Date.now() - t0;
    log(`拼接完成 ${(timings.spliceMs / 1000).toFixed(1)}s`);

    if (tag) {
      t0 = Date.now();
      try {
        await tag(raw);
      } catch (e) {
        throw new FxStageError(FX_STAGE.tag, '色彩标记写入失败（画面已拼好，重跑这一步即可）', {cause: e, detail: String(e && e.message ? e.message : e)});
      }
      timings.tagMs = Date.now() - t0;
    }
    ok = true;
    return {ok: true, timings, segs};
  } finally {
    // 成功即删；失败按保留策略留着（调用方会把路径打进错误信息）
    if (ok || !retainOnFailure) rmDir(tmpDir);
  }
};
