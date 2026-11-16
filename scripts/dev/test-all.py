#!/usr/bin/env python3
"""test-all.py — 一条命令跑完开发期全部检查（维护者用，不进包；不渲染）。

    python3 scripts/dev/test-all.py                 # 全部
    python3 scripts/dev/test-all.py --list          # 列出步骤名
    python3 scripts/dev/test-all.py unittest selftest   # 只跑这几步（按名字）
    python3 scripts/dev/test-all.py --skip negative

步骤：unittest（tests/ 全部单测）→ collection（每个测试文件真的收集到用例）→ selftest →
negative（负向抽查，每道门禁喂坏输入必须拦）→ validate-skill → links（链接 / 锚点）→
reuse（`reuse lint`，没装就 SKIP）→ tsc（设了 NV_E2E_NODE_MODULES 才跑：模板副本里软链依赖跑
`tsc --noEmit`，再跑 tests/test_frame_types.py；否则 SKIP）。

单测步骤**不会**把 NV_E2E_NODE_MODULES 传下去：那个变量会打开 test_sweep_e2e 的渲染型用例。
要连渲染型 e2e 一起跑，加 --e2e。退出码：任何一步 FAIL 即 1。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TPL = ROOT / "assets" / "lecture-template"
PY = sys.executable


def sh(argv, env=None, cwd=ROOT):
    r = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8", **(env or {})})
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def no_e2e_env():
    env = {k: v for k, v in os.environ.items() if k != "NV_E2E_NODE_MODULES"}
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def step_unittest(e2e: bool):
    argv = [PY, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
    r = subprocess.run(argv, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=None if e2e else no_e2e_env())
    return r.returncode, r.stdout + r.stderr


def step_tsc():
    deps = os.environ.get("NV_E2E_NODE_MODULES")
    if not deps or not (Path(deps) / "typescript" / "bin" / "tsc").is_file():
        return None, "没设 NV_E2E_NODE_MODULES（指向装好的模板依赖）"
    with tempfile.TemporaryDirectory(prefix="nv-tsc-") as td:
        proj = Path(td) / "tpl"
        shutil.copytree(TPL, proj, ignore=shutil.ignore_patterns("node_modules", "renders"))
        (proj / "node_modules").symlink_to(Path(deps).resolve(), target_is_directory=True)
        rc, out = sh(["node", str(Path(deps) / "typescript" / "bin" / "tsc"), "--noEmit", "-p", "."], cwd=proj)
    if rc:
        return rc, out
    rc2, out2 = sh([PY, "-m", "unittest", "tests.test_frame_types"], env={"NV_E2E_NODE_MODULES": deps})
    return rc2, out + "tsc --noEmit: 0 错\n" + out2


def step_reuse():
    exe = shutil.which("reuse")
    if not exe:
        return None, "没装 reuse（pip install reuse==6.3.0，GPL-3.0，只做开发期检查）"
    return sh([exe, "lint"])


STEPS = {
    "unittest": None,  # 特殊：带 e2e 开关
    "collection": lambda: sh([PY, "scripts/dev/check-test-collection.py"]),
    "selftest": lambda: sh([PY, "scripts/selftest.py"]),
    "negative": lambda: sh([PY, "scripts/negative-gate-check.py"]),
    "validate-skill": lambda: sh(["node", "scripts/notebook-video.mjs", "validate-skill"]),
    "links": lambda: sh([PY, "scripts/dev/check-links.py", "."]),
    "reuse": step_reuse,
    "tsc": step_tsc,
}


def tail(out: str) -> str:
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    ran = [ln for ln in lines if ln.startswith("Ran ")]
    return ((ran[-1].split(" in ")[0] + " · ") if ran else "") + (lines[-1][:150] if lines else "")


def main(argv: list[str]) -> int:
    if "--list" in argv:
        print("\n".join(STEPS))
        return 0
    e2e = "--e2e" in argv
    skip = {argv[i + 1] for i, a in enumerate(argv) if a == "--skip" and i + 1 < len(argv)}
    names = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--skip")]
    unknown = [n for n in names + list(skip) if n not in STEPS]
    if unknown:
        print(f"不认识的步骤：{unknown}；可选：{', '.join(STEPS)}")
        return 2
    if (TPL / "node_modules").exists():
        print("⚠ 模板里有 node_modules：validate-skill 会判泄漏，单测会打开渲染型 e2e。跑完记得删，或改用 NV_E2E_NODE_MODULES。")
    failed = 0
    for name in STEPS:
        if (names and name not in names) or name in skip:
            continue
        t0 = time.time()
        rc, out = step_unittest(e2e) if name == "unittest" else STEPS[name]()
        verdict = "SKIP" if rc is None else ("PASS" if rc == 0 else "FAIL")
        failed += verdict == "FAIL"
        print(f"{verdict:<5} {name:<15} {time.time() - t0:6.1f}s  {tail(out)}", flush=True)
        if verdict == "FAIL":
            print("\n".join("      " + ln for ln in out.splitlines()[-25:]))
    print(f"结论：{'全部通过' if not failed else f'{failed} 步失败'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
