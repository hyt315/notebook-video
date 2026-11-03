// ============================================================================
// render-lock.mjs · 同工程渲染锁 + raw 内容指纹
//
// 为什么有这个东西（P0-04）：
//   raw 路径由「工程 + 分辨率 + 合成 + 是否 GPU 卷页」决定，是个**稳定**路径——这样失败后能续跑。
//   但稳定路径也意味着两个进程可以同时写同一个文件：后一个把前一个的产物覆盖，或者把别人任务的
//   半成品当成品交付。以前只有「--resume 时比一下 mtime」，既挡不住并发，也分不清「raw 完整」和
//   「raw 写到一半」。
//
// 这里只做三件事，全部可单测（不依赖 Remotion）：
//   1. acquireRenderLock：同 key 只允许一个活着的进程；持有者已死 → 明确接管并说明。
//   2. inputFingerprint：对 src / public / audio / manifests / story.json 做**内容**哈希，
//      不是只看最新 mtime。输入变了，指纹就变，旧 raw 不会被误当新片。
//   3. manifest：raw 旁边写一份 JSON（指纹、参数、pid、状态），resume 只认 state=raw-complete。
// ============================================================================

import {createHash} from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

export const FINGERPRINT_DIRS = ['src', 'public', 'audio', 'manifests'];
export const FINGERPRINT_FILES = ['story.json'];
export const MANIFEST_SCHEMA = 1;

/** 收集工程里会影响画面/声音的文件（相对路径，正斜杠，已排序）。 */
export const fingerprintFiles = (project) => {
  const out = [];
  const walk = (abs) => {
    let st;
    try { st = fs.statSync(abs); } catch { return; }
    if (st.isDirectory()) {
      for (const name of fs.readdirSync(abs).sort()) walk(path.join(abs, name));
      return;
    }
    if (st.isFile()) out.push(abs);
  };
  for (const rel of FINGERPRINT_DIRS) walk(path.join(project, rel));
  for (const rel of FINGERPRINT_FILES) {
    const abs = path.join(project, rel);
    if (fs.existsSync(abs)) out.push(abs);
  }
  return out.map((abs) => path.relative(project, abs).replace(/\\/g, '/')).sort();
};

/**
 * 内容指纹：文件路径 + 内容全进哈希。
 * 不用 mtime：`git checkout`、拷贝工程、时钟回拨都会让 mtime 说谎，而内容没变；
 * 反过来，同一秒内改两次内容，mtime 也不会变。
 */
export const inputFingerprint = (project, files = fingerprintFiles(project)) => {
  const h = createHash('sha256');
  for (const rel of files) {
    h.update(rel);
    h.update('\0');
    try {
      h.update(fs.readFileSync(path.join(project, rel)));
    } catch {
      h.update('<unreadable>');
    }
    h.update('\0');
  }
  return h.digest('hex').slice(0, 16);
};

export const lockPathFor = (key) => path.join(os.tmpdir(), `nv-render-${key}.lock`);
export const manifestPathFor = (rawPath) => rawPath.replace(/\.mp4$/i, '') + '.render.json';
/** 工程级 key：同一工程的两个 render 会互相踩（sync 会写工程文件），所以锁按工程取，不按 raw 取。 */
export const projectKeyFor = (project) => createHash('sha1').update(String(project)).digest('hex').slice(0, 12);

const pidAlive = (pid) => {
  if (!Number.isInteger(pid) || pid <= 0) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch (e) {
    // EPERM = 进程存在但不属于我们（仍算活着，不能抢）
    return e && e.code === 'EPERM';
  }
};

/**
 * 取锁。返回 {ok:true, release(), tookOver:boolean} 或 {ok:false, holder}。
 * 持有者进程已死 = 上次崩溃留下的锁 → 接管，但把这件事说出来，不静默覆盖。
 */
export const acquireRenderLock = (lockPath, meta = {}, opts = {}) => {
  const payload = JSON.stringify({...meta, pid: process.pid, startedAt: new Date().toISOString()}, null, 2);
  const tryCreate = () => {
    const fd = fs.openSync(lockPath, 'wx');
    fs.writeSync(fd, payload);
    fs.closeSync(fd);
  };
  try {
    tryCreate();
    return {ok: true, tookOver: false, release: () => releaseLock(lockPath)};
  } catch (e) {
    if (e.code !== 'EEXIST') throw e;
  }
  let holder = null;
  try {
    holder = JSON.parse(fs.readFileSync(lockPath, 'utf8'));
  } catch {
    holder = null;                       // 锁文件损坏：当作死锁处理
  }
  if (holder && pidAlive(holder.pid) && holder.pid !== process.pid) {
    return {ok: false, holder};
  }
  // 持有者已死（或锁文件损坏、或就是本进程上次没清）：接管
  try { fs.rmSync(lockPath, {force: true}); } catch { /* 竞态里被别人删了也无所谓 */ }
  try {
    tryCreate();
    return {ok: true, tookOver: Boolean(holder), release: () => releaseLock(lockPath)};
  } catch (e) {
    if (e.code === 'EEXIST') {
      try { holder = JSON.parse(fs.readFileSync(lockPath, 'utf8')); } catch { holder = null; }
      return {ok: false, holder};
    }
    throw e;
  }
};

export const releaseLock = (lockPath) => {
  try {
    const holder = JSON.parse(fs.readFileSync(lockPath, 'utf8'));
    if (holder.pid !== process.pid) return;    // 不是自己的锁，别删
  } catch {
    return;
  }
  fs.rmSync(lockPath, {force: true});
};

export const readManifest = (manifestPath) => {
  try {
    const doc = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    return doc && doc.schema === MANIFEST_SCHEMA ? doc : null;
  } catch {
    return null;
  }
};

export const writeManifest = (manifestPath, patch) => {
  const prev = readManifest(manifestPath) || {};
  const doc = {...prev, schema: MANIFEST_SCHEMA, ...patch, updatedAt: new Date().toISOString()};
  fs.writeFileSync(manifestPath, JSON.stringify(doc, null, 2));
  return doc;
};

/**
 * resume 判定。**只认完整 raw**：manifest.state === 'raw-complete' 且指纹一致。
 * 没有 manifest 的旧 raw 一律不复用——分不清它是完整的还是写了一半的。
 * 返回 {resume:boolean, reason:string}
 */
export const canResume = ({manifest, fingerprint, rawExists}) => {
  if (!rawExists) return {resume: false, reason: 'raw 不存在'};
  if (!manifest) return {resume: false, reason: '没有 render manifest（旧 raw 无法证明完整）'};
  if (manifest.state !== 'raw-complete') return {resume: false, reason: `raw 状态是 ${manifest.state ?? '未知'}`};
  if (manifest.fingerprint !== fingerprint) return {resume: false, reason: '输入内容已变（指纹不同）'};
  return {resume: true, reason: '输入与参数一致，raw 完整'};
};
