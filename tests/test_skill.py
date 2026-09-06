#!/usr/bin/env python3
"""Standard regression test entry point for notebook-video."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "selftest.py")])
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
