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
- `Reading Level`: one of `A1`, `A1+`, `A2`, `A2+`, `B1`, `B1+`, `B2`, `B2+`, `C1`, `C1+`, `C2`; default `A2`. Also accepted as `Level` for backwards compatibility — treated as Reading Level.
- `Grammar Level`: one of `A1`, `A1+`, `A2`, `A2+`, `B1`, `B1+`, `B2`, `B2+`, `C1`, `C1+`, `C2`; default = Reading Level.
- `Writing Level`: one of `A1`, `A1+`, `A2`, `A2+`, `B1`, `B1+`, `B2`, `B2+`, `C1`, `C1+`, `C2`; default = Reading Level.
- `Vocabulary Level`: one of `A1`, `A1+`, `A2`, `A2+`, `B1`, `B1+`, `B2`, `B2+`, `C1`, `C1+`, `C2`; default = Reading Level.
- `Number of IELTS Reading Questions`: default `13`.
- `Number of Vocabulary Words`: default `20`.
- `Number of Grammar Questions`: default `30`.
- `Number of Writing Practice`: default `5`.
- Optional prior history: previous daily topics, learner errors, weak skills, or past outputs.
- Optional cumulative review request.

### Level Input Rules

**Single-level input** (e.g. `Level: A2` or `Reading Level: A2`):
- Set `reading_level = A2`.
- Set `grammar_level = writing_level = vocabulary_level = reading_level` (inherit).

**Split-level input** (e.g. `Reading Level: A2+, Writing Level: A1`):
- Set each skill level independently.
- Any unspecified skill level inherits from `reading_level`.

**lesson_meta mapping** — always populate all four flat keys **and** the nested `skill_level` dict:
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
If all four levels are identical, a compact single-level form may be used instead:
```
(Level: A2)
```

Normalize common variants: `Writting` means `Writing`; `IELTS Reading Questions` means reading question count; `Vocab Level` means `Vocabulary Level`; `Grammar` alone means `Grammar Level`.


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
5. Run **Reading Agent** using `references/reading-agent.md`, `references/deep-question-blueprint.md`, and `references/deep-reading-generation-rules.md`. **Crucially, the Reading Agent must strictly align its passage and question complexity to the resolved `Reading Level` (e.g. A2+) and its corresponding pedagogical rules.** Ensure the Reading blueprint is created before questions, all questions have verbatim evidence quotes, and the level-specific deep-reading ratios are met.
6. Run **Vocabulary Agent** using `references/vocabulary-agent.md`. **The Vocabulary Agent must strictly target vocabulary extraction and check matching difficulty according to the resolved `Vocabulary Level`.**
7. Run **Grammar Agent** using `references/grammar-agent.md`, `references/deep-question-blueprint.md`, and `references/deep-grammar-generation-rules.md`. **The Grammar Agent must strictly generate and validate grammar items according to the resolved `Grammar Level` (and its corresponding pedagogical rules).** Ensure the Grammar blueprint is created before questions, no hardcoded headings appear, and transformations preserve meaning.
8. Run **Writing Agent** using `references/writing-agent.md`. **The Writing Agent must strictly align the writing tasks, prompts, and success criteria to the resolved `Writing Level`.** Ensure daily topic relevance.
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
All rendering, table splitting, heading cleansing, writing-line allocation, SVG protection, and visual-data formatting rules are documented in `references/output-template.md §Exporter and Template Rendering Constraints`.
Do NOT load this section into agent context; it is consumed only by `scripts/export_daily_pack.py`.

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

