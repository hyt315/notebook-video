# 维护者手册（MAINTAINING）

> **仅维护者阅读；做片子请回到 [SKILL.md](SKILL.md)。** 本文件不进发布包（`.gitattributes` export-ignore）。
> 这里放文档结构、合并对照表、维护纪律等维护期内容。原计划移到这里的 remotion-architecture / dependency-policy / official-skills-exemplar
> 里有 agent 也要守的规则（依赖边界、时长延长不变式、模板驳回条件），所以留在发布文档 `references/technique.md`、`references/scenes.md`。

## 文档结构与合并对照（第 1 批 #9）

面向 agent 的文档（发布）：`SKILL.md`（入口路由）+ `references/` 9 篇 + `references/themes/` 6 篇 + `references/MOVED.md`（旧名索引）。
面向维护者（不发布）：本文件、`CHANGELOG.md` 的旧档 `docs/history/CHANGELOG-legacy.md`、`scripts/dev/`、`tests/`。

合并方式：每篇旧文档**整篇**搬进新文件的一节（节前 `<a id="旧文件名"></a>`，标题降一级），所以旧文档里的每条规则都原样在新位置；
全仓库 `.md/.py/.mjs/.cjs/.json` 里指向旧文件的链接、路径、错误提示一律改成 `新文件#旧文件名`。
模板 `.ts/.tsx` 注释里的路径已在第 2 批改为新位置（`check-links.py` 一并检查）；`references/MOVED.md` 保留给外部旧链接换算。

后续可做的压缩（第 2 批起，需逐条核对后再删）：`media.md` 里 media-routing 部分仍是原文全量（约 42 KB），组件索引与 `src/components` 重复，可改为由代码生成；
`checks.md` 里 composition-gate / presentation-gate 的实现口径与事故记录可迁到本文件，只留「每类报错怎么修」。

### 旧 references → 新位置（52 篇，含 INDEX）

