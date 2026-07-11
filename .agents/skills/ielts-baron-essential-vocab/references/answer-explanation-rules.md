# Answer Explanation Rules

## Per-Answer Requirements
Each answer MUST include:
1. **Answer** — The correct answer
2. **Source** — Where in the source this answer comes from
3. **Paragraph** — Which paragraph contains the evidence
4. **Evidence** — Short source quote (with source_ref)
5. **Reasoning** — Why this is correct
6. **Distractor Analysis** — Why each wrong option is wrong
7. **Paraphrase Matrix** — Source text ↔ question paraphrase mapping
8. **Confidence** — 0.0-1.0
9. **Review Status** — source-confirmed | derived-with-high-confidence | human-review-required

## Review Status Rules
- `source-confirmed`: Answer found directly in Answer Key section of source
- `derived-with-high-confidence`: Answer inferred from passage with confidence ≥ 0.90
- `human-review-required`: Confidence < 0.90 or conflicting evidence

## Word Family Explanations
For each Word Family question, explain:
- Syntactic position requiring this word form
- Part of speech and why
- Singular/plural reasoning
- Agent vs concept distinction
- Collocation requirements
- Why other forms are rejected (with specific reason per form)

## Anti-Fabrication
- If Answer Key not found in source → `ANSWER_KEY_NOT_FOUND`, do NOT fabricate
- If answer uncertain → mark `human-review-required`
- Evidence quotes must have source_refs
- Never say "the book says" without verified source_ref
