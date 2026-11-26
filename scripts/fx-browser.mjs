// fx-browser.mjs · 真卷页（@remotion/effects 的 pageTurn，WebGL2）的能力探针
//
// pageTurn 走 WebGL2 + HTML-in-canvas，Remotion 缺省的 Chrome Headless Shell 就画得出来
// （Linux 无显卡时是软件 ANGLE / SwiftShader），所以整片用同一个浏览器、同样的并发一次渲完。
// 探针仍然保留：渲一帧 320×180 的卷页、读像素，确认这台机器的浏览器真的有 WebGL2——
// 没有时 pageTurn 会直接抛错，所以探针不过就不传 {nvFx:'on'}，合成里 pageturn 退回纯 CSS 的
// pageflip 折痕翻页、peel 退回 drop，片子照样有翻页。
// 结论缓存在 <project>/renders/.fx-probe.json（键 = Remotion 版本 + 平台），make-video 读它写报告。

import {createHash} from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import zlib from 'node:zlib';
import {fileURLToPath} from 'node:url';

export const FX_PROBE_COMPOSITION = 'NotebookVideoFxProbe';
/** 探针的上限（毫秒）：渲一帧通常十几秒；到点就杀，按失败处理（退回 pageflip）。 */
export const FX_PROBE_TIMEOUT_MS = 90_000;

// 转场计划（哪几帧要卷页）在 scripts/transition-plan.mjs，这里只转出。
import {curlPlan, curlWindows, projectUsesCurl, warnFallback} from './transition-plan.mjs';
export {CURL_FRAMES, curlWindows, projectUsesCurl} from './transition-plan.mjs';

/** 最小 PNG 解码（8 位 RGB / RGBA、非隔行），只给探针读几个像素用 —— 不引第三方包。 */
export const decodePng = (buf) => {
  if (buf.readUInt32BE(0) !== 0x89504e47) throw new Error('not a PNG');
  let off = 8, w = 0, h = 0, bitDepth = 0, colorType = 0, interlace = 0;
  const idat = [];
  while (off < buf.length) {
    const len = buf.readUInt32BE(off), type = buf.toString('ascii', off + 4, off + 8), data = buf.subarray(off + 8, off + 8 + len);
    if (type === 'IHDR') { w = data.readUInt32BE(0); h = data.readUInt32BE(4); bitDepth = data[8]; colorType = data[9]; interlace = data[12]; }
    else if (type === 'IDAT') idat.push(data);
    else if (type === 'IEND') break;
    off += 12 + len;
  }
  if (bitDepth !== 8 || interlace !== 0 || (colorType !== 2 && colorType !== 6)) throw new Error(`unsupported PNG (depth ${bitDepth}, color ${colorType}, interlace ${interlace})`);
  const bpp = colorType === 6 ? 4 : 3, stride = w * bpp;
  const raw = zlib.inflateSync(Buffer.concat(idat));
  const out = Buffer.alloc(h * stride);
  for (let y = 0; y < h; y++) {
    const ft = raw[y * (stride + 1)], src = raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1));
    for (let x = 0; x < stride; x++) {
      const a = x >= bpp ? out[y * stride + x - bpp] : 0, b = y > 0 ? out[(y - 1) * stride + x] : 0, c = x >= bpp && y > 0 ? out[(y - 1) * stride + x - bpp] : 0;
      let v = src[x];
      if (ft === 1) v += a; else if (ft === 2) v += b; else if (ft === 3) v += (a + b) >> 1;
      else if (ft === 4) { const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c); v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c; }
      out[y * stride + x] = v & 255;
    }
  }
  return {w, h, px: (x, y) => { const i = y * stride + x * bpp; return [out[i], out[i + 1], out[i + 2]]; }};
};

