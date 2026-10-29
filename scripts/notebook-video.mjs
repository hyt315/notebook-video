#!/usr/bin/env node
import {spawn, spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import {fileURLToPath} from 'node:url';
import {FX_CONCURRENCY, curlWindows, resolveFx, spliceArgs} from './fx-browser.mjs';

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = path.dirname(SCRIPT_DIR);
const IS_WINDOWS = process.platform === 'win32';

const fail = (message, code = 1) => {
  console.error(message);
  process.exit(code);
};

const resolvePath = (value, base = process.cwd()) => path.resolve(base, value);
const ensureParent = (target) => fs.mkdirSync(path.dirname(target), {recursive: true});
const isNonEmptyFile = (target) => fs.existsSync(target) && fs.statSync(target).isFile() && fs.statSync(target).size > 0;

const run = (command, args = [], options = {}) => new Promise((resolve, reject) => {
  const child = spawn(command, args, {
    cwd: options.cwd,
    env: options.env ?? process.env,
    stdio: options.capture ? ['ignore', 'pipe', 'pipe'] : 'inherit',
    windowsHide: true,
    shell: false,
  });
  let stdout = '';
  let stderr = '';
  if (options.capture) {
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
  }
  child.on('error', reject);
  child.on('close', (code) => {
    if (code === 0 || options.allowFailure) resolve({code, stdout, stderr});
    else reject(new Error(`${command} exited with code ${code}`));
  });
});

const commandExists = (command, args = ['--version']) => {
  const result = spawnSync(command, args, {stdio: 'ignore', windowsHide: true, shell: false});
  return !result.error && result.status === 0;
};

const findPython = () => {
  const candidates = IS_WINDOWS
    ? [['py', ['-3']], ['python', []], ['python3', []]]
    : [['python3', []], ['python', []]];
  for (const [command, prefix] of candidates) {
    if (commandExists(command, [...prefix, '--version'])) return {command, prefix};
  }
  return null;
};

const runPython = async (scriptName, args = [], options = {}) => {
  const python = findPython();
  if (!python) throw new Error('Python 3 was not found. Install Python 3 and make py, python, or python3 available on PATH.');
  const script = path.isAbsolute(scriptName) ? scriptName : path.join(SCRIPT_DIR, scriptName);
  return run(python.command, [...python.prefix, script, ...args], options);
};

const npmInvocation = () => {
  if (!IS_WINDOWS) return {command: 'npm', prefix: []};
  const candidates = [
    path.join(path.dirname(process.execPath), 'node_modules', 'npm', 'bin', 'npm-cli.js'),
    path.resolve(path.dirname(process.execPath), '..', 'node_modules', 'npm', 'bin', 'npm-cli.js'),
  ];
  const cli = candidates.find((candidate) => fs.existsSync(candidate));
  return cli ? {command: process.execPath, prefix: [cli]} : {command: 'npm.cmd', prefix: []};
};

const runNpm = (args, options = {}) => {
  const npm = npmInvocation();
  const cwd = options.cwd ?? process.cwd();
  const cache = process.env.NOTEBOOK_VIDEO_NPM_CACHE || path.join(cwd, '.tools', 'npm-cache');
  fs.mkdirSync(cache, {recursive: true});
  return run(npm.command, [...npm.prefix, ...args], {...options, env: {...process.env, npm_config_cache: cache}});
};

const hashFile = (target) => createHash('sha256').update(fs.readFileSync(target)).digest('hex');

const checkDeps = async () => {
  const checks = [
    ['node', process.execPath, ['--version']],
    ['npm', npmInvocation().command, [...npmInvocation().prefix, '--version']],
    ['ffmpeg', 'ffmpeg', ['-version']],
    ['ffprobe', 'ffprobe', ['-version']],
  ];
  let missing = false;
  for (const [label, command, args] of checks) {
    if (commandExists(command, args)) console.log(`[ok] ${label}`);
    else {
      console.error(`[missing] ${label}`);
      missing = true;
    }
  }
  const python = findPython();
  if (python) console.log(`[ok] python3 (${python.command}${python.prefix.length ? ` ${python.prefix.join(' ')}` : ''})`);
  else {
    console.error('[missing] Python 3 (py, python, or python3)');
    missing = true;
  }
  const major = Number(process.versions.node.split('.')[0]);
  if (major < 20) {
    console.error('[unsupported] Node.js 20 or newer is required');
    missing = true;
  }
  if (missing) process.exit(1);
  console.log(`Remotion production dependencies are ready on ${process.platform}.`);
};

// flat 为默认；cel 漫画；3.3.0 新增三套手作皮肤（亮底纸张）：journal 手账水彩 / papercut 红色剪纸 / archive 档案灯台。
const THEME_IDS = ['flat', 'cel', 'journal', 'papercut', 'archive'];
// 手作皮肤的字幕与正文用 Noto Serif SC Bold（用户字幕规范：96 px@1440 衬线粗体），需要额外字体。
const SERIF_THEMES = ['journal', 'papercut', 'archive'];

// LXGW WenKai Lite (OFL-1.1) is not stored in the repo (~28 MB). It is downloaded once
// from the official GitHub release, pinned by version and sha256, into assets/fonts/.
// Mirror: set NOTEBOOK_VIDEO_FONT_BASE_URL to a folder URL holding the same two files,
// or copy the two .ttf files into assets/fonts/ by hand.
const FONT_RELEASE = 'v1.522';
const FONT_FILES = {
  'LXGWWenKaiLite-Regular.ttf': '140c99ba4e28e817cec49bf82a0c5fcdc4fe633fb9dfda16d0ee8d59a8545f15',
  'LXGWWenKaiLite-Medium.ttf': '02eb0f8deed11b00481393f5720630ae1a44424f37f4157ea160a69a1c72a0b6',
};
const ensureFonts = async () => {
  const fontDir = path.join(SKILL_DIR, 'assets', 'fonts');
  fs.mkdirSync(fontDir, {recursive: true});
  const base = (process.env.NOTEBOOK_VIDEO_FONT_BASE_URL || `https://github.com/lxgw/LxgwWenKai-Lite/releases/download/${FONT_RELEASE}`).replace(/\/+$/, '');
  for (const [name, sha] of Object.entries(FONT_FILES)) {
    const file = path.join(fontDir, name);
    if (fs.existsSync(file) && hashFile(file) === sha) continue;
    const url = `${base}/${name}`;
    console.log(`Downloading font ${name} (LXGW WenKai Lite ${FONT_RELEASE}, OFL-1.1) from ${url}`);
    let res;
    try { res = await fetch(url, {redirect: 'follow'}); } catch (error) { res = null; }
    if (!res || !res.ok) fail(`Font download failed: ${url}\nDownload ${name} (${FONT_RELEASE}) manually from https://github.com/lxgw/LxgwWenKai-Lite/releases and put it in ${fontDir}, or set NOTEBOOK_VIDEO_FONT_BASE_URL to a mirror.`);
    const tmp = `${file}.part`;
    fs.writeFileSync(tmp, Buffer.from(await res.arrayBuffer()));
    if (hashFile(tmp) !== sha) { fs.rmSync(tmp, {force: true}); fail(`Font checksum mismatch for ${name}; expected ${FONT_RELEASE} sha256 ${sha}.`); }
    fs.renameSync(tmp, file);
  }
  return fontDir;
};

// Noto Serif SC Bold（OFL-1.1，~12 MB，SC 子集 OTF）同样按需下载、按版本与 sha256 锁定，不入库。
// 镜像：NOTEBOOK_VIDEO_SERIF_URL 指向同一个文件。
const SERIF_RELEASE = 'Serif2.003';
const SERIF_FILE = 'NotoSerifSC-Bold.otf';
const SERIF_SHA = '24693d48bdb9152f0a06b02af625638a1097abd6de4010ebba027f6e82710527';
const ensureSerif = async () => {
  const fontDir = path.join(SKILL_DIR, 'assets', 'fonts');
  fs.mkdirSync(fontDir, {recursive: true});
  const file = path.join(fontDir, SERIF_FILE);
  if (fs.existsSync(file) && hashFile(file) === SERIF_SHA) return fontDir;
  const url = process.env.NOTEBOOK_VIDEO_SERIF_URL || `https://github.com/notofonts/noto-cjk/raw/${SERIF_RELEASE}/Serif/SubsetOTF/SC/${SERIF_FILE}`;
  console.log(`Downloading font ${SERIF_FILE} (Noto Serif CJK ${SERIF_RELEASE}, OFL-1.1) from ${url}`);
  let res;
  try { res = await fetch(url, {redirect: 'follow'}); } catch (error) { res = null; }
  if (!res || !res.ok) fail(`Font download failed: ${url}\nDownload ${SERIF_FILE} from https://github.com/notofonts/noto-cjk (tag ${SERIF_RELEASE}, Serif/SubsetOTF/SC/) and put it in ${fontDir}, or set NOTEBOOK_VIDEO_SERIF_URL to a mirror.`);
  const tmp = `${file}.part`;
  fs.writeFileSync(tmp, Buffer.from(await res.arrayBuffer()));
  if (hashFile(tmp) !== SERIF_SHA) { fs.rmSync(tmp, {force: true}); fail(`Font checksum mismatch for ${SERIF_FILE}; expected ${SERIF_RELEASE} sha256 ${SERIF_SHA}.`); }
  fs.renameSync(tmp, file);
  return fontDir;
};

const newProject = async (args) => {
  // --classic（暖象牙纸面示例工程 example-project）已整体删除，给出明确报错而不是静默忽略。
  if (args.includes('--classic')) fail('--classic was removed in 3.2.0 (the warm-ivory example project is gone). Use --style=flat (default) or --style=cel.', 2);
  const styleFlag = args.find((a) => a.startsWith('--style='));
  const style = styleFlag ? styleFlag.slice('--style='.length) : 'flat';
  if (!THEME_IDS.includes(style)) fail(`Unknown style "${style}". Valid values: ${THEME_IDS.join(', ')}`, 2);
  const targetArg = args.find((a) => !a.startsWith('--style='));
  if (!targetArg) fail('Usage: notebook-video new-project PROJECT_DIRECTORY [--style=flat|cel|journal|papercut|archive]', 2);
  const target = resolvePath(targetArg);
  if (fs.existsSync(target)) {
    if (!fs.statSync(target).isDirectory()) fail(`Target exists and is not a directory: ${target}`);
    if (fs.readdirSync(target).length > 0) fail(`Target directory must be empty to prevent stale project files: ${target}`);
  } else fs.mkdirSync(target, {recursive: true});

  // The lecture template is the only project template: pure code-drawn SVG scenes
  // over locked theme backgrounds that work in every environment.
  fs.cpSync(path.join(SKILL_DIR, 'assets', 'lecture-template'), target, {
    recursive: true, force: true,
    // A developer checkout may have node_modules installed inside the template; never copy it.
    filter: (src) => !src.split(path.sep).includes('node_modules'),
  });
  // Theme selection rewrites the one-line theme switch in the copied project.
  if (style !== 'flat') {
    const activePath = path.join(target, 'src', 'theme', 'active.ts');
    if (!fs.existsSync(activePath)) fail(`Theme switch is missing in the copied template: ${activePath}`);
    fs.writeFileSync(activePath, `import {THEME} from './${style}';\nexport {THEME};\n`);
  }
  const fontDir = await ensureFonts();
  const publicDir = path.join(target, 'public');
  fs.mkdirSync(publicDir, {recursive: true});
  for (const name of [
    'LXGWWenKaiLite-Regular.ttf',
    'LXGWWenKaiLite-Medium.ttf',
    'LICENSE-OFL-1.1-LXGW.txt',
  ]) fs.copyFileSync(path.join(fontDir, name), path.join(publicDir, name));
  if (SERIF_THEMES.includes(style)) {
    const serifDir = await ensureSerif();
    fs.copyFileSync(path.join(serifDir, SERIF_FILE), path.join(publicDir, SERIF_FILE));
    fs.copyFileSync(path.join(serifDir, 'LICENSE-OFL-1.1-NotoSerifSC.txt'), path.join(publicDir, 'LICENSE-OFL-1.1-NotoSerifSC.txt'));
  }
  fs.mkdirSync(path.join(target, 'renders'), {recursive: true});
  console.log(`Created official lecture-template Remotion notebook project (pure code-drawn SVG default): ${target}`);
  console.log(`Theme locked to "${style}". Style contract: references/theme-${style}.md.`);
  console.log('Multi-zone lecture composition rules: references/lecture-composition.md. Image generation stays an optional add-on offered separately.');
  console.log('Preserve the engine, background, subtitle, chrome, asset gate, audio tree and frame conventions. Replace topic content, visual plan, registered imagery and semantic scene objects.');
  console.log('Narration audio is intentionally not bundled. Generate or supply licensed audio, then run sync before rendering.');
};

const syncProjectAssets = async ([projectArg]) => {
  if (!projectArg) fail('Usage: notebook-video sync PROJECT_DIRECTORY', 2);
  const project = resolvePath(projectArg);
  const pairs = [
    ['audio/narration.mp3', 'public/narration.mp3'],
    ['manifests/caption-cues.json', 'src/caption-cues.json'],
  ];
  const required = [...pairs.map(([from]) => from), 'audio/narration.mp3.json'];
  for (const rel of required) {
    const source = path.join(project, ...rel.split('/'));
    if (!isNonEmptyFile(source)) fail(`Required render input is missing or empty: ${source}`);
  }
  for (const [from, to] of pairs) {
    const source = path.join(project, ...from.split('/'));
    const target = path.join(project, ...to.split('/'));
    ensureParent(target);
    fs.copyFileSync(source, target);
    if (hashFile(source) !== hashFile(target)) fail(`Render input sync failed: ${from} -> ${to}`);
  }
  console.log('Synchronized canonical render inputs into public/ and src/.');
};

const prepareBrowser = async ([projectArg]) => {
  if (!projectArg) fail('Usage: notebook-video prepare-browser PROJECT_DIRECTORY', 2);
  const project = resolvePath(projectArg);
  const remotionCli = path.join(project, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
  if (!fs.existsSync(remotionCli)) await runNpm(['ci', '--no-audit', '--no-fund'], {cwd: project});
  if (!fs.existsSync(remotionCli)) fail(`Remotion CLI is missing after npm ci: ${remotionCli}`);
  const args = [remotionCli, 'browser', 'ensure'];
  const browserExecutable = process.env.REMOTION_BROWSER_EXECUTABLE;
  if (browserExecutable) {
    const resolved = resolvePath(browserExecutable);
    if (!fs.existsSync(resolved)) fail(`REMOTION_BROWSER_EXECUTABLE does not exist: ${resolved}`);
    args.push(`--browser-executable=${resolved}`);
  }
  await run(process.execPath, args, {cwd: project});
  console.log('Remotion rendering browser is ready.');
};

const suggestedConcurrency = () => Math.max(2, Math.min(6, Math.floor(os.availableParallelism() / 2)));

// Remotion CLI entry point is a POSITIONAL argument:
//   remotion render [<entry-point|serve-url>] [<composition-id>] [<output-location>]
// There is NO `--entry-point` flag in @remotion/cli 4.0.x. An unknown `--entry-point=…`
// is not rejected: findEntryPoint() only looks at argv positions (see
// node_modules/@remotion/cli/dist/entry-point.js), so the bogus flag falls through to the
// 3rd-priority "common paths" lookup and the render still succeeds — against the wrong
// file. Measured on @remotion/cli 4.0.526: `still ProbeColor out.png --entry-point=alt/entry.tsx`
// exits 0 and renders src/index.tsx instead (log: "Selected …src\index.tsx as the entry
// point because file exists and is a common entry point and no entry point was explicitly
// selected"). Passing it positionally selects the requested file.
const REMOTION_ENTRY_POINT = 'src/index.tsx';

// Color metadata contract for the delivery file (also applied by the template's
// package.json scripts and documented in references/windows-compatibility.md):
//   H.264 + yuv420p + bt709 + limited (tv) range, the de-facto standard for SDR
//   web video. Remotion's own default is `--color-space=default`, which emits NO
//   color flags at all: the encoder then tagged frames yuvj420p (full range) while
//   players that find no matrix fall back to BT.601, so saturated colors shifted
//   slightly in strict players. `bt709` makes the renderer pass
//   `-colorspace:v bt709 -color_primaries:v bt709 -color_trc:v bt709 -color_range tv`
//   and (since @remotion/renderer 4.0.83) actually convert the pixels to limited
//   range via `zscale=matrix=709:matrixin=709:range=limited`, so the four flags and
//   the pixel data agree.
const REMOTION_COLOR_ARGS = ['--color-space=bt709'];

// The tag pass below copies the video stream instead of re-encoding it. FFmpeg ignores
// `-color_primaries/-color_trc/-colorspace/-color_range` on a copied stream ("has not
// been used for any stream"), and Remotion's own final stitch re-muxes with `-c:v copy`
// the same way: measured on @remotion/cli 4.0.526, `--color-space=bt709` alone still
// leaves `color_primaries` and `color_transfer` reported as `unknown`. Rewriting the SPS
// VUI with the h264_metadata bitstream filter sets what the MP4 `colr` atom and every
// player actually read, so all four fields end up self-consistent:
// yuv420p / tv / bt709 / bt709 / bt709. FFmpeg builds since 3.4 ship this filter.
const H264_COLOR_TAG_FILTER = 'h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0';

// 交付文件的**色彩契约**（四项元数据必须就是这个组合，见 references/composition-gate.md §6）。
// 前面两道（`--color-space=bt709` + `h264_metadata` 回写）只是**生产者**；
// 这里是**交付前的断言**——只有把契约写死在门禁里，"谁把参数删了"才会被立刻发现：
//   · 删掉 `--color-space=bt709` → 流回到 yuvj420p / pc / bt470bg，transfer 与 primaries 变 unknown；
//   · 删掉 `h264_metadata` 回写 → range/space 还是 bt709，但 transfer / primaries 仍是 unknown
//     （实测：`--color-space=bt709` 单独一条盖不住这两项，Remotion 最后一道 stitch 是 `-c:v copy`）。
// 为什么只认 `tv + bt709×3`、不接受"别的自洽组合"：
//   ① 交付画布都是 SDR 网络播放，`pc`（满幅）会让严格播放器把信号当有限幅解释 → 对比度/饱和色偏移，
//      正是上一轮修掉的那个缺陷；`bt470bg`（BT.601）与 `bt709` 的矩阵不同，同样偏色；
//   ② "自洽"无法只从这四项推出来：`pc + bt709×3` 字段上也自洽，但它不是本链路产的片
//      （渲染端已按 `range=limited` 转换过像素），放行它等于把"标错范围"的片子当合格；
//   ③ 门禁的作用是抓**漂移**，判据就该是精确等于契约，而不是"看起来合理"。
// 非交付的中间产物（Remotion 自己 stitch 出来的 raw mp4）本来就不满足这四项，所以这条断言
// 只挂在 `validate-video`（交付门）上，不去卡渲染路径。
const DELIVERY_COLOR_CONTRACT = {
  color_range: 'tv',
  color_space: 'bt709',
  color_transfer: 'bt709',
  color_primaries: 'bt709',
};

// Applies the color tags to a file Remotion just wrote, in place and without re-encoding.
// Only the **delivery** render paths call this (`render`, `render-range`, `showcase`) — see
// remotionRender's `colorTagged` flag. The debug artifacts (`review-frames`, `benchmark-render`)
// are not tagged: nobody asserts the color contract on them (that assertion lives in
// `validate-video`, the delivery gate), and the extra ffmpeg pass per artifact is pure cost.
// `showcase` **is** tagged since v3.1.1: its mp4 is the contact-sheet deliverable (the file you
// share or publish next to a release), so it has to meet the same contract as a film.
// Trade-off, written down because it is easy to forget: an untagged review clip reports
// `color_transfer=unknown` in ffprobe and may look slightly more saturated when a player
// falls back to BT.601 — measure color on the tagged delivery file, not on the review clip.
const applyColorTags = async (target) => {
  const tagged = `${target}.color-tagged.mp4`;
  try {
    await run('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-i', target, '-map', '0:v:0', '-map', '0:a?', '-c', 'copy', '-bsf:v', H264_COLOR_TAG_FILTER, tagged]);
    fs.renameSync(tagged, target);
  } catch (error) {
    fs.rmSync(tagged, {force: true});
    // 这一步失败**不是渲染失败**：视频本体已经完整落在 target 上了（Remotion 已退出 0）。
    // 话必须说清，否则下一个人会以为要整片重渲（那要几十分钟）—— 实际只需重做这一段回写。
    throw new Error(
      `视频已经渲染完成，只是「色彩元数据回写」失败：${target} 本身是完整可用的，` +
      `但它的 H.264 流缺 bt709 的 colr/VUI 标记（交付门 validate-video 会因此判不合格）。\n` +
      `修法（不必重渲）：\n  ffmpeg -y -i "${target}" -map 0:v:0 -map 0:a? -c copy -bsf:v ${H264_COLOR_TAG_FILTER} "${target}.retag.mp4"\n` +
      `  然后把 .retag.mp4 改名覆盖回 ${path.basename(target)}\n` +
      `底层错误：${error && error.message ? error.message : error}`,
    );
  }
};

// 3.5.0：真卷页能力探针（scripts/fx-browser.mjs）。同一进程内只探一次；结论写 renders/.fx-probe.json 供 make-video 写报告。
const fxCache = new Map();
const fxFor = async (project, {force = false, quiet = false} = {}) => {
  if (!force && fxCache.has(project)) return fxCache.get(project);
  const remotionCli = path.join(project, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
  let remotionVersion = '';
  try { remotionVersion = JSON.parse(fs.readFileSync(path.join(project, 'node_modules', 'remotion', 'package.json'), 'utf8')).version; } catch { /* 未安装 */ }
  const runStill = async (args) => {
    if (!fs.existsSync(remotionCli)) return {code: 1, out: `Remotion CLI missing: ${remotionCli}`};
    const r = await run(process.execPath, [remotionCli, 'still', REMOTION_ENTRY_POINT, ...args], {cwd: project, capture: true, allowFailure: true});
    return {code: r.code, out: `${r.stdout}\n${r.stderr}`};
  };
  const fx = await resolveFx({project, remotionVersion, runStill, force});
  if (!quiet && fx.used) console.log(fx.on ? `真卷页（pageturn / peel）：已开启 · ${fx.browser}` : `⚠ 真卷页未开启：${fx.reason}`);
  fxCache.set(project, fx);
  return fx;
};

// 成片总帧数（src/shots.ts 的 SHOT_TOTAL）；读不到就返回 null（窗口不截尾，Remotion 自己会报越界）。
const readFilmDuration = (project) => {
  try { const m = fs.readFileSync(path.join(project, 'src', 'shots.ts'), 'utf8').match(/SHOT_TOTAL\s*=\s*(\d+)/); return m ? Number(m[1]) : null; } catch { return null; }
};

const fxProbe = async ([projectArg, ...rest]) => {
  if (!projectArg) fail('Usage: notebook-video fx-probe PROJECT_DIRECTORY [--force]', 2);
  const project = resolvePath(projectArg);
  const fx = await fxFor(project, {force: rest.includes('--force'), quiet: true});
  console.log(JSON.stringify(fx, null, 2));
};

// 3.7.0：FillGate 的浏览器日志按镜头去重。fill-gate.tsx 每个标签每镜只打一条 `[FillGate] underfilled <镜号> …`，
// 这里把所有标签的这类行吞掉、记下镜号，渲染结束汇总成**一行**；其他输出原样透传。
const runRemotionFiltered = (nodeArgs, cwd) => new Promise((resolve, reject) => {
  const child = spawn(process.execPath, nodeArgs, {cwd, env: process.env, stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true, shell: false});
  const shots = new Set();
  let other = 0;
  const pump = (src, dst) => {
    let buf = '';
    src.setEncoding('utf8');
    const emit = (line) => {
      if (line.includes('[FillGate]')) {
        const m = line.match(/underfilled\s+(\S+)/);
        if (m) shots.add(m[1]); else other += 1;
        return;
      }
      dst.write(line + '\n');
    };
    src.on('data', (chunk) => {
      buf += chunk;
      let i;
      while ((i = buf.indexOf('\n')) >= 0) { emit(buf.slice(0, i)); buf = buf.slice(i + 1); }
    });
    src.on('end', () => { if (buf) emit(buf); buf = ''; });
  };
  pump(child.stdout, process.stdout);
  pump(child.stderr, process.stderr);
  child.on('error', reject);
  child.on('close', (code) => {
    if (shots.size) {
      const ids = [...shots].sort((a, b) => a.localeCompare(b, 'en', {numeric: true}));
      console.warn(`FillGate: ${ids.length} shot${ids.length > 1 ? 's' : ''} (${ids.join(',')}) bottom-quarter underfilled${other ? ` (+${other} other FillGate lines)` : ''}`);
    } else if (other) console.warn(`FillGate: ${other} message(s) (no underfilled shot)`);
    if (code === 0) resolve({code}); else reject(new Error(`${process.execPath} exited with code ${code}`));
  });
});

const remotionRender = async ({project, composition, output, frames, concurrency, colorTagged = false, scale, fxMode = 'auto', crf = 16, muted = false}) => {
  const remotionCli = path.join(project, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
  if (!fs.existsSync(remotionCli)) await runNpm(['ci', '--no-audit', '--no-fund'], {cwd: project});
  if (!fs.existsSync(remotionCli)) fail(`Remotion CLI is missing after npm ci: ${remotionCli}`);
  ensureParent(output);
  const nodeArgs = [];
  if (process.env.REMOTION_USE_NETWORK_SHIM === '1') {
    const shim = path.join(project, 'remotion-network-shim.cjs');
    if (!fs.existsSync(shim)) fail(`Optional network shim is missing: ${shim}`);
    nodeArgs.push('--require', shim);
  }
  // 3.5.0 真卷页（pageturn / peel，WebGPU）：只有成片 composition、且本片用到卷页时才探测；
  // 探针通过 → 换完整版 Chromium + 软件 GPU 参数并传 {nvFx:'on'}，并发压到 1（完整版 Chrome 多标签会花屏，见 fx-browser.mjs）；
  // 不通过 → 照常渲染（合成里自动退回 slide / drop）。
  // fxMode：auto = 探针说行就开；off = 不开（整片快速渲染那一遍）；on = 必须开（卷页片段那一遍，调用方已确认探针通过）。
  const fx = composition === 'NotebookVideoFilm' && fxMode !== 'off' ? await fxFor(project) : {on: false};
  nodeArgs.push(remotionCli, 'render', REMOTION_ENTRY_POINT, composition, output, '--codec=h264', `--crf=${crf}`, ...REMOTION_COLOR_ARGS, `--concurrency=${fx.on ? FX_CONCURRENCY : concurrency}`);
  if (muted) nodeArgs.push('--muted');
  if (frames) nodeArgs.push(`--frames=${frames}`);
  // 缩放必须是**十进制字面量**：CLI 不接受分数字面量（`--scale=4/3` 会被判非法参数而拒绝渲染），
  // 所以这里传的是 1.3333333333333333（= 2560/1920，四舍五入回正好 2560×1440）。
  if (scale) nodeArgs.push(`--scale=${scale}`);
  if (fx.on) nodeArgs.push(...fx.args);
  // Browser resolution: explicit env wins, then the local Remotion cache that
  // `prepare-browser` already populated — never trigger a fresh 100MB+ shell
  // download when a cached copy exists on this machine.
  let browserExecutable = process.env.REMOTION_BROWSER_EXECUTABLE;
  if (!browserExecutable && process.platform === 'win32') {
    const cached = path.join(process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local'), 'remotion-browser', 'chrome-headless-shell', 'win64', 'chrome-headless-shell.exe');
    if (fs.existsSync(cached)) browserExecutable = cached;
  }
  if (browserExecutable && !fx.on) {
    const resolved = resolvePath(browserExecutable);
    if (!fs.existsSync(resolved)) fail(`REMOTION_BROWSER_EXECUTABLE does not exist: ${resolved}`);
    nodeArgs.push(`--browser-executable=${resolved}`);
  }
  await runRemotionFiltered(nodeArgs, project);
  if (colorTagged) await applyColorTags(output);
};

const render = async ([projectArg, outputArg, composition = 'NotebookVideoFilm']) => {
  if (!projectArg || !outputArg) fail('Usage: notebook-video render PROJECT_DIRECTORY OUTPUT_MP4 [COMPOSITION_ID]', 2);
  const project = resolvePath(projectArg);
  const output = resolvePath(outputArg);
  await syncProjectAssets([project]);
  // 中间文件放系统临时目录。Remotion 的 faststart 第二遍要回写文件头，网络 / FUSE 盘（实测 JuiceFS）上会
  // `Error writing trailer: Input/output error`，整片渲完却拿不到文件。
  const raw = path.join(os.tmpdir(), `nv-remotion-raw-${process.pid}.mp4`);
  fs.mkdirSync(path.dirname(raw), {recursive: true});
  ensureParent(output);
  const concurrency = Number(process.env.REMOTION_CONCURRENCY || suggestedConcurrency());
  console.log(`Rendering at concurrency ${concurrency}. Override with REMOTION_CONCURRENCY after running benchmark-render.`);
  // 交付路径：这是"真正出交付物"的渲染，色彩元数据必须打全（见 applyColorTags）。
  // NOTEBOOK_VIDEO_SCALE=0.75 → 1920×1080 交付（缺省 2560×1440）
  const scaleArg = process.env.NOTEBOOK_VIDEO_SCALE || undefined;
  // 3.5.0 真卷页：完整版 Chrome + 软件 GPU 每帧约 3 s（实测 2 核 arm64、2560×1440，缺省 Headless Shell 约 0.25 s），
  // 整片都用它会慢 10 倍以上。所以「快速整片 + 卷页片段 + 按帧号拼接」：
  //   ① 整片照常用 Headless Shell 渲（卷页处是退回的 slide，马上被替换），近无损 crf 8；
  //   ② 每个卷页窗口（22 帧）用完整版 Chrome 单独渲（crf 8、静音）；
  //   ③ ffmpeg 按帧号 split/trim/concat 拼回，只在这一遍编码到交付质量（crf 16）。
  const fx = composition === 'NotebookVideoFilm' ? await fxFor(project) : {on: false};
  const total = composition === 'NotebookVideoFilm' ? readFilmDuration(project) : null;
  const windows = fx.on ? curlWindows(project, total ?? Infinity) : [];
  if (windows.length) {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'nv-fx-'));
    const fastRaw = path.join(tmpDir, 'fast.mp4');
    console.log(`真卷页：整片快速渲染 + ${windows.length} 个卷页片段（${windows.map(([a, b]) => `${a}-${b}`).join(', ')}）拼接`);
    await remotionRender({project, composition, output: fastRaw, concurrency, scale: scaleArg, fxMode: 'off', crf: 8});
    const segs = [];
    for (const [a, b] of windows) {
      const seg = path.join(tmpDir, `curl-${a}.mp4`);
      await remotionRender({project, composition, output: seg, frames: `${a}-${b}`, concurrency: FX_CONCURRENCY, scale: scaleArg, fxMode: 'on', crf: 8, muted: true});
      segs.push(seg);
    }
    await run('ffmpeg', spliceArgs(fastRaw, segs, windows, raw));
    await applyColorTags(raw);
    fs.rmSync(tmpDir, {recursive: true, force: true});
  } else {
    await remotionRender({project, composition, output: raw, concurrency, colorTagged: true, scale: scaleArg});
  }
  // 响度目标可调（NOTEBOOK_VIDEO_LUFS）。缺省 −16 LUFS、真峰 −1.5 dBTP；3.6.0 起静音占位旁白的片子也用 −16
  //（AES TD1004：流媒体 −16…−20，−23/−24 在手机上不够响）。
  const LUFS = process.env.NOTEBOOK_VIDEO_LUFS || '-16';
  // 两遍响度规范化：先测（linear 模式需要 measured_* 才能同时打准 LUFS 与真峰）
  const probe = await run('ffmpeg', ['-hide_banner', '-i', raw, '-af', `loudnorm=I=${LUFS}:LRA=11:TP=-1.5:print_format=json`, '-f', 'null', '-'], {capture: true, allowFailure: true});
  let loudFilter = `loudnorm=I=${LUFS}:LRA=11:TP=-1.5`;
  const probeJson = `${probe.stdout || ''}
${probe.stderr || ''}`.match(/\{[\s\S]*\}/);
  if (probeJson) {
    try {
      const m = JSON.parse(probeJson[0]);
      loudFilter = `loudnorm=I=${LUFS}:LRA=11:TP=-1.5:measured_I=${m.input_i}:measured_TP=${m.input_tp}:measured_LRA=${m.input_lra}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true`;
    } catch { console.warn('loudnorm 测量解析失败，退回单遍模式'); }
  }
  // 末尾只是换封装：视频流已经是 bt709/limited 的 yuv420p 并带齐四项标记（见 applyColorTags），
  // 这里 `-c:v copy` 会原样带走；音频重新编码为 AAC 并做一次响度规范化。
  // 最后这一步的 `+faststart` 同样要回写文件头：直接写到 FUSE 盘（JuiceFS）上的交付路径会在收尾时
  // `Error writing trailer: Input/output error`（cell 演示片实测：2020 帧渲完、成片拿不到）。
  // 所以成品也先落在临时目录，写完再整文件拷到交付路径（顺序写，FUSE 盘没问题）。
  const finalTmp = path.join(os.tmpdir(), `nv-final-${process.pid}.mp4`);
  try {
    await run('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-i', raw, '-map', '0:v:0', '-map', '0:a:0', '-c:v', 'copy', '-af', loudFilter, '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', finalTmp]);
    fs.copyFileSync(finalTmp, output);
    fs.rmSync(raw, {force: true});   // 只在成功后删：失败时留着 raw，可以只重跑这一步而不必重渲
  } finally {
    fs.rmSync(finalTmp, {force: true});
  }
  console.log(`Rendered and normalized: ${output}`);
};

const renderRange = async ([projectArg, outputArg, startArg, endArg, composition = 'NotebookVideoFilm']) => {
  if (!projectArg || !outputArg || startArg === undefined || endArg === undefined) fail('Usage: notebook-video render-range PROJECT_DIRECTORY OUTPUT_MP4 START_FRAME END_FRAME [COMPOSITION_ID]', 2);
  const start = Number(startArg), end = Number(endArg);
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end < start) fail(`Invalid frame range: ${startArg}-${endArg}`);
  const project = resolvePath(projectArg), output = resolvePath(outputArg);
  await syncProjectAssets([project]);
  const concurrency = Number(process.env.REMOTION_CONCURRENCY || suggestedConcurrency());
  // 交付路径（短片段也常被直接拿去交付/送审）：回写色彩元数据。
  await remotionRender({project, composition, output, frames: `${start}-${end}`, concurrency, colorTagged: true});
  console.log(`Rendered review range ${start}-${end}: ${output}`);
};

