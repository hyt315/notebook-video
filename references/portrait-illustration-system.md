# Portrait illustration system (3:4) — illustration-first grammar

This reference captures the portrait (3:4) visual grammar verified on a produced pilot. It sits on top of `canvas-modes.md` (which fixes the 1080×1440 design space) and tells any AI **how to fill that space so it never reads empty or text-heavy**. Read it whenever the canvas mode is 3:4 portrait.

The one-line rule: **on portrait, the illustration is the hero and the in-scene text is a short label — the full narration already lives in the bottom subtitle strip, so never restate whole sentences inside the frame.**

## 1. Text vs graphic role split

- The **subtitle strip** carries the complete narration verbatim. In-scene text must therefore be **short key labels only** (a title, a punch phrase, a 2-line note), never a paragraph.
- Do **not** stack full-width Paper "bars" with a short line of text crammed at the left — that is the landscape habit and it looks empty on a tall frame. Either center the text, or pair it with a code-drawn illustration/icon that fills the row.
- Every beat = **one code-drawn scene/figure (hero) + a short label**. Text supports the picture; the picture is not decoration for the text.

## 2. Reusable code-drawn figure library

Portrait scenes are carried by named character/object components drawn purely in SVG (no raster images), in the warm palette, sized by `viewBox` and scaled with the `size` prop. Give each a subtle idle animation so nothing sits dead-still.

```tsx
// A worried elder on the phone — bob + blinking-style micro motion
const ElderPhone:React.FC<{f:number,size?:number}>=({f,size=250})=>{
  const bob=Math.sin(f*0.08)*3;                    // gentle idle bob
  return <svg width={size} height={size*1.15} viewBox="0 0 200 230" style={{transform:`translateY(${bob}px)`}}>
    {/* shoulders → head → glasses → worried brows → phone at ear */}
  </svg>;
};
```

Build a small cast per topic (e.g. `ElderPhone`, `Scammer`, `Robot`, `FamilyShield`) plus object icons (`SrcIcon`, hand/lock/face arts). Rules:
- warm palette only (`C.ink` outlines, `C.paper`/`#f1dcc3` fills, accent colors); stroke 2.4–3.2.
- idle motion driven by the scene-local frame `f`: bob `sin(f*0.08)`, blink `(f%56)<3`, pulse `sin(f*0.14)`.
- ground shadow ellipse under every standing figure for weight.
- reuse the same cast across a series — this is the channel's visual IP.

## 3. Ambient fill layer (kills "empty" negative space)

Sequential reveal leaves early frames sparse and the wide beige margins read as void. Add one **persistent faint scatter layer** per scene, low opacity with a slow twinkle, behind the content (zIndex ~55):

```tsx
const AMB=[[70,300],[1004,280],[58,700],[1012,660],[92,1116],[1000,1120],[150,182],[930,178],[520,120],[300,1180],[788,1180],[40,940],[1030,940],[222,540],[862,520],[540,1266]] as const;
const Ambient:React.FC<{f:number}>=({f})=><svg width={1080} height={1440} style={{position:'absolute',left:0,top:0,zIndex:55}} aria-hidden="true">{AMB.map((p,i)=>{const tw=0.05+0.07*(0.5+0.5*Math.sin(f*0.05+i*1.3));const k=i%3;return <g key={i} opacity={tw} transform={`translate(${p[0]} ${p[1]})`} stroke={C.muted} strokeWidth={2.4} fill="none" strokeLinecap="round">{k===0?<circle r={7}/>:k===1?<path d="M-7 0h14M0 -7v14"/>:<path d="M-8 4h5M-1 -2h5M6 4h4"/>}</g>;})}</svg>;
```

Marks sit in the margins/corners (never dead-center over content), 5–12% opacity. This alone removes most of the "空空荡荡" feeling.

## 4. Text emphasis kit

Short in-scene text still needs presence. Use, in order of preference:
- **Highlighter marker** behind a key phrase (auto-fits the text, classic hand-drawn marker):
  ```tsx
  <span style={{background:'linear-gradient(transparent 60%, rgba(210,161,40,.30) 60%)',padding:'0 10px'}}>声音<span style={{color:C.red}}>一模一样</span></span>
  ```
- **Hand-drawn underline swipe** (a slightly wavy gold stroke) under a payoff line.
- **Contrast label pair** next to a picture to add meaning and fill side space, e.g. blue「你以为是"妈妈"」under one figure vs red「其实是骗子」under the other.
- **Count-up number** for shock stats — but reveal the number only on its narration cue and ramp fast (≈16 frames) with a pop scale; never let it dwell on `0`.

## 5. Scene structural bands

Keep three populated vertical bands inside the y200–1290 content region:
- **Heading band** (top, ~y200–320): a short centered title, optionally highlighted.
- **Hero band** (middle, ~y330–840): the code-drawn illustration/figure — the largest, most-read element.
- **Payoff band** (lower, ~y850–1180): the punch label, the checklist, or the CTA.

Patterns proven on the pilot:
- **Process beat**: `wave → [Robot] → wave` with duplicate faint copies on the fake side to imply scale.
- **Checklist beat** (3 steps): left icon-chip (196px rounded card, accent border, number badge) + right title & 2 short lines; a dashed **spine** links the badges top-to-bottom and a green **CheckBadge** stamps each chip as its detail reveals.
- **End beat**: warm family/shield illustration + pill labels + a gold collect **Star** with radial burst rays + waving mascot.

## 6. Guardrails learned the hard way

- **Author in the 1080×1440 design space, not 1440×1920.** The film wraps content in a 1080×1440 layer scaled ×1.333; coordinates beyond width 1080 overflow the right edge and get clipped. Full cards ≤980 wide, center axis x=540.
- **Chapter chrome boundaries must equal the scene-cut frames.** After setting scene frame ranges, set `Chrome` `stage` boundaries and the `FinalDemo` switch to the *same* frames; a mismatch shows the wrong chapter title over a scene.
- **No transient empty frame and no `0`-dwell counter** — check the contact sheet for a frame that is mostly background; if found, enlarge the current hero or bring the next element's reveal earlier.
