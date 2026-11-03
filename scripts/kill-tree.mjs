/**
 * kill-tree.mjs — 连子进程树一起结束（P1-14）
 *
 * 为什么需要单独一个文件：`child.kill('SIGKILL')` 在 Windows 上是 TerminateProcess，
 * 只结束**直接子进程**；它再拉起的进程（Remotion 的 Chrome Headless、ffmpeg、分段渲染的子 node）
 * 会原地变成孤儿，继续占内存与工程文件。POSIX 上同理：只杀父进程，孙进程会被 init 收养成孤儿。
 *
 * 所以两端都按「树」来杀：
 *   Windows → `taskkill /PID <pid> /T /F`（/T 是整棵树）
 *   POSIX   → 先用 `ps -A -o pid=,ppid=` 枚举后代，从最深的一层往上 SIGKILL，最后杀父进程。
 *             不走 `kill(-pid)`：那要求子进程以 detached 启动，而 detached 之后终端里的
 *             Ctrl+C 也收不到它——为了杀干净反而先造出孤儿，不划算。
 *             进程组 kill 保留为枚举失败时的退路。
 *
 * 这里不判断「该不该杀」——只负责「杀干净」。超时/停滞/任务失败的判据在调用方。
 */
import {spawnSync} from 'node:child_process';

/** 枚举 rootPid 的全部后代，父在子之后（即从深到浅）。 */
const descendantsOf = (rootPid) => {
  // `ps -A -o pid=,ppid=` 在 Linux 与 macOS 上都能用（BSD ps 支持 -o 与 '=' 后缀）。
  const r = spawnSync('ps', ['-A', '-o', 'pid=,ppid='], {encoding: 'utf8', windowsHide: true});
  if (r.status !== 0 || !r.stdout) return [];
  const kids = new Map();
  for (const line of r.stdout.split('\n')) {
    const m = line.trim().split(/\s+/);
    if (m.length < 2) continue;
    const pid = Number(m[0]);
    const ppid = Number(m[1]);
    if (!Number.isFinite(pid) || !Number.isFinite(ppid)) continue;
    if (!kids.has(ppid)) kids.set(ppid, []);
    kids.get(ppid).push(pid);
  }
  const out = [];
  const walk = (p) => {
    for (const c of kids.get(p) ?? []) {
      walk(c);          // 先把孙子收进来
      out.push(c);      // 再收儿子 —— 保证从深到浅
    }
  };
  walk(rootPid);
  return out;
};

/**
 * @param {{pid?: number, kill?: (signal?: string) => boolean}} child spawn 返回的 ChildProcess
 * @param {{tree?: boolean}} [opts] tree=false 时只杀自己（用于已经自己退出的进程）
 * @returns {'taskkill'|'tree'|'group'|'single'|'none'} 实际用了哪种方式（测试与日志用）
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
    const descendants = descendantsOf(pid);
    if (descendants.length) {
      for (const p of descendants) {
        try { process.kill(p, 'SIGKILL'); } catch { /* 已经退出 */ }
      }
      try { child.kill?.('SIGKILL'); } catch { /* 已经退出 */ }
      return 'tree';
    }
    try {
      process.kill(-pid, 'SIGKILL');   // 退路：子进程恰好是进程组组长时一次收全组
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
