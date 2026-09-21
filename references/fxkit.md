# fxkit：固定动效组件库（反 PPT 专用）

`assets/lecture-template/src/fxkit.tsx`，v3 共 19 个组件，只做 transform/opacity 位移
（内部只用 remotion 原生 `spring`/`interpolate`——这是实现选择，不是"不许引库"的意思），
cel 皮肤锁定（2.5px 墨线 + 硬偏移阴影 + 纯平填充，无渐变无模糊阴影），
30fps 确定性（无随机数）。依赖边界见 [dependency-policy.md](dependency-policy.md)。用法：

```tsx
import {FitCard, Typewriter, StampSeal, Funnel, ChatThread, ProgressRing, StaggerList, DiffView, SkeletonCard, fitH} from './fxkit';
```

> **⚠️ 帧参数名（实测踩过，必读）**：fxkit 的帧参数叫 **`frame`**，而 v2.10 新增模块
> （`shotkit` / `stagekit` / `media` / `skeletons` / `insert`）的帧参数叫 **`f`**。
> 给 fxkit 组件传 `f={f}` 会被**静默忽略**，组件回落到 `useCurrentFrame()`（全局帧），
> 于是动画整体错位，甚至抛 `Frame NaN`。**fxkit 传 `frame={f}`，新模块传 `f={f}`。**
>
> 另外每个组件的 `frame` 语义是**本镜本地帧**（0 起），不是全局帧；在 `ShotCamera` 内组合时必须传本地帧。
>
> **这条以前只是文档，现在有门禁**：`python scripts/validate-frame-props.py PROJECT_DIR` 逐个标签核对
> 参数名，写错即 P0。实测两支自带样板片各有 5–6 处违反，印章 / Funnel / 打字机的进场动画因此长期失效
> （组件回落到全局帧后，`start={局部节拍}` 早已过去，元素直接以完成态出现）。**改完场景文件先跑它。**

**参数名对照（写场景时照这张表，别凭记忆）**

| 取值 | 模块 / 组件 |
|---|---|
| `frame={f}` | `fxkit` 全部 9 个：`FitCard` `Typewriter` `StampSeal` `Funnel` `ChatThread` `ProgressRing` `StaggerList` `DiffView` `SkeletonCard` |
| `f={f}` | `components/`（**新封装层全部**）、`media`（`ConsoleWindow` `MetricGrid` `StampBanner`）、`stagekit`（`StageFrame` `PhaseRail`）、`skeletons`（`Corridor` `SplitStage` `ZoomStage`）、`insert`（`RevealMask`）、`shotkit`（`ShotCamera` `CoverPanel`） |
| 不收帧参数 | `kit` 的 `PillTag/LineIcon/CheckBadge`、`CoverPanel`、`PhaseRail`（从 `ctx` 取）、`ShotCamera`（内部自取） |

> **写列表错峰（v2.11 校准）**：`StaggerList` 默认 `stagger=6`。实测 18–30 帧的错峰在中文旁白下会读成
> "一个个淡出来"，观众看不到"成串落下"，还会让后几张卡在旁白已经讲下一句时才出现（用户会报"四项只看到三项"）。
> **同句内错峰 ≤8 帧**；真正需要长间隔的是叙事节拍，那应该由 `beats` 决定，不是由 `stagger` 决定。

## 本轮动效升级（v3，多时钟）

| 组件 | 改了什么 | 为什么 |
|---|---|---|
| `StampSeal` | 砸下 9 帧后加一次 `1→1.06→1` 回弹 + 墨圈冲击波 | 只有"压下去"的印章只是"圆变小了"；有回弹才读作"砸在纸上" |
| `ProgressRing` | 弧 30 帧 / 数字约 24 帧**双时钟**；弧端加行进圆点；过冲只给容器 | 同一条曲线会让"数字就是那条弧"；数值类动画不能弹（会短暂显示错误的数） |
| `Funnel` | 进度由 `width` 改 `scaleX` | `width` 是布局属性会重排，且会让圆角胶囊在动画中途被拉变形 |
| `DiffView` | 删除行向左快退（12 帧 ease-in）、新增行向右稳进（16 帧 ease-out）+ 落行高亮 | 补丁的语义就是"一侧拿走、一侧放进"，同向同速会毁掉这个语义 |
| `Typewriter` | 光标 9 帧方波 → 16 帧软阶梯（约 0.53s） | 9 帧方波在 30fps 下读作频闪；这是全片看得最久的运动 |

