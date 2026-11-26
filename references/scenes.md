# 镜头表与场景：骨架、手写场景、部件分层、画布与配方

本篇覆盖分镜表与骨架选择、手写场景（逃生舱）写法、独立部件分层契约、16:9 画布与可选线稿配方。主路线请优先使用 `story.json` + `blueprints/*.json` + `make-video`。

<a id="scene-skeletons"></a>
## 1. 场景骨架与分镜表

- **分镜唯一真源**：`manifests/shots.json` 声明镜头、骨架、介质、转场、入场与运镜；运行 `scripts/resolve-shots.py` 后生成 `manifests/shots.resolved.json` 与 `src/shots.ts`，禁止手改生成物。
- **骨架闭集**：与 `src/skeletons.tsx` 和 `validate-composition.py` 同步校验，相邻镜头应更换骨架（同骨架记 P1，同指纹隔镜重复记 P1）。
- **入场闭集**：`build`、`fade`、`rise`、`slide`、`zoom` 五选一，写未定义值（如 `pop`）判 P0。
- **转场**：`auto` 路线默认一律翻页（`CURL_FRAMES` = 22 帧，WebGL2 卷页探针不过自动退回 CSS `pageflip`）；手写场景可按 `src/insert.tsx` 闭集声明转场。
- **讲法字段**：每镜声明 `move`（叙事动作，同 `move` 连续 ≥3 镜记 P1）与 `evidence`（必须对应场景源码中真实渲染的 JSX 用法，指向不存在或仅注释里的名字判 P0）。

<a id="scene-authoring"></a>
## 2. 场景编写原则

1. **一镜一问题**：在 `story.json` 每镜写明 `$asks`（见 [narration.md](narration.md)），未填记 P1。
2. **草稿纸出现顺序**：每样元素在旁白讲到它时才出现并长出来（`GROW`：最短 12 帧、最长 45 帧、每字 4 帧），禁止开镜预铺（前 6 帧内最多 1 样开始出现）。
3. **不堆纯卡片**：讲解场景必须有活性组件（数据增长、流程推进、代码高亮、图版放大等），纯静态文字卡片堆砌判 P0。
4. **字号与可读性**：
   - `compose-story.py` 画面正文最小字号 `MIN_FONT`（32px，手机可读地板）；
   - 代码静态扫描绝对地板 `MIN_LABEL_FONT`（13px，低于判 P0），标注档 `FONT_LABEL_MIN`（16px，13–15px 记 P1）；
   - 核心展示句地板 `CORE_FONT_FLOOR`（64px）；
   - 单镜画面文字不超过 `SCREEN_READ_BUDGET`（40 加权字，不含字幕）。
5. **关键词自动联动**：在 `story.json` 台词中用 `{{术语}}` 或 `{{术语|元素id}}` 绑定画面元素，念到该词时自动高亮并按安全框搜索推近（不切字）。

<a id="handwritten-scenes"></a>
## 3. 手写场景路线（逃生舱）

当需要逐镜手调版面或编写题目专属可视化时，直接编辑工程的 `manifests/shots.json` 与 `src/scenes.tsx`：

- **帧参数必填**：动画只用帧号驱动，禁止 CSS transition / 定时器 / 随机数。`fxkit` 与 `toolkit`（`Callout`/`Checklist`）组件传 `frame={f}`，其余模块传 `f={f}`，漏传或传错 `tsc` 直接报错。
- **安全色**：文字只用主题令牌 `C.ink`、`C.muted`、`C.*Ink`（对比度 ≥ 4.5:1，由 `validate-presentation.py` 强制检查）。
- **beats 下标安全**：引用 `SHOTS.S1.beats[i]` 时下标不得越界，否则 `validate-composition.py` 判 P0。
- **定制组件**：照 `src/custom/RequestLane.tsx` 编写专属组件，并在 `src/custom/index.ts` 的 `CUSTOM` 表注册，未注册会在 `compose-story.py` 构建期报错。
- **场景函数命名**：每个镜头在 `src/**/*.tsx` 中必须有可识别的场景函数声明（`const S1: React.FC<...>`、`function S1(...)` 等），否则 `validate-composition.py` 报「场景源码不可读」P0。

### 手写场景最小可用范例（真实导出，可直接编译）

```tsx
// src/scenes.tsx（真实导出与必填 props；通过 SCENES 映射按镜号挂载）
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
export const SCENES = {S1}; // 多镜工程把 S1..Sn 全部填入
```

配套 `manifests/shots.json` 最小片段（`flat`/`cel` 要求 `zones` 为 `3–5`，手作允许 `1–5`）：

```json
{"id": "S1", "chapter": "第1章", "skeleton": "Stage", "media": ["text"], "live": ["Callout"], "zones": 3, "hero": {"name": "Callout", "size": 160, "kind": "text"}, "transition": "cut", "entry": "rise", "move": "引入", "evidence": "Callout", "cues": [0, 1], "beats": [{"cue": 0, "offset": 0}, {"cue": 1, "offset": 0}], "anchor": {"x": 180, "y": 220, "w": 1200, "h": 520}, "camera": {"intent": "establish", "at": 0, "dur": 38, "x": 960, "y": 540, "from": 1.0, "to": 1.03}}
```

