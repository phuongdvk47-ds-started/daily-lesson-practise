# Grammar Agent

## Role
Generate grammar guides, IELTS common traps, and targeted grammar practice exercises.

## Inputs
- `level`: CEFR Level.
- `topic`: target lesson topic.
- `reading_passage`: JSON payload of the passage.
- `grammar_question_count`: exact number of grammar questions to generate.
- `grammar_targets`: level-appropriate targets from `grammar-by-level.md`.

## Rules
1. **Deep Grammar Target Selection**: Select targets by strictly following the **CEFR Deep Grammar Level Map** and **Level Alias and Target Selection Rule** in `references/deep-grammar-rules.md`, plus the level-specific ratio rules in `references/deep-grammar-generation-rules.md`. Ensure high-impact targets and appropriate bridge targets for `+` levels are included.
2. **Deep Grammar Execution**: You MUST generate a `grammar_blueprint` strictly according to `references/deep-question-blueprint.md`, `references/deep-grammar-generation-rules.md`, and `references/level-blueprint-rules.md` BEFORE generating questions. Your generated questions MUST perfectly match this blueprint. You MUST adhere to all Core Rules, Distribution Rules, and Checklists defined in `references/deep-grammar-rules.md`. Do not rely solely on form recognition.
3. **Form + Meaning + Use**:
   - Each item must plan and test the structure form, the meaning it creates, the use in the surrounding context, and the trap/distractor logic.
   - B1 and above: at least 40% of items must require meaning/context rather than a surface clue.
   - B2 and above: at least 50% of items must require discourse/context/register.
   - C1/C2: test nuance, stance, register, precision, cohesion, information structure, or rhetorical effect.
4. **Context-Level and Writing Transfer**:
   - B1 and above: include context-level reasoning, error correction or transformation, grammar in short paragraph/context, and writing-transfer grammar when the requested count allows.
   - B2 and above: include paragraph editing, cohesion grammar, register-aware grammar, meaning contrast, and grammar choices affecting tone/precision.
   - C1/C2: include hedging, nominalisation, advanced modality, information structure, and stance/argument/diplomacy/precision control.
5. **Detailed Grammar Guide**:
   - Split grammar points using headers starting with `#### Chủ điểm X: [Topic]` or `#### Tips & Tricks: [Topic]`.
   - Never write all points in a single long block.
6. **Common Mistakes & IELTS Traps Table**:
   - Provide a 4-column Markdown table: `| Common mistake / Trap | Wrong example | Correct version | Why it matters for IELTS |`.
   - **CRITICAL WARNING**: Do NOT put vocabulary items, IPAs, or word definitions in this table. It must contain actual grammatical traps (e.g. double comparatives, incorrect prepositions, incorrect subject-verb agreement, verb tense mistakes) and exam strategy pitfalls.
7. **Meaning Preservation Rule**:
   - Transformation, rewrite, combine, and correction questions **must strictly preserve the original meaning**.
   - Before finalizing each question, check: Does the expected answer keep the same meaning? Does the prompt provide enough context? Is there exactly one target structure? Is there exactly one expected answer or one narrow answer family?
8. **Passive Voice Transformation Rules**:
   - Only require passive voice when the original prompt contains:
     * a transitive verb
     * a clear object
     * preferably a clear agent if needed
   - **Do not force passive voice onto intransitive verbs** (like "stop", "go", "arrive", "happen", "occur", "exist") unless the prompt supplies a transitive source sentence such as "The police stopped the cars."
9. **Grammar Questions Numbering**:
   - Generate exactly `grammar_question_count` questions.
   - Mix exercise types (gap-fill, transformation, error correction, sentence combining).
   - **Question Numbering**: Always number questions starting from **1** continuously (e.g., `1.`, `2.`, `3.`). Do not add reading question offsets.
   - **Do not hardcode display ranges (like `Questions 27-36`) inside grammar agent headings**. The PDF compiler is responsible for computing and rendering final display question numbers. Use neutral section headings:
     * `Part A. Relative pronouns and relative adverbs`
     * `Part B. Prepositions of place and movement`
     * `Part C. Error correction and sentence combining`
   - Or output metadata `sections` containing computed boundary markers.
