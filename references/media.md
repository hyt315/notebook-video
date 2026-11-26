# 介质路由、真实素材与背景库

本篇定义内容到视觉介质的路由规则、外部授权素材（Wikimedia Commons / Openverse）与自备截图录屏的入库门禁，以及皮肤背景库契约。产品硬约束：**不调用生图模型，只收公有领域 / CC0 / CC BY 素材**。

<a id="media-routing"></a>
## 1. 内容 → 视觉介质路由

| 你要讲什么 | 优先介质 | 对应版式 / 组件 | 避免 |
|---|---|---|---|
| 真实历史物件、标本、原书图版、照片 | 真图版（手账页） | `layout: "page"`（`plate` / `loupe`） | 用纯文字卡片或简笔画替代实物 |
| 流程步骤、状态流转 | 结构流程图 | `flow` | 大段文字平铺 |
| 数值对比、性能测试 | 条形图 / 大数字 | `bars` / `number` | 在段落里堆叠一串数字 |
| 误区纠偏、方案优劣 | 左右对照 | `compare` | 只用红绿色区分而不加文字标记 |
| 代码改动、接口报错 | 代码块 / 真实截图 | `code` / `media` | 把超长代码硬塞进小字号 |
| 唯一核心关系 / 锤子句 | 直书页 / 印章横幅 | `type` / `StampBanner` / `HandLettering` | 套多层圆角框 |

<a id="component-index"></a>
## 2. 组件选型索引

