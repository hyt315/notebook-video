# 场景骨架与分镜表

> 状态：**v2.10 生效**。落地件：`assets/lecture-template/src/stagekit.tsx`（Stage）、
> `skeletons.tsx`（Corridor / Split / Zoom）；门禁：`scripts/validate-composition.py`。

## 目录

- [1. 要解决的问题](#1-要解决的问题)
- [2. 四种骨架](#2-四种骨架)
- [3. Stage 的写法](#3-stage-的写法活体主体)
- [3.5 时序铁律：讲到哪，出现到哪](#35-时序铁律讲到哪出现到哪)
- [4. 分镜表](#4-分镜表唯一真源)
- [5. 添加新骨架的门槛](#5-添加新骨架的门槛)

## 1. 要解决的问题

v2.8 的四个场景**结构同构**：`SceneContribute` / `SceneShip` / `SceneSkills` 三处近乎逐行相同
（`Paper` + 涂鸦字 + 标题 + 编号列表 + 底部贴标），另有一整套 `*P` 竖屏复制品共 8 份。
**换内容不换结构 = 四个 PPT 页。** 这不是 AI 偷懒，是模板只给了这一种结构。

解法不是加 157 张镜头卡（维护债 >> 收益），而是**四种构图本来就不同的骨架**。

## 2. 四种骨架

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

## 3. Stage 的写法（活体主体）

三条标准：

1. **占主体**：16:9 下 ≥1024×620 设计像素，或占画幅宽 ≥60%；
2. **有状态机**：≥3 拍（长度 ≥12s 时 ≥5 拍），每拍 2–4 秒，**全程同一实例不卸载**；
3. **能装东西**：`header` / `main` / `rail` / `stamp` 四个命名槽。

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

**`Attach`** 用于"附着信息"：原本要新开一张说明卡的，改成挂在主体附近的贴标。
只有"主体装不下的、且与主体无物理关系的信息"才允许独立成卡。

## 3.5 时序铁律：讲到哪，出现到哪

**元素出现帧必须绑定到"讲到它的那一句"**，即 `SHOTS.Sx.beats` 里的某个节拍。
禁止在镜头开头把一屏元素一次性铺完——那会让画面比旁白跑得快，观众看到的是"已经讲完了"。

```tsx
const b = SHOTS.S6.beats;                       // cue 推导出的本地节拍帧
const at = (i: number, d = 0) => (b[i] ?? 0) + d;

<框架   style={enterAt(f, at(0))} />            // 框架在本镜首句出现
<元素   style={enterAt(f, at(1))} />            // 第 2 句讲到的元素，第 2 拍才出现
items.map((x, i) => <项 style={enterAt(f, at(2) + i * 8)} />)  // 同句内最多 8 帧错峰
```

**入场统一用 `enterAt()`**：22 帧 `easeOut`（`bezier(.16,1,.3,1)`）+ 22px 上浮 + `0.975→1` 微缩放。
不要 0 帧闪现，不要线性缓动，不要每个元素各写一套曲线。同一句内的多个元素错峰 8–16 帧；
跨句的元素**必须**跨拍出现。整镜末尾留 18 帧干净淡出。

自检：随手暂停任意一帧，画面里出现的元素**不应该超出旁白已经讲到的东西**。

## 4. 分镜表（唯一真源）

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
    "live": ["TimeRail", "StaggerList"],
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
| `zones` / `bottomFill` | 功能分区数（3–5）、下 1/4 是否填满 | `validate-composition` |
| `contentBand` / `cover` | 内容带与背景装饰区的关系 | `validate-shot-motion` |
| `transition` / `entry` | 转场与入场方式（多样性） | `validate-composition` |
| `beats` | 状态变化帧（节奏判据） | `validate-composition` |

### 解析流程

```
python scripts/resolve-shots.py PROJECT_DIR
  → 写 src/shots.ts（含已展开的相机关键帧 keys）与 manifests/shots.resolved.json
  → 校验：时间轴连续、无断档重叠、覆盖 = duration、cue 索引在范围内
```

**边界规则**：`from` = 本镜首句 cue 的起始帧；`to` = **下一镜首句的起始帧**（末镜 = 末句结束 + `tail`）。
由构造保证连续。

**好处**：改一句台词 → 改 `narration.txt` 与语义字幕行 → 重跑 `resolve-shots`，
所有帧号（含音效钉帧）自动跟着走。**不再手改几十处 `ease(l,95,130)`。**

## 5. 添加新骨架的门槛

新骨架必须：

1. 构图与现有四种**明显不同**（同构图不算新骨架）；
2. 在 `skeletons.tsx` 的 `SKELETONS` 里注册，并同步 `validate-composition.py` 的 `SKELETONS`；
3. 有「何时用 / 何时不用」的判据，写进本文件的表格；
4. 在 `NotebookVideoShowcase` 的接触表里出现（让后续 AI 看得见）。

**不要**为了题材加一次性骨架——一次性效果留在该片的场景文件里。
