# Pipeline Contracts — All Agent Specifications

Each agent declares its contract as a JSON object per `schemas/execution-contract.schema.json`.

## Agent 00 — Request Intake & Input Normalizer

```json
{
  "name": "request_intake",
  "purpose": "Normalize input parameters, validate source, create request manifest",
  "input_schema": "CLI args or chat parameters",
  "output_schema": "request.normalized.json (schemas/request.schema.json)",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "python_stdlib",
  "fallback_engines": [],
  "premium_llm_allowed": false,
  "preconditions": ["source provided or lesson_id provided"],
  "postconditions": ["request.normalized.json exists and validates"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 1, "backoff_strategy": "none"},
  "cache_policy": {"cacheable": false},
  "error_codes": ["SRC_UNSUPPORTED_FORMAT"],
  "human_review_conditions": [],
  "estimated_cost_class": "free"
}
```

## Agent 00B — Execution & Model Router

```json
{
  "name": "execution_router",
  "purpose": "Classify tasks, select engine, enforce policy, manage budget",
  "input_schema": "task_name + task_metadata",
  "output_schema": "routing-decision.json (schemas/routing-decision.schema.json)",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "route_execution.py",
  "fallback_engines": [],
  "premium_llm_allowed": false,
  "preconditions": ["task_name defined in routing policy"],
  "postconditions": ["routing decision validated against policy"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 0, "backoff_strategy": "none"},
  "cache_policy": {"cacheable": false},
  "error_codes": ["EXECUTION_POLICY_VIOLATION"],
  "human_review_conditions": [],
  "estimated_cost_class": "free"
}
```

## Agent 01 — Source Identity & Cache Resolver

```json
{
  "name": "cache_resolver",
  "purpose": "Generate unique_source_id, check cache, identify completed stages",
  "input_schema": "source file path",
  "output_schema": "cache-manifest.json, pipeline-state.json",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "hashlib_sha256",
  "fallback_engines": [],
  "premium_llm_allowed": false,
  "preconditions": ["source file accessible"],
  "postconditions": ["unique_source_id computed", "cache status resolved"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 1, "backoff_strategy": "none"},
  "cache_policy": {"cacheable": false},
  "error_codes": ["SRC_HASH_MISMATCH", "CACHE_CORRUPTED"],
  "human_review_conditions": [],
  "estimated_cost_class": "free"
}
```

## Agent 02 — Source Acquisition

```json
{
  "name": "source_acquisition",
  "purpose": "Download or copy source PDF, generate checksum and metadata",
  "input_schema": "source location (path/URL)",
  "output_schema": "source/original.pdf, source-metadata.json, checksum.sha256",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "urllib",
  "fallback_engines": ["requests"],
  "premium_llm_allowed": false,
  "preconditions": ["source location is valid"],
  "postconditions": ["original.pdf exists", "checksum matches"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 3, "backoff_strategy": "exponential", "retry_on": ["SRC_DOWNLOAD_FAILED"]},
  "cache_policy": {"cacheable": true, "cache_key_components": ["source_url_or_path"]},
  "error_codes": ["SRC_ACCESS_DENIED", "SRC_DOWNLOAD_FAILED", "SRC_UNSUPPORTED_FORMAT"],
  "human_review_conditions": ["Google Drive folder with multiple files", "non-PDF source"],
  "estimated_cost_class": "free"
}
```

## Agent 03 — PDF Structure Analyzer

```json
{
  "name": "pdf_structure_analyzer",
  "purpose": "Analyze page count, outline, TOC, text layer, image/table inventory",
  "input_schema": "source/original.pdf",
  "output_schema": "extraction/document-structure.json, page-inventory.json",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "pymupdf",
  "fallback_engines": ["pdfplumber", "pypdf"],
  "premium_llm_allowed": false,
  "preconditions": ["original.pdf exists"],
  "postconditions": ["document-structure.json validates", "page count > 0"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 1, "backoff_strategy": "none"},
  "cache_policy": {"cacheable": true, "cache_key_components": ["source_checksum"]},
  "error_codes": ["PDF_ENCRYPTED", "PDF_TEXT_LAYER_MISSING"],
  "human_review_conditions": [],
  "estimated_cost_class": "free"
}
```

## Agent 04 — Text & Asset Extractor

