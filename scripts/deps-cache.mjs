// SPDX-License-Identifier: Apache-2.0
// 跨工程依赖与资源复用：按锁文件哈希共享 node_modules、npm 缓存与字体目录，避免反复下载与重复占盘。
import {createHash} from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';

const CACHE_APP_DIR = 'notebook-video';
const LOCK_STALE_MS = 15 * 60 * 1000;
const LOCK_WAIT_MS = 5 * 60 * 1000;
const sleepSync = (ms) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);

export function userCacheRoot(env = process.env) {
  if (env.NOTEBOOK_VIDEO_CACHE_DIR) return path.resolve(env.NOTEBOOK_VIDEO_CACHE_DIR);
  if (process.platform === 'win32') {
    const base = env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local');
    return path.join(base, CACHE_APP_DIR);
  }
  if (process.platform === 'darwin') {
    return path.join(os.homedir(), 'Library', 'Caches', CACHE_APP_DIR);
  }
  const base = env.XDG_CACHE_HOME || path.join(os.homedir(), '.cache');
  return path.join(base, CACHE_APP_DIR);
}

export function sharedNpmCacheDir(env = process.env) {
  return env.NOTEBOOK_VIDEO_NPM_CACHE ? path.resolve(env.NOTEBOOK_VIDEO_NPM_CACHE) : path.join(userCacheRoot(env), 'npm-cache');
}

export function sharedFontsDir(env = process.env) {
  return path.join(userCacheRoot(env), 'fonts');
}

export function fileSha256(filePath) {
  return createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

function sameResolvedPath(a, b) {
  try {
    return path.resolve(fs.realpathSync(a)) === path.resolve(fs.realpathSync(b));
  } catch {
    return path.resolve(a) === path.resolve(b);
  }
}

function removeEmptyOrBrokenLink(linkPath) {
  let st;
  try {
    st = fs.lstatSync(linkPath);
  } catch {
    return true;
  }
  if (st.isSymbolicLink()) {
    try {
      fs.rmdirSync(linkPath);
    } catch {
      fs.unlinkSync(linkPath);
    }
    return true;
  }
  if (st.isDirectory()) {
    if (fs.readdirSync(linkPath).length === 0) {
      fs.rmdirSync(linkPath);
      return true;
    }
    return false;
  }
  return false;
}

export function linkDirectory(targetDir, linkPath) {
  try {
    if (!fs.existsSync(targetDir)) return false;
    if (!removeEmptyOrBrokenLink(linkPath)) return false;
    fs.mkdirSync(path.dirname(linkPath), {recursive: true});
    fs.symlinkSync(path.resolve(targetDir), linkPath, process.platform === 'win32' ? 'junction' : 'dir');
    return fs.existsSync(linkPath);
  } catch {
    return false;
  }
}

async function withDirLock(lockFile, fn) {
  fs.mkdirSync(path.dirname(lockFile), {recursive: true});
  const start = Date.now();
  while (true) {
    try {
      const fd = fs.openSync(lockFile, 'wx');
      try {
        fs.writeFileSync(fd, String(process.pid));
        return await fn();
      } finally {
        try { fs.closeSync(fd); } catch {}
        try { fs.unlinkSync(lockFile); } catch {}
      }
    } catch (err) {
      if (err?.code !== 'EEXIST') throw err;
      try {
        const st = fs.statSync(lockFile);
        if (Date.now() - st.mtimeMs > LOCK_STALE_MS) {
          fs.unlinkSync(lockFile);
          continue;
        }
      } catch {
        continue;
      }
      if (Date.now() - start > LOCK_WAIT_MS) throw err;
      sleepSync(150);
    }
  }
}

/**
 * 为工程准备 node_modules：
 * 1. 已有可用依赖则直接复用；
 * 2. 匹配同 package-lock.json 哈希的缓存或模板依赖并用目录链接复用；
 * 3. 没有则装入用户级共享缓存一次再链接给工程，不可链接时平滑回退到工程本地安装。
 */
export async function ensureProjectNodeModules(project, {
  skillDir = null,
  runNpm,
  verifyRel = path.join('@remotion', 'cli', 'remotion-cli.js'),
  env = process.env,
  log = console.log,
} = {}) {
  const projectNm = path.join(project, 'node_modules');
  const projectVerify = path.join(projectNm, verifyRel);
  if (fs.existsSync(projectVerify)) return {mode: 'existing', target: projectNm};

  const lockPath = path.join(project, 'package-lock.json');
  const pkgPath = path.join(project, 'package.json');
  if (env.NOTEBOOK_VIDEO_SHARED_DEPS === '0' || !fs.existsSync(lockPath) || !fs.existsSync(pkgPath)) {
    await runNpm(['ci', '--no-audit', '--no-fund'], {cwd: project});
    return {mode: 'local', target: projectNm};
  }

  const lockHash = fileSha256(lockPath).slice(0, 16);
  const sharedDir = path.join(userCacheRoot(env), 'deps', lockHash);
  const candidates = [sharedDir];
  if (skillDir) candidates.push(path.join(skillDir, 'assets', 'lecture-template'));

  for (const cand of candidates) {
    if (!cand || sameResolvedPath(cand, project)) continue;
    const candLock = path.join(cand, 'package-lock.json');
    const candNm = path.join(cand, 'node_modules');
    const candVerify = path.join(candNm, verifyRel);
    if (!fs.existsSync(candLock) || !fs.existsSync(candVerify)) continue;
    if (fileSha256(candLock).slice(0, 16) !== lockHash) continue;
    if (linkDirectory(candNm, projectNm) && fs.existsSync(projectVerify)) {
      log(`复用已有依赖（lock ${lockHash.slice(0, 8)}）：${candNm}`);
      return {mode: 'linked', target: candNm, lockHash};
    }
  }

  try {
    const sharedNm = path.join(sharedDir, 'node_modules');
    const sharedVerify = path.join(sharedNm, verifyRel);
    const sharedLock = path.join(sharedDir, 'package-lock.json');
    await withDirLock(`${sharedDir}.lock`, async () => {
      if (fs.existsSync(sharedVerify) && fs.existsSync(sharedLock) && fileSha256(sharedLock).slice(0, 16) === lockHash) return;
      fs.mkdirSync(sharedDir, {recursive: true});
      fs.copyFileSync(pkgPath, path.join(sharedDir, 'package.json'));
      fs.copyFileSync(lockPath, sharedLock);
      await runNpm(['ci', '--no-audit', '--no-fund'], {cwd: sharedDir});
    });
    if (fs.existsSync(sharedVerify) && linkDirectory(sharedNm, projectNm) && fs.existsSync(projectVerify)) {
      log(`依赖已缓存并复用（lock ${lockHash.slice(0, 8)}）：${sharedNm}`);
      return {mode: 'installed-shared', target: sharedNm, lockHash};
    }
  } catch {
    // 共享目录无写权限或文件系统不支持目录链接时，优雅回退到当前工程本地安装。
  }

  await runNpm(['ci', '--no-audit', '--no-fund'], {cwd: project});
  return {mode: 'local-fallback', target: projectNm};
}
