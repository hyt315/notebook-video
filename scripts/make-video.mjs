#!/usr/bin/env node
// ============================================================================
// make-video.mjs · 3.2.0 一条命令出片（Windows / macOS / Linux 同一套 Node 实现）
//
//   node scripts/make-video.mjs STORY.json [PROJECT_DIR] [--style=flat|cel] [--stills] [--render OUT.mp4] [--skip-review]
//   --skip-review：手作皮肤 treatment.review.rounds 为空时 --render 默认停下（3.7.0），草稿 / 自测用它显式跳过
//                                         [--scale=0.75] [--no-gates]
//
// 流程：建工程（不存在时）→ compose-story（排版 + 字幕定时 + 关键词同步 + 相机 + 自动修）
//      → 静音旁白占位（无 TTS）→ resolve-shots → 构建期门禁 → tsc
//      → --stills：一次打包、按每镜关键时刻出静帧 + 接触表 + renders/report.md（不渲整片）
//      → --render：整片渲染（响度规范化）→ 静止段门禁 → 从成片抽帧出接触表
// 硬门禁（任何一个失败就停）：字幕读速 / 每行字数 / 字号地板 / 对比度 / 取景不切字 / 静止段 / 音画同步 / 音效电平。
// 软提示（只打印建议，不拦）：动画与图标预算、同屏焦点、一镜一概念、快慢交替、相邻同版式、内容留白。
// ============================================================================
import {spawn, spawnSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import {fileURLToPath} from 'node:url';

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const IS_WIN = process.platform === 'win32';
const args = process.argv.slice(2);
const flag = (name) => args.find((a) => a === `--${name}` || a.startsWith(`--${name}=`));
const flagVal = (name, dflt) => { const f = flag(name); if (!f) return dflt; const i = f.indexOf('='); if (i > 0) return f.slice(i + 1); const k = args.indexOf(f); return args[k + 1] && !args[k + 1].startsWith('--') ? args[k + 1] : dflt; };
const positional = args.filter((a, i) => !a.startsWith('--') && !(i > 0 && /^--(render|scale|style)$/.test(args[i - 1])));
if (!positional[0]) {
  console.error('用法：node scripts/make-video.mjs STORY.json [PROJECT_DIR] [--style=flat|cel] [--stills] [--render OUT.mp4] [--scale=0.75] [--skip-review]');
  process.exit(2);
}
// 两种入口。① 工程目录（推荐，手写组件场景路线：shots.json + scenes.tsx 里用默认组件）；
//        ② STORY.json（auto 草稿路线：compose-story 自动排版）。两条路线共用 resolve → 门禁 → tsc → 静帧/渲染。
const HAND = fs.existsSync(path.join(path.resolve(positional[0]), 'src', 'index.tsx'));
const storyPath = HAND ? null : path.resolve(positional[0]);
const story = HAND ? {title: path.basename(path.resolve(positional[0]))} : JSON.parse(fs.readFileSync(storyPath, 'utf8'));
const project = HAND ? path.resolve(positional[0]) : path.resolve(positional[1] ?? storyPath.replace(/\.json$/i, '') + '-project');
const style = flagVal('style', story.theme ?? 'flat');
const scale = flagVal('scale', '0.75');
const renderOut = flag('render') ? path.resolve(flagVal('render', path.join(project, 'renders', 'final.mp4'))) : null;

const run = (cmd, argv, opts = {}) => new Promise((resolve) => {
  const child = spawn(cmd, argv, {cwd: opts.cwd, stdio: opts.capture ? ['ignore', 'pipe', 'pipe'] : 'inherit', windowsHide: true, shell: opts.shell ?? false});
  let out = '';
  if (opts.capture) { child.stdout.on('data', (d) => { out += d; }); child.stderr.on('data', (d) => { out += d; }); }
  child.on('close', (code) => resolve({code, out}));
  child.on('error', (e) => resolve({code: 127, out: String(e)}));
});
const findPython = () => {
  const cands = IS_WIN ? [['py', ['-3']], ['python', []], ['python3', []]] : [['python3', []], ['python', []]];
  for (const [c, pre] of cands) { const r = spawnSync(c, [...pre, '--version'], {stdio: 'ignore', windowsHide: true}); if (!r.error && r.status === 0) return {c, pre}; }
  console.error('找不到 Python 3（py / python / python3）。'); process.exit(2);
};
const PY = findPython();
// 中文 Windows 的控制台默认 cp936，而门禁脚本会 print「✓ ✗ ⚠」——这三个字符不在 GBK 里，
// 输出被管道捕获时（make-video 就是这么调的）会抛 UnicodeEncodeError → 门禁假失败 → 出片被拦死。
// 统一给子进程开 UTF-8 模式，比逐个脚本改 print 可靠。
const PY_UTF8_ENV = {...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1'};
const py = (script, argv, opts = {}) => run(PY.c, [...PY.pre, path.join(SCRIPT_DIR, script), ...argv], {...opts, env: PY_UTF8_ENV});
const node = (argv, opts) => run(process.execPath, argv, opts);
const step = (t) => console.log(`\n── ${t}`);
const die = (m) => { console.error(`\n✗ ${m}`); process.exit(1); };

// 1. 工程
if (!fs.existsSync(path.join(project, 'src', 'index.tsx'))) {
  step(`新建工程 ${project}（${style}）`);
  const r = await node([path.join(SCRIPT_DIR, 'notebook-video.mjs'), 'new-project', project, `--style=${style}`]);
  if (r.code) die('new-project 失败');
}
fs.mkdirSync(path.join(project, 'renders'), {recursive: true});

let rep;
if (HAND) {
  step('手写场景工程：跳过 compose-story，沿用工程自己的旁白与字幕');
  const sj = JSON.parse(fs.readFileSync(path.join(project, 'manifests', 'shots.json'), 'utf8'));
  rep = {frames: sj.duration ?? sj.total ?? Math.max(...(sj.shots ?? []).map((x) => x.to ?? 0)), fixes: [], hints: []};
  // 3.3.0 修：手写工程没有 audio/narration.mp3 时（新建工程直接 --stills 的常见情形），
  // 以前会在「同步渲染输入」处 ENOENT 崩溃。现在与 auto 路线一致：补一条静音旁白占位（不覆盖已有旁白）。
  const narr = path.join(project, 'audio', 'narration.mp3');
  if (!fs.existsSync(narr)) {
    step('没有 audio/narration.mp3：生成静音旁白占位（不做 TTS）');
    const cues = JSON.parse(fs.readFileSync(path.join(project, 'manifests', 'caption-cues.json'), 'utf8')).cues ?? [];
    const lastMs = Math.max(0, ...cues.map((c) => c.end_ms ?? c.speech_end_ms ?? 0));
    const secs = (Math.max(rep.frames / 30, lastMs / 1000) + 0.5).toFixed(2);
    const a = await run('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-t', secs, '-c:a', 'libmp3lame', '-b:a', '64k', narr]);
    if (a.code) die('ffmpeg 不可用：请安装 ffmpeg 并放进 PATH');
  }
} else {
// 2. compose
step('compose-story：排版 / 字幕定时 / 关键词同步 / 相机 / 自动修');
const reportJson = path.join(project, 'renders', 'compose-report.json');
const comp = await py('compose-story.py', [storyPath, project, '--report', reportJson]);
if (comp.code) die('compose-story 有修不了的问题（见上面的 ✗，每条都写了怎么改）');
rep = JSON.parse(fs.readFileSync(reportJson, 'utf8'));

// 3. 静音旁白占位（无 TTS）：时长 = 片长 + 0.5 s
step('静音旁白占位（不做 TTS）');
const secs = (rep.frames / 30 + 0.5).toFixed(2);
const a = await run('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-t', secs, '-c:a', 'libmp3lame', '-b:a', '64k', path.join(project, 'audio', 'narration.mp3')]);
if (a.code) die('ffmpeg 不可用：请安装 ffmpeg 并放进 PATH');
}

