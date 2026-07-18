# Contributing

## Scope

Keep one official implementation. Do not introduce candidate and approved variants side by side, separate Windows/macOS renderers, silent fallback engines or unvalidated visual replacements.

## Before opening a pull request

1. Create a focused branch from the latest default branch. Do not work directly on `main`.
2. Keep the same Node launcher as the authoritative cross-platform implementation.
3. Run `node scripts/notebook-video.mjs validate-skill` and `node scripts/notebook-video.mjs validate-official-example`.
4. Run `npm audit --package-lock-only --ignore-scripts` in `assets/example-project`.
5. For visual or timing work, create a clean project with `new-project`, range-render the affected scene, then complete a full validated render before proposing a new default.
6. Preserve source and third-party license notices.
7. Do not add credentials, generated `node_modules`, cache directories, raw render intermediates or personal project files.

Open a pull request using the repository template. Include the commands actually run, the result, screenshots or a short range render for visual changes, and any validation you could not run. CI must pass before merge.

## Visual changes

The warm-ivory notebook system, subtitle geometry, native 30fps delivery, Remotion renderer and source package workflow are intentional defaults. A proposal that changes any of them needs a rendered comparison and explicit approval before it replaces the official example.
