# Changelog

All notable changes are recorded here. The project follows semantic versioning.

本文件的每个条目为**中英双文**（中文在上、English 在下），条目按版本倒序排列。

## [3.1.2] - 2026-09-22

> 对照基线 `v3.1.1`：**35 个文件，+1 020 行，−145 行**。

### 背景与动机

本版是 v3.1.1 之后的第二批补丁，仍属 v3.1.0 大版本优化的收口。主线是**门禁有效性**：对全部 `validate-*.py` 做了一次整体审计，并把交接文档 15 条待办逐项核到底（含字幕 #2、接触表 #3/#5、双真源 #7、口径 #9）。验收口径只有一条：**改前先复现、改后实证转绿**，并以真渲染回归——"读代码以为修好了"在本版被实测推翻过三次，因此全部结论都带运行证据。

### 新增

- 接触表 17 页 → **18 页**：⑱ 页 `FocusFx` 整页专属（`position:fixed` 锚点不能进格子），dim/spot/loupe/marker 四态按帧轮转；⑪ 页转场 durations 压回页内（4×12−3×6=30，三个转场全在页内）；JPG 抽样从"每页首帧"改为**每页第 6 / 21 帧**（select 滤镜、6×6=36 格），转场中态第一次在接触表上可见。`assets/demo/` 接触表按新母版真渲染重出（18.0 s / 2560×1440 / 540 帧 / 静音 AAC / bt709）。
- `validate-skill-consistency.py` 三条交叉校验：**转场/骨架集合**（模板 ⇄ 门禁判据）、**画布数值对**（`canvas.ts` ⇄ `validate-visual-plan.py`，designW/H、字幕安全宽、边距、底距）、**数值双真源配对表**（字号地板、舞台中心三写、变焦上限、运镜时长区间与默认、FPS，共 14 对）。任一侧锚点解析不到即报错——防"换个写法就静默放行"；语义不同款的数值**明确拒收**并注释存档。
- `negative-gate-check.py`：40 例 / 80 断言 → **65 例 / 112 断言**（`python -O` 档同绿）。此前**零对抗夹具**的四道门禁（layering / visual-plan / audio-levels / official-example）各补定向 needle 的 must_block + must_pass 阴性对照；本版全部新硬拦行为都有夹具钉住。

### 修复（静默路径收口）

- `validate-audio-levels.py`：ffmpeg 不可用 / 读不到峰值，从「记 P1 → rc=0」改为 **rc=2 门禁自身故障**——此前该门在无 ffmpeg 的环境里从未真正跑成过。
- `validate-composition.py`：场景源码改**递归扫描**（场景放子目录时整段判据曾被静默跳过）；新增「场景源码不可读，判据无法执行」逐镜覆盖率 P0；场景函数声明形态放宽至 `React.FC<` / 裸 `FC<` / `function` / `JSX.Element`（收紧形态对合法写法 8/8 镜误报，实测复现后修复并钉夹具）。
- `validate-presentation.py`：resolved 与 declared **镜数不一致（双向）报 P0** 并注明疑未重跑 `resolve-shots`——陈旧时间轴不再空转 exit 0。
- `notebook-video.mjs`（CLI）：交付链 `validate-semantic-breaks` **自动探测**工程 `node_modules/budoux` 并恒带 `--require-budoux`——缺依赖从「响亮跳过」变为硬失败；`--no-budoux` 保留为刻意跳过开关。CI 中 `npm ci` 之前的裸跑步骤改直调 `.py`，维持"跳过并告警"语义，避免收口后假红。
- `validate-caption-sync.py`：新增 caption-cues **双份字节相等锁**（`manifests/` 校验份 ⇄ `src/` 渲染份），堵住"校验一份、渲染另一份"。
- `match-timing.py`：6 条防护性 `assert` 全改 `raise SystemExit`——`python -O` 会把 assert 连判断一起剥离，防护当场静默失效。
- `validate-visual-plan.py`：影片 `<Composition>` 抽不到数字宽从「静默当通过」改为报**判据无法执行**；判据锚定 `id="NotebookVideoFilm"`（实测旧版会抓接触表 composition 的 1920 当影片画布宽比对并静默 PASS）。
- `coords-lint.py`：负整数字面量进入识别（此前对 linter 完全隐形）；负向阈值**刻意暂不设**——全仓扫描证实存在合法负坐标（chart 的 SVG 局部坐标、sticker 出血 Tape、Callout 骑跨上沿），证据与补判据前提写入注释。
- **相机数学三写合一**：`validate-shot-motion.py` 删手写展开分支（−28 行），importlib 复用 `resolve-shots.py` 的 `expand_cam` 作唯一展开真源；`expand_cam` 与 `shotkit.tsx` 的隐式默认逐条对齐（establish 1.03 / push-in 1.12 / reveal 1.08 / pull-back 先 1.12 后 1.0 / micro-orbit 默认 6° / still 尾帧按 `to`）——关闭 micro-orbit 省 rotY「门禁记 0°、成片真转 6°」的漏放，与「省参数=零运动」的误拦链。模板 8 镜（全显式参数）展开输出**逐字节不变**，兼容性实测。

### 文档（口径修正）

- 背景图尺寸：实测 **16:9 三张确与画布逐像素**；4:3 为 2240×1680、3:4 为 1680×2240（画布 7/6 超采样，渲染均匀降采样、不裁切不拉伸）。三份主题契约、三套皮肤代码注释、`visual-assets.json` 的 `crop_policy` 按实测改口径；`sticker` 补入位图背景皮肤清单（此前漏记，paper 为纯代码绘制）。
- 相机历史数字：「10 个关键帧越界」改写为双口径——**10 是 s 超旧上限 1.018（16:9 空间口径），真正可见窗出画的是 8 个关键帧、最大 383px**（按 v2.8.0 源码复算，逐帧非零露底约 862–892 帧随亚像素容差），并注明 `CAM_KEYS_P` / `CameraRig` 已随 **v2.9.0** 删除（`visual-system.md` 此前误写"v3.1 起"）。
- 字幕：澄清「跨 cue 判据其实一直存在」（validator 对整句拼接跑 BudouX），真实缺口是「缺模型时降级放行」——已随交付路径收口；相关命令示例同步实装行为。

### 已知边界（知情接受，非缺陷）

- TS `shotkit.tsx` 的 micro-orbit 末 hold 帧不带 rotY（会回摆 0°），resolved 数据侧保留——差异已注释钉明；改行为会动已渲片输出，待拍板。
- 「交付必须走 CLI」不做机器强制（裸调 `.py` 的夹具语义与交付语义混在文档，加检查引出的约定比收益重），靠 SKILL.md 命令示例统一兜住。
- coords-lint 的「两画布并集」阈值属锁定画布口径，不动。
- 模板 ⇄ 工程两份副本仍按 `dependency-policy.md` §九人工同步，无机器检查（前轮已定"不为此加门禁"）。

### 测试

`negative-gate-check` 65 例 / 112 断言全 PASS（含 `python -O` 档）；`validate-skill-consistency`、`validate-official-example`、`selftest` 11/11 全绿；模板 `tsc --noEmit` 0 错；模板新建工程**真渲染** `render-range` 61 帧 rc=0（2560×1440@30）。

---

## [3.1.2] - 2026-09-22 (English)

> Baseline `v3.1.1`: **35 files, +1,020 / −145 lines**.

### Motivation

The second patch round after v3.1.1, still closing out the v3.1.0 overhaul. The theme is **gate effectiveness**: a full audit of every `validate-*.py` gate plus a line-by-line verification of the 15 open backlog items. One acceptance rule: **reproduce the defect first, prove it green after the fix, regress with a real render** — code-only review was falsified by experiment three times this round, so every claim below carries runtime evidence.

### Added

- Showcase grows to **18 pages**: page ⑱ gives `FocusFx` a dedicated full page (its `position: fixed` anchor cannot live in a tile), cycling dim/spot/loupe/marker by frame; page ⑪ transitions now fit inside the page (4×12−3×6=30, all three mid-transition states on-page); JPG sampling moves from "first frame per page" to **frames 6 and 21 of each page** (select filter, 6×6=36 cells) — transition mid-states are visible on the sheet for the first time. `assets/demo/` showcase re-rendered from the new master (18.0 s / 2560×1440 / 540 frames, silent AAC, bt709).
- Three cross-checks in `validate-skill-consistency.py`: transition/skeleton **enum pairs** (template ⇄ gate), canvas **numeric pairs** (`canvas.ts` ⇄ `validate-visual-plan.py`: design W/H, subtitle safe width, margins, bottom), and a declarative **numeric dual-source table** (font floor, stage center written thrice, zoom caps, camera-move durations, FPS — 14 pairs). An unparseable anchor on either side is itself an error — "reformat the code and the check silently dies" is not allowed; numerals that merely look equal but mean different things were explicitly rejected, with reasons in comments.
- `negative-gate-check.py`: 40 cases / 80 assertions → **65 / 112** (also green under `python -O`). The four gates that previously had **zero adversarial fixtures** (layering / visual-plan / audio-levels / official-example) each got a needle-targeted must_block plus a must_pass negative control; every new hard-fail behavior shipped this round is pinned by a fixture.

### Fixed (silent-pass closures)

- `validate-audio-levels.py`: missing ffmpeg / unreadable peak now means **rc=2 gate failure** instead of "P1 note, exit 0" — on machines without ffmpeg this gate had literally never run.
- `validate-composition.py`: scene sources are scanned **recursively** (scenes in subdirectories used to silently skip a whole block of checks); per-shot coverage P0 when a shot's function body cannot be found; declaration matching widened to `React.FC<`, bare `FC<`, `function` and `JSX.Element` forms (the narrow form falsely blocked legal code 8/8 shots — reproduced, fixed, pinned).
- `validate-presentation.py`: resolved/declared shot-count mismatch (**either direction**) is now a P0 naming the likely missed `resolve-shots` run; stale timelines can no longer spin silently to exit 0.
- `notebook-video.mjs` (CLI): the delivery-path `validate-semantic-breaks` **auto-detects** the project's `node_modules/budoux` and always adds `--require-budoux` — a missing dependency is a hard failure, not a loud skip; `--no-budoux` stays as the deliberate opt-out. The CI step before `npm ci` calls the `.py` directly to keep loud-skip semantics and avoid a false red.
- `validate-caption-sync.py`: byte-equality lock between the **two caption-cues copies** (`manifests/` validated vs `src/` rendered), closing "validate one copy, ship the other".
- `match-timing.py`: six defensive `assert`s became `raise SystemExit` — `python -O` strips asserts and silently disarms the guards.
- `validate-visual-plan.py`: failing to parse the film composition's numeric width now reports "check cannot run" instead of returning `[]`; the check anchors `id="NotebookVideoFilm"` (experiment: the old first-match logic grabbed the showcase's 1920 and silently PASSed against the wrong canvas).
- `coords-lint.py`: negative integer literals are now recognized (they used to be invisible); a negative threshold is **deliberately withheld** — a repo-wide scan found legitimate negative coordinates (chart SVG-local values, sticker-bleed Tape, Callout straddling the top edge); evidence and preconditions recorded in comments.
- **Camera math consolidated to one source**: `validate-shot-motion.py` deletes its hand-written key expansion (−28 lines) and imports `expand_cam` from `resolve-shots.py`; `expand_cam` now mirrors `shotkit.tsx` implicit defaults one by one (establish 1.03 / push-in 1.12 / reveal 1.08 / pull-back 1.12→1.0 / micro-orbit default 6° / still tail follows `to`) — closing the micro-orbit miss ("gate sees 0°, film rotates 6°") and the false-block chain for omitted parameters. Template output for explicitly-parameterized shots is **byte-identical** (compatibility verified).

### Docs (measurements corrected)

- Background rasters: verified **16:9 files are pixel-exact with the canvas**; 4:3 files are 2240×1680 and 3:4 are 1680×2240 (exported at 7/6 supersampling; uniform downscale, no crop, no stretch). Three theme contracts, three theme code comments and `visual-assets.json` crop policies now match reality; `sticker` added to the fixed-raster skin list (previously omitted; `paper` is code-drawn).
- Camera history: "10 out-of-bounds keys" rewritten with both rulers — **10 counts `s` beyond the old 1.018 cap (16:9 space), while genuinely visible-window escapes are 8 keys, max 383 px** (recomputed from v2.8.0 sources; ~862–892 frames with tolerance-dependent nonzero bleed), noting `CAM_KEYS_P`/`CameraRig` were removed in **v2.9.0** (`visual-system.md` had said "since v3.1").
- Subtitles: clarified that a **cross-cue rule always existed** (the validator runs BudouX over the joined stream); the real gap was graceful degradation when the model is missing — now hard-failed on the delivery path; command examples updated accordingly.

### Known boundaries (accepted, not defects)

- TS `shotkit.tsx` micro-orbit's final hold frame omits rotY (swings back to 0°) while resolved data keeps it — difference pinned in comments; changing behavior would alter already-rendered films and awaits a decision.
- No machine gate forces "delivery via CLI" (fixture vs delivery semantics share the docs; the convention would cost more than it saves); SKILL.md command examples carry it.
- The coords-lint "union of two canvases" threshold belongs to the locked canvas contract and stays.
- Template ⇄ project copies remain manually synced per `dependency-policy.md` §九, per the earlier "no gate for this" decision.

### Testing

Full `negative-gate-check` 65/112 green (incl. `python -O`); `validate-skill-consistency`, `validate-official-example`, `selftest` 11/11; template `tsc --noEmit` 0 errors; a fresh project from this template **really rendered** `render-range` 61 frames, rc=0 (2560×1440@30).

## [3.1.1] - 2026-09-22

> 对照基线 `v3.1.0`：**50 个文件，+2 634 行，−330 行**。

### 背景与动机

本版是 v3.1.0 的补丁，不是新特性版本。改动集中在三件事，外加渲染链路的两个静默失败。

**一、补上「画布越界」这一类没有任何门禁覆盖的缺陷。** 接触表第 ⑥ 页第三站的标签块越出画布右缘被裁（文案「按 Flash 结算」渲成「按 Flash 结」），而当时四道渲染期门禁与构建期坐标检查一条都没响——这是结构性的：门禁全挂在 `FilmLayout` 里，接触表那条 composition 不经过它；而四道渲染期门禁各自只看图元被裁、卡片内溢出、文字互相压、下 1/4 铺到多低，构建期 `coords-lint.py` 又把 `Corridor` / `ZoomStage` / `StageFrame` 这类布局件排除在外。本版新增渲染期第 7 道门禁 `CanvasBoundsGate`。

**二、两条写在文档里、却从来没有门禁读过的叙事规则。** `references/narrative-moves.md` 一直写着「同一个 `move` 不得连续 ≥3 镜」，而 `validate-presentation.py` 此前只检查「每镜的 `move` 是不是 10 个名字之一」；`evidence` 一词的唯一检查是「字段非空」，写成根本不存在的组件名、或指向一张从头到尾不动的静态卡片，都照旧 PASS。两条都在本版落成判据。

**三、字幕断句从「按字数机械折行」换成 BudouX 短语边界。** 依据是一次真实事故：按 17 字机械折行把 `服务器` 切成 `传到服` / `务器。`，而中文 TTS 每字一个 word、切点「绑得上」，所以没有任何门禁看得见。

此外，渲染链路上有两个静默失败在本版修掉：Remotion CLI 的入口位置参数（一个不存在的 `--entry-point` 标志不报错、静默回落去渲另一个文件），以及交付文件的色彩元数据（`--color-space=bt709` 单独一条盖不住 `color_primaries` / `color_transfer`）。

### 新增

- **渲染期第 7 道门禁 `CanvasBoundsGate`（画布越界）—— 门禁总数 13 → 14**（`assets/lecture-template/src/canvas-bounds-gate.tsx`、`src/index.tsx`）。判据（v2）是**含文字的叶元素**（HTML 叶 + SVG `text` / `tspan`）的**墨迹矩形**（用 `Range` 取字）越出 composition 视口：≥6px 出声、**落定态**（有效不透明度 ≥0.98）越界 ≥20px 硬拦。
  - **挂载档位刻意不同**：片子取 `mode="warn"`、接触表取 `mode="block"`。接触表是「看见才会用」的唯一入口，目录页缺件就该中断渲染；片子那条的硬拦发生在交付渲染的最后一刻，判据一旦误报就等于「整片渲到最后一帧被打断、不出片」，而本版判据的实测来源全是接触表。两条档位的理由都写在件头注释与 `index.tsx` 里。
  - 件头注释同时写明 v2 相对 v1 砍掉的四件复杂度及每件的代价：不做设计坐标回折、不做图形 / 版面件分支、不养「铺底 / 底托 / z≥140 chrome 层」那套排除、不按帧抽样（改成每帧都量）。**已知空白如实写出**：一个越出画布、但一个文字都没有的装饰块，这条门禁抓不到。
  - 判定后 `blocked` 置位、异常**不被自家 catch 吞**（本仓库踩过两次「报了硬拦却照样出图 rc=0」）。
  - 门禁上线当天即抓到接触表自身的一处真实同类缺陷：第 ③ 页声明 5 件而 `Grid4` 只有 4 格，第 5 件（`FitTextBox`）被摆到 `top=1076`，整格落在 1080 高的画布**外面** 466px——那件组件在接触表上根本看不见。

- **负向夹具 28 → 40 例**（`scripts/negative-gate-check.py`）：新增 AB0–AB4（画布越界的接线、档位与判据收窄，5 条）、AC / AD / AE（`move` 连续段，3 条）与 AF / AG / AJ / AK（`evidence`，4 条）。`SKILL.md` 的负向抽查段落同步为 **40 例 / 80 条断言，其中 38 条是 needle**（钉住或禁止某条消息子串，「因别的原因失败」不算通过）。上一版的数字（23 → 28 例）保留在 `[3.1.0]` 一节里，不改。

- **`evidence` 从「只查非空」补成真门禁（G-15）**（`scripts/validate-presentation.py`）。按 v2 判：`evidence` 的名字必须作为 **JSX 用法**（`<名字 …>` / `<名字/>`）出现在该工程的**场景源码**里；只在注释 / 字符串 / import 行里出现**不算「用到」**——扫之前先用 `noncode()` 把注释与字符串抹成空格，再按 JSX 用法匹配；命中不了即 P0「找不到这个用法」。**已知边界如实标注**：不做**本镜**作用域，名字在本镜没用到、只在别的镜用了会漏（负向夹具 AG 把这一口径钉在明处，它必须放行）；也拦不住「指向本镜里从头到尾不动的静态卡片」。口径写回 `references/narrative-moves.md` §2 与 `references/presentation-gate.md`。

- **`move` 连续段判据（G-14②）** —— 按**成片镜序**逐镜扫极大连续段，同一 `move` 连续 ≥3 镜即 P0（`MOVE_RUN_LIMIT = 3`，即最多连续 2 镜）；缺 `move` 或非闭集 `move` 的镜打断计数，不接出跨越断点的假「连续」。口径与级别写回 `narrative-moves.md` §2。

- **接触表第 ③ 页新增 5 格表 `Grid5`**（`assets/lecture-template/src/showcase.tsx`）——3 列 × 2 行、格子 610×470、舞台等比 0.7；横向 3×610 + 2×25 间隙 + 2×20 边距 = 1920，纵向沿用 `Grid4` 的 76 / 576 两行。5 件全部落在画布内，17 页在 block 档下逐页抽帧跑过：每页 rc=0 且有图、无一处误报。

- **`SUPPORT.md`（新）** —— 提问去处（Discussions / Bug 模板 / Feature 模板 / 私有漏洞上报）、Bug 报告应带的信息（版本、系统与 Node、`ffmpeg -version`、确切命令、出错帧号、原样模板能否复现）、开 issue 前的三条自查、范围与响应说明（单人维护、无 SLA）。

- **`assets/lecture-template/src/external-types.d.ts`（新）与两个依赖** —— `GeoView` 现在画真陆地轮廓：数据来自 `world-atlas`（只用 `land-110m.json`，实测 55 KB / 130 条弧）、解码用 `topojson-client`（只用 `feature()` 一个函数）。类型是**本地声明**（不额外引入 `@types/topojson-client`）。`GeoView` 的经纬度标记由调用方手填，本技能不做地理编码、也不含城市或国界数据。

- **接触表的交付规格**（`scripts/notebook-video.mjs`）——`NotebookVideoShowcase` 的原生画布是 1920×1080，而交付文件是 2560×1440，因此渲染时按 4/3 放大（`--scale` 只吃十进制字面量，必须写 `1.3333333333333333`），随后补一条静音 AAC 音轨、再回写色彩四项。三段各自可单独重做，后两段失败时的报错都会说清「视频已经渲完了，不必重渲」。

- **CI 三步**（`.github/workflows/validate.yml`）——模板类型检查（`npm ci` + `npm run typecheck`，必须排在「断言仓库树里没有 node_modules」那一步之后）、模板 `package-lock.json` 纳入缓存、以及带 `--require-budoux` 的语义断句重跑（必须排在前面的 `npm ci` 之后）。

- **`references/windows-compatibility.md` 新增两节** —— 色彩契约为什么必须钉（分两步的理由与实测）与 `npx remotion` 挂死一例（低 CPU、零输出、无子进程）；`references/dependency-policy.md` 新增 §九「模板 → 工程同步清单」（本轮实测：模板的 `GeoView` 已有真陆地轮廓，而长片 `package.json` 里 `world-atlas` / `topojson-client` 是 0 处、`data.tsx` 也没有对应 import，所以长片仍是旧版经纬网）。

### 变更

- **版本串统一为 `3.1.1`** —— `SKILL.md` frontmatter、`manifest.json`（并补 `"license": "Apache-2.0"`）、接触表页脚（`COMPONENTS_VERSION` → `components-v3.1.1 · 27 件`）、`.github/repository-metadata.yml` 的 release tag / title。

- **封装层件数 29 → 27 件，逐件点算的地板 55 → 53 件**（`assets/lecture-template/src/components/index.ts`；53 = 本层 27 + 其余 8 个模块 26）。同步 `references/fxkit.md`、`references/media-routing.md`、`references/dependency-policy.md`、`references/locked-style-contract.json` 与 `scripts/validate-frame-props.py` 的注释。`SKILL.md` 的 `@remotion/*` 官方扩展口径同步为**五个**（去掉 `motion-blur`）。

- **组件权威索引收敛到一处** —— `references/media-routing.md` §5.1「组件权威索引」（53 件逐件：用途 / 何时用 / 何时别用 / 接触表第几页 / 真实使用记录，含未上接触表的件及其原因）。`fxkit.md` 与 `showcase.tsx` 只保留实现细节与接触表版面，不再各自维护组件清单——`SKILL.md` 明确写出别从接触表反推「有哪些件」。接触表的旧件口径同步收口：`SHOWCASE_VERSION` 原写「26 件旧件」，与实际渲染进接触表的 **18 件**不符（26 是旧模块对外 export 的件数），现统一为 18 件，并在 §6 写明两个口径的区别。

- **`FitTextBox` 真的接进画面（「加一件＝换掉一件」）** —— 模板 `scenes.tsx` S1 的 rail 面板正文块（固定内宽 348，原为手写 20px + 手写 `<br />`）改由「宽度 + 行数上限」反推字号（`maxFontSize` = 原设计字号、`maxLines` = 设计行数），文案变长时自动降字号而不是撑出面板。

- **字幕断句改用 BudouX 短语边界**（`scripts/build-semantic-captions.py`、`scripts/validate-semantic-breaks.py`）—— 合法断点 = BudouX 短语边界，或子句标点（`，。！？；：、…—` 及 ASCII 同义符）之后；**ASCII / 数字 token 内部不许断**；被迫移动的边界逐条打印。两个工具都按项目 `node_modules` 找 BudouX，找不到就**大声降级**（`WARNING: BudouX …` + `break_rule: mechanical-only (BudouX unavailable)`），不静默跳过；**交付路径上再加一道 `--require-budoux`：找不到模型直接 rc≠0**（「跳过」在退出码上看不出来）。`--warn-chars N` 是可选提示、**默认关**（出厂模板合法跑到 19 字，任何阈值都会有假警报）。依据与操作步骤写回 `references/subtitle-timing.md` 与 `references/tts-audio.md`（改为「写语义单元、让工具决定显示断点」）。**已知边界如实写出**：这道门禁覆盖的是「句内断行 + 保护短语」，跨 cue 的词组搭配没有判据。

- **交付文件的色彩契约**（`scripts/notebook-video.mjs`、两个模板的 `package.json`）—— 先 `--color-space=bt709`（自 `@remotion/renderer` 4.0.83 起会真的把像素转成 limited range），再在**复制流**上用 `h264_metadata` 位流过滤器回写四项元数据（FFmpeg 在 `-c:v copy` 上会忽略 `-colorspace/-color_primaries/-color_trc/-color_range`，Remotion 自己最后一道 stitch 也是 `-c:v copy`，所以单靠 `--color-space` 仍留下 `color_primaries` / `color_transfer` 为 `unknown`）。交付结果是自洽的 `yuv420p / tv / bt709 ×3`，`validate-video`（交付门）上**断言**这一组合；回写只在交付路径（`render` / `render-range` / `showcase`）上跑，`review-frames` / `benchmark-render` 那类中间产物不再回写。

- **Remotion 入口改为位置参数** —— `remotion render <entry> <composition> <output>`；4.0.x 没有 `--entry-point` 标志，而这个不存在的标志不报错（实测 `still ProbeColor out.png --entry-point=alt/entry.tsx` 退出码 0，实际渲的是 `src/index.tsx`）。`npm run render` / `npm run still`（模板与示例工程）同步改为位置参数传 `src/index.tsx`。

- **文案与许可证元数据** —— `README.md` / `README.en.md` 的许可证徽章由 MIT 改为 Apache-2.0（项目实际是 Apache-2.0），并补 CI 状态徽章；`NOTICE` 的编号修正，并新增 `world-atlas` 与 `topojson-client` 条目（ISC，由依赖声明在 `npm install` 时安装，本仓库不分发这两个包、也不在仓库里放地图数据副本）。

- **样片重渲（5 个文件）** —— `assets/demo/` 下的 `hero.png`、`notebook-video-components-demo.mp4`、`notebook-video-demo.mp4`、`notebook-video-demo.webp`、`social-preview.png` 全部按当前模板重渲，README 的免责声明改为与事实一致（此前写的是「这批样片是改动前渲的、未重渲」）。

### 修复

- **接触表第 ⑥ 页第三站标签越出画布右缘被裁**（`assets/lecture-template/src/showcase.tsx`）——组件内站点标签块固定 `left: pts[i]-150, width: 300`，旧用法 `Corridor x={100} w={1720}` 让第三站标签块伸到设计 x=2010 而被右边缘裁掉。改为 `x={130} w={1580}`（端点以画布中心 960 对称，标签块落在 20..1900 的对称留白里）。

- **接触表第 ③ 页第 5 件落在画布外 466px** —— 修法见上文新增的 `Grid5` 五格表（原 `Grid4` 只有 4 格）。

- **Remotion 入口静默失败** —— 见上文「变更」；两个模板与示例工程的 `render` / `still` 脚本一并改正。

- **交付文件色彩元数据不完整** —— 见上文「变更」；`validate-video` 上新增四项元数据的断言（缺字段的流 ffprobe 不返回该项，一律按 `unknown` 报出，不静默放过）。

- **`showcase` 的输出路径会把产物覆盖掉** —— 旧版把同一个位置参数同时当成 mp4 与 jpg 的路径，传了输出路径时最后那步抽帧会用一张 jpg 覆盖掉刚渲好的 mp4（默认路径下看不出来，因为两个默认路径本来就不同）。现两个产物各自有自己的路径。

- **`SHOWCASE_VERSION` 的「26 件旧件」与实际渲染的 18 件不符** —— 已统一为 18 件并写明两个口径的区别。该串**不在任何画面上渲染**（全仓库没有一处读它），改它不会改变任何渲染结果。

- **门禁数量三处不一致** —— `SKILL.md` frontmatter description `thirteen` → `fourteen`、`README.md` / `README.en.md` 的门禁表「十道」→「十四道」（构建期 6 + 渲染期 7 + 成片后验 1）、`.github/repository-metadata.yml` 的 `10 automated gates` → `14`。`CI` 步骤的注释同时澄清「构建期 6 道」是门禁表的分类口径，而实际挂的命令是 7 条（表里那 6 道不含字幕同步与语义断句这两条文本链检查）。

- **README 文件树漏列模板源码** —— 补上 `clipping-gate.tsx` / `fill-gate.tsx`（模板 `src` 共 14 个 `.tsx`，原来只列了 12 个）。

- **真实工程 `overview-film` 的 S2：`evidence` 写 `MetricGrid`，而本镜代码里早已换成 `Chart` + 手绘行**（`MetricGrid` 只在注释里留名）—— 已改准为 `Chart`，帧号未变。这条缺陷正是 G-15 落成判据后当场抓到的。

- **README 双份与当前实现不一致** —— 门禁枚举（补 `CanvasBoundsGate`）、接触表页数、画布说明、交付命令（`npm run render` 不做色彩回写与响度归一，出片要走交付链路 `notebook-video render`）、确定性口径、文件树、参考文档导读的可点链接等，均按当前实现改写。

### 移除

- **`PieDraw`** —— 被 `Chart variant="pie"`（有扇区百分比与图例）与 `ProgressRing`（有中央数值）上下夹住，它自己没标签、没图例、没数值。接触表第 ⑪ 页原是它独占一格，换成 pathfx 家族的组合用法（`SHAPES.callout` 标注框 + `PathDraw` 引线）。
- **`CameraMotionBlur` / `Trail` 与 `@remotion/motion-blur` 依赖** —— 全历史零渲染（全仓库只剩两处再导出与 `insert.tsx` 一行注释），而它们唯一想表达的「速度峰值」从来不在七种合法运镜意图里。
- **已删件的名字在文档里一律不加反引号**（本技能自己的规矩：反引号表示「这是可直接使用的标识符」）。

---

**English**


### Background

This is a patch release for v3.1.0, not a feature release. It concentrates on three things plus two silent failures in the render pipeline.

**1. A gate for canvas overflow, a class of defect nothing covered.** The third station's label block on contact-sheet page ⑥ was clipped by the right edge of the canvas (the copy "按 Flash 结算" rendered as "按 Flash 结"), and none of the four render-time gates or the build-time coordinate check fired. The reason was structural: every gate hangs inside `FilmLayout`, and the contact-sheet composition never passes through it, while the four render-time gates only look at clipped SVG primitives, overflow inside a card, text-on-text collisions and how low the lower quarter is filled — and `coords-lint.py` deliberately excludes layout components such as `Corridor` / `ZoomStage` / `StageFrame`. This release adds the seventh render-time gate, `CanvasBoundsGate`.

**2. Two narrative rules that were written down but never enforced.** `references/narrative-moves.md` has always said that the same `move` must not run for three or more consecutive shots, while `validate-presentation.py` only checked that each shot's `move` was one of ten names; and the only check on `evidence` was that the field was non-empty, so naming a component that does not exist, or pointing at a static card that never moves, still passed. Both rules became criteria in this release.

**3. Caption boundaries now come from BudouX phrases instead of a character count.** The trigger was a real incident: a fixed-width wrap at 17 characters split `服务器` into `传到服` / `务器。`, and because the Chinese TTS adapter reports one word per character, the cut bound cleanly and no gate could see it.

Two silent failures in the render pipeline were fixed as well: the Remotion CLI entry point (a nonexistent `--entry-point` flag is not rejected and silently falls back to another file) and the delivery file's colour metadata (the `--color-space=bt709` flag alone does not cover `color_primaries` / `color_transfer`).

### Added

- **Seventh render-time gate `CanvasBoundsGate` (canvas overflow) — gate count 13 → 14** (`assets/lecture-template/src/canvas-bounds-gate.tsx`, `src/index.tsx`). The v2 criterion is the **ink rectangle** (text taken via `Range`) of **leaf elements that contain text** (HTML leaves plus SVG `text` / `tspan`) escaping the composition viewport: ≥6px is reported, and ≥20px in a **settled state** (effective opacity ≥0.98) hard-blocks.
  - **The two mounting gears are deliberately different**: the film runs `mode="warn"` and the contact sheet runs `mode="block"`. The contact sheet is the only entry point that exists so components get seen, so a missing tile should interrupt the render; the film's hard block would land at the very last moment of a delivery render, where a false positive means the whole film is interrupted on its final frame and nothing ships — and every defect this criterion found so far came from the contact sheet. Both reasons are recorded in the gate's header and in `index.tsx`.
  - The header also records the four pieces of complexity v2 dropped relative to v1, with the cost of each: no design-coordinate folding, no graphic/layout-element branch, no exclusion set for backdrops and z≥140 chrome layers, and no frame sampling (it measures every frame). **A known blank is stated plainly**: a decorative block that overflows the canvas but contains no text at all will not be caught.
  - Once the verdict latches `blocked`, the exception is **not swallowed by the gate's own catch handler** — this repository has twice shipped a gate that reported a hard block and still produced an image with `rc=0`.
  - On its first day the gate found a real defect of the same kind in the contact sheet itself: page ③ declared five components while `Grid4` has four tiles, so the fifth (`FitTextBox`) was placed at `top=1076` and the whole tile sat **466px outside** the 1080-high canvas — that component was simply not visible on the contact sheet.

- **Negative fixtures 28 → 40** (`scripts/negative-gate-check.py`): AB0–AB4 (canvas-bounds wiring, gears and criterion narrowing), AC / AD / AE (`move` runs) and AF / AG / AJ / AK (`evidence`). `SKILL.md`'s negative spot-check paragraph is synchronised to **40 fixtures and 80 assertions, 38 of which are needles** (they pin or forbid an expected message substring, so "failed for some other reason" cannot count as a blocked fixture). The previous numbers (23 → 28) stay as they are in the `[3.1.0]` section.

- **`evidence` promoted from "non-empty" to a real gate (G-15)** (`scripts/validate-presentation.py`). Under v2, the name in `evidence` must appear **as JSX** (`<Name …>` / `<Name/>`) in the project's **scene sources**; appearing only in a comment, a string or an import line **does not count as used** — `noncode()` blanks comments and strings before the JSX match, and a miss is a P0 "no such usage". **The known limits are stated**: it does not scope to the shot in question, so a name used in another shot but not this one is missed (fixture AG pins that behaviour and must pass), and it cannot catch an `evidence` entry that points at a static card which never moves. The criterion is written back into `references/narrative-moves.md` §2 and `references/presentation-gate.md`.

- **`move` run criterion (G-14②)** — maximal runs are scanned in film order, and the same `move` for three or more consecutive shots is a P0 (`MOVE_RUN_LIMIT = 3`, i.e. at most two in a row); shots with a missing or non-whitelisted `move` break the run rather than bridging a fake one. The criterion and its severity are written back into `narrative-moves.md` §2.

- **`Grid5`, a five-tile table for contact-sheet page ③** (`assets/lecture-template/src/showcase.tsx`) — three columns by two rows, tiles 610×470, stage scaled to 0.7; horizontally 3×610 with 2×25 gaps and 2×20 margins fills 1920 exactly, and vertically it keeps `Grid4`'s 76 / 576 rows. All five components land inside the canvas, and all 17 pages were sampled frame by frame under the block gear with `rc=0`, an image, and no false positive.

- **`SUPPORT.md` (new)** — where to ask (Discussions, bug template, feature template, private vulnerability reporting), what a bug report should carry (version, OS and Node, `ffmpeg -version`, the exact command, the frame number, whether the untouched template reproduces it), three checks to run before opening an issue, and the scope and response statement (single maintainer, no SLA).

- **`assets/lecture-template/src/external-types.d.ts` (new) plus two dependencies** — `GeoView` now draws real land outlines, sourced from `world-atlas` (only `land-110m.json`, measured at 55 KB and 130 arcs) and decoded with `topojson-client` (only the `feature()` function). The types are **declared locally** rather than pulling in `@types/topojson-client`. Geographic markers are supplied by the caller; the skill does no geocoding and carries no city or border data.

- **A delivery specification for the contact sheet** (`scripts/notebook-video.mjs`) — `NotebookVideoShowcase` renders natively at 1920×1080 while the delivered file is 2560×1440, so it is scaled by 4/3 (`--scale` only accepts a decimal literal, so this must be written as `1.3333333333333333`), then a silent AAC track is added and the four colour tags are written back. Each of the three steps can be redone on its own, and the failure messages for the last two say explicitly that the video itself is already complete and does not need re-rendering.

- **Three CI steps** (`.github/workflows/validate.yml`) — type-checking the template (`npm ci` plus `npm run typecheck`, which must come after the step that asserts no `node_modules` exists in the repository tree), caching the template's `package-lock.json`, and re-running the semantic-break check with `--require-budoux` (which must come after the `npm ci` above it).

- **Two new sections in `references/windows-compatibility.md`** — why the colour contract is pinned (the two ordered steps and what each contributes) and a `npx remotion` hang (low CPU, zero output, no child process); `references/dependency-policy.md` gains §9, a template-to-project sync checklist (measured this round: the template's `GeoView` already draws real land outlines, while the long film's `package.json` has zero occurrences of `world-atlas` / `topojson-client` and its `data.tsx` has no matching import, so that project is still on the old graticule).

### Changed

- **Version strings unified to `3.1.1`** — `SKILL.md`'s frontmatter, `manifest.json` (which also gains `"license": "Apache-2.0"`), the contact-sheet footer (`COMPONENTS_VERSION` → `components-v3.1.1 · 27 件`) and the release tag and title in `.github/repository-metadata.yml`.

- **Wrapped layer 29 → 27 components, and the counted floor 55 → 53** (`assets/lecture-template/src/components/index.ts`; 53 = 27 in this layer plus 26 across the other eight modules). `references/fxkit.md`, `references/media-routing.md`, `references/dependency-policy.md`, `references/locked-style-contract.json` and the comment in `scripts/validate-frame-props.py` are synchronised, and `SKILL.md` now counts **five** official `@remotion/*` extensions (dropping `motion-blur`).

- **One authoritative component index** — §5.1 "component index" in `references/media-routing.md` (53 components with purpose, when to use, when not to, contact-sheet page and real usage record, including the components that are not on the contact sheet and why). `fxkit.md` and `showcase.tsx` now keep only implementation details and page layout and no longer maintain their own lists, and `SKILL.md` states plainly that the contact sheet must not be reverse-engineered into a component list. The old-component count also stops drifting: `SHOWCASE_VERSION` claimed "26 件旧件" while the contact sheet renders **18**, so it now says 18, and §6 explains the difference between the two counts (26 is how many the old modules export).

- **`FitTextBox` actually used ("add one, replace one")** — the rail panel's body block in the template's `scenes.tsx` S1 (fixed inner width 348, previously a hand-written 20px size with a hand-written `<br />`) now derives its size from width and a line limit (`maxFontSize` set to the original design size, `maxLines` to the design line count), so longer copy steps down in size instead of pushing out of the panel.

- **Caption boundaries now come from BudouX phrases** (`scripts/build-semantic-captions.py`, `scripts/validate-semantic-breaks.py`) — a boundary is legal only at a BudouX phrase boundary or immediately after a clause mark (`，。！？；：、…—` and their ASCII equivalents), never inside an ASCII or digit token, and every boundary that had to be moved is printed with its reason. Both tools locate BudouX through the project's `node_modules` and **degrade loudly** when it is missing (`WARNING: BudouX …` plus `break_rule: mechanical-only (BudouX unavailable)`) rather than skipping silently; the **delivery path adds `--require-budoux`, where a missing model exits non-zero**, because a skip is invisible in an exit code. `--warn-chars N` is an optional hint and **off by default** (the shipped template legitimately reaches 19 characters, so any threshold produces false alarms). The rationale and the exact commands are written back into `references/subtitle-timing.md` and `references/tts-audio.md`, which now say to author semantic units and let the tool decide display boundaries. **The known limit is stated**: this covers within-sentence breaks and protected phrases; wording that straddles two cues has no criterion.

- **A colour contract for delivered files** (`scripts/notebook-video.mjs`, both templates' `package.json`) — first `--color-space=bt709` (which, since `@remotion/renderer` 4.0.83, really converts the pixels to limited range), then a `h264_metadata` bitstream filter on the **copied** stream to write the four metadata fields back. FFmpeg ignores `-colorspace/-color_primaries/-color_trc/-color_range` on a copied stream, and Remotion's own final stitch also copies, so the flag alone still leaves `color_primaries` and `color_transfer` as `unknown`. The delivered file is now self-consistent (`yuv420p / tv / bt709 ×3`), and `validate-video` (the delivery gate) **asserts** that combination. Tagging runs only on the delivery paths (`render` / `render-range` / `showcase`); debug artifacts such as `review-frames` and `benchmark-render` are no longer tagged.

- **The Remotion entry point is passed positionally** — `remotion render <entry> <composition> <output>`. `@remotion/cli` 4.0.x has no `--entry-point` flag, and the bogus flag is not rejected (measured: `still ProbeColor out.png --entry-point=alt/entry.tsx` exits 0 and renders `src/index.tsx` instead). The `render` and `still` scripts in both templates and the example project now pass `src/index.tsx` positionally.

- **Copy and licence metadata** — the licence badge in `README.md` / `README.en.md` changes from MIT to Apache-2.0 (which is what the project actually uses), and a CI status badge is added; `NOTICE` is renumbered and gains entries for `world-atlas` and `topojson-client` (ISC; installed by the dependency declaration at `npm install` — this repository neither redistributes those packages nor keeps a copy of the map data).

- **Demo files re-rendered (five files)** — `hero.png`, `notebook-video-components-demo.mp4`, `notebook-video-demo.mp4`, `notebook-video-demo.webp` and `social-preview.png` under `assets/demo/` were all re-rendered with the current template, and the README disclaimer was rewritten to match (it previously said the samples were rendered before the changes and had not been re-rendered).

### Fixed

- **Contact-sheet page ⑥'s third station label clipped by the right edge** (`assets/lecture-template/src/showcase.tsx`) — the component's station label block is fixed at `left: pts[i]-150, width: 300`, and the old `Corridor x={100} w={1720}` pushed the third station's label block out to design x=2010, where the right edge cut it off. It is now `x={130} w={1580}` (endpoints symmetric about the canvas centre at 960, so the label blocks sit inside a symmetric 20..1900 margin).

- **Contact-sheet page ③'s fifth component sitting 466px outside the canvas** — fixed by the new `Grid5` table described above (the old `Grid4` had only four tiles).

- **The silent Remotion entry-point failure** — see Changed; the `render` and `still` scripts in both templates and the example project were corrected together.

- **Incomplete colour metadata on delivered files** — see Changed; `validate-video` now asserts the four fields (a stream missing a field means ffprobe returns nothing for it, which is reported as `unknown` rather than passed over).

- **`showcase` overwriting its own output** — the old code used one positional argument as the path for both the mp4 and the jpg, so passing an output path made the final frame extraction overwrite the freshly rendered mp4 with a jpg (invisible on the default paths, because the two defaults differ). Each artifact now has its own path.

- **`SHOWCASE_VERSION` claiming "26 件旧件" against 18 actually rendered** — it now says 18, with the difference between the two counts explained. The string **is not rendered anywhere** (nothing in the repository reads it), so changing it cannot change any output.

- **Gate counts disagreed in three places** — `SKILL.md`'s frontmatter moves from `thirteen` to `fourteen`, the gate table in `README.md` / `README.en.md` from ten to fourteen (six build-time, seven render-time, one post-render), and `.github/repository-metadata.yml` from `10 automated gates` to `14`. A comment in the CI step also clarifies that "six build-time gates" is the classification used by the gate table while the step actually runs seven commands (the table's six exclude the two text-chain checks for caption sync and semantic breaks).

- **README file tree missing template sources** — `clipping-gate.tsx` / `fill-gate.tsx` were added (the template's `src` holds 14 `.tsx` files; only 12 were listed).

- **`overview-film` S2: `evidence` named `MetricGrid` while the shot's code had long since switched to `Chart` plus hand-drawn rows** (`MetricGrid` survived only in a comment). It now names `Chart`, with the frame numbers unchanged. This is the defect the new G-15 criterion caught on its first run.

- **Both READMEs had drifted from the implementation** — the gate enumeration (adding `CanvasBoundsGate`), the contact-sheet page count, the canvas notes, the delivery commands (`npm run render` does no colour write-back and no loudness normalisation, so shipping requires the delivery path `notebook-video render`), the determinism statement, the file tree and the clickable reference index were all rewritten to match.

### Removed

- **`PieDraw`** — squeezed between `Chart variant="pie"` (which has sector percentages and a legend) and `ProgressRing` (which has a central value), it had no labels, no legend and no numbers of its own. Its dedicated tile on contact-sheet page ⑪ is now a pathfx combination (`SHAPES.callout` plus a `PathDraw` leader line).
- **`CameraMotionBlur` / `Trail` and the `@remotion/motion-blur` dependency** — never rendered once in the project's history (only two re-exports and one comment in `insert.tsx` remained), and the "speed peak" they existed to express was never one of the seven legal camera intents.
- **Deleted component names are no longer written in backticks anywhere in the documentation** — the skill's own convention is that a backtick marks a usable identifier.

---

## [3.1.0] - 2026-09-21

> 对照基线 `v3.0.3`：**79 个文件，+13 099 行，−1 905 行**。

### 背景与动机

本版由两条相互独立的线索推动，两条都在本次差异里有对应的改动。

**一、多道渲染期门禁自装上起从未真正拦过。** 起因是成片 2:58 处一处「组件没有动」的缺陷，而当时十道门禁全部 PASS。回查的结论不是判据过松，而是执行路径失效：测量排在 `requestAnimationFrame` 里，却没有 `delayRender` 兜住截帧——Remotion 截帧不等 rAF，测量永远晚于出图；判定包在 `try/catch` 里，而 `cancelRender()` 的实现就是 `throw`，硬拦异常被自家 `catch` 吞掉、handle 照常释放，于是出现「报了硬拦却照样出图 rc=0」。本版先把五道渲染期门禁逐条修成真拦（判据：负向夹具 `rc≠0` **且**不产出图片），再补两类此前没有任何门禁覆盖的缺陷（图形被裁、下 1/4 空着），并把模板的 TypeScript 从「能打包就行」收到 `tsc` 0 错。

**二、「零依赖」的边界被误读。** 技能里原有的「零第三方依赖」本意只是限定 `scripts/` 下的 Python 脚本，却被读成「整个技能不许用任何第三方库」。后果是所有成熟组件都不敢碰、画面元素全部手写 SVG——恰好做出了最难复现的结果，而这条规矩的本意正是「任何环境都能复现」。本版把边界写成唯一定源、把依赖补齐、建起封装组件层，并留下可复现的验证记录。

### 新增

- **依赖边界的唯一定源 `references/dependency-policy.md`（新，227 行）** —— 按三类纪律划分：禁止按次付费、结果不可复现的生成式模型（生图 / 生视频 API）；允许且鼓励开源、可被 lock 文件锁版本的 React 库，随模板一次 `npm install` 装好、无需额外授权；清单之外的新库需用户授权。附三条判据（要钱吗 / 能复现吗 / 能锁版本吗）、已内置依赖清单、零依赖效果配方、社区组件库不能原样粘贴的理由，以及组件增长纪律「加一件＝换掉一件」——合规判据是「零引用」而不是一个拍脑袋的总数。

- **封装组件层 `assets/lecture-template/src/components/`（新，10 个文件，29 件）** —— 场景的唯一入口；库提供结构，本层提供皮肤与帧驱动适配，颜色 / 边框 / 阴影只读 `THEME`，动画一律是帧号的纯函数。
  - `ui.tsx`：`Accordion`（Radix 手风琴）、`Tabs`（Radix 标签页）、`ControlStack`（开关 / 复选 / 单选 / 滑块 / 分段 / 进度条，状态由 `steps: [{at, value}]` 显式表决定）、`HighlightCode`（语法高亮 + 行号 + 逐行聚焦）、`MathBlock`（KaTeX）、`TopicIcon` / `IconWall`（react-icons，`fa` + `fi` + `lu` 三套）。
  - `chart.tsx`：`Chart`（`line` / `area` / `stack` / `stackExpand` / `stream` / `radar` / `pie` 七个变体，含 `csv` 入口）、`StatRow`。
  - `data.tsx`：`TreeView`（`tree` / `treemap` / `pack` / `sunburst`）、`GeoView`、`SankeyChart`、`QrCode`、`fitNodeLabel` / `fitOneLine`。
  - `overlay.tsx`：`OverlayFrame`（`dialog` / `menu` / `popover` / `tooltip` 四种弹层，Portal 落点钉死在画面根）。
  - `network.tsx`：`NetworkGraph`（d3-force 力导向布局，初值显式给定 + 迭代次数写死 + 果断 `.stop()`）。
  - `sketch.tsx`：`SketchFx` / `sketchCircleArea` / `sketchUnderline` / `sketchBox`（roughjs 手绘风）。
  - `effects.tsx`：`GlowFrame` / `ShimmerText` / `ClipReveal` / `NoiseJitter` / `VerdictBar`（全部零依赖，CSS/SVG 数学 + 帧号）。
  - `pathfx.tsx`：`PathDraw` / `MorphShape` / `ShapeDraw` / `SHAPES` / `SceneTransitions`（`PRESENTATIONS` 20 种官方转场）。
  - `fittext.tsx`：`FitTextBox` / `fitChineseTextOnNLines` / `assertFits` / `fitsWithin`。
  - `focus.tsx`：`FocusFx`（注意力三件：dim / spot / loupe / marker）。

- **模板的类型检查** —— 新增 `assets/lecture-template/tsconfig.json`、`typescript` devDependency 与 `npm run typecheck`（= `tsc -p tsconfig.json`，`noEmit` 已开）。模板此前能打包但没有类型检查，"能跑就行"的那类错误因此永远不会有人看见。

- **两道渲染期门禁回灌模板并接线**（工程侧已有，本版复制进模板）：
  - `assets/lecture-template/src/clipping-gate.tsx`：图形被裁——SVG / 图形元素的实际 rect 越出最近的「会裁切」祖先（HTML 的 `overflow≠visible` 祖先，或所属 `<svg>` 视口；显式 `overflow:visible` 按计算样式判、不算越界）。`CardFitGate` 只管 div/span 里的文字、`OverlapGate` 只管文字互相压，两者都看不见「缺了半边的球」。
  - `assets/lecture-template/src/fill-gate.tsx`：下 1/4 实测密度——信息元素（有文字 / 有边框 / 有描边）rect 并集的最低边对比 y=876（±24 容差），z≥140 的子树跳过。
  - 接线契约：设计根新增 `data-design-root`（`FillGate` 靠它把输出像素折回设计像素，缺了它会静默 `return`），两道门一并挂进 `index.tsx` 的 `WATCH` 抽样。

- **`WATCH` 抽样补「落定帧」`to−12`** —— 项目约定「落定帧 = 镜尾 − 12」，而它一般不是 15 的倍数、也不在事件帧里。补上之前，21 张落定帧里只有 1 张落在抽样集合上。

- **成片后验门禁 `scripts/validate-motion-gaps.py`（新）** —— `ffmpeg freezedetect` 逐帧比对，连续「几乎完全相同」超过阈值即 P0。必须先裁掉字幕带：字幕逐字上屏会把每一段静止都遮掉（同一支片：全画幅只报 73 段、S19 的 2.5 秒完全不在榜上；裁掉字幕带后报 53 段）。

- **呈现效果门禁 `scripts/validate-presentation.py`（新）与判据文档 `references/presentation-gate.md`（新）** —— 现有门禁问的都是「有没有 / 够不够多 / 会不会撞」，没有一条问过「观众此刻该看哪里、读不读得过来」，于是「五个同等大小的标题并排」「正文 11px」「灰字压灰底」全部合法。本道新增判据：G-1 节拍时间接近（beat 必须落在它声明的那句 / 那一镜内，不早于该句 12 帧、不晚于该句结束 +8 帧，每条 cue 至少一拍）；G-2 字幕阅读预算（≤9 加权字/秒、**每行** ≤16、≤2 行，加权 = CJK 1 / ASCII 0.5）；G-3 可读性（`fontSize < 13` 即 P0；正文色对比度 < 4.5:1 即 P0，WCAG 2.2 SC 1.4.3）；G-5 节拍拥挤（P1）。

- **讲法字段门禁 G-14 / G-15 / G-16 与 `references/narrative-moves.md`（新）** —— `move` 必须落在 10 个名字的闭集里、`evidence` 必填、`hold` 不低于标定线 40 帧、`misconception` 与 `noMisconception(+why)` 二选一。配套修好 `resolve-shots.py` 把 `move` / `evidence` / `hold` / `misconception` 整组丢掉的问题——此前下游读 `resolved` 的门禁根本看不到这四个字段。

- **构建期判据两条**：
  - `validate-composition.py` 新增 **P0-7 · beats 下标越界**：逐镜扫场景源码里的 `b[k]` 与 `SHOTS.Sx.beats[k]`（**两种写法都扫**），`k` 必须小于真实拍数；引用不存在的镜号一并报。越界取到的是 `undefined`，传进 `interpolate` 会整帧渲染失败，传进比较则那件东西永远不出现。
  - `validate-shot-motion.py` 新增节拍空档 P1（`BEAT_GAP_MAX_RATIO = 0.60`，先离线标定再定阈值）。

- **四套主题各补 5 个文字安全色** —— `blueInk` / `orangeInk` / `greenInk` / `goldInk` / `redInk`（同色相按 WCAG 反解压暗），`theme/types.ts` 的 `ThemePalette` 相应扩容。约定写进 `references/theme-system.md`：原色只用于填充与描边，当文字色一律用对应的 Ink 变体。`validate-presentation.py` 同步新增 `*Ink` 判据（五个 `*Ink` 不过 4.5:1 直接报），作为该机制的自检。

- **CI 挂上模板的门禁** —— `.github/workflows/validate.yml` 新增三步：模板上的 6 道构建期门禁、`negative-gate-check.py`、`coords-lint.py`。此前 CI 一条门禁都不跑，「负向抽查」长期只是本地仪式。

- **负向夹具 23 → 28 例**（`scripts/negative-gate-check.py`）：新增 X（讲法字段缺 `move`）、Y（`*Ink` 文字安全色压白底）、Z1–Z3（拍数越界：本地别名 `b[9]` / 全路径 `SHOTS.S2.beats[9]` / 一条阴性对照）。判据加了而夹具没加，等于那道门仍然只是名义存在，所以新增判据与夹具同版落地。

- **依赖补齐** —— 模板 `assets/lecture-template/package.json` 从 5 个 dependencies（0 个 devDependencies）扩到 37 + 10：
  - UI 与结构：12 个 Radix primitive、`react-icons`、`react-syntax-highlighter` `^16.1.1`。
  - 数据与图形：`d3-scale` / `d3-shape` / `d3-hierarchy` / `d3-geo` / `d3-sankey` / `d3-dsv` / `d3-force`、`roughjs`、`qrcode`、`katex`。
  - 文本：`budoux`（中文按词组断行）、`@cto.af/linebreak`（UAX #14 断行算法；此前先用 foliojs 的 `linebreak@1.1.0`，因其钉死 `base64-js@0.0.8`（2014 年）且 2022 年后停更而换成现代实现，实测两包在同一批文本上断点逐一相同、换包零行为变化）。
  - 六个 `@remotion/*` 官方扩展：`transitions` / `paths` / `shapes` / `motion-blur` / `layout-utils` / `noise`。

- **接触表 9 → 17 页**（`SHOWCASE_PAGES`，`SHOWCASE_VERSION` 随之升到 `showcase-v8`）—— 新增图表变体、层级与关系、弹层与形状、手绘风与公式等页。

- **官方美学系统的可编辑面补第 8 项**（`references/official-aesthetic-system.md`）—— `src/components/` 组件层是明确允许编辑的界面，须「先用现成封装件，再考虑手写 SVG」。此前 7 项可编辑范围里没有组件层，AI 读到的信号是「组件不归我管」。

### 变更

- **`SKILL.md` 的「零依赖」措辞（3 处）** —— 开篇补一段边界声明（禁的是付费生成式模型，不是开源库；手写每个 UI 元素不是目标，是最慢的劣解）；Zero-Mutation 一节把「依赖」拆成两种纪律（模板已内置的无需授权直接 `import`；清单之外的新依赖才需授权）；「`scripts/*.py` 零第三方依赖」明确限定只针对 Python 脚本。`references/fxkit.md` / `README.md` / `src/insert.tsx` 里残留的「零依赖」口号同步删除，`insert.tsx` 的 whip 甩镜注释改为指向已内置的 `@remotion/motion-blur`；README FAQ 新增一问「能用开源的 UI 组件库吗」（能，而且鼓励）。

- **组件清理：49 件 → 45 件** —— 删掉 23 件从未出现在任何画面里的组件，加入 19 件新封装层。删除依据是一份逐件实测的使用率审计（按真实 JSX 渲染统计，不是只看有没有 import）；其中 `AIChatBox`（315 行）是整库里最大的一件、v3.0.3 的头号新功能，但一帧画面都没进过。全部删除项可从 git 历史取回。

- **两处命名冲突（实测踩到，都会静默出错）** —— 新封装层的代码块组件原名 `CodeBlock`，与 `toolkit.tsx` 已有的同名件冲突、被静默盖住后渲染期直接报错 → 改名 `HighlightCode`；新层 `RevealMask` 与 `insert.tsx` 的 `RevealMask` 同名 → 改名 `ClipReveal`。

- **确定性口径收窄** —— **still / PNG 逐字节可复现；长片段 mp4 只保证画面等价**。实测同一棵树连渲 900 帧的 md5 每次都不同（`3f5557ad` / `2ad431d5` / `11a88601`），像素差只落在边缘少数点（最大 76、平均 0.12、95.2% 字节相同），属 x264 编码层噪声而非内容差异。README 两份按此改写。

- **门禁数量的表述** —— `SKILL.md` frontmatter description `nine` → `thirteen`；`README.md` / `README.en.md` 的门禁表 `九道` → `十道`；`.github/repository-metadata.yml` 的 `8 automated gates` → `10`。

- **`bottomFill` 判据降级（构建期）** —— `validate-composition` 原来校验 `bottomFill == true`，而这个字段是生成分镜表的脚本自己写死的常量、`resolve-shots` 再原样透传，生成器写 `true`、门禁要求 `true`，**结构上不可能失败**（实测成片里 17/21 镜的下 1/4 是空的，它一次都没响）。现只查字段在不在，真实判据交给渲染期 `FillGate`；`validate-shot-motion` 里同源的 `bottomFill is False` 分支同步降级。判据说明写回 `references/composition-gate.md` 的 P0-4、`references/scene-skeletons.md` 与 `SKILL.md` 第 16 条。

- **门禁编号改号** —— 讲法字段那一组原标成 `G-6`，而 `G-6` 在调研报告里是「对比层结构闭合」（至今未实现）。按 `references/narrative-moves.md` §4 改为 **G-14 `move` 闭合 / G-15 `evidence` 真的会动 / G-16 误解与留白**。

- **模板 `tsc` 清到 0 错：19 条未用导入 / 死变量 + 1 条 TS2367** —— 它翻出来的不是洁癖问题，而是一批**静默失效**（「传了参数、库当没看见」或引用了不存在的名字，运行时不报错）：`ShapeInfo` 从 `@remotion/shapes` 深路径导入而该类型未从包根导出；`SHAPES` 四处错参数（`makeCallout` 的 `pointerBaseWidth`、`makeHeart` 的 `height`+`aspectRatio`、`makeEllipse` 的 `rx`+`ry`、`makeTriangle` 的必填 `direction`）；`pushCut` 传了它没有的 `direction`；`ui.tsx` 的 `fitsWithin` 从未 import（且挂在 `NODE_ENV !== 'production'` 下，出片路径永远走不到）；`shotkit.tsx` 的 `head`/`tail` 声明成 `CamKey[]` 却赋一个关键帧对象，`shotCam` 因此返回嵌套数组、`camAt` 读到的是垃圾；`scenes.tsx` 的 `FitCard` 被多传了它不认的 `f={f}`（React 会把未知 prop 静默丢掉）。另有三处「入参从未使用」的假旋钮（`fxkit` 的 `lift`、`skeletons` 的 `from`/`to`）：类型里保留、实现里不再声明。`Film4x3` / `Film3x4` 按 `references/canvas-modes.md` 的契约（「定义了但默认不注册」）改为导出，以免被 `noUnusedLocals` 判成死代码。

- **`useSteppedFrame` 回到场景可 import 的那一层** —— `references/motion-design.md` 教作者用 `useSteppedFrame(15)`，而全树没有任何实现。处置是把 API 放回 `toolkit.tsx` 而不是删文档（停帧是贴纸风的正经手法），并给出两个入口：拿到镜内局部帧时用纯函数 `stepped(f, 15)`，不接帧参数的组件才用 `useSteppedFrame(15)`。

- **`popS` / `SPRINGS` 从 `fxkit.tsx` 导出** —— `motion-design.md` 的纪律此前不可执行（这两个名字只有模块内的私有定义、没有 `export`，场景文件在物理上 import 不到）。

- **路由表改为每行一个「首选」** —— 原表多行并列新旧三四个平级选项（如「数据 / 对比」同时列 `Chart` + `ProgressRing` + `MetricGrid`），等于没给建议。其余选项标注「何时才用」，并在表头写明教训：路由表里有名字的组件照样一件不用——实测 23 件从未出现在任何画面里，其中 21 件早已登记在本表。

- **lockfile 重生与两份 lock 对齐** —— 模板 lock 原先自身混用 Remotion 家族版本（`remotion` / `@remotion/cli` / `@remotion/media` 为 4.0.489，`@remotion/transitions` 等为 4.0.526），而 Remotion 要求全家族同版本。重生后家族 33 个包统一为 4.0.526；两份 lock 解析出的直接依赖版本现已完全一致，形式差异（模板 caret / 验证工程 exact）是刻意的。

- **`HighlightCode` 换 `PrismLight`** —— 从全语言构建改为按需注册 6 种语言（tsx / ts / python / bash / json / diff，含别名）：源侧体积从 `refractor/lang` 的 277 个语言文件 / 0.83 MB 降到 8 个 / 30 KB。

- **混排断行换 UAX #14** —— `fittext.tsx` 原先手写两张字符表（`NO_LINE_START` / `NO_LINE_END`）做避头尾，实测只是粗糙近似且**错在中英混排**：10 条真实文本里手写表允许 **36 个非法断点**（`在G|itHub`、`hyt|315`、`第三个A|I技能`、`S|1：`…），换 UAX #14 后 **36 → 0**；纯中文用例两者逐一相同。

- **文档同步** —— `references/fxkit.md` 目录重写并补封装层一节、`references/media-routing.md` 路由表剔除已删件并改写「修辞动作 → 组件」表、`references/official-aesthetic-system.md` 补组件层与图标政策、`SKILL.md` / `README.md` / `README.en.md` 的门禁清单补 `ClippingGate` / `FillGate` / `validate-motion-gaps`。

### 修复

- **`OverlapGate` 从「从没拦过」修成真拦（四处静默失效 + 一处结构性失明）**：
  - 没有 `delayRender`：测量排在 `requestAnimationFrame` 里，而 Remotion 截帧不等 rAF，门禁从装上那天起就没站上出图路径。改为逐帧持柄（每个抽样帧开一个 handle，测完才 `continueRender`）。
  - 字体未就绪直接 `return`：真实出片路径上 `document.fonts.status` 一直是 `'loading'`，于是每帧都在这一行返回（重渲后日志里连覆盖率日志都没有）。改为等 `document.fonts.ready` 再量。
  - 三个采样点全落在文字框垂直中线：S14 那处「弹层标题条切掉正文下半截」实测漏判（墨迹 685..703、压线 702、中线 ~699，正好落在压线之上）。补 22% / 78% 两个高度层共 5 点。
  - 硬拦被自家 `catch` 吞掉：`cancelRender()` 的实现是 `throw`，旧代码 `catch (e) { console.warn(e) }` 把它吞了，随后走到末尾的 `release()` → handle 归零 → 渲染器取到 ready → 硬拦命中却出图 rc=0。改为 `blocked` 置位后 handle 永不释放、异常原样抛出。
  - **`INVISIBLE_CHARS` 少一个 `u` 标志**：原写法被正则引擎拆成 `\uf000` + `0` + `-` + `\uffff` + `d`，字符类里凭空多出 **U+0030–U+FFFF（65 488 个码点）**，全部汉字、数字与多数可打印 ASCII 都被替换成空串，后果是整块是汉字的文字叶元素一个都进不了 `texts`（成片实测：87 条字幕文本 100% 被整条吞空，覆盖率日志里每帧只「已测 2 个文字块」）。修法是补 `u` 标志并把补充平面写成 `\u{…}`，另加启动自检：`visibleText('重A0') !== '重A0'` 就在控制台报警。

- **`CardFitGate` / `CaptionFitGate` 补上同一处置**（`assets/lecture-template/src/index.tsx`）—— 两处的「拦得住」此前纯属结构巧合（`cancelRender` 之后的 `continueRender` 恰好在 `try` 块内），现在与其余门禁一致：判定后 `blocked` 置位、异常不被吞。

- **`FocusFx` 压暗按「三因」重做**：
  - 颜色是纸色：`background: C.paperBase` 在纸色底上等于没画（亮底 249.2 → 247.4，中灰 128 → 214，反而提亮）。改用 `muted` + `multiply`：亮底 → 146.8、中灰 → 76.1。
  - 不是覆盖层：原实现只有 `position:absolute` 且没有 z-index，「写在内容前面」就被内容盖住。新增 `SCENE_ANCHOR`。
  - 坐标随宿主漂移：注释承诺 `rect` 是场景坐标，实现却按最近的定位祖先算，塞进 `left:200,top:300` 的包裹层后蒙版整体偏出画布左上（左缘 60px 处实测 247.3 = 完全没被盖到）。`SCENE_ANCHOR` 用 `position:fixed` 把坐标钉回场景坐标。

- **`FocusFx` 的 `zIndex` 从 9000 降到 160：定位遮罩不再盖住字幕** —— 上一版把遮罩做成覆盖层时取了 9000，结果它落在 `SubtitleChrome`（z=200）之上，S8 的字幕被 `multiply` 同一档压暗（字形核心 25.1 → 15.1 = 墨色 × 0.594），而这正是 `focus.tsx` 注释里承诺「不会发生」的事。现按整片的层级梯子取值：场景内容 ≤130 → 页眉 140 / 章节卡 150 → 遮罩 160 → Grade 190 → 字幕 200。实测（同一帧 2360）：字幕字形核心 6 点均值 27.5 → 26.2（回到修前水平），洞外角点仍被压暗 146.1–150.7，洞内均值 216.0，洞的边界仍在输出 540/753/460/620。

- **一批「传了参数、库当没看见」的静默失效**（由 `tsc` 翻出，逐项见上文「变更」中的诊断表）。

- **`assertFits` 是名存实亡的门禁** —— 它定义了却从未被任何代码调用。处置：新增 `fitsWithin()`（同一套 `measureText` 实测，只警告不抛错）并接进真正会出现「固定尺寸卡片 + 可变文案」的 `StatRow` 与 `VerdictBar`（仅开发期执行，生产渲染零开销）；`assertFits()` 保留为编写期自查工具，文档里不再称其为自动门禁。

- **`coords-lint.py` 漏检整整一层** —— 它只扫 `src/*.tsx`，而组件封装层在 `src/components/`，整个新层从未被坐标检查覆盖。改为 `rglob` 递归，并把 `OVERLAYS` 名单改为从 `src/components/** + src/theme/**` 推导（只取场景坐标语义的件）。

- **`validate-frame-props.py` 对 `src/components/` 整层失效** —— 名单含 4 个不存在的文件且不递归（解析组件数 65 → 88）。

- **`import_integrity` 上一条是「写了但没做」** —— 现在真做了：递归扫 `src/**`（.ts/.tsx），认 `./x` `../x` 与目录桶 `./components` → `components/index`，跟随 `export *`，并把「从 npm 包再导出」与「名字不存在」分开（前者必须不报，否则整条链全是假 P0）。实测模板 30 个文件 / 78 条相对 import → P0=0，并在当场抓到一条真漏检。

- **接触表自身的渲染缺陷** —— `DiffView` 在接触表里一直渲染失败（示例数据首行漏了 `at` 字段，`undefined` 传进 `spring({frame})` 触发 Remotion 报错）；`Chart` 的 `d3line(...)` 仍传旧的 `data` 变量（用 `csv` 入口时 `d3-shape` 收到 `undefined` 抛 `undefined is not iterable`）；`TreeView` 的 `viewBox` 切掉根节点顶沿；`SketchFx` 每帧重画会叠加笔迹（roughjs 往 DOM 里 append，改为每次绘制前清空）。

- **图表与层级件的一批「不报错但画错」** —— `treemap` / `pack` / `partition` 共用同一个 `hierarchy()` 根导致后跑的布局覆盖先跑的；`d3.arc` 默认访问器与 partition 节点不匹配，旭日图的环一个都没画出来且不报错；`d3stack` 入参需显式转置；`TreeView` 标签只检查宽度不检查高度；旭日图标签方向与下半圈翻转；`Chart` 的 `pie` 变体取整列当扇区；雷达图半径过小。第二轮复验另修掉三处：旭日图标签单行溢出（反推按 2 行、实画 1 行）、关系网节点标签被拆成两行、面积图首个数据点的数值标签压在 Y 轴刻度上。

- **`fillStyle:'dots'` 让整页不可复现** —— 同一帧渲三次得到三个不同哈希，差异恒定落在接触表 ⑭ 页 dots 那一格。定位到根因：roughjs 的 dots 填充器在 `dotsOnLines` 里无条件调 `Math.random()` 两次 / 每点，与 `seed` 无关。处置是把 `'dots'` 从 `SketchStyle.fillStyle` 移除、改用确定性的 `'dashed'`；同时加护栏：`seed: 0` 是假值（roughjs 的 LCG 写作 `this.seed ? … : Math.random()`），为假值时打印明确告警并自动改用 `seed=1`。

- **`index.tsx` 的 TS2367 死比较** —— `s.cameraIntent !== 'still'` 恒真（`shots.ts` 只生成 5 种意图，类型里根本没有 `'still'`），「静止镜不加咔哒声」实际一个都没排除。改为正向名单 `CAM_MOTION`，名单里没有的值（含将来的 `still`）不加音；没有简单删掉判断（删了会让静止镜也加音效）。

- **`ShotIntent` 类型缺 `'still'`** —— 类型里没有它，而 `stillCam` 的注释明写「still 是合法选择」。已补进联合类型（即上面那条恒真比较的根因）。

- **`fxkit.tsx` 里一条与文件内容不符的注释** —— 它写「`q` 与 `ease` 两个局部 helper…本文件从头到尾没用过」，而紧邻其下的 `easeOutSoft` / `SPRINGS` / `popS` 正在被本文件用了十几次。现在写明是「那两件」没被调用过，并显式标注下面三个是在用的、别一起删。

- **版本号对不上** —— `SKILL.md` frontmatter 仍是 `3.0.3`、`README.md` 仍写「当前 v3.0.2」，而 CHANGELOG 已到 3.1.0 → 统一为 **3.1.0**。

- **文档残留已删组件名（8 个文件约 30 处）** —— 其中最危险的一类会指使执行 AI 去 import 一个不存在的组件：`shot-language.md` 的示例代码里有 `import {..., DepthLayers} from './shotkit'` 与整段 `<DepthLayers>` 用法；`fxkit.md` 仍列 `BrowserChrome` / `Mascot` 行且有一整节在讲已删除的 `ShotPlate`；`media-routing.md` 的「修辞动作 → 组件」表里 7 行推荐的是已删组件；`README.md` / `README.en.md` 结构树里仍列已删除的 `plates.tsx`。复检后残留清零。

### 移除

- **23 件从未出现在任何画面里的组件**（`fxkit.tsx` / `toolkit.tsx` / `insert.tsx` / `stagekit.tsx` / `shotkit.tsx` / `plates.tsx` 六个模块），其中 `AIChatBox`（315 行）是整库里最大的一件、v3.0.3 的头号新功能。全部删除项可从 git 历史取回。
- **`assets/lecture-template/src/plates.tsx` 整个文件删除**（其唯一组件 `ShotPlate` 从未进过画面）。
- **接触表第 ⑧ 页整页删除**（该页全部是已删组件），其余页合并。
- **手写的避头尾字符表**（`fittext.tsx` 的 `NO_LINE_START` / `NO_LINE_END`）由 UAX #14 算法取代。

---

**English**


### Background

This release was driven by two independent findings, both with concrete changes in the diff.

**1. Several render-time gates had never actually blocked anything.** The trigger was a defect at 2:58 in a finished film where "a component did not move", while all ten gates reported PASS. The cause was not loose thresholds but a broken execution path: measurement was scheduled inside `requestAnimationFrame` with no `delayRender` holding the frame — Remotion captures without waiting for rAF, so measurement always happened after the picture was taken. On top of that, the verdict was wrapped in `try/catch`, and `cancelRender()` itself is implemented as `throw`, so the hard-block exception was swallowed by the gate's own catch handler and the handle was released as usual: a gate could report a hard block and still produce an image with `rc=0`. This release reworks five render-time gates into gates that really block (criterion: a negative fixture must exit non-zero **and** produce no image), closes two classes of defect that no gate covered at all (clipped graphics, an empty lower quarter), and tightens the template's TypeScript from "it bundles" to `tsc` with zero errors.

**2. The "zero dependency" boundary was misread.** The skill carried the sentence "zero third-party dependencies", which only ever meant the Python scripts under `scripts/`; it was read as "no third-party library may be used anywhere in the skill". The result was that no mature component library was ever touched and every visual element was hand-written SVG — which produced exactly the hardest-to-reproduce result, while the rule's actual intent was reproducibility in any environment. This release writes the boundary down as a single source of truth, installs the dependencies, and builds the wrapped component layer.

### Added

- **`references/dependency-policy.md` (new, 227 lines) — the single source of truth for the dependency boundary.** Three classes of discipline: banned are paid, non-reproducible generative models (image/video generation APIs); allowed and encouraged are open-source React libraries pinned by a lock file, installed in one `npm install` with no separate authorisation; anything outside the list requires the user's approval. It also carries three tests (does it cost money / is it reproducible / can it be version-locked), the built-in dependency list, zero-dependency effect recipes, why community component libraries cannot be pasted in as-is, and the growth rule "add one, replace one" — compliance is judged by "zero references", not by an arbitrary total.

- **Wrapped component layer `assets/lecture-template/src/components/` (new, 10 files, 29 components)** — the single entry point for scenes. The libraries provide structure; this layer provides skin and frame-driven adaptation, reads colours / borders / shadows only from `THEME`, and makes every animation a pure function of the frame number.
  - `ui.tsx`: `Accordion`, `Tabs`, `ControlStack` (switch / checkbox / radio / slider / segmented / progress, state driven by an explicit `steps: [{at, value}]` table), `HighlightCode`, `MathBlock` (KaTeX), `TopicIcon` / `IconWall` (react-icons, `fa` + `fi` + `lu`).
  - `chart.tsx`: `Chart` (seven variants: `line` / `area` / `stack` / `stackExpand` / `stream` / `radar` / `pie`, plus a `csv` entry point), `StatRow`.
  - `data.tsx`: `TreeView` (`tree` / `treemap` / `pack` / `sunburst`), `GeoView`, `SankeyChart`, `QrCode`, `fitNodeLabel` / `fitOneLine`.
  - `overlay.tsx`: `OverlayFrame` (`dialog` / `menu` / `popover` / `tooltip`; the Radix portal container is pinned to the picture root).
  - `network.tsx`: `NetworkGraph` (d3-force, with explicit initial values, a fixed iteration count and an immediate `.stop()`).
  - `sketch.tsx`: `SketchFx` / `sketchCircleArea` / `sketchUnderline` / `sketchBox` (roughjs).
  - `effects.tsx`: `GlowFrame` / `ShimmerText` / `ClipReveal` / `NoiseJitter` / `VerdictBar` — all zero-dependency, CSS/SVG maths plus the frame number.
  - `pathfx.tsx`: `PathDraw` / `MorphShape` / `ShapeDraw` / `SHAPES` / `SceneTransitions` (20 official presentations).
  - `fittext.tsx`: `FitTextBox` / `fitChineseTextOnNLines` / `assertFits` / `fitsWithin`.
  - `focus.tsx`: `FocusFx` (the attention trio: dim / spot / loupe / marker).

- **Type checking for the template** — adds `assets/lecture-template/tsconfig.json`, a `typescript` devDependency and `npm run typecheck` (`tsc -p tsconfig.json`, `noEmit` on). The template bundled but was never type-checked, so the whole "it runs, so it must be fine" class of defect could never be seen.

- **Two render-time gates ported into the template and wired up** (they already existed in the production project):
  - `assets/lecture-template/src/clipping-gate.tsx`: clipped graphics — an SVG/graphic element's real rect escaping its nearest clipping ancestor (an HTML ancestor with `overflow≠visible`, or the enclosing `<svg>` viewport; an explicit `overflow:visible` svg is judged by computed style and does not count). `CardFitGate` only covers text inside div/span, `OverlapGate` only covers text-on-text, and neither can see "half a ball missing".
  - `assets/lecture-template/src/fill-gate.tsx`: measured density of the lower quarter — the lowest edge of the union of information elements (text, border or stroke) against y=876 (±24 tolerance), skipping subtrees at z≥140.
  - Wiring contract: the design root gains `data-design-root` (`FillGate` folds output pixels back to design pixels through it; without it the gate silently returns), and both gates join the `WATCH` sampling in `index.tsx`.

- **`WATCH` sampling now includes the settle frame `to−12`** — the project defines the settle frame as shot end minus 12, which is generally not a multiple of 15 and not an event frame. Before this change only one of 21 settle frames was inside the sampling set.

- **Post-render gate `scripts/validate-motion-gaps.py` (new)** — `ffmpeg freezedetect` compares frame by frame; consecutive "nearly identical" runs past the threshold are P0. The subtitle band must be cropped away first, otherwise per-character subtitles mask every static passage (on the same film: 73 segments reported at full frame with S19's 2.5 seconds absent; 53 segments after cropping, with S19 clearly surfaced).

- **Presentation gate `scripts/validate-presentation.py` (new) and its reference `references/presentation-gate.md` (new)** — every existing gate asked "is it there / is there enough of it / does it collide"; none asked "where should the viewer look right now, and can they read it in time", which made "five equally sized headings side by side", "11px body text" and "grey text on grey" all legal. New criteria: G-1 beat timing (a beat must land inside the line/shot it declares, no earlier than 12 frames before it and no later than 8 frames after it ends; every cue needs at least one beat); G-2 caption reading budget (≤9 weighted characters per second, ≤16 per line, ≤2 lines; CJK counts 1, ASCII 0.5); G-3 legibility (`fontSize < 13` is P0; body-colour contrast below 4.5:1 is P0, WCAG 2.2 SC 1.4.3); G-5 beat crowding (P1).

- **Narrative-field gates G-14 / G-15 / G-16 and `references/narrative-moves.md` (new)** — `move` must be one of ten names, `evidence` is required, `hold` must not fall below the 40-frame calibration line, and `misconception` and `noMisconception(+why)` are mutually exclusive. This also fixes `resolve-shots.py`, which dropped the whole `move` / `evidence` / `hold` / `misconception` group, so downstream gates reading `resolved` could not see those fields at all.

- **Two new build-time criteria**:
  - `validate-composition.py` gains **P0-7, beat index out of range**: scene sources are scanned for both `b[k]` and `SHOTS.Sx.beats[k]` spellings, and `k` must be below the real beat count; references to non-existent shots are reported too. An out-of-range index yields `undefined`, which either throws per frame inside `interpolate` or makes the element never appear.
  - `validate-shot-motion.py` gains a beat-gap P1 (`BEAT_GAP_MAX_RATIO = 0.60`, calibrated offline before the threshold was chosen).

- **Five text-safety colours per theme** — `blueInk` / `orangeInk` / `greenInk` / `goldInk` / `redInk` (the same hue darkened by solving for WCAG), with `ThemePalette` in `theme/types.ts` extended accordingly. The convention is written into `references/theme-system.md`: the original accents are for fills and strokes only, and text always uses the matching ink variant. `validate-presentation.py` enforces both halves as a self-check on the new mechanism.

- **CI now runs the template's gates** — `.github/workflows/validate.yml` gains three steps: the six build-time gates on the default template, `negative-gate-check.py`, and `coords-lint.py`. CI previously ran no gate at all, so the "negative spot-check" was a local ritual.

- **Negative fixtures 23 → 28** (`scripts/negative-gate-check.py`): X (a narrative field missing `move`), Y (`*Ink` safety colour against white), Z1–Z3 (beat index out of range: the local alias `b[9]`, the full path `SHOTS.S2.beats[9]`, and a negative control). A criterion added without a fixture means that gate still only exists on paper, so criteria and fixtures ship together.

- **Dependencies installed** — `assets/lecture-template/package.json` grows from 5 dependencies (and no devDependencies) to 37 + 10:
  - UI and structure: 12 Radix primitives, `react-icons`, `react-syntax-highlighter` `^16.1.1`.
  - Data and graphics: `d3-scale` / `d3-shape` / `d3-hierarchy` / `d3-geo` / `d3-sankey` / `d3-dsv` / `d3-force`, `roughjs`, `qrcode`, `katex`.
  - Text: `budoux` (Chinese phrase-based line breaking) and `@cto.af/linebreak` (UAX #14). The first attempt used foliojs `linebreak@1.1.0`, which pins `base64-js@0.0.8` (2014) and stopped shipping in 2022; it was replaced with the modern implementation, with identical break positions across the same test set and no behaviour change.
  - Six official `@remotion/*` extensions: `transitions`, `paths`, `shapes`, `motion-blur`, `layout-utils`, `noise`.

- **Contact sheet 9 → 17 pages** (`SHOWCASE_PAGES`, `SHOWCASE_VERSION` moving to `showcase-v8`).

- **The locked aesthetic system gains an eighth editable surface** (`references/official-aesthetic-system.md`) — the wrapped component layer under `src/components/` is explicitly editable: reach for a ready-made wrapped component before hand-writing SVG. The component layer was absent from the previous seven, and the signal the AI read was "components are not mine to touch".

### Changed

- **The "zero dependency" wording in `SKILL.md` (three places)** — the introduction gains a boundary statement (paid generative models are banned, open-source libraries are not; hand-writing every UI element is not a goal but the slowest route to a worse result); the Zero-Mutation section splits "dependencies" into two disciplines (libraries already in the template may be imported directly with no authorisation; only new ones outside the list need approval); and "`scripts/*.py` has zero third-party dependencies" is explicitly scoped to the Python scripts. The leftover "zero dependency" slogans in `references/fxkit.md`, `README.md` and `src/insert.tsx` are removed — the whip transition comment in `insert.tsx` now points at the bundled `@remotion/motion-blur` — and the README FAQ gains a question about open-source UI libraries (yes, and encouraged).

- **Component cleanup: 49 → 45** — 23 components that never appeared in any picture were deleted and 19 wrapped components added. Deletion was driven by a per-component audit of real JSX renders rather than import statements; `AIChatBox` (315 lines), the largest component in the library and the headline feature of v3.0.3, had never entered a single frame. Everything deleted can be recovered from git history.

- **Two naming collisions, both of which fail silently** — the new layer's code-block component was also called `CodeBlock`, colliding with the existing same-named component in `toolkit.tsx` and failing at render time when silently shadowed, so it became `HighlightCode`; the new layer's `RevealMask` collided with `insert.tsx`'s `RevealMask` and became `ClipReveal`.

- **Determinism claims narrowed** — stills and PNGs are byte-for-byte reproducible; long mp4 segments are only guaranteed to be visually equivalent. Rendering the same tree twice for 900 frames produced a different md5 every time (`3f5557ad` / `2ad431d5` / `11a88601`), with the pixel differences confined to a few points at the edges (max 76, mean 0.12, 95.2% of bytes identical) — an x264 encoding artefact, not a content difference. Both READMEs were rewritten accordingly.

- **Gate counts** — `SKILL.md`'s frontmatter description moves from `nine` to `thirteen`; the gate table in `README.md` / `README.en.md` moves from nine to ten; `.github/repository-metadata.yml` moves from `8 automated gates` to `10`.

- **`bottomFill` downgraded at build time** — `validate-composition` used to assert `bottomFill == true`, but that field is a constant the shot-table generator writes itself and `resolve-shots` passes through unchanged: the generator writes `true`, the gate demands `true`, and the check is structurally incapable of failing (17 of 21 shots in the finished film had an empty lower quarter and it never fired once). It now only checks that the field is present, and the real criterion lives in the render-time `FillGate`; the sibling `bottomFill is False` branch in `validate-shot-motion` is downgraded the same way, and the rationale is written back into `references/composition-gate.md` (P0-4), `references/scene-skeletons.md` and item 16 of `SKILL.md`.

- **Gate renumbering** — the narrative-field group was labelled `G-6`, but `G-6` is "contrast-layer structural closure" in the research report (still unimplemented). Per `references/narrative-moves.md` §4 the group is now **G-14 `move` closure / G-15 `evidence` actually used / G-16 misconception and deliberate silence**.

- **Template `tsc` cleared to zero errors: 19 unused imports or dead variables plus one TS2367** — what it surfaced was not tidiness but a batch of silent failures (arguments the library ignored, or references to names that do not exist; none of them error at runtime): `ShapeInfo` imported from a deep path in `@remotion/shapes` although the type is not exported from the package root; four wrong `SHAPES` arguments (`makeCallout`'s `pointerBaseWidth`, `makeHeart`'s `height`+`aspectRatio`, `makeEllipse`'s `rx`+`ry`, `makeTriangle`'s required `direction`); `pushCut` receiving a `direction` it does not have; `fitsWithin` in `ui.tsx` never imported (and gated behind `NODE_ENV !== 'production'`, so it could never run on the delivery path); `shotkit.tsx` declaring `head`/`tail` as `CamKey[]` while assigning a keyframe object, which made `shotCam` return a nested array that `camAt` then read as garbage; and `FitCard` in `scenes.tsx` receiving an unknown `f={f}` prop (React silently drops unknown props). Three fake knobs (unused `lift`, `from` / `to` parameters) keep their types but are no longer declared in the implementation, so they no longer look adjustable. `Film4x3` / `Film3x4` are exported per the contract in `references/canvas-modes.md` ("defined but not registered by default") so that `noUnusedLocals` does not treat them as dead code.

- **`useSteppedFrame` restored to a layer scenes can import** — `references/motion-design.md` teaches authors to use `useSteppedFrame(15)` but no implementation existed anywhere. The fix was to put the API back in `toolkit.tsx` rather than delete the documentation (stop-frame motion is a legitimate sticker-style technique), with two entry points: the pure function `stepped(f, 15)` when a component receives shot-local frames, and `useSteppedFrame(15)` for components that take no frame argument.

- **`popS` / `SPRINGS` exported from `fxkit.tsx`** — the discipline stated in `motion-design.md` was previously unenforceable, because both names existed only as private module-level definitions and scene files could not physically import them.

- **Routing table reduced to one first choice per row** — rows used to list three or four peer options (for example "data / comparison" listing `Chart` + `ProgressRing` + `MetricGrid` together), which is the same as giving no advice. The alternatives now carry a "only when" note, and the table header records the lesson: a named component in the routing table will still go unused — 23 components never appeared in any picture, and 21 of them were already registered in that table.

- **Lockfile regenerated and both lockfiles aligned** — the template lockfile mixed Remotion family versions (`remotion` / `@remotion/cli` / `@remotion/media` at 4.0.489 while `@remotion/transitions` and others were 4.0.526), which Remotion does not support since it requires one version across the family. After regeneration all 33 family packages are 4.0.526, and the resolved direct dependency versions in the two lockfiles now match exactly; the remaining formal difference (caret in the template, exact in the validation project) is deliberate.

- **`HighlightCode` switched to `PrismLight`** — from a full-language build to six languages registered on demand (tsx / ts / python / bash / json / diff, with aliases): 277 language files and 0.83 MB under `refractor/lang` down to 8 files and 30 KB.

- **Mixed-script line breaking now uses UAX #14** — `fittext.tsx` used to implement 避头尾 with two hand-written character tables (`NO_LINE_START` / `NO_LINE_END`), which measurement showed to be a rough approximation that fails specifically on mixed Chinese/Latin text: across ten real strings the tables allowed **36 illegal break points** (`在G|itHub`, `hyt|315`, `第三个A|I技能`, `S|1：` …) where UAX #14 allows zero, while pure-Chinese cases are identical under both.

- **Documentation synchronised** — `references/fxkit.md` rewritten with a section for the wrapped layer, `references/media-routing.md` purged of deleted components, `references/official-aesthetic-system.md` extended with the component layer and the icon policy, and the gate lists in `SKILL.md` / `README.md` / `README.en.md` updated with `ClippingGate` / `FillGate` / `validate-motion-gaps`.

### Fixed

- **`OverlapGate` reworked from "never blocked once" into a gate that really blocks (four silent failures and one structural blindness)**:
  - No `delayRender`: measurement ran inside `requestAnimationFrame`, which Remotion does not wait for, so the gate had never been on the render path. It now holds a handle per sampled frame and only calls `continueRender` after measuring.
  - A bare `return` while fonts were loading: on the real render path `document.fonts.status` is permanently `'loading'`, so every frame returned at that line (the re-rendered log did not even contain a coverage line). It now waits for `document.fonts.ready`.
  - All three sample points sat on the vertical centre line of the text box, so S14's "popover title bar cuts the lower half of the body text" was missed (ink at 685..703, the cut at 702, the centre line at ~699 — just above the cut). Two height levels at 22% and 78% were added for five points in total.
  - The hard block was swallowed by the gate's own catch handler: `cancelRender()` is implemented as `throw`, the old `catch (e) { console.warn(e) }` swallowed it, execution then reached the trailing `release()`, the handle count returned to zero and the renderer saw "ready" — a hard block that still produced an image with `rc=0`. Now `blocked` is latched, the handle is never released and the exception propagates unchanged.
  - **`INVISIBLE_CHARS` was missing the `u` flag**: the pattern was parsed as `\uf000` + `0` + `-` + `\uffff` + `d`, which silently added **U+0030–U+FFFF (65 488 code points)** to the character class — every Chinese character, digit and most printable ASCII was replaced with an empty string. The consequence was structural blindness: text leaves made entirely of Chinese never entered `texts` (in a finished film, all 87 caption strings were emptied and the coverage line reported only 2 text blocks measured per frame). The fix restores the `u` flag and writes the supplementary planes as `\u{…}`, plus a startup self-check that warns loudly when `visibleText('重A0') !== '重A0'`.

- **`CardFitGate` / `CaptionFitGate` given the same treatment** (`assets/lecture-template/src/index.tsx`) — their ability to block was a structural coincidence (`continueRender` happened to sit inside the `try` block after `cancelRender`), and they now latch `blocked` and let the exception through like every other gate.

- **`FocusFx` dimming reworked around three causes**:
  - The colour was paper on paper: `background: C.paperBase` drew nothing on a paper ground (bright ground 249.2 → 247.4; mid grey 128 → 214, i.e. brighter). It now uses `muted` with `multiply`: bright ground → 146.8, mid grey → 76.1.
  - It was not an overlay: the original had only `position:absolute` and no z-index, so being written before the content meant being covered by it. A `SCENE_ANCHOR` was added.
  - Coordinates drifted with the host: the comment promised `rect` was in scene coordinates, but the implementation resolved against the nearest positioned ancestor, so inside a wrapper at `left:200,top:300` the veil slid off the top-left of the canvas (measured 247.3 at x=60 on the left edge, i.e. not covered at all). `SCENE_ANCHOR` uses `position:fixed` to pin the coordinates back to scene space.

- **`FocusFx`'s `zIndex` lowered from 9000 to 160, so the veil no longer covers subtitles** — the previous release made the veil an overlay at 9000, which placed it above `SubtitleChrome` (z=200), and S8's subtitles were dimmed by the same `multiply` step (glyph core 25.1 → 15.1, i.e. ink × 0.594) — exactly what the comment in `focus.tsx` promised would not happen. The value now follows the film's layer ladder: scene content ≤130 → header 140 / chapter card 150 → veil 160 → grade 190 → subtitles 200. Measured on the same frame 2360: the six-point mean of the subtitle glyph core returns to 26.2 (from 27.5 before the fix), the corners outside the hole are still dimmed at 146.1–150.7, the hole's interior averages 216.0, and its boundary still lands at output 540/753/460/620.

- **A batch of silent failures where arguments were passed and the library ignored them** (surfaced by `tsc`; itemised in the Changed section above).

- **`assertFits` was a gate in name only** — it was defined and never called by any code. A new `fitsWithin()` performs the same real `measureText` measurement but only warns, and it is wired into the two components that genuinely combine fixed-size cards with variable copy (`StatRow` and `VerdictBar`), running in development only with zero cost in production; `assertFits()` remains as an authoring-time self-check and is no longer described as an automated gate.

- **`coords-lint.py` missed an entire layer** — it only scanned `src/*.tsx`, while the wrapped component layer lives in `src/components/`, so the whole new layer was outside coordinate checking. It now recurses, and the `OVERLAYS` list is derived from `src/components/** + src/theme/**` (taking only components with scene-coordinate semantics).

- **`validate-frame-props.py` was ineffective for the whole `src/components/` layer** — its list named four files that no longer existed and it did not recurse (parsed components 65 → 88).

- **`import_integrity` had been described as done but was not** — it now really recurses over `src/**` (.ts/.tsx), understands `./x`, `../x` and directory barrels (`./components` → `components/index`), follows `export *`, and separates "re-exported from an npm package" from "name does not exist" (the former must not be reported, or the whole chain becomes false P0s). Measured on the template: 30 files and 78 relative imports → P0=0, and it immediately caught one real gap.

- **Contact-sheet rendering defects** — `DiffView` had always failed to render there (its sample data omitted the `at` field on the first row, and `undefined` reached `spring({frame})`); `Chart`'s `d3line(...)` still received the old `data` variable, so the `csv` entry point fed `undefined` into `d3-shape`; `TreeView`'s `viewBox` clipped the root node's top edge; and `SketchFx` accumulated strokes on every redraw because roughjs appends to the DOM (it now clears before drawing).

- **A batch of chart and hierarchy defects that do not error but draw wrong** — `treemap` / `pack` / `partition` shared one `hierarchy()` root so later layouts overwrote earlier ones; `d3.arc`'s default accessors did not match partition nodes, so the sunburst drew no rings at all and reported nothing; `d3stack` needed an explicit transpose; `TreeView` checked label width but not height; the sunburst's label orientation and its lower-half flip; the `pie` variant taking a whole column as one sector; and an over-tight radar radius. A second verification pass fixed three more: sunburst labels overflowing on a single line (two lines assumed, one drawn), network node labels split across two lines, and the area chart's first data point label landing on the Y axis tick.

- **`fillStyle:'dots'` made a whole page irreproducible** — the same frame rendered three times produced three different hashes, with the difference always in the dots tile of contact-sheet page ⑭. The cause was inside roughjs: its dots filler calls `Math.random()` twice per point in `dotsOnLines`, independent of `seed`. `'dots'` was removed from `SketchStyle.fillStyle` and the tile switched to deterministic `'dashed'`; a guard was added as well, because `seed: 0` is falsy and roughjs writes its LCG as `this.seed ? … : Math.random()`, so a falsy seed now prints a clear warning and falls back to `seed=1`.

- **Dead TS2367 comparison in `index.tsx`** — `s.cameraIntent !== 'still'` was always true (`shots.ts` emits only five intents and the type has no `'still'`), so "no click sound for a static shot" excluded nothing. It became a positive `CAM_MOTION` list, where values not on the list (including a future `still`) get no sound; the comparison was not simply deleted, since that would add sound to static shots.

- **`ShotIntent` was missing `'still'`** — the type did not include it while `stillCam`'s comment stated it was a legal choice. It was added to the union, which is also the root cause of the always-true comparison above.

- **A comment in `fxkit.tsx` that contradicted the file** — it claimed the two local helpers `q` and `ease` had never been used "from the top of this file to the bottom", while `easeOutSoft` / `SPRINGS` / `popS` right below it are used a dozen times. It now says it means those two, and explicitly marks the three below as in use and not to be deleted together.

- **Version numbers disagreed** — `SKILL.md`'s frontmatter still said `3.0.3` and `README.md` still said "current v3.0.2" while the CHANGELOG had reached 3.1.0; all three are now **3.1.0**.

- **Deleted component names left behind in documentation (about 30 places across 8 files)** — the most dangerous kind instructs an executing AI to import a component that no longer exists: `shot-language.md` contained `import {..., DepthLayers} from './shotkit'` and a whole `<DepthLayers>` example; `fxkit.md` still listed `BrowserChrome` / `Mascot` and had a section on the deleted `ShotPlate`; seven rows of `media-routing.md`'s "rhetorical move → component" table still recommended deleted components; and the file trees in `README.md` / `README.en.md` still listed the deleted `plates.tsx`. A re-check shows no leftovers.

### Removed

- **23 components that never appeared in any picture** (across `fxkit.tsx` / `toolkit.tsx` / `insert.tsx` / `stagekit.tsx` / `shotkit.tsx` / `plates.tsx`), among them `AIChatBox` (315 lines), the largest component in the library and the headline feature of v3.0.3. Everything deleted can be recovered from git history.
- **`assets/lecture-template/src/plates.tsx` deleted entirely** (its only component, `ShotPlate`, never entered a frame).
- **Contact-sheet page ⑧ removed** (the whole page consisted of deleted components); the remaining pages were consolidated.
- **The hand-written 避头尾 character tables** (`NO_LINE_START` / `NO_LINE_END` in `fittext.tsx`), replaced by the UAX #14 algorithm.

---

## [3.0.3] - 2026-09-18

### 背景与动机

动机直接来自本版新增的代码与规范条目：① **缺少"AI 对话 / Prompt 交互"这一类内容的原生组件**——到此为止 fxkit 只有 `ChatThread`（简易气泡）与 `MailScan`（邮件），而"用户提问 → 模型思考 → 流式作答 → 追问 / 重写 / 纠错"是这类讲解片最常见的修辞动作，因此新增 `AIChatBox` 并在接触表与路由表里登记（`fxkit.tsx` 第 19 件、`media-routing.md` 两张表）；② **打字机的停顿不分级**——原实现对中英文标点用同一档停顿，读起来是机械线性吐字，因此把吐字与停顿抽成 `getStreamingSlice` 单一纯函数（句末深停顿、子句短顿挫），供 `Typewriter` 与 `AIChatBox` 共用；③ **左上角顶栏章节卡存在隐形空间碰撞**——新增 `coords-lint.py` 的 `VERIFY-TOP-CHROME` 告警，并在坑表里立为第 11 条；④ **元素满屏瞬出退化成 PPT**——在坑表里立为第 12 条铁律（台词节拍阶梯涌现）。

### 新增

- **`AIChatBox` 拟真 AI 对话交互框（fxkit 第 19 件）** —— 端到端的对话介质组件：macOS 三色灯标题栏 + 标题 + 模型药丸徽章（默认 `DeepSeek-V3 · 活人模式`）+ ONLINE 脉冲指示灯；消息区按 `msgs[{side,text,at,cps,thinkingDur,strikethrough,strikethroughAt,tag}]` 渲染，用户 / AI 两侧头像与气泡，`thinkingDur` 内显示三点思考动画，之后用 `getStreamingSlice` 逐字吐字并跟一枚闪烁光标；`strikethrough` 在估时后画出动态划除线（标 `data-gate-allow="strikethrough"`，`scaleX` 推进），完成态以 ✓ / ✗ 徽章区分；底部为提示词输入条与 `SEND ↵`。默认 900×460、`zIndex 75`，支持 `start` / `exitStart`，帧参数名为 `frame`。`assets/lecture-template/src/fxkit.tsx`
- **`getStreamingSlice(text, f, start, cps)` 流式吐字纯函数** —— 把"字符预算 + 标点长短停顿"抽象成单一实现：句末标点（`。！？!?` 与换行）记深停顿（`5.5×cps + 1.2`），子句标点（`，、；;:,`）记短顿挫（`2.5×cps + 0.6`），返回 `{shown, isDone, currentText}`；`Typewriter` 与 `AIChatBox` 共用同一套节奏，避免各写一套。`assets/lecture-template/src/fxkit.tsx`
- **接触表第 4 页收录 `AIChatBox`** —— Page 4 新增 `AIChatBox` 演示格（一段"把技术说明重写成活人感 → 划掉八股 → 人话重写"的两轮对话），原 `ChatThread` 与 `MailScan` 合并为一格；页数仍为 9，`SHOWCASE_VERSION` 由 `showcase-v2 · 9 pages · 30 components` 升级为 `showcase-v3 · 9 pages · 31 components + 6 intents + 4 skeletons`。`assets/lecture-template/src/showcase.tsx`
- **`coords-lint.py` 顶栏保留区告警** —— `OVERLAYS` 名单加入 `AIChatBox`；对 `AIChatBox` / `ChatThread` 的 `y={n}`（0 < n < 170）输出 `VERIFY-TOP-CHROME` 警告，提示顶栏章节卡占用 `x: 92..484, y: 74..164`，需警惕遮挡。`scripts/coords-lint.py`
- **规范补两条** —— `references/scene-authoring.md` 坑表 10 → 12 条：**Pit #11**「场景标题 / 顶层卡片与左上角章节卡撞车」——修法是标题放进 `StageFrame` 的槽由引擎统一管理，或独立元素保持 `y >= 170`；**Pit #12**「卡片 / 文字满屏瞬间全出、退化成 PPT」——立为铁律：必须与分镜表的 `beats` 强绑定，随旁白语流逐项点亮与吐字（`start={at(i)}`）。`references/scene-authoring.md`
- **介质路由表登记 `AIChatBox`** —— 内容介质路由表新增"对话 / 交互 / 提示词"一行；选型表新增"模拟 AI 对话 / Prompt 交互"一行（首选 `AIChatBox`，备选 `ChatThread`，并注明对话条数建议 2–3 条以避免溢出窗口高度）。`references/media-routing.md`

### 变更

- **`Typewriter` 改用分级停顿并新增排版开关** —— 吐字与停顿改调 `getStreamingSlice`（由"单档标点集合 + 固定停顿"改为"句末深停顿 / 子句短顿挫"两档）；默认 `cps` 由 0.4 提到 0.45；新增 `multiline`（`whiteSpace: pre-wrap`，多行排版）与 `cursorSticky`（打完后光标保持）两个开关，光标显示条件改为 `cursor && (!isDone || cursorSticky)`；外层 `span` 加 `display: inline-block`，光标尺寸由 `0.5 × 1.05` 收到 `0.48 × 1.02`、左边距 6 → 4。`assets/lecture-template/src/fxkit.tsx`
- **`references/fxkit.md` 同步** —— 组件数 18 → 19（版本行改为 v3）、示例 import 加入 `AIChatBox`、参数名对照表与组件表各补一行（拟真对话框、关键 props 与 `frame`）。`references/fxkit.md`
- **版本与元数据** —— `SKILL.md` 版本 3.0.2 → 3.0.3（frontmatter）；`manifest.json` 版本 3.0.2 → 3.0.3、`updated_at` 由 2026-09-09 更新为 2026-09-18；`.github/repository-metadata.yml` 的 `release.tag` / `title` 更新为 v3.0.3。`SKILL.md`、`manifest.json`、`.github/repository-metadata.yml`

**English**

### Background

The motivation comes directly from the code and specifications this release adds: (1) **there was no native component for "AI dialogue / prompt interaction"** — fxkit had only `ChatThread` (simple bubbles) and `MailScan` (email), while "user asks → model thinks → streams an answer → follow-up / rewrite / correction" is the most common rhetorical move in this kind of explainer, so `AIChatBox` is added and registered in the contact sheet and the routing tables (the 19th fxkit component; both tables in `media-routing.md`); (2) **the typewriter did not grade its pauses** — the previous implementation used one pause tier for all punctuation, which reads as mechanical, so character output and pauses are extracted into the single pure function `getStreamingSlice` (deep pause at sentence end, short beat at clause boundaries) shared by `Typewriter` and `AIChatBox`; (3) **the top-left chapter card has an invisible collision zone** — a `VERIFY-TOP-CHROME` warning is added to `coords-lint.py` and recorded as pit #11; (4) **elements appearing all at once degrade into a slide deck** — recorded as iron law #12 in the pit table (cue-beat staggered reveal).

### Added

- **`AIChatBox`, a realistic AI dialogue box (fxkit's 19th component)** — an end-to-end dialogue medium: a macOS-style three-light title bar with a title, a model pill badge (default `DeepSeek-V3 · 活人模式`) and an ONLINE pulse indicator; the message area renders `msgs[{side,text,at,cps,thinkingDur,strikethrough,strikethroughAt,tag}]` with avatars and bubbles on both sides, a three-dot thinking animation for `thinkingDur`, then per-character streaming via `getStreamingSlice` with a blinking cursor; `strikethrough` draws an animated strike line after an estimate (marked `data-gate-allow="strikethrough"`, advanced with `scaleX`); the finished state is shown as a ✓ / ✗ badge; the footer holds a prompt input bar and `SEND ↵`. Defaults to 900×460 at `zIndex 75`, supports `start` / `exitStart`, and takes its frame as `frame`. `assets/lecture-template/src/fxkit.tsx`
- **`getStreamingSlice(text, f, start, cps)`, a streaming-text pure function** — it abstracts "character budget plus graded punctuation pauses" into one implementation: sentence-final punctuation (`。！？!?` and newlines) costs a deep pause (`5.5×cps + 1.2`) and clause punctuation (`，、；;:,`) a short beat (`2.5×cps + 0.6`), returning `{shown, isDone, currentText}`; `Typewriter` and `AIChatBox` share one rhythm instead of each carrying its own. `assets/lecture-template/src/fxkit.tsx`
- **`AIChatBox` on contact-sheet page 4** — page 4 gains an `AIChatBox` cell (a two-turn "rewrite this technical text with a human voice → strike out the boilerplate → plain-language rewrite" dialogue) while `ChatThread` and `MailScan` merge into one cell; the page count stays at 9 and `SHOWCASE_VERSION` moves from `showcase-v2 · 9 pages · 30 components` to `showcase-v3 · 9 pages · 31 components + 6 intents + 4 skeletons`. `assets/lecture-template/src/showcase.tsx`
- **A top-chrome reserved-zone warning in `coords-lint.py`** — `AIChatBox` joins the `OVERLAYS` list, and a `y={n}` between 0 and 170 on `AIChatBox` / `ChatThread` now prints `VERIFY-TOP-CHROME`, pointing out that the chapter card occupies `x: 92..484, y: 74..164` and that occlusion should be checked. `scripts/coords-lint.py`
- **Two new specifications** — `references/scene-authoring.md`'s pit table grows from 10 to 12 entries: **pit #11** "a scene title or top-level card collides with the top-left chapter card" — fixed by putting the title into the `StageFrame` slot for the engine to manage, or by keeping standalone elements at `y >= 170`; **pit #12** "cards and text appear all at once, degrading into a slide deck" — an iron law: bind to the shot table's `beats` and light items up and type them out with the narration (`start={at(i)}`). `references/scene-authoring.md`
- **`AIChatBox` registered in the routing tables** — the content-medium table gains a "dialogue / interaction / prompt" row, and the selection table gains a "simulate AI dialogue / prompt interaction" row (first choice `AIChatBox`, fallback `ChatThread`, noting that two to three exchanges are recommended to avoid overflowing the window height). `references/media-routing.md`

### Changed

- **`Typewriter` moves to graded pauses and gains layout switches** — output and pauses now call `getStreamingSlice` (one punctuation set with a fixed pause becomes two tiers: deep at sentence end, short at clause boundaries); the default `cps` rises from 0.4 to 0.45; two switches are added — `multiline` (`whiteSpace: pre-wrap`) and `cursorSticky` (keep the cursor after completion) — with the cursor shown when `cursor && (!isDone || cursorSticky)`; the outer `span` gains `display: inline-block`, and the cursor shrinks from `0.5 × 1.05` to `0.48 × 1.02` with its left margin going from 6 to 4. `assets/lecture-template/src/fxkit.tsx`
- **`references/fxkit.md` updated** — the component count goes from 18 to 19 (version line to v3), the import example gains `AIChatBox`, and both the frame-prop table and the component table gain a row (the realistic dialogue box, its key props and `frame`). `references/fxkit.md`
- **Version and metadata** — `SKILL.md` moves from 3.0.2 to 3.0.3 (frontmatter); `manifest.json` moves from 3.0.2 to 3.0.3 with `updated_at` refreshed from 2026-09-09 to 2026-09-18; `.github/repository-metadata.yml`'s `release.tag` / `title` become v3.0.3. `SKILL.md`, `manifest.json`, `.github/repository-metadata.yml`

---

## [3.0.2] - 2026-09-11

### 背景与动机

本版给 3.0.1 收尾：3.0.1 把 11 件修辞工具组件迁出并 export，但它们**一件都没被渲染过**——接触表里一页都没有（`showcase.tsx` 注释），模板里也没有一处使用，等于"能 import 却没人用"。同时修掉这一轮改动（实渲 + 交叉复核）抓到的缺陷，其中两条写在代码注释里：修 `ZoomStage` 假阳性时第一版用了 `closest('[data-fit-skip]')`，而 `closest` 会向上遍历，把取景框内所有后代卡片的真实裁切一起放过（复核用 A/B 实渲证明 248px 的裁切被漏检）；以及章节卡（z=150）此前被 `CardFitGate` 静默跳过，于是"章节标题太长被裁"从来没有任何门禁报过警。

### 新增

- **`Callout` / `Checklist` 真正用进官方模板** —— S1 用 `Callout` 圈住控制台里的那一行并配手写标注"还躺在硬盘里"（`x=14, y=124, 296×40`，标注偏移 330px）；S3 的 `FitCard` 里"三步路径"改用 `Checklist`（带序号圆牌），**换掉原先手写的三行 `CheckBadge`**（加组件＝换掉一个元素，不是往里堆）。分镜表与 `shots.ts` 的 `live` 同步声明 `Callout` / `Checklist`。`assets/lecture-template/src/scenes.tsx`、`manifests/shots.json`、`src/shots.ts`
- **接触表补 3 页（⑦⑧⑨）** —— 11 件修辞工具件首次被渲染：⑦ `Callout` / `Connector` / `Checklist`，⑧ `CountUp` / `ProgressBar` / `RollDigit` / `BrowserChrome`，⑨ `JumpInText` / `WaveText` / `Mascot` / `CodeBlock`。`SHOWCASE_PAGES` 6 → 9，`SHOWCASE_VERSION` 由 `showcase-v1 · 6 pages · 16 components` 改为 `showcase-v2 · 9 pages · 30 components`；补页当场发现 `WaveText` 丢空格（见修复）。`assets/lecture-template/src/showcase.tsx`
- **CLI 登记两道构建期门禁** —— `scripts/notebook-video.mjs` 的 `pythonCommandMap` 与 `--help` 文本补上 `validate-frame-props` 与 `validate-audio-levels`（此前只能直接 `python scripts/…` 调用，CLI 里点不到）。`scripts/notebook-video.mjs`

### 变更

- **`CardFitGate` 的 z 分档重排** —— z ≥ 200 仍跳过（字幕归 `CaptionFitGate` 量），**z 145–199 改为量测并 warn**（章节卡内容溢出会打印 `章节卡内容溢出 Npx（标题过长？）`），z < 145 照常判卡片溢出。`assets/lecture-template/src/index.tsx`
- **章节卡与页眉防溢出** —— 章节卡高度 82 → 90（竖屏 76 → 84）、内边距收紧、内容块加 `minWidth: 0`；标题改为**按可用宽自适应字号**（可用内宽 286px / 竖屏 214px，CJK 记 1 单位、ASCII 与间隔号记 0.55 单位，字号夹在 `[19, TYPE.titleS]`）并禁止换行、超长裁切（注释记录：`TYPE.titleS = 27px` 时"第三步 · 运营与三技能"实算 282.96px，只差不到 1px 就会折行、折行即被框裁掉）；右上页眉加 `maxWidth` 与 `overflow: hidden`（1180px / 560px）。`assets/lecture-template/src/index.tsx`
- **`toolkit.tsx` 的弹簧参数与引擎对齐** —— `SPRINGS` 的 `snappy` 由 20/190 改为 16/200、`bouncy` 由 12/170 改为 11/160，与 `index.tsx` / `fxkit.tsx` 逐参数一致（迁移时写岔会让搬到本模块的组件动感偏移）。`assets/lecture-template/src/toolkit.tsx`
- **`validate-frame-props.py` 覆盖新模块** —— `ENGINE_FILES` 增加 `toolkit.tsx` / `plates.tsx` / `charts.tsx`；并加防呆：解析到的组件数 < 20 时打印原因并返回 2，**不给出 PASS**（此前遇到过"引擎源码没读到却报通过"的静默漏判）。`scripts/validate-frame-props.py`
- **README 补回引导性章节** —— 中英文 README 重新补上视觉成片与画幅、制作全流程、端到端实战演示、参考文档导读、文件结构、FAQ 与参与贡献（中文目录树里的版本行改为 v3.0.2）。`README.md`、`README.en.md`
- **文档与实现对齐** —— `fxkit.md` 接触表页数与构件计数（→ 9 页、30 件）、新增"修辞工具件"章节与 `hasAttribute` 逃生口说明；`SKILL.md` 澄清 `live` 断言的真实口径（门禁查的是"名字必须出现在场景源码里"）并补第 9 道门禁；`media-routing.md` 的组件分层清单补 `toolkit.tsx`；`composition-gate.md` 与 `locked-style-contract.json` 的转场清单收敛为三式；`motion-design.md` 的转场段改写为"`reveal` 由分镜表驱动、`handoff` 需要共享 carrier、`whip` / `paper-turn` 已删除"。`references/*`

### 修复

- **`CardFitGate` 的逃生口写法用错了（差点放过一整类真实裁切）** —— `card.closest('[data-fit-skip]')` 会向上遍历，挂在取景框上的标记会把框内所有后代卡片一起跳过；改为 `card.hasAttribute('data-fit-skip')`（只跳标记者自身）。复核的 A/B 实渲证明：故意塞一张竖向裁切的卡片，带 `closest` 时渲染通过（248px 真实裁切漏检），换成 `hasAttribute` 后立即被抓。`assets/lecture-template/src/index.tsx`
- **缩放容器在 `CardFitGate` 上假阳性** —— `ZoomStage` 的取景框是 `overflow: hidden` 且内部有 `scale()` 子层，`scrollWidth/scrollHeight` 必然大于自身（注释实测 `scrollWidth` 1093 vs `clientWidth` 996），那是"推近"本身的效果；给 `ZoomStage` 取景框与 `EvidenceZoom` 根标 `data-fit-skip`（容器的缩放溢出不再误报，框内卡片的真裁切照抓）。`assets/lecture-template/src/skeletons.tsx`、`src/fxkit.tsx`
- **`WaveText` 吃掉空格** —— 逐字 span 里的半角空格被 HTML 折叠，"OPEN SOURCE" 渲成 "OPENSOURCE"；改为与 `JumpInText` 一致的非断行空格（`ch === ' ' ? '\u00a0' : ch`）。`assets/lecture-template/src/toolkit.tsx`
- **回退 `Callout` / `Connector` 的 `data-gate-allow` 豁免（过度豁免）** —— `closest` 语义会让整棵子树退出重叠判定，连组件的标注文字一起豁免，违反仓库自己的白名单纪律；而画圈的两道椭圆是 `fill="none"` 的 SVG，`looksSolid` 本来就不会把它当遮挡物，这个豁免根本不需要。同时给 `Callout` 标注补 `'Caveat,Kai'` 字体回退（`Caveat` 只有拉丁字形，中文此前由浏览器挑默认字体）。`assets/lecture-template/src/toolkit.tsx`
- **`validate-composition.py` 在 Python 3.10 / 3.11 上直接 `SyntaxError`** —— 3.0.1 写入的一行 f-string 在表达式里复用了同种引号（PEP 701 只在 3.12+ 合法），而脚本与 `SKILL.md` 都声明支持 3.10+；已改为 `%` 格式化。`scripts/validate-composition.py`
- **`reveal` 核对不再误伤"只有分镜表"的工程** —— 3.0.1 加的这条 P0 在场景源码缺失时无从比对实现，却照样报"声明没兑现"，把负向抽查的阴性对照自己拦下（属 3.0.1 带出的缺陷）；改为与 `live` 名字同一口径（有源码才查）。同时把取镜代码块的窗口由"400 字符"改为"到本镜 `</Shot>` 为止"（注释记录实测窗口长 413，会越过边界吞掉下一镜），并把 `reveal` 的识别放宽为正则 `\breveal(?![A-Za-z0-9_$])`（仍排除 `revealAt` / `revealSpeed`，但允许 `reveal >` 与换行写法）。`scripts/validate-composition.py`
- **`.github/repository-metadata.yml` 的 `release.title` 被纠正** —— 由 "Notebook Video v2.9.0" 改为 "Notebook Video v3.0.2"（该字段在 3.0.0、3.0.1 两版一直没跟上 tag）。`.github/repository-metadata.yml`

**English**

### Background

This release closes out 3.0.1: that release moved the 11 rhetorical tool components out and exported them, but **not one of them had ever been rendered** — they had no page in the contact sheet (`showcase.tsx` comment) and no use in the template, so "importable" still meant "unused". It also fixes what this round (real renders plus cross-review) turned up, two of which are recorded in code comments: the first attempt at the `ZoomStage` false positive used `closest('[data-fit-skip]')`, and since `closest` walks upwards, a marker on the viewport exempted every descendant card from real clipping checks (cross-review proved a 248px clip slipped through in an A/B render); and the chapter card (z=150) had been silently skipped by `CardFitGate`, so "chapter title too long and clipped" had never been reported by any gate.

### Added

- **`Callout` / `Checklist` are actually used in the bundled template** — S1 uses `Callout` to circle the console line with the handwritten note "还躺在硬盘里" (`x=14, y=124, 296×40`, note offset 330px); S3's `FitCard` switches its three-step path to `Checklist` (numbered discs), **replacing three handwritten `CheckBadge` rows** (adding a component means replacing an element, not stacking another one). The shot table and `shots.ts` declare `Callout` / `Checklist` in `live`. `assets/lecture-template/src/scenes.tsx`, `manifests/shots.json`, `src/shots.ts`
- **Three more contact-sheet pages (⑦⑧⑨)** — the 11 rhetorical tools are rendered for the first time: ⑦ `Callout` / `Connector` / `Checklist`, ⑧ `CountUp` / `ProgressBar` / `RollDigit` / `BrowserChrome`, ⑨ `JumpInText` / `WaveText` / `Mascot` / `CodeBlock`. `SHOWCASE_PAGES` goes 6 → 9 and `SHOWCASE_VERSION` from `showcase-v1 · 6 pages · 16 components` to `showcase-v2 · 9 pages · 30 components`; adding the pages immediately exposed `WaveText` losing spaces (see Fixed). `assets/lecture-template/src/showcase.tsx`
- **CLI registers two build-time gates** — `scripts/notebook-video.mjs` adds `validate-frame-props` and `validate-audio-levels` to `pythonCommandMap` and to the `--help` text (they could previously only be run as `python scripts/…` directly, with no CLI entry point). `scripts/notebook-video.mjs`

### Changed

- **`CardFitGate`'s z bands were rearranged** — z ≥ 200 is still skipped (captions belong to `CaptionFitGate`), but **z 145–199 is now measured and warned** (chapter-card overflow prints `章节卡内容溢出 Npx（标题过长？）`), while z < 145 keeps the normal card-overflow judgement. `assets/lecture-template/src/index.tsx`
- **Chapter card and header made overflow-proof** — the chapter card grows from 82 to 90 in height (portrait 76 → 84) with tighter padding and `minWidth: 0` on the content block; the title now **auto-fits the available width** (286px available width, 214px in portrait; CJK counts as 1 unit, ASCII and the separator dot as 0.55, clamped to `[19, TYPE.titleS]`) with wrapping disabled and overflow clipped (the comment records that at `TYPE.titleS = 27px`, "第三步 · 运营与三技能" measures 282.96px — less than 1px from wrapping, and a wrapped line is clipped by the frame); the top-right header gains `maxWidth` and `overflow: hidden` (1180px / 560px). `assets/lecture-template/src/index.tsx`
- **`toolkit.tsx` spring presets realigned with the engine** — `SPRINGS.snappy` goes from 20/190 to 16/200 and `bouncy` from 12/170 to 11/160, matching `index.tsx` / `fxkit.tsx` parameter for parameter (the values drifted during migration, which shifts the feel of every component moved into this module). `assets/lecture-template/src/toolkit.tsx`
- **`validate-frame-props.py` covers the new modules** — `ENGINE_FILES` gains `toolkit.tsx` / `plates.tsx` / `charts.tsx`, plus a guard: fewer than 20 parsed components prints why and returns 2 **instead of a PASS** (a silent miss of this kind had been observed before). `scripts/validate-frame-props.py`
- **READMEs restored to a guided structure** — both READMEs regain the visual demo and aspect-ratio section, the production pipeline, a worked end-to-end example, the reference-document guide, the file structure, the FAQ and the contributing section (the Chinese tree's version line now reads v3.0.2). `README.md`, `README.en.md`
- **Docs aligned with the implementation** — `fxkit.md`'s contact-sheet page and component counts (→ 9 pages, 30 components) plus a new "rhetorical tools" section and the `hasAttribute` escape-hatch note; `SKILL.md` clarifies what the `live` assertion actually checks (the name must appear in the scene sources) and lists the 9th gate; `media-routing.md`'s layer inventory gains `toolkit.tsx`; `composition-gate.md` and `locked-style-contract.json` shrink the transition list to three; `motion-design.md`'s transition paragraph now reads "`reveal` is driven by the shot table, `handoff` needs a shared carrier, `whip` / `paper-turn` were removed". `references/*`

### Fixed

- **`CardFitGate`'s escape hatch used the wrong form (and nearly let a whole class of real clipping through)** — `card.closest('[data-fit-skip]')` walks upwards, so a marker on the viewport exempted every descendant card inside it; it is now `card.hasAttribute('data-fit-skip')`, skipping only the marked element itself. Cross-review's A/B render proved the difference: with a deliberately vertically-clipped card inside the viewport, `closest` rendered successfully (a 248px clip missed) while `hasAttribute` caught it immediately. `assets/lecture-template/src/index.tsx`
- **Scaling containers were false positives for `CardFitGate`** — `ZoomStage`'s viewport is `overflow: hidden` with a `scale()` layer inside, so `scrollWidth`/`scrollHeight` necessarily exceed it (`scrollWidth` 1093 vs `clientWidth` 996 in the comment), which is the push-in itself; `ZoomStage`'s viewport and `EvidenceZoom`'s root are now marked `data-fit-skip`, so a container's own zoom overflow is not reported while real clipping of the cards inside is still caught. `assets/lecture-template/src/skeletons.tsx`, `src/fxkit.tsx`
- **`WaveText` ate spaces** — a half-width space inside a per-character span is collapsed by HTML, rendering "OPEN SOURCE" as "OPENSOURCE"; it now uses a no-break space like `JumpInText` (`ch === ' ' ? '\u00a0' : ch`). `assets/lecture-template/src/toolkit.tsx`
- **The `data-gate-allow` exemption on `Callout` / `Connector` was rolled back as over-exempting** — `closest` semantics would have removed the whole subtree from overlap checking, including the component's own annotation text, violating the repository's own allow-list discipline; and since the two ellipses are `fill="none"` SVG, `looksSolid` never treated them as occluders, so the exemption was unnecessary. `Callout`'s note also gains a `'Caveat,Kai'` font fallback (`Caveat` covers Latin only, so Chinese previously fell to the browser default). `assets/lecture-template/src/toolkit.tsx`
- **`validate-composition.py` raised a `SyntaxError` on Python 3.10 / 3.11** — an f-string added in 3.0.1 reused the same quote character inside its expression (PEP 701 is only legal on 3.12+), while the script and `SKILL.md` both claim Python 3.10+; it now uses `%` formatting. `scripts/validate-composition.py`
- **The `reveal` check no longer punishes shot-table-only projects** — the P0 added in 3.0.1 could not compare against an implementation when scene sources were absent, yet still reported "declaration not honoured", which failed the negative spot-check's own clean control (a defect shipped in 3.0.1); it now follows the same rule as `live` names (checked only when sources exist). The same pass changes the shot-block window from "400 characters" to "up to this shot's `</Shot>`" (the comment records a measured window length of 413, which crossed the boundary and swallowed the next shot) and broadens `reveal` detection to the regex `\breveal(?![A-Za-z0-9_$])` (still excluding `revealAt` / `revealSpeed`, while allowing `reveal >` and line-broken forms). `scripts/validate-composition.py`
- **`release.title` in `.github/repository-metadata.yml` corrected** — from "Notebook Video v2.9.0" to "Notebook Video v3.0.2" (the field had lagged behind the tag through 3.0.0 and 3.0.1). `.github/repository-metadata.yml`

---

## [3.0.1] - 2026-09-11

### 背景与动机

本版在 3.0.0 之上做三件事，动机都写在本版新增代码的注释里：① **音效"几乎没有音效"的真因是双重衰减**——素材本身录得极轻（`paper-tap.wav` 峰值只有 −31 dB），再乘上混音音量后有效峰值被压到 −49 dB，而 BGM 一直在 −22 dB（`validate-audio-levels.py` 文件头注释）；② **可选组件"可选"不起来**——11 件修辞工具组件原本定义在 `index.tsx` 里且**没有 `export`**，场景文件在物理上无法 import，这正是"组件很多、成片里零使用"的结构性原因（`toolkit.tsx` 文件头注释）；③ **分镜表的声明可以不被兑现**——成片里出现过"表里声明 `handoff`、代码里从未实现"以及"表写 `cut`、代码写 `reveal`"（`validate-composition.py` 的"声明即承诺"注释）；音效钉帧也被钉在"镜头时长的 42%"，那一帧画面上什么都没有（`index.tsx` 的 SFX 注释）。本版不新增功能面，改动集中在"让已有的东西真的生效"：把可选组件真正变成可用词汇、把分镜表的声明变成必须兑现的约束、把听不见的音效修回来。

### 新增

- **音效电平门禁 `scripts/validate-audio-levels.py`（第 9 道门禁）** —— 用 ffmpeg 逐个量 `public/sfx/` 素材（`bgm*` 除外）的峰值：低于 **−12 dBFS** 即 P0（素材太轻，混音后必然被压住），并直接给出 `ffmpeg -af volume=…dB` 的归一命令；`index.tsx` 引用的 `sfx/xxx` 文件缺失也是 P0；缺 BGM、引用了音效却查不到任何 `vol:` 设定记 P1。`scripts/validate-audio-levels.py`
- **`src/toolkit.tsx`：11 件修辞工具件可被 import** —— `Callout`（画圈 + 引线 + 手写标注）、`Connector`（贝塞尔关系线 + 箭头 + 可选流向）、`Checklist`（序号圆牌 / 完成态对勾）、`CountUp` / `RollDigit`、`JumpInText` / `WaveText`、`CodeBlock`、`BrowserChrome`、`Mascot`、`ProgressBar` 从 `index.tsx` 迁出并 **export**；模块刻意不 import `index.tsx`（避免 `index → scenes → index` 的循环依赖），因此自持同名 helper。`assets/lecture-template/src/toolkit.tsx`
- **「修辞动作 → 组件」路由表** —— `references/media-routing.md` 新增 15 行选型表（含"何时别用"列），把路由从"内容类型 → 介质"扩到"我此刻要做的修辞动作该用哪一件"；`SKILL.md` 把 `fxkit.md` 与这张表改为**必读**，并要求 `live` 里的每个名字都能在这张表（或 `fxkit.md` 的组件表）上指到。`references/media-routing.md`、`SKILL.md`
- **`SKILL.md` 脚本清单登记第 9 道门禁** —— `scripts/validate-audio-levels.py` 写入脚本清单（构建期：素材峰值 < −12 dBFS 即 P0）。`SKILL.md`

### 变更

- **音效钉帧由"按镜头比例"改为"绑定节拍"** —— 旧的 `data-whoosh` 固定钉在镜头时长的 42% 处；新实现完全由 `beats` 推导：换章播 `paper-rustle`（0.38）、首拍 `paper-tap`（0.34）、末拍 `chime`（0.40）、中间拍在 `drop` / `toggle` / `click` 之间轮换（0.30），非 `still` 镜头沿用相机关键帧位置播 `click`（0.26）。`drop.ogg` 与 `toggle.ogg` 由此首次被引用。`assets/lecture-template/src/index.tsx`
- **`reveal` 由分镜表推导，场景不再手写** —— `resolve-shots.py` 生成 `reveal: transition === 'reveal'` 写进 `src/shots.ts` 与 `shots.resolved.json`，消除"表与实现不一致"的可能。`scripts/resolve-shots.py`
- **转场词汇收缩为三式** —— `TRANSITIONS` 由 `cut | handoff | whip | reveal | paper-turn` 收缩为 `cut | handoff | reveal`，`validate-composition.py` 的闭合集合、`references/composition-gate.md` 与 `locked-style-contract.json` 同步。**注意：分镜表若仍声明 `whip` / `paper-turn`，会被枚举闭合判为 P0。**
- **新增"声明即承诺"P0** —— `validate-composition.py` 校验 `reveal` 声明与场景里该镜的 `<Shot>` 是否一致（正反向都查）、`handoff` 声明是否带 `carrier` 且下一镜声明了同一个 `carrier`（否则它与 `cut` 没有区别）；模板分镜表里 S2 / S4 / S6 / S8 四镜的 `handoff` 因此改为 `cut`。`scripts/validate-composition.py`、`assets/lecture-template/manifests/shots.json`
- **新增三条 P1 门禁（阈值由两条成片校准）** —— 组件词汇多样性（≥16 镜要求可选组件 ≥10 件、8–15 镜 ≥7 件、≤7 镜 ≥5 件；单件占比 > 35% 提示换表达；结构件豁免）、反堆砌（≥12 镜的成片里"只出现在 1 镜"的可选件 ≥5 件即提示人工确认）、节拍密度（单镜 > 240 帧且节拍 < 3 个，画面会在台词中途冻住）。`scripts/validate-composition.py`
- **音效素材归一** —— `public/sfx/` 下 7 个素材（chime / click / data-whoosh / drop / paper-rustle / paper-tap / toggle）整体替换为归一后的版本。`assets/lecture-template/public/sfx/*`
- **README 与仓库元数据** —— `README.md` / `README.en.md` 按开源体例重写（介绍技能本身）；`.github/repository-metadata.yml` 的 description 压缩为"代码绘制或实拍素材 + 4 种骨架 + 8 道门禁"。`README.md`、`README.en.md`、`.github/repository-metadata.yml`

### 修复

- **"音效少"的真因不是数量而是双重衰减** —— 素材峰值过低（`paper-tap` −31 dB）× 混音音量过低（实测 0.13 ≈ −17.7 dB）后被 BGM（−22 dB）压住；本版既归一素材，又把音量提到 0.26–0.40，并新增门禁防止回退。`scripts/validate-audio-levels.py`、`assets/lecture-template/src/index.tsx`
- **`theme/types.ts` 的注释指向已删组件** —— 背景装饰区说明里"用 `BackgroundMute` 铺一层羽化暖底"改指 `CoverPanel`。`assets/lecture-template/src/theme/types.ts`

### 移除

- **死代码删除（净删约 150 行，零行为变化）** —— `WhipStreak`（8 帧甩镜在 30fps 下读不到，要真生效必须改交接引擎）、`PaperTurn`（换章翻场）、`BackgroundMute`（在 paper / sticker 皮肤下必然返回 `null`，是条死路）、`TransitionIn`（与 `RevealMask` 重复）；过渡实现收敛为"`cut` = 引擎的 10 帧叠帧、`handoff` = 需要 carrier、`reveal` = `RevealMask`"。`assets/lecture-template/src/insert.tsx`、`src/shotkit.tsx`、`src/index.tsx`
- **相关版本串与文档** —— `INSERT_VERSION` → `insert-v2`（三式转场）、`SHOTKIT_VERSION` → `shotkit-v2`；`references/media-routing.md`、`theme-cel.md`、`theme-flat.md` 与 `motion-design.md` 中关于上述组件与五式转场的段落同步改写。

**English**

### Background

Three things on top of 3.0.0, each motivated in the comments this release adds: (1) **"there are no sound effects" was caused by double attenuation** — the assets themselves are recorded very quietly (`paper-tap.wav` peaks at −31 dB) and the mix volume attenuates them again, leaving an effective peak of −49 dB while the BGM sits at −22 dB (`validate-audio-levels.py` header); (2) **the optional vocabulary was unreachable** — the 11 rhetorical tool components were defined inside `index.tsx` **without `export`**, so scene files physically could not import them, which is the structural reason a large component library produced so little use (`toolkit.tsx` header); (3) **shot-table declarations were not honoured** — shipped films declared `handoff` in the table without ever implementing it, and one declared `cut` while the code wrote `reveal` (the "a declaration is a promise" note in `validate-composition.py`); sound effects were also pinned at 42% of a shot's duration, a frame at which nothing happens (`index.tsx` SFX comment). This release adds no feature surface; it makes what already existed actually take effect — turning optional components into usable vocabulary, turning declarations into obligations, and making the sound effects audible.

### Added

- **Audio-level gate `scripts/validate-audio-levels.py` (the 9th gate)** — it measures the peak of every asset in `public/sfx/` (excluding `bgm*`) with ffmpeg: below **−12 dBFS** is a P0 (the asset is too quiet and will be buried at mix time), with the exact `ffmpeg -af volume=…dB` normalisation command printed; a `sfx/xxx` file referenced from `index.tsx` but missing on disk is also a P0; a missing BGM or a sound reference with no `vol:` setting anywhere is a P1. `scripts/validate-audio-levels.py`
- **`src/toolkit.tsx`: the 11 rhetorical tools become importable** — `Callout` (circle plus leader plus handwritten note), `Connector` (bezier relationship line with arrow and optional flow), `Checklist` (numbered discs / completion ticks), `CountUp` / `RollDigit`, `JumpInText` / `WaveText`, `CodeBlock`, `BrowserChrome`, `Mascot` and `ProgressBar` move out of `index.tsx` and are **exported**; the module deliberately does not import `index.tsx` (avoiding the `index → scenes → index` cycle) and therefore carries its own copies of the shared helpers. `assets/lecture-template/src/toolkit.tsx`
- **A "rhetorical move → component" routing table** — `references/media-routing.md` gains a 15-row selection table with a "when not to use it" column, extending routing from "content type → medium" to "which component fits the move I am making right now"; `SKILL.md` makes `fxkit.md` and this table **required reading** and asks that every name in `live` be traceable on the table (or in `fxkit.md`'s component list). `references/media-routing.md`, `SKILL.md`
- **`SKILL.md` script inventory gains the 9th gate** — `scripts/validate-audio-levels.py` is listed as a build-time gate (asset peak below −12 dBFS is a P0). `SKILL.md`

### Changed

- **Sound cues now bind to beats instead of shot ratios** — `data-whoosh` used to be pinned at 42% of the shot duration; the new implementation derives every cue from `beats`: a chapter change plays `paper-rustle` (0.38), the first beat `paper-tap` (0.34), the last beat `chime` (0.40), middle beats rotate through `drop` / `toggle` / `click` (0.30), and non-`still` shots keep a `click` at the camera keyframe position (0.26). This is the first use of `drop.ogg` and `toggle.ogg`. `assets/lecture-template/src/index.tsx`
- **`reveal` is derived from the shot table** — `resolve-shots.py` now writes `reveal: transition === 'reveal'` into `src/shots.ts` and `shots.resolved.json`, removing any chance of the table and the implementation disagreeing. `scripts/resolve-shots.py`
- **The transition vocabulary shrinks to three** — `TRANSITIONS` goes from `cut | handoff | whip | reveal | paper-turn` to `cut | handoff | reveal`, with `validate-composition.py`'s closed set, `references/composition-gate.md` and `locked-style-contract.json` updated to match. **Note: a shot table still declaring `whip` or `paper-turn` will now be reported as a P0 by the closed-enumeration check.**
- **New "a declaration is a promise" P0** — `validate-composition.py` verifies that a `reveal` declaration matches the shot's `<Shot>` in the scene source (both directions), and that a `handoff` declaration carries a `carrier` which the next shot declares as well (otherwise it is indistinguishable from `cut`); S2 / S4 / S6 / S8 in the bundled shot table therefore move from `handoff` to `cut`. `scripts/validate-composition.py`, `assets/lecture-template/manifests/shots.json`
- **Three new P1 gates (thresholds calibrated on two shipped films)** — component vocabulary diversity (≥10 optional components for a film of 16+ shots, ≥7 for 8–15, ≥5 for 7 or fewer; a single component above 35% of shots is flagged; structural components are exempt), anti-pile-up (in a film of 12+ shots, five or more optional components appearing in exactly one shot is flagged for human review), and beat density (a shot longer than 240 frames with fewer than three beats freezes mid-sentence). `scripts/validate-composition.py`
- **Sound assets normalised** — all seven assets under `public/sfx/` (chime, click, data-whoosh, drop, paper-rustle, paper-tap, toggle) are replaced with normalised versions. `assets/lecture-template/public/sfx/*`
- **READMEs and repository metadata** — `README.md` / `README.en.md` are rewritten for an open-source audience (describing the skill itself); the `.github/repository-metadata.yml` description is compressed to "code-drawn scenes or real screenshots, 4 scene skeletons, 8 automated gates". `README.md`, `README.en.md`, `.github/repository-metadata.yml`

### Fixed

- **"Too few sound effects" was double attenuation, not quantity** — an asset peak that is too low (`paper-tap` at −31 dB) times a mix volume that is too low (measured 0.13 ≈ −17.7 dB) ends up buried under a BGM sitting at −22 dB; this release normalises the assets, raises the volumes to 0.26–0.40, and adds a gate so it cannot regress. `scripts/validate-audio-levels.py`, `assets/lecture-template/src/index.tsx`
- **A comment in `theme/types.ts` pointed at a removed component** — the background-decoration note that said "use `BackgroundMute` for a feathered warm plate" now points at `CoverPanel`. `assets/lecture-template/src/theme/types.ts`

### Removed

- **Dead code deleted (a net ~150 lines, no behaviour change)** — `WhipStreak` (an 8-frame whip is unreadable at 30 fps and would require changing the handoff engine to work), `PaperTurn` (chapter flip), `BackgroundMute` (it inevitably returns `null` on the paper / sticker skins) and `TransitionIn` (duplicated by `RevealMask`); transitions are now `cut` (the engine's 10-frame overlay), `handoff` (requires a carrier) and `reveal` (`RevealMask`). `assets/lecture-template/src/insert.tsx`, `src/shotkit.tsx`, `src/index.tsx`
- **Version strings and docs** — `INSERT_VERSION` → `insert-v2` (three transitions) and `SHOTKIT_VERSION` → `shotkit-v2`; the passages about those components and the five-transition vocabulary in `references/media-routing.md`, `theme-cel.md`, `theme-flat.md` and `motion-design.md` are rewritten to match.

---

## [3.0.0] - 2026-09-11

### 背景与动机

本版是用两支真实成片（记录中为 DeepSeek 129 秒、SWE-2 237 秒）打磨出来的修复版，动机来自这段 diff 本身能看到的三个问题：① **帧参数名写错不报错**——`fxkit` 的组件收 `frame`、其他模块收 `f`，传错只会静默回落到全局帧，`start={局部节拍}` 早已过去，元素以"完成态"直接出现（`validate-frame-props.py` 文件头注释）；② **渲染期门禁静默失效**——`CardFitGate` 的字体未就绪整桶跳过与 `offsetParent` 链断裂、`OverlapGate` 的 15 帧网格漏掉短命重叠，都写进了本版重写后的代码注释；③ **分镜表可以写假名字**——`intent` / `transition` / `entry` / `media` / `skeleton` 此前是自由字符串，`live` 写不存在的组件名也能 P0=0 通过（`validate-composition.py` 注释）。因此本版把"构建期能证明的"全部变成 P0，并新增实拍素材框。

### 不兼容的变更（主版本号升级的原因）

本版没有删除或改名任何对外组件 API（新增文件只有 `src/plates.tsx` 与 `scripts/validate-frame-props.py`）。**不兼容发生在"门禁口径"这一层：此前通过的分镜表 / 工程可能被判 P0 或被中断渲染，交付验收的阈值也被收紧。** 逐条如下（全部可在本版 diff 中指到）：

- **枚举闭合（新 P0）**：`cameraIntent` / `transition` / `entry` / `media` / `skeleton` 写错名字即 P0——此前这些字段是自由字符串，`media: ["FAKE_MEDIUM_A", …]`、`live: ["NO_SUCH_COMPONENT"]` 都能 P0=0 通过。`scripts/validate-composition.py`
- **`live` 名字必须能兑现（新 P0）**：`live` 里每个名字必须出现在工程的场景源码里，否则报 P0。`scripts/validate-composition.py`
- **声明运镜必须真的动（新 P0）**：`Δs < 0.02` 且 `Δ平移 < 20px` 即 P0；把 `still` 改名成 `push-in` 不再能骗过意图多样性与运镜配额。`scripts/validate-shot-motion.py`
- **`explanation:false` 不再能整体绕过密度校验（新 P0）**：只豁免"活性组件"这一条，且全片最多 1 镜；`zones` 必须是 3–5 的整数，`bottomFill` 必须为 `true`。`scripts/validate-composition.py`
- **交付真峰阈值收紧**：`validate-video` 由 `peak > -1` 改为 `peak > -1.5`（dBTP），此前 −1.3 dBTP 的违标成片会从"通过"变成"失败"。`scripts/notebook-video.mjs`
- **渲染期门禁在模板成片里切到阻断档**：`OverlapGate` 由默认警告改为 `mode="block"`（命中严重重叠即 `cancelRender`），并新增事件帧强制抽样。`assets/lecture-template/src/index.tsx`
- **`CardFitGate` 判据换口径**：改判"卡片内容是否超出卡片"（`scrollHeight`/`scrollWidth`，竖向 10px 容差、横向只在文字真越界时按 8px 报），并把"渐变背景 + 有边框"的元素也算卡片、跳过阈值由 z ≥ 140 提到 z ≥ 145（页眉层 z=140 从此参与检查，章节卡 150 与字幕 200 仍跳过）——以前静默通过的溢出现在会拦。`assets/lecture-template/src/index.tsx`
- **`ConsoleWindow` 的高度语义变化**：未传 `h` 时，旧实现按 `24 + 行数 × rowGap` 算出一个高度，新实现交给浏览器按内容撑（`height: auto`）。依赖旧计算值的调用方需要显式传 `h`。`assets/lecture-template/src/media.tsx`

### 新增

- **帧参数名门禁 `scripts/validate-frame-props.py`（第 8 道构建期门禁）** —— 从引擎源码解析每个导出组件的帧参数名（`fxkit` 用 `frame`，`media` / `kit` / `stagekit` / `skeletons` / `insert` / `shotkit` 用 `f`；两者都收或都不收也能识别），再逐个 JSX 标签核对：只认 `frame` 的组件被传 `f={f}`（或反之）即 P0，因为组件会静默回落到全局帧；该传未传记 P1，不该传却传了记 P1。场景文件按 `*scene*` 匹配（含被拆分出来的 `scenes-a/b/c/d.tsx`）；解析到的组件数 < 20 时直接返回 2、不给 PASS（防"引擎源码没读到"的假通过）。`scripts/validate-frame-props.py`
- **实拍素材框 `ShotPlate`** —— 把真实截图/官方图表装进锁定皮肤的墨线框（`paper` 底 + 2.5px 墨线 + 硬偏移阴影），配角标、右上角标与底部署名，用 `transform` + `focus` 做确定性推近（`zoom` / `dur`，不重排、无随机）。素材仍需按双清单登记（`manifests/visual-assets.json` 的来源/授权/是否含文字/校验和，与 `asset-manifest.json` 的素材 id），登记契约与用法写进 `references/fxkit.md`。`assets/lecture-template/src/plates.tsx`
- **`SKILL.md`「开工前 20 行授权契约」** —— 放在参考文件表之前，20 条逐条对应一个真实事故（分镜表不写帧号、骨架相邻不同款、`live` 不许写假名字、帧参数名、卡片高度必须 `fitH`、底托必须负 z、下 1/4 必须填满、门禁失败只许改内容不许改判据等）。`SKILL.md`
- **文档与门禁表同步** —— `references/fxkit.md` 新增参数名对照表与错峰校准说明；`references/scene-authoring.md` 坑表 6 → 10 条（新增"flex 子项只含绝对定位元素导致宽度塌陷、多卡精确叠压"与"卡片高度必须用 `fitH` 算"）；`SKILL.md` 的门禁表更新为 8 道，并补上"覆盖率日志缺失 = 门禁没跑，按失败处理"的判据。`SKILL.md`、`references/fxkit.md`、`references/scene-authoring.md`

### 变更

- **交付响度改为两遍规范化** —— 渲染后先用 `loudnorm` 以 JSON 探针测出 `input_i` / `input_tp` / `input_lra` / `input_thresh`，再以 `measured_*` + `linear=true` 精准应用（解析失败时退回单遍模式）。`scripts/notebook-video.mjs`
- **`OverlapGate` 判定与抽样面扩大** —— 基础 15 帧网格之外，把镜头边界、节拍与相机关键帧（±2 帧）交由 `index.tsx` 传入强制抽样；`looksSolid` 把 `backgroundImage !== 'none'` 也算实心（渐变面板此前被当透明）；`SKIP_Z` 由 140 提到 145（页眉层参与检查，只跳过章节卡 150 / 字幕 200）；文本矩形一律用 `Range` 取并集；每 5 秒打一次覆盖率日志。版本串 → `overlap-gate-v3`。`assets/lecture-template/src/overlap-gate.tsx`
- **`CardFitGate` 重写** —— 等 `document.fonts.ready` 后补测（不再因字体未就绪整桶跳过）；判据换成"卡片内容是否超出卡片"（竖向容差按代码注释取 10px，横向只在**文字**真的越界时按 8px 容差报，避免把引线/焦点点/硬阴影当裁切）；剔除 `overflow: visible` 容器；z ≥ 145 跳过（章节卡 150 / 字幕 200 是锁定覆盖层）；每 5 秒打覆盖率。`assets/lecture-template/src/index.tsx`
- **构建期门禁硬化** —— `validate-composition.py`：枚举闭合、`live` 可兑现、`explanation:false` 收紧、`zones` 必须为整数区间；新增 P1（单镜 > 300 帧、骨架指纹 `(骨架,意图,转场,入场)` 重复、镜长分布与 ≤4s 短镜、`hero.size` 下限）；P1 由"每镜刷一条最长静止"改为**汇总 + 帧区间归因**；`--json` 输出增加 `notes`，打印"已校验：枚举 5 类 / live N 个名字 / hero N 镜 / 时长 N 镜"。`scripts/validate-composition.py`
- **组件动效校准** —— `StaggerList` 默认错峰 14 → 6 帧（同句内 ≤8 帧）；`Corridor` 停驻呼吸频率 0.5 → 0.045 rad/帧、`SkeletonCard` 0.105 → 0.048（把"约 12.6 帧 / 60 帧"的毛躁呼吸拉长到约 140 / 131 帧）；`CompareBars` 行补 14px 位移（此前只有透明度）；`SplitStage` 分割线补 `opacity`；`Funnel` 行距与条高收窄；`FitCard` / `StaggerList` 的透明度改用独立时钟。`assets/lecture-template/src/fxkit.tsx`、`skeletons.tsx`
- **模板场景同步** —— `scenes.tsx` 修帧参数名（`StampSeal` / `Typewriter` / `Funnel` / `SkeletonCard` 由 `f={f}` 改为 `frame={f}`）；`PhaseRail` 的两个调用处不再传入硬写 `local: 0` 的假 ctx，直接使用回调给的 ctx；`Funnel` / `StaggerList` / `MetricGrid` 的错峰收紧到 6 帧。`assets/lecture-template/src/scenes.tsx`

### 修复

- **`OverlapGate` 遮挡判断漏看祖先 z** —— 只查元素自身的 `z-index`，而字幕的文字 `span` 自身是 `auto`（其祖先是 z=200），于是字幕被当成"遮挡物"整片误报；改为祖先链一并检查，并明确"锁定覆盖层（自身或其祖先 z ≥ 145）不作为遮挡物"。同一处还修掉渐变遮挡物看不见、多文本节点按整块矩形量两个问题。`assets/lecture-template/src/overlap-gate.tsx`
- **`CardFitGate` 此前三处静默失效** —— 字体未就绪整桶跳过且从不等待字体、`offsetParent` 链断裂导致部分文字块从未被校验、零输出无法区分"全部合格"与"根本没跑"；三者均已按上述重写修掉。`assets/lecture-template/src/index.tsx`
- **`SKILL.md` 门禁表把 `SlotGuard` 明确为 dev-only** —— 该行由 `render (dev)` 改为 `render (dev only)`，槽宽校验明确由 `CardFitGate` 与重叠门承担（`stagekit.tsx` 在本版未被改动）。`SKILL.md`
- **`validate-frame-props.py` 的早期写法只匹配 `scenes.tsx`** —— 场景被拆成多份后一个文件都不查却报 P0=0（脚本注释记录了这一静默漏判）；本版按 `*scene*` 匹配修复，实测覆盖从 1 个文件变为 6 个。`scripts/validate-frame-props.py`

### 移除

- 无对外组件删除（`fxkit` / `media` / `stagekit` / `skeletons` / `insert` / `shotkit` 的导出保持兼容）。

**English**

### Background

This release is a repair pass driven by two real films (recorded as DeepSeek 129s and SWE-2 237s). The motivation is visible in this diff itself: (1) **a wrong frame-prop name fails silently** — `fxkit` components take `frame`, the other modules take `f`, and a mismatch falls back to the global frame, so `start={local beat}` is already in the past and the element appears in its finished state (`scripts/validate-frame-props.py` header); (2) **runtime gates that silently did nothing** — `CardFitGate` skipping the whole bucket while fonts load and breaking on the `offsetParent` chain, and `OverlapGate`'s 15-frame grid missing short-lived overlaps, both documented in the rewritten code; (3) shot tables that could name things that do not exist — `intent` / `transition` / `entry` / `media` / `skeleton` were free strings and a `live` name with no implementation still passed with P0=0 (`validate-composition.py`). This release turns everything provable at build time into a P0, and adds the material plate.

### Incompatible changes (why this is a major release)

No public component API was removed or renamed (the only new files are `src/plates.tsx` and `scripts/validate-frame-props.py`). **The breakage is in gate criteria: shot tables and projects that passed before can now be reported as P0 or have their render aborted, and the delivery ceiling was tightened.** Each item below is traceable in this release's diff:

- **Closed enumerations (new P0)** — a wrong `cameraIntent` / `transition` / `entry` / `media` / `skeleton` name is now P0; previously these were free strings, so `media: ["FAKE_MEDIUM_A", …]` or `live: ["NO_SUCH_COMPONENT"]` passed with P0=0. `scripts/validate-composition.py`
- **`live` names must resolve (new P0)** — every name in `live` must appear in the project's scene sources. `scripts/validate-composition.py`
- **A declared camera move must actually move (new P0)** — `Δs < 0.02` and `Δpan < 20px` is a P0; renaming `still` to `push-in` no longer fools the intent-diversity count or the per-chapter quota. `scripts/validate-shot-motion.py`
- **`explanation:false` no longer bypasses density (new P0)** — it exempts the live-component rule only, at most one shot per film; `zones` must be an integer from 3 to 5 and `bottomFill` must be `true`. `scripts/validate-composition.py`
- **Tightened delivery true-peak ceiling** — `validate-video` moves from `peak > -1` to `peak > -1.5` dBTP, so a −1.3 dBTP film now fails instead of passing. `scripts/notebook-video.mjs`
- **The runtime gate blocks in the bundled films** — `OverlapGate` switches from warning to `mode="block"` (severe overlap calls `cancelRender`) and gains forced sampling on event frames. `assets/lecture-template/src/index.tsx`
- **A changed `CardFitGate` criterion** — it now judges whether a card's content exceeds the card (`scrollHeight`/`scrollWidth`; 10px vertical tolerance, 8px horizontal and only when text really crosses the edge), counts "gradient background plus a border" as a card, and raises the skip threshold from z ≥ 140 to z ≥ 145 (the header layer at z=140 now participates; the chapter card at 150 and subtitles at 200 are still skipped), so overflow that used to pass silently is caught. `assets/lecture-template/src/index.tsx`
- **Changed height semantics in `ConsoleWindow`** — without `h`, the old code computed `24 + rows × rowGap`; the new code lets the browser size it to content (`height: auto`). Callers relying on the computed value should pass `h` explicitly. `assets/lecture-template/src/media.tsx`

### Added

- **Frame-prop-name gate `scripts/validate-frame-props.py` (the 8th build-time gate)** — it parses the frame-prop name of every exported engine component (`fxkit` uses `frame`; `media` / `kit` / `stagekit` / `skeletons` / `insert` / `shotkit` use `f`; components accepting both or neither are identified too) and then checks every JSX tag: passing `f={f}` to a component that only accepts `frame` (or the reverse) is a P0, because the component silently falls back to the global frame; omitting a required frame prop is a P1, as is passing one to a component that uses none. Scene files are matched by `*scene*` (including split-out `scenes-a/b/c/d.tsx`), and fewer than 20 parsed components returns 2 instead of a PASS, so "the engine sources were never read" cannot masquerade as success. `scripts/validate-frame-props.py`
- **Material plate `ShotPlate`** — real screenshots and official charts sit inside the locked skin's ink frame (`paper` surface + 2.5px ink outline + hard offset shadow), with a caption, a top-right badge and a source line, pushed in deterministically via `transform` + `focus` (`zoom` / `dur`, no reflow, no randomness). Assets still have to be registered in both manifests (`manifests/visual-assets.json` records source, rights, baked text and checksum; `asset-manifest.json` mirrors the ids), and the contract and usage are documented in `references/fxkit.md`. `assets/lecture-template/src/plates.tsx`
- **SKILL.md "20-line authorisation contract before you start"** — placed ahead of the reference-file table, each line tied to a real incident (no frame numbers in the shot table, adjacent scenes must differ, never invent a `live` name, frame-prop names, compute card heights with `fitH`, backing plates must use a negative z, fill the lower quarter, when a gate fails change the content and never the criterion). `SKILL.md`
- **Docs and gate table kept in sync** — `references/fxkit.md` gains the frame-prop name table and the stagger calibration note; `references/scene-authoring.md`'s pit table grows from 6 to 10 entries (flex children containing only absolutely-positioned elements collapsing to width 0 and stacking cards, and heights that must be computed with `fitH`); `SKILL.md` updates the gate table to eight gates and adds the rule that a missing coverage log means the gate never ran and must be treated as a failure. `SKILL.md`, `references/fxkit.md`, `references/scene-authoring.md`

### Changed

- **Delivery loudness is normalised in two passes** — after rendering, `loudnorm` probes the file as JSON for `input_i` / `input_tp` / `input_lra` / `input_thresh`, then applies them with `measured_*` and `linear=true` (falling back to a single pass if the probe cannot be parsed). `scripts/notebook-video.mjs`
- **`OverlapGate` judges and samples more** — beyond the 15-frame grid, shot boundaries, beats and camera keyframes (±2 frames) are pushed in as forced samples by `index.tsx`; `looksSolid` now counts `backgroundImage !== 'none'` as opaque (gradient panels used to read as transparent); `SKIP_Z` rises from 140 to 145 so the header layer participates (only the chapter card at 150 and subtitles at 200 are skipped); text rects are always unioned with `Range`; a coverage line is logged every 5 seconds. Version string → `overlap-gate-v3`. `assets/lecture-template/src/overlap-gate.tsx`
- **`CardFitGate` rewritten** — it re-measures after `document.fonts.ready` (no more skipping the bucket while fonts load); the criterion becomes "does the card's content exceed the card" (vertical tolerance 10px per the code comment; horizontal reports only when *text* actually crosses the edge, at 8px, so leader lines, focus dots and hard shadows are not read as clipping); `overflow: visible` containers are excluded; z ≥ 145 is skipped (the chapter card at 150 and subtitles at 200 are locked overlays); coverage is logged every 5 seconds. `assets/lecture-template/src/index.tsx`
- **Build-time gates hardened** — `validate-composition.py`: closed enumerations, resolvable `live` names, the tightened `explanation:false` rule, `zones` as an integer range; new P1s (single shot > 300 frames, repeated skeleton fingerprints `(skeleton, intent, transition, entry)`, shot-length distribution and the ≤4s short shot, `hero.size` floors); P1 output changes from one static-run line per shot to an **aggregated report with frame ranges**; `--json` gains `notes` stating what was actually checked (5 enum families, N live names, N shots for hero and duration). `scripts/validate-composition.py`
- **Component motion calibrated** — `StaggerList`'s default stagger drops from 14 to 6 frames (≤8 within one sentence); `Corridor`'s dwell breathing goes from 0.5 to 0.045 rad/frame and `SkeletonCard`'s from 0.105 to 0.048 (lengthening a jittery ~12.6-frame / 60-frame breath to roughly 140 / 131 frames); `CompareBars` rows gain 14px of travel (previously opacity only); `SplitStage`'s divider gains `opacity`; `Funnel` tightens its row spacing and bar height; `FitCard` / `StaggerList` move opacity onto independent clocks. `assets/lecture-template/src/fxkit.tsx`, `skeletons.tsx`
- **Bundled scenes updated** — `scenes.tsx` fixes frame-prop names (`StampSeal` / `Typewriter` / `Funnel` / `SkeletonCard` move from `f={f}` to `frame={f}`); the two `PhaseRail` call sites no longer pass a fake ctx with a hard-coded `local: 0` and use the callback's ctx directly; `Funnel` / `StaggerList` / `MetricGrid` staggers tighten to 6 frames. `assets/lecture-template/src/scenes.tsx`

### Fixed

- **`OverlapGate` ignored ancestor z-index** — it looked only at an element's own `z-index`, while a subtitle's text span is `auto` (its ancestor carries z=200), so subtitles were reported as occluders across the whole film; the check now walks the ancestor chain and locked overlays (self or ancestor at z ≥ 145) are explicitly not treated as occluders. The same pass fixes gradient occluders being invisible and multi-node text being measured as one block. `assets/lecture-template/src/overlap-gate.tsx`
- **Readability backing plates are now semi-transparent** — the `cel` skin's `Paper` goes from fully opaque to 88%; the scene shell's feathered plate centre from 96% to 76% and its mid stop from 84% to 59%; the chapter card's backing leaves pure white for semi-transparency, so the background is no longer covered outright. `assets/lecture-template/src/theme/cel.tsx`, `src/index.tsx`
- **Three silent failures in `CardFitGate`** — skipping the whole bucket while fonts were not loaded (and never waiting for them), the broken `offsetParent` chain leaving some text blocks unmeasured, and zero output being indistinguishable from "everything passed"; all three are addressed by the rewrite above. `assets/lecture-template/src/index.tsx`
- **`SKILL.md`'s gate table marks `SlotGuard` dev-only** — the row changes from `render (dev)` to `render (dev only)`, and slot-width checking is stated to be carried by `CardFitGate` and the overlap gate (`stagekit.tsx` is untouched in this release). `SKILL.md`
- **An early form of `validate-frame-props.py` matched only `scenes.tsx`** — once scenes were split into several files it checked nothing and still reported P0=0 (the script's own comment records this silent miss); this release matches `*scene*` instead, taking coverage from 1 file to 6. `scripts/validate-frame-props.py`

### Removed

- No public component removals (`fxkit` / `media` / `stagekit` / `skeletons` / `insert` / `shotkit` exports stay compatible).

---

## [2.9.0] - 2026-09-11

### 背景与动机

上一版把「不许做成 PPT」写成了一批强制条款（强制使用反 PPT 组件、镜头只允许 ±15px 微移与 1.8% 景别变化），但这些条款在实现里无从检查：规范强制使用的组件引用数为 0，也没有任何脚本能发现（依据：本版新增脚本的注释与 `validate-composition.py` 的文件头说明）。同时旧契约把取景写成**全片一条关键帧轨道**（`camera_micro_framing_only`、`camera_x_bounds`、`camera_scale_bounds`，全部在本版被删除），镜头不可能有自己的取景。本版把"合规"从文档条款改成**可运行的构建期门禁**，并把取景改为**镜头级受限配方 + anchor 出界证明**；同时补齐"内容 → 视觉介质"这一层，让每个讲解场景至少有一个会随旁白变状态的组件。

### 新增

- **镜头层与出界证明** —— 新增 `ShotCamera`：每镜声明六个意图之一（`establish` / `push-in` / `pull-back` / `pan-follow` / `reveal` / `micro-orbit`）加一个必须始终可见的 `anchor`；`panBudget()` / `camAt()` 在运行时按 `maxPanX = 960×(1−1/s)` 钳制平移；`DepthLayers` 提供 0.35 / 0.70 / 1.00 三档景深视差（层数 ≤3），`ambientBreath(f)` 提供幅度 ≤4% 的环境呼吸。`assets/lecture-template/src/shotkit.tsx`
- **两道构建期门禁** —— `scripts/validate-shot-motion.py`（P0：时间轴覆盖、逐关键帧证明 anchor 不出界、缩放预算、平移预算、`rotY ≤ 6°`、单镜运镜时长 30–45 帧与每章/全片配额、全片 ≥3 种意图；P1：背景装饰区重叠须声明 `cover`）与 `scripts/validate-composition.py`（P0：相邻骨架不得相同且全片 ≥3 种、每个讲解场景 ≥1 个活性组件、≥3 种介质、`zones` 3–5、下 1/4 填满；P1：转场 ≥2 种、入场 ≥3 种、节拍间隔）。两脚本纯标准库、只读，P0 阻断渲染。
- **分镜表与解析器** —— 分镜表只声明语义（`cues` 起止、骨架、介质、活性组件、镜头意图、anchor），`scripts/resolve-shots.py` 从 TTS 词级时间戳推出全部绝对帧，生成 `src/shots.ts`（带 AUTO-GENERATED 头，相机关键帧已展开）与 `manifests/shots.resolved.json`；解析器自身校验断档/重叠、覆盖总长与声明时长、cue 越界。`scripts/resolve-shots.py`、`assets/lecture-template/manifests/shots.json`
- **四种场景骨架** —— `StageFrame`（含 `useStageMachine` / `PhaseRail` / `Attach` / `SlotGuard`）、`Corridor`、`SplitStage`、`ZoomStage`（三段式变换：先平移到框心、再缩放、再把焦点平移回原点，并按内容尺寸钳制缩放上限）。`assets/lecture-template/src/stagekit.tsx`、`assets/lecture-template/src/skeletons.tsx`
- **内容 → 视觉介质层** —— `ConsoleWindow`、`MetricGrid`、`StampBanner`，并把主题无关原子 `PillTag` / `LineIcon` / `CheckBadge` / `TYPE` 抽到独立模块供工程侧引用。`assets/lecture-template/src/media.tsx`、`assets/lecture-template/src/kit.tsx`
- **渲染期重叠/遮挡门禁 `OverlapGate`** —— 每 15 帧抽样：① 文字两两重叠（用 `Range.getClientRects()` 量真实字形矩形，避免居中文本按整块宽度误报）；② 文字被遮挡（按绘制顺序判定，排除祖先、透明蒙层与有意覆盖）。默认仅警告，可切 `mode="block"` 阻断渲染。同时确立**有意覆盖的标注约定**：带 `data-gate-allow` 的元素视为有意覆盖（约定取值 `handoff` / `swap` / `value-swap`，`MetricGrid` 的新旧值替换即标 `value-swap` 并把两项改成两条互不相交的 56px 轨道），`data-gate-skip` 用于整块跳过——且不允许用白名单掩盖两条不同信息互相压字。`assets/lecture-template/src/overlap-gate.tsx`
- **负向抽查** —— `scripts/negative-gate-check.py` 为三道构建期门禁喂"该被拦"的夹具（anchor 出界、平移超预算、相邻同骨架且无活性组件、时间轴断档），外加一条阴性对照必须全过，用于证明门禁不是"见谁拦谁"。`scripts/negative-gate-check.py`
- **组件接触表** —— 新增 `NotebookVideoShowcase` Composition 与 `showcase` / `showcase-sheet` 命令：6 页 × 16 个构件 + 6 种镜头意图 + 4 种骨架，1fps 抽帧即得一页一图，让执行方"看图选型"而不是读 props 文档。`assets/lecture-template/src/showcase.tsx`、`scripts/notebook-video.mjs`
- **背景可读性契约** —— 主题新增 `backgroundDecorZones`（cel 4 区、flat 2 区），内容压到装饰区时必须坐在 `CoverPanel` 上（wash 底托必须用负 z，正 z 会压住场景内所有 `z-index: auto` 的元素）；锁定背景位图本身不改。`assets/lecture-template/src/theme/types.ts`、`theme/cel.tsx`、`theme/flat.tsx`
- **参考文档与契约** —— 新增 `references/shot-language.md`、`scene-skeletons.md`、`media-routing.md`、`composition-gate.md`；`locked-style-contract.json` 换成"每镜受限配方 + anchor 证明 + 配额"契约（`camera_is_per_shot`、`camera_intents`、`camera_anchor_proof_required`、`camera_min_moves_per_chapter`、`camera_max_moves_per_shot`、`camera_move_frames`、`camera_zoom_max_text/graphic`、`depth_layers_max`、`depth_parallax_coefficients`、`scene_skeletons`、`adjacent_skeleton_must_differ`、`zones_per_scene` 等），并新增 `timing_system` 与 `readability_system` 两组契约；`motion-design.md` 写入多时钟动效规则（同一元素多属性用不同时钟、出入场曲线不同、不要只动透明度、数值用 `tabular-nums` + 固定小数位、进度动 `scaleX` 不动 `width`、过冲只给物体不给数值）与"每镜保留一处缓慢环境运动"的正面要求。

### 变更

- **取景由"全片一条轨道"改为镜头级** —— `NotebookVideoFilm` 不再使用全片级相机（`CameraRig` 的指数滞后跟焦整段删除），每镜自带关键帧；页眉、章节卡与字幕渲染在 `ShotCamera` 之外，结构上不会被运镜带动。
- **`FinalDemo` 改为只挂载当前镜** —— 由分镜表决定当前是哪一镜（不再由硬编码帧区间切换场景），并在每镜开头 10 帧把上一镜末帧叠在上层淡出（标 `data-gate-allow="handoff"`），镜头边界不再出现空帧。
- **音效钉帧改为相对镜头起点推导** —— `Sound` 不再持有 7 组绝对帧数组，改由分镜表的节拍与相机关键帧推导（换章翻纸、传输 whoosh、要点 tap、完成 chime、点击 click、翻牌 toggle、吸附 drop）。
- **`index.tsx` 由"引擎 + 内联组件库"瘦身为引擎层** —— 场景骨架、介质、原子、插入镜头与接触表拆成独立模块；`storyboard.md` 改为由 `shots.json` 派生的镜头表（镜号、帧区间、骨架、介质、镜头意图、转场、入场、活性组件）；`asset-manifest.json` 的场景改为 `S1…S8` 并登记骨架/介质/镜头意图/转场/章节，总帧数 1126 → 1150；`selftest.py` 关键产物清单纳入本版新增模块、四份文档与三个脚本；README 与 SKILL.md 按"四种骨架 + 内容路由 + 受限镜头 + 门禁"重写（SKILL.md 新增参考文件读取时机清单、门禁表与脚本清单）。

### 修复

- **字幕宽度门禁此前是"画幅盲"的** —— 旧实现固定用 44px / 字重 400 / 字距 1.2 与主题里的安全宽度量，未计入画布与主题字幕框内边距；新实现取当前画布的 `mode.subFont` 与主题新增的 `subtitleWeight` / `subtitleLetterSpacing` / `subtitlePadX`（cel 64、sticker 72、flat 108、paper 0）度量，超 `mode.safe` 记 fail 并阻断渲染、仅超内边距记 warn。后果是 4:3 与 3:4 画幅下此前静默放行的超宽字幕会开始被拦下。`assets/lecture-template/src/index.tsx`、`src/theme/*.tsx`
- **`fxkit` 在 paper / flat 皮肤下会崩** —— `THEME.extras.Burst` 改为可选链：这两个皮肤没有 `extras`，原写法在 import 该模块时即抛错。`assets/lecture-template/src/fxkit.tsx`
- **`fxkit` 动效细节修正（均有原位前后对比）** —— `Typewriter` 光标由 9 帧方波改为 16 帧余弦软闪（方波在 30fps 下读作频闪）；`StampSeal` 增加 1→1.06→1 回弹与冲击波环；`Funnel` 级联间隔 22 → 14 帧、水滴错峰 3 帧、条宽由 `width` 改 `scaleX`；`ProgressRing` 弧与数字改用不同时钟、数字加 `tabular-nums`、过冲只给容器；`DiffView` 增删行分方向进出并加扫光；`SkeletonCard` 等待呼吸由 0.55±0.25（读作闪灯）改为 0.9±0.05。`assets/lecture-template/src/fxkit.tsx`

### 移除

- **`CameraRig` / `CAM_KEYS_L` / `CAM_KEYS_P` / `camAt`** —— 全片级相机轨道及其 14 点指数滞后跟焦实现删除，取景改由镜头层承担。`assets/lecture-template/src/index.tsx`
- **旧相机契约的三个键** —— `locked-style-contract.json` 删除 `camera_micro_framing_only` / `camera_x_bounds` / `camera_scale_bounds`，`motion-design.md` 删除旧的 "Camera Micro-Framing Invariant" 整节。

**English**

### Background

The previous version wrote "do not ship a slide deck" down as mandatory clauses (required anti-PPT components, a camera limited to ±15px drift and 1.8% zoom travel), but none of them were checkable in the implementation: the components the rules demanded had zero references and no script could notice (see the header comments added to the new gates in this version). The old contract also described framing as **one film-wide keyframe track** (`camera_micro_framing_only`, `camera_x_bounds`, `camera_scale_bounds` — all deleted here), so an individual shot could not have its own framing. This version turns compliance from prose into **run-time build gates**, replaces the camera with a **per-shot restricted recipe plus an anchor out-of-bounds proof**, and adds the missing "content → visual medium" layer so every explanation scene carries at least one component that changes state with the narration.

### Added

- **Shot layer with an out-of-bounds proof** — new `ShotCamera`: each shot declares one of six intents (`establish` / `push-in` / `pull-back` / `pan-follow` / `reveal` / `micro-orbit`) plus an `anchor` that must stay visible; `panBudget()` / `camAt()` clamp panning at run time to `maxPanX = 960×(1−1/s)`; `DepthLayers` supplies three parallax coefficients (0.35 / 0.70 / 1.00, at most three layers) and `ambientBreath(f)` supplies a ≤4%-amplitude ambient motion. `assets/lecture-template/src/shotkit.tsx`
- **Two build-time gates** — `scripts/validate-shot-motion.py` (P0: timeline coverage, per-keyframe proof that the anchor stays inside the visible window, zoom budgets, pan budget, `rotY ≤ 6°`, 30–45-frame move duration with per-chapter and per-film quotas, ≥3 intents; P1: a content band overlapping a background decoration zone must declare `cover`) and `scripts/validate-composition.py` (P0: adjacent scenes may not share a skeleton and ≥3 skeletons per film, ≥1 live component per explanation scene, ≥3 media, `zones` 3–5, lower quarter filled; P1: ≥2 transitions, ≥3 entries, beat gaps). Both are standard-library only, read-only, and P0 blocks the render.
- **Shot table and resolver** — the shot table declares semantics only (cue range, skeleton, media, live components, camera intent, anchor); `scripts/resolve-shots.py` derives every absolute frame from the TTS word timings and generates `src/shots.ts` (AUTO-GENERATED header, camera keyframes already expanded) plus `manifests/shots.resolved.json`. The resolver also checks gaps/overlaps, coverage versus the declared duration and cue bounds. `scripts/resolve-shots.py`, `assets/lecture-template/manifests/shots.json`
- **Four scene skeletons** — `StageFrame` (with `useStageMachine` / `PhaseRail` / `Attach` / `SlotGuard`), `Corridor`, `SplitStage`, `ZoomStage` (a three-part transform: translate to the frame centre, scale, then translate the focus back, with the zoom ceiling clamped by content size). `assets/lecture-template/src/stagekit.tsx`, `assets/lecture-template/src/skeletons.tsx`
- **Content → visual medium layer** — `ConsoleWindow`, `MetricGrid`, `StampBanner`, with the theme-agnostic atoms `PillTag` / `LineIcon` / `CheckBadge` / `TYPE` extracted into their own module for project-side use. `assets/lecture-template/src/media.tsx`, `assets/lecture-template/src/kit.tsx`
- **Runtime overlap/occlusion gate `OverlapGate`** — samples every 15 frames for (1) pairwise text overlap, measured on real glyph rects via `Range.getClientRects()` so centred text is not reported as spanning the full block width, and (2) occlusion, judged in paint order while excluding ancestors, transparent overlays and declared intentional overlaps. Warn by default; `mode="block"` aborts the render. It also establishes the **intentional-overlap marking convention**: an element carrying `data-gate-allow` is read as an intentional overlap (the agreed values are `handoff` / `swap` / `value-swap` — `MetricGrid`'s value swap is marked `value-swap` and its two values moved onto two non-intersecting 56px tracks), while `data-gate-skip` skips a block entirely — and the allow-list may never hide two different pieces of information colliding. `assets/lecture-template/src/overlap-gate.tsx`
- **Negative spot-check** — `scripts/negative-gate-check.py` feeds deliberately broken fixtures to the three build gates (anchor outside the frame, pan beyond budget, adjacent scenes sharing a skeleton with no live component, timeline gap) plus one clean control that must pass, proving the gates are not "reject everything". `scripts/negative-gate-check.py`
- **Component contact sheet** — new `NotebookVideoShowcase` composition and `showcase` / `showcase-sheet` commands: 6 pages × 16 components + 6 camera intents + 4 skeletons, one image per page at 1 fps, so the executor picks components by sight instead of reading prop tables. `assets/lecture-template/src/showcase.tsx`, `scripts/notebook-video.mjs`
- **Background readability contract** — themes gain `backgroundDecorZones` (cel 4 zones, flat 2 zones); content overlapping a zone must sit on a `CoverPanel` (a wash plate must use a negative z-index — a positive one covers every `z-index: auto` element in the scene). The locked background bitmaps are untouched. `assets/lecture-template/src/theme/types.ts`, `theme/cel.tsx`, `theme/flat.tsx`
- **Reference docs and contracts** — new `references/shot-language.md`, `scene-skeletons.md`, `media-routing.md`, `composition-gate.md`; `locked-style-contract.json` becomes a "per-shot restricted recipe + anchor proof + quotas" contract (`camera_is_per_shot`, `camera_intents`, `camera_anchor_proof_required`, `camera_min_moves_per_chapter`, `camera_max_moves_per_shot`, `camera_move_frames`, `camera_zoom_max_text/graphic`, `depth_layers_max`, `depth_parallax_coefficients`, `scene_skeletons`, `adjacent_skeleton_must_differ`, `zones_per_scene`, …) and adds the `timing_system` and `readability_system` blocks; `motion-design.md` records the multi-clock motion rules (separate clocks per property, different in/out curves, never opacity alone, `tabular-nums` with fixed decimals for numbers, progress via `scaleX` rather than `width`, overshoot only on objects) and the positive requirement that every shot keeps one slow ambient motion.

### Changed

- **Framing moved from one film-wide track to per shot** — `NotebookVideoFilm` no longer uses a film-level camera (the `CameraRig` exponential follow-focus is deleted wholesale); each shot carries its own keyframes, and the header, chapter card and subtitles render outside `ShotCamera`, so camera motion cannot drag them.
- **`FinalDemo` mounts only the active shot** — the current shot is resolved from the shot table (no more hard-coded frame ranges) and the previous shot's last frame is laid on top for 10 frames at each boundary and faded out (marked `data-gate-allow="handoff"`), so shot boundaries no longer show empty frames.
- **Sound effects are pinned relative to the shot** — `Sound` no longer holds seven absolute frame arrays; cues are derived from the shot table's beats and camera keyframes (chapter rustle, transfer whoosh, beat tap, completion chime, click, toggle, drop).
- **`index.tsx` slimmed from "engine plus inlined component library" to the engine layer** — skeletons, media, atoms, inserts and the contact sheet became separate modules; `storyboard.md` is now a shot table derived from `shots.json` (shot, frame range, skeleton, media, camera intent, transition, entry, live components); `asset-manifest.json` renames scenes to `S1…S8` and records skeleton / media / camera intent / transition / chapter with a total of 1126 → 1150 frames; `selftest.py` adds the new modules, the four documents and the three scripts to its key-artefact list; the README and SKILL.md are rewritten around "four skeletons + content routing + restricted camera + gates" (SKILL.md gains a read-timing list, the gate table and the script inventory).

### Fixed

- **The caption-width gate was canvas-blind** — it measured with a fixed 44px / weight 400 / letter-spacing 1.2 and the theme's safe width, ignoring the canvas and the theme's subtitle padding. It now measures with the current canvas `mode.subFont` and the new theme fields `subtitleWeight` / `subtitleLetterSpacing` / `subtitlePadX` (cel 64, sticker 72, flat 108, paper 0): exceeding `mode.safe` fails and blocks the render, exceeding only the inner padding warns. As a result, over-wide captions that used to pass silently on 4:3 and 3:4 are now rejected. `assets/lecture-template/src/index.tsx`, `src/theme/*.tsx`
- **`fxkit` crashed on the paper / flat skins** — `THEME.extras.Burst` now uses optional chaining; those skins have no `extras`, so the previous form threw as soon as the module was imported. `assets/lecture-template/src/fxkit.tsx`
- **`fxkit` motion details corrected (each with a before/after in this diff)** — `Typewriter`'s cursor moves from a 9-frame square wave to a 16-frame cosine fade (the square wave reads as flicker at 30 fps); `StampSeal` gains a 1→1.06→1 rebound and a shock ring; `Funnel` tightens its stagger from 22 to 14 frames, offsets its droplets by 3 frames and drives bar width through `scaleX`; `ProgressRing` uses separate clocks for the arc and the number, adds `tabular-nums`, and puts overshoot on the container only; `DiffView` gives added and removed lines direction-specific in/out motion plus a sweep; `SkeletonCard`'s waiting breath goes from 0.55±0.25 (reads as a blinking light) to 0.9±0.05. `assets/lecture-template/src/fxkit.tsx`

### Removed

- **`CameraRig` / `CAM_KEYS_L` / `CAM_KEYS_P` / `camAt`** — the film-wide camera track and its 14-sample exponential lag follow-focus are gone; framing is now a shot-layer responsibility. `assets/lecture-template/src/index.tsx`
- **The old camera keys in the contract** — `locked-style-contract.json` drops `camera_micro_framing_only` / `camera_x_bounds` / `camera_scale_bounds`, and `motion-design.md` drops the whole "Camera Micro-Framing Invariant" section.

---

## [2.8.0] - 2026-09-08

### 背景与动机
已记录：`references/fxkit.md` 写明本版新增的两条铁律都来自本片的真实出格缺陷——S3（170px 容器装 208px 内容）与 S5（400px 装 430px）的文字溢出、S4 印章把卡片相对坐标写成场景坐标而飞出屏；`fxkit.tsx` 头部写明组件库以「零新依赖、只做 transform/opacity 位移、cel 皮肤锁定、30fps 确定性（无随机数）」为设计原则。运行期防出格门与时长漂移修复的动机未在记录中留存（据改动推断）。

### 新增
- **fxkit 动效组件库（v2，18 个组件，零新依赖）** —— `FitCard` / `fitH`（高度必须显式算出的防出格卡片）、`Typewriter`、`PayPop`、`StampSeal`、`Funnel`、`ChatThread`、`MailScan`、`TimeRail`、`CompareBars`、`ProgressRing`、`ShakeX`、`BurstCallout`、`StaggerList`、`KenBurnsImg`、`EvidenceZoom`、`DiffView`、`ConfettiPop`、`SkeletonCard`。只依赖 `react` 与 `remotion`，只做 transform/opacity 动画，统一接受本地帧 `frame` + `start`，给出 `exitStart` 即完整离场。`assets/lecture-template/src/fxkit.tsx`
- **fxkit 目录与两条铁律** —— `references/fxkit.md` 列出 18 个组件的用途与关键 props，并记录「高度必须由 `fitH()` 算出」与「`x`/`y` 永远相对最近的 positioned 祖先（卡片内为卡片相对坐标）」两条铁律及其对应的真实故障场景。`references/fxkit.md`
- **`CardFitGate` 卡片防出格门** —— 运行期门禁：按 15 帧为桶扫描已挂载场景中含文字的叶元素，用 offset 链累加其相对最近卡片祖先（不透明底 + 实线边框）的位置，超出卡片 padding 盒 2px 即 `cancelRender`；offset 链天然无视 transform 位移动画，`z>=140` 的 chrome 与字幕层跳过（各自已有门），字体未就绪的桶跳过。`assets/lecture-template/src/index.tsx`
- **`scripts/coords-lint.py` 坐标审计（只读）** —— 列出覆盖层组件的数字 `x` / `y` 字面量，超出整画布（1920×1080 / 1080×1440）直接报错，`x>1000` 或 `y>700` 打 WARN 提示人工确认是场景坐标还是卡片相对坐标，`--strict` 下 WARN 亦判失败。`scripts/coords-lint.py`
- **`scripts/retime.py` 重定时工具** —— 口播或章节变化后一条命令重写 `src/index.tsx` 的 `DURATION` 与 `manifests/asset-manifest.json` 的 `duration_frames` 及各场景起止帧，并打印音效帧重排建议表（场景起点 / 中点 / 完成点，人工确认后手改）；场景数与边界段数不符时拒写 manifest。`scripts/retime.py`
- **`scripts/audition.py` 试听条与多音字扫描** —— 从已缓存的 `audio/seg*.wav` 每段取前 3 秒拼出约 30 秒试听条（零 API 调用），并用内置高危多音字表扫描 `narration.txt`，命中时报行号与改写建议。`scripts/audition.py`
- **密钥防呆门禁与关键产物清单扩充** —— `selftest.py` 新增密钥防呆检查：被追踪文件命中 `sk-` + 16 位以上字母数字即判失败；关键产物清单补入 `coords-lint.py`、`retime.py`、`audition.py`、`fxkit.tsx` 与 `references/fxkit.md`。`scripts/selftest.py`

### 变更
- **`SKILL.md` 组件清单补入 fxkit** —— 组件清单追加 fxkit 全部 18 个组件与 `references/fxkit.md` 入口；版本号更新为 2.8.0。`SKILL.md`
- **仓库元数据与清单版本推进** —— 根 `manifest.json` 版本 2.8.0、`updated_at` 2026-09-09；`.github/repository-metadata.yml` 发布 tag 更新为 v2.8.0。`manifest.json`、`.github/repository-metadata.yml`

### 修复
- **`lecture-template` 时长漂移** —— `manifests/asset-manifest.json` 的 `duration_frames` 由 900 改为 1126，末场景 `end_frame` 由 900 改为 1126，与 `src/index.tsx` 的 `DURATION=1126` 及字幕轨一致；`validate-visual-plan.py` 新增 `DURATION` 交叉校验，manifest 与源码不一致即失败，堵住该类漂移。`assets/lecture-template/manifests/asset-manifest.json`、`scripts/validate-visual-plan.py`
- **`validate-visual-plan.py` 校验加严** —— `image-text` 场景必须引用至少一个非背景插画资产（`bg-` 前缀不计），否则报错。`scripts/validate-visual-plan.py`

**English**

### Background
Recorded: `references/fxkit.md` states that both iron laws added in this release come from real overflow defects in this film — text overflowing its container in S3 (208px of content in a 170px box) and S5 (430px in 400px), and an S4 stamp that used scene coordinates where card-relative coordinates were required and flew off-screen; the header of `fxkit.tsx` states the library's design principles (zero new dependencies, transform/opacity animation only, cel skin locked, deterministic 30fps with no random numbers). The motivation for the runtime overflow gate and the duration-drift fix is not in the record (inferred from the change).

### Added
- **fxkit motion library (v2, 18 components, zero new dependencies)** — `FitCard` / `fitH` (an overflow-proof card whose height must be computed), `Typewriter`, `PayPop`, `StampSeal`, `Funnel`, `ChatThread`, `MailScan`, `TimeRail`, `CompareBars`, `ProgressRing`, `ShakeX`, `BurstCallout`, `StaggerList`, `KenBurnsImg`, `EvidenceZoom`, `DiffView`, `ConfettiPop` and `SkeletonCard`. It depends only on `react` and `remotion`, animates transform and opacity only, takes a local `frame` plus `start` on every component, and fully exits as soon as `exitStart` is passed. `assets/lecture-template/src/fxkit.tsx`
- **fxkit catalogue and its two iron laws** — `references/fxkit.md` lists the purpose and key props of all 18 components and records the two laws — heights must be computed by `fitH()`, and `x`/`y` are always relative to the nearest positioned ancestor (card-relative inside a card) — together with the real failures behind them. `references/fxkit.md`
- **`CardFitGate` overflow gate** — a runtime gate that scans the mounted scenes once per 15-frame bucket: for every leaf element holding text it accumulates the offset chain relative to the nearest card ancestor (opaque background plus a solid border) and calls `cancelRender` when the content passes the card's padding box by more than 2px. The offset chain is transform-independent, `z>=140` chrome and subtitle layers are skipped (they have their own gates) and buckets whose fonts are not loaded yet are skipped. `assets/lecture-template/src/index.tsx`
- **`scripts/coords-lint.py` coordinate reporter (read-only)** — lists numeric `x` / `y` literals of overlay components; values outside the full canvas (1920×1080 / 1080×1440) fail, and `x>1000` or `y>700` emit a WARN asking a human to confirm scene versus card-relative coordinates; with `--strict` a WARN also fails. `scripts/coords-lint.py`
- **`scripts/retime.py` retiming tool** — one command rewrites `DURATION` in `src/index.tsx`, the `duration_frames` and scene bounds in `manifests/asset-manifest.json`, and prints a sound-frame remap table (scene start, midpoint, completion point) for manual confirmation; it refuses to write the manifest when the scene count does not match the boundary list. `scripts/retime.py`
- **`scripts/audition.py` audition strip and polyphone scan** — builds an approximately 30-second audition strip from the first three seconds of each cached `audio/seg*.wav` with zero API calls, and scans `narration.txt` against a built-in high-risk polyphone table, reporting line numbers and rewrite advice. `scripts/audition.py`
- **Secret-leak guard and an expanded key-artifact list** — `selftest.py` fails when any tracked file contains a key-like token (`sk-` followed by 16 or more alphanumerics); the key-artifact list gains `coords-lint.py`, `retime.py`, `audition.py`, `fxkit.tsx` and `references/fxkit.md`. `scripts/selftest.py`

### Changed
- **`SKILL.md` component list gains fxkit** — the list now names all 18 fxkit components and points at `references/fxkit.md`; the version is bumped to 2.8.0. `SKILL.md`
- **Repository metadata and manifest version advanced** — the root `manifest.json` moves to version 2.8.0 with `updated_at` 2026-09-09, and `.github/repository-metadata.yml` sets the release tag to v2.8.0. `manifest.json`, `.github/repository-metadata.yml`

### Fixed
- **`lecture-template` duration drift** — `duration_frames` in `manifests/asset-manifest.json` is corrected from 900 to 1126 and the last scene's `end_frame` from 900 to 1126, matching `DURATION=1126` in `src/index.tsx` and the caption track; `validate-visual-plan.py` now cross-checks `DURATION`, so a manifest that disagrees with the source fails and this class of drift is blocked. `assets/lecture-template/manifests/asset-manifest.json`, `scripts/validate-visual-plan.py`
- **`validate-visual-plan.py` tightened** — an `image-text` scene must reference at least one non-background illustration asset (anything without the `bg-` prefix), otherwise it fails. `scripts/validate-visual-plan.py`

---

## [2.7.0] - 2026-09-08

### 背景与动机
已记录：`references/motion-design.md` 的新增条款写明本版要「消除静止 PPT 感，同时不让正在讲解的内容被推出画面」，为此把虚拟相机的位移与缩放收敛为极小量级；同一份文档把「复杂机制禁止纯文字卡片堆叠，必须使用带状态变化的实体交互组件」写成铁律，并把字幕句末标点从画面上彻底去掉。Cel 主题美学减重的动机未在记录中留存（据改动推断）。

### 新增
- **6 个反 PPT 实体交互组件** —— `BrainwaveEEG`（认知脉冲波形，会话中断或记忆清空瞬间拉成红色直线）、`VectorRadarSonar`（360° 扫描光束 + 向量聚类点高亮）、`BM25TokenRibbon`（倒排索引词条与匹配分标尺）、`HookMountBay`（钩子插头插入端口并锁定变绿）、`RedactionScanner`（红外光束扫过敏感 token 并实时掩码）、`ChipContract`（微硬件芯片流转卡）。`assets/lecture-template/src/index.tsx`
- **镜头微运镜铁律（Camera Micro-Framing Invariant）** —— 16:9 主线镜头关键帧由大幅推拉（缩放 1.02–1.16、x 700–1495、y 485–610）收敛为 x 948–974、y 538–542、缩放 1.012–1.018，方向与讲解内容同向（左卡微左聚 `x≈948`、右侧数据微右浮 `x≈974`、换章归位 `x=960`）。`assets/lecture-template/src/index.tsx`
- **镜头与反 PPT 契约条款** —— `locked-style-contract.json` 新增 `camera_micro_framing_only`、`camera_x_bounds [945, 975]`、`camera_scale_bounds [1.00, 1.018]`、`anti_ppt_functional_components_required`；`SKILL.md`、`motion-design.md`、`quality-checklist.md` 同步写入硬性位移约束、语意跟随规则与拒绝项。`references/locked-style-contract.json`、`SKILL.md`、`references/motion-design.md`、`references/quality-checklist.md`
- **字幕句末标点消除机制** —— `Subtitle` 引入 `targetChars` 字符序号闸门，逐字渲染的字符数不超过 `cleanTail` 处理后的文本长度，句中逗号保留、句末标点不再渲染；契约新增 `trailing_punctuation_forbidden`。`assets/lecture-template/src/index.tsx`、`references/locked-style-contract.json`、`references/quality-checklist.md`
- **仓库根 `manifest.json`** —— 记录 `name` / `version` / `owner` / `updated_at` / `status` / `maturity_tier`。`manifest.json`

### 变更
- **Cel 主题美学减重** —— 卡片描边 5px → 2.5px、圆角 8 → 10、硬偏移墨影由 `7 + 7×lift` 收紧为 `3 + 3×lift`；字幕框描边 5px → 2.5px、硬影 `8px 8px 0` → `3.5px 3.5px 0`、内边距由 12/34 收为 10/32；分镜微倾角系数 0.5 → 0.35（实际幅度 ±1° → ±0.7°）。`assets/lecture-template/src/theme/cel.tsx`
- **`CodeBlock` 改为深色终端样式** —— 由 Paper 卡片皮肤改为深底终端（`#14110f` 底 + 2.2px 墨边 + 3.5px 硬偏移影），行文本默认改为浅色；新增逐行独立 `start`（未到帧不渲染）、行前缀 `prefix`、更精确的行尾光标判定。`assets/lecture-template/src/index.tsx`
- **Cel 契约与拒绝项同步收紧** —— 卡片与字幕的描边、圆角、阴影数值改写，新增「任何描边超过 2.5px 或阴影超过 4px 一律拒绝」与「字幕末尾可见标点一律拒绝」两条拒绝项。`references/theme-cel.md`、`references/motion-design.md`、`references/quality-checklist.md`
- **TTS 适配器支持 env 文件与默认值** —— 依次尝试项目内 `tts.env`、项目内 `.env` 及上层 `tts.env` 并注入环境变量（不覆盖已有值）；`TTS_API_KEY` 缺失时给出明确报错；`TTS_MODEL` 默认 `mimo-v2.5-tts`、`TTS_VOICE` 默认 `冰糖`；项目目录参数可省略。`assets/lecture-template/scripts/tts-openai-compatible.py`
- **忽略本地密钥与审计产物** —— `.gitignore` 增加 `*.env`、`audit-report.txt`、`.doctor/`。`.gitignore`

**English**

### Background
Recorded: the new clause in `references/motion-design.md` states the goal of eliminating the static PPT feeling while preventing any actively narrated content from being pushed out of frame, which is why the virtual camera's displacement and scale are reduced to a minimal range. The same document makes it an iron law that complex mechanisms must use active components with state changes instead of stacked text cards, and removes trailing punctuation from subtitles entirely. The motivation for the cel aesthetic slimming is not in the record (inferred from the change).

### Added
- **Six anti-PPT interactive components** — `BrainwaveEEG` (cognitive pulse wave that flatlines to a red line when the session breaks or memory is flushed), `VectorRadarSonar` (360° sweep beam with highlighted vector clusters), `BM25TokenRibbon` (inverted-index token and score meter), `HookMountBay` (hook plug inserts into the port and locks green), `RedactionScanner` (infrared beam sweeps sensitive tokens and masks them live) and `ChipContract` (micro-hardware chip capsule). `assets/lecture-template/src/index.tsx`
- **Camera Micro-Framing Invariant** — the 16:9 main-track camera keyframes are pulled in from large pushes (scale 1.02–1.16, x 700–1495, y 485–610) to x 948–974, y 538–542 and scale 1.012–1.018, moving with the narration (drift left `x≈948` for a left card, right `x≈974` for right-side data, back to `x=960` between chapters). `assets/lecture-template/src/index.tsx`
- **Camera and anti-PPT contract clauses** — `locked-style-contract.json` gains `camera_micro_framing_only`, `camera_x_bounds [945, 975]`, `camera_scale_bounds [1.00, 1.018]` and `anti_ppt_functional_components_required`; `SKILL.md`, `motion-design.md` and `quality-checklist.md` record the hard bounds, the semantic follow rules and the rejection flags. `references/locked-style-contract.json`, `SKILL.md`, `references/motion-design.md`, `references/quality-checklist.md`
- **Subtitle trailing-punctuation strip** — `Subtitle` gains a `targetChars` character-index gate so no more characters are rendered than the length of the text after `cleanTail`; mid-sentence commas stay, trailing punctuation is never drawn. The contract gains `trailing_punctuation_forbidden`. `assets/lecture-template/src/index.tsx`, `references/locked-style-contract.json`, `references/quality-checklist.md`
- **Repository-root `manifest.json`** — records `name`, `version`, `owner`, `updated_at`, `status` and `maturity_tier`. `manifest.json`

### Changed
- **Cel theme aesthetic slimming** — card borders 5px → 2.5px, radius 8 → 10, the hard offset ink shadow tightened from `7 + 7×lift` to `3 + 3×lift`; the subtitle chrome border goes 5px → 2.5px, its shadow `8px 8px 0` → `3.5px 3.5px 0` and its padding 12/34 → 10/32; the panel tilt coefficient goes 0.5 → 0.35 (actual amplitude ±1° → ±0.7°). `assets/lecture-template/src/theme/cel.tsx`
- **`CodeBlock` becomes a dark terminal** — it drops the Paper card skin for a dark terminal (`#14110f` background, 2.2px ink border, 3.5px hard offset shadow) with light default text; lines gain an independent `start` (not rendered before their frame), an optional `prefix` and a more precise trailing-cursor test. `assets/lecture-template/src/index.tsx`
- **Cel contract and rejection flags tightened** — the card and subtitle border, radius and shadow values are rewritten, and two rejection flags are added: any border over 2.5px or shadow over 4px, and any visible trailing punctuation in a subtitle. `references/theme-cel.md`, `references/motion-design.md`, `references/quality-checklist.md`
- **TTS adapter reads env files and has defaults** — it tries `tts.env` in the project, `.env` in the project and an upper-level `tts.env` in turn and injects them without overwriting existing variables; a missing `TTS_API_KEY` now fails with a clear message; `TTS_MODEL` defaults to `mimo-v2.5-tts` and `TTS_VOICE` to `冰糖`; the project directory argument is optional. `assets/lecture-template/scripts/tts-openai-compatible.py`
- **Local secrets and audit artifacts ignored** — `.gitignore` gains `*.env`, `audit-report.txt` and `.doctor/`. `.gitignore`

---

## [2.6.0] - 2026-09-06

### 背景与动机
本版把校验与安全纪律补齐：仓库级一致性校验从单模板扩到双模板（`example-project` + `lecture-template`），`selftest.py` 增加脚本语法门禁与密钥防呆并提供标准回归入口，`SKILL.md` 写入交付指标事实卡与 Zero-Mutation 执行纪律；同时修掉字幕与口播不同步、`new-project` 文档指向失效、CLI 缺少计时命令、`SKILL.md` 与锁定视觉系统矛盾等一批缺陷。文档已记录的意图：`SKILL.md` 新增条款要求脚本检测与视觉审查恪守纯只读排查、绝不擅自变动系统配置，完整渲染、依赖安装或大构架重写须经用户明确授权。

### 新增
- **双模板一致性校验门** —— `validate-skill-consistency.py` 在原有校验之后追加 `lecture-template` 的 layering / visual-plan / caption-sync / semantic-breaks 四项校验，并以 sha256 强制 `manifests/caption-cues.json` 与 `src/caption-cues.json` 内容一致；新增 `--json` 只读结构化输出（含 `problems_count` 与 `templates_validated`）。`scripts/validate-skill-consistency.py`
- **脚本 AST 语法门禁与标准回归入口** —— `selftest.py` 用 `ast.parse` 逐个解析 `scripts/*.py`，任一语法错误即判失败；新增 `tests/test_skill.py` 作为统一回归入口，转发到 `scripts/selftest.py`。`scripts/selftest.py`、`tests/test_skill.py`
- **交付指标事实卡与 Zero-Mutation 纪律** —— `SKILL.md` 交付清单增至 10 项并新增事实卡表格（画幅与帧率、响度与混音、字幕对齐、黑帧与图层穿透四层），同版写明脚本检测与视觉审查纯只读、完整渲染与依赖安装须用户授权、`scripts/*.py` 基于 Python 3.10+ 标准库零第三方依赖。`SKILL.md`
- **v2.5 组件库演示视频** —— 新增 `assets/demo/notebook-video-components-demo.mp4`（2560×1440、30fps、54 秒、1620 帧、H.264/AAC，约 10.9 MB），README 中英双版加入入口链接，覆盖 26 枚锁定图标、七个组件、三式转场、文字动效、物理件与四套主题皮肤。`assets/demo/notebook-video-components-demo.mp4`、`README.md`、`README.en.md`

### 变更
- **参考文档体系调整** —— 参考资料清单改为「按需加载与行动指引」并逐条补写使用场景；同时补充 `scripts/` 下各脚本的职责清单。`SKILL.md`

### 修复
- **`lecture-template` 字幕与口播不同步** —— `audio/narration.mp3.json` 的 154 条词级时间戳重排，末词由 30.00s 顺延到 37.55s，与 16 条语义 cue（末条 `speech_end` 37.55s、对应 `DURATION` 1126 帧）对齐；`manifests/caption-cues.json` 与 `src/caption-cues.json` 同步并补入 `source` / `lead_ms` / `segmentation` 字段。`assets/lecture-template/audio/narration.mp3.json`、`assets/lecture-template/manifests/caption-cues.json`、`assets/lecture-template/src/caption-cues.json`
- **`new-project --style=paper` 指向不存在的文档** —— 帮助信息改为按主题选择：`paper` 指向 `references/visual-system.md`，其余主题仍指向 `references/theme-<style>.md`（原先一律输出 `references/theme-paper.md`）。`scripts/notebook-video.mjs`
- **CLI 缺少计时命令** —— 把 `match-timing` 映射进跨平台启动器并更新用法文本，文档中的调用示例改为经 `scripts/notebook-video.mjs` 调用，`speed-post.py` 示例路径同步修正。`scripts/notebook-video.mjs`、`references/tts-audio.md`
- **`SKILL.md` 与锁定视觉系统矛盾** —— 删除过时的左侧橙色定位环与右侧蓝色状态环描述，字幕改为纯底部字幕（无深色边框、无侧边伪影、无定位环），并明确「无装饰条」。`SKILL.md`
- **文档层级过深** —— `lecture-composition.md` 与 `windows-compatibility.md` 增加目录；文档中的嵌套链接引用改为反引号单跳引用（`visual-director.md`、`remotion-architecture.md`、`performance-design.md`、主题契约等）。`references/lecture-composition.md`、`references/windows-compatibility.md`、`references/independent-parts.md`、`references/pacing-rhythm.md`、`references/remotion-architecture.md`、`references/theme-system.md`、`references/official-aesthetic-system.md`、`references/official-skills-exemplar.md`

**English**

### Background
This release closes gaps in validation and safety: the repository-wide consistency gate now audits both templates (`example-project` and `lecture-template`), `selftest.py` gains a script syntax gate and a secret-leak guard plus a standard regression entry point, and `SKILL.md` records a delivery fact card and the Zero-Mutation execution discipline. It also fixes caption/narration desync, a dead documentation route in `new-project`, a timing command missing from the CLI, and a `SKILL.md` contradiction with the locked visual system. Recorded intent: the new `SKILL.md` clause requires script checks and visual review to stay strictly read-only and never change system configuration, while a full render, dependency installation or large architectural rewrite needs explicit user authorisation.

### Added
- **Dual-template consistency gate** — `validate-skill-consistency.py` now runs the layering, visual-plan, caption-sync and semantic-breaks checks for `lecture-template` after its existing checks, and enforces byte equality (sha256) between `manifests/caption-cues.json` and `src/caption-cues.json`; a new `--json` flag emits read-only structured output (`problems_count`, `templates_validated`). `scripts/validate-skill-consistency.py`
- **Script AST syntax gate and standard regression entry point** — `selftest.py` parses every `scripts/*.py` with `ast.parse` and fails on any syntax error; `tests/test_skill.py` is added as the standard regression entry point that forwards to `scripts/selftest.py`. `scripts/selftest.py`, `tests/test_skill.py`
- **Delivery fact card and Zero-Mutation discipline** — the `SKILL.md` delivery list grows to ten items and gains a fact-card table (canvas and frame rate, loudness and mix, caption alignment, black frames and layer bleed-through); the same document states that script checks and visual review are read-only, that a full render or dependency install needs user authorisation, and that `scripts/*.py` stay on the Python 3.10+ standard library with zero third-party dependencies. `SKILL.md`
- **v2.5 component-library showcase video** — adds `assets/demo/notebook-video-components-demo.mp4` (2560×1440, 30fps, 54 seconds, 1620 frames, H.264/AAC, about 10.9 MB) and links it from both READMEs; it covers the 26 locked icons, the seven components, the three transitions, type motion, physical parts and all four theme skins. `assets/demo/notebook-video-components-demo.mp4`, `README.md`, `README.en.md`

### Changed
- **Reference-document map restructured** — the resource list becomes "load on demand, with an action pointer" and each entry gains its use case; the responsibilities of every script under `scripts/` are listed alongside. `SKILL.md`

### Fixed
- **`lecture-template` caption and narration desync** — the 154 word-level timestamps in `audio/narration.mp3.json` are re-timed, moving the final word from 30.00s to 37.55s so they match the 16 semantic cues (last `speech_end` 37.55s, i.e. `DURATION` of 1126 frames); `manifests/caption-cues.json` and `src/caption-cues.json` are aligned and gain `source`, `lead_ms` and `segmentation` fields. `assets/lecture-template/audio/narration.mp3.json`, `assets/lecture-template/manifests/caption-cues.json`, `assets/lecture-template/src/caption-cues.json`
- **`new-project --style=paper` pointed at a non-existent document** — the help text now resolves the contract per style: `paper` points at `references/visual-system.md` and the other themes keep `references/theme-<style>.md` (previously it always printed `references/theme-paper.md`). `scripts/notebook-video.mjs`
- **Timing command missing from the CLI** — `match-timing` is mapped into the cross-platform launcher and the usage text is updated; the documented invocations now go through `scripts/notebook-video.mjs` and the `speed-post.py` example path is corrected. `scripts/notebook-video.mjs`, `references/tts-audio.md`
- **`SKILL.md` contradicted the locked visual system** — the obsolete left orange locator and right blue status ring are removed and the subtitle becomes a pure bottom caption (no dark border, no side artifacts, no locator or ring), with "no decorative bar" stated explicitly. `SKILL.md`
- **Reference hierarchy too deep** — `lecture-composition.md` and `windows-compatibility.md` gain a table of contents, and nested markdown links are flattened to single-hop backtick references (`visual-director.md`, `remotion-architecture.md`, `performance-design.md`, the theme contracts and others). `references/lecture-composition.md`, `references/windows-compatibility.md`, `references/independent-parts.md`, `references/pacing-rhythm.md`, `references/remotion-architecture.md`, `references/theme-system.md`, `references/official-aesthetic-system.md`, `references/official-skills-exemplar.md`

---

## [2.5.0] - 2026-09-06

### 背景与动机
本版在讲解模板中扩容量化组件库（图标集与 7 个通用组件），并把弹性预设、转场、镜头脚本与停帧点缀固化成「锁定动效包」，同时修掉 `RollDigit` 定格错字的缺陷。组件库扩容的动机未在记录中留存（据改动推断）：改动落点是让常见题材直接取用既有构件，而不是每个场景各写一套。`RollDigit` 缺陷的现象与成因由改动本身完整说明。

### 新增
- **`LineIcon` 图标集由 4 枚扩到 26 枚** —— 新增 star / fork / branch / rocket / shield / terminal / cloud / link / bug / search / user / clock / download / upload / folder / chart / globe / lock / mail / calendar / heart / settings 共 22 枚，沿用同一 32 视窗、圆头描边语言，换题材直接取用。`assets/lecture-template/src/index.tsx`
- **7 个锁定通用组件** —— `CodeBlock`（三灯终端窗 + 语法色行 + 逐行滑入 + 可选光标）、`BrowserChrome`（三灯 + 锁 + URL 胶囊）、`Connector`（贝塞尔连接件，可选流向虚线 / 箭头 / 标签）、`Checklist`（编号清单，`done` 转对勾）、`CountUp`（缓动数字滚动 + 颜色过渡）、`ProgressBar`（轨道 + 填充 + 可选标签与百分比）、`Callout`（双描边手绘椭圆 + 手写体标注，弹入）。`assets/lecture-template/src/index.tsx`
- **锁定动效包** —— `SPRINGS` / `popS` 三档弹性预设（`snappy` 用于 UI 与代码行、`soft` 与旧 `pop` 参数完全一致、`bouncy` 用于标注）、`TransitionIn` 三式转场（`flip` 翻页 / `slide` 滑盖 / `wipe` 擦除）、`camScript` 链式镜头关键帧构建器（自动补齐首尾帧）、`useSteppedFrame(15)` 停帧点缀。`assets/lecture-template/src/index.tsx`
- **动效契约条款** —— 文档同步记录预设用途、同一部片最多一种转场风格，以及**严禁场景重叠**：上一场景必须完全离场（或降到 opacity 0）后下一转场才可开始，任何一帧不得同时出现两个场景；`camScript` 取代手写关键帧表；停帧只用于贴纸风味，不得用于字幕、转账或镜头。`references/motion-design.md`

### 变更
- **`SKILL.md` 组件与动效清单更新** —— 组件清单补入 `LineIcon`（26 枚）、`PillTag`、7 个新组件、`Gauge`、`StepRail`；动效清单补入动效包四项；版本号更新为 2.5.0。`SKILL.md`

### 修复
- **`RollDigit` 定格在错误字符** —— 滚动结束后旧字符仍可见、新字符被隐藏，版本号停在起始值。两个字符层的 opacity 条件改为只按转动相位判定（前段 `turnPhase <= 0.56`、后段 `turnPhase >= 0.44`），定格态必然显示目标字符。`assets/lecture-template/src/index.tsx`
- **`visual-system.md` 相机表述过期** —— 由「固定相机」改为「唯一的全局相机是官方 `CameraRig`，`--classic` 路线保留固定相机」，并把组件来源指向 `assets/lecture-template/src/index.tsx`。`references/visual-system.md`

**English**

### Background
This release expands the lecture template's locked component library (a wider icon set plus seven general components), freezes spring presets, transitions, the camera-track builder and the stop-motion accent into a locked motion pack, and fixes the `RollDigit` defect that settled on the wrong character. The motivation for the library expansion is not in the record (inferred from the change): common topics should reuse existing parts instead of each scene writing its own. The `RollDigit` defect is fully described by the change itself.

### Added
- **`LineIcon` grows from 4 to 26 glyphs** — 22 new glyphs: star, fork, branch, rocket, shield, terminal, cloud, link, bug, search, user, clock, download, upload, folder, chart, globe, lock, mail, calendar, heart and settings, all on the same 32-grid round-cap stroke language. `assets/lecture-template/src/index.tsx`
- **Seven new locked components** — `CodeBlock` (terminal window with traffic lights, syntax-coloured lines, per-line entry and an optional cursor), `BrowserChrome` (traffic lights plus lock and URL capsule), `Connector` (bezier link with optional flow dashes, arrow and label), `Checklist` (numbered rows, `done` turns the number into a check), `CountUp` (eased number roller with a colour transition), `ProgressBar` (track, fill and optional label/percentage) and `Callout` (double-stroke hand-drawn ellipse with a handwritten caption, bouncy entry). `assets/lecture-template/src/index.tsx`
- **Locked motion pack** — `SPRINGS` / `popS` spring presets (`snappy` for UI ticks and code lines, `soft` identical to the legacy `pop`, `bouncy` for callouts), `TransitionIn` scene transitions (`flip` page turn, `slide` cover, `wipe` edge reveal), the chainable `camScript` camera-keyframe builder (it guarantees first/last-frame coverage) and `useSteppedFrame(15)` for a stop-motion accent. `assets/lecture-template/src/index.tsx`
- **Motion contract clauses** — the docs record what each preset is for, the at-most-one-transition-style-per-film rule, and the **no-scene-overlap rule**: the outgoing scene must fully unmount (or reach opacity 0) before the incoming transition starts, so no frame shows two scenes. `camScript` replaces raw keyframe tables, and the stepped-frame accent is reserved for sticker-style charm — never subtitles, transfers or the camera. `references/motion-design.md`

### Changed
- **`SKILL.md` component and motion lists updated** — the component list now names `LineIcon` (26 glyphs), `PillTag`, the seven new components, `Gauge` and `StepRail`; the motion list names the four motion-pack entries; the version is bumped to 2.5.0. `SKILL.md`

### Fixed
- **`RollDigit` settled on the wrong character** — after the roll completed the outgoing glyph stayed visible and the incoming one was hidden, so version badges froze on their starting value. Both spans now key on the turn phase alone (outgoing `turnPhase <= 0.56`, incoming `turnPhase >= 0.44`), so the settled state always shows the target character. `assets/lecture-template/src/index.tsx`
- **Stale camera wording in `visual-system.md`** — "fixed camera" now reads "the only global camera is the official `CameraRig`; the `--classic` route keeps its fixed camera", and the component source now points at `assets/lecture-template/src/index.tsx`. `references/visual-system.md`

---

## [2.4.0] - 2026-09-05

### 背景与动机
`cel` / `sticker` / `flat` 三套主题的背景此前由主题文件用 SVG 代码自绘（半调网点、速度线、网格与手绘涂鸦、几何小怪兽）。本版把三者整体切换为「每画幅比例一张固定资产图」，并把该规则与拒绝项写入三份主题契约。动机未在记录中留存（据改动推断）：改动落点是让背景不再由代码随场景重绘，而由固定图统一承担背景语言；默认 `paper` 主题不在改动范围内。

### 变更
- **主题背景改为锁定固定资产图** —— `cel` / `sticker` / `flat` 的 `Background` 组件改为 `Img` + `staticFile`，按 `useCanvas().canvas` 从 `bg-<theme>-<169|43|34>.jpg` 三选一，以 `100%` 宽高 + `objectFit: cover` 铺满画布；三主题中自绘的半调网点、速度线、网格、手绘涂鸦与几何小怪兽 SVG 代码全部删除。`assets/lecture-template/src/theme/cel.tsx`、`assets/lecture-template/src/theme/sticker.tsx`、`assets/lecture-template/src/theme/flat.tsx`
- **9 张背景图入库并登记来源** —— 每主题 3 张（16:9 图为 2560×1440，4:3 图为 2240×1680，3:4 图为 1680×2240，与各自画幅同比），`manifests/visual-assets.json` 记录各图 id 与 sha256，`manifests/asset-manifest.json` 的顶层资产表与全部场景 `visual_asset_ids` 补齐 9 个 id。`assets/lecture-template/public/bg-*.jpg`、`assets/lecture-template/manifests/visual-assets.json`、`assets/lecture-template/manifests/asset-manifest.json`
- **三份主题契约改写为固定资产图规则** —— 背景小节与拒绝项同步替换为「禁止改回代码自绘背景、禁止在图上叠加装饰、禁止把错误比例的图拉伸到画布」；`cel` 契约同版记录背景的完整语言（做旧纸面 + 印刷颗粒、半调网点、爆炸星与速度线分居三角、中部留净）。`references/theme-cel.md`、`references/theme-sticker.md`、`references/theme-flat.md`

### 修复
- **`SKILL.md` frontmatter 分隔符非法** —— 头部由 `***` 修正为标准 YAML 的 `---`，并补入 `version: 2.4.0`。`SKILL.md`

**English**

### Background
The `cel` / `sticker` / `flat` theme backgrounds were previously drawn in code (halftone dot fields, speed lines, grid paper and hand-drawn doodles, geometric monsters). This release switches all three to one locked raster image per canvas ratio and records the rule plus rejection flags in the three theme contracts. The motivation is not in the record (inferred from the change): the background stops being re-drawn by code and is carried by one fixed image per ratio; the default `paper` theme is untouched.

### Changed
- **Theme backgrounds switched to locked fixed raster assets** — the `Background` component of `cel` / `sticker` / `flat` now renders `Img` + `staticFile`, selecting `bg-<theme>-<169|43|34>.jpg` from `useCanvas().canvas` and filling the canvas with `100%` width/height and `objectFit: cover`; the code-drawn halftone fields, speed lines, grid, doodles and monster SVGs are deleted from all three themes. `assets/lecture-template/src/theme/cel.tsx`, `assets/lecture-template/src/theme/sticker.tsx`, `assets/lecture-template/src/theme/flat.tsx`
- **Nine background rasters committed with provenance** — three per theme (the 16:9 images are 2560×1440, the 4:3 images 2240×1680, the 3:4 images 1680×2240, each matching the aspect ratio of its canvas); `manifests/visual-assets.json` records every id with its sha256, and `manifests/asset-manifest.json` lists all nine ids in the top-level asset table and in every scene's `visual_asset_ids`. `assets/lecture-template/public/bg-*.jpg`, `assets/lecture-template/manifests/visual-assets.json`, `assets/lecture-template/manifests/asset-manifest.json`
- **Three theme contracts rewritten to the fixed-raster rule** — the background sections and rejection flags now read "never restore the code-drawn background, never draw extra ornaments on top of the image, never stretch a wrong-ratio image onto a canvas"; the `cel` contract records the full background language (aged paper with print grain, halftone dot fields, an explosion star and radiating speed lines kept to the corners, clean centre). `references/theme-cel.md`, `references/theme-sticker.md`, `references/theme-flat.md`

### Fixed
- **Invalid `SKILL.md` frontmatter delimiters** — the header now opens with the standard YAML `---` instead of `***`, and `version: 2.4.0` is added. `SKILL.md`

---

## [2.3.0] - 2026-09-05

### 背景与动机
本版提交信息为「重新推导 cel/sticker/flat 三主题配色，并把 flat 改为几何小怪兽」。据改动推断的问题是：三个非默认主题此前的浅色线性与填充透明度太低（细线 0.11–0.18、浅填充 0.08–0.10），卡片内的示例框与标注框会「化」进卡片背景而看不见；同时 flat 主题原本靠右上大靛蓝圆块承载视觉，导致技术头部必须用白字压在色块上。本版把三主题的强调色重新落到统一档位、抬高中性线的对比，并重画 flat 的背景与卡片语言。

### 变更
- **三主题配色按锁定档位重推导** —— `cel` 保持蓝/红双主角，绿色 `#1d9e57`→`#24bc6e`、金色 `#ffc62b`→`#f2b721` 抬到同一档；`sticker` 保持粉色主角，蓝 `#4f9fd8`→`#5ca9e0`、绿 `#4fb894`→`#61d188` 抬入粉彩带；`flat` 保持靛蓝主角，珊瑚 `#ff5d3b`→`#f05f42`、薄荷 `#37c99b`→`#41d27b`、金黄 `#ffcf3f`→`#f0c63c` 在同档下推导。`assets/lecture-template/src/theme/cel.tsx`、`assets/lecture-template/src/theme/sticker.tsx`、`assets/lecture-template/src/theme/flat.tsx`
- **中性线与浅色填充整体抬高对比** —— 三主题的 `line` 类 token 由 0.13–0.18 抬到 0.42–0.45，`lineOrange/lineBlue/lineGreen` 由 0.30–0.40 抬到 0.58–0.62；`mutedFill` / `mutedBar` / `mutedWash` 由 0.12–0.25 抬到 0.18–0.33，`gaugeTrack` 由 0.13–0.14 抬到 0.22，`dotIdle` 同步加深，灯光类 token（`blueLight` / `orangeLight` / `greenLight`）由 0.10 抬到 0.17–0.30。`assets/lecture-template/src/theme/`
- **`flat` 主题重画为几何小怪兽** —— 背景的右上大靛蓝圆块与孟菲斯点缀集整体替换为两只几何小怪兽与四个小道具：右下靛蓝圆球怪（金色触角球、白眼底墨瞳、微笑弧、小短腿，按画布比例锚定 `0.930w, 0.860h`，身体半径 `0.052w`）、左下珊瑚方块怪（边长 `0.058w`、−8° 倾斜、举小手、锯齿嘴）、金黄四角星 / 珊瑚小星 / 薄荷感叹号 / 靛蓝波浪线；全部按画布比例锚定、纯色平涂、禁止渐变与描边。`assets/lecture-template/src/theme/flat.tsx`
- **`flat` 卡片语言更换** —— 卡片由「3.5px 墨色描边 + 2px 白色内衬线 + 墨色硬偏移影」改为「2px 中性灰细线（界定上/左缘）+ 彩色硬偏移实影（默认靛蓝，场景传 `borderColor` 时影子同步变色）」；`paperOutline` 由 3.5 改为 0。`assets/lecture-template/src/theme/flat.tsx`
- **`flat` 字幕由通栏墨条改为悬浮胶囊** —— 由通栏实心墨色条（高 128、文字前橙色小条、文字后薄荷小条）改为底部居中的靛蓝圆角胶囊（圆角 26、内边距 16×40、硬偏移墨影 `7px 7px 0`、底距 40、最大宽度取画幅安全宽度），文字前橙色小圆点、文字后薄荷小圆点，白字加粗。`assets/lecture-template/src/theme/flat.tsx`
- **`flat` 技术头部改用深墨字** —— 头部主色由 `#ffffff` 改为 `#191919`、副色由半透明白改为 `#6f6a63`（原先是为压在右上圆块上而用白字）。`assets/lecture-template/src/theme/flat.tsx`
- **`sticker` 卡片加印刷边并加深投影** —— 贴纸卡的纸张阴影由 0.06/0.10 基准加深到 0.12/0.17 基准，并新增 2.5px 柔棕印刷边（`rgba(74,59,47,0.55)`），使白色模切边在淡薄荷底上保持可辨识；`blueLine` 与胶带色随新蓝值同步。`assets/lecture-template/src/theme/sticker.tsx`
- **主题契约文档同步** —— `theme-cel.md` 记入「蓝红同档双主角、绿金同阶梯推导、不许跳出档位」；`theme-flat.md` 改名为「modern flat geometric monsters」并重写设计语言、锁定 token、背景锚点、拒绝清单（禁止渐变/模糊/暗角、禁止墨框与白内衬、禁止小怪兽位移或改色、禁止通栏字幕条）；`theme-sticker.md` 记入粉彩同阶梯规则并把拒绝清单的「卡片墨框」细化为「5px 赛璐璐式墨框」。`references/theme-cel.md`、`references/theme-flat.md`、`references/theme-sticker.md`
- **默认主题不在本版范围内** —— 本版只改动 `cel` / `sticker` / `flat` 三个主题文件，`assets/lecture-template/src/theme/paper.tsx` 未被改动。`assets/lecture-template/src/theme/paper.tsx`
- **发行元数据更新** —— 发布标签推进到 v2.3.0。`.github/repository-metadata.yml`

### 修复
- **非默认主题上的不可见元素** —— `cel` / `sticker` / `flat` 中示例框与标注框原先使用 0.11–0.18 透明度的细线与 0.08–0.10 透明度的填充，会与卡片背景融为一体；细线 token 现从 0.42–0.45 起、浅填充从 0.17–0.30 起。`assets/lecture-template/src/theme/cel.tsx`、`assets/lecture-template/src/theme/sticker.tsx`、`assets/lecture-template/src/theme/flat.tsx`

**English**

### Background
The commit message reads "re-derive cel/sticker/flat color systems, redesign flat with geometric monsters". The inferred problems are that the three non-default themes had hairlines and light fills at alpha values low enough (lines 0.11–0.18, fills 0.08–0.10) for example and annotation boxes to melt into their cards and become invisible, and that the flat theme carried its composition on a large top-right indigo circle, which forced the technical header to sit as white text on a colour block. This release re-derives every accent onto one locked step, raises neutral contrast, and redraws the flat background and card language.

### Changed
- **Three theme colour systems re-derived on locked steps** — `cel` keeps its blue/red co-leads, lifting green `#1d9e57`→`#24bc6e` and gold `#ffc62b`→`#f2b721` onto the same step; `sticker` keeps its pink lead, lifting blue `#4f9fd8`→`#5ca9e0` and green `#4fb894`→`#61d188` into the pastel band; `flat` keeps its indigo lead, deriving coral `#ff5d3b`→`#f05f42`, mint `#37c99b`→`#41d27b` and sun `#ffcf3f`→`#f0c63c` underneath it. `assets/lecture-template/src/theme/cel.tsx`, `assets/lecture-template/src/theme/sticker.tsx`, `assets/lecture-template/src/theme/flat.tsx`
- **Neutral lines and light fills raised in contrast** — across the three themes the `line` tokens move from 0.13–0.18 to 0.42–0.45 and `lineOrange/lineBlue/lineGreen` from 0.30–0.40 to 0.58–0.62; `mutedFill` / `mutedBar` / `mutedWash` move from 0.12–0.25 to 0.18–0.33, `gaugeTrack` from 0.13–0.14 to 0.22, `dotIdle` is deepened, and the light tokens (`blueLight` / `orangeLight` / `greenLight`) move from 0.10 to 0.17–0.30. `assets/lecture-template/src/theme/`
- **`flat` redesigned around geometric little monsters** — the top-right indigo mega-circle and the whole Memphis accent set are replaced by two monsters and four props: an indigo round blob monster at the bottom right (gold antenna ball, white eyes with ink pupils, smile arc, stub legs; canvas-ratio anchored at `0.930w, 0.860h` with body radius `0.052w`), a coral square monster at the bottom left (side `0.058w`, −8° tilt, raised arms, zigzag mouth), plus a gold four-point star, a small coral star, a mint exclamation mark and an indigo squiggle; all canvas-ratio anchored, flat fills only, no gradients or outlines. `assets/lecture-template/src/theme/flat.tsx`
- **`flat` card language replaced** — cards drop "3.5px ink border + 2px white inset liner + hard offset ink shadow" for "2px neutral gray hairline (defining the top/left edges) + coloured hard offset solid shadow (indigo by default, following the scene's `borderColor`)"; `paperOutline` moves from 3.5 to 0. `assets/lecture-template/src/theme/flat.tsx`
- **`flat` subtitle becomes a floating pill** — the full-width solid ink bar (128px tall, orange tick before the text, mint tick after) becomes a bottom-centred indigo rounded pill (radius 26, padding 16×40, hard offset ink shadow `7px 7px 0`, bottom offset 40, max width taken from the canvas safe width) with an orange dot before the text and a mint dot after it, on bold white type. `assets/lecture-template/src/theme/flat.tsx`
- **`flat` technical header switches to dark ink type** — the header accent moves from `#ffffff` to `#191919` and the sub-colour from translucent white to `#6f6a63` (white was previously needed to read on the top-right circle). `assets/lecture-template/src/theme/flat.tsx`
- **`sticker` cards gain a print edge and a deeper shadow** — the sticker card's paper shadow base is deepened from 0.06/0.10 to 0.12/0.17 and a 2.5px soft-brown print edge (`rgba(74,59,47,0.55)`) is added so the white die-cut edge stays readable on the pale mint page; `blueLine` and the tape colour follow the new blue. `assets/lecture-template/src/theme/sticker.tsx`
- **Theme contract docs updated** — `theme-cel.md` records the "blue+red co-leads on one step, green+gold derived on the same step, never off-step" rule; `theme-flat.md` is retitled "modern flat geometric monsters" and rewrites the design language, locked tokens, background anchors and rejection flags (no gradients/blur/vignette, no ink borders or white inset liners, no moved or recoloured monsters, no full-width subtitle bar); `theme-sticker.md` records the pastel one-step rule and refines its rejection flag from "ink borders on cards" to "5px cel-style ink frames". `references/theme-cel.md`, `references/theme-flat.md`, `references/theme-sticker.md`
- **Default theme out of scope for this release** — only the `cel` / `sticker` / `flat` theme files change; `assets/lecture-template/src/theme/paper.tsx` is not modified. `assets/lecture-template/src/theme/paper.tsx`
- **Release metadata updated** — the release tag advances to v2.3.0. `.github/repository-metadata.yml`

### Fixed
- **Invisible elements on non-default themes** — example and annotation boxes across `cel` / `sticker` / `flat` used hairlines at 0.11–0.18 alpha and fills at 0.08–0.10 alpha that melted into the cards; line tokens now start at 0.42–0.45 alpha and light fills at 0.17–0.30. `assets/lecture-template/src/theme/cel.tsx`, `assets/lecture-template/src/theme/sticker.tsx`, `assets/lecture-template/src/theme/flat.tsx`

---

## [2.2.0] - 2026-09-05

### 背景与动机
本版是主题皮肤体系落地 + 命令行提速。提交信息给出的动机有三条：一、把讲稿模板锁定的美学内核抽成可插拔皮肤（`new-project --style=` 一次选择）；二、新增 `review-frames` 命令，把「一段帧 + 接触片」放在同一次打包与同一次浏览器里完成（多帧检查比逐帧 still 约快 3 倍）；三、`remotionRender` 复用本机已缓存的 remotion 浏览器，避免重新触发 100MB+ 的下载。主题侧的中间迭代也留有动机记录：cel 由奶油底改为近白、sticker 改为淡薄荷、flat 改为冷灰蓝并做细节收敛，都是为了与默认暖米纸主题明确区分。

### 新增
- **主题皮肤体系（四主题）** —— 模板锁定的美学内核抽为可插拔皮肤，由 `src/theme/active.ts` 一行开关决定，并由 `new-project ./dir --style=<id>` 在开拍时写入。共用不变的部分：画布坐标、字阶、动效契约与看门脚本；主题只换调色板、卡片皮肤、背景装饰、调色层与字幕外壳。四个主题：`paper`（默认暖米纸笔记本）、`cel`（动漫赛璐璐分镜）、`sticker`（卡通贴纸手账）、`flat`（现代扁平几何）。`assets/lecture-template/src/theme/`
- **主题契约接口与画布引擎拆分** —— 新增 `theme/types.ts`（`ThemePalette` / `ThemeAesthetic` / `Theme` 接口，含 13 个场景层柔色 token 与 `Background` / `Paper` / `Grade` / `SubtitleChrome` / `extras` 契约）与 `theme/canvas.ts`（`MODES` 画布参数表、`CanvasContext`、`useCanvas()`）。`assets/lecture-template/src/theme/types.ts`、`assets/lecture-template/src/theme/canvas.ts`
- **`new-project --style=` 主题选择** —— 启动器新增 `THEME_IDS = ['paper','cel','sticker','flat']`，按值改写被复制工程的 `src/theme/active.ts`；非法值直接失败并提示合法取值，别名 `--classic` 与用法文本同步。`scripts/notebook-video.mjs`
- **`review-frames` 命令** —— 新增 `notebook-video review-frames PROJECT OUTPUT START END [COMPOSITION]`：一次 `render` 出帧区间，并自动用同一支 mp4 生成接触片（`-contact.jpg`），接触片抽帧数与拼版由时长决定（>60s 用 24 帧 4×6，否则 12 帧 4×3）。接触片生成抽成共用实现，`validate-video` 改为调用同一函数。`scripts/notebook-video.mjs`
- **主题契约文档** —— 新增 `references/theme-system.md`（主题边界：可换什么、绝不可换什么、后续新增主题的步骤）与三份逐主题锁定清单 `theme-cel.md`、`theme-sticker.md`、`theme-flat.md`。`references/`
- **主题完整性与开关门禁** —— `validate-skill-consistency.py` 要求 7 个主题文件、4 份主题文档齐备，且 `active.ts` 必须默认指向 `./paper`（cel / sticker 还须用 `useCanvas()` 锚定装饰）；`selftest.py` 增至 9 项检查，加入主题文件清单、默认主题开关与非法 `--style` 被拦且不污染目标目录；CI 增加 `--style=cel` 冒烟断言（主题文件存在、`active.ts` 被改写、首行为 `import`）并开始运行 `selftest.py`。`scripts/validate-skill-consistency.py`、`scripts/selftest.py`、`.github/workflows/validate.yml`

### 变更
- **场景柔色 token 化** —— 引擎中约 20 处硬编码的场景色（地球淡色、主干线、合并圆点、未激活填充与条、LOCAL HOST 胶囊底、CTA 波浪起始色、章节序号渐变色、仪表轨道、对勾投影、舞台背板、技术头部主副色）改读 `ThemePalette` 的 13 个柔色 token，`paper` 保持历史精确值。`assets/lecture-template/src/index.tsx`、`assets/lecture-template/src/theme/types.ts`
- **浏览器解析改为优先复用本机缓存** —— `remotionRender` 的浏览器可执行文件解析顺序变为：显式 `REMOTION_BROWSER_EXECUTABLE` → Windows 下 `%LOCALAPPDATA%\remotion-browser\chrome-headless-shell\win64\chrome-headless-shell.exe`（若已存在），避免重复触发 100MB+ 的下载。`scripts/notebook-video.mjs`
- **技能文档补入主题与帧检查流程** —— `SKILL.md` 新增主题选择说明（开拍时一次性选定画幅与主题，并路由到唯一一份主题契约）、`review-frames` 用法与「一次区间渲染优于多次单帧 still」的实测收益。`SKILL.md`
- **演示资产收为单一 16:9 sticker 主题样片** —— 出厂演示改为一份 16:9（2560×1440）全程片，以 `sticker` 主题渲染，并重出动图预览；README 的画幅比例矩阵收为一行默认值。`assets/demo/notebook-video-demo.mp4`、`assets/demo/notebook-video-demo.webp`、`README.md`、`README.en.md`

### 移除
- **4:3 与 3:4 演示资产** —— 删除 `notebook-video-demo-43.mp4/.webp` 与 `notebook-video-demo-34.mp4/.webp`，README 中对应的矩阵行同步删除。`assets/demo/`

### 安全
- **依赖告警修复** —— 示例工程锁文件的 `fast-uri` 由 `3.1.5` 升到 `3.1.7`；讲稿模板锁文件的 `fast-uri` 由 `3.1.4` 升到 `3.1.7`、`browserslist` 由 `4.28.6` 升到 `4.28.8`，并连带更新其传递依赖（`baseline-browser-mapping`、`caniuse-lite`、`electron-to-chromium`、`node-releases`、`update-browserslist-db`、`postcss`、`nanoid`）。`assets/example-project/package-lock.json`、`assets/lecture-template/package-lock.json`

**English**

### Background
This release lands the theme-skin system and speeds up the command line. The commit record gives three motives: extract the lecture template's locked aesthetic core into a pluggable skin chosen once with `new-project --style=`; add a `review-frames` command that renders a frame range plus a contact sheet in a single bundle and a single browser (measured ~3x faster than serial stills for multi-frame checks); and make `remotionRender` reuse the locally cached remotion browser instead of triggering a fresh 100MB+ download. The mid-iteration theme commits also record their motive: cel moved from a cream base to near-white, sticker to pale mint and flat to a cool gray-blue with a detail pass, all to separate them clearly from the default warm-ivory theme.

### Added
- **Theme skin system (four themes)** — the template's locked aesthetic core becomes a pluggable skin selected by a one-line switch in `src/theme/active.ts` and written at kickoff by `new-project ./dir --style=<id>`. Shared and unchanged: canvas coordinates, type scale, motion contracts and QA gates; a theme swaps only the palette, card skin, background decoration, grade layer and subtitle chrome. The four themes are `paper` (default warm-ivory notebook), `cel` (anime cel-shading storyboard), `sticker` (cartoon sticker journal) and `flat` (modern flat geometric). `assets/lecture-template/src/theme/`
- **Theme contract interface and canvas engine split out** — adds `theme/types.ts` (`ThemePalette` / `ThemeAesthetic` / `Theme`, including 13 scene soft-colour tokens and the `Background` / `Paper` / `Grade` / `SubtitleChrome` / `extras` contract) and `theme/canvas.ts` (the `MODES` canvas table, `CanvasContext` and `useCanvas()`). `assets/lecture-template/src/theme/types.ts`, `assets/lecture-template/src/theme/canvas.ts`
- **`new-project --style=` theme selection** — the launcher adds `THEME_IDS = ['paper','cel','sticker','flat']` and rewrites the copied project's `src/theme/active.ts`; an unknown value fails with the valid list, and the `--classic` alias and usage text are updated. `scripts/notebook-video.mjs`
- **`review-frames` command** — adds `notebook-video review-frames PROJECT OUTPUT START END [COMPOSITION]`: one `render` produces the frame range and automatically builds a contact sheet (`-contact.jpg`) from the same mp4, with the sample count and tile layout decided by duration (24 frames in 4×6 above 60s, otherwise 12 frames in 4×3). Contact-sheet generation is extracted into a shared helper and `validate-video` now calls it. `scripts/notebook-video.mjs`
- **Theme contract docs** — adds `references/theme-system.md` (the theme boundary: what may change, what never may, and how to add a theme later) plus the per-theme locked checklists `theme-cel.md`, `theme-sticker.md` and `theme-flat.md`. `references/`
- **Theme integrity and switch gates** — `validate-skill-consistency.py` requires the seven theme files and four theme docs to exist and `active.ts` to default to `./paper` (cel and sticker must also anchor decoration via `useCanvas()`); `selftest.py` grows to 9 checks adding the theme file list, the default theme switch, and an illegal `--style` being blocked without polluting the target directory; CI adds a `--style=cel` smoke assertion (theme file present, `active.ts` rewritten, first line an `import`) and starts running `selftest.py`. `scripts/validate-skill-consistency.py`, `scripts/selftest.py`, `.github/workflows/validate.yml`

### Changed
- **Scene soft colours tokenised** — about 20 hardcoded scene colours in the engine (globe tint, main branch line, merge dot, idle fills and bars, LOCAL HOST wash, CTA wave start, chapter-number gradient, gauge track, check glow, stage tint, header accent and sub) now read the 13 `ThemePalette` soft tokens, with `paper` keeping its historical exact values. `assets/lecture-template/src/index.tsx`, `assets/lecture-template/src/theme/types.ts`
- **Browser resolution reuses the local cache first** — `remotionRender` now resolves its browser executable in the order explicit `REMOTION_BROWSER_EXECUTABLE` → on Windows `%LOCALAPPDATA%\remotion-browser\chrome-headless-shell\win64\chrome-headless-shell.exe` when present, so the 100MB+ download is not triggered again. `scripts/notebook-video.mjs`
- **Skill docs cover themes and the frame-check flow** — `SKILL.md` documents theme selection (canvas and theme are chosen once at kickoff and routed to exactly one theme contract) and the `review-frames` usage with the measured benefit of one range render over several single stills. `SKILL.md`
- **Demo reduced to a single 16:9 sticker-themed film** — the bundled demo becomes one 16:9 (2560×1440) full film rendered in the `sticker` theme with a regenerated animated preview, and the README's ratio matrix narrows to one default row. `assets/demo/notebook-video-demo.mp4`, `assets/demo/notebook-video-demo.webp`, `README.md`, `README.en.md`

### Removed
- **4:3 and 3:4 demo assets** — `notebook-video-demo-43.mp4/.webp` and `notebook-video-demo-34.mp4/.webp` are deleted, along with their README matrix rows. `assets/demo/`

### Security
- **Dependency advisories resolved** — in the example project's lock file `fast-uri` moves from `3.1.5` to `3.1.7`; in the lecture template's lock file `fast-uri` moves from `3.1.4` to `3.1.7` and `browserslist` from `4.28.6` to `4.28.8`, with their transitive dependencies refreshed alongside (`baseline-browser-mapping`, `caniuse-lite`, `electron-to-chromium`, `node-releases`, `update-browserslist-db`, `postcss`, `nanoid`). `assets/example-project/package-lock.json`, `assets/lecture-template/package-lock.json`

---

## [2.1.1] - 2026-09-03

### 背景与动机
本版提交信息为「复配音时间对齐、校验器与长片文档修正」。据改动推断的问题是：旁白文本锁定后若更换音色或模型，各章时长会变，所有场景挂载守卫与音效帧都会随之漂移；本版给出「把新合成对回已批准时间轴」的正式流程，而不必重写场景。同版修掉视觉资产哈希大小写被误判为不匹配，并补记长片路径与打包器踩坑。

### 新增
- **复配音时间对齐脚本** —— 新增 `scripts/match-timing.py`。`--lock` 把已批准的 `manifests/chapters.json` 快照为 `manifests/chapters-timing-lock.json`；默认模式读取该快照，对 TTS 适配器产出的分段 `audio/seg{N}-*.wav` 逐章施加保持音高的 `atempo`（超出一档时自动串接多级），按标准静音间隔重新拼接、做响度归一（`loudnorm=I=-16:TP=-1.5:LRA=11`，48kHz 立体声，192kbps），并把扁平的词级时间流按各章比例缩放到锁定帧表上，最后用锁定表回写 `manifests/chapters.json`。任一章时长比超出 **0.4–2.5** 即断言失败；结尾打印锁定总时长对应的帧数（30fps）。`scripts/match-timing.py`
- **复配音流程文档** —— `references/tts-audio.md` 新增「不重排时间的复配音」小节，给出 `--lock` → 合成 → `speed-post` → 对齐 → 重建语义字幕的调用序列，并注明对齐后必须重建字幕（换音色一定会改变章内词级时间），同时为该文档补入目录。`references/tts-audio.md`

### 变更
- **长片路径写明** —— `references/remotion-architecture.md` 新增「长片路径：保持 `TIMELINE_SCALE = 1`」小节：新写长片时把 `DURATION` 设为交付总帧数、所有挂载守卫/提示/边界/音效帧直接以交付帧书写，从而避开分数缩放；文中记录该路径在 4996 帧 / 22 章的长片上验证过，并指出出厂讲稿模板自带 1126 帧时间轴、900 帧这一数字对应视觉总监示例工程。`references/remotion-architecture.md`
- **打包器踩坑记录** —— 同文件新增「相邻泛型标注箭头组件的解析坑」小节：紧跟在以密集 JSX 结尾的组件之后的组件可能被误解析，报错行落在无辜的下一行；给出三种可靠写法（改用 `function` 声明、把前一组件从跨行裸片段改为显式包裹、在两组件间插一条普通语句）与用打包器的 esbuild `tsx` loader 逐步前缀转换来定位触发点的做法。`references/remotion-architecture.md`

### 修复
- **视觉资产哈希大小写被误判** —— `validate-visual-plan` 改为把资产记录的 `sha256` 统一转小写后再比对，使 `Get-FileHash` 等工具产出的全大写摘要不再被当作不匹配。`scripts/validate-visual-plan.py`

**English**

### Background
The commit message reads "re-voicing timing match, validator and long-film doc fixes". The inferred problem is that once the narration text is locked, changing the voice or model shifts every chapter duration, which drags every scene mount guard and sound frame with it; this release provides a formal "align the new synthesis back to the approved timeline" procedure instead of re-authoring scenes. The same version fixes uppercase visual-asset hashes being treated as mismatches and records the long-film path and a bundler pitfall.

### Added
- **Re-voicing timing-alignment script** — adds `scripts/match-timing.py`. `--lock` snapshots the approved `manifests/chapters.json` to `manifests/chapters-timing-lock.json`; the default mode reads that snapshot, applies a pitch-preserving `atempo` per chapter to the adapter's segment files `audio/seg{N}-*.wav` (chaining multiple stages when one is out of range), re-joins with the standard silence gap, normalises loudness (`loudnorm=I=-16:TP=-1.5:LRA=11`, 48kHz stereo, 192kbps) and scales the flat word-timing stream onto the locked frame table, then writes the lock back over `manifests/chapters.json`. Any chapter ratio outside **0.4–2.5** fails an assertion; the run ends by printing the locked total in frames at 30fps. `scripts/match-timing.py`
- **Re-voicing procedure documented** — `references/tts-audio.md` gains a "re-voicing without re-timing" section with the `--lock` → synthesise → `speed-post` → align → rebuild-captions sequence, notes that captions must be rebuilt afterwards (a new voice always changes intra-chapter word timing), and gains a table of contents. `references/tts-audio.md`

### Changed
- **Long-film path written down** — `references/remotion-architecture.md` gains a "long-film path: keep `TIMELINE_SCALE = 1`" section: for a newly authored long film set `DURATION` to the total delivery frame count and author every mount guard, cue, boundary and sound frame directly in delivery frames, avoiding fractional scale math; it records that this path was verified on a 4996-frame / 22-chapter film, and notes the bundled lecture template ships a 1126-frame timeline while the 900-frame figure corresponds to the visual-director example project. `references/remotion-architecture.md`
- **Bundler pitfall recorded** — the same file gains an "adjacent generic-annotated arrow components" section: a component placed immediately after one whose body ends in dense JSX can be misparsed, with the reported error landing on the innocent following line; it lists three reliably parsing workarounds (use a `function` declaration, wrap the preceding value in an explicit element instead of a multi-line bare fragment, or separate the two components with a plain statement) and describes isolating the trigger by transforming growing prefixes of the file with the bundler's esbuild `tsx` loader. `references/remotion-architecture.md`

### Fixed
- **Visual-asset hashes rejected over letter case** — `validate-visual-plan` now lowercases the recorded `sha256` before comparing, so all-uppercase digests such as those produced by `Get-FileHash` are no longer reported as mismatches. `scripts/validate-visual-plan.py`

---

## [2.1.0] - 2026-09-02

### 背景与动机
本版提交信息为「弹性波浪字体、Caveat 手写体与多画幅渲染」。据改动推断的动因是：v2.0.0 的 `CANVAS` 常量是编译期单值，同一份代码无法一次输出三种画幅，且场景切换处存在跨场景重叠与闪烁；本版把画幅改为运行期上下文并注册三个独立合成，同时把场景生命周期硬隔离。更细的逐条动机未在记录中留存。

### 新增
- **三画幅独立合成（Canonical Tri-Aspect Rendering Engine）** —— 用 `CanvasContext` + `useCanvas()` 取代编译期 `CANVAS` 常量，新增 `FilmLayout` 包装层与三个合成：`NotebookVideoFilm-16x9`（2560×1440）、`NotebookVideoFilm-4x3`（1920×1440）、`NotebookVideoFilm-3x4`（1440×1920）；原 `NotebookVideoFilm` 保留并等同 16:9，一份代码可同时渲染三种画幅。`assets/lecture-template/src/index.tsx`
- **Caveat 手写体标注** —— 新增 `Caveat-Latin.woff2` 与 `Caveat` 字体族，用于手写风格标注贴（如 `lonely code`、`start small`、`packaging`、`ongoing triage`、`always by your side`）。`assets/lecture-template/public/fonts/Caveat-Latin.woff2`、`assets/lecture-template/src/index.tsx`
- **`PillTag` 胶囊标签组件** —— 新增可复用胶囊标签（默认橙字 + 橙色淡底），用于 EP 标签行。`assets/lecture-template/src/index.tsx`
- **调色板补入淡色槽位** —— 新增 `orangeLight` 等浅色底槽，供胶囊标签与结论条使用。`assets/lecture-template/src/index.tsx`

### 变更
- **`JumpInText` 升级为 4 段双轴弹性过冲** —— 波浪位移改为 4 段关键帧（纵向 `[14,-6,1.5,0]`、横向 `[3,-1,0,0]`、`rotX` `[40,-5,0]`），并加入逐字点亮色到墨色的颜色过渡。`assets/lecture-template/src/index.tsx`
- **场景生命周期硬隔离** —— 场景由统一 `stageFade` 改为各自 `return null` 的严格挂载窗口（场景 1 `f>212` 卸载、场景 2 `f<210||f>414` 卸载、场景 3 `f<415||f>680` 卸载、场景 4 `f<680` 挂载）与 `intro`/`outro`/`exitSlide` 三段自持淡入淡出；场景 2 出口定在 396~412 帧并带向左微滑，场景 3 严格在第 416 帧挂载。`assets/lecture-template/src/index.tsx`
- **浮动模块卡改为容器内文件清单** —— 删除 `Module` 组件与其浮动动画，改为场景内的「标准化模板」容器：带标题栏的圆角容器内以行式条目依次滑入点亮（`README.md`、`LICENSE`、`CI / Actions`）。`assets/lecture-template/src/index.tsx`
- **排版层级与色彩细化** —— 场景标题改用 `JumpInText`、章节序号与技术头部改用 `Clash` / `Space` 与更大字距、节点卡标签改用 `Space,Kai` 加粗；示例场景的节点卡、Gauge 环、地球描边等几何与透明度同步微调。`assets/lecture-template/src/index.tsx`

**English**

### Background
The commit message reads "elastic wave typography, Caveat handwriting and multi-aspect rendering". The inferred drivers are that v2.0.0's `CANVAS` constant was a compile-time single value, so one codebase could not emit all three canvases at once, and that scene transitions suffered from cross-scene overlap and flicker; this release turns the canvas into a runtime context with three separately registered compositions and hard-isolates scene lifecycles. Per-item rationale beyond that was not preserved in the record.

### Added
- **Three independent compositions (canonical tri-aspect rendering engine)** — `CanvasContext` plus `useCanvas()` replace the compile-time `CANVAS` constant, a `FilmLayout` wrapper is added, and three compositions are registered: `NotebookVideoFilm-16x9` (2560×1440), `NotebookVideoFilm-4x3` (1920×1440) and `NotebookVideoFilm-3x4` (1440×1920); the original `NotebookVideoFilm` id is kept and is equivalent to 16:9, so one codebase renders all three canvases. `assets/lecture-template/src/index.tsx`
- **Caveat handwriting annotations** — adds `Caveat-Latin.woff2` and the `Caveat` family for hand-drawn annotation stickers (for example `lonely code`, `start small`, `packaging`, `ongoing triage`, `always by your side`). `assets/lecture-template/public/fonts/Caveat-Latin.woff2`, `assets/lecture-template/src/index.tsx`
- **`PillTag` pill component** — a reusable pill label (orange text on a light orange fill by default), used for the EP tag row. `assets/lecture-template/src/index.tsx`
- **Light colour slots added to the palette** — new light-fill slots such as `orangeLight` for pill labels and conclusion strips. `assets/lecture-template/src/index.tsx`

### Changed
- **`JumpInText` upgraded to a 4-stage two-axis elastic overshoot** — the wave displacement becomes a 4-keyframe trajectory (vertical `[14,-6,1.5,0]`, horizontal `[3,-1,0,0]`, `rotX` `[40,-5,0]`) with a per-glyph colour transition from an ignition colour to ink. `assets/lecture-template/src/index.tsx`
- **Scene lifecycles hard-isolated** — scenes move from a shared `stageFade` to strict mount windows with their own `return null` guards (scene 1 unmounts at `f>212`, scene 2 at `f<210||f>414`, scene 3 at `f<415||f>680`, scene 4 mounts at `f<680`) plus self-owned `intro`/`outro`/`exitSlide` fades; scene 2 exits over frames 396–412 with a small leftward slide and scene 3 mounts exactly at frame 416. `assets/lecture-template/src/index.tsx`
- **Floating module cards become an in-container file list** — the `Module` component and its floating animation are deleted in favour of a "standardized template" container inside the scene: a rounded container with a title bar whose rows slide in and light up in order (`README.md`, `LICENSE`, `CI / Actions`). `assets/lecture-template/src/index.tsx`
- **Typographic hierarchy and colour refined** — scene titles use `JumpInText`, chapter numbers and the technical header use `Clash` / `Space` with wider letter-spacing, and node card labels use bold `Space,Kai`; node cards, gauge rings and globe strokes are adjusted in geometry and opacity. `assets/lecture-template/src/index.tsx`

---

## [2.0.0] - 2026-09-02

### 背景与动机
本版提交信息为「电影级动效与音频体系升级 —— Tibo 3D 滚轮数字、Lo-Fi 背景乐、UI 音效与三画幅演示重渲」。本版采用主版本号，但从 v1.9.1 到 v2.0.0 的 diff **未能识别到明确的不兼容变更**：三个画布参数表、设计坐标、`DURATION`（1126 帧）、字幕契约、字阶与场景分界均未改动，合成 id 仍为 `NotebookVideoFilm`。唯一改变了既有契约的一点在 Assets 小节说明：`AssetGate` 不再预加载音频资源。是否以此作为主版本号依据，记录中未留存说明。

### 新增
- **`RollDigit` 3D 滚轮翻牌数字** —— 新增组件，用投影压缩的 `rotateX`（`cos` 透视压缩）在旧字符与新字符之间翻转，并带纵向位移与颜色过渡；用于发版场景把 `v1.0` 翻成 `v1.1`。`assets/lecture-template/src/index.tsx`
- **发版状态提示** —— 数字翻转后跟随一枚对勾徽章与绿色「准备发版」文字。`assets/lecture-template/src/index.tsx`
- **Lo-Fi 背景乐与 UI 音效资产** —— 两个工程的 `public/sfx/` 新增 `bgm.mp3`、`click.ogg`、`drop.ogg`、`toggle.ogg`。`assets/lecture-template/public/sfx/`、`assets/example-project/public/sfx/`
- **三画幅演示全套重渲** —— 16:9、4:3、3:4 三个画幅的成片与动态预览全部换为新版渲染。`assets/demo/`

### 变更
- **声音层扩展** —— `Sound` 由单行片段改为函数组件：在原有旁白与四类动作音效之外，加入 `bgm.mp3` 作为循环背景乐，音量按帧插值（0 → 0.08 → 0.08 → 0，首尾各留淡入淡出段）；新增三组 UI 音效序列（`click.ogg` 4 处、`toggle.ogg` 1 处、`drop.ogg` 4 处）。`assets/lecture-template/src/index.tsx`
- **既有音效音量微调** —— `paper-rustle` .13→.12、`data-whoosh` .12→.11、`paper-tap` .15→.14、`chime` .18→.16。`assets/lecture-template/src/index.tsx`
- **吉祥物加入呼吸动效** —— `Mascot` 由内联单行改为多行组件，`svg` 增加 `1 + 0.016*sin(f*0.16)` 的正弦缩放（以底部为原点），与原有眨眼与挥手叠加。`assets/lecture-template/src/index.tsx`
- **演示资产与发行元数据更新** —— 发布元数据标签推进到 v2.0.0。`.github/repository-metadata.yml`

### 移除
- **资产门不再预加载音频** —— 删掉 `preloadAudio` 辅助函数，`AssetGate` 的 `delayRender` 文案由「等待字体与音频资源」改为「等待字体」，等待内容只剩字体（超时 60s→120s），不再等待旁白与音效文件；`Sound` 内的 `<Audio>` 元素随之成为音频可用性的唯一来源。`assets/lecture-template/src/index.tsx`

**English**

### Background
The commit message reads "cinematic motion and audio system upgrade — Tibo 3D roll digit, Lo-Fi BGM, UI SFX and refreshed 3-canvas demos". The version takes a major number, but the diff from v1.9.1 to v2.0.0 **does not contain an identifiable incompatible change**: the three canvas parameter tables, design coordinates, `DURATION` (1126 frames), subtitle contract, type scale and scene boundaries are unchanged, and the composition id remains `NotebookVideoFilm`. The only change that alters an existing contract is noted under Removed: `AssetGate` no longer preloads audio assets. Whether that is the intended basis for the major number is not stated in the record.

### Added
- **`RollDigit` 3D rolling flip digit** — a new component flips from an old character to a new one using projection-compressed `rotateX` (`cos` perspective squash) with vertical offset and a colour transition; the release scene uses it to roll `v1.0` to `v1.1`. `assets/lecture-template/src/index.tsx`
- **Release status cue** — the rolled digit is followed by a check badge and green "准备发版" text. `assets/lecture-template/src/index.tsx`
- **Lo-Fi background track and UI SFX assets** — `public/sfx/` in both projects gains `bgm.mp3`, `click.ogg`, `drop.ogg` and `toggle.ogg`. `assets/lecture-template/public/sfx/`, `assets/example-project/public/sfx/`
- **All three canvas demos re-rendered** — the 16:9, 4:3 and 3:4 films and their animated previews are all replaced with new renders. `assets/demo/`

### Changed
- **Audio layer extended** — `Sound` becomes a function component: alongside the existing narration and four action-sound groups it adds `bgm.mp3` as a looping background track whose volume is interpolated across frames (0 → 0.08 → 0.08 → 0, with fade-in and fade-out segments), plus three new UI SFX sequences (`click.ogg` at 4 frames, `toggle.ogg` at 1 frame, `drop.ogg` at 4 frames). `assets/lecture-template/src/index.tsx`
- **Existing SFX volumes retuned** — `paper-rustle` .13→.12, `data-whoosh` .12→.11, `paper-tap` .15→.14, `chime` .18→.16. `assets/lecture-template/src/index.tsx`
- **Mascot gains a breathing motion** — `Mascot` goes from an inline one-liner to a multi-line component whose `svg` applies a `1 + 0.016*sin(f*0.16)` sine scale about its base, composing with the existing blink and arm wave. `assets/lecture-template/src/index.tsx`
- **Demo assets and release metadata updated** — the release metadata tag advances to v2.0.0. `.github/repository-metadata.yml`

### Removed
- **Asset gate no longer preloads audio** — the `preloadAudio` helper is deleted and `AssetGate`'s `delayRender` message changes from "waiting for fonts and audio assets" to "waiting for fonts", with the wait reduced to fonts only (timeout 60s→120s); narration and SFX files are no longer awaited, so the `<Audio>` elements inside `Sound` are now the only source of audio availability. `assets/lecture-template/src/index.tsx`

---

## [1.9.1] - 2026-09-02

### 背景与动机
本版把 v1.9.0 的渲染结果固化成文档契约。提交信息写明动机：「锁定高级动效契约 —— 文档现在精确规定 v1.9 实际渲染出来的东西」。据改动推断的问题是：v1.9 换了镜头、字体与字幕，但参考文档与锁定样式契约仍写着「镜头固定」「撕纸字幕条 + 橙色定位环 + 蓝色状态环」，文档与实际渲染不一致；同一批还把示例工程里的字幕组件补齐到同一形态，并修掉 CI 里一处因字体迁移而过期的断言。

### 变更
- **动效契约从「固定镜头」改为「镜头运动」** —— `references/motion-design.md` 由「保持相机固定，运动属于独立建模的物体」改写为 CameraRig 连续镜头轨道（16:9 与 3:4 关键帧表、4:3 复用横向轨道、`scale` 恒 ≥1、指数滞后跟焦），并把推镜、逐字旋入、字母波浪、图形旋入、逐词字幕浮现写入标准动效清单。`references/motion-design.md`
- **字幕契约全套升级为「底部纯文字」** —— `references/visual-system.md`、`references/official-aesthetic-system.md`、`references/remotion-architecture.md`、`references/quality-checklist.md`、`references/canvas-modes.md`、`references/subtitle-timing.md` 与 `SKILL.md` 统一改为：无底条、无撕纸轮廓、无橙色定位环与蓝色状态环；左右边距沿用各画幅值，底距统一 18px；逐词浮现、字间错峰 0.9 帧、6px 淡入上移、比词起点提前 180ms；隐藏的全宽占位保证不横向抖动。`references/`、`SKILL.md`
- **锁定样式契约的字幕段重写** —— `subtitle_input` 由 `clean-white-torn-wave-input` 改名为 `bottom-pinned-pure-caption-reveal`，边界由 `[188,934,1732,1046]` 改为 `[188,1006,1732,1062]`，`paper` 改为透明无条、`contour` 改为 `none`、阴影改为 `text-shadow`，并删除定位环、内衬线、`bounds_by_mode`、`font_px_by_mode` 等字段。`references/locked-style-contract.json`
- **画幅字幕坐标表更新** —— `references/canvas-modes.md` 的「字幕条 bottom/height」行改为「字幕文字 bottom（无条）18」。`references/canvas-modes.md`
- **示例工程字幕组件同步** —— 规范示例的 `Subtitle` 由撕纸条 + 橙色定位环 + 蓝色状态环改为同一套底部纯文字逐词浮现实现。`assets/example-project/src/index.tsx`
- **SKILL.md 锁定元素清单更新** —— 「干净白色下缘撕纸字幕」改为「底部纯文字字幕，逐词浮现、无装饰条」，并把 CameraRig、JumpInText、WaveText、图形旋入与逐词浮现列入锁定高级动效契约，同时要求开拍前必读动效与视觉系统文档。`SKILL.md`

### 修复
- **CI 冒烟断言指向已迁移的许可证文件名** —— 两条 `new-project` 冒烟断言由 `public/SourceHanSans-LICENSE.txt` 改为 `public/LICENSE-OFL-1.1-LXGW.txt`。`.github/workflows/validate.yml`
- **示例工程校验的字幕边界同步** —— `validate-official-example.py` 的字幕边界期望值改为 `[188,1006,1732,1062]`。`scripts/validate-official-example.py`

**English**

### Background
This release turns what v1.9.0 renders into a documented contract. The commit message states the motivation: "lock premium motion contracts — docs now prescribe exactly what v1.9 renders". The inferred problem is that v1.9 changed the camera, the typeface and the subtitle, while the reference docs and the locked style contract still described a fixed camera and a torn-paper subtitle bar with an orange locator and blue status ring, so documentation and rendering disagreed; the same batch brings the example project's subtitle component to the same shape and fixes one CI assertion left stale by the font migration.

### Changed
- **Motion contract moves from "keep the camera fixed" to camera motion** — `references/motion-design.md` is rewritten from "keep the camera fixed, motion belongs to independently modelled objects" to the CameraRig continuous camera track (per-canvas keyframe tables for 16:9 and 3:4, 4:3 reusing the landscape track, scale always >=1, exponential lag follow-focus), and camera push, per-glyph flip-in, letter-wave typing, figure roll-in and per-word subtitle reveal join the standard motion list. `references/motion-design.md`
- **Subtitle contract upgraded everywhere to bottom-pinned pure text** — `references/visual-system.md`, `references/official-aesthetic-system.md`, `references/remotion-architecture.md`, `references/quality-checklist.md`, `references/canvas-modes.md`, `references/subtitle-timing.md` and `SKILL.md` all become: no bar, no torn contour, no orange locator and no blue ring; horizontal margins keep each canvas's value and the bottom offset is a uniform 18px; per-word reveal, per-character stagger of 0.9 frames, a 6px fade-slide, 180ms ahead of the word start; a hidden full-width placeholder keeps the line from shifting horizontally. `references/`, `SKILL.md`
- **Locked style contract's subtitle block rewritten** — `subtitle_input` is renamed from `clean-white-torn-wave-input` to `bottom-pinned-pure-caption-reveal`, its bounds change from `[188,934,1732,1046]` to `[188,1006,1732,1062]`, `paper` becomes transparent (no bar), `contour` becomes `none`, the shadow becomes a `text-shadow`, and the locator, inner liner, `bounds_by_mode` and `font_px_by_mode` fields are dropped. `references/locked-style-contract.json`
- **Canvas subtitle coordinate table updated** — the "subtitle strip bottom/height" row in `references/canvas-modes.md` becomes "subtitle text bottom (no bar) 18". `references/canvas-modes.md`
- **Example project's subtitle component brought in line** — the official example's `Subtitle` moves from the torn bar with an orange locator and blue ring to the same bottom-pinned per-word reveal implementation. `assets/example-project/src/index.tsx`
- **`SKILL.md` locked-elements list updated** — "clean white lower torn-wave subtitle" becomes "bottom-pinned pure caption text with per-word reveal, no decorative bar", the locked premium motion contracts (CameraRig, JumpInText, WaveText, figure roll-in, per-word reveal) are declared, and reading the motion and visual-system documents before directing scenes becomes mandatory. `SKILL.md`

### Fixed
- **CI smoke assertions pointed at the migrated licence filename** — two `new-project` smoke assertions change from `public/SourceHanSans-LICENSE.txt` to `public/LICENSE-OFL-1.1-LXGW.txt`. `.github/workflows/validate.yml`
- **Example-project validator subtitle bounds synced** — the expected subtitle bounds in `validate-official-example.py` become `[188,1006,1732,1062]`. `scripts/validate-official-example.py`

---

## [1.9.0] - 2026-09-02

### 背景与动机
本版是模板的「质感升级固化」：提交信息写明把讲稿模板升级为电影级基线，并列出双画幅镜头、逐字动效、字幕重构、字体统一与时间轴重排。可推断的动因是：v1.7.0 引入三画幅后，模板需要一套与画幅无关的镜头语言与统一字体栈，且旧的展示体 / 黑体资产与许可证被视为待替换的遗留项。更细的逐条动机未在记录中留存。

### 新增
- **`CameraRig` 双画幅镜头层** —— 新增全局镜头组件，用 `translate + scale` 模拟相机；16:9 与 3:4 各有一张关键帧表（`CAM_KEYS_L` / `CAM_KEYS_P`），段内用贝塞尔缓动，并对目标轨迹做指数加权采样实现「跟焦滞后」；`scale` 恒 ≥1 保证不露底，镜头包在场景之外，场景交叉淡变发生在连续运动中。`assets/lecture-template/src/index.tsx`
- **`JumpInText` 逐字 3D 旋入** —— 每个字独立 `rotateX` 翻转 + 上移 + 错峰弹出，用于章节标题与场景标题。`assets/lecture-template/src/index.tsx`
- **`WaveText` 字母波浪打字** —— 每字母多段关键帧波浪位移 + 起始色到终色的插值渐变，用于 CTA 拉丁字符串。`assets/lecture-template/src/index.tsx`
- **形象图形多关键帧旋入** —— 地球开场由单次弹出改为 150°→360° 多关键帧旋入，中段带一次轻微放大过冲。`assets/lecture-template/src/index.tsx`
- **拉丁点缀字体** —— 新增 `ClashDisplay-Medium/Semibold/Bold.woff2` 与 `SpaceGrotesk-Latin.woff2`，供 EP 标签、代码感字符串与技术头部使用。`assets/fonts/`、`assets/lecture-template/public/fonts/`

### 变更
- **中文字体统一为 LXGW WenKai Lite** —— 字体栈由「思源黑体 Regular/Bold + Smiley Sans 展示体」改为 `Kai`（`LXGWWenKaiLite-Regular/Medium`），拉丁点缀改用 `Clash` / `Space`；`AssetGate` 改为等待 Kai / Clash / Space 字重就绪，字幕测量门与 `SKILL.md`、`references/visual-system.md`、`references/canvas-modes.md`、`references/lecture-composition.md`、`references/locked-style-contract.json` 同步。`assets/lecture-template/src/index.tsx`、`references/`、`SKILL.md`
- **字幕改为底部纯文字逐词浮现** —— 去掉撕纸字幕条（`clipPath` 锯齿多边形、纸底与双层棕影），改为按画幅字幕边距定位的居中纯文字；逐字 `opacity` + 6px 上移浮现，词间仅在 CJK↔拉丁边界补空格，前置量由 60ms 改为 180ms（`FPS*.18`）。`assets/lecture-template/src/index.tsx`
- **配色与质感柔和化** —— 调色板整体提亮（`paperBase` `#f3e4c4`→`#f5efe3`、`paper` `#fffdf7`→`#fffef9`、`muted` `#746956`→`#8a7a63`、`line` `#514a40`→`#554e42`），纸张阴影改为多层柔和扩散；`AESTHETIC` 描边 1.6→1.1、圆角 12→14、纹理 .026→.018、网格 .09→.05、暖调 .055→.028、暗角 .06→.045。`assets/lecture-template/src/index.tsx`
- **时间轴重排到 1126 帧** —— 整片时长由 900 帧改为 1126 帧，章节卡分界与场景挂载区间改为 0/213/416/682，动作音效帧与逐词字幕 cue 表按新时间轴整体重排（16 条语义 cue，末条 `speech_end` 37550ms）。需注意的是：本版**未改动** `assets/lecture-template/audio/narration.mp3.json`，其 154 条词级时间戳仍止于 30000ms，与新时间轴不一致的部分在后续版本才补齐。`assets/lecture-template/src/index.tsx`、`assets/lecture-template/src/caption-cues.json`、`assets/lecture-template/manifests/caption-cues.json`
- **字体替换同步到 CLI 与校验** —— `new-project` 拷贝的字体清单改为 `LXGWWenKaiLite-Regular/Medium.ttf` 与 `LICENSE-OFL-1.1-LXGW.txt`；示例工程校验改为检查新字体三件与 `document.fonts.load('400 40px Kai')`。`scripts/notebook-video.mjs`、`scripts/validate-official-example.py`
- **依赖清单与仓库元数据更新** —— `DEPENDENCIES.md` 的字体行改为 LXGW WenKai Lite（Regular/Medium）与 Clash Display / Space Grotesk；发布元数据标签推进到 v1.9.0；`.gitignore` 放行 `assets/demo/*.mp4` 并忽略 `narration.mp3`。`DEPENDENCIES.md`、`.github/repository-metadata.yml`、`.gitignore`
- **双语 README 补完** —— 两份 README 按画幅矩阵、流水线与 FAQ 重写。`README.md`、`README.en.md`
- **演示资产仅重渲 16:9** —— `assets/demo/notebook-video-demo.mp4` 与 `.webp` 换为新版渲染，4:3 与 3:4 的预览产物本版未改动。`assets/demo/`

### 移除
- **旧字体与旧许可证** —— 删除 `SmileySans-Oblique.otf`、`SourceHanSansCN-Regular.otf`、`SourceHanSansCN-Bold.otf` 与思源黑体许可证文件；原展示体许可证文件改名为 `LICENSE-OFL-1.1-LXGW.txt` 并改写为 LXGW 的 OFL-1.1 声明。`assets/fonts/`

**English**

### Background
This release locks in a premium motion baseline for the template: the commit message describes upgrading the lecture template to a cinematic-quality baseline and lists dual-canvas camera work, per-glyph motion, a subtitle redesign, typeface unification and a re-timed timeline. The inferred drivers are that after v1.7.0 introduced three canvases the template needed a canvas-independent camera language and a unified font stack, and that the legacy display/CJK typeface assets and licences were treated as items to be replaced. Per-item rationale beyond that was not preserved in the record.

### Added
- **`CameraRig` dual-canvas camera layer** — a global camera component simulates a camera with `translate + scale`; 16:9 and 3:4 each get a keyframe table (`CAM_KEYS_L` / `CAM_KEYS_P`) with bezier easing between segments and exponentially-weighted sampling of the target track for lag follow-focus. Scale stays >=1 so the canvas never shows outside the stage, the rig wraps the scenes rather than living inside them, and scene cross-fades happen inside continuous camera motion. `assets/lecture-template/src/index.tsx`
- **`JumpInText` per-glyph 3D flip-in** — each glyph flips independently with `rotateX`, rises, and pops in on a stagger; used for chapter and scene titles. `assets/lecture-template/src/index.tsx`
- **`WaveText` letter-wave typing** — per-letter multi-keyframe wave displacement interpolated from a start colour to an end colour; used for the CTA latin string. `assets/lecture-template/src/index.tsx`
- **Multi-keyframe figure roll-in** — the globe intro changes from a single pop to a 150°→360° multi-keyframe roll with a mid-scale bulge. `assets/lecture-template/src/index.tsx`
- **Latin accent typefaces** — adds `ClashDisplay-Medium/Semibold/Bold.woff2` and `SpaceGrotesk-Latin.woff2` for EP tags, code-ish strings and the technical header. `assets/fonts/`, `assets/lecture-template/public/fonts/`

### Changed
- **CJK typeface unified to LXGW WenKai Lite** — the font stack moves from "Source Han Sans Regular/Bold plus Smiley Sans display" to `Kai` (`LXGWWenKaiLite-Regular/Medium`), with `Clash` / `Space` as Latin accents; `AssetGate` now waits for the Kai / Clash / Space weights, and the caption measurement gate plus `SKILL.md`, `references/visual-system.md`, `references/canvas-modes.md`, `references/lecture-composition.md` and `references/locked-style-contract.json` follow. `assets/lecture-template/src/index.tsx`, `references/`, `SKILL.md`
- **Subtitle becomes bottom-pinned pure text with per-word reveal** — the torn-paper subtitle bar (jagged `clipPath` polygon, paper fill, two-layer brown shadow) is removed in favour of centred pure text positioned by the canvas subtitle margin; characters fade in with a 6px rise, a space is inserted only at CJK↔Latin boundaries, and the lead moves from 60ms to 180ms (`FPS*.18`). `assets/lecture-template/src/index.tsx`
- **Palette and texture softened** — the palette is lightened throughout (`paperBase` `#f3e4c4`→`#f5efe3`, `paper` `#fffdf7`→`#fffef9`, `muted` `#746956`→`#8a7a63`, `line` `#514a40`→`#554e42`) and the paper shadow becomes a multi-layer soft diffusion; `AESTHETIC` moves outline 1.6→1.1, radius 12→14, texture .026→.018, grid .09→.05, warmth .055→.028 and vignette .06→.045. `assets/lecture-template/src/index.tsx`
- **Timeline re-issued at 1126 frames** — total duration moves from 900 to 1126 frames, chapter card boundaries and scene mount windows become 0/213/416/682, and the action-audio frames and the word-by-word caption cue tables are re-issued against the new timeline (16 semantic cues, the last `speech_end` at 37550ms). Note that `assets/lecture-template/audio/narration.mp3.json` is **not** modified in this version: its 154 word-level timestamps still end at 30000ms, and the part that disagrees with the new timeline is only brought in line in a later release. `assets/lecture-template/src/index.tsx`, `assets/lecture-template/src/caption-cues.json`, `assets/lecture-template/manifests/caption-cues.json`
- **Typeface swap propagated to the CLI and validators** — `new-project` now copies `LXGWWenKaiLite-Regular/Medium.ttf` and `LICENSE-OFL-1.1-LXGW.txt`; the official-example validator checks the three new font files and `document.fonts.load('400 40px Kai')`. `scripts/notebook-video.mjs`, `scripts/validate-official-example.py`
- **Dependency manifest and repository metadata updated** — the font rows in `DEPENDENCIES.md` become LXGW WenKai Lite (Regular/Medium) and Clash Display / Space Grotesk, the release metadata tag advances to v1.9.0, and `.gitignore` allows `assets/demo/*.mp4` while ignoring `narration.mp3`. `DEPENDENCIES.md`, `.github/repository-metadata.yml`, `.gitignore`
- **Bilingual READMEs completed** — both READMEs are rewritten around a canvas matrix, the pipeline and an FAQ. `README.md`, `README.en.md`
- **Demo assets re-rendered for 16:9 only** — `assets/demo/notebook-video-demo.mp4` and `.webp` are replaced with new renders; the 4:3 and 3:4 preview artifacts are untouched in this version. `assets/demo/`

### Removed
- **Legacy typefaces and licence** — `SmileySans-Oblique.otf`, `SourceHanSansCN-Regular.otf`, `SourceHanSansCN-Bold.otf` and the Source Han Sans licence file are deleted; the former display-typeface licence file is renamed to `LICENSE-OFL-1.1-LXGW.txt` and rewritten as the LXGW OFL-1.1 notice. `assets/fonts/`

---

## [1.8.0] - 2026-09-02

### 背景与动机
本版放宽依赖与运行时版本兼容区间。提交信息写明动机：「拓宽 React 18/19 与 Remotion ^4.0 的依赖兼容性，并更新 CI 一致性检查」。据改动推断的问题是：两个工程原先把依赖钉死在确切的 `4.0.489` / `19.2.7` 且要求 Node `>=20`，在 React 18 环境或希望自动获得 Remotion 小版本升级的环境里会形成同侪依赖锁死；配套校验脚本又用精确字符串比对，任何合法的版本区间写法都会被判失败。

### 变更
- **依赖与引擎区间放宽** —— 两个工程的 `package.json` 把 `remotion` / `@remotion/cli` / `@remotion/media` 由 `4.0.489` 改为 `^4.0.0`，`react` / `react-dom` 由 `19.2.7` 改为 `^18.2.0 || ^19.0.0`，`engines.node` 由 `>=20` 放宽为 `>=18`；锁定样式契约里的渲染器串同步为 `Remotion ^4.0.0`。`assets/lecture-template/package.json`、`assets/example-project/package.json`、`references/locked-style-contract.json`
- **校验改为按语义化版本区间判定** —— `validate-official-example.py` 不再比对确切的 `4.0.489` / `19.2.7`：Remotion 依赖改为判定是否落在 `^4.` / `4.` 区间，React 依赖改为判定是否包含 18 或 19，渲染器串改为判定是否以 `Remotion` 开头。`scripts/validate-official-example.py`
- **CI 更新** —— 工作流把 `actions/checkout` 由 v7.0.0 升到 v7.0.1。`.github/workflows/validate.yml`
- **自测输出改为单行结论** —— `selftest.py` 的明细由打印截断输出改为 `blocked as expected` / `unexpectedly allowed` 与 `passed` / `failed`，全绿时打印 `SELFTEST PASS (all 6 checks passed)`。`scripts/selftest.py`
- **脚本补 shebang 与说明** —— `speed-post.py`、`tts-openai-compatible.py` 补 `#!/usr/bin/env python3`；`validate-official-example.py`、`validate-skill-consistency.py` 补模块说明字符串。`assets/lecture-template/scripts/`、`scripts/`
- **一致性检查不再把 `__pycache__` 当作泄漏目录** —— 生成目录清单去掉 `__pycache__`。`scripts/validate-skill-consistency.py`

### 安全
- **高危依赖公告处理** —— `browserslist` 由 `4.28.6` 升到 `4.28.8`，处理 high 级公告 GHSA-c83g-rgw3-j3cx。`assets/example-project/package-lock.json`

**English**

### Background
This release widens the dependency and runtime compatibility window. The commit message states the motivation: "widen dependency compatibility for React 18/19 and Remotion ^4.0, update CI consistency checks". The inferred problem is that both projects pinned their dependencies to exact versions (`4.0.489` / `19.2.7`) and required Node `>=20`, which causes peer-dependency lockups on React 18 or in environments that want automatic Remotion minor upgrades; the accompanying validators compared exact strings, so any legitimate version range would have been reported as a failure.

### Changed
- **Dependency and engine ranges widened** — both projects' `package.json` move `remotion` / `@remotion/cli` / `@remotion/media` from `4.0.489` to `^4.0.0` and `react` / `react-dom` from `19.2.7` to `^18.2.0 || ^19.0.0`, and relax `engines.node` from `>=20` to `>=18`; the renderer string in the locked style contract becomes `Remotion ^4.0.0`. `assets/lecture-template/package.json`, `assets/example-project/package.json`, `references/locked-style-contract.json`
- **Validators now judge semantic version ranges** — `validate-official-example.py` no longer compares against exact `4.0.489` / `19.2.7`: Remotion dependencies must fall in a `^4.` / `4.` range, React dependencies must contain 18 or 19, and the renderer string must start with `Remotion`. `scripts/validate-official-example.py`
- **CI updated** — the workflow bumps `actions/checkout` from v7.0.0 to v7.0.1. `.github/workflows/validate.yml`
- **Self-test output reduced to one-line verdicts** — `selftest.py` reports `blocked as expected` / `unexpectedly allowed` and `passed` / `failed` instead of truncated process output, and prints `SELFTEST PASS (all 6 checks passed)` when everything is green. `scripts/selftest.py`
- **Shebangs and module docstrings added** — `speed-post.py` and `tts-openai-compatible.py` gain `#!/usr/bin/env python3`; `validate-official-example.py` and `validate-skill-consistency.py` gain module docstrings. `assets/lecture-template/scripts/`, `scripts/`
- **Consistency check no longer treats `__pycache__` as a leaked directory** — `__pycache__` is dropped from the generated-directory list. `scripts/validate-skill-consistency.py`

### Security
- **High-severity advisory resolved** — `browserslist` moves from `4.28.6` to `4.28.8`, resolving high-severity advisory GHSA-c83g-rgw3-j3cx. `assets/example-project/package-lock.json`

---

## [1.7.1] - 2026-09-01

### 背景与动机
本版是文档与回归自测的补丁。提交信息即为动机记录：「修正 `SKILL.md` 悬空引用措辞（LK002）、新增回归自测 `selftest.py`（DY001）、并把自测登记进 `SKILL.md`」。据此推断的目的是：让文档里被引用的路径与仓库中真实存在的文件一致，并给引擎、模板、QA 脚本与参考文档的后续改动提供一个可一键复跑的回归入口。

### 新增
- **回归自测入口** —— 新增 `scripts/selftest.py`。好夹具检查关键产物是否齐全并跑官方 `validate-skill`；负向夹具要求三条门禁真的拦截：受保护短语被 cue 边界切开（`validate-semantic-breaks`）、cue 文本与词级时间戳对不上（`validate-caption-sync`）、非媒体输入（`validate-video`）。全部通过退出 0，任一失败退出 1。`scripts/selftest.py`
- **自测登记进技能文档** —— `SKILL.md` 新增「Regression self-test」小节，要求改动引擎、模板、QA 脚本或参考文档后运行 `python "<SKILL_DIR>/scripts/selftest.py"`。`SKILL.md`

### 修复
- **`SKILL.md` 引用路径悬空** —— 四处引用改为仓库中的实际路径：`manifests/visual-assets.json` → `assets/lecture-template/manifests/visual-assets.json`（两处，均在「视觉资产」与「预加载资产」章节）、`manifests/protected-caption-phrases.txt` → `assets/lecture-template/manifests/protected-caption-phrases.txt`、`scripts/tts-openai-compatible.py` → `assets/lecture-template/scripts/tts-openai-compatible.py`；同段把 `chapters.json` 的落点由 `manifests/chapters.json` 澄清为「写入工程自身的 `manifests/` 目录」。`SKILL.md`

**English**

### Background
This is a documentation-and-regression patch. The commit message is the motivation record: "fix SKILL.md dangling reference wording (LK002), add regression selftest.py (DY001), register selftest in SKILL.md". The inferred purpose is twofold: make the document's referenced paths match files that actually exist in the repository, and give later changes to the engine, template, QA scripts and reference docs a single re-runnable regression entry point.

### Added
- **Regression self-test entry point** — adds `scripts/selftest.py`. Good fixtures check that the key artifacts exist and run the official `validate-skill`; negative fixtures require three gates to actually block: a protected phrase split across a cue boundary (`validate-semantic-breaks`), cue text that disagrees with its word-level timestamps (`validate-caption-sync`), and a non-media input (`validate-video`). It exits 0 when everything passes and 1 if any check fails. `scripts/selftest.py`
- **Self-test registered in the skill document** — `SKILL.md` gains a "Regression self-test" section requiring `python "<SKILL_DIR>/scripts/selftest.py"` after any change to the engine, template, QA scripts or reference docs. `SKILL.md`

### Fixed
- **Dangling references in `SKILL.md`** — four references are corrected to paths that exist in the repository: `manifests/visual-assets.json` → `assets/lecture-template/manifests/visual-assets.json` (two occurrences, in the visual-asset and preload-assets sections), `manifests/protected-caption-phrases.txt` → `assets/lecture-template/manifests/protected-caption-phrases.txt`, and `scripts/tts-openai-compatible.py` → `assets/lecture-template/scripts/tts-openai-compatible.py`; the same passage restates where `chapters.json` lands, from `manifests/chapters.json` to "the project's own `manifests/` folder". `SKILL.md`

---

## [1.7.0] - 2026-09-01

### 背景与动机
本版把讲稿模板从「单画幅 + 画布内嵌套纸框」改为「一份模板三种画幅 + 整幅纸张表面」，并按新模板重出全部演示资产。改动本身即留存的动机依据：`references/visual-system.md` 写明整幅纸张的取舍是「纸即画框，因此小屏上不会再出现嵌套框环」，`references/canvas-modes.md` 写明模板「自 v1.7.0 起把三种版式放在 `CANVAS` 常量之后」。更细的逐条动机未在记录中留存，据改动推断。

### 新增
- **一份模板、三种画幅（`CANVAS` 开关）** —— 模板新增 `CANVAS='16:9' | '4:3' | '3:4'` 与每画幅锁定参数表（合成尺寸、设计坐标、字幕左右边距/底距/高度、安全宽度、字幕字号）；4:3 在缩放包装层内复用横向场景集，3:4 走单列 `*P` 场景集，合成尺寸随画幅生效。`assets/lecture-template/src/index.tsx`
- **4:3 与 3:4 画幅样片** —— 新增 `notebook-video-demo-43.mp4/.webp`（4:3）与 `notebook-video-demo-34.mp4/.webp`（3:4 竖屏），16:9 样片同步重渲；README 加入三画幅演示画廊。`assets/demo/`
- **英文档** —— 新增 `README.en.md`；`README.md` 重写为双语文档（触发方式、前置条件、交付物、技能路径、演示区）。`README.md`、`README.en.md`

### 变更
- **背景改为整幅纸张表面** —— `Background` 去掉纸张外的暖色径向桌面色带、1.7px 页面描边与偏移页面投影，改为整幅 `C.paperBase` 平铺；54px 网格与静态点纹理仍限制在内框 `(72,58)–(1848,1020)` 之内。锁定样式契约同步：`outer_gradient` / `page_outline` / `page_shadow` 置 `null`，`page_bounds` 改为整张画布 `[0,0,1920,1080]`。`assets/lecture-template/src/index.tsx`、`references/locked-style-contract.json`、`references/visual-system.md`
- **卡片文字与步骤列表对齐** —— 节点卡标签由卡片下缘外（`top: n.y+6`）移入卡片留白内（`top: n.y-4`）；贡献场景步骤列表压缩为 `height` 56→48、`marginBottom` 12→8、容器 `top/bottom` 120/96→116/104。本版记录的目的是让底部 `github-oss-contribute` 胶囊不再压住第 4 条。`assets/lecture-template/src/index.tsx`
- **章节与场景时间轴改为 0/216/396/600** —— 章节卡分界与各场景本地帧基准由 205/377/571 改为 216/396/600，章节卡左右区块几何随画幅切换；词级时间数据与字幕 cue 表整表重排。`assets/lecture-template/src/index.tsx`、`assets/lecture-template/audio/narration.mp3.json`、`assets/lecture-template/manifests/caption-cues.json`
- **`Module` 支持自定义纵向起点** —— 新增可选 `top` 参数（默认 250），供竖屏场景把模块卡摆到不同高度。`assets/lecture-template/src/index.tsx`
- **画布说明文档更新** —— `references/canvas-modes.md` 补入 `CANVAS` 开关与 `*P` 场景集说明，并声明下方坐标表仍对自定义版式有效。`references/canvas-modes.md`

### 修复
- **TTS 适配器空 `voice` 字段被拒** —— 合成参数由「始终下发 `"voice": ""`」改为仅在 `voice` 非空时写入 `audio.voice`。本版记录的现象是：空字符串会被 MiMo voicedesign 类模型以 HTTP 400 拒绝。`assets/lecture-template/scripts/tts-openai-compatible.py`

### 移除
- **中文单语 README** —— 删除 `README.zh-CN.md`，由双语 `README.md` 取代。`README.zh-CN.md`

**English**

### Background
This release moves the lecture template from "one canvas with a nested paper frame inside it" to "one template, three canvases, with the paper filling the whole frame", and re-issues every demo asset from the updated template. The change itself carries the recorded rationale: `references/visual-system.md` states that the paper now *is* the frame, "so no nested frame rings appear on small screens", and `references/canvas-modes.md` states the template has shipped all three layouts behind the `CANVAS` constant "since v1.7.0". Per-item rationale beyond that was not preserved in the record; it is inferred from the changes.

### Added
- **One template, three canvases (the `CANVAS` switch)** — the template gains `CANVAS='16:9' | '4:3' | '3:4'` plus a locked per-canvas parameter table (composition size, design coordinates, subtitle margins / bottom / height, safe width, subtitle font size). The 4:3 mode reuses the landscape scene set inside a scaled wrapper, the 3:4 mode uses its own single-column `*P` scene set, and the composition size follows the selected canvas. `assets/lecture-template/src/index.tsx`
- **4:3 and 3:4 demo renders** — adds `notebook-video-demo-43.mp4/.webp` (4:3) and `notebook-video-demo-34.mp4/.webp` (3:4 portrait), and re-renders the 16:9 demo; the README gains a three-canvas demo gallery. `assets/demo/`
- **English README** — adds `README.en.md`; `README.md` is rewritten as the bilingual entry document (triggers, prerequisites, deliverables, skill paths, demo section). `README.md`, `README.en.md`

### Changed
- **Background becomes a full-canvas paper surface** — `Background` drops the warm radial desk band outside the page, the 1.7px page outline and the offset page shadow, and paints the whole canvas with `C.paperBase`; the 54px grid and static dot texture stay inside the inner rule `(72,58)–(1848,1020)`. The locked style contract follows: `outer_gradient` / `page_outline` / `page_shadow` become `null` and `page_bounds` becomes the full canvas `[0,0,1920,1080]`. `assets/lecture-template/src/index.tsx`, `references/locked-style-contract.json`, `references/visual-system.md`
- **Card text and step-list alignment** — node card labels move from hanging below the card edge (`top: n.y+6`) into the card whitespace (`top: n.y-4`); the contribution scene's step list is compacted (`height` 56→48, `marginBottom` 12→8, container `top/bottom` 120/96→116/104). The stated purpose in this version is that the bottom `github-oss-contribute` pill no longer overlaps the fourth step. `assets/lecture-template/src/index.tsx`
- **Chapter and scene timeline moves to 0/216/396/600** — chapter card boundaries and the per-scene local frame bases change from 205/377/571 to 216/396/600, chapter card geometry becomes canvas-aware, and the word-level timing data and caption cue table are re-issued wholesale. `assets/lecture-template/src/index.tsx`, `assets/lecture-template/audio/narration.mp3.json`, `assets/lecture-template/manifests/caption-cues.json`
- **`Module` accepts a custom vertical origin** — a new optional `top` parameter (default 250) lets portrait scenes place module cards at a different height. `assets/lecture-template/src/index.tsx`
- **Canvas documentation updated** — `references/canvas-modes.md` documents the `CANVAS` switch and the `*P` scene set, and states that the coordinate tables below remain authoritative for custom layouts. `references/canvas-modes.md`

### Fixed
- **TTS adapter rejected on an empty `voice` field** — the synthesis payload now writes `audio.voice` only when `voice` is non-empty, instead of always sending `"voice": ""`. The failure recorded in this version is that the empty string is rejected with HTTP 400 by MiMo voicedesign-type models. `assets/lecture-template/scripts/tts-openai-compatible.py`

### Removed
- **Chinese-only README** — `README.zh-CN.md` is deleted and replaced by the bilingual `README.md`. `README.zh-CN.md`

---

## [1.6.2] - 2026-07-31

### 背景与动机

多音字读错只能在源头修。动机来自提交信息 `docs: polyphone source-rewrite rule (v1.6.2) (#16)`：中文 TTS 对多音字不可靠（"重装"常被读成 zhòng），而适配器只喂纯文本、没有拼音或 SSML 通道，且旁白文本本身就是字幕源，合成之后再补音频补不回来。

### 变更

- **新增"多音字处理"规则** —— 写 `narration.txt` 时就把易读错的多音字改写成语义等价、读音无歧义的表达，并同步改写 `manifests/semantic-caption-lines.txt`；改写保持字数接近，因此章节帧几乎不动。附生产验证过的对照表：重装（电脑/系统）→ 重新装（重 zhòng vs chóng）、批量重命名 → 批量重新命名、输一行命令 → 输入一条命令（行 háng vs xíng）、钉在屏幕上 → 贴在屏幕上（钉 dìng vs dīng）、一模一样 → 长得一样（模 mú vs mó）；并要求同步更新画面上呼应这些词组的卡片文字，使字幕、旁白与图形一致。现代模型在上下文里通常读对的（调色 tiáo、时长 cháng、模型 mó）可以保留，但 QA 时抽查；若仍有读错，从 `narration.txt` 改起并重跑"合成 → speed-post → 生成字幕 → 渲染"，不做事后音频补丁。`references/tts-audio.md`
- **技能流程的 TTS 步骤同步该规则** —— `SKILL.md` 的字幕步骤加入"把易读错的多音字改写成语义等价词并镜像到语义字幕行"的说明与三个示例。`SKILL.md`

**English**

### Background

A misread polyphone can only be prevented at the source. The motivation comes from the commit message `docs: polyphone source-rewrite rule (v1.6.2) (#16)`: Chinese TTS is unreliable on polyphones (重装 is often voiced zhòng), the adapter feeds plain text with no pinyin or SSML channel, and the narration text is itself the subtitle source, so a wrong reading cannot be patched after synthesis.

### Changed

- **New "polyphone handling" rule** — while writing `narration.txt`, rewrite easily-misread polyphones into reading-unambiguous, meaning-equivalent phrasing and mirror the edit into `manifests/semantic-caption-lines.txt`; keeping replacements close in character count means chapter frames barely shift. The document ships production-verified rewrites — 重装（电脑/系统）→ 重新装 (重 zhòng vs chóng), 批量重命名 → 批量重新命名, 输一行命令 → 输入一条命令 (行 háng vs xíng), 钉在屏幕上 → 贴在屏幕上 (钉 dìng vs dīng), 一模一样 → 长得一样 (模 mú vs mó) — and requires updating matching on-screen card text so captions, narration and graphics stay consistent. Polyphones a modern model usually reads correctly in context (调色 tiáo, 时长 cháng, 模型 mó) may stay but should be spot-checked at QA; when a mispronunciation still slips through, edit `narration.txt` at the source and re-run synthesis → speed-post → captions → render rather than attempting a post-hoc audio patch. `references/tts-audio.md`
- **The skill's TTS step carries the same rule** — `SKILL.md` states that easily-misread polyphones are rewritten into unambiguous synonyms and mirrored into the semantic caption lines, with three examples. `SKILL.md`

---

## [1.6.1] - 2026-07-30

### 背景与动机

修正"插画优先"被过度执行的风险。动机来自提交信息 `docs: text/graphic co-star balance + guardrails (v1.6.1) (#15)`：插画优先讲的是**角色分工**（画面内文字只做短标签、完整旁白在字幕条），不等于"什么都得画"；同批文档另记两条实测踩到的排版护栏。

### 变更

- **新增"选择载体"一节（文字与图形仍是共同主角）** —— 按节拍性质选载体：定义、原理、规则、列表、来源、对比、警示与冲击数字走**文字优先**（带标题的 Paper 面板、逐条点亮的清单、好坏对比卡、大号跳数），场景、流程、物件、转变与关系走**图形优先**（插画为英雄、文字为短标签）；无论哪种，单个节拍必须"只看文字能懂、只看动画也能懂"（三步"该怎么做"是清单而不是三张画；一通诈骗电话是场景而不是一串要点）。`references/portrait-illustration-system.md`
- **两条新护栏** —— 内联图标必须小于它的容器（例如 48px 圆片里放 34px 图形），否则图形会溢出圆角、看起来像坏了；堆叠的面板与文字行之间要留 ≥50px 纵向间隙，否则在手机上像重叠 bug。`references/portrait-illustration-system.md`

**English**

### Background

A correction against over-applying "illustration-first". The motivation comes from the commit message `docs: text/graphic co-star balance + guardrails (v1.6.1) (#15)`: illustration-first is about **role** (in-scene text is a short label, full narration lives in the subtitle strip), not a mandate to draw everything; two layout guardrails hit in practice are added alongside it.

### Changed

- **New "choosing the vehicle" section (text and graphics stay co-stars)** — pick the vehicle by what the beat is: definitions, principles, rules, lists, sources, comparisons, warnings and shock numbers go **text-forward** (a titled Paper panel, a ticking checklist, good/bad comparison cards, a big pull-number), while scenes, processes, objects, transformations and relationships go **graphic-forward** (illustration as hero, text as a short label); either way the beat must stand alone, legible from the text alone or from the animation alone (a three-step "what to do" list is a checklist, not three drawings; a scam phone call is a scene, not a bullet list). `references/portrait-illustration-system.md`
- **Two new guardrails** — an inline icon must render smaller than its container (for example a 34px glyph in a 48px chip), or it spills over the rounded corners and reads as broken; stacked panels and lines need ≥50px vertical gaps, or they look like an overlap bug on a phone. `references/portrait-illustration-system.md`

---

## [1.6.0] - 2026-07-30

### 背景与动机

竖版有了画布参数还不够 —— 需要一套"怎么把 1080×1440 填满、既不空也不通篇是字"的画面语法。动机来自提交信息 `feat: portrait illustration-first grammar reference (v1.6.0) (#14)`：把一支已产出的竖版试验片验证过的做法写成可照做的参考文档。

### 新增

- **`references/portrait-illustration-system.md`（插画优先的竖版语法）** —— 一句话规则：竖版里插画是主角、画面内文字只做短标签，完整旁白已经在底部字幕条，因此画面内不再复述整句。文档包含：文字与图形分工（禁止把一短行文字塞在满宽 Paper 条左侧这种横版习惯）、可复用的纯 SVG 角色/物件组件库（暖色系、`viewBox` + `size` 缩放、待机微动如 `sin(f*0.08)` 摆动 / `(f%56)<3` 眨眼 / 脉冲，站立角色配地面投影，同系列复用同一套角色群作为频道视觉 IP）、常驻极淡 **Ambient** 散布层（约 5–12% 透明度、缓慢闪烁、只落在边角、`zIndex ~55`，用来消除大片空米色负空间）、文字强调工具包（荧光笔底色、手绘波浪下划线、对比标签对、冲击数字快速跳数且不许停在 `0`）、三带场景结构（标题带 y≈200–320 / 主图带 y≈330–840 / 收束带 y≈850–1180）与已验证的流程、清单、结尾三种节拍。`references/portrait-illustration-system.md`
- **三条硬教训写入文档** —— 只在 1080×1440 设计空间里写坐标（x 超过 1080 会被裁，满宽卡 ≤980、中轴 x=540）；章节条的 `stage` 边界必须等于场景切帧（`FinalDemo` 的 switch 同帧），否则会出现错误的章节标题压在新场景上；接触表上不许出现整帧几乎全是背景的瞬间或停在 `0` 的计数。`references/portrait-illustration-system.md`

### 变更

- **竖版开场指向该文档** —— `SKILL.md` 的画布开场说明在 3:4 时同时要求阅读 `canvas-modes.md` 与 `portrait-illustration-system.md`，并概括其要点（插画为英雄、文字为标签、Ambient 层与代码绘制角色群）。`SKILL.md`

**English**

### Background

Canvas parameters alone are not enough for portrait — what is needed is a visual grammar for filling 1080×1440 so the frame reads neither empty nor entirely textual. The motivation comes from the commit message `feat: portrait illustration-first grammar reference (v1.6.0) (#14)`: the lessons verified on a produced portrait pilot are written down as a followable reference.

### Added

- **`references/portrait-illustration-system.md` (illustration-first portrait grammar)** — the one-line rule: on portrait the illustration is the hero and in-scene text is a short label, because the full narration already lives in the bottom subtitle strip, so sentences are never restated inside the frame. The document covers the text-vs-graphic role split (banning the landscape habit of a short line crammed at the left of a full-width Paper bar), a reusable pure-SVG figure and object library (warm palette, `viewBox` plus a `size` prop, idle micro-motion such as `sin(f*0.08)` bob / `(f%56)<3` blink / pulse, ground shadows under standing figures, and the same cast reused across a series as the channel's visual IP), a persistent faint **Ambient** scatter layer (roughly 5–12% opacity, slow twinkle, corners and margins only, `zIndex ~55`, removing large empty beige negative space), a text-emphasis kit (highlighter marker, hand-drawn wavy underline, contrast label pair, fast shock-number count-up that never dwells on `0`), the three-band scene structure (heading y≈200–320 / hero y≈330–840 / payoff y≈850–1180) and proven process, checklist and end beats. `references/portrait-illustration-system.md`
- **Three hard-won guardrails recorded in the document** — author strictly in the 1080×1440 design space (x beyond 1080 is clipped; full cards ≤980 wide, centre axis x=540); chapter-chrome `stage` boundaries must equal the scene-cut frames (including the `FinalDemo` switch), or the wrong chapter title shows over a scene; the contact sheet must contain no transient mostly-background frame and no counter dwelling on `0`. `references/portrait-illustration-system.md`

### Changed

- **Portrait kickoff points at the new document** — the canvas kickoff in `SKILL.md` requires reading both `canvas-modes.md` and `portrait-illustration-system.md` on 3:4, summarising its key points (illustration as hero, text as label, the ambient layer and the code-drawn figure cast). `SKILL.md`

---

## [1.5.0] - 2026-07-27

### 背景与动机

增加第三种锁定画布（3:4 竖版）并明确否掉 9:16。动机来自提交信息 `feat: add 3:4 portrait canvas mode (v1.5.0) (#13)`：竖屏信息流需要原生长宽比；同批文档记录 9:16 会在平台 UI 下留一条死的下边带，因此被否掉。

### 新增

- **第三种锁定画布：3:4 竖版** —— 交付 1440×1920、设计空间 1080×1440；画布表新增一列，并附竖版改写流程：所有 3:4 参数一起改（`Composition` 1440×1920、包裹层 1080×1440、字幕条左右 50 / bottom 40 / 高 104、`TYPE.subtitle` 40、`subtitleSafeWidth` 900）；章节条移到 y≈80、内容区 y≈200–1290；双栏场景改为单栏堆叠（满宽卡约 980，各自保留底部锚定结论条），时间轴 SVG 可拉到约 900 宽；字幕按 900px 门在 40px 下断句（竖版一行约 13 个汉字）。同节写明不用 9:16 的原因（平台 UI 下方死带、观感过长）。`references/canvas-modes.md`
- **契约与校验支持三模式** —— `locked-style-contract.json` 新增 `canvas.modes["3:4"]`（交付尺寸、设计空间、字幕边界 [50,1296,1030,1400]、安全宽 900、字幕 40px）、`subtitle_input.bounds_by_mode["3:4"]` 与 `font_px_by_mode`（16:9 44 / 4:3 44 / 3:4 40）；`validate-video` 接受 1440×1920 容器；`validate-visual-plan` 的画布门识别三种模式，并新增"设计空间高度"与"字幕条 bottom 偏移"两项交叉校验。`references/locked-style-contract.json`、`scripts/notebook-video.mjs`、`scripts/validate-visual-plan.py`

### 变更

- **开场询问改为三选一** —— 画布模式在开场问一次，三选一（16:9 默认 / 4:3 / 3:4 竖版）；渲染尺寸与字幕宽度门说明补上竖版口径（900px）。`SKILL.md`
- **分模式字幕字号合并成表** —— v1.4.0 只在横版语境里说明的字幕字号，现在按模式统一列出（横版 44 / 竖版 40）。`references/canvas-modes.md`

**English**

### Background

A third locked canvas (3:4 portrait) is added and 9:16 is explicitly rejected. The motivation comes from the commit message `feat: add 3:4 portrait canvas mode (v1.5.0) (#13)`: portrait feeds need a native aspect ratio, and 9:16 was measured to leave a dead lower band under platform UI.

### Added

- **Third locked canvas: 3:4 portrait** — 1440×1920 delivery with a 1080×1440 design space; the canvas table gains a column plus a portrait authoring procedure: set every 3:4 value together (`Composition` 1440×1920, wrapper 1080×1440, subtitle strip margins 50, bottom 40, height 104, `TYPE.subtitle` 40, `subtitleSafeWidth` 900); chrome moves to y≈80 and the content region runs y≈200–1290; two-column scenes become single-column stacked zones (full-width cards around 980 wide, each keeping its bottom-anchored conclusion strip) and timeline SVGs stretch to about 900 wide; captions break at the 900px gate and 40px (about 13 CJK characters per portrait line). The same section records why 9:16 is not used (a dead band under platform UI and a stretched feel). `references/canvas-modes.md`
- **Contract and validation support three modes** — `locked-style-contract.json` gains `canvas.modes["3:4"]` (delivery size, design space, subtitle bounds [50,1296,1030,1400], safe width 900, 40px subtitle), `subtitle_input.bounds_by_mode["3:4"]` and `font_px_by_mode` (16:9 44 / 4:3 44 / 3:4 40); `validate-video` accepts the 1440×1920 container; the `validate-visual-plan` canvas gate knows all three modes and additionally cross-checks the design-space height and the subtitle strip bottom offset. `references/locked-style-contract.json`, `scripts/notebook-video.mjs`, `scripts/validate-visual-plan.py`

### Changed

- **Kickoff question becomes a three-way choice** — the canvas mode is asked once (16:9 default / 4:3 / 3:4 portrait), and the render-size and caption-width guidance gains the portrait value (900px). `SKILL.md`
- **Per-mode subtitle sizes consolidated into the table** — the subtitle size that v1.4.0 stated only in landscape terms is now listed per mode (44 landscape / 40 portrait). `references/canvas-modes.md`

---

## [1.4.0] - 2026-07-27

### 背景与动机

把三件原本靠提示词和手感的事改成确定性输出：交付语速、字幕条观感、结尾行动号召。动机来自提交信息 `feat: standard pace, Smiley subtitle and save-hook ending (v1.4.0) (#12)`。

### 新增

- **标准交付语速（后期固定）** —— 模板新增 `scripts/speed-post.py`：对合成结果应用 `atempo=1.10`（不变调）并重新归一化响度，同时把 `narration.mp3.json` 与 `manifests/chapters.json` 内所有时间戳按同一系数缩放，使字幕、场景边界与音效表继续自洽。该版本文档记录的依据：原始讲解语气实测约 305 字/分、短平台观感偏慢，而提示词无法稳定命中目标（任何"更快"指令都会冲过 400），因此在后期固定为 336 字/分；用法为合成后、生成字幕前跑一次。`assets/lecture-template/scripts/speed-post.py`、`references/tts-audio.md`
- **结尾"收藏钩子"契约** —— 知识类结尾卡从"求关注"改为"请收藏并给出具体未来场景"（如"点个收藏，下次写崩了翻出来照着敲"），配一段代码绘制的星星（说到那个字时描边并填充）；系列片在收藏卡下方加一行下一集预告；平台引用只用合规措辞、不带账号与链接。`references/pacing-rhythm.md`
- **满画面纵向预算** —— 有字幕条上方留 40px 余量的前提下，卡片上沿约 y=190、下沿到约 y=876（1080 设计空间），双栏讲解场景卡高约 686；下方空出四分之一是排版缺陷而非留白，并且卡片内应使用底部锚定的结论条来吃掉这段高度。`references/canvas-modes.md`
- **三条新的渲染前自检** —— 正文只用纯墨色（弱化色保留给装饰性抬头与被划掉的对比词）；内容卡要吃到字幕条上方约 40px；SVG 元素之间保持至少 24px 净空，且不得让文字标签压在图形上。`references/lecture-composition.md`

### 变更

- **字幕条改用 Smiley Sans 并去掉无意义装饰** —— 字幕字号 40 → 44px、字距 1.2px，字体族改为 `Smiley`（回退 Source Han）；宽度门同步按 44px / Smiley 测量；移除右侧蓝色圆环（保留橙色定位条）。模板、宽度门与锁定契约三处同改（`font_px: 44`、新增 `font_family` / `letter_spacing_px` / `right_decoration`）。`assets/lecture-template/src/index.tsx`、`references/locked-style-contract.json`

**English**

### Background

Three things that used to depend on prompt wording and feel become deterministic: delivery pace, subtitle-strip look and the closing call to action. The motivation comes from the commit message `feat: standard pace, Smiley subtitle and save-hook ending (v1.4.0) (#12)`.

### Added

- **Standard delivery pace fixed in post** — the template ships `scripts/speed-post.py`, which applies `atempo=1.10` (pitch unchanged) and re-normalizes loudness while scaling every timestamp in `narration.mp3.json` and `manifests/chapters.json` by the same factor, so captions, scene boundaries and the sound table stay self-consistent. The basis: raw teaching-tone synthesis measures about 305 characters per minute, which reads slow on short-video platforms, and prompt wording cannot hit a target reliably (any "faster" instruction overshoots past 400), so 336 characters per minute is fixed in post; run it once, after synthesis and before building captions. `assets/lecture-template/scripts/speed-post.py`, `references/tts-audio.md`
- **Save-hook ending contract** — knowledge-genre closing cards ask for a save with a concrete future moment ("点个收藏，下次写崩了翻出来照着敲") paired with a code-drawn star that draws its outline and fills on the spoken word, a one-line next-episode teaser for series films, and compliant platform wording without account names or links. `references/pacing-rhythm.md`
- **Full-canvas vertical budget** — with 40px kept above the subtitle strip, card tops start near y=190 and bottoms reach about y=876 in the 1080 design space, giving two-column explainer cards a height near 686; an empty lower quarter is a layout defect rather than negative space, and bottom-anchored conclusion strips inside each card are the standard way to consume that height. `references/canvas-modes.md`
- **Three new pre-render self-check items** — body copy is pure ink (muted reserved for decorative kickers and struck-through contrast words); content cards reach about 40px above the subtitle strip; SVG elements keep at least 24px clearance and no text label sits on top of a graphic. `references/lecture-composition.md`

### Changed

- **The subtitle strip switches to Smiley Sans and drops a meaningless decoration** — subtitle size goes 40 → 44px with 1.2px tracking and the family becomes `Smiley` (falling back to Source Han); the width gate measures with the same 44px Smiley setting; the right-hand blue ring is removed while the orange locator bar stays. Template, width gate and locked contract move together (`font_px: 44`, plus new `font_family`, `letter_spacing_px` and `right_decoration`). `assets/lecture-template/src/index.tsx`, `references/locked-style-contract.json`

---

## [1.3.1] - 2026-07-27

### 背景与动机

补一道画布一致性的硬校验。动机来自提交信息 `fix: validate canvas-mode consistency in visual plan (v1.3.1) (#11)`：4:3 的四个参数漏改其中一个就会静默出错 —— 真实生产里出过"4:3 片子保留 16:9 字幕边距、字幕条错位"的事故，此前校验放它过去。

### 修复

- **`validate-visual-plan` 新增画布模式交叉校验** —— 从 `src/index.tsx` 读出 `Composition` 宽度（2560 / 1920），要求与之配套的设计包裹宽度、`subtitleSafeWidth` 与字幕条左右边距全部匹配；混用（例如 4:3 工程仍用 16:9 字幕边距）现在报精确错误而不是静默通过。`scripts/validate-visual-plan.py`
- **画布参考文档标注"必须同改"并补流程步骤** —— 四个 4:3 参数被明确标为一起改，并把 `validate-visual-plan` 列为渲染前必跑的一步。`references/canvas-modes.md`

**English**

### Background

A canvas-consistency gate is added. The motivation comes from the commit message `fix: validate canvas-mode consistency in visual plan (v1.3.1) (#11)`: missing one of the four 4:3 values fails silently — a real production shipped a 4:3 film that kept the 16:9 subtitle margins and misplaced the subtitle strip, and validation let it pass.

### Fixed

- **`validate-visual-plan` cross-checks the canvas mode** — it reads the `Composition` width from `src/index.tsx` (2560 / 1920) and requires the matching design wrapper width, `subtitleSafeWidth` and subtitle strip margins; a mixed-mode file (for example a 4:3 project keeping 16:9 subtitle margins) now fails with a precise error instead of passing silently. `scripts/validate-visual-plan.py`
- **The canvas reference marks the values as change-together and adds the step** — the four 4:3 values are explicitly labelled as a set, and `validate-visual-plan` is listed as a pre-render step. `references/canvas-modes.md`

---

## [1.3.0] - 2026-07-27

### 背景与动机

画布从单模式扩为双模式，并补上两套此前"只有原则、没有判据"的约束。动机来自提交信息 `feat: dual canvas modes, pacing contract and cold-open templates (v1.3.0) (#10)`：4:3 在手机信息流里同字号可大约大三成，需要成为一种一等交付画布；同时整片节奏与开头三秒此前缺少可执行的检查口径。

### 新增

- **`references/canvas-modes.md`（16:9 与 4:3）** —— 两种交付画布的完整参数表（16:9 = 2560×1440 默认；4:3 = 1920×1440，设计空间 1440×1080；含设计坐标系、字幕条左右边距 188 / 60、`subtitleSafeWidth` 1334 / 1060、可用内容宽与双栏预算）、4:3 的机械改写流程（改窄双栏而不是减分区；宽 SVG 可用 `transform:scale(0.85)` 包裹），以及"移动端可读字号地板"（bodyL/M/S 26/24/23、labelL/M/S 22/21/20、microL/S 18/16，任何正文不得低于 16px 设计尺寸）。
- **`references/pacing-rhythm.md`（能量曲线契约）** —— 每 60–90 秒一个"锤子帧"（一章最可引用的一句做成近空画面的全屏大字，其余分区先完整退场，按 cue 表定时，并在分镜里标注 `Hammer:`）；快慢章节交替（慢章状态变化 3–4 秒一次、快章 1.5–2.5 秒一次）且不连续两章同节奏；章间 0.5–1 秒呼吸（旧场景完整退场、只剩章节条、再进新章首元素）；结尾主动降密度（最多三个元素）；并给出渲染前的节奏审查门。
- **冷开场三套首句模板 + 前三秒动作密度门** —— "结果前置 / 好奇缺口 / 冲突对比"三种写法（该版本文档引用数据点：结果前置的完播表现优于功能陈述两倍以上，78% 高完播视频把核心冲突或结果前置），禁止用人群标签或路线图开场（"作为XX专业的学生…""上一课我们学了…"）；前三秒要求至少三次不同视觉动作、全屏锤子帧在 45 帧内落定并配一次短促落点音，常规多分区版面在锤子帧可读满 1 秒后才展开。`references/narrative-hook.md`

### 变更

- **锁定风格契约写入双画布** —— 新增 `canvas.mode_selection`（开场问一次，16:9 为默认）与 `canvas.modes`（两模式的交付尺寸、设计空间、字幕边界、安全宽），`subtitle_input` 新增 `bounds_by_mode`。`references/locked-style-contract.json`
- **`validate-video` 接受两种容器** —— 2560×1440 与 1920×1440 均可通过。`scripts/notebook-video.mjs`
- **开场与流程绑定新契约** —— `SKILL.md` 增加"开场问一次画布模式"，把文案步骤绑定到冷开场与节奏契约，渲染与字幕宽度说明补上双模式口径；模板字号地板抬到 v1.3.0 口径。`SKILL.md`、`assets/lecture-template/src/index.tsx`
- **落地页仓库地图同步** —— 中英 README 的 `references/` 一行补上 `canvas-modes` 与 `pacing-rhythm`。`README.md`、`README.zh-CN.md`

**English**

### Background

The canvas grows from one mode to two, and two contracts that previously had principles but no criteria are written down. The motivation comes from the commit message `feat: dual canvas modes, pacing contract and cold-open templates (v1.3.0) (#10)`: 4:3 renders the same fonts roughly a third larger in a phone feed, so it deserves to be a first-class delivery canvas, while film-level pacing and the first three seconds lacked an executable check.

### Added

- **`references/canvas-modes.md` (16:9 and 4:3)** — the full parameter table for both delivery canvases (16:9 = 2560×1440 default; 4:3 = 1920×1440 with a 1440×1080 design space; including design coordinate space, subtitle strip margins 188 / 60, `subtitleSafeWidth` 1334 / 1060, usable content width and two-column budgets), the mechanical 4:3 conversion procedure (narrow both cards rather than dropping a zone; wide SVG diagrams may be wrapped in `transform:scale(0.85)`), and the mobile readability type floor (bodyL/M/S 26/24/23, labelL/M/S 22/21/20, microL/S 18/16, with no content text below 16px design size).
- **`references/pacing-rhythm.md` (energy-curve contract)** — a hammer frame every 60–90 seconds (a chapter's most quotable line as an oversized full-screen statement on a nearly empty paper, all other zones exited first, timed from the cue table and marked `Hammer:` in the storyboard); fast/slow chapter alternation (state changes every 3–4 seconds in slow chapters, every 1.5–2.5 seconds in fast ones) with no two adjacent chapters at the same energy; a 0.5–1 second chapter breath (outgoing scene fully exits, only chrome remains, then the next chapter's first element pops); a deliberately sparse ending (at most three elements); and a pre-render pacing review gate.
- **Three proven first-sentence templates plus a first-three-seconds density gate** — result-first, curiosity-gap and conflict/contrast openings (with the cited data point that result-first openings outperform feature statements by more than 2x on completion and that 78% of high-completion videos front-load the core conflict or result), a ban on audience labeling or roadmap openers, and a requirement of at least three distinct visual actions inside the first three seconds with the full-screen hammer frame landing within 45 frames plus one short accent sound; the regular multi-zone layout begins only after the hammer frame has been legible for a full second. `references/narrative-hook.md`

### Changed

- **The locked style contract records both canvases** — new `canvas.mode_selection` (asked once at kickoff, 16:9 default) and `canvas.modes` (per-mode delivery size, design space, subtitle bounds and safe width), plus `subtitle_input.bounds_by_mode`. `references/locked-style-contract.json`
- **`validate-video` accepts both containers** — 2560×1440 and 1920×1440 both pass. `scripts/notebook-video.mjs`
- **Kickoff and workflow bound to the new contracts** — `SKILL.md` asks the canvas mode once, binds the copywriting step to the cold-open and pacing contracts, and states both canvases in the render and caption-width guidance; the template's type floor is raised. `SKILL.md`, `assets/lecture-template/src/index.tsx`
- **Landing-page repository map updated** — both READMEs list `canvas-modes` and `pacing-rhythm` in the `references/` line. `README.md`, `README.zh-CN.md`

---

## [1.2.0] - 2026-07-26

### 背景与动机

把"讲课式多分区"定为默认视觉路线。动机来自提交信息 `feat: make lecture composition the default visual route (v1.2.0) (#9)`：默认路线改为纯代码绘制（SVG + 同步文字），任何环境、任何 Agent 都能复现同一风格，**不依赖生图能力**；生图降级为"每部片问用户一次"的可选附加项。

### 新增

- **新的默认项目模板 `assets/lecture-template/`** —— 一份已通过校验的 900 帧讲课式成片工程（+2891 行锁文件），源码分三层：LOCKED 层（美学核心、字幕、背景、章节条、资源门，不得改）、组件库层（`Paper`、`LineIcon`、`CheckBadge`、`Mascot`、`StepRail` 等）、内容层（`COPY`、场景边界、`Scene*`、音效表）；随附 30 秒示例分镜、字幕资料、4 个程序生成音效与许可文件，以及空数组的 `manifests/visual-assets.json`（默认路线零位图）。`assets/lecture-template/`
- **`references/lecture-composition.md`** —— 默认路线的六条规范（纯代码绘制、多分区布局、文字与图形同为叙事主体、按 cue 帧对齐语音、演示性动画、系列组件复用）+ 机械的 cue→帧换算流程（先跑 TTS 与 `build-semantic-captions`，打印每条 cue 的帧区间，场景边界取每章首条 cue 起始帧，元素出现帧取对应台词起始帧）+ 渲染前七问自检。`references/lecture-composition.md`
- **章节分段 TTS 适配器 `scripts/tts-openai-compatible.py`** —— 面向任何接受 `chat/completions` 且返回 base64 音频的 OpenAI 兼容端点（示例 MiMo-V2.5-TTS），只用环境变量 `TTS_API_BASE` / `TTS_API_KEY` / `TTS_MODEL`（可选 `TTS_VOICE` / `TTS_STYLE_PROMPT`）配置；逐段合成后用 ffprobe 量真实段长、固定静音间隔拼接、段内推词级时间，除标准产物外写出 `manifests/chapters.json`，并按"模型 + 音色 + 段落文本"哈希缓存段落音频（改一段只重合成一段）。`assets/lecture-template/scripts/tts-openai-compatible.py`

### 变更

- **`new-project` 默认复制讲课模板** —— 新增 `--classic` 开关才复制 `example-project`（视觉导演样例，适用于已接受生图附加项的制作）。`scripts/notebook-video.mjs`
- **技能流程与资源地图改口径** —— 默认路线写明"每个镜头都用代码画（SVG + 富同步文字）"；生图改为"每部片问一次"，并如实说明效果取决于当前工具的生图质量、Codex 内置生图最合适；`visual-assets.json` 在默认路线保持为空。`SKILL.md`
- **配音参考文档改首选形状** —— "首选零密钥适配器（Edge Read Aloud）"改为"推荐适配器：章节分段 + OpenAI 兼容"，Edge Read Aloud 降为零密钥回退。`references/tts-audio.md`
- **CI 冒烟测试覆盖两条路线** —— 默认路线断言"无 `public/illustrations/visual-director.png`、有 `manifests/visual-assets.json`、`validate-visual-plan` 通过"；再跑一次 `--classic` 并断言生图与清单存在。`.github/workflows/validate.yml`
- **演示资产与落地页同步** —— `assets/demo/` 四个文件重渲，中英 README 描述默认路线。`assets/demo/`、`README.md`、`README.zh-CN.md`

**English**

### Background

Lecture composition becomes the default visual route. The motivation comes from the commit message `feat: make lecture composition the default visual route (v1.2.0) (#9)`: the default route is drawn entirely with code (SVG plus synchronized text) so any agent in any environment can reproduce the same style **without an image-generation model**; image generation drops to an optional add-on offered to the user once per production.

### Added

- **New default template `assets/lecture-template/`** — a validated 900-frame lecture-composition film project (+2891 lines of lockfile) whose source is layered: a LOCKED layer (aesthetic core, subtitle, background, chapter chrome, resource gates — never edited), a component library (`Paper`, `LineIcon`, `CheckBadge`, `Mascot`, `StepRail` and friends) and a content layer (`COPY`, scene boundaries, `Scene*` components, sound table); shipped with a 30-second storyboard, caption material, four procedurally generated sound effects with their license, and an empty `manifests/visual-assets.json` (zero rasters on the default route). `assets/lecture-template/`
- **`references/lecture-composition.md`** — the six rules of the default route (pure code-drawn graphics, multi-zone layout, text and graphics as co-stars, frame-accurate speech sync, demonstrative animation, series component reuse), a mechanical cue-to-frame procedure (run TTS and `build-semantic-captions`, print the cue frame table, take scene boundaries from each chapter's first cue, take element appearance frames from the line that speaks about them) and a seven-question pre-render self-check. `references/lecture-composition.md`
- **Chapter-segmented TTS adapter `scripts/tts-openai-compatible.py`** — targets any OpenAI-compatible endpoint that accepts a `chat/completions` payload with an `audio` block and returns base64 audio (MiMo-V2.5-TTS is one example), configured only through `TTS_API_BASE` / `TTS_API_KEY` / `TTS_MODEL` (optional `TTS_VOICE` / `TTS_STYLE_PROMPT`); it synthesizes each paragraph separately, measures every segment's real duration with ffprobe, joins segments with a fixed silence gap and derives per-character timings inside each measured paragraph, writing `manifests/chapters.json` besides the canonical outputs, and caches segment audio by a hash of model, voice and paragraph text so editing one paragraph re-synthesizes only that paragraph. `assets/lecture-template/scripts/tts-openai-compatible.py`

### Changed

- **`new-project` copies the lecture template by default** — the new `--classic` flag copies `example-project` instead (the visual-director exemplar, for productions that accepted the image add-on). `scripts/notebook-video.mjs`
- **Workflow and resource map restated** — the default route draws every scene with code (SVG plus rich synchronized text); image generation becomes a once-per-production question with the honest note that its quality depends on the current tool and that Codex's built-in image generation is best suited; `visual-assets.json` stays empty on the default route. `SKILL.md`
- **Narration reference changes its recommended shape** — "preferred zero-key adapter (Edge Read Aloud)" becomes "recommended adapter: chapter-segmented, OpenAI-compatible", with Edge Read Aloud demoted to the zero-key fallback. `references/tts-audio.md`
- **CI smoke tests cover both routes** — the default route asserts no `public/illustrations/visual-director.png`, a present `manifests/visual-assets.json` and a passing `validate-visual-plan`; a `--classic` run then asserts the generated image and manifest exist. `.github/workflows/validate.yml`
- **Demo assets and landing pages follow** — the four `assets/demo/` files are re-rendered and both READMEs describe the default route. `assets/demo/`, `README.md`, `README.zh-CN.md`

---

## [1.1.0] - 2026-07-19

### 背景与动机

官方引擎从 v8 performance 升级到 v9 visual director。动机来自提交信息 `feat: add v9 visual director workflow (#7)`：在动手做分镜之前，先由"视觉导演"按内容含义给每个镜头定视觉模式（图文 / 纯文字 / 纯图形），并把生图作为**可选增强**接入 —— 图片只作素材层，精确文字、箭头、图表、时间与退场仍由 Remotion 控制。

### 新增

- **视觉导演参考文档 `references/visual-director.md`** —— 七节：按含义选模式（具体对象/场景/转变 → `image-text`；对比、口号、误区、关键词 → `pure-text`；流程、系统、数量、关系 → `pure-graphic`）、探测可用生图能力与回退（Codex 内置生图 → 等价 provider / 用户素材 / 授权素材 / 原生 SVG，无生成器也不阻塞生产）、面向动画的生图提示词七条要求（含禁止烘焙字幕/图表/UI 文字、指定留白区）、`public/illustrations/` 存档与 `manifests/visual-assets.json` 溯源字段、图像与信息分开动画、镜头生命周期与边界四帧复核、以及"要视频不要幻灯片"的拒收口径。`references/visual-director.md`
- **`validate-visual-plan` 校验命令** —— 校验场景模式合法性、帧区间不重叠不留缝并与 `duration_frames` 对齐、挂载契约必须为 `start-inclusive-end-exclusive`、非末镜不得 `final-hold`、栅格文件存在性与 SHA-256、`source_type` 取值（`ai-generated` / `user-supplied` / `licensed-third-party`）、AI 生成件必须带 provider 与 prompt 摘要且 `baked_text: false`、两份清单的资产 ID 必须互相一致。`scripts/validate-visual-plan.py`
- **官方图文镜头样例** —— 第二镜由纯图形改为 `image-text`：`Img` 图层（带轻微推近）+ 两个依次出现的框选 + 两个短语对齐的标签，并按提示在下一镜前完整退场；`AssetGate` 增加图像预载与 60 秒超时；生图文件随包发布并登记溯源。`assets/example-project/src/index.tsx`、`assets/example-project/manifests/visual-assets.json`、`assets/example-project/public/illustrations/visual-director.png`
- **零密钥配音适配器口径转正** —— 未选定付费 provider 时，优先使用 Microsoft Edge Read Aloud（可达且条款符合用途时），并明确不得硬编码代理。`SKILL.md`、`references/tts-audio.md`

### 变更

- **锁定风格契约升级为 `warm-ivory-remotion-2k30-v9-visual-director`** —— 新增 `visual_director`、`image_assets`、`scene_lifetime` 三节；可编辑面新增"视觉计划 / 生成或自备图片 / 图片溯源清单"；`same_four_act_grammar: true` 改为 `fixed_four_act_grammar: false` + `adaptive_scene_modes: true`；官方样例的 `asset-manifest.json` 增加 `scenes`（含 `visual_mode` 与资产映射）与 `visual_asset_ids`。`references/locked-style-contract.json`、`assets/example-project/manifests/asset-manifest.json`
- **生产流程由十步扩为十一步** —— 插入"第 2 步 导演视觉并生成配图"（在分镜前先写视觉计划：场景 ID、时间区间、讲解目的、主模式、完整退场帧）；交付清单从 7 项扩到 9 项（新增视觉计划、图片溯源清单）；拒收条件新增"未登记的栅格资产""图片里烘焙了文字""像幻灯片一样不同步的图像卡片序列"。`SKILL.md`
- **CLI 与 CI 接入新校验** —— 新增 `validate-visual-plan` 命令并在帮助文本中说明栅格资产需登记；CI 增加该步与冒烟断言（默认工程必须生成 `public/illustrations/visual-director.png` 与 `manifests/visual-assets.json`）。`scripts/notebook-video.mjs`、`.github/workflows/validate.yml`
- **样例工程与文档对齐新口径** —— 工程名、页眉与"视觉车间"镜头更新为视觉导演语义；`validate-official-example.py` 增加模式序列与资产映射断言、渲染输入哈希断言；`validate-skill-consistency.py` 把旧 v8 标识列为废弃 token 并新增必查文件；中英落地页、agent 元数据与技能描述改为"视觉导演 + 生图可插拔"。`assets/example-project/package.json`、`scripts/validate-official-example.py`、`scripts/validate-skill-consistency.py`、`README.md`、`README.zh-CN.md`、`agents/openai.yaml`
- **演示资产重渲** —— `assets/demo/` 四个文件随新引擎更新（成片、预览动图、主视觉、社交预览）。`assets/demo/`

**English**

### Background

The official engine moves from v8 performance to v9 visual director. The motivation comes from the commit message `feat: add v9 visual director workflow (#7)`: before any storyboard work, a "visual director" stage assigns one visual mode per scene from the narration's meaning (image-plus-text, pure text or pure graphic) and folds image generation in as an **optional enhancement** — the bitmap is only an asset layer, while exact text, arrows, diagrams, timing and exits stay under Remotion's control.

### Added

- **Visual-director reference `references/visual-director.md`** — seven sections: choosing the mode from meaning (concrete object/place/transformation → `image-text`; contrast, slogan, misconception, keyword → `pure-text`; process, system, quantity, relationship → `pure-graphic`), detecting an available image-generation capability with fallbacks (Codex built-in image generation → an equivalent provider / user assets / licensed assets / native SVG, never blocking production), seven prompt requirements for animation-ready art (including no baked captions, charts or UI text and an explicit quiet overlay region), storing rasters in `public/illustrations/` with provenance in `manifests/visual-assets.json`, animating image and information separately, four-frame scene-boundary review, and a rejection rule for "video, not slides". `references/visual-director.md`
- **`validate-visual-plan` command** — validates allowed scene modes, non-overlapping and gapless frame ranges that match `duration_frames`, the `start-inclusive-end-exclusive` mount contract, `final-hold` only on the last scene, raster existence and SHA-256, the `source_type` value set (`ai-generated` / `user-supplied` / `licensed-third-party`), mandatory provider and prompt summary with `baked_text: false` for AI-generated assets, and matching asset IDs between the two manifests. `scripts/validate-visual-plan.py`
- **Official image-plus-text scene example** — scene two becomes `image-text`: an `Img` layer with a restrained push-in, two sequential box callouts and two phrase-timed labels, cleared completely before the next scene; `AssetGate` gains image preloading and a 60-second timeout; the generated file ships with the repository and its provenance record. `assets/example-project/src/index.tsx`, `assets/example-project/manifests/visual-assets.json`, `assets/example-project/public/illustrations/visual-director.png`
- **Zero-key narration adapter promoted in the contract** — when no paid provider is selected, Microsoft Edge Read Aloud is preferred when it is reachable and its terms fit the intended use, with an explicit ban on hardcoding a proxy. `SKILL.md`, `references/tts-audio.md`

### Changed

- **The locked style contract becomes `warm-ivory-remotion-2k30-v9-visual-director`** — new `visual_director`, `image_assets` and `scene_lifetime` sections; the editable surface gains the visual plan, generated or supplied imagery and the provenance manifest; `same_four_act_grammar: true` becomes `fixed_four_act_grammar: false` plus `adaptive_scene_modes: true`; the official example's `asset-manifest.json` gains `scenes` (with `visual_mode` and asset mapping) and `visual_asset_ids`. `references/locked-style-contract.json`, `assets/example-project/manifests/asset-manifest.json`
- **Production workflow grows from ten steps to eleven** — "Step 2: direct the visuals and generate support art" is inserted (write a compact visual plan before implementing scenes: scene ID, time range, narration purpose, primary mode, complete-exit frame); deliverables grow from 7 to 9 items (visual plan and image provenance manifest); rejection conditions add unregistered raster assets, generated text baked into imagery, and a static image-card sequence that does not synchronize with the narration. `SKILL.md`
- **CLI and CI wired to the new validation** — a `validate-visual-plan` command is added and the help text states that raster assets must be registered; CI runs the step and a smoke assertion that a default project contains `public/illustrations/visual-director.png` and `manifests/visual-assets.json`. `scripts/notebook-video.mjs`, `.github/workflows/validate.yml`
- **Example project and documentation aligned** — the project name, header and workshop scene follow the visual-director semantics; `validate-official-example.py` gains mode-sequence and asset-mapping assertions plus render-input hash checks; `validate-skill-consistency.py` lists the old v8 identifier as an obsolete token and requires the new files; both landing pages, the agent metadata and the skill description state "visual director plus pluggable image generation". `assets/example-project/package.json`, `scripts/validate-official-example.py`, `scripts/validate-skill-consistency.py`, `README.md`, `README.zh-CN.md`, `agents/openai.yaml`
- **Demo assets re-rendered** — the four files under `assets/demo/` are updated for the new engine. `assets/demo/`

---

## [1.0.3] - 2026-07-18

### 背景与动机

署名与命名口径的纠正。动机来自提交信息 `docs: attribute ChatGPT Codex collaboration`：让 GitHub 把协作方识别为 Codex 身份，而不是无关的 `noreply` 账号，同时统一名称口径（ChatGPT 是桌面应用，Codex 是它的软件开发模式与提交身份）。

### 新增

- **贡献者说明 `CONTRIBUTORS.md`** —— 明确两个角色：`hyt315` 为创作者（产品方向、编辑要求、发版负责），`ChatGPT (Codex)` 为架构、实现、校验、文档与开源发布工程；并写明命名口径（桌面应用现名 ChatGPT，Codex 是其开发模式与用于可归属提交的 GitHub 身份）。`CONTRIBUTORS.md`

### 修复

- **双语落地页补署名** —— 新增 Contributors 徽章，并在"参与贡献与安全"一节写明"本项目由 hyt315 与 ChatGPT 的 Codex 模式协作完成，具体贡献与署名见 CONTRIBUTORS.md"。`README.md`、`README.zh-CN.md`

### 变更

- **发版元数据指向本版** —— `release.tag` / `release.title` 更新为 v1.0.3。`.github/repository-metadata.yml`

**English**

### Background

A correction of attribution and naming. The motivation comes from the commit message `docs: attribute ChatGPT Codex collaboration`: GitHub should recognize the collaborator as the Codex identity instead of an unrelated `noreply` account, and the naming should be stated consistently (ChatGPT is the desktop application, Codex remains its software-development mode and commit identity).

### Added

- **Contributor statement `CONTRIBUTORS.md`** — names both roles: `hyt315` as creator (product direction, editorial requirements, release ownership) and `ChatGPT (Codex)` for architecture, implementation, validation, documentation and open-source release engineering, plus the naming convention (the desktop application is now ChatGPT, while Codex remains its development mode and the GitHub identity used for attributable commits). `CONTRIBUTORS.md`

### Fixed

- **Attribution added to both landing pages** — a Contributors badge, plus a sentence in the contributing/security section stating that the project is built by hyt315 with ChatGPT in Codex mode and pointing to CONTRIBUTORS.md. `README.md`, `README.zh-CN.md`

### Changed

- **Release metadata points at this version** — `release.tag` / `release.title` updated to v1.0.3. `.github/repository-metadata.yml`

---

## [1.0.2] - 2026-07-18

### 背景与动机

落地页从"说明"转向"证据"。动机来自提交信息 `docs: add real showcase and install paths (#5)`：让访客第一眼看到真实产物、最短路径就能装上。这一版同时新增 4 个由官方引擎渲染的演示资产，并重写中英双语落地页。

### 新增

- **真实产物演示资产** —— 4 个新文件：30 秒成片、四镜头预览动图、主视觉图与社交预览图，全部由仓库内的官方 Remotion 工程渲染；落地页明确声明预览不是概念图，链接的 MP4 为静音（不转授权第三方配音）。`assets/demo/notebook-video-demo.mp4`、`assets/demo/notebook-video-demo.webp`、`assets/demo/hero.png`、`assets/demo/social-preview.png`
- **安装路径与下载路径** —— 新增 "Install as an Agent Skill"（Codex / Claude Code / Cursor 的用户级与仓库级安装表，含 PowerShell 示例）与 "Download"（HTTPS、SSH、GitHub CLI、分支 ZIP、只取原始契约五种方式），并给出"直接交给编码 Agent 的安装提示词"。`README.md`、`README.zh-CN.md`
- **五分钟首跑示例** —— 把 `check-deps` → `new-project` → `prepare-browser` → 改内容 → `build-semantic-captions` → `render` → `validate-video` 串成一条可照做的命令序列。`README.md`、`README.zh-CN.md`

### 变更

- **中英双语落地页重写** —— 结构改为"为何用它 / 安装为 Agent Skill / 下载 / 五分钟示例 / 环境要求 / 仓库地图 / 验证修改 / 许可与第三方 / 参与贡献与安全"，并把"下载最新版 / 安装 / 看 30 秒示例"提到首屏；旧版的"它做什么 / 开头规则"等段落被并入新结构。`README.md`、`README.zh-CN.md`
- **仓库展示元数据** —— 描述改为 "Agent Skill for turning Chinese explainer scripts into reproducible 2K notebook videos…"，话题增删（新增 `agent-skills`、`motion-graphics`、`subtitles`，移除 `codex`、`video-rendering`），必需状态检查名改为 `validate`，release tag/title 更新为 v1.0.2。`.github/repository-metadata.yml`
- **`.webp` 纳入二进制标注** —— `.gitattributes` 增加 `*.webp binary`，与新增的预览动图配套。`.gitattributes`

**English**

### Background

The landing pages move from explanation to evidence. The motivation comes from the commit message `docs: add real showcase and install paths (#5)`: show the real output first and keep the shortest install path in reach. This version also adds four demo assets rendered by the official engine and rewrites both landing pages.

### Added

- **Real-output demo assets** — four new files: the 30-second film, a four-scene preview animation, a hero image and a social preview, all rendered by the repository's official Remotion project; the landing page states plainly that the preview is not a concept image and that the linked MP4 is silent so no third-party narration is redistributed. `assets/demo/notebook-video-demo.mp4`, `assets/demo/notebook-video-demo.webp`, `assets/demo/hero.png`, `assets/demo/social-preview.png`
- **Install and download paths** — new "Install as an Agent Skill" (user-level and repository-level install tables for Codex, Claude Code and Cursor, with a PowerShell example) and "Download" (HTTPS, SSH, GitHub CLI, branch ZIP, and raw-contract-only) sections, plus a copy-paste install prompt to hand to a coding agent. `README.md`, `README.zh-CN.md`
- **Five-minute first-run example** — `check-deps` → `new-project` → `prepare-browser` → edit content → `build-semantic-captions` → `render` → `validate-video` as one followable command sequence. `README.md`, `README.zh-CN.md`

### Changed

- **Both landing pages rewritten** — the structure becomes "Why use it / Install as an Agent Skill / Download / Five-minute example / Requirements / Repository map / Validate a change / Licensing and third-party materials / Contributing and security", with "download latest / install / see the 30-second demo" moved to the top; the older "What it does" and "Opening rule" paragraphs are folded into the new structure. `README.md`, `README.zh-CN.md`
- **Repository showcase metadata** — the description becomes "Agent Skill for turning Chinese explainer scripts into reproducible 2K notebook videos…", topics change (adding `agent-skills`, `motion-graphics`, `subtitles`; dropping `codex`, `video-rendering`), the required status check becomes `validate`, and the release tag/title moves to v1.0.2. `.github/repository-metadata.yml`
- **`.webp` marked binary** — `.gitattributes` gains `*.webp binary`, matching the new preview animation. `.gitattributes`

---

## [1.0.1] - 2026-07-18

### 背景与动机

首发当天的 CI 与依赖策略修复。动机来自提交信息 `Fix CI validation and dependency policy (#4)`：校验流水线本身有问题、依赖策略需要收紧。改动面只有 3 个文件（+21 / −7），全部落在流程与策略上，不涉及画面。

### 修复

- **CI 的 Python 语法检查不再生成被禁目录** —— 用内联 `python3 -c` 逐个 `compile()` 代替 `python3 -m compileall`，避免检查动作本身生成 `__pycache__`，而流水线下一句恰好断言该目录不得存在。`.github/workflows/validate.yml`
- **GitHub Actions 升到钉住的 v7 提交** —— `actions/checkout` 与 `actions/setup-node` 从 v4 换为 v7.0.0 的 commit 哈希（保持按哈希钉版）。`.github/workflows/validate.yml`
- **CI 显式安装 FFmpeg** —— 在依赖审计与校验之前 `apt-get install --no-install-recommends ffmpeg`，让声明了 FFmpeg/FFprobe 的校验步骤有工具可用。`.github/workflows/validate.yml`
- **Dependabot 不再升级风格引擎** —— 删掉 remotion 分组，改为 `ignore` `@remotion/*` 与 `remotion`，注释写明"Remotion 是风格引擎钉版，不是普通库升级；只能伴随一次渲染视觉复核与契约更新"。`.github/dependabot.yml`

**English**

### Background

A same-day CI and dependency-policy fix. The motivation comes from the commit message `Fix CI validation and dependency policy (#4)`: the validation pipeline itself was faulty and the dependency policy needed tightening. The change touches only 3 files (+21 / −7) and stays entirely in process and policy, not in visuals.

### Fixed

- **The CI Python syntax check no longer creates a forbidden directory** — an inline `python3 -c` loop over `compile()` replaces `python3 -m compileall`, so the check stops generating `__pycache__`, which the very next pipeline step asserts must not exist. `.github/workflows/validate.yml`
- **GitHub Actions bumped to pinned v7 commits** — `actions/checkout` and `actions/setup-node` move from v4 to the v7.0.0 commit hashes, keeping hash pinning. `.github/workflows/validate.yml`
- **CI installs FFmpeg explicitly** — `apt-get install --no-install-recommends ffmpeg` runs before dependency audit and validation, so the steps that declare FFmpeg/FFprobe actually have the tools. `.github/workflows/validate.yml`
- **Dependabot no longer upgrades the style engine** — the remotion group is removed and replaced by an `ignore` for `@remotion/*` and `remotion`, with a comment stating that Remotion is a style-engine pin rather than an ordinary library update and may only move alongside a rendered visual review and a contract update. `.github/dependabot.yml`

---

## [1.0.0] - 2026-07-18

> 初始版本（仓库根提交，没有上一个 tag）：本条不描述"改了什么"，而是记录**这个技能最初是什么**。

### 背景与动机

初始导入。动机未在记录中留存（据改动推断）：该提交只有一条信息 `Release Notebook Video v1.0.0`，同批新增的 `CHANGELOG.md` 首版声明"首个公开发布后开始按语义化版本记录"，未写理由。可确证的是这一版一次交付了完整的三件套 —— 一套可被 Agent 直接执行的制作契约、一份可运行的官方 Remotion 样例工程、以及把它钉住的自动校验与开源工程外壳（受版本控制文件 85 个 / +8336 行）。

### 新增

- **技能主契约 `SKILL.md`（224 行）** —— frontmatter 写明能力与触发场景（做科普视频、手账风视频、定格动画、产品/技能讲解、加中文配音字幕音效、网站动画转 MP4 等）；正文把生产流程写成十步：锁定内容 → 生成 TTS 与语义字幕 → 建模独立部件与层级 → 保持视觉契约 → 逐段加动画 → 声明式音频 → 预载资源 → 渲染与归一化 → 校验成片 → 打包；并给出交付清单与 15 篇参考文档的资源地图。`SKILL.md`
- **官方引擎标识与锁定风格契约** —— 官方默认引擎为暖白（warm-ivory）2K/30fps 的 v8 性能档标识（v1.1.0 起升级为 v9 visual-director 标识）；`references/locked-style-contract.json` 把画布（2560×1440 交付 / 1920×1080 设计坐标系 / 原生 30fps）、调色板、字体、章节条与页眉坐标、字幕输入几何与"拒绝位"（无深色边框、无深色侧痕、无内嵌细线）、层级角色、运动约束、性能约束与编码参数（H.264 CRF16、AAC 192k、faststart、-16 LUFS、真峰 -1.5dBTP、48kHz）写成机读契约，并列出"锁定常量"与"日常可编辑面"。
- **官方 30 秒样例工程 `assets/example-project/`** —— 唯一官方 Remotion 实现 `src/index.tsx`、`storyboard.md`、`narration.txt`、900 帧 `manifests/asset-manifest.json`、字幕资料（`caption-cues.json`、`semantic-caption-lines.txt`、`protected-caption-phrases.txt`）、4 个程序生成音效与许可证、`sync-render-inputs.cjs`、用于网络受限环境的 `remotion-network-shim.cjs`。
- **渲染期资源门与字幕宽度门** —— 样例工程里 `AssetGate` 在第一帧前等字体与音频全部就绪（`delayRender` / `continueRender`），`CaptionFitGate` 在真实字体加载后于浏览器 DOM 中量出每条字幕宽度、超过锁定安全宽（1334px）直接 `cancelRender`。`assets/example-project/src/index.tsx`
- **跨平台 Node 启动器 + 平台薄封装** —— 同一条命令在 macOS Terminal、Windows CMD 与 PowerShell 通用；`notebook-video.mjs` 提供 14 条命令（`check-deps`、`validate-skill`、`new-project`、`build-semantic-captions`、`sync`、`prepare-browser`、`benchmark-render`、`render-range`、`render`、`validate-video`、`validate-caption-sync`、`validate-semantic-breaks`、`validate-official-example`、`package`），`.cmd` / `.sh` 只做转发。`scripts/notebook-video.mjs`
- **自动校验链** —— `validate-skill-consistency.py`（技能内部一致性、废弃 token 与打包排除项）、`validate-official-example.py`（契约与样例工程逐 token 断言 + 渲染输入哈希比对）、`validate-layering.py`（部件层级与退场契约）、`validate-caption-sync.py`（字幕文本、词序与时间同 TTS 边界一致）、`validate-semantic-breaks.py`（保护短语不被切断）、`build-semantic-captions.py`（把人工语义行绑到 TTS 词边界）；`validate-video` 负责容器（H.264/AAC 2560×1440 30fps、48kHz 立体声）、时长偏差 ±0.2s、黑帧检测、响度区间（-18 ~ -14 LUFS，真峰 ≤ -1dBTP）与 12/24 帧接触表。`scripts/`
- **字体与音频资产** —— 内置 Source Han Sans CN Regular/Bold 与 Smiley Sans Oblique 及各自许可证；音效为程序生成并附重用说明。`assets/fonts/`、`assets/example-project/public/sfx/LICENSE.txt`
- **Provider 中立的配音契约** —— 不打包、也不自动安装任何 TTS 客户端；只要求 `audio/narration.mp3` 与逐词时间 JSON，平台 TTS、商业 API、本地模型皆可接入；Edge Read Aloud 只允许作为外部参考提及。`references/tts-audio.md`
- **开源工程外壳** —— Apache-2.0 许可证与第三方声明（`LICENSE`、`NOTICE`、`DEPENDENCIES.md`）、安全与行为准则（`SECURITY.md`、`CODE_OF_CONDUCT.md`）、贡献指南、中英双语落地页（`README.md` / `README.zh-CN.md`）、`CHANGELOG.md`、跨平台适配说明 `CROSS-PLATFORM-ADAPTATION.md`、以及 agent 界面元数据 `agents/openai.yaml`。
- **CI 与仓库配置** —— `.github/workflows/validate.yml`（启动器与脚本语法检查、技能与官方样例校验、锁定依赖 `npm audit`、`new-project` 冒烟测试）、`dependabot.yml`、Issue 与 PR 模板、`repository-metadata.yml`（描述、话题、分支规则集、release tag）。

### 安全

- 仓库忽略凭据、私钥、缓存、渲染产物与本地环境文件（`node_modules/`、`renders/`、`.env*`、`*.key`、`*.pem`、`*.mp4`、`*.zip` 等）。`.gitignore`

**English**

### Background

Initial import (repository root commit; no previous tag). The motivation is not preserved in the record (inferred from the change): the commit carries only the message `Release Notebook Video v1.0.0`, and the `CHANGELOG.md` added in the same change states that semantic versioning begins after the first public release, without giving a reason. What is provable is that this version delivered three parts at once — an agent-executable production contract, a runnable official Remotion example project, and the automated validation and open-source engineering shell that pins them down (85 tracked files / +8336 lines).

### Added

- **Skill contract `SKILL.md` (224 lines)** — the frontmatter states the capability and trigger scenarios (explainer videos, notebook-style videos, stop-motion, product/skill explanations, Chinese narration/subtitles/sound effects, website animation to MP4); the body writes the production workflow as ten steps: lock the content → generate TTS and semantic captions → model independent parts and layers → preserve the visual contract → animate progressively → keep audio declarative → preload assets → render and normalize → validate the actual result → package. It also lists the deliverables and a resource map of 15 reference documents. `SKILL.md`
- **Official engine identity and locked style contract** — the official default engine was the warm-ivory 2K/30fps v8 performance identifier (upgraded to the v9 visual-director identifier in v1.1.0); `references/locked-style-contract.json` records the canvas (2560×1440 delivery / 1920×1080 design space / native 30fps), palette, fonts, chapter and header coordinates, subtitle-input geometry and its rejection flags (no dark border, no dark side marks, no inner line), layer roles, motion and performance constraints, and encoding parameters (H.264 CRF16, AAC 192k, faststart, -16 LUFS, true peak -1.5dBTP, 48kHz) as a machine-readable contract, with explicit locked constants and an ordinary editable surface.
- **Official 30-second example project `assets/example-project/`** — the only official Remotion implementation (`src/index.tsx`), `storyboard.md`, `narration.txt`, a 900-frame `manifests/asset-manifest.json`, caption material (`caption-cues.json`, `semantic-caption-lines.txt`, `protected-caption-phrases.txt`), four procedurally generated sound effects with their license, `sync-render-inputs.cjs`, and `remotion-network-shim.cjs` for restricted networks.
- **Render-time asset gate and caption width gate** — in the example project, `AssetGate` waits for all fonts and audio before the first frame (`delayRender` / `continueRender`), and `CaptionFitGate` measures every caption in the browser DOM after the exact font loads, calling `cancelRender` when the locked safe width (1334px) is exceeded. `assets/example-project/src/index.tsx`
- **Cross-platform Node launcher plus thin platform wrappers** — the same command works in macOS Terminal, Windows Command Prompt and PowerShell; `notebook-video.mjs` provides 14 commands (`check-deps`, `validate-skill`, `new-project`, `build-semantic-captions`, `sync`, `prepare-browser`, `benchmark-render`, `render-range`, `render`, `validate-video`, `validate-caption-sync`, `validate-semantic-breaks`, `validate-official-example`, `package`), and the `.cmd` / `.sh` files only delegate. `scripts/notebook-video.mjs`
- **Automated validation chain** — `validate-skill-consistency.py` (internal consistency, obsolete tokens, packager exclusions), `validate-official-example.py` (token assertions over the contract and example project plus render-input hash comparison), `validate-layering.py` (part layering and exit contracts), `validate-caption-sync.py` (caption text, word order and timing against TTS boundaries), `validate-semantic-breaks.py` (protected phrases never split), `build-semantic-captions.py` (binds authored semantic lines to TTS word boundaries); `validate-video` covers the container (H.264/AAC 2560×1440 30fps, 48kHz stereo), duration within ±0.2s, black-frame detection, loudness range (-18 to -14 LUFS, true peak ≤ -1dBTP) and a 12/24-frame contact sheet. `scripts/`
- **Bundled font and audio assets** — Source Han Sans CN Regular/Bold and Smiley Sans Oblique with their license notices, and procedurally generated sound effects with a reuse note. `assets/fonts/`, `assets/example-project/public/sfx/LICENSE.txt`
- **Provider-neutral narration contract** — no TTS client is bundled or installed automatically; only `audio/narration.mp3` plus a word-timing JSON are required, so platform TTS, commercial APIs and local models all fit; Edge Read Aloud may only be mentioned as an external reference. `references/tts-audio.md`
- **Open-source engineering shell** — Apache-2.0 license and third-party notices (`LICENSE`, `NOTICE`, `DEPENDENCIES.md`), `SECURITY.md`, `CODE_OF_CONDUCT.md`, contribution guide, English and Chinese landing pages (`README.md` / `README.zh-CN.md`), `CHANGELOG.md`, `CROSS-PLATFORM-ADAPTATION.md`, and agent interface metadata `agents/openai.yaml`.
- **CI and repository configuration** — `.github/workflows/validate.yml` (launcher/script syntax checks, skill and official-example validation, locked-dependency `npm audit`, `new-project` smoke test), `dependabot.yml`, issue and PR templates, and `repository-metadata.yml` (description, topics, branch ruleset, release tag).

### Security

- The repository ignores credentials, private keys, caches, rendered output and local environment files (`node_modules/`, `renders/`, `.env*`, `*.key`, `*.pem`, `*.mp4`, `*.zip` and others). `.gitignore`
