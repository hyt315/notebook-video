# 维护者手册（MAINTAINING）

> **仅维护者阅读；做片子请回到 [SKILL.md](SKILL.md)。** 本文件不进发布包（`.gitattributes` export-ignore）。
> 这里放文档结构、合并对照表、维护纪律等维护期内容。原计划移到这里的 remotion-architecture / dependency-policy / official-skills-exemplar
> 里有 agent 也要守的规则（依赖边界、时长延长不变式、模板驳回条件），所以留在发布文档 `references/technique.md`、`references/scenes.md`。

## 文档结构与合并对照（第 1 批 #9）

面向 agent 的文档（发布）：`SKILL.md`（入口路由）+ `references/` 9 篇 + `references/themes/` 6 篇 + `references/MOVED.md`（旧名索引）。
面向维护者（不发布）：本文件、`CHANGELOG.md` 的旧档 `docs/history/CHANGELOG-legacy.md`、`scripts/dev/`、`tests/`。

合并方式：每篇旧文档**整篇**搬进新文件的一节（节前 `<a id="旧文件名"></a>`，标题降一级），所以旧文档里的每条规则都原样在新位置；
全仓库 `.md/.py/.mjs/.cjs/.json` 里指向旧文件的链接、路径、错误提示一律改成 `新文件#旧文件名`。
例外：模板 `.ts/.tsx` 的注释（第 1 批不碰 .ts/.tsx），读者按 `references/MOVED.md` 换算；第 2 批改 .tsx 时顺手更新。

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

## 维护纪律

- **版本号只写在 `manifest.json`**。SKILL.md、README、模板 package.json 不写版本号；发版时只改 manifest 并在 CHANGELOG 加一节（每条一行）。
- **指令文档只写「现在怎么做」**：SKILL.md 与 `references/` 里不写版本史、事故复述、评审过程（`validate-skill` 的 `check_process_words` 会拦「踩过 / 事故 / 上一版」和内部版本号）。这些写进 CHANGELOG 或本文件。
- **门禁分级**：一次事故只进 P1，同类问题复现 ≥2 次才升 P0。形式性要求（候选个数、是否搜过、开场写法）记 P1；客观测量（出界、重叠、字幕超长、静音、主题物缺失、像素实测）才是 P0。
- **改文档时每条规则都要有落位**：删、并、挪之前对照上面的表，写清新位置。
- **发布包**：`python scripts/package-skill.py`（或 `git archive`，按 `.gitattributes` 的 export-ignore 剔除开发期文件）。`scripts/dev/`、`tests/`、`docs/`、本文件不进包。
- **测试默认离线**：`python3 -m unittest discover -s tests -p 'test_*.py'`；设 `NV_ONLINE=1` 才跑要下载字体的首跑用例。
- **跨语言常量只写一次**：FPS、字幕单行上限、读速、行高地板、标签字号地板、卷页帧数、舞台中心、相机缩放上限与运镜时长、文字展开时长参数都在 `assets/lecture-template/src/contract.json`。TS 用 `import CONTRACT from './contract.json'`，Python 用 `from contract import C`（`scripts/contract.py`），`scripts/transition-plan.mjs` 用 `fs` 读。新增一个两边都要用的数，加进这份 JSON，不要在两边各写一遍再加正则核对。语义不同但数值相同的（如字幕逐字计的 16 和 G-2 加权字计的 16）只共用数值，计法函数各自保留。
