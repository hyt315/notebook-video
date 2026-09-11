# Changelog

All notable changes are recorded here. The project follows semantic versioning.

## [3.0.1] - 2026-09-11

> 小版本：在 3.0.0 上做"可选词汇真正可用 + 声明必须兑现 + 音效听得见"三件事。
> 全部改动都有实测依据（两条成片 + 探针实渲），**净删 236 行**，不新增功能面。

### Added

- **`scripts/validate-audio-levels.py`（第 9 道门禁）**：音效素材峰值 < **−12 dBFS** 即 P0。实测旧素材 `paper-tap` 峰值只有 **−31 dB**、`chime` **−38.5 dB**，乘上 0.11–0.16 的混音音量后有效峰值 **−39 ~ −55 dB**（BGM 一直在 −22 dB）——四个音效全被压住，成片听起来"几乎没有音效"。这才是"音效少"的真因（双重衰减），不是数量问题。
- **`src/toolkit.tsx`**：把 11 个"修辞工具"组件从 `index.tsx` 迁出并 **export**——它们原先没有 `export`，场景文件**物理上无法 import**，这是"54 件组件 27 件零使用"的结构性真因。含 `Callout`（画圈+引线+手写标注）、`Connector`（关系箭头）、`WaveText`/`JumpInText`、`CountUp`/`RollDigit`、`Checklist`、`CodeBlock`、`BrowserChrome`、`Mascot`、`ProgressBar`。模块自包含（刻意不 import `index.tsx`，避免循环依赖）。
- `references/media-routing.md` 新增**「修辞动作 → 组件」表**（15 行，含"何时别用"列）。技能原先只路由"内容类型 → 介质"，缺"我此刻要做的修辞动作该用哪一件"这一层——这是弱模型选不准组件的直接原因。
- `SKILL.md` 把 fxkit 那条改为**必读**、指向选型表，并加了可检查的断言：**`live` 里每个名字都要能在表上指到**。

### Fixed

- **音效钉帧从"按镜头比例"改为"绑定节拍"**。旧规则把 whoosh 固定在"镜头时长的 42% 处"——那一帧画面上什么都没有，正是 `tts-audio.md` 自己明令禁止的"把音效放在看不见的动作上"。现在按 `beats`（"讲到这一句"的时刻）钉帧，沿用同一套自动重定时；中间节拍轮换 `drop`/`toggle`/`click`（`drop.ogg`、`toggle.ogg` 此前**从未被引用**），并把音量重设为 0.26–0.42。
- **声明即承诺**：`reveal` 改由 `resolve-shots.py` 从分镜表生成进 `shots.ts`（场景不再手写这个布尔）；`validate-composition.py` 新增检查：`reveal` 声明 ↔ 场景里该镜的 `reveal` 必须一致（正反向都查）、`handoff` 声明**必须有 `carrier` 且下一镜同一个**（否则它与 `cut` 没有区别）。实测两条成片共 **15 处 `handoff` 声明从未兑现**、SWE-2 的 S1 还"表写 cut、代码写 reveal"，全部已修正。
- **删死代码（净删 ~150 行，零行为变化）**：`PaperTurn`（淡出条件恒假）、`BackgroundMute`（paper/sticker 皮肤下必返回 `null`）、`TransitionIn`（与 `RevealMask` 重复）、`WhipStreak`（8 帧甩镜在 30fps 下读不到）；`TRANSITIONS` 收缩为 **`cut | handoff | reveal`**。
- `theme/types.ts` 里指向已删组件的注释改指 `CoverPanel`。

### Changed

- **新增三条 P1 门禁**（阈值用两条成片实测校准）：**组件多样性**（≥16 镜 → 可选组件 ≥10 件；8–15 → ≥7；≤7 → ≥5；单件占比 ≤35%，结构件豁免）、**反堆砌**（≥12 镜的成片里"新增件只出现在 1 镜"达 5 件即提示——堆砌的真实指纹）、**节拍密度**（单镜 >240 帧且 beats <3 → 画面会在台词中途冻住）。

## [3.0.0] - 2026-09-11

> 版本说明：本版是**用两个真实成片打磨出来的修复版**——DeepSeek（129 秒）与 SWE-2（237 秒）。
> 下面每一条都来自成片里实测到的缺陷、或实测到"门禁其实没在工作"，不是推测。
> 早期 v2.9 / v3.0 两条试验线的优点已吸收，两分支与旧 tag 均已删除，只保留 `main`。

### Added

- **`scripts/validate-frame-props.py`（新增第 8 道门禁）**：逐个 JSX 标签核对帧参数名——`fxkit` 的 18 个组件用 `frame`，`media / stagekit / skeletons / insert / shotkit / charts` 用 `f`。**写错不报错、只会静默回落到全局帧**（`start={局部节拍}` 早已过去，元素直接以完成态出现），是这套代码里最高频的真实事故。实测两支自带样板片共 **11 处 P0**：4 个 `StampSeal`、`Funnel`、`Typewriter` 等进场动画长期失效。
- **`ShotPlate`（`assets/lecture-template/src/plates.tsx`）**：**实拍素材框**。把用户提供的真实截图与官方图表装进锁定皮肤的墨线框（2.5px 描边 + 硬偏移阴影），配角标、右上角标与来源署名，用 `transform` 做确定性推近（不重排）。素材仍须按 `manifests/visual-assets.json` 登记（`source_type` / `rights` / `baked_text` / `sha256`），并在 `asset-manifest.json` 里同步素材 id。
- `SKILL.md` 新增**「开工前 20 行授权契约」**，放在参考文件表之前——这是唯一保证会进上下文的文本，每条都对应一个真实事故。
- `references/fxkit.md` 新增**参数名对照表**与错峰校准说明；`references/scene-authoring.md` 坑表 6 → **10 条**（新增"flex 子项只含绝对定位元素导致宽度塌陷、多卡精确叠压"与"卡片高度必须用 `fitH` 算"）。

### Fixed（SWE-2 成片轮 · 又抓出两处门禁自身的缺陷）

- **`OverlapGate` 的遮挡判断漏看祖先 z**：只检查元素**自身**的 `z-index`，而字幕的文字 `span` 自身是 `auto`（它的祖先才是 z=200），于是**字幕被当成"遮挡物"**，全片刷出大量"被遮挡"误报。已改为祖先链一并检查，误报减半（144 → 72 行）。
- **`validate-frame-props.py` 扫不到拆分后的场景文件**：它只匹配 `scenes.tsx`；把场景拆成 `scenes-a/b/c/d.tsx` 之后，它**一个文件都没查却报 P0=0**（与上面 `SlotGuard` 同类的"门禁静默失效"）。已改为匹配所有 `scene*.tsx`（实测从 1 个文件变 6 个）。
- **可读性垫底改为半透明**：`cel` 皮肤的 `Paper` 从**完全不透明**（`#ffffff`，它才是"整块盖住背景"的元凶）→ 88%；场景外壳的羽化垫底中心 96% → 76%、中段 84% → 59%；左上角章节卡的底也从纯白改半透明。背景图不再被盖死，文字依然压得住。
- **字幕/章节卡不再被误判为遮挡物**（配合上一条）：锁定覆盖层（z ≥ 145）自身**及其子树**都不算遮挡物——否则每片都会在片头被自己的章节卡拦下。

### Fixed（v2.11 引擎补丁 · 全部有实测证据）


**三道渲染期门禁此前是静默失效的（都做了可复现实验）**

