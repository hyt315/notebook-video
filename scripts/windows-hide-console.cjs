// windows-hide-console.cjs · Windows 上不让子进程闪出控制台窗口（3.3.0）
//
// 为什么要它：
//   Remotion 的 @remotion/renderer 拉浏览器、收尾杀浏览器时**从不**设 windowsHide：
//     · node_modules/@remotion/renderer/dist/browser/BrowserRunner.js:82
//         childProcess.spawn(launch.executablePath, launch.args, {detached, env, stdio})   ← 没 windowsHide
//     · node_modules/@remotion/renderer/dist/browser/BrowserRunner.js:106
//         childProcess.exec(`taskkill /pid ${proc.pid} /T /F`)                              ← 没 windowsHide
//   而在 Windows 上 `child_process.exec` 固定经 cmd.exe /d /s /c 启动 —— 于是每关一次浏览器
//   就闪一个 CMD 窗口。静帧模式逐帧起进程（26 帧 = 26 次开关 = 26 次闪），整片渲染更多。
//   实测抓到的命令行：cmd.exe /d /s /c "taskkill /pid 18280 /T /F"
//   （chrome-headless-shell.exe 的 PE 子系统也是 CONSOLE，同样会带控制台。）
//
// 怎么修：
//   不改 node_modules（重装依赖就没了），改成用 node --require 预加载本文件，
//   在 Remotion 进程启动时把 child_process 的 spawn / exec / execFile 包一层，
//   强制补上 windowsHide: true。child_process 是单例模块，`require('node:child_process')`
//   与 `require('child_process')` 拿到同一个对象，所以 patch 对 Remotion 生效。
//
// 用法：node --require <此文件> <remotion-cli.js> render|still ...
//   由 scripts/notebook-video.mjs 与 scripts/make-video.mjs 自动加上，用户不用管。

'use strict';

const childProcess = require('node:child_process');

// 只在 Windows 上动手：POSIX 没有控制台窗口这回事。
if (process.platform === 'win32') {
  // Node 内部实现里 exec → execFile → spawn 会层层转调。若每一层都重新包装 options，
  // 参数位就会被搞乱（实测 exec(cmd, cb) 会把 options 当成 callback 传给 execFile，
  // 报 ERR_INVALID_ARG_TYPE）。
  // 解法：用内部 Symbol 标记「这份 options 本 shim 已处理过」，下游层看到标记就直接放行。
  const HANDLED = Symbol('nvWindowsHideHandled');
  const mark = (options) => {
    if (!options || typeof options !== 'object') return options;
    if (options.windowsHide === true) return options;
    const next = {...options, windowsHide: true};
    Object.defineProperty(next, HANDLED, {value: true, enumerable: false});
    return next;
  };

  const originalSpawn = childProcess.spawn;
  childProcess.spawn = function spawn(command, args, options) {
    return originalSpawn.call(this, command, args, mark(options));
  };

  const originalSpawnSync = childProcess.spawnSync;
  childProcess.spawnSync = function spawnSync(command, args, options) {
    return originalSpawnSync.call(this, command, args, mark(options));
  };

  const originalExec = childProcess.exec;
  childProcess.exec = function exec(command, options, callback) {
    // exec 有两种签名：exec(cmd, cb) 与 exec(cmd, options, cb)
    if (typeof options === 'function') {
      return originalExec.call(this, command, mark({}), options);
    }
    return originalExec.call(this, command, mark(options), callback);
  };

  const originalExecSync = childProcess.execSync;
  childProcess.execSync = function execSync(command, options) {
    return originalExecSync.call(this, command, mark(options));
  };

  // execFile **不要**包。
  // 原因：Node 内部实现里 exec 会转调 execFile(cmd, args, options, cb)，而那个转调
  // 走的是模块内部的原始 execFile 引用 —— 但它命中的是我们挂在 childProcess 上的
  // 这个属性（内部实现读的就是 childProcess.execFile）。一旦我们包了它，
  // exec 传下来的 (cmd, args, options, cb) 会被我们的签名判断误判成
  // (file, args=options对象, options=cb) → callback 位收到对象 → ERR_INVALID_ARG_TYPE。
  // 既然 exec 最终会落到 spawn，而 spawn 已经带上了 windowsHide，这里不动 execFile。
  //
  // execFile 的独立调用（Remotion 没用到）保持原样即可。
}
