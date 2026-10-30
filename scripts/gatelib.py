"""gatelib.py — 负向抽查的公共壳：临时工程、跑脚本、断言、汇总。

从 `negative-gate-check.py` 里抽出来，因为**用例会越加越多**（现在 102 例），
壳不该跟着同一个文件一起膨胀；用例模块只要 `from gatelib import case, run, ...`
就能加一条夹具，不用碰这个文件。

两种断言口径别搞混：
  · `must_block` / `must_absent` 要求 **rc != 0**（门必须真的拦）
  · `must_pass` / `must_warn` 要求 **rc == 0**（阴性对照 / 只警告）
只判 rc 会把"因为别的原因失败"记成通过——第一版 P 用例就是这么假通过的。
"""
import io, json, os, re, shutil, subprocess, sys, tempfile

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
        # 会被当成本夹具通过（第一版 P 用例就是这样假通过的：拷贝时跳过了大文件，
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


def summary() -> int:
    """打印明细，返回进程退出码。"""
    print()
    print('== 负向抽查明细 ==')
    steps = 0
    for name, ok, detail in results:
        print(('PASS  ' if ok else 'FAIL  ') + name)
        steps += len(detail)
        for d in detail:
            print(d)
    good = all(r[1] for r in results)
    verdict = "全部通过" if good else "存在失败"
    print(f'合计：用例 {len(results)} · 断言 {steps} · {verdict}')
    return 0 if good else 1
