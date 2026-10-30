"""gates_compose.py — 3.2.0 那一批负向用例：compose-story / 自动修 / 音效元数据 / 背景库 / 评审拦截。

从 `negative-gate-check.py` 切出来的一整块（导入即注册，顺序与原先一致）。
放在单独文件里的理由：这批夹具都要"造一个带 story 的工程再跑脚本"，跟前面那些
"改一个 shots.json 字段"的夹具不是一类东西；混在一起时改一个 story 夹具要滚 800 行。
"""
import io
import json
import os
import re
import shutil
import tempfile

from gatelib import (  # noqa: F401
    PY, SKILL, SRC, TPL, case, cleanup, mkproj, resolve, results, run,
)

# ============================ 3.2.0 · compose-story / 自动修 / 音效元数据 ============================
COMPOSE = os.path.join(SKILL, 'scripts/compose-story.py')
DEMO45 = os.path.join(SKILL, 'examples/code-change-cache.story.json')


def story_case(mutate):
    td_ = tempfile.mkdtemp(prefix='nv-compose-')
    d = json.load(io.open(DEMO45, encoding='utf-8'))
    mutate(d)
    sp = os.path.join(td_, 'story.json')
    io.open(sp, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False))
    return td_, sp


def _shot(d, i):
    return [s for ch in d['chapters'] for s in ch['shots']][i]


# V1 蓝图占位符没填 → 拦
td_, sp = story_case(lambda d: _shot(d, 0)['lines'].__setitem__(0, '<<一句钩子>>'))
case('V1 compose · 蓝图占位符没填', [('must_block:占位符', 'compose-story', run([PY, COMPOSE, sp, os.path.join(td_, 'p')]))])
cleanup(td_)
# V2 台词关键词在画面上找不到 → 拦，且列出可用 id
td_, sp = story_case(lambda d: _shot(d, 1)['lines'].__setitem__(1, '慢的只有 {{/nowhere}} 一个。'))
case('V2 compose · {{关键词}} 在画面上找不到', [('must_block:可用 id', 'compose-story', run([PY, COMPOSE, sp, os.path.join(td_, 'p')]))])
cleanup(td_)
# V3 超长字幕 → 自动拆行（放行），且拆出来的每行都 ≤16 加权字
td_, sp = story_case(lambda d: _shot(d, 0)['lines'].__setitem__(0, '这个接口在高峰时段每一次请求都要等待 {{1.2 秒}} 才能返回结果。'))
r3 = run([PY, COMPOSE, sp, os.path.join(td_, 'p')])
cues3 = json.load(io.open(os.path.join(td_, 'p/manifests/caption-cues.json'), encoding='utf-8'))['cues'] if r3[0] == 0 else []
w3 = max([sum(1.0 if ord(ch) > 0x2E80 else 0.5 for ch in re.sub(r'\s+', '', c['text'])) for c in cues3] or [99])
case('V3 compose · 超长字幕自动拆行（不拦）且每行 ≤16', [('must_warn:自动拆成', 'compose-story', r3),
     ('must_pass', f'最长一行 {w3:g} 加权字', (0 if w3 <= 16 else 1, ''))])
cleanup(td_)
# V4 代码行太长（32px 地板也放不下）→ 拦，并写明每行上限
td_, sp = story_case(lambda d: _shot(d, 3)['content'].__setitem__('code', 'x = ' + 'a_very_long_identifier + ' * 6 + '1'))
case('V4 compose · 代码行放不下', [('must_block:每行请', 'compose-story', run([PY, COMPOSE, sp, os.path.join(td_, 'p')]))])
cleanup(td_)
# V5 相邻同版式 statement → 自动换变体（不拦）
def _v5(d):
    d['chapters'][-1]['shots'].append({"layout": "statement", "lines": ["再说一遍：先量再改。"], "content": {"text": "先量，再改"}})