- **`CardFitGate` 从未真正校验过**：实测把卡片高度压到 40px、内容必然溢出，渲染仍 exit 0 且零输出。
  三个叠加原因：① 开头 `if(document.fonts.status!=='loaded') return;` —— 实测某帧 `fonts=loading`，整桶跳过，
  且从不等待字体就绪（字幕门是 `await document.fonts.ready` 的）；② `offsetParent` 链做累加再 `if(m!==card) return;`
  —— 实测 87 个文字块里 18 个在链上断裂（逐字动画 span、Takeaway 文本），这些文字从未被校验；
  ③ 零输出既可能是"全部合格"也可能是"根本没跑"。现改为：等字体就绪后补测、判据换成
  `scrollHeight > clientHeight`（overflow 的定义，含 6px 容差吸收内联行盒取整）、剔除 `overflow:visible`
  容器（避免绝对定位子元素虚增，实测 MetricGrid 虚增 180–213px）、每 5 秒打一次覆盖率。
  **修好后立刻拦下 S2 卡片真裁切 25px 与 S3 控制台水平溢出 8px。**
- **`OverlapGate` 四处看不见**：① 每 15 帧网格漏掉短命重叠（镜头交接 10 帧、页眉滑变 7–16 帧、数值滑动 14 帧）
  → 现在基础网格 + **事件帧强制抽样**（镜头边界 / 节拍 / 相机关键帧 ±2 帧，由 `index.tsx` 传入）；
  ② `looksSolid` 只看 `backgroundColor`，渐变面板被当成透明 → `backgroundImage !== 'none'` 也算实心；
  ③ `SKIP_Z=140` 把页眉层连内容带祖先一起跳过 → 阈值提到 145（只跳过章节卡 150 / 字幕 200）；
  ④ 多文本节点按整块矩形量 → 一律用 `Range` 取并集。另加覆盖率日志；两支自带成片已切 `mode="block"`。
- **`SlotGuard` 在生产渲染中永不执行**：条件写的是 `process.env.NODE_ENV !== 'production'`，而 Remotion 打包恒为
  production（本仓也没有 dev 渲染入口）。文档已据实修正为 dev-only，真正的槽宽校验由 `CardFitGate` + 重叠门承担。

**最高频真实事故：帧参数名（文档写对了，两支样板片自己违反了 11 处）**

- 新增 `scripts/validate-frame-props.py`：解析每个导出组件的帧参数名（fxkit 18 个用 `frame`，
  media/stagekit/skeletons/insert/shotkit 用 `f`），逐个标签核对。**实测抓出 11 处 P0**——
  4 个 `StampSeal`、`Funnel`、`Typewriter` 等被传 `f={f}`，组件静默回落到全局帧，
  于是 `start={局部节拍}` 早已过去，这些进场动画长期以"完成态"直接出现。
- `PhaseRail` 的三个调用处把 `StageFrame` 传入的**真实 ctx** 换成硬写 `local: 0` 的假 ctx，
  导致"本拍接管"脉冲 / 连接线绘制 / 当前行入场全部冻结；已改为直接使用回调给的 ctx。

**构建期门禁硬化（堵住"填假名字也能过"）**

- 枚举闭合：`intent` / `transition` / `entry` / `media` / `skeleton` 写错名字即 P0
  （实测把 media 写成 `FAKE_MEDIUM_A…`、live 写成 `NO_SUCH_COMPONENT` 曾能 P0=0 通过）。
- `live` 里的每个名字必须能在场景文件里找到（真实 import 并渲染过）。
- `explanation:false` 不再能整体绕过 `zones` / `bottomFill`（旧版一个 false 就能跳过整块密度校验），
  且全片最多 1 镜。
- 声明了运镜就**必须真的动**（`Δs ≥ 0.02` 或 `Δ平移 ≥ 20px`）：把 `still` 改名成 `push-in` 不再能同时骗过
  意图多样性统计与每章运镜配额。
- 新增 P1：单镜时长（>10s）、镜长分布（最长/最短倍数、同一时长档占比、是否有 ≤4s 短镜）、
  骨架指纹重复（`(骨架,意图,转场,入场)` 组合）、主角尺寸（`hero.size` 必须是主体短边设计像素）。
- P1 去噪：原来"每镜刷 1 条最长静止"改为**汇总一条并带帧区间归因**（`S8(105帧 f=2408-2513)` 这种），
  让 P1 真正可执行。
- 负向抽查 4 → **8 条**：新增"假 live/media 名""冻结的假运镜""帧参数写错"三条必须被拦的夹具，
  外加干净对照必须全过。

**成片缺陷（由修好的门禁抓出并修复）**

- S12 四张事实卡**精确叠在同一位置**（用户报的 2:07）：flex 子项只含绝对定位子元素 → 宽度塌成 0，
  四张 248px 宽的卡被 `gap:20` 排到 x=0/20/40/60。已显式给宽高。
- S2 名片高度比内容矮 25px，`overflow:hidden` 把第三行裁掉（旧成片带着这个伤）。
- S3 控制台高度公式少算自身内边距与真实行高 → 最后一行被裁 27px；改为 `height:auto`；
  随后门禁又抓出该面板**水平**溢出 8px（内容 1000 > 内宽 996），修内边距。
- `MetricGrid` 数字滚动的小数位改为取 `before`/`after` 的较大精度（避免中途出现第三档精度）。
- `Funnel` 纵向压缩 24px（S11 里比容器高 19px）。

**动效（把六律真正落到组件上）**

- 出场统一"快而急"：`exitStyle` 改 `easeInQuad` 9 帧——**一处修好 9 个组件的"出场 = 入场"**。
- `FitCard` / `StaggerList` 透明度改用独立时钟（此前位移与透明度共用一个 spring，读作"整块刚体出现"）。
- 错峰校准：列表 18–30 帧 → **6 帧**（实测 18–30 帧在中文旁白下读成"一个个淡出来"，
  且后几张卡要等旁白讲下一句才出现，用户报过"四项只看到三项"）。
- 呼吸周期去毛躁：Corridor 承载物 12.6 帧 → 140 帧、`SkeletonCard` 60 帧 → 131 帧。
- `CompareBars` 行补 14px 位移（此前只有透明度）；`SplitStage` 分割线补 opacity；
  `ProgressBar` 由 `width` 改 `scaleX`（圆角胶囊中途不再被拉变形）；百分比补 `tabular-nums`。
- 删除死掉的 `CameraRig` / `CAM_KEYS` / `camAt`（48 行）：它会教出"全片一条相机轨道"的错做法，
  而那正是 v2.8 被锁死相机的根因。

**文档**

- `SKILL.md` 新增**「开工前 20 行授权契约」**（放在参考文件表之前：这是唯一保证会进上下文的文本），
  并更新门禁表为 8 道、补上"覆盖率日志缺失 = 门禁没跑，按失败处理"的判据。
- `fxkit.md` 新增**参数名对照表**与错峰校准说明；`scene-authoring.md` 坑表 6 → 10 条
  （新增"flex 宽度塌陷导致多卡叠压"与"卡片高度必须 `fitH` 算"）。
- `validate-composition.py` 的 P1 现在带帧区间归因。


### Changed

- 负向抽查 4 → **8 条**：新增"假 `live` / `media` 名""冻结的假运镜""帧参数写错"三条必须被拦的夹具，外加干净对照必须全过。
- `validate-composition.py` 的 P1 从"每镜刷一条最长静止"改为**汇总 + 帧区间归因**（如 `S8(105帧 f=2408-2513)`），让 P1 真正可执行。
- **交付响度改为两遍规范化**：先测再用 `measured_*` + `linear=true` 精准应用；并把 `validate-video` 的真峰阈值收紧到文档写明的 **−1.5 dBTP**（原来 `> -1` 会放过 −1.3 dBTP 的违标片）。

