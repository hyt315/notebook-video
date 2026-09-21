#!/usr/bin/env python3
"""负向抽查：给**每道构建期门禁**喂"该 FAIL 的夹具"，验证它们真的会拦（不渲染任何东西）。
门在名义上存在、实际静默放行 = 最危险的病。

每步各自声明期望：`(kind, label, (rc, out))`，kind 四种：
  · `must_block:<子串>`  rc != 0 **且**输出含该子串（不带子串则只要求 rc != 0）
  · `must_absent:<子串>` rc != 0 **且**输出**不含**该子串——用来钉"不该报的那一侧"
                         （例如注释/字符串里的反例不许被当成违规报出来）
  · `must_warn:<子串>`   rc == 0 **且**含该子串——P1 级判据"放行但要点名"的夹具
  · `must_pass`          rc == 0（阴性对照：合法输入必须全过）

为什么子串断言是必须的：只看 rc 会把"因为别的原因失败"记成通过（第一版 P 用例就是这样假通过的）。"""
import io, json, os, shutil, subprocess, sys, tempfile

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(SKILL, 'assets/lecture-template')
PY = sys.executable
SRC = os.path.join(TPL, 'manifests/shots.json')
results = []

def cleanup(td):
    """删除临时夹具目录；失败要打 WARN 而不是静默忽略（隐藏的跳过 = 脏环境累积）。"""
    try:
        shutil.rmtree(td)
    except OSError as e:
        print(f"WARN 临时目录未能清理：{td}（{e.__class__.__name__}）——请手动删除")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    return r.returncode, (r.stdout or '') + (r.stderr or '')

def mkproj(mutate=None):
    td = tempfile.mkdtemp(prefix='nv-gate-')
    os.makedirs(os.path.join(td, 'manifests'), exist_ok=True)
    os.makedirs(os.path.join(td, 'src'), exist_ok=True)
    shutil.copy(os.path.join(TPL, 'manifests/caption-cues.json'), os.path.join(td, 'manifests/caption-cues.json'))
    doc = json.loads(io.open(SRC, encoding='utf-8').read())
    if mutate:
        doc = mutate(doc)
    io.open(os.path.join(td, 'manifests/shots.json'), 'w', encoding='utf-8', newline='').write(
        json.dumps(doc, ensure_ascii=False, indent=2))
    rc, out = run([PY, os.path.join(SKILL, 'scripts/resolve-shots.py'), td])
    return td, rc, out

def resolve(td):
    return run([PY, os.path.join(SKILL, 'scripts/resolve-shots.py'), td])

def case(name, steps):
    ok = True
    detail = []
    for kind, label, (rc, out) in steps:
        # `must_block:<子串>` = 必须失败**且**输出里出现该子串 —— 否则"因为别的原因失败"
        # 会被当成本夹具通过（第一版 P 用例就是这样假通过的：拷贝时跳过了 assets/demo 的大文件，
        # 于是它因为"链接断了"而失败，根本没测到"文档写了不存在的组件名"）。
        # `must_absent:<子串>` = 必须失败**且**输出里**没有**该子串，用来钉"不许误报"的那一侧。
        kind_base, _sep, arg = kind.partition(':')
        good = (rc == 0) if kind_base in ('must_pass', 'must_warn') else (rc != 0)
        if arg:
            good = good and (arg not in out if kind_base == 'must_absent' else arg in out)
        ok = ok and good
        lines = [l.strip() for l in out.split('\n') if l.strip()][:2]
        detail.append(f"    {'PASS' if good else 'FAIL'}  [{kind}] {label}: rc={rc} · {' / '.join(lines)[:230]}")
    results.append((name, ok, detail))
    print(('PASS  ' if ok else 'FAIL  ') + name)

