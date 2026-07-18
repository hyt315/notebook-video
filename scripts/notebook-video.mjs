#!/usr/bin/env node
import {spawn, spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import {fileURLToPath} from 'node:url';

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

const newProject = async ([targetArg]) => {
  if (!targetArg) fail('Usage: notebook-video new-project PROJECT_DIRECTORY', 2);
  const target = resolvePath(targetArg);
  if (fs.existsSync(target)) {
    if (!fs.statSync(target).isDirectory()) fail(`Target exists and is not a directory: ${target}`);
    if (fs.readdirSync(target).length > 0) fail(`Target directory must be empty to prevent stale project files: ${target}`);
  } else fs.mkdirSync(target, {recursive: true});

  fs.cpSync(path.join(SKILL_DIR, 'assets', 'example-project'), target, {recursive: true, force: true});
  const fontDir = path.join(SKILL_DIR, 'assets', 'fonts');
  const publicDir = path.join(target, 'public');
  fs.mkdirSync(publicDir, {recursive: true});
  for (const name of [
    'SourceHanSansCN-Regular.otf',
    'SourceHanSansCN-Bold.otf',
    'SourceHanSans-LICENSE.txt',
    'SmileySans-Oblique.otf',
    'SmileySans-LICENSE.txt',
  ]) fs.copyFileSync(path.join(fontDir, name), path.join(publicDir, name));
  fs.mkdirSync(path.join(target, 'renders'), {recursive: true});
  console.log(`Created official v8 performance Remotion notebook project: ${target}`);
  console.log('Preserve the engine, background, subtitle, chrome, asset gate, audio tree and frame conventions. Replace topic content and semantic scene objects.');
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

const remotionRender = async ({project, composition, output, frames, concurrency}) => {
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
  nodeArgs.push(remotionCli, 'render', composition, output, '--entry-point=src/index.tsx', '--codec=h264', '--crf=16', `--concurrency=${concurrency}`);
  if (frames) nodeArgs.push(`--frames=${frames}`);
  const browserExecutable = process.env.REMOTION_BROWSER_EXECUTABLE;
  if (browserExecutable) {
    const resolved = resolvePath(browserExecutable);
    if (!fs.existsSync(resolved)) fail(`REMOTION_BROWSER_EXECUTABLE does not exist: ${resolved}`);
    nodeArgs.push(`--browser-executable=${resolved}`);
  }
  await run(process.execPath, nodeArgs, {cwd: project});
};

const render = async ([projectArg, outputArg, composition = 'NotebookVideoFilm']) => {
  if (!projectArg || !outputArg) fail('Usage: notebook-video render PROJECT_DIRECTORY OUTPUT_MP4 [COMPOSITION_ID]', 2);
  const project = resolvePath(projectArg);
  const output = resolvePath(outputArg);
  await syncProjectAssets([project]);
  const raw = path.join(project, 'renders', '.remotion-raw.mp4');
  fs.mkdirSync(path.dirname(raw), {recursive: true});
  ensureParent(output);
  const concurrency = Number(process.env.REMOTION_CONCURRENCY || suggestedConcurrency());
  console.log(`Rendering at concurrency ${concurrency}. Override with REMOTION_CONCURRENCY after running benchmark-render.`);
  await remotionRender({project, composition, output: raw, concurrency});
  await run('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-i', raw, '-map', '0:v:0', '-map', '0:a:0', '-c:v', 'copy', '-af', 'loudnorm=I=-16:LRA=11:TP=-1.5', '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', output]);
  fs.rmSync(raw, {force: true});
  console.log(`Rendered and normalized: ${output}`);
};

const renderRange = async ([projectArg, outputArg, startArg, endArg, composition = 'NotebookVideoFilm']) => {
  if (!projectArg || !outputArg || startArg === undefined || endArg === undefined) fail('Usage: notebook-video render-range PROJECT_DIRECTORY OUTPUT_MP4 START_FRAME END_FRAME [COMPOSITION_ID]', 2);
  const start = Number(startArg), end = Number(endArg);
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end < start) fail(`Invalid frame range: ${startArg}-${endArg}`);
  const project = resolvePath(projectArg), output = resolvePath(outputArg);
  await syncProjectAssets([project]);
  const concurrency = Number(process.env.REMOTION_CONCURRENCY || suggestedConcurrency());
  await remotionRender({project, composition, output, frames: `${start}-${end}`, concurrency});
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
    await remotionRender({project, composition, output, frames: '0-89', concurrency});
    const seconds = (Date.now() - started) / 1000;
    fs.rmSync(output, {force: true});
    results.push({concurrency, seconds});
    console.log(`concurrency ${concurrency}: ${seconds.toFixed(1)}s`);
  }
  results.sort((a, b) => a.seconds - b.seconds);
  console.log(`Recommended: REMOTION_CONCURRENCY=${results[0].concurrency}`);
};

