# Changelog

All notable changes are recorded here. The project follows semantic versioning.

## [3.1.0] - 2026-09-20

> **这是一次"纠错 + 补齐"的发布。** 起因是一个被长期误读的规矩：技能里原本写着一句
> 「零第三方依赖」（本意只是说 `scripts/` 下的 Python 脚本不许有依赖），却被执行 AI 读成了
> "整个技能不许用任何第三方库"。后果是所有成熟组件都不敢碰，画面元素全部手写 SVG——
> **恰好做出了最难复现的结果**，而这条规矩的本意正是"任何环境都能复现"。
> 本版把边界钉死、把依赖补齐、建起封装组件层，并留下可复现的验证记录。

### Added

- **`references/dependency-policy.md`（新）——依赖边界的唯一定源。** 明确三类纪律：① **禁止**按次付费、结果不可复现的生成式模型（生图/生视频 API）；② **允许且鼓励**开源、可被 lock 锁版本的 React 库（随模板一次 `npm install` 装好，**不需要额外授权**）；③ **需授权**清单之外的新库。附三条判据（要钱吗 / 能复现吗 / 能锁版本吗）、已内置清单、零依赖效果配方、社区组件库为什么不能原样粘贴，以及组件纪律与**「加一件 = 换掉一件」的增长纪律**（合规判据是「零引用」，不是一个拍脑袋的总数——见 §8）。
- **`assets/lecture-template/src/components/`（新）——封装组件层，场景的唯一入口。** 库提供结构，本层提供皮肤与帧驱动适配；颜色/边框/阴影只读 `THEME`，动画一律 `f(帧号)` 的纯函数。
  - `ui.tsx`：`Accordion`（Radix 手风琴）、`Tabs`（Radix 标签页）、`HighlightCode`（语法高亮 + 行号 + 逐行聚焦。**与 toolkit 同名的 `CodeBlock` 是两个东西，故新层改名**）、`TopicIcon` / `IconWall`（react-icons，限定 `fa` + `fi` 两套）
  - `chart.tsx`：`Chart`（d3-scale 算刻度、d3-shape 算路径，画还是我们画）、`StatRow`
  - `effects.tsx`：`GlowFrame`（流光边框）、`TiltCard`（3D 倾斜）、`ShimmerText`（文字闪光）、`RevealMask`（遮罩擦除）、`NoiseJitter`（有机抖动）、`VerdictBar`——**全部零依赖**，只是 CSS/SVG 数学 + 帧号
  - `pathfx.tsx`：`PathDraw`（描线生长）、`MorphShape`（形状连续变形）、`ShapeDraw` / `PieDraw` / `SHAPES`（参数化几何）、`SceneTransitions`（18 种官方转场）、`CameraMotionBlur` / `Trail`（运动模糊）
  - `fittext.tsx`：`FitTextBox` / `fitChineseTextOnNLines`（**中文反推字号 + 断行**）、`assertFits`（渲染期宽度门禁）
- **新增 6 个库依赖**：`@radix-ui/react-accordion`、`@radix-ui/react-tabs`、`react-syntax-highlighter`、`react-icons`、`d3-scale`、`d3-shape`（+ 类型包）。
- **新增 6 个 `@remotion/*` 官方扩展依赖**：`transitions`（18 种转场）、`paths`（描线/变形/沿线运动）、`shapes`（参数化图形）、`motion-blur`（相机模糊 + 拖尾）、`layout-utils`（实测文字尺寸）、`noise`（同种子同结果的有机抖动）。选这一族是因为它们与渲染引擎同厂、**按帧驱动设计**，不存在"库自带时间动画"的冲突。
- **`official-aesthetic-system.md` 的「Ordinary editable surface」加第 8 项**：`src/components/` 组件层是**明确允许编辑的界面**——必须"先用现成封装件，再考虑手写 SVG"。此前这 7 项可编辑范围里没有组件层，AI 读到的信号是"组件不归我管"，这是组件吃灰的直接原因之一。

### Fixed

- **SKILL.md 的「零依赖」措辞（3 处）**：
  - 开篇补一段边界声明——禁的是**付费生成式模型**，不是开源库；手写每个 UI 元素不是目标，是最慢的劣解。
  - Zero-Mutation 一节把「依赖」**拆成两种纪律**：模板**已内置**的依赖无需任何授权直接 import；**新增**清单外依赖才需授权。此前两者被混为一谈，"依赖安装须授权"这句是 AI 不敢用组件的直接原因。
  - 「`scripts/*.py` 零第三方依赖」明确限定**只针对 Python 脚本**，不是对整个技能的约束。
- **`references/fxkit.md` / `README.md` / `src/insert.tsx` 里残留的"零依赖"口号**：不再把"没引包"当卖点。`insert.tsx` 的 whip 甩镜注释原本写着"零依赖，不用 motion-blur 包"——**这正是误读的活化石**（把"不用付费模型"执行成了连官方运动模糊包都不敢用，只好手绘速度线去凑），现改为指向已内置的 `@remotion/motion-blur`。
- **README FAQ 新增一问**："能用开源的 UI 组件库吗？"——能，而且鼓励。

### Changed

- **组件清理：49 件 → 45 件（删掉 23 件从未出现在任何画面里的，加入 19 件新封装层）。** 依据是一份逐件实测的使用率审计（按真实 JSX 渲染统计，不是只看有没有 import）：

  | 模块 | 删前 | 删后 | 删掉的 |
  |---|---|---|---|
  | `fxkit.tsx` | 19 | 9 | `AIChatBox` `MailScan` `TimeRail` `CompareBars` `PayPop` `ConfettiPop` `EvidenceZoom` `KenBurnsImg` `ShakeX` `BurstCallout` |
  | `toolkit.tsx` | 11 | 3 | `CodeBlock` `Mascot` `RollDigit` `Connector` `ProgressBar` `BrowserChrome` `CountUp` `WaveText` |
  | `insert.tsx` | 3 | 1 | `InsertShot` `HandoffCarrier` |
  | `stagekit.tsx` | 3 | 2 | `Attach` |
  | `shotkit.tsx` | 3 | 2 | `DepthLayers` |
  | `plates.tsx` | 1 | — | `ShotPlate`（整个文件删除） |

  其中 `AIChatBox`（315 行）是整库里最大的一件、v3.0.3 的头号新功能，但**一帧画面都没进过**。全部删除项可从 git 历史取回（提交 `8eca144`）。

- **两处命名冲突（实测踩到，都会静默出错）**：
  - 新封装层的代码块组件原名 `CodeBlock`，与 `toolkit.tsx` 里已有的 `CodeBlock`（吃 `lines` 参数）**同名**，被静默盖住后渲染期直接报错 → 改名 **`HighlightCode`**。
  - 新封装层的 `RevealMask` 与 `insert.tsx` 的 `RevealMask` 同名 → 改名 **`ClipReveal`**。
- **门禁名单同步**：`coords-lint.py` 的 `OVERLAYS` 与 `validate-composition.py` 的 `STRUCTURAL` 里剔除了已删组件（这两处是按组件名写死的名单）。
- **接触表（`showcase.tsx`）重排**：11 页 → 10 页，删掉整页都是已删组件的第 ⑧ 页，其余页合并；新增 2 页展示封装层。
- **文档同步**：`references/fxkit.md` 目录重写（19 + 11 → 9 + 3，并补上封装层一节）、`references/media-routing.md` 路由表剔除已删件、`SKILL.md` 的组件清单指向新封装层。

### Integrated（新组件真正接进画面）

**新封装层 19 件现已全部有真实渲染记录 —— 零渲染件为 0。** 做法不是"往参考片里加场景"（那会破坏字幕与配音的时间轴契约），而是**原地替换**：在同一镜的同一帧时间轴内，用封装件换掉手写表达。

| 位置 | 换掉了什么 | 换成什么 | 为什么合适 |
|---|---|---|---|
| S1 | 三张手写卡片（324×148 ×3，各自 `enterAt`） | **`StatRow`** | 三张"标签 / 值"卡片就是指标行的形状；换后不再手写卡片、不再手写入场 |
| S8 收尾 | 一行内联 `CheckBadge` + 文字 | **`VerdictBar`**（全宽结论条） | 收尾镜需要收束感，全宽条比一行内联文字强 |

`manifests/shots.json` 的 `live` 同步加了 `StatRow` / `VerdictBar`；构图门禁复跑 P0=0（live 名字 14 → 16）。

**未接进参考片的其余 17 件**，走接触表（`showcase.tsx`，10 页 → 12 页，新增 ⑪ 路径与几何 / ⑫ 效果件）。理由：参考片的题材是"GitHub 开源入门"，`MorphShape` / `SceneTransitions` / `PieDraw` 这类没有在该题材里自然落点——硬塞进去比不用更糟。接触表是技能自己定义的"看见才会用"入口，且每件都已登记在路由表（双入口）。

> **一次记录在案的判断失误**：我一度认为 S5"声明了 chart 介质却没有图表"是个缺口，于是加了一个 `Chart`。核对 `StageFrame` 几何后发现主槽只有 **1040×518**，图表放在 `top:360` 高 300 会**超出槽底 142px**（我把"空白"看错了，那里根本没位置）；而且 S5 的 `Funnel` / `ProgressRing` **本就属于 chart 类介质**，声明并不缺失。已撤回该改动，`live` 同步去掉 `Chart`。

### Verified

在独立工程里渲染了一支 **2K / 30fps / 60 秒**组件演示片（2560×1440，1:1 输出，无放大），六个场景逐一验证：手风琴、标签页、代码高亮、图标墙、d3 图表、组合收尾。`validate-video` 通过（容器合法、时长正确、无黑帧）。

组件层另建了 5 屏冒烟夹具（`ComponentSmoke1-4` + `TransitionProbe`），确认每一件都能打包、渲染、读皮肤。

**实测踩到的中文地雷（已写入 dependency-policy.md §5.1）**：`@remotion/layout-utils` 的 `fitTextOnNLines` 实现是 `text.split(' ')`——按空格分词。中文没有空格，整段被当成一个不可断的"词"，于是只能塞进一行，字号被压到 `maxBoxWidth ÷ 字数`（44 字 / 738px 容器 → **16.77px / 1 行**，正确答案是 46px / 3 行）。**它不报错，只静默给出一个极小的字号**。故自研 `fitChineseTextOnNLines`（`measureText` + 二分 + CJK 避头尾断行），并要求**每行不得超过容器宽**——否则浏览器二次折行，实测 3 行会被折成 6 行。

