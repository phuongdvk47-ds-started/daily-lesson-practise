# Quality Gates

## Gate 0 — Execution Policy
- [ ] Task classified with execution_class
- [ ] Engine is allowed for this task
- [ ] Privacy level satisfied
- [ ] Budget within limits
- [ ] Cache checked
- [ ] Fallback chain defined

## Gate 1 — Source Integrity
- [ ] Source file exists
- [ ] Checksum computed and matches
- [ ] Source metadata recorded
- [ ] Format is supported (PDF)

## Gate 2 — Extraction Integrity
- [ ] Page inventory complete
- [ ] Critical pages have text (or OCR attempted)
- [ ] Images extracted and inventoried
- [ ] Tables extracted where present
- [ ] extraction-manifest.json exists

## Gate 3 — Unit Integrity
- [ ] Target unit identified
- [ ] Page range determined
- [ ] Reading passage located
- [ ] Question section located
- [ ] Confidence >= 0.90

## Gate 4 — Provenance Integrity
- [ ] All reading paragraphs have source_refs
- [ ] All questions have source_refs
- [ ] Answer key entries reference valid question_ids
- [ ] No orphan answer entries
- [ ] No unsupported source quotes

## Gate 4B — Model Output Quality
- [ ] Output validates against schema
- [ ] Confidence meets threshold
- [ ] Provenance present on source-grounded claims
- [ ] No unsupported claims detected
- [ ] Quality score meets minimum

## Gate 5 — Content Integrity
- [ ] No answer leakage in practice document
- [ ] Answer numbering matches questions
- [ ] Enriched content properly labeled
- [ ] lession_id valid and consistent
- [ ] No critical unresolved items

## Gate 6 — Render Integrity
- [ ] All pages are A4
- [ ] Footer present on every page with correct lession_id
- [ ] No text overflow
- [ ] No missing images/tables
- [ ] No unexpected blank pages
- [ ] No orphan headings at page bottom
- [ ] IPA renders correctly
- [ ] Vietnamese text renders correctly

## Gate 6B — Cost and Resource Integrity
- [ ] No unnecessary premium LLM calls
- [ ] No repeated calls for cached results
- [ ] No full-document context sent unnecessarily
- [ ] Local-first principle respected
- [ ] All premium escalations documented with reasons

## Gate 7 — Final Delivery
- [ ] daily-practice.pdf exists and > 0 bytes
- [ ] vocabulary-grammar.pdf exists and > 0 bytes
- [ ] answer-key.pdf exists and > 0 bytes
- [ ] lesson-manifest.json validates
- [ ] Content QA status = PASS
- [ ] Visual QA status = PASS or WARN
- [ ] Output path is correct

## Confidence Thresholds

```yaml
confidence_thresholds:
  unit_location: 0.90
  ocr_block: 0.92
  answer_mapping: 0.95
  level_assessment: 0.75
```

Below threshold → no auto-approve → escalate or human review.
