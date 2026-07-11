---
name: ielts-daily-reading-writing
description: create modular daily IELTS practice packs with deep reading, deep grammar, source verification, reading, vocabulary, grammar, writing, answer-key reasoning, quality-control, and PDF export stages. Use when the user asks to generate IELTS daily practice, reading questions, grammar drills, writing tasks, Quizlet vocabulary, answer keys, cumulative review packs, or printable PDF packs for CEFR levels A1-C2 including A1+, A2+, B1+, B2+, and C1+ bridge levels.
---

# IELTS Daily Pack Orchestrator

## Core Principle
Use a modular pipeline. Do not generate the full IELTS pack in one monolithic response. Resolve inputs once, pass structured JSON between stages, validate the assembled `lesson_source.json` using the validator script, then export PDFs from that JSON only.

## Accepted Inputs
Accept these parameters when provided:
- `Day`: date label such as `Day 20260625`; default to `current_date` from the active environment/local timezone in `YYYYMMDD`.
- `Topic`: topic name; default by running `scripts/select_daily_inputs.py` or selecting a level-appropriate topic from `references/topic-bank.md` while respecting history windows.
- `Level`: one of `A1`, `A1+`, `A2`, `A2+`, `B1`, `B1+`, `B2`, `B2+`, `C1`, `C1+`, `C2`; default `A2`.
- `Number of IELTS Reading Questions`: default `13`.
- `Number of Vocabulary Words`: default `20`.
- `Number of Grammar Questions`: default `30`.
- `Number of Writing Practice`: default `5`.
- Optional prior history: previous daily topics, learner errors, weak skills, or past outputs.
- Optional cumulative review request.

Normalize common variants: `Writting` means `Writing`; `IELTS Reading Questions` means reading question count.

## Execution Model
Each named Sub-Agent is a pipeline stage, not a free-form chat persona. For each stage:
1. Load only the relevant reference file listed in the Reference Loading Map.
2. Pass the current structured lesson payload plus that stage's required inputs.
3. Return only the JSON section(s) owned by that stage, compatible with `references/output-schema.md`.
4. Merge revised sections into `lesson_source.json` without rewriting unrelated sections.

## High-Level Workflow for Daily Pack
1. Resolve inputs and defaults. If topic or history context is missing, use `scripts/select_daily_inputs.py` and `outputs/ielts-daily-reading-writing/lesson_history.txt`.
2. Load `references/orchestrator.md`.
3. Check lesson history and anti-duplication rules. Find prior same-level lesson for vocabulary recycling.
4. Run **Source Research Agent** using `references/source-research-agent.md`. If source verification fails, stop.
5. Run **Reading Agent** using `references/reading-agent.md`, `references/deep-question-blueprint.md`, and `references/deep-reading-generation-rules.md`. Ensure the Reading blueprint is created before questions, all questions have verbatim evidence quotes, and the level-specific deep-reading ratios are met.
6. Run **Vocabulary Agent** using `references/vocabulary-agent.md`.
7. Run **Grammar Agent** using `references/grammar-agent.md`, `references/deep-question-blueprint.md`, and `references/deep-grammar-generation-rules.md`. Ensure the Grammar blueprint is created before questions, no hardcoded headings appear, and transformations preserve meaning.
8. Run **Writing Agent** using `references/writing-agent.md`. Ensure daily topic relevance.
9. Run **Answer Agent** using `references/answer-agent.md` and `references/deep-answer-key-rules.md`.
10. Assemble the complete payload into `lesson_source.json` according to `references/output-schema.md`.
11. Run **Quality Control Agent** using `references/quality-control-agent.md` and `references/regeneration-quality-gates.md`.
12. If QC fails, set `execution.pipeline_status` to `qc_failed`, increment the relevant `revision_attempts` counter, regenerate the failed section(s) only, and rerun QC.
13. Stop and report unresolved challenges if a section reaches the maximum revision attempts listed under Loop Specific Hard Rules.
14. When content QC passes and no high/critical challenge remains open, set `execution.pipeline_status` to `qc_passed`.
15. Rerun validation script: `python scripts/validate_lesson_json.py [lesson_source.json]`.
16. If validation passes, invoke compilation script: `python scripts/export_daily_pack.py [lesson_source.json]`.
17. Treat the lesson as final only after post-render PDF QC passes.

