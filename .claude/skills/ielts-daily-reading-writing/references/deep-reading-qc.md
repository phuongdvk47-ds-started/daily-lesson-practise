# Deep Reading Quality Control & Generation Guidelines

This reference defines the strict rules for generating and evaluating the "Deep Reading Quality" of a reading lesson.
- **The Reading Agent** must use these rules during the generation phase to ensure the question distribution strictly matches the stated CEFR level's cognitive depth.
- **The Quality Control Agent** must use these rules to evaluate the pack and ensure it actually matches its stated CEFR level in terms of cognitive depth, not just in correct answers.

## 1. Reading Question Classifications

Both the Reading Agent (when creating) and the QC Agent (when evaluating) must classify every reading question into one of the following 8 categories:

- **Literal / keyword scanning**: Can be answered by scanning for keywords or finding exact/nearly exact wording in the passage.
- **Direct paraphrase**: Requires understanding a simple paraphrase, but the target information is isolated within one sentence or very close sentences.
- **Local comprehension**: Requires understanding the meaning of a full sentence or a cluster of sentences, not just matching words.
- **Light inference**: Requires drawing a simple, direct conclusion from explicitly stated facts.
- **Integration / synthesis**: Requires connecting information across multiple sentences or paragraphs.
- **Main idea / writer purpose**: Requires understanding the primary point, the purpose of a paragraph, or the writer's attitude/stance.
- **Discourse relationship**: Requires understanding logical connections (cause-effect, contrast, example-illustration, condition, concession, conclusion).
- **Evaluation / implication**: Requires understanding underlying implications, evaluating arguments, recognizing limitations of evidence, or detecting implicit attitudes. Primarily suitable for C1-C2.

## 2. Level Expectations & Distributions

The Reading Agent must generate questions, and the QC Agent must evaluate the pack, against the expected distribution for its stated level.
The Reading Agent must distribute questions according to these maximum/minimum ratios:

| Level | Literal | Inference / Reasoning | Function / Structure / Purpose | Vocab / Reference |
| ----- | ------: | --------------------: | -------------------: | ---------------: |
| A1    |   <=70% |                 >=10% |                >=10% |            >=10% |
| A1+   |   <=60% |                 >=15% |                >=10% |            >=15% |
| A2    |   <=50% |                 >=20% |                >=15% |            >=15% |
| A2+   |   <=45% |                 >=25% |                >=15% |            >=15% |
| B1    |   <=40% |                 >=30% |                >=15% |            >=15% |
| B1+   |   <=35% |                 >=35% |                >=15% |            >=15% |
| B2    |   <=30% |                 >=40% |                >=15% |            >=15% |
| B2+   |   <=25% |                 >=45% |                >=15% |            >=15% |
| C1    |   <=20% |                 >=45% |                >=20% |            >=15% |
| C1+   |   <=15% |                 >=50% |                >=20% |            >=15% |
| C2    |   <=10% |                 >=50% |                >=25% |            >=10% |

**Rule for `+` levels:** A level with a `+` (A1+, A2+, B1+, B2+, C1+) is a transitional level. It must show a measurable step up from its base level.

### A1 / A1+
- **Mandatory Types**: Matching basic info; Simple reference (this, it, they); Understanding simple purpose (notice, email, message).
- **Rule**: Max 80% direct copy.
- **High Issue**: 100% keyword copying. Requires inference above A1. Vocabulary/structures in questions are much harder than the passage.

### A2 / A2+
- **Mandatory Types**: At least 1 simple inference; At least 1 vocabulary-in-context; At least 1 reference question; At least 1 question connecting two adjacent sentences.
- **Rule**: Distractor must use near-synonyms or same topic, not obviously wrong.
- **High Issue**: Almost entirely verbatim matching. Gap-fill only targets vocabulary words. No comprehension beyond single isolated phrases.

### B1 / B1+
- **Mandatory Types**: At least 2 inference questions; At least 1 main idea/purpose question; At least 1 reference question; At least 1 vocabulary-in-context question; At least 1 attitude/reason/result/contrast/cause-effect question.
- **Rule**: No blocks of pure literal word finding.
- **High Issue**: Majority of questions are keyword scanning. MCQs have only one plausible option. Zero inference/main idea/relationship questions.

### B2 / B2+
- **Mandatory Types**: Inference from dispersed evidence; Author attitude/stance; Text structure/paragraph function; Implied contrast or assumption; Vocabulary meaning by context (not dictionary).
- **Rule**: Distractors must be plausible, using paraphrase or opposite logic.
- **High Issue**: >40% literal questions. Zero questions on writer purpose, paragraph function, inference, or synthesis.

### C1 / C1+
- **Mandatory Types**: Nuanced inference; Author implication; Rhetorical purpose; Tone/stance/hedging; Argument structure; Distinguish claim/evidence/limitation/concession.
- **Rule**: Questions must not be answerable by a single isolated evidence sentence.
- **High Issue**: Too many surface-level questions. Fails to test stance, implication, discourse function, or argument structure. Passage/questions are too easy for C1.

### C2
- **Mandatory Types**: Subtle implication; Assumption behind argument; Evaluation of reasoning; Irony/nuance/qualification; Multiple pieces of evidence synthesis.
- **Rule**: Distractors must be very close but wrong in logic, scope, degree, or implication.
- **High Issue**: Can be solved via keyword search. Fails to require argument/nuance processing. Answers/distractors are too simple for C2.