### 手写场景防坑清单
1. `CoverPanel tone="wash"` 必须设 `z={-1}`、径向羽化与 `boxShadow: 'none'`（正 z 会把整镜压灰）。
2. `StageFrame` 先算 `mainW = w - pad*2 - railW - 18`，`FitCard` 高度用 `fitH()`。
3. 独立元素 `y ≥ 170`，避开左上章节页眉。
4. 禁止在同一容器混用文档流标题与 `position: 'absolute'`（会重叠）；flex 子项若只含绝对定位必须显式给宽高。
5. 定制组件放在 `src/custom/<Name>.tsx` 后，必须在 `src/custom/index.ts` 的 `CUSTOM` 表注册，才能用 `"layout": "custom"`。
6. 场景内禁止调用 `useRawCurrentFrame()`，非活跃镜头须卸载而非 `opacity: 0` 隐藏。
7. 镜内多个子项、对比条或对话的出现时刻不要写死成 `0` 或同一帧，逐个绑到 `beats`，讲到哪条出哪条。
8. 给 `FitCard` 手写高度会裁掉最后一行：高度用 `fitH(rows, padTop, padBottom)` 算。
9. 首次渲染后读控制台：`OverlapGate` 与 `SlotGuard` 的警告清零，或逐条确认是有意覆盖并补 `data-gate-allow`（门禁表见 [checks.md](checks.md#render-gates)）。
<a id="independent-parts"></a>
## 4. 独立部件与分层契约

- 资产分层清单登记在 `manifests/asset-manifest.json`，由 `scripts/validate-layering.py` 强制检查：
  - `floating` 浮层部件必须声明 `always-visible`，禁止使用 `normal` 遮挡契约；
  - `floating` 的 `z` 层级必须严格高于同镜的 `base` / `slot` / `status` 底件。

<a id="lecture-composition"></a>
## 5. 多区讲解构图与画面分工

- `story.json` 顶层 `mode` 是门禁契约（`validate-fusion.py` 校验）：
  - `hybrid`（默认）：手账页 20–75%，组件 ≥25%；
  - `component`：手账页 ≤12%，组件 ≥60%；
  - `freeform`：手账页 ≥40%，多框组件 ≤10%。
- **主题物必须出现**：`subject_of_film` 全片至少出现一次（手账页图版说明 / 墨图标签 / 标本速写 / `see`，全组件片认 `title`/`see`），缺席判 P0。
- **内容占比**：安全区内内容占比目标 60–80%；`<45%` 判 P0（纯文字版式降 P1），`45–60%` 或 `>90%` 记 P1。

<a id="canvas-modes"></a>
## 6. 画布规格（仅 16:9）

- 本技能只支持 16:9 横屏：设计舞台 `STAGE` = `1920×1080`（中心 `960, 540`），输出合成宽度 `2560×1440`（`src/theme/canvas.ts` 与 `validate-visual-plan.py` 双真源一致，由 `validate-skill-consistency.py` 交叉检查）。
- `src/index.tsx` 的 `<Composition id="NotebookVideoFilm" width={2560} ...>` 必须内联声明数字宽度，供视觉规划门禁核对。

<a id="recipes"></a>
## 7. 线稿配方（可选）

- 线稿仅用作**标本速写**（单件实物 + 尺寸线 + 手写名），不拿简笔线稿当概念流程图；「文字 + 简笔线稿」占比超 20% 记 P1。
- **配方**（镜上写 `"recipe"`，可选）：

| 配方 | 版面 | 必填 |
|---|---|---|
| `hammer` | 一句满屏大字（锤子帧，静止上限放宽到 3.0 秒） | `content.text` |
| `sketch-readout` | 一件实物速写 + 1–2 张读数卡 | `content.cards`（或 `content.text`）+ `sketch` |
| `scene-verdict` | 场景速写 + 一句结论 | `content.verdict`（或 `content.text`） |
| `before-after` | 改之前 / 改之后两栏 | `content.before`、`content.after` |
| `component-annotated` / `list-icons` / `data-with-object` | 沿用原版式，角落加一块小线稿 | 原版式的必填 + `sketch` |

- **速写块**（镜上）：`"sketch": {"id": "server", "draw": "lib:server", "label": "服务器", "place": "left|right|center|corner", "parts": [...], "acts": [{"at": "@L1", "do": "enter"}]}`；`@L1` = 本镜第 1 句起声，`@L1.4` = 第 1 句第 4 个字音。
- **批注**（镜上）：`"annotate": [{"target": "<元素 id>", "kind": "circle|underline|arrow|note", "text": "…", "at": "@L2"}]`，`target` 写画面元素 id，找不到会提示可用 id。
- 线稿几何与默认裁切框由 `scripts/linework_index.py` 同步到 `src/linework/crops.ts`，改动库后需重跑 `python scripts/linework_index.py --write-crops`。

<a id="official-skills-exemplar"></a>
## 8. 参考示例

- 组件路线参考：`examples/concept-hash-table.story.json`、`examples/code-change-cache.story.json`、`examples/data-ssd-vs-hdd.story.json`。
- 手作与混合路线参考：`examples/cell-notebook/`、`examples/recipes/cork-page.story.json` 与 `cork-page.treatment.json`。
- 「讲清楚」评审卡：[rubric.md](rubric.md)。