| 旧文件 | 新位置 | 原标题 | 处置 |
|---|---|---|---|
| `references/director-method.md` | `references/director.md#director-method` | 导演层：先找"只属于这个题"的东西，再动手 | 整篇原文搬入，标题降一级 |
| `references/narrative-moves.md` | `references/director.md#narrative-moves` | 讲法规范（叙事动作 · 误解优先 · 留白）——第三张表：**怎么讲** | 整篇原文搬入，标题降一级 |
| `references/narrative-hook.md` | `references/director.md#narrative-hook` | Cold-open narrative contract | 整篇原文搬入，标题降一级 |
| `references/pacing-rhythm.md` | `references/director.md#pacing-rhythm` | Pacing and rhythm contract | 整篇原文搬入，标题降一级 |
| `references/style-recipes.md` | `references/director.md#style-recipes` | 风格配方：把一种"观感"拆成可执行的八个轴 | 整篇原文搬入，标题降一级 |
| `references/visual-director.md` | `references/director.md#visual-director` | Visual director and generated-image workflow | 搬入；§2「检测生图能力」§3「生图提示词」改写为「图从哪来（用户 / Commons / 授权）」与「素材怎么挑」（#8 删生图段）；§1、§4–§7 原样 |
| `references/reveal-rules.md` | `references/draftpaper.md#reveal-rules` | 出现规则（草稿纸讲解） | 整篇原文搬入，标题降一级 |
| `references/draftpaper-design.md` | `references/draftpaper.md#draftpaper-design` | 草稿纸讲解 · 设计规范 | 整篇原文搬入，标题降一级 |
| `references/motion-design.md` | `references/draftpaper.md#motion-design` | Motion design contract | 整篇原文搬入，标题降一级 |
| `references/scene-skeletons.md` | `references/scenes.md#scene-skeletons` | 场景骨架与分镜表 | 整篇原文搬入，标题降一级 |
| `references/scene-authoring.md` | `references/scenes.md#scene-authoring` | 场景编写说明书（照着抄，不要重新发明） | 整篇原文搬入，标题降一级 |
| `references/handwritten-scenes.md` | `references/scenes.md#handwritten-scenes` | 手写场景路线（完整作者手册） | 整篇原文搬入，标题降一级 |
| `references/independent-parts.md` | `references/scenes.md#independent-parts` | Independent components and layer contracts | 整篇原文搬入，标题降一级 |
| `references/lecture-composition.md` | `references/scenes.md#lecture-composition` | Lecture composition: the default multi-zone visual route | 整篇原文搬入，标题降一级 |
| `references/canvas-modes.md` | `references/scenes.md#canvas-modes` | Canvas: 16:9 only | 整篇原文搬入，标题降一级 |
| `references/recipes.md` | `references/scenes.md#recipes` | 七个线稿配方（`recipe`）· 降级为可选 | 整篇原文搬入，标题降一级 |
| `references/fxkit.md` | `references/components.md#fxkit` | fxkit：固定动效组件库（反 PPT 专用） | 整篇原文搬入，标题降一级 |
| `references/craft-kit.md` | `references/components.md#craft-kit` | craft 组件：手作材质 | 整篇原文搬入，标题降一级 |
| `references/linework.md` | `references/components.md#linework` | 线稿层（`sketch`）· 弱模型写法 | 整篇原文搬入，标题降一级 |
| `references/journal-page.md` | `references/components.md#journal-page` | 手账页 · 把真东西摆到观众眼前 | 整篇原文搬入，标题降一级 |
| `references/shot-language.md` | `references/camera.md#shot-language` | 镜头语言：受限配方 + 出界数学证明 | 整篇原文搬入，标题降一级 |
| `references/camera-language.md` | `references/camera.md#camera-language` | 镜头语言：为什么动、动多少、什么时候不动 | 整篇原文搬入，标题降一级 |
| `references/cinema-camera.md` | `references/camera.md#cinema-camera` | 引擎虚拟镜头（`src/cinema.tsx`） | 整篇原文搬入，标题降一级 |
| `references/fx-effects.md` | `references/camera.md#fx-effects` | 真翻页 / 揭纸转场（`@remotion/effects`） | 整篇原文搬入，标题降一级 |
| `references/media-routing.md` | `references/media.md#media-routing` | 内容 → 视觉介质 路由 | 整篇原文搬入，标题降一级 |
| `references/commons-media.md` | `references/media.md#commons-media` | 真实素材：先搜 Wikimedia Commons / Openverse | 整篇原文搬入，标题降一级 |
| `references/real-media.md` | `references/media.md#real-media` | 真实素材（截图 / 录屏 / 动图） | 整篇原文搬入，标题降一级 |
| `references/html-capture.md` | `references/media.md#html-capture` | HTML and website capture | 整篇原文搬入，标题降一级 |
| `references/background-library.md` | `references/media.md#background-library` | 背景库 · Background library | 整篇原文搬入，标题降一级 |
| `references/tts-audio.md` | `references/audio-captions.md#tts-audio` | TTS and declarative audio | 整篇原文搬入，标题降一级 |
| `references/subtitle-timing.md` | `references/audio-captions.md#subtitle-timing` | Subtitle timing and absolute-frame contract | 整篇原文搬入，标题降一级 |
| `references/sfx-library.md` | `references/audio-captions.md#sfx-library` | SFX library | 整篇原文搬入，标题降一级 |
| `references/audio-ducking.md` | `references/audio-captions.md#audio-ducking` | 音效与旁白的相对电平（P2-20 的剩余部分） | 整篇原文搬入，标题降一级 |
| `references/auto-engine.md` | `references/technique.md#auto-engine` | auto 引擎：story.json → 成片 | 整篇原文搬入，标题降一级 |
| `references/environment-matrix.md` | `references/technique.md#environment-matrix` | 环境矩阵：这台机器能出什么片 | 整篇原文搬入，标题降一级 |
| `references/cross-platform-compatibility.md` | `references/technique.md#cross-platform-compatibility` | Cross-platform compatibility contract | 整篇原文搬入，标题降一级 |
| `references/windows-compatibility.md` | `references/technique.md#windows-compatibility` | Windows-specific compatibility notes | 整篇原文搬入，标题降一级 |
| `references/performance-design.md` | `references/technique.md#performance-design` | Performance design contract | 整篇原文搬入，标题降一级 |
| `references/quality-checklist.md` | `references/checks.md#quality-checklist` | Delivery acceptance checklist | 整篇原文搬入，标题降一级 |
| `references/official-aesthetic-system.md` | `references/checks.md#official-aesthetic-system` | Official aesthetic system | 整篇原文搬入，标题降一级 |
| `references/composition-gate.md` | `references/checks.md#composition-gate` | 构图门禁：把"审美"变成可执行检查 | 整篇原文搬入，标题降一级 |
| `references/presentation-gate.md` | `references/checks.md#presentation-gate` | 呈现效果门禁（`validate-presentation.py`） | 整篇原文搬入，标题降一级 |
| `references/theme-system.md` | `references/themes/system.md#theme-system` | Theme system: shared contract | 整篇原文搬入，标题降一级 |
| `references/theme-flat.md` | `references/themes/flat.md` | Theme contract: flat (calm modern edu illustration) | 整篇原文搬入，标题降一级 |
| `references/theme-cel.md` | `references/themes/cel.md` | Theme contract: cel (bold comic / manga) | 整篇原文搬入，标题降一级 |
| `references/theme-journal.md` | `references/themes/journal.md` | 皮肤契约：journal · 博物学家手账 | 整篇原文搬入，标题降一级 |
| `references/theme-papercut.md` | `references/themes/papercut.md` | 皮肤契约：papercut · 红色窗花剪纸 | 整篇原文搬入，标题降一级 |
| `references/theme-archive.md` | `references/themes/archive.md` | 皮肤契约：archive · 档案灯台 | 整篇原文搬入，标题降一级 |
| `references/remotion-architecture.md` | `references/technique.md#remotion-architecture` | Remotion architecture contract | 整篇原文搬入，标题降一级 |
| `references/dependency-policy.md` | `references/technique.md#dependency-policy` | 依赖政策：什么能引，什么不能引 | 整篇原文搬入，标题降一级 |
| `references/official-skills-exemplar.md` | `references/scenes.md#official-skills-exemplar` | Official exemplar | 整篇原文搬入，标题降一级 |
| `references/INDEX.md` | `SKILL.md` | 文档索引（并入 SKILL.md 的路由表） | 整篇原文搬入，标题降一级 |