## 3. General Deep Reading QC Rules

- A correct answer does NOT guarantee a "PASS" for Deep Reading. If the cognitive depth is too shallow for the level, the pack's quality rating must be lowered.
- If an answer is factually wrong, lacks printed evidence, has multiple valid answers, or the question is unanswerable: This remains a **CRITICAL logic error** (FAIL).
- Do not penalize A1/A2 packs for lacking academic inference.
- You MUST penalize B2-C2 packs if they lack inference, synthesis, writer purpose, or discourse relationship questions.
- If all or nearly all questions rely on keyword scanning, raise a **High Issue**.
- If logic is correct but Deep Reading is weak, the status should be `NEEDS REVISION` or `CONDITIONAL PASS` depending on severity.
  - A1/A2: Max `CONDITIONAL PASS` if still useful for basic practice.
  - B1/B1+: `NEEDS REVISION` or `CONDITIONAL PASS`.
  - B2/B2+: `NEEDS REVISION` if inference/synthesis is clearly lacking.
  - C1/C1+/C2: `NEEDS REVISION` or `FAIL` if the pack completely misses the level's objective.

### Fail Conditions (PDF Checker / Daily IELTS Checker)
The pack MUST FAIL if any of the following are true:
- The level-specific distribution table above is violated.
- > 50% of questions are keyword-scan/literal at B1 or above.
- > 40% of questions are keyword-scan/literal at B2 or above.
- 0 inference questions at B1 or above.
- 0 main idea/purpose questions at B1 or above.
- 0 reference or vocabulary-in-context questions at B1 or above.
- 0 cause-effect, contrast, reason, result, or implication questions at B1 or above.
- 0 vocabulary-in-context questions at A2 or above.
- Distractors are obviously wrong (no plausible keyword traps).
- Answer explanation simply copies evidence without reasoning.
- TFNG relies solely on keywords without paraphrasing.
- Gap-fill only requires copying exact words from the passage without contextual grammar constraints.

## 4. Reading Logic Scoring Breakdown (20 points total)

When evaluating "Logic & Pedagogical Quality > Reading logic: 20", the 20 points must be explicitly divided into:
- **Answer correctness and evidence support**: 8 points
- **Question uniqueness and answerability**: 4 points
- **Deep Reading quality for stated level**: 6 points (Compare against the specific rubric for the stated level, do not use a universal standard).
- **Level-appropriate reading skill mix**: 2 points

## 5. Severity Guidelines for Deep Reading Issues

- **Critical**: Use ONLY for logic errors (wrong answer, missing passage evidence, multiple correct answers, unanswerable question, or causes negative learning). Do NOT use Critical for "weak depth" unless the weak depth makes the question unanswerable or factually wrong.
- **High**: Deep Reading is clearly below the stated level. The majority of B1+ questions are keyword scanning. B2/B2+ completely lacks inference/synthesis/writer purpose. C1+ lacks synthesis/evaluation. The pack functions at least one full level below its stated level (e.g., a B2+ pack that reads like B1/B1+).
- **Medium**: Some deep reading exists but the distribution falls short. A `+` level pack acts like its base level (e.g., B1+ acts like standard B1). MCQ distractors are too easy. TFNG struggles to differentiate False and Not Given cognitively.
- **Low**: Minor wording/distractor tweaks needed to improve depth. A few literal questions should be paraphrased more strongly, but the pack is generally at the correct level.

## 6. Output Format: ielts-daily-reading-writing

When generating a review report for the Reading section, you must strictly follow the current output format of `ielts-daily-reading-writing` (maintaining the existing structure while adding Deep Reading insights):

### Executive Summary
[High-level summary of the pack's overall quality and readiness]

### Score Breakdown
[Include the breakdown of the 20-point Reading logic score as defined above]

### 3.1 Reading Logic
[Standard logic checks...]

#### Deep Reading distribution
- Literal / keyword scanning: x/y
- Direct paraphrase: x/y
- Local comprehension: x/y
- Light inference: x/y
- Integration / synthesis: x/y
- Main idea / writer purpose: x/y
- Discourse relationship: x/y
- Evaluation / implication: x/y

#### Level expectation
- **Stated level**: [Level]
- **Expected Deep Reading profile**: [Brief summary of expected distribution]
- **Actual profile**: [Brief summary of actual distribution]
- **Verdict**: [Meets / Partially meets / Does not meet]

#### Examples
- **Questions that are too literal**: [List IDs/Brief descriptions]
- **Questions that show good Deep Reading**: [List IDs/Brief descriptions]
- **Questions to revise first**: [List IDs/Brief descriptions]

*Note: The agent must explicitly state if the actual difficulty aligns more closely with a different level than the stated level.*

### Critical / High / Medium / Low Issues
[List categorized issues]

### Final Recommendation
The Final Recommendation MUST answer the following questions clearly:
- Does the Reading section achieve Deep Reading appropriate for its level?
- Does the Reading section truly match the level stated on the pack?
- If not, what level does it actually resemble?
- Is it ready to be distributed to students?
- If usable, should it be used as `official`, `internal`, or `teacher-reviewed`?
- If it is not ready, which types of questions must be revised first?
- Based on the current level, which specific reading skills need to be increased or decreased?
- (For `+` levels) Does the pack successfully demonstrate a "transition upward" compared to its base level?
