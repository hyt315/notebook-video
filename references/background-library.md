# 背景库 · Background library（3.3.0）

> 3.3.0 之前每个皮肤只有 `main / chapter / quiet` 三张背景，一条片子来回就那三张。3.3.0 起每个手作皮肤（journal / papercut / archive）
> 新增 8 张、flat / cel 各新增 5 张风格各异、符合皮肤媒介的背景，旧的三张原样保留并入库（标 legacy）。
> Every craft skin gains 8 backgrounds and flat / cel gain 5 each; the three 3.3.0 rasters stay, marked legacy.

## 1. 怎么用 / Usage

### 换纸粒度 `bgMode`（3.3.0）/ How often the paper changes

`manifests/shots.json` 顶层的 `bgMode` 决定多久换一次背景：

| `bgMode` | 行为 | 默认给谁 |
|---|---|---|
| `"chapter"` | 只在章节首镜换纸，章内所有镜头沿用同一张；跨章不与上一章同一张 | journal / papercut / archive（手作皮肤：全片是"一本手账"，逐镜换纸会打断媒介连续性） |
| `"film"` | 全片一张纸 | —（想要最强的"一本书"感时手动写） |
| `"shot"` | 逐镜轮换（下面的规则，3.3.0–3.3.0 的行为） | flat / cel |

- `chapter` / `film` 模式下那张纸要撑满章内的常规镜头，所以只从 `roles` 含 `main`、且没有标 `busy` 的背景里挑。
- **改回逐镜轮换：** 顶层写 `"bgMode": "shot"`。**完全不轮换（3.3.0 行为）：** `"bgRotate": false`（优先级高于 `bgMode`）。
- 显式写了 `bg` 的镜头永远用它自己的，只影响那一镜，章内其他镜头照样沿用章节纸。
- `validate-backgrounds --shots` 只在 `bgMode=shot` 时把"相邻两镜同一张"记 P1；`chapter` / `film` 模式同章同纸是设计如此，不报。

**装饰重的背景 `"busy": true`：** 便签墙、窗花、洒金笺、祥云、挂笺、红纸衬边、集中线、放射光在 `backgrounds.json` 里标了 `busy`。
自动选择时它们**不会分给 `main` 角色**（也不会当章节纸），只给章节卡或安静镜；想用在某一镜就显式写 `bg`。

### 逐镜轮换（`bgMode: "shot"`）/ Per-shot rotation

`resolve-shots` 按镜头角色从库里给每镜挑一张：

| 镜头 | 角色 | 候选 |
|---|---|---|
| 章节首镜（`src/film.ts` 的 `CHAPTER_SHOTS`；没有就看 `chapter` 名变化） | `chapter` | 本皮肤 `roles` 含 `chapter` 的背景 |
| `zones ≥ 4` 的信息密集镜 | `quiet` | `roles` 含 `quiet` 的背景 |
| 其余 | `main` | `roles` 含 `main`、且不是 `busy` 的背景 |

挑法是纯函数：最久没用过的优先（从没用过的最先），同分按 `sha1(bgSeed:镜号:id)` 定序；**永不与上一镜同一张**（候选只剩一张时除外）。
同一分镜表 + 同一 `bgSeed` → 同一结果。想换一套组合，在 `manifests/shots.json` 顶层写 `"bgSeed": 7`（任意值）。

**指定某一镜：** 在那一镜写 `bg`：

```jsonc
{ "id": "S3", "bg": "ruled" }            // 简写：本皮肤的 journal/ruled
{ "id": "S4", "bg": "journal/oldpage" }  // 全名
{ "id": "S5", "bg": "quiet" }            // 3.3.0 的三张之一（main / chapter / quiet），照旧可用
```

写了不存在的名字或别的皮肤的背景，`resolve-shots` 直接报错并列出本皮肤可选的名字。

**关掉轮换（回到 3.3.0 行为）：** `manifests/shots.json` 顶层写 `"bgRotate": false`。没有 `manifests/backgrounds.json` 的旧工程
本来就不轮换，`resolve-shots` 的输出逐字节不变。

**看一眼全部背景：** `python scripts/dev/bg-gallery.py out.jpg`（需要 numpy + pillow；每张图都按 96 px 交付字号压一行墨色字幕，不加衬底，即门禁量的最坏情况）。

### 引擎怎么画 / How the engine draws it

`resolve-shots` 把选中的库 id 写进 `src/shots.ts` 的 `bg`，文件路径写进 `bgFile`；`src/index.tsx` 的 `Backdrop`
有 `bgFile` 就直接铺这张 2560×1440 的图（`objectFit: cover`，底色 `palette.paperBase`），没有就按 3.3.0 的 `main / chapter / quiet` 走 `THEME.Background`。
相邻两镜背景不同时交叉淡化 10 帧，背景随摄影机视差移动——与 3.3.0 相同。`Theme` 接口没有变。