### Added（第二批依赖：数据与素材计算）

**再加 8 个依赖，全部已实测能渲染**（`D:\电脑桌面\demo-video` 的 `deps-smoke` 冒烟屏，8 件一次性验证）：

| 包 | 解锁什么 | 版本 |
|---|---|---|
| `d3-hierarchy` | 目录树 / 组织图 / 树状图 | 3.1.2 |
| `d3-geo` | 地图 / 地球 / 经纬网 | 3.1.1 |
| `d3-sankey` | 流量图（转化、分流、去向） | 0.12.3 |
| `d3-dsv` | 解析 CSV / TSV——真实数据进图表的入口 | 3.0.1 |
| `roughjs` | 手绘风图形（手账风的天然契合件） | 4.6.6 |
| `qrcode` | 收尾二维码，纯计算不联网 | 1.5.4 |
| `katex` | 数学公式静态渲染 | 0.18.7 |
| `budoux` | 中文**按词组**断行 | 0.9.2 |

**体积实测（这是决定加不加的依据）**：8 个包 + 传递依赖合计约 **12 MB**，其中 `katex`(4.6 MB) 与 `budoux`(3.2 MB) 是大头且几乎全是字体与模型数据。对照 `node_modules` 总量 **1.1 GB**——`react-icons` 一个就 85 MB、Chrome 无头浏览器 270 MB。**增量约 1%，可忽略。**

冒烟屏逐件确认：目录树 / 正交投影地球 / 桑基流量图 / CSV 数据卡 / 手绘方框+圆+线 / 墨色二维码 / 积分公式 + `E=mc²` / 中文词组断行对比——**全部在我们四套皮肤下正确读 `THEME`**。

> **同时立了一份硬性待办**（[dependency-policy.md](references/dependency-policy.md) §4.4）：这 8 个依赖**目前没有任何组件封装它们**，按「零引用」判据属于"装了还没用"。**引入依赖 ≠ 获得能力**——封装成组件并登记进路由表才算。清单里逐条写了建议的封装形态（`TreeView` / `GeoView` / `SankeyChart` / `SketchFx` / `QrCode` / `MathBlock`，以及并入 `Chart` 的 CSV 入口、并入中文断行的 budoux）。

> 另记一个留给下一轮的**包体优化点**（§4.5）：`HighlightCode` 用的是 `react-syntax-highlighter` 的**全语言构建**，把 180+ 种语言的词法定义都打进了包，而实际只用两三种。该包自带 `prism-light` 轻量入口，换成 `PrismLight` + 按需注册语言是**纯赚**。

### Fixed（收尾与自纠）

- **版本号对不上**：`SKILL.md` frontmatter 仍是 `3.0.3`、`README.md` 仍写"当前 v3.0.2"，而 CHANGELOG 已到 3.1.0 → 统一为 **3.1.0**。
- **文档残留已删组件名（8 个文件约 30 处）**，其中**最危险的一类会指使执行 AI 去 import 一个不存在的组件**：
  - `shot-language.md` 的示例代码里有 `import {..., DepthLayers} from './shotkit'` 与整段 `<DepthLayers>` 用法 → 照抄直接报错，已删；
  - `fxkit.md` 仍列 `BrowserChrome` / `Mascot` 行，且**有一整节在讲 `ShotPlate`**（组件与 `plates.tsx` 都已删除）→ 已删；
  - `media-routing.md` 的「修辞动作 → 组件」表里 7 行推荐的是已删组件（`Connector` / `ShakeX` / `WaveText` / `CountUp` / `AIChatBox` / `BrowserChrome` / `CompareBars` / `TimeRail` / `ShotPlate`）→ 全部改指新封装层的对位件；
  - `README.md` / `README.en.md` 结构树里仍列 `plates.tsx`（文件已删）→ 已改，并补上 `components/` 一行。
  复检：**残留清零**。
- **`coords-lint.py` 漏检整整一层**：它只扫 `src/*.tsx`。v3.1 起组件封装层在 `src/components/`，**整个新层从未被坐标检查覆盖** → 改为 `rglob` 递归。
- **`assertFits` 是"名存实亡的门禁"**（技能自己的铁律写着「A gate that exists in name only is the most dangerous defect」）。它定义了却**从未被任何代码调用**。处置：
  - 新增 **`fitsWithin()`**——同一套 `measureText` 实测，但**只警告不抛错**；
  - 接进真正会出现"固定尺寸卡片 + 可变文案"的两个组件：**`StatRow`**（逐卡检查值文案与标签）与 **`VerdictBar`**（检查整条文案），仅开发期执行，生产渲染零开销；
  - `assertFits()` 保留为**编写期自查工具**，文档里不再称其为自动门禁。
- **路由表的"选择过载"**：多行并列了新旧三四个平级选项（如"数据/对比"同时列 `Chart` + `ProgressRing` + `MetricGrid`），等于没给建议。已改为**每行一个「首选」**，其余标注「何时才用」；并在表头写明教训：*路由表里有名字的组件照样一件不用——实测 23 件从未出现在任何画面里，其中 **21 件早已登记在本表***。

### Added（8 个新依赖全部封装成组件）

第二批 8 个依赖**全部完成封装、全部有渲染记录、全部登记进路由表**——「零引用」判据无一触发。

| 依赖 | 封装成的组件 | 文件 |
|---|---|---|
| `d3-hierarchy` | `TreeView`（目录树 / 组织图，按层级逐层展开） | `components/data.tsx` |
| `d3-geo` | `GeoView`（正交投影地球 + 经纬网，可自转） | `components/data.tsx` |
| `d3-sankey` | `SankeyChart`（流量图，带宽按数值分配） | `components/data.tsx` |
| `qrcode` | `QrCode`（二维码，自带 `delayRender` 等待生成） | `components/data.tsx` |
| `roughjs` | `SketchFx`（手绘风，**画出的线条可"自己画出来"**）+ `sketchCircleArea` / `sketchUnderline` / `sketchBox` | `components/sketch.tsx` |
| `katex` | `MathBlock`（公式块，静态渲染） | `components/ui.tsx` |
| `d3-dsv` | 并入 `Chart` 的 `csv` 入口 + `csvToChartData()` | `components/chart.tsx` |
| `budoux` | 并入 `fitChineseTextOnNLines()`（断行优先落词组边界） | `components/fittext.tsx` |

接触表 12 页 → **14 页**（新增 ⑬ 结构化数据→图形 / ⑭ 手绘风与公式），14 页逐一实渲抽样验证通过。

**关于 budoux 的诚实结论**：它是**辅助不是保证**。实测它对"反推"「并返回」这类词也会切错（切成 `反|推该`、`并返|回断`），模型本身不够准。所以标题可以依赖它的断点，正文别指望；断行仍是"能落词组边界就落，落不了按字断并遵守避头尾"。

### Fixed（本轮抓到的缺陷）

- **`DiffView` 在接触表里一直渲染失败**（**原就存在的 bug**，本轮第一次把 14 页全部抽样才暴露）：示例数据的第一行漏了 `at` 字段，而类型要求 `at: number`，`undefined` 传进 `spring({frame})` 触发 Remotion 的 `Argument passed for "frame" is not a number`。已补 `at: 0`。
- **`Chart` 的 `d3line(...)` 仍传旧的 `data` 变量**：加 `csv` 入口时批量替换只改了 `data.length` / `data.map`，漏了传给 `d3-shape` 的裸参数，用 `csv` 时 `d3-shape` 收到 `undefined` 抛 `undefined is not iterable`。已改为 `rows`。
- **`TreeView` 的 `viewBox` 切掉根节点顶沿**（根节点 `y=0`，上沿在 `-nodeH/2`，而 `viewBox` 从 `-10` 起）。已改为从 `-(nodeH/2+8)` 起。
- **`SketchFx` 每帧重画会叠加笔迹**（roughjs 是往 DOM 里 append，不清空就越画越重）→ 每次绘制前 `svg.innerHTML = ''`。

### Verified（补充）

- **四套皮肤全部实渲验证**（此前只验了 cel 与 paper）：`StatRow` 在 **flat** 皮肤、`VerdictBar` 在 **sticker** 皮肤下均正确适配——圆角、描边、投影、配色全部随 `THEME` 变化，证明"新组件只读 THEME"的设计成立。至此 **cel / paper / sticker / flat 四套全覆盖**。
- **模板整片端到端渲染通过**（此前只渲过单帧）：`audio/narration.mp3` 按设计不随包发布（技能文档明说 intentionally not bundled），验证时用等长静音占位跑通管线。成片 **2560×1440 / 30fps / 1150 帧 / 38.38 秒**，`validate-video` 报容器合法、**无黑帧**（响度项 -21.5 LUFS 是静音占位的必然结果，非缺陷）。这同时证明 S1 的 `StatRow` 与 S8 的 `VerdictBar` 替换在整片 1150 帧里没有引入任何渲染期错误。

### 关于「组件总数」的诚实结论

**本版未能达到「20 件左右」的目标，且经核算是不可达的。** 45 件的构成：

| 类别 | 件数 | 能否再减 |
|---|---|---|
| 引擎/结构件（3 骨架 + `ShotCamera` `StageFrame` `PhaseRail` `CoverPanel` `RevealMask` + `LineIcon` `CheckBadge` `PillTag` `FitCard` `StampBanner`） | 12 | ❌ `validate-composition.py` 的 `STRUCTURAL` 集合就是这份名单；骨架门禁要求 ≥3 种且相邻不得重复 |
| 旧表意件 | 14 | ⚠️ 全部在参考片里真的被用过 |
| 新封装层 | 19 | ⚠️ 全部已进画面（参考片 2 件 + 接触表 17 件） |