/** 探针判据：左侧仍是红页（卷页画出来了），右侧露出蓝底（卷走的部分透明）。 */
export const judgeProbe = (png) => {
  const near = (c, t) => c.every((v, i) => Math.abs(v - t[i]) < 40);
  const left = png.px(16, 90), right = png.px(png.w - 16, 90);
  if (near(left, [255, 0, 0]) && near(right, [0, 0, 255])) return {ok: true};
  if (near(left, [255, 0, 0]) && near(right, [255, 0, 0])) return {ok: false, why: '卷页没有生效（整页仍平铺）'};
  if (near(left, [0, 0, 255])) return {ok: false, why: '卷页那一层是空的（画布没有合成上屏）'};
  return {ok: false, why: `探针像素异常 left=${left} right=${right}`};
};

/**
 * 决定这台机器能否给成片开真卷页。返回 {on, reason, props}。
 * runStill(args) → Promise<{code, out}>：由调用方用工程内的 remotion CLI、与成片相同的浏览器渲探针那一帧。
 */
export const resolveFx = async ({project, remotionVersion = '', runStill, env = process.env, force = false}) => {
  const cacheFile = path.join(project, 'renders', '.fx-probe.json');
  const save = (r) => { try { fs.mkdirSync(path.dirname(cacheFile), {recursive: true}); fs.writeFileSync(cacheFile, JSON.stringify({...r, at: new Date().toISOString()}, null, 2) + '\n'); } catch { /* 只读工程也照常渲染 */ } return r; };
  const plan = curlPlan(project);
  const used = plan.boundaries.some((b) => b.curl);
  if (/^(off|0|false|no)$/i.test(env.NOTEBOOK_VIDEO_FX ?? '')) return save({on: false, used, reason: 'NOTEBOOK_VIDEO_FX=off（手动关闭）'});
  warnFallback(project, plan.problems);
  const planInfo = {source: plan.source, theme: plan.theme, craftTransition: plan.craftTransition, curlShots: plan.boundaries.filter((b) => b.curl).length};
  if (!used && !force) return save({on: false, used, plan: planInfo, reason: '本片没有用到 pageturn / peel'});
  const key = createHash('sha256').update(JSON.stringify({probe: 4, remotionVersion, platform: process.platform, arch: process.arch, browser: env.REMOTION_BROWSER_EXECUTABLE ?? ''})).digest('hex').slice(0, 16);
  if (!force) { try { const c = JSON.parse(fs.readFileSync(cacheFile, 'utf8')); if (c.key === key && c.probed) return {...c, used}; } catch { /* 没缓存 */ } }
  const out = path.join(os.tmpdir(), `nv-fx-probe-${key}.png`);
  fs.rmSync(out, {force: true});
  const t0 = Date.now();
  let res;
  try { res = await runStill([FX_PROBE_COMPOSITION, out, '--frame=0']); } catch (e) { res = {code: 1, out: String(e?.message ?? e)}; }
  const base = {key, probed: true, used, plan: planInfo, remotionVersion, probeMs: Date.now() - t0};
  if (res.code || !fs.existsSync(out)) {
    const hint = /No supported implementation|webgl2/i.test(res.out ?? '') ? '浏览器没有 WebGL2' : /HTML in Canvas|CanvasDrawElement/i.test(res.out ?? '') ? '浏览器不支持 HTML-in-canvas' : '探针渲染失败';
    return save({...base, on: false, reason: `${hint}；已退回折痕翻页（pageflip）`});
  }
  let verdict;
  try { verdict = judgeProbe(decodePng(fs.readFileSync(out))); } catch (e) { verdict = {ok: false, why: `探针图读不出：${e.message}`}; }
  if (!verdict.ok) return save({...base, on: false, reason: `${verdict.why}；已退回折痕翻页（pageflip）`});
  return save({...base, on: true, reason: 'WebGL2 卷页探针通过'});
};