```json
{
  "name": "text_asset_extractor",
  "purpose": "Extract text blocks, images, tables with page/bbox/confidence",
  "input_schema": "original.pdf + document-structure.json",
  "output_schema": "extraction/ (text-blocks.json, images/, tables/)",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "pymupdf",
  "fallback_engines": ["pdfplumber"],
  "premium_llm_allowed": false,
  "preconditions": ["original.pdf exists", "document-structure.json exists"],
  "postconditions": ["extraction-manifest.json exists", "text blocks extracted"],
  "quality_thresholds": {"min_ocr_confidence": 0.92},
  "retry_policy": {"max_retries": 2, "backoff_strategy": "linear", "retry_on": ["OCR_LOW_CONFIDENCE"]},
  "cache_policy": {"cacheable": true, "cache_key_components": ["source_checksum", "page_range"]},
  "error_codes": ["OCR_LOW_CONFIDENCE"],
  "human_review_conditions": ["OCR confidence < 0.85 on critical pages"],
  "estimated_cost_class": "free"
}
```

## Agent 05 — Unit/Topic Locator

```json
{
  "name": "unit_topic_locator",
  "purpose": "Find target unit, topic, page range, reading, questions, vocabulary, answer key",
  "input_schema": "extraction data + target unit/topic",
  "output_schema": "units/[unit-id]/unit-location.json, source-slice.json",
  "execution_class": "LOCAL_MODEL",
  "preferred_engine": "rule_based_plus_regex",
  "fallback_engines": ["sentence_transformer", "low_cost_llm"],
  "premium_llm_allowed": false,
  "preconditions": ["extraction complete"],
  "postconditions": ["unit identified with confidence >= 0.90"],
  "quality_thresholds": {"unit_location_confidence": 0.90},
  "retry_policy": {"max_retries": 2, "backoff_strategy": "linear"},
  "cache_policy": {"cacheable": true, "cache_key_components": ["source_checksum", "target_unit"]},
  "error_codes": ["UNIT_NOT_FOUND", "UNIT_AMBIGUOUS"],
  "human_review_conditions": ["multiple candidates", "confidence < 0.90", "heading unclear"],
  "estimated_cost_class": "free"
}
```

## Agent 06 — Source Canonicalizer

```json
{
  "name": "source_canonicalizer",
  "purpose": "Convert extraction into canonical source model without adding content",
  "input_schema": "unit-location.json + source-slice text blocks",
  "output_schema": "canonical-source.json (schemas/canonical-source.schema.json)",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "python_stdlib",
  "fallback_engines": [],
  "premium_llm_allowed": false,
  "preconditions": ["unit-location.json exists"],
  "postconditions": ["canonical-source.json validates against schema"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 1, "backoff_strategy": "none"},
  "cache_policy": {"cacheable": true, "cache_key_components": ["source_checksum", "unit_id"]},
  "error_codes": [],
  "human_review_conditions": [],
  "estimated_cost_class": "free"
}
```

## Agent 07 — Grounding & Fidelity Validator

```json
{
  "name": "grounding_validator",
  "purpose": "Verify canonical source against extraction, detect missing/reordered content",
  "input_schema": "canonical-source.json + extraction data",
  "output_schema": "grounding-report.json",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "python_stdlib",
  "fallback_engines": [],
  "premium_llm_allowed": false,
  "preconditions": ["canonical-source.json exists"],
  "postconditions": ["all source claims verified", "no orphan answers"],
  "quality_thresholds": {"answer_mapping_confidence": 0.95},
  "retry_policy": {"max_retries": 1, "backoff_strategy": "none"},
  "cache_policy": {"cacheable": true},
  "error_codes": ["PROVENANCE_MISSING", "ANSWER_KEY_NOT_FOUND", "QUESTION_COUNT_MISMATCH"],
  "human_review_conditions": ["answer mapping confidence < 0.95"],
  "estimated_cost_class": "free"
}
```

## Agent 08 — Reading Level Assessor

```json
{
  "name": "reading_level_assessor",
  "purpose": "Assess CEFR level, IELTS band, lexical/grammar/discourse complexity",
  "input_schema": "reading passage text only (not full canonical source)",
  "output_schema": "level-assessment.json (schemas/level-assessment.schema.json)",
  "execution_class": "PREMIUM_LLM",
  "preferred_engine": "configured_reasoning_model",
  "fallback_engines": ["human_review"],
  "premium_llm_allowed": true,
  "preconditions": ["reading passage extracted"],
  "postconditions": ["CEFR level assigned", "confidence >= 0.75"],
  "quality_thresholds": {"level_assessment_confidence": 0.75},
  "retry_policy": {"max_retries": 2, "backoff_strategy": "linear"},
  "cache_policy": {"cacheable": true, "cache_key_components": ["reading_text_hash", "model_version"]},
  "error_codes": ["LEVEL_ASSESSMENT_LOW_CONFIDENCE"],
  "human_review_conditions": ["confidence < 0.75", "conflicting signals"],
  "estimated_cost_class": "medium",
  "token_budget": {"max_input_tokens": 6000, "max_output_tokens": 2000}
}
```

