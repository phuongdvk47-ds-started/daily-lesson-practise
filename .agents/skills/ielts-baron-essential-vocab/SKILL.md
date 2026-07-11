---
name: ielts-baron-essential-vocab
description: create source-grounded IELTS reading, vocabulary, grammar, and answer-key practice booklets from Barron-style PDF units using a modular cached pipeline, specialized sub-agents, human review checkpoints, CEFR and IELTS level assessment, provenance validation, deterministic local processing, cost-aware model routing, and print-ready A4 PDF rendering. use when a user provides an IELTS or Barron PDF, Google Drive document, unit number, topic, or reading passage and requests printable daily practice, vocabulary analysis, grammar guidance, detailed answers, cached reruns, or PDF regeneration.
---

# IELTS Barron Essential Vocab — Orchestrator

## Core Principle

Use a **modular cached pipeline**. Never run the full workflow in one monolithic prompt.
Each pipeline stage has a single responsibility, explicit input/output schemas, cache policy,
quality gate, and execution class. The orchestrator is the control plane — it dispatches,
validates, and never performs extraction, analysis, or rendering itself.

## Accepted Inputs

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| `source` | **yes** | — | Local path, uploaded file, or public Google Drive URL |
| `unit` | no | — | Unit name or number (e.g. "Unit 1") |
| `topic` | no | — | Topic name (e.g. "Bird Migration") |
| `day` | no | 1 | Day number for lesson ID |
| `human-review` | no | true | Enable HITL checkpoints |
| `force-reextract` | no | false | Force re-extraction from source |
| `force-rebuild-content` | no | false | Force content regeneration |
| `force-rerender` | no | false | Force HTML/PDF re-render only |

## Pipeline Stages

```
Agent 00  → Request Intake & Input Normalizer
Agent 00B → Execution & Model Router
Agent 01  → Source Identity & Cache Resolver
Agent 02  → Source Acquisition
Agent 03  → PDF Structure Analyzer
Agent 04  → Text & Asset Extractor
Agent 05  → Unit/Topic Locator            [HITL Checkpoint B]
Agent 06  → Source Canonicalizer
Agent 07  → Grounding & Fidelity Validator
Agent 08  → Reading Level Assessor        [HITL Checkpoint D]
Agent 09  → Lesson Identity Manager
Agent 10  → Vocabulary Knowledge Builder
Agent 11  → Grammar & Strategy Analyst
Agent 12  → Daily Practice Composer
Agent 13  → Answer Key & Explanation Builder
Agent 14  → Content QA Agent              [HITL Checkpoint E]
Agent 15  → Document Model Builder
Agent 16  → HTML Renderer
Agent 17  → PDF Renderer
Agent 18  → PDF Visual QA                 [HITL Checkpoint F]
```

Full agent contracts: [pipeline-contracts.md](references/pipeline-contracts.md)
Agent responsibilities: [sub-agents.md](references/sub-agents.md)

## Execution Model — Deterministic-First, Local-First, Cost-Aware

Every task is classified into an execution class before dispatch:

```
DETERMINISTIC → LOCAL_MODEL → LOW_COST_LLM → PREMIUM_LLM → HUMAN_REQUIRED
```

**Rule**: Use the cheapest engine that reliably passes the required quality gate.

- **DETERMINISTIC**: file I/O, hashing, JSON schema, Jinja2, regex, PDF render
- **LOCAL_MODEL**: OCR, heading detection, POS tagging, keyword extraction
- **LOW_COST_LLM**: OCR normalization, vocabulary grouping, draft explanations
- **PREMIUM_LLM**: CEFR assessment, grammar analysis, answer explanations, ambiguity
- **HUMAN_REQUIRED**: checkpoint decisions, override, final approval

Routing policy: [execution-routing.md](references/execution-routing.md)
Model selection: [model-selection-policy.md](references/model-selection-policy.md)
Escalation chain: [model-escalation.md](references/model-escalation.md)
Cost guardrails: [cost-quality-policy.md](references/cost-quality-policy.md)
Local stack: [local-open-source-stack.md](references/local-open-source-stack.md)

## Cache-First Execution

Before running any stage, check:

1. Does the output artifact exist?
2. Does the input checksum match?
3. Is the stage version unchanged?
4. Does the output pass schema validation?
5. Is the status COMPLETE?

If all pass → **skip from cache**. Otherwise → run the stage.

Cache root: `.cache/ielts-baron-essential-vocab/[unique_source_id]/`
Lesson cache: `.cache/.../lessons/[lession_id]/`

Cache strategy: [cache-and-retry.md](references/cache-and-retry.md)

## Human-in-the-Loop Checkpoints

