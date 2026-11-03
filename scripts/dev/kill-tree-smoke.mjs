#!/usr/bin/env node
/**
 * kill-tree-smoke.mjs — 父进程被杀时，孙进程必须一起走（P1-14）
 *
 * 真实现场：render 超时或被 Ctrl+C，`child.kill('SIGKILL')` 只结束直接子进程；
 * 它拉起的 Chrome Headless / ffmpeg 会继续跑，占着内存和工程里的 raw 文件。
 * 下次渲染就会撞上「raw 被占用」或「锁还在」的假故障。
 *
 * 这里起三段真进程：本脚本 → 父（模拟 render）→ 孙（模拟 Chrome），然后用产品代码里的
 * `killTree` 杀父，再确认孙真的死了。不渲染、不联网，1 秒级。
 *
 * 退出码 0 = 孙进程随父一起结束。
 */
import {spawn, spawnSync} from 'node:child_process';
import process from 'node:process';
import {killTree} from '../kill-tree.mjs';

const problems = [];
const say = (ok, msg, detail = '') => {
  if (!ok) problems.push(msg);
  console.log(`  ${ok ? 'OK  ' : 'FAIL'} ${msg}${detail ? `（${detail}）` : ''}`);
};

const alive = (pid) => {
  if (process.platform === 'win32') {
    const r = spawnSync('tasklist', ['/FI', `PID eq ${pid}`, '/NH'], {encoding: 'utf8', windowsHide: true});
    return (r.stdout || '').includes(String(pid));
  }
  try { process.kill(pid, 0); return true; } catch { return false; }
};

// 父进程：再拉一个长睡的孙进程，报告两个 pid，然后自己也不退出
const parentCode = `
const {spawn} = require('node:child_process');
const grandchild = spawn(process.execPath, ['-e', 'setTimeout(() => {}, 60000)'], {stdio: 'ignore'});
console.log(JSON.stringify({parent: process.pid, grandchild: grandchild.pid}));
setTimeout(() => {}, 60000);
`;
const startPair = async () => {
  const parent = spawn(process.execPath, ['-e', parentCode], {stdio: ['ignore', 'pipe', 'ignore'], windowsHide: true});
  const ids = await new Promise((resolve, reject) => {
    let buf = '';
    const timer = setTimeout(() => reject(new Error('父进程 3 秒内没报告 pid')), 3000);
    parent.stdout.on('data', (c) => {
      buf += c.toString();
      const nl = buf.indexOf('\n');
      if (nl >= 0) { clearTimeout(timer); try { resolve(JSON.parse(buf.slice(0, nl))); } catch (e) { reject(e); } }
    });
    parent.on('exit', (code) => { if (code !== 0) reject(new Error(`父进程退出码 ${code}`)); });
  });
  return {parent, ids};
};

// ── 对照组：只 kill 直接子进程（旧行为）。
// 注意：这一组**只记录观察，不算判据**。本机（WorkBuddy 的 shell）把进程放在 Job Object 里，
// 父进程结束时系统会把整棵树一起收掉，所以这里复现不出孤儿；用户从普通终端启动时没有这个 Job，
// 孤儿会留着。硬断言"必须留孤儿"会让带 Job 的环境假红。
{
  const {parent, ids} = await startPair();
  await new Promise((r) => setTimeout(r, 400));
  if (!alive(ids.grandchild)) problems.push(`对照前提不成立：孙进程 ${ids.grandchild} 在杀父前就不在了`);
  try { parent.kill('SIGKILL'); } catch { /* 已退出 */ }
  await new Promise((r) => setTimeout(r, 600));
  console.log(`  ·    对照观察：只 kill 父进程后，孙进程 ${alive(ids.grandchild) ? '仍在（会变孤儿）' : '也没了（本机在 Job Object 里，复现不出孤儿）'}`);
  if (alive(ids.grandchild)) killTree({pid: ids.grandchild});   // 收掉对照组的孤儿
  await new Promise((r) => setTimeout(r, 300));
}

// ── 实验组：产品代码的 killTree
const pair = await startPair();
const pids = pair.ids;
if (pids) {
  // 先确认孙进程确实活着（否则这条测试等于什么都没验）
  await new Promise((r) => setTimeout(r, 200));
  say(alive(pids.grandchild), '前提：孙进程已启动', `pid ${pids.grandchild}`);

  const how = killTree(pair.parent);
  // win32 走 taskkill；POSIX 走 ps 枚举出的后代（'tree'），枚举不到才退回进程组（'group'）。
  // 'single' 不算通过：父进程明明还有孙进程，只杀自己就是留孤儿。
  const expected = process.platform === 'win32' ? ['taskkill'] : ['tree', 'group'];
  say(expected.includes(how), 'killTree 走到了预期分支', `方式 ${how}`);

  await new Promise((r) => setTimeout(r, 600));
  say(!alive(pids.parent), '父进程已结束');
  say(!alive(pids.grandchild), '孙进程随父一起结束（没有留孤儿）');

  // 兜底：万一没死，别把孤儿留在测试机上
  if (alive(pids.grandchild)) killTree({pid: pids.grandchild});
}

console.log(problems.length ? `\nFAILED：${problems.length} 条不成立` : '\nkill-tree smoke PASS');
process.exit(problems.length ? 1 : 0);
