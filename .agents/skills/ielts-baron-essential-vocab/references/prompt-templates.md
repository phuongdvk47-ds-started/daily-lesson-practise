# Prompt Templates

## Overview
This document defines the prompt template conventions for all LLM-powered stages. Each prompt template is versioned and cached to ensure reproducibility and cost control.

## Prompt Versioning
- Each prompt template has a version string: `v1.0.0`, `v1.1.0`, etc.
- Version changes invalidate model cache entries
- Version is included in cache key computation

## Template Variables
Templates use `{{variable}}` syntax for substitution:
- `{{reading_passage}}` — The reading passage text
- `{{questions_json}}` — Questions in JSON format
- `{{answer_key_json}}` — Answer key in JSON format
- `{{vocabulary_json}}` — Vocabulary items in JSON format
- `{{cefr_level}}` — Target CEFR level
- `{{unit_name}}` — Unit name
- `{{topic}}` — Unit topic

## System Instructions (Common Prefix)
All LLM prompts include:
```
You are an IELTS Academic Content Specialist. Your role is to analyze source material with precision and honesty. Follow these rules:
1. Never fabricate information. If data is missing, report it as UNRESOLVED.
2. Always cite specific evidence from the provided text.
3. Use the exact JSON schema provided in the output specification.
4. Classify all content using the content classification system.
5. Provide confidence scores for subjective assessments.
```

## Token Budget Enforcement
- Input context is trimmed to fit within the task's token budget
- Lazy loading: only relevant sections are included
- Context window usage is logged in execution-metadata.json

## Output Schema Enforcement
- All LLM outputs must conform to the specified JSON schema
- Schema validation happens immediately after generation
- Failed validation triggers retry or escalation