// 4. resolve
step('resolve-shots');
if ((await py('resolve-shots.py', [project])).code) die('resolve-shots 失败');

// 4b. 3.7.0 评审拦截：手作皮肤要出成片，先得有一轮独立评审（director-method.md 第 4 步），或显式 --skip-review。
//     只拦 --render（静帧 / 联系表就是给评审看的，不拦）；flat / cel 不拦，CI / selftest 不走 --render。
const activeSkin = (() => {
  try { return fs.readFileSync(path.join(project, 'src', 'theme', 'active.ts'), 'utf8').match(/from\s+'\.\/(\w+)'/)?.[1] ?? style; } catch { return style; }
})();
if (renderOut && ['journal', 'papercut', 'archive'].includes(activeSkin) && !flag('skip-review')) {
  let rounds = null;
  try { rounds = JSON.parse(fs.readFileSync(path.join(project, 'manifests', 'treatment.json'), 'utf8'))?.review?.rounds ?? []; } catch { rounds = null; }
  if (Array.isArray(rounds) && rounds.length === 0) {
    console.error([
      '',
      '══════════════════════════════════════════════════════════════════',
      `✗ 停在渲染前：${activeSkin} 是手作皮肤，manifests/treatment.json 的 review.rounds 还是空的。`,
      '',
      '  为什么停：手作片的问题（构图、调度、隐喻和媒介是否一致）只有独立的眼睛才看得出，',
      '  渲染一次很贵，先评审再出片（references/director-method.md 第 4 步）。',
      '',
      '  怎么评审：',
      '    1. node scripts/make-video.mjs <工程> --stills       → renders/stills-*.jpg 联系表',
      '    2. 开一个全新的会话 / 子代理，只给它：联系表 + storyboard.md（resolve-shots 自动生成）+ manifests/treatment.json，',
      '       按 references/quality-checklist.md 与 director-method.md 的评审项打分、分 P0 / P1 / P2 列问题；',
      '    3. 修掉 P0 / P1，把这一轮写进 treatment.json 的 review.rounds（时间、评审者、问题、处理）。',
      '',
      '  确实要跳过（草稿 / 自测）：加 --skip-review。',
      '══════════════════════════════════════════════════════════════════',
    ].join('\n'));
    process.exit(3);
  }
}

