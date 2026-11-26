#!/usr/bin/env python3
"""story_time.py — 帧率与「毫秒 → 帧」换算

为什么单独立一个这么小的模块：`FPS` 现在有两个真要它的地方——
时间轴（`compose-story.build` 里所有 `frame(...)`）与动作层（`story_acts` 把 `@L1.3`
换算成本镜帧号）。切动作层时若把 `FPS` 留在主文件，`story_acts` 就得反向 import，
或者抄一个 30——前者是循环依赖，后者是第二个真源。

所以这里只放**共享底座**：帧率与换算。时间轴本身（镜头怎么串、总帧数怎么算）仍然在
`compose-story.build()` 里，没有跟着搬过来（§8.5 的决定：流水线不拆）。
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract import C  # noqa: E402  跨语言常量：assets/lecture-template/src/contract.json

FPS = C["FPS"]


def frame(ms: float) -> int:
    """毫秒 → 帧，.5 向上，与渲染端 `Math.round(ms*FPS/1000)` 同式（内置 round 五成双会少 1 帧）。

    运算顺序固定为 `ms * FPS / 1000`：换成 `ms / 1000 * FPS` 在
    .5 边界上可能因浮点舍入差 1 帧，而帧号会进 story.ts。
    """
    return math.floor(ms * FPS / 1000 + 0.5)
