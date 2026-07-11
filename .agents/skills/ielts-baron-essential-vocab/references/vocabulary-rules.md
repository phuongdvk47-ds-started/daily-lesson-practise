# Vocabulary Rules

## Categories
1. **Academic Vocabulary** — AWL words and topic-specific academic terms from the reading
2. **Compound Words** — Multi-word terms (source + enriched, labeled)
3. **Idioms** — Idiomatic expressions (source + C1-C2 enriched, labeled)
4. **Phrasal Verbs** — Verb+particle combinations
5. **Academic Collocations** — Frequently co-occurring academic word pairs

## Table Format
```
Word/Phrase | IPA | POS | Definition & Vietnamese | Example in Passage
```

## Content Classification Rules
- Source vocabulary found in the reading → `SOURCE_EXTRACTED`
- Vocabulary normalized from OCR → `SOURCE_NORMALIZED`
- POS/word family derived from source word → `DERIVED_FROM_SOURCE`
- Additional vocabulary not in source → `ENRICHED_CONTENT`
- Dictionary definitions → `EXTERNAL_REFERENCE`

## Hard Rules
1. Examples from the passage MUST have `source_refs` with page and block_id
2. Generated examples MUST be labeled `generated_example`
3. Never fabricate IPA — use verified dictionary or mark UNRESOLVED
4. Never fabricate definitions — use verified dictionary
5. Enriched compound words MUST be labeled `ENRICHED_CONTENT`
6. C1-C2 idioms not in source MUST be labeled `ENRICHED_CONTENT`
7. Never call enriched vocabulary "from Barron's" or "from the source"