### Specific Logic & Quality Constraints:
1. **Present Perfect vs. Past Simple Clarification**: When testing present perfect vs. past simple, the prompt sentence MUST contain an explicit time indicator (e.g., `so far today`, `since 2024`, `yesterday`, `three days ago`) to rule out any alternative interpretations and guarantee a single unique correct answer.
2. **Inference Distractor Uniqueness**: Every inference question must have exactly one option that is logically supported by the passage. All other options must be unambiguously false, unsupported by the passage, or contain extreme language (e.g., `only`, `always`, `never`).
3. **Main Idea Evidence Quotes**: Main idea questions must have a broad `evidence_quote` containing the entire paragraph or the sentences summarizing the core idea, rather than a single narrow sentence.
4. **Draft Placeholder Removal**: All placeholders such as `[R]` or `[R]` must be completely removed from the reading passage text, question texts, option texts, and answer explanations. No draft markers are allowed in final student-facing sheets.
5. **Level Consistency**: Suffix levels (e.g., `A2+`, `B1+`) must be consistent across `level`, `lesson_meta.level`, and the markdown header titles.
6. **Detailed Explanations**: Grammar answer explanations (`analysis_vi`) must be comprehensive, explaining the grammar target, context clues, grammar rules, and explicitly detailing why each incorrect option is wrong.

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

## Reference Loading Map (STRICT)

Load ONLY the files listed for the **current pipeline stage**. Do NOT pre-load all reference files.

| Stage | MUST Load | MUST NOT Load |
|---|---|---|
| **Startup / Input Resolution** | `orchestrator.md`, `pedagogical-constraints.md` | All `deep-*` files, agent files |
| **Source Research** | `source-research-agent.md` | All `deep-*` files, `grammar-*`, `writing-*`, `answer-*` |
| **Reading** | `reading-agent.md`, `deep-reading-generation-rules.md`, `deep-question-blueprint.md`, `level-blueprint-rules.md` | `deep-grammar-*`, `writing-agent.md`, `answer-agent.md`, `vocabulary-agent.md` |
| **Vocabulary** | `vocabulary-agent.md` | `deep-grammar-*`, `deep-reading-*`, `writing-agent.md`, `answer-agent.md` |
| **Grammar** | `grammar-agent.md`, `deep-grammar-generation-rules.md`, `deep-grammar-rules.md`, `deep-question-blueprint.md`, `level-blueprint-rules.md`, `grammar-by-level.md` | `deep-reading-*`, `vocabulary-agent.md`, `writing-agent.md` |
| **Writing** | `writing-agent.md` | `deep-grammar-*`, `deep-reading-*`, `vocabulary-agent.md` |
| **Answers** | `answer-agent.md`, `deep-answer-key-rules.md` | `deep-grammar-*`, `deep-reading-generation-rules.md`, `vocabulary-agent.md` |
| **QC** | `quality-control-agent.md`, `regeneration-quality-gates.md`, `deep-reading-qc.md` | `vocabulary-agent.md`, `writing-agent.md`, `grammar-by-level.md` |
| **Post-render PDF QC** | `post-render-pdf-qc.md` | All agent files |
| **Human Review** | `human-in-loop.md`, `agent-review-loop.md` | All `deep-*` files |
| **Schema Reference** | `output-schema.md` | `output-schema-full.md` (used only by `validate_lesson_json.py`) |
| **Topic Selection** | `topic-bank.md` | All `deep-*` files, all agent files |

## Recurring QA Errors — Prevention Registry

This section documents every concrete error pattern that was caught during QA review and fixed in post-production. Each entry carries a **Root Cause**, **Prevention Rule**, and **Verification Step** that must be run before marking a lesson as final.

---

### RQA-01 · Double Letter Prefix in MCQ Options (`A. A.`)

**Symptom**: Rendered PDF/HTML shows `A. A. Option text`, `B. B. Option text`, etc.

**Root Cause**: The renderer automatically prefixes options with `A.`, `B.`, etc. If the `options` array in the JSON already contains hardcoded letter prefixes (`"A. Option text"`), the renderer doubles them.

**Prevention Rule**:
- Options in `lesson_source.json` must contain **raw option text only** — no leading `A. `, `B. `, `C. `, `D. ` prefix.
- Applies to every question type: Reading MCQ, Grammar MCQ, Vocabulary Checker.
- The QC Agent must reject any `options` element matching the regex `^[A-D]\.\s`.

**Verification Step**:
```python
# Must return 0 matches
import re, json
data = json.load(open("lesson_source.json", encoding="utf-8"))
bad = [f"Q{q['id']}: {opt}" for section in ["reading","grammar"]
       for q in data[section]["questions"]
       for opt in q.get("options", [])
       if re.match(r'^[A-D]\.\s', opt)]
assert not bad, bad
```

