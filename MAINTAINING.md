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
`checks.md` 里 composition-gate / presentation-gate 的实现口径与事故记录可迁到本文件，只留「每类报错怎么修」。（第 3 批已做，见「checks.md 压缩对照」。）

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

`references/locked-style-contract.json` 只留描述性字段（调色、字体、章节卡、字幕区等，给手写场景查）；与 `src/contract.json` 重复的数值已删，数值只以 `contract.json` 为准。没有代码读它。
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

## checks.md 压缩对照（第 3 批）

`references/checks.md` 由 69,427 字节压到约 44,100 字节（802 → 467 行）。做法同 media-routing：同一条规则只留一处，删历史叙述与修复经过；门禁的**实测记录与实现口径**迁到下面「门禁实测记录」，不删。四个外部锚点（`quality-checklist` / `official-aesthetic-system` / `composition-gate` / `presentation-gate`）与被代码注释引用的小节号（§5.2、§6、§6.1、§G-1、§G-15、「P0-4 降级说明」「还没做的」）保持不变。下表逐条列出压缩前的规则与它现在的位置。

| # | 压缩前的规则（原小节） | 现在在哪 |
|---|---|---|
| 1 | Story 6 条：1.5s payoff / 8s open loop / 一景一意一动作 / 无旁白可懂 / 先 payoff 后背景 + 证据回扣 / 2–4s 状态变化 / 结尾 ≥1s（Story） | Story 3 条（同义条合并，「1.5s」与「先于背景」并为一条） |
| 2 | Architecture 5 条（Remotion 主渲染、TTS 一次转整帧、同一 FPS、首帧前资源就绪、音效随可见动作声明） | Architecture 3 条（原句合并） |
| 3 | 背景/章节/页眉/字幕与标准样例一致（Visuals） | Visuals 第 1 条 |
| 4 | 每景一个 media kind；`image-text` 只在用户/Commons/授权图片时（Visuals） | Visuals 第 2 条（原样） |
| 5 | 图片 6 条：有助理解才用原创/提供/授权图、图里不烘字、visual-assets.json 登记、识别-标注-关系-结论同步、只允许克制的裁切/推近、标注独立运动（Visuals） | Visuals「Images」一条（6 句全留；"Generated imagery/images" 改为 "Imagery/Images"，与第 1 批「技能不调用生图模型」一致） |
| 6 | 物件 5 条：独立运动即独立组件、一个 home/destination 区、无关卡片间距 ≥70px 含阴影、中央走廊至多一个临时传送物、连续过程保留同一任务物、浮物在底座之上（Visuals） | Visuals「Objects」一条 |
| 7 | 槽与离场 3 条：越过后才遮挡、插件完全没入前唇、临时件完全离场（Visuals） | Visuals「Slots and exits」一条 |
| 8 | 阴影 2 条：只在纸抬起时变化、用锁定的 lift-linked 配方（Visuals） | Visuals「Shadows」一条 |
| 9 | 官方引擎 4 条：锁定字号阶、不用系统字形/emoji、静态克制调色、普通编辑只在 COPY 等表面内（Visuals） | Visuals「In the official engine」一条（编辑面改为链到 #ordinary-editable-surface，那里是同一张清单） |
| 10 | 数据虚线只在真实传送时按正确方向动；带字纸面四边留白（Visuals） | Visuals 同一条 |
| 11 | 保留中文原文与真实品牌素材；无错字标签/假 logo/软化汉字（Visuals） | Visuals 同一条 |
| 12 | 无讲解中大空白；无杂点碎屑蒸汽；无效果堆/迷你卡堆/半可见层；无全局缩放/抖动/噪点/色调分离/整屏翻页（Visuals 4 条） | Visuals 同一条 |
| 13 | 运镜闭集 + anchor + validate-shot-motion P0=0 + 文字镜缩放 ≤1.35 + 章节运镜配额 + 全片 ≥3 种 intent（Visuals） | Visuals「Shot camera」（原样） |
| 14 | 骨架 ≥3 种、相邻不同（Visuals） | Visuals「Scene skeletons」（原样） |
| 15 | 介质 ≥3、讲解景至少一个活性组件、纯卡片堆拒绝（Visuals） | Visuals「Visual media」（原样） |
| 16 | 每景 3–5 区、填满下 1/4（Visuals） | Visuals「Density」（原样） |
| 17 | 背景装饰区内容放 CoverPanel、位图不动（Visuals） | Visuals「Background readability」（原样） |
| 18 | OverlapGate 零警告、有意覆盖标 data-gate-allow、不许用白名单藏碰撞（Visuals） | Visuals「Runtime overlap gate」（原样） |
| 19 | SlotGuard：槽高给满、目标 ≥60%、<35% 出声、宽度自己算（Visuals） | Visuals「Main-slot fill gate」（11% 实测并入括号） |
| 20 | Motion：scaleX 不用 width、tabular-nums、多属性入场不同时钟（Visuals） | Visuals「Motion」（原样） |
| 21 | Anti-PPT 活性组件清单；不要把不可达的名字写成硬要求（Visuals + 历史注） | Visuals「Anti-PPT」（规则留；六件已删组件的历史注删去，见末行） |
| 22 | Subtitle 11 条（纯字幕、无边框/侧标/定位器、一行居中 44px、CaptionFitGate、半显不横移、尾标点剥除、semantic 分段、保护短语清单、不跨 cue、对齐 TTS 词流、领先 ≤80ms） | Subtitle 7 条（11 条全留，同类合并） |
| 23 | Audio 6 条 | Audio 3 条（两两合并） |
| 24 | File validation 10 条 + 「设计提案不更新技能，用户认可成片后才更新」 | File validation 5 条 + 原句 |
| 25 | Deliverables 10 项 + 事实卡 + 「不要停在提示词/静帧/无声动画/未验证渲染」 | Deliverables（原样，标题去掉「原文迁自 SKILL.md」） |
| 26 | 美学系统定义：flat/cel 两锁定皮肤、一个模板、3.2.0 删 classic（Official aesthetic system） | 节首一段 |
| 27 | Locked production grammar 两段（含「必须仅靠原生 SVG 可构建」） | 原样 |
| 28 | Locked aesthetic core 6 项 + 语义色只来自 C 等约束 | 原样 |
| 29 | Ordinary editable surface 8 项 + 语义 ID 与显示文字分离 | 原样（第 6 项 "generated or supplied" → "supplied"，理由同 #5） |
| 30 | Visual rules 14 条 | Visual rules 9 条（同主题合并；"generated bitmaps" → "bitmaps"） |
| 31 | Future updates：一次性副本 → 整片渲染 → 用户认可 → 再覆盖模板 | Locked official elements 节首（与「用户看成片并认可前不写入技能」合在一处） |
| 32 | Locked official elements 25 项 | 22 项（30fps / 画布 / 不重复帧 / 60fps 合为一项；两条字幕项合为一项；"optional generated imagery" → "optional imagery"） |
| 33 | 构图门禁为什么要有：没有会拒绝 PPT 的门禁条款会退化；规则少而硬（§1） | §1（统计数字与历史删去） |
| 34 | P0-1…P0-7 判据（§2） | §2 P0 表（原样；P0-4 的降级日期改为指向降级说明） |
| 35 | P1-7…P1-10 判据（§2） | §2 P1 表（原样） |
| 36 | 「十一项」数法 + 旧锚点说明（§2 引用块） | §2 首句（数法留，旧锚点故事删） |
| 37 | P0-4 降级：声明只查存在、真实判据在 FillGate；「声明只能查写没写」（§2 引用块） | §2「P0-4 降级说明」 |
| 38 | 横向空洞：四个数、只报不拦、合并落盘带 at（§2） | §2「横向空洞」列表 |
| 39 | 横向口径表 4 行（最完整帧 / 条状豁免 / 组合豁免 / 阈值） | §2 口径表（原样，"为什么"列压短） |
| 40 | 只有 render 与 sweep 落盘，窗口渲染只打印（§2 基线） | §2「横向空洞」列表 |
| 41 | sweep 每镜量一遍、少一镜明写未量到（§2 堵上的坑） | §2「横向空洞」列表 |
| 42 | 镜头开头空着正常、不要提前摆（§2 可复用写法） | §2 口径表后 |
| 43 | 四个装置表 + 「拿掉这一层主体还完整吗」判据（§2） | §2 装置表（原样） |
| 44 | 不该做 3 条（§2） | §2「不该做」一段 |
| 45 | 怎么跑、退出码、NV_GATE_JSON、纯标准库只读（§3） | §3（原样） |
| 46 | 失败修法表 7 行 + 不要把门禁改松（§4） | §4（原样） |
| 47 | 修复顺序：先组件级再场景坐标 + 四类组件级根因与修法（§4.6） | §4 表后「修复顺序」（根因写成形态+修法，删"本版实测"数字） |
| 48 | 门禁分工表 9 行 + 分工原则（§5） | §5（CardFitGate「抓到 4 处」与 OverlapGate「3 类」实测数删；CanvasBoundsGate 一格压短） |
| 49 | CanvasBoundsGate 判据：文字叶墨迹、Range 并集、≥6 出声、落定态且 ≥20 硬拦（§5.2） | §5.2「判据」 |
| 50 | 会裁切的祖先 / 铺满视口不算裁切（§5.2） | §5.2 列表 |
| 51 | 输出像素口径、不做设计坐标回折（§5.2 + 砍掉表第 1 行） | §5.2 列表 |
| 52 | 不判纯图形装饰块（已知空白）、不与 ClippingGate 重复报、SVG 文字两道各报是两件事（§5.2 砍掉表 + 重复报一段） | §5.2「不查」 |
| 53 | 每帧量、整片耗时未实测（砍掉表第 4 行） | §5.2 列表 |
| 54 | 相机不计入、会误报（§5.2） | §5.2 列表 |
| 55 | 何时会响：block/warn 档、覆盖率日志、扫过 0 个当异常（§5.2） | §5.2「档位」 |
| 56 | 怎么修 4 步（§5.2） | §5.2「怎么修」（例子保留口径，删事故叙述） |
| 57 | Grid5：一页 5 件用自己的格子表（§5.2 真实命中） | §5.2 怎么修第 4 步 |
| 58 | 负向夹具 AB0–AB4；渲染夹具建在交付工程外（§5.2） | §5.2「负向夹具」 |
| 59 | 交付门槛 7 条（§6） | §6（原样，理由压短） |
| 60 | 色彩契约：缺口、判据、只认一个组合的三条论证、只挂交付门（§6.1） | §6.1（原样压短） |
| 61 | 14 道门禁数法 + 本道查什么 + 纯算术（呈现门禁节首） | 节首（"第 10 道"的历史删） |
| 62 | 运行命令、退出码 | 原样 |
| 63 | G-1 断言表 6 行 | 原样 |
| 64 | G-1：上下界缺一不可、8 帧是承重墙、换配音必须重跑、修数据不调容差（引用块） | G-1 表后列表 |
| 65 | G-1 与调研报告 6 帧形式的差异 + 文献依据 | G-1 表后列表末条 |
| 66 | G-2 表 + 数据来源 | 原样 |
| 67 | G-3 表 8 行 | 原样（MIN_LABEL_FONT 出处更正为 contract.json，data.tsx 导出） |
| 68 | 强调色当文字色的 ①②③ 处置 | G-3「强调色当文字色时」 |
| 69 | 对比度能力边界（硬编码 / 改名 / 渐变 / SVG fill 读不到；FocusGate 未做） | G-3「能力边界」 |
| 70 | 扫描口径：只扫值位置、注释与字符串抹空格、两侧边界 | G-3「扫描口径」 |
| 71 | 配对必须是声明的契约，五类（假阳性引用块） | G-3「配对是声明的契约」 |
| 72 | G-14/15/16 字段与判据出处 | 原样 |
| 73 | G-15 现口径（JSX 用法、noncode、P0）+ 不做三件与代价 + 宁可少报 | G-15 段 |
| 74 | 编号规则：不叫 G-6，新门禁往后排 | 「编号」段 |
| 75 | G-5 代理判据与差距 | 原样 |
| 76 | 每条判据要有夹具 + 阴性对照；must_block 子串（二） | 二节首段 |
| 77 | 夹具表 17 行（I…AK） | 二节表（"门禁实际报的"逐字输出改为"期望"摘要；逐字输出以 `negative-gate-check.py` 为准） |
| 78 | X/Y 是新增判据的夹具、Y 兼自检；AC–AE 口径；AF–AK 语义；I 必须用 S1（四个引用块） | 并入表内对应行（AC 行写 G-14② 口径、AE 行写打断计数、AG 行写语义、I 行写为什么用 S1） |
| 79 | 已知真实缺陷：白字在彩色填充上不足，留给用户（三） | 三（原样压短） |
| 80 | 还没做的（四） | 四（加上 G-3 FocusGate 一行，原文在 G-3 引用块里） |
| — | 非规则内容：「状态：生效」标注；34 库组件 32 个零引用、9 个脚本没一条能发现；「八项/十项」数错故事；六件已删组件历史注；FillGate 第一版取第一帧的错口径经过；cell 8 镜基线数字；preview 只覆盖前六镜的坑；CanvasBoundsGate 第 ⑥ / ③ 页事故、v1/v2 对照、文件行数、参考简版差异、v2 实测表、与 ClippingGate 实测对照；色彩契约正反实跑输出；G-1 第一版 PASS 漏洞与 demo 余量；对比度两版假阳性经过；G-15 旧 465 行实现与 overview-film S2；Ink 处置日期与 orangeDeep 4.19:1；夹具逐字输出 | 实测数据与实现口径迁到下面「门禁实测记录」；纯历史叙述**删**（按维护纪律不留在指令文档） |

