# 草稿纸讲解：出现规则、设计规范与动效

「讲到哪长到哪」的规则本体：什么时候出现、怎么长出来、版式配色与动效纪律。

本篇各节：

- [出现规则（草稿纸讲解）](#reveal-rules)
- [草稿纸讲解 · 设计规范](#draftpaper-design)
- [Motion design contract](#motion-design)

<a id="reveal-rules"></a>

## 出现规则（草稿纸讲解）

**草稿纸讲解**：画面像一张边讲边写的草稿纸——讲到哪，长到哪。画面上没有笔，也不要求什么都画成线稿；组件、图片、文字照常用。这份规则只管**什么时候出现、怎么出现**。

**四条规则**

1. **跟着旁白**：一样东西在讲到它的那句话开始时才开始出现，不提前。同一句里有几样东西，按先后排开。
   **本镜长完**：每样东西在切镜前 4 帧长完；放不下时 compose 先把展开压到 12 帧，仍放不下就提示删元素或拆镜。标注总在它标的东西长完 2 帧后才开始。
2. **长出来**：不淡入、不弹出、不从下面浮上来。文字和卡片左→右展开（展开边按字边界落：边线只停在字与字之间，不会把一个字切成半个——`src/glyph-snap.tsx`）；线稿一个部位一个部位描出来，方框和圆圈也是沿边描；标注随讲随画。只有照片、截图可以整件出现，也要等讲到它的那句。
3. **不扎堆**：同一镜里，相邻两样东西开始出现至少隔 12 帧（0.4 秒）；同一时刻最多 2 样在长。
4. **不预铺**：镜头切进来时，纸上只有已经讲过的东西；开镜头 6 帧内最多 1 样东西开始出现。

**参数（30 fps）**

| 东西 | 怎么长 | 用时 |
|---|---|---|
| 文字、卡片、清单项 | 左→右展开（线性） | 字数 × 4 帧，最少 12、最多 45 |
| 代码行 | 左→右展开（线性） | 字数 × 1.5 帧，最少 12、最多 24 |
| auto 的数字 | 整串左→右展开，直接写终值（不滚动、不放大） | 字符数 × 4 帧，12–45 |
| 没有字的块 | 左→右展开 | 宽度 ÷ 40 帧，12–45 |
| 线稿 | 按部位依次描，底座最后 | 12 × 部位数，24–45 |
| 线稿被点名 / 换态 / 打勾 / 计数 | — | 12 |
| 圈注 | 沿路径描 | 14 |
| 下划线、箭头 | 沿路径描 | 12 |
| 手写小字 | 逐字写 | 24 |
| 术语小注 | 左→右展开 | 10 |
| 模板 `enterAt()`（手写场景路线） | 左→右展开 | 22 |
| `MagnifyInset` 方框 | 沿边描，描完再铺淡底 | 16 |
| 带 `reveal: "type" / "slide"` 的文字 | 逐字写出，外框不再展开 | 该句时长 −4 帧（10–72） |
| 手账页的图版、照片、截图、放大镜（承载层） | 贴上（整件出现） | 等讲到它的那句；同样计入「不扎堆」 |

**auto 路线**：以上全部由 `compose-story.py` 的排程（`schedule_reveals`）和 `auto.tsx` 自动做到；排完以后东西只会比你写的晚、不会早。一镜东西太多、讲完了还在长，compose 会提示「删 1–2 个元素或拆成两镜」。

**手写场景路线**：用 `enterAt(f, at(n))` 把每个元素绑到讲到它的那一句；同一句里多个元素写成 `at(n) + i * 12`；不要在开镜第 0 帧摆好东西。

**怎么量**：`python scripts/measure-reveal.py <工程> [renders/preview-*.mp4]`。静态部分看 `same`（同帧开始，应为 1）、`gap`（相邻开始间隔，应 ≥12）、`conc`（同时在长，应 ≤2）、`pre`（开镜预铺，应 ≤1）；给了预览视频还会算**镜内生长比 G**（每镜最后一帧的内容里，有多少是开镜 0.8 秒后才长出来的）：每镜 ≥0.45、中位 ≥0.60 算合格，中位 ≥0.75 算好。只报告，不拦。

更完整的目标规则（全片一张纸、跟随生长的镜头、出现注册表门禁）另有专门规则，见 [components.md#journal-page](components.md#journal-page)。

版式、配色与组件搭配见 [draftpaper.md#draftpaper-design](draftpaper.md#draftpaper-design)。

<a id="draftpaper-design"></a>

## 草稿纸讲解 · 设计规范

「草稿纸」指的是**讲述方式和出现方式**：画面上没有笔，也不要求笔迹；组件、图片、文字照常用；所有东西讲到哪长到哪，和旁白同步，不整块弹出；版式和搭配要帮人理解，也要好看。时间单位为 30 fps 下的帧（f），空间为设计坐标 1920×1080 下的 px。

### 1. 出现规则

1. **绑词**【引擎保证】：每样东西从讲到它的那句话开始出现，不提前。文字、数字在所讲词头前 4 帧开始；引线在词头前 6 帧，标签在引线完成后接上；线稿最早在词头前 20 帧开始，60% 的笔画在该词结束前完成；结论印章、勾在最后一个音节处。
2. **本句、本镜长完**【引擎保证】：每样东西在切镜前 4 帧长完；放不下时先把展开压到 12 帧，仍放不下就删元素或拆镜。说完一句之后才开始出现的东西，应当属于下一句。
3. **长出来，不整块**【引擎保证】：文字、卡片、清单项、代码行左→右展开；线稿一个部位一个部位描出（外轮廓 → 内部 → 细节，底座最后）；方框、圆圈、下划线、箭头沿路径描出；字先描轮廓再填色。不用透明度、缩放、位移做出现。单个元素单帧进度增量 ≤0.35。只有证据类照片、截图可以「贴」（整件 10–14 帧落下），每镜 ≤1 次，面积 ≤画面 30%，也要等讲到它。
4. **不扎堆**【引擎保证】：同一时刻最多 2 样东西在长；同一镜里相邻两样东西开始出现至少隔 12 帧（0.4 秒）；一组同类小东西（几根柱、几个格、几个点）算 1 样，组内错开 2–3 帧，整组 ≤45 帧。
5. **不预铺**【引擎保证（auto）/ 作者遵守（手写）】：切进新镜时纸上只有已经讲过的东西；开镜 6 帧内最多 1 样东西开始出现；不先摆空框、灰色占位条、空心圈再往里填。
6. **标注在后**【引擎保证】：圈、下划线、箭头在它标的东西长完 2 帧后才开始；每句 ≤1 次强调，每镜 ≤3 次；多步组合按「荧光 → 圈 → 箭头 → 批注字」，相邻间隔 2–6 帧。
7. **改错留痕**【作者遵守】：错值用灰色正常写出 → 「不对」词头后 1 帧划一道近水平删除线（7 帧，≤10°，覆盖 120% 字宽）→ 停 ≥6 帧 → 在旁边用强调色写对的值 → 回头圈。错值留在纸上，不擦、不淡出、不原地变形。
8. **停顿与呼吸**【作者遵守】：句间 ≥9 帧不长新东西；一组意思结束 12–18 帧；关键结论后「想一想」24–36 帧、镜头不动；讲解中任意 36 帧内至少有一样东西在长（刻意呼吸 ≤60 帧、每镜 ≤1 次）；结尾停留 36–60 帧。
9. **时长参考**【引擎保证】：

| 东西 | 怎么长 | 用时 |
|---|---|---|
| 文字、卡片、清单项 | 左→右展开 | 字数 × 4 帧，12–45 |
| 代码行 | 左→右展开 | 字数 × 1.5 帧，12–24 |
| 数字（auto） | 整串左→右展开，直接写终值 | 字符数 × 4 帧，12–45 |
| 没有字的块 | 左→右展开 | 宽度 ÷ 40 帧，12–45 |
| 线稿 | 按部位依次描 | 12 × 部位数，24–45 |
| 线稿被点名 / 换态 / 打勾 / 计数 | — | 12 |
| 圈注 | 沿路径描，1.12 圈，左上起笔 | 14 |
| 下划线、箭头 | 沿路径描（箭头头在杆完成后 +4 帧） | 12 |
| 手写批注 | 逐字写 | 24 |
| 方框 | 周长当一笔 | 14–24 |
| 柱条 | 从基线往上 | 12–18，柱间 ≥3 |

### 2. 版式规则

1. **书写区**【作者遵守】：x 96–1824、y 140–890（1728×750）；字幕顶约 y 940，推近时书写区下沿仍在字幕顶以上 ≥40 px。
2. **一个视口一种版式**【作者遵守】：单主体 / 对比 / 流程（因果链、时间线）/ 层级 / 推导 / 例题 / 数据 / 代码 / 证据 / 锤子句，选一种，不混。主要块 3–5 个。
3. **主体位置与大小**【作者遵守，3.6 目标为门禁】：单主体中心 Cx 在 0.28–0.40 或 0.60–0.72、Cy 在 0.45–0.60（正中只给对称结构与锤子句）；单主体占画宽 0.35–0.50、高占书写区 0.55–0.80；双主体每侧 0.28–0.40；条状主体（时间线、因果链）宽 ≥0.75。主体是画面里最重的东西：面积最大或颜色最深。
4. **留白有方向**【作者遵守】：过程中空白留在下一样东西要长去的一侧；终态空白连成一块、贴着书写区一边；终态重心 Cy 在 0.42–0.62，下半部墨迹 ≥30%，整列空白 ≤1 列（8×6 网格）。锤子句是唯一允许四周大片空白的版式。
5. **视线**【作者遵守】：顺读左→右、上→下；放射从主体向外；顺链沿箭头。相邻两样东西视线跳动 ≤0.5 画宽，更远用引线带过去；每镜对角线跨越 ≤1 次。读序用编号或箭头二选一；箭头同向、不交叉——交叉了就挪位置，不弯线绕开。
6. **标签贴着对象**【作者遵守】：标签离所指部位 ≤0.12 画宽（约 230 px），更远就画引线；术语要写在纸上对象旁边，不能只出现在字幕里。
7. **纸上只写关键词**【作者遵守，compose 提示】：每处 ≤10 字（题条、引文 ≤24 字，以「贴」出现）；整句交给旁白与字幕；纸上的字不与当句字幕逐字相同。
8. **字号**【作者遵守】：大字 96 / 正文 64 / 批注 48 / 角注 36；必读内容 ≥48 px。
9. **一张纸往下写**【3.6 目标】：同一话题的 2–4 镜（20–45 秒）写在同一张纸上，镜头平移到相邻空白处接着写；旧内容退后到不透明度 0.40（0.35–0.45），在视口边缘露出 5–15%；回扣时镜头回到原处，只多一处变化，不重画。换话题、视口写满超过 36 格、锤子句需要干净揭示时才换纸；任何换纸平均每 25 秒 ≤1 次，真翻页每 60 秒 ≤1 次。不用 whip、zoom 转场。

### 3. 配色规则

1. **色数**【作者遵守】：全片 = 纸色 + 墨色 + 1 个强调色，至多再加 1 个辅助色。默认纸 `#F6F2E8`（48 px 浅蓝灰方格 `rgba(64,98,128,.10)`，线宽 1.2 px），墨 `#1F1F1F` 系，强调红 `#C23A2B`，荧光黄 `rgba(255,214,64,.62)`（multiply，压在字下）。
2. **强调色只给要强调的**【作者遵守】：强调色面积 ≤画面 15%；全片手写字数 ≤画面文字的 15%；同一帧处于强调态的文字 ≤3 处。
3. **线条退后**【作者遵守】：箭头、表格线、容器边框用墨灰，线宽 ≤正文笔画 1.5 倍；不在已有边框的卡片外再套框。
4. **装饰让位**【作者遵守，3.6 目标为开关】：与内容无关的装饰（吉祥物、角落色块、渐变天空、星星）在讲解段总面积 ≤画面 3%、不动；同一片里背景不在纸和天空之间来回切换。

### 4. 组件与草稿的搭配

1. **组件要「写」在纸上**【引擎保证（出现）/ 作者遵守（样式）】：卡片、表格、代码框不铺满底色再填字——底色高度 = 已写出内容的高度；卡片用细墨线边、无投影或极浅投影，和线稿同一墨色。
2. **只在精确形状就是信息时才用规整组件**【作者遵守】：表格要 ≥3×3 个需要比较的精确值；图表要 ≥5 个点或要看趋势；代码要看语法；截图、照片是证据。达不到就把「名 + 数」直接写在对象旁边，用引线连过去。每个视口最多 1 件（数据对比镜可 2 件），宽 ≤45%、面积 ≤50%；出现后 1.5 秒内要有标注指向它。
3. **组件和线稿要连起来**【作者遵守】：数据配实物时，读数写在实物旁边或用引线连到对应柱子；代码配示意图时，圈出的那一行要有箭头指向图上对应部位。
4. **组件内部也按出现规则**【引擎保证（auto）】：表格逐行（每格 4 帧、格间 3 帧，一行 ≤18 帧）；柱条逐根；控制台 / 代码逐行，一步 ≤3 行；流程链「节点框 → 连线 → 下一节点」；清单「勾选框 4 帧 → 文字」。
5. **图片**【作者遵守，3.6 目标为默认】：默认局部显影——四个 L 角标 6 帧描出 → 讲到的部位圆形显影（12 帧，半径 0→110 px，羽化 10 px）→ 下一句扩成全图 18 帧 → 署名逐字写。证据类才用「贴」。

### 5. 怎么量

`python scripts/measure-reveal.py <工程> [renders/preview-*.mp4]`：静态看 `same`（应为 1）、`gap`（应 ≥12）、`conc`（应 ≤2）、`pre`（应 ≤1）；给了预览还会算每镜生长比 G（≥0.45 合格、中位 ≥0.60，模板目标每镜 ≥0.60、中位 ≥0.80）。只报告，不拦。compose 的「才长完」「纸上 … 有 N 字」两类提示要清零。

<a id="motion-design"></a>

## Motion design contract
- **Anti-PPT 的构件从真实存在的里面挑**：`ConsoleWindow`（`media.tsx`）、`MetricGrid`（`media.tsx`）、`Funnel` / `ProgressRing` / `ChatThread`（`fxkit.tsx`）、`Chart` / `TreeView` / `NetworkGraph` / `ControlStack`（`src/components/`）。
  > 历史注：本节曾列出 6 件专门为 Anti-PPT 设计的插图件（脑波仪 / 雷达声呐 / BM25 标尺 / 挂载坞 / 脱敏扫描 / 芯片契约）——它们定义在 `index.tsx` 内部、**零 export、且从未被任何一处 JSX 渲染过**，按本技能自己的「零引用」判据已删除。**不要再写它们。**

### Contents

- [Cadence](#cadence)
- [Standard motions](#standard-motions)
- [Shot camera (受限配方 + 出界证明)](#shot-camera-镜头受限配方与出界证明)
- [Anti-PPT Functional Component Invariant](#anti-ppt-functional-component-invariant-组件防-ppt-化与功能实体化)
- [Locked motion pack](#locked-motion-pack)
- [Scene grammar](#scene-grammar)
- [Spatial density budget](#spatial-density-budget)
- [Continuous process rule](#continuous-process-rule)
- [Physical assembly rule](#physical-assembly-rule)
- [Duration guidance](#duration-guidance)
- [Restraint](#restraint)

### Cadence

Deliver at native 30fps. Keep scene constants, physical poses, subtitle reveal and output in the same 30fps coordinate system. Do not duplicate frames into a 60fps container. For an intentional stop-motion accent, quantize only that component to 15fps so each pose holds for two output frames.

The camera is **per shot**, not one film-wide track. Each shot declares one intent from a closed set and an `anchor` that must stay visible; the arithmetic proof lives in [camera.md#shot-language](camera.md#shot-language). Quotas: ≥3 camera moves per chapter, ≤1 per shot, 30–45 frames each, easeInOut, zoom ≤1.35 on shots carrying text, and the chrome card / header / subtitle sit **outside** the camera so they never move. Keep scale always >=1 so the canvas never shows outside the stage. Author `still` only deliberately — a film with no camera at all reads as page-turning.

Keep stable layout coordinates fixed and animate movement with `translate3d`, rotate, scale and opacity. Mount only the active scene, plus the incoming scene during a short transition.

### Standard motions

- Camera: one intent per shot (`establish` / `push-in` / `pull-back` / `pan-follow` / `reveal` / `micro-orbit`), parameters and zoom budgets per [camera.md#shot-language](camera.md#shot-language). The narrated `anchor` must stay fully inside the frame at every keyframe — proved by `scripts/validate-shot-motion.py`, not by keeping the camera still.
- JumpInText title: per-glyph 3D flip-in (rotateX ~88deg from the baseline, 12px rise, spring over-bounce, ~1.6-frame stagger). Always for chapter and scene titles.
- Figure roll-in: multi-keyframe rotation (150deg to 360deg with a mid-scale bulge) instead of a plain pop for emblem graphics.
- Subtitle reveal: one word at a time, chars inside a word stagger by 0.9 frames, 6px fade-slide, 180ms lead over the word start; all trailing punctuation strictly eliminated; never a decorative bar.
- Paper entry: cubic ease-out, one 8–13% overshoot, settle within about 0.8s.
- Paper lift: raise position and increase shadow distance/blur while lowering shadow alpha.
- Paper landing: close/darken shadow, compress no more than 3%, then settle once.
- Curved transfer: follow the same SVG geometry as the visible rail; do not approximate with a different sine path.
- Directed data line: animate `stroke-dashoffset` only from sender to receiver during transfer.
- Check state: scale 0 → 1.12 → 1 and add one soft chime.
- Slot insertion: remain above the base until crossing the slot, then pass behind the front lip.
- Complete exit: move the entire component outside the canvas or remove it after it is fully out; never leave a clipped corner.
- Character reaction: move separate arms, face or body parts; do not wobble one flattened character image.

### Motion polish: multi-clock motion

**根因诊断**：模板里每个组件原本都是「一个元素的、一个属性、一条曲线、动完永久静止」。
所有看起来丝滑的开源库都在动**同一元素的多个属性、用不同的时钟**，并且画面里永远有
一个缓慢的背景运动。下面六条是把"丝滑"从形容词变成参数。

1. **多时钟**：同一元素的位移与透明度用不同时长（参考 number-flow：位移 900ms / 透明度 450ms，
   约 2:1）。本模板取：数值位移 27 帧 / 透明度 14 帧；卡片入场 透明度 16 帧 / 位移 20 帧。
   同长同曲线会读成"一个刚体弹出"。
2. **入场与出场曲线不同**：出场快而急（`Easing.in(Easing.quad)`，约为入场时长的 60%），
   入场慢而稳（`Easing.bezier(0.16,1,0.3,1)`）。这是最容易被感知到的一条。
3. **不用透明度做出现**：组件出现一律按 [draftpaper.md#reveal-rules](draftpaper.md#reveal-rules) 左→右展开或沿路径描出；
   透明度只用于退后（变暗）与退场。
4. **数值用 `tabular-nums` + 固定小数位**（`fontVariantNumeric:'tabular-nums'`，
   `minimumFractionDigits === maximumFractionDigits`）。否则数字每帧改变宽度、整格横向抖动
   ——这是"看起来不丝滑"最常见的真实原因。
5. **进度类动 `scaleX`，不动 `width`**（进度条、漏斗条、时间轨填充）。`width` 是布局属性，
   会重排，而且会让圆角胶囊在动画中途被拉变形。父容器保留 `overflow:hidden` 与圆角。
6. **过冲只给物体，不给数值**：印章/横幅可以 0.94→1.03→1 弹一下，百分比与环不能弹
   （会短暂显示错误的数）。环要"落定"就给容器 scale 一个 1→1.03→1。

**Rule 5 · 环境运动（每镜一处，永不停止）**：所有元素都"动完即永久静止"时，画面读起来像被暂停。
每镜保留**一处**缓慢的背景运动：幅度 ≤4%、周期 120–180 帧、`Easing.inOut(Easing.sin)`，
**只放在背景/次级元素上**（本模板用 `shotkit.ambientBreath(f)` 施加在底托上），
绝不放内容层——内容只在语义节点变化。这一条是"正面要求"，与下面"不要随机漂移"的禁令不冲突：
禁令针对的是没有叙事理由的抖动，环境运动提供的是前景参照。

配套的两条结构性要求：
- **每镜保留一个全程缓慢的"环境运动"**（≤4% 幅度、周期 90–180 帧、`Easing.inOut(Easing.sin)`），
  且**只在停驻时**呼吸——行驶/进行中不要抖动，"一直在微动"不算语义变化。
- **状态机推进要有动作**：`PhaseRail` 的当前点脉冲 + 光晕、连接线按拍画出、完成态用
  **描线**而不是缩放入场（对勾是笔画，应当画出来）。

### Shot camera (镜头受限配方与出界证明)

**取代旧的 Camera Micro-Framing Invariant。** 旧铁律把相机锁在 `x ∈ [945,975]`、`s ∈ [1.00,1.018]`
（景别变化 1.8%，等同定焦），而且是**全片一条关键帧轨道**，所以每个镜头不可能有自己的取景；
同时按旧源码复算，`CAM_KEYS_P`（轨道已删除）10 个关键帧 `s` 超旧上限 1.018（16:9 设计空间口径），
真正可见窗出画的是 8 个关键帧、最大 383px，且无人发现。两个极端都来自同一件事：**没有校验**。

现行规则：

1. **每个 shot 一个 intent**，取值仅限 `establish` / `push-in` / `pull-back` / `pan-follow` / `reveal` / `micro-orbit` / `still`；
   曲线形状由 intent 决定，调用方只填少量参数 —— 自由曲线一律不接受。
2. **每个 shot 必须声明 `anchor`**（本镜必须始终可见的矩形）。`safeCheck()` 与
   `scripts/validate-shot-motion.py` 用同一套纯算术证明 `anchor` 在所有关键帧都落在可见窗内；
   任一越界即 P0，阻断渲染。
3. **配额**：每章 ≥3 次运镜（**章节 <20s 时 ≥1 次**）、每镜 ≤1 次、单次 30–45 帧 easeInOut；全片 ≥3 种 intent。
4. **缩放预算**：含文字的镜头 `s ≤ 1.35`，纯图形镜头 `s ≤ 1.60`；
   需要"更大"时优先**把主角画大**，而不是把相机推近（推近会牺牲文字锐度）。
5. **页眉 / 章节卡 / 字幕在相机之外**（屏幕空间），结构上不可能被运镜带动。
7. **不要**重新引入全片级相机轨道。取景是镜头级的。

镜头部分的完整参数表与写法见 [camera.md#shot-language](camera.md#shot-language)（本文件只保留与动效相关的部分）。

### Anti-PPT Functional Component Invariant (组件防 PPT 化与功能实体化)

Never stack plain text bullets inside generic rectangular boxes. Every explanation scene must incorporate at least one function-driven interactive component with physical state transitions synchronized to narration:


### Locked motion pack

- Spring presets: use `popS(f, start, preset)` with `SPRINGS` — `snappy` for small UI ticks and code lines, `soft` (identical to the legacy `pop`) for cards and lists, `bouncy` for callouts and celebratory beats. Do not hand-tune new damping/stiffness values per scene.
- Scene transitions: the vocabulary is `cut | handoff | reveal`. `reveal` is implemented by `RevealMask` (`src/insert.tsx`) and is driven by the shot table's `transition` field — **never write the `reveal` prop by hand**, it is generated into `shots.ts` by `resolve-shots.py`. `handoff` requires a `carrier` shared with the next shot. `whip` / `paper-turn` were removed (zero uses in two shipped films, and a single-frame whip is unreadable at 30fps). **No scene overlap, ever**: the outgoing scene must reach opacity 0 before the incoming one starts.
- Camera script: build keyframe tracks in the `camera` field of `manifests/shots.json` (expanded by `resolve-shots.py`) instead of raw keyframe tables; it guarantees first/last frame coverage. The same easing and exponential lag follow-focus apply.
- Stop-motion accent: `useSteppedFrame(15)` quantizes a component to 15fps so each pose holds two output frames. Reserve it for occasional hand-made charm; never apply it to subtitles, transfers or the camera.
- Component motion stays inside the locked library: `Checklist` rows slide in with staggered `soft` springs, `HighlightCode` lines enter with `snappy` springs, `PathDraw` animates its dash flow only during transfer.

### Scene grammar

Build progressively:

1. stable chapter and hero;
2. supporting semantic parts;
3. relationship or transfer;
4. local feedback;
5. readable hold;
6. remove obsolete parts completely.

Cause one meaningful semantic change every 2–4 seconds. Do not count random drift, blinking cursors, animated texture, global zoom or constant line motion.

### Spatial density budget

- Divide the 1920×1080 design stage, rendered inside the 2560×1440 composition, into explicit work zones before animating.
- Give each large object a stable home zone and reserve the center corridor for transfer only.
- Keep unrelated paper objects at least 70px apart, including their airborne shadows.
- Allow one dominant transfer object in the corridor at a time.
- Prefer 3–5 large semantic objects over 8–12 small decorative objects.
- Remove, cover or move completed objects fully before the next semantic group arrives.
- If the frame feels crowded, increase object size and redistribute it; do not solve crowding by shrinking everything.

### Continuous process rule

When the narration describes one task moving through several steps, keep one persistent task card. Move it along one visible path and change its label, color or status at each station. Do not replace it with a newly spawned card unless the narration explicitly describes a new object.

### Physical assembly rule

Model the slot, front lip, inserted part and status feedback as separate layers. Keep the part above the base before crossing the slot. After crossing, lower its z-order beneath the front lip and fade or translate it to complete invisibility. At the end of insertion, assert that no pixel-sized corner remains outside the machine.

### Duration guidance

- 30 seconds: 5–7 scenes.
- 60 seconds: 3–4 acts with small internal steps.
- 2–3 minutes: 8–12 sections, usually 10–20 seconds each.

Use a clean cut when the metaphor changes. Continue progressive construction while the same concept develops.

### Restraint

Do not apply every effect to every object. Dynamic shadow requires actual lift. Data pulses require an active transfer. Sound requires a visible action. Keep fixed panels fixed.
