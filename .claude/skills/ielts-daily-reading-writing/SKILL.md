---
name: ielts-daily-reading-writing
description: >-
  Create modular daily IELTS practice packs with deep reading, deep grammar,
  source verification, reading, vocabulary, grammar, writing, answer-key
  reasoning, quality-control, and PDF export stages. Use when the user asks to
  generate IELTS daily practice, reading questions, grammar drills, writing
  tasks, Quizlet vocabulary, answer keys, cumulative review packs, or printable
  PDF packs for CEFR levels A1-C2 including A1+, A2+, B1+, B2+, and C1+ bridge
  levels. Invoke with /ielts-daily-reading-writing.
---

# IELTS Daily Pack Orchestrator (Claude Code)

This is a Claude Code port of the multi-sub-agent, human-in-the-loop IELTS
daily-pack skill. The pipeline runs as a modular set of stages. Each stage is a
dedicated **sub-agent** (defined in `.claude/agents/ielts-*.md`) that you, the
orchestrator (main agent), spawn with the Agent tool, collect its JSON output,
merge into `lesson_source.json`, validate, and finally export to PDF.

Sub-agents (see `.claude/agents/`):

| Sub-agent file | `subagent_type` | Owns section |
|---|---|---|
| `ielts-source-research.md` | `ielts-source-research` | `source` |
| `ielts-reading.md` | `ielts-reading` | `reading` |
| `ielts-vocabulary.md` | `ielts-vocabulary` | `vocabulary` |
| `ielts-grammar.md` | `ielts-grammar` | `grammar` |
| `ielts-writing.md` | `ielts-writing` | `writing` |
| `ielts-answer.md` | `ielts-answer` | `answers` |
| `ielts-quality-control.md` | `ielts-quality-control` | QC report |

All supporting reference docs live in
`.claude/skills/ielts-daily-reading-writing/references/` and scripts in
`.claude/skills/ielts-daily-reading-writing/scripts/`.

## Core Principle
Use a modular pipeline. Do **not** generate the full IELTS pack in one
monolithic response. Resolve inputs once, pass structured JSON between stages,
validate the assembled `lesson_source.json` with the validator script, then
export PDFs from that JSON only.

## Accepted Inputs
Accept these parameters when provided:
- `Day`: date label such as `Day 20260625`; default to today's date in `YYYYMMDD`.
- `Topic`: topic name; default by running `select_daily_inputs.py` or selecting a
  level-appropriate topic from `references/topic-bank.md` while respecting history windows.
- `Reading Level`: one of `A1`, `A1+`, `A2`, `A2+`, `B1`, `B1+`, `B2`, `B2+`,
  `C1`, `C1+`, `C2`; default `A2`. Also accepted as `Level` for backwards compatibility.
- `Grammar Level` / `Writing Level` / `Vocabulary Level`: same set; each defaults to Reading Level.
- `Number of IELTS Reading Questions`: default `13`.
- `Number of Vocabulary Words`: default `20`.
- `Number of Grammar Questions`: default `30`.
- `Number of Writing Practice`: default `5`.
- Optional prior history: previous daily topics, learner errors, weak skills, or past outputs.
- Optional cumulative review request.

### Level Input Rules
**Single-level input** (e.g. `Level: A2`): set `reading_level = A2`; set
`grammar_level = writing_level = vocabulary_level = reading_level` (inherit).

**Split-level input** (e.g. `Reading Level: A2+, Writing Level: A1`): set each
skill level independently; any unspecified skill level inherits from `reading_level`.

**`lesson_meta` mapping** — always populate all four flat keys **and** the nested
`skill_level` dict:
```json
{
  "level": "<reading_level>",
  "reading_level": "<reading_level>",
  "grammar_level": "<grammar_level>",
  "writing_level": "<writing_level>",
  "vocabulary_level": "<vocabulary_level>",
  "skill_level": {
    "reading_level": "<reading_level>",
    "grammar_level": "<grammar_level>",
    "writing_level": "<writing_level>",
    "vocabulary_level": "<vocabulary_level>"
  }
}
```
The top-level `level` key must always equal `reading_level` (used for file naming and history tracking).

