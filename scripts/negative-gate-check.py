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


# ════════════════════════════════════════════════════════════════════════════
# 渲染期门禁的**接线与硬拦纪律**静态检查（画布越界门禁 CanvasBoundsGate）
#
# 为什么需要它：这道门禁跑在浏览器里，本脚本（纯标准库、不渲染）没法喂它一帧坏画面 ——
# 但"装没装、关键判据还在不在"是纯静态可查的，而这一层恰好是最容易在重构里被削掉的：
#   · 没挂上 → 门禁不存在（接触表 composition 此前**一道门禁都没有**，第 ⑥ 页的越界就是这么漏的）；
#   · 删掉 `if (blocked) throw e;` → 报"硬拦"却照样出图 rc=0（本仓库踩过两次的坑）；
#   · 删掉 `[data-design-root]` 折算 → 口径从设计坐标退回输出像素，换 --scale 就失真。
# 所以这三条各自一条夹具：原样必须过，删掉任一条必须被抓住。
# （真渲染的负向/正向夹具在演示工程之外：见 references/composition-gate.md §5.2 的七条 composition。）
# ════════════════════════════════════════════════════════════════════════════
CANVAS_BOUNDS_NEEDLES = (
    # (检查项, 子串, 说人话)
    ('硬拦纪律', 'let blocked = false;', '缺少 blocked 标志位：判定作出后 handle 还能被释放'),
    ('硬拦纪律', 'if (released || blocked) return;', '缺少"blocked 后 handle 不释放"的处置'),
    ('硬拦纪律', 'if (blocked) throw e;', 'cancelRender 的异常会被自家 catch 吞掉（报了硬拦却出图 rc=0 的老坑）'),
    ('逐帧持柄', 'delayRender(', '缺 delayRender：测量晚于截帧，门禁等于不存在'),
    ('逐帧持柄', 'continueRender(', '缺 continueRender：handle 永远不释放，渲染卡死'),
    ('逐帧持柄', 'cancelRender(', '缺 cancelRender：硬拦根本无从谈起'),
    ('等字体', 'document.fonts.ready', '字体未就绪直接 return 会让每帧都跳过（另外两道门禁都踩过）'),
    # v2 判据的**收窄**就是这道门禁的全部价值所在（也是它不再与 ClippingGate 重复报的原因），
    # 所以这两条收窄各自一条夹具：削掉任一条，门禁就退回 v1 那个"什么都判"的宽口径。
    ('只看文字叶元素', 'if (el.children.length) return;', '丢掉了"只看叶元素"的收窄：容器的整块宽会被当成墨迹（居中文字误判）'),
    ('只看文字叶元素', "textContent || ''", '丢掉了"含文字"的收窄：无字元素（装饰块 / 铺底）会被拉进来判'),
    ('墨迹口径', 'createRange', '丢了 Range 取墨迹：块级元素整块宽会被误判（居中文字）'),
    ('白名单', 'data-gate-allow', '没有接 data-gate-allow：有意出血无处声明，只能调阈值'),
    ('白名单', 'data-gate-skip', '没有接 data-gate-skip'),
    ('覆盖率', 'REPORT_EVERY', '没有覆盖率日志：分不清"没报"与"没跑"'),
)


def canvas_bounds_wiring(project_dir):
    """静态检查渲染期画布越界门禁：装没装、片子那条**是 warn**、接触表那条**是 block**、判据还在不在。"""
    src = os.path.join(project_dir, 'src')
    gate = os.path.join(src, 'canvas-bounds-gate.tsx')
    index = os.path.join(src, 'index.tsx')
    if not os.path.isfile(gate):
        return ['canvas-bounds-gate.tsx 不存在：渲染期画布越界门禁没有装']
    if not os.path.isfile(index):
        return ['src/index.tsx 不存在：无法确认门禁有没有被挂上']
    g = io.open(gate, encoding='utf-8').read()
    t = io.open(index, encoding='utf-8').read()
    problems = []
    for kind, needle, why in CANVAS_BOUNDS_NEEDLES:
        if needle not in g:
            problems.append(f'{kind}：{why}（找不到 `{needle}`）')
    if "from './canvas-bounds-gate'" not in t:
        problems.append('接线：index.tsx 没有 import CanvasBoundsGate')
    mounts = t.count('<CanvasBoundsGate')
    if mounts < 2:
        problems.append(f'接线：index.tsx 没有挂载 CanvasBoundsGate（找到 {mounts} 处；片子与接触表各要一处）')
    # 两条挂载**故意不同档**（2026-09-22）：片子 warn（它的硬拦发生在交付渲染最后一刻，
    # 判据误报的代价 = 整片不出）、接触表 block（件看不见 = 目录页缺件，必须中断）。
    # 谁把它们"统一"成同一档，都会被这条夹具抓住 —— 这是刻意的，别来放宽。
    if '<CanvasBoundsGate mode="warn"' not in t:
        problems.append('接线：片子那条 CanvasBoundsGate 不是 mode="warn"（理由见 index.tsx 里的注释：'
                        '在片子上它的价值未经证明，硬拦误报 = 整个交付不出片）')
    if '<CanvasBoundsGate mode="block"' not in t:
        problems.append('接线：接触表那条 CanvasBoundsGate 不是 mode="block"（件整件看不见 = 目录页缺件，只出声不够）')
    return problems


