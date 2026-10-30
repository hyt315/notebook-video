# 导演层：先找"只属于这个题"的东西，再动手

> 3.3.0 新增。适用：每一条片子，尤其是手作皮肤（journal / papercut / archive）。产物：`manifests/treatment.json`，
> 由 `scripts/validate-treatment.py` 检查（手作皮肤缺它或没填完 = P0；flat / cel 缺它 = P1 提醒）。
>
> 方法来源：lemo-opuscar 的 DIRECTOR.md（MIT，© 2026 LemoLab，<https://github.com/lemomo-ai/lemo-opuscar>）的思路——
> 先对标、媒介原生动作、三候选结构、风格帧先行、一轮修改——以及用户第三季十条片子的实战复盘；
> 独立评审回路借鉴 motion-video-kit（MIT）的 "builder ≠ judge"。本文是 notebook-video 自己的写法，不是译文。

> 配套：开场钩子 [narrative-hook.md](narrative-hook.md)、节奏 [pacing-rhythm.md](pacing-rhythm.md)、运镜 [camera-language.md](camera-language.md)。

## 为什么要这一层

蓝图（concept / process / …）告诉你"讲什么顺序"，组件表告诉你"画什么卡片"。两者都不回答最要紧的问题：
**这件事，用什么东西演出来，观众才会"啊——原来是这样"？**
不回答它，片子就会落进同一个模板：名词 → 定义 → 拆开 → 升华，画面是卡片里放组件。

## 七步（按顺序，每步写进 treatment.json）

### 1. 一个生活里的问题（`question`）
第一秒就要能问出口的那句话，观众自己遇到过："咖啡渍为什么总是一圈深边？""'细胞'这个词，最早是什么意思？"
不是"今天我们来了解 XX"。

### 2. 只属于这个题的隐喻（`metaphor`）
找一个**换个题就不成立**的形象。检验：把题目换成邻近的另一个题，这个隐喻还能用吗？能用 = 太泛，重找。
- 好：二维码本来就是"黑白剪纸"——深色模块是纸，浅色模块是洞（纠错码）。
- 差："知识的大门""信息的海洋"。

### 3. 媒介即隐喻（`medium`）
选一个皮肤 / 媒介，让**物质本身**就在讲这个道理。写清"为什么是它"：
| 媒介（皮肤） | 它天生会做的事 | 适合 |
|---|---|---|
| `journal` 手账水彩 | 观察、记录、晕开、批注、贴照片 | 发现、实验、自然、"有人第一次看见" |
| `papercut` 红色剪纸 | 剪掉、对折复制、镂空、碎片回位、背光透洞 | 对称、复制、冗余、结构、缺了还能补 |
| `archive` 档案灯台 | 真实物件、放大镜、负片转正、并排比对、编目 | 考据、溯源、"这话最早谁说的"、真实数据 |
| `flat` / `cel` | 组件、仪表盘、代码、流程 | 软件、产品、操作教程 |
更多媒介的"配方"（risograph、engraving、whiteboard、one-line…）见 [style-recipes.md](style-recipes.md)。

### 4. 一个原生动作（`native_move`）——放在顿悟点
**只有这个媒介做得出**的那个动作，放在观众理解发生变化的那一秒：
水彩在镜头前晕开干透、自己圈出深边；对折剪一刀，两份同时坏；放大镜压上去，镜片里的负片转正。
写清：做什么、在第几秒、为什么换成别的媒介就做不出。没有原生动作的顿悟点，只能是"一个数字滚到位"。

### 5. 三个候选结构，选一个（`candidates` + `chosen` + `chosen_why`）
每个两三行：形状（一次旅程 / 前后对比 / 倒计时 / 一个清单逐条翻转 / 错误猜想被推翻……）、开头画面、结尾。
第一个想到的往往是这个媒介的陈词滥调；写满三个再选。

**选结构族（3.3.0 起检查）**：每个候选写 `family`，三个候选**至少来自 2 个族**（否则只是同一条曲线的三种写法，validate-treatment 记 P1）。
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

### 5b. 声音设计（`sound`）
静音片也要设计声音（3.3.0 起检查，缺项 P1）。`treatment.json → sound` 每项的意思：

| 字段 | 意思 | 示例 |
|---|---|---|
| `bed` | 底噪 / 环境声，全片垫底 | "安静的书房：纸面极轻的摩擦" |
| `foley` | 哪些动作配什么材料声 | ["刀片划过软木：短促的擦声"] |
| `silence` | 顿悟前那次安静在第几秒（原生动作前留白） | "21.0–21.8 s 全静，放大镜落下前" |
| `most_important_sound` | 全片最重要的一声：什么声音、第几秒（要比别的都突出） | "22.0 s 放大镜落定：木头轻磕" |
| `music.use` / `music.why` / `music.mood_curve` | 用不用配乐、为什么；用就写情绪曲线 | `{"use": false, "why": "素材库尚未接入，留白优于凑数"}` |
| `foley_per_medium` | 每种媒介动作对应的拟音 | ["画线：铅笔划纸", "晕染：湿笔刷", "盖章：印泥按压"] |

响度目标 −16 LUFS（静音旁白片同样）。

