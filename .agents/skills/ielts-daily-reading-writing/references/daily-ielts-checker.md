# PDF Checker / Daily IELTS Checker

The Quality Control Agent will run these checks on the final output to ensure it meets the Deep Reading and Deep Grammar standards before publishing.

## 1. Reading Logic Score (0-100)

The QC Agent calculates a Reading Logic Score out of 100 based on the following rubric:

* **Answer correctness and evidence support (0-40 points)**: Are the answers factually correct according to the printed passage? Is there unambiguous verbatim evidence?
* **Deep Reading Blueprint Alignment (0-30 points)**: Does the generated reading set match the mandatory types and cognitive depth ratios specified in the blueprint for the target CEFR level?
* **Question Uniqueness and Answerability (0-20 points)**: Are questions independent? Are they answerable from the text without outside knowledge? Are distractors plausible?
* **Level-appropriate reading skill mix (0-10 points)**: Is the vocabulary and syntax of the questions appropriate for the target level?

### Reading Fail Conditions
The reading section immediately scores 0 and FAILS if:
- > 60% of questions have evidence verbatim in a single sentence.
- 0 inference questions at B1 or above.
- 0 vocabulary-in-context questions at A2 or above.
- 0 main idea/purpose questions at B1 or above.
- Distractors are obviously wrong (no plausible keyword traps).
- Answer explanation simply copies evidence without reasoning.
- TFNG relies solely on keywords without paraphrasing.
- Gap-fill only requires copying exact words from the passage without contextual grammar constraints.

## 2. Grammar Logic Score (0-100)

The QC Agent calculates a Grammar Logic Score out of 100 based on the following rubric:

* **Grammatical Correctness (0-40 points)**: Is the target structure used correctly? Is the answer the only valid answer?
* **Deep Grammar Blueprint Alignment (0-30 points)**: Does the generated grammar set match the Form/Meaning/Context/Transformation ratios specified in the blueprint for the target CEFR level?
* **Anti-Repetition and Distractor Quality (0-20 points)**: Are there varying grammatical patterns? Are distractors realistic learner errors (traps)?
* **Meaning Preservation and Context (0-10 points)**: Do transformation questions preserve meaning? Do gap-fills provide sufficient context?

### Grammar Fail Conditions
The grammar section immediately scores 0 and FAILS if:
- > 5 consecutive questions with the same target grammar and clue type.
- > 40% of questions use obvious surface clues at B1 or above.
- 0 error correction or transformation questions at B1 or above.
- 0 paragraph/context grammar questions at B2 or above.
- Explanations only state the formula without explaining meaning/use.
- A question lacks a reasonable/plausible distractor.
- The grammar target is drastically lower than the current level.

## 3. Final Status Rule

Based on the combined scores and fail conditions, the QC Agent must assign a Final Status to the lesson pack:

* **PASS**: Reading and Grammar scores both $\ge$ 85, and NO Fail Conditions triggered. The pack is ready for students.
* **PASS WITH MINOR FIXES**: Scores between 75-84. Minor issues like a slightly weak distractor or formatting issue, but pedagogically sound.
* **NEEDS REVISION**: Any score < 75. The pack is fundamentally flawed and must be regenerated.
* **FAIL**: Any Fail Condition triggered. The pack cannot be used and must be regenerated.
