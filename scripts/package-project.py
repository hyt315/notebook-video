#!/usr/bin/env python3
"""Package editable source without credentials, caches or linked external files."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

EXCLUDED_DIRS = {"node_modules", ".tools", ".git", ".cache", "__pycache__", "renders"}
SECRET_NAMES = {".env", "tts.env", ".npmrc", ".pypirc", "credentials.json", "id_rsa", "id_ed25519"}


def excluded(rel: Path, active_segments: set[str] | None = None) -> bool:
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return True
    name = rel.name.lower()
    if name in {".env.example", ".env.sample", "tts.env.example"}:
        return False
    return (name in SECRET_NAMES or name.startswith(".env.")
            or name.endswith((".env", ".pem", ".key", ".p12", ".pfx", ".pyc", ".log", ".zip"))
            or (rel.parts[0] == "audio" and rel.as_posix() not in (active_segments or set()) and (name.startswith("seg") or name in {
                "gap.wav", "concat.txt", "concat-matched.txt", "narration.wav", "narration-matched.wav"})))


def package(project: Path, output: Path) -> None:
    if not project.is_dir():
        raise ValueError(f"Project directory does not exist: {project}")
    if output.suffix.lower() != ".zip":
        raise ValueError("Output must have a .zip extension")
    active_segments = set()
    provenance = project / 'manifests/tts-segments.json'
    if provenance.is_file():
        entries = json.loads(provenance.read_text(encoding='utf-8')).get('segments', [])
        for entry in entries:
            rel = Path(entry['path'])
            source = project / rel
            if rel.is_absolute() or not source.resolve().is_relative_to(project / 'audio') or source.is_symlink() or not source.is_file():
                raise ValueError('Active audio segment is missing or outside the project')
            if hashlib.sha256(source.read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError('Active audio segment hash mismatch')
            active_segments.add(rel.as_posix())
    else:
        legacy = {}
        for source in (project / 'audio').glob('seg*.wav'):
            match = re.fullmatch(r'seg([1-9][0-9]*)-(?!matched)[^.]+\.wav', source.name)
            if match and 'matched' not in source.name:
                legacy.setdefault(int(match[1]), []).append(source)
        if legacy:
            if set(legacy) != set(range(1, len(legacy) + 1)) or any(len(paths) != 1 for paths in legacy.values()):
                raise ValueError('Ambiguous legacy TTS cache: publish tts-segments.json before packaging')
            for paths in legacy.values():
                source = paths[0]
                if source.is_symlink():
                    raise ValueError('Active audio segment must not be a symlink')
                active_segments.add(source.relative_to(project).as_posix())
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".notebook-package-", suffix=".zip", dir=output.parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for directory, dirs, files in os.walk(project, followlinks=False):
                parent = Path(directory)
                dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS and not (parent / d).is_symlink())
                for name in sorted(files):
                    source = parent / name
                    rel = source.relative_to(project)
                    if source.is_symlink() or source.resolve() in {output, Path(temporary)} or excluded(rel, active_segments):
                        continue
                    if source.is_file():
                        archive.write(source, rel.as_posix())
        os.replace(temporary, output)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: package-project.py PROJECT_DIRECTORY OUTPUT_ZIP")
    project, output = (Path(arg).resolve() for arg in sys.argv[1:])
    package(project, output)
    print(f"Packaged editable Remotion project: {output}")


if __name__ == "__main__":
    main()
