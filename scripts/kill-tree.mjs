/**
 * kill-tree.mjs — 连子进程树一起结束（P1-14）
 *
 * 为什么需要单独一个文件：`child.kill('SIGKILL')` 在 Windows 上是 TerminateProcess，
 * 只结束**直接子进程**；它再拉起的进程（Remotion 的 Chrome Headless、ffmpeg、分段渲染的子 node）
 * 会原地变成孤儿，继续占内存与工程文件。POSIX 上同理：没有进程组的 kill 也留孤儿。
 *
 * 所以两端都按「树」来杀：
 *   Windows → `taskkill /PID <pid> /T /F`（/T 是整棵树）
 *   POSIX   → 子进程以 detached 启动时是进程组组长，`process.kill(-pid)` 一次收全组；
 *             不是组长就退回单进程 kill（调用方拿不到组时这是唯一安全做法）。
 *
 * 这里不判断「该不该杀」——只负责「杀干净」。超时/停滞/任务失败的判据在调用方。
 */
import {spawnSync} from 'node:child_process';

/**
 * @param {{pid?: number, kill?: (signal?: string) => boolean}} child spawn 返回的 ChildProcess
 * @param {{tree?: boolean}} [opts] tree=false 时只杀自己（用于已经自己退出的进程）
 * @returns {'taskkill'|'group'|'single'|'none'} 实际用了哪种方式（测试与日志用）
 */
export const killTree = (child, opts = {}) => {
  const pid = child?.pid;
  const tree = opts.tree !== false;
  if (!pid) return 'none';
  if (tree && process.platform === 'win32') {
    // taskkill 的退出码在「进程已不存在」时非 0，这里不当失败——目标本来就没了。
    const r = spawnSync('taskkill', ['/PID', String(pid), '/T', '/F'], {windowsHide: true, stdio: 'ignore'});
    if (r.status === 0 || r.status === 128 || r.status === 1) return 'taskkill';
    // taskkill 不可用时退回单进程，至少别完全没动作
  }
  if (tree && process.platform !== 'win32') {
    try {
      process.kill(-pid, 'SIGKILL');   // 负 pid = 整个进程组（子进程须以 detached 启动）
      return 'group';
    } catch { /* 不是组长，或已经退出 */ }
  }
  try {
    child.kill?.('SIGKILL');
    return 'single';
  } catch {
    return 'none';
  }
};