td_, sp = story_case(_v5)
case('V5 compose · 相邻同版式自动换变体', [('must_warn:自动换成变体', 'compose-story', run([PY, COMPOSE, sp, os.path.join(td_, 'p')]))])
cleanup(td_)
# V6 取景不切字：demo 每一个相机关键帧都不许把任何文字元素切成两半（自动回退推近倍数的结果）
td_, sp = story_case(lambda d: None)
r6 = run([PY, COMPOSE, sp, os.path.join(td_, 'p')])
import importlib.util as _ilu
_spc = _ilu.spec_from_file_location('_cs', COMPOSE); _cs = _ilu.module_from_spec(_spc); _spc.loader.exec_module(_cs)
_st = io.open(os.path.join(td_, 'p/src/story.ts'), encoding='utf-8').read()
_story = json.loads(_st[_st.index('= {') + 2:_st.rindex(';')])
_shots = json.load(io.open(os.path.join(td_, 'p/manifests/shots.json'), encoding='utf-8'))['shots']
_bad = [(s['id'], k['at']) for s in _shots for k in s['cinema']['path'] if _cs.partial_clips((k['x'], k['y']), k['s'], _story[s['id']]['elements'])]
case('V6 compose · 相机路径不切字（全部关键帧）', [('must_pass', f'{sum(len(s["cinema"]["path"]) for s in _shots)} 个关键帧，切字 {len(_bad)} 处 {_bad[:3]}', (0 if r6[0] == 0 and not _bad else 1, ''))])
cleanup(td_)
# V7 文字优先版式的留白只提示、不拦（主观规则不许硬拦）
td_, sp = story_case(lambda d: None)
run([PY, COMPOSE, sp, os.path.join(td_, 'p')])
run([PY, os.path.join(SKILL, 'scripts/resolve-shots.py'), os.path.join(td_, 'p')])
case('V7 shot-motion · statement 留白只提示（P1）', [('must_warn:留白是有意的', 'validate-shot-motion', run([PY, os.path.join(SKILL, 'scripts/validate-shot-motion.py'), os.path.join(td_, 'p')]))])
cleanup(td_)
# V8 手写场景的「死尾巴」→ resolve 自动补收束焦点
def _v8(d):
    d['shots'][-1]['beats'] = d['shots'][-1]['beats'][:1]
    return d
td, _rc8, _out8 = mkproj(_v8)
_r8 = json.load(io.open(os.path.join(td, 'manifests/shots.resolved.json'), encoding='utf-8'))['shots'][-1]
_settle = [k for k in (_r8.get('cinema') or {}).get('focus', []) if k.get('settle')]
case('V8 resolve · 镜尾 >1.5s 无事件 → 自动收束焦点', [('must_pass', f'settle 焦点 {len(_settle)} 个', (0 if _settle else 1, ''))])
cleanup(td)
# V9 音效增益与库元数据不一致 → 拦（3.2.0 增益以 manifest 为准）
td = tempfile.mkdtemp(prefix='nv-sfx-')
shutil.copytree(os.path.join(TPL, 'public'), os.path.join(td, 'public'))
os.makedirs(os.path.join(td, 'src'))
_sfx = io.open(os.path.join(TPL, 'src/sfx.ts'), encoding='utf-8').read()
if 'highlight: 0.356' not in _sfx:
    raise SystemExit('V9 夹具锚点没找到：sfx.ts 的 SFX_GAIN.highlight 写法变了')
io.open(os.path.join(td, 'src/sfx.ts'), 'w', encoding='utf-8').write(_sfx.replace('highlight: 0.356', 'highlight: 0.6', 1))
case('V9 audio-levels · SFX_GAIN 与 manifest gain 漂移', [('must_block:不一致', 'validate-audio-levels', run([PY, os.path.join(SKILL, 'scripts/validate-audio-levels.py'), td]))])
cleanup(td)

# ---------------------------------------------------------------- 3.2.0 真实素材门禁（validate-media / prepare-media）
VMEDIA = os.path.join(SKILL, 'scripts/validate-media.py')
PMEDIA = os.path.join(SKILL, 'scripts/prepare-media.py')
PNG = os.path.join(SKILL, 'examples/real-media/pr-placeholder.png')
def media_proj(entry_mut=None, scene=None, add=True):
    td = tempfile.mkdtemp(prefix='nv-media-')
    for d in ('manifests', 'src', 'public/media'):
        os.makedirs(os.path.join(td, d), exist_ok=True)
    io.open(os.path.join(td, 'manifests/media.json'), 'w', encoding='utf-8').write('{"items": []}')
    if add:
        run([PY, PMEDIA, td, '--add', PNG, '--id', 'pr', '--region', 'diff', '0.0125', '0.31', '0.6875', '0.17'])
    if entry_mut:
        mp = os.path.join(td, 'manifests/media.json')
        d = json.load(io.open(mp, encoding='utf-8'))
        entry_mut(d['items'][0])
        txt = json.dumps(d, ensure_ascii=False, indent=1) + '\n'
        io.open(mp, 'w', encoding='utf-8').write(txt)
        io.open(os.path.join(td, 'src/media.json'), 'w', encoding='utf-8').write(txt)
    io.open(os.path.join(td, 'src/scenes.tsx'), 'w', encoding='utf-8').write(
        scene or '<MediaFrame f={f} id="pr" x={200} y={200} w={1060} h={662} focus="diff" />\n')
    return td
