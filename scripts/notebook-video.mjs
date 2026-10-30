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

// 3.7.0：Windows 上 Remotion 拉浏览器 / 收尾 taskkill 时不设 windowsHide，
// 于是每渲染一帧就闪一个 CMD 窗口（child_process.exec 在 Windows 上固定经 cmd.exe /d /s /c 启动）。
// 不改 node_modules（重装依赖就没了），改成预加载 scripts/windows-hide-console.cjs，
// 由它把 child_process 的 spawn/exec 包一层强制补上 windowsHide。
// 见 scripts/windows-hide-console.cjs 头部的实测记录。
const HIDE_CONSOLE_SHIM = path.join(SCRIPT_DIR, 'windows-hide-console.cjs');
const hideConsoleArgs = () => (IS_WINDOWS && fs.existsSync(HIDE_CONSOLE_SHIM) ? ['--require', HIDE_CONSOLE_SHIM] : []);

const fail = (message, code = 1) => {
  console.error(message);
  process.exit(code);
};

const resolvePath = (value, base = process.cwd()) => path.resolve(base, value);
const ensureParent = (target) => fs.mkdirSync(path.dirname(target), {recursive: true});
const isNonEmptyFile = (target) => fs.existsSync(target) && fs.statSync(target).isFile() && fs.statSync(target).size > 0;

// 3.9.0：preview / sweep / poster 各抄了一份「取 --flag=值 + 拒绝拼错参数」，收成一份。
// 拼错参数默默按默认值跑是修过一次的坑（`--second=6` 会渲 30 秒）；三份漏一份就等于没修，
// poster 就一直是漏的。只做这件事，不碰排版 / 渲染。
const parseFlags = (argv, name, names) => {
  const opt = (flag, fallback) => {
    const hit = argv.find((a) => a.startsWith(`--${flag}=`));
    return hit === undefined ? fallback : hit.slice(flag.length + 3);
  };
  const unknown = argv
    .filter((a) => a.startsWith('--'))
    .map((a) => a.slice(2).split('=')[0])
    .filter((n) => !names.includes(n));
  if (unknown.length) {
    fail(`${name} 不认这些参数：${[...new Set(unknown)].map((n) => `--${n}`).join(', ')}（可用：${names.map((n) => `--${n}`).join(' / ')}）`, 2);
  }
  return opt;
};

// 读分镜表；找不到返回 null，要不要报错由调用方定（preview 没它也能渲，sweep 不能）。
const readShotTable = (project) => {
  try {
    const table = JSON.parse(fs.readFileSync(path.join(project, 'manifests', 'shots.resolved.json'), 'utf8'));
    return {table, shots: Array.isArray(table.shots) ? table.shots : [], total: Number(table.duration) || null};
  } catch { return null; }
};

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