## 先看见，再选用

`NotebookVideoShowcase` Composition 把库组件渲染成 **9 页**接触表（1fps 抽帧即一页一图）：

```text
node scripts/notebook-video.mjs showcase PROJECT_DIR
node scripts/notebook-video.mjs showcase-sheet PROJECT_DIR
```

选组件前先看接触表，比读 props 文档准确得多。新增组件时必须同时加进接触表。

## 组件一览

| 组件 | 用途 | 关键 props |
|---|---|---|
| `FitCard` + `fitH()` | 防出格卡片：高度必须经 `fitH()` 显式算出 | `x,y,w,h,pad,borderColor,start,exitStart` |
| `Typewriter` | 打字机：标点分级停顿（句长逗短）、多行排版、块光标闪烁 | `text,fontSize,cps,start,multiline` |
| `StampSeal` | 印章砸下：2.6x→1 回弹，-8° 旋转 | `text,color,size,x,y,start` |
| `Funnel` | 尝试漏斗：宽进窄出 + 计数 + 滴落点 | `x,y,w,rows[{label,sub,count,color,ratio}]` |
| `ChatThread` | 对话气泡：typing 三点 → 气泡 pop，左右交替 | `x,y,w,msgs[{side,text,at}]` |
| `ProgressRing` | 进度环：dashoffset 填充 + 中央标签 | `size,pct,label,color` |
| `DiffView` | 补丁 diff：红删绿加，逐行滑入 | `x,y,w,title,lines[{k,text,at}]` |
| `SkeletonCard` | 骨架→内容：等待 beats 先占位 | `x,y,w,h,rows,revealAt` |
| `StaggerList` | 级联列表：逐行滑入 + 微旋转，防 bullets 堆砌 | `x,y,w,items,start,stagger` |

## 封装组件层（`src/components/`，22 件）

见 [dependency-policy.md](dependency-policy.md)。**场景从这里 import，不要直接 import 原始库。**
帧参数名统一 `f`；颜色只读 `THEME`；登记在 [media-routing.md](media-routing.md) 两张路由表里。

| 组件 | 做什么 | 参数要点 |
|---|---|---|
| `Accordion` | 手风琴（Radix）：展开项随帧累积 | `f,items[{title,body,tone}],startAt,step,width,rowH,bodyRows` |
| `Tabs` | 标签页（Radix）：激活项由帧号决定 | `f,tabs[{key,label,title,body,points,verdict,tone}],startAt,step,width,height` |
| `HighlightCode` | 语法高亮 + 行号 + 逐行聚焦（**与 toolkit 的 `CodeBlock` 不同物**） | `f,code,language,startAt,lineStep,width,height,title` |
| `TopicIcon` / `IconWall` | 题材性图标（react-icons：`fa` 品牌 + `fi`/`lu` 线条，笔画重量已对齐 LineIcon） | `name,size,color,strokeWidth` / `f,names,startAt,step,columns,tile` |
| `Chart` | d3 图表：刻度与路径由 d3 算，画由 THEME 定；7 个 `variant`（line/area/stack/stackExpand/stream/radar/pie） | `f,data,csv,series,labels,variant,startAt,width,height,title,showBars,tone,innerRadius` |
| `StatRow` | 指标卡一行，数字随帧滚动 | `f,startAt,items,width,height` |
| `GlowFrame` | 流光边框（conic-gradient 绑帧号） | `f,width,height,thickness,tone` |
| `ControlStack` | **控件状态随旁白变化**（Radix 六个纯受控 primitive：开关/复选/单选/滑块/分段/进度） | `f,items,width,rowH,gap,startAt,step,glide`；每行 `steps:[{at,value}]` 是帧→状态的显式表 |
| `OverlayFrame` | **拟真弹层**（Radix dialog/popover/tooltip/dropdown-menu；Portal 已指到画面内） | `f,kind,x,y,width,steps,title,body,items,confirm,cancel,tone,pointer`；父容器需 `position:relative` |
| `NetworkGraph` | **关系网**（d3-force；固定迭代 + 显式初值 + 包围盒归一化） | `f,nodes,links,startAt,width,height,iterations,nodeR,showLabels` |
| `TreeView` | 目录树 / 组织图 / **矩形树图 / 圆形打包 / 旭日图** | `f,data,startAt,width,height,variant,step,nodeW,nodeH,legend` |
| `ShimmerText` | 文字闪过一道光 | `f,text,fontSize,periodInFrames,sweep` |
| `ClipReveal` | 遮罩擦除（clip-path 按帧推进） | `f,from,durationInFrames,direction` |
| `NoiseJitter` | 有机抖动（同种子同结果） | `f,seed,amplitude,speed` |
| `VerdictBar` | 全宽结论条（填满底部，收束场景） | `f,delay,text,tag,tone,width` |
| `PathDraw` | 描线生长 + 沿线运动的点 / **沿线转向的箭头** | `f,path,startAt,durationInFrames,width,height,viewBox,showDot,showArrow` |
| `MorphShape` | 形状连续变形（方→圆） | `f,fromPath,toPath,startAt,durationInFrames` |
| `ShapeDraw` / `SHAPES` | 参数化几何：星/六边形/三角/圆/星芒/**标注框 callout**/**箭头 arrow**/**心形 heart**/椭圆/矩形 | `f,shape,startAt,size,tone,label` |
| `PieDraw` | 饼图（唯一自带 progress 的图形） | `f,startAt,radius,spin,tone` |
| `SceneTransitions` | **全部 20 种官方转场**已登记（`PRESENTATIONS` 的键即转场名；`transitionsTotalFrames()` 算总长） | `children,durations,transition,transitionDuration,width,height,direction` |
| `FitTextBox` | **中文反推字号 + 断行**（自带字体就绪门） | `text,maxLines,boxWidth,maxFontSize,showMeasure` |
| `CameraMotionBlur` / `Trail` | 运动模糊 / 拖尾（官方扩展再导出） | 见 `@remotion/motion-blur` |