**PDF Header** — the compiler renders all four skill levels in the header:
```
(Level: Reading A2+ | Grammar A2 | Writing A1 | Vocab A2)
```
If all four levels are identical, a compact single-level form may be used:
```
(Level: A2)
```

Normalize common variants: `Writting` → `Writing`; `IELTS Reading Questions` →
reading question count; `Vocab Level` → `Vocabulary Level`; `Grammar` alone →
`Grammar Level`.

## Execution Model (Claude Code)
Each Sub-Agent is a pipeline stage, not a free-form chat persona. For each stage:
1. Read only the relevant reference file(s) listed in the Reference Loading Map.
2. Spawn the sub-agent with the Agent tool (`subagent_type` from the table above),
   passing the current structured inputs/upstream JSON via the prompt.
3. The sub-agent returns only the JSON section(s) it owns, compatible with
   `references/output-schema.md`.
4. Merge the returned section into `lesson_source.json` (Write the file after
   every stage) without rewriting unrelated sections.

**Temp Working Directory (mandatory):** Every data file, generated script
output, and temp artifact produced while running this skill MUST be written under:
`.temps/ielts-daily-reading-writing/<run_id>/`
where `<run_id>` is a unique id created once at run start:
`run_id = f"{day_part}-{level}-{uuid4().hex[:8]}"` (e.g. `20260713-A2+-a1b2c3d4`;
generate the 8-hex suffix with `python -c "import uuid;print(uuid.uuid4().hex[:8])"`).
Create it with `mkdir -p .temps/ielts-daily-reading-writing/<run_id>` — this is `TEMPDIR`.
Under `TEMPDIR` keep:
- `lesson_source.json` — the assembly-in-progress (overwritten after every stage).
- `stage_<section>.json` — each sub-agent's returned JSON fragment (traceability).
- `validate_report.txt`, `qc_pass_<N>.json`, rendered `*.html`, and any logs.
Do NOT scatter working files in the repo root or other folders. The FINAL exported
PDFs and the canonical `lesson_source.json` are written by the exporter into
`outputs/ielts-daily-reading-writing/[Day]-[Level]/` (the existing output
contract); only those final artifacts leave `.temps/`.

**Passing payloads to sub-agents:** Include the upstream JSON the stage needs
inline in the Agent prompt (e.g. pass `source` to Reading, `reading` to
Vocabulary/Grammar, `grammar_targets`+`vocabulary` to Writing, all sections to
Answer, full payload to QC). Sub-agents only have the `Read` tool (Source
Research also has `WebSearch`/`WebFetch`), so do file I/O on their behalf.

## High-Level Workflow for Daily Pack
1. Resolve inputs and defaults. If topic or history context is missing, run
   `python .claude/skills/ielts-daily-reading-writing/scripts/select_daily_inputs.py --level <L>`
   and consult `outputs/ielts-daily-reading-writing/lesson_history.txt`.
2. Read `references/orchestrator.md` and `references/pedagogical-constraints.md`.
3. Check lesson history and anti-duplication rules; find prior same-level lesson
   for vocabulary recycling (pick 3 words/phrases from its `Quizlet-Vocab`/`lesson_source.json`).
4. Spawn **ielts-source-research** (its body is `.claude/agents/ielts-source-research.md`).
   If source verification fails, stop and report a source gap.
5. Spawn **ielts-reading** (its body is `.claude/agents/ielts-reading.md`; it reads
   `references/deep-question-blueprint.md`, `references/deep-reading-generation-rules.md`,
   `references/level-blueprint-rules.md`). Ensure the reading blueprint is created
   before questions, all questions have verbatim evidence quotes, and level-specific
   deep-reading ratios are met.
6. Spawn **ielts-vocabulary** (its body is `.claude/agents/ielts-vocabulary.md`).
7. Spawn **ielts-grammar** (its body is `.claude/agents/ielts-grammar.md`; it reads
   `references/deep-question-blueprint.md`, `references/deep-grammar-generation-rules.md`,
   `references/deep-grammar-rules.md`, `references/level-blueprint-rules.md`,
   `references/grammar-by-level.md`). Ensure the grammar blueprint is created before
   questions, no hardcoded headings appear, and transformations preserve meaning.