## High-Level Workflow for Cumulative Review Pack
1. Identify target days and retrieve recent level lessons from `outputs/ielts-daily-reading-writing/lesson_history.txt`.
2. Run aggregation script: `python scripts/prepare_review_inputs.py --level [Level] [--days [Days]]`.
3. Generate review reading passage and questions based on aggregated topics.
4. Generate grammar drill questions based on aggregated grammar targets.
5. Generate writing tasks testing those targets.
6. Assemble review JSON payload according to `references/output-schema.md` and run QC.
7. If QC fails, regenerate only the failed section(s), respecting the same revision attempt limits as daily packs.
8. When QC passes, set `execution.pipeline_status` to `qc_passed` and run `python scripts/validate_lesson_json.py [review JSON]`.
9. If validation passes, compile review PDFs: `python scripts/export_review_pack.py [review JSON]`.
10. Treat the review pack as final only after post-render PDF QC passes.

## Hard Rules
- Only **Source Research Agent** may search or verify web sources.
- Do not invent URLs, titles, authors, publication dates, facts, or source details. If no verified source exists, stop and report a source gap.
- Every Sub-Agent must return structured JSON compatible with `references/output-schema.md`.
- Reading and Grammar generation must create `reading_blueprint` and `grammar_blueprint` before writing the actual questions, then self-check every generated item against its blueprint.
- **JSON Validator Integration**: Do not export PDF from free-form markdown or unvalidated JSON. The compiler script will automatically run `validate_lesson_json.py` and reject compilation if any errors exist.
- If one section fails QC, regenerate ONLY that section. Do not regenerate the whole pack unless the source, level, or topic changes.
- Preserve the existing output folder contract relative to the repository root: `outputs/ielts-daily-reading-writing/[Day]-[Level]/{lsn/, aws/, quizlet}`.
- Preserve spelling `Practise.pdf`.
- Preserve history logging in `outputs/ielts-daily-reading-writing/lesson_history.txt`.
- Preserve spaced repetition vocabulary recycling.

## Compiler and Exporter Robustness Rules

To prevent rendering omissions, alignment mismatches, and parsing failures during PDF export:
- **Forced Markdown Cache Regeneration**: The compilation script must always pop and regenerate intermediate markdown fields (`practice_markdown`, `vocabulary_grammar_markdown`, `answers_markdown`, `quizlet_markdown`) when compiling structured JSON payloads, rather than reusing cached fields.
- **Robust Table Pipe Splitting**: Markdown table rows must be split using negative lookbehind `re.split(r'(?<!\\)\|', line)` to support escaped pipes (`\|`) within cell contents (such as inside embedded sub-tables).
- **Embedded Table Preservation**: Do not use simple substring checks like `"---" in line` to skip table headers, as this will incorrectly skip rows containing embedded markdown tables. Use a strict pattern match like `re.match(r'^\|[\s\-|\:]+$', line)` instead.
- **ASCII-only Heading Cleansing**: When cleaning redundant task type headings from prompt texts, use ASCII-only patterns (e.g., `[a-zA-Z\s\-]+` instead of `[\w\s\-]+`) to prevent matching and stripping Unicode Vietnamese prompts.
- **Writing Level Header Injection**: The structured JSON converter (`convert_json_to_markdown_fields`) must write the `Reading: {level}` and `Writing: {w_level}` lines at the very beginning of `practice_markdown` so that the compiler correctly parses and renders the Writing level in the Practice sheet header instead of defaulting to `A1`.
- **Dynamic Vocabulary Table Numbering**: The compiler must dynamically index the vocabulary tables (Core, Topic, Phrases/Collocations, and Recycled) in the Materials sheet to prevent sequence gaps (such as skipping Table 2.2) when a table is empty.
- **Review Bridge Rendering**: The compiler must include `"review bridge"` in the major section heading keywords to split it correctly. In student sheets, it must render the Review Bridge prompts with writing lines while completely hiding answers and explanations. In the teacher Answer Key, it must render the prompts along with their correct answers and explanations.
- **Writing Formatting and Key Consistency**:
  - `useful_language` and `success_criteria` must be lists/arrays of strings, not comma-separated strings.
  - Prompts for Task 2 (Sentence Combining) must use bullet points (`-`) instead of numbered lists to avoid inserting blank lines in between.
  - `visual_data.type` for tables must be exactly `"markdown_table"`.
  - SVG visual content must be flattened to a single continuous line to prevent `<br>` injection.
  - Paragraph writing tasks (e.g. Task 5) must specify `write X-Y sentences` to scale up the printed lines.
  - Warm-up section instruction must be `*Answer the following questions in English:*` (with asterisks) and questions must be in English only.
  - Answers keys must use the precise keys mapping: `writing_guidance` (`task_id`, `model_answer`, `guidance_vi`, `self_checklist`), `review_bridge` (`id`, `prompt`, `correct_answer`, `rationale_vi`).