// 中文 Windows 控制台是 cp936，门禁脚本里的「✓ ✗ ⚠」不在 GBK 里；输出被管道捕获时
// print 会抛 UnicodeEncodeError，看起来像门禁失败。统一给 python 子进程开 UTF-8。
const PY_UTF8_ENV = {...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1'};

const runPython = async (scriptName, args = [], options = {}) => {
  const python = findPython();
  if (!python) throw new Error('Python 3 was not found. Install Python 3 and make py, python, or python3 available on PATH.');
  const script = path.isAbsolute(scriptName) ? scriptName : path.join(SCRIPT_DIR, scriptName);
  return run(python.command, [...python.prefix, script, ...args], {...options, env: options.env ?? PY_UTF8_ENV});
};

const npmInvocation = () => {
  if (!IS_WINDOWS) return {command: 'npm', prefix: []};
  const candidates = [
    path.join(path.dirname(process.execPath), 'node_modules', 'npm', 'bin', 'npm-cli.js'),
    path.resolve(path.dirname(process.execPath), '..', 'node_modules', 'npm', 'bin', 'npm-cli.js'),
  ];
  const cli = candidates.find((candidate) => fs.existsSync(candidate));
  // 找不到随 Node 安装的 npm-cli.js 时退回 npm.cmd——但 Node 18+ 禁止直接 spawn .cmd（EINVAL），
  // 必须经 shell，所以把 shell 需求一起带出去。
  return cli ? {command: process.execPath, prefix: [], shell: false} : {command: 'npm.cmd', prefix: [], shell: true};
};

const runNpm = (args, options = {}) => {
  const npm = npmInvocation();
  const cwd = options.cwd ?? process.cwd();
  const cache = process.env.NOTEBOOK_VIDEO_NPM_CACHE || path.join(cwd, '.tools', 'npm-cache');
  fs.mkdirSync(cache, {recursive: true});
  return run(npm.command, [...npm.prefix, ...args], {...options, shell: options.shell ?? npm.shell ?? false, env: {...process.env, npm_config_cache: cache}});
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

// 渲染前把中文字体补进工程。字体不入库（OFL 的 12 MB 二进制不该进 git），只在
// `new-project` 时拷；于是"直接渲染一个现成工程/模板副本"会因为缺 ttf 在**第 0 帧**
// 报 Chrome 的 `A network error occurred`——完全看不出是缺字体。这里补齐它。
const ensureProjectFonts = async (project) => {
  const want = ['LXGWWenKaiLite-Regular.ttf', 'LXGWWenKaiLite-Medium.ttf'];
  const missing = want.filter((n) => !fs.existsSync(path.join(project, 'public', n)));
  if (!missing.length) return;
  const dir = await ensureFonts();
  fs.mkdirSync(path.join(project, 'public'), {recursive: true});
  for (const n of missing) fs.copyFileSync(path.join(dir, n), path.join(project, 'public', n));
  console.log(`已补中文字体到工程 public/：${missing.join(', ')}（LXGW WenKai Lite · OFL-1.1）`);
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
  // 3.3.0（T8.1）：模板自带的 treatment.json 描述的是示例片；换皮肤时 medium.skin 必须跟着改，
  // 否则 validate-treatment 直接以「medium.skin 与工程皮肤不一致」判 P0（手作皮肤必填项）。
  const treatmentPath = path.join(target, 'manifests', 'treatment.json');
  if (fs.existsSync(treatmentPath)) {
    const t = JSON.parse(fs.readFileSync(treatmentPath, 'utf8'));
    if (t.medium && typeof t.medium === 'object') {
      t.medium.skin = style;
      fs.writeFileSync(treatmentPath, `${JSON.stringify(t, null, 2)}\n`);
    }
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
  // 3.3.0：手作皮肤的导演层是必填项，直接说清下一步，别让新用户在门禁前面猜。
  if (SERIF_THEMES.includes(style)) {
    console.log('下一步：改 manifests/treatment.json（facts 换成你选题的出处、跑一次 commons-search.py search "<关键词>" --project .），然后 make-video --stills。');
  } else {
    console.log('下一步：node scripts/make-video.mjs <工程> --stills，先看静帧接触表。');
  }
};

const syncProjectAssets = async ([projectArg], {quiet = false} = {}) => {
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
  if (!quiet) console.log('Synchronized canonical render inputs into public/ and src/.');
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
  await run(process.execPath, [...hideConsoleArgs(), ...args], {cwd: project});
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

// 3.3.0：真卷页能力探针（scripts/fx-browser.mjs）。同一进程内只探一次；结论写 renders/.fx-probe.json 供 make-video 写报告。
const fxCache = new Map();
const fxFor = async (project, {force = false, quiet = false} = {}) => {
  if (!force && fxCache.has(project)) return fxCache.get(project);
  const remotionCli = path.join(project, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
  let remotionVersion = '';
  try { remotionVersion = JSON.parse(fs.readFileSync(path.join(project, 'node_modules', 'remotion', 'package.json'), 'utf8')).version; } catch { /* 未安装 */ }
  const runStill = async (args) => {
    if (!fs.existsSync(remotionCli)) return {code: 1, out: `Remotion CLI missing: ${remotionCli}`};
    const r = await run(process.execPath, [...hideConsoleArgs(), remotionCli, 'still', REMOTION_ENTRY_POINT, ...args], {cwd: project, capture: true, allowFailure: true});
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

// 3.9.0：覆盖率判据**只写这一处**。渲染收尾的汇总行和 `sweep` 的全片表都调它 ——
// 这个项目已经在"两个地方各判一次"上栽过三次（响度读数、空场采样、耗时推算），
// 症状都是"终端说 pass、报告说有问题"，查半天才发现判的不是同一件事。
const assessCoverage = (coverage) => {
  const ids = [...coverage.keys()].sort((a, b) => a.localeCompare(b, 'en', {numeric: true}));
  const rows = ids.map((id) => {
    const c = coverage.get(id);
    const cells = Number(c.cells);
    const total = Number(c.total);
    const blank = Number(c.blank);
    const cols = Number(c.cols);
    const largest = Number(c.largest);
    const widest = Number(c.widest);
    // 两条豁免（阈值来自 3.8.0 实测，理由见 fill-gate.tsx 与 composition-gate.md）：
    //   条状主体（标尺 / 格带 / 时间轴）：面积天然小，但跨度够 45% 画宽，不算空。
    //   组合装置（照片 + 引线 + 网格）：没有空白列、48 格里至少 24 格有内容。
    //   largest 是按**单个 DOM 元素**量的，多个中等元素拼成的主体天生只有 3%。
    // ⚠ 豁免只在"没有它就会报警"（largest<0.06）时才算数。否则 S4 这种 widest=0.82
    //   但 largest=0.29 的镜也会被贴上"条状主体"，读的人会以为它本来要报警。
    const needsExemption = largest < 0.06;
    const exempt = !needsExemption ? null : (widest >= 0.45 ? 'strip' : (blank === 0 && cells >= 24 ? 'composite' : null));
    const verdict = blank >= 3 ? 'hollow' : (needsExemption && !exempt ? 'sparse' : 'pass');
    return {id, cells, total, blank, cols, largest, widest, exempt, needsExemption, verdict};
  });
  return {
    rows,
    sparse: rows.filter((r) => r.needsExemption && !r.exempt).map((r) => r.id),
    hollow: rows.filter((r) => r.blank >= 3).map((r) => r.id),
  };
};

// 覆盖率落盘：合并、不覆盖。`preview --shot=S6` 只量了 S6，不该把另外五镜的数字抹掉——
// 之前是整体覆盖，量完单镜后文件里只剩一镜，读的人会以为全片只有一镜。
// 每条记 `at`（何时量的），陈旧数字因此看得出来，而不是冒充"刚量过"。
const writeCoverage = (cwd, coverage) => {
  try {
    const out = path.join(cwd, 'renders', 'fill-coverage.json');
    fs.mkdirSync(path.dirname(out), {recursive: true});
    let prev = {};
    try { prev = JSON.parse(fs.readFileSync(out, 'utf8')); } catch { /* 首次或损坏，按空处理 */ }
    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const at = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
    const merged = {...prev};
    for (const [id, c] of coverage) merged[id] = {...c, at};
    const ordered = {};
    for (const id of Object.keys(merged).sort((a, b) => a.localeCompare(b, 'en', {numeric: true}))) ordered[id] = merged[id];
    fs.writeFileSync(out, `${JSON.stringify(ordered, null, 1)}\n`);
  } catch { /* 写不进盘不影响出片，数字已经打在终端上 */ }
};

// 3.3.0：FillGate 的浏览器日志按镜头去重。fill-gate.tsx 每个标签每镜只打一条 `[FillGate] underfilled <镜号> …`，
// 这里把所有标签的这类行吞掉、记下镜号，渲染结束汇总成**一行**；其他输出原样透传。
// 3.9.0 加 quiet：`sweep` 要为每镜起一次 still，八次"汇总 + 落盘"会刷八遍；
// quiet 只收数字不吭声，失败时把尾巴 40 行吐出来（否则报错只有一句 exit code 1）。
// measure=false：窗口短到还没进入落定态时，量到的必然是入场帧，那不是"空场"——
// 不打印、不落盘，免得一个 1 秒预览把某镜的覆盖率改成一个假数字。
// persist=false：`preview` 只打印不落盘。它的窗口可能只盖到某镜的前半段，
// 那个数字是"窗口内最完整帧"，不是"整镜最完整帧"——留档会让人以为量过整镜。
// 落盘只有两个来源：整片 `render`（覆盖全部帧）和 `sweep`（每镜取落定态）。
const runRemotionFiltered = (nodeArgs, cwd, {quiet = false, measure = true, persist = true} = {}) => new Promise((resolve, reject) => {
  const child = spawn(process.execPath, nodeArgs, {cwd, env: process.env, stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true, shell: false});
  const shots = new Set();
  const coverage = new Map();
  const tailLines = [];
  let other = 0;
  const pump = (src, dst) => {
    let buf = '';
    src.setEncoding('utf8');
    const emit = (line) => {
      if (line.includes('[FillGate]')) {
        // verbose 模式下 Chrome 会把同一行再包一层 `chrome [pid:ts:INFO:CONSOLE:…] "…"`，
        // 所以这里用 find 而不是锚定行首。
        const cov = line.match(/coverage\s+(\S+)\s+cells=(\d+)\/(\d+)\s+blank=(\d+)\/(\d+)\s+largest=([\d.]+)\s+widest=([\d.]+)/);
        if (cov) {
          coverage.set(cov[1], {cells: cov[2], total: cov[3], blank: cov[4], cols: cov[5], largest: cov[6], widest: cov[7]});
          return;
        }
        const m = line.match(/underfilled\s+(\S+)/);
        if (m) shots.add(m[1]); else other += 1;
        return;
      }
      if (quiet) {
        tailLines.push(line);
        if (tailLines.length > 40) tailLines.shift();
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
    if (quiet && code !== 0 && tailLines.length) console.error(tailLines.join('\n'));
    if (coverage.size && !quiet && measure) {
      const {rows, sparse, hollow} = assessCoverage(coverage);
      console.warn(`FillGate coverage: ${rows.map((r) => {
        return `${r.id} cells=${r.cells}/${r.total} blank=${r.blank}/${r.cols} largest=${r.largest.toFixed(2)} widest=${r.widest.toFixed(2)}${r.exempt ? ` (${r.exempt})` : ''}`;
      }).join(' | ')}`);
      if (sparse.length) console.warn(`FillGate 主体过小（largest<0.06，且不属条状 / 组合装置）：${sparse.join(',')}`);
      if (hollow.length) console.warn(`FillGate 横向空洞（blank≥3/8）：${hollow.join(',')}`);
      if (persist) writeCoverage(cwd, coverage);
    }
    if (!quiet && shots.size) {
      const ids = [...shots].sort((a, b) => a.localeCompare(b, 'en', {numeric: true}));
      console.warn(`FillGate: ${ids.length} shot${ids.length > 1 ? 's' : ''} (${ids.join(',')}) bottom-quarter underfilled${other ? ` (+${other} other FillGate lines)` : ''}`);
    } else if (!quiet && other) console.warn(`FillGate: ${other} message(s) (no underfilled shot)`);
    const measured = measure && coverage.size ? assessCoverage(coverage) : null;
    const underfilled = [...shots].sort((a, b) => a.localeCompare(b, 'en', {numeric: true}));
    if (code === 0) resolve({code, coverage, measured, underfilled}); else reject(new Error(`${process.execPath} exited with code ${code}`));
  });
});

// 3.9.0：浏览器路径解析抽出来给 render / still 共用。以前这段埋在 remotionRender 里，
// `sweep` 要起 still 就得抄一遍——抄第二遍的时候一定会漏掉"缓存存在就别下载"这条。
const resolveBrowserExecutable = () => {
  let browserExecutable = process.env.REMOTION_BROWSER_EXECUTABLE;
  if (!browserExecutable && process.platform === 'win32') {
    const cached = path.join(process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local'), 'remotion-browser', 'chrome-headless-shell', 'win64', 'chrome-headless-shell.exe');
    if (fs.existsSync(cached)) browserExecutable = cached;
  }
  if (!browserExecutable) return null;
  const resolved = resolvePath(browserExecutable);
  if (!fs.existsSync(resolved)) fail(`REMOTION_BROWSER_EXECUTABLE does not exist: ${resolved}`);
  return resolved;
};

const remotionRender = async ({project, composition, output, frames, concurrency, colorTagged = false, scale, fxMode = 'auto', crf = 16, muted = false, measure = true, persist = true}) => {  const remotionCli = path.join(project, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
  if (!fs.existsSync(remotionCli)) await runNpm(['ci', '--no-audit', '--no-fund'], {cwd: project});
  if (!fs.existsSync(remotionCli)) fail(`Remotion CLI is missing after npm ci: ${remotionCli}`);
  ensureParent(output);
  const nodeArgs = [...hideConsoleArgs()];
  if (process.env.REMOTION_USE_NETWORK_SHIM === '1') {
    const shim = path.join(project, 'remotion-network-shim.cjs');
    if (!fs.existsSync(shim)) fail(`Optional network shim is missing: ${shim}`);
    nodeArgs.push('--require', shim);
  }
  // 3.3.0 真卷页（pageturn / peel，WebGPU）：只有成片 composition、且本片用到卷页时才探测；
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
  const browserExecutable = resolveBrowserExecutable();
  if (browserExecutable && !fx.on) nodeArgs.push(`--browser-executable=${browserExecutable}`);
  // 返回 FillGate 的实测结果：`render` 不看，`sweep` 要拿它打全片表。
  // 之前这里丢掉了返回值，于是 sweep 只能再读一次终端输出——那就是第二个真源。
  const result = await runRemotionFiltered(nodeArgs, project, {measure, persist});
  if (colorTagged) await applyColorTags(output);
  return result;
};

const render = async ([projectArg, outputArg, composition = 'NotebookVideoFilm']) => {
  if (!projectArg || !outputArg) fail('Usage: notebook-video render PROJECT_DIRECTORY OUTPUT_MP4 [COMPOSITION_ID]', 2);
  const project = resolvePath(projectArg);
  const output = resolvePath(outputArg);
  await ensureProjectFonts(project);
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
  // 3.3.0 真卷页：完整版 Chrome + 软件 GPU 每帧约 3 s（实测 2 核 arm64、2560×1440，缺省 Headless Shell 约 0.25 s），
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
    fs.rmSync(tmpDir, {recursive: true, force: true, maxRetries: 5, retryDelay: 120});   // Windows：文件被短暂占用时重试
  } else {
    await remotionRender({project, composition, output: raw, concurrency, colorTagged: true, scale: scaleArg});
  }
  // 响度目标可调（NOTEBOOK_VIDEO_LUFS）。缺省 −16 LUFS、真峰 −1.5 dBTP；3.3.0 起静音占位旁白的片子也用 −16
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
  await ensureProjectFonts(project);
  await syncProjectAssets([project]);
  const concurrency = Number(process.env.REMOTION_CONCURRENCY || suggestedConcurrency());
  // 交付路径（短片段也常被直接拿去交付/送审）：回写色彩元数据。
  // 同 preview：这是**窗口**渲染，FillGate 量到的是窗口内最完整帧，不是整镜最完整帧。
  // 留档会让人以为量过整镜（实测 60 帧窗口把 S1 记成 cells=25，整镜是 28）。
  // 要留档的只有两个来源：整片 `render` 和 `sweep`。
  const windowFrames = end - start + 1;
  await remotionRender({project, composition, output, frames: `${start}-${end}`, concurrency, colorTagged: true, measure: windowFrames >= 60, persist: false});
  console.log(`Rendered review range ${start}-${end}: ${output}`);
};

// 30 秒验证单元（3.8.0）：只渲一段，用来判断"这一版好不好看"，不是交付物。
// 存在的理由：全片 1472 帧约 13 分钟，改一版看一版会把迭代次数压到个位数。
// 默认半分辨率、默认前 30 秒；--shot=S4 只看一镜。
const preview = async (argv) => {
  const [projectArg, ...rest] = argv;
  if (!projectArg) fail('Usage: notebook-video preview PROJECT_DIRECTORY [--seconds=30] [--from=SEC] [--shot=ID] [--scale=0.5]', 2);
  const opt = parseFlags(rest, 'preview', ['seconds', 'from', 'shot', 'scale', 'fx']);
  if (opt('shot', null) !== null && opt('from', null) !== null) {
    fail('preview：--shot 和 --from 只能给一个（--shot 会覆盖 --from，别让它悄悄生效）', 2);
  }
  const project = resolvePath(projectArg);
  await ensureProjectFonts(project);
  const fps = Number(process.env.NOTEBOOK_VIDEO_FPS || 30);
  const st = readShotTable(project);
  const totalFrames = st ? st.total : null;
  const shots = st ? st.shots : [];
  const shotId = opt('shot', null);
  let start = Math.max(0, Math.round(Number(opt('from', 0)) * fps));
  let end;
  if (shotId) {
    const shot = shots.find((s) => s.id === shotId);
    if (!shot) fail(`没有这一镜：${shotId}（现有 ${shots.map((s) => s.id).join(', ') || '无'}）`, 2);
    start = Number(shot.from);
    end = Number(shot.to);
  } else {
    end = start + Math.round(Number(opt('seconds', 30)) * fps);
  }
  if (totalFrames) end = Math.min(end, totalFrames);
  if (!Number.isFinite(end) || end <= start) fail(`渲染区间无效：${start}-${end}`, 2);
  const scale = Number(opt('scale', 0.5));
  if (!Number.isFinite(scale) || scale < 0.1 || scale > 1) fail(`--scale 必须在 0.1–1 之间，收到 ${opt('scale', 0.5)}`, 2);
  // 预览默认关掉卷页特效：翻页要换完整版 Chromium + 并发 1（见 remotionRender 注释），
  // 实测把 30 秒片段从 ~1 分钟拖到 8 分钟以上。判构图不需要它；要看翻页时加 --fx=on。
  const fxMode = opt('fx', 'off') === 'on' ? 'auto' : 'off';
  const label = shotId ? `shot-${shotId}` : `f${start}-${end}`;
  const output = path.join(project, 'renders', `preview-${label}.mp4`);
  await syncProjectAssets([project]);
  const concurrency = Number(process.env.REMOTION_CONCURRENCY || suggestedConcurrency());
  const started = Date.now();
  console.log(`Preview ${start}-${end - 1}（${((end - start) / fps).toFixed(1)} 秒）@ ${scale}x …`);
  // 窗口不足 2 秒（60 帧）时，FillGate 量到的还只是入场帧——元素还在画，那不是空场。
  // 实测：`--seconds=1` 会把 S1 判成「横向空洞」（cells 很少、blank 很多），
  // 而同一镜在 30 秒预览里是 28/48。所以这种窗口不判、也不写 fill-coverage.json，
  // 免得一个"只看一眼"的预览把某镜的覆盖率改成一个假数字。
  const measure = end - start >= fps * 2;
  if (!measure) console.log(`窗口只有 ${end - start} 帧，还没进入落定态：这次只出片，不判 FillGate（要量密度用 sweep）`);
  await remotionRender({project, composition: 'NotebookVideoFilm', output, frames: `${start}-${end - 1}`, concurrency, scale, fxMode, measure, persist: false});
  const contact = output.replace(/\.mp4$/i, '-contact.jpg');
  await makeContactSheet(output, contact, (end - start) / fps);
  // 响度：用 loudnorm 的 JSON（和正片 §probe 同口径）。原来用 ebur128 + 正则，
  // 但 ebur128 每 100 ms 打一行运行值，正则会抓到**第一行**——开场静音段，于是报 −70 LUFS。
  // 预览片明明有声音（ffprobe 有 aac 流、RMS 约 −24 dB）。读数错比没有读数更坏。
  const lufs = await run('ffmpeg', ['-hide_banner', '-i', output, '-af', 'loudnorm=I=-16:TP=-1.5:print_format=json', '-f', 'null', '-'],
    {capture: true, allowFailure: true});
  const lufsJson = `${lufs.stdout || ''}\n${lufs.stderr || ''}`.match(/\{[\s\S]*\}/);
  let loudness = null;
  if (lufsJson) {
    try {
      const m = JSON.parse(lufsJson[0]);
      if (Number.isFinite(Number(m.input_i))) loudness = {lufs: m.input_i, tp: m.input_tp};
    } catch { /* 读不到就只说没读到，不编数 */ }
  }
  const took = (Date.now() - started) / 1000;
  console.log(`Preview: ${output}`);
  console.log(`Contact: ${contact}`);
  console.log(loudness
    ? `Loudness: ${loudness.lufs} LUFS / true peak ${loudness.tp} dBTP（预览是原始渲染、未做交付规范化；交付按 −16 LUFS）`
    : 'Loudness: 未能读取（loudnorm 输出无法解析）');
  // 全片推算只在它成立的时候给。开了真卷页时**不能线性外推**：WebGPU 只用于转场那几十帧，
  // 其余帧走普通渲染，按"每帧 1.8 秒"乘全片会得到 40 分钟这种假数字（实测：
  // `--from=3 --seconds=1 --fx=on` 53 秒，外推全片 2614 秒；而全片实际是 13 分钟）。
  // 探针结论已缓存（fxFor），这里问一次不会重跑浏览器。
  const fxOn = fxMode !== 'off' && (await fxFor(project, {quiet: true})).on;
  if (totalFrames && fxOn) {
    console.log(`Done in ${took.toFixed(0)}s — 开了真卷页，全片耗时无法从窗口线性推算（只有转场帧走 WebGPU）`);
  } else if (totalFrames) {
    console.log(`Done in ${took.toFixed(0)}s — 按 ${scale}x 推算全片约 ${Math.round(took * totalFrames / Math.max(1, end - start))}s（交付分辨率另计）`);
  }
  // 3.9.0：预览只盖一段时，**当场说出后面还有几镜没看**。
  // 文档里写"记得补跑"不算工程手段——cell 的 S7/S8 就是整片漏掉的，
  // 直到补量才发现 S7 右下角空 30%。这句话是把那次教训变成自动提醒。
  if (totalFrames && end < totalFrames) {
    const unseen = shots.filter((s) => Number(s.from) >= end).map((s) => s.id);
    const tailNote = unseen.length
      ? `后面 ${unseen.length} 镜（${unseen.join(', ')}）没看`
      : `后面还有 ${((totalFrames - end) / fps).toFixed(0)} 秒没看`;
    console.log(`⚠ Preview 只到 f${end}/${totalFrames} · ${tailNote} · 全片量一遍用 sweep`);
  }
};

// 3.9.0 · `sweep`：全片每一镜都量一遍，一分钟出头。
//
// 存在的理由不是"再多一个检查"，是补一个**已经发生过的漏检**：`preview` 默认只盖前 30 秒，
// 片子比 30 秒长的时候，后半段的镜头**一次都没有被任何门禁看过**。cell 的 S7/S8 就是这么漏的
// ——补跑 `--from=32` 才发现 S7 右下角空 30%。靠"记得补跑尾巴"不是工程手段。
//
// 做法是每镜截**一张落定态**，不是渲一段视频：45 帧里 44 帧长得一样，渲成 mp4 只是把
// 同一个数字量 45 遍；而一张 PNG 既能出数字，又能直接拼成"全片体检表"一眼看完。
const SWEEP_GRID = 15;   // FillGate 的 sampleEvery 缺省值，见 fill-gate.tsx

// 每镜一个采样帧：**必须是 15 的倍数**——FillGate 只在 `frame % 15 === 0` 或 watch 事件
// ±2 帧上采样。取一个不在网格上的帧会得到**零数据**，而零数据和"这镜没问题"长得一模一样，
// 这是这个项目已经犯过三次的错（量错东西，但数字看着合理）。
//
// 位置取"切点前最近的一个网格帧"：入场帧几乎必然是空的（元素还在画），拿它判空场会把
// 每一镜都打成空洞——FillGate 第一版就是这么误报的。切点前是落定态。
const sweepFrames = (shots) => {
  const picks = [];
  const skipped = [];
  for (const s of shots) {
    const from = Math.round(Number(s.from));
    const last = Math.round(Number(s.to)) - 1;      // shots[].to 是开区间
    if (!Number.isFinite(from) || !Number.isFinite(last) || last < from) {
      skipped.push({id: s.id, why: '区间无效'});
      continue;
    }
    // 必须落在**后半段**：只要求"是 15 的倍数"不够——一个 15 帧长的镜头，
    // 唯一的网格点就是它的入场帧（0），而入场帧几乎必然是空的。那会量出一个假空洞。
    const midpoint = from + Math.floor((last - from + 1) / 2);
    const lastGrid = Math.floor(last / SWEEP_GRID) * SWEEP_GRID;
    const gridAfterMid = Math.ceil(midpoint / SWEEP_GRID) * SWEEP_GRID;
    const frame = lastGrid >= midpoint ? lastGrid : gridAfterMid;
    // 后半段里一个网格点都没有（镜头短于一个网格）→ 退回最后一帧，靠 FillGate 的
    // hot 事件兜底；兜不住会进 missing —— 那也比假装量过好。
    const onGrid = frame <= last;
    // 兜底时也标上落在后半段的哪一帧，不是随便取第一帧。
    picks.push({id: s.id, frame: onGrid ? frame : last, onGrid});
  }
  return {picks, skipped};
};

// 单帧截图。`--log=verbose` 不是可选的：不加它 Remotion 不转发浏览器 console，
// FillGate 的 coverage 行就一条都收不到——而"收不到"和"没问题"在终端上长得一样。
const renderStill = async ({project, output, frame, scale}) => {
  const remotionCli = path.join(project, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
  if (!fs.existsSync(remotionCli)) fail(`Remotion CLI 缺失：${remotionCli}（先在工程里跑 npm ci）`, 1);
  const nodeArgs = [...hideConsoleArgs()];
  nodeArgs.push(remotionCli, 'still', REMOTION_ENTRY_POINT, 'NotebookVideoFilm', output, `--frame=${frame}`, `--scale=${scale}`, '--log=verbose');
  // ⚠ 必须放在 remotion 子命令参数里（nodeArgs 末尾），不是 node 自己的参数——
  // 放前面 node 会报 `bad option: --browser-executable=…` 然后 rc=9，而且八镜会连报八次。
  const browser = resolveBrowserExecutable();
  if (browser) nodeArgs.push(`--browser-executable=${browser}`);
  return runRemotionFiltered(nodeArgs, project, {quiet: true});
};

// 把每镜一张拼成一张表。用 ffmpeg 的 concat demuxer + tile：不依赖文件名排序，
// 也不要求镜头数是 4 的倍数（xstack 做不到）。
const tileStills = async (pngs, output, cols) => {
  if (!pngs.length) return false;
  if (pngs.length === 1) { fs.copyFileSync(pngs[0], output); return true; }
  const list = path.join(os.tmpdir(), `nv-sweep-list-${process.pid}.txt`);
  const esc = (p) => p.replace(/\\/g, '/').replace(/'/g, "'\\''");
  fs.writeFileSync(list, `${pngs.map((p) => `file '${esc(p)}'`).join('\n')}\n`);
  const rows = Math.ceil(pngs.length / cols);
  const r = await run('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
    '-i', list, '-vf', `tile=${cols}x${rows}:padding=10:margin=10:color=white`, '-frames:v', '1', '-q:v', '3', output],
    {capture: true, allowFailure: true});
  fs.rmSync(list, {force: true});
  if (r.code) {
    console.warn(`拼表失败（单张图还在 renders/sweep/）：${((r.stderr || '').trim().split('\n').slice(-1)[0] || `ffmpeg ${r.code}`)}`);
    return false;
  }
  return true;
};

const sweep = async (argv) => {
  const [projectArg, ...rest] = argv;
  if (!projectArg) fail('Usage: notebook-video sweep PROJECT_DIRECTORY [--scale=0.5] [--cols=4] [--plan] [--json]', 2);
  const opt = parseFlags(rest, 'sweep', ['scale', 'cols', 'plan', 'json']);

  const project = resolvePath(projectArg);
  const resolvedPath = path.join(project, 'manifests', 'shots.resolved.json');
  const st = readShotTable(project);
  if (!st) fail(`没有 ${resolvedPath}：先跑 resolve-shots PROJECT_DIRECTORY`, 2);
  const shots = st.shots;
  if (!shots.length) fail(`${resolvedPath} 里 shots 为空，没有可扫的镜头`, 2);
  const {picks, skipped} = sweepFrames(shots);
  if (!picks.length) fail('没有可扫的镜头（分镜表区间都无效）', 2);

  // 参数校验放在 --plan 之前：`sweep --plan --scale=0.05` 也该当场报错，
  // 否则"先看成本"这一步会给出一个能跑、但跑起来参数非法的计划。
  const scale = Number(opt('scale', 0.5));
  if (!Number.isFinite(scale) || scale < 0.1 || scale > 1) fail(`--scale 必须在 0.1–1 之间，收到 ${opt('scale', 0.5)}`, 2);
  const tileCols = Number(opt('cols', 4));
  if (!Number.isInteger(tileCols) || tileCols < 1 || tileCols > 8) fail(`--cols 必须是 1–8 的整数，收到 ${opt('cols', 4)}`, 2);

  // --plan：只算会量哪几帧，不启动浏览器。给"先看成本"和测试用（纯函数，不需要工程能跑）。
  if (rest.includes('--plan')) {
    console.log(JSON.stringify({grid: SWEEP_GRID, picks, skipped}, null, 2));
    return;
  }

  const asJson = rest.includes('--json');
  await ensureProjectFonts(project);
  await syncProjectAssets([project], {quiet: asJson});
  const dir = path.join(project, 'renders', 'sweep');
  fs.mkdirSync(dir, {recursive: true});
  // 清掉上一次的 PNG：镜头改过（删了一镜、改了顺序）时旧图会留在目录里，
  // 拼图只用本次的 pngs 不会拼错，但人翻目录时会看到一张不存在的镜头。
  for (const f of fs.readdirSync(dir)) {
    if (/^S\d+\.png$/.test(f)) fs.rmSync(path.join(dir, f), {force: true});
  }

  const started = Date.now();
  // --json 时终端只能留 JSON：进度行混进去就没法 `| jq` 了。
  const progress = asJson ? () => {} : (line) => process.stdout.write(line);
  if (!asJson) console.log(`Sweep ${picks.length} 镜 · 每镜一张落定态 @ ${scale}x …`);
  const merged = new Map();
  const pngs = [];
  const failed = [];
  for (const [i, pick] of picks.entries()) {
    const png = path.join(dir, `${pick.id}.png`);
    const t0 = Date.now();
    progress(`  [${i + 1}/${picks.length}] ${pick.id} @${pick.frame}${pick.onGrid ? '' : '（不在网格上）'} … `);
    try {
      const r = await renderStill({project, output: png, frame: pick.frame, scale});
      if (r?.coverage?.size) for (const [id, c] of r.coverage) merged.set(id, c);
      if (fs.existsSync(png)) pngs.push(png); else failed.push(pick.id);
      progress(`${((Date.now() - t0) / 1000).toFixed(0)}s\n`);
    } catch (e) {
      progress(`失败（${String(e.message).split('\n')[0]}）\n`);
      failed.push(pick.id);
    }
  }
  if (merged.size) writeCoverage(project, merged);
  const assessed = assessCoverage(merged);
  const rows = assessed.rows;
  const got = new Set(rows.map((r) => r.id));
  const missing = picks.filter((p) => !got.has(p.id)).map((p) => p.id);
  const took = (Date.now() - started) / 1000;

  const sheet = path.join(project, 'renders', 'sweep-sheet.jpg');
  const sheetOk = pngs.length ? await tileStills(pngs, sheet, tileCols) : false;

  const label = (r) => {
    if (r.verdict === 'hollow') return '空洞（blank≥3/8）';
    if (r.verdict === 'sparse') return '主体过小（largest<0.06）';
    if (r.exempt === 'strip') return '过（条状主体）';
    if (r.exempt === 'composite') return '过（组合装置）';
    return '过';
  };
  const now = new Date();
  const p2 = (n) => String(n).padStart(2, '0');
  const payload = {
    at: `${now.getFullYear()}-${p2(now.getMonth() + 1)}-${p2(now.getDate())} ${p2(now.getHours())}:${p2(now.getMinutes())}`,
    grid: SWEEP_GRID, scale, cols: tileCols,
    picks, skipped, missing, failed,
    sheet: sheetOk ? sheet : null,
    rows,
  };
  try {
    fs.mkdirSync(path.join(project, 'renders'), {recursive: true});
    fs.writeFileSync(path.join(project, 'renders', 'sweep.json'), `${JSON.stringify(payload, null, 1)}\n`);
  } catch { /* 写不进盘不影响结论，表已经打出来了 */ }

  // 一镜都没量到 = 这次没有产出任何判断。rc=0 会让"没量到"和"全过"在脚本里长得一样。
  // 放在 --json 分支之前，两种输出模式都退 1。
  if (!rows.length) {
    console.error('Sweep 一镜都没量到：上面每一镜都失败了，这次没有给出任何判断');
    process.exitCode = 1;
  }
  if (asJson) { console.log(JSON.stringify(payload, null, 2)); return; }
  console.log('');
  for (const r of rows) {
    console.log(`  ${r.id.padEnd(4)}cells=${String(r.cells).padStart(2)}/${r.total}  blank=${r.blank}/${r.cols}  largest=${r.largest.toFixed(2)}  widest=${r.widest.toFixed(2)}  ${label(r)}`);
  }
  if (missing.length) console.log(`  未量到：${missing.join(', ')}（那一帧 FillGate 没采样——镜头短于 15 帧，或画面还在画）`);
  if (skipped.length) console.log(`  跳过：${skipped.map((s) => `${s.id}（${s.why}）`).join('、')}`);
  const bad = rows.filter((r) => r.verdict !== 'pass');
  console.log('');
  console.log(`Sweep: ${rows.length}/${picks.length} 镜量到 · ${rows.length - bad.length} 过 · ${assessed.sparse.length} 过小 · ${assessed.hollow.length} 空洞 · ${took.toFixed(0)}s`);
  if (sheetOk) console.log(`Sweep sheet: ${sheet}`);
  console.log(`Sweep stills: ${dir}`);
};


const reviewFrames = async ([projectArg, outputArg, startArg, endArg, composition = 'NotebookVideoFilm']) => {
  if (!projectArg || !outputArg || startArg === undefined || endArg === undefined) fail('Usage: notebook-video review-frames PROJECT_DIRECTORY OUTPUT_MP4 START_FRAME END_FRAME [COMPOSITION_ID]', 2);
  const start = Number(startArg), end = Number(endArg);
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end < start) fail(`Invalid frame range: ${startArg}-${endArg}`);
  const project = resolvePath(projectArg), output = resolvePath(outputArg);
  await ensureProjectFonts(project);
  await syncProjectAssets([project]);
  const concurrency = Number(process.env.REMOTION_CONCURRENCY || suggestedConcurrency());
  const fps = Number(process.env.NOTEBOOK_VIDEO_FPS || 30);
  // 调试产物（看画面对不对，不是拿去交付）：不回写色彩元数据。
  // 代价写在 applyColorTags 上方：这条片子的 ffprobe 会显示 color_transfer=unknown，
  // 要验色彩契约请验**交付文件**（validate-video 也只认交付文件）。
  await remotionRender({project, composition, output, frames: `${start}-${end}`, concurrency, measure: (end - start + 1) >= 60, persist: false});
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
  ['export-srt', ['export-srt.py']],
  ['eval-project', ['eval-project.py']],
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
  // 3.3.0：背景库门禁（来源 / 许可 / sha256 / 亮底 / 字幕区对比度；--shots 查相邻镜重复）
  ['validate-backgrounds', ['validate-backgrounds.py']],
]);

// 交付路径收口：CLI 的 `validate-semantic-breaks` 是渲染后质检链（SKILL.md
// "Validation after rendering"、references/subtitle-timing.md）的固定入口。底层短语规则
// 找不到 BudouX 时原本只是 SKIPPED + rc=0，只有 `--require-budoux` 才硬失败 —— 而交付链上
// 没有任何调用方带这个开关，这正是本门禁要消灭的"跳过即静默放行"降级路径。现在由 CLI 收口：
//   · 从 CAPTION_CUES_JSON 所在目录逐级向上探测 node_modules/budoux/module/index.js
//     （判据与 validate-semantic-breaks.py 的 find_budoux_root 同一 marker）；
//   · 探测到 → 注入 `--budoux-dir <该 node_modules> --require-budoux`（真正跑短语规则）；
//   · 探测不到 → 退到技能自带的 `assets/vendor`（3.9.0 起随包分发，80 KB 中文切片）；
//   · 连自带切片都没了 → 才注入 `--require-budoux` 硬失败（那是真的坏了，报错写明两条修法）。
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
  // 找不到工程的 node_modules 时退到技能自带的切片（`assets/vendor`，见 assets/vendor/README.md）。
  // 3.9.0 之前这里直接注入 --require-budoux，于是新克隆的仓库跑交付链**必然失败**——
  // 而现在那个目录里就有一份 80 KB 的中文模型，不需要谁先去 npm ci。
  // 顺序仍然优先工程依赖：那样模型版本跟 package-lock.json 走。
  const bundled = path.resolve(SCRIPT_DIR, '..', 'assets', 'vendor');
  if (!budouxModules && fs.existsSync(path.join(bundled, marker))) budouxModules = bundled;
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
// 3.9.0：showcase / showcase-sheet / craft-sheet 是同一件事的三个入口（都是"组件样张"），
// 收成一个 `showcase`，用 --sheet / --craft 选产物。命令面 42 → 39，craft-sheet 那条
// 618 字符的说明（全手册最重的一条）随之消失。**产出物一字不变**。
const showcase = async (args) => {
  const opt = parseFlags(args, 'showcase', ['sheet', 'craft', 'frame', 'scale']);
  const craft = args.includes('--craft');
  const sheet = args.includes('--sheet');
  if (craft && sheet) fail('showcase：--sheet 和 --craft 只能给一个（前者出组件库接触表，后者出手作笔刷样张）', 2);
  const positional = args.filter((a) => !a.startsWith('--'));
  const [projectArg, outputArg] = positional;
  if (!projectArg) fail('Usage: notebook-video showcase PROJECT_DIRECTORY [OUTPUT] [--sheet|--craft] [--frame=N] [--scale=S]', 2);
  const project = resolvePath(projectArg);

  if (craft) {
    const remotionCli = path.join(project, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
    if (!fs.existsSync(remotionCli)) await runNpm(['ci', '--no-audit', '--no-fund'], {cwd: project});
    if (!fs.existsSync(remotionCli)) fail(`Remotion CLI is missing after npm ci: ${remotionCli}`);
    const out = resolvePath(outputArg ?? path.join(project, 'renders', 'craft-sheet.png'));
    ensureParent(out);
    const frame = Number(opt('frame', 72));
    const scale = Number(opt('scale', 1));
    const nodeArgs = [...hideConsoleArgs(), remotionCli, 'still', REMOTION_ENTRY_POINT, 'NotebookVideoCraftSheet', out, `--frame=${frame}`, `--scale=${scale}`];
    const browser = resolveBrowserExecutable();
    if (browser) nodeArgs.push(`--browser-executable=${browser}`);
    await run(process.execPath, nodeArgs, {cwd: project});
    console.log(`Craft sheet written: ${out} — 读它判断当前皮肤下的手作组件（references/craft-kit.md）。`);
    return;
  }

  // 两个产物**各自**有自己的路径：视频是 mp4、接触表是 jpg。
  // （旧版把同一个 outputArg 同时当成两者的路径 —— 传了输出路径时，最后那步抽帧会用
  //  一张 jpg 覆盖掉刚渲好的 mp4；默认路径下看不出来，因为两个默认路径本来就不同。）
  const mp4 = resolvePath(!sheet && outputArg ? outputArg : path.join(project, 'renders', 'showcase.mp4'));
  const jpg = resolvePath(sheet && outputArg ? outputArg : path.join(project, 'renders', 'showcase-sheet.jpg'));
  ensureParent(mp4);
  ensureParent(jpg);
  if (!sheet || !isNonEmptyFile(mp4)) {
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
  console.log('读它按样子挑组件；见 references/media-routing.md §6。');
};

const deliver = async (args) => {
  const positional = args.filter((a) => !a.startsWith('--'));
  const [projectArg] = positional;
  if (!projectArg) fail('Usage: notebook-video deliver PROJECT_DIRECTORY', 2);
  const project = resolvePath(projectArg);
  const cues = path.join(project, 'manifests', 'caption-cues.json');
  const srtOut = path.join(project, 'renders', 'captions.srt');
  if (fs.existsSync(cues)) {
    const r = await runPython('export-srt.py', [cues, srtOut], {capture: true});
    if (r.code) fail(`字幕导出失败：${(r.stdout + r.stderr).trim().split('\n').slice(-1)[0] || r.code}`, 1);
    console.log(`Subtitle: ${srtOut}`);
  } else {
    console.warn(`没有 ${cues}：跳过字幕导出`);
  }
  await poster([project]);
};

const usage = () => {  console.log(`Notebook Video cross-platform CLI\n\nCommands:\n  check-deps\n  fonts [--serif]   (download the pinned LXGW WenKai Lite fonts once — plus Noto Serif SC with --serif; new-project does this automatically)\n  validate-skill\n  new-project PROJECT_DIRECTORY [--style=flat|cel|journal|papercut|archive]\n  build-semantic-captions WORD_TIMING_JSON SEMANTIC_LINES OUTPUT_JSON [options]\n  match-timing PROJECT_DIRECTORY [--lock]\n  sync PROJECT_DIRECTORY\n  prepare-browser PROJECT_DIRECTORY\n  render-range PROJECT_DIRECTORY OUTPUT_MP4 START_FRAME END_FRAME [COMPOSITION_ID]
  preview PROJECT_DIRECTORY [--seconds=30] [--from=SEC] [--shot=ID] [--scale=0.5] [--fx=on]   (3.8.0: 30 s low-res check before the full render; 卷页默认关)\n  sweep PROJECT_DIRECTORY [--scale=0.5] [--cols=4] [--plan] [--json]   (3.9.0: 每镜末段扫一遍，全片都量到——preview 只看开头，尾巴容易漏)\n  review-frames PROJECT_DIRECTORY OUTPUT_MP4 START_FRAME END_FRAME [COMPOSITION_ID]\n  render PROJECT_DIRECTORY OUTPUT_MP4 [COMPOSITION_ID]\n  validate-video VIDEO_MP4 EXPECTED_DURATION [CONTACT_SHEET_JPG]\n  validate-caption-sync WORD_TIMING_JSON CAPTION_CUES_JSON\n  validate-semantic-breaks CAPTION_CUES_JSON PROTECTED_PHRASES_TXT [--budoux-dir DIR|--no-budoux]\n  (delivery default: the CLI auto-detects the project node_modules/budoux and always adds --require-budoux; a missing BudouX fails instead of silently skipping — pass --no-budoux to skip the phrase rule on purpose)\n  validate-visual-plan PROJECT_DIRECTORY\nresolve-shots PROJECT_DIRECTORY [--check]\nvalidate-shot-motion PROJECT_DIRECTORY\nvalidate-composition PROJECT_DIRECTORY [--strict]\nvalidate-frame-props PROJECT_DIRECTORY\nvalidate-audio-levels PROJECT_DIRECTORY\nvalidate-treatment PROJECT_DIRECTORY   (3.3.0 director layer: manifests/treatment.json)\nvalidate-opening PROJECT_DIRECTORY [--video MP4]   (3.3.0 first three seconds: cold open, first caption, beats, pixels)\nsilent-timing LINES_TXT OUT_JSON [--cps N] [--project DIR]   (3.3.0 caption timing without TTS; hand-made skins default 6.5 chars/s)\nvalidate-backgrounds PROJECT_DIRECTORY [--shots] [--recompute]   (3.3.0 background library: manifests/backgrounds.json)\nvalidate-media PROJECT_DIRECTORY\nprepare-media PROJECT_DIRECTORY [--add FILE --id ID …]\ncommons search \"QUERY\" [--type image|video|audio] [--source commons|openverse] [--audio-category music|sound_effect] [--project DIR] | commons add PROJECT \"File:…\" --id ID | commons credits PROJECT\nvalidate-ocr PROJECT_DIRECTORY --video MP4 | --stills DIR   (optional: needs pip rapidocr onnxruntime)\nshowcase PROJECT_DIRECTORY [OUTPUT] [--sheet|--craft] [--frame=N] [--scale=S]   (组件样张：默认出库的 mp4+接触表，--sheet 只要接触表，--craft 出手作笔刷样张)
poster PROJECT_DIRECTORY [OUTPUT_JPG] [--frame=N|--shot=ID] [--scale=1]   (3.9.0: one cover still — a settled frame of the signature shot, captions suppressed)
deliver PROJECT_DIRECTORY   (3.9.0: subtitles + cover for a finished project, re-runnable without re-rendering)
export-srt CAPTION_CUES_JSON OUTPUT_SRT [--offset-ms N]   (3.9.0: delivery subtitles from the cues the film already uses)
eval-project PROJECT_A [PROJECT_B] [--json]   (3.9.0: measure one film, or diff two versions — numbers only, no score)\nfx-probe PROJECT_DIRECTORY [--force]   (3.3.0: can this machine draw the WebGPU page turn? prints JSON; render runs it automatically)\n  package PROJECT_DIRECTORY OUTPUT_ZIP\n\nTTS is provider-neutral: supply audio/narration.mp3 and audio/narration.mp3.json using the documented adapter contract.\nGenerated or supplied raster assets are provider-neutral: register used files in manifests/visual-assets.json.\nThe same command works on macOS, Linux, Windows Command Prompt and PowerShell.`);
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
    case 'render-range': return renderRange(args);
    case 'preview': return preview(args);
    case 'sweep': return sweep(args);
    case 'review-frames': return reviewFrames(args);
    case 'render': return render(args);
    case 'showcase': return showcase(args);
    case 'poster': return poster(args);
    case 'deliver': return deliver(args);
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
