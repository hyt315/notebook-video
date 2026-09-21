# 依赖政策：什么能引，什么不能引

> 这份文件是依赖边界的**唯一定源**。与其它文档冲突时，以本文为准。
>
> 它存在的原因是一次真实的、代价很大的误读：技能原本写着一句「零第三方依赖」（本意只是说
> `scripts/` 下的 Python 脚本不许有依赖），却被执行 AI 读成了「整个技能不许用任何第三方库」。
> 结果是所有成熟组件都不敢碰，画面元素全部手写 SVG——**恰好做出了最难复现的结果**，
> 而这条规矩的本意正是"任何环境都能复现"。本文件用来钉死这个边界。

## 一、一句话边界

> **禁的是「按次付费、结果不可复现」的生成式模型；不是开源库。**

## 二、三类依赖，三种纪律

| 类别 | 例子 | 纪律 |
|---|---|---|
| ❌ **禁止**（默认路线） | 生图模型 API、生视频模型 API、任何按次计费的生成服务 | 默认路线**绝不用**。它们按调用付费，且同一提示词两次返回不同画面，风格锁不住。仅当用户**主动要求**时，才走 [visual-director.md](visual-director.md) 那条可选的生图附加路线 |
| ✅ **允许，且鼓励** | 开源、免费、可被 lock 文件锁死版本的 React 库 | **直接 `import` 用，不需要额外授权、不需要"先证明现有件做不到"**。装已在模板 `package.json` 里，`npm install` 一次到位 |
| ⚠️ **需授权** | 清单之外的新库 | 先问用户，同意后才加进模板 |

## 三、三条判据（拿不准时按顺序自问）

1. **要钱吗？** 按次计费 / 按量计费的生成式 API → 禁止。免费开源 → 通过。
2. **能复现吗？** 同一输入两次跑出不同结果（模型采样、随机种子没固定）→ 禁止。给定种子/帧号必然得到同一结果 → 通过。
3. **可能被 lock 锁死版本吗？** 能写进 `package-lock.json` → 通过。只能调远程接口、版本随时变 → 禁止。

三条全过才叫"允许"。**注意：第 2 条和第 3 条与"是否第三方"无关**——自研代码同样会因为
`Math.random()` 或 `setTimeout` 而不可复现。判断的对象是**行为**，不是**来源**。

## 四、模板已内置的依赖（无需授权，直接用）

`assets/lecture-template/package.json` 已声明以下依赖，`new-project` 之后一次 `npm install` 全部就位。

### 4.1 UI 与结构（解决"技能里根本没有这类形态"）

| 包 | 解决什么 |
|---|---|
| `@radix-ui/react-accordion` | 手风琴：展开/收起状态机、焦点管理、键盘导航、ARIA |
| `@radix-ui/react-tabs` | 标签页：多方案切换、面板管理 |
| `@radix-ui/react-switch` / `-checkbox` / `-radio-group` / `-slider` / `-toggle-group` / `-progress` | **「控件状态随旁白变化」**（`ControlStack`）：开关 / 复选 / 单选 / 滑块 / 分段 / 进度条。源码级核实：这 6 个 primitive 的产物里 **Portal 0 处、timer 0 处、`Math.random` 0 处**，是纯受控 DOM 件——无交互环境里长得和有人点时一模一样 |
| `@radix-ui/react-dialog` / `-popover` / `-dropdown-menu` / `-tooltip` | **拟真弹层**（`OverlayFrame`）：确认框 / 下拉选择 / 说明气泡 / 提示。**必须先做 Portal 落点处理**（见 §7.7） |
| `react-syntax-highlighter` | 代码语法高亮（180+ 语言、行号、行聚焦） |
| `react-icons` | 图标字形库。允许 `fa`（品牌实心）+ `fi` / `lu`（线条）+ `si`（仅品牌 logo），见第 7 节纪律 |
| `d3-scale` / `d3-shape` | 图表计算：数据→刻度、数据→SVG 路径。**纯数学，零渲染零动画零样式** |

### 4.2 数据与素材计算（纯计算，全部确定性）

