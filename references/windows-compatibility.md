# Windows-specific compatibility notes

The binding two-platform contract is [cross-platform-compatibility.md](cross-platform-compatibility.md).

## Goal

Windows support must not change the Remotion component tree, scene timing, fonts, assets, codec settings, subtitle geometry, physical-motion quantization or final aesthetic. Only the command-launch and filesystem layer differs by operating system.

## Supported entry point

Use the cross-platform Node launcher from Command Prompt, PowerShell, macOS or Linux:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" --help
```

Windows also includes a Command Prompt wrapper that does not require changing PowerShell execution policy:

```text
"<SKILL_DIR>\scripts\notebook-video.cmd" --help
```

The individual Windows wrappers `check-deps.cmd`, `new-project.cmd`, `sync-project-assets.cmd`, `render-remotion.cmd`, `validate-video.cmd` and `package-project.cmd` are convenience aliases for the same Node implementation.

## Required applications

Make these commands available on `PATH`:

- Node.js 18 or newer, including npm;
- Python 3, exposed as `py -3`, `python`, or `python3`;
- FFmpeg, including `ffmpeg` and `ffprobe`.

A separate `zip` program, Bash, GNU `sed`, `grep`, `awk`, `install`, `cmp`, `cp` or `chmod` is not required on Windows. Packaging uses Python's standard `zipfile` implementation.

After installation, close and reopen the terminal before running:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" check-deps
```

## Paths

Always quote paths. The launcher accepts spaces, non-ASCII folder names and either slash style. Prefer short project paths when possible, for example:

```text
D:/VideoProjects/notebook-video-project
```

Do not create the project inside a cloud-sync folder while rendering. File locking by OneDrive or antivirus software can interrupt Chromium, npm or FFmpeg temporary files. Copy the finished source ZIP into the sync folder after packaging instead.

## Python launcher differences

The Node launcher automatically tries these commands:

1. Windows `py -3`;
2. `python`;
3. `python3`.

Do not hard-code `python3` in Windows workflows.

## npm and native packages

The pinned `package-lock.json` already contains the Remotion, Rspack and esbuild Windows x64 packages. Run the normal project creation workflow and let the launcher execute `npm ci`. Never copy an existing `node_modules` directory from macOS or Linux to Windows; native packages must be installed on the current operating system.

## Rendering browser

Prepare the pinned Remotion browser after project creation:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" prepare-browser "D:/VideoProjects/notebook-video-project"
```

Remotion manages its rendering browser. If a restricted network prevents the browser binary from being prepared, resolve that environment constraint rather than changing the visual engine. The optional network shim remains opt-in through `REMOTION_USE_NETWORK_SHIM=1` and does not alter the rendered component tree.

## FFmpeg output parity

The cross-platform launcher invokes the same FFmpeg arguments on all systems:

- H.264 video from Remotion is stream-copied;
- narration is normalized toward -16 LUFS;
- 48kHz stereo AAC at 192kbps;
- `faststart` is enabled;
- final QA verifies H.264/AAC, 2560×1440, native 30fps, duration, loudness, true peak and black frames.

Therefore Windows adaptation must not produce a different visual style or timeline.

## Common Windows failures

### Command is not recognized

Reopen the terminal after installing Node, Python or FFmpeg, then run `check-deps` again. Confirm the application directory was added to the user or system `PATH`.

### PowerShell blocks scripts

Use `node scripts/notebook-video.mjs ...` or the `.cmd` wrapper. Neither requires changing PowerShell execution policy.

### npm installation fails with locked files

Close Remotion Studio, editors and Explorer preview panes that are using the project. Delete only the project's `node_modules` directory and run render again; do not copy `node_modules` from another operating system.

### Very long path error

Move the skill and project closer to the drive root. Avoid deeply nested cloud folders. The source package preserves relative project paths, so moving the folder does not change the film.

### Antivirus blocks Chromium or FFmpeg

Allow the installed Node, Remotion browser and FFmpeg executables, or render in a trusted local working directory. Do not disable asset validation or switch renderers to bypass the block.
