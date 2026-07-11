# Content Classification Labels

## Overview
Every piece of content in the pipeline carries a classification label indicating its provenance and trust level. This ensures transparency, prevents hallucination, and enables clear visual distinction in rendered PDFs.

## Label Definitions

### SOURCE_EXTRACTED
- **Meaning**: Verbatim text from the source PDF
- **Trust Level**: Highest
- **CSS Class**: `label-source`
- **Visual**: Green badge
- **Required Provenance**: `source_id`, `page`, `block_id`, `extraction_method`, `confidence`

### SOURCE_NORMALIZED
- **Meaning**: Source text with OCR corrections applied
- **Trust Level**: High
- **CSS Class**: `label-source`
- **Visual**: Green badge
- **Required Provenance**: Original text + correction log

### DERIVED_FROM_SOURCE
- **Meaning**: Content derived from source (e.g., POS tags, word forms)
- **Trust Level**: Medium-High
- **CSS Class**: `label-derived`
- **Visual**: Blue badge
- **Required Provenance**: `source_ref` + derivation method

### ENRICHED_CONTENT
- **Meaning**: Content added by the agent (examples, Vietnamese translations, C1-C2 idioms)
- **Trust Level**: Medium
- **CSS Class**: `label-enriched`
- **Visual**: Yellow badge
- **Required Provenance**: Agent name, model version (if LLM)

### EXTERNAL_REFERENCE
- **Meaning**: From a verified external source (dictionary, grammar reference)
- **Trust Level**: Medium-High
- **CSS Class**: `label-external`
- **Visual**: Purple badge
- **Required Provenance**: URL + access date

### MODEL_GENERATED_DRAFT
- **Meaning**: LLM output not yet validated against quality gates
- **Trust Level**: Low
- **CSS Class**: N/A (should not appear in final output)
- **Required Provenance**: model name, prompt version, timestamp

### UNRESOLVED
- **Meaning**: Data gap — information could not be determined
- **Trust Level**: Explicit gap
- **CSS Class**: N/A
- **Required Provenance**: Description + suggested resolution action

## Validation Rules
1. Content without classification = pipeline validation failure
2. SOURCE_EXTRACTED content must have `confidence >= 0.92`
3. ENRICHED_CONTENT must never claim to be from the source
4. MODEL_GENERATED_DRAFT must not appear in final rendered output
5. UNRESOLVED items with severity "critical" block pipeline completion
