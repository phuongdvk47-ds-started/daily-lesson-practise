# Deep Question Blueprint

Use this reference before generating Reading or Grammar questions. The blueprint is mandatory internal planning and must be present in `lesson_source.json` before the generated questions.

## Reading Blueprint

Each Reading blueprint item must contain:

```json
{
  "question_no": 1,
  "type": "literal | inference | reference | main_idea | author_purpose | structure_function | vocabulary_in_context | synthesis",
  "depth": "low | medium | high",
  "target_skill": "string",
  "evidence_strategy": "single sentence | multiple sentences | paragraph-level | cross-paragraph",
  "distractor_strategy": "string"
}
```

Generation rules:
- Create exactly one item per requested Reading question.
- Choose the distribution from `deep-reading-generation-rules.md`.
- For B1 and above, do not allow the blueprint to be mostly `literal`.
- For B2 and above, include at least one `structure_function`, author stance/purpose item, and one multi-evidence inference or synthesis item when the question count allows.
- For C1/C2, include nuance, implication, rhetorical purpose, assumption, or claim/evidence/limitation/concession analysis when the source text supports it.
- Use `evidence_strategy` to force depth: a high-depth question should usually require paragraph-level or cross-paragraph evidence, not a single sentence.
- Use one of these distractor strategies for MCQ items:
  - true detail but wrong reason
  - true detail but wrong scope
  - similar keyword but opposite meaning
  - plausible paraphrase but unsupported by passage
  - partially correct but incomplete
  - correct idea but wrong paragraph/person/time
  - too broad or too narrow

After generating questions, check each item against its blueprint. If a question does not match its planned type, evidence strategy, depth, or distractor strategy, revise that question before QC.

## Grammar Blueprint

Each Grammar blueprint item must contain:

```json
{
  "question_no": 14,
  "grammar_target": "string",
  "question_type": "controlled choice | contextual choice | error correction | transformation | paragraph editing | writing transfer",
  "depth": "low | medium | high",
  "tested_dimension": "form | meaning | use | discourse | register | writing transfer",
  "trap": "string"
}
```

Generation rules:
- Create exactly one item per requested Grammar question.
- Choose the distribution from `deep-grammar-generation-rules.md`.
- B1 and above must include context-level reasoning, error correction or transformation, short paragraph/context grammar, and writing transfer.
- B2 and above must include paragraph editing, cohesion grammar, register-aware grammar, meaning contrast, and grammar choices that affect tone or precision when the question count allows.
- C1/C2 must test nuance, stance, register, precision, cohesion, rhetorical effect, or information structure rather than only form recall.
- Do not cluster more than 5 consecutive questions with the same grammar target and clue type; prefer no more than 3.

After generating questions, check each item against its blueprint. If a question can be answered by a surface keyword only, revise the item or update the blueprint distribution before returning JSON.

## B1 Example Blueprint

```json
{
  "reading_blueprint": [
    {
      "question_no": 1,
      "type": "literal",
      "depth": "low",
      "target_skill": "identify an explicitly stated campus service",
      "evidence_strategy": "single sentence",
      "distractor_strategy": "true detail but wrong paragraph/person/time"
    },
    {
      "question_no": 2,
      "type": "inference",
      "depth": "medium",
      "target_skill": "infer why student involvement helps first-year students settle in",
      "evidence_strategy": "multiple sentences",
      "distractor_strategy": "true detail but wrong reason"
    },
    {
      "question_no": 3,
      "type": "main_idea",
      "depth": "medium",
      "target_skill": "identify the main purpose of a paragraph about student clubs",
      "evidence_strategy": "paragraph-level",
      "distractor_strategy": "too broad or too narrow"
    }
  ],
  "grammar_blueprint": [
    {
      "question_no": 1,
      "grammar_target": "present perfect vs past simple",
      "question_type": "contextual choice",
      "depth": "medium",
      "tested_dimension": "meaning",
      "trap": "single time word suggests a tense, but the context shows an ongoing result"
    },
    {
      "question_no": 2,
      "grammar_target": "relative clauses",
      "question_type": "error correction",
      "depth": "medium",
      "tested_dimension": "use",
      "trap": "generic noun without context creates defining/non-defining ambiguity"
    },
    {
      "question_no": 3,
      "grammar_target": "contrast linkers",
      "question_type": "writing transfer",
      "depth": "medium",
      "tested_dimension": "writing transfer",
      "trap": "connector must preserve the contrast between two campus participation rates"
    }
  ]
}
```
