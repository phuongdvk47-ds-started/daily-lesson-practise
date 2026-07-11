# Agent Review Loop

## Role
The Agent Review Loop allows Sub-Agents to critique and improve one another's outputs before final export.
This is not a simple sequential pipeline. Each major section must be reviewed by at least one downstream agent and by the QC Agent.

## 1. Review Philosophy
Each Sub-Agent should act as a specialist.
- Source Research Agent protects factuality and source reliability.
- Reading Agent creates passage and questions.
- Vocabulary Agent checks lexical usefulness and vocabulary coverage.
- Grammar Agent checks grammar suitability and ambiguity.
- Writing Agent checks transferability to writing.
- Answer Agent checks explainability.
- QC Agent challenges all sections as an examiner and senior teacher.

## 2. Required Review Interactions

### Source → Reading
Before Reading Agent generates questions:
- Reading Agent must check whether the source is usable for the requested level.
- If the source is too hard, Reading Agent may request a simplified source-based passage while preserving factual grounding.
- If the source is unsuitable, Reading Agent must reject it and ask Source Research Agent for another source.

### Reading → Vocabulary
Vocabulary Agent must review the Reading passage and check:
- Are there enough useful vocabulary items?
- Are there enough phrases/chunks/collocations?
- Are recycled words integrated naturally?
- Are vocabulary items useful for Writing?
If not, Vocabulary Agent may request Reading Agent to:
- naturally include missing recycled vocabulary
- include more topic vocabulary
- simplify wording for level
- reduce overly advanced vocabulary

### Reading → Grammar
Grammar Agent must review the Reading passage and questions for:
- grammar level suitability
- possible structures to teach
- sentence complexity
- grammar-to-writing transfer opportunities
Grammar Agent may request Reading Agent to adjust passage complexity if:
- the passage is too hard for the level
- sentence structures do not support selected grammar targets
- examples are not suitable for grammar practice

### Reading → Answer (Printed Passage Verification)
Answer Agent must review Reading questions and check:
- **CRITICAL**: Can every reading question be answered *only* using information printed in the passage?
- **CRITICAL**: Does every reading question correct answer map directly to an `evidence_quote` present *verbatim* in the passage text?
- Does the question match its `reading_blueprint` item?
- Does B1+ Reading include required inference, purpose/main idea, reference/vocabulary-in-context, and logic relationship items?
- Are distractors explainable?
- Is there exactly one correct answer?
- Does the answer explanation require real reasoning, not only evidence copying?
If any question relies on omitted source facts or general knowledge, lacks verbatim passage evidence, misses required blueprint depth, or has weak distractor logic, the Answer Agent **must raise a challenge** to the Reading Agent.

### Vocabulary → Writing
Writing Agent must review vocabulary output and check:
- Are there useful chunks for Writing?
- Are collocations usable in student responses?
- Are idioms appropriate for the level and register?
- Are academic vocabulary items suitable for Task 1/Task 2?
If not, Writing Agent may request Vocabulary Agent to revise the vocabulary mix.

### Grammar → Writing
Writing Agent must review grammar targets and check:
- Can the grammar targets be practiced in Writing tasks?
- Are writing tasks designed to use the selected grammar?
- Are target structures level-appropriate?
If not, Writing Agent must request Grammar Agent to adjust targets or provide better transfer structures.

### Writing → Answer (Topic Relevance & Self-Check)
Writing Agent must self-check and verify topic alignment before returning tasks.
Answer Agent must review Writing tasks and check:
- **CRITICAL**: Is each task clearly connected to the daily lesson topic, even at lower levels?
- Can a model answer be produced at the requested level?
- Is target length clear?
- Are success criteria clear?
- Is visual data sufficient when numbers are used?
If not, Answer Agent must request Writing Agent revision.

