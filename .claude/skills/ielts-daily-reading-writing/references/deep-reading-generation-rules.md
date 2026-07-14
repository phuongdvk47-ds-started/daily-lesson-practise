# Deep Reading Generation Rules

Use this reference with `.claude/agents/ielts-reading.md` and `deep-question-blueprint.md` before generating the reading blueprint, passage questions, and reading answer metadata.

## Ratio Rules by Level

Treat the Literal column as a maximum and the other columns as minimums. For small question counts, convert percentages to sensible minimum counts while preserving at least a few non-literal items.

| Level | Literal | Inference / Reasoning | Function / Structure / Purpose | Vocab / Reference |
|---|---:|---:|---:|---:|
| A1 | <=70% | >=10% | >=10% | >=10% |
| A1+ | <=60% | >=15% | >=10% | >=15% |
| A2 | <=50% | >=20% | >=15% | >=15% |
| A2+ | <=45% | >=25% | >=15% | >=15% |
| B1 | <=40% | >=30% | >=15% | >=15% |
| B1+ | <=35% | >=35% | >=15% | >=15% |
| B2 | <=30% | >=40% | >=15% | >=15% |
| B2+ | <=25% | >=45% | >=15% | >=15% |
| C1 | <=20% | >=45% | >=20% | >=15% |
| C1+ | <=15% | >=50% | >=20% | >=15% |
| C2 | <=10% | >=50% | >=25% | >=10% |

## Mandatory Types

For B1 and above, every Reading set must include:
- at least 1 inference item
- at least 1 main idea or author purpose item
- at least 1 reference or vocabulary-in-context item
- at least 1 cause-effect, contrast, reason, result, or implication item

For B2 and above, also include:
- paragraph function
- author stance or attitude
- inference from multiple pieces of evidence

For C1/C2, also include:
- nuance or implication
- rhetorical purpose
- assumption behind an argument
- claim/evidence/limitation/concession distinction

## Question Design Rules

- Do not let Reading become information retrieval only.
- Gap-fill must require contextual understanding, grammar fit, paraphrase, or reference resolution; it must not only copy an exact word from the passage.
- TFNG must require paraphrase and reasoning, especially for `False` vs `Not Given`.
- MCQ stems should usually paraphrase the passage. Do not copy passage keywords into the stem unless the blueprint marks the item as low-depth literal.
- Every non-literal item must include `paraphrase_mapping` and a `keyword_overlap_check`.
- Every question must be answerable only from the printed passage, with verbatim evidence in the printed passage.
- For inference questions, identify the two or more pieces of evidence the learner must connect.

## Distractor Rules

Use plausible distractors. Do not create options that are nonsense, outside the passage topic, or obviously false.

Allowed distractor strategies:
1. True detail but wrong reason.
2. True detail but wrong scope.
3. Similar keyword but opposite meaning.
4. Plausible paraphrase but unsupported by passage.
5. Partially correct but incomplete.
6. Correct idea but wrong paragraph/person/time.
7. Too broad or too narrow.

At least 30% of incorrect MCQ options should be keyword traps: they reuse or paraphrase passage wording but fail in logic, scope, time, reason, or implication.

## Level-Specific Guidance

### A1 / A1+
- Keep language simple, but do not make all questions direct copying.
- Include simple reference or simple purpose.
- Include a question about what a notice, email, message, or schedule is used for.

### A2 / A2+
- Include simple inference.
- Include vocabulary-in-context and simple reference.
- Include at least one question connecting two nearby sentences.

### B1 / B1+
- Require inference, main idea/purpose, reference or vocabulary-in-context, and cause-effect/contrast/reason/result/implication.
- Avoid gap-fill sets that can be solved by copying exact words only.

### B2 / B2+
- Use dispersed evidence, author attitude/stance, text structure, paragraph function, implied contrast/assumption, vocabulary by context, and plausible distractors.

### C1 / C1+
- Require nuanced inference, author implication, rhetorical purpose, tone/stance/hedging, argument structure, and claim/evidence/limitation/concession distinctions.

### C2
- Test subtle implication, assumptions behind arguments, reasoning quality, irony/nuance/qualification/rhetorical positioning when appropriate, and multiple-evidence synthesis.
- Distractors should be close to correct but wrong in logic, scope, degree, or implication.
