# Dependency and reusable-component policy

This file distinguishes three things that have sometimes been conflated:

1. **Python helper scripts** under `scripts/` use the Python standard library only; this is the project's “zero third-party dependencies” statement.
2. **The Remotion application/template** is not dependency-free. Its runtime packages are declared in `package.json` and pinned in `package-lock.json`; install them reproducibly with `npm ci`.
3. **Open-source components/libraries are permitted** when their license, determinism, compatibility and actual rendered usefulness are checked. “No paid generative API in the default route” does not mean “never use open source.”

The first-party project history records that reading “zero dependency” as a blanket ban on open-source React libraries led to weaker hand-written SVGs and repeated custom work. The corrected boundary preserved lockfile-pinned open-source packages while requiring that newly added dependencies be justified, licensed, reproducible and reviewed. Do not change this boundary back into a ban.

## 1. Before adding an external dependency

Check the upstream license and exact package, transitive/runtime weight, maintenance, browser/runtime compatibility, determinism when rendered repeatedly at a fixed frame, and whether the need recurs often enough to justify a reusable wrapper. Prefer an existing locked dependency if it already solves the problem. New dependencies beyond the declared template inventory require explicit user approval; do not install an external project's full stack just to borrow a visual idea.

For reusable components, wrap the library at the template boundary where needed, document its purpose/limits, use deterministic frame-driven behavior, and test Chinese text and the intended output size. Do not copy assets, generated clips, or code from a project without confirming the applicable license.

## 2. Frame and layout invariants

All time-dependent output must be a pure function of the Remotion frame. Do not rely on browser wall-clock CSS animation, `setTimeout`, or unseeded `Math.random()` for rendered video. Use the wrapper layer when it helps maintain a coherent visual treatment; custom local SVG/HTML is also appropriate when it is the simplest correct representation.

Check text fit and diagram geometry in Chinese, not just English examples. Fit helpers and component wrappers reduce repeated errors, but their default values are not universal accessibility thresholds. Inspect the rendered composition at the intended native output and playback sizes.

## 3. Keeping a reusable component library purposeful

The component index is an inventory, not a target size or a demand to use each item. A reusable component is retained because it solves a real repeated task, has license-compatible implementation, and appears usefully in an actual rendered composition or a deliberately maintained showcase—not merely because it appears in a routing table or import statement.

The historical “add one = replace one” principle applies to **growth of the shared reusable library**: first consider a variant/wrapper or retire an item with no actual rendered use. If no item can be retired without losing a demonstrated capability, document the specific need and obtain approval for the dependency/library addition. It does **not** mean replacing one visual object with another in every film, nor does it set a magic global component-count cap.

Historical evidence: a prior library reached 49 components; 23 were not used in any rendered frame, and 21 of those had already been entered in the routing table. Adding a routing row therefore did not create a real use case. The AI chat-box component was removed after source/frame audit showed it never appeared in an output frame; that is not evidence that dialogue boxes are inherently a bad visual form. Evaluate the actual teaching need and the actual render, not a component category by name.

## 4. Inventory maintenance

`references/media-routing.md` holds the current component inventory and usage notes. Keep its version/count information synchronized with source. Mark a component “used” only when it appears in an actual rendered frame (a showcase counts only when it is intentionally maintained as a real demonstration). Remove stale references or clearly label available-but-unused items; do not treat “referenced in the table” as proof of value.

When a project copies the template, shared source files, package metadata, lockfile, theme assets and gates can diverge. Synchronize deliberately and preserve project-specific `scenes.tsx`, shot manifests, captions, audio and assets. After syncing, run typecheck, validators and a representative render; source-copy alone does not prove a gate or component is visible.

## 5. License and asset checks

Keep package licenses and bundled font/media terms available. Use only assets with known usage and redistribution rights appropriate to the project. For external inspirations, borrow general design ideas only unless their code and assets carry a license permitting reuse and all notices/conditions are followed.
