# 镜头语言、虚拟摄影机与转场

运镜与转场：场景自己的 ShotCamera、引擎的虚拟摄影机、镜头语言和真翻页 / 揭纸转场。

本篇各节：

- [镜头语言：受限配方 + 出界数学证明](#shot-language)
- [镜头语言：为什么动、动多少、什么时候不动](#camera-language)
- [引擎虚拟镜头（`src/cinema.tsx`）](#cinema-camera)
- [真翻页 / 揭纸转场（`@remotion/effects`）](#fx-effects)

<a id="shot-language"></a>

## 镜头语言：受限配方 + 出界数学证明

> 状态：**生效**。取代旧的 `Camera Micro-Framing Invariant`。
> 落地件：`assets/lecture-template/src/shotkit.tsx`；门禁：`scripts/validate-shot-motion.py`。

### 目录

- [1. 为什么改](#1-为什么改)
- [2. 六个运镜意图](#2-六个运镜意图--still合法取值-7-个)
- [2.5 平移安全预算](#25-平移安全预算想平移多少就先缩放到能覆盖它铁律)
- [3. anchor：出界证明](#3-anchor出界证明)
- [4. 配额](#4-配额防止为了动而动也防止全片不动)
- [5. 怎么写](#5-怎么写)
- [6. 向后兼容](#6-向后兼容)
- [7. 自检](#7-自检)

> 本文件讲场景自己的 `ShotCamera`。引擎在它外面还有一台虚拟摄影机（缺省缓推、讲到哪推到哪、横摇、甩镜/推穿转场、视差、内容自动放大），见 [camera.md#cinema-camera](camera.md#cinema-camera)。两者相乘的总缩放仍钳在 1.35。

### 1. 为什么改

> 本节数字均为 **早期版本的历史口径**（源码已复算核实），现行规则见下文。

早期版本的铁律把虚拟相机锁在 `x ∈ [945, 975]`（±15px）、`y ∈ [538, 542]`、`s ∈ [1.00, 1.018]`。
这三个界是 **16:9 的 1920×1080 设计空间**里的取值。
景别变化上限 **1.8%**，等同定焦；而且 `CameraRig` 是**全片一条关键帧轨道**，包在所有场景外——
所以**每个镜头不可能有自己的取景**。观众感受到的就是"翻页"。

同时这条铁律并没有真的保住稳定性（口径澄清 + 真数，均按旧源码复算；
`CAM_KEYS_P` 与 `CameraRig` 整条轨道已删除）：该轨道共 15 个关键帧，
其中 10 个是 `s` 超过旧上限 1.018（最大 s=1.14）——这是拿 16:9 口径去量当年竖屏轨道的结论（竖屏画布已删除）；
x 最偏到 410，但 x=410 在 1080 宽空间本身合法，与 945–975 并排属范畴错误。
**真正危险的是"可见窗出画"口径：8 个关键帧**（f=248/328/390/613/669/840/950/1056），
最大露出 383px（第 950 帧下缘）；逐帧扫描非零露底约 862–892 帧（随亚像素容差浮动）。
根因不变：**没有任何校验器能抓到它**。

结论（与历史方案一致）：**不能靠"放开限制"解决（自由曲线会立刻出界），
只能把自由曲线换成"带内置不变量的受限配方"，并把"不出界"从"靠不动"换成"靠证明"。**

### 2. 六个运镜意图 + `still`（合法取值 7 个）

每个镜头（shot）声明**一个** intent，曲线形状由 intent 决定，调用方只填少量参数。

| intent | 用途 | 缩放预算 | 默认参数 |
|---|---|---|---|
| `establish` | 章节开场建立空间 | `s ≤ 1.05` | 稳定 0.5s 后微推至 `1.03` |
| `push-in` | 聚焦细节 / 揭示重点 | `s ≤ 1.35` | `1.00 → 1.12` |
| `pull-back` | 章节收束、拉远 | `s ≤ 1.60` | `1.12 → 1.00` |
| `pan-follow` | 对象沿轨道移动时跟随 | `s ≤ 1.20` | 注视点从 `fromX/fromY` 移到 `x/y`，缩放不变 |
| `reveal` | 擦除揭示（转场即表达） | `s ≤ 1.12` | `1.00 → 1.08`，与 `RevealMask` 共用时间线 |
| `micro-orbit` | 单体 hero 微环绕 | `s ≤ 1.10`，`rotY ≤ 6°` | 走 3D 路径（CSS `zoom`） |
| `still` | 明确不运镜 | `s = 1.00` | 合法，但受配额限制 |

**缩放上限按主角类型收紧**（硬上限）：

- 含文字的镜头 `s ≤ 1.35`（`TEXT_ZOOM_MAX`）；
- 纯图形镜头 `s ≤ 1.60`（`GRAPHIC_ZOOM_MAX`）。

超过 1.35 的文字会被光栅化后放大而发虚，所以"放大"这件事**优先用更大的字号做，
而不是用相机推近做**——这也是 everything2explainer 「主角尺寸档」的道理。

### 2.5 平移安全预算：想平移多少，就先缩放到能覆盖它（**铁律**）

相机平移会**整层移动内容**，所以在 `s = 1.00` 时任何平移都会把内容推出画面、露出边缘。
实测：`pan-follow` 在 `s=1.0` 下把走廊左侧的站名裁掉了。

几何上，缩放为 `s` 时可见窗半宽 = `960/s`，只要窗口仍落在 1920×1080 舞台内就不会露边，因此：

```
maxPanX = 960 × (1 − 1/s)        maxPanY = 540 × (1 − 1/s)
```

| s | 允许的最大平移 |
|---|---|
| 1.00 | 0（不能平移） |
| 1.06 | ±54px |
| 1.08 | ±71px |
| 1.12 | ±103px |
| 1.20 | ±160px |

`camAt()` 会按此**钳制**；`validate-shot-motion.py` 用同一公式检查，请求量超预算时记 P1
（说明实际平移会被削减）。所以带平移的镜头必须自带一个能覆盖它的缩放，例如：

```json
{"intent": "pan-follow", "at": 10, "dur": 45,
 "fromX": 900, "x": 1020, "from": 1.08, "to": 1.08}   // ±60px ≤ ±71px ✅
```

推论：**纯 `still`（s=1.00）的镜头不能有任何取景偏移**（`x` 必须 = 960）。想要偏心构图，
就必须给一个 `from ≥ 1.02` 的小缩放。

### 3. anchor：出界证明

每个镜头必须额外声明一个 **`anchor`**——本镜**必须始终可见**的矩形（设计坐标，
通常就是当前解说对象的外框）。

可见窗（设计空间 1920×1080，注视点 `(x,y)`、缩放 `s`）：

```
left = x - 960/s      right  = x + 960/s
top  = y - 540/s      bottom = y + 540/s
```

证明条件：`anchor` 的四个边都落在可见窗内。

**为什么只校验关键帧就够（精确，不是近似）**：相邻关键帧之间 `x`、`y`、`s` 单调变化，
而 `left/right/top/bottom` 对 `x` 与 `s` 都单调，因此一个区间的极值必在端点取得。
所以逐关键帧校验 = 连续时间上的精确证明。脚本与运行时（`shotkit.safeCheck`）用同一套数学。

`validate-shot-motion.py` 会逐镜、逐关键帧跑这个证明，**任一越界即 P0，阻断渲染**。

### 4. 配额（防止"为了动而动"，也防止"全片不动"）

| 规则 | 判据 | 级别 |
|---|---|---|
| 每章 ≥3 次运镜（**章节 <20s 时 ≥1 次**，与 `validate-shot-motion.py` 的 `CHAPTER_LONG_SECONDS=20` 一致） | 按 `chapter` 分组统计非 `still` 的镜头数 | P0 |
| 每镜 ≤1 次运镜 | 关键帧里位移段数 | P1（>2 记 P0 级问题） |
| 单次运镜 30–45 帧 | `at + dur` | P1 |
| 全片 ≥3 种 intent（不含 `still`） | 去重计数 | P0 |
| 缓冲口令 | 入场后先停 ≥10 帧再动，运镜期间不做 Glitch | 人工 |
| **页眉 / 章节卡 / 字幕永不被运镜带动** | 它们在相机之外（屏幕空间） | 结构性保证 |

> 页眉与字幕在 `ShotCamera` 之外渲染，所以**结构上不可能被带动**——这是早期版本`CameraRig`
> 已经做对的一件事，继续保留。任何把 chrome 或字幕放进相机内的写法都是错的。

**配额来自实测教训**（参考项目 anything2explainer）：他们自己的参考片只有 2.2–2.5 次运镜/分钟、
**零次推近**，根因是旧文档写了「静态镜头为主」。所以这里把配额写成**数字**，并让门禁检查。

### 5. 怎么写

#### 5.1 分镜表里声明（唯一真源）

```json
{
  "id": "S4",
  "camera": {"intent": "pan-follow", "at": 10, "dur": 45,
             "fromX": 830, "fromY": 560, "x": 1090, "y": 540,
             "from": 1.0, "to": 1.0},
  "anchor": {"x": 300, "y": 300, "w": 1340, "h": 520}
}
```

`scripts/resolve-shots.py` 把 intent 展开成显式关键帧表，写进 `src/shots.ts`。

#### 5.2 场景里消费

```tsx
import {ShotCamera} from './shotkit';
import {SHOTS} from './shots';

<ShotCamera keys={SHOTS.S4.keys} f={localFrame} anchor={SHOTS.S4.anchor}>
  {/* 这一镜的全部内容 */}
</ShotCamera>
```

#### 5.3 手动构图（少数情况）

```tsx
import {shotCam, stillCam, camAt, camTransform, safeCheck, DEPTH} from './shotkit';

const keys = shotCam('push-in', {duration: 240, x: 980, y: 520, to: 1.12, at: 30});
const bad = safeCheck(keys, {x: 320, y: 190, w: 1280, h: 640}, 1.35); // [] 表示证明通过
```

#### 5.4 景深视差

```tsx
```

层数 ≤3、系数只用 `0.35 / 0.70 / 1.00`。**远层必须有真实内容**，不能只是同一内容的模糊缩放，
否则视差会显得廉价。远层是整幅背景时必须给 `overscan`，否则位移会露出边缘。

### 6. 向后兼容

- 没有任何 `rotY` 关键帧时走**纯 `translate + scale`** 路径；当 `s = 1.0`、`x = 960`、`y = 540` 时
  `transform` 退化为 `translate(0,0) scale(1)`，与早期版本的定焦渲染**逐像素一致**。
- 有 `rotY` 时走 3D 路径：外层 `perspective`，内层用 **CSS `zoom`** 而不是 `transform: scale`——
  因为 Chromium 会先按布局宽度光栅化 3D 复合层再用 GPU 放大，文字会糊（这条来自 video-shotcraft
  `PageCam.tsx` 的实现注释）。
- `CameraRig` 与 `CAM_KEYS_L/CAM_KEYS_P` 已删除，不要再新增全片级相机轨道：
  **取景是镜头级的，不是全片级的。**

### 7. 自检

- [ ] 每一镜都有 `anchor`，且 `validate-shot-motion.py` P0 = 0；
- [ ] 每章 ≥3 次运镜（**章节 <20s 时 ≥1 次**，与 `validate-shot-motion.py` 的 `CHAPTER_LONG_SECONDS=20` 一致），全片 ≥3 种 intent；
- [ ] 含文字的镜头 `s ≤ 1.35`；
- [ ] 运镜期间解说对象始终完整可见（门禁已证明）；
- [ ] chrome / 字幕放在 `ShotCamera` 之外；
- [ ] 视差层数 ≤3、系数只用 0.35/0.70/1.00，远层有真实内容。

<a id="camera-language"></a>

## 镜头语言：为什么动、动多少、什么时候不动

> 适用：每一条片子（手作路线必读）。配套：[camera.md#cinema-camera](camera.md#cinema-camera)（引擎能做什么、字段怎么写）、
> [camera.md#shot-language](camera.md#shot-language)（7 个 intent 与出界证明）、[director.md#director-method](director.md#director-method) 第 7 步（treatment 里写景别和理由）。
> 门禁：`validate-treatment.py` 对照 treatment 与镜头表（§2），`validate-composition.py` 查镜长（§5）。
>
> 方法来源：纪录片 / 讲解片通行的景别阶梯与剪辑连续性（公开的电影语法常识）；镜头配方卡的写法参考 video-shotcraft（Apache-2.0，只借结构，
> 不用它打包的音效）。本文是 notebook-video 自己的写法。

### 1. 先问"为什么动"——动机 → 运镜

镜头每动一次都要有一个观众能感到的理由。没有理由的漂移，等于告诉观众"这里没什么可看"。

| 动机（这一拍在发生什么） | 运镜（`cameraIntent` / 引擎字段） | 幅度参考 | 反例 |
|---|---|---|---|
| 交代：这是哪、有什么、谁和谁的关系 | `establish`（全景，可极慢漂移 `drift ≤ 0.02`） | 缩放 1.00–1.05 | 一开场就推近局部，观众不知道在看哪 |
| 顿悟 / 强调：观众理解发生变化的那一秒 | `push-in`，或 `cinema.focus` 在那一拍推近 | **≥ 12%**（招牌镜头硬要求），常用 15–30% | 6 秒推 5%：看不出在推，只像画面在"呼吸" |
| 跟随：一个东西在动（墨线在画、纸条在走） | `pan-follow` / `cinema.pan`，速度跟着运动体 | 横移 ≥ 1/6 画宽 | 运动体停了镜头还在走 |
| 把局部放回整体："原来它是这么大的一部分" | `pull-back` | 从 ≥ 1.2 拉回 ≤ 1.05 | 拉远之后没有新信息进画 |
| 揭示：遮住的部分露出来 | `reveal`（遮罩 / 移开前景）+ 镜内 `RevealMask` | — | 用淡入代替揭示 |
| 呼吸：揭示之后让观众消化 | `still`（锁定） | 0 | 每一镜都在动，没有一处停下来 |

**一句话规则**：推 = "注意这里"；拉 = "放回整体"；横移 = "跟着它"；不动 = "想一想"。

### 2. 景别阶梯：写了就要兑现

| 景别 | 观众看到 | 怎么得到 | `validate-treatment` 的判据 |
|---|---|---|---|
| 全 | 整个场景、所有关系 | 缩放 ≈ 1 | 最松处缩放 ≤ 1.05 |
| 中 | 主体 + 一圈环境 | 构图本身，或轻推 | 最松处缩放 ≤ 1.20 |
| 近 | 主体占画面一半 | 推近或构图放大 | 峰值缩放 ≥ 1.20，或主体 ≥ 1/2 画高 |
| 特写 | 一个细节填满画面 | **插入镜**（硬切到同一画面的局部重排），或大幅推近 | 插入镜（镜头表 `insert`）、峰值缩放 ≥ 1.35（纯图形 ≥ 1.5），或主体 ≥ 2/3 画高 |

- 景别变化**主要靠剪辑**（全 → 近 → 特写，一镜一个景别），不是靠在一镜里慢慢推。纪录片里的景别阶梯就是这么来的。
- 含字镜头的总缩放钳在 1.35（字会糊）；纯图形镜头可以到 1.6。要更"近"又有字：做插入镜，按特写尺寸重新排版，而不是放大。
- treatment 的 `move` 必须等于镜头表的 `cameraIntent`；`framing` 按上表对照实际缩放 / 主体占比。不一致记 P1——要么改镜头表，要么改 treatment，别让评审拿到的是"意图"。
- **招牌镜头**（`signature_shot`）的缩放变化必须 ≥ 12%（keys 的最大 / 最小缩放，或 `cinema.focus` 的 `zoom`），否则手作皮肤 P0。

### 3. 视线连续：剪辑点前后让眼睛不用找

1. **落点接起点**：上一镜结束时主体在右下，下一镜的主体从右下开始（或第一个动作发生在那里）。
2. **运动方向一致**：上一镜往右走，下一镜继续往右（横移、翻页、纸条都一样）；反向只用在"转折"。
3. **匹配剪辑**：上一镜的圆（软木塞截面）接下一镜的圆（细胞）——形状、颜色或位置相同的东西是最好的剪辑点。
4. **一次只给一个焦点**：同一时刻画面里"必须读"的东西只有一个；第二个用压暗 / 缩小 / 晚 0.5 s 出现。
5. **关系要画出来**：两个东西有关系，就用引线、箭头或同色把它们连起来；放在两边不说话，观众不会自己连。
6. **跨镜留一个物件**：上一拍的某个物件（一张纸条、一个圆、一枚印章）在下一镜继续存在，片子才连成一条线。

### 4. 什么时候不动

- 关键揭示之后 1.5–3 s：锁定，让字幕和画面被读完；
- 字幕正在出整行、且画面里有要对照着读的细节时；
- 原生动作（水彩晕开、盖章、剪刀落下）进行时：动作本身就是运动，镜头再动会抢；
- 片尾回到开头构图时：用同样的取景（只变一处），不动反而最有力。

### 5. 镜长：长短要错开

| 规则 | 判据（`validate-composition.py`，P1） |
|---|---|
| 不能像节拍器 | 镜长变异系数（标准差 / 平均）≥ 0.35；最长 / 最短 ≥ 2 倍；≤ 80% 落在同一档 |
| 要有短镜 | 至少一镜 ≤ 4 s（插入镜、重音镜头） |
| 一个构图撑太久 | 单镜 > 12 s 必须在镜内换焦点（`cinema.focus`）或接插入镜；> 10 s 提示锯开 |
| 揭示后要呼吸 | 关键揭示到下一条字幕之间留 1.5–3 s（导演自查；门禁只看前两条） |

讲解片常用的节奏：交代镜 6–9 s → 推进 / 证据 4–6 s 一镜、两三镜一组 → 顿悟镜 8–12 s（含呼吸）→ 结尾回扣 6–8 s。

### 6. 写进 treatment 的样子

```json
{"id": "S4", "framing": "特写", "move": "push-in",
 "why": "顿悟：放大镜落下后推近 25%，镜片里的盒子一间间被刷成房间；推完锁定 2 s 呼吸"}
```
镜头表对应：`"camera": {"intent": "push-in", "from": 1.0, "to": 1.25, …}` 或 `cinema.focus: [{"beat": 2, "zoom": 1.25, "hold": 60}]`。

<a id="cinema-camera"></a>

## 引擎虚拟镜头（`src/cinema.tsx`）

> **何时读**：写分镜表之前。它决定这部片「像电影还是像 PPT」。
> 场景自己的 `ShotCamera`（[camera.md#shot-language](camera.md#shot-language)）仍然在；本层套在它**外面**，由引擎（`index.tsx` 的 `FinalDemo` / `Backdrop`）统一驱动。分镜表什么都不写也有缺省运动。

### 1. 为什么要有这一层

没有虚拟镜头时每一镜是「静止舞台 + 卡片依次出现」：即使 `ShotCamera` 推了 3%，观众感受仍是翻幻灯片。
引擎给每一镜套一台虚拟摄影机，并且把「内容太小」「镜头不跟讲解」「换镜硬切」这三类 PPT 感的来源变成默认行为与门禁。

### 2. 六个能力（全部是帧的纯函数）

| 能力 | 缺省 | 分镜表写法 | 说明 |
|---|---|---|---|
| **fit** 内容自动放大 | `auto` | `cinema.fit: "auto" \| "none"` | anchor 占内容带（安全区）面积 < 60% 时，整镜按 anchor 中心推近到 72%；上限：anchor 放大后仍在内容带内、≤ 1.30、与场景缩放相乘 ≤ 1.35。`resolve-shots.py` 预算成 `cinema.fit = {x, y, s, fill, fillAfter}`。 |
| **drift** 缓推 / 漂移 | `auto`（4.5%） | `cinema.drift: "auto" \| "none" \| 0–0.08` | 每镜一次慢推，镜与镜之间轮换：正推 → 右移推 → 拉 → 左移推（不会全片同一种推）。 |
| **focus** 讲到哪推到哪 | 无 | `cinema.focus: [{beat \| cue \| at, region \| x,y,w,h, zoom?, hold?}]` | 第 N 拍开始，弹簧曲线（20 帧）推近该区域，停 `hold` 帧（缺省 60）后 24 帧缓拉回；相邻焦点首尾相接时直接从一个**横摇**到下一个。`region` 简写：`left/right/top/bottom/center/top-left/…`（按本镜 `contentBand` 切）。<br>**不切字**：`slide: false` 关掉横向滑回；`keep: {x,y,w,h} \| region` = 推近时也必须完整入画的矩形（例如推近右侧终端时左侧的大数字），引擎把推近倍数降到能装下「焦点 ∪ keep」（留 28 px 边距，不低于 1.1，装不下就忽略 keep）。`hero-number` 版式缺省 `keep` = anchor + 8% 字号的字形外溢余量；`keep: false` 关掉。镜头里有 MediaFrame 卡片又要推近别处时，给卡片写 `keep`，否则卡片会被推出画面一半。 |
| **pan** 宽画布横摇 | 无 | `cinema.pan: {worldW: 2800, beat? \| at?, dur?, dir?: "ltr" \| "rtl"}` | 场景按更宽的世界排版，摄影机横摇扫过（时间线、长链路）。 |
| **transition** 换镜 | `auto` | 镜级 `transition` | `auto` = 章节首镜 **zoom**（推穿：上一镜放大淡出、新镜从远处推来）、其余 **whip**（甩镜：水平方向模糊 + 位移，左右交替）；也可写 `whip / whip-left / whip-right / zoom / fade / hard`，手作皮肤另有 `slide / drop` 与真卷页 `pageturn / peel`（[camera.md#fx-effects](camera.md#fx-effects)；渲染器探针不通过时退回 `slide / drop`）。`cut / handoff / reveal` 是旧写法，引擎按 `auto` 处理。转场 14 帧（卷页 22 帧）。 |
| **parallax** 视差 | 开 | — | 背景按 0.3 的系数跟随摄影机（背景动得比内容少 → 纵深），预放大 1.06 保证不露边；甩镜时背景一起甩。 |

纪律：无随机、无状态、无实时动画库；同一帧渲两次结果相同。总缩放（场景 × 引擎）钳在 `TEXT_ZOOM_MAX = 1.35`，取景窗永远落在 1920×1080 舞台（或 pan 世界）之内。

### 3. 怎么写一镜

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

### 4. 内容要大（60–80% 安全区）

- 代码镜头：`HighlightCode fontSize={34–40}`；差异镜头：`DiffView fontSize={26–32}`；控制台是主角时 `ConsoleWindow fontSize={28–34}`。
- 关键数字：`KineticNumber`（`src/cinema.tsx`）——计数（ease-out）+ 落定瞬间放大 1.18 回弹 + 下划线扫入；字号 200–380。用在「讲到这个数」的那一拍。
- `validate-shot-motion.py` 复核每镜 `fillAfter`（实测常量 `FIT_P0, FIT_LO, FIT_HI_WARN = 0.45, 0.60, 0.90`）：< 45% → **P0**（引擎推到上限仍太小，内容本身画小了；`statement / define / quiz / list / custom` 这几种"文字为主"的版式留白是有意的，降为 P1，提示加大字号或补副标题）；45–60% → P1；> 90% → P1（太满，或 anchor 写得比内容大）。**目标是 60–80%。**

### 5. 相邻镜头换布局

分镜表可写 `layout`（自由命名的版式：`hero-number / chart-number / code-full / diff-split / rail / ring-tree / chart-metric / hero-verdict …`）。
`validate-composition.py`：相邻两镜都写了 `layout` 且相同 → **P0**。骨架不同但版式一样，观众照样读作「同一页换了字」。

### 6. 门禁口径

| 门禁 | 查什么 |
|---|---|
| `resolve-shots.py` | `cinema.drift / fit / focus / pan` 与 `transition` 取值；focus 的 beat 越界；region 名 |
| `validate-shot-motion.py` | `fillAfter` 目标 60–80%（<45% P0，文字为主版式降 P1；45–60% P1；>90% P1）；focus zoom × 场景缩放 ≤ 1.35；焦点矩形放大后放得进画面；focus.at 在本镜内；缺 cinema 块（旧解析结果）→ P1 |
| `validate-composition.py` | 转场闭合集合（`auto/cut/handoff/reveal/whip/whip-left/whip-right/zoom/fade/hard/slide/drop/pageturn/peel`）；相邻 `layout` 不同 |
| 渲染期 | 转场期间新旧两镜都挂载，带 `data-gate-allow="handoff"`，重叠门禁对这 14 帧（卷页 22 帧）放行 |

<a id="fx-effects"></a>

## 真翻页 / 揭纸转场（`@remotion/effects`）

> 手作皮肤的「翻到下一页」不再是镜头横移，而是一页纸真的卷起来翻走：卷曲、折痕高光、纸背透出上一页的墨迹。
> The hand-made skins now turn a real page: the old page curls away with a shaded fold and its back showing through, instead of a camera pan.

### 1. 用法

| 转场 | 画面 | 缺省用在 | 探针不通过时退回 |
|---|---|---|---|
| `pageturn` | 近乎竖直的折线（-78°，下角领先），整页从右往左翻走 | **所有皮肤的缺省**（`auto`） | `pageflip`（纯 CSS 折痕翻页） |
| `peel` | 对角折线（315°），从右下角往左上角揭起 | `papercut` 的 `auto` | `drop`（新纸落下） |

- **翻页是缺省。** 分镜表写 `auto`（或不写、或整个 story 不写 `transition`）就是翻页——这是「笔记本影片」的基本语法，不该由每部片、每套皮肤重新决定。显式写 `"transition": "pageturn"` / `"peel"` 也可以（任何皮肤都行）。
- 章节首镜也翻页：翻到新一章和翻到下一页是同一个动作，中途插一个 `zoom` / `drop` 会把观众从本子里拽出来。
- 卷页时长 22 帧（`CURL_FRAMES`，0.73 s，手翻的速度）；`pageflip` 同为 22 帧；其余转场仍是 14 帧。
- 卷走的是上一镜的**整页**：背景（按上一镜末帧的视差位置）+ 内容；新的一页在下面不动，背景不交叉淡化。页眉、章节卡、字幕在纸面之上，不跟着卷。
- 几何（`src/fx.tsx` 的 `curlParams`）是进度 p 的纯函数，pageTurn 本身无随机：同一帧渲两次结果相同。

### 2. 探针

`pageTurn()` 走 **WebGL2 + HTML-in-canvas**（Remotion ≥ 4.0.540）。Remotion 缺省的 Chrome Headless Shell 就能画：无显卡的 Linux 上走软件 ANGLE（缺省 GL 设置或 `--gl=swangle`）；`--gl=angle` 在没有显卡的机器上拿不到 WebGL2，pageTurn 报 `No supported implementation for effect "remotion/page-turn"`。实测（2 核 arm64、无 GPU 的 Linux 容器，Remotion 4.0.543）：探针通过；60 帧 2560×1440、concurrency 2，开卷页 26 s、不开 25 s——卷页不额外花时间，整片同一个浏览器、同样的并发一遍渲完。

没有 WebGL2 的浏览器会让 pageTurn 直接抛错，所以仍然先真画一张、读像素。`scripts/fx-browser.mjs` 做这件事：

1. 本片没用到 `pageturn` / `peel`（分镜表 + 当前皮肤）→ 不探测，什么都不变。
2. 用与成片相同的浏览器渲 `NotebookVideoFxProbe`（320×180：红页卷走一半露出蓝底）一帧，读像素：左红右蓝才算通过。结论连同 Remotion 版本、平台写进 `renders/.fx-probe.json`，键不变就不重探。
3. 通过 → 成片渲染传 `{nvFx: 'on'}`；不通过 → 不传，合成里 `pageturn → pageflip`、`peel → drop`，片子照出，**仍然是翻页**，make-video 报告里记一条 **P1 卷页降级** 并写明原因。
4. 探针有 90 秒上限（`FX_PROBE_TIMEOUT_MS`），到点就杀，按失败处理。

```bash
node scripts/notebook-video.mjs fx-probe <工程> [--force]   # 单独探测，打印 JSON
NOTEBOOK_VIDEO_FX=off node scripts/notebook-video.mjs render <工程> out.mp4   # 手动关掉
```

Studio 预览与普通 `remotion still` 缺省没有 `nvFx`，看到的是退回后的 **pageflip 折痕翻页**（不是横移）；要看卷页，以 `--props='{"nvFx":"on"}'` 启动。

### 3. 卷页帧窗

`render` 不需要单独处理卷页帧：整片一遍渲完。帧窗只用于排查和单独看一眼。

**窗口从哪来**：`manifests/shots.resolved.json`（`resolve-shots` 的产物）→ `scripts/transition-plan.mjs`
按 `cinema.tsx` 的 `resolveTransition` 规则逐镜判定"哪种转场"→ 卷页的镜取 `[from, from+21]`。
`src/shots.ts` 是生成物，只在旧工程没有 manifest 时兜底（那时会打一行 warn 说明走的是旧路径）。

排查用：`node scripts/transition-plan.mjs <工程>` 打印每镜声明值、实际生效的转场、以及最终窗口。

#### 单独看一眼卷页，别渲整片

```bash
node scripts/notebook-video.mjs preview <工程> --from=3.4 --seconds=1.2 --scale=0.5 --fx=on
```

`--from` 取「跨镜边界前一秒」，边界在 `manifests/shots.resolved.json` 的 `from` 里；`--seconds` 收小数。

### 4. `fractalNoise()` 评估结论：不默认开

`fractalNoise()`（WebGL2）可以做「纸纹的动态层」。实测：

- Headless Shell + `--gl=swangle`（Remotion 4.0.539 实测）：2560×1440 全分辨率 ≈ 3.2 s/帧（30 帧 103 s）——整片叠一层要多 1.5 小时以上；
- 观感：纸本身不会动，逐帧演化的云纹在亮底上像「沸腾的纸」，盖过了墨线和水彩的手作感。1/4 分辨率 + 每 5 帧跳一次（6 fps 手绘抖动）便宜很多，但仍需要 `--gl=swangle` 整片渲染。

结论：现有的静态纤维纹理（`public/craft/fibre-tile.png`）+ 背景库里 Paper Shaders 离线预渲的纸纹，已经比动态噪声好且零运行时成本。`fractalNoise` 只作为**离线**生成静态纹理的候选（维护者工具里渲一次存成位图，与处理 Paper Shaders 的方式相同），不进渲染期。

### 5. 许可

`@remotion/effects` 与 `remotion` 同属 Remotion 仓库，受 Remotion License 约束（npm 元数据写作 `UNLICENSED`，与已依赖的 `@remotion/transitions` 相同；以仓库根 `LICENSE.md` 为准）。其中 Fractal Noise 等着色器改编自 EffectCraft（MIT），见包内 `THIRD_PARTY_LICENSES.md`。本仓库不分发这些包，由 `npm ci` 安装。详见 `DEPENDENCIES.md`、`NOTICE`。
