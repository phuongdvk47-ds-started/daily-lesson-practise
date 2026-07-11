# Regeneration Quality Gates

Use these gates in the Reading Agent, Grammar Agent, Answer Agent, Quality Control Agent, and orchestrator challenge loop. A failed gate requires regenerating only the affected section or item unless source, level, topic, or user instruction changes.

## Reading Regeneration Gates

Regenerate Reading if:
- More than 50% of questions are keyword-scan/literal at B1 or above.
- More than 40% of questions are keyword-scan/literal at B2 or above.
- The Reading set violates the level ratio table in `deep-reading-generation-rules.md`.
- No inference question exists at B1 or above.
- No main idea or author purpose question exists at B1 or above.
- No reference or vocabulary-in-context question exists at B1 or above.
- No cause-effect, contrast, reason, result, or implication item exists at B1 or above.
- B2+ lacks paragraph function, author stance/attitude, or multi-evidence inference when the question count allows it.
- C1/C2 lacks nuance, implication, rhetorical purpose, assumption, or claim/evidence/limitation/concession analysis when the source supports it.
- Gap-fill only asks students to copy exact words from the passage.
- MCQ distractors are obviously wrong or not passage-plausible.
- TFNG lacks paraphrase or reasoning.
- A question relies on outside knowledge or omitted source information.
- A question has multiple valid answers.


## Grammar Regeneration Gates

Regenerate Grammar if:
- More than 5 consecutive questions share the same grammar target and clue type.
- More than 40% of questions at B1 or above rely on obvious surface clues.
- More than 30% of questions at B2 or above rely on obvious surface clues.
- The Grammar set violates the level ratio table in `deep-grammar-generation-rules.md`.
- B1+ lacks error correction or transformation.
- B1+ lacks writing-transfer grammar.
- B2+ lacks paragraph/context grammar.
- Explanations only state formulas and do not explain meaning/use.
- A Correct-the-error item has no real error, has more than one target error when the prompt says singular, or has a correction identical to the original.
- A transformation changes the meaning of the source sentence.
- Multiple reasonable answers exist but the answer key accepts only one.

## Answer Key Regeneration Gates

Regenerate Answers if:
- Reading answers lack evidence, reasoning, distractor analysis, or depth checks.
- Reading reasoning does not connect the evidence to the answer.
- Grammar answers lack form, meaning, use in context, trap logic, or depth checks.
- Grammar explanations do not prove uniqueness or meaning preservation.


## Challenge Severity

- Use `critical` for wrong answers, missing printed evidence, multiple valid answers, unanswerable questions, missing real error in error correction, answer identical to prompt, or meaning-changing transformation.
- Use `high` for sections below the stated level, excessive keyword scanning, excessive surface-clue grammar, weak distractors, missing mandatory B1+ or B2+ question types, or answer explanations that cannot teach the reasoning path.
- Use `medium` for partial ratio imbalance, weak but usable distractors, or a `+` level that behaves like its base level.