8. Spawn **ielts-writing** (its body is `.claude/agents/ielts-writing.md`).
9. Spawn **ielts-answer** (its body is `.claude/agents/ielts-answer.md`; it reads
   `references/deep-answer-key-rules.md`).
10. Assemble the complete payload into `lesson_source.json` per `references/output-schema.md`.
11. Spawn **ielts-quality-control** (its body is `.claude/agents/ielts-quality-control.md`; it reads
    `references/regeneration-quality-gates.md`, `references/deep-reading-qc.md`).
12. If QC fails, set `execution.pipeline_status` to `qc_failed`, increment the
    relevant `revision_attempts` counter, regenerate the failed section(s) only
    (spawn the responsible sub-agent again with the challenge + current section),
    and rerun QC.
13. Stop and report unresolved challenges if a section reaches the maximum revision
    attempts listed under Loop Specific Hard Rules.
14. When content QC passes and no high/critical challenge remains open, set
    `execution.pipeline_status` to `qc_passed`.
15. Rerun validation: `python .claude/skills/ielts-daily-reading-writing/scripts/validate_lesson_json.py <lesson_source.json>`.
16. If validation passes, invoke compilation:
    `python .claude/skills/ielts-daily-reading-writing/scripts/export_daily_pack.py <lesson_source.json>`.
17. Treat the lesson as final only after post-render PDF QC passes.

## High-Level Workflow for Cumulative Review Pack
> Note: `scripts/export_review_pack.py` currently has a pre-existing Python syntax
> error in the source tree (line ~1412). Fix that file before running review-pack
> export; the rest of the review workflow still applies.

1. Identify target days and retrieve recent level lessons from
   `outputs/ielts-daily-reading-writing/lesson_history.txt`.
2. Run aggregation: `python .claude/skills/ielts-daily-reading-writing/scripts/prepare_review_inputs.py --level [Level] [--days [Days]]`.
3. Generate review reading passage and questions based on aggregated topics.
4. Generate grammar drill questions based on aggregated grammar targets.
5. Generate writing tasks testing those targets.
6. Assemble review JSON per `references/output-schema.md` and run QC.
7. If QC fails, regenerate only the failed section(s), respecting the same revision limits.
8. When QC passes, set `execution.pipeline_status` to `qc_passed` and run
   `python .claude/skills/ielts-daily-reading-writing/scripts/validate_lesson_json.py [review JSON]`.
9. If validation passes, compile: `python .claude/skills/ielts-daily-reading-writing/scripts/export_review_pack.py [review JSON]`.
10. Treat the review pack as final only after post-render PDF QC passes.

## Hard Rules
- Only **ielts-source-research** may search or verify web sources.
- Do not invent URLs, titles, authors, publication dates, facts, or source details.
  If no verified source exists, stop and report a source gap.
- Every Sub-Agent must return structured JSON compatible with `references/output-schema.md`.
- Reading and Grammar generation must create `reading_blueprint` / `grammar_blueprint`
  before writing the actual questions, then self-check every generated item against its blueprint.
- **JSON Validator Integration**: Do not export PDF from free-form markdown or
  unvalidated JSON. `export_daily_pack.py` auto-runs `validate_lesson_json.py` and
  rejects compilation if any errors exist.
- If one section fails QC, regenerate ONLY that section. Do not regenerate the
  whole pack unless the source, level, or topic changes.
- Preserve the output folder contract: `outputs/ielts-daily-reading-writing/[Day]-[Level]/{lsn/, aws/, quizlet}`.
- Preserve spelling `Practise.pdf`.
- Preserve history logging in `outputs/ielts-daily-reading-writing/lesson_history.txt`.
- Preserve spaced repetition vocabulary recycling.

## Compiler and Exporter Robustness Rules
All rendering, table splitting, heading cleansing, writing-line allocation, SVG
protection, and visual-data formatting rules are in
`references/output-template.md §Exporter and Template Rendering Constraints`.
Do NOT load this section into agent context; it is consumed only by `export_daily_pack.py`.

## Human-in-the-loop and Agent Review Loop
Before finalizing any daily practice pack, use the review workflow in
`references/human-in-loop.md`, `references/agent-review-loop.md`, and
`references/quality-control-agent.md`. The orchestrator runs internal agent
review loops; the user may also request explicit checkpoints.