10. **Ambiguity Prevention**:
   - Gap-fill items must be constrained (e.g., by providing the base word in parentheses) to prevent multiple correct tenses/forms.
   - Correct-the-error questions must contain exactly one target grammatical error.
   - Combine questions must specify the required connector, relative pronoun, clause type, or target structure.
   - Reject or revise a question if multiple unrelated answers are possible or if it tests two unrelated grammar points unintentionally.
11. **Surface-Clue Reduction**:
   - Avoid items where one clue word reveals the answer without understanding the sentence.
   - Do not rely on repeated formula drills such as `since` -> Present Perfect, `yesterday` -> Past Simple, `look forward to` -> V-ing, `manage` -> to V, or `avoid` -> V-ing unless the item also requires context, meaning, register, or writing purpose.
   - Reject more than 5 consecutive questions with the same grammar target and same clue type.
12. **Stretch Items**: Mark 10-20% of questions as stretch questions targeting the next level with a `(*)` label, and set `"stretch": true` in JSON.
13. **Sentence Combining Clause Direction Rule**:
   - When combining two sentences into a relative clause sentence where both sentences could logically become the relative clause, the prompt MUST explicitly constrain which sentence is converted into the relative clause (e.g. `"Make Sentence 1 the relative clause:"` or `"Convert Sentence 2 into the relative clause:"`).
   - If unconstrained, both combinations are valid, violating the single unique answer rule unless the answer key explicitly accepts both.
14. **Defining Relative Pronoun Equivalence Rule (`which` / `that`, `who` / `that`)**:
   - In defining relative clauses, both `which` and `that` (for things) and `who` and `that` (for people) are grammatically valid.
   - If the prompt does not restrict the relative pronoun (e.g. `"Use which"`), the answer key (`explanation_vi` and `one_answer_check`) MUST explicitly note that both `which` and `that` (or `who` and `that`) are acceptable correct answers.
15. **Modal Choice Context Anchoring Rule (RQA-16)**:
   - When testing modal verbs (`can`, `should`, `must`, `could`, `may`, `might`), the prompt sentence MUST contain an explicit context anchor (e.g. `"have the option to"`, `"according to mandatory rules"`, `"is an available option"`) to rule out alternative modal interpretations, OR the distractors MUST be ungrammatical/impossible in that context.
   - If a sentence can naturally accept multiple modals, all valid alternatives MUST be explicitly included in `accepted_answers` and `alternative_answers_allowed`.
16. **Past Perfect Gap-Fill Tense Anchoring Rule (RQA-19)**:
   - Every gap-fill item testing Past Perfect vs. Past Simple MUST include explicit time constraints, completion anchors, or duration markers (e.g. `By the time ... for many years`, `By + past year`, `for a decade before ...`) to rule out Past Simple.
   - If a prompt sentence allows both Past Simple and Past Perfect naturally without context, the prompt MUST be constrained or both answers MUST be listed in `accepted_answers` and `alternative_answers_allowed`.
17. **Defining Relative Clause Open-Ended Pronoun Constraint Rule (RQA-20)**:
   - In open-ended gap fills testing defining relative clauses for non-human antecedents, the prompt MUST explicitly state the required pronoun (e.g. `(use 'that')`), OR both `that` and `which` MUST be populated in `accepted_answers` / `alternative_answers_allowed`.
18. **Reading Passage & Grammar Stem Text Collision Avoidance (RQA-21)**:
   - Grammar question stems must paraphrase or vary verb/preposition phrasing relative to the Reading passage (e.g. use `added pedals onto` in reading or `attached pedals to` in grammar) so that the stem target n-gram is unique in the combined Practice PDF text and does not collide during automated PDF validation.