- **Reading Options Prefixes**: Multiple-choice options in the JSON payload must not contain manual prefixes like `A. `, `B. `, etc., as the compiler automatically pre-formats and prepends them.
- **Writing Task Sub-Item Lines**: The compiler must support lists/bullet points (numbered `1.`, lettered `a)`, and bulleted `-`, `*`) as sub-items inside writing task prompts, drawing writing lines beneath each sub-item.
- **Table-Based Writing Task Spacing**: If a writing task prompt or visual data contains a table, skip rendering duplicate trailing `Answer:` lines or empty writing lines at the bottom of the block only if the table contains fill-in-the-blank placeholders (like `.......`, `___`, or `[Fill`). For read-only data tables without placeholders, render the required writing lines below the table block for student comparisons and essays.
- **Suggested Answers Table Rendering**: Suggested model answers for writing tasks containing tables must not be wrapped in markdown blockquotes (`>`) so the compiler can correctly parse and output them as HTML tables in the answer key.
- **Writing Line Fallback**: The compiler must inspect the target length (e.g. `3 sentences`) when computing required student answer spaces to ensure at least 3-4 lines are rendered for paragraph-based tasks when English instructions are missing.
- **Responsive MC Option Alignment**: Multiple-choice options must be dynamically aligned to 1, 2, or 4 columns based on the max and total text lengths of the options to conserve space and save paper.
- **Compact Writing Space Layout**: Writing prompt items and lines must be structured using HTML block divs joined by newlines rather than using redundant `<br>` tags, which prevents wasteful blank vertical gaps.
- **HTML/SVG Protection**: In writing task formatting, skip markdown inline replacement for lines that contain HTML/SVG markup tags to prevent corruption of rendered charts.

## Human-in-the-loop and Agent Review Loop
Before finalizing any daily practice pack, use the review workflow described in:
- `references/human-in-loop.md`
- `references/agent-review-loop.md`
- `references/quality-control-agent.md`

The Skill supports two execution modes:

### Auto Mode
Use Auto Mode by default unless the user explicitly asks to review intermediate outputs.
In Auto Mode:
1. Run all Sub-Agents.
2. Run Agent Review Loop internally.
3. Let QC Agent challenge and critique weak sections.
4. Regenerate only failed sections.
5. Export PDF only after QC passes.
6. Return final files and QC report.

### Review Mode
Use Review Mode when the user asks to approve sources, approve outline, review questions, review vocabulary, review grammar, review writing tasks, or check before PDF export.
In Review Mode:
1. Stop at human checkpoints.
2. Present compact review summaries.
3. Ask for user approval or correction.
4. Continue only after user approval.
5. Preserve the user's decision in `lesson_source.json`.

### Loop Specific Hard Rules
- QC Agent must be allowed to challenge Reading, Vocabulary, Grammar, Writing, and Answer Agent outputs.
- Any challenged Sub-Agent must revise only the challenged section.
- Do not regenerate the whole pack unless source, level, topic, or user direction changes.
- If QC detects ambiguity, multiple possible answers, missing evidence, missing visual data, insufficient answer space, or vocabulary imbalance, the relevant agent must revise its output.
- If QC detects the fail conditions in `references/regeneration-quality-gates.md`, route the challenge to the responsible section and regenerate only that item or section.
- PDF export must not run until content QC status is `pass`, `execution.pipeline_status` is `qc_passed`, and `validate_lesson_json.py` passes without errors.
- Maximum revision attempts: source 2, reading 3, vocabulary 2, grammar 3, writing 2, answers 2, PDF layout 2.
- If any section reaches its maximum revision attempts, stop Auto Mode, keep unresolved challenges open, and report the blocker instead of silently accepting it.