| 包 | 解锁什么 | 备注 |
|---|---|---|
| `d3-hierarchy` | **目录树 / 组织图 / 树状图**（`TreeView` 的 `treemap` / `pack` / `sunburst` 三个变体） | 与 `d3-scale` 同族；`hierarchy()` + `tree()` 给出每个节点的坐标。⚠️ 三个布局都是**有状态地写回节点**的，共用同一个 `hierarchy()` 根会互相覆盖——每个布局各拿一个根 |
| `d3-force` | **关系网**（`NetworkGraph`）：谁连着谁，没有层级也没有方向 | 源码级核实 `Math.random` **0 处**（用固定种子 LCG）。**必须**：初值显式给定 + 迭代次数写死 + 立刻 `.stop()` 掉内部 d3-timer；算完还要按包围盒等比归一化，否则会溢出画框（实测） |
| `d3-geo` | 地图 / 地球 / 经纬网 | 需要国界数据时另配 TopoJSON；无数据也能画经纬网与投影框 |
| `d3-sankey` | **流量图**（转化、分流、去向） | 带宽按数值分配 |
| `d3-dsv` | 解析 CSV / TSV | **真实数据进图表的入口**——不再手写数据数组 |
| `roughjs` | **手绘风图形**（线条带手抖） | 手账风的天然契合件。**seed 固定 → 每次渲染同一笔迹**；用 `rough.svg()` 而非内部路径。⚠️ **两个实测例外**（2026-09-21，接触表 ⑭ 页同帧多渲抓到）：① `fillStyle:'dots'` 的填充器在 `dotsOnLines` 里**无条件调 `Math.random()` 两次/每点**，与 seed 无关 → **已从 `SketchStyle` 移除**（同一帧渲三次三个哈希，差异全在 dots 那格）；② `seed: 0` 是假值，roughjs 的 LCG 写成 `this.seed ? … : Math.random()`，传 0 会让**所有**填充退回真随机 |
| `qrcode` | 二维码（收尾"扫码看仓库"） | 纯计算、不联网；`QRCode.toString(..., {type:'svg'})` 输出 SVG 字符串 |
| `katex` | **数学公式**静态渲染 | 需 `import 'katex/dist/katex.min.css'`；无动画，确定性 |
| `budoux` | **中文按词组断行** | Google 出品；`loadDefaultSimplifiedChineseParser().parse(text)` 返回词组数组。用于**标题**断行（正文中文可任意字断行） |
| `@cto.af/linebreak` | **UAX #14 断行算法**（避头尾 + "拉丁/数字串内部不断"的正解） | `new Rules({string:true}).breaks(text)` → 每个断点带 `position`。MIT、60 KB、**UAX #14 / Unicode 17**、2026-03 发版、依赖树干净（`@cto.af/unicode-trie-runtime` → `fflate`，都是现代在维护的包）、纯函数无 timer/random。此前 `fittext.tsx` 手写两张字符表做避头尾，实测只是粗糙近似且**错在中英混排**：10 条真实文本里它允许 **36 个非法断点**（`在G\|itHub`、`hyt\|315`、`第三个A\|I技能`、`S\|1：`…），换 UAX #14 后 **36 → 0**（纯中文用例两者完全一致）。⚠️ **选包口径**（用户 2026-09-21 定的原则：依赖要通用、能用新的就不用旧的）：先用的是 foliojs 的 `linebreak@1.1.0`，但它**钉死 `base64-js@0.0.8`（2014 年）**、且 2022 年后没再发版 → 换成 `@cto.af/linebreak`（自述是前者那包的 refresh），实测两包在同一批文本上**断点逐一相同**，换包零行为变化（同名页面重渲逐字节一致）。另外：**不要回头试 `Intl.Segmenter({granularity:"line"})`**——`line` 粒度不在 ECMA-402 规范内，Node 24 直接抛 `RangeError` |

> **实测**：这 8 个已在独立验证工程 `demo-video` 里逐个渲染验证（目录树 / 地球 / 流量图 / CSV / 手绘 / 二维码 / 公式 / 中文词组断行），全部能在四套皮肤下正确读 `THEME`。
> **体积**：8 个包 + 传递依赖合计约 **12 MB**（其中 `katex` 4.6 MB 与 `budoux` 3.2 MB 是大头，且几乎全是字体与模型数据）。相比之下 `react-icons` 一个 85 MB、Chrome 无头浏览器 270 MB——**这点体积可以忽略**。