# 本脚本自带一个 CLI 分支，好让下面的夹具走和其它门禁同一条 `run()`/`case()` 通道
if len(sys.argv) >= 3 and sys.argv[1] == '--canvas-bounds-wiring':
    probs = canvas_bounds_wiring(sys.argv[2])
    for p in probs:
        print(p)
    sys.exit(0 if not probs else 1)

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

# ── N · 帧参数名门禁必须覆盖 **src/components/ 那一层**（v3.1.1 的 27 件）──
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

# ════════════════════════════════════════════════════════════════════════════
# AB · 渲染期「画布越界」门禁（CanvasBoundsGate）的接线、档位与判据收窄
#
# 渲染期门禁没法在这个脚本里真渲一帧（那要浏览器 + 30 秒/帧），但**最容易在重构里被削掉的几层**
# 是纯静态可查的：挂载、档位（片子 warn / 接触表 block）、硬拦纪律、判据的收窄。
# 真渲染的正/负向夹具与实测数字在 references/composition-gate.md §5.2。
# ════════════════════════════════════════════════════════════════════════════
CBW = [PY, os.path.join(SKILL, 'scripts/negative-gate-check.py'), '--canvas-bounds-wiring']


def mksrc_edits(edits):
    """带模板 src 的夹具项目，并按 (相对路径, 原文, 替换) 逐条改。
    锚点找不到直接断言失败 —— 防"夹具没改到、于是因为别的原因失败"这种假通过。"""
    td_, rc_, out_ = mkproj()
    for base, _dirs, files in os.walk(os.path.join(TPL, 'src')):
        for name in files:
            if not name.endswith(('.tsx', '.ts')):
                continue
            src_path = os.path.join(base, name)
            dst = os.path.join(td_, 'src', os.path.relpath(src_path, os.path.join(TPL, 'src')))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src_path, dst)
    for rel, old, new in edits:
        p = os.path.join(td_, 'src', rel)
        text = io.open(p, encoding='utf-8').read()
        assert old in text, f'夹具锚点没找到：src/{rel} :: {old[:60]}'
        io.open(p, 'w', encoding='utf-8', newline='').write(text.replace(old, new, 1))
    return td_, rc_, out_


# AB0 = 阳性对照：模板原样必须全过（证明 AB1–AB4 不是"见到就报"）
td, _rc, _out = mksrc_edits([])
case('AB0 画布越界门禁 · 接线原样必须过（阳性对照）', [
    ('must_pass', 'canvas-bounds-wiring', run(CBW + [td])),
])
cleanup(td)

# AB1 = 片子那条挂载被删掉（门禁在成片上等于不存在）
td, _rc, _out = mksrc_edits([('index.tsx', '<CanvasBoundsGate mode="warn"/>', '')])
case('AB1 画布越界门禁 · 删掉片子里的挂载', [
    ('must_block:没有挂载 CanvasBoundsGate', 'canvas-bounds-wiring', run(CBW + [td])),
])
cleanup(td)

# AB2 = 「异常不被自家 catch 吞」被删掉 —— 本仓库实测过两次的"报了硬拦却出图 rc=0"
td, _rc, _out = mksrc_edits([('canvas-bounds-gate.tsx', 'if (blocked) throw e;', 'if (false) throw e;')])
case('AB2 画布越界门禁 · 删掉硬拦纪律（异常被自家 catch 吞）', [
    ('must_block:硬拦纪律', 'canvas-bounds-wiring', run(CBW + [td])),
])
cleanup(td)

# AB3 = 片子那条被改成 block（"统一档位"这个最容易顺手做的动作）→ 必须被抓住
# 理由：它的硬拦发生在**交付渲染的最后一刻**，而 v2 判据在片子上的价值未经证明；
# 误报的代价是整片不出，比漏报一处 20px 裁切贵。接触表那条则必须保持 block。
td, _rc, _out = mksrc_edits([('index.tsx', '<CanvasBoundsGate mode="warn"/>', '<CanvasBoundsGate mode="block"/>')])
case('AB3 画布越界门禁 · 把片子那条擅自升成 block', [
    ('must_block:不是 mode="warn"', 'canvas-bounds-wiring', run(CBW + [td])),
])
cleanup(td)

# AB4 = 判据的**收窄**被削掉（"只看含文字的叶元素"退回"什么都判"）→ 必须被抓住。
# 这一条守的是 v2 的全部价值：宽口径正是 v1 与 ClippingGate 重复报、且要养一整套排除规则的根源。
td, _rc, _out = mksrc_edits([('canvas-bounds-gate.tsx', 'if (el.children.length) return;', 'if (false) return;')])
case('AB4 画布越界门禁 · 削掉"只看叶元素"的收窄', [
    ('must_block:只看叶元素', 'canvas-bounds-wiring', run(CBW + [td])),
])
cleanup(td)