## Post-Render PDF Quality Control

After generating PDFs, run Post-Render PDF QC using `references/post-render-pdf-qc.md` and `scripts/validate_rendered_pdf.py`.
The automated script validates the Practice PDF against `lesson_source.json`; use the post-render checklist to inspect every exported PDF for missing content or layout regressions.

A lesson is not final until:
1. `lesson_source.json` validation passes.
2. Content QC passes.
3. PDFs are exported.
4. Rendered PDF QC passes.
5. No critical/high post-render issues remain.

Do not mark pipeline as `exported` or final if the rendered PDF is missing:
- Multiple Choice options
- Grammar blanks
- computed section ranges
- correct Time Allowed
- required writing spaces
- charts/visual data
- footer metadata

If rendered PDF QC fails, fix the compiler/template only when lesson_source.json is correct. Do not regenerate lesson content unless the JSON itself is wrong.

## Zero-Tolerance Logic Rule

Question logic errors are critical failures.

The Skill must never finalize, export, or mark QC as passed if any question has:
- more than one naturally valid answer
- insufficient context to determine the correct answer
- a correct option that does not produce a complete grammatical sentence
- missing punctuation needed to complete the sentence
- hidden assumptions that only the author knows
- mismatch between instruction and expected answer
- answer key that is correct only under one unstated interpretation

Any such issue must be marked as:
`challenge_type: "logic_error"`
with severity:
`critical`

The responsible agent must revise the item before PDF export.

No high-level or critical logic challenge may be accepted silently in Auto Mode.

## Zero-Tolerance Correct-the-Error Rule

For any question whose instruction is `Correct the error`, `Correct the mistake`, `Error correction`, or equivalent:
- The original sentence must contain exactly one clear target error.
- The correct answer must be different from the original sentence.
- The explanation must refer to an error that actually appears in the original sentence.
- If the original sentence is already grammatical, the item is invalid.
- If the correct answer is identical to the original sentence, the item is invalid.
- If the explanation mentions a word or structure that is not present in the original sentence, the item is invalid.
- These failures are critical logic errors.

No lesson may be marked `qc_passed`, `exported`, or final if any Correct-the-error item fails this rule.

## Reference Loading Map
Load only the relevant reference file for the current stage:
- Orchestration & Review: `references/orchestrator.md`
- Human checkpoints: `references/human-in-loop.md`
- Agent critique loops: `references/agent-review-loop.md`
- Core pedagogical targets: `references/pedagogical-constraints.md`
- Source verification: `references/source-research-agent.md`
- Reading: `references/reading-agent.md`
- Vocabulary: `references/vocabulary-agent.md`
- Grammar: `references/grammar-agent.md`
- Deep Question Blueprint: `references/deep-question-blueprint.md`
- Deep Reading Generation: `references/deep-reading-generation-rules.md`
- Deep Grammar Generation: `references/deep-grammar-generation-rules.md`
- Deep Grammar Rules: `references/deep-grammar-rules.md`
- Writing: `references/writing-agent.md`
- Answers: `references/answer-agent.md`
- Deep Answer Key Rules: `references/deep-answer-key-rules.md`
- QC: `references/quality-control-agent.md`
- Deep Reading QC: `references/deep-reading-qc.md`
- Regeneration Quality Gates: `references/regeneration-quality-gates.md`
- Post-render PDF QC: `references/post-render-pdf-qc.md`
- Blueprint Rules: `references/level-blueprint-rules.md`
- Daily IELTS Checker: `references/daily-ielts-checker.md`
- JSON Schema contract: `references/output-schema.md`
- Formatting & Layout: `references/output-template.md`
- Topic selection: `references/topic-bank.md`
- Grammar targets: `references/grammar-by-level.md`
