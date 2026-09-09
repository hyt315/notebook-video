# Shot recipes: reuse an operation, not a page

These four recipes combine existing tools. They are starting points, not required scene types or an A/B alternation quota. Choose the simplest combination that explains the content.

| Need | Reuse | Semantic beats | Continuity |
|---|---|---|---|
| Explain a process | SVG route + persistent object + state badge | locate → transfer → arrive → change state | Keep the same object and route between steps |
| Show evidence/detail | `EvidenceZoom` or `EvidenceBridge` + live labels | recognize → locate → explain → return | Keep the same image and focal subject |
| Compare alternatives | `CompareBars`, `CountUp`, `ProgressBar`, `DiffView` | common baseline → meaningful difference → result | Preserve scale, units and position |
| Explain a UI action | `BrowserChrome`, `CodeBlock`, `Checklist`, `Callout` | input → operation → visible feedback | Keep UI context; highlight the relevant region |

A typography-only contrast or final CTA may need none of these. Do not add a mechanism animation to a slogan just to make it move.

## Main/support is a relationship

The main visual carries the argument. Support supplies context, evidence, a concrete example or a bridge into the next idea. It can be a photo, illustration, screenshot, native diagram or code panel. It need not become a separate scene.

Example: show the mechanism with code, keep a concrete subject in a quiet inset, promote the inset when the narration names a detail, annotate it, then return it to the same place. The viewer retains context without a sequence of unrelated pages.

Prefer supplied/authorized images for real evidence. Generated or code-drawn imagery explains concepts but is not proof that an event or measurement occurred. Label illustrations when this distinction matters. Keep exact labels/data in Remotion and register used rasters with provenance.

## Reusable image bridge

`src/recipes/EvidenceBridge.tsx` is a small composition of the existing `EvidenceZoom`, not a new scene scheduler. Its `children` remain the explanatory view. The single image expands from an inset, focuses, then returns. A local transform changes attention; narration, scene duration, global camera, chrome and subtitles do not move.

```tsx
import {EvidenceBridge} from './recipes/EvidenceBridge';

// Frame values use the current scene's local clock. Resolve them from the
// corresponding narration cues, not a fixed fraction of the film's duration.
<EvidenceBridge
  src="illustrations/subject.png"
  label="The detail that supports the explanation"
  frame={localFrame}
  width={1560}
  height={660}
  inset={{x: 980, y: 60, scale: 0.36}}
  beats={{expand: showDetail, focus: locateDetail, conclude: explainDetail, return: resumeExplanation}}
  fx={0.73}
  fy={0.47}
>
  <YourExistingDiagram />
</EvidenceBridge>
```

The parent positions the content viewport outside the subtitle/header areas. The inset must fit inside it. `focus` must follow the 18-frame expansion; `conclude > focus`, `return > conclude`. All beat values are in the same frame domain. Use a different scoped design on portrait, not a scaled landscape screenshot.

`EvidenceZoom` retains its previous props and adds `focusAt`, `concludeAt`, `exitStart`. Give numeric `style.width/height` so crop geometry is explicit. `fx/fy` are normalized coordinates in the **cover-fitted viewport**, not raw source-image pixels. Edge focus is clamped to prevent empty gutters. If an exact edge detail cannot be centered at the chosen zoom, change the crop or use a larger source margin.

For a restrained image hold, use `KenBurnsImg` instead. It uses Remotion `Img`, as does `EvidenceZoom`; cold loading and missing-image behavior are part of the render smoke tests.

## Beats and review

Keep scene windows in the existing asset manifest. Optionally annotate review points:

```json
"beats": [
  {"frame": 286, "action": "The same change follows the visible branch"},
  {"frame": 358, "action": "Arrival becomes a pull request"}
]
```

These are review annotations, not an automatic runtime dispatcher. `review-plan` combines them with actual scene boundaries and caption candidates. After audio changes, update the code's cue bindings and these annotations together. Repeated recipes are acceptable when the meaning repeats; repeated layout with no new operation is a manual-review warning, not a machine-certifiable aesthetic score.

## Why no new animation dependency?

[Remotion animations](https://www.remotion.dev/docs/animating-properties) must be frame-driven. Its existing `spring`, `interpolate`, `Sequence` and `Img` cover these recipes without a browser-clock animation adapter.

[TransitionSeries](https://www.remotion.dev/docs/transitions/) is useful for authored overlaps, but normal transitions subtract overlap duration. Blindly placing measured narration scenes inside it changes the timeline. The image bridge needs neither overlap scheduling nor a new dependency. If a future production genuinely needs TransitionSeries, pin a compatible package and account for overlap explicitly. Do not use newer documentation features without checking the installed Remotion version.
