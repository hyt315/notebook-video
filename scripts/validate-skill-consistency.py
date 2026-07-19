#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
IGNORED_PARTS = {"node_modules", ".git", ".cache", ".tools", "renders", "__pycache__"}
TEXT_SUFFIXES = {'.md', '.py', '.sh', '.cmd', '.mjs', '.json', '.yaml', '.yml', '.tsx', '.cjs'}


def reusable_file(path: Path) -> bool:
    rel = path.relative_to(SKILL)
    return path.is_file() and not any(part in IGNORED_PARTS for part in rel.parts)


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

    for generated_dir in ('node_modules', '.tools', '.cache', 'renders', '__pycache__'):
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

    if problems:
        for problem in problems:
            print(f"CONSISTENCY ERROR: {problem}", file=sys.stderr)
        raise SystemExit(len(problems))

    subprocess.run([sys.executable, str(SKILL / 'scripts' / 'validate-official-example.py')], check=True)
    print('Skill-wide consistency validation passed: single official v9 visual-director track, no obsolete renderer residue, stale render inputs or contract mismatch')


if __name__ == '__main__':
    main()