### 4.3 Remotion 官方扩展（天生帧驱动安全）

| 包 | 解锁什么效果 |
|---|---|
| `@remotion/transitions` | 20 种演示型转场：fade / slide / wipe / flip / clockWipe / iris / dissolve / ripple / zoom-blur / film-burn / book-flip / swap / crosswarp … 用 `TransitionSeries` 串联 |
| `@remotion/paths` | `evolvePath`（描线生长）、`getPointAtLength`（沿线运动）、`interpolatePath`（形状连续变形）、`warpPath`、`cutPath`、`getBoundingBox` |
| `@remotion/shapes` | 参数化几何图形：圆 / 椭圆 / 矩形 / 三角 / 多边形 / 星 / Pie / 心形 / 箭头 / 对话气泡 / 星芒，`make*()` 直接给出 path 字符串 |
| `@remotion/motion-blur` | `CameraMotionBlur`（相机快门式模糊）、`Trail`（拖尾残影）。快甩、冲刺、切镜用 |
| `@remotion/layout-utils` | `measureText`（实测文字宽高，**准确且严格线性**：已验证 46px 时 44 字 = 2024px）、`fillTextBox`。**治卡片裁切的正解**。⚠️ **不要用 `fitTextOnNLines` 处理中文**，见第 5.1 节 |
| `@remotion/noise` | `noise2D/3D`：给同一 seed 得到同一结果，可做有机抖动、自然呼吸而不破坏可复现性 |

> 选型理由：这六个与渲染引擎同厂，**按帧驱动设计**，不存在"库自带时间动画"的冲突，是引入成本最低、
> 风险最小的一类扩展。加依赖时优先考虑这一族。

> **两个名字很像的包，别搞混（也别说错）**：`@remotion/media` 与 `@remotion/media-utils`。
>
> | | `@remotion/media` | `@remotion/media-utils` |
> |---|---|---|
> | 在模板 `package.json` 里声明了吗 | **有**（`<Audio>` / `<Video>` 组件，影片的音频树用它） | **没有** |
> | 它从哪来 | 直接依赖 | **`@remotion/cli` 的传递依赖**（`remotion` 本身不依赖它） |
> | 给什么 | 播放媒体元素 | 媒体分析工具函数 |
>
> `@remotion/media-utils` 实测（4.0.526，读 `dist/index.d.ts`）导出的**运行时函数有 12 个**：
> `getAudioData` · `getAudioDuration` · `getAudioDurationInSeconds` · `getWaveformPortion` ·
> `visualizeAudio` · `visualizeAudioWaveform` · `createSmoothSvgPath` · `useAudioData` ·
> `useWindowedAudioData` · `getImageDimensions` · `getVideoMetadata` · `audioBufferToDataUrl`
> ——**给的是波形/时长的数据，不是一个现成的波形或频谱组件**（包里没有 `<AudioWaveform>` 这种东西，
> 要画还是得自己画。<del>"只导出 4 个函数"是 2026-09-20 那份调研报告的错记</del>）。
> **技能没有封装它、也没有用它**：它**不在依赖清单**里（要用得先走 §二 的"需授权"），
> 而且说不出来它能替换掉哪个平淡表达（代码库里没有"用静态竖条假装声波"的写法要它来治）。
> 所以：**不要因为看到 `visualizeAudioWaveform` 这个名字，就以为技能"有波形/频谱能力"**——
> 那是这个包的函数名，不是本技能已具备的能力；也不要为它新造组件。

### 4.4 已封装的组件（全部登记在路由表里）

