// P0-04 的行为探针：不依赖 Remotion，只验证锁与指纹的判定。
// 由 tests/test_render_lock.py 调用；任何一条不成立就非零退出。
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {acquireRenderLock, canResume, inputFingerprint, lockPathFor, manifestPathFor,
        readManifest, writeManifest} from '../../scripts/render-lock.mjs';

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'nv-lock-probe-'));
const project = path.join(tmp, 'proj');
fs.mkdirSync(path.join(project, 'src'), {recursive: true});
fs.mkdirSync(path.join(project, 'manifests'), {recursive: true});
fs.writeFileSync(path.join(project, 'src', 'a.tsx'), 'export const A = 1;\n');
fs.writeFileSync(path.join(project, 'manifests', 'shots.json'), '{"shots":[]}\n');

// ── 1. 指纹只认内容，不认 mtime ──────────────────────────────────────────────
const fp1 = inputFingerprint(project);
const old = new Date('2020-01-01T00:00:00Z');
fs.utimesSync(path.join(project, 'src', 'a.tsx'), old, old);      // 只改时间
assert.equal(inputFingerprint(project), fp1, 'mtime 变了但内容没变，指纹不该变');
fs.writeFileSync(path.join(project, 'src', 'a.tsx'), 'export const A = 2;\n');
const fp2 = inputFingerprint(project);
assert.notEqual(fp2, fp1, '内容变了，指纹必须变');
fs.writeFileSync(path.join(project, 'src', 'b.tsx'), 'export const B = 1;\n');
assert.notEqual(inputFingerprint(project), fp2, '新增文件也要改变指纹');

// ── 2. 活着的持有者 → 拒绝 ────────────────────────────────────────────────────
const lock = lockPathFor('probe-live');
fs.rmSync(lock, {force: true});
fs.writeFileSync(lock, JSON.stringify({pid: process.ppid, startedAt: 'x'}));   // 父进程一定活着
const blocked = acquireRenderLock(lock, {project: 'p'});
assert.equal(blocked.ok, false, '另一个活进程持锁时必须拒绝');
assert.equal(blocked.holder.pid, process.ppid);

// ── 3. 死掉的持有者 → 接管并说明 ─────────────────────────────────────────────
const staleLock = lockPathFor('probe-stale');
fs.rmSync(staleLock, {force: true});
fs.writeFileSync(staleLock, JSON.stringify({pid: 999999, startedAt: 'x'}));
const taken = acquireRenderLock(staleLock, {project: 'p'});
assert.equal(taken.ok, true, '持有者已死，必须能接管');
assert.equal(taken.tookOver, true, '接管要显式标记，不能静默');

// ── 4. 归一释放：第二个进程才能拿到 ──────────────────────────────────────────
taken.release();
const again = acquireRenderLock(staleLock, {project: 'p'});
assert.equal(again.ok, true, '释放后必须能再取');
assert.equal(again.tookOver, false, '干净释放后不该算接管');
again.release();

// ── 5. resume 只认 raw-complete + 指纹一致 ────────────────────────────────────
const raw = path.join(tmp, 'raw.mp4');
const man = manifestPathFor(raw);
assert.equal(canResume({manifest: null, fingerprint: fp2, rawExists: true}).resume, false, '没有 manifest 不许续');
writeManifest(man, {state: 'running', fingerprint: fp2});
assert.equal(canResume({manifest: readManifest(man), fingerprint: fp2, rawExists: true}).resume, false, '写了一半不许续');
writeManifest(man, {state: 'raw-complete', fingerprint: fp2});
assert.equal(canResume({manifest: readManifest(man), fingerprint: fp2, rawExists: true}).resume, true, '完整且指纹一致要能续');
assert.equal(canResume({manifest: readManifest(man), fingerprint: fp1, rawExists: true}).resume, false, '指纹不同不许续');
assert.equal(canResume({manifest: readManifest(man), fingerprint: fp2, rawExists: false}).resume, false, 'raw 不在不许续');
writeManifest(man, {state: 'delivered'});
assert.equal(canResume({manifest: readManifest(man), fingerprint: fp2, rawExists: true}).resume, false, '已交付不该再续');

console.log('render-lock probe: 5/5 OK');
