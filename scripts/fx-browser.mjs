// fx-browser.mjs · 真卷页（@remotion/effects 的 pageTurn，WebGPU）的浏览器选择 + 能力探针（3.5.0）
//
// 为什么要这一层：Remotion 缺省的 Chrome Headless Shell 是老式无头模式，没有 WebGPU 适配器
// （实测 157.0.8080.0 / linux-arm64：`No WebGPU adapter available`）。pageTurn 要：
//   · 完整版 Chrome（Chrome for Testing ≥ 149，Remotion `--chrome-mode=chrome-for-testing` → --headless=new）；
//   · HTML-in-canvas（Remotion 已自动加 `--enable-features=CanvasDrawElement`）；
//   · 没有 GPU 的机器：软件 Vulkan（SwiftShader）+ ANGLE 跑在同一个 Vulkan 上 ——
//     `--use-angle=vulkan --use-vulkan=swiftshader --enable-unsafe-swiftshader` + feature `Vulkan`。
//     （实测：ANGLE 走 GL/SwiftShader 而 WebGPU 走 Vulkan 时，WebGPU 画布与合成器之间的共享纹理建不起来，
//      卷页那一层变成全透明 —— 不报错，只是**悄悄画空**。所以必须用像素探针验收，不能只问 navigator.gpu。）
// Remotion 4 的 CLI 不收任意 Chromium 参数，所以在 POSIX 上生成一个包装脚本当 --browser-executable：
// 合并 --enable-features、去掉 Remotion 自己的 GL 参数、换成上面这组。
// ⚠ 完整版 Chrome 的 --headless=new 下**并发 > 1 会花屏**（实测 concurrency=2：第二个标签页截图超出窗口的部分
//   重复平铺，2560×1440 帧里出现 780×380 的格子）。所以开 fx 时渲染一律 concurrency=1（FX_CONCURRENCY）。
//
// 结论缓存在 <project>/renders/.fx-probe.json（键 = 浏览器 + 参数 + Remotion 版本），make-video 读它写报告。
// 任何一步不通 → {on:false, reason}，调用方照常渲染（pageturn / peel 在合成里自动退回 slide / drop）。

import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import zlib from 'node:zlib';
import {fileURLToPath} from 'node:url';

export const FX_PROBE_COMPOSITION = 'NotebookVideoFxProbe';
/** 开 fx 时的渲染并发（见文件头 ⚠）。 */
export const FX_CONCURRENCY = 1;
/** 软件 GPU（无显卡的 Linux 服务器 / 容器）上实测能画出 pageTurn 的参数组。 */
export const SOFTWARE_GPU_FLAGS = ['--use-angle=vulkan', '--use-vulkan=swiftshader', '--enable-unsafe-swiftshader'];

