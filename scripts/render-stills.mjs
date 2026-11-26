#!/usr/bin/env node
// SPDX-License-Identifier: Apache-2.0
// render-stills.mjs — 单浏览器会话批量出静帧（@remotion/renderer openBrowser + renderStill）
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import {createRequire} from 'node:module';
import {resolveBrowserExecutable} from './browser-exec.mjs';

const die = (msg, code = 2) => { console.error(`render-stills: ${msg}`); process.exit(code); };
const args = process.argv.slice(2);
const projectArg = args.find((a) => !a.startsWith('--'));
const flagVal = (name, dflt) => {
  const f = args.find((a) => a === `--${name}` || a.startsWith(`--${name}=`));
  if (!f) return dflt;
  const i = f.indexOf('=');
  return i > 0 ? f.slice(i + 1) : dflt;
};

if (!projectArg) die('Usage: render-stills.mjs PROJECT --bundle=DIR --spec=JSON [--composition=NotebookVideoFilm] [--scale=0.5]');
const project = path.resolve(projectArg);
const bundle = path.resolve(flagVal('bundle', ''));
const specPath = path.resolve(flagVal('spec', ''));
const compositionId = flagVal('composition', 'NotebookVideoFilm');
const scale = Number(flagVal('scale', '0.5'));
if (!fs.existsSync(bundle) || !fs.existsSync(specPath)) die('--bundle 与 --spec 必须存在');
if (!Number.isFinite(scale) || scale <= 0) die(`非法 scale: ${scale}`);

const jobs = JSON.parse(fs.readFileSync(specPath, 'utf8'));
if (!Array.isArray(jobs) || !jobs.length) die('spec 不能为空');

const req = createRequire(path.join(project, 'package.json'));
let renderer;
try {
  renderer = req('@remotion/renderer');
} catch (e) {
  die(`缺少 @remotion/renderer：${e.message}`);
}

const browserExecutable = resolveBrowserExecutable();
if (!browserExecutable) await renderer.ensureBrowser();
const browser = await renderer.openBrowser('chrome', {browserExecutable, chromiumOptions: {}});
try {
  const composition = await renderer.selectComposition({
    serveUrl: bundle,
    id: compositionId,
    inputProps: {},
    puppeteerInstance: browser,
    browserExecutable,
  });
  for (const job of jobs) {
    fs.mkdirSync(path.dirname(job.out), {recursive: true});
    try {
      await renderer.renderStill({
        composition,
        serveUrl: bundle,
        inputProps: {},
        frame: Number(job.f),
        output: job.out,
        imageFormat: 'png',
        scale,
        puppeteerInstance: browser,
        browserExecutable,
        overwrite: true,
        onBrowserLog: (log) => {
          const line = String(log.text ?? '').trim();
          if (!line) return;
          if (log.type === 'error') console.error(line);
          else console.log(line);
        },
      });
      console.log(`Rendered still [${jobs.indexOf(job) + 1}/${jobs.length}] f${job.f}`);
    } catch (err) {
      console.error(`\n[render-stills] f${job.f} Error: ${err?.message || err}`);
      process.exitCode = 1;
      break;
    }
  }
} finally {
  await browser.close({silent: true});
}