### Auto Mode (default)
Use Auto Mode unless the user explicitly asks to review intermediate outputs.
1. Run all Sub-Agents.
2. Run Agent Review Loop internally (each section reviewed by a downstream agent + QC).
3. Let QC challenge and critique weak sections.
4. Regenerate only failed sections.
5. Export PDF only after QC passes.
6. Return final files and QC report.

### Review Mode
Use Review Mode when the user asks to approve sources, approve outline, review
questions, review vocabulary, review grammar, review writing tasks, or check
before PDF export. Trigger phrases include: "cho tôi duyệt nguồn trước",
"review từng phần", "dừng trước khi export PDF", "cho tôi kiểm tra câu hỏi",
"cho tôi duyệt vocabulary", "chạy human-in-loop", "manual approval", "review mode".

In Review Mode, **stop at human checkpoints** and present a compact review
summary, then use **AskUserQuestion** to collect the user's decision before
continuing. Checkpoints (See `references/human-in-loop.md` for the exact fields
to show and allowed actions):
1. **Source Approval** — title, publisher, URL, credibility/relevance/copyright notes, proposed use.
2. **Lesson Blueprint Approval** — Day, per-section levels, topic, source, grammar targets, vocab mix, writing plan, stretch ratio.
3. **Reading Question Approval** — per-question ID, type, skill, answer, evidence paragraph, QC note.
4. **Vocabulary Approval** — count by `vocab_type`, samples, recycled vocab, writing-useful chunks.
5. **Grammar Approval** — targets, question-type distribution, stretch items, ambiguity warnings.
6. **Writing Task Approval** — task list, target length, visual data type, grammar/vocab focus, success criteria.
7. **Pre-PDF Approval** — QC result, counts, output files, layout warnings.

Record every human decision in `lesson_source.json` under `human_review`
(`mode`, `checkpoints[]` with `checkpoint`, `status`, `user_instruction`).

## Loop Specific Hard Rules
- QC Agent must be allowed to challenge Reading, Vocabulary, Grammar, Writing, and Answer outputs.
- Any challenged Sub-Agent must revise only the challenged section.
- Do not regenerate the whole pack unless source, level, topic, or user direction changes.
- If QC detects ambiguity, multiple possible answers, missing evidence, missing
  visual data, insufficient answer space, or vocabulary imbalance, the responsible
  agent must revise its output.
- PDF export must not run until content QC status is `pass`, `execution.pipeline_status`
  is `qc_passed`, and `validate_lesson_json.py` passes without errors.
- **Maximum revision attempts**: source 2, reading 3, vocabulary 2, grammar 3,
  writing 2, answers 2, PDF layout 2.
- If any section reaches its maximum revision attempts, stop Auto Mode, keep
  unresolved challenges open, and report the blocker instead of silently accepting it.

## Post-Render PDF Quality Control
After generating PDFs, run Post-Render PDF QC using `references/post-render-pdf-qc.md`
and `python .claude/skills/ielts-daily-reading-writing/scripts/validate_rendered_pdf.py`.
The automated script validates the Practice PDF against `lesson_source.json`; use
the post-render checklist to inspect every exported PDF for missing content or layout regressions.

A lesson is not final until:
1. `lesson_source.json` validation passes.
2. Content QC passes.
3. PDFs are exported.
4. Rendered PDF QC passes.
5. No critical/high post-render issues remain.

Do not mark pipeline as `exported` or final if the rendered PDF is missing:
multiple-choice options, grammar blanks, computed section ranges, correct Time
Allowed, required writing spaces, charts/visual data, or footer metadata.

If rendered PDF QC fails, fix the compiler/template only when `lesson_source.json`
is correct. Do not regenerate lesson content unless the JSON itself is wrong.

## Zero-Tolerance Logic Rule
Question logic errors are critical failures. Never finalize, export, or mark QC
passed if any question has:
- more than one naturally valid answer
- insufficient context to determine the correct answer
- a correct option that does not produce a complete grammatical sentence
- missing punctuation needed to complete the sentence
- hidden assumptions that only the author knows
- mismatch between instruction and expected answer
- an answer key correct only under one unstated interpretation

