"""sweep 端到端：模板工程每一镜都必须真的量到数（不是 0/8 那种"跑了但什么都没量"）。

为什么必须有这条（2026-10-30 实测）：sweep 在 Linux 上 0/8 镜量到，两处根因都不是"命令失败"——
`remotion still` 不转发组件 console、FillGate 把推近镜头整镜跳过。命令照样 rc=0、照样出一张
看着合理的接触表。单元测试（test_sweep.py）只钉采样帧，抓不到这一类。

这条测试真渲染：复制模板 → 软链 node_modules → 补静音旁白 → `sweep --json`。
没装依赖 / 没有 node / 没有 ffmpeg 时 skip，并写明原因（不冒充通过）。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "assets" / "lecture-template"
CLI = ROOT / "scripts" / "notebook-video.mjs"
NODE = shutil.which("node") or shutil.which("node.exe")
FFMPEG = shutil.which("ffmpeg")
NODE_MODULES = TPL / "node_modules"
# 开发机上模板依赖通常不放在仓库里（validate-skill 会把仓库内的 node_modules 判成泄漏）。
# 用这个环境变量指向一份装好的依赖目录，测试就能跑；没设且模板里也没有时 skip。
DEPS = Path(os.environ.get("NV_E2E_NODE_MODULES", "")) if os.environ.get("NV_E2E_NODE_MODULES") else NODE_MODULES


def link_node_modules(src: Path, dst: Path) -> bool:
    """把模板的 node_modules 链到临时工程：Windows 用 junction（不需要管理员），POSIX 用 symlink。"""
    try:
        if os.name == "nt":
            r = subprocess.run(
                f'cmd /c mklink /J "{dst}" "{src}"',
                capture_output=True, text=True, timeout=60,
            )
        else:
            os.symlink(src, dst, target_is_directory=True)
            r = None
        return dst.exists() and (r is None or r.returncode == 0)
    except OSError:
        return False


@unittest.skipUnless(NODE, "node 未安装：sweep 端到端需要 Node 20+")
@unittest.skipUnless(FFMPEG, "ffmpeg 未安装：需要它生成静音旁白占位")
@unittest.skipUnless(DEPS.is_dir(), "没有可用的 Remotion 依赖：在资产模板跑 npm ci，或设 NV_E2E_NODE_MODULES")
class SweepMeasuresEveryShot(unittest.TestCase):
    def test_template_sweep_measures_all_shots(self):
        shots_doc = json.loads((TPL / "manifests" / "shots.json").read_text(encoding="utf-8"))
        duration = int(shots_doc["duration"])
        shots = shots_doc["shots"]

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        project = Path(tmp.name) / "proj"
        shutil.copytree(
            TPL, project,
            ignore=shutil.ignore_patterns("node_modules", "renders", "build-test", "*.log"),
        )
        if not link_node_modules(DEPS, project / "node_modules"):
            self.skipTest("无法把模板 node_modules 链进临时工程（junction/symlink 不可用）")

        audio = project / "audio" / "narration.mp3"
        audio.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
             "-i", "anullsrc=r=48000:cl=mono", "-t", f"{duration / 30:.3f}", "-q:a", "9", str(audio)],
            check=True, timeout=120,
        )
        subprocess.run([NODE, str(CLI), "sync", str(project)], check=True, capture_output=True, text=True, timeout=180)

        r = subprocess.run(
            [NODE, str(CLI), "sweep", str(project), "--json", "--scale=0.35"],
            capture_output=True, text=True, timeout=900,
        )
        self.assertEqual(r.returncode, 0, f"sweep 失败：\n{r.stdout[-3000:]}\n{r.stderr[-2000:]}")
        try:
            doc = json.loads(r.stdout[r.stdout.index("{"):])
        except ValueError:
            self.fail(f"sweep --json 没有输出 JSON：\n{r.stdout[-3000:]}")

        rows = doc.get("rows") or []
        self.assertEqual(len(rows), len(shots),
                         f"只量到 {len(rows)}/{len(shots)} 镜：FillGate 的 console 没被转发，"
                         f"或推近镜头被整镜跳过（见 nbv-sweep-fix.patch 两处根因）")
        self.assertEqual(doc.get("missing"), [], f"有镜头没有测量数据：{doc.get('missing')}")
        self.assertEqual(doc.get("failed"), [], f"有镜头渲染失败：{doc.get('failed')}")
        for row in rows:
            self.assertIsInstance(row.get("cells"), int,
                                  f"{row.get('id')} 没有 coverage 数据：{row}")


if __name__ == "__main__":
    unittest.main()
