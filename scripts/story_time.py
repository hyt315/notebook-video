#!/usr/bin/env python3
"""story_time.py — 帧率与「毫秒 → 帧」换算（P2-24 第三切片的前置）

为什么单独立一个这么小的模块：`FPS` 现在有两个真要它的地方——
时间轴（`compose-story.build` 里所有 `frame(...)`）与动作层（`story_acts` 把 `@L1.3`
换算成本镜帧号）。切动作层时若把 `FPS` 留在主文件，`story_acts` 就得反向 import，
或者抄一个 30——前者是循环依赖，后者是第二个真源。

所以这里只放**共享底座**：帧率与换算。时间轴本身（镜头怎么串、总帧数怎么算）仍然在
`compose-story.build()` 里，没有跟着搬过来（§8.5 的决定：流水线不拆）。
"""
from __future__ import annotations

FPS = 30


def frame(ms: float) -> int:
    """毫秒 → 帧（四舍五入）。与模板 `FPS = 30` 同一个数（一致性检查另行钉死）。

    运算顺序保持 `ms * FPS / 1000`（与旧版逐字一致）：换成 `ms / 1000 * FPS` 在
    .5 边界上可能因浮点舍入差 1 帧，而帧号会进 story.ts。
    """
    return int(round(ms * FPS / 1000))
