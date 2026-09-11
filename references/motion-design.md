# Motion design contract

## Contents

- [Cadence](#cadence)
- [Standard motions](#standard-motions)
- [Shot camera (受限配方 + 出界证明)](#shot-camera-镜头受限配方与出界证明)
- [Anti-PPT Functional Component Invariant](#anti-ppt-functional-component-invariant-反-ppt-实体交互组件铁律)
- [Transitions](#transitions)
- [Stop-motion accent](#stop-motion-accent)
- [Rejection flags](#rejection-flags)

## Cadence

Deliver at native 30fps. Keep scene constants, physical poses, subtitle reveal and output in the same 30fps coordinate system. Do not duplicate frames into a 60fps container. For an intentional stop-motion accent, quantize only that component to 15fps so each pose holds for two output frames.

The camera is **per shot**, not one film-wide track. Each shot declares one intent from a closed set and an `anchor` that must stay visible; the arithmetic proof lives in [shot-language.md](shot-language.md). Quotas: ≥3 camera moves per chapter, ≤1 per shot, 30–45 frames each, easeInOut, zoom ≤1.35 on shots carrying text, and the chrome card / header / subtitle sit **outside** the camera so they never move. Keep scale always >=1 so the canvas never shows outside the stage. Author `still` only deliberately — a film with no camera at all reads as page-turning.

Keep stable layout coordinates fixed and animate movement with `translate3d`, rotate, scale and opacity. Mount only the active scene, plus the incoming scene during a short transition.

## Standard motions

- Camera: one intent per shot (`establish` / `push-in` / `pull-back` / `pan-follow` / `reveal` / `micro-orbit`), parameters and zoom budgets per [shot-language.md](shot-language.md). The narrated `anchor` must stay fully inside the frame at every keyframe — proved by `scripts/validate-shot-motion.py`, not by keeping the camera still.
- JumpInText title: per-glyph 3D flip-in (rotateX ~88deg from the baseline, 12px rise, spring over-bounce, ~1.6-frame stagger). Always for chapter and scene titles.
- WaveText latin: per-letter wave typing with a color gradient (10-frame wave, 4 keyframe offsets), for CTA latin strings.
- Figure roll-in: multi-keyframe rotation (150deg to 360deg with a mid-scale bulge) instead of a plain pop for emblem graphics.
- Subtitle reveal: one word at a time, chars inside a word stagger by 0.9 frames, 6px fade-slide, 180ms lead over the word start; all trailing punctuation strictly eliminated; never a decorative bar.
- Paper entry: cubic ease-out, one 8–13% overshoot, settle within about 0.8s.
- Paper lift: raise position and increase shadow distance/blur while lowering shadow alpha.
- Paper landing: close/darken shadow, compress no more than 3%, then settle once.
- Curved transfer: follow the same SVG geometry as the visible rail; do not approximate with a different sine path.
- Directed data line: animate `stroke-dashoffset` only from sender to receiver during transfer.
- Check state: scale 0 → 1.12 → 1 and add one soft chime.
- Slot insertion: remain above the base until crossing the slot, then pass behind the front lip.
- Complete exit: move the entire component outside the canvas or remove it after it is fully out; never leave a clipped corner.
- Character reaction: move separate arms, face or body parts; do not wobble one flattened character image.

## Motion polish: multi-clock motion (v2.9.0)

**根因诊断**：模板里每个组件原本都是「一个元素的、一个属性、一条曲线、动完永久静止」。
所有看起来丝滑的开源库都在动**同一元素的多个属性、用不同的时钟**，并且画面里永远有
一个缓慢的背景运动。下面六条是把"丝滑"从形容词变成参数。

1. **多时钟**：同一元素的位移与透明度用不同时长（参考 number-flow：位移 900ms / 透明度 450ms，
   约 2:1）。本模板取：数值位移 27 帧 / 透明度 14 帧；卡片入场 透明度 16 帧 / 位移 20 帧。
   同长同曲线会读成"一个刚体弹出"。
2. **入场与出场曲线不同**：出场快而急（`Easing.in(Easing.quad)`，约为入场时长的 60%），
   入场慢而稳（`Easing.bezier(0.16,1,0.3,1)`）。这是最容易被感知到的一条。
3. **不要只动透明度**：每个淡入都配 10–24px 位移或 2–6% 缩放。30fps 下纯淡入只有
   约 30 个可辨中间态，且没有空间线索。
4. **数值用 `tabular-nums` + 固定小数位**（`fontVariantNumeric:'tabular-nums'`，
   `minimumFractionDigits === maximumFractionDigits`）。否则数字每帧改变宽度、整格横向抖动
   ——这是"看起来不丝滑"最常见的真实原因。
5. **进度类动 `scaleX`，不动 `width`**（进度条、漏斗条、时间轨填充）。`width` 是布局属性，
   会重排，而且会让圆角胶囊在动画中途被拉变形。父容器保留 `overflow:hidden` 与圆角。
6. **过冲只给物体，不给数值**：印章/横幅可以 0.94→1.03→1 弹一下，百分比与环不能弹
   （会短暂显示错误的数）。环要"落定"就给容器 scale 一个 1→1.03→1。

**Rule 5 · 环境运动（每镜一处，永不停止）**：所有元素都"动完即永久静止"时，画面读起来像被暂停。
每镜保留**一处**缓慢的背景运动：幅度 ≤4%、周期 120–180 帧、`Easing.inOut(Easing.sin)`，
**只放在背景/次级元素上**（本模板用 `shotkit.ambientBreath(f)` 施加在底托上），
绝不放内容层——内容只在语义节点变化。这一条是"正面要求"，与下面"不要随机漂移"的禁令不冲突：
禁令针对的是没有叙事理由的抖动，环境运动提供的是前景参照。

配套的两条结构性要求：
- **每镜保留一个全程缓慢的"环境运动"**（≤4% 幅度、周期 90–180 帧、`Easing.inOut(Easing.sin)`），
  且**只在停驻时**呼吸——行驶/进行中不要抖动，"一直在微动"不算语义变化。
- **状态机推进要有动作**：`PhaseRail` 的当前点脉冲 + 光晕、连接线按拍画出、完成态用
  **描线**而不是缩放入场（对勾是笔画，应当画出来）。

## Shot camera (镜头受限配方与出界证明)

**v2.10 起取代旧的 Camera Micro-Framing Invariant。** 旧铁律把相机锁在 `x ∈ [945,975]`、`s ∈ [1.00,1.018]`
（景别变化 1.8%，等同定焦），而且是**全片一条关键帧轨道**，所以每个镜头不可能有自己的取景；
同时 3:4 的 `CAM_KEYS_P` 反而有 10 个关键帧越界且无人发现。两个极端都来自同一件事：**没有校验**。

现行规则：

1. **每个 shot 一个 intent**，取值仅限 `establish` / `push-in` / `pull-back` / `pan-follow` / `reveal` / `micro-orbit` / `still`；
   曲线形状由 intent 决定，调用方只填少量参数 —— 自由曲线一律不接受。
2. **每个 shot 必须声明 `anchor`**（本镜必须始终可见的矩形）。`safeCheck()` 与
   `scripts/validate-shot-motion.py` 用同一套纯算术证明 `anchor` 在所有关键帧都落在可见窗内；
   任一越界即 P0，阻断渲染。
3. **配额**：每章 ≥3 次运镜、每镜 ≤1 次、单次 30–45 帧 easeInOut；全片 ≥3 种 intent。
4. **缩放预算**：含文字的镜头 `s ≤ 1.35`，纯图形镜头 `s ≤ 1.60`；
   需要"更大"时优先**把主角画大**，而不是把相机推近（推近会牺牲文字锐度）。
5. **页眉 / 章节卡 / 字幕在相机之外**（屏幕空间），结构上不可能被运镜带动。
6. **景深视差**：`DepthLayers` 系数只用 `0.35 / 0.70 / 1.00`，层数 ≤3，远层必须有真实内容。
7. **不要**重新引入全片级相机轨道。取景是镜头级的。

镜头部分的完整参数表与写法见 [shot-language.md](shot-language.md)（本文件只保留与动效相关的部分）。

## Anti-PPT Functional Component Invariant (组件防 PPT 化与功能实体化)

Never stack plain text bullets inside generic rectangular boxes. Every explanation scene must incorporate at least one function-driven interactive component with physical state transitions synchronized to narration:

- `BrainwaveEEG`: Oscilloscope cognitive pulse wave; flatlines to a straight red line upon session exit, memory flush, or failure.
- `VectorRadarSonar`: Circular radar display with rotating scan line, vector cluster dots, and ANN metrics.
- `BM25TokenRibbon`: Dynamic inverted index symbol meter with token tags and match scores.
- `HookMountBay`: Modular connector dock where agent hook plug visibly inserts into target port and lights up green.
- `RedactionScanner`: Real-time security preview with a red laser scanner sweeping over sensitive tokens and masking them to `[REDACTED_SECRET_KEY_*****]`.
- `ChipContract`: Floating micro-hardware chip contract with LED indicators and pin headers moving along data pipelines.

## Locked motion pack

- Spring presets: use `popS(f, start, preset)` with `SPRINGS` — `snappy` for small UI ticks and code lines, `soft` (identical to the legacy `pop`) for cards and lists, `bouncy` for callouts and celebratory beats. Do not hand-tune new damping/stiffness values per scene.
- Scene transitions: wrap the incoming scene in `TransitionIn` (`flip` = page turn when the metaphor changes, `slide` = cover-over for a lateral topic shift, `wipe` = edge reveal for a detail focus). **No scene overlap, ever**: the outgoing scene must finish its exit and fully unmount (or reach opacity 0) before the incoming transition starts — no frame may show two scenes at once. Only the incoming scene carries the transition effect. Use at most one transition style per film and keep clean cuts elsewhere.
- Camera script: build new keyframe tracks with `camScript(x, y, duration).hold(f).to(f, {x, y, s}).done()` instead of raw keyframe tables; it guarantees first/last frame coverage. The same easing and exponential lag follow-focus apply.
- Stop-motion accent: `useSteppedFrame(15)` quantizes a component to 15fps so each pose holds two output frames. Reserve it for sticker-style charm; never apply it to subtitles, transfers or the camera.
- Component motion stays inside the locked library: `Connector` animates dash flow only during transfer, `Checklist` rows slide in with staggered `soft` springs, `CodeBlock` lines enter with `snappy` springs, `CountUp` eases with the standard soft-out curve.

## Scene grammar

Build progressively:

1. stable chapter and hero;
2. supporting semantic parts;
3. relationship or transfer;
4. local feedback;
5. readable hold;
6. remove obsolete parts completely.

Cause one meaningful semantic change every 2–4 seconds. Do not count random drift, blinking cursors, animated texture, global zoom or constant line motion.

## Spatial density budget

- Divide the 1920×1080 design stage, rendered inside the 2560×1440 composition, into explicit work zones before animating.
- Give each large object a stable home zone and reserve the center corridor for transfer only.
- Keep unrelated paper objects at least 70px apart, including their airborne shadows.
- Allow one dominant transfer object in the corridor at a time.
- Prefer 3–5 large semantic objects over 8–12 small decorative objects.
- Remove, cover or move completed objects fully before the next semantic group arrives.
- If the frame feels crowded, increase object size and redistribute it; do not solve crowding by shrinking everything.

## Continuous process rule

When the narration describes one task moving through several steps, keep one persistent task card. Move it along one visible path and change its label, color or status at each station. Do not replace it with a newly spawned card unless the narration explicitly describes a new object.

## Physical assembly rule

Model the slot, front lip, inserted part and status feedback as separate layers. Keep the part above the base before crossing the slot. After crossing, lower its z-order beneath the front lip and fade or translate it to complete invisibility. At the end of insertion, assert that no pixel-sized corner remains outside the machine.

## Duration guidance

- 30 seconds: 5–7 scenes.
- 60 seconds: 3–4 acts with small internal steps.
- 2–3 minutes: 8–12 sections, usually 10–20 seconds each.

Use a clean cut when the metaphor changes. Continue progressive construction while the same concept develops.

## Restraint

Do not apply every effect to every object. Dynamic shadow requires actual lift. Data pulses require an active transfer. Sound requires a visible action. Keep fixed panels fixed.