## 2. 门禁 / Gates

`scripts/validate-backgrounds.py`（标准库；CLI：`notebook-video validate-backgrounds`；`make-video` 构建期自动跑）：

| 级别 | 判据 |
|---|---|
| P0 | manifest 缺字段；文件不在 `public/` 下或不存在；sha256 不符（改图没重跑生成器） |
| P0 | 许可不在白名单（PD / CC0-1.0 / CC-BY-2.0–4.0 / Apache-2.0）；CC BY 缺署名或来源链接；Commons 来源缺标题 / 链接 / 作者 / 原许可 |
| P0 | 不是亮底：整幅平均相对亮度 < 0.55 |
| P0 | 字幕区（交付坐标 x 391–2169、y 1236–1404）：皮肤墨色 vs 区内平均 < 7:1，或 vs 区内最暗 5 %（4 px 模糊后）< 4.5:1。按「字幕衬底不存在」量：journal 本来就没有衬底，其余皮肤有衬底，这条是保底 |
| P1 | 中央 70 % 起伏（1/8 降采样后亮度标准差）> 0.05：背景可能和内容抢 |
| P1 | 皮肤缺某个角色的背景（轮换会退回到全部背景里挑） |
| P1 | `--shots`：分镜里相邻两镜同一张背景（仅 `bgMode=shot` 时报；只可能来自显式 `bg`） |

亮度 / 对比度指标在生成时算好写进 manifest 并与 sha256 绑定；维护者用 `python scripts/dev/bg_metrics.py assets/lecture-template` 从像素按同一算法重算比对（numpy + pillow；单元测试会跑）。
`--min-per-skin journal=8,…` 只数新增的库背景（不含 legacy 三张），CI 与 `validate-skill` 用它守住数量。

## 3. 来源与做法 / Where they come from

按用户「不造轮子」的原则，优先级：