const validateVideo = async ([videoArg, expectedArg, contactArg]) => {
  if (!videoArg || !expectedArg) fail('Usage: notebook-video validate-video VIDEO_MP4 EXPECTED_DURATION [CONTACT_SHEET_JPG]', 2);
  const video = resolvePath(videoArg);
  const expected = Number(expectedArg);
  if (!Number.isFinite(expected) || expected <= 0) fail(`EXPECTED_DURATION must be a positive number: ${expectedArg}`);
  if (!isNonEmptyFile(video)) fail(`Video is missing or empty: ${video}`);
  const contact = contactArg ? resolvePath(contactArg) : path.join(path.dirname(video), 'contact-sheet.jpg');
  const probe = await run('ffprobe', ['-v', 'error', '-show_entries', 'stream=codec_name,codec_type,width,height,r_frame_rate,duration,sample_rate,channels', '-show_entries', 'format=duration', '-of', 'json', video], {capture: true});
  const data = JSON.parse(probe.stdout);
  const streams = data.streams ?? [];
  const videoStream = streams.find((s) => s.codec_type === 'video');
  const audioStream = streams.find((s) => s.codec_type === 'audio');
  if (!videoStream || !audioStream) fail('Both video and audio streams are required.');
  if (videoStream.codec_name !== 'h264' || audioStream.codec_name !== 'aac') fail('Expected H.264 video and AAC audio.');
  if (videoStream.width !== 2560 || videoStream.height !== 1440) fail(`Expected 2560x1440, got ${videoStream.width}x${videoStream.height}.`);
  const expectedFps = Number(process.env.NOTEBOOK_VIDEO_FPS || 30);
  if (videoStream.r_frame_rate !== `${expectedFps}/1`) fail(`Expected ${expectedFps}fps, got ${videoStream.r_frame_rate}.`);
  if (String(audioStream.sample_rate) !== '48000' || Number(audioStream.channels) !== 2) fail('Expected 48kHz stereo audio.');
  const duration = Number(data.format?.duration);
  if (Math.abs(duration - expected) > 0.2) fail(`Duration mismatch: ${duration} vs ${expected}`);
  console.log(`container valid: H.264/AAC 2560x1440 ${expectedFps}fps, ${duration.toFixed(3)}s`);

  const black = await run('ffmpeg', ['-hide_banner', '-i', video, '-vf', 'blackdetect=d=0.15:pix_th=0.02', '-an', '-f', 'null', '-'], {capture: true, allowFailure: true});
  const blackLog = `${black.stdout}\n${black.stderr}`;
  if (/black_(start|end)/.test(blackLog)) fail(`Black frames detected:\n${blackLog.match(/.*black_(?:start|end).*$/gm)?.join('\n') ?? blackLog}`);

  const loud = await run('ffmpeg', ['-hide_banner', '-i', video, '-af', 'loudnorm=I=-16:LRA=11:TP=-1.5:print_format=summary', '-f', 'null', '-'], {capture: true, allowFailure: true});
  const loudLog = `${loud.stdout}\n${loud.stderr}`;
  const integrated = Number(loudLog.match(/Input Integrated:\s*([-0-9.]+) LUFS/)?.[1]);
  const peak = Number(loudLog.match(/Input True Peak:\s*([-0-9.]+) dBTP/)?.[1]);
  if (!Number.isFinite(integrated) || !Number.isFinite(peak)) fail('Unable to parse loudness analysis from FFmpeg output.');
  if (integrated < -18 || integrated > -14) fail(`Integrated loudness outside target range: ${integrated} LUFS`);
  if (peak > -1) fail(`True peak too high: ${peak} dBTP`);
  console.log(`audio valid: ${integrated.toFixed(1)} LUFS, ${peak.toFixed(1)} dBTP`);

  const count = expected > 60 ? 24 : 12;
  const tile = count === 24 ? '4x6' : '4x3';
  const rate = (count / expected).toFixed(12).replace(/0+$/, '').replace(/\.$/, '');
  ensureParent(contact);
  await run('ffmpeg', ['-y', '-loglevel', 'error', '-i', video, '-vf', `fps=${rate},scale=640:360,tile=${tile}`, '-frames:v', '1', contact]);
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
  ['validate-caption-sync', ['validate-caption-sync.py']],
  ['validate-semantic-breaks', ['validate-semantic-breaks.py']],
  ['validate-official-example', ['validate-official-example.py']],
]);

const usage = () => {
  console.log(`Notebook Video cross-platform CLI\n\nCommands:\n  check-deps\n  validate-skill\n  new-project PROJECT_DIRECTORY\n  build-semantic-captions WORD_TIMING_JSON SEMANTIC_LINES OUTPUT_JSON [options]\n  sync PROJECT_DIRECTORY\n  prepare-browser PROJECT_DIRECTORY\n  benchmark-render PROJECT_DIRECTORY [COMPOSITION_ID]\n  render-range PROJECT_DIRECTORY OUTPUT_MP4 START_FRAME END_FRAME [COMPOSITION_ID]\n  render PROJECT_DIRECTORY OUTPUT_MP4 [COMPOSITION_ID]\n  validate-video VIDEO_MP4 EXPECTED_DURATION [CONTACT_SHEET_JPG]\n  validate-caption-sync WORD_TIMING_JSON CAPTION_CUES_JSON\n  validate-semantic-breaks CAPTION_CUES_JSON PROTECTED_PHRASES_TXT\n  validate-official-example\n  package PROJECT_DIRECTORY OUTPUT_ZIP\n\nTTS is provider-neutral: supply audio/narration.mp3 and audio/narration.mp3.json using the documented adapter contract.\nThe same command works on macOS, Linux, Windows Command Prompt and PowerShell.`);
};

const main = async () => {
  const [command, ...args] = process.argv.slice(2);
  if (!command || command === 'help' || command === '--help' || command === '-h') return usage();
  if (pythonCommandMap.has(command)) {
    const [script] = pythonCommandMap.get(command);
    await runPython(script, args);
    return;
  }
  switch (command) {
    case 'check-deps': return checkDeps();
    case 'new-project': return newProject(args);
    case 'sync': return syncProjectAssets(args);
    case 'prepare-browser': return prepareBrowser(args);
    case 'benchmark-render': return benchmarkRender(args);
    case 'render-range': return renderRange(args);
    case 'render': return render(args);
    case 'validate-video': return validateVideo(args);
    case 'package': return packageProject(args);
    default: fail(`Unknown command: ${command}\nRun with --help for available commands.`, 2);
  }
};

main().catch((error) => {
  console.error(error?.stack || error?.message || String(error));
  process.exit(1);
});
