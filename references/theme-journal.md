# 皮肤契约：journal · 博物学家手账（3.3.0）

状态：LOCKED。实现在 `assets/lecture-template/src/theme/journal.tsx`。`new-project ./dir --style=journal` 选它（会按需下载 Noto Serif SC Bold，OFL-1.1，sha256 锁定）。
手作皮肤**必须**先写导演层 `manifests/treatment.json`（[director-method.md](director-method.md)），`validate-treatment.py` 把缺项记 P0。
配方（八个轴）见 [style-recipes.md](style-recipes.md)。

## 媒介
一页暖白棉纸笔记本。东西是被**画上去、贴上去、写上去**的：水彩淡彩、钢笔批注、胶带贴住的照片和裁下的纸片。
适合"有人第一次看见"：观察、实验记录、生物 / 自然 / 历史上的发现。

## 锁定的值
- 纸面：`paper` `#fbf6ea`（卡片）、`paperWarm` `#f6eedc`、`paperBase` `#efe6d2`（台面）；卡片叠纸纤维（`textureOpacity` 0.55）。
- 墨：`ink` `#2b2420`、`muted` `#5b4f44`。
- 强调：**只有朱砂** `orange` `#c8442a`（字用 `orangeInk` `#a2311b`）。淡彩：雨水蓝 `#4f7d95`、鼠尾草绿 `#6f8f5a`、赭黄 `#d8a23a`——只做大面积淡彩，不写字。
- 卡片：一张裁下的纸，两条和纸胶带贴在左上角，按位置确定性微倾 ±0.8°，贴面暖投影（不是 UI 悬浮影）。
- 字幕：**没有胶囊**。72 设计 px（= 96 px@1440）Noto Serif SC Bold 墨字直接写在纸上，下面垫纸色柔光晕（任何底上 ≥7:1）。
- 章节标识（`Chrome`）：左上角钢笔小字 "No.01 — 章名" + 一条手划线；**没有**右上技术页眉、没有吉祥物。
- 调色（`Grade`）：轻微暖色 + 暗角。
- 背景：`bg-journal-{main,chapter,quiet}.jpg`（2560×1440，`scripts/dev/make-craft-textures.py` 确定性生成，sha256 登记）；chapter 变体左下 / 右上各一团水彩晕。
- 背景库（3.4.0）：再加 8 张——`journal/ruled` 横线本、`grid` 方格本、`dots` 点阵本、`kraft` 牛皮纸本、`watercolor` 水彩纸、`sticky` 便签墙、`oldpage` 旧书页、`graph` 坐标纸；不写 `bg` 时按镜头角色自动轮换、相邻不重复，见 [background-library.md](background-library.md)。
- 转场缺省：`slide`（沿同一页横移）；章节首镜 `drop`（新的一页盖上来）。

## 原生动作（顿悟点用）
1. **晕染即揭示**：`WashBlob` 在结构上晕开，水干后边缘自己变深——"本来就在那里，只是你没看出来"。
2. **标本 + 批注**：`PinnedPhoto` 贴上真实标本照，`HandNote` 的引线长到细节上再写字。
3. **放大镜压在真照片上**：`Loupe` / `LoupeMedia`，镜片里的东西和镜外不一样（被刷上颜色、被圈出）。
4. **雾洗回白纸**：结尾一层纸色淡彩盖过整页，回到开头的空白页，但留下一处变化。

## 不要
- 矢量插画套水彩滤镜；暗底；发光；UI 胶囊、进度条、终端窗口当主角。
- 在淡彩上写字（字只写在纸上）；一帧超过 3 处画内文字。
