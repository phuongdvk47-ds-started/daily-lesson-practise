# Deep Grammar and IELTS Accuracy Rules

## 1. Grammar Depth Distribution Rule

Each grammar set must include a balanced distribution of cognitive levels. Do not allow the grammar section to rely mainly on isolated form recognition.

→ **Ratio table by level**: See `deep-grammar-generation-rules.md §Ratio Rules by Level` (this is the authoritative source; do not duplicate it here).

Categories:
- **Mechanical Form**: learners identify the correct grammatical form from a controlled sentence.
- **Meaning Contrast**: learners choose forms based on meaning differences, not only patterns.
- **Context / Discourse**: learners use sentence meaning, time context, logical relationship, register, cohesion, or surrounding clues.
- **Transformation / Error Correction / Writing Transfer**: learners rewrite, combine, correct, edit, or produce language for writing.

For lower levels A1 and A1+:
- keep sentences short
- keep vocabulary familiar
- still include context, but do not overload the learner
- use pictures, schedules, simple routines, classroom contexts, family, daily activities, school, food, places, hobbies, and simple personal information

For higher levels B2-C2:
- increase complexity through meaning, clause structure, precision, register, cohesion, and editing accuracy
- do not increase difficulty only by adding rare vocabulary


## 2. Difficulty Balance Rule

Each grammar set must include:
- 30-40% easy questions
- 40-50% medium questions
- 10-20% hard or stretch questions

Questions marked as stretch must:
- target the next CEFR level
- include `(*)` in the visible question text
- set `"stretch": true`
- set `"difficulty": "hard"`

For `+` levels:
- treat the current level as almost mastered
- use 60-70% current-level targets
- use 30-40% next-level bridge targets
- mark the most difficult 10-20% as stretch

## 3. Anti-Pattern Repetition Rule

Do not create more than 3 consecutive questions testing the same surface pattern.

Invalid patterns:
- 10 consecutive tense questions
- 10 consecutive gerund/infinitive questions
- 10 consecutive article questions
- 10 consecutive questions where a single time marker reveals the answer
- 10 consecutive questions with identical sentence frames

Required behavior:
- Mix tense, clause, linker, agreement, article, preposition, correction, and transformation items where level-appropriate.
- Avoid predictable blocks where students can answer mechanically.
- Keep section grouping learner-friendly, but vary item type and cognitive demand inside each section.

## 4. Grammar from Reading Evidence Rule

At least 30% of grammar questions must reuse ideas, situations, noun phrases, or logical relationships from the reading passage when a reading passage is provided.

Rules:
- Do not copy full sentences mechanically from the passage.
- Adapt passage ideas into new grammar contexts.
- Preserve factual accuracy when the sentence refers to the passage.
- If the item says “According to the passage/report/text”, the factual claim must be directly supported by the reading passage.
- If factual support is weak or absent, remove the attribution and make the sentence hypothetical/general.
- For A1-A2, simplify the language while preserving the same basic situation.
- For B1-C2, preserve more of the original logical relationship and discourse purpose.

Valid:
“Universities often provide meeting spaces, which helps student organizations organize regular events.”

Invalid:
“According to the passage, every student who joins a club gets a job immediately.”
Reason: unsupported by passage.

## 5. Writing Transfer Rule

At least 20-30% of grammar questions must prepare students for the writing tasks in the same pack.

For chart/table writing tasks:
- include comparison structures
- include contrast linkers
- include quantity expressions
- include articles and plural generalisations where level-appropriate
- include subject-verb agreement in chart-style sentences
- include referencing such as this, these, such, one/ones at B2 and above

For email or paragraph writing tasks:
- include polite requests
- include purpose clauses
- include relative clauses where level-appropriate
- include sentence combining for concision
- include verb patterns useful for intentions, plans, and recommendations
- include register control at B2 and above

For opinion/argument writing tasks:
- include concession, counterargument, hedging, stance, nominalisation, and formal recommendation structures where level-appropriate

## 6. Smart Distractor Rule for MCQ

For MCQ grammar questions, distractors must represent common learner errors, not random impossible forms.