`references/locked-style-contract.json` 原样保留（validate-skill 读它；第 2 批并入 `contract.json`）。
`references/INDEX.md` 删除：分组路由并入 `SKILL.md` 的「去哪读」表，每篇的去向即上表。

### 原 SKILL.md 规则 → 新位置（第 1 批 #8）

原 SKILL.md 正文（frontmatter 之后、「文档」一节之前）**整段原文**搬进 `references/technique.md#skill-workflow`；新 SKILL.md 只做路由并复述最关键的约束。

| 原 SKILL.md 规则 | 新 SKILL.md 落位 | reference 落位 |
|---|---|---|
| 第一原则：草稿纸讲解、无笔、讲到才出现、冲突时按草稿纸 | SKILL「第一原则」 | `draftpaper.md#reveal-rules` |
| 出现规则 1–4（字数×4 帧 12–45、线稿 24–45、圈注 14/下划线箭头 12/手写 24、相隔 ≥12 帧、同时 ≤2、开镜 6 帧内 ≤1） | SKILL「出现规则」（数字原样） | `draftpaper.md#reveal-rules` |
| 手账页承载 / 组件讲解、交替出现 | SKILL「画面怎么分工」 | `components.md#journal-page` |
| 三种 mode 配比（hybrid 20–75%/≥25%，component ≤12%/≥60%，freeform ≥40%/多框 ≤10%）；mode 是门禁契约 | SKILL「画面怎么分工」 | `technique.md#skill-workflow` |
| 主题物全片至少出现一次，否则 P0 | SKILL「画面怎么分工」 | `technique.md#skill-workflow` |
| 手账页容器是纸，不套圆角框、不做成浏览器截图卡片 | SKILL「画面怎么分工」 | `components.md#journal-page` |
| 线稿只做标本速写；文字+简笔线稿 >20% 记 P1 | SKILL「画面怎么分工」 | `components.md#linework` |
| 直书页每行 ≤10 字、≤5 行、全片 ≤40% | SKILL「画面怎么分工」表 | `components.md#journal-page` |
| 锤子帧 2–3 个、1.5–2.5 秒，组件用 StampBanner / 手作用 HandLettering 或 Seal | SKILL「画面怎么分工」 | `director.md#pacing-rhythm` |
| 只有 16:9；五个皮肤 | SKILL「画面怎么分工」 | `themes/system.md` |
| TTS 是正式步骤；无真实旁白 --render 停；默认无 BGM、音效稀疏 | SKILL「五步命令」 | `audio-captions.md#tts-audio` |
| 先选路线表（题目→mode→皮肤） | SKILL「选路线」 | `technique.md#skill-workflow` |
| 每个选题先搜 Commons / Openverse；只收 PD / CC0 / CC BY；署名上屏 | SKILL「选路线」 | `media.md#commons-media` |
| 导演层（手作必做）：treatment.json 七步、三候选至少 2 族 | SKILL「选路线」 | `director.md#director-method` |
| 手作路线必读 4 份；auto 路线必读 2 份 | SKILL「去哪读」下一段 | `technique.md#skill-workflow` |
| 整片渲染前独立评审写 review.rounds；--skip-review | SKILL「五步命令」 | `director.md#director-method` |
| 蓝图表（10 个蓝图对应题目） | SKILL「选路线」（蓝图名） | `technique.md#skill-workflow（完整表）` |
| 组件路线照蓝图 $components 选骨架与组件，别发明版式 | SKILL「选路线」主路线 | `technique.md#skill-workflow` |
| new-project 命令；手作 --style 下载 Noto Serif SC | SKILL「五步命令」 | `technique.md#skill-workflow` |
| 翻页是缺省（pageturn→pageflip、同向）；纸声；探针与拼帧；装浏览器 | —（细节下沉） | `technique.md#skill-workflow、camera.md#fx-effects` |
| 照抄示例片结构（shots.json/scenes.tsx/film.ts/字幕） | SKILL「选路线」逃生舱 | `technique.md#skill-workflow、scenes.md#handwritten-scenes` |
| 抄结构不抄片子：eval-project 对比 | SKILL「五步命令」 | `technique.md#skill-workflow` |
| 一镜 1–3 句、字幕 ≤16 字自动拆、cinema.focus、相邻换骨架、KineticNumber | SKILL「五步命令」（前两条） | `technique.md#skill-workflow` |
| 背景 bgMode / bgRotate / bg 指定 | —（细节下沉） | `technique.md#skill-workflow、media.md#background-library` |
| 帧参数名 fxkit 传 frame、其余传 f | SKILL「选路线」逃生舱 | `scenes.md#handwritten-scenes` |
| make-video 流水线、OCR 可选 | — | `technique.md#skill-workflow` |
| 旁白顺序；改了 story 必须重跑 compose 再 tts；--allow-stale | SKILL「五步命令」 | `technique.md#skill-workflow` |
| 先 --stills 再渲整片；整片渲染先征得用户同意 | SKILL「五步命令」+「何时停下问用户」 | `technique.md#skill-workflow` |
| --render 默认 1920×1080；响度 −16 LUFS | — | `technique.md#skill-workflow` |
| --resume；raw 产物成功后才删；看门狗 8 分钟 | SKILL「五步命令」(--resume) | `technique.md#skill-workflow` |
| eval-project 不打分，判据只在门禁 | — | `technique.md#skill-workflow` |
| 读输出 ✓/·/✗；同一 ✗ 两次没改过停下告诉用户 | SKILL「读输出」 | — |
| 交付 captions.srt / poster.jpg；poster 取招牌镜落定窗口、不画字幕；不拿几何中点当封面 | SKILL「五步命令」（产物名） | `technique.md#skill-workflow` |
| preview / --fx=on / 只截转场帧 / measure-reveal / FillGate 读数与两条豁免 | — | `technique.md#skill-workflow` |
| 被判空不放大卡片凑面积；不为开头满提前摆上 | SKILL「读输出」 | `technique.md#skill-workflow、checks.md#composition-gate` |
| 片子 >30 秒用 sweep；15 的倍数帧、后半段；覆盖率只认 render 与 sweep | SKILL「五步命令」(sweep) | `technique.md#skill-workflow` |
| 定制组件：只用 f、文字 ≥32px、文字色 C.ink/C.muted/C.*Ink | SKILL「选路线」逃生舱 | `technique.md#skill-workflow` |
| 真实截图/录屏：prepare-media、MediaFrame、来源优先级、无兼容许可用组件重画 | SKILL「选路线」(许可) | `technique.md#skill-workflow、media.md#real-media` |
| 硬门禁（客观）清单与软建议 | — | `technique.md#skill-workflow、checks.md` |
| 引擎验不了事实：validate-facts --review 人工审读；claim 标注规则 | SKILL「读输出」 | `technique.md#skill-workflow` |
| 开场门禁 O1–O5 记 P1、像素 O6/O7 手作 P0 | — | `technique.md#skill-workflow、checks.md` |
| 音效规则（offsetMs、间隔 ≥150 ms、sfxDensity） | — | `technique.md#skill-workflow、audio-captions.md#sfx-library` |
| auto 路线版式清单；statement 只是一张卡片 | SKILL「选路线」（主路线） | `technique.md#skill-workflow、technique.md#auto-engine` |
| 自检三命令；BudouX 自带；did NOT run 是真故障 | SKILL「读输出」 | `technique.md#skill-workflow` |
| 依赖纪律：scripts 只用标准库；新增 npm 依赖要用户同意 | SKILL「何时停下问用户」 | `technique.md#dependency-policy` |
| 生图相关（原 visual-director） | 删除（#8：技能不调用生图模型） | `director.md#visual-director 改写` |

