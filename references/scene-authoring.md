# 场景编写说明书（照着抄，不要重新发明）

> 这份文档是给**执行 AI** 的：本技能的用法是「强 AI 做出一版最好的成片 → 把它的结构与代码沉淀成模板
> → 后续用任何（包括较弱的）AI 照着模板模仿，收敛到 95% 的水平」。
> 所以**模板里的代码形状就是标准答案**；你的任务是**照抄结构、替换内容**，不是自由发挥。
>
> 看不懂就想一句话：**结构别动，只换内容。** 需要换结构时，先读
> [scene-skeletons.md](scene-skeletons.md) 与 [composition-gate.md](composition-gate.md)。

---

## 目录

- [0. 六步流程（顺序不要跳）](#0-六步流程顺序不要跳)
- [1. 分镜表长什么样](#1-分镜表长什么样可直接改造)
- [2. 场景代码的标准形状](#2-场景代码的标准形状照抄)
- [3. 反复踩的八个坑](#3-反复踩的八个坑每个都是真金白银换的)
- [4. 渲染前自检](#4-渲染前自检逐条打勾)
- [5. 想做得更好时的顺序](#5-想做得更好时的顺序)

## 0. 六步流程（顺序不要跳）

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

## 1. 分镜表长什么样（可直接改造）

```json
{
  "duration": 1126, "theme": "paper", "canvas": "16:9",
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

- `cues: [起, 止]` 是**闭区间**；`from` = 首句起始帧，`to` = 下一镜首句起始帧（末镜 = 末句结束 + `tail`）。
- **禁止**在分镜表里手写帧号。**禁止**手改 `src/shots.ts`（它带 AUTO-GENERATED 头）。
- `beats` 覆盖每一句的起始帧即可；若某段超过 110 帧没有变化，解析器会提醒你补拍。

---

## 2. 场景代码的标准形状（照抄）

```tsx
import {SHOTS} from './shots';
import {ShotCamera, CoverPanel} from './shotkit';
import {StageFrame, PhaseRail} from './stagekit';

const C = THEME.palette;
const IN = 22;
/** 入场：22 帧 easeOut + 上浮 + 微缩放。所有元素都用它。 */
const enterAt = (f: number, at: number): React.CSSProperties => {
  const p = easeOut(f, at, at + IN);
  return {opacity: p, transform: `translateY(${(1 - p) * 22}px) scale(${0.975 + 0.025 * p})`};
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
（`ConsoleWindow` / `MetricGrid` / `StampBanner` / fxkit 的 18 件）都已提供。
**先用现成的，缺什么再补；补的要加进接触表。**

### 槽宽公式（给槽内组件传宽度前先算）

```
mainW = w − pad×2 − (rail ? railW + 18 : 0)
mainH = h − pad×2 − headH − stampH − (stamp ? 14 : 0) − (header ? 14 : 0)
```

`StageFrame` 会把这两个值算好，并在**开发模式**下用 `SlotGuard` 检查 main 槽是否溢出（超宽/超高会在控制台打警告）。
所以：给 `ConsoleWindow` / `SkeletonCard` / `MetricGrid` 传 `w` 之前，**先算 `mainW`**，不要凭感觉写整数。

### 三个必须遵守的写法

1. **元素出现帧绑到节拍**：`enterAt(f, at(i))`，不要用 `popS(f, 0)` 或镜头开头的固定帧。
2. **容器里不要混用**"文档流内的标题"和"绝对定位组件"——两者都从容器原点起，会精确重叠。
   给绝对定位组件显式 `y`，或把标题也绝对定位。
3. **整幅底托用负 z 且羽化**（见 [media-routing.md](media-routing.md) §4.2）：
   `z={-1}`、`boxShadow:'none'`、径向渐变。正 z 会把整镜内容压成半透明。

---

## 3. 反复踩的六个坑（每个都是真金白银换的）

| # | 症状 | 真因 | 修法 |
|---|---|---|---|
| 1 | 动画整体错位、`Frame NaN` | 给 **fxkit** 组件传了 `f`（它的参数叫 `frame`），`f` 被静默忽略 → 回落到全局帧 | fxkit 传 `frame={f}`；v2.10 新模块传 `f={f}` |
| 2 | 镜头一动，边缘内容被裁掉 | 平移会整层移动内容，`s=1.0` 时必然露边 | 平移量须由缩放覆盖：`maxPanX=960(1−1/s)`；`pan-follow` 自带 `from≥1.06` |
| 3 | 一屏字叠成一团 | 文档流标题 + 绝对定位组件都从容器原点起 | 给组件显式 `y`，或把标题绝对定位 |
| 4 | 整镜内容发灰/半透明 | 底托用了**正 z-index**，压住所有 `z-index:auto` 的场景元素 | 底托 `z={-1}` |
| 5 | 画面下沿一条硬缝 | 底托是硬边矩形 | 径向羽化 + 去掉描边环 |
| 6 | 字幕被裁切却没人报错 | `CaptionFitGate` 曾硬编码 16:9 的字号/安全宽 | 已修：按当前画布与主题实测（**修好后会更严格，会拦下以前静默放行的字幕**） |
| 7 | **给槽内组件传的宽度超过了槽的可用宽**，不透明组件压住右侧轨道文字 | 没算 `mainW = w − pad×2 − railW − 18`，凭感觉写 `w=1060` 而实际只有 1035 | 先算 `mainW/mainH` 再传宽度；`StageFrame` 内建 `SlotGuard` 会在控制台警告超宽（见 §2 下方） |
| 8 | 两个不同信息互相压字（门禁报 `OverlapGate`） | 真的重叠 | 按 §4 自检逐条修；**只有**"同一信息在同位置替换"和"镜头交接"才允许用 `data-gate-allow` 白名单 |

---

## 4. 渲染前自检（逐条打勾）

- [ ] `resolve-shots.py` 通过（时间轴连续、覆盖 = duration）
- [ ] `validate-shot-motion.py` **P0 = 0**（含每镜 anchor 出界证明、平移预算）
- [ ] `validate-composition.py` **P0 = 0**（骨架相邻不同款、活性组件覆盖、介质 ≥3 种、下 1/4 填满）
- [ ] 一镜内**没有元素在它该出现的那句之前出现**
- [ ] 章节卡 / 页眉 / 字幕都在 `ShotCamera` **之外**
- [ ] 压到背景装饰区的内容坐在底托上；底托是负 z + 羽化
- [ ] 用到的每个构件都在 `NotebookVideoShowcase` 接触表里出现过
- [ ] **首次渲染后读一遍控制台**：`OverlapGate`（文字重叠/遮挡）与 `SlotGuard`（槽内溢出）的警告必须清空，或逐条确认是"有意覆盖"并补上 `data-gate-allow`
- [ ] 进度类动画用 `scaleX`，数值类用 `tabular-nums`（见 motion-design.md 六律）

---

## 5. 想做得更好时的顺序

先改**内容层的表达**（换介质、换骨架、把一屏元素拆成逐句出现），
再改**参数**（时间、位移、缩放、颜色），**最后**才考虑动引擎。
**不要**为了"更炫"加新组件——本技能的失效模式从来不是组件不够，而是没被用上、或结构同构。