# ════════════════════════════════════════════════════════════════════════════
# AC/AD/AE · 讲法字段 G-14②：同一 `move` **不得连续 ≥3 镜**
#
# 为什么补这一组：这条规则在 `references/narrative-moves.md` 写了**两处**（§2 动作表的开头、§4 门禁表），
# 可它此前**从没被任何门禁读过** —— `validate-presentation.py` 的 G-14 只查了"move 是不是 10 个名字
# 之一"，于是写 3 镜连续 `引入` 的 shots.json 照旧 PASS。**判据加了而夹具没加 = 那道门仍然只是名义存在**，
# 所以判据与夹具同版落地：
#   AC = 连续 3 镜必须拦（阈值下界，文档说"不得连续 ≥3 镜"）；
#   AD = 连续 2 镜必须放行（阴性对照，证明它不是"见到重复就拦"—— 上限是 2 镜）；
#   AE = 中间夹一镜**缺 move** 时，不许把它两侧接成一条假的"连续 3 镜"（缺 move 自己另报 P0）。
#        ⚠️ 这条不是凑数：判据的第一版写的是 `continue`（跳过缺 move 的那镜但**不打断计数**），
#        于是 `引入,引入,缺move,引入` 被报成"S1→S2→S4 连续 3 镜"—— 一句用户照着改不了的假话。
#        夹具当场抓到，判据才改成"遇到非闭集 move 就断段"。
# ════════════════════════════════════════════════════════════════════════════

def mut_move_run(d, first, count):
    """把从 first 起的 count 镜改成同一个 move（模板 S1 本来就是 `引入`）。"""
    for k in range(first, first + count):
        d['shots'][k]['move'] = d['shots'][first]['move']
    return d


