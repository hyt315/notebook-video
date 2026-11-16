# 导演层：讲法、开场、节奏、风格与画面模式

选题怎么讲：导演层（treatment）、修辞动作、开场钩子、节奏、风格配方和每镜的画面模式。手作路线先读这一篇。

本篇各节：

- [导演层：先找"只属于这个题"的东西，再动手](#director-method)
- [讲法规范（叙事动作 · 误解优先 · 留白）——第三张表：**怎么讲**](#narrative-moves)
- [Cold-open narrative contract](#narrative-hook)
- [Pacing and rhythm contract](#pacing-rhythm)
- [风格配方：把一种"观感"拆成可执行的八个轴](#style-recipes)
- [Visual director: image, text and graphic modes](#visual-director)

<a id="director-method"></a>

## 导演层：先找"只属于这个题"的东西，再动手

> 适用：每一条片子，尤其是手作皮肤（journal / papercut / archive）。产物：`manifests/treatment.json`，
> 由 `scripts/validate-treatment.py` 检查（手作皮肤缺文件、留占位或写得自相矛盾 = P0；字段空着只提示 P1；flat / cel 一律 P1）。
> 思路来源：lemo-opuscar 的 DIRECTOR.md（MIT，© 2026 LemoLab，<https://github.com/lemomo-ai/lemo-opuscar>）；
> 独立评审借鉴 motion-video-kit（MIT）的 "builder ≠ judge"。本文是自己的写法，不是译文。
>
> 配套：开场钩子 [director.md#narrative-hook](director.md#narrative-hook)、节奏 [director.md#pacing-rhythm](director.md#pacing-rhythm)、运镜 [camera.md#camera-language](camera.md#camera-language)。

### 为什么要这一层

蓝图管顺序，组件表管卡片，都不回答：**这件事用什么东西演出来，观众才会"啊——原来是这样"？**
不回答它，片子就落进同一个模板：名词 → 定义 → 拆开 → 升华，画面是卡片里放组件。

### 七步（按顺序，每步写进 treatment.json）

#### 1. 一个生活里的问题（`question`）
第一秒就能问出口、观众自己遇到过的那句话（"咖啡渍为什么总是一圈深边？"），不是"今天我们来了解 XX"。

#### 2. 只属于这个题的隐喻（`metaphor`）
找一个**换个题就不成立**的形象。检验：换成邻近的题还能用 = 太泛，重找。
- 好：二维码本来就是"黑白剪纸"——深色模块是纸，浅色模块是洞（纠错码）。
- 差："知识的大门""信息的海洋"。

#### 3. 媒介即隐喻（`medium`）
选一个皮肤 / 媒介，让**物质本身**就在讲这个道理。写清"为什么是它"：
| 媒介（皮肤） | 它天生会做的事 | 适合 |
|---|---|---|
| `journal` 手账水彩 | 观察、记录、晕开、批注、贴照片 | 发现、实验、自然、"有人第一次看见" |
| `papercut` 红色剪纸 | 剪掉、对折复制、镂空、碎片回位、背光透洞 | 对称、复制、冗余、结构、缺了还能补 |
| `archive` 档案灯台 | 真实物件、放大镜、负片转正、并排比对、编目 | 考据、溯源、"这话最早谁说的"、真实数据 |
| `flat` / `cel` | 组件、仪表盘、代码、流程 | 软件、产品、操作教程 |
更多媒介的"配方"（risograph、engraving、whiteboard、one-line…）见 [director.md#style-recipes](director.md#style-recipes)。

#### 4. 一个原生动作（`native_move`）——放在顿悟点
**只有这个媒介做得出**的那个动作，放在观众理解发生变化的那一秒（水彩晕开干透、自己圈出深边；对折剪一刀，两份同时坏；镜片里负片转正）。
写清：做什么、在第几秒、为什么换成别的媒介做不出。没有原生动作的顿悟点，只能是"一个数字滚到位"。

#### 5. 三个候选结构，选一个（`candidates` + `chosen` + `chosen_why`）
每个两三行：形状（旅程 / 前后对比 / 倒计时 / 清单逐条翻转 / 错误猜想被推翻……）、开头画面、结尾。第一个想到的往往是陈词滥调；写满三个再选。

**选结构族**：每个候选写 `family`，三个候选**至少来自 2 个族**（否则只是同一条曲线的三种写法，validate-treatment 记 P1）。
族名与蓝图：

| 族 `family` | 蓝图 | 适合 |
|---|---|---|
| `medium-metaphor` | `blueprints/medium-metaphor.json` | 错误直觉被一个原生动作推翻（手作默认） |
| `kishotenketsu` | `blueprints/kishotenketsu.json` | 起承转合，第三拍出意外 |
| `mystery` | `blueprints/mystery.json` | 悬案：线索逐条揭开 |
| `scale-ladder` | `blueprints/scale-ladder.json` | 尺度阶梯：一级一级比出大小 / 多少 |
| `experiment` | `blueprints/experiment.json` | 对照实验：只变一个量 |
| `lecture-arc` | `blueprints/concept.json`、`code-change.json`、`data-compare.json`、`process.json`、`pitfall.json` | 组件路线的讲解弧 |
| `one-take-journey` | （无蓝图） | 一镜到底的旅程 |
| `myth-flip` | （无蓝图） | 一个流行说法被逐条翻转 |

10 个蓝图的归属即上表：5 个组件路线蓝图都属 `lecture-arc`，5 个手作蓝图各自成族。

推荐默认形状（蓝图 `blueprints/medium-metaphor.json`）：
```
生活钩子 → 观众真有的错误直觉被"演出来" → 原生动作把它推翻 → 数得出来的证据（大数字画成"数得出来的多"）
→ 40–45% 处转向"你" → 结尾回到开头画面，但有一处变化，并回答开头的问题
```

#### 5b. 声音设计（`sound`）
**默认无 BGM**：`music.use` 不写或 `false` 时不加载音乐床；要配乐才写 `true` 并给出理由。声音设计仍必填（缺项 P1），`treatment.json → sound`：

| 字段 | 意思 | 示例 |
|---|---|---|
| `bed` | 底噪 / 环境声，全片垫底 | "安静的书房：纸面极轻的摩擦" |
| `foley` | 哪些动作配什么材料声 | ["刀片划过软木：短促的擦声"] |
| `silence` | 顿悟前那次安静在第几秒（原生动作前留白） | "21.0–21.8 s 全静，放大镜落下前" |
| `most_important_sound` | 全片最重要的一声：什么声音、第几秒（要比别的都突出） | "22.0 s 放大镜落定：木头轻磕" |
| `music.use` / `music.why` / `music.mood_curve` | 用不用配乐、为什么；用就写情绪曲线 | `{"use": false, "why": "素材库尚未接入，留白优于凑数"}` |
| `foley_per_medium` | 每种媒介动作对应的拟音 | ["画线：铅笔划纸", "晕染：湿笔刷", "盖章：印泥按压"] |

响度目标 −16 LUFS（真峰值 ≤ −1.5 dBTP，与渲染端两遍响度规范化的 TP 值一致；全文目标见 [audio-captions.md#tts-audio](audio-captions.md#tts-audio)）。旁白由 `notebook-video tts` 生成；句间空隙必须是真安静。

#### 6. 对标：学什么、不学什么（`benchmark`）
挑一两部真实作品（纪录片、片头、绘本、展览），写"学：构图 / 节奏 / 镜头语法 / 配色逻辑"和"不学：角色、具体镜头、旋律、字体"；勾掉同质化清单（`avoid`）：暗底发光线、粒子、金色 / 冰蓝科技风、电子 BGM、名词→定义→升华模板。

#### 7. 镜头表要写"为什么"（`shots`、`signature_shot`）
每镜：景别（全 / 中 / 近 / 特写 / 插入）、运镜（推 / 拉 / 横移 / 跟 / 静）、**理由**。全片 ≥4 种运镜，一个招牌镜头。
**景别写了就要兑现**：`validate-treatment` 拿 `move` / `framing` 对照镜头表 `cameraIntent` 和实际缩放；招牌镜头至少真推 12%（keys 缩放或 `cinema.focus` 的 zoom），否则手作皮肤 P0。
动机、景别阶梯、视线连续、何时不动、镜长见 [camera.md#camera-language](camera.md#camera-language)。
转场在媒介内部完成（翻页、换一张纸、剪刀剪过、墨晕开），不用缺省的淡入淡出 / 甩镜。
关键时刻主体 ≥1/3 画高；每个构图 ≤12–15 秒；关键揭示后留 2–3 秒呼吸。
"节拍边界要有东西活下来"：上一拍的某个物件变成下一拍的起点，片子才连成一条线而不是幻灯片。

### 素材：每个选题先搜 Commons（`commons`）

```text
python scripts/commons-search.py search "<英文关键词>" --project ./my-video            # 图
python scripts/commons-search.py search "<关键词>" --type audio --project ./my-video   # 真实的声音
python scripts/commons-search.py search "<关键词>" --source openverse --project ./my-video
```
真东西（1665 年的铜版画、第一张 X 光片、显微照片、历史录音）几乎总能让片子更好。搜过记进 `manifests/commons-log.json`；手作皮肤没搜过 → P1；断网不卡出片。
能用的 `add` 进来，放进 `ArchivePhoto` / `PinnedPhoto` / `LoupeMedia`（[components.md#craft-kit](components.md#craft-kit)），署名自动上屏；没找到就写清搜了什么。

### 事实（`facts`）
每个数字、日期、人名：打开原始出处，写 `url` + 原文引文 `quote`。区分实验条件（"在真空中"、"小鼠"）。

### 先做风格帧，再做全片
1. 写完 treatment.json；
2. 3 张风格帧（含招牌镜头 / 最难的一镜），`make-video --stills` 看图，不像就改媒介或隐喻，不硬上；
3. 全片；`--stills` 联系表两遍；关键动作 0.2 秒连帧；
4. **独立评审**（做的人不评自己）：开一个新会话 / 子 agent，**只给它三样东西**：`--stills` 联系表、工程根目录的
   `storyboard.md`、`manifests/treatment.json`，不给任何过程记录。按七项 1–10 打分：
   构图主体、调度节奏、隐喻与媒介一致、顿悟惊艳、字幕可读、手作质感与色彩纪律、叙事完整；问题分 P0 / P1 / P2 列出。
   <8 的改完再评，分数、问题与处理写进 `treatment.json → review.rounds`（时间、评审者、问题、处理）。
   - `storyboard.md` 由 `resolve-shots` 从 `manifests/shots.resolved.json` **自动生成**（片名、总帧数、时长、皮肤；每镜起止秒、景别、运镜、意图 / 实际缩放、转场、背景、主要组件、字幕摘要）。
     文件头有"自动生成"标记，手改会被覆盖；手写过的（无标记）不覆盖，生成到 `storyboard.generated.md`——评审用生成的那份。
5. 一轮改完所有问题再渲整片。手作皮肤 `review.rounds` 为空时 `make-video --render` 给一条 P1 提示（照常渲染、写进报告）；草稿 / 自测加 `--skip-review`。

### treatment.json 字段一览
见 `assets/lecture-template/manifests/treatment.example.json`（复制成 `treatment.json` 再填）。门禁规则：

| 检查 | 手作皮肤 | flat / cel |
|---|---|---|
| treatment.json 存在、不留 `<<…>>` | P0 | P1 |
| 必填字段非空、`facts` 非空、写了 `native_move.at_sec`（纸面字段） | P1 | P1 |
| `chosen` 指向候选之一、候选的 `shape` 写完 | P0 | P1 |
| 恰好 3 个候选（思考工具，不拦渲染） | P1 | P1 |
| `medium.skin` 与工程的皮肤一致 | P0 | P1 |
| `native_move.at_sec` 写了就要是 >0 且在片长内 | P0 | P1 |
| 写了的每条 `facts` 有 http(s) 链接和引文 | P0 | P1 |
| `commons.used` 都在 media.json 里 | P0 | P1 |
| 搜过 Commons（`commons-log.json` 至少一次；断网时不拦） | P1 | P1 |
| `turn_to_you_sec` 落在片长 35–55% | P1 | P1 |
| 镜头表每镜有理由；运镜 ≥4 种；有 `signature_shot` | P1 | P1 |
| 招牌镜头实推 ≥ 12%（对照 shots.resolved.json） | P0 | P1 |
| `move` = 镜头表 `cameraIntent`；`framing` 与实际缩放 / 主体占比相符 | P1 | P1 |
| `review.rounds` 最后一轮七项都 ≥8 | P1 | P1 |

<a id="narrative-moves"></a>

## 讲法规范（叙事动作 · 误解优先 · 留白）——第三张表：**怎么讲**

> 本节管**"讲得对不对"**，不管"画得好不好"。依据是一次实证：同一份牛顿定律内容，364 名大一物理生分两组——
> "清楚流畅的讲解版" 26 题从 6.0 → **6.3（等于没学）**，且自评"简单、清楚"、更有信心；"**先说出误解、再反驳**"版 6 → **11**。
> 出处与拆解见 `讲解手法拆解.md`。纯"说明文"结构（「想入场，其实只要三步。第一步…」）就是那个"清楚了但没学"的版本。

### 1. 三条字段（写进 `manifests/shots.json` 的每镜）

| 字段 | 含义 | 取值 | 级别 |
|---|---|---|---|
| `misconception` | **观众此刻脑子里的错误想法**（用观众的话写，不是术语） | 一句话；或 `noMisconception: true` + 理由 | P1 必填其一（两者同时写是 P0） |
| `known` → `new` | 这镜**从什么已知**推到**什么新知**（相邻镜必须闭合：`known` 要能在前面某镜的 `new` 里找到，或属于常识锚点） | 各一句短语 | P0（闭合）/ P1（锚点存疑） |
| `hold` | 留白预算：**这镜里至少有一段什么都不新增** | 帧数（见 §3 标定） | P1 |

**`misconception` 必须可豁免，而且豁免要写理由**：先立误解对外行收益最大，对已学好的观众零增益、还显得冒犯。所以要求是"**要么立一个真误解，要么写清为什么这镜不需要**"，不是"每镜都卖关子"。

```jsonc
// 正面：先立误解
{"id": "S3", "misconception": "很多人以为 PR 一提交就自动生效", "known": "本地改了代码", "new": "远端还没有你的提交", "hold": 45}
// 豁免：写理由
{"id": "S7", "noMisconception": true, "why": "这镜是操作复述，观众上一镜刚被纠正过，再立一次会显得啰嗦",
 "known": "已推送成功", "new": "PR 是请别人看，不是自动合并", "hold": 40}
```

### 2. 叙事动作（闭合集，一镜一个 `move`）

第二张表（修辞动作 → 组件）解决"用哪件"，这张表解决"**此刻在讲什么动作**"。
闭合 10 个，**同一个 `move` 不得连续 ≥3 镜**：

| # | 动作 | 观众能看出什么（视觉证据） | 首选件 |
|---|---|---|---|
| 1 | 引入 | 一个新实体出现 + 名字贴上去 | `Paper` + `PillTag`/`TopicIcon` |
| 2 | 定位 | 某个已存在的东西被点亮/圈住，**其余退** | **`FocusFx`(dim/spot)** / `Callout` |
| 3 | 推进 | 同一主体进入下一状态 | `StageFrame`/`PhaseRail` |
| 4 | 传递 | 东西从 A 移动到 B（可见路径） | `Corridor`/`PathDraw` |
| 5 | 对比 | 两个状态同屏并陈 + 差异被标出 | `SplitStage`/`MetricGrid` |
| 6 | 拆分/合并 | 一个变多个 / 多个变一个 | `SplitStage`/`MorphShape` |
| 7 | 累积 | 已经讲过的东西留在那里、越讲越满 | `Checklist`/`StaggerList` |
| 8 | 收束 | 结论条出现，前面内容退到次要 | `VerdictBar`/`StatRow` |
| 9 | **反证** | **先给错的（或旧值），再给对的，两者被区分** | `MetricGrid`/`SplitStage` |
| 10 | 回看 | 把前面几件再摆一次（复用同一视觉件） | 复用既有骨架 |

> **「不得连续 ≥3 镜」的判据口径**：按**成片镜序**（= `shots.json` 顺序；`resolve-shots` 要求 `from` 连续，两者必然一致）逐镜比较，
> 同一 `move` 的**极大连续段 ≥3 镜即点名**——同一动作**最多连续 2 镜**，第 3 镜起报（不是"超过 3 镜"）。
> 跨章节**不重置**（观众不认章节号）；缺 `move` 或不在闭集里的镜**打断计数**（它们另报），不会拼出跨断点的假"连续"。
> **级别是 P1**：它约束写法不约束画面，连续同动作是节奏问题，点名不拦。
> 报错样式：`P1 S1–S3: 同一 move 连续 3 镜：S1→S2→S3 都是 «引入»（上限 2 镜…）`；连续 2 镜不报。

**`evidence` 必填**：指到一个**在该镜内真的会变**的元素。**静态元素不算证据。**

> 这是**作者侧的写作要求**；门禁只验其中一半，别当成"门禁已经保证"。
>
> **门禁判法**：`validate-presentation.py` 只查**名字有没有作为 JSX 用法**（`<名字 …>` / `<名字/>`）**出现在该工程的场景源码里**：
>
> | 判据 | 检查 | 级别 |
> |---|---|---|
> | G-15 **用在源码里** | `evidence` 的名字作为 **JSX 用法**出现在场景源码里；**注释、字符串、import 行里都不算"用到"** | **P0** |
>
> 先用 `noncode()` 把注释与字符串抹成空格（"只在注释里写过"会被报出），再用 `<名字` + 一个非标识符字符匹配。
> 场景源码 = `src/**` 里名字带 `scene` 的 `.tsx`；没有就退到任一 `.tsx`；连 `.tsx` 都没有则报一条 P1 说明**这条判据没生效**（让"没报"与"没跑"可区分）。
>
> **不做的（别高估它）**：
> · **不做本镜作用域**：名字在本镜没用到、但在别的镜用了，**会漏**。夹具 AG 钉住这个语义（必须放行）。
> · **不做"是不是静态"**：指向本镜里从头到尾不动的静态卡片，**门禁不会响**。理由：这一半只能做白名单判定且误报——
>   帧经 `ctx` 这类不透明参数传进组件的写法会被判成静态，本表「推进」首选件 `PhaseRail` 恰好如此，判 P0 等于"照本表写、门禁拦你"。
> · **不做降级**：没有"本镜"这一层，无级可降。
>
> 取舍与本仓库其它判据一致：**宁可少报，也不要假报告**（更复杂的旧判法在接触表上抓到的真缺陷与本版是同一批）。
> 实例：`assets/lecture-template` 8 镜全过；`overview-film` 的 S2 把 `MetricGrid` 换成手绘行 + `Chart`、只在注释里留名 → P0。
> 夹具：`scripts/negative-gate-check.py` 的 **AF / AG / AJ / AK**（AF 名字不存在、AJ 只在注释里 → 必须拦；AK 原样模板必须全过；AG 见上）。

### 3. 留白预算：先标定，再定阈值

**标定方法**：对成片 `demo-video`（8 镜 / 1453 帧）数每镜最长的"无新增窗"（镜内相邻 beat 之间、镜首/镜尾到最近 beat 的帧数）。

| 镜 | 时长 | beat 数 | 相邻 beat 最小间隔 | **最长"无新增"窗** |
|---|---|---|---|---|
| S1 | 333 | 5 | 50 | **134** |
| S2 | 106 | 2 | 106 | 106 |
| S3 | 184 | 3 | 80 | 104 |
| S4 | 167 | 3 | 80 | 87 |
| S5 | 158 | 3 | 78 | 80 |
| S6 | 141 | 3 | 69 | 72 |
| S7 | 106 | 3 | **9** | 97 |
| S8 | 258 | 4 | **8** | 96 |

**标定结论**：
- 每镜都已有 ≥72 帧（2.4 s）无新增窗，所以"留白 ≥30 帧"**等于没检查**，不能照抄。
- **`hold ≥ 40 帧（1.33 s）`** 为 P1：低于它点名不拦；低于现状最小值 72 留 32 帧余量，不误伤现有片，又能拦住"每 20 帧蹦一个新元素"的过载镜。
- **P1：相邻 beat < 20 帧**（现状有 9 / 8 帧两处）→ 提示"两件事挤在一拍"，**不阻断**（节奏问题，不是对错问题）。
- ⚠️ 两条都来自真实数据标定；新长片出来后要用新数据再标定一次。

### 4. 落到门禁（`validate-presentation.py` 的 G-14/G-15/G-16）

| 判据 | 检查 | 级别 |
|---|---|---|
| G-14 `move` 闭合 | 每镜必填 `move` 且属于 §2 的 10 个名字；同一 `move` 不得连续 ≥3 镜（**连续 3 镜起即点名**，口径见 §2 的注） | 不在闭集（拼错）P0；缺 `move`、连续 ≥3 镜 P1 |
| G-15 `evidence` 用在源码里 | 见 §2 的判法：名字必须**作为 JSX 用法**出现在该工程的场景源码里（**不做本镜作用域、不做帧驱动判定** —— 代价见 §2） | P0 |
| G-16 误解与留白 | `misconception` 或 `noMisconception`+`why` 二选一；`hold` ≥ 标定值 | 两者同时写 P0；缺写、`hold` 不足 P1 |
| G-17 `known → new` 闭合 | 相邻镜的 `known` 能在前面某镜的 `new` 里找到（或标为常识锚点） | P1 |

**为什么能机械检查**：这些字段都是**声明**，可以查枚举闭合、指向、阈值、跨镜一致性——**不靠自觉，靠"写出来 + 被检查"**。

### 5. 与既有文档的关系

本表决定**这一镜做什么事**（动作、误解、留白）；第二张表（`media.md#media-routing` 的"修辞动作 → 组件"）决定**用哪件做**；
`checks.md#presentation-gate` 检查**讲与画对不对得上、读不读得过来**（T1 纯算术）。

<a id="narrative-hook"></a>

## Cold-open narrative contract

The first ten seconds are a retention beat, not an introduction. Start from the most consequential **verified** result, conflict, reversal or concrete scale in the finished story; then temporarily withhold the explanation and return to it later with evidence.

### Required opening shape

| Design time | Required job | What it looks/sounds like |
| --- | --- | --- |
| 0–1.5s | Immediate payoff | The largest verified fact or visible outcome appears before a title card, greeting or context sentence. A hero object enters or changes state within 0.5s. |
| 1.5–4s | Stakes or tension | State why that result is surprising, difficult, risky or consequential. Prefer a precise contrast over a vague question. |
| 4–8s | Open loop | Promise the explanation without resolving it: name the mechanism, constraint or unanswered question that the main body will unpack. |
| 8–12s | Pivot | Begin normal context and show the first evidence path. Do not repeat the opening claim verbatim. |

The hook must work with sound off: one large, specific claim and one visual consequence in the first four seconds (a number, outcome, before/after contrast, unresolved constraint or rare capability), never exaggerated beyond the sources.

### Callback and payoff

For every cold open, put three entries in `storyboard.md`:

1. `Opening payoff`: the exact verified claim or image shown first.
2. `Deferred question`: the mechanism or tension intentionally held back.
3. `Callback / payoff`: the later scene and narration line that answers it, normally before the final 25% of the video.

The callback must add evidence or causality, not repeat the headline (open on “十万卡已真机亮相”, defer “十万张卡为什么不是简单堆卡”, answer through compute, fabric, storage and cooling).

### Writing rules

- Lead with the consequence, not the chronology (not “在某展会上，一台设备亮相”).
- One sharp angle only (scale, reversal, constraint, trade-off or real-world consequence); never stack claims in the opening sentence.
- No generic openings (“你知道吗”“今天我们聊聊”“最近很火”“一台机器被围住了”) unless the next clause gives the concrete payoff.
- No source lists, definitions, caveats, chapter explanation or slow logo reveal before the payoff; qualifiers go in the pivot or callback.
- Keep the open loop honest: if sourced evidence cannot answer it, do not open it.

### Visual rules

- Begin with a completed consequence, contrast or tension, not neutral decorative cards being assembled.
- One oversized hero statement plus at most two supporting elements; keep the fixed camera, paper style, subtitle and chrome contract.
- The chapter label may appear only after the payoff is legible and must not cover or delay it.
- The callback reuses the opener's hero object, number, rail, module or status state so the viewer recognizes the answer.

### Three proven first-sentence templates

Write the first spoken sentence from one of these shapes, then verify it against the source. Rule: the core result or conflict goes in the first sentence. Reason: viewers decide whether to stay before any context is given, so context-first openings waste the only seconds that decide retention.

1. **Result first** — state the verified outcome before any context: "一条命令，能让你写崩的代码一秒回到十分钟前。"
2. **Curiosity gap** — name a mistake or blind spot most viewers do not know they have: "你花399买的课，GitHub上大概率有人免费开源了。"
3. **Conflict / contrast** — open on the concrete disaster or before/after gap the video resolves: "两个人改同一个文件，一提交，队友三天的代码直接消失。"

Never open with audience labeling or roadmap sentences ("作为XX专业的学生…", "上一课我们学了…", "这一期我们聊聊…"). Series continuity references belong after the pivot, never in the first sentence.

### First-three-seconds motion density

Rule: the first three seconds carry several distinct visual changes. Reason: a single slow title pop reads as a still image, which at second one looks like a loading screen.

- at least **three distinct visual actions** inside the first 90 native frames (hero statement lands, then two supporting elements enter or change state);
- the hero statement is a full-screen hammer frame (displayL or larger) that lands within 45 frames, with one short accent sound at its landing frame — it counts as one of the film's 2–3 hammer frames; build it as described in director.md#pacing-rhythm;
- the regular multi-zone layout and chapter chrome begin only after the hammer frame has been legible for at least 1 second.

### Opening review gate

Before full render, range-render 0–360 native frames and inspect at 0.5s, 2s, 4s, 8s and 10s. Reject and rewrite the opening when any condition is true:

- the primary claim is not visible by 1.5s;
- the first spoken sentence is generic context rather than a consequence or tension;
- the visual is understandable only after reading a later caption;
- the open loop has no identified callback in the storyboard;
- the opening contains an unsupported superlative, implication or performance comparison.

<a id="pacing-rhythm"></a>

## Pacing and rhythm contract

A film whose chapters all share one structure, density and speed loses viewers after a minute even when each scene is good. This contract makes energy rise and fall on purpose; the hook (`director.md#narrative-hook`) wins the first ten seconds, pacing keeps the rest.

### Hammer frames

Plan two or three hammer moments per film (roughly one per 60–90 seconds, never in adjacent chapters) — the **only** exception to SKILL.md's rule that regular shots never become full-screen text pages. A hammer moment is a chapter's single most quotable line as a full-screen statement:

- one oversized sentence (displayL or larger) on an otherwise nearly empty paper, held 1.5–2.5 seconds;
- all other zones exit completely before it enters; the multi-zone layout resumes after it;
- place it on the narration line it quotes, timed from the cue table like every other element;
- choose lines that reverse an assumption or compress the chapter ("冲突不是报错，是 Git 在问你意见"), not summaries;
- **how to build it** — component route: a `StampBanner` (or a `Callout` at displayL) alone in its shot; hand-made route: the sentence hand-lettered across the page with `HandLettering`, or stamped as a large `Seal` — the line lives in the medium, not as plain type on blank paper.

Mark each hammer frame in `storyboard.md` with `Hammer:` plus its cue number so the reviewer can check the beat spacing.

### Fast and slow chapters

Alternate chapter energy instead of keeping one speed:

- **Slow chapters** (new concepts): fewer elements per beat, longer holds, state changes every 3–4 seconds.
- **Fast chapters** (procedures, lists, montages): denser entries, state changes every 1.5–2.5 seconds, clipped holds.
- Never two slow chapters back to back; separate them with a fast chapter or a hammer frame.

With a chapter-segmented TTS adapter, give each paragraph a style instruction (calmer, slightly slower for slow chapters; brisker for fast chapters and the hook). One voice; vary delivery, not identity.

### Chapter breathing

Between chapters insert a breath of 0.5–1 second: the outgoing scene completes its exit, the paper stays briefly empty except chrome, then the incoming chapter's first element starts growing in (see draftpaper.md#reveal-rules). Do not butt the last element of one chapter directly against the first element of the next. The `chapter` sting and the `page` flip mark this breath.

### Ending beat

The final chapter drops density on purpose: at most three elements (wrap-up line, mascot, closing card) so the film visibly lands instead of stopping mid-texture.

For knowledge films the closing card is a save hook, not a follow plea (algorithms weight saves and shares above completion for this genre): name the future moment they will need it ("点个收藏，下次写崩了翻出来照着敲") and pair it with a code-drawn star that draws its outline and fills on the spoken word. For a series, add a one-line next-episode teaser under the save card; platform references stay at the compliant "主页可以查看" wording, no account names or links.

### Review gate

Before the full render, check on the contact sheet or range renders:

- hammer frames exist, are alone on screen, and are spaced by at least one chapter;
- no two adjacent chapters share the same energy level in the storyboard table;
- every chapter boundary shows the breathing gap;
- the last scene is visibly sparser than the body chapters.

<a id="style-recipes"></a>

## 风格配方：把一种"观感"拆成可执行的八个轴

> "风格"不是参考图或滤镜，而是一组**互相约束的决定**——最关键的是**这个材料会做、别的材料做不出的那个动作**。
> 写清八个轴，再写清"它不是什么"和"它的坑"。拆法参考 lemo-opuscar（MIT，© 2026 LemoLab）的 `styles/*/STYLE.md`；配方内容为原创，不是译文。

### 八个轴

| # | 轴 | 要回答的问题 | 落在本项目的哪里 |
|---|---|---|---|
| 1 | **材料** | 画面是"什么东西"做的？纸的种类、颜料、光从哪来 | 皮肤背景三张图、`Paper` 卡片皮、`FibreOverlay`、`Grade` |
| 2 | **颜色分工** | 底色家族、正文墨色、**唯一**强调色、什么颜色永远不出现 | `palette`（`*Ink` 文字安全色）、`THEME.craft.accent` |
| 3 | **字** | 正文 / 标题 / 批注各用什么字体；字幕长什么样（不是 UI 胶囊） | `aesthetic.subtitleSize/Family`、`SubtitleChrome`、`Chrome` |
| 4 | **运动质感** | 东西怎么动：平滑缓动？12 fps 跳帧？墨水速度？纸的落定过冲？ | craft 组件的 `prog` / `stepped`、动作助手 |
| 5 | **镜头语法** | 推、拉、横移、俯视台面、跟着笔尖走——各在什么情况下用 | 镜头表 `cinema`、treatment 的 `shots[].move` + 理由 |
| 6 | **换场** | 在媒介内部换场：翻页、换一张纸、剪刀剪过、墨晕开、灯台换片 | `transition`（`slide` / `drop` / …），皮肤 `craft.transition` |
| 7 | **声音** | 物质的声音：纸、笔、剪刀、印章、灯台开关；"安静 → 最重要的那一声" | `public/sfx/lib/`（Kenney CC0 拟音） |
| 8 | **原生动作** | 只有这个材料做得出的 2–4 个动作，留给顿悟点 | craft 组件组合（[components.md#craft-kit](components.md#craft-kit)） |

每个配方还要写两段：
- **不是什么**：最容易做成的那个假货（"矢量插画套水彩滤镜""红色背景上放红字"）。
- **坑**：这个媒介实际做时最常翻车的地方（可读性、色彩纪律、性能、同质化）。

### 已实现为皮肤的三个配方

#### journal · 博物学家手账（[themes/journal.md](themes/journal.md)）
1. 材料：暖白棉纸，纸纤维，胶带贴上去的纸片和照片；光是均匀的桌面光。
2. 颜色：纸色家族 + 深棕墨；强调只有朱砂；淡彩用雨水蓝、鼠尾草绿（只做大面积淡彩，不写字）。
3. 字：批注用楷体手写感；字幕是**直接写在纸上的宋体墨字**，下面垫纸色光晕。
4. 运动：墨线按书写速度长出来；水彩 1 秒左右晕开、边缘先深；纸片放下时有一点落定。
5. 镜头：俯视本子；沿着一页横移像翻看；推近到批注；招牌镜头常是放大镜压上真照片（手写场景路线；auto 路线的 page 版式图版占满整页高，相机推不进，auto 片的招牌镜点 flow / list / compare，自动横移扫镜）。
6. 换场：同一页上横移（`slide`）、新的一页盖上来（`drop`）。
7. 声音：笔尖、纸张摩擦、胶带、翻页。
8. 原生动作：晕染即揭示；标本 + 引线批注；放大镜压在贴进来的真照片上；雾洗回白纸（结尾回到空白页）。
- 不是：矢量插画加水彩滤镜；暗底；UI 胶囊字幕。
- 坑：淡彩上写字对比度不够（字只写在纸上）；满页批注变成笔记截图（一帧 ≤3 处文字）。

#### papercut · 红色窗花剪纸（[themes/papercut.md](themes/papercut.md)）
1. 材料：米色宣纸上平铺红纸剪片；细节只来自"剪掉了什么"（洞就是线）；正面光，纸有厚度。
2. 颜色：米色纸家族 + 中国红主材；靛青 / 玉绿只做配角纸；金箔全片只用一次。
3. 字：宋体；字幕是一条深红横批，米色字。
4. 运动：12 fps 跳帧（剪纸动画的手感），纸片落定无弹簧。
5. 镜头：正面平视为主；推近到镂空细节；对称构图。
6. 换场：一张新纸盖上（`drop`）、剪刀沿线剪开。
7. 声音：剪刀、纸片落桌、印章。
8. 原生动作：对折一刀展开成多份；碎片飞回原位（纠错 / 修复）；剪掉一角；背光透过洞。
- 不是：红背景上放红东西；渐变、描边、发光。
- 坑：红压红看不清（底永远是米色）；镂空太细在 1440p 下糊成一片。

#### archive · 档案灯台（[themes/archive.md](themes/archive.md)）
1. 材料：冷白背光台面，上面摆真实档案物件（扫描件、老照片、手稿、显微照片）。
2. 颜色：冷灰白 + 近黑墨；一个信号色（橙红）只做标注、读数、锚点。
3. 字：宋体标题 + 编目签小字；字幕是白色标签条。
4. 运动：物件平稳放下；放大镜落定；几乎没有装饰动画。
5. 镜头：俯拍台面；推近到物件细节；拉远变成索引（很多物件排成网格）。
6. 换场：台面横移到下一件（`slide`）。
7. 声音：灯台开关、纸袋、相纸、安静的房间。
8. 原生动作：镜片里负片转正；一行字亮起；两份记录并排比对；拉远成索引。
- 不是：做旧滤镜、咖啡渍、"复古"字体；生成的假档案。
- 坑：物件必须是真的（Commons / Openverse 找不到就换媒介）；署名必须上屏。

### 只写了配方、还没做成皮肤的方向

这些方向按同样八轴写好，需要时照它实现一套皮肤（`theme/<id>.tsx` + 三张背景 + `references/theme-<id>.md`）。

| 配方 | 材料 / 颜色 | 原生动作 | 适合 | 不是 |
|---|---|---|---|---|
| risograph 孔版印刷 | 粗纸 + 2–3 种荧光专色叠印，套版偏移 | 两色叠出第三色；套版错位再对齐 | 叠加、混合、"两件事合起来变成第三件" | 平涂矢量加噪点 |
| engraving 铜版雕刻 | 白纸黑线，排线密度表达明暗 | 排线一层层刻出体积；局部放大见线 | 19 世纪科学、解剖、机械 | 照片加"素描"滤镜 |
| whiteboard 白板 | 白板 + 马克笔，手在画 | 边讲边画，擦掉重画 | 推导、流程、"一步步想" | 白底 PPT |
| one-line 一笔画 | 一根连续的线 | 一根线变成另一个东西（形变） | 转化、连续性、"其实是同一个" | 多笔描边插画 |
| pictogram 图标人 | 等宽几何人形、统一网格 | 一个人变成一群（数得出来的多） | 人口、统计、比例 | 扁平插画角色 |

### 选配方的检验

1. 把题目换成邻近的题，这个材料的原生动作还"刚好"吗？还刚好 = 选得太泛。
2. 顿悟那一秒，换成 flat 皮肤还能做吗？还能 = 媒介没用上。
3. 静帧去掉字幕，观众能认出这是什么材料吗？认不出 = 材料轴没做足。

<a id="visual-director"></a>

## Visual director: image, text and graphic modes

Read before storyboarding. The skill does not call an image-generation model: images come from the user, Wikimedia Commons / Openverse ([media.md](media.md#commons-media)) or other licensed sources.

### 1. Choose the visual mode from meaning

Assign exactly one primary mode to every scene before building it.

| Scene meaning | Primary mode | Typical treatment |
|---|---|---|
| Concrete object, place, person, atmosphere or visual transformation | `image-text` | User-supplied, Commons / Openverse or licensed image plus Remotion labels, highlights, arrows and conclusion text |
| Contrast, slogan, misconception, keyword or emotional beat | `pure-text` | Scale, replacement, underline, staggered explanation and typographic rhythm |
| Process, system, relationship, quantity or state transition | `pure-graphic` | SVG paths, nodes, tracks, cards and state changes |

Do not force a bitmap into an abstract relationship.

### 2. Where images come from

Commons / Openverse first (`commons-search.py`, see [素材](#director-method)), then user files or clearly licensed assets. If nothing fits, keep the storyboard and draw the layer with native SVG / Remotion components; do not block the video.

### 3. Prepare assets for animation

The raster is an input layer, never the finished video. Pick or crop it so that:

1. it shows the subject and serves the explanation;
2. it fits the active skin's look;
3. it matches 16:9 or the exact target crop;
4. one side or region stays visually quiet for overlays;
5. subjects that will be highlighted are separable;
6. it carries no baked captions, labels, charts, logos or UI text you need to change;
7. the subtitle safe area is free of clutter.

Diagrams, arrows, exact labels and data are SVG/HTML in Remotion: images give atmosphere and objects, Remotion gives exact information.

### 4. Register provenance

Store each used raster in `public/illustrations/` and record it in `manifests/visual-assets.json` with: stable ID and relative path; `source_type` (`ai-generated`, `user-supplied`, `licensed-third-party` or `code-generated` — procedural, e.g. the craft-skin backgrounds, matching `backgrounds.json` `source.kind: procedural` and NOTICE); provider or source URL when applicable; prompt summary or original-asset description; intended scene and crop policy; rights note; `baked_text: false` when the image carries no text (legacy `ai-generated` backgrounds keep their existing records).

No unused images in the deliverable; never commit an asset with uncertain redistribution rights.

### 5. Animate image and information separately

Bitmap, each callout, arrow and explanation line are independent parts:

- the image gets a restrained reveal, crop wipe or 2–5% push-in;
- callouts come only after the image is recognizable, each timed to its narration phrase;
- annotations leave before the image exits when the next scene changes subject;
- text stays live Remotion typography, never text inside the bitmap;
- prefer one image with two or three sequential annotations over several static image cards.

### 6. Enforce scene lifetime

Scene windows and layer ownership follow [technique.md](technique.md) (start-inclusive, end-exclusive; at scene end unmount the whole group or drive every obsolete part to zero opacity or fully outside the canvas). Before the next scene enters, inspect:

1. last readable hold;
2. middle of exit;
3. first clean frame;
4. first frame of the next scene.

No outgoing label, hidden corner, arrow head, shadow or image crop may remain beneath the next scene.

### 7. Review for video, not slides

Reject the scene if the image merely sits on a card beside unrelated text; image and overlays must answer the same question in the same few seconds. Typical rhythm:

`recognize image → locate object → explain relation → land conclusion → clear scene`

Across the film, vary the primary mode with the content so it never feels like a moving slide deck.
