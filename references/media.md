# 介质路由、真实素材与背景库

本篇定义内容到视觉介质的路由、外部授权素材（Wikimedia Commons / Openverse）与自备截图录屏入库门禁，以及皮肤背景库契约。产品硬约束：**不调用生图模型，只收公有领域 / CC0 / CC BY 素材**。

<a id="media-routing"></a>
## 1. 内容 → 视觉介质路由

| 你要讲什么 | 优先介质 | 对应版式 / 组件 | 避免 |
|---|---|---|---|
| 真实历史物件、标本、原书图版、照片 | 真图版（手账页） | `layout: "page"`（`plate` / `loupe`） | 纯文字卡片或简笔画替代实物 |
| 流程步骤、状态流转 | 结构流程图 | `flow` | 大段文字平铺 |
| 数值对比、性能测试 | 条形图 / 大数字 | `bars` / `number` | 段落里堆一串数字 |
| 误区纠偏、方案优劣 | 左右对照 | `compare` | 只靠红绿配色不加文字标记 |
| 代码改动、接口报错 | 代码块 / 真实截图 | `code` / `media` | 超长代码硬塞进小字号 |
| 唯一核心关系 / 锤子句 | 直书页 / 印章横幅 | `type` / `StampBanner` / `HandLettering` | 套多层圆角框 |

<a id="component-index"></a>
## 2. 组件选型索引

**全技能唯一一份解释组件清单**（53 件，`KineticNumber` 属引擎运动件不计入）。帧参数铁律与 `props` 规则见 [components.md](components.md)；定制件放入 `src/custom/` 并在 `src/custom/index.ts` 注册。

### 2.1 组件索引

