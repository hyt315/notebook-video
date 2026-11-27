// SPDX-License-Identifier: Apache-2.0
// 浏览器解析：环境变量优先，其次扫描本机标准目录中已缓存的无头渲染浏览器，都没有才交由 Remotion 下载一次。
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import {fileURLToPath} from 'node:url';
import {userCacheRoot} from './deps-cache.mjs';

const SKILL_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

function headlessShellPlatformParts() {
  if (process.platform === 'win32') return [['win64', 'chrome-headless-shell.exe']];
  if (process.platform === 'darwin') {
    return process.arch === 'arm64'
      ? [['mac-arm64', 'chrome-headless-shell'], ['mac-x64', 'chrome-headless-shell']]
      : [['mac-x64', 'chrome-headless-shell'], ['mac-arm64', 'chrome-headless-shell']];
  }
  return process.arch === 'arm64'
    ? [['linux-arm64', 'chrome-headless-shell'], ['linux64', 'chrome-headless-shell']]
    : [['linux64', 'chrome-headless-shell'], ['linux-arm64', 'chrome-headless-shell']];
}

function osStandardCacheRoots(env = process.env) {
  if (process.platform === 'win32') {
    return [env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local')];
  }
  if (process.platform === 'darwin') {
    return [path.join(os.homedir(), 'Library', 'Caches')];
  }
  return [env.XDG_CACHE_HOME || path.join(os.homedir(), '.cache')];
}

function listSubdirsSortedNewest(dir) {
  try {
    return fs.readdirSync(dir, {withFileTypes: true})
      .filter((e) => e.isDirectory())
      .map((e) => {
        const full = path.join(dir, e.name);
        try { return {full, name: e.name, mtime: fs.statSync(full).mtimeMs}; } catch { return {full, name: e.name, mtime: 0}; }
      })
      .sort((a, b) => b.mtime - a.mtime);
  } catch {
    return [];
  }
}

function findUnderHeadlessShellRoot(baseDir, platParts) {
  if (!baseDir || !fs.existsSync(baseDir)) return null;
  for (const [plat, exe] of platParts) {
    const direct = path.join(baseDir, plat, exe);
    if (fs.existsSync(direct)) return direct;
  }
  for (const sub of listSubdirsSortedNewest(baseDir).slice(0, 8)) {
    for (const [plat, exe] of platParts) {
      const nested = path.join(sub.full, `chrome-headless-shell-${plat}`, exe);
      if (fs.existsSync(nested)) return nested;
      const flat = path.join(sub.full, plat, exe);
      if (fs.existsSync(flat)) return flat;
    }
  }
  return null;
}

function scanCachedHeadlessShell(env = process.env, skillDir = SKILL_DIR) {
  const platParts = headlessShellPlatformParts();
  const cacheRoot = userCacheRoot(env);
  const directRoots = [
    path.join(cacheRoot, 'browser', 'chrome-headless-shell'),
    ...osStandardCacheRoots(env).map((r) => path.join(r, 'remotion-browser', 'chrome-headless-shell')),
    ...listSubdirsSortedNewest(path.join(cacheRoot, 'deps')).slice(0, 6)
      .map((d) => path.join(d.full, 'node_modules', '.remotion', 'chrome-headless-shell')),
    skillDir ? path.join(skillDir, 'assets', 'lecture-template', 'node_modules', '.remotion', 'chrome-headless-shell') : null,
    path.join(os.homedir(), '.cache', 'puppeteer', 'chrome-headless-shell'),
  ];
  for (const root of directRoots) {
    const hit = findUnderHeadlessShellRoot(root, platParts);
    if (hit) return hit;
  }
  for (const osCache of osStandardCacheRoots(env)) {
    const pwRoot = path.join(osCache, 'ms-playwright');
    for (const sub of listSubdirsSortedNewest(pwRoot).filter((s) => s.name.startsWith('chromium_headless_shell-')).slice(0, 6)) {
      const winExe = path.join(sub.full, 'chrome-headless-shell-win64', 'chrome-headless-shell.exe');
      if (process.platform === 'win32' && fs.existsSync(winExe)) return winExe;
      for (const [plat, exe] of platParts) {
        const cand = path.join(sub.full, `chrome-headless-shell-${plat}`, exe);
        if (fs.existsSync(cand)) return cand;
      }
    }
  }
  return null;
}

/**
 * 解析渲染浏览器与运行模式：{executable, chromeMode}。
 * 1) REMOTION_BROWSER_EXECUTABLE 优先（路径错误直接抛错）；
 * 2) 扫描跨工程共享与操作系统标准缓存中的 chrome-headless-shell；
 * 3) 都没有返回 null，由 Remotion 下载一次。
 */
export function resolveBrowserInfo(resolvePath = (p) => path.resolve(process.cwd(), p), {env = process.env, skillDir = SKILL_DIR} = {}) {
  const browserExecutable = env.REMOTION_BROWSER_EXECUTABLE;
  if (browserExecutable) {
    const resolved = resolvePath(browserExecutable);
    if (!fs.existsSync(resolved)) throw new Error(`REMOTION_BROWSER_EXECUTABLE does not exist: ${resolved}`);
    const base = path.basename(resolved).toLowerCase();
    const explicitMode = env.REMOTION_CHROME_MODE || null;
    const inferredMode = explicitMode || (base.includes('headless-shell') || base.includes('headless_shell') ? null : 'chrome-for-testing');
    return {executable: resolved, chromeMode: inferredMode};
  }
  const cached = scanCachedHeadlessShell(env, skillDir);
  return cached ? {executable: cached, chromeMode: null} : {executable: null, chromeMode: null};
}

/** 返回可执行文件绝对路径；都没有返回 null（Remotion 会自己下载）。 */
export function resolveBrowserExecutable(resolvePath = (p) => path.resolve(process.cwd(), p), opts = {}) {
  return resolveBrowserInfo(resolvePath, opts).executable;
}

/** 直接给 CLI 用的参数：找到就带 --browser-executable（及必要时的 --chrome-mode）。 */
export function browserArgs(resolvePath = (p) => path.resolve(process.cwd(), p), opts = {}) {
  const {executable, chromeMode} = resolveBrowserInfo(resolvePath, opts);
  if (!executable) return [];
  return chromeMode ? [`--browser-executable=${executable}`, `--chrome-mode=${chromeMode}`] : [`--browser-executable=${executable}`];
}
