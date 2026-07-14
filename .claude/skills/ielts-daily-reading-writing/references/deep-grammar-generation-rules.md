# Deep Grammar Generation Rules

Use this reference with `.claude/agents/ielts-grammar.md`, `grammar-by-level.md`, and `deep-question-blueprint.md` before generating grammar guides and practice questions.

## Ratio Rules by Level

Treat Mechanical Form as a maximum and the other columns as minimums.

| Level | Mechanical Form | Meaning Contrast | Context / Discourse | Transformation / Error Correction / Writing Transfer |
|---|---:|---:|---:|---:|
| A1 | <=60% | >=20% | >=10% | >=10% |
| A1+ | <=55% | >=20% | >=15% | >=10% |
| A2 | <=45% | >=25% | >=15% | >=15% |
| A2+ | <=40% | >=25% | >=20% | >=15% |
| B1 | <=30% | >=30% | >=20% | >=20% |
| B1+ | <=25% | >=30% | >=25% | >=20% |
| B2 | <=20% | >=30% | >=30% | >=20% |
| B2+ | <=15% | >=30% | >=35% | >=20% |
| C1 | <=10% | >=30% | >=35% | >=25% |
| C1+ | <=10% | >=30% | >=40% | >=25% |
| C2 | <=5% | >=30% | >=40% | >=30% |

## Form + Meaning + Use Rule

Each grammar item must test more than a remembered pattern whenever the level allows it. For every item, plan:
- Form: the structure required.
- Meaning: what the grammar means in the sentence.
- Use: why that form fits this context.
- Trap: why a plausible learner answer is wrong.

Weak: `We have lived here since 2020. Answer: have lived because since.`

Deep: `The sentence connects a past starting point with a situation still true now. The key is not only "since" but the continuing meaning, so Present Perfect is required.`

## Surface-Clue Reduction

Reduce questions where one keyword reveals the answer:
- `since` -> Present Perfect
- `yesterday/last month` -> Past Simple
- `look forward to` -> V-ing
- `mind` -> V-ing
- `manage/decide` -> to V
- `avoid` -> V-ing

These patterns may appear only when mixed with contextual reasoning and plausible distractors. For B1 and above, at least 40% of Grammar questions must require meaning/context. For B2 and above, at least 50% must require discourse/context/register. For C1/C2, grammar must test nuance, stance, register, precision, cohesion, or rhetorical effect.

## Context-Level Requirements

For B1 and above:
- Include at least 5 context-level reasoning items when `grammar_question_count >= 20`.
- Include at least 3 error correction or transformation items when `grammar_question_count >= 20`.
- Include at least 2 short paragraph/context grammar items.
- Include at least 2 writing-transfer grammar items.
- Do not create more than 5 consecutive questions with the same grammar target and clue type.

For B2 and above:
- Include paragraph editing.
- Include cohesion grammar.
- Include register-aware grammar.
- Include meaning contrast.
- Include grammar choices affecting tone or precision.

For C1/C2:
- Include hedging, nominalisation, advanced modality, information structure, and grammar linked to stance, argument, diplomacy, or precision.
- Use inversion, cleft sentences, ellipsis/substitution, and emphasis when suitable for the target level and topic.

## Sentence Combining and Transformation

- Do not only ask learners to use a fixed connector such as `because`, `although`, or `who`.
- Require natural rewriting and meaning preservation.
- Allow a narrow answer family when more than one natural expression is possible.
- B1+ should test logical relationships: cause, contrast, concession, purpose, result, condition.
- B2+ should test cohesion, emphasis, information flow, and sentence maturity.

## Error Correction

Every error correction item must:
- contain exactly one target error unless the prompt explicitly asks for multiple errors
- match the target grammar
- have a natural corrected sentence
- not use an already-correct original sentence
- not use a corrected answer identical to the original
- not allow many reasonable corrections while the answer key accepts only one

## Level-Specific Guidance

### A1 / A1+
- Use basic form in short context: be/have, word order, pronoun clarity, basic tense meaning.
- Do not exceed 70% mechanical drill.

### A2 / A2+
- Test tense meaning contrast, countable/uncountable nouns in context, modal meaning, connectors, and simple error correction.

### B1 / B1+
- Test present perfect vs past simple by meaning, gerund/infinitive in context, modals, relative clauses, conditionals, passive focus shift, error correction, transformation, and writing transfer.

### B2 / B2+
- Test tense/aspect nuance, modality nuance, participle clauses, reduced relative clauses, passive/reporting structures, conditionals, cohesion, register-aware grammar, and paragraph-level editing.

### C1 / C1+
- Test advanced modality, inversion/emphasis, cleft sentences, hedging, stance, nominalisation, complex subordination, ellipsis/substitution, information structure, and grammar choices linked to tone and argument.

### C2
- Test fine-grained grammar nuance, ambiguity resolution, register and rhetorical effect, complex clause architecture, advanced cohesion, implication, stance, precision, and diplomacy.
- Distractors may be grammatically possible but contextually wrong.
