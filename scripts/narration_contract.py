"""旁白内容契约：让「这份音频念的是哪一版文本」变成可验证的事实（P1-07）。

为什么不能只比 mtime：
  · 旧文本被重新保存一次，mtime 就比 narration.txt 新 —— 检查被绕过，念的还是旧稿；
  · 反过来，`git checkout` / 拷工程会让 mtime 全部刷新，明明没改也会被拦。

所以 compose 写出**内容指纹**，tts 合成时核对这个指纹。契约里还留一份文本快照，
目的只有一个：不一致时能指出**第几行**不同，而不是甩一句"请重跑"。

这里只放纯函数与小文件读写，两个脚本共用同一份实现（避免两边算法漂移——
那会让"指纹不同"变成假警报）。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

CONTRACT_REL = "manifests/narration.contract.json"
SCHEMA = 1


def normalize(text: str) -> str:
    """按"有效行 + 末尾换行"规范化：行尾空格与多余空行不参与比较。"""
    lines = [ln.strip() for ln in str(text).splitlines() if ln.strip()]
    return "\n".join(lines) + "\n" if lines else ""


def sha(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


def chars(text: str) -> int:
    return sum(1 for c in normalize(text) if not c.isspace())


def read(project: Path) -> dict | None:
    p = Path(project) / CONTRACT_REL
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA or not doc.get("text_sha256"):
        return None
    return doc


def write(project: Path, text: str, *, source: str, lines: int | None = None) -> dict:
    doc = {
        "schema": SCHEMA,
        "source": source,
        "text_sha256": sha(text),
        "lines": lines if lines is not None else len([x for x in normalize(text).splitlines() if x]),
        "chars": chars(text),
        "text": [ln for ln in normalize(text).splitlines()],
    }
    p = Path(project) / CONTRACT_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return doc


def first_diff(old_text: str, new_text: str) -> dict:
    """第一处不同的行。没有差异返回 {same: True}。"""
    a = [ln for ln in normalize(old_text).splitlines()]
    b = [ln for ln in normalize(new_text).splitlines()]
    if a == b:
        return {"same": True}
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else None
        y = b[i] if i < len(b) else None
        if x != y:
            return {"same": False, "line": i + 1, "old": x, "new": y,
                    "old_lines": len(a), "new_lines": len(b)}
    return {"same": False, "line": None, "old": None, "new": None,
            "old_lines": len(a), "new_lines": len(b)}


def describe(diff: dict) -> str:
    """给人看的差异描述：只报第一处，附行号与两边原文。"""
    if diff.get("same"):
        return "文本一致"
    n = diff.get("line")
    if n is None:
        return f"行数不同（{diff.get('old_lines')} → {diff.get('new_lines')}），但逐行内容一致？"
    old = "（缺失）" if diff.get("old") is None else f"「{diff['old']}」"
    new = "（缺失）" if diff.get("new") is None else f"「{diff['new']}」"
    return (f"第 {n} 行不同（共 {diff.get('old_lines')} → {diff.get('new_lines')} 行）：\n"
            f"    compose 记录：{old}\n"
            f"    narration.txt：{new}")
