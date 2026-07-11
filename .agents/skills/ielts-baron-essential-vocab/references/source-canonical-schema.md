# Source Canonical Schema

Documentation for `schemas/canonical-source.schema.json`.

## Purpose
The canonical source model is the single-source-of-truth representation of one unit/topic extracted from the source PDF. It is created by Agent 06 and must not add any content beyond what was extracted.

## Key Sections
- `unit` — Unit metadata (ID, name, topic, page range)
- `reading_passage` — Title + paragraphs with paragraph_id and source_refs
- `questions` — All questions with type, text, options, source_refs
- `word_family` — Word family items with forms and POS
- `core_vocabulary` — Vocabulary items from the unit
- `answer_key_source` — Answers as found in the source (not fabricated)
- `assets` — Images, tables, charts with paths and provenance
- `unresolved_items` — Gaps that could not be resolved

## source_ref Object
```json
{
  "source_id": "sha256-...",
  "page": 12,
  "block_id": "BLK-0042",
  "paragraph_id": "C",
  "extraction_method": "native_text",
  "confidence": 0.98
}
```

## Rules
- Every paragraph, question, and answer must have at least one source_ref
- If answer key is not found, set `answer_key_source` to empty and add an unresolved_item
- Do not add definitions, explanations, or enriched content at this stage
