---
name: ielts-daily-reading-writing
description: create modular daily IELTS practice packs with separate source verification, reading, vocabulary, grammar, writing, answer, quality-control, and PDF export stages. Use when the user asks to generate IELTS daily practice, reading questions, grammar drills, writing tasks, Quizlet vocabulary, answer keys, cumulative review packs, or printable PDF packs for CEFR levels A1-C2.
---

# IELTS Daily Pack Orchestrator

## Core Principle
Use a modular pipeline. Do not generate the full IELTS pack in one monolithic response. Resolve inputs once, pass structured JSON between stages, validate the assembled `lesson_source.json`, then export PDFs from that JSON only.

## Accepted Inputs
Accept these parameters when provided:
- `Day`: date label such as `Day 20260625`; default to today's date in `YYYYMMDD`.
- `Topic`: topic name; default by selecting a level-appropriate topic from `references/topic-bank.md`.
- `Level`: one of `A1`, `A2`, `B1`, `B2`, `C1`, `C2`; default `A2`.
- `Number of IELTS Reading Questions`: default `13`.
- `Number of Vocabulary Words`: default `20`.
- `Number of Grammar Questions`: default `30`.
- `Number of Writing Practice`: default `5`.
- Optional prior history: previous daily topics, learner errors, weak skills, or past outputs.
- Optional cumulative review request.

Normalize common variants: `Writting` means `Writing`; `IELTS Reading Questions` means reading question count.

## High-Level Workflow for Daily Pack
1. Resolve inputs and defaults.
2. Load `references/orchestrator.md`.
3. Check lesson history and anti-duplication rules. Find prior same-level lesson for vocabulary recycling.
4. Run **Source Research Agent** using `references/source-research-agent.md`. If source verification fails, stop.
5. Run **Reading Agent** using `references/reading-agent.md`.
6. Run **Vocabulary Agent** using `references/vocabulary-agent.md`.
7. Run **Grammar Agent** using `references/grammar-agent.md`.
8. Run **Writing Agent** using `references/writing-agent.md`.
9. Run **Answer Agent** using `references/answer-agent.md`.
10. Assemble the complete payload into `lesson_source.json` according to `references/output-schema.md`.
11. Run **Quality Control Agent** using `references/quality-control-agent.md`.
12. If QC fails, regenerate the failed section(s) only. Rerun QC.
13. Rerun validation script: `python scripts/validate_lesson_json.py [lesson_source.json]`.
14. If validation passes, invoke compilation script: `python scripts/export_daily_pack.py [lesson_source.json]`.

## High-Level Workflow for Cumulative Review Pack
1. Identify target days and retrieve recent level lessons from `lesson_history.txt`.
2. Run aggregation script: `python scripts/prepare_review_inputs.py --level [Level] [--days [Days]]`.
3. Generate review reading passage and questions based on aggregated topics.
4. Generate grammar drill questions based on aggregated grammar targets.
5. Generate writing tasks testing those targets.
6. Assemble review JSON payload and run QC.
7. If QC passes, compile review PDFs: `python scripts/export_review_pack.py [review JSON]`.

## Hard Rules
- Only **Source Research Agent** may search or verify web sources.
- Do not invent URLs, titles, authors, publication dates, facts, or source details. If no verified source exists, stop and report a source gap.
- Every Sub-Agent must return structured JSON compatible with `references/output-schema.md`.
- Do not export PDF from free-form markdown. PDF files must be compiled only from `lesson_source.json`.
- If one section fails QC, regenerate ONLY that section. Do not regenerate the whole pack unless the source, level, or topic changes.
- Preserve the existing output folder contract: `/outputs/ielts-daily-reading-writing/[Day]-[Level]/{lsn/, aws/, quizlet}`.
- Preserve spelling `Practise.pdf`.
- Preserve history logging in `/outputs/ielts-daily-reading-writing/lesson_history.txt`.
- Preserve spaced repetition vocabulary recycling.

## Reference Loading Map
Load only the relevant reference file for the current stage:
- Orchestration & Review: `references/orchestrator.md`
- Source verification: `references/source-research-agent.md`
- Reading: `references/reading-agent.md`
- Vocabulary: `references/vocabulary-agent.md`
- Grammar: `references/grammar-agent.md`
- Writing: `references/writing-agent.md`
- Answers: `references/answer-agent.md`
- QC: `references/quality-control-agent.md`
- JSON Schema contract: `references/output-schema.md`
- Formatting & Layout: `references/output-template.md`
- Topic selection: `references/topic-bank.md`
- Grammar targets: `references/grammar-by-level.md`