// 5. gates
const results = [];
if (!flag('no-gates')) {
  step('构建期门禁（硬门禁失败即停；P1 只是建议）');
  const gates = [
    ['validate-shot-motion.py', [project], true],
    ['validate-presentation.py', [project], true],
    ['validate-frame-props.py', [project], true],
    ['validate-audio-levels.py', [project], true],
    ['validate-media.py', [project], true],
    // 3.3.0 导演层：手作皮肤缺 treatment.json / 没搜过 Commons 即停；flat / cel 只提示
    ['validate-treatment.py', [project], true],
    // 3.6.0 开场 3 秒：第 0 帧就有事件、首条字幕 ≤ 1 s、片名不当第一镜、前 3 秒 ≥ 3 拍、第一句不是泛问句（手作 P0，flat / cel 只提示）
    ['validate-opening.py', [project], true],
    // 3.4.0 背景库：库本身（来源 / 许可 / sha256 / 对比度）硬拦；分镜里相邻镜同一张背景只提示
    ['validate-backgrounds.py', [project], true],
    ['validate-backgrounds.py', [project, '--shots'], true],
    ['validate-caption-sync.py', [path.join(project, 'audio', 'narration.mp3.json'), path.join(project, 'manifests', 'caption-cues.json')], true],
    ['validate-semantic-breaks.py', [path.join(project, 'manifests', 'caption-cues.json'), path.join(project, 'manifests', 'protected-caption-phrases.txt')], true],
    // 手写场景的结构门禁（骨架 / 组件多样性）：auto 版式由引擎保证结构，这里只作参考
    ['validate-composition.py', [project], HAND],
  ];
  for (const [g, argv, hard] of gates) {
    const r = await py(g, argv, {capture: true});
    const verdict = (r.out.match(/结论[^\n]*/) ?? [r.code ? 'FAIL' : 'PASS'])[0];
    results.push({gate: g, code: r.code, hard, verdict});
    console.log(`  ${r.code ? (hard ? '✗' : '·') : '✓'} ${g.padEnd(30)} ${verdict}`);
    if (r.code && hard) { console.log(r.out.split('\n').filter((l) => /P0|✗|FAIL|Error|错误/.test(l)).slice(0, 12).join('\n')); die(`${g} 未通过`); }
  }
}

