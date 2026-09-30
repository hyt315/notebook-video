# Teaching-design notes: optional prompts for a shot plan

This page offers questions for planning an explanation, not a required shot taxonomy or a scoring rubric. Use only the prompts that help the topic. An ordinary statement, uninterrupted explanation, static diagram, or deliberate pause may need none of them.

## Optional questions

Before building a visual, an author may note:

- **Teaching move:** Is this passage introducing a concept, locating a detail, showing a process, transferring an object/state, comparing alternatives, decomposing or combining, accumulating evidence, refuting an old value, or revisiting a conclusion?
- **Evidence:** What visible object, relationship, source, or measured result supports the spoken claim?
- **Audience assumption:** Is there a real, likely misconception to address? If not, do not invent one just to create dramatic conflict.
- **Reading hold:** Does the audience need time to inspect a diagram, compare two values, or think? A hold can be static and can be longer or shorter than a neighboring shot.
- **Knowledge bridge:** What previous idea does this part use, and what new idea should it add? This is useful for complex or cumulative material but is not a required field in every manifest.

These are a menu. Do not turn “one action at a time”, “one beat per sentence”, a minimum hold, or a minimum variety of moves into universal gates. Visual change should coincide with meaning when change is useful; it is not necessary just because a sentence boundary exists.

## Optional vocabulary

When a compact label helps an author or reviewer, this suggestion set is available:

`引入` · `定位` · `推进` · `传递` · `对比` · `拆分/合并` · `累积` · `收束` · `反证` · `回看`

The names do not prescribe a component. A comparison could use aligned numbers, a chart, a line of code, an equation, a spoken explanation, or another suitable representation. Do not select a visual because it is listed here.

## What the automated note checks actually do

In `shots.json`, all note fields are optional. `validate-presentation.py` may flag contradictory optional notes and checks basic types. If an `evidence` name is provided, it can confirm only that a corresponding JSX name occurs in some scene source file. It does not check shot-local scope, frame-by-frame movement, factual correctness, or whether viewers understand the evidence. Omitting the note is valid.

## Use evidence with care

Research on misconception-first explanation and multimedia signaling is informative but context-specific. A compelling correction can help where the audience actually holds the misconception; it can also waste time or frustrate an audience that does not. A synchronized visual highlight may help direct attention when it points to the object being described; this does not imply every spoken phrase should trigger a new graphic, color change, or sound effect.

Keep facts and values coherent across narration, diagrams, source data, and labels. If they are generated from one mathematical or process model, that can reduce inconsistency. Otherwise document and verify the relevant source.