### 6. 对标：学什么、不学什么（`benchmark`）
挑一两部真实作品（纪录片、片头、绘本、展览），写"学：构图 / 节奏 / 镜头语法 / 配色逻辑"和"不学：角色、具体镜头、旋律、字体"。
同时勾掉同质化清单（`avoid`）：暗底发光线、粒子、金色 / 冰蓝科技风、电子 BGM、名词→定义→升华模板。

### 7. 镜头表要写"为什么"（`shots`、`signature_shot`）
每镜：景别（全 / 中 / 近 / 特写 / 插入）、运镜（推 / 拉 / 横移 / 跟 / 静）、**理由**。全片 ≥4 种运镜，一个招牌镜头。
**景别写了就要兑现**（3.3.0）：`validate-treatment` 拿 treatment 的 `move` / `framing` 对照镜头表的 `cameraIntent` 和实际缩放；
招牌镜头至少真推 12%（keys 缩放或 `cinema.focus` 的 zoom），否则手作皮肤 P0。动机、景别阶梯、视线连续、什么时候不动、镜长：
见 [camera-language.md](camera-language.md)。
转场在媒介内部完成（翻页、换一张纸、剪刀剪过、墨晕开），不用缺省的淡入淡出 / 甩镜。
关键时刻主体 ≥1/3 画高；每个构图 ≤12–15 秒；关键揭示后留 2–3 秒呼吸。
"节拍边界要有东西活下来"：上一拍的某个物件变成下一拍的起点，片子才连成一条线而不是幻灯片。

## 素材：每个选题先搜 Commons（`commons`）

```text
python scripts/commons-search.py search "<英文关键词>" --project ./my-video            # 图
python scripts/commons-search.py search "<关键词>" --type audio --project ./my-video   # 真实的声音
python scripts/commons-search.py search "<关键词>" --source openverse --project ./my-video
```
真东西（1665 年的铜版画、第一张 X 光片、真实的显微照片、一段历史录音）几乎总能让片子更好。
搜过就会记进 `manifests/commons-log.json`；门禁要求手作皮肤至少搜过一次。找到能用的就 `add` 进来，放进
`ArchivePhoto` / `PinnedPhoto` / `LoupeMedia`（见 [craft-kit.md](craft-kit.md)），署名自动上屏。没找到也没关系——写清搜了什么。

## 事实（`facts`）
每个数字、日期、人名：打开原始出处，写 `url` + 原文引文 `quote`。区分实验条件（"在真空中"、"小鼠"）。

## 先做风格帧，再做全片
1. 写完 treatment.json；
2. 做 3 张风格帧（其中一张是招牌镜头 / 最难的那一镜）：`make-video --stills` 看图，不像就改媒介或改隐喻，不要硬上；
3. 全片；`--stills` 联系表两遍；关键动作 0.2 秒连帧；
4. **独立评审**（做的人不评自己）：开一个新会话 / 子 agent，**只给它三样东西**：`--stills` 联系表、工程根目录的
   `storyboard.md`、`manifests/treatment.json`，不给任何过程记录。按七项 1–10 打分：
   构图主体、调度节奏、隐喻与媒介一致、顿悟惊艳、字幕可读、手作质感与色彩纪律、叙事完整；问题分 P0 / P1 / P2 列出。
   <8 的改完再评，分数、问题与处理写进 `treatment.json → review.rounds`（时间、评审者、问题、处理）。
   - `storyboard.md` 由 `resolve-shots` 从 `manifests/shots.resolved.json` **自动生成**（3.3.0）：片名、总帧数、时长、皮肤，
     每镜一行写起止秒、景别、运镜、意图缩放 / 实际缩放、转场、背景、主要组件、字幕摘要。文件头有"自动生成"标记，手改会被覆盖；
     如果你手写过 storyboard.md（没有标记），不覆盖，生成的那份写到 `storyboard.generated.md`——评审用生成的那份。
5. 一轮修改把所有问题改完，再渲整片。手作皮肤 `review.rounds` 为空时 `make-video --render` 会停下并说明原因；
   草稿 / 自测确实要跳过，显式加 `--skip-review`。

## treatment.json 字段一览
见 `assets/lecture-template/manifests/treatment.example.json`（复制成 `treatment.json` 再填）。门禁规则：

| 检查 | 手作皮肤 | flat / cel |
|---|---|---|
| treatment.json 存在、必填字段非空、不留 `<<…>>` | P0 | P1 |
| 恰好 3 个候选，`chosen` 指向其中之一 | P0 | P1 |
| `medium.skin` 与工程的皮肤一致 | P0 | P1 |
| `native_move.at_sec` 在片长内 | P0 | P1 |
| 每个 `facts` 有 http(s) 链接和引文 | P0 | P1 |
| 搜过 Commons（`commons-log.json` 至少一次）且 `commons.used` 都在 media.json 里 | P0 | P1 |
| `turn_to_you_sec` 落在片长 35–55% | P1 | P1 |
| 镜头表每镜有理由；运镜 ≥4 种；有 `signature_shot` | P1 | P1 |
| 招牌镜头实推 ≥ 12%（对照 shots.resolved.json，3.3.0） | P0 | P1 |
| `move` = 镜头表 `cameraIntent`；`framing` 与实际缩放 / 主体占比相符（3.3.0） | P1 | P1 |
| `review.rounds` 最后一轮七项都 ≥8 | P1 | P1 |
