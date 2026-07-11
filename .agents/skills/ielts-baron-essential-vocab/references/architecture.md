# Pipeline Architecture

## Overview

The `ielts-baron-essential-vocab` skill uses a 20-stage modular pipeline.
Each stage is independent, cacheable, and re-runnable.

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                              │
│  (run_pipeline.py — control plane, dispatch, state management)  │
└───────────┬─────────────────────────────────────────────────────┘
            │
  ┌─────────▼──────────┐
  │ Agent 00            │  Request Intake & Input Normalizer
  │ Agent 00B           │  Execution & Model Router
  └─────────┬──────────┘
            │
  ┌─────────▼──────────┐
  │ Agent 01            │  Source Identity & Cache Resolver
  │ Agent 02            │  Source Acquisition
  └─────────┬──────────┘
            │
  ┌─────────▼──────────┐    ┌──────────────────────┐
  │ Agent 03            │───▶│ PDF Structure Analyzer│
  │ Agent 04            │───▶│ Text & Asset Extractor│
  └─────────┬──────────┘    └──────────────────────┘
            │
  ┌─────────▼──────────┐    HITL Checkpoint B
  │ Agent 05            │  Unit/Topic Locator
  │ Agent 06            │  Source Canonicalizer
  │ Agent 07            │  Grounding & Fidelity Validator
  └─────────┬──────────┘
            │
  ┌─────────▼──────────┐    HITL Checkpoint D
  │ Agent 08            │  Reading Level Assessor  (PREMIUM_LLM)
  │ Agent 09            │  Lesson Identity Manager (DETERMINISTIC)
  └─────────┬──────────┘
            │
  ┌─────────▼──────────┐
  │ Agent 10            │  Vocabulary Knowledge Builder
  │ Agent 11            │  Grammar & Strategy Analyst (PREMIUM_LLM)
  │ Agent 12            │  Daily Practice Composer
  │ Agent 13            │  Answer Key & Explanation Builder (PREMIUM_LLM)
  └─────────┬──────────┘
            │
  ┌─────────▼──────────┐    HITL Checkpoint E
  │ Agent 14            │  Content QA Agent
  └─────────┬──────────┘
            │
  ┌─────────▼──────────┐
  │ Agent 15            │  Document Model Builder
  │ Agent 16            │  HTML Renderer (DETERMINISTIC)
  │ Agent 17            │  PDF Renderer  (DETERMINISTIC)
  └─────────┬──────────┘
            │
  ┌─────────▼──────────┐    HITL Checkpoint F
  │ Agent 18            │  PDF Visual QA
  └────────────────────┘
```

## Stage Dependencies

Each stage depends only on its predecessor's output artifacts.
If upstream artifacts are valid and cached, downstream stages can skip re-execution.

## Data Flow

```
Source PDF → extraction/ → units/ → analysis/ → lessons/ → render/ → outputs/
```

Intermediate data is stored under `.cache/ielts-baron-essential-vocab/[unique_source_id]/`.
Final outputs go to `outputs/ielts-baron-essential-vocab/[lession_id]/`.

## Execution Classes

| Class | Description | Cost | Examples |
|-------|------------|------|----------|
| DETERMINISTIC | Pure code, no ML | Free | file I/O, hashing, Jinja2, regex |
| LOCAL_MODEL | Local ML model | Free | OCR, POS tagging, embeddings |
| LOW_COST_LLM | Cheap API model | Low | draft explanations, grouping |
| PREMIUM_LLM | Reasoning model | Medium | CEFR assessment, grammar analysis |
| HUMAN_REQUIRED | Human decision | N/A | checkpoint approvals |
