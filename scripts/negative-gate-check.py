#!/usr/bin/env python3
"""负向抽查：给三道构建期门禁喂"该 FAIL 的夹具"，验证它们真的会拦（不渲染任何东西）。
门在名义上存在、实际静默放行 = 最危险的病。

每步各自声明期望：('must_block' | 'must_pass', label, (rc, out))。"""
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
        good = (rc != 0) if kind == 'must_block' else (rc == 0)
        ok = ok and good
        lines = [l.strip() for l in out.split('\n') if l.strip()][:2]
        detail.append(f"    {'PASS' if good else 'FAIL'}  [{kind}] {label}: rc={rc} · {' / '.join(lines)[:230]}")
    results.append((name, ok, detail))
    print(('PASS  ' if ok else 'FAIL  ') + name)

# ── A：anchor 出界 → validate-shot-motion 必须拦 ──
td, rc0, out0 = mkproj(lambda d: (d['shots'][0].__setitem__('anchor', {'x': 1900, 'y': 1500, 'w': 1200, 'h': 600}), d)[1])
case('A 镜头 anchor 出界', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block', 'validate-shot-motion', run([PY, os.path.join(SKILL, 'scripts/validate-shot-motion.py'), td])),
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
    ('must_block', 'validate-shot-motion', run([PY, os.path.join(SKILL, 'scripts/validate-shot-motion.py'), td])),
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
    ('must_block', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
])
cleanup(td)

# ── D：时间轴断档（跳过两句话）→ resolve-shots 自身必须拦 ──
td, rc0, out0 = mkproj(lambda d: (d['shots'][1].__setitem__('cues', [6, 6]), d)[1])
case('D 时间轴断档', [('must_block', 'resolve-shots', (rc0, out0))])
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
    ('must_block', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
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
    ('must_block', 'validate-shot-motion', run([PY, os.path.join(SKILL, 'scripts/validate-shot-motion.py'), td])),
])
cleanup(td)

# ── H：帧参数写错（fxkit 组件传 f={f}）→ validate-frame-props 必须拦（v2.11 新增）──
td, rc0, out0 = mkproj()
# 必须把真实引擎文件放进 src/，否则门禁无从比对组件签名
shutil.copy(os.path.join(TPL, 'src/fxkit.tsx'), os.path.join(td, 'src/fxkit.tsx'))
io.open(os.path.join(td, 'src/scenes.tsx'), 'w', encoding='utf-8', newline='').write(
    "import {Typewriter} from './fxkit';" + NL
    + "export const S=({f}:{f:number}) => <Typewriter f={f} text='x'/>;" + NL)
case('H 帧参数写错（fxkit 传 f）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block', 'validate-frame-props', run([PY, os.path.join(SKILL, 'scripts/validate-frame-props.py'), td])),
])
cleanup(td)

# ── E：阴性对照：原样分镜表三道门必须全过（证明门不是"见谁拦谁"） ──
td, rc0, out0 = mkproj()
case('E 阴性对照（原样应全过）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_pass', 'validate-shot-motion', run([PY, os.path.join(SKILL, 'scripts/validate-shot-motion.py'), td])),
    ('must_pass', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
])
cleanup(td)

print()
print('== 负向抽查明细 ==')
for name, ok, detail in results:
    print(('PASS  ' if ok else 'FAIL  ') + name)
    for d in detail:
        print(d)
sys.exit(0 if all(r[1] for r in results) else 1)
