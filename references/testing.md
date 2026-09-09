# Testing and verification boundaries

## Fast checks

```text
python scripts/selftest.py
python -m unittest discover -s tests
```

The original self-test validates the two templates, links, manifests and basic negative fixtures. The additional tests cover invalid timestamp streams/cue ends, failed retiming without mutation, secret-safe packaging, failed FFmpeg analysis, TTS cache identity/format normalization, active segment selection, repeated pacing and exact locked chapter reconstruction with synthetic media.

Python tests use the standard library. Audio integration tests need FFmpeg/ffprobe, but no network service or API key. Root `scripts/*.py` and the copied template's scripts should both be syntax-checked.

## Real browser smoke test

```text
python scripts/render-smoke.py /absolute/path/to/empty-test-workspace --video
```

Pass `--browser /absolute/path/to/chrome` or set `REMOTION_BROWSER_EXECUTABLE` to reuse an installed browser. The workspace must be empty and outside this repository. The test copies the lecture and classic projects, installs its locked npm dependencies and leaves logs, frame images and `results.json` there for inspection.

Coverage:

- all four themes on all three canvases at a dense frame, plus the classic template;
- fxkit import and the evidence recipe under every theme;
- first/final frames and both sides of every scene cut;
- a missing image must fail during rendering;
- a deliberately overflowing card must fail the browser gate;
- overwide captions must fail on 4:3 and 3:4;
- optional 12-second evidence-bridge movie with a reproducible raster fixture.

The fixtures are code-generated diagrams and a synthetic tone. They verify rendering, not real speech alignment or image-model quality. The recipe film is a visual experiment, not a narrated final deliverable. Run a real narration/listening pass before claiming end-to-end acoustic quality.

## Project QA

`validate-project` groups manifest, layering, caption-stream and semantic-boundary checks, and checks a minimum narration tail from the supplied timestamps. `review-plan` creates ranges around scene cuts, beat annotations, opening/final frames and a longest-caption candidate. It does not certify pixels.

`CaptionFitGate` measures with the selected canvas font/width. `CardFitGate` waits for fonts and blocks each captured frame until its static card-layout scan completes. Its automatic card heuristic and offset-chain checks do not cover every SVG, transform, crop or collision. Never call it a complete layout guarantee.

`validate-video` fails when FFmpeg analysis fails, duration is unavailable, audio/container constraints are wrong or the contact sheet is missing. Contact sheets preserve portrait/4:3 aspect ratios. Black detection does not detect an empty cream-colored content region; inspect those in the boundary-aware review.

## Performance comparisons

Compare the same frame range, canvas, theme, concurrency and browser with a warm cache. Do not claim speedups from mismatched samples. Unchanged sync inputs keep their mtimes; dependency installation is keyed by the lockfile; image decoding uses native Remotion gates. Full renders use unique temporary raw files. These reduce unnecessary work or avoid races, not a promised percentage improvement.

## Portability

The command launcher and standard-library tests are intended for Node 20+, Python 3.10+, Windows, macOS and Linux. Linux smoke coverage is automated. Do not claim the other OS/browser combinations were executed merely because wrappers exist. The POSIX subprocess-stub test is skipped on Windows; real media tests exercise FFmpeg there.
