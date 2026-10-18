# 真实素材（截图 / 录屏 / 动图）· v4.5

把用户给的或合法找来的截图、短录屏放进片子里，和组件场景混排（例如 Git 协作课里放一张真实的 PR 页面截图）。
外观沿用 v4.4 卡片语言：`MediaFrame` = 主题卡片（`THEME.Paper`）+ 可选外壳（browser 地址栏 / window 三圆点 / device 手机边框）+ 署名徽章。

## 什么时候用真实素材，什么时候用组件画

| 用真实素材 | 用组件画（默认） |
|---|---|
| 观众以后要在**那个界面**上操作（GitHub PR 页、设置页、报错弹窗） | 讲原理、讲结构、讲数字（组件更清楚，也能逐步出现） |
| 「这是真的」本身就是论据（真实报错、真实数据面板） | 素材里的字太小、太乱，推近后也读不清 |
| 一个短操作过程（≤10 秒录屏） | 找不到许可兼容的素材 → **一律用组件重画** |

## 素材从哪来（按优先级）

1. 用户自己给的文件（`source: "user"`）；
2. 自己截的图 / 自己录的屏（官方文档页、自己的仓库）—— 也记 `source: "user"`，`credit` 写来源；
3. 许可宽松的图库：Wikimedia Commons（CC0 / CC-BY / CC-BY-SA）、Pexels、Unsplash、Pixabay —— 记 `source: "web"`，**必须**写 `url` / `license` / `credit`，署名会自动显示在画面上。

**绝不**使用别人的视频 / 图片而没有兼容许可（NC 非商用、ND 禁止演绎、全部权利保留、来源不明都不行）。拿不准就用组件重画。

## 三步

```text
python "<SKILL_DIR>/scripts/prepare-media.py" ./my-video --add ./pr.png --id pr-page --region diff 0.01 0.31 0.69 0.17
python "<SKILL_DIR>/scripts/prepare-media.py" ./my-video --add ./demo.mov --id clip --trim 2.0 9.5          # 视频自动转 H.264 恒定 30fps、去音轨
python "<SKILL_DIR>/scripts/validate-media.py" ./my-video                                                  # make-video 也会自动跑
```

Windows：`scripts\prepare-media.cmd` 同参数。素材进 `public/media/`，登记在 `manifests/media.json`（同步一份到 `src/media.json`）。

`manifests/media.json` 每条：`{id, file, kind: image|video|gif, source: user|web, url, license, credit, trimStartSec, trimEndSec, focusRegions: [{id, x, y, w, h}], muted}`。
区域坐标是 **0–1 的相对值**（相对原图宽高）。`muted` 缺省 true；写 `false` 才保留原声（门禁会提示）。动图会被转成 MP4（`kind` 变 `video`，帧驱动播放）。

## 手写场景里用

```tsx
import {MediaFrame} from './media-frame';
<MediaFrame f={f} id="pr-page" x={200} y={200} w={1060} h={662} chrome="browser"
  focus="diff" focusAt={b[1]} highlight={['merge']} highlightAt={b[2]}
  callouts={[{region: 'diff', text: '只改了三行', at: b[1] + 20}]} />
```

- `focus`：在卡片**内部**推近到某个区域（不露出素材外的空白）；也可以只在镜头表 `cinema.focus` 推近整张卡片——二选一，别叠两层大倍数。
- `highlight`：只描框不推近；`callouts`：区域旁边的一句话标签。
- 视频从入场帧 `at` 开始播，`trimStartSec`→`trimEndSec` 播完停在最后一帧。全部由帧号驱动。
- `src/media.json` 必须存在（模板自带空的 `{"items": []}`）。

## auto 草稿里用（story.json）

顶层写 `media` 列表（`file` 相对 story.json），镜头写 `"layout": "media"`：

```json
"media": [{"id": "pr-page", "file": "pr.png", "source": "user", "focusRegions": [{"id": "diff", "label": "改动", "x": 0.01, "y": 0.31, "w": 0.69, "h": 0.17}]}],
"shots": [{"layout": "media", "lines": ["先看中间的 {{改动|diff}}。"], "content": {"media": "pr-page", "chrome": "browser", "caption": "绿色是新增"}}]
```

台词里 `{{词|区域id}}` → 念到时给那个区域描框并推近镜头。完整例子：`examples/real-media/git-pr.story.json`（截图是脚本生成的占位图）。

## 门禁（validate-media.py）

P0：文件不存在 / 类型不符；放大超过 1.5 倍（含区域推近，按 1080p 交付）；视频不是 H.264 + 恒定 30fps + yuv420p；
`source: web` 缺 url / license / credit 或许可不兼容；引用了不存在的区域；区域坐标出界；`src/media.json` 未同步；场景源码自己画或关掉署名徽章。
P1：`muted: false`；登记了没用到；2K 交付时放大超过 1.5 倍。

## 高亮与推近的注意事项（v4.5c）

- `highlight` / `focus` 的区域框画在视口坐标里：4 px 橙色描边 + 白内圈 + 抬升阴影，区域外压一层 0.16 的淡暗幕，缩小看也一眼能找到；区域推近后露出不足 90% 的框不画（不会出现被切掉的半个框）。
- 镜头表 `cinema.focus` 推近画面别处时，旁边的 MediaFrame 卡片可能被推出画面一半——给那条 focus 写 `keep: {x,y,w,h}`（卡片的矩形），引擎会降低推近倍数把两者都装下。
- `w` / `h` 请写数字或同文件 `const`（`w={W}`、`w={W * 0.6}` 都能量）；写成布局对象字段时 validate-media 量不出放大倍数，只按占满画布估并给 P1 提醒。

## Highlight & push-in notes (v4.5c)

Region highlights are drawn in viewport space (4 px orange stroke, white inner ring, lift shadow, 0.16 veil outside); boxes < 90 % visible after a region zoom are hidden. When a shot-level `cinema.focus` pushes in elsewhere, add `keep: {x,y,w,h}` for the MediaFrame card. Write `w`/`h` as numbers or same-file consts so validate-media can measure upscaling.

