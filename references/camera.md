# 镜头语言、虚拟摄影机与翻页转场

本篇规范运镜、景别、缩放上限、虚拟摄影机与翻页转场，上限数值以 `assets/lecture-template/src/contract.json` 为唯一真源。

<a id="camera-language"></a>
## 1. 受限配方与出界数学证明

- 镜头运动全部由 `manifests/shots.json` 声明并经 `scripts/resolve-shots.py` 展开为 `shots.resolved.json` 与 `src/shots.ts`，禁止在组件里手写无约束的 CSS 位移。
- `validate-shot-motion.py` 对每镜真实关键帧做数学校验（auto 路线查 `cinema.path`，`at` 严格递增）：
  - **anchor 不出界**：所有关注点必须落在舞台 `STAGE`（`1920×1080`）可见边界内，越界判 P0。
  - **平移安全公式与外层豁免**：带平移镜头须满足 `maxPanX = 960 × (1 - 1/s)`（`still` 不偏心）；页眉、章节卡与字幕必须渲染在 `ShotCamera` 之外。
- **自动抬缩放后不超预算**：平移导致边角露白时引擎会自动抬升缩放，若超过该 `intent` 预算或缩放天花板，判 P0。
  - **杜绝假运镜**：声明运动型 `intent` 但关键帧 `Δs ≈ 0` 且 `Δ平移 ≈ 0`，记 P1。

<a id="shot-language"></a>
## 2. 镜头语言：为什么动、动多少、何时不动

| 意图（`intent`） | 适用时机 | 缩放 / 运动约束（代码真源） |
|---|---|---|
| `establish` | 交代全景与关系 | `1.00–1.05`（省略 `to` 默认尾值 1.03），极慢漂移 |
| `push-in` | 聚焦关键证据或公式 | 含字镜总缩放 ≤ `TEXT_ZOOM_MAX`（1.35）；纯图形 ≤ `GRAPHIC_ZOOM_MAX`（1.6） |
| `pull-back` | 从细节拉回全局对照 | 退回全景看结构全貌 |
| `pan-follow` | 沿并排流程或时间线横移 | 停留点不切字，单镜缩放不超意图预算（1.2） |
| `reveal` | 随旁白逐步揭示图表/图版 | 配合草稿纸长出节奏 |
| `micro-orbit` | 立体物件/展板微幅环绕 | `rotY` 上限 `ORBIT_ROT`（6°） |
| `still` | 锤子帧、复杂对照停顿消化 | 普通镜静止 ≤ `DEFAULT_MAX_STATIC`（2.5s）；锤子镜 ≤ `HAMMER_MAX_STATIC`（3.0s） |

- **景别四档**：全（`≤1.05`）、中（`≤1.20`）、近（`≥1.20`）、特写（插入镜或 `≥1.35`，纯图形 `≥1.5`）。有字且要更近时用插入镜重排字号，不要硬放大把字拉糊。
- **单次运镜时长**：`CAM_DUR` 区间 `30–45` 帧（`short: 30` / `std: 38` / `long: 45`）；每 12 秒至少 1 次有效运镜。

- **招牌镜头**（`signature_shot`）缩放变化必须 ≥ 12%（相机路径最大/最小缩放，或 `cinema.focus` 的 `zoom`），或屏幕位移 ≥ 120px，否则手作皮肤 P0（`validate-treatment.py`）。推不进也扫不开时 compose 改选最近能推的镜并写回。
- **treatment 与镜头表一致**：auto 路线 `cameraIntent` 按 `cinema.path` 的真实运动记（`move: still` 的镜不推不扫），与 `treatment.json` 的 `move`、`framing`（景别四档）对照，不一致记 P1。
- **插入镜**：要特写又有字时，用镜头表 `insert` 硬切到同一画面的局部重排，按特写尺寸重新排版，而不是放大。
- **视线连续**（剪辑点前后让眼睛不用找）：落点接起点；运动方向一致（反向只用于转折）；用形状/颜色/位置相同的东西做匹配剪辑；同一时刻只给一个必须读的焦点；有关系的两样东西用引线、箭头或同色连起来；跨镜留一个物件。
- **何时不动**：关键揭示后锁定 1.5–3 s；字幕整行出且画面有要对照读的细节时；原生动作（晕开、盖章、落剪）进行时；片尾回到开头构图时。
- **镜长错开**（`validate-composition.py`，P1）：镜长变异系数（标准差 / 平均）≥ 0.35，最长/最短 ≥ 2 倍，≤ 80% 落在同一档；至少一镜 ≤ 4 s；单镜 > 12 s 须镜内换焦点或接插入镜。

<a id="cinema-camera"></a>
## 3. 引擎虚拟摄影机（`src/cinema.tsx`）

- **视线连续**：开头从上一镜末尾的注视点过渡回全景。
- **讲到哪推到哪**：`story.json` 台词里的 `{{关键词}}` 命中元素后，auto 路线在 `ZOOM_MAX`（1.32）内自动搜索安全取景窗（不切断任何标题或标签），推近不足 1.08 倍则仅高亮不推。
- **手写 `cinema` 块**（`manifests/shots.json` 每镜）：`"cinema": {"fit": "auto|none", "drift": "auto|none|<数字>", "focus": [{"beat": 1, "region": "right", "zoom": 1.2, "hold": 45}], "pan": {"worldW": 2600, "at": 10, "dur": 90, "dir": "ltr"}}`。`focus` 的时刻三选一：`beat`（拍下标）/ `cue`（字幕序号）/ `at`（帧），可加 `offset`；范围写 `region`（`left` / `right` / `top` / `bottom` / `center` / 四角）或 `x,y,w,h`；`pan.worldW` 必须 > 1920。
- **推近保件（`keep`）**：手写 `cinema.focus` 推近局部且需保住同屏 `MediaFrame`/大数字时，写 `keep: {x, y, w, h}` 防止被推出画框。
- **内容自动放大（`fit`）**：anchor 占安全区面积 `< 60%` 时自动等比放大，总缩放仍钳在 `TEXT_ZOOM_MAX`（1.35）内。
- **镜尾自动收束**：`resolve-shots.py` 检测到镜尾 > 1.5 秒无新事件时，自动补一段轻微收束慢推，防止触发静止段门禁。

<a id="fx-effects"></a>
## 4. 真翻页 / 揭纸转场（`@remotion/effects`）

- `auto` 路线换镜默认一律翻页，时长为 `CURL_FRAMES`（22 帧，约 0.73 秒）；其余转场 14 帧。
- 卷页使用 `@remotion/effects` 官方 WebGL2 `pageTurn`；`notebook-video fx-probe <工程>` 会先探测当前浏览器 WebGL2 能力，探针不过自动退回纯 CSS 折痕翻页 `pageflip`（并在报告中记 P1 提示，不拦出片）。
- 转场重叠窗口内的双镜挂载带 `data-gate-allow="handoff"`，渲染期重叠门禁对该 22 帧（或 14 帧）窗口放行。
