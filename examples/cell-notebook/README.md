# 参考片（仅文档）·《细胞为什么叫细胞》（cell 片）

> **仅文档，不能直接运行。** 本目录没有 story.json，也不含素材与成片；它记录的是一支 49.1 秒 / 8 镜 / `journal` 皮肤 / 2560×1440 成片的导演层与分镜，用来学方法。
> 想直接跑一支同题材的片子：`node scripts/make-video.mjs examples/recipes/cork-page.story.json <工程> --stills`（4 镜精简版，自带导演层；缺图版时 make-video 会给出要先运行的 commons-search 命令）。
它证明了一件事——**讲解视频的说服力来自「真东西 + 手写的证据」，不是来自更多笔画。**

本目录只放**导演层与分镜**（不含素材与成片，素材见文末）：

| 文件 | 是什么 |
|---|---|
| `treatment.json` | 导演层：隐喻、媒介选择、招牌镜头、8 镜的景别/运镜/理由、已核实事实与出处、声音设计 |
| `storyboard.md` | resolve-shots 生成的分镜表：每镜实际缩放、转场、背景、组件、字幕摘要 |
| `narration.txt` | 旁白（15 句，TTS 生成，词级时间对齐） |

## 三镜的构成（现在用 `layout: "page"` 就能排出来）

### S3 · 图版页 —— `plate`

一张 1665 年原版铜版画装裱在右侧（画宽 45%），左侧手写「1665」+ 朱红印章「胡克」+ 手写「第十八篇 · 软木」。
画面没有一个卡片框，容器是牛皮纸。

### S4 · 招牌镜头 —— `loupe`

放大镜压在同一张图版上（图版位置不动，切镜时它不跳），镜内是 3 倍放大的格子；
镜内的格子被水彩一格一格刷成「房间」（约 2 秒刷完），墨线盒壁永远压在颜色之上。
**这是全片的核心动作**：把「别人没看见的东西」放大给观众看。

### S7 · 抽色 —— 组件做不到的那件事

拉远让今天的真显微照与 S4 的「房间」并排，然后把颜色抽干，只剩墨线画的墙。
「房间被涂满又被抽空、墙还在」只有颜料与墨的物质差别演得出——这是选 `journal` 媒介的理由本身。

## 现在怎么写（自动版式）

```json
{"role": "context", "layout": "page",
 "lines": ["1665 年，胡克削下一片软木。", "放到显微镜下。"],
 "content": {"page": "plate", "media": "hooke-plate", "catalogue": "Schem. XI",
             "title": "《显微图谱》1665", "big": "1665", "stamp": "胡克", "note": "第十八篇 · 软木"}}
```

```json
{"role": "evidence", "layout": "page",
 "lines": ["他看见「许许多多的小盒子」。", "他把它们叫作 cells。"],
 "content": {"page": "loupe", "media": "hooke-plate", "catalogue": "Schem. XI",
             "title": "《显微图谱》1665", "big": "细胞", "note": "cells · 小房间",
             "look": [0.25, 0.42], "zoom": 2.6}}
```

可运行的四镜版（图版 → `compare` 讲 cella→cell 的词义 → 放大镜 → 十二亿间）见 `examples/recipes/cork-page.story.json`，配套导演层 `examples/recipes/cork-page.treatment.json`。

## 素材与署名

| id | 文件 | 来源 | 许可 |
|---|---|---|---|
| `hooke-plate` | `hooke-plate.jpg` | [Micrographia Schem 11](https://commons.wikimedia.org/wiki/File:Micrographia_Schem_11.jpg) | Public domain · Robert Hooke (1635–1703) |
| `cork-micro` | `cork-micro.png` | Wikimedia Commons | 见工程 `manifests/media.json` |
| `pencil` | `pencil.wav` | Commons PD 铅笔声 | Public domain |

只在画面里显示署名（`ArchivePhoto` / `PinnedPhoto` 自动带）。**不要**把图版裁掉署名区。

## 构图与细节提示

抄它的**语法**（纸、真图版、手写、印章、放大镜），并留意三个构图要点：

- 手账皮肤仍要保持主题物在画面中的体量感，避免主图版长期缩在一角。
- 图版框若受竖构图高度限制，可配合右侧手写批注或局部放大镜均衡版面。
- 课本对比示意与真实显微素材之间应通过几何轮廓或引线建立清晰对照。