**全技能唯一一份解释组件清单**（53 件，`KineticNumber` 属引擎运动件不计入）。参数以源码为准；帧参数口径以 [components.md](components.md) 开头的「帧参数铁律」为准（`tsc` 会拦）。手作材质件见 [components.md#craft-kit](components.md#craft-kit)；定制件放入 `src/custom/` 并在 `src/custom/index.ts` 注册。

### 2.1 组件索引

| 组件 | 用途 | 何时用 | 何时别用 / 注意 |
|---|---|---|---|
| `Accordion`（components） | 手风琴，展开项随帧累积 | 并列要点逐项展开 / 收起，一屏放不下 | 只是逐行出现 → `StaggerList`；控件被改 → `ControlStack` |
| `Tabs`（components） | 标签页，激活项由帧号决定 | 2–4 个对等方案切换，且切换本身是讲解内容 | "被改动"而非"切换" → `ControlStack` |
| `ControlStack`（components） | 六种受控控件（开关 / 复选 / 单选 / 分段 / 滑块 / 进度，纯 div），`steps:[{at,value}]` 帧→状态，纯函数可复算 | 讲某个设置被改了：旁白说到哪、控件变到哪 | 一行一个控件，别把 6 种塞进一镜；控件不是主角时别用（抢戏） |
| `OverlayFrame`（components） | 拟真弹层 dialog / menu / popover / tooltip（纯 div，Portal 指到画面根） | 讲"弹出来一个框" | 一次别冒三个；压在装饰区同样要坐 `CoverPanel` |
| `NetworkGraph`（components） | d3-force 关系网（固定迭代 + 显式初值） | 谁连着谁：无层级、无方向 | 有层级用 `TreeView`；反过来别用树画网（凭空造出上下级） |
| `HighlightCode`（components） | 语法高亮 + 行号 + 逐行聚焦，带窗口壳 | 页面形态的代码；"这是官方 / 真实代码" | 终端 → `ConsoleWindow`；逐字敲 → `Typewriter`；纯代码路线不做实拍框 |
| `MathBlock`（components） | katex 公式块（静态、确定性） | 有公式 / 推导 | 无动画，别当装饰塞公式 |
| `TopicIcon`（components） | 单个题材图标（simple-icons 品牌 + lucide-react 线条，笔画对齐 `LineIcon`） | 技术栈 / 品牌的单点 | 成排 → `IconWall`；与内容无关时别用 |
| `IconWall`（components） | 图标墙（错峰入场） | 技术栈 / 依赖清单具象成一堵墙 | 图标不是内容时别用 |
| `Chart`（components） | d3 算刻度与路径；`variant`：line（默认）/ area / stack / stackExpand（百分比堆叠）/ stream / radar / pie（扇区百分比 + 图例）；可喂 CSV（d3-dsv） | 数据 / 趋势 / 分布 / 多值对比；真实数据进图 | 一个百分比 → `ProgressRing`；前后两值 → `MetricGrid`；柱状用默认 line + `series` 驱动；未知 `variant` 直接抛错 |
| `StatRow`（components） | 一行指标卡，数字随帧滚动（字符串值直显） | 报一个大数字；等权指标并排；对比两方不等权时 | 数值已在 `MetricGrid` 里滚动时别重复 |
| `KineticNumber`（cinema，引擎运动件，**不计入 53 件**） | 关键数字动态排版：计数 + 缩放入场 + 下划线扫入，字号 170–380 | 一镜的主角就是一个数（耗时、倍数、降幅），讲到它的那一拍 | 一镜并排 ≥3 个数（用 `StatRow` / `MetricGrid`）；全片超过 35% 的镜都用它 |
| `TreeView`（components） | 目录树 / 组织图 + treemap / pack / sunburst（d3-hierarchy，面积 = 数值） | 有层级；或占比 + 层级 | 无层级的网 → `NetworkGraph` |
| `GeoView`（components） | 真陆地轮廓（d3-geo + world-atlas `land-110m`，55 KB 进 bundle），可叠经纬度标记点；`projection="flat"`（naturalEarth1）看全局，默认正交投影可 `spin` 自转 | 地理 / 全球视野；节点 / 站点分布 | **不含国界与地名**：要国界得换 `countries-110m.json` 并另立一件，别扩 `GeoView` 语义；同一组对比之外别混用两种投影 |
| `SankeyChart`（components） | 流量图（d3-sankey） | 流量在环节之间怎么分流 | 逐级递减的漏斗 → `Funnel` |
| `QrCode`（components） | 二维码（纯计算、不联网） | 收尾引导"扫码看仓库" | 中途别放（观众不会暂停扫码） |
| `SketchFx`（components） | 手绘风图形（roughjs，seed 固定 → 每次同一笔迹）；`fillStyle` 6 种确定性值：hachure（手账风招牌）/ solid / zigzag / cross-hatch / dashed / zigzag-line | 手绘强调：圈画 / 下划线 / 方框 | 要精确几何 → `ShapeDraw`；`'dots'` 已移除（内部调 `Math.random()`，同帧两次不一致） |
| `FocusFx`（components） | 一镜一次的注意力动作（dim / spot / loupe / marker） | 把注意力压到一块矩形区域 | 一镜一次；画面已有高亮或缩放时别叠 |
| `GlowFrame`（components） | 流光边框（conic-gradient 绑帧号） | 强调一瞬（警告感） | 与 `ShimmerText` 二选一；要"真的变了状态"→ `ControlStack` |
| `ShimmerText`（components） | 文字闪过一道光 | 只强调一句话；念口号 | 与 `GlowFrame` 二选一；讲解中段用显浮夸 |
| `ClipReveal`（components） | 遮罩擦除（clip-path 按帧推进） | 逐条揭示（不只是淡入） | 镜头级交接 → `RevealMask` |
| `NoiseJitter`（components） | 有机抖动（noise2D，同种子同结果） | 让静止物活一点（手绘 / 贴纸感） | 别给文字用（伤可读性） |
| `VerdictBar`（components） | 全宽结论条（填满底部） | 收束场景且底部要填满 | 一镜一条；别与 `StampBanner` 同时砸（互压底线） |
| `PathDraw`（components） | 描线生长 + 沿线运动的点 / 沿线转向的箭头（`showArrow`，`getTangentAtLength`，不用自己差分算切线） | 两者关系 / 因果；箭头沿路线跑；流程备选 | 路径短于 200px 时箭头盖住整条线；已有导轨 / 时间轴别叠；关系是网 → `NetworkGraph` |
| `MorphShape`（components） | 形状连续变形（flubber；`engine="remotion"` 用 `interpolatePath`） | 同一个东西形态变了 | 没有变形语义别用 |
| `ShapeDraw` / `SHAPES`（components） | 参数化几何（@remotion/shapes）：星 / 六边形 / 三角 / 圆 / 星芒 / callout 标注框 / arrow / heart / 椭圆 / 矩形 | 要标注框 / 箭头 / 星标，不想手写 path | 图标 → `TopicIcon`；形状要有语义，别撒装饰；份额别用它 |
| `SceneTransitions`（components） | **仅样张**：在接触表里预览 `@remotion/transitions` 的 20 种官方转场（几何 9 + 着色器 11，名 = `PRESENTATIONS` 的键）。成片换镜只走镜头的 `transition` 字段（[camera.md#fx-effects](camera.md#fx-effects)），与这套不相连 | 只在接触表里看效果 | 别在 scene 里套 `TransitionSeries`：会和成片的翻页转场叠在一起 |
| `FitTextBox`（components） | 中文反推字号 + 断行（自带字体就绪门） | 固定宽 + 行数上限定字号（治卡片文字被裁） | 管卡片多高用 `FitCard` / `fitH()`（分工见 [components.md#fxkit](components.md#fxkit)） |
| `PillTag`（kit） | 胶囊贴标 | 页眉 kicker、标签行 | 别当正文 |
| `LineIcon`（kit） | 26 字形线条图标（lucide-react） | 卡片小标题旁 | 大图 / 插图 → `TopicIcon` |
| `CheckBadge`（kit） | 对勾圆徽章 | "已完成"状态 | 要盖章体量 → `StampSeal` |
| `FitCard`（fxkit） | 防出格卡片（`h` 必须经 `fitH()` 算） | 任何文字卡片 | 禁止手写"看着差不多"的固定高度 |
| `Typewriter`（fxkit） | 打字机（标点分级停顿、块光标） | 一个字一个字敲出来；正在写 | 改了什么 → `DiffView`；整段代码 → `HighlightCode` |
| `StampSeal`（fxkit） | 印章砸下（2.6x→1 压下，-8°） | 盖章定论 / 认证 | 字数 >4 溢出圆 |
| `Funnel`（fxkit） | 尝试漏斗（宽进窄出 + 计数 + 滴落点） | 逐级递减 / 收束 | 只有一个百分比 → `ProgressRing` |
| `ChatThread`（fxkit） | 对话气泡（typing 三点 → pop，左右交替） | 模拟 AI 对话 / Prompt 交互（多方案对比时备选 `Tabs`） | 2–3 条（1 问 + 1~2 答），否则溢出窗口高度 |
| `ProgressRing`（fxkit） | 进度环（dashoffset + 中央标签） | **只有一个**百分比 | 多份额 → `Chart`；有前后值 → `MetricGrid` |
| `DiffView`（fxkit） | 补丁 diff（红删绿加逐行滑入；`before`/`after` 由 jsdiff 算行） | 讲改了什么 | 无增无删时别用 |
| `SkeletonCard`（fxkit） | 骨架 → 内容（等待 beats 先占位） | 已知要等（拉取 / 计算有过程） | 内容本该立刻出现时别用 |
| `StaggerList`（fxkit） | 级联列表（逐行滑入 + 微旋转） | 只是逐行出现，防 bullets 堆砌 | 相邻开始至少 12 帧（`stagger` 取 12，见 [draftpaper.md#reveal-rules](draftpaper.md#reveal-rules)）；要完成态 → `Checklist` |
| `ConsoleWindow`（media） | 控制台 / 终端窗口（整块界面） | 正在跑、命令行；终端形态 | 必须给 `h`，否则高度由内容撑；带行号高亮的代码 → `HighlightCode` |
| `MetricGrid`（media） | 指标网格（before→after 替换，数字滚动） | 前后值成对 | 只有一个值 → `StatRow` |
| `StampBanner`（media） | 结论吸底条（三段式落定 + 底色闪） | 砸一句结论、吸底；口号备选 | 一镜别砸两条（互压底线） |
| `StageFrame`（stagekit） | 活体主体框（header / main / rail / stamp） | 一个主体持续演化（≥5 拍） | 只有 2–3 拍别用（状态机撑不起来），备选 `Corridor` |
| `PhaseRail`（stagekit） | 状态进度轨（状态机显式画出来） | 让观众看见推进到第几步 | 静态内容别用 |
| `Corridor`（skeletons） | 走廊 / 流程骨架（到站 + 停留 + 对勾描线，隐含顺序） | 演示一段流程；因果的备选 | 站点 <3 个改用 `StaggerList` |
| `SplitStage`（skeletons） | 双栏对比（先暗输方，再亮赢方） | 两个对等对象对比 | 两方不是同一维度别用 |
| `ZoomStage`（skeletons） | 整体→聚焦→标注→回整体（B 段插入） | 放大看局部（0.8–2s 取证）；圈住一处的备选 | 会缩放，静止元素别用 |
| `RevealMask`（insert） | 镜头级遮罩揭示（ltr / rtl / ttb） | 镜头进场要"揭开" | 逐条揭示 → `ClipReveal` |
| `ShotCamera`（shotkit） | 受限相机外壳（只做 transform / opacity） | 每一镜都要 | 页眉 / 章节卡 / 字幕放在它**之外**（否则被运镜带动） |
| `CoverPanel`（shotkit） | 局部底托 / 卡片底 | 内容压到背景装饰区时 | 规则见 §4.2：wash 负 z、羽化、不铺整幅 |
| `Callout`（toolkit） | 圈住一处 + 引线 + 手写标注 | 圈住 / 指出一处 | 画面已有高亮别叠（重复编码） |
| `Checklist`（toolkit） | 带完成态的清单（`done` 后序号变对勾） | 列清单、要完成态 | 项 >6 溢出；只是逐行出现 → `StaggerList` |
| `JumpInText`（toolkit） | 逐字跳入（字色激活） | 念一句口号（钩子与收尾） | 全片最多 1–2 处；讲解中段显浮夸 |

### 2.2 选型提示

- 先按「内容 → 介质」路由（§1）决定要不要组件，再在 §2.1 按「何时用 / 何时别用」挑。

<a id="commons-media"></a>
## 3. 真实素材：Wikimedia Commons / Openverse

每个有实物的选题都应先搜一次开源图库，避免凭空臆造：

```text
python scripts/commons-search.py search "<英文关键词>" --project <工程>
python scripts/commons-search.py add <工程> "File:<文件名>" --id <素材id>
python scripts/commons-search.py credits <工程>
```

- **许可白名单**：只收 `PD`（公有领域）、`CC0-1.0`、`CC-BY-2.0`、`CC-BY-3.0`、`CC-BY-4.0`、`Apache-2.0`。`NC`、`ND` 或未知许可一律判 P0 拦截。`CC BY-SA` 缺省不收：「相同方式共享」会让整条片子须以 CC BY-SA 发布，常与短视频平台条款冲突；用户确认接受时 `commons-search.py` 加 `--allow-by-sa`，manifest 记 `shareAlike: true`。
- **交付署名清单**：交付前跑 `commons-search.py credits <工程>` 生成 `CREDITS.md`。
- **自动署名**：`MediaFrame` 自动在画面上显示署名徽章，禁止在场景代码里隐藏或手画假署名（`validate-media.py` 判 P0）。
- **找不到兼容许可**：改用组件重画结构，或停下询问用户是否提供自有素材。

<a id="real-media"></a>
## 4. 自备截图、录屏与清晰度门禁

- 自备素材通过 `scripts/prepare-media.py` 入库并登记到 `manifests/media.json`。
- **视频格式硬要求**：H.264、恒定 `FPS`（30）、`yuv420p`、默认静音；不合规视频运行 `prepare-media.py` 自动转码。
- **清晰度门禁（`validate-media.py`）**：原图尺寸与最终显示尺寸（含相机推近倍数）之比不得放大超过 **1.5 倍**，否则判 P0（「会糊」）；显示框 `w`/`h` 应写成字面量或同文件常量，量不出时按占满画布估算并给 P1 提示。
- **防冲突与去幽灵遮罩**：`MediaFrame` 的 `focus` 与 `cinema.focus` 二选一不叠放大；`flat`/`cel` 压到背景装饰区须坐 `CoverPanel`，禁止整幅半透明 wash 洗成幽灵。
- **区域引用**：`focusRegion` 引用的区域名必须在 `manifests/media.json` 中存在，否则判 P0。
- **位图登记（`validate-visual-plan.py`）**：用到的每张位图（皮肤背景、用户图；用户图放在 `public/illustrations/`）都登记到 `manifests/visual-assets.json`：`id`、`path`、`source_type`（`ai-generated` / `user-supplied` / `licensed-third-party` / `code-generated`）、`use_context`、`crop_policy`、`rights`、`sha256`；`ai-generated` 另需 `provider`、`prompt_summary` 与 `baked_text: false`。这里的 ID 要与工程声明、各场景引用的 `visual_asset_ids` 完全一致。交付物里不留没用到的图，再分发权利不明的素材不进工程。

<a id="html-capture"></a>
## 5. 网页与界面截图规范

- 截取软件界面或网页时，使用高分辨率（≥ 1600px 宽）干净视口，隐藏无关浏览器标签栏与个人隐私信息。
- 截图进入工程后按真实素材走 `manifests/media.json` 登记与清晰度门禁，不把图版强套进花哨的浏览器装饰壳里。
- **录制现成的交互网页**（只在用户明确要求时；新讲解片一律走 Remotion 工程）：优先让页面暴露按帧控制的函数（如 `window.renderAt(seconds)`），逐帧设时间、按交付尺寸截 PNG、FFmpeg 编码，旁白另外合成；页面做不到才用实时录屏，隐藏浏览器栏、通知与鼠标，固定视口与缩放，先录无声母版。录屏不能代替校验，录完要核时长、尺寸、帧率与镜头边界。

<a id="background-library"></a>
## 6. 皮肤背景库契约

- 全部背景登记在 `assets/lecture-template/manifests/backgrounds.json`，每套皮肤至少具备锁定 3 张（`main` / `chapter` / `quiet`）及背景库轮换图（手作皮肤 ≥8 张，`flat`/`cel` ≥4 张）。
- `scripts/validate-backgrounds.py` 硬拦截项（P0）：许可不在白名单、CC BY 缺署名、平均相对亮度 `< 0.55`（非亮底）、字幕区最暗 5% 与皮肤墨色对比度 `< 4.5:1`、`sha256` 校验失败。
- `bgMode` 选配：手作默认 `chapter`、组件默认 `shot`、全片一张可选 `film`；可用 `"bgRotate": false` 或单镜 `"bg"` 覆盖。
- `resolve-shots.py` 默认自动轮换背景保证相邻镜不重复；显式指定不存在或跨皮肤背景判 P0，显式相邻重复记 P1。
