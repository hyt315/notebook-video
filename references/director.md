# 导演层：讲法、开场、节奏、风格与画面模式

本篇是手作路线（`journal` / `papercut` / `archive`）的必读文档，讲稿层的通用写作标准见 [narration.md](narration.md)。

<a id="director-method"></a>
## 1. 导演层方法（`manifests/treatment.json`）

动手画画面之前，先回答 7 个导演问题并写进 `manifests/treatment.json`（模板见 `treatment.example.json`）：
1. **生活问题（`question`）**：观众真会在意的一个具体疑问，而非学术名词。
2. **专属隐喻（`metaphor`）**：`idea` + `why_unique`——换成相邻题目立刻不成立的隐喻才算过关。
3. **皮肤契合（`medium`）**：为什么必须用这套手作皮肤（`journal` 手账记录 / `archive` 档案考据 / `papercut` 剪纸层次），而不是通用卡片。
4. **顿悟原生动作（`native_move`）**：在顿悟点做一个只有该媒介演得出的动作（例如水彩抽干只剩墨线、放大镜压上原版铜版画）。
5. **三选一结构（`candidates` / `chosen`）**：至少给出 3 个候选结构、覆盖至少 2 个结构族（`medium-metaphor`、`kishotenketsu`、`mystery`、`scale-ladder`、`experiment`），说明取舍理由。
6. **对标边界（`benchmark` / `avoid`）**：写清学什么构图/节奏逻辑、不学什么（禁止复刻具体角色或套暗底发光风）。
7. **逐镜理由与招牌镜（`shots` / `signature_shot`）**：每镜写景别、运镜与理由；招牌镜必须有真实推近（≥12%）或屏幕位移（≥120px），否则 `validate-treatment.py` 判 P0（`auto` 路线下 `signature_shot` 不可点名 `page`，应点名 `flow`/`list`/`compare`）。

**独立评审（P1，不阻塞）**：手作皮肤整片渲染前，建议用 `--stills` 出联系表，由新会话独立评审（**只给三样**：`--stills` 联系表、`storyboard.md`、`treatment.json`，不给过程记录）按 [rubric.md](rubric.md) 5 项评审卡独立打分并写入 `treatment.json` 的 `review.rounds`。结果会直接显示在 `renders/report.md` 首屏；未评审时首行显示「未评审」并给 P1 提示（`--skip-review` 可关闭提示）。

### `manifests/treatment.json` 必填字段速查

`validate-treatment.py` 检查的核心键：`topic`、`question`、`metaphor.{idea, why_unique}`、`medium.{skin, why}`、`native_move.{what, at_sec, why_only_this_medium}`、`candidates[].{id, family, shape}`（≥3 个且覆盖 ≥2 个结构族）、`chosen`（匹配 `id`）/ `chosen_why`、`benchmark.{works, learn, not_learn}`、`turn_to_you_sec`、`sound.{silence_before_native_move_sec, most_important_sound, music, foley_per_medium}`、`logline`、`arc.{setup, turn, ending}`、`ending_echo.{opening_image, one_change}`、`shots[].{id, framing, move, why}`、`signature_shot`、`commons.queries`、`facts[].{claim, url, quote}`、`review.rounds`。

- **模板路径**：`assets/lecture-template/manifests/treatment.example.json`。
- **合法景别枚举（`shots[].framing`）**：`全` / `中` / `近` / `特写`。
- **合法运镜枚举（`shots[].move`）**：`establish` / `push-in` / `pull-back` / `pan-follow` / `reveal` / `micro-orbit` / `still`。

<a id="narrative-moves"></a>
## 2. 讲法规范（误解优先 · 叙事动作 · 留白）

- **误解优先**：先演活观众原本的错误直觉，再用原图或实验证据推翻，比直接讲定义记忆深得多（组件路线同样适用，见 [narration.md](narration.md)）。
- **叙事动作（`move`）**：`shots.json` 合法叙事动作枚举为「引入、定位、推进、传递、对比、`拆分/合并`（整体带斜杠）、累积、收束、反证、回看」，并配 `misconception` 或 `noMisconception`、`hold ≥ 40` 帧及 `silentCues`；每镜在 `shots.json` 声明叙事动作，同一 `move` 不得连续超过 2 镜（连续 ≥3 镜由 `validate-presentation.py` 记 P1）。
| 动作 | 观众看得出的画面证据 | 首选件 |
|---|---|---|
| 引入 | 新实体出现，名字贴上去 | `Paper` + `PillTag` / `TopicIcon` |
| 定位 | 已有的东西被点亮或圈住，其余退后 | `FocusFx`（dim / spot）/ `Callout` |
| 推进 | 同一主体进入下一状态 | `StageFrame` / `PhaseRail` |
| 传递 | 东西沿可见路径从 A 到 B | `Corridor` / `PathDraw` |
| 对比 | 两个状态同屏，差异被标出 | `SplitStage` / `MetricGrid` |
| 拆分/合并 | 一变多或多变一 | `SplitStage` / `MorphShape` |
| 累积 | 讲过的留在原地，越讲越满 | `Checklist` / `StaggerList` |
| 收束 | 结论出现，前面内容退到次要 | `VerdictBar` / `StatRow` |
| 反证 | 先给错的或旧值，再给对的，两者被区分 | `MetricGrid` / `SplitStage` |
| 回看 | 把前面几件再摆一次，复用同一视觉件 | 复用原骨架 |

