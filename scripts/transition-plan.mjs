// transition-plan.mjs · 分镜转场计划（卷页窗口的唯一真源）
//
// 为什么要这一层：`render` 要按帧窗把「GPU 卷页片段」拼回整片，窗口原先靠**逐行正则扫 src/shots.ts**。
// shots.ts 是生成物（resolve-shots 从 manifests/shots.json 写出来，一行一镜、字段极多），
// 正则隐含三条契约：① `from:` 与 `id:` 必须同一行；② `from` 必须在 `id` 之后也能命中（顺序变了就漏）；
// ③ 新字段里出现 `from:` 也不会误伤。任何一条被格式化 / 换行 / 注释 / 生成方式变化打破，
// 症状都不是报错，而是**某些翻页悄悄退回折痕版**：渲染成功、时长照对、门禁照样过。
//
// 现在：以 `manifests/shots.resolved.json`（resolve-shots 的产物，结构化）为输入，
// `src/shots.ts` 只在旧工程没有 manifest 时兜底，并打一次 warn（让人知道这条片子走的是旧路径）。
//
// 判据本身（哪种转场是卷页）必须与引擎一致，唯一真源是 `src/cinema.tsx` 的 resolveTransition；
// 这里逐条复刻，并由 tests/test_transition_plan.py 与源码交叉校验。

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import {fileURLToPath} from 'node:url';

/** 卷页转场时长（帧），与 src/fx.tsx 的 CURL_FRAMES 同值（tests/test_fx.py 交叉校验）。 */
export const CURL_FRAMES = 22;

/** 引擎里「显式写死、且不需要 WebGPU」的转场（cinema.tsx 第一段直接 return 的那批）。 */
const EXPLICIT_PLAIN = new Set(['hard', 'fade', 'zoom', 'whip-left', 'whip-right', 'slide', 'drop']);

/**
 * 某镜的**有效**转场：与 cinema.tsx 的 resolveTransition 同规则。
 * @returns {string|null} null = 没有转场（首镜）
 */
export const effectiveTransition = (declared, index, craftTransition = null) => {
  if (index === 0) return null;
  const d = String(declared ?? 'auto').trim();
  if (EXPLICIT_PLAIN.has(d)) return d;
  if (d === 'pageturn' || d === 'peel') return d;
  if (d === 'whip') return index % 2 ? 'whip-left' : 'whip-right'; // 引擎按镜号交替，不是随机
  if (craftTransition === 'pageturn' || craftTransition === 'peel') return craftTransition;
  if (craftTransition === 'slide' || craftTransition === 'drop') return craftTransition;
  // 既没声明卷页、皮肤也没声明 → pageflip（纯 CSS 折痕翻页，不需要 WebGPU）。3.9.0 的缺省。
  // cut / reveal / handoff / 未知名在引擎里**没有**单独分支，同样落到这里——别为了"看起来更合理"给它们单开分支，
  // 那会让本函数与 resolveTransition 悄悄分叉，而症状只是某处翻页换了种翻法。
  return 'pageflip';
};

export const isCurlKind = (kind) => kind === 'pageturn' || kind === 'peel';

const read = (p) => { try { return fs.readFileSync(p, 'utf8'); } catch { return ''; } };
const readJson = (p) => { try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return null; } };

