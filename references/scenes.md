# 镜头表与场景：骨架、手写场景、独立部件、画布与配方

镜头表与场景怎么写：骨架、手写场景（scenes.tsx / src/custom/）、独立部件、版面组织、画布和线稿配方。

本篇各节：

- [场景骨架与分镜表](#scene-skeletons)
- [场景编写说明书（照着抄，不要重新发明）](#scene-authoring)
- [手写场景路线（完整作者手册）](#handwritten-scenes)
- [Independent components and layer contracts](#independent-parts)
- [Lecture composition: the default multi-zone visual route](#lecture-composition)
- [Canvas: 16:9 only](#canvas-modes)
- [七个线稿配方（`recipe`）· 降级为可选](#recipes)
- [Official exemplar](#official-skills-exemplar)

<a id="scene-skeletons"></a>

## 场景骨架与分镜表

> 状态：**生效**。落地件：`assets/lecture-template/src/stagekit.tsx`（Stage）、
> `skeletons.tsx`（Corridor / Split / Zoom）；门禁：`scripts/validate-composition.py`。

### 目录

- [1. 要解决的问题](#1-要解决的问题)
- [2. 四种骨架](#2-四种骨架)
- [3. Stage 的写法](#3-stage-的写法活体主体)
- [3.5 时序铁律：讲到哪，出现到哪](#35-时序铁律讲到哪出现到哪)
- [4. 分镜表](#4-分镜表唯一真源)
- [5. 添加新骨架的门槛](#5-添加新骨架的门槛)

### 1. 要解决的问题

场景**结构同构**（`Paper` + 标题 + 编号列表 + 底部贴标，逐镜只换字）= 一串 PPT 页；根因是模板只给了一种结构。
解法不是堆镜头卡（维护债 >> 收益），而是**四种构图本来就不同的骨架**。

### 2. 四种骨架

| 骨架 | 结构 | 适用内容 | 实现 |
|---|---|---|---|
| **Stage** | 单体舞台：一个主体在空间中演化 3–6 个状态 | 机制、概念、控制台、设备界面 | `stagekit.StageFrame` |
| **Corridor** | 走廊：一个持久对象沿共享轨道穿过若干站点，留下完成态 | 流程、状态转移、时间窗口 | `skeletons.Corridor` |
| **Split** | 双栏对比：两侧各自入场，差异侧高亮 | 对比、优劣、before/after、取舍 | `skeletons.SplitStage` |
| **Zoom** | 整体 → 聚焦 → 标注 → 回整体（**纯代码局部放大，不是图片**） | 证据、细节、界面、等式 | `skeletons.ZoomStage` |

**硬约束（门禁 P0）**：

- **相邻场景不得同骨架**；
- **全片 ≥3 种骨架**。

这两条直接杀掉"四个场景长一样"。

### 3. Stage 的写法（活体主体）

四条标准：

1. **占主体**：16:9 下 ≥1024×620 设计像素，或占画幅宽 ≥60%；
2. **有状态机**：≥3 拍（长度 ≥12s 时 ≥5 拍），每拍 2–4 秒，**全程同一实例不卸载**；
3. **能装东西**：`header` / `main` / `rail` / `stamp` 四个命名槽。
4. **把 main 槽填满**：`main` 槽拿走的是 `h − pad×2 − header − stamp` 之后的**全部剩余高度**，
   所以槽里的内容要自己撑满它——外层给 `height:'100%'`，内部再按 `mainH` 分栏或按拍数分块，
   **不要只放一行标题**（槽给足了、内容只有一行，读成「一张空纸 + 一行标题」）。占用目标 ≥60%，
   `SlotGuard` 在出图路径上把占用率打进日志（<35% 出声），拿这个数字自查，别目测。

```tsx
const phases = [
  {at: b0, state: 'ingress', label: '请求进入'},
  {at: b1, state: 'policy',  label: '命中新政策'},
  {at: b2, state: 'verdict', label: '按 Flash 结算'},
];

<StageFrame x={200} y={190} w={1520} h={700} f={f} phases={phases} railW={400}
  header={() => <PillTag text="DS 路由调整" />}
  rail={({index}) => <PhaseRail phases={phases} ctx={...} />}
  stamp={() => <StampBanner x={0} y={0} w={1010} f={f} at={b2} text="过渡期内按 Flash 计费" />}
>
  {({index}) => <ConsoleWindow x={0} y={0} w={1010} f={f} rows={rowsFor(index)} />}
</StageFrame>
```

**坐标语义**：槽内是**框内相对坐标**（`x=0` 即槽左上角）；只有直接放在场景根下才是舞台坐标。
`StageFrame` 的 header / stamp 槽已设为定位祖先，槽内绝对定位构件不会跑到框外。

**为什么状态机是关键**：它把「按句子换状态」这件事从"手算几十个魔法帧号"降到"每句台词一个帧号"。
`useStageMachine(phases, f)` 返回 `{index, phase, prev, local, t, span, nextAt, entering}`。

**`PhaseRail` 要把状态机显式画出来**——观众能看见主体在推进，这是"主线演化"和"卡片轮播"在观感上的分水岭。

**"附着信息"用贴标做**（`PillTag` / `StampBanner` / `Callout`）：原本要新开一张说明卡的，改成挂在主体附近的贴标。
只有"主体装不下的、且与主体无物理关系的信息"才允许独立成卡。

### 3.5 时序铁律：讲到哪，出现到哪

**元素出现帧必须绑定到"讲到它的那一句"**，即 `SHOTS.Sx.beats` 里的某个节拍。
禁止在镜头开头把一屏元素一次性铺完——那会让画面比旁白跑得快，观众看到的是"已经讲完了"。

```tsx
const b = SHOTS.S6.beats;                       // cue 推导出的本地节拍帧
const at = (i: number, d = 0) => (b[i] ?? 0) + d;

<框架   style={enterAt(f, at(0))} />            // 框架在本镜首句出现
<元素   style={enterAt(f, at(1))} />            // 第 2 句讲到的元素，第 2 拍才出现
items.map((x, i) => <项 style={enterAt(f, at(2) + i * 12)} />)  // 同句内相邻至少隔 12 帧
```

**出现统一用 `enterAt()`**：是左→右展开 22 帧（线性），不淡入、不上浮、不缩放。
不要每个元素各写一套曲线。同一句内相邻元素开始出现至少隔 12 帧，同一时刻最多 2 个在长；
跨句的元素**必须**跨拍出现。整镜末尾留 18 帧干净淡出。规则全文见 [draftpaper.md#reveal-rules](draftpaper.md#reveal-rules)。

自检：随手暂停任意一帧，画面里出现的元素**不应该超出旁白已经讲到的东西**。

### 4. 分镜表（唯一真源）

`manifests/shots.json` 是**语义层**分镜表：**不写绝对帧号**，只声明"这一镜覆盖哪几句 cue"。

```json
{
  "duration": 3867,
  "theme": "cel",
  "shots": [{
    "id": "S4",
    "chapter": "一次请求的旅程",
    "skeleton": "Corridor",
    "cues": [12, 16],
    "media": ["graphic", "console"],
    "live": ["StaggerList", "Checklist"],
    "camera": {"intent": "pan-follow", "at": 10, "dur": 45, "fromX": 830, "x": 1090, "y": 540},
    "anchor": {"x": 300, "y": 300, "w": 1340, "h": 520},
    "contentBand": {"x": 120, "y": 240, "w": 1680, "h": 660},
    "hero": {"name": "请求包", "size": 124, "kind": "text"},
    "zones": 4,
    "bottomFill": true,
    "cover": "paper",
    "transition": "handoff",
    "entry": "rise",
    "beats": [{"cue": 12}, {"cue": 13}, {"cue": 16}]
  }]
}
```

字段含义：

| 字段 | 作用 | 谁检查 |
|---|---|---|
| `cues` | 覆盖的 cue 索引闭区间 → 推导 `from/to` | `resolve-shots` |
| `skeleton` / `media` / `live` | 骨架、视觉介质、活性组件 | `validate-composition` |
| `camera` / `anchor` | 镜头配方与必须可见矩形 | `validate-shot-motion` |
| `chapter` | 章节归属（运镜配额按章统计） | `validate-shot-motion` |
| `zones` | 功能分区数（3–5） | `validate-composition` |
| `bottomFill` | 下 1/4 密度的**声明位**：`validate-composition` 只查这个字段**在不在**（缺字段=配置错误）；**"到底填满了没有"由渲染期 `FillGate` 实测**（信息元素最低边 vs y=876）；为什么不按值判见 [checks.md#composition-gate](checks.md#composition-gate) 的 P0-4 降级说明 | `FillGate`（渲染期） |
| `contentBand` / `cover` | 内容带与背景装饰区的关系 | `validate-shot-motion` |
| `transition` / `entry` | 转场与入场方式（多样性） | `validate-composition` |
| `beats` | 状态变化帧（节奏判据） | `validate-composition` |

#### 解析流程

```
python scripts/resolve-shots.py PROJECT_DIR
  → 写 src/shots.ts（含已展开的相机关键帧 keys）与 manifests/shots.resolved.json
  → 校验：时间轴连续、无断档重叠、覆盖 = duration、cue 索引在范围内
```

**边界规则**：`from` = 本镜首句 cue 的起始帧；`to` = **下一镜首句的起始帧**（末镜 = 末句结束 + `tail`）。
由构造保证连续。改一句台词 → 改 `narration.txt` 与语义字幕行 → 重跑 `resolve-shots`，所有帧号（含音效钉帧）自动跟着走，不手改帧号。

### 4.5 版式 `layout`

骨架管「机制怎么演」，版式管「这一页长什么样」。分镜表每镜可写 `layout`（自由命名，如 `hero-number`、`chart-number`、
`code-full`、`diff-split`、`rail`、`ring-tree`、`chart-metric`、`hero-verdict`）。相邻两镜都写了且相同 → `validate-composition.py` P0。
建议每镜都写，逼自己想清楚这一镜和上一镜哪里不一样。镜头怎么动见 [camera.md#cinema-camera](camera.md#cinema-camera)。

### 5. 添加新骨架的门槛

新骨架必须：

1. 构图与现有四种**明显不同**（同构图不算新骨架）；
2. 在 `skeletons.tsx` 的 `SKELETONS` 里注册，并同步 `validate-composition.py` 的 `SKELETONS`（`validate-skill-consistency.py` 交叉校验两处，忘同步会红）；
3. 有「何时用 / 何时不用」的判据，写进本文件的表格；
4. 在 `NotebookVideoShowcase` 的接触表里出现（让后续 AI 看得见）。

**不要**为了题材加一次性骨架——一次性效果留在该片的场景文件里。

<a id="scene-authoring"></a>

## 场景编写说明书（照着抄，不要重新发明）

> 给**执行 AI**：模板是最好成片的结构沉淀，后续任何（含较弱的）AI 照抄才能收敛到同一水平，
> 所以**模板里的代码形状就是标准答案**——**结构别动，只换内容**，不自由发挥。需要换结构时，先读
> [scenes.md#scene-skeletons](scenes.md#scene-skeletons) 与 [checks.md#composition-gate](checks.md#composition-gate)。

---

### 目录

- [0. 六步流程（顺序不要跳）](#0-六步流程顺序不要跳)
- [1. 分镜表长什么样](#1-分镜表长什么样可直接改造)
- [2. 场景代码的标准形状](#2-场景代码的标准形状照抄)
- [3. 十二个坑](#3-十二个坑)
- [4. 渲染前自检](#4-渲染前自检逐条打勾)
- [5. 想做得更好时的顺序](#5-想做得更好时的顺序)

### 0. 六步流程（顺序不要跳）

```text
① 锁内容      narration.txt + manifests/semantic-caption-lines.txt（一行为一条 cue）
② 写分镜表    manifests/shots.json（语义层：只写"覆盖哪几句 cue"，不写帧号）
③ 解析        python scripts/resolve-shots.py PROJECT       → src/shots.ts + shots.resolved.json
④ 写场景      src/scenes.tsx（每个 shot 一个组件；照 §2 的代码形状）
⑤ 过门禁      validate-shot-motion.py / validate-composition.py（P0 必须为 0）
⑥ 出片复核    render → 抽 1fps 接触表 → 逐帧看边界/最长字幕/最复杂运动
```

②之前的输入是③；④依赖③生成的 `SHOTS`；⑤必须在⑥之前。**顺序错了会白干。**

---

### 1. 分镜表长什么样（可直接改造）

```json
{
  "duration": 1126, "theme": "flat", "canvas": "16:9",
  "shots": [
    {
      "id": "S1",
      "chapter": "代码不再孤独",
      "skeleton": "Stage",
      "cues": [0, 3],
      "media": ["console", "graphic"],
      "live": ["ConsoleWindow", "StampBanner"],
      "camera": {"intent": "establish", "at": 24, "dur": 38, "x": 960, "y": 540, "from": 1.0, "to": 1.03},
      "anchor": {"x": 340, "y": 180, "w": 1240, "h": 660},
      "contentBand": {"x": 180, "y": 120, "w": 1560, "h": 800},
      "hero": {"name": "本地仓库", "size": 640, "kind": "text"},
      "zones": 4, "bottomFill": true, "cover": "paper",
      "transition": "cut", "entry": "rise",
      "beats": [{"cue": 0}, {"cue": 1}, {"cue": 2}, {"cue": 3}]
    }
  ]
}
```

- `cues: [起, 止]` 是**闭区间**；`from/to` 的边界规则见 [§4](#4-分镜表唯一真源)。
- **禁止**在分镜表里手写帧号。**禁止**手改 `src/shots.ts`（它带 AUTO-GENERATED 头）。
- `beats` 覆盖每一句的起始帧即可；若某段超过 110 帧没有变化，解析器会提醒你补拍。

---

### 2. 场景代码的标准形状（照抄）

```tsx
import {SHOTS} from './shots';
import {ShotCamera, CoverPanel} from './shotkit';
import {StageFrame, PhaseRail} from './stagekit';
import {Easing, interpolate} from 'remotion';

const C = THEME.palette;
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const IN = 22;
/** 出现（草稿纸）：左→右展开 22 帧，线性；不淡入、不上浮、不缩放。所有元素统一用它。见 references/draftpaper.md#reveal-rules */
const enterAt = (f: number, at: number): React.CSSProperties => {
  const p = interpolate(f, [at, at + IN], [0, 1], {...clamp, easing: Easing.linear});
  if (p <= 0) return {opacity: 0};
  return {clipPath: `inset(-4% ${((1 - p) * 100).toFixed(2)}% -4% -2%)`};
};

const S1: React.FC<{f: number}> = ({f}) => {
  const b = SHOTS.S1.beats;
  const at = (i: number, d = 0) => (b[Math.min(i, b.length - 1)] ?? 0) + d;
  const phases = [
    {at: at(0), state: 'local', label: '代码躺在硬盘里'},
    {at: at(1), state: 'push',  label: '接上 GitHub'},
    {at: at(2), state: 'world', label: '全世界一起造'},
  ];
  return (
    <Shot id="S1" f={f} entry="rise">
      <StageFrame x={210} y={176} w={1500} h={710} f={f} phases={phases} railW={390}
        header={() => <span>…</span>}
        rail={({index}) => <PhaseRail phases={phases} ctx={…} />}
        stamp={() => <StampBanner x={0} y={0} w={1000} f={f} at={at(2)} text="…" />}>
        {() => (
          <div style={{position: 'relative', height: '100%'}}>
            <ConsoleWindow x={0} y={0} w={1000} h={300} f={f} rows={rows} rowGap={62} />
            <div style={{position: 'absolute', left: 0, top: 372, display: 'flex', gap: 14}}>
              {chips.map((x) => <div key={x.k} style={{…, ...enterAt(f, x.at)}}>…</div>)}
            </div>
          </div>
        )}
      </StageFrame>
    </Shot>
  );
};
```

四个骨架的组件（`StageFrame` / `Corridor` / `SplitStage` / `ZoomStage`）与介质组件
（`ConsoleWindow` / `MetricGrid` / `StampBanner` / fxkit 的 9 件）都已提供。
**先用现成的，缺什么再补；补的要加进接触表。**

#### 槽宽公式（给槽内组件传宽度前先算）

```
mainW = w − pad×2 − (rail ? railW + 18 : 0)
mainH = h − pad×2 − headH − stampH − (stamp ? 14 : 0) − (header ? 14 : 0)
```

`StageFrame` 算好这两个值，`SlotGuard` 在**出图路径**上实测 main 槽**占用率**（槽内有内容的最内层元素高度并集 ÷ 槽高），
<35% 在控制台警告并报出 `mainW×mainH`。两件事都要做：① 给 `ConsoleWindow` / `SkeletonCard` / `MetricGrid` 传 `w` 前**先算 `mainW`**，
不凭感觉写整数；② 内容**撑满 `mainH`**，不要只放一行字——见 [§3 第 4 条](#3-stage-的写法活体主体)。

#### 三个必须遵守的写法

1. **元素出现帧绑到节拍**：`enterAt(f, at(i))`，不要用 `popS(f, 0)` 或镜头开头的固定帧。
2. **容器里不要混用**"文档流内的标题"和"绝对定位组件"——两者都从容器原点起，会精确重叠。
   给绝对定位组件显式 `y`，或把标题也绝对定位。
3. **不铺整幅底托**（见 [media.md#media-routing](media.md#media-routing) §4.2）：背景中央本就是安全区；
   局部底托若用 `tone='wash'`，必须 `z={-1}`、`boxShadow:'none'`、径向渐变。正 z 会把整镜内容压成半透明。

---

### 3. 十二个坑

| # | 症状 | 真因 | 修法 |
|---|---|---|---|
| 1 | `tsc` 报 `Property 'frame' is missing` / `Property 'f' does not exist` | 给 **fxkit** 组件传了 `f`（它的参数叫 `frame`），或反过来 | fxkit 传 `frame={f}`；其它模块传 `f={f}`；帧参数是必填类型，tsc 会报错 |
| 2 | 镜头一动，边缘内容被裁掉 | 平移会整层移动内容，`s=1.0` 时必然露边 | 平移量须由缩放覆盖：`maxPanX=960(1−1/s)`；`pan-follow` 自带 `from≥1.06` |
| 3 | 一屏字叠成一团 | 文档流标题 + 绝对定位组件都从容器原点起 | 给组件显式 `y`，或把标题绝对定位 |
| 4 | 整镜内容发灰/半透明 | 底托用了**正 z-index**，压住所有 `z-index:auto` 的场景元素 | 底托 `z={-1}` |
| 5 | 画面下沿一条硬缝 | 底托是硬边矩形 | 径向羽化 + 去掉描边环 |
| 6 | 字幕被裁切 | 字幕超出安全宽 | `CaptionFitGate` 按当前画布与主题的真实字号/安全宽实测并拦下；照报错改字幕 |
| 7 | **给槽内组件传的宽度超过了槽的可用宽**，不透明组件压住右侧轨道文字 | 没算 `mainW = w − pad×2 − railW − 18`，凭感觉写 `w=1060` 而实际只有 1035 | 先算 `mainW/mainH` 再传宽度；`StageFrame` 内建 `SlotGuard` 会在控制台警告超宽（见 §2 下方） |
| 8 | 两个不同信息互相压字（门禁报 `OverlapGate`） | 真的重叠 | 按 §4 自检逐条修；**只有**"同一信息在同位置替换"和"镜头交接"才允许用 `data-gate-allow` 白名单 |
| 9 | **多张卡片精确叠在同一点**，文字互相穿刺 | flex 子项**只含绝对定位子元素**时没有在流内容，宽度塌成 0 → 四张 248px 宽的卡被 `gap:20` 排到 x=0/20/40/60 | 给这类 wrapper **显式 `width` + `height`**，或不要包一层、直接把宽高给卡片本身；`OverlapGate` 会报这种重叠 |
| 10 | 卡片最后一行被裁掉一截 | `FitCard` 的高度是手写的，比内容矮，叠加 `overflow:hidden` 后文字被切 | 高度用 `fitH(rows, padTop, padBottom)` 算；渲染期 `CardFitGate` 用 `scrollHeight > clientHeight` 拦真裁切（容差 6px，吸收行盒取整） |
| 11 | **场景标题/顶层卡片与左上角章节卡撞车** | 全局 `Chrome` 章节卡占用 `x: 92..484, y: 74..164`；独立元素写在 `top: 100~140` 发生物理重叠 | 场景标题放入 `StageFrame` 内由槽统一管理，或独立元素保持 `y >= 170`；`coords-lint.py` 会对 `y < 170` 报警 |
| 12 | **卡片/文字满屏瞬间全出，退化成 PPT** | 场景内多个子项、对比条或对话的 `start` 全部写死为 `0` 或同一帧 | **台词节拍阶梯涌现（铁律）**：必须强绑定 `beats`（`start={at(i)}`），随旁白语流逐项点亮与打字吐字 |

---

### 4. 渲染前自检（逐条打勾）

- [ ] `resolve-shots.py` 通过（时间轴连续、覆盖 = duration）
- [ ] `validate-shot-motion.py` **P0 = 0**（含每镜 anchor 出界证明、平移预算）
- [ ] `validate-composition.py` **P0 = 0**（骨架相邻不同款、活性组件覆盖、介质 ≥3 种、下 1/4 填满）
- [ ] 一镜内**没有元素在它该出现的那句之前出现**
- [ ] 章节卡 / 页眉 / 字幕都在 `ShotCamera` **之外**
- [ ] 压到背景装饰区的内容坐在底托上；底托是负 z + 羽化
- [ ] 用到的每个构件都在 `NotebookVideoShowcase` 接触表里出现过
- [ ] **首次渲染后读一遍控制台**：`OverlapGate`（文字重叠/遮挡）与 `SlotGuard`（槽内溢出）的警告必须清空，或逐条确认是"有意覆盖"并补上 `data-gate-allow`
- [ ] 进度类动画用 `scaleX`，数值类用 `tabular-nums`（见 draftpaper.md#motion-design 六律）

---

### 5. 想做得更好时的顺序

先改**内容层的表达**（换介质、换骨架、把一屏元素拆成逐句出现），
再改**参数**（时间、位移、缩放、颜色），**最后**才考虑动引擎。
**不要**为了"更炫"加新组件——本技能的失效模式从来不是组件不够，而是没被用上、或结构同构。

<a id="handwritten-scenes"></a>

## 手写场景路线（完整作者手册）

> **默认路线是 story.json + `make-video.mjs`**（见 SKILL.md）。本页是逃生舱：给要逐镜手调、手写 `scenes.tsx` 的工程：
> 引擎、门禁、主题都通用；只是排版、关键词同步、相机路径要自己写。


## Create notebook explainer videos

Build a finished, validated MP4 **and** an editable Remotion project. This is a low-freedom production
system, not a visual prompt: Remotion is the only renderer, the **composition and its data** are authored
in code, and every animation is a pure function of the frame number. The established style must be
reproducible by any AI in any environment — no image-generation model required.

**"No model dependency" bans paid generative models** (pay per call, a different picture every time), **not
open-source libraries**: reuse free, lock-file-pinned React packages and the wrapped layer in `src/components/`
before writing new SVG — see [technique.md#dependency-policy](technique.md#dependency-policy).

**The film must not look like a slide deck.** That is enforced structurally and by gates, not by taste:
four different scene skeletons with no adjacent repeats, at least three visual media per film, at least
one live state-changing component per explanation scene, and a camera that really moves. See
[scenes.md#scene-skeletons](scenes.md#scene-skeletons), [media.md#media-routing](media.md#media-routing)
and [camera.md#shot-language](camera.md#shot-language).

### Reference files（按需加载参考 · 读取时机如下）

Read only what the current production needs：按下面每条标注的时机读，不要一次全读。「先读」几份只在写手写场景（逃生舱）时需要；走主路线（story.json + 蓝图）不用读。

**读取时机说明**：每条开头的加粗词就是读取时机 —— 「先读」= 动手前读；「必读」= 这一步不做完不许往下走；
「照抄」= 直接复用其代码形状；「逐条对照」= 完成后一条条核对；「何时读」= 满足该条件时才读；「仅当」= 只有该前提成立才读。

**先读** [references/locked-style-contract.json](locked-style-contract.json) — binding tokens、坐标与 rejection flags.
**先读** [references/technique.md#dependency-policy](technique.md#dependency-policy) — 依赖边界（什么能引、什么不能引）、已内置清单、组件纪律与「加一件＝换掉一件」的增长纪律（合规判据是「零引用」，不是一个拍脑袋的总数）。**动任何库或组件之前读这一份。**
**照抄** [references/scenes.md#scene-authoring](scenes.md#scene-authoring) — 场景代码的标准形状与八个坑；不要重新发明。
**照抄** [references/scenes.md#scene-skeletons](scenes.md#scene-skeletons) — 四种骨架与分镜表结构（写分镜表前必读）。
**先读** [references/media.md#media-routing](media.md#media-routing) — 内容→介质路由、**§5.1 组件权威索引（53 件逐件，选型只查这一处）**、A/B 场景、背景可读性契约。
**先读** [references/camera.md#shot-language](camera.md#shot-language) — 六个运镜意图（+ `still` = 合法取值 7 个）、缩放预算、anchor 出界证明、平移预算。
**先读** [references/camera.md#cinema-camera](camera.md#cinema-camera) — 引擎虚拟镜头：缺省缓推、`cinema.focus` 讲到哪推到哪、横摇、甩镜 / 推穿转场、视差、内容自动放大到安全区 60–80%、`KineticNumber` 关键数字、相邻 `layout` 不同。**这是「不像 PPT」的主开关。**
**必读** [references/scenes.md#lecture-composition](scenes.md#lecture-composition) 与 [references/draftpaper.md#motion-design](draftpaper.md#motion-design) — 构图规范与多时钟动效六律。
**何时读**（选定皮肤后只读那一份）： [references/themes/flat.md](themes/flat.md) (flat, default) **or** [references/themes/cel.md](themes/cel.md); the shared boundary and engine chrome are in [references/themes/system.md](themes/system.md).
**必读** [references/checks.md#official-aesthetic-system](checks.md#official-aesthetic-system) — 不许改的锁定元素清单。
**逐条对照** [references/checks.md#composition-gate](checks.md#composition-gate) 与 [references/checks.md#quality-checklist](checks.md#quality-checklist) — 每道门禁的判据、失败修法、交付事实卡。
**何时读**（改引擎结构/时长/渲染速度时）：[references/technique.md#remotion-architecture](technique.md#remotion-architecture) 与 [references/technique.md#performance-design](technique.md#performance-design)。
**何时读**（切字幕 / 合成配音时）：[references/audio-captions.md#subtitle-timing](audio-captions.md#subtitle-timing) 与 [references/audio-captions.md#tts-audio](audio-captions.md#tts-audio)。
**何时读**（策划脚本 / 编排章节时）：[references/director.md#narrative-hook](director.md#narrative-hook) 与 [references/director.md#pacing-rhythm](director.md#pacing-rhythm)。
**先读** [references/scenes.md#independent-parts](scenes.md#independent-parts) — 部件分解、z-order、进出场契约（动任何部件之前读）。
**必读** [references/components.md#fxkit](components.md#fxkit) 与 [references/media.md#media-routing](media.md#media-routing) 的「修辞动作 → 组件」表 — 选组件之前读：**`live` 里每个名字都要能在表上指到**（这是选型纪律；门禁实际查的是"这个名字必须真的出现在场景源码里"，见 `validate-composition.py`）；写 `f={f}` 与 `frame={f}` 的地方见 fxkit 的命名陷阱。修辞工具件（`Callout` / `Checklist` / `JumpInText`）在 `src/toolkit.tsx`；**新封装层在 `src/components/`（Radix 手风琴与标签页、语法高亮、d3 图表、零依赖炫效果、描线/几何、中文反推字号）——选型前先看这一层**。
> **"一共有哪些件"只查一处：[media.md#media-routing §5.1 组件权威索引](media.md#51-组件权威索引53-件--选型只查这一处)**（53 件逐件：用途 / 何时用 / **何时别用** / 接触表第几页 / 真实使用记录）。
> `components.md#fxkit` 与 `showcase.tsx` 各自只保留实现细节与接触表版面，**不再维护组件清单**——别从接触表反推"有哪些件"，那里有 10 件根本没上。
**何时读**（排版前）：[references/scenes.md#canvas-modes](scenes.md#canvas-modes) — 唯一画布 16:9 的锁定参数、手机可读字号地板与纵向预算。
**何时读**（场景要用真实图片——用户提供 / Commons / 其他授权来源——时）：[references/director.md#visual-director](director.md#visual-director)。技能不调用生图模型。
**何时读**（组装工程 / 抓 HTML / 跨平台排错时）：[references/scenes.md#official-skills-exemplar](scenes.md#official-skills-exemplar)、[references/media.md#html-capture](media.md#html-capture)、[references/technique.md#cross-platform-compatibility](technique.md#cross-platform-compatibility)、[references/technique.md#windows-compatibility](technique.md#windows-compatibility)。

### 开工前 20 行授权契约

> **只记这 20 行；它与后面任何参考冲突时，以这段为准。** 每一条都对应一类真实问题。
>
> 1. 先跑 `new-project` 复制模板，绝不从记忆重建引擎。
> 2. 分镜表只写语义：`cues` 里**绝不写帧号**，帧号由 `resolve-shots.py` 推。
> 3. 骨架按内容的**第一性**选，不按标题关键词：有机制在跑 → Stage/Corridor；两个对等对象 → Split；要放大看局部 → Zoom。平局时**用能演示机制的那个**。
> 4. 相邻两镜骨架必须不同，全片 ≥3 种；"卡片 + 文字列表"不算讲解。
> 5. 每个讲解场景 ≥1 个**真的随旁白变状态**的构件；`live` 里必须是你场景文件里真实 import 并渲染过的组件名——**写假名字等于没写**（门禁会查）。
> 6. `media` 只允许 6 个值：`chart | console | code | graphic | text | metric`。
> 7. 每镜必须有 `camera.intent`（7 选 1）与 `anchor`；含文字的镜头放大 `s ≤ 1.35`。
> 8. 声明了运镜就**必须真的动**：`max(s) − min(s) ≥ 0.02` 或 `|Δx| + |Δy| ≥ 20`（把 `still` 改名成 `push-in` 不算运镜）。
> 9. 元素出现帧绑到"讲到它的那一句"（`SHOTS.Sx.beats`），**禁止镜头开头一次铺完**。
> 10. 出现统一用模板的 `enterAt()`（左→右展开 22 帧，不淡入、不上浮）。同一句里的多个元素，相邻两个开始出现**至少隔 12 帧**，同一时刻最多 2 个在长；见 [draftpaper.md#reveal-rules](draftpaper.md#reveal-rules)。
> 11. 帧参数名：`fxkit` 全部传 `frame={f}`；`media / kit / stagekit / skeletons / insert / shotkit` 传 `f={f}`。帧参数是必填类型，传错名或漏传时 `tsc` 报错（make-video 的 TypeScript 检查会停）。
> 12. 卡片高度必须用 `fitH()` 算，禁止手写"看着差不多"的固定高度（渲染期 `CardFitGate` 会拦下真裁切）。
> 13. 给槽内组件传宽度前先算 `mainW = w − pad×2 − railW − 18`。
> 14. 绝对定位构件的 `x/y` 相对**最近的定位祖先**，与文档流标题共用容器原点会精确重叠；**flex 子项若只含绝对定位子元素，必须显式给宽高**，否则宽度塌成 0、多张卡会叠在同一点。
> 15. 不铺整幅底托（它会把背景四角的吉祥物洗成幽灵）；局部 `tone='wash'` 底托必须 `z={-1}` 且径向羽化，正 z 会把整镜内容压成半透明。
> 16. 下 1/4 必须填满（底边接近 y=876）；面板下半空洞就是 PPT。**判据在渲染期 `FillGate`**（实测信息元素的最低边，不是读 `shots.json` 里那个声明字段——见 `references/checks.md#composition-gate` 的 P0-4 降级说明）。
> 17. 页眉 / 章节卡 / 字幕放在 `ShotCamera` **之外**。
> 18. 写场景文件后按顺序跑 `resolve-shots.py` → 构建期门禁，**P0 必须 = 0** 才允许渲染。
> 19. 门禁失败只允许改内容（换骨架 / 换介质 / 补元素 / 改高度），**不许改阈值、不许改判据**；连续两次不过就停下来报告。
> 20a. 字幕每行 ≤ 16 字（去句末标点后逐字计）：`build-semantic-captions.py` 自动在合法断点劈开超长行，`validate-caption-sync.py` 与渲染期 `CaptionFitGate` 双重把关。
> 20b. 讲到哪推到哪：每个讲解镜至少想一次 `cinema.focus`；代码/差异镜头字号 ≥ 26，关键数字用 `KineticNumber`（见 [camera.md#cinema-camera](camera.md#cinema-camera)）。
> 20. 首次渲染后读控制台：`OverlapGate` / `ClippingGate` / `CardFitGate` / `FillGate` 的覆盖率与告警必须清零或显式 `data-gate-allow`；拿不准就先出接触表看图。T3 的 `validate-motion-gaps` 也要跑（画面真的没动这类缺陷只有它能抓）。

### Create a project

Always start by copying a bundled template through the launcher; never rebuild the engine from memory.

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" check-deps
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-skill
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project ./notebook-video-project --style=cel
node "<SKILL_DIR>/scripts/notebook-video.mjs" prepare-browser ./notebook-video-project
```

- `assets/lecture-template` is the only project template (`--classic` fails with a pointer to `--style`).
- Five skins, chosen once at kickoff: `flat` (default) and `cel` are the component themes;
  `journal` / `papercut` / `archive` are the hand-made skins driven by the director layer.
  Themes swap palette, card skin, background decoration and subtitle chrome only — every
  coordinate, type scale, motion contract and gate is shared.
- **Text-safety colours (`*Ink`).** Fills and strokes keep the original accent; **text (`color:`) always uses
  the `*Ink` variant** (the original reads 2–3:1, under the 4.5:1 body text needs). Rule and gate:
  [references/themes/system.md](themes/system.md)「文字安全色」.
- One locked canvas at native 30 fps: 2560×1440 (16:9), authored in the 1920×1080 design space.
  4:3 / 3:4 canvases and the `paper` / `sticker` skins are not supported.
- Create the project in an empty directory so stale files from an earlier run cannot survive.

### Production workflow

```text
[input: topic / script]
  ① lock content      narration.txt + semantic caption lines (one cue per line)
  ② write shot table  <project>/manifests/shots.json — semantic only, no frame numbers
  ③ resolve           python "<SKILL_DIR>/scripts/resolve-shots.py" ./notebook-video-project
  ④ author scenes     four skeletons + media routing; each shot wrapped in ShotCamera(keys, anchor)
  ⑤ build-time gates  P0 must be 0
  ⑥ render            render + loudness normalisation (−16 LUFS / −1.5 dBTP)
  ⑦ runtime gates     CaptionFitGate / CardFitGate / OverlapGate / ClippingGate / CanvasBoundsGate / FillGate / SlotGuard — read the console
                      (then validate-motion-gaps on the finished MP4: "画面真的没动" is only visible there)
  ⑧ package           MP4 + contact sheet + editable source ZIP
```

Step-by-step detail and the per-step read list live in the numbered sections of
[references/scenes.md#scene-authoring](scenes.md#scene-authoring) (authoring) and
[references/scenes.md#lecture-composition](scenes.md#lecture-composition) (composition).

```text
# ②→③ the shot table is the single source of truth; never hand-edit the generated files
python "<SKILL_DIR>/scripts/resolve-shots.py" ./notebook-video-project
# it writes <project>/src/shots.ts (camera keyframes expanded) and <project>/manifests/shots.resolved.json

# ⑤ build-time gates — both must be P0 = 0 before spending render time
python "<SKILL_DIR>/scripts/validate-shot-motion.py" ./notebook-video-project
python "<SKILL_DIR>/scripts/validate-composition.py" ./notebook-video-project

# see components before choosing them (18-page contact sheet (`SHOWCASE_PAGES`); a select filter grabs each page's frames 6 and 21 → two mid-page frames per page, tiled 6x6)
node "<SKILL_DIR>/scripts/notebook-video.mjs" showcase ./notebook-video-project

# ⑥ render, then iterate cheaply on ranges
node "<SKILL_DIR>/scripts/notebook-video.mjs" render ./notebook-video-project ./notebook-video-project/renders/final.mp4
node "<SKILL_DIR>/scripts/notebook-video.mjs" review-frames ./notebook-video-project ./notebook-video-project/renders/scene-review.mp4 START_FRAME END_FRAME
```

### The gates

| Gate | When | Catches | Blocking? |
|---|---|---|---|
| `resolve-shots.py` | build | timeline gaps/overlaps, coverage ≠ duration, cue index out of range | yes |
| `validate-shot-motion.py` | build | anchor leaves the frame at any keyframe, zoom over budget, pan beyond the zoom-derived budget, camera-move quotas, **unknown intent names**, **a declared camera move that does not actually move** | yes (P0) |
| `validate-composition.py` | build | adjacent scenes sharing a skeleton, <3 skeletons, no live component in an explanation scene, **a `live` name that does not exist in the scene file**, <3 media, **unknown transition/entry/media names**, zones out of 3–5 (1–5 for the journal / papercut / archive skins), lower quarter not filled, **`explanation:false` used to bypass density**, hero size, shot-length spread, repeated骨架 fingerprints, beat gaps (aggregated with frame ranges), **a beat index past the end (`b[k]` / `SHOTS.Sx.beats[k]` — both spellings; the value is `undefined`, so it either throws per frame or the element never appears)** | yes (P0) |
| `validate-audio-levels.py` | build | **a sound-effect asset peaking below −12 dBFS** — it gets attenuated again at mix time and ends up inaudible | yes (P0) |
| `validate-presentation.py` | build | **讲与画对不对得上、读不读得过来**：beat 必须落在它声明的那句/那一镜内且不提前剧透、每条 cue 至少有一拍；字幕 ≤9 加权字/秒、单行 ≤16、≤2 行；字号绝不低于 13px、正文色对比度 ≥4.5:1（WCAG 2.2 SC 1.4.3）。详见 [references/checks.md#presentation-gate](checks.md#presentation-gate) | yes (P0) |
| `tsc --noEmit` | build | **`f={f}` passed to an fxkit component (or `frame={f}` to the other modules), or the frame prop left out** — the frame prop is a required type, so this is a compile error | yes |
| `CaptionFitGate` | render | caption wider than the safe width, measured with the **current canvas and skin's real weight/spacing** | yes |
| `CardFitGate` | render | content taller/wider than its card (`scrollHeight > clientHeight`, 6px tolerance; clips only), waits for fonts, logs coverage every 5s | yes |
| `OverlapGate` | render (15-frame grid **+ every shot boundary, beat and camera keyframe**) | text-vs-text overlap and paint-order occlusion using real glyph rects; gradient backgrounds count as opaque; header layer (z=140) included | `mode="block"` in the bundled films |
| `ClippingGate` | render (same sampling as `OverlapGate`) | **图形被裁**：SVG/图形元素的真实 rect 越出最近的"会裁切"祖先（HTML 的 `overflow≠visible` 祖先，或所属 `<svg>` 视口；显式 `overflow:visible` 的 svg 按计算样式判、不算越界）——`CardFitGate` / `OverlapGate` 只看文字，看不见"缺了半边的图形" | `mode="block"` in the bundled films |
| `CanvasBoundsGate` | render (every frame) | **含文字的叶元素**（HTML 叶 + SVG `text`/`tspan`）的**墨迹矩形**（`Range` 取字）越出 composition 视口：≥6px 出声、落定态（有效不透明度 ≥0.98）≥20px 硬拦；不判图形 / 版面件（归 `ClippingGate`，避免同一元素重复报）。补的是其它渲染期门禁与 `coords-lint.py`（排除布局件）都不管的「文字被画布边缘裁掉」。判据见 [references/checks.md#composition-gate](checks.md#composition-gate) §5.2 | `mode="warn"` in the bundled film / `mode="block"` on the contact sheet (deliberately different gears; reasons in `index.tsx` and the gate's header) |
| `FillGate` | render (same sampling) | **下 1/4 实测密度**：信息元素（有文字/有边框/有描边）rect 并集的最低边 vs y=876（±24 容差），z≥140 的子树跳过。这是 P0-4 的**真实判据**（构建期只查 `bottomFill` 字段在不在） | warn（观感线；"画错了"那三类才硬拦） |
| `SlotGuard` | render (output path, inside `StageFrame`) | **fill of the main slot**: union height of the innermost content elements ÷ slot height; speaks up below 35% and prints the slot's `mainW×mainH` — catches "slot was big enough, content left it empty" (measured: a 428px slot used 11%) | warn |
| `validate-motion-gaps.py` | **post-render (T3, needs the MP4)** | **画面真的没动**：ffmpeg `freezedetect` 逐帧比对，连续"几乎完全相同"超过阈值（默认按镜长比例）即 P0。⚠️ 必须先裁掉字幕带，否则逐字上屏的字幕会把每一段静止都遮掉 | yes (P0) |

Intentional overlaps (shot handoff, header swap, metric value replacement) must be declared with
`data-gate-allow`; the allow-list may never hide two different pieces of information colliding.

**A gate that prints nothing must be distinguishable from a gate that never ran.** `CardFitGate`,
`OverlapGate`, `ClippingGate` and `FillGate` log a coverage line every 5 seconds (`已测 N 个字…` /
`扫过 N 个，无被裁` / `下 1/4 已填`); if you see no coverage line at all,
the gate did not execute — treat that as a failure, not as a pass.

Validation after rendering:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-video ./notebook-video-project/renders/final.mp4 EXPECTED_SECONDS ./notebook-video-project/renders/contact-sheet.jpg
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-caption-sync ./notebook-video-project/audio/narration.mp3.json ./notebook-video-project/manifests/caption-cues.json
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-semantic-breaks ./notebook-video-project/manifests/caption-cues.json ./notebook-video-project/manifests/protected-caption-phrases.txt
# The CLI closes the delivery path: it auto-detects <project>/node_modules/budoux (walking up from the
# caption file) and always adds --require-budoux. A missing BudouX is a hard failure, not a silent skip —
# installing project dependencies is a precondition, never a skippable item. Pass --no-budoux to opt out.
node "<SKILL_DIR>/scripts/notebook-video.mjs" validate-visual-plan ./notebook-video-project
```

Inspect the opening, every shot boundary, the longest caption and the final frame. Reject any render
with black frames, subtitle overflow, a split protected phrase, half-visible exited objects, incorrect
stacking, unregistered rasters, or generated text baked into imagery.

### Execution discipline and safety (Zero-Mutation 原则)

脚本检测与视觉审查只读排查，绝不擅自变动系统配置；完整渲染（render）或引擎级重构须用户明确授权后方可执行。

**依赖分两种（最容易读错的一条）**：模板**已内置**的（`assets/lecture-template/package.json` 已声明）随 `npm install` 装好，**无需授权，直接 `import`**；清单之外的**新**依赖需用户明确授权后才能加进模板。
内置清单与边界见 [technique.md#dependency-policy](technique.md#dependency-policy)：**禁的是"按次付费、结果不可复现"的生成式模型，不是开源库。**

`scripts/*.py` 只用 Python 3.10+ **标准库**、**零第三方依赖**——这条**只针对 `scripts/` 下的 Python 脚本**，不是对整个技能的约束。不要在本技能里写入实验性改动，直到用户看过渲染成片并明确批准。

### Scripts 清单（`.sh` / `.cmd` 都是同一套 Node 实现的平台包装器，行为完全一致）

```text
scripts/notebook-video.mjs          跨平台统一启动器（new-project / resolve-shots / render / review-frames / showcase / package …）
scripts/resolve-shots.py            分镜表 → 帧号与相机关键帧（唯一定源）
scripts/validate-shot-motion.py     构建期：镜头出界证明 + 运镜配额
scripts/validate-composition.py     构建期：骨架 / 活性组件 / 介质 / 密度 / 枚举闭合 / live 可解析 / 主角尺寸 / 镜长分布
scripts/validate-audio-levels.py    构建期：音效素材峰值 < -12 dBFS 即 P0；预制音效库 hash/响度/峰值/事件映射/增益一致性（references/audio-captions.md#sfx-library）
scripts/validate-presentation.py    构建期：呈现效果（beat↔cue 对齐 / 字幕阅读预算 / 字号与对比度）——现有门禁都没问过的那一层
scripts/validate-caption-sync.py    字幕与 TTS 词边界一致
scripts/validate-semantic-breaks.py 保护短语不被切断
scripts/validate-visual-plan.py     视觉计划与清单一致
scripts/validate-layering.py        图层与离场契约
scripts/validate-skill-consistency.py 仓库级一致性（模板 + 文档链接 + 主题包完整性 + 每主题三张背景）
scripts/build-semantic-captions.py  语义字幕行 → cue 表
scripts/match-timing.py             换配音后重对齐章节时间轴
scripts/retime.py                   时长变化的机械重写（DURATION / 清单 / 音效建议表）
scripts/audition.py                 TTS 试听条 + 多音字扫描
scripts/coords-lint.py              覆盖层坐标越界体检
scripts/package-project.py         交付源码打包（排除 node_modules / renders / 密钥）
scripts/selftest.py                 端到端回归自测
scripts/negative-gate-check.py     负向抽查：给六道构建期门禁喂"该拦的夹具"，验证它们真的会拦
scripts/notebook-video.mjs | .cmd   统一入口：check-deps / prepare-browser / new-project / sync / render / validate-video / package …
scripts/make-video.mjs | .cmd       一条命令出片（compose → 门禁 → 静帧 / 渲染）
```

### Regression self-test

```text
python "<SKILL_DIR>/scripts/selftest.py"
```

Good fixtures must pass and each broken fixture (protected phrase split across cues, mismatched caption
sync, non-video input) must be rejected by the matching gate.

For the build-time gates, run the negative spot-check: it feeds each gate fixtures it must catch (anchor out of
frame, pan over budget, adjacent same skeleton, no live component, timeline gap, faked `live`/media names, a
camera move that never moves, frame-prop typos, mistimed or out-of-range beats, too-fast captions, fonts below the
floor, low-contrast text, stale imports and doc names, a weakened canvas-bounds gate, `evidence` and narrative-`move`
fixtures, layering and visual-plan violations, inaudible or corrupt audio, the removed example project put back,
a stale resolved timeline, camera defaults, a BudouX-less delivery, canvas-mode drift) plus negative controls, and
asserts each gate blocks, warns or passes as expected — 65 fixtures / 112 assertions (the script prints its own tally).
Rules these fixtures pin: a failed measurement must hard-fail the gate, not pass; a width is never borrowed from
another composition; guards must never be plain `assert`s (they must survive `python -O`); shared numbers (FPS,
caption cap, reading speed, stage, zoom caps, grow timing) live once in `assets/lecture-template/src/contract.json`,
read by both TS and Python; and every blocking fixture pins the expected message substring, so "failed for some
other reason" cannot pass as a blocked fixture.
**A gate that exists in name only is the most dangerous defect.**

```text
python "<SKILL_DIR>/scripts/negative-gate-check.py"
```

<a id="independent-parts"></a>

## Independent components and layer contracts

### Decompose by motion ownership

If two visible things enter, move, rotate, hide, light or exit at different frames, model them as separate React components or SVG groups (body/arms, folder back/front, each card, wire, button, status light, badge). A flattened scene cut into rectangles is not independent modeling.

### Manifest fields

Every moving part requires:

```json
{
  "id": "source-card",
  "scene": 4,
  "z": 50,
  "layer_role": "floating",
  "occlusion_contract": "always-visible",
  "entry_frame": 1220,
  "exit_frame": 1430,
  "exit_contract": "fully-outside",
  "motion": ["curved-transfer", "dynamic-shadow"]
}
```

Use stable IDs in code and cue data.

### Layer roles

Order: background → wire → base → slot → status → floating → foreground → chrome → subtitle.

- Floating objects stay above base/slot/status objects unless explicitly being inserted.
- A slot may cover a card only after the card crosses a visible slot boundary.
- Chrome remains above scene content.
- Subtitle remains highest.

CSS transforms, opacity, filters and isolation create stacking contexts. Do not assume a child z-index can escape its parent. Put objects that must overlap in a shared intended context.

### Complete exit

Every temporary part needs an exit contract. Remove it only after it is completely outside the canvas, or fade the whole component after its geometry is no longer clipped. Never move only a portion behind an accidental container edge.

Inspect entry, midpoint, rest and exit frames at full 2560×1440 delivery resolution.

### Raster assets

Use generated raster images only for topic-specific illustration. Keep exact text, logos, wires and independently moving parts in code. Include transparent padding only when rotation requires it.

Register each used raster in `manifests/visual-assets.json`. Treat the bitmap, each highlight box, each arrow and each explanation line as separate parts with their own timing. Preload the bitmap in `AssetGate`. Generated assets must not contain baked labels or charts; request crop-safe negative space and add exact information in Remotion. Read `director.md#visual-director`.

<a id="lecture-composition"></a>

## Lecture composition: the default multi-zone visual route

> **仅限组件路线（flat / cel）。** 手作路线（journal / papercut / archive）不读这份，必读清单见 SKILL.md 第 0 步。

### Contents

- [The six rules](#the-six-rules)
  - [1. Pure code-drawn graphics](#1-pure-code-drawn-graphics)
  - [2. Multi-zone layout](#2-multi-zone-layout)
  - [3. Text and graphics are co-stars](#3-text-and-graphics-are-co-stars)
  - [4. Frame-accurate speech sync](#4-frame-accurate-speech-sync)
  - [5. Demonstrative animation](#5-demonstrative-animation)
  - [6. Series component reuse](#6-series-component-reuse)
- [Skeletons, media and camera](#skeletons-media-and-camera)
- [Working the template](#working-the-template)
- [Self-check before rendering](#self-check-before-rendering)

### Skeletons, media and camera

Besides the six rules, three gated layers decide framing and medium (checked by `validate-composition.py` /
`validate-shot-motion.py`; read [checks.md#composition-gate](checks.md#composition-gate) before rendering):

1. **Skeletons** — `Stage` / `Corridor` / `Split` / `Zoom`; no adjacent repeat, ≥3 per film. See [scenes.md#scene-skeletons](scenes.md#scene-skeletons).
2. **Media** — answer "what medium" before "which card": ≥3 media per film, ≥1 live component per explanation
   scene; pure card-and-bullets scenes are rejected. See [media.md#media-routing](media.md#media-routing).
3. **Camera** — one intent per shot plus a provably-visible `anchor`, ≥3 moves per chapter. See
   [camera.md#shot-language](camera.md#shot-language).

This is the default visual route: pure code-drawn SVG plus synchronized text, no image model. Follow the steps
mechanically; the template has a working example of every pattern. When a concrete hero scene needs a real image,
take it from the user, Wikimedia Commons / Openverse or another licensed source and follow
`director.md#visual-director` for those scenes only.

### The six rules

#### 1. Pure code-drawn graphics

Every visual object (mascot, diagram, machine, chart, arrow) is SVG in the Remotion tree; no bitmap is required.
Exploit it: strokes grow (`strokeDasharray` + `strokeDashoffset`), parts move independently, colors match the
locked palette. Copy `LineIcon`, `ShapeDraw`, `PathDraw`-style components instead of inventing new drawing styles.

#### 2. Multi-zone layout

A scene is not one hero object. Split the 1920×1080 design canvas into 3–5 functional zones, for example:

- left: explanation panel (`Paper` with a WenKai title + body copy);
- right or center: the graphic demonstration area;
- bottom or side: a progressive checklist or comparison cards;
- floating: small annotation tags that appear on cue.

Locked density budget: **each zone runs one main action at a time**, unrelated cards stay ≥70px apart, and only
one temporary transfer object crosses the central corridor at once — parallel zones, never parallel actions in one zone.

#### 3. Text and graphics are co-stars

Pair every graphic demonstration with readable text carrying the same knowledge (ticking checklists, good/bad
cards, warning strips, step tags); the viewer should learn from the text alone or the animation alone.

#### 4. Frame-accurate speech sync

Every appearance frame comes from the caption cue table, never from guessing:

1. Run the TTS adapter, then `build-semantic-captions`, producing
   `manifests/caption-cues.json`.
2. Print the cue frame table:

   ```text
   python -c "import json; d=json.load(open('manifests/caption-cues.json',encoding='utf-8'))['cues']; [print(i+1, round(c['start_ms']*30/1000), round(c['speech_end_ms']*30/1000), c['text'][:16]) for i,c in enumerate(d)]"
   ```

3. Scene boundary = start frame of the first cue of each narration paragraph (the chapter-segmented adapter
   also writes `manifests/chapters.json` with exact chapter frames).
4. Element appearance frame = start frame of the line that speaks about it, minus the scene start frame
   (scenes use local frames `l`).
5. A checklist item lights up on the cue that says it (a lamp turns red on "red"). Speak it, then show it —
   never earlier than the previous cue.

#### 5. Demonstrative animation

Animations must carry knowledge, not just decorate entries: a task card travels a shared track and changes state
at each station (process); a card flies from one owner to another (fork, transfer, push); one log line highlights
(locating an error); gauges fill, digits light positionally, growth chains light level by level (quantities).
Entries/exits stay restrained; the knowledge lives in what the object does between them.

#### 6. Series component reuse

One channel, one visual IP: reuse the same mascot, paper cards, badges and list patterns across a series and
cross-reference episodes in the closing scene. New graphics become reusable components next to the existing ones,
in the same stroke and palette style.

### Working the template

`new-project` copies `assets/lecture-template`, a fully validated 900-frame film that demonstrates every rule. The source is layered:

- **LOCKED layer** — aesthetic core, subtitle, background, chrome, gates: never edit.
- **Component library** — `Paper`, `LineIcon`, `CheckBadge`, rails, gauges: reuse directly, extend by imitation.
- **Content layer** — `COPY`, scene boundaries, `Scene*` components, `Sound` frame lists: rewrite for a new topic.

To change duration, follow the duration-extension invariant in `technique.md#remotion-architecture` and update
`DURATION`, the scene guards and `manifests/asset-manifest.json` together.

### Self-check before rendering

Answer every question with yes; fix the scene otherwise.

1. Every scene has ≥3 populated zones (except a deliberate title/CTA scene)?
2. Every animation start frame traces to a specific cue line?
3. Bitmap count is zero on this route (`visual-assets.json` assets empty), unless the user explicitly accepted the image add-on?
4. Each zone runs one main action at a time, ≥70px between unrelated cards?
5. ≥1 animation per explanatory scene demonstrates the mechanism (transfer, highlight, fill, state change), not just an entry?
6. Checklists tick exactly when their line is spoken?
7. Standard QA battery passed (`validate-visual-plan`, `validate-layering`, `validate-caption-sync`, `validate-semantic-breaks`, `validate-video`)?
8. All reading text is pure ink (`C.ink`)? Muted is only for decorative kickers and struck-through contrast words; muted body copy fails on phones.
9. Content cards reach about 40px above the subtitle strip (bottom edge near y=876 in the 1080 design space)? An empty lower quarter wastes the area phones show largest.
10. Every SVG element keeps ≥24px clearance from its neighbors, with no text label on top of a graphic?

<a id="canvas-modes"></a>

## Canvas: 16:9 only

本技能只有**一种**交付画布：16:9。不支持 4:3 与 3:4（`Film4x3` / `Film3x4` 及其背景、门禁分支均不存在）。

### Spec

| Parameter | Value |
| --- | --- |
| Composition (delivery) | 2560×1440, native 30fps |
| Design coordinate space | 1920×1080 |
| Delivery scale | 4/3 (`MODES['16:9'].scale`) |
| Subtitle text `left/right` | 188 |
| Subtitle text `bottom` (contract value) | 34 |
| Subtitle font (WenKai Lite) | 44px |
| Subtitle safe width (`safe` / `subtitleSafeWidth`) | 1334 |
| Usable content width | ~1700 |
| Column layout | two columns |

These are contract values. They live in `assets/lecture-template/src/theme/canvas.ts` (`MODES['16:9']`) and in `scripts/validate-visual-plan.py` (`CANVAS_MODES[2560]`); `validate-skill-consistency.py` cross-checks the two. Each skin's `SubtitleChrome` has its own render-time `bottom` (`cel` 44 / `flat` 40).

`validate-visual-plan` rejects any `NotebookVideoFilm` Composition width other than 2560, and `validate-video` accepts only 2560×1440 containers.

### Mobile readability type floor

Small text is the main reason films look blurry on phones; the floor raises only the small tiers:

```text
bodyL:26  bodyM:24  bodyS:23
labelL:22 labelM:21 labelS:20
microL:18 microS:16
```

Never author content text below 16px design size; if a note only fits below that, cut it or move it into the narration.

### Full-canvas vertical budget

Use the full height between chapter chrome and subtitle strip: card tops near y=190, bottoms about y=876 (40px above the strip). An empty lower quarter is a layout defect, not negative space; bottom-anchored conclusion strips inside cards are the standard way to fill it.

<a id="recipes"></a>

## 七个线稿配方（`recipe`）· 降级为可选

> **先读这段。** 主线是 [components.md#journal-page](components.md#journal-page)：
> **手账页承载（真图版 / 放大镜）+ 组件讲概念**。下面七个配方把简笔线稿当解释图，在讲解视频里像剪贴画，
> **比不画更差**（`validate-fusion` 对这类镜头 >20% 报 P1）。
>
> 什么时候还能用：**标本速写**——一件具体的东西（软木塞、电池、火箭、芯片）+ 手写名 + 尺寸线，
> 观众需要先认出「这是哪个东西」。抽象概念（流程、对比、数量关系）一律用组件，不要画。

一镜先问：**这一镜讲的东西在哪？** 再选配方。配方决定版面、线稿摆哪、卡片多大；
你只填内容（卡片写什么、结论是什么、线稿画什么）。

```json
{
  "layout": "statement",
  "recipe": "sketch-readout",
  "lines": ["第一级最重，占起飞质量八成多。", "烧完就扔掉，不再拖着它。"],
  "sketch": {"draw": "lib:rocket", "acts": [{"at": "@L1", "do": "enter"}, {"at": "@L2", "do": "point", "target": "stage1"}]},
  "content": {"cards": ["第一级约占起飞质量的 85%", "烧完就分离，不进入轨道"]}
}
```

> 配方镜头仍然要写 `layout`（引擎的骨架/节奏用它），但版面由配方接管。
> `sketch-readout` / `scene-verdict` / `before-after` / `hammer` 不需要写 `content.text`。

### ① `sketch-readout` 线稿主体 + 读数贴边

- 版面：线稿占左 55%，右侧 1–2 张读数卡。
- 必填：`sketch` + `content.cards`（1–2 条，每条 ≤ 3 行）。
- 什么时候用：讲「一个东西是什么」，数字/结论要贴在它旁边。
- 讲解层：`point` 的部位会换强调色，其余压暗；卡片独立入场。

### ② `component-annotated` 组件为主 + 线稿批注

- 版面：原版式占 70%，右下角一块小线稿；`annotate` 叠在组件上。
- 必填：任意组件版式 + `annotate:[{target, kind, text, at}]`（`kind` = `circle` / `underline` / `arrow` / `note`，`at` 与 `sketch.acts` 同一写法：数字帧 / `@L1` / `@L1.3`）。
  旧写法 `line`（0 起数）仍能用，compose 会提示改写。
- 什么时候用：屏幕里、代码里发生的事（终端报错、代码行、图表异常）。
- 例：`"annotate":[{"target":"L3","kind":"circle","text":"就是这一行","at":"@L2"}]`。

### ③ `scene-verdict` 情境线稿 + 结论卡

- 版面：小场景占上 60%，结论卡在下。
- 必填：`sketch` + `content.verdict`（一句结论）。
- 什么时候用：用一个生活场景引出知识点（排队、塞车、堆满的桌子）。

### ④ `before-after` 同一线稿两状态

- 版面：线稿居中，左右各一张小卡（「改之前 / 改之后」）。
- 必填：`sketch` + `content.before` + `content.after`。
- 线稿用 `swap` 换状态；`mark:"check"` 落在「之后」。
- 什么时候用：改前/改后、贵/便宜、满/空。

### ⑤ `list-icons` 清单 + 小线稿图标

- 版面：清单组件为主，右侧一块小线稿（当前版本的图标位）。
- 必填：`layout:"list"` + `content.items`（2–5 条）。
- 什么时候用：几个要点，每条都能用一个东西代表。

### ⑥ `data-with-object` 数据 + 实物单位

- 版面：柱条/数字行按原版式，右下角一枚小线稿当「实物单位」。
- 必填：`layout:"bars"` 或 `"number"` + 数据 + `sketch`（`place:"corner"`）。
- 什么时候用：几个数字比较，观众对量级没概念（一枚小火箭 = 一吨）。

### ⑦ `hammer` 锤子帧

- 版面：手写大字满屏 + 角落一个小线稿。
- 必填：`content.text`（全片最该记住的一句，≤ 18 字）。
- 全片 ≤3 个；多了会变成口号片。

### 配比（门禁按 P1 提醒）

- 含线稿的镜头：片长 **30%–60%**。
- 纯组件镜头（无线稿、无讲解层）：**≤30%**。
- 纯文字镜头（锤子帧除外）：**≤10%**。
- 锤子帧：**≤3**。
- 主题里的那个东西（`subject_of_film`）：**全片至少出现一次**，否则 P0。

### 选不出来时

| 这一镜讲的是 | 用哪个 |
|---|---|
| 一个东西 / 一个现象是什么 | ① |
| 屏幕里、代码里发生的事 | ② |
| 一个生活场景引出的知识点 | ③ |
| 改之前 / 改之后 | ④ |
| 几个要点 | ⑤ |
| 一张真照片 / 截图 | ⑥ |
| 几个数字比较 | ⑦ |
| 全片最该记住的一句 | ⑧ |

<a id="official-skills-exemplar"></a>

## Official exemplar

The binding exemplar is the lecture template itself: an 8-shot, 1150-frame Remotion film configured at native 2560×1440 and 30fps (design space 1920×1080), skinned by one of two locked themes, `flat` (default) and `cel`. It demonstrates the four scene skeletons, five camera intents and the full gate stack on one topic (an open-source onboarding explainer). The removed `example-project` (`--classic`) is not a reference.

### Required starting point

Run `node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project <PROJECT_DIRECTORY> [--style=flat|cel]`. It copies the exact runnable source, pinned dependencies, caption timing, the three locked backgrounds per theme, open-license fonts and procedural action sounds.

Canonical sources:

- `assets/lecture-template/src/index.tsx` (engine: gates, subtitle, chrome, backdrop, audio tree)
- `assets/lecture-template/src/scenes.tsx` (scene layer: copy this structure, replace the content)
- `assets/lecture-template/src/theme/` (the two locked skins)
- `assets/lecture-template/package-lock.json`
- `references/locked-style-contract.json`

### What remains reusable

Keep these components and behaviors:

- `AssetGate`, `CaptionFitGate`, `Background`, `Paper`;
- the theme's `SubtitleChrome` with the per-word reveal from `Subtitle`;
- stable `Chrome` chapter/header system;
- the backdrop rule: chapter shots on the `chapter` background, dense shots (zones ≥ 4) on `quiet`, the rest on `main`, with a `bg` override in the shot table;
- stepped physical frame helper `q`;
- dynamic shadow tied to actual lift;
- declarative `Sound` tree;
- integer-frame caption preprocessing;
- complete exit of obsolete components;
- `manifests/visual-assets.json` provenance and crop contracts for every raster;
- one semantic action per spatial zone;
- large readable objects distributed across the wide canvas instead of a central effect pile.

Topic-specific heroes, copy, props and scene metaphors must change for the new subject.

### Rejection conditions

Reject the render if:

- any non-Remotion visual renderer is introduced without explicit user approval;
- a generated image is treated as the complete video instead of an asset animated and explained by Remotion;
- exact labels or diagrams are baked into generated imagery;
- a raster asset lacks provenance, crop policy or redistribution notes;
- the background, subtitle or chapter system is reconstructed from memory;
- a full-frame translucent wash is laid over the background (it ghosts the corner characters);
- shadows remain identical while cards lift;
- cards disappear by clipping and leave a visible fragment;
- temporary cards overlap unrelated zones or collect in a central pile;
- action sounds are added in an unrelated post-production timeline;
- fonts may render before the preload gate resolves, or any text depends on a system font;
- the output lacks actual video QA.
