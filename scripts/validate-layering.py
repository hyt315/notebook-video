#!/usr/bin/env python3
"""Validate object-layer and motion contracts in an asset manifest."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


ALLOWED_ROLES = {"background", "annotation", "wire", "base", "slot", "status",
                 "floating", "foreground", "subtitle"}
ALLOWED_CONTRACTS = {"normal", "always-visible", "insertable", "highest"}
ALLOWED_EXITS = {"persistent", "scene-cut", "fully-outside", "fully-outside-or-zero",
                 "arrive-at-destination", "final-hold"}
DECORATIVE_MOTIONS = {"drift", "orbit", "steam", "float-loop", "random-wiggle"}


def validate(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    parts = data.get("parts")
    if not isinstance(parts, list) or not parts:
        return ["manifest must contain a non-empty parts array"]

    errors: list[str] = []
    ids: set[str] = set()
    scenes: dict[object, list[dict]] = defaultdict(list)
    for index, part in enumerate(parts):
        label = part.get("id", f"parts[{index}]")
        if label in ids:
            errors.append(f"{label}: duplicate id")
        ids.add(label)
        for field in ("scene", "z", "layer_role", "occlusion_contract", "exit_contract"):
            if field not in part:
                errors.append(f"{label}: missing {field}")
        role = part.get("layer_role")
        contract = part.get("occlusion_contract")
        if role not in ALLOWED_ROLES:
            errors.append(f"{label}: invalid layer_role {role!r}")
        if contract not in ALLOWED_CONTRACTS:
            errors.append(f"{label}: invalid occlusion_contract {contract!r}")
        if part.get("exit_contract") not in ALLOWED_EXITS:
            errors.append(f"{label}: invalid exit_contract {part.get('exit_contract')!r}")
        if role == "floating" and contract != "always-visible":
            errors.append(f"{label}: floating parts must use always-visible")
        motions = set(part.get("motion", []))
        if motions & DECORATIVE_MOTIONS and not part.get("narrative_reason"):
            errors.append(f"{label}: decorative motion requires narrative_reason")
        scene_values = part.get("scene")
        if not isinstance(scene_values, list):
            scene_values = [scene_values]
        for scene in scene_values:
            scenes[scene].append(part)

    for scene, scene_parts in scenes.items():
        lower_z = [p.get("z", -10**9) for p in scene_parts
                   if p.get("layer_role") in {"base", "slot", "status"}]
        ceiling = max(lower_z, default=-10**9)
        for part in scene_parts:
            if part.get("layer_role") == "floating" and part.get("z", -10**9) <= ceiling:
                errors.append(
                    f"{part.get('id')}: floating z={part.get('z')} must be above "
                    f"base/slot/status z={ceiling} in scene {scene}"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    errors = validate(args.manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Layering valid: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
