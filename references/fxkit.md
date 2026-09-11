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
>
> **这条以前只是文档，现在有门禁**：`python scripts/validate-frame-props.py PROJECT_DIR` 逐个标签核对
> 参数名，写错即 P0。实测两支自带样板片各有 5–6 处违反，印章 / Funnel / 打字机的进场动画因此长期失效
> （组件回落到全局帧后，`start={局部节拍}` 早已过去，元素直接以完成态出现）。**改完场景文件先跑它。**

**参数名对照（写场景时照这张表，别凭记忆）**

| 取值 | 模块 / 组件 |
|---|---|
| `frame={f}` | `fxkit` 全部 18 个：`FitCard` `Typewriter` `PayPop` `StampSeal` `Funnel` `ChatThread` `MailScan` `TimeRail` `CompareBars` `ProgressRing` `ShakeX` `BurstCallout` `StaggerList` `KenBurnsImg` `EvidenceZoom` `DiffView` `ConfettiPop` `SkeletonCard` |
| `f={f}` | `media`（`ConsoleWindow` `MetricGrid` `StampBanner`）、`stagekit`（`StageFrame` `Attach`）、`skeletons`（`Corridor` `SplitStage` `ZoomStage`）、`insert`（`InsertShot` `HandoffCarrier` `RevealMask`）、`shotkit`（`DepthLayers`） |
| 不收帧参数 | `kit` 的 `PillTag/LineIcon/CheckBadge`、`CoverPanel`、`PhaseRail`（从 `ctx` 取）、`ShotCamera`（内部自取） |

> **写列表错峰（v2.11 校准）**：`StaggerList` 默认 `stagger=6`。实测 18–30 帧的错峰在中文旁白下会读成
> "一个个淡出来"，观众看不到"成串落下"，还会让后几张卡在旁白已经讲下一句时才出现（用户会报"四项只看到三项"）。
> **同句内错峰 ≤8 帧**；真正需要长间隔的是叙事节拍，那应该由 `beats` 决定，不是由 `stagger` 决定。

## 本轮动效升级（v3，多时钟）

| 组件 | 改了什么 | 为什么 |
|---|---|---|
| `StampSeal` | 砸下 9 帧后加一次 `1→1.06→1` 回弹 + 墨圈冲击波 | 只有"压下去"的印章只是"圆变小了"；有回弹才读作"砸在纸上" |
| `ProgressRing` | 弧 30 帧 / 数字约 24 帧**双时钟**；弧端加行进圆点；过冲只给容器 | 同一条曲线会让"数字就是那条弧"；数值类动画不能弹（会短暂显示错误的数） |
| `Funnel` / `CompareBars` / `TimeRail` | 进度由 `width` 改 `scaleX` | `width` 是布局属性会重排，且会让圆角胶囊在动画中途被拉变形 |
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

## 修辞工具件（`src/toolkit.tsx`，11 件）

这 11 件自成一个模块（v3.0.1 从 `index.tsx` 迁出——此前**没有 `export`，场景文件物理上 import 不到**）。
**帧参数名与 fxkit 一致：`frame`；只有 `Mascot` 用 `f`。**
选型别按外观挑，走 `media-routing.md` 的**「修辞动作 → 组件」表**：先想"我此刻要做的修辞动作是什么"。
下表只列**关键 props**（够选型用），不是完整签名——每个组件都另有 `style`，字符类组件另有 `fontFamily` / `fontWeight` / `letterSpacing` 等；要精确签名直接读 `src/toolkit.tsx`。

| 组件 | 修辞动作 | 关键 props |
|---|---|---|
| `Callout` | 圈住一处 + 旁边手写标注 | `x,y,w,h,text,textDy,textDx,color,rotate,start,frame` |
| `Connector` | 表现两者关系/因果（贝塞尔 + 箭头 + 可选流向） | `from,to,bend,color,flow,arrow,label,width,frame` |
| `Checklist` | 列一份清单；`done` 给完成数，序号变对勾 | `items,start,stagger,colors,done,rowH,fontSize,frame` |
| `CountUp` | 报一个大数字（滚动计数） | `to,from,start,duration,fontSize,color,prefix,suffix,frame` |
| `RollDigit` | 数字/字符 3D 滚轮翻牌 | `fromChar,toChar,start,duration,fontSize,colorFrom,colorTo,frame` |
| `ProgressBar` | 进度条，`v` 由场景驱动（0~1） | `v,color,height,label,showPct,style` |
| `JumpInText` | 逐字跳入（钩子与收尾，全片 1–2 处） | `items[{text,color,colorActive}],fontSize,start,stagger,frame` |
| `WaveText` | 逐字波浪打字（同上） | `text,fontSize,colorFrom,colorTo,start,stagger,frame` |
| `CodeBlock` | 终端风代码窗（三灯 + 逐行滑入） | `title,lines[{text,color,prefix,start}],start,stagger,cursor,frame` |
| `BrowserChrome` | 页面形态（三灯 + 锁 + URL 胶囊），内容放 children | `url,lift,style` |
| `Mascot` | 系列吉祥物（代码绘制的 git 猫，会眨眼/挥手） | `size,f,wave` |

`Callout` / `Connector` **不带** `data-gate-allow`：画圈的椭圆是 `fill="none"` 的 SVG，`OverlapGate` 的 `looksSolid`
本来就不会把它当遮挡物；而标注文字是"另一条信息"，必须继续参与重叠判定（白名单只留给镜头交接与同位置换信息）。
反过来，**缩放容器**（`ZoomStage` 取景框、`EvidenceZoom`）只给**容器自己**标 `data-fit-skip`——
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

## 实拍素材框：ShotPlate（`src/plates.tsx`）

有真实素材（产品界面截图、官方图表、推文截图）时，**用它比用代码画近似图强得多**——
真实界面本身就是证据。`ShotPlate` 把截图装进锁定皮肤的墨线框（2.5px 描边 + 硬偏移阴影 + 纯平填充），
配角标（说明这是什么图）、右上角标（如"官方图表"）与来源署名，并用 `transform` 做**确定性推近**
（`zoom` + `focus`，不重排、无随机）。

```tsx
import {ShotPlate} from './plates';
<ShotPlate x={210} y={168} w={1010} h={600} f={f} src="materials/devin-cli.png"
  at={at(0)}                  // 出现节拍，必绑（不要写死帧号）
  zoom={1.32} focus={{fx: 0.5, fy: 0.72}} dur={96}
  caption="Devin CLI 实拍" badge="v3000.10.21" source="输入 /model 即可切换" />
```

**素材必须登记**（两道清单要一致，`validate-visual-plan` 会核对）：
1. `manifests/visual-assets.json` 增一条：`id / path / source_type / provider / prompt_summary / use_context / crop_policy / rights / baked_text / sha256`；截图类 `baked_text` 记 `true`。
2. `manifests/asset-manifest.json` 的 `visual_asset_ids` 与对应 `scenes[].visual_asset_ids` 里加上同一个 `id`（该镜 `visual_mode` 用 `image-text`）。
文件放 `public/materials/`，代码里写 `src="materials/xxx.png"`。

**取舍**：能说清的用画的（更可控、跟节拍更紧），需要"这确实是官方/真实"的用实拍。每镜最多一块实拍图，别把片子做成截图集。