td, rc0, out0 = mkproj(lambda d: mut_move_run(d, 0, 3))
case('AC 讲法字段 · 同一 move 连续 3 镜（G-14②）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:同一 move 连续 3 镜', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

td, rc0, out0 = mkproj(lambda d: mut_move_run(d, 0, 2))
case('AD 讲法字段 · 同一 move 连续 2 镜（阴性对照，必须放行）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_pass', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)


def mut_move_run_gap(d):
    """S1/S2/S4 都是 `引入`，S3 删掉 move：不许报"连续 3 镜"（缺 move 已经报了 P0）。"""
    mut_move_run(d, 0, 2)
    d['shots'][3]['move'] = d['shots'][0]['move']
    d['shots'][2].pop('move', None)
    return d


td, rc0, out0 = mkproj(mut_move_run_gap)
case('AE 讲法字段 · 缺 move 打断连续计数（不许拼出假的连续）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:缺 move', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
    ('must_absent:同一 move 连续', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# ════════════════════════════════════════════════════════════════════════════
# AF–AK · 讲法字段 G-15：`evidence` 必须**作为 JSX 用法**出现在场景源码里（v2 简版口径）
#
# 为什么补这一组：`references/narrative-moves.md` §2/§4 与 `presentation-gate.md` 把 `evidence`
# 的判法写成 **P0**，而 `validate-presentation.py` 此前读它的唯一一处是 `if not ev:`（只查字段非空）：
# 名字写成**不存在的**、或指向一个**不动的**东西，门禁一声不响。
# 「文档里有、代码里没有」是本仓库最危险的一类缺陷（CardFitGate / OverlapGate / bottomFill 都是这样废掉的）。
#
# 2026-09-22 按实测**简化**（原版 465 行：手写 JSX 解析 + 本镜作用域 + 帧驱动白名单 + 降级分支）。
# 现在只查一件事：名字有没有被当成 JSX 用法（`<名字 …>` / `<名字/>`）用在场景源码里。
# 夹具跟着换 —— **只留还成立的那几条**，并把它原本想防的东西重新钉一遍：
#   AF = 名字在源码里根本不存在              → P0（必须拦）
#   AG = 名字在**别的镜**里（StaggerList 只在 S4）→ 现在**放行**：这就是"不做本镜作用域"的代价本身，
#        用 must_pass 把它**钉在明处**（谁哪天加回本镜作用域，这条夹具会先失败，提醒他同步改口径与文档）
#   AJ = 名字只出现在**注释**里（`exitAt` 是模板里被删掉、只在注释中留名的小助手）→ P0
#        （⚠️ 这一条是实测逼出来的：真实工程 overview-film 的 S2 把 `MetricGrid` 换成手绘行 + `Chart`，
#         只在注释里留了一句"这里本来用 MetricGrid"——"文件里搜得到名字"的宽松判法会**假通过**）
#   AK = 原样（带模板 src）→ 全过 —— AF/AJ 的**阴性对照**，也证明模板 8 镜的 evidence 个个合格
#        （E 用例是"只有分镜表、没有 src"的版本，它走不到这条判据）
# 删掉的两条夹具与原因（"不再具备的能力"不留夹具，但**在文档里如实写清、不留空承诺**）：
#   AH/AI = 帧驱动 vs 静态（P1 只点名）—— 这半边判据已删除：帧驱动量只能做**白名单**判定，而它的误报面
#           已经实测到了（帧经 `ctx` 这类不透明参数传进组件的写法会被判成静态，动作表推荐的 `PhaseRail`
#           恰是这种写法，判成 P0 就等于"照文档写、门禁拦你"）。
#   AL = 切不出"本镜"时降级并自报 —— 已经没有"本镜"这一层，无级可降。
# 两条都写进了 `references/narrative-moves.md` §2 与 `presentation-gate.md` §G-15 的"现在不做"。
# ════════════════════════════════════════════════════════════════════════════


def mksrc_mut(mutate=None, replace_scene=None):
    """带模板 src 的夹具项目，可**同时**改 shots.json（改在 resolve-shots 之前，与 X/AC 同口径）
    与 scenes.tsx。锚点找不到直接断言失败 —— 防"夹具没改到、于是因为别的原因通过"。"""
    td, rc0, out0 = mkproj(mutate)
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


def mut_evidence(idx, name):
    def f(d):
        d['shots'][idx]['evidence'] = name
        return d
    return f


# AF · 名字在源码里根本不存在 → 必须拦（且不能走成"静态"那一侧）
td, rc0, out0 = mksrc_mut(mut_evidence(0, 'GhostWidget'))
case('AF 讲法字段 · evidence 指向源码里不存在的名字（G-15）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:找不到这个用法', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
    ('must_absent:看不出一丝帧驱动', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# AG（改写）· 名字在**别的镜**里（StaggerList 只在 S4 出现）→ **必须放行**：
# 这一条现在**语义变了** —— 它不再钉"本镜作用域"（那个能力已按实测砍掉），
# 而是把这个**已知漏检**钉在明处：名字没在本镜用到、只在别的镜用了，判据看不见。
# 谁哪天把本镜作用域加回来，这条夹具会先失败 —— 那是**有意的信号**：请同时改口径与文档。
td, rc0, out0 = mksrc_mut(mut_evidence(0, 'StaggerList'))
case('AG 讲法字段 · evidence 指向别镜的组件（v2 口径下**已知漏检**，如实放行）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_pass', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# AJ · 名字只出现在**注释**里（`exitAt` 是模板里被删掉、只在注释中留名的小助手）→ 必须拦
td, rc0, out0 = mksrc_mut(mut_evidence(0, 'exitAt'))
case('AJ 讲法字段 · evidence 只出现在注释里（注释里的名字不算"用到"）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:找不到这个用法', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# AK · 阴性对照：带 src 的原样模板必须全过（也证明模板 8 镜的 evidence 个个合格）
td, rc0, out0 = mksrc_mut()
case('AK 讲法字段 · 带场景源码的原样模板（阴性对照，必须全过）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_pass', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# ════════════════════════════════════════════════════════════════════════════
# BB–BG · 四道"零对抗夹具"门禁的补钉 + HEAD 里三条新硬拦行为的钉桩
#
# 审计结论：validate-layering / validate-visual-plan / validate-audio-levels /
# validate-official-example 此前**只在 CI 与一致性检查里正向跑**，一条喂坏输入的
# 实证都没有 —— "门在名义上存在、实际静默放行"正是本脚本存在的意义要防的病。
# 每一道各补 must_block（定向 needle，不用宽松匹配）+ must_pass 阴性对照
# （好输入必须过，防判据写反方向把什么都拦）。全部离线自包含：临时目录造、结束清理。
#
# 另三条 HEAD 新硬拦行为各一条 must_block（needle = 报错文案里的独特子串）：
#   BD3 = validate-audio-levels：素材读不到峰值（损坏/非音频）→ rc=2 门禁自身故障
#   BF1 = validate-composition：有场景源码但某镜切不出 `const S…: React.FC<` 函数体 → P0
#   BG1 = validate-presentation：resolved 与 declared 镜数不一致 → P0"疑未重跑"
# ════════════════════════════════════════════════════════════════════════════

# ── BB · validate-layering（对象层/遮挡契约）：直接喂 asset-manifest 路径 ──
# 判据（源码里逐条核实过的）：
#   · floating 部件的 occlusion_contract 必须是 always-visible（否则报 "floating parts must use always-visible"）
#   · floating 的 z 必须**压过**同场景 base/slot/status 的最高 z（否则报 "must be above"）
# 坏输入只踩一个判据（z 抬高 / 契约改对），保证 needle 定位到被测分支而不是"因为别的原因失败"。
LAY_BASE = {"id": "base1", "scene": "S1", "z": 10, "layer_role": "base",
            "occlusion_contract": "normal", "exit_contract": "scene-cut"}


def mklayer(badge):
    td = tempfile.mkdtemp(prefix='nv-layer-')
    doc = {"parts": [dict(LAY_BASE), badge]}
    p = os.path.join(td, 'asset-manifest.json')
    io.open(p, 'w', encoding='utf-8', newline='').write(json.dumps(doc, ensure_ascii=False, indent=2))
    return td, p


LAY = os.path.join(SKILL, 'scripts/validate-layering.py')
td, mp = mklayer({"id": "badge1", "scene": "S1", "z": 200, "layer_role": "floating",
                  "occlusion_contract": "normal", "exit_contract": "scene-cut"})
case('BB1 分层契约 · floating 用了 normal 遮挡契约', [
    ('must_block:floating parts must use always-visible', 'validate-layering', run([PY, LAY, mp])),
])
cleanup(td)

td, mp = mklayer({"id": "badge1", "scene": "S1", "z": 5, "layer_role": "floating",
                  "occlusion_contract": "always-visible", "exit_contract": "scene-cut"})
case('BB2 分层契约 · floating 的 z 压在底件之下', [
    ('must_block:must be above', 'validate-layering', run([PY, LAY, mp])),
])
cleanup(td)

td, mp = mklayer({"id": "badge1", "scene": "S1", "z": 200, "layer_role": "floating",
                  "occlusion_contract": "always-visible", "exit_contract": "scene-cut"})
case('BB3 分层契约 · 两份契约全对（阴性对照，必须放行）', [
    ('must_pass', 'validate-layering', run([PY, LAY, mp])),
])
cleanup(td)

# ── BC · validate-visual-plan（视觉模式/镜时生命周期/介质溯源/画布档一致性）──
# 判据逐条核实：visual_mode 必须落在 {image-text, pure-text, pure-graphic}；
# 场景帧区间必须从 0 起**无缝无叠**地铺到 duration_frames。
# 最小白名单工程：一份 pure-text 场景（无插图资产 → assets 空数组即合法），
# 两条坏输入各只踩一个判据。
def mkvisual(scene0, duration):
    td = tempfile.mkdtemp(prefix='nv-vplan-')
    os.makedirs(os.path.join(td, 'manifests'), exist_ok=True)
    am = {"scenes": [scene0], "duration_frames": duration}
    io.open(os.path.join(td, 'manifests/asset-manifest.json'), 'w', encoding='utf-8', newline='').write(
        json.dumps(am, ensure_ascii=False, indent=2))
    io.open(os.path.join(td, 'manifests/visual-assets.json'), 'w', encoding='utf-8', newline='').write(
        json.dumps({"assets": []}, ensure_ascii=False, indent=2))
    return td


VPLAN = os.path.join(SKILL, 'scripts/validate-visual-plan.py')
GOOD_SCENE = {"id": "S1", "visual_mode": "pure-text", "start_frame": 0, "end_frame": 120,
              "visual_asset_ids": [], "mount_contract": "start-inclusive-end-exclusive",
              "exit_contract": "complete-exit"}
td = mkvisual(dict(GOOD_SCENE, visual_mode="pure-illustration"), 120)
case('BC1 视觉规划 · visual_mode 不在闭集', [
    ('must_block:invalid visual_mode', 'validate-visual-plan', run([PY, VPLAN, td])),
])
cleanup(td)

td = mkvisual(dict(GOOD_SCENE, start_frame=10, end_frame=130), 130)
case('BC2 视觉规划 · 时间轴留了断档（0..10 无人覆盖）', [
    ('must_block:uncovered frame gap', 'validate-visual-plan', run([PY, VPLAN, td])),
])
cleanup(td)

td = mkvisual(GOOD_SCENE, 120)
case('BC3 视觉规划 · 自洽的最小规划（阴性对照，必须放行）', [
    ('must_pass', 'validate-visual-plan', run([PY, VPLAN, td])),
])
cleanup(td)

# ── BD · validate-audio-levels（音效可听度：峰值地板 -12 dBFS）──
# 素材用标准库 wave 现合成 16-bit 正弦（离线、零下载）；ffmpeg 实测：
#   幅度 200 → 峰值 -44.3 dBFS（顶 P0）；幅度 26000 → -2.0 dBFS（该放行）。
# ⚠️ BD1/BD2 依赖环境里有 ffmpeg：没装时门禁按纪律报 rc=2"测量失败"，
# 夹具会如实红掉 —— 这正是 HEAD 修掉的"静默放行"反面的镜像，不是夹具的锅。
def write_tone_wav(path, amp, secs=0.3, rate=22050):
    import math, struct, wave
    n = int(secs * rate)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b''.join(struct.pack('<h', int(amp * math.sin(2 * math.pi * 440 * i / rate)))
                               for i in range(n)))


def mksfxproj(files):
    """files: {名字: 字节生成器}。返回带 public/sfx 的最小工程目录。"""
    td = tempfile.mkdtemp(prefix='nv-sfx-')
    d = os.path.join(td, 'public', 'sfx')
    os.makedirs(d, exist_ok=True)
    for name, gen in files.items():
        p = os.path.join(d, name)
        if gen is None:
            open(p, 'wb').close()
        elif isinstance(gen, bytes):
            io.open(p, 'wb').write(gen)
        else:
            gen(p)
    return td


ALEV = os.path.join(SKILL, 'scripts/validate-audio-levels.py')
td = mksfxproj({'quiet.wav': lambda p: write_tone_wav(p, 200)})
case('BD1 音效可听度 · 素材峰值 -44 dBFS（太轻）', [
    ('must_block:低于 -12 dBFS', 'validate-audio-levels', run([PY, ALEV, td])),
])
cleanup(td)

td = mksfxproj({'loud.wav': lambda p: write_tone_wav(p, 26000)})
case('BD2 音效可听度 · 素材峰值 -2 dBFS（阴性对照，必须放行）', [
    ('must_pass', 'validate-audio-levels', run([PY, ALEV, td])),
])
cleanup(td)

# BD3 · HEAD 新行为：素材**读不到峰值**（损坏/非音频）→ rc=2 门禁自身故障，不是 rc=1 内容问题。
# 判据核实：peak_db() 拿不到 max_volume 就记 measure_fail → main 里先于一切 PASS/FAIL 结论打
# "门禁自身故障"并 return 2。"测量没跑成"与"内容没测出缺陷"必须可区分（旧版记 P1 → rc=0 静默过）。
td = mksfxproj({'corrupt.wav': b'THIS IS NOT A WAVE FILE, just some text bytes.'})
case('BD3 音效可听度 · 损坏素材读不到峰值 → rc=2 门禁自身故障', [
    ('must_block:门禁自身故障', 'validate-audio-levels', run([PY, ALEV, td])),
])
cleanup(td)

# ── BE · validate-official-example（官方示例一致性锁）──
# 它校验的是**技能自带的 example-project**，没有 project 参数 —— 但 SKILL 路径由
# 脚本自身位置推导，所以"整技能拷一份（临时目录）、改副本再跑副本里的脚本"就是合法喂点。
# 副本裁掉 assets/demo 与 *.ttf（P 用例同款理由：快）；assets/fonts 的三个文件补零字节
# 占位 —— 官方示例对它们只查 is_file()，而 example-project 的 png **必须真拷**
# （validate-visual-plan 会核它的 sha256，空文件会先撞"missing or empty asset"，
#  那又是一次"因为别的原因失败"）。
def mk_skill_full():
    td = tempfile.mkdtemp(prefix='nv-skill-full-')
    ignore = shutil.ignore_patterns('node_modules', 'renders', '.git', '.cache', '.tools',
                                    '__pycache__', 'demo', '*.mp4', '*.webp', '*.jpg', '*.ttf')
    shutil.copytree(SKILL, td, dirs_exist_ok=True, ignore=ignore)
    for name in ('LXGWWenKaiLite-Regular.ttf', 'LXGWWenKaiLite-Medium.ttf'):
        q = os.path.join(td, 'assets', 'fonts', name)
        if not os.path.exists(q):
            open(q, 'wb').close()
    return td


td_skill = mk_skill_full()
OE = os.path.join(td_skill, 'scripts/validate-official-example.py')
case('BE1 官方示例 · 忠实副本必须全过（阴性对照）', [
    ('must_pass', 'validate-official-example', run([PY, OE])),
])
# 坏输入：把契约的画布宽从 2560 改成 1080（身份锁的第一道判据）→ 必须点名"canvas ... changed"
cp = os.path.join(td_skill, 'references/locked-style-contract.json')
_doc = json.loads(io.open(cp, encoding='utf-8').read())
_doc['canvas']['width'] = 1080
io.open(cp, 'w', encoding='utf-8', newline='').write(json.dumps(_doc, ensure_ascii=False, indent=2))
case('BE2 官方示例 · 契约画布宽被改成 1080', [
    ('must_block:canvas or native motion rate changed', 'validate-official-example', run([PY, OE])),
])
cleanup(td_skill)

# ── BF · validate-composition 覆盖率自述（HEAD 新硬拦）──
# 病因：`scene_source` 只扫一层时，`if scene_text` 为空 → live 名字可解析/转场兑现/
# beats 越界三类判据**整段静默跳过**还 rc=0。修复口径：只要 src 里有**任何** .tsx
# （scene_text 非空），某一镜切不出 `const S…: React.FC<` 函数体就记 P0。
# BF1 夹具：最小一份"有场景源码"的工程（scenes.tsx 存在但**没有** FC 形态的镜函数）
# → 8 镜各报一条"场景源码不可读，判据无法执行"。needle 是该分支独有的报错文案。
td, rc0, out0 = mkproj()
io.open(os.path.join(td, 'src/scenes.tsx'), 'w', encoding='utf-8', newline='').write(
    "export const Scenes = () => null;" + NL)
case('BF1 组合门禁 · 有源码但镜函数切不出（覆盖率自述）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:场景源码不可读，判据无法执行', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
])
cleanup(td)

# BF2 · 同一判据的**方向对照**：带模板全量 src（每镜都有 `const S…: React.FC<`）
# 必须放行 —— 证明 BF1 不是"见到源码就报"，覆盖率自述只在真切不出时才响。
td, rc0, out0 = mksrc()
case('BF2 组合门禁 · 镜函数齐全的原样 src（阴性对照）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_pass', 'validate-composition', run([PY, os.path.join(SKILL, 'scripts/validate-composition.py'), td])),
])
cleanup(td)

# ── BG · validate-presentation resolved/declared 一致性（HEAD 新硬拦）──
# 病因：旧版 `if not rec: continue` —— 改了 shots.json 没重跑 resolve-shots 时，
# resolved 陈旧缺镜，整段 G-1 被静默跳过还能 exit 0。
# 夹具：resolve 之后**人为删掉 resolved 的最后一镜**（模拟陈旧清单），declared 仍有 8 镜
# → 镜数不一致 + 缺记录两处都点名"疑未重跑 scripts/resolve-shots.py"。
# 放行侧已由 E（resolved 与 declared 一致 → presentation PASS）覆盖，不重复造。
td, rc0, out0 = mkproj()
rp = os.path.join(td, 'manifests/shots.resolved.json')
rr = json.loads(io.open(rp, encoding='utf-8').read())
assert len(rr['shots']) >= 2, 'resolved 不足 2 镜，删一条就不是"不一致"而是清空了'
dropped = rr['shots'].pop()['id']
io.open(rp, 'w', encoding='utf-8', newline='').write(json.dumps(rr, ensure_ascii=False))
case(f'BG 呈现门禁 · resolved 被删成 7 镜（缺 {dropped}，疑未重跑 resolve）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:疑未重跑', 'validate-presentation', run([PY, os.path.join(SKILL, 'scripts/validate-presentation.py'), td])),
])
cleanup(td)

# ════════════════════════════════════════════════════════════════════════════
# BH–BJ · 相机隐式默认收口（resolve-shots.expand_cam ⇄ shotkit.tsx 的 shotCam）
#
# 由来：PY 侧展开把"省略 to"一律回落成 `to := from`（= 不动），而 TS 侧 shotCam 有 intent
# 默认（establish 1.03 @:113 / push-in 1.12 @:116 / pull-back to=1.0、from(k1)=1.12 @:119 /
# reveal 1.08 @:125 / micro-orbit rotY ?? 6 @:128 / still 尾帧 `o.to ?? o.from ?? 1` @:109）。
# 不对齐的后果两头都有：
#   · 误拦 —— establish/push-in 省 to 的镜展开成零运动，撞"声明运镜却不动"P0；
#   · 漏放 —— micro-orbit 省 rotY 时 resolved 里是 0°，成片其实真转 6°，门禁看不见。
# 收口后展开只剩一份真源（validate-shot-motion 直接 import expand_cam），默认对齐落在
# resolve-shots.py 一处。三条夹具把**新默认**钉在 resolved 输出上，并保住 P0 判据本身：
#   BH = micro-orbit 省 rotY → resolved rotY 幅度 = 6（正向钉，关闭漏放）；
#   BI = establish 省 to   → resolved s 尾值 = 1.03（正向钉，关闭误拦）；
#   BJ = 显式 from==to 的 push-in（**真正**零运动）→ validate-shot-motion 必须仍拦
#        —— G 那条"冻结假运镜"喂的是改写 resolved 的坏输入；默认对齐后"省参数"不再
#        等于零运动，这条把 P0"几乎不动"的 must_block 换喂**显式写了 from==to** 的坏输入，
#        判据一字未动，只是喂准。
# ════════════════════════════════════════════════════════════════════════════

MOTION = os.path.join(SKILL, 'scripts/validate-shot-motion.py')


def mut_cam(idx, cam):
    """整组替换某镜的 camera 声明（放在 resolve 之前，走真实展开路径）。"""
    def f(d):
        d['shots'][idx]['camera'] = dict(cam)
        return d
    return f


def resolved_keys(td_, sid):
    rp = os.path.join(td_, 'manifests/shots.resolved.json')
    rr = json.loads(io.open(rp, encoding='utf-8').read())
    return next(s for s in rr['shots'] if s['id'] == sid)['keys']


# BH · micro-orbit 省略 rotY → resolved 里 rotY 幅度必须是 6°（shotkit.tsx:128 的 `rotY ?? 6`）
td, rc0, out0 = mkproj(mut_cam(2, {'intent': 'micro-orbit', 'at': 10, 'dur': 38,
                                   'x': 960, 'y': 540, 'from': 1.05}))
rot_max = max((abs(k.get('rotY', 0.0)) for k in resolved_keys(td, 'S3')), default=-1.0) if rc0 == 0 else -1.0
case('BH 相机默认 · micro-orbit 省略 rotY → resolved rotY 幅度 6°（正向钉）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_warn:rotY 幅度 = 6.0', 'resolved 断言（BH）', (0, f'resolved rotY 幅度 = {rot_max}')),
])
cleanup(td)

