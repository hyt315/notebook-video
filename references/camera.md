# 镜头语言、虚拟摄影机与翻页转场

本篇规范运镜意图、景别、缩放上限、虚拟摄影机与翻页转场，上限常量以 `assets/lecture-template/src/contract.json` 为准。

<a id="camera-language"></a>
## 1. 受限配方与出界数学证明

- 镜头运动由 `manifests/shots.json` 经 `scripts/resolve-shots.py` 展开为 `shots.resolved.json` 与 `src/shots.ts` 驱动，禁止组件内手写无约束 CSS 位移。
- `validate-shot-motion.py` 对每镜真实关键帧（auto 路线读 `cinema.path`，`at` 严格递增）做算术证明：
  - **anchor 不出界**：核心包围盒须始终落在舞台 `STAGE`（`1920×1080`）可见窗内，越界判 P0。
  - **平移与外层豁免**：水平/垂直平移受限于 `maxPanX = 960 × (1 - 1/s)`；页眉、章节徽标与字幕必须挂载在 `ShotCamera` 之外。
  - **缩放合规与真运动**：总缩放不越 `intent` 预算与天花板；声明运动型意图却几乎无位移/缩放（`Δs ≈ 0` 且 `Δ平移 ≈ 0`）记 P1。

<a id="shot-language"></a>
## 2. 镜头语言：景别、意图与节奏

| 意图（`intent`） | 适用时机 | 缩放 / 运动约束（代码真源） |
|---|---|---|
| `establish` | 交代全景与结构关系 | `1.00–1.05`，缓慢交代 |
| `push-in` | 聚焦核心结论、关键词或大数字 | 含字 ≤ `TEXT_ZOOM_MAX`（1.35）；纯图形 ≤ `GRAPHIC_ZOOM_MAX`（1.6） |
| `pull-back` | 从局部术语/主角卡片缓缓拉回全貌 | 取景窗随缩放放开（`driftDir: "none"` 防冲突微推） |
| `pan-follow` | 沿并排流程 / 对比 / 柱图横移扫镜 | `s` 不超意图预算（1.2），起落停留点不切字 |
| `reveal` | 随旁白逐步揭示图表/图版 | 配合草稿纸长出节奏 |
| `micro-orbit` | 立体物件/展板微幅环绕 | `rotY` ≤ `ORBIT_ROT`（6°） |
| `still` | 锤子帧、定机图版或精细阅读停顿 | 普通镜静止 ≤ `DEFAULT_MAX_STATIC`（2.5s）；锤子镜 ≤ `HAMMER_MAX_STATIC`（3.0s） |

- **景别四档与插入镜**：全（`≤1.05`）、中（`≤1.20`）、近（`≥1.20`）、特写（插入镜或 `≥1.35`，纯图形 `≥1.5`）；带字特写用 `insert` 重排字号，不硬拉大糊字。
- **时长与密度**：单次运镜 `CAM_DUR` 为 `30–45` 帧；每 12 秒 ≥ 1 次运镜；全片非静止意图 ≥ 3 种；镜长变异系数 ≥ 0.35（最长/最短 ≥ 2×，≥1 镜 ≤ 4s）。
- **招牌镜与联动**：`signature_shot` 须实现 ≥12% 缩放变化或 ≥120px 位移（手作路线 P0）；auto 路线 `cameraIntent` 依 `cinema.path` 实算写回并与 `treatment.json` 核对。
- **视线连续与不动时机**：剪辑点落点接前镜注视点、同向承接；关键揭示后锁 `1.5–3s`、原生动作时与结尾回扣时保持稳定。

<a id="cinema-camera"></a>
## 3. 引擎虚拟摄影机（`src/cinema.tsx`）

- **auto 多意图镜头导演**：`compose-story.py` 结合版式与前序镜流自动编排 `push-in`（冷开聚焦与重音数字/引语）、`pull-back`（局部拉回全景）、`pan-follow`（沿 `flow`/`compare`/`bars` 横移扫镜，边界按安全窗与 `keep` 交集求取）与 `still`（短收束停顿）；并通过 `driftDir`（`'none'|'push'|'pull'|'pan-left'|'pan-right'`）防止引擎默认慢推对抗拉远/横移镜头。
- **手写 `cinema` 块**：支持 `fit`、`drift`、`focus`（`beat`/`cue`/`at` + `region` 或坐标 + `keep` 防推出画外件）及 `pan`（`worldW > 1920`）。`resolve-shots` 在长镜尾无新事件时补温和收束动势防静止超时。

<a id="fx-effects"></a>
## 4. 翻页与转场调度

- 换章境界与手作皮肤默认 `"auto"` 真翻页（WebGL2 卷页 `pageturn`/`peel` 时长 `CURL_FRAMES` = 22 帧，探测未通过自动退回 CSS 折痕翻页 `pageflip`）；组件路线同章内切镜依布局节奏选用 `slide`（流程/对比/柱图）与 `fade`（14 帧），并支持单镜 `transition` 显式覆盖。
- `fx-probe` 结果写入报告；转场重叠窗口带 `data-gate-allow="handoff"` 放行浏览器重叠检测。