td = media_proj()
case('M0 media · 合规素材通过', [('must_pass', 'validate-media', run([PY, VMEDIA, td]))])
cleanup(td)
td = media_proj(lambda e: e.update(file='missing.png'))
case('M1 media · 文件不存在 → 拦', [('must_block:不存在', 'validate-media', run([PY, VMEDIA, td]))])
cleanup(td)
td = media_proj(scene='<MediaFrame f={f} id="pr" x={0} y={0} w={1800} h={1000} focus="diff" focusZoom={2.4} />\n')
case('M2 media · 放大 >1.5 倍会糊 → 拦', [('must_block:会糊', 'validate-media', run([PY, VMEDIA, td]))])
cleanup(td)
td = media_proj(lambda e: e.update(source='web', url='https://example.com/x.png'))
case('M3 media · 网上素材缺 license / credit → 拦', [('must_block:license', 'validate-media', run([PY, VMEDIA, td]))])
cleanup(td)
td = media_proj(lambda e: e.update(source='web', url='https://example.com/x.png', license='CC-BY-NC-4.0', credit='someone'))
case('M4 media · 不兼容许可（NC）→ 拦', [('must_block:不能用于本片', 'validate-media', run([PY, VMEDIA, td]))])
cleanup(td)
td = media_proj(scene='<MediaFrame f={f} id="pr" x={200} y={200} w={1060} h={662} focus="nope" />\n')
case('M5 media · 引用不存在的区域 → 拦', [('must_block:没有区域', 'validate-media', run([PY, VMEDIA, td]))])
cleanup(td)
td = media_proj()
_mv = os.path.join(td, 'public/media/clip.mp4')
run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc=s=320x180:r=25', '-f', 'lavfi', '-i', 'sine', '-t', '1', '-c:v', 'mpeg4', '-c:a', 'aac', _mv])
_md = json.load(io.open(os.path.join(td, 'manifests/media.json'), encoding='utf-8'))
_md['items'].append({'id': 'clip', 'file': 'clip.mp4', 'kind': 'video', 'source': 'user'})
_t = json.dumps(_md, ensure_ascii=False, indent=1) + '\n'
io.open(os.path.join(td, 'manifests/media.json'), 'w', encoding='utf-8').write(_t)
io.open(os.path.join(td, 'src/media.json'), 'w', encoding='utf-8').write(_t)
_bad = run([PY, VMEDIA, td])
_prep = run([PY, PMEDIA, td])
_good = run([PY, VMEDIA, td])
_mj = json.load(io.open(os.path.join(td, 'manifests/media.json'), encoding='utf-8'))
_clip = [x for x in _mj['items'] if x['id'] == 'clip'][0]
case('M6 media · 25fps mpeg4 → 拦；prepare-media 转成 H.264 CFR 30fps 静音 → 通过', [
    ('must_block:H.264', 'validate-media（转码前）', _bad),
    ('must_pass', 'prepare-media', _prep),
    ('must_warn', 'validate-media（转码后）', _good),
    ('must_pass', f'muted={_clip.get("muted", True)} 无 muted:false', (0 if _clip.get('muted', True) is not False else 1, ''))])
cleanup(td)
td = media_proj(lambda e: e.update(source='web', url='https://example.com/x.png', license='CC0', credit='x'),
                scene='<MediaFrame f={f} id="pr" x={200} y={200} w={1060} h={662} />\n<div data-media-credit="pr" />\n')
case('M7 media · 场景里自己画 / 关署名徽章 → 拦', [('must_block:署名', 'validate-media', run([PY, VMEDIA, td]))])
cleanup(td)
td = media_proj(scene='const W = 900;\nconst BIG = W * 2;\n<MediaFrame f={f} id="pr" x={0} y={0} w={BIG} h={W * 1.1} focus="diff" focusZoom={2} />\n')
case('M8 media · 尺寸写成同文件常量表达式，放大 >1.5 → 照样拦', [('must_block:会糊', 'validate-media', run([PY, VMEDIA, td]))])
cleanup(td)
td = media_proj(scene='<MediaFrame f={f} id="pr" x={L.x} y={L.y} w={L.w} h={L.h} focus="diff" focusZoom={2.4} />\n')
case('M9 media · 尺寸来自布局对象量不出 → 按占满画布估，可能糊 → 提醒', [('must_warn:量不出', 'validate-media', run([PY, VMEDIA, td]))])
cleanup(td)