# BI · establish 省略 to → resolved 末关键帧 s 必须是 1.03（shotkit.tsx:113 的 `o.to ?? 1.03`）
td, rc0, out0 = mkproj(mut_cam(2, {'intent': 'establish', 'at': 10, 'dur': 38,
                                   'x': 960, 'y': 540, 'from': 1.0}))
s_tail = resolved_keys(td, 'S3')[-1]['s'] if rc0 == 0 else -1.0
case('BI 相机默认 · establish 省略 to → resolved s 尾值 1.03（正向钉）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_warn:s 尾值 = 1.03', 'resolved 断言（BI）', (0, f'resolved s 尾值 = {s_tail}')),
])
cleanup(td)

# BJ · 真正零运动（显式 from==to 的 push-in）→ "声明运镜却不动"P0 必须仍拦（判据不许因收口失效）
td, rc0, out0 = mkproj(mut_cam(2, {'intent': 'push-in', 'at': 10, 'dur': 38,
                                   'x': 960, 'y': 540, 'from': 1.0, 'to': 1.0}))
case('BJ 相机默认 · 显式 from==to 的零运动 push-in 仍被 P0 拦（喂准的坏输入）', [
    ('must_pass', 'resolve-shots', (rc0, out0)),
    ('must_block:几乎不动', 'validate-shot-motion', run([PY, MOTION, td])),
])
cleanup(td)