原「文档」一节（51 篇索引、自检、BudouX）由新 SKILL 的「去哪读」「读输出」承接。


---

## media.md#media-routing 压缩对照（第 2 批）

`references/media.md` 的 media-routing 一节由 42,269 字节压到约 31,100 字节（全文 73,547 → 约 62,400）。做法：同一条规则只留一处（件的边界与实现注意只在 §5.1 行里，§2 路由表只留分支条件，「修辞动作」表只留首选 / 备选与条件），删掉历史叙述与实测故事，规则原文语义不变。下表逐条列出压缩前的规则与它现在的位置；「删」只用于非规则内容，并写明理由。

| # | 压缩前的规则（原小节） | 现在在哪 |
|---|---|---|
| 1 | 落地件 media/fxkit/kit；门禁 validate-composition 介质多样性 ≥3（节首） | 节首引用块 |
| 2 | 像 PPT 的原因是单一介质；要不同介质；路由表是"何时用哪个"的决策入口（§1） | §1（三句合一段） |
| 3 | 路由表每行一个首选，其余标"何时才用"（§2 引用块） | §2 列表第 1 条 |
| 4 | 加组件 = 换掉一件；上限见 dependency-policy §8（§2） | §2 列表第 2 条 |
| 5 | 本表管"内容配哪个件"，件清单只看 §5.1（§2） | §2 列表第 3 条 |
| 6 | 数据：Chart 按语义选 variant；单个百分比 ProgressRing；前后两值 MetricGrid（§2） | §2「数据」行；variant 全列表在 §5.1 Chart 行 |
| 7 | 真实数据直接喂 CSV（csv=…，csvToChartSeries，不手抄数组）（§2「真实数据进图」行） | §2「数据」行（两行合并） |
| 8 | 软件界面：ConsoleWindow、HighlightCode 窗口壳；弹框 → OverlayFrame（§2） | §2「软件流程」行 |
| 9 | 代码：HighlightCode；逐字敲 Typewriter；改了什么 DiffView（§2） | §2「技术代码」行 |
| 10 | 结构：连线 PathDraw；网 NetworkGraph；清单 Checklist；逐行 StaggerList（§2） | §2「结构关系」行 |
| 11 | 分步展开 Accordion；多标签 Tabs（§2） | §2 两行（删"此前零覆盖"历史注） |
| 12 | 配置被改动 → ControlStack，帧→状态表 steps，纯函数；别用文字卡假装（§2） | §2 行 + §5.1 ControlStack 行 |
| 13 | 技术栈 IconWall / TopicIcon；抽象概念 StageFrame + SVG（§2） | §2 两行 |
| 14 | 强调：ShimmerText / GlowFrame / JumpInText / StampSeal（§2） | §2「强调信息」行 |
| 15 | 几何 ShapeDraw/SHAPES（形状清单）；饼图别找图形件 → Chart pie / ProgressRing（§2） | §2 行（分支）+ §5.1 ShapeDraw 行（形状清单、"份额别用它"） |
| 16 | PathDraw showArrow，getTangentAtLength，不用自己算切线（§2） | §2 行 + §5.1 PathDraw 行 |
| 17 | 证据细节 ZoomStage（§2） | §2 行 |
| 18 | 指标：KineticNumber / StatRow / VerdictBar / MetricGrid / StampBanner 分支（§2） | §2「指标结论」行 |
| 19 | 对话 ChatThread；层级 TreeView + treemap/pack/sunburst（§2） | §2 两行 |
| 20 | GeoView：land-110m 真轮廓、55 KB、标记点、flat/正交 spin、不含国界地名、要国界另立一件别扩语义（§2 + §5.1 重复） | §5.1 GeoView 行（一处） |
| 21 | Sankey；MathBlock 静态确定性；QrCode 纯计算不联网；Funnel/ProgressRing 收束（§2） | §2 各行 + §5.1 对应行 |
| 22 | SketchFx：seed 固定、6 种确定性 fillStyle 及名称、hachure 招牌、'dots' 因 Math.random 移除（§2 + §5.1 重复） | §5.1 SketchFx 行（一处） |
| 23 | SceneTransitions：20 种全部登记、命名规则 = PRESENTATIONS 键、11 着色器 / 9 几何（bookFlip 属几何）、本机全部可用、flip 50% 侧对截 25/75%、none 硬切、无 Math.random（§2 + §5.1 + §6 重复） | §5.1 SceneTransitions 行（一处）；§6 只留"看 flip 截 25/75%，默认串 wipe" |
| 24 | 手写转场 3 式在 shotkit + insert（§2） | §2「场景衔接」行 |
| 25 | 不提供运动模糊件（motion-blur 已删，速度峰值不在七种意图）；用帧内位移 + 速度线，别手绘模糊（§2） | §2「快速运镜」行 |
| 26 | NoiseJitter 同种子同结果（§2） | §2 行 + §5.1 行 |
| 27 | FitTextBox / fitChineseTextOnNLines 治文字被裁；fitNodeLabel 宽高都过、<13px 不画字进图例（§2） | §2「文字排版」行（13px 注明 = MIN_LABEL_FONT） |
| 28 | 逐条揭示 ClipReveal；旧件 RevealMask 在 insert（§2） | §2 行 |
| 29 | 硬约束 P0：≥3 介质、每讲解场景 ≥1 活性组件、禁纯卡片堆（§2） | §2 表后 |
| 30 | A = 主体常驻 StageFrame，不是卡片轮播（§3） | §3 第 1 条 |
| 31 | B = 换介质插入 0.8–2 s（24–60 帧）说完即回；是注意力转移不是另一场景；不留残片（§3） | §3 第 2 条 |
| 32 | ZoomStage 实现，区间外返回 null，整体→聚焦→标注→回整体（§3） | §3 第 3 条 |
| 33 | B 结束回到 A 同一状态（§3） | §3 第 4 条 |
| 34 | 「recipes/EvidenceBridge.tsx 可回收使用」（§3） | **删**：仓库里没有这个文件，指向失效 |
| 35 | flat/cel 背景锁定不替换不重绘；装饰位置描述（§4.1） | §4.1 |
| 36 | 内容压装饰区必须坐 CoverPanel；BackgroundMute 已删（§4.1） | §4.1 引用块 |
| 37 | backgroundDecorZones：1920×1080、三变体并集、cel 6 / flat 4（§4.2） | §4.2 |
| 38 | CoverPanel 示例代码（§4.2） | §4.2（原样） |
| 39 | 无成片级整幅底托；中央 70% 安全区；整幅 wash 洗成幽灵；只给那一块垫 paper（§4.2） | §4.2 第 1 条 |
| 40 | z 序：底托在背景上内容下；wash 负 z；不用正 z（z=5 → 15% 不透明）；paper 默认 z=42（§4.2） | §4.2 第 2 条 |
| 41 | wash 不铺满整幅（§4.2） | §4.2 第 3 条 |
| 42 | wash 不能硬边（接缝）、径向渐变羽化、去 1px 描边环；示例代码（§4.2 + §4.2.1 重复） | §4.2.1（一处） |
| 43 | validate-shot-motion P1：contentBand 与装饰区相交未声明 cover（§4.3） | §4.3 |
| 44 | 面板填满：按可用高度排布（main 高公式）、520/196 例、拿不准居中或缩框、别降不透明度（§4.4） | §4.4 |
| 45 | OverlapGate 报所有重叠；有意重叠必须标注；四种标注（§4.5） | §4.5 表 |
| 46 | 白名单只用于同信息替换与镜头交接，不许掩盖不同信息压字（§4.5） | §4.5 表后 |
| 47 | 模块表（kit / components 27 件 / fxkit 9 / media / stagekit Attach 已删 / skeletons / insert / shotkit / index 不导出、只 16:9 一个 Composition、Paper/Subtitle/Chrome 私有、6 件已删 / toolkit）（§5） | §5 表（新增「帧参数」列） |
| 48 | 帧参数：fxkit 用 frame，其余 f；传错会时间轴错位（§5 警告，写的是"静默忽略、回落 useCurrentFrame"）；§5.1 另写 toolkit 也是 frame | §5 警告：fxkit 与 toolkit 用 `frame`，其余 `f`；**按 #13 现状改写**为"必填类型，传错名或漏传 tsc 报错"（原"静默回落"已不成立） |
| 49 | 布局陷阱：文档流标题与绝对定位组件混用会精确重叠；两种修法（§5） | §5 第二条警告 |
| 50 | §5.1 是唯一清单；components.md / showcase.tsx / 源码注释各管什么；SHOWCASE_VERSION 不渲染；改组件先改这里（§5.1） | §5.1 首段 |
| 51 | 53 件口径、各模块件数、不算件的列表、复核命令（§5.1） | §5.1「口径」段 |
| 52 | 帧参数名（§5.1 口径段重复） | 并入 §5 警告（#48） |
| 53 | 接触表列 / 使用记录列定义；"未使用"不等于从没渲染（§5.1） | §5.1 两条列表 |
| 54 | 53 件 + KineticNumber 每行的用途 / 何时用 / 别用 / 接触表 / 使用记录（§5.1） | §5.1 表，逐行保留；「修辞动作」表里的"何时别用"并入对应行（StatRow 不等权对比、StaggerList stagger 取 12、ChatThread 备选 Tabs、ZoomStage / Corridor 作备选、CoverPanel 指回 §4.2） |
| 55 | 10 件未上接触表：8 件不该进、StatRow/VerdictBar 该进没进（§5.1 缺口） | §5.1「两处缺口」第 1 条 |
| 56 | FocusFx 挂 SCENE_ANCHOR 进不了格子 → 第 ⑱ 整页，每 8 帧一态；JPG 只见 dim/loupe，spot/marker 以 mp4 为准（§5.1 缺口） | 第 2 条 |
| 57 | PieDraw / CameraMotionBlur / Trail 已删及理由；⑪ 空格换成标注框 + 引线（§5.1 缺口） | 第 3 条 |
| 58 | 未使用 25 件全在新封装层、全在接触表可见；旧 26 件全用过；FocusFx 真实工程记录；过渡态、替换要单独一轮（§5.1 缺口） | 第 4 条 |
| 59 | 接触表件数只查 §5.1、本节只讲机制（§6） | §6 首段 |
| 60 | showcase：18 页 × 1 秒，1920×1080；旧层 18 件口径（实际渲染）与 26 件 export 口径别混；⑤ 6 种运镜意图；⑥ 四骨架（StageFrame 未渲染）；⑨–⑱ 25 件 + 新能力 3 页（§6） | §6 列表 |
| 61 | 两条命令（mp4 / --sheet）（§6） | §6 代码块（原样） |
| 62 | mp4 是交付物：4/3 放大到 2560×1440、静音 AAC、色彩四项；默认参数出调试版会静默替换（§6） | §6 第 1 条 |
| 63 | 为什么要接触表：看图选型（§6） | §6 首段 |
| 64 | 第 ⑪ 页 durations=[12×4] td=6 → 30 帧，转场在 6–12/12–18/18–24 帧（§6「已修复」） | §6 第 2 条（删修复经过叙述） |
| 65 | --sheet 用 select 按帧号取第 6/21 帧，36 帧铺 6×6；别改回 fps=1 或 -ss+fps（§6「已修复」） | §6 第 3 条 |
| 66 | flip 截 25/75%；默认串 wipe 不需特殊照顾（§6） | §6 第 4 条 |
| 67 | 自检 5 项（§7） | §7（原样） |
| 68 | 修辞表路由动作；live 每个名字要能在本表或 components.md#fxkit 指到（修辞动作） | 修辞动作节首段 |
| 69 | 修辞表 19 行首选 / 备选（修辞动作） | 修辞动作表（19 行全留，备选条件保留） |
| 70 | 修辞表"何时别用"列（与 §5.1 重复） | 并入 §5.1 对应件的行（见 #54）；表首段注明去 §5.1 看 |
| 71 | 两条纪律：加 = 换；落在擅长的动作上才算数（修辞动作） | 表后（原样） |
| — | 非规则内容：状态"生效"标注、"34 个库里 32 个引用数为 0""23 件从未出现…21 件已登记""排查了很久""38 秒处接缝""用户会明确感到…""旧版这一节写的是只记录未修"等实测故事与历史；"←此前没有/零覆盖"注 | **删**（历史叙述，按维护纪律写进 CHANGELOG / 本文件，不留在指令文档） |