要减到 20，需要再删 25 件——**只能是删掉引擎件或在用的表意件**。继续合并的边际收益很低：逐对核对后，真正"同一修辞动作、两套实现"的只有 4–5 对（`GlowFrame`/`TiltCard`、`ProgressRing`/`PieDraw`、`StaggerList`/`Checklist`、`ClipReveal`/`RevealMask`），合并后约 40 件，而每一对都各有一点对方没有的能力（`TiltCard` 的 3D 透视、`ProgressRing` 的中央数值、`StaggerList` 的副标题行、`RevealMask` 的镜头级交接）。

**故本版的处置是：不再做有损合并，改为把"不再膨胀"写成纪律**（[dependency-policy.md](references/dependency-policy.md) §8「加一件 = 换掉一件」），并把选择收敛到路由表的单一首选上——**让库变窄，而不是变小**。

### Known gaps（未完成，勿当作已解决）

- **组件总数仍是 45 件，未达到「20 件左右」的目标。**（第一步"删死件"已完成、新封装层也已全部接入画面；缺的是第二步"合并替换"。） 本版完成了第一步（**删掉全部 23 件从未出现在任何画面里的组件**），但第二步（**合并功能重叠**）未执行。现状拆解：

  | 类别 | 件数 | 能否再减 |
  |---|---|---|
  | 结构/引擎件（3 骨架 + `ShotCamera` `StageFrame` `PhaseRail` `CoverPanel` `RevealMask` + `LineIcon` `CheckBadge` `PillTag`） | 11 | ❌ 门禁要求 ≥3 骨架且相邻不得重复；相机与舞台框是引擎底座 |
  | 旧修辞件（`FitCard` `Typewriter` `StampSeal` `Funnel` `ChatThread` `ProgressRing` `StaggerList` `DiffView` `SkeletonCard` `Callout` `Checklist` `JumpInText` `ConsoleWindow` `MetricGrid` `StampBanner`） | 15 | ⚠️ 全部在参考片里真的被用过；再减就是删能力 |
  | 新封装层 | 19 | ⚠️ 其中多数是替代形态（`Chart` 替代手写图表、`HighlightCode` 替代 toolkit 的代码窗），但旧件尚未移除，**当前处于新旧并存的过渡态** |

  **下一步（未执行）**：按「加一件 = 换掉一件」把新封装层与旧件一一对上——`Chart` ⇄ `MetricGrid`/`ProgressRing`、`HighlightCode` ⇄ `ConsoleWindow`、`Accordion`/`Tabs` ⇄ 对应的卡片堆表达、`FitTextBox` ⇄ 手写 `fitH` 估算；每换掉一件就改一处场景、跑一次门禁。**这需要动参考片的 `scenes.tsx`，必须单独一轮、逐个模块做，不能一次性重写。**
- **`example-project` 未同步依赖与组件层——这是设计如此，不是缺口。** 它是**单文件工程**（`src/index.tsx` + `caption-cues.json`，没有 theme/、没有组件目录），定位是「经典路线的最小可读示例」，用来演示可选的生图附加路线（`Img` + 实拍素材框）。给它塞 12 个依赖和一整套组件层，只会把它变成第二个 `lecture-template`，并重新制造本版刚清掉的膨胀。**后续请勿"顺手补齐"它。**

### Added（第三批：组件库升级 —— 按《组件库调研报告》逐条施工）

调研报告（`D:\电脑桌面\组件库调研报告.md`）的第六节分批清单已**全部执行完毕**，并先跑完了第七节
「必须实测才能定的 8 项」中的 4 项关键实测。本轮新增 **3 件封装件**、**11 个 npm 包**（约 0.85 MB），
净组件数 25 → 27（严格按「加一件 = 换掉一件」：`ControlStack` 换掉了 `TiltCard`）。

**第 0 步 · 4 项关键实测（先做，可能推翻后面的计划）**

| # | 实测什么 | 结论 | 证据 |
|---|---|---|---|
| ① | Radix Portal 的 `container` 落点 | **通过** | `diag-up-1-portal.png`：四件弹层全部 `挂载点=画面根`、完整在 1920×1080 内；Dialog 实测矩形 `x=480 y=130 w=420 h=134` 与给定坐标逐像素一致。**附带发现：Popover/Tooltip/DropdownMenu 的落位是异步的**（floating-ui `computePosition` 在微任务里 resolve，实测要 8 轮渲染才稳）→ `OverlayFrame` 因此不用它的自动避让，把锚点钉死在我们给的坐标上 |
| ② | `d3-force` 确定性 | **通过** | 同一帧渲两次，PNG 的 SHA-256 完全一致（接手复核时用当前代码重跑：`600210d7…`）；第 3 帧哈希不同。d3-force 产物里 `Math.random` 0 处、用固定种子 LCG。**附带发现：力导向的自然结果会溢出画框**，必须按包围盒归一化 |
| ③ | treemap / pack / sunburst 的中文字号 | **通过（修正两轮）** | 第一版渲出来：treemap 全是 20px 细条（三个布局共用了一个 `hierarchy()` 根，互相覆盖）、旭日图的环**一个都没画**（`d3.arc` 默认访问器要 `{startAngle,endAngle,innerRadius,outerRadius}`，传 partition 节点返回 null 而不报错）、treemap 有标签宽度合规但高度顶出格子。修正后过窄的格子自动降级（不画字 + 图例）。**接手复验时抓到第二处**：旭日图的标签是**沿切线写一整行**的，而反推字号按 2 行算——口径不一致时「帧参数名 / 构图与活性」单行超出弧长、横压到隔壁扇区上。已改为 `maxLines=1` 反推（放不下的自动进图例）。最终口径一致后：**treemap 10/10 无溢出、pack 10/10 无溢出、sunburst 0 溢出 / 5 个过窄项降级** |
| ④ | 图标族混排的风格漂移 | **通过** | `diag-up-4-icons.png`：`fi` 与 `lu` 并排**肉眼无法分辨**（`react-icons` 里两族同源同款），无漂移；唯一可测差异是 `LineIcon`（32 视窗 / 2.2 笔画）与 `fi`·`lu`（24 视窗 / 2）的视觉重量 → `TopicIcon` 统一压一档 `strokeWidth = 2.2×24/32 = 1.65` |

**批次 1 · 拟真控件（最值钱的一项）**

- **新组件 `ControlStack`**（`components/ui.tsx`）：开关 / 复选 / 单选 / 滑块 / 分段 / 进度条六种形态，
  状态由 `steps: [{at: 帧, value}]` 这张**显式的表**决定（`controlStateAt()` 是导出的纯函数，可复算）。
  离散件在 `at` 帧瞬切，连续件在 `glide` 帧内线性滑到位。
  替换掉什么：技能此前**完全没有**「控件被改变」这个形态——要讲"这个选项被打开了"只能写一张文字卡片假装，
  而 `validate-composition.py` 的硬门禁恰恰要求每个讲解场景 ≥1 个真的随旁白变状态的构件。
- **换掉 `TiltCard`**（按「加一件 = 换掉一件」）：它与 `ShimmerText` 在"强调一瞬"上重叠，且 3D 透视与四套皮肤都不合。
  已从 `effects.tsx` / `index.ts` / 接触表 / 两张路由表 / `fxkit.md` 一并清掉。
- 6 个 Radix primitive 的版本与许可逐条核对：`react-switch` 1.3.7 / `checkbox` 1.3.11 / `radio-group` 1.4.7 /
  `slider` 1.4.7 / `toggle-group` 1.1.19 / `progress` 1.1.16，**全部 MIT**。

**批次 2 · 拟真弹层（前置的 Portal 实测已通过）**

- **新组件 `OverlayFrame`**（`components/overlay.tsx`）：`dialog` / `menu` / `popover` / `tooltip` 四种形态，
  `steps: [{at, open}]` 决定显隐。Portal 的 `container` 指到**本组件自己的宿主节点**（不是 `document.body`）。
  替换掉什么：此前所有"界面感"都压在 `ConsoleWindow` 一个件上，"弹一个确认框 / 下拉里选一项 / 气泡说明"只能画静态线框。
- 两处实测逼出来的细节：Dialog 的 a11y `Title` 必须**视觉隐藏**（否则它会占掉一行文档流、把弹层整体往下推，
  实测标题跑到盒子外面）；`menu` 的选中项是**单选语义**（`selected: [{at, value}]`），不是累积高亮。

**批次 3 · 关系网络**

- **新组件 `NetworkGraph`**（`components/network.tsx`）：`d3-force` 力导向布局。
  确定性三道保险：**初值显式给定**（按序号摆一圈，不用库的默认螺旋）、**迭代次数写死**（默认 300）、
  立刻 `.stop()` 掉内部 d3-timer。算完按包围盒**等比归一化并居中**（实测不归一化会有节点被裁在框外）。
  替换掉什么：此前只有树（d3-hierarchy）与流向（d3-sankey），表达"谁连着谁"只能硬套树——而树会凭空造出一个不存在的上下级。

**批次 0 剩余 4 项（零新依赖，全部是"打开已经装好的"）**

- **`Chart` 加 7 个 `variant`**：`line`（默认）/ `area` / `stack` / `stackExpand`（百分比堆叠）/ `stream`（河流）/ `radar` / `pie`。
  多序列走 `series`，多序列 CSV 入口 `csvToChartSeries()`。**柱宽改由 `scaleBand` 给出**，替掉原来手算的 `barW`。
  同时补齐 `CHART_BOX` 常量：所有变体共用同一套内边距，所以 `fitH()` 的高度契约不因变体而变。
- **`TreeView` 加 3 个 `variant`**：`treemap` 矩形树图 / `pack` 圆形打包 / `sunburst` 旭日图（`partition` + `d3.arc`）。
  标签一律先过新导出的 **`fitNodeLabel()`**：宽度与高度**都要**过，反推字号 < 13px 就**降级不画字**并进图例。
- **放开 `react-icons/lu`（Lucide 1541 字形）**，`TOPIC_ICONS` 从 14 个扩到 34 个（新增 brain / bot / rocket / sparkles /
  check / bug / ruler / gauge / workflow / milestone / wrench / zap / fileCode / server / shield / trend / puzzle / idea / flag / refactor）。
  **不引 35 MB 的 `lucide-react`**——`react-icons/lu` 里就是同一批字形。图标政策同步改写为
  `fa`（品牌实心）+ `fi`/`lu`（线条）+ `si`（仅品牌 logo），并写死纪律：**`LineIcon` 仍是主图标语言、只有 `color` 可来自 THEME**。