Each distractor must be wrong for a clear reason:
- wrong tense
- wrong verb pattern
- wrong linker meaning
- wrong relative pronoun
- wrong clause type
- missing comma or wrong comma placement
- subject-verb agreement error
- article/preposition error
- wrong register
- awkward cohesion
- changes original meaning

Avoid obviously impossible options unless the level is A1-A2.

For every MCQ question, include internal option validation metadata.

## 7. Context-Rich Tense Rule

Tense questions must not rely only on obvious time markers such as “yesterday”, “last month”, or “up to now”.

At least half of tense questions must require context interpretation.

Weak:
“Yesterday, the club ______ a meeting.”
Reason: answer is too obvious from “Yesterday”.

Better:
“The club started in 2022 and is still active today. It ______ many new members since then.”
Reason: students must understand continuation from past to present.

## 8. Clause and Linker Depth Rule

Clause and linker questions must test logical relationship, not only memorized translation.

Depending on level, include:
- A1-A2: and, but, because, so, when
- A2+: although, before, after, while, so that
- B1: although, while, whereas, because, since, as a result, so that
- B2: despite, in spite of, whereas, while, therefore, consequently, so as to, in order that
- C1-C2: notwithstanding, albeit, insofar as, provided that, unless, even if, whereas, thereby, hence

Every linker question must have only one intended logical relationship.
Avoid cases where two linkers are both acceptable unless the task explicitly asks for multiple possible answers.

## 9. IELTS Editing Accuracy Rule

Error correction questions must imitate realistic learner errors in IELTS Writing.

Prioritize by level:
- A1-A1+: be/have, articles, plural -s, basic word order, simple prepositions, subject-verb agreement
- A2-A2+: tense consistency, comparatives, countable/uncountable nouns, modals, because/so/although, adverbs
- B1-B1+: present perfect vs past simple, relative clauses, passive basics, conditionals, linkers, gerund/infinitive
- B2-B2+: complex subject-verb agreement, articles in academic generalisations, reduced relative clauses, parallelism, referencing
- C1-C1+: inversion, cleft sentences, nominalisation, participle clauses, hedging, advanced cohesion
- C2: register precision, rhetorical structure, dense noun phrases, complex punctuation, ambiguity reduction, concise academic editing

Each error correction item must:
- contain exactly one target error
- have a corrected answer that differs from the original
- explain the actual error present in the original sentence

## 10. Meaning-Preservation Transformation Rule

Sentence transformation and sentence combining items must preserve the original meaning strictly.

Before finalizing each item, check:
- Does the expected answer keep the same meaning?
- Does the prompt provide enough context?
- Is there exactly one target structure?
- Is there exactly one expected answer or one narrow answer family?
- Does the transformation accidentally add, remove, or exaggerate information?
- Does the transformation change certainty, quantity, time, subject, cause, contrast, or condition?

Invalid:
Original: “Some students join clubs to reduce stress.”
Rewrite: “All students join clubs because they are stressed.”
Reason: meaning changed.

Valid:
Original: “Some students join clubs to reduce stress.”
Rewrite using “so that”:
“Some students join clubs so that they can reduce stress.”

## 11. Productive Grammar Rule

At least 25% of questions must require learners to produce language, not only select options.

Productive types include:
- constrained gap-fill without options
- sentence transformation
- sentence combining
- error correction
- short controlled rewrite
- register editing at B2 and above
- concision editing at C1 and above

Ensure productive questions remain constrained enough to have one expected answer or a narrow answer family.

## 12. Surface-Clue Reduction Rule

Avoid questions where students can answer correctly by spotting only one surface clue.

For every question, ask:
- Can the learner answer without understanding the sentence?
- Is the answer revealed by a single word only?
- Are the distractors too obviously impossible?
- Does the same trick repeat across many questions?

If yes, revise the item to require more context, meaning, sentence relationship, or writing purpose.

# CEFR Deep Grammar Level Map

Use this map when selecting grammar targets, difficulty, cognitive level, and stretch items.

Important:
- For a normal level, prioritize targets inside that level.
- For a `+` level, combine current-level consolidation with next-level bridge targets.
- Do not skip foundational accuracy at lower levels.
- Do not make upper-level grammar difficult only by using rare vocabulary.

