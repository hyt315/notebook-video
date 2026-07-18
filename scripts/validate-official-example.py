#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
EXAMPLE = SKILL / "assets" / "example-project"
CONTRACT = SKILL / "references" / "locked-style-contract.json"
STYLE = "warm-ivory-remotion-2k30-v8-performance"


def require_text(path: Path, required: list[str], forbidden: list[str] | None = None) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [token for token in required if token not in text]
    found = [token for token in (forbidden or []) if token in text]
    if missing or found:
        raise SystemExit(f"{path}: missing={missing or 'none'} forbidden={found or 'none'}")


def same(a: Path, b: Path) -> None:
    if hashlib.sha256(a.read_bytes()).digest() != hashlib.sha256(b.read_bytes()).digest():
        raise SystemExit(f"stale duplicate render input: {a.relative_to(EXAMPLE)} != {b.relative_to(EXAMPLE)}")


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("version") != STYLE or contract.get("status") != "official-current":
        raise SystemExit("official style identity changed")
    canvas = contract["canvas"]
    if (canvas["width"], canvas["height"], canvas["delivery_fps"], canvas["physical_motion_fps"]) != (2560, 1440, 30, 30):
        raise SystemExit("2K/30 canvas or native motion rate changed")
    performance = contract["performance_system"]
    if performance["duplicate_frame_delivery"] or not performance["active_scene_mounting"]:
        raise SystemExit("performance contract changed")
    if contract["engine"]["renderer"] != "Remotion 4.0.489":
        raise SystemExit("renderer pin changed")
    subtitle = contract["subtitle_input"]
    if subtitle["bounds"] != [188, 934, 1732, 1046]:
        raise SystemExit("subtitle bounds changed")
    if subtitle["dark_border"] or subtitle["dark_side_marks"] or subtitle["inner_line"]:
        raise SystemExit("subtitle artifact rejection flags changed")

    manifest = json.loads((EXAMPLE / "manifests" / "asset-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("style_version") != STYLE:
        raise SystemExit("official asset manifest style version is stale")
    if manifest.get("duration_frames") != 900:
        raise SystemExit("official asset manifest duration must match the 900-frame composition")

    source = EXAMPLE / "src" / "index.tsx"
    require_text(
        source,
        [
            "const BASE_FPS=30,FPS=30,MOTION_FPS=30,TIMELINE_SCALE=1,DURATION=900,DESIGN_SCALE=4/3",
            "useCurrentFrame as useRawCurrentFrame",
            "const useCurrentFrame=()=>useRawCurrentFrame()*BASE_FPS/FPS/TIMELINE_SCALE",
            "const deliveryFrame=(designFrame:number)=>Math.round(designFrame*FPS*TIMELINE_SCALE/BASE_FPS)",
            "const msFrame=(ms:number)=>Math.round(ms*FPS/1000)",
            "const q=(f:number)=>{const step=BASE_FPS/MOTION_FPS",
            "const AssetGate=()",
            "Required audio failed to load",
            "const CaptionFitGate=",
            "if(done)return null",
            "getBoundingClientRect().width/DESIGN_SCALE",
            "document.fonts.load('400 40px SourceHan')",
            "const C={ink:'#2b2924'",
            "const TYPE={displayXL:58",
            "const AESTHETIC={subtitleSafeWidth:1334",
            "const COPY={",
            "const paperShadow=(lift:number)",
            "const LineIcon:",
            "const CheckBadge:React.FC",
            "const Grade=",
            "background:C.paper",
            "width:AESTHETIC.subtitleSafeWidth",
            "@remotion/media",
            "<Sequence",
            "<Audio src={staticFile('narration.mp3')}",
            "<Fonts/><AssetGate/><CaptionFitGate/><Sound/>",
            "f<205&&<FinalActOne/>",
            "const FinalDemo=()=>{const f=q(useCurrentFrame())",
            "from={deliveryFrame(f)}",
            "translate3d",
            "registerRoot(Root)",
            "width={2560} height={1440}",
            "transform:'scale(1.3333333333)'",
        ],
        forbidden=[
            "render.py", "inner_wave", "camera_drift", "from PIL", "Pillow",
            "CardSpec", "FeatureCard", "FilmScene", "BigModule",
            "StageOne", "StageTwo", "StageThree", "WideDemo",
        ],
    )

    require_text(
        EXAMPLE / "storyboard.md",
        ["升级原则", "独立工位", "连续装配", "验证交付", "2K"],
        forbidden=["原技能", "触及上限", "保留能力", "引擎迁移", "资源安全锁"],
    )

    package = json.loads((EXAMPLE / "package.json").read_text(encoding="utf-8"))
    for name in ("remotion", "@remotion/cli", "@remotion/media"):
        if package["dependencies"].get(name) != "4.0.489":
            raise SystemExit(f"dependency pin changed: {name}")
    for name in ("react", "react-dom"):
        if package["dependencies"].get(name) != "19.2.7":
            raise SystemExit(f"dependency pin changed: {name}")
    if package.get("name") != "notebook-video-final-motion-system-v8-performance":
        raise SystemExit("official package identity is stale")
    if "network-shim" in " ".join(package.get("scripts", {}).values()):
        raise SystemExit("environment-specific network shim is still forced by package scripts")

    cues_path = EXAMPLE / "manifests" / "caption-cues.json"
    cues = json.loads(cues_path.read_text(encoding="utf-8"))["cues"]
    words = sum(len(cue["words"]) for cue in cues)
    if (len(cues), words) != (13, 91):
        raise SystemExit(f"caption exemplar changed: cues={len(cues)} words={words}")

    for unlicensed_audio in (EXAMPLE / "audio" / "narration.mp3", EXAMPLE / "public" / "narration.mp3"):
        if unlicensed_audio.exists():
            raise SystemExit(f"generated narration must not be bundled without documented redistribution rights: {unlicensed_audio.relative_to(EXAMPLE)}")
    same(cues_path, EXAMPLE / "src" / "caption-cues.json")
    for name in ("paper-rustle.wav", "paper-tap.wav", "data-whoosh.wav", "chime.wav"):
        if not (EXAMPLE / "public" / "sfx" / name).is_file():
            raise SystemExit(f"missing declarative action sound: {name}")
    for name in ("SourceHanSansCN-Regular.otf", "SourceHanSansCN-Bold.otf", "SmileySans-Oblique.otf"):
        if not (SKILL / "assets" / "fonts" / name).is_file():
            raise SystemExit(f"missing bundled font: {name}")

    for rel in (
        "scripts/notebook-video.mjs",
        "scripts/notebook-video.cmd",
        "scripts/new-project.sh",
        "scripts/new-project.cmd",
        "scripts/prepare-browser.sh",
        "scripts/prepare-browser.cmd",
        "scripts/package-project.py",
        "assets/example-project/REMOTION-LICENSE-NOTICE.md",
        "assets/example-project/audio/README.md",
        "references/cross-platform-compatibility.md",
        "references/windows-compatibility.md",
    ):
        if not (SKILL / rel).is_file():
            raise SystemExit(f"missing cross-platform support file: {rel}")

    run(sys.executable, str(SKILL / "scripts" / "validate-layering.py"), str(EXAMPLE / "manifests" / "asset-manifest.json"))
    run(sys.executable, str(SKILL / "scripts" / "validate-caption-sync.py"), str(EXAMPLE / "audio" / "narration.mp3.json"), str(cues_path))
    run(sys.executable, str(SKILL / "scripts" / "validate-semantic-breaks.py"), str(cues_path), str(EXAMPLE / "manifests" / "protected-caption-phrases.txt"))
    print("Official warm-ivory v8 performance 2K/30 Final Motion System exemplar is internally consistent and style-locked")


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Official exemplar validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
