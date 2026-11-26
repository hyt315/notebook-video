# 导演层：讲法、开场、节奏、风格与画面模式

本篇为手作路线（`journal` / `papercut` / `archive`）必读；通用讲稿规范见 [narration.md](narration.md)。

<a id="director-method"></a>
## 1. 导演层方法（`manifests/treatment.json`）

动手编排前先填写 7 项导演决策（模板 `assets/lecture-template/manifests/treatment.example.json`）：
1. **生活问题（`question`）**：观众真实在意的具体疑问，不用学术词条命名。
2. **专属隐喻（`metaphor`）**：`idea` + `why_unique`——换成相邻选题立刻失效才算成立。
3. **皮肤契合（`medium`）**：说明为何非此手作媒介（手账考据/档案灯台/剪纸层叠）不可。
4. **顿悟原生动作（`native_move`）**：在认知转折点设计只有该媒介能演出的动作（水彩抽干留墨、放大镜落片、剪纸掀层）。
5. **三候选结构（`candidates` / `chosen`）**：≥3 个候选、覆盖 ≥2 个结构族（`medium-metaphor`、`kishotenketsu`、`mystery`、`scale-ladder`、`experiment`），注明取舍原因。
6. **对标边界（`benchmark` / `avoid`）**：学构图/节奏逻辑，禁复刻具体角色或暗底霓虹风。
7. **逐镜理由与招牌镜（`shots` / `signature_shot`）**：景别（`全`/`中`/`近`/`特写`）与运镜（`establish`/`push-in`/`pull-back`/`pan-follow`/`reveal`/`micro-orbit`/`still`）须匹配；`signature_shot` 须有真实推近 ≥12% 或位移 ≥120px（手作 `validate-treatment.py` P0；`auto` 路线不点名 `page`，改为有并列/大主体的 `flow`/`compare`/`list`/`number`）。

- **独立评审**：手作皮肤建议先出 `--stills`，由独立新会话（仅看 `--stills` 联系表、`storyboard.md` 与 `treatment.json`）按 [rubric.md](rubric.md) 打分写入 `review.rounds`；未评审仅给 P1 提示（`--skip-review` 可关闭）。
- **必填字段速查**：`topic`、`question`、`metaphor.{idea, why_unique}`、`medium.{skin, why}`、`native_move.{what, at_sec, why_only_this_medium}`、`candidates[].{id, family, shape}`、`chosen`/`chosen_why`、`benchmark.{works, learn, not_learn}`、`turn_to_you_sec`、`sound.{silence_before_native_move_sec, most_important_sound, music, foley_per_medium}`、`logline`、`arc.{setup, turn, ending}`、`ending_echo.{opening_image, one_change}`、`shots[].{id, framing, move, why}`、`signature_shot`、`commons.queries`、`facts[].{claim, url, quote}`、`review.rounds`。

<a id="narrative-moves"></a>
## 2. 讲法规范（误解优先 · 叙事动作 · 留白）

- **误解优先**：先立出直觉误区或反常证据，再拆解推翻。
- **叙事动作（`move`）**：枚举为「引入、定位、推进、传递、对比、`拆分/合并`、累积、收束、反证、回看」（同一 `move` 跨章节连续 ≥3 镜记 P1），配 `misconception`/`noMisconception`、`hold ≥ 40` 及真实随帧变化的 `evidence` JSX 组件：

| 动作 | 画面证据 | 首选件 |
|---|---|---|
| 引入 / 定位 | 新实体出现或焦点点亮 | `Paper`+`PillTag` / `FocusFx`+`Callout` |
| 推进 / 传递 | 同物进阶或沿路径移动 | `StageFrame`+`PhaseRail` / `Corridor`+`PathDraw` |
| 对比 / 拆分合并 / 反证 | 同屏对照或新旧替换 | `SplitStage` / `MetricGrid` / `MorphShape` |
| 累积 / 收束 / 回看 | 步步叠加、锤子收束或复现原件 | `Checklist` / `VerdictBar` / 复用原骨架 |

- **留白**：关键反转或顿悟帧后留 1.5–2.5s 供观众消化。

<a id="narrative-hook"></a>
## 3. 冷开场契约（前 3–6 秒承诺与全片兑现）

`validate-opening.py` 检核第 0 帧主体（`O6` 成片 P0）与前 3 秒节奏（`O1–O5`/`O7` 记 P1）：

- **第 0 帧即见主体且首句 ≤ 1.0s 起声**：禁止黑屏、泛问候或「XX 是一种……」教科书开篇；前 90 帧 ≥ 3 拍视觉推进。
- **开场承诺（0–6 秒） vs 结论兑现**：
  - **0–1.5 秒（抓手）**：亮出最有力画面或具体已核实的反常结果，主体立刻动作。
  - **1.5–6 秒（诚实立张力）**：点清直观冲突或必须回答的核心问题（禁标题党夸大或虚假悬念）。
  - **兑现节奏**：直接讲解型（组件蓝图）在前两镜点明方向并逐问拆解；发现/悬疑结构族须在全片 **80% 进度之前** 揭晓核心机制并留足实证回扣（不在片尾强留未答悬念）。
- **无声可懂 & 写三行回扣**：前 4 秒有具体对比与可见动作；在 `storyboard.md` 写明 `Opening payoff` / `Deferred question` / `Callback / payoff`（复用开场物件/数字补足因果，不简单复读标题），整片渲染前抽看 0.5 / 2 / 4 / 8 / 10 秒。

<a id="pacing-rhythm"></a>
## 4. 节奏与韵律

- **快慢交替**：短镜（`number`/定论）与长镜（机制拆解/图版）错落，每镜 1–3 句仅答 `$asks`。
- **锤子帧**：全片 2–3 处，满屏停顿 1.5–2.5s（上限 `HAMMER_MAX_STATIC` = 3.0s，普通 `DEFAULT_MAX_STATIC` = 2.5s），出现前清空四周，隔章落点并标 `Hammer:`。
- **章节奏与结尾**：慢章（每 3–4s 变化）与快章（每 1.5–2.5s 变化）交替，章间留 0.5–1s 呼吸；末章精简至 ≤3 样并给实用回看钩子（禁空洞求关注）。

<a id="style-recipes"></a>
## 5. 风格配方八轴

只沿八轴对齐观感，不混搭违和装饰：纸底纹理、墨线粗细、单主强调色占比、字号层级、留白比例、草稿纸长出节奏、翻页转场、材质颗粒（色板见 `references/themes/<皮肤>.md`）。

<a id="visual-director"></a>
## 6. 画面模式选择

- 真品/档案/标本优先 `layout: "page"`（`plate` / `loupe`）；
- 结构/数据/对比/代码用 `bars` / `flow` / `compare` / `code`；
- 单一核心关系或锤子句用直书页 `type`（每行 ≤10 字、≤5 行、全片 ≤40%，不套框）。
