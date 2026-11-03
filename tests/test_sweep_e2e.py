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



def gray_stats(path: Path) -> tuple[int, int, float]:
    """把图解成灰度字节流，返回 (min, max, mean)。不用 numpy/PIL——测试依赖越少越好。"""
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, check=True).stdout
    if not raw:
        raise AssertionError(f"{path} 解不出像素")
    lo, hi, total = min(raw), max(raw), sum(raw)
    return lo, hi, total / len(raw)


class FixedFrameSmoke(unittest.TestCase):
    """P1-15：固定帧冒烟 —— 每镜末帧都必须真渲出来，且不是一块死板的单色。

    为什么不是"渲一张看看"：3.6.2 的第二次事故是 `case 'node'` 里的 CSS 写成了非法的
    `inset: 0, border: ..., border: ...`，前几镜照常出图、第 566 帧整片崩掉。
    `--stills` 只截前几镜，front matter 全绿。这条测试把**每一镜的末帧**都渲一遍：
    崩在中途的 React 错误、空白图层、全透明滤镜，都在这里现形。
    """

    def test_every_shot_tail_renders_a_real_frame(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        project = Path(tmp.name) / "proj"
        shutil.copytree(TPL, project,
                        ignore=shutil.ignore_patterns("node_modules", "renders", "build-test", "*.log"))
        if not link_node_modules(DEPS, project / "node_modules"):
            self.skipTest("无法把模板 node_modules 链进临时工程（junction/symlink 不可用）")
        duration = int(json.loads((TPL / "manifests" / "shots.json").read_text(encoding="utf-8"))["duration"])
        audio = project / "audio" / "narration.mp3"
        audio.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                        "-i", "anullsrc=r=48000:cl=mono", "-t", f"{duration / 30:.3f}", "-q:a", "9", str(audio)],
                       check=True, timeout=120)
        subprocess.run([NODE, str(CLI), "sync", str(project)], check=True,
                       capture_output=True, text=True, timeout=180)

        # 每镜的真帧号在 resolve-shots 的产物里（sync 会跑它）；模板自带的 shots.json 只有 id 与转场。
        resolved = json.loads((project / "manifests" / "shots.resolved.json").read_text(encoding="utf-8"))["shots"]
        out_dir = Path(tmp.name) / "frames"
        out_dir.mkdir()
        for shot in resolved:
            frame = int(shot["to"]) - 1          # 末帧：退场 / 转场 / 收束都在这一段
            out = out_dir / f"{shot['id']}.jpg"
            r = subprocess.run([NODE, str(CLI), "poster", str(project), str(out),
                                f"--frame={frame}", "--scale=0.25"],
                               capture_output=True, text=True, timeout=300)
            self.assertEqual(r.returncode, 0,
                             f"{shot['id']} 第 {frame} 帧渲染失败：\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
            self.assertTrue(out.is_file() and out.stat().st_size > 4000,
                            f"{shot['id']} 第 {frame} 帧出图太小（{out.stat().st_size if out.is_file() else 0} B）——空白？")
            lo, hi, mean = gray_stats(out)
            self.assertGreaterEqual(hi - lo, 24,
                                    f"{shot['id']} 第 {frame} 帧几乎是单色（{lo}–{hi}，均值 {mean:.0f}）——没画东西")
            self.assertLess(mean, 250, f"{shot['id']} 第 {frame} 帧几乎全白")
            self.assertGreater(mean, 8, f"{shot['id']} 第 {frame} 帧几乎全黑")



class HandmadeSkinSmoke(unittest.TestCase):
    """手作皮肤（journal）必须能渲出来——缺 NotoSerifSC 时不是"字体回退"，是第 0 帧 NetworkError。

    实测（视觉矩阵）：模板副本直接渲 journal，四镜全部 failed、`sheet: null`，
    stderr 只有 `NetworkError: A network error occurred`，一个字不提字体。
    `ensureProjectFonts` 当时只补 LXGW，漏了 serif。这条钉住补齐逻辑。
    """

    def test_journal_renders_without_manual_font_setup(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        project = Path(tmp.name) / "proj"
        shutil.copytree(TPL, project,
                        ignore=shutil.ignore_patterns("node_modules", "renders", "build-test", "*.log"))
        if not link_node_modules(DEPS, project / "node_modules"):
            self.skipTest("无法把模板 node_modules 链进临时工程（junction/symlink 不可用）")
        # 故意先删掉 serif（模板本来也没有，但万一有就复现不了）
        (project / "public" / "NotoSerifSC-Bold.otf").unlink(missing_ok=True)
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "set-skin.py"), str(project), "journal"],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        duration = int(json.loads((TPL / "manifests" / "shots.json").read_text(encoding="utf-8"))["duration"])
        audio = project / "audio" / "narration.mp3"
        audio.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                        "-i", "anullsrc=r=48000:cl=mono", "-t", f"{duration / 30:.3f}", "-q:a", "9", str(audio)],
                       check=True, timeout=120)
        subprocess.run([NODE, str(CLI), "sync", str(project)], check=True,
                       capture_output=True, text=True, timeout=180)
        out = Path(tmp.name) / "journal.jpg"
        r = subprocess.run([NODE, str(CLI), "poster", str(project), str(out), "--frame=60", "--scale=0.25"],
                           capture_output=True, text=True, timeout=300)
        self.assertEqual(r.returncode, 0, f"journal 渲染失败：\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
        self.assertTrue(out.is_file() and out.stat().st_size > 4000, "journal 出图为空")
        self.assertTrue((project / "public" / "NotoSerifSC-Bold.otf").is_file(),
                        "渲染前必须把 NotoSerifSC 补进工程 public/")


if __name__ == "__main__":
    unittest.main()
