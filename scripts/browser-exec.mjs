// Remotion 浏览器解析：环境变量优先，其次用本机已有缓存，都没有才让 Remotion 自己下载。
// 抽成模块是为了让 make-video 的静帧与 notebook-video 的渲染/预览共用同一套解析——
// 以前 make-video 不传 --browser-executable，于是明明本机已有缓存它还要再下一个。
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const WIN_CACHE = () =>
  path.join(process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local'),
    'remotion-browser', 'chrome-headless-shell', 'win64', 'chrome-headless-shell.exe');

/** 返回可执行文件绝对路径；都没有返回 null（Remotion 会自己下载）。 */
export function resolveBrowserExecutable(resolvePath = (p) => path.resolve(process.cwd(), p)) {
  const browserExecutable = process.env.REMOTION_BROWSER_EXECUTABLE;
  if (browserExecutable) {
    const resolved = resolvePath(browserExecutable);
    // 3.5.2：补回 3.5.0 的存在性检查——指错路径要明确报错，不能把坏路径交给 Remotion
    if (!fs.existsSync(resolved)) throw new Error(`REMOTION_BROWSER_EXECUTABLE does not exist: ${resolved}`);
    return resolved;
  }
  if (process.platform === 'win32') {
    const cached = WIN_CACHE();
    if (fs.existsSync(cached)) return cached;
  }
  return null;
}

/** 直接给 CLI 用的参数：找到就带 --browser-executable，找不到就空数组。 */
export function browserArgs(resolvePath = (p) => path.resolve(process.cwd(), p)) {
  const exe = resolveBrowserExecutable(resolvePath);
  return exe ? [`--browser-executable=${exe}`] : [];
}