## [2.9.0] - 2026-09-10

> 版本说明：v2.9 / v3.0 两条线（受限配方、内容路由、限量文本架构）的优点已被本版吸收，
> 因此不再保留这两条分支与旧 tag；本版即 main 线上的 v2.9.0。

### Added

- **`OverlapGate`（渲染期重叠/遮挡门禁，`src/overlap-gate.tsx`）**：本版最重要的新增。每 15 帧抽样一次，做两件事——① 文字**两两重叠**（用 `Range.getClientRects()` 量真实字形矩形，避免居中文本按整块宽度误报）；② 文字**被遮挡**（在文字块内取采样点调 `document.elementsFromPoint`，返回的是绘制顺序；排除祖先、透明蒙层、以及标了 `data-gate-allow` 的有意覆盖）。默认只警告，校准后可开 `mode="block"` 阻断渲染。**这一道门禁抓出了本版全部 10 类重叠缺陷中的每一类**，并且从"抓到 3 类真实重叠"到"全片零报告"走完了一个完整的门禁闭环。
- **有意覆盖白名单约定**：`data-gate-allow="handoff" | "swap" | "value-swap"` 与 `data-gate-skip`。镜头交接叠帧、头部滑变双层、指标新旧值替换都属有意重叠，必须显式标注；不允许用白名单掩盖两个不同信息互相压字。
- **多时钟动效六律**（写进 `motion-design.md`）：同一元素多属性错开时长的双时钟、入场/出场曲线不同、不要只动透明度、数值必须 `tabular-nums` + 固定小数位、进度动 `scaleX` 不动 `width`、过冲只给物体不给数值。另加"每镜保留一个缓慢环境运动"与"状态机推进要有动作"两条结构性要求。
- **镜头边界交接**：`FinalDemo` 在每镜开头 10 帧把上一镜末帧叠在上层淡出，`Shot` 不再在镜末淡到全透明——**消灭了镜头边界的空帧**（逐帧审计实测每个边界都有 1–2 个空帧）。
- **平移安全预算（镜头铁律之二）**：相机平移会整层移动内容，因此 `s=1.00` 时任何平移都会把内容推出画面（实测把走廊左侧站名裁掉）。新增 `panBudget()` 与 `camAt()` 运行时钳制，规则 `maxPanX = 960×(1−1/s)`，`validate-shot-motion.py` 用同一公式检查。**推论：纯静止镜头不能有取景偏移；想要偏心构图就必须带一个能覆盖它的缩放。**
- **时序铁律：讲到哪、出现到哪**。元素出现帧必须绑定到 `SHOTS.Sx.beats` 的某个节拍，禁止在镜头开头把一屏元素一次性铺完；入场统一为 22 帧 `easeOut` + 22px 上浮 + 微缩放（`enterAt()`），同句内错峰 8–16 帧，镜末 18 帧干净淡出。写入 `scene-skeletons.md` §3.5 并给出可直接照抄的代码形状。
- `locked-style-contract.json` 新增 `timing_system` 与 `readability_system` 两组契约。
- **镜头层 (`src/shotkit.tsx`)：受限配方 + 出界数学证明。** 取代 v2.8 的 Camera Micro-Framing Invariant（x∈[945,975]、s∈[1.00,1.018]，景别变化 1.8%，等同定焦，且全片只有一条相机轨道）。现在每个 shot 声明六个意图之一（`establish` / `push-in` / `pull-back` / `pan-follow` / `reveal` / `micro-orbit`）加一个必须始终可见的 `anchor`；`safeCheck()` 与 `scripts/validate-shot-motion.py` 用同一套纯算术逐关键帧证明 anchor 不出界（因 `x/y/s` 在关键帧间单调、可见窗边界对其单调，故逐帧校验即为精确证明）。含 `DepthLayers` 景深视差（系数 0.35/0.70/1.00，层数 ≤3）与 3D 路径（CSS `zoom` 而非 `transform: scale`，避免 Chromium 先光栅化再放大导致文字发虚）。
- **场景骨架层 (`src/stagekit.tsx`、`src/skeletons.tsx`)：四种骨架。** `Stage`（单体舞台：一个主体演化 3–6 个状态，`StageFrame` + `useStageMachine` + `PhaseRail` + `Attach`）、`Corridor`（持久对象沿轨道穿站）、`Split`（双栏对比）、`Zoom`（整体→聚焦→标注→回整体，纯代码局部放大）。默认强制"相邻场景不得同骨架、全片 ≥3 种"。
- **介质层 (`src/media.tsx`、`src/kit.tsx`)：内容 → 视觉介质。** 新增 `ConsoleWindow`（控制台/窗口介质）、`MetricGrid`（指标网格）、`StampBanner`（结论吸底）；并把主题无关原子 `PillTag` / `LineIcon`(26 字形) / `CheckBadge` / `TYPE` 从 `index.tsx` 抽到 `src/kit.tsx`，使工程侧也能引用。新增 `references/media-routing.md` 的内容→介质路由表与 A/B 场景定义。
- **组件接触表 (`src/showcase.tsx` + `NotebookVideoShowcase` Composition + `showcase` / `showcase-sheet` 命令）。** 6 页渲染 16 个构件 + 6 种镜头意图 + 4 种骨架，1fps 抽帧即得 6 张图。解决"能力存在但不可达"：让执行 AI 看图选型，而不是读 props 文档。
- **分镜表与解析器 (`scripts/resolve-shots.py` + `manifests/shots.json`)。** 分镜表只声明"本镜覆盖哪几句 cue"与语义字段，解析器从 TTS 词级时间戳推出全部绝对帧，生成 `src/shots.ts`（相机关键帧已展开）与 `shots.resolved.json`。改台词后重跑即可，**不再手改几十处魔法帧号**。音效钉帧也改为相对所属镜头起点推导。
- **两道构图门禁 (`scripts/validate-shot-motion.py`、`scripts/validate-composition.py`)。** 这是本版最重要的新增：v2.8 的强制条款全部空转（明文强制 6 个反 PPT 组件，实测 34 个库组件里 32 个引用数为 0，9 个校验脚本无一条能发现）。八项检查、P0 阻断渲染 / P1 仅警告，纯标准库只读，可直接进 CI。
- **背景可读性契约。** 主题新增 `backgroundDecorZones`（cel 4 区、flat 2 区）；`CoverPanel` 提供内容底托，`BackgroundMute` 提供成片级羽化兜底。**锁定背景位图保持原样不改**——它很好看，只解决压在上面的文字被装饰吃掉的问题。
- **四份新参考文档**：`shot-language.md`、`scene-skeletons.md`、`media-routing.md`、`composition-gate.md`。

### Fixed

- **`PhaseRail` 的入场动画是一段死代码**：`translateX(${(1 - reveal) * 0}` 乘以 0，整段推进没有可见动作。改成真实的每拍推进：圆点脉冲 + 光晕收放 + 连接线按拍画出 + 完成态用描线对勾。
- **`ZoomStage` 变换顺序错误**：`translate(tx,ty) scale(k)` 里 `tx` 用的是未缩放单位，导致"要聚焦的点"不落在框心，且放大后内容被框裁掉（静态审计实测四个场景被裁 100–500px，其中一项指标完全移出画面）。改为三段式 `translate(框心) scale(k) translate(-焦点)`，并新增 `contentW/contentH` 按内容自动钳制缩放上限。
- **`Corridor` 状态标签与站点标签只剩 3.6px**：状态标签从承载物下方 116px 改到上方 46px，站点标签下移 96px；退场中的标签锚在它自己的站点位置上（否则两个标签会叠在一起，门禁实测 3500px²）。到站反馈由"缩放入场"改为"圆环脉冲 + 对勾描线"。
- **`MetricGrid` 新旧数值是同位置替换**，属有意重叠，已标 `data-gate-allow="value-swap"`；同时把替换改为两条互不相交的轨道（行程 56px），避免中途叠字。
- **`SplitStage` 两侧同时同向入场读作"两张幻灯片"**：改为左侧先入场 6 帧；分隔线先画、徽章后落；胜出改为因果顺序（输方先暗+去饱和+下沉 → 赢方边框 → 赢方放大 → 徽章），输方的行逐行划掉。
- **`StageFrame` 头部文本是硬切**：改为滑变双层（旧的 7 帧上移淡出、新的 12 帧落下淡入，两层错开 4 帧），且**完全由 `phase.at` 派生**——不用 `useRef` 记"上一帧"，因为 Remotion 逐帧乱序渲染，ref 跨帧状态不可靠。
- **`ConsoleWindow` 高度默认值比内容高约 120px**（整块死黑）：改为按内容自适应；行节奏从 9 帧改到 16 帧（300ms 太快，光标读不出"移动"）；新增光标接棒、写入式 clip 擦除、ok/warn 行一闪、末行扫描。
- **`validate-shot-motion.py` 读错了数据源**：它按 `shot["camera"]` 自己再"猜"一遍关键帧，而不是读解析器已展开的顶层 `keys`，于是校验的是一个假想的静止相机——**此前的 PASS 有一部分是空的**。改为优先读 `keys` 后，立刻暴露出 11 个镜头的平移超预算问题。教训：门禁必须与运行时读同一份真源。
- **遮挡底托是硬边矩形**，下沿留下肉眼可见的水平接缝（38 秒处横切爆炸贴）。改为径向羽化渐变并去掉 1px 描边环。
- **同一容器里"文档流标题 + 绝对定位组件"必然重叠**：绝对定位组件的 `x/y` 相对容器原点，而文档流标题也占容器顶部，两者精确压在一起（实测：走廊场景的"整个过程对你是透明的"与列表第一行叠成乱字）。
- **章节卡与场景标签互相压字**（用户反馈"左上角文字每次都被盖住"）：移除与章节卡信息重复的场景标签胶囊，并把章节卡与页眉移到画幅贴角位置。
- **`CaptionFitGate` 之前是"画幅盲"的**：硬编码 16:9 的 44px / 字重 400 / 字距 1.2 / 安全宽 1334，也没有计入主题字幕框内边距（cel 64px、sticker 72px、flat 108px）。结果是 **4:3 与 3:4 的字幕超宽静默通过、渲染后被裁切**，cel/sticker/flat 的字重与字距也量错了。现在字号/字重/字距/安全宽全部取自当前 canvas 与主题（新增 `subtitleWeight` / `subtitleLetterSpacing` / `subtitlePadX`），超 `mode.safe` 记 fail、超内边距记 warn。**修好之后会开始拦截以前静默放行的字幕——那正是门禁在工作**（本版实测拦下一条 1345px 的长字幕，已按语义拆分为两条）。
- **`StageFrame` 的 `header` / `stamp` 槽缺少定位祖先**，槽内绝对定位构件（如 `StampBanner`）会跑到 StageFrame 顶部压住页眉。
- **`CoverPanel` 的 wash 底板若用正 z-index，会盖住场景内所有 `z-index: auto` 的元素**（CSS 中正 z-index 稳定压过 auto）。实测导致整镜内容被压成 15% 不透明。wash 必须用**负 z-index**。
- `motion-design.md` 删除旧的相机铁律整节，改为指向 `shot-language.md`；`quality-checklist.md`、`locked-style-contract.json` 同步改为"每镜受限配方 + anchor 证明 + 配额"的契约。

### Changed

- `NotebookVideoFilm` 不再使用全片级 `CameraRig`（连同 `CAM_KEYS_L` / `CAM_KEYS_P` 一并移除）。取景是**镜头级**的。`shotkit` 在无 3D 关键帧时走纯 `translate + scale`，且 `s=1.0 / x=960 / y=540` 时与 v2.8 定焦渲染逐像素一致。
- `selftest.py` 的关键产物清单纳入 v2.10 的 8 个源文件、4 份文档与 3 个脚本。

> 说明：本版所有结论来自 (a) 对成片逐帧审计、(b) 对 20 个场景的静态坐标审计、(c) 在真实无头浏览器里的实测 spike 三路交叉验证，而非推测。
> 说明：模板自带的 30 秒样片仍保留 v2.8 的四个场景，作为**美学与技术基线**；场景语法请遵循
> `references/scene-skeletons.md`，并参考 `NotebookVideoShowcase` 接触表。旧场景将被下一版替换。
## [2.8.0] - 2026-09-09

### Added

- **fxkit motion kit v2 (固定动效组件库)**: new `assets/lecture-template/src/fxkit.tsx` with 18 cel-locked, zero-dependency components — `FitCard`/`fitH` (overflow-proof cards with computed heights), `Typewriter` (typing with punctuation pauses), `PayPop` (payment notification), `StampSeal` (seal slam), `Funnel` (attempt funnel), `ChatThread` (dialogue bubbles), `MailScan` (email confirm), `TimeRail` (event timeline), `CompareBars`, `ProgressRing`, `ShakeX` (hammer shake), `BurstCallout` (3-char-safe sticker), `StaggerList`, `KenBurnsImg` (restrained push-in), `EvidenceZoom` (recognize → locate → conclude), `DiffView` (patch red/green), `ConfettiPop` (celebration burst), `SkeletonCard` (skeleton → content). Catalog and two iron laws (computed heights; scene-vs-card coordinates) in `references/fxkit.md`.
- **CardFitGate (卡片防出格门)**: runtime browser gate in the lecture template that scans mounted scenes every 15 frames and `cancelRender`s on any text overflowing its card (transform-independent via offset chains; chrome/subtitle layers excluded). Caught 4 real overflows during the v2.8.0 film production.
- **Coordinate reporter (`scripts/coords-lint.py`)**: read-only audit of overlay-component x/y literals; off-canvas values fail, suspicious card-frame values warn.
- **Retiming tool (`scripts/retime.py`)**: one command rewrites `DURATION`, `asset-manifest.json` duration/scenes and prints the sound-frame remap table after narration changes.
- **TTS audition strip + polyphone scanner (`scripts/audition.py`)**: builds a 30s first-lines audition from cached TTS segments (zero API calls) and scans `narration.txt` against the production polyphone table.
- **Secret-leak guard in `selftest.py`**: fails if any tracked file contains a key-like token (`sk-` + 16 alphanumerics); TTS keys stay in local untracked `tts.env` by contract.

### Fixed

- **`lecture-template` duration drift**: `asset-manifest.json` said 900 frames while `src/index.tsx` `DURATION` and the caption track run 1126 frames; manifest corrected to 1126 (new `validate-visual-plan` DURATION cross-check now blocks this drift class).
- **`validate-visual-plan` tightening**: added `DURATION` cross-check and the rule that `image-text` scenes must reference at least one non-background illustration.

## [2.7.0] - 2026-09-08

### Added

- **6 Anti-PPT Interactive Functional Components (反 PPT 实体交互组件库)**: added `BrainwaveEEG` (cognitive waveform pulse & flatline alert), `VectorRadarSonar` (360° sonar beam & clustered vector highlights), `BM25TokenRibbon` (keyword relevance scoring ribbon), `HookMountBay` (zero-overhead auto-mount slot & lock state), `RedactionScanner` (infrared laser scan & real-time secret asterisk masking), and `ChipContract` (high-tech circuit bus transfer capsule) to `assets/lecture-template/src/index.tsx`.
- **Camera Micro-Framing Invariant (微运镜与防出界铁律)**: hard-locked virtual camera center drift within $X \in [945, 975]$ (maximum $\pm 15\text{px}$) and scale within $S \in [1.00, 1.018]$ in `camScript` and specification contracts, completely eliminating large camera shifts that throw left-side active content off-screen.
- **Subtitle Trailing Punctuation Strip Invariant (字幕句末标点消除机制)**: implemented `targetChars` length gate in `Subtitle` component (`assets/lecture-template/src/index.tsx`) to preserve mid-sentence commas for natural rhythm while 100% eliminating trailing punctuation marks from rendered subtitles.
- **Skill Doctor Audit PASS & SEI 100/100**: verified zero vulnerabilities with `skill-doctor`, cleaned test keys, added `*.env` and audit artifacts to `.gitignore`, and passed all 39 static and dynamic audit points.

### Changed

- **Cel Theme Aesthetic Refinement (动漫赛璐璐美学减重瘦身)**: slimmed `paperOutline` from 4.5px to locked 2.5px, reduced `paperShadow` from 7px block slabs to 3.5px crisp ink offset, narrowed `panelTilt` amplitude to 0.35, and locked `SubtitleChrome` and `CodeBlock` borders to 2.2px~2.5px.

## [2.6.0] - 2026-09-06

### Added

- **Dual-template consistency validation gate (`validate-skill-consistency.py`)**: expanded repository-wide validator to audit both `example-project` and `lecture-template` across layering, visual plan, speech caption sync, semantic breaks, and cue file parity, supporting structured `--json` read-only output.
- **AST syntax regression gate & test suite (`tests/test_skill.py`)**: integrated AST parsing validation across all `scripts/*.py` in `selftest.py` and provided standard regression entry point `tests/test_skill.py`.
- **Video Delivery Fact Card & Zero-Mutation discipline**: established standardized delivery metrics table in `SKILL.md` and explicit read-only / user authorization security policies.

### Fixed

- **`lecture-template` caption synchronization & semantic breaks**: synchronized 154 TTS word boundaries across 16 semantic cues (37.55s / 1126 frames) and aligned `manifests/caption-cues.json` with `src/caption-cues.json` and `audio/narration.mp3.json`.
- **`new-project` broken documentation route**: fixed `--style=paper` pointing to non-existent `references/theme-paper.md`, redirecting to canonical `references/visual-system.md`.
- **CLI unmapped timing tool**: mapped `scripts/match-timing.py` into cross-platform launcher `scripts/notebook-video.mjs` and updated reference commands.
- **Reference documentation hierarchy**: added Table of Contents to `lecture-composition.md` and `windows-compatibility.md`; flattened nested reference citations to satisfy SK003 single-hop dispatch.
- **Spec contradiction in `SKILL.md`**: removed obsolete locator ring description to align with locked visual system and quality checklist.

## [2.5.0] - 2026-09-06

### Added

- **Locked component library expansion (组件库扩容)**: `LineIcon` grows from 4 to 26 glyphs (star/fork/branch/rocket/shield/terminal/cloud/link/bug/search/user/clock/download/upload/folder/chart/globe/lock/mail/calendar/heart/settings) on the same 32-grid round-cap stroke language; seven new locked components — `CodeBlock` (terminal window with traffic lights, syntax-colored lines, per-line snappy spring entry, optional cursor), `BrowserChrome` (browser window with traffic lights + lock + URL capsule), `Connector` (bezier curve with optional flow dashes / arrow / label chip), `Checklist` (numbered rows with `done` check-state), `CountUp` (eased number roller with color transition), `ProgressBar` (track + fill + optional label/pct) and `Callout` (double-stroke hand-drawn ellipse with Caveat caption, bouncy entry). All components consume `ThemePalette` tokens only — zero hardcoded colors, so every theme skin applies automatically.
- **Locked motion pack**: `SPRINGS`/`popS` three spring presets (`snappy` for UI ticks, `soft` identical to the legacy `pop`, `bouncy` for callouts), `TransitionIn` scene transitions (`flip` page turn / `slide` cover / `wipe` edge reveal), `camScript` chainable camera-keyframe builder with guaranteed first/last-frame coverage, and `useSteppedFrame(15)` stop-motion accent. Contract docs (`SKILL.md`, `references/motion-design.md`) record the presets, the at-most-one-transition-style-per-film rule and the **no-scene-overlap rule**: the outgoing scene must fully unmount before the incoming transition starts — no frame may show two scenes at once.

### Fixed

- **`RollDigit` settles on the wrong character**: after the roll completes, the outgoing span's opacity condition kept the *old* glyph visible and hid the new one, so version badges froze on the from-value (e.g. `v1.0` instead of `v1.1`). Both spans now key purely on the turn phase, so the settled state always shows the `to` character.
- **`visual-system.md` stale camera wording**: the doc still said "fixed camera / no global zoom" from before `CameraRig` (v1.9.0); it now states CameraRig as the only legal global camera on the default route (the classic route keeps its fixed camera).

## [2.4.0] - 2026-09-05

### Changed

- **Theme backgrounds switched to locked fixed raster assets (主题背景改为固定资产图)**: `cel` / `sticker` / `flat` now render one AI-generated background image per canvas ratio instead of code-drawn SVG decorations — 9 pixel-exact JPEGs (`public/bg-<theme>-<169|43|34>.jpg`, 2560×1440 / 1920×1440 / 1440×1920) auto-selected via `useCanvas()`. The images carry the full background language (cel: aged paper + halftone + burst star + speed lines; sticker: mint grid paper + corner doodles + washi tape; flat: peeking geometric monsters on grained gray-blue paper). The retired SVG background code is deleted; the `paper` default theme stays code-drawn and untouched. All 9 assets are registered in `manifests/visual-assets.json` with sha256 provenance, and the three theme contracts now record the fixed-raster rule with "never restore the SVG background" rejection flags.

## [2.3.0] - 2026-09-05

### Changed

- **Per-theme color systems re-derived on locked S/L steps (三主题配色同阶梯重推导)**: every accent now sits on one saturation/lightness step under a single lead hue per theme — `cel` keeps blue+red co-leads (S≈80/L≈54) with green `#24bc6e` and gold `#f2b721` lifted onto the step; `sticker` keeps the pink lead and lifts blue `#5ca9e0` / green `#61d188` into the pastel band; `flat` keeps the indigo lead with coral `#f05f42`, mint `#41d27b` and sun `#f0c63c` derived underneath. Theme contracts record the step rule with a "no off-step colors" flag.
- **`flat` redesign: geometric little monsters (几何小怪兽)** replaces the mega-circle + Memphis set: a locked indigo blob monster (bottom-right) and a coral square monster (bottom-left, −8° tilt) with star / exclamation / squiggle props; the chapter header switches to dark ink on the pale base (the white-on-circle pairing is gone with the circle).
- **`flat` card & subtitle**: cards drop the 3.5px ink border + white inset liner for a 2px neutral gray hairline plus a colored offset solid shadow (indigo by default, follows the scene's semantic accent color); the full-width ink subtitle bar becomes a floating indigo pill with hard offset ink shadow and coral/mint dots.

### Fixed

- **Invisible frames on non-default themes**: example/annotation boxes across `cel`/`sticker`/`flat` used hairlines at 0.11–0.18 alpha and fills at 0.08–0.10 alpha that melted into the cards; line tokens now start at 0.42–0.45 alpha and light fills at 0.17–0.30. `sticker` cards gain a 2.5px soft-brown print edge plus a deepened two-layer shadow so the white die-cut edge stays readable on the mint page. `paper` (default) is untouched and renders byte-identical.

## [2.2.0] - 2026-09-05

### Added

- **Theme pack system (四主题皮肤体系)**: the lecture template's locked aesthetic core is now a pluggable skin behind a one-line `src/theme/active.ts` switch, selected at kickoff via `new-project ./dir --style=<id>` and enforced per-theme by contract docs and QA gates. Layout coordinates, type scale, motion contracts and validators are shared and unchanged; themes swap palette, card skin, background decoration, grade and subtitle chrome only. Progressive disclosure preserved: a production reads exactly one theme contract.
  - *`paper` (default)*: the original warm-ivory notebook, byte-identical rendering (SSIM 1.0 regression on frames 100/300/550/900).
  - *`cel` (动漫赛璐璐·分镜风)*: near-white base, 5px ink borders with hard offset shadows, deterministic ±1° panel tilt, halftone dots and speed lines, boxed ink subtitle, locked `Burst` explosion-sticker extra.
  - *`sticker` (卡通贴纸·手账风)*: pale mint grid paper, white-outlined sticker cards, hand-drawn doodles, washi-tape subtitle chip, locked `Tape` extra.
  - *`flat` (现代扁平·几何风)*: cool gray-blue base, indigo mega-circle, Memphis accents, thick ink borders with white inset liner, solid ink subtitle bar with dual accent ticks.
- **Scene soft-color tokens**: ~20 previously hardcoded scene colors (globe tint, branch lines, merge dots, idle fills, chapter-number gradient, CTA wave start, gauge tracks, check glow, stage tint, header pair) now route through 13 mandatory `ThemePalette` tokens; every theme ships its own set with `paper` keeping pixel-identical historical values.
- **Theme docs & gates**: `references/theme-system.md` plus per-theme contracts (`theme-cel.md`, `theme-sticker.md`, `theme-flat.md`) written as locked checklists with rejection flags; `validate-skill` verifies the theme pack integrity and a paper-defaulting switch; `selftest` grows to 9 checks including illegal `--style` rejection without polluting the target directory.
- **Single 16:9 demo in sticker skin**: the bundled demo asset is now one 16:9 (2560×1440) full-film rendered in the `sticker` theme, replacing the old three-canvas demo set; `assets/demo/demo-43/34` files and README ratio matrix rows are removed accordingly.

## [2.1.1] - 2026-09-03

### Added

- **Re-voicing workflow (`scripts/match-timing.py`)**: when the narration text is locked but the voice (or model) changes, snapshot the approved `manifests/chapters.json` with `--lock`, then align the new synthesis back to it — per-chapter pitch-preserving `atempo`, standard-gap re-join, loudness re-normalization and word-timing rescale. Chapter starts, scene guards and sound frames do not move; rebuild semantic captions afterwards. Verified on a 4996-frame / 22-chapter production across three voice passes.

### Fixed

- **Case-insensitive visual-asset hashes**: `validate-visual-plan` now accepts uppercase `sha256` digests (e.g. from `Get-FileHash`) instead of rejecting them as mismatches.

### Docs

- **Long-film path** (`references/remotion-architecture.md`): for newly authored long films keep `TIMELINE_SCALE = 1` and set `DURATION` to the total delivery frame count with all timing authored in delivery frames; notes the bundled template ships a 1126-frame timeline.
- **Bundler authoring pitfall** (`references/remotion-architecture.md`): documents the observed misparse of adjacent generic-annotated arrow components after dense JSX (error misreported on the following line) with verified workarounds.
- **Re-voicing procedure** (`references/tts-audio.md`): lock → synthesize → speed-post → match → rebuild-captions sequence.

## [2.1.0] - 2026-09-02

### Changed

- **Elastic Glyph Wave Typography (4段双轴弹性波浪跳字与点亮系统)**:
  - *Tibo-style 4-Stage Overshoot JumpInText*: fully ported and tuned the physical spring wave trajectory (`waveY: [14px, -6px, 1.5px, 0px]`, `waveX: [3px, -1px, 0px, 0px]`, `rotX: [40deg, -5deg, 0deg]`), delivering tactile bounce and per-glyph ignition color transition (`activeColor -> ink`).
  - *Caveat Latin Handwriting Sub-system*: integrated `Caveat-Latin.woff2` hand-drawn annotation stickers (`lonely code`, `start small`, `packaging`, `ongoing triage`, `always by your side`) for rich multi-tier typographic hierarchy.
  - *Zero-Overlap & Zero-Flicker Transitions*: implemented strict lifecycle boundary isolation (`396~412f` exit, `416f` mount) eliminating the 14s transition collision; replaced floating Module overlays with smooth `Staggered Stack Inset` file lists, completely curing 16s flicker and 17s card-header collisions.
  - *Canonical Tri-Aspect Rendering Engine*: cleanly unified responsive rendering across all 3 official 2K canvases (16:9 `2560×1440`, 4:3 `1920×1440`, 3:4 `1440×1920`) with dedicated layout compositions (`NotebookVideoFilm-16x9`, `NotebookVideoFilm-4x3`, `NotebookVideoFilm-3x4`).

## [2.0.0] - 2026-09-02

### Changed

- **Cinematic Motion & Audio System (质感与音效体系大版本跃迁)**:
  - *Tibo-style 3D Mechanical RollDigit*: added `RollDigit` component utilizing projection-compressed `rotateX` 3D flipping with `cos` perspective scaling, replacing plain pop-in transitions for numerical and version releases (`v1.0` -> `v1.1` release with green `RELEASED` badge).
  - *Idle Life & Micro-Interactions*: upgraded mascot with sinusoidal breathing motion (`1 + 0.016*sin(f*0.16)`) and natural arm-waving lifespans.
  - *Curated Audio & Lo-Fi BGM System*: integrated ambient Lo-Fi background track (`bgm.mp3`) with gentle fade-in and decay at volume `0.08` (voice-safe), accompanied by high-frequency CC0 UI feedback audio cues (`toggle.ogg` mechanical flip, `click.ogg` step trigger, `drop.ogg` card magnetic snap-in).
  - *Three-Canvas Demo Suite Refreshed*: fully re-rendered 2K demos and animated WebP previews across all three delivery formats — 16:9 (`notebook-video-demo.mp4` / `.webp`), 4:3 (`notebook-video-demo-43.mp4` / `.webp`), and 3:4 portrait (`notebook-video-demo-34.mp4` / `.webp`).
  - *Native Browser Rendering Engine*: configured direct native Chrome/Edge binary binding for instant multi-threaded zero-download rendering.

## [1.9.0] - 2026-09-02

### Changed

- **Premium motion upgrade (质感升级固化)**: the lecture template is now a cinematic-quality baseline that any future skill video inherits:
  - *CameraRig dual-canvas camera*: per-canvas keyframe tables (16:9 landscape and 3:4 portrait), Tibo-style exponential lag follow-focus, per-chapter slow push-ins.
  - *JumpInText / WaveText*: per-glyph 3D flip-in (rotateX + stagger + spring) for chapter and scene titles; per-letter wave typing with color gradient for the CTA latin string.
  - *Subtitle redesign*: torn-paper bar removed, pure centered text pinned near the bottom, per-word/per-character fade-slide with a 180ms lead; word spacing only at CJK<->Latin boundaries.
  - *Globe intro*: multi-keyframe rotate-in (150deg to 360deg with a mid-scale bulge) replacing the plain pop-in.
  - *Palette softened*: lighter ivory paper, reduced grid/texture/vignette, soft layered card shadows and thinner outlines.
- **Typography**: unified to LXGW WenKai Lite (SIL OFL 1.1; Regular + Medium) for all CJK copy, with Clash Display / Space Grotesk Latin accents. Legacy Smiley Sans / Source Han Sans assets, font-faces and license files are removed; the example-project is unified to the same stack.
- **MiMo narration**: the 30s demo timeline was re-voiced through the MiMo TTS adapter (37.55s), and the whole scene timeline was remapped word-by-word to 1126 frames (new scene starts 0/213/416/682; caption cues rebuilt to 16 semantic lines). Narration audio stays unbundled per repository convention.
- **Demo assets**: `assets/demo/notebook-video-demo.mp4` and its animated webp are refreshed for 16:9 only; the 4:3 and 3:4 previews keep the previous renders.

## [1.8.0] - 2026-09-02

### Changed

- **Widen Dependency Compatibility (拓宽依赖与通用兼容)**:
  - Widen React & ReactDOM dependency range to `^18.2.0 || ^19.0.0` across example projects and lecture templates, eliminating peer dependency lockups and enabling seamless execution on both React 18 and React 19 environments.
  - Widen Remotion dependency range to `^4.0.0` (`remotion`, `@remotion/cli`, `@remotion/media`), allowing automatic minor/patch upgrades without breaking style locks.
  - Relax Node.js engine requirement to `>=18`.
  - Refactor `validate-official-example.py` and `validate-skill-consistency.py` to validate semantic version ranges rather than brittle exact string equality.
  - Bump `browserslist` transitive dependency to `4.28.8` to resolve high severity advisory (GHSA-c83g-rgw3-j3cx).

## [1.7.0] - 2026-09-01

### Changed

- **Background redesigned to a full-canvas paper surface** (`Background` in the lecture template): the warm radial desk band outside the page, the 1.7px page outline and the offset page shadow are removed. The ivory surface (`C.paperBase`) now covers the whole canvas; the 54px grid and static dot texture stay inside the inner rule. On narrow/phone frames the paper is no longer surrounded by nested rails and rings.
- **Card text alignment fixes** in the lecture template: node card labels (`仓库/Star/Issue/Fork/PR`) are drawn inside the card whitespace instead of hanging below the card edge, and the step list in the contribution scene is compacted (item height 56→48, gap 12→8, container `top/bottom` 120/96→116/104) so the bottom `github-oss-contribute` pill no longer overlaps the fourth step.
- **TTS adapter** (`tts-openai-compatible.py`): the `voice` field is now omitted when empty instead of sending `"voice": ""` — MiMo voicedesign models reject the empty string with HTTP 400.
- **Demo assets replaced**: `assets/demo/notebook-video-demo.mp4` (1280×720) and `notebook-video-demo.webp` are fresh renders of the updated template with chapter-synced narration, no black/letterbox frames and the new full-canvas background. New canvas variants were added: `notebook-video-demo-43.mp4` (4:3) and `notebook-video-demo-34.mp4` (3:4 portrait) with matching animated webp previews, and the READMEs now show a three-canvas demo gallery.

### Added

- **One template, three canvases**: the lecture template ships a `CANVAS` switch (`'16:9' | '4:3' | '3:4'`) in `src/index.tsx`. Composition, film wrapper, subtitle strip, chrome and safe-width values come from the locked per-mode table; the 4:3 landscape reuses the landscape scene set inside a scaled wrapper, and the 3:4 portrait film uses its own single-column `*P` scene set (verified in the rendered demo). The template caption data set was refreshed to the 30s chapter-synced timeline (scene cuts 216/396/600).

### Docs

- `references/visual-system.md` background section and `references/locked-style-contract.json` background tokens updated to the full-canvas contract (`outer_gradient`/`page_outline`/`page_shadow` now `null`, `page_bounds` = full canvas).

## [1.6.2] - 2026-07-31

### Changed

- `references/tts-audio.md` and the SKILL.md TTS step add a **polyphone (多音字) handling** rule: rewrite easily-misread polyphones into reading-unambiguous, meaning-equivalent phrases directly in `narration.txt` (and mirror them into `manifests/semantic-caption-lines.txt`) instead of relying on TTS context or SSML. The adapter feeds plain text with no pinyin channel and the narration doubles as subtitle text, so a wrong reading can only be prevented at the source; keeping replacements close in character count means chapter frames barely shift. Ships a table of production-verified rewrites (重装→重新装, 批量重命名→批量重新命名, 输一行命令→输入一条命令, 钉在屏幕上→贴在屏幕上, 一模一样→长得一样) and a reminder to update matching on-screen card text.

## [1.6.1] - 2026-07-30

### Changed

- `references/portrait-illustration-system.md` gains a "choosing the vehicle" section: illustration-first is about role, not a mandate to draw everything — pick text-forward panels/checklists for definitions, lists, comparisons, sources and shock numbers, and illustration for scenes/processes, with every beat legible from the text alone or the animation alone. Two guardrails added: an inline icon must render smaller than its container box (or it spills over the corners), and stacked panels/lines need ≥50px vertical gaps to avoid a phone-screen overlap.

## [1.6.0] - 2026-07-27

### Added

- `references/portrait-illustration-system.md`: the illustration-first grammar for 3:4 portrait, verified on a produced pilot. Codifies the text-vs-graphic role split (in-scene text is a short label; full narration lives in the subtitle strip), a reusable code-drawn figure cast with subtle idle motion, a persistent faint **Ambient** scatter layer that removes empty negative space, a text-emphasis kit (highlighter marker, hand-drawn underline, contrast label pair, fast pop count-up), the three-band scene structure (heading / hero illustration / payoff), and proven process/checklist/end beat patterns.
- Guardrails carried into the doc: author strictly in the 1080×1440 design space (coordinates beyond 1080 clip), keep chapter-chrome `stage` boundaries identical to the scene-cut frames, and check the contact sheet for any transient mostly-background frame or a `0`-dwelling counter.

### Changed

- SKILL.md portrait kickoff now points to `references/portrait-illustration-system.md` alongside `canvas-modes.md`.

## [1.5.0] - 2026-07-27

### Added

- Third locked canvas: **3:4 portrait** (1440×1920 delivery, 1080×1440 design space) for portrait feeds such as Douyin. Full parameter column in `references/canvas-modes.md` plus a portrait authoring procedure: single-column stacked zones, subtitle strip at the bottom (margins 50, bottom 40, height 104), Smiley subtitle at 40px with a 900px width gate. Verified on a produced pilot; 9:16 was tested and rejected (dead lower band under platform UI).
- `validate-video` accepts the 1440×1920 container; `validate-visual-plan` canvas gate now knows all three modes and additionally cross-checks the design-space height and the subtitle strip bottom offset.
- `references/locked-style-contract.json` defines the 3:4 mode (bounds, safe width, per-mode subtitle font sizes).

### Changed

- SKILL.md kickoff question offers three canvases; canvas-modes.md consolidated per-mode subtitle sizes (44 landscape / 40 portrait) that v1.4.0 left stated only for landscape.

## [1.4.0] - 2026-07-27

### Added

- Standard delivery pace: the lecture template now ships `scripts/speed-post.py`, a deterministic post-synthesis step (`atempo=1.10`, pitch unchanged, loudness re-normalized) that also scales every timestamp in `narration.mp3.json` and `manifests/chapters.json` by the same factor. Documented in `references/tts-audio.md`; raw teaching-tone synthesis measures ~305 chars/min and prompt wording cannot hit a target pace reliably, so 336 chars/min is fixed in post.
- Save-hook ending contract in `references/pacing-rhythm.md`: knowledge-genre closing cards ask for a save with a concrete future moment (algorithms weight saves above completion for this genre), pair it with a code-drawn star animation, and keep platform references to the compliant wording without account names or links.
- Full-canvas vertical budget in `references/canvas-modes.md`: card bottoms reach ~40px above the subtitle strip; an empty lower quarter is a layout defect on phone screens.
- Three new pre-render self-check items in `references/lecture-composition.md`: body copy is pure ink (muted reserved for decorative kickers), cards consume the vertical budget, and SVG elements keep 24px clearance with no label over a graphic.

### Changed

- Subtitle strip refined: font switches to bundled Smiley Sans (designed for video subtitles, SIL OFL) at 44px with 1.2px tracking; the meaning-free blue ring decoration is removed while the orange locator bar stays. Template, caption width gate and `references/locked-style-contract.json` updated together. Verified on a produced pilot and a full episode.

## [1.3.1] - 2026-07-26

### Fixed

- `validate-visual-plan` now cross-checks canvas-mode consistency inside `src/index.tsx`: the `Composition` width (2560 or 1920) must agree with the film wrapper design width, `subtitleSafeWidth` and the subtitle strip margins. A mixed-mode file — for example a 4:3 film keeping the 16:9 subtitle margins, which shipped once and misplaced the subtitle strip — now fails validation with a precise error instead of passing silently.
- `references/canvas-modes.md` marks the four 4:3 values as change-together and adds the pre-render `validate-visual-plan` step.

## [1.3.0] - 2026-07-26

### Added

- `references/canvas-modes.md`: two delivery canvases now coexist — 16:9 (2560×1440, default) and 4:3 (1920×1440, taller mobile presence). The mode is asked once at kickoff and decides every layout coordinate; the reference carries the full parameter table (design space, subtitle strip margins, subtitle safe width, two-column budgets), a mechanical 4:3 re-layout procedure and the mobile-readability font floor. Both modes were verified on full-length productions.
- `references/pacing-rhythm.md`: the energy-curve contract — hammer frames (one full-screen quotable line per 60–90 seconds), fast/slow chapter alternation with per-segment TTS pace instructions, breathing gaps between chapters, reduced density at the close, plus a pre-render pacing gate.
- Three proven first-sentence templates in `references/narrative-hook.md` (result first / curiosity gap / conflict-contrast) with an action-density gate for the first 3 seconds, and a ban on audience-labeling or roadmap openers.

### Changed

- `SKILL.md` kickoff now asks the canvas mode (16:9 or 4:3) once per production and binds the copywriting step to the cold-open and pacing contracts.
- `validate-video` accepts both locked canvases (2560×1440 and 1920×1440); the locked style contract defines both modes including subtitle bounds.
- Lecture template font floor raised for phone readability: body 26 / label 22 / footnote 18 (titles and subtitles unchanged).

## [1.2.0] - 2026-07-26

### Added

- `assets/lecture-template/`, the new default project template: a fully validated 30-second lecture-composition film with layered source (locked core, reusable component library, clearly marked content layer) proven across a produced multi-episode series.
- `references/lecture-composition.md`: the default multi-zone code-drawn visual route — six binding rules (pure SVG graphics, multi-zone layout, text/graphic co-stars, cue-frame speech sync, demonstrative animation, series component reuse), a mechanical cue-to-frame procedure and a pre-render self-check list, written so weaker models can reproduce the established style by imitation.
- `scripts/tts-openai-compatible.py` inside the template: a provider-neutral, chapter-segmented TTS adapter for any OpenAI-compatible chat TTS endpoint, configured only through environment variables; measures real segment durations so chapter boundaries never drift, writes `manifests/chapters.json`, and caches segments by text hash.
- `new-project ./dir --classic` to copy the original visual-director exemplar for productions that accepted the image add-on.

### Changed

- Lecture composition is now the default visual route; image generation became an optional add-on offered to the user once per production, with an explicit note that its result depends on the current tool's image quality and that Codex's built-in image generation is the best-suited environment for it.
- `new-project` copies the lecture template by default; smoke tests cover both routes.
- `SKILL.md`, both landing pages and `references/tts-audio.md` updated for the default-route/add-on split and the recommended chapter-segmented TTS adapter (Edge Read Aloud remains the zero-key fallback).

## [1.1.0] - 2026-07-19

### Added

- A provider-neutral visual-director stage that selects `image-text`, `pure-text` or `pure-graphic` for every scene from the narration meaning.
- Optional Codex image-generation enhancement with complete fallbacks for other agents and local environments.
- Generated-image prompt, crop, provenance and redistribution records through `manifests/visual-assets.json`.
- `validate-visual-plan` for scene modes, start-inclusive/end-exclusive lifetimes, raster existence, SHA-256 integrity and provenance.
- An official Remotion image-plus-text example with the bitmap, callouts and exact labels animated as independent layers.
- Microsoft Edge Read Aloud as the preferred zero-key Mandarin TTS adapter when available and appropriate.

### Changed

- Upgraded the official style contract from v8 performance to v9 visual director while preserving 2K/30fps rendering, semantic subtitles, declarative audio, complete exits and automated QA.
- Updated the skill metadata, English/Chinese landing pages and project scaffolding for image-generation-aware production.

## [1.0.3] - 2026-07-18

### Fixed

- Corrected contributor attribution so GitHub recognizes the Codex collaborator instead of the unrelated `noreply` account.
- Clarified the current naming: ChatGPT is the desktop application, while Codex remains its coding mode and GitHub contributor identity.

## [1.0.2] - 2026-07-18

### Added

- A real 30-second animated showcase and four-scene preview rendered by the official engine.
- Direct release, ZIP, HTTPS, SSH, GitHub CLI and raw-contract download paths.
- Verified user-level and repository-level installation examples for Codex, Claude Code and Cursor.
- A five-minute first-run example and an AI-assisted installation prompt.

### Changed

- Rewrote the English and Chinese landing pages around the output, shortest install path and real evidence.
- Refined repository description, topics and tracked release metadata for discoverability.

## [1.0.1] - 2026-07-18

### Fixed

- CI now checks Python syntax without creating forbidden `__pycache__` files.
- GitHub Actions upgraded to pinned v7 commits with the current runtime.
- CI installs its declared FFmpeg/FFprobe system dependency before validation.
- Dependabot no longer proposes unreviewed changes to the style-locked Remotion engine.

## [1.0.0] - 2026-07-18

### Added

- Cross-platform Node launcher for the full notebook-video workflow.
- Official 2K/30fps Remotion example with synchronized narration, semantic captions and licensed fonts.
- Automated skill, layering, caption, render and packaging validation.
- English and Simplified Chinese project documentation.
- Apache License 2.0 project licensing and third-party notices.
- Provider-neutral TTS audio and word-timing adapter contract.
- Locked 900-frame asset manifest aligned with the canonical 30-second composition.

### Security

- Repository ignores credentials, private keys, caches, generated renders and local environment files.