const benchmarkRender = async ([projectArg, composition = 'NotebookVideoFilm']) => {
  if (!projectArg) fail('Usage: notebook-video benchmark-render PROJECT_DIRECTORY [COMPOSITION_ID]', 2);
  const project = resolvePath(projectArg);
  await syncProjectAssets([project]);
  const max = Math.max(2, Math.min(6, os.availableParallelism()));
  const candidates = [...new Set([2, 4, 6].filter((value) => value <= max).concat(max))].sort((a, b) => a - b);
  const results = [];
  for (const concurrency of candidates) {
    const output = path.join(project, 'renders', `.benchmark-c${concurrency}.mp4`);
    const started = Date.now();
    // 调试产物：只为了测速，渲完就删 —— 不回写色彩元数据（那是交付路径的事）。
    await remotionRender({project, composition, output, frames: '0-89', concurrency});
    const seconds = (Date.now() - started) / 1000;
    fs.rmSync(output, {force: true});
    results.push({concurrency, seconds});
    console.log(`concurrency ${concurrency}: ${seconds.toFixed(1)}s`);
  }
  results.sort((a, b) => a.seconds - b.seconds);
  console.log(`Recommended: REMOTION_CONCURRENCY=${results[0].concurrency}`);
};

const reviewFrames = async ([projectArg, outputArg, startArg, endArg, composition = 'NotebookVideoFilm']) => {
  if (!projectArg || !outputArg || startArg === undefined || endArg === undefined) fail('Usage: notebook-video review-frames PROJECT_DIRECTORY OUTPUT_MP4 START_FRAME END_FRAME [COMPOSITION_ID]', 2);
  const start = Number(startArg), end = Number(endArg);
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end < start) fail(`Invalid frame range: ${startArg}-${endArg}`);
  const project = resolvePath(projectArg), output = resolvePath(outputArg);
  await syncProjectAssets([project]);
  const concurrency = Number(process.env.REMOTION_CONCURRENCY || suggestedConcurrency());
  const fps = Number(process.env.NOTEBOOK_VIDEO_FPS || 30);
  // 调试产物（看画面对不对，不是拿去交付）：不回写色彩元数据。
  // 代价写在 applyColorTags 上方：这条片子的 ffprobe 会显示 color_transfer=unknown，
  // 要验色彩契约请验**交付文件**（validate-video 也只认交付文件）。
  await remotionRender({project, composition, output, frames: `${start}-${end}`, concurrency});
  // 一次 bundle/一次浏览器：范围视频 + 自动接触片一步到位。
  // 多帧视觉检查用本命令替代逐帧 still，实测约省 3 倍时间（bundle 与浏览器开销只付一次）。
  const contact = path.join(path.dirname(output), path.basename(output).replace(/\.mp4$/i, '') + '-contact.jpg');
  await makeContactSheet(output, contact, (end - start + 1) / fps);
  console.log(`Rendered review range ${start}-${end}: ${output}`);
  console.log(`Contact sheet: ${contact}`);
};