# ── A：anchor 出界 → validate-shot-motion 必须拦 ──
td, rc0, out0 = mkproj(lambda d: (d['shots'][0].__setitem__('anchor', {'x': 1900, 'y': 1500, 'w': 1200, 'h': 600}), d)[1])
case('A 镜头 anchor 出界', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:anchor 出界', 'validate-shot-motion', run([PY, os.path.join(SKILL, 'scripts/validate-shot-motion.py'), td])),
])
cleanup(td)

# ── B：平移超出缩放预算（s=1.0 却平移 ±220px）→ validate-shot-motion 必须拦 ──
def mut_pan(d):
    d['shots'][3]['camera'] = {'intent': 'pan-follow', 'at': 10, 'dur': 45, 'fromX': 700, 'fromY': 540,
                               'x': 1220, 'y': 540, 'from': 1.0, 'to': 1.0}
    return d
td, rc0, out0 = mkproj(mut_pan)
case('B 平移超预算（s=1.0 平移 ±220px）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:超出缩放', 'validate-shot-motion', run([PY, os.path.join(SKILL, 'scripts/validate-shot-motion.py'), td])),
])
cleanup(td)

# ── C：相邻同骨架 + 抽掉活性组件 → validate-composition 必须拦 ──
def mut_skel(d):
    d['shots'][1]['skeleton'] = d['shots'][0]['skeleton']
    d['shots'][1]['live'] = []
    return d
td, rc0, out0 = mkproj(mut_skel)
case('C 相邻同骨架 + 无活性组件', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:同骨架', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
])
cleanup(td)

# ── D：时间轴断档（跳过两句话）→ resolve-shots 自身必须拦 ──
td, rc0, out0 = mkproj(lambda d: (d['shots'][1].__setitem__('cues', [6, 6]), d)[1])
case('D 时间轴断档', [('must_block:非正', 'resolve-shots', (rc0, out0))])
cleanup(td)

NL = chr(10)

# ── F：假 live / 假 media 名 → validate-composition 必须拦（v2.11 新增）──
# 旧版只查"live 非空、media 去重 ≥3"，编造的名字照样过；现在 live 必须在场景文件里真实出现。
def mut_fake(d):
    d['shots'][0]['live'] = ['NO_SUCH_COMPONENT_9876']
    d['shots'][1]['media'] = ['FAKE_MEDIUM_A', 'FAKE_MEDIUM_B', 'FAKE_MEDIUM_C']
    return d
td, rc0, out0 = mkproj(mut_fake)
# 需要一个带真实组件名的场景文件，否则"可解析"这一条无从判定
io.open(os.path.join(td, 'src/scenes.tsx'), 'w', encoding='utf-8', newline='').write(
    "import {ConsoleWindow} from './media';" + NL + "export const S=()=> <ConsoleWindow/>;" + NL)
case('F 造假 live / media 名', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:未知介质', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
])
cleanup(td)

# ── G：冻结的假运镜（声明 intent 但关键帧不动）→ validate-shot-motion 必须拦（v2.11 新增）──
td, rc0, out0 = mkproj(lambda d: (d['shots'][1].__setitem__('cameraIntent', 'pan-follow'), d)[1])
if rc0 == 0:
    import json as _json
    rp = os.path.join(td, 'manifests/shots.resolved.json')
    rr = _json.loads(io.open(rp, encoding='utf-8').read())
    for s in rr['shots']:
        if s['id'] == 'S2':
            for k in s['keys']:
                k['s'] = 1.0; k['x'] = 960.0; k['y'] = 540.0
    io.open(rp, 'w', encoding='utf-8', newline='').write(_json.dumps(rr, ensure_ascii=False))
case('G 冻结的假运镜', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:几乎不动', 'validate-shot-motion', run([PY, os.path.join(SKILL, 'scripts/validate-shot-motion.py'), td])),
])
cleanup(td)

