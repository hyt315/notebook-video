# Portrait (3:4) illustration and layout ideas — unverified

**3:4 has not been adequately tested in this review.** This file is an optional collection of design hypotheses and SVG examples, not a validated recipe or production guarantee. Do not turn its cast, palette, three-band layout, idle motion, or text limits into hard requirements. The implementation values are listed in `canvas-modes.md`; their presence does not establish readability.

There is no universal portrait rule that illustration must dominate or that in-scene text must be brief. Choose the visual carrier that makes the narrated learning relation understandable, then test the actual 3:4 render at its intended phone size.

## 1. Text vs graphic role split

- Synchronized captions can support access to the narration, while in-scene text can name, compare, or explain the pictured relation. Whether to repeat, summarize, or add a label depends on the learning task and audience.
- A full-width bar with short text may work when the text is the lesson; an illustration, chart, or process diagram may be better for spatial or causal relations. Judge the rendered hierarchy, not whether a band is filled.
- A beat may use text, a diagram, a screenshot, a process view, an illustration, or a purposeful combination. There is no one-illustration-per-beat requirement.

## 2. Reusable code-drawn figure library

Named character/object components can be drawn in SVG and sized by `viewBox`/`size`. The following snippet is one optional animation sketch; a still pose is equally valid when it communicates clearly.

```tsx
// Optional subtle motion sketch; keep the figure static if motion adds no meaning.
const ElderPhone:React.FC<{f:number,size?:number}>=({f,size=250})=>{
  const bob=Math.sin(f*0.08)*3;                    // gentle idle bob
  return <svg width={size} height={size*1.15} viewBox="0 0 200 230" style={{transform:`translateY(${bob}px)`}}>
    {/* shoulders → head → glasses → worried brows → phone at ear */}
  </svg>;
};
```

Possible choices to test, not rules:
- Reuse a small cast across a series when that helps viewers track roles; do not invent characters when a label, diagram, or real interface is clearer.
- Keep line weight, palette, motion, and grounding consistent with the film's chosen visual treatment.
- Static figures are allowed. Any idle motion should have a reason and should not compete with the instructional carrier.

## 3. Decorative margin treatment (optional)

If a particular composition benefits from subtle margin decoration, a sparse SVG layer is one possible treatment. Whitespace may also be intentional; do not add decoration merely to make the frame feel busy. This untested snippet is not a template default:

```tsx
const AMB=[[70,300],[1004,280],[58,700],[1012,660],[92,1116],[1000,1120],[150,182],[930,178],[520,120],[300,1180],[788,1180],[40,940],[1030,940],[222,540],[862,520],[540,1266]] as const;
const Ambient:React.FC<{f:number}>=({f})=><svg width={1080} height={1440} style={{position:'absolute',left:0,top:0,zIndex:55}} aria-hidden="true">{AMB.map((p,i)=>{const tw=0.05+0.07*(0.5+0.5*Math.sin(f*0.05+i*1.3));const k=i%3;return <g key={i} opacity={tw} transform={`translate(${p[0]} ${p[1]})`} stroke={C.muted} strokeWidth={2.4} fill="none" strokeLinecap="round">{k===0?<circle r={7}/>:k===1?<path d="M-7 0h14M0 -7v14"/>:<path d="M-8 4h5M-1 -2h5M6 4h4"/>}</g>;})}</svg>;
```

If used, inspect it over the full film and at phone size: even low-contrast twinkle can distract from reading. Remove it if it adds no instructional value.

## 4. Text emphasis kit

When emphasis helps identify the concept being discussed, options include:
- **Highlighter marker** behind a key phrase (auto-fits the text, classic hand-drawn marker):
  ```tsx
  <span style={{background:'linear-gradient(transparent 60%, rgba(210,161,40,.30) 60%)',padding:'0 10px'}}>声音<span style={{color:C.red}}>一模一样</span></span>
  ```
- **Hand-drawn underline swipe** (a slightly wavy gold stroke) under a payoff line.
- **Contrast label pair** next to a picture to add meaning and fill side space, e.g. blue「你以为是"妈妈"」under one figure vs red「其实是骗子」under the other.
- **Count-up number** only when the change in value is part of the explanation; a static, legible number is often simpler. Any highlight or sound cue should align with the spoken reference, not merely the beat.

## 5. Scene structural bands

One possible portrait layout divides the usable region into:
- **Heading band** (top, ~y200–320): a short centered title, optionally highlighted.
- **Hero band** (middle, ~y330–840): the code-drawn illustration/figure — the largest, most-read element.
- **Payoff band** (lower, ~y850–1180): the punch label, the checklist, or the CTA.

Pattern sketches to prototype and review (not proven for 3:4):
- **Process beat**: `wave → [Robot] → wave` with duplicate faint copies on the fake side to imply scale.
- **Checklist beat** (3 steps): left icon-chip (196px rounded card, accent border, number badge) + right title & 2 short lines; a dashed **spine** links the badges top-to-bottom and a green **CheckBadge** stamps each chip as its detail reveals.
- **End beat**: warm family/shield illustration + pill labels + a gold collect **Star** with radial burst rays + waving mascot.

## 6. Implementation and review notes

- The existing 3:4 wrapper uses a 1080×1440 design space scaled for delivery. Confirm the active wrapper/composition values and inspect actual layout before using these coordinates; do not infer overall support from the code.
- Keep chapter metadata synchronized with shot boundaries; this is a technical consistency check independent of visual style.
- Review early and late frames, icon bounds, overlaps, and spacing in the actual render. Do not enlarge content or accelerate a reveal simply to eliminate negative space; fix only concrete readability or timing issues.
- Gaps, text sizes, and caption lengths are context-dependent. Use overlap/readability checks as diagnostics and confirm in the rendered mobile view rather than treating any fixed pixel gap or type floor as universal.

## 7. Choosing the vehicle: text and graphics stay co-stars

The options below illustrate different carriers; none is universally preferred. Keep the visual task mandatory: every narration cue needs a readable picture/text/chart/process carrier that supports its declared core relation.

- **Text-forward** — a titled panel, checklist, comparison, or formula may be best when the wording itself is the concept. Keep it large enough to review at target size.
- **Graphic-forward** — a diagram, process view, or illustration may be best for scenes, transformations, and relationships; labels should name the relevant parts.
- **Use combinations only when they clarify.** A list may remain a checklist, a call interaction may be a sequence, and a static diagram may support several sentences. The right form depends on the narrated relation and the viewer's reading time.
