# 皮肤契约：archive · 档案灯台（3.3.0）

状态：LOCKED。实现在 `assets/lecture-template/src/theme/archive.tsx`。`new-project ./dir --style=archive`。
手作皮肤**必须**先写导演层 `manifests/treatment.json`（[director-method.md](director-method.md)）。配方见 [style-recipes.md](style-recipes.md)。

## 媒介
冷白的背光台面，上面摆着**真实的**档案物件——Commons / Openverse 上的公有领域扫描件、老照片、手稿、显微照片
（[commons-media.md](commons-media.md)）。放大镜压上去，物件在镜片里"活"过来。
适合：考据、溯源、"这句话最早是谁说的"、历史上的第一张图、真实数据。

## 锁定的值
- 台面与纸：`paperBase` `#edf0f2`（台面）、`paper` `#ffffff`（档案纸）、`paperWarm` `#f7f5ef`；不叠纸纤维（`craft.fibre` 0）。
- 墨：`ink` `#1d2328`、`muted` `#505b65`；辅助蓝 `#3b6ea5`。
- **一个信号色**：`orange` `#e0481f`（字用 `orangeInk` `#ad330e`），只做标注、读数、锚点。
- 卡片：白档案纸、细灰边、2 px 圆角，躺在台面上的短投影，微倾 ±0.4°。
- 字幕：博物馆说明签——白条、左侧 8 px 信号色竖线，墨字 72 设计 px（= 96 px@1440）Noto Serif SC Bold。
- 章节标识：左上编目号 + 宋体章名；无技术页眉。
- 调色：冷灰暗角。背景：`bg-archive-{main,chapter,quiet}.jpg`（背光台面的明暗与网格痕）。
- 背景库（3.4.0）：再加 8 张——`archive/envelope` 档案袋、`newsprint` 旧报纸、`map` 古地图、`catalog` 卡片目录、`filmstrip` 胶片灯箱、`linen` 展柜布面、`ledger` 登记簿、`vellum` 描图纸；不写 `bg` 时按镜头角色自动轮换、相邻不重复，见 [background-library.md](background-library.md)。
- 转场缺省：`slide`（台面横移到下一件）；章节首镜 `drop`。

## 原生动作
1. **镜片里负片转正**：`LoupeMedia` 的 `treatment="negative"` + `insideTreatment="none"`。
2. **一行字亮起**：扫描件上原文那一行在镜片里被信号色标出（`Underline` / `InkCircle` 只画在 `inside` 版本里）。
3. **两份记录并排**：两件 `ArchivePhoto` 并排，编目签对齐，差异处一个信号色圈。
4. **拉远成索引**：最后一个镜头拉远，台面上是整片用到的所有物件，排成编目网格。

## 不要
- 做旧滤镜、咖啡渍、"复古"字体——干净、现代、安静。
- 生成或重画的"假档案"（物件必须是真的；找不到就换媒介）。
- 署名不上屏（组件会强制显示，别用别的方式贴图绕开）。
