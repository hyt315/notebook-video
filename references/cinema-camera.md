# 引擎虚拟镜头（v4.4 · `src/cinema.tsx`）

> **何时读**：写分镜表之前。它决定这部片「像电影还是像 PPT」。
> 场景自己的 `ShotCamera`（[shot-language.md](shot-language.md)）仍然在；本层套在它**外面**，由引擎（`index.tsx` 的 `FinalDemo` / `Backdrop`）统一驱动。分镜表什么都不写也有缺省运动。

## 1. 为什么要有这一层

v4.3 之前每一镜是「静止舞台 + 卡片依次出现」：即使 `ShotCamera` 推了 3%，观众感受仍是翻幻灯片。
v4.4 在引擎里给每一镜套一台虚拟摄影机，并且把「内容太小」「镜头不跟讲解」「换镜硬切」这三类 PPT 感的来源变成默认行为与门禁。

## 2. 六个能力（全部是帧的纯函数）

| 能力 | 缺省 | 分镜表写法 | 说明 |
|---|---|---|---|
| **fit** 内容自动放大 | `auto` | `cinema.fit: "auto" \| "none"` | anchor 占内容带（安全区）面积 < 60% 时，整镜按 anchor 中心推近到 72%；上限：anchor 放大后仍在内容带内、≤ 1.30、与场景缩放相乘 ≤ 1.35。`resolve-shots.py` 预算成 `cinema.fit = {x, y, s, fill, fillAfter}`。 |
| **drift** 缓推 / 漂移 | `auto`（4.5%） | `cinema.drift: "auto" \| "none" \| 0–0.08` | 每镜一次慢推，镜与镜之间轮换：正推 → 右移推 → 拉 → 左移推（不会全片同一种推）。 |
| **focus** 讲到哪推到哪 | 无 | `cinema.focus: [{beat \| cue \| at, region \| x,y,w,h, zoom?, hold?}]` | 第 N 拍开始，弹簧曲线（20 帧）推近该区域，停 `hold` 帧（缺省 60）后 24 帧缓拉回；相邻焦点首尾相接时直接从一个**横摇**到下一个。`region` 简写：`left/right/top/bottom/center/top-left/…`（按本镜 `contentBand` 切）。<br>**不切字（v4.5c）**：`slide: false` 关掉横向滑回；`keep: {x,y,w,h} \| region` = 推近时也必须完整入画的矩形（例如推近右侧终端时左侧的大数字），引擎把推近倍数降到能装下「焦点 ∪ keep」（留 28 px 边距，不低于 1.1，装不下就忽略 keep）。`hero-number` 版式缺省 `keep` = anchor + 8% 字号的字形外溢余量；`keep: false` 关掉。镜头里有 MediaFrame 卡片又要推近别处时，给卡片写 `keep`，否则卡片会被推出画面一半。 |
| **pan** 宽画布横摇 | 无 | `cinema.pan: {worldW: 2800, beat? \| at?, dur?, dir?: "ltr" \| "rtl"}` | 场景按更宽的世界排版，摄影机横摇扫过（时间线、长链路）。 |
| **transition** 换镜 | `auto` | 镜级 `transition` | `auto` = 章节首镜 **zoom**（推穿：上一镜放大淡出、新镜从远处推来）、其余 **whip**（甩镜：水平方向模糊 + 位移，左右交替）；也可写 `whip / whip-left / whip-right / zoom / fade / hard`。`cut / handoff / reveal` 是旧写法，引擎按 `auto` 处理。转场 14 帧。 |
| **parallax** 视差 | 开 | — | 背景按 0.3 的系数跟随摄影机（背景动得比内容少 → 纵深），预放大 1.06 保证不露边；甩镜时背景一起甩。 |

纪律：无随机、无状态、无实时动画库；同一帧渲两次结果相同。总缩放（场景 × 引擎）钳在 `TEXT_ZOOM_MAX = 1.35`，取景窗永远落在 1920×1080 舞台（或 pan 世界）之内。

## 3. 怎么写一镜

```jsonc
{
  "id": "S3", "layout": "code-full",
  "anchor": {"x": 200, "y": 200, "w": 1520, "h": 620},        // 内容外接矩形：决定自动放大
  "contentBand": {"x": 160, "y": 180, "w": 1600, "h": 690},   // 安全区
  "beats": [{"cue": 4}, {"cue": 4, "offset": 30}, {"cue": 5}],
  "cinema": {
    "focus": [
      {"beat": 1, "x": 200, "y": 486, "w": 1080, "h": 200, "zoom": 1.3, "hold": 66},  // 先推到「查库」那一行
      {"beat": 2, "x": 200, "y": 372, "w": 1080, "h": 200, "zoom": 1.3, "hold": 80}   // 再横摇到「装饰器」那一行
    ]
  }
}
```

- 焦点矩形是**场景设计坐标**（和你在场景里写的 `left/top` 同一套），引擎会经过场景 `ShotCamera` 换算到屏幕。
- 代码镜头：配合 `HighlightCode active={行号}` 把高亮钉在讲到的那一行，镜头同时推过去——「讲到哪一行，亮哪一行、推哪一行」。
- 一镜 1–2 个焦点最好；每个焦点都要对应旁白里真的在讲的东西，否则是「为了动而动」。

## 4. 内容要大（60–80% 安全区）

- 代码镜头：`HighlightCode fontSize={34–40}`；差异镜头：`DiffView fontSize={26–32}`；控制台是主角时 `ConsoleWindow fontSize={28–34}`。
- 关键数字：`KineticNumber`（`src/cinema.tsx`）——计数（ease-out）+ 落定瞬间放大 1.18 回弹 + 下划线扫入；字号 200–380。用在「讲到这个数」的那一拍。
- `validate-shot-motion.py` 复核每镜 `fillAfter`：< 45% → **P0**（引擎推到上限仍太小，内容本身画小了）；45–60% → P1；> 90% → P1（太满，或 anchor 写得比内容大）。

## 5. 相邻镜头换布局

分镜表可写 `layout`（自由命名的版式：`hero-number / chart-number / code-full / diff-split / rail / ring-tree / chart-metric / hero-verdict …`）。
`validate-composition.py`：相邻两镜都写了 `layout` 且相同 → **P0**。骨架不同但版式一样，观众照样读作「同一页换了字」。

## 6. 门禁口径

| 门禁 | 查什么 |
|---|---|
| `resolve-shots.py` | `cinema.drift / fit / focus / pan` 与 `transition` 取值；focus 的 beat 越界；region 名 |
| `validate-shot-motion.py` | `fillAfter` 60–80%；focus zoom × 场景缩放 ≤ 1.35；焦点矩形放大后放得进画面；focus.at 在本镜内；缺 cinema 块（旧解析结果）→ P1 |
| `validate-composition.py` | 转场闭合集合（`auto/cut/handoff/reveal/whip/whip-left/whip-right/zoom/fade/hard`）；相邻 `layout` 不同 |
| 渲染期 | 转场期间新旧两镜都挂载，带 `data-gate-allow="handoff"`，重叠门禁对这 14 帧放行 |
