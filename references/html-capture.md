# HTML and website capture

Use this route only when the user explicitly asks to record an existing interactive website. New notebook explainers use the canonical Remotion project instead.

## Preferred website route: deterministic frames

Expose a frame-controlled function such as `window.renderAt(seconds)` or drive animation time from a query parameter. For every output frame:

1. Load the local page in Chromium.
2. Set the exact animation time.
3. Capture a PNG at the delivery dimensions.
4. Encode the ordered PNG sequence with FFmpeg.
5. Add narration and audio in a separate assembly pass.

This is more reproducible than real-time screen capture and avoids dropped frames, cursor movement, browser chrome and notification leaks.

## Fallback: real-time recording

Use only when the page cannot expose deterministic time. Hide browser chrome, notifications and the pointer. Fix viewport size and device scale. Record a silent master first, then assemble clean audio afterward.

Never substitute real-time recording for the Remotion renderer merely because both use Chromium. Never treat recording as validation. Inspect the resulting video stream duration, dimensions, frame rate and scene boundaries.