核对方式：压缩前全文在 git（`git show 65cd8ab:references/checks.md`）；`check-links.py`、`validate-skill`、`selftest` 通过。

### 门禁实测记录（自 checks.md 迁出）

- **横向空洞基线**（cell 全片 8 镜，修正口径后，`sweep` 量）：S1 28/1/0.16/0.44 · S2 23/1/0.26/0.43 · S3 19/1/0.08/0.32 · S4 32/0/0.29/0.82 · S5 27/0/0.03/0.84（条状豁免）· S6 28/0/0.14/0.36 · S7 24/0/0.02/0.37（组合豁免）· S8 28/0/0.15/0.43（cells/blank/largest/widest）。sweep 取「切点前最近的 15 倍数帧」，与整片渲染「整镜取最完整帧」差 2–3 格，判定不变。第一版取第一帧时六镜全判空洞（假阳性）。
- **CanvasBoundsGate v2**（2026-09-22）：468 → 231 行。与仓库外参考简版的有意差异：参考版代码「任何 >6px 即硬拦」，本仓取「落定态且 ≥20」。v2 砍掉 v1 的设计坐标回折、图形/版面件分支、三条排除规则（z≥140 chrome、≥92% 底托、小取景框）、按帧抽样——两种口径在接触表上抓到同一批真缺陷。实测：接触表 6 页 rc=0 零报告（扫过 27/25/20/74 个文字叶）；第 ⑥ 页改回 `Corridor x={100} w={1720}` → rc=1 无图，两处 26px；第 ③ 页改回 `Grid4` → rc=1，27px；片子帧 300/900 warn 下零报告。与 `ClippingGate` 同挂：帧 150 只有 CanvasBoundsGate 报，帧 395 只有 ClippingGate 报（path 超出 svg 视口）。修 `Grid5` 后接触表 17 页只有第 ③ 页像素变化。
- **色彩契约正反对照**：老片 `pc/bt470bg/unknown/unknown`（yuvj420p）→ rc=1；新渲片段（render-range 300–599，2560×1440）→ rc=0，`-17.1 LUFS, -3.8 dBTP`。
- **G-1**：第一版只有③时 `{cue:0, offset:200}` 实测 PASS（③b 补它）；demo 上 S8/cue14 只剩 2 帧、S7/cue13 5 帧（修数据前）。
- **G-3**：第一版 `white × paper` 全交叉 → 假 P0；第二版按 `background:` 推断又请回来——所以配对写死为五类。Ink 机制落地后 `flat: orangeDeep`（4.19:1）P1 消失。绕过实测：硬编码 `#dcdcdc` on `#faf7f2` = 1.28:1 rc=0。
- **G-15**：旧实现 465 行（JSX 遍历 + 本镜切片 + 帧驱动白名单 + 降级），与现口径抓到同一批真缺陷；overview-film S2（`MetricGrid` 只在注释留名）现口径仍抓得住（夹具 AJ）。删掉的夹具 AH/AI（帧驱动 vs 静态）、AL（降级）。
- **负向夹具 I**：第一版给 S2 的 cue4 加负 offset，该 cue 帧号等于镜起点，永远先撞①，测不到③。

