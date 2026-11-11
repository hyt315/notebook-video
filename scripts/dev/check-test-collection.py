#!/usr/bin/env python3
"""每个 tests/test_*.py 必须被 unittest 收集到 ≥1 条测试（3.5.4）。

事故：test_craft_paper.py（pytest 风格裸函数）和 test_skill.py（只有 main()）在
`unittest discover` 下一条都不跑，CI 却一直绿——"0 条"冒充了"全过"。
本脚本逐文件用 unittest 的加载器数用例（不执行），任何文件 0 条或导入失败即 rc=1。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests"


def _count(suite: unittest.TestSuite, broken: list[str]) -> int:
    n = 0
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            n += _count(item, broken)
        else:
            if type(item).__name__ in ("_FailedTest", "ModuleImportFailure"):
                broken.append(str(item))
            n += 1
    return n


def main() -> int:
    sys.path.insert(0, str(ROOT))
    loader = unittest.TestLoader()
    bad: list[str] = []
    total = 0
    files = sorted(TESTS.glob("test_*.py"))
    for f in files:
        broken: list[str] = []
        suite = loader.loadTestsFromName(f"tests.{f.stem}")
        n = _count(suite, broken)
        total += n
        if broken:
            bad.append(f"{f.name}: 导入/收集失败 {broken[:2]}")
        elif n == 0:
            bad.append(f"{f.name}: 收集到 0 条测试（pytest 风格裸函数 / 只有 main() 都不会被 unittest 运行）")
    if bad:
        print("FAIL 以下测试文件没有真实运行的用例：")
        for b in bad:
            print("  -", b)
        return 1
    print(f"OK {len(files)} 个测试文件，共收集 {total} 条用例，每个文件 ≥1 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
