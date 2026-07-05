# Deep Answer Key Rules

Use this reference with `answer-agent.md` whenever generating Reading or Grammar answer explanations.

## Reading Answer Format

Each Reading answer must include these fields in JSON and equivalent rendered content:

```markdown
Question X
Answer:
Question type:
Evidence:
Reasoning:
Why other options are wrong:
Depth check:
```

Rules:
- `Evidence` must identify the passage sentence or idea supporting the answer and include the paragraph number.
- `Reasoning` must explain the logic, not merely paraphrase or copy the evidence.
- `Why other options are wrong` must address each distractor separately.
- `Depth check` must label the item as `literal`, `inference`, `reference`, `main idea`, `purpose`, `function`, `vocabulary-in-context`, or `synthesis`.
- For inference questions, reasoning must state which pieces of evidence the learner must connect.
- If the answer can be justified only with outside knowledge, challenge the Reading Agent.

## Grammar Answer Format

Each Grammar answer must include these fields in JSON and equivalent rendered content:

```markdown
Question X
Answer:
Grammar target:
Form:
Meaning:
Use in context:
Trap / distractor logic:
Why other options are wrong:
Depth check:
```

Rules:
- `Form` must state the structure accurately.
- `Meaning` must explain what the form means in that sentence.
- `Use in context` must explain why the surrounding context requires it.
- `Trap / distractor logic` must name the surface clue, learner error, register issue, punctuation issue, or meaning shift.
- `Why other options are wrong` must be explicit for MCQ/gap-fill distractors.
- `Depth check` must explain why the item is not only mechanical form recall.

## Answer Agent Challenge Duties

Before finalizing answers, the Answer Agent must challenge the source agent if:
- a Reading explanation only repeats evidence without explaining logic
- a Reading item has more than one valid answer
- a distractor analysis does not explain why each option is wrong
- a Grammar explanation only states a formula and omits meaning/use
- a Grammar item has an identical correction, missing error, hidden assumption, or multiple valid answers
- a transformation changes meaning, certainty, quantity, subject, cause, contrast, or time
