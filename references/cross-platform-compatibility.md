# Cross-platform compatibility contract

## Non-negotiable parity

macOS and Windows must use the same Remotion source, package lock, fonts, audio, manifests, component tree, timeline, codec arguments and QA thresholds. Platform support may change only command launch, executable discovery and filesystem operations.

## Universal command

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" --help
```

macOS/Linux may use `.sh` aliases. Windows may use `.cmd` aliases. Both delegate to the same `notebook-video.mjs`.

## Requirements on both systems

- Node.js 18 or newer with npm;
- Python 3;
- FFmpeg with `ffmpeg` and `ffprobe`;
- network access for the first npm install and Remotion browser preparation, unless dependencies and the tested browser are already present.

Run:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" check-deps
node "<SKILL_DIR>/scripts/notebook-video.mjs" new-project "./notebook-video-project"
node "<SKILL_DIR>/scripts/notebook-video.mjs" prepare-browser "./notebook-video-project"
```

## macOS notes

Use Terminal with the universal Node command; executable permission on `.sh` files is optional because the Node entry does not depend on it. Do not copy `node_modules` from Windows. Install dependencies on the Mac through the launcher. On Apple Silicon and Intel, npm selects the native packages from the pinned lockfile.

## Windows notes

Command Prompt and PowerShell are both supported. The `.cmd` wrapper does not require changing PowerShell execution policy. Python is detected as `py -3`, `python` or `python3`. Do not copy `node_modules` from macOS. Keep rendering projects outside OneDrive or other sync folders to avoid file locks.

## Paths

Always quote paths. Spaces and non-ASCII names are supported, but short local paths reduce Windows long-path and antivirus problems. The launcher accepts either slash style.

## Rendering browser

The default is Remotion's tested browser, prepared by `prepare-browser` or automatically during render. This provides the best visual parity. In a restricted environment, set `REMOTION_BROWSER_EXECUTABLE` to an existing compatible browser executable before `prepare-browser` or `render`. A manual override is an environment workaround, not a different rendering engine, and should be followed by the full visual QA.

Examples:

macOS/Linux:
```text
export REMOTION_BROWSER_EXECUTABLE="/absolute/path/to/chrome"
```

Windows Command Prompt:
```text
set REMOTION_BROWSER_EXECUTABLE=C:\absolute\path\to\chrome.exe
```

Windows PowerShell:
```text
$env:REMOTION_BROWSER_EXECUTABLE = "C:\absolute\path\to\chrome.exe"
```

## Output parity

The launcher uses identical Remotion and FFmpeg settings on both platforms: H.264 video, 2560×1440, native 30fps, normalized narration near -16 LUFS, 48kHz stereo AAC at 192kbps and `faststart`. Run the same video QA after every render regardless of operating system.
