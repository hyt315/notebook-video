# craft 组件：手作材质（3.3.0）

> 源码：`assets/lecture-template/src/craft/`（`import {…} from './craft'`）。在任何皮肤下都能用（颜色取当前皮肤的
> `THEME.palette` / `THEME.craft`），在 `journal` / `papercut` / `archive` 三套手作皮肤下最协调。
> 导演层先决定"媒介 + 原生动作"（[director-method.md](director-method.md)），再从这里挑组件把它演出来。

## 为什么要这一层

组件库里的 53 件 UI 组件是"信息容器"：会出现、勾选、填充，但不会**晕开、剪开、被写出来、被放大镜放大**。
手作片子的顿悟点几乎都是这种"物质的动作"。craft 组件只做一件事：把成熟的开源绘制库包成
**帧驱动、确定性、门禁友好**的 React 组件。

| 用到的现成项目 | 许可 | 用在哪 |
|---|---|---|
| [perfect-freehand](https://github.com/steveruizok/perfect-freehand) 1.2.3 | MIT | 有压感、起收笔尖的墨线（`InkPath` / `Underline` / `InkCircle` / `HandNote` 引线） |
| [opentype.js](https://github.com/opentypejs/opentype.js) 2.0.0 | MIT | 把霞鹜文楷的字形轮廓取出来，让中文字被"写"出来（`HandLettering`） |
| `@remotion/noise`（已依赖） | Remotion 许可 | 纸边、晕染边缘、手抖的确定性噪声（固定 seed，任一帧可单独重放） |
| `@remotion/paths`（已依赖） | Remotion 许可 | SVG 路径等弧长采样 |

自己写的只有拼装层；纸纤维平铺纹理由 `scripts/dev/make-craft-textures.py` 确定性生成，入库并登记 sha256
（`public/craft/craft-manifest.json`）。

## 纪律（和引擎一致）

- **只用帧号**：每个组件吃 `f`（或一个由 `prog(f, at, dur)` 算出的进度 `p`），没有 `Math.random`、没有 `useState` 计时。
- **字号**：画内必读文字 ≥ `CRAFT_TYPE.label`（48 设计 px ≈ 64 px@1440），一帧 ≤ 3 处画内文字；字幕交给皮肤（72 设计 px = 96 px@1440）。
- **颜色**：墨线默认 `THEME.craft.inkLine`，强调默认 `THEME.craft.accent`（每套皮肤只有一个强调色，别再加）。
- **真实素材必须署名**：`ArchivePhoto` / `PinnedPhoto` / `LoupeMedia` 对 `source:"web"` 的素材总会显示署名，没有关掉的参数。

## 组件一览

### 墨与手写（`ink.tsx`）

| 组件 | 做什么 | 关键参数 |
|---|---|---|
| `InkPath` | 一笔有压感的墨线，按 `p` 从起点画出来 | `d`（SVG 路径）或 `points`；`p`；`size`；`thinning`（0 马克笔 → 0.6 蘸水笔）；`seed` |
| `Underline` | 手划下划线（略上扬、带抖） | `x y w p` |
| `InkCircle` | 手圈一个东西（1.12 圈，首尾交叠） | `cx cy rx ry p` |
| `HandNote` | 钢笔批注：引线先长到目标，字再从左往右写出 | `f at x y text to?`；纸色光晕保证 ≥7:1 |
| `HandLettering` | 一行中文（≤10 字）沿字形轮廓描墨、再填墨 | `f at text x y size perChar` |

辅助：`prog(f, at, dur)`（帧 → 0..1，墨水缓动）、`samplePath(d, n)`、`easeInk`、`CRAFT_TYPE`（字号阶梯）。

```tsx
<InkPath d="M 300 700 C 600 640, 900 760, 1200 690" p={prog(f, b[1], 24)} size={9} seed="arrow" />
<HandNote f={f} at={b[2]} x={1180} y={300} text="一间间小盒子" to={{x: 980, y: 520}} />
<HandLettering f={f} at={10} text="细胞" x={760} y={380} size={CRAFT_TYPE.hero} />
```

### 纸与颜料（`paper.tsx`）

| 组件 | 做什么 | 关键参数 |
|---|---|---|
| `PaperSheet` | 一张自由放置的纸：毛边 / 撕边、纤维、贴面投影、可选胶带；"放下来"入场 | `f x y w h at rot edge='clean'|'deckle'|'torn' tape children` |
| `WashBlob` | 一团水彩：三遍叠色（积水深边）+ 颗粒，按进度晕开 | `f at dur cx cy rx ry color opacity sweep` |
| `CutPaper` | 一片剪纸：任意 SVG 路径（evenodd 内子路径 = 剪掉的洞）、切口亮边、纸厚投影；12 fps 跳帧入场 | `f at d color inset backlit id` |
| `Seal` | 一方红印：3 帧按下、印泥不匀 | `f at x y size text rot` |

另有 `TapeStrip`（和纸胶带）、`FibreOverlay`（纸纤维覆盖层），从 `theme/craft-common` 重新导出。

### 放大镜（`lens.tsx`）

`Loupe` 是"看近一点"的原生动作：镜片落到台面上（影子由大变小），镜片里是同一画面放大 `zoom` 倍。
`render(inside)` 被调两次——镜外 `false`、镜内 `true`——所以**镜片里可以变**：负片转正、一行字亮起、空盒子被刷成房间。
镜片之外的世界不动，不需要相机推近，也不触发取景门禁。

```tsx
<Loupe f={f} x={1240} y={520} r={230} zoom={2.4} target={{x: 900, y: 540}} at={b[2]}
  render={(inside) => <>{/* 同一画面；inside 时多画一层 WashBlob */}</>} />
```

### 真实素材（`media.tsx`）

素材从 `manifests/media.json` 读（`commons-search.py add` 或 `prepare-media.py --add` 写入，见 [commons-media.md](commons-media.md)）。

| 组件 | 做什么 |
|---|---|
| `ArchivePhoto` | 档案件：原比例（不裁不拉）、纸托边、编目签（编号 / 名称 / 署名）。3.7.0：图片区 ≥ 纸托卡片面积 70%（纸托边自动收窄）、编目签字号 ≤ 图高 12%，署名字号不缩；框太小、署名太长时签仍可能和图一样大——给它更大的 w×h |
| `PinnedPhoto` | 贴进手账的照片：白边、胶带或图钉、微倾，下沿手写说明 + 署名 |
| `LoupeMedia` | 放大镜压在素材上；`insideTreatment` 让镜片里换处理（如 `negative` → `none`）。3.7.0：手柄方向按署名框自动选，手柄永不压署名 |
| `MediaAudio` | 真实声音（拟音 / 历史录音），按帧起播，支持 `trimStartSec` / `trimEndSec` |

`treatment`：`none` / `sepia`（做旧，手账里的老照片）/ `duotone` / `negative` / `ink`（高反差黑白，像铜版画）。
`validate-media` 认得这些组件名，按字面量 `w` / `h` 计算放大倍数（>1.5 倍会糊 → P0）。

## 组合配方（手作片常用的几招）

| 想演的 | 组合 |
|---|---|
| "有人第一次看见" | `PinnedPhoto`（真图）→ `Loupe` 压上去 → 镜内 `WashBlob` 把结构刷出来 → `HandNote` 写下当时的原话 |
| "一变多 / 复制" | `CutPaper` 对折一刀 → 两片同时出现（同一路径镜像） → `Seal` 盖章 |
| "这句话最早出自哪" | `ArchivePhoto`（原始扫描件）→ `LoupeMedia` 镜里那行字亮起 → `Underline` |
| 片名 / 结论 | `HandLettering`（≤10 字），落笔后 `Underline` |

## 升级位（下一轮）

- 真水彩笔刷：p5.brush（MIT）的 standalone 版需要 WebGL2，本机 SwiftShader 逐帧重绘成本未知；本轮 `WashBlob` 用 SVG 叠色 + `feTurbulence` 颜料颗粒（分辨率无关）。
- Paper Shaders（Apache-2.0）做纸纹 / 颗粒：同样依赖 WebGL，且 0.0.x API 未稳定。


## 样张：改完先看一眼

`src/craft-sheet.tsx`（合成 `NotebookVideoCraftSheet`，组件 `CraftSheet`）把 12 个组件排在一页上，用当前皮肤的纸面与颜色：

```text
node scripts/notebook-video.mjs craft-sheet ./my-video                       # renders/craft-sheet.png，第 72 帧（全部落定）
node scripts/notebook-video.mjs craft-sheet ./my-video mid.png --frame=18    # 动作进行中
```

真实素材格用 `manifests/media.json` 里的前两张图；还没有图时画虚线占位。样张挂了越界闸门（`CanvasBoundsGate` block），
署名签被挤出画布会直接报错——3.3.0 的第一张样张就靠它抓到了"署名被省略号截断 / 编目签挤出框外"两个问题。
