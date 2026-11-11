#!/usr/bin/env node
/**
 * purity-smoke.mjs — CI 用的「连续渲 vs 单帧渲」回归（3.5.4 P0 的回归锁）
 *
 * 用随仓库的 examples/concept-hash-table.story.json 现搭一个工程（compose → 静音旁白 → resolve-shots），
 * 依赖直接借模板已经 `npm ci` 好的 node_modules（符号链接，不再装一遍），然后对**带转场的镜头交接**
 * 各取一个短窗口：从交接前 12 帧连续渲到交接后 44 帧，再挑交接帧 / 转场末帧 / 元素入场后几帧单独渲，
 * 逐像素比。3.5.3 的缺陷（panel 写 NaN opacity → 连续渲时 S5 整镜消失）在这里是 64k 像素级的差。
 *
 * 用法：node scripts/dev/purity-smoke.mjs [--windows=2] [--scale=0.2] [--keep]
 * 前置：assets/lecture-template 已 npm ci；ffmpeg 在 PATH 上。
 * 退出码：0 通过；1 有窗口不一致；2 环境问题。
 */
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import {fileURLToPath} from 'node:url';
import {writeSilentNarration} from '../silent-audio.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const TEMPLATE = path.join(ROOT, 'assets', 'lecture-template');
const args = process.argv.slice(2);
const flag = (n, d) => { const a = args.find((x) => x.startsWith(`--${n}=`) || x === `--${n}`); return a ? (a.includes('=') ? a.split('=')[1] : true) : d; };
const windows = Number(flag('windows', 2));
const scale = String(flag('scale', 0.2));
// 像素容差：同一 DOM 在两种渲法下，裁切边 / 缩放中的卡片边缘偶有 ≤27/255 的抗锯齿差
// （实测：截图时刻两边 DOM 哈希完全相同，差异只在 1px 宽的边上）。缺陷级的差是 Δ≥200。
const tol = String(flag('tol', 48));
const die = (m, c = 2) => { console.error(`purity-smoke: ${m}`); process.exit(c); };
const run = (cmd, argv, opt = {}) => {
  const r = spawnSync(cmd, argv, {stdio: 'inherit', ...opt});
  if (r.status !== 0) die(`${cmd} ${argv.join(' ')} 失败（rc=${r.status}）`, opt.rcOnFail ?? 2);
};
if (!fs.existsSync(path.join(TEMPLATE, 'node_modules', '@remotion', 'renderer'))) die('模板还没 npm ci（assets/lecture-template/node_modules 缺 @remotion/renderer）');

const work = fs.mkdtempSync(path.join(os.tmpdir(), 'nv-purity-smoke-'));
const project = path.join(work, 'p');
console.log(`purity-smoke: 工程 ${project}`);
run(process.execPath, [path.join(ROOT, 'scripts', 'notebook-video.mjs'), 'new-project', project]);
fs.symlinkSync(path.join(TEMPLATE, 'node_modules'), path.join(project, 'node_modules'), 'junction');
const py = process.platform === 'win32' ? 'python' : 'python3';
fs.mkdirSync(path.join(project, 'renders'), {recursive: true});
run(py, [path.join(ROOT, 'scripts', 'compose-story.py'), path.join(ROOT, 'examples', 'concept-hash-table.story.json'), project,
  '--report', path.join(project, 'renders', 'compose-report.json')], {stdio: ['ignore', 'ignore', 'inherit']});
const rep = JSON.parse(fs.readFileSync(path.join(project, 'renders', 'compose-report.json'), 'utf8'));
writeSilentNarration(project, (rep.frames / 30 + 0.5).toFixed(2));
run(py, [path.join(ROOT, 'scripts', 'resolve-shots.py'), project], {stdio: ['ignore', 'ignore', 'inherit']});
run(process.execPath, [path.join(project, 'sync-render-inputs.cjs')], {stdio: ['ignore', 'ignore', 'inherit']});

const resolved = JSON.parse(fs.readFileSync(path.join(project, 'manifests', 'shots.resolved.json'), 'utf8'));
const shots = resolved.shots ?? [];
const total = Number(resolved.duration ?? Math.max(...shots.map((s) => s.to)));
// 选窗口：优先「上一镜有卡片 / 对比面板、本镜也有」的交接——panel 的那个 NaN 正是在这里暴露的；
// 其余按出现顺序补足。窗口：交接前 12 帧 → 交接后 44 帧。
const story = fs.readFileSync(path.join(project, 'src', 'story.ts'), 'utf8');
const panelShots = new Set([...story.matchAll(/"(S\d+)":\{"layout":"(compare|number)"/g)].map((m) => m[1]));
const bounds = shots.slice(1).map((s) => ({id: s.id, b: Number(s.from)}));
bounds.sort((x, y) => Number(panelShots.has(y.id)) - Number(panelShots.has(x.id)) || x.b - y.b);
const picked = bounds.slice(0, windows);
if (!picked.length) die('分镜里没有镜头交接');
let bad = 0;
for (const {id, b} of picked) {
  const from = Math.max(0, b - 12), to = Math.min(total - 1, b + 44);
  const checks = [...new Set([b, b + 14, b + 24, b + 34, to].filter((f) => f >= from && f <= to))].join(',');
  console.log(`\npurity-smoke: ${id} 交接 f${b} → 窗口 ${from}-${to}，单帧比对 ${checks}`);
  const r = spawnSync(process.execPath, [path.join(ROOT, 'scripts', 'dev', 'frame-purity.mjs'), project,
    `--from=${from}`, `--to=${to}`, `--check=${checks}`, `--scale=${scale}`, `--tol=${tol}`, `--out=${path.join(work, `out-${id}`)}`], {stdio: 'inherit'});
  if (r.status === 1) bad++;
  else if (r.status !== 0) die(`frame-purity 异常退出（rc=${r.status}）`);
}
if (!flag('keep', false)) fs.rmSync(work, {recursive: true, force: true});
else console.log(`purity-smoke: 保留 ${work}`);
if (bad) { console.error(`\n✗ purity-smoke：${bad}/${picked.length} 个窗口里，连续渲与单帧渲画面不同`); process.exit(1); }
console.log(`\n✓ purity-smoke：${picked.length} 个镜头交接窗口，连续渲与单帧渲一致（容差 Δ≤${tol}/255）`);