# ════════════════════════════════════════════════════════════════════════════
# CA–CF · 本轮三项收口的负向夹具（判据与夹具同版落地）
#   CA = validate-visual-plan：index.tsx **在**但抽不到 <Composition width> →
#        必须报"canvas consistency check cannot run"（旧版这里 return [] 静默跳过，
#        画布一致性整段判据等于不存在）。
#   CB = 同一判据的**放行侧**：index.tsx 带合法 width={2560} 的 Composition → 必须过
#        （证明 CA 不是"见到 index.tsx 就报"；无 index.tsx 的放行侧仍由 BC3 钉着）。
#   CC = match-timing：防护从 assert 换成 raise SystemExit 后，`python -O` 喂
#        "lock 与 chapters 镜数不一致"的坏输入仍必须拦（needle = 新报错独有文案；
#        旧版 -O 下 assert 被剥离，会带着错误数据往下跑到 FileNotFoundError 为止）。
#   CD = validate-caption-sync：manifests/ 与 src/ 两份 caption-cues.json 都在且**不等** →
#        必须报"dual-copy divergence"（防"校验一份、渲染另一份"）。
#   CE = 两份等值 → 必须放行（CD 的阴性对照）。
#   CF = validate-skill-consistency 新增的画布数值双真源交叉校验：把 canvas.ts 的
#        designW 单独改掉 → 一致性检查必须红（needle = "canvas mode numeric drift"）。
#        放行侧 = 本仓全量 `python scripts/validate-skill-consistency.py` rc=0（任务验证项）。
# ════════════════════════════════════════════════════════════════════════════

