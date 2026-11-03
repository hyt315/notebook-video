#!/usr/bin/env node
/**
 * render-lock-smoke.mjs — 跨进程互斥 smoke（P2-27）
 *
 * 为什么要有它：单元测试（tests/test_render_lock.py）只锁了**同一个进程里**两次取锁的行为，
 * 而真正的风险在跨进程——两个终端同时跑 `render` 会争用同一个 raw 文件。锁文件是不是真的原子、
 * 崩溃残留能不能被接管、释放后能不能再取，这些都只有两个真实 OS 进程才验得出来。
 *
 * 做法（不渲染、不开浏览器，1 秒级）：
 *   1. 父进程 spawn 一个 holder 子进程，取锁后 hold 2 秒再退出；
 *   2. 父进程在 holder 持锁期间取锁 —— 必须失败，且 holder.pid 指向子进程；
 *   3. holder 退出后父进程再取 —— 必须成功（锁随进程结束释放）。
 *
 * 退出码 0 = 三条都对；1 = 有断言不成立（打印实际值）。
 */
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import {acquireRenderLock, lockPathFor, projectKeyFor} from '../render-lock.mjs';

const HOLD_MS = 2000;
const problems = [];
const ok = (cond, msg, detail = '') => {
  if (!cond) problems.push(`${msg}${detail ? `（实际：${detail}）` : ''}`);
  console.log(`  ${cond ? 'OK  ' : 'FAIL'} ${msg}${cond || !detail ? '' : ` → ${detail}`}`);
};

const project = fs.mkdtempSync(path.join(os.tmpdir(), 'nv-lock-smoke-'));
const lockPath = lockPathFor(projectKeyFor(project));

// holder 子进程：取锁 → 报告 pid → hold → 退出（不显式释放，模拟"进程结束时锁该消失"）
const holder = spawn(process.execPath, ['--input-type=module', '-e', `
import {acquireRenderLock, lockPathFor, projectKeyFor} from ${JSON.stringify(new URL('../render-lock.mjs', import.meta.url).href)};
const lockPath = lockPathFor(projectKeyFor(${JSON.stringify(project)}));
const lock = acquireRenderLock(lockPath, {project: ${JSON.stringify(project)}, output: 'holder.mp4'});
if (!lock.ok) { console.error('holder 拿不到锁'); process.exit(3); }
console.log(JSON.stringify({pid: process.pid}));
setTimeout(() => process.exit(0), ${HOLD_MS});
`], {stdio: ['ignore', 'pipe', 'pipe']});

const firstLine = await new Promise((resolve, reject) => {
  let buf = '';
  const timer = setTimeout(() => reject(new Error('holder 3 秒内没报告 pid')), 3000);
  holder.stdout.on('data', (chunk) => {
    buf += chunk.toString();
    const nl = buf.indexOf('\n');
    if (nl >= 0) {
      clearTimeout(timer);
      try { resolve(JSON.parse(buf.slice(0, nl))); } catch (e) { reject(e); }
    }
  });
  holder.on('exit', (code) => { if (code !== 0) reject(new Error(`holder 退出码 ${code}`)); });
}).catch((err) => {
  problems.push(`holder 启动失败：${err.message}`);
  return null;
});

if (firstLine) {
  // ② 持锁期间再取 → 必须失败，且要能说清是谁占着
  const second = acquireRenderLock(lockPath, {project, output: 'intruder.mp4'});
  ok(second.ok === false, '第二个进程取锁必须失败', `ok=${second.ok}`);
  if (!second.ok) {
    ok(second.holder?.pid === firstLine.pid, '失败时能报出持锁进程的 pid',
       `expected ${firstLine.pid}, got ${second.holder?.pid}`);
  }

  // ③ holder 自然退出后 → 必须能取到
  const exited = new Promise((resolve) => holder.on('exit', resolve));
  await exited;
  const third = acquireRenderLock(lockPath, {project, output: 'after.mp4'});
  ok(third.ok === true, 'holder 退出后锁应可再取（不能留下永久残锁）', `ok=${third.ok}`);
  if (third.ok) third.release();
}

fs.rmSync(project, {recursive: true, force: true});
console.log(problems.length ? `\nFAILED：${problems.length} 条不成立` : '\nrender-lock smoke PASS');
process.exit(problems.length ? 1 : 0);
