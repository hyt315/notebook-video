"""gate_report.py — 门禁的统一结果格式（每条问题一行 JSON）。

每个 validate-*.py 照旧在终端打印给人看的明细和「结论：…」汇总；另外在打印之前调一次
`emit(门禁名, p0, p1, file)`。设了环境变量 `NV_GATE_JSON=<文件路径>` 时，每条 P0 / P1
追加一行 JSON 到那个文件（JSON Lines）；没设就什么也不写，终端输出不受影响。

一行的形状（所有门禁一样）：
    {"gate": "validate-presentation", "id": "S3", "level": "P1",
     "file": "manifests/shots.resolved.json", "message": "…", "fix": "…"}

  · id      明细自带编号就用它（`{"id": "S3", ...}` 或文字开头的 `S3: …`），否则「门禁名-P1-序号」
  · message 问题本身（`——` 之前的部分）
  · fix     `——` 之后的修法提示；没有就是空串
  · file    该门禁主要读的文件，相对工程目录；说不清时为空串

make-video.mjs 读这个文件：P1 写进 renders/report.md 的「建议（不拦）」，全部记录
写进 renders/gates.json。只读这一种格式，不再从终端文字里猜。
"""
import json
import os
import re

TAGGED = re.compile(r"^([-A-Za-z0-9_.:]+)\s*[:：]\s*(.+)$", re.S)


def record(gate: str, level: str, item, n: int, file: str = "") -> dict:
    gate = gate[:-3] if gate.endswith(".py") else gate
    if isinstance(item, dict):
        rid, text = str(item.get("id") or ""), str(item.get("issue") or item.get("message") or "")
        fix = str(item.get("fix") or "")
    else:
        rid, text, fix = "", str(item), ""
        m = TAGGED.match(text.strip())
        if m:
            rid, text = m.group(1), m.group(2)
    if not fix and "——" in text:
        text, fix = text.split("——", 1)
    return {"gate": gate, "id": rid or f"{gate}-{level}-{n}", "level": level, "file": file,
            "message": text.strip(), "fix": fix.strip()}


def emit(gate: str, p0, p1, file: str = "") -> None:
    path = os.environ.get("NV_GATE_JSON")
    if not path:
        return
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        for level, items in (("P0", p0 or []), ("P1", p1 or [])):
            for n, item in enumerate(items, 1):
                fh.write(json.dumps(record(gate, level, item, n, file), ensure_ascii=False) + "\n")