---

### RQA-02 · Split-Level Metadata Not Synced to PDF Header

**Symptom**: `lesson_meta` contains `reading_level`, `grammar_level`, `writing_level`, `vocabulary_level`, but the Practice PDF and/or Answer Key PDF header shows only the generic `level` or only two skills.

**Root Cause**: `build_practice_html` and `build_answers_html` in `export_daily_pack.py` used to extract only `reading_level` and `writing_level` from the markdown `Intro` section via regex; they ignored the structured `skill_level` dict in `lesson_meta`.

**Prevention Rule (JSON)**:
Every lesson with split-level instruction must populate `lesson_meta` with:
```json
{
  "reading_level": "A2+",
  "grammar_level": "A2",
  "writing_level": "A1",
  "vocabulary_level": "A2",
  "skill_level": {
    "reading_level": "A2+",
    "grammar_level": "A2",
    "writing_level": "A1",
    "vocabulary_level": "A2"
  }
}
```
All four flat keys AND the nested `skill_level` dict must be populated.

**Prevention Rule (Compiler)**:
`build_practice_html` and `build_answers_html` receive `skill_level: dict` from the call site. The rendered header must read:
```
(Level: Reading A2+ | Grammar A2 | Writing A1 | Vocab A2)
```

**Verification Step**:
```python
meta = data["lesson_meta"]
assert meta.get("reading_level"), "missing reading_level"
assert meta.get("grammar_level"), "missing grammar_level"
assert meta.get("writing_level"), "missing writing_level"
assert meta.get("vocabulary_level"), "missing vocabulary_level"
assert meta.get("skill_level"), "missing skill_level dict"
```
And in both compiled HTML files:
```python
assert "(Level: Reading" in practice_html
assert "(Level: Reading" in answer_html
assert "Grammar" in practice_html  # all 4 parts present
assert "Vocab" in practice_html
```

---

### RQA-03 · Review Bridge Splitting Across Pages

**Symptom**: The Review Bridge section is broken across two pages in the printed PDF.

**Root Cause**: The Review Bridge `<div>` had no page-break CSS. Depending on where it fell on the page, it could be split mid-section.

**Prevention Rule (Compiler)**:
The Review Bridge wrapper div in `build_practice_html` and `build_answers_html` must always carry:
```html
<div class="review-bridge-container"
     style="page-break-before: always; page-break-inside: avoid;">
```
This ensures it always starts on a fresh page and is never split.

**Verification Step**:
```python
assert 'page-break-before: always' in practice_html
assert 'review-bridge-container' in practice_html
assert 'page-break-before: always' in answer_html
assert 'review-bridge-container' in answer_html
```

---

### RQA-04 · Ambiguous MCQ Distractor (Double Comparative / `more quiet`)

**Symptom**: Option A reads `"more quiet"`, which is acceptable in informal English, making both `"more quiet"` and `"quieter"` valid answers — violating the Single Unique Answer Rule.

**Root Cause**: The Grammar Agent selected `"more quiet"` as a plausible-but-incorrect distractor for a comparative question. However, `"more quiet"` is widely accepted in native speech.

**Prevention Rule**:
- **Never use `"more quiet"` as a distractor** for a question testing `"quieter"`.
- Use demonstrably wrong double-comparative forms instead: `"more quieter"` (double comparative error) is unambiguously wrong.
- The `one_answer_check.has_exactly_one_valid_answer` field must be `true` for every MCQ.
- Any distractor that could be acceptable in informal or regional English must be replaced.

**Verification Step**:
```python
for q in data["grammar"]["questions"]:
    assert q.get("one_answer_check", {}).get("has_exactly_one_valid_answer") is True, \
        f"Q{q['id']} fails one_answer_check"
```

---

### RQA-05 · Multi-Error Sentence in Correct-the-Error Items

**Symptom**: An error-correction prompt sentence contains two grammatical errors (e.g., wrong tense + wrong auxiliary). A student could correct either one, giving multiple valid corrected sentences.