- **`@remotion/shapes` 补齐**：`SHAPES` 新增 `callout`（标注框）/ `arrow` / `heart` / `ellipse` / `rect` / `triangleShape`。
  **`PathDraw` 新增 `showArrow`**：用 `getTangentAtLength` 让箭头沿路径自动转向（此前要自己差分算切线）。

**实测抓到的缺陷（都是"不报错但画错"的那一类）**

- `treemap` / `pack` / `partition` **共用同一个 `hierarchy()` 根** → 后跑的布局覆盖先跑的 `x0/x1`，treemap 渲成一片细条。已改为每个布局各拿一个根。
- `d3.arc` **默认访问器**读的是 `{startAngle,endAngle,innerRadius,outerRadius}`，传 partition 的 `{x0,x1,y0,y1}` 返回 `null` 而不是报错 → 旭日图的环**一个都没画出来**，只剩标签。已显式设置四个访问器。
- `d3stack` 的入参是**数据点数组**（`points[i][si]`），直接传 `series` 数组等于转置错 → 堆叠图只铺了 40% 宽、且是三块近似水平的色带。已显式转置。
- `TreeView` 的**标签只检查宽度、不检查高度** → 150×60 的格子被反推到 34px 两行、整块 68px 高顶出格子。`fitNodeLabel` 现在两个约束都要过。
- 旭日图标签原本**沿半径方向**排且下半圈不翻转 → 环宽只有 ~55px 放不下几个字，圆心下方的标签全是倒着的。已改为沿切线排 + 下半圈翻 180°。
- `Chart` 的 `pie` 变体原本取 `series[0].values` 整列当扇区 → 只画出一块 100% 的饼、图例全是 `undefined`。已改为「一个序列 = 一个扇区」。
- 雷达图半径原按 `min(innerW,innerH)/2 − 74` → 只剩 135px，四个维度挤在中间像一个墨点。已收紧留白到 56 并把接触表的画布调高。

**第二轮复验（接手后逐页实渲 + 独立复跑）**

前一位施工者被中途取消，留下的三张新页（⑮⑯⑰）与 ⑫ 页**没有被完整看过**。接手后重新同步、逐页实渲并逐张看图，
抓到并修掉三处"不报错但画错"的缺陷：

| # | 缺陷 | 处置 | 证据 |
|---|---|---|---|
| 1 | **旭日图标签单行溢出**（口径不一致：反推按 2 行、实画 1 行）→「帧参数名 / 构图与活性」横压到隔壁扇区，下半圈两个标签互相叠字 | `data.tsx` 旭日图分支改 `fitNodeLabel(..., maxLines=1)`，放不下自动进图例 | `renders/upgrade/fresh-465.png`（修前）→ `fix-465.png`（修后） |
| 2 | **关系网节点标签被拆成两行**：「服务端」→「服务 / 端」，一个孤字吊在下面 | `network.tsx` 改 `fitNodeLabel(..., maxLines=1)`：单行反推字号反而更大（r≈43 的圆给 18.6px，一行 56px 宽 < 弦长 87px） | `renders/upgrade/crop-net.png` → `crop-net2.png` |
| 3 | **面积图首个数据点的数值标签压在 Y 轴刻度上**（`12` 叠在 `20k` 上）：area 变体的 X 铺满整宽，首尾点贴边、标签仍居中 | `chart.tsx` 只在 area 的两端改用 `start`/`end` 锚点，标签始终留在绘图区内 | `renders/upgrade/crop-area.png` → `crop-area2.png` |
| 4 | **`fillStyle:'dots'` 让整页不可复现**（报告第七节第 3 项"帧间稳定性"**不通过**）：同一帧渲三次得到**三个不同哈希**，差异恒定落在 contact ⑭ 页 dots 那一格 | 读 `node_modules/roughjs/bundled/rough.cjs.js` 定位到根因——dots 填充器在 `dotsOnLines` 里**无条件调 `Math.random()` 两次/每点**，与 `seed` 无关（其余填充器都走种子化 LCG）。**把 `'dots'` 从 `SketchStyle.fillStyle` 移除**，接触表该格换成确定性的 `'dashed'`；同时写明第二个坑：**`seed: 0` 是假值**，roughjs 的 LCG 写作 `this.seed ? … : Math.random()`，传 0 会让所有填充退回真随机 | 修前 `sweep-p14` / `sweep2-p14` / `p14-b` / `p14-c` 四个哈希两两不同；修后同帧两次均为 `1cda0b0f5bc5174f71c1bd7bfd094691` |

> 第 4 条是**本轮最值钱的一条**：它不是"画得不好看"，而是"同一份代码渲不出同一支片"——
> 正是 `dependency-policy.md` 三条判据里第 2 条要防的事，而且**它藏在 `fillStyle` 的一个枚举值里**，
> 不逐帧比对像素根本发现不了。结论已回写 `dependency-policy.md` §4.2 / §4.4 与 `media-routing.md`。

**同时修掉了探针自身的口径漂移**：`diag-upgrade.tsx` 的页③原本**自己复写了一份** fitLabel（多算一行高度），
量的是替身不是本体——现在直接 import `components/data.tsx` 的 `fitNodeLabel`，并按各变体实画的行数传 `maxLines`。

- **同步与打包**：`assets/lecture-template/src/components/*`（10 个文件）与 `src/showcase.tsx` 与验证工程**逐字节一致**（`diff -rq` 无输出）；`remotion compositions` 列出 `NotebookVideoFilm 1150f` 与 `NotebookVideoShowcase 510f`（17 页 × 30f）两份合成，打包通过。
- **逐页实渲**：17 页各渲一帧（第 N 页取 `frame=(N-1)×30+15`），17 张全部出图、无一失败；拼成两张接触页逐张看图，**无一页空白/塌版**。新增与改动的 ⑫⑮⑯⑰ 另按 1:1 放大逐格核对（见上表三处缺陷即由此抓出）。
- **确定性复验（用当前代码重跑）**：`diag-upgrade` 页② 同一帧渲两次 → MD5 均为 `3b507703684b9565ea41a6ca300e2c73`；接触表第 ⑯ 页（treemap / pack / sunburst / NetworkGraph 四件同页）同一帧渲两次 → MD5 均为 `bd0eee5bcf9a1ab82388eae3297ccae7`；第 ⑭ 页修正 `dots` 后同一帧渲两次 → MD5 均为 `1cda0b0f5bc5174f71c1bd7bfd094691`。另渲第 30 / 33 / 42 帧三个不同帧，MD5 两两不同（`975bd1a7…` / `5b7cbc85…` / `3b507703…`）——**布局是算出来的，不是写死的，且逐字节可复现**。
- **跨进程复验（隔日重渲）**：把今天重渲的 17 页与**前一次（另一个进程、前一天）**的 17 页逐页比 MD5 —— ①–⑬ 与 ⑰ **全部逐字节相同**；⑭ 不同（即上面第 4 条 `dots` 不确定性，已修）；⑮⑯ 不同（即第 1–3 条修复生效）。**"跨天跨进程像素一致"这一条比同进程重渲强得多**，因为后者可能只是缓存命中。第 ⑰ 页（四个 Radix 弹层）隔日重渲 SHA-256 相同（`f0e17beb…`）——**floating-ui 的异步落位在本工程里不破坏可复现性**，这条实测同时给了 `OverlayFrame`。
- **本轮的四个关键结论（一句话版）**：① Radix Portal 落点 **通过**（四件弹层挂载点全是画面根、矩形完整在画布内，Dialog 实测 `x=480 y=130 w=420 h=134` 与给定坐标一致）→ 批次 2 放行；② `d3-force` 确定性 **通过**（同帧两次哈希一致、不同帧不同）；③ treemap / pack / sunburst 中文字号 **通过**（口径统一后 0 溢出、过窄项自动降级进图例）；④ 图标族混排 **通过**（`fi` 与 `lu` 并排肉眼无法分辨；`LineIcon` 与它们的唯一可测差异是 32/24 视窗的笔画重量，已用 `strokeWidth = 1.65` 对齐）。**另加一条报告里没有的**：`fillStyle:'dots'` 确定性 **不通过** → 已按"不硬绕"的原则直接从枚举里移除并回写政策。
- **lockfile 逐条核对**：`npm install --package-lock-only` 后 `npm ci --dry-run` 通过（lock 与 `package.json` 一致、可解析）；lock 里 12 个 Radix 包齐备且版本与调研报告逐一相符——accordion 1.2.20 / checkbox 1.3.11 / dialog 1.1.23 / dropdown-menu 2.1.24 / popover 1.1.23 / progress 1.1.16 / radio-group 1.4.7 / slider 1.4.7 / switch 1.3.7 / tabs 1.1.21 / toggle-group 1.1.19 / tooltip 1.2.16，外加 `d3-force` 3.0.0。`lockfileVersion 3` / 451 条目 / 根依赖 36 + 开发依赖 8，与 `package.json` 一致。
- **四道门禁以当前代码复跑，P0 全为 0**：`validate-frame-props`（P0=0 P1=0 → PASS）· `validate-composition`（P0=0 P1=5 → PASS）· `validate-skill-consistency`（通过，两个模板均有效）· `negative-gate-check`（A–H 八项全 PASS，含阴性对照 E）。

**第三轮收尾（把上一轮自己列的 6 条未完成项做完）**

**① `TreeView` 默认 `tree` 变体的两处观感缺陷（用户看得见的那一类）**

根因与修法（`components/data.tsx`，全部有实渲与 DOM 实测）：

- **同层框重叠**：原来用 `d3.tree().size([width-nodeW, …])`——`size()` 会把布局**归一化**到给定宽度，而框宽是固定像素。
  实测同一份数据里 `ui`/`chart`/`data` 的中心只隔 **95.2px**，而框宽 116px → 每对兄弟重叠 21px。
  改为 `nodeSize` 在**槽单位**里布局（1 槽 = 1 个兄弟位，不被归一化），渲染时把 1 槽换成 `slotW` 像素；
  框宽由两个约束联立解出：`boxW ≤ (availW − gapX·spanU)/(spanU + 1)`（第一版漏了 `+boxW` 项，实测左右两端各被裁掉 4px）。