## 修辞工具件（`src/toolkit.tsx`，3 件）

这 11 件自成一个模块（v3.0.1 从 `index.tsx` 迁出——此前**没有 `export`，场景文件物理上 import 不到**）。
**帧参数名与 fxkit 一致：`frame`。**
选型别按外观挑，走 `media-routing.md` 的**「修辞动作 → 组件」表**：先想"我此刻要做的修辞动作是什么"。
下表只列**关键 props**（够选型用），不是完整签名——每个组件都另有 `style`，字符类组件另有 `fontFamily` / `fontWeight` / `letterSpacing` 等；要精确签名直接读 `src/toolkit.tsx`。

| 组件 | 修辞动作 | 关键 props |
|---|---|---|
| `Callout` | 圈住一处 + 旁边手写标注 | `x,y,w,h,text,textDy,textDx,color,rotate,start,frame` |
| `Checklist` | 列一份清单；`done` 给完成数，序号变对勾 | `items,start,stagger,colors,done,rowH,fontSize,frame` |
| `JumpInText` | 逐字跳入（钩子与收尾，全片 1–2 处） | `items[{text,color,colorActive}],fontSize,start,stagger,frame` |

`Callout` **不带** `data-gate-allow`：画圈的椭圆是 `fill="none"` 的 SVG，`OverlapGate` 的 `looksSolid`
本来就不会把它当遮挡物；而标注文字是"另一条信息"，必须继续参与重叠判定（白名单只留给镜头交接与同位置换信息）。
反过来，**缩放容器**（`ZoomStage` 取景框）只给**容器自己**标 `data-fit-skip`——
被放大的子层必然溢出取景框（实测 `scrollWidth` 1093 vs `clientWidth` 996），`CardFitGate` 会把"推近"误判成"文字被裁"，
在渲染期直接拦下成片。注意 `CardFitGate` 判逃生口用的是 `hasAttribute`（只跳标记者自身）而不是 `closest`：
后者会把取景框内所有卡片的真实裁切一起放过（交叉复核用 A/B 对照实渲证明：248px 的真实裁切因此被漏检）。

## 两条铁律（本片真实 bug 换来的）

1. **高度必须算出来**：所有文字容器高度经 `fitH()` 计算，禁止手写
   "看着差不多" 的固定高度。S3（170px 装 208px 内容）和 S5
   （400px 装 430px 内容）的出格事故根因都是这一条。
2. **坐标看祖先**：`x/y` 永远相对于最近的 positioned 祖先。放在
   `Paper` 卡片内部时是"卡片相对坐标"；只有直接放在场景根 div 下
   才是场景坐标。S4 印章曾因写成场景坐标而飞出屏（渲染不报错）。