### Specific Logic & Quality Constraints:
1. **Present Perfect vs. Past Simple**: when testing present perfect vs. past
   simple, the prompt MUST contain an explicit time indicator (e.g. `so far today`,
   `since 2024`, `yesterday`, `three days ago`).
2. **Inference Distractor Uniqueness**: every inference question must have exactly
   one option logically supported by the passage; all others unambiguously false,
   unsupported, or containing extreme language (`only`, `always`, `never`).
3. **Main Idea Evidence Quotes**: main idea questions must have a broad
   `evidence_quote` covering the whole paragraph / core-idea sentences.
4. **Draft Placeholder Removal**: all `[R]` markers must be removed from passage,
   question, option, and explanation text. No draft markers in student-facing sheets.
5. **Level Consistency**: suffix levels (e.g. `A2+`, `B1+`) must be consistent
   across `level`, `lesson_meta.level`, and the markdown header titles.
6. **Detailed Explanations**: grammar answer explanations (`analysis_vi`) must be
   comprehensive — explain the grammar target, context clues, grammar rules, and
   explicitly why each incorrect option is wrong.

Mark any such issue as `challenge_type: "logic_error"` with severity `critical`.
The responsible agent must revise the item before PDF export. No high/critical
logic challenge may be accepted silently in Auto Mode.

## Zero-Tolerance Correct-the-Error Rule
For any question whose instruction is `Correct the error`, `Correct the mistake`,
`Error correction`, or equivalent:
- The original sentence must contain exactly one clear target error.
- The correct answer must differ from the original sentence.
- The explanation must refer to an error actually present in the original sentence.
- If the original sentence is already grammatical, the item is invalid.
- If the correct answer equals the original sentence, the item is invalid.
- If the explanation mentions a word/structure not present in the original, it is invalid.
These are critical logic errors. No lesson may be marked `qc_passed`, `exported`,
or final if any Correct-the-error item fails this rule.

## Reference Loading Map (STRICT)
Load ONLY the files listed for the **current pipeline stage**. Do NOT pre-load all reference files.

> **Path convention:** every `references/...` path below is relative to this
> skill folder — i.e. `.claude/skills/ielts-daily-reading-writing/references/...`.
> Sub-agent file paths (`.claude/agents/ielts-*.md`) are project-root-relative.

| Stage | Spawn sub-agent | MUST Read (in sub-agent) | MUST NOT Load |
|---|---|---|---|
| **Startup / Input Resolution** | — (orchestrator) | `orchestrator.md`, `pedagogical-constraints.md` | all `deep-*` files, agent files |
| **Source Research** | `ielts-source-research` | `source-research-agent.md` | all `deep-*`, `grammar-*`, `writing-*`, `answer-*` |
| **Reading** | `ielts-reading` | `reading-agent.md`, `deep-reading-generation-rules.md`, `deep-question-blueprint.md`, `level-blueprint-rules.md` | `deep-grammar-*`, `writing-agent.md`, `answer-agent.md`, `vocabulary-agent.md` |
| **Vocabulary** | `ielts-vocabulary` | `vocabulary-agent.md` | `deep-grammar-*`, `deep-reading-*`, `writing-agent.md`, `answer-agent.md` |
| **Grammar** | `ielts-grammar` | `grammar-agent.md`, `deep-grammar-generation-rules.md`, `deep-grammar-rules.md`, `deep-question-blueprint.md`, `level-blueprint-rules.md`, `grammar-by-level.md` | `deep-reading-*`, `vocabulary-agent.md`, `writing-agent.md` |
| **Writing** | `ielts-writing` | `writing-agent.md` | `deep-grammar-*`, `deep-reading-*`, `vocabulary-agent.md` |
| **Answers** | `ielts-answer` | `answer-agent.md`, `deep-answer-key-rules.md` | `deep-grammar-*`, `deep-reading-generation-rules.md`, `vocabulary-agent.md` |
| **QC** | `ielts-quality-control` | `quality-control-agent.md`, `regeneration-quality-gates.md`, `deep-reading-qc.md` | `vocabulary-agent.md`, `writing-agent.md`, `grammar-by-level.md` |
| **Post-render PDF QC** | — (orchestrator + script) | `post-render-pdf-qc.md` | all agent files |
| **Human Review** | — (orchestrator) | `human-in-loop.md`, `agent-review-loop.md` | all `deep-*` files |
| **Schema Reference** | — | `output-schema.md` | `output-schema-full.md` (used only by `validate_lesson_json.py`) |
| **Topic Selection** | — (orchestrator) | `topic-bank.md` | all `deep-*`, all agent files |

