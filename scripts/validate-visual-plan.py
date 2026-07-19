#!/usr/bin/env python3
"""Validate visual modes, scene lifetimes and raster-asset provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ALLOWED_MODES = {"image-text", "pure-text", "pure-graphic"}
ALLOWED_SOURCES = {"ai-generated", "user-supplied", "licensed-third-party"}


def validate(project: Path) -> list[str]:
    errors: list[str] = []
    layer_path = project / "manifests" / "asset-manifest.json"
    visual_path = project / "manifests" / "visual-assets.json"
    if not layer_path.is_file():
        return [f"missing {layer_path}"]
    if not visual_path.is_file():
        return [f"missing {visual_path}"]

    layer_data = json.loads(layer_path.read_text(encoding="utf-8"))
    scenes = layer_data.get("scenes")
    scene_asset_ids: set[str] = set()
    if not isinstance(scenes, list) or not scenes:
        errors.append("asset-manifest.json must contain a non-empty scenes array")
    else:
        previous_end = 0
        ids: set[str] = set()
        for index, scene in enumerate(scenes):
            label = scene.get("id", f"scenes[{index}]")
            if label in ids:
                errors.append(f"{label}: duplicate scene id")
            ids.add(label)
            mode = scene.get("visual_mode")
            if mode not in ALLOWED_MODES:
                errors.append(f"{label}: invalid visual_mode {mode!r}")
            start = scene.get("start_frame")
            end = scene.get("end_frame")
            if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
                errors.append(f"{label}: invalid start/end frame")
                continue
            if start < previous_end:
                errors.append(f"{label}: overlaps previous scene ({start} < {previous_end})")
            if start > previous_end:
                errors.append(f"{label}: leaves an uncovered frame gap ({previous_end}..{start})")
            previous_end = end
            referenced_assets = scene.get("visual_asset_ids")
            if not isinstance(referenced_assets, list) or not all(isinstance(item, str) and item for item in referenced_assets):
                errors.append(f"{label}: visual_asset_ids must be an array of non-empty strings")
            else:
                scene_asset_ids.update(referenced_assets)
            if scene.get("mount_contract") != "start-inclusive-end-exclusive":
                errors.append(f"{label}: missing start-inclusive/end-exclusive mount contract")
            if scene.get("exit_contract") not in {"complete-exit", "final-hold"}:
                errors.append(f"{label}: invalid scene exit contract")
            if index < len(scenes) - 1 and scene.get("exit_contract") == "final-hold":
                errors.append(f"{label}: final-hold is only valid for the last scene")
        duration = layer_data.get("duration_frames")
        if not isinstance(duration, int) or duration <= 0:
            errors.append("asset-manifest.json must contain a positive integer duration_frames")
        elif previous_end != duration:
            errors.append(f"scene coverage ends at {previous_end}, expected duration_frames {duration}")

    visual_data = json.loads(visual_path.read_text(encoding="utf-8"))
    assets = visual_data.get("assets")
    if not isinstance(assets, list):
        errors.append("visual-assets.json must contain an assets array")
        assets = []
    asset_ids: set[str] = set()
    for index, asset in enumerate(assets):
        label = asset.get("id", f"assets[{index}]")
        if label in asset_ids:
            errors.append(f"{label}: duplicate visual asset id")
        asset_ids.add(label)
        for field in ("path", "source_type", "use_context", "crop_policy", "rights"):
            if not asset.get(field):
                errors.append(f"{label}: missing {field}")
        if asset.get("source_type") not in ALLOWED_SOURCES:
            errors.append(f"{label}: invalid source_type {asset.get('source_type')!r}")
        rel = asset.get("path")
        if isinstance(rel, str):
            target = project / rel
            if not target.is_file() or target.stat().st_size == 0:
                errors.append(f"{label}: missing or empty asset {rel}")
            elif asset.get("sha256") != hashlib.sha256(target.read_bytes()).hexdigest():
                errors.append(f"{label}: sha256 does not match {rel}")
        if asset.get("source_type") == "ai-generated":
            if not asset.get("provider") or not asset.get("prompt_summary"):
                errors.append(f"{label}: AI-generated assets require provider and prompt_summary")
            if asset.get("baked_text") is not False:
                errors.append(f"{label}: generated assets must set baked_text to false")

    declared = set(layer_data.get("visual_asset_ids", []))
    if declared != asset_ids:
        errors.append(f"visual asset IDs differ between manifests: {sorted(declared)} != {sorted(asset_ids)}")
    if scene_asset_ids != declared:
        errors.append(f"scene visual asset IDs differ from project declaration: {sorted(scene_asset_ids)} != {sorted(declared)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    errors = validate(args.project.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Visual plan valid: {args.project.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