/** 皮肤声明的媒介转场（craft.transition）。只在 `craft: {…}` 那一段里找，避免命中别处的同名键。 */
export const readCraftTransition = (themeFile) => {
  const src = read(themeFile);
  if (!src) return null;
  const at = src.search(/\bcraft\s*:\s*\{/);
  const scope = at >= 0 ? src.slice(at, at + 900) : src;
  const m = scope.match(/\btransition\s*:\s*['"]([\w-]+)['"]/);
  return m ? m[1] : null;
};

/** active.ts 的皮肤名（机器生成的 3 行文件；manifest 有 theme 时不读它）。 */
const activeSkin = (project) => {
  const m = read(path.join(project, 'src', 'theme', 'active.ts')).match(/from\s+['"]\.\/([\w-]+)['"]/);
  return m ? m[1] : null;
};

const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null);

/**
 * 读结构化分镜表。返回 {shots:[{id,from,to,transition,index}], duration, theme, craftTransition, source, problems}。
 * source: 'manifest' | 'typescript' | 'none'。
 */
export const readShotPlan = (project) => {
  const problems = [];
  let shots = null;
  let duration = null;
  let theme = null;
  let source = 'none';

  const doc = readJson(path.join(project, 'manifests', 'shots.resolved.json'));
  if (doc && Array.isArray(doc.shots) && doc.shots.length) {
    const rows = doc.shots.map((s, i) => ({i, s}));
    const bad = rows.filter(({s}) => !s || typeof s.id !== 'string' || num(s.from) === null || num(s.from) < 0);
    if (!bad.length) {
      const ids = new Set();
      for (const {s} of rows) {
        if (ids.has(s.id)) problems.push(`shots.resolved.json 里镜号重复：${s.id}`);
        ids.add(s.id);
      }
      const sorted = [...rows].sort((a, b) => num(a.s.from) - num(b.s.from));
      if (sorted.some(({i}, k) => i !== k)) problems.push('shots.resolved.json 的镜序与 from 不一致，已按 from 排序');
      shots = sorted.map(({s}, k) => ({
        id: s.id,
        from: num(s.from),
        to: num(s.to),
        transition: typeof s.transition === 'string' ? s.transition : null,
        index: k,
      }));
      duration = num(doc.duration) ?? shots.at(-1)?.to ?? null;
      theme = typeof doc.theme === 'string' ? doc.theme : null;
      source = 'manifest';
    } else {
      problems.push(`shots.resolved.json 有 ${bad.length} 镜缺 id / from，退回解析 src/shots.ts`);
    }
  } else if (doc) {
    problems.push('manifests/shots.resolved.json 里没有 shots 数组，退回解析 src/shots.ts');
  }

  if (!shots) {
    // 旧工程兜底：一行一镜的正则。它比 manifest 脆得多，所以只在没有结构化输入时用。
    const ts = read(path.join(project, 'src', 'shots.ts'));
    const rows = [];
    ts.split('\n').forEach((line, i) => {
      const from = line.match(/\bfrom\s*:\s*(\d+)/);
      if (!from) return;
      const id = (line.match(/\bid\s*:\s*['"]([\w-]+)['"]/) ?? [])[1];
      if (!id) return;
      const to = (line.match(/\bto\s*:\s*(\d+)/) ?? [])[1];
      rows.push({id, from: Number(from[1]), to: to === undefined ? null : Number(to), transition: (line.match(/\btransition\s*:\s*['"]([\w-]+)['"]/) ?? [])[1] ?? null, index: rows.length});
    });
    if (rows.length) {
      // 镜序 = 在片中的位置。旧路径只拿到解析得出的行，若首行不是 from:0（中间某镜写法特殊没解析出来），
      // 它仍然是「第二镜之后」，不能当成首镜——否则那一处翻页会被误判成「首镜没有转场」而漏掉。
      rows.sort((a, b) => a.from - b.from);
      const offset = rows[0].from === 0 ? 0 : 1;
      rows.forEach((r, i) => { r.index = i + offset; });
      shots = rows;
      duration = Number((ts.match(/SHOT_TOTAL\s*=\s*(\d+)/) ?? [])[1]) || rows.at(-1)?.to || null;
      source = 'typescript';
      problems.push('没有可用的 manifests/shots.resolved.json，已退回正则解析 src/shots.ts（旧路径，跑一次 resolve-shots 即可消除）');
    }
  }

  if (!theme) theme = activeSkin(project);
  const craftTransition = theme ? readCraftTransition(path.join(project, 'src', 'theme', `${theme}.tsx`)) : null;
  if (theme && !craftTransition) problems.push(`皮肤 src/theme/${theme}.tsx 里读不到 craft.transition，按「无媒介转场」处理（auto → pageflip）`);
  return {shots: shots ?? [], duration, theme, craftTransition, source, problems};
};

/**
 * 逐镜的转场结论 + 卷页帧窗（未合并）。窗口**宁多勿少**：多拼一个窗口只是那 22 帧换完整版 Chrome 再渲一遍
 * （同一合成、同一帧 → 同样的画面）；少拼一个则那一处留着折痕版，观众看到的是另一种翻页。
 */
export const curlPlan = (project, total = Infinity) => {
  const plan = readShotPlan(project);
  // total 缺省用 manifest 自己的总帧数：窗口不截尾会伸到片尾之外，拼接时那一段 trim 拿不满帧，
  // concat 出来的总长就少几帧——症状是「最后一处翻页之后画面轻微跳一下」，很难查。
  const limit = Number.isFinite(total) ? total : (Number.isFinite(plan.duration) && plan.duration > 0 ? plan.duration : Infinity);
  const boundaries = plan.shots.map((s) => {
    const kind = effectiveTransition(s.transition, s.index, plan.craftTransition);
    return {...s, kind, curl: isCurlKind(kind)};
  });
  const raw = boundaries.filter((b) => b.curl).map((b) => [b.from, Math.min(limit - 1, b.from + CURL_FRAMES - 1)]);
  const windows = [];
  for (const w of raw) {
    const last = windows.at(-1);
    if (last && w[0] <= last[1] + 1) last[1] = Math.max(last[1], w[1]);
    else windows.push([...w]);
  }
  return {windows, boundaries, ...plan};
};

/** 成片里可能出现卷页的帧窗 [[a, b], …]（含两端、已合并）。fx-browser 与 notebook-video 都调它。 */
export const curlWindows = (project, total = Infinity) => curlPlan(project, total).windows;

/** 本片是否用到卷页（决定要不要去找完整版 Chromium、要不要跑探针）。 */
export const projectUsesCurl = (project) => curlPlan(project).boundaries.some((b) => b.curl);

const warned = new Set();
/** 退回正则路径时提示一次：这是「隐性契约又回来了」的唯一信号。 */
export const warnFallback = (project, problems, log = console.error) => {
  if (!problems.some((p) => p.includes('退回'))) return;
  const key = path.resolve(project);
  if (warned.has(key)) return;
  warned.add(key);
  log(`  ! 转场计划：${problems.find((p) => p.includes('退回'))}`);
};

// CLI：node scripts/transition-plan.mjs <工程> [--json]
// 给测试与人工排查用：一次看清「每镜声明了什么、引擎会用什么、哪几帧要卷页」。
if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1]) && !process.argv.includes('--self-test')) {
  const project = process.argv[2];
  if (!project) { console.error('Usage: node scripts/transition-plan.mjs PROJECT_DIRECTORY [--json]'); process.exit(2); }
  const plan = curlPlan(path.resolve(project));
  if (process.argv.includes('--json')) {
    console.log(JSON.stringify(plan, null, 2));
  } else {
    console.log(`来源：${plan.source}｜皮肤：${plan.theme ?? '?'}（craft.transition=${plan.craftTransition ?? '无'}）｜总帧 ${plan.duration ?? '?'}`);
    for (const b of plan.boundaries) console.log(`  ${b.id.padStart(4)} ${String(b.from).padStart(5)} ${(b.transition ?? 'auto').padEnd(9)} → ${String(b.kind).padEnd(9)} ${b.curl ? '卷页' : ''}`);
    console.log(`卷页窗口：${plan.windows.length ? plan.windows.map(([a, b]) => `${a}-${b}`).join(', ') : '无'}`);
    for (const p of plan.problems) console.log(`  ! ${p}`);
  }
  process.exit(0);
}