td = mkvisual(GOOD_SCENE, 120)
os.makedirs(os.path.join(td, 'src'), exist_ok=True)
io.open(os.path.join(td, 'src/index.tsx'), 'w', encoding='utf-8', newline='').write(
    "import {registerRoot} from 'remotion';" + NL + "export const Root = () => null;" + NL)
case('CA 视觉规划 · index.tsx 在但 Composition 宽度抽不出（判据无法执行）', [
    ('must_block:canvas consistency check cannot run', 'validate-visual-plan', run([PY, VPLAN, td])),
])
cleanup(td)

td = mkvisual(GOOD_SCENE, 120)
os.makedirs(os.path.join(td, 'src'), exist_ok=True)
io.open(os.path.join(td, 'src/index.tsx'), 'w', encoding='utf-8', newline='').write(
    '<Composition id="NotebookVideoFilm" durationInFrames={120} fps={30} width={2560} height={1440}/>' + NL)
case('CB 视觉规划 · 带合法 width={2560} 的 index.tsx（阴性对照，必须放行）', [
    ('must_pass', 'validate-visual-plan', run([PY, VPLAN, td])),
])
cleanup(td)

td = tempfile.mkdtemp(prefix='nv-mt-')
os.makedirs(os.path.join(td, 'manifests'), exist_ok=True)
io.open(os.path.join(td, 'manifests/chapters-timing-lock.json'), 'w', encoding='utf-8', newline='').write(
    json.dumps([{'start_ms': 0, 'end_ms': 1000}, {'start_ms': 1000, 'end_ms': 2000}]))