## Agent 09 — Lesson Identity Manager

```json
{
  "name": "lesson_id_manager",
  "purpose": "Generate unique lession_id: LSN-[Day]-[Level]-[Random8]",
  "input_schema": "day number + CEFR level",
  "output_schema": "lession_id string",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "python_stdlib",
  "fallback_engines": [],
  "premium_llm_allowed": false,
  "preconditions": ["day and level determined"],
  "postconditions": ["lession_id matches format", "idempotent on rerun"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 0, "backoff_strategy": "none"},
  "cache_policy": {"cacheable": true, "cache_key_components": ["day", "level", "source_checksum"]},
  "error_codes": [],
  "human_review_conditions": [],
  "estimated_cost_class": "free"
}
```

## Agent 10 — Vocabulary Knowledge Builder

```json
{
  "name": "vocabulary_builder",
  "purpose": "Build academic vocab, compounds, idioms, phrasal verbs, collocations with provenance",
  "input_schema": "canonical-source.json (vocabulary + reading passage)",
  "output_schema": "vocabulary-knowledge.json",
  "execution_class": "LOW_COST_LLM",
  "preferred_engine": "configured_low_cost_model",
  "fallback_engines": ["configured_reasoning_model"],
  "premium_llm_allowed": true,
  "preconditions": ["canonical-source.json exists"],
  "postconditions": ["all vocab items have content_class", "source examples have refs"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 2, "backoff_strategy": "linear"},
  "cache_policy": {"cacheable": true, "cache_key_components": ["vocab_text_hash", "model_version"]},
  "error_codes": ["MODEL_OUTPUT_VALIDATION_FAILED"],
  "human_review_conditions": [],
  "estimated_cost_class": "low",
  "token_budget": {"max_input_tokens": 6000, "max_output_tokens": 4000}
}
```

## Agent 11 — Grammar & Strategy Analyst

```json
{
  "name": "grammar_analyst",
  "purpose": "Identify grammar points, explain, apply to Writing Task 2, create tips",
  "input_schema": "reading passage text + canonical source grammar hints",
  "output_schema": "grammar-analysis.json",
  "execution_class": "PREMIUM_LLM",
  "preferred_engine": "configured_reasoning_model",
  "fallback_engines": ["human_review"],
  "premium_llm_allowed": true,
  "preconditions": ["reading passage available"],
  "postconditions": ["≥1 grammar point", "≥3 tips", "source examples have refs"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 2, "backoff_strategy": "linear"},
  "cache_policy": {"cacheable": true, "cache_key_components": ["reading_text_hash", "model_version"]},
  "error_codes": ["MODEL_OUTPUT_VALIDATION_FAILED"],
  "human_review_conditions": [],
  "estimated_cost_class": "medium",
  "token_budget": {"max_input_tokens": 6000, "max_output_tokens": 4000}
}
```

## Agent 12 — Daily Practice Composer

```json
{
  "name": "practice_composer",
  "purpose": "Assemble daily practice document model (NO answers included)",
  "input_schema": "canonical-source.json + level-assessment.json + lession_id",
  "output_schema": "practice-document-model.json",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "python_stdlib",
  "fallback_engines": [],
  "premium_llm_allowed": false,
  "preconditions": ["canonical source validated", "level assessed"],
  "postconditions": ["no answer leakage", "all sections present"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 1, "backoff_strategy": "none"},
  "cache_policy": {"cacheable": true},
  "error_codes": [],
  "human_review_conditions": [],
  "estimated_cost_class": "free"
}
```

## Agent 13 — Answer Key & Explanation Builder

```json
{
  "name": "answer_key_builder",
  "purpose": "Build detailed answer explanations, distractor analysis, paraphrase matrix",
  "input_schema": "canonical-source.json (questions + answer_key_source + reading passage)",
  "output_schema": "answer-key.json",
  "execution_class": "PREMIUM_LLM",
  "preferred_engine": "configured_reasoning_model",
  "fallback_engines": ["human_review"],
  "premium_llm_allowed": true,
  "preconditions": ["canonical source has questions and answer key"],
  "postconditions": ["each answer has evidence + reasoning", "confidence assigned"],
  "quality_thresholds": {"answer_mapping_confidence": 0.95},
  "retry_policy": {"max_retries": 2, "backoff_strategy": "linear"},
  "cache_policy": {"cacheable": true, "cache_key_components": ["questions_hash", "answers_hash", "model_version"]},
  "error_codes": ["ANSWER_KEY_NOT_FOUND", "ANSWER_MAPPING_LOW_CONFIDENCE"],
  "human_review_conditions": ["answer mapping confidence < 0.95"],
  "estimated_cost_class": "medium",
  "token_budget": {"max_input_tokens": 8000, "max_output_tokens": 6000}
}
```