| 组件 | 用途 | 何时用 / 注意 |
|---|---|---|
| `Accordion` | 手风琴，展开项随帧累积 | 多项展开收起（一屏放不下时）；仅逐行出现用 `StaggerList`，改设置用 `ControlStack` |
| `Tabs` | 标签页，激活项由帧号决定 | 2–4 个方案切换；"被改动"状态用 `ControlStack` |
| `ControlStack` | 六种受控控件（`steps:[{at,value}]` 帧驱动） | 讲设置切换与参数变化；每行 1 个，勿抢主体戏份 |
| `OverlayFrame` | 拟真弹层 dialog/menu/popover/tooltip（Portal 到根） | 讲"弹出一个框"；压背景装饰区须坐 `CoverPanel` |
| `NetworkGraph` | d3-force 关系网（固定迭代） | 无层级、无方向关系网；有层级用 `TreeView` |
| `HighlightCode` | 语法高亮 + 行号 + 逐行聚焦窗口 | 真实页面形态代码；终端用 `ConsoleWindow`，逐字敲用 `Typewriter` |
| `MathBlock` | katex 公式块（静态确定性） | 有公式与推导时；无动画，勿作装饰 |
| `TopicIcon` | 单个题材图标（simple-icons + lucide-react） | 技术栈/品牌单点；成排用 `IconWall` |
| `IconWall` | 图标墙（错峰入场） | 技术栈或依赖清单具象化；无关勿放 |
| `Chart` | d3 图表（`variant`：line/area/stack/stackExpand/stream/radar/pie） | 多值趋势/分布/对比（支持 CSV）；单百分比用 `ProgressRing`，前后两值用 `MetricGrid` |
| `StatRow` | 多指标并排滚动卡 | 报大数字或等权指标并排；与 `MetricGrid` 二选一 |
| `KineticNumber` | 关键数字动态排版（170–380px，引擎件，不计 53 件） | 一镜聚焦单个核心数（耗时/倍数）；并排 ≥3 数用 `StatRow`，全片 ≤35% |
| `TreeView` | 目录树 + treemap/pack/sunburst（面积=数值） | 有层级或层级占比；无层级用 `NetworkGraph` |
| `GeoView` | d3-geo 真陆地轮廓（默认正交自转，`projection="flat"` 全局） | 地理/站点分布（不含国界地名）；勿混用两种投影 |
| `SankeyChart` | 流量分配流向图（d3-sankey） | 环节分流；单向递减用 `Funnel` |
| `QrCode` | 纯计算二维码（不联网） | 仅放片尾引导 |
| `SketchFx` | roughjs 确定性手绘框/下划线（fixed seed；含 hachure 等 6 种填色） | 手绘圈画；精确几何用 `ShapeDraw`（禁用含随机的 `'dots'`） |
| `FocusFx` | 注意力动作（dim / spot / loupe / marker） | 一镜一次聚光压暗；避免与缩放重复 |
| `GlowFrame` | 流光边框（警告/高亮） | 短暂强调；与 `ShimmerText` 二选一 |
| `ShimmerText` | 文字流光扫过 | 口号/金句点题；勿在中段滥用 |
| `ClipReveal` | clip-path 逐帧擦除 | 元素逐条揭示；镜头交接用 `RevealMask` |
| `NoiseJitter` | 有机确定性微抖（noise2D） | 贴纸/静止物微活；严禁用于文字 |
| `VerdictBar` | 底部全宽裁决结论条 | 镜尾收束；勿与 `StampBanner` 同镜叠压 |
| `PathDraw` | 描线生长 + 沿线动点/转向箭头（`showArrow`） | 因果/路径流转（路径需 ≥200px） |
| `MorphShape` | 形状连续变形（flubber / Remotion `interpolatePath`） | 同物形态演变 |
| `ShapeDraw` / `SHAPES` | `@remotion/shapes` 参数几何（星/多边形/箭头/标注框等） | 需要带语义的几何图示；图标用 `TopicIcon` |
| `SceneTransitions` | 接触表预览 20 种官方转场（`PRESENTATIONS` 样张） | 仅用于样张目录；成片切镜走镜头 `transition` 字段 |
| `FitTextBox` | 中文反推字号与断行 | 固定宽 + 行数上限定字号；控卡高用 `FitCard`/`fitH()` |
| `PillTag` | 胶囊贴标（kit） | 页眉 kicker、标签行 |
| `LineIcon` | 26 字形线条图标（kit，lucide-react） | 小标题图标；大图用 `TopicIcon` |
| `CheckBadge` | 对勾圆徽章（kit） | 已完成状态；大章用 `StampSeal` |
| `FitCard` | 防出格卡片（fxkit，`h` 须由 `fitH()` 算） | 任何文字卡片；严禁手写估高 |
| `Typewriter` | 打字机（fxkit，标点停顿+块光标） | 逐字敲出；代码差异用 `DiffView` |
| `StampSeal` | 印章砸下定论（fxkit） | ≤4 字定论/认证 |
| `Funnel` | 漏斗递减 + 计数（fxkit） | 逐级筛选收束 |
| `ChatThread` | 对话气泡（fxkit） | 2–3 条问答演示 |
| `ProgressRing` | 单百分比环形进度（fxkit） | 仅单一百分比 |
| `DiffView` | 红删绿加代码差异（fxkit） | 改前改后对比 |
| `SkeletonCard` | 骨架占位转真实内容（fxkit） | 有明确等待过程时 |
| `StaggerList` | 级联列表（fxkit，`stagger` 取 12 帧） | 逐行出现；带完成态用 `Checklist` |
| `ConsoleWindow` | 终端窗口（media，必传 `h`） | 命令行演示；带行号高亮代码用 `HighlightCode` |
| `MetricGrid` | before→after 数字滚动网格（media） | 前后成对数值 |
| `StampBanner` | 底部结论砸条（media） | 锤子句收束；一镜仅一条 |
| `StageFrame` | 活体演化框（stagekit：header/main/rail/stamp） | 单主体 ≥5 拍连续演化；2–3 拍用 `Corridor` |
| `PhaseRail` | 状态机进度轨（stagekit） | 推进阶段指示；静态内容勿用 |
| `Corridor` | 流程站台骨架（skeletons） | ≥3 站因果流程；<3 站用 `StaggerList` |
| `SplitStage` | 双栏对比骨架（skeletons，先暗输后亮赢） | 同维度二选一对比 |
| `ZoomStage` | 整体→聚焦→标注→回整体（skeletons） | 0.8–2s 局部放大取证 |
| `RevealMask` | 镜头遮罩揭开（insert：ltr/rtl/ttb） | 镜头入场揭示 |
| `ShotCamera` | 受限相机外壳（shotkit，仅 transform/opacity） | 每镜主体外层（页眉/字幕在其外） |
| `CoverPanel` | 局部底托（shotkit） | 压背景装饰区时（`wash` 负 z 羽化，不铺整幅） |
| `Callout` | 圈注 + 引线 + 手写标注（toolkit） | 指出关键处；不与缩放高亮叠加 |
| `Checklist` | 带对勾完成态清单（toolkit，≤6 项） | 核对清单 |
| `JumpInText` | 逐字激活（toolkit） | 开场钩子或收尾口号，全片 ≤2 处 |