## A1 / A1+
- **Mandatory Types**: Meaning contrast (basic); Pronoun/reference clarity; Word order in real sentences; Short context.
- **Rule**: Max 70% mechanical fill-in.
**Targets (1-3):** be: am/is/are, have/has, there is/are, present simple for routines/facts, basic subject-verb agreement, singular/plural nouns, articles in simple phrases, possessives, basic prepositions (in, on, at, under, next to), can/can't, simple conjunctions (and, but, because).
**Deep Goal:** Understand the simple situation. Use familiar contexts (classroom, family, daily routine, school, food, hobbies).
**Question Types:** simple MCQ, picture/context gap fill, sentence ordering, choose correct sentence, correct one simple error, short controlled transformation.
**Stretch:** present simple with he/she -s, some/any, past simple of be, simple comparative.

## A2 / A2+
- **Mandatory Types**: Tense meaning contrast; Countable/uncountable in context; Modal meaning (ability/permission/advice); Basic connectors (because/so/but/although); Simple error correction.
**Targets (1-3):** present simple vs continuous, past simple regular/irregular, future with going to/will, comparatives/superlatives, data comparison modifiers (significantly, slightly, much, a little, twice as...as, higher/lower than), countable/uncountable, some/any/much/many/a few/a little, modals (should, must, have to, can/could), adverbs of frequency/manner, compound sentences (because/so/although).
**Deep Goal:** Move beyond isolated forms. Choose tense based on time context, understand cause/result/contrast, compare quantities accurately, use modals based on advice/obligation/ability.
**Stretch:** present perfect experience, first conditional, passive simple present/past, relative clauses, contrast linkers (while/whereas).

## B1 / B1+
- **Mandatory Types**: Present perfect vs past simple by meaning (not keyword); Gerund/infinitive with meaning difference; Modals of advice/obligation/prohibition; Relative clauses; Conditionals; Passive (focus shift).
- **Rule**: At least 5 items must require context-level reasoning. At least 3 items must be error correction or transformation. No 10 consecutive tense or V-ing/to V drills.
**Targets (1-3):** present perfect vs past simple, present perfect continuous, past continuous, first/second conditionals, basic passives, relative clauses (who/which/that/where), defining vs non-defining, gerunds/infinitives, reported speech basics, linkers (cause, contrast, result), chart contrast linkers (while, whereas, by contrast, in contrast).
**Deep Goal:** Decide tense from context, distinguish essential/extra info, use linkers logically, combine sentences, correct common IELTS errors.
**Stretch:** subject-verb agreement with complex subjects, articles with general plural nouns, reduced relative clauses, parallel structures.

## B2 / B2+
- **Mandatory Types**: Tense/aspect nuance; Modality nuance; Participle clauses; Reduced relative clauses; Passive/reporting structures; Conditionals and mixed conditionals; Cohesion devices; Register-aware grammar; Paragraph-level grammar editing.
**Targets (1-3):** complex sentences (concession, purpose, result), advanced passives, nominalisation basics, reduced relative clauses, participle clauses, mixed conditionals introduction, hedging (may/might/tend to/appear to), referencing/substitution (this, these, such, one/ones), advanced subject-verb agreement, articles (geographical, institutions, abstract, categories, academic generalisations), parallel structures.
**Deep Goal:** Focus on writing accuracy and sentence maturity. Reduce wordiness, improve cohesion, use articles accurately, combine ideas precisely, use hedging.
**Stretch:** advanced nominalisation, inversion, cleft sentences, participle clauses for concision, complex conditionals, subjunctive mood.

## C1 / C1+
- **Mandatory Types**: Advanced modality; Inversion / emphasis; Cleft sentences; Hedging and stance; Nominalisation; Complex subordination; Ellipsis/substitution; Information structure; Grammar choices linked to tone and argument.
**Targets (1-3):** advanced nominalisation, inversion, cleft sentences, participle clauses, complex conditionals, subjunctive mood (it is essential that...), hedging/stance, advanced cohesive referencing, counterargument/concession.
**Deep Goal:** Test control, precision, register, rhetorical purpose. Express ideas academically, reduce clumsy clauses, manage concession, avoid overstatement.
**Stretch:** dense noun phrases, rhetorical fronting, nuanced modality, advanced punctuation, register shifting.