- 同一 `move` 最多连续 2 镜，第 3 镜起记 P1（按成片镜序，跨章节不重置）。
- `evidence` 必填，指向一个在本镜内真的会变的元素；静态元素不算证据。门禁（G-15）只核对这个名字在场景源码里被当成 JSX 用到，不判断它是否在本镜作用域内、是否真的随帧变化，这两点靠审片。
- **留白呼吸**：关键反转或顿悟帧后留 1.5–2.5 秒不塞新信息，让画面动作先于或陪着观众消化。

<a id="narrative-hook"></a>
## 3. 冷开场契约（前 3 秒）

开场写法由 `validate-opening.py` 检查（全部 P1，成片后的像素复核只进报告）：
- **第 0 帧即见主体**：不开黑屏、不用「片名居中」当第一镜；第 1 镜首个可见事件 ≤ 6 帧。
- **首句 ≤ 1.0 秒起声**：冷开直奔反常现象或误解，禁止用「大家好」「今天我们来聊聊」等泛问句开场。
- **前 3 秒（90 帧）≥ 3 拍**：迅速建立视觉与问题钩子。

**前 10 秒的形状**：

| 时间 | 任务 |
|---|---|
| 0–1.5 秒 | 直接给结果：最大的已核实事实或可见结果先于片名、问候和背景出现，主体 0.5 秒内入场或变化 |
| 1.5–4 秒 | 立张力：说清这个结果为什么反常、难、有风险，用精确对比，不用空泛提问 |
| 4–8 秒 | 留悬念：点名后面要拆的机制或限制，但不解答 |
| 8–12 秒 | 转入正文：给出第一条证据路径，不复读开场句 |

- **首句三种写法**（写完对照出处核实）：结果先行（「一条命令，能让你写崩的代码一秒回到十分钟前。」）；指出盲区（「你花 399 买的课，GitHub 上大概率有人免费开源了。」）；冲突反差（「两个人改同一个文件，一提交，队友三天的代码直接消失。」）。不用「作为 XX 专业的学生」「上一课我们学了」这类身份标签或路线图开场。
- **一个角度**：规模、反转、限制、取舍或真实后果，挑一个；开场句不堆多个论断。出处、定义、限定语放到转入正文或回扣里。
- **关声也成立**：前 4 秒有一个大而具体的论断加一个可见后果，不夸大出处。
- **回扣**：在 `storyboard.md` 写三行：`Opening payoff`（开场给出的论断或画面）、`Deferred question`（故意留下的问题）、`Callback / payoff`（哪一镜哪一句回答它，通常在最后 25% 之前）。回扣要补证据或因果，不复读标题，并复用开场的主体物件、数字或状态。证据答不上的悬念不要开。
- **开场复查**：整片渲染前局部渲 0–360 帧，看 0.5 / 2 / 4 / 8 / 10 秒。主论断 1.5 秒还没出现、首句是背景铺垫、画面要读后面的字幕才懂、悬念没写回扣、或含无出处的最高级比较，就重写开场。

<a id="pacing-rhythm"></a>
## 4. 节奏与韵律

- **快慢交替**：短镜（信息确认、数字落定）与长镜（原理拆解、图版细看）交替出现，避免整片镜长划一。
- **一镜一问题**：每镜只回答 `$asks` 写明的一个问题，单镜台词 1–3 句。
- **锤子帧**：全片留 2–3 个满屏停顿 1.5–2.5 秒的记忆句（锤子镜静止上限 `HAMMER_MAX_STATIC` = 3.0s，普通镜 `DEFAULT_MAX_STATIC` = 2.5s）。
  - 大约每 60–90 秒一个，不放在相邻两章；出现前其他区域完全离场，之后再恢复多区版式。挑能反转认知或压缩整章的句子（「冲突不是报错，是 Git 在问你意见」），不挑总结句。在 `storyboard.md` 标 `Hammer:` 加 cue 号。
- **快章与慢章**：慢章（新概念）每 3–4 秒一次状态变化、停留更长；快章（步骤、清单、蒙太奇）每 1.5–2.5 秒一次。不连续两个慢章，中间隔一个快章或锤子帧。按章分段的 TTS 可以给慢章更沉稳、快章和开场更利落的语气，同一个声音。
- **章间呼吸**：两章之间留 0.5–1 秒，上一镜完整离场、纸面只剩页眉，再开始长下一章的第一个元素。
- **结尾**：最后一章刻意变稀，最多三样（收束句、角色、结尾卡）。知识类片子的结尾卡用收藏钩子，点出下次什么时候会用到（「点个收藏，下次写崩了翻出来照着敲」），不求关注。

<a id="style-recipes"></a>
## 5. 风格配方八轴

选择或微调观感时只在这八个轴上对齐，不发明脱轨装饰：纸底纹理、墨线粗细、强调色占比（仅 1 种主强调色）、字号层级、留白比例、进场节奏（草稿纸长出）、翻页转场、材质颗粒。详细锁定色板见 `references/themes/<皮肤>.md`。

<a id="visual-director"></a>
## 6. 画面模式选择

- **真图版承载（`page`）**：历史文物、自然标本、原书版画优先走手账页 `plate` / `loupe`。
- **结构拆解（组件）**：数字对比、机制流程、代码改动走 `bars` / `flow` / `compare` / `code`。
- **直书页（`type`）**：只有单一关系或锤子句时，靠字号与行距排层级，不出圆角框（每行 ≤10 字、≤5 行、全片 ≤40%）。