const makeContactSheet = async (video, contact, durationSec) => {
  const count = durationSec > 60 ? 24 : 12;
  const tile = count === 24 ? '4x6' : '4x3';
  const rate = (count / durationSec).toFixed(12).replace(/0+$/, '').replace(/\.$/, '');
  ensureParent(contact);
  await run('ffmpeg', ['-y', '-loglevel', 'error', '-i', video, '-vf', `fps=${rate},scale=640:360,tile=${tile}`, '-frames:v', '1', contact]);
  return contact;
};

const validateVideo = async ([videoArg, expectedArg, contactArg]) => {
  if (!videoArg || !expectedArg) fail('Usage: notebook-video validate-video VIDEO_MP4 EXPECTED_DURATION [CONTACT_SHEET_JPG]', 2);
  const video = resolvePath(videoArg);
  const expected = Number(expectedArg);
  if (!Number.isFinite(expected) || expected <= 0) fail(`EXPECTED_DURATION must be a positive number: ${expectedArg}`);
  if (!isNonEmptyFile(video)) fail(`Video is missing or empty: ${video}`);
  const contact = contactArg ? resolvePath(contactArg) : path.join(path.dirname(video), 'contact-sheet.jpg');
  const probe = await run('ffprobe', ['-v', 'error', '-show_entries', 'stream=codec_name,codec_type,width,height,r_frame_rate,duration,sample_rate,channels,pix_fmt,color_range,color_space,color_transfer,color_primaries', '-show_entries', 'format=duration', '-of', 'json', video], {capture: true});
  const data = JSON.parse(probe.stdout);
  const streams = data.streams ?? [];
  const videoStream = streams.find((s) => s.codec_type === 'video');
  const audioStream = streams.find((s) => s.codec_type === 'audio');
  if (!videoStream || !audioStream) fail('Both video and audio streams are required.');
  if (videoStream.codec_name !== 'h264' || audioStream.codec_name !== 'aac') fail('Expected H.264 video and AAC audio.');
  // One locked delivery canvas (3.2.0+): 2560x1440 (16:9).
  // 同一张 16:9 画布的 1080p 交付（NOTEBOOK_VIDEO_SCALE=0.75，make-video 的缺省）也接受；其他尺寸 / 比例一律拒。
  const canvasOk = (videoStream.width === 2560 && videoStream.height === 1440) || (videoStream.width === 1920 && videoStream.height === 1080);
  if (!canvasOk) fail(`Expected 2560x1440 or 1920x1080 (16:9), got ${videoStream.width}x${videoStream.height}.`);
  const expectedFps = Number(process.env.NOTEBOOK_VIDEO_FPS || 30);
  if (videoStream.r_frame_rate !== `${expectedFps}/1`) fail(`Expected ${expectedFps}fps, got ${videoStream.r_frame_rate}.`);
  if (String(audioStream.sample_rate) !== '48000' || Number(audioStream.channels) !== 2) fail('Expected 48kHz stereo audio.');
  const duration = Number(data.format?.duration);
  if (Math.abs(duration - expected) > 0.2) fail(`Duration mismatch: ${duration} vs ${expected}`);
  console.log(`container valid: H.264/AAC ${videoStream.width}x${videoStream.height} ${expectedFps}fps, ${duration.toFixed(3)}s`);

  // 色彩断言：四项元数据必须精确等于交付契约（理由见 DELIVERY_COLOR_CONTRACT 上方的注释）。
  // 缺字段的流 ffprobe 直接不返回该项 → 一律按 unknown 报出来，不静默放过。
  const colorRows = Object.entries(DELIVERY_COLOR_CONTRACT);
  const colorBad = colorRows.filter(([field, expected]) => videoStream[field] !== expected);
  if (colorBad.length) {
    fail(
      `Color metadata does not match the delivery contract (${colorBad.length} of ${colorRows.length} fields wrong):\n` +
        colorBad.map(([field, expected]) => `  ${field} = ${videoStream[field] ?? 'unknown'} (合同要求 ${expected})`).join('\n') +
        `\nGiven: pix_fmt=${videoStream.pix_fmt ?? 'unknown'}. Re-render through \`notebook-video render\` (it passes --color-space=bt709 and rewrites the SPS VUI with h264_metadata).`
    );
  }
  console.log(`color valid: ${colorRows.map(([field]) => `${field}=${videoStream[field]}`).join(' ')} (pix_fmt=${videoStream.pix_fmt ?? 'unknown'})`);

  const black = await run('ffmpeg', ['-hide_banner', '-i', video, '-vf', 'blackdetect=d=0.15:pix_th=0.02', '-an', '-f', 'null', '-'], {capture: true, allowFailure: true});
  const blackLog = `${black.stdout}\n${black.stderr}`;
  if (/black_(start|end)/.test(blackLog)) fail(`Black frames detected:\n${blackLog.match(/.*black_(?:start|end).*$/gm)?.join('\n') ?? blackLog}`);

  const loud = await run('ffmpeg', ['-hide_banner', '-i', video, '-af', 'loudnorm=I=-16:LRA=11:TP=-1.5:print_format=summary', '-f', 'null', '-'], {capture: true, allowFailure: true});
  const loudLog = `${loud.stdout}\n${loud.stderr}`;
  const integrated = Number(loudLog.match(/Input Integrated:\s*([-0-9.]+) LUFS/)?.[1]);
  const peak = Number(loudLog.match(/Input True Peak:\s*([-0-9.]+) dBTP/)?.[1]);
  if (!Number.isFinite(integrated) || !Number.isFinite(peak)) fail('Unable to parse loudness analysis from FFmpeg output.');
  const lufsTarget = Number(process.env.NOTEBOOK_VIDEO_LUFS || -16);
  if (integrated < lufsTarget - 2 || integrated > lufsTarget + 2) fail(`Integrated loudness outside target range: ${integrated} LUFS (target ${lufsTarget}; set NOTEBOOK_VIDEO_LUFS to validate another target)`);
  if (peak > -1.5) fail(`True peak above the documented -1.5 dBTP ceiling: ${peak} dBTP`);
  console.log(`audio valid: ${integrated.toFixed(1)} LUFS, ${peak.toFixed(1)} dBTP`);

  await makeContactSheet(video, contact, expected);
  console.log('No black frames detected.');
  console.log(`Contact sheet: ${contact}`);
};