1. **Paper Shaders**（[paper-design/shaders](https://github.com/paper-design/shaders)，`@paper-design/shaders@0.0.82`，Apache-2.0）——纸纹（冷压水彩纸、长纤维宣纸、
   帘纹纸、旧纸 foxing、揉皱折痕）、mesh 渐变、点阵、半调网点。它是 WebGL：3.3.0 因为逐帧 WebGL 在纯 CPU（SwiftShader）上太贵而暂缓。
   3.3.0 的做法是**离线预渲一次**：`scripts/dev/prerender-paper-shaders.py` 用无头 Chromium 把 `scripts/dev/paper-shaders.spec.json` 里每个着色器
   以静态参数（speed 0、固定 seed）渲成 2560×1440 PNG，再由生成器合成、压成 WebP 入库。**渲染期零 WebGL、零新 npm 依赖**。
2. **Wikimedia Commons 的公有领域 / CC0 纹理**（用 `scripts/commons-search.py` 搜，CC0 / PD 优先）：牛皮纸（Coyau，PD）、
   粗麻布（Poly Haven「Hessian 380」，CC0）、1630 年荷兰古地图（PD）。生成器取图时重新核对 Commons 页面上的许可，变了就拒绝。
3. **确定性程序生成**（numpy + pillow，固定 seed，2× 超采样抗锯齿）：横线 / 方格 / 坐标纸、便签、剪纸窗花 / 祥云 / 挂笺 / 洒金、
   档案袋扣绳、报纸版式（灰条，不含真实文字，避免 OCR 门禁误读）、胶片齿孔、账簿栏线、漫画分格 / 集中线 / 网点。纸底复用 3.3.0 的 `make-craft-textures.py`。

重建（只有维护者需要；普通用户永远不跑）：

```bash
pip install playwright numpy pillow && playwright install chromium
python scripts/dev/prerender-paper-shaders.py          # → ~/.cache/notebook-video/paper-shaders/renders/*.png
python scripts/dev/make-bg-library.py                   # → public/bg/lib/*.webp + manifests/backgrounds.json（sha256 + 指标）
python scripts/dev/bg_metrics.py assets/lecture-template
python scripts/validate-backgrounds.py assets/lecture-template --min-per-skin journal=8,papercut=8,archive=8,flat=4,cel=4
```

同一输入两次构建逐字节相同（已验证）。体积：34 张库背景 WebP 共约 2.7 MB（有损 q82；两张大面积浅色渐变用 q95 保住抖动、防色带）。
纸纹的 1 px 颗粒先轻微模糊再编码：H.264 交付时本来就会丢掉这个频段，留着只会让文件大三倍。

**加自己的背景**：把 2560×1440 的图放进工程 `public/bg/lib/`，在工程的 `manifests/backgrounds.json` 里照现有条目加一条（`source` / `license` / `attribution`
必填，`sha256` 自己算，`metrics` 用 `python scripts/dev/bg_metrics.py 图片` 的输出），再重跑 `resolve-shots`。BY-SA / NC / ND 不收。

## 4. 清单与许可 / Inventory and licences

Paper Shaders 与程序生成的图由本仓库生成，随仓库以 Apache-2.0 发布；Commons 来源的图保留原许可（PD / CC0），署名照样写上（好习惯，也便于核查）。
完整字段（seed、着色器参数、合成步骤、sha256、对比度指标）见 `assets/lecture-template/manifests/backgrounds.json`。

### journal

| id | 名称 | 角色 | 来源 | 许可 | 署名 / 出处 |
|---|---|---|---|---|---|
| `journal/ruled` | 横线本 | main / quiet | Paper Shaders 预渲 | Apache-2.0 | `ps-coldpress` · @paper-design/shaders@0.0.82 |
| `journal/grid` | 方格本（线圈） | main / chapter | Paper Shaders 预渲 | Apache-2.0 | `ps-coldpress` · @paper-design/shaders@0.0.82 |
| `journal/dots` | 点阵本 | main / quiet | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1103 |
| `journal/kraft` | 牛皮纸本 | main / chapter | Wikimedia Commons | PD | [File:Kraft tileable 1024x1024.png](https://commons.wikimedia.org/wiki/File:Kraft_tileable_1024x1024.png) · Coyau (own work) |
| `journal/watercolor` | 水彩纸 | chapter / main | Paper Shaders 预渲 | Apache-2.0 | `ps-coldpress` · @paper-design/shaders@0.0.82 |
| `journal/sticky` | 便签墙 | chapter / main | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1106 |
| `journal/oldpage` | 旧书页 | main / chapter | Paper Shaders 预渲 | Apache-2.0 | `ps-oldpage` · @paper-design/shaders@0.0.82 |
| `journal/graph` | 坐标纸 | quiet / main | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1108 |
| `journal/main` | 棉纸·常规 *(legacy)* | main | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |
| `journal/chapter` | 棉纸·章节 *(legacy)* | chapter | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |
| `journal/quiet` | 棉纸·安静 *(legacy)* | quiet | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |

### papercut

| id | 名称 | 角色 | 来源 | 许可 | 署名 / 出处 |
|---|---|---|---|---|---|
| `papercut/hongzhi` | 红纸衬边 | chapter | Paper Shaders 预渲 | Apache-2.0 | `ps-xuan` · @paper-design/shaders@0.0.82 |
| `papercut/xuan` | 宣纸 | main / quiet | Paper Shaders 预渲 | Apache-2.0 | `ps-xuan` · @paper-design/shaders@0.0.82 |
| `papercut/kraft` | 牛皮纸·红绳 | main / chapter | Wikimedia Commons | PD | [File:Kraft tileable 1024x1024.png](https://commons.wikimedia.org/wiki/File:Kraft_tileable_1024x1024.png) · Coyau (own work) |
| `papercut/origami` | 折纸纹 | main / quiet | Paper Shaders 预渲 | Apache-2.0 | `ps-origami` · @paper-design/shaders@0.0.82 |
| `papercut/lattice` | 窗花角 | chapter / main | Paper Shaders 预渲 | Apache-2.0 | `ps-xuan` · @paper-design/shaders@0.0.82 |
| `papercut/sajin` | 洒金笺 | main / chapter | Paper Shaders 预渲 | Apache-2.0 | `ps-xuan` · @paper-design/shaders@0.0.82 |
| `papercut/cloud` | 祥云 | chapter / main | Paper Shaders 预渲 | Apache-2.0 | `ps-xuan` · @paper-design/shaders@0.0.82 |
| `papercut/menjian` | 挂笺 | chapter | Paper Shaders 预渲 | Apache-2.0 | `ps-xuan` · @paper-design/shaders@0.0.82 |
| `papercut/main` | 米纸·常规 *(legacy)* | main | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |
| `papercut/chapter` | 米纸·章节 *(legacy)* | chapter | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |
| `papercut/quiet` | 米纸·安静 *(legacy)* | quiet | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |

### archive

| id | 名称 | 角色 | 来源 | 许可 | 署名 / 出处 |
|---|---|---|---|---|---|
| `archive/envelope` | 档案袋 | chapter / main | Wikimedia Commons | PD | [File:Kraft tileable 1024x1024.png](https://commons.wikimedia.org/wiki/File:Kraft_tileable_1024x1024.png) · Coyau (own work) |
| `archive/newsprint` | 旧报纸 | main | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1302 |
| `archive/map` | 古地图 | chapter / main | Wikimedia Commons | PD | [File:Helmink Antique map of Holland by Anonymous 3rd state by Frederick de Wit 1630.jpg](https://commons.wikimedia.org/wiki/File:Helmink_Antique_map_of_Holland_by_Anonymous_3rd_state_by_Frederick_de_Wit_1630.jpg) · Anonymous, 3rd state by Frederick de Wit (1630); scan Leen Helmink |
| `archive/catalog` | 卡片目录 | main / quiet | Paper Shaders 预渲 | Apache-2.0 | `ps-laid` · @paper-design/shaders@0.0.82 |
| `archive/filmstrip` | 胶片灯箱 | main / chapter | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1305 |
| `archive/linen` | 展柜布面 | main / quiet | Wikimedia Commons | CC0-1.0 | [File:Hessian 380 diff 8k (Rico Cilliers and colormass via Poly Haven).jpg](https://commons.wikimedia.org/wiki/File:Hessian_380_diff_8k_(Rico_Cilliers_and_colormass_via_Poly_Haven).jpg) · Rico Cilliers (processing), colormass (photography) via Poly Haven |
| `archive/ledger` | 登记簿 | quiet / main | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1307 |
| `archive/vellum` | 描图纸 | quiet / main | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1308 |
| `archive/main` | 灯箱·常规 *(legacy)* | main | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |
| `archive/chapter` | 灯箱·章节 *(legacy)* | chapter | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |
| `archive/quiet` | 灯箱·安静 *(legacy)* | quiet | 程序生成 | Apache-2.0 | `scripts/dev/make-craft-textures.py` |

### flat

| id | 名称 | 角色 | 来源 | 许可 | 署名 / 出处 |
|---|---|---|---|---|---|
| `flat/mesh-dawn` | 晨光渐变 | main / quiet | Paper Shaders 预渲 | Apache-2.0 | `ps-mesh-dawn` · @paper-design/shaders@0.0.82 |
| `flat/mesh-mint` | 薄荷渐变 | main / quiet | Paper Shaders 预渲 | Apache-2.0 | `ps-mesh-mint` · @paper-design/shaders@0.0.82 |
| `flat/dotgrid` | 点阵 | quiet / main | Paper Shaders 预渲 | Apache-2.0 | `ps-dotgrid` · @paper-design/shaders@0.0.82 |
| `flat/sunrise` | 暖角渐变 | chapter / main | Paper Shaders 预渲 | Apache-2.0 | `ps-grain-sun` · @paper-design/shaders@0.0.82 |
| `flat/shapes` | 几何角饰 | chapter / main | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1405 |
| `flat/main` | 天空吉祥物·常规 *(legacy)* | main | AI 生成（3.2.0） | Apache-2.0 | 见 `manifests/visual-assets.json` |
| `flat/chapter` | 天空吉祥物·章节 *(legacy)* | chapter | AI 生成（3.2.0） | Apache-2.0 | 见 `manifests/visual-assets.json` |
| `flat/quiet` | 天空吉祥物·安静 *(legacy)* | quiet | AI 生成（3.2.0） | Apache-2.0 | 见 `manifests/visual-assets.json` |

### cel

| id | 名称 | 角色 | 来源 | 许可 | 署名 / 出处 |
|---|---|---|---|---|---|
| `cel/halftone` | 网点角 | main / chapter | Paper Shaders 预渲 | Apache-2.0 | `ps-halftone-corners` · @paper-design/shaders@0.0.82 |
| `cel/speedlines` | 集中线 | chapter | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1502 |
| `cel/panels` | 分格边 | main / chapter | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1503 |
| `cel/screentone` | 渐变网点 | main / quiet | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1504 |
| `cel/sunburst` | 放射光 | chapter | 程序生成 | Apache-2.0 | `scripts/dev/make-bg-library.py` seed 1505 |
| `cel/main` | 漫画角饰·常规 *(legacy)* | main | AI 生成（3.2.0） | Apache-2.0 | 见 `manifests/visual-assets.json` |
| `cel/chapter` | 漫画角饰·章节 *(legacy)* | chapter | AI 生成（3.2.0） | Apache-2.0 | 见 `manifests/visual-assets.json` |
| `cel/quiet` | 漫画角饰·安静 *(legacy)* | quiet | AI 生成（3.2.0） | Apache-2.0 | 见 `manifests/visual-assets.json` |
