# 时间码分镜：GitHub 开源三部曲 EP0（官方模板示例片）

paper 皮肤 · 16:9 · 1150 帧（38.3 秒）· 4 章 8 镜 · 4 种骨架

> 本文件由 `manifests/shots.json`（语义分镜表）派生，**帧号不手写**：
> 改台词 → 改 `narration.txt` 与 `manifests/semantic-caption-lines.txt` → 重跑 `scripts/resolve-shots.py`。

## 镜头表

| 镜 | 帧 | 时长 | 章 | 骨架 | 视觉介质 | 镜头意图 | 转场 | 入场 | 活性组件 |
|---|---|---|---|---|---|---|---|---|---|
| S1 | 0–213 | 7.1s | 代码不再孤独 | Stage | console / graphic | establish | cut | rise | ConsoleWindow · StampBanner |
| S2 | 213–286 | 2.4s | 入场三步 | Corridor | graphic / chart | pan-follow | handoff | rise | StampSeal |
| S3 | 286–416 | 4.3s | 入场三步 | Zoom | code / console | reveal | reveal | zoom | DiffView · Typewriter |
| S4 | 416–532 | 3.9s | 第二步 · 发布 | Split | text / code | push-in | handoff | slide | FitCard · StaggerList |
| S5 | 532–682 | 5.0s | 第三步 · 运营与三技能 | Stage | chart / metric | push-in | cut | fade | Funnel · ProgressRing |
| S6 | 682–803 | 4.0s | 第三步 · 运营与三技能 | Corridor | graphic / text | pan-follow | handoff | rise | StampSeal |
| S7 | 803–919 | 3.9s | 第三步 · 运营与三技能 | Zoom | console / text | reveal | reveal | zoom | ChatThread · SkeletonCard |
| S8 | 919–1150 | 7.7s | 第三步 · 运营与三技能 | Stage | metric / text | pull-back | handoff | fade | MetricGrid · StampBanner |

## 多样性（门禁 P0）

- 骨架：4 种（Corridor / Split / Stage / Zoom）；相邻不同款：无相邻重复
- 视觉介质：6 种（chart / code / console / graphic / metric / text）
- 每章运镜：代码不再孤独 1 次；入场三步 2 次；第二步 · 发布 1 次；第三步 · 运营与三技能 4 次

## 固定约束

- 页眉 / 章节卡 / 字幕在 `ShotCamera` 之外（屏幕空间），不被运镜带动；
- 内容坐在羽化底托上（负 z），背景装饰保持原样；
- 每镜只挂载活动场景，旧元素完整离场；
- 音效钉帧相对所属镜头起点推导；
- 本片场景按 16:9 设计空间编写；4:3 / 3:4 需要各自的版面重排。