# ── H：帧参数写错（fxkit 组件传 f={f}）→ validate-frame-props 必须拦（v2.11 新增）──
td, rc0, out0 = mkproj()
# 必须把**整棵 src** 拷进去：只拷 fxkit.tsx 时门禁只解析到 11 个组件，
# 会先撞"引擎源码没读到"的防呆分支（rc=2）—— 复核实测这条 case 一直是这样**假通过**的，
# 它声称测的"帧参数写错"根本没走到。拷全之后才会走真正的判据。
for base, _dirs, files in os.walk(os.path.join(TPL, 'src')):
    for name in files:
        if not name.endswith(('.tsx', '.ts')):
            continue
        src_path = os.path.join(base, name)
        rel = os.path.relpath(src_path, os.path.join(TPL, 'src'))
        dst = os.path.join(td, 'src', rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src_path, dst)
io.open(os.path.join(td, 'src/scenes.tsx'), 'w', encoding='utf-8', newline='').write(
    "import {Typewriter} from './fxkit';" + NL
    + "export const S=({f}:{f:number}) => <Typewriter f={f} text='x'/>;" + NL)
case('H 帧参数写错（fxkit 传 f）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:只认 frame', 'validate-frame-props', run([PY, os.path.join(SKILL, 'scripts/validate-frame-props.py'), td])),
])
cleanup(td)

# ── I · 呈现效果门禁 G-1：beat 提前剧透（offset 远早于它那句）→ validate-presentation 必须拦 ──
# 这里刻意让 resolve-shots 仍然通过（它只算帧号，不管"讲与画对不对得上"），
# 证明新门禁不是"看着 resolve-shots 过了就放行"。
def mut_spoiler(d):
    # 用 S1 的 cue1（它的帧号在 S1 区间内）而不是 S2 的 cue4 —— 后者帧号恰好 = S2 镜起点，
    # 任何负 offset 都会先撞判据①"落在镜外"，于是这条夹具**永远测不到③**（复核实测）。
    d['shots'][0]['beats'] = [{'cue': 0, 'offset': 0}, {'cue': 1, 'offset': -13}, {'cue': 2, 'offset': 0}, {'cue': 3, 'offset': 0}]
    return d