## Recurring QA Errors — Prevention Registry
Each entry has a **Root Cause**, **Prevention Rule**, and **Verification Step**
that must run before marking a lesson final. (Condensed; see the original
pipeline rules embedded in the sub-agent docs and `references/`.)

| ID | Symptom | Prevention Rule |
|---|---|---|
| RQA-01 | MCQ options show `A. A. Option` (doubled prefix) | Options must be raw text only — no `A. `/`B. ` prefix. QC rejects any option matching `^[A-D]\.\s`. |
| RQA-02 | Split-level metadata not synced to PDF header | Populate all four flat keys AND `skill_level` dict; header must read `(Level: Reading A2+ \| Grammar A2 \| Writing A1 \| Vocab A2)`. |
| RQA-03 | Review Bridge split across pages | Review Bridge wrapper div must carry `page-break-before: always; page-break-inside: avoid;`. |
| RQA-04 | Ambiguous MCQ distractor (`more quiet`) | Never use `more quiet` for a `quieter` question; use `more quieter`. `one_answer_check.has_exactly_one_valid_answer` must be `true`. |
| RQA-05 | Multi-error sentence in Correct-the-Error | Exactly one target error (`error_correction_validation.exactly_one_target_error: true`); corrected sentence differs in exactly one token. |
| RQA-06 | Reading `reasoning_skill` mislabeled | Use schema-allowed values: `paraphrase`/`classification`/`inference`/`writer_purpose`. Validator enforces the list. |
| RQA-07 | Missing author attitude / writer purpose question | At A2+ and above, include ≥1 `writer_purpose`/`author_attitude` question with evidence + 3-step Vietnamese Thinking Process. |
| RQA-08 | Draft marker `[R]` left in final lesson | Remove all `[R]` from passage/questions/options/answers; QC greps `[R]` as blocking. |
| RQA-09 | Subgroup data overclaim | Reading questions about a subgroup must be supported uniquely by that subgroup's data, not overall cohort stats. |
| RQA-10 | Double punctuation in grammar MCQ options | Option punctuation must not duplicate punctuation already at the blank boundary. |
| RQA-11 | Reversed cause-effect in connective tasks | `Result because Cause` / `Because Cause, Result` — verify direction with `because`/`since`/`therefore`/`consequently`. |
| RQA-12 | Gap-fill numbering mismatch | Blank label `(N)` must equal the question number `N`. |
| RQA-13 | Level `+` suffix stripped from file/folder names | `safe_filename_part()` must allow `+`; folders/files keep `A2+`, `B1+`, etc. |

### Summary QA Gate (Run Before Every PDF Export)
`python .claude/skills/ielts-daily-reading-writing/scripts/validate_lesson_json.py <lesson_source.json>`
must return `0 FAIL`. Additionally confirm:
- RQA-01: no `A./B./C./D.` prefix in any `options` array.
- RQA-02: `lesson_meta.skill_level` populated; PDF header shows all 4 skills.
- RQA-03: Review Bridge has `page-break-before: always` in compiled HTML.
- RQA-04: all grammar MCQs have `one_answer_check.has_exactly_one_valid_answer: true`.
- RQA-05: all error-correction items have `exactly_one_target_error: true`.
- RQA-06: all `reasoning_skill` values are schema-allowed.
- RQA-07: at A2+ and above, ≥1 `writer_purpose` question exists.
- RQA-08: no `[R]` marker anywhere in the JSON.
- RQA-09: subgroup questions fully supported by subgroup-specific data.
- RQA-10: grammar MCQ options do not create double punctuation when inserted.
- RQA-11: writing combination model answers preserve logical cause-effect.
- RQA-12: gap-fill blank numbers `(N)` match question number `N`.
- RQA-13: level `+` suffix preserved in folder and file names.
