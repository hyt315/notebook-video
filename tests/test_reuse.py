"""REUSE.toml 与运行期素材登记必须一致（开发期检查，不进发布包）。

运行期仍读各自的登记：背景库 manifests/backgrounds.json、音效 public/sfx/sfx-manifest.json、
纸纹 public/craft/craft-manifest.json。REUSE.toml 是给 `reuse lint` 看的同一份事实；两边说法不一样
就是有一边写错了。这里不依赖 `reuse` 工具（GPL-3.0，只在 CI 临时安装），按 REUSE 规范自己解析：
`*` 不跨目录、`**` 跨目录；同一文件命中多条时，文件里靠后的 override 生效，否则用 aggregate 默认。
"""
import json
import re
import subprocess
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10：技能本身只要 3.10，这条开发期检查在 3.11+ 跑
    tomllib = None

ROOT = Path(__file__).resolve().parents[1]
TPL = "assets/lecture-template/"
PD = "LicenseRef-PublicDomain"


def _rx(glob: str) -> re.Pattern:
    out, i = "", 0
    while i < len(glob):
        if glob.startswith("**", i):
            out, i = out + ".*", i + 2
        elif glob[i] == "*":
            out, i = out + "[^/]*", i + 1
        else:
            out, i = out + re.escape(glob[i]), i + 1
    return re.compile(out + r"\Z")


@unittest.skipIf(tomllib is None, "需要 Python 3.11+ 的 tomllib")
class ReuseMatchesRegistries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        doc = tomllib.loads((ROOT / "REUSE.toml").read_text(encoding="utf-8"))
        cls.ann = []
        for a in doc["annotations"]:
            paths = a["path"] if isinstance(a["path"], list) else [a["path"]]
            cls.ann.append(([_rx(p) for p in paths], a.get("precedence", "closest"), a["SPDX-License-Identifier"],
                            a["SPDX-FileCopyrightText"]))

    def resolve(self, rel: str, explicit_only=False):
        hit = None
        for rxs, prec, lic, cr in self.ann:
            if any(r.match(rel) for r in rxs) and (prec == "override" or not explicit_only):
                if prec == "override" or hit is None:
                    hit = (lic, cr)
        return hit

    def test_backgrounds_registry(self):
        bgs = json.loads((ROOT / TPL / "manifests/backgrounds.json").read_text(encoding="utf-8"))["backgrounds"]
        self.assertGreater(len(bgs), 40)
        for b in bgs:
            want = PD if b["license"] == "PD" else b["license"]
            got = self.resolve(TPL + b["file"], explicit_only=True)
            self.assertIsNotNone(got, f"{b['file']} 没在 REUSE.toml 里登记")
            self.assertEqual(got[0], want, b["file"])

    def test_sfx_registry(self):
        man = json.loads((ROOT / TPL / "public/sfx/sfx-manifest.json").read_text(encoding="utf-8"))
        rows = []
        for e in man["events"]:
            rows.append(e)
            rows.extend(e.get("variants", []))
        self.assertGreaterEqual(len(rows), 12)
        for r in rows:
            got = self.resolve(TPL + "public/" + r["file"], explicit_only=True)
            self.assertIsNotNone(got, r["file"])
            self.assertEqual(got[0], r["license"].split()[0], r["file"])
            kenney = "Kenney" in r["license"] or "Kenney" in json.dumps(r.get("source", {}))
            self.assertEqual(kenney, "Kenney" in got[1], f"{r['file']} 的版权方与登记不一致")

    def test_craft_tiles(self):
        man = json.loads((ROOT / TPL / "public/craft/craft-manifest.json").read_text(encoding="utf-8"))
        for name in man["tiles"]:
            self.assertEqual(self.resolve(TPL + "public/craft/" + name, explicit_only=True)[0], "Apache-2.0")

    def test_every_tracked_asset_is_explicit(self):
        """public/ 与 assets/fonts 下每个二进制素材都要有一条 override 登记，不能只靠默认的 Apache-2.0 兜底。"""
        r = subprocess.run(["git", "ls-files", TPL + "public", "assets/fonts"], cwd=ROOT,
                           capture_output=True, text=True)
        files = [f for f in r.stdout.split() if re.search(r"\.(jpg|png|webp|ogg|mp3|wav|woff2?|ttf|otf)$", f)]
        if not files:  # 不在 git 工作树里（如解包后的发布目录）：按磁盘找
            files = [p.relative_to(ROOT).as_posix() for d in (TPL + "public", "assets/fonts") for p in (ROOT / d).rglob("*")
                     if p.is_file() and "node_modules" not in p.parts
                     and re.search(r"\.(jpg|png|webp|ogg|mp3|wav|woff2?|ttf|otf)$", p.name)]
        self.assertGreater(len(files), 60)
        missing = [f for f in files if self.resolve(f, explicit_only=True) is None]
        self.assertEqual(missing, [], "新素材要在 REUSE.toml 里写来源与许可")

    def test_clash_display_is_not_ofl(self):
        for w in ("Bold", "Medium", "Semibold"):
            self.assertEqual(self.resolve(f"{TPL}public/fonts/ClashDisplay-{w}.woff2")[0], "LicenseRef-ITF-FFL")

    def test_license_texts_match_usage(self):
        used = {lic for _, _, lic, _ in self.ann}
        have = {p.stem for p in (ROOT / "LICENSES").glob("*.txt")}
        self.assertEqual(used, have)

    def test_glob_semantics(self):
        self.assertTrue(_rx("a/*.webp").match("a/x.webp"))
        self.assertFalse(_rx("a/*.webp").match("a/b/x.webp"))
        self.assertTrue(_rx("**").match("a/b/c"))


if __name__ == "__main__":
    unittest.main()