## C2
- **Mandatory Types**: Fine-grained grammar nuance; Ambiguity resolution; Register and rhetorical effect; Complex clause architecture; Advanced cohesion; Grammar affecting implication/stance; Grammatically possible but contextually wrong distractors.
**Targets (1-3):** stylistic control, register shifting, dense noun phrases, advanced subordination, rhetorical emphasis, nuanced modality, subjunctive/mandative structures, parallelism, ambiguity reduction, complex punctuation.
**Deep Goal:** Test expert-level control. Exact meaning, subtle register, concision, rhetorical rhythm, information structure, ambiguity management, academic polish.
**Stretch:** Use C2 mastery tasks. Increase rhetorical precision, elegant concision, register-sensitive alternatives.



# Level Alias and Target Selection Rule

## Level Normalization
The input `level` may be: A1, A1+, A2, A2+, B1, B1+, B2, B2+, C1, C1+, C2.
Do not treat `+` levels as invalid.

## Meaning of `+`
A `+` level means the learner is stronger than the base level but not fully at the next level. The grammar set must consolidate the base level and introduce bridge targets.

## Target Selection by Level Type
**Normal levels:**
- 1-3 main targets from the level.
- 0-1 stretch target from next level if `grammar_question_count >= 10`.
- Prioritize high-impact IELTS targets.

**`+` levels:**
- 1-2 strong targets from current level.
- 1-2 bridge targets from next level.
- Ensure 30-40% of questions prepare for the next level.
- Mark the hardest 10-20% as stretch if they clearly exceed the current level.

# Grammar Question Distribution Rule

## For 30 Grammar Questions
- 6 questions: controlled form check
- 8 questions: context-based MCQ or gap-fill
- 6 questions: realistic error correction
- 5 questions: sentence combining
- 3 questions: sentence transformation / paraphrase
- 2 questions: stretch questions from the next CEFR level (or mastery for C2)

Recommended neutral section titles:
- Part A. Grammar in context
- Part B. Linkers, clauses, and meaning
- Part C. Error correction
- Part D. Sentence combining and transformation

## For 20 Grammar Questions
4 form check, 6 context-use, 4 error correction, 3 combining, 2 transformation, 1 stretch.

## For 10 Grammar Questions
2 form check, 3 context-use, 2 error correction, 2 combining/transformation, 1 stretch.

## For Fewer Than 10 Questions
Include at least 2 item types, at least 1 context-use, at least 1 productive. Avoid repeating patterns.

# Deep Grammar Examples by Level

## A1 Example
Deep A1: "Look at the school card: Name: Anna. Class: 1A. Role: student. Anna ___ a student." -> is. Uses simple context but language remains A1.

## A1+ Example
Question: “Tom plays football every Sunday. He ______ plays on weekdays because he has school.” -> never. Tests frequency adverbs in context.

## A2 Example
Deep A2: “Last week, I visited the library for the first time. Before that, I usually ______ at home.” -> studied. Past simple in contrast.

## A2+ Example
Question: “Mai has never joined a school club before, but she wants to try one this semester. She ______ a member of the art club yet.” -> has not become. Present perfect with yet.

## B1 Example
Deep B1: “The student union released its first guide in 2022. Since then, it ______ several updated versions for new students.” -> has released. Tense in context.

## B1+ Example
Question: “There are several student mentors in the dormitory. Choose the sentence that clearly identifies which mentor helped the new students.” -> The mentor who lives next door helped the new students. Defining relative clause.

## B2 Example
Question: “Correct the error: The number of students who join academic clubs are increasing.” -> is increasing. Subject-verb agreement with complex subject.

## B2+ Example
Question: “Rewrite the sentence to make it more concise using a participle clause: Students who participate in campus organizations often develop stronger communication skills.” -> Students participating in campus organizations often develop stronger communication skills.

## C1 Example
Question: “Rewrite the sentence using a formal subjunctive structure: Schools should provide more support for first-year students.” -> It is essential that schools provide more support for first-year students.

