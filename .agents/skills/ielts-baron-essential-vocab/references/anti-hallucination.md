# Anti-Hallucination Rules

## Content Classification (mandatory)

Every content block MUST carry exactly one classification:

| Classification | Meaning | Provenance Required |
|---------------|---------|-------------------|
| `SOURCE_EXTRACTED` | Verbatim text from source PDF | source_id, page, block_id, method, confidence |
| `SOURCE_NORMALIZED` | Source text with OCR corrections | original + correction_log |
| `DERIVED_FROM_SOURCE` | Inferred from source (e.g., POS tagging) | source_ref + derivation_method |
| `ENRICHED_CONTENT` | Added by agent (examples, explanations) | Must be labeled visually |
| `EXTERNAL_REFERENCE` | From verified external source | URL + access_date |
| `MODEL_GENERATED_DRAFT` | LLM output not yet validated | model_name + prompt_version |
| `UNRESOLVED` | Data gap — not fabricated | description + suggested_action |

Content without classification = validation failure.

## Provenance Requirements

Source-grounded content (SOURCE_EXTRACTED, SOURCE_NORMALIZED) must include:
- `source_id` — unique_source_id (SHA-256)
- `page` — 1-indexed page number
- `block_id` — BLK-XXXX from extraction
- `paragraph_id` — if applicable
- `extraction_method` — native_text | ocr | table_parser | image_extract
- `confidence` — 0.0 to 1.0

## Hard Rules

1. **Never fabricate IPA transcriptions**. Use verified dictionaries or mark `UNRESOLVED`.
2. **Never fabricate Answer Keys**. If not found in source, report `ANSWER_KEY_NOT_FOUND`.
3. **Never fabricate definitions**. Use verified dictionaries or mark `ENRICHED_CONTENT`.
4. **Never claim "extracted from source"** if text was modified, enriched, or inferred.
5. **Never silently correct OCR errors**. Keep raw + create normalized copy + log correction.
6. **Never label enriched content as source**. Vocabulary expansions, C1-C2 idioms, compound words not in source = `ENRICHED_CONTENT`.
7. **Never fabricate URLs**. Only link to verified domains (Cambridge Dictionary, British Council, Perfect English Grammar).

## When Data is Missing

1. Record the gap as an `unresolved_item` with severity and suggested action.
2. If severity = critical → trigger human review, do NOT auto-fill.
3. If severity = low → proceed with warning label.
4. Never fill gaps to make output "look complete."

Example:
```json
{
  "item_id": "UNRES-001",
  "type": "answer_key_missing",
  "description": "Answer Key for questions 8-13 not found in source document",
  "severity": "high",
  "suggested_action": "human_review"
}
```
