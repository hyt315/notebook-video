# 组件速查：fxkit、手作材质、线稿、手账页

可直接用的组件：fxkit 动效件、craft 手作材质、线稿（标本速写）与手账页。

本篇各节：

- [fxkit：固定动效组件库（反 PPT 专用）](#fxkit)
- [craft 组件：手作材质](#craft-kit)
- [线稿层（`sketch`）](#linework)
- [手账页 · 把真东西摆到观众眼前](#journal-page)

<a id="fxkit"></a>

## fxkit：固定动效组件库（反 PPT 专用）

`assets/lecture-template/src/fxkit.tsx`，共 9 件，只做 transform/opacity 位移（内部只用 remotion 原生 `spring`/`interpolate`——实现选择，不是"不许引库"），
cel 皮肤锁定（2.5px 墨线 + 硬偏移阴影 + 纯平填充，无渐变无模糊阴影），30fps 确定性（无随机数）。依赖边界见 [technique.md#dependency-policy](technique.md#dependency-policy)。

```tsx
import {FitCard, Typewriter, StampSeal, Funnel, ChatThread, ProgressRing, StaggerList, DiffView, SkeletonCard, fitH} from './fxkit';
```

> **⚠️ 帧参数名（必读）**：fxkit 叫 **`frame`**，模块（`shotkit` / `stagekit` / `media` / `skeletons` / `insert`）叫 **`f`**。
> 帧参数**必填**：传错名或漏传，`tsc` 直接报错（`Property 'frame' is missing`），make-video 的 TypeScript 检查一步就停。**fxkit 传 `frame={f}`，新模块传 `f={f}`。**
> `frame` 是**本镜本地帧**（0 起），不是全局帧；在 `ShotCamera` 内组合时必须传本地帧。

**参数名对照（写场景时照这张表，别凭记忆）**

| 取值 | 模块 / 组件 |
|---|---|
| `frame={f}` | `fxkit` 全部 9 个：`FitCard` `Typewriter` `StampSeal` `Funnel` `ChatThread` `ProgressRing` `StaggerList` `DiffView` `SkeletonCard` |
| `f={f}` | `components/`（**新封装层全部**）、`media`（`ConsoleWindow` `MetricGrid` `StampBanner`）、`stagekit`（`StageFrame` `PhaseRail`）、`skeletons`（`Corridor` `SplitStage` `ZoomStage`）、`insert`（`RevealMask`）、`shotkit`（`ShotCamera` `CoverPanel`） |
| 不收帧参数 | `kit` 的 `PillTag/LineIcon/CheckBadge`、`CoverPanel`、`PhaseRail`（从 `ctx` 取）、`ShotCamera`（内部自取） |

> **写列表错峰**：`StaggerList` 默认 `stagger=6`。18–30 帧的错峰在中文旁白下读成"一个个淡出来"，后几张卡还会拖到旁白讲下一句时才出现（"四项只看到三项"）。
> **同句内相邻开始至少隔 12 帧**（[draftpaper.md#reveal-rules](draftpaper.md#reveal-rules)）；长间隔是叙事节拍，由 `beats` 决定，不由 `stagger` 决定。

### 动效细节（多时钟）

| 组件 | 怎么动 | 为什么 |
|---|---|---|
| `StampSeal` | 砸下 9 帧后一次 `1→1.06→1` 回弹 + 墨圈冲击波 | 没有回弹只读作"圆变小了"，有回弹才是"砸在纸上" |
| `ProgressRing` | 弧 30 帧 / 数字约 24 帧**双时钟**；弧端行进圆点；过冲只给容器 | 同一条曲线让"数字就是那条弧"；数值不能弹（会短暂显示错误的数） |
| `Funnel` | 进度用 `scaleX`，不用 `width` | `width` 是布局属性会重排，且把圆角胶囊拉变形 |
| `DiffView` | 删除行向左快退（12 帧 ease-in）、新增行向右稳进（16 帧 ease-out）+ 落行高亮 | 补丁语义是"一侧拿走、一侧放进"，同向同速会毁掉它 |
| `Typewriter` | 光标 16 帧软阶梯（约 0.53s），不用 9 帧方波 | 9 帧方波在 30fps 下读作频闪；这是全片看得最久的运动 |

### 先看见，再选用

`NotebookVideoShowcase` Composition 把库组件渲染成 **18 页**接触表（select 滤镜按帧号抽每页第 6/21 帧两张中段图，6×6=36 格一张 JPG）：

```text
node scripts/notebook-video.mjs showcase PROJECT_DIR
node scripts/notebook-video.mjs showcase PROJECT_DIR --sheet
```

选组件前先看接触表，比读 props 准确得多。新增组件时必须同时加进接触表。
接触表不是全部：**哪 10 件没上（及为什么）见 [media.md#media-routing §5.1](media.md#51-组件权威索引53-件--选型只查这一处) 的「两处缺口」**。

### 组件一览

> **件的权威索引在 [media.md#media-routing §5.1](media.md#51-组件权威索引53-件--选型只查这一处)**（全技能 53 件，含 fxkit 9 件：用途 / 何时用 / **何时别用** / 接触表页号 / 使用记录）。
> **别处不要再单独维护"有哪些件"的清单**；本节只补 fxkit 的参数与动效细节。

| 组件 | 用途 | 关键 props |
|---|---|---|
| `FitCard` + `fitH()` | 防出格卡片：高度必须经 `fitH()` 显式算出 | `x,y,w,h,pad,borderColor,start,exitStart` |
| `Typewriter` | 打字机：标点分级停顿（句长逗短）、多行排版、块光标闪烁 | `text,fontSize,cps,start,multiline` |
| `StampSeal` | 印章砸下：2.6x→1 回弹，-8° 旋转 | `text,color,size,x,y,start` |
| `Funnel` | 尝试漏斗：宽进窄出 + 计数 + 滴落点 | `x,y,w,rows[{label,sub,count,color,ratio}]` |
| `ChatThread` | 对话气泡：typing 三点 → 气泡 pop，左右交替 | `x,y,w,msgs[{side,text,at}]` |
| `ProgressRing` | 进度环：dashoffset 填充 + 中央标签 | `size,pct,label,color` |
| `DiffView` | 补丁 diff：红删绿加，逐行滑入。给 `before`/`after` 两段文本就由 jsdiff 自动算增删行（推荐）；也可手写 `lines` | `x,y,w,title,before,after,startAt,step` 或 `lines[{k,text,at}]` |
| `SkeletonCard` | 骨架→内容：等待 beats 先占位 | `x,y,w,h,rows,revealAt` |
| `StaggerList` | 级联列表：逐行滑入 + 微旋转，防 bullets 堆砌 | `x,y,w,items,start,stagger` |

### 封装组件层（`src/components/`，27 件）

> 清单来源同上（[media.md §5.1](media.md#51-组件权威索引53-件--选型只查这一处)），这里只留口径与参数要点。
> **「件」的口径**（按 `src/components/index.ts` 的对外 `export` 点算）：**大写 React 组件 27** = 本层实现 27（**无库再导出**）；大写常量 8（`TOPIC_ICONS` `TOPIC_ICON_TONE` `CHART_BOX` `MIN_LABEL_FONT` `FOCUS_MODES` `SHAPES` `PRESENTATIONS` `COMPONENTS_VERSION`）、小写函数/钩子 18、type-only 导出 22（含 `GeoMarker` / `GeoProjection`）都**不算件**。下表列常用 21 个（未列 6 个：`MathBlock` `GeoView` `SankeyChart` `QrCode` `SketchFx` `FocusFx`），完整以 `index.ts` 为准；`COMPONENTS_VERSION` 串为 `components-3.2.0 · 27 件`。

见 [technique.md#dependency-policy](technique.md#dependency-policy)。**场景从这里 import，不要直接 import 原始库。**
帧参数名统一 `f`；颜色只读 `THEME`；登记在 [media.md#media-routing](media.md#media-routing) 两张路由表里。

| 组件 | 做什么 | 参数要点 |
|---|---|---|
| `Accordion` | 手风琴（纯 div）：展开项随帧累积 | `f,items[{title,body,tone}],startAt,step,width,rowH,bodyRows` |
| `Tabs` | 标签页（纯 div）：激活项由帧号决定 | `f,tabs[{key,label,title,body,points,verdict,tone}],startAt,step,width,height` |
| `HighlightCode` | 语法高亮（Shiki，语法色由当前主题调色板生成）+ 行号 + 逐行聚焦（导入以 `src/components/` 的为准） | `f,code,language,startAt,lineStep,width,height,title` |
| `TopicIcon` / `IconWall` | 题材性图标（simple-icons 品牌 + lucide-react 线条，笔画重量已对齐 LineIcon） | `name,size,color,strokeWidth` / `f,names,startAt,step,columns,tile` |
| `Chart` | 图表：刻度与布局由 d3 算，坐标轴/网格/线/面积/柱由 @visx 画，颜色由 THEME 定；7 个 `variant`（line/area/stack/stackExpand/stream/radar/pie） | `f,data,csv,series,labels,variant,startAt,width,height,title,showBars,tone,innerRadius` |
| `StatRow` | 指标卡一行，数字随帧滚动 | `f,startAt,items,width,height` |
| `GlowFrame` | 流光边框（conic-gradient 绑帧号） | `f,width,height,thickness,tone` |
| `ControlStack` | **控件状态随旁白变化**（六种控件，纯 div：开关/复选/单选/滑块/分段/进度） | `f,items,width,rowH,gap,startAt,step,glide`；每行 `steps:[{at,value}]` 是帧→状态的显式表 |
| `OverlayFrame` | **拟真弹层**（dialog/popover/tooltip/menu，纯 div，钉在给定坐标，无 Portal、无异步定位） | `f,kind,x,y,width,steps,title,body,items,confirm,cancel,tone,pointer`；父容器需 `position:relative` |
| `NetworkGraph` | **关系网**（d3-force；固定迭代 + 显式初值 + 包围盒归一化） | `f,nodes,links,startAt,width,height,iterations,nodeR,showLabels` |
| `TreeView` | 目录树 / 组织图 / **矩形树图 / 圆形打包 / 旭日图** | `f,data,startAt,width,height,variant,step,nodeW,nodeH,legend` |
| `ShimmerText` | 文字闪过一道光 | `f,text,fontSize,periodInFrames,sweep` |
| `ClipReveal` | 遮罩擦除（clip-path 按帧推进） | `f,from,durationInFrames,direction` |
| `NoiseJitter` | 有机抖动（同种子同结果） | `f,seed,amplitude,speed` |
| `VerdictBar` | 全宽结论条（填满底部，收束场景） | `f,delay,text,tag,tone,width` |
| `PathDraw` | 描线生长 + 沿线运动的点 / **沿线转向的箭头** | `f,path,startAt,durationInFrames,width,height,viewBox,showDot,showArrow` |
| `MorphShape` | 形状连续变形（方→圆） | `f,fromPath,toPath,startAt,durationInFrames` |
| `ShapeDraw` / `SHAPES` | 参数化几何：星/六边形/三角/圆/星芒/**标注框 callout**/**箭头 arrow**/**心形 heart**/椭圆/矩形 | `f,shape,startAt,size,tone,label` |
| `SceneTransitions` | **全部 20 种官方转场**已登记（`PRESENTATIONS` 的键即转场名；`transitionsTotalFrames()` 算总长） | `children,durations,transition,transitionDuration,width,height,direction` |
| `FitTextBox` | **中文反推字号 + 断行**（自带字体就绪门） | `text,maxLines,boxWidth,maxFontSize,showMeasure` |

### 修辞工具件（`src/toolkit.tsx`，3 件）

场景文件可直接 import。**帧参数名与 fxkit 一致：`frame`。** 选型别按外观挑，先想修辞动作，走 `media.md#media-routing` 的**「修辞动作 → 组件」表**。
下表只列**关键 props**，不是完整签名（另有 `style`，字符类另有 `fontFamily` / `fontWeight` / `letterSpacing` 等；精确签名读 `src/toolkit.tsx`）。

| 组件 | 修辞动作 | 关键 props |
|---|---|---|
| `Callout` | 圈住一处 + 旁边手写标注 | `x,y,w,h,text,textDy,textDx,color,rotate,start,frame` |
| `Checklist` | 列一份清单；`done` 给完成数，序号变对勾 | `items,start,stagger,colors,done,rowH,fontSize,frame` |
| `JumpInText` | 逐字跳入（钩子与收尾，全片 1–2 处） | `items[{text,color,colorActive}],fontSize,start,stagger,frame` |

`Callout` **不带** `data-gate-allow`：圈的椭圆是 `fill="none"` 的 SVG，`OverlapGate` 的 `looksSolid` 本来不当它是遮挡物；标注文字是"另一条信息"，必须参与重叠判定（白名单只留给镜头交接与同位置换信息）。
**缩放容器**（`ZoomStage` 取景框）只给**容器自己**标 `data-fit-skip`：被放大的子层必然溢出取景框，不标则 `CardFitGate` 把"推近"误判成"文字被裁"、在渲染期拦下成片。
`CardFitGate` 判逃生口用 `hasAttribute`（只跳标记者自身）而不是 `closest`——后者会把取景框内所有卡片的真实裁切一起放过。

### 两条铁律

1. **高度必须算出来**：所有文字容器高度经 `fitH()` 计算，禁止手写"看着差不多"的固定高度（否则内容出格）。
2. **坐标看祖先**：`x/y` 永远相对于最近的 positioned 祖先。在 `Paper` 卡片内部是卡片相对坐标；只有直接放在场景根 div 下才是场景坐标。写错会飞出屏，而渲染不报错。

<a id="craft-kit"></a>

## craft 组件：手作材质

> 源码：`assets/lecture-template/src/craft/`（`import {…} from './craft'`）。在任何皮肤下都能用（颜色取当前皮肤的
> `THEME.palette` / `THEME.craft`），在 `journal` / `papercut` / `archive` 三套手作皮肤下最协调。
> 导演层先决定"媒介 + 原生动作"（[director.md#director-method](director.md#director-method)），再从这里挑组件把它演出来。

### 为什么要这一层

53 件 UI 组件是"信息容器"，不会**晕开、剪开、被写出来、被放大镜放大**——而手作片的顿悟点几乎都是这种"物质的动作"。
craft 组件把成熟的开源绘制库包成**帧驱动、确定性、门禁友好**的 React 组件。

| 用到的现成项目 | 许可 | 用在哪 |
|---|---|---|
| [perfect-freehand](https://github.com/steveruizok/perfect-freehand) 1.2.3 | MIT | 有压感、起收笔尖的墨线（`InkPath` / `Underline` / `InkCircle` / `HandNote` 引线） |
| [opentype.js](https://github.com/opentypejs/opentype.js) 2.0.0 | MIT | 把霞鹜文楷的字形轮廓取出来，让中文字被"写"出来（`HandLettering`） |
| `@remotion/noise`（已依赖） | Remotion 许可 | 纸边、晕染边缘、手抖的确定性噪声（固定 seed，任一帧可单独重放） |
| `@remotion/paths`（已依赖） | Remotion 许可 | SVG 路径等弧长采样 |

自己写的只有拼装层；纸纤维平铺纹理由 `scripts/dev/make-craft-textures.py` 确定性生成，入库并登记 sha256
（`public/craft/craft-manifest.json`）。

### 纪律（和引擎一致）

- **只用帧号**：每个组件吃 `f`（或一个由 `prog(f, at, dur)` 算出的进度 `p`），没有 `Math.random`、没有 `useState` 计时。
- **字号**：画内必读文字 ≥ `CRAFT_TYPE.label`（48 设计 px ≈ 64 px@1440），一帧 ≤ 3 处画内文字；字幕交给皮肤（72 设计 px = 96 px@1440）。
- **颜色**：墨线默认 `THEME.craft.inkLine`，强调默认 `THEME.craft.accent`（每套皮肤只有一个强调色，别再加）。
- **真实素材必须署名**：`ArchivePhoto` / `PinnedPhoto` / `LoupeMedia` 对 `source:"web"` 的素材总会显示署名，没有关掉的参数。

### 组件一览

#### 墨与手写（`ink.tsx`）

| 组件 | 做什么 | 关键参数 |
|---|---|---|
| `InkPath` | 一笔有压感的墨线，按 `p` 从起点画出来 | `d`（SVG 路径）或 `points`；`p`；`size`；`thinning`（0 马克笔 → 0.6 蘸水笔）；`seed` |
| `Underline` | 手划下划线（略上扬、带抖） | `x y w p` |
| `InkCircle` | 手圈一个东西（1.12 圈，首尾交叠） | `cx cy rx ry p` |
| `HandNote` | 钢笔批注：引线先长到目标，字再从左往右写出 | `f at x y text to?`；纸色光晕保证 ≥7:1 |
| `HandLettering` | 一行中文（≤10 字）沿字形轮廓描墨、再填墨 | `f at text x y size perChar` |

辅助：`prog(f, at, dur)`（帧 → 0..1，墨水缓动）、`samplePath(d, n)`、`easeInk`、`CRAFT_TYPE`（字号阶梯）。

**「空场」的正解**：画面显得空时，先问「主体还缺哪一层属于它的东西」——
有尺寸就用 `InkPath` + `HandNote` 标尺寸，由很多小单元组成就用 `LoupeMedia` / `Loupe` 拎一个出来看近。
不要放大卡片凑面积，也不要往空白处另起一句说明（判据见 composition-gate 的「横向空洞」一节）。

```tsx
<InkPath d="M 300 700 C 600 640, 900 760, 1200 690" p={prog(f, b[1], 24)} size={9} seed="arrow" />
<HandNote f={f} at={b[2]} x={1180} y={300} text="一间间小盒子" to={{x: 980, y: 520}} />
<HandLettering f={f} at={10} text="细胞" x={760} y={380} size={CRAFT_TYPE.hero} />
```

#### 纸与颜料（`paper.tsx`）

| 组件 | 做什么 | 关键参数 |
|---|---|---|
| `PaperSheet` | 一张自由放置的纸：毛边 / 撕边、纤维、贴面投影、可选胶带；"放下来"入场 | `f x y w h at rot edge='clean'|'deckle'|'torn' tape children` |
| `WashBlob` | 一团水彩：三遍叠色（积水深边）+ 颗粒，按进度晕开 | `f at dur cx cy rx ry color opacity sweep` |
| `CutPaper` | 一片剪纸：任意 SVG 路径（evenodd 内子路径 = 剪掉的洞）、切口亮边、纸厚投影；12 fps 跳帧入场 | `f at d color inset backlit id` |
| `Seal` | 一方红印：3 帧按下、印泥不匀 | `f at x y size text rot` |

另有 `TapeStrip`（和纸胶带）、`FibreOverlay`（纸纤维覆盖层），从 `theme/craft-common` 重新导出。

#### 放大镜（`lens.tsx`）

`Loupe` 是"看近一点"的原生动作：镜片落到台面上（影子由大变小），镜片里是同一画面放大 `zoom` 倍。
`render(inside)` 被调两次——镜外 `false`、镜内 `true`——所以**镜片里可以变**：负片转正、一行字亮起、空盒子被刷成房间。
镜片之外的世界不动，不需要相机推近，也不触发取景门禁。

```tsx
<Loupe f={f} x={1240} y={520} r={230} zoom={2.4} target={{x: 900, y: 540}} at={b[2]}
  render={(inside) => <>{/* 同一画面；inside 时多画一层 WashBlob */}</>} />
```

#### 真实素材（`media.tsx`）

素材从 `manifests/media.json` 读（`commons-search.py add` 或 `prepare-media.py --add` 写入，见 [media.md#commons-media](media.md#commons-media)）。

| 组件 | 做什么 |
|---|---|
| `ArchivePhoto` | 档案件：原比例（不裁不拉）、纸托边、编目签（编号 / 名称 / 署名）。图片区 ≥ 纸托卡片面积 70%（纸托边自动收窄）、编目签字号 ≤ 图高 12%，署名字号不缩；框太小、署名太长时签仍可能和图一样大——给它更大的 w×h。署名签不进字幕带：整件底边自动收在设计坐标 y = 874（字幕框顶 934 再让 60，招牌推镜后也不压字幕）以上，框伸进字幕带时图会相应缩小 |
| `PinnedPhoto` | 贴进手账的照片：白边、胶带或图钉、微倾，下沿手写说明 + 署名 |
| `LoupeMedia` | 放大镜压在素材上；`insideTreatment` 让镜片里换处理（如 `negative` → `none`）。手柄方向按署名框自动选，手柄永不压署名 |

`treatment`：`none` / `sepia`（做旧，手账里的老照片）/ `duotone` / `negative` / `ink`（高反差黑白，像铜版画）。
`validate-media` 认得这些组件名，按字面量 `w` / `h` 计算放大倍数（>1.5 倍会糊 → P0）。

### 组合配方（手作片常用的几招）

| 想演的 | 组合 |
|---|---|
| "有人第一次看见" | `PinnedPhoto`（真图）→ `Loupe` 压上去 → 镜内 `WashBlob` 把结构刷出来 → `HandNote` 写下当时的原话 |
| "一变多 / 复制" | `CutPaper` 对折一刀 → 两片同时出现（同一路径镜像） → `Seal` 盖章 |
| "这句话最早出自哪" | `ArchivePhoto`（原始扫描件）→ `LoupeMedia` 镜里那行字亮起 → `Underline` |
| 片名 / 结论 | `HandLettering`（≤10 字），落笔后 `Underline` |

### 样张：改完先看一眼

`src/craft-sheet.tsx`（合成 `NotebookVideoCraftSheet`，组件 `CraftSheet`）把 12 个组件排在一页上，用当前皮肤的纸面与颜色：

```text
node scripts/notebook-video.mjs showcase ./my-video --craft                   # renders/craft-sheet.png，第 72 帧（全部落定）
node scripts/notebook-video.mjs showcase ./my-video mid.png --craft --frame=18  # 动作进行中
```

真实素材格用 `manifests/media.json` 前两张图，没有图时画虚线占位。样张挂越界闸门（`CanvasBoundsGate` block）：署名被省略号截断、编目签挤出框外都直接报错。

<a id="linework"></a>

## 线稿层（`sketch`）

> 画面 = **组件（信息）+ 线稿（认出来）+ 讲解层（连起来）**。线稿只让观众一眼认出「在讲什么东西」，**不画内部结构**；要拆机制请换原理片工具。

### 1. 一条线稿长什么样

写在 story.json 的**镜头**上（和 `recipe` 同级）：

```json
"recipe": "sketch-readout",
"sketch": {
  "id": "rocket",
  "draw": "lib:rocket",
  "place": "left",
  "parts": {"stage1": "第一级", "stage2": "第二级"},
  "acts": [
    {"at": "@L1", "do": "enter"},
    {"at": "@L1.4", "do": "point", "target": "stage1"},
    {"at": "@L2.3", "do": "drop", "target": "stage1"}
  ]
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `draw` | 是 | `lib:<名字>`（内置 30 个）/ `shapes:[…]`（自拼 ≤10 形） |
| `place` | 否 | `left`（默认）/ `right` / `center` / `corner`；配方会覆盖 |
| `parts` | 否 | 部位 id → 上屏的名字（不写就用库里自带的「第一级」） |
| `acts` | 否 | 不写 = 在本镜第 1 句开始时描出（等同 `[{"at": "@L1", "do": "enter"}]`）；动词见下 |
| `keep` | 否 | 下一镜沿用同一线稿（只保持状态，没有连续演变系统） |

**时间写法**：`"@L1"` = 本镜第 1 句开始；`"@L1.4"` = 第 1 句第 4 个字音；数字 = 本镜帧号。

### 2. 七个动词（闭集，只这七个）

| 动词 | 画面 | 什么时候用 |
|---|---|---|
| `enter` | 线稿按部位依次描出来（整幅 24–45 帧 = 0.8–1.5 秒，部位越多越长） | 这一镜第一次出现 |
| `point` | 点一个部位：换强调色加粗、其余压暗、旁边手写名字 | 旁白点名某个部位 |
| `drop` | 部位脱离、带一点旋转落出画面 | 「烧完就扔」「这一段不要了」 |
| `swap` | 同一位置换状态（满→空、贵→便宜） | 前后对比，但只想画一条线稿 |
| `count` | 复制成 N 个 | 数量、规模（`"n": 5`） |
| `mark` | 旁边落一个手绘勾/叉/圈（`"mark": "check"`） | 结论落定 |
| `exit` | 线稿退场 | 这一镜不再需要它 |

### 3. 内置 30 个（`lib:<名字>`）

火箭 `rocket` · 卫星 `satellite` · 地球 `earth` · 灯泡 `bulb` · 电池 `battery` · 手机 `phone` ·
笔记本 `laptop` · 服务器 `server` · 芯片 `chip` · 云 `cloud` · 房子 `house` · 汽车 `car` ·
钞票 `money` · 硬币 `coin` · 购物车 `cart` · 钱包 `wallet` · 人 `person` · 人群 `crowd` ·
对话气泡 `bubble` · 书 `book` · 笔记本 `notebook` · 日历 `calendar` · 钟表 `clock` ·
放大镜 `magnifier` · 锁 `lock` · 钥匙 `key` · 文件 `file` · 邮件 `mail` · 工厂 `factory` · 树 `tree`

常用部位 id：`rocket` → `payload` / `stage1` / `stage2`；`phone` → `body` / `screen` / `button`；
`house` → `roof` / `body` / `door` / `window`；`person` → `head` / `body` / `arms` / `legs`。
其余线稿的部位见 `assets/lecture-template/src/linework/library.ts` 的 `parts`。

### 4. 自拼（库里没有那个东西时）

```json
"draw": "shapes:[{\"k\":\"rect\",\"x\":20,\"y\":30,\"w\":60,\"h\":40},{\"k\":\"circle\",\"cx\":50,\"cy\":20,\"r\":12},{\"k\":\"line\",\"x1\":50,\"y1\":70,\"x2\":50,\"y2\":90}]"
```

- 5 种基本形：`rect` / `circle` / `path` / `line` / `dots`；最多 12 个，超过的部分不会画出来，`validate-fusion` 会提示。
- 坐标是线稿自己的 0–100 方框；**≤10 个形**，超过会被门禁判「画得太深了」。
- 画法三步：**轮廓剪影**（一眼认得出）→ 加 **1–2 个识别特征**（火箭的舷窗、房子的门）→ 停。

### 5. 硬边界（门禁会拦）

| 可以画 | 不画 |
|---|---|
| 外形轮廓、门窗、屏幕、把手这类识别特征 | 剖面、内部结构、零件拆解、爆炸图 |
| 出现、指一处、一段脱落、变满/变空、复制、打勾 | 粒子流、管路循环、部件级连续演变 |
| 一个 3–6 个元素的小场景 | 完整机制示意图 |
| ≤10 个形 | >12 个形（P1「画得太深了」） |

### 6. 皮肤笔触

线稿只读皮肤自己的墨色与一个强调色，不自带颜色：

- 五个皮肤用同一种笔触：等宽 SVG 描边、圆角端点。线宽基准 flat / journal / papercut / archive 为 0.95、cel 为 1.35（viewBox 单位，随缩放修正）；墨色读 `THEME.craft.inkLine`。

单帧强调色面积 ≤15%：`point` 只给一个部位换色加粗，其余压暗，不铺色块。

### 7. 常见错误

| 现象 | 原因 | 改法 |
|---|---|---|
| 线稿没出现 | `draw` 名字拼错 | 对照第 3 节 |
| 部位点不亮 | `target` 不是这个线稿的 part id | 看 library.ts 的 `parts` |
| 线稿被裁出画外 | 镜头推近 | 有线稿的镜头引擎会自动保持全景；不要手写 `cinema` |
| 画得像原理图 | 形太多 / 画了内部 | 删到 ≤10 形，只留轮廓与 1–2 个特征 |
| 单部位特写只剩半边 | 手写了 `fit` 但比图形小 | `python scripts/linework_index.py --geometry` 会点名是哪一边超出；改大 `fit` 或删掉它改用缺省框 |
| 单部位特写里那个部位很小 | 部位没写 `fit`，用了整图取景 | 正常情况下不会：没写 `fit` 时引擎用 `crops.ts` 里按真实包围盒算出的缺省框 |

**取景框（`fit`）由几何决定，不靠眼估。**

- 线稿级 `fit`：[x, y, w, h]，0–100 坐标，是引擎的 viewBox。它必须盖住全部基本形，否则内容画到框外。
- 部位级 `fit`：只在这个部位**被单独选中**时生效（`parts: ["hull"]`）。多部位组合始终用整图坐标，相对位置才不会漂。
- 没写部位级 `fit` 时用 `src/linework/crops.ts` 里的缺省框（`python scripts/linework_index.py --write-crops` 生成，
  按真实包围盒留 12% 边，短边不小于 16）。改了 `library.ts` 就要重跑一次，`validate-skill` 会检查两者是否同步。

### 8. 笔法（仿 a2e 的线稿技巧）

线稿像剪贴画的根因不是形状不够多，而是**线只有一档、标注压在物体上、每个部位同样用力**。口径：

1. **三档线宽**（相对基准）：轮廓 1.0、细节件 0.72（偏暖灰）、被 `point` 点名的部位 1.35（强调色）。`detail: true` 的部位（窗、按钮、指示灯、刻度、螺丝）自动走细节档；不要把所有线都加粗。
2. **一条连续的轮廓剪影**：先画闭合外形（火箭 = 头锥 + 箭体 + 尾翼 + 喷口一条 path），再叠分段线、舷窗、尾焰等细节。`rect` 叠 `rect` 一定像积木。
3. **标注在线稿外侧**：`point` 的手写名字带细引线和起点圆点，放在轮廓外（右半 → 往左，左半 → 往右）；**不要压在物体上**。名字 ≤6 个字，是名词（「第一级」），不是句子。
4. **填色只做辅助**：`wash` 是 8% 强调色；`accent` 只给尾焰、钥匙这类「小而关键」的实心件。
   单帧强调色面积 ≤15%，一幅画里不超过 3 种颜色。
5. **比例**：主体占画面约 2/3；同一幅画里大小合常识（塔比人高）。
6. **只加 2–4 处细节**：舷窗、门、指示灯、刻度，够认出即可；不要塞满。

判断标准：把画面缩到手机大小，还能一眼认出是什么；把颜色去掉，轮廓仍然立得住。

### 9. 页内墨图的动作（`content.ink.acts`）

手账页上的小图不是装饰：**讲到哪一句，纸上就发生对应的一件事**。写在 `content.ink.acts`，`at` 写法与 `shot.sketch` 相同（写「第几句旁白」，帧号由 compose 换算，不手算）。

```json
"ink": {
  "draw": "lib:chiplog",
  "label": "船尾抛板与测速绳",
  "parts": ["hull", "line"],
  "acts": [
    {"do": "point", "target": "line", "at": "@L2", "text": "等距的结"},
    {"do": "mark",  "target": "line", "mark": "circle", "at": "@L2.4"}
  ]
}
```

- 开放动词：`point` / `drop` / `swap` / `mark` / `exit`。`enter` 由 `content.ink.at` 决定；
  `count`（复制 n 份）会撞版面，暂不开放。写错动词、写错部位名、`target` 不在 `parts` 里，都是**构建期错误**
  （不是渲染期空白），报错会列出可用值。
- 一镜 1–3 个动作。动作要改变观众的理解——指一处、换一态、划掉一个误解、圈出结论；
  只是「让画面动起来」的多余动作会被提示。
- 不写 `acts` 时画面与旧版完全一致（只有入场），旧 story 不用改。

### 10. 跨镜复现：有意回扣 vs 无意重复（`recallOf` / `variantOf`）

同一张线稿常要**再出现一次**（回忆、前后对照、结论回扣），不该一律拦；但「同图 + 同局部 + 同动作」再现又没说清为什么，观众读到的就是「这段我看过」。

在 shot（或 content）上写意图：

```json
{"layout": "page", "recallOf": "S1",
 "content": {"ink": {"draw": "lib:chiplog", "parts": ["hull", "line"],
                     "label": "回到船尾的那根绳", "acts": [{"do": "mark", "target": "line", "at": "@L1"}]}}}
```

- `recallOf` ：回扣先前那张图（回忆 / 结论回扣）
- `variantOf`：同一主题物的另一态（前后对照）
- 两者都必须指向**更早**的镜头 id。

门禁只拦**无意**的完全重复。构图（`parts`）、动作（`acts`）、信息量（`label`）三者
**至少一项有变化**即放行：

| 情况 | 结果 |
|---|---|
| 同图同局部同动作，**连续**两镜，无意图 | 拦（换 parts / acts，或写 `recallOf`） |
| 同图同局部同动作同标签，隔镜，无意图 | 拦（同上） |
| 标了 `recallOf` 但构图、动作、信息量全同 | 拦（那是复制，不是复现） |
| 标了 `recallOf` + 换了 label / acts | 放行（正解） |
| 同图不同局部（如 chiplog 的船身 vs 木板） | 放行（本来就不是重复） |
| 同图同局部，换了动作 | 放行（演示变了） |

`content.ink` / `content.figure` / `shot.sketch` 三条路径都进同一道检查，构建期就报，不靠作者记。

<a id="journal-page"></a>

## 手账页 · 把真东西摆到观众眼前

> 一句话：**组件讲概念，手账页给证据。** 观众要先看见那个东西，才愿意听你解释它。

手账页上的东西同样按出现规则出现：图版 / 照片可以整件贴上，放大镜、手写、印章都等讲到它的那句再出现，见 [draftpaper.md#reveal-rules](draftpaper.md#reveal-rules)。

### 为什么是手账页

简笔线稿 + 自动标注像剪贴画：能说明「这里有个火箭」，说不清「这枚火箭为什么这样」。抓住人的是真东西（见 [examples/cell-notebook](../examples/cell-notebook/README.md)：49 秒讲「细胞为什么叫细胞」，导演层与分镜已归档，**仅文档**、不能直接跑；可运行的精简版是 `examples/recipes/cork-page.story.json`）：

| | 线稿当解释图 | 手账页 |
|---|---|---|
| 容器 | 白底 + 卡片框 | **纸**（点阵 / 牛皮 / 横线）+ 手写页眉 |
| 主体 | 矢量简笔 | **真实图版**（1665 年原版铜版画、显微照、标本照），装裱在白卡纸上 |
| 说服力 | 「我画给你看」 | 「这是原件，你自己看」 |
| 细节 | 画不了那么细 | 放大镜压上去，镜内是原图 3 倍 |
| 结论 | 像课件 | 像一个人在笔记本上研究给你看 |

所以 **手账页是承载层，线稿降级为可选的标本速写**。

### 一页由六件东西组成

1. **纸**：皮肤 `journal`（`public/bg/journal/*.png`，点阵 / 牛皮 / 网格 / 横线 / 水彩）。容器是纸，**不要套圆角卡片**。
2. **真图版**：`ArchivePhoto` —— 白卡纸装裱、细阴影、下方编目签（编目号 + 图名 + CC BY 署名）。
3. **手写页眉**：`No.03 小盒子` 这种，由模板页眉自动生成，编号来自镜序。
4. **手写大字**：`HandLettering`，一页只写一个「年份 / 数字 / 词」，是页标题，不是正文。
5. **印章**：`Seal`，2–3 字，朱砂，压在第一句末尾。
6. **手写说明**：`HandNote`，一行 ≤16 字，写在第二句。

可选：**放大镜**（`LoupeMedia`）、**引线**（`InkPath`，把说明指到图版上的某一点）。

### 三种页型

#### ① `plate` · 图版页 —— 「这是原件」

```json
{"role": "context", "layout": "page",
 "lines": ["1665 年，胡克削下一片软木。", "放到显微镜下。"],
 "content": {"page": "plate", "media": "hooke-plate",
             "catalogue": "Schem. XI", "title": "《显微图谱》1665",
             "big": "1665", "stamp": "胡克", "note": "第十八篇 · 软木"}}
```

- `big` 是**一个**年份 / 数字 / 词，≤8 字（超了会自动降字号并提示）。
- `stamp` 2–3 字，盖在人名 / 学派 / 结论上。
- `note` 一行，写「第几篇 / 什么材料」这类出处信息，不重复字幕。

#### ② `loupe` · 放大镜页 —— 「你看这里」

```json
{"content": {"page": "loupe", "media": "hooke-plate", "catalogue": "Schem. XI",
             "title": "《显微图谱》1665", "big": "细胞", "note": "cells · 小房间",
             "look": [0.25, 0.42], "zoom": 2.6}}
```

- `look` 是镜心在图版上的**相对坐标**（0–1）。`zoom` 默认 2.6；>3 会糊，`validate-media` 会拦。
- 放大镜是「看」这个动作本身。**一个片子最多用 1–2 次**，多了就是重复。
- 招牌镜用这个：把「别人没看见的东西」放大给观众看。

#### ③ `specimen` · 标本页 —— 「这是那件东西」（线稿唯一该出现的地方）

一件东西 + 尺寸线 + 手写名。用 `layout: "statement"` + `sketch`：

```json
{"layout": "statement",
 "content": {"text": "一枚软木塞，直径两厘米。"},
 "sketch": {"draw": "lib:cork", "label": "软木塞", "place": "left",
            "acts": [{"at": "@L1", "do": "enter"}, {"at": "@L2", "do": "point", "target": "body"}]}}
```

规矩：只画**外形**和 1–2 个识别特征；不画剖面、不画内部结构（要讲内部就放真图版）。
标签 ≤6 字，是这个东西的**名字**，不是一句话。

### 页内示意图（可选）· `content.figure`

文字旁随手画的小图——线稿在手账页上**唯一合适的位置**：不解释概念，只帮观众认出「说的是哪件东西」。

```json
{"content": {"page": "plate", "media": "hooke-plate", "big": "1665", "note": "第十八篇 · 软木",
             "figure": {"draw": "lib:book", "label": "《显微图谱》", "size": 300}}}
```

- 尺寸硬压 360（画宽 ≤19%）；再大就变成「线稿当解释图」，实测比不画更差。
- 只用 30 个内置库里的**实物**（书 / 手机 / 电池 / 芯片 / 树 / 锁……）；
  流程、对比、数量关系一律用组件，不要画。
- 一页最多一张，放在图版对侧的空白处（compose 固定给左下）。
- 线宽三档、外置标注这些技法见 [components.md#linework](components.md#linework)；这里只当速写用，不点名、不拆解。

### 与组件怎么配

```
手账页（承载） → 组件（讲解） → 手账页（新证据 / 放大） → 组件（收束）
```

- 手账页占 **25–75%**，组件 **≥25%**（`validate-fusion` 判 P1）。
- 连续两页手账页之间要有组件，否则节奏塌（compose 会提示"与上一镜同为 page 版式"）。
- 组件负责回答：**为什么 / 差多少 / 分几步 / 怎么选**。手账页负责回答：**它是什么 / 长什么样 / 谁在什么时候记下来的**。

### 素材从哪来

先搜 `node scripts/notebook-video.mjs commons-search <工程> "cork cells microscope"`，再 `commons-search.py add`（写 `manifests/media.json` + 下载到 `public/media/`）；图版 id 就是 `content.media`。
署名由 `ArchivePhoto` 自动显示（CC BY 要求完整署名，组件没有关闭它的参数）。流程同 [director.md#director-method](director.md#director-method) 的素材一节。

没有可用素材时：**宁可换成组件，也不要临时画一张线稿冒充**。

### 禁忌

- ❌ 给手账页套圆角卡片 / 阴影框（立刻变回 PPT）
- ❌ 把真图版塞进"浏览器窗口"外壳（那是截图，不是档案）
- ❌ 一页写两句以上的手写大字（手账的标题只有一个）
- ❌ 用简笔线稿"解释"抽象概念（流程、对比、数量关系用组件）
- ❌ 放大倍数 >3（糊）；图版在画面里 <25% 宽（看不清，等于没放）