| 依赖 | 封装成的组件 | 渲染验证 |
|---|---|---|
| `d3-hierarchy` | `TreeView`（目录树 / 组织图 / **矩形树图 / 圆形打包 / 旭日图**） | ✅ 接触表 ⑬⑯ |
| `d3-geo` | `GeoView`（地球 / 经纬网） | ✅ 接触表 ⑬ |
| `d3-sankey` | `SankeyChart`（流量图） | ✅ 接触表 ⑬ |
| `d3-force` | `NetworkGraph`（关系网，固定迭代 + 显式初值） | ✅ 接触表 ⑯ |
| `qrcode` | `QrCode`（二维码） | ✅ 接触表 ⑬ |
| `roughjs` | `SketchFx`（手绘风，**含五种确定性 `fillStyle`**：hachure / cross-hatch / dashed / zigzag / zigzag-line；`'dots'` 因内部调 `Math.random()` 已移除）+ `sketchCircleArea` / `sketchUnderline` / `sketchBox` | ✅ 接触表 ⑭ |
| `katex` | `MathBlock`（公式块） | ✅ 接触表 ⑭ |
| `d3-dsv` | 并入 `Chart` 的数据入口（`csv` prop）+ `csvToChartData()` / `csvToChartSeries()` | ✅ 接触表 ⑭ |
| `budoux` | 并入 `fitChineseTextOnNLines()`（断行优先落词组边界） | ✅ 接触表 ⑭ |
| `d3-shape` / `d3-scale` | `Chart` 的 7 个 `variant`（line / area / stack / stackExpand / stream / radar / pie），柱宽由 `scaleBand` 给出 | ✅ 接触表 ⑮ |
| Radix 6 控件 | `ControlStack`（帧 → 状态的显式表） | ✅ 接触表 ⑫ |
| Radix 4 弹层 | `OverlayFrame`（dialog / popover / tooltip / menu） | ✅ 接触表 ⑰ |
| `@remotion/shapes` / `@remotion/paths` | `SHAPES`（含 callout / arrow / heart）+ `PathDraw showArrow`（`getTangentAtLength` 沿线朝向） | ✅ 接触表 ⑰ |

**全部封装完成、全部有渲染记录、全部登记进路由表**——「零引用」判据无一触发。

> **关于 budoux 的诚实结论**：它是**辅助不是保证**。实测它对"反推"「并返回」这类词也会切错
> （切成 `反|推该`、`并返|回断`），模型本身不够准。所以：**标题可以依赖它的断点，正文别指望**。
> 断行仍然是"能落在词组边界就落，落不了按字断并遵守避头尾"。

> **教训留档**（这条清单本来是"待办"）：技能曾累积 23 件"从未出现在任何画面里"的组件，
> 起因正是"装了/建了却没人用"。**引入依赖 ≠ 获得能力**——封装成组件 + 登记进路由表 + 真的渲染过，三件都做到才算。

### 4.5 包体优化（已做：`HighlightCode` 换 PrismLight）

`src/components/ui.tsx` 的 `HighlightCode` 原本用 `react-syntax-highlighter` 的**全语言构建**（`import {Prism}`），
把 **180+ 种语言的词法定义都打进了包**，而实际只用 tsx / ts / python / bash / json / diff 六种。

**2026-09-21 已改为 `PrismLight` + 按需注册**（`PRISM_LANGUAGES` 表，别名 ts/js/sh/py 一并注册）：
功能不变、包体纯赚，实渲确认语法高亮与逐行聚焦仍然正常（接触表 ⑨ 页 frame 255）。
⚠️ **换了 PrismLight 就必须注册语言**：没注册的语言不会报错，只是整段退化成纯文本——
加新语言时记得往 `PRISM_LANGUAGES` 里补一行。

## 五、零依赖也能做的"炫效果"（优先做这些）

社区组件库里最抓眼的效果，**八成不需要任何依赖**——它们的底层只是 CSS/SVG 数学。做成组件时优先走这条路：

| 效果 | 实现 |
|---|---|
| 流光边框 / 渐变描边 | `conic-gradient` 旋转角绑帧号 |
| 光晕 / 聚光焦点 | 多层 `radial-gradient` + `blur` + `mix-blend-mode` |
| 3D 倾斜卡片 | `perspective` + `rotateX/rotateY`，角度绑帧号 |
| 遮罩擦除转场 | `clip-path: inset()` 按帧推进 |
| 文字闪过一道光 | `background-clip:text` + 移动的渐变遮罩 |
| 描线生长 / 路径流动 | `strokeDasharray` / `strokeDashoffset`（或 `evolvePath`） |
| 网格 / 点阵 / 噪点背景 | `repeating-linear-gradient` |
| 数字滚动 / 逐字生成 | 逐帧取整 / 取字符 |