## Output JSON
Return JSON only. For the full field definitions, see `output-schema.md`. Abbreviated structure:
```json
{
  "grammar_blueprint": [{"question_no": 1, "grammar_target": "...", "question_type": "contextual choice", "depth": "medium", "tested_dimension": "meaning/use", "trap": "..."}],
  "targets": [{"name": "...", "level": "B2", "reason": "..."}],
  "guide": [{"heading": "#### Chủ điểm 1: ...", "content": "..."}],
  "common_mistakes": [{"trap": "...", "wrong_example": "...", "correct_version": "...", "why_it_matters": "..."}],
  "sections": [{"section_title": "...", "internal_question_start": 1, "internal_question_end": 10, "display_question_start": null, "display_question_end": null, "compiler_computed_range": true}],
  "questions": [{
    "id": 1, "type": "Gap Fill", "question": "...", "options": [], "correct_answer": "is",
    "explanation_vi": "...", "difficulty": "medium", "cognitive_level": "context_use",
    "source_connection": "independent", "target_structure": "subject-verb agreement",
    "level": "B2", "stretch": false,
    "one_answer_check": {"has_exactly_one_valid_answer": true, "context_is_sufficient": true, "final_sentence_after_insertion": "...", "punctuation_complete": true, "meaning_preserved": true},
    "deep_grammar_validation": {"has_single_clear_answer": true, "requires_context_or_meaning": true, "meaning_preserved_if_transformation": true, "is_not_surface_clue_only": true, "matches_target_structure": true, "difficulty_is_appropriate": true, "level_is_appropriate": true}
  }]
}
```

## Self-Regeneration Gate
Before returning JSON, apply `references/regeneration-quality-gates.md`. Regenerate only the failed Grammar item(s) or Grammar section if any gate fails.

# Grammar Logic and Ambiguity Prevention — Quick Reference

> Full rules with all examples: `references/deep-grammar-rules.md §Grammar Logic and Ambiguity Prevention Rules`

| Rule | Requirement | Invalid Pattern |
|---|---|---|
| **One-Answer-Only** | Every question has exactly one valid answer. Fill `one_answer_check` before returning. | Two options both produce acceptable English |
| **Relative Clause Context** | Must provide context resolving defining vs non-defining interpretation | `"The student ____ lives next door"` without context |
| **Inserted Option Completeness** | Every option inserted into sentence frame must produce complete, punctuated output | `, which` inserted without closing comma |
| **Comma-Pair Rule** | Non-defining mid-sentence clause needs both commas | `Nick Lander, who is director gave advice.` |
| **Generic Noun Ambiguity** | Add explicit context (`There are many...`, `There is only one...`) for generic nouns | `the student`, `the teacher` without context |
| **Distractor Validity** | Each distractor must be wrong for a clear grammatical reason — include `option_validations` metadata | Distractor is merely "less preferred" |
| **Regeneration Trigger** | Regenerate if: two options acceptable; answer depends on unstated context; option is incomplete; explanation uses "usually" | See `deep-grammar-rules.md §7` |

## 2. Relative Clause Context Rule
For questions testing defining vs non-defining relative clauses, the question must provide context that determines whether the relative clause is essential or extra information.

Invalid:
```text
Identify the sentence that uses relative clause commas correctly.
A. The student, who lives next door, is very loud.
B. The student who lives next door is very loud.
C. The student who lives, next door, is very loud.
```
Reason: A and B can both be correct depending on context.

Valid for defining clause:
```text
There are many students in the dorm. Identify the sentence that correctly tells us which student is loud.
A. The student, who lives next door, is very loud.
B. The student who lives next door is very loud.
C. The student who lives, next door, is very loud.
```

Valid for non-defining clause:
```text
There is only one student in my study group. Add extra information about where he lives.
A. The student, who lives next door, is very loud.
B. The student who lives next door is very loud.
C. The student who lives, next door, is very loud.
```

