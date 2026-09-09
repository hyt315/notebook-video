#!/usr/bin/env python3
"""Validate and update duration metadata; scene animation still needs cue review.

Usage: python scripts/retime.py PROJECT_DIR DURATION 0,s1,s2,...,DURATION
No files are changed if the proposed boundaries or source contract are invalid.
This is not an automatic re-authoring of narration, scene motion or sound cues.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def retime(project: Path, duration: int, bounds: list[int]) -> None:
    if duration <= 0 or len(bounds) < 2 or bounds[0] != 0 or bounds[-1] != duration:
        raise ValueError("Invalid boundaries: require positive DURATION, first 0 and last DURATION")
    if any(b <= a for a, b in zip(bounds, bounds[1:])):
        raise ValueError("Invalid boundaries: frames must be strictly increasing")
    index_tsx = project / "src" / "index.tsx"
    manifest_path = project / "manifests" / "asset-manifest.json"
    text = index_tsx.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenes = manifest["scenes"]
    if len(scenes) != len(bounds) - 1:
        raise ValueError(f"Invalid scene count: {len(scenes)} scenes, {len(bounds) - 1} intervals")
    if any(scene.get("shots") for scene in scenes):
        raise ValueError("Re-time shot/beat anchors explicitly before using retime; nested timings are not scaled")
    new_text, n = re.subn(r"\bDURATION\s*=\s*\d+", f"DURATION={duration}", text)
    if n != 1:
        raise ValueError("Expected exactly one numeric DURATION in src/index.tsx")
    for scene, start, end in zip(scenes, bounds[:-1], bounds[1:]):
        if any(type(beat.get('frame')) is not int or not start <= beat['frame'] < end for beat in scene.get('beats', [])):
            raise ValueError('Re-anchor review beats inside their new scene before retiming')
        scene["start_frame"], scene["end_frame"] = start, end
    manifest["duration_frames"] = duration
    # Prepare both payloads before publishing either. Validation failures never mutate inputs.
    payload = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    index_tsx.write_text(new_text, encoding="utf-8")
    manifest_path.write_text(payload, encoding="utf-8")
    print(f"Updated duration={duration} and {len(scenes)} scene windows")
    print("Review scene motion, caption tail, camera and sound beats against the new narration before rendering.")


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    try:
        retime(Path(sys.argv[1]), int(sys.argv[2]), [int(x) for x in sys.argv[3].split(",")])
    except (ValueError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