**纪律：这些一律写成 `f(帧号)` 的纯函数**，禁止 `animation: ... infinite`、`transition`、`setTimeout`。

### 5.1 已知地雷：库不一定适配中文

引库不是无脑照搬。**上线前必须用中文实测过**，因为有些库是按拉丁文假设写的。已踩过的：

| 库 / API | 问题 | 处置 |
|---|---|---|
| `@remotion/layout-utils` 的 `fitTextOnNLines` | 实现是 `text.split(' ')`——按**空格**分词。中文没有空格，整段被当成一个不可断的「词」，于是只能塞进一行，字号被压到 `maxBoxWidth ÷ 字数`（实测：44 字 / 738px 容器 → **16.77px / 1 行**，而正确答案是 46px / 3 行）。**它不报错，只静默给出一个极小的字号** | 改用 `src/components/fittext.tsx` 的 **`fitChineseTextOnNLines`**（自研：`measureText` + 二分 + CJK 避头尾断行）。断行必须保证**每行不超过容器宽**，否则浏览器会二次折行（实测 3 行被折成 6 行） |

**通用教训**：引入任何"处理文字"的库，先用一段中文跑一遍，把结果量出来看——不要看文档示例（示例都是英文）。

## 六、为什么不直接粘贴网上的组件库

21st.dev、Aceternity UI、Magic UI、shadcn/ui 这类**分享型组件库**（别人写好源码、复制即用）确实是最快的
"炫效果"来源，但**不能原样粘进本技能**，三堵墙：

| 墙 | 具体表现 |
|---|---|
| **Tailwind 墙** | 它们的写法是 `className="relative flex h-[500px] overflow-hidden rounded-lg border"`。本技能不用 Tailwind，样式一律是 inline style + `THEME`。粘进来类名全部不生效，画面直接塌 |
| **时间驱动墙** | 它们的动画是 `animation: 3s infinite` 或自动播放的 motion。视频按帧渲染，**同一帧可能被渲染多次**，时间驱动的动画每次结果都不同——这正是九道门禁要防的事 |
| **审美墙** | 它们绝大多数是暗色科技 SaaS 落地页风格（黑底极光、流星、光束）。本技能的皮肤是暖米纸手账 / 动漫赛璐璐，硬搬会打架 |

**正确用法：取"效果配方"，不取"实现"。** 把它拆成第五节的 CSS/SVG 数学，重新用 `THEME` 上色、用帧号驱动，
然后做成**本技能自己的组件**。效果是别人的，皮肤和可复现性是我们的。

## 七、引入库之后必须遵守的组件纪律

新组件不是"直接暴露库"，而是**包一层再给场景用**：

1. **封装一层**：场景 `import` 的是 `src/components/` 里的封装件，不直接 `import` 原始库。
   理由：库是无样式的，直接引用会让每个场景写出不同的边框/圆角/阴影，违反"不得发明 per-scene 样式"。