// 6. tsc
step('TypeScript 检查');
const tscJs = path.join(project, 'node_modules', 'typescript', 'bin', 'tsc');
if (!fs.existsSync(tscJs)) {
  // Node 18 起禁止直接 spawn .cmd（CVE-2024-27980），Windows 上 spawn('npm.cmd') 会抛 EINVAL。
  // 优先用随 Node 安装的 npm-cli.js 直接跑；找不到才退回 shell。
  const npmCli = [
    path.join(path.dirname(process.execPath), 'node_modules', 'npm', 'bin', 'npm-cli.js'),
    path.resolve(path.dirname(process.execPath), '..', 'node_modules', 'npm', 'bin', 'npm-cli.js'),
  ].find((q) => fs.existsSync(q));
  const r = npmCli
    ? await node([npmCli, 'ci', '--no-audit', '--no-fund'], {cwd: project})
    : await run(IS_WIN ? 'npm.cmd' : 'npm', ['ci', '--no-audit', '--no-fund'], {cwd: project, shell: IS_WIN});
  if (r.code) die(`npm ci 失败（在 ${project} 里手动跑一次 npm ci 看具体报错）`);
}
if ((await node([tscJs, '--noEmit', '-p', '.'], {cwd: project})).code) die('tsc 报错（多半是 src/custom/ 里的定制组件）');

