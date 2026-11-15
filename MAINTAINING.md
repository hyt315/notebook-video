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

{{SKILL_TABLE}}

---