- **标签出框**：节点名当时**完全没过反推**，`notebook-video`（14 个半角字符）宽出框沿。
  新增导出 **`fitOneLine()`**：先按反推字号放下，降到下限 13px 仍放不下就**截断加省略号**（树节点不能没有名字，
  这一点与 treemap/pack/sunburst 的"放不下就不画字、改走图例"分工不同）。
- **实测证据（`diag-upgrade` 页⑤，量真 DOM 的 `getBoundingClientRect`）**：
  常规树（9 节点）同层最小间距 **22.0px**、重叠对数 **0**、标签溢出 **0**；
  密集树（15 节点 / 10 叶）最小间距 **22.5px**、重叠 **0**、溢出 **0**（走的是缩框路径）。
  接触表 ⑬ 页 frame 375 放大目视：根节点显示为 `notebook-video`（140px 框下自动缩小字号后完整放下），四行框各留空隙。
- **四个变体全部复验**：`tree`（⑬ 页 375 帧）· `treemap`/`pack`/`sunburst`（⑯ 页 465 帧）逐个放大看图，均正常。
- 顺带修掉一个探针暴露的稳健性问题：**"过窄未标注"图例过长会横穿出图框**（`textAnchor="end"` 越长越往左顶，
  而 SVG 是 `overflow:visible`）→ 图例最多列 5 项，其余折成 `…等 N 项`。

**② 四皮肤一致性（此前只在 `paper` 下实渲过）**

- 补渲 **cel / sticker / flat** 三套皮肤 × 接触表 ⑫ 页（`ControlStack` 六控件 + `TopicIcon`）与
  ⑮ 页（`Chart` 的 area / stackExpand / radar / pie 四变体），共 6 张（`renders/upgrade/skin-<skin>-p<345|435>.png`）。
- 逐张看图结论：**圆角、描边、投影、配色全部随 THEME 变化**——cel 是饱和三色 + 深描边、sticker 是薄荷底 + 粉/黄/绿马卡龙、
  flat 是细灰边 + 彩色硬偏移投影；控件没有残留浏览器默认样式（滑块/开关/进度条全部吃主题色），
  图表在四套皮肤下都不出界、不裁字。渲完已把 `theme/active.ts` 切回 `paper`。

**③ 诊断探针的判据缺陷（全部改为"量真实组件"）**

- 页①：不再自己拼 Radix 的四个 primitive，改为渲染**真实 `OverlayFrame`** 四种形态，
  按组件自己的实现口径核对落点（dialog 用 left/top 钉死；popover/menu/tooltip 是 `side="bottom"` + sideOffset 2/12）。
  实测 **PASS 4/4，偏差全部 (0.0, 0.0)**：dialog x=120 y=170 w=460 h=301、menu x=700 y=182、popover x=120 y=522、tooltip x=700 y=522，
  四件均"完整在画布内=是 / 挂载点=画面根"。**同时修掉上一版"定位状态：仍未落位"的误判**——
  根因是判据去看 floating-wrap 的 `transform`，而 Dialog 的父节点就是画面根、根本没有那一层；
  另外**必须量到落位稳定**（floating-ui 的 `computePosition` 在微任务里 resolve：第一轮量出来 menu 是 y=-688、偏差 -870，而画面其实是对的）→ 探针改为"连续两轮完全一致"才收工。
- 页②：几何直接取自组件导出的 **`layoutNetwork()`**（探针不再重算），画面用**真实 `NetworkGraph`**；
  同一份输入给两个帧号（f=36 / f=90）并排，一眼看出"布局是算出来的、动画是帧驱动的"。
- 页④：不再直接 import `react-icons`，改为渲染**真实 `TopicIcon` / `LineIcon`**，
  并从渲染出的 `<svg>` 上**读回真值**：`LineIcon` viewBox `0 0 32 32` / stroke-width **2.2**；
  `TopicIcon` 的 fi 与 lu 都是 viewBox `0 0 24 24` / stroke-width **1.65**（= 2.2×24/32，三族视觉重量对齐的口径落地）。
- 页③ 保持"直接调组件的 `fitNodeLabel`"（上一轮已改）。
- **另加两页**：页⑤ 目录树（上面①的证据）、页⑥ **全部 20 种转场逐格实渲**（下面 ⑤a 的证据）。

**④ `seed: 0` 运行期护栏（`components/sketch.tsx`）**

- roughjs 的 LCG 写作 `this.seed ? imul(48271, seed) : Math.random()`——**0 是假值**，
  `seed: 0`（或第一个图形算出的 `0 + 0*7`）会让整条随机链退回真随机。
  现在：`base.seed` 为假值时**打印明确告警**（写清后果与修法）并**自动改用 seed=1**。
- **这条告警刻意不加 `NODE_ENV !== 'production'` 门**（本仓库其它开发期告警是加的）：
  渲染包由 webpack 以 production 模式打包，`process.env.NODE_ENV` 会被替换成 `'production'`——
  加门等于"真正出片的那条路径上永远看不到告警"（第一版就是这么写的，探针实测**捕获到 0 条**，
  改成无条件后才捕到）。它只在作者真的传了 0 时才响，正常渲染零噪音。
- **实测证据（`diag-upgrade` 页⑤ 底部新增的两格：同一个图形，左 seed=0 / 右 seed=3）**：
  ① 告警被探针捕获并印在画面上（`seed:0 护栏告警捕获：1 条 →「[SketchFx] style.seed 传了 0…」`）；
  ② 同一帧渲两次**逐字节一致**（MD5 `cf2ff839…`）→ "给 0 也不会产出不确定结果"这条成立；
  ③ 该改动不影响既有画面——接触表 ⑭ 页（用到 `SketchFx`）重渲后与改动前**逐字节相同**（`1cda0b0f…`）。

**⑤ 三件遗留**

- **`@remotion/transitions` 全部登记**：`PRESENTATIONS` 从 5 种补到 **20 种**（`fade` `slide` `wipe` `flip` `clockWipe` `iris`
  `dissolve` `ripple` `zoomBlur` `filmBurn` `bookFlip` `swap` `crosswarp` `crossZoom` `zoomInOut` `dreamyZoom`
  `blurSlide` `linearBlur` `pushCut` `none`），签名统一收一个 `{direction,width,height}` 的 ctx。
  经查 **`@remotion/transitions` 全包 `Math.random` 0 处**；`filmBurn` 的 `seed` 显式写死 7。
  **逐格实渲（`diag-upgrade` 页⑥，25%/50%/75% 三帧）**：20 格全部 A→B 生效，**12 种 WebGL 着色器式在无头 Chrome 里全部可用**，
  三帧互不相同（帧驱动成立）。唯一要说明的是 `flip` 在 50% 处正好侧对镜头、那一格看着是空的（25%/75% 正常）。
  已登记进 `media-routing.md` 与 `fxkit.md`。
- **`HighlightCode` 换 `PrismLight`**：从全语言构建（`import {Prism}` → `refractor` 全量入口）改为
  `PrismLight` + `PRISM_LANGUAGES` 按需注册 6 种语言（tsx / ts / python / bash / json / diff，含 ts/js/sh/py 别名）。
  源侧体积：`refractor/lang` 共 **277 个语言文件 / 0.83 MB** → 我们只要 **8 个 / 30 KB**。
  **实渲确认**（接触表 ⑨ 页 frame 255）：关键字/字符串/JSX 标签/Tag 配色与行号、逐行聚焦高亮全部照旧。
- **两份 lock 的一致性（查清楚后才处置）**：
  - 逐条比对模板 lock 与验证工程 lock 的 **44 个直接依赖**：**41 个一致**，3 个不一致 ——
    `remotion` / `@remotion/cli` / `@remotion/media` 在模板 lock 里是 **4.0.489**，而验证工程是 **4.0.526**；
    同一份模板 lock 里 `@remotion/transitions` 等又是 **4.0.526** → **模板 lock 自身版本混用**（Remotion 要求全家族同版本，用户 `npm install` 会装到跑不起来的组合）。
  - 处置：重生模板 lock（删掉后 `npm install --package-lock-only`）→ **Remotion 家族 33 个包全部 4.0.526**（= npm `latest` = 我实测验证的版本）。
  - 重生成后仍有 2 个不一致：`react` / `react-dom` → 模板 **19.3.0**，验证工程 **19.2.7**。
    按"**以模板 lock 为准**"，把验证工程升到 **19.3.0** 并**重跑全部渲染**（见下：17 页 + 6 探针 + 两支成片都是 19.3.0 下渲的）。
  - 结论：两份 lock 现在**解析出的直接依赖版本完全一致**；形式差异（模板 caret / 验证工程 exact）是刻意的——
    模板要能被用户 `npm update`，验证工程要钉死复现。已写进文档。

**⑥ 整片与接触表的完整渲染**

- **接触表 510 帧整支 mp4**（1920×1080，17 页 × 30 帧）与**整片 1150 帧 mp4**（2560×1440，38.33s）都在**对齐后的版本**下重渲，
  并跑 `validate-video` 校验容器/时长/黑帧（结果见下）。
- 17 页 still 与上一轮逐页比对 MD5：**1–12、15、16、17 页逐字节相同**（说明 react 19.3.0 升级没有引入任何像素变化），
  ⑬⑭ 两页的差异正好落在本轮改动的那两块（目录树布局 / SketchFx 填充格）。

**第四轮：装上真实配音（小米 MiMo TTS · 男声白桦）——响度缺口闭合**

> ⚠️ 本节把配音压进了锁定时间轴，已被下面「第四轮修正」推翻（用户反馈语速太快）。原文保留以便对照。


上一轮最后一条未过项是 `validate-video` 的「Integrated loudness outside target range: -21.5 LUFS」，
根因是 `audio/narration.mp3` 一直是**等长静音占位**。本轮用真实 TTS 补上，整片重渲后**该项通过**。

**① 接入配方（写进 `references/tts-audio.md`，key 只走环境变量，未落任何工程文件）**