# ── BG · 3.3.0 背景库门禁（validate-backgrounds.py）+ resolve-shots 的背景解析 ──
# 判据逐条：许可白名单、CC BY 必须署名、sha256 绑定、字幕区对比度（按 manifest 指标）、亮底、
# 显式 bg 不存在 / 跨皮肤 → resolve-shots 拦；自动轮换绝不相邻重复；没有背景库的旧工程解析结果逐字节不变。
VBG = os.path.join(SKILL, 'scripts/validate-backgrounds.py')
_LIB = json.load(io.open(os.path.join(TPL, 'manifests/backgrounds.json'), encoding='utf-8'))


def bg_proj(mutate):
    td = tempfile.mkdtemp(prefix='nv-bg-')
    os.makedirs(os.path.join(td, 'manifests'), exist_ok=True)
    e = json.loads(json.dumps(next(x for x in _LIB['backgrounds'] if x['id'] == 'journal/dots')))
    os.makedirs(os.path.join(td, os.path.dirname(e['file'])), exist_ok=True)
    shutil.copy(os.path.join(TPL, e['file']), os.path.join(td, e['file']))
    mutate(e)
    io.open(os.path.join(td, 'manifests/backgrounds.json'), 'w', encoding='utf-8').write(json.dumps(dict(_LIB, backgrounds=[e]), ensure_ascii=False))
    return td


td = bg_proj(lambda e: None)
case('BGL0 背景库 · 原样一张 → 通过', [('must_pass', 'validate-backgrounds', run([PY, VBG, td]))])
cleanup(td)
td = bg_proj(lambda e: e.update(license='CC-BY-NC-4.0'))
case('BGL1 背景库 · NC 许可 → 拦', [('must_block:白名单', 'validate-backgrounds', run([PY, VBG, td]))])
cleanup(td)
td = bg_proj(lambda e: (e.update(license='CC-BY-4.0', attribution=''), e['source'].pop('url', None)))
case('BGL2 背景库 · CC BY 无署名无链接 → 拦', [('must_block:署名', 'validate-backgrounds', run([PY, VBG, td]))])
cleanup(td)
td = bg_proj(lambda e: e['metrics'].update(zone_p05_lum=0.05))
case('BGL3 背景库 · 字幕区有深色装饰（最暗 5 % 过暗）→ 拦', [('must_block:字幕区有深色装饰', 'validate-backgrounds', run([PY, VBG, td]))])
cleanup(td)
td = bg_proj(lambda e: e['metrics'].update(mean_lum=0.3))
case('BGL4 背景库 · 暗底 → 拦', [('must_block:不是亮底', 'validate-backgrounds', run([PY, VBG, td]))])
cleanup(td)
td = bg_proj(lambda e: e.update(sha256='0' * 64))
case('BGL5 背景库 · sha256 对不上 → 拦', [('must_block:sha256', 'validate-backgrounds', run([PY, VBG, td]))])
cleanup(td)


def lib_proj(mutate, theme='flat'):
    def m(doc):
        doc['theme'] = theme
        mutate(doc)
        return doc
    td, rc, out = mkproj(m)
    shutil.copy(os.path.join(TPL, 'manifests/backgrounds.json'), os.path.join(td, 'manifests/backgrounds.json'))
    return td


td = lib_proj(lambda d: d['shots'][0].update(bg='no-such-paper'))
case('BGL6 分镜 · 显式 bg 不在背景库 → resolve-shots 拦并列出可选名', [('must_block:不在背景库', 'resolve-shots', resolve(td))])
cleanup(td)
td = lib_proj(lambda d: d['shots'][0].update(bg='journal/ruled'))
case('BGL7 分镜 · 显式 bg 属于别的皮肤 → 拦', [('must_block:属于 journal 皮肤', 'resolve-shots', resolve(td))])
cleanup(td)
td = lib_proj(lambda d: None)
_r = resolve(td)
_res = json.load(io.open(os.path.join(td, 'manifests/shots.resolved.json'), encoding='utf-8'))
_files = [s.get('bgFile') for s in _res['shots']]
_adj = sum(1 for a, b in zip(_files, _files[1:]) if a == b)
case('BGL8 分镜 · 自动轮换：每镜都有 bgFile、相邻不重复、门禁无 P1', [
    ('must_pass', 'resolve-shots', _r),
    ('must_pass', f'bgFile 全有 {all(_files)} · 相邻重复 {_adj}', (0 if all(_files) and _adj == 0 else 1, '')),
    ('must_pass', 'validate-backgrounds --shots', run([PY, VBG, td, '--shots']))])