const packageProject = async ([projectArg, outputArg]) => {
  if (!projectArg || !outputArg) fail('Usage: notebook-video package PROJECT_DIRECTORY OUTPUT_ZIP', 2);
  const project = resolvePath(projectArg);
  const output = resolvePath(outputArg);
  ensureParent(output);
  await runPython('package-project.py', [project, output]);
};

const pythonCommandMap = new Map([
  ['validate-skill', ['validate-skill-consistency.py']],
  ['build-semantic-captions', ['build-semantic-captions.py']],
  ['validate-layering', ['validate-layering.py']],
  ['validate-visual-plan', ['validate-visual-plan.py']],
  ['validate-caption-sync', ['validate-caption-sync.py']],
  ['validate-semantic-breaks', ['validate-semantic-breaks.py']],
  ['match-timing', ['match-timing.py']],
  ['resolve-shots', ['resolve-shots.py']],
  ['validate-shot-motion', ['validate-shot-motion.py']],
  ['validate-composition', ['validate-composition.py']],
  // v3.0.2 补登记：这两道也是构建期必跑门禁，之前只能直接 `python scripts/…` 调用，CLI 里点不到。
  ['validate-frame-props', ['validate-frame-props.py']],
  ['validate-audio-levels', ['validate-audio-levels.py']],
  // v3.1 新增：呈现效果门禁（T1 纯算术：时间接近 / 字幕阅读预算 / 可读性底线），见 references/presentation-gate.md
  ['validate-presentation', ['validate-presentation.py']],
  // 3.3.0：导演层门禁、真实素材检索（Commons / Openverse）、渲染后 OCR 可读性抽查
  ['validate-treatment', ['validate-treatment.py']],
  ['validate-opening', ['validate-opening.py']],
  ['silent-timing', ['silent-timing.py']],
  ['validate-media', ['validate-media.py']],
  ['commons', ['commons-search.py']],
  ['prepare-media', ['prepare-media.py']],
  ['validate-ocr', ['validate-ocr.py']],
  // 3.4.0：背景库门禁（来源 / 许可 / sha256 / 亮底 / 字幕区对比度；--shots 查相邻镜重复）
  ['validate-backgrounds', ['validate-backgrounds.py']],
]);