2. **只读皮肤**：颜色 / 边框 / 圆角 / 阴影只能从 `THEME` 取，不得硬编码。
3. **帧驱动**：动画是 `f(帧号)` 的纯函数。禁止 CSS transition、`setTimeout`、`Math.random()`。
4. **高度算出来**：文字容器高度用 `fitH()` 或 `fitTextOnNLines()` 得出，禁止手写"看着差不多"。
5. **图标限定**：`react-icons` 允许三族，各管一段，**不许混着用同一个意思**：
   - `fa`（实心）＝ 品牌 logo 与技术栈（React / Python / GitHub …，唯一有品牌标识的一族）；
   - `fi`（Feather 287 字形）与 `lu`（Lucide 1541 字形）＝ 线条题材标识。
     两者**同源同款**：`react-icons/fi` 的 `FiZoomOut` 与 `lu` 的 `LuZoomOut`，attr 与子节点
     字节级相同（Lucide 是 Feather 的后继）。所以放开 `lu` **不引入风格漂移**（已并排实渲确认），
     而它带来 `fi` 里没有的 brain / rocket / sparkles / circle-check / bot / milestone 等增量字形。
     **不要为此装 35 MB 的 `lucide-react`**——那是同一批字形换一个包名。
   - `si`（Simple Icons）＝ 仅在没有对应 `fa` 品牌件时兜底。
   **锁定的 `LineIcon`（26 字形 / 32 视窗）仍是主图标语言**；新图标只用于题材性标识。
   混排时**笔画重量要压一档**：`LineIcon` 是 32 视窗 2.2 笔画，`fi`/`lu` 是 24 视窗 2 笔画，
   同一 size 下后者更粗。`TopicIcon` 已统一给 `fi`/`lu` 传 `strokeWidth = 2.2×24/32 = 1.65`。
   图标**只用 THEME 给的 color**，不许用自带 fill 或多色。
6. **进路由表**：新组件必须同时登记进 [media-routing.md](media-routing.md) 的「内容→介质」与
   「修辞动作→组件」两张表，否则会重演"组件在仓库里吃灰"的老问题。
7. **弹层必须有 Portal 落点**：Radix 的 Portal 默认挂 `document.body`，**那是 Remotion 画布之外**。
   用 Dialog / Popover / DropdownMenu / Tooltip 时必须把 `container` 指到画面内的宿主节点
   （`OverlayFrame` 已经封好这一层）。另有一条实测结论：**Popover / Tooltip / DropdownMenu
   的落位是异步的**（floating-ui 的 `computePosition` 在微任务里才 resolve，实测要 8 轮渲染才稳），
   所以 `OverlayFrame` 不用它的自动避让，而是把锚点钉在我们给的坐标上。
   **Toast 不要引**：它带 `duration` 计时器，与帧驱动正面冲突。

## 八、组件总数：一条纪律，不是一个数字

**纪律：加一件 = 换掉一件。** 新效果优先做成既有组件的**参数或变体**（`Paper variant="glow"`、
`FitCard tilt={...}`），**不要为新效果新开组件**——否则"引入社区效果"会把库顶到 30 件以上，重演吃灰。

**不要设一个拍脑袋的数字上限。** v3.1 实测过一遍：库的地板由两部分撑住，砍不动——

| 类别 | 件数 | 为什么砍不动 |
|---|---|---|
| 引擎 / 结构件（`validate-composition.py` 的 `STRUCTURAL` 集合：3 骨架 + `ShotCamera` `StageFrame` `PhaseRail` `CoverPanel` + `LineIcon` `CheckBadge` `PillTag` `StampBanner` `FitCard` `CardHead` `Shot`） | 14 | `validate-composition.py` 的 `STRUCTURAL` 集合就是这份名单；骨架门禁要求 ≥3 种且相邻不得重复 |
| 表意件（修辞动作各一件） | 41 | 逐对核对后，真正"同一修辞动作、两套实现"的只有 4–5 对，且每对都各有一点对方没有的能力 |

- **故本节的合规判据是「零引用」而不是「总数」**：任何组件只要**从未出现在任何画面里**（参考片或接触表），
  就是待删除项。v3.1 按这条清掉了 23 件。
- 想让库"更窄"而不是"更小"：走 [media-routing.md](media-routing.md) 的**单一首选**——每行只给一个建议，
  其余标注「何时才用」。一行并列三个平级选项 = 没给建议。

> **历史教训（两条，都很硬）**：
> ① 本技能曾累积到 49 件组件，其中 **23 件（47%）从未在任何画面里出现过**，而其中 **21 件早已登记在路由表上**——
>    说明"补决策入口"不是解药，**规矩必须同时给许可**（这就是本文件存在的原因）。
> ② 反过来，"总数压到 20 件"同样不可达：v3.1 逐件点算的地板是 **55 件**（`src/components/` 29 + 六个旧模块 26，其中 `STRUCTURAL` 14 件豁免多样性检查），再往下就是删引擎件或在用的表意件。
>    **别对着一个数字做有损合并。**