| 项 | 值 |
|---|---|
| Base URL | `https://api.xiaomimimo.com/v1` |
| 鉴权 | `Authorization: Bearer $TTS_API_KEY` |
| TTS 模型 | `mimo-v2.5-tts`（`GET /v1/models` 实测列出 6 个模型） |
| 音色表 | `mimo_default` · `冰糖` · `茉莉` · `苏打` · **`白桦`（男声）** · `Mia` · `Chloe` · `Milo` · `Dean` |
| 请求 | `POST /v1/chat/completions`，`messages:[{role:"assistant",content:"<文本>"}]` + `audio:{format:"wav",voice:"白桦"}`；可选的 user 风格指令放在 assistant 之前，**实测会真的改变输出**（同一句 2.24s → 3.52s） |
| 响应 | `choices[0].message.audio.data` = base64 WAV（**24kHz 单声道 16bit**） |

- 没有 `/v1/voices` 接口：音色表是**故意传一个不存在的音色**、从 400 报错的 `message` 里读出来的。
- **音色确实生效**（不听声音也能验）：同一句话用 `白桦` / `冰糖` 合成，返回的 WAV 哈希不同；
  再对 WAV 做自相关基频估计——整段中位 **白桦 ≈140 Hz**（男声区）vs **冰糖 ≈258 Hz**，参数被忽略时这个差会立刻消失。
- ⚠️ **ASR 交叉校验用不了**：`mimo-v2.5-asr` 返回 `402 {"type":"insufficient_balance"}`（余额不足），
  所以"合成→转写→对文本"这条自动查错路走不通，多音字只能靠源头规避 + 时长旁证（见 ④）。

**② `narration.txt` 从「一整行」拆成「每句一行」（10 行）——这是能不能对齐的前提**

适配器**一行 = 一章**。原文件是一整行 154 字，只会产出 1 个章：整片一起拉伸/压缩，**逐句对齐不可能**。
拆成 10 行后（与 `manifests/semantic-caption-lines.txt` 逐行同构，规范化后仍完全相等，字幕契约不破），
10 个章正好对应已批准时间轴里的 10 个「句」边界（350ms 间隙处）。模板 `assets/lecture-template/narration.txt`
同步改成 10 行（否则模板自己的流程也做不了逐句对齐），已复跑门禁确认无副作用。

**③ 对齐：用了哪些脚本、章节帧有没有动**

```text
node notebook-video.mjs match-timing ./demo-video --lock   # 锁定已批准章表（10 章 / 37550ms / 1126.5 帧）
python scripts/tts-openai-compatible.py .                  # 合成 10 段，原始总长 46510ms
python scripts/speed-post.py . 1.10                        # 标准语速后处理 → 42282ms
node notebook-video.mjs match-timing .                     # 逐章 atempo 回锁定时长 → 37550ms
```

- 逐章拉伸倍率 **0.909 – 1.500**（全部落在脚本允许的 0.4–2.5 内），**最终总长 37550ms 与锁定值逐毫秒相同**；
  `manifests/chapters.json` 与 `manifests/chapters-timing-lock.json` 的 10 个章起止**逐个比对全部相同** →
  **章节帧、场景边界、音效帧一个都没动**（1150 帧 / 8 镜时间轴原样）。
- 合成音频：**48kHz 立体声 192kbps，37.558s**，`loudnorm=I=-16:TP=-1.5:LRA=11` 后实测 **-17.6 LUFS / -4.7 dBTP**。

**④ 字幕：只换时间戳，分段沿用已批准的 16 条**

- 文档里的重跑命令（`build-semantic-captions`）是**一行切一条 cue**，会把已批准的 16 条短句并成 10 条长句
  （最长 23 字）；现片的分镜、字幕框与 `CaptionFitGate` 都是按 16 条短句调的，合并等于改画面。
- 处置：写了一个一次性脚本（`.tmp-probe/resplit-cues.py`，不进技能），**沿用已批准 16 条分段的文本**，
  把每条逐字对齐到新词流，只换 `start/end`。结果：**16 条不变**，各条 `end` 与已批准表逐条相同（±1ms），
  `start` 只因 `--lead-ms 60`（文档规定的重建值）提前 60ms。
- 校验：`validate-caption-sync`（154 个词边界 / 16 条 cue）· `validate-semantic-breaks`（16 条 / 9 个保护短语）**均 exit 0**。

**⑤ 结果：`validate-video` 这次真的过了**

```text
container valid: H.264/AAC 2560x1440 30fps, 38.379s
audio valid: -17.1 LUFS, -2.1 dBTP          ← 目标区间 [-18,-14] LUFS / ≤ -1.5 dBTP，均满足
No black frames detected.
（exit=0；上一版同一命令因 -21.5 LUFS 而 exit=1）
```

`validate-audio-levels`：P0=0 P1=0（7 个音效峰值 -2.8 ~ -3.0 dBFS）。

**⑥ 多音字与念法的诚实结论**

- 文本里**没有**文档"已生产验证的改写表"里那类高危多音字（重装 / 批量重命名 / 输一行命令 / 钉在屏幕上 / 一模一样），
  所以**这一轮没有做任何源头改写**（`narration.txt` 与 `semantic-caption-lines.txt` 一字未改）。
- 四个非中文串的读法用**时长旁证**推断（ASR 走不通）：`GitHub` 1043ms/6 字符（174ms/字符，接近整词读）、
  `PR` 400ms、`AI` 491ms、`hyt315` 1280ms（均接近逐字母拼读，符合中文 TTS 的常规做法），未见异常。
- **仍需人耳确认**：`GitHub` / `PR` / `AI` / `hyt315` 这四处（我无法听音，也没有可用的 ASR 交叉校验）。

**第四轮修正（用户反馈"配音太快"）：撤掉"时间轴不许动"，改成配音驱动时间轴**

上一轮把 46.51s 的自然配音**逐章 atempo 硬压进** 37.55s 的锁定时间轴（倍率 0.909–1.500），
结果是**语速偏快且逐句不齐**（170–254 字/分，1.49× 落差）。那条"时间轴不许动"的约束与技能设计冲突
（`tts-audio.md` / `scene-authoring.md` 都写明"每个出现帧都来自字幕 cue 表，不许猜"），已撤回。处置：

- **去掉 `speed-post 1.10`**，合成后不再为凑时长变速；只做**抹平句间快慢**的微补偿：
  目标 = 该配音自己的**中位语速**，逐章 `atempo` 夹在 **[0.85, 1.15]**（上一版是 0.909–1.500）。
  实测逐句 **195–216 字/分（1.11×）**，中位 208；上一版 170–254（1.49×）。
  *（说明：你举例的 [0.95,1.05] 只能把 1.49× 压到约 1.35×，达不到"明显收窄"，所以放宽到 ±15%；最大倍率仍远低于上一版的 1.50。）*
  实现方式是把目标章时长写进 `manifests/chapters-timing-lock.json` 再跑技能自带的 `match-timing.py`，
  没有自造变速脚本。
- **时间轴跟着配音走**：`build-semantic-captions`（常规流程，一行 = 一条 cue）→ `resolve-shots.py` 重算分镜帧。
  总长 **1150 → 1453 帧（+303 帧 / +10.1s）**；各镜帧位（旧 → 新）：
  S1 0–213→0–333、S2 213–286→333–439、S3 286–416→439–623、S4 416–532→623–790、
  S5 532–682→790–948、S6 682–803→948–1089、S7 803–919→1089–1195、S8 919–1150→1195–1453。
  连带更新：`src/shots.ts`（+SHOT_TOTAL=1453，`index.tsx` 的 `DURATION` 是派生的，无需手改）、
  `manifests/shots.resolved.json`、`manifests/shots.json` 的 `duration`、`manifests/asset-manifest.json`
  （`duration_frames` + 8 个场景边界）。**音效帧无需手改**：`index.tsx` 的 `SFX` 表由 `SHOTS[id].from + beats` 派生。
- **字幕条数 = 16**，用常规流程产生（`build-semantic-captions`）。为了"一行 = 一条 cue"既成立、又不至于单条过长，
  把 `manifests/semantic-caption-lines.txt` 拆成 **16 行（最长 12 个中文字宽）**——这与影片原本的字幕分段一致，
  也让 `shots.json` 里按 cue 区间声明的 8 个镜头（[0,3]/[4,4]/[5,6]/[7,8]/[9,10]/[11,12]/[13,13]/[14,15]）继续有效。
  模板侧同名文件同步改成 16 行（模板自己的 `caption-cues.json` 本来就是 16 条，改完两边自洽）。
- **抽查实渲（按收窄后的范围只渲 4 帧，其中 2 帧是无效样本）**：
  frame 333 与 790 落在 cue 的**第一帧**，字幕 reveal 的 `opacity` 按设计正好为 0（不是缺陷）→ 改抽 cue 中段：
  **frame 350**（S2 / 章节 02 "入场三步"）字幕显示"想入"（cue 5「想入场，其实只要三步。」正在逐字显示）✓；
  **frame 820**（S5 / 章节 04 "第三步·运营与三技能"）字幕显示"第三步，"（cue 10）✓ —— **字幕落在正确的镜头上**。
- **门禁（demo 侧，时间轴已变）**：`validate-shot-motion` P0=0 P1=0 · `validate-frame-props` P0=0 P1=0 ·
  `validate-visual-plan` valid · `validate-layering` valid · **`validate-composition` P0=0 P1=7 → PASS**。
  新增 P1（如实列出）：**S1 单镜 333 帧（11.1s）超过 300 帧参考上限**；**1 处静止间隔 >4s（S1 f=130-264）**；
  另有 2 处 3–4s 间隔从 2 处增至 4 处（S2/S3/S7/S8）。根因是自然语速比原锁定轴慢，每镜都变长了。
- `validate-caption-sync`（154 词边界 / 16 cue）· `validate-semantic-breaks`（16 cue / 9 保护短语）·
  `validate-audio-levels`（P0=0）全部通过；技能模板侧四道门禁 **P0=0**（模板自身的 1150 帧轴未变，P1 仍是原来那 5 条）。
- **本轮没有整片渲染**（按收窄后的范围：渲染只是抽查手段）。仓库里那份 `renders/upgrade/film-tts.mp4`
  是**上一轮错误时间轴**的产物，已过期；正确产物是数据与清单（`audio/` + `manifests/` + `src/shots.ts`）。

**第五轮：收尾四项（全部不整片渲染）**