// 交付路径收口：CLI 的 `validate-semantic-breaks` 是渲染后质检链（SKILL.md
// "Validation after rendering"、references/subtitle-timing.md）的固定入口。底层短语规则
// 找不到 BudouX 时原本只是 SKIPPED + rc=0，只有 `--require-budoux` 才硬失败 —— 而交付链上
// 没有任何调用方带这个开关，这正是本门禁要消灭的"跳过即静默放行"降级路径。现在由 CLI 收口：
//   · 从 CAPTION_CUES_JSON 所在目录逐级向上探测 node_modules/budoux/module/index.js
//     （判据与 validate-semantic-breaks.py 的 find_budoux_root 同一 marker）；
//   · 探测到 → 注入 `--budoux-dir <该 node_modules> --require-budoux`（真正跑短语规则）；
//   · 探测不到 → 仍然注入 `--require-budoux`，缺依赖直接硬失败，报错会写明装依赖/--budoux-dir 两条修法。
// 调用方已显式传 `--require-budoux` 或 `--no-budoux`（本地夹具刻意跳过短语规则）时原样放行。
const semanticBreaksArgs = (args) => {
  if (args.some((a) => a === '--require-budoux' || a === '--no-budoux')) return args;
  // 已显式指定 --budoux-dir 时不再自动注入：后传的 --budoux-dir 会覆盖它，反而把调用方
  // 精心指定的目录换掉；此时只补上缺依赖必败的 --require-budoux。
  if (args.some((a) => a === '--budoux-dir' || a.startsWith('--budoux-dir='))) return [...args, '--require-budoux'];
  const cuesArg = args.find((a) => !a.startsWith('--'));
  if (!cuesArg) return args;
  const marker = path.join('budoux', 'module', 'index.js');
  let current = path.dirname(resolvePath(cuesArg));
  let budouxModules = null;
  for (let depth = 0; depth < 8; depth += 1) {
    const modules = path.join(current, 'node_modules');
    if (fs.existsSync(path.join(modules, marker))) { budouxModules = modules; break; }
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return budouxModules
    ? [...args, '--budoux-dir', budouxModules, '--require-budoux']
    : [...args, '--require-budoux'];
};

// 接触表交付规格。`NotebookVideoShowcase` 的原生画布是 1920×1080，而交付文件（接触表成片）是 **2560×1440** —— 也就是锁定画布 16:9 的交付尺寸，所以
// 渲染时必须按 4/3 放大。⚠️ `--scale` 只吃十进制字面量：`--scale=4/3` 会被 CLI 判成非法参数
// 而拒绝渲染（实测），必须写 1.3333333333333333（= 2560/1920，乘回去落回 2560×1440）。
const SHOWCASE_DELIVERY_SCALE = '1.3333333333333333';

// 给视频补一条**静音 AAC 音轨**（48kHz 立体声，与 `render` 的音频规格同源）。
// 为什么要补：`NotebookVideoShowcase` 这个 composition 本身不挂音频，渲出来是**纯视频流**；
// 而这条 mp4 是交付物（README 的组件接触表入口），没有音轨的文件在部分播放器/平台侧会被当成残缺。
// `-shortest` 让无限长的 anullsrc 停在视频结束处；`-c:v copy` 原样带走已回写的色彩标记。
const SILENT_AUDIO_INPUT = ['-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000'];
const addSilentAudioTrack = async (target) => {
  const muxed = `${target}.muxed.mp4`;
  try {
    await run('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', ...SILENT_AUDIO_INPUT, '-i', target,
      '-map', '1:v:0', '-map', '0:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest',
      '-movflags', '+faststart', muxed]);
    fs.renameSync(muxed, target);
  } catch (error) {
    fs.rmSync(muxed, {force: true});
    throw new Error(
      `视频已经渲染完成，只是「补静音音轨」失败：${target} 本身是完整可用的（只是没有音轨）。\n` +
      `修法（不必重渲）：\n  ffmpeg -y -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 -i "${target}" -map 1:v:0 -map 0:a:0 -c:v copy -c:a aac -b:a 192k -shortest "${target}.muxed.mp4"\n` +
      `底层错误：${error && error.message ? error.message : error}`,
    );
  }
};

