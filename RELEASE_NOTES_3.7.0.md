# notebook-video 3.7.0

> **3.2.0 之后的首个公开版本**，合并了 3.3.0–3.7.0 五个版本的改进（56 个提交）。
> 上一个公开版本是 3.2.0（`main` = `d8d03cb`）。

## 亮点

1. **真翻页转场**：手作皮肤的镜间转场是 WebGPU 卷页（`pageturn` / `peel`）——上一页整页卷走，有折痕高光、纸背透出墨迹。机器画不了会自动退回 `slide` / `drop` 并在报告里记 P1，成片照出。
   *Real page-turn transitions on hand-made skins (WebGPU). If the machine cannot draw them, the renderer falls back and records a P1 — a film always renders.*

2. **音效默认稀疏**：`sfxDensity` 缺省 `sparse`——每镜一记（换章的镜给章节声、其余给末拍，误区镜另留反转音）。演示片从 39 条候选 / 落地约 24 条每分钟降到 **9 条 / 11 条每分钟**。旁白由使用者后配，所以默认就该克制；想更热闹写 `"sfxDensity": "normal"`。
   *Sparse sound effects by default: one hit per shot. The demo drops from ~24 cues/min to 11. Set `"sfxDensity": "normal"` for the old density.*

3. **手作皮肤开箱即过门禁**：模板自带填好的导演层（`treatment.json` 带 GitHub 官方文档的逐字引文、一次真实的 Commons 搜索记录、招牌镜头真推 12.5%），新建 `journal` / `papercut` / `archive` 工程不再被 `validate-treatment` 以 P0 拦死。
   *A fresh hand-made project passes the director gate out of the box.*

4. **运镜与冷开有门禁**：`validate-treatment` 拿 treatment 写的 `move` / `framing` 对照镜头表，招牌镜头必须真推 ≥12%；`validate-opening` 管前 3 秒（第 0 帧有事件、首条字幕 ≤1 s、片名不当第一镜、前 3 秒 ≥3 拍、第一句不是泛问句），`--video` 还会读像素复核。
   *Camera and cold-open gates, including pixel-level checks on the rendered file.*

5. **按章换纸 + 分镜表自动生成**：`bgMode`（film / chapter / shot）手作皮肤默认每章一张；`storyboard.md` 由镜头表生成，手作皮肤渲染前需要一轮评审记录或显式 `--skip-review`。
   *`bgMode`, and a storyboard generated from the shot table with a review gate.*

## 升级注意

- **音效会变少**：默认稀疏。恢复 3.6.0 的「一拍一个」，在 `manifests/shots.json` 顶层写 `"sfxDensity": "normal"`。
- **交付版必须写 `--scale=1`**：`make-video --render` 缺省 `--scale=0.75`（出 1920×1080）。
- **手作皮肤背景改为每章一张**：要逐镜轮换写 `bgMode:"shot"`。
- **手作皮肤字幕整行出现**：`src/film.ts` 里 `export const CAPTION_REVEAL = 'type'` 恢复逐字。
- **手作皮肤 `--render` 没有评审记录会以 rc=3 停下**：补 `treatment.json` 的 `review.rounds`，或加 `--skip-review`。
- **兼容检查**：3.2.x（`d8d03cb`）的模板工程原样用 3.7.0 脚本跑构建期门禁，**无异常栈、无 P0**，只多出若干 P1（缺 `treatment.json`、镜长太整齐、骨架指纹重复、节拍间隔长、小字号）。详见 CHANGELOG「从 3.2.x / 3.6.x 升级」。

## 质量实测（演示片《细胞为什么叫细胞》）

| 项 | 实测 |
|---|---|
| 规格 | 2560×1440 / H.264 High / yuv420p / BT.709 / 30 fps / faststart / 49.100 s |
| 响度 | I = **−16.7 LUFS**（目标 −16 ±1）、Peak = **−1.4 dBFS**（≤ −1） |
| 构建期 + 成片门禁 | **15 条全部 P0=0**（含 `validate-opening --video` P0=0 P1=0、`validate-motion-gaps` 静止段 0） |
| 真翻页 | 开启（探针通过，6 个卷页窗口拼接） |
| 音效 | 9 条 / 11 条每分钟 |
| 字幕 | 整行出现；2560 版 OCR **SKIPPED**（见下） |

## 如实披露

- **独立评审两轮都没到 8 分线**：第 1 轮 P0=0 / P1=10，七项均分 **7.1**；修完 10 条后第 2 轮各项 **5–7 分**。主要短板是版面留白（评审原话「五镜主体缩在一角、四到七成画面是空的」），已列入 Roadmap，本版未改。
- **2560 版没有 OCR 证据**：本机 `onnxruntime` import 即段错误（rc=0xC0000005），RapidOCR 无法加载，`validate-ocr` 按设计 SKIPPED。同一份字幕在 1080 版上实测相似度 **1.00 / P0=0 / P1=0**。
- **真翻页只在 Linux 验证过**（Windows / macOS 未验证；失败会自动退回）。
- **Openverse 音频分类**：参数按官方 OpenAPI 实现，但 2026-10-29 实测线上 `category` 过滤返回 0 条（`sound_effect`）或 HTTP 500（`music`），属上游问题。

## Roadmap（下一版）

- 重排演示片 S1 / S2 / S6 的版面：主体放大到 ≥40% 画宽，或每镜补一个功能元素（评审第 2 轮的主要意见）。
- 在能跑 onnxruntime 的机器上补 2560 版 OCR。
- Windows 上验证真翻页。
- `fx-browser --self-test` 在 Windows 上已不再崩，但真翻页仍未在 Windows 验证。

## 致谢与依赖

- 感谢所有提 Issue 与 Star 的用户。
- 自 3.2.0 起新增（3.7.0 本身没有新增依赖）：
  - 3.3.0：导演方法思路致谢 lemo-opuscar（MIT，未复制代码 / 文本）与 motion-video-kit（MIT）；`perfect-freehand`（MIT）、`opentype.js`（MIT），npm 安装、不随仓库分发；Noto Serif SC Bold（SIL OFL 1.1，按需下载、sha256 校验）；手作音效、手作皮肤背景与背景库（自制，生成脚本 `scripts/dev/make-bg-library.py`）；`commons-search.py` 取回的 Wikimedia / Openverse 素材（仅 PD / CC0 / CC BY）；可选 OCR 门禁使用 RapidOCR（Apache-2.0，用户自行安装）。
  - 3.5.0：`@remotion/effects@4.0.539`（Remotion 许可，可选真翻页）；可选的完整版 Chromium（用户自备）。
- 完整原文见仓库 `NOTICE` 与 `DEPENDENCIES.md`。

## 配图

发布时作为 Release 附件上传，**不入库**：

- 前后对比：`cell/look/cell-v2-vs-v3.jpg`
- 开场四帧：`cell/look/opening-v3.png`
- 预览片：`cell/look/cell-v3-preview.mp4`
