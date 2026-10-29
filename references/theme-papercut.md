# 皮肤契约：papercut · 红色窗花剪纸（3.3.0）

状态：LOCKED。实现在 `assets/lecture-template/src/theme/papercut.tsx`。`new-project ./dir --style=papercut`。
手作皮肤**必须**先写导演层 `manifests/treatment.json`（[director-method.md](director-method.md)）。配方见 [style-recipes.md](style-recipes.md)。

## 媒介
一切都是剪刀剪出来、平铺在米色宣纸上的纸片；细节只来自"剪掉了什么"——**洞就是线**。正面光，纸有厚度。
适合：对称、复制、一变多、缺一块还能补回、结构与镂空（纠错码、细胞分裂、雪花、编码）。

## 锁定的值
- 纸面：`paper` `#fbf3e3`、`paperWarm` `#f4e7cf`、`paperBase` `#efe2c8`（米色宣纸家族，底**永远**不是红的）。
- 主材：中国红 `orange` `#d2201f`（字用 `orangeInk` `#a3151a`）；配角纸：靛青 `#2f4e7a`、玉绿 `#3e7d68`；金箔 `gold` `#c9a13b` **全片只用一次**。
- 墨：`ink` `#2a1a14`、`muted` `#654b3b`。
- 卡片：一张米色厚纸，不倒圆角，内侧一圈红色"阴刻"双线（剪纸的双轮廓），紧贴软影 + 右下 1 px 切口暗边，微倾 ±0.5°。
- 字幕：一条深红横批（`#8f1216`，两端燕尾，像贴上去的对联条），米色字 72 设计 px（= 96 px@1440）Noto Serif SC Bold，≥7:1。
- 章节标识：左上一枚红色方印（序号）+ 宋体章名；无技术页眉。
- 背景：`bg-papercut-{main,chapter,quiet}.jpg`；chapter 变体上沿一条红色锯齿条（装饰区 y<72）。
- 背景库（3.4.0）：再加 8 张——`papercut/hongzhi` 红纸衬边、`xuan` 宣纸、`kraft` 牛皮纸·红绳、`origami` 折纸纹、`lattice` 窗花角、`sajin` 洒金笺、`cloud` 祥云、`menjian` 挂笺；3.7.0 起手作皮肤默认 `bgMode: "chapter"`：只在章节首镜换纸、章内沿用（装饰重的 `busy` 背景只给章节卡 / 安静镜）；想全片一张纸写 `"bgMode": "film"`，想改回逐镜轮换写 `"bgMode": "shot"`，见 [background-library.md](background-library.md)。
- 转场缺省：`peel`（3.5.0，从右下角把上一张剪纸揭起来，见 [fx-effects.md](fx-effects.md)）；画不了 WebGPU 时自动退回 `drop`（新纸盖上来）。运动用 `CutPaper` 的 12 fps 跳帧（剪纸动画手感），落定不弹。

## 原生动作
1. **对折一刀展开**：一条路径镜像成两份 / 四份，同时出现——复制、对称。
2. **碎片飞回原位**：缺了的纸片按原路径落回——纠错、修复、"缺了还能补"。
3. **剪掉一角**：一片纸少一块，结构还在不在？
4. **背光透洞**：`CutPaper` 的 `backlit`，洞里透出暖光——"空的地方才是重点"。

## 不要
- 红底红字、红压红；渐变、描边、发光、阴影糊成一片。
- 镂空细于 6 设计 px（1440p 下会糊）；金箔用两次。
