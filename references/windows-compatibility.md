# Windows-specific compatibility notes

## Contents

- [Goal](#goal)
- [Supported entry point](#supported-entry-point)
- [Required applications](#required-applications)
- [Paths](#paths)
- [Python launcher differences](#python-launcher-differences)
- [npm and native packages](#npm-and-native-packages)
- [Rendering browser](#rendering-browser)
- [FFmpeg output parity](#ffmpeg-output-parity)
- [Common Windows failures](#common-windows-failures)

The binding two-platform contract is `cross-platform-compatibility.md`.

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
- the copied stream carries one self-consistent color contract — `pix_fmt=yuv420p`, `color_range=tv`, `color_space=bt709`, `color_transfer=bt709`, `color_primaries=bt709`;
- narration is normalized toward -16 LUFS;
- 48kHz stereo AAC at 192kbps;
- `faststart` is enabled;
- final QA verifies H.264/AAC, 2560×1440, native 30fps, duration, loudness, true peak and black frames.

Therefore Windows adaptation must not produce a different visual style or timeline.

### Why the color contract is pinned

Remotion's own default is `--color-space=default`, which emits no color flags at all: the encoder writes `yuvj420p` (full range) with `color_space=bt470bg` and `color_transfer`/`color_primaries` missing. Players that find no transfer/matrix fall back to BT.601 and interpret a full-range signal as limited range, so saturated colors shift slightly on strict players.

Two steps are required, in this order, because neither alone is enough:

1. `--color-space=bt709` on the Remotion render. It passes `-colorspace:v bt709 -color_primaries:v bt709 -color_trc:v bt709 -color_range tv` **and** (since `@remotion/renderer` 4.0.83) really converts the pixels to limited range through `zscale=matrix=709:matrixin=709:range=limited`. Without this step the frames stay full-range, and merely re-tagging them would expand the contrast.
2. A `h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0` bitstream filter on the copy, applied in place by `scripts/notebook-video.mjs`. FFmpeg ignores `-color_primaries`/`-color_trc` on a copied stream ("has not been used for any stream"), and Remotion's own final stitch re-muxes with `-c:v copy` the same way, so `--color-space=bt709` alone still leaves `color_primaries` and `color_transfer` reported as `unknown`.

Verified on `@remotion/cli` 4.0.526 and Windows FFmpeg: a 30-frame `render-range` and a full `render` both report `yuv420p / tv / bt709 / bt709 / bt709`, and a decoded frame matches the Chrome screenshot pixel-for-pixel within ±1 on a neutral background.

## Common Windows failures

### `npx remotion` hangs and has to be killed

Symptom: `npx remotion ...` never returns. The process burned 2.3 seconds of CPU over 15 minutes, spawned no child process and printed nothing at all, so it could only be killed.

Cause: `npx` adds a package-resolution layer that this workflow does not need. The launcher, the `.cmd`/`.sh` wrappers and the template's `npm run render` / `npm run still` scripts all resolve the already-installed local CLI instead, which costs nothing extra. When the local `remotion` cannot be resolved, `npx` has to reach the registry, and that is the step that waits without output — the exact "low CPU, zero output, no children" shape above. Measured on this machine: in a project that already has `node_modules`, `npx remotion --version` returns in 1.9s (Git Bash), 1.6s (cmd.exe) and 3.1s (PowerShell) — no faster than the local CLI; in a directory without `node_modules` it either fails fast with the npm error "could not determine executable to run" (2.3s) or retries silently for ~71s before giving up with an npm ECONNREFUSED error when the registry is unreachable. There is no scenario in which `npx` is the better call.

Correct command — call the local CLI directly and point it at the already-cached browser, which bundles in about 2 seconds:

```text
cd "<PROJECT_DIRECTORY>"
node node_modules/@remotion/cli/remotion-cli.js render src/index.tsx NotebookVideoFilm renders/out.mp4 --browser-executable="%LOCALAPPDATA%\remotion-browser\chrome-headless-shell\win64\chrome-headless-shell.exe"
```

`scripts/notebook-video.mjs` already does exactly this (it also falls back to that cached browser automatically on Windows when `REMOTION_BROWSER_EXECUTABLE` is unset), so prefer `node "<SKILL_DIR>/scripts/notebook-video.mjs" render ...` or the `render-remotion.cmd` wrapper. Never rewrite the documented workflow as `npx remotion ...`.

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
