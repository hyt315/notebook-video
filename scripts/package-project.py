#!/usr/bin/env python3
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

EXCLUDED_DIRS = {"node_modules", ".tools", ".git", ".cache", "__pycache__", "renders"}


def excluded(rel: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return True
    name = rel.name
    if name.endswith((".pyc", ".log")):
        return True
    return False


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: package-project.py PROJECT_DIRECTORY OUTPUT_ZIP")
    project = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    if not project.is_dir():
        raise SystemExit(f"Project directory does not exist: {project}")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sorted(project.rglob("*")):
            rel = source.relative_to(project)
            if source.is_file() and not excluded(rel):
                archive.write(source, rel.as_posix())
    print(f"Packaged editable Remotion project: {output}")


if __name__ == "__main__":
    main()