---

## 维护纪律

- **版本号只写在 `manifest.json`**。SKILL.md、README、模板 package.json 不写版本号；发版时只改 manifest 并在 CHANGELOG 加一节（每条一行）。
- **指令文档只写「现在怎么做」**：SKILL.md 与 `references/` 里不写版本史、事故复述、评审过程（`validate-skill` 的 `check_process_words` 会拦「踩过 / 事故 / 上一版」和内部版本号）。这些写进 CHANGELOG 或本文件。
- **门禁分级**：一次事故只进 P1，同类问题复现 ≥2 次才升 P0。形式性要求（候选个数、是否搜过、开场写法）记 P1；客观测量（出界、重叠、字幕超长、静音、主题物缺失、像素实测）才是 P0。
- **改文档时每条规则都要有落位**：删、并、挪之前对照上面的表，写清新位置。
- **发布包**：`python scripts/package-skill.py`（或 `git archive`，按 `.gitattributes` 的 export-ignore 剔除开发期文件）。`scripts/dev/`、`tests/`、`docs/`、本文件不进包。
- **测试默认离线**：`python3 -m unittest discover -s tests -p 'test_*.py'`；设 `NV_ONLINE=1` 才跑要下载字体的首跑用例。
- **一条命令跑全部检查**：`python3 scripts/dev/test-all.py`（单测 → 用例收集 → selftest → 负向抽查 → validate-skill → 链接 → `reuse lint`（装了才跑）→ tsc + test_frame_types（设了 `NV_E2E_NODE_MODULES` 才跑，在模板副本里软链依赖，不往模板里放 `node_modules`））。`--list` 看步骤名，可以只跑其中几步。单测步骤不把 `NV_E2E_NODE_MODULES` 传下去（它会打开渲染型 e2e），要渲染型 e2e 加 `--e2e`。
- **回归集**：`tests/test_regress.py` 把 `examples/**/*.story.json`（现 16 份）逐份 compose → resolve → shot-motion / presentation 门禁，产物 sha256 与门禁 P0/P1 条数钉在 `tests/fixtures/regress.json`。有意改了排版 / 字幕 / 相机 / 判据时 `NV_REGRESS_UPDATE=1 python3 -m unittest tests/test_regress.py` 重写，并在提交说明里写清哪些 story 变了。
- **组件使用率**：`python3 scripts/dev/component-usage.py`（`--unused` 只列蓝图 / 示例 / 模板场景里零引用的件，`--json` 给数据）。按「零引用即待删」纪律核对时用它，不要凭印象。组件清单从代码 export 读，`docs` 栏为 0 表示 references/ 里没写这件。
- **跨语言常量只写一次**：FPS、字幕单行上限、读速、行高地板、标签字号地板、卷页帧数、舞台中心、相机缩放上限与运镜时长、micro-orbit 环绕角（ORBIT_ROT，shotkit 默认值 = 门禁上限）、文字展开时长参数都在 `assets/lecture-template/src/contract.json`。TS 用 `import CONTRACT from './contract.json'`，Python 用 `from contract import C`（`scripts/contract.py`），`scripts/transition-plan.mjs` 用 `fs` 读。新增一个两边都要用的数，加进这份 JSON，不要在两边各写一遍再加正则核对。语义不同但数值相同的（如字幕逐字计的 16 和 G-2 加权字计的 16）只共用数值，计法函数各自保留。
- **素材许可两处登记**：`REUSE.toml`（+ `LICENSES/`，开发期 `reuse lint`，不进包）记每个文件的版权与许可；运行期仍读 `manifests/backgrounds.json`、`public/sfx/sfx-manifest.json`、`public/craft/craft-manifest.json`。加或换素材时两边一起改，`tests/test_reuse.py` 核对两边一致、且 `public/` 与 `assets/fonts/` 下每个二进制素材都有显式登记。本机检查：`pip install reuse==6.3.0`（GPL-3.0，装在仓库外的虚拟环境）后 `reuse lint`。