1. **`TreeView` 密集树入场封顶**（`components/data.tsx`）：同层错峰从"序号 × 5 帧"改成
   **总窗口封顶**——`间隔 = min(5, 24 / (该层节点数 − 1))`，一层无论多少节点都在 24 帧内错开完。
   实测（纯算术）：3 叶 56 帧（与原行为相同）、5 叶 66 帧（相同）、**10 叶 91 → 70 帧**、
   20 叶 155 → 84、60 叶 355 → 84。**抽 1 帧确认**（`renders/upgrade/tree-cap-75.png`）：
   密集树在 f=75 全部 15 个节点就位（旧公式此时最后一格还没淡入）。
2. **`@remotion/media-utils` 的表述更正**（`references/dependency-policy.md` §4.3 新增对照表）：
   它是 **`@remotion/cli` 的传递依赖**（`remotion` 本身不依赖它）、**模板 `package.json` 未声明**、
   **包里没有现成的波形/频谱组件**（要画得自己画）。⚠️ **顺带纠正一处错记**：2026-09-20 的调研报告写
   "只导出 4 个函数"，实测 4.0.526 的 `dist/index.d.ts` 有 **12 个运行时导出**，其中就有
   `visualizeAudio` / `visualizeAudioWaveform` / `getWaveformPortion`——**但那只是这个包的函数名，
   不是本技能已具备的能力**。技能没有封装它、也没有用它，本轮**没有为它新造任何组件**。
3. **`CardFitGate` 负例夹具 —— 发现并修掉一处"门禁等于不存在"的静默失效**：
   - 新建夹具 `demo-video/src/index.tsx` 的 `CardFitFixture`（三种模式：`ok` / `tooSmall` / `textOverflow`；
     住在本文件是因为 `import './index'` 会二次执行 `registerRoot()`，实测报 "called more than once"）。
   - **第一次跑：负例照样出图**（"260px 卡片里塞 560px 图表"397px 的溢出被静默放过）。
     根因：门禁的测量排在 `requestAnimationFrame` 里，却**没有 `delayRender` 兜住截帧**——
     still 渲染先截图，门禁永远来不及量（字幕门一直是 `delayRender`+`continueRender` 的，本门禁漏了）。
     诊断（给夹具加 1.5s hold）：**压住就拦**（397px / 1297px 都被 cancelRender）→ 判据没问题，是时序。
   - **修**：`CardFitGate` 现在持有 handle 到首次测量完成（`timeoutInMilliseconds: 60000` 兜底）。
     修后**不再需要任何外部 hold**：`tooSmall` → exit 1、`Card overflow: @40 …溢出 397px`、无 PNG；
     `textOverflow` → exit 1、1297px；`ok` → exit 0 正常出图（控制组）。技能模板侧同步修了同一处。
4. **`assets/demo/` 样片如实标注**（`README.md` / `README.en.md`）：4 个文件由**旧版模板**渲染、
   **不对应当前模板输出**，此后所有改动**均未重渲**；并给出"如何核对当前版本"的命令。
   **没有重渲这批样片**（按要求）。

**第六轮：回查"哪些是我们自己造的轮子"（并替掉一个）**

用户的指路：能靠依赖解决的就别自己造。逐个过了一遍 `components/` 里手写的几何 / 排版 / 测量 / 缓动 /
颜色 / 图像处理，结论是**只替掉一个**，其余要么已经在用库、要么是我们自己的设计决策。

**替掉的：中文断行 → UAX #14 真算法（`linebreak`，MIT）**

- 原来 `fittext.tsx` 手写两张字符表（`NO_LINE_START` / `NO_LINE_END`）做避头尾。实测（Node 里两套算法对同一批真实文本比对断点）它只是粗糙近似，**而且错在中英混排上**：
  `在GitHub，全世界的开发者，` 它允许 **5 个非法断点**（在G\|itH、在Gi\|tHu、Git\|Hub…）；
  `主页搜hyt315，…` 5 个（hyt\|315…）；`中文English混排test` 9 个；`notebook-video` **13 个**（UAX #14 只允许 1 个：连字符后）。
  纯中文时两者**逐一相同**（`第一步，参与别人的项目，`、`给容器宽度和行数上限，反推该用多大字号`），所以换掉的正是"我们写得更差"的那部分。
- 换后实测可断点：`在GitHub…` 15 → **8**、`主页搜hyt315…` 14 → **7**、`notebook-video` 13 → **1**、
  纯中文 `三步走` 2 → 2（**不变**）。
- 确定性：算法 + 随包发布的 Unicode 表，纯函数、无 timer、无 `Math.random`，版本被 lock 锁死 ✓。
- **回归确认（1 帧）**：接触表 ⑩ 页（FitTextBox 主力页）重渲与换算法前**逐字节相同**（`f7b66451…`）——
  我们自己的中文内容一行都没变，换的是混排时的那批错断点。
- 代价与替代方案已写进 `dependency-policy.md`：它钉死 `base64-js@0.0.8`（2014 年版本）作为传递依赖，
  lock 里会多一个嵌套老包；不想背就用"3 行手写规则"兜（仍是近似）。

**没替的（逐个给了不替的理由）**

| 候选 | 结论 | 依据 |
|---|---|---|
| `@remotion/layout-utils` 的 `fillTextBox` | **不替** | 读源码确认：它是**调用方逐 token 喂**的累加器（`add({text,fontSize,…})` → 超过 `maxBoxWidth` 就换行），**不是"把这段文字塞进盒子"的函数**。它自带的中文断行就是那个已实测失效的 `fitTextOnNLines` 一脉；而我们的 fitter 是"参考字号量一次 + 线性缩放 + 二分字号"，比它逐 token 调 `measureText` 快得多。同一族的 `measureText` 我们**已经在用**（`fitsWithin` / `assertFits`） |
| `pangu`（中英混排加空格） | **不替** | 我们那条运行时规则（字幕逐字显示时在"相邻两字异文种"之间插发空间）在真实字幕上逐条核对**全部正确**（在␣GitHub、搜␣hyt315、个␣AI、I␣技、个␣PR；`hyt315` 内部与纯中文内部都不插）。pangu 是**整串文本变换**，用它就得改字幕/台词文本并重新对齐词流；且 v10 的 Node API 只有 `spaceFile`（文件级）。**没有可修的缺陷**，不引 |
| `culori`（OKLab 感知插值） | **列为待定，不擅自加** | 我们先看代码：`components/` 里**没有任何手写颜色数学**（只有一处把 flash 透明度拼成 8 位 hex alpha，两行算术），渐变是 **CSS 渲染的**（`conic-gradient` 等），我们只负责给停靠色。所以 culori 不是"替掉我们写得更差的轮子"，而是**新增一种能力**（把渐变中段调成感知均匀）；目前**没有观察到任何一条渐变发灰发浊**。按 §8"加依赖必须是替轮子或解锁能力"，这属于后者，且缺一个可复现的缺陷证据 → **交你拍板** |
| `@remotion/media-utils` 的波形函数 | **无可替** | 全仓 grep 过：我们**从来没有手画过波形/频谱**（没有假声波、没有竖条假装波形），所以没有"轮子"可换。它仍是未声明的传递依赖，已在 §4.3 如实记录 |
| 手写缓动 | **不需要** | `fxkit.tsx` 的 `ease` / `easeOutSoft` / `popS` / `easeInQuad` **本来就是** Remotion 的 `Easing.bezier` / `Easing.inOut` / `spring` 的薄封装，没有自己实现的曲线 |
| 手写图像处理 / 颜色转换 / 日期 / CSV / 二维码 / 数学渲染 | **不需要** | 逐项确认都已在用库或平台能力：`measureText`（layout-utils）、`d3-*`、`roughjs`、`katex`、`qrcode`、`react-icons`、`react-syntax-highlighter`（PrismLight）、Radix、`budoux` |

**Verified**

- **四道门禁全部复跑，P0 = 0**：`validate-frame-props`（P0=0 P1=0 PASS）· `validate-composition`（P0=0 P1=5 PASS，P1 与改动前逐条一致，无新增）· `validate-skill-consistency`（passed）· `negative-gate-check`（8 项全 PASS，含 A–H 阴性对照）。
- **接触表 14 页 → 17 页**（新增 ⑮ 图表变体 / ⑯ 层级与关系 / ⑰ 弹层与形状；⑫ 页的 `TiltCard` 格子换成 `ControlStack`），
  `SHOWCASE_PAGES = 17`、`SHOWCASE_VERSION = showcase-v8`。新增与改动的每一页都**实渲了一帧并看图确认**（不是只看"没报错"）。
- **确定性复验（成品件，不只是诊断件）**：接触表第 ⑯ 页（treemap / pack / sunburst / NetworkGraph）与第 ⑰ 页
  （四个 Radix 弹层）各渲同一帧两次，**PNG 哈希逐字节相同**——证明 floating-ui 的异步落位在本工程里不破坏可复现性。
- **依赖表与 lockfile 同步**：`assets/lecture-template/package.json` 新增 11 个包 + 1 个类型包，
  在该目录跑 `npm install --package-lock-only` 重生 `package-lock.json`，并逐条核对 lock 里确实有这些包、
  版本与许可与调研报告一致（MIT / ISC）。

**Known gaps（本轮未做，勿当作已解决）**

> 上一轮列的 6 条已在「第三轮收尾」里全部处理：转场 20 种全登记 ✅ · `PrismLight` ✅ · 四皮肤实渲 ✅ ·
> 目录树两处观感缺陷 ✅ · 探针口径 ✅ · 两份 lock 一致性 ✅ · 整片与接触表整支渲染 ✅。
> 下面只剩本轮新发现 / 仍未做的。

- **`Chart` 新变体的 `CardFitGate` 没有单独跑过告警清零**（报告第七节第 7 项）：只按"所有变体共用 `CHART_BOX` 内边距"
  的构造保证了高度契约不变，没有构造一个"故意把图表塞进过小卡片"的负例来验证门禁真的会拦。
- **`TreeView` 的入场错峰是按"同层序号 × 5 帧"推进的**：密集树（10 叶）最后一个节点要到第 ~91 帧才完全出现。
  接触表用 110 帧截帧看不出来，但**塞进 3 秒以内的镜头要留意**——要么减少同层节点，要么显式传更大的 `step` 语义（当前 `step` 是层间隔）。
