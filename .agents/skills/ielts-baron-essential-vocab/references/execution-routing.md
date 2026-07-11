# Execution Routing Policy

## Routing Priority

```
DETERMINISTIC → LOCAL_MODEL → LOW_COST_LLM → PREMIUM_LLM → HUMAN_REQUIRED
```

**Core Rule**: Use the cheapest engine that reliably passes the required quality gate.

## Routing Table

```yaml
routing_policy:
  # === DETERMINISTIC (free) ===
  pdf_metadata:
    execution_class: DETERMINISTIC
    preferred_engine: pymupdf
    premium_llm_allowed: false

  file_download:
    execution_class: DETERMINISTIC
    preferred_engine: urllib
    premium_llm_allowed: false

  fingerprint:
    execution_class: DETERMINISTIC
    preferred_engine: hashlib_sha256
    premium_llm_allowed: false

  text_extraction:
    execution_class: DETERMINISTIC
    preferred_engine: pymupdf
    fallback_engines: [pdfplumber, pdfminer]
    premium_llm_allowed: false

  table_extraction:
    execution_class: DETERMINISTIC
    preferred_engine: pdfplumber
    fallback_engines: [camelot]
    premium_llm_allowed: false

  json_validation:
    execution_class: DETERMINISTIC
    preferred_engine: jsonschema
    premium_llm_allowed: false

  lesson_id_generation:
    execution_class: DETERMINISTIC
    preferred_engine: python_stdlib
    premium_llm_allowed: false

  html_render:
    execution_class: DETERMINISTIC
    preferred_engine: jinja2
    premium_llm_allowed: false

  pdf_render:
    execution_class: DETERMINISTIC
    preferred_engine: playwright_chromium
    fallback_engines: [weasyprint]
    premium_llm_allowed: false

  footer_generation:
    execution_class: DETERMINISTIC
    preferred_engine: jinja2
    premium_llm_allowed: false

  # === LOCAL_MODEL (free) ===
  ocr:
    execution_class: LOCAL_MODEL
    preferred_engine: paddleocr
    fallback_engines: [tesseract]
    premium_llm_allowed: false

  heading_detection:
    execution_class: LOCAL_MODEL
    preferred_engine: rule_based_plus_regex
    fallback_engines: [sentence_transformer]
    premium_llm_allowed: false

  unit_candidate_detection:
    execution_class: LOCAL_MODEL
    preferred_engine: rule_based_plus_regex
    fallback_engines: [sentence_transformer]
    premium_llm_allowed: false

  keyword_extraction:
    execution_class: LOCAL_MODEL
    preferred_engine: spacy
    fallback_engines: [nltk, keybert]
    premium_llm_allowed: false

  answer_leakage_detection:
    execution_class: LOCAL_MODEL
    preferred_engine: rule_based_string_match
    premium_llm_allowed: false

  # === LOW_COST_LLM ===
  ocr_normalization:
    execution_class: LOW_COST_LLM
    preferred_engine: configured_low_cost_model
    fallback_engines: [configured_reasoning_model]
    premium_llm_allowed: true
    estimated_cost_class: low

  vocabulary_grouping:
    execution_class: LOW_COST_LLM
    preferred_engine: configured_low_cost_model
    premium_llm_allowed: true
    estimated_cost_class: low

  # === PREMIUM_LLM ===
  cefr_assessment:
    execution_class: PREMIUM_LLM
    preferred_engine: configured_reasoning_model
    fallback_engines: [human_review]
    premium_llm_allowed: true
    estimated_cost_class: medium

  grammar_analysis:
    execution_class: PREMIUM_LLM
    preferred_engine: configured_reasoning_model
    premium_llm_allowed: true
    estimated_cost_class: medium

  answer_explanation:
    execution_class: PREMIUM_LLM
    preferred_engine: configured_reasoning_model
    premium_llm_allowed: true
    estimated_cost_class: medium

  ambiguity_resolution:
    execution_class: PREMIUM_LLM
    preferred_engine: configured_reasoning_model
    premium_llm_allowed: true
    estimated_cost_class: medium
```

## Escalation Conditions

Escalate to next engine tier only when:
- Schema validation fails
- Confidence below threshold
- Provenance missing
- Semantic consistency fails
- Retry limit exceeded at current tier
- Multiple ambiguous candidates

## Premium LLM Blocking

If `premium_llm_allowed = false`, the router MUST reject any attempt to use Premium LLM
and return `EXECUTION_POLICY_VIOLATION`.

Deterministic tasks that call Premium LLM = test failure.
