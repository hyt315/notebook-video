#!/usr/bin/env python3
"""重定时工具（本地）：口播/章节变化后，一键重写时长相关的三处机械数字。

只做机械事，不猜语义：
  1. src/index.tsx 的 DURATION=<n>
  2. manifests/asset-manifest.json 的 duration_frames + 各 scene 起止帧
    （scene id 顺序必须与现状一致，只改数字不改结构）
  3. 打印 Sound 音效帧重排建议表（场景起点/中点/完成点，人工确认后改）

用法：
  python scripts/retime.py PROJECT_DIR DURATION s1,s2,s3,...
  例：python scripts/retime.py astra-video 4423 0,429,1243,1688,2698,3756,4423

边界数 = 场景数 + 1，且首尾必须为 0 和 DURATION。改完必跑：
  validate-visual-plan / validate-layering / 各场景边界 range-render。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    project = Path(sys.argv[1])
    duration = int(sys.argv[2])
    bounds = [int(x) for x in sys.argv[3].split(",")]
    if bounds[0] != 0 or bounds[-1] != duration:
        print("边界首尾必须为 0 和 DURATION")
        return 2

    index_tsx = project / "src" / "index.tsx"
    text = index_tsx.read_text(encoding="utf-8")
    new_text, n = re.subn(r"DURATION=\d+", f"DURATION={duration}", text, count=1)
    if n != 1:
        print("src/index.tsx 里没有找到 DURATION=<n>")
        return 1
    index_tsx.write_text(new_text, encoding="utf-8")
    print(f"DURATION -> {duration}")

    manifest_path = project / "manifests" / "asset-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenes = manifest["scenes"]
    if len(scenes) != len(bounds) - 1:
        print(f"场景数 {len(scenes)} 与边界段数 {len(bounds) - 1} 对不上，不写 manifest")
        return 1
    for scene, start, end in zip(scenes, bounds[:-1], bounds[1:]):
        scene["start_frame"], scene["end_frame"] = start, end
    manifest["duration_frames"] = duration
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"asset-manifest: duration_frames={duration}，{len(scenes)} 场景边界已更新")

    print("--- Sound 音效帧重排建议（场景起点/中点/完成点，确认后手改） ---")
    for scene, start, end in zip(scenes, bounds[:-1], bounds[1:]):
        print(f"{scene['id']}: rustle={start + 4} whoosh={(start + end) // 2} chime={end - 30}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