核对方式：压缩前全文存档在 git（`git show 758ed6f:references/media.md`）；`validate-skill`（文档里点名的组件必须在源码里存在）与 `check-links.py` 通过。

---

## 维护纪律

- **版本号只写在 `manifest.json`**。SKILL.md、README、模板 package.json 不写版本号；发版时只改 manifest 并在 CHANGELOG 加一节（每条一行）。
- **指令文档只写「现在怎么做」**：SKILL.md 与 `references/` 里不写版本史、事故复述、评审过程（`validate-skill` 的 `check_process_words` 会拦「踩过 / 事故 / 上一版」和内部版本号）。这些写进 CHANGELOG 或本文件。
- **门禁分级**：一次事故只进 P1，同类问题复现 ≥2 次才升 P0。形式性要求（候选个数、是否搜过、开场写法）记 P1；客观测量（出界、重叠、字幕超长、静音、主题物缺失、像素实测）才是 P0。
- **改文档时每条规则都要有落位**：删、并、挪之前对照上面的表，写清新位置。
- **发布包**：`python scripts/package-skill.py`（或 `git archive`，按 `.gitattributes` 的 export-ignore 剔除开发期文件）。`scripts/dev/`、`tests/`、`docs/`、本文件不进包。
- **测试默认离线**：`python3 -m unittest discover -s tests -p 'test_*.py'`；设 `NV_ONLINE=1` 才跑要下载字体的首跑用例。
- **跨语言常量只写一次**：FPS、字幕单行上限、读速、行高地板、标签字号地板、卷页帧数、舞台中心、相机缩放上限与运镜时长、文字展开时长参数都在 `assets/lecture-template/src/contract.json`。TS 用 `import CONTRACT from './contract.json'`，Python 用 `from contract import C`（`scripts/contract.py`），`scripts/transition-plan.mjs` 用 `fs` 读。新增一个两边都要用的数，加进这份 JSON，不要在两边各写一遍再加正则核对。语义不同但数值相同的（如字幕逐字计的 16 和 G-2 加权字计的 16）只共用数值，计法函数各自保留。