- **接触表 mp4 没有音轨，`validate-video` 用不上**（它要求音视频流都有）：本项目用 `ffprobe`（510 帧 / 17.000s / 1920×1080）
  加 `ffmpeg blackdetect`（0 处黑帧）代偿；`validate-video` 只对整片跑得通。
- **整片验证用的是等长静音占位 narration**（`audio/narration.mp3` 按设计不随包发布，实测 mean/max volume = -91.0 dB = 数字静音）。
  因此 `validate-video` 的"综合响度 -21.5 LUFS 超出目标区间"是占位的必然结果，**不是视觉或编码缺陷**；
  容器/时长/黑帧三项全部通过。
- **模板用 caret、验证工程用 exact，两份 lock 的形式差异是刻意的**（模板要能被 `npm update`，验证工程要钉死复现）。
  但**解析出的直接依赖版本已逐条核对为完全一致**（44 个直接依赖 44 个相同；模板 lock 刚重生成过，
  修掉了它自己原先 remotion 家族 4.0.489/4.0.526 混用的问题）。校验口径见「第三轮收尾」⑤。
- **`demo-video` 的 `react` / `react-dom` 已从 19.2.7 升到 19.3.0**（跟着模板 lock 走）。这是本轮唯一一次"为了对齐版本而重跑全部渲染"的改动；
  重跑结果：17 页 still 里 15 页与升级前**逐字节相同**，说明升级没有引入像素变化。

## [3.0.3] - 2026-09-18

> 小版本发布：新增拟真 AI 对话交互框、打字机标点分级停顿与流式切片引擎、顶栏章节卡安全区防遮挡门禁，以及台词驱动的错峰涌现规范。

### Added

- **`AIChatBox` 拟真 AI 对话交互框（收录至 `fxkit.tsx` 第 19 件组件）**：提供端到端 AI 对话交互高阶组件。内建 macOS 三色灯标题栏、模型药丸徽章（`DeepSeek/Claude/GPT` 等）、在线脉冲指示灯、用户与 AI 头像、思考状态动画、打字机流式输出、完成态徽章、动态划除线（`data-gate-allow="strikethrough"` 门禁白名单合规）以及底部提示词输入条。
- **`getStreamingSlice` 流式文本计算核心工具函数（`fxkit.tsx`）**：将字符计算、标点长短停顿律（句号/问号深停顿、逗号/分号短顿挫）抽象为统一纯函数，供 `Typewriter`、`AIChatBox` 及所有自定义场景组件复用，保证节奏统一。
- **接触表收录 `AIChatBox`（`showcase.tsx`）**：接触表 Page 4 同步扩充 `AIChatBox` 独立演示格，组件展示数由 30 件提升至 31 件（`SHOWCASE_VERSION` 升级至 `showcase-v3`），确保可被直观阅览选用。

### Improved

- **`Typewriter` 标点长短停顿分级与多行排版**：重构字符预算消耗算法，中英文标点引入层级权重，句子结尾自然呼吸停顿，避免机械线性吐字；新增 `multiline` 多行排版支持（`pre-wrap`）与 `cursorSticky` 保持光标配置，避免打字完成后的生硬跳变。
- **`coords-lint.py` 顶栏章节卡保留区（Top Chrome Reserved Zone）防碰撞门禁**：增加对 `x < 500` 且 `0 < y < 170` 的坐标检测，当场景根级元素或主要卡片试图放置在顶栏章节卡（`x: 92..484, y: 74..164`）区域时给出 `VERIFY-TOP-CHROME` 明确告警，彻底杜绝左上角隐蔽遮挡。
- **规范强化：台词节拍驱动的阶梯涌现（Cue-Beat Staggered Reveal）**：在 `scene-authoring.md` 中补充 Pit #11 & #12，避免场景内多组要点、对比条或对话在 `f=0` 瞬间全量铺开，推荐与分镜表 `beats`（`at(i)`）绑定错峰展开。
- **介质路由表升级（`media-routing.md`）**：在内容介质路由表与修辞动作表中分别登记 `AIChatBox` 的选型时机与容量规范（推荐 2~3 轮对话，防窗口溢出）。

## [3.0.2] - 2026-09-11

> 补丁：给 3.0.1 收尾——把"迁出来但没人用"的修辞工具件真正用上、让它们进接触表，并修掉过程中（实渲 + **四组独立代理交叉复核**）抓到的缺陷。
> 这批改动里有一条是"改错方向"被复核拦下的，已回退重做，见下面 `hasAttribute` 那条。

### Added

- **`Callout` / `Checklist` 用进官方模板**（3.0.1 的目标到此才算闭环：组件能 import ≠ 被用上）。S1 的 `Callout` 圈住控制台里 `(没有远程仓库，只有本地)` 那一行，配标注"还躺在硬盘里"——圈住症结、旁边写字，正是这件组件擅长的修辞动作；S3 的 `FitCard` 里三步路径改用 `Checklist`（带序号圆牌），换掉原先手写的三行 `CheckBadge`（**加组件 = 换掉一个元素**，不是往里堆）。`manifests/shots.json` 的 `live` 同步声明 `Callout` / `Checklist`。
- **接触表补 3 页（⑦⑧⑨）**：`toolkit.tsx` 的 11 件在模板里**此前一页都没有**，等于"能 import 却从未被渲染过"。现在 `Callout / Connector / Checklist`、`CountUp / ProgressBar / RollDigit / BrowserChrome`、`JumpInText / WaveText / Mascot / CodeBlock` 全部进接触表，`SHOWCASE_PAGES` 6 → 9（26 个演示格 / 展开 30 件组件）。补页当场抓出下面 `WaveText` 那条真缺陷。
- `scripts/notebook-video.mjs` 补登记 `validate-frame-props` 与 `validate-audio-levels`：这两道构建期门禁此前只能直接 `python scripts/…` 调用，CLI 里点不到。

### Fixed

- **`CardFitGate` 的逃生口写法用错了，差点把一整类真实裁切放过**（交叉复核拦下的 P0）。修 `ZoomStage` 假阳性时，第一版写的是 `card.closest('[data-fit-skip]')`——`closest` 会向上遍历，**挂在取景框上的标记因此把她框内所有后代卡片一起跳过**。复核代理用 A/B 对照实渲证明：故意在取景框里塞一张竖向裁切的卡片，带 `closest` 时渲染通过（248px 的真实裁切漏检），换成 `hasAttribute`（只跳标记者自身）后立刻被抓。**最终写法 `card.hasAttribute('data-fit-skip')`：取景框自身的缩放溢出不再误报，框内卡片的真裁切照抓。**
- **`CardFitGate` 在缩放容器上假阳性，导致模板 S3/S7 渲不出来**。`ZoomStage` 的取景框是 `overflow:hidden` 且内部有 `scale()` 子层，`scrollWidth/scrollHeight` 必然大于自身（实测 `scrollWidth` 1093 vs `clientWidth` 996），那是"推近"本身的效果，不是文字被裁。修法：`ZoomStage` 取景框与 `EvidenceZoom` 框标 `data-fit-skip`。
- **S3 的 `Checklist` 漏传 `frame={f}`（自己写的回归，被门禁抓到）**：回落到全局帧后，`start={at(1,20)}` 这个**镜内局部节拍**在全局帧上早已过去，三行清单从该镜第 0 帧就以 `opacity=1` 齐刷出现，错峰入场 100% 丢失。补上 `frame={f}`；`validate-frame-props` 对模板的输出从 `P1=1` 回到 `P1=0`。
- **`WaveText` 吃掉空格**（接触表实渲发现）：逐字 span 里的半角空格被 HTML 折叠，"OPEN SOURCE" 渲成 "OPENSOURCE"。改为 `ch===' '?'\u00a0':ch`，与 `JumpInText` 的处理一致。
- **`validate-composition.py` 在 Python 3.10 / 3.11 上直接 `SyntaxError`**：3.0.1 写的一行 f-string 在表达式里复用了同种引号（PEP 701 只在 3.12+ 合法），而脚本与 SKILL.md 都声明"Python 3.10+"。已改为 `%` 格式化；并加了 3.10 语法自检（`ast.parse(..., feature_version=(3,10))` 全仓 19 个脚本 0 处不兼容）。
- **`validate-composition` 的 `reveal` 核对不再误伤"只有分镜表"的工程**：3.0.1 加的这条 P0 在**场景源码缺失**时无从比对实现，却照样报"声明没兑现"，于是负向抽查的阴性对照（原样必须全过）被它自己拦下——**这是 3.0.1 发布时带着的缺陷**。改为与 `live` 名字同一口径（有源码才查），对真实工程的核对能力不变（复核代理用"表写 reveal、代码删掉 reveal"反例确认仍报 P0；抽查 C 也仍以正确的"相邻同骨架"理由拦下）。
- **`has_reveal` 正则放宽**：原 `\breveal(?=[s/>])` 会漏判 `reveal >`（`>` 前带空格）/ 属性换行等合法写法（会变成假 P0），改为 `\breveal(?![A-Za-z0-9_$])`（仍排除 `revealAt` / `revealSpeed`）。
- **回退"给 `Callout`/`Connector` 加 `data-gate-allow`"**（复核指出是**过度豁免**）：`closest` 语义会让整棵子树退出重叠判定，连组件的**标注文字**一起豁免，违反仓库自己的白名单纪律（只允许"同位置换信息"与镜头交接）。而画圈的两道椭圆是 `fill="none"` 的 SVG，`looksSolid` 本来就不会把它当遮挡物——这个豁免**根本不必要**，已删除。同时给 `Callout` 标注补 `Caveat,Kai` 字体回退（`Caveat` 只有拉丁字形，中文此前由浏览器挑默认字体）。
- **文档与实现对齐**：`fxkit.md` 接触表页数（16 构件 / 6 页 → 9 页）、构件计数口径（27 → 实测 30）、`SKILL.md` 的 `live` 断言（原文写成"可检查"，实际门禁只查"名字出现在场景源码里"，已注明区别）、`SKILL.md` 门禁表补上第 9 道 `validate-audio-levels`、`README.md` 目录树里的"当前 v3.0.0" → v3.0.2。

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
