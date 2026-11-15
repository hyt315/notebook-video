#!/usr/bin/env python3
"""检查仓库内所有相对链接（含 #锚点）与 .py/.mjs/.cjs/.json/.md/.yaml 里出现的 references/ 路径是否可解析。
用法：python3 scripts/dev/check-links.py .   退出码 = 问题数。.ts/.tsx 的注释单独列出（第 1 批不改 .ts/.tsx）。"""
import re, sys, os, unicodedata
from pathlib import Path
ROOT = Path(sys.argv[1]).resolve()
SKIP = {'.git', 'node_modules', 'history'}
FENCE = re.compile(r'^\s*(```|~~~)')
def slug(h):
    h = re.sub(r'<[^>]+>', '', h).strip().lower()
    h = re.sub(r'[`*_~\[\]()]', '', h) if False else h
    out = []
    for ch in h:
        if ch.isalnum() or ch in '-_' or unicodedata.category(ch).startswith('L') or unicodedata.category(ch) == 'Mn':
            out.append(ch)
        elif ch == ' ':
            out.append('-')
    return ''.join(out)
anchors = {}
def get_anchors(p):
    if p in anchors: return anchors[p]
    s, seen, code = set(), {}, False
    for line in p.read_text(encoding='utf-8', errors='ignore').splitlines():
        if FENCE.match(line): code = not code; continue
        if code: continue
        for m in re.finditer(r'<a\s+(?:id|name)="([^"]+)"', line): s.add(m.group(1))
        m = re.match(r'^#{1,6}\s+(.*?)\s*#*\s*$', line)
        if m:
            b = slug(m.group(1)); n = seen.get(b, 0); seen[b] = n + 1
            s.add(b if n == 0 else f'{b}-{n}')
    anchors[p] = s; return s
problems, tsx = [], []
files = [p for p in ROOT.rglob('*') if p.is_file() and not (set(p.relative_to(ROOT).parts) & SKIP)]
LINK = re.compile(r'\]\(([^)\s]+)\)')
PATH = re.compile(r'(?<![\w/.-])((?:\.\./)*references/[\w./-]+?\.(?:md|json))(#[\w\-\u4e00-\u9fff%]+)?')
for p in files:
    rel = p.relative_to(ROOT).as_posix()
    if p.suffix not in ('.md', '.py', '.mjs', '.cjs', '.json', '.yaml', '.yml', '.ts', '.tsx', '.txt'): continue
    t = p.read_text(encoding='utf-8', errors='ignore')
    if rel == 'CHANGELOG.md': continue
    if p.suffix == '.md':
        for m in LINK.finditer(t):
            tgt = m.group(1)
            if '://' in tgt or tgt.startswith('mailto:'): continue
            path, _, a = tgt.partition('#')
            dest = (p.parent / path).resolve() if path else p
            if not dest.exists(): problems.append(f'{rel}: broken link {tgt}'); continue
            if a and dest.suffix == '.md' and a not in get_anchors(dest):
                problems.append(f'{rel}: missing anchor {tgt}')
    if rel in ('MAINTAINING.md', 'references/MOVED.md'): continue   # 新旧对照表本身
    for m in PATH.finditer(t):
        path, a = m.group(1), m.group(2)
        cands = [(ROOT / path.lstrip('./')).resolve(), (p.parent / path).resolve()]
        dest = next((c for c in cands if c.exists()), None)
        bad = None
        if dest is None: bad = f'path {path}'
        elif a and dest.suffix == '.md' and a[1:] not in get_anchors(dest): bad = f'anchor {path}{a}'
        if bad:
            (tsx if p.suffix in ('.ts', '.tsx') else problems).append(f'{rel}: {bad}')
print('\n'.join(problems) or 'OK: no broken links / reference paths')
if tsx:
    print(f'\n[.ts/.tsx 注释里的旧路径：{len(tsx)} 处，第 1 批不改 .ts/.tsx，见 references/MOVED.md]')
    print('\n'.join(tsx))
sys.exit(len(problems))
