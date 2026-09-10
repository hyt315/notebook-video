# fxkit：固定动效组件库（反 PPT 专用）

`assets/lecture-template/src/fxkit.tsx`，v2 共 18 个组件，零新依赖
（只用 remotion 原生 `spring`/`interpolate`），只做 transform/opacity 位移，
cel 皮肤锁定（2.5px 墨线 + 硬偏移阴影 + 纯平填充，无渐变无模糊阴影），
30fps 确定性（无随机数）。用法：

```tsx
import {FitCard, Typewriter, PayPop, StampSeal, Funnel, ChatThread, MailScan, TimeRail, CompareBars, ProgressRing, ShakeX, BurstCallout, StaggerList, fitH} from './fxkit';
```

> **⚠️ 帧参数名（实测踩过，必读）**：fxkit 的帧参数叫 **`frame`**，而 v2.10 新增模块
> （`shotkit` / `stagekit` / `media` / `skeletons` / `insert`）的帧参数叫 **`f`**。
> 给 fxkit 组件传 `f={f}` 会被**静默忽略**，组件回落到 `useCurrentFrame()`（全局帧），
> 于是动画整体错位，甚至抛 `Frame NaN`。**fxkit 传 `frame={f}`，新模块传 `f={f}`。**
>
> 另外每个组件的 `frame` 语义是**本镜本地帧**（0 起），不是全局帧；在 `ShotCamera` 内组合时必须传本地帧。

## 本轮动效升级（v3，多时钟）

| 组件 | 改了什么 | 为什么 |
|---|---|---|
| `StampSeal` | 砸下 9 帧后加一次 `1→1.06→1` 回弹 + 墨圈冲击波 | 只有"压下去"的印章只是"圆变小了"；有回弹才读作"砸在纸上" |
| `ProgressRing` | 弧 30 帧 / 数字约 24 帧**双时钟**；弧端加行进圆点；过冲只给容器 | 同一条曲线会让"数字就是那条弧"；数值类动画不能弹（会短暂显示错误的数） |
| `Funnel` / `CompareBars` / `TimeRail` | 进度由 `width` 改 `scaleX` | `width` 是布局属性会重排，且会让圆角胶囊在动画中途被拉变形 |
| `DiffView` | 删除行向左快退（12 帧 ease-in）、新增行向右稳进（16 帧 ease-out）+ 落行高亮 | 补丁的语义就是"一侧拿走、一侧放进"，同向同速会毁掉这个语义 |
| `Typewriter` | 光标 9 帧方波 → 16 帧软阶梯（约 0.53s） | 9 帧方波在 30fps 下读作频闪；这是全片看得最久的运动 |

## 先看见，再选用

`NotebookVideoShowcase` Composition 把本库 16 个构件渲染成 6 页接触表（1fps 抽帧即一页一图）：

```text
node scripts/notebook-video.mjs showcase PROJECT_DIR
node scripts/notebook-video.mjs showcase-sheet PROJECT_DIR
```

选组件前先看接触表，比读 props 文档准确得多。新增组件时必须同时加进接触表。

## 组件一览

| 组件 | 用途 | 关键 props |
|---|---|---|
| `FitCard` + `fitH()` | 防出格卡片：高度必须经 `fitH()` 显式算出 | `x,y,w,h,pad,borderColor,start,exitStart` |
| `Typewriter` | 打字机，标点自动停顿，块光标闪烁 | `text,fontSize,cps,start` |
| `PayPop` | 到账通知弹窗：下滑入 + 金额 + 可选盖章 | `x,y,w,app,amount,time,stampAt` |
| `StampSeal` | 印章砸下：2.6x→1 回弹，-8° 旋转 | `text,color,size,x,y,start` |
| `Funnel` | 尝试漏斗：宽进窄出 + 计数 + 滴落点 | `x,y,w,rows[{label,sub,count,color,ratio}]` |
| `ChatThread` | 对话气泡：typing 三点 → 气泡 pop，左右交替 | `x,y,w,msgs[{side,text,at}]` |
| `MailScan` | 邮件确认：激光扫过 → 高亮 → 密钥打码，定高不溢出 | `x,y,w,rows,secret` |
| `TimeRail` | 时间轨道：圆点行进，到 tick 弹事件卡 | `x,y,w,ticks[{t,label,color,at}]` |
| `CompareBars` | 对比条：宽度动画 + 差值 chip | `x,y,w,rows,delta` |
| `ProgressRing` | 进度环：dashoffset 填充 + 中央标签 | `size,pct,label,color` |
| `ShakeX` | 强调抖动：落点后 ±amp 衰减摆 3 次 | `start,dur,amp` |
| `KenBurnsImg` | 克制推近：只放大不移出框（父容器须 `overflow:hidden`） | `src,zoom,dur,fit` |
| `EvidenceZoom` | 证据三节拍：识别 → 定位推近 → 落结论 chip | `src,fx,fy,zoom,at,label` |
| `DiffView` | 补丁 diff：红删绿加，逐行滑入 | `x,y,w,title,lines[{k,text,at}]` |
| `ConfettiPop` | 到账庆祝：N 碎片炸开旋转下落 | `x,y,maxR,n,start,dur` |
| `SkeletonCard` | 骨架→内容：等待 beats 先占位 | `x,y,w,h,rows,revealAt` |
| `BurstCallout` | 爆炸贴纸安全 wrapper：超 3 字截断，无 Burst 的主题直接隐藏 | `x,y,size,text` |
| `StaggerList` | 级联列表：逐行滑入 + 微旋转，防 bullets 堆砌 | `x,y,w,items,start,stagger` |

## 两条铁律（本片真实 bug 换来的）

1. **高度必须算出来**：所有文字容器高度经 `fitH()` 计算，禁止手写
   "看着差不多" 的固定高度。S3（170px 装 208px 内容）和 S5
   （400px 装 430px 内容）的出格事故根因都是这一条。
2. **坐标看祖先**：`x/y` 永远相对于最近的 positioned 祖先。放在
   `Paper` 卡片内部时是"卡片相对坐标"；只有直接放在场景根 div 下
   才是场景坐标。S4 印章曾因写成场景坐标而飞出屏（渲染不报错）。