## C1+ Example
Question: “Edit the sentence to make the claim more nuanced and academic: Joining clubs always improves students’ academic performance.” -> Joining clubs may improve...

## C2 Example
Question: “Rewrite the sentence to make it more concise, formal, and rhetorically controlled: Students who are involved in clubs usually get many benefits, and these benefits can help them in their studies and in their future jobs.” -> Club involvement can yield academic and professional benefits.

# Weak vs Deep Grammar Examples

## Weak tense item
Invalid: “Yesterday, the student union ______ a guide.” (Revealed by "Yesterday")
Improved: “The student union released its first guide in 2022. Since then, it ______ several updated versions for new students.”

## Weak gerund/infinitive item
Invalid: “We look forward to ______ our new advisor.” (Only tests memorized pattern)
Improved: “Complete the sentence so that it sounds natural in a formal email: I look forward to ______ your advice about joining the debating society.”

## Weak relative clause item
Invalid: “The student ______ lives next door is helpful.” (Pronoun matching only)
Improved: “There are several student mentors in the dormitory. Identify the sentence that clearly tells us which mentor helped the new students.”

## Weak correction item
Invalid: “Correct the error: Local businesses do not like the new calendar.” (No error exists)
Improved: “Correct the error: The number of students who join academic clubs are increasing.”

## Weak advanced item
Invalid: “Choose the correct word: It is important that he ___ on time.”
Improved: “A school policy proposal is making a formal recommendation. Complete the sentence: It is essential that every first-year student ______ access to academic support during the first semester.”

# Final Deep Grammar Quality Checklist

Before returning JSON, verify:

## 1. Exact Count
- The number of questions equals `grammar_question_count`.

## 2. Level Handling
- The input level is recognized. `+` levels handled as bridge levels.

## 3. Target Quality
- 1-3 main grammar targets selected.
- Stretch/bridge targets used appropriately.

## 4. Depth
- Not mostly form-recognition.
- At least 30% require context or meaning.
- At least 20-30% support writing tasks.
- At least 30% connect to reading passage.
- At least 25% require productive grammar.

## 5. Anti-Repetition
- No more than 3 consecutive questions test the same surface pattern.

## 6. One Answer
- Each item has exactly one clear answer or one narrow answer family.

## 7. Error Correction
- Exactly one target error. Original actually contains the error. Corrected differs. Explanation matches.

## 8. Relative Clauses
- Defining/non-defining include enough context. Commas used correctly.
- **Sentence Combining Direction**: If combining two main clauses into a relative clause sentence where either clause could logically become the relative clause, the prompt MUST specify which sentence to convert (e.g. `"Make Sentence 1 the relative clause:"`).
- **Defining Pronoun Equivalence**: In defining relative clauses, if the prompt does not restrict the relative pronoun to `which` or `who`, the answer key MUST accept `that` as equally valid and document it in explanations.

## 9. Factual Accuracy
- "According to the report" claims must be supported by the reading passage. Otherwise, make hypothetical.

## 10. Metadata
Every question includes: `difficulty`, `cognitive_level`, `source_connection`, `target_structure`, `level`, `stretch`, `one_answer_check`, `deep_grammar_validation`.
MCQ includes: `option_validations`.
Error Correction includes: `error_correction_validation`.
Sentence Transformation / Combining includes: `meaning_preservation_validation`.

## 11. Fail Conditions (PDF Checker / Daily IELTS Checker)
The pack MUST FAIL if any of the following are true:
- > 5 consecutive questions with the same target grammar and clue type.
- > 40% of questions use obvious surface clues at B1 or above.
- > 30% of questions use obvious surface clues at B2 or above.
- The level-specific distribution table in this reference is violated.
- 0 error correction or transformation questions at B1 or above.
- 0 paragraph/context grammar questions at B2 or above.
- 0 writing-transfer grammar questions at B1 or above.
- Explanations only state the formula without explaining meaning/use.
- A question lacks a reasonable/plausible distractor.
- The grammar target is drastically lower than the current level.

## 12. JSON Validity
- Return JSON only. No Markdown outside JSON. No trailing comments. No invalid enum values. No missing required metadata.