### PDF Compiler → Grammar Agent / Orchestrator
Before compiling the final PDF, the PDF Compiler must run structural checks:
- Verify that no grammar section heading contains hardcoded display ranges.
- Ensure that question ranges inside the PDF are computed dynamically from actual counts.
- Ensure that all subjective grammar tasks (without options and without inline blanks) have been allocated dotted lines (`.writing-line`) for writing space.
If these rules are violated, the PDF export must fail.

### QC → All Agents
QC Agent must challenge all outputs.
QC Agent must not pass weak content just because counts match.

## 3. Challenge Types
Use challenge types and severity levels defined in `output-schema.md §challenge_type Enum`.

Required fields per challenge:
`challenge_type` · `severity` (`low`|`medium`|`high`|`critical`) · `challenged_agent` · `location` · `problem` · `required_fix` · `regenerate_scope` (`single_question`|`section`|`full_agent_output`)

## 4. Revision Protocol
When a challenge is raised:
1. Orchestrator routes the challenge to the responsible agent.
2. The responsible agent revises only the affected section.
3. The revised section is merged back into `lesson_source.json`.
4. QC reruns only relevant checks first.
5. If relevant checks pass, run full QC.
6. Export PDF only if full QC passes.

## 5. Maximum Revision Attempts
Default maximum attempts:
- Source: 2 attempts
- Reading: 3 attempts
- Vocabulary: 2 attempts
- Grammar: 3 attempts
- Writing: 2 attempts
- Answers: 2 attempts
- PDF layout: 2 attempts

If maximum attempts are exceeded:
- Stop.
- Return unresolved challenges.
- Ask for human direction.

## 6. Challenge Log
Record all challenges in `lesson_source.json` under `agent_review.challenges` (see `output-schema.md §Challenge Object`).
Required fields: `id` · `from_agent` · `to_agent` · `challenge_type` · `severity` · `location` · `problem` · `required_fix` · `status` · `revision_attempt`

## 7. Review Output Format
Every reviewing agent must return a JSON object with keys:
`review_status` (`pass`|`challenge`) · `reviewer_agent` (str) · `reviewed_section` (str) · `strengths` (str[]) · `challenges` (str[]) · `recommended_revision_scope` (str)

## 8. Pass Criteria
A section can pass review only if:
- It satisfies pedagogical constraints.
- It matches the requested level.
- It is useful for the learner.
- It supports the full daily pack.
- It does not create downstream problems for Answers or PDF.

# Grammar Cross-Review Requirements

## Answer Agent Must Challenge Grammar Agent
Before finalizing grammar answers, Answer Agent must verify:
- the selected answer is the only valid answer
- each distractor is clearly wrong
- the explanation can prove why all other options are wrong
- the explanation covers form, meaning, use in context, and trap logic
- the item matches its `grammar_blueprint`
- no hidden context is required
- punctuation is complete in the final reconstructed sentence

If Answer Agent cannot prove uniqueness, context use, meaning preservation, or blueprint alignment, it must challenge Grammar Agent.

## PDF QC Must Challenge Logic-Related Rendering
Post-render PDF QC must detect whether punctuation or blanks were lost in PDF rendering in a way that creates ambiguity.

For example:
- if the JSON question has `_______` but the PDF loses the blank
- if comma punctuation disappears
- if options are truncated
- if a non-defining relative clause loses its closing comma

# Answer Agent Must Challenge Error-Correction Items
Before finalizing grammar answers, Answer Agent must verify every Correct-the-error item:
- Does the original sentence actually contain the target error?
- Is the corrected sentence different from the original?
- Does the explanation describe the actual error?
- Is there exactly one error?
- Is the correction pedagogically useful for the target level?

If not, Answer Agent must challenge Grammar Agent.

Example challenge:
```json
{
  "from_agent": "answers",
  "to_agent": "grammar",
  "challenge_type": "missing_error_in_error_correction",
  "severity": "critical",
  "location": "grammar.questions[26]",
  "problem": "The item asks students to correct an error, but the original sentence is already correct.",
  "required_fix": "Rewrite the prompt so the original sentence contains exactly one target error."
}
```