// 7. stills / render
const frameList = () => {
  const r = JSON.parse(fs.readFileSync(path.join(project, 'manifests', 'shots.resolved.json'), 'utf8'));
  let data = {};
  try { const st = fs.readFileSync(path.join(project, 'src', 'story.ts'), 'utf8'); data = JSON.parse(st.slice(st.indexOf('= {') + 2, st.lastIndexOf(';'))); } catch { /* 手写工程没有 story.ts */ }
  const out = [];
  for (const s of r.shots) {
    const sh = data[s.id];
    out.push({f: s.from + Math.min(45, Math.floor(s.duration / 3)), shot: s.id, what: `${sh?.layout ?? ''} 开场`});
    for (const k of sh?.focus ?? []) out.push({f: s.from + Math.min(s.duration - 2, k.at + 26), shot: s.id, what: `关键词「${k.term}」→ ${k.id}${k.cam ? '（推近）' : '（高亮）'}`});
    out.push({f: s.to - 6, shot: s.id, what: '镜尾'});
  }
  return out;
};
const sheet = async (pngs, out) => {
  const cols = 4, rows = Math.ceil(pngs.length / cols);
  const inputs = pngs.flatMap((p) => ['-i', p]);
  const blank = Array.from({length: rows * cols - pngs.length}, () => ['-f', 'lavfi', '-i', 'color=c=white:s=640x360']).flat();
  const n = rows * cols;
  const scaleF = Array.from({length: n}, (_, i) => `[${i}]scale=640:360[v${i}]`).join(';');
  const layout = Array.from({length: n}, (_, i) => `${(i % cols) ? Array.from({length: i % cols}, () => 'w0').join('+') : '0'}_${Math.floor(i / cols) ? Array.from({length: Math.floor(i / cols)}, () => 'h0').join('+') : '0'}`).join('|');
  return run('ffmpeg', ['-y', '-loglevel', 'error', ...inputs, ...blank, '-filter_complex', `${scaleF};${Array.from({length: n}, (_, i) => `[v${i}]`).join('')}xstack=inputs=${n}:layout=${layout}`, out]);
};
const cli = path.join(project, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
// 3.5.0 真卷页：render / fx-probe 把结论写在 renders/.fx-probe.json。本片用到 pageturn / peel 却没开成 → P1（片子照出，转场已退回 slide / drop）。
const fxNote = () => {
  try {
    const fx = JSON.parse(fs.readFileSync(path.join(project, 'renders', '.fx-probe.json'), 'utf8'));
    if (!fx.used) return [];
    return fx.on ? [`- 真卷页（pageturn / peel）：已开启（${fx.browser}；探针 ${fx.probeMs ?? '?'} ms）`]
      : [`- **P1 真卷页未开启**：${fx.reason}。本片的 pageturn / peel 已自动退回 slide / drop；要开：装完整版 Chromium（\`npx playwright install chromium\` 或设 NOTEBOOK_VIDEO_FX_BROWSER），再跑 \`node scripts/notebook-video.mjs fx-probe <工程> --force\`（见 references/fx-effects.md）`];
  } catch { return []; }
};
const writeReport = (frames, sheets, extra = '') => {
  const lines = [`# make-video 报告 · ${story.title ?? ''}`, '', `- 时长：${rep.frames} 帧（${(rep.frames / 30).toFixed(1)} 秒）`, `- 自动修：${rep.fixes.length} 条 · 建议：${rep.hints.length} 条`, ...fxNote(), '',
    '## 门禁', ...results.map((r) => `- ${r.code ? (r.hard ? '✗' : '·') : '✓'} ${r.gate} — ${r.verdict}`), '',
    '## 自动修', ...rep.fixes.map((x) => `- ${x}`), '', '## 建议（不拦）', ...rep.hints.map((x) => `- ${x}`), '',
    '## 静帧（看：字是否完整、强调是否对上台词关键词、镜头是否切到标题）', ...frames.map((x) => `- f${x.f} ${x.shot} ${x.what}`), '',
    ...sheets.map((s) => `![contact](${path.basename(s)})`), extra];
  fs.writeFileSync(path.join(project, 'renders', 'report.md'), lines.join('\n') + '\n');
};

// 同步渲染输入
fs.copyFileSync(path.join(project, 'manifests', 'caption-cues.json'), path.join(project, 'src', 'caption-cues.json'));
fs.copyFileSync(path.join(project, 'audio', 'narration.mp3'), path.join(project, 'public', 'narration.mp3'));

if (flag('stills')) {
  step('静帧报告（一次打包，逐帧出图；不渲整片）');
  const bundle = path.join(project, 'renders', '.bundle');
  fs.rmSync(bundle, {recursive: true, force: true});
  if ((await node([cli, 'bundle', 'src/index.tsx', '--out-dir', bundle], {cwd: project, capture: true})).code) die('remotion bundle 失败');
  // 3.5.0：先探一次真卷页能力，结论进报告（P1）。静帧本身不走完整版 Chrome（每帧 ~3 s）：静帧取的是镜头开场 / 关键词 / 镜尾，
  // 不落在镜头开头 22 帧的卷页窗口里（只有短于 66 帧的镜头例外，那张静帧里看到的是退回后的 slide / drop）。
  const fxr = await node([path.join(SCRIPT_DIR, 'notebook-video.mjs'), 'fx-probe', project], {capture: true});
  try { const fx = JSON.parse(fxr.out.slice(fxr.out.indexOf('{'))); if (fx.used) console.log(fx.on ? '  真卷页：探针通过（成片里开启）' : `  ⚠ P1 真卷页未开启：${fx.reason}`); } catch { /* 探针输出读不出：按未开启处理 */ }
  const frames = frameList();
  const dir = path.join(project, 'renders', 'stills');
  fs.mkdirSync(dir, {recursive: true});
  const pngs = [];
  for (const x of frames) {
    const out = path.join(dir, `f${String(x.f).padStart(5, '0')}.png`);
    const r = await node([cli, 'still', bundle, 'NotebookVideoFilm', out, `--frame=${x.f}`, '--scale=0.5'], {cwd: project, capture: true});
    if (r.code) { console.log(r.out.split('\n').filter((l) => /Error|Gate|overflow|溢出|越出/.test(l)).slice(0, 6).join('\n')); die(`静帧 f${x.f} 渲染失败（渲染期门禁拦下了，见上）`); }
    pngs.push(out);
    process.stdout.write('.');
  }
  const sheets = [];
  for (let i = 0; i < pngs.length; i += 12) {
    const out = path.join(project, 'renders', `stills-${i / 12 + 1}.jpg`);
    await sheet(pngs.slice(i, i + 12), out);
    sheets.push(out);
  }
  writeReport(frames, sheets);
  console.log(`\n✓ 静帧 ${pngs.length} 张 → ${sheets.join(', ')}；报告 renders/report.md`);
}

if (renderOut) {
  step(`整片渲染 → ${renderOut}（scale ${scale}）`);
  process.env.NOTEBOOK_VIDEO_SCALE = scale;
  // 3.6.0：静音旁白片也规范到 −16 LUFS（真峰 ≤ −1.5 dBTP），与有人声的片子同一目标。3.5.0 及以前是 −24：
  // AES TD1004 建议流媒体 −16…−20 LUFS，并点名 −23/−24 在手机上开到最大也不够响；YouTube 只压低过响的内容、不抬高轻的。
  // 要回到旧电平：NOTEBOOK_VIDEO_LUFS=-24。
  const r = await node([path.join(SCRIPT_DIR, 'notebook-video.mjs'), 'render', project, renderOut]);
  if (r.code) die('渲染失败（渲染期门禁或 Remotion 报错，见上）');
  step('成片门禁：静止段 / 编码 / 时长');
  const mg = await py('validate-motion-gaps.py', [project, '--video', renderOut], {capture: true});
  results.push({gate: 'validate-motion-gaps.py', code: mg.code, hard: true, verdict: (mg.out.match(/结论[^\n]*/) ?? [mg.code ? 'FAIL' : 'PASS'])[0]});
  console.log(`  ${mg.code ? '✗' : '✓'} validate-motion-gaps ${results.at(-1).verdict}`);
  const frames = frameList();
  const dir = path.join(project, 'renders', 'frames');
  fs.mkdirSync(dir, {recursive: true});
  const pngs = [];
  for (const x of frames) {
    const out = path.join(dir, `f${String(x.f).padStart(5, '0')}.jpg`);
    await run('ffmpeg', ['-y', '-loglevel', 'error', '-ss', (x.f / 30 + 0.001).toFixed(3), '-i', renderOut, '-frames:v', '1', '-vf', 'scale=640:360', out]);
    pngs.push(out);
  }
  const sheets = [];
  for (let i = 0; i < pngs.length; i += 12) { const out = path.join(project, 'renders', `frames-${i / 12 + 1}.jpg`); await sheet(pngs.slice(i, i + 12), out); sheets.push(out); }
  // 3.6.0：开场像素复核（第 0 / 15 / 45 / 90 帧有主体、在变化）。成片已出，不拦，P0 记进报告。
  const op = await py('validate-opening.py', [project, '--video', renderOut], {capture: true});
  results.push({gate: 'validate-opening.py --video', code: op.code, hard: false, verdict: (op.out.match(/结论[^\n]*/) ?? [op.code ? 'FAIL' : 'PASS'])[0]});
  console.log(`  ${op.code ? '·' : '✓'} validate-opening --video ${results.at(-1).verdict}`);
  if (op.code) console.log(op.out.split('\n').filter((l) => /P0/.test(l)).slice(0, 6).map((l) => `    ${l}`).join('\n'));
  // 3.3.0：字幕真的读得出吗？（RapidOCR 可选；没装 → SKIPPED，不阻断；P0 记进报告并提示，不自动拦）
  step('字幕 OCR 复核（validate-ocr，可选）');
  const ocr = await py('validate-ocr.py', [project, '--video', renderOut, '--json', path.join(project, 'renders', 'ocr.json')], {capture: true});
  const ocrVerdict = /SKIPPED/.test(ocr.out) ? 'SKIPPED（未装 RapidOCR）' : (ocr.out.match(/结论[^\n]*/) ?? [ocr.code ? 'FAIL' : 'PASS'])[0];
  results.push({gate: 'validate-ocr.py', code: ocr.code, hard: false, verdict: ocrVerdict});
  console.log(ocr.out.split('\n').filter((l) => /validate-ocr|✗|·|结论/.test(l)).slice(0, 12).map((l) => `  ${l}`).join('\n'));
  writeReport(frames, sheets, `\n成片：${renderOut}`);
  if (mg.code) die('validate-motion-gaps 未通过（画面有超长静止段）');
  console.log(`✓ 成片 ${renderOut}；抽帧接触表 ${sheets.join(', ')}；报告 renders/report.md`);
}
console.log('\n完成。');