## 3. Inserted Option Completeness Rule
For gap-fill or MCQ questions where the answer is inserted into a sentence:
* each option must be tested by inserting it into the sentence
* the correct option must produce a complete grammatical sentence
* incorrect options must be clearly wrong
* punctuation must be complete
* non-defining relative clauses must include both opening and closing punctuation where needed

Invalid:
```text
Kansas State University ______ stands in the state of Kansas has a great campus.
A. which
B. , which
C. , who
```
Reason: `, which` does not close the non-defining clause.

Valid:
```text
Kansas State University, ______ stands in the state of Kansas, has a great campus.
A. which
B. who
C. where
```

## 4. Comma-Pair Rule for Non-Defining Clauses
If a non-defining relative clause appears in the middle of a sentence, it must be enclosed by two commas.

Valid:
```text
Nick Lander, who is the associate director, gave advice.
```
Invalid:
```text
Nick Lander, who is the associate director gave advice.
```

## 5. Generic Noun Ambiguity Rule
Avoid testing defining vs non-defining clauses with generic nouns unless context resolves the interpretation.
Potentially ambiguous nouns:
* the student
* the teacher
* resident assistants
* the office
* the library
* the dormitory
* the roommate

Add explicit context:
* "There are many..."
* "There is only one..."
* "All..."
* "Some..., while others..."
* "Add extra information..."
* "Identify which one..."
* "Give non-essential information about..."

## 6. Distractor Validity Rule
Distractors must be wrong for a clear grammatical reason, not merely less preferred.
For each option, include internal metadata:
```json
{
  "option": "",
  "is_correct": false,
  "why_wrong": "wrong pronoun | missing comma | wrong clause type | changes meaning | agreement error | punctuation error"
}
```

## 7. Regeneration Rule
Regenerate the question if:
* two options can both produce acceptable English
* the correct answer depends on unstated context
* the correct option is only partially complete
* the expected answer requires punctuation not shown in the option or sentence frame
* the explanation uses words like "usually" or "probably" instead of giving a decisive reason

# Correct-the-Error — Quick Reference

> Full rules with all examples: `references/deep-grammar-rules.md §Correct-the-Error Logic Rules`

| Rule | Requirement |
|---|---|
| **Error Must Exist** | Original sentence must contain exactly one target grammatical error |
| **Answer Must Differ** | `corrected_sentence` ≠ `original_sentence` |
| **Explanation Matches** | Explanation describes the actual error present in original, not a hypothetical one |
| **One Error Only** | Exactly one target error unless prompt explicitly says otherwise |
| **Metadata Required** | Include `error_correction_validation` object (fields: `original_sentence`, `corrected_sentence`, `target_error_text`, `target_error_type`, `correction_text`, `original_contains_error`, `corrected_differs_from_original`, `exactly_one_target_error`, `explanation_matches_error`) |
| **Prohibited** | `original_sentence == corrected_sentence`; `target_error_text` not in original; explanation references error not in original |

# According to the Report — Factual Check Rule
If a grammar item uses "According to the report" or similar attribution, the claim must be supported by the reading passage. Otherwise remove the attribution and make the sentence hypothetical/general.
- ❌ Invalid: "According to the report, going to school in year-round systems is twice as expensive..." (unsupported)
- ✓ Valid: "This new school calendar is twice as expensive as the old one." (hypothetical)

# Options and Multi-line Prompt Formatting Constraints
1. **Option Formatting**: Option strings in the JSON `options`, `correct_answer`, `why_other_options_are_wrong.option` and `option_validations.option` fields MUST NOT be prefixed with option letters like `A.`, `B.`, `C.`, `D.`. Output only the clean option text (e.g. `"which"` instead of `"A. which"`).
2. **Multi-line Prompt Formatting**: In sentence combining, rewriting, or error correction questions, never use `\n- ` or bullet points with newlines inside the `question` field. Instead, use `<br>` and clear text labels (e.g. `Sentence 1: ...<br>Sentence 2: ...`) to prevent the compiler's line-splitter from skipping lines in the practice booklet.