// 组件接触表：把 NotebookVideoShowcase 渲染成 mp4，再抽接触表 jpg。
// 抽帧口径：`select` 滤镜按帧号精确取帧 —— 每页（30 帧 = 1 秒）取**第 6 与第 21 帧**
// 两张中段图，`tile=6x6` 正好 36 格 = 18 页。（实测教训：`-ss 0.2 + fps=2` 的落点会偏 ——
// seek 与 fps 取整叠加后实际抽到第 12/27 帧，第 ⑪ 页的转场中态又被错过；select 无此问题。）
// 旧版 `fps=1` 只抽**页首帧**，转场这类"动作在页中段"的件（第 ⑪ 页 SceneTransitions）在抽图上根本看不见。
// 作用：让执行 AI 看见库组件形态，而不是读文字描述（references/media-routing.md §6）。
//
// ⚠️ 这个 mp4 是**交付物**（组件接触表成片），
// 所以它走的是交付规格，不是调试规格：2560×1440（`SHOWCASE_DELIVERY_SCALE`）+ 静音 AAC 音轨 +
// 色彩四项回写。v3.1.1 之前这条命令按 Remotion 默认参数跑（1920×1080、无音轨、不回写色彩），
// 于是"照文档跑一遍"会把交付文件**静默换成调试版** —— 规格漂了却没有任何门禁看得见。
const showcase = async (args, sheetOnly = false) => {
  const positional = args.filter((a) => !a.startsWith('--'));
  const [projectArg, outputArg] = positional;
  if (!projectArg) fail(`Usage: notebook-video ${sheetOnly ? 'showcase-sheet' : 'showcase'} PROJECT_DIRECTORY [OUTPUT_FILE]`, 2);
  const project = resolvePath(projectArg);
  // 两个产物**各自**有自己的路径：`showcase` 的位置参数是 mp4，`showcase-sheet` 的是 jpg。
  // （旧版把同一个 outputArg 同时当成 mp4 和 jpg 的路径 —— 传了输出路径时，最后那步抽帧会用
  //  一张 jpg 覆盖掉刚渲好的 mp4；默认路径下看不出来，因为两个默认路径本来就不同。）
  const mp4 = resolvePath(!sheetOnly && outputArg ? outputArg : path.join(project, 'renders', 'showcase.mp4'));
  const jpg = resolvePath(sheetOnly && outputArg ? outputArg : path.join(project, 'renders', 'showcase-sheet.jpg'));
  ensureParent(mp4);
  ensureParent(jpg);
  if (!sheetOnly || !isNonEmptyFile(mp4)) {
    const concurrency = Number(process.env.REMOTION_CONCURRENCY || suggestedConcurrency());
    // 三段各自可单独重做（后两段失败时的报错都会说清"视频已经渲完了，不必重渲"）：
    //   ① 放大 4/3 渲出视频流 → ② 补静音音轨 → ③ 回写色彩四项。
    await remotionRender({project, composition: 'NotebookVideoShowcase', output: mp4, concurrency, scale: SHOWCASE_DELIVERY_SCALE});
    await addSilentAudioTrack(mp4);
    await applyColorTags(mp4);
    console.log(`Showcase mp4 (delivery spec): ${mp4} — ${SHOWCASE_DELIVERY_SCALE}x scale, silent AAC track, bt709/tv color tags.`);
  }
  await run('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-i', mp4, '-vf', "select='eq(mod(n,30),6)+eq(mod(n,30),21)',scale=640:-1,tile=6x6", '-frames:v', '1', '-q:v', '3', jpg]);
  console.log(`Showcase contact sheet written: ${jpg}`);
  console.log('Read it to pick components by sight; see references/media-routing.md §6.');
};