**Root Cause**: Grammar Agent generated a prompt sentence with both a tense and an auxiliary error simultaneously.

**Prevention Rule**:
- Each Correct-the-Error item must contain **exactly one target error** (confirmed by `error_correction_validation.exactly_one_target_error: true`).
- `target_error_text` must be a single word or minimal phrase.
- The corrected sentence must differ from the original in **exactly one token**.
- Example compliant item: `"Have you ever book a class?"` → error = `"book"` → correction = `"booked"`.
- Example non-compliant item: `"Did you ever booked a class?"` → two errors: `Did` + `booked`.

**Verification Step**:
```python
for q in data["grammar"]["questions"]:
    ecv = q.get("error_correction_validation", {})
    if ecv:
        assert ecv.get("exactly_one_target_error") is True, f"Q{q['id']} has multiple errors"
        assert ecv.get("original_contains_error") is True, f"Q{q['id']} original has no error"
```

---

### RQA-06 · Reading Q Reasoning Skill Mislabeled

**Symptom**: A NOT GIVEN question is labeled `reasoning_skill: "inference"` instead of `"classification"`. This confuses the answer key explanation category.

**Root Cause**: The Reading Agent used `"inference"` as a catch-all for all non-literal questions.

**Prevention Rule**:
- `reasoning_skill` must be one of the schema's allowed values. Common mappings:
  - Literal information present → `"paraphrase"`
  - Information missing from text → `"classification"` (NOT GIVEN)
  - Implication from evidence → `"inference"`
  - Writer's opinion/attitude → `"writer_purpose"`
- The schema validator (`validate_lesson_json.py`) enforces the allowed list; do not invent new values.

**Verification Step**:
Run `python scripts/validate_lesson_json.py lesson_source.json` — any invalid `reasoning_skill` will cause validation failure.

---

### RQA-07 · Deep Reading Missing Author Attitude / Writer Purpose Question

**Symptom**: A 13-question reading section has no question testing the author's tone, attitude, or purpose — a required deep-reading skill at A2+ and above.

**Root Cause**: The Reading Agent filled all question slots with vocabulary, inference, and True/False questions, skipping the `writer_purpose` category.

**Prevention Rule**:
- At A2+ and above, the 13-question reading section **must include at least one** question with `reasoning_skill: "writer_purpose"` or `reasoning_skill: "author_attitude"`.
- This question must cite evidence from the passage (no external knowledge).
- The answer key must include a 3-step Thinking Process in Vietnamese.

**Verification Step**:
```python
level = data["lesson_meta"].get("level", "")
if "+" in level or level in ("B1","B2","C1","C2"):
    skills = [q.get("reasoning_skill") for q in data["reading"]["questions"]]
    assert "writer_purpose" in skills or "author_attitude" in skills, \
        "Missing writer_purpose/author_attitude question at this level"
```

---

### RQA-08 · Draft Marker `[R]` Left in Final Lesson

**Symptom**: Practice PDF contains visible `[R]` placeholder text inside reading passages, question prompts, or answer explanations.

**Root Cause**: Temporary research markers were inserted during source verification but never cleaned before finalization.

**Prevention Rule**:
- The Reading Agent must remove all `[R]`, ` [R]`, and `[R] ` markers from `passage_text`, question texts, option texts, and `answers` before committing to `lesson_source.json`.
- The QC Agent must grep for `[R]` as a blocking condition.

**Verification Step**:
```python
import re, json
text = json.dumps(data)
assert not re.search(r'\[R\]', text), "Draft [R] marker found in lesson_source.json"
```

---

### RQA-09 · Subgroup Data Overclaim in Reading Questions

**Symptom**: A reading question asks about a specific subgroup, but the answer key relies on data for the overall cohort (which contains multiple subgroups).

**Root Cause**: The Reading Agent treats overall cohort statistics as applicable to a specific subgroup named in the passage.

**Prevention Rule**:
- Ensure reading questions referencing subgroups (e.g., specific studies or sub-populations) are supported explicitly and uniquely by details about that specific subgroup.
- Do not generalize overall statistics to a named subgroup.

