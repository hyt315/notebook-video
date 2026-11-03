# 环境矩阵：这台机器能出什么片

`notebook-video capabilities` 把环境判成三档。三档不是"好/中/差"的评分，而是**用户会看到什么差别**。

| 判定 | 含义 | 用户会遇到的 |
|---|---|---|
| `full` 全能力 | 硬依赖齐、有带 WebGPU 的 Chromium、字体齐 | 卷页是真卷页；语义断句生效 |
| `degraded` 折页降级 | 能出片，但没找到带 WebGPU 的 Chromium | `pageturn` / `peel` 退成 CSS 折痕翻页；片照出，只是没有纸背弧面 |
| `unsupported` 不支持 | 缺 ffmpeg / ffprobe / Python / npm，或 Node < 20 | 连合成都做不了。每条缺项都打印出补它的命令 |

## 怎么自检

```bash
node scripts/notebook-video.mjs capabilities          # 人读
node scripts/notebook-video.mjs capabilities --json   # 给脚本用；unsupported 时退码 1
```

`--json` 的字段：`platform` / `node` / `level` / `blockers[]`（每项含 `fix`）/ `capabilities` /
`pageTurn` / `fonts` / `budoux` / `concurrency`。

## 已验证与未验证（别把下表当成"三平台都测过"）

| 平台 | 状态 | 依据 |
|---|---|---|
| Windows 11 x64 · Node 22 | **已实测**（2026-11-02） | `capabilities` → `full`；整片渲染链路此前完整跑通（约 3 分 25 秒）；2026-11-02 的 `tests/test_capabilities.py` 锁住判定逻辑 |
| macOS | **未实测** | 只做了代码路径审查：`findPython` 认 `python3`；`npmInvocation` 非 Windows 分支走 `npm`；字体下载走 `https` |
| Linux | **未实测** | CI 在 `ubuntu-latest` 上跑单测与门禁，但**不跑真实渲染**（无 GPU、无 Chromium 下载），所以只证明"脚本能跑"，不证明"片能出" |
| 低配机（4 核 / 8 GB） | **未实测** | `suggestedConcurrency()` 会把它压到 2–3；但没有实测帧率与内存峰值 |

未实测的三行，谁有条件谁补：跑完 `capabilities` + 一次 `preview`，把 `level`、耗时、峰值内存记进上表。
在那之前，**本文件不承诺这三个平台的表现**。

## 已知的"能出片但不对"的陷阱

- **BudouX 未装**：语义断句会以 SKIPPED 形式跳过，rc 仍是 0。交付路径带 `--require-budoux`，
  这时会**失败**而不是静默跳过——这是刻意的：宁可拦住，也不要交出一份"看起来检查过"的字幕。
- **缺 NotoSerifSC**：手作皮肤（journal / papercut / archive）渲染时 Chrome 抛网络错误（报错里不写"字体"两个字），
  报错里不会提"缺字体"。`capabilities` 的 `fonts.serif` 就是提前看这个。
- **缺 ffmpeg**：`validate-video` 与音轨合成都不可用，但 `compose` 仍能跑完写出工程——
  于是"排版成功"容易被误当成"能出片"。