// 3.3.0：craft 组件样张 —— 一页 12 格（src/craft-sheet.tsx），出一张 PNG 看图。缺省第 72 帧（全部落定）。
const craftSheet = async (args) => {
  const positional = args.filter((a) => !a.startsWith('--'));
  const [projectArg, outputArg] = positional;
  if (!projectArg) fail('Usage: notebook-video craft-sheet PROJECT_DIRECTORY [OUTPUT_PNG] [--frame=N] [--scale=S]', 2);
  const project = resolvePath(projectArg);
  const remotionCli = path.join(project, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
  if (!fs.existsSync(remotionCli)) await runNpm(['ci', '--no-audit', '--no-fund'], {cwd: project});
  if (!fs.existsSync(remotionCli)) fail(`Remotion CLI is missing after npm ci: ${remotionCli}`);
  const out = resolvePath(outputArg ?? path.join(project, 'renders', 'craft-sheet.png'));
  ensureParent(out);
  const opt = (k, d) => (args.find((a) => a.startsWith(`--${k}=`)) ?? `=${d}`).split('=')[1];
  const nodeArgs = [remotionCli, 'still', REMOTION_ENTRY_POINT, 'NotebookVideoCraftSheet', out, `--frame=${opt('frame', 72)}`, `--scale=${opt('scale', 1)}`];
  if (process.env.REMOTION_BROWSER_EXECUTABLE) nodeArgs.push(`--browser-executable=${resolvePath(process.env.REMOTION_BROWSER_EXECUTABLE)}`);
  await run(process.execPath, nodeArgs, {cwd: project});
  console.log(`Craft sheet written: ${out} — read it to judge the craft components under the current skin (references/craft-kit.md).`);
};

const usage = () => {
  console.log(`Notebook Video cross-platform CLI\n\nCommands:\n  check-deps\n  fonts [--serif]   (download the pinned LXGW WenKai Lite fonts once — plus Noto Serif SC with --serif; new-project does this automatically)\n  validate-skill\n  new-project PROJECT_DIRECTORY [--style=flat|cel|journal|papercut|archive]\n  build-semantic-captions WORD_TIMING_JSON SEMANTIC_LINES OUTPUT_JSON [options]\n  match-timing PROJECT_DIRECTORY [--lock]\n  sync PROJECT_DIRECTORY\n  prepare-browser PROJECT_DIRECTORY\n  benchmark-render PROJECT_DIRECTORY [COMPOSITION_ID]\n  render-range PROJECT_DIRECTORY OUTPUT_MP4 START_FRAME END_FRAME [COMPOSITION_ID]\n  review-frames PROJECT_DIRECTORY OUTPUT_MP4 START_FRAME END_FRAME [COMPOSITION_ID]\n  render PROJECT_DIRECTORY OUTPUT_MP4 [COMPOSITION_ID]\n  validate-video VIDEO_MP4 EXPECTED_DURATION [CONTACT_SHEET_JPG]\n  validate-caption-sync WORD_TIMING_JSON CAPTION_CUES_JSON\n  validate-semantic-breaks CAPTION_CUES_JSON PROTECTED_PHRASES_TXT [--budoux-dir DIR|--no-budoux]\n  (delivery default: the CLI auto-detects the project node_modules/budoux and always adds --require-budoux; a missing BudouX fails instead of silently skipping — pass --no-budoux to skip the phrase rule on purpose)\n  validate-visual-plan PROJECT_DIRECTORY\nresolve-shots PROJECT_DIRECTORY [--check]\nvalidate-shot-motion PROJECT_DIRECTORY\nvalidate-composition PROJECT_DIRECTORY [--strict]\nvalidate-frame-props PROJECT_DIRECTORY\nvalidate-audio-levels PROJECT_DIRECTORY\nvalidate-treatment PROJECT_DIRECTORY   (3.3.0 director layer: manifests/treatment.json)\nvalidate-opening PROJECT_DIRECTORY [--video MP4]   (3.6.0 first three seconds: cold open, first caption, beats, pixels)\nsilent-timing LINES_TXT OUT_JSON [--cps N] [--project DIR]   (3.6.0 caption timing without TTS; hand-made skins default 6.5 chars/s)\nvalidate-backgrounds PROJECT_DIRECTORY [--shots] [--recompute]   (3.4.0 background library: manifests/backgrounds.json)\nvalidate-media PROJECT_DIRECTORY\nprepare-media PROJECT_DIRECTORY [--add FILE --id ID …]\ncommons search \"QUERY\" [--type image|video|audio] [--source commons|openverse] [--audio-category music|sound_effect] [--project DIR] | commons add PROJECT \"File:…\" --id ID | commons credits PROJECT\nvalidate-ocr PROJECT_DIRECTORY --video MP4 | --stills DIR   (optional: needs pip rapidocr onnxruntime)\nshowcase PROJECT_DIRECTORY [OUTPUT_MP4]\nshowcase-sheet PROJECT_DIRECTORY [OUTPUT_JPG]\ncraft-sheet PROJECT_DIRECTORY [OUTPUT_PNG] [--frame=N]   (3.3.0: one page with every src/craft component)\nfx-probe PROJECT_DIRECTORY [--force]   (3.5.0: can this machine draw the WebGPU page turn? prints JSON; render runs it automatically)\n  package PROJECT_DIRECTORY OUTPUT_ZIP\n\nTTS is provider-neutral: supply audio/narration.mp3 and audio/narration.mp3.json using the documented adapter contract.\nGenerated or supplied raster assets are provider-neutral: register used files in manifests/visual-assets.json.\nThe same command works on macOS, Linux, Windows Command Prompt and PowerShell.`);
};

const main = async () => {
  const [command, ...args] = process.argv.slice(2);
  if (!command || command === 'help' || command === '--help' || command === '-h') return usage();
  if (pythonCommandMap.has(command)) {
    const [script] = pythonCommandMap.get(command);
    await runPython(script, command === 'validate-semantic-breaks' ? semanticBreaksArgs(args) : args);
    return;
  }
  switch (command) {
    case 'check-deps': return checkDeps();
    case 'fonts': return ensureFonts().then(async (d) => { if (args.includes('--serif')) await ensureSerif(); console.log(`Fonts ready: ${d}`); });
    case 'new-project': return newProject(args);
    case 'sync': return syncProjectAssets(args);
    case 'prepare-browser': return prepareBrowser(args);
    case 'benchmark-render': return benchmarkRender(args);
    case 'render-range': return renderRange(args);
    case 'review-frames': return reviewFrames(args);
    case 'render': return render(args);
    case 'showcase': return showcase(args, false);
    case 'showcase-sheet': return showcase(args, true);
    case 'craft-sheet': return craftSheet(args);
    case 'fx-probe': return fxProbe(args);
    case 'validate-video': return validateVideo(args);
    case 'package': return packageProject(args);
    default: fail(`Unknown command: ${command}\nRun with --help for available commands.`, 2);
  }
};

main().catch((error) => {
  console.error(error?.stack || error?.message || String(error));
  process.exit(1);
});
