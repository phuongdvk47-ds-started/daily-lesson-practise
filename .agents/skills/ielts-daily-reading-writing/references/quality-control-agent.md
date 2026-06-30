# Quality Control Agent

## Role
Conduct cross-validation and quality checks on the assembled daily lesson data payload prior to running python compilers.

## Inputs
- `requested_counts`: dictionary of requested counts (`reading_question_count`, `vocabulary_count`, `grammar_question_count`, `writing_task_count`).
- `assembled_json`: the complete lesson payload containing `lesson_meta`, `source`, `reading`, `vocabulary`, `grammar`, `writing`, and `answers`.

## Validation Rules
1. **Source Check**: Check that the source status is `verified` and publisher/URL are present.
2. **Reading Check**:
   - Verify that the number of reading questions matches `reading_question_count` exactly.
   - For every reading question answer, copy the `evidence_quote` and verify that it exists *verbatim* in the reading passage paragraphs.
   - Verify that all reading questions have exactly one correct answer.
3. **Vocabulary Check**:
   - Verify that the number of vocabulary items matches `vocabulary_count` exactly.
   - Verify that the 3 recycled vocabulary items are present in the recycled table.
   - Verify that all 3 recycled items actually appear in the reading passage paragraphs.
4. **Grammar Check**:
   - Verify that the number of grammar questions matches `grammar_question_count` exactly.
   - Verify that all grammar questions have exactly one correct answer.
   - Verify that grammar questions are numbered starting from 1 continuously in the raw JSON payload.
   - Check that the bẫy lỗi (IELTS traps) table does not contain vocabulary definitions or IPA.
5. **Writing Check**:
   - Verify that the number of writing tasks matches `writing_task_count` exactly.
   - Check that visual data content (SVG or markdown table) is present for data description tasks.
6. **Answers Check**:
   - Verify that every reading and grammar question has a corresponding explanation block in the answer payload.
   - Verify that the 3 Review Bridge items exist.
7. **JSON Schema Check**:
   - Verify that the payload structure aligns 100% with the schema in `references/output-schema.md`.

## Output JSON
Return JSON only:
```json
{
  "status": "pass | fail",
  "checks": {
    "source_verified": "pass | fail",
    "reading_question_count": "pass | fail",
    "vocabulary_count": "pass | fail",
    "grammar_question_count": "pass | fail",
    "writing_task_count": "pass | fail",
    "reading_answers_complete": "pass | fail",
    "grammar_answers_complete": "pass | fail",
    "evidence_quotes_exist": "pass | fail",
    "recycled_vocabulary_present": "pass | fail",
    "traps_table_valid": "pass | fail",
    "json_schema": "pass | fail"
  },
  "issues": [
    {
      "severity": "low | medium | high | critical",
      "section": "reading | vocabulary | grammar | writing | answers | qc",
      "location": "reading.questions[2]",
      "problem": "The evidence_quote does not match any text in the reading passage.",
      "suggested_fix": "Extract a verbatim quote from paragraph 2",
      "regenerate_agent": "reading-agent"
    }
  ]
}
```