---

### RQA-10 · Double Punctuation in Grammar MCQ Options

**Symptom**: Selecting the correct grammar option produces double commas or double periods (e.g., `, which, was built...` when a comma is already present in the prompt).

**Root Cause**: The Grammar Agent includes surrounding punctuation in the option text without checking if that punctuation is already written in the prompt.

**Prevention Rule**:
- Any punctuation included in option texts (especially commas) must not duplicate the punctuation already present at the boundaries of the blank in the sentence prompt.

---

### RQA-11 · Reversed Cause-Effect in Connective Tasks

**Symptom**: Sentence combination model answers reverse the natural cause-effect relationship (e.g., `A happened because B happened` when A is actually the cause of B).

**Root Cause**: Writing Agent links sentences without checking semantic logic of the cause-effect direction.

**Prevention Rule**:
- Always check that the resulting sentence using `because`, `since`, `as`, `therefore`, or `consequently` correctly places the cause and effect: `Result because Cause` or `Because Cause, Result`.

---

### RQA-12 · Gap-Fill Numbering Mismatch with Blanks

**Symptom**: In gap-fill questions, the blank label numbers inside parentheses (e.g. `(11)`) do not match the absolute question numbers (e.g. `Question 6`).

**Root Cause**: Renumbering or re-ordering during compilation splits/changes question IDs but leaves the inner blank text unchanged.

**Prevention Rule**:
- Check that the label inside the gap-fill blank `(N)` exactly equals the question number `N` for that question.

---

### Summary QA Gate (Run Before Every PDF Export)

The following script must return `0 FAIL` before running `export_daily_pack.py`:

```
python scripts/validate_lesson_json.py lesson_source.json
```

In addition, confirm manually or via automated checks:

| Gate | Check |
|---|---|
| RQA-01 | No `A./B./C./D.` prefix in any `options` array |
| RQA-02 | `lesson_meta.skill_level` populated; PDF header shows all 4 skills |
| RQA-03 | Review Bridge has `page-break-before: always` in compiled HTML |
| RQA-04 | All grammar MCQs have `one_answer_check.has_exactly_one_valid_answer: true` |
| RQA-05 | All error-correction items have `exactly_one_target_error: true` |
| RQA-06 | All `reasoning_skill` values are in the schema-allowed list |
| RQA-07 | At A2+ and above, at least one `writer_purpose` question exists |
| RQA-08 | No `[R]` marker appears anywhere in the JSON |
| RQA-09 | Reading questions referencing subgroups are fully supported by subgroup-specific data |
| RQA-10 | Grammar MCQ options do not create double punctuation when inserted |
| RQA-11 | Writing combination task model answers preserve logical cause-effect relationships |
| RQA-12 | Reading gap-fill blank numbers `(N)` match the question number `N` |
| RQA-13 | Level '+' suffix (e.g., A2+, B1+) is correctly preserved in folder and file names |
| RQA-14 | Sentence combining prompts specify clause conversion direction or accept both valid combinations |
| RQA-15 | Defining relative clause answers accept `that` alongside `which`/`who` unless restricted by prompt |
| RQA-16 | Modal choice prompts contain explicit context anchors or ungrammatical distractors to rule out alternative modal interpretations |
| RQA-17 | Defining relative clause error correction and combining items include `that` in `accepted_answers` and `alternative_answers_allowed` |
| RQA-18 | Writing prompt bullet hints (`-`, `*`) do not render answer lines between hint items |
| RQA-19 | Past Perfect gap-fills include explicit duration/time anchors to eliminate Past Simple ambiguity |
| RQA-20 | Open-ended defining relative clause gap-fills restrict pronoun in prompt or accept both `that` and `which` |
| RQA-21 | Grammar stems vary phrasing from Reading passage to avoid PDF text-matching collisions |
| RQA-22 | Writing Opinion tasks for A1-B1 include 5-step numbered structure and explicit sentence starters |

---

### RQA-13 · Level '+' Suffix Stripped from File/Folder Names

