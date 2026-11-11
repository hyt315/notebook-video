#!/usr/bin/env node
/**
 * frame-purity.mjs — 「渲染是帧号的纯函数」回归检查（3.5.4 P0）
 *
 * 为什么要有它：3.5.3 的 hash 片从 f0 连续渲染时，S5 两张对比卡整镜消失，单帧 still 却都在。
 * 根因是 auto.tsx 的 panel 把 `opacity: NaN` 写进 inline style —— 浏览器拒收非法值、**保留上一帧
 * 的旧值**，于是同一帧的画面取决于这个标签页之前渲过哪些帧。这类缺陷单帧 still 永远看不见、
 * 联系表给假阴性，只有「同一帧分别用两种方式渲出来再逐像素比」才抓得住。
 *
 * 做法（一个浏览器、一次打包）：
 *   1. 连续渲：renderFrames 在**一个标签页里**从 --from 顺序渲到 --to（concurrency=1，与成片同路径）；
 *   2. 单帧渲：对 --check 里的每一帧各开一个新页面 renderStill（与 stills / 联系表同路径）；
 *   3. 逐像素比：任何一个通道差 > --tol（默认 0）的像素都计数；有差即 rc=1，并把差异图落盘。
 *
 * 用法：
 *   node scripts/dev/frame-purity.mjs PROJECT --from=0 --to=120 --check=10,57,100 [--scale=0.25]
 *        [--every=N] [--tol=0] [--out=DIR] [--composition=NotebookVideoFilm] [--json]
 *   --check 省略时取 --every（默认 15）步长的所有帧；--check=all = 区间内每一帧。
 *   PROJECT 要先跑过 sync-render-inputs（caption-cues / narration 已就位）。
 *
 * 退出码：0 = 全部 0 像素差；1 = 有帧不一致；2 = 用法 / 环境错误。
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import {createRequire} from 'node:module';
import {resolveBrowserExecutable} from '../browser-exec.mjs';

const die = (msg, code = 2) => { console.error(`frame-purity: ${msg}`); process.exit(code); };
const args = process.argv.slice(2);
const project = args.find((a) => !a.startsWith('--'));
if (!project) die('Usage: frame-purity.mjs PROJECT --from=A --to=B [--check=f1,f2|all] [--every=15] [--scale=0.25] [--tol=0] [--out=DIR]');
const flag = (name, dflt) => {
  const hit = args.find((a) => a === `--${name}` || a.startsWith(`--${name}=`));
  if (!hit) return dflt;
  return hit.includes('=') ? hit.slice(hit.indexOf('=') + 1) : true;
};
const known = new Set(['from', 'to', 'check', 'every', 'scale', 'tol', 'out', 'composition', 'json', 'keep']);
for (const a of args) if (a.startsWith('--') && !known.has(a.slice(2).split('=')[0])) die(`未知参数 ${a}`);

const root = path.resolve(project);
if (!fs.existsSync(path.join(root, 'src', 'index.tsx'))) die(`不是工程目录（缺 src/index.tsx）：${root}`);
const req = createRequire(path.join(root, 'package.json'));
let bundler, renderer, PNG;
try {
  bundler = req('@remotion/bundler');
  renderer = req('@remotion/renderer');
  ({PNG} = req('pngjs'));
} catch (e) {
  die(`工程依赖没装好（先 npm ci）：${e.message}`);
}

const from = Number(flag('from', 0));
const to = Number(flag('to', from + 60));
const scale = Number(flag('scale', 0.25));
const tol = Number(flag('tol', 0));
const every = Math.max(1, Number(flag('every', 15)));
const compId = String(flag('composition', 'NotebookVideoFilm'));
if (!(Number.isInteger(from) && Number.isInteger(to) && to >= from)) die(`区间无效：${from}-${to}`);
const checkArg = flag('check', null);
let checks;
if (checkArg === 'all') checks = Array.from({length: to - from + 1}, (_, i) => from + i);
else if (checkArg) checks = String(checkArg).split(',').map((x) => Number(x.trim())).filter((x) => Number.isInteger(x));
else { checks = []; for (let f = from; f <= to; f += every) checks.push(f); if (checks[checks.length - 1] !== to) checks.push(to); }
const outside = checks.filter((f) => f < from || f > to);
if (outside.length) die(`--check 里的帧必须落在连续区间 ${from}-${to} 内：${outside.join(',')}`);
if (!checks.length) die('没有要比对的帧');

const outDir = path.resolve(String(flag('out', fs.mkdtempSync(path.join(os.tmpdir(), 'nv-purity-')))));
fs.mkdirSync(path.join(outDir, 'seq'), {recursive: true});
fs.mkdirSync(path.join(outDir, 'still'), {recursive: true});

const t0 = Date.now();
const log = (m) => console.log(`[purity ${((Date.now() - t0) / 1000).toFixed(0)}s] ${m}`);
const browserExecutable = resolveBrowserExecutable() ?? null;

log(`打包 ${root}`);
const serveUrl = await bundler.bundle({
  entryPoint: path.join(root, 'src', 'index.tsx'),
  publicDir: path.join(root, 'public'),
  rootDir: root,
});
if (!browserExecutable) await renderer.ensureBrowser();   // CI 首次运行：下载 Remotion 的 headless shell
const browser = await renderer.openBrowser('chrome', {browserExecutable, chromiumOptions: {}});
let rc = 0;
try {
  const composition = await renderer.selectComposition({serveUrl, id: compId, inputProps: {}, puppeteerInstance: browser, browserExecutable});
  if (to >= composition.durationInFrames) die(`--to=${to} 超出片长 ${composition.durationInFrames}`);

  log(`连续渲 ${from}-${to}（一个标签页，concurrency=1，scale=${scale}）`);
  const seqFiles = new Map();
  await renderer.renderFrames({
    composition, serveUrl, inputProps: {}, imageFormat: 'png', scale, concurrency: 1,
    frameRange: [from, to], outputDir: path.join(outDir, 'seq'), puppeteerInstance: browser, browserExecutable,
    onStart: () => {}, onFrameUpdate: () => {},
  });
  // renderFrames 的文件名是 element-<帧号补零>.png
  for (const name of fs.readdirSync(path.join(outDir, 'seq'))) {
    const m = /(\d+)\.png$/.exec(name);
    if (m) seqFiles.set(Number(m[1]), path.join(outDir, 'seq', name));
  }

  log(`单帧渲 ${checks.length} 帧（每帧一个新页面）`);
  const results = [];
  for (const f of checks) {
    const still = path.join(outDir, 'still', `f${f}.png`);
    await renderer.renderStill({composition, serveUrl, inputProps: {}, frame: f, output: still, imageFormat: 'png', scale, puppeteerInstance: browser, browserExecutable, overwrite: true});
    const seq = seqFiles.get(f);
    if (!seq) { results.push({frame: f, error: '连续渲染里没有这一帧'}); continue; }
    const a = PNG.sync.read(fs.readFileSync(seq));
    const b = PNG.sync.read(fs.readFileSync(still));
    if (a.width !== b.width || a.height !== b.height) { results.push({frame: f, error: `尺寸不同 ${a.width}x${a.height} vs ${b.width}x${b.height}`}); continue; }
    const diff = new PNG({width: a.width, height: a.height});
    let n = 0, max = 0, x0 = Infinity, y0 = Infinity, x1 = -1, y1 = -1;
    for (let i = 0; i < a.data.length; i += 4) {
      const d = Math.max(Math.abs(a.data[i] - b.data[i]), Math.abs(a.data[i + 1] - b.data[i + 1]), Math.abs(a.data[i + 2] - b.data[i + 2]), Math.abs(a.data[i + 3] - b.data[i + 3]));
      const hot = d > tol;
      if (hot) {
        n++; if (d > max) max = d;
        const p = i / 4, x = p % a.width, y = Math.floor(p / a.width);
        if (x < x0) x0 = x; if (y < y0) y0 = y; if (x > x1) x1 = x; if (y > y1) y1 = y;
      }
      diff.data[i] = hot ? 255 : a.data[i] >> 2; diff.data[i + 1] = hot ? 0 : a.data[i + 1] >> 2;
      diff.data[i + 2] = hot ? 0 : a.data[i + 2] >> 2; diff.data[i + 3] = 255;
    }
    const r = {frame: f, diffPixels: n, maxDiff: max, bbox: n ? [x0, y0, x1, y1] : null};
    if (n) {
      r.diffImage = path.join(outDir, `diff-f${f}.png`);
      fs.writeFileSync(r.diffImage, PNG.sync.write(diff));
      r.seq = seq; r.still = still;
    }
    results.push(r);
    console.log(`  ${n ? 'DIFF' : 'OK  '} f${f}${n ? `  ${n} px（max Δ${max}，bbox ${r.bbox.join(',')}）→ ${r.diffImage}` : ''}`);
  }
  const bad = results.filter((r) => r.error || r.diffPixels);
  fs.writeFileSync(path.join(outDir, 'report.json'), JSON.stringify({project: root, from, to, scale, tol, results}, null, 2));
  log(`${checks.length - bad.length}/${checks.length} 帧一致；报告 ${path.join(outDir, 'report.json')}`);
  if (bad.length) {
    rc = 1;
    console.error(`✗ 渲染不是帧号的纯函数：${bad.map((r) => `f${r.frame}${r.error ? `（${r.error}）` : `（${r.diffPixels} px）`}`).join(' ')}`);
    console.error('  同一帧「从前面连续渲到这里」和「单独渲这一帧」出了不同的画面：有组件把上一帧的状态带进了这一帧');
    console.error('  （inline style 写了 NaN / 非法值、useState/useRef 存了渲染结果、模块级缓存在字体就绪前写入……）。');
  }
} finally {
  await browser.close({silent: true}).catch(() => {});
}
if (flag('json', false)) console.log(fs.readFileSync(path.join(outDir, 'report.json'), 'utf8'));
process.exit(rc);