td, rc0, out0 = mkproj(mut_spoiler)
case('I 呈现效果 · beat 提前剧透 13 帧', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:早于该句', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# ── J · 呈现效果门禁 G-1②：beat 声明了不属于本镜的 cue → 必须拦 ──
td, rc0, out0 = mkproj(lambda d: (d['shots'][1].__setitem__('beats', [{'cue': 13, 'offset': 0}]), d)[1])
case('J 呈现效果 · beat 引用了别的镜的 cue', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:超出本镜', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# ── S · 呈现效果门禁 G-1③b：beat **晚于**它那句讲完太久 → 必须拦（上界的方向）──
# 复核抓到的口径漏洞：第一版只防"早"，`{cue:0, offset:200}`（台词讲完 6.7s 才出现）照样 PASS。
# 这条夹具把 S1 的第一拍推到 offset=200（该句 31 帧、容差 8 帧 → 上界 39）。
td, rc0, out0 = mkproj(lambda d: (d['shots'][0]['beats'].__setitem__(0, {'cue': 0, 'offset': 200}), d)[1])
case('S 呈现效果 · beat 晚于该句结束 169 帧', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:晚于该句结束', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# ── R · 呈现效果门禁 G-1③b-P1：合法但**贴边**的拍要被点名（rc 仍为 0，不许当成拦）──
# 复核实测：模板最紧的合法拍余量恰好 8 帧（offset = 该句帧数 = "句末那拍"），容差是承重墙。
# 夹具把 S7 的 cue13 第二拍从 offset=100 推到 112（该句 106 帧 → 余量只剩 2 帧，仍在 8 帧容差内）：
# 判据必须**放行**（rc=0）同时**点名**它 —— 让"脆"在变成 P0 之前就被看见。
def mut_tight(d):
    beats = d['shots'][6]['beats']
    for b in beats:
        if b['cue'] == 13 and b['offset'] == 100:
            b['offset'] = 112
    return d
td, rc0, out0 = mkproj(mut_tight)
case('R 呈现效果 · 距容差上界只剩 2 帧（贴边预警）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_warn:贴边', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# ── K · 呈现效果门禁 G-2：字幕阅读速度超预算（40 字塞进 1 秒）→ 必须拦 ──
def mut_dense(td_):
    p = os.path.join(td_, 'manifests/caption-cues.json')
    doc = json.loads(io.open(p, encoding='utf-8').read())
    c = doc['cues'][0]
    c['text'] = '这是一条故意写得很长的字幕用来把阅读速度顶到上限之上让门禁必须拦住它才行'
    c['speech_end_ms'] = c['start_ms'] + 900
    io.open(p, 'w', encoding='utf-8', newline='').write(json.dumps(doc, ensure_ascii=False, indent=2))
td, rc0, out0 = mkproj()
mut_dense(td)
case('K 呈现效果 · 字幕 40 字压进 0.9 秒', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:阅读速度', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# ── L · 呈现效果门禁 G-3：字号低于绝对地板 13 → 必须拦 ──
td, rc0, out0 = mkproj()
io.open(os.path.join(td, 'src/tooSmall.tsx'), 'w', encoding='utf-8', newline='').write(
    "export const S=()=> <div style={{fontSize: 9}}>太小的字</div>;" + NL)
case('L 呈现效果 · 字号 9px 低于地板', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:低于绝对地板', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# ── M · 呈现效果门禁 G-3：主题正文色对比度不足 → 必须拦 ──
td, rc0, out0 = mkproj()
os.makedirs(os.path.join(td, 'src/theme'), exist_ok=True)
io.open(os.path.join(td, 'src/theme/paper.tsx'), 'w', encoding='utf-8', newline='').write(
    "const palette = {" + NL
    + "  ink: '#f2f2f2'," + NL          # 近乎白 → 压在白底上读不出来
    + "  muted: '#eeeeee'," + NL
    + "  white: '#ffffff'," + NL
    + "  paper: '#ffffff'," + NL
    + "  paperWarm: '#faf5ee'," + NL
    + "  paperBase: '#faf7f2'," + NL
    + "};" + NL)
case('M 呈现效果 · 正文色几乎等于底色', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:正文色', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# ── N · 帧参数名门禁必须覆盖 **src/components/ 那一层**（v3.1 的 29 件）──
# 旧版 `collect_components` 只 os.listdir(src) 一层、且名单里有 4 个不存在的文件名，
# 于是给 `Chart` 写成 `frame={f}` 完全不会被抓（静默回落到全局帧）。
# 夹具刻意把组件放在 **src/components/** 里使用，只有"递归扫描"才能判出来。
def mk_fixture_scene(td_, attr):
    io.open(os.path.join(td_, 'src/scenes-p.tsx'), 'w', encoding='utf-8', newline='').write(
        "import {Chart} from './components/chart';" + NL
        + "export const S=({f}:{f:number}) => <Chart " + attr + " width={400} height={300} startAt={0} data={[]} />;" + NL)

td, rc0, out0 = mkproj()
os.makedirs(os.path.join(td, 'src/components'), exist_ok=True)
# 整层拷进去：只拷一个文件会让门禁的"引擎源码没读到"防呆（<20 个组件）先触发，
# 那样测到的是防呆、不是本夹具要测的"递归覆盖 components/ 层"。
for f in os.listdir(os.path.join(TPL, 'src/components')):
    shutil.copy(os.path.join(TPL, 'src/components', f), os.path.join(td, 'src/components', f))
mk_fixture_scene(td, 'frame={f}')     # 错：Chart 只认 f
case('N 帧参数名 · components 层写成 frame={f}', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:只认 f', 'validate-frame-props', run([PY, os.path.join(SKILL, 'scripts/validate-frame-props.py'), td])),
])
cleanup(td)

# ── O · 同一夹具写对（f={f}）→ 必须放行（证明 N 不是"见到就拦"）──
td, rc0, out0 = mkproj()
os.makedirs(os.path.join(td, 'src/components'), exist_ok=True)
# 整层拷进去：只拷一个文件会让门禁的"引擎源码没读到"防呆（<20 个组件）先触发，
# 那样测到的是防呆、不是本夹具要测的"递归覆盖 components/ 层"。
for f in os.listdir(os.path.join(TPL, 'src/components')):
    shutil.copy(os.path.join(TPL, 'src/components', f), os.path.join(td, 'src/components', f))
mk_fixture_scene(td, 'f={f}')          # 对
case('O 帧参数名 · 同一夹具写对（阴性对照）', [
    ('must_pass', 'validate-frame-props', run([PY, os.path.join(SKILL, 'scripts/validate-frame-props.py'), td])),
])
cleanup(td)

# ── P · 一致性检查必须拦住"文档写了不存在的组件名"（审计 A1/A6/A7/A8 那一整类）──
# 夹具：把整份技能拷一份（跳过 assets/demo 的大文件），在 SKILL.md 里塞一个不存在的组件名，
# 然后让 validate-skill-consistency.py --root 指向这份副本 —— 它必须报出来。
def mk_skill_copy():
    td = tempfile.mkdtemp(prefix='nv-skill-')
    ignore = shutil.ignore_patterns('node_modules', 'renders', '.git', '.cache', '.tools', '__pycache__',
                                   '*.mp4', '*.webp', '*.png', '*.jpg')
    shutil.copytree(SKILL, td, dirs_exist_ok=True, ignore=ignore)
    # 大文件跳过拷贝，但**补占位空文件**：否则链接检查会先报"broken link"，
    # 夹具就变成"因为别的原因失败"了（第一版的假通过）。
    for rel in ('assets/demo/notebook-video-demo.mp4', 'assets/demo/notebook-video-demo.webp',
                'assets/demo/notebook-video-components-demo.mp4', 'assets/demo/hero.png',
                'assets/demo/social-preview.png'):
        q = os.path.join(td, rel)
        if not os.path.exists(q):
            os.makedirs(os.path.dirname(q), exist_ok=True)
            open(q, 'wb').close()
    return td


td_skill = mk_skill_copy()
with io.open(os.path.join(td_skill, 'SKILL.md'), 'a', encoding='utf-8', newline='') as fh:
    fh.write(NL + '**`NoSuchComponent`** 是故意写坏的名字。' + NL)
case('P 一致性 · 文档写了不存在的组件名', [
    ('must_block:NoSuchComponent', 'validate-skill-consistency', run([PY, os.path.join(SKILL, 'scripts/validate-skill-consistency.py'), '--root', td_skill])),
])
cleanup(td_skill)

# ── E：阴性对照：原样分镜表三道门必须全过（证明门不是"见谁拦谁"） ──
td, rc0, out0 = mkproj()
case('E 阴性对照（原样应全过）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_pass', 'validate-shot-motion', run([PY, os.path.join(SKILL, 'scripts/validate-shot-motion.py'), td])),
    ('must_pass', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
    ('must_pass', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# ── Q · import_integrity 必须覆盖「桶文件」与「组件层内部」（第二轮复核实测：此前两层都不查）──
# 夹具三种形态，每种都能单独定位（needle = 那个编出来的名字）：
#   (a) 顶层文件从桶文件 './components' 导入不存在的名字；
#   (b) 组件层内部文件从兄弟模块 './ui' 导入不存在的名字；
#   (c) 桶文件把坏名字再导出一次 —— **坏再导出不许把坏名字洗白**（本次修的洞）。
td, rc0, out0 = mkproj()
for base, _dirs, files in os.walk(os.path.join(TPL, 'src')):
    for name in files:
        if not name.endswith(('.tsx', '.ts')):
            continue
        src_path = os.path.join(base, name)
        rel = os.path.relpath(src_path, os.path.join(TPL, 'src'))
        dst = os.path.join(td, 'src', rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src_path, dst)
with io.open(os.path.join(td, 'src/scenes.tsx'), 'a', encoding='utf-8', newline='') as fh:
    fh.write("import {GhostFromBarrel} from './components';" + NL)
    fh.write("import {GhostWashedByBarrel} from './components';" + NL)
with io.open(os.path.join(td, 'src/components/network.tsx'), 'a', encoding='utf-8', newline='') as fh:
    fh.write("import {GhostSibling} from './ui';" + NL)
with io.open(os.path.join(td, 'src/components/index.ts'), 'a', encoding='utf-8', newline='') as fh:
    fh.write("export {GhostWashedByBarrel} from './ui';" + NL)
case('Q import_integrity · 桶文件 + 组件层内部 + 坏再导出', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:GhostFromBarrel', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
    ('must_block:GhostSibling', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
    ('must_block:GhostWashedByBarrel', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
])
cleanup(td)

# ── T · 字号扫描只认"值位置"：注释 / 字符串 / JSX 撇号都不许误报，真违规仍必须报 ──
# 第三轮复核指出：我声称的"四条夹具"是当场跑的、**没固化**（脚本里只有 L 一条），回归护栏是空的。
# 这个夹具把四条行为钉死在同一份文件上——行号写死，故意让 needle 唯一：
#   第 1 行 模板字符串里的代码样例（`fontSize: 8` 那种，本仓库确实这么写文档）
#   第 2 行 块注释里的反例 · 第 3 行 整行注释 · 第 4 行 JSX 撇号 don't 后面的行尾注释
#   第 5 行 真违规 → 必须报"第 5 行"
td, rc0, out0 = mkproj()
with io.open(os.path.join(td, 'src/audit-fonts.tsx'), 'w', encoding='utf-8', newline='') as fh:
    fh.write(NL.join([
        "const SAMPLE = `import {GhostInSnippet} from './toolkit';`;",
        "/* 注释里的反例：fontSize: 8 是禁止写法 */",
        "// 整行注释 fontSize: 8 也不许报",
        "export const A = () => <div>don't</div>; // fontSize: 8",
        "export const B = () => <div style={{fontSize: 9}}/>;",
    ]) + NL)
case('T 字号扫描只认代码（注释/字符串/撇号不误报，真违规仍拦）', [
    ('must_block:audit-fonts.tsx:5 fontSize:9', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
    ('must_absent:audit-fonts.tsx:1 fontSize', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
    ('must_absent:audit-fonts.tsx:2 fontSize', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
    ('must_absent:audit-fonts.tsx:4 fontSize', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# ── U · 合法的"别名再导出"必须放行（第三轮复核抓到的潜在假阳性，第一版真报 P0）──
# 三种形态一次覆盖：`export {A as B}`、`export *` 链上的别名、`export {default as X}`。
# 第一版拿**别名**去上游找导出（上游有的是**源名**）→ 合法写法被判"导出不存在"。
td, rc0, out0 = mkproj()
for base, _dirs, files in os.walk(os.path.join(TPL, 'src')):
    for name in files:
        if not name.endswith(('.tsx', '.ts')):
            continue
        src_path = os.path.join(base, name)
        rel = os.path.relpath(src_path, os.path.join(TPL, 'src'))
        dst = os.path.join(td, 'src', rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src_path, dst)
with io.open(os.path.join(td, 'src/components/chain.ts'), 'w', encoding='utf-8', newline='') as fh:
    fh.write("export {Accordion as ChainedAccordion} from './ui';" + NL)
with io.open(os.path.join(td, 'src/components/raw.tsx'), 'w', encoding='utf-8', newline='') as fh:
    fh.write("const Raw:React.FC<{f:number}>=()=>null;" + NL + "export default Raw;" + NL)
with io.open(os.path.join(td, 'src/components/index.ts'), 'a', encoding='utf-8', newline='') as fh:
    fh.write("export {Accordion as MyAccordion} from './ui';" + NL)
    fh.write("export * from './chain';" + NL)
    fh.write("export {default as Widget} from './raw';" + NL)
with io.open(os.path.join(td, 'src/scenes.tsx'), 'a', encoding='utf-8', newline='') as fh:
    fh.write("import {MyAccordion, ChainedAccordion, Widget} from './components';" + NL)
case('U import_integrity · 别名再导出（合法）必须放行', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_pass', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
])
cleanup(td)

# ── V · 别名再导出的**反向**：源名在上游根本不存在 → 仍然必须拦（别名放行不等于放走坏名字）──
td, rc0, out0 = mkproj()
for base, _dirs, files in os.walk(os.path.join(TPL, 'src')):
    for name in files:
        if not name.endswith(('.tsx', '.ts')):
            continue
        src_path = os.path.join(base, name)
        rel = os.path.relpath(src_path, os.path.join(TPL, 'src'))
        dst = os.path.join(td, 'src', rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src_path, dst)
with io.open(os.path.join(td, 'src/components/index.ts'), 'a', encoding='utf-8', newline='') as fh:
    fh.write("export {NoSuchUpstream as GhostAlias} from './ui';" + NL)
with io.open(os.path.join(td, 'src/scenes.tsx'), 'a', encoding='utf-8', newline='') as fh:
    fh.write("import {GhostAlias} from './components';" + NL)
case('V import_integrity · 坏别名再导出不许洗白', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:GhostAlias', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
])
cleanup(td)

# ── W · 字符串里的代码样例不许被当成真 import（第三轮复核的例子；本仓库确实这么放文档样例）──
td, rc0, out0 = mkproj()
for base, _dirs, files in os.walk(os.path.join(TPL, 'src')):
    for name in files:
        if not name.endswith(('.tsx', '.ts')):
            continue
        src_path = os.path.join(base, name)
        rel = os.path.relpath(src_path, os.path.join(TPL, 'src'))
        dst = os.path.join(td, 'src', rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src_path, dst)
with io.open(os.path.join(td, 'src/scenes.tsx'), 'a', encoding='utf-8', newline='') as fh:
    fh.write("export const CODE = `import {GhostInSnippet} from './toolkit';`;" + NL)
case('W import_integrity · 模板字符串里的 import 样例不算真 import', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_pass', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
])
cleanup(td)

# ════════════════════════════════════════════════════════════════════════════
# 2026-09-21 补的三条：本轮新增的判据此前**不在负向库里**。
# 这个库存在的意义就是"每道门禁都有'喂坏输入必须拦住'的实证"——判据加了而夹具没加，
# 等于这道门仍然只是名义存在。三条都在下面：X（讲法字段 G-14）/ Y（*Ink 文字安全色）/
# Z1–Z3（beats 下标越界，含"全路径写法"这个原来漏掉的盲区与一条阴性对照）。
# ════════════════════════════════════════════════════════════════════════════

def mksrc(replace_scene=None):
    """带上模板 src 的夹具项目（有些门禁必须读场景源码），可选对 scenes.tsx 做一次替换。"""
    td, rc0, out0 = mkproj()
    for base, _dirs, files in os.walk(os.path.join(TPL, 'src')):
        for name in files:
            if not name.endswith(('.tsx', '.ts')):
                continue
            src_path = os.path.join(base, name)
            dst = os.path.join(td, 'src', os.path.relpath(src_path, os.path.join(TPL, 'src')))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src_path, dst)
    if replace_scene is not None:
        p = os.path.join(td, 'src/scenes.tsx')
        text = io.open(p, encoding='utf-8').read()
        new = replace_scene(text)
        assert new != text, '夹具没有真正改到 scenes.tsx（锚点变了？）'
        io.open(p, 'w', encoding='utf-8', newline='').write(new)
    return td, rc0, out0


# ── X · 讲法字段必填（G-14/G-15/G-16）：删掉一镜的 move → validate-presentation 必须拦 ──
# 为什么值得单独一条：这四个字段**曾经在 resolve 那一步被整组丢掉**，
# 于是"规范要求必填"下游根本看不见（实测删掉 move，全部门禁照旧 PASS）。
def mut_move(d):
    d['shots'][2].pop('move', None)
    return d
td, rc0, out0 = mkproj(mut_move)
case('X 讲法字段 · 缺 move（G-14）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:缺 move', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# ── Y · 文字安全色（*Ink）：把 blueInk 改成近乎白色 → validate-presentation 必须拦（P0）──
# 这一条同时是"新增机制的自检"：五个 *Ink 是专门用来当文字色的，
# 它们不过 4.5:1，"把强调色压暗到能当文字"这个约定就是空话。
td, rc0, out0 = mkproj()
os.makedirs(os.path.join(td, 'src/theme'), exist_ok=True)
for name in ('types.ts', 'canvas.ts', 'active.ts', 'paper.tsx', 'cel.tsx', 'sticker.tsx', 'flat.tsx'):
    src_p = os.path.join(TPL, 'src/theme', name)
    if os.path.exists(src_p):
        shutil.copy(src_p, os.path.join(td, 'src/theme', name))
ink_path = os.path.join(td, 'src/theme/paper.tsx')
ink_text = io.open(ink_path, encoding='utf-8').read().replace("blueInk: '#2563eb'", "blueInk: '#eeeeee'")
assert "blueInk: '#eeeeee'" in ink_text, '夹具没改到 paper 的 blueInk（值变了？）'
io.open(ink_path, 'w', encoding='utf-8', newline='').write(ink_text)
case('Y 文字安全色 · *Ink 压不过 4.5:1', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:文字安全色', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# ── Z · beats 下标越界（validate-composition）：两种写法 + 一条阴性对照 ──
# 由来：场景写 `b[3]` 而镜里只有 3 拍时，要么整帧渲染抛错、要么那件东西永远不出现（都实测过）。
# ⚠️ 原来只扫本地别名 `b[k]`，写成全路径 `SHOTS.Sx.beats[k]` 就整条漏掉 —— Z3 钉住这一侧。
S1_ANCHOR = "const b = SHOTS.S1.beats;"
S2_ANCHOR = "const b = SHOTS.S2.beats;"

td, rc0, out0 = mksrc(lambda t: t.replace(
    S1_ANCHOR, S1_ANCHOR + NL + "  const okIdx = b[1];", 1).replace(
    S2_ANCHOR, S2_ANCHOR + NL + "  const okFull = SHOTS.S2.beats[1];", 1))
case('Z1 拍数越界 · 合法下标必须放行（阴性对照）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_pass', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
])
cleanup(td)

td, rc0, out0 = mksrc(lambda t: t.replace(S1_ANCHOR, S1_ANCHOR + NL + "  const badIdx = b[9];", 1))
case('Z2 拍数越界 · 本地别名 b[9]', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:场景里用了 b[9]', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
])
cleanup(td)

td, rc0, out0 = mksrc(lambda t: t.replace(S2_ANCHOR, S2_ANCHOR + NL + "  const badFull = SHOTS.S2.beats[9];", 1))
case('Z3 拍数越界 · 全路径 SHOTS.S2.beats[9]（原来漏掉的写法）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:SHOTS.S2.beats[9]', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
])
cleanup(td)

print()
print('== 负向抽查明细 ==')
for name, ok, detail in results:
    print(('PASS  ' if ok else 'FAIL  ') + name)
    for d in detail:
        print(d)
sys.exit(0 if all(r[1] for r in results) else 1)