io.open(os.path.join(td, 'manifests/chapters.json'), 'w', encoding='utf-8', newline='').write(
    json.dumps([{'start_ms': 0, 'end_ms': 1200}]))
case('CC 时间对齐 · python -O 下镜数不一致仍必须拦（assert 已换 SystemExit）', [
    ('must_block:chapter count mismatch', 'match-timing(-O)',
     run([PY, '-O', os.path.join(SKILL, 'scripts/match-timing.py'), td])),
])
cleanup(td)

CAPSYNC = os.path.join(SKILL, 'scripts/validate-caption-sync.py')


def mkcues(diverge=False):
    """最小"双份 cues"工程：manifests 与 src 各一份 caption-cues.json + 词级时间戳。
    diverge=True 时只改 src 那份（真正被 index.tsx import 的那份），内容**不等**。"""
    td_ = tempfile.mkdtemp(prefix='nv-cues-')
    for sub in ('manifests', 'src', 'audio'):
        os.makedirs(os.path.join(td_, sub), exist_ok=True)
    shutil.copy(os.path.join(TPL, 'manifests/caption-cues.json'), os.path.join(td_, 'manifests/caption-cues.json'))
    shutil.copy(os.path.join(TPL, 'manifests/caption-cues.json'), os.path.join(td_, 'src/caption-cues.json'))
    shutil.copy(os.path.join(TPL, 'audio/narration.mp3.json'), os.path.join(td_, 'audio/narration.mp3.json'))
    if diverge:
        p = os.path.join(td_, 'src/caption-cues.json')
        doc = json.loads(io.open(p, encoding='utf-8').read())
        doc['cues'][0]['text'] = doc['cues'][0]['text'] + '（只改了渲染那份，校验那份不知道）'
        io.open(p, 'w', encoding='utf-8', newline='').write(json.dumps(doc, ensure_ascii=False, indent=2))
    return td_


td = mkcues(diverge=True)
case('CD 字幕同步 · manifests 与 src 两份 caption-cues 不等（校验一份渲染另一份）', [
    ('must_block:dual-copy divergence', 'validate-caption-sync',
     run([PY, CAPSYNC, os.path.join(td, 'audio/narration.mp3.json'), os.path.join(td, 'manifests/caption-cues.json')])),
])
cleanup(td)

td = mkcues(diverge=False)
case('CE 字幕同步 · 两份等值（阴性对照，必须放行）', [
    ('must_pass', 'validate-caption-sync',
     run([PY, CAPSYNC, os.path.join(td, 'audio/narration.mp3.json'), os.path.join(td, 'manifests/caption-cues.json')])),
])
cleanup(td)

td_skill = mk_skill_copy()
ctp = os.path.join(td_skill, 'assets/lecture-template/src/theme/canvas.ts')
_ct = io.open(ctp, encoding='utf-8').read()
assert "'16:9': {compW: 2560" in _ct, 'CF 锚点没找到（canvas.ts 的 16:9 行变了？）'
_ct = _ct.replace("'16:9': {compW: 2560, compH: 1440, designW: 1920", "'16:9': {compW: 2560, compH: 1440, designW: 1900", 1)
assert 'designW: 1900' in _ct, 'CF 夹具没改到 canvas.ts'
io.open(ctp, 'w', encoding='utf-8', newline='').write(_ct)
case('CF 一致性 · canvas.ts 的 designW 单独漂移（画布数值双真源交叉校验）', [
    ('must_block:canvas mode numeric drift', 'validate-skill-consistency',
     run([PY, os.path.join(SKILL, 'scripts/validate-skill-consistency.py'), '--root', td_skill])),
])
cleanup(td_skill)

print()
print('== 负向抽查明细 ==')
_steps = 0
for name, ok, detail in results:
    print(('PASS  ' if ok else 'FAIL  ') + name)
    _steps += len(detail)
    for d in detail:
        print(d)
print(f'合计：用例 {len(results)} · 断言 {_steps} · {"全部通过" if all(r[1] for r in results) else "存在失败"}')
sys.exit(0 if all(r[1] for r in results) else 1)