**Symptom**: Generated output folder is named `20260715-A2` instead of `20260715-A2+`, causing duplicate directories or level mismatch.

**Root Cause**: The helper function `safe_filename_part()` in compilation/export scripts was stripping `+` characters from filenames.

**Prevention Rule**:
- Ensure `safe_filename_part()` allows `+` characters: `re.sub(r"[^\w\s.+\-]+", "", value)`.
- Ensure levels containing `+` (e.g., `A2+`, `B1+`, `B2+`, `C1+`) are preserved in both folder names and compiled PDF/HTML filenames.

**Verification Step**:
Verify that the output directory contains the resolved level with its exact suffix (e.g., `outputs/ielts-daily-reading-writing/20260715-A2+`).

---

### RQA-14 · Unconstrained Sentence Combining Ambiguity

**Symptom**: A sentence combining prompt allows converting either main clause into a relative clause, producing two valid answers with slightly different emphasis.

**Root Cause**: The Grammar Agent did not specify which sentence should be converted into the relative clause.

**Prevention Rule**:
- Sentence combining prompts MUST specify clause direction (e.g., `"Make Sentence 1 the relative clause:"`), OR the answer key (`explanation_vi` & `one_answer_check`) MUST document both valid combinations.

---

### RQA-15 · Defining Relative Pronoun Equivalence Omission

**Symptom**: Answer key accepts only `which` (or `who`) in a defining relative clause and rejects `that`.

**Root Cause**: The Grammar Agent did not constrain the pronoun in the prompt, nor did it document `that` as acceptable in defining relative clauses.

**Prevention Rule**:
- If the prompt does not restrict the relative pronoun (e.g., `"Use which"`), the answer key MUST explicitly document `that` as an acceptable alternative in defining relative clauses.

---

### RQA-16 · Ambiguous Modal Verb Distractors in Controlled Choice

**Symptom**: A modal choice question like `"If the receptionist is busy, you ____ book an appointment..."` has multiple plausible modals (`can`, `should`, `might`) because the prompt lacks specific context clues.

**Root Cause**: The Grammar Agent created a modal question without contextual anchors (such as `"have the option to"`, `"according to mandatory rules"`, `"is available"`) or without restricting distractors to ungrammatical/impossible forms.

**Prevention Rule**:
- Every modal choice question MUST include an explicit context clue establishing the exact modal nuance targeted (ability/option vs obligation vs advice), OR use distractors that are clearly ungrammatical or semantically impossible in that context.
- If a sentence can be naturally completed by more than one modal, all valid alternatives MUST be explicitly included in `accepted_answers` and `alternative_answers_allowed`.

**Verification Step**:
Verify that every modal choice question in `grammar.questions` contains explicit context anchors or ungrammatical distractors, and `one_answer_check.has_exactly_one_valid_answer` is `true`.

---

### RQA-17 · Defining Relative Clause Alternative Answer Equivalence (`that` vs `which` / `who`)

**Symptom**: Answer key accepts only `which` (or `who`) in a defining relative clause or error correction item (e.g., `The prescription which...`) and marks `that` as incorrect, or fails to populate `accepted_answers` / `alternative_answers_allowed`.

**Root Cause**: The Grammar / Answer Agent omitted `that` from `accepted_answers` and `alternative_answers_allowed`.

**Prevention Rule**:
- For every defining relative clause item (including Error Correction and Sentence Combining), both `which` (or `who`) AND `that` MUST be included in `accepted_answers` and `alternative_answers_allowed` unless the prompt explicitly specifies a single pronoun.

**Verification Step**:
Check that defining relative clause items in `grammar.questions` and `answers.grammar_answers` have `accepted_answers` and `alternative_answers_allowed` containing both `which`/`who` and `that` variants.

---

### RQA-18 · Writing Hint / Sentence Starter Line Render Leak

**Symptom**: Bulleted hint sections or useful sentence starters (e.g., `- In my opinion, ...`) in writing prompts get blank answer lines rendered between them, making hints look like answer spaces.

