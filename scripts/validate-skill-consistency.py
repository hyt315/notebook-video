#!/usr/bin/env python3
"""Audit skill files for obsolete renderer residue, stale render inputs, or contract mismatches."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# 默认根目录 = 本脚本所在技能的根；`--root DIR` 可指向一份夹具副本
# （负向抽查要能"喂一份写坏了的技能"，见 scripts/negative-gate-check.py 的 P 用例）。
SKILL = Path(__file__).resolve().parent.parent
if '--root' in sys.argv:
    SKILL = Path(sys.argv[sys.argv.index('--root') + 1]).resolve()
IGNORED_PARTS = {"node_modules", ".git", ".cache", ".tools", "renders", "__pycache__"}
TEXT_SUFFIXES = {'.md', '.py', '.sh', '.cmd', '.mjs', '.json', '.yaml', '.yml', '.tsx', '.cjs'}


def reusable_file(path: Path) -> bool:
    rel = path.relative_to(SKILL)
    return path.is_file() and not any(part in IGNORED_PARTS for part in rel.parts)


# ---------------------------------------------------------------------------
# 文档反引号里的 PascalCase 名字必须能在源码里找到定义
#
# 为什么加这一条：A1（`Attach`）/ A6（`CameraRig`）/ A7（`camScript`）/ A8（六件不可达组件）/
# B11（代码注释层的已删件名）这一整类"会误导执行 AI"的缺陷，之前的门禁一条都拦不住 ——
# 它只查相对链接，不查名字。这一条是同构检查：**文档写了不存在的名字 → 直接报错**。
#
# 判据与边界：
#   · 真值来源 = 模板/示例工程的源码里**定义过的一切标识符**（含未导出的）∪ manifests 里的字符串取值
#     （骨架名 `Stage`/`Corridor` 这类是数据不是标识符）∪ 白名单（外部库 / 平台 API / 文献人名）。
#   · `CHANGELOG.md` **不查**：它是历史记录，按历史处理（写已删组件的名字是它的职责）。
#   · 白名单只装"本来就不属于本仓库的东西"，每类都写了理由；**不要为了消红把自家组件名塞进来**。
#   · **提到已删除的名字时不要加反引号**：本技能里反引号 = "这是可直接使用的标识符"。
#     写历史对照（"X 已于 v3.1 删除"）时用纯文本写名字，检查就不会误报，读者也不会以为它还能用。
# ---------------------------------------------------------------------------
DOC_IDENT_SKIP_FILES = {'CHANGELOG.md'}
DOC_IDENT_WHITELIST = {
    # 平台 / 框架 API（Remotion、React、Web）
    'Composition', 'Sequence', 'Series', 'AbsoluteFill', 'Audio', 'Video', 'Img', 'Still', 'Player',
    'DelayRender', 'ContinueRender', 'CancelRender', 'Interpolate', 'Spring', 'Easing', 'Random',
    'CurrentFrame', 'UseCurrentFrame', 'React', 'ReactDOM', 'JSX', 'TSX', 'HTML', 'CSS', 'SVG', 'DOM',
    'API', 'URL', 'CLI', 'JSON', 'YAML', 'CSV', 'TSV', 'PNG', 'JPG', 'JPEG', 'WEBP', 'MP4', 'MOV',
    'OTF', 'TTF', 'WOFF', 'XML', 'PNPM', 'NPM', 'NodeJS', 'Node', 'GPU', 'CPU', 'RAM', 'ID', 'UI',
    # 依赖与库
    'Remotion', 'Radix', 'KaTeX', 'RoughJS', 'BudouX', 'PrismLight', 'Prism', 'TypeScript', 'Chrome',
    'FFmpeg', 'FFprobe', 'TrueType', 'Typekit', 'Tailwind', 'Emotion', 'Panda', 'Mantine', 'Chakra',
    'HeroUI', 'DaisyUI', 'Storybook', 'Lottie', 'GIF', 'WebP', 'LineBreaker', 'Fflate', 'Lucide',
    'Feather', 'Tabler', 'Simple', 'Icons', 'OpenSCAD',
    # 规范 / 标准 / 许可
    'WCAG', 'OFL', 'MIT', 'ISC', 'Apache', 'MPL', 'UAX', 'CJK', 'SDH', 'TTS', 'ASR', 'LLM', 'AI',
    'BM25', 'EEG', 'ANN', 'SaaS', 'PDF', 'PDFs', 'PPT', 'VIP', 'IDE', 'LRU',
    # 文献 / 出处（调研里引用的作者与刊物，不是本仓库的名字）
    'Mayer', 'Yantis', 'Jonides', 'Gleicher', 'Zikmund', 'Itti', 'Koch', 'Rosenholtz', 'Semizer',
    'Fyfield', 'Klepsch', 'Schmitz', 'Seufert', 'Heliyon', 'ERIC', 'Netflix', 'Foliojs', 'Manim',
    'Motion', 'Canvas', 'AWSM', 'CTML',
    # 本技能自己的非源码标识符（数据字段 / 门禁名 / composition id / 常量）
    'STRUCTURAL', 'DURATION', 'MODES', 'CanvasMode', 'ThemePalette', 'NotebookVideoFilm',
    'NotebookVideoShowcase', 'CardFitFixture', 'CardFitGate', 'CaptionFitGate', 'OverlapGate',
    'SlotGuard', 'AssetGate', 'CameraRig', 'CAM_KEYS_L', 'CAM_KEYS_P',  # 后三者是"已删除"的对照物
    'Overlays', 'TSV', 'YAML', 'ENV', 'NFC', 'PIL', 'PNG', 'Range', 'RangeError',
    'HTTPS_PROXY', 'PATH', 'TTS_API_BASE', 'TTS_API_KEY', 'TTS_MODEL', 'TTS_VOICE', 'TTS_STYLE_PROMPT',
    'REMOTION_CONCURRENCY', 'REMOTION_BROWSER_EXECUTABLE',  # 环境变量，不是源码标识符
    'Chloe', 'Dean', 'Mia', 'Milo', 'TransitionSeries',      # 供应商音色名 / Remotion API
    'FiZoomOut', 'LuZoomOut',                                 # react-icons 的两个字形名（政策里做字节级对照）
    'DeepSeek', 'Opus',                                       # 模型名
    # —— 以下名字在文档里**只允许以"已删除/历史对照"的身份出现**（写它们的用途是告诉读者"别再用"）——
    'BackgroundMute', 'CameraRig', 'SceneContribute', 'SceneShip', 'SceneSkills',
    'ElderPhone', 'FamilyShield', 'Robot', 'Scammer', 'SrcIcon',   # portrait 示例题材的插画命名，从来不是模板组件
}


def doc_defined_names() -> set[str]:
    """本仓库"真实存在过"的标识符集合：模板 + 示例工程源码 ∪ **脚本里的常量与函数** ∪ manifests 字符串取值。

    ⚠️ 第三项是必须的：文档会**正当**引用脚本常量（`BEAT_LATE_FRAMES`、`BEAT_TIGHT_FRAMES` 这类门禁口径），
    只扫 TS 源码会把它们当成"文档编出来的名字"报 P0 —— 复核第二轮我自己就踩了这条假阳性。
    """
    names: set[str] = set()
    for f in (SKILL / 'scripts').glob('*.py'):
        t = f.read_text(encoding='utf-8', errors='ignore')
        names |= set(re.findall(r'^([A-Za-z_][\w]*)\s*=', t, re.M))   # 模块级常量/变量
        names |= set(re.findall(r'^def\s+([A-Za-z_][\w]*)', t, re.M)) # 函数名
    roots = [SKILL / 'assets' / 'lecture-template' / 'src', SKILL / 'assets' / 'example-project' / 'src']
    for root in roots:
        if not root.is_dir():
            continue
        for f in list(root.rglob('*.ts')) + list(root.rglob('*.tsx')):
            t = f.read_text(encoding='utf-8', errors='ignore')
            names |= set(re.findall(r'(?:export\s+)?(?:const|function|class|type|interface|let|var)\s+([A-Za-z_$][\w$]*)', t))
            # 多声明 const（`const BASE_FPS=30,FPS=30,TIMELINE_SCALE=1,...`）：只取第一个名字会漏掉后面所有。
            # 逐行扫，避免在正则里写换行转义。
            for line in t.splitlines():
                if 'const ' not in line or '=' not in line:
                    continue
                head = line.split('const ', 1)[1]
                for part in head.split(';', 1)[0].split(','):
                    m2 = re.match(r'\s*([A-Za-z_$][\w$]*)\s*=', part)
                    if m2:
                        names.add(m2.group(1))
            for m in re.finditer(r'export\s*\{([^}]*)\}', t):
                for part in m.group(1).split(','):
                    tok = part.strip().split(' as ')[-1].strip()
                    if tok:
                        names.add(tok)
    for man in (SKILL / 'assets' / 'lecture-template' / 'manifests').glob('*.json'):
        try:
            data = json.loads(man.read_text(encoding='utf-8'))
        except Exception:
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, str) and re.fullmatch(r'[A-Z][A-Za-z0-9]{1,30}', node):
                names.add(node)
    return names


def check_doc_identifiers() -> list[str]:
    defined = doc_defined_names()
    problems: list[str] = []
    docs = [SKILL / 'SKILL.md', SKILL / 'README.md', SKILL / 'README.en.md']
    docs += [p for p in (SKILL / 'references').glob('*.md')]
    docs += [p for p in (SKILL / 'agents').glob('*.yaml')]
    for doc in docs:
        if not doc.is_file() or doc.name in DOC_IDENT_SKIP_FILES:
            continue
        text = doc.read_text(encoding='utf-8', errors='ignore')
        bad = sorted({
            m.group(1) for m in re.finditer(r'`([A-Z][A-Za-z0-9_$]{2,})`', text)
            if m.group(1) not in defined and m.group(1) not in DOC_IDENT_WHITELIST
        })
        if bad:
            problems.append(
                f"doc names not found in source: {doc.relative_to(SKILL)} -> {', '.join(bad[:8])}"
                + (f" (+{len(bad) - 8})" if len(bad) > 8 else "")
            )
    return problems


# ---------------------------------------------------------------------------
# 枚举集合双真源交叉校验：模板源码 vs validate-composition.py 的判据集合。
# 两侧各自独立存在（脚本读不到工程运行副本，也不该去读），漂移只会红在这一条上。
# ---------------------------------------------------------------------------
def check_enum_dual_source() -> list[str]:
    problems: list[str] = []
    vc = (SKILL / 'scripts' / 'validate-composition.py').read_text(encoding='utf-8', errors='ignore')
    for name, ts_rel in (('TRANSITIONS', 'assets/lecture-template/src/insert.tsx'),
                         ('SKELETONS', 'assets/lecture-template/src/skeletons.tsx')):
        ts = (SKILL / ts_rel).read_text(encoding='utf-8', errors='ignore')
        m_ts = re.search(rf'export const {name} = \[([^\]]*)\] as const', ts)
        m_py = re.search(rf'^{name} = \{{([^}}]*)\}}', vc, re.M)
        if not (m_ts and m_py):
            problems.append(f"enum dual-source parse failed: {name} in {ts_rel} or scripts/validate-composition.py")
            continue
        ts_set = set(re.findall(r"'([^']+)'", m_ts.group(1)))
        py_set = set(re.findall(r'"([^"]+)"', m_py.group(1)))
        if ts_set != py_set:
            problems.append(f"{name} set drift: {ts_rel} {sorted(ts_set)} vs scripts/validate-composition.py {sorted(py_set)}")
    return problems


# ---------------------------------------------------------------------------
# 画布参数集双真源交叉校验：validate-visual-plan.py 的 CANVAS_MODES（python 判据侧）
# vs 模板 src/theme/canvas.ts 的 MODES（TS 运行时真源）。check_enum_dual_source 比的是
# 字符串集合；这里比的是**数值对集合**——按 compW（输出画布宽，两共同有的锁键）配对，
# 逐字段比 design 宽高 / 字幕安全宽 / 边距 / 底距。任一侧改数值而另一侧忘跟 → 红。
# ---------------------------------------------------------------------------
CANVAS_NUMERIC_FIELDS = (  # (validate-visual-plan.py 键, canvas.ts 键)
    ('design_width', 'designW'),
    ('design_height', 'designH'),
    ('subtitle_safe_width', 'safe'),
    ('subtitle_margin', 'subMar'),
    ('subtitle_bottom', 'subBottom'),
)


def check_canvas_mode_dual_source() -> list[str]:
    problems: list[str] = []
    vp = (SKILL / 'scripts' / 'validate-visual-plan.py').read_text(encoding='utf-8', errors='ignore')
    ct = (SKILL / 'assets' / 'lecture-template' / 'src' / 'theme' / 'canvas.ts').read_text(encoding='utf-8', errors='ignore')
    # py 侧：`    2560: {"label": "16:9", "design_width": 1920, ...},`
    py: dict[int, dict[str, int]] = {}
    for m in re.finditer(r'^\s*(\d+):\s*\{([^\n]*)\},?\s*$', vp, re.M):
        body = m.group(2)
        nums = {k: int(v) for k, v in re.findall(r'"(\w+)":\s*(\d+)', body)}
        if 'design_width' in nums:
            py[int(m.group(1))] = nums
    # ts 侧：`  '16:9': {compW: 2560, compH: 1440, designW: 1920, ...},`
    ts: dict[int, dict[str, int]] = {}
    for m in re.finditer(r"'([^']+)':\s*\{([^}]*)\}", ct):
        nums = {k: int(v) for k, v in re.findall(r'\b(\w+):\s*(\d+)\b', m.group(2))}
        if 'compW' in nums:
            ts[nums['compW']] = nums
    if not py or not ts:
        problems.append('canvas dual-source parse failed: CANVAS_MODES in scripts/validate-visual-plan.py '
                        'or MODES in assets/lecture-template/src/theme/canvas.ts')
        return problems
    if set(py) != set(ts):
        problems.append(f"canvas mode set drift: validate-visual-plan.py {sorted(py)} vs canvas.ts {sorted(ts)}")
        return problems
    for width in sorted(py):
        for py_key, ts_key in CANVAS_NUMERIC_FIELDS:
            if py_key not in py[width] or ts_key not in ts[width]:
                problems.append(f"canvas dual-source parse failed: compW {width} missing {py_key}/{ts_key}")
                continue
            if py[width][py_key] != ts[width][ts_key]:
                problems.append(
                    f"canvas mode numeric drift: compW {width} {py_key}={py[width][py_key]} vs "
                    f"{ts_key}={ts[width][ts_key]} (scripts/validate-visual-plan.py vs src/theme/canvas.ts)")
    return problems


def main() -> None:
    problems: list[str] = []
    text_files = [
        p for p in SKILL.rglob('*')
        if reusable_file(p) and p.suffix.lower() in TEXT_SUFFIXES and not p.name.startswith('validate-')
    ]
    joined = '\n'.join(p.read_text(encoding='utf-8', errors='ignore') for p in text_files)
    for token in ('from PIL', 'import PIL', 'Pillow', 'build-caption-timing.py', 'aesthetic-candidate-project',
                  'candidate-awaiting-render-approval', 'new-aesthetic-candidate.sh',
                  'validate-aesthetic-candidate.py', 'locked-style-contract-v7-candidate.json',
                  'warm-ivory-remotion-2k30-v8-performance'):
        if token in joined:
            problems.append(f"obsolete token remains: {token}")

    for forbidden_path in (
        SKILL / 'assets' / 'aesthetic-candidate-project',
        SKILL / 'references' / 'locked-style-contract-v7-candidate.json',
        SKILL / 'scripts' / 'new-aesthetic-candidate.sh',
        SKILL / 'scripts' / 'validate-aesthetic-candidate.py',
    ):
        if forbidden_path.exists():
            problems.append(f"obsolete dual-track path remains: {forbidden_path.relative_to(SKILL)}")

    if (SKILL / 'CANDIDATE-VALIDATION.md').exists():
        problems.append('one-run environment validation report remains inside the reusable skill')

    for generated_dir in ('node_modules', '.tools', '.cache', 'renders'):
        leaked = [path for path in SKILL.rglob(generated_dir) if path.is_dir()]
        if leaked:
            problems.append(f"generated dependency/cache directory leaked into source: {leaked[0].relative_to(SKILL)}")

    required_cross_platform = (
        SKILL / 'scripts' / 'notebook-video.mjs',
        SKILL / 'scripts' / 'notebook-video.cmd',
        SKILL / 'scripts' / 'new-project.sh',
        SKILL / 'scripts' / 'new-project.cmd',
        SKILL / 'scripts' / 'prepare-browser.sh',
        SKILL / 'scripts' / 'prepare-browser.cmd',
        SKILL / 'scripts' / 'package-project.py',
        SKILL / 'DEPENDENCIES.md',
        SKILL / 'references' / 'cross-platform-compatibility.md',
        SKILL / 'references' / 'windows-compatibility.md',
        SKILL / 'references' / 'visual-director.md',
        SKILL / 'scripts' / 'validate-visual-plan.py',
    )
    for required in required_cross_platform:
        if not required.is_file():
            problems.append(f"missing cross-platform entry: {required.relative_to(SKILL)}")

    # Theme pack integrity: four locked skins plus the engine contract and docs.
    theme_dir = SKILL / 'assets' / 'lecture-template' / 'src' / 'theme'
    for theme_file in ('types.ts', 'canvas.ts', 'paper.tsx', 'cel.tsx', 'sticker.tsx', 'flat.tsx', 'active.ts'):
        if not (theme_dir / theme_file).is_file():
            problems.append(f"missing theme pack file: assets/lecture-template/src/theme/{theme_file}")
    for theme_doc in ('theme-system.md', 'theme-cel.md', 'theme-sticker.md', 'theme-flat.md'):
        if not (SKILL / 'references' / theme_doc).is_file():
            problems.append(f"missing theme contract doc: references/{theme_doc}")
    if theme_dir.is_dir():
        active = (theme_dir / 'active.ts').read_text(encoding='utf-8', errors='ignore')
        if "from './paper'" not in active:
            problems.append("theme switch active.ts must ship defaulting to './paper'")
        for theme_id in ('cel', 'sticker', 'flat'):
            theme_src = (theme_dir / f'{theme_id}.tsx').read_text(encoding='utf-8', errors='ignore')
            if not re.search(r"useCanvas\(\)", theme_src) and theme_id != 'flat':
                problems.append(f"theme {theme_id}.tsx must anchor decoration via useCanvas()")

    with tempfile.TemporaryDirectory(prefix='notebook-video-package-test-') as temp:
        root = Path(temp)
        project = root / 'project'
        (project / 'src').mkdir(parents=True)
        (project / 'renders').mkdir()
        (project / 'node_modules' / 'example').mkdir(parents=True)
        (project / 'src' / 'index.tsx').write_text('export {};\n', encoding='utf-8')
        (project / 'renders' / 'temporary.mp4').write_bytes(b'temporary render')
        (project / 'node_modules' / 'example' / 'index.js').write_text('module.exports = {};\n', encoding='utf-8')
        archive = root / 'project.zip'
        subprocess.run(
            [sys.executable, str(SKILL / 'scripts' / 'package-project.py'), str(project), str(archive)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        with zipfile.ZipFile(archive) as packaged:
            names = set(packaged.namelist())
        if 'src/index.tsx' not in names:
            problems.append('packager omitted editable source')
        if any(name.startswith(('renders/', 'node_modules/')) for name in names):
            problems.append('packager included renders or node_modules')

    active_docs = [SKILL / 'SKILL.md', SKILL / 'references' / 'subtitle-timing.md', SKILL / 'references' / 'remotion-architecture.md', SKILL / 'references' / 'official-skills-exemplar.md', SKILL / 'references' / 'narrative-hook.md', SKILL / 'references' / 'visual-director.md']
    for doc in active_docs:
        text = doc.read_text(encoding='utf-8')
        for obsolete_command in ('python3 scripts/', 'bash "$SKILL_DIR/scripts/', 'scripts/new-project.sh`'):
            if obsolete_command in text:
                problems.append(f"platform-specific command remains in {doc.relative_to(SKILL)}: {obsolete_command}")

    for p in SKILL.rglob('*.md'):
        if not reusable_file(p):
            continue
        text = p.read_text(encoding='utf-8')
        for match in re.finditer(r'\[[^\]]+\]\(([^)]+)\)', text):
            link = match.group(1).split('#')[0]
            if not link or '://' in link or link.startswith('mailto:'):
                continue
            if not (p.parent / link).resolve().exists():
                problems.append(f"broken link: {p.relative_to(SKILL)} -> {link}")

    problems.extend(check_doc_identifiers())
    problems.extend(check_enum_dual_source())
    problems.extend(check_canvas_mode_dual_source())

    if problems:
        for problem in problems:
            print(f"CONSISTENCY ERROR: {problem}", file=sys.stderr)
        raise SystemExit(len(problems))

    subprocess.run([sys.executable, str(SKILL / 'scripts' / 'validate-official-example.py')], check=True)

    lecture = SKILL / 'assets' / 'lecture-template'
    lecture_cues = lecture / 'manifests' / 'caption-cues.json'
    lecture_src_cues = lecture / 'src' / 'caption-cues.json'
    if hashlib.sha256(lecture_cues.read_bytes()).digest() != hashlib.sha256(lecture_src_cues.read_bytes()).digest():
        raise SystemExit("lecture-template caption-cues mismatch between manifests/ and src/")

    subprocess.run([sys.executable, str(SKILL / 'scripts' / 'validate-layering.py'), str(lecture / 'manifests' / 'asset-manifest.json')], check=True)
    subprocess.run([sys.executable, str(SKILL / 'scripts' / 'validate-visual-plan.py'), str(lecture)], check=True)
    subprocess.run([sys.executable, str(SKILL / 'scripts' / 'validate-caption-sync.py'), str(lecture / 'audio' / 'narration.mp3.json'), str(lecture_cues)], check=True)
    subprocess.run([sys.executable, str(SKILL / 'scripts' / 'validate-semantic-breaks.py'), str(lecture_cues), str(lecture / 'manifests' / 'protected-caption-phrases.txt')], check=True)

    if "--json" in sys.argv:
        print(json.dumps({
            "status": "pass",
            "read_only": True,
            "problems_count": len(problems),
            "templates_validated": ["example-project", "lecture-template"],
        }, indent=2))
    else:
        print('Skill-wide consistency validation passed: both templates valid, single official v9 visual-director track, no obsolete renderer residue, stale render inputs or contract mismatch')


if __name__ == '__main__':
    main()