### 2.2 选型提示

按 §1 选介质后在 §2.1 按「何时用 / 注意」挑。

<a id="commons-media"></a>
## 3. 真实素材：Wikimedia Commons / Openverse

有实物的选题优先检索开源图库：
```text
python scripts/commons-search.py search "<英文关键词>" --project <工程>
python scripts/commons-search.py add <工程> "File:<文件名>" --id <素材id>
python scripts/commons-search.py credits <工程>
```
- **许可白名单**：只收 `PD`、`CC0-1.0`、`CC-BY-2.0`、`CC-BY-3.0`、`CC-BY-4.0`、`Apache-2.0`；`NC`/`ND`/未知许可判 P0。`CC BY-SA` 默认排除，用户确认接受时加 `--allow-by-sa`（`shareAlike: true`）。
- **强制署名**：`MediaFrame` / `ArchivePhoto` / `PinnedPhoto` / `LoupeMedia` 自动上屏署名并导出 `CREDITS.md`，禁止隐藏或伪造（`validate-media.py` 判 P0）。找不到合规图则用组件重画或停下问用户。

<a id="real-media"></a>
## 4. 自备截图、录屏与清晰度门禁

- 自备素材通过 `scripts/prepare-media.py` 登记 `manifests/media.json`；视频强制 H.264、30fps、`yuv420p`、默认静音。
- **清晰度门禁（`validate-media.py`）**：原图相对最终显示尺寸（含推近）放大不得超 **1.5×**，否则 P0；`focusRegion` 必须存在于 `media.json`。
- `MediaFrame` 的 `focus` 与 `cinema.focus` 二选一；`flat`/`cel` 压装饰区走 `CoverPanel`。
- **位图台账（`validate-visual-plan.py`）**：每张位图（背景与 `public/illustrations/` 用户图）须与 `manifests/visual-assets.json`（`id`、`path`、`source_type`、`use_context`、`crop_policy`、`rights`、`sha256`）及场景 `visual_asset_ids` 完全一致，交付物不留未用图。

<a id="html-capture"></a>
## 5. 网页与界面截图规范

- 截软件/网页用 ≥1600px 宽干净视口，隐去无关标签与隐私信息，按 `media.json` 登记，不套花哨浏览器装饰壳。
- 仅用户明确要求录制现成交互网页时：优先按帧驱动函数（如 `window.renderAt(seconds)`）逐帧截图编码后再配音，否则隐藏界面栏固定视口录无声母版并复核尺寸帧率。

<a id="background-library"></a>
## 6. 皮肤背景库契约

- 背景登记于 `assets/lecture-template/manifests/backgrounds.json`，每套含锁定 3 张（`main`/`chapter`/`quiet`）及轮换图库（手作 ≥8 张，`flat`/`cel` ≥4 张）。
- `scripts/validate-backgrounds.py` P0 拦截：许可非法、CC BY 缺署名、相对亮度 `< 0.55`、字幕区对比度 `< 4.5:1`、`sha256` 不符。
- `bgMode`：手作默认 `chapter`、组件默认 `shot`、全局可选 `film`；`resolve-shots.py` 自动轮换避免相邻重复。