**Root Cause**: The exporter script treated bullet prefixes (`-`, `*`) identically to numbered sub-questions (`1.`, `a)`), appending `writing-line` elements after bullet points.

**Prevention Rule**:
- Sub-items starting with `-` or `*` are hints/bullet points and MUST NOT have answer lines appended. Only numbered items (`1.`, `2.`, `a)`, `b)`) receive writing lines.

**Verification Step**:
Check rendered HTML/PDF for Writing tasks to ensure bulleted sentence starters have no blank writing lines between them.

---

### RQA-19 · Open-Ended Past Perfect Gap-Fill Tense Ambiguity

**Symptom**: Gap-fill prompts like `Until chain drives were implemented, cyclists ______ (rely)...` or `Prior to 1890, cities ______ (not develop)...` accept both Past Simple (`relied`, `did not develop`) and Past Perfect (`had relied`, `had not developed`).

**Root Cause**: Prompt lacks explicit duration markers or completion time anchors to mandate Past Perfect over Past Simple.

**Prevention Rule**:
- Every gap-fill item testing Past Perfect vs. Past Simple MUST include explicit time constraints, completion anchors, or duration markers (e.g. `By the time ... for many years`, `By + past year`, `for a decade before ...`).
- If a prompt allows both Past Simple and Past Perfect naturally, the prompt MUST be constrained or both answers MUST be listed in `accepted_answers` and `alternative_answers_allowed`.

**Verification Step**:
Check all Past Perfect gap-fills in `grammar.questions` to ensure explicit time anchors or duration markers exist, or both forms are documented.

---

### RQA-20 · Open-Ended Defining Relative Clause Relative Pronoun Ambiguity

**Symptom**: Open-ended relative clause gap-fills like `Cities ______ invest in protected bicycle lanes...` accept both `that` and `which`.

**Root Cause**: Open-ended format does not specify which pronoun to use for non-human antecedents in defining relative clauses.

**Prevention Rule**:
- In open-ended gap fills testing defining relative clauses for non-human antecedents, the prompt MUST explicitly state the required pronoun (e.g., `Complete the essay sentence using a relative clause (use 'that'):`), OR both `that` and `which` MUST be populated in `accepted_answers` / `alternative_answers_allowed`.

**Verification Step**:
Check open-ended relative clause gap-fills to ensure prompt restriction exists or both `that` and `which` are listed as acceptable.

---

### RQA-21 · Reading Passage & Grammar Stem Text Collisions

**Symptom**: An exact n-gram in a Grammar question stem (e.g., `"pedals to"`) matches text in the Reading passage (e.g., `"added pedals to"`), causing automated PDF layout validators (`validate_rendered_pdf.py`) to match the passage text instead of the grammar blank line, triggering false positive QC failures.

**Root Cause**: Grammar question stems reuse exact multi-word phrases from the Reading passage.

**Prevention Rule**:
- Grammar question stems must paraphrase or vary verb/preposition phrasing relative to the Reading passage (e.g., use `added pedals onto` in reading or `attached pedals to` in grammar) so that the stem target n-gram is unique in the combined Practice PDF text.

**Verification Step**:
Run `validate_rendered_pdf.py` on exported PDFs to confirm no text-matching collisions occur between Reading and Grammar sections.

---

### RQA-22 · Writing Opinion Task Scaffolding Missing for A1-B1 Levels

**Symptom**: Opinion paragraph tasks for lower levels (A1, A2, B1) lack structural guidance, resulting in unorganized student responses.

**Root Cause**: Prompt asks for a 5-6 sentence opinion paragraph without providing a step-by-step 5-sentence outline or sentence starters.

**Prevention Rule**:
- Writing Opinion tasks for A1, A2, and B1 levels MUST include an explicit 5-step numbered structure (1. State opinion, 2. Reason 1, 3. Reason 2, 4. Result/Example, 5. Conclusion) and a list of useful sentence starters (`In my opinion, ... | First, ... | As a result, ... | Therefore, ...`).

**Verification Step**:
Check Writing Task 5 for A1-B1 levels to confirm 5-point numbered outline and sentence starters are present in the prompt.
