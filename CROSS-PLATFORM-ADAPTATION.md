# macOS + Windows cross-platform adaptation

This build keeps one official `warm-ivory-remotion-2k30-v9-visual-director` Remotion project for every operating system. The component tree, fonts, registered image assets, timing, subtitle geometry, native 30fps motion, 2K/30fps output and FFmpeg settings are shared. Only the launcher, optional image-generation provider and filesystem layer adapt to the host OS.

## Universal entry

Use this command on macOS, Windows Command Prompt or Windows PowerShell:

```text
node "<SKILL_DIR>/scripts/notebook-video.mjs" --help
```

Convenience wrappers call the same implementation:

- macOS/Linux: `scripts/*.sh`
- Windows: `scripts\*.cmd`

The wrappers contain no separate rendering logic, so the two platforms cannot drift into different visual results.

## Cross-platform changes

- Native Node filesystem operations replace `cp`, `install`, `cmp`, `grep`, `sed` and `awk`.
- Python is resolved from `py -3`, `python` or `python3`.
- ZIP packaging uses Python's standard library instead of an external `zip` command.
- npm is invoked safely on both POSIX and Windows.
- Paths with spaces and non-ASCII characters are quoted and resolved by Node.
- Remotion's pinned CLI is invoked directly through Node.
- Browser preparation is available through `prepare-browser`; an exact local browser path may be supplied with `REMOTION_BROWSER_EXECUTABLE` in restricted environments.

## Verification performed

- official exemplar and skill-wide consistency validation;
- project creation, render-input synchronization and packaging;
- paths containing spaces;
- Node and Python syntax checks;
- Remotion dependency installation and bundle compilation;
- FFmpeg/FFprobe container, loudness, black-frame and contact-sheet QA;
- SHA-256 comparison confirming the official example-project remains unchanged.

The build environment was Linux, so macOS and Windows wrapper behavior was statically audited rather than executed on native machines. The universal Node path is the authoritative entry on all systems.
