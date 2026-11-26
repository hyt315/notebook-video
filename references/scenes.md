# 镜头表与场景：骨架、手写场景、部件分层、画布与配方

本篇说明分镜骨架、手写场景（逃生舱）、分层契约、16:9 画布与线稿配方。主路线请优先走 `story.json` + `blueprints/*.json`。

<a id="scene-skeletons"></a>
## 1. 场景骨架与分镜表

- **分镜唯一真源**：`manifests/shots.json` 经 `scripts/resolve-shots.py` 生成 `shots.resolved.json` 与 `src/shots.ts`（禁手改生成物）。
- **枚举闭集**：骨架（`src/skeletons.tsx`）须相邻更换，同骨架或隔镜同指纹记 P1；入场仅限 `build`/`fade`/`rise`/`slide`/`zoom`（非法判 P0）；换章境界与手作路线默认 `"auto"` 翻页（`CURL_FRAMES` = 22 帧），组件同章内依布局走 `slide`/`fade`，可由 `src/insert.tsx` 显式声明。
- **讲法字段**：每镜声明 `move`（连续 ≥3 镜同动作记 P1）与 `evidence`（须指向源码中真用到的 JSX 组件名，否则 P0）。

<a id="scene-authoring"></a>
## 2. 场景编写原则

1. **一镜一问题**：每镜填 `$asks`（未填记 P1），讲完 1–3 句回答一问。
2. **草稿纸节奏**：遵循 [draftpaper.md](draftpaper.md#reveal-rules) 随旁白长出与字号/密度上限（`MIN_FONT` 32px、`CORE_FONT_FLOOR` 64px、`SCREEN_READ_BUDGET` 40 加权字、代码扫面地板 `MIN_LABEL_FONT` 13px）。
3. **活性与关键词**：讲解镜须有真实数据/状态变化的活性组件，纯静态卡片堆判 P0；用 `{{术语}}` 或 `{{术语|元素id}}` 自动绑定聚光与相机焦点。

<a id="handwritten-scenes"></a>
## 3. 手写场景路线（逃生舱）

逐镜手调版面时编辑 `manifests/shots.json` 与 `src/scenes.tsx`：

- **帧参数铁律**：仅 `fxkit` 与 `toolkit`（`Callout`/`Checklist`）传 `frame={f}`，其余传 `f={f}`（[components.md](components.md)）；严禁用 `useRawCurrentFrame()` 或隐身占位，非活跃镜头须卸载。
- **安全色、下标与命名**：文字仅用 `C.ink`/`C.muted`/`C.*Ink`（对比度 ≥ 4.5:1）；`SHOTS.Sx.beats[i]` 不得越界；定制件照 `src/custom/RequestLane.tsx` 写并在 `src/custom/index.ts` 的 `CUSTOM` 注册；每个镜号须对应明确场景函数声明（`const S1: React.FC<...>`），否则 P0。

### 最小可用范例（真实导出，可直接编译）

```tsx
// src/scenes.tsx
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {THEME} from './theme/active';
import {SHOTS} from './shots';
import {Callout} from './toolkit';
import {HandNote} from './craft/ink';

const C = THEME.palette;
export const S1: React.FC<{f: number}> = ({f}) => {
  const b = SHOTS.S1.beats;
  return (
    <AbsoluteFill>
      <Callout frame={f} start={b[0]} x={200} y={240} w={680} h={160} text="核心结论" color={C.ink} />
      <HandNote f={f} at={b[1]} x={200} y={440} text="手写批注 ≤16 字" />
    </AbsoluteFill>
  );
};
export const SCENES = {S1};
```

配套 `manifests/shots.json` 片段（`flat`/`cel` 需 `zones` `3–5`，手作允许 `1–5`）：

```json
{"id": "S1", "chapter": "第1章", "skeleton": "Stage", "media": ["text"], "live": ["Callout"], "zones": 3, "hero": {"name": "Callout", "size": 160, "kind": "text"}, "transition": "cut", "entry": "rise", "move": "引入", "evidence": "Callout", "cues": [0, 1], "beats": [{"cue": 0, "offset": 0}, {"cue": 1, "offset": 0}], "anchor": {"x": 180, "y": 220, "w": 1200, "h": 520}, "camera": {"intent": "establish", "at": 0, "dur": 38, "x": 960, "y": 540, "from": 1.0, "to": 1.03}}
```

**防坑速记**：1）`CoverPanel tone="wash"` 设 `z={-1}` 羽化、`boxShadow: 'none'`；2）`StageFrame` 主槽宽 `w - pad*2 - railW - 18`，卡片高必用 `fitH()`；3）独立元素 `y ≥ 170` 避开左上徽标；4）同一容器不混用流式标题与绝对定位；5）多子项按 `beats` 错峰出场；6）渲染后清除 `OverlapGate`/`SlotGuard` 告警。

<a id="independent-parts"></a>
## 4. 独立部件与分层契约

`manifests/asset-manifest.json` 经 `scripts/validate-layering.py` 检查：`floating` 须声明 `always-visible`（禁 `normal`），且 `z` 严格高于同镜 `base`/`slot`/`status`。

<a id="lecture-composition"></a>
## 5. 多区构图与模式配比

- **`mode` 配比契约（`validate-fusion.py`）**：`hybrid`（默认：手账 20–75%、组件 ≥25%）、`component`（手账 ≤12%、组件 ≥60%）、`freeform`（手账 ≥40%、多框组件 ≤10%）。
- 主题物 `subject_of_film`（纯软件/抽象可标 `"software"`/`"abstract"` + `subject_why`）全片至少出现一次，否则 P0；安全区占幅目标 60–80%。

<a id="canvas-modes"></a>
## 6. 画布规格（仅 16:9）

设计舞台 `STAGE` = `1920×1080`，合成画布固定为 `2560×1440`（`src/theme/canvas.ts` 与 `validate-visual-plan.py` 双真源交叉校验）；`src/index.tsx` 的 `<Composition id="NotebookVideoFilm" width={2560} ...>` 须内联数字宽度。

<a id="recipes"></a>
## 7. 线稿配方（可选标本速写）

线稿仅用于单件实物标本配尺寸线/手写名（「文字+简笔线稿」超 20% 记 P1）：

| 配方 | 版面 | 必填 |
|---|---|---|
| `hammer` | 满屏大字锤子帧（静止上限 3.0s） | `content.text` |
| `sketch-readout` | 标本速写 + 1–2 张读数卡 | `content.cards`（或 `text`）+ `sketch` |
| `scene-verdict` | 速写 + 结论句 | `content.verdict`（或 `text`） |
| `before-after` | 改前 / 改后双栏 | `content.before`、`content.after` |
| `component-annotated` / `list-icons` / `data-with-object` | 原版式角落加小线稿 | 原版式必填 + `sketch` |

`"sketch"` 块指定 `draw`（`lib:` 或 `shapes:[...]`）、`label`、`place`、`parts` 与 `acts`（`@L1`/`@L1.4`）；`"annotate"` 指向画面元素 `id`；改内置线稿库后跑 `python scripts/linework_index.py --write-crops` 同步 `src/linework/crops.ts`。

<a id="official-skills-exemplar"></a>
## 8. 参考示例

- 组件：`examples/concept-hash-table.story.json`、`examples/code-change-cache.story.json`、`examples/data-ssd-vs-hdd.story.json`。
- 手作/混合：`examples/cell-notebook/`、`examples/recipes/cork-page.story.json`（配 `.treatment.json`）。评审卡见 [rubric.md](rubric.md)。