## Agent 14 — Content QA Agent

```json
{
  "name": "content_qa",
  "purpose": "Validate all content for completeness, consistency, and correctness",
  "input_schema": "all content artifacts",
  "output_schema": "qa/content-qa-report.json (schemas/qa-report.schema.json)",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "python_stdlib",
  "fallback_engines": [],
  "premium_llm_allowed": false,
  "preconditions": ["all content stages complete"],
  "postconditions": ["QA report generated", "status is PASS or FAIL"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 0, "backoff_strategy": "none"},
  "cache_policy": {"cacheable": false},
  "error_codes": ["CONTENT_QA_FAILED"],
  "human_review_conditions": ["QA status is FAIL"],
  "estimated_cost_class": "free"
}
```

## Agent 15 — Document Model Builder

```json
{
  "name": "document_model_builder",
  "purpose": "Build render-ready document model with sections, typography, page breaks",
  "input_schema": "canonical-source + vocabulary + grammar + answers + level + lession_id",
  "output_schema": "render/document-model.json",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "python_stdlib",
  "fallback_engines": [],
  "premium_llm_allowed": false,
  "preconditions": ["content QA passed"],
  "postconditions": ["document-model.json is complete"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 1, "backoff_strategy": "none"},
  "cache_policy": {"cacheable": true},
  "error_codes": [],
  "human_review_conditions": [],
  "estimated_cost_class": "free"
}
```

## Agent 16 — HTML Renderer

```json
{
  "name": "html_renderer",
  "purpose": "Render document model to print-safe HTML via Jinja2",
  "input_schema": "document-model.json",
  "output_schema": "render/html/*.html",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "jinja2",
  "fallback_engines": [],
  "premium_llm_allowed": false,
  "preconditions": ["document-model.json exists"],
  "postconditions": ["3 HTML files rendered", "HTML is valid"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 2, "backoff_strategy": "none"},
  "cache_policy": {"cacheable": true},
  "error_codes": ["HTML_VALIDATION_FAILED"],
  "human_review_conditions": [],
  "estimated_cost_class": "free"
}
```

## Agent 17 — PDF Renderer

```json
{
  "name": "pdf_renderer",
  "purpose": "Convert HTML to A4 PDF with footer, page numbers via Playwright",
  "input_schema": "render/html/*.html + lession_id",
  "output_schema": "outputs/[lession_id]/*.pdf",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "playwright_chromium",
  "fallback_engines": ["weasyprint"],
  "premium_llm_allowed": false,
  "preconditions": ["HTML files exist", "Playwright browsers installed"],
  "postconditions": ["3 PDFs created", "each PDF > 0 bytes"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 2, "backoff_strategy": "linear", "retry_on": ["PDF_RENDER_FAILED"]},
  "cache_policy": {"cacheable": true, "cache_key_components": ["html_checksums"]},
  "error_codes": ["PDF_RENDER_FAILED"],
  "human_review_conditions": [],
  "estimated_cost_class": "free"
}
```

## Agent 18 — PDF Visual QA

```json
{
  "name": "pdf_visual_qa",
  "purpose": "Inspect rendered PDFs for A4 compliance, footer, overflow, blank pages",
  "input_schema": "rendered PDFs + lession_id",
  "output_schema": "qa/visual-qa-report.json (schemas/qa-report.schema.json)",
  "execution_class": "DETERMINISTIC",
  "preferred_engine": "pymupdf",
  "fallback_engines": [],
  "premium_llm_allowed": false,
  "preconditions": ["PDFs exist"],
  "postconditions": ["QA report generated"],
  "quality_thresholds": {},
  "retry_policy": {"max_retries": 0, "backoff_strategy": "none"},
  "cache_policy": {"cacheable": false},
  "error_codes": ["PDF_PAGE_OVERFLOW", "PDF_ASSET_MISSING", "FOOTER_INVALID"],
  "human_review_conditions": ["QA status is FAIL"],
  "estimated_cost_class": "free"
}
```
