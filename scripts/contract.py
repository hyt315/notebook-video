"""跨语言常量：读模板 `assets/lecture-template/src/contract.json`（TS 侧 import 同一份）。

用法：`from contract import C`，然后 `C["FPS"]`、`C["STAGE"]["cx"]`。
改数值只改那份 JSON，Python 门禁、排版和 TS 渲染同时生效，不再需要双源核对。
"""
from __future__ import annotations

import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "assets" / "lecture-template" / "src" / "contract.json"
C: dict = json.loads(PATH.read_text(encoding="utf-8"))
