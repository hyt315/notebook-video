# fxkit：固定动效组件库（反 PPT 专用）

`assets/lecture-template/src/fxkit.tsx`，v2 共 18 个组件，零新依赖
（使用 Remotion 原生动画和 `Img` 加载门）。优先 transform/opacity；部分旧组件仍通过宽度或位置表现进度，
cel 皮肤锁定（2.5px 墨线 + 硬偏移阴影 + 纯平填充，无渐变无模糊阴影），
30fps 确定性（无随机数）。用法：

```tsx
import {FitCard, Typewriter, PayPop, StampSeal, Funnel, ChatThread, MailScan, TimeRail, CompareBars, ProgressRing, ShakeX, BurstCallout, StaggerList, fitH} from './fxkit';
```

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
| `KenBurnsImg` | 克制推近：只放大不移出框（父容器须 `overflow:hidden`） | `src,zoom,dur,fit,frame,start,exitStart` |
| `EvidenceZoom` | 证据三节拍：识别 → 定位推近 → 落结论 chip | `src,fx,fy,zoom,at,label,focusAt,concludeAt,exitStart` |
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

图片组件在所有主题可导入；无 Burst 的主题安全隐藏该装饰。`EvidenceZoom` 焦点基于 cover 后的 viewport，边界钳制避免空边。完整组合见 [shot recipes](shot-recipes.md)。
