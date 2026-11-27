# SPDX-License-Identifier: Apache-2.0
"""Tests for cross-project dependency, browser, and font cache reuse."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DEPS_URL = "file:///" + quote(str((SCRIPTS / "deps-cache.mjs").resolve()).replace("\\", "/"), safe=":/")
BROWSER_URL = "file:///" + quote(str((SCRIPTS / "browser-exec.mjs").resolve()).replace("\\", "/"), safe=":/")


def _run_node(code: str, env_extra: dict[str, str] | None = None) -> dict:
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    r = subprocess.run(
        ["node", "--input-type=module", "-e", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    if r.returncode != 0:
        raise AssertionError(f"node exited {r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    return json.loads(r.stdout.strip().splitlines()[-1])


class DepsAndBrowserCacheTest(unittest.TestCase):
    def setUp(self):
        if not shutil.which("node"):
            self.skipTest("node not installed")

    def test_cache_dirs_honor_env_overrides(self):
        with tempfile.TemporaryDirectory() as td:
            res = _run_node(
                f"import {{userCacheRoot, sharedNpmCacheDir, sharedFontsDir}} from '{DEPS_URL}';"
                "console.log(JSON.stringify({root: userCacheRoot(), npm: sharedNpmCacheDir(), fonts: sharedFontsDir()}));",
                {"NOTEBOOK_VIDEO_CACHE_DIR": td, "NOTEBOOK_VIDEO_NPM_CACHE": str(Path(td) / "custom-npm")},
            )
            self.assertEqual(Path(res["root"]).resolve(), Path(td).resolve())
            self.assertEqual(Path(res["npm"]).resolve(), (Path(td) / "custom-npm").resolve())
            self.assertEqual(Path(res["fonts"]).resolve(), (Path(td) / "fonts").resolve())

    def test_shared_deps_install_once_and_reuse_across_projects(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cache_dir = root / "cache"
            lock_v1 = json.dumps({"name": "tpl", "lockfileVersion": 3, "packages": {"": {"version": "1.0.0"}}})
            lock_v2 = json.dumps({"name": "tpl", "lockfileVersion": 3, "packages": {"": {"version": "2.0.0"}}})
            pkg_json = json.dumps({"name": "tpl", "version": "1.0.0"})

            p1, p2, p3 = root / "proj1", root / "proj2", root / "proj3"
            for proj, lock in ((p1, lock_v1), (p2, lock_v1), (p3, lock_v2)):
                proj.mkdir(parents=True, exist_ok=True)
                (proj / "package.json").write_text(pkg_json, encoding="utf-8")
                (proj / "package-lock.json").write_text(lock, encoding="utf-8")

            script = f"""
            import fs from 'node:fs';
            import path from 'node:path';
            import {{ensureProjectNodeModules}} from '{DEPS_URL}';
            let npmCalls = 0;
            const runNpm = async (_args, {{cwd}}) => {{
              npmCalls += 1;
              const marker = path.join(cwd, 'node_modules', 'dummy', 'ok.txt');
              fs.mkdirSync(path.dirname(marker), {{recursive: true}});
              fs.writeFileSync(marker, path.basename(cwd));
            }};
            const verifyRel = path.join('dummy', 'ok.txt');
            const r1 = await ensureProjectNodeModules({json.dumps(str(p1))}, {{runNpm, verifyRel, log: () => {{}}}});
            const r2 = await ensureProjectNodeModules({json.dumps(str(p2))}, {{runNpm, verifyRel, log: () => {{}}}});
            const r3 = await ensureProjectNodeModules({json.dumps(str(p3))}, {{runNpm, verifyRel, log: () => {{}}}});
            const p1Has = fs.existsSync({json.dumps(str(p1 / 'node_modules' / 'dummy' / 'ok.txt'))});
            const p2Has = fs.existsSync({json.dumps(str(p2 / 'node_modules' / 'dummy' / 'ok.txt'))});
            const p3Has = fs.existsSync({json.dumps(str(p3 / 'node_modules' / 'dummy' / 'ok.txt'))});
            console.log(JSON.stringify({{npmCalls, r1, r2, r3, p1Has, p2Has, p3Has}}));
            """
            res = _run_node(script, {"NOTEBOOK_VIDEO_CACHE_DIR": str(cache_dir), "NOTEBOOK_VIDEO_SHARED_DEPS": "1"})
            self.assertEqual(res["npmCalls"], 2)  # once for lock_v1 (p1+p2 shared), once for lock_v2 (p3)
            self.assertEqual(res["r1"]["mode"], "installed-shared")
            self.assertEqual(res["r2"]["mode"], "linked")
            self.assertEqual(res["r3"]["mode"], "installed-shared")
            self.assertEqual(res["r1"]["lockHash"], res["r2"]["lockHash"])
            self.assertNotEqual(res["r1"]["lockHash"], res["r3"]["lockHash"])
            self.assertTrue(res["p1Has"] and res["p2Has"] and res["p3Has"])

            # Removing temp directory must safely unlink without touching shared deps target
            shutil.rmtree(p2)
            self.assertTrue(Path(res["r2"]["target"]).exists())

    def test_shared_deps_disabled_installs_locally(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            proj = root / "proj"
            proj.mkdir()
            (proj / "package.json").write_text('{"name":"x"}', encoding="utf-8")
            (proj / "package-lock.json").write_text('{"name":"x","lockfileVersion":3}', encoding="utf-8")
            script = f"""
            import fs from 'node:fs';
            import path from 'node:path';
            import {{ensureProjectNodeModules}} from '{DEPS_URL}';
            const runNpm = async (_args, {{cwd}}) => {{
              const m = path.join(cwd, 'node_modules', 'dummy', 'ok.txt');
              fs.mkdirSync(path.dirname(m), {{recursive: true}});
              fs.writeFileSync(m, 'local');
            }};
            const r = await ensureProjectNodeModules({json.dumps(str(proj))}, {{runNpm, verifyRel: path.join('dummy', 'ok.txt'), log: () => {{}}}});
            console.log(JSON.stringify(r));
            """
            res = _run_node(
                script,
                {"NOTEBOOK_VIDEO_CACHE_DIR": str(root / "cache"), "NOTEBOOK_VIDEO_SHARED_DEPS": "0"},
            )
            self.assertEqual(res["mode"], "local")
            self.assertEqual(Path(res["target"]).resolve(), (proj / "node_modules").resolve())

    def test_browser_discovery_scans_shared_and_playwright_caches(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cache_dir = root / "cache"
            if os.name == "nt":
                plat, exe = "win64", "chrome-headless-shell.exe"
                pw_plat = "chrome-headless-shell-win64"
            elif os.uname().sysname == "Darwin":
                plat, exe = ("mac-arm64" if os.uname().machine == "arm64" else "mac-x64"), "chrome-headless-shell"
                pw_plat = f"chrome-headless-shell-{plat}"
            else:
                plat, exe = "linux64", "chrome-headless-shell"
                pw_plat = "chrome-headless-shell-linux64"

            # 1) Found inside <cache>/deps/<hash>/node_modules/.remotion/chrome-headless-shell/<plat>/<exe>
            dep_exe = cache_dir / "deps" / "abcd1234" / "node_modules" / ".remotion" / "chrome-headless-shell" / plat / exe
            dep_exe.parent.mkdir(parents=True, exist_ok=True)
            dep_exe.write_text("stub", encoding="utf-8")

            env_clean = {
                "NOTEBOOK_VIDEO_CACHE_DIR": str(cache_dir),
                "LOCALAPPDATA": str(root / "empty-local"),
                "XDG_CACHE_HOME": str(root / "empty-xdg"),
                "USERPROFILE": str(root / "empty-home"),
                "HOME": str(root / "empty-home"),
                "REMOTION_BROWSER_EXECUTABLE": "",
                "REMOTION_CHROME_MODE": "",
            }
            res1 = _run_node(
                f"import {{resolveBrowserInfo}} from '{BROWSER_URL}';"
                f"console.log(JSON.stringify(resolveBrowserInfo(undefined, {{skillDir: {json.dumps(str(root))}}})));",
                env_clean,
            )
            self.assertEqual(Path(res1["executable"]).resolve(), dep_exe.resolve())
            self.assertIsNone(res1["chromeMode"])

            # 2) Playwright cache fallback when deps/ & remotion-browser/ are absent
            shutil.rmtree(cache_dir / "deps")
            pw_exe = root / "empty-local" / "ms-playwright" / "chromium_headless_shell-1181" / pw_plat / exe
            pw_xdg_exe = root / "empty-xdg" / "ms-playwright" / "chromium_headless_shell-1181" / pw_plat / exe
            pw_exe.parent.mkdir(parents=True, exist_ok=True)
            pw_exe.write_text("pw", encoding="utf-8")
            pw_xdg_exe.parent.mkdir(parents=True, exist_ok=True)
            pw_xdg_exe.write_text("pw", encoding="utf-8")
            res2 = _run_node(
                f"import {{resolveBrowserInfo}} from '{BROWSER_URL}';"
                f"console.log(JSON.stringify(resolveBrowserInfo(undefined, {{skillDir: {json.dumps(str(root))}}})));",
                env_clean,
            )
            self.assertTrue(res2["executable"] and Path(res2["executable"]).name == exe)
            self.assertIsNone(res2["chromeMode"])

            # 3) Explicit custom chrome binary sets --chrome-mode=chrome-for-testing automatically
            chrome_bin = root / ("chrome.exe" if os.name == "nt" else "google-chrome")
            chrome_bin.write_text("bin", encoding="utf-8")
            res3 = _run_node(
                f"import {{resolveBrowserInfo, browserArgs}} from '{BROWSER_URL}';"
                f"console.log(JSON.stringify({{info: resolveBrowserInfo(), args: browserArgs()}}));",
                {**env_clean, "REMOTION_BROWSER_EXECUTABLE": str(chrome_bin)},
            )
            self.assertEqual(res3["info"]["chromeMode"], "chrome-for-testing")
            self.assertIn("--chrome-mode=chrome-for-testing", res3["args"])

            # 4) Missing REMOTION_BROWSER_EXECUTABLE fails loudly instead of falling through
            bad_bin = root / "missing-chrome"
            r_bad = subprocess.run(
                ["node", "--input-type=module", "-e", f"import {{resolveBrowserInfo}} from '{BROWSER_URL}'; resolveBrowserInfo();"],
                capture_output=True, text=True, encoding="utf-8",
                env={**os.environ, **env_clean, "REMOTION_BROWSER_EXECUTABLE": str(bad_bin)},
            )
            self.assertNotEqual(r_bad.returncode, 0)
            self.assertIn("REMOTION_BROWSER_EXECUTABLE does not exist", r_bad.stderr)


if __name__ == "__main__":
    unittest.main()