cleanup(td)
td = lib_proj(lambda d: (d['shots'][1].update(bg='mesh-mint'), d['shots'][2].update(bg='flat/mesh-mint')))
resolve(td)
case('BGL9 分镜 · 显式写了相邻同一张 → P1 提示（不拦）', [('must_warn:相邻镜重复', 'validate-backgrounds --shots', run([PY, VBG, td, '--shots']))])
cleanup(td)
td, _rc, _out = mkproj()
_before = io.open(os.path.join(td, 'src/shots.ts'), encoding='utf-8').read()
case('BGL10 分镜 · 没有背景库的旧工程 → 不出 bgFile（3.3.0 行为）', [
    ('must_pass', 'resolve-shots', (_rc, _out)),
    ('must_absent:bgFile', 'shots.ts 不含 bgFile', (1, _before))])
cleanup(td)


# ── SFX1：非法的 sfxDensity 必须被 resolve-shots 拦下（3.3.0）──
_td, _rc, _out = mkproj(lambda d: (d.__setitem__('sfxDensity', 'loud'), d)[1])
case('SFX1 分镜 · 非法 sfxDensity → resolve-shots 拦', [
    ('must_block:sfxDensity', 'resolve-shots', (_rc, _out))])
cleanup(_td)


# ── SFX2：缺省不写 sfxDensity 时按 sparse 生成（3.3.0 行为变更）──
_td, _rc, _out = mkproj()
case('SFX2 分镜 · 缺省 sfxDensity = sparse（值由 tests/test_sfx_density.py 核对）', [
    ('must_pass', 'resolve-shots', (_rc, _out))])
cleanup(_td)


# ---- 3.3.0 评审拦截：手作皮肤 review.rounds 为空时 make-video --render 必须停（不加 --skip-review） ----
def mk_review_proj(skin, rounds):
    td = tempfile.mkdtemp(prefix='nv-review-')
    os.makedirs(os.path.join(td, 'manifests'))
    os.makedirs(os.path.join(td, 'src', 'theme'))
    os.makedirs(os.path.join(td, 'audio'))
    shutil.copy(os.path.join(TPL, 'manifests/caption-cues.json'), os.path.join(td, 'manifests/caption-cues.json'))
    shutil.copy(SRC, os.path.join(td, 'manifests/shots.json'))
    io.open(os.path.join(td, 'src/index.tsx'), 'w', encoding='utf-8').write('// fixture\n')
    io.open(os.path.join(td, 'src/theme/active.ts'), 'w', encoding='utf-8').write(f"export {{theme}} from './{skin}';\n")
    # treatment 故意不完整：放行后会被 validate-treatment 拦在 tsc / npm ci 之前（夹具永远不会真的去渲染）
    io.open(os.path.join(td, 'manifests/treatment.json'), 'w', encoding='utf-8').write(json.dumps({'review': {'rounds': rounds}}))
    return td

MV = os.path.join(SKILL, 'scripts/make-video.mjs')
td = mk_review_proj('journal', [])
case('RV1 手作皮肤 · review.rounds 为空 · --render 不加 --skip-review → 渲染前停下', [
    ('must_block:review.rounds', 'make-video --render', run(['node', MV, td, '--render', os.path.join(td, 'renders', 'x.mp4')]))])
case('RV2 同一工程加 --skip-review → 不再被评审拦（继续走到构建期门禁）', [
    ('must_absent:review.rounds 还是空的', 'make-video --render --skip-review', run(['node', MV, td, '--render', os.path.join(td, 'renders', 'x.mp4'), '--skip-review'])),
    ('must_block:构建期门禁', '走到了门禁那一步', run(['node', MV, td, '--render', os.path.join(td, 'renders', 'x.mp4'), '--skip-review']))])
cleanup(td)
td = mk_review_proj('flat', [])
case('RV3 flat 皮肤 · review.rounds 为空 → 不拦（只拦手作皮肤）', [
    ('must_absent:review.rounds 还是空的', 'make-video --render（flat）', run(['node', MV, td, '--render', os.path.join(td, 'renders', 'x.mp4')]))])
cleanup(td)