| Checkpoint | Trigger | What is shown |
|------------|---------|---------------|
| A — Source Selection | GDrive folder, multi-file, non-PDF | File list, preview |
| B — Unit Confirmation | Multiple candidates, low confidence | Candidates, page ranges, headings |
| C — Extraction Review | Low OCR, missing text, table errors | Extraction report, warnings |
| D — Level Approval | Level assessed | CEFR, IELTS Band, evidence |
| E — Content Preview | Content assembled | Outlines of all sections |
| F — Final PDF Approval | PDFs rendered | File paths, page counts, QA results |

All decisions logged to `human-decisions.json`.
Workflow details: [human-review-workflow.md](references/human-review-workflow.md)

## Anti-Hallucination & Provenance

Every content block must carry a classification:

```
SOURCE_EXTRACTED | SOURCE_NORMALIZED | DERIVED_FROM_SOURCE
ENRICHED_CONTENT | EXTERNAL_REFERENCE | MODEL_GENERATED_DRAFT | UNRESOLVED
```

- Source-grounded claims require: source_id, page, block_id, extraction method, confidence
- Missing data → `UNRESOLVED` + human review if critical
- Never fabricate IPA, definitions, Answer Keys, or URLs
- Keep raw extraction; create normalized copy separately

Rules: [anti-hallucination.md](references/anti-hallucination.md)

## Quality Gates

| Gate | Validates |
|------|-----------|
| 0 — Execution Policy | Task classified, engine allowed, budget OK |
| 1 — Source Integrity | Checksum valid, source accessible |
| 2 — Extraction Integrity | Pages extracted, assets accounted |
| 3 — Unit Integrity | Target identified, page range approved |
| 4 — Provenance Integrity | All claims referenced, no orphans |
| 4B — Model Output | Schema valid, confidence sufficient |
| 5 — Content Integrity | No answer leakage, labels correct |
| 6 — Render Integrity | A4 valid, footer correct, no overflow |
| 6B — Cost/Resource | No unnecessary premium calls |
| 7 — Final Delivery | PDFs exist, manifest valid, QA PASS |

Details: [quality-gates.md](references/quality-gates.md)

## Output Structure

```
outputs/ielts-baron-essential-vocab/[lession_id]/
├── daily-practice.pdf
├── vocabulary-grammar.pdf
├── answer-key.pdf
├── complete-booklet.pdf          (optional)
├── lesson-manifest.json
├── provenance-report.json
├── qa-report.json
└── render/
    └── html/
```

## CLI Reference

### Full pipeline run
```bash
python scripts/run_pipeline.py \
  --source "<path-or-url>" \
  --unit "Unit 1" --topic "Bird Migration" --day 1 \
  --human-review
```

### Re-render only (no re-extraction)
```bash
python scripts/run_pipeline.py \
  --lesson-id "LSN-001-B2-A7K9P2QX" \
  --from-stage html-render \
  --force-rerender
```

### Re-OCR a single page
```bash
python scripts/run_pipeline.py \
  --source "<source>" \
  --from-stage extract \
  --page 18 \
  --force-page-reextract
```

### Resume from last completed stage
```bash
python scripts/run_pipeline.py --resume --lesson-id "LSN-001-B2-A7K9P2QX"
```

### All CLI flags
```
--source              PDF path or Google Drive URL
--unit                Target unit name/number
--topic               Target topic name
--day                 Day number (default: 1)
--human-review        Enable HITL checkpoints
--resume              Resume from last completed stage
--from-stage          Start from a specific stage
--to-stage            Stop after a specific stage
--force-reextract     Force re-extraction
--force-rebuild-content  Force content rebuild
--force-rerender      Force re-render only
--skip-human-review   Skip all HITL checkpoints
--lesson-id           Existing lesson ID for reruns
--output-root         Custom output directory
--cache-root          Custom cache directory
--page                Target specific page (for re-OCR)
--force-page-reextract  Force re-extract specific page
```

## Error Codes

All error codes with severity, retry policy, and HITL requirements:
[error-codes.md](references/error-codes.md)

## Content Rules

- Vocabulary: [vocabulary-rules.md](references/vocabulary-rules.md)
- Grammar: [grammar-rules.md](references/grammar-rules.md)
- Answers: [answer-explanation-rules.md](references/answer-explanation-rules.md)
- CEFR/IELTS: [cefr-ielts-assessment.md](references/cefr-ielts-assessment.md)
- PDF layout: [pdf-layout-spec.md](references/pdf-layout-spec.md)

## Recovery

If the pipeline fails mid-run:

1. Check `state/pipeline-state.json` for last completed stage
2. Use `--resume` to continue from that point
3. Use `--from-stage <name>` to restart a specific stage
4. Use `--force-rerender` if only rendering failed
5. Never re-extract if upstream artifacts are valid

Stage states: `PENDING | RUNNING | COMPLETE | FAILED | BLOCKED | WAITING_FOR_HUMAN | STALE | SKIPPED_FROM_CACHE`