/** 工程是否用到卷页：分镜表显式写了 pageturn / peel，或当前皮肤的缺省转场是它们。 */
export const projectUsesCurl = (project) => {
  const read = (p) => { try { return fs.readFileSync(p, 'utf8'); } catch { return ''; } };
  const shots = read(path.join(project, 'src', 'shots.ts'));
  if (/transition\s*:\s*['"](pageturn|peel)['"]/.test(shots)) return true;
  const active = read(path.join(project, 'src', 'theme', 'active.ts'));
  const m = active.match(/from\s+['"]\.\/([\w-]+)['"]/);
  if (!m) return false;
  const skin = read(path.join(project, 'src', 'theme', `${m[1]}.tsx`));
  return /transition\s*:\s*['"](pageturn|peel)['"]/.test(skin);
};

/** 卷页转场时长（帧），与 src/fx.tsx 的 CURL_FRAMES 同值（tests/test_fx.py 交叉校验）。 */
export const CURL_FRAMES = 22;

/**
 * 成片里可能出现卷页的帧窗 [[a, b], …]（含两端）：分镜表显式 pageturn / peel，或皮肤缺省是卷页且该镜写 auto 类。
 * **宁多勿少**：多拼一个窗口只是那 22 帧换完整版 Chrome 再渲一遍（同一合成、同一帧 → 同样的画面，章节首镜照样是 drop）；
 * 少拼一个则那一处留着退回后的 slide。读 src/shots.ts（引擎真正吃的那份）。
 */
export const curlWindows = (project, total = Infinity) => {
  const read = (p) => { try { return fs.readFileSync(p, 'utf8'); } catch { return ''; } };
  const shots = read(path.join(project, 'src', 'shots.ts'));
  const active = read(path.join(project, 'src', 'theme', 'active.ts')).match(/from\s+['"]\.\/([\w-]+)['"]/);
  const skin = active ? read(path.join(project, 'src', 'theme', `${active[1]}.tsx`)) : '';
  const skinCurl = /transition\s*:\s*['"](pageturn|peel)['"]/.test(skin);
  const out = [];
  for (const line of shots.split('\n')) {
    const from = line.match(/\bfrom\s*:\s*(\d+)/);
    if (!from || !/\bid\s*:/.test(line)) continue;
    const a = Number(from[1]);
    if (a === 0) continue; // 首镜没有转场
    const tr = (line.match(/\btransition\s*:\s*['"]([\w-]+)['"]/) ?? [])[1] ?? 'auto';
    const curl = tr === 'pageturn' || tr === 'peel' || (skinCurl && ['auto', 'cut', 'reveal', 'handoff'].includes(tr));
    if (curl) out.push([a, Math.min(total - 1, a + CURL_FRAMES - 1)]);
  }
  out.sort((x, y) => x[0] - y[0]);
  const merged = [];
  for (const w of out) { const last = merged.at(-1); if (last && w[0] <= last[1] + 1) last[1] = Math.max(last[1], w[1]); else merged.push([...w]); }
  return merged;
};

/**
 * 把完整版 Chrome 渲的卷页片段按帧号拼回快速渲染的整片（split + trim + concat，按帧号精确；只重编码这一遍）。
 * 返回 ffmpeg 参数（不含可执行名）。segs[i] 对应 windows[i]。
 */
export const spliceArgs = (raw, segs, windows, out, {crf = 16} = {}) => {
  const n = windows.length, parts = [];
  const chains = [`[0:v]split=${n + 1}${Array.from({length: n + 1}, (_, i) => `[m${i}]`).join('')}`];
  let cursor = 0;
  windows.forEach(([a, b], i) => {
    chains.push(`[m${i}]trim=start_frame=${cursor}:end_frame=${a},setpts=PTS-STARTPTS[p${i}]`);
    chains.push(`[${i + 1}:v]trim=end_frame=${b - a + 1},setpts=PTS-STARTPTS[w${i}]`);
    parts.push(`[p${i}]`, `[w${i}]`);
    cursor = b + 1;
  });
  chains.push(`[m${n}]trim=start_frame=${cursor},setpts=PTS-STARTPTS[p${n}]`);
  parts.push(`[p${n}]`);
  chains.push(`${parts.join('')}concat=n=${parts.length}:v=1:a=0[v]`);
  return ['-y', '-hide_banner', '-loglevel', 'error', '-i', raw, ...segs.flatMap((sg) => ['-i', sg]),
    '-filter_complex', chains.join(';'), '-map', '[v]', '-map', '0:a?', '-c:a', 'copy',
    '-c:v', 'libx264', '-crf', String(crf), '-preset', 'medium', '-pix_fmt', 'yuv420p',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', out];
};

/** 找一个完整版 Chromium / Chrome for Testing：显式环境变量优先，其次本机 Playwright 缓存里版本最高的那个。 */
export const findFxBrowser = (env = process.env) => {
  if (env.NOTEBOOK_VIDEO_FX_BROWSER) return fs.existsSync(env.NOTEBOOK_VIDEO_FX_BROWSER) ? env.NOTEBOOK_VIDEO_FX_BROWSER : null;
  const home = os.homedir();
  const roots = [env.PLAYWRIGHT_BROWSERS_PATH, path.join(home, '.cache', 'ms-playwright'), path.join(home, 'Library', 'Caches', 'ms-playwright'),
    env.LOCALAPPDATA && path.join(env.LOCALAPPDATA, 'ms-playwright')].filter(Boolean);
  const rel = ['chrome-linux-arm64/chrome', 'chrome-linux64/chrome', 'chrome-linux/chrome', 'chrome-win64/chrome.exe', 'chrome-win/chrome.exe',
    'chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing', 'chrome-mac/Chromium.app/Contents/MacOS/Chromium'];
  const found = [];
  for (const root of roots) {
    let dirs = [];
    try { dirs = fs.readdirSync(root); } catch { continue; }
    for (const d of dirs) {
      const m = d.match(/^chromium-(\d+)$/); // 不要 chromium_headless_shell-*：那是老式无头，没有 WebGPU
      if (!m) continue;
      for (const r of rel) { const p = path.join(root, d, r); if (fs.existsSync(p)) found.push({rev: Number(m[1]), p}); }
    }
  }
  found.sort((a, b) => b.rev - a.rev);
  return found[0]?.p ?? null;
};

/** POSIX 包装脚本：合并 --enable-features、去掉 Remotion 的 GL 参数、追加软件 GPU 参数。返回脚本路径。 */
export const writeChromeWrapper = (browser, extraFlags, dir = os.tmpdir()) => {
  const key = createHash('sha256').update(`${browser}\n${extraFlags.join(' ')}`).digest('hex').slice(0, 12);
  const file = path.join(dir, `nv-fx-chrome-${key}.sh`);
  const q = (s) => `'${String(s).replace(/'/g, `'\\''`)}'`;
  // 软件 Vulkan：Chromium 自带 libvk_swiftshader.so + vk_swiftshader_icd.json，但 Vulkan loader 不会自己去找浏览器目录里的 ICD。
  // 不指 VK_ICD_FILENAMES 时 ANGLE 报 `Internal Vulkan error (-7): A requested extension is not supported`，
  // 退回 GL → WebGPU 的共享纹理建不起来（`Could not find SharedImageBackingFactory`）→ 卷页层画空。
  // 实测 2026-10-27：同一容器重启后这个变量没了，探针立刻从通过变成全白。用户自己设了就不覆盖。
  const icd = path.join(path.dirname(browser), 'vk_swiftshader_icd.json');
  const icdLine = extraFlags.includes('--use-vulkan=swiftshader') && fs.existsSync(icd) ? `[ -n "$VK_ICD_FILENAMES" ] || export VK_ICD_FILENAMES=${q(icd)}\n` : '';
  const script = `#!/bin/sh
# notebook-video fx wrapper (generated): real page-turn needs WebGPU; see scripts/fx-browser.mjs
${icdLine}feats=Vulkan
set -- "$@" __NV_END__
while [ "$1" != __NV_END__ ]; do
  a=$1; shift
  case "$a" in
    --enable-features=*) feats="$feats,\${a#--enable-features=}" ;;
    --use-gl=*|--use-angle=*|--use-vulkan=*|--disable-vulkan-fallback-to-gl-for-testing|--disable-vulkan-surface) ;;
    *) set -- "$@" "$a" ;;
  esac
done
shift
exec ${q(browser)} "$@" "--enable-features=$feats" --window-size=3840,2160 ${extraFlags.map(q).join(' ')}
`;
  fs.writeFileSync(file, script, {mode: 0o755});
  fs.chmodSync(file, 0o755);
  return file;
};

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
  if (near(left, [0, 0, 255])) return {ok: false, why: '卷页那一层是空的（WebGPU 画布没有合成上屏）'};
  return {ok: false, why: `探针像素异常 left=${left} right=${right}`};
};

/**
 * 决定这台机器能否给成片开真卷页。返回 {on, reason, args, browser, flags}。
 * runStill(args) → Promise<{code, out}>：由调用方用工程内的 remotion CLI 渲探针那一帧（args 已含输出路径）。
 */
export const resolveFx = async ({project, remotionVersion = '', runStill, env = process.env, force = false}) => {
  const cacheFile = path.join(project, 'renders', '.fx-probe.json');
  const save = (r) => { try { fs.mkdirSync(path.dirname(cacheFile), {recursive: true}); fs.writeFileSync(cacheFile, JSON.stringify({...r, at: new Date().toISOString()}, null, 2) + '\n'); } catch { /* 只读工程也照常渲染 */ } return r; };
  if (/^(off|0|false|no)$/i.test(env.NOTEBOOK_VIDEO_FX ?? '')) return save({on: false, used: projectUsesCurl(project), reason: 'NOTEBOOK_VIDEO_FX=off（手动关闭）', args: []});
  const used = projectUsesCurl(project);
  if (!used && !force) return save({on: false, used, reason: '本片没有用到 pageturn / peel', args: []});
  const browser = findFxBrowser(env);
  const linux = process.platform === 'linux';
  const flags = env.NOTEBOOK_VIDEO_FX_FLAGS !== undefined ? env.NOTEBOOK_VIDEO_FX_FLAGS.split(/\s+/).filter(Boolean) : (linux ? SOFTWARE_GPU_FLAGS : []);
  const key = createHash('sha256').update(JSON.stringify({wrapper: 3, browser, flags, remotionVersion, platform: process.platform, arch: process.arch})).digest('hex').slice(0, 16);
  const propsFile = path.join(os.tmpdir(), 'nv-fx-props-on.json');
  fs.writeFileSync(propsFile, JSON.stringify({nvFx: 'on'}));
  // 包装脚本放系统临时目录（每次都重写：缓存命中时 /tmp 可能已被清掉）
  const exe = browser && !process.platform.startsWith('win') && flags.length ? writeChromeWrapper(browser, flags) : browser;
  if (!force) { try { const c = JSON.parse(fs.readFileSync(cacheFile, 'utf8')); if (c.key === key && c.probed) return {...c, used}; } catch { /* 没缓存 */ } }
  const args = ['--gl=angle', '--chrome-mode=chrome-for-testing', ...(exe ? [`--browser-executable=${exe}`] : []), `--props=${propsFile}`];
  const out = path.join(os.tmpdir(), `nv-fx-probe-${key}.png`);
  fs.rmSync(out, {force: true});
  const t0 = Date.now();
  let res;
  try { res = await runStill([FX_PROBE_COMPOSITION, out, '--frame=0', ...args.filter((a) => !a.startsWith('--props='))]); } catch (e) { res = {code: 1, out: String(e?.message ?? e)}; }
  const ms = Date.now() - t0;
  const base = {key, probed: true, used, browser: browser ?? '(Remotion chrome-for-testing 自动下载)', flags, remotionVersion, probeMs: ms};
  if (res.code || !fs.existsSync(out)) {
    const hint = /No WebGPU adapter/.test(res.out ?? '') ? '浏览器没有 WebGPU 适配器' : /HTML in Canvas|CanvasDrawElement/i.test(res.out ?? '') ? '浏览器不支持 HTML-in-canvas（需 Chrome ≥ 149）' : '探针渲染失败';
    return save({...base, on: false, reason: `${hint}；${browser ? '' : '没找到完整版 Chromium（设 NOTEBOOK_VIDEO_FX_BROWSER 或 npx playwright install chromium）；'}已退回 slide / drop`, args: []});
  }
  let verdict;
  try { verdict = judgeProbe(decodePng(fs.readFileSync(out))); } catch (e) { verdict = {ok: false, why: `探针图读不出：${e.message}`}; }
  if (!verdict.ok) return save({...base, on: false, reason: `${verdict.why}；已退回 slide / drop`, args: []});
  return save({...base, on: true, reason: 'WebGPU 卷页探针通过', args});
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
  fs.writeFileSync(path.join(tmp, 'src', 'theme', 'journal.tsx'), "craft: {transition: 'pageturn'}");
  const usedSkin = projectUsesCurl(tmp);
  fs.writeFileSync(path.join(tmp, 'src', 'theme', 'journal.tsx'), "craft: {transition: 'slide'}");
  const unused = projectUsesCurl(tmp);
  fs.writeFileSync(path.join(tmp, 'src', 'shots.ts'), "S2: {transition:'peel'}");
  const usedShot = projectUsesCurl(tmp);
  fs.writeFileSync(path.join(tmp, 'src', 'shots.ts'), "export const SHOTS = {\n  S1: {id:'S1',from:0,to:100,transition:'cut'},\n  S2: {id:'S2',from:100,to:200,transition:'pageturn'},\n  S3: {id:'S3',from:200,to:300,transition:'slide'},\n  S4: {id:'S4',from:300,to:310,transition:'peel'},\n  S5: {id:'S5',from:310,to:400},\n};\n");
  const winSlide = curlWindows(tmp, 400); // 皮肤缺省 slide：只有显式的 S2、S4
  fs.writeFileSync(path.join(tmp, 'src', 'theme', 'journal.tsx'), "craft: {transition: 'pageturn'}");
  const winCurl = curlWindows(tmp, 400); // 皮肤缺省 pageturn：S5（auto）也算，S4/S5 窗口相接 → 合并
  const sp = spliceArgs('raw.mp4', ['a.mp4', 'b.mp4'], [[100, 121], [300, 331]], 'out.mp4');
  const fc = sp[sp.indexOf('-filter_complex') + 1];
  const wrapper = writeChromeWrapper('/bin/echo', SOFTWARE_GPU_FLAGS, tmp);
  // Windows 上包装脚本（Linux shell 脚本）根本执行不了，spawnSync 的 stdout 是 undefined，
  // 以前直接 .trim() 就抛 TypeError，自检整个崩掉（3.7.0 修）。这里容错，并把「echo 断言」限定在 POSIX。
  const echoRun = spawnSync(wrapper, ['--use-gl=angle', '--enable-features=CanvasDrawElement', '--headless=new'], {encoding: 'utf8'});
  const echoed = (echoRun.stdout ?? '').trim();
  const echoChecked = process.platform !== 'win32';
  if (!echoChecked) console.error('SKIP: wrapper echo check (POSIX only — 包装脚本是 shell 脚本)');
  // 浏览器目录里有 SwiftShader ICD → 包装脚本要指 VK_ICD_FILENAMES（没有它 ANGLE-Vulkan 初始化失败、卷页画空）
  fs.mkdirSync(path.join(tmp, 'cft'));
  fs.writeFileSync(path.join(tmp, 'cft', 'vk_swiftshader_icd.json'), '{}');
  const icdWrapped = fs.readFileSync(writeChromeWrapper(path.join(tmp, 'cft', 'chrome'), SOFTWARE_GPU_FLAGS, tmp), 'utf8').includes('export VK_ICD_FILENAMES=');
  const icdSkipped = !fs.readFileSync(writeChromeWrapper(path.join(tmp, 'cft', 'chrome'), [], tmp), 'utf8').includes('VK_ICD_FILENAMES');
  fs.rmSync(tmp, {recursive: true, force: true, maxRetries: 5, retryDelay: 120});
  const result = {good: good.ok, flat: flat.ok, empty: empty.ok, usedSkin, unused, usedShot, echoed, winSlide, winCurl, fc, icdWrapped, icdSkipped};
  console.log(JSON.stringify(result));
  const pass = icdWrapped && icdSkipped && good.ok && !flat.ok && !empty.ok && usedSkin && !unused && usedShot
    && JSON.stringify(winSlide) === '[[100,121],[300,321]]' && JSON.stringify(winCurl) === '[[100,121],[300,331]]'
    && fc === '[0:v]split=3[m0][m1][m2];[m0]trim=start_frame=0:end_frame=100,setpts=PTS-STARTPTS[p0];[1:v]trim=end_frame=22,setpts=PTS-STARTPTS[w0];[m1]trim=start_frame=122:end_frame=300,setpts=PTS-STARTPTS[p1];[2:v]trim=end_frame=32,setpts=PTS-STARTPTS[w1];[m2]trim=start_frame=332,setpts=PTS-STARTPTS[p2];[p0][w0][p1][w1][p2]concat=n=5:v=1:a=0[v]'
    && (!echoChecked || echoed === '--headless=new --enable-features=Vulkan,CanvasDrawElement --window-size=3840,2160 --use-angle=vulkan --use-vulkan=swiftshader --enable-unsafe-swiftshader');
  process.exit(pass ? 0 : 1);
}