// 自测：node scripts/fx-browser.mjs --self-test（tests/test_fx.py 调它；不开浏览器）
if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1]) && process.argv.includes('--self-test')) {
  const mk = (w, h, f) => { // 造一张 RGB PNG（filter 0）
    const rows = []; for (let y = 0; y < h; y++) { const r = Buffer.alloc(1 + w * 3); for (let x = 0; x < w; x++) f(x, y).forEach((v, i) => { r[1 + x * 3 + i] = v; }); rows.push(r); }
    const chunk = (t, d) => { const b = Buffer.alloc(12 + d.length); b.writeUInt32BE(d.length, 0); b.write(t, 4, 'ascii'); d.copy(b, 8); return b; };
    const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 2;
    return Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(Buffer.concat(rows))), chunk('IEND', Buffer.alloc(0))]);
  };
  const good = judgeProbe(decodePng(mk(320, 180, (x) => (x < 176 ? [255, 0, 0] : [0, 0, 255]))));
  const flat = judgeProbe(decodePng(mk(320, 180, () => [255, 0, 0])));
  const empty = judgeProbe(decodePng(mk(320, 180, () => [0, 0, 255])));
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'nv-fx-test-'));
  fs.mkdirSync(path.join(tmp, 'src', 'theme'), {recursive: true});
  fs.writeFileSync(path.join(tmp, 'src', 'theme', 'active.ts'), "import {THEME} from './journal';\nexport {THEME};\n");
  const skinFile = path.join(tmp, 'src', 'theme', 'journal.tsx');
  const shotsFile = path.join(tmp, 'src', 'shots.ts');
  const setSkin = (kind) => fs.writeFileSync(skinFile, `craft: {transition: '${kind}'}`);
  // ① 分镜表只写 auto：用不用卷页完全由皮肤决定（没有 manifest 的工程走 shots.ts 兜底）
  fs.writeFileSync(shotsFile, "export const SHOTS = {\n  S1: {id:'S1',from:0,to:100,transition:'auto'},\n  S2: {id:'S2',from:100,to:200,transition:'auto'},\n};\n");
  setSkin('slide');
  const unused = projectUsesCurl(tmp);
  setSkin('pageturn');
  const usedSkin = projectUsesCurl(tmp);
  // ② 皮肤是 slide，但分镜显式写了 pageturn / peel：显式优先
  fs.writeFileSync(shotsFile, "export const SHOT_TOTAL = 400;\nexport const SHOTS = {\n  S1: {id:'S1',from:0,to:100,transition:'cut'},\n  S2: {id:'S2',from:100,to:200,transition:'pageturn'},\n  S3: {id:'S3',from:200,to:300,transition:'slide'},\n  S4: {id:'S4',from:300,to:310,transition:'peel'},\n  S5: {id:'S5',from:310,to:400},\n};\n");
  setSkin('slide');
  const usedShot = projectUsesCurl(tmp);
  const winSlide = curlWindows(tmp, 400); // 皮肤缺省 slide：只有显式的 S2、S4
  setSkin('pageturn');
  const winCurl = curlWindows(tmp, 400); // 皮肤缺省 pageturn：S5（auto）也算，S4/S5 窗口相接 → 合并
  // ③ 有了 manifests/shots.resolved.json 就按结构化输入算，shots.ts 的排版不再影响结果
  fs.mkdirSync(path.join(tmp, 'manifests'), {recursive: true});
  fs.writeFileSync(path.join(tmp, 'manifests', 'shots.resolved.json'), JSON.stringify({duration: 400, theme: 'journal',
    shots: [{id: 'S1', from: 0, to: 100, transition: 'auto'}, {id: 'S2', from: 100, to: 200, transition: 'peel'}]}));
  const planSource = curlPlan(tmp).source;
  const winManifest = curlWindows(tmp, 400);
  fs.rmSync(tmp, {recursive: true, force: true, maxRetries: 5, retryDelay: 120});
  const result = {good: good.ok, flat: flat.ok, empty: empty.ok, usedSkin, unused, usedShot, planSource, winManifest, winSlide, winCurl};
  console.log(JSON.stringify(result));
  const pass = good.ok && !flat.ok && !empty.ok && usedSkin && !unused && usedShot
    && planSource === 'manifest' && JSON.stringify(winManifest) === '[[100,121]]'
    && JSON.stringify(winSlide) === '[[100,121],[300,321]]' && JSON.stringify(winCurl) === '[[100,121],[300,331]]';
  process.exit(pass ? 0 : 1);
}